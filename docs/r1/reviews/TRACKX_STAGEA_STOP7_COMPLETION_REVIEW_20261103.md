# Track X Stage A — scoped review of the failed-start server-record finalization (v14, STOP 7)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-03 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`); local test runs as before.

**Verdict: `BLOCK`.** The v14 change finalizes the failed-start records' `stopped_utc`/`returncode`, which
satisfies the **runner's** `_write_lease_completion` check — but the **guardian's** `validate_completion`
also requires every `llama_server_*.json` record under the run root to carry a SAME-OFD `lease_inheritance`
proof (`kcmp_rc==0`, `kcmp_same_ofd is True`, `server_pid`, `server_start_ticks`). The three failed-start
records in the retained t7f6 evidence have `lease_inheritance: None` (the other 40 records have it), and the
`start()` inheritance verification is only performed after `/health` returns 200 — so the failed-start
records still cannot pass the guardian. With v14, the completion would move from the runner's
`STOP: server record incomplete for lease completion` to the guardian's
`STOP: server record lacks lease inheritance evidence`; the lease would still be retained and STOP-7 would
not be resolved. A secondary defect: the claimed `r1/tests/test_llama_server_instance.py` change is **not**
in the frozen v14 snapshot (`files/`/`SHA256SUMS` omit it; the live worktree has it uncommitted).

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v14` |
| `SHA256SUMS` SHA-256 | `84a5ce7e7cbd86498d2180f07cdea95f9d3fc4d5e1cc6a66bb12f9d5812eb6d6` — **verified**; 57/57 entries OK |
| Base | published real-shape OOM commit `14b9f79` + binding `9d2e213` |
| Delta vs v13 | `r1/scripts/llama_server_instance.py` **only** in the frozen snapshot (plus the already-published binding config); the claimed `r1/tests/test_llama_server_instance.py` change is absent from `files/` and `SHA256SUMS` (55 files; live worktree has it as an uncommitted modification: +25 lines, the new test) |
| Files | v14 `files/` == live worktree for the files it contains (0 mismatches), but the live test-file change is not frozen |

Delta hash: `llama_server_instance.py 53838bb6…`; the new test exists only in the live worktree
(`git diff HEAD` shows `r1/tests/test_llama_server_instance.py | 25 +`).

## 2. STOP-7 evidence and the exact incomplete records (verified read-only)

Attempt `r1_stagea_20261102_t7f6`: `batch_state.json` **COMPLETE**, 24 completed rows, no interruptions;
`stage_a_table.json` present; every replay offload record is `full:true, route:log_line` (as reported). The
runner then stopped at `_write_lease_completion`; the retained guardian `STOP.json`
(`completed_release:false`, `retry_permitted:false`, guardian 2911993, utc 2026-11-03T09:16:51Z). Recovery
`r1_stop7_shutdown_20261103T093541Z/` (09:35:41Z): `before` shows only the retained guardian 2911993 (the
server/worker had gone) with the FLOCK on inode 56251186, batch COMPLETE, the three incomplete records and the
lease hashes; `after` LOCK-FREE, lock size 0/inode 56251186/nlink 1, GPU 243 MiB/0 %. Current: guardian
absent, `/proc/locks` free, GPU idle, 22/22 models verified (0 failed), code clone `9d2e213`. The t7f6 batch
is not reused and is not Stage A evidence.

Scan of the 43 `llama_server_*.json` records under the t7f6 run root: **exactly 3 lack `stopped_utc`**, and
they are the failed-start qualification probes:
- `olmo31_32b/stage-a/32768/qualification/probe_…/llama_server_43967.json` — pid 3159959, start_ticks 277560414, `exited_early 1`, `returncode None`, `healthy_utc None`, `stopped_before_ready None`;
- `nemotron35_30b_a3b/stage-a/32768/qualification/probe_…/llama_server_37613.json` — pid 3178546, start_ticks 277730260, same shape;
- `nemotron35_30b_a3b/stage-a/16384/qualification/probe_…/llama_server_54245.json` — pid 3178650, start_ticks 277731913, same shape.

All three also have **`lease_inheritance: None`**; all 40 completed records have a `lease_inheritance` dict.
The `pid`/`start_ticks` are ints. The three correspond to the template-parser error and the 32k/16k KV OOM.

## 3. Why v14 does not resolve STOP-7

- Runner side: `_write_lease_completion` requires `pid`/`start_ticks` ints and a non-empty `stopped_utc` per
  record. The v14 finalization (`stopped_utc`, `returncode`, `stopped_before_ready`) would satisfy this
  check — the STOP at the runner would no longer occur.
- Guardian side: `validate_completion` walks **every** `llama_server_*.json` under the run root and requires
  each record to have `lease_inheritance` with `version`, `kcmp_rc == 0`, `kcmp_same_ofd is True`,
  `server_pid == pid`, an int `server_start_ticks > 0`, and a non-empty `stopped_utc`; it then requires the
  completion to cover exactly the record set (no survivor blind spot). The three failed-start records have
  `lease_inheritance: None` → the guardian raises
  `STOP: server record lacks lease inheritance evidence`. **The v14 delta does not add the inheritance**;
  the completion still cannot be released.
- Root cause of the missing inheritance: `LlamaServerInstance.start()` verifies
  `_verify_lease_inheritance(lease_fd, server_ticks)` only inside the `status == 200` (`/health`) branch and
  records `lease_inheritance`/the inherited `start_ticks` there. A server that exits before readiness never
  reaches that branch, so it has no inheritance proof. The v14 test does not cover this: the stub executable
  does not inherit a lease fd, and it asserts only `stopped_utc`/`returncode`/`exited_early`/
  `stopped_before_ready`/no `healthy_utc`/`alive()` false — not a valid `lease_inheritance` and not a
  `validate_completion` acceptance.
- Therefore question (b) is not satisfied: the record now passes the runner's `_write_lease_completion`
  fields, but **not** the guardian's `validate_completion` (which also requires the SAME-OFD inheritance), and
  the Lead's listed fields (pid/start_ticks/stopped_utc/digest) omit that requirement.

Question (a) is otherwise supported: the failed-start branch is the only producer of records lacking
`stopped_utc` (3/43; the rest have it), it never reached `healthy_utc`, so it served no request; the
completion validator is unchanged; a still-running preserved server is never touched (the preserved server is
on a STOP path, not a COMPLETE completion, and would itself keep the completion fail-closed). Question (c)
is supported: the delta only touches the pre-readiness branch; the `stop()` path, the completion validator,
the guardian and the offload/cache semantics are unchanged. But the fix is incomplete for (b).

## 4. Secondary defect: frozen snapshot omits the claimed test

The v14 snapshot's `files/` has 55 files and `SHA256SUMS` 57 entries; `r1/tests/test_llama_server_instance.py`
is absent from both. The live worktree has the test-file change (+25 lines, the new test) uncommitted, and
the claimed delta (`llama_server_instance.py` + `test_llama_server_instance.py`) is therefore not the frozen
delta. (The 3 pre-existing `test_llama_server_instance.py` macOS failures are unchanged by the delta — they
exist in base `9d2e213` and exercise `/proc`-only helpers; not regressions.)

## 5. What a correct v14b needs

1. Record a valid SAME-OFD `lease_inheritance` for the failed-start server **before** it can exit — e.g.,
   verify the inheritance immediately after `Popen` (the server has inherited the lease fd at exec; the
   ancestor→descendant kcmp/`/proc` FD dev/ino proof works while the process is alive; the template/OOM load
   takes seconds) and store it (with the inherited `server_start_ticks`) before the readiness wait; the
   failed-start branch then finalizes `stopped_utc`/`returncode` on a record that already carries the
   inheritance. Alternatively, a separately reviewed guardian-validator change that explicitly accepts a
   `stopped_before_ready` record without inheritance (the Lead currently says the validator is unchanged, so
   this would be a semantic change requiring its own review and tests).
2. Add a test that the failed-start record carries a valid `lease_inheritance` (with a lease fd inherited by
   the stub) and that a completion containing that record passes `_write_lease_completion` **and**
   `validate_completion` (including the coverage/no-survivor checks).
3. Freeze the corrected `test_llama_server_instance.py` in the snapshot/`SHA256SUMS` (and the README claim).
4. Then the conditions for `t7g7`: commit/rebind `paper_commit` (llama_server_instance.py is runtime-checked;
   the `14b9f79` binding would fail the launcher no-diff), clean TASL-7 checkout, rebuild the manifest,
   fresh real-lock preflight, `t7g7` in new dirs (22/22 models, continuous guardian lock, periodic
   GPU/server/lease/**progress** checks, 16k fallback only for the evidenced healthy-idle 32k OOM,
   template hits stay candidate rows), no STOP-batch reuse, B1/B2 STOP.

## 6. Tests

v14 relevant Mac CPU subset: **388 passed, 1 skipped** — matches. `test_llama_server_instance.py`: 16 passed,
3 failed (the 3 pre-existing macOS `/proc` failures, unchanged in base `9d2e213`; the new test passes). But
the new test does not exercise the missing `lease_inheritance`/guardian validation (see §3/§5).

## 7. NOT CHECKABLE in this review

- `t7g7` behaviour (not run), and whether a corrected inheritance capture succeeds for very fast-failing
  servers (the design must remain fail-closed if the proof cannot be captured).
- The future commit/binding/manifest bytes; host-global/same-UID; B1/B2 on TASL-7 (STOP).

## 8. Final verdict

**`BLOCK`.** The v14 finalization is necessary but not sufficient: the three failed-start records also lack
the `lease_inheritance` SAME-OFD proof that the guardian's `validate_completion` requires for every record
under the run root, so the completion would still be rejected (now at the guardian) and the lease retained.
The fix must record the inheritance for the failed-start server before readiness (or a separately reviewed
validator change), be tested through the guardian validation, and be included in a frozen snapshot with the
test file. The STOP-7 evidence/recovery itself is verified and the t7f6 batch is not reused.
