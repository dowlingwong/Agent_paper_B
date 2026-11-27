"""D.3b arm A5/A6 forecast sidecar: client path, image choice and fallback accounting (gap G9). AI-assisted (Claude).

ENGINEERING_ONLY until a signed D.3b note cites the reviewed unit.  Source: the D.3 pre-declaration revision 4 §6
(A5 = ``SidecarPrior`` against ``r1/c3/serve.py`` with the pinned adapter, head and calibration map; on a sidecar
failure the fallback prior answers and ``prior_unavailable`` is logged; the sidecar costs compute only), §10 (more
than 1 % of A5/A6 forecasts answered by the fallback is a STOP; a pin mismatch is a STOP), §12 G9 and §13 item 16
(the sidecar image: **open**), and the rows R1-NO-TIMEOUT (no time limit decides anything) and R1-CARD-SHARE (3)
(an attempt lost to the card or host is an infrastructure failure, never an outcome).

**Why a D.3 client.**  ``prior_model.SidecarPrior`` answers *every* error with the fallback prior, a 1 s timeout
included.  Under R1-NO-TIMEOUT a time limit must not decide a forecast, and under R1-CARD-SHARE a sidecar lost to the
host is infrastructure, not an outcome; a fallback there would change the arm's decisions and count towards the §10
STOP.  ``D3SidecarPrior`` therefore splits the failures (``SIDECAR_FAILURE_RULE``):

* **no answer within the transport timeout** -> the *same* request is issued again (same row; the forecast is
  deterministic), without limit, and each re-issue is counted (``reissued``, descriptive).  The transport timeout
  is an operational poll interval, never a decision;
* **connection refused / reset** (the co-resident sidecar is gone) -> ``SidecarLost``: an infrastructure failure;
  the runner seals the attempt and attempts the chunk again whole (§3.1 item 3);
* **digest differs from the pin** -> ``SidecarPinMismatch``: a pin mismatch is a STOP (§10);
* **an answer that is an error** (HTTP 5xx, a malformed reply, probabilities that are not 12 finite numbers) -> the
  fallback prior answers and ``prior_unavailable`` is logged (§6), counted against the 1 % STOP
  (``fallback_stop``).

This split is this unit's reading of R1-NO-TIMEOUT for the sidecar, which revision 4 does not spell out; it is
listed as an open question in the unit report.  ``prior_model.SidecarPrior`` is unchanged.

**Path.**  The sidecar is co-resident with the proposer in the D.3b job (§12 G9: "HTCondor co-residence of the
sidecar with llama-server"); ``sidecar_url`` accepts only a loopback address.

**Image (§13 item 16, open).**  ``SIDECAR_IMAGE_CHOICE`` is ``None``: ``resolve_sidecar_image`` refuses until the
author settles item 16.  The candidates are the v1 proposer image (the digest on ``main``, R1-SWEEP2-IMAGE; whether
it carries the sidecar's stack is unchecked) and the Track P training image (provisional preference of §13 item 16;
its current digest is not on ``main`` -- R1-TRACKP-IMAGE-V22 rebuilds it -- so it must be passed explicitly).
"""
from __future__ import annotations

import http.client
import re
import socket
import time
import urllib.error
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from r1.c3.prior_model import SIDECAR_TIMEOUT_S, Forecast, SidecarPrior

SIDECAR_FAILURE_RULE = "d3_sidecar_failures/v1"   # timeout -> reissue; lost -> infrastructure; pin -> STOP; else fallback
FALLBACK_STOP_SHARE = 0.01                        # §10: more than 1 % of A5/A6 forecasts by the fallback is a STOP
SIDECAR_ARMS = ("A5", "A6")
V1_IMAGE = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296"
TRACKP_IMAGE_REPO = "ghcr.io/dowlingwong/"
SIDECAR_IMAGE_CHOICE: str | None = None           # §13 item 16: open author item; "v1" or "trackp" once settled
_DIGEST_REF = re.compile(r"^ghcr\.io/dowlingwong/[a-z0-9._-]+@sha256:[0-9a-f]{64}$")


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
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("the D.3 sidecar is co-resident with the proposer: loopback only")
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("port must be an integer in 1..65535")
    return f"http://[{host}]:{port}" if host == "::1" else f"http://{host}:{port}"


