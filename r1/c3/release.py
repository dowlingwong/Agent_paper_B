"""Staged label release and partition-reading locks (PRE-STAGE A of the sweep-2 analysis preregistration, §4, §6, §8).

AI-assisted (Claude). For **both sources** (sweep 1 and sweep 2 for T0; the G.5 tables for T1), until the test release
row exists, readers get the label block of **train and dev instances only** and **no evaluation value of any
instance**. Mechanism:

* **Release step** (``release``). Run once per (source, stage) when its PLAN row exists on the committed checkout:
  - stage ``traindev`` (row R1-S2-LABELS-TRAINDEV-RELEASE for T0, R1-T1-LABELS-UNSEAL for T1) writes
    ``label_block.traindev.jsonl``: the label rows of P3 train and dev instances, byte-identical lines;
  - stage ``test`` (row R1-S2-LABELS-TEST-RELEASE / R1-T1-LABELS-TEST-RELEASE, which also cites the arms-frozen
    record) writes ``label_block.test.jsonl`` and ``evaluation_block.all.jsonl``; it needs the traindev receipt;
  - each writes ``RECEIPT.json``: the row id and the sha256 of its decision text, the preregistration, split file,
    release-code commit (and arms-frozen record) it binds, input and output sha256s, counts, and the integrity result.
  Before writing, the step checks: the D8 confirmation (gate v3.1), the release row's exact text, the preregistration
  frozen (``frozen: true``, its ``split_file`` naming the pinned P3 split sha256, its ``gate_input_builder_sha256``
  and ``gate_sha256`` equal to the committed files), the release-code commit (an ancestor of HEAD with this file's
  bytes), and the source's **integrity check**.
* **Integrity carve-out** (§6). ``audit.verify_evidence_completion`` opens ``runs.jsonl`` and
  ``evaluation_block.jsonl``; before the test release row it runs only inside the release step
  (``integrity_context``), which records pass/fail, counts and hashes, never a value. Registered checks:
  ``sweep1`` (the sweep-1 B.2 audit). A source with no registered check (sweep 2, G.5 until their audits and checks
  are reviewed) is a STOP at release.
* **Readers** (``open_partition``, ``builder_source``) open only receipted partitions: the receipt's output sha256s,
  the row (still present, same text), the preregistration sha256 and the release code are re-checked on every open.
* **Locks on the existing readers** (``guard_raw_label_path``, ``require_integrity_or_test_release``): a raw
  ``label_block.jsonl``, ``evaluation_block.jsonl`` or ``runs.jsonl`` of an audit is refused unless the test release
  row of its tier exists (inside the release step for the integrity check). Used by ``sft_data.LabelBlockSource``,
  ``offline_eval.assemble``, ``env.label_rows``, ``ni_masking.load_audits`` and ``audit.verify_evidence_completion``.

What may be read before release: counts and divergence diagnostics without values (the receipts' counts).
A lock forbids reads; it cannot prevent a deliberate read, which is a STOP (§6).
"""
from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from r1.c3 import p3_split
from r1.c3.analysis_guard import _author_heading, _decision_header, refuse_sealed, require_d8_confirmation
from r1.harness import REPO

RECEIPT_SCHEMA = "r1_c3_release_receipt/v1"
PREREG_PATH = "docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md"
RELEASE_PATH = "r1/c3/release.py"
BUILDER_PATH = "r1/c3/gate_input_builder.py"
GATE_PATH = "r1/c3/gate.py"
STAGES = ("traindev", "test")
TIERS = ("T0", "T1")
SOURCES = {"sweep1": "T0", "sweep2": "T0", "g5": "T1"}
ROWS = {("T0", "traindev"): "R1-S2-LABELS-TRAINDEV-RELEASE", ("T0", "test"): "R1-S2-LABELS-TEST-RELEASE",
        ("T1", "traindev"): "R1-T1-LABELS-UNSEAL", ("T1", "test"): "R1-T1-LABELS-TEST-RELEASE"}
