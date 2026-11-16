"""B1 proposer calls: a per-call completion cap, and a truncated output is an invalid proposal.

PLAN §10 ``R1-EXAM-B1-TRUNCATION-INVALID`` (11 Nov 2026). AI-assisted (Claude).

Why. B1 run ``fffa_20261111_b`` stopped when one ``qwen36_27b`` thinking-on generation filled the
32,768-token context (completion 31,551 tokens). On the ``manager_proposal/v1`` path the harness asks for
a JSON-schema ``response_format``, so ``langchain_openai`` parses the reply through the OpenAI SDK's
structured-output parser. That parser raises ``openai.LengthFinishReasonError`` when
``finish_reason == "length"``, before any content reaches the harness's proposal validator. The pinned harness
(``a3fedbb``) treats any exception from the call as non-retryable, logs ``llm_call_failed`` and re-raises it,
and nothing above it catches it. So the root worker exited 1 and the batch stopped. A *returned* reply that does
not parse would have been an invalid proposal instead. See ``reports/B1_TRUNCATION_DIAGNOSIS_20261111.md``.

What this module changes, on the paper side only (the harness pin stays ``a3fedbb``):

* Every proposer call carries ``max_tokens = B1_MAX_COMPLETION_TOKENS`` on the chat model. langchain-openai 1.x
  sends it as ``max_completion_tokens`` (older clients as ``max_tokens``); llama.cpp ``620d222`` reads either
  name as ``n_predict``. The host's frozen client versions are checked before the restart (restart hand-off
  ``_c`` §0).
* A reply cut short (``LengthFinishReasonError`` or ``ContentFilterFinishReasonError`` from the SDK
  parser, or a returned reply whose ``finish_reason`` is ``length`` or ``content_filter``) reaches the harness
  as an empty reply. Its text is discarded, even when part of it would parse. The harness's own validator
  then marks it ``parse_failed``, and the control plane records it as an invalid trial
  (``PROPOSAL_PRECONDITION_FAILED``, no worker run). The call is charged to the LLM budget like every
  other proposal call, and the campaign continues.
* The trial's ``llm_call`` record (copied into the ``llm_call`` event) gains ``max_completion_tokens``,
  ``finish_reason`` and ``truncated`` on every call. A truncated call also gains ``truncation_policy``,
  the SDK error type (if any), and the discarded character counts.

R1-EXAM-B1-MODEL-OUTPUT-INVALID (13 Nov 2026) extends this to a prompt that has outgrown the context:
llama-server answers HTTP 400 ``exceed_context_size_error`` and no reply exists. Past trial 1 that can only
come from model text the memory summary repeats, so the call becomes an empty reply and an invalid trial,
charged, like a truncation (``context_overflow`` in its record). At trial 1 it stays a STOP: a
configuration fault. The model-output pre-check and the proposal journal are described on
``B1CappedLangGraphManager``.

Unchanged: the harness pin, the prompt, the schema, the seed, ``cache_prompt``, the observer (which has its
own ``max_tokens`` and its own non-fatal ``query_failed`` path), every other exception (still a STOP), and the
root manifest and its diagnostics. A truncated trial counts under ``invalid`` and ``parse_failed`` there,
exactly like any other unparseable proposal.
"""
from __future__ import annotations

from autoresearch.manager.langgraph_manager import LangGraphManager

# Per proposer call. Fixed before the per-root completion usage of run fffa_20261111_b was read; the
# restart hand-off checks it is above the largest completion of every completed root (PLAN row).
B1_MAX_COMPLETION_TOKENS = 16384
TRUNCATION_POLICY = 'b1_truncated_output_invalid/v1'
TRUNCATING_FINISH_REASONS = frozenset({'length', 'content_filter'})


def _truncation_errors() -> tuple[type[BaseException], ...]:
    import openai
    names = ('LengthFinishReasonError', 'ContentFilterFinishReasonError')
    found = tuple(getattr(openai, n) for n in names if isinstance(getattr(openai, n, None), type))
    if len(found) != len(names):
        raise RuntimeError('STOP: the installed openai SDK lacks the finish-reason error classes')
    return found


CONTEXT_OVERFLOW_TYPE = 'exceed_context_size_error'


def _context_overflow(exc) -> dict | None:
    """llama-server's HTTP 400 for a prompt longer than the context (llama.cpp 620d222 ``server-context.cpp``).

    Returns ``{'prompt_tokens': n | None, 'message': ...}`` for that error and None for any other."""
    import re
    import openai
    if not isinstance(exc, openai.BadRequestError):
        return None
    body = getattr(exc, 'body', None)
    err = body.get('error', body) if isinstance(body, dict) else None
    if not isinstance(err, dict) or err.get('type') != CONTEXT_OVERFLOW_TYPE:
        return None
    message = str(err.get('message') or '')
    tokens = err.get('n_prompt_tokens')
    if type(tokens) is not int:
        found = re.search(r'request \((\d+) tokens\)', message)
        tokens = int(found.group(1)) if found else None
    return {'prompt_tokens': tokens, 'message': message[:300]}


