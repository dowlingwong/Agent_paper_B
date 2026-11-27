"""Staged release and partition locks (PRE-STAGE A): synthetic only.

A pytest-owned Git checkout carries copies of the gate, the gate-input builder and the release step, a synthetic
frozen preregistration, a synthetic arms-frozen record, a synthetic G.1b summary and a synthetic PLAN, with an
``origin/main`` ref; tables and audit blocks are synthetic (the builder test's world). No real label, audit value,
sealed file or author row is used.
"""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from r1.c3 import analysis_guard, audit, gate_input_builder as B, p3_split, release as R, release_checks
from r1.harness import REPO

sys.path.insert(0, str(Path(__file__).parent))
import test_gate_input_builder as W  # noqa: E402  (synthetic world)

ARMS = "docs/r1/reviews/ARMS_FROZEN_SYNTHETIC.md"
G1B = "results/r1/g1b_synthetic/mlab_cifar10_summary.json"
INDEX_SHA = "ab" * 32                 # not the sweep-1 index: a sweep-2 label block
OPENED, RECORDING = [], [False]


def _hook(event, args):
    if RECORDING[0] and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        OPENED.append(os.fsdecode(args[0]))


sys.addaudithook(_hook)               # one hook for the module, recording only inside ``recording()``


class recording:
    def __enter__(self):
        OPENED.clear(); RECORDING[0] = True
        return OPENED

    def __exit__(self, *a):
        RECORDING[0] = False


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


class Paper:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir()
        _git(root, "init", "-q")
        for rel in (R.GATE_PATH, R.BUILDER_PATH, R.RELEASE_PATH, R.CHECKS_PATH):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, root / rel)
        self.gate_sha = _sha((root / R.GATE_PATH).read_bytes())
        self.builder_sha = _sha((root / R.BUILDER_PATH).read_bytes())
        self.write(R.PREREG_PATH, self.prereg())
        self.write(ARMS, "arms frozen (synthetic)\n")
        self.write(G1B, '{"synthetic": true}\n')
        self.code = self.commit("code")
        self.publish()
        self.prereg_sha = _sha((root / R.PREREG_PATH).read_bytes())
        self.arms_sha = _sha((root / ARMS).read_bytes())
        self.g1b_sha = _sha((root / G1B).read_bytes())

    def prereg(self, *, frozen="true", builder=None, gate=None, split=None, stage="A", extra="", block_extra="",
               tail=""):
        split = split or f"{R.SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}"
        decisions = "".join(f"{k}: {stage if k == 'pre_stage' else v}\n" for k, v in R.SIGNED_DECISIONS.items())
        return ("# synthetic preregistration\n\nfrozen: false (an earlier draft line, outside the block)\n\n"
                f"{extra}```\nfrozen: {frozen}\nsplit_file: {split}\n{decisions}"
                f"gate_sha256: {gate or self.gate_sha}\ngate_input_builder_sha256: {builder or self.builder_sha}\n"
                f"signed_by: synthetic\nfrozen_utc: 2026-11-22T00:00:00Z\n{block_extra}```\n{tail}")

    def write(self, rel, text):
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / rel).write_text(text)

    def commit(self, msg):
        _git(self.root, "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg)
        return _git(self.root, "rev-parse", "HEAD")

    def publish(self):
        _git(self.root, "update-ref", "refs/remotes/origin/main", "HEAD")

    def v31(self):
        line = next(l for l in (REPO / "docs/r1/PLAN.md").read_text().splitlines()
                    if l.startswith("| R1-BX-D8-CONFIRM-V31 |"))
        cell = line.split("|")[2].strip()
        start = cell.index("@ `") + 3
        return cell[:start] + self.code + cell[cell.index("`", start):]

    def row(self, tier, stage, **kw):
        args = {"prereg": self.prereg_sha, "split": p3_split.P3_SPLIT_SHA256, "commit": self.code}
        if stage == "test":
            args.update(arms_path=ARMS, arms=self.arms_sha)
        if tier == "T1" and stage == "traindev":
            args.update(g1b={"mlab_cifar10": (G1B, self.g1b_sha)})
        args.update(kw)
        return R.row_text(tier, stage, **args)

    def plan(self, rows, *, raw=None, v31=True, publish=True):
        body = "".join(f"| {i} | {d} |\n" for i, d in ([("R1-BX-D8-CONFIRM-V31", self.v31())] if v31 else []) + rows)
        self.write("docs/r1/PLAN.md", "# PLAN\n\n## 10. Open decisions\n\n### 22 November 2026 — synthetic (author)\n\n"
                                      "| ID | Decision |\n|---|---|\n" + body + (raw or ""))
        head = self.commit("plan")
        if publish:
            self.publish()
        return head


@pytest.fixture
def paper(tmp_path, monkeypatch):
    p = Paper(tmp_path / "paper")
    monkeypatch.setattr(R, "REPO", p.root)
    monkeypatch.setattr(analysis_guard, "REPO", p.root)
    monkeypatch.setattr(release_checks, "INTEGRITY_CHECKS", {"sweep2": _fake_integrity, "sweep1": _fake_integrity})
    monkeypatch.setattr(release_checks, "__file__", str(p.root / R.CHECKS_PATH))   # the synthetic checkout's copy
    return p


def _fake_integrity(table_dir, audit_dir, **kw):
    lb = (Path(audit_dir) / "label_block.jsonl").read_bytes()
    eb = (Path(audit_dir) / "evaluation_block.jsonl").read_bytes()
    return {"check": "synthetic", "pass": True,
            "completion": {"schema": "r1.c3_audit_completion/2", "label": "EVIDENCE", "label_block_sha256": _sha(lb),
                           "evaluation_block_sha256": _sha(eb),
                           "label_seeds": [7001, 7002, 7003, 7004, 7005], "index_sha256": INDEX_SHA}}


@pytest.fixture(scope="module")
def world():
    return W._world()


def _write_audit(aud, srcs):
    aud.mkdir(exist_ok=True)
    (aud / "label_block.jsonl").write_text("".join(json.dumps(r) + "\n" for r in srcs[0].labels))
    (aud / "evaluation_block.jsonl").write_text("".join(json.dumps(r) + "\n" for r in srcs[0].evaluations))
    (aud / "evidence_completion.json").write_text("{}\n")


@pytest.fixture
def data(tmp_path, world):
    srcs = world[0]
    table, aud = tmp_path / "table", tmp_path / "audit"
    table.mkdir()
    (table / "build.json").write_text(json.dumps({"label": "EVIDENCE"}))
    (table / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in srcs[0].rows))
    _write_audit(aud, srcs)
    return table, aud, tmp_path / "released"


