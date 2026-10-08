"""B-DAC1: decision-time text serialisation of H1 / H2 for the configurator encoder.

Design reference: ``docs/paper_split/B_DAC_CONFIGURATOR_AMENDMENT_20261004.md`` §4.1.

The configurator's encoder reads a *text* view of the agent's history at a
checkpoint.  This module is the only path from a recorded history to that text,
and it enforces the controller-design information rules (design v2 §1-§2):

- only events at or before the checkpoint step enter the text (no information
  from after the decision time);
- only allowlisted event kinds enter the text; outcome, grade, hidden-data and
  evaluator-only material cannot be represented as an event;
- declared identifiers (root, template, family ids) are redacted, so the
  encoder cannot key on lineage;
- the H1 events must be an exact prefix of the H2 events (H2 contains H1 and
  the checkpoint-2 history is the continue branch's own state);
- truncation is deterministic: the task statement (capped) is always kept,
  then the most recent events that fit, with an explicit omission marker.

The character budget is a conservative proxy for the encoder's token budget
(CLM's reference server uses 2,048 tokens).  The bound encoder records the
prompt-token count it actually received, so silent server-side truncation is
detectable (``encoder.CLMEncoder``).

Nothing here calls a model.  Nothing here is scientific evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

SERIALISER_VERSION = "b_dac_serialiser_v1"

#: Event kinds that may appear in a decision-time history.  Anything else
#: (an outcome, a grade, hidden rows, a condition label) is rejected, not
#: filtered, so a mislabelled record cannot pass silently.
ALLOWED_KINDS = frozenset({
    "task",          # the task statement shown to the agent
    "assistant",     # the agent's own messages / reasoning summaries
    "tool_call",     # a tool invocation (name + arguments)
    "tool_result",   # the visible tool output
    "observation",   # environment messages visible to the agent
    "checkpoint",    # the checkpoint marker itself
})

#: Defaults sized for CLM's 2,048-token reference context at roughly three
#: characters per token, leaving headroom for the template.
DEFAULT_MAX_CHARS = 6000
DEFAULT_TASK_CHARS = 1200
DEFAULT_EVENT_CHARS = 800
REDACTION = "<id>"


class SerialiserError(ValueError):
    """A history violates the decision-time information rules."""


@dataclass(frozen=True)
class HistoryEvent:
    step: int
    kind: str
    text: str
    name: str = ""   # tool name for tool_call / tool_result

    def __post_init__(self) -> None:
        if self.kind not in ALLOWED_KINDS:
            raise SerialiserError(f"event kind {self.kind!r} is not decision-time visible")
        if not isinstance(self.step, int) or self.step < 0:
            raise SerialiserError("event step must be a non-negative int")


@dataclass(frozen=True)
class DecisionHistory:
    """The recorded history of one branch up to (and including) a checkpoint."""

    phase: int
    checkpoint_step: int
    events: tuple[HistoryEvent, ...]
    redact: tuple[str, ...] = field(default_factory=tuple)
    # Provenance (runbook step 2).  Never rendered into the serialised text:
    # the ids are redaction targets, the digests bind the history to the
    # session file the executor captured it from.
    root_id: str = ""
    template_family_id: str = ""
    session_prefix_sha256: str = ""
    raw_sha256: str = ""

    def __post_init__(self) -> None:
        if self.phase not in (1, 2):
            raise SerialiserError("phase must be 1 or 2")
        steps = [e.step for e in self.events]
        if steps != sorted(steps):
            raise SerialiserError("events must be in step order")
        late = [e.step for e in self.events if e.step > self.checkpoint_step]
        if late:
            raise SerialiserError(
                f"events after the checkpoint step {self.checkpoint_step}: {late[:3]}")
        if not any(e.kind == "task" for e in self.events):
            raise SerialiserError("a history must carry its task statement")


@dataclass(frozen=True)
class SerialisedHistory:
    phase: int
    text: str
    sha256: str
    n_events: int
    n_kept: int
    truncated: bool
    serialiser_version: str = SERIALISER_VERSION


def _redact(text: str, ids: tuple[str, ...]) -> str:
    for ident in sorted((i for i in ids if i), key=len, reverse=True):
        text = text.replace(ident, REDACTION)
    return text


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: max(0, n - 3)] + "..."


def _line(event: HistoryEvent, max_event_chars: int) -> str:
    tag = event.kind if not event.name else f"{event.kind}:{event.name}"
    body = " ".join(event.text.split())
    return f"[{event.step:03d} {tag}] {_clip(body, max_event_chars)}"


def serialise(history: DecisionHistory, *, max_chars: int = DEFAULT_MAX_CHARS,
              task_chars: int = DEFAULT_TASK_CHARS,
              event_chars: int = DEFAULT_EVENT_CHARS) -> SerialisedHistory:
    """Render a decision-time history as deterministic text."""

    if max_chars <= task_chars + 200:
        raise SerialiserError("max_chars leaves no room for events")
    task = " ".join(" ".join(e.text.split()) for e in history.events if e.kind == "task")
    header = (f"CHECKPOINT {history.phase} | step {history.checkpoint_step}\n"
              f"TASK: {_clip(task, task_chars)}\n")
    body_events = [e for e in history.events if e.kind != "task"]
    lines = [_line(e, event_chars) for e in body_events]
    budget = max_chars - len(header) - 64
    kept: list[str] = []
    used = 0
    for line in reversed(lines):          # most recent first
        if used + len(line) + 1 > budget:
            break
        kept.append(line)
        used += len(line) + 1
    kept.reverse()
    omitted = len(lines) - len(kept)
    text = header
    if omitted:
        text += f"[... {omitted} earlier events omitted ...]\n"
    text += "\n".join(kept)
    text = _redact(text, history.redact)
    return SerialisedHistory(
        phase=history.phase, text=text,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        n_events=len(history.events), n_kept=len(kept) + 1, truncated=bool(omitted))


def check_prefix(h1: DecisionHistory, h2: DecisionHistory) -> None:
    """H2 must extend H1 exactly (same continue branch, no transplanted state)."""

    if h1.phase != 1 or h2.phase != 2:
        raise SerialiserError("check_prefix expects (phase-1, phase-2) histories")
    if h2.checkpoint_step <= h1.checkpoint_step:
        raise SerialiserError("checkpoint 2 must come after checkpoint 1")
    if tuple(h2.events[: len(h1.events)]) != tuple(h1.events):
        raise SerialiserError("H1 events are not a prefix of H2 events")


def serialise_root(h1: DecisionHistory, h2: DecisionHistory | None, **kw
                   ) -> tuple[SerialisedHistory, SerialisedHistory | None]:
    """Serialise one root's checkpoint histories (H2 is None if not reached)."""

    s1 = serialise(h1, **kw)
    if h2 is None:
        return s1, None
    check_prefix(h1, h2)
    return s1, serialise(h2, **kw)