def _is_timeout(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    reason = getattr(exc, "reason", None)
    return isinstance(reason, (TimeoutError, socket.timeout)) or "timed out" in str(exc)


def _is_lost(exc: BaseException) -> bool:
    lost = (ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError, BrokenPipeError,
            http.client.RemoteDisconnected)
    if isinstance(exc, lost):
        return True
    return isinstance(exc, urllib.error.URLError) and isinstance(getattr(exc, "reason", None), lost)


class D3SidecarPrior(SidecarPrior):
    """``SidecarPrior`` with the D.3 failure rule (module docstring).  ``expected_digest`` is required (the pin of
    the arms-frozen record); ``sleep_s`` is the pause between re-issues (operational)."""

    def __init__(self, url: str, fallback, *, name: str, expected_digest: str, timeout_s: float = SIDECAR_TIMEOUT_S,
                 sleep_s: float = 0.0) -> None:
        if name not in SIDECAR_ARMS:
            raise ValueError(f"the D.3 sidecar serves {SIDECAR_ARMS} only")
        if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
            raise ValueError("expected_digest must be the 64-hex pin digest (an unpinned sidecar is refused)")
        host = urlparse(url).hostname
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError("the D.3 sidecar is co-resident with the proposer: loopback only")
        super().__init__(url, fallback, name=name, expected_digest=expected_digest, timeout_s=timeout_s,
                         rule_layer=True)
        self.version = f"{name}/sidecar_d3/v1"
        self.sleep_s = float(sleep_s)
        self.reissued = 0
        self.forecasts = 0
        self.fallbacks = 0

    def forecast(self, row: Mapping[str, Any]) -> Forecast:
        t0 = time.perf_counter()
        reissues = 0
        while True:
            try:
                reply = self._post(row)
                break
            except Exception as exc:  # noqa: BLE001 - classified below
                if _is_timeout(exc):
                    reissues += 1
                    self.reissued += 1
                    if self.sleep_s:
                        time.sleep(self.sleep_s)
                    continue
                if _is_lost(exc):
                    raise SidecarLost(f"sidecar at {self.url} lost: {exc!r}"[:300]) from exc
                return self._fallback(row, t0, exc, reissues)
        self.forecasts += 1
        if reply.get("digest") != self.expected_digest:
            raise SidecarPinMismatch(f"sidecar digest {reply.get('digest')!r} != pin {self.expected_digest!r}")
        try:
            probs = tuple(float(x) for x in reply["probs"])
            if len(probs) != 12 or not all(p == p and p not in (float("inf"), float("-inf")) for p in probs):
                raise ValueError("not 12 finite probabilities")
        except Exception as exc:  # noqa: BLE001 - a malformed answer is an answer that is an error
            self.forecasts -= 1
            return self._fallback(row, t0, exc, reissues)
        return Forecast(probs=probs, version=str(reply.get("version", self.version)), digest=self.expected_digest,
                        latency_s=time.perf_counter() - t0,
                        info={"sidecar_compute_s": float(reply.get("compute_s", 0.0)), "sidecar_reissued": reissues,
                              "failure_rule": SIDECAR_FAILURE_RULE})

    def _fallback(self, row, t0, exc, reissues) -> Forecast:
        self.forecasts += 1
        self.fallbacks += 1
        fb = self.fallback.forecast(row)
        return Forecast(probs=fb.probs, version=self.version, digest=self.digest,
                        latency_s=time.perf_counter() - t0, fallback=f"prior_unavailable: {type(exc).__name__}",
                        info={"error": repr(exc)[:300], "fallback_version": fb.version, "fallback_digest": fb.digest,
                              "sidecar_reissued": reissues, "failure_rule": SIDECAR_FAILURE_RULE})


def fallback_stop(campaign_events: Iterable[Iterable[dict]]) -> dict:
    """§10: over the A5/A6 campaigns of a stage, count E1 forecasts (control-decision details with a sidecar
    forecast or a fallback) and ``prior_unavailable`` events; ``stop`` iff fallbacks > 1 % of forecasts."""
    forecasts = fallbacks = 0
    for events in campaign_events:
        for e in events:
            if e.get("event_type") == "prior_unavailable":
                fallbacks += 1
            elif e.get("event_type") == "control_decision":
                d = (e.get("payload") or {}).get("detail") or {}
                if "sidecar_compute_s" in d or str(d.get("fallback") or "").startswith("prior_unavailable"):
                    forecasts += 1
    share = fallbacks / forecasts if forecasts else 0.0
    if fallbacks > forecasts:
        raise ValueError("more prior_unavailable events than forecasts: the event streams are inconsistent")
    return {"forecasts": forecasts, "fallbacks": fallbacks, "share": share, "threshold": FALLBACK_STOP_SHARE,
            "stop": share > FALLBACK_STOP_SHARE}
