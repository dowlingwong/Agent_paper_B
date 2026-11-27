"""Real-loop RL skeleton (paperc.realloop): reward attribution, worker layout, budgets, environment, trainer.

CPU only, no worker and no node: a fake runner stands in for the B11 real-loop runner.
"""
from __future__ import annotations

import os
import socket

import numpy as np
import pytest

from paperc.realloop import budget as B
from paperc.realloop import env as E
from paperc.realloop import layout as L
from paperc.realloop import reward as R
from paperc.realloop import train as T

H = R.HostEvidence
INF = "infrastructure_failure"


# ---------------------------------------------------------------------------------------------- reward

@pytest.mark.parametrize("run, policy, control, want", [
    (R.RunRecord("ok", value=1.0), "host_evidence", None, "ok"),
    (R.RunRecord("divergent", "timeout"), "host_evidence", None, "proposal_failure"),
    (R.RunRecord("divergent", "timeout_repeated"), "host_evidence", None, "proposal_failure"),
    # a preemption that surfaces as a measured timeout truncates
    (R.RunRecord("divergent", "timeout", host=H(preempted_by_priority=True)), "host_evidence", None,
     "truncate_host"),
    # worker-producible infrastructure on edited code is not neutral
    (R.RunRecord(INF, "infrastructure_log_pattern"), "host_evidence", None, "proposal_failure"),
    (R.RunRecord(INF, "killed"), "host_evidence", None, "proposal_failure"),            # an OOM kill included
    (R.RunRecord(INF, "no_exit_status"), "host_evidence", None, "proposal_failure"),
    # application-triggerable Xids are not host evidence; hardware Xids are
    (R.RunRecord(INF, "infrastructure_log_pattern", host=H(xid=13)), "host_evidence", None, "proposal_failure"),
    (R.RunRecord(INF, "infrastructure_log_pattern", host=H(xid=79)), "host_evidence", None, "truncate_host"),
    (R.RunRecord(INF, "killed", host=H(preempted_by_priority=True)), "host_evidence", None, "truncate_host"),
    (R.RunRecord(INF, "killed", host=H(node_drain=True)), "host_evidence", None, "truncate_host"),
    (R.RunRecord(INF, "infrastructure_log_pattern", host=H(disk_full_unwritable_fs=True)), "host_evidence", None,
     "truncate_host"),
    (R.RunRecord(INF, "launch_error"), "host_evidence", None, "truncate_infrastructure"),
    (R.RunRecord(INF, "infrastructure_log_pattern", trusted_code=True), "host_evidence", None,
     "truncate_infrastructure"),
    (R.RunRecord(INF, "timeout"), "host_evidence", None, "stop"),
    (R.RunRecord(INF, "timeout", host=H(node_drain=True)), "host_evidence", None, "stop"),
    # RL-INFRA B: the control rerun of the trusted start configuration decides
    (R.RunRecord(INF, "infrastructure_log_pattern"), "control_rerun",
     R.RunRecord(INF, "infrastructure_log_pattern", trusted_code=True), "truncate_infrastructure"),
    (R.RunRecord(INF, "infrastructure_log_pattern"), "control_rerun",
     R.RunRecord("ok", value=0.5, trusted_code=True), "proposal_failure"),
])
def test_attribution(run, policy, control, want):
    assert R.attribute(run, policy=policy, control=control) == want


def test_attribution_refusals():
    run = R.RunRecord(INF, "infrastructure_log_pattern")
    with pytest.raises(R.RewardError, match="author row"):
        R.attribute(run, policy="neutral")
    with pytest.raises(R.RewardError, match="control rerun"):
        R.attribute(run, policy="control_rerun")
    with pytest.raises(R.RewardError, match="trusted start configuration"):
        R.attribute(run, policy="control_rerun", control=R.RunRecord("ok", value=0.1))   # an incumbent is not trusted
    with pytest.raises(R.RewardError, match="unclassified"):
        R.attribute(R.RunRecord(INF, "mystery"), policy="host_evidence")
    with pytest.raises(R.RewardError, match="value"):
        R.RunRecord("ok")
    with pytest.raises(R.RewardError, match="value"):
        R.RunRecord("divergent", "timeout", value=1.0)


