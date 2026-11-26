"""The G.5 job (sweep2/t1_tasl/g5_job.py, G.5 code unit part 3b-1): waves, audit planning and chunks, E5, diagnostics,
the STOP counters, K uniformity, the access log, and the job end to end with fake host tools, a fake proposer and fake
harness engines. Synthetic only: no GPU, no network, no harness engine, no label is read (rows carry a synthetic value
that the job never reads).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
import g5_tasl as S  # noqa: E402
import g5_job as J  # noqa: E402
import g1b_tasl as G  # noqa: E402
import g4_tasl as T4  # noqa: E402

SPEC = json.loads((ROOT / "sweep2" / "t1_tasl" / "g5_tasl_spec.json").read_text())
UUID2 = SPEC["worker"]["gpu_uuid"]
LS = J.LEDGER_SCHEMA
RUN_S = 10.0          # synthetic run seconds in the ledgers (below every node's timeout basis)


def stop(match, fn, *a, **kw):
    with pytest.raises(J.Stop, match=match):
        fn(*a, **kw)


# =============================================================================================== synthetic ledgers
def step_line(step, decision, parent=None, cand=None, diff=None, prompt=1000, completion=300, reason=None):
    e = {"schema": LS, "step": step, "decision": decision,
         "manager_call": {"usage": {"prompt_tokens": prompt, "completion_tokens": completion, "wall_seconds": 30.0},
                          "request": {"cache_prompt": False}}}
    if decision in J.RAN:
        e["proposal"] = {"diff": diff}
        e["runs"] = [{"code_state_sha256": cand, "incumbent_code_state_sha256": parent, "executed": True,
                      "elapsed_seconds_info_only": RUN_S}]
        e["final_outcome"] = {"kind": "divergent" if decision == "discarded_divergent" else "ok", "reason": reason,
                              "value": 0.5}
    return json.dumps(e)


def ledger(k, *, wave_tag="", base="B", steps=20, invalid=(4, 12), divergent=(), first_kept=True):
    """Instance k: step 1 proposes the common diff d1 from the baseline (kept), then ran / invalid / inert steps."""
    lines = [json.dumps({"schema": LS, "step": 0, "decision": "baseline", "runs": [{"code_state_sha256": base}],
                         "final_outcome": {"kind": "ok", "value": 0.4}})]
    parent = base
    if first_kept:
        lines.append(step_line(1, "kept", base, "C1", "d1"))
        parent = "C1"
    for s in range(2, steps + 1):
        if s in invalid:
            lines.append(step_line(s, "invalid_proposal"))
        elif s % 4 in (2, 3):
            dec = "discarded_divergent" if s in divergent else "discarded"
            lines.append(step_line(s, dec, parent, f"S{wave_tag}{k}_{s}", f"diff-{wave_tag}{k}-{s}",
                                   reason="timeout" if s in divergent else None))
        else:
            lines.append(step_line(s, "not_run_inert"))
    return lines


def wave_ledgers(spec, wave, **kw):
    return {J.campaign_dir_name(i): ledger(i["instance"], wave_tag=f"w{wave}", **kw)
            for i in J.wave_instances(spec, wave)}


# =============================================================================================== instances, campaign file
def test_wave_instances_and_campaign_file():
    w1, w2 = J.wave_instances(SPEC, 1), J.wave_instances(SPEC, 2)
    assert [i["instance"] for i in w1] == [1, 2, 3, 4] and [i["instance"] for i in w2] == list(range(5, 13))
    assert all(i["train_seed"] == i["split_seed"] == i["manager_seed"] == 5100 + i["instance"] for i in w1 + w2)
    assert {i["memory_mode"] for i in w1} == {"history"}
    b = S.apply_options(SPEC, {"G5-MEM": "B"})
    twins = J.wave_instances(b, 1)
    assert len(twins) == 8 and {(i["instance"], i["memory_mode"]) for i in twins} == \
        {(k, m) for k in range(1, 5) for m in ("history", "none")}
    node = S.node_entry(SPEC, "mlab_imdb")
    f = J.campaign_file(SPEC, node, 1, interpreter="/py", cgroup_parent="/cg", deadline_epoch=1.0)
    assert (f["schema"], f["label"], f["budget"], f["temperature"], f["max_tokens"], f["measured_run_seconds"]) == \
        ("trackg_g5_campaign/v1", "EVIDENCE", 20, 0.2, 4096, 65.156)
    assert f["extra_payload"] == {"cache_prompt": False} and f["isolation_waivers"] == {}
    t = S.apply_options(SPEC, {"G5-TEMP": "B"})
    assert J.campaign_file(t, node, 1, interpreter="/py", cgroup_parent="/cg", deadline_epoch=1.0)["temperature"] == 0.0
    stop("G5-W B", J.campaign_file, S.apply_options(SPEC, {"G5-W": "B"}), node, 1, interpreter="/py",
         cgroup_parent="/cg", deadline_epoch=1.0)


# =============================================================================================== plan
def test_rematerialisation_and_integrity():
    led = J.parse_ledger(ledger(1, wave_tag="w1"), "instance_1_history")
    assert led["baseline_state"] == "B"
    st = {s["step"]: s for s in led["steps"]}
    assert st[1]["chain"] == [] and st[1]["parent_state"] == "B"
    assert st[2]["chain"] == ["d1"] and st[2]["parent_state"] == "C1" and st[2]["candidate_state"] == "Sw11_2"
    bad = ledger(1)
    bad[3] = step_line(3, "discarded", "B", "X", "dx")         # its incumbent is not the kept chain's last state
    stop("does not follow the kept chain", J.parse_ledger, bad, "instance_1_history")
    stopped = ledger(1)[:3] + [json.dumps({"schema": LS, "step": 3, "decision": "stop_transport"})]
    assert J.parse_ledger(stopped, "x")["stop"] == "stop_transport"


def test_audit_plan_groups_units_and_options():
    ledgers = wave_ledgers(SPEC, 1, divergent=(6,))
    plan = J.audit_plan(SPEC, "mlab_imdb", 1, ledgers, k=10)
    common = [g for g in plan["groups"] if g["candidate_state"] == "C1"]
    assert len(common) == 1 and len(common[0]["members"]) == 4          # audited once across instances
    assert len(plan["groups"]) == 1 + 4 * 10
    states = {u["state"]: u for u in plan["units"]}                     # reuse: one unit per code state
    assert states["B"]["diffs"] == [] and states["C1"]["diffs"] == ["d1"]
    assert states["Sw12_6"]["diffs"] == ["d1", "diff-w12-6"]
    assert len(plan["units"]) == 2 + 40 and plan["seeds"] == list(range(7001, 7011))
    b = S.apply_options(SPEC, {"G5-AUDIT": "B"})                        # ok outcomes only
    assert len(J.audit_plan(b, "mlab_imdb", 1, ledgers, k=10)["groups"]) == 1 + 4 * 9
    nr = copy.deepcopy(SPEC)
    nr["audit"]["reuse_parent_runs"] = False                            # every group has its own two units
    p = J.audit_plan(nr, "mlab_imdb", 1, ledgers, k=6)          # M5: one parent unit per distinct parent state
    parents = {u["unit"] for u in p["units"] if u["unit"].startswith("parent:")}
    assert parents == {"parent:B", "parent:C1"} and len(p["units"]) == len(p["groups"]) + 2
    assert p["label_seeds"] == [7001, 7002, 7003]
    assert p["seeds"] == [7001, 7002, 7003, 7006, 7007, 7008]
    w2 = J.audit_plan(SPEC, "mlab_imdb", 2, wave_ledgers(SPEC, 2), k=10,
                      prior_units={u["unit"]: u for u in plan["units"]},
                      prior_groups={f"{g['parent_state']}:{g['candidate_state']}" for g in plan["groups"]})
    assert [len(c["members"]) for c in w2["carried_groups"]] == [8]     # step 1 of wave 2: carried, not re-run
    assert w2["reused_units"] == ["C1"] and not {"B", "C1"} & {u["unit"] for u in w2["units"]}
    two = dict(ledgers)
    two["instance_9_history"] = ledger(9, base="B2")
    stop("disagree on the baseline", J.audit_plan, SPEC, "mlab_imdb", 1, two, k=10)


def test_chunks_fit_the_walltime(monkeypatch):
    node = S.node_entry(SPEC, J.S.AR)
    plan = J.audit_plan(SPEC, J.S.AR, 1, wave_ledgers(SPEC, 1), k=10)
    chunks = J.chunk_plan(plan, node)
    assert sum(len(c) for c in chunks) == len(plan["units"]) * 10
    assert all(len(c) * node["run_seconds"] * 1.25 * 1.5 <= J.CHUNK_LIMIT_S for c in chunks)
    f = J.audit_chunk_file(SPEC, node, plan, 0, chunks[0], interpreter="/py", cgroup_parent="/cg", deadline_epoch=1.0)
    assert f["schema"] == "trackg_g5_audit_chunk/v1" and f["split_policy"] == "vary"
    assert {u["unit"] for u in f["units"]} == {r["unit"] for r in chunks[0]}
    stop("STOP 10", J.audit_chunk_file, SPEC, node, plan, 0, [{"unit": "B", "seed": 9001, "train_seed": 9001,
                                                                "split_seed": 9001}], interpreter="/py",
         cgroup_parent="/cg", deadline_epoch=1.0)


# =============================================================================================== rows, E5
# the isolation block as audit_g5._isolation_block writes it at the G.5 harness commits (all six keys)
ISOLATED = {"effective": True, "waivers": {}, "exceptions": [], "log_intact": True, "parent_traced_by": None,
            "parent_dumpable_at_accept": False}


def make_rows(chunk, kind=lambda unit, state, seed: "ok"):
    state = {u["unit"]: u["code_state_sha256"] for u in chunk["units"]}
    return [json.dumps({"schema": J.ROW_SCHEMA, "unit": r["unit"], "seed": r["seed"], "executed": True,
                        "code_state_sha256": state[r["unit"]], "value": 0.123,
                        "outcome": {"kind": kind(r["unit"], state[r["unit"]], r["seed"]), "reason": None},
                        "isolation": dict(ISOLATED)}) for r in chunk["runs"]]


def small_plan(k=10):
    return J.audit_plan(SPEC, "mlab_imdb", 1, {"instance_1_history": ledger(1, steps=3, invalid=())}, k=k)


def test_read_rows_checks():
    plan = small_plan()
    chunk = J.audit_chunk_file(SPEC, S.node_entry(SPEC, "mlab_imdb"), plan, 0, J.chunk_plan(plan, {"run_seconds": 1})[0],
                               interpreter="/py", cgroup_parent="/cg", deadline_epoch=1.0)
    rows = make_rows(chunk)
    got = J.read_rows(rows, chunk)
    assert len(got) == len(chunk["runs"]) and all("value" not in r for r in got)       # the value is never returned
    stop("have no row", J.read_rows, rows[:-1], chunk)
    stop("appears twice", J.read_rows, rows + rows[:1], chunk)
    bad = json.loads(rows[0]) | {"isolation": dict(ISOLATED, waivers={"x": 1})}
    stop("STOP 2", J.read_rows, [json.dumps(bad)] + rows[1:], chunk)
    bad = json.loads(rows[0]) | {"seed": 7004 if plan["K"] == 6 else 9001}
    stop("STOP 10", J.read_rows, [json.dumps(bad)] + rows[1:], chunk)
    bad = json.loads(rows[0]) | {"code_state_sha256": "other"}
    stop("integrity", J.read_rows, [json.dumps(bad)] + rows[1:], chunk)


def test_e5_on_label_seeds_only():
    plan = small_plan()
    groups = {g["candidate_state"]: g for g in plan["groups"]}

    def rows_for(divergent: dict):
        out = []
        for u in plan["units"]:
            for s in plan["seeds"]:
                kind = "divergent" if s in divergent.get(u["state"], ()) else "ok"
                out.append({"unit": u["unit"], "seed": s, "kind": kind, "reason": None})
        return out
    lab, ev = plan["label_seeds"], [7006, 7007, 7008, 7009, 7010]
    res = J.e5(plan, rows_for({"S1_2": lab[:3], "S1_3": lab[:1], "C1": ev}))
    assert (res["audited"], res["divergent_label"], res["partial_label"]) == (3, 1, 1)
    assert res["complete_label"] == 1                                       # C1: evaluation-seed divergence ignored
    res = J.e5(plan, rows_for({"S1_2": lab[:2]}))                          # 2 of 5 is not more than half
    assert res["divergent_label"] == 0 and res["partial_label"] == 1
    res = J.e5(plan, rows_for({"B": lab[:1]}))                              # the baseline parent diverged at a seed
    assert res["baseline_label_divergent_other"] == 1 and res["baseline_label_timeouts"] == 0
    assert res["partial_label"] == 1
    timed = [dict(r, reason="timeout") if r["unit"] == "B" and r["seed"] == lab[0] else r
             for r in rows_for({"B": lab[:1]})]
    res = J.e5(plan, timed)
    assert res["baseline_label_timeouts"] == 1 and res["baseline_label_divergent_other"] == 0
    stop("lacks label-seed rows", J.e5, plan, rows_for({})[1:])
    assert groups["C1"]["parent_state"] == "B"


# =============================================================================================== diagnostics, STOPs
def diag_campaign(ledgers, wave=1, node="mlab_imdb"):
    c = J.campaign_counts(ledgers, max_tokens=4096, ctx=32768)
    return J.check_diagnostics({"schema": J.DIAG_CAMPAIGN, "label": "EVIDENCE", "run_id": "r", "node": node,
                                "job": f"campaigns-wave{wave}", "wave": wave, "attempt": 1, "spec_sha256": "s",
                                **c, "gpu_seconds": 10.0, "stop": None, "stop_class": None})


def diag_audit(e5, wave=1, node="mlab_imdb"):
    return J.check_diagnostics({"schema": J.DIAG_AUDIT, "label": "EVIDENCE", "run_id": "r", "node": node,
                                "job": f"audits-wave{wave}", "wave": wave, "attempt": 1, "spec_sha256": "s",
                                "chunk": 0, "chunks": 1, "K": 10, "plan_sha256": "p", "runs_planned_label": 5,
                                "runs_planned_evaluation": 5, "label_seed_runs": {"ok": 5, "divergent": 0,
                                                                                   "infrastructure": 0},
                                "seeds_planned": [7001], "wave_e5": e5, "gpu_seconds": 5.0, "stop": None,
                                "stop_class": None})


def e5_counts(audited, divergent, baseline=0, other=0):
    return {"audited": audited, "members": audited, "divergent_label": divergent, "partial_label": 0,
            "complete_label": audited - divergent, "parent_divergent_seeds": 0, "baseline_label_timeouts": baseline,
            "baseline_label_divergent_other": other}


def test_campaign_counts_and_fixed_schema():
    d = diag_campaign(wave_ledgers(SPEC, 1))
    c = d["counts"]
    assert (c["proposals"], c["manager_calls"], c["invalid"], c["ran"], c["inert"]) == (80, 80, 8, 44, 28)
    assert d["shares"]["invalid_of_calls"] == 0.1 and d["cross_instance_duplicate_groups"] == 1
    assert "value" not in json.dumps(d) and "best" not in json.dumps(d)
    stop("keys differ", J.check_diagnostics, dict(d, extra=1))
    stop("counts. keys differ", J.check_diagnostics, dict(d, counts=dict(c, best_value=0.9)))
    stop("must be num", J.check_diagnostics, dict(d, prompt_tokens={"p50": [0.5], "p95": None, "max": None}))
    stop("must be int", J.check_diagnostics, dict(d, counts=dict(c, ran=0.5)))


def stops_of(res):
    return sorted({(s["stop"], s["class"]) for s in res["stops"]}, key=str)


def test_stop_counters_from_diagnostics():
    ok = J.evaluate_stops(SPEC, [diag_campaign(wave_ledgers(SPEC, 1)), diag_audit(e5_counts(41, 4))], wave=1,
                          gpu_hours_consumed=1.0)
    assert ok["stops"] == []
    # STOP 1: from 40 audited, E5 share above 20 %; below 40 only a warning
    r = J.evaluate_stops(SPEC, [diag_campaign(wave_ledgers(SPEC, 1)), diag_audit(e5_counts(41, 9))], wave=1,
                         gpu_hours_consumed=1.0)
    assert (1, "node") in stops_of(r)
    r = J.evaluate_stops(SPEC, [diag_campaign(wave_ledgers(SPEC, 1)), diag_audit(e5_counts(39, 30))], wave=1,
                         gpu_hours_consumed=1.0)
    assert (1, "node") not in stops_of(r) and any("early warning" in w for w in r["warnings"])
    assert (9, "node") not in stops_of(r)                                  # 39 x 3 = 117 is inside 100-200
    r = J.evaluate_stops(SPEC, [diag_campaign(wave_ledgers(SPEC, 1)), diag_audit(e5_counts(30, 0))], wave=1,
                         gpu_hours_consumed=1.0)
    assert (9, "node") in stops_of(r)                                      # STOP 9 band: 30 x 3 = 90 < 100
    # STOP 3 liveness, STOP 4 invalid share and prompt overflow, STOP 7 infrastructure
    many_invalid = {k: ledger(i, invalid=tuple(range(2, 21))) for i, k in enumerate(wave_ledgers(SPEC, 1), 1)}
    assert (4, "node") in stops_of(J.evaluate_stops(SPEC, [diag_campaign(many_invalid)], wave=1, gpu_hours_consumed=0))
    refused = {k: [l.replace('"decision": "discarded"', '"decision": "not_run_refused"') for l in v]
               for k, v in wave_ledgers(SPEC, 1).items()}
    r = J.evaluate_stops(SPEC, [diag_campaign(refused)], wave=1, gpu_hours_consumed=0)
    assert stops_of(r) == [(3, "node")]                                    # ran-of-valid 4/72 after wave 1 (D4)
    big = {k: [l.replace('"prompt_tokens": 1000', '"prompt_tokens": 30000') for l in v]
           for k, v in wave_ledgers(SPEC, 1).items()}
    assert (4, "node") in stops_of(J.evaluate_stops(SPEC, [diag_campaign(big)], wave=1, gpu_hours_consumed=0))
    trunc = {k: [l.replace('"completion_tokens": 300', '"completion_tokens": 4096') for l in v]
             for k, v in wave_ledgers(SPEC, 1).items()}
    assert (4, "infrastructure") in stops_of(J.evaluate_stops(SPEC, [diag_campaign(trunc)], wave=1,
                                                              gpu_hours_consumed=0))
    infra = {k: [l.replace('"not_run_inert"', '"infrastructure_failure_final"') for l in v]
             for k, v in wave_ledgers(SPEC, 1).items()}
    assert (7, "node") in stops_of(J.evaluate_stops(SPEC, [diag_campaign(infra)], wave=1, gpu_hours_consumed=0))
    # STOP 8 (baseline timeout, campaign and audit), STOP 2 and 6 (ledger stops), STOP 9 (GPU-hours)
    bt = {"instance_1_history": [json.dumps({"schema": LS, "step": 0, "decision": "baseline_failed",
                                             "final_outcome": {"kind": "divergent", "reason": "timeout"}})]}
    assert (8, "timing") in stops_of(J.evaluate_stops(SPEC, [diag_campaign(bt)], wave=1, gpu_hours_consumed=0))
    r = J.evaluate_stops(SPEC, [diag_campaign(wave_ledgers(SPEC, 1)), diag_audit(e5_counts(41, 0, baseline=1))],
                         wave=1, gpu_hours_consumed=0)
    assert (8, "timing") in stops_of(r)
    r = J.evaluate_stops(SPEC, [diag_campaign(wave_ledgers(SPEC, 1)), diag_audit(e5_counts(41, 0, other=1))],
                         wave=1, gpu_hours_consumed=0)
    assert (6, "node") in stops_of(r) and (8, "timing") not in stops_of(r)          # m1: by reason
    for line, want in (({"decision": "stop_unisolated"}, (2, "node")), ({"decision": "stop_integrity"},
                                                                          (6, "infrastructure"))):
        led = {"instance_1_history": ledger(1)[:3] + [json.dumps({"schema": LS, "step": 3, **line})]}
        assert want in stops_of(J.evaluate_stops(SPEC, [diag_campaign(led)], wave=1, gpu_hours_consumed=0))
    assert (9, "node") in stops_of(J.evaluate_stops(SPEC, [], wave=1, gpu_hours_consumed=425.1))
    # the band is doubled under G5-MEM B (§4 item 9)
    mb = S.apply_options(SPEC, {"G5-MEM": "B"})
    assert (9, "node") in stops_of(J.evaluate_stops(mb, [diag_audit(e5_counts(41, 0))], wave=1, gpu_hours_consumed=0))


# =============================================================================================== K, access log
@pytest.fixture
def jspec(tmp_path):
    s = copy.deepcopy(SPEC)
    s["run_id"] = "c3_t1_labels_20261201"
    s["worker"].update(runs_root=str(tmp_path / "runs"), sealed_root=str(tmp_path / "sealed"),
                       base=str(tmp_path / "base"))
    for fam, c in (("G5-7", "7"), ("G5-AR", "8")):
        s["harness_families"][fam].update(g5_commit=c * 40, harness_dir=str(tmp_path / f"h{c}"))
    sp = tmp_path / "g5_spec.json"
    sp.write_text(json.dumps(s))
    return s, sp


def test_k_lock_is_table_wide(jspec):
    s, _ = jspec
    assert J.k_lock(s, 10, None)["K"] == 10 and J.k_lock(s, 10, None)["K"] == 10
    stop("K is uniform within the table", J.k_lock, s, 6, "R1-K")


def test_access_log_purposes(jspec, tmp_path):
    s, _ = jspec
    f = tmp_path / "x.tar"
    f.write_bytes(b"x")
    J.access(s, f, "audit planning: campaign ledgers of mlab_imdb wave 1")
    assert len(J.check_access_log(s)) == 1
    stop("STOP 11", J.access, s, f, "curiosity")
    log = J.run_root(s) / "_access_log.jsonl"
    log.write_text(log.read_text() + json.dumps({"who": "someone", "purpose": "audit planning: x"}) + "\n")
    stop("STOP 11", J.check_access_log, s)


# =============================================================================================== the job end to end
class Server:
    def __init__(self, up=True, props=None):
        self.up = up
        self.props = props or {"default_generation_settings": {"n_ctx": 32768}, "total_slots": 1,
                               "build_info": T4.props_build(SPEC["proposer"]["expected_build"]),
                               "model_path": SPEC["proposer"]["model_path"]}

    def __call__(self, url, timeout=10.0):
        if not self.up:
            raise ConnectionRefusedError("down")
        if url.endswith("/health"):
            return 200, b'{"status":"ok"}'
        return 200, json.dumps(self.props).encode()


class Engine:
    """Fake harness engines: campaign ledgers and audit rows as the contract in g5_job's docstring."""

    def __init__(self, spec, divergent_states=(), campaign_stop=None, row_kind=None, ledger_edit=None,
                 campaign_stop_kind=None, chunk_stop=None, chunk_stop_kind=None, rows_edit=None):
        self.spec, self.calls = spec, []
        self.divergent_states = set(divergent_states)
        self.campaign_stop = campaign_stop
        # the real engines write stop and stop_kind together (refused, deadline, integrity, unisolated, transport,
        # baseline_failed, runner, error); a stop without a kind given here is "error"
        self.campaign_stop_kind = campaign_stop_kind or ("error" if campaign_stop else None)
        self.chunk_stop, self.chunk_stop_kind = chunk_stop, chunk_stop_kind or ("error" if chunk_stop else None)
        self.rows_edit = rows_edit or (lambda rows: rows)
        self.row_kind = row_kind
        self.ledger_edit = ledger_edit or (lambda line: line)
        self.paths = []

    def __call__(self, argv, **kw):
        self.calls.append(argv)
        self.paths.append(kw.get("env", {}).get("PATH", ""))
        out = Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True)
        if "--campaign" in argv:
            f = json.loads(Path(argv[argv.index("--campaign") + 1]).read_text())
            for inst in f["instances"]:
                d = out / J.campaign_dir_name(inst)
                d.mkdir()
                (d / "campaign_ledger.jsonl").write_text(
                    "\n".join(self.ledger_edit(x) for x in ledger(inst["instance"], wave_tag=f"w{f['wave']}"))
                    + "\n")
            (out / "campaign_record.json").write_text(json.dumps({"stop": self.campaign_stop,
                                                                  "stop_kind": self.campaign_stop_kind}))
            work = out / J.campaign_dir_name(f["instances"][0]) / "runs" / "s001" / "work"
            work.mkdir(parents=True)
            (work / "model.pt").write_bytes(bytes(range(256)) * 4)          # a binary output (M1)
        else:
            chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
            label = set(S.audit_seeds(self.spec, chunk["K"])["label"])
            rows = make_rows(chunk, self.row_kind or (lambda u, st, seed: "divergent"
                                                      if st in self.divergent_states and seed in label else "ok"))
            rows = self.rows_edit(rows)
            (out / "rows.jsonl").write_text("\n".join(rows) + ("\n" if rows else ""))
            (out / "chunk_record.json").write_text(json.dumps({"stop": self.chunk_stop,
                                                               "stop_kind": self.chunk_stop_kind}))
            (out / "runs").mkdir()
            (out / "runs" / "weights.npy").write_bytes(b"\x93NUMPY\xff\xfe" * 64)
        return subprocess.CompletedProcess(argv, 0, "engine ok", "")


