"""D.3b arm A5/A6 forecast sidecar: client path, image choice and fallback accounting (gap G9). AI-assisted (Claude).

ENGINEERING_ONLY until a signed D.3b note cites the reviewed unit.  Source: the D.3 pre-declaration revision 4 §6
(A5 = ``SidecarPrior`` against ``r1/c3/serve.py`` with the pinned adapter, head and calibration map; on a sidecar
failure the fallback prior answers and ``prior_unavailable`` is logged; the sidecar costs compute only), §10 (more
than 1 % of A5/A6 forecasts answered by the fallback is a STOP; a pin mismatch is a STOP), §12 G9 and §13 item 16
(the sidecar image: **open**), and the rows R1-NO-TIMEOUT (no time limit decides anything) and R1-CARD-SHARE (3)
(an attempt lost to the card or host is an infrastructure failure, never an outcome).

**Why a D.3 client.**  ``prior_model.SidecarPrior`` answers *every* error with the fallback prior, a 1 s timeout
included.  Under R1-NO-TIMEOUT a time limit must not decide a forecast, and under R1-CARD-SHARE a sidecar lost to the
host is infrastructure, not an outcome.  ``D3SidecarPrior`` therefore splits the failures (``SIDECAR_FAILURE_RULE``,
an author item: the unit report's draft row R1-D3B-SIDECAR-FAILURES):

* **no answer yet** -> the call is **waited for**, on the same connection, without a read time limit and without
  re-issuing it (a re-issue would queue behind the unanswered request, since ``serve.Sidecar`` serialises
  forecasts).  Only the connection set-up has a guard (``connect_timeout_s``).  While waiting, a progress record is
  written every ``poll_s`` seconds (``on_progress``), so the operator / G1 can see a call that makes no progress
  and end it as an infrastructure failure (R1-NO-TIMEOUT (1)); the client never decides that itself;
* **the connection fails** (refused, reset, closed, unreachable, an incomplete or unreadable HTTP exchange: every
  ``OSError`` and ``http.client.HTTPException``) -> ``SidecarLost``: an infrastructure failure; the runner seals the
  attempt and attempts the chunk again whole (§3.1 item 3);
* **an answer that is an error** (an HTTP status other than 200, a body that is not a JSON object with a
  ``digest``, probabilities that are not 12 finite numbers) -> the fallback prior answers and ``prior_unavailable``
  is logged (§6), counted against the 1 % STOP (``fallback_stop``);
* **a well-formed answer whose digest differs from the pin** -> ``SidecarPinMismatch``: a STOP (§10).

``prior_model.SidecarPrior`` is unchanged.  ``D3SidecarRuleController`` is ``RuleController`` with the client's wait
record (``sidecar_wait_polls``, ``sidecar_wait_s``, ``failure_rule``) copied into the E1 decision detail, so it
reaches the ledger.

**Path.**  The sidecar is co-resident with the proposer in the D.3b job (§12 G9); ``sidecar_url`` and the client
accept only ``http`` on a loopback address.

**Image (§13 item 16, open).**  ``SIDECAR_IMAGE_CHOICE`` is ``None``: ``resolve_sidecar_image`` refuses until the
author settles item 16.  The candidates are the v1 proposer image (the digest on ``main``, R1-SWEEP2-IMAGE; whether
it carries the sidecar's stack is unchecked) and the Track P training image (provisional preference of §13 item 16;
its current digest is not on ``main`` -- R1-TRACKP-IMAGE-V22 rebuilds it -- so it must be passed explicitly).
"""
from __future__ import annotations

import http.client
import json
import math
import re
import select
import time
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlparse

from r1.c3.control import RuleController
from r1.c3.prior_model import Forecast, SidecarPrior

SIDECAR_FAILURE_RULE = "d3_sidecar_failures/v2"   # wait (no read limit); lost -> infrastructure; error -> fallback;
                                                  # pin -> STOP
FALLBACK_STOP_SHARE = 0.01                        # §10: more than 1 % of A5/A6 forecasts by the fallback is a STOP
SIDECAR_ARMS = ("A5", "A6")
CONNECT_TIMEOUT_S = 10.0                          # connection set-up guard only; a refused connection is SidecarLost
POLL_S = 30.0                                     # progress record interval while waiting (operational)
WAIT_DETAIL_KEYS = ("sidecar_wait_polls", "sidecar_wait_s", "failure_rule")
V1_IMAGE = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296"
SIDECAR_IMAGE_CHOICE: str | None = None           # §13 item 16: open author item; "v1" or "trackp" once settled
_DIGEST_REF = re.compile(r"^ghcr\.io/dowlingwong/[a-z0-9._-]+@sha256:[0-9a-f]{64}$")
_LOOPBACK = ("127.0.0.1", "localhost", "::1")


