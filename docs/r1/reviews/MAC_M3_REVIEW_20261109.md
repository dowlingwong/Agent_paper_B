# Independent review of the M3 overnight unit (mac-m3-20261109), 9–10 Nov 2026

Freshly spawned independent reviewer (Claude subagent; did not write the unit). Status: round 1 changes requested; round 2 **accepted** at `4df14fd6`. Rounds copied verbatim below.

---

## Round 1

# Independent review — M3 overnight unit, round 1

Reviewer: fresh independent reviewer (Claude), cloud container (Linux 6.18.44 x86-64, Python 3.13.18, sklearn 1.9.1). Read-only on `/tmp/pb/wt/m3`; scratch under `/tmp/pb/scratch_rev_m3/`, scratch cgroup `/sys/fs/cgroup/unified/pb-rev-m3`. No SSH, no host, no push, no real OpenML cache, label table or seed 7001–7010 file read. Upstream `kernel/seccomp.c` (and `kernel/exit.c` v6.18) were fetched read-only from raw.githubusercontent.com to check the kernel reading.

Unit: `mac-m3-20261109`, `478d1d32..25a2f301` (b6d77f73, e78b81c5, 89cc6ae5, 25a2f301).

## What was verified (no finding)

- **Base/merges.** Every `origin/mac-m3-*` branch is an ancestor of `478d1d32`; the five merges are needed (HUP-source review, cache-copy and case-binding components, the two other 8 Nov reviews). `origin/mac-int-20261107` contains no M3 code; its only differing file under the M3 globs is `r1/c3/offline_eval.py`, which the M3 line never touched after the merge base, so a later integration will not conflict. Base choice is right.
- **Hygiene.** All four commits authored and committed by `Dowling Wong <wangdowling@gmail.com>`; `git diff --diff-filter=D 478d1d32..HEAD` is empty; the worktree, `harness-pin` and `harness-6adf385` stay clean after all test runs.
- **Failure set.** Baseline `478d1d32` (scratch git clone): 129 passed / 7 failed. HEAD: 183 passed / 7 failed / 10 skipped. Same 7 `test_m3_pinned_openml_loader.py` failures (sklearn 1.9.1 vs 1.8.0). Kernel opt-in with my own delegated cgroup, as root: the four files give 46 passed (78 s), matching the hand-off.
- **clone3 wrapper.** `struct clone_args` is 11 × u64 = 88 bytes (`CLONE_ARGS_SIZE_VER2`); `CLONE_PIDFD=0x1000`, `CLONE_INTO_CGROUP=0x200000000`, `exit_signal=SIGCHLD`, `stack=0`; the kernel writes an `int` through `.pidfd` (a `c_int` here, right); kernel pidfds are O_CLOEXEC. `PyDLL` keeps the GIL across the call. Failure paths: I ran real `clone3` with a non-cgroup dir fd and a cgroup-v1 dir fd: both `LauncherStop ... EBADF`, no child created. ENOSYS/E2BIG/EINVAL/EACCES on older kernels, filtered clone3 or missing delegation all end in the same STOP. The supervisor and launcher contain no `os.fork`, no `waitpid` and no numeric `cgroup.procs` write. Every wait is `waitid(P_PIDFD)` and every kill goes through cgroup.kill or `pidfd_send_signal`. `verify_membership` reads `/proc/<pid>` only while the pidfd is not readable.
- **Drain logic (kernel reading).** The hashes match the hand-off (v6.1 `dbaa4efd…`, v6.6 `27c9834f…`, v6.18 `b1dcfea0…`). The `interrupted:` path only does `list_del` and never decrements `requests`/the semaphore (v6.1 l.1158–1178; v6.18 same). In the sleeping loop the count is checked again after `prepare_to_wait_event`, so `-ERESTARTSYS`→`EINTR` comes back only while the count is zero, whatever signal caused it. ENOENT=residue / success=pending / EINTR=zero is therefore sound **while a trusted filter user is alive and no workload task remains**. If the sentinel is gone on ≥ v6.11, every receive returns ENOENT, `max_iterations` is hit and the result is `DrainStop`. That fails closed and never gives a false "clean". (The version labels are wrong, see finding 2.)
- **PID-1 sentinel against the workload (executed).** I wrote static C workloads and ran them through the full supervisor. `kill(1,SIGKILL|SIGTERM|SIGINT|SIGSTOP)`, `tgkill(1,1,SIGKILL)` and `kill(-1,SIGKILL)` are all dropped (the sentinel survived and the protocol completed). `/proc/1/fd/N`, `/proc/1/mem`, `/proc/1/exe` and `/proc/1/environ` give EACCES; listing `/proc/1/fd` is refused for each entry. No descriptor ≥ 3 survives in the workload. `ptrace`, `process_vm_*`, `pidfd_*`, `prctl`, `seccomp`, `socket*` and `sendmsg` (except on the handoff fd number, which the workload cannot obtain as a socket) are notified. The channel is closed in the workload child before exec. `W` is sent only after `waitpid(-1)` returns ECHILD, and `D` comes only from the supervisor. I found no way to forge `W<status>`/`D`, only ways to abort the protocol, and an abort is a STOP (finding 7).
- **HUP/completion ordering.** Checked in order: listener POLLIN, listener ERR/NVAL, channel, listener HUP, pidfd. Completion needs W → clean drain → D → HUP (seen, or awaited after the pidfd exit) → pidfd reap → empty cgroup → status 0/0. The order of HUP and pidfd exit does not matter: on 5.9–6.10 the filter is released at reap (B reaps S before B exits), and on ≥ 6.11 it is released at `do_exit` (`kernel/exit.c` v6.18 l.913–915). Both orders are handled.
- **16-case preflight.** In the pinned 6adf385 OpenML template (all 12 OpenML cases' `benchmark.py`, including the credit_g/bank_marketing variants that differ only in their identity constants), `Pipeline.fit` is the first model fit and `model_type` is restricted to LR/RF/GB. In the MLP nodes, `MLPClassifier.fit` is the first model fit after `StandardScaler.fit`. Nothing before the fit catches `BaseException` (the pinned `train.py` `except Exception` is not even on the preflight path), so `ReachedFit` cannot be swallowed. `case_files` skips `data_cache` without reading it, and the tests and kernel tests use synthetic caches only. The 16 recovered edits are `config.yaml` for the 12 OpenML cases, and for the 4 MLP cases a `train.py` change to `HIDDEN_UNITS`/`LEARNING_RATE_INIT` constants only (diffed).
- **The 11 removed tests** (8 parametrizations of `test_mocked_supervisor_sequences_listener_before_workload_ack` and 3 signal-mask tests): obsolete as written, because they mock `os.fork`, `add_own_child` and the mask guard, none of which exists any more. The replacements cover the clone3 order, teardown by pidfd and most of the event loop, **except** what finding 3 lists.

## Findings

1. **[blocking] The drain can hang indefinitely, past the supervisor timeout, when SIGALRM is blocked.** `r1/c3/offline_seccomp.py:229-247`; called from `r1/c3/offline_supervisor.py:199`. `drain_withdrawn` relies on `SIGALRM` from `setitimer` to end the last blocking `NOTIF_RECV`. If the supervisor's thread has SIGALRM blocked (an inherited mask, a caller's `pthread_sigmask`, some job runners), the final receive sleeps forever. The `deadline` in `monitor` is not checked inside the drain, so `timeout_seconds` does not bound it. Executed: `probe_sup.py` with `pthread_sigmask(SIG_BLOCK,[SIGALRM])` before `supervise(..., timeout_seconds=15)` and a clean workload hung until an external `timeout 40` killed it (audit stops after `listener_ready`; PDEATHSIG then cleaned up B/S). Since the fork design's mask restore was removed, the same blocked mask also reaches B, S and the workload across `execve` (`offline_launcher._child_exec`, `offline_bootstrap.main`). This is fail-closed in the sense that there is no false accept, but it breaks the "bounded STOP" property the reviewer asked about. **Fix:** in `drain_withdrawn`, read the mask (`signal.pthread_sigmask(SIG_BLOCK, [])`) and either unblock SIGALRM for the drain (restoring it afterwards) or STOP before the first receive. Also bound the drain by wall clock (pass the remaining `deadline`, and STOP when it is exceeded even on repeated ENOENT). In the bootstrap entry, set an empty mask (`pthread_sigmask(SIG_SETMASK, [])`) before anything else, and consider resetting all inherited `SIG_IGN` dispositions for the workload, not only SIGPIPE/SIGXFSZ (`offline_bootstrap.py:145`). Add a unit test with SIGALRM blocked (it must STOP or complete within a bound, never block).

