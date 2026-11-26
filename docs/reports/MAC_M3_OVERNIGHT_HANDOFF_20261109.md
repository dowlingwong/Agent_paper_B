# M3 overnight hand-off — 9 November 2026

**Review: accepted in round 2 at `4df14fd6` (`reviews/MAC_M3_REVIEW_20261109.md`; answers `reviews/MAC_M3_REVIEW_ANSWERS_20261109.md`). Test numbers in §3 below are from round 1; after the round-1 fixes: regular set 196 passed / 7 failed (same sklearn 7) / 13 skipped, kernel opt-in 53 passed (13 kernel tests) as root and as the unprivileged user. Non-blocking reviewer notes N1–N4 (deadline passed to the drain untested; redundant child mask reset; drain at the deadline fails closed; small max_iterations in the deadline test) are open for the next M3 unit.** AI-assisted (Claude, overnight worker in the cloud container; Linux 6.18.44 x86-64, Python 3.13.18, sklearn 1.9.1). Code and synthetic tests only. No SSH, no server, no host, no real dataset cache, no model, no GPU, no numerical replay. The production replay STOPs in `r1/scripts/c3_env_replay.py` (lines 482–483 and 578–579) are **unchanged**. Nothing here is a target-host qualification or an authorization.

Branch `mac-m3-20261109`. Code commits: `b6d77f73` (supervisor), `e78b81c5` (preflight), and the commit carrying this revision of the report (bootstrap identity in the audit, §2.1).

## 1. Base

`origin/mac-m3-16case-path-review-20261108` (`dad7fffd`) with these merged in (all merges clean, no conflict):

| merged branch | why |
|---|---|
| `mac-m3-blocker-review-20261108`, `mac-m3-withdrawn-recheck-review-20261108` | the other two 8 Nov reviews (docs only, same base `78cf7220`) |
| `mac-m3-hup-source-20261107` | `4b52ae92` (HUP source review) was not in `78cf7220` |
| `mac-m3-cache-copy-20261105`, `mac-m3-case-binding-20261105` | `offline_cache_copy`, `offline_config_checks`, `offline_recovered_cases` and their reviews were not in `78cf7220`; the 16-case work needs them |

`mac-m3-supervisor-20261105`, `-listener-`, `-pidfd-wait-`, `-sigchld-` are already ancestors of `78cf7220`. Merge tip `478d1d32`.

## 2. The open items of the 8 Nov reviews, now

| # | open item (8 Nov) | now | where |
|---|---|---|---|
| 1 | original-child identity: `os.fork()` then numeric `cgroup.procs` write; a parent `os.register_at_fork` callback could reap/recycle before assignment (`MAC_M3_SIGCHLD_ASSIGNMENT_REVIEW_20261107.md`, blocker recheck) | **done in code, local-kernel tested; site qualification pending** | `r1/c3/offline_launcher.py`, `offline_supervisor.py` |
| 2 | withdrawn notification: an attempt interrupted before `NOTIF_RECV` leaves no record; HUP/exit then look like a clean run (`MAC_M3_WITHDRAWN_RECHECK_20261108.md`) | **done in code; the swallowed-interruption counterexample is a passing test on the local kernel; site qualification pending** | `offline_seccomp.drain_withdrawn`, `offline_bootstrap.py` (PID-1 sentinel), `offline_supervisor.monitor` |
| 3 | HUP handling: listener HUP was an unconditional STOP, pidfd-only completion was possible | **done** (protocol below) | `offline_supervisor.monitor` |
| 4 | all 16 cases: non-numerical, configuration-dependent preflight under the boundary, bound to the later real path (`MAC_M3_16CASE_PATH_RECHECK_20261108.md`) | **partly**: preflight, binding and re-verification exist and all 16 actual recovered configurations pass under the local boundary with synthetic OpenML caches; not wired into `c3_env_replay.run`; the fit-time-input question stays a review item; site run pending | `r1/c3/offline_case_preflight.py`, `offline_runtime_closure.py` |

### 2.1 Child identity (item 1)

`offline_launcher.spawn_into_cgroup` issues one raw `clone3` with exactly `CLONE_PIDFD | CLONE_INTO_CGROUP`, `exit_signal = SIGCHLD`, `stack = 0` (fork-like). The kernel puts the child into the private cgroup before it runs and returns its pidfd atomically. Consequences:

