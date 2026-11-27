# Independent tier-E re-review — local/20261127-28

**ACCEPTED** at `fc95186bc7071e7d62622aacea657313ea7145cd`, against base `35c42b81880a444c55d25d604007366c7533ec82`. The first review of `cce0413e86a62e66716a58c02447efedead51e2f` requested changes to CUDA ordinal handling and verification, malformed and missing occupancy records, the canonical Ada lock path, and direct-launch UUID validation.

The revised lease resolves inherited numeric CUDA masks through CUDA in a fresh process, validates the selected physical GPU, and verifies the bound UUID before model or kernel execution. It acquires `gpu<index>.lock` before sampling that UUID’s occupancy. The start and end records contain only the count and aggregate memory of other compute processes. Invalid samples fail closed. An end-sample failure prevents success and preserves an existing job exception.

Standalone Ada E0 uses the reviewed host lock directory. The smoke handoff must pass `--lock /data1/zli538/r1_locks/gpu0.lock` so both commands resolve the same per-index lock. The staged P.4 direct path retains its job-local lock and requires the launcher’s full GPU UUID. Existing one-card and HTCondor slot paths remain compatible. Use the native `nvidia-smi` for Ada P5 because the historical H200 shim accepts only the older query format.

The focused lease, trainer, E0 and P.4 direct fixtures returned **75 passed, 1 skipped**. `git diff --check` passed. This review used CPU fixtures and published engineering records. Live Ada smoke and E0 acceptance remain with `compute/20261127-29`.