def _release(stage, data, source="sweep2"):
    table, aud, out = data
    return R.release(stage, source=source, table_dir=table, audit_dir=aud, out_root=out, integrity_args={})


def T0_ROWS(p):
    return [("R1-S2-LABELS-TRAINDEV-RELEASE", p.row("T0", "traindev")),
            ("R1-S2-LABELS-TEST-RELEASE", p.row("T0", "test"))]


# ---------------------------------------------------------------------------------------------------- rows

def test_row_text_round_trips_the_exact_pattern():
    for tier in R.TIERS:
        for stage in R.STAGES:
            kw = {"prereg": "1" * 64, "split": "2" * 64, "commit": "3" * 40}
            if stage == "test":
                kw.update(arms_path="docs/r1/x/ARMS.md", arms="4" * 64)
            if tier == "T1" and stage == "traindev":
                kw.update(g1b={"mlab_cifar10": ("results/a.json", "5" * 64), "mlgym_fmnist": ("results/b.json", "6" * 64)})
            m = re.fullmatch(R.row_pattern(tier, stage), R.row_text(tier, stage, **kw))
            assert m and m.group("prereg") == "1" * 64 and m.group("commit") == "3" * 40


def test_author_rows_find_what_the_analysis_guard_finds_on_the_real_plan():
    plan = (REPO / "docs/r1/PLAN.md").read_text()
    gate_sha = _sha((REPO / "r1/c3/gate.py").read_bytes())
    rows = [d for i, d in R.author_rows(plan) if i == analysis_guard.CONFIRM_V31_ID]
    assert len(rows) == 1 and re.fullmatch(analysis_guard._confirm_v31_pattern(gate_sha), rows[0])
    # main 985dd45d signed the T0 train/dev row; the test rows and the T1 rows are not on the plan yet. The signed
    # row parses as the release step reads it (prereg, split and release commit as published).
    released = [i for i, _ in R.author_rows(plan) if i in R.ROWS.values()]
    assert released == [R.ROWS[("T0", "traindev")]]
    row = R.release_row("T0", "traindev")
    assert row["row_id"] == "R1-S2-LABELS-TRAINDEV-RELEASE"


