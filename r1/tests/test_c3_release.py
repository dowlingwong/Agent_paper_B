"""Staged release and partition locks (PRE-STAGE A): synthetic only.

A pytest-owned Git checkout carries copies of the gate, the gate-input builder and the release step, a synthetic
frozen preregistration, a synthetic arms-frozen record and a synthetic PLAN; tables and audit blocks are synthetic
(the builder test's world). No real label, audit value, sealed file or author row is used.
"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from r1.c3 import analysis_guard, audit, gate_input_builder as B, p3_split, release as R
from r1.harness import REPO

sys.path.insert(0, str(Path(__file__).parent))
import test_gate_input_builder as W  # noqa: E402  (synthetic world)

ARMS = "docs/r1/reviews/ARMS_FROZEN_SYNTHETIC.md"
INDEX_SHA = "ab" * 32                 # not the sweep-1 index: a sweep-2 label block


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


class Paper:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir()
        _git(root, "init", "-q")
        for rel in (R.GATE_PATH, R.BUILDER_PATH, R.RELEASE_PATH):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, root / rel)
        self.gate_sha = _sha((root / R.GATE_PATH).read_bytes())
        self.builder_sha = _sha((root / R.BUILDER_PATH).read_bytes())
        self.write(R.PREREG_PATH, self.prereg())
        self.write(ARMS, "arms frozen (synthetic)\n")
        self.code = self.commit("code")
        self.prereg_sha = _sha((root / R.PREREG_PATH).read_bytes())
        self.arms_sha = _sha((root / ARMS).read_bytes())

    def prereg(self, frozen="true", builder=None, split=None):
        return ("# synthetic preregistration\n\n```\n"
                f"frozen: {frozen}\nsplit_file: r1/c3/splits/c3_p3_split_v1.json sha256 {split or p3_split.P3_SPLIT_SHA256}\n"
                f"gate_sha256: {self.gate_sha}\ngate_input_builder_sha256: {builder or self.builder_sha}\n"
                "frozen_utc: 2026-11-22T00:00:00Z\n```\n")

    def write(self, rel, text):
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / rel).write_text(text)

    def commit(self, msg):
        _git(self.root, "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg)
        return _git(self.root, "rev-parse", "HEAD")

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
        args.update(kw)
        return R.row_text(tier, stage, **args)

    def plan(self, rows):
        body = "".join(f"| {i} | {d} |\n" for i, d in [("R1-BX-D8-CONFIRM-V31", self.v31()), *rows])
        self.write("docs/r1/PLAN.md", "# PLAN\n\n## 10. Open decisions\n\n### 22 November 2026 — synthetic (author)\n\n"
                                      "| ID | Decision |\n|---|---|\n" + body)
        return self.commit("plan")


@pytest.fixture
def paper(tmp_path, monkeypatch):
    p = Paper(tmp_path / "paper")
    monkeypatch.setattr(R, "REPO", p.root)
    monkeypatch.setattr(analysis_guard, "REPO", p.root)
    monkeypatch.setattr(R, "INTEGRITY_CHECKS", {"sweep2": _fake_integrity, "sweep1": _fake_integrity})
    return p


def _fake_integrity(table_dir, audit_dir, **kw):
    lb = (Path(audit_dir) / "label_block.jsonl").read_bytes()
    return {"check": "synthetic", "pass": True,
            "completion": {"schema": "r1.c3_audit_completion/2", "label": "EVIDENCE", "label_block_sha256": _sha(lb),
                           "label_seeds": [7001, 7002, 7003, 7004, 7005], "index_sha256": INDEX_SHA}}


@pytest.fixture(scope="module")
def world():
    return W._world()


@pytest.fixture
def data(tmp_path, world):
    srcs = world[0]
    table, aud = tmp_path / "table", tmp_path / "audit"
    table.mkdir(); aud.mkdir()
    (table / "build.json").write_text(json.dumps({"label": "EVIDENCE"}))
    (table / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in srcs[0].rows))
    (aud / "label_block.jsonl").write_text("".join(json.dumps(r) + "\n" for r in srcs[0].labels))
    (aud / "evaluation_block.jsonl").write_text("".join(json.dumps(r) + "\n" for r in srcs[0].evaluations))
    return table, aud, tmp_path / "released"


def _release(stage, data, source="sweep2"):
    table, aud, out = data
    return R.release(stage, source=source, table_dir=table, audit_dir=aud, out_root=out, integrity_args={})


def test_row_text_round_trips_the_exact_pattern():
    import re
    for tier in R.TIERS:
        for stage in R.STAGES:
            kw = {"prereg": "1" * 64, "split": "2" * 64, "commit": "3" * 40}
            if stage == "test":
                kw.update(arms_path="docs/r1/x/ARMS.md", arms="4" * 64)
            m = re.fullmatch(R.row_pattern(tier, stage), R.row_text(tier, stage, **kw))
            assert m and m.group("prereg") == "1" * 64 and m.group("commit") == "3" * 40


def test_author_rows_find_what_the_analysis_guard_finds_on_the_real_plan():
    plan = (REPO / "docs/r1/PLAN.md").read_text()
    gate_sha = _sha((REPO / "r1/c3/gate.py").read_bytes())
    rows = [d for i, d in R.author_rows(plan) if i == analysis_guard.CONFIRM_V31_ID]
    import re
    assert len(rows) == 1 and re.fullmatch(analysis_guard._confirm_v31_pattern(gate_sha), rows[0])
    assert analysis_guard._confirmation_commit(plan, gate_sha) is not None
    assert not any(i in R.ROWS.values() for i, _ in R.author_rows(plan))   # no release row on the checkout yet


def test_traindev_then_test_release_and_the_builder_reads_them(paper, data, world):
    table, aud, out = data
    with pytest.raises(RuntimeError, match="R1-BX-D8-CONFIRM"):              # no PLAN: the D8 check stops first
        _release("traindev", data)
    paper.plan([])
    with pytest.raises(R.ReleaseStop, match="absent"):
        _release("traindev", data)
    paper.plan([("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev"))])
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
    assert rec["counts"]["label_rows"]["test"] > 0 and rec["counts"]["released_label_rows"] == len(lines)
    with pytest.raises(R.ReleaseStop, match="exists"):
        _release("traindev", data)
    # the Track P reader opens the partition, never the raw block
    from r1.c3.train import sft_data
    src = sft_data.LabelBlockSource(part / "label_block.traindev.jsonl", sweep="sweep2")
    got = {r["proposal_id"] for r in src.label_records()}
    assert all(assign[inst[p]]["split"] != "test" for p in got) and len(got) == len(lines)
    assert src.provenance()["release_receipt"]["row_id"] == "R1-S2-LABELS-TRAINDEV-RELEASE"
    with pytest.raises(R.ReleaseStop, match="before R1-S2-LABELS-TEST-RELEASE"):
        sft_data.LabelBlockSource(aud / "label_block.jsonl", sweep="sweep2").label_records()
    with pytest.raises(R.ReleaseStop, match="absent"):
        _release("test", data)
    paper.plan([("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev")),
                ("R1-S2-LABELS-TEST-RELEASE", paper.row("T0", "test"))])
    R.open_partition(part)                                     # a later PLAN commit keeps the receipt valid
    paper.plan([("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev", commit=paper.code[:39] + "0"))])
    with pytest.raises(R.ReleaseStop):                          # the row it was released under is gone
        R.open_partition(part)


def test_test_release_and_builder_end_to_end(paper, data, world):
    table, aud, out = data
    rows = [("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev")),
            ("R1-S2-LABELS-TEST-RELEASE", paper.row("T0", "test"))]
    paper.plan(rows)
    with pytest.raises(R.ReleaseStop, match="no release receipt"):
        _release("test", data)                                                # traindev first
    _release("traindev", data)
    rec = _release("test", data)
    assert rec["arms_frozen_sha256"] == paper.arms_sha and rec["counts"]["evaluation_rows"] == len(world[0][0].evaluations)
    src = R.builder_source(out, "sweep2", table)
    got = B.build([src, world[0][1]], world[1], world[2], t0_nodes=B.SEVEN_T0)
    want = B.build(world[0], world[1], world[2], t0_nodes=B.SEVEN_T0)
    assert json.dumps(got, sort_keys=True) == json.dumps(want, sort_keys=True)
    # a tampered partition, a removed row, a changed arms record: readers stop
    (out / "sweep2" / "test" / "evaluation_block.all.jsonl").write_text("{}\n")
    with pytest.raises(R.ReleaseStop, match="differs from its receipt"):
        R.open_partition(out / "sweep2" / "test")
    paper.plan(rows[:1])
    R.open_partition(out / "sweep2" / "traindev")
    with pytest.raises(R.ReleaseStop, match="absent"):
        R.release_row("T0", "test")
    paper.plan(rows)
    paper.write(ARMS, "changed\n"); paper.commit("arms changed")
    with pytest.raises(R.ReleaseStop, match="arms-frozen record"):
        R.release_row("T0", "test")


@pytest.mark.parametrize("case,match", [
    ("wrong_text", "exact release text"),
    ("duplicate", "not unique"),
    ("not_frozen", "not frozen"),
    ("builder", "gate-input builder"),
    ("split", "another split file"),
    ("prereg_sha", "another preregistration"),
    ("release_bytes", "other r1/c3/release.py bytes"),
])
def test_release_row_refusals(paper, data, case, match):
    row = paper.row("T0", "traindev")
    rows = [("R1-S2-LABELS-TRAINDEV-RELEASE", row)]
    if case == "wrong_text":
        rows = [(rows[0][0], row.replace("No test label", "No label"))]
    elif case == "duplicate":
        rows = rows * 2
    elif case == "not_frozen":
        paper.write(R.PREREG_PATH, paper.prereg(frozen="false")); paper.commit("unfreeze")
    elif case == "builder":
        paper.write(R.PREREG_PATH, paper.prereg(builder="0" * 64)); paper.commit("other builder")
    elif case == "split":
        rows = [(rows[0][0], paper.row("T0", "traindev", split="5" * 64))]
    elif case == "prereg_sha":
        rows = [(rows[0][0], paper.row("T0", "traindev", prereg="6" * 64))]
    elif case == "release_bytes":
        paper.write(R.RELEASE_PATH, (paper.root / R.RELEASE_PATH).read_text() + "# changed\n")
        paper.commit("release changed after the cited commit")
    paper.plan(rows)
    with pytest.raises(R.ReleaseStop, match=match):
        _release("traindev", data)
    assert not (data[2] / "sweep2").exists()


def test_integrity_check_absent_or_failing_writes_nothing(paper, data, monkeypatch):
    paper.plan([("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev"))])
    monkeypatch.setattr(R, "INTEGRITY_CHECKS", {})
    with pytest.raises(R.ReleaseStop, match="no reviewed integrity check"):
        _release("traindev", data)

    def boom(*a, **k):
        raise ValueError("secret value 0.123")
    monkeypatch.setattr(R, "INTEGRITY_CHECKS", {"sweep2": boom})
    with pytest.raises(R.ReleaseStop) as exc:
        _release("traindev", data)
    assert "ValueError" in str(exc.value) and "0.123" not in str(exc.value)   # pass/fail only, never a value
    assert not (data[2] / "sweep2").exists()


def test_locks_on_the_existing_readers(paper, data):
    table, aud, _ = data
    opened = []

    def hook(event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            opened.append(os.fsdecode(args[0]))
    sys.addaudithook(hook)
    paper.plan([])
    for name in ("label_block.jsonl", "evaluation_block.jsonl", "runs.jsonl"):
        with pytest.raises(R.ReleaseStop, match="PRE-STAGE A"):
            R.guard_raw_label_path(aud / name)
    R.guard_raw_label_path(aud / "audits.jsonl")                              # pilot tables keep their path
    with R.integrity_context():
        R.guard_raw_label_path(aud / "evaluation_block.jsonl")                # the release step's carve-out
    opened.clear()
    with pytest.raises(R.ReleaseStop):
        audit.verify_evidence_completion(table, aud / "label_block.jsonl", paper.root, table, table)
    assert not any(Path(p).name in R.RAW_NAMES or Path(p).name == "evidence_completion.json" for p in opened)
    from r1.c3 import ni_masking, offline_eval
    with pytest.raises(R.ReleaseStop):
        offline_eval.assemble(table, aud / "label_block.jsonl")
    with pytest.raises(R.ReleaseStop):
        ni_masking.load_audits(table, aud / "label_block.jsonl")
    paper.plan([("R1-S2-LABELS-TRAINDEV-RELEASE", paper.row("T0", "traindev")),
                ("R1-S2-LABELS-TEST-RELEASE", paper.row("T0", "test"))])
    R.guard_raw_label_path(aud / "evaluation_block.jsonl")                    # after the test release row
    assert R.test_released("T0") and not R.test_released("T1")


def test_t1_rows_and_sources_without_an_integrity_check(paper, data):
    paper.plan([("R1-T1-LABELS-UNSEAL", paper.row("T1", "traindev"))])
    assert R.release_row("T1", "traindev")["row_id"] == "R1-T1-LABELS-UNSEAL"
    with pytest.raises(R.ReleaseStop, match="no reviewed integrity check for g5"):
        _release("traindev", data, source="g5")
    with pytest.raises(R.ReleaseStop, match="absent"):
        R.release_row("T0", "traindev")