def test_the_first_attempt_decides_and_every_attempt_is_charged():
    rerolled = R.RunRecord("ok", value=5.0, prior_attempts=(R.RunRecord(INF, "infrastructure_log_pattern"),
                                                             R.RunRecord(INF, "killed")))
    att, runs, first = R.attribute_attempts(rerolled, policy="host_evidence")
    assert (att, runs, first.reason) == ("proposal_failure", 3, "infrastructure_log_pattern")
    att, runs, first = R.attribute_attempts(R.RunRecord("ok", value=1.0, runs_consumed=2), policy="host_evidence")
    assert (att, runs, first.value) == ("ok", 2, 1.0)
    # an attempt after an ok is a STOP (a runner may not reroll a success)
    after_ok = R.RunRecord("ok", value=-5.0, prior_attempts=(R.RunRecord("ok", value=10.0),))
    assert R.attribute_attempts(after_ok, policy="host_evidence")[0] == "stop"
    # the parent's example record decides over host evidence; a launch error and a provisional timeout keep priority
    hosted = R.RunRecord(INF, "killed", host=H(preempted_by_priority=True))
    att, _, first = R.attribute_attempts(hosted, policy="host_evidence", budget_over=True)
    assert att == "proposal_failure" and first.reason == "budget_exceeded" and not first.host.any()
    assert R.attribute_attempts(R.RunRecord(INF, "launch_error"), policy="host_evidence",
                                budget_over=True)[0] == "truncate_infrastructure"
    assert R.attribute_attempts(R.RunRecord(INF, "timeout"), policy="host_evidence", budget_over=True)[0] == "stop"


def test_reward_spec_and_truncation_imbalance():
    spec = R.RewardSpec(g=0.1, sigma_node=2.0)
    assert spec.step("proposal_failure", 3) == pytest.approx(-0.3)
    assert spec.terminal(3.0, 1.0) == pytest.approx(1.0)
    with pytest.raises(R.RewardError):
        spec.step("truncate_host", 1)
    assert R.truncation_check({"A": (1, 20), "B": (2, 20)}, 0.05)["spread"] == pytest.approx(0.05)   # equal passes
    with pytest.raises(R.RewardError, match="STOP"):
        R.truncation_check({"A": (0, 20), "B": (2, 20)}, 0.05)


# ---------------------------------------------------------------------------------------------- layout

ROLES = {"train.py": "code", "parent/run_fixed_budget.py": "frozen", "train/x.npy": "train_inputs",
         "train/y.npy": "train_labels", "val/x.npy": "val_inputs", "val/y.npy": "val_labels",
         "test/x.npy": "test_inputs", "test/y.npy": "test_labels"}


def _kit(tmp_path):
    kit = tmp_path / "kit"
    for rel in ROLES:
        (kit / rel).parent.mkdir(parents=True, exist_ok=True)
        (kit / rel).write_bytes(f"content of {rel}".encode())
    return kit, L.manifest(kit, ROLES)


def _build_root(tmp_path, kit, plan, name="root"):
    root = tmp_path / name
    root.mkdir()
    for f in plan:
        (root / f.rel).parent.mkdir(parents=True, exist_ok=True)
        (root / f.rel).write_bytes((kit / f.rel).read_bytes())
    return root


@pytest.mark.parametrize("layout, roles", [
    ("served", {"code", "frozen"}),
    ("train_only", {"code", "frozen", "train_inputs", "train_labels"}),
    ("train_and_val_inputs", {"code", "frozen", "train_inputs", "train_labels", "val_inputs"}),
])
def test_worker_plans_with_per_split_directories(tmp_path, layout, roles):
    kit, files = _kit(tmp_path)
    plan = L.plan_worker_root(files, layout)
    assert {f.role for f in plan} == roles
    root = _build_root(tmp_path, kit, plan)
    (root / "train.py").write_bytes(b"edited by the proposal")          # edited code passes the scan
    (root / "helpers.py").write_bytes(b"a file the edit added")         # next to planned code
    assert L.check_worker_root(root, files, layout)["files"] == len(plan)


def _moved(tmp_path, p, tag):
    os.replace(p, tmp_path / f"moved_{tag}")                          # moved out of the root, never deleted