- the supervisor never calls `os.fork`, so **no** `os.register_at_fork` callback and no `pthread_atfork` handler runs in the parent (asserted in the kernel tests by registering a parent callback and checking it never fires);
- no numeric PID is written anywhere; the old `add_own_child` path is no longer called by the supervisor (left in `offline_cgroup.py` unchanged, with its tests);
- every later wait and kill is by pidfd (`waitid(P_PIDFD)`, `pidfd_send_signal`); teardown without a pidfd refuses to reap by number;
- the blocked-signal-mask guard of the fork design is removed (it protected only the numeric write). SIGCHLD `SIG_IGN`/`SA_NOCLDWAIT` is still refused, now only to keep the exit status (a lost status is a fail-closed STOP, never a misattribution).

Between `clone3` and `execve` the child runs only `_child_exec` (three `dup2`, one `execve`); the syscall is made through `ctypes.PyDLL` so the GIL is held, and the supervisor must be single-threaded (checked). The child execs a fresh `python -I -S -B r1/c3/offline_bootstrap_entry.py` with an empty environment; the bootstrap specification is passed as a file in the private output directory together with its SHA-256 (checked by the bootstrap). The `group_bound` audit record now also carries the bootstrap interpreter's real path and SHA-256 and the SHA-256 of the six bootstrap source files the child execs (`bootstrap_identity`); they are recorded, not yet compared with a pin. A latent bug found by the first real run is fixed: the exec'd bootstrap must load its codecs before `chroot` (`codecs.lookup`), which the forked design had inherited.

### 2.2 Withdrawn notifications (item 2) and HUP (item 3)

**Kernel basis** (read from upstream `kernel/seccomp.c`, fetched from `raw.githubusercontent.com/torvalds/linux/<tag>/kernel/seccomp.c`): v6.18 (sha256 `b1dcfea0…f1fb`), v6.11 (`7396faa0…`), v6.10 (`a2b1254c…`), v6.6 (`27c9834f…d5fe`), v6.1 (`dbaa4efd…d072`), v5.15 (`439783c5…99e1`), v5.9 (`197a1ff5…`), v5.8 (`9bdc50a5…`). *(Corrected 10 Nov after review: see §7.)*

- Each queued notification increments a request count: `atomic_inc(&match->notif->requests)` (v6.6+, `seccomp_do_user_notification`, v6.18 line 1186) or `up(&match->notif->request)` (v6.1 line 1119, v5.15 line 1103).
- If the notifying task is interrupted *before* receipt, the `interrupted:` path only `list_del`s the entry (v6.18 lines 1226–1246); the count is **not** decremented.
- `NOTIF_RECV` first takes one count without sleeping when it is positive (`atomic_dec_if_positive` in `recv_wait_event`, v6.18 lines 1524–1548; `down_interruptible` fast path before v6.6), then returns `ENOENT` if no un-received entry exists (v6.18 line 1586); it sleeps interruptibly only when the count is zero.
- From **v6.11** (absent in v6.6–v6.10; any stable backport aside), `recv_wait_event` returns at once when the filter has no users (v6.18 line 1529), so after the last user is gone `NOTIF_RECV` always says `ENOENT` and the count is unobservable; before v6.11 that receive sleeps with count zero. In the same series the filter release moved from reap to `do_exit` (v6.18 `kernel/exit.c` l.913–915). The sentinel keeps `users > 0` on every version, so the drain is valid on all of them. (The 9 Nov text said "from v6.6"; that was wrong.)

**Mechanism.** `drain_withdrawn(listener)` repeats raw `NOTIF_RECV` (ctypes, no CPython EINTR retry) under a periodic `SIGALRM` without `SA_RESTART`: each `ENOENT` is one withdrawn-before-receipt attempt, a success is a still-pending notification, `EINTR` means the count was zero. Soundness does not depend on the tick: `EINTR` comes only from the sleeping path, which is reached only with count zero. The precondition is that a trusted task still holds the filter and no workload task remains. That is why **PID 1 of the private PID namespace is now the trusted bootstrap, not the workload**: it makes itself non-dumpable and checks it has no signal handlers (so in-namespace signals to init are dropped), installs the filter, hands off the listener, starts the workload as its child, reaps the whole namespace until `ECHILD`, sends `W<status>`, and waits for `D`. The supervisor drains on `W`, STOPs on any residue or pending entry (PID 1 is then killed with the cgroup), else sends `D`.

