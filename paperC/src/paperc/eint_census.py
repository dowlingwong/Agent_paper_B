"""Run one authorized E-INT development cell on its assigned CUDA card."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

import torch
from torch import nn
from torch.nn import functional as F

from paperc import eint_batches as E
from r1.c3 import audit

AUTHORIZATION = "docs/r1/authorizations/paperc_eint_census_20261127.md"
CELLS = {"baseline": (512, False), "A": (512, True), "B": (2048, False), "A+B": (2048, True)}
SEEDS = (61005, 61006, 61007)
TARGETS_PER_UPDATE = 8192


class Block(nn.Module):
    def __init__(self, width=256, heads=4):
        super().__init__()
        self.heads = heads
        self.norm = nn.LayerNorm(width)
        self.qkv = nn.Linear(width, 3 * width)
        self.project = nn.Linear(width, width)
        self.feed_forward = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, 4 * width), nn.GELU(),
                                          nn.Linear(4 * width, width))

    def forward(self, x, attention):
        batch, length, width = x.shape
        qkv = self.qkv(self.norm(x)).reshape(batch, length, 3, self.heads, width // self.heads)
        q, k, v = qkv.permute(2, 0, 3, 1, 4).unbind()
        with torch.nn.attention.sdpa_kernel(torch.nn.attention.SDPBackend.MATH):
            a = F.scaled_dot_product_attention(q, k, v, attn_mask=attention[:, None])
        x = x + self.project(a.transpose(1, 2).reshape(batch, length, width))
        return x + self.feed_forward(x)


class Model(nn.Module):
    def __init__(self, width=256):
        super().__init__()
        self.words = nn.Embedding(8192, width)
        self.positions = nn.Embedding(2048, width)
        self.blocks = nn.ModuleList(Block(width) for _ in range(6))
        self.norm = nn.LayerNorm(width)

    def forward(self, input_ids, positions, attention):
        x = self.words(input_ids) + self.positions(positions)
        for block in self.blocks:
            x = block(x, attention)
        return F.linear(self.norm(x), self.words.weight)


def train_update(model, optimizer, segments, device, *, context, packed, max_rows=4) -> int:
    """Normalize the accumulated gradient by observed real targets once per update."""
    count = sum(len(s.targets) for s in segments)
    if not count:
        raise ValueError("training update has no loss targets")
    optimizer.zero_grad(set_to_none=True)
    observed = 0
    for batch in E.rows(segments, context=context, packed=packed, max_rows=max_rows):
        (E.batch_loss(model, batch, device) / count).backward()
        observed += batch["loss_tokens"]
    if observed != count:
        raise ValueError("packing changed the effective token budget")
    optimizer.step()
    return observed


def _launch_note(root: Path, spec_bytes: bytes) -> dict:
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, timeout=30).strip()

    root = root.resolve()
    if (Path(__file__).resolve().parents[3] != root or Path(E.__file__).resolve().parents[3] != root
            or Path(audit.__file__).resolve().parents[2] != root):
        raise ValueError("running modules did not come from the pinned paper checkout")
    note = audit._key_block(audit._published_bytes(root, AUTHORIZATION).decode())
    head = git("rev-parse", "HEAD")
    expected = {"approved": "true", "paper_commit": head,
                "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(), "task": "local/20261127-20"}
    if any(note.get(k) != v for k, v in expected.items()) or not re.fullmatch(r"[0-9a-f]{64}", note.get("review", "")):
        raise ValueError("published E-INT authorization does not bind the clean code, spec and review")
    git("merge-base", "--is-ancestor", head, "origin/main")
    if git("status", "--porcelain"):
        raise ValueError("dirty E-INT launch checkout")
    return note


def run(root: Path, data: Path, out: Path, spec_bytes: bytes, cell: str, seed: int) -> None:
    note = _launch_note(root, spec_bytes)
    spec = json.loads(spec_bytes)
    if cell not in CELLS or seed not in SEEDS or spec["phase"] not in ("smoke", "development"):
        raise ValueError("cell, seed or phase is outside E-INT development")
    if [cell, seed] not in spec["attempts"]:
        raise ValueError("cell and seed are outside the authorized attempts")
    if torch.cuda.device_count() != 1 or torch.cuda.get_device_name(0) != spec["gpu_model"]:
        raise ValueError("E-INT requires exactly one visible GPU of the bound model")
    if (os.environ.get("PYTORCH_NO_CUDA_MEMORY_CACHING", "0") not in ("", "0")
            or torch.cuda.memory.get_allocator_backend() != "native"):
        raise ValueError("E-INT requires the enabled native CUDA caching allocator")
    cap = int(spec["allocator_cap_bytes"])
    steps = int(spec["updates"])
    validation_targets = int(spec["validation_targets"])
    total = torch.cuda.get_device_properties(0).total_memory
    if not 0 < cap <= total or not 0 < steps <= 128 or not 0 < validation_targets <= 65_536:
        raise ValueError("invalid memory cap or target budget")
    E.verify_data(data)
    out.mkdir()
    (out / "spec.json").write_bytes(spec_bytes)
    result = {"cell": cell, "seed": seed, "phase": spec["phase"], "paper_commit": note["paper_commit"],
              "gpu_model": spec["gpu_model"], "allocator_cap_bytes": cap, "trained_tokens": 0,
              "torch_version": torch.__version__, "cuda_version": torch.version.cuda,
              "spec_sha256": note["spec_sha256"],
              "data_manifest_sha256": E.MANIFEST_SHA256, "planned_train_tokens": steps * TARGETS_PER_UPDATE,
              "validation_tokens": validation_targets}
    torch.cuda.set_per_process_memory_fraction(cap / total, 0)
    torch.cuda.reset_peak_memory_stats(0)
    device = torch.device("cuda", 0)
    context, packed = CELLS[cell]
    started = time.monotonic()
    try:
        torch.manual_seed(seed)
        model = Model().to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
        stream = E.documents(data, split="train", seed=seed)
        digest = hashlib.sha256()
        with (out / "updates.jsonl").open("x") as log, torch.autocast("cuda", dtype=torch.bfloat16, cache_enabled=False):
            for segments in E.updates(stream, context=context, tokens_per_update=TARGETS_PER_UPDATE, steps=steps):
                E.add_targets(digest, segments)
                count = train_update(model, optimizer, segments, device, context=context, packed=packed)
                result["trained_tokens"] += count
                log.write(json.dumps({"loss_tokens": count, "trained_tokens": result["trained_tokens"]}) + "\n")
                log.flush()
            torch.cuda.synchronize()
            result["training_seconds"] = time.monotonic() - started
            result["target_sha256"] = digest.hexdigest()
            val_docs = E.documents(data, split="validation", seed=seed)
            result["validation_loss"], result["validation_target_sha256"] = E.validate(
                model, val_docs, device, target_count=validation_targets)
        torch.cuda.synchronize()
        if (result["trained_tokens"] != result["planned_train_tokens"] or torch.cuda.max_memory_reserved(0) > cap
                or not math.isfinite(result["validation_loss"])):
            raise ValueError("E-INT target budget, allocator cap or finite-loss check failed")
        result["status"] = "complete"
    except torch.OutOfMemoryError:
        result["status"] = "out_of_memory"
        raise
    except Exception as exc:
        result.update(status="failed", failure=type(exc).__name__)
        raise
    finally:
        result.update(wall_seconds=time.monotonic() - started,
                      peak_allocated_bytes=torch.cuda.max_memory_allocated(0),
                      peak_reserved_bytes=torch.cuda.max_memory_reserved(0))
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def interaction(records: list[dict]) -> dict:
    """Read feasibility first and calculate the interaction on complete, matched seeds."""
    grouped = {}
    for row in records:
        key = row["seed"], row["cell"]
        if key in grouped or row["cell"] not in CELLS:
            raise ValueError("duplicate or unknown E-INT cell")
        grouped[key] = row
    summaries = {}
    for seed in sorted({seed for seed, _ in grouped}):
        cells = {cell: grouped.get((seed, cell), {"status": "missing"}) for cell in CELLS}
        statuses = {cell: rec["status"] for cell, rec in cells.items()}
        delta = None
        if set(statuses.values()) == {"complete"}:
            for key in ("phase", "spec_sha256", "target_sha256", "validation_target_sha256", "trained_tokens",
                        "validation_tokens", "allocator_cap_bytes", "paper_commit", "gpu_model",
                        "data_manifest_sha256", "torch_version", "cuda_version"):
                if len({rec[key] for rec in cells.values()}) != 1:
                    raise ValueError(f"E-INT seed {seed} is unmatched on {key}")
            loss = {cell: rec["validation_loss"] for cell, rec in cells.items()}
            if not all(math.isfinite(value) for value in loss.values()):
                raise ValueError(f"E-INT seed {seed} has non-finite evaluation loss")
            delta = loss["A"] + loss["B"] - loss["A+B"] - loss["baseline"]
        summaries[seed] = {"status": statuses, "quality_interaction": delta}
    return summaries


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--cell", choices=CELLS, required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    args = parser.parse_args(argv)
    run(args.paper, args.data, args.out, args.spec.read_bytes(), args.cell, args.seed)


if __name__ == "__main__":
    main()
