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
AR_COPY = "docs/r1/reports/rel_t1_g1b_20261205/g1b_tasl_ar_summary.json"
HOST7 = "docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md"
HOSTAR = "docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md"
RECORD = "docs/r1/reports/g5_ar_20261205/G5_AR_PREREQUISITES_20261205.md"
AR_NOTE = "docs/r1/authorizations/g1b_ar_t1_tasl_20261122.md"
FREEZE = "sweep2/g1b/env/ar-cond7a.freeze.txt"


ASSEMBLY = "a" * 64          # the assembly sha256 the seven-node summary and its cross-check gate record share
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


def _summary(schema, run_id, nodes, qualifies=True):
    return json.dumps({"schema": schema, "label": "ENGINEERING_ONLY", "run_id": run_id, "assembly_sha256": ASSEMBLY,
                       "verdicts": {n: {"qualifies_D21": qualifies if not isinstance(qualifies, dict)
                                        else qualifies.get(n, True)} for n in nodes}}, indent=1).encode()


def _host(pin):
    return (f"host_check_host: TASL-2\nhost_check_harness_commit: {pin}\nhost_check_items: 1-7 PASS\n"
            "host_check_verdict: PASS\n").encode()


class Main(dict):
    """Published main as {path: bytes}; ``read`` is the read_main the code takes."""

    def read(self, rel):
        return self.get(rel)

    def on_main(self, rel, raw):
        return self.get(rel) == raw

    def ls(self, prefix=""):
        return sorted(p for p in self if p.startswith(prefix))


def _plan_rows(**extra):
    rows = {r: f"| {r} | row text |" for r in T.PLAN_ROWS}
    rows["R1-G5-SIGN"] = "| R1-G5-SIGN | " + ", ".join(f"{d} A" for d in T.DECISIONS) + " (the author signs §11) |"
    rows["R1-G5-E4"] = "| R1-G5-E4 | amends E4 'both memory modes' for T1: G5-MEM A, history only |"
    rows.update(extra)
    return ("# PLAN\n" + "\n".join(rows.values()) + "\n").encode()


def ready(tmp_path, *, seven_qualifies=True, spec_edit=None, gate=None):
    m = Main()
    seven = _summary("g1b_tasl_summary/1", "g1b-tasl-20261121-b", list(T.SEVEN), seven_qualifies)
    m[SEVEN_COPY] = seven
    m[GATE7] = gate if gate is not None else _gate()
    m["docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md"] = (
        f"copy {SEVEN_COPY} sha256 {sha(seven)} of the sealed {SEALED7}\n"
        f"gate {GATE7} sha256 {sha(m[GATE7])}\n\nVerdict: ACCEPTED\n").encode()
    m["docs/r1/reviews/G5_CODE_REVIEW.md"] = b"Verdict: ACCEPTED\n"
    m["docs/r1/reviews/IMDB_BASELINE_REVIEW.md"] = b"Verdict: ACCEPTED\n"
    m[HOST7] = _host(PC.PIN_SEVEN)
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
                                     sealed_path=SEALED7, gate_copy=GATE7, gate_sha256=sha(m[GATE7]))
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
                "autoresearch PENDING (G5-ARPEND A)",
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
                    decl=b"autoresearch_fixedtokens: student_t (from the G.1b summary)\n"):
    ar = _summary("g1b_tasl_ar_summary/1", "g1b-ar-tasl-20261122-a", [T.AR], qualifies)
    m[AR_COPY] = ar
    m["docs/r1/reviews/REL_T1_G1B_AR_COPY_REVIEW.md"] = (f"{AR_COPY} sha256 {sha(ar)} from {SEALEDAR}\n"
                                                          "Verdict: ACCEPTED\n").encode()
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
    s, sp, note, m = ready(tmp_path)
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
    stop("part 3b", go, sp, note, m, runner=None)                  # no job yet: the default runner refuses
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


def test_switch_rel_t1_g1b_copy_checks_and_stop_5(tmp_path, keys):
    s, sp, note, m = ready(tmp_path)
    good = m[SEVEN_COPY]
    m[SEVEN_COPY] = good + b" "
    stop("not on published main with sha256", go, sp, note, m)
    m[SEVEN_COPY] = good
    m["docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md"] = f"copy {SEVEN_COPY} sha256 {sha(good)}\n".encode()
    stop("Verdict: ACCEPTED", go, sp, note, m)
    s, sp, note, m = ready(tmp_path, seven_qualifies={"mlab_imdb": False})
    with pytest.raises(T.NodeStop, match="STOP 5: mlab_imdb does not qualify"):
        go(sp, note, m, node="mlab_imdb")
    assert go(sp, note, m, node="mlab_cifar10")["ran"] == "mlab_cifar10"     # only that node STOPs
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
    with pytest.raises(T.NodeStop, match="STOP 5: autoresearch_fixedtokens does not qualify"):
        go(sp, note, m, node=T.AR)
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
        b["noise_floor"]["ar"].update(copy=AR_COPY, sha256=sha(ar), review=review, sealed_path=SEALEDAR)
        x.clear()
        x.update(b)
    s, sp, note, m = ready(tmp_path, spec_edit=to_b)
    assert T.note_lines(s)["ar_prerequisites"].startswith("PASS")
    m[HOSTAR] = _host(PC.PIN_AR)
    m[AR_COPY] = ar
    stop(r"does not name \['G5-ARPEND B'\]", go, sp, note, m, node=T.AR)      # the row must sign B
    m["docs/r1/PLAN.md"] = _plan_rows(**{"R1-G5-SIGN": "| R1-G5-SIGN | " + ", ".join(
        f"{d} {'B' if d == 'G5-ARPEND' else 'A'}" for d in T.DECISIONS) + " |"})
    stop(f"review {review}", go, sp, note, m, node=T.AR)
    m[review] = f"{AR_COPY} sha256 {sha(ar)} from {SEALEDAR}\nVerdict: ACCEPTED\n".encode()
    calls = []
    go(sp, note, m, node=T.AR, calls=calls)                            # no completion record needed under B
    ctx = calls[0][2]
    assert ctx["host_check"]["G5-AR"]["record"] == HOSTAR and "ar_record" not in ctx
    assert sorted(ctx["floor_by_node"]["nodes"]) == sorted(T.T1_NODES)
    m[HOSTAR] = _host(PC.PIN_SEVEN)                       # the AR host check replaced (here: at the wrong pin)
    stop("differs from its declared sha256", go, sp, note, m, node=T.AR)


def test_m5_plan_row_duplicate_and_id():
    plan = _plan_rows().decode() + "| R1-G5-SIGN | again |\n"
    stop("exactly once", T.plan_row, "R1-G5-SIGN", lambda rel: plan.encode())
    stop("not a PLAN row id", T.plan_row, "G5-SIGN", lambda rel: plan.encode())
    assert T.plan_row("R1-G5-E4", lambda rel: plan.encode(), terms=("E4", "G5-MEM"))


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