_REPLY_FIELDS = frozenset({'rationale', 'summary', 'objective', 'param', 'old_value', 'new_value'})  # manager_proposal/v1


def _has_lone_surrogate(text: str) -> bool:
    """True if ``text`` holds a UTF-16 surrogate code point, which cannot be encoded as UTF-8."""
    return any('\ud800' <= ch <= '\udfff' for ch in text)


def _unencodable(content) -> bool:
    """A reply whose ``summary`` field, as the harness will parse it, carries a lone surrogate (e.g. the JSON
    escape ``\\ud800``).

    In B1's memory mode the summary is the only reply field the harness copies into later prompts (the trial's
    summary line and the best-strategy line). The HTTP client cannot encode such a prompt, so the next proposer
    call would raise ``UnicodeEncodeError`` and stop the root. Only this case is caught; a surrogate in any other
    field reaches no later prompt and is left to the harness exactly as before. The parse mirrors the harness's
    schema path (``langgraph_manager`` l. 562-566 and 288-295 at a3fedbb): inline ``<think>`` blocks are removed,
    the rest must be a JSON object of exactly the six string fields, otherwise the harness records a parse
    failure with its default summary and no surrogate can reach memory."""
    import json
    import re
    if not isinstance(content, str):
        return False
    content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()
    try:
        parsed = json.loads(content)
    except (ValueError, RecursionError):
        return False
    if not isinstance(parsed, dict) or set(parsed) != _REPLY_FIELDS or any(not isinstance(v, str) for v in parsed.values()):
        return False
    return _has_lone_surrogate(parsed['summary'].strip())


def _sdk_usage(completion) -> tuple[int | None, int | None]:
    usage = getattr(completion, 'usage', None)
    prompt = getattr(usage, 'prompt_tokens', None)
    output = getattr(usage, 'completion_tokens', None)
    return (prompt if type(prompt) is int else None, output if type(output) is int else None)


def _sdk_discarded(completion) -> tuple[int, int]:
    try:
        message = completion.choices[0].message
    except Exception:
        return 0, 0
    content = getattr(message, 'content', None)
    reasoning = getattr(message, 'reasoning_content', None)
    if reasoning is None:
        reasoning = (getattr(message, 'model_extra', None) or {}).get('reasoning_content')
    return (len(content) if isinstance(content, str) else 0, len(reasoning) if isinstance(reasoning, str) else 0)


def _empty_reply(prompt_tokens: int | None, completion_tokens: int | None, finish_reason: str):
    """An empty assistant reply with the call's usage, so the harness records the token counts."""
    from langchain_core.messages import AIMessage
    kwargs = {'content': '', 'response_metadata': {'finish_reason': finish_reason}}
    if prompt_tokens is not None and completion_tokens is not None:
        kwargs['usage_metadata'] = {'input_tokens': prompt_tokens, 'output_tokens': completion_tokens,
                                    'total_tokens': prompt_tokens + completion_tokens}
    return AIMessage(**kwargs)


