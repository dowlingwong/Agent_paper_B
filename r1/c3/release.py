"""Staged label release and partition-reading locks (PRE-STAGE A of the sweep-2 analysis preregistration, §4, §6, §8).

AI-assisted (Claude). For **both sources** (sweep 1 and sweep 2 for T0; the G.5 tables for T1), until the test release
row exists, readers get the label block of **train and dev instances only** and **no evaluation value of any
instance**. Mechanism:

* **Release step** (``release``). Run once per (source, stage) when its PLAN row exists on the committed checkout:
  - stage ``traindev`` (row R1-S2-LABELS-TRAINDEV-RELEASE for T0, R1-T1-LABELS-UNSEAL for T1) writes
    ``label_block.traindev.jsonl``: the label rows of P3 train and dev instances, byte-identical lines;
  - stage ``test`` (row R1-S2-LABELS-TEST-RELEASE / R1-T1-LABELS-TEST-RELEASE, which also cites the arms-frozen
    record) writes ``label_block.test.jsonl`` and ``evaluation_block.all.jsonl``; it needs the traindev receipt of the
    same label block and table;
  - each writes ``RECEIPT.json``: the row id and the sha256 of its decision text, the preregistration, split file,
    release-code commit (and arms-frozen record, and for T1 the G.1b summaries) it binds, the integrity-check module's
    sha256, input and output sha256s, counts, and the integrity result.
  Before writing, the step checks: the D8 confirmation (gate v3.1); the release row's exact text in a dated author
  table of PLAN §10; the preregistration frozen (its final fenced block: ``frozen: true``, ``pre_stage: A``,
  ``split_file`` naming the pinned P3 split file and sha256, ``gate_input_builder_sha256`` and ``gate_sha256`` equal to
  the committed files, the signed decisions, each key once, and the block must end the document); the release-code commit (an ancestor of HEAD and of ``origin/main``, whose
  ``release.py`` the running file must equal); for a test row the arms-frozen record's bytes; for a T1 train/dev row
  each cited G.1b summary's bytes; HEAD unchanged during the step; a clean checkout whose PLAN, preregistration,
  release code, integrity checks and the code the release runs (gate, builder, split file, ``p3_split``, ``audit``,
  ``dataset``, ``analysis_guard``) equal ``origin/main``'s; the integrity checks imported being this checkout's
  committed ``release_checks.py``; and the source's **integrity check**, whose result must name the sha256 of the label
  block (and at the test stage of the evaluation block) the step then partitions.
* **Integrity carve-out** (§6). Checks live in ``r1.c3.release_checks`` (so registering a source's check does not
  change this file). ``audit.verify_evidence_completion`` opens ``runs.jsonl`` and ``evaluation_block.jsonl``; before
  the test release row it runs only inside the release step (``integrity_context``), and the step records pass/fail,
  counts and hashes, never a value; a failing check is reported by its exception type only.
* **Readers** (``open_partition``, ``traindev_labels``, ``builder_source``) open only receipted partitions. On every
  open they re-check: the D8 confirmation for sweep-2 and G.5 partitions; the receipt's source and stage against what
  the caller expects; the row still present with the same text and bindings (the receipt's own release-code commit,
  not HEAD's bytes, so a later reviewed edit of this file does not void earlier receipts); the output sha256s; and
  **P3 membership of every row**, re-derived from the proposal id's instance and the pinned split file (traindev label
  rows only train and dev instances, test label rows only test instances), with the receipt's counts. A caller may
  also pin the receipt's own sha256 (e.g. from the arms-frozen record).
* **Locks on the existing readers** (``guard_raw_label_path``, ``require_integrity_or_test_release``): a raw
  ``label_block.jsonl``, ``evaluation_block.jsonl`` or ``runs.jsonl``, and **any file in a B.2 evidence audit
  directory** (one holding ``evidence_completion.json``, ``evidence_binding.json``, ``label_block.jsonl`` or
  ``evaluation_block.jsonl``; symlinks resolved), is refused until the test release row of its tier exists. A reader
  that does not know the tier passes none and needs the test rows of **both** tiers (fail closed). Inside the release
  step's integrity check and inside the evidence audit's own writer (``producer_context``) the lock is open. Used by
  ``sft_data.LabelBlockSource`` (T0), ``offline_eval.assemble``, ``env.label_rows``, ``ni_masking.load_audits``,
  ``audit.RunCache`` (T0, a non-empty run log in an evidence directory), ``audit collect`` (refuses an evidence
  directory) and ``audit.verify_evidence_completion`` (T0).

* **Split file v2** (R1-G5-S9 (1)). A release row may cite the split file v1 (the frozen preregistration's) or v2
  (v1 plus the expansion nodes, every v1 entry byte-identical). A row citing v2 also needs the PRE-SPLIT amendment
  published on the committed checkout (``split_v2_amendment``: ``SPLIT_AMENDMENT_PATH`` with its final block approved
  and frozen, naming R1-G5-S9, the preregistration and both split files; R1-G5-S9 an author row of PLAN §10). The
  preregistration's own block still names v1 (its bytes are not changed). The release step partitions, and every
  reader re-derives P3 membership, by the split file the row cites (the receipt's ``split_sha256``), so a v1 row never
  admits a joining node's instance.

What may be read before release: counts and divergence diagnostics without values (the receipts' counts).
A lock forbids reads; it cannot prevent a deliberate read (copying a block elsewhere, editing a receipt), which is a
STOP (§6).
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

RECEIPT_SCHEMA = "r1_c3_release_receipt/v2"
PREREG_PATH = "docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md"
RELEASE_PATH = "r1/c3/release.py"
CHECKS_PATH = "r1/c3/release_checks.py"
BUILDER_PATH = "r1/c3/gate_input_builder.py"
GATE_PATH = "r1/c3/gate.py"
SPLIT_PATH = "r1/c3/splits/c3_p3_split_v1.json"
SPLIT_V2_PATH = "r1/c3/splits/c3_p3_split_v2.json"                  # R1-G5-S9 (1)
# The PRE-SPLIT amendment (R1-G5-S9 (1): "PRE-SPLIT is amended to cite v2"), published by the coordinator from the draft
# docs/r1/proposals/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_DRAFT_20261127.md; the preregistration's bytes are not changed.
SPLIT_AMENDMENT_PATH = "docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md"
SPLIT_AMENDMENT_ROW = "R1-G5-S9"
G5_TAILS_AMENDMENT_PATH = "docs/r1/authorizations/C3_SWEEP2_G5_TAILS_AMENDMENT_20261127.md"
G5_TAILS_AMENDMENT_ROW = "R1-G5-TAILS-PREREG-AMEND"
G5_TAILS_CODE_PINS = {
    "gate_sha256": GATE_PATH,
    "gate_input_builder_sha256": BUILDER_PATH,
    "labels_sha256": "r1/c3/labels.py",
    "arms_freeze_sha256": "r1/c3/arms_freeze.py",
    "arms_constants_sha256": "r1/c3/arms_constants.py",
    "sft_data_sha256": "r1/c3/train/sft_data.py",
    "fold_analysis_sha256": "r1/c3/fold_analysis.py",
    "release_sha256": RELEASE_PATH,
}
STAGES = ("traindev", "test")
TIERS = ("T0", "T1")
SOURCES = {"sweep1": "T0", "sweep2": "T0", "g5": "T1"}
D8_SOURCES = ("sweep2", "g5")
ROWS = {("T0", "traindev"): "R1-S2-LABELS-TRAINDEV-RELEASE", ("T0", "test"): "R1-S2-LABELS-TEST-RELEASE",
        ("T1", "traindev"): "R1-T1-LABELS-UNSEAL", ("T1", "test"): "R1-T1-LABELS-TEST-RELEASE"}
WHAT = {"T0": "both sources (sweep 1 and sweep 2)", "T1": "the G.5 T1 tables"}
RAW_NAMES = frozenset({"label_block.jsonl", "evaluation_block.jsonl", "runs.jsonl"})
EVIDENCE_MARKERS = ("evidence_completion.json", "evidence_binding.json", "label_block.jsonl", "evaluation_block.jsonl")
PARTITIONS = {"traindev": ("label_block.traindev.jsonl",),
              "test": ("label_block.test.jsonl", "evaluation_block.all.jsonl")}
# The signed decision block (R1-SWEEP2-PREREG): exactly these keys; the decisions as signed on 21 Nov 2026.
SIGNED_DECISIONS = {"pre_wdbc": "B", "pre_split": "A", "pre_mem": "C", "pre_joint": "A", "pre_select": "A",
                    "pre_a2": "C", "pre_delta": "A", "pre_dup": "A", "pre_div": "A", "pre_t1": "A",
                    "pre_secondary": "A", "pre_stage": "A", "pre_power": "A"}
PREREG_KEYS = ("frozen", "split_file", *SIGNED_DECISIONS, "gate_sha256", "gate_input_builder_sha256", "signed_by",
               "frozen_utc")
_HEX = r"[0-9a-f]{64}"
_COMMIT = r"(?:[0-9a-f]{40}|[0-9a-f]{64})"
_G1B_ITEM = r"`[a-z0-9_]+`: `[A-Za-z0-9_./-]+` \(sha256 `" + _HEX + r"`\)"
_INTEGRITY = contextvars.ContextVar("r1_c3_release_integrity", default=False)
_PRODUCER = contextvars.ContextVar("r1_c3_release_producer", default=False)
_GIT_ERRORS = (OSError, subprocess.CalledProcessError, UnicodeError, ValueError, AttributeError, TypeError, KeyError)


class ReleaseStop(RuntimeError):
    """A PRE-STAGE A STOP: nothing is written or read."""


# --------------------------------------------------------------------------------------------- row templates

def row_pattern(tier: str, stage: str) -> str:
    """The exact decision text of a release row (the §8 drafts), as a regex with named groups prereg, split,
    commit (arms_path, arms for a test row; g1b for the T1 train/dev row)."""
    pre = (r"Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration "
           r"\(`" + re.escape(PREREG_PATH) + r"`, sha256 `(?P<prereg>" + _HEX + r")`\)")
    pre += (r"(?: and the G\.5 tail-law amendment \(`" + re.escape(G5_TAILS_AMENDMENT_PATH) +
            r"`, sha256 `(?P<tail_amendment>" + _HEX + r")`\))?")
    arms = r", after the arms-frozen record `(?P<arms_path>docs/r1/[A-Za-z0-9_./-]+\.md)` \(sha256 `(?P<arms>" + _HEX + r")`\)"
    tail = (r", partitioned by the P3 split file \(sha256 `(?P<split>" + _HEX + r")`\) with the release step "
            r"`r1/c3/release\.py` @ `(?P<commit>" + _COMMIT + r")`\.")
    what = re.escape(WHAT[tier])
    if stage == "traindev":
        g1b = ""
        if tier == "T1":
            g1b = r", with the T1 nodes' G\.1b noise summaries (?P<g1b>" + _G1B_ITEM + r"(?:; " + _G1B_ITEM + r")*)"
        return (pre + r": the train and dev label blocks of " + what + g1b + tail +
                r" No test label and no evaluation value is released by this row\.")
    return pre + arms + r": the test label blocks and every evaluation block of " + what + tail


def row_text(tier: str, stage: str, *, prereg: str, split: str, commit: str, arms_path: str | None = None,
             arms: str | None = None, g1b: dict | None = None, tail_amendment: str | None = None) -> str:
    """The decision text of a release row with the values filled in (for the drafts and tests). ``g1b``:
    {node: (path, sha256)} for the T1 train/dev row (PRE-DELTA)."""
    head = (f"Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`{PREREG_PATH}`, "
            f"sha256 `{prereg}`)")
    if tail_amendment is not None:
        head += f" and the G.5 tail-law amendment (`{G5_TAILS_AMENDMENT_PATH}`, sha256 `{tail_amendment}`)"
    tail = f", partitioned by the P3 split file (sha256 `{split}`) with the release step `r1/c3/release.py` @ `{commit}`."
    if stage == "traindev":
        mid = ""
        if tier == "T1":
            mid = ", with the T1 nodes' G.1b noise summaries " + "; ".join(
                f"`{n}`: `{p}` (sha256 `{h}`)" for n, (p, h) in sorted((g1b or {}).items()))
        return (head + f": the train and dev label blocks of {WHAT[tier]}" + mid + tail +
                " No test label and no evaluation value is released by this row.")
    return (head + f", after the arms-frozen record `{arms_path}` (sha256 `{arms}`): the test label blocks and every "
            f"evaluation block of {WHAT[tier]}" + tail)


# ---------------------------------------------------------------------------------------- committed authority

def _git(*args, root=None) -> bytes:
    return subprocess.check_output(["git", "-C", str(root or REPO), *args], stderr=subprocess.DEVNULL)


def _head(root=None) -> str:
    try:
        head = _git("rev-parse", "--verify", "HEAD", root=root).decode().strip()
    except _GIT_ERRORS as exc:
        raise ReleaseStop("STOP: the checkout HEAD is unavailable") from exc
    if not re.fullmatch(_COMMIT, head):
        raise ReleaseStop("STOP: invalid HEAD object id")
    return head


def _committed(path: str, root=None) -> bytes:
    """The bytes of ``path`` at HEAD, refused unless the working file is the same regular file."""
    root = Path(root or REPO)
    f = root / path
    refuse_sealed(f)
    if f.is_symlink() or not f.is_file():
        raise ReleaseStop(f"STOP: {path} is absent or a symlink")
    try:
        head = _head(root)
        entry = _git("ls-tree", "-z", head, "--", path, root=root)
        if not re.fullmatch(rb"(?:100644|100755) blob [0-9a-f]{40,64}\t" + re.escape(path.encode()) + rb"\x00", entry):
            raise ReleaseStop(f"STOP: {path} is not a regular committed file")
        data = _git("show", f"{head}:{path}", root=root)
        same = data == f.read_bytes()
    except ReleaseStop:
        raise
    except _GIT_ERRORS as exc:
        raise ReleaseStop(f"STOP: committed {path} unavailable") from exc
    if not same:
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


def _strip_comments(text: str) -> str:
    """The text with HTML comments removed (as ``author_rows`` treats them)."""
    out, rest = [], text
    while True:
        pos = rest.find("<!--")
        if pos < 0:
            out.append(rest)
            return "".join(out)
        out.append(rest[:pos])
        end = rest.find("-->", pos + 4)
        if end < 0:
            return "".join(out)
        rest = rest[end + 3:]


def _fenced_blocks(lines: list[str]) -> list[tuple[int, int]]:
    """(opening line, closing line) of every closed fenced code block."""
    out, start, fence = [], None, None
    for i, line in enumerate(lines):
        m = re.match(r" {0,3}(`{3,}|~{3,})", line)
        if fence is None:
            if m:
                start, fence = i, m.group(1)
        elif re.fullmatch(r" {0,3}(`{3,}|~{3,})\s*", line) and line.strip()[0] == fence[0] and \
                len(line.strip()) >= len(fence):
            out.append((start, i))
            fence = None
    return out


def _final_block(text: str) -> list[str]:
    """The lines of the preregistration's decision block: HTML comments ignored, exactly one fenced block holds a
    ``frozen:`` line, and that block ends the document (nothing but blank lines after it)."""
    lines = _strip_comments(text).splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    blocks = [(a, b) for a, b in _fenced_blocks(lines) if any(l.startswith("frozen:") for l in lines[a + 1:b])]
    if len(blocks) != 1:
        raise ReleaseStop(f"STOP: the preregistration has {len(blocks)} fenced blocks with a frozen: line, not one")
    a, b = blocks[0]
    if b != len(lines) - 1:
        raise ReleaseStop("STOP: the preregistration does not end with its fenced decision block")
    return lines[a + 1:b]


def g5_tail_amendment_published(root=None) -> bool:
    """Whether published main contains a G.5 tail-law amendment decision."""
    try:
        data = _git("show", "refs/remotes/origin/main:docs/r1/PLAN.md", root=root).decode("utf-8")
    except _GIT_ERRORS:
        return False
    return any(key == G5_TAILS_AMENDMENT_ROW for key, _ in author_rows(data))


def _g5_tails_prereg(base_sha: str, original_builder: str, root=None) -> dict:
    """Resolve an exact author-approved amendment before accepting a replacement builder."""
    rows = [decision for key, decision in author_rows(_committed("docs/r1/PLAN.md", root).decode())
            if key == G5_TAILS_AMENDMENT_ROW]
    pattern = (rf"Use the reviewed G\.5 tail-law amendment `{re.escape(G5_TAILS_AMENDMENT_PATH)}` "
               rf"sha256 `({_HEX})` with implementation commit `({_COMMIT})`\.")
    match = re.fullmatch(pattern, rows[0]) if len(rows) == 1 else None
    if match is None:
        raise ReleaseStop("STOP: the committed gate-input builder is not the one the preregistration froze; "
                          "an exact signed G.5 tail-law amendment is required")
    digest, commit = match.groups()
    raw = _committed(G5_TAILS_AMENDMENT_PATH, root)
    if _sha(raw) != digest:
        raise ReleaseStop("STOP: the G.5 tail-law amendment differs from the signed digest")
    fields = {}
    for line in _final_block(raw.decode("utf-8")):
        key, separator, value = line.partition(": ")
        if not separator or key in fields:
            raise ReleaseStop("STOP: malformed or duplicate G.5 tail-law amendment key")
        fields[key] = value
    required = {"frozen", "base_preregistration_sha256", "original_gate_input_builder_sha256",
                "signed_by", "frozen_utc", *G5_TAILS_CODE_PINS}
    if set(fields) != required or fields["frozen"] != "true" or \
            fields["base_preregistration_sha256"] != base_sha or \
            fields["original_gate_input_builder_sha256"] != original_builder or \
            not fields["signed_by"] or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z",
                                                        fields["frozen_utc"]):
        raise ReleaseStop("STOP: the G.5 tail-law amendment lacks its frozen bindings")
    try:
        published = "refs/remotes/origin/main"
        published_plan = _git("show", f"{published}:docs/r1/PLAN.md", root=root).decode("utf-8")
        published_rows = [decision for key, decision in author_rows(published_plan)
                          if key == G5_TAILS_AMENDMENT_ROW]
        if published_rows != rows or _git("show", f"{published}:{G5_TAILS_AMENDMENT_PATH}", root=root) != raw:
            raise ReleaseStop("STOP: the G.5 tail-law amendment and decision must match published main")
        _git("merge-base", "--is-ancestor", commit, "HEAD", root=root)
        _git("merge-base", "--is-ancestor", commit, published, root=root)
        for key, path in G5_TAILS_CODE_PINS.items():
            if fields[key] != _sha(_committed(path, root)) or fields[key] != _sha(
                    _git("show", f"{commit}:{path}", root=root)):
                raise ReleaseStop(f"STOP: the G.5 tail-law amendment does not bind {path}")
    except _GIT_ERRORS as exc:
        raise ReleaseStop("STOP: the G.5 tail-law implementation is not the reviewed published commit") from exc
    return {"sha256": base_sha, "g5_tail_amendment_sha256": digest,
            "builder_sha256": fields["gate_input_builder_sha256"], "gate_sha256": fields["gate_sha256"]}


def prereg_frozen(root=None, *, historical_builder_commit: str | None = None) -> dict:
    """The committed preregistration, refused unless its final fenced block says it is frozen with the pinned split
    file, PRE-STAGE A and the committed builder and gate sha256s (each key exactly once)."""
    data = _committed(PREREG_PATH, root)
    try:
        lines = _final_block(data.decode("utf-8"))
    except UnicodeError as exc:
        raise ReleaseStop("STOP: the preregistration is not UTF-8") from exc
    block = {}
    for line in lines:
        m = re.fullmatch(r"([a-z_0-9]+): (.*)", line)
        if not m:
            raise ReleaseStop(f"STOP: the preregistration block has a line that is not 'key: value': {line!r}")
        if m.group(1) in block:
            raise ReleaseStop(f"STOP: the preregistration block repeats {m.group(1)}")
        block[m.group(1)] = m.group(2).strip()
    if set(block) != set(PREREG_KEYS):
        raise ReleaseStop(f"STOP: the preregistration block lacks {sorted(set(PREREG_KEYS) - set(block))} or has "
                          f"other keys {sorted(set(block) - set(PREREG_KEYS))}")
    changed = sorted(k for k, v in SIGNED_DECISIONS.items() if block[k] != v)
    if changed:
        raise ReleaseStop(f"STOP: the preregistration block's decisions differ from the signed ones: {changed}")
    gate = _sha(_committed(GATE_PATH, root))
    if block["frozen"] != "true":
        raise ReleaseStop("STOP: the preregistration is not frozen (frozen: true); no label is released before")
    if block["split_file"] != f"{SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}":
        raise ReleaseStop(f"STOP: split_file must read exactly '{SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}'")
    if block["gate_sha256"] != gate:
        raise ReleaseStop("STOP: the committed gate is not the one the preregistration binds")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z", block["frozen_utc"]):
        raise ReleaseStop("STOP: the preregistration has no frozen_utc (YYYY-MM-DDTHH:MM[:SS]Z)")
    base_sha = _sha(data)
    if historical_builder_commit is not None:
        try:
            builder = _sha(_git("show", f"{historical_builder_commit}:{BUILDER_PATH}", root=root))
        except _GIT_ERRORS as exc:
            raise ReleaseStop("STOP: the historical gate-input builder is unavailable") from exc
        if builder != block["gate_input_builder_sha256"]:
            raise ReleaseStop("STOP: the historical gate-input builder is not the one the preregistration binds")
        return {"sha256": base_sha, "builder_sha256": builder, "gate_sha256": gate}
    builder = _sha(_committed(BUILDER_PATH, root))
    if block["gate_input_builder_sha256"] != builder or g5_tail_amendment_published(root):
        return _g5_tails_prereg(base_sha, block["gate_input_builder_sha256"], root)
    return {"sha256": base_sha, "builder_sha256": builder, "gate_sha256": gate}


def split_v2_amendment(root=None) -> dict:
    """The published PRE-SPLIT amendment that lets evidence cite the split file v2 (R1-G5-S9 (1)): the committed
    ``SPLIT_AMENDMENT_PATH``, whose final fenced block holds exactly these lines (each once) with ``approved: true``
    and ``frozen: true``; and R1-G5-S9 an author row of the committed PLAN §10. Returns {path, sha256}."""
    try:
        data = _committed(SPLIT_AMENDMENT_PATH, root)
    except ReleaseStop as exc:
        raise ReleaseStop(f"STOP: the split file v2 needs the published PRE-SPLIT amendment {SPLIT_AMENDMENT_PATH} "
                          "(R1-G5-S9 (1))") from exc
    try:
        text = data.decode("utf-8")
        lines = _final_block(text)
        plan = _committed("docs/r1/PLAN.md", root).decode("utf-8")
    except UnicodeError as exc:
        raise ReleaseStop("STOP: the PRE-SPLIT amendment or PLAN is not UTF-8") from exc
    block = {}
    for line in lines:
        m = re.fullmatch(r"([a-z_0-9]+): (.*)", line)
        if not m or m.group(1) in block:
            raise ReleaseStop(f"STOP: the PRE-SPLIT amendment block has a bad or repeated line: {line!r}")
        block[m.group(1)] = m.group(2).strip()
    pre = _sha(_committed(PREREG_PATH, root))
    want = {"amends": f"{PREREG_PATH} sha256 {pre}", "plan_row": SPLIT_AMENDMENT_ROW, "pre_split": "A",
            "split_file": f"{SPLIT_V2_PATH} sha256 {p3_split.P3_SPLIT_V2_SHA256}",
            "supersedes_split_file": f"{SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}",
            "approved": "true", "frozen": "true"}
    keys = set(want) | {"signed_by", "signed_utc"}
    if set(block) != keys:
        raise ReleaseStop(f"STOP: the PRE-SPLIT amendment block must hold exactly {sorted(keys)}")
    bad = sorted(k for k, v in want.items() if block[k] != v)
    status = re.findall(r"^approved: (.+)$", re.split(r"^```", _strip_comments(text), maxsplit=1, flags=re.M)[0], re.M)
    if bad or status != ["true"]:
        raise ReleaseStop(f"STOP: the PRE-SPLIT amendment is not published as approved and frozen for v2: {bad}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z", block["signed_utc"]) or not block["signed_by"]:
        raise ReleaseStop("STOP: the PRE-SPLIT amendment has no signed_by / signed_utc (YYYY-MM-DDTHH:MM[:SS]Z)")
    rows = [d for i, d in author_rows(plan) if i == SPLIT_AMENDMENT_ROW]
    if len(rows) != 1:
        raise ReleaseStop(f"STOP: {SPLIT_AMENDMENT_ROW} is absent or not unique in PLAN §10")
    try:
        main = "refs/remotes/origin/main"
        published = _git("show", f"{main}:{SPLIT_AMENDMENT_PATH}", root=root)
        published_plan = _git("show", f"{main}:docs/r1/PLAN.md", root=root).decode("utf-8")
    except _GIT_ERRORS as exc:
        raise ReleaseStop("STOP: the PRE-SPLIT amendment and author row must match published main") from exc
    if published != data or [d for i, d in author_rows(published_plan) if i == SPLIT_AMENDMENT_ROW] != rows:
        raise ReleaseStop("STOP: the PRE-SPLIT amendment and author row must match published main")
    return {"path": SPLIT_AMENDMENT_PATH, "sha256": _sha(data)}


def release_row(tier: str, stage: str, *, writing: bool = False, root=None) -> dict:
    """The exact release row of (tier, stage) in the committed PLAN, with every cited binding checked. ``writing``:
    the running ``release.py`` must also be the cited commit's (the release step itself)."""
    if (tier, stage) not in ROWS:
        raise ReleaseStop(f"STOP: unknown tier/stage {tier}/{stage}")
    rid = ROWS[(tier, stage)]
    head = _head(root)
    try:
        plan = _committed("docs/r1/PLAN.md", root).decode("utf-8")
    except UnicodeError as exc:
        raise ReleaseStop("STOP: PLAN is not UTF-8") from exc
    rows = [d for i, d in author_rows(plan) if i == rid]
    if len(rows) != 1:
        raise ReleaseStop(f"STOP: {rid} is {'absent' if not rows else 'not unique'} in PLAN §10 (PRE-STAGE A)")
    m = re.fullmatch(row_pattern(tier, stage), rows[0])
    if not m:
        raise ReleaseStop(f"STOP: {rid} does not have the exact release text (§8 draft)")
    commit = m.group("commit")
    try:
        _git("merge-base", "--is-ancestor", commit, "HEAD", root=root)
        _git("merge-base", "--is-ancestor", commit, "refs/remotes/origin/main", root=root)
        declared = _git("show", f"{commit}:{RELEASE_PATH}", root=root)
    except _GIT_ERRORS as exc:
        raise ReleaseStop(f"STOP: {rid}'s release-code commit is not a published ancestor with {RELEASE_PATH}") from exc
    # Legacy read-only T0 train/dev receipts retain the builder from their published release commit.
    historical = (tier, stage) == ("T0", "traindev") and not writing and m.group("tail_amendment") is None
    pre = prereg_frozen(root, historical_builder_commit=commit if historical else None)
    if m.group("prereg") != pre["sha256"]:
        raise ReleaseStop(f"STOP: {rid} cites another preregistration sha256")
    amendment = pre.get("g5_tail_amendment_sha256")
    if m.group("tail_amendment") != amendment:
        raise ReleaseStop(f"STOP: {rid} does not cite the effective G.5 tail-law amendment")
    if m.group("split") not in p3_split.VERSION_OF_SHA:
        raise ReleaseStop(f"STOP: {rid} cites another split file")
    if m.group("split") == p3_split.P3_SPLIT_V2_SHA256:
        split_v2_amendment(root)
    if writing and declared != _committed(RELEASE_PATH, root):
        raise ReleaseStop(f"STOP: the running {RELEASE_PATH} is not the one {rid} cites")
    out = {"row_id": rid, "decision_sha256": _sha(rows[0].encode()), "prereg_sha256": pre["sha256"],
           "builder_sha256": pre["builder_sha256"], "gate_sha256": pre["gate_sha256"],
           "split_sha256": m.group("split"), "release_commit": commit}
    if amendment is not None:
        out["g5_tail_amendment_sha256"] = amendment
    if stage == "test":
        if _sha(_committed(m.group("arms_path"), root)) != m.group("arms"):
            raise ReleaseStop(f"STOP: the arms-frozen record cited by {rid} is missing or changed")
        out.update(arms_frozen_path=m.group("arms_path"), arms_frozen_sha256=m.group("arms"))
    if tier == "T1" and stage == "traindev":
        g1b = {}
        for node, path, digest in re.findall(r"`([a-z0-9_]+)`: `([A-Za-z0-9_./-]+)` \(sha256 `(" + _HEX + r")`\)",
                                             m.group("g1b")):
            if node in g1b or _sha(_committed(path, root)) != digest:
                raise ReleaseStop(f"STOP: {rid}'s G.1b summary for {node} is repeated, missing or changed")
            g1b[node] = {"path": path, "sha256": digest}
        out["g1b_summaries"] = g1b
    if _head(root) != head:
        raise ReleaseStop("STOP: the checkout HEAD changed during the release-row check")
    return out


