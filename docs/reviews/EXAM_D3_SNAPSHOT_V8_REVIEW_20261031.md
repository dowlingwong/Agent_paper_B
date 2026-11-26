# Independent review: Track X D3 engineering snapshot v8 — 31 October 2026

**BLOCK.** The 37 snapshot files passed SHA-256 verification; `SHA256SUMS` SHA-256 `fcb78fa5908e9de39551f815fdead24c78e2f408b93b7086eb8f12b06104ccfc`. Production entry, cold-start and GPU lease continuity remain unconditionally stopped. The reviewer compiled 33 Python files in memory, checked qualification error propagation and malformed/low VRAM samples using CPU fakes, and did not independently run the full pytest suite. No model or GPU was used.

Two defects require repair and re-review:

1. `cache_order.py` does not bind all primary false requests to the frozen 50 prompts, seeds, modes and repeats; a synthetic set of 201 `/completion` bodies with only `cache_prompt=false` passes. True request checks also omit exact model, temperature, length and schema content. This validator does not establish matched settings or coverage.
2. Journal write failure can lead the false, non-generation or observer error path to attempt another write; repeated ENOSPC leaks a plain `OSError` that broad exception handlers may classify as a model failure rather than STOP. CPU fake reproduces this.

A separate read-only portal census, outside this code review, found 588 visible process executable links returning EACCES in one instantaneous scan, including 202 non-kernel live processes. Thus the current fail-closed `/proc` guard stops immediately; the scan does not establish host-wide visibility. A user+network namespace capability probe succeeded, but GPU, server, lease compatibility and whether namespace-scoped single-server evidence meets the author requirement remain unresolved. Passwordless sudo was unavailable.

Cold true-first, single-server exclusivity, host-wide visibility, `flock` continuity, Linux end-to-end execution and actual binary response fields remain unproven; this snapshot is not authorized for execution.
