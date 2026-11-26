# Independent review: Track X D3 engineering snapshot v7 — 31 October 2026

**BLOCK.** The 35 snapshot files passed SHA-256 verification; `SHA256SUMS` SHA-256 is `daf3be942429c278f8c51ffe9f7d9826667cfc5c88132e10afe220355e7c6fae`. Production entry and cold-service proof remain unconditionally stopped. No real model or GPU was used. The reviewer did not independently rerun the full suite because pytest was absent.

Two STOP-propagation defects were reproduced with isolated synthetic tests:

1. An existing `qualification.json` can cause `exam_runner.py` to swallow an arbitrary qualification `RuntimeError`, including a GPU census or margin STOP, and continue. Qualification evidence must bind to the present attempt and infrastructure STOP must propagate.
2. An incomplete GPU sample such as `telemetry=[{}]` is converted from `KeyError: free_mib` to a normal candidate offload failure rather than a STOP.

Additional deployment blockers: the `/proc/<pid>/exe` census stops on any readlink error, including a simulated disappearing or kernel PID; real Linux behavior and visibility are not established. Preserving a service plus a marker or `runner.lock` does not establish that the outer GPU `flock` remains held after the supervisor exits. Cold true-first, server exclusivity and identity, deployed binary response semantics, Linux end-to-end behavior and lease continuity remain unproven. The reviewed snapshot is retained under the local operations archive; it is not authorized to run.