def _row_assignment(row: dict) -> dict:
    """The P3 assignment of the split file a release row cites (``split_sha256``: v1 or v2)."""
    try:
        return p3_split.assignment(p3_split.load_pinned(p3_split.pin_of_sha(row["split_sha256"])))
    except p3_split.SplitError as exc:
        raise ReleaseStop(f"STOP: the split file the row cites cannot be loaded ({exc})") from exc


def test_released(tier: str = "T0", root=None) -> bool:
    try:
        release_row(tier, "test", root=root)
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


@contextlib.contextmanager
def producer_context():
    """Marks the evidence audit's own writer, reading back the run log it is writing (``audit.evidence_run``)."""
    token = _PRODUCER.set(True)
    try:
        yield
    finally:
        _PRODUCER.reset(token)


def require_integrity_or_test_release(tier: str | None = None, what: str = "evaluation-seed values") -> None:
    """Allowed only inside the integrity check or the evidence writer, or once the test release row of ``tier``
    exists (``None``: of both tiers)."""
    if _INTEGRITY.get() or _PRODUCER.get():
        return
    tiers = TIERS if tier is None else (tier,)
    missing = [t for t in tiers if not test_released(t)]
    if missing:
        raise ReleaseStop(f"STOP: {what} are not read before {', '.join(ROWS[(t, 'test')] for t in missing)} "
                          "(PRE-STAGE A); integrity checks run only inside the release step (§6)")


