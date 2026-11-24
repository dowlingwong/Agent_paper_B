"""Track P P.4 phase 1: the pieces the runner unit adds around the SFT pipeline. ENGINEERING_ONLY; AI-assisted (Claude).

Authority: the P.4 phase-1 authorization draft (`docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`,
revision 4.2), R1-TRACKP-P4-DECISIONS (P4-LABELS A, P4-LC A, P4-JOB A), R1-TRACKP-V21-FREEZE,
R1-TRACKP-P4-RUNNER-DECISIONS (1), R1-HTC-QTORCH.

* ``check_env3_freeze`` — R1-TRACKP-V21-FREEZE: the env3 ``pip freeze`` in the image may differ from R1-ENV-PIN's
  freeze (``pip_freeze_trackp-gpu.txt``) **only in the ``causal_conv1d`` line, at the same version number**. The
  difference is returned for the job record; any other difference is a STOP. R1-TRACKP-P4-RUNNER-DECISIONS (1), as
  recommended: "the same version number" reads as version 1.7.0 (the PEP 440 *public* version), any local build label
  admitted and recorded; with image v2.2 building causal_conv1d from source (R1-TRACKP-IMAGE-V22-B) the env3 line is
  checked against 1.7.0. So the image's causal_conv1d line must read ``causal-conv1d==1.7.0`` or
  ``causal-conv1d==1.7.0+<local label>`` (the label recorded), whether the freeze is otherwise identical or not; every
  other line must match the pin exactly. Any other form (another version, another spelling of the name, a direct
  reference ``@ <url>``) is a STOP.
* ``check_partition`` — P4-LABELS A and §4: the receipted sweep-1 train/dev partition bound to the note's
  ``labels:`` and ``label_receipt:`` sha256 and to the frozen source block (``inputs.label_block_sha256``);
  ``LabelBlockSource`` (``release.open_partition``) re-checks the receipt's own bindings when the data is built.
* ``lc_points`` / ``lc_subset`` — P4-LC A: the learning-curve points below the training-set size, plus the full set
  (the selected-lr grid runs); "examples" are training rows of the data directory, rule no-ops included, drawn
  without replacement by a fixed seed per point (``LC_SEED + n``). A subset is a derived data directory: the drawn
  train rows and every val / val_seen row, ``splits.json`` unchanged, and an ``lc_subset`` record binding the parent's
  ``sft_data.json`` sha256.
* ``rps_skill_bootstrap`` — §3: the instance-cluster bootstrap 95 % interval for RPS skill on **primary val**
  (2,000 resamples, seed 20261108), for the seed mean of the selected-lr runs, raw and at each run's fitted
  temperature. Readiness only: no gate decision is taken in phase 1.
* ``arm_pin`` — the per-arm pin file: the base and adapter revisions, the staged weight sha256, the data directory,
  the selected lr, the micro-batch the runs used, and for every run the sha256 of its ``sft_report.json``,
  ``stage_s/best.json``, the checkpoint manifest (``best/manifest.json``; ``record.json`` for the CPU stand-in), the
  whole ``best/`` tree and ``best/temperature.json`` (a run missing any of them is a STOP).

Nothing here opens an evaluation block or a test row: the data directory holds none.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

FREEZE_RULE = "R1-TRACKP-V21-FREEZE"
FREEZE_DECISION = "R1-TRACKP-P4-RUNNER-DECISIONS (1)"
CAUSAL = "causal-conv1d"
CAUSAL_VERSION = "1.7.0"               # R1-TRACKP-P4-RUNNER-DECISIONS (1): the env3 line is checked against 1.7.0
SOURCE_BLOCK_SHA256 = "cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca"   # the frozen sweep-1 block
PARTITION_NAME = "label_block.traindev.jsonl"
RECEIPT_NAME = "RECEIPT.json"
LC_POINTS = (250, 500)                 # RUNBOOK P.4's points that fit below ~590 P3 training rows (P4-LC A)
LC_SEED = 20261122
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20261108
LC_SCHEMA = "trackp_p4_lc_subset/v1"
BOOT_SCHEMA = "trackp_p4_bootstrap/v1"
PIN_SCHEMA = "trackp_p4_arm_pin/v2"


class P4Stop(Exception):
    """A STOP of the P.4 phase-1 runner (for the author; outputs are kept)."""


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_file(p: Path | str) -> str:
    return _sha_bytes(Path(p).read_bytes())


# =============================================================================================== env3 freeze
_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
PINNED_CAUSAL_LINE = f"{CAUSAL}=={CAUSAL_VERSION}"
# FREEZE_DECISION: exactly the pinned line, or the pinned line with a PEP 440 local label (``+seg[.seg]...``)
_CAUSAL_LINE = re.compile(rf"^{re.escape(PINNED_CAUSAL_LINE)}(?:\+([A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*))?$")


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _line_name(line: str) -> str:
    m = _NAME.match(line.strip())
    return _norm(m.group(1)) if m else line.strip()


def _image_causal(lines: Sequence[str]) -> tuple[str, str | None]:
    """The image freeze's one causal_conv1d line, checked against 1.7.0: ``causal-conv1d==1.7.0`` or
    ``causal-conv1d==1.7.0+<local label>`` (FREEZE_DECISION). Returns (line, local label or None)."""
    causal = [x for x in lines if _line_name(x) == CAUSAL]
    if len(causal) != 1:
        raise P4Stop(f"STOP: the image freeze has {len(causal)} causal_conv1d lines, not one ({FREEZE_RULE}; "
                     f"{FREEZE_DECISION})")
    m = _CAUSAL_LINE.fullmatch(causal[0])
    if m is None:
        raise P4Stop(f"STOP: the causal_conv1d line {causal[0]!r} is not {PINNED_CAUSAL_LINE} with at most a local "
                     f"build label ({FREEZE_RULE}; {FREEZE_DECISION})")
    return causal[0], m.group(1)


def check_env3_freeze(got: str, pinned: str) -> dict:
    """R1-TRACKP-V21-FREEZE read per R1-TRACKP-P4-RUNNER-DECISIONS (1) (module docstring). The pinned freeze must
    hold ``causal-conv1d==1.7.0``; the image freeze must equal it line for line (sorted, blank lines dropped), except
    that its causal_conv1d line may carry a local build label (``causal-conv1d==1.7.0+<label>``). Returns the record
    for the job: ``identical`` or ``causal_conv1d_only``, with the image's causal_conv1d line and its local label."""
    have = sorted(x.strip() for x in got.splitlines() if x.strip())
    want = sorted(x.strip() for x in pinned.splitlines() if x.strip())
    if len(set(have)) != len(have) or len(set(want)) != len(want):
        raise P4Stop("STOP: a freeze holds a duplicate line (R1-HTC-QTORCH)")
    if PINNED_CAUSAL_LINE not in want:
        raise P4Stop(f"STOP: the pinned freeze does not hold {PINNED_CAUSAL_LINE} ({FREEZE_DECISION})")
    extra, missing = sorted(set(have) - set(want)), sorted(set(want) - set(have))
    others = [x for x in extra + missing if _line_name(x) != CAUSAL]
    if others:
        raise P4Stop(f"STOP: the env3 freeze differs from R1-ENV-PIN's outside the causal_conv1d line ({FREEZE_RULE}): "
                     f"{others[:10]}")
    if len(extra) != len(missing) or len(extra) > 1:
        raise P4Stop(f"STOP: the causal_conv1d difference is not one line for one line ({FREEZE_RULE}): "
                     f"extra {extra}, missing {missing}")
    line, label = _image_causal(have)
    record = {"rule": FREEZE_RULE, "decision": FREEZE_DECISION, "lines": len(have),
              "sha256_sorted": _sha_bytes("\n".join(have).encode()), "image_line": line, "version": CAUSAL_VERSION,
              "local_label": label}
    if not extra:
        return {**record, "status": "identical"}
    return {**record, "status": "causal_conv1d_only", "pinned_line": missing[0],
            "disclosure": f"the causal_conv1d line carries the local build label {label!r} on version {CAUSAL_VERSION} "
                          f"({FREEZE_RULE}; {FREEZE_DECISION}); recorded in the job record and disclosed in the P.4 "
                          "report"}