def test_worker_root_scan_refusals(tmp_path):
    kit, files = _kit(tmp_path)
    plan = L.plan_worker_root(files, "train_only")
    root = _build_root(tmp_path, kit, plan)
    hidden = root / "train" / "cache.bin"                               # a renamed copy of the test labels
    hidden.write_bytes((kit / "test/y.npy").read_bytes())
    with pytest.raises(L.LayoutError, match="bytes of parent-only test/y.npy"):
        L.check_worker_root(root, files, "train_only")
    _moved(tmp_path, hidden, "a")
    (root / "train.py").write_bytes((kit / "val/y.npy").read_bytes())   # label bytes inside a code file
    with pytest.raises(L.LayoutError, match="bytes of parent-only val/y.npy"):
        L.check_worker_root(root, files, "train_only")
    (root / "train.py").write_bytes(b"code")
    (root / "val").mkdir()
    (root / "val" / "y.npy").write_bytes(b"other bytes")                # at a parent-only path
    with pytest.raises(L.LayoutError, match="path of a parent-only file"):
        L.check_worker_root(root, files, "train_only")
    _moved(tmp_path, root / "val" / "y.npy", "b")
    (root / "val" / "y.npy").mkdir()                                    # a directory at a parent-only path
    with pytest.raises(L.LayoutError, match="directory at the path"):
        L.check_worker_root(root, files, "train_only")
    _moved(tmp_path, root / "val", "c")
    (root / "train" / "extra.npy").write_bytes(b"x")                    # not planned, not in a code directory
    with pytest.raises(L.LayoutError, match="not in the worker plan"):
        L.check_worker_root(root, files, "train_only")
    _moved(tmp_path, root / "train" / "extra.npy", "d")
    (root / "train" / "x.npy").write_bytes(b"changed data")
    with pytest.raises(L.LayoutError, match="differs from the planned file"):
        L.check_worker_root(root, files, "train_only")
    (root / "train" / "x.npy").write_bytes((kit / "train/x.npy").read_bytes())
    _moved(tmp_path, root / "train" / "y.npy", "e")
    with pytest.raises(L.LayoutError, match="missing"):
        L.check_worker_root(root, files, "train_only")
    os.replace(tmp_path / "moved_e", root / "train" / "y.npy")
    assert L.check_worker_root(root, files, "train_only")["files"] == 4
    with pytest.raises(L.LayoutError, match="RL-LAYOUT"):
        L.plan_worker_root(files, "status_quo")
    with pytest.raises(L.LayoutError, match="shared_dev_shm"):
        L.plan_worker_root(files, "served", shared_dev_shm=True)
    L.plan_worker_root(files, "served", shared_dev_shm=True, shm_waiver="R1-EXAMPLE-WAIVER")


@pytest.mark.parametrize("make", ["symlink", "fifo", "socket"])
def test_special_files_are_refused_without_opening_them(tmp_path, make):
    kit, files = _kit(tmp_path)
    root = _build_root(tmp_path, kit, L.plan_worker_root(files, "served"))
    p = root / "special"
    if make == "symlink":
        os.symlink(kit / "test/y.npy", p)
    elif make == "fifo":
        os.mkfifo(p)                                                    # opening it would block
    else:
        s = socket.socket(socket.AF_UNIX)
        s.bind(str(p))
        s.close()
    with pytest.raises(L.LayoutError, match="not a regular file or directory"):
        L.check_worker_root(root, files, "served")


def test_empty_files_do_not_clash_and_identical_bytes_are_refused_at_planning(tmp_path):
    kit, _ = _kit(tmp_path)
    (kit / "pkg").mkdir()
    (kit / "pkg" / "__init__.py").write_bytes(b"")
    (kit / "test" / "empty.npy").write_bytes(b"")
    files = L.manifest(kit, {**ROLES, "pkg/__init__.py": "code", "test/empty.npy": "test_labels"})
    L.plan_worker_root(files, "served")
    (kit / "train/y.npy").write_bytes((kit / "test/y.npy").read_bytes())
    with pytest.raises(L.LayoutError, match="parent-only"):
        L.plan_worker_root(L.manifest(kit, ROLES), "train_only")


# ---------------------------------------------------------------------------------------------- budgets

def test_example_server_serves_contents_in_a_per_epoch_order_and_refuses_beyond_the_limit():
    rows = [f"row{i}" for i in range(10)]
    srv = B.ExampleServer(rows, epochs=2, seed=0)
    first, second = srv.serve(10), srv.serve(10)
    assert sorted(first) == rows and sorted(second) == rows and first != rows and first != second
    with pytest.raises(B.BudgetExceeded):
        srv.serve(1)
    rec = srv.record()
    assert rec == {"limit": 20, "served": 20, "refused_requests": 1}
    assert B.classify_run("ok", "", rec) == ("divergent", "budget_exceeded")
    assert B.classify_run(INF, "killed", rec) == ("divergent", "budget_exceeded")      # deliberate
    assert B.classify_run(INF, "launch_error", rec) == (INF, "launch_error")
    assert B.classify_run(INF, "timeout", rec) == (INF, "timeout")                      # the STOP keeps priority
    assert B.classify_run("ok", "", {"limit": 20, "served": 20, "refused_requests": 0}) == ("ok", "")


