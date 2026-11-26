# Independent B1 batch verifier audit — 5 November 2026

AI-assisted (Codex). Target `mac-b1-overnight-20261105` at `c03d76ff1f7b23b5eebedcc868158b81c9ccc12d`, with executable code pin `1dd6e8877beb61238b66d34474abf7b474261aff`. **Verdict: NOT ACCEPTED for complete sealed-path refusal**, one actionable finding. The audit is scoped to local code inspection and a synthetic path counterexample, not real B1 execution, model, server, GPU, experiment or independent verification of the full batch.

## Finding — case-insensitive sealed-path alias

`r1/exam/b1_batch.py:25–30` checks each lexical and resolved path component against the exact case-sensitive string `r1_sealed`. On this Mac's case-insensitive filesystem, a synthetic temporary directory named `r1_sealed` and its synthetic `fake.json` were also accessible as `R1_SEALED/fake.json` (`Path.exists() == True`). `Path.resolve()` retained the uppercase spelling and `refuse_sealed()` returned normally. Thus `b1_summary_verified`, which uses this guard before reading a batch, can accept this alias rather than refusing it. No actual sealed file was opened. This is the same type of filesystem alias recently corrected in M11's separate `r1/c3/analysis_guard.py`; that correction does not cover this B1-specific copy.

**Unblock:** case-fold both lexical and resolved path components when rejecting `r1_sealed`, add synthetic uppercase and resolved-path tests, and have this reviewer recheck the exact fix. **Owner:** Mac-local implementer, then independent reviewer. **Effort:** a bounded local code/test change and review. This is separate from author/anchor/test/site STOPs and does not justify authorizing a run.

## Scope and limits

I compared the verifier's candidate ordering, Stage A union, root grid, source and budget bindings, replayed diagnostics and per-candidate D28 with the current `exam_runner.py`, `campaign.py`, pinned config, registry and `MAC_B1_BATCH_VERIFIER_REVIEW_20261105.md`. No additional concrete production-shape mismatch is asserted by this bounded read-only inspection. It does not establish that real model outputs, host state, complete-batch fixtures or future changes pass; prior scoped test limitations and the full-readiness NOT ACCEPTED verdict remain.

## Recheck — case-insensitive sealed paths

**ACCEPTED for the bounded sealed-path correction**, target `bab4b8cb0569b94c23f2828f1a8cdb5ce3782dcf`. The only verifier change applies `casefold()` to every lexical and resolved component before comparison. An independent synthetic reproduction on the same case-insensitive Mac confirmed the uppercase alias exists and is now refused. The four new tests cover lowercase, two case variants and a symlink to a case-variant directory; the complete synthetic `test_exam_b1_batch_verify.py` suite returned **36 passed in 4.36 s** against the local pinned harness. The tests neither use a model nor connect to a server.

This acceptance does not establish a real production batch, Linux-host behavior, a final code pin, author approval, the pilot interval, historical worker determinism or B1 readiness. The implementation and draft must be repinned and independently reviewed before any handoff.
