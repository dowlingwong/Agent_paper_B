"""Per-completion substrate identity and the completion/usage ledger (WP2).

Two rules live here.

**The identity rule is fatal.** Every completion must return the signed model ID
and the expected `system_fingerprint`. A missing value, a changed value, or a
different response model is `substrate_identity_mismatch`: it invalidates and
stops the entire stage, is *not* retried as a branch failure, and is *not*
scored as an unresolved outcome. Data is never pooled across fingerprints,
because two fingerprints are two backend configurations and the study's claim is
about one substrate.

**The ledger is exact.** A tool loop produces several model completions per
branch, so a single `usage` summary silently undercounts. Every completion is
recorded individually, deduplicated by completion ID, checked against the
provider's own token arithmetic, and summed component-wise. A duplicate event
never double-charges; a duplicate ID with different contents is fatal.

Nothing in this module makes a model call, and nothing here ever accepts,
stores, or digests an API key.
"""

from __future__ import annotations

import json

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

MISMATCH_KIND = "substrate_identity_mismatch"


class SubstrateIdentityMismatch(RuntimeError):
    """Fatal: the substrate that answered is not the substrate that was signed.

    Carries the incident record so the caller can persist evidence before exit.
    """

    def __init__(self, message: str, incident: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.incident = dict(incident)


class CompletionLedgerError(RuntimeError):
    """The completion ledger is not internally consistent (fatal for the stage)."""


@dataclass(frozen=True)
class SubstrateIdentity:
    """The identity a stage is bound to.

    `expected_system_fingerprint` is `None` only before the replacement contract
    is signed: fingerprints are then *recorded* (so an audit can establish that
    one value is observed consistently) but not yet *enforced*. Once signed it is
    always set, and `enforce_fingerprint` is what makes a missing value fatal.
    """

    base_url: str
    model_id: str
    expected_system_fingerprint: str | None = None
    request_contract_sha256: str = ""
    enforce_fingerprint: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompletionUsage:
    """One completion's token accounting, in the provider's own decomposition."""

    prompt_tokens: int
    prompt_cache_hit_tokens: int
    prompt_cache_miss_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    total_tokens: int
    #: Did the provider actually REPORT a cached-prompt figure?
    #:
    #: A server that reports no cache metric at all used to be indistinguishable
    #: from a server that reported zero, because the parse below defaults the
    #: hit count to 0. Under `cache_isolation_mode: disabled` that turns "we
    #: cannot see whether the cache was used" into "the cache was not used" --
    #: a silent pass on the one property the isolation gate exists to check.
    #: Round 5-Titan's criterion is the correct one and is now enforced here
    #: too: the figure must be PRESENT and zero. Defaults True so that
    #: constructed (scripted, fixture) usage is unaffected.
    prompt_cache_metric_present: bool = True

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    def __add__(self, other: "CompletionUsage") -> "CompletionUsage":
        return CompletionUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            prompt_cache_hit_tokens=self.prompt_cache_hit_tokens + other.prompt_cache_hit_tokens,
            prompt_cache_miss_tokens=self.prompt_cache_miss_tokens + other.prompt_cache_miss_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            # Absence is contagious: a sum that includes one unreported
            # completion cannot claim the cache figure was observed.
            prompt_cache_metric_present=(
                self.prompt_cache_metric_present and other.prompt_cache_metric_present),
        )

    @classmethod
    def zero(cls) -> "CompletionUsage":
        return cls(0, 0, 0, 0, 0, 0)


ZERO_USAGE = CompletionUsage.zero()


def _nonnegative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CompletionLedgerError(f"usage field {field_name} must be an integer, got {value!r}")
    if value < 0:
        raise CompletionLedgerError(f"usage field {field_name} must be nonnegative, got {value}")
    return value