def test_campaign_budget():
    cb = B.CampaignBudget(W=2, N=3)
    cb.charge_call()
    cb.charge_runs(2)
    assert cb.end_reason() == "W" and not cb.can_run(1)
    with pytest.raises(B.BudgetExceeded):
        cb.charge_runs(1)
    cb2 = B.CampaignBudget(W=5, N=1)
    cb2.charge_call()
    assert cb2.end_reason() == "llm_cap"
    with pytest.raises(ValueError):
        B.CampaignBudget(W=0, N=1)
    with pytest.raises(ValueError):
        B.CampaignBudget(W=1, N=0)


# ---------------------------------------------------------------------------------------------- environment

class FakeRunner:
    """Proposals with a true increment d ~ N(mu, 1) (sigma units); an ok run measures incumbent + d + noise and asks
    the parent for its training rows. Modes: "honest"; "log_pattern" (every edited run prints an infrastructure
    pattern); "overspend" (asks for one row too many and claims a high metric); "host_loss" (a priority preemption on
    every run); "reroll" (hides an infrastructure attempt before an ok); "stop" (a provisional timeout);
    "expensive" (every run consumes 2); "not_run" (every proposal is refused for scope)."""

    def __init__(self, seed=0, mu=0.0, mode="honest", noise=0.0, repeat_hash=False):
        self.rng = np.random.default_rng(seed)
        self.mu, self.mode, self.noise, self.repeat_hash = mu, mode, noise, repeat_hash
        self.true = {None: 0.0, "start": 0.0}
        self.k = 0
        self.runs = 0

    def start_hash(self):
        return "start"

    def training_rows(self):
        return list(range(8))

    def propose(self):
        self.k += 1
        d = float(self.rng.normal(self.mu, 1.0))
        h = "same" if self.repeat_hash else ("start" if self.mode == "revert" else f"p{self.k}")
        self.true[h] = d
        status = "not_run_scope" if self.mode == "not_run" else "ok"
        max_runs = 2 if self.mode in ("expensive", "reroll") else 1
        return E.Proposal(h, forecast_mean=d, status=status, max_runs=max_runs)

    def run(self, proposal, server):
        self.runs += 1
        if self.mode == "overspend":
            server.serve(server.limit)
            try:
                server.serve(1)
            except B.BudgetExceeded:
                pass
            return R.RunRecord("ok", value=10.0)
        if self.mode == "log_pattern":
            return R.RunRecord(INF, "infrastructure_log_pattern")
        if self.mode == "host_loss" or (self.mode == "late_host_loss" and self.runs > 1):
            return R.RunRecord(INF, "killed", host=R.HostEvidence(preempted_by_priority=True))
        if self.mode == "hosted_overspend":
            try:
                server.serve(server.limit + 1)
            except B.BudgetExceeded:
                pass
            return R.RunRecord(INF, "killed", host=R.HostEvidence(preempted_by_priority=True))
        if self.mode == "stop":
            return R.RunRecord(INF, "timeout")
        server.serve(server.limit)
        value = self.true[proposal.hash] + float(self.rng.normal(0, self.noise))
        if self.mode == "reroll":
            return R.RunRecord("ok", value=value, prior_attempts=(R.RunRecord(INF, "infrastructure_log_pattern"),))
        if self.mode == "expensive":
            return R.RunRecord("ok", value=value, runs_consumed=2)
        return R.RunRecord("ok", value=value)

    def control_rerun(self):
        return R.RunRecord("ok", value=0.0, trusted_code=True)

    def audit(self, incumbent):
        return self.true[incumbent], 0.0


SPLIT = {"n__s1": "train", "n__s2": "train", "n__s3": "dev", "n__s4": "test"}
SPEC = R.RewardSpec(g=0.2, sigma_node=1.0)


def _env(runner, instance="n__s1", policy="host_evidence", mode="train", W=4, N=6):
    return E.RealLoopEnv(runner, instance=instance, split_of=SPLIT, W=W, N=N, reward=SPEC, infra_policy=policy,
                         epochs=1, mode=mode)


