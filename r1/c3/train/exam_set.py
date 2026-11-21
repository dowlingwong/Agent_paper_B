"""The P.3b decision-model exam set, drawn inside P3 train (PRE-SPLIT A; R1-MAIN-PROPOSER-ITEMS; spec §5.3).

AI-assisted (Claude). ENGINEERING code that writes a membership file; it reads table rows only (``sft_data.load_table``:
proposal ids, nodes, instance seeds, rule flags and configuration hashes) and **no label, audit or evaluation value**.
The membership is a function of the table's rows, the pinned P3 split file and a salt, so the coordinating session can
regenerate it and commit it with its sha256 (Portal Track P runbook Phase 6 (b)); the exam's labels (``y_train``, the
label seeds only) come later from the receipted train/dev partition of the release step (PRE-STAGE A).

Rule (spec §5.3: "≈ 400–500 audited proposals from the training partition, ≥ 3 nodes, frozen as ``exam_member``;
internal split 70 / 30 by instance seed, grouped by edit hash; labels ``y_train`` only; ``y_eval`` and test instances
are not touched"; R1-MAIN-PROPOSER-ITEMS: "the P.3b exam set is drawn from the training partition"):

1. **Universe.** The rows of one source's table (``source``: an author choice, EX-SOURCE in the report; bound to the
   table pin, whose name begins with the source, ``sweep1_v3`` → ``sweep1``) whose instance is
   a **P3 train** instance of a T0 node (``p3_split``; an instance outside the split file is refused) and which are
   audited proposals, i.e. not rule-skips (no-ops and within-campaign duplicates carry no audit label).
2. **Instances.** The P3 train instances with at least one eligible proposal, ordered by
   ``sha256("trackp_exam/v1:" + <instance id>)``. The exam takes the shortest prefix with at least ``TARGET_MIN`` = 400
   eligible proposals and at least ``MIN_NODES`` = 3 nodes; whole instances (both memory-mode campaigns) enter or not.
   If every train instance together falls short, all are taken and ``below_target`` is set (a STOP for the exam:
   the author decides); a prefix above ``TARGET_MAX`` = 500 sets ``above_target`` (reported).
3. **Internal split.** In the same order, the first ``(7 n + 5) // 10`` exam instances (0.7 n rounded half up, in
   integers) are exam-train, the rest exam-val; an empty exam-val is a STOP (``write`` refuses it).
   Grouping by edit hash follows R1-TRACKP-SFT-DUP (``heldout_excludes_seen``): an exam-val proposal whose
   (node, incumbent hash, candidate hash) occurs on any table row of an exam-train instance is ``val_seen`` (kept, but
   outside the primary exam-val population, as in the SFT builder).

4. **Labels (later).** At the P.3b label join every member must have a ``y_train`` record (``check_labelled``, by
   proposal id only); a missing one is a STOP.

The rule's EX-* choices (source, ``val_seen`` key, instance-count split, prefix stop, no-op exclusion, rounding) are
proposed items for the author (report ``TRACKP_P3_20261121.md``), not spec text.

``python -m r1.c3.train.exam_set write --table DIR --table-pin sweep1_v3 --source sweep1 --out FILE`` writes the file
(refused when ``below_target`` or the exam-val is empty; ``above_target`` is printed) and prints its sha256;
``verify`` regenerates and compares bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from r1.c3 import p3_split
from r1.c3.arms import rule_skip

SCHEMA = "trackp_exam_set/v1"
SALT = "trackp_exam/v1"
TARGET_MIN, TARGET_MAX, MIN_NODES = 400, 500, 3
TRAIN_SHARE = 0.7          # applied as (7 n + 5) // 10
SOURCES = ("sweep1", "sweep2")
DEFAULT_SFT_CONFIG = Path(__file__).resolve().parents[3] / "r1" / "scripts" / "configs" / "trackp_sft.json"


class ExamSetError(ValueError):
    """A refusal: rows outside the P3 split file, an unknown source, or a malformed table."""


def _key(row: dict) -> str:
    return f"{row['node']}|{row['incumbent_hash']}|{row['candidate_hash']}"     # sft_data.dup_key


def draw(rows: list[dict], *, source: str, proposals_sha256: str, split_path=None) -> dict:
    """The exam-set membership (module docstring) as a JSON-ready dict."""
    if source not in SOURCES:
        raise ExamSetError(f"source must be one of {SOURCES} (EX-SOURCE)")
    split = p3_split.load(split_path) if split_path else p3_split.load()
    assign = p3_split.assignment(split)
    by_inst, keys_by_inst, seen = {}, {}, set()
    for r in rows:
        pid = r["proposal_id"]
        if pid in seen:
            raise ExamSetError(f"duplicate proposal id {pid}")
        seen.add(pid)
        inst = p3_split.instance_id(r["node"], r["instance_seed"])
        if r.get("instance") not in (None, inst):
            raise ExamSetError(f"{pid}: instance {r.get('instance')!r} is not {inst!r}")
        if inst not in assign or assign[inst]["node"] != r["node"]:
            raise ExamSetError(f"{pid}: instance {inst} is not in the P3 split file")
        if assign[inst]["tier"] != "T0" or assign[inst]["split"] != "train":
            continue
        keys_by_inst.setdefault(inst, set()).add(_key(r))
        if not rule_skip(r):
            by_inst.setdefault(inst, []).append(r)
    order = sorted(by_inst, key=lambda i: hashlib.sha256(f"{SALT}:{i}".encode()).hexdigest())
    chosen, n_items = [], 0
    for inst in order:
        chosen.append(inst)
        n_items += len(by_inst[inst])
        if n_items >= TARGET_MIN and len({assign[i]["node"] for i in chosen}) >= MIN_NODES:
            break
    nodes = sorted({assign[i]["node"] for i in chosen})
    below = n_items < TARGET_MIN or len(nodes) < MIN_NODES
    n_train = (7 * len(chosen) + 5) // 10
    exam_train, exam_val = chosen[:n_train], chosen[n_train:]
    train_keys = set().union(*(keys_by_inst[i] for i in exam_train)) if exam_train else set()
    items = {}
    for inst in chosen:
        for r in by_inst[inst]:
            part = "train" if inst in exam_train else ("val_seen" if _key(r) in train_keys else "val")
            items[r["proposal_id"]] = {"instance": inst, "node": r["node"], "exam_split": part}
    counts = {"items": len(items), "instances": len(chosen), "exam_train_instances": len(exam_train),
              "exam_val_instances": len(exam_val),
              "by_split": {s: sum(v["exam_split"] == s for v in items.values()) for s in ("train", "val", "val_seen")},
              "by_node": {n: sum(v["node"] == n for v in items.values()) for n in nodes},
              "eligible_p3_train_proposals": sum(len(v) for v in by_inst.values())}
    return {"schema": SCHEMA, "source": source, "salt": SALT,
            "rule": "P3 train instances of one source's table, audited (non rule-skip) proposals; instances ordered by "
                    "sha256('trackp_exam/v1:' + instance); shortest prefix with >= 400 proposals and >= 3 nodes; first "
                    "(7 n + 5) // 10 instances exam-train, the rest exam-val; exam-val proposals whose (node, incumbent, "
                    "candidate) occurs on an exam-train instance are val_seen (R1-TRACKP-SFT-DUP)",
            "targets": {"min": TARGET_MIN, "max": TARGET_MAX, "min_nodes": MIN_NODES, "train_share": TRAIN_SHARE},
            "below_target": below, "above_target": n_items > TARGET_MAX, "empty_exam_val": not exam_val,
            "split_file": {"path": "r1/c3/splits/c3_p3_split_v1.json", "sha256": p3_split.P3_SPLIT_SHA256},
            "table_proposals_sha256": proposals_sha256, "nodes": nodes,
            "instances": {"exam_train": exam_train, "exam_val": exam_val}, "counts": counts, "items": items}


def render(exam: dict) -> bytes:
    return (json.dumps(exam, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode()


def check_labelled(exam: dict, labelled_ids) -> None:
    """The P.3b label join (m4): every member must carry a ``y_train`` record; ids only, no value is read here."""
    missing = sorted(set(exam["items"]) - set(labelled_ids))
    if missing:
        raise ExamSetError(f"{len(missing)} exam members have no y_train record (STOP): {missing[:5]}")


def from_table(table_dir, *, source: str, table_pin: str, sft_config=None, split_path=None) -> dict:
    """The membership of a pinned table (``tables`` of the Track P SFT config); the source is the pin's sweep."""
    from r1.c3.train import sft_data
    tables = json.loads(Path(sft_config or DEFAULT_SFT_CONFIG).read_text())["tables"]
    if table_pin not in tables:
        raise ExamSetError(f"unknown table pin {table_pin!r}; known: {sorted(tables)}")
    if table_pin.split("_")[0] != source:
        raise ExamSetError(f"source {source!r} is not the table pin's sweep ({table_pin}) (EX-SOURCE)")
    rows, files = sft_data.load_table(table_dir, tables[table_pin]["sha256"])
    exam = draw(rows, source=source, proposals_sha256=files["proposals.jsonl"], split_path=split_path)
    exam["table_pin"] = table_pin
    return exam


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("write", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--table", required=True)
        p.add_argument("--table-pin", required=True)
        p.add_argument("--source", required=True, choices=SOURCES)
        p.add_argument("--sft-config", default=str(DEFAULT_SFT_CONFIG))
        p.add_argument("--out" if name == "write" else "--file", required=True)
    a = ap.parse_args(argv)
    try:
        exam = from_table(a.table, source=a.source, table_pin=a.table_pin, sft_config=a.sft_config)
    except (ExamSetError, ValueError) as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 2
    raw = render(exam)
    if a.cmd == "write":
        out = Path(a.out)
        if out.exists():
            print(f"{out} exists; a membership file is written once", file=sys.stderr)
            return 2
        if exam["below_target"] or exam["empty_exam_val"]:
            print(f"STOP: below_target={exam['below_target']} empty_exam_val={exam['empty_exam_val']} "
                  f"({exam['counts']['items']} items, {len(exam['nodes'])} nodes): the author decides; nothing written",
                  file=sys.stderr)
            return 2
        out.write_bytes(raw)
        if exam["above_target"]:
            print(f"FLAG above_target: {exam['counts']['items']} items > {TARGET_MAX} (reported)", file=sys.stderr)
        print(hashlib.sha256(raw).hexdigest())
        return 0
    same = Path(a.file).read_bytes() == raw
    print("OK " + hashlib.sha256(raw).hexdigest() if same else "DIFFERS")
    return 0 if same else 2


if __name__ == "__main__":
    raise SystemExit(main())