# =============================================================================================== labels
def check_partition(part_dir: Path | str, *, partition_sha256: str, receipt_sha256: str,
                    source_block_sha256: str = SOURCE_BLOCK_SHA256) -> dict:
    """The note's ``labels:`` and ``label_receipt:`` pins and the receipt's source block (§4, P3 of the draft)."""
    part_dir = Path(part_dir)
    part, rec = part_dir / PARTITION_NAME, part_dir / RECEIPT_NAME
    for p in (part, rec):
        if p.is_symlink() or not p.is_file():
            raise P4Stop(f"STOP: {p} missing (the receipted sweep-1 train/dev partition, P4-LABELS A)")
    got_part, got_rec = _sha_file(part), _sha_file(rec)
    if got_part != partition_sha256:
        raise P4Stop(f"STOP: the partition sha256 {got_part} is not the note's labels: {partition_sha256}")
    if got_rec != receipt_sha256:
        raise P4Stop(f"STOP: the receipt sha256 {got_rec} is not the note's label_receipt: {receipt_sha256}")
    receipt = json.loads(rec.read_bytes())
    if receipt.get("source") != "sweep1" or receipt.get("stage") != "traindev":
        raise P4Stop("STOP: the receipt is not the sweep-1 train/dev release")
    if (receipt.get("inputs") or {}).get("label_block_sha256") != source_block_sha256:
        raise P4Stop(f"STOP: the receipt's source block is not the frozen sweep-1 block {source_block_sha256}")
    if (receipt.get("outputs") or {}).get(PARTITION_NAME) != partition_sha256:
        raise P4Stop("STOP: the receipt does not bind this partition")
    return {"partition": str(part), "partition_sha256": got_part, "receipt_sha256": got_rec,
            "source_block_sha256": source_block_sha256, "release_commit": receipt.get("release_commit"),
            "counts": receipt.get("counts")}


