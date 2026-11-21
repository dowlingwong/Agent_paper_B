"""Real-loop RL skeleton (paperc.realloop): reward attribution, worker layout, budgets, environment, trainer.

CPU only, no worker and no node: a fake runner stands in for the B11 real-loop runner.
"""
from __future__ import annotations

import os

import numpy as np
import pytest

from paperc.realloop import budget as B
from paperc.realloop import env as E
from paperc.realloop import layout as L
from paperc.realloop import reward as R
from paperc.realloop import train as T

H = R.HostEvidence


# ---------------------------------------------------------------------------------------------- reward

@pytest.mark.parametrize("run, policy, control, want", [
    (R.RunRecord("ok", value=1.0), "host_evidence", None, "ok"),
    (R.RunRecord("divergent", "timeout"), "host_evidence", None, "proposal_failure"),
    # a worker-printed infrastructure pattern on an edited state is not neutral
    (R.RunRecord("infrastructure_failure", "infrastructure_log_pattern"), "host_evidence", None, "proposal_failure"),
    (R.RunRecord("infrastructure_failure", "killed"), "host_evidence", None, "proposal_failure"),
    (R.RunRecord("infrastructure_failure", "no_exit_status"), "host_evidence", None, "proposal_failure"),
    # evidence the worker cannot produce
    (R.RunRecord("infrastructure_failure", "infrastructure_log_pattern", host=H(gpu_xid=True)), "host_evidence",
     None, "truncate"),
    (R.RunRecord("infrastructure_failure", "killed", host=H(scheduler_eviction=True)), "host_evidence", None,
     "truncate"),
    (R.RunRecord("infrastructure_failure", "launch_error"), "host_evidence", None, "truncate"),
    (R.RunRecord("infrastructure_failure", "infrastructure_log_pattern", edited=False), "host_evidence", None,
     "truncate"),
    # a provisional timeout has no place in RL
    (R.RunRecord("infrastructure_failure", "timeout"), "host_evidence", None, "stop"),
    # RL-INFRA B: the control rerun of the incumbent decides
    (R.RunRecord("infrastructure_failure", "infrastructure_log_pattern"), "control_rerun",
     R.RunRecord("infrastructure_failure", "infrastructure_log_pattern", edited=False), "truncate"),
    (R.RunRecord("infrastructure_failure", "infrastructure_log_pattern"), "control_rerun",
     R.RunRecord("ok", value=0.5, edited=False), "proposal_failure"),
])
def test_attribution(run, policy, control, want):
    assert R.attribute(run, policy=policy, control=control) == want


def test_attribution_refusals():
    run = R.RunRecord("infrastructure_failure", "infrastructure_log_pattern")
    with pytest.raises(R.RewardError, match="author row"):
        R.attribute(run, policy="neutral")
    with pytest.raises(R.RewardError, match="control rerun"):
        R.attribute(run, policy="control_rerun")
    with pytest.raises(R.RewardError, match="unedited"):
        R.attribute(run, policy="control_rerun", control=R.RunRecord("ok", value=0.1, edited=True))
    with pytest.raises(R.RewardError, match="unclassified"):
        R.attribute(R.RunRecord("infrastructure_failure", "mystery"), policy="host_evidence")
    with pytest.raises(R.RewardError, match="value"):
        R.attribute(R.RunRecord("ok"), policy="host_evidence")


def test_reward_spec_and_truncation_imbalance():
    spec = R.RewardSpec(g=0.1, sigma_node=2.0)
    assert spec.step("proposal_failure", 1) == pytest.approx(-0.1)     # a failure is charged like any run
    assert spec.terminal(3.0, 1.0) == pytest.approx(1.0)
    with pytest.raises(R.RewardError):
        spec.step("truncate", 1)
    assert R.truncation_check({"A": (1, 20), "B": (2, 20)}, 0.1)["spread"] == pytest.approx(0.05)
    with pytest.raises(R.RewardError, match="STOP"):
        R.truncation_check({"A": (0, 20), "B": (5, 20)}, 0.1)


# ---------------------------------------------------------------------------------------------- layout

ROLES = {"train.py": "code", "parent/run_fixed_budget.py": "frozen", "data/train_x.npy": "train_inputs",
         "data/train_y.npy": "train_labels", "data/val_x.npy": "val_inputs", "data/val_y.npy": "val_labels",
         "data/test_x.npy": "test_inputs", "data/test_y.npy": "test_labels"}


def _kit(tmp_path):
    kit = tmp_path / "kit"
    for rel in ROLES:
        (kit / rel).parent.mkdir(parents=True, exist_ok=True)
        (kit / rel).write_bytes(f"content of {rel}".encode())
    return kit, L.manifest(kit, ROLES)


def _build_root(tmp_path, kit, plan, name="root"):
    root = tmp_path / name
    for f in plan:
        (root / f.rel).parent.mkdir(parents=True, exist_ok=True)
        (root / f.rel).write_bytes((kit / f.rel).read_bytes())
    return root