@pytest.fixture
def world(jspec, tmp_path, monkeypatch):
    s, sp = jspec
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path / "home" / p.lstrip("~/")))
    monkeypatch.setattr(G, "host_identity", lambda sh, h: {"host": h})
    monkeypatch.setattr(G, "ptrace_scope", lambda: 1)
    scope = app_slice(tmp_path) / "run-r1a2b.scope"     # the user manager's layout (round 2, n1)
    scope.mkdir(parents=True)
    monkeypatch.setattr(G, "scope_cgroup", lambda: {"cgroup_parent": str(scope)})
    monkeypatch.setattr(G, "harness_checkout", lambda sh, h, git=None: {"commit": sh["harness"]["commit"]})
    monkeypatch.setattr(G, "environment", lambda sh, h, n: {"name": n["env"],
                                                            "python": sh["hosts"][h]["env_python"][n["env"]]})
    monkeypatch.setattr(G, "check_affinity", lambda sh, n, affinity=None: [0])
    monkeypatch.setattr(os, "environ", dict(os.environ))
    p = s["proposer"]
    rec = {"schema": T4.SERVER_RECORD_SCHEMA, "run_id": s["run_id"], "host": "TASL-7", "hostname": p["hostname"],
           "server_url": p["server_url"], "spec_sha256": G.L._sha_file(sp), "binary_sha256": p["binary_sha256"],
           "bin_dir_manifest_sha256": p["bin_dir_manifest_sha256"], "model_sha256": T4.MODEL["sha256"],
           "build": f"version: {p['expected_build']}", "argv": T4.server_argv(s, 8095),
           "gpu": {"uuid": p["gpu_uuid"], "name": T4.GPU_MODEL}, "pid": 7, "started_utc": "2026-12-01T00:00:00Z"}
    srv = tmp_path / "server_record.json"
    srv.write_text(json.dumps(rec))

    def smi(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID2}, NVIDIA GeForce RTX 4090, 535.309.01, 24564\n", "")

    def git(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, "", "")

    def setup(h, n, base, out):
        return {"data_root": str(base / "data")}
    return {"spec": s, "sp": sp, "srv": srv, "smi": smi, "git": git, "setup": setup, "scope": scope}


def run(w, node, job, engine, *, k=10, get=None, git=None, **kw):
    ctx = {"K": k, "K_row": None if k == 10 else "R1-K-CHECK-PASS"}
    return J.run_job(w["sp"], node, job, ctx, smi=w["smi"], engine=engine, setup=w["setup"], get=get or Server(),
                     git=git or w["git"], server_record=w["srv"] if job.startswith("campaigns") else None, **kw)


