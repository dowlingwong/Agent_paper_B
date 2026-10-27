"""Track P 1.9 / 1.10: Jev client and R-B demonstration writer against fake servers (no real API, no key).

ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pytest

from r1.c3 import jev_client as J
from r1.c3 import rb_demos as R
from r1.c3.train.types import DecisionPrompt

FAKE_KEY = "test-key-not-a-secret-123"
PROMPT = DecisionPrompt(state="node digits_mlp; budget 5/20; incumbent lr=0.01", proposal="set lr 0.01 -> 0.03",
                        group="s1", meta={"proposal_id": "p1", "y_train": [0.5] * 12, "mu_train": 0.7,
                                          "u_train": 0.2, "split": "train"})


class _Fake:
    """Stdlib fake server; ``reply(body) -> (status, json)``; records requests and headers."""

    def __init__(self, reply):
        fake = self
        self.requests, self.headers = [], []

        class H(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fake.requests.append(body)
                fake.headers.append(dict(self.headers))
                status, out = reply(body)
                data = json.dumps(out).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()


@pytest.fixture
def fake():
    servers = []

    def make(reply):
        servers.append(_Fake(reply))
        return servers[-1]
    yield make
    for s in servers:
        s.close()


def jev_reply(model="jev-1.14.0", jitter=0.0):
    calls = {"n": 0}

    def reply(body):
        calls["n"] += 1
        answers = {}
        for name in body["questions"]:
            k = int(name[-2:])
            p = float(np.clip(1 - (k / 11) + jitter * (calls["n"] - 2), 0, 1))
            answers[name] = {"type": "noul", "noul": p}
        return 200, {"model": model, "answers": answers, "usage": {"input_tokens": 100, "output_tokens": 11}}
    return reply


CLOCK = lambda: dt.datetime(2026, 10, 24, 12, 0, tzinfo=dt.timezone.utc)  # noqa: E731  (a Saturday)


def jcfg(fake_url, tmp_path, **kw):
    return J.JevConfig(model="jev-1.14.0", base_url=fake_url, log_root=tmp_path / "jev", **kw)


# ---------------------------------------------------------------- Jev

@pytest.mark.parametrize("bad", ["jev-latest", "jev-preview", "jev", "jev-1.14", "Jev-1.14.0", "jev-1.14.0-rc"])
def test_unversioned_model_names_are_refused(bad):
    with pytest.raises(J.JevError):
        J.JevConfig(model=bad)


def test_ten_questions_one_per_finite_edge():
    qs = J.questions()                      # R1-EDGES-10: 10 yes/no questions, no inert question
    assert len(qs) == 10 == len(J.FINITE_EDGES)
    assert all(q["type"] == "noul" for q in qs.values())
    assert sorted(qs) == [J.edge_name(k) for k in range(1, 11)]


def test_bins_monotone_cdf_and_mass():
    s = np.array([0.95, 0.9, 0.92, 0.7, 0.6, 0.65, 0.3, 0.2, 0.1, 0.05])  # two non-monotone steps
    ans = {J.edge_name(k + 1): {"noul": v} for k, v in enumerate(s)}
    p = J.bins_from_answers(ans)
    assert p.shape == (12,) and np.isclose(p.sum(), 1) and np.all(p >= 0) and p[0] == 0
    cdf = np.maximum.accumulate(1 - s)
    assert np.allclose(np.cumsum(p[1:])[:-1], cdf)


def test_forecast_three_repeats_one_request_each_and_full_log(fake, tmp_path):
    srv = fake(jev_reply(jitter=0.01))
    c = J.JevClient(jcfg(srv.url, tmp_path), clock=CLOCK, env={J.KEY_ENV: FAKE_KEY})
    out = c.forecast(PROMPT)
    assert len(srv.requests) == 3 and len(out["repeats"]) == 3
    assert np.isclose(sum(out["probs"]), 1) and max(out["spread"]) > 0
    body = srv.requests[0]
    assert body["model"] == "jev-1.14.0" and len(body["questions"]) == 10
    assert body["state"].startswith(PROMPT.state) and PROMPT.proposal in body["state"]
    assert srv.headers[0]["Authorization"] == f"Bearer {FAKE_KEY}"
    log = (tmp_path / "jev" / "20261024" / "calls.jsonl").read_text()
    assert FAKE_KEY not in log
    recs = [json.loads(line) for line in log.splitlines()]
    assert len(recs) == 3 and [r["repeat"] for r in recs] == [0, 1, 2]
    assert all(r["model_returned"] == "jev-1.14.0" and r["request"] == body and r["response"]["answers"]
               and r["endpoint"].endswith("/v1/systemone") for r in recs)


def test_no_meta_or_label_reaches_jev(fake, tmp_path):
    srv = fake(jev_reply())
    J.JevClient(jcfg(srv.url, tmp_path, repeats=1), clock=CLOCK, env={J.KEY_ENV: FAKE_KEY}).forecast(PROMPT)
    sent = json.dumps(srv.requests[0])
    for leak in ("y_train", "mu_train", "u_train", "split", "0.7"):
        assert leak not in sent


def test_version_mismatch_is_a_stop(fake, tmp_path):
    srv = fake(jev_reply(model="jev-1.15.0"))
    c = J.JevClient(jcfg(srv.url, tmp_path), clock=CLOCK, env={J.KEY_ENV: FAKE_KEY})
    with pytest.raises(J.JevVersionMismatch):
        c.forecast(PROMPT)
    rec = json.loads((tmp_path / "jev" / "20261024" / "calls.jsonl").read_text().splitlines()[0])
    assert rec["model_returned"] == "jev-1.15.0"  # the offending response is still logged


def test_http_error_raises_and_is_logged(fake, tmp_path):
    srv = fake(lambda body: (422, {"detail": "bad question"}))
    c = J.JevClient(jcfg(srv.url, tmp_path), clock=CLOCK, env={J.KEY_ENV: FAKE_KEY})
    with pytest.raises(J.JevError):
        c.call(PROMPT)
    rec = json.loads((tmp_path / "jev" / "20261024" / "calls.jsonl").read_text())
    assert rec["status"] == 422


def test_missing_key_refuses():
    with pytest.raises(J.JevError):
        J.JevClient(J.JevConfig(model="jev-1.14.0"), env={})


# ---------------------------------------------------------------- R-B demonstrations

def ds_reply(model="DeepSeek-V4.1-Flash-1017"):
    return lambda body: (200, {"model": model, "choices": [{"message": {"role": "assistant",
                                                                         "content": "Likely a small gain."}}],
                               "usage": {"prompt_tokens": 80, "completion_tokens": 6}})


def test_messages_only_from_state_and_proposal():
    msgs = R.build_messages(PROMPT)
    text = json.dumps(msgs)
    assert PROMPT.state in text and PROMPT.proposal in text
    for leak in ("y_train", "mu_train", "u_train", "split", "p1", "0.7", PROMPT.question):
        assert leak not in text
    with pytest.raises(TypeError):
        R.build_messages({"state": PROMPT.state, "proposal": PROMPT.proposal})


def test_request_reads_no_meta_field():
    class Spy(dict):
        def __getitem__(self, k):
            raise AssertionError(f"meta[{k!r}] read")
        get = __getitem__
    spied = dataclasses.replace(PROMPT, meta=Spy())
    body = R.request_body(spied)
    assert body["model"] == "deepseek-flash" and body["max_tokens"] == 256


def test_demo_written_and_logged(fake, tmp_path):
    srv = fake(ds_reply())
    w = R.DemoWriter(base_url=srv.url, log_root=tmp_path / "rb", clock=CLOCK, env={R.KEY_ENV: FAKE_KEY})
    rec = w.write(PROMPT)
    assert rec["analysis"] == "Likely a small gain." and rec["model_returned"] == "DeepSeek-V4.1-Flash-1017"
    assert srv.requests[0]["messages"] == R.build_messages(PROMPT)
    assert srv.headers[0]["Authorization"] == f"Bearer {FAKE_KEY}"
    log = (tmp_path / "rb" / "20261024" / "calls.jsonl").read_text()
    assert FAKE_KEY not in log
    logged = json.loads(log)
    assert logged["usage"]["completion_tokens"] == 6 and logged["request"]["messages"] == R.build_messages(PROMPT)


@pytest.mark.parametrize("when,peak", [
    (dt.datetime(2026, 10, 26, 1, 0), True), (dt.datetime(2026, 10, 26, 3, 59), True),
    (dt.datetime(2026, 10, 26, 4, 0), False), (dt.datetime(2026, 10, 26, 6, 30), True),
    (dt.datetime(2026, 10, 26, 10, 0), False), (dt.datetime(2026, 10, 30, 9, 59), True),
    (dt.datetime(2026, 10, 25, 2, 0), False),  # Sunday
    (dt.datetime(2026, 10, 24, 7, 0), False),  # Saturday
])
def test_peak_window(when, peak):
    assert R.is_peak(when.replace(tzinfo=dt.timezone.utc)) is peak


def test_refuses_in_peak_hours_without_calling(fake, tmp_path):
    srv = fake(ds_reply())
    monday = lambda: dt.datetime(2026, 10, 26, 7, 0, tzinfo=dt.timezone.utc)  # noqa: E731
    w = R.DemoWriter(base_url=srv.url, log_root=tmp_path / "rb", clock=monday, env={R.KEY_ENV: FAKE_KEY})
    with pytest.raises(R.PeakHours):
        w.write(PROMPT)
    assert srv.requests == []


def test_demo_missing_key_refuses():
    with pytest.raises(R.DemoError):
        R.DemoWriter(env={})


def _dead_url():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()                       # nothing listens there: connection refused
    return f"http://127.0.0.1:{port}"


def test_version_mismatch_is_not_a_jev_error():
    """STOP 1 review #10: a retry/skip on JevError must not swallow the version STOP."""
    assert not issubclass(J.JevVersionMismatch, J.JevError)


def test_transport_failures_are_logged_by_both_clients(tmp_path):
    c = J.JevClient(jcfg(_dead_url(), tmp_path), clock=CLOCK, env={J.KEY_ENV: FAKE_KEY})
    with pytest.raises(J.JevError, match="transport"):
        c.call(PROMPT)
    rec = json.loads((tmp_path / "jev" / "20261024" / "calls.jsonl").read_text())
    assert rec["status"] is None and "transport_error" in rec and FAKE_KEY not in json.dumps(rec)
    w = R.DemoWriter(base_url=_dead_url(), log_root=tmp_path / "rb", clock=CLOCK, env={R.KEY_ENV: FAKE_KEY})
    with pytest.raises(R.DemoError):
        w.write(PROMPT)
    rec = json.loads((tmp_path / "rb" / "20261024" / "calls.jsonl").read_text())
    assert rec["status"] is None and "transport_error" in rec
