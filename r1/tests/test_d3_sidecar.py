"""D.3b A5/A6 sidecar client path, image choice, fallback accounting (gap G9). Fake sidecar only; no model.

AI-assisted (Claude).
"""
from __future__ import annotations

import http.client
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pytest

from r1.c3 import d3_sidecar as S
from r1.c3.prior_model import FixedPrior
from r1.c3.serve import FakeLoader, Pin, Sidecar, write_fake_pin
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.tests.c3_campaign_fixtures import node_context, run_campaign

A5 = [0.1, 0.0, 0.0, 0.05, 0.1, 0.15, 0.2, 0.2, 0.1, 0.05, 0.03, 0.02]
A1 = [0.3, 0.02, 0.03, 0.08, 0.15, 0.17, 0.1, 0.06, 0.05, 0.02, 0.01, 0.01]
ROW = {"node": "digits_mlp", "features": {"key_code": 1.0, "budget_index": 3.0}}
PIN = "a" * 64


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


class _Raw:
    """A loopback server that answers every POST with a fixed status and body (or closes the connection)."""

    def __init__(self, status=200, body=b"{}", close=False):
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                if outer.close:
                    self.connection.shutdown(socket.SHUT_RDWR)
                    return
                self.send_response(outer.status)
                self.send_header("Content-Length", str(len(outer.body)))
                self.end_headers()
                self.wfile.write(outer.body)
        self.status, self.body, self.close = status, body, close
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture()
def raw():
    made = []

    def make(**kw):
        r = _Raw(**kw)
        made.append(r)
        return r
    yield make
    for r in made:
        r.stop()


def _prior(url, digest, **kw):
    return S.D3SidecarPrior(url, FixedPrior(A1, "A1"), name="A5", expected_digest=digest, **kw)


def test_round_trip(sidecar):
    sc, url = sidecar()
    p = _prior(url, sc.digest)
    f = p.forecast(ROW)
    assert f.fallback is None and np.allclose(f.probs, A5) and f.digest == sc.digest and f.llm_calls == 0
    assert f.info["sidecar_wait_polls"] == 0 and f.info["failure_rule"] == S.SIDECAR_FAILURE_RULE
    assert (p.forecasts, p.fallbacks) == (1, 0) and sc.calls == 1


def test_a_slow_sidecar_is_waited_for_once_with_progress_records_and_never_reissued(sidecar):
    # every call is slower than the poll interval (review B1: the old client re-issued forever here)
    sc, url = sidecar(delay_s=0.45)
    p = _prior(url, sc.digest, poll_s=0.1)
    for _ in range(3):
        f = p.forecast(ROW)
        assert f.fallback is None and np.allclose(f.probs, A5) and f.info["sidecar_wait_polls"] >= 2
    assert sc.calls == 3  # one request per forecast: nothing was issued again
    assert len(p.progress_log) >= 6 and all(r["event"] == "sidecar_waiting" for r in p.progress_log)
    assert p.fallbacks == 0


def test_an_error_answer_falls_back_and_is_counted(sidecar):
    sc, url = sidecar(fail=True)
    p = _prior(url, sc.digest)
    f = p.forecast(ROW)
    assert f.fallback.startswith("prior_unavailable") and np.allclose(f.probs, A1)
    assert (p.forecasts, p.fallbacks) == (1, 1)


@pytest.mark.parametrize("body", [b"not json", b"[1, 2]", b'{"probs": []}', b'{"digest": 5}',
                                  json.dumps({"digest": PIN, "probs": [0.5] * 11}).encode(),
                                  json.dumps({"digest": PIN, "probs": ["x"] * 12}).encode()])
def test_malformed_answers_fall_back(raw, body):
    r = raw(body=body)
    p = _prior(r.url, PIN)
    f = p.forecast(ROW)
    assert f.fallback.startswith("prior_unavailable") and (p.forecasts, p.fallbacks) == (1, 1)


def test_a_well_formed_answer_with_another_digest_is_a_stop(sidecar, raw):
    sc, url = sidecar()
    with pytest.raises(S.SidecarPinMismatch):
        _prior(url, "0" * 64).forecast(ROW)
    r = raw(body=json.dumps({"digest": "b" * 64, "probs": A5}).encode())
    with pytest.raises(S.SidecarPinMismatch):
        _prior(r.url, PIN).forecast(ROW)


def test_a_lost_sidecar_is_infrastructure_not_a_fallback(sidecar, raw):
    sc, url = sidecar()
    sc.stop()
    p = _prior(url, sc.digest)
    with pytest.raises(S.SidecarLost):
        p.forecast(ROW)
    r = raw(close=True)  # the connection closes without an answer
    p2 = _prior(r.url, PIN)
    with pytest.raises(S.SidecarLost):
        p2.forecast(ROW)
    assert p.fallbacks == p2.fallbacks == 0