def parse_usage(raw: Mapping[str, Any] | None) -> CompletionUsage:
    """Validate one provider usage block.

    DeepSeek documents `prompt_tokens`, `completion_tokens`, `total_tokens`,
    `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens`. Both documented
    identities are enforced, because an expense computed from components that do
    not add up cannot be reconciled against an invoice.
    """
    if not isinstance(raw, Mapping):
        raise CompletionLedgerError("completion has no usage block")
    prompt = _nonnegative_int(raw.get("prompt_tokens"), "prompt_tokens")
    completion = _nonnegative_int(raw.get("completion_tokens"), "completion_tokens")
    total = _nonnegative_int(raw.get("total_tokens"), "total_tokens")
    metric_present = True
    if "prompt_cache_hit_tokens" in raw or "prompt_cache_miss_tokens" in raw:
        hit = _nonnegative_int(raw.get("prompt_cache_hit_tokens", 0), "prompt_cache_hit_tokens")
        miss = _nonnegative_int(raw.get("prompt_cache_miss_tokens", 0), "prompt_cache_miss_tokens")
    else:
        # A provider that reports only `prompt_tokens_details.cached_tokens`
        # still determines the split: the remainder is a cache miss.
        details = raw.get("prompt_tokens_details")
        # PRESENT means the provider stated a figure, not that the figure is
        # non-zero. A missing block, or a block without the key, is absence.
        metric_present = (
            isinstance(details, Mapping) and "cached_tokens" in details)
        hit = _nonnegative_int(
            (details or {}).get("cached_tokens", 0) if isinstance(details, Mapping) else 0,
            "prompt_tokens_details.cached_tokens",
        )
        miss = prompt - hit
        if miss < 0:
            raise CompletionLedgerError(
                f"cached_tokens {hit} exceeds prompt_tokens {prompt}"
            )
    reasoning_details = raw.get("completion_tokens_details")
    reasoning = _nonnegative_int(
        (reasoning_details or {}).get("reasoning_tokens", 0)
        if isinstance(reasoning_details, Mapping)
        else raw.get("reasoning_tokens", 0) or 0,
        "reasoning_tokens",
    )
    if hit + miss != prompt:
        raise CompletionLedgerError(
            f"prompt_tokens {prompt} != cache hit {hit} + cache miss {miss}"
        )
    if prompt + completion != total:
        raise CompletionLedgerError(
            f"total_tokens {total} != prompt_tokens {prompt} + completion_tokens {completion}"
        )
    return CompletionUsage(
        prompt_cache_metric_present=metric_present,
        prompt_tokens=prompt,
        prompt_cache_hit_tokens=hit,
        prompt_cache_miss_tokens=miss,
        completion_tokens=completion,
        reasoning_tokens=reasoning,
        total_tokens=total,
    )


