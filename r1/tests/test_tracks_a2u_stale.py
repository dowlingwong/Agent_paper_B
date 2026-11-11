"""R1-TRACKS-A2U-STALE: A2-U on a stale proposal the harness rejected (Track S STOP 3, S0.4 s30000 trial 13).

ENGINEERING_ONLY; AI-assisted (Claude). The harness rejects a structured edit whose ``old`` value no longer
matches the incumbent (``PROPOSAL_PRECONDITION_FAILED``, an invalid trial without a worker run) but still calls
the controller at E2 for that trial; at paper pin ``d10b05b7`` A2-U's ``_e2_detail`` then replayed the stale
edit and raised ``ReplayError``. Three checks:

1. the S0.4 failure shape (HIDDEN_UNITS is 2048, the proposal expects 1024) runs to the end of the campaign;
2. an invalid trial's E2 is "not eligible" without calling the forecast;
3. on valid trials the decisions and the controller log are byte-identical to the code at ``d10b05b7``
   (on the S0.4 committed-root ledgers when present under ``r1/tests/data/tracks_s04_roots/``, and always on
   generated campaigns).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.c3.features import NodeContext, ReplayError, ReplayProposal, ReplayView, _row_edit
from r1.tests.c3_campaign_fixtures import HARNESS, NODE, node_context, run_campaign
from r1.tracks import a2u

REPO = Path(__file__).resolve().parents[2]
BASE_PIN = "d10b05b738fc0e0dba54e0e692c248bedf095482"   # Track S paper pin of S0.4 (manifest provenance)
# The five S0.4 committed-root ledgers (<root_id>/root_trials.jsonl). Default: a copy under the repo; on TASL-2
# the operator may point TRACKS_S04_ROOTS read-only at <run.work>/roots instead.
import os  # noqa: E402
S04_ROOTS = Path(os.environ.get("TRACKS_S04_ROOTS") or REPO / "r1" / "tests" / "data" / "tracks_s04_roots")
S04_SIGMA, S04_W = 0.0066, 40                            # results/r1/tracks/digits_mlp/s04/manifest.json


def _old_a2u():
    """``r1/tracks/a2u.py`` exactly as at the Track S pin, imported under its own name."""
    try:
        src = subprocess.run(["git", "-C", str(REPO), "show", f"{BASE_PIN}:r1/tracks/a2u.py"], check=True,
                             capture_output=True, text=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:  # the pin must be in the clone
        raise AssertionError(f"paper pin {BASE_PIN} not available: {exc}") from exc
    path = Path(sys.modules[__name__].__file__).parent / "_a2u_at_d10b05b7.py"
    spec = importlib.util.spec_from_loader("a2u_at_d10b05b7", loader=None)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod   # dataclasses resolve the module by name
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


class ScriptBackend:
    """Proposes the scripted edits in order; ``old=None`` reads the current value (a fresh proposal), a given
    ``old`` is used as is (a stale proposal when the incumbent has moved on)."""

    mode, deterministic = "script_backend", True

    def __init__(self, steps) -> None:
        self.steps, self.n = list(steps), 0

    def propose_next_trial(self, status, memory_context, node_spec):
        from autoresearch.manager.base import ManagerProposal
        key, new, old = self.steps[self.n % len(self.steps)]
        self.n += 1
        old = status.current_constants[key] if old is None else old
        return ManagerProposal(manager_mode=self.mode, proposal_summary=f"{key} {old} -> {new}", proposal_rationale="",
                               target_files=tuple(node_spec.editable_paths), objective=f"Change {key}.",
                               extra={"structured_edit": {"type": "python_constant", "path": "train.py",
                                                          "symbol": key, "old": old, "new": new}})


# Trial 1 (kept unconditionally) moves HIDDEN_UNITS to 2048; trial 2 is the S0.4 s30000 shape: the proposal
# still expects 1024. Later trials are fresh, one of them stale again.
S04_SHAPE = [("HIDDEN_UNITS", "2048", None), ("HIDDEN_UNITS", "512", "1024"), ("ALPHA", "0.001", None),
             ("MAX_ITER", "80", None), ("HIDDEN_UNITS", "64", "1024"), ("ALPHA", "0.01", None)]


def _s04_controller(mod, sigma=S04_SIGMA, W=S04_W):
    ctx = node_context(sigma, runs=W, memory_mode="append_only_summary")
    return mod.ExecuteNonRuleController(None, ctx, obs_inflation=1.0), ctx


def _campaign(tmp_path, ctl, steps, budget=6, W=S04_W):
    kwargs = ctl.campaign_kwargs(W=W, llm_cap=budget)
    return run_campaign(tmp_path, ScriptBackend(steps), memory_mode="append_only_summary", **kwargs)


def _control(events, epoch):
    """budget index -> control_decision payload of that epoch (trial ids end in the zero-padded index)."""
    return {int(e["trial_id"].rsplit("-", 1)[-1]): e["payload"] for e in events
            if e["event_type"] == "control_decision" and e["payload"].get("epoch") == epoch and e.get("trial_id")}


# ---- 1. the S0.4 failure shape no longer crashes ---------------------------

def test_stale_proposal_of_the_s04_shape_crashed_the_pin_and_now_runs_through(tmp_path):
    old_ctl, _ = _s04_controller(_old_a2u())
    with pytest.raises(ReplayError, match="stale edit: HIDDEN_UNITS is '2048', edit expects '1024'") as exc:
        _campaign(tmp_path / "old", old_ctl, S04_SHAPE)
    assert "_e2_detail" in [entry.name for entry in exc.traceback]   # the S0.4 frame (E2, not E1)
    ctl, _ = _s04_controller(a2u)
    records, events, rows, worker = _campaign(tmp_path / "new", ctl, S04_SHAPE)
    assert [r["budget_index"] for r in rows] == list(range(1, 7))
    stale = [r for r in rows if (_row_edit(r) or {}).get("old") == "1024"]
    assert [r["budget_index"] for r in stale] == [2, 5]
    for r in stale:   # rejected by the harness before any worker run
        assert r["decision"] != "kept" and r["worker_mode"].endswith("_precheck") and r["delta_vs_best"] is None
        assert "proposal_precondition_failed" in json.dumps(r) and r["validity_status"] == "invalid"
    assert worker.runs == 4


def test_forecast_of_a_stale_current_proposal_is_none_with_reason(tmp_path):
    ctl, _ = _s04_controller(a2u)
    _, _, rows, _ = _campaign(tmp_path, ctl, S04_SHAPE)
    view = _views(rows, 1, S04_W)[0]
    fresh, _ = _s04_controller(a2u)
    assert fresh.forecast(view) is None and fresh.forecast_reason == a2u.STALE_PROPOSAL
    d = fresh.decide(view, {"skip": True})
    assert d.action == "continue" and d.detail["reason"] == a2u.STALE_PROPOSAL and d.detail["eligible"] is False
    with pytest.raises(a2u.StaleProposalError):
        a2u.replay(view, fresh.ctx)
    # A fresh proposal after it forecasts normally and clears the reason.
    ok = _views(rows, 2, S04_W)[0]
    assert fresh.forecast(ok) is not None and fresh.forecast_reason is None


def test_an_inconsistent_ledger_prefix_still_raises(tmp_path):
    """Only the current proposal is excused; a stale edit in an executed prefix row is a real replay error."""
    ctl, _ = _s04_controller(a2u)
    _, _, rows, _ = _campaign(tmp_path, ctl, S04_SHAPE)
    bad = json.loads(json.dumps(rows))
    bad[2]["extra"]["manager"]["structured_edit"]["old"] = "0.123"   # executed row 3 no longer replays
    view = ReplayView(budget_index=4, ledger_prefix=tuple(bad[:3]), current_best=bad[3]["current_best_before"],
                      proposal=ReplayProposal(extra={"structured_edit": _row_edit(bad[3])}))
    with pytest.raises(ReplayError) as exc:
        ctl.forecast(view)
    assert not isinstance(exc.value, a2u.StaleProposalError)


def test_numerically_equal_old_value_crashed_the_pin_at_e1_and_now_becomes_an_invalid_trial(tmp_path):
    """Second crash class (review finding 3): the harness precheck compares values numerically ("0.0001" ==
    "1e-4") and accepts the proposal, replay and the worker compare strings. The pin crashed at E1; the fix
    forecasts None (stale_proposal), the worker rejects the edit and the trial is invalid."""
    steps = [("HIDDEN_UNITS", "64", None), ("ALPHA", "0.001", "0.0001"), ("MAX_ITER", "80", None),
             ("HIDDEN_UNITS", "128", None)]
    old_ctl, _ = _s04_controller(_old_a2u())
    with pytest.raises(ReplayError, match="stale edit: ALPHA is '1e-4', edit expects '0.0001'") as exc:
        _campaign(tmp_path / "old", old_ctl, steps, budget=4)
    assert "_decide_e1" in [entry.name for entry in exc.traceback]
    ctl, _ = _s04_controller(a2u)
    _, events, rows, _ = _campaign(tmp_path / "new", ctl, steps, budget=4)
    assert [r["budget_index"] for r in rows] == [1, 2, 3, 4]
    assert rows[1]["decision"] != "kept" and rows[1]["delta_vs_best"] is None
    e1, e2 = _control(events, "E1"), _control(events, "E2")
    assert e1[2]["detail"]["reason"] == a2u.STALE_PROPOSAL and e1[2]["detail"]["eligible"] is False
    assert e2[2]["detail"]["eligible"] is False
    assert e1[3]["detail"]["eligible"] is True   # later trials replay normally (invalid rows never apply)


# ---- 2. an invalid trial's E2 is not eligible ------------------------------

def test_e2_of_an_invalid_trial_is_not_eligible_without_a_forecast(tmp_path):
    ctl, _ = _s04_controller(a2u)
    records, events, rows, _ = _campaign(tmp_path, ctl, S04_SHAPE)
    e2 = _control(events, "E2")
    for b in (2, 5):
        d = e2[b]["detail"]
        assert d["eligible"] is False and d["reason"] == "no_features_or_no_comparison"
    # Direct: delta_vs_best None returns before the forecast (a forecast call would fail here).
    probe, _ = _s04_controller(a2u)
    probe.forecast = lambda view: (_ for _ in ()).throw(AssertionError("forecast called on an invalid trial"))
    view = _views(rows, 1, S04_W)[1]
    assert view.provisional.delta_vs_best is None
    d = probe.decide(view, {})
    assert d.action == "continue"
    assert d.detail == {"controller": probe.version, "epoch": "E2", "decision": "failed_invalid",
                        "reason": "no_features_or_no_comparison", "eligible": False}


# ---- 3. valid trials: decisions and log byte-identical to d10b05b7 ---------

def _views(rows, i, W):
    row = rows[i]
    edit = _row_edit(row)
    prop = ReplayProposal(extra={"structured_edit": edit}) if edit else None
    used = sum(1 for r in rows[:i] if not str(r.get("worker_mode", "")).endswith(("_precheck", "control_plane")))
    budget = {"worker_runs_used": used, "worker_runs_remaining": W - used, "trials_remaining": W - i,
              "trials_total": W}
    e1 = SimpleNamespace(epoch="E1", budget_index=row["budget_index"], ledger_prefix=tuple(rows[:i]),
                         current_best=row.get("current_best_before"), proposal=prop, provisional=None, budget=budget,
                         input_hash=lambda: "h")
    e2 = SimpleNamespace(epoch="E2", budget_index=row["budget_index"], ledger_prefix=tuple(rows[:i]),
                         current_best=row.get("current_best_before"), proposal=prop, budget=budget,
                         provisional=SimpleNamespace(delta_vs_best=row.get("delta_vs_best"),
                                                     decision=SimpleNamespace(value=row.get("decision"))),
                         input_hash=lambda: "h")
    return e1, e2


def _dump(decision) -> str:
    import dataclasses
    return json.dumps(dataclasses.asdict(decision), sort_keys=True, default=repr)


def _a2u_with_prior(mod, sigma=S04_SIGMA, W=S04_W):
    """A2-U with a real prior and a positive g (the later phases' controller), not the S0.4 stand-in."""
    ctx = node_context(sigma, runs=W, memory_mode="append_only_summary")
    pr = mod.A2UPrior(node=NODE, sigma_node=sigma, kinds={"local": mod.KindPrior(0.001, 0.004, sigma, 0.002)})
    return mod.A2UController(pr, ctx, g=0.0004, W=W), ctx


def assert_identical_on_ledger(rows, *, sigma=S04_SIGMA, W=S04_W, factory=None):
    """Every trial's E1 and E2 decision of the fixed controller equals the pin's, byte for byte, where the pin
    did not raise; where the pin raised (only possible on a stale proposal), the fix returns "not eligible".
    The controller logs are equal as well. Returns (identical decisions, pin crashes)."""
    factory = factory or _s04_controller
    old_mod = _old_a2u()
    old, _ = factory(old_mod, sigma, W)
    new, _ = factory(a2u, sigma, W)
    same = crashed = 0
    crashed_at: set[int] = set()
    for i in range(len(rows)):
        for view in _views(rows, i, W):
            try:
                a = old.decide(view, {"skip": False})
            except ReplayError:
                crashed += 1
                crashed_at.add(int(rows[i]["budget_index"]))
                assert rows[i].get("delta_vs_best") is None or view.epoch == "E1"
                b = new.decide(view, {"skip": False})
                assert b.detail["eligible"] is False
                continue
            b = new.decide(view, {"skip": False})
            assert _dump(a) == _dump(b), (rows[i]["budget_index"], view.epoch)
            if view.epoch == "E2" and rows[i].get("delta_vs_best") is not None:   # the keep prior served at E2
                assert repr(old.keep_prior(view)) == repr(new.keep_prior(view)), rows[i]["budget_index"]
            same += 1
    # The log: identical except for the entries the fix adds where the pin raised (and logged nothing).
    new_log = [e for e in new.log if e["budget_index"] not in crashed_at]
    assert all(e["reason"] == a2u.STALE_PROPOSAL for e in new.log if e["budget_index"] in crashed_at)
    assert json.dumps(old.log, sort_keys=True, default=repr) == json.dumps(new_log, sort_keys=True, default=repr)
    return same, crashed


@pytest.mark.parametrize("seed", range(4))
def test_valid_trials_identical_to_the_pin_on_generated_campaigns(tmp_path, seed):
    """Generated S0.4-configured campaigns without stale proposals: everything identical, nothing crashes."""
    keys = [("ALPHA", "0.001", None), ("MAX_ITER", "80", None), ("HIDDEN_UNITS", "64", None),
            ("ALPHA", "0.0001", None), ("MAX_ITER", "40", None), ("HIDDEN_UNITS", "32", None),
            ("LEARNING_RATE_INIT", "0.01", None), ("LEARNING_RATE_INIT", "0.001", None)]
    steps = keys[seed:] + keys[:seed]
    ctl, _ = _s04_controller(a2u)
    _, _, rows, _ = _campaign(tmp_path, ctl, steps, budget=12)
    same, crashed = assert_identical_on_ledger(rows)
    assert crashed == 0 and same == 2 * len(rows)


@pytest.mark.parametrize("seed", range(2))
def test_valid_trials_identical_to_the_pin_for_a2u_with_a_prior(tmp_path, seed):
    keys = [("ALPHA", "0.001", None), ("MAX_ITER", "80", None), ("HIDDEN_UNITS", "64", None),
            ("ALPHA", "0.0001", None), ("LEARNING_RATE_INIT", "0.01", None), ("HIDDEN_UNITS", "32", None)]
    ctl, _ = _s04_controller(a2u)
    _, _, rows, _ = _campaign(tmp_path, ctl, keys[seed:] + keys[:seed], budget=10)
    same, crashed = assert_identical_on_ledger(rows, factory=_a2u_with_prior)
    assert crashed == 0 and same == 2 * len(rows)


def test_s04_shape_identical_except_where_the_pin_crashed(tmp_path):
    ctl, _ = _s04_controller(a2u)
    _, _, rows, _ = _campaign(tmp_path, ctl, S04_SHAPE)
    same, crashed = assert_identical_on_ledger(rows)
    assert crashed == 4 and same == 2 * len(rows) - 4   # E1 and E2 of trials 2 and 5


S04_COMMITTED = ("tracks_S04_digits_mlp__s30001", "tracks_S04_digits_mlp__s30004", "tracks_S04_digits_mlp__s30006",
                 "tracks_S04_digits_mlp__s30007", "tracks_S04_digits_mlp__s30009")   # roots.jsonl of the s04 scene


def _s04_ledgers():
    if os.environ.get("TRACKS_S04_ROOTS"):
        # Set explicitly (the TASL-2 check): missing ledgers are a failure, never a skip (review finding 2).
        found = [S04_ROOTS / r / "root_trials.jsonl" for r in S04_COMMITTED]
        missing = [str(p) for p in found if not p.is_file()]
        assert not missing, f"TRACKS_S04_ROOTS set but ledgers missing: {missing}"
        return found
    if not S04_ROOTS.is_dir():
        return []
    found = [S04_ROOTS / r / "root_trials.jsonl" for r in S04_COMMITTED if (S04_ROOTS / r / "root_trials.jsonl").is_file()]
    assert not found or len(found) == len(S04_COMMITTED), f"only {len(found)} of the 5 committed S0.4 ledgers present"
    return found


@pytest.mark.skipif(not _s04_ledgers(), reason=f"S0.4 committed-root ledgers not present under {S04_ROOTS} "
                    "(copy back from TASL-2 <run.work>/roots/<root_id>/root_trials.jsonl); generated campaigns above")
@pytest.mark.parametrize("path", _s04_ledgers(), ids=lambda p: p.parent.name)
def test_valid_trials_identical_to_the_pin_on_the_s04_committed_roots(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    same, crashed = assert_identical_on_ledger(rows)
    assert crashed == 0 and same == 2 * len(rows)
    print(f"{path.parent.name}: {len(rows)} trials identical; ledger sha256 "
          f"{__import__('hashlib').sha256(path.read_bytes()).hexdigest()}")