def test_job_end_to_end_two_waves(world, monkeypatch):
    s = world["spec"]
    eng = Engine(s, divergent_states={"Sw11_2", "Sw12_3"})
    stop("needs campaigns-wave1 complete", run, world, "mlab_imdb", "audits-wave1", eng)
    rec = run(world, "mlab_imdb", "campaigns-wave1", eng)
    assert rec["stop"] is None and rec["attempt"] == 1 and rec["server_props_after"] == rec["server_props_before"]
    argv = eng.calls[-1]
    assert argv[2:4] == ["autoresearch.trackg.audit_g5", "campaign"] and argv[-2:] == ["--gpu-uuid", UUID2]
    assert eng.paths[-1].startswith(str(Path(argv[0]).parent) + ":")           # M2: the node env's bin first
    att = J.job_dir(s, "mlab_imdb", "campaigns-wave1") / "attempt-1"
    assert sorted(p.name for p in att.iterdir()) == ["SHA256SUMS", "attempt.json", "diagnostics.json",
                                                     "job_record.json", "out.tar"]            # out/ only in the tar
    diag = json.loads((att / "diagnostics.json").read_text())
    assert diag["counts"]["proposals"] == 80 and "value" not in json.dumps(diag)
    assert set(json.loads((att / "job_record.json").read_text())) <= J.RECORD_KEYS
    stop("is complete", run, world, "mlab_imdb", "campaigns-wave1", eng)
    stop("needs the wave-1 audits complete", run, world, "mlab_imdb", "campaigns-wave2", eng)
    monkeypatch.setattr(J, "CHUNK_LIMIT_S", 120.27 * 150)                 # several chunks
    chunks = 0
    while not J.audits_done(s, "mlab_imdb", 1):
        r = run(world, "mlab_imdb", "audits-wave1", eng)
        assert r["stop"] is None and r["K"] == 10
        chunks += 1
    assert chunks == json.loads(J.plan_path(s, "mlab_imdb", 1).read_text())["chunks"] > 1
    assert eng.calls[-1][2:4] == ["autoresearch.trackg.audit_g5", "audit"]
    last = J.complete_attempt(J.job_dir(s, "mlab_imdb", "audits-wave1", chunks - 1))[1]
    assert last["wave_e5"]["audited"] == 41 and last["wave_e5"]["divergent_label"] == 2
    assert "plan.json" not in {p.name for p in J.job_dir(s, "mlab_imdb", "audits-wave1").iterdir()}
    checks = json.loads(J.wave_checks_path(s, "mlab_imdb", 1).read_text())
    assert checks["stops"] == [] and J.wave_checks(s, "mlab_imdb", 1) == checks          # append-only
    stop("every chunk is complete", run, world, "mlab_imdb", "audits-wave1", eng)
    run(world, "mlab_imdb", "campaigns-wave2", eng)
    while not J.audits_done(s, "mlab_imdb", 2):
        run(world, "mlab_imdb", "audits-wave2", eng)
    plan2 = J.load_plan(s, "mlab_imdb", 2, "audit planning: test")
    assert plan2["carried_groups"] and plan2["reused_units"] == ["C1"]
    log = J.check_access_log(s)
    assert log and all(e["who"] == "g5_job" for e in log)
    assert J.gpu_hours_consumed(s) >= 0 and json.loads((J.run_root(s) / "_k_lock.json").read_text())["K"] == 10


def test_job_k_change_mid_table_and_node_stop(world, monkeypatch):
    s = world["spec"]
    eng = Engine(s)
    run(world, "mlab_imdb", "campaigns-wave1", eng)
    run(world, "mlab_imdb", "audits-wave1", eng)
    run(world, "mlab_cifar10", "campaigns-wave1", eng)
    stop("K is uniform within the table", run, world, "mlab_cifar10", "audits-wave1", eng, k=6)
    # a node STOP: the wave-1 E5 share above 20 % from 41 audited STOPs the node before wave 2
    eng2 = Engine(s, divergent_states={f"Sw1{i}_{n}" for i in range(1, 5) for n in (2, 3, 6)})
    run(world, "mlab_ogbn_arxiv", "campaigns-wave1", eng2)
    while not J.audits_done(s, "mlab_ogbn_arxiv", 1):
        run(world, "mlab_ogbn_arxiv", "audits-wave1", eng2)
    stop("STOP", run, world, "mlab_ogbn_arxiv", "campaigns-wave2", eng2)
    assert J.node_stopped(J.run_root(s) / "mlab_ogbn_arxiv")


def test_job_stops_and_refusals(world):
    s = world["spec"]
    stop("STOP 12|/props", run, world, "mlab_imdb", "campaigns-wave1", Engine(s),
         get=Server(props=Server().props | {"total_slots": 2}))
    assert not J.job_dir(s, "mlab_imdb", "campaigns-wave1").exists()           # refused before an attempt
    eng = Engine(s, campaign_stop="RuntimeError: unexpected at seed 7006 metric 0.81")
    stop("campaign engine", run, world, "mlab_imdb", "campaigns-wave1", eng)
    att = J.job_dir(s, "mlab_imdb", "campaigns-wave1") / "attempt-1"
    rec = json.loads((att / "job_record.json").read_text())
    assert rec["stop_class"] == "infrastructure"
    for clear in att.rglob("*.json"):                  # the engine's own stop text stays sealed (review n1)
        assert "7006" not in clear.read_text() and "0.81" not in clear.read_text(), clear
    assert J.ENGINE_STOP_CAMPAIGN in rec["stop"]
    assert run(world, "mlab_imdb", "campaigns-wave1", Engine(s))["attempt"] == 2      # infrastructure: new attempt
    stop("server_record", J.run_job, world["sp"], "mlab_cifar10", "campaigns-wave1", {"K": 10}, smi=world["smi"],
         engine=Engine(s), setup=world["setup"], get=Server(), git=world["git"])

    def no_engines(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, "", "")
    stop("has no src/autoresearch/trackg/audit_g5.py carrying", run, world, "mlab_cifar10", "campaigns-wave1", Engine(s), git=no_engines)


def test_gpuh_b_audits_need_the_server_stopped(world):
    s = S.apply_options(world["spec"], {"G5-TASL-GPUH": "B"})
    world["sp"].write_text(json.dumps(s))
    rec = json.loads(world["srv"].read_text())                 # the server record binds the spec's sha256
    world["srv"].write_text(json.dumps(rec | {"spec_sha256": G.L._sha_file(world["sp"])}))
    eng = Engine(s)
    run(world, "mlab_imdb", "campaigns-wave1", eng)
    stop("stopped during the audits", run, world, "mlab_imdb", "audits-wave1", eng, get=Server(up=True))
    # part 3b-2 (3b-1 review ruling 2): the server's span is registered before an audit job under B
    stop("span of the server", run, world, "mlab_imdb", "audits-wave1", eng, get=Server(up=False))
    sha = G.L._sha_file(world["srv"])
    receipt = world["srv"].parent / "receipt.json"
    receipt.write_text(json.dumps({"schema": J.SE.SERVER_RECEIPT_SCHEMA, "run_id": s["run_id"], "server": "server-1",
                                   "server_record_sha256": sha, "started_utc": "2026-12-01T00:00:00Z",
                                   "stopped_utc": "2026-12-01T02:00:00Z", "span_seconds": 7200.0}))
    J.SE.register_server_span(s, receipt)
    rec = run(world, "mlab_imdb", "audits-wave1", eng, get=Server(up=False))
    assert rec["server_stopped"]["reachable"] is False


def test_autoresearch_job_uses_the_record_environment(world):
    s = world["spec"]
    eng = Engine(s)
    env = {"name": "ar-cond7a", "freeze": "sweep2/g1b/env/ar-cond7a.freeze.txt",
           "sha256": SPEC["ar_prerequisites"]["proposed_environment"]["sha256"], "python": "3.12.15",
           "interpreter": "/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python"}
    stop("not resolved", J.run_job, world["sp"], J.S.AR, "campaigns-wave1", {"K": 10}, smi=world["smi"],
         engine=eng, setup=world["setup"], get=Server(), git=world["git"], server_record=world["srv"])
    rec = J.run_job(world["sp"], J.S.AR, "campaigns-wave1", {"K": 10, "ar_environment": env}, smi=world["smi"],
                    engine=eng, setup=world["setup"], get=Server(), git=world["git"], server_record=world["srv"])
    assert rec["environment"]["python"] == env["interpreter"]
    assert eng.calls[-1][0] == env["interpreter"] and "h8" in eng.calls[-1][eng.calls[-1].index("--harness-root") + 1]