2. **[should-fix] The kernel-version reading is wrong in one place, and the kernel test's version gate would hang the on-site qualification run on 6.6–6.10.** `r1/c3/offline_seccomp.py:198,211`; `r1/tests/test_m3_withdrawn_drain.py:164-170`; hand-off `docs/r1/reports/MAC_M3_OVERNIGHT_HANDOFF_20261109.md:46,54,101,107`. The `refcount_read(&filter->users) == 0` early return in `recv_wait_event` is **not** in v6.6. Its v6.6 body (sha `27c9834f…`, l.1474–1495) has no users check, and I checked each tag v6.7–v6.10 without it; it first appears in **v6.11** (the hand-off cites the v6.18 line, 1529). In the same series the filter release moved to `do_exit` (v6.18 `kernel/exit.c` l.915). On 6.6–6.10 (unless backported), a receive after HUP with count 0 therefore **sleeps**, and `test_kernel_clean_workload_drains_to_zero`, which calls `_libc_recv` with no timer when `release >= (6, 6)`, blocks forever. That is exactly the kind of kernel the site step may meet (e.g. a 6.8 distribution kernel). The design itself is unaffected, because the sentinel keeps `users > 0` on every version. **Fix:** correct the docstring, test comment and hand-off ("v6.11+, and any stable backport; before that the residue stays observable after HUP but the sentinel is still required for ≥ v6.11"). In the test, do not gate on the version: run the negative-control receive under a short `setitimer`/SIGALRM and accept either ENOENT (≥ 6.11 behaviour) or EINTR (pre-6.11), recording which one occurred. Also add to §4 that listener HUP requires ≥ v5.9 (no `EPOLLHUP` in v5.8 `seccomp.c`), not just clone3 ≥ 5.7, and that 5.9–6.10 release the filter at reap while ≥ 6.11 releases it at exit.

