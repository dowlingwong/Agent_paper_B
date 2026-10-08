"""Explicit Pi checkpoint forking (DeepSeek handoff Work Package 1).

An E0 sibling is not "a copy of the parent JSONL dropped into a session
directory". `--session-dir` selects *storage*; it does not prove Pi opened the
copied checkpoint, and the first candidate run demonstrated the failure mode
directly by finding two session JSONLs where one was expected.

Pi has an explicit fork: `--fork <parent-session-path> --session-id <child-id>`
calls `SessionManager.forkFrom`, which writes a *new* session file with a new
header whose `parentSession` names the source, followed by every non-header
entry of the source. This module owns the Python half of that contract:

- locate and validate the single session JSONL Pi wrote for a branch;
- restore the parent to the exact registered checkpoint entry before forking, so
  no post-checkpoint parent entry can be inherited;
- derive a frozen, unique, Pi-valid child session ID from registered lineage
  (never a random one, so a resumed or re-run root forks to the same ID);
- verify after startup that the child's inherited prefix is canonically exact
  through the registered entry and contains no post-checkpoint parent entries.

Every check fails closed. Nothing here makes a model call.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

# Pi's own session-id rule (`assertValidSessionId` in session-manager.ts).
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")

# Pi writes the session header as a `type: "session"` record; every other record
# is a tree entry carrying `id` and `parentId`.
HEADER_TYPE = "session"


class ForkError(RuntimeError):
    """An explicit fork could not be proven correct. Never downgraded."""


@dataclass(frozen=True)
class SessionDocument:
    """A parsed Pi session JSONL: one header plus ordered entries."""

    path: Path
    header: dict[str, Any]
    entries: tuple[dict[str, Any], ...]

    @property
    def session_id(self) -> str:
        return str(self.header.get("id", ""))

    @property
    def parent_session(self) -> str | None:
        value = self.header.get("parentSession")
        return str(value) if isinstance(value, str) and value else None

    @property
    def entry_ids(self) -> tuple[str, ...]:
        return tuple(str(entry["id"]) for entry in self.entries)

    @property
    def leaf_entry_id(self) -> str | None:
        return self.entry_ids[-1] if self.entries else None

    def index_of(self, entry_id: str) -> int:
        try:
            return self.entry_ids.index(entry_id)
        except ValueError as exc:
            raise ForkError(f"entry {entry_id!r} is not present in {self.path}") from exc

    def prefix_digest(self, through_entry_id: str) -> str:
        """Canonical digest of the entry prefix through `through_entry_id`.

        Canonical rather than byte-exact: `forkFrom` re-serializes each entry
        with `JSON.stringify`, so key order and whitespace are not preserved
        across the fork even though the entry *content* is. Sorting keys makes
        the comparison exact on content and blind to serialization.
        """
        return _canonical_digest(self.entries[: self.index_of(through_entry_id) + 1])

    def full_digest(self) -> str:
        return _canonical_digest(self.entries)


def _canonical_digest(entries: Sequence[dict[str, Any]]) -> str:
    payload = json.dumps(list(entries), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_session(path: Path) -> SessionDocument:
    """Parse and validate one Pi session JSONL. Malformed input fails closed."""
    if not path.is_file():
        raise ForkError(f"session file missing: {path}")
    header: dict[str, Any] | None = None
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ForkError(f"malformed session record at {path}:{line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise ForkError(f"non-object session record at {path}:{line_number}")
        if record.get("type") == HEADER_TYPE:
            if header is not None:
                raise ForkError(f"more than one session header in {path}")
            if entries:
                raise ForkError(f"session header is not the first record in {path}")
            header = record
            continue
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ForkError(f"session entry at {path}:{line_number} lacks a string id")
        if record_id in seen:
            raise ForkError(f"duplicate session entry id {record_id!r} in {path}")
        seen.add(record_id)
        entries.append(record)
    if header is None:
        raise ForkError(f"session has no header: {path}")
    return SessionDocument(path=path, header=header, entries=tuple(entries))


def sole_session_file(session_dir: Path) -> Path:
    """The one session JSONL in `session_dir`.

    Zero or more than one is a fault: a second JSONL is exactly the "Pi silently
    started a new session instead of opening the one we gave it" failure the
    fork contract exists to rule out.
    """
    candidates = sorted(p for p in session_dir.glob("*.jsonl") if p.is_file())
    if not candidates:
        raise ForkError(f"no session JSONL in {session_dir}")
    if len(candidates) > 1:
        raise ForkError(
            f"ambiguous session directory {session_dir}: expected one JSONL, found "
            + ", ".join(p.name for p in candidates)
        )
    return candidates[0]


def session_file_count(session_dir: Path) -> int:
    return len([p for p in session_dir.glob("*.jsonl") if p.is_file()]) if session_dir.is_dir() else 0


def derive_child_session_id(
    *, run_id: str, root_id: str, checkpoint_id: str, regime_id: str, repetition: int = 0
) -> str:
    """A frozen, unique, Pi-valid child session ID for one sibling branch.

    Derived from registered lineage only, so the same branch always forks to the
    same child ID: a resumed client re-forks identically instead of inventing a
    new identity. Contains no free text from the task and no secrets.
    """
    lineage = "|".join((run_id, root_id, checkpoint_id, regime_id, str(repetition)))
    digest = hashlib.sha256(lineage.encode("utf-8")).hexdigest()[:16]
    session_id = f"cbf-{digest}"
    if not SESSION_ID_PATTERN.match(session_id):  # pragma: no cover - construction is safe
        raise ForkError(f"derived child session id is not Pi-valid: {session_id!r}")
    return session_id


def validate_session_id(session_id: str) -> str:
    if not SESSION_ID_PATTERN.match(session_id):
        raise ForkError(
            f"session id {session_id!r} is not Pi-valid: alphanumeric, '-', '_', '.', "
            "starting and ending alphanumeric"
        )
    return session_id


@dataclass(frozen=True)
class ParentCheckpoint:
    """The frozen parent state a sibling forks from."""

    session_path: Path
    checkpoint_id: str
    entry_id: str
    session_sha256: str
    prefix_sha256: str
    leaf_entry_id: str
    entry_count: int
    truncated_entries: int

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["session_path"] = str(self.session_path)
        return record


def restore_parent_to_checkpoint(
    session_file: Path, *, checkpoint_id: str, entry_id: str
) -> ParentCheckpoint:
    """Truncate the parent session to the exact registered checkpoint entry.

    Pi's `forkFrom` copies *every* non-header entry of the source, so anything
    appended to the parent after the checkpoint would be inherited by all three
    siblings. Restoring first is what makes `--fork` an exact-prefix operation
    rather than a whole-session copy. Rewriting is atomic (temp file + replace)
    so an interrupted restore cannot leave a half-written parent.
    """
    document = read_session(session_file)
    index = document.index_of(entry_id)
    kept = document.entries[: index + 1]
    dropped = len(document.entries) - len(kept)

    if dropped:
        lines = [json.dumps(document.header, separators=(",", ":"), ensure_ascii=False)]
        lines.extend(json.dumps(entry, separators=(",", ":"), ensure_ascii=False) for entry in kept)
        temp = session_file.with_suffix(session_file.suffix + ".restore")
        temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temp.replace(session_file)
        document = read_session(session_file)
        if document.entry_ids != tuple(str(entry["id"]) for entry in kept):
            raise ForkError(f"parent restore did not produce the registered prefix: {session_file}")

    return ParentCheckpoint(
        session_path=session_file,
        checkpoint_id=checkpoint_id,
        entry_id=entry_id,
        session_sha256=file_digest(session_file),
        prefix_sha256=document.prefix_digest(entry_id),
        leaf_entry_id=entry_id,
        entry_count=len(document.entries),
        truncated_entries=dropped,
    )


@dataclass(frozen=True)
class ForkRecord:
    """The auditable one-to-one record of one sibling fork.

    Written into the branch record so a reviewer can re-derive, from evidence
    alone, that this child inherited exactly the registered parent prefix.
    """

    parent_checkpoint_id: str
    parent_entry_id: str
    parent_session_path: str
    parent_session_sha256: str
    parent_prefix_sha256: str
    child_session_id: str
    child_session_path: str
    child_session_sha256: str
    child_leaf_entry_id: str | None
    inherited_prefix_sha256: str
    inherited_entry_count: int
    post_checkpoint_entries_inherited: int
    child_entries_after_checkpoint: int
    fork_argv_sha256: str
    exact_prefix: bool
    verified: bool
    errors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["errors"] = list(self.errors)
        return record


def fork_argv_digest(argv: Sequence[str]) -> str:
    return hashlib.sha256(
        json.dumps(list(argv), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def verify_fork(
    *,
    parent: ParentCheckpoint,
    child_session_file: Path,
    expected_child_session_id: str,
    fork_argv: Sequence[str],
    post_checkpoint_parent_entry_ids: Sequence[str] = (),
) -> ForkRecord:
    """Prove the child is an exact fork of the parent checkpoint.

    Checks, in order: the child is a distinct file; its header names the parent
    session; its ID is the frozen one we asked for; its first `n` entries are
    canonically identical to the parent prefix through the registered entry; and
    no entry the parent produced *after* the checkpoint appears in the child.
    """
    errors: list[str] = []
    child = read_session(child_session_file)
    parent_document = read_session(parent.session_path)
    parent_prefix = parent_document.entries[: parent_document.index_of(parent.entry_id) + 1]
    inherited = child.entries[: len(parent_prefix)]

    if child_session_file.resolve() == parent.session_path.resolve():
        errors.append("child session file is the parent session file (no fork happened)")
    if child.session_id != expected_child_session_id:
        errors.append(
            f"child session id {child.session_id!r} is not the frozen "
            f"{expected_child_session_id!r}"
        )
    if child.parent_session is None:
        errors.append("child session header has no parentSession (not produced by --fork)")
    elif Path(child.parent_session).name != parent.session_path.name:
        errors.append(
            f"child parentSession {child.parent_session!r} does not name the parent checkpoint "
            f"{parent.session_path.name!r}"
        )
    if len(child.entries) < len(parent_prefix):
        errors.append(
            f"child inherited {len(child.entries)} entries, fewer than the registered prefix "
            f"of {len(parent_prefix)}"
        )

    inherited_digest = _canonical_digest(inherited)
    exact_prefix = len(inherited) == len(parent_prefix) and inherited_digest == parent.prefix_sha256
    if not exact_prefix:
        errors.append("child prefix is not canonically identical to the parent checkpoint prefix")

    leaked = [
        entry_id
        for entry_id in post_checkpoint_parent_entry_ids
        if entry_id in set(child.entry_ids)
    ]
    if leaked:
        errors.append("child inherited post-checkpoint parent entries: " + ", ".join(sorted(leaked)))

    return ForkRecord(
        parent_checkpoint_id=parent.checkpoint_id,
        parent_entry_id=parent.entry_id,
        parent_session_path=str(parent.session_path),
        parent_session_sha256=parent.session_sha256,
        parent_prefix_sha256=parent.prefix_sha256,
        child_session_id=child.session_id,
        child_session_path=str(child_session_file),
        child_session_sha256=file_digest(child_session_file),
        child_leaf_entry_id=child.leaf_entry_id,
        inherited_prefix_sha256=inherited_digest,
        inherited_entry_count=len(inherited),
        post_checkpoint_entries_inherited=len(leaked),
        child_entries_after_checkpoint=max(0, len(child.entries) - len(parent_prefix)),
        fork_argv_sha256=fork_argv_digest(fork_argv),
        exact_prefix=exact_prefix,
        verified=not errors,
        errors=tuple(errors),
    )