def _play(env, e1="execute", e2="keep"):
    obs, phase = env.reset()
    done, total, taken = obs is None, 0.0, []
    while not done:
        obs, phase, r, done, t = env.step(e1 if phase == "E1" else e2)
        total += r
        taken.append(t)
    return env.episode, total, taken


def test_training_split_only():
    for inst in ("n__s3", "n__s4"):
        with pytest.raises(E.EnvStop, match="training split"):
            _env(FakeRunner(), instance=inst)
    _env(FakeRunner(), instance="n__s4", mode="eval")
    with pytest.raises(R.RewardError, match="not allowed"):
        _env(FakeRunner(), policy="neutral")


def test_honest_episode_terminates_with_the_audited_increment_in_the_returns():
    runner = FakeRunner(seed=1, mu=1.0)
    env = _env(runner)
    ep, total, _ = _play(env)
    assert ep.end == "terminated" and ep.end_reason == "W" and ep.attributions == {"ok": 4}
    assert total == pytest.approx(ep.ret)
    assert total == pytest.approx(-0.2 * 4 + runner.true[env.incumbent])


def test_worker_log_patterns_and_hidden_rerolls_are_charged():
    ep, total, _ = _play(_env(FakeRunner(mode="log_pattern")))
    assert ep.attributions == {"proposal_failure": 4} and total == pytest.approx(-0.8)
    assert [s.action for s in ep.steps if s.phase == "E2"] == ["discard"] * 4
    assert all(s.forced for s in ep.steps if s.phase == "E2")
    ep_b, _, _ = _play(_env(FakeRunner(mode="log_pattern"), policy="control_rerun"))
    assert ep_b.attributions == {"proposal_failure": 4}
    # a runner that hides an infrastructure attempt before an ok: the first attempt decides, both runs are charged
    ep_r, total_r, _ = _play(_env(FakeRunner(mode="reroll"), W=4))
    assert ep_r.attributions == {"proposal_failure": 2} and total_r == pytest.approx(-0.2 * 4)
    assert not any(s.phase == "E2" and not s.forced for s in ep_r.steps)   # the rerolled ok never reaches a keep


def test_host_failures_truncate_stops_are_recorded_and_overspending_fails():
    ep, total, _ = _play(_env(FakeRunner(mode="host_loss")))
    assert ep.end == "truncated" and ep.end_reason == "host" and total == 0.0 and ep.ret == 0.0
    env = _env(FakeRunner(mode="stop"))
    with pytest.raises(E.EnvStop, match="protocol STOP"):
        _play(env)
    assert env.episode.end == "truncated" and env.episode.end_reason == "protocol_stop"
    ep2, total2, _ = _play(_env(FakeRunner(mode="overspend")))
    assert ep2.attributions == {"proposal_failure": 4} and total2 == pytest.approx(-0.8)
    assert all(s.forced for s in ep2.steps if s.phase == "E2")         # the claimed metric never reaches a keep


def test_run_costs_above_one_the_controller_refusal_and_an_undeclared_cost():
    runner = FakeRunner(seed=3, mode="expensive")
    env = _env(runner, W=3, N=10)
    ep, total, taken = _play(env)
    assert runner.runs == 1 and env.budget.runs_used == 2                # later executes do not fit
    assert ep.forced.get("over_budget", 0) >= 1 and "skip" not in taken   # the policy is never asked there
    assert ep.end == "terminated" and ep.end_reason == "llm_cap"
    assert total == pytest.approx(-0.2 * 2 + runner.true[env.incumbent])

    class Undeclared(FakeRunner):
        def propose(self):
            p = super().propose()
            return E.Proposal(p.hash, p.forecast_mean, p.status, max_runs=1)
    env2 = _env(Undeclared(mode="expensive"), W=4)
    with pytest.raises(E.EnvStop, match="more than its declared"):
        _play(env2)
    assert env2.episode.end_reason == "protocol_stop"


def test_not_run_proposals_and_duplicates_are_rule_forced():
    env = _env(FakeRunner(mode="not_run"), W=4, N=3)
    obs, phase = env.reset()
    assert obs is None and env.episode.end == "terminated" and env.episode.end_reason == "llm_cap"
    assert env.episode.forced == {"not_run_scope": 3}
    runner = FakeRunner(seed=4, repeat_hash=True)
    env2 = _env(runner, W=4, N=4)
    ep, _, _ = _play(env2)
    assert runner.runs == 1 and ep.forced == {"not_run_duplicate": 3}   # an evaluated code state is not rerun