# =============================================================================================== learning curve
def _rows(data_dir: Path) -> list[dict]:
    return [json.loads(x) for x in (Path(data_dir) / "rows.jsonl").read_text().splitlines() if x.strip()]


def lc_points(n_train: int, points: Sequence[int] = LC_POINTS) -> list:
    """P4-LC A: the points below the training-set size, then ``"full"`` (the selected-lr grid runs)."""
    if n_train < 1:
        raise P4Stop("STOP: an empty training set")
    return [int(p) for p in sorted(points) if 0 < int(p) < n_train] + ["full"]


def lc_subset(data_dir: Path | str, n: int, out_dir: Path | str, *, seed: int | None = None) -> dict:
    """A derived data directory with ``n`` training rows drawn by ``seed`` (default ``LC_SEED + n``) and every
    held-out row (module docstring). Returns its manifest."""
    data_dir, out_dir = Path(data_dir), Path(out_dir)
    if out_dir.exists():
        raise P4Stop(f"STOP: {out_dir} exists (no overwrite)")
    parent = json.loads((data_dir / "sft_data.json").read_bytes())
    for name, key in (("rows.jsonl", "rows_sha256"), ("splits.json", "splits_sha256")):
        if _sha_file(data_dir / name) != parent.get(key):
            raise P4Stop(f"STOP: {data_dir}/{name} differs from its sft_data.json")
    if parent.get("lc_subset"):
        raise P4Stop("STOP: a learning-curve subset is drawn from the full data directory only")
    rows = _rows(data_dir)
    train = [r for r in rows if r["split"] == "train"]
    if not 0 < n < len(train):
        raise P4Stop(f"STOP: a learning-curve point must be below the training-set size ({n} vs {len(train)})")
    seed = LC_SEED + int(n) if seed is None else int(seed)
    pick = set(np.random.default_rng(seed).choice(len(train), size=int(n), replace=False).tolist())
    keep_ids = {r["proposal_id"] for k, r in enumerate(train) if k in pick}
    out_rows = [r for r in rows if r["split"] != "train" or r["proposal_id"] in keep_ids]
    out_dir.mkdir(parents=True)
    text = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in out_rows)
    (out_dir / "rows.jsonl").write_text(text)
    (out_dir / "splits.json").write_bytes((data_dir / "splits.json").read_bytes())
    counts = dict(parent.get("counts") or {})
    counts["train"] = int(n)
    manifest = {**parent, "rows_sha256": _sha_file(out_dir / "rows.jsonl"), "counts": counts,
                "lc_subset": {"schema": LC_SCHEMA, "rule": "P4-LC A (R1-TRACKP-P4-DECISIONS)", "n_train": int(n),
                              "parent_n_train": len(train), "seed": seed,
                              "parent_sft_data_sha256": _sha_file(data_dir / "sft_data.json"),
                              "train_ids_sha256": _sha_bytes("\n".join(sorted(keep_ids)).encode())}}
    (out_dir / "sft_data.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


# =============================================================================================== bootstrap
def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def rps_skill_bootstrap(data_dir: Path | str, run_dirs: Sequence[Path | str], *,
                        resamples: int = BOOTSTRAP_RESAMPLES, seed: int = BOOTSTRAP_SEED) -> dict:
    """§3 (module docstring): ``run_dirs`` are the selected-lr runs of one arm on ``data_dir`` (their ``stage_s``
    directories hold ``sft_report.json``, ``pred_val_logits.npy`` and ``best/temperature.json``)."""
    from r1.c3.train import metrics as M
    data_dir = Path(data_dir)
    data_sha = _sha_file(data_dir / "sft_data.json")
    rows = _rows(data_dir)
    val = [r for r in rows if r["split"] == "val"]                    # primary val, in load_sft_data's order
    y_val = np.asarray([r["y"] for r in val], float)
    base = M.base_rate(np.asarray([r["y"] for r in rows if r["split"] == "train"], float))
    instances = sorted({r["instance"] for r in val})
    idx = {i: k for k, i in enumerate(instances)}
    row_inst = np.asarray([idx[r["instance"]] for r in val])
    if not run_dirs:
        raise P4Stop("STOP: no runs for the bootstrap")
    probs = {}
    for d in map(Path, run_dirs):
        rep = json.loads((d / "sft_report.json").read_bytes())
        if rep.get("data_sha256") != data_sha:
            raise P4Stop(f"STOP: {d} was trained on another data directory")
        logits = np.load(d / "pred_val_logits.npy")
        if logits.shape != (len(val), y_val.shape[1]) or not np.isfinite(logits).all():
            raise P4Stop(f"STOP: {d}/pred_val_logits.npy does not match the primary val rows")
        T = float(json.loads((d / "best" / "temperature.json").read_bytes())["temperature"])
        probs[str(d)] = {"raw": _softmax(logits), "temperature_scaled": _softmax(logits / T), "temperature": T}
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(instances), size=(int(resamples), len(instances)))
    out = {"schema": BOOT_SCHEMA, "rule": "§3 of the P.4 phase-1 draft: instance-cluster bootstrap on primary val; "
                                          "readiness only, no gate decision in phase 1",
           "data_sft_data_sha256": data_sha, "n_val_rows": len(val), "n_val_instances": len(instances),
           "resamples": int(resamples), "seed": int(seed), "runs": sorted(probs),
           "temperatures": {k: v["temperature"] for k, v in sorted(probs.items())}}
    for kind in ("raw", "temperature_scaled"):
        point = float(np.mean([M.rps_skill(p[kind], y_val, base) for p in probs.values()]))
        boot = np.empty(int(resamples))
        for b in range(int(resamples)):
            w = np.bincount(draws[b], minlength=len(instances))[row_inst].astype(float)
            boot[b] = np.mean([M.rps_skill(p[kind], y_val, base, w) for p in probs.values()])
        lo, hi = np.percentile(boot, [2.5, 97.5])
        out[kind] = {"rps_skill_seed_mean": point, "ci95": [float(lo), float(hi)]}
    return out