def is_evidence_dir(directory) -> bool:
    d = Path(directory)
    return any((d / m).exists() for m in EVIDENCE_MARKERS)


def evidence_root(path) -> Path | None:
    """The nearest directory at or above ``path``'s directory (lexical or resolved) holding an evidence marker."""
    p = Path(path)
    for start in (p.parent, p.resolve().parent):
        for d in (start, *start.parents):
            if is_evidence_dir(d):
                return d
    return None


def evidence_tier(root) -> str | None:
    """T0 for a B.2 evidence audit (its completion record's schema, metadata only); otherwise unknown (None). A G.5
    evidence writer must use its own completion schema (not ``r1.c3_audit_completion/``), else its run log would be
    treated as T0 (a condition in the §8 drafts)."""
    f = Path(root) / "evidence_completion.json"
    try:
        schema = str(json.loads(f.read_text()).get("schema", ""))
    except (OSError, ValueError, AttributeError):
        return None
    return "T0" if schema.startswith("r1.c3_audit_completion/") else None


def guard_raw_label_path(path, tier: str | None = None) -> None:
    """Refuse a raw audit label/evaluation file, or any file under an evidence audit directory (symlinks resolved,
    ancestors included, e.g. seed journals), before the test release row of ``tier`` (``None``: both tiers)."""
    p = Path(path)
    r = p.resolve()
    if p.name in RAW_NAMES or r.name in RAW_NAMES or evidence_root(p) is not None:
        require_integrity_or_test_release(tier, f"raw audit files ({r.name})")