@pytest.mark.parametrize("case,match", [
    ("wrong_text", "exact release text"), ("duplicate", "not unique"), ("t1_text_in_t0_row", "exact release text"),
    ("fenced", "absent"), ("comment", "absent"), ("indented", "absent"), ("non_author_heading", "absent"),
    ("split", "another split file"), ("prereg_sha", "another preregistration"),
    ("not_frozen", "not frozen"), ("builder", "gate-input builder"), ("gate", "committed gate"),
    ("frozen_outside_block", "does not end with"), ("missing_key", "lacks"), ("repeated_key", "repeats"),
    ("split_substring", "split_file must read exactly"), ("pre_stage_b", "differ from the signed"),
    ("unpublished_commit", "published"), ("release_bytes", "running r1/c3/release.py"),
    ("appendix_block_after", "2 fenced blocks"), ("commented_block_after", "not frozen"),
    ("changed_decision", "differ from the signed"), ("extra_key", "other keys"),
    ("unpublished_plan", "not published"), ("dirty_checkout", "clean checkout"),
    ("dirty_checks", "differs from committed HEAD"), ("unpublished_checks", "not published"),
])
def test_release_row_and_freeze_refusals(paper, data, case, match):
    row = paper.row("T0", "traindev")
    rid = "R1-S2-LABELS-TRAINDEV-RELEASE"
    rows, raw = [(rid, row)], None
    if case == "wrong_text":
        rows = [(rid, row.replace("No test label", "No label"))]
    elif case == "duplicate":
        rows = rows * 2
    elif case == "t1_text_in_t0_row":
        rows = [(rid, paper.row("T1", "traindev"))]
    elif case in ("fenced", "comment", "indented", "non_author_heading"):
        rows, cell = [], f"| {rid} | {row} |\n"
        raw = {"fenced": f"\n```\n{cell}```\n", "comment": f"\n<!--\n{cell}-->\n",
               "indented": f"\n    | ID | Decision |\n    |---|---|\n    {cell}",
               "non_author_heading": f"\n### 23 November 2026 — notes\n\n| ID | Decision |\n|---|---|\n{cell}"}[case]
    elif case == "split":
        rows = [(rid, paper.row("T0", "traindev", split="5" * 64))]
    elif case == "prereg_sha":
        rows = [(rid, paper.row("T0", "traindev", prereg="6" * 64))]
    elif case in ("not_frozen", "builder", "gate", "frozen_outside_block", "missing_key", "repeated_key",
                  "split_substring", "pre_stage_b", "appendix_block_after", "commented_block_after",
                  "changed_decision", "extra_key"):
        good = paper.prereg()
        frozen_block = good[good.index("```"):]
        kw = {"not_frozen": {"frozen": "false"}, "builder": {"builder": "0" * 64}, "gate": {"gate": "0" * 64},
              "frozen_outside_block": {"frozen": "false", "tail": "\nfrozen: true\n"},
              "repeated_key": {"block_extra": "frozen: true\n"},
              "split_substring": {"split": f"<pending: {p3_split.P3_SPLIT_SHA256}>"},
              "pre_stage_b": {"stage": "B"},
              "appendix_block_after": {"frozen": "false", "tail": "\n## Appendix: the block after freeze\n\n" + frozen_block},
              "commented_block_after": {"frozen": "false", "tail": "\n<!--\n" + frozen_block + "-->\n"},
              "extra_key": {"block_extra": "note: x\n"}}.get(case, {})
        text = paper.prereg(**kw)
        if case == "missing_key":
            text = text.replace("pre_stage: A\n", "")
        if case == "changed_decision":
            text = text.replace("pre_mem: C\n", "pre_mem: A\n")
        paper.write(R.PREREG_PATH, text)
        paper.commit("prereg variant")
        paper.prereg_sha = _sha((paper.root / R.PREREG_PATH).read_bytes())
        rows = [(rid, paper.row("T0", "traindev"))]
    elif case == "unpublished_commit":
        paper.write("r1/other.txt", "x\n")
        rows = [(rid, paper.row("T0", "traindev", commit=paper.commit("unpublished")))]
    elif case == "release_bytes":
        paper.write(R.RELEASE_PATH, (paper.root / R.RELEASE_PATH).read_text() + "# changed\n")
        paper.commit("release changed after the cited commit")
    paper.plan(rows, raw=raw, publish=case not in ("unpublished_plan", "unpublished_commit"))
    if case == "unpublished_checks":                     # only release_checks.py differs from origin/main
        paper.write(R.CHECKS_PATH, (paper.root / R.CHECKS_PATH).read_text() + "# local\n")
        paper.commit("checks changed, not published")

    if case == "dirty_checkout":
        paper.write(R.GATE_PATH.replace("gate.py", "gate_input_builder.py"),
                    (paper.root / R.BUILDER_PATH).read_text())      # unchanged bytes: a clean no-op
        (paper.root / "r1/c3/release_checks.py").touch()
        paper.write("docs/r1/reviews/ARMS_FROZEN_SYNTHETIC.md", "edited, not committed\n")
    if case == "dirty_checks":
        paper.write(R.CHECKS_PATH, (paper.root / R.CHECKS_PATH).read_text() + "def always_pass(): pass\n")
    with pytest.raises(R.ReleaseStop, match=match):
        _release("traindev", data)
    assert not (data[2] / "sweep2").exists()


# ---------------------------------------------------------------------------------------------------- release

def test_traindev_then_test_release_and_the_builder_reads_them(paper, data, world):
    table, aud, out = data
    with pytest.raises(RuntimeError, match="R1-BX-D8-CONFIRM"):              # no PLAN: the D8 check stops first
        _release("traindev", data)
    paper.plan([])
    with pytest.raises(R.ReleaseStop, match="absent"):
        _release("traindev", data)
    paper.plan(T0_ROWS(paper)[:1])
    with pytest.raises(R.ReleaseStop):
        _release("test", data)                                                # no test row (and no traindev yet)
    rec = _release("traindev", data)
    part = out / "sweep2" / "traindev"
    assert sorted(p.name for p in part.iterdir()) == ["RECEIPT.json", "label_block.traindev.jsonl"]
    lines = (part / "label_block.traindev.jsonl").read_text().splitlines()
    orig = (aud / "label_block.jsonl").read_text().splitlines()
    assign = p3_split.assignment(p3_split.load())
    inst = {r["proposal_id"]: r["instance"] for r in world[0][0].rows}
    want = [l for l in orig if assign[inst[json.loads(l)["proposal_id"]]]["split"] in ("train", "dev")]
    assert sorted(lines) == sorted(want) and len(lines) < len(orig)          # byte-identical lines, no test rows
    assert rec["counts"]["evaluation_rows"] == 0 and "evaluation_block_sha256" not in rec["inputs"]
    assert rec["release_checks_sha256"] == _sha(Path(release_checks.__file__).read_bytes())
    with pytest.raises(R.ReleaseStop, match="exists"):
        _release("traindev", data)
    rows, _ = R.traindev_labels(out, "sweep2")
    assert len(rows) == len(lines)
    with pytest.raises(R.ReleaseStop, match="not the sweep2/test"):
        R.open_partition(part, expect_source="sweep2", expect_stage="test")
    with pytest.raises(R.ReleaseStop, match="not the sweep1/traindev"):
        R.open_partition(part, expect_source="sweep1", expect_stage="traindev")
    with pytest.raises(R.ReleaseStop, match="pinned receipt"):
        R.traindev_labels(out, "sweep2", receipt_sha256="0" * 64)
    paper.plan(T0_ROWS(paper))
    rec2 = _release("test", data)
    assert rec2["arms_frozen_sha256"] == paper.arms_sha
    assert rec2["counts"]["evaluation_rows"] == len(world[0][0].evaluations)
    got = B.build([R.builder_source(out, "sweep2", table), world[0][1]], world[1], world[2], t0_nodes=B.SEVEN_T0)
    want_gi = B.build(world[0], world[1], world[2], t0_nodes=B.SEVEN_T0)
    assert json.dumps(got, sort_keys=True) == json.dumps(want_gi, sort_keys=True)


