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
def make_rows(chunk, kind=lambda unit, state, seed: "ok"):
    state = {u["unit"]: u["code_state_sha256"] for u in chunk["units"]}
    return [json.dumps({"schema": J.ROW_SCHEMA, "unit": r["unit"], "seed": r["seed"], "executed": True,
                        "code_state_sha256": state[r["unit"]], "value": 0.123,
                        "outcome": {"kind": kind(r["unit"], state[r["unit"]], r["seed"]), "reason": None},
                        "isolation": {"effective": True, "waivers": {}, "exceptions": []}}) for r in chunk["runs"]]


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
    bad = json.loads(rows[0]) | {"isolation": {"effective": True, "waivers": {"x": 1}, "exceptions": []}}
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

    def __init__(self, spec, divergent_states=(), campaign_stop=None, row_kind=None, ledger_edit=None):
        self.spec, self.calls = spec, []
        self.divergent_states = set(divergent_states)
        self.campaign_stop = campaign_stop
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
            (out / "campaign_record.json").write_text(json.dumps({"stop": self.campaign_stop}))
            work = out / J.campaign_dir_name(f["instances"][0]) / "runs" / "s001" / "work"
            work.mkdir(parents=True)
            (work / "model.pt").write_bytes(bytes(range(256)) * 4)          # a binary output (M1)
        else:
            chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
            label = set(S.audit_seeds(self.spec, chunk["K"])["label"])
            rows = make_rows(chunk, self.row_kind or (lambda u, st, seed: "divergent"
                                                      if st in self.divergent_states and seed in label else "ok"))
            (out / "rows.jsonl").write_text("\n".join(rows) + "\n")
            (out / "chunk_record.json").write_text(json.dumps({"stop": None}))
            (out / "runs").mkdir()
            (out / "runs" / "weights.npy").write_bytes(b"\x93NUMPY\xff\xfe" * 64)
        return subprocess.CompletedProcess(argv, 0, "engine ok", "")


@pytest.fixture
def world(jspec, tmp_path, monkeypatch):
    s, sp = jspec
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path / "home" / p.lstrip("~/")))
    monkeypatch.setattr(G, "host_identity", lambda sh, h: {"host": h})
    monkeypatch.setattr(G, "ptrace_scope", lambda: 1)
    monkeypatch.setattr(G, "scope_cgroup", lambda: {"cgroup_parent": "/sys/fs/cgroup/scope"})
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
    return {"spec": s, "sp": sp, "srv": srv, "smi": smi, "git": git, "setup": setup}


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
    eng = Engine(s, campaign_stop="ManagerTransportStop: down at seed 7006 metric 0.81")
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
    assert c["truncation_invalid_in"].endswith("manager_v2_diff.py") and "manager_v2_diff.py" in S.ENGINE_FILES
    seen = []

    def git(argv, **kw):                        # m3: the marker and both schemas must be in audit_g5.py
        seen.append(argv[argv.index("-e") + 1])
        return subprocess.CompletedProcess(argv, 0 if argv[argv.index("-e") + 1] != J.CHUNK_SCHEMA else 1, "", "")
    stop("trackg_g5_audit_chunk/v1", J.check_engines, tmp_path, "7" * 40, git=git)
    assert seen[0] == J.ENGINE_CONTRACT
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
