# Independent review: Track X D3 engineering snapshot v9 — 31 October 2026

**BLOCK.** The 38 snapshot files passed SHA-256 verification; `SHA256SUMS` SHA-256 `ffb75219c2861736767cfb255e5750c0c360f0e9cc9e90db91f79aaef0065c81`. Production entry, cold-start and GPU lease continuity remain unconditionally stopped. No model or GPU was used.

Independent synthetic checks reproduced three issues: true/false replay request matching ignores additional parameters such as `top_p` and thinking settings; six non-generation records can all use `/tokenize` while the validator passes, so five fixed `/apply-template` calls are not established; and an old RUNNING batch can enter stale-lock recovery after a crash before STOPPED is recorded. None authorizes continuation of an old batch. The false and non-generation recorders did propagate `D3EvidenceStop` in independent CPU fake tests of initial journal ENOSPC and repeated ENOSPC while recording STOP. The full pytest suite was not independently rerun.

Cold true-first, isolation, Linux behavior, deployed binary semantics and GPU flock continuity remain unproven. The snapshot is retained in the local operations archive and is not authorized for execution.
