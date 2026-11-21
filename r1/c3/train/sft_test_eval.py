"""Track P P.4 test evaluator: the held-out test number under R1-TRACKP-SFT-DUP. ENGINEERING_ONLY on sweep 1;
AI-assisted (Claude).

The SFT data directory (``sft_data.build_sft_data``) holds no test rows; it lists the test instances and, under the
decided policy ``heldout_excludes_seen``, the test proposals whose (node, incumbent, candidate) key also occurs on
a train or val instance (``splits.json`` ``test_proposals_seen_in_train_or_val``; "seen" includes val, the reading of
R1-TRACKP-SFT-DUP that reproduces its 74 primary test proposals). This module turns one trained arm's logits on the
test proposals into the test report:

* **primary** test population (the headline number, R1-TRACKP-SFT-DUP): the labelled test proposals **not** in the
  exclusion list;
* **secondary** population: every labelled test proposal, duplicates of the training data included;
* the same belief metrics as the Stage S validation (``sft.val_metrics``: RPS, RPS skill against the training base
  rate, NLL, all-bins and top-1 ECE, PIT histogram, predictive and label sd, width ratio), with the prefix
  ``test_`` (primary) and ``test_full_`` (secondary), **at the arm's fitted temperature** (headline) and raw
  (T = 1), both from the one logits file;
* the same metrics per node and per suite (``suite_of``) on the primary population, with the counts of both.

**Test target.** The targets are the label-seed (7001–7005) soft labels of the test instances, read through
``LabelBlockSource`` (which never opens evaluation-seed files); no value from 7006–7010 is read. That is the
phase-1 / ENGINEERING target. Spec §7.1 declares the evidence test belief metrics on ``y_eval`` (7006–7010); which
target the evidence test uses is the author decision P4-TARGET of the phase-2 note, and the report records
``test_target``.

**Phase 1 reads no real-label test.** Under R1-MAIN-PROPOSER (e) sweep 1 and sweep 2 share one instance assignment
and twin campaigns share labels, so a real-label test read on sweep 1 would expose the evidence test partition before
the phase-2 choices (P.4 draft, P4-PHASE1-TEST). ``evaluate_test`` therefore refuses real labels on ENGINEERING_ONLY
data unless ``allow_engineering_real_label_read=True`` (only under the author's option B of that decision).

Bindings and refusals (each is a STOP, ``TestEvalError``):

* the data directory: schema, featurizer and prompt versions, ``rows.jsonl`` and ``splits.json`` sha256 against
  ``sft_data.json``; the policy must be ``heldout_excludes_seen`` unless the labels are synthetic;
* the split: the recorded train/val/test instances must form the recorded universe (n, sha256) and equal the
  assignment ``sft_data.assign_splits`` recomputes from the recorded config;
* the table: loaded with the data manifest's table hashes as pins (R1-BX-D8 and sealed-path guards); unique ids;
  every table instance in the recorded split;
* **the exclusion list is recomputed** from the table and the recorded split (a key is seen if it occurs on any
  table row of a train or val instance, labelled or not, as in the builder) and must equal ``splits.json``'s list;
* the labels: the label source's provenance must equal the data manifest's (kind, sha256, seed, shift_z, sweep, and
  the label block's completion record);
* the arm: the run directory's ``sft_report.json`` must name this data directory; the temperature is read from
  ``best/temperature.json``; the logits file must carry the sha256 of ``sft_report.json``, ``best.json``,
  ``best/temperature.json`` and the ``best/`` tree as they are now, the same arm id, the replay record of this table
  and sweep index, one finite 12-logit vector per labelled test proposal and no other id;
* **one test read per arm:** the test-read ledger (append-only JSON lines, file name ``LEDGER_NAME``, one per table by
  the runner's convention, appended under an exclusive file lock) refuses a second read of the same arm id, or of the
  same best checkpoint, on the same test material — the table, the label source and the split, whatever data
  directory was rebuilt from them; the output directory is new and the report is written once.

``replay_test_prompts`` replays the test proposals' prompts from the sweep with the table loaded under the manifest's
pins and checks every replayed proposal's features against its table row (``features_hash``), as the builder does;
``predict_test`` loads the arm's best model itself (through the caller's ``loader`` on ``run_dir/best``) and writes the
logits file.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np

from r1.c3.analysis_guard import refuse_sealed
from r1.c3.train import sft_data as SD

TEST_REPORT_SCHEMA = "trackp_sft_test_report/v2"
PREDICTIONS_SCHEMA = "trackp_sft_test_logits/v2"
LEDGER_SCHEMA = "trackp_sft_test_read/v2"
LEDGER_NAME = "trackp_p4_test_reads.jsonl"
N_BINS = 12
RULE = ("R1-TRACKP-SFT-DUP: primary test population = labelled test proposals not in "
        "splits.json test_proposals_seen_in_train_or_val; secondary = every labelled test proposal")
TEST_TARGET = ("label-seed (7001-7005) soft labels of the test instances: the phase-1 / ENGINEERING target; spec "
               "§7.1 declares y_eval (7006-7010) for the evidence test (P4-TARGET, phase-2 note)")


class TestEvalError(SD.SFTDataError):
    """A STOP of the test evaluator."""

    __test__ = False  # not a pytest class


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _ids_sha(ids: Sequence[str]) -> str:
    return _sha_bytes("\n".join(sorted(ids)).encode())


def _json_safe(obj):
    """NaN and infinities as null (JSON has none)."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, (float, np.floating)):
        return float(obj) if math.isfinite(float(obj)) else None
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