**Completion now requires**, in order: `W`, a clean drain, `D`, listener **HUP** (the filter's last user is gone; checked within 5 s after the pidfd exit), pidfd exit via `waitid(P_PIDFD)`, an empty cgroup, bootstrap exit 0 and workload status 0. Listener HUP before the drain is a STOP ("withdrawn attempts unobservable"); pidfd exit before the drain is a STOP; a readable listener is always a STOP via `monitor_one`, also after the drain.

**The counterexample, executed** (local kernel, `AR_M3_KERNEL_TESTS=1`):
- `test_m3_withdrawn_drain.py::test_kernel_swallowed_interruption_is_invisible_to_poll_but_found_by_drain`: the real M3 filter; a workload whose `socket(AF_UNIX)` is suspended, interrupted by `SIGALRM` (handler without `SA_RESTART`) and whose `EINTR` is swallowed, exit 0. `poll` on the listener shows no `POLLIN` (the old monitor saw nothing); the drain returns `withdrawn = 1`.
- `test_kernel_clean_workload_drains_to_zero`: no attempt → `withdrawn = 0`; and the negative control: after HUP the receive runs under a timer and either `ENOENT` (v6.11+: no residue is observable, which is why the sentinel is required) or `EINTR` (pre-v6.11) is accepted and reported; no version gate (the 9 Nov version gate could block forever on 6.6–6.10).
- `test_m3_supervisor_kernel.py::test_withdrawn_before_receipt_is_found_by_drain`: the **full supervisor** with a static C workload making 200 swallowed interrupted `socket()` calls while the supervisor's first poll is delayed 2 s: STOP "withdrawn before receipt", audit `"withdrawn": 200`, no `prohibited_syscall` record. Without the delay the same workload is stopped through the received route; either way it STOPs.

### 2.3 Sixteen cases (item 4)

`offline_case_preflight.preflight_case` (workload side, run inside the boundary) calls the node's **actual pinned entry function** (`run_openml_benchmark` / `run_benchmark`) with every model fit (`Pipeline.fit/fit_predict/fit_transform`, `MLPClassifier.fit/partial_fit`, and the three classifiers' `fit`) replaced by a guard raising `ReachedFit`, a `BaseException`, so the pinned `except Exception` cannot swallow it. The real path runs verbatim up to the first model fit: seed variables, config parsing and validation, data loading from the private cache copy (OpenML) or bundled digits / `make_classification`, label encoding, the split, `StandardScaler.fit` (MLP preprocessing) and the configuration-dependent estimator construction. The record holds the files' hashes, seeds, the cache fingerprint before (= after, else STOP), the estimator class and a parameter hash, the training-array shape, class counts and digest, and `estimator_fitted: false` (`check_is_fitted`). No model is trained, no metric computed, no artifact written.

Host side: `build_case_binding` binds the 16 cases' exact node files (pinned files plus the recovered edit, hash-checked against `configuration_file_sha256`), seeds, per-node cache fingerprints and the runtime-closure digest. `check_preflight_results` accepts only if all 16 records match and each supervisor run was `COMPLETE_UNQUALIFIED` with a clean drain. `verify_execution_binding` re-checks files, cache and runtime immediately before a later real execution. `build_preflight_spec` produces the bootstrap specification; `offline_runtime_closure.build_closure` builds the hash-pinned interpreter/stdlib/package/`ldd` closure (≈4,900 files here; each bound read-only at its own path).

Results: all 16 actual recovered configurations reach the fit guard in-process (synthetic OpenML data); all 16 pass under the **full local boundary** (`test_m3_case_preflight_kernel.py`, ≈70 s), `check_preflight_results` → `ALL_16_PASSED_UNQUALIFIED`; a damaged cache makes sklearn try to re-download and the **kernel filter** stops it (`prohibited syscall`).

Not done for item 4: wiring `verify_execution_binding` and the preflight verdict into `c3_env_replay.run` (and any change to its OpenML STOP) — a separate reviewed step and an author/authorization matter; the frozen-code argument that the four `fit` paths (liblinear LR, RF with `n_jobs=1`, GB, MLP) read no external input remains a reviewer item; the OpenML data here is synthetic (iris minus one class, relabelled per data id), and the real caches were not touched (the pinned harness holds real `data_cache` for sonar and climate; not read).

## 3. Tests and results

