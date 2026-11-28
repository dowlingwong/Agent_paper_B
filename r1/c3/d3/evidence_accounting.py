"""D.3 §3.1 retry provenance and §8 proposer reservation time."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

RETRY_SCHEMA = "r1_d3_retry_ledger/v1"
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_SHA = re.compile(r"[0-9a-f]{64}")


class AccountingStop(ValueError):
    """The deployment accounting inputs are missing or inconsistent."""


def _matches(value: Any, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def check_retry_ledger(launch: Mapping[str, Any]) -> dict[str, Any]:
    """Check the launch's immutable snapshot of the operator's retry ledger.

    Prior entries refer to sealed infrastructure-loss receipts. The last entry names
    the fresh attempt being dispatched. Queue denials and reissued calls are excluded.
    """
    ledger = launch.get("retry_ledger")
    if not isinstance(ledger, dict) or set(ledger) != {"schema", "run_id", "chunk", "attempts"}:
        raise AccountingStop("a deployment launch needs an exact retry ledger")
    if ledger["schema"] != RETRY_SCHEMA or not _matches(ledger["run_id"], _ID):
        raise AccountingStop("invalid retry ledger schema or run_id")
    expected = {key: launch[key] for key in ("stage", "node", "arm", "repetition", "instance_seeds")}
    expected["manifest_sha256"] = launch["manifest"]["sha256"]
    chunk = ledger["chunk"]
    if (not isinstance(chunk, dict) or set(chunk) != {*expected, "gpu_model"}
            or any(chunk[key] != value for key, value in expected.items())
            or not _matches(chunk["manifest_sha256"], _SHA)
            or not isinstance(chunk["gpu_model"], str) or not chunk["gpu_model"].strip()):
        raise AccountingStop("retry ledger chunk identity differs from the launch")
    attempts = ledger["attempts"]
    if not isinstance(attempts, list) or not attempts:
        raise AccountingStop("retry ledger must contain the current attempt")
    ids, jobs, receipts = set(), set(), set()
    for entry in attempts:
        if not isinstance(entry, dict) or not _matches(entry.get("attempt_id"), _ID):
            raise AccountingStop("retry ledger has an invalid attempt ID")
        if entry["attempt_id"] in ids:
            raise AccountingStop("retry ledger repeats an attempt ID")
        ids.add(entry["attempt_id"])
    for entry in attempts[:-1]:
        if (set(entry) != {"attempt_id", "state", "job_id", "receipt_sha256", "gpu_model"}
                or entry["state"] != "infrastructure_lost"
                or entry["gpu_model"] != chunk["gpu_model"]
                or not _matches(entry["job_id"], _ID)
                or not _matches(entry["receipt_sha256"], _SHA)
                or entry["job_id"] in jobs or entry["receipt_sha256"] in receipts):
            raise AccountingStop("each prior attempt needs a distinct sealed infrastructure-loss receipt and job ID")
        jobs.add(entry["job_id"])
        receipts.add(entry["receipt_sha256"])
    current = attempts[-1]
    if set(current) != {"attempt_id", "state"} or current["state"] != "current":
        raise AccountingStop("retry ledger must end with exactly one current attempt")
    return ledger


@dataclass(frozen=True)
class CampaignAccounting:
    """Validated inputs common to every campaign in the retained chunk."""

    ledger: dict[str, Any]
    gpu_uuid: str
    lease_kind: str

    @classmethod
    def from_job(cls, launch: Mapping[str, Any], observed: Mapping[str, Any]) -> CampaignAccounting:
        ledger = check_retry_ledger(launch)
        lease_kind = "htcondor" if launch["launcher"] == "htcondor" else "lease"
        gpu_uuid = observed.get("gpu_uuid")
        if (observed.get("schema") != "r1_d3_observed/v1"
                or observed.get("lease") is not True or observed.get("lease_kind") != lease_kind
                or observed.get("lease_path") != launch.get("lease_path")
                or not isinstance(gpu_uuid, str) or not gpu_uuid.startswith("GPU-")
                or len(gpu_uuid) <= 4 or observed.get("model") != ledger["chunk"]["gpu_model"]):
            raise AccountingStop("retry ledger and live proposer reservation do not name the same GPU model")
        return cls(ledger, gpu_uuid, lease_kind)

    @property
    def infra_attempts(self) -> int:
        return len(self.ledger["attempts"])

    def receipt(self, started_ns: int, ended_ns: int) -> dict[str, Any]:
        elapsed_ns = ended_ns - started_ns
        if elapsed_ns <= 0:
            raise AccountingStop("proposer reservation needs a positive elapsed interval")
        return {
            "basis": "single_gpu_reservation_monotonic",
            "run_id": self.ledger["run_id"],
            "attempt_id": self.ledger["attempts"][-1]["attempt_id"],
            "infra_attempts": self.infra_attempts,
            "gpu_uuid": self.gpu_uuid,
            "lease_kind": self.lease_kind,
            "elapsed_ns": elapsed_ns,
        }