def test_a_later_reviewed_edit_of_release_py_keeps_earlier_receipts_but_not_new_releases(paper, data):
    paper.plan(T0_ROWS(paper)[:1])
    _release("traindev", data)
    paper.write(R.RELEASE_PATH, (paper.root / R.RELEASE_PATH).read_text() + "# later reviewed edit\n")
    paper.commit("release edited")
    paper.publish()
    R.open_partition(data[2] / "sweep2" / "traindev", expect_source="sweep2", expect_stage="traindev")
    paper.plan(T0_ROWS(paper))
    with pytest.raises(R.ReleaseStop, match="running r1/c3/release.py"):
        _release("test", data)


def test_tampered_partitions_and_receipts_are_refused(paper, data):
    table, aud, out = data
    paper.plan(T0_ROWS(paper)[:1])
    _release("traindev", data)
    part = out / "sweep2" / "traindev"
    rec = json.loads((part / "RECEIPT.json").read_text())
    full = (aud / "label_block.jsonl").read_bytes()                        # the whole block, test rows included
    (part / "label_block.traindev.jsonl").write_bytes(full)
    rec["outputs"]["label_block.traindev.jsonl"] = _sha(full)
    rec["counts"]["released_label_rows"] = len(full.splitlines())
    (part / "RECEIPT.json").write_text(json.dumps(rec))
    with pytest.raises(R.ReleaseStop, match="outside its P3 partition"):
        R.open_partition(part, expect_source="sweep2", expect_stage="traindev")
    from r1.c3.train import sft_data
    with pytest.raises(sft_data.SFTDataError, match="outside its P3 partition"):
        sft_data.LabelBlockSource(part / "label_block.traindev.jsonl", sweep="sweep2").label_records()


def test_test_release_needs_the_traindev_label_block(paper, data, world):
    table, aud, out = data
    paper.plan(T0_ROWS(paper))
    _release("traindev", data)
    other = copy.deepcopy(world[0])
    lab = next(l for l in other[0].labels if l["label_kind"] == "audit")
    lab["delta_label"] = lab["soft_parameters"]["delta_label"] = 0.5
    _write_audit(aud, other)
    with pytest.raises(R.ReleaseStop, match="label block and table of the traindev release"):
        _release("test", data)


def test_integrity_check_absent_or_failing_writes_nothing_and_leaks_nothing(paper, data, monkeypatch):
    paper.plan(T0_ROWS(paper)[:1])
    monkeypatch.setattr(release_checks, "INTEGRITY_CHECKS", {})
    with pytest.raises(R.ReleaseStop, match="no reviewed integrity check"):
        _release("traindev", data)

    def boom(*a, **k):
        raise ValueError("secret value 0.123")
    monkeypatch.setattr(release_checks, "INTEGRITY_CHECKS", {"sweep2": boom})
    with pytest.raises(R.ReleaseStop) as exc:
        _release("traindev", data)
    assert "ValueError" in str(exc.value) and "0.123" not in str(exc.value)
    assert exc.value.__context__ is None and exc.value.__cause__ is None      # the original message is not kept
    assert not (data[2] / "sweep2").exists()


def test_sweep1_integrity_calls_the_compat_published_guard(monkeypatch, tmp_path):
    from r1.c3 import sweep1_compat
    monkeypatch.setattr(release_checks, "_sweep1_compat_published",
                        lambda: (_ for _ in ()).throw(RuntimeError("guard sentinel")))
    (tmp_path / "build.json").write_text(json.dumps({"commit": sweep1_compat.V2_BUILDER_COMMIT}))
    with pytest.raises(RuntimeError, match="guard sentinel"):
        release_checks.sweep1_integrity(tmp_path, tmp_path, paper_root=tmp_path, index=tmp_path,
                                        classification=tmp_path)


def test_sweep1_integrity_refuses_a_table_not_from_the_pinned_commit(monkeypatch, tmp_path):
    monkeypatch.setattr(release_checks, "_sweep1_compat_published", lambda: None)
    (tmp_path / "build.json").write_text(json.dumps({"commit": "0" * 40}))
    with pytest.raises(ValueError, match="pinned v2 builder commit"):
        release_checks.sweep1_integrity(tmp_path, tmp_path, paper_root=tmp_path, index=tmp_path,
                                        classification=tmp_path)


