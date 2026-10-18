"""Lifecycle for a fleet of long-running child processes.

Written after an interrupted soak left four llama.cpp servers alive holding all
of the VRAM on all four GPUs. Two separate defects caused that:

1. The runner's cleanup lived in a `finally` block. `SIGINT` raises
   `KeyboardInterrupt` so `finally` runs, but the default `SIGTERM` disposition
   terminates the interpreter outright and `finally` never executes. An operator
   stopping a run the ordinary way got no cleanup at all.
2. Children are spawned with `start_new_session=True`, which puts each in its
   own process group. `Popen.terminate()` signals only the direct child, so any
   grandchild survives.

This module fixes both: signals are trapped and turned into an orderly shutdown,
and the whole process *group* is signalled rather than the leader alone.

It is deliberately substrate-agnostic and knows nothing about models, GPUs or the
soak. It manages processes.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

# Signals that must produce an orderly shutdown rather than an abrupt exit.
TRAPPED_SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)

DEFAULT_GRACE_SECONDS = 20.0


@dataclass
class ManagedProcess:
    name: str
    process: subprocess.Popen
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def pid(self) -> int:
        return self.process.pid

    def alive(self) -> bool:
        return self.process.poll() is None


def _signal_group(process: subprocess.Popen, sig: int) -> None:
    """Signal a child's whole process group, falling back to the child alone.

    The fallback matters: if the child was *not* started with
    `start_new_session=True` it shares our group, and signalling that group would
    also signal us.
    """
    try:
        os.killpg(os.getpgid(process.pid), sig)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.send_signal(sig)
        except (ProcessLookupError, OSError):
            pass


class ProcessFleet:
    """Owns child processes and guarantees they die when the runner does."""

    def __init__(self, *, record_path: Path | None = None,
                 grace_seconds: float = DEFAULT_GRACE_SECONDS) -> None:
        self.members: list[ManagedProcess] = []
        self.record_path = record_path
        self.grace_seconds = grace_seconds
        self._previous_handlers: dict[int, Any] = {}
        self._shutdown_done = False
        self.interrupted_by: str | None = None

    # -- registration --------------------------------------------------------

    def adopt(self, name: str, process: subprocess.Popen,
              **detail: Any) -> ManagedProcess:
        member = ManagedProcess(name=name, process=process, detail=detail)
        self.members.append(member)
        return member

    def spawn(self, name: str, argv: Sequence[str], *, stdout: Any = None,
              **detail: Any) -> ManagedProcess:
        """Start a child in its OWN session so its group can be signalled."""
        process = subprocess.Popen(
            list(argv), stdout=stdout,
            stderr=subprocess.STDOUT if stdout is not None else None,
            start_new_session=True)
        return self.adopt(name, process, argv=list(argv), **detail)

    # -- signal trapping -----------------------------------------------------

    def install_signal_handlers(self) -> None:
        for sig in TRAPPED_SIGNALS:
            try:
                self._previous_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, self._handle_signal)
            except (ValueError, OSError):
                # Not on the main thread, or the platform disallows it. The
                # `finally` path still covers normal exit.
                continue

    def restore_signal_handlers(self) -> None:
        for sig, handler in self._previous_handlers.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                continue
        self._previous_handlers.clear()

    def _handle_signal(self, signum: int, _frame: Any) -> None:
        name = signal.Signals(signum).name
        self.interrupted_by = name
        survivors = self.shutdown(reason=f"received {name}")
        # Exit non-zero: an interrupted run is not a successful one, and must
        # never be mistaken for a completed qualification.
        raise SystemExit(130 if not survivors else 1)

    # -- shutdown ------------------------------------------------------------

    def shutdown(self, *, reason: str) -> list[ManagedProcess]:
        """Terminate every member's process group. Idempotent.

        Returns the members still alive afterwards, which must be empty. The
        caller fails closed on a non-empty list rather than reporting success.
        """
        if self._shutdown_done:
            return [m for m in self.members if m.alive()]
        self._shutdown_done = True

        for member in self.members:
            if member.alive():
                _signal_group(member.process, signal.SIGTERM)

        deadline = time.monotonic() + self.grace_seconds
        while time.monotonic() < deadline:
            if all(not m.alive() for m in self.members):
                break
            time.sleep(0.1)

        for member in self.members:
            if member.alive():
                _signal_group(member.process, signal.SIGKILL)

        hard_deadline = time.monotonic() + 10.0
        while time.monotonic() < hard_deadline:
            if all(not m.alive() for m in self.members):
                break
            time.sleep(0.1)

        for member in self.members:
            try:
                member.process.wait(timeout=1)
            except (subprocess.TimeoutExpired, OSError):
                pass

        survivors = [m for m in self.members if m.alive()]
        self.write_record(reason=reason, survivors=survivors)
        return survivors

    def write_record(self, *, reason: str,
                     survivors: Sequence[ManagedProcess]) -> dict[str, Any]:
        record = {
            "schema_version": "0.1",
            "artifact_kind": "process_fleet_interruption_record",
            "qualifying": False,
            "scientific_evidence": "none",
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "interrupted_by_signal": self.interrupted_by,
            "members": [
                {"name": m.name, "pid": m.pid,
                 "exit_code": m.process.poll(), "alive_after_shutdown": m.alive(),
                 **m.detail}
                for m in self.members
            ],
            "survivors": [m.pid for m in survivors],
            "all_children_terminated": not survivors,
            # An interrupted run never produces a qualifying artifact. Saying so
            # here keeps a partial run from being read as a completed one.
            "produced_qualifying_artifact": False,
        }
        if self.record_path is not None:
            self.record_path.parent.mkdir(parents=True, exist_ok=True)
            self.record_path.write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return record

    # -- context manager -----------------------------------------------------

    def __enter__(self) -> "ProcessFleet":
        self.install_signal_handlers()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        reason = "normal exit" if exc_type is None else f"exception: {exc_type.__name__}"
        survivors = self.shutdown(reason=reason)
        self.restore_signal_handlers()
        if survivors:
            names = ", ".join(f"{m.name}:{m.pid}" for m in survivors)
            raise RuntimeError(f"child processes survived shutdown: {names}")
        return False


def run_with_fleet(fleet: ProcessFleet, argv: Sequence[str], *,
                   cwd: Path | None = None,
                   on_start: Callable[[subprocess.Popen], None] | None = None) -> int:
    """Run a foreground child under the fleet so a signal reaches it too.

    `subprocess.run` would leave the child running when the parent is signalled,
    because the parent dies without waiting. Adopting it into the fleet makes it
    part of the same orderly shutdown as the servers.
    """
    process = subprocess.Popen(list(argv), cwd=str(cwd) if cwd else None,
                               start_new_session=True)
    fleet.adopt("workload", process, argv=list(argv))
    if on_start is not None:
        on_start(process)
    return process.wait()
