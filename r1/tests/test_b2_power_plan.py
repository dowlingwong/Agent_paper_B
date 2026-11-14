"""Synthetic tests of r1/scripts/b2_power_plan.py (ENGINEERING_ONLY; AI-assisted)."""
import math
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import chi2, t as student_t

spec = importlib.util.spec_from_file_location("b2pp", Path(__file__).resolve().parents[1] / "scripts/b2_power_plan.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


def manifest(cand, role, roots):
    """roots: {(node, seed): [(trial, incumbent_metrics), ...]}"""
    aps, paths = [], []
    for (node, seed), props in roots.items():
        inst = f"{node}__s{seed}"
        paths.append(f"/w/{cand}/b1/off/{inst}/campaign_manifest.json")
        for trial, inc in props:
            aps.append({"proposal_id": f"EXAM:{inst}:t{trial:03d}", "instance_id": inst, "node": node, "mode": "off",
                        "incumbent_metrics": inc, "candidate_metrics": inc, "delta_audit": 0.0})
    return {"candidate": cand, "role": role, "audited_proposals": aps, "root_manifests": paths,
            "phase": "b1", "status": "COMPLETE"}


def e1(sig):
    return {"nodes": {n: {"edits": [{"sd_joint": s, "material": True}]} for n, s in sig.items()}}


def test_proxy_uses_last_audited_trial_and_skips_anchors_and_on_mode():
    m = manifest("c1", "candidate", {("a", 9001): [(2, [0.1] * 4), (7, [0.5] * 4), (3, [0.9] * 4)]})
    m["audited_proposals"].append({"proposal_id": "EXAM:a__s9001:t009", "instance_id": "a__s9001", "node": "a",
                                   "mode": "on", "incumbent_metrics": [9.0] * 4})
    anchor = manifest("x", "anchor", {("a", 9001): [(2, [7.0] * 4)]})
    cells, excl = P.root_proxies([m, anchor])
    assert cells == {("c1", "a"): {"a__s9001": 0.5}} and excl == {}


def test_root_without_audit_is_counted_as_excluded():
    m = manifest("c1", "candidate", {("a", 9001): [(2, [0.1] * 4)]})
    m["root_manifests"].append("/w/c1/b1/off/a__s9002/campaign_manifest.json")
    _, excl = P.root_proxies([m])
    assert excl == {"a": 1}


def test_pooled_variance_and_ucl():
    ys1, ys2 = [0.1, 0.2, 0.4], [0.5, 0.5, 0.8, 0.9]
    ms = [manifest("c1", "candidate", {("a", 9000 + i): [(2, [y] * 4)] for i, y in enumerate(ys1)}),
          manifest("c2", "candidate", {("a", 9000 + i): [(2, [y] * 4)] for i, y in enumerate(ys2)})]
    cells, _ = P.root_proxies(ms)
    pv = P.pooled_variance(cells, "a")
    v = (2 * np.var(ys1, ddof=1) + 3 * np.var(ys2, ddof=1)) / 5
    assert pv["dof"] == 5 and math.isclose(pv["V_hat"], v)
    assert math.isclose(pv["V_ucl"], v * 5 / chi2.ppf(0.2, 5))


def test_n_required_is_the_smallest_n():
    V, h = 0.01 ** 2, 0.006
    n = P.n_required(V, h, 1)
    assert student_t.ppf(0.975, n - 1) * math.sqrt(V / n) <= h
    assert student_t.ppf(0.975, n - 2) * math.sqrt(V / (n - 1)) > h
    assert P.n_required(V, h, 2) > n


def test_plan_within_cap_and_stop_over_cap_never_clipped():
    rng = np.random.default_rng(1)
    def ms(sd):
        return [manifest(f"c{c}", "candidate", {("a", 9001 + i): [(2, [float(rng.normal(0, sd))] * 4)] for i in range(4)})
                for c in range(15)]
    small = P.plan(ms(0.001), e1({"a": 0.01}), ["a"], ["c1"])
    assert small["cap_status"] == "within_cap" and small["b2_instances_per_node"] == small["n"] <= 10
    big = P.plan(ms(0.05), e1({"a": 0.005}), ["a"], ["c1"])
    assert big["n"] > 10 and big["cap_status"] == "STOP_author_decides" and big["b2_instances_per_node"] is None
    two = P.plan(ms(0.01), e1({"a": 0.01}), ["a"], ["c1", "c2"])
    assert two["k"] == 2


def test_sigma_node_is_median_over_material_edits():
    s = {"nodes": {"a": {"edits": [{"sd_joint": 0.1, "material": True}, {"sd_joint": 0.3, "material": True},
                                   {"sd_joint": 9.0, "material": False}]}}}
    assert math.isclose(P.sigma_node(s, "a"), 0.2)
    s2 = {"nodes": {"a": {"edits": [{"sd_joint": 0.1}, {"sd_joint": 0.5}]}}}
    assert math.isclose(P.sigma_node(s2, "a"), 0.3)


def test_main_refuses_a_wrong_manifest_sha(tmp_path):
    f = tmp_path / "m.json"
    f.write_text('{"label":"EXAM","manifests":[]}')
    g = tmp_path / "e.json"
    g.write_text("{}")
    with pytest.raises(SystemExit, match="STOP: manifests sha256"):
        P.main(["--manifests", str(f), "--manifests-sha256", "0" * 64, "--e1-summary", str(g), "--finalists", "c"])
