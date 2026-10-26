"""Jev zero-shot rung through TypeSafe's official System One API (PLAN R1-JEV-RUNG; spec §5.1). ENGINEERING_ONLY; AI-assisted (Claude).

API (read 26 Oct 2026 from the public docs, no key):
- ``POST https://api.typesafe.ai/v1/systemone`` (https://docs.typesafe.ai/api/system-one.md), header
  ``Authorization: Bearer <key>``, JSON body ``{"model", "state", "questions": {name: {"type": "noul",
  "instructions", "criteria": {"true", "false"}}}}``; response ``{"model", "answers": {name: {"type": "noul",
  "noul": p}}, "usage": {"input_tokens", "output_tokens"}}``. The response ``model`` is "the model that answered the
  questions. May differ from the alias supplied in the request".
- Versioned model IDs ``jev-1.14.0`` / ``jev-1.13.0``; aliases (``jev-latest``, ...) point to a moving ID
  (https://docs.typesafe.ai/models.md). Errors: 400/401/413/415/422/429/529 (https://docs.typesafe.ai/api/errors.md).

Protocol (spec §5.1): one request per state and repeat, all questions as branches on one shared state; three repeats
per state (responses vary by about +-0.02); every request and response logged in full (the key never: it is read
from ``TYPESAFE_API_KEY`` and only placed in the request header, which is not logged). The config pins a versioned
model ID; an alias is refused, and a response naming another model raises ``JevVersionMismatch`` (a STOP).

Questions and bins. ``labels.EDGES`` has 10 finite edges between the 11 non-inert bins, so "one Noul per bin edge"
gives 10 questions ``z > e_k``; the 11th question is the inert bin ("does the edit leave the active configuration
unchanged?"), which makes the 11 questions of the runbook and fills bin 0 (``include_inert=False`` sends only the 10
edge questions and puts no mass on bin 0). Bins: p0 = P(inert); the edge answers S_k = P(z > e_k) give a CDF
F_k = 1 - S_k made monotone by a cumulative max over the sorted edges; bins 1..11 = (1 - p0) * diff([0, F, 1]).
No Jev output is ever a training label.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from r1.c3.labels import EDGES, N_BINS
from r1.c3.train.types import DecisionPrompt

REPO = Path(__file__).resolve().parents[2]
BASE_URL = "https://api.typesafe.ai"
ENDPOINT = "/v1/systemone"
KEY_ENV = "TYPESAFE_API_KEY"
CLIENT_VERSION = "jev_client/v1"
VERSIONED = re.compile(r"^jev-\d+\.\d+\.\d+$")
REPEATS = 3
FINITE_EDGES = tuple(float(e) for e in EDGES[1:-1])  # 10 interior edges, increasing
INERT_Q = "inert"


class JevError(RuntimeError):
    pass


class JevVersionMismatch(RuntimeError):
    """The API answered with a model other than the pinned one: STOP (R1-JEV-RUNG). Deliberately *not* a
    ``JevError``, so a caller that retries or skips on ``JevError`` cannot swallow it."""


def edge_name(k: int) -> str:
    return f"z_gt_e{k:02d}"


@dataclass(frozen=True)
class JevConfig:
    model: str                      # a versioned model ID, e.g. "jev-1.14.0"
    base_url: str = BASE_URL
    repeats: int = REPEATS
    include_inert: bool = True
    timeout_s: float = 60.0
    log_root: Path = field(default=REPO / "results" / "track_p" / "jev")

    def __post_init__(self) -> None:
        if not VERSIONED.match(self.model):
            raise JevError(f"model must be a versioned ID like 'jev-1.14.0', not {self.model!r} (aliases move)")
        if self.repeats < 1:
            raise JevError("repeats must be >= 1")


def questions(include_inert: bool = True) -> dict:
    """The Noul questions of one state: one per finite bin edge (+ the inert bin)."""
    qs = {}
    if include_inert:
        qs[INERT_Q] = {"type": "noul",
                       "instructions": "Does the proposed edit leave the active configuration unchanged (a no-op)?",
                       "criteria": {"true": "Only inactive keys change, or the edit returns to the incumbent's active "
                                            "configuration, so the metric cannot change.",
                                    "false": "The edit changes the active configuration."}}
    for k, e in enumerate(FINITE_EDGES, start=1):
        qs[edge_name(k)] = {"type": "noul",
                            "instructions": (f"Will this proposed edit change the validation metric by more than "
                                             f"z = {e:g} noise units (z = change / sigma_node; positive is better)?"),
                            "criteria": {"true": f"The standardised change z is greater than {e:g}.",
                                         "false": f"The standardised change z is at most {e:g}."}}
    return qs


def state_text(prompt: DecisionPrompt) -> str:
    """The shared state of the request: the loop state and the proposal (never meta, labels or audit fields)."""
    if not isinstance(prompt, DecisionPrompt):
        raise TypeError("state_text takes a DecisionPrompt")
    return f"{prompt.state}\n\nProposed edit:\n{prompt.proposal}"


def request_body(prompt: DecisionPrompt, cfg: JevConfig) -> dict:
    return {"model": cfg.model, "state": state_text(prompt), "questions": questions(cfg.include_inert)}


def bins_from_answers(answers: dict, include_inert: bool = True) -> np.ndarray:
    """12-bin distribution from Noul answers (monotone CDF by cumulative max over the sorted edges)."""
    try:
        s = np.array([float(answers[edge_name(k)]["noul"]) for k in range(1, len(FINITE_EDGES) + 1)])
        p0 = float(answers[INERT_Q]["noul"]) if include_inert else 0.0
    except (KeyError, TypeError, ValueError) as exc:
        raise JevError(f"incomplete or malformed answers: {exc}") from exc
    if not (np.all((s >= 0) & (s <= 1)) and 0 <= p0 <= 1):
        raise JevError("noul probabilities outside [0, 1]")
    cdf = np.maximum.accumulate(1.0 - s)
    p = np.zeros(N_BINS)
    p[0] = p0
    p[1:] = (1.0 - p0) * np.diff(np.concatenate([[0.0], cdf, [1.0]]))
    return p


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class JevClient:
    """One request per (state, repeat); ``forecast`` returns the mean 12-bin distribution and its spread."""

    def __init__(self, cfg: JevConfig, clock=_now, env=os.environ) -> None:
        self.cfg = cfg
        self.clock = clock
        key = env.get(KEY_ENV)
        if not key:
            raise JevError(f"{KEY_ENV} is not set (the author places ~/.config/r1/secrets.env; STOP)")
        self._key = key
        self.log_path = Path(cfg.log_root) / clock().strftime("%Y%m%d") / "calls.jsonl"

    def _log(self, record: dict) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

    def call(self, prompt: DecisionPrompt, repeat: int = 0) -> dict:
        body = request_body(prompt, self.cfg)
        url = self.cfg.base_url.rstrip("/") + ENDPOINT
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {self._key}"})
        record = {"client": CLIENT_VERSION, "endpoint": url, "date": self.clock().isoformat(),
                  "model_requested": self.cfg.model, "prompt_id": prompt.meta.get("proposal_id"),
                  "group": prompt.group, "repeat": repeat, "request": body,
                  "request_headers": {"Content-Type": "application/json", "Authorization": "Bearer <redacted>"}}
        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_s) as r:
                status, raw = r.status, r.read().decode()
        except urllib.error.HTTPError as exc:
            status, raw = exc.code, exc.read().decode(errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:   # transport failure: logged, then raised
            record.update(status=None, transport_error=repr(exc)[:300], response=None, model_returned=None)
            self._log(record)
            raise JevError(f"transport failure calling {url}: {exc!r}") from exc
        record.update(status=status, response_raw=raw)
        try:
            resp = json.loads(raw)
        except json.JSONDecodeError:
            resp = None
        record["response"] = resp
        record["model_returned"] = resp.get("model") if isinstance(resp, dict) else None
        self._log(record)
        if status != 200 or not isinstance(resp, dict):
            raise JevError(f"HTTP {status} from {url}")
        if resp.get("model") != self.cfg.model:
            raise JevVersionMismatch(f"pinned {self.cfg.model!r}, API answered with {resp.get('model')!r}: STOP")
        return resp

    def forecast(self, prompt: DecisionPrompt) -> dict:
        reps = [bins_from_answers(self.call(prompt, r)["answers"], self.cfg.include_inert)
                for r in range(self.cfg.repeats)]
        arr = np.stack(reps)
        return {"probs": arr.mean(axis=0).tolist(), "repeats": arr.tolist(),
                "spread": (arr.max(axis=0) - arr.min(axis=0)).tolist(), "model": self.cfg.model}
