"""G1 charged-run snapshots — the D.3 ``snapshots/w{5,10,15,20}.json`` contract.

ENGINEERING code; no campaign, audit, label or evaluation is run here.

Design authority: ``docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md``
(revision 5b) §2.2 and the coordinator's decision in ``tasks/compute/20261127-04``
(option 1).  The pinned harness exposes a snapshot hook at E0, E1 and E2 only; it does not
expose a per-charged-run callback.  G1 therefore wraps the ``Worker`` passed to
``run_real_campaign`` and counts every ``run_trial`` / ``run_trial_at_seed`` call.  Each
call is exactly one charged worker run (the harness itself calls
``ComputeBudget.consume_worker_run`` immediately after the same call), so the wrapper's
counter must equal ``ComputeBudget.worker_runs`` at every harness hook and at the end of the
campaign.  Any difference is a STOP (``SnapshotParityStop``): this is the replacement for
the missing per-run harness callback and is what forbids a block charge.

The controller state written with a snapshot is the state captured at the last E1 hook,
before the E1 decision (the design's rule).  The harness calls the controller exactly once
between that hook and the main run (E1), and once more before a verify block (E2); the
snapshot records the E1 state and the action in flight, so a replay uses the same input.

Limits recorded honestly in the snapshot payload:

* ``llm_calls`` is the last observed ``ComputeBudget`` value at the hook/charge.  A
  controller that issues its own calls must consume the harness budget; the wrapper does
  not add a second copy.  A manager call made after the E1 hook (a revision) is not visible
  to the wrapper; ``llm_calls_basis`` names the source.  No G1 decision depends on it.
* The exact-``w`` snapshot is written immediately after the run that reaches ``w``.  At
  W only, after the final decision, the pre-decision record is preserved as
  ``w<W>_pre.json`` and ``w<W>.json`` is rewritten from the post-decision final (the final
  governs; R1-D3-OUTCOMES2 §7.5(a)).  No other ``w`` point is imputed or mutated.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from r1.harness import import_harness

import_harness()

from autoresearch.control_plane.budget import ComputeBudget  # noqa: E402
from autoresearch.control_plane.campaign import SnapshotContext  # noqa: E402

SNAPSHOT_SCHEMA = "r1_d3_snapshot/v1"
SNAPSHOT_WS: tuple[int, ...] = (5, 10, 15, 20)
ENDED_ON = ("worker_runs", "llm_call_cap", "no_fundable_candidate", "stop", "error")


class SnapshotStop(RuntimeError):
    """A pre-declared STOP: the G1 record is not the run that was authorised."""


class SnapshotParityStop(SnapshotStop):
    """The wrapper's charged-run count differs from ``ComputeBudget.worker_runs``."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str,
                      allow_nan=False).encode("utf-8")


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _jsonable(value: Any) -> Any:
    """A deterministic JSON projection of controller/forecast state.

    Unknown objects are refused: their ``repr`` may contain an object address, which would
    make the projection non-deterministic.  A controller with mutable state exposed through a
    non-JSON attribute must provide ``snapshot_state()`` (see
    :func:`controller_state_sha256`); a silent ``repr`` fallback is not a replay record.
    """
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else {"nonfinite": repr(value)}
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_jsonable(v) for v in value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _jsonable(value.to_dict())
        except Exception as exc:  # noqa: BLE001 - projection only
            raise SnapshotStop(f"controller state has a to_dict() that cannot be projected: {exc}") from exc
    raise SnapshotStop(f"controller state value {type(value).__name__} is not JSON-projectable; "
                       "provide snapshot_state() or a JSON-able field")


def _plan_state(plan: Any) -> Any:
    fields = ("key", "features_hash", "kind", "pi", "mu", "tau", "sigma")
    out = {k: _jsonable(getattr(plan, k, None)) for k in fields}
    forecast = getattr(plan, "forecast", None)
    if forecast is not None:
        out["forecast"] = {
            "version": _jsonable(getattr(forecast, "version", None)),
            "digest": _jsonable(getattr(forecast, "digest", None)),
            "probs": _jsonable(getattr(forecast, "probs", None)),
            "llm_calls": _jsonable(getattr(forecast, "llm_calls", None)),
            "fallback": _jsonable(getattr(forecast, "fallback", None)),
        }
    return out