Environment for the comparison: `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin` (`a3fedbb`), `AR_M3_PINNED_HARNESS` = worktree of harness `6adf385`. Files: `r1/tests/test_m3_*.py r1/tests/test_c3_env_replay.py r1/tests/test_c3_recovered_fixture_archive.py`.

| run | passed | failed | skipped |
|---|---|---|---|
| baseline `478d1d32`, pinned harness set | 129 | 7 | 0 |
| after `e78b81c5`, pinned harness set | 183 | 7 | 10 (kernel opt-in) |
| baseline, no `AR_M3_PINNED_HARNESS` | 123 | 0 | 13 |
| after, no `AR_M3_PINNED_HARNESS` | 170 | 0 | 30 |

**Failure set unchanged**: the same 7 `test_m3_pinned_openml_loader.py` tests fail before and after, all on `assert sklearn.__version__=='1.8.0'` (local 1.9.1; environment, not code).

Kernel opt-in (`AR_M3_KERNEL_TESTS=1 AR_M3_DELEGATED_CGROUP=<writable cgroup-v2 dir> AR_M3_PINNED_HARNESS=…`; with them the four files give 46 passed, re-run on the final commit both as root and as the unprivileged user): 10 tests in `test_m3_launcher.py` (1), `test_m3_withdrawn_drain.py` (2), `test_m3_supervisor_kernel.py` (5), `test_m3_case_preflight_kernel.py` (2): **10 passed as root**, and **10 passed as an unprivileged user** (`m3user`) whose supervisor ran in a user-owned cgroup subtree (`…/pb-m3-user/super`, delegated dir `…/pb-m3-user/deleg`), emulating systemd delegation. The 59 tests of `test_m3_launcher.py`, `test_m3_withdrawn_drain.py`, `test_m3_supervisor_kernel.py` and `test_m3_monitor_protocol.py` were run three times in a row as root: stable.

Changed existing tests (all in `test_m3_supervisor_component.py`; the mechanisms they asserted were removed):
- removed: `test_mocked_supervisor_sequences_listener_before_workload_ack[none|error|pending_hup|pidfd_error|pidfd_hup|pidfd_invalid|pidfd_premature|listener_invalid]` (fork + numeric assignment + mask order) → replaced by `test_mocked_supervisor_clone3_sequence_binds_then_acknowledges`, `test_mocked_supervisor_failure_tears_down_by_pidfd[spawn|membership|monitor]` and the event-loop cases in the new `test_m3_monitor_protocol.py`. *Corrected 10 Nov:* the 9 Nov version of this file (15 cases: HUP before drain, pidfd exit before drain, residue/pending, POLLIN, exit without HUP, notification after drain, non-zero status, signalled bootstrap, channel EOF, invalid message, no reap, timeout, clean) did **not** cover listener POLLERR/POLLNVAL, pidfd POLLERR/POLLHUP/POLLNVAL or POLLIN|POLLHUP in one batch, contrary to what this line said; those cases were added on 10 Nov with a scripted poller and checked by mutation (§7);
- removed: `test_signal_mask_restored_when_guard_rejects_before_fork`, `test_restore_failure_stops_before_bootstrap_ack_and_closes`, `test_mocked_child_restores_original_mask_before_bootstrap` (signal-mask guard no longer exists) → `test_refuses_auto_reaping_sigchld`, `test_refuses_multithreaded_supervisor`, `test_child_branch_only_dups_and_execs` in `test_m3_launcher.py`;
- edited: the two teardown tests now inject the pidfd wait and assert no numeric `waitpid`; new `test_teardown_without_pidfd_never_signals_or_reaps_by_number`; `test_pid1_rearms_death_guard_after_capability_drop_before_exec` now also asserts handler check → non-dumpable → filter → listener → sentinel.

Commands:
```
export AR_HARNESS_ROOT=<harness a3fedbb> AR_M3_PINNED_HARNESS=<harness 6adf385>
python3 -m pytest -q -p no:cacheprovider r1/tests/test_m3_*.py r1/tests/test_c3_env_replay.py r1/tests/test_c3_recovered_fixture_archive.py
# local-kernel (Linux x86-64, gcc, user namespaces, cgroup v2, clone3):
AR_M3_KERNEL_TESTS=1 AR_M3_DELEGATED_CGROUP=<owned cgroup-v2 dir> python3 -m pytest -q -p no:cacheprovider \
  r1/tests/test_m3_launcher.py r1/tests/test_m3_withdrawn_drain.py r1/tests/test_m3_supervisor_kernel.py r1/tests/test_m3_case_preflight_kernel.py
```
No test copies the harness tree; none runs a dry-run campaign.

