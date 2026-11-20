"""Track P P.4 test evaluator: the held-out test number under R1-TRACKP-SFT-DUP. ENGINEERING_ONLY on sweep 1;
AI-assisted (Claude).

The SFT data directory (``sft_data.build_sft_data``) holds no test rows; it lists the test instances and, under the
decided policy ``heldout_excludes_seen``, the test proposals whose (node, incumbent, candidate) key also occurs on
a train or val instance (``splits.json`` ``test_proposals_seen_in_train_or_val``). This module turns one trained
arm's predictions on the test proposals into the test report:

* **primary** test population (the headline number, R1-TRACKP-SFT-DUP): the labelled test proposals **not** in the
  exclusion list;
* **secondary** population: every labelled test proposal, duplicates of the training data included;
* the same belief metrics as the Stage S validation (``sft.val_metrics``: RPS, RPS skill against the training base
  rate, NLL, all-bins and top-1 ECE, PIT histogram, predictive and label sd, width ratio), with the prefix
  ``test_`` (primary) and ``test_full_`` (secondary);
* the same metrics per node and per suite (``suite_of``) on the primary population, with the counts of both.

Bindings and refusals (each is a STOP, ``TestEvalError``):

* the data directory: schema, ``rows.jsonl`` and ``splits.json`` sha256 against ``sft_data.json``; the policy must
  be ``heldout_excludes_seen`` unless the labels are synthetic;
* the table: loaded with the data manifest's table hashes as pins (``sft_data.load_table`` runs the R1-BX-D8 and
  sealed-path guards); every table instance must be in the recorded split, and the train/val/test instances of
  ``splits.json`` must cover the table;
* **the exclusion list is recomputed** from the table and the recorded split (a key is seen if it occurs on any
  table row of a train or val instance, labelled or not, as in the builder) and must equal ``splits.json``'s list;
* the labels: the label source's provenance must equal the data manifest's (same label block sha256 and
  completion, or the same synthetic seed); the label block is read through ``LabelBlockSource``, which never opens
  evaluation-seed files and asks for the R1-BX-D8 confirmation before a sweep-2 block. The test targets are the
  soft labels from the label seeds 7001–7005 of the test instances, exactly as for training; **no value from
  7006–7010 is read** (R1-MAIN-PROPOSER (e), R1-TRACKP-SFT-DEV);
* the predictions file (``trackp_sft_test_predictions/v1``): bound to this data directory (``sft_data_sha256``),
  one 12-bin probability vector per labelled test proposal and no other id, finite, non-negative, summing to 1;
* the output directory is new; the report is written once and never overwritten (one test read per arm).

``predict_test(model, prompts, temperature, data_dir, out)`` writes the predictions file from a trained model
(``sft.predict_logits``, softmax at the selected temperature); ``replay_test_prompts`` replays the test proposals'
prompts from the sweep. Neither is needed by ``evaluate_test``, which works from the file alone.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np

from r1.c3.train import sft_data as SD

TEST_REPORT_SCHEMA = "trackp_sft_test_report/v1"
PREDICTIONS_SCHEMA = "trackp_sft_test_predictions/v1"
N_BINS = 12
RULE = ("R1-TRACKP-SFT-DUP: primary test population = labelled test proposals not in "
        "splits.json test_proposals_seen_in_train_or_val; secondary = every labelled test proposal")


class TestEvalError(SD.SFTDataError):
    """A STOP of the test evaluator."""

    __test__ = False  # not a pytest class


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _ids_sha(ids: Sequence[str]) -> str:
    return _sha_bytes("\n".join(sorted(ids)).encode())


# ---------------------------------------------------------------------------------------------- data directory

def read_data_dir(data_dir: Path | str) -> dict:
    """The data manifest, the splits record and the training base rate, with the hash checks of ``load_sft_data``
    (without torch)."""
    data_dir = Path(data_dir)
    raw_manifest = (data_dir / "sft_data.json").read_bytes()
    manifest = json.loads(raw_manifest)
    if manifest.get("schema") != SD.SFT_DATA_SCHEMA:
        raise TestEvalError(f"{data_dir}: not an SFT data directory")
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
            "policy": policy, "base": M.base_rate(np.asarray(y_train, dtype=float))}


# ---------------------------------------------------------------------------------------------- populations

def heldout_populations(table_rows: Sequence[Mapping], splits: Mapping, records: Sequence[Mapping]) -> dict:
    """Primary and secondary test populations; the exclusion list recomputed and compared with ``splits.json``."""
    instances = splits.get("instances") or {}
    split_of: dict[str, str] = {}
    for name in SD.SPLITS:
        for inst in instances.get(name) or []:
            if inst in split_of:
                raise TestEvalError(f"instance {inst} is in two splits")
            split_of[inst] = name
    outside = sorted({r["instance"] for r in table_rows} - set(split_of))
    if outside:
        raise TestEvalError(f"table instances outside the recorded split: {outside[:5]}")
    seen = {SD.dup_key(r) for r in table_rows if split_of[r["instance"]] in ("train", "val")}
    recomputed = sorted(r["proposal_id"] for r in table_rows
                        if split_of[r["instance"]] == "test" and SD.dup_key(r) in seen)
    recorded = splits.get("test_proposals_seen_in_train_or_val")
    if recorded is None or sorted(recorded) != recomputed:
        n = None if recorded is None else len(recorded)
        raise TestEvalError(f"the exclusion list differs from the recomputation ({n} recorded, "
                            f"{len(recomputed)} recomputed)")
    by_id = {r["proposal_id"]: r for r in table_rows}
    unknown = sorted(r["proposal_id"] for r in records if r["proposal_id"] not in by_id)
    if unknown:
        raise TestEvalError(f"{len(unknown)} labelled proposals are not in the table, e.g. {unknown[:3]}")
    excluded = set(recomputed)
    secondary = sorted(r["proposal_id"] for r in records if split_of[by_id[r["proposal_id"]]["instance"]] == "test")
    primary = [p for p in secondary if p not in excluded]
    test_rows = [r for r in table_rows if split_of[r["instance"]] == "test"]
    return {"split_of": split_of, "primary": primary, "secondary": secondary, "excluded": recomputed,
            "holdout_nodes": sorted(splits.get("holdout_nodes") or []),
            "counts": {"test_instances": len(instances.get("test") or []), "test_table_rows": len(test_rows),
                       "test_rows_seen_in_train_or_val": len(recomputed),
                       "labelled_test": len(secondary), "labelled_test_seen_in_train_or_val": len(secondary)
                       - len(primary), "primary": len(primary), "secondary": len(secondary),
                       "test_rows_without_label": len(test_rows) - len(secondary)}}


# ---------------------------------------------------------------------------------------------- predictions

def read_predictions(path: Path | str, data: Mapping, wanted: Sequence[str]) -> tuple[dict, dict]:
    """{proposal_id: probs} for exactly the labelled test proposals, and the file's header fields."""
    path = Path(path)
    SD.refuse_evaluation_path(path)
    raw = path.read_bytes()
    doc = json.loads(raw)
    if doc.get("schema") != PREDICTIONS_SCHEMA:
        raise TestEvalError(f"{path}: schema {doc.get('schema')!r} is not {PREDICTIONS_SCHEMA}")
    if doc.get("sft_data_sha256") != data["manifest_sha256"]:
        raise TestEvalError(f"{path}: predictions were made for another data directory")
    preds = doc.get("predictions")
    if not isinstance(preds, dict):
        raise TestEvalError(f"{path}: no predictions mapping")
    missing, extra = sorted(set(wanted) - set(preds)), sorted(set(preds) - set(wanted))
    if missing or extra:
        raise TestEvalError(f"{path}: predictions must cover exactly the labelled test proposals "
                            f"({len(missing)} missing, {len(extra)} not labelled test proposals)")
    out = {}
    for pid, p in preds.items():
        arr = np.asarray(p, dtype=float)
        if arr.shape != (N_BINS,) or not np.all(np.isfinite(arr)) or (arr < 0).any() or abs(arr.sum() - 1.0) > 1e-6:
            raise TestEvalError(f"{path}: {pid}: not a {N_BINS}-bin probability vector")
        out[pid] = arr
    header = {k: doc.get(k) for k in ("model", "temperature", "arm", "created_utc")}
    header["sha256"] = _sha_bytes(raw)
    return out, header