class SidecarLost(RuntimeError):
    """The co-resident sidecar cannot be reached: an infrastructure failure (§3.1); the chunk is attempted again."""


class SidecarPinMismatch(RuntimeError):
    """The sidecar serves another digest than the pin: a STOP (§10)."""


def resolve_sidecar_image(choice: str | None = SIDECAR_IMAGE_CHOICE, *, trackp_ref: str | None = None) -> str:
    """The digest-pinned image of the A5/A6 sidecar; refuses while §13 item 16 is open (``choice`` None)."""
    if choice is None:
        raise ValueError("the D.3b sidecar image is an open author item (pre-declaration §13 item 16)")
    if choice == "v1":
        if trackp_ref is not None:
            raise ValueError("choice 'v1' takes no Track P reference")
        return V1_IMAGE
    if choice == "trackp":
        if not isinstance(trackp_ref, str) or not _DIGEST_REF.fullmatch(trackp_ref) or trackp_ref == V1_IMAGE:
            raise ValueError("choice 'trackp' needs the Track P image as 'ghcr.io/dowlingwong/<name>@sha256:<64 hex>' "
                             "from its image report")
        return trackp_ref
    raise ValueError(f"unknown sidecar image choice {choice!r}")


def sidecar_url(port: int, host: str = "127.0.0.1") -> str:
    """The URL of the co-resident sidecar; only loopback hosts are accepted."""
    if host not in _LOOPBACK:
        raise ValueError("the D.3 sidecar is co-resident with the proposer: loopback only")
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("port must be an integer in 1..65535")
    return f"http://[{host}]:{port}" if host == "::1" else f"http://{host}:{port}"


def _body(row: Mapping[str, Any]) -> bytes:
    """The request body of ``SidecarPrior._post`` (same row fields)."""
    return json.dumps({"row": {"node": row["node"], "features": row["features"],
                               **({"edit": row["edit"]} if row.get("edit") is not None else {}),
                               **({"prompt": row["prompt"]} if row.get("prompt") is not None else {})}},
                      sort_keys=True, default=str).encode()


