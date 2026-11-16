# Pinned-server full-context prefill boundary

26 October 2026. Source-only preflight; no real Stage A request has been sent.

The runbook Phase 3 step 1 calls for a 32,768-token prefill at context 32,768 (and fallback context 16,384). The accepted runner currently requests exactly `instance.ctx_size` prompt tokens with `n_predict: 0`.

Pinned llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab` rejects this request before evaluation:

- `tools/server/server-task.h`, `server_task::need_embd` (around line 220): ordinary completion tasks return false.
- `tools/server/server-context.cpp`, `server_slot::can_split` (around line 447): tasks not needing embeddings can split.
- `tools/server/server-context.cpp`, prompt admission (around line 3676): the splittable path rejects `slot.task->n_tokens() >= slot.n_ctx`, returning an available-context error. There is no exception for `n_predict: 0` before this check.

This is an API reserve, not an observed model fit failure. Sending the current request would systematically misclassify the endpoint rejection as offload failure at both contexts.

Concrete proposed author resolution: retain server context/cache allocation 32,768, fit estimates at 32,768, all offload settings and margins; prefill the maximum legal 32,767 tokens with an explicitly bounded one-token generation. At the 16,384 fallback use 16,383 prefill tokens plus one generated token. Record declared context, actual prefill count and the one-token native API reserve explicitly in every result. The fit-estimate threshold and declared context would not change. A completion request with `n_predict: 0` is not a verified no-generation route in this pin: `server_task::need_sampling` remains true for completion; `server-context.cpp` around lines 4446–4470 samples after the prompt, while the budget stop around line 2037 applies after at least one generated token. Therefore the proposed probe requests `n_predict: 1` explicitly and records its observed generated-token count rather than promising zero. No lower prefill count has been adopted or used; author approval is required before changing the runbook's literal prompt length.

**Author decision, 26 October:** “Approve the one-slot reserve probe.” PLAN R1-EXAM-PREFILL-RESERVE adopts the concrete proposal above. Declared context and fit estimates remain unchanged. Implementation and independent checks precede real use; STOP 2 still requires all artifact hashes and independent acceptance.
