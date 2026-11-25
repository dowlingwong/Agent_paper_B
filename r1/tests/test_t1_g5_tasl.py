"""The G.5 spec validator and switch (sweep2/t1_tasl/g5_tasl.py, G.5 code unit part 3a).

Synthetic only: no host, no GPU, no network, no label, no evaluation value. Published main is a dict served by a fake
``read_main``; the harness checks run on throwaway git repositories (and on the real pins when AR_HARNESS_ROOT is set).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
import g5_tasl as T  # noqa: E402
import g5_pin_check as PC  # noqa: E402

SPEC_PATH = ROOT / "sweep2" / "t1_tasl" / "g5_tasl_spec.json"
SPEC = json.loads(SPEC_PATH.read_text())
DRAFT = (ROOT / "docs" / "r1" / "proposals" / "T1_G5_AUTHORIZATION_DRAFT_20261120.md").read_text()
ALL_A = {d: "A" for d in T.DECISIONS}
TODAY = date(2026, 12, 1)
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731


def stop(match, fn, *a, **kw):
    with pytest.raises(T.Stop, match=match):
        fn(*a, **kw)


# =============================================================================================== the shipped spec
def test_shipped_spec_is_all_a_unsigned_and_matches_the_draft():
    out = T.validate_spec(copy.deepcopy(SPEC))
    assert out["options"] == ALL_A and out["unsigned"] == list(T.DECISIONS) and out["launch_blockers"] == []
    p = out["projection"]
    assert (p["share=0.6 K=10"]["worker_gpu_hours"], p["share=0.8 K=10"]["worker_gpu_hours"],
            p["share=0.6 K=6"]["worker_gpu_hours"], p["share=0.8 K=6"]["worker_gpu_hours"]) == (305.3, 386.0, 208.5, 259.9)
    assert out["share_0_8_with_margin"] == 424.6 <= out["cap_gpu_hours"] == 425          # §2.6
    assert out["audited_band"] == [100, 200] and out["e4_amendment_needed"] is True
    for needle in ("| 10 | share 0.6, LLM 60 s | 305.3 |", "386.0 × 1.1 = 424.6", "below 0.25", "exceeds 0.2",
                   "above 5 % of a node's proposals", "100–200 under A, 150–240 under B; doubled under MEM B",
                   "release date: **18 Dec 2026**", "instance_seeds: 5101-5112"):
        assert needle in DRAFT, needle
    stop("must be a full 40-hex commit|run_id|not signed", T.validate_spec, copy.deepcopy(SPEC), launch=True)


def test_spec_carries_nodes_families_seeds_markers_and_key_values():
    s = SPEC
    assert [n["node"] for n in s["nodes"]] == list(T.T1_NODES)
    assert {n["node"]: n["family"] for n in s["nodes"]}[T.AR] == "G5-AR"
    assert all(n["family"] == "G5-7" for n in s["nodes"] if n["node"] != T.AR)
    assert s["harness_families"]["G5-7"]["g1b_pin"] == PC.PIN_SEVEN == "c025f89aeafc2199bf3487b4bcaa16678273c702"
    assert s["harness_families"]["G5-AR"]["g1b_pin"] == PC.PIN_AR == "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe"
    assert s["audit"]["seed_blocks"] == {"10": {"label": [7001, 7005], "evaluation": [7006, 7010]},
                                         "6": {"label": [7001, 7003], "evaluation": [7006, 7008]}}
    assert s["instances"]["seeds"] == [5101, 5112] and s["instances"]["per_node"] == 12
    ar = T.node_entry(s, T.AR)
    assert ar["env"] == ar["tails"] == T.AR_PENDING and ar["census_gpu_model"] == T.GPU_MODEL
    assert s["noise_floor"]["ar"]["copy"] == T.AR_PENDING and s["ar_prerequisites"]["pending"] == T.AR_PENDING_ITEMS
    assert s["harness_families"]["G5-AR"]["isolation_host_check"] == T.AR_PENDING
    assert "ar-cond7a" not in s["envs"]
    kv = s["key_values"]
    assert (kv["cap_gpu_hours"], kv["liveness_floor"], kv["invalid_share_stop"], kv["infrastructure_stop_share"],
            kv["audited_band"], kv["freeze_wait_release_date"], kv["seal_mode"]) == \
        (425, 0.25, 0.2, 0.05, [100, 200], "2026-12-18", "procedural")
    assert kv["cuda_ipc"]["mode"].startswith("PENDING")
    assert s["ar_prerequisites"]["proposed_environment"]["sha256"].startswith("11def6ad")
    assert all(not d["signed"] and d["recommended"] == "A" for d in s["decisions"].values())
    assert s["e4_amendment_row"].startswith("PENDING") and "E4" in s["e4_amendment_row"]
    assert T.apply_options(SPEC, ALL_A) == SPEC                         # the shipped spec is the all-A spec


def test_split_and_seed_rules():
    split = json.loads((ROOT / "r1/c3/splits/c3_p3_split_v1.json").read_text())["t1"]["nodes"]
    for node in T.T1_NODES:
        assert T.split_from_rule(node, list(range(5101, 5113))) == {k: sorted(v) for k, v in split[node].items()}
    k6 = T.audit_seeds(SPEC, 6)
    assert k6 == {"label": [7001, 7002, 7003], "evaluation": [7006, 7007, 7008]}                   # STOP 10
    assert not {7004, 7005, 7009, 7010} & set(k6["label"] + k6["evaluation"])
    assert T.audit_seeds(SPEC, 10)["label"] == [7001, 7002, 7003, 7004, 7005]
    stop("K is 10 or 6", T.audit_seeds, SPEC, 8)


def _edit(fn):
    s = copy.deepcopy(SPEC)
    fn(s)
    return s


@pytest.mark.parametrize("fn, match", [
    (lambda s: s["nodes"][0].update(run_seconds=1.0), "differs from its G.1b spec"),
    (lambda s: s["nodes"][1].update(family="G5-AR"), "harness family G5-7"),
    (lambda s: s["nodes"].pop(), "eight T1 nodes"),
    (lambda s: s["nodes"][7].update(census_gpu_model=T.ADA_MODEL), "census_gpu_model"),
    (lambda s: s["nodes"][7].update(env="ar-cond7a"), "PENDING marker"),
    (lambda s: s["instances"].update(seeds=[9001, 9012]), "seeds 5101-5112"),
    (lambda s: s["audit"]["seed_blocks"]["6"].update(label=[7001, 7005]), "seed_blocks"),
    (lambda s: s["audit"].update(e5_seed_block="all"), "inconsistent with the chosen options"),
    (lambda s: s["instances"]["split_file"].update(sha256="0" * 64), "split_file"),
    (lambda s: s["harness_families"]["G5-7"]["g1b_spec"].update(sha256="0" * 64), "differs from"),
    (lambda s: s["harness_families"]["G5-7"].update(harness_dir="/home/dowling/r1_tracks/t1_tasl/harness"),
     "must not be a G.1b or G.4 checkout"),
    (lambda s: s["harness_families"]["G5-AR"].update(harness_dir=s["harness_families"]["G5-7"]["harness_dir"]),
     "two checkouts"),
    (lambda s: s["harness_families"]["G5-AR"].update(g1b_pin=PC.PIN_SEVEN), "g1b_pin"),
    (lambda s: s["proposer"].update(server_url="http://tasl-7.tail119748.ts.net:8096"), "G.4 spec's"),
    (lambda s: s["worker"].update(sealed_root="/home/dowling/r1_tracks/t1_tasl/sealed_g1b"), "G.5's own"),
    (lambda s: s["worker"].update(driver="550.0"), "driver"),
    (lambda s: s["key_values"].update(seal_mode="encryption"), "only the procedural seal is built"),
    (lambda s: s["key_values"]["cuda_ipc"].update(mode="c12"), "c12 needs its record"),
    (lambda s: s["key_values"].update(cap_gpu_hours=300), "above the cap 300"),
    (lambda s: s["key_values"].update(liveness_floor=1.5), "liveness_floor"),
    (lambda s: s["noise_floor"]["ar"].update(copy="docs/x.json"), "PENDING"),
    (lambda s: s["noise_floor"]["seven"].update(run_id="g1b-tasl-20261121-a"), "summary of run"),
    (lambda s: s["decisions"]["G5-W"].update(option="Z"), "decisions.G5-W"),
    (lambda s: s["decisions"].pop("G5-SLOT"), "exactly"),
    (lambda s: s["gate"].update(sha256="0" * 64), "gate"),
    (lambda s: s["pilot_basis"].update(run_id="g4-tasl-x"), "pilot_basis"),
    (lambda s: s.update(label="ENGINEERING_ONLY"), "EVIDENCE"),
    (lambda s: s["campaign"].update(temperature=0.0), "inconsistent with the chosen options"),
    (lambda s: s["memory"].update(modes=["history", "none"]), "inconsistent with the chosen options"),
    (lambda s: s.update(e4_amendment_row="not-a-row"), "PLAN row id"),
])
def test_spec_tampering_stops(fn, match):
    stop(match, T.validate_spec, _edit(fn))


# =============================================================================================== the §11 options
def test_g5_w_b_fields_band_cap_and_launch_refusal():
    s = T.apply_options(SPEC, {"G5-W": "B"})
    assert (s["campaign"]["W_semantics"], s["campaign"]["llm_call_cap"], s["key_values"]["audited_band"]) == \
        ("worker_runs", 80, [150, 240])
    stop(r"project 489.5 GPU-h .* above the cap 425", T.validate_spec, s)          # §2.11 W B row
    s["key_values"]["cap_gpu_hours"] = 540
    out = T.validate_spec(s)
    assert any("worker-run budget" in b for b in out["launch_blockers"])
    assert any("P3" in b and "W_semantics" in b for b in out["launch_blockers"])
    assert T.dates_params(s)["w_semantics"] == "worker_runs"


def test_g5_temp_b_needs_a_pilot_at_zero(monkeypatch):
    """M2: what the pilot ran is read from g4_tasl_spec.json's pilot block; only a re-issued G.4 spec clears P3."""
    s = T.apply_options(SPEC, {"G5-TEMP": "B"})
    assert s["campaign"]["temperature"] == 0.0
    assert [b for b in T.validate_spec(s)["launch_blockers"] if "temperature" in b and "g4_tasl_spec.json" in b]
    declared = copy.deepcopy(s)
    declared["pilot_basis"]["temperature"] = 0.0                # declaring it in the G.5 spec is refused
    stop("not declared here", T.validate_spec, declared)
    reissued = copy.deepcopy(T.g4_spec())
    reissued["pilot"]["temperature"] = 0.0                      # a re-issued G.4 spec whose pilot ran at 0
    monkeypatch.setattr(T, "g4_spec", lambda: reissued)
    assert T.validate_spec(s)["launch_blockers"] == []
    assert "0.0 (G5-TEMP B)" in T.note_lines(s)["temperature"]
    assert T.pilot_settings(json.loads((ROOT / "sweep2/t1_tasl/g4_tasl_spec.json").read_text())) == \
        {"W_semantics": "manager_calls", "W": 20, "memory_modes": ["history"], "temperature": 0.2}


def test_g5_mem_b_doubles_band_and_needs_its_cap_and_c_is_refused():
    s = T.apply_options(SPEC, {"G5-MEM": "B"})
    assert s["memory"] == {"modes": ["history", "none"], "instances_per_mode": 12}
    assert s["key_values"]["audited_band"] == [200, 400] and s["e4_amendment_row"] is None
    stop(r"project 610.7 GPU-h", T.validate_spec, s)
    s["key_values"]["cap_gpu_hours"] = 700
    out = T.validate_spec(s)
    assert [b for b in out["launch_blockers"] if "memory_modes" in b] and out["e4_amendment_needed"] is False
    assert T.dates_params(s)["mem_modes"] == 2
    assert T.note_lines(s)["instances_per_node"] == "12 per memory mode (history, none)"
    assert "e4_amendment_row" not in T.note_lines(s)
    wb = T.apply_options(s, {"G5-W": "B"})
    assert wb["key_values"]["audited_band"] == [300, 480]
    c = T.apply_options(SPEC, {"G5-MEM": "C"})
    assert c["memory"]["instances_per_mode"] == 6
    stop("G5-MEM C is not built", T.validate_spec, c)


