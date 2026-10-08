"""Immutable, content-addressed retention of Pi session histories (C-2).

Author decision C-2 (2026-09-20): retain the full Pi session history ``H`` --
the parent checkpoint history and every executed branch history, failed
branches included -- compressed, outside Git, addressed by digest.

What is stored, per history:

* the raw JSONL bytes, zlib-compressed, at
  ``<store>/objects/<raw_sha256[:2]>/<raw_sha256>.jsonl.z``;
* a retention record (JSON) at ``<store>/records/<run>/<branch_id>.json`` with
  the checkpoint prefix boundary (``entry_id``), the RAW-byte digest (the
  digest the checkpoint layer already binds as ``history_bytes_digest`` --
  never replaced by the compressed-object digest), the compressed-object
  digest, the encoding/compression version, the durable location and the
  run/root/branch identity.

The two digests are kept distinct by name: ``raw_sha256`` verifies the
reconstructed history against the checkpoint bundle; ``compressed_sha256``
verifies the stored object on disk. Equating them would let a re-encoded
object pass as the original history.

Objects are write-once: an existing object with the same raw digest is
verified, not overwritten; an existing object whose bytes decompress to a
different digest is a corruption that raises. Records are written to a
temporary file and renamed into place so an interrupted write leaves either
the old record or the complete new one, never a torn one.

The store is meant to live on persistent storage named by the run
configuration (``history_store``); it is never ``/tmp`` by default -- the
default is ``<evidence_root>/history`` beside the ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import zlib
from pathlib import Path
from typing import Any

RETENTION_SCHEMA = "session_history_retention/v1"
ENCODING = "utf-8-jsonl"
COMPRESSION = "zlib-9"


class HistoryRetentionError(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-%d" % os.getpid())
    with tmp.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def object_path(store: Path, raw_sha256: str) -> Path:
    return Path(store) / "objects" / raw_sha256[:2] / f"{raw_sha256}.jsonl.z"


def record_path(store: Path, run_id: str, branch_id: str) -> Path:
    safe_run = run_id.replace("/", "_")
    safe_branch = branch_id.replace("/", "_")
    return Path(store) / "records" / safe_run / f"{safe_branch}.json"


def retain_session_history(
    *,
    store: Path,
    session_file: Path | None,
    run_id: str,
    root_id: str,
    branch_id: str,
    regime_id: str,
    role: str,
    entry_id: str | None,
    terminal: str | None,
) -> dict[str, Any]:
    """Retain one history; return its retention record.

    A missing session file (an arm that died before Pi wrote one) is retained
    as an ATTEMPTED-ARM record with ``retained: false`` and
    ``reason: session_file_absent`` -- the attempt is on record, and nothing
    is invented for it.
    """
    store = Path(store)
    record: dict[str, Any] = {
        "schema": RETENTION_SCHEMA,
        "run_id": run_id, "root_id": root_id, "branch_id": branch_id,
        "regime_id": regime_id, "role": role,
        "checkpoint_entry_id": entry_id, "terminal": terminal,
        "retained_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "encoding": ENCODING, "compression": COMPRESSION,
    }
    if session_file is None or not Path(session_file).is_file():
        record.update({"retained": False, "reason": "session_file_absent",
                       "session_file": str(session_file) if session_file else None})
        _atomic_write(record_path(store, run_id, branch_id),
                      json.dumps(record, sort_keys=True, indent=2).encode("utf-8"))
        return record
    raw = Path(session_file).read_bytes()
    raw_sha = _sha256(raw)
    compressed = zlib.compress(raw, 9)
    comp_sha = _sha256(compressed)
    target = object_path(store, raw_sha)
    if target.exists():
        existing = target.read_bytes()
        try:
            if _sha256(zlib.decompress(existing)) != raw_sha:
                raise HistoryRetentionError(
                    f"stored object {target} does not decompress to {raw_sha}")
        except zlib.error as exc:
            raise HistoryRetentionError(f"stored object {target} is corrupt: {exc}") from exc
        comp_sha = _sha256(existing)
        deduplicated = True
    else:
        _atomic_write(target, compressed)
        deduplicated = False
    record.update({
        "retained": True,
        "raw_sha256": raw_sha,
        "raw_bytes": len(raw),
        "compressed_sha256": comp_sha,
        "compressed_bytes": target.stat().st_size,
        "object_path": str(target),
        # Resolution key for a relocated store: verification resolves the
        # object as <selected store>/<object_relpath>, never through the
        # producer's absolute path.
        "object_relpath": str(target.relative_to(store)),
        "store": str(store),
        "deduplicated": deduplicated,
        "entry_count": sum(1 for line in raw.splitlines() if line.strip()),
        "session_file": str(session_file),
    })
    _atomic_write(record_path(store, run_id, branch_id),
                  json.dumps(record, sort_keys=True, indent=2).encode("utf-8"))
    return record


def reconstruct_history(store: Path, raw_sha256: str) -> bytes:
    """Return the raw JSONL bytes for a retained history, verifying the digest."""
    target = object_path(store, raw_sha256)
    if not target.is_file():
        raise HistoryRetentionError(f"no retained object for {raw_sha256} at {target}")
    raw = zlib.decompress(target.read_bytes())
    if _sha256(raw) != raw_sha256:
        raise HistoryRetentionError(f"retained object {target} does not verify against {raw_sha256}")
    return raw


def _entry_ids(raw: bytes) -> list[str]:
    """Session entry ids in order (header lines of type ``session`` excluded)."""
    ids: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            raise HistoryRetentionError("history is not JSONL") from None
        if isinstance(record, dict) and record.get("type") != "session" and "id" in record:
            ids.append(str(record["id"]))
    return ids


#: S5: the ONLY header fields a valid fork of the pinned Pi may change
#: (``SessionManager.forkFrom``, third_party/pi/packages/coding-agent/src/core/
#: session-manager.ts): a new session id, the fork time, the target cwd and the
#: ``parentSession`` pointer. Every other header field (``type``, ``version``)
#: must equal the parent's, and every non-header entry is copied verbatim
#: (``JSON.stringify(JSON.parse(line))``), so entries are compared as parsed
#: JSON objects -- serialization differences cannot matter, content can.
FORK_HEADER_METADATA = ("id", "timestamp", "cwd", "parentSession")


def _session_parts(raw: bytes) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """(header, entries) of a JSONL session; raises HistoryRetentionError if not JSONL objects."""
    header: dict[str, Any] | None = None
    entries: list[dict[str, Any]] = []
    for index, line in enumerate(raw.splitlines()):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            raise HistoryRetentionError("history is not JSONL") from None
        if not isinstance(record, dict):
            raise HistoryRetentionError("history line is not a JSON object")
        if record.get("type") == "session":
            if header is not None or entries:
                raise HistoryRetentionError("session header is not the single first line")
            header = record
        else:
            entries.append(record)
    return header, entries


def fork_prefix_problem(parent_raw: bytes, child_raw: bytes, boundary: str) -> str | None:
    """Why ``child_raw`` is not a valid Pi fork of ``parent_raw`` at ``boundary`` (None = valid).

    The child's leading entries must EQUAL the parent's entries through the
    checkpoint entry -- ids, types, parent links, timestamps, roles, message
    content and tool results -- and the child's first own entry must chain to
    the checkpoint (nothing the parent did after it is inherited). Only the
    header metadata in ``FORK_HEADER_METADATA`` may differ, and the child must
    name a parent session as Pi's fork does.
    """
    try:
        parent_header, parent_entries = _session_parts(parent_raw)
        child_header, child_entries = _session_parts(child_raw)
    except HistoryRetentionError:
        return "history_not_jsonl"
    if parent_header is None or child_header is None:
        return "session_header_missing"
    if not child_header.get("parentSession"):
        return "child_header_names_no_parent_session"
    for key in sorted(set(parent_header) | set(child_header)):
        if key not in FORK_HEADER_METADATA and parent_header.get(key) != child_header.get(key):
            return f"child_header_{key}_differs_from_parent"
    parent_ids = [str(e.get("id")) for e in parent_entries]
    if boundary not in parent_ids:
        return "checkpoint_entry_absent_from_parent"
    prefix = parent_entries[: parent_ids.index(boundary) + 1]
    if [str(e.get("id")) for e in child_entries[: len(prefix)]] != [str(e.get("id")) for e in prefix]:
        return "child_prefix_differs_from_checkpoint"
    for mine, theirs in zip(child_entries, prefix):
        if mine != theirs:
            changed = sorted(k for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k))
            return f"child_prefix_content_differs_at_{theirs.get('id')}:{','.join(changed)}"
    rest = child_entries[len(prefix):]
    if rest and str(rest[0].get("parentId")) != boundary:
        return "child_does_not_continue_from_the_checkpoint"
    inherited = set(parent_ids[len(prefix):]) & {str(e.get("id")) for e in rest}
    if inherited:
        return "child_inherits_post_checkpoint_entries"
    return None


def verify_retention_record(record: dict[str, Any], store: Path | None = None) -> list[str]:
    """Problems with one retention record against the store (empty = verified).

    With ``store`` given the object is resolved INSIDE that store from the
    record's raw digest (``objects/<sha[:2]>/<sha>.jsonl.z``); the producer's
    absolute ``object_path`` is ignored, so a store moved to durable storage
    on another host verifies, and a record cannot point verification at an
    object outside the selected store. Without ``store`` the legacy absolute
    path is used (development only).
    """
    problems: list[str] = []
    if not record.get("retained"):
        problems.append(f"not_retained:{record.get('reason') or record.get('error')}")
        return problems
    raw_sha = record.get("raw_sha256")
    if not isinstance(raw_sha, str) or len(raw_sha) != 64:
        return ["raw_digest_absent"]
    target = object_path(store, raw_sha) if store is not None else Path(record["object_path"])
    if not target.is_file():
        problems.append("object_missing")
        return problems
    data = target.read_bytes()
    if _sha256(data) != record.get("compressed_sha256"):
        problems.append("compressed_digest_mismatch")
    try:
        raw = zlib.decompress(data)
    except zlib.error:
        problems.append("object_corrupt")
        return problems
    if _sha256(raw) != raw_sha:
        problems.append("raw_digest_mismatch")
    if len(raw) != record.get("raw_bytes"):
        problems.append("raw_length_mismatch")
    return problems


def expected_histories(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The histories a run MUST have retained, derived from the ledger.

    * a parent history for every root whose checkpoint was taken (a
      ``restore_intent`` exists for it -- the checkpoint precedes the intent);
    * a sibling history for every arm that was started (``branch_started``)
      or reported exposed at its terminal (``branch_terminal`` with
      ``exposed: true``).

    Keys are the executor's branch ids (``<root>-parent``, ``<root>-<regime>``).
    """
    expected: dict[str, dict[str, Any]] = {}
    for event in events:
        kind = event.get("kind")
        identity = event.get("identity") or {}
        payload = event.get("payload") or {}
        root_id = identity.get("root_id")
        if root_id is None:
            continue
        if kind == "restore_intent":
            entry = expected.setdefault(f"{root_id}-parent", {
                "root_id": str(root_id), "regime_id": "g_0", "role": "parent"})
            entry["checkpoint_entry_id"] = payload.get("entry_id")
            entry["checkpoint_history_sha256"] = payload.get("checkpoint_history_sha256")
            entry["checkpoint_id"] = identity.get("checkpoint_id")
        elif kind == "branch_started" or (kind == "branch_terminal" and payload.get("exposed") is True):
            regime_id = identity.get("regime_id")
            if regime_id is None:
                continue
            expected.setdefault(f"{root_id}-{regime_id}", {
                "root_id": str(root_id), "regime_id": str(regime_id), "role": "sibling"})
    return expected