def test_serve_launch_is_behind_the_note_and_keys(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(S, "validate_spec", lambda spec, launch=False: {})
    monkeypatch.setattr(S, "check_note", lambda *a, **k: {})
    sp = tmp_path / "s.json"
    sp.write_text(json.dumps(SPEC))
    monkeypatch.delenv(S.ENABLE_ENV, raising=False)
    stop("disabled", J.serve_launch, sp, tmp_path / "n.md", enable=True, server=lambda *a: calls.append(a) or {})
    monkeypatch.setenv(S.ENABLE_ENV, "1")
    out = J.serve_launch(sp, tmp_path / "n.md", enable=True, server=lambda spec, p: calls.append(p) or {"ok": 1},
                         launch_binding=lambda repo, s, rows: {"rows": rows})
    assert out["ok"] == 1 and calls == [sp] and out["launch"]["rows"] == S.PLAN_ROWS


def test_engine_contract_and_wrapper(tmp_path):
    c = J.engine_contract()
    assert c["file"] == "src/autoresearch/trackg/audit_g5.py" and c["file"] in S.G5_TRACKG_ADDITIONS
    assert c["subcommands"] == {"campaign": "campaign", "audit": "audit"} and c["infrastructure_reruns"] == 2
    assert c["truncation_invalid_in"] == "autoresearch.trackg.audit_g5.TruncationInvalidManager"     # §7 item 5
    assert "manager_v2_diff.py" in S.ENGINE_FILES                       # still an engine file for P5
    seen = []

    def git(argv, **kw):                        # m3: the marker and both schemas must be in audit_g5.py
        seen.append(argv[argv.index("-e") + 1])
        return subprocess.CompletedProcess(argv, 0 if argv[argv.index("-e") + 1] != J.CHUNK_SCHEMA else 1, "", "")
    stop("trackg_g5_audit_chunk/v1", J.check_engines, tmp_path, "7" * 40, git=git)
    assert seen[0] == J.ENGINE_CONTRACT
    seen.clear()

    def git_no_class(argv, **kw):              # the truncation class the contract names must be in audit_g5.py too
        seen.append(argv[argv.index("-e") + 1])
        return subprocess.CompletedProcess(argv, 1 if seen[-1] == J.TRUNCATION_NEEDLE else 0, "", "")
    stop("class TruncationInvalidManager", J.check_engines, tmp_path, "7" * 40, git=git_no_class)
    assert seen == [J.ENGINE_CONTRACT, J.CAMPAIGN_SCHEMA, J.CHUNK_SCHEMA, "class TruncationInvalidManager("]
    script = (ROOT / "sweep2" / "t1_tasl" / "t1_tasl_node.sh").read_text()
    assert "g5)  SCRIPT=g5_tasl.py" in script and "G5_TASL_NODE_LOG" in script
    res = subprocess.run(["bash", str(ROOT / "sweep2" / "t1_tasl" / "t1_tasl_node.sh"), "g5", "s.json", "n", "note",
                          "wave3", "-"], capture_output=True, text=True)
    assert res.returncode == 2 and "needs the job" in res.stderr


# =============================================================================================== review round 1
def _audit_diag_for(rows_kind, tmp_path, name):
    plan = small_plan()
    plan["chunks"] = 2                                    # not the last chunk: no wave E5 here
    node = S.node_entry(SPEC, "mlab_imdb")
    chunk = J.audit_chunk_file(SPEC, node, plan, 0, J.chunk_plan(plan, {"run_seconds": 1})[0], interpreter="/py",
                               cgroup_parent="/cg", deadline_epoch=1.0)
    out = tmp_path / name
    out.mkdir()
    (out / "rows.jsonl").write_text("\n".join(make_rows(chunk, rows_kind)) + "\n")
    (out / "chunk_record.json").write_text(json.dumps({"stop": None}))
    rec = {"spec_sha256": "s", "attempt": 1, "chunk": 0, "K": 10, "plan_sha256": "p"}
    return J.check_diagnostics(J.audit_diagnostics(SPEC, node, 1, rec, plan, 0, chunk, out) | {"gpu_seconds": 1.0})


def test_b1_no_evaluation_seed_outcome_in_clear_diagnostics(tmp_path):
    """The clear audit diagnostics are identical whatever happens on the evaluation seeds, so no combination of their
    fields gives an evaluation-seed outcome count."""
    ev = set(S.audit_seeds(SPEC, 10)["evaluation"])
    base = _audit_diag_for(lambda u, st, seed: "ok", tmp_path, "a")
    for name, kind in (("b", lambda u, st, seed: "divergent" if seed in ev else "ok"),
                       ("c", lambda u, st, seed: "divergent" if seed in ev and st != "B" else "ok")):
        assert _audit_diag_for(kind, tmp_path, name) == base
    assert base["runs_planned_evaluation"] == base["runs_planned_label"] and base["label_seed_runs"]["ok"] == \
        base["runs_planned_label"]
    lab = set(S.audit_seeds(SPEC, 10)["label"])
    d = _audit_diag_for(lambda u, st, seed: "divergent" if seed in lab and st == "C1" else "ok", tmp_path, "d")
    assert d["label_seed_runs"]["divergent"] == 5                      # label-seed outcomes are counted


def test_m4_infrastructure_rows_are_stop_7(world, tmp_path):
    plan = small_plan()
    chunk = J.audit_chunk_file(SPEC, S.node_entry(SPEC, "mlab_imdb"), plan, 0,
                               J.chunk_plan(plan, {"run_seconds": 1})[0], interpreter="/py", cgroup_parent="/cg",
                               deadline_epoch=1.0)
    rows = [json.loads(x) for x in make_rows(chunk)]
    rows[0] = {"schema": J.ROW_SCHEMA, "unit": rows[0]["unit"], "seed": rows[0]["seed"], "executed": False,
               "outcome": {"kind": "infrastructure_failure", "reason": "launch"}}      # no isolation block
    got = J.read_rows([json.dumps(r) for r in rows], chunk)
    assert got[0]["kind"] == "infrastructure_failure"
    s = world["spec"]
    run(world, "mlab_imdb", "campaigns-wave1", Engine(s))
    eng = Engine(s, row_kind=lambda u, st, seed: "infrastructure_failure" if st == "C1" and seed == 7001 else "ok")
    stop("STOP 7", run, world, "mlab_imdb", "audits-wave1", eng)
    rec = json.loads((J.job_dir(s, "mlab_imdb", "audits-wave1", 0) / "attempt-1" / "job_record.json").read_text())
    assert rec["stop_class"] == "infrastructure"
    assert run(world, "mlab_imdb", "audits-wave1", Engine(s))["attempt"] == 2       # a new attempt


def test_m3_timing_and_cache_prompt_stops(world):
    s = world["spec"]
    slow = Engine(s, ledger_edit=lambda x: x.replace(f'"elapsed_seconds_info_only": {RUN_S}',
                                                     '"elapsed_seconds_info_only": 100.0'))     # > 65.156 s basis
    stop("timing STOP", run, world, "mlab_imdb", "campaigns-wave1", slow)
    att = J.job_dir(s, "mlab_imdb", "campaigns-wave1") / "attempt-1"
    rec, diag = (json.loads((att / n).read_text()) for n in ("job_record.json", "diagnostics.json"))
    assert rec["stop_class"] == "timing" and diag["checks"]["run_median_over_basis"] == 1
    assert "100" not in json.dumps(diag["checks"]) and "median" not in json.dumps(diag["shares"])
    cache = Engine(s, ledger_edit=lambda x: x.replace('"cache_prompt": false', '"cache_prompt": true'))
    stop("cache_prompt: false", run, world, "mlab_cifar10", "campaigns-wave1", cache)
    rec = json.loads((J.job_dir(s, "mlab_cifar10", "campaigns-wave1") / "attempt-1" / "job_record.json").read_text())
    assert rec["stop_class"] == "infrastructure"


def test_m6_meter_counts_the_proposer_card_under_gpuh_b(jspec):
    """Under G5-TASL-GPUH B the proposer card counts from TASL-7's server spans (part 3b-2, replacing 3b-1's
    campaign-wall-time lower bound): a registered span, or an open span until now for a server without one."""
    s, _ = jspec
    start = "2026-12-01T00:00:00Z"
    t0 = J.SE.parse_utc(start)
    for job, secs in (("campaigns-wave1", 3600.0), ("audits-wave1", 3600.0)):
        d = J.run_root(s) / "mlab_imdb" / job / "attempt-1"
        d.mkdir(parents=True)
        rec = {"schema": J.RECORD_SCHEMA, "job": job, "gpu_seconds": secs}
        if job.startswith("campaigns"):
            rec["server_record"] = {"sha256": "a" * 64, "pid": 7, "started_utc": start}
        (d / "job_record.json").write_text(json.dumps(rec))
    b = S.apply_options(s, {"G5-TASL-GPUH": "B"})
    assert J.gpu_hours_consumed(s) == 2.0                                   # A: the worker card only
    assert J.gpu_hours_consumed(b, now=lambda: t0 + 3 * 3600) == 5.0       # B: open span of 3 h until now
    receipt = J.run_root(s).parent / "r.json"
    receipt.write_text(json.dumps({"schema": J.SE.SERVER_RECEIPT_SCHEMA, "run_id": s["run_id"], "server": "server-1",
                                   "server_record_sha256": "a" * 64, "started_utc": start,
                                   "stopped_utc": "2026-12-01T01:30:00Z", "span_seconds": 5400.0}))
    J.SE.register_server_span(b, receipt)
    assert J.gpu_hours_consumed(b, now=lambda: t0 + 99 * 3600) == 3.5      # B: the registered span, 1.5 h


def test_m7_close_attempt(world, monkeypatch):
    s, sp = world["spec"], world["sp"]
    n, d = G.next_attempt(J.job_dir(s, "mlab_imdb", "campaigns-wave1"))
    owner = json.loads((d / "attempt.json").read_text())
    start = J.datetime.strptime(owner["started_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=J.timezone.utc).timestamp()
    stop("still name", J.close_attempt, s, sp, "mlab_imdb", "campaigns-wave1", d, "OOM kill in the scope",
         scan=lambda p: [99])
    stop("still alive", J.close_attempt, s, sp, "mlab_imdb", "campaigns-wave1", d, "OOM kill in the scope",
         scan=lambda p: [])
    stop("reason", J.close_attempt, s, sp, "mlab_imdb", "campaigns-wave1", d, "short", scan=lambda p: [],
         alive=lambda pid: False)
    stop("not an attempt of", J.close_attempt, s, sp, "mlab_cifar10", "campaigns-wave1", d,
         "OOM kill in the scope", scan=lambda p: [], alive=lambda pid: False)
    stop("with its chunk", J.close_attempt, s, sp, "mlab_imdb", "audits-wave1", d, "OOM kill in the scope",
         scan=lambda p: [], alive=lambda pid: False)
    (d / "out").mkdir()
    (d / "out" / "partial.log").write_text("engine output before the crash")
    for p in (d / "out" / "partial.log", d / "out", d / "attempt.json", d):
        os.utime(p, (start + 3600.0, start + 3600.0))                    # the last write, 1 h after the start
    rec = J.close_attempt(s, sp, "mlab_imdb", "campaigns-wave1", d, "OOM kill in the scope", scan=lambda p: [],
                          alive=lambda pid: False, now=lambda: start + 7200.0)
    assert rec["schema"] == J.RECORD_SCHEMA and rec["stop_class"] == "infrastructure"
    assert rec["gpu_seconds"] == 7200.0 and rec["end_basis"] == "closed"     # metered to the closing (3b-2 M4)
    assert rec["gpu_seconds_to_latest_mtime"] == 3600.0 and rec["closed_utc"] > rec["latest_mtime_utc"]   # for C9
    assert J.gpu_hours_consumed(s) == 2.0                                 # counted on the meter
    stop("without a job record", J.close_attempt, s, sp, "mlab_imdb", "campaigns-wave1", d, "OOM kill in the scope",
         scan=lambda p: [], alive=lambda pid: False)
    assert run(world, "mlab_imdb", "campaigns-wave1", Engine(s))["attempt"] == 2
    cd = J.job_dir(s, "mlab_imdb", "audits-wave1", 0)
    _, a = G.next_attempt(cd)
    assert J.close_attempt(s, sp, "mlab_imdb", "audits-wave1", a, "host rebooted mid-chunk", chunk=0,
                           scan=lambda p: [], alive=lambda pid: False)["chunk"] == 0


def test_minors_k_lock_deadline_props_after_tar_and_refusals(world, monkeypatch):
    s = world["spec"]
    # refusals before the lease are recorded (m7)
    stop("needs campaigns-wave1 complete", run, world, "mlab_imdb", "audits-wave1", Engine(s))
    assert list((J.run_root(s) / "_refusals").iterdir())
    run(world, "mlab_imdb", "campaigns-wave1", Engine(s))

    def no_engine(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, "", "")
    stop("has no src/autoresearch/trackg/audit_g5.py", run, world, "mlab_imdb", "audits-wave1", Engine(s),
         git=no_engine)
    assert not (J.run_root(s) / "_k_lock.json").exists()                 # m2: a refused audit does not fix K
    # STOP 9 past the deadline is a node STOP (m5)
    def timeout(argv, **kw):
        raise subprocess.TimeoutExpired(argv, 1, output="o", stderr="e")
    stop("STOP 9: the engine reached the job deadline", run, world, "mlab_cifar10", "campaigns-wave1", timeout)
    rec = json.loads((J.job_dir(s, "mlab_cifar10", "campaigns-wave1") / "attempt-1" / "job_record.json").read_text())
    assert rec["stop_class"] == "node"
    # STOP 12: /props the same before, changed after the wave
    class Flip(Server):
        n = 0

        def __call__(self, url, timeout=10.0):
            if url.endswith("/props"):
                Flip.n += 1
                if Flip.n > 1:
                    return 200, json.dumps(self.props | {"total_slots": 2}).encode()
            return super().__call__(url, timeout)
    stop("STOP 12", run, world, "mlab_ogbn_arxiv", "campaigns-wave1", Engine(s), get=Flip())
    rec = json.loads((J.job_dir(s, "mlab_ogbn_arxiv", "campaigns-wave1") / "attempt-1" / "job_record.json")
                     .read_text())
    assert rec["stop_class"] == "infrastructure"
    # a tar failure keeps out/ for the seal and STOPs
    monkeypatch.setattr(J, "make_tar", lambda d: False)
    stop("out.tar could not be written", run, world, "mlgym_cifar10", "campaigns-wave1", Engine(s))
    att = J.job_dir(s, "mlgym_cifar10", "campaigns-wave1") / "attempt-1"
    assert (att / "out").is_dir() and not (att / "out.tar").exists()


# =============================================================================================== G.5 follow-ups
def _chunk():
    plan = small_plan()
    chunk = J.audit_chunk_file(SPEC, S.node_entry(SPEC, "mlab_imdb"), plan, 0,
                               J.chunk_plan(plan, {"run_seconds": 1})[0], interpreter="/py", cgroup_parent="/cg",
                               deadline_epoch=1.0)
    return plan, chunk


def test_followup_1_read_rows_needs_every_gate_field(tmp_path):
    """Harness report §7 item 1 (review m1): a gate refusal on log_intact, parent_traced_by or
    parent_dumpable_at_accept alone, or any row carrying gate_refusal, is STOP 2 (node class), not missing rows."""
    plan, chunk = _chunk()
    rows = make_rows(chunk)
    assert len(J.read_rows(rows, chunk)) == len(chunk["runs"])
    first = json.loads(rows[0])
    for change in ({"isolation": dict(ISOLATED, log_intact=False)},
                   {"isolation": {k: v for k, v in ISOLATED.items() if k != "log_intact"}},
                   {"isolation": dict(ISOLATED, parent_traced_by=4242)},
                   {"isolation": dict(ISOLATED, parent_dumpable_at_accept=True)},
                   {"gate_refusal": "run u000_s7001_a0: not effectively isolated (log_intact=False)"},
                   {"outcome": {"kind": "divergent", "reason": "log_tampered"},
                    "gate_refusal": "run u000_s7001_a0: not effectively isolated"}):
        stop("STOP 2", J.read_rows, [json.dumps(first | change)] + rows[1:], chunk)
    # infrastructure rows: an executed one carries its isolation block and must pass it; one that never executed
    # (a host refusal on every attempt) has none and keeps its path to STOP 7
    infra = {"outcome": {"kind": "infrastructure_failure", "reason": "killed"}}
    assert J.read_rows([json.dumps(first | infra)] + rows[1:], chunk)[0]["kind"] == "infrastructure_failure"
    stop("STOP 2", J.read_rows, [json.dumps(first | infra | {"isolation": dict(ISOLATED, log_intact=False)})]
         + rows[1:], chunk)
    stop("STOP 2", J.read_rows, [json.dumps({k: v for k, v in first.items() if k != "isolation"} | infra)]
         + rows[1:], chunk)
    never = {"schema": J.ROW_SCHEMA, "unit": first["unit"], "seed": first["seed"], "executed": False,
             "code_state_sha256": None, "outcome": {"kind": "infrastructure_failure", "reason": "runner_error"}}
    assert J.read_rows([json.dumps(never)] + rows[1:], chunk)[0]["kind"] == "infrastructure_failure"
    stop("STOP 2", J.read_rows, [json.dumps(never | {"gate_refusal": "x"})] + rows[1:], chunk)
    # in the job's diagnostics the class is node
    out = tmp_path / "a"
    out.mkdir()
    (out / "rows.jsonl").write_text(json.dumps(first | {"isolation": dict(ISOLATED, log_intact=False)}) + "\n")
    (out / "chunk_record.json").write_text(json.dumps({"stop": "G5EngineStop: STOP: stop_unisolated: run 1 failed "
                                                               "the record gate", "stop_kind": "unisolated"}))
    rec = {"spec_sha256": "s", "attempt": 1, "chunk": 0, "K": 10, "plan_sha256": "p"}
    plan["chunks"] = 2
    d = J.audit_diagnostics(SPEC, S.node_entry(SPEC, "mlab_imdb"), 1, rec, plan, 0, chunk, out)
    assert d["stop"].startswith("STOP 2: audit run") and d["stop_class"] == "node"


def _audit_diag(tmp_path, name, rows, crec, plan, chunk):
    out = tmp_path / name
    out.mkdir()
    (out / "rows.jsonl").write_text("".join(r + "\n" for r in rows))
    (out / "chunk_record.json").write_text(json.dumps(crec))
    rec = {"spec_sha256": "s", "attempt": 1, "chunk": 0, "K": 10, "plan_sha256": "p"}
    return J.check_diagnostics(J.audit_diagnostics(SPEC, S.node_entry(SPEC, "mlab_imdb"), 1, rec, plan, 0, chunk, out)
                               | {"gpu_seconds": 1.0})


def test_followup_2_audit_stop_kind_classes(tmp_path):
    """Harness report §7 item 2: stop_kind deadline is node-class STOP 9 before the missing-rows check; unisolated
    (a gate refusal on an infrastructure outcome writes no row) is STOP 2; other kinds stay infrastructure; the
    engine's own text never reaches the clear diagnostics."""
    plan, chunk = _chunk()
    plan["chunks"] = 2
    rows = make_rows(chunk)
    sealed = "G5EngineStop: STOP: deadline: run 3 of 9 could not finish (seed 7777 metric 0.8125)"
    for i, (kind, n_rows, want, cls) in enumerate((
            ("deadline", 2, "STOP 9: the audit engine stopped at the job deadline", "node"),
            ("deadline", 0, "STOP 9: the audit engine stopped at the job deadline", "node"),
            ("unisolated", 2, "STOP 2: the audit engine stopped on the isolation gate", "node"),
            ("integrity", 0, "planned audit runs have no row", "infrastructure"),
            ("runner", 2, "planned audit runs have no row", "infrastructure"),
            ("refused", 0, "planned audit runs have no row", "infrastructure"))):
        d = _audit_diag(tmp_path, f"k{i}", rows[:n_rows], {"stop": sealed, "stop_kind": kind}, plan, chunk)
        assert want in d["stop"] and d["stop_class"] == cls, (kind, d["stop"])
        assert "7777" not in json.dumps(d) and "0.8125" not in json.dumps(d)
    # all rows present: the kind still decides the class (node before STOP 7, infrastructure after it)
    d = _audit_diag(tmp_path, "full-int", rows, {"stop": sealed, "stop_kind": "integrity"}, plan, chunk)
    assert d["stop"].startswith("STOP 6: the audit engine stopped on an integrity check") and \
        d["stop_class"] == "infrastructure"
    d = _audit_diag(tmp_path, "full-err", rows, {"stop": sealed, "stop_kind": "error"}, plan, chunk)
    assert (d["stop"], d["stop_class"]) == (J.ENGINE_STOP_AUDIT, "infrastructure")
    d = _audit_diag(tmp_path, "full-nokind", rows, {"stop": sealed}, plan, chunk)            # an engine without it
    assert (d["stop"], d["stop_class"]) == (J.ENGINE_STOP_AUDIT, "infrastructure")
    d = _audit_diag(tmp_path, "unknown", rows, {"stop": sealed, "stop_kind": "seed 7777"}, plan, chunk)
    assert (d["stop"], d["stop_class"]) == (J.ENGINE_STOP_AUDIT, "infrastructure") and "7777" not in json.dumps(d)
    infra = [json.dumps(json.loads(rows[0]) | {"outcome": {"kind": "infrastructure_failure", "reason": "killed"}})]
    d = _audit_diag(tmp_path, "infra-dl", infra + rows[1:], {"stop": sealed, "stop_kind": "deadline"}, plan, chunk)
    assert d["stop"].startswith("STOP 9") and d["stop_class"] == "node"
    d = _audit_diag(tmp_path, "infra-err", infra + rows[1:], {"stop": sealed, "stop_kind": "error"}, plan, chunk)
    assert d["stop"].startswith("STOP 7") and d["stop_class"] == "infrastructure"
    d = _audit_diag(tmp_path, "clean", rows, {"stop": None, "stop_kind": None}, plan, chunk)
    assert d["stop"] is None
    # a node-class row STOP keeps its own reason under a deadline
    bad = json.loads(rows[0]) | {"seed": 9001}
    d = _audit_diag(tmp_path, "s10", [json.dumps(bad)], {"stop": sealed, "stop_kind": "deadline"}, plan, chunk)
    assert d["stop"].startswith("STOP 10") and d["stop_class"] == "node"


def test_followup_2_campaign_stop_kind_classes(world, tmp_path):
    """stop_kind deadline in campaign_record.json is node-class STOP 9 before the ledger-set and proposal-count
    checks (and before the infrastructure-class cache_prompt check); transport and integrity are STOP 6,
    infrastructure; refused, runner and error keep the generic reason."""
    s = world["spec"]
    node = S.node_entry(s, "mlab_imdb")
    rec = {"spec_sha256": "s", "attempt": 1}
    want = [J.campaign_dir_name(i) for i in J.wave_instances(s, 1)]
    sealed = "G5EngineStop: STOP: deadline: reached before instance 3 (seed 5103)"

    def diag(name, crec, n_ledgers=4, steps=20, edit=lambda x: x):
        out = tmp_path / name
        for label in want[:n_ledgers]:
            (out / label).mkdir(parents=True)
            k = int(label.split("_")[1])
            (out / label / "campaign_ledger.jsonl").write_text(
                "\n".join(edit(x) for x in ledger(k, wave_tag="w1", steps=steps)) + "\n")
        out.mkdir(exist_ok=True)
        (out / "campaign_record.json").write_text(json.dumps(crec))
        return J.check_diagnostics(J.campaign_diagnostics(s, node, 1, rec, out) | {"gpu_seconds": 1.0})
    for i, (crec, n, steps) in enumerate((({"stop": sealed, "stop_kind": "deadline"}, 2, 20),
                                          ({"stop": sealed, "stop_kind": "deadline"}, 4, 7),
                                          ({"stop": sealed, "stop_kind": "deadline"}, 0, 20))):
        d = diag(f"dl{i}", crec, n, steps)
        assert d["stop"].startswith("STOP 9: the campaign engine stopped at the job deadline") and "(stop_kind deadline;" in d["stop"]
        assert d["stop_class"] == "node" and "5103" not in json.dumps(d)
    cache = diag("dl-cache", {"stop": sealed, "stop_kind": "deadline"}, 2,
                 edit=lambda x: x.replace('"cache_prompt": false', '"cache_prompt": true'))
    assert cache["stop"].startswith("STOP 9") and cache["stop_class"] == "node"
    for kind, start, cls in (("transport", "STOP 6: the campaign engine stopped on the proposer transport",
                              "infrastructure"),
                             ("integrity", "STOP 6: the campaign engine stopped on an integrity check",
                              "infrastructure"),
                             ("refused", J.ENGINE_STOP_CAMPAIGN, "infrastructure"),
                             ("runner", J.ENGINE_STOP_CAMPAIGN, "infrastructure"),
                             ("error", J.ENGINE_STOP_CAMPAIGN, "infrastructure")):
        d = diag(f"k-{kind}", {"stop": sealed, "stop_kind": kind})
        assert d["stop"].startswith(start) and d["stop_class"] == cls, (kind, d["stop"])
    assert diag("short-nokind", {"stop": None, "stop_kind": None}, 4, 7)["stop"].startswith("STOP: 28 proposals")
    assert diag("clean", {"stop": None, "stop_kind": None})["stop"] is None
    # the job end to end: a deadline stop is a node STOP on record (the author decides; no new attempt)
    eng = Engine(s, campaign_stop=sealed, campaign_stop_kind="deadline")
    stop("STOP 9: the campaign engine stopped at the job deadline", run, world, "mlab_imdb", "campaigns-wave1", eng)
    att = J.job_dir(s, "mlab_imdb", "campaigns-wave1") / "attempt-1"
    jrec = json.loads((att / "job_record.json").read_text())
    assert jrec["stop_class"] == "node" and J.node_stopped(J.run_root(s) / "mlab_imdb")
    assert "5103" not in (att / "job_record.json").read_text() + (att / "diagnostics.json").read_text()


def test_followup_2_audit_deadline_through_the_job(world):
    s = world["spec"]
    run(world, "mlab_imdb", "campaigns-wave1", Engine(s))
    eng = Engine(s, chunk_stop="G5EngineStop: STOP: deadline: run 3 of 40 could not finish", chunk_stop_kind="deadline",
                 rows_edit=lambda rows: rows[:2])
    stop("STOP 9: the audit engine stopped at the job deadline", run, world, "mlab_imdb", "audits-wave1", eng)
    jrec = json.loads((J.job_dir(s, "mlab_imdb", "audits-wave1", 0) / "attempt-1" / "job_record.json").read_text())
    assert jrec["stop_class"] == "node"
    stop("has a STOP on record", run, world, "mlab_imdb", "audits-wave1", Engine(s))      # not retried


def app_slice(root):
    """A fake ``user@<uid>.service/app.slice`` under ``root`` (the start-of-job scan reads only that subtree)."""
    return Path(root) / "user.slice" / f"user-{os.getuid()}.slice" / f"user@{os.getuid()}.service" / "app.slice"


def _cg(scope, name, populated, procs=""):
    d = scope / name
    d.mkdir(parents=True)
    (d / "cgroup.kill").write_text("")
    (d / "cgroup.procs").write_text(procs)
    (d / "cgroup.events").write_text(f"populated {int(populated)}\nfrozen 0\n")
    return d


def test_followup_3_kill_run_cgroups_with_fakes(tmp_path):
    """Harness report §7 item 3: cgroup.kill on every ar_* child of the scope (SIGKILL of each process as the
    fallback), a wait, then every ar_* child that still holds a process; other children are never touched."""
    scope = tmp_path / "scope"
    a = _cg(scope, "ar_u000_s7001_a0_11_22", True, "4242\n")
    b = _cg(scope, "ar_u001_s7002_a0_11_33", False)
    other = _cg(scope, "not_a_run", True, "77\n")
    kills = []

    def sleep(_):                                         # the kernel empties the cgroup after the kill
        (a / "cgroup.events").write_text("populated 0\nfrozen 0\n")
    res = J.kill_run_cgroups(scope, sleep=sleep, signal_pid=lambda pid, sig: kills.append((pid, sig)))
    assert res["left"] == [] and res["run_cgroups"] == [a.name, b.name]
    assert (a / "cgroup.kill").read_text() == "1" == (b / "cgroup.kill").read_text()
    assert (other / "cgroup.kill").read_text() == "" and kills == [(4242, J.signal.SIGKILL)]
    # a process that survives: listed after the grace (fake clock), with a nested child cgroup's process
    scope2 = tmp_path / "scope2"
    c = _cg(scope2, "ar_u002_s7003_a1_11_44", True, "")
    (c / "sandbox").mkdir()
    (c / "sandbox" / "cgroup.procs").write_text("5151\n")
    t = [0.0]
    kills.clear()
    res = J.kill_run_cgroups(scope2, grace=1.0, sleep=lambda _: t.__setitem__(0, t[0] + 0.5),
                             monotonic=lambda: t[0], signal_pid=lambda pid, sig: kills.append(pid))
    assert res["left"] == [c.name] and set(kills) == {5151}
    # no cgroup.kill writable: SIGKILL each process, as RunCgroup.kill does
    scope3 = tmp_path / "scope3"
    d = _cg(scope3, "ar_x", True, "6161\n")
    (d / "cgroup.kill").unlink()
    (d / "cgroup.kill").symlink_to(tmp_path / "no" / "such" / "dir")   # writing it fails with an OSError
    kills.clear()

    def sleep3(_):
        (d / "cgroup.events").write_text("populated 0\n")
    res = J.kill_run_cgroups(scope3, sleep=sleep3, signal_pid=lambda pid, sig: kills.append(pid))
    assert res["methods"] == {"ar_x": "sigkill_each"} and kills == [6161] and res["left"] == []
    # a scope that cannot be read is not verified
    assert J.kill_run_cgroups(tmp_path / "missing")["left"] is None
    empty = tmp_path / "scope4"
    empty.mkdir()
    assert J.kill_run_cgroups(empty) == {"cgroup_parent": str(empty), "run_cgroups": [], "methods": {}, "left": []}


def test_followup_3_timeout_kills_run_cgroups_before_the_tar(world, monkeypatch):
    import functools
    s, scope = world["spec"], world["scope"]
    kills, seen, made = [], {}, {}

    def timeout(argv, **kw):                  # the engine's runner has a run in flight when the job kills the engine
        out = Path(argv[argv.index("--out") + 1])
        (out / "instance_1_history").mkdir(parents=True)
        made["ar"] = _cg(scope, "ar_s001_a0_9_9", True, "4242\n")
        raise subprocess.TimeoutExpired(argv, 1, output="o", stderr="e")

    def flip(_):
        (made["ar"] / "cgroup.events").write_text("populated 0\n")
    real_tar = J.make_tar

    def tar(d):
        seen["kill_at_tar"] = (made["ar"] / "cgroup.kill").read_text()
        return real_tar(d)
    monkeypatch.setattr(J, "make_tar", tar)
    killer = functools.partial(J.kill_run_cgroups, sleep=flip, signal_pid=lambda pid, sig: kills.append(pid))
    stop("STOP 9: the engine reached the job deadline; its ar_\\* run cgroups were killed", run, world, "mlab_cifar10",
         "campaigns-wave1", timeout, kill_cgroups=killer)
    assert seen["kill_at_tar"] == "1" and kills == [4242]                       # killed before the tar
    att = J.job_dir(s, "mlab_cifar10", "campaigns-wave1") / "attempt-1"
    rec = json.loads((att / "job_record.json").read_text())
    assert rec["stop_class"] == "node" and (att / "out.tar").is_file() and not (att / "out").exists()
    with tarfile.open(att / "out.tar") as t:
        killed = json.loads(t.extractfile("out/run_cgroups_kill.json").read())
    assert killed["left"] == [] and killed["run_cgroups"] == [made["ar"].name]
    # a run cgroup that keeps a process: STOP, node class, out/ kept untarred for the seal, the operator rule stated
    t0 = [0.0]
    stuck = functools.partial(J.kill_run_cgroups, grace=1.0, sleep=lambda _: t0.__setitem__(0, t0[0] + 0.5),
                              monotonic=lambda: t0[0], signal_pid=lambda pid, sig: None)

    def timeout2(argv, **kw):
        made["ar2"] = _cg(scope, "ar_s002_a0_9_9", True, "5151\n")
        raise subprocess.TimeoutExpired(argv, 1, output="o", stderr="e")
    stop("still hold processes", run, world, "mlab_ogbn_arxiv", "campaigns-wave1", timeout2, kill_cgroups=stuck)
    att = J.job_dir(s, "mlab_ogbn_arxiv", "campaigns-wave1") / "attempt-1"
    rec = json.loads((att / "job_record.json").read_text())
    assert rec["stop_class"] == "node" and "out_tar_sha256" not in rec and "operator rule" in rec["stop"]
    assert (att / "out").is_dir() and not (att / "out.tar").exists()
    assert json.loads((att / "out" / "run_cgroups_kill.json").read_text())["left"] == [made["ar2"].name]
    assert subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS"], cwd=att).returncode == 0
    # m2: while the orphan holds a process, no further job starts (refused before an attempt directory)
    stop("hold processes.*operator rule", run, world, "mlgym_cifar10", "campaigns-wave1", Engine(s))
    assert not J.job_dir(s, "mlgym_cifar10", "campaigns-wave1").exists()
    (made["ar2"] / "cgroup.events").write_text("populated 0\n")                # the operator cleared it

    # a kill helper that fails is "not verified": the same STOP
    def broken(parent):
        raise PermissionError("cgroup.kill")
    stop("could not be checked", run, world, "mlgym_cifar10", "campaigns-wave1", timeout, kill_cgroups=broken)


def test_review_m1_unlistable_scope_is_not_verified(tmp_path, monkeypatch):
    """Follow-ups review m1: Path.glob swallows PermissionError; the helpers use os.scandir, so a scope that exists
    but cannot be listed gives left None (the STOP), not []."""
    scope = app_slice(tmp_path / "a") / "run-r1.scope"
    _cg(scope, "ar_a", True, "4242\n")
    real = J.os.scandir

    def deny(path):
        if Path(path) == scope:
            raise PermissionError(13, "Permission denied", str(path))
        return real(path)
    monkeypatch.setattr(J.os, "scandir", deny)
    res = J.kill_run_cgroups(scope, signal_pid=lambda pid, sig: None)
    assert res["left"] is None and "PermissionError" in res["error"]
    assert J.run_cgroups_left(scope) is None and J.orphan_run_cgroups(scope) is None
    monkeypatch.setattr(J.os, "scandir", real)
    # a run cgroup whose cgroup.procs cannot be read (and no cgroup.events): not verified either
    scope2 = tmp_path / "scope2"
    d = _cg(scope2, "ar_b", True, "")
    (d / "cgroup.events").unlink()
    (d / "cgroup.procs").unlink()
    (d / "cgroup.procs").mkdir()                    # reading it fails with IsADirectoryError
    assert J.run_cgroups_left(scope2) is None
    d2 = _cg(tmp_path / "scope3", "ar_c", True, "not-a-pid\n")
    (d2 / "cgroup.events").unlink()
    assert J.run_cgroups_left(tmp_path / "scope3") is None
    # a cgroup that vanished holds nothing; an empty scope is verified clean
    assert J._cgroup_populated(tmp_path / "scope3" / "gone") is False
    clean = app_slice(tmp_path / "clean") / "run-r2.scope"
    clean.mkdir(parents=True)
    assert J.run_cgroups_left(clean) == [] and J.orphan_run_cgroups(clean) == []
    # the start-of-job check reads sibling scopes too: an unreadable sibling run cgroup is not verified
    bad = app_slice(tmp_path / "b") / "run-r3.scope"
    d3 = _cg(app_slice(tmp_path / "b") / "run-r4.scope", "ar_d", True, "x\n")
    (d3 / "cgroup.events").unlink()
    bad.mkdir()
    assert J.orphan_run_cgroups(bad) is None


def test_round2_n1_sibling_scan_only_under_the_user_manager(tmp_path):
    """Round 2 n1: the sibling scan runs only for a scope under this user's user@<uid>.service; otherwise None."""
    outside = tmp_path / "system.slice" / "foo.scope"
    outside.mkdir(parents=True)
    assert J.user_manager_scope(outside) is False and J.orphan_run_cgroups(outside) is None
    other = tmp_path / "user@99999.service" / "app.slice" / "run-r1.scope"
    other.mkdir(parents=True)
    assert J.orphan_run_cgroups(other) is None if os.getuid() != 99999 else True
    mine = app_slice(tmp_path) / "run-r1.scope"
    mine.mkdir(parents=True)
    assert J.user_manager_scope(mine) and J.orphan_run_cgroups(mine) == []
    assert not J.user_manager_scope(tmp_path / f"user@{os.getuid()}.service")     # the manager itself is no scope


def test_round2_m2_a_sibling_that_ends_during_the_scan_is_clean(tmp_path, monkeypatch):
    """Round 2 m2: a sibling unit, or its ar_* child, that ends between the listing and its scan holds nothing; any
    other read error still fails closed."""
    app = app_slice(tmp_path)
    mine = app / "run-r1.scope"
    mine.mkdir(parents=True)
    gone = app / "run-r2.scope"
    gone_child = _cg(app / "run-r3.scope", "ar_y", True, "1\n")
    gone.mkdir()
    real = J.os.scandir

    def vanish(path):
        if Path(path) == gone:                     # listed in app.slice, then the unit ends
            gone.rmdir()
            raise FileNotFoundError(2, "No such file or directory", str(path))
        if Path(path) == gone_child.parent:        # the ar_* child is listed, then removed with its unit
            it = real(path)
            entries = list(it)
            it.close()
            for f in gone_child.iterdir():
                f.unlink()
            gone_child.rmdir()
            return _Entries(entries)
        return real(path)
    monkeypatch.setattr(J.os, "scandir", vanish)
    assert J.orphan_run_cgroups(mine) == []

    def denied(path):
        if Path(path) == app / "run-r3.scope":
            raise PermissionError(13, "Permission denied", str(path))
        return real(path)
    _cg(app / "run-r3.scope", "ar_y", False)
    monkeypatch.setattr(J.os, "scandir", denied)
    assert J.orphan_run_cgroups(mine) is None


class _Entries(list):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_review_n1_sigkill_fallback_skips_pid_0_and_itself(tmp_path):
    scope = tmp_path / "scope"
    d = _cg(scope, "ar_x", True, f"0\n{os.getpid()}\n7171\n")
    (d / "cgroup.kill").unlink()
    (d / "cgroup.kill").symlink_to(tmp_path / "no" / "such")
    kills, t = [], [0.0]
    J.kill_run_cgroups(scope, grace=0.1, sleep=lambda _: t.__setitem__(0, t[0] + 0.1), monotonic=lambda: t[0],
                       signal_pid=lambda pid, sig: kills.append(pid))
    assert kills == [7171]


def test_review_m3_run_cgroups_checked_after_every_engine_exit(world):
    """Follow-ups review m3: after a non-zero exit, an engine error or a clean rc 0, the ar_* children are killed and
    must be empty; otherwise node STOP 9 and out/ untarred. A clean exit with an empty scope runs as before."""
    s, scope = world["spec"], world["scope"]
    rec = run(world, "mlab_imdb", "campaigns-wave1", Engine(s))          # rc 0, empty scope
    with tarfile.open(J.job_dir(s, "mlab_imdb", "campaigns-wave1") / "attempt-1" / "out.tar") as tar:
        assert json.loads(tar.extractfile("out/run_cgroups_kill.json").read())["left"] == []
    assert rec["stop"] is None
    left = {"left": ["ar_z"]}
    for node, rc in (("mlab_cifar10", 0), ("mlab_ogbn_arxiv", 3), ("mlgym_cifar10", -9)):
        class Exit(Engine):
            def __call__(self, argv, **kw):
                res = super().__call__(argv, **kw)
                return subprocess.CompletedProcess(argv, rc, res.stdout, res.stderr)
        stop("after the engine exited, ar_\\* run cgroups of the scope still hold processes", run, world, node,
             "campaigns-wave1", Exit(s), kill_cgroups=lambda parent: left)
        att = J.job_dir(s, node, "campaigns-wave1") / "attempt-1"
        jrec = json.loads((att / "job_record.json").read_text())
        assert jrec["stop_class"] == "node" and (att / "out").is_dir() and not (att / "out.tar").exists(), node

    def crash(argv, **kw):
        raise OSError("cannot start the interpreter")
    stop("after the engine exited", run, world, "mlgym_fmnist", "campaigns-wave1", crash,
         kill_cgroups=lambda parent: {"left": None})
    jrec = json.loads((J.job_dir(s, "mlgym_fmnist", "campaigns-wave1") / "attempt-1" / "job_record.json").read_text())
    assert jrec["stop_class"] == "node"


def test_review_m2_start_of_job_and_before_tar_checks(world, monkeypatch):
    """Follow-ups review m2: a populated ar_* child in this scope or a sibling scope refuses the job before any
    attempt; one that appears after the exit-time kill STOPs the job just before the tar (out/ untarred)."""
    s, scope = world["spec"], world["scope"]
    sib = scope.parent / "run-u77.scope"
    orphan = _cg(sib, "ar_u003_s7006_a0_1_2", True, "9191\n")
    odd = _cg(scope.parent / "train-7007.scope", "ar_u004_s7008_a0_1_2", True, "9292\n")   # a unit name not systemd's
    stop("hold processes: 2 populated ar_\\* run cgroup\\(s\\) in unit\\(s\\) <other unit>, run-u77.scope; "
         "operator rule: inspect", run, world, "mlab_imdb", "campaigns-wave1", Engine(s))
    refusal = "".join(p.read_text() for p in (J.run_root(s) / "_refusals").iterdir())
    for secret in ("7006", "7007", "7008", "ar_u00"):              # round 2 m3: no ar_* name, no odd unit name
        assert secret not in refusal, secret
    assert "run-u77.scope" in refusal and not J.job_dir(s, "mlab_imdb", "campaigns-wave1").exists()
    (orphan / "cgroup.events").write_text("populated 0\n")
    (odd / "cgroup.events").write_text("populated 0\n")
    _cg(scope.parent / "unrelated.scope", "app_x", True, "5\n")                  # not an ar_* child: ignored

    def kill_then_appear(parent):                           # a run cgroup populated after the exit-time kill
        _cg(Path(parent), "ar_late_1_2", True, "8181\n")
        return {"left": []}
    stop("before the tar, ar_\\* run cgroups of the scope hold processes", run, world, "mlab_imdb", "campaigns-wave1",
         Engine(s), kill_cgroups=kill_then_appear)
    att = J.job_dir(s, "mlab_imdb", "campaigns-wave1") / "attempt-1"
    jrec = json.loads((att / "job_record.json").read_text())
    assert jrec["stop_class"] == "node" and (att / "out").is_dir() and not (att / "out.tar").exists()
    assert "recorded before" not in jrec["stop"]                    # nothing was recorded before here


def test_round2_m1_before_tar_stop_keeps_the_earlier_reason(world):
    """Round 2 m1: an rc-0 job with a recorded STOP 2 whose pre-tar re-check fails keeps both reasons, in the job
    record and the diagnostics."""
    s, scope = world["spec"], world["scope"]
    run(world, "mlab_imdb", "campaigns-wave1", Engine(s))
    gate = (lambda rows: [json.dumps(json.loads(rows[0]) | {"isolation": dict(ISOLATED, log_intact=False)})]
            + rows[1:])

    def kill_then_unreadable(parent):        # the exit-time kill is clean; the pre-tar re-check cannot read a child
        d = _cg(Path(parent), "ar_flaky_1_2", True, "")
        (d / "cgroup.events").unlink()
        (d / "cgroup.procs").unlink()
        (d / "cgroup.procs").mkdir()
        return {"left": []}
    stop("before the tar.*; recorded before: STOP 2: audit run", run, world, "mlab_imdb", "audits-wave1",
         Engine(s, rows_edit=gate), kill_cgroups=kill_then_unreadable)
    att = J.job_dir(s, "mlab_imdb", "audits-wave1", 0) / "attempt-1"
    jrec, diag = (json.loads((att / n).read_text()) for n in ("job_record.json", "diagnostics.json"))
    assert jrec["stop"] == diag["stop"] and jrec["stop"].startswith(J.ORPHANS_BEFORE_TAR + "; recorded before: STOP 2")
    assert jrec["stop_class"] == diag["stop_class"] == "node" and not (att / "out.tar").exists()


def test_review_M1_g5_scope_matches_the_other_kinds(tmp_path):
    """Follow-ups review M1: no -p OOMPolicy= (scopes accept it only from systemd v253; TASL-2 runs 249): the g5
    kind's scope properties equal g1b's, g4's and xc's."""
    import test_t1_tasl_g1b as TG
    script = ROOT / "sweep2" / "t1_tasl" / "t1_tasl_node.sh"
    assert "OOMPolicy=continue" not in script.read_text().split("set -u", 1)[1]
    env = TG._stub_env(tmp_path, tmp_path / "runs" / "rid", 0)
    stub = Path(env["STUB_DIR"])
    for kind_args in (["g5", "spec.json", "mlab_imdb", "note.md", "audits-wave1", "-", "--enable"],
                      ["g1b", "spec.json", "mlab_imdb", "note.md"], ["g4", "spec.json", "mlab_imdb", "note.md", "srv"],
                      ["xc", "spec.json", "mlab_imdb", "note.md", "TASL-2"]):
        res = subprocess.run(["bash", str(script), *kind_args], env=env, capture_output=True, text=True)
        assert res.returncode == 0, res.stderr
        args = (stub / "systemd_run_args").read_text().split()
        assert " ".join(args[:args.index("--")]) == "--user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0"
        if kind_args[0] == "g5":
            argv = (stub / "run_node_argv").read_text().split("\n")[0]
            assert argv == "run spec.json --node mlab_imdb --note note.md --job audits-wave1 --enable"


# =============================================================================================== R1-G5-AUDIT-TWO-CARDS
UUID7 = SPEC["tasl7_audits"]["gpu_uuid"]
XC3_RUN = "g1b-tasl-20261121-b-xc3-a"


class FakeMain(dict):
    def read(self, rel):
        return self.get(rel)

    def ls(self, prefix=""):
        return sorted(p for p in self if p.startswith(prefix))


def short_pass(node, **kw):
    v = {"schema": "g1b_tasl_crosscheck_verdict/1", "label": "ENGINEERING_ONLY", "node": node, "mode": "short",
         "verdict": "PASS", "reason": None, "complete": True, "rule": "R1-G5-AUDIT-TWO-CARDS",
         "harness_commit": SPEC["harness_families"]["G5-7"]["g1b_pin"],
         "g1b_spec_sha256": SPEC["harness_families"]["G5-7"]["g1b_spec"]["sha256"], "g1b_run_id": "g1b-tasl-20261121-b",
         "crosscheck_run_id": XC3_RUN,
         "sides": {"TASL-7": {"run_id": f"{XC3_RUN}-TASL-7", "spec_sha256": "3" * 64, "job_record_sha256": "4" * 64,
                              "attempt": 1},
                   "TASL-2": {"run_id": "g1b-tasl-20261121-b", "spec_sha256": "5" * 64, "job_record_sha256": "6" * 64,
                              "attempt": 1}}}
    v.update(kw)
    return json.dumps(v, sort_keys=True).encode()


SHORT_REL = "docs/r1/reports/tasl_chain_20261122/G1B_XC3_SHORT_VERDICT_mlab_imdb_20261125.json"


def fake_main():
    """What published main holds for mlab_imdb to run on TASL-7: the TASL-7 host check, the xc2 verdicts, a signed
    xc3 note (XC3-FAIL A) and mlab_imdb's short PASS."""
    m = FakeMain()
    t = SPEC["tasl7_audits"]
    m[t["isolation_host_check"]["record"]] = (ROOT / t["isolation_host_check"]["record"]).read_bytes()
    for n in ("mlab_cifar10", "mlgym_cifar10", "mlgym_breakout_minatar"):
        for e in t["crosshost_pass"][n]:
            m[e["record"]] = (ROOT / e["record"]).read_bytes()
    m["docs/r1/PLAN.md"] = b"# PLAN\n"
    m["docs/r1/authorizations/g1b_xc_short_t1_tasl_20261126.md"] = (
        f"approved: true\nrun_id: {XC3_RUN}\nxc3_fail: A\nxc3_cap: R1-G1B-CAP\nskip_nodes: none\n").encode()
    m[SHORT_REL] = short_pass("mlab_imdb")
    return m


@pytest.fixture
def two(world, tmp_path, monkeypatch):
    """Two runs trees with the same layout: TASL-2's (the table's) and TASL-7's; ``on(host)`` switches the one the job
    code sees (in production they are two hosts at the same path); ``main`` is published main."""
    roots = {"TASL-2": J.run_root(world["spec"]), "TASL-7": tmp_path / "tasl7" / world["spec"]["run_id"]}
    cur = {"host": "TASL-2"}
    monkeypatch.setattr(J, "run_root", lambda spec: roots[cur["host"]])
    monkeypatch.setattr(J.SE, "run_root", lambda spec: roots[cur["host"]])
    monkeypatch.setattr(J, "CHUNK_LIMIT_S", 120.27 * 60)                  # several chunks per wave (7 for imdb)

    def smi7(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID7}, {out['model7']}, 580.178.04, 24564\n", "")

    def on(host):
        cur["host"] = host
    out = dict(world, roots=roots, on=on, smi7=smi7, model7="NVIDIA GeForce RTX 4090", main=fake_main())
    return out


def mkw(w):
    return dict(hostname=HOST2, read_main=w["main"].read, list_main=w["main"].ls)


def claim(w, node, wave, chunk, spec=None):
    return J.claim_chunk(spec or w["spec"], w["sp"], node, wave, chunk, **mkw(w))


def run7(w, node, job, chunk, engine, *, get=None, smi=None, k=10, node_log=None):
    ctx = {"K": k, "K_row": None, "host": "TASL-7", "chunk": chunk,
           "crosshost_pass": S.check_crosshost_pass(w["spec"], node, w["main"].read, w["main"].ls)}   # as the switch
    return J.run_job(w["sp"], node, job, ctx, smi=smi or w["smi7"], engine=engine, setup=w["setup"],
                     get=get or Server(up=False), git=w["git"], node_log=node_log)


def copy_to_tasl7(w, node, wave, chunk):
    """What the operator copies to TASL-7 (byte-identical, same relative paths): the claim and the wave's plan."""
    src, dst = w["roots"]["TASL-2"], w["roots"]["TASL-7"]
    rels = [J.claim_path(w["spec"], node, wave, chunk).relative_to(src)]
    rels += [p.relative_to(src) for p in (src / node / f"audits-wave{wave}").glob("plan*")]
    for rel in rels:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        (dst / rel).write_bytes((src / rel).read_bytes())


def back(w, tmp_path, node, job, chunk, attempt, tag=""):
    """Copy a TASL-7 attempt and TASL-7's access log to a staging area (as the operator does); returns both paths."""
    import shutil
    w["on"]("TASL-7")
    src = J.job_dir(w["spec"], node, job, chunk) / f"attempt-{attempt}"
    stage = tmp_path / f"staged{tag}" / f"attempt-{attempt}"
    stage.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, stage)
    log = tmp_path / f"staged{tag}" / f"access_log_{attempt}.jsonl"
    log.write_bytes((J.run_root(w["spec"]) / "_access_log.jsonl").read_bytes())
    w["on"]("TASL-2")
    return stage, log


def register(w, stage, log, node="mlab_imdb", wave=1, chunk=1, **kw):
    return J.register_attempt(w["spec"], w["sp"], stage, node, wave, chunk, log, **mkw(w), **kw)


def first_wave(w, node="mlab_imdb"):
    eng = Engine(w["spec"])
    run(w, node, "campaigns-wave1", eng)
    run(w, node, "audits-wave1", eng)                       # makes the plan and runs chunk 0 on TASL-2
    return eng, json.loads(J.plan_path(w["spec"], node, 1).read_text())["chunks"]


HOST2 = lambda: SPEC["worker"]["hostname"]                  # noqa: E731


def test_two_cards_claims_on_tasl2(two):
    s, sp = two["spec"], two["sp"]
    stop("has no plan yet", claim, two, "mlab_imdb", 1, 1)
    eng, chunks = first_wave(two)
    assert chunks > 3
    stop("are made on TASL-2", J.claim_chunk, s, sp, "mlab_imdb", 1, 1, hostname=lambda: "TASL-7",
         read_main=two["main"].read, list_main=two["main"].ls)
    stop("audits stay on TASL-2", claim, two, J.S.AR, 1, 1)
    stop("not claimable", claim, two, "mlab_imdb", 1, chunks - 1)                     # the E5 chunk
    stop("has attempts on TASL-2", claim, two, "mlab_imdb", 1, 0)
    c = claim(two, "mlab_imdb", 1, 2)
    assert (c["host"], c["chunk"], c["K"], c["spec_sha256"]) == ("TASL-7", 2, 10, G.L._sha_file(sp))
    assert c["registered_attempts_at_claim"] == [] and c["crosshost_pass"]["records"][0]["record"] == SHORT_REL
    assert (J.run_root(s) / "_remote" / "claims.lock").exists()                       # m4
    stop("is claimed already", claim, two, "mlab_imdb", 1, 2)
    stop("another claim is open", claim, two, "mlab_imdb", 1, 1)
    # TASL-2 skips the claimed chunk and never runs the wave's last chunk while a claim is open
    done = []
    while True:
        try:
            done.append(run(two, "mlab_imdb", "audits-wave1", eng)["chunk"])
        except J.Stop as exc:
            assert "STOP (not yet)" in str(exc) and "[2]" in str(exc)
            break
    assert 2 not in done and chunks - 1 not in done and sorted(done) == [i for i in range(1, chunks - 1) if i != 2]


def test_two_cards_c12_claim_needs_tasl7s_own_record(two):
    """P1 on TASL-7 (this unit): under ``cuda_ipc: c12`` a claim for TASL-7 needs TASL-7's own C12 PASS record on main
    (``g5_tasl.check_c12``); TASL-2's record alone does not let a chunk move. Under the acceptance line nothing more is
    read (the line names TASL-7's audit chunks)."""
    first_wave(two)
    m = two["main"]
    c12, c12_7 = "docs/r1/reports/x/C12_TASL2.md", "docs/r1/reports/x/C12_TASL7.md"
    m[c12], m[c12_7] = b"c12_host: TASL-2\nc12_verdict: PASS\n", b"c12_host: TASL-7\nc12_verdict: PASS\n"
    s = copy.deepcopy(two["spec"])
    s["key_values"]["cuda_ipc"].update(mode="c12", c12_record=c12, c12_sha256=hashlib.sha256(m[c12]).hexdigest())
    stop("needs a C12 PASS record for TASL-7", claim, two, "mlab_imdb", 1, 1, spec=s)
    s["key_values"]["cuda_ipc"].update(c12_tasl7_record=c12_7, c12_tasl7_sha256=hashlib.sha256(m[c12_7]).hexdigest())
    assert J.tasl7_eligible(s, "mlab_imdb", m.read, m.ls)["cuda_ipc"]["host"] == "TASL-7"
    assert claim(two, "mlab_imdb", 1, 1, spec=s)["chunk"] == 1


def test_two_cards_m1_claims_only_for_a_node_that_can_run_on_tasl7(two):
    """Review M1: no claim for a node without its cross-host PASS, without the TASL-7 host check, with an unfilled
    TASL-7 environment, or under G5-TASL-GPUH B (each would deadlock the wave's E5 chunk)."""
    s = two["spec"]
    first_wave(two)
    m = two["main"]
    good = m.pop(SHORT_REL)
    stop("no cross-host PASS record of mlab_imdb", claim, two, "mlab_imdb", 1, 1)
    m[SHORT_REL] = short_pass("mlab_imdb", verdict="STOP", reason="cross_host_mismatch")
    stop("not a cross-host PASS of mlab_imdb", claim, two, "mlab_imdb", 1, 1)
    m[SHORT_REL] = good
    host = s["tasl7_audits"]["isolation_host_check"]["record"]
    hc = m.pop(host)
    stop("not on published main", claim, two, "mlab_imdb", 1, 1)
    m[host] = hc
    s2 = copy.deepcopy(s)
    s2["tasl7_audits"]["node_extra_env"]["mlab_imdb"] = {"X": "PENDING: its path on TASL-7"}
    stop("environment on TASL-7 is not filled", claim, two, "mlab_imdb", 1, 1, spec=s2)
    stop("not built under G5-TASL-GPUH B", claim, two, "mlab_imdb", 1, 1,
         spec=S.apply_options(s, {"G5-TASL-GPUH": "B"}))
    assert not list((J.run_root(s) / "_remote").glob("claims/**/*.json"))           # nothing was claimed
    assert claim(two, "mlab_imdb", 1, 1)["chunk"] == 1


def test_two_cards_m4_tasl2_takes_the_claims_lock_around_its_chunk_pick(two, monkeypatch):
    seen = []
    real = J.claims_lock

    @__import__("contextlib").contextmanager
    def spy(spec):
        with real(spec) as p:
            seen.append(p)
            yield p
    monkeypatch.setattr(J, "claims_lock", spy)
    first_wave(two)
    assert seen and seen[-1].endswith("_remote/claims.lock")


def test_two_cards_tasl7_chunk_refusals(two):
    s, sp = two["spec"], two["sp"]
    eng, chunks = first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    stop("no claim of mlab_imdb", run7, two, "mlab_imdb", "audits-wave1", 1, eng)          # nothing copied yet
    two["on"]("TASL-2")
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    stop("no claim of mlab_imdb audits-wave1 chunk 2", run7, two, "mlab_imdb", "audits-wave1", 2, eng)
    stop("only audit chunks run on TASL-7", run7, two, "mlab_imdb", "campaigns-wave1", 1, eng)
    stop("does not name this job.*K", run7, two, "mlab_imdb", "audits-wave1", 1, eng, k=6)
    # a campaign wave holds the server: it answers /health
    stop("proposer answers /health .* while a G.5 audit chunk runs on TASL-7", run7, two, "mlab_imdb", "audits-wave1",
         1, eng, get=Server(up=True))
    # the server's lease is held (the running server holds it): no shared card
    with G.gpu_lease(SPEC["proposer"]["lease"]):
        stop("held by another job", run7, two, "mlab_imdb", "audits-wave1", 1, eng)
    # one table, one GPU model
    two["model7"] = "NVIDIA RTX 6000 Ada Generation"
    stop("not NVIDIA GeForce RTX 4090", run7, two, "mlab_imdb", "audits-wave1", 1, eng)
    two["model7"] = "NVIDIA GeForce RTX 4090"
    # autoresearch never runs on TASL-7 (its claim cannot be made; the job refuses it too)
    stop("audits stay on TASL-2", J.worker_shim, s, J.S.node_entry(s, J.S.AR), {"host": "TASL-7"})
    # a node whose TASL-7 environment is not filled is refused there
    s2 = copy.deepcopy(s)
    s2["tasl7_audits"]["node_extra_env"]["mlgym_houseprice"]["AR_HOUSEPRICE_TRAIN_CSV"] = "PENDING: x"
    stop("environment on TASL-7 is not filled", J.worker_shim, s2, J.S.node_entry(s2, "mlgym_houseprice"),
         {"host": "TASL-7"})
    shim, _ = J.worker_shim(s, J.S.node_entry(s, "mlgym_houseprice"), {"host": "TASL-7"})        # n1: filled
    assert shim["hosts"]["TASL-7"]["extra_env"]["AR_HOUSEPRICE_TRAIN_CSV"] == "/home/dowling/r1_inputs/house-prices/train.csv"
    # a TASL-2 job never names a chunk
    two["on"]("TASL-2")
    stop("takes the next unclaimed chunk", J.run_job, sp, "mlab_imdb", "audits-wave1", {"K": 10, "chunk": 1},
         smi=two["smi"], engine=eng, setup=two["setup"], get=Server(), git=two["git"])


def test_two_cards_claim_run_register_end_to_end(two, tmp_path):
    s, sp = two["spec"], two["sp"]
    eng, chunks = first_wave(two)
    c = claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    rec = run7(two, "mlab_imdb", "audits-wave1", 1, eng)
    assert rec["stop"] is None and rec["worker_host"] == "TASL-7" and rec["chunk"] == 1
    assert rec["claim_sha256"] == c["sha256"] and rec["gpu"]["uuid"] == UUID7 and rec["gpu"]["name"] == T4.GPU_MODEL
    assert rec["crosshost_pass"]["records"][0]["record"] == SHORT_REL           # the PASS records it ran under
    assert rec["server_stopped"]["reachable"] is False and "--gpu-uuid" in eng.calls[-1] and UUID7 in eng.calls[-1]
    assert "wave_checks" not in rec and not (two["roots"]["TASL-7"] / "_k_lock.json").exists()
    t7_log = J.run_root(s) / "_access_log.jsonl"
    assert any("claimed chunk 1 on TASL-7" in json.loads(x)["purpose"] for x in t7_log.read_text().splitlines())
    stop("is complete", run7, two, "mlab_imdb", "audits-wave1", 1, eng)
    two["on"]("TASL-2")
    stage, log = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1)
    stop("are made on TASL-2", J.register_attempt, s, sp, stage, "mlab_imdb", 1, 1, log, hostname=lambda: "TASL-7")
    stop("is not claimed", register, two, stage, log, chunk=3)
    bad_log = tmp_path / "bad_log.jsonl"
    bad_log.write_text(json.dumps({"who": "someone", "purpose": "curiosity"}) + "\n")
    stop("STOP 11", register, two, stage, bad_log)
    reg = register(two, stage, log)
    assert reg["host"] == "TASL-7" and reg["stop"] is None and reg["crosshost_pass"]["records"] == rec["crosshost_pass"]["records"]
    stop("is closed", register, two, stage, log)                  # m1 / M2 b: a closed claim takes nothing more
    assert J.complete_attempt(J.job_dir(s, "mlab_imdb", "audits-wave1", 1))[0]["worker_host"] == "TASL-7"
    assert J.open_claims(s) == []                                       # the next claim may be made
    while not J.audits_done(s, "mlab_imdb", 1):
        r = run(two, "mlab_imdb", "audits-wave1", eng)
        assert r["chunk"] != 1
    last = J.complete_attempt(J.job_dir(s, "mlab_imdb", "audits-wave1", chunks - 1))[1]
    assert last["wave_e5"]["audited"] == 41                     # E5 over every chunk, the registered one included
    assert json.loads(J.wave_checks_path(s, "mlab_imdb", 1).read_text())["stops"] == []
    # the final TASL-7 log registration closes TASL-7 work; afterwards nothing more is claimed or registered
    final = J.finalize_remote(s, sp, log, hostname=HOST2)
    assert final["access_log_sha256"] == reg["access_log"]["sha256"]
    assert J.SE.check_remote_final(s)["utc"] == final["utc"]
    stop("final registration", claim, two, "mlab_imdb", 1, 2)
    stop("final registration", register, two, stage, log)


def test_two_cards_m2_every_tasl7_attempt_is_registered_in_order(two, tmp_path):
    """Review M2, scenario 1: an infrastructure-STOP TASL-7 attempt cannot be skipped (attempt 2 needs attempt 1
    registered first), so its hours reach the meter and it is sealed; the claim stays open until a complete attempt is
    registered, and the node, the run and the TASL-7 log cannot be sealed or finalised meanwhile."""
    s, sp = two["spec"], two["sp"]
    first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    stop("audit engine", run7, two, "mlab_imdb", "audits-wave1", 1, Engine(s, chunk_stop="boom"))       # infra STOP
    assert run7(two, "mlab_imdb", "audits-wave1", 1, Engine(s))["attempt"] == 2
    two["on"]("TASL-2")
    s1, l1 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    s2, l2 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 2, "b")
    stop(r"attempt-2 is not the next attempt of the chunk \(registered: \[\]\)", register, two, s2, l2)
    before = J.gpu_hours_consumed(s)
    assert J.SE.open_claims(s) and J.SE.node_finished(s, "mlab_imdb") is None
    stop("open TASL-7 claim", J.SE.seal_node, s, "mlab_imdb")
    stop("TASL-7 claims are open", J.SE.seal_run, s, not_run=tuple(n for n in S.T1_NODES if n != "mlab_imdb"))
    stop("claims are open", J.finalize_remote, s, sp, l2, hostname=HOST2)
    register(two, s1, l1)
    assert J.SE.open_claims(s)                                  # an infrastructure STOP leaves the claim open
    register(two, s2, l2)
    assert not J.SE.open_claims(s)
    recs = [json.loads((J.job_dir(s, "mlab_imdb", "audits-wave1", 1) / f"attempt-{n}" / "job_record.json").read_text())
            for n in (1, 2)]
    assert J.gpu_hours_consumed(s) == pytest.approx(before + sum(r["gpu_seconds"] for r in recs) / 3600.0, abs=1e-3)
    stop("TASL-7 ran audit chunks but its access log has no final registration", J.SE.check_remote_final, s)


