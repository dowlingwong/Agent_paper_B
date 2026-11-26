# Independent review: B.2 recovered dirfd candidate

Reviewed `7df307b..f9af3a5` and the follow-up `f9af3a5..f98e315` in `/private/tmp/paper-b-b2-repair-20261031`. This is an offline review; no mount, replay, real task, real cache, or old failed fixture was executed or touched. B.2 remains STOP.

## Initial review: BLOCK for protection against accidental execution

At `f9af3a5`, the working fixture's direct CLI stopped unconditionally, but the archived historical fixture still called `main()`, the working `main()` remained import-callable, and the seccomp candidate exposed a command executor. The mount module's import-callable `bind_readonly_fd_pinned` accepted a caller-provided namespace-attestation dictionary and could reach a raw mount syscall. A claimed current namespace string alone did not establish isolation from the host namespace. Therefore the direct CLI STOP did not close all execution paths.

The recovered fixture source's Git blob `5afae90e29b5f7dad163fc6322acd86ab970db63` matches the `5afae90` prefix in the historical independent review's `git show 00d35d3` diff, retained at `/Users/wongdowling/.codex/sessions/2026/10/28/rollout-2026-10-28T16-37-06-01a18328-6b41-7d23-9c27-a3f3ba903945.jsonl:1161`. This supports recovery of that source blob only, not the historical commit object or entire tree. Other reconstructed files have no located historical final blob IDs.

## Follow-up review of f98e315: ACCEPT limited to preservation and closure of identified entry points

The former fixture and seccomp modules are absent as importable Python modules; the former source files are retained as Base64 data. The active mount module's `_raw_mount` and `bind_readonly_fd_pinned` unconditionally raise STOP before I/O, and the active module no longer contains the mount syscall implementation. Direct offline calls to both functions confirmed the STOP. This resolves the specific accidental-execution exposure identified above; decoding and deliberately executing preserved data is outside that protection.

Independently decoded all 11 manifest entries in memory and compared each byte-for-byte with its corresponding `f9af3a5` Git object. All matched, including each recorded decoded byte length, SHA-256 and Git blob SHA-1. The historical fixture remains blob `5afae90e29b5f7dad163fc6322acd86ab970db63`.

The local Python environment lacked pytest, so pytest was not independently rerun in this review. Previously reported Mac synthetic tests used mocks and skipped the Linux-only mount test. This review does not verify Linux mount, rename, teardown, namespace or real sklearn procfd behavior, source-mutation races, B.1 replay integration, numerical equivalence, or authorization to execute B.2.