# ---------------------------------------------------------------------------------------------- data directory

def read_data_dir(data_dir: Path | str) -> dict:
    """The data manifest, the splits record and the training base rate, with the checks of ``load_sft_data``
    (without torch)."""
    data_dir = Path(data_dir)
    refuse_sealed(data_dir)
    raw_manifest = (data_dir / "sft_data.json").read_bytes()
    manifest = json.loads(raw_manifest)
    if manifest.get("schema") != SD.SFT_DATA_SCHEMA:
        raise TestEvalError(f"{data_dir}: not an SFT data directory")
    if manifest.get("prompt_version") != SD.PROMPT_VERSION or \
            manifest.get("featurizer_version") != SD.FEATURIZER_VERSION:
        raise TestEvalError(f"{data_dir}: built with {manifest.get('featurizer_version')} / "
                            f"{manifest.get('prompt_version')}, this code is {SD.FEATURIZER_VERSION} / "
                            f"{SD.PROMPT_VERSION}")
    blobs = {name: (data_dir / name).read_bytes() for name in ("rows.jsonl", "splits.json")}
    for name, key in (("rows.jsonl", "rows_sha256"), ("splits.json", "splits_sha256")):
        if _sha_bytes(blobs[name]) != manifest.get(key):
            raise TestEvalError(f"{data_dir}/{name}: sha256 differs from sft_data.json")
    splits = json.loads(blobs["splits.json"])
    policy = (splits.get("config") or {}).get("cross_split_duplicates", "drop_from_train")
    synthetic = (manifest.get("labels") or {}).get("kind") == "synthetic"
    if policy != SD.DECIDED_DUPLICATE_POLICY and not synthetic:
        raise TestEvalError(f"{data_dir}: built with cross_split_duplicates {policy!r}; R1-TRACKP-SFT-DUP decides "
                            f"{SD.DECIDED_DUPLICATE_POLICY!r} for real labels")
    if policy == "drop_from_train" or splits.get("test_proposals_seen_in_train_or_val") is None:
        raise TestEvalError(f"{data_dir}: no exclusion list (policy {policy!r}); the primary test number needs one")
    y_train = [r["y"] for r in (json.loads(x) for x in blobs["rows.jsonl"].decode("utf-8").splitlines() if x.strip())
               if r["split"] == "train"]
    if not y_train:
        raise TestEvalError(f"{data_dir}: no training rows (the base rate needs them)")
    from r1.c3.train import metrics as M
    return {"dir": data_dir, "manifest": manifest, "manifest_sha256": _sha_bytes(raw_manifest), "splits": splits,
            "policy": policy, "synthetic": synthetic, "base": M.base_rate(np.asarray(y_train, dtype=float))}


def check_label_source(manifest: Mapping, label_source: SD.LabelSource) -> dict:
    """The label source's provenance must equal the data manifest's; returns it."""
    want, got = manifest.get("labels") or {}, label_source.provenance()
    for key in ("kind", "sha256", "seed", "shift_z", "sweep"):
        if want.get(key) != got.get(key):
            raise TestEvalError(f"label source {key} {got.get(key)!r} differs from the data manifest's "
                                f"{want.get(key)!r}")
    if want.get("kind") == "label_block" and \
            (want.get("completion") or {}).get("sha256") != (got.get("completion") or {}).get("sha256"):
        raise TestEvalError("label block completion record differs from the data manifest's")
    return got