def test_sweep1_integrity_wraps_the_completion_verifier(monkeypatch, tmp_path):
    seen = {}

    def verify(table, label_block, paper_root, index, classification, replay_builder=None):
        R.guard_raw_label_path(label_block.parent / "evaluation_block.jsonl")     # open inside the carve-out
        seen["args"] = (table, label_block.name)
        seen["replay_builder"] = replay_builder
        return {"schema": "r1.c3_audit_completion/2", "label_block_sha256": "a" * 64, "counts": {"n": 1},
                "secret": "not kept"}
    monkeypatch.setattr(audit, "verify_evidence_completion", verify)
    monkeypatch.setattr(release_checks, "_sweep1_compat_published", lambda: None)
    from r1.c3 import sweep1_compat
    (tmp_path / "build.json").write_text(json.dumps({"commit": sweep1_compat.V2_BUILDER_COMMIT}))
    (tmp_path / "evidence_completion.json").write_text("{}")
    out = release_checks.sweep1_integrity(tmp_path, tmp_path, paper_root=tmp_path, index=tmp_path,
                                          classification=tmp_path)
    assert out["pass"] and "secret" not in out["completion"] and seen["args"][1] == "label_block.jsonl"
    from r1.c3 import sweep1_compat
    assert seen["replay_builder"] is sweep1_compat.rebuild_v2_table


def test_t1_rows_bind_the_g1b_summaries_and_sources_without_checks_stop(paper, data):
    paper.plan([("R1-T1-LABELS-UNSEAL", paper.row("T1", "traindev"))])
    assert R.release_row("T1", "traindev")["g1b_summaries"] == {"mlab_cifar10": {"path": G1B, "sha256": paper.g1b_sha}}
    with pytest.raises(R.ReleaseStop, match="no reviewed integrity check for g5"):
        _release("traindev", data, source="g5")
    paper.write(G1B, '{"changed": true}\n')
    paper.commit("g1b changed")
    with pytest.raises(R.ReleaseStop, match="G.1b summary"):
        R.release_row("T1", "traindev")


def test_partition_readers_check_d8_before_opening(paper, data):
    paper.plan(T0_ROWS(paper)[:1])
    _release("traindev", data)
    paper.plan(T0_ROWS(paper)[:1], v31=False)
    with recording() as opened, pytest.raises(RuntimeError, match="R1-BX-D8-CONFIRM"):
        R.open_partition(data[2] / "sweep2" / "traindev", expect_source="sweep2", expect_stage="traindev")
    assert not any(Path(p).name in ("RECEIPT.json", "label_block.traindev.jsonl") for p in opened)


def test_test_released_is_false_not_an_error_when_git_misbehaves(paper, monkeypatch):
    paper.plan(T0_ROWS(paper))
    monkeypatch.setattr(R, "_git", lambda *a, **k: "text, not bytes")
    assert R.test_released("T0") is False


# ---------------------------------------------------------------------------------------------------- locks

def test_locks_on_the_existing_readers(paper, data, tmp_path):
    table, aud, _ = data
    paper.plan([])
    (aud / "runs.jsonl").write_text('{"node": "digits_mlp", "config_hash": "h", "seed": 7006, "metric": 0.5}\n')
    (aud / "audits.jsonl").write_text('{"proposal_id": "x", "seeds": [7001]}\n')
    alias = tmp_path / "elsewhere"
    alias.mkdir()
    (alias / "labels.jsonl").symlink_to(aud / "label_block.jsonl")
    from r1.c3 import ni_masking, offline_eval
    readers = [
        lambda: R.guard_raw_label_path(aud / "label_block.jsonl"),
        lambda: R.guard_raw_label_path(alias / "labels.jsonl"),                # a symlink under another name
        lambda: R.guard_raw_label_path(aud / "audits.jsonl"),                   # a legacy file in a B.2 directory
        lambda: audit.RunCache(aud / "runs.jsonl"),
        lambda: audit.verify_evidence_completion(table, aud / "label_block.jsonl", paper.root, table, table),
        lambda: offline_eval.assemble(table, aud / "label_block.jsonl"),
        lambda: ni_masking.load_audits(table, aud / "audits.jsonl"),
    ]
    for reader in readers:
        with recording() as opened, pytest.raises(R.ReleaseStop, match="PRE-STAGE A"):
            reader()
        assert not any(Path(p).parent in (aud, alias) and Path(p).name != "evidence_completion.json"
                       for p in opened), opened                               # completion metadata only
    with pytest.raises(R.ReleaseStop, match="evidence audit directory"):
        audit.main(["collect", "--plan", str(table / "build.json"), "--out", str(aud)])
    (aud / "seed_journals").mkdir()
    (aud / "seed_journals" / "j.jsonl").write_text((aud / "runs.jsonl").read_text())
    with pytest.raises(R.ReleaseStop, match="PRE-STAGE A"):
        audit.RunCache(aud / "seed_journals" / "j.jsonl")                      # a seed journal below the evidence dir
    g5 = tmp_path / "g5_audit"                                                   # an evidence dir of unknown tier
    g5.mkdir()
    (g5 / "label_block.jsonl").write_text("")
    (g5 / "runs.jsonl").write_text((aud / "runs.jsonl").read_text())
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / "audits.jsonl").write_text("")
    R.guard_raw_label_path(pilot / "audits.jsonl")                            # pilot tables keep their path
    with R.integrity_context():
        R.guard_raw_label_path(aud / "evaluation_block.jsonl")                # the release step's carve-out
    with R.producer_context():
        audit.RunCache(aud / "runs.jsonl")                                    # the evidence writer reads back
    paper.plan(T0_ROWS(paper))
    R.guard_raw_label_path(aud / "evaluation_block.jsonl", "T0")              # after the T0 test release row
    (aud / "evidence_completion.json").write_text('{"schema": "r1.c3_audit_completion/2"}')
    audit.RunCache(aud / "runs.jsonl")                                        # a B.2 (T0) run log opens
    with pytest.raises(R.ReleaseStop, match="R1-T1-LABELS-TEST-RELEASE"):
        audit.RunCache(g5 / "runs.jsonl")                                     # tier unknown: both test rows
    with pytest.raises(R.ReleaseStop, match="R1-T1-LABELS-TEST-RELEASE"):
        R.guard_raw_label_path(aud / "evaluation_block.jsonl")                # tier unknown: both test rows needed
    assert R.test_released("T0") and not R.test_released("T1")