def verify_store_against_ledger(store: Path, events: list[dict[str, Any]], *,
                                run_id: str | None = None) -> dict[str, Any]:
    """Prove the run's required history coverage from the ledger and the store.

    Required coverage comes from :func:`expected_histories`, not from the
    retention events that happen to exist. For each required history:

    * exactly one ``history_retained`` event (a missing one is
      ``missing_retention_event``; several are ``duplicate_retention_events``);
    * the event identity, the record identity and the run agree;
    * the object resolves inside ``store`` and verifies (compressed and raw
      digests, length);
    * a parent history's raw digest equals the checkpoint's
      ``checkpoint_history_sha256`` recorded in its ``restore_intent`` and its
      prefix boundary equals the checkpoint entry; a sibling history carries
      the parent's entries through the checkpoint entry as its prefix.

    An attempted arm whose session could not be obtained is listed under
    ``unretained`` with its recorded reason: it is accounted for, and it keeps
    the run from being fully evidenced. Retention events for branches the
    ledger never required are ``unexpected``. Nothing here repairs anything.
    """
    store = Path(store)
    expected = expected_histories(events)
    by_branch: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("kind") == "history_retained":
            branch = str((event.get("identity") or {}).get("branch_id"))
            by_branch.setdefault(branch, []).append(event)
    ledger_run = run_id
    if ledger_run is None:
        for event in events:
            if event.get("kind") == "run_opened":
                ledger_run = (event.get("identity") or {}).get("run") or event.get("run_id")
                break

    verified: list[str] = []
    failed: dict[str, list[str]] = {}
    unretained: dict[str, str] = {}
    missing: list[str] = []
    raw_cache: dict[str, bytes] = {}

    def _raw(record: dict[str, Any]) -> bytes | None:
        sha = record.get("raw_sha256")
        if sha in raw_cache:
            return raw_cache[sha]
        try:
            raw_cache[sha] = reconstruct_history(store, sha)
        except (HistoryRetentionError, zlib.error, OSError):
            return None
        return raw_cache[sha]

    records: dict[str, dict[str, Any]] = {}
    for branch_id, requirement in sorted(expected.items()):
        found = by_branch.get(branch_id, [])
        if not found:
            missing.append(branch_id)
            continue
        if len(found) > 1:
            failed[branch_id] = ["duplicate_retention_events"]
            continue
        event = found[0]
        payload = event.get("payload") or {}
        problems: list[str] = []
        identity = event.get("identity") or {}
        if str(identity.get("root_id")) != requirement["root_id"]:
            problems.append("event_root_mismatch")
        for key in ("root_id", "branch_id"):
            if key in payload and str(payload.get(key)) != (requirement["root_id"] if key == "root_id" else branch_id):
                problems.append(f"record_{key}_mismatch")
        if "regime_id" in payload and str(payload.get("regime_id")) != requirement["regime_id"]:
            problems.append("record_regime_mismatch")
        if "role" in payload and str(payload.get("role")) != requirement["role"]:
            problems.append("record_role_mismatch")
        if ledger_run is not None and "run_id" in payload and str(payload.get("run_id")) != str(ledger_run):
            problems.append("record_run_mismatch")
        if not payload.get("retained"):
            if problems:
                failed[branch_id] = problems
            else:
                unretained[branch_id] = str(payload.get("reason") or payload.get("error") or "unknown")
            continue
        problems.extend(verify_retention_record(payload, store))
        if requirement["role"] == "parent" and not problems:
            bound = requirement.get("checkpoint_history_sha256")
            if not bound:
                problems.append("checkpoint_history_digest_unbound")
            elif bound != payload.get("raw_sha256"):
                problems.append("parent_history_differs_from_checkpoint")
            if requirement.get("checkpoint_entry_id") != payload.get("checkpoint_entry_id"):
                problems.append("prefix_boundary_mismatch")
        if problems:
            failed[branch_id] = problems
        else:
            records[branch_id] = payload
            verified.append(branch_id)

    # Sibling prefix: the parent's entries through the checkpoint entry are
    # the child's leading entries.
    for branch_id in list(verified):
        requirement = expected[branch_id]
        if requirement["role"] != "sibling":
            continue
        parent_id = f"{requirement['root_id']}-parent"
        parent_req = expected.get(parent_id) or {}
        boundary = parent_req.get("checkpoint_entry_id")
        parent_record = records.get(parent_id)
        child_raw = _raw(records[branch_id])
        problem = None
        if parent_record is None or not boundary:
            problem = "parent_history_unverified"
        elif child_raw is None:
            problem = "object_missing"
        else:
            # S5: entry CONTENT and lineage, not only ids.
            problem = fork_prefix_problem(_raw(parent_record) or b"", child_raw, boundary)
        if problem:
            verified.remove(branch_id)
            failed[branch_id] = [problem]

    unexpected = sorted(set(by_branch) - set(expected))
    return {
        "required": len(expected),
        "records": sum(len(v) for v in by_branch.values()),
        "verified": len(verified),
        "verified_branches": sorted(verified),
        "missing": sorted(missing),
        "failed": failed,
        "unretained": unretained,
        "unexpected": unexpected,
        "store": str(store),
        "fully_evidenced": bool(expected) and len(verified) == len(expected)
                           and not missing and not failed and not unretained and not unexpected,
    }