@dataclass(frozen=True)
class CompletionRecord:
    """One model completion, with the identity and accounting it must carry."""

    completion_id: str
    response_model: str | None
    system_fingerprint: str | None
    provider_created_utc: str | None
    finish_reason: str | None
    usage: CompletionUsage
    request_contract_sha256: str = ""
    user_id_sha256: str = ""
    root_id: str = ""
    branch_id: str = ""
    regime_id: str = ""
    repetition: int = 0
    retry_attempt: int = 0
    turn_index: int = 0
    completion_index: int = 0
    expected_cost_usd: float | None = None
    # Review finding F3: a wall-clock stamp per completion is what makes a
    # time-of-day provider-drift effect measurable at all. Without it, drift
    # over a multi-day run is invisible rather than small.
    observed_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["usage"] = self.usage.to_dict()
        return record

    def content_digest(self) -> str:
        """Digest over everything except bookkeeping that may legitimately vary
        between two deliveries of the *same* completion event."""
        payload = {
            "completion_id": self.completion_id,
            "response_model": self.response_model,
            "system_fingerprint": self.system_fingerprint,
            "provider_created_utc": self.provider_created_utc,
            "finish_reason": self.finish_reason,
            "usage": self.usage.to_dict(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def provider_created_to_utc(created: Any) -> str | None:
    """Convert the provider's unix `created` seconds to an ISO-8601 UTC string."""
    if created is None:
        return None
    if isinstance(created, bool) or not isinstance(created, (int, float)):
        raise CompletionLedgerError(f"provider created time must be numeric, got {created!r}")
    return datetime.fromtimestamp(float(created), tz=timezone.utc).isoformat()


def provider_error_from_message(message: Mapping[str, Any]) -> dict[str, Any] | None:
    """Structure a provider error, or return None if this is not one.

    A provider error is not a completion. llama.cpp refusing a request -- an
    over-length prompt, say -- makes Pi record an assistant message with
    `stopReason: "error"`, zero usage and none of `responseId`, `providerUsage`
    or `systemFingerprint`, because no completion was ever produced.

    Passing that to `completion_from_message` raised "assistant message has no
    provider completion id", which is true but misdirects: it reads as a
    malformed completion when the branch actually failed on an HTTP error the
    provider reported in full. This preserves what the provider said and invents
    nothing -- no completion id, no response id, no usage record, no fingerprint.
    """
    if message.get("stopReason") != "error":
        return None
    raw = message.get("errorMessage")
    detail: dict[str, Any] = {
        "http_status": None, "error_type": None,
        "provider_message": raw if isinstance(raw, str) else None,
        "api": message.get("api"), "provider": message.get("provider"),
        "model": message.get("model"),
        # Stated explicitly so no downstream reader mistakes absence for loss.
        "completion_id": None, "response_id": None, "usage": None,
        "system_fingerprint": None,
        "is_completion": False, "counts_as_settlement": False,
    }
    if isinstance(raw, str):
        head, _, body = raw.partition(":")
        if head.strip().isdigit():
            detail["http_status"] = int(head.strip())
        try:
            parsed = json.loads(body.strip())
        except (ValueError, AttributeError):
            parsed = None
        if isinstance(parsed, Mapping):
            detail["error_type"] = parsed.get("type")
            detail["provider_message"] = parsed.get("message", raw)
            for key in ("n_prompt_tokens", "n_ctx", "code"):
                if key in parsed:
                    detail[key] = parsed[key]
    return detail


def completion_from_message(
    message: Mapping[str, Any],
    *,
    turn_index: int = 0,
    completion_index: int = 0,
    lineage: Mapping[str, Any] | None = None,
) -> CompletionRecord:
    """Build a completion record from one Pi `message_completed` assistant message.

    The identity fields come from the locally patched Pi
    (`systemFingerprint` / `providerModel` / `providerCreated` / `providerUsage`);
    a Pi build without that patch yields `None` for them, which the identity
    check then treats as a missing fingerprint rather than silently passing.
    """
    lineage = dict(lineage or {})
    completion_id = message.get("responseId")
    if not isinstance(completion_id, str) or not completion_id:
        raise CompletionLedgerError("assistant message has no provider completion id")
    raw_usage = message.get("providerUsage")
    if not isinstance(raw_usage, Mapping):
        raise CompletionLedgerError(
            f"completion {completion_id} has no provider usage block"
        )
    fingerprint = message.get("systemFingerprint")
    response_model = message.get("providerModel") or message.get("responseModel") or message.get("model")
    return CompletionRecord(
        completion_id=completion_id,
        response_model=str(response_model) if response_model else None,
        system_fingerprint=str(fingerprint) if isinstance(fingerprint, str) and fingerprint else None,
        provider_created_utc=provider_created_to_utc(message.get("providerCreated")),
        finish_reason=(str(message.get("rawStopReason")) if message.get("rawStopReason") else None),
        usage=parse_usage(raw_usage),
        turn_index=turn_index,
        completion_index=completion_index,
        observed_at_utc=_utc_now(),
        request_contract_sha256=str(lineage.get("request_contract_sha256", "")),
        user_id_sha256=str(lineage.get("user_id_sha256", "")),
        root_id=str(lineage.get("root_id", "")),
        branch_id=str(lineage.get("branch_id", "")),
        regime_id=str(lineage.get("regime_id", "")),
        repetition=int(lineage.get("repetition", 0)),
        retry_attempt=int(lineage.get("retry_attempt", 0)),
    )


def identity_incident(
    record: CompletionRecord, identity: SubstrateIdentity, reason: str
) -> dict[str, Any]:
    """The incident artifact written before a stage exits on identity failure.

    Deliberately excludes prompts, keys, and raw secrets: it must be safe to
    commit as evidence.
    """
    return {
        "schema_version": "0.1",
        "artifact_kind": MISMATCH_KIND,
        "qualifying": False,
        "reason": reason,
        "observed_at_utc": _utc_now(),
        "root_id": record.root_id,
        "branch_id": record.branch_id,
        "regime_id": record.regime_id,
        "repetition": record.repetition,
        "retry_attempt": record.retry_attempt,
        "turn_index": record.turn_index,
        "completion_index": record.completion_index,
        "completion_id": record.completion_id,
        "observed_model": record.response_model,
        "observed_system_fingerprint": record.system_fingerprint,
        "expected_model": identity.model_id,
        "expected_system_fingerprint": identity.expected_system_fingerprint,
        "request_contract_sha256": record.request_contract_sha256
        or identity.request_contract_sha256,
        "user_id_sha256": record.user_id_sha256,
        "provider_created_utc": record.provider_created_utc,
        "stage_action": "cancelled_and_invalidated",
        "retryable": False,
        "scored_as_unresolved_termination": False,
    }


def check_identity(record: CompletionRecord, identity: SubstrateIdentity) -> None:
    """Raise `SubstrateIdentityMismatch` unless this completion is in-contract."""
    if record.response_model is not None and record.response_model != identity.model_id:
        raise SubstrateIdentityMismatch(
            f"response model {record.response_model!r} is not the signed "
            f"{identity.model_id!r}",
            identity_incident(record, identity, "response_model_mismatch"),
        )
    if record.response_model is None:
        raise SubstrateIdentityMismatch(
            f"completion {record.completion_id} reported no response model",
            identity_incident(record, identity, "response_model_missing"),
        )
    if not identity.enforce_fingerprint:
        return
    if record.system_fingerprint is None:
        raise SubstrateIdentityMismatch(
            f"completion {record.completion_id} reported no system_fingerprint",
            identity_incident(record, identity, "system_fingerprint_missing"),
        )
    expected = identity.expected_system_fingerprint
    if expected is not None and record.system_fingerprint != expected:
        raise SubstrateIdentityMismatch(
            f"system_fingerprint {record.system_fingerprint!r} is not the signed {expected!r}",
            identity_incident(record, identity, "system_fingerprint_mismatch"),
        )


class CompletionLedger:
    """Every model completion of one scope, deduplicated and summed exactly."""

    def __init__(self, identity: SubstrateIdentity | None = None) -> None:
        self.identity = identity
        self._records: dict[str, CompletionRecord] = {}
        self._order: list[str] = []
        self.duplicate_events = 0

    def __len__(self) -> int:
        return len(self._order)

    @property
    def records(self) -> list[CompletionRecord]:
        return [self._records[key] for key in self._order]

    def add(self, record: CompletionRecord) -> CompletionRecord:
        """Record one completion.

        A repeated delivery of the same completion is dropped rather than
        charged twice. A repeated ID with different contents is fatal: the two
        cannot both be true, and guessing which is would corrupt the ledger.
        """
        if self.identity is not None:
            check_identity(record, self.identity)
        existing = self._records.get(record.completion_id)
        if existing is not None:
            if existing.content_digest() != record.content_digest():
                raise CompletionLedgerError(
                    f"conflicting duplicate completion id {record.completion_id}: "
                    "the same completion was reported with different contents"
                )
            self.duplicate_events += 1
            return existing
        self._records[record.completion_id] = record
        self._order.append(record.completion_id)
        return record

    def extend(self, records: Iterable[CompletionRecord]) -> None:
        for record in records:
            self.add(record)

    def aggregate_usage(self) -> CompletionUsage:
        total = ZERO_USAGE
        for record in self.records:
            total = total + record.usage
        return total

    def observed_fingerprints(self) -> list[str]:
        return sorted({r.system_fingerprint for r in self.records if r.system_fingerprint})

    def missing_fingerprints(self) -> int:
        return sum(1 for r in self.records if not r.system_fingerprint)

    def expected_cost_usd(self) -> float | None:
        priced = [r.expected_cost_usd for r in self.records if r.expected_cost_usd is not None]
        if len(priced) != len(self._order) or not priced:
            return None
        return float(sum(priced))

    def to_dict(self) -> dict[str, Any]:
        """The branch-level record: aggregate plus every completion's identity.

        Both halves are required — the aggregate alone loses the one-to-many
        chain that makes the accounting auditable.
        """
        usage = self.aggregate_usage()
        return {
            "completion_count": len(self._order),
            "duplicate_events_ignored": self.duplicate_events,
            "observed_system_fingerprints": self.observed_fingerprints(),
            "missing_system_fingerprints": self.missing_fingerprints(),
            "aggregate_usage": usage.to_dict(),
            "expected_cost_usd": self.expected_cost_usd(),
            "completions": [record.to_dict() for record in self.records],
        }


def merge_ledgers(ledgers: Sequence[CompletionLedger]) -> CompletionLedger:
    """Merge shard ledgers into a stage ledger.

    Order-independent by construction: dedup is by completion ID and the sum is
    component-wise, so any shard order yields the same aggregate and the same
    record set.
    """
    merged = CompletionLedger()
    for ledger in ledgers:
        for record in ledger.records:
            merged.add(record)
    return merged


K8_TOKEN_COMPONENTS = ("input_tokens", "output_tokens")


def usage_to_cost_components(
    usage: CompletionUsage, *, api_expense_usd: float | None = None
) -> dict[str, float]:
    """Map aggregated usage into the registered raw cost components.

    Input tokens stay decomposed into cache hit and miss rather than being
    scalarized: the two are priced differently, and the scientific cost outcome
    is a vector, not a scalar.
    """
    components: dict[str, float] = {
        "input_tokens": float(usage.prompt_tokens),
        "output_tokens": float(usage.completion_tokens),
        "input_cache_hit_tokens": float(usage.prompt_cache_hit_tokens),
        "input_cache_miss_tokens": float(usage.prompt_cache_miss_tokens),
        "reasoning_tokens": float(usage.reasoning_tokens),
    }
    if api_expense_usd is not None:
        components["api_expense"] = float(api_expense_usd)
    return components