def test_g5_audit_b_and_parent_reuse():
    s = T.apply_options(SPEC, {"G5-AUDIT": "B"})
    assert s["audit"]["scope"] == "ok_outcome_only"
    assert T.validate_spec(s)["divergence_denominator_weaker"] is True
    r = copy.deepcopy(SPEC)
    r["audit"]["reuse_parent_runs"] = False
    out = T.validate_spec(r)                                      # §2.4: 349.5 at 0.6, 445.5 at 0.8 (above 425)
    assert out["projection"]["share=0.6 K=10"]["worker_gpu_hours"] == 349.5
    assert out["projection"]["share=0.8 K=10"]["worker_gpu_hours"] == 445.5
    assert "reuse_parent_runs false" in T.note_lines(r)["audit_scope"]


def test_g5_div_options_thresholds():
    assert T.divergence_threshold(SPEC, "mlab_imdb") == {"node": "mlab_imdb", "threshold": 0.2,
                                                         "literal_2x_census": 0.25, "min_audited": 40,
                                                         "rule": "G5-DIV A"}
    b = T.apply_options(SPEC, {"G5-DIV": "B"})
    assert sorted(b["divergence"]["pilot_counts"]) == sorted(SPEC["pilot_basis"]["nodes"])
    out = T.validate_spec(b)
    assert len([x for x in out["launch_blockers"] if "G5-DIV B" in x]) == 3
    b["divergence"]["pilot_counts"]["mlab_cifar10"] = {"divergent": 0, "proposals": 60}
    b["divergence"]["pilot_counts"]["mlgym_fmnist"] = {"divergent": 3, "proposals": 60}
    b["divergence"]["pilot_counts"]["mlgym_breakout_minatar"] = {"divergent": 1, "proposals": 60}
    assert T.validate_spec(b)["launch_blockers"] == []
    t0 = T.divergence_threshold(b, "mlab_cifar10")
    assert abs(t0["cp_upper"] - (1 - 0.025 ** (1 / 60))) < 1e-9 and abs(t0["threshold"] - 2 * t0["cp_upper"]) < 1e-6
    assert T.divergence_threshold(b, "mlgym_fmnist")["threshold"] == 0.2             # capped at 20 %
    assert T.divergence_threshold(b, "mlab_imdb")["threshold"] == 0.2                # not a pilot node
    c = T.apply_options(SPEC, {"G5-DIV": "C"})
    assert len([x for x in T.validate_spec(c)["launch_blockers"] if "G5-DIV C" in x]) == 8
    c["divergence"]["g1b_divergent_rows"]["mlab_imdb"] = {"divergent": 1, "rows": 115}
    assert T.divergence_threshold(c, "mlab_imdb")["threshold"] == round(2 / 115, 6)
    assert T.note_lines(c)["divergence_stop"].startswith("G5-DIV C")
    stop("pilot_counts for exactly", T.validate_spec, _edit(lambda s: s.update(
        divergence=T.apply_options(SPEC, {"G5-DIV": "B"})["divergence"] | {"pilot_counts": {}},
        decisions=s["decisions"] | {"G5-DIV": s["decisions"]["G5-DIV"] | {"option": "B"}})))


def test_clopper_pearson_upper():
    assert T.clopper_pearson_upper(60, 60) == 1.0
    assert abs(T.clopper_pearson_upper(0, 10) - (1 - 0.025 ** 0.1)) < 1e-9
    assert 0.0835 < T.clopper_pearson_upper(2, 60) < 0.1155
    stop("integer counts", T.clopper_pearson_upper, 3, 2)


def test_g5_tasl_gpuh_b_needs_the_server_stopped_during_audits():
    s = T.apply_options(SPEC, {"G5-TASL-GPUH": "B"})
    assert s["cap"]["counts"] == "both_cards" and s["proposer"]["server_stopped_during_audits"] is True
    out = T.validate_spec(s)                     # §2.9: 305 + 55 ≈ 360 at 0.6, 386 + 62 ≈ 448 at 0.8
    assert out["projection"]["share=0.6 K=10"]["capped_gpu_hours"] == 360.4
    assert out["projection"]["share=0.8 K=10"]["capped_gpu_hours"] == 448.3 > 425
    assert "both cards" in T.note_lines(s)["cap_gpu_hours"]
    s["proposer"]["server_stopped_during_audits"] = False
    stop("inconsistent with the chosen options", T.validate_spec, s)
    back = T.apply_options(T.apply_options(SPEC, {"G5-TASL-GPUH": "B"}), {"G5-TASL-GPUH": "A"})
    assert back == SPEC


def test_g5_slot_b_is_not_built():
    stop("G5-SLOT B .* is not built", T.validate_spec, T.apply_options(SPEC, {"G5-SLOT": "B"}))


def test_g5_arpend_b_carries_autoresearch_in_the_spec():
    s = T.apply_options(SPEC, {"G5-ARPEND": "B"})
    ar = T.node_entry(s, T.AR)
    assert ar["env"] == T.AR_FILL_B and s["envs"]["ar-cond7a"]["sha256"].startswith("11def6ad")
    assert s["ar_prerequisites"]["pending"] == [] and s["ar_prerequisites"]["mode"] == "B"
    stop("env must be its G.1b environment", T.validate_spec, s)        # filled at signature
    ar["env"] = "ar-cond7a"
    out = T.validate_spec(s)
    assert out["options"]["G5-ARPEND"] == "B"
    lines = T.note_lines(s)
    assert lines["ar_prerequisites"].startswith("PASS") and "completion record" not in lines["noise_floor"]
    assert T.apply_options(s, {"G5-ARPEND": "A"})["envs"] == SPEC["envs"]


def test_every_option_switches_and_is_reported_unsigned():
    for key in T.DECISIONS:
        for opt in T.OPTIONS[key]:
            s = T.apply_options(SPEC, {key: opt})
            assert s["decisions"][key]["option"] == opt and s["decisions"][key]["signed"] is False
    stop("unknown decision", T.apply_options, SPEC, {"G5-W": "C"})


# =============================================================================================== a launch-ready world
SEVEN_COPY = "docs/r1/reports/rel_t1_g1b_20261205/g1b_tasl_summary.json"
GATE7 = "docs/r1/reports/rel_t1_g1b_20261205/crosscheck_gate.json"
AR_COPY = "docs/r1/reports/rel_t1_g1b_ar_20261205/g1b_tasl_ar_summary.json"
HOST7 = "docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md"
HOSTAR = "docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md"
HOST_T7 = SPEC["tasl7_audits"]["isolation_host_check"]["record"]      # R1-G5-AUDIT-TWO-CARDS (the real record)
XC2_RECORDS = [e["record"] for n in T.X_NODES for e in SPEC["tasl7_audits"]["crosshost_pass"][n]]
PLAN_TEXT = (ROOT / "docs" / "r1" / "PLAN.md").read_text()
UNIT_ROWS = {r: next(ln for ln in PLAN_TEXT.splitlines() if ln.startswith(f"| {r} |"))
             for r in (T.D21_SCOPE_ROW, T.TWO_CARDS_ROW)}           # this unit's rows, as on main 5d4f1b09
RECORD = "docs/r1/reports/g5_ar_20261205/G5_AR_PREREQUISITES_20261205.md"
AR_NOTE = "docs/r1/authorizations/g1b_ar_t1_tasl_20261122.md"
FREEZE = "sweep2/g1b/env/ar-cond7a.freeze.txt"


# D6 A (R1-T1-FEAT-DECISIONS): each summary copy has its run's ASSEMBLY.json and runs.jsonl copied beside it; the
# summary's assembly_sha256 (shared with the seven-node cross-check gate record) is that ASSEMBLY.json's sha256
def g1b_runs_raw(nodes, *, flat=False, nan=False) -> bytes:
    """Synthetic G.1b runs.jsonl (never real values) for the switch's noise pre-check (review m6): per node, c0
    constant at the joint seeds 3001-3003, c1 = c0 + 0.25 + (-2^-6, 0, 2^-6) (material, sd 2^-6), c2 = c0 + (-2^-4, 0,
    2^-4) (sd 2^-4); ``flat``: every paired difference equal (sd 0); ``nan``: one c1 metric NaN."""
    rows = []
    for node in nodes:
        for cfg, base, spread in (("c0", 0.5, 0.0), ("c1", 0.75, 2.0 ** -6), ("c2", 0.5, 2.0 ** -4)):
            for i, sd in enumerate((3001, 3002, 3003)):
                m = base + (0.0 if flat else (i - 1) * spread)
                if nan and cfg == "c1" and i == 0:
                    m = float("nan")
                rows.append({"node": node, "config": cfg, "condition": "joint", "train_seed": sd, "split_seed": sd,
                             "success": True, "metric": m})
    return "".join(json.dumps(r) + "\n" for r in rows).encode()