def test_two_cards_m2_no_registration_after_a_node_stop(two, tmp_path):
    """Review M2, scenario 2: after a registered node STOP the claim is closed; a later attempt is refused."""
    s, sp = two["spec"], two["sp"]
    first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    stop("STOP 2", run7, two, "mlab_imdb", "audits-wave1", 1, Engine(s, chunk_stop="x", chunk_stop_kind="unisolated"))
    two["on"]("TASL-2")
    s1, l1 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    register(two, s1, l1)
    assert J.SE.claim_state(s, json.loads(J.claim_path(s, "mlab_imdb", 1, 1).read_text())) == "closed"
    assert J.node_stopped(J.run_root(s) / "mlab_imdb")
    import shutil
    later = tmp_path / "later" / "attempt-2"
    shutil.copytree(s1, later)
    stop("is closed; nothing more is registered", register, two, later, l1)
    stop("is closed; it is not abandoned", J.abandon_claim, s, sp, "mlab_imdb", 1, 1, "TASL-7 is down for a week", l1,
         hostname=HOST2)


def test_two_cards_m1_abandon_claim_returns_the_chunk_to_tasl2(two, tmp_path):
    s, sp = two["spec"], two["sp"]
    eng, chunks = first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    stop("audit engine", run7, two, "mlab_imdb", "audits-wave1", 1, Engine(s, chunk_stop="boom"))
    two["on"]("TASL-2")
    s1, l1 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    register(two, s1, l1)
    stop("needs a reason", J.abandon_claim, s, sp, "mlab_imdb", 1, 1, "short", l1, hostname=HOST2)
    missing = tmp_path / "missing.jsonl"
    stop("does not exist", J.abandon_claim, s, sp, "mlab_imdb", 1, 1, "TASL-7 card failed its checks", missing,
         hostname=HOST2)
    rec = J.abandon_claim(s, sp, "mlab_imdb", 1, 1, "TASL-7 card failed its checks", l1, hostname=HOST2)
    assert rec["registered_attempts"] == [1] and "returns to TASL-2" in rec["effect"]
    assert J.SE.abandon_path(s, "mlab_imdb", "audits-wave1", 1).is_file()
    assert J.claimed_chunks(s, "mlab_imdb", 1) == set() and J.open_claims(s) == []
    stop("is abandoned", register, two, s1, l1)
    stop("is abandoned", J.abandon_claim, s, sp, "mlab_imdb", 1, 1, "TASL-7 card failed again", l1, hostname=HOST2)
    r = run(two, "mlab_imdb", "audits-wave1", eng)                 # TASL-2 takes the chunk back, as attempt 2
    assert (r["chunk"], r["attempt"], r["worker_host"]) == (1, 2, "TASL-2")
    J.finalize_remote(s, sp, l1, hostname=HOST2)
    assert J.SE.check_remote_final(s)