def test_label_block_source_partition_refusals(paper, data, monkeypatch):
    from r1.c3.train import sft_data
    paper.plan(T0_ROWS(paper)[:1])
    part = data[2] / "sweep2" / "traindev" / "label_block.traindev.jsonl"

    def release_with(completion_update):
        def fake(table_dir, audit_dir, **kw):
            out = _fake_integrity(table_dir, audit_dir)
            out["completion"].update(completion_update)
            out["completion"] = {k: v for k, v in out["completion"].items() if v is not None}
            return out
        monkeypatch.setattr(release_checks, "INTEGRITY_CHECKS", {"sweep2": fake})
        shutil.rmtree(data[2], ignore_errors=True)      # this test's own synthetic output under pytest's tmp_path
        _release("traindev", data)
    writer_refuses = [({"label_block_sha256": "0" * 64}, "label block read is not"),
                      ({"label_block_sha256": None}, "label block read is not")]           # a result without the hash
    for update, match in writer_refuses:
        with pytest.raises(R.ReleaseStop, match=match):
            release_with(update)
    reader_refuses = [({"schema": None}, {}, "no audit completion"),
                      ({"label_seeds": [7001, 7002, 7003, 7004, 7006]}, {}, "label seeds"),
                      ({"index_sha256": analysis_guard.SWEEP1_INDEX_SHA}, {}, "belongs to sweep1"),
                      ({}, {"index_sha256": "cd" * 32}, "another sweep index"),
                      ({"classification_sha256": "ef" * 32}, {"classification_sha256": "01" * 32}, "classification")]
    for update, kw, match in reader_refuses:
        release_with(update)                                                              # the writer accepts
        with pytest.raises(sft_data.SFTDataError, match=match):
            sft_data.LabelBlockSource(part, sweep="sweep2", **kw).label_records()
    release_with({})
    rp = part.parent / "RECEIPT.json"                    # the reader's own binding of the completion to the block
    rec = json.loads(rp.read_text())
    rec["integrity"]["completion"]["label_block_sha256"] = "1" * 64
    rp.write_text(json.dumps(rec))
    with pytest.raises(sft_data.SFTDataError, match="binds another label block"):
        sft_data.LabelBlockSource(part, sweep="sweep2").label_records()
    shutil.rmtree(data[2], ignore_errors=True)
    release_with({})
    with pytest.raises(sft_data.SFTDataError, match="not the sweep1/traindev"):
        sft_data.LabelBlockSource(part, sweep="sweep1").label_records()
    assert len(sft_data.LabelBlockSource(part, sweep="sweep2").label_records()) > 0


def test_cited_files_must_be_published_and_modules_not_shadowed(paper, data, monkeypatch):
    paper.plan(T0_ROWS(paper))
    _release("traindev", data)
    paper.write(ARMS, "arms changed after publication\n")
    paper.arms_sha = _sha((paper.root / ARMS).read_bytes())
    paper.plan(T0_ROWS(paper), publish=False)                 # the row cites the new record; main has the old one
    _git(paper.root, "update-ref", "refs/remotes/origin/main", "HEAD~1")
    with pytest.raises(R.ReleaseStop, match="not published|published ancestor"):
        _release("test", data)
    paper.publish()
    from r1.c3 import dataset
    monkeypatch.setattr(dataset, "__file__", str(Path(dataset.__file__).parent / "dataset" / "__init__.py"))
    with pytest.raises(R.ReleaseStop, match="shadowed"):
        _release("test", data)


# ---------------------------------------------------------------------------- split file v2 (R1-G5-S9 (1))

def _amendment(paper, **kw):
    lines = {"amends": f"{R.PREREG_PATH} sha256 {paper.prereg_sha}", "plan_row": "R1-G5-S9", "pre_split": "A",
             "split_file": f"{R.SPLIT_V2_PATH} sha256 {p3_split.P3_SPLIT_V2_SHA256}",
             "supersedes_split_file": f"{R.SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}",
             "approved": "true", "frozen": "true", "signed_by": "synthetic", "signed_utc": "2026-11-27T12:00:00Z"}
    lines.update(kw)
    body = "".join(f"{k}: {v}\n" for k, v in lines.items() if v is not None)
    paper.write(R.SPLIT_AMENDMENT_PATH, f"# synthetic PRE-SPLIT amendment\n\napproved: true\n\n```\n{body}```\n")


def _v2_rows(paper):
    return [("R1-G5-S9", "synthetic S9 row"),
            ("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev", split=p3_split.P3_SPLIT_V2_SHA256))]