@pytest.mark.parametrize("exc", [http.client.IncompleteRead(b""), http.client.BadStatusLine("x"),
                                 OSError(65, "No route to host"), ConnectionResetError()])
def test_every_connection_failure_is_lost(monkeypatch, exc):
    p = _prior("http://127.0.0.1:9", PIN)

    def boom(self):
        raise exc
    monkeypatch.setattr(http.client.HTTPConnection, "connect", boom)
    with pytest.raises(S.SidecarLost):
        p.forecast(ROW)
    assert p.fallbacks == 0


@pytest.mark.parametrize("kw,match", [
    ({"name": "A3"}, "serves"), ({"expected_digest": None}, "unpinned"), ({"expected_digest": "abc"}, "unpinned"),
    ({"url": "http://10.0.0.5:8765"}, "loopback"), ({"url": "file://localhost:8765"}, "loopback"),
    ({"url": "https://127.0.0.1:8765"}, "loopback"), ({"url": "http://127.0.0.1"}, "loopback"),
    ({"poll_s": 0}, "positive"),
])
def test_client_refusals(kw, match):
    args = {"url": "http://127.0.0.1:8765", "name": "A5", "expected_digest": PIN, **kw}
    with pytest.raises(ValueError, match=match):
        S.D3SidecarPrior(args.pop("url"), FixedPrior(A1, "A1"), **args)


def test_sidecar_url_is_loopback_only():
    assert S.sidecar_url(8765) == "http://127.0.0.1:8765" and S.sidecar_url(1, "::1") == "http://[::1]:1"
    for bad in ((8765, "0.0.0.0"), (0, "127.0.0.1"), (70000, "127.0.0.1"), (True, "127.0.0.1")):
        with pytest.raises(ValueError):
            S.sidecar_url(*bad)


def test_image_choice_is_open_and_fails_closed():
    assert S.SIDECAR_IMAGE_CHOICE is None
    with pytest.raises(ValueError, match="open author item"):
        S.resolve_sidecar_image()
    assert S.resolve_sidecar_image("v1") == S.V1_IMAGE
    ref = "ghcr.io/dowlingwong/r1-trackp-gpu@sha256:" + "e" * 64
    assert S.resolve_sidecar_image("trackp", trackp_ref=ref) == ref
    for bad in (None, "ghcr.io/dowlingwong/x:latest", "docker.io/x@sha256:" + "e" * 64, S.V1_IMAGE):
        with pytest.raises(ValueError):
            S.resolve_sidecar_image("trackp", trackp_ref=bad)
    with pytest.raises(ValueError):
        S.resolve_sidecar_image("v1", trackp_ref=ref)
    with pytest.raises(ValueError):
        S.resolve_sidecar_image("v2")


def _ev(kind, detail=None):
    return {"event_type": kind, "payload": {"epoch": "E1", "detail": detail or {}}}


def test_fallback_stop_threshold():
    ok = [[_ev("control_decision", {"sidecar_compute_s": 0.01})] * 100]
    assert S.fallback_stop(ok) == {"forecasts": 100, "fallbacks": 0, "share": 0.0, "threshold": 0.01, "stop": False}
    one = [[_ev("control_decision", {"sidecar_compute_s": 0.01})] * 99
           + [_ev("prior_unavailable"), _ev("control_decision", {"fallback": "prior_unavailable: HTTPError"})]]
    assert S.fallback_stop(one)["stop"] is False  # exactly 1 % is not above 1 %
    two = one + [[_ev("prior_unavailable"), _ev("control_decision", {"fallback": "prior_unavailable: x"})]]
    assert S.fallback_stop(two)["stop"] is True
    with pytest.raises(ValueError, match="inconsistent"):
        S.fallback_stop([[_ev("prior_unavailable")]])


def test_campaign_records_the_wait_in_the_ledger_and_counts_forecasts(tmp_path, sidecar):
    sc, url = sidecar()
    ctl = S.D3SidecarRuleController(_prior(url, sc.digest), node_context(0.005), fallback=FixedPrior(A1, "A1"))
    _, events, rows, _ = run_campaign(tmp_path, ScriptedRandomManager("digits_mlp", seed=3, repetition=0),
                                      **ctl.campaign_kwargs(W=20, llm_cap=12))
    verdict = S.fallback_stop([events])
    assert verdict["forecasts"] > 0 and verdict["fallbacks"] == 0 and not verdict["stop"]
    details = [e["payload"]["detail"] for e in events if e["event_type"] == "control_decision"
               and "sidecar_compute_s" in (e["payload"].get("detail") or {})]
    assert details and all(d["sidecar_wait_polls"] == 0 and d["failure_rule"] == S.SIDECAR_FAILURE_RULE
                           and "sidecar_wait_s" in d for d in details)