def test_two_cards_round2_n2_registration_compares_with_the_claim(two, tmp_path):
    """Review round 2, N2: the record's ``crosshost_pass`` must equal the claim's (m2: non-null). If main moves between
    the run and the registration, the attempt is still registered (accounting is never blocked); the check on main
    then is recorded for information only."""
    s, sp = two["spec"], two["sp"]
    first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    run7(two, "mlab_imdb", "audits-wave1", 1, Engine(s))
    two["on"]("TASL-2")
    s1, l1 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    import shutil
    nul = tmp_path / "nul" / "attempt-1"
    shutil.copytree(s1, nul)
    rec = json.loads((nul / "job_record.json").read_text())
    (nul / "job_record.json").write_text(json.dumps(rec | {"crosshost_pass": None}))
    stop("crosshost_pass", register, two, nul, l1)                              # m2: non-null
    other = tmp_path / "other" / "attempt-1"
    shutil.copytree(s1, other)
    (other / "job_record.json").write_text(json.dumps(rec | {"crosshost_pass": {"records": [{"record": "x"}]}}))
    stop("not the PASS records the claim checked", register, two, other, l1)
    two["main"][SHORT_REL] = short_pass("mlab_imdb", crosscheck_run_id="g1b-tasl-20261121-b-xc3-b")   # main moved
    reg = register(two, s1, l1)
    assert reg["stop"] is None and reg["crosshost_pass"]["same_as_claim"] is False and "error" in reg["crosshost_pass"]
    assert J.complete_attempt(J.job_dir(s, "mlab_imdb", "audits-wave1", 1)) is not None      # it counts


