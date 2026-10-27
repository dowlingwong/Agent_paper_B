"""Track P 1.8: P.3 selection rule v2 (spec §5.7; R1-EXAM-RULE-V2) on synthetic exam results. ENGINEERING_ONLY;
AI-assisted (Claude)."""
from __future__ import annotations

import hashlib
import json
import shutil

import numpy as np
import pytest

from r1.c3.train import exam_analyze as X

N_INST, PER = 30, 5


def _items():
    return {f"i{k:03d}": f"s{k // PER}" for k in range(N_INST * PER)}


def _base(items):
    rng = np.random.default_rng(0)
    return {i: float(0.2 + 0.05 * rng.random()) for i in items}


def _model(name, family, skill, items, base, *, noise=0.002, seed=1, e2=0.1, width=1.0, ckpt="base", cost=1.0,
           e0=(0.9, 0.95, 0.5), oom=False, det=True, e6=None, e7=None, **kw):
    """Per-item RPS = base * (1 - skill) + small item noise, for 3 seeds."""
    rng = np.random.default_rng(seed)
    rps = {str(s): {i: base[i] * (1 - skill) + noise * rng.standard_normal() for i in items} for s in range(3)}
    m = {"model": name, "family": family, "checkpoint": ckpt,
         "e0": None if e0 is None else {"protocol": "trackp_e0/v2", "width_slope_vs_label": e0[0],
                                        "mean_slope": e0[1], "width_slope_vs_label_lb95": e0[2] if len(e0) > 2 else 0.5},
         "e2": {"val_rps_skill": e2}, "e3": {"rps": rps, "width_ratio": width},
         "e4": {"oom": oom, "reload_deterministic": det, "cost_s": cost}, "e6": e6, "e7": e7}
    m.update(kw)
    return m


def _data(*models):
    items = _items()
    return {"schema": X.SCHEMA, "items": items, "base_rate_rps": _base(items), "models": list(models)}


@pytest.fixture
def env():
    items = _items()
    return items, _base(items)


def _run(env, *specs):
    items, base = env
    return X.analyze({"schema": X.SCHEMA, "items": items, "base_rate_rps": base,
                      "models": [_model(*s[:3], items, base, **s[3]) for s in specs]})


def test_rule_file_hash_matches_committed():
    rule, digest = X.load_rule()
    assert digest == hashlib.sha256(X.RULE_PATH.read_bytes()).hexdigest()
    assert rule["bootstrap"]["resamples"] == 2000 and rule["bootstrap"]["alpha"] == 0.05
    assert rule["version"] == "p3_rule/v2" and rule["e0_protocol"] == "trackp_e0/v2"
    assert rule["e0_pass"] == {"width_slope_vs_label_min": 0.6, "width_slope_vs_label_lb95_gt": 0.0,
                               "mean_slope_min": 0.8}
    assert rule["finalists"]["e2_tie_tolerance"] == 0.01 and rule["pending_author_families"] == []
    assert rule["e6"]["a4_min_frac_monotone_vs_label"] == 0.95


def test_rule_v1_is_refused():
    with pytest.raises(X.RuleSuperseded, match="v2 only"):
        X.load_rule(X.RULE_PATH.with_name("p3_rule_v1.yaml"))


def test_hash_mismatch_is_refused(tmp_path, env):
    p = tmp_path / "p3_rule_v2.yaml"
    shutil.copy(X.RULE_PATH, p)
    shutil.copy(str(X.RULE_PATH) + ".sha256", str(p) + ".sha256")
    p.write_text(p.read_text().replace("resamples: 2000", "resamples: 200"))
    with pytest.raises(X.RuleHashError):
        X.load_rule(p)
    items, base = env
    with pytest.raises(X.RuleHashError):
        X.analyze(_data(_model("kev", "kev", 0.2, items, base)), rule_path=p)


def test_skill_definition(env):
    items, base = env
    m = _model("kev", "kev", 0.3, items, base, noise=0.0)
    res = X.analyze(_data(m))
    assert res["records"]["kev"]["e3_skill"] == pytest.approx(0.3, abs=1e-12)


