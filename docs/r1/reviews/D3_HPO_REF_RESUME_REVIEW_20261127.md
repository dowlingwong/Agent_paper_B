# D.3 HPO-REF production adapter review

Task `local/20261127-15`. Tier E. Independent review by a separate Codex agent with no implementation edits.
Published base `91cfd48a67f8d62d4e20826976cbdbdbcfcaf505`. This update resumes the former candidate `666320c9`.

## Initial review

**CHANGES REQUIRED** at `df8d9525447cbb3c8ba68b2d4defd724421abbc4`.

- B1. Both pinned OpenML climate and sonar node trees contain tracked cache placeholders. The G1 staging helper ignored the supplied populated cache when that directory existed. A synthetic cache marker failed to reach the worker tree.
- B2. A real LocalWorker running an unknown synthetic runtime failure returned an ordinary failed charge. That would continue a campaign in a case that revision 4 §10 stops. A host-killed subprocess would also be charged instead of invalidating the attempt.
- Separately, the audit uses the declared deepthought §7.2 runtime and shared G6 audit cache. The SMAC3 numerical environment is distinct.
- The initial focused suite passed 28 tests with the real backend. For seven nodes × 18 instance seeds, the independently exercised real SMAC3 initial designs contained five distinct configurations including the exact G1 default. All 630 rendered configurations round-tripped through the typed parser and the start hashes matched G1's worker file hash.

## Independent re-check

**ACCEPTED** at `ff7961b4eafad116aa83865a4569362c107703a2`.

- B1 is closed. Both climate and sonar receive the approved synthetic cache despite tracked placeholders. The originals are retained. G6 uses the same cache hash, verifies contents and receives explicit audit worker runtime metadata.
- B2 is closed. A real LocalWorker with synthetic children raises a STOP on an unadmitted runtime error and signals infrastructure failure on exit 137. The CPU run-budget path remains a proposal charge. The full attempt is retained before a retry receives fresh worker, sampler and optimizer directories.
- The independent focused subset passed **95/95** with the real pinned SMAC3 backend and harness `9bb416805175149eb87b71f28d77530572aa4bce`. `git diff --check` passed. The independently exercised initial design and rendered hash/type checks from the first round remain applicable.
- The campaign-level APIs are used by the signed-stage launcher. The launcher applies the declared worker environment and host admission, the 12.99% pooled failure STOP at stage assembly and the §7.2 audit placement and co-tenancy conditions.

The reviews used synthetic fixtures only. No live host, worker training job, label or evaluation partition was used.