def test_a_v2_row_needs_the_published_pre_split_amendment_and_partitions_by_v2(paper, data, world):
    paper.plan(_v2_rows(paper))
    with pytest.raises(R.ReleaseStop, match="PRE-SPLIT amendment"):
        R.release_row("T0", "traindev")
    _amendment(paper)
    paper.plan(_v2_rows(paper), publish=False)
    from r1.c3.train import sft_data
    with pytest.raises(R.ReleaseStop, match="must match published main"):
        R.split_v2_amendment()
    with pytest.raises(sft_data.SFTDataError, match="must match published main"):
        sft_data._signed_split({"split_file": sft_data.SIGNED_SPLIT_FILE_V2})
    paper.publish()
    assert sft_data._signed_split({"split_file": sft_data.SIGNED_SPLIT_FILE_V2})
    row = R.release_row("T0", "traindev")
    assert row["split_sha256"] == p3_split.P3_SPLIT_V2_SHA256
    assert R.split_v2_amendment()["path"] == R.SPLIT_AMENDMENT_PATH
    rec = _release("traindev", data)
    assert rec["split_sha256"] == p3_split.P3_SPLIT_V2_SHA256
    rows, _ = R.traindev_labels(data[2], "sweep2")          # the reader re-derives membership by v2
    v1 = p3_split.assignment(p3_split.load())
    assert rows and all(v1[r["proposal_id"].split(":")[1]]["split"] in ("train", "dev") for r in rows)


@pytest.mark.parametrize("kw,match", [
    ({"approved": "false"}, "not published as approved"), ({"frozen": "false"}, "not published as approved"),
    ({"split_file": f"{R.SPLIT_PATH} sha256 {p3_split.P3_SPLIT_SHA256}"}, "not published as approved"),
    ({"plan_row": "R1-OTHER"}, "not published as approved"), ({"signed_utc": "<pending>"}, "signed_utc"),
    ({"signed_by": None}, "exactly"), ({"extra": "x"}, "exactly"), ({"amends": "x sha256 " + "0" * 64}, "approved"),
])
def test_pre_split_amendment_refusals(paper, kw, match):
    _amendment(paper, **kw)
    paper.plan(_v2_rows(paper))
    with pytest.raises(R.ReleaseStop, match=match):
        R.split_v2_amendment()


def test_pre_split_amendment_needs_the_s9_row(paper):
    _amendment(paper)
    paper.plan([("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev"))])
    with pytest.raises(R.ReleaseStop, match="R1-G5-S9 is absent"):
        R.split_v2_amendment()


def test_a_v1_receipt_keeps_partitioning_by_v1(paper, data):
    paper.plan(T0_ROWS(paper)[:1])
    rec = _release("traindev", data)
    assert rec["split_sha256"] == p3_split.P3_SPLIT_SHA256
    assert R._row_assignment({"split_sha256": p3_split.P3_SPLIT_SHA256}) == p3_split.assignment(p3_split.load())
    assert "mlgym_titanic__s5101" in R._row_assignment({"split_sha256": p3_split.P3_SPLIT_V2_SHA256})
    assert "mlgym_titanic__s5101" not in R._row_assignment({"split_sha256": p3_split.P3_SPLIT_SHA256})
    with pytest.raises(R.ReleaseStop, match="cannot be loaded"):
        R._row_assignment({"split_sha256": "0" * 64})


def test_tail_amendment_preserves_historical_receipts_and_binds_future_test(paper, data, monkeypatch):
    from r1.c3 import arms_freeze as AF

    legacy_row = (R.ROWS[("T0", "traindev")], paper.row("T0", "traindev"))
    paper.plan([legacy_row])
    _release("traindev", data)
    partition = data[2] / "sweep2" / "traindev"
    legacy = R.open_partition(partition, expect_source="sweep2", expect_stage="traindev")

    original = (paper.root / R.BUILDER_PATH).read_bytes()
    for path in R.G5_TAILS_CODE_PINS.values():
        if not (paper.root / path).exists():
            paper.write(path, "# synthetic implementation dependency\n")
    paper.write(R.BUILDER_PATH, (paper.root / R.BUILDER_PATH).read_text() + "# synthetic tail-law builder\n")
    implementation = paper.commit("synthetic tail-law implementation")
    paper.publish()
    with pytest.raises(R.ReleaseStop, match="exact signed G.5 tail-law amendment"):
        R.prereg_frozen()
    assert R.open_partition(partition, expect_source="sweep2", expect_stage="traindev") == legacy
    with pytest.raises(AF.ArmsFreezeError, match="exact signed G.5 tail-law amendment"):
        monkeypatch.setattr(AF, "PREREG_SHA256", paper.prereg_sha)
        AF._prereg_block(paper.root)

    fields = {"frozen": "true", "base_preregistration_sha256": paper.prereg_sha,
              "original_gate_input_builder_sha256": paper.builder_sha,
              **{key: _sha((paper.root / path).read_bytes()) for key, path in R.G5_TAILS_CODE_PINS.items()},
              "signed_by": "synthetic", "frozen_utc": "2026-11-27T00:00:00Z"}
    amendment = "# Synthetic amendment\n\n```\n" + "".join(f"{k}: {v}\n" for k, v in fields.items()) + "```\n"
    amendment_sha = _sha(amendment.encode())
    paper.write(R.G5_TAILS_AMENDMENT_PATH, amendment)
    decision = (f"Use the reviewed G.5 tail-law amendment `{R.G5_TAILS_AMENDMENT_PATH}` "
                f"sha256 `{amendment_sha}` with implementation commit `{implementation}`.")
    test_row = (R.ROWS[("T0", "test")], paper.row("T0", "test", tail_amendment=amendment_sha, commit=implementation))
    rows = [legacy_row, test_row, (R.G5_TAILS_AMENDMENT_ROW, decision)]
    paper.plan(rows, publish=False)
    with pytest.raises(R.ReleaseStop, match="must match published main"):
        R.prereg_frozen()
    paper.publish()

    assert R.open_partition(partition, expect_source="sweep2", expect_stage="traindev") == legacy
    with pytest.raises(R.ReleaseStop, match="does not cite the effective G.5 tail-law amendment"):
        R.release_row("T0", "traindev", writing=True)
    assert R.release_row("T0", "test")["prereg_sha256"] == paper.prereg_sha
    assert R.release_row("T0", "test")["g5_tail_amendment_sha256"] == amendment_sha
    assert R.release_row("T0", "test")["builder_sha256"] == fields["gate_input_builder_sha256"]
    monkeypatch.setattr(AF, "PREREG_SHA256", paper.prereg_sha)
    block = AF._prereg_block(paper.root)
    assert block["g5_tail_amendment_sha256"] == amendment_sha
    assert block["gate_input_builder_sha256"] == fields["gate_input_builder_sha256"]

    revised = (paper.root / R.BUILDER_PATH).read_text()
    (paper.root / R.BUILDER_PATH).write_bytes(original)
    paper.commit("synthetic rollback")
    assert _sha((paper.root / R.BUILDER_PATH).read_bytes()) == paper.builder_sha
    with pytest.raises(R.ReleaseStop, match="does not bind r1/c3/gate_input_builder.py"):
        R.prereg_frozen()
    paper.write(R.BUILDER_PATH, revised)
    paper.write("r1/c3/labels.py", "# another implementation\n")
    paper.commit("synthetic code change after approval")
    with pytest.raises(R.ReleaseStop, match="does not bind r1/c3/labels.py"):
        R.prereg_frozen()