3. **[should-fix] STOP branches that the removed tests guarded are now untested; the hand-off overstates the replacement coverage.** `r1/c3/offline_supervisor.py:191-192` (listener POLLERR/POLLNVAL) and `:213-214` (pidfd POLLERR/POLLHUP/POLLNVAL). Mutation check: I deleted both branches in a scratch clone, and `test_m3_monitor_protocol.py`, `test_m3_supervisor_component.py` and `test_m3_launcher.py` still pass, 54/54. The removed parametrizations `error`, `listener_invalid`, `pidfd_error`, `pidfd_hup` and `pidfd_invalid` asserted these; hand-off §3 lists "listener error … pidfd error" among the 15 replacement cases, but none of the 15 produces them. The old `pending_hup` case (POLLIN|POLLHUP in one batch must go through `monitor_one`) is also not reproduced: the new test uses POLLIN alone. **Fix:** add monitor tests with a fake poller (or closed pipe ends) for listener POLLERR, listener POLLNVAL, pidfd POLLHUP/POLLERR/POLLNVAL before the drain, and listener POLLIN|POLLHUP in one batch. Correct the hand-off list.

4. **[should-fix] `check_preflight_results` does not tie the 16 runs to the bound runtime or spec, and accepts extra executed files.** `r1/c3/offline_case_preflight.py:305-339`. (a) `results[...]['supervisor']` is `supervise()`'s return, which carries neither the spec SHA nor the closure digest (`offline_supervisor.py:287-289`). So "ALL_16_PASSED" can be assembled from runs under a different closure or spec, although the binding claims `runtime_closure_sha256` and `verify_execution_binding` later re-checks only the binding's own digest. (b) `seen = {... if n in bound_files}` (l.325) drops files in the record that are not in the binding, so an extra file in `/work/node` (e.g. an extra importable `.py`) is accepted silently. (c) `preflight_source_sha256` is stored but never checked. **Fix:** return `spec_sha256` and the closure digest from `supervise` (the spec is already hashed in `_write_spec`). Have `check_preflight_results` require closure digest == `binding['runtime_closure_sha256']`, require the spec hash to match one rebuilt by `build_preflight_spec` for that case, and require exact equality of `files_sha256`. Either verify `preflight_source_sha256` against the closure item for `offline_case_preflight.py` or drop the field.

