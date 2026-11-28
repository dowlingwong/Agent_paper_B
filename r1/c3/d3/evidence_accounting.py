"""D.3 §3.1 retry provenance and §8 proposer reservation time."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

RETRY_SCHEMA = "r1_d3_retry_ledger/v1"
LOSS_SCHEMA = "r1_d3_infrastructure_loss/v1"
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_SHA = re.compile(r"[0-9a-f]{64}")


class AccountingStop(ValueError):
    """The deployment accounting inputs are missing or inconsistent."""


def _matches(value: Any, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def stage_retry_receipts(launch: dict[str, Any], *, source_dir: Path) -> None:
    """Embed the exact UTF-8 receipt bytes so the job can recheck them without shared storage."""
    ledger = launch.get("retry_ledger")
    attempts = ledger.get("attempts") if isinstance(ledger, dict) else None
    if not isinstance(attempts, list) or not attempts:
        return  # The structured validator reports the missing or invalid ledger.
    from r1.c3.analysis_guard import refuse_sealed

    staged = []
    for entry in attempts[:-1]:
        if isinstance(entry, dict) and "receipt_path" in entry:
            source = entry["receipt_path"]
            if (set(entry) != {"attempt_id", "state", "job_id", "receipt_sha256", "receipt_path"}
                    or entry["state"] != "infrastructure_lost" or not _matches(entry["receipt_sha256"], _SHA)
                    or not isinstance(source, str) or not source):
                raise AccountingStop("each prior loss receipt must name one source file and its SHA-256")
            path = source_dir / source
            refuse_sealed(path)
            try:
                receipt = path.read_bytes().decode("utf-8")
            except (OSError, UnicodeError) as exc:
                raise AccountingStop(f"cannot stage the loss receipt for {entry.get('attempt_id')!r}") from exc
            entry = {key: value for key, value in entry.items() if key != "receipt_path"}
            entry["receipt"] = receipt
        staged.append(entry)
    launch["retry_ledger"] = {**ledger, "attempts": [*staged, attempts[-1]]}


def _check_loss_receipt(entry: dict[str, Any], ledger: dict[str, Any]) -> None:
    text = entry["receipt"]
    if not isinstance(text, str):
        raise AccountingStop("prior attempt loss receipt must contain UTF-8 text")
    try:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    except UnicodeError as exc:
        raise AccountingStop("prior attempt loss receipt must contain UTF-8 text") from exc
    if digest != entry["receipt_sha256"]:
        raise AccountingStop("prior attempt loss receipt SHA-256 differs")
    try:
        receipt = json.loads(text)
    except ValueError as exc:
        raise AccountingStop("prior attempt loss receipt is not JSON") from exc
    identity = {key: entry[key] for key in ("attempt_id", "job_id", "state")}
    identity.update(schema=LOSS_SCHEMA, run_id=ledger["run_id"], chunk=ledger["chunk"])
    if (not isinstance(receipt, dict) or set(receipt) != {*identity, "job_record_sha256"}
            or any(receipt[key] != value for key, value in identity.items())
            or not _matches(receipt["job_record_sha256"], _SHA)):
        raise AccountingStop("prior attempt loss receipt identity differs from the retry ledger")


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
        if (set(entry) != {"attempt_id", "state", "job_id", "receipt_sha256", "receipt"}
                or entry["state"] != "infrastructure_lost"
                or not _matches(entry["job_id"], _ID)
                or not _matches(entry["receipt_sha256"], _SHA)
                or entry["job_id"] in jobs or entry["receipt_sha256"] in receipts):
            raise AccountingStop("each prior attempt needs a distinct sealed infrastructure-loss receipt and job ID")
        _check_loss_receipt(entry, ledger)
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
        if launch["launcher"] == "ssh":
            expected_uuid = (launch.get("hardware") or {}).get("proposer_gpu_uuid")
            if expected_uuid != gpu_uuid:
                raise AccountingStop("the live SSH reservation differs from the bound proposer GPU UUID")
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