@pytest.mark.parametrize("layout, n", [("train_and_val_inputs", 5), ("train_only", 4)])
def test_worker_plan_holds_no_label_of_val_or_test(tmp_path, layout, n):
    kit, files = _kit(tmp_path)
    plan = L.plan_worker_root(files, layout)
    roles = {f.role for f in plan}
    assert len(plan) == n and not roles & {"val_labels", "test_inputs", "test_labels"}
    assert ("val_inputs" in roles) == (layout == "train_and_val_inputs")
    root = _build_root(tmp_path, kit, plan)
    assert L.check_worker_root(root, files, layout)["files"] == n


def test_worker_root_scan_refusals(tmp_path):
    kit, files = _kit(tmp_path)
    plan = L.plan_worker_root(files, "train_only")
    root = _build_root(tmp_path, kit, plan)
    hidden = root / "data" / "cache.bin"                       # a renamed copy of the test labels
    hidden.write_bytes((kit / "data/test_y.npy").read_bytes())
    with pytest.raises(L.LayoutError, match="bytes of parent-only data/test_y.npy"):
        L.check_worker_root(root, files, "train_only")
    os.replace(hidden, tmp_path / "moved_out.bin")             # moved out of the root, never deleted
    (root / "data" / "val_y.npy").write_bytes(b"other bytes")  # the name of a parent-only file
    with pytest.raises(L.LayoutError, match="name of a parent-only file"):
        L.check_worker_root(root, files, "train_only")
    os.replace(root / "data" / "val_y.npy", tmp_path / "moved_out2.bin")
    (root / "extra.txt").write_bytes(b"x")
    with pytest.raises(L.LayoutError, match="not in the worker plan"):
        L.check_worker_root(root, files, "train_only")
    os.replace(root / "extra.txt", tmp_path / "moved_out3.txt")
    os.symlink(kit / "data/test_y.npy", root / "link")
    with pytest.raises(L.LayoutError, match="symlink"):
        L.check_worker_root(root, files, "train_only")
    os.replace(root / "link", tmp_path / "moved_link")
    (root / "train.py").write_bytes(b"edited by someone")
    with pytest.raises(L.LayoutError, match="differs from the planned file"):
        L.check_worker_root(root, files, "train_only")
    with pytest.raises(L.LayoutError, match="RL-LAYOUT"):
        L.plan_worker_root(files, "status_quo")


def test_a_worker_file_with_the_bytes_of_a_label_file_is_refused_at_planning(tmp_path):
    kit, _ = _kit(tmp_path)
    (kit / "data/train_y.npy").write_bytes((kit / "data/test_y.npy").read_bytes())
    files = L.manifest(kit, ROLES)
    with pytest.raises(L.LayoutError, match="parent-only"):
        L.plan_worker_root(files, "train_only")


# ---------------------------------------------------------------------------------------------- budgets

def test_example_budget_refuses_beyond_the_limit_and_the_run_becomes_a_proposal_failure():
    eb = B.ExampleBudget(n_examples=10, epochs=2, seed=0)
    first = eb.serve(10)
    assert sorted(first.tolist()) == list(range(10))
    eb.serve(10)
    with pytest.raises(B.BudgetExceeded):
        eb.serve(1)
    rec = eb.record()
    assert rec == {"limit": 20, "served": 20, "refused_requests": 1}
    assert B.classify_run("ok", "", rec) == ("divergent", "budget_exceeded")
    assert B.classify_run("ok", "", {"limit": 20, "served": 20, "refused_requests": 0}) == ("ok", "")


def test_campaign_budget_is_owned_by_the_controller():
    cb = B.CampaignBudget(W=2, N=3)
    cb.charge_call()
    cb.charge_runs(2)
    assert cb.end_reason() == "W" and not cb.can_run(1)
    with pytest.raises(B.BudgetExceeded):
        cb.charge_runs(1)
    cb2 = B.CampaignBudget(W=5, N=1)
    cb2.charge_call()
    assert cb2.end_reason() == "llm_cap"


# ---------------------------------------------------------------------------------------------- environment

class FakeRunner:
    """Proposals with a true increment d ~ N(mu, 1) (sigma units); an ok run measures incumbent + d + noise.
    ``mode``: "honest", "log_pattern" (every edited run prints an infrastructure pattern),
    "overspend" (asks for one example too many), "host_loss" (a scheduler eviction on every run)."""

    def __init__(self, seed=0, mu=0.0, mode="honest", noise=0.0):
        self.rng = np.random.default_rng(seed)
        self.mu, self.mode, self.noise = mu, mode, noise
        self.true = {None: 0.0}
        self.k = 0

    def propose(self):
        self.k += 1
        d = float(self.rng.normal(self.mu, 1.0))
        h = f"p{self.k}"
        self.true[h] = d
        return E.Proposal(h, forecast_mean=d)

    def run(self, proposal, budget):
        if self.mode == "overspend":
            budget.serve(budget.limit)
            try:
                budget.serve(1)
            except B.BudgetExceeded:
                pass
            return R.RunRecord("ok", value=10.0)                   # the worker claims a great metric anyway
        if self.mode == "log_pattern":
            return R.RunRecord("infrastructure_failure", "infrastructure_log_pattern")
        if self.mode == "host_loss":
            return R.RunRecord("infrastructure_failure", "killed", host=R.HostEvidence(scheduler_eviction=True))
        budget.serve(budget.limit)
        return R.RunRecord("ok", value=self.true[proposal.hash] + float(self.rng.normal(0, self.noise)))

    def control_rerun(self):
        return R.RunRecord("ok", value=0.0, edited=False)

    def audit(self, incumbent):
        return self.true[incumbent], 0.0