5. **[note] The MLP preflight does not execute the node's actual `train.py`.** `r1/c3/offline_case_preflight.py:110-121,178-181`. It extracts the five constants with `ast.literal_eval` and calls `run_benchmark` itself. For the 16 recovered cases this is equivalent: I diffed them, and only constant values change. It is still a divergence from "the actual pinned entry", and a future edit of `main()` would not be seen. Suggest either running `train.py` via `runpy.run_path(..., run_name='__main__')` under the guard, or asserting that the edited `train.py` AST equals the pinned one apart from those five constants' values.

6. **[note] `bootstrap_identity` is computed after the child has exec'd, and omits two executed files.** `r1/c3/offline_supervisor.py:134-140,279`. Hashing after `spawn_into_cgroup` leaves a TOCTOU window, and `r1/__init__.py` and `r1/c3/__init__.py` (executed by the entry) and the stdlib modules B imports are not covered. It is audit-only today (hand-off §4.4), but compute it before the spawn and include the package `__init__` files before the value is ever pinned.

7. **[note] The workload can change PID 1's resource limits.** `prlimit64` (302) is not notified, and the workload has the same uid. Executed: `prlimit(1, RLIMIT_AS|RLIMIT_NOFILE, …)` from the workload returns 0. I found no route from this to a false "clean": `W` still requires ECHILD. The only effect is an abort, e.g. a hard `RLIMIT_CPU` makes the kernel force-SIGKILL PID 1, which leads to HUP before the drain and a STOP. Consider notifying `prlimit64` when `arg0 != 0` (glibc's own get/setrlimit use pid 0), or record this as accepted denial-of-service only.

8. **[note] `verify_membership` compares only the cgroup basename** (`r1/c3/offline_launcher.py:206`). `CLONE_INTO_CGROUP` already guarantees placement and the name is random, so the risk is negligible. Comparing the full path relative to the cgroup-v2 mount would make this belt-and-braces check exact.

