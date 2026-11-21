"""Track P 1.4: soft label v2 (R1-SOFT-SIGMA) and the action target (spec §3.4-3.5). ENGINEERING_ONLY; AI-assisted (Claude)."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm

from r1.c3 import labels as L
from r1.c3 import offline_eval as O
from r1.c3 import rules
from r1.c3.arms import TAU_FLOOR_Z
from r1.harness import REPO

PILOT = REPO / "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
# sha256 of json.dumps(offline_eval.assemble(PILOT, seed_split=...), sort_keys=True) and of the evaluate() JSON,
# computed with the code at 4919f59 (before R1-SOFT-SIGMA) in the Track P venv (Python 3.12, numpy/scipy pinned there).
V1_REFERENCE = {
    True: "5960856db849b59a839d225c8f39af21b253eebff21c6c71b1fecb0da178ccd7",
    False: "e1e7c12856c6f4a8474d02a658b0d368b20742b34e6130cc460b6289d1a4c870",
    "evaluate": "b12f1f5fcb09f569bcf58df66d6fbeceecee3a805d62362876fce6fc2d509fa2",
}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=lambda o: o.tolist()).encode()).hexdigest()


def test_pooled_node_width_is_sigma_over_sqrt_k():
    p = L.soft_label(0.004, None, 0.004, k_label=5)          # z = 1, s = 1/sqrt(5) in z units
    cdf = norm.cdf((L.EDGES - 1.0) * np.sqrt(5))
    np.testing.assert_allclose(p[1:], np.diff(cdf) / np.diff(cdf).sum(), atol=1e-12)
    assert p[0] == 0 and p.sum() == pytest.approx(1.0)
    # larger K (raised near t*) -> narrower; a separate pooled sigma widens it
    assert L.soft_label(0.0, None, 1.0, k_label=10)[6] > L.soft_label(0.0, None, 1.0, k_label=5)[6]
    wide = L.soft_label(0.0, None, 1.0, k_label=5, sigma_pooled=2.0)
    np.testing.assert_allclose(wide, L.soft_label(0.0, 2.0 / np.sqrt(5), 1.0, sigma_mode="se_audit"), atol=1e-12)


def test_v2_is_the_default_and_refuses_v1_style_calls():
    assert L.DEFAULT_SIGMA_MODE == "pooled_node"
    assert L.soft_label_version() == "soft_label/v2_pooled_node"
    assert L.soft_label_version("se_audit") == "soft_label/v1_se_audit"
    with pytest.raises(ValueError, match="se_audit"):
        L.soft_label(0.004, 0.001, 0.004)                    # old positional se under the new default
    with pytest.raises(ValueError, match="k_label"):
        L.soft_label(0.004, None, 0.004)
    with pytest.raises(ValueError):
        L.soft_label(0.0, None, 1.0, sigma_mode="bogus")
    assert L.soft_label(None, None, 1.0, inert=True)[0] == 1.0


def test_v1_mode_is_the_old_formula():
    for d, se, s in [(0.004, 0.001, 0.004), (0.0, 1.0, 1.0), (-0.3, 0.05, 0.1), (0.2, 0.0, 0.1)]:
        p = L.soft_label(d, se, s, sigma_mode="se_audit")
        if se == 0:
            assert p[L.hard_bin(d / s)] == 1.0
        else:
            cdf = norm.cdf((L.EDGES - d / s) / (se / s))
            np.testing.assert_allclose(p[1:], np.clip(np.diff(cdf), 0, None) / np.clip(np.diff(cdf), 0, None).sum())


def test_sigma_source_is_the_c1_table():
    from r1.c3 import dataset
    assert L.SOFT_SIGMA_SOURCE["file"] == dataset.E1_SUMMARY
    got = hashlib.sha256((REPO / dataset.E1_SUMMARY).read_bytes()).hexdigest()
    assert got == L.SOFT_SIGMA_SOURCE["sha256"]


@pytest.mark.skipif(not PILOT.is_dir(), reason="pilot table not in this checkout")
def test_existing_pilot_table_rebuilt_under_v1_is_byte_identical():
    for seed_split in (True, False):
        rows = O.assemble(PILOT, seed_split=seed_split)
        assert len(rows) == 627
        assert _sha(rows) == V1_REFERENCE[seed_split]
        assert not any("soft_version" in r for r in rows)
    ev = O.evaluate(O.assemble(PILOT))
    assert hashlib.sha256(json.dumps(ev, sort_keys=True, default=str).encode()).hexdigest() == V1_REFERENCE["evaluate"]


@pytest.mark.skipif(not PILOT.is_dir(), reason="pilot table not in this checkout")
def test_v2_table_records_its_version_and_uses_k_label():
    rows = O.assemble(PILOT, sigma_mode="pooled_node")
    lab = [r for r in rows if r.get("soft") is not None and r["soft"][0] < 1]
    assert lab and all(r["soft_version"] == "soft_label/v2_pooled_node" for r in lab)
    r = lab[0]
    from r1.c3.audit import split_audit
    a = {x["proposal_id"]: x for x in map(json.loads, (PILOT / "audits.jsonl").read_text().splitlines()) if x}
    half = split_audit(a[r["proposal_id"]])[0]
    np.testing.assert_allclose(r["soft"], L.soft_label(half["delta_audit"], None, r["sigma_node"], k_label=half["k"]))


def test_action_target_hand_value():
    a1 = np.zeros(12)
    a1[6] = 1.0                                    # mu = 0, tau = floor 0.15 sigma_node
    sigma_node, sigma_cmp = 0.01, 0.01
    _, mu, tau = L.moments(a1, sigma_node, tau_floor_z=TAU_FLOOR_Z)
    assert mu == pytest.approx(0.0) and tau == pytest.approx(0.0015)
    # t* = -mu sigma^2 / tau^2 = 0: keep iff delta_hat > 0
    u = L.action_target([0.02, 0.02, -0.01], [0.001, -0.001, 0.003], a1, sigma_node, sigma_cmp)
    np.testing.assert_allclose(u, [0.02 - 0.001, -0.001, -0.01 - 0.001])
    # keep agrees with rules.keep under the same moments
    a2 = np.r_[0.1, np.full(11, 0.9 / 11)]
    _, mu2, tau2 = L.moments(a2, sigma_node, tau_floor_z=TAU_FLOOR_Z)
    dh = np.linspace(-0.02, 0.02, 9)
    want = np.full(9, 0.005) * rules.keep(dh, mu2, tau2, sigma_cmp) - 0.1 * sigma_node
    np.testing.assert_allclose(L.action_target(np.full(9, 0.005), dh, a2, sigma_node, sigma_cmp), want)