SPLIT = {"n__s1": "train", "n__s2": "train", "n__s3": "dev", "n__s4": "test"}
SPEC = R.RewardSpec(g=0.2, sigma_node=1.0)


def _env(runner, instance="n__s1", policy="host_evidence", mode="train", W=4, N=6):
    return E.RealLoopEnv(runner, instance=instance, split_of=SPLIT, W=W, N=N, reward=SPEC, infra_policy=policy,
                         example_budget=(8, 1), mode=mode)


def _play(env, e1="execute", e2="keep"):
    obs, phase = env.reset()
    done, total = False, 0.0
    while not done:
        obs, phase, r, done = env.step(e1 if phase == "E1" else e2)
        total += r
    return env.episode, total


def test_training_split_only():
    with pytest.raises(E.EnvStop, match="training split"):
        _env(FakeRunner(), instance="n__s4")
    with pytest.raises(E.EnvStop, match="training split"):
        _env(FakeRunner(), instance="n__s3")
    _env(FakeRunner(), instance="n__s4", mode="eval")             # evaluation may run on test campaigns
    with pytest.raises(R.RewardError, match="not allowed"):
        _env(FakeRunner(), policy="neutral")


def test_honest_episode_terminates_with_the_audited_increment():
    ep, total = _play(_env(FakeRunner(seed=1, mu=1.0)))
    assert ep.end == "terminated" and ep.end_reason == "W" and ep.attributions == {"ok": 4}
    assert total == pytest.approx(ep.ret)
    assert any(s.phase == "E2" for s in ep.steps)


def test_worker_log_patterns_are_charged_and_never_rerun_for_free():
    ep, total = _play(_env(FakeRunner(mode="log_pattern")))
    assert ep.end == "terminated" and ep.attributions == {"proposal_failure": 4}
    assert total == pytest.approx(-0.2 * 4 + 0.0)                   # four charged runs, nothing kept
    # under RL-INFRA B the control rerun of the incumbent succeeds, so the failure is the proposal's
    ep_b, _ = _play(_env(FakeRunner(mode="log_pattern"), policy="control_rerun"))
    assert ep_b.attributions == {"proposal_failure": 4}


def test_host_evidenced_failures_truncate_and_overspending_is_a_proposal_failure():
    ep, total = _play(_env(FakeRunner(mode="host_loss")))
    assert ep.end == "truncated" and ep.end_reason == "infrastructure" and total == 0.0
    ep2, total2 = _play(_env(FakeRunner(mode="overspend")))
    assert ep2.attributions == {"proposal_failure": 4} and total2 == pytest.approx(-0.8)
    assert not any(s.phase == "E2" for s in ep2.steps)              # the claimed metric never reaches a keep


def test_the_policy_cannot_run_beyond_W():
    env = _env(FakeRunner(seed=2), W=2, N=10)
    ep, _ = _play(env)
    assert env.budget.runs_used == 2 and ep.end_reason == "W"
    env2 = _env(FakeRunner(seed=2), W=10, N=3)
    ep2, _ = _play(env2, e1="skip")
    assert env2.budget.runs_used == 0 and ep2.end_reason == "llm_cap"


# ---------------------------------------------------------------------------------------------- trainer

def test_trainer_refuses_non_training_instances():
    with pytest.raises(E.EnvStop, match="non-training"):
        T.reinforce(lambda inst, k: _env(FakeRunner(seed=k), instance=inst), ["n__s1", "n__s4"], SPLIT,
                    iterations=1, batch=2, lr=0.1)


def test_trainer_learns_to_skip_when_running_never_pays():
    """Every proposal's true increment is about -1 sigma: executing costs g and keeping loses; the policy should
    learn to skip (or at least to discard), raising the mean return."""
    def make(inst, k):
        return _env(FakeRunner(seed=1000 + k, mu=-1.0), instance=inst, W=4, N=6)
    out = T.reinforce(make, ["n__s1", "n__s2"], SPLIT, iterations=60, batch=8, lr=0.5, seed=0)
    first = np.mean([r["mean_return"] for r in out["log"][:5]])
    last = np.mean([r["mean_return"] for r in out["log"][-5:]])
    assert last > first + 0.3
    p = out["policy"]
    obs_e2 = np.array([1.0, 0.5, 0.5, -1.0, -1.0, 0.0])
    assert p.probs(obs_e2, "E2")[1] > 0.6                          # discard a measured loss


def test_trainer_drops_truncated_episodes_and_stops_if_all_truncate():
    with pytest.raises(E.EnvStop, match="every episode truncates"):
        T.reinforce(lambda inst, k: _env(FakeRunner(mode="host_loss"), instance=inst), ["n__s1"], SPLIT,
                    iterations=1, batch=2, lr=0.1)
