"""Matched target accounting and boundary-safe E-INT batching."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Iterator, Sequence
import hashlib
import json
from pathlib import Path
import pickle
import random

import torch
from torch.nn import functional as F

IGNORE = -100
MANIFEST_SHA256 = "ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51"
REVISION = "915333b4f8b8684f39aeaafea600fea6f43fb703"
TRAIN_SHARDS = tuple(f"data/shard_{i:05d}.parquet" for i in range(10))
VAL_SHARD = "data/shard_06542.parquet"
TOKENIZER = "tokenizer/tokenizer.pkl"


@dataclass(frozen=True)
class Segment:
    inputs: tuple[int, ...]
    targets: tuple[int, ...]


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def add_targets(digest, segments: Iterable[Segment]) -> None:
    for segment in segments:
        for target in segment.targets:
            digest.update(target.to_bytes(4, "little"))


def verify_data(root: Path) -> None:
    """Verify the precise source and every file before opening the pinned tokenizer."""
    manifest = (root / "data_manifest.json").read_bytes()
    if hashlib.sha256(manifest).hexdigest() != MANIFEST_SHA256:
        raise ValueError("E-INT data manifest differs from the published ClimbMix pin")
    doc = json.loads(manifest)
    required = {*TRAIN_SHARDS, VAL_SHARD, TOKENIZER, "tokenizer/token_bytes.pt"}
    if doc["source"]["revision"] != REVISION or set(doc["files"]) != required:
        raise ValueError("E-INT document split or tokenizer manifest differs")
    for rel, meta in doc["files"].items():
        file = root / rel
        if not file.resolve().is_relative_to(root.resolve()) or file.stat().st_size != meta["bytes"] or \
                _sha(file) != meta["sha256"]:
            raise ValueError(f"E-INT pinned data file differs: {rel}")


def documents(root: Path, *, split: str, seed: int) -> Iterator[list[int]]:
    """Read intact tokenized documents in a deterministic train order or canonical validation order."""
    from pyarrow.parquet import ParquetFile

    verify_data(root)
    with (root / TOKENIZER).open("rb") as stream:
        encoder = pickle.load(stream)
    bos = encoder.encode_single_token("<|reserved_0|>")
    if split == "train":
        shards = list(TRAIN_SHARDS)
        random.Random(seed).shuffle(shards)
    elif split == "validation":
        shards = [VAL_SHARD]
    else:
        raise ValueError("split must be train or validation")
    for rel in shards:
        path = ParquetFile(root / rel)
        for batch in path.iter_batches(batch_size=128, columns=["text"], use_threads=False):
            for text in batch.column(0).to_pylist():
                yield [bos, *encoder.encode_ordinary(text)]


def updates(documents: Iterable[Sequence[int]], *, context: int, tokens_per_update: int,
            steps: int) -> Iterator[list[Segment]]:
    """Yield an exact ordered block of targets per optimizer update."""
    if min(context, tokens_per_update, steps) <= 0:
        raise ValueError("positive context, tokens per update and steps are required")
    remaining = tokens_per_update
    batch = []
    for doc in documents:
        position = 0
        while position < len(doc) - 1:
            n = min(context, remaining, len(doc) - 1 - position)
            end = position + n
            batch.append(Segment(tuple(doc[position:end]), tuple(doc[position + 1:end + 1])))
            position = end
            remaining -= n
            if remaining == 0:
                yield batch
                steps -= 1
                if steps == 0:
                    return
                batch = []
                remaining = tokens_per_update
    raise ValueError("document stream ended before the exact target budget")


def rows(segments: Iterable[Segment], *, context: int, packed: bool, max_rows: int) -> Iterator[dict]:
    """Use sequential next-fit packing and materialize only one microbatch at a time."""
    if min(context, max_rows) <= 0:
        raise ValueError("positive context and microbatch row count are required")
    pending, row, size = [], [], 0
    for segment in segments:
        n = len(segment.inputs)
        if not 0 < n <= context or len(segment.targets) != n:
            raise ValueError("invalid segment length")
        if row and (not packed or size + n > context):
            pending.append(row)
            row, size = [], 0
            if len(pending) == max_rows:
                yield _tensors(pending, context)
                pending = []
        row.append(segment)
        size += n
    if row:
        pending.append(row)
    if pending:
        yield _tensors(pending, context)


def _tensors(group: list[list[Segment]], context: int) -> dict:
    shape = (len(group), context)
    input_ids = torch.zeros(shape, dtype=torch.long)
    positions = torch.zeros_like(input_ids)
    targets = torch.full_like(input_ids, IGNORE)
    segment_ids = torch.full_like(input_ids, -1)
    for i, row in enumerate(group):
        offset = 0
        for j, segment in enumerate(row):
            n = len(segment.inputs)
            slot = slice(offset, offset + n)
            input_ids[i, slot] = torch.tensor(segment.inputs)
            targets[i, slot] = torch.tensor(segment.targets)
            positions[i, slot] = torch.arange(n)
            segment_ids[i, slot] = j
            offset += n
    same = segment_ids[:, :, None] == segment_ids[:, None, :]
    valid = segment_ids >= 0
    attention = same & valid[:, :, None] & torch.ones((context, context), dtype=torch.bool).tril()
    # Give padding queries a harmless self-edge. Their targets are ignored by the loss.
    attention |= (~valid[:, :, None]) & torch.eye(context, dtype=torch.bool)
    return {"input_ids": input_ids, "targets": targets, "positions": positions, "attention_mask": attention,
            "loss_tokens": int((targets != IGNORE).sum())}


def batch_loss(model, batch: dict, device: torch.device) -> torch.Tensor:
    """Compute a sum for exact accumulation across padding and microbatches."""
    logits = model(batch["input_ids"].to(device), batch["positions"].to(device), batch["attention_mask"].to(device))
    return F.cross_entropy(logits.flatten(0, 1).float(), batch["targets"].flatten().to(device),
                           ignore_index=IGNORE, reduction="sum")


@torch.no_grad()
def validate(model, validation_documents: Iterable[Sequence[int]], device: torch.device, *,
             context: int = 512, target_count: int = 65_536) -> tuple[float, str]:
    """Evaluate every cell with the same context, order, target positions and denominator."""
    model.eval()
    segments, = updates(validation_documents, context=context, tokens_per_update=target_count, steps=1)
    digest = hashlib.sha256()
    add_targets(digest, segments)
    loss = sum(float(batch_loss(model, batch, device)) for batch in
               rows(segments, context=context, packed=False, max_rows=4))
    return loss / target_count, digest.hexdigest()
