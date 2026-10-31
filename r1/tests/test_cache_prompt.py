"""R1-CACHEPROMPT-FALSE (31 Oct 2026): the A4 / manager-question side queries carry ``cache_prompt``.

The manager path goes through the harness provider; the A4 observer (``r1/exam/observer.py``) and
``ManagerQuestionPrior`` use the paper's own ``chat_client``, which posts its own body. Those paths must
send the same setting, or EXAM and C3-A4 stay subject to the non-determinism the ruling removes.
ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest import mock

import numpy as np

from r1.c3.prior_model import N_BINS, FixedPrior, ManagerQuestionPrior, chat_client
from r1.exam.observer import SelfForecastObserver

TYPED = json.dumps({"p_no_effect": 0.6, "p_positive": 0.9, "size": "small"})
ROW = {"node": "digits_mlp", "features": {"key_code": 3},
       "edit": {"symbol": "ALPHA", "old": "1e-4", "new": "1e-3"}}


class _StandIn(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    bodies: list = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
        type(self).bodies.append(body)
        data = json.dumps({"id": "x", "object": "chat.completion", "created": 1, "model": body.get("model"),
                           "choices": [{"index": 0, "finish_reason": "stop",
                                        "message": {"role": "assistant", "content": TYPED}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class _Server:
    def __enter__(self):
        _StandIn.bodies = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _StandIn)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


class TestA4CachePrompt(unittest.TestCase):
    def test_chat_client_sends_the_field_and_exposes_it(self):
        with _Server() as url, mock.patch.dict("os.environ", {"LLAMACPP_CACHE_PROMPT": "false"}):
            call = chat_client(url, "r1-manager", max_tokens=8)
            call("hello")
        self.assertIs(_StandIn.bodies[0]["cache_prompt"], False)
        self.assertIs(call.cache_prompt, False)
        self.assertEqual(call.cache_prompt, _StandIn.bodies[0]["cache_prompt"])

    def test_env_override_reaches_the_a4_body(self):
        with _Server() as url, mock.patch.dict("os.environ", {"LLAMACPP_CACHE_PROMPT": "true"}):
            chat_client(url, "r1-manager", max_tokens=8)("hello")
        self.assertIs(_StandIn.bodies[0]["cache_prompt"], True)

    def test_exam_observer_records_it(self):
        proposal = SimpleNamespace(extra={"structured_edit": {"objective": "o"}})
        spec = SimpleNamespace(name="digits_mlp")
        with _Server() as url, mock.patch.dict("os.environ", {"LLAMACPP_CACHE_PROMPT": "false"}):
            obs = SelfForecastObserver(base_url=url, model="r1-manager")
            payload = obs.observe(proposal, SimpleNamespace(), spec)
        self.assertIs(_StandIn.bodies[0]["cache_prompt"], False)
        self.assertIs(payload["cache_prompt"], False)
        self.assertEqual(payload["llm_calls"], 1)

    def test_manager_question_prior_records_it_on_the_forecast(self):
        fallback = FixedPrior(np.ones(N_BINS), "A1")
        with _Server() as url, mock.patch.dict("os.environ", {"LLAMACPP_CACHE_PROMPT": "false"}):
            a4 = ManagerQuestionPrior(chat_client(url, "r1-manager", max_tokens=8), fallback)
            fc = a4.forecast(ROW)
        self.assertIs(_StandIn.bodies[0]["cache_prompt"], False)
        self.assertIs(fc.cache_prompt, False)
        self.assertEqual(fc.llm_calls, 1)

    def test_an_injected_fake_client_records_nothing(self):
        fallback = FixedPrior(np.ones(N_BINS), "A1")
        fc = ManagerQuestionPrior(lambda prompt: TYPED, fallback).forecast(ROW)
        self.assertIsNone(fc.cache_prompt)


if __name__ == "__main__":
    unittest.main()