# =============================================================================================== per-arm pin file
def arm_pin(*, arm: str, base_record: Mapping, staged: Mapping[str, str], data_dir: Path | str,
            select_report: Mapping, grid_runs: Sequence[Path | str], lc_runs: Mapping[str, Sequence[Path | str]],
            micro_batch: int, host_config_sha256: str) -> dict:
    """The per-arm pin file (module docstring)."""
    def run_entry(d: Path) -> dict:
        stage = d / "stage_s"
        rep = json.loads((stage / "sft_report.json").read_bytes())
        best_dir = stage / "best"
        manifest = next((best_dir / n for n in ("manifest.json", "record.json") if (best_dir / n).is_file()), None)
        files = sorted(p for p in best_dir.rglob("*") if p.is_file()) if best_dir.is_dir() else []
        for need, ok in (("stage_s/best.json", (stage / "best.json").is_file()),
                         ("best/manifest.json (record.json for the CPU stand-in)", manifest is not None),
                         ("best/temperature.json", (best_dir / "temperature.json").is_file()),
                         ("a non-empty best/ checkpoint", bool(files))):
            if not ok:
                raise P4Stop(f"STOP: {d.name} lacks {need}: its best checkpoint cannot be pinned")
        tree = _sha_bytes("".join(f"{p.relative_to(best_dir).as_posix()}\0{_sha_file(p)}\n" for p in files).encode())
        return {"run_dir": d.name, "lr": rep.get("lr"), "seed": rep.get("seed"),
                "best_value": (rep.get("train") or {}).get("best_value"),
                "data_sha256": rep.get("data_sha256"),
                "sft_report_sha256": _sha_file(stage / "sft_report.json"),
                "best_json_sha256": _sha_file(stage / "best.json"),
                "best_manifest": {"name": manifest.name, "sha256": _sha_file(manifest)},
                "best_tree_sha256": tree,
                "temperature_sha256": _sha_file(best_dir / "temperature.json")}
    return {"schema": PIN_SCHEMA, "label": "ENGINEERING_ONLY", "arm": arm, "base": dict(base_record),
            "staged_weights_sha256": dict(sorted(staged.items())),
            "data_sft_data_sha256": _sha_file(Path(data_dir) / "sft_data.json"),
            "micro_batch": int(micro_batch), "host_config_sha256": host_config_sha256,
            "selected_lr": select_report.get("selected_lr"),
            "mean_best_val_rps": select_report.get("mean_best_val_rps"),
            "grid": [run_entry(Path(d)) for d in grid_runs],
            "learning_curve": {str(k): [run_entry(Path(d)) for d in v] for k, v in lc_runs.items()}}
