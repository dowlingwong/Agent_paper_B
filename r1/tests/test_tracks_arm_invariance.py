"""Track S arm-invariance tests (runbook rev. 3 §2 tests 1-4; rev.-4 amendment test 5; mechanical budget check).

The root and its branches run the real harness loop (``run_real_campaign`` / ``resume_campaign``) with the
real ``LangGraphManager`` prompt path (an injected stub LLM that records every prompt and D26 seed and
answers deterministically from them), an A2-U controller, and the in-process synthetic worker on the
digits_mlp surface. ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.c3.features import NodeContext
from r1.harness import import_harness
from r1.tracks import a2u
from r1.tracks.collect import AllSnapshots, decisions_from, read_jsonl
from r1.tracks.synthetic import SURFACE, LogLinearLaw, SyntheticWorker, surface_start_files, synthetic_node

HARNESS = import_harness()

from autoresearch.control_plane.snapshot import ArmOverride, read_snapshot, resume_campaign  # noqa: E402
from autoresearch.control_plane.campaign import run_real_campaign  # noqa: E402
from autoresearch.manager.langgraph_manager import LangGraphManager  # noqa: E402
from autoresearch.memory.event_store import CampaignEventStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402

SIGMA = 0.002
SEED = 39001
W, CAP = 20, 12
FACTORS = (0.5, 0.8, 1.25, 2.0)


class StubLLM:
    """Records (prompt, seed); proposes a multiplicative edit of ALPHA or LEARNING_RATE_INIT from hash(seed, prompt)."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def invoke(self, messages, **kwargs):
        prompt, seed = messages[0].content, kwargs.get("seed")
        self.calls.append((prompt, seed))
        h = int(hashlib.sha256(f"{seed}|{prompt}".encode()).hexdigest()[:8], 16)
        key = ("ALPHA", "LEARNING_RATE_INIT")[h % 2]
        old = re.search(rf"^\s*{key} = (\S+)\s*$", prompt, re.MULTILINE).group(1)
        new = repr(float(old) * FACTORS[(h // 2) % len(FACTORS)])
        body = {"summary": f"{key}-{new}", "rationale": "r", "objective": f"Change {key} from {old} to {new}.",
                "param": key, "old_value": old, "new_value": new}
        return SimpleNamespace(content=json.dumps(body), usage_metadata={}, response_metadata={})


class RecordingWorker(SyntheticWorker):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.calls: list[tuple[int, int, str]] = []

    def run_trial(self, proposal, node_spec, budget_index):
        self.calls.append((int(budget_index), int(self._train_seed), (self.node_root / "train.py").read_text()))
        return super().run_trial(proposal, node_spec, budget_index)


class RecordingA2U(a2u.A2UController):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.views: list = []

    def decide(self, view, mask):
        self.views.append(view)
        return super().decide(view, mask)


def law() -> LogLinearLaw:
    return LogLinearLaw(salt=SEED, theta={"ALPHA": 0.01, "LEARNING_RATE_INIT": 0.01}, sigma_run=SIGMA)


def prior() -> a2u.A2UPrior:
    return a2u.A2UPrior(node=SURFACE, sigma_node=SIGMA,
                        kinds={"local": a2u.KindPrior(mu0=0.0, tau0=0.004, sigma_cmp=SIGMA, tau_w=0.002)})


def ctx() -> NodeContext:
    return NodeContext(node=SURFACE, start_files=surface_start_files(), sigma_node=SIGMA, runs_total=W,
                       memory_mode="append_only_summary")


def controller(**kw) -> RecordingA2U:
    return RecordingA2U(prior(), ctx(), g=0.0006, **kw)


@pytest.fixture(scope="module")
def root(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("root")
    spec = load_registered_node(SURFACE, repo_root=HARNESS)
    node = tmp / "node"
    shutil.copytree(HARNESS / "nodes" / SURFACE, node, ignore=shutil.ignore_patterns("__pycache__"))
    llm, ctl = StubLLM(), controller()
    snaps = AllSnapshots(tmp / "snapshots")
    run_real_campaign(node_spec=spec, campaign_id=f"tracks_fixture_{SURFACE}__s{SEED}", manager_mode="langgraph_manager",
                      memory_mode="append_only_summary", records_path=tmp / "root_trials.jsonl",
                      worker=RecordingWorker(node, law(), train_seed=SEED, split_seed=SEED),
                      proposal_backend=LangGraphManager(llm=llm), snapshot_hook=snaps,
                      event_store=CampaignEventStore(tmp / "root_events.jsonl"),
                      **ctl.campaign_kwargs(W=W, llm_cap=CAP))
    rows = read_jsonl(tmp / "root_trials.jsonl")
    decisions = decisions_from(rows, read_jsonl(tmp / "root_events.jsonl"), snaps.written)
    e1 = [d for d in decisions if d["epoch"] == "E1" and d["eligible"] and d["index"] >= 3]
    assert e1, "the fixture root needs an eligible E1 fork"
    fork = e1[0]
    return SimpleNamespace(tmp=tmp, rows=rows, llm=llm, decisions=decisions, fork=fork,
                           snapshot=read_snapshot(snaps.written[("E1", fork["index"])]), snaps=snaps.written)


def leaf(root, name, arm=None, first_action=None, repetition=101):
    into = root.tmp / f"leaf_{name}"
    if into.exists():
        shutil.rmtree(into)
    snap = root.snapshot
    llm, ctl = StubLLM(), controller()
    worker = RecordingWorker(into, law(), train_seed=int(snap.train_seed))
    res = resume_campaign(snap, into, arm=arm, first_action=first_action, policy=ctl,
                          horizon=snap.budget_total - snap.budget_consumed - 1, worker=worker,
                          manager=LangGraphManager(llm=llm, repetition=repetition), keep_prior=ctl.keep_prior)
    rows = read_jsonl(res.restored.records_path)
    events = read_jsonl(res.restored.events_path)
    return SimpleNamespace(res=res, rows=rows, events=events, llm=llm, ctl=ctl, worker=worker,
                           decisions=[(e["trial_id"], e["payload"]["epoch"], e["payload"]["action"]) for e in events
                                      if e["event_type"] == "control_decision"])


@pytest.fixture(scope="module")
def arms(root):
    return {name: leaf(root, name, ArmOverride(name)) for name in ("skip", "ghost", "ctrl_only")}


def _first_divergence(a, b) -> int:
    """Index (in trial order) of the first trial whose controller decisions differ; len if none."""
    def by_trial(decisions):
        out: dict[str, list] = {}
        for tid, epoch, action in decisions:
            out.setdefault(tid, []).append((epoch, action))
        return [out[t] for t in sorted(out)]
    da, db = by_trial(a.decisions), by_trial(b.decisions)
    for i, (x, y) in enumerate(zip(da, db)):
        if x != y:
            return i
    return min(len(da), len(db))


def test_1_prompts_and_seeds_identical_until_the_controllers_differ(arms):
    skip = arms["skip"]
    compared = 0
    for name in ("ghost", "ctrl_only"):
        other = arms[name]
        d = _first_divergence(skip, other)
        # The prompt of the divergence trial is built before its decision, so it must still agree.
        n = min(d + 1, len(skip.llm.calls), len(other.llm.calls))
        assert skip.llm.calls[:n] == other.llm.calls[:n], name
        compared += n
    assert compared >= 4  # non-vacuous: several post-fork prompts compared
    # Seeds: D26 repetition 101 at the root's campaign id, the same in every arm.
    assert [s for _, s in skip.llm.calls[:3]] == [s for _, s in arms["ghost"].llm.calls[:3]]


def test_2_ghost_record_leaks_no_metric_or_delta(root, arms):
    ghost = arms["ghost"]
    b = root.fork["index"]
    row = [r for r in ghost.rows if r["budget_index"] == b][0]
    assert row["decision"] == "skipped" and row["parsed_metrics"] == {} and row["delta_vs_best"] is None
    assert "keep_rule" not in row["extra"] and "arm_override" not in row["extra"]
    shadow = ghost.res.shadow_record
    metric = shadow.parsed_metrics["val_score"]
    assert f"{metric:.6f}" not in "\n".join(p for p, _ in ghost.llm.calls)  # the summariser never shows it
    # Controller features: no later view holds the shadow's metric or delta, nor its configuration.
    sha = None
    for view in ghost.ctl.views:
        rec = [r for r in view.ledger_prefix if r.budget_index == b]
        if rec:
            assert rec[0].parsed_metrics == {} and rec[0].delta_vs_best is None
        if view.epoch == "E1" and view.proposal is not None and view.budget_index > b:
            fc = ghost.ctl.forecast(view)
            if fc is not None:
                assert shadow.delta_vs_best not in sum(fc["rep"].deltas.values(), [])
    # Novelty: no edit_novelty event for the ghost trial.
    tid = shadow.trial_id
    assert not [e for e in ghost.events if e["event_type"] == "edit_novelty" and e["trial_id"] == tid]


def _projection_of_fork(root) -> str:
    from r1.c3.features import active_projection, apply_edit
    from r1.diagnostics.di_test import configuration
    inc = {k: v.decode() for k, v in root.snapshot.incumbent_files.items()}
    return active_projection(configuration(apply_edit(inc, root.snapshot.proposal.extra["structured_edit"])), SURFACE)


def test_3_seen_sets(root, arms):
    proj = _projection_of_fork(root)
    b = root.fork["index"]
    for name, in_controller in (("ghost", False), ("ctrl_only", True)):
        leaf_ = arms[name]
        later = [v for v in leaf_.ctl.views if v.budget_index > b and v.epoch == "E1"]
        assert later, name
        rep = a2u.replay(later[0], ctx())
        assert (proj in rep.first_eval) is in_controller, name
        # ctrl_only's controller sees the executed (non-kept) record; ghost's sees the skip.
        rec = [r for r in later[0].ledger_prefix if r.budget_index == b][0]
        assert (rec.decision.value != "skipped") is in_controller
        # The harness novelty set never gets it.
        assert not [e for e in leaf_.events if e["event_type"] == "edit_novelty"
                    and e["trial_id"] == leaf_.res.shadow_record.trial_id]
    # Execute arm for contrast: the configuration enters both seen-sets.
    ex = leaf(root, "execute", ArmOverride("execute"))
    later = [v for v in ex.ctl.views if v.budget_index > b and v.epoch == "E1"]
    assert proj in a2u.replay(later[0], ctx()).first_eval


def _signature(rows):
    return [(r["budget_index"], r["decision"], r["proposal_summary"], json.dumps(r["parsed_metrics"], sort_keys=True))
            for r in rows]


def test_4_aa_fork_reproduces_the_root(root):
    b = root.fork["index"]
    arm = ArmOverride("skip", skip_reason=root.fork["skip_reason"]) if root.fork["action"] == "skip" else None
    aa = leaf(root, "aa", arm=arm, first_action=None if arm else "continue", repetition=0)
    new = aa.rows[len(root.snapshot.ledger_prefix):]
    assert _signature(new) == _signature([r for r in root.rows if r["budget_index"] >= b])
    # and the manager saw the root's prompts and seeds after the fork
    root_calls = root.llm.calls[b:]  # one call per trial; trial b's call was made before the snapshot
    assert aa.llm.calls == root_calls[:len(aa.llm.calls)]


def test_5_worker_seeds_and_workspace_identical_across_arms(root, arms):
    b = root.fork["index"]
    incumbent = root.snapshot.incumbent_files["train.py"].decode()
    skip, ghost, ctrl = arms["skip"], arms["ghost"], arms["ctrl_only"]
    # The ghost / ctrl_only run of the fork trial itself started from the incumbent ...
    for a in (ghost, ctrl):
        assert a.worker.calls[0][:2] == (b, SEED) and a.worker.calls[0][2] == incumbent
    # ... and the workspace was restored: the next trial starts from the same files and seed in every arm.
    post = {name: [c for c in a.worker.calls if c[0] > b] for name, a in arms.items()}
    assert post["skip"] and post["skip"][0][2] == incumbent
    for name in ("ghost", "ctrl_only"):
        d = _first_divergence(skip, arms[name])
        n = min(len(post["skip"]), len(post[name]))
        assert n >= 1
        # worker calls agree until the controllers diverge
        same = [x == y for x, y in zip(post["skip"][:n], post[name][:n])]
        assert same[0], name
        trials_before_divergence = d  # decisions at trials b+1 .. b+d agree
        assert all(same[:max(1, min(n, trials_before_divergence))]), name
    # Worker noise is keyed by (campaign seed, trial): identical across arms for the same trial.
    lw = law()
    assert lw.eps(SEED, b + 1) == lw.eps(SEED, b + 1) and lw.eps(SEED, b + 1) != lw.eps(SEED, b + 2)


def test_mechanical_budget_check_skip_vs_ghost_at_W2(tmp_path):
    """At W = 2 the ghost spends the last run: skip and ghost must differ clearly (Delta_B > 0)."""
    # The N0 law (independent values fixed in advance, no information, no feedback) run at a binding W = 2.
    node = synthetic_node("synthetic_N0", {"mechanism": "loglinear", "mu_step": 0.02, "spread": 0.001, "sigma_run": 0.0005})
    spec = load_registered_node(SURFACE, repo_root=HARNESS)
    nd = tmp_path / "node"
    shutil.copytree(HARNESS / "nodes" / SURFACE, nd, ignore=shutil.ignore_patterns("__pycache__"))
    pr = node.prior()
    c = NodeContext(node=SURFACE, start_files=surface_start_files(), sigma_node=pr.sigma_node, runs_total=2,
                    memory_mode="append_only_summary")
    ctl = a2u.A2UController(pr, c, g=0.0)
    snaps = AllSnapshots(tmp_path / "snaps")
    run_real_campaign(node_spec=spec, campaign_id="tracks_fixture_n0__s39002", manager_mode="scripted",
                      memory_mode="append_only_summary", records_path=tmp_path / "root.jsonl",
                      worker=node.worker(nd, 39002), proposal_backend=node.manager(39002, 0), snapshot_hook=snaps,
                      **ctl.campaign_kwargs(W=2, llm_cap=6))
    snap = read_snapshot(snaps.written[("E1", 2)])
    ys = {}
    for arm in ("skip", "ghost"):
        into = tmp_path / arm
        res = resume_campaign(snap, into, arm=ArmOverride(arm), policy=a2u.A2UController(pr, c, g=0.0),
                              horizon=snap.budget_total - snap.budget_consumed - 1, worker=node.worker(into, 39002),
                              manager=node.manager(39002, 101), keep_prior=ctl.keep_prior)
        rows = read_jsonl(res.restored.records_path)
        files = {"train.py": (into / "train.py").read_text()}
        ys[arm] = node.audit(39002, files, [1])[0]
        ys[arm + "_runs"] = sum(1 for r in rows[len(snap.ledger_prefix):] if r["decision"] != "skipped") + \
            (1 if res.shadow_record is not None else 0)
    assert ys["skip_runs"] == ys["ghost_runs"] == 1
    assert ys["skip"] - ys["ghost"] > 0.01  # the freed run bought a ~0.02 increment under skip
