# Track X Stage A — re-review of the failed-start server-record finalization (v14b, STOP 7)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-03 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`); local test runs as before.

**Verdict: `ACCEPT` (with conditions).** The v14b BLOCK is resolved: the SAME-OFD `lease_inheritance` proof is
now captured for a server **before** the readiness loop (immediately after the start record is saved, while the
child is alive and has inherited the lease FD), so a failed-start record can carry both the proof and the
finalized stop; the failed-start record then passes the runner's `_write_lease_completion` **and** the
guardian's `validate_completion`. If the proof genuinely fails while the child is alive the start still STOPs
(verified directly); if the child is already gone the capture is recorded as failed, no proof is invented, and
the guardian keeps rejecting the record (fail-closed). The snapshot defect is fixed (the test file is now in
`files/`/`SHA256SUMS`).

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v14b` |
| `SHA256SUMS` SHA-256 | `9724933fd86a83cb90ae246731904d44915ee401291a1ecb123dfbc26c5c1cec` — **verified**; 58/58 entries OK (56 files + `tracked.patch` + `README.md`) |
| Base | published real-shape OOM commit `14b9f79` + binding `9d2e213` |
| Delta vs v13 | `r1/scripts/llama_server_instance.py`; `r1/tests/test_llama_server_instance.py` (**now in `files/`/`SHA256SUMS`** — the v14 defect), `r1/tests/test_trackx_lease_guardian.py`, `r1/tests/test_exam_qualify_guard.py`; the v13→v14b config difference is the already-published `14b9f79` binding |
| Files | v14b `files/` == live worktree (0 mismatches); live HEAD `9d2e213` with 4 modified tracked (the delta uncommitted) |

Delta hashes: `llama_server_instance.py b697fc44…`, `test_llama_server_instance.py 2ceab93e…`,
`test_trackx_lease_guardian.py cd124f02…`, `test_exam_qualify_guard.py e3f5c7c2…`.

## 2. (a) Pre-readiness capture — real proof, genuine failure still STOPs

- `LlamaServerInstance.start()` now, immediately after the start record is saved and **before** the readiness
  loop, calls `self._verify_lease_inheritance(lease_fd, server_ticks)` — the **same reviewed verifier**
  (`cache_runtime.verify_server_lease_inheritance`; ancestor→descendant `kcmp(KCMP_FILE)` + `/proc` FD
  dev/ino + pid/start-ticks/parent identity). No new proof path, no direction/FD-identity change; only the
  timing (child barely alive after fork/exec, the FD already inherited) — so a false SAME-OFD proof is not
  created.
- On success it stores `lease_inheritance` and updates the record's `start_ticks` from the proof
  (`server_start_ticks`); the health-200 branch still re-verifies (unchanged).
- On failure it records `lease_inheritance_capture: {captured:false, utc, error}` and, **if the child is still
  alive, re-raises** (a genuine STOP). I verified this directly: a simulated verifier failure while the stub
  child was alive raised, and the record carried the capture-failure with no `lease_inheritance`/`stopped_utc`
  — no silent pass.
- If the child is already gone, it does not fabricate a proof: it falls through to the readiness loop, the
  "exited before readiness" branch finalizes `stopped_utc`/`returncode`/`stopped_before_ready`, and the record
  has no `lease_inheritance` → the guardian rejects it (fail-closed; the same retained-lease STOP behaviour,
  now with the diagnostic capture).

## 3. (b) Both completion checks accept the failed-start record; coverage unchanged

- New test `test_failed_start_records_the_lease_inheritance_proof`: stub exits before healthy; synthetic
  verifier returns a proof; the record has `lease_inheritance` (`kcmp_same_ofd:true`, `server_pid == pid`),
  `start_ticks` from the proof (777), non-empty `stopped_utc`, `returncode == 1`, `stopped_before_ready`,
  and the verifier was called with the inherited FD.
- `test_completion_accepts_a_failed_start_record_with_lease_inheritance`: guardian `validate_completion`
  accepts the failed-start shape (no `healthy_utc`) when the inheritance row is present.
  `test_completion_rejects_a_failed_start_record_without_inheritance`: the same shape without it is rejected
  with `lacks lease inheritance evidence` — the fail-closed direction is preserved.
- `test_lease_completion_accepts_a_failed_start_record`: the runner's `_write_lease_completion` writes the
  completion for the finalized record (pid/start_ticks/stopped_utc/hash, `runner_start_ticks` from the fake
  clock). The guardian's coverage/no-survivor checks are unchanged and the existing tests still pass.
- The 391/1 subset passes (including the new guardian/runner tests); `test_llama_server_instance.py` is
  17 passed + the **3 pre-existing macOS `/proc`-only failures** (same three in base `9d2e213`;
  `test_start_records_argv_cmdline_pins_and_identity`, `test_orphan_is_stopped_only_when_provably_ours`,
  `test_a_matching_process_of_another_user_is_never_signalled`) — not regressions.

## 4. (c) No other semantics changed

The delta only adds the pre-readiness capture and the failed-start finalization (v14) plus tests. `stop()`,
`_write_lease_completion`, `validate_completion`, the guardian, the preserved-server semantics and the
offload/cache/lease paths are untouched. The pre-readiness capture runs once per lease-FD server (the healthy
path re-verifies at health-200); the failed-start branch is still only the pre-readiness exit path; a
still-running preserved server is never touched (it would keep the completion fail-closed).

## 5. (d) Snapshot and README

- The v14 defect is corrected: `r1/tests/test_llama_server_instance.py` is now in `files/` and the
  `SHA256SUMS` (58 entries / 56 files); `files/` == live worktree; the README records the v14b fix and the
  pre-existing macOS failures. The README's "Delta vs v13" lists the four reviewed files; the v13→v14b
  config difference is only the already-published `14b9f79` binding (minor: the list could name it, no code
  effect).
- The 3 pre-existing `test_llama_server_instance.py` failures are unchanged (verified against base `9d2e213`).

## 6. STOP-7 evidence and recovery (re-verified read-only)

t7f6 `batch_state` COMPLETE, 24 rows, `stage_a_table.json` present; the 3 failed-start records (olmo template
error, nemotron 32k/16k KV OOM) are the only records lacking `stopped_utc`, and they also lack
`lease_inheritance` — the v14b evidence of the defect. Recovery `r1_stop7_shutdown_20261103T093541Z/` unchanged
(only the retained guardian 2911993 ended; LOCK-FREE, inode 56251186/size 0/nlink 1, GPU idle). Current: lock
free, guardian absent, GPU idle, 22/22 models verified (0 failed), code `9d2e213`. The t7f6 batch is not
reused and is not Stage A evidence; the t7g7 attempt is separate.

## 7. (e) Conditions for `t7g7`

1. Commit the v14b delta; **rebind `paper_commit` to the v14b code commit** (`r1/scripts/llama_server_instance.py`
   is runtime-checked; the `14b9f79` binding would fail the launcher's ancestor/no-diff); clean TASL-7
   checkout; rebuild the guardian manifest (M1/M2/M3).
2. Fresh TASL-7 real-lock preflight; then `t7g7` in new out/evidence dirs, 22/22 models, continuous guardian
   lock, periodic GPU/server/lease/**progress** checks (the 12 h-deadline risk note applies), the 16k fallback
   only for the evidenced healthy-idle 32k OOM, template-class hits stay candidate rows, B1/B2 remain STOP,
   no STOP-batch reuse.
3. The completion is expected to pass for the failed-start servers (inheritance captured before exit). If a
   child is gone before the capture, the record has no proof, the guardian rejects the completion and the
   lease stays retained — this is the intended fail-closed residual; recover only under the standing
   authorization.
4. The alternative guardian-validator change is **not** needed/preferred: the v14b route preserves the
   SAME-OFD proof for failed-start records and leaves the validator unchanged, which is the stronger,
   fail-closed design.

## 8. NOT CHECKABLE in this review

- The `t7g7` behaviour (not run), including whether its failed-start servers all exit after the immediate
  capture (the same verifier is exercised by the preflight/run; the synthetic unit test covers the wiring).
- The very-fast-exit child case (fail-closed by design; the completion stops).
- The future commit/binding/manifest bytes; host-global/same-UID; B1/B2 on TASL-7 (STOP).

## 9. Final verdict

**`ACCEPT`** of the v14b failed-start record finalization, with the §7 conditions. The pre-readiness capture
uses the same reviewed SAME-OFD verifier (no false-proof path), a genuine failure while the child is alive
still STOPs (verified), a gone child yields no invented proof (fail-closed), and the failed-start record now
passes both the runner's `_write_lease_completion` and the guardian's `validate_completion` (tests + coverage
unchanged). The snapshot/test-file defect is fixed, the 391/1 subset passes with the 3 pre-existing macOS
failures unchanged, and the STOP-7 evidence/recovery remains consistent.