def _pinned_table(data: Mapping, table_dir: Path | str) -> tuple[list[dict], dict]:
    pins = ((data["manifest"].get("table") or {}).get("sha256") or {})
    if "proposals.jsonl" not in pins:
        raise TestEvalError(f"{data['dir']}: the data manifest records no table hash; the test cannot be bound")
    return SD.load_table(table_dir, pins=pins)


# ---------------------------------------------------------------------------------------------- populations

def check_split(splits: Mapping) -> dict[str, str]:
    """{instance: split} from ``splits.json``; no instance in two splits."""
    instances = splits.get("instances") or {}
    split_of: dict[str, str] = {}
    for name in SD.SPLITS:
        for inst in instances.get(name) or []:
            if inst in split_of:
                raise TestEvalError(f"instance {inst} is in two splits")
            split_of[inst] = name
    return split_of


def _check_assignment(splits: Mapping, split_of: Mapping[str, str]) -> None:
    """The recorded instances form the recorded universe and equal the assignment recomputed from the config."""
    union = sorted(split_of)
    uni = splits.get("universe") or {}
    if uni.get("n") != len(union) or uni.get("sha256") != _sha_bytes("\n".join(union).encode()):
        raise TestEvalError("the recorded split instances do not form the recorded universe (n, sha256)")
    try:
        again = SD.assign_splits(union, splits.get("config") or {}, universe=union)
    except SD.SFTDataError as exc:
        raise TestEvalError(f"the recorded split config cannot be recomputed: {exc}") from None
    if again != dict(split_of):
        diff = sorted(i for i in union if again.get(i) != split_of[i])
        raise TestEvalError(f"the recorded split differs from its recomputation ({len(diff)} instances, "
                            f"e.g. {diff[:3]})")


def heldout_populations(table_rows: Sequence[Mapping], splits: Mapping, records: Sequence[Mapping]) -> dict:
    """Primary and secondary test populations; the split and the exclusion list recomputed and compared with
    ``splits.json``."""
    split_of = check_split(splits)
    outside = sorted({r["instance"] for r in table_rows} - set(split_of))
    if outside:
        raise TestEvalError(f"table instances outside the recorded split: {outside[:5]}")
    _check_assignment(splits, split_of)
    by_id = {r["proposal_id"]: r for r in table_rows}
    if len(by_id) != len(table_rows):
        raise TestEvalError("duplicate proposal id in the table")
    seen = {SD.dup_key(r) for r in table_rows if split_of[r["instance"]] in ("train", "val")}
    recomputed = sorted(r["proposal_id"] for r in table_rows
                        if split_of[r["instance"]] == "test" and SD.dup_key(r) in seen)
    recorded = splits.get("test_proposals_seen_in_train_or_val")
    if recorded is None or sorted(recorded) != recomputed:
        n = None if recorded is None else len(recorded)
        raise TestEvalError(f"the exclusion list differs from the recomputation ({n} recorded, "
                            f"{len(recomputed)} recomputed)")
    unknown = sorted(r["proposal_id"] for r in records if r["proposal_id"] not in by_id)
    if unknown:
        raise TestEvalError(f"{len(unknown)} labelled proposals are not in the table, e.g. {unknown[:3]}")
    excluded = set(recomputed)
    secondary = sorted(r["proposal_id"] for r in records if split_of[by_id[r["proposal_id"]]["instance"]] == "test")
    primary = [p for p in secondary if p not in excluded]
    test_rows = [r for r in table_rows if split_of[r["instance"]] == "test"]
    noop = {r["proposal_id"] for r in records if r.get("label_kind") == "rule_noop"}
    return {"split_of": split_of, "primary": primary, "secondary": secondary, "excluded": recomputed,
            "holdout_nodes": sorted(splits.get("holdout_nodes") or []),
            "counts": {"test_instances": len((splits.get("instances") or {}).get("test") or []),
                       "test_table_rows": len(test_rows), "test_rows_seen_in_train_or_val": len(recomputed),
                       "labelled_test": len(secondary),
                       "labelled_test_seen_in_train_or_val": len(secondary) - len(primary),
                       "primary": len(primary), "secondary": len(secondary),
                       "primary_rule_noops": sum(p in noop for p in primary),
                       "secondary_rule_noops": sum(p in noop for p in secondary),
                       "test_rows_without_label": len(test_rows) - len(secondary)}}