def test_g5_tail_laws_come_from_the_receipted_build(tmp_path):
    node = "autoresearch_fixedtokens"
    table_sha = "a" * 64
    build = {"source": "g5", "schema": "g5_t1_table/2", "proposals_sha256": table_sha,
             "nodes": {node: {"tails": "student_t", "nu": 7, "t_scale": "sd_matched"},
                       "mlab_imdb": {}}}
    raw = json.dumps(build).encode()
    path = tmp_path / "build.json"
    path.write_bytes(raw)
    receipt = {"source": "g5", "stage": "traindev", "inputs": {"proposals_sha256": table_sha},
               "integrity": {"completion": {"build_sha256": _sha(raw)}}}
    assert R.g5_tail_laws(tmp_path, receipt) == {node: ("student_t", 7), "mlab_imdb": ("gaussian", None)}
    t1 = B.Tier1(suites={node: "autoresearch"}, modes=("history",))
    assert B.bind_g5_tail_laws(t1, tmp_path, receipt).tail_laws == {node: ("student_t", 7)}
    assert t1.tail_laws == {}

    tampered = copy.deepcopy(build)
    tampered["nodes"][node]["t_scale"] = "fixed_scale"
    path.write_text(json.dumps(tampered))
    with pytest.raises(R.ReleaseStop, match="differs from the receipt"):
        R.g5_tail_laws(tmp_path, receipt)
    receipt["integrity"]["completion"]["build_sha256"] = _sha(path.read_bytes())
    with pytest.raises(R.ReleaseStop, match="does not record sd matching"):
        R.g5_tail_laws(tmp_path, receipt)


def test_gate_reader_and_fold_use_the_receipted_noninitial_tail_law(tmp_path, monkeypatch):
    from r1.c3 import dataset, fold_analysis
    from r1.c3.labels import soft_label

    node = "autoresearch_fixedtokens"
    row = W._row(node, 10, "history", 1, src="g5")
    lab = W._label(row)
    lab["soft_parameters"].update(tails="student_t", nu=7)
    evaluation = W._evaluation(row)
    proposals = json.dumps(row).encode() + b"\n"
    (tmp_path / "proposals.jsonl").write_bytes(proposals)
    build = {"source": "g5", "schema": "g5_t1_table/2", "proposals_sha256": _sha(proposals),
             "nodes": {node: {"tails": "student_t", "nu": 7, "t_scale": "sd_matched"}}}
    raw = json.dumps(build).encode()
    (tmp_path / "build.json").write_bytes(raw)

    def partition(path, *, expect_source, expect_stage):
        receipt = {"source": expect_source, "stage": expect_stage, "g5_tail_amendment_sha256": "a" * 64,
                   "split_sha256": p3_split.P3_SPLIT_SHA256,
                   "inputs": {"proposals_sha256": _sha(proposals), "label_block_sha256": "b" * 64},
                   "integrity": {"completion": {"build_sha256": _sha(raw)}}}
        parts = {"label_block.traindev.jsonl": [lab]} if expect_stage == "traindev" else {
            "label_block.test.jsonl": [], "evaluation_block.all.jsonl": [evaluation]}
        return parts, receipt

    monkeypatch.setattr(R, "open_partition", partition)
    monkeypatch.setattr(dataset, "load_table", lambda path: [row])
    source = R.builder_source(tmp_path, "g5", tmp_path)
    assert source.tail_laws == {node: ("student_t", 7)}
    fold, = fold_analysis.node_subset([source], [node])
    assignment = {row["instance"]: {"node": node, "split": "dev"}}
    t1 = B.Tier1(suites={node: "autoresearch"}, modes=("history",))
    prepared, _, _ = B._prepare([fold], assignment, t1)
    expected = soft_label(lab["delta_label"], None, row["sigma_node"], k_label=5, tails="student_t", nu=7)
    assert prepared[0]["soft"].tobytes() == expected.tobytes()
    t1.tail_laws[node] = ("gaussian", None)
    with pytest.raises(B.BuilderError, match="different tail laws"):
        B._prepare([fold], assignment, t1)