def history_from_json(obj: dict) -> DecisionHistory:
    """Load a history from its JSON record (the planned live-run format)."""

    return DecisionHistory(
        phase=int(obj["phase"]), checkpoint_step=int(obj["checkpoint_step"]),
        events=tuple(HistoryEvent(step=int(e["step"]), kind=e["kind"], text=e["text"],
                                  name=e.get("name", "")) for e in obj["events"]),
        redact=tuple(obj.get("redact", ())),
        root_id=str(obj.get("root_id", "")),
        template_family_id=str(obj.get("template_family_id", "")),
        session_prefix_sha256=str(obj.get("session_prefix_sha256", "")),
        raw_sha256=str(obj.get("raw_sha256", "")))


def history_to_json(h: DecisionHistory) -> dict:
    return {"phase": h.phase, "checkpoint_step": h.checkpoint_step,
            "events": [{"step": e.step, "kind": e.kind, "text": e.text, "name": e.name}
                       for e in h.events],
            "redact": list(h.redact),
            "root_id": h.root_id, "template_family_id": h.template_family_id,
            "session_prefix_sha256": h.session_prefix_sha256, "raw_sha256": h.raw_sha256}


def serialiser_fingerprint(**kw) -> str:
    cfg = {"version": SERIALISER_VERSION, "max_chars": kw.get("max_chars", DEFAULT_MAX_CHARS),
           "task_chars": kw.get("task_chars", DEFAULT_TASK_CHARS),
           "event_chars": kw.get("event_chars", DEFAULT_EVENT_CHARS),
           "allowed_kinds": sorted(ALLOWED_KINDS)}
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
