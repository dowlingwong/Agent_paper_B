# Track X Stage A — scoped review of the bounded GPU-quiescence wait (v15, STOP 8)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-03 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`); local test runs as before.

**Verdict: `ACCEPT` (with conditions).** The v15 change replaces the single instantaneous pre-qualification
GPU check with a bounded quiescence wait (`await_idle_gpu`) that absorbs the CUDA teardown of a just-exited
server. The acceptance criterion is **unchanged and fail-closed** (final observation: no compute apps,
≥1024 MiB free, ≤5 % utilisation), an unknown census (`apps is None`) still STOPs immediately, a persistent
foreign workload still STOPs after the bounded deadline, the last observation is diagnostic only, and only
the one pre-qualification call site changed. The STOP-8 evidence is consistent and the STOP-7 fix is
validated on the real failed start.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v15` |
| `SHA256SUMS` SHA-256 | `23689415a697778b8218caccc5d5b3d115ad211d4682a11ef16e3be54cda0477` — **verified**; 58/58 entries OK (56 files + `tracked.patch` + `README.md`) |
| Base | published v14b commit `6f1b90b` + binding `70a7a6f` |
| Delta vs v14b | `r1/scripts/exam_runner.py` and `r1/tests/test_exam_qualify_guard.py` only; the v14b→v15 config difference is the already-published `6f1b90b` binding |
| Files | v15 `files/` == live worktree (0 mismatches); live HEAD `70a7a6f` with 2 modified tracked (the delta uncommitted) |

Delta hashes: `exam_runner.py eeec5e9a…`, `test_exam_qualify_guard.py 8d6fdac8…`.

## 2. The change — bounded wait, unchanged fail-closed criterion

- `await_idle_gpu(cfg, *, attempts=12, interval=5.0, sleep=time.sleep)`: up to 12 observations 5 s apart
  (≤55 s of waiting; 11 intervals). Each observation reads `gpu_sample(cfg)` and
  `lsi.gpu_compute_apps()`; the acceptance condition is exactly the pre-existing one — `apps == []`,
  `sample['free_mib'] >= 1024`, `sample['utilisation_percent'] <= 5`.
- `apps is None` → immediate `PreparationStop: STOP: GPU census unavailable for independent qualification`
  (no wait: waiting cannot make an unobservable GPU observable).
- After the bounded attempts without acceptance → `PreparationStop: STOP: GPU not available for independent
  qualification after {attempts} observations: {last}`; a persistent foreign app therefore still STOPs; the
  waits occur only between observations (no extra sleep after the final one).
- The single call site changed: in `_stage_a_cooperative`, the old
  `sample=…; apps=…; if apps is None or apps or …: raise PreparationStop('STOP: GPU not available for
  independent qualification')` is replaced by `await_idle_gpu(runner.cfg)`. It is the same pre-qualification
  check that runs for every `ctx` (32k and the 16k retry) inside the `if not dryrun` branch; the wait is not
  restricted to the 16k retry, but it is the only call site and the acceptance is the same. The function
  returns `(apps, sample)` on acceptance; the caller ignores the return (as the old check did).

## 3. (a) A foreign/unknown state cannot be waited through

The final acceptance observation is the unchanged criterion; a persistent foreign compute app never satisfies
`apps == []`, an unknown census STOPs immediately, and the loop is bounded. The only timing effect is to allow
a transiently visible GPU state to settle; a transient foreign workload that *exits* during the wait leaves an
idle GPU that satisfies the same final criterion — the wait does not lower the bar, and the runtime census
(`run_job`/server start/qualification) still observes the GPU afterwards. `apps is None` is never accepted.
There is no new call site and no swallowed exception: the function raises `PreparationStop` in all
non-acceptance paths.

## 4. (b) Only the pre-qualification check changed

The diff is confined to the new function and the one call-site replacement. Server start, `/health`/readiness,
the startup GPU census (`run_job`), the lease re-verification, the qualification (`run_fresh_qualification`),
the offload/cache/lease checks and the other `gpu_sample`/`gpu_compute_apps` sites (probe, `run_job`) are
unchanged. The call site is the pre-qualification GPU check before `run_fresh_qualification`; the 32k and 16k
paths share it, and the STOP-8 scenario (16k retry right after the 32k OOM teardown) is exactly what the wait
absorbs.

## 5. (c) The last observation is diagnostic only

The final observation is included in the `PreparationStop` message for diagnosis, and the function raises —
it never returns the last observation as an acceptance. The caller does not read the message as success. The
tests assert the raise (`after 3 observations` / `GPU census unavailable`), not an acceptance.

## 6. Tests

v15 relevant Mac CPU subset: **394 passed, 1 skipped** — matches the README (the message's "393" is a typo;
the snapshot/subset is 394/1 including the 3 new tests). The new tests are genuine:
`test_await_idle_gpu_retries_a_transient_teardown` (busy 100/99 → busy 200/40 → idle 20000/0; returns the idle
sample after two waits); `test_await_idle_gpu_still_stops_for_a_foreign_app` (persistent foreign app; raises
`after 3 observations`; waits only between attempts, len(slept)==2);
`test_await_idle_gpu_stops_immediately_when_the_census_is_unknown` (apps None; raises
`GPU census unavailable`; slept==[]). The pre-existing `test_llama_server_instance.py` 3 macOS `/proc`-only
failures remain unchanged (not in this subset; verified previously against base `9d2e213`).

## 7. STOP-8 evidence and recovery (verified read-only)

Attempt `r1_stagea_20261103_t7g7`: `batch_state` STOPPED with `stop_reason`
`PreparationStop: STOP: GPU not available for independent qualification`, **11 completed rows**; the
`nemotron35_30b_a3b/stage-a/32768/stage_a.json` row is the 32k OOM mechanical-failure row
(`passed:false, failure_classes:['offload'], prompts:0`); the retained 32k failed-start probe record has
`stopped_utc`, `returncode 1` and a `lease_inheritance` SAME-OFD proof (`kcmp_same_ofd: true`) — the STOP-7
fix validated on this real failed start too. The 32k qualification `runner.log` ends
`STOP: RuntimeError: STOP: dedicated llama-server exited during start (rc=1)` (the evidenced OOM probe); the
16k retry then hit the single instantaneous pre-qualification check — the STOP-8 defect. Guardian
`STOP.json` 3589647 `completed_release:false`, `retry_permitted:false`, utc 17:27:20Z. Recovery
`r1_stop8_shutdown_20261103T202105Z/`: only the retained guardian 3589647 ended; `after` LOCK-FREE
(inode 56251186, size 0, nlink 1), GPU 243 MiB/0 %. Current: guardian absent, `/proc/locks` free, GPU idle,
22/22 models verified (0 failed), code clone `70a7a6f`. The t7g7 batch is not reused and is not Stage A
evidence.

## 8. (d) Conditions for `t7h8`

1. Commit the v15 delta; **rebind `paper_commit` to the v15 code commit** (`r1/scripts/exam_runner.py` is
   runtime-checked; the `6f1b90b` binding would fail the launcher's ancestor/no-diff); clean TASL-7
   checkout; rebuild the guardian manifest (M1/M2/M3).
2. Fresh TASL-7 real-lock preflight; then `t7h8` in new out/evidence dirs, 22/22 models, continuous guardian
   lock, periodic GPU/server/lease/**progress** checks (the 12 h-deadline risk note applies), the 16k
   fallback only for the evidenced healthy-idle 32k OOM (the wait now lets the teardown settle), template-class
   hits stay candidate rows, B1/B2 remain STOP, no STOP-batch reuse.
3. The bounded wait is ≤55 s; if the GPU is genuinely busy the pre-qualification STOPs as before (no
   indefinite wait); an unknown census STOPs immediately.
4. Keep the STOP-8 evidence untouched; the t7g7 rows are not reused.

## 9. NOT CHECKABLE in this review

- The `t7h8` behaviour (not run), including the real TASL-7 teardown timing at the 16k boundary (the preflight/
  run exercises the same `await_idle_gpu`).
- Whether a transient foreign workload with a brief idle gap could satisfy the final observation (the
  acceptance criterion is the pre-existing one; the wait is bounded; any such risk is not new to the criterion).
- The future commit/binding/manifest bytes; host-global/same-UID; B1/B2 on TASL-7 (STOP).

## 10. Final verdict

**`ACCEPT`** of the v15 bounded GPU-quiescence wait, with the §8 conditions. It is a bounded, single-call-site
wait with the unchanged fail-closed acceptance criterion; `apps is None` and persistent foreign workloads
still STOP; the last observation is diagnostic only; only the pre-qualification check changed; and the tests,
the 394/1 subset and the STOP-8 evidence (including the validated STOP-7 failed-start record) support it.