# --------------------------------------------------------------------------------------------- release step

def _parse(data: bytes, what: str) -> list[tuple[str, dict]]:
    out = []
    try:
        for line in data.decode("utf-8").splitlines():
            if line.strip():
                out.append((line, json.loads(line)))
    except (UnicodeError, ValueError) as exc:
        raise ReleaseStop(f"STOP: {what} is not JSON lines") from exc
    return out


def _instance_of_pid(pid) -> str:
    parts = str(pid).split(":")
    if len(parts) != 3:
        raise ReleaseStop(f"STOP: proposal id {pid!r} is not source:instance:trial")
    return parts[1]


PUBLISHED_PATHS = ("docs/r1/PLAN.md", PREREG_PATH, RELEASE_PATH, CHECKS_PATH, GATE_PATH, BUILDER_PATH, SPLIT_PATH,
                   SPLIT_V2_PATH, "r1/c3/p3_split.py", "r1/c3/audit.py", "r1/c3/dataset.py", "r1/c3/analysis_guard.py")


def _published_clean(release_checks, extra_paths=()) -> bytes:
    """The release step runs on a clean checkout whose authority and code (and the files the row cites) equal
    ``origin/main``'s; the integrity checks that run are the committed ``release_checks.py``, and the modules the step
    runs are the plain modules beside this file (no shadowing package). Returns the checks module's bytes."""
    if Path(release_checks.__file__).resolve() != (REPO / CHECKS_PATH).resolve():
        raise ReleaseStop(f"STOP: the integrity checks imported are not this checkout's {CHECKS_PATH}")
    from r1.c3 import analysis_guard as _ag, audit as _au, dataset as _ds, p3_split as _ps
    here = Path(__file__).resolve().parent
    for mod in (_ag, _au, _ds, _ps):
        name = mod.__name__.rsplit(".", 1)[1]
        if Path(mod.__file__).resolve() != here / f"{name}.py":
            raise ReleaseStop(f"STOP: r1.c3.{name} is not the module file beside release.py (shadowed?)")
    data = _committed(CHECKS_PATH)
    try:
        dirty = _git("status", "--porcelain", "--untracked-files=no").decode().strip()
        differs = subprocess.run(["git", "-C", str(REPO), "diff", "--quiet", "refs/remotes/origin/main", "HEAD", "--",
                                  *PUBLISHED_PATHS, *extra_paths], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL).returncode
    except _GIT_ERRORS as exc:
        raise ReleaseStop("STOP: the checkout's state cannot be read") from exc
    if dirty:
        raise ReleaseStop("STOP: the release step runs on a clean checkout (tracked changes present)")
    if differs != 0:
        raise ReleaseStop("STOP: the release authority and code differ from origin/main (not published)")
    return data