def test_revert_to_start_unknown_status_and_end_to_end_budget_over_host_evidence():
    runner = FakeRunner(mode="revert")
    env = _env(runner, W=4, N=3)
    obs, _ = env.reset()
    assert obs is None and runner.runs == 0 and env.episode.forced == {"not_run_duplicate": 3}

    class Odd(FakeRunner):
        def propose(self):
            return E.Proposal("x", status="mystery")
    env2 = _env(Odd())
    with pytest.raises(E.EnvStop, match="unknown proposal status"):
        env2.reset()
    assert env2.episode.end_reason == "protocol_stop"
    ep, total, _ = _play(_env(FakeRunner(mode="hosted_overspend")))
    assert ep.end == "terminated" and ep.attributions == {"proposal_failure": 4} and total == pytest.approx(-0.8)


def test_a_truncated_episode_has_return_zero_even_after_charged_steps():
    ep, _, _ = _play(_env(FakeRunner(seed=5, mode="late_host_loss")))
    assert ep.end == "truncated" and ep.end_reason == "host"
    assert sum(s.reward for s in ep.steps) < 0 and ep.ret == 0.0


def test_a_launch_error_truncates_as_infrastructure():
    class Launch(FakeRunner):
        def run(self, proposal, server):
            return R.RunRecord(INF, "launch_error")
    ep, _, _ = _play(_env(Launch()))
    assert ep.end == "truncated" and ep.end_reason == "infrastructure"


def test_the_policy_cannot_run_beyond_W():
    env = _env(FakeRunner(seed=2), W=2, N=10)
    ep, _, _ = _play(env)
    assert env.budget.runs_used == 2 and ep.end_reason == "W"
    env2 = _env(FakeRunner(seed=2), W=10, N=3)
    ep2, _, _ = _play(env2, e1="skip")
    assert env2.budget.runs_used == 0 and ep2.end_reason == "llm_cap"


# ---------------------------------------------------------------------------------------------- trainer

def test_trainer_refuses_non_training_instances():
    with pytest.raises(E.EnvStop, match="non-training"):
        T.reinforce(lambda inst, k: _env(FakeRunner(seed=k), instance=inst), ["n__s1", "n__s4"], SPLIT,
                    iterations=1, batch=2, lr=0.1)


def test_trainer_learns_to_skip_and_discard_when_running_never_pays():
    """Every proposal's true increment is about -1 sigma: executing costs g and keeping loses."""
    def make(inst, k):
        return _env(FakeRunner(seed=1000 + k, mu=-1.0), instance=inst, W=4, N=6)
    out = T.reinforce(make, ["n__s1", "n__s2"], SPLIT, iterations=80, batch=8, lr=0.5, seed=0)
    first = np.mean([r["mean_return"] for r in out["log"][:5]])
    last = np.mean([r["mean_return"] for r in out["log"][-5:]])
    assert last > first + 0.3
    p = out["policy"]
    assert p.probs(np.array([1.0, 0.5, 0.5, -1.0, -1.0, 0.0]), "E2")[1] > 0.6      # discard a measured loss
    assert p.probs(np.array([0.0, 0.5, 0.5, -1.0, 0.0, 0.0]), "E1")[1] > 0.55      # skip a predicted loss


def test_trainer_enforces_the_truncation_level():
    with pytest.raises(E.EnvStop, match="more than half"):
        T.reinforce(lambda inst, k: _env(FakeRunner(mode="host_loss"), instance=inst), ["n__s1"], SPLIT,
                    iterations=1, batch=2, lr=0.1)

    def sometimes(inst, k):                    # one host loss in every eight draws: 12.5 % > 5 %
        return _env(FakeRunner(seed=k, mode="host_loss" if k % 8 == 0 else "honest"), instance=inst)
    with pytest.raises(E.EnvStop, match="cumulative truncation rate"):
        T.reinforce(sometimes, ["n__s1"], SPLIT, iterations=10, batch=4, lr=0.1)
    out = T.reinforce(sometimes, ["n__s1"], SPLIT, iterations=3, batch=4, lr=0.1, trunc_level=0.2)
    assert out["log"][-1]["cumulative_truncation_rate"] > 0