def controller_state(controller: Any) -> dict[str, Any]:
    """The documented projection hashed into ``controller_state_sha256``.

    A controller may expose ``snapshot_state()``; it is used verbatim.  Otherwise the
    projection covers the public ``version`` plus the C3 ``RuleController`` state
    (``_plans``, ``_pending``, ``revisions_requested``, ``log``).  A stateless controller
    (e.g. the harness ``ContinueController``) hashes to its class name and version.
    """
    if type(controller).__name__ == "RecordingController" and getattr(controller, "_inner", None) is not None:
        controller = controller._inner
    hook = getattr(controller, "snapshot_state", None)
    if callable(hook):
        return {"state": _jsonable(hook())}
    out: dict[str, Any] = {
        "class": type(controller).__name__,
        "version": _jsonable(getattr(controller, "version", None)),
    }
    if hasattr(controller, "revisions_requested"):
        out["revisions_requested"] = _jsonable(controller.revisions_requested)
    if hasattr(controller, "_pending"):
        out["pending"] = _jsonable(controller._pending)
    plans = getattr(controller, "_plans", None)
    if isinstance(plans, Mapping):
        out["plans"] = {str(k): _plan_state(v) for k, v in sorted(plans.items(), key=lambda kv: str(kv[0]))}
    log = getattr(controller, "log", None)
    if isinstance(log, list):
        out["log"] = _jsonable(log)
    return out


def controller_state_sha256(controller: Any) -> str:
    return sha256_json(controller_state(controller))


def _files_config(contents: Mapping[str, bytes | str | None]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for rel, data in sorted(contents.items()):
        if data is None:
            out[rel] = None
        elif isinstance(data, str):
            # The replicate-arm API passes config *contents* as text, exactly as the
            # snapshot payload stores them (bytes are still accepted from the harness).
            out[rel] = data
        else:
            try:
                out[rel] = data.decode("utf-8")
            except UnicodeDecodeError:
                out[rel] = {"binary": True, "bytes": len(data), "sha256": _sha256_bytes(data)}
    return out


def config_sha256(config: Mapping[str, Any]) -> str:
    digests = {}
    for rel, value in sorted(config.items()):
        if isinstance(value, str):
            digests[rel] = _sha256_bytes(value.encode("utf-8"))
        elif value is None:
            digests[rel] = None
        elif isinstance(value, Mapping) and "sha256" in value:
            digests[rel] = value["sha256"]
        else:
            digests[rel] = sha256_json(value)
    return sha256_json(digests)


def _decision_text(value: Any) -> str:
    """Normalise a harness ``TrialDecision`` (or a string) to the ledger's decision text."""
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def _worker_root(worker: Any) -> Path | None:
    for attr in ("node_root", "_node_root"):
        value = getattr(worker, attr, None)
        if value:
            return Path(value)
    return None


def read_worker_config(worker: Any, node_spec: Any) -> dict[str, Any]:
    root = _worker_root(worker)
    if root is None:
        return {}
    contents: dict[str, bytes | None] = {}
    for rel in node_spec.editable_paths:
        path = root / rel
        contents[rel] = path.read_bytes() if path.is_file() else None
    return _files_config(contents)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    data = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False, default=str) + "\n"
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return _sha256_bytes(data.encode("utf-8"))


def _last_kept_trial_index(ledger_prefix: list[Any]) -> int | None:
    last = None
    for record in ledger_prefix:
        decision = getattr(getattr(record, "decision", None), "value", getattr(record, "decision", None))
        if str(decision).lower() in ("keep", "kept"):
            last = getattr(record, "budget_index", None)
    return last


def _decision_value(record: Mapping[str, Any]) -> str:
    decision = record.get("decision")
    if isinstance(decision, Mapping):
        decision = decision.get("value", decision)
    return str(decision).lower()


def _last_kept_from_rows(rows: list[Mapping[str, Any]]) -> int | None:
    last = None
    for row in rows:
        if _decision_value(row) in ("keep", "kept") and row.get("budget_index") is not None:
            last = int(row["budget_index"])
    return last