def test_two_cards_round2_n3_an_abandoned_claim_does_not_run_on_tasl7(two, tmp_path):
    s, sp = two["spec"], two["sp"]
    first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    stop("audit engine", run7, two, "mlab_imdb", "audits-wave1", 1, Engine(s, chunk_stop="boom"))
    two["on"]("TASL-2")
    s1, l1 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    register(two, s1, l1)
    J.abandon_claim(s, sp, "mlab_imdb", 1, 1, "TASL-7 card failed its checks", l1, hostname=HOST2)
    rel = J.SE.abandon_path(s, "mlab_imdb", "audits-wave1", 1).relative_to(two["roots"]["TASL-2"])
    dst = two["roots"]["TASL-7"] / rel                                    # the operator copies it to TASL-7
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes((two["roots"]["TASL-2"] / rel).read_bytes())
    two["on"]("TASL-7")
    stop("is abandoned .its record is here.", run7, two, "mlab_imdb", "audits-wave1", 1, Engine(s))


def test_two_cards_m5_tasl7_meter_does_not_double_count(two, tmp_path):
    """Review m5: the claim lists the registered TASL-7 attempts its meter reading includes; TASL-7's check adds only
    its records the claim does not list."""
    s, sp = two["spec"], two["sp"]
    first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    run7(two, "mlab_imdb", "audits-wave1", 1, Engine(s))
    rp = J.job_dir(s, "mlab_imdb", "audits-wave1", 1) / "attempt-1" / "job_record.json"
    two["on"]("TASL-2")
    s1, l1 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    register(two, s1, l1)
    c2 = claim(two, "mlab_imdb", 1, 2)
    assert c2["registered_attempts_at_claim"] == ["mlab_imdb/audits-wave1/chunk-1/attempt-1"]
    copy_to_tasl7(two, "mlab_imdb", 1, 2)
    two["on"]("TASL-7")
    cap = s["key_values"]["cap_gpu_hours"]
    cp = J.claim_path(s, "mlab_imdb", 1, 2)
    local = json.loads(cp.read_text())
    rp.write_text(json.dumps(json.loads(rp.read_text()) | {"gpu_seconds": 3600.0}))     # one hour on TASL-7's copy
    cp.write_text(json.dumps(local | {"gpu_hours_at_claim": cap - 0.5}))
    J.check_order_tasl7(s, sp, "mlab_imdb", "audits-wave1", 2, {"K": 10})               # listed: not counted again
    cp.write_text(json.dumps(local | {"gpu_hours_at_claim": cap - 0.5, "registered_attempts_at_claim": []}))
    stop("STOP 9", J.check_order_tasl7, s, sp, "mlab_imdb", "audits-wave1", 2, {"K": 10})