# ---------------------------------------------------------------------------------------------- the arm's run

def _tree_sha(d: Path) -> str:
    files = sorted(p for p in d.rglob("*") if p.is_file()) if d.is_dir() else []
    if not files:
        raise TestEvalError(f"{d}: empty or missing (no best checkpoint)")
    return _sha_bytes("".join(f"{p.relative_to(d).as_posix()}\0{SD.sha256_file(p)}\n" for p in files).encode())


def run_record(run_dir: Path | str, data: Mapping) -> dict:
    """The selected run's binding: its report names this data directory; the temperature from
    ``best/temperature.json``; the sha256 of the files that fix the arm."""
    run_dir = Path(run_dir)
    refuse_sealed(run_dir)
    paths = {"sft_report": run_dir / "sft_report.json", "best_json": run_dir / "best.json",
             "temperature": run_dir / "best" / "temperature.json"}
    for p in paths.values():
        if not p.is_file():
            raise TestEvalError(f"{p}: missing (the arm is not a finished Stage S run)")
    report = json.loads(paths["sft_report"].read_text())
    if report.get("data_sha256") != data["manifest_sha256"]:
        raise TestEvalError(f"{run_dir}: the run was trained on another data directory")
    T = json.loads(paths["temperature"].read_text()).get("temperature")
    if not (isinstance(T, (int, float)) and not isinstance(T, bool) and math.isfinite(T) and T > 0):
        raise TestEvalError(f"{paths['temperature']}: temperature {T!r} must be a positive number")
    return {"run_dir": str(run_dir), "temperature": float(T), "lr": report.get("lr"), "seed": report.get("seed"),
            "sft_report_sha256": SD.sha256_file(paths["sft_report"]),
            "best_json_sha256": SD.sha256_file(paths["best_json"]),
            "temperature_json_sha256": SD.sha256_file(paths["temperature"]),
            "best_tree_sha256": _tree_sha(run_dir / "best")}


# ---------------------------------------------------------------------------------------------- logits file

def read_predictions(path: Path | str, data: Mapping, wanted: Sequence[str]) -> tuple[dict, dict]:
    """{proposal_id: logits} for exactly the labelled test proposals, and the file's header fields."""
    path = Path(path)
    SD.refuse_evaluation_path(path)
    refuse_sealed(path)
    raw = path.read_bytes()
    doc = json.loads(raw)
    if doc.get("schema") != PREDICTIONS_SCHEMA:
        raise TestEvalError(f"{path}: schema {doc.get('schema')!r} is not {PREDICTIONS_SCHEMA}")
    if doc.get("sft_data_sha256") != data["manifest_sha256"]:
        raise TestEvalError(f"{path}: logits were made for another data directory")
    logits = doc.get("logits")
    if not isinstance(logits, dict):
        raise TestEvalError(f"{path}: no logits mapping")
    missing, extra = sorted(set(wanted) - set(logits)), sorted(set(logits) - set(wanted))
    if missing or extra:
        raise TestEvalError(f"{path}: logits must cover exactly the labelled test proposals "
                            f"({len(missing)} missing, {len(extra)} not labelled test proposals)")
    out = {}
    for pid, z in logits.items():
        try:
            arr = np.asarray(z, dtype=float)
        except (TypeError, ValueError):
            raise TestEvalError(f"{path}: {pid}: not a numeric {N_BINS}-logit vector") from None
        if arr.shape != (N_BINS,) or not np.all(np.isfinite(arr)):
            raise TestEvalError(f"{path}: {pid}: not a finite {N_BINS}-logit vector")
        out[pid] = arr
    header = {k: doc.get(k) for k in ("arm", "model", "run", "replay")}
    header["sha256"] = _sha_bytes(raw)
    return out, header