# ---------------------------------------------------------------------------------------------- evaluation

def _metrics(pids: Sequence[str], probs: Mapping[str, np.ndarray], targets: Mapping[str, np.ndarray],
             base: np.ndarray, prefix: str) -> dict:
    from r1.c3.train.sft import val_metrics
    if not pids:
        return {f"{prefix}n": 0}
    p = np.stack([probs[i] for i in pids])
    y = np.stack([targets[i] for i in pids])
    return {f"{prefix}n": len(pids), **val_metrics(p, y, base, prefix=prefix)}


def evaluate_test(data_dir: Path | str, table_dir: Path | str, label_source: SD.LabelSource,
                  predictions: Path | str, out_dir: Path | str, *,
                  suite_of: Callable[[str], str] | Mapping[str, str] | None = None) -> dict:
    """Write ``<out_dir>/test_report.json`` (module docstring) and return it."""
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise TestEvalError(f"{out_dir}: output directory exists and is not empty (one test read per arm)")
    data = read_data_dir(data_dir)
    manifest = data["manifest"]
    pins = ((manifest.get("table") or {}).get("sha256") or {})
    if "proposals.jsonl" not in pins:
        raise TestEvalError(f"{data_dir}: the data manifest records no table hash; the test cannot be bound")
    table_rows, table_files = SD.load_table(table_dir, pins=pins)
    want_labels = manifest.get("labels") or {}
    got_labels = label_source.provenance()
    for key in ("kind", "sha256", "seed", "shift_z", "sweep"):
        if want_labels.get(key) != got_labels.get(key):
            raise TestEvalError(f"label source {key} {got_labels.get(key)!r} differs from the data manifest's "
                                f"{want_labels.get(key)!r}")
    if want_labels.get("kind") == "label_block" and \
            (want_labels.get("completion") or {}).get("sha256") != (got_labels.get("completion") or {}).get("sha256"):
        raise TestEvalError("label block completion record differs from the data manifest's")
    records = label_source.label_records()
    pops = heldout_populations(table_rows, data["splits"], records)
    probs, header = read_predictions(predictions, data, pops["secondary"])
    by_id = {r["proposal_id"]: r for r in table_rows}
    rec_of = {r["proposal_id"]: r for r in records}
    targets = {pid: np.asarray(SD.soft_target(rec_of[pid], by_id[pid]), dtype=float) for pid in pops["secondary"]}
    base = data["base"]
    suite = (suite_of if callable(suite_of) else (lambda n, m=dict(suite_of or {}): m.get(n, "unassigned")))
    groups: dict[str, dict[str, list[str]]] = {"node": {}, "suite": {}}
    for pid in pops["primary"]:
        node = by_id[pid]["node"]
        groups["node"].setdefault(node, []).append(pid)
        groups["suite"].setdefault(suite(node), []).append(pid)
    secondary_n = {"node": {}, "suite": {}}
    for pid in pops["secondary"]:
        node = by_id[pid]["node"]
        secondary_n["node"][node] = secondary_n["node"].get(node, 0) + 1
        secondary_n["suite"][suite(node)] = secondary_n["suite"].get(suite(node), 0) + 1
    breakdown = {kind: {name: {**_metrics(ids, probs, targets, base, "test_"),
                               "test_full_n": secondary_n[kind].get(name, 0)}
                        for name, ids in sorted(g.items())}
                 for kind, g in groups.items()}
    for kind in ("node", "suite"):   # groups present only among the excluded proposals
        for name, n in secondary_n[kind].items():
            breakdown[kind].setdefault(name, {"test_n": 0, "test_full_n": n})
    report = {
        "schema": TEST_REPORT_SCHEMA, "label_status": manifest.get("label_status"),
        "ai_assisted": "AI-assisted (Claude)", "rule": RULE, "headline": "primary",
        "data": {"dir": str(data["dir"]), "sft_data_sha256": data["manifest_sha256"],
                 "splits_sha256": manifest.get("splits_sha256"), "rows_sha256": manifest.get("rows_sha256"),
                 "cross_split_duplicates": data["policy"]},
        "table": {"dir": str(table_dir), "sha256": table_files},
        "labels": got_labels, "label_seeds": list(SD.LABEL_SEEDS), "evaluation_seeds_read": False,
        "predictions": header,
        "populations": {**pops["counts"], "holdout_nodes": pops["holdout_nodes"],
                        "primary_ids_sha256": _ids_sha(pops["primary"]),
                        "secondary_ids_sha256": _ids_sha(pops["secondary"]),
                        "excluded_ids_sha256": _ids_sha(pops["excluded"]),
                        "exclusion_list_matches_recomputation": True},
        "metrics_primary": _metrics(pops["primary"], probs, targets, base, "test_"),
        "metrics_secondary": _metrics(pops["secondary"], probs, targets, base, "test_full_"),
        "by_node": breakdown["node"], "by_suite": breakdown["suite"],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=1, sort_keys=True, default=float) + "\n"
    with (out_dir / "test_report.json").open("x") as fh:
        fh.write(text)
    return report


