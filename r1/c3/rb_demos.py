"""Demonstration analyses for the reasoning arm R-B (PLAN R1-RB-TEACHER; spec §6.4). ENGINEERING_ONLY; AI-assisted (Claude).

DeepSeek API, OpenAI-compatible chat completions: ``POST https://api.deepseek.com/chat/completions`` with
``Authorization: Bearer <key>``, model ``deepseek-flash`` ("now served by DeepSeek-V4.1-Flash-1017"; read 26 Oct 2026
at https://api-docs.deepseek.com/, Your First API Call). The alias can move, so every response's ``model`` string is
logged with the prompt, the output and the token usage (``results/track_p/rb_demos/<date>/calls.jsonl``).

Leak guard: the request is built only from ``DecisionPrompt.state`` and ``.proposal`` plus a fixed instruction;
``meta`` (proposal id, split, labels, audit values) never reaches it. Off-peak only: refused on weekdays
01:00-04:00 and 06:00-10:00 UTC. The key is read from ``DEEPSEEK_API_KEY`` and never logged.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from r1.c3.train.types import DecisionPrompt

REPO = Path(__file__).resolve().parents[2]
BASE_URL = "https://api.deepseek.com"
ENDPOINT = "/chat/completions"
MODEL = "deepseek-flash"
EXPECTED_BACKEND = "DeepSeek-V4.1-Flash-1017"
KEY_ENV = "DEEPSEEK_API_KEY"
MAX_ANALYSIS_TOKENS = 256
DEMO_VERSION = "rb_demos/v1"
PEAK_UTC = ((1, 4), (6, 10))  # weekday hours [start, end) when demonstrations are not written

SYSTEM = ("You analyse proposed hyperparameter edits in an automated machine-learning experiment loop. "
          "You see the loop state and one proposed edit, never its result.")
INSTRUCTION = ("In at most 256 tokens, analyse whether this edit is likely to improve the validation metric beyond "
               "the node's noise level, or to have no effect or a negative one. Reason from the state and the edit "
               "only; end with one sentence stating your expectation.")


class DemoError(RuntimeError):
    pass


class PeakHours(DemoError):
    pass


def is_peak(now: dt.datetime) -> bool:
    now = now.astimezone(dt.timezone.utc)
    return now.weekday() < 5 and any(a <= now.hour < b for a, b in PEAK_UTC)


def build_messages(prompt: DecisionPrompt) -> list[dict]:
    """Chat messages from the serialised view only (no meta, labels or audit fields)."""
    if not isinstance(prompt, DecisionPrompt):
        raise TypeError("build_messages takes a DecisionPrompt")
    user = f"Loop state:\n{prompt.state}\n\nProposed edit:\n{prompt.proposal}\n\n{INSTRUCTION}"
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def request_body(prompt: DecisionPrompt, temperature: float = 1.0) -> dict:
    return {"model": MODEL, "messages": build_messages(prompt), "max_tokens": MAX_ANALYSIS_TOKENS,
            "temperature": temperature, "thinking": {"type": "disabled"}, "stream": False}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


@dataclass
class DemoWriter:
    base_url: str = BASE_URL
    temperature: float = 1.0
    timeout_s: float = 120.0
    log_root: Path = field(default=REPO / "results" / "track_p" / "rb_demos")
    clock: object = _now
    env: object = field(default_factory=lambda: os.environ)

    def __post_init__(self) -> None:
        self._key = self.env.get(KEY_ENV)
        if not self._key:
            raise DemoError(f"{KEY_ENV} is not set (the author places ~/.config/r1/secrets.env; STOP)")

    @property
    def log_path(self) -> Path:
        return Path(self.log_root) / self.clock().strftime("%Y%m%d") / "calls.jsonl"

    def write(self, prompt: DecisionPrompt) -> dict:
        now = self.clock()
        if is_peak(now):
            raise PeakHours(f"{now.isoformat()} is inside the peak window (weekdays {PEAK_UTC} UTC)")
        body = request_body(prompt, self.temperature)
        url = self.base_url.rstrip("/") + ENDPOINT
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {self._key}"})
        transport = None
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
                status, raw = r.status, r.read().decode()
        except urllib.error.HTTPError as exc:
            status, raw = exc.code, exc.read().decode(errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:   # transport failure: logged, then raised
            status, raw, transport = None, "", repr(exc)[:300]
        try:
            resp = json.loads(raw)
        except json.JSONDecodeError:
            resp = None
        ok = status == 200 and isinstance(resp, dict) and bool(resp.get("choices"))
        analysis = resp["choices"][0]["message"].get("content") if ok else None
        record = {"version": DEMO_VERSION, "endpoint": url, "date": now.isoformat(), "model_requested": MODEL,
                  "model_returned": resp.get("model") if isinstance(resp, dict) else None,
                  "prompt_id": prompt.meta.get("proposal_id"), "request": body, "status": status,
                  "response": resp if resp is not None else raw, "analysis": analysis,
                  "usage": resp.get("usage") if isinstance(resp, dict) else None,
                  **({"transport_error": transport} if transport else {})}
        path = self.log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        if not ok:
            raise DemoError(f"HTTP {status} from {url}")
        return record