def test_step1_discards_e0_and_e4_failures_only(env):
    res = _run(env,
               ("kev", "kev", 0.30, {}),
               ("laya_w", "laya", 0.40, {"e0": (0.59, 0.95), "seed": 2}),
               ("laya_m", "laya", 0.40, {"e0": (0.9, 0.79), "seed": 3}),
               ("laya_lb", "laya", 0.40, {"e0": (0.7, 0.95, 0.0), "seed": 7}),
               ("laya_ok", "laya", 0.10, {"e0": (0.6, 0.8, 0.01), "seed": 8}),
               ("extra_oom", "extra", 0.40, {"oom": True, "seed": 4}),
               ("extra_det", "extra", 0.40, {"det": False, "seed": 5}),
               ("extra_e6", "extra", 0.25, {"e6": {"A1": False, "A2": True, "A3": False}, "seed": 6}))
    assert res["discarded"] == {"laya_w": ["e0_width_slope"], "laya_m": ["e0_mean_slope"],
                                "laya_lb": ["e0_width_slope_lb95"],
                                "extra_oom": ["e4_oom"], "extra_det": ["e4_reload_nondeterministic"]}
    assert res["ranking"] == ["kev", "extra_e6", "laya_ok"]          # thresholds are inclusive (>=), lb strict (>)
    r = res["records"]["extra_e6"]
    assert r["e6_failed"] == ["A1", "A3"] and r["packing_disabled"]
    assert not res["records"]["kev"]["packing_disabled"]


def test_ranking_tied_set_and_clear_loser(env):
    res = _run(env,
               ("kev", "kev", 0.300, {"seed": 1, "noise": 0.02}),
               ("laya", "laya", 0.300, {"seed": 2, "noise": 0.02}),
               ("extra", "extra", 0.10, {"seed": 3}))
    assert res["ranking"][2] == "extra" and set(res["ranking"][:2]) == {"kev", "laya"}
    other = res["ranking"][1]
    assert res["comparisons_vs_top"][other]["tied"]
    assert not res["comparisons_vs_top"]["extra"]["tied"]
    assert set(res["tied_set"]) == {"kev", "laya"}


def test_second_finalist_by_sequential_tie_breaks(env):
    tie = {"noise": 0.02}
    # finalist 1 = E3 point top even with the worse E2 (R1-EXAM-RULE-V2)
    r = _run(env, ("kev", "kev", 0.300, {**tie, "seed": 1, "e2": 0.1}), ("laya", "laya", 0.299, {**tie, "seed": 2, "e2": 0.2}))
    assert r["ranking"] == ["kev", "laya"] and r["finalists"] == ["kev", "laya"]   # v1 would have put laya first
    # among tied models of another class: E2 decides beyond the 0.01 tolerance
    r = _run(env, ("kev", "kev", 0.300, {**tie, "seed": 1}),
             ("laya", "laya", 0.299, {**tie, "seed": 2, "e2": 0.10, "width": 1.0}),
             ("ext", "extra", 0.299, {**tie, "seed": 3, "e2": 0.13, "width": 1.5}))
    assert r["ranking"][0] == "kev" and r["finalists"] == ["kev", "ext"]
    # E2 within 0.01: tied on E2, width ratio closer to 1 decides
    r = _run(env, ("kev", "kev", 0.300, {**tie, "seed": 1}),
             ("laya", "laya", 0.299, {**tie, "seed": 2, "e2": 0.105, "width": 1.0}),
             ("ext", "extra", 0.299, {**tie, "seed": 3, "e2": 0.110, "width": 1.5}))
    assert r["ranking"][0] == "kev" and r["finalists"] == ["kev", "laya"]
    assert [t["key"] for t in r["second_finalist_trace"]] == ["e2_probe_skill", "width_ratio_distance"]


def test_pick_second_filters_in_order():
    rule = X.load_rule()[0]
    m = lambda name, e2, w=1.0, ck="base", cost=1.0: {"model": name, "e2": {"val_rps_skill": e2},  # noqa: E731
                                                     "e3": {"width_ratio": w}, "checkpoint": ck, "e4": {"cost_s": cost}}
    assert X._pick_second(rule, [m("a", 0.20), m("b", 0.25)])[0]["model"] == "b"
    assert X._pick_second(rule, [m("a", 0.20, w=0.9), m("b", 0.209, w=1.3)])[0]["model"] == "a"
    assert X._pick_second(rule, [m("a", 0.2, ck="instruct"), m("b", 0.2)])[0]["model"] == "b"
    assert X._pick_second(rule, [m("a", 0.2, cost=3.0), m("b", 0.2, cost=1.0)])[0]["model"] == "b"
    pick, trace = X._pick_second(rule, [m("b", 0.2), m("a", 0.2)])
    assert pick["model"] == "a" and trace[-1]["key"] == "model_name"
    assert X._pick_second(rule, [{**m("a", 0.2), "e2": None}, m("b", 0.0)])[0]["model"] == "b"   # missing E2 = worst
    assert X._pick_second(rule, []) == (None, [])


