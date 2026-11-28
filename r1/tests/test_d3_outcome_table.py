"""D.3 gap G7: outcome-table builder writing ``r1_d3_outcome/v2``. Synthetic inputs only. AI-assisted (Claude)."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from r1.c3 import d3_analysis as D3
from r1.c3 import d3_hpo_ref as HPO
from r1.c3 import d3_outcome_table as T
from r1.c3.accounting import campaign_usage
from r1.c3.d3_controllers import a0r_controller
from r1.harness import REPO
from r1.tests.c3_campaign_fixtures import SequenceBackend, node_context, run_campaign

START, FINAL, MID = "b" * 64, "c" * 64, "d" * 64
GPU = {n: ("NVIDIA H200" if i % 2 else "NVIDIA A100-SXM4-80GB") for i, n in enumerate(D3.NODES)}


def _summary(stage, arm, node, seed, rep=0, **over):
    s = {"schema": T.SUMMARY_SCHEMA, "stage": stage, "arm": arm, "node": node, "instance_seed": seed,
         "repetition": rep, "status": "complete", "gpu_model": None if stage == "HPO-REF" else GPU[node],
         "infra_attempts": 1, "worker_runs": 20, "llm_calls": 0 if stage == "HPO-REF" else 30, "unfundable": False,
         "start_config_hash": START, "final_config_hash": FINAL, "last_keep_run": 9,
         "proposals": 30, "llm_tokens_prompt": 0 if stage == "HPO-REF" else 1000,
         "llm_tokens_completion": 0 if stage == "HPO-REF" else 300, "worker_seconds": 12.5,
         "proposer_gpu_seconds": 0.0 if stage == "HPO-REF" else 40.0, "controller_seconds": 0.1,
         "wall_seconds": 60.0, "duplicates_proposed": 3, "duplicates_executed": 0, "rule_skips": 0,
         "value_skips": 0, "keeps": 2, "distinct_configs_executed": 10}
    if arm not in D3.RULE_LAYER_ARMS:
        s["duplicates_executed"] = 3
    else:
        s["rule_skips"] = 3
    s.update(over)
    return s


def _audits(stage, arm, node, seed, rep=0, *, runs=20, y=0.01, keeps=((1, 0.004, MID), (9, None, FINAL))):
    cid = D3.campaign_id(stage, arm, node, seed, rep)
    out = []
    if runs == 0:
        return out

    def a(point, y_raw, cfg=FINAL, keep_run=None):
        return {"schema": T.AUDIT_ROW_SCHEMA, "campaign_id": cid, "point": point, "keep_run": keep_run,
                "config_sha256": cfg, "y_raw": y_raw}
    out.append(a("final", y))
    for w in D3.BUDGET_POINTS:
        if w <= runs:
            out.append(a(str(w), y if w == 20 else y / 2, FINAL if w == 20 else MID))
    for run, yk, cfg in keeps:
        out.append(a("keep", y if yk is None else yk, cfg, run))
    return out


def _design(stage="D.3a", arms=None):
    arms = arms or {"D.3a": D3.ARMS_D3A, "D.3b": D3.ARMS_D3B, "HPO-REF": D3.ARMS_HPO}[stage]
    sums, auds = [], []
    for arm in arms:
        for node in D3.NODES:
            for seed in D3.INSTANCE_SEEDS:
                sums.append(_summary(stage, arm, node, seed))
                auds += _audits(stage, arm, node, seed)
    return sums, auds


@pytest.fixture
def pre():
    return REPO / "docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md"


def _note(tmp_path, a6):
    p = tmp_path / "d3b_note.md"
    p.write_text(f"approved: true\na6_entered: {'true' if a6 else 'false'}\n")
    return p


def test_full_d3a_table_is_accepted_by_the_pinned_analysis_and_written_once(tmp_path, pre):
    sums, auds = _design()
    table = T.build_table("D.3a", sums, auds, predeclaration_path=pre)
    assert len(table["rows"]) == 7 * 7 * 18 and table["schema"] == "r1_d3_outcome/v2"
    assert table["predeclaration_sha256"] == hashlib.sha256(pre.read_bytes()).hexdigest()
    row = table["rows"][0]
    assert row["arm"] == "A0" and row["ended_on"] == "worker_runs" and row["y_raw_w"]["20"] == row["y_raw"] == 0.01
    assert row["last_improving_run"] == 9 and row["audit_seeds"] == list(range(6701, 6711))
    out = T.write_table(table, tmp_path / "d3a_outcome.json")
    with pytest.raises(FileExistsError):
        T.write_table(table, out)
    loaded = D3.load_table(out, "D.3a")
    assert loaded == json.loads(json.dumps(table))
    D3.verify_sigma_against_noise_source(loaded["sigma_node"])
    report = D3.analyse(loaded, d3b_not_run="not_started")  # the pinned analysis runs end to end on it
    assert report["families"]["D.3b"]["status"] == "not_run" and "D.3a" in report["secondary"]


@pytest.mark.parametrize("stage", D3.STAGES)
def test_each_stage_refuses_changed_predeclaration_bytes(tmp_path, pre, stage):
    old = REPO / "docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md"
    changed = tmp_path / pre.name
    changed.write_bytes(pre.read_bytes() + b"\n")
    for wrong in (changed, old):
        with pytest.raises(T.OutcomeTableError, match="sha256 differs from frozen revision 5"):
            T.build_table(stage, [], [], predeclaration_path=wrong)


def test_write_refuses_a_table_with_a_changed_predeclaration_hash(tmp_path, pre):
    sums, auds = _design()
    table = T.build_table("D.3a", sums, auds, predeclaration_path=pre)
    table["predeclaration_sha256"] = "0" * 64
    out = tmp_path / "table.json"
    with pytest.raises(T.OutcomeTableError, match="sha256 differs from frozen revision 5"):
        T.write_table(table, out)
    assert not out.exists()


def _one(stage="D.3a", arm="A0", **over):
    return _summary(stage, arm, "digits_mlp", 6201, **over)


def test_an_early_end_has_missing_budget_points_and_the_declared_ended_on():
    s = _one(arm="FIXR3", worker_runs=18, unfundable=True, last_keep_run=9)
    row = T.build_row("D.3a", s, T._audits_by_campaign(_audits("D.3a", "FIXR3", "digits_mlp", 6201, runs=18))[
        D3.campaign_id("D.3a", "FIXR3", "digits_mlp", 6201, 0)])
    assert row["ended_on"] == "no_fundable_candidate" and row["y_raw_w"]["20"] is None
    assert row["y_raw_w"]["15"] == 0.005


def test_last_keep_run_without_a_keep_is_refused():
    s = _one(arm="A1", worker_runs=0, llm_calls=80, final_config_hash=START, keeps=0, last_keep_run=3,
             duplicates_proposed=0, duplicates_executed=0, distinct_configs_executed=0)
    with pytest.raises(T.OutcomeTableError, match="last_keep_run must be null"):
        T.build_row("D.3a", s, None)


def test_a_campaign_without_a_charged_run_has_y_zero_and_no_audit():
    s = _one(arm="A1", worker_runs=0, llm_calls=80, final_config_hash=START, keeps=0, last_keep_run=None,
             duplicates_proposed=0, duplicates_executed=0, distinct_configs_executed=0)
    row = T.build_row("D.3a", s, None)
    assert (row["y_raw"], row["ended_on"], row["last_improving_run"]) == (0.0, "llm_call_cap", None)
    assert row["y_raw_w"] == {"5": None, "10": None, "15": None, "20": None}


def _cid(arm="A0"):
    return D3.campaign_id("D.3a", arm, "digits_mlp", 6201, 0)


def _by(auds):
    return T._audits_by_campaign(auds)[_cid()]


@pytest.mark.parametrize("mutate,match", [
    (lambda s, a: s.update(status="stop"), "STOP"),
    (lambda s, a: a.__setitem__(slice(None), [x for x in a if x["point"] != "final"]), "final-incumbent audit"),
    (lambda s, a: next(x for x in a if x["point"] == "final").update(config_sha256=MID), "another configuration"),
    (lambda s, a: a.__setitem__(slice(None), [x for x in a if x["point"] != "10"]), "w = 10 is missing"),
    (lambda s, a: next(x for x in a if x["point"] == "20").update(y_raw=0.02), "one canonical audit"),
    (lambda s, a: s.update(keeps=3), "one keep audit per keep"),
    (lambda s, a: s.update(last_keep_run=8), "not at last_keep_run"),
    (lambda s, a: next(x for x in a if x["point"] == "keep" and x["keep_run"] == 9).update(y_raw=0.5),
     "must agree"),
    (lambda s, a: s.update(worker_runs=12, llm_calls=12), "has not ended"),
    (lambda s, a: s.update(unfundable="no"), "boolean"),
    (lambda s, a: s.update(extra=1), "exactly"),
    (lambda s, a: s.update(keeps=2.0), "integer"),
    (lambda s, a: s.update(proposals=None), "integer"),
])
def test_row_refusals(mutate, match):
    s, a = _one(), _audits("D.3a", "A0", "digits_mlp", 6201)
    mutate(s, a)
    with pytest.raises(T.OutcomeTableError, match=match):
        T.build_row("D.3a", s, T._audits_by_campaign(a).get(_cid()))


def test_snapshot_audit_beyond_the_final_count_is_refused():
    s = _one(arm="FIXR3", worker_runs=18, unfundable=True)
    a = _audits("D.3a", "FIXR3", "digits_mlp", 6201, runs=20)
    with pytest.raises(T.OutcomeTableError, match="ended at 18"):
        T.build_row("D.3a", s, T._audits_by_campaign(a)[_cid("FIXR3")])


@pytest.mark.parametrize("bad,match", [
    ({"y_raw": float("nan")}, "finite"), ({"point": "7"}, "audit point"), ({"keep_run": 3}, "only for keep"),
    ({"schema": "x"}, "schema"),
])
def test_audit_row_refusals(bad, match):
    a = _audits("D.3a", "A0", "digits_mlp", 6201)
    a[0].update(bad)
    with pytest.raises(T.OutcomeTableError, match=match):
        T._audits_by_campaign(a)


def test_duplicate_audit_point_and_orphan_audit_are_refused(pre):
    a = _audits("D.3a", "A0", "digits_mlp", 6201)
    with pytest.raises(T.OutcomeTableError, match="twice"):
        T._audits_by_campaign(a + [copy.deepcopy(a[0])])
    sums, auds = _design()
    orphan = copy.deepcopy(auds[0])
    orphan["campaign_id"] = D3.campaign_id("D.3a", "A0", "digits_mlp", 6201, 1)
    with pytest.raises(T.OutcomeTableError, match="no summary"):
        T.build_table("D.3a", sums, auds + [orphan], predeclaration_path=pre)


def test_a_partial_design_is_refused_by_the_analysis_rule(pre):
    sums, auds = _design()
    with pytest.raises(D3.D3InputError, match="does not cover the declared design"):
        T.build_table("D.3a", sums[:-1], [a for a in auds if a["campaign_id"] != _cid_of(sums[-1])],
                      predeclaration_path=pre)


def _cid_of(s):
    return D3.campaign_id(s["stage"], s["arm"], s["node"], s["instance_seed"], s["repetition"])


def test_gpu_model_must_be_one_per_instance(pre):
    sums, auds = _design()
    sums[0]["gpu_model"] = "NVIDIA L40S"
    with pytest.raises(D3.D3InputError, match="more than one GPU model"):
        T.build_table("D.3a", sums, auds, predeclaration_path=pre)


@pytest.mark.parametrize("a6,arms", [(False, ["A3", "A5"]), (True, ["A3", "A5", "A6"])])
def test_d3b_arms_follow_the_signed_note(tmp_path, pre, a6, arms):
    sums, auds = _design("D.3b", arms)
    table = T.build_table("D.3b", sums, auds, predeclaration_path=pre, d3b_note=_note(tmp_path, a6))
    assert table["arms"] == arms and table["a6_entered"] is a6
    assert table["predeclaration_sha256"] == hashlib.sha256(pre.read_bytes()).hexdigest()
    with pytest.raises(T.OutcomeTableError, match="needs the signed D.3b note"):
        T.build_table("D.3b", sums, auds, predeclaration_path=pre)
    with pytest.raises(T.OutcomeTableError, match="only a D.3b table"):
        T.build_table("D.3a", sums, auds, predeclaration_path=pre, d3b_note=_note(tmp_path, a6))


def test_hpo_ref_rows(pre):
    sums, auds = _design("HPO-REF")
    s0 = next(s for s in sums if s["arm"] == "RS")
    s0.update(worker_runs=17, proposals=80, last_keep_run=9)
    auds = [a for a in auds if not (a["campaign_id"] == _cid_of(s0) and a["point"] == "20")]
    table = T.build_table("HPO-REF", sums, auds, predeclaration_path=pre)
    digest = hashlib.sha256(pre.read_bytes()).hexdigest()
    assert table["predeclaration_sha256"] == digest
    assert HPO.build_table(table["rows"], predeclaration_sha256=digest,
                           sigma_node=table["sigma_node"])["predeclaration_sha256"] == digest
    old = REPO / "docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md"
    for wrong in ("0" * 64, hashlib.sha256(old.read_bytes()).hexdigest()):
        with pytest.raises(HPO.HpoRefError, match="sha256 differs from frozen revision 5"):
            HPO.build_table(table["rows"], predeclaration_sha256=wrong, sigma_node=table["sigma_node"])
    r0 = next(r for r in table["rows"] if r["campaign_id"] == _cid_of(s0))
    assert r0["ended_on"] == "proposal_cap" and r0["gpu_model"] is None and r0["memory_mode"] == "not_applicable"
    smac = next(s for s in sums if s["arm"] == "SMAC3")
    smac.update(worker_runs=17, proposals=80)
    with pytest.raises(T.OutcomeTableError, match="has not ended"):
        T.build_row("HPO-REF", smac, None)


@pytest.mark.parametrize("keeps,expect", [([], None), ([(1, 0.0)], None), ([(1, 0.01)], 1),
                                          ([(1, 0.01), (5, 0.005), (9, 0.02)], 9),
                                          ([(1, 0.01), (5, 0.02), (9, 0.015)], 5), ([(3, -0.01), (7, 0.0)], 7)])
def test_last_improving_run(keeps, expect):
    assert T.last_improving_run(keeps) == expect


DUP_EDITS = [("HIDDEN_UNITS", "32", "64"), ("ALPHA", "1e-4", "1e-3"), ("ALPHA", "1e-4", "1e-3"),
             ("MAX_ITER", "40", "80"), ("ALPHA", "1e-4", "1e-3")]


def _config_of(record):
    edit = (record.get("extra") or {}).get("manager", {}).get("structured_edit")
    return hashlib.sha256(json.dumps(edit, sort_keys=True).encode()).hexdigest()


def test_mechanism_counts_on_a_harness_campaign(tmp_path):
    ctl = a0r_controller(node_context(0.005))
    _, events, rows, worker = run_campaign(tmp_path, SequenceBackend(DUP_EDITS), **ctl.campaign_kwargs(d3=False, W=20, llm_cap=8))
    m = T.mechanism_counts(rows, events, config_of=_config_of)
    skipped = [r for r in rows if r["decision"] == "skipped"]
    assert m["rule_skips"] == len(skipped) > 0 and m["duplicates_proposed"] >= m["rule_skips"]
    assert m["duplicates_executed"] == 0 and m["value_skips"] == 0
    u = campaign_usage(tmp_path / "trials.jsonl", tmp_path / "events.jsonl", arm="A0R", instance="i",
                       information_set="s", worker_run_cap=20, llm_call_cap=8, manager_deterministic=True)
    assert m["worker_runs"] == u.worker_runs == worker.runs
    assert m["keeps"] == sum(r["decision"] == "kept" for r in rows) and m["last_keep_run"] is not None
    assert m["distinct_configs_executed"] <= m["worker_runs"]


def test_mechanism_counts_charge_replicates_and_refuse_an_executed_trial_without_a_config():
    rows = [{"budget_index": 1, "trial_id": "t1", "worker_mode": "w", "decision": "kept",
             "extra": {"control": {"replicates": [{"role": "candidate", "j": 1, "seed": 6501, "success": True,
                                                   "charged": True},
                                                  {"role": "candidate", "j": 2, "seed": 6502, "success": True,
                                                   "charged": True}]}}},
            {"budget_index": 2, "trial_id": "t2", "worker_mode": "w", "decision": "discarded", "extra": {}}]
    events = [{"event_type": "control_decision", "trial_id": "t1",
               "payload": {"epoch": "E1", "detail": {"reason": "no_features"}}},
              {"event_type": "control_decision", "trial_id": "t2",
               "payload": {"epoch": "E1", "detail": {"rule": {"noop": False, "duplicate": True}}}}]
    m = T.mechanism_counts(rows, events, config_of=lambda r: r["trial_id"])
    assert (m["worker_runs"], m["last_keep_run"], m["keeps"], m["distinct_configs_executed"]) == (4, 3, 1, 2)
    assert (m["duplicates_proposed"], m["duplicates_executed"]) == (1, 1)
    with pytest.raises(T.OutcomeTableError, match="without a configuration"):
        T.mechanism_counts(rows, events, config_of=lambda r: None)
    with pytest.raises(T.OutcomeTableError, match="flag-logging controller"):
        T.mechanism_counts(rows, events[:1], config_of=lambda r: r["trial_id"])
    unflagged = [events[0], {**events[1], "payload": {"epoch": "E1", "detail": {}}}]
    with pytest.raises(T.OutcomeTableError, match="flag-logging controller"):
        T.mechanism_counts(rows, unflagged, config_of=lambda r: r["trial_id"])


def test_a_campaign_under_continue_controller_is_refused(tmp_path):
    from autoresearch.control_plane.action_versions import ActionVersions
    from autoresearch.control_plane.controller import ContinueController
    kw = a0r_controller(node_context(0.005)).campaign_kwargs(d3=False, W=20, llm_cap=6)
    kw["controller"] = ContinueController()
    kw["action_versions"] = ActionVersions.new_campaign()
    _, events, rows, _ = run_campaign(tmp_path, SequenceBackend(DUP_EDITS), **kw)
    with pytest.raises(T.OutcomeTableError, match="flag-logging controller"):
        T.mechanism_counts(rows, events, config_of=_config_of)


def test_over_budget_propagates_as_a_stop():
    from r1.c3.accounting import OverBudget
    with pytest.raises(OverBudget):
        T.build_row("D.3a", _one(worker_runs=21), None)
    with pytest.raises(OverBudget):
        T.build_row("D.3a", _one(llm_calls=81), None)


def test_path_and_write_guards(tmp_path, pre):
    sums, auds = _design()
    bad = tmp_path / "predeclaration.txt"
    bad.write_text("x")
    with pytest.raises(T.OutcomeTableError, match=".md"):
        T.build_table("D.3a", sums, auds, predeclaration_path=bad)
    lab = tmp_path / "labels.md"
    lab.write_text("x")
    with pytest.raises(D3.D3InputError):
        T.build_table("D.3a", sums, auds, predeclaration_path=lab)
    table = T.build_table("D.3a", sums, auds, predeclaration_path=pre)
    with pytest.raises(D3.D3InputError):
        T.write_table(table, tmp_path / "eval_labels.json")


def test_a_failed_write_leaves_no_partial_file(tmp_path, pre, monkeypatch):
    sums, auds = _design()
    table = T.build_table("D.3a", sums, auds, predeclaration_path=pre)
    real = T.os.fdopen

    class Boom:
        def __init__(self, fd, mode):
            self.fh = real(fd, mode)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.fh.close()

        def write(self, data):
            self.fh.write(data[:10])
            raise OSError("disk full")
    monkeypatch.setattr(T.os, "fdopen", Boom)
    out = tmp_path / "d3a_outcome.json"
    with pytest.raises(OSError, match="disk full"):
        T.write_table(table, out)
    assert not out.exists()