WHAT = {"T0": "both sources (sweep 1 and sweep 2)", "T1": "the G.5 T1 tables"}
RAW_NAMES = frozenset({"label_block.jsonl", "evaluation_block.jsonl", "runs.jsonl"})
PARTITIONS = {"traindev": ("label_block.traindev.jsonl",),
              "test": ("label_block.test.jsonl", "evaluation_block.all.jsonl")}
COMPLETION_KEEP = ("schema", "label", "label_block_sha256", "evaluation_block_sha256", "proposals_sha256",
                   "build_sha256", "configs_sha256", "plan_sha256", "counts", "label_seeds", "evaluation_seeds",
                   "index_sha256", "classification_sha256")
_HEX = r"[0-9a-f]{64}"
_COMMIT = r"(?:[0-9a-f]{40}|[0-9a-f]{64})"
_INTEGRITY = contextvars.ContextVar("r1_c3_release_integrity", default=False)


class ReleaseStop(RuntimeError):
    """A PRE-STAGE A STOP: nothing is written or read."""


# --------------------------------------------------------------------------------------------- row templates

def row_pattern(tier: str, stage: str) -> str:
    """The exact decision text of a release row (the §8 drafts), as a regex with named groups prereg, split,
    commit (and arms_path, arms for a test row)."""
    pre = (r"Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration "
           r"\(`" + re.escape(PREREG_PATH) + r"`, sha256 `(?P<prereg>" + _HEX + r")`\)")
    arms = r", after the arms-frozen record `(?P<arms_path>docs/r1/[A-Za-z0-9_./-]+\.md)` \(sha256 `(?P<arms>" + _HEX + r")`\)"
    tail = (r", partitioned by the P3 split file \(sha256 `(?P<split>" + _HEX + r")`\) with the release step "
            r"`r1/c3/release\.py` @ `(?P<commit>" + _COMMIT + r")`\.")
    what = re.escape(WHAT[tier])
    if stage == "traindev":
        return (pre + r": the train and dev label blocks of " + what + tail +
                r" No test label and no evaluation value is released by this row\.")
    return pre + arms + r": the test label blocks and every evaluation block of " + what + tail


def row_text(tier: str, stage: str, *, prereg: str, split: str, commit: str, arms_path: str | None = None,
             arms: str | None = None) -> str:
    """The decision text of a release row with the values filled in (for the drafts and tests)."""
    head = (f"Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`{PREREG_PATH}`, "
            f"sha256 `{prereg}`)")
    tail = f", partitioned by the P3 split file (sha256 `{split}`) with the release step `r1/c3/release.py` @ `{commit}`."
    if stage == "traindev":
        return (head + f": the train and dev label blocks of {WHAT[tier]}" + tail +
                " No test label and no evaluation value is released by this row.")
    return (head + f", after the arms-frozen record `{arms_path}` (sha256 `{arms}`): the test label blocks and every "
            f"evaluation block of {WHAT[tier]}" + tail)


# ---------------------------------------------------------------------------------------- committed authority

def _git(*args, root=None) -> bytes:
    return subprocess.check_output(["git", "-C", str(root or REPO), *args], stderr=subprocess.DEVNULL)