def test_second_finalist_needs_a_different_class(env):
    tie = {"noise": 0.02}
    r = _run(env, ("kev08", "kev", 0.300, {**tie, "seed": 1, "e2": 0.3}), ("kev4", "kev", 0.300, {**tie, "seed": 2, "e2": 0.2}),
             ("laya", "laya", 0.300, {**tie, "seed": 3, "e2": 0.1}))
    assert set(r["tied_set"]) == {"kev08", "kev4", "laya"}
    assert r["ranking"][0] == "kev08" and r["finalists"] == ["kev08", "laya"]
    r = _run(env, ("kev08", "kev", 0.300, {**tie, "seed": 1}), ("kev4", "kev", 0.299, {**tie, "seed": 2}),
             ("laya", "laya", 0.05, {"seed": 3}))
    assert r["finalists"] == [r["ranking"][0]] and r["ranking"][0] in ("kev08", "kev4")


def test_control_always_carried_never_counts(env):
    r = _run(env, ("kev", "kev", 0.30, {"seed": 1}),
             ("q08", "qwen_control", 0.20, {"seed": 2}),
             ("q4", "qwen_control", 0.35, {"seed": 3, "e0": (0.1, 0.1, 0.5)}))
    assert r["control"] == "q4"
    assert "q4" not in r["ranking"] and "q4" not in r["finalists"] and "q4" not in r["discarded"]
    assert r["records"]["q4"]["step1_failures"] == ["e0_width_slope", "e0_mean_slope"]


def test_startlux_is_a_candidate_without_an_author_rung(env):
    r = _run(env, ("kev", "kev", 0.2, {"seed": 1}), ("slx", "startlux", 0.4, {"seed": 2}))
    assert r["top"] == "slx" and "slx" not in r["discarded"]                  # R1-STARTLUX-TRAINABLE


def test_floor_stop_and_pass(env):
    r = _run(env, ("kev", "kev", 0.10, {"seed": 1}), ("q4", "qwen_control", 0.10, {"seed": 2}),
             ("gbdt", "floor", 0.10, {"seed": 3, "e0": None}), ("ordlr", "floor", 0.05, {"seed": 4, "e0": None}))
    assert r["floor_check"]["floor"] == "gbdt" and r["floor_check"]["stop_escalate"]
    r = _run(env, ("kev", "kev", 0.30, {"seed": 1}), ("gbdt", "floor", 0.10, {"seed": 3, "e0": None}))
    assert not r["floor_check"]["stop_escalate"] and r["floor_check"]["llm_vs_floor"]["kev"]["significant"]
    r = _run(env, ("kev", "kev", 0.30, {"seed": 1}))
    assert r["floor_check"]["stop_escalate"] and r["floor_check"]["reason"] == "no floor result"


def test_head_form_from_e7(env):
    tie = {"noise": 0.02}
    r = _run(env, ("kev", "kev", 0.3, {**tie, "seed": 1, "e7": {"softmax_12": 0.30, "cumulative_11": 0.32}}),
             ("laya", "laya", 0.299, {**tie, "seed": 2, "e2": 0.05, "e7": {"softmax_12": 0.3, "cumulative_11": 0.3}}))
    assert r["head_forms"] == {"kev": "cumulative_11", "laya": "softmax_12"}


def test_bootstrap_is_deterministic_and_cli(tmp_path, env):
    items, base = env
    d = _data(_model("kev", "kev", 0.3, items, base, seed=1), _model("laya", "laya", 0.29, items, base, seed=2, noise=0.02),
              _model("gbdt", "floor", 0.1, items, base, seed=3, e0=None))
    assert X.analyze(d) == X.analyze(d)
    p = tmp_path / "res.json"
    p.write_text(json.dumps(d))
    out = tmp_path / "sel.json"
    assert X.main([str(p), "--out", str(out)]) == 0
    sel = json.loads(out.read_text())
    assert sel["rule_sha256"] == X.load_rule()[1] and sel["schema"] == X.OUTPUT_SCHEMA


def test_schema_and_missing_items_refused(env):
    items, base = env
    d = _data(_model("kev", "kev", 0.3, items, base))
    with pytest.raises(ValueError):
        X.analyze({**d, "schema": "other"})
    del d["models"][0]["e3"]["rps"]["0"][next(iter(items))]
    with pytest.raises(ValueError):
        X.analyze(d)


def test_e0_records_must_declare_protocol_v2(env):
    items, base = env
    m = _model("kev", "kev", 0.2, items, base)
    m["e0"]["protocol"] = "trackp_e0/v1"
    with pytest.raises(X.RuleSuperseded, match="trackp_e0/v2"):
        X.analyze(_data(m))
    del m["e0"]["protocol"]
    with pytest.raises(X.RuleSuperseded):
        X.analyze(_data(m))