def _check_header(header: Mapping, arm: str, run: Mapping, data: Mapping, table_files: Mapping,
                  wanted: Sequence[str]) -> None:
    if header.get("arm") != arm:
        raise TestEvalError(f"the logits file is for arm {header.get('arm')!r}, not {arm!r}")
    rec = header.get("run") or {}
    for key in ("sft_report_sha256", "best_json_sha256", "temperature_json_sha256", "best_tree_sha256",
                "temperature"):
        if rec.get(key) != run[key]:
            raise TestEvalError(f"the logits file's {key} differs from the run directory's (another checkpoint, "
                                f"temperature or run)")
    replay = header.get("replay") or {}
    if replay.get("table_sha256") != dict(table_files) or replay.get("ids_sha256") != _ids_sha(wanted):
        raise TestEvalError("the logits were made from prompts replayed against another table or proposal set")
    want_index = ((data["manifest"].get("prompts") or {}).get("sweep_index") or {}).get("sha256")
    if want_index is None and not data["synthetic"]:
        raise TestEvalError("the data manifest records no sweep index; real-label prompts cannot be bound")
    if want_index is not None and replay.get("sweep_index_sha256") != want_index:
        raise TestEvalError("the logits were made from prompts replayed from another sweep index")


# ---------------------------------------------------------------------------------------------- ledger

def material_key(table_files: Mapping, labels: Mapping, splits_sha: str | None) -> str:
    """The test material: the table, the label source and the split (not the data directory, which can be rebuilt)."""
    label_id = {k: labels.get(k) for k in ("kind", "sha256", "seed", "shift_z", "sweep")}
    return _sha_bytes(json.dumps({"table": dict(table_files), "labels": label_id, "splits": splits_sha},
                                 sort_keys=True).encode())


def _check_ledger_locked(fh, material: str, arm: str, best_sha: str, ledger: Path) -> None:
    fh.seek(0)
    for line in fh.read().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if e.get("material_sha256") == material and (e.get("arm") == arm or e.get("best_tree_sha256") == best_sha):
            raise TestEvalError(f"{ledger}: this arm or this checkpoint was already read on this test material "
                                f"({e.get('arm')!r}, {e.get('report')!r}); one test read per arm")


# ---------------------------------------------------------------------------------------------- evaluation

def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def _metrics(pids: Sequence[str], probs: Mapping[str, np.ndarray], targets: Mapping[str, np.ndarray],
             base: np.ndarray, prefix: str) -> dict:
    from r1.c3.train.sft import val_metrics
    if not pids:
        return {f"{prefix}n": 0}
    p = np.stack([probs[i] for i in pids])
    y = np.stack([targets[i] for i in pids])
    return {f"{prefix}n": len(pids), **val_metrics(p, y, base, prefix=prefix)}


def suite_function(suite_of: Callable[[str], str] | Mapping[str, str] | None) -> Callable[[str], str]:
    """A mapping refuses nodes it does not name; no mapping puts every node in "unassigned"."""
    if callable(suite_of):
        return suite_of
    if suite_of is None:
        return lambda node: "unassigned"
    mapping = dict(suite_of)

    def suite(node: str) -> str:
        if node not in mapping:
            raise TestEvalError(f"node {node!r} has no suite in the given mapping")
        return mapping[node]
    return suite


def breakdown(primary: Sequence[str], secondary: Sequence[str], node_of: Mapping[str, str],
              suite: Callable[[str], str], probs: Mapping[str, np.ndarray], targets: Mapping[str, np.ndarray],
              base: np.ndarray) -> dict:
    """Per node and per suite: primary metrics and both counts; a group present only among the excluded proposals
    gets ``test_n`` 0 and its secondary count."""
    groups: dict[str, dict[str, list[str]]] = {"node": {}, "suite": {}}
    for pid in primary:
        node = node_of[pid]
        groups["node"].setdefault(node, []).append(pid)
        groups["suite"].setdefault(suite(node), []).append(pid)
    secondary_n: dict[str, dict[str, int]] = {"node": {}, "suite": {}}
    for pid in secondary:
        node = node_of[pid]
        for kind, name in (("node", node), ("suite", suite(node))):
            secondary_n[kind][name] = secondary_n[kind].get(name, 0) + 1
    out = {kind: {name: {**_metrics(ids, probs, targets, base, "test_"),
                         "test_full_n": secondary_n[kind].get(name, 0)}
                  for name, ids in sorted(g.items())}
           for kind, g in groups.items()}
    for kind in ("node", "suite"):
        for name, n in secondary_n[kind].items():
            out[kind].setdefault(name, {"test_n": 0, "test_full_n": n})
    return out