class D3SidecarPrior(SidecarPrior):
    """``SidecarPrior`` with the D.3 failure rule (module docstring).  ``expected_digest`` is required (the pin of
    the arms-frozen record).  ``on_progress(record)`` receives a progress record every ``poll_s`` seconds while a
    call waits; by default records are kept in ``progress_log``."""

    def __init__(self, url: str, fallback, *, name: str, expected_digest: str,
                 connect_timeout_s: float = CONNECT_TIMEOUT_S, poll_s: float = POLL_S,
                 on_progress: Callable[[dict], Any] | None = None) -> None:
        if name not in SIDECAR_ARMS:
            raise ValueError(f"the D.3 sidecar serves {SIDECAR_ARMS} only")
        if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
            raise ValueError("expected_digest must be the 64-hex pin digest (an unpinned sidecar is refused)")
        parsed = urlparse(url)
        if parsed.scheme != "http" or parsed.hostname not in _LOOPBACK or parsed.port is None:
            raise ValueError("the D.3 sidecar is co-resident with the proposer: http on a loopback host and port only")
        if not (connect_timeout_s > 0 and poll_s > 0):
            raise ValueError("connect_timeout_s and poll_s must be positive")
        super().__init__(url, fallback, name=name, expected_digest=expected_digest, timeout_s=connect_timeout_s,
                         rule_layer=True)
        self.host, self.port = parsed.hostname, parsed.port
        self.version = f"{name}/sidecar_d3/v2"
        self.connect_timeout_s, self.poll_s = float(connect_timeout_s), float(poll_s)
        self.progress_log: list[dict] = []
        self.on_progress = on_progress if on_progress is not None else self.progress_log.append
        self.forecasts = self.fallbacks = self.wait_polls = 0

    def _exchange(self, row: Mapping[str, Any]) -> tuple[int, bytes, int, float]:
        """One request, waited for without a read limit; any connection failure is ``SidecarLost``."""
        t0 = time.monotonic()
        polls = 0
        conn = http.client.HTTPConnection(self.host, self.port, timeout=self.connect_timeout_s)
        try:
            conn.connect()
            conn.sock.settimeout(None)  # no read time limit: an unanswered call is waited for (R1-NO-TIMEOUT)
            conn.request("POST", "/forecast", body=_body(row), headers={"Content-Type": "application/json"})
            while not select.select([conn.sock], [], [], self.poll_s)[0]:
                polls += 1
                self.wait_polls += 1
                self.on_progress({"event": "sidecar_waiting", "url": self.url, "polls": polls,
                                  "waited_s": time.monotonic() - t0, "failure_rule": SIDECAR_FAILURE_RULE})
            resp = conn.getresponse()
            status, data = resp.status, resp.read()
        except (OSError, http.client.HTTPException) as exc:
            raise SidecarLost(f"sidecar at {self.url} lost: {exc!r}"[:300]) from exc
        finally:
            conn.close()
        return status, data, polls, time.monotonic() - t0

    def forecast(self, row: Mapping[str, Any]) -> Forecast:
        t0 = time.perf_counter()
        status, data, polls, waited = self._exchange(row)
        wait = {"sidecar_wait_polls": polls, "sidecar_wait_s": waited, "failure_rule": SIDECAR_FAILURE_RULE}
        try:
            if status != 200:
                raise ValueError(f"HTTP {status}")
            reply = json.loads(data.decode())
            if not isinstance(reply, dict) or not isinstance(reply.get("digest"), str):
                raise ValueError("the reply is not a JSON object with a digest")
        except Exception as exc:  # noqa: BLE001 - an answer that is an error
            return self._fallback(row, t0, exc, wait)
        if reply["digest"] != self.expected_digest:
            raise SidecarPinMismatch(f"sidecar digest {reply['digest']!r} != pin {self.expected_digest!r}")
        try:
            probs = tuple(float(x) for x in reply["probs"])
            if len(probs) != 12 or not all(math.isfinite(p) for p in probs):
                raise ValueError("not 12 finite probabilities")
            compute_s = float(reply.get("compute_s", 0.0))
        except Exception as exc:  # noqa: BLE001 - a malformed answer is an answer that is an error
            return self._fallback(row, t0, exc, wait)
        self.forecasts += 1
        return Forecast(probs=probs, version=str(reply.get("version", self.version)), digest=self.expected_digest,
                        latency_s=time.perf_counter() - t0, info={"sidecar_compute_s": compute_s, **wait})

    def _fallback(self, row, t0, exc, wait) -> Forecast:
        self.forecasts += 1
        self.fallbacks += 1
        fb = self.fallback.forecast(row)
        return Forecast(probs=fb.probs, version=self.version, digest=self.digest,
                        latency_s=time.perf_counter() - t0, fallback=f"prior_unavailable: {type(exc).__name__}",
                        info={"error": repr(exc)[:300], "fallback_version": fb.version, "fallback_digest": fb.digest,
                              **wait})


class D3SidecarRuleController(RuleController):
    """``RuleController`` (A5/A6 as §6) that also copies the D.3 client's wait record into the E1 decision detail."""

    def _fill(self, plan, res, view) -> dict:
        numbers = super()._fill(plan, res, view)
        info = plan.forecast.info if plan.forecast is not None else {}
        numbers.update({k: info[k] for k in WAIT_DETAIL_KEYS if k in info})
        return numbers


def fallback_stop(campaign_events: Iterable[Iterable[dict]]) -> dict:
    """§10: over the A5/A6 campaigns of a stage, count sidecar forecasts (``control_decision`` details, at any epoch,
    that carry a sidecar forecast or a fallback: E1 forecasts and E2 re-forecasts alike) and ``prior_unavailable``
    events; ``stop`` iff fallbacks > 1 % of forecasts.

    Caller contract: pass the event streams of the stage's A5/A6 campaigns only, from their non-sealed attempts
    (an attempt lost to infrastructure is sealed, §3.1, and never enters a count)."""
    forecasts = fallbacks = 0
    for events in campaign_events:
        for e in events:
            if e.get("event_type") == "prior_unavailable":
                fallbacks += 1
            elif e.get("event_type") == "control_decision":
                d = (e.get("payload") or {}).get("detail") or {}
                if "sidecar_compute_s" in d or str(d.get("fallback") or "").startswith("prior_unavailable"):
                    forecasts += 1
    if fallbacks > forecasts:
        raise ValueError("more prior_unavailable events than forecasts: the event streams are inconsistent")
    share = fallbacks / forecasts if forecasts else 0.0
    return {"forecasts": forecasts, "fallbacks": fallbacks, "share": share, "threshold": FALLBACK_STOP_SHARE,
            "stop": share > FALLBACK_STOP_SHARE}
