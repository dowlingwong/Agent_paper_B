"""Runbook P3 step 2: the E-SYN world port equals the pinned Track S original on shared seeds."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from paperc.esyn import worlds as W

REPO = Path(__file__).resolve().parents[2]
PIN = "fab88fced839c5fb794ed62a0742b4646cb76ea2"


@pytest.fixture(scope="module")
def ORIG(tmp_path_factory):
    try:
        src = subprocess.run(["git", "-C", str(REPO), "show", f"{PIN}:r1/tracks/worlds.py"], check=True,
                             capture_output=True, text=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("pinned Track S commit not available (git fetch origin trackS-ops-20261030)")
    f = tmp_path_factory.mktemp("orig") / "tracks_worlds_orig.py"
    f.write_text(src)
    spec = importlib.util.spec_from_file_location("tracks_worlds_orig", f)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tracks_worlds_orig"] = mod
    spec.loader.exec_module(mod)
    return mod


def _cases(mod):
    out = [("N0", None, 0.0), ("P1", None, 8.0), ("P0", None, 0.01)]
    return out + [(k, v, 0.01) for (k, v) in mod.VARIANTS]


@pytest.mark.parametrize("seed", [1, 7, 20261029])
def test_port_equals_original(ORIG, seed):
    for kind, variant, strength in _cases(ORIG):
        wo, wp = ORIG.make_world(kind, strength, variant), W.make_world(kind, strength, variant)
        assert wo.to_dict() == wp.to_dict()
        ro, rp = ORIG.Regime(), W.Regime()
        for inst in range(3):
            to, tp = ORIG.theta_table(wo, ro, seed, inst), W.theta_table(wp, rp, seed, inst)
            np.testing.assert_array_equal(to, tp)
            so, sp = ORIG.Stream([seed, inst, 1], ro.llm_cap), W.Stream([seed, inst, 1], rp.llm_cap)
            po, pp = ORIG.proposal_sequence(wo, ro, to, so), W.proposal_sequence(wp, rp, tp, sp)
            assert [vars(x) for x in po] == [vars(x) for x in pp]
            log_o, log_p = [], []
            for x, y in zip(po, pp):
                if x.rule:
                    continue
                assert ORIG.true_increment(wo, ro, to, x, so, log_o) == W.true_increment(wp, rp, tp, y, sp, log_p)
                assert ORIG.measurement_noise(wo, x, so) == W.measurement_noise(wp, y, sp)
                eo, ep = ORIG.keep_log_entry(wo, x.t, x.t % 9 + 1, 12), W.keep_log_entry(wp, y.t, y.t % 9 + 1, 12)
                assert eo == ep
                if eo:
                    log_o.append(eo)
                    log_p.append(ep)
    for a, A, s in [(0.0, 1e-4, 0.0066), (-0.001, 4e-5, 0.0019), (0.002, 1e-6, 0.01)]:
        assert ORIG.v_star(a, A, s) == W.v_star(a, A, s)


def test_port_has_no_repository_imports():
    src = Path(W.__file__).read_text()
    assert "import r1" not in src and "from r1" not in src