RUNS_RAW = g1b_runs_raw(list(T.T1_NODES))
ASM_RAW = json.dumps({"schema": "synthetic", "runs_sha256": hashlib.sha256(RUNS_RAW).hexdigest()}).encode()
ASSEMBLY = hashlib.sha256(ASM_RAW).hexdigest()
XC = json.loads((ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json").read_text())
SEALED7 = "/home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-tasl-20261121-b/summary.json"
SEALEDAR = "/home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-ar-tasl-20261122-a/summary.json"


def _gate(**kw):
    rec = {"schema": "g1b_tasl_crosscheck_gate/1", "rule": "R1-T1-TASL-ENV",
           "nodes": {n: {"verdict": f"docs/r1/reports/xc/{n}.json"} for n in XC["nodes"]},
           "g1b_spec_sha256": XC["g1b_spec"]["sha256"], "crosscheck_run_id": XC["run_id"],
           "assembly_json_sha256": ASSEMBLY, "runs_jsonl_sha256": "b" * 64}
    rec.update(kw)
    return json.dumps(rec, indent=1, sort_keys=True).encode()


def _summary(schema, run_id, nodes, qualifies=True, assembly=None):
    return json.dumps({"schema": schema, "label": "ENGINEERING_ONLY", "run_id": run_id,
                       "assembly_sha256": assembly or ASSEMBLY,
                       "verdicts": {n: {"qualifies_D21": qualifies if not isinstance(qualifies, dict)
                                        else qualifies.get(n, True), "n_edits": 2, "paired_joint_n": [3, 3],
                                        "determinism": {"deterministic": True}}       # g1b_lib.summarise's shape
                                    for n in nodes}}, indent=1).encode()


def _host(pin):
    return (f"host_check_host: TASL-2\nhost_check_harness_commit: {pin}\nhost_check_items: 1-7 PASS\n"
            "host_check_verdict: PASS\n").encode()


def run_copies(m, copy_rel, runs_raw=RUNS_RAW):
    """Put the D6 A copies beside a summary copy on the fake main; returns their spec fields and review needles."""
    d = Path(copy_rel).parent
    asm_raw = ASM_RAW if runs_raw == RUNS_RAW else json.dumps({"schema": "synthetic", "runs_sha256": sha(runs_raw)}).encode()
    f = {"assembly_copy": f"{d}/ASSEMBLY.json", "assembly_sha256": sha(asm_raw), "runs_copy": f"{d}/runs.jsonl",
         "runs_sha256": sha(runs_raw)}
    m[f["assembly_copy"]], m[f["runs_copy"]] = asm_raw, runs_raw
    return f, " ".join(f.values())


class Main(dict):
    """Published main as {path: bytes}; ``read`` is the read_main the code takes."""

    def read(self, rel):
        return self.get(rel)

    def on_main(self, rel, raw):
        return self.get(rel) == raw

    def ls(self, prefix=""):
        return sorted(p for p in self if p.startswith(prefix))


T1_FEAT_ROW_TEXT = ("| R1-T1-FEAT-DECISIONS | ARMS-T1FEAT A report §5 (synthetic): D1–D4 A, D8 A (as built); D6 A "
                    "(amending REL-T1-G1B's copy list); D6-σ B; D7 a separate unit; D9 B |")


def _plan_rows(**extra):
    rows = {r: f"| {r} | row text |" for r in T.PLAN_ROWS}
    rows["R1-T1-FEAT-DECISIONS"] = T1_FEAT_ROW_TEXT
    rows.update(UNIT_ROWS)
    rows["R1-G5-SIGN"] = ("| R1-G5-SIGN | " + ", ".join(f"{d} A" for d in T.DECISIONS)
                          + " (the author signs §11; G5-MEM A with R1-G5-E4) |")
    rows["R1-G5-E4"] = "| R1-G5-E4 | amends E4 'both memory modes' for T1: G5-MEM A, history only |"
    rows.update(extra)
    return ("# PLAN\n" + "\n".join(rows.values()) + "\n").encode()


def ready(tmp_path, *, seven_qualifies=True, spec_edit=None, gate=None):
    m = Main()
    seven = _summary("g1b_tasl_summary/1", "g1b-tasl-20261121-b", list(T.SEVEN), seven_qualifies)
    m[SEVEN_COPY] = seven
    m[GATE7] = gate if gate is not None else _gate()
    runs7, needles7 = run_copies(m, SEVEN_COPY)
    m["docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md"] = (
        f"copy {SEVEN_COPY} sha256 {sha(seven)} of the sealed {SEALED7}\n"
        f"gate {GATE7} sha256 {sha(m[GATE7])}\nrun copies {needles7}\n\nVerdict: ACCEPTED\n").encode()
    m["docs/r1/reviews/G5_CODE_REVIEW.md"] = b"Verdict: ACCEPTED\n"
    m["docs/r1/reviews/IMDB_BASELINE_REVIEW.md"] = b"Verdict: ACCEPTED\n"
    m[HOST7] = _host(PC.PIN_SEVEN)
    for rel in [HOST_T7] + XC2_RECORDS:                     # the real TASL-7 host check and xc2 verdicts (on main)
        m[rel] = (ROOT / rel).read_bytes()
    m["docs/r1/PLAN.md"] = _plan_rows()
    s = copy.deepcopy(SPEC)
    s["run_id"] = "c3_t1_labels_20261201"
    s["paper"]["commit"] = "2" * 40
    s["harness_families"]["G5-7"]["g5_commit"] = "7" * 40
    s["harness_families"]["G5-AR"]["g5_commit"] = "8" * 40
    s["harness_families"]["G5-7"]["isolation_host_check"]["sha256"] = sha(m[HOST7])
    for d in s["decisions"].values():
        d["signed"] = True
    s["decisions_row"], s["e4_amendment_row"] = "R1-G5-SIGN", "R1-G5-E4"
    s["noise_floor"]["seven"].update(copy=SEVEN_COPY, sha256=sha(seven), review="docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md",
                                     sealed_path=SEALED7, gate_copy=GATE7, gate_sha256=sha(m[GATE7]), **runs7)
    for n in s["nodes"]:
        if n["node"] != T.AR:
            n["tails"] = "gaussian"
    s["key_values"]["cuda_ipc"]["mode"] = "acceptance"
    s["projection"]["gpu_hours_p7"] = 310.0
    if spec_edit:
        spec_edit(s)
    sp = tmp_path / "g5_spec.json"
    sp.write_text(json.dumps(s, indent=1))
    T.validate_spec(s, launch=True)
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True, exist_ok=True)
    note = d / f"{s['run_id']}.md"
    note.write_bytes(note_text(s, sp))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    return s, sp, note, m


def note_text(s, sp, *, k=10, k_row=None, approved="true", edit=None, freeze=None, freeze_row=None):
    lines = {"approved": approved, **T.note_lines(s, k=k, k_row=k_row, freeze=freeze, freeze_row=freeze_row),
             "paper_commit": s["paper"]["commit"],
             "spec_sha256": T.L._sha_file(sp)}
    ps = {"P1": f"PASS — R1-T1-HOST-TASL: {s['harness_families']['G5-7']['isolation_host_check']['record']}; "
                f"TASL-7 {s['tasl7_audits']['isolation_host_check']['record']}; autoresearch PENDING (G5-ARPEND A)",
          "P2": f"PASS — {s['noise_floor']['seven']['copy']}; autoresearch PENDING (G5-ARPEND A)",
          "P3": f"PASS — the G.4 pilot {s['pilot_basis']['run_id']} with W, memory mode and temperature as decided",
          "P4": "PASS — K = 10 (R1-G5-DECISIONS)", "P5": "PASS — docs/r1/reviews/G5_CODE_REVIEW.md",
          "P6": f"PASS — {s['decisions_row']}", "P7": "PASS — 310.0 GPU-h within 425",
          "P8": "PASS — docs/r1/reviews/IMDB_BASELINE_REVIEW.md", "P9": "PASS — R1-T1-TASL-ENV",
          "P10": "PASS — per node from the G.1b summary", "P11": "PASS — C1-C13"}
    lines.update(ps)
    if edit:
        edit(lines)
    return ("# G.5 note (synthetic)\n\n" + "\n".join(f"{key}: {v}" for key, v in lines.items()) + "\n").encode()


def ar_record_world(m, s, sp, *, edit=None, env=None, review_ok=True, qualifies=True, note_bytes=None,
                    decl=b"autoresearch_fixedtokens: student_t (from the G.1b summary)\n", runs_raw=RUNS_RAW):
    f, needles = run_copies(m, AR_COPY, runs_raw)
    ar = _summary("g1b_tasl_ar_summary/1", "g1b-ar-tasl-20261122-a", [T.AR], qualifies, f["assembly_sha256"])
    m[AR_COPY] = ar
    m["docs/r1/reviews/REL_T1_G1B_AR_COPY_REVIEW.md"] = (f"{AR_COPY} sha256 {sha(ar)} from {SEALEDAR}\n"
                                                          f"run copies {needles}\nVerdict: ACCEPTED\n").encode()
    m[HOSTAR] = _host(PC.PIN_AR)
    m[AR_NOTE] = note_bytes or (ROOT / AR_NOTE).read_bytes()
    m[FREEZE] = (ROOT / FREEZE).read_bytes()
    m["docs/r1/reports/g5_ar_20261205/AR_P10.md"] = decl
    fields = {"schema": "g5_ar_prerequisites/1", "node": T.AR, "g5_spec_sha256": T.L._sha_file(sp),
              "host_check": f"{HOSTAR} sha256 {sha(m[HOSTAR])}", "g1b_note": f"{AR_NOTE} sha256 {sha(m[AR_NOTE])}",
              "g1b_sealed_summary": f"{SEALEDAR} sha256 {sha(ar)}",
              "noise_floor_copy": f"{AR_COPY} sha256 {sha(ar)}",
              "noise_floor_copy_review": "docs/r1/reviews/REL_T1_G1B_AR_COPY_REVIEW.md",
              "d21_verdict": "qualifies" if qualifies else "does_not_qualify", "tails": "student_t",
              "tails_declaration": f"docs/r1/reports/g5_ar_20261205/AR_P10.md sha256 "
                                   f"{sha(m['docs/r1/reports/g5_ar_20261205/AR_P10.md'])}",
              "environment": env or (f"ar-cond7a freeze {FREEZE} sha256 {sha(m[FREEZE])} python 3.12.15 interpreter "
                                     "/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python"),
              "review": "docs/r1/reviews/G5_AR_PREREQUISITES_REVIEW.md", "verdict": "PASS"}
    if edit:
        edit(fields)
    raw = ("# completion record (synthetic)\n" + "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n").encode()
    m[RECORD] = raw
    m["docs/r1/reviews/G5_AR_PREREQUISITES_REVIEW.md"] = (
        f"Reviewed {RECORD} sha256 {sha(raw)}\n" + ("Verdict: ACCEPTED\n" if review_ok else "Verdict: NOT ACCEPTED\n")
    ).encode()
    return raw


def go(sp, note, m, node="mlab_imdb", *, job="campaigns-wave1", today=TODAY, enable=True, calls=None, **kw):
    calls = [] if calls is None else calls

    def runner(spec_path, node_name, job_name, context):
        calls.append((node_name, job_name, context))
        return {"ran": node_name}
    args = dict(on_main=m.on_main, read_main=m.read, list_main=m.ls,
                pin_check=lambda repo, a, b: {"repo": str(repo), "g5_seven": a, "g5_ar": b},
                mpath_check=lambda repo, pin, g5: {"repo": str(repo), "g1b_pin": pin, "g5_commit": g5},
                checkout=lambda spec, fam: {"family": fam},
                launch_binding=lambda repo, s, rows: {"rows": rows}, runner=runner)
    args.update(kw)
    return T.launch(sp, note, node, job=job, enable=enable, today=today, **args)


@pytest.fixture
def keys(monkeypatch):
    monkeypatch.setenv(T.ENABLE_ENV, "1")


# =============================================================================================== the note (§5)
def test_note_key_lines_are_matched_line_by_line(tmp_path):
    s, sp, note, m = ready(tmp_path)
    fields = T.check_note(note, sp, spec=s, on_main=m.on_main, read_main=m.read)
    assert fields["_K"] == 10 and fields["cap_gpu_hours"].startswith("425, counted per the worker card")
    assert fields["e4_amendment_row"] == "R1-G5-E4" and fields["cuda_ipc_acceptance"] == T.CUDA_IPC_ACCEPTANCE
    assert fields["ar_prerequisites"].startswith("PENDING until the completion record")
    for key in T.note_lines(s):                         # every key line is enforced
        note.write_bytes(note_text(s, sp, edit=lambda d, k=key: d.update({k: d[k] + " x"})))
        m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
        stop(rf"differ from the spec.*'{key}'|placeholder|{key} line", T.check_note, note, sp, spec=s, on_main=m.on_main,
             read_main=m.read)


@pytest.mark.parametrize("edit, match", [
    (lambda d: d.update(paper_commit="3" * 40), "paper_commit"),
    (lambda d: d.update(spec_sha256="0" * 64), "spec_sha256"),
    (lambda d: d.update(P6="PASS — some other row"), "P6 must cite"),
    (lambda d: d.update(P1="PASS — R1-T1-HOST-TASL"), "P1 must cite"),
    (lambda d: d.update(P11="PENDING"), "P11 must be PASS|placeholder"),
    (lambda d: d.update(gpu_hours="<P7>"), "placeholder"),
    (lambda d: d.pop("audited_band"), "audited_band"),
])
def test_note_binding_and_prerequisites(tmp_path, edit, match):
    s, sp, note, m = ready(tmp_path)
    note.write_bytes(note_text(s, sp, edit=edit))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    stop(match, T.check_note, note, sp, spec=s, on_main=m.on_main, read_main=m.read)


def test_note_signature_draft_mode_and_name(tmp_path):
    s, sp, note, m = ready(tmp_path)
    stop("byte-identically", T.check_note, note, sp, spec=s, on_main=lambda r, b: False, read_main=m.read)
    note.write_bytes(note_text(s, sp, approved="false"))
    stop("approved: true", T.check_note, note, sp, spec=s, on_main=m.on_main, read_main=m.read)
    assert T.check_note(note, sp, spec=s, read_main=m.read, draft=True)["_K"] == 10      # before signature
    other = note.parent / "c3_t1_labels_20261202.md"
    other.write_bytes(note.read_bytes())
    stop("spec's run_id", T.check_note, other, sp, spec=s, on_main=m.on_main, read_main=m.read)


def test_audit_k_is_read_from_the_note(tmp_path, keys):
    """P4: the K amendment is a docs-only change of the note's audit_K and seed lines; the spec does not change."""
    s, sp, note, m = ready(tmp_path)
    spec_sha = T.L._sha_file(sp)
    note.write_bytes(note_text(s, sp, k=6, k_row="R1-K-CHECK-PASS"))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    stop("R1-K-CHECK-PASS must exist", T.check_note, note, sp, spec=s, on_main=m.on_main, read_main=m.read)
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-K-CHECK-PASS": "| R1-K-CHECK-PASS | sweep-1 subsampling K-check: FAIL |"})
    stop("does not name", T.check_note, note, sp, spec=s, on_main=m.on_main, read_main=m.read)
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-K-CHECK-PASS": "| R1-K-CHECK-PASS | sweep-1 subsampling K-check PASS |"})
    fields = T.check_note(note, sp, spec=s, on_main=m.on_main, read_main=m.read)
    assert (fields["_K"], fields["audit_seeds_label"], fields["audit_seeds_evaluation"]) == (6, "7001-7003", "7006-7008")
    assert T.L._sha_file(sp) == spec_sha
    calls = []
    go(sp, note, m, job="audits-wave1", calls=calls)
    ctx = calls[0][2]
    assert ctx["K"] == 6 and ctx["audit_seeds"] == {"label": [7001, 7002, 7003], "evaluation": [7006, 7007, 7008]}
    assert "R1-K-CHECK-PASS" in ctx["launch"]["rows"]
    # the seed lines left at K = 10 while audit_K says 6: refused
    note.write_bytes(note_text(s, sp, k=6, k_row="R1-K-CHECK-PASS", edit=lambda d: d.update(
        audit_seeds_label="7001-7005", audit_seeds_evaluation="7006-7010")))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    stop("audit_seeds", T.check_note, note, sp, spec=s, on_main=m.on_main, read_main=m.read)
    note.write_bytes(note_text(s, sp, edit=lambda d: d.update(audit_K="8 (whatever)")))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    stop("audit_K line", T.check_note, note, sp, spec=s, on_main=m.on_main, read_main=m.read)


# =============================================================================================== the switch
def test_switch_is_off_by_default_and_needs_both_keys(tmp_path, monkeypatch):
    # runs_root isolated: the runner=None case below reaches g5_job's own checks, which read the runs tree
    s, sp, note, m = ready(tmp_path, spec_edit=lambda x: [x[k].update(runs_root=str(tmp_path / "runs"))
                                                          for k in ("worker", "tasl7_audits")])
    monkeypatch.delenv(T.ENABLE_ENV, raising=False)
    stop("disabled", go, sp, note, m)
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    stop("disabled", go, sp, note, m, enable=False)
    calls = []
    out = go(sp, note, m, calls=calls)
    assert out["ran"] == "mlab_imdb" and calls[0][1] == "campaigns-wave1" and calls[0][2]["K"] == 10
    ctx = calls[0][2]
    assert ctx["host_check"]["G5-7"]["record"] == HOST7 and "R1-G5-SIGN" in ctx["launch"]["rows"]
    assert ctx["measurement_path"] == {"repo": s["harness_families"]["G5-7"]["harness_dir"], "g1b_pin": PC.PIN_SEVEN,
                                       "g5_commit": "7" * 40}
    assert ctx["pin_check"]["g5_seven"] == "7" * 40 and ctx["pin_check"]["g5_ar"] == "8" * 40
    assert "audit_seeds" not in ctx
    stop("needs the proposer.s server_record", go, sp, note, m, runner=None)   # the real runner (3b-1) refuses here
    assert list((tmp_path / "runs" / s["run_id"] / "_refusals").iterdir())        # recorded, in the isolated tree
    stop("job must be one of", go, sp, note, m, job="wave3")
    stop("not a G.5 node", go, sp, note, m, node="mlab_wdbc")


def test_switch_refuses_an_unsigned_or_blocked_spec(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    s2 = copy.deepcopy(s)
    s2["decisions"]["G5-DIV"]["signed"] = False
    sp.write_text(json.dumps(s2))
    stop("not signed", go, sp, note, m)
    s3 = T.apply_options(s, {"G5-TEMP": "B"})
    for d in s3["decisions"].values():
        d["signed"] = True
    sp.write_text(json.dumps(s3))
    stop("cannot launch: P3", go, sp, note, m)


def test_switch_decisions_and_e4_rows(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-G5-SIGN": "| R1-G5-SIGN | G5-W A, G5-TEMP A, G5-MEM AB |"})
    stop("does not name", go, sp, note, m)
    m["docs/r1/PLAN.md"] = _plan_rows()
    rows = _plan_rows().decode().replace("| R1-G5-E4 |", "| R1-G5-E4X |").encode()
    m["docs/r1/PLAN.md"] = rows
    stop("R1-G5-E4 must exist", go, sp, note, m)                     # G5-MEM A needs the E4 amendment row
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-G5-SIGN": "| R1-G5-SIGN | " + ", ".join(f"{d} A" for d in T.DECISIONS)
                                         + " |"})
    stop("R1-G5-SIGN does not name", go, sp, note, m)            # the decisions row must cite the E4 row
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-G5-E4": "| R1-G5-E4 | amends something else for T1 |"})
    stop("R1-G5-E4 does not name", go, sp, note, m)


def test_followup_6_one_row_cannot_serve_as_decisions_and_e4_row(tmp_path, keys):
    """G.5 follow-ups item 6: plan_row strips only the id cell, so one row whose text names its own id, "E4" and
    "memory modes" passes both term checks; decision_row_checks therefore refuses decisions_row == e4_amendment_row
    under G5-MEM A explicitly (the switch STOPs before any job)."""
    both = ("| R1-G5-SIGN | " + ", ".join(f"{d} A" for d in T.DECISIONS)
            + " (with R1-G5-SIGN: amends E4 'both memory modes' for T1, history only) |")
    plan = _plan_rows(**{"R1-G5-SIGN": both})
    spec = dict(SPEC, decisions_row="R1-G5-SIGN", e4_amendment_row="R1-G5-E4")
    o = dict(T.options(spec), **{d: "A" for d in T.DECISIONS})
    terms = dict(T.decision_row_checks(spec, o))
    for term_set in terms.values():                       # the term checks alone would pass the self-citing row
        T.plan_row("R1-G5-SIGN", lambda rel: plan, terms=tuple(t.replace("R1-G5-E4", "R1-G5-SIGN") for t in term_set))
    stop("must be two rows", T.decision_row_checks, dict(spec, e4_amendment_row="R1-G5-SIGN"), o)
    b = dict(o, **{"G5-MEM": "B"})                        # under B there is no E4 row to compare
    assert [r for r, _ in T.decision_row_checks(dict(spec, e4_amendment_row=None), b)] == ["R1-G5-SIGN"]
    s, sp, note, m = ready(tmp_path, spec_edit=lambda s: s.update(e4_amendment_row="R1-G5-SIGN"))
    m["docs/r1/PLAN.md"] = plan
    calls = []
    stop("must be two rows", go, sp, note, m, calls=calls)
    assert calls == []


# =============================================================================================== R1-T1-FEAT-DECISIONS
def test_t1_feat_decisions_row_is_checked_at_launch(tmp_path, keys):
    """The switch STOPs until R1-T1-FEAT-DECISIONS is on published main exactly once, naming D6 A, D6-σ B, D8 A and
    D9 B (the decisions the G.5 code on main implements). plan_row matches each term literally: "D6-σ B" needs the
    ASCII hyphen-minus and the Greek small sigma U+03C3 (UTF-8 in PLAN), and no term may run on into a letter or
    digit."""
    assert T.T1_FEAT_ROW == "R1-T1-FEAT-DECISIONS" and T.T1_FEAT_TERMS == ("D6 A", "D6-σ B", "D8 A", "D9 B")
    assert "D6-\u03c3 B" in T.T1_FEAT_TERMS
    s, sp, note, m = ready(tmp_path)
    calls = []
    go(sp, note, m, calls=calls)
    assert "R1-T1-FEAT-DECISIONS" in calls[0][2]["launch"]["rows"]
    plan = _plan_rows().decode()
    m["docs/r1/PLAN.md"] = plan.replace(T1_FEAT_ROW_TEXT + "\n", "").encode()           # not published yet
    stop("R1-T1-FEAT-DECISIONS must exist exactly once", go, sp, note, m)
    m["docs/r1/PLAN.md"] = (plan + T1_FEAT_ROW_TEXT + "\n").encode()                      # twice
    stop("R1-T1-FEAT-DECISIONS must exist exactly once", go, sp, note, m)
    for bad, missing in (("D6 A", "D6 A"), ("D6-σ B", "D6-σ B"), ("D9 B", "D9 B"), ("D8 A", "D8 A")):
        for variant in {"D6 A": ["D6 B", "D6 AB", "D6A"], "D6-σ B": [
                "D6-σ A", "D6-sigma B", "D6–σ B", "D6‑σ B", "D6-ς B", "D6-Σ B", "D6 σ B", "D6-σ B2"],
                "D9 B": ["D9 A", "D9B"], "D8 A": ["D8 B"]}[bad]:
            row = T1_FEAT_ROW_TEXT.replace(bad, variant, 1)
            assert row != T1_FEAT_ROW_TEXT
            m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-T1-FEAT-DECISIONS": row})
            stop(rf"R1-T1-FEAT-DECISIONS does not name \[{missing!r}\]", go, sp, note, m)
    m["docs/r1/PLAN.md"] = _plan_rows()
    assert go(sp, note, m)["ran"] == "mlab_imdb"
    # the fixture PLAN's row passes plan_row directly, as bytes in UTF-8
    assert T.plan_row("R1-T1-FEAT-DECISIONS", lambda rel: _plan_rows(), terms=T.T1_FEAT_TERMS) == T1_FEAT_ROW_TEXT


def test_plan_row_preceding_boundary_and_negation_limit():
    """Review m5: a term may not run on into a letter or digit on either side; plan_row cannot see negation."""
    row = "| R1-XY | {} |"
    read = lambda text: (lambda rel: ("# PLAN\n" + row.format(text) + "\n").encode())    # noqa: E731
    for text, term in (("XD9 B", "D9 B"), ("AD6 A", "D6 A"), ("2D6-σ B", "D6-σ B"), ("D9 BX", "D9 B"),
                       ("xG5-W A", "G5-W A")):
        stop("does not name", T.plan_row, "R1-XY", read(text), terms=(term,))
    for text in ("(D9 B)", "-D9 B,", "`D9 B`", "D9 B", "ARMS-T1FEAT D9 B; D6-σ B"):
        T.plan_row("R1-XY", read(text), terms=("D9 B",))
    T.plan_row("R1-XY", read("not D9 B"), terms=("D9 B",))           # the limit: negation is not seen


def test_switch_noise_precheck_before_any_job(tmp_path, keys):
    """Review m6: at every job start the switch computes the node's σ_node by T0's definition and δ_n from the run
    copies on main (g5_noise.node_noise, check_usable); a σ_node of 0 or a non-finite value STOPs before the runner."""
    s, sp, note, m = ready(tmp_path)
    calls = []
    go(sp, note, m, calls=calls)
    pre = calls[0][2]["noise_precheck"]
    assert pre == {"node": "mlab_imdb", "sigma_node": 2.0 ** -6, "delta_n": 0.25 * (2.0 ** -6 + 2.0 ** -4) / 2,
                   "runs_sha256": sha(RUNS_RAW)}
    ar_record_world(m, s, sp)
    calls = []
    go(sp, note, m, node=T.AR, calls=calls)
    assert calls[0][2]["noise_precheck"]["node"] == T.AR and calls[0][2]["noise_precheck"]["sigma_node"] == 2.0 ** -6
    for runs, match in ((g1b_runs_raw([T.AR], flat=True), "no positive σ_node by T0's definition"),
                        (g1b_runs_raw([T.AR], nan=True), "non-finite paired sd or median")):
        ar_record_world(m, s, sp, runs_raw=runs)
        calls = []
        stop(match, go, sp, note, m, node=T.AR, calls=calls)
        assert calls == []
    good = dict(T.check_g1b_copy(s["noise_floor"]["seven"], schema="g1b_tasl_summary/1",
                                 run_id="g1b-tasl-20261121-b", nodes=list(T.SEVEN), read_main=m.read))
    assert T.noise_precheck(good, "mlgym_fmnist", m.read)["sigma_node"] == 2.0 ** -6
    stop("not on published main", T.noise_precheck, good, "mlab_imdb", {k: v for k, v in m.items()
                                                                       if k != good["runs_copy"]}.get)


def test_t1_feat_decisions_row_on_this_checkouts_plan():
    """This checkout's PLAN: until the author publishes R1-T1-FEAT-DECISIONS the switch's row check STOPs (every G.5
    job STOPs); once published, the row must pass the term check. Written to pass before and after publication."""
    plan = (Path(__file__).resolve().parents[2] / "docs" / "r1" / "PLAN.md").read_bytes()
    published = any(ln.startswith("| R1-T1-FEAT-DECISIONS |") for ln in plan.decode("utf-8").splitlines())
    if published:
        T.plan_row(T.T1_FEAT_ROW, lambda rel: plan, terms=T.T1_FEAT_TERMS)
    else:
        stop("R1-T1-FEAT-DECISIONS must exist exactly once", T.plan_row, T.T1_FEAT_ROW, lambda rel: plan,
             terms=T.T1_FEAT_TERMS)


def test_spec_carries_the_t1_feat_decisions_fields():
    """D6-σ B: noise_floor.t1_sigma_node is "t0_definition" (the one rule built; the same constant in g5_noise and
    g5_assemble's check); D6 A: the run copies' fields beside the summary copy, PENDING until the copy step (the AR
    copy's under G5-ARPEND A the PENDING marker, under B filled at signature); the t1_table_readings text names
    σ_node by T0's definition."""
    import g5_noise
    nf = SPEC["noise_floor"]
    assert nf["t1_sigma_node"] == T.T1_SIGMA_NODE == g5_noise.T1_SIGMA_NODE == "t0_definition"
    assert all(nf["seven"][k].startswith("PENDING") for k in T.RUN_COPY_KEYS)
    assert all(nf["ar"][k] == T.AR_PENDING for k in T.RUN_COPY_KEYS)
    for value in (None, "sigma_joint", "T0_definition"):
        s = copy.deepcopy(SPEC)
        s["noise_floor"]["t1_sigma_node"] = value
        stop("t1_sigma_node must be 't0_definition'", T.validate_spec, s)
    s = copy.deepcopy(SPEC)
    s["noise_floor"]["seven"]["runs_sha256"] = "not-a-sha"
    stop("noise_floor.seven.runs_sha256 must be a sha256", T.validate_spec, s)
    s = copy.deepcopy(SPEC)
    s["noise_floor"]["ar"]["runs_copy"] = "docs/r1/reports/x/runs.jsonl"
    stop("noise_floor.ar is the PENDING marker", T.validate_spec, s)
    b = T.apply_options(SPEC, {"G5-ARPEND": "B"})
    assert all(b["noise_floor"]["ar"][k] == T.AR_FILL_B for k in T.RUN_COPY_KEYS)
    assert T.apply_options(b, {"G5-ARPEND": "A"})["noise_floor"]["ar"] == SPEC["noise_floor"]["ar"]
    readings = T.TABLE_READINGS["sigma_cmp"]
    assert "dataset.noise_table's definition" in readings and "D6-sigma B" in readings and "joint sigma" not in readings
    assert readings.isascii()


def test_launch_validation_wants_the_run_copies_beside_the_summary_copy(tmp_path):
    for key, other in (("assembly_copy", "docs/r1/reports/other/ASSEMBLY.json"),
                       ("runs_copy", "docs/r1/reports/rel_t1_g1b_20261205/runs_v2.jsonl")):
        stop("assembly_copy and runs_copy must be ASSEMBLY.json and runs.jsonl beside the summary copy", ready,
             tmp_path, spec_edit=lambda x, k=key, o=other: x["noise_floor"]["seven"].update({k: o}))


def test_main_decision_rows_pass_the_switch_row_checks():
    """The rows the author signed on main (R1-G5-DECISIONS-2, R1-G5-MEM-E4; PLAN at 89899f76), read from this
    checkout's PLAN, pass the switch's two row checks under the default options."""
    plan = (Path(__file__).resolve().parents[2] / "docs" / "r1" / "PLAN.md").read_bytes()
    read = lambda rel: plan                                                        # noqa: E731
    spec = dict(SPEC, decisions_row="R1-G5-DECISIONS-2", e4_amendment_row="R1-G5-MEM-E4")
    checks = T.decision_row_checks(spec, T.options(spec))         # the same checks launch() runs
    assert [r for r, _ in checks] == ["R1-G5-DECISIONS-2", "R1-G5-MEM-E4"]
    for row, terms in checks:
        T.plan_row(row, read, terms=terms)


def test_switch_rel_t1_g1b_copy_checks_and_stop_5(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    good = m[SEVEN_COPY]
    m[SEVEN_COPY] = good + b" "
    stop("not on published main with sha256", go, sp, note, m)
    m[SEVEN_COPY] = good
    m["docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md"] = f"copy {SEVEN_COPY} sha256 {sha(good)}\n".encode()
    stop("Verdict: ACCEPTED", go, sp, note, m)
    # R1-T1-D21-SCOPE: a node that does not qualify under D21 is recorded (its D21 value in the context), not STOPped
    s, sp, note, m = ready(tmp_path, seven_qualifies={"mlab_imdb": False})
    calls = []
    assert go(sp, note, m, node="mlab_imdb", calls=calls)["ran"] == "mlab_imdb"
    assert calls[0][2]["d21"]["qualifies_D21"] is False and calls[0][2]["d21"]["selects"] is False
    assert calls[0][2]["d21"]["rule"] == "R1-T1-D21-SCOPE"
    assert T.D21_SCOPE_ROW in calls[0][2]["launch"]["rows"] and T.TWO_CARDS_ROW in calls[0][2]["launch"]["rows"]
    m[SEVEN_COPY] = _summary("g1b_tasl_summary/1", "g1b-tasl-20261121-b", list(T.SEVEN)[:6])
    stop("not on published main|covers", T.check_g1b_copy, s["noise_floor"]["seven"], schema="g1b_tasl_summary/1",
         run_id="g1b-tasl-20261121-b", nodes=list(T.SEVEN), read_main=m.read)


def test_switch_stop_13_pin_check_and_family_checkout(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)

    def bad_pin(repo, a, b):
        raise PC.Stop("STOP: the G.5 commits differ outside the pin delta")
    stop("STOP 13: STOP: the G.5 commits differ", go, sp, note, m, pin_check=bad_pin)

    def git(argv, **kw):                      # the G5-7 checkout is at the G5-AR commit
        out = ("8" * 40 + "\n") if "rev-parse" in argv else ""
        return subprocess.CompletedProcess(argv, 0, out, "")
    stop(r"STOP 13: G5-7: .*not the pin " + "7" * 40, go, sp, note, m,
         checkout=lambda spec, fam: T.family_checkout(spec, fam, git=git))

    def git_ok(argv, **kw):
        out = ("7" * 40 + "\n") if "rev-parse" in argv else ""
        return subprocess.CompletedProcess(argv, 0, out, "")
    assert T.family_checkout(s, "G5-7", git=git_ok)["commit"] == "7" * 40

    def mp(repo, pin, g5):
        raise T.Stop("STOP: the measurement path differs")
    stop("measurement path differs", go, sp, note, m, mpath_check=mp)
    stop("another commit", go, sp, note, m, mpath_check=lambda r, p, g: {"g5_commit": "9" * 40})


def test_switch_stop_14_freeze_wait(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    assert go(sp, note, m, today=date(2026, 12, 17))["ran"]
    stop("STOP 14: the freeze-wait release deadline 2026-12-18 is reached", go, sp, note, m, today=date(2026, 12, 18))
    assert T.freeze_wait_check(s, today=TODAY, released=list(T.T1_NODES), before_arms_frozen=True)["released"]
    stop(r"WAIT \(not yet\): the train/dev release of \['autoresearch_fixedtokens'\]", T.freeze_wait_check, s,
         today=TODAY, released=list(T.SEVEN), before_arms_frozen=True)
    stop(r"STOP 14: the release deadline 2026-12-18 has passed \(2026-12-18\)", T.freeze_wait_check, s,
         today=date(2026, 12, 18), released=list(T.SEVEN), before_arms_frozen=True)
    stop("STOP 14: nodes STOPped at G.5", T.freeze_wait_check, s, today=TODAY, released=list(T.SEVEN),
         stopped=[T.AR], before_arms_frozen=True)
    stop("unknown nodes", T.freeze_wait_check, s, today=TODAY, released=["x"], before_arms_frozen=True)


def test_switch_stop_15_exactly_one_reviewed_record(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    assert go(sp, note, m, node="mlab_cifar10")["ran"]                 # the seven nodes do not wait for it
    stop(r"STOP 15: exactly one completion record .* found 0", go, sp, note, m, node=T.AR)
    ar_record_world(m, s, sp)
    calls = []
    assert go(sp, note, m, node=T.AR, calls=calls)["ran"] == T.AR
    ctx = calls[0][2]
    assert ctx["ar_environment"]["name"] == "ar-cond7a" and ctx["ar_tails"] == "student_t"
    assert ctx["host_check"]["G5-AR"]["record"] == HOSTAR and ctx["ar_record"]["record"] == RECORD
    assert ctx["measurement_path"]["g1b_pin"] == PC.PIN_AR and ctx["measurement_path"]["g5_commit"] == "8" * 40
    assert ctx["measurement_path"]["repo"] == s["harness_families"]["G5-AR"]["harness_dir"]
    m["docs/r1/reports/g5_ar_20261206/G5_AR_PREREQUISITES_20261206.md"] = m[RECORD]     # a second record
    stop(r"STOP 15: exactly one completion record .* found 2", go, sp, note, m, node=T.AR)


@pytest.mark.parametrize("edit, match", [
    (lambda f: f.update(g5_spec_sha256="0" * 64), "g5_spec_sha256"),
    (lambda f: f.update(verdict="FAIL"), "verdict"),
    (lambda f: f.pop("tails"), "PENDING items"),
    (lambda f: f.update(host_check=f["host_check"][:-1] + "0"), "host_check"),
    (lambda f: f.update(g1b_sealed_summary="/x/summary.json sha256 " + "1" * 64), "byte-identical"),
    (lambda f: f.update(d21_verdict="does_not_qualify"), "d21_verdict"),
    (lambda f: f.update(tails="laplace"), "tails"),
    (lambda f: f.update(noise_floor_copy_review="docs/r1/reviews/MISSING.md"), "review"),
    (lambda f: f.update(g1b_note=f"{HOSTAR} sha256 " + "0" * 64), "g1b_note"),
    (lambda f: f.update(environment="ar-cond7a freeze x"), "environment must read"),
    (lambda f: f.update(review="docs/r1/reviews/OTHER.md"), "review must be on main"),
    (lambda f: f.update(extra="<FILL>"), "unfilled"),
])
def test_stop_15_record_contents(tmp_path, keys, edit, match):
    s, sp, note, m = ready(tmp_path)
    ar_record_world(m, s, sp, edit=edit)
    stop(match, go, sp, note, m, node=T.AR)


def test_stop_15_review_verdict_and_other_environment(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    ar_record_world(m, s, sp, review_ok=False)
    stop("Verdict: ACCEPTED", go, sp, note, m, node=T.AR)
    other = (f"ar-cond7b freeze {FREEZE} sha256 {sha((ROOT / FREEZE).read_bytes())} python 3.12.15 interpreter "
             "/home/dowling/r1_trackp/venvs/ar-cond7b/bin/python")
    ar_record_world(m, s, sp, env=other)
    stop("needs environment_row", go, sp, note, m, node=T.AR)
    ar_record_world(m, s, sp, env=other, edit=lambda f: f.update(environment_row="R1-AR-ENV-G5"))
    stop("R1-AR-ENV-G5 must exist", go, sp, note, m, node=T.AR)
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-AR-ENV-G5": "| R1-AR-ENV-G5 | ar-cond7b for autoresearch's G.1b |"})
    stop("does not name", go, sp, note, m, node=T.AR)
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-AR-ENV-G5": "| R1-AR-ENV-G5 | ar-cond7b for autoresearch's G.1b and G.5 |"})
    calls = []
    go(sp, note, m, node=T.AR, calls=calls)
    assert calls[0][2]["ar_environment"]["interpreter"].endswith("ar-cond7b/bin/python")
    assert "R1-AR-ENV-G5" in calls[0][2]["launch"]["rows"]


def test_stop_5_for_autoresearch_from_its_record(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    ar_record_world(m, s, sp, qualifies=False)          # a complete, reviewed record whose D21 verdict is negative
    calls = []                                          # R1-T1-D21-SCOPE: recorded, not STOPped
    assert go(sp, note, m, node=T.AR, calls=calls)["ran"] == T.AR
    assert calls[0][2]["d21"]["qualifies_D21"] is False
    m[AR_COPY] = _summary("g1b_tasl_ar_summary/1", "g1b-ar-tasl-20261122-a", [T.AR])   # copy changed after review
    stop("STOP 15: noise_floor_copy", go, sp, note, m, node=T.AR)


def test_import_sources_are_the_reviewed_files():
    out = T.check_import_sources()
    assert out["g5_tasl"] == "sweep2/t1_tasl/g5_tasl.py" and out["g1b_tasl"] == "sweep2/t1_tasl/g1b_tasl.py"


# =============================================================================================== P5 measurement path
def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          capture_output=True, text=True, check=True).stdout.strip()


def _commit(repo, files, msg, parent=None):
    if parent:
        _git(repo, "checkout", "-q", "-f", "--detach", parent)
    for rel, text in files.items():
        p = repo / rel
        if text is None:
            p.unlink()
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def harness(tmp_path):
    repo = tmp_path / "h"
    repo.mkdir()
    _git(repo, "init", "-q")
    pin = _commit(repo, {
        "src/autoresearch/__init__.py": "",
        "src/autoresearch/trackg/__init__.py": "extra = 1\ndiagnostics_g5 = None\n",
        "src/autoresearch/trackg/noise_floor.py": ("from autoresearch.trackg import runner, extra, diagnostics_g5\n"
                                                   "from autoresearch.common.util import f\n"
                                                   "def g():\n    from .outcome import OK\n"),
        "src/autoresearch/trackg/runner.py": "import json\n",
        "src/autoresearch/trackg/outcome.py": "OK = 1\n",
        "src/autoresearch/trackg/manager_v2_diff.py": "m = 0\n",
        "src/autoresearch/common/__init__.py": "",
        "src/autoresearch/common/util.py": "def f(): pass\n",
        "src/autoresearch/other/unrelated.py": "u = 0\n",
        "nodes/cifar/node.py": "c\n", "configs/trackg/nodes/cifar.yaml": "a: 1\n", "README.md": "r\n"}, "pin")
    return repo, pin


def test_measurement_path_closure_and_allowed_changes(harness):
    repo, pin = harness
    closure = T.import_closure(repo, pin)
    assert closure == {"src/autoresearch/__init__.py", "src/autoresearch/trackg/__init__.py",
                       "src/autoresearch/trackg/noise_floor.py", "src/autoresearch/trackg/runner.py",
                       "src/autoresearch/trackg/outcome.py", "src/autoresearch/common/__init__.py",
                       "src/autoresearch/common/util.py"}
    g5 = _commit(repo, {"src/autoresearch/trackg/manager_v2_diff.py": "m = 1\n",           # an engine file
                        "src/autoresearch/trackg/audit_g5.py": "from autoresearch.trackg import runner\n",  # new
                        "src/autoresearch/other/unrelated.py": "u = 1\n", "README.md": "r2\n"}, "g5", pin)
    out = T.measurement_path_check(repo, pin, g5)
    assert out["closure_outside_trackg"] == ["src/autoresearch/__init__.py", "src/autoresearch/common/__init__.py",
                                             "src/autoresearch/common/util.py"]
    assert out["g5_added"] == ["src/autoresearch/trackg/audit_g5.py"] and out["engine_files_in_closure"] == []


@pytest.mark.parametrize("files, match", [
    ({"nodes/cifar/node.py": "c2\n"}, "measurement path differs.*nodes/cifar/node.py"),
    ({"configs/trackg/nodes/cifar.yaml": None}, "measurement path differs.*cifar.yaml"),
    ({"src/autoresearch/common/util.py": "def f(): return 1\n"}, "measurement path differs.*common/util.py"),
    ({"src/autoresearch/trackg/outcome.py": "OK = 2\n"}, "measurement path differs.*outcome.py"),
    ({"src/autoresearch/trackg/diagnostics_g5.py": "x = 1\n"}, "import closure changed.*trackg/diagnostics_g5.py"),
    ({"src/autoresearch/trackg/extra.py": "x = 1\n"}, "adds files inside the measurement directories.*extra.py"),
    ({"nodes/cifar/json.py": "x\n"}, "adds files .*nodes/cifar/json.py"),
    ({"configs/trackg/nodes/new.yaml": "a: 1\n"}, "adds files .*new.yaml"),
    ({"src/autoresearch/trackg/node_lib/helper.py": "x\n"}, "adds files .*node_lib/helper.py"),
    ({"third_party/mlgym/nodes/x/extra.py": "x\n"}, "adds files .*third_party"),
])
def test_measurement_path_violations_stop(harness, files, match):
    repo, pin = harness
    g5 = _commit(repo, files, "g5", pin)
    stop(match, T.measurement_path_check, repo, pin, g5)


def test_measurement_path_mode_change_and_ancestry(harness):
    repo, pin = harness
    (repo / "src/autoresearch/trackg/runner.py").chmod(0o755)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chmod")
    stop("measurement path differs.*runner.py", T.measurement_path_check, repo, pin, _git(repo, "rev-parse", "HEAD"))
    _git(repo, "checkout", "-q", "--orphan", "other")
    (repo / "x").write_text("x")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "unrelated")
    stop("does not descend", T.measurement_path_check, repo, pin, _git(repo, "rev-parse", "HEAD"))


def test_measurement_path_on_the_real_pins():
    root = os.environ.get("AR_HARNESS_ROOT")
    if not root or subprocess.run(["git", "-C", root, "cat-file", "-e", PC.PIN_AR + "^{commit}"],
                                  capture_output=True).returncode != 0:
        pytest.skip("the harness repo with both pins is not available (set AR_HARNESS_ROOT)")
    for pin in (PC.PIN_SEVEN, PC.PIN_AR):
        out = T.measurement_path_check(Path(root), pin, pin)
        assert out["engine_files_in_closure"] == [] and "src/autoresearch/trackg/runner.py" in out["closure"]
    # §2.12 / P5: the AR pin's ar_isolated change fails the check against c025f89a (why G5-PIN arose)
    stop(r"measurement path differs .*node_lib/ar_isolated.py", T.measurement_path_check, Path(root), PC.PIN_SEVEN,
         PC.PIN_AR)


# =============================================================================================== dates, CLI
def test_dates_params_are_eight_nodes_with_autoresearch_unscaled():
    p = T.dates_params(SPEC)
    assert p["t1_nodes"] == list(T.T1_NODES) and p["ratio_exempt_nodes"] == [T.AR]
    assert p["pilot_nodes"] == ["mlab_cifar10", "mlgym_fmnist", "mlgym_breakout_minatar"]
    assert (p["w_semantics"], p["mem_modes"], p["reuse_parent_runs"], p["g5_cap_gpu_hours"]) == \
        ("manager_calls", 1, True, 425)
    r = T.T4.recompute_dates({}, p, today=date(2026, 11, 22))
    assert r["g5_total_gpu_hours"] == 305.3 and r["nodes_from_census_unscaled"] == [T.AR]


def _g4b_pilot(tmp_path: Path, **pilot) -> Path:
    g4 = T.g4_spec()
    g4b = copy.deepcopy(g4)
    g4b["harness"].update(commit="9" * 40, g1b_pin=g4["harness"]["commit"], pin_rule="R1-G5-DIFF-RECOUNT")
    g4b["run_id"] = "g4b-tasl-20261124-a"
    g4b["worker"]["harness_dir"] += "_g4b"
    g4b["pilot"].update(pilot)
    path = tmp_path / f"g4b_{len(list(tmp_path.iterdir()))}.json"
    path.write_text(json.dumps(g4b))
    return path


def test_dates_reads_the_g4b_pilot_spec_only_with_g4_settings(tmp_path, capsys):
    """R1-G5-DIFF-RECOUNT: ``dates --pilot-spec`` reads the G.4b re-pilot's sealed attempts against the G.4b spec; the
    default stays g4_tasl_spec.json; a spec that is not G.4b, or runs other pilot settings than P3 reads, is refused."""
    g4, g4sha = T.dates_pilot_spec(None)
    assert g4["run_id"] == "g4-tasl-20261121-a" and g4sha == T.L._sha_file(T.HERE / "g4_tasl_spec.json")
    p = _g4b_pilot(tmp_path)
    got, got_sha = T.dates_pilot_spec(p)
    assert got["run_id"] == "g4b-tasl-20261124-a" and got_sha == T.L._sha_file(p)
    plain = tmp_path / "g4_copy.json"
    plain.write_text(json.dumps(g4))
    stop("--pilot-spec is for the G.4b re-pilot spec", T.dates_pilot_spec, plain)
    stop("must run the G.4 pilot's settings", T.dates_pilot_spec, _g4b_pilot(tmp_path, memory_mode="none"))
    assert T.main(["dates", str(SPEC_PATH), "--today", "2026-11-25", "--pilot-spec", str(p)]) == 0
    assert json.loads(capsys.readouterr().out)["g5_total_gpu_hours"] == 305.3        # pre-pilot: no sealed attempt
    assert T.main(["dates", str(SPEC_PATH), "--today", "2026-11-25", "--pilot-spec", str(plain)]) == 2


def test_cli(tmp_path, capsys):
    assert T.main(["validate", str(SPEC_PATH)]) == 0
    assert json.loads(capsys.readouterr().out)["options"] == ALL_A
    assert T.main(["validate", str(SPEC_PATH), "--launch"]) == 2
    capsys.readouterr()
    assert T.main(["options", str(SPEC_PATH), "--set", "G5-SLOT=B"]) == 0
    slot_b = tmp_path / "slot_b.json"
    slot_b.write_text(capsys.readouterr().out)
    assert T.main(["validate", str(slot_b)]) == 2 and "not built" in capsys.readouterr().err
    assert T.main(["key-lines", str(SPEC_PATH)]) == 0
    out = capsys.readouterr().out
    assert "audit_K: 10 (R1-G5-DECISIONS;" in out and "freeze_wait:" in out and "cap_gpu_hours: 425," in out
    assert T.main(["freeze-wait", str(SPEC_PATH), "--today", "2026-12-18"]) == 2


# =============================================================================================== review round 1
C12 = "docs/r1/reports/trackg_g0_20261117/TASL2_C12_CUDA_IPC_20261205.md"


def _c12_spec(s, raw, review=None):
    s["key_values"]["cuda_ipc"].update(mode="c12", c12_record=C12, c12_sha256=sha(raw), c12_review=review)


def test_m1_c12_record_is_read_from_main(tmp_path, keys):
    good = b"c12_host: TASL-2\nc12_item: 7 PASS\nc12_verdict: PASS\n"
    s, sp, note, m = ready(tmp_path, spec_edit=lambda x: _c12_spec(x, good))
    assert T.note_lines(s)["cuda_ipc"] == f"C12 PASS: {C12} sha256 {sha(good)}" and \
        "cuda_ipc_acceptance" not in T.note_lines(s)
    stop(r"C12 record .* is not on published main", go, sp, note, m)                       # missing record
    m[C12] = good + b"\n"
    stop("differs from its declared sha256", go, sp, note, m)                             # wrong sha256
    m[C12] = good
    calls = []
    go(sp, note, m, calls=calls)
    assert calls[0][2]["cuda_ipc"]["fields"]["c12_verdict"] == "PASS"
    for bad in (b"c12_host: TASL-2\nc12_verdict: FAIL\n", b"c12_host: TASL-7\nc12_verdict: PASS\n",
                b"c12_host: TASL-2\n"):                                                   # non-PASS / other host
        s, sp, note, m = ready(tmp_path, spec_edit=lambda x, b=bad: _c12_spec(x, b))
        m[C12] = bad
        stop("does not read a PASS", go, sp, note, m)
    prose = b"# C12 on TASL-2\nItem 7 tested; see captures.\n"                            # format not fixed yet
    s, sp, note, m = ready(tmp_path, spec_edit=lambda x: _c12_spec(x, prose))
    m[C12] = prose
    stop("no c12_review names it", go, sp, note, m)
    rev = "docs/r1/reviews/C12_REVIEW.md"
    s, sp, note, m = ready(tmp_path, spec_edit=lambda x: _c12_spec(x, prose, rev))
    m[C12] = prose
    m[rev] = f"{C12} sha256 {sha(prose)}\nVerdict: NOT ACCEPTED\n".encode()
    stop("C12_REVIEW.md of the C12 record", go, sp, note, m)
    m[rev] = f"{C12} sha256 {sha(prose)}\nVerdict: ACCEPTED\n".encode()
    calls = []
    go(sp, note, m, calls=calls)
    assert calls[0][2]["cuda_ipc"]["review"] == rev


@pytest.mark.parametrize("gate, match", [
    (_gate(assembly_json_sha256="c" * 64), "assembly_json_sha256"),
    (_gate(schema="other/1"), "schema"),
    (_gate(nodes={"mlab_cifar10": {}}), "nodes"),
    (_gate(crosscheck_run_id="g1b-tasl-20261121-b-xc"), "crosscheck_run_id"),
    (_gate(g1b_spec_sha256="0" * 64), "g1b_spec_sha256"),
])
def test_m3_seven_copy_needs_its_cross_check_gate(tmp_path, keys, gate, match):
    s, sp, note, m = ready(tmp_path, gate=gate)
    stop(rf"does not bind this summary's assembly.*{match}", go, sp, note, m)


def test_m3_gate_copy_on_main_beside_the_summary_and_reviewed(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    good = m.pop(GATE7)
    stop("cross-check gate copy .* is not on published main", go, sp, note, m)
    m[GATE7] = good
    m["docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md"] = (f"copy {SEVEN_COPY} sha256 {sha(m[SEVEN_COPY])} of the sealed "
                                                       f"{SEALED7}\nVerdict: ACCEPTED\n").encode()
    stop("must be on published main, name", go, sp, note, m)                          # the review omits the gate
    stop("beside the summary copy", ready, tmp_path, spec_edit=lambda x: x["noise_floor"]["seven"].update(
        gate_copy="docs/r1/reports/other/crosscheck_gate.json"))
    assert "g1b_tasl_join.py floor-by-node" in T.note_lines(s)["noise_floor"]
    assert f"cross-check gate record {GATE7} sha256" in T.note_lines(s)["noise_floor"]


def test_m3_autoresearch_jobs_join_the_floors_by_node(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    ar_record_world(m, s, sp)
    calls = []
    go(sp, note, m, node=T.AR, calls=calls)
    floor = calls[0][2]["floor_by_node"]
    assert floor["schema"] == "g1b_tasl_floor_by_node/1" and sorted(floor["nodes"]) == sorted(T.T1_NODES)
    assert floor["nodes"][T.AR]["summary"] == AR_COPY and floor["nodes"]["mlab_imdb"]["summary"] == SEVEN_COPY


def test_m1_minor_record_checks(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    ar_record_world(m, s, sp)                       # (a) the copy's review must name the sealed path
    m["docs/r1/reviews/REL_T1_G1B_AR_COPY_REVIEW.md"] = (f"{AR_COPY} sha256 {sha(m[AR_COPY])}\n"
                                                          "Verdict: ACCEPTED\n").encode()
    stop(f"name .*{SEALEDAR}", go, sp, note, m, node=T.AR)
    for decl in (b"autoresearch_fixedtokens: gaussian\n", b"mlab_imdb: student_t\n",
                 b"autoresearch_fixedtokens: student_t, not gaussian\n"):       # (b) the declaration's content
        ar_record_world(m, s, sp, decl=decl)
        stop("tails declaration .* must name autoresearch_fixedtokens with student_t", go, sp, note, m, node=T.AR)
    real = (ROOT / AR_NOTE).read_bytes()             # (c) the third note binds the AR G.1b spec this spec binds
    assert b"spec_sha256: " + s["harness_families"]["G5-AR"]["g1b_spec"]["sha256"].encode() in real
    ar_record_world(m, s, sp, note_bytes=real.replace(b"spec_sha256: 65da95db", b"spec_sha256: 00da95db"))
    stop("binding the autoresearch G.1b spec", go, sp, note, m, node=T.AR)
    assert s["ar_prerequisites"]["pending"] == ["host_check", "noise_floor_copy", "environment", "tails"]
    ar_record_world(m, s, sp, edit=lambda f: f.pop("host_check"))
    stop(r"PENDING items \['host_check'\]", go, sp, note, m, node=T.AR)


@pytest.mark.parametrize("extra", ["docs/r1/reports/g5_ar_20261206/G5_AR_PREREQUISITES_20261206_v2.md",
                                   "docs/r1/reports/a/b/G5_AR_PREREQUISITES_20261206.md",
                                   "docs/r1/G5_AR_PREREQUISITES_20261206.md"])
def test_m2_near_miss_record_names_stop(tmp_path, keys, extra):
    s, sp, note, m = ready(tmp_path)
    ar_record_world(m, s, sp)
    m[extra] = m[RECORD]
    stop(r"STOP 15: paths on published main that name G5_AR_PREREQUISITES", go, sp, note, m, node=T.AR)


def test_m3_freeze_date_read_from_the_note(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    spec_sha = T.L._sha_file(sp)
    assert T.note_lines(s)["freeze_wait"].endswith("until 2026-12-18; no G.5 job starts on or after this date (STOP 14)")
    note.write_bytes(note_text(s, sp, freeze="2026-12-22", freeze_row="R1-FREEZE-MOVE"))   # docs-only amendment
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    stop("R1-FREEZE-MOVE must exist", go, sp, note, m, today=date(2026, 12, 20))
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-FREEZE-MOVE": "| R1-FREEZE-MOVE | G.5 freeze wait moved |"})
    stop("does not name", go, sp, note, m, today=date(2026, 12, 20))
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-FREEZE-MOVE": "| R1-FREEZE-MOVE | G.5 freeze wait moved to 2026-12-22 |"})
    calls = []
    go(sp, note, m, today=date(2026, 12, 20), calls=calls)
    assert calls[0][2]["freeze_wait"]["deadline"] == "2026-12-22"
    stop("STOP 14: the freeze-wait release deadline 2026-12-22", go, sp, note, m, today=date(2026, 12, 22))
    assert T.L._sha_file(sp) == spec_sha                               # the spec did not change
    note.write_bytes(note_text(s, sp, edit=lambda d: d.update(freeze_wait=d["freeze_wait"].replace(
        "2026-12-18", "2026-12-22"))))                                   # another date without a row
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    stop("needs the author row", go, sp, note, m)
    note.write_bytes(note_text(s, sp, edit=lambda d: d.update(freeze_wait="until 2026-12-18 (STOP 14)")))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    stop("freeze_wait line is not in the required form", go, sp, note, m)


def test_m5_launch_under_arpend_b(tmp_path, keys):
    ar = _summary("g1b_tasl_ar_summary/1", "g1b-ar-tasl-20261122-a", [T.AR])
    review = "docs/r1/reviews/REL_T1_G1B_AR_COPY_REVIEW.md"

    def to_b(x):
        b = T.apply_options(x, {"G5-ARPEND": "B"})
        for d in b["decisions"].values():
            d["signed"] = True
        node = T.node_entry(b, T.AR)
        node.update(env="ar-cond7a", tails="student_t")
        b["harness_families"]["G5-AR"]["isolation_host_check"] = {"record": HOSTAR, "sha256": sha(_host(PC.PIN_AR))}
        b["noise_floor"]["ar"].update(copy=AR_COPY, sha256=sha(ar), review=review, sealed_path=SEALEDAR,
                                      **run_copies(Main(), AR_COPY)[0])
        x.clear()
        x.update(b)
    s, sp, note, m = ready(tmp_path, spec_edit=to_b)
    assert T.note_lines(s)["ar_prerequisites"].startswith("PASS")
    m[HOSTAR] = _host(PC.PIN_AR)
    m[AR_COPY] = ar
    stop(r"does not name \['G5-ARPEND B'\]", go, sp, note, m, node=T.AR)      # the row must sign B
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-G5-SIGN": "| R1-G5-SIGN | " + ", ".join(
        f"{d} {'B' if d == 'G5-ARPEND' else 'A'}" for d in T.DECISIONS) + " (G5-MEM A with R1-G5-E4) |"})
    stop("copies of the G.1b run's ASSEMBLY.json and runs.jsonl must be on published main", go, sp, note, m, node=T.AR)
    _, needles = run_copies(m, AR_COPY)                                  # D6 A: the run copies beside the AR copy
    stop(f"review {review}", go, sp, note, m, node=T.AR)
    m[review] = f"{AR_COPY} sha256 {sha(ar)} from {SEALEDAR}\nVerdict: ACCEPTED\n".encode()
    stop(f"review {review}", go, sp, note, m, node=T.AR)                 # the review must name the run copies (D6 A)
    m[review] = f"{AR_COPY} sha256 {sha(ar)} from {SEALEDAR}\n{needles}\nVerdict: ACCEPTED\n".encode()
    calls = []
    go(sp, note, m, node=T.AR, calls=calls)                            # no completion record needed under B
    assert calls[0][2]["noise_floor"]["ar"]["runs_copy"] == str(Path(AR_COPY).parent / "runs.jsonl")
    ctx = calls[0][2]
    assert ctx["host_check"]["G5-AR"]["record"] == HOSTAR and "ar_record" not in ctx
    assert sorted(ctx["floor_by_node"]["nodes"]) == sorted(T.T1_NODES)
    m[HOSTAR] = _host(PC.PIN_SEVEN)                       # the AR host check replaced (here: at the wrong pin)
    stop("differs from its declared sha256", go, sp, note, m, node=T.AR)


def test_m5_plan_row_duplicate_and_id():
    plan = _plan_rows().decode() + "| R1-G5-SIGN | again |\n"
    stop("exactly once", T.plan_row, "R1-G5-SIGN", lambda rel: plan.encode())
    stop("not a PLAN row id", T.plan_row, "G5-SIGN", lambda rel: plan.encode())
    assert T.plan_row("R1-G5-E4", lambda rel: plan.encode(), terms=("E4", "memory modes"))


def test_m6_wording_checkouts_and_cited_reviews(tmp_path, keys):
    assert SPEC["campaign"]["per_call_seed_rule"] == 'sha256(f"{manager_seed}:{step}")[:8]' == T.SEED_RULE
    assert T.note_lines(SPEC)["temperature"].endswith('per-call seed sha256(f"{manager_seed}:{step}")[:8]')
    b = T.apply_options(SPEC, {"G5-DIV": "B"})
    assert "two-sided 95 % Clopper-Pearson interval (upper tail 2.5 %)" in T.note_lines(b)["divergence_stop"]
    for d in ("/home/dowling/r1_tracks/t1_tasl/harness_ar", T.g4_spec()["worker"].get("harness_dir")
              or "/home/dowling/r1_tracks/t1_tasl/harness"):
        stop("G.1b or G.4 checkout", T.validate_spec, _edit(lambda x, d=d: x["harness_families"]["G5-7"].update(
            harness_dir=d)))
    s, sp, note, m = ready(tmp_path)
    m["docs/r1/reviews/IMDB_BASELINE_REVIEW.md"] = b"Verdict: NOT ACCEPTED\n"
    stop("P8 cites docs/r1/reviews/IMDB_BASELINE_REVIEW.md", go, sp, note, m)
    m.pop("docs/r1/reviews/IMDB_BASELINE_REVIEW.md")
    stop("P8 cites", go, sp, note, m)
    m["docs/r1/reviews/IMDB_BASELINE_REVIEW.md"] = b"Verdict: ACCEPTED\n"
    m.pop("docs/r1/reviews/G5_CODE_REVIEW.md")
    stop("P5 cites", go, sp, note, m)


def test_cited_reviews_must_name_a_review_file(tmp_path, keys):
    """P5 and P8 must cite at least one review file: a bare 'docs/r1/reviews/' with no file checks nothing (round-2 m1)."""
    for key in ("P5", "P8"):
        (tmp_path / key).mkdir()
        s, sp, note, m = ready(tmp_path / key)
        note.write_bytes(note_text(s, sp, edit=lambda x, key=key: x.update(
            {key: "PASS — docs/r1/reviews/ (G.5 code review, round 2)"})))
        m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
        stop(f"{key} must cite a review file", go, sp, note, m)


# =============================================================================================== R1-T1-D21-SCOPE
DET_FAILED = {"qualifies_D21": False, "reason": "fixed-seed determinism failed",
              "determinism": {"deterministic": False}, "divergent": {"rows": 0, "by_config": {}}}


def _seven_with(m, s, verdicts):
    """Rewrite the seven-node copy on the fake main with the given verdict overrides; rebinding the spec is not needed
    for check_g1b_copy's result, so the copy and its review are rewritten together."""
    raw = json.loads(m[SEVEN_COPY])
    raw["verdicts"].update(verdicts)
    m[SEVEN_COPY] = json.dumps(raw, indent=1).encode()
    return m[SEVEN_COPY]


def test_d21_scope_verdict_record_and_determinism():
    """g1b_verdict_scope records the D21 value (JSON-safe) and decides only on fixed-seed determinism; no threshold."""
    v = {"qualifies_D21": False, "n_material": 1, "mean_p_wrong_material": float("nan"), "n_edits": 4,
         "checks": {"material_edits_ge_2": False, "mean_p_wrong_ge_0.10": False}, "determinism": {"deterministic": True}}
    sc = T.g1b_verdict_scope("mlab_imdb", v)
    assert sc["deterministic"] is True and sc["d21"]["qualifies_D21"] is False and sc["d21"]["n_material"] == 1
    assert sc["d21"]["mean_p_wrong_material"] is None and sc["d21"]["selects"] is False
    json.dumps(sc, allow_nan=False)
    assert T.require_deterministic("mlab_imdb", v)["d21"]["checks"]["material_edits_ge_2"] is False
    for bad in (DET_FAILED, {"qualifies_D21": True}, {"qualifies_D21": True, "determinism": {"deterministic": "yes"}},
                {"qualifies_D21": True, "determinism": {"deterministic": True}, "reason": T.DETERMINISM_FAILED}):
        with pytest.raises(T.NodeStop, match="STOP 5: mlab_imdb has no G.1b fixed-seed determinism PASS"):
            T.require_deterministic("mlab_imdb", bad)


def test_d21_scope_determinism_and_cross_host_still_stop(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    raw = _seven_with(m, s, {"mlab_imdb": DET_FAILED})
    s["noise_floor"]["seven"]["sha256"] = sha(raw)
    sp.write_text(json.dumps(s, indent=1))
    note.write_bytes(note_text(s, sp))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    review = m["docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md"].decode()           # the review names the new bytes
    m["docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md"] = (f"copy {SEVEN_COPY} sha256 {sha(raw)}\n" + review).encode()
    with pytest.raises(T.NodeStop, match="STOP 5: mlab_imdb has no G.1b fixed-seed determinism PASS"):
        go(sp, note, m, node="mlab_imdb")
    assert go(sp, note, m, node="mlab_cifar10")["ran"] == "mlab_cifar10"       # only that node STOPs
    # the G.1b cross-host gate (where run) still STOPs: a gate record that does not name the TASL-7 nodes
    (tmp_path / "g").mkdir()
    s, sp, note, m = ready(tmp_path / "g", gate=_gate(nodes={"mlab_cifar10": {}}))
    stop("does not bind this summary's assembly and the TASL-7 nodes", go, sp, note, m, node="mlab_imdb")


def test_d21_scope_non_qualifying_node_without_usable_sigma_still_stops(tmp_path, keys):
    """A non-qualifying node runs, but σ_node by T0's definition (the fallback to all edits with an sd, here none
    material) must still be finite and > 0: flat runs (sd 0) STOP before the job."""
    s, sp, note, m = ready(tmp_path)
    ar_record_world(m, s, sp, qualifies=False, runs_raw=g1b_runs_raw([T.AR], flat=True))
    calls = []
    stop("no positive σ_node by T0's definition", go, sp, note, m, node=T.AR, calls=calls)
    assert calls == []


def test_d21_scope_rows_are_required_on_main(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    for row in (T.D21_SCOPE_ROW, T.TWO_CARDS_ROW):
        rows = dict(UNIT_ROWS)
        rows.pop(row)
        plan = ("# PLAN\n" + "\n".join([f"| {r} | row text |" for r in T.PLAN_ROWS] + [T1_FEAT_ROW_TEXT]
                                        + list(rows.values()) + [
            "| R1-G5-SIGN | " + ", ".join(f"{d} A" for d in T.DECISIONS) + " (G5-MEM A with R1-G5-E4) |",
            "| R1-G5-E4 | amends E4 'both memory modes' for T1: G5-MEM A, history only |"]) + "\n").encode()
        m["docs/r1/PLAN.md"] = plan
        stop(f"the PLAN row {row} must exist exactly once", go, sp, note, m)


# =============================================================================================== R1-G5-AUDIT-TWO-CARDS
SHORT_DIR = "docs/r1/reports/tasl_chain_20261122"         # the xc3 unit's names (coordinator, 25 Nov; not final)


def short_verdict(name, **kw):
    """An xc3 short-check verdict in the shape the coordinator gave: schema g1b_tasl_crosscheck_verdict/1, mode short,
    rule R1-G5-AUDIT-TWO-CARDS, sides with run_id, spec_sha256, job_record_sha256 and attempt (no value)."""
    side = {"run_id": "g1b-tasl-20261121-b-xc3-{h}", "spec_sha256": "3" * 64, "job_record_sha256": "4" * 64,
            "attempt": 1}
    v = {"schema": "g1b_tasl_crosscheck_verdict/1", "node": name, "mode": "short", "verdict": "PASS", "reason": None,
         "rule": "R1-G5-AUDIT-TWO-CARDS", "harness_commit": PC.PIN_SEVEN,
         "g1b_spec_sha256": SPEC["harness_families"]["G5-7"]["g1b_spec"]["sha256"], "g1b_run_id": "g1b-tasl-20261121-b",
         "crosscheck_run_id": "g1b-tasl-20261121-b-xc3",
         "sides": {h: dict(side, run_id=side["run_id"].format(h=h)) for h in ("TASL-7", "TASL-2")}}
    v.update(kw)
    return json.dumps(v, indent=1, sort_keys=True).encode()


def put_short(m, node, raw=None, *, date_="20261125"):
    rel = f"{SHORT_DIR}/G1B_XC3_SHORT_VERDICT_{node}_{date_}.json"
    m[rel] = raw if raw is not None else short_verdict(node)
    return rel


def test_two_cards_spec_block_and_pending_markers():
    t = SPEC["tasl7_audits"]
    assert t["families"] == ["G5-7"] and T.AR not in t["crosshost_pass"] and t["lease"] == SPEC["proposer"]["lease"]
    assert t["gpu_uuid"] == SPEC["proposer"]["gpu_uuid"] and t["runs_root"] == SPEC["worker"]["runs_root"]
    assert sorted(T.validate_spec(copy.deepcopy(SPEC))["tasl7_pending_crosshost"]) == \
        ["mlab_imdb", "mlab_ogbn_arxiv", "mlgym_fmnist", "mlgym_houseprice"]
    for n in ("mlab_imdb", "mlab_ogbn_arxiv", "mlgym_fmnist", "mlgym_houseprice"):
        assert t["crosshost_pass"][n] == f"PENDING short cross-check: {n}"
    for n in T.X_NODES:                                       # both xc2 verdicts, bound by sha256 to the files on main
        got = {e["mode"]: e for e in t["crosshost_pass"][n]}
        assert set(got) == {"xc", "preassembly"}
        for e in got.values():
            assert sha((ROOT / e["record"]).read_bytes()) == e["sha256"]
    assert SPEC["slots"] == {"worker_slots": 1, "worker_host": "TASL-2", "audit_hosts": ["TASL-2", "TASL-7"]}
    lines = T.note_lines(SPEC)
    assert "PENDING short cross-check: mlab_imdb" in lines["tasl7_audits"] and HOST_T7 in lines["tasl7_audits"]
    assert "R1-T1-D21-SCOPE" in lines["t1_node_scope"] and "one GPU model" in lines["gpu_model"]


@pytest.mark.parametrize("fn, match", [
    (lambda t: t["crosshost_pass"].update({T.AR: "PENDING short cross-check: autoresearch_fixedtokens"}), "seven nodes"),
    (lambda t: t["crosshost_pass"].update(mlab_cifar10="PENDING short cross-check: mlab_cifar10"), "xc2 verdicts"),
    (lambda t: t["crosshost_pass"]["mlab_cifar10"].pop(), "exactly its xc2"),
    (lambda t: t["crosshost_pass"].update(mlab_imdb="PENDING"), "list of PASS records"),
    (lambda t: t["crosshost_pass"].update(mlab_imdb=[{"record": "docs/r1/reports/x.json", "sha256": "1" * 64,
                                                       "mode": "preassembly", "crosscheck_run_id": "r"}]), "xc"),
    (lambda t: t.update(lease="~/r1_locks/gpu1.lock"), "lease"),
    (lambda t: t.update(families=["G5-7", "G5-AR"]), "families"),
    (lambda t: t.update(harness_dir="/home/dowling/r1_tracks/t1_tasl/harness"), "harness_dir"),
    (lambda t: t.update(gpu_uuid=SPEC["worker"]["gpu_uuid"]), "gpu_uuid"),
    (lambda t: t["isolation_host_check"].update(sha256="0" * 64), "isolation_host_check"),
    (lambda t: t.update(extra="x"), "unknown fields"),
])
def test_two_cards_spec_tampering_stops(fn, match):
    s = copy.deepcopy(SPEC)
    fn(s["tasl7_audits"])
    stop(match, T.validate_spec, s)


def test_two_cards_slot_amendment_is_bound():
    s = copy.deepcopy(SPEC)
    s["slots"]["audit_hosts"] = ["TASL-2"]
    stop("inconsistent with the chosen options", T.validate_spec, s)
    stop("G5-SLOT B .* is not built", T.validate_spec, T.apply_options(SPEC, {"G5-SLOT": "B"}))


def test_two_cards_tasl7_audit_launch_needs_the_cross_host_pass(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    calls = []
    go(sp, note, m, node="mlab_cifar10", job="audits-wave1", host="TASL-7", chunk=1, calls=calls)
    ctx = calls[0][2]
    assert ctx["host"] == "TASL-7" and ctx["chunk"] == 1 and ctx["crosshost_pass"]["source"] == "spec"
    assert sorted(r["mode"] for r in ctx["crosshost_pass"]["records"]) == ["preassembly", "xc"]
    assert ctx["host_check"]["TASL-7"]["record"] == HOST_T7 and "g1b_crosshost_gate" in ctx
    # refusals: campaigns, autoresearch, no chunk / chunk on TASL-2
    stop("only audit chunks run on TASL-7", go, sp, note, m, node="mlab_cifar10", host="TASL-7", chunk=1)
    stop("audits stay on TASL-2", go, sp, note, m, node=T.AR, job="audits-wave1", host="TASL-7", chunk=1)
    stop("names its claimed chunk", go, sp, note, m, node="mlab_cifar10", job="audits-wave1", host="TASL-7")
    stop("names its claimed chunk", go, sp, note, m, node="mlab_cifar10", job="audits-wave1", chunk=1)
    # an xc2 record changed on main, or a STOP verdict: refused
    rec = XC2_RECORDS[0]
    good = m[rec]
    m[rec] = good + b" "
    stop("is not on published main with sha256", go, sp, note, m, node="mlab_cifar10", job="audits-wave1",
         host="TASL-7", chunk=1)
    m[rec] = good
    m.pop(HOST_T7)                                            # the TASL-7 host check record is required on main
    stop("not on published main", go, sp, note, m, node="mlab_cifar10", job="audits-wave1", host="TASL-7", chunk=1)


def test_two_cards_pending_node_runs_on_tasl2_not_on_tasl7_until_its_pass(tmp_path, keys):
    """A PENDING node: TASL-2 not blocked; TASL-7 fails closed until its xc3 short PASS is on main; accepted from main
    without a spec change; a STOP verdict or any other shape keeps only its TASL-7 chunks off (XC3-FAIL A)."""
    s, sp, note, m = ready(tmp_path)
    kw = dict(node="mlab_imdb", job="audits-wave1")
    assert go(sp, note, m, **kw)["ran"] == "mlab_imdb"                         # TASL-2: not blocked
    stop(r"PENDING short cross-check: mlab_imdb: no cross-host PASS record", go, sp, note, m, host="TASL-7", chunk=0,
         **kw)
    rel = put_short(m, "mlab_imdb")
    calls = []
    go(sp, note, m, host="TASL-7", chunk=0, calls=calls, **kw)                       # accepted without a spec change
    assert calls[0][2]["crosshost_pass"] == {"node": "mlab_imdb", "source": "main",
                                             "records": [{"record": rel, "sha256": sha(m[rel]), "mode": "short",
                                                          "crosscheck_run_id": "g1b-tasl-20261121-b-xc3"}]}
    sides_bad = json.loads(short_verdict("mlab_imdb"))["sides"]
    sides_bad["TASL-2"].pop("job_record_sha256")
    for bad, match in ((dict(verdict="STOP", reason="cross_host_mismatch"), "verdict"),
                       (dict(mode="xc"), "mode"), (dict(rule="R1-T1-TASL-ENV"), "rule"),
                       (dict(node="mlab_ogbn_arxiv"), "node"), (dict(g1b_spec_sha256="0" * 64), "g1b_spec_sha256"),
                       (dict(sides={"TASL-7": sides_bad["TASL-7"]}), "sides"), (dict(sides=sides_bad), "sides"),
                       (dict(complete=False), "complete"), (dict(label="EVIDENCE"), "label")):
        put_short(m, "mlab_imdb", short_verdict("mlab_imdb", **bad))
        with pytest.raises(T.Stop, match=rf"not a cross-host PASS of mlab_imdb.*{match}.*XC3-FAIL A") as exc:
            go(sp, note, m, host="TASL-7", chunk=0, **kw)
        assert not isinstance(exc.value, T.NodeStop)                          # a refusal, not a node STOP
        assert go(sp, note, m, **kw)["ran"] == "mlab_imdb"                    # TASL-2 still runs it (XC3-FAIL A)
    put_short(m, "mlab_imdb")
    put_short(m, "mlab_imdb", date_="20261126")                                     # two verdicts: refused
    stop("2 short cross-check verdicts of mlab_imdb", go, sp, note, m, host="TASL-7", chunk=0, **kw)
    m.pop(f"{SHORT_DIR}/G1B_XC3_SHORT_VERDICT_mlab_imdb_20261126.json")
    m[f"{SHORT_DIR}/sub/G1B_XC3_SHORT_VERDICT_mlab_imdb_20261127.json"] = b"{}"       # a near-miss name: refused
    stop("but are not", go, sp, note, m, host="TASL-7", chunk=0, **kw)
