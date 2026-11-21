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
             arms: str | None = None, g1b: dict | None = None) -> str:
    """The decision text of a release row with the values filled in (for the drafts and tests). ``g1b``:
    {node: (path, sha256)} for the T1 train/dev row (PRE-DELTA)."""
    head = (f"Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`{PREREG_PATH}`, "
            f"sha256 `{prereg}`)")
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


def prereg_frozen(root=None) -> dict:
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
    builder = _sha(_committed(BUILDER_PATH, root))
    gate = _sha(_committed(GATE_PATH, root))
    if block["frozen"] != "true":
        raise ReleaseStop("STOP: the preregistration is not frozen (frozen: true); no label is released before")
    if block["split_file"] != f"{SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}":
        raise ReleaseStop(f"STOP: split_file must read exactly '{SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}'")
    if block["gate_input_builder_sha256"] != builder:
        raise ReleaseStop("STOP: the committed gate-input builder is not the one the preregistration froze")
    if block["gate_sha256"] != gate:
        raise ReleaseStop("STOP: the committed gate is not the one the preregistration binds")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z", block["frozen_utc"]):
        raise ReleaseStop("STOP: the preregistration has no frozen_utc (YYYY-MM-DDTHH:MM[:SS]Z)")
    return {"sha256": _sha(data), "builder_sha256": builder, "gate_sha256": gate}


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
    pre = prereg_frozen(root)
    if m.group("prereg") != pre["sha256"]:
        raise ReleaseStop(f"STOP: {rid} cites another preregistration sha256")
    if m.group("split") != p3_split.P3_SPLIT_SHA256:
        raise ReleaseStop(f"STOP: {rid} cites another split file")
    commit = m.group("commit")
    try:
        _git("merge-base", "--is-ancestor", commit, "HEAD", root=root)
        _git("merge-base", "--is-ancestor", commit, "refs/remotes/origin/main", root=root)
        declared = _git("show", f"{commit}:{RELEASE_PATH}", root=root)
    except _GIT_ERRORS as exc:
        raise ReleaseStop(f"STOP: {rid}'s release-code commit is not a published ancestor with {RELEASE_PATH}") from exc
    if writing and declared != _committed(RELEASE_PATH, root):
        raise ReleaseStop(f"STOP: the running {RELEASE_PATH} is not the one {rid} cites")
    out = {"row_id": rid, "decision_sha256": _sha(rows[0].encode()), "prereg_sha256": pre["sha256"],
           "builder_sha256": pre["builder_sha256"], "gate_sha256": pre["gate_sha256"],
           "split_sha256": m.group("split"), "release_commit": commit}
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
                   "r1/c3/p3_split.py", "r1/c3/audit.py", "r1/c3/dataset.py", "r1/c3/analysis_guard.py")


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


def release(stage: str, *, source: str, table_dir, audit_dir, out_root, integrity_args: dict) -> dict:
    """Write the receipted partition of (source, stage); returns the receipt. Refuses an existing output."""
    from r1.c3 import release_checks
    if source not in SOURCES or stage not in STAGES:
        raise ReleaseStop(f"STOP: unknown source/stage {source}/{stage}")
    tier = SOURCES[source]
    table_dir, audit_dir, out_root = Path(table_dir), Path(audit_dir), Path(out_root)
    refuse_sealed(table_dir, audit_dir, out_root)
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
        [v["path"] for v in (row.get("g1b_summaries") or {}).values()]
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
    assign = p3_split.assignment(p3_split.load())
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
    for k, v in row.items():
        if receipt.get(k) != v:
            raise ReleaseStop(f"STOP: {rp} no longer matches {row['row_id']} ({k})")
    assign = p3_split.assignment(p3_split.load())
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