class TruncationGuard:
    """Wraps the chat model of one proposer call; turns a truncated reply into an empty one."""

    def __init__(self, model, cap: int):
        self.model = model
        self.cap = cap
        self.calls = 0
        self.outcome: dict | None = None
        self.raw_content: str | None = None

    def invoke(self, messages, *args, **kwargs):
        self.calls += 1
        self.outcome = None
        self.raw_content = None
        try:
            response = self.model.invoke(messages, *args, **kwargs)
        except _truncation_errors() as exc:
            completion = getattr(exc, 'completion', None)
            finish = 'content_filter' if type(exc).__name__ == 'ContentFilterFinishReasonError' else 'length'
            prompt_tokens, completion_tokens = _sdk_usage(completion)
            content_chars, reasoning_chars = _sdk_discarded(completion)
            self.outcome = {'finish_reason': finish, 'truncated': True, 'truncation_error_type': type(exc).__name__,
                            'discarded_content_chars': content_chars, 'discarded_reasoning_chars': reasoning_chars}
            return _empty_reply(prompt_tokens, completion_tokens, finish)
        except Exception as exc:
            overflow = _context_overflow(exc)
            if overflow is None:
                raise
            # R1-EXAM-B1-MODEL-OUTPUT-INVALID: the prompt outgrew the context (the memory summary repeats
            # earlier model text); no reply exists, so the proposal is invalid like a truncated one.
            self.outcome = {'finish_reason': None, 'truncated': False, 'context_overflow': True,
                            'context_overflow_prompt_tokens': overflow['prompt_tokens'],
                            'context_overflow_message': overflow['message']}
            return _empty_reply(None, None, 'context_overflow')
        meta = getattr(response, 'response_metadata', None) or {}
        finish = meta.get('finish_reason')
        if finish in TRUNCATING_FINISH_REASONS:
            usage = getattr(response, 'usage_metadata', None) or {}
            content = getattr(response, 'content', '')
            reasoning = (getattr(response, 'additional_kwargs', None) or {}).get('reasoning_content')
            self.outcome = {'finish_reason': finish, 'truncated': True, 'truncation_error_type': None,
                            'discarded_content_chars': len(content) if isinstance(content, str) else 0,
                            'discarded_reasoning_chars': len(reasoning) if isinstance(reasoning, str) else 0}
            return _empty_reply(usage.get('input_tokens'), usage.get('output_tokens'), finish)
        content = getattr(response, 'content', None)
        if _unencodable(content):
            # R1-EXAM-B1-MODEL-OUTPUT-INVALID (M20): unusable model text; an invalid proposal like a truncation.
            usage = getattr(response, 'usage_metadata', None) or {}
            self.outcome = {'finish_reason': finish, 'truncated': False, 'unencodable_reply': True,
                            'discarded_content_chars': len(content)}
            return _empty_reply(usage.get('input_tokens'), usage.get('output_tokens'), finish or 'stop')
        self.outcome = {'finish_reason': finish, 'truncated': False}
        self.raw_content = content if isinstance(content, str) else None
        return response