## 4. What remains for the on-site qualification (host step, not tonight)

On the target host, as the operator user, inside a delegated cgroup-v2 subtree, with the batch venv (pinned sklearn 1.8.0):
1. kernel version, cgroup-v2 delegation (target and common-ancestor `cgroup.procs` writable), unprivileged user namespaces, `clone3` + `CLONE_INTO_CGROUP` (≥ 5.7), seccomp user notification with `NEW_LISTENER`, and listener `EPOLLHUP` (≥ **5.9**; absent in v5.8 `seccomp.c`), so the kernel must be ≥ 5.9; note that 5.9–6.10 release the filter at reap and ≥ 6.11 at `do_exit` (both orders are handled by the supervisor);
2. run the 10 kernel opt-in tests; in particular the two drain tests and `test_withdrawn_before_receipt_is_found_by_drain` qualify the request-count accounting on **that** kernel (pre-6.6 semaphore or 6.6+ atomic form; the post-HUP negative control reports whether the kernel has the v6.11 early return);
3. re-derive `PREFLIGHT_PACKAGES` and the runtime closure from the batch venv (the local list includes `narwhals` for sklearn 1.9.1), then run the 16-case boundary preflight on the real private cache copies — this needs its own authorization note, since it reads the real caches;
4. pin the bootstrap interpreter and source hashes now recorded in `group_bound` (today the supervisor's `sys.executable`; recorded, not compared).

## 5. Open questions (for the author or the reviewer)

1. **PID 1 is now the trusted sentinel, not the workload.** Needed so a filter user survives the workload for the drain. Options: (a) accept; (b) keep the workload as PID 1 and accept that withdrawn attempts are unobservable on ≥ 6.11 (contradicts the reviewed requirement); (c) a ptrace-based observer instead. **Recommend (a).**
2. **Is the preflight "non-numerical"?** It runs the data split and the MLP `StandardScaler.fit` (feature means) but no model fit and no metric. Options: (a) accept as non-numerical (no training, no metric; needed to exercise the configuration-dependent pipeline on the real column types); (b) stop before the split (then `_build_pipeline` is not exercised as in the real path). **Recommend (a).**
3. **Fit-time inputs.** Whether the four pinned fit paths can read any external input is a frozen-code review item; options: reviewer argues it statically (recommended), or the author accepts the residual risk explicitly.
4. **Wiring into `c3_env_replay.run`.** Not done on purpose; recommend a separate small unit after this one is accepted, and only with the e1 authorization path.

## 6. Scratch and side effects

Scratch only under `/tmp` and, for the kernel tests, cgroups under `/sys/fs/cgroup/unified/pb-m3-scratch` and `/sys/fs/cgroup/unified/pb-m3-user` of this disposable container (left in place, empty). A local user `m3user` was created in the container for the unprivileged run. No tracked file was deleted.

## 7. Round-1 review fixes (10 November)

See `docs/r1/reviews/MAC_M3_REVIEW_ANSWERS_20261109.md` for the per-finding answers. In short:
- **Drain bound (finding 1, blocking):** `drain_withdrawn` unblocks SIGALRM in its thread for the drain and restores the caller's mask, STOPs before the first receive if SIGALRM stays blocked, and is bounded by the monitor's deadline (or 30 s) and by its iteration cap, also on endless `ENOENT`. The bootstrap entry clears the inherited signal mask first; the workload child resets every inherited `SIG_IGN` and the mask.
- **Kernel versions (finding 2):** the `users == 0` early return is v6.11+ (corrected in §2.2, the docstring and the test); listener HUP needs ≥ 5.9 (§4).
- **Event-loop coverage (finding 3):** scripted-poller tests for listener POLLERR/POLLNVAL, pidfd POLLHUP/POLLERR/POLLNVAL and POLLIN|POLLHUP; mutation-checked.
- **Preflight tied to the bound runtime (finding 4):** `supervise()` returns `spec_sha256`, `spec_content_sha256` and `runtime_closure_sha256`; `check_preflight_results` requires the executed spec, the bound closure and preflight source, exact file sets, seeds and command.
- Notes 5–8: MLP `train.py` edits must be constants-only (AST check); bootstrap identity hashed before the spawn and including the package `__init__` files; `prlimit64` on another process is notified; membership check compares the full cgroup path.