def test_two_cards_m7_node_wrapper_log_is_registered(two, tmp_path):
    s, sp = two["spec"], two["sp"]
    first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    logdir = J.run_root(s) / "_logs"
    logdir.mkdir(parents=True, exist_ok=True)
    nl = logdir / "mlab_imdb-20261201T000000Z-1.node.log"
    nl.write_text("# t1_tasl g5t7 node=mlab_imdb\nNODE_EXIT=0\n")
    run7(two, "mlab_imdb", "audits-wave1", 1, Engine(s), node_log=str(nl))
    two["on"]("TASL-2")
    s1, l1 = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    stop("register it with the attempt", register, two, s1, l1)
    reg = register(two, s1, l1, node_log=nl)
    assert reg["node_log"]["sha256"] == G.L._sha_file(nl)
    assert (J.run_root(s) / "_remote" / "TASL-7" / "logs" / nl.name).read_bytes() == nl.read_bytes()


def test_two_cards_register_refuses_a_tampered_or_foreign_attempt(two, tmp_path):
    s, sp = two["spec"], two["sp"]
    first_wave(two)
    claim(two, "mlab_imdb", 1, 1)
    copy_to_tasl7(two, "mlab_imdb", 1, 1)
    two["on"]("TASL-7")
    run7(two, "mlab_imdb", "audits-wave1", 1, Engine(s))
    two["on"]("TASL-2")
    src, log = back(two, tmp_path, "mlab_imdb", "audits-wave1", 1, 1, "a")
    import shutil
    for name, edit, match in (
            ("sums", lambda d: (d / "out.tar").write_bytes(b"x"), "does not verify"),
            ("extra", lambda d: (d / "notes.txt").write_text("x"), "files other than"),
            ("norec", lambda d: (d / "job_record.json").unlink(), "has no job_record.json"),        # n3
            ("host", lambda d: (d / "job_record.json").write_text(json.dumps(
                json.loads((d / "job_record.json").read_text()) | {"worker_host": "TASL-2"})), "worker_host")):
        d = tmp_path / name / "attempt-1"
        shutil.copytree(src, d)
        edit(d)
        stop(match, register, two, d, log)
    register(two, src, log)
    short = tmp_path / "short.jsonl"
    short.write_text(json.dumps({"who": "g5_job", "purpose": "wave E5: other"}) + "\n")
    stop("does not extend", J.register_access_log, s, short)


def test_two_cards_node_wrapper_kind():
    """``t1_tasl_node.sh g5t7``: one claimed audit chunk on TASL-7 (``run ... --host TASL-7 --chunk <i>``), its cpus
    and log directory asked for TASL-7 (review n2)."""
    sh = str(ROOT / "sweep2" / "t1_tasl" / "t1_tasl_node.sh")
    script = Path(sh).read_text()
    assert '--job "$JOB" --host TASL-7 --chunk "$CHUNK"' in script and '[ "$KIND" = g5t7 ] && QUERY+=(--host TASL-7)' in script
    for args, why in ((["campaigns-wave1", "1"], "audit chunks only"), (["audits-wave1", "x"], "claimed chunk number"),
                      (["audits-wave1", ""], "claimed chunk number")):
        res = subprocess.run(["bash", sh, "g5t7", "s.json", "n", "note", *args], capture_output=True, text=True)
        assert res.returncode == 2 and why in res.stderr, res.stderr
    spec = ROOT / "sweep2" / "t1_tasl" / "g5_tasl_spec.json"
    out = subprocess.run([sys.executable, str(ROOT / "sweep2" / "t1_tasl" / "g5_tasl.py"), "cpus", str(spec), "--node",
                          "mlab_imdb", "--host", "TASL-7"], capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == SPEC["tasl7_audits"]["cpus"]