# ---------------------------------------------------------------------------------------------- predictions writer

def replay_test_prompts(inputs: Mapping, *, tokenizers: Mapping | None, data_dir: Path | str,
                 table_rows: Sequence[Mapping], label_source: SD.LabelSource) -> dict[str, object]:
    """{proposal_id: DecisionPrompt} for the labelled test proposals, replayed from the sweep like the training
    prompts (``sft_data.sweep_prompts``)."""
    data = read_data_dir(data_dir)
    pops = heldout_populations(table_rows, data["splits"], label_source.label_records())
    replayed = SD.sweep_prompts(inputs, tokenizers=tokenizers, wanted=set(pops["secondary"]))
    missing = sorted(set(pops["secondary"]) - set(replayed))
    if missing:
        raise TestEvalError(f"{len(missing)} labelled test proposals have no replayed prompt, e.g. {missing[:3]}")
    return {pid: replayed[pid][0] for pid in pops["secondary"]}


def predict_test(model, prompts: Mapping[str, object], temperature: float, data_dir: Path | str, out: Path | str,
                 *, model_record: Mapping | None = None, arm: str | None = None, batch_size: int = 16) -> dict:
    """Write the predictions file of one arm: softmax(logits / T) at the arm's selected temperature."""
    from r1.c3.train.sft import _softmax, predict_logits
    out = Path(out)
    if out.exists():
        raise TestEvalError(f"{out}: exists (never overwritten)")
    if not (isinstance(temperature, (int, float)) and math.isfinite(temperature) and temperature > 0):
        raise TestEvalError(f"temperature {temperature!r} must be a positive number")
    data = read_data_dir(data_dir)
    ids = sorted(prompts)
    probs = _softmax(predict_logits(model, [prompts[i] for i in ids], batch_size=batch_size) / float(temperature))
    doc = {"schema": PREDICTIONS_SCHEMA, "sft_data_sha256": data["manifest_sha256"], "arm": arm,
           "model": dict(model_record or {}), "temperature": float(temperature),
           "predictions": {i: [float(v) for v in p] for i, p in zip(ids, probs)}}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as fh:
        fh.write(json.dumps(doc, sort_keys=True) + "\n")
    return doc