@dataclass(frozen=True)
class ParityBudget(ComputeBudget):
    """A ``ComputeBudget`` that reports every charge to the G1 recorder.

    The harness reassigns its local ``compute_budget`` on every charge, so a plain object
    reference would go stale.  This subclass carries the recorder through every reassignment
    and checks the charged-run parity at the exact moment of the charge (before the next
    harness hook), which is stronger than checking only at E0/E1/E2.  The LLM-call counter
    is also observed, so a snapshot written after a proposal or revision carries the exact
    ``llm_calls`` value at that run.
    """

    recorder: Any = field(default=None, compare=False, repr=False)

    def _new(self, **changes: Any) -> "ParityBudget":
        data: dict[str, Any] = {
            "max_worker_runs": self.max_worker_runs,
            "max_worker_seconds": self.max_worker_seconds,
            "max_llm_calls": self.max_llm_calls,
            "worker_runs": self.worker_runs,
            "worker_seconds": self.worker_seconds,
            "llm_calls": self.llm_calls,
            "recorder": self.recorder,
        }
        data.update(changes)
        return ParityBudget(**data)

    def consume_worker_run(self, seconds: float = 0.0) -> "ParityBudget":
        new = self._new(worker_runs=self.worker_runs + 1,
                        worker_seconds=self.worker_seconds + max(float(seconds), 0.0))
        if self.recorder is not None:
            self.recorder.observe_budget(new, where="consume_worker_run")
        return new

    def consume_llm_call(self, count: int = 1) -> "ParityBudget":
        new = self._new(llm_calls=self.llm_calls + int(count))
        if self.recorder is not None:
            self.recorder.observe_budget(new, where="consume_llm_call")
        return new


@dataclass
class _TrialState:
    trial_id: str
    incumbent_config: dict[str, Any]
    config_sha256: str
    controller_state_sha256: str
    last_kept_trial_index: int | None
    llm_calls: int | None
    controller_calls_at_e1: int = 0
    pending_action: str | None = None
    step_index: int | None = None