def refuse_g5_engineering(table_dir: Path, *other_paths: Path) -> None:
    """Refuse P11 artifacts before a release can read a data partition."""
    root = (Path.home() / "r1_engineering" / "g5-p11").resolve()
    if any(path.resolve().is_relative_to(root) for path in (table_dir, *other_paths)):
        raise ReleaseStop("STOP: P11 engineering outputs cannot enter a G.5 release")
    metadata = table_dir / "build.json"
    if metadata.is_file():
        try:
            build = json.loads(metadata.read_bytes())
        except (OSError, ValueError):
            return  # The existing integrity check handles malformed evidence metadata.
        if isinstance(build, dict) and build.get("label") == "ENGINEERING_ONLY":
            raise ReleaseStop("STOP: P11 engineering outputs cannot enter a G.5 release")


def release(stage: str, *, source: str, table_dir, audit_dir, out_root, integrity_args: dict) -> dict:
    """Write the receipted partition of (source, stage); returns the receipt. Refuses an existing output."""
    from r1.c3 import release_checks
    if source not in SOURCES or stage not in STAGES:
        raise ReleaseStop(f"STOP: unknown source/stage {source}/{stage}")
    tier = SOURCES[source]
    table_dir, audit_dir, out_root = Path(table_dir), Path(audit_dir), Path(out_root)
    refuse_sealed(table_dir, audit_dir, out_root)
    if source == "g5":
        refuse_g5_engineering(table_dir, audit_dir, out_root)
    head = _head()
    require_d8_confirmation()
    row = release_row(tier, stage, writing=True)
    out = out_root / source / stage
    if out.exists():
        raise ReleaseStop(f"STOP: {out} exists; a release is written once")
    proposals = (table_dir / "proposals.jsonl").read_bytes()
    label_bytes = (audit_dir / "label_block.jsonl").read_bytes()
    if stage == "test":
        prior = open_partition(out_root / source / "traindev", expect_source=source, expect_stage="traindev")[1]
        if prior["inputs"]["label_block_sha256"] != _sha(label_bytes) or \
                prior["inputs"]["proposals_sha256"] != _sha(proposals):
            raise ReleaseStop("STOP: the test release must use the label block and table of the traindev release")
    cited = ([row["arms_frozen_path"]] if "arms_frozen_path" in row else []) + \
        [v["path"] for v in (row.get("g1b_summaries") or {}).values()] + \
        ([SPLIT_AMENDMENT_PATH] if row["split_sha256"] == p3_split.P3_SPLIT_V2_SHA256 else [])
    checks_bytes = _published_clean(release_checks, cited)
    check = release_checks.INTEGRITY_CHECKS.get(source)
    if check is None:
        raise ReleaseStop(f"STOP: no reviewed integrity check for {source} (§6 carve-out); add one to "
                          f"{CHECKS_PATH} before its release")
    failure = None
    try:
        integrity = check(table_dir, audit_dir, **integrity_args)
    except Exception as exc:  # pass/fail only: no value leaves the check
        failure = type(exc).__name__
    if failure is not None:
        raise ReleaseStop(f"STOP: integrity check failed for {source} ({failure})")
    completion = integrity.get("completion") or {}
    if completion.get("label_block_sha256") != _sha(label_bytes):
        raise ReleaseStop("STOP: the label block read is not the one the integrity check verified")
    from r1.c3.dataset import load_table
    assign = _row_assignment(row)                       # the split file the row cites (v1 or v2)
    inst_of = {}
    for r in load_table(table_dir):
        inst = p3_split.instance_id(r["node"], r["instance_seed"])
        if inst not in assign:
            raise ReleaseStop(f"STOP: table instance {inst} is not in the P3 split file (§6)")
        inst_of[r["proposal_id"]] = inst
    if _sha((table_dir / "proposals.jsonl").read_bytes()) != _sha(proposals):
        raise ReleaseStop("STOP: the table changed during the release")
    labels = _parse(label_bytes, "the label block")
    evals = []
    if stage == "test":
        with integrity_context():
            eval_bytes = (audit_dir / "evaluation_block.jsonl").read_bytes()
        if completion.get("evaluation_block_sha256") != _sha(eval_bytes):
            raise ReleaseStop("STOP: the evaluation block read is not the one the integrity check verified")
        evals = _parse(eval_bytes, "the evaluation block")
    parts = {"train": [], "dev": [], "test": []}
    kinds = {"train": {}, "dev": {}, "test": {}}       # counts by label kind (divergence diagnostics, no values)
    for line, row_ in labels:
        inst = inst_of.get(row_.get("proposal_id"))
        if inst is None or _instance_of_pid(row_["proposal_id"]) != inst:
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
               "head": head, "published": _git("rev-parse", "refs/remotes/origin/main").decode().strip(),
               "release_checks_sha256": _sha(checks_bytes),
               "inputs": {"proposals_sha256": _sha(proposals), "label_block_sha256": _sha(label_bytes),
                          **({"evaluation_block_sha256": _sha(eval_bytes)} if stage == "test" else {})},
               "outputs": outputs,
               "counts": {"label_rows": {k: len(v) for k, v in parts.items()}, "label_kinds": kinds,
                          "released_label_rows": sum(len(v) for k, v in parts.items()
                                                     if (k == "test") == (stage == "test")),
                          "evaluation_rows": len(evals)},
               "integrity": integrity, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if _head() != head:
        raise ReleaseStop("STOP: the checkout HEAD changed during the release")
    (tmp / "RECEIPT.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    tmp.rename(out)
    return receipt


# --------------------------------------------------------------------------------------------- readers

def g5_tail_laws(table_dir, receipt: dict) -> dict[str, tuple[str, float | None]]:
    """Read only the G.5 build metadata bound by a verified release receipt."""
    from r1.c3.labels import STUDENT_T_SCALE, check_tail_law

    path = Path(table_dir) / "build.json"
    refuse_sealed(path)
    if path.is_symlink() or path.resolve().parent != Path(table_dir).resolve():
        raise ReleaseStop("STOP: the G.5 build metadata path is redirected")
    if receipt.get("source") != "g5" or receipt.get("stage") not in STAGES:
        raise ReleaseStop("STOP: a G.5 release receipt is required for tail-law metadata")
    expected = ((receipt.get("integrity") or {}).get("completion") or {}).get("build_sha256")
    if not re.fullmatch(_HEX, str(expected)):
        raise ReleaseStop("STOP: the G.5 receipt lacks its build metadata SHA")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ReleaseStop("STOP: the G.5 build metadata is unavailable") from exc
    if _sha(raw) != expected:
        raise ReleaseStop("STOP: the G.5 build metadata differs from the receipt")
    try:
        build = json.loads(raw)
        if build["source"] != "g5" or build["schema"] not in ("g5_t1_table/1", "g5_t1_table/2") or \
                build["proposals_sha256"] != receipt["inputs"]["proposals_sha256"]:
            raise ValueError("G.5 build metadata does not identify the receipted table")
        if not build["nodes"]:
            raise ValueError("the G.5 build has no tail declarations")
        laws = {}
        for node, entry in build["nodes"].items():
            tails, nu = entry.get("tails", "gaussian"), entry.get("nu")
            check_tail_law(tails, nu)
            if tails == "student_t" and entry.get("t_scale") != STUDENT_T_SCALE:
                raise ValueError(f"{node}: the Student-t build does not record sd matching")
            if tails == "gaussian" and {"nu", "t_scale"} & entry.keys():
                raise ValueError(f"{node}: Student-t fields on a Gaussian build entry")
            laws[node] = (tails, nu)
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise ReleaseStop(f"STOP: invalid G.5 tail-law build metadata ({exc})") from exc
    return laws


def open_partition(part_dir, *, expect_source: str, expect_stage: str,
                   receipt_sha256: str | None = None) -> tuple[dict, dict]:
    """({file name: [rows]}, receipt) of one receipted partition; every binding and the P3 membership of every row
    are re-checked."""
    part_dir = Path(part_dir)
    refuse_sealed(part_dir)
    if expect_source in D8_SOURCES:
        require_d8_confirmation()
    rp = part_dir / "RECEIPT.json"
    if not rp.is_file():
        raise ReleaseStop(f"STOP: {part_dir} has no release receipt; readers open only receipted partitions")
    raw = rp.read_bytes()
    if receipt_sha256 is not None and _sha(raw) != receipt_sha256:
        raise ReleaseStop(f"STOP: {rp} is not the pinned receipt")
    try:
        receipt = json.loads(raw)
    except ValueError as exc:
        raise ReleaseStop(f"STOP: {rp} is not JSON") from exc
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("source") != expect_source or \
            receipt.get("stage") != expect_stage or SOURCES.get(expect_source) != receipt.get("tier"):
        raise ReleaseStop(f"STOP: {rp} is not the {expect_source}/{expect_stage} release receipt")
    if set(receipt.get("outputs", {})) != set(PARTITIONS[expect_stage]):
        raise ReleaseStop(f"STOP: {rp} lists other partition files")
    row = release_row(receipt["tier"], expect_stage)
    if receipt.get("g5_tail_amendment_sha256") != row.get("g5_tail_amendment_sha256"):
        raise ReleaseStop(f"STOP: {rp} no longer matches {row['row_id']} (g5_tail_amendment_sha256)")
    for k, v in row.items():
        if receipt.get(k) != v:
            raise ReleaseStop(f"STOP: {rp} no longer matches {row['row_id']} ({k})")
    assign = _row_assignment(row)
    out = {}
    for name, digest in receipt["outputs"].items():
        data = (part_dir / name).read_bytes()
        if _sha(data) != digest:
            raise ReleaseStop(f"STOP: {part_dir / name} differs from its receipt")
        rows = [r for _, r in _parse(data, name)]
        allowed = {"label_block.traindev.jsonl": {"train", "dev"}, "label_block.test.jsonl": {"test"},
                   "evaluation_block.all.jsonl": {"train", "dev", "test"}}[name]
        for r in rows:
            inst = _instance_of_pid(r.get("proposal_id"))
            if inst not in assign or assign[inst]["split"] not in allowed or assign[inst]["node"] != r.get("node"):
                raise ReleaseStop(f"STOP: {part_dir / name} holds a row outside its P3 partition")
        want = receipt["counts"]["evaluation_rows"] if name.startswith("evaluation") else \
            receipt["counts"]["released_label_rows"]
        if len(rows) != want:
            raise ReleaseStop(f"STOP: {part_dir / name} row count differs from its receipt")
        out[name] = rows
    return out, receipt


def traindev_labels(release_root, source: str, *, receipt_sha256: str | None = None) -> tuple[list[dict], dict]:
    """The released train/dev label rows of a source and their receipt (arms training, selection, A2's fit)."""
    parts, receipt = open_partition(Path(release_root) / source / "traindev", expect_source=source,
                                    expect_stage="traindev", receipt_sha256=receipt_sha256)
    return parts["label_block.traindev.jsonl"], receipt


def g5_consumer_rows(receipt: dict, rows: list[dict]) -> list[dict]:
    """Exclude S9 descriptive tasks from an authorized v2 G.5 consumer's input."""
    if receipt.get("source") == "g5" and receipt.get("split_sha256") == p3_split.P3_SPLIT_V2_SHA256:
        return [r for r in rows if r["node"] not in p3_split.T1_EXTRA_TASKS]
    return rows


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
    td, rtd = open_partition(root / "traindev", expect_source=source, expect_stage="traindev")
    ts, rts = open_partition(root / "test", expect_source=source, expect_stage="test")
    if rtd["inputs"]["label_block_sha256"] != rts["inputs"]["label_block_sha256"] or \
            rtd["inputs"]["proposals_sha256"] != rts["inputs"]["proposals_sha256"]:
        raise ReleaseStop(f"STOP: the {source} partitions come from different label blocks or tables")
    if _sha((Path(table_dir) / "proposals.jsonl").read_bytes()) != rts["inputs"]["proposals_sha256"]:
        raise ReleaseStop(f"STOP: {table_dir} is not the table the {source} partitions were released from")
    labels = td["label_block.traindev.jsonl"] + ts["label_block.test.jsonl"]
    rows, evaluations = load_table(Path(table_dir)), ts["evaluation_block.all.jsonl"]
    split_sha, tail_laws = None, {}
    if source == "g5":
        split_sha = rts["split_sha256"]
        if split_sha != rtd["split_sha256"]:
            raise ReleaseStop("STOP: the G.5 partitions bind different split files")
        if rtd.get("g5_tail_amendment_sha256") != rts.get("g5_tail_amendment_sha256"):
            raise ReleaseStop("STOP: the G.5 partitions bind different tail-law amendments")
        if rtd.get("g5_tail_amendment_sha256"):
            tail_laws = g5_tail_laws(table_dir, rtd)
            if tail_laws != g5_tail_laws(table_dir, rts):
                raise ReleaseStop("STOP: the G.5 partitions bind different tail laws")
        rows, labels, evaluations = (g5_consumer_rows(rts, records) for records in (rows, labels, evaluations))
        if split_sha == p3_split.P3_SPLIT_V2_SHA256:
            tail_laws = {node: law for node, law in tail_laws.items() if node not in p3_split.T1_EXTRA_TASKS}
    return Source(source, rows, labels, evaluations, split_sha256=split_sha, tail_laws=tail_laws)


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