def evaluate_test(data_dir: Path | str, table_dir: Path | str, label_source: SD.LabelSource,
                  predictions: Path | str, run_dir: Path | str, out_dir: Path | str, *, arm: str,
                  ledger: Path | str, suite_of: Callable[[str], str] | Mapping[str, str] | None = None,
                  allow_engineering_real_label_read: bool = False) -> dict:
    """Write ``<out_dir>/test_report.json`` (module docstring), append the read to ``ledger`` and return the
    report."""
    out_dir, ledger = Path(out_dir), Path(ledger)
    refuse_sealed(out_dir, ledger, table_dir)
    if ledger.name != LEDGER_NAME:
        raise TestEvalError(f"the test-read ledger must be named {LEDGER_NAME} (one per table)")
    if not (isinstance(arm, str) and arm.strip()):
        raise TestEvalError("arm must be a non-empty id")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise TestEvalError(f"{out_dir}: output directory exists and is not empty (one test read per arm)")
    data = read_data_dir(data_dir)
    manifest = data["manifest"]
    if not data["synthetic"] and str(manifest.get("label_status", "")).startswith("ENGINEERING_ONLY") \
            and not allow_engineering_real_label_read:
        raise TestEvalError("a real-label test read on ENGINEERING_ONLY data is refused in phase 1 "
                            "(P4-PHASE1-TEST: it would expose the shared evidence test partition)")
    table_rows, table_files = _pinned_table(data, table_dir)
    got_labels = check_label_source(manifest, label_source)
    records = label_source.label_records()
    pops = heldout_populations(table_rows, data["splits"], records)
    run = run_record(run_dir, data)
    material = material_key(table_files, got_labels, manifest.get("splits_sha256"))
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a+") as lock_fh:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)
        _check_ledger_locked(lock_fh, material, arm, run["best_tree_sha256"], ledger)
        report, text, header = _evaluate_locked(data, manifest, table_dir, table_rows, table_files, got_labels,
                                                records, pops, run, predictions, out_dir, arm, suite_of)
        entry = {"schema": LEDGER_SCHEMA, "material_sha256": material, "sft_data_sha256": data["manifest_sha256"],
                 "arm": arm, "best_tree_sha256": run["best_tree_sha256"], "logits_sha256": header["sha256"],
                 "report": str(out_dir / "test_report.json"), "report_sha256": _sha_bytes(text.encode())}
        lock_fh.seek(0, 2)
        lock_fh.write(json.dumps(entry, sort_keys=True) + "\n")
        lock_fh.flush()
        os.fsync(lock_fh.fileno())
    return report


def _evaluate_locked(data, manifest, table_dir, table_rows, table_files, got_labels, records, pops, run, predictions,
                     out_dir, arm, suite_of):
    logits, header = read_predictions(predictions, data, pops["secondary"])
    _check_header(header, arm, run, data, table_files, pops["secondary"])
    by_id = {r["proposal_id"]: r for r in table_rows}
    rec_of = {r["proposal_id"]: r for r in records}
    targets = {pid: np.asarray(SD.soft_target(rec_of[pid], by_id[pid]), dtype=float) for pid in pops["secondary"]}
    T = run["temperature"]
    scaled = {pid: _softmax(z / T) for pid, z in logits.items()}
    raw = {pid: _softmax(z) for pid, z in logits.items()}
    base = data["base"]
    suite = suite_function(suite_of)
    node_of = {pid: by_id[pid]["node"] for pid in pops["secondary"]}
    parts = breakdown(pops["primary"], pops["secondary"], node_of, suite, scaled, targets, base)
    report = {
        "schema": TEST_REPORT_SCHEMA, "label_status": manifest.get("label_status"),
        "ai_assisted": "AI-assisted (Claude)", "rule": RULE, "headline": "primary, at the fitted temperature",
        "test_target": TEST_TARGET, "arm": arm, "run": run,
        "data": {"dir": str(data["dir"]), "sft_data_sha256": data["manifest_sha256"],
                 "splits_sha256": manifest.get("splits_sha256"), "rows_sha256": manifest.get("rows_sha256"),
                 "cross_split_duplicates": data["policy"]},
        "table": {"dir": str(table_dir), "sha256": table_files},
        "labels": got_labels, "label_seeds": list(SD.LABEL_SEEDS), "evaluation_seeds_read": False,
        "logits": header,
        "populations": {**pops["counts"], "holdout_nodes": pops["holdout_nodes"],
                        "primary_ids_sha256": _ids_sha(pops["primary"]),
                        "secondary_ids_sha256": _ids_sha(pops["secondary"]),
                        "excluded_ids_sha256": _ids_sha(pops["excluded"]),
                        "exclusion_list_matches_recomputation": True, "split_matches_recomputation": True},
        "metrics_primary": _metrics(pops["primary"], scaled, targets, base, "test_"),
        "metrics_secondary": _metrics(pops["secondary"], scaled, targets, base, "test_full_"),
        "metrics_primary_raw": _metrics(pops["primary"], raw, targets, base, "test_"),
        "metrics_secondary_raw": _metrics(pops["secondary"], raw, targets, base, "test_full_"),
        "by_node": parts["node"], "by_suite": parts["suite"],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_json_safe(report), indent=1, sort_keys=True, allow_nan=False) + "\n"
    with (out_dir / "test_report.json").open("x") as fh:
        fh.write(text)
    return report, text, header