class B1CappedLangGraphManager(LangGraphManager):
    """The pinned harness proposer, with the completion cap and the truncation rule of this module.

    R1-EXAM-B1-MODEL-OUTPUT-INVALID (13 Nov 2026) adds two things here, both before the control plane can
    call the worker:

    * the model-output checks of ``r1.exam.b1_proposal_precheck``. A proposal that fails them, and that the
      harness itself would neither revise (D25 inactive key) nor reject (its precondition checks), loses its
      structured edit and is marked ``proposal_precondition_failed``. The harness then records it as an
      invalid trial without a worker run. The rejected edit and the reason are kept in
      ``extra['b1_model_output_rejected']``. Proposals the harness revises or rejects by itself are left
      exactly as before, so every trial that did not STOP before is recorded exactly as before;
    * a durable proposal journal (``journal_path``, one fsynced JSON line per proposer call, first proposals
      and D25 revisions): the objective, the structured edit, the directive the worker would parse, the raw
      reply and the check outcome. It is written before ``propose_next_trial`` returns, so before any
      execution.

    ``b1_worker`` must be set to the campaign's worker (the harness precondition reads its node root)."""

    def __init__(self, *args, max_completion_tokens: int = B1_MAX_COMPLETION_TOKENS, journal_path=None, **kwargs):
        if type(max_completion_tokens) is not int or max_completion_tokens < 1:
            raise ValueError('max_completion_tokens must be a positive int')
        _truncation_errors()   # fail at construction, not mid-campaign, if the SDK lacks the error classes
        super().__init__(*args, **kwargs)
        self.b1_max_completion_tokens = max_completion_tokens
        self._b1_guards: list[TruncationGuard] = []
        self.b1_journal_path = journal_path
        self.b1_worker = None

    def _resolve_llm(self, seed: int | None = None):
        model = super()._resolve_llm(seed=seed)
        if self._injected_llm is not None:
            raise RuntimeError('STOP: the B1 capped proposer does not take an injected model')
        guard = TruncationGuard(model.model_copy(update={'max_tokens': self.b1_max_completion_tokens}),
                                self.b1_max_completion_tokens)
        self._b1_guards.append(guard)
        return guard

    def propose_next_trial(self, status, memory_context, node_spec, *, revision_feedback=None, revision_attempt=None):
        self._b1_guards = []
        proposal = super().propose_next_trial(status, memory_context, node_spec, revision_feedback=revision_feedback,
                                              revision_attempt=revision_attempt)
        used = [g for g in self._b1_guards if g.calls]
        call = (proposal.extra or {}).get('llm_call')
        if len(used) != 1 or used[0].calls != 1 or used[0].outcome is None or not isinstance(call, dict):
            raise RuntimeError('STOP: B1 proposer call record is not exactly one guarded call')
        outcome = used[0].outcome
        call['max_completion_tokens'] = self.b1_max_completion_tokens
        call.update(outcome)
        if outcome['truncated'] or outcome.get('context_overflow') or outcome.get('unencodable_reply'):
            if outcome['truncated']:
                call['truncation_policy'] = TRUNCATION_POLICY
            elif outcome.get('unencodable_reply'):
                from r1.exam.b1_proposal_precheck import POLICY
                call['unencodable_reply_policy'] = POLICY
            else:
                from r1.exam.b1_proposal_precheck import POLICY
                call['context_overflow_policy'] = POLICY
                if status.budget_index <= 1:
                    # nothing the model wrote is in the first prompt: a configuration fault, not model output
                    raise RuntimeError('STOP: B1 first proposer prompt exceeds the context')
            if call.get('parse_ok') is not False or proposal.extra.get('parse_failed') is not True \
                    or proposal.extra.get('structured_edit'):
                raise RuntimeError('STOP: a truncated B1 proposal was not rejected by the harness validator')
        edit = proposal.extra.get('structured_edit')
        outcome_kind, rejection = self._b1_model_output_check(proposal, status, node_spec)
        if rejection is not None:
            from autoresearch.nodes.active_keys import inactive_key_in_proposal
            from r1.exam.b1_proposal_precheck import POLICY
            proposal.extra.pop('structured_edit', None)
            proposal.extra.pop('deterministic_patch', None)
            proposal.extra['proposal_precondition_failed'] = True
            proposal.extra['b1_model_output_rejected'] = {'policy': POLICY, **rejection, 'structured_edit': edit}
            # Without its structured edit, the harness's D25 check would read the key from the objective and could
            # ask for a revision of a rejected proposal. Name the (active) edit key so the rejection is final.
            proposal.extra['named_param'] = edit['symbol']
            if inactive_key_in_proposal(proposal, node_spec, status.current_constants) is not None:
                raise RuntimeError('STOP: a rejected B1 proposal would still be revised by the D25 loop')
        self._b1_journal(status, proposal, edit, used[0].raw_content, revision_attempt, outcome_kind, rejection)
        return proposal

    def _b1_model_output_check(self, proposal, status, node_spec):
        """Return (outcome kind, rejection or None). Only proposals headed for the worker are checked."""
        from autoresearch.control_plane.campaign import _precondition_failure_result
        from autoresearch.nodes.active_keys import inactive_key_in_proposal
        from r1.exam.b1_proposal_precheck import check_model_output
        edit = proposal.extra.get('structured_edit')
        if proposal.extra.get('parse_failed') or not isinstance(edit, dict):
            return 'not_applicable', None          # the harness rejects it (parse or precondition)
        if inactive_key_in_proposal(proposal, node_spec, status.current_constants) is not None:
            return 'd25_inactive_key', None        # the harness revises or skips it; never executed as is
        if self.b1_worker is None:
            raise RuntimeError('STOP: B1 proposer has no worker for the precondition check')
        if _precondition_failure_result(proposal, node_spec, self.b1_worker) is not None:
            return 'harness_precondition', None    # the harness rejects it exactly as before
        rejection = check_model_output(proposal.objective, edit, node_spec)
        return ('rejected' if rejection else 'passed'), rejection

    def _b1_journal(self, status, proposal, edit, raw, revision_attempt, outcome_kind, rejection):
        if self.b1_journal_path is None:
            return
        import hashlib
        import json
        import os
        from autoresearch.worker.local_worker import _parse_change_directive
        directive = _parse_change_directive(proposal.objective or '')
        row = {'schema': 'b1_proposal_journal/v1', 'campaign_id': status.campaign_id,
               'trial_id': f'{status.campaign_id}-trial-{status.budget_index:03d}',
               'budget_index': status.budget_index, 'revision_attempt': int(revision_attempt or 0),
               'summary': proposal.proposal_summary, 'rationale': proposal.proposal_rationale,
               'objective': proposal.objective, 'structured_edit': edit,
               'final_structured_edit': proposal.extra.get('structured_edit'),
               'directive': list(directive) if directive else None,
               'parse_failed': bool(proposal.extra.get('parse_failed')),
               'truncated': bool(proposal.extra['llm_call'].get('truncated')),
               'context_overflow': bool(proposal.extra['llm_call'].get('context_overflow')),
               'unencodable_reply': bool(proposal.extra['llm_call'].get('unencodable_reply')),
               'raw_proposal_sha256': proposal.extra.get('raw_proposal_sha256'),
               'raw_reply': raw,
               'raw_reply_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest() if isinstance(raw, str) else None,
               'check': outcome_kind, 'rejection': rejection}
        data = (json.dumps(row, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
        fd = os.open(self.b1_journal_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        try:
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError('short B1 proposal journal write')
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
