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

    def invoke(self, messages, *args, **kwargs):
        self.calls += 1
        self.outcome = None
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
        self.outcome = {'finish_reason': finish, 'truncated': False}
        return response


class B1CappedLangGraphManager(LangGraphManager):
    """The pinned harness proposer, with the completion cap and the truncation rule of this module."""

    def __init__(self, *args, max_completion_tokens: int = B1_MAX_COMPLETION_TOKENS, **kwargs):
        if type(max_completion_tokens) is not int or max_completion_tokens < 1:
            raise ValueError('max_completion_tokens must be a positive int')
        _truncation_errors()   # fail at construction, not mid-campaign, if the SDK lacks the error classes
        super().__init__(*args, **kwargs)
        self.b1_max_completion_tokens = max_completion_tokens
        self._b1_guards: list[TruncationGuard] = []

    def _resolve_llm(self, seed: int | None = None):
        model = super()._resolve_llm(seed=seed)
        if self._injected_llm is not None:
            raise RuntimeError('STOP: the B1 capped proposer does not take an injected model')
        guard = TruncationGuard(model.model_copy(update={'max_tokens': self.b1_max_completion_tokens}),
                                self.b1_max_completion_tokens)
        self._b1_guards.append(guard)
        return guard

    def propose_next_trial(self, *args, **kwargs):
        self._b1_guards = []
        proposal = super().propose_next_trial(*args, **kwargs)
        used = [g for g in self._b1_guards if g.calls]
        call = (proposal.extra or {}).get('llm_call')
        if len(used) != 1 or used[0].calls != 1 or used[0].outcome is None or not isinstance(call, dict):
            raise RuntimeError('STOP: B1 proposer call record is not exactly one guarded call')
        outcome = used[0].outcome
        call['max_completion_tokens'] = self.b1_max_completion_tokens
        call.update(outcome)
        if outcome['truncated']:
            call['truncation_policy'] = TRUNCATION_POLICY
            if call.get('parse_ok') is not False or proposal.extra.get('parse_failed') is not True \
                    or proposal.extra.get('structured_edit'):
                raise RuntimeError('STOP: a truncated B1 proposal was not rejected by the harness validator')
        return proposal