# ---------------------------------------------------------------------------------------------- logits writer

def replay_test_prompts(inputs: Mapping, *, tokenizers: Mapping | None, data_dir: Path | str,
                        table_dir: Path | str, label_source: SD.LabelSource) -> tuple[dict[str, object], dict]:
    """({proposal_id: DecisionPrompt} for the labelled test proposals, the replay record), replayed from the sweep
    like the training prompts, against the table pinned by the data manifest, each replayed proposal's features
    checked against its table row."""
    data = read_data_dir(data_dir)
    table_rows, table_files = _pinned_table(data, table_dir)
    check_label_source(data["manifest"], label_source)
    pops = heldout_populations(table_rows, data["splits"], label_source.label_records())
    index_sha = SD.sha256_file(inputs["index_path"])
    want_index = ((data["manifest"].get("prompts") or {}).get("sweep_index") or {}).get("sha256")
    if want_index is not None and index_sha != want_index:
        raise TestEvalError("the sweep index differs from the one the data directory was built from")
    replayed = SD.sweep_prompts(inputs, tokenizers=tokenizers, wanted=set(pops["secondary"]))
    missing = sorted(set(pops["secondary"]) - set(replayed))
    if missing:
        raise TestEvalError(f"{len(missing)} labelled test proposals have no replayed prompt, e.g. {missing[:3]}")
    by_id = {r["proposal_id"]: r for r in table_rows}
    for pid in pops["secondary"]:
        if SD.features_hash(replayed[pid][1]) != SD.features_hash(by_id[pid]["features"]):
            raise TestEvalError(f"{pid}: replayed features differ from the table row")
    record = {"table_sha256": dict(table_files), "sweep_index_sha256": index_sha, "n": len(pops["secondary"]),
              "ids_sha256": _ids_sha(pops["secondary"])}
    return {pid: replayed[pid][0] for pid in pops["secondary"]}, record


def predict_test(loader: Callable[[Path], object], prompts: Mapping[str, object], replay: Mapping,
                 run_dir: Path | str, data_dir: Path | str, out: Path | str, *, arm: str,
                 model_record: Mapping | None = None, batch_size: int = 16) -> dict:
    """Write the logits file of one arm from its best model, loaded here by ``loader(run_dir / "best")``, with the
    run's binding (``run_record``, taken before and after loading) and the replay record."""
    from r1.c3.train.sft import predict_logits
    out = Path(out)
    if out.exists():
        raise TestEvalError(f"{out}: exists (never overwritten)")
    data = read_data_dir(data_dir)
    run = run_record(run_dir, data)
    if replay.get("ids_sha256") != _ids_sha(list(prompts)):
        raise TestEvalError("the prompts are not the replayed set")
    model = loader(Path(run_dir) / "best")
    if run_record(run_dir, data) != run:
        raise TestEvalError(f"{run_dir}: the run directory changed while the model was loaded")
    ids = sorted(prompts)
    z = predict_logits(model, [prompts[i] for i in ids], batch_size=batch_size)
    doc = {"schema": PREDICTIONS_SCHEMA, "sft_data_sha256": data["manifest_sha256"], "arm": arm,
           "model": dict(model_record or {}), "run": run, "replay": dict(replay),
           "logits": {i: [float(v) for v in row] for i, row in zip(ids, z)}}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as fh:
        fh.write(json.dumps(doc, sort_keys=True) + "\n")
    return doc