def _committed(path: str, root=None) -> bytes:
    """The bytes of ``path`` at HEAD, refused unless the working file is the same regular file."""
    root = Path(root or REPO)
    f = root / path
    refuse_sealed(f)
    if f.is_symlink() or not f.is_file():
        raise ReleaseStop(f"STOP: {path} is absent or a symlink")
    try:
        head = _git("rev-parse", "--verify", "HEAD", root=root).decode().strip()
        entry = _git("ls-tree", "-z", head, "--", path, root=root)
        if not re.fullmatch(rb"(?:100644|100755) blob [0-9a-f]{40,64}\t" + re.escape(path.encode()) + rb"\x00", entry):
            raise ReleaseStop(f"STOP: {path} is not a regular committed file")
        data = _git("show", f"{head}:{path}", root=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseStop(f"STOP: committed {path} unavailable") from exc
    if data != f.read_bytes():
        raise ReleaseStop(f"STOP: {path} differs from committed HEAD")
    return data


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def author_rows(plan: str) -> list[tuple[str, str]]:
    """(id, decision) of every row of a dated author decision table in PLAN §10, with the structural rules of
    ``analysis_guard._confirmation_commit`` (fenced code, HTML blocks, comments and indented code are ignored)."""
    section = False; dated = 0; fenced = None; comment = False; html = None; header = None; table = False
    out = []
    for raw in plan.splitlines():
        if html:
            if re.search(r"</" + re.escape(html) + r"\s*>", raw, re.I):
                html = None
            header = None; table = False; continue
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", raw)
        if fenced:
            if re.match(r"^ {0,3}" + re.escape(fenced[0]) + r"{" + str(len(fenced)) + r",}\s*$", raw):
                fenced = None
            header = None; table = False; continue
        if marker:
            fenced = marker.group(1); header = None; table = False; continue
        line, rest = "", raw
        while rest:
            if comment:
                pos = rest.find("-->")
                if pos < 0:
                    rest = ""; break
                rest = rest[pos + 3:]; comment = False; continue
            pos = rest.find("<!--")
            if pos < 0:
                line += rest; break
            line += rest[:pos]; rest = rest[pos + 4:]; comment = True
        if not line.strip() or line.expandtabs(4).startswith("    "):
            header = None; table = False; continue
        tag = re.match(r"^ {0,3}<([A-Za-z][\w-]*)\b[^>]*>", line)
        if tag:
            if not re.search(r"</" + re.escape(tag.group(1)) + r"\s*>", line, re.I):
                html = tag.group(1)
            header = None; table = False; continue
        if line.startswith("## "):
            section = bool(re.match(r"^## 10\.(?:\s|$)", line)); dated = 0; header = None; table = False; continue
        if line.startswith("### "):
            dated = _author_heading(line) if section else 0
            header = None; table = False; continue
        if line.startswith("#"):
            dated = 0; header = None; table = False; continue
        if not section or not dated or not line.lstrip().startswith("|"):
            header = None; table = False; continue
        parts = line.strip().split("|")
        cells = parts[1:-1] if parts[-1] == "" else parts[1:]
        if len(cells) >= 2 and all(re.fullmatch(r"\s*:?-{3,}:?\s*", c) for c in cells):
            table = header if header == len(cells) else False; header = None; continue
        if not table:
            strength = _decision_header(cells)
            header = len(cells) if strength and (dated == 2 or strength == 2) else None; continue
        if len(cells) != table:
            continue
        out.append((cells[0].strip().strip("*` "), cells[1].strip()))
    return out


def prereg_frozen(root=None) -> dict:
    """The committed preregistration, refused unless frozen with the pinned split file and the committed builder and
    gate sha256s. Returns {"sha256", "builder_sha256", "gate_sha256"}."""
    data = _committed(PREREG_PATH, root)
    block = {}
    for line in data.decode("utf-8").splitlines():
        m = re.fullmatch(r"([a-z_0-9]+): (.*)", line.strip())
        if m:
            block[m.group(1)] = m.group(2).strip()
    builder = _sha(_committed(BUILDER_PATH, root))
    gate = _sha(_committed(GATE_PATH, root))
    if block.get("frozen") != "true":
        raise ReleaseStop("STOP: the preregistration is not frozen (frozen: true); no label is released before")
    if p3_split.P3_SPLIT_SHA256 not in block.get("split_file", ""):
        raise ReleaseStop("STOP: the frozen preregistration does not name the pinned P3 split file")
    if block.get("gate_input_builder_sha256") != builder:
        raise ReleaseStop("STOP: the committed gate-input builder is not the one the preregistration froze")
    if block.get("gate_sha256") != gate:
        raise ReleaseStop("STOP: the committed gate is not the one the preregistration binds")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T[0-9:]+Z?", block.get("frozen_utc", "")):
        raise ReleaseStop("STOP: the preregistration has no frozen_utc")
    return {"sha256": _sha(data), "builder_sha256": builder, "gate_sha256": gate}


def release_row(tier: str, stage: str, root=None) -> dict:
    """The exact release row of (tier, stage) in the committed PLAN, with every cited binding checked."""
    if (tier, stage) not in ROWS:
        raise ReleaseStop(f"STOP: unknown tier/stage {tier}/{stage}")
    rid = ROWS[(tier, stage)]
    plan = _committed("docs/r1/PLAN.md", root).decode("utf-8")
    rows = [d for i, d in author_rows(plan) if i == rid]
    if len(rows) != 1:
        raise ReleaseStop(f"STOP: {rid} is {'absent' if not rows else 'not unique'} in PLAN §10 (PRE-STAGE A)")
    m = re.fullmatch(row_pattern(tier, stage), rows[0])
    if not m:
        raise ReleaseStop(f"STOP: {rid} does not have the exact release text (§8 draft)")
    pre = prereg_frozen(root)
    if m.group("prereg") != pre["sha256"]:
        raise ReleaseStop(f"STOP: {rid} cites another preregistration sha256")
    if m.group("split") != p3_split.P3_SPLIT_SHA256:
        raise ReleaseStop(f"STOP: {rid} cites another split file")
    here = _committed(RELEASE_PATH, root)
    try:
        _git("merge-base", "--is-ancestor", m.group("commit"), "HEAD", root=root)
        declared = _git("show", f"{m.group('commit')}:{RELEASE_PATH}", root=root)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseStop(f"STOP: {rid}'s release-code commit is not an ancestor with {RELEASE_PATH}") from exc
    if declared != here:
        raise ReleaseStop(f"STOP: {rid}'s release-code commit has other {RELEASE_PATH} bytes")
    out = {"row_id": rid, "decision_sha256": _sha(rows[0].encode()), "prereg_sha256": pre["sha256"],
           "builder_sha256": pre["builder_sha256"], "gate_sha256": pre["gate_sha256"],
           "split_sha256": m.group("split"), "release_commit": m.group("commit")}
    if stage == "test":
        if _sha(_committed(m.group("arms_path"), root)) != m.group("arms"):
            raise ReleaseStop(f"STOP: the arms-frozen record cited by {rid} is missing or changed")
        out.update(arms_frozen_path=m.group("arms_path"), arms_frozen_sha256=m.group("arms"))
    return out


def test_released(tier: str = "T0", root=None) -> bool:
    try:
        release_row(tier, "test", root)
        return True
    except ReleaseStop:
        return False


# --------------------------------------------------------------------------------------------- locks

@contextlib.contextmanager
def integrity_context():
    """Marks the release step's integrity check (§6 carve-out)."""
    token = _INTEGRITY.set(True)
    try:
        yield
    finally:
        _INTEGRITY.reset(token)


def require_integrity_or_test_release(tier: str = "T0", what: str = "evaluation-seed values") -> None:
    """Allowed only inside the release step's integrity check or once the tier's test release row exists."""
    if _INTEGRITY.get():
        return
    if not test_released(tier):
        raise ReleaseStop(f"STOP: {what} are not read before {ROWS[(tier, 'test')]} (PRE-STAGE A); integrity checks "
                          "run only inside the release step (§6)")


def guard_raw_label_path(path, tier: str = "T0") -> None:
    """Refuse a raw audit label/evaluation file before the tier's test release row (readers use partitions)."""
    if Path(path).name in RAW_NAMES:
        require_integrity_or_test_release(tier, f"raw audit files ({Path(path).name})")


# --------------------------------------------------------------------------------------------- release step

def _lines(path: Path) -> list[tuple[str, dict]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append((line, json.loads(line)))
    return out


def _sweep1_integrity(table_dir: Path, audit_dir: Path, *, paper_root: Path, index: Path, classification: Path) -> dict:
    from r1.c3 import audit
    with integrity_context():
        completion = audit.verify_evidence_completion(Path(table_dir), Path(audit_dir) / "label_block.jsonl",
                                                      Path(paper_root), Path(index), Path(classification))
    return {"check": "audit.verify_evidence_completion", "pass": True,
            "completion_sha256": _sha((Path(audit_dir) / "evidence_completion.json").read_bytes()),
            "completion": {k: completion[k] for k in COMPLETION_KEEP if k in completion}}


INTEGRITY_CHECKS = {"sweep1": _sweep1_integrity}


def release(stage: str, *, source: str, table_dir, audit_dir, out_root, integrity_args: dict) -> dict:
    """Write the receipted partition of (source, stage); returns the receipt. Refuses an existing output."""
    if source not in SOURCES or stage not in STAGES:
        raise ReleaseStop(f"STOP: unknown source/stage {source}/{stage}")
    tier = SOURCES[source]
    table_dir, audit_dir, out_root = Path(table_dir), Path(audit_dir), Path(out_root)
    refuse_sealed(table_dir, audit_dir, out_root)
    require_d8_confirmation()
    row = release_row(tier, stage)
    out = out_root / source / stage
    if out.exists():
        raise ReleaseStop(f"STOP: {out} exists; a release is written once")
    if stage == "test":
        prior = open_partition(out_root / source / "traindev", verify_row=True)[1]
        if prior["source"] != source:
            raise ReleaseStop("STOP: traindev receipt of another source")
    check = INTEGRITY_CHECKS.get(source)
    if check is None:
        raise ReleaseStop(f"STOP: no reviewed integrity check for {source} (§6 carve-out); add one before its release")
    try:
        integrity = check(table_dir, audit_dir, **integrity_args)
    except Exception as exc:  # pass/fail only: no value leaves the check
        raise ReleaseStop(f"STOP: integrity check failed for {source} ({type(exc).__name__})") from None
    from r1.c3.dataset import load_table
    assign = p3_split.assignment(p3_split.load())
    inst_of = {}
    for r in load_table(table_dir):
        inst = p3_split.instance_id(r["node"], r["instance_seed"])
        if inst not in assign:
            raise ReleaseStop(f"STOP: table instance {inst} is not in the P3 split file (§6)")
        inst_of[r["proposal_id"]] = inst
    with integrity_context():
        labels = _lines(audit_dir / "label_block.jsonl")
        evals = _lines(audit_dir / "evaluation_block.jsonl") if stage == "test" else []
    parts = {"train": [], "dev": [], "test": []}
    kinds = {"train": {}, "dev": {}, "test": {}}       # counts by label kind (divergence diagnostics, no values)
    for line, row_ in labels:
        inst = inst_of.get(row_.get("proposal_id"))
        if inst is None:
            raise ReleaseStop("STOP: a label row names a proposal outside the table")
        split = assign[inst]["split"]
        parts[split].append(line)
        kind = str(row_.get("label_kind"))
        kinds[split][kind] = kinds[split].get(kind, 0) + 1
    for _, ev in evals:
        if ev.get("proposal_id") not in inst_of:
            raise ReleaseStop("STOP: an evaluation row names a proposal outside the table")
    files = ({"label_block.traindev.jsonl": parts["train"] + parts["dev"]} if stage == "traindev" else
             {"label_block.test.jsonl": parts["test"], "evaluation_block.all.jsonl": [l for l, _ in evals]})
    tmp = out.with_name(out.name + ".partial")
    if tmp.exists():
        raise ReleaseStop(f"STOP: {tmp} exists (an interrupted release); inspect it")
    tmp.mkdir(parents=True)
    outputs = {}
    for name, lines in files.items():
        data = "".join(l + "\n" for l in lines).encode()
        (tmp / name).write_bytes(data)
        outputs[name] = _sha(data)
    receipt = {"schema": RECEIPT_SCHEMA, "source": source, "tier": tier, "stage": stage, **row,
               "head": _git("rev-parse", "HEAD").decode().strip(),
               "inputs": {"proposals_sha256": _sha((table_dir / "proposals.jsonl").read_bytes()),
                          "label_block_sha256": _sha((audit_dir / "label_block.jsonl").read_bytes()),
                          **({"evaluation_block_sha256": _sha((audit_dir / "evaluation_block.jsonl").read_bytes())}
                             if stage == "test" else {})},
               "outputs": outputs,
               "counts": {"label_rows": {k: len(v) for k, v in parts.items()}, "label_kinds": kinds,
                          "released_label_rows": sum(len(v) for k, v in parts.items()
                                                     if (k == "test") == (stage == "test")),
                          "evaluation_rows": len(evals)},
               "integrity": integrity, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (tmp / "RECEIPT.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    tmp.rename(out)
    return receipt


# --------------------------------------------------------------------------------------------- readers

def open_partition(part_dir, *, verify_row: bool = True) -> tuple[dict, dict]:
    """({file name: [rows]}, receipt) of one receipted partition; every binding is re-checked."""
    part_dir = Path(part_dir)
    refuse_sealed(part_dir)
    rp = part_dir / "RECEIPT.json"
    if not rp.is_file():
        raise ReleaseStop(f"STOP: {part_dir} has no release receipt; readers open only receipted partitions")
    receipt = json.loads(rp.read_text())
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("stage") not in STAGES or \
            receipt.get("source") not in SOURCES or SOURCES[receipt["source"]] != receipt.get("tier"):
        raise ReleaseStop(f"STOP: {rp} is not a release receipt")
    if set(receipt.get("outputs", {})) != set(PARTITIONS[receipt["stage"]]):
        raise ReleaseStop(f"STOP: {rp} lists other partition files")
    if verify_row:
        row = release_row(receipt["tier"], receipt["stage"])
        for k, v in row.items():
            if receipt.get(k) != v:
                raise ReleaseStop(f"STOP: {rp} no longer matches {row['row_id']} ({k})")
    out = {}
    for name, digest in receipt["outputs"].items():
        data = (part_dir / name).read_bytes()
        if _sha(data) != digest:
            raise ReleaseStop(f"STOP: {part_dir / name} differs from its receipt")
        out[name] = [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]
    return out, receipt


def traindev_labels(release_root, source: str) -> tuple[list[dict], dict]:
    """The released train/dev label rows of a source and their receipt (arms training, selection, A2's fit)."""
    parts, receipt = open_partition(Path(release_root) / source / "traindev")
    return parts["label_block.traindev.jsonl"], receipt


def builder_source(release_root, source: str, table_dir):
    """A ``gate_input_builder.Source`` for a gate source (``sweep2``, ``g5``) from the receipted partitions of both
    stages, after the test release row; for ``sweep1`` (repeat keys only) the table rows alone."""
    from r1.c3.dataset import load_table
    from r1.c3.gate_input_builder import GATE_SOURCES, KEY_SOURCES, Source
    if source in KEY_SOURCES:
        return Source(source, load_table(Path(table_dir)))
    if source not in GATE_SOURCES:
        raise ReleaseStop(f"STOP: unknown source {source}")
    root = Path(release_root) / source
    td, rtd = open_partition(root / "traindev")
    ts, rts = open_partition(root / "test")
    if rtd["inputs"]["label_block_sha256"] != rts["inputs"]["label_block_sha256"] or \
            rtd["inputs"]["proposals_sha256"] != rts["inputs"]["proposals_sha256"]:
        raise ReleaseStop(f"STOP: the {source} partitions come from different label blocks or tables")
    if _sha((Path(table_dir) / "proposals.jsonl").read_bytes()) != rts["inputs"]["proposals_sha256"]:
        raise ReleaseStop(f"STOP: {table_dir} is not the table the {source} partitions were released from")
    labels = td["label_block.traindev.jsonl"] + ts["label_block.test.jsonl"]
    return Source(source, load_table(Path(table_dir)), labels, ts["evaluation_block.all.jsonl"])


def main(argv=None) -> int:
    """``python -m r1.c3.release --stage traindev|test --source sweep1|sweep2|g5 --table DIR --audit DIR --out DIR
    [--paper-root P --index I --classification C]`` (the sweep-1 integrity check needs the last three)."""
    import argparse
    ap = argparse.ArgumentParser(description="PRE-STAGE A release step")
    ap.add_argument("--stage", required=True, choices=STAGES)
    ap.add_argument("--source", required=True, choices=sorted(SOURCES))
    ap.add_argument("--table", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--paper-root")
    ap.add_argument("--index")
    ap.add_argument("--classification")
    a = ap.parse_args(argv)
    extra = {k: Path(v) for k, v in (("paper_root", a.paper_root), ("index", a.index),
                                     ("classification", a.classification)) if v}
    receipt = release(a.stage, source=a.source, table_dir=a.table, audit_dir=a.audit, out_root=a.out,
                      integrity_args=extra)
    print(json.dumps({k: receipt[k] for k in ("row_id", "source", "stage", "outputs", "counts")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
