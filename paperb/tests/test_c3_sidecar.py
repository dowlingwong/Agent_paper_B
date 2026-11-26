"""RUNBOOK Track H.5: the forecast sidecar, its pin, and the client's timeout fallback. ENGINEERING_ONLY; AI-assisted (Claude).

No model is loaded anywhere: the sidecar runs with ``FakeLoader``.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time

import numpy as np
import pytest

from r1.c3.control import RuleController
from r1.c3.prior_model import FixedPrior, SidecarPrior
from r1.c3.serve import FakeLoader, Pin, PinError, Sidecar, TorchLoraLoader, write_fake_pin
from r1.harness import REPO
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.tests.c3_campaign_fixtures import node_context, run_campaign

A5 = [0.1, 0.0, 0.0, 0.05, 0.1, 0.15, 0.2, 0.2, 0.1, 0.05, 0.03, 0.02]
A1 = [0.3, 0.02, 0.03, 0.08, 0.15, 0.17, 0.1, 0.06, 0.05, 0.02, 0.01, 0.01]
ROW = {"node": "digits_mlp", "features": {"key_code": 1.0, "budget_index": 3.0}}


@pytest.fixture()
def sidecar(tmp_path):
    started = []

    def start(**kw):
        sc = Sidecar(Pin.load(write_fake_pin(tmp_path)), FakeLoader({"default": A5}), **kw)
        url = sc.start()
        started.append(sc)
        return sc, url
    yield start
    for sc in started:
        sc.stop()


def test_forecast_round_trip_and_pin(sidecar):
    sc, url = sidecar()
    prior = SidecarPrior(url, FixedPrior(A1, "A1"), expected_digest=sc.digest)
    f = prior.forecast(ROW)
    assert f.fallback is None and np.allclose(f.probs, A5) and f.digest == sc.digest
    assert f.version.startswith("A5/c3_sidecar/v1") and f.llm_calls == 0 and "sidecar_compute_s" in f.info
    wrong = SidecarPrior(url, FixedPrior(A1, "A1"), expected_digest="0" * 64).forecast(ROW)
    assert wrong.fallback.startswith("prior_unavailable") and np.allclose(wrong.probs, A1)


def test_refuses_an_adapter_whose_sha256_differs_from_the_pin(tmp_path):
    pin_path = write_fake_pin(tmp_path)
    (tmp_path / "A5_adapter.fixture").write_bytes(b"tampered")
    with pytest.raises(PinError, match="adapter sha256"):
        Sidecar(Pin.load(pin_path), FakeLoader({"default": A5}))
    done = subprocess.run([sys.executable, "-m", "r1.c3.serve", "--pin", str(pin_path), "--port", "0",
                           "--fake", str(_table(tmp_path))], cwd=REPO, capture_output=True, text=True, timeout=60)
    assert done.returncode == 2 and "REFUSED" in done.stderr
    # Track P 1.11: the real loader exists; a fixture pin (no model spec, no manifest) is refused before loading
    with pytest.raises(PinError, match="model pin needs"):
        TorchLoraLoader().load(Pin.load(write_fake_pin(tmp_path / "ok")))


def _table(tmp_path):
    p = tmp_path / "fixed.json"
    p.write_text(json.dumps({"default": A5}))
    return p


@pytest.mark.parametrize("fault", ["timeout", "error", "down"])
def test_timeout_and_errors_fall_back_to_a1(sidecar, fault):
    if fault == "down":
        url = "http://127.0.0.1:9"  # nothing listens
    else:
        _, url = sidecar(delay_s=1.5) if fault == "timeout" else sidecar(fail=True)
    prior = SidecarPrior(url, FixedPrior(A1, "A1"), timeout_s=1.0)
    t0 = time.perf_counter()
    f = prior.forecast(ROW)
    assert time.perf_counter() - t0 < 1.4
    assert f.fallback.startswith("prior_unavailable") and np.allclose(f.probs, A1)
    if fault == "timeout":
        assert "timeout" in f.fallback


def test_campaign_survives_a_dead_sidecar_and_logs_prior_unavailable(tmp_path, sidecar):
    sc, url = sidecar(delay_s=1.5)
    fallback = FixedPrior(A1, "A1")
    ctl = RuleController(SidecarPrior(url, fallback, name="A5", expected_digest=sc.digest), node_context(0.005),
                         fallback=fallback)
    _, events, rows, _ = run_campaign(tmp_path / "c", ScriptedRandomManager("digits_mlp", seed=2, repetition=0),
                                      budget=4, **ctl.campaign_kwargs())
    assert len(rows) == 4
    unavailable = [e for e in events if e["event_type"] == "prior_unavailable"]
    assert len(unavailable) == 3 and all("timeout" in e["payload"]["reason"] for e in unavailable)
    e1 = [e["payload"]["detail"] for e in events if e["event_type"] == "control_decision"
          and e["payload"]["epoch"] == "E1" and "probs" in e["payload"].get("detail", {})]
    assert all(np.allclose(d["probs"], A1) and d["fallback"].startswith("prior_unavailable") for d in e1)
    assert all(d["llm_calls"] == 0 for d in e1)  # sidecar calls cost compute only