@dataclass
class SnapshotRecorder:
    """The G1 snapshot hook plus the recording half of the counting worker.

    ``out_dir`` is the campaign directory; snapshots go to ``<out_dir>/snapshots``.
    ``stage``, ``arm``, ``node``, ``repetition`` and ``instance_id`` are copied into every
    snapshot.
    """

    out_dir: Path
    stage: str
    arm: str
    node: str
    repetition: int
    instance_id: str
    count: int = 0
    start_config: dict[str, Any] | None = None
    _trial: _TrialState | None = None
    _last_budget: Any | None = None
    _controller_calls: int = 0
    _controller_state_at_hook: str = ""
    _written: dict[int, str] = field(default_factory=dict)
    _pre_written: dict[int, str] = field(default_factory=dict)
    _final_written: bool = False
    _pending: dict[str, Any] | None = None
    _post_decision_state: str | None = None
    _trial_configs: list[dict[str, Any]] = field(default_factory=list)

    # ---- harness hook -----------------------------------------------------
    def __call__(self, ctx: SnapshotContext) -> None:
        self.observe_budget(ctx.compute_budget, where=f"hook {ctx.epoch}")
        if ctx.epoch == "E0":
            if self.start_config is None:
                self.start_config = read_worker_config(ctx.worker, ctx.node_spec)
            self._controller_state_at_hook = controller_state_sha256(ctx.controller)
            return
        if ctx.epoch == "E1":
            incumbent = (_files_config(ctx.incumbent_snapshot.contents)
                         if ctx.incumbent_snapshot is not None else {})
            # E1 state is authoritative for every snapshot of this trial, including the
            # verify runs that happen after the E2 hook (coordinator condition 3).
            self._controller_state_at_hook = controller_state_sha256(ctx.controller)
            self._trial = _TrialState(
                trial_id=str(ctx.trial_id),
                incumbent_config=incumbent,
                config_sha256=config_sha256(incumbent),
                controller_state_sha256=controller_state_sha256(ctx.controller),
                last_kept_trial_index=_last_kept_trial_index(list(ctx.ledger_prefix)),
                llm_calls=int(getattr(ctx.compute_budget, "llm_calls", 0)),
                controller_calls_at_e1=self._controller_calls,
            )
            return
        # E2 must not overwrite the E1 state; the E2 decision and the verify runs use the
        # E1 capture (the only deliberate update is the budget's llm_calls).
        if self._trial is None:
            raise SnapshotStop(f"hook {ctx.epoch} arrived before an E1 state")
        if ctx.epoch == "E2":
            # Capture the configuration the worker actually executed for this trial.  The
            # ledger decides whether it was kept; this list is the G1 record G7's summary and
            # G6's per-keep audits are built from (never a recomputed edit chain).
            live = read_worker_config(ctx.worker, ctx.node_spec)
            self.note_trial_config(
                trial_id=str(ctx.trial_id), budget_index=int(ctx.budget_index),
                decision=_decision_text(getattr(ctx.provisional, "decision", None)),
                config=live, w=int(self.count),
            )

    def observe_budget(self, budget: Any, *, where: str) -> None:
        """Record the exact budget and check charged-run parity at the charge."""
        self._last_budget = budget
        runs = getattr(budget, "worker_runs", None)
        if runs is not None:
            self.check_parity(runs, where=where)
        if self._trial is not None:
            calls = getattr(budget, "llm_calls", None)
            if calls is not None:
                self._trial.llm_calls = int(calls)

    # ---- controller wrapper callbacks ------------------------------------
    # ---- per-trial configuration records (G1 -> G7/G6 integration) -------
    def note_trial_config(self, *, trial_id: str, budget_index: int, decision: str,
                          config: Mapping[str, Any], w: int) -> None:
        """Record one executed trial's live configuration (the ledger decides keep/discard)."""
        contents = _files_config(dict(config))
        self._trial_configs.append({
            "trial_id": str(trial_id), "budget_index": int(budget_index),
            "decision": str(decision), "w": int(w),
            "config_sha256": config_sha256(contents), "files": contents,
        })

    def trial_configs(self) -> list[dict[str, Any]]:
        """Every executed trial configuration captured at E2, in trial order."""
        return [dict(row) for row in self._trial_configs]

    def config_by_trial(self) -> dict[int, dict[str, Any]]:
        return {int(row["budget_index"]): dict(row) for row in self._trial_configs}

    def note_decision(self, epoch: str, action: str, controller: Any | None = None) -> None:
        self._controller_calls += 1
        if self._trial is not None and epoch in ("E1", "E2"):
            self._trial.pending_action = action
        if epoch in ("E1", "E2"):
            # The final record is post-decision (unlike the exact-w snapshots, which keep the
            # E1 state by coordinator condition 3).  The harness gives us the live controller
            # object here, so hash its state after the decision.
            if controller is not None:
                self._post_decision_state = controller_state_sha256(controller)

    # ---- counting worker callback ----------------------------------------
    def note_run(self, run_kind: str, where: str) -> None:
        if self._trial is not None:
            # E1 decision = +1 controller call; a verify run happens after the E2 decision
            # = +2.  A revise/re-screen that adds another controller call fails closed.
            expected = self._trial.controller_calls_at_e1 + (2 if run_kind == "verify" else 1)
            if self._controller_calls != expected:
                raise SnapshotStop(
                    f"the controller was called {self._controller_calls - self._trial.controller_calls_at_e1} "
                    f"time(s) between the E1 hook and a {run_kind} run; expected "
                    f"{expected - self._trial.controller_calls_at_e1}"
                )
        self.count += 1
        w = self.count
        if w in SNAPSHOT_WS:
            self._write_snapshot(w, run_kind=run_kind, where=where)

    # ---- replicate-arm callbacks -----------------------------------------
    def begin_step(self, *, trial_id: str, incumbent_config: Mapping[str, Any],
                   start_config: Mapping[str, Any] | None, state: Any,
                   last_kept_trial_index: int | None, llm_calls: int,
                   step_index: int, pending_action: str | None = None) -> None:
        """Record the step-start state that the replicate arm's E2 decision will see.

        ``incumbent_config`` and ``start_config`` are **config contents** dicts (not a
        configuration sha); the recorder computes the sha exactly as the harness path does.
        ``state`` is G1's documented ordered projection of the engine and counter; it is
        hashed with the same canonical JSON rule as every other controller state.
        """
        if self._final_written:
            raise SnapshotStop("begin_step after the final snapshot")
        if state is None:
            raise SnapshotStop("begin_step needs the engine/counter projection")
        if start_config is not None:
            self.start_config = _files_config(dict(start_config))
        elif self.start_config is None:
            self.start_config = _files_config(dict(incumbent_config))
        contents = _files_config(dict(incumbent_config))
        self._trial = _TrialState(
            trial_id=str(trial_id),
            incumbent_config=contents,
            config_sha256=config_sha256(contents),
            controller_state_sha256=sha256_json(state),
            last_kept_trial_index=None if last_kept_trial_index is None else int(last_kept_trial_index),
            llm_calls=int(llm_calls),
            step_index=int(step_index),
            pending_action=pending_action,
        )
        self._pending = None

    def set_pending(self, *, step: int, j: int, candidate_metrics: list[float],
                    incumbent_metrics: list[float], diffs: list[float]) -> None:
        """Record the metrics seen so far inside a multi-run replicate step.

        The snapshot written at an exact ``w`` inside the step carries this object, so the
        in-step decision state is replayable without re-running the charged runs.
        """
        self._pending = {"step": int(step), "j": int(j),
                         "candidate_metrics": _jsonable(candidate_metrics),
                         "incumbent_metrics": _jsonable(incumbent_metrics),
                         "diffs": _jsonable(diffs)}

    def on_charge(self, run: Any) -> None:
        """The single per-charge hook of a replicate campaign (``ChargedRunCounter``).

        The counter has already appended ``run``; this callback must observe exactly the
        next charge.  It writes an exact-``w`` snapshot before the next worker call.
        """
        w = int(getattr(run, "w"))
        if w != self.count + 1:
            raise SnapshotParityStop(
                f"charged-run parity failure at charge {w}: recorder counted {self.count}; "
                "a block charge or an untracked run would make the snapshot invalid"
            )
        self.count = w
        if w in SNAPSHOT_WS:
            self._write_snapshot(w, run_kind=str(getattr(run, "kind", "replicate")),
                                 where=f"charge {w}")

    # ---- parity -----------------------------------------------------------
    def check_parity(self, budget_runs: int | None, *, where: str) -> None:
        if budget_runs is None:
            return
        if int(budget_runs) != self.count:
            raise SnapshotParityStop(
                f"charged-run parity failure at {where}: G1 wrapper counted {self.count}, "
                f"ComputeBudget.worker_runs is {int(budget_runs)}; a block charge or an untracked "
                f"run would make the snapshot invalid"
            )

    # ---- snapshot payload -------------------------------------------------
    def _payload(self, *, w: int, final: bool, ended_on: str | None = None,
                 run_kind: str | None = None) -> dict[str, Any]:
        trial = self._trial
        if trial is None:
            # A campaign that ends before its first E1 (w_final = 0, design §3.3): the
            # canonical record is final.json at w=0 with the start configuration.
            if not final or w != 0:
                raise SnapshotStop(f"no E1 state recorded before snapshot w={w}")
            incumbent = self.start_config or {}
            payload: dict[str, Any] = {
                "schema": SNAPSHOT_SCHEMA, "stage": self.stage, "arm": self.arm, "node": self.node,
                "repetition": int(self.repetition), "instance_id": self.instance_id,
                "w": 0, "w_actual": 0, "incumbent_config": incumbent,
                "start_config": self.start_config or {}, "last_kept_trial_index": None,
                "worker_runs": 0, "llm_calls": getattr(self._last_budget, "llm_calls", 0),
                "llm_calls_basis": "budget_observed_at_run", "ended": True,
                "config_sha256": config_sha256(incumbent),
                "controller_state_sha256": self._controller_state_at_hook,
                "pending_action": None, "trial_id": None, "run_kind": run_kind,
                "timestamp_utc": utc_now(), "final": True, "ended_on": ended_on,
            }
            return payload
        payload: dict[str, Any] = {
            "schema": SNAPSHOT_SCHEMA,
            "stage": self.stage,
            "arm": self.arm,
            "node": self.node,
            "repetition": int(self.repetition),
            "instance_id": self.instance_id,
            "w": int(w),
            "w_actual": int(w),
            "incumbent_config": trial.incumbent_config,
            "start_config": self.start_config or {},
            "last_kept_trial_index": trial.last_kept_trial_index,
            "worker_runs": int(w),
            "llm_calls": trial.llm_calls,
            "llm_calls_basis": "budget_observed_at_run",
            "ended": bool(final),
            "config_sha256": trial.config_sha256,
            "controller_state_sha256": trial.controller_state_sha256,
            "pending_action": trial.pending_action,
            "trial_id": trial.trial_id,
            "step_index": getattr(trial, "step_index", None),
            "run_kind": run_kind,
            "timestamp_utc": utc_now(),
        }
        if self._pending is not None:
            payload["pending"] = self._pending
        if final:
            payload["final"] = True
            payload["ended_on"] = ended_on
        return payload

    def _write_snapshot(self, w: int, *, run_kind: str, where: str) -> str:
        path = Path(self.out_dir) / "snapshots" / f"w{w}.json"
        if path.exists() or w in self._written:
            raise SnapshotStop(f"refusing to overwrite snapshot {path}")
        payload = self._payload(w=w, final=False, run_kind=run_kind)
        digest = _atomic_write_json(path, payload)
        self._written[w] = digest
        return digest

    def _final_payload(self, *, w: int, ended_on: str,
                       incumbent_config: Mapping[str, Any],
                       start_config: Mapping[str, Any] | None = None,
                       last_kept_trial_index: int | None = None,
                       llm_calls: int | None = None,
                       controller_state_sha256_value: str | None = None,
                       trial_id: str | None = None, step_index: int | None = None,
                       pending: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """The canonical post-decision final payload.

        ``incumbent_config`` is the live configuration after the last decision (read from the
        node on the harness route, or the engine's post-decision incumbent on the replicate
        route), never a cached pre-E1 copy.
        """
        contents = _files_config(dict(incumbent_config))
        payload: dict[str, Any] = {
            "schema": SNAPSHOT_SCHEMA, "stage": self.stage, "arm": self.arm, "node": self.node,
            "repetition": int(self.repetition), "instance_id": self.instance_id,
            "w": int(w), "w_actual": int(w), "incumbent_config": contents,
            "start_config": _files_config(dict(start_config)) if start_config is not None
            else (self.start_config or {}),
            "last_kept_trial_index": None if last_kept_trial_index is None else int(last_kept_trial_index),
            "worker_runs": int(w),
            "llm_calls": int(llm_calls) if llm_calls is not None else getattr(self._last_budget, "llm_calls", 0),
            "llm_calls_basis": "budget_observed_at_run",
            "ended": True,
            "config_sha256": config_sha256(contents),
            "controller_state_sha256": controller_state_sha256_value or self._post_decision_state
            or self._controller_state_at_hook,
            "pending_action": None, "trial_id": trial_id, "step_index": step_index,
            "run_kind": "final", "timestamp_utc": utc_now(), "final": True, "ended_on": ended_on,
        }
        if pending is not None:
            payload["pending"] = _jsonable(pending)
        return payload

    def _write_final_payload(self, payload: Mapping[str, Any], *, w_final: int) -> str:
        """Write final.json; canonicalise the at-W record if one exists.

        The w snapshot is written immediately after the charge that reaches ``w``, i.e. before
        that trial's E2 decision.  It is therefore a pre-decision record and must never be
        aliased as final.  When the campaign reaches W, the pre-decision payload is preserved
        as ``w<W>_pre.json`` (unchanged apart from the two provenance fields ``pre_decision``
        and ``superseded_by``; a distinct replay record) and ``w<W>.json`` is rewritten from
        the post-decision final, so G6 audits one canonical Y(W) and G7's equality check holds.
        """
        if payload.get("ended_on") not in ENDED_ON:
            raise SnapshotStop(f"unknown ended_on {payload.get('ended_on')!r}")
        path = Path(self.out_dir) / "snapshots" / "final.json"
        if path.exists() or self._final_written:
            raise SnapshotStop(f"refusing to overwrite {path}")
        if int(w_final) != int(payload["w"]):
            raise SnapshotParityStop(
                f"final payload w={payload['w']} differs from the recorder's charged count {w_final}"
            )
        if int(w_final) in SNAPSHOT_WS and payload.get("ended_on") != "error":
            source = Path(self.out_dir) / "snapshots" / f"w{int(w_final)}.json"
            if source.is_file():
                pre = json.loads(source.read_text(encoding="utf-8"))
                pre["pre_decision"] = True
                pre["superseded_by"] = "final.json"
                pre_path = Path(self.out_dir) / "snapshots" / f"w{int(w_final)}_pre.json"
                if pre_path.exists():
                    raise SnapshotStop(f"refusing to overwrite {pre_path}")
                self._pre_written[int(w_final)] = _atomic_write_json(pre_path, pre)
                canonical = dict(payload)
                canonical["final"] = False
                canonical["ended"] = False
                canonical.pop("ended_on", None)
                canonical["run_kind"] = "final-at-w"
                canonical["canonical_final"] = "final.json"
                self._written[int(w_final)] = _atomic_write_json(source, canonical)
        digest = _atomic_write_json(path, payload)
        self._final_written = True
        return digest

    def write_final(self, *, w_final: int, ended_on: str) -> str:
        """Write ``snapshots/final.json`` (single call; w=0 keeps its historical meaning).

        At w>0 the live post-decision incumbent is required: use :meth:`write_final_live`
        for a harness campaign and :meth:`write_final_from_state` for a replicate campaign.
        """
        if ended_on not in ENDED_ON:
            raise SnapshotStop(f"unknown ended_on {ended_on!r}")
        if int(w_final) != self.count:
            raise SnapshotParityStop(
                f"final w_final={w_final} differs from the recorder's charged count {self.count}"
            )
        if int(w_final) != 0:
            raise SnapshotStop("a final at w>0 needs the live incumbent and ledger; use write_final_live")
        payload = self._final_payload(
            w=0, ended_on=ended_on, incumbent_config=self.start_config or {},
            last_kept_trial_index=None,
            llm_calls=getattr(self._last_budget, "llm_calls", 0) if self._last_budget is not None else 0,
            trial_id=None, step_index=None,
        )
        return self._write_final_payload(payload, w_final=0)

    def write_final_live(self, *, w_final: int, ended_on: str, worker: Any,
                         node_spec: Any, ledger_path: str | Path | None = None,
                         incumbent_config: Mapping[str, Any] | None = None,
                         state: Any | None = None,
                         last_kept_trial_index: int | None = None,
                         llm_calls: int | None = None,
                         trial_id: str | None = None, step_index: int | None = None,
                         pending: Mapping[str, Any] | None = None) -> str:
        """Write the harness route's post-decision final from the live node configuration.

        ``worker`` is the live worker (a ``CountingWorker`` delegates ``node_root``); the
        editable files after ``run_real_campaign`` are the terminal incumbent, including a
        keep on the final trial.  The ledger supplies the last kept trial index, the final
        trial id and the LLM count.  The post-decision controller state is the one captured
        by the last E1/E2 decision; the exact-w snapshots keep the E1 state as before.
        """
        if ended_on not in ENDED_ON:
            raise SnapshotStop(f"unknown ended_on {ended_on!r}")
        if int(w_final) != self.count:
            raise SnapshotParityStop(
                f"final w_final={w_final} differs from the recorder's charged count {self.count}"
            )
        contents = dict(incumbent_config) if incumbent_config is not None else read_worker_config(worker, node_spec)
        if int(w_final) == 0:
            contents = dict(contents or self.start_config or {})
        elif not contents:
            raise SnapshotStop("a kept campaign must provide its live final config contents")
        rows: list[dict[str, Any]] = []
        if ledger_path is not None and Path(ledger_path).is_file():
            for line in Path(ledger_path).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        if rows:
            if last_kept_trial_index is None:
                last_kept_trial_index = _last_kept_from_rows(rows)
            last = rows[-1]
            if llm_calls is None and last.get("llm_calls") is not None:
                llm_calls = int(last["llm_calls"])
            if trial_id is None:
                trial_id = last.get("trial_id")
            if step_index is None:
                step_index = last.get("step_index")
        if llm_calls is None and self._last_budget is not None:
            llm_calls = getattr(self._last_budget, "llm_calls", None)
        state_sha = sha256_json(state) if state is not None else (self._post_decision_state
                                                                  or self._controller_state_at_hook)
        payload = self._final_payload(w=int(w_final), ended_on=ended_on, incumbent_config=contents,
                                      last_kept_trial_index=last_kept_trial_index,
                                      llm_calls=llm_calls, controller_state_sha256_value=state_sha,
                                      trial_id=trial_id, step_index=step_index, pending=pending)
        return self._write_final_payload(payload, w_final=int(w_final))

    def write_final_from_state(self, *, w_final: int, ended_on: str,
                               incumbent_config: Mapping[str, Any], state: Any,
                               last_kept_trial_index: int | None, llm_calls: int,
                               trial_id: str | None = None,
                               step_index: int | None = None,
                               pending: Mapping[str, Any] | None = None) -> str:
        """Write the replicate arm's post-decision ``final.json``.

        The replicate exact-``w`` snapshot is the pre-decision state inside the last step;
        at W it is preserved as ``w<W>_pre.json`` and the canonical ``w<W>.json`` is
        rewritten from this post-decision record (the final governs), so one audit serves
        both and G7's Y(W) = final equality holds.
        """
        if ended_on not in ENDED_ON:
            raise SnapshotStop(f"unknown ended_on {ended_on!r}")
        if int(w_final) != self.count:
            raise SnapshotParityStop(
                f"final w_final={w_final} differs from the recorder's charged count {self.count}"
            )
        if int(w_final) == 0 and ended_on not in ("llm_call_cap", "error"):
            raise SnapshotStop(f"a campaign with w_final = 0 can only end llm_call_cap, not {ended_on!r}")
        if state is None:
            raise SnapshotStop("write_final_from_state needs the engine/counter projection")
        if int(w_final) == 0:
            contents = dict(incumbent_config or self.start_config or {})
        else:
            if not incumbent_config:
                raise SnapshotStop("a kept campaign must pass its final config contents")
            contents = dict(incumbent_config)
        payload = self._final_payload(w=int(w_final), ended_on=ended_on, incumbent_config=contents,
                                      last_kept_trial_index=last_kept_trial_index,
                                      llm_calls=llm_calls, controller_state_sha256_value=sha256_json(state),
                                      trial_id=trial_id, step_index=step_index, pending=pending)
        return self._write_final_payload(payload, w_final=int(w_final))

    def pre_decision_hashes(self) -> dict[str, str]:
        return {f"w{w}_pre.json": digest for w, digest in sorted(self._pre_written.items())}

    def snapshot_hashes(self) -> dict[str, str]:
        return {f"w{w}.json": digest for w, digest in sorted(self._written.items())}


class CountingWorker:
    """A ``Worker`` proxy that counts the harness's charged worker runs.

    The proxy is exactly one count per ``run_trial``/``run_trial_at_seed`` call, including
    a call that raises: the harness charges a failed run too (a failed run that consumed a
    worker run is charged once).  ``run_trial_at_seed`` is exposed only when the wrapped
    worker exposes it, so the harness's verify feasibility is unchanged.
    """

    def __init__(self, inner: Any, recorder: SnapshotRecorder) -> None:
        self._inner = inner
        self.recorder = recorder
        self.mode = getattr(inner, "mode", "counting_worker")
        if callable(getattr(inner, "run_trial_at_seed", None)):
            self.run_trial_at_seed = self._run_at_seed

    def run_trial(self, proposal: Any, node_spec: Any, budget_index: int) -> Any:
        try:
            return self._inner.run_trial(proposal, node_spec, budget_index)
        finally:
            self.recorder.note_run("main", "run_trial")

    def _run_at_seed(self, proposal: Any, node_spec: Any, budget_index: int, **kwargs: Any) -> Any:
        try:
            return self._inner.run_trial_at_seed(proposal, node_spec, budget_index, **kwargs)
        finally:
            self.recorder.note_run("verify", "run_trial_at_seed")

    def __getattr__(self, name: str) -> Any:
        if name == "run_trial_at_seed":
            raise AttributeError(name)
        return getattr(self._inner, name)


class RecordingController:
    """A ``Controller`` proxy that reports the action and its LLM calls to the recorder."""

    def __init__(self, inner: Any, recorder: SnapshotRecorder) -> None:
        self._inner = inner
        self.recorder = recorder

    def decide(self, view: Any, mask: Mapping[str, bool]) -> Any:
        decision = self._inner.decide(view, mask)
        self.recorder.note_decision(str(view.epoch), str(decision.action), controller=self._inner)
        return decision

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def wrap(campaign_kwargs: Mapping[str, Any], recorder: SnapshotRecorder) -> dict[str, Any]:
    """Return ``run_real_campaign`` kwargs with the counting worker and recording controller.

    The caller supplies ``worker`` and ``controller``; they are replaced by their proxies.
    ``snapshot_hook`` is the recorder.  A ``compute_budget`` is converted to
    :class:`ParityBudget` so every charge is observed; when it is absent a parity budget
    with no caps is created (the G1 chunk always supplies the declared W/cap).
    Any other keyword is passed through unchanged.
    """
    out = dict(campaign_kwargs)
    if "worker" not in out or "controller" not in out:
        raise ValueError("wrap() needs the harness worker and controller")
    budget = out.get("compute_budget")
    if isinstance(budget, ParityBudget):
        pass
    elif isinstance(budget, ComputeBudget):
        out["compute_budget"] = ParityBudget(
            max_worker_runs=budget.max_worker_runs,
            max_worker_seconds=budget.max_worker_seconds,
            max_llm_calls=budget.max_llm_calls,
            worker_runs=budget.worker_runs,
            worker_seconds=budget.worker_seconds,
            llm_calls=budget.llm_calls,
            recorder=recorder,
        )
    elif budget is None:
        out["compute_budget"] = ParityBudget(recorder=recorder)
    else:
        raise TypeError(f"unsupported compute_budget type {type(budget).__name__}")
    out["worker"] = CountingWorker(out["worker"], recorder)
    out["controller"] = RecordingController(out["controller"], recorder)
    out["snapshot_hook"] = recorder
    return out