9. **[note] Questions for the author (agree with the hand-off's framing).** Q1: the PID-1 sentinel is sound as reviewed above, so (a) is reasonable. Q2: the MLP preflight runs `StandardScaler.fit` (feature means) and the split; no model fit and no metric. Whether that counts as "non-numerical" is the author's call. Q3: whether the four frozen fit paths read any external input is still unreviewed; I did not argue it statically. Wiring into `c3_env_replay.run` is correctly left out; the production OpenML STOPs are unchanged.

VERDICT: changes requested

---

## Round 2

# Independent review — M3 overnight unit, round 2

Same reviewer as round 1 (`/tmp/pb/reviews/REVIEW_M3_round1.md`). Read-only on `/tmp/pb/wt/m3`; scratch under `/tmp/pb/scratch_rev_m3/` (probes `probe/`, mutation clone `headgit/` at `4df14fd6`, driver `mut.py`); scratch cgroup `/sys/fs/cgroup/unified/pb-rev-m3/deleg` (it survived the container restart). No SSH, no host, no push, no real cache, label table or seed file read.

Unit under review: `4df14fd6` on `25a2f301`. Answers: `docs/r1/reviews/MAC_M3_REVIEW_ANSWERS_20261109.md`; hand-off §7.

## Re-verification

- **Hygiene.** `4df14fd6` is authored and committed by `Dowling Wong <wangdowling@gmail.com>`. No file is deleted (`--diff-filter=D` empty). The worktree, `harness-pin` and `harness-6adf385` stay clean.
- **Regular set.** 196 passed / 7 failed / 13 skipped. The 7 failures are the same `test_m3_pinned_openml_loader.py` sklearn-version failures as the baseline (129/7), so the failure set is unchanged.
- **Kernel opt-in, as root, my own cgroup.** The four files give 53 passed (72 s).

## Round-1 findings

1. **[blocking → closed] Drain hang with SIGALRM blocked.**
   - *Re-ran my probe:* `pthread_sigmask(SIG_BLOCK,{SIGALRM,SIGUSR1})`, with SIGHUP and SIGTERM set to `SIG_IGN` in the supervisor, then `supervise(..., timeout_seconds=15)` with a static workload that prints its `/proc/self/status`.
     - The run returns `COMPLETE_UNQUALIFIED` / `clean` in 0.17 s; it previously hung until killed.
     - Afterwards the caller's mask is restored exactly (`[10, 14]`), the SIGALRM handler is back to `SIG_DFL` and the timer is `(0, 0)`.
     - The workload reports `SigBlk`, `SigIgn` and `SigCgt` all `0000000000000000`.
   - *Code:*
     - The drain unblocks SIGALRM, re-reads the mask and STOPs before the first receive if SIGALRM is still blocked.
     - Every receive is preceded by a deadline check, and the monitor passes its own deadline (30 s without one). The iteration cap is kept.
     - The bootstrap entry clears the mask first. The workload child resets every `SIG_IGN` and the mask.
   - *Mutations:* removing the unblock, the still-blocked check or the mask restore each fails its unit test. Removing the deadline check fails `test_drain_is_bounded_by_its_deadline_even_on_endless_enoent`, but only after about 1000 s (100 000 iterations × 10 ms); see note N4. Removing the entry's mask clear fails `test_entry_clears_an_inherited_signal_mask`. Removing the workload `SIG_IGN` reset fails `test_sentinel_child_closes_channel_restores_signals_and_execs`.
2. **[should-fix → closed] Kernel versions.**
   - The docstring (`offline_seccomp.py:205-226`), the test comment and hand-off §2.2/§4/§7 now say v6.11 for the `users == 0` early return, ≥ 5.9 for listener `EPOLLHUP`, and release at reap (5.9–6.10) vs at `do_exit` (≥ 6.11). This matches my own round-1 checks of the sources.
   - The post-HUP negative control has no version gate any more. It runs under a 0.5 s timer and accepts ENOENT or EINTR, which removes the 6.6–6.10 hang.
3. **[should-fix → closed] Event-loop coverage.**
   - New scripted-poller tests cover listener POLLERR/POLLNVAL, pidfd POLLHUP/POLLERR/POLLNVAL/POLLERR|POLLIN, and POLLIN|POLLHUP in one batch. The last asserts that `monitor_one` is called exactly once.
   - *Re-ran my mutations:*
     - The listener ERR/NVAL branch replaced by `if False:` fails both listener tests.
     - The same mutation on the pidfd ERR/HUP/NVAL branch fails all 4 pidfd tests.
     - Disabling the POLLIN-first branch fails 3 tests, including the new one-batch test.
4. **[should-fix → closed] Preflight tied to the bound runtime.**
   - `supervise()` now returns `spec_sha256`, `spec_content_sha256` and `runtime_closure_sha256`.
   - `check_preflight_results` requires the executed spec and checks, case by case:
     - the spec content digest against the supervisor's;
     - both closure digests against the binding's;
     - the closure item for `offline_case_preflight.py` against `preflight_source_sha256`;
     - the spec's node files, exactly;
     - the seeds and the preflight argv;
     - the record's `files_sha256`, exactly.
   - *Mutations:* disabling each of the eight checks in turn (exact record files, closure, spec digest, source, spec files, seeds, argv) fails `test_results_accepted_only_when_every_case_matches`. The kernel 16-case test passes with the executed specs.

## Round-1 notes

- **5 — MLP preflight (addressed).** `mlp_edit_is_constants_only` compares the AST with the five constants' literal values blanked. All 16 cases pass it. The mutation that disables the check fails `test_mlp_edit_beyond_the_constants_is_refused`. Accepted.
- **6 — Bootstrap identity (addressed).** It is now hashed before the spawn, over 8 files including both package `__init__.py` files. It is still audit-only, as declared.
- **7 — `prlimit64` (addressed).** I traced the BPF jumps by hand:
  - nr 302 with `arg0` low word ≠ 0 goes to `USER_NOTIF`; pid 0 goes to `ALLOW`.
  - For every other syscall the `jf=4` jump lands on the syscall list with the accumulator still holding nr.
  - The `clone` block's `jf=6` is unchanged and still correct.
  - Only the low word is checked, which matches the kernel's `pid_t` truncation.
  - *Re-ran my probe:* `prlimit(1, …)` from the workload now gives `STOP: prohibited syscall 302`.
  - The unit test catches the mutation that allows `prlimit64`.
- **8 — Full cgroup path (addressed).** `rel` always starts with `/`, so the `endswith` suffix match is component-aligned. The mutation is caught by `test_membership_check_reads_proc_only_while_pidfd_unready`.
- **Sentinel attack probes re-run** with SIGALRM blocked in the supervisor. Signals to PID 1 are still dropped, `/proc/1/{fd/N,mem,exe,environ}` still give EACCES, `kill(-1)` gives ESRCH, and all runs complete cleanly.

## Remaining notes (non-blocking; no change required for acceptance)

- **N1.** No test checks that `monitor` passes its deadline to the drain (`offline_supervisor.py:213`). Mutating it to `drain(listener)` survives the unit tests. The drain is then still bounded by `max_seconds=30`, so this is only a coverage gap: the drain could run up to 30 s past the workload deadline. A one-line assertion in a monitor test with a fake drain would close it.
- **N2.** The workload child's own `pthread_sigmask(SIG_SETMASK, set())` (`offline_bootstrap.py`, sentinel fork branch) is redundant behind the entry's mask clear. Its mutation survives both the unit and the kernel tests. It is harmless defence in depth, so it can stay.
- **N3.** If the workload finishes just before its deadline, the drain can STOP with "exceeded its deadline". That is fail-closed and acceptable. In the same window, a SIGALRM the caller had pending while blocked is consumed by the drain's handler. Neither affects soundness.
- **N4.** `test_drain_is_bounded_by_its_deadline_even_on_endless_enoent` only detects a missing deadline check after about 1000 s, because the default `max_iterations` is used. Passing a small `max_iterations` such as 1000 would make it fail fast while still telling the deadline STOP apart from the cap STOP.
- **N5.** Some hand-off text is stale. §3 l.80 still says "the four files give 46 passed" and §4.2 says "run the 10 kernel opt-in tests"; the current numbers are 53 and 13, as the answers file states. Please update them when the hand-off is next touched.
- The author questions Q1–Q4 (hand-off §5) stand as before. Wiring into `c3_env_replay.run` is correctly not done. Nothing here is a site qualification.

VERDICT: accepted
