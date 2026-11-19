Reviewed base: `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` (harness branch `mac-harness-isolation-20261117`; accepted in round 8; report `06692ecc` accepted in round 8, with its one requested wording fix in `80b7cb92`)

# Independent review record — harness isolation unit (R1-HARNESS-ISOLATION)

**Unit.** The isolated run of Track G nodes in `autoresearch_harness`: `src/autoresearch/trackg/isolation.py`, the node
library `src/autoresearch/trackg/node_lib/ar_isolated.py`, the runner, outcome, node-template and campaign changes, the
template config and the tests under `tests/trackg/`, on `mac-harness-isolation-20261117` over `r1-local-trackg-v2-20261114`
@ `717ad835`; and the report `docs/r1/reports/HARNESS_ISOLATION_20261117.md` on `mac-harness-isolation-report-20261117`
over `main` `50176481`. Authority: PLAN rows R1-HARNESS-ISOLATION and R1-TRACKG-PORT-DECISIONS (4) (on `main`
`50176481`); queue of 17 Nov 2026, item (1).

**Process.** One independent reviewer, a separate agent that did not write the code, for all eight rounds (rounds 7 and 8: the report and the record's limits text). It edited
nothing in the worktree; its probes and scratch files are under `/tmp/hisorev/`, and it removed the cgroups and
`/dev/shm` files it created. The round texts are reproduced below as delivered, as block quotes, so that only this
record's own closing lines are read as the acceptance.

| Round | Commits reviewed | Verdict |
|---|---|---|
| 1 | `033b7ad` (diff from `717ad835`) | CHANGES REQUESTED (4 blocking, 4 minor) |
| 2 | `99dba0e` (diff from `033b7ad`) | CHANGES REQUESTED (1 blocking, 4 minor) |
| 3 | `0b2c892`, `c5d2358` (diff from `99dba0e`) | ACCEPTED with follow-ups F1–F3 |
| 4 | `be7734e` (diff from `c5d2358`: F1–F3 and notes) | ACCEPTED (2 notes) |
| 5 | `1950d4b` (diff from `be7734e`: the round-4 notes) | ACCEPTED (1 note) |
| 6 | `eac6846` (diff from `1950d4b`: the round-5 note) | ACCEPTED |
| 7 | report `1d52760c` and this record's first version, against `eac6846` | CHANGES REQUESTED (documentation only: R-1 to R-15) |
| 8 | `68cdd1a` (diff from `eac6846`: limits text, R-3) and report `06692ecc` (diff from `1d52760c`) | ACCEPTED (one wording fix, applied in `80b7cb92`) |

**Coordinator's note on round 3.** The uncommitted `unshare` EINVAL retry the reviewer saw in the worktree was the
coordinator's own experiment; it was dropped, never committed, and replaced by the launcher reviewed in round 4.

**Full harness suite** (coordinator, Python 3.12, `tests`, `--continue-on-collection-errors`): base `717ad835` and
`eac6846` give the same 65 failing or erroring tests (environmental: optional packages missing, the t0 identity test,
and one collection error in `tests/test_legacy_noop_skip.py`). `68cdd1a` changes record text only; `tests/trackg` on it
gives 200 passed and the same t0 failure. The full-suite run left an untracked `paper/tables/artifact_completeness_report.txt`
in the harness worktree (round 8 noticed it); it was never committed and was moved out of the worktree.

---
## Round 1 (commit `033b7ad`)

> # Independent review: R1-HARNESS-ISOLATION unit, round 1
>
> - Worktree `/tmp/pb/wt/hiso`, branch `mac-harness-isolation-20261117`, commit `033b7ad`, base `717ad835`. Reviewed `git diff 717ad835..033b7ad`: 13 files, +1736/−32.
> - Reviewer: independent; I did not write this code. Read-only: no commits, checkouts or edits under /tmp/pb. Probes and scratch files are under `/tmp/hisorev/`. Every `hisorev_*` cgroup I created has been removed.
> - Authority: R1-HARNESS-ISOLATION; R1-TRACKG-PORT-DECISIONS (4).
>
> ## Verdict: CHANGES REQUESTED
>
> The single-host mechanics are well built:
> - the runner starts the parent without a shell;
> - it accepts the result channel only from the parent's pid (SO_PEERCRED);
> - the log is append-only and its hash is checked;
> - the frozen files are hashed before and after the run;
> - cgroup.kill works, and the user and cgroup namespace is set up correctly.
>
> The tests pass: 190 passed, 1 failed. The failure is the known `test_trackg_t0_identity` case, and I checked that it has the same cause as on the base: `ImportError: langchain-openai is required`.
>
> The unit does not yet meet its own threat model, though. Four probes get a **forged metric accepted with `isolation.effective: true`**, with every check green (log intact, no frozen file changed, no rejected connection):
> - **P1**: a proposal rewrites the next run's frozen parent.
> - **P2**: a same-uid process outside the run takes over the parent, with no race.
> - **P2b**: the same, through the startup window, when the cgroup namespace is off.
> - **P6**: an interpreter startup hook.
>
> A fifth probe, **P7**, gets past the measured timeout, which the authority requires to kill the run and count against the proposal. Each probe below is reproducible.
>
> ---
>
> ## BLOCKING
>
> ### B1. The frozen-file check is only relative, so a proposal can rewrite the frozen parent of later runs (P1, demonstrated)
>
> **Where:**
> - `runner.py:379,398-400`: `frozen_before` and `frozen_after` both hash the run's *own copy*.
> - `runner.py:244-246`: the code snapshot lives in `run_dir/code`, inside the tree the worker can write.
> - `campaign_v2_diff.py:153,184`: the next incumbent is `result.code_dir`.
> - `campaign_v2_diff.py:113`: every later run is copied from that snapshot.
>
> **What happens:** the worker's cwd is `runs/<id>/work`. Its uid can write `../code/` and every sibling `runs/*/code/`, including the current incumbent. It can also write the node kit directory, which belongs to the same user. Nothing compares the frozen files of the directory a run is copied from against a pinned reference. The next run therefore copies a rewritten `parent.py` (or `ar_isolated.py`, `worker.py`, `ar_data.py`, …). Its before and after hashes match each other, and the run is accepted.
>
> **Probe `p1_incumbent.py`** runs as uid 65534 with a delegated cgroup and the cgroup namespace, mirroring the campaign:
> 1. `s000` (baseline): ok 0.5.
> 2. `s001` is a proposal diff to `train.py` that rewrites `../../*/code/parent.py`. The diff is applied and the run gives ok 0.5, so it is discarded and the incumbent stays `s000/code`.
> 3. `s002` runs from the unchanged incumbent: **`ok 0.9999`**, `effective: true`, `frozen_files_changed: []`, `log_intact: true`, channel `val_accuracy: 0.9999`.
>
> Any single proposal, even one that is divergent or discarded, compromises every later run of the campaign. That includes the sealed test metric the parent writes.
>
> **Fix:**
> - Pin the frozen-file manifest once, from the kit at a trusted moment (or commit it in the kit or spec).
> - Check each run's copy against that manifest *before* the run and refuse on a mismatch.
> - Before promoting a snapshot, re-hash its editable state against the recorded `code_state_sha256`.
> - Keep snapshots out of the run uid's reach (see the common fix below).
>
> ### B2. A same-uid process outside the run can take over the frozen parent (P2 and P2b, demonstrated)
>
> **(a) With `cgroup_namespace=True` (the default), there is no race.** See `isolation.py:316-344` and the docstring at lines 21-27 and 38-42.
> - The child calls `unshare(CLONE_NEWUSER|CLONE_NEWCGROUP)` *before* it execs the parent. The parent's `mm->user_ns` is therefore a user namespace whose owner is the run uid.
> - The kernel gives the owner of a user namespace every capability inside it, including `CAP_SYS_PTRACE`, to any process of that uid in the parent namespace.
> - So `__ptrace_may_access` passes for such a process despite `PR_SET_DUMPABLE=0`. So does Yama's relational check, which has a `ns_capable(child_cred->user_ns, CAP_SYS_PTRACE)` exception.
>
> **Probe `p2_userns_ptrace.py` + `outsider.py`.** The runner runs as uid 65534 with a delegated cgroup. A separate uid-65534 process runs in the init user namespace and is not a descendant of the runner. It:
> 1. takes the parent's result socket with `pidfd_getfd`;
> 2. writes `val_accuracy: 0.9999` on that socket;
> 3. uses `PTRACE_SEIZE` and syscall-entry register edits to turn the parent's own channel write into `exit_group(0)`.
>
> Result: **`ok 0.9999`**, `effective: true`, `rejected_result_connections: 0`. In the control run with `cgroup_namespace=False`, `pidfd_getfd` returns `EPERM` and the run is ok 0.5.
>
> **(b) With `cgroup_namespace=False`, the startup window is open.** See `ar_isolated.py:39,80-88` and the fixture/template parent.
> - `parent_start()` runs only after `import ar_isolated`, which imports NumPy (about 85 ms here) on top of interpreter startup. The parent is dumpable for that whole time, because exec resets the dumpable flag.
> - A `PTRACE_SEIZE` made inside that window survives the later `prctl(PR_SET_DUMPABLE, 0)`.
>
> **Probe `p2b_startup_race.py` + `outsider_early.py`, 4 of 4 runs succeeded.** The outsider attaches early. Using register edits only, it points the parent's channel `sendto` at bytes the worker had returned in its prediction array, then turns the second write into `exit_group(0)`. Result: **`ok 0.9999`**, `effective: true`, although the honest accuracy is about 0. Case (b) needs Yama `ptrace_scope=0` (this kernel has no Yama; RHEL-family default 0). Case (a) does not depend on Yama.
>
> **How a worker gets such an outsider:**
> - `ssh localhost` with a key it appends to `~/.ssh/authorized_keys` (the run shares the host network namespace);
> - `systemd-run --user` or D-Bus activation;
> - `at` or `crontab`;
> - an existing tmux or screen server.
>
> None of these is a descendant of the runner or a member of the run cgroup. The outsider persists, so it can forge every later run of that uid: baselines, census, T1 labels.
>
> **The docstring claims the opposite:** "no process ever holds the channel while it can be reached through /proc", "Capabilities in the new user namespace end at exec, so the run gains no privilege", and "calls parent_start as its first statement".
>
> **Fix:**
> - Put the namespaces on the **worker**, not the parent. The parent execs in the runner's user namespace and stays in the run cgroup. A frozen launcher puts the worker into a child cgroup with its own user, cgroup and PID namespace (and ideally a mount namespace).
> - Close the dumpable window. For example, the runner `PTRACE_SEIZE`s the child itself (only one tracer is allowed) until the parent reports that it is non-dumpable. Alternatively, make `prctl` the parent's first bytecode using only `ctypes`, with no other import before it. That still leaves interpreter startup open, so the tracer guard is the robust option.
> - Without these, `effective` must not be `true`.
>
> ### B3. Interpreter startup hooks are writable by the run uid and give a cross-run takeover of the parent before `parent_start` (P6, demonstrated)
>
> **Where:**
> - `node_template.py:290-291`: `argv` is `[interpreter, entry, …]`, with no `-I`, `-s`, `-E` or `-P`.
> - `runner.py:306-311`: the run gets the full `os.environ`, including `HOME`.
> - The docstring at `isolation.py:56-61`.
>
> **Probe `p6_pth.py`** runs as uid 65534:
> 1. Run `r1`'s worker writes `zz_ar.pth` into its user site-packages (`$HOME/.local/lib/python3.13/site-packages`) together with a payload. The payload wraps `ResultChannel.write` once `ar_isolated` is imported.
> 2. Run `r2`, from an **honest** node, gives **`ok 0.9999`**, `effective: true`, `frozen_files_changed: []`.
>
> The same works through a user-owned venv's `site-packages` (`.pth`, `sitecustomize`, `usercustomize`). It also works within one run, through `sys.path[0]` (the work directory, where the worker can create `<module>.py`) for anything the parent imports lazily after the worker has started. Torch-based GPU parents import a lot lazily.
>
> The docstring's limit ("a writable Python environment the parent imports from later; the parent imports what it needs before it starts the worker") reads as if this were contained. It is not, because the hook runs at the *next* run's startup, before any frozen code.
>
> **Fix:** the interpreter tree and `$HOME`'s Python paths must not be writable by the run uid. Start the parent with `-I`, add the shim and the frozen directory explicitly, and drop `sys.path[0]`. As a minimum, hash the run interpreter's site directories and startup hook files before each run and refuse on a change.
>
> **Common root cause of B1 and B3, and of M3 and N2 below:** the worker runs as the uid that owns the harness, the kits, the runs tree and the environment. The robust fix is to run the worker as a dedicated uid, or in the namespace the runner already creates plus `CLONE_NEWNS` with read-only bind mounts of `$HOME`, the venv, the kit, `runs_root` (except its own `work/`) and `data/`, and with `CLONE_NEWPID` (see B4). Read-only bind remounts are allowed inside an unprivileged user and mount namespace.
>
> ### B4. The worker can get past the measured timeout by stopping the runner (P7, demonstrated)
>
> **Where:**
> - `isolation.py:442-455`: the loop checks `proc.poll()` before the deadline, and nothing compares the elapsed time with the timeout after exit.
> - There is no PID namespace, so the worker can signal any process of its uid, including the runner. `kill_ok_by_cred` matches on kuid across user namespaces.
>
> **Probe `p7_sigstop.py`** runs as uid 65534 with a measured timeout of 3 s (1 s × 3). A helper forked by the worker sends `SIGSTOP` to the runner. The worker then works for 6 s, and the helper sends `SIGCONT` once the parent has exited. Result: **`ok 1.0`**, `timed_out: false`, wall time 6.3 s.
>
> In isolated mode, budget accounting stays in the worker (a stated limit). The timeout is therefore the *only* compute bound the runner enforces, and an RL policy that learns to stop the runner gets unbounded compute. This defeats "a timeout kills the run with a cgroup" and R1-TRACKG-PORT-DECISIONS (4).
>
> The same signalling power lets a worker `SIGKILL` the runner, ending the campaign, or kill processes of other runs or campaigns of the same uid on the host.
>
> **Fix:**
> - Classify `elapsed > timeout` as a timeout in both runner paths, measured from a monotonic start.
> - Give the worker a PID namespace, so it cannot address outside pids.
>
> ---
>
> ## MINOR
>
> ### M1. The worker can turn its own run into an infrastructure failure, which is rerun and never registered as evaluated (P3, demonstrated)
>
> **Where:** `outcome.py:139-153` (infrastructure checks first, including log patterns matched against worker output); `campaign_v2_diff.py:131-137` (reruns, then `infrastructure_failure_final`, which can be proposed again).
>
> The probe `p3_censor.py` shows three routes:
> - the worker `SIGKILL`s its parent: `infrastructure_failure/killed signal 9`;
> - the worker shrinks the memfd it was lent: the parent's `snapshot()` hits **SIGBUS**, giving `infrastructure_failure/killed signal 7` (`ar_isolated.py:264-266` creates the memfd without seals);
> - the worker prints `No space left on device`: `infrastructure_failure/infrastructure_log_pattern`.
>
> A fourth route is untested: up to `MAX_MESSAGE_BYTES` (16 GiB, `ar_isolated.py:45`) of declared arrays can get the parent OOM-killed (SIGKILL, so infrastructure).
>
> In RL, a policy can censor its own bad outcomes this way. It is the same class of exploit that decision (4) closed for timeouts.
>
> **Recommend, for isolated runs:**
> - treat a parent death by a signal the runner did not send, and an infrastructure pattern that appears only in worker output, as divergent (or register the state after N such outcomes, like `timeout_cap`);
> - create memfds with `MFD_ALLOW_SEALING` and add `F_SEAL_SHRINK|F_SEAL_GROW|F_SEAL_SEAL` before sending them;
> - let the parent pass the expected shape and dtype to `recv`, and check them before allocating.
>
> **This is an author decision, to be taken before any RL training.**
>
> ### M2. The subreaper backstop is beaten by pid hopping when `nsdelegate` is missing (P5, demonstrated)
>
> **Where:** `isolation.py:140-167`; docstring lines 44-49; `runner.py:422`.
>
> **Probe `p5b_hopper_nobody.py`** runs as uid 65534 with a delegated cgroup; this host is cgroup2 without `nsdelegate`.
> - A daemon moves itself to `hisorev_p5b/runs`, which the cgroup namespace does not prevent without `nsdelegate`, and then loops fork+exit.
> - Result: `orphans_killed: 0`. The process is still alive 9 s after the run, as a child of the runner, in `0::/hisorev_p5b/runs`.
>
> The bounded snapshot-and-kill loop cannot catch a process that changes pid faster than a `/proc` scan. A survivor can:
> - edit `run.log` between `verify_log` and the second read in `parse_run_log` (see M3);
> - edit `run_record.json` or earlier runs' files after the fact;
> - hold the GPU, CPU or memory that later runs need.
>
> The record states `nsdelegate: false` and `migration_possible: true`, yet still says `effective: true`. The docstring's "until none is left" and "this catches one that migrated out" are not true.
>
> **Recommend:** refuse the run, or set `effective: false`, whenever `migration_possible and not nsdelegate`, and correct the docstring.
>
> ### M3. The runner writes into a directory the worker can write (P4, demonstrated)
>
> **Where:** `runner.py:402,448-452,261`.
>
> - `result_channel.txt` is written with `Path.write_text`, which follows symlinks. A worker that pre-creates `../result_channel.txt` as a symlink gets the target overwritten: the probe overwrote a `runs/victim.txt` standing in for `campaign_ledger.jsonl`.
> - `run_record.json` is opened with `"x"`, so a pre-created file makes the runner raise `FileExistsError`, which ends the campaign.
> - Classification re-reads `run.log` from disk after `verify_log`, a TOCTOU window for any survivor (M2, B2).
> - `determinism_shim.json` can be forged by the run. This predates the unit.
>
> **Fix:**
> - Classify from the bytes that were verified.
> - Write runner-owned outputs with `O_NOFOLLOW|O_EXCL` into a directory the run cannot write, or create them before the run starts.
>
> ### M4. The docstrings and `limits_text()` overstate the isolation
>
> The text at `isolation.py:1-61,538-545` and `ar_isolated.py:1-26` should either state the following or have it fixed:
> - (B1) the frozen check is relative, and the incumbent and the kit can be written;
> - (B2) the user-namespace owner's capabilities, and the dumpable window before `parent_start`;
> - (B3) the startup hooks;
> - (B4, M1) the worker can signal the runner and other runs;
> - (M2) pid hopping;
> - the "random" socket name is listed in `/proc/net/unix`, so only SO_PEERCRED protects the channel;
> - `data/` is a symlink that is not followed, and the worker can **read** the validation and test labels and predict them (metric gaming, test leakage), and **write** them if the data directory belongs to the run uid;
> - the CUDA IPC path is untested: the parent must clone the shared tensor before scoring, and the worker can tamper with torch's IPC reference counter (crash or leak, which ends in a crash or infrastructure outcome).
>
> `isolation.effective` is `euid != 0` alone. It should also need the cgroup, the namespace, and `nsdelegate` (or no migration).
>
> ---
>
> ## NOTES
>
> - **N1. Late accept** (`isolation.py:467`). A connection already queued from the parent's pid is rejected once `proc.poll()` has seen the exit. A very fast parent whose `connect` sits in the backlog when the loop polls loses its metric (divergent `no_metric`). Accept queued connections after exit too: the SO_PEERCRED pid was recorded at connect time.
> - **N2.** `rejected_result_connections > 0` is recorded but not acted on. Any foreign connection is evidence of an attack; consider making it divergent.
> - **N3.** `frozen_file_hashes` uses `read_bytes()` for each file, twice per run. Real `data/` directories (CIFAR, ogbn-arxiv, the autoresearch token shards) would mean holding up to gigabytes in runner memory per file. A worker can also drop a huge sparse file into a frozen directory to exhaust the runner's memory. Hash in streams, or pin data once and stat-check it per run.
> - **N4.** `__pycache__` is skipped in frozen directories. A planted `.pyc` with a matching source mtime would be loaded by a lazy import in the parent during the same run (the same class as B3).
> - **N5.** Test lines:
>   - The one-metric-line rule covers only `metric_regex`.
>   - A second test-metric line in a plain run is still resolved by taking the last one (`selection.py:85-86`).
>   - In isolated runs, a test line in the run output is not refused.
>   - If T1 labels use the sealed metric, apply the rule to test lines as well.
> - **N6. Timeout policy:**
>   - Under a measured timeout, a *baseline* timeout now goes straight to `baseline_failed` STOP and skips the baseline infrastructure reruns. The baseline is not a proposal; is that intended?
>   - Any `timeout_factor` makes a timeout a proposal failure; decision (4) says × 3. Consider requiring 3, or recording a reason.
>   - Once kits are converted, the census baseline must be measured on the isolated split, because the IPC and worker start-up add time.
>   - The isolated timeout path calls `cgroup.kill()` with its default 10 s grace, not `limits.kill_grace_seconds`.
> - **N7. No harness gate yet.** Nothing makes T1 label runs or RL entry points refuse nodes without effective isolation. The PLAN calls for one before T1 or RL; add it in the kit-conversion unit.
> - **N8. Protocol parser.** `np.prod(..., dtype=int64)` can overflow. NumPy then raises a `ValueError` that is not an `IsolationProtocolError`, so the parent crashes and the run is divergent, which is acceptable. Use a Python int product anyway.
> - **N9. Regressions for non-isolated runs: none found** beyond the intended changes:
>   - measured timeout gives divergent;
>   - more than one metric line gives divergent;
>   - new `cgroup` keys appear in the records.
>
>   I checked the seven ported kit wrappers in tgb-ar, tgb-mlab and tgb-mlgym: each emits `AR_METRIC` and `AR_TEST` once, so the one-line rule does not break them. The plain cgroup path, both the timeout kill and the leftover kill, is correct.
>
> ## Test adequacy
>
> - **Missing tests:**
>   - an outside same-uid process (B2);
>   - cross-run tampering through the incumbent, the kit or startup hooks (B1, B3);
>   - the worker signalling the runner (B4);
>   - memfd shrink and oversized arrays (M1);
>   - pid hopping (M2);
>   - symlinked or pre-created run-directory files (M3);
>   - foreign connections, channel overflow and `result_channel_error`;
>   - several isolated runs in one runner process (the persistent non-dumpable and subreaper flags, `children_before`).
> - `test_escaped_daemon_…` passes vacuously on this host. Its key assertion is guarded by `if nsdelegate`, and the daemon only sleeps, so it is easy to catch.
> - `test_node_library_copy_matches_the_master` is a tautology: it checks that the master contains `parent_start`. It compares no copies.
> - `test_forging_through_proc_…` makes only conditional assertions as root. The real check is the uid-65534 test, which tries only from *inside* the namespace.
>
> ## Probes (all in `/tmp/hisorev/probes/`; the harness runs as root and drops to uid 65534 like the unprivileged test)
>
> Run each with `cd /tmp/hisorev/probes && PYTHONDONTWRITEBYTECODE=1 /tmp/tgport312/bin/python <probe>`.
>
> | Probe | Finding | Result |
> |---|---|---|
> | `p1_incumbent.py` | B1 | s002 ok 0.9999 accepted |
> | `p2_userns_ptrace.py` (+ `outsider.py`) | B2a | ok 0.9999; control EPERM, ok 0.5 |
> | `p2b_startup_race.py` (+ `outsider_early.py`) | B2b | ok 0.9999 with `cgroup_namespace=False`, 4 of 4 |
> | `p6_pth.py` | B3 | honest node ok 0.9999 |
> | `p7_sigstop.py` | B4 | 6.3 s run, 3 s timeout, ok, `timed_out=false` |
> | `p3_censor.py` (`MODES=` to select) | M1, M3 | parent SIGKILL, SIGBUS and log pattern each give infrastructure; `run_record.json` pre-created gives the runner `FileExistsError`; symlinked `result_channel.txt` overwrites the target |
> | `p5b_hopper_nobody.py` | M2 | survivor alive, `orphans_killed: 0` |
>
> `common.py` holds the shared helpers. `p5_hopper.py` is the root-runner variant of P5, kept because `p5b` reads its payload. Its own run did not demonstrate an escape: as an unmapped root inside the user namespace the daemon got `EACCES` on the chowned `cgroup.procs`.

---

## Round 2 (commit `99dba0e`)

> # Independent review: R1-HARNESS-ISOLATION unit, round 2
>
> - Worktree `/tmp/pb/wt/hiso`, commit `99dba0e`, reviewed against `033b7ad` (`git diff 033b7ad..99dba0e`).
> - Read-only: no commits, checkouts or edits under /tmp/pb, and the worktree is still clean.
> - Probes are in `/tmp/hisorev/probes2/`, along with round-1 helpers in `/tmp/hisorev/probes/`. Every `hisorev_r2_*` cgroup I created has been removed. The scratch venv `/tmp/hisorev/r2venv` is left with no `.pth` planted.
> - Tests: `tests/trackg` gives **197 passed, 1 failed**. The failure is the known `test_trackg_t0_identity` case (missing `langchain-openai`).
>
> ## Verdict: CHANGES REQUESTED (1 BLOCKING, 4 MINOR)
>
> The round-1 findings are fixed, and I re-verified each one by re-running its probe (table below). Moving the namespaces to the worker, pinning the frozen files, checking elapsed time, and making host conditions explicit waivers are all sound.
>
> One new forgery path remains. A worker can get a command run **outside** the sandbox through a pathname Unix socket that the sandbox does not hide. That outside process then forges the metric of a later run, from an honest node (R2-B1, demonstrated).
>
> ### Round-1 findings re-checked
>
> | Round 1 | Probe (round 2) | Result now |
> |---|---|---|
> | B1 incumbent / kit tamper | `r2p1.py` | The worker's write gets `OSError` (read-only mount), so s001 and s002 are honest 0.5. An outside tamper of the incumbent gives **IntegrityError STOP**. Closed. |
> | B2a late pidfd_getfd / ptrace | `r2p2.py late` | `EPERM` (the parent stays in the runner's user namespace). Closed. |
> | B2b early PTRACE_SEIZE | `r2p2.py early` ×3 | `infrastructure_failure/parent_traced`, caught by the TracerPid check. Needs Yama ≥ 1 or the explicit waiver. See also NOTE N2. |
> | B3 user-site `.pth` | `r2p3.py user_pth` | The real HOME is read-only, and the parent runs with `-s`. Closed. |
> | B4 SIGSTOP of the runner | `r2p3.py stop_runner`, `pgstop` | The runner's pid is invisible to the worker. `kill(0, SIGSTOP)` stops only the parent and worker, and the run ends as divergent `timeout` (3.4 s against a 3 s limit). Closed. |
> | M1 memfd SIGBUS | `r2p3.py sigbus` | `ftruncate` gets `PermissionError` because of the seals; the run is ok. Closed. |
> | M1 parent SIGKILL | `r2p3.py pgkill`, `cgkill_run` | **Still open by two other routes.** See R2-M2. |
> | M2 escape + pid hopping | `r2p3.py hopper` | The cgroup migration still succeeds (`moved`, no `nsdelegate`), but the PID namespace kills the hopper: no survivor. Closed. |
> | M3 run-directory files | `r2p3.py precreate`, `symlink` | Read-only mount, so the worker cannot write there and the run fails as divergent. Closed. |
>
> ---
>
> ## BLOCKING
>
> ### R2-B1. A pathname Unix socket gives a command outside the sandbox, which forges a later run (P8, demonstrated)
>
> **Where:**
> - `runner.py` `_sandbox_config`: the protected paths are made read-only, but they stay *visible*.
> - `/tmp`, `/var/tmp` and `/run/user/<uid>` are made private only "when no protected path lies under them".
> - Nothing else is hidden.
> - `ar_isolated.py:23-36`.
>
> **Two facts make this possible:**
> - A read-only bind mount does **not** stop `connect()` to a Unix socket on it. The kernel exempts sockets from `EROFS`.
> - The network namespace blocks only abstract sockets and IP. It does not block pathname sockets.
>
> So any same-uid daemon that runs commands for clients of its uid stays reachable from inside the sandbox:
> - a tmux server under `/tmp` (when `/tmp` is not private), under `TMUX_TMPDIR`, or under HOME;
> - GNU screen under `/run/screen/S-<user>`, which is never made private;
> - similar daemons whose sockets live under HOME.
>
> A process started that way runs outside every protection: no namespace, no read-only mounts.
>
> **Probe `r2p8.py`** runs as uid 65534 with a delegated cgroup and the full sandbox; the only waiver is `ptrace_scope`, because this host has no Yama, and the attack does not use ptrace.
> - A tmux-like daemon (`fake_tmux_server.py`) runs as the same uid outside the runner. Real tmux cannot allocate a pty as non-root in this container. The daemon checks the peer uid with SO_PEERCRED, as tmux does, and listens at `$HOME/.tmux/default`, so its socket sits under the read-only HOME.
> - Run `r1` (attacker): the worker cannot write HOME (`home_write: OSError`). It connects to the socket (`tmux: b'ok'`), and the outside command copies a `.pth` into the run interpreter's venv (`/tmp/hisorev/r2venv`, owned by the uid).
> - Run `r2` (**honest node**): **`ok 0.9999`**, `frozen_files_changed: []`, `log_intact: true`, channel `val_accuracy: 0.9999`. The parent's `-E -s` flags do not stop site-packages `.pth` files.
>
> `effective` is `false` here only because of the Yama waiver. On a host with Yama ≥ 1 the same chain runs with `effective: true`. The record shows `private: ["/var/tmp"]` only: `/tmp` is not private because the runs root lies under it, which is also how the test suite runs.
>
> **Other things the outside process can change for later runs:**
> - the data, if the uid can write it (the kits only `chmod` it, and the owner can undo that);
> - the user's harness checkout, which the next campaign process imports;
> - kits of later campaigns, because the pin is taken "as the kit is now" (see N1).
>
> **Fix, robust options:**
> - Build the worker's filesystem from an allow-list instead of a deny-list: `pivot_root` into a new tmpfs root that holds only the interpreter (read-only), the data (read-only), the work directory (read-write), `/dev` basics and `/proc`. Daemon sockets then simply do not exist inside.
> - Or run the worker as a dedicated uid.
>
> **Fix, cheap partial measures:**
> - Always make `/tmp`, `/var/tmp` and `/run` private, then re-bind the protected and writable subpaths that lie under them (stage them before covering).
> - Hide HOME and the runs root (an empty tmpfs plus the own `work/`) instead of making them read-only.
> - Refuse a run whose interpreter `sys.path` directories or data target the run uid can write.
>
> ---
>
> ## MINOR
>
> ### R2-M1. Frozen files inside the working copy can be written during the run; a modify-and-restore passes the check (P9, demonstrated)
>
> The whole `work/` directory is read-write for the worker, frozen files included. The frozen check compares only before and after the run.
>
> **Probe `r2p9.py`:** the parent reads a frozen `labels.npy` after the train call. The worker overwrites it in `train()` and restores it in `predict()`. With all-zero predictions (honest accuracy 0.5) the run gives **ok 1.0** and `frozen_files_changed: []`.
>
> The current kits read data through the `data` link, whose target is protected, so this needs a kit that reads a frozen input after it starts the worker.
>
> **Fix (a few lines):** after the read-write bind of `work`, bind every frozen path inside it read-only. Fix before the kits are converted.
>
> ### R2-M2. The worker can still kill the parent (an infrastructure outcome), contrary to the docstring (demonstrated)
>
> **Routes:**
> - **`kill(0, SIGKILL)`** (`r2p3.py pgkill`): the worker keeps the parent's process group. The parent is the session and group leader, and a process-group signal reaches members outside the caller's PID namespace. Result: `infrastructure_failure/killed signal 9`.
> - **cgroupfs** (`r2p3.py cgkill_run`): the host cgroup mount is visible and writable inside the sandbox. Writing `1` to the run cgroup's `cgroup.kill` (all its files belong to the uid) kills the parent: `infrastructure_failure/killed`.
>   - Not demonstrated here (on this host the runner's `cgroup.kill` is root-owned): where the runner's own cgroup is delegated to the uid, as under `user@UID.service`, the same write kills the runner (campaign DoS), and `cgroup.freeze` can stall it.
>
> Both routes reopen the round-1 M1 censoring route. The docstring claims "cannot see or signal any process outside its PID namespace (the runner, the parent)".
>
> **Fix:**
> - `start_new_session=True` (or `setsid`) for the worker.
> - Put the worker in a child cgroup (`run/worker`) with its cgroup namespace rooted there.
> - Mount a fresh cgroup2 at `/sys/fs/cgroup` inside the sandbox, or cover it.
>
> ### R2-M3. Determinism regression in isolated runs
>
> - `-E` makes the parent ignore `PYTHONHASHSEED` (`python3 -E` with `PYTHONHASHSEED=0` still has `hash_randomization=1`) and the `PYTHONPATH` shim.
> - The worker's shim cannot write `determinism_shim.json`, because the run directory is read-only for it.
> - The isolated record therefore says `shim_not_loaded` for every setting, while `environment.PYTHONHASHSEED` reads `"0"`. In round 1 the parent loaded the shim.
>
> **Fix:**
> - Set the hash seed and determinism settings explicitly in the parent (for example, re-exec with the seed, or apply the settings in `ar_isolated`).
> - Give the worker's shim a writable record path in `work/`, and have the runner read it after verification.
>
> ### R2-M4. The worker can still read things it does not need: docstrings and record
>
> - `r2p3.py read` shows the worker reading other runs' `result_channel.txt`, which includes **sealed test metrics**, and a secrets-like file in HOME (`OPENAI_API_KEY=…`).
> - Without network access, the only way out for such data is the run log and the outputs. Logs are kept and may be published.
> - `limits_text` names data and labels only.
>
> **Fix:** hide the runs root (except the own `work/`) and HOME, as above. If they stay readable, state it, including the sealed metrics of earlier runs and any credentials under HOME.
>
> ---
>
> ## NOTES
>
> - **N1. The pin is "the kit as it is now".** `r2p1.py` case s004 shows that a fresh `WorkingCopyRunner` on a tampered directory pins the tampered files and accepts **ok 0.9999**. Census and T1 label runs build their own runners. Take the pin from a manifest committed with the kit or spec, not from the live directory.
> - **N2. The TracerPid check is bypassed when Yama is off.** `r2p2.py evade` with `outsider_evade.py`, 3 of 3 runs: an early tracer turns both `PR_SET_DUMPABLE(0)` calls into `getpid` and detaches before the accept, so TracerPid is 0. It then re-attaches after the accept, takes the channel with `pidfd_getfd` and forges: **ok 0.9999**. This is the waived configuration (`effective: false`), so it is acceptable, but:
>   - check at accept that the parent is non-dumpable (`stat("/proc/<pid>").st_uid == 0` for a non-root runner);
>   - do not present the TracerPid check as a defence without Yama;
>   - make `parent_traced` an integrity STOP rather than an infrastructure rerun.
> - **N3. Unprotected `sys.path` entries.** Only `sys.prefix` and `sys.base_prefix` are protected. `/tmp/tgport312`'s `sys.path` also contains `/tmp/trackp_venv/...` through a `.pth`, and editable installs add more. Protect every entry of the parent interpreter's `sys.path`.
> - **N4. Host suspension.** The elapsed-time timeout also counts a suspension of the whole host or job (an HTCondor SIGSTOP or checkpoint) as a proposal failure. Document it, or record wall time against process CPU time.
> - **N5.** The plain runner path has no elapsed-time check. Campaigns gate plain nodes with `unisolated_reason`; T1 and census entry points need the same gate.
> - **N6. CUDA IPC across PID namespaces** is untested and may need a shared PID or IPC namespace. Run a GPU smoke test with the sandbox on before the kits rely on it.
> - **N7.** `/dev/shm` stays shared and writable: memory DoS, and tampering with torch's IPC reference counter files.
> - **N8. Unrelated file in the commit.** `paper/tables/artifact_completeness_report.txt` is a generated "0/0 checks, Ledger not found" report with absolute /tmp paths. Remove it.
> - **N9.** The infrastructure-log-pattern route is now documented as an author decision. It remains open by design.
>
> ## Test adequacy
>
> - All isolation tests run with the runs root under `/tmp`, so a private `/tmp` is never exercised.
> - No tests cover:
>   - pathname-socket reachability (R2-B1);
>   - modify-and-restore of a frozen file (R2-M1);
>   - `kill(0)` or cgroupfs writes from the worker (R2-M2);
>   - the determinism record of isolated runs (R2-M3);
>   - hiding versus read-only access to the runs root and HOME (R2-M4).
> - The tests do cover the sandbox report, the integrity stop, the elapsed-time timeout, the PID-namespace kill and the memfd seal.
>
> ## Probes (`/tmp/hisorev/probes2/`)
>
> | Probe | What it shows |
> |---|---|
> | `r2p1.py` | B1 re-check, plus N1 |
> | `r2p2.py late`, `early`, `evade` | B2 re-check, plus N2 |
> | `r2p3.py <mode>` | modes: pgkill, cgkill_run, cgkill_runner, sigbus, infra, precreate, symlink, stop_runner, pgstop, user_pth, read, hopper |
> | `r2p8.py` with `fake_tmux_server.py` | R2-B1 |
> | `r2p9.py` | R2-M1 |
>
> Run each with `cd /tmp/hisorev/probes2 && PYTHONDONTWRITEBYTECODE=1 /tmp/tgport312/bin/python <probe> [mode]`.

---

## Round 3 (commits `0b2c892`, `c5d2358`)

> # Independent review: R1-HARNESS-ISOLATION unit, round 3
>
> - Worktree `/tmp/pb/wt/hiso`. Reviewed `git diff 99dba0e..c5d2358`: commit `0b2c892` (round-2 fixes) plus `c5d2358` (lazy NumPy import), per the addendum.
> - Read-only. Probes are in `/tmp/hisorev/probes3/`. Every `hisorev_r3_*` cgroup and every `/dev/shm` stash I created has been removed.
>
> **Concurrent edit in the worktree.** At 11:55, during my session, `src/autoresearch/trackg/node_lib/ar_isolated.py` became modified and uncommitted. The change is an `unshare` EINVAL retry loop. I did not make it, and it is not part of this review. My test numbers below are therefore also taken from a clean `git archive c5d2358` in `/tmp/hisorev/c5d`.
>
> ## Verdict: ACCEPTED (with follow-ups)
>
> R2-B1 and R2-M1..M3 are closed. R2-M4 is closed for files; environment variables still leak (F1). Every probe that used to forge a metric or censor an outcome now fails. No path found in this round gets a forged metric accepted or a refused run accepted. Three MINOR follow-ups remain: F1, F2 and F3. F1 and F2 should be done before RL training.
>
> ## Round-2 findings re-checked
>
> | Round 2 | Probe | Result at `c5d2358` |
> |---|---|---|
> | R2-B1 pathname socket to an outside daemon | `r2p8.py` | Closed. The socket path (under HOME) does not exist in the worker's root, so `connect` raises and r1 is divergent. r2 from an honest node: ok 0.5, and no `.pth` was planted. The allow-list root (record `worker_sandbox.ro`) holds only `/usr` `/bin` `/sbin` `/lib*` `/etc`, the interpreter paths and the shim. |
> | R2-M1 frozen modify-and-restore | `r2p9.py` | Closed. Writing `labels.npy` gets EROFS, and the run is divergent `nonzero_exit`. |
> | R2-M2 `kill(0)` / `cgroup.kill` | `r2p3.py pgkill`, `cgkill_run` | Closed: both runs ok 0.5. The worker is in its own session, `kill(0)` does not reach the parent, and the cgroupfs is hidden. |
> | R2-M3 determinism | record | Closed: `shim_loaded: true`, and the parent keeps its environment (`-s` only). |
> | R2-M4 reads of other runs / HOME | `r2p3.py read` | Closed for files: no runs tree, and the HOME secrets file is `FileNotFoundError`. Not closed for environment variables; see F1. |
> | N2 TracerPid evade | `r2p2.py evade` | Now an `IntegrityError` STOP (dumpable at accept). The early tracer also gives an `IntegrityError` STOP, and the late `pidfd_getfd` gets EPERM. |
> | Round-1 rechecks | `r2p1.py`; `r2p3.py` sigbus, hopper, precreate, stop_runner | All still hold. The incumbent attack finds nothing to write; an outside tamper gives an IntegrityError STOP; the seals refuse the shrink; the hopper cannot reach the cgroupfs; the runner's pid is invisible. |
> | N1 pin from the live kit | `r2p1.py` s004 | Unchanged (ok 0.9999 for a fresh runner on a tampered directory). `frozen_pin_sha256` is now recorded; census enforcement is pending. |
>
> ## MINOR (follow-ups)
>
> ### F1. The worker inherits the runner's whole environment, including credentials (demonstrated)
>
> `Worker` starts the worker with `child_env = dict(os.environ)`, and the run environment is the runner's `os.environ` (`runner.build_environment`). In `r2p3.py envleak`, a token set in the runner's environment is printed by the worker into `run.log` (`envleak: 'sk-fake-review-token'`).
>
> A campaign process holds the LLM transport's credentials (for example, from a secrets file loaded into its environment). The network is closed, but logs are kept and may be published.
>
> **Fix:** give the worker an allow-listed environment: budget, seeds, determinism, `CUDA_*`/`NVIDIA_*`, `PATH`, `LANG`, the sandbox's `HOME` and caches, and the node's `isolation.env`.
>
> ### F2. `/dev/shm` carries state between runs (demonstrated)
>
> In `r2p3.py shm`, run a0 writes `/dev/shm/ar_review_stash_*` and run x1 reads it back (`shm_read: ['state from an earlier run']`). A proposal can therefore:
> - reuse weights or computations stashed by earlier runs (it trains more than the fixed budget, across proposals);
> - open a channel between concurrent runs or campaigns of the same uid;
> - fill the host's memory.
>
> The docstring says `/dev/shm` is shared, but not what follows from that.
>
> **Fix:** give the worker a private `/dev/shm` (a per-run tmpfs), and restrict shared buffers to memfd (the CUDA IPC reference counters are the only reason for sharing). At the least, state the cross-run consequence in `limits_text`.
>
> ### F3. The parent forks the worker with a Python `preexec_fn` while threads are running (not demonstrated)
>
> `c5d2358` fixes the worker's PID-1 fork by keeping NumPy out of the worker until after it.
>
> The parent has the same hazard: it imports NumPy, and in the kits Torch, before `Worker()`. `subprocess` then runs the long `_sandbox_preexec` in the forked child: `ctypes.CDLL` (which takes the dynamic-loader lock), `os.makedirs`, `realpath`, reading `mountinfo`. A lock held by another thread at fork time deadlocks the child, and the run ends as a timeout, which counts as a proposal failure. CPython warns that `preexec_fn` is unsafe with threads.
>
> **Fix:** exec a small frozen launcher (single-threaded, `python -I`, or a few lines of C) that does the namespace and `pivot_root` setup and then execs the worker. Alternatively, document a kit rule that `Worker()` starts before NumPy or Torch is imported.
>
> ## NOTES
>
> - **Flaky test.** `test_elapsed_time_beyond_the_timeout_is_a_timeout_even_after_a_normal_exit` fails in about 1 of 5 runs on its own, and failed in both full-suite runs on the clean archive. The helper sends SIGSTOP after a fixed 0.3 s; if the runner is still in setup (the sandbox probe, hashing), the stop comes before `started`, the run is ok, and the assertion fails. Synchronise the helper on the parent's start, for example by waiting for `parent.py` to appear in `/proc`. The code is correct.
> - **Tests.**
>   - Clean archive: 193 passed and 3 failed, with t0 deselected. One failure is the flaky test above; the other two are archive artefacts (`scripts/` and `configs/` were not exported).
>   - Full suite in the worktree: 198 passed, 1 failed (t0) at the first run; 197 passed, 2 failed (t0 plus the flaky test) at HEAD `c5d2358`, while the uncommitted edit was present.
> - **`unshare` EINVAL.** The uncommitted edit suggests that `unshare(CLONE_NEWUSER)` sometimes gets EINVAL when another task holds the child's mm, for example a reader of `/proc/<pid>/stat` such as the runner's own `/proc` scans. Without a retry, sandbox setup fails, which is an infrastructure rerun: benign, but noisy. Review that edit when it is committed.
> - **Broad `sys.path` entries.** The allow-list includes every `sys.path` entry of the run interpreter, as queried with the runner's environment. A broad `PYTHONPATH` entry (HOME, `/`, a repo root holding `.env` files) would bring that tree, and any daemon socket under it, back into the worker's root. Refuse entries that are HOME or one of its ancestors, or bind only the package directories.
> - **`/dev` is a recursive read-write bind of the host `/dev`.** This includes the user's `/dev/pts/*` where devpts permissions allow, so the worker could read terminal input, though it cannot inject input without a controlling tty. A minimal `/dev` (null, zero, random, urandom, `nvidia*`, a private shm) is tighter.
> - **Still open, stated:**
>   - the infrastructure-log-pattern route (author decision);
>   - the CUDA IPC path is untested under the PID namespace (needs a GPU smoke test with the sandbox on);
>   - the census frozen-pin manifest is not yet enforced (N1).
> - **Memory DoS.** The private `/tmp` is an unlimited tmpfs. Give it a `size=` limit, or rely on the cgroup memory limit.
>
> ## Probes (`/tmp/hisorev/probes3/`)
>
> | Probe | What it shows |
> |---|---|
> | `r2p8.py` with `fake_tmux_server.py` | R2-B1 re-check |
> | `r2p9.py` | R2-M1 re-check |
> | `r2p3.py <mode>` | modes: pgkill, cgkill_run, read, sigbus, hopper, precreate, stop_runner, infra, envleak, shm |
> | `r2p1.py` | round-1 incumbent re-check, plus N1 |
> | `r2p2.py late`, `early`, `evade` | round-1 B2 re-check, plus N2 |
>
> Run each with `cd /tmp/hisorev/probes3 && PYTHONDONTWRITEBYTECODE=1 /tmp/tgport312/bin/python <probe> [mode]`.

---

## Round 4 (commit `be7734e`)

> # Independent review: R1-HARNESS-ISOLATION unit, round 4 (round-3 follow-ups)
>
> - Worktree `/tmp/pb/wt/hiso`. Reviewed `git diff c5d2358..be7734e`. The worktree is clean at `be7734e`.
> - Read-only. Probes are in `/tmp/hisorev/probes4/`. Every `hisorev_r4_*` cgroup and every `/dev/shm` stash I created has been removed.
> - Tests: `tests/trackg` gives **200 passed, 1 failed**. The failure is the known `test_trackg_t0_identity` environment case.
> - The elapsed-time, environment and `/dev/shm` tests passed 6 of 6 times in a row, so the round-3 flake is gone.
>
> ## Verdict: ACCEPTED
>
> F1, F2 and F3 are closed. Every earlier forgery or censoring probe still fails against `be7734e`. Two NOTES are below; neither blocks.
>
> ## Follow-ups verified
>
> | Follow-up | Check | Result |
> |---|---|---|
> | **F3** (worker started from a threaded parent) | code; `r2p*` runs | Closed. The worker starts through `python -I -S ar_isolated.py --ar-sandbox-launch` with no `preexec_fn`, so `Popen` is safe even when the parent has threads. The sandbox setup and the PID-1 fork run in that fresh single-threaded process; PID 1 mounts `/proc`, drops its capabilities, sets `no_new_privs` and execs the worker. `worker_connect` no longer forks. The launcher closes the worker socket and only waits. |
> | **F1** (environment) | `r2p3.py envleak` | Closed for the names the harness uses. `OPENAI_API_KEY` and an arbitrary `FAKE_SECRET_TOKEN` are not passed to the worker. But see N1: the allow-listed prefixes let `HF_TOKEN`, `TORCH_HUB_TOKEN` and `AR_*_API_KEY` through. |
> | **F2** (`/dev/shm`) | `r2p3.py shm` | Closed. A stash written by run a0 is not visible to run x1 (`shm_read: []`), and nothing is left on the host's `/dev/shm`. |
> | `sys.path` breadth | code | The home directory, the runs tree and their ancestors are refused (`RunnerError`). |
> | `/tmp` size | code | Capped with `size=8g`. |
>
> ## Earlier probes re-run at `be7734e`, all still holding
>
> | Probe | Result |
> |---|---|
> | `r2p8.py` (outside daemon) | The connect fails, the honest run gives 0.5, and no `.pth` was planted. |
> | `r2p9.py` (frozen modify-and-restore) | The worker's write gets EROFS; divergent. |
> | `r2p1.py` (incumbent) | The worker finds nothing to write; an outside tamper gives an IntegrityError STOP. |
> | `r2p2.py late` | EPERM. |
> | `r2p2.py early`, `evade` | IntegrityError STOP: traced, or dumpable at the accept. |
> | `r2p3.py` pgkill, cgkill_run | ok (the parent is not reached). |
> | `r2p3.py` sigbus | Refused by the seals. |
> | `r2p3.py` hopper | The cgroupfs is absent; no survivor. |
> | `r2p3.py` precreate, read | The files land in the private tmpfs only; reading HOME gives `FileNotFoundError`. |
> | `r2p3.py` stop_runner | `ProcessLookupError`. |
>
> Three probe modes (read, hopper, stop_runner) first failed only because their own `FAKE_*` variables were now filtered from the worker's environment. I renamed them to `AR_FAKE_*` and re-ran them, with the results above.
>
> ## NOTES
>
> - **N1. Some credentials still pass the prefix allow-list.** The prefixes `HF_`, `TORCH` and `AR_` also keep credentials. `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` are common on ML hosts and were demonstrated to reach the worker. The harness itself uses no such names today. Suggested fix: drop any variable whose name contains `TOKEN`, `KEY`, `SECRET`, `PASSWORD` or `CREDENTIAL`, whatever its prefix; or list the needed `HF_*` variables (`HF_HOME`, `HF_HUB_OFFLINE`, …) explicitly.
> - **N2. `shared_dev_shm` does not affect `effective`.** A node that sets it (any kit that uses CUDA IPC) gets the cross-run `/dev/shm` channel back, and its record still says `effective: true`. The flag appears only inside `worker_sandbox` and the limits text. Consider listing it next to the waivers, or giving GPU kits a memfd-only path so they can keep `/dev/shm` private.
> - **Still open, unchanged and already stated:**
>   - the infrastructure-log-pattern route (author decision);
>   - the census must commit `frozen_pin_sha256`; a fresh runner on a tampered directory still accepts 0.9999 (`r2p1.py` s004);
>   - CUDA IPC under the PID namespace is untested here, because this host has no GPU.

---

## Round 5 (commit `1950d4b`)

> # Independent review: R1-HARNESS-ISOLATION unit, round 5 (confirmation of N1 and N2)
>
> - Worktree `/tmp/pb/wt/hiso`. Reviewed `git diff be7734e..1950d4b`. The base `be7734e` was ACCEPTED in round 4. The worktree is clean.
> - Read-only. Probes are in `/tmp/hisorev/probes4/`. I created no cgroups that are still present.
> - Tests: `tests/trackg` gives **200 passed, 1 failed**. The failure is the known `test_trackg_t0_identity` environment case.
>
> ## Verdict: ACCEPTED
>
> ## N1: credential-like names are dropped (`node_lib/ar_isolated.py` `_worker_environment`)
>
> **Code.** The allow-list is unchanged. On top of it, any name that contains TOKEN, KEY, SECRET, PASSWORD, PASSWD, CREDENTIAL, AUTH, COOKIE or SESSION (case-insensitive) is now dropped, whatever its prefix. The sandbox's own variables (`HOME`, the caches, the determinism record) and `AR_WORKER_FD` are added after the filter, so they are not affected.
>
> **Probe.** `r2p3.py envleak` sets `OPENAI_API_KEY`, `HF_TOKEN`, `TORCH_HUB_TOKEN`, `AR_MANAGER_API_KEY` and `FAKE_SECRET_TOKEN` in the runner's environment. The worker sees none of them (`envleak: [] None`), and the run is ok 0.5. The new test also covers `CUDA_FAKE_PASSWORD`.
>
> **Harness names.** None of the environment variables the harness or the ported kits pass to runs contains a dropped substring. `AR_TOKENS` in the autoresearch kit is a log line, not a variable.
>
> **Side effect (NOTE).** `TOKENIZERS_PARALLELISM` contains "TOKEN", so it is now dropped as well; the probe confirms `TP=None` in the worker. That makes the `TOKENIZERS_` prefix in the keep list dead. HF tokenizers inside a worker that forks DataLoader workers will then warn, or may misbehave, without it. Either add `TOKENIZERS_PARALLELISM` to `_ENV_KEEP`, which is checked before the drop, or exempt it by name, or let a kit set it through `isolation.env`.
>
> `isolation.env` values are also filtered by the same allow-list before they reach the worker. That is not new in this commit, but kit authors should know it.
>
> ## N2: `shared_dev_shm` is an exception (`runner.py`)
>
> `exceptions = ["shared_dev_shm"]` when the node opts in. `effective` now requires no waivers *and* no exceptions, and the record carries `isolation.exceptions` next to `waivers`. The change is tested. This is correct.
>
> ## Remaining open, unchanged and already stated
>
> - The infrastructure-log-pattern route is an author decision.
> - The census must commit `frozen_pin_sha256` before T1.
> - CUDA IPC under the PID namespace is untested here, because this host has no GPU.

---

## Round 6 (commit `eac6846`)

> # Independent review: R1-HARNESS-ISOLATION unit, round 6 (confirmation)
>
> - Worktree `/tmp/pb/wt/hiso`. Reviewed `git diff 1950d4b..eac6846`. The base `1950d4b` was ACCEPTED in round 5. The worktree is clean.
> - Read-only. The mutation runs used a copy made with `git archive` in `/tmp/hisorev/e6`.
> - Tests: `tests/trackg` gives **200 passed, 1 failed**. The failure is the known `test_trackg_t0_identity` environment case.
>
> ## Verdict: ACCEPTED
>
> ## Code: `_worker_environment` in `node_lib/ar_isolated.py`
>
> A name in `_ENV_KEEP` is now kept exactly as listed, and the credential filter applies only to names admitted by the prefix allow-list. `_ENV_KEEP` is a short fixed set (PATH, LANG, LANGUAGE, TZ, PYTHONPATH, PYTHONHASHSEED, SOURCE_DATE_EPOCH, TOKENIZERS_PARALLELISM). None of these can carry a credential, so exempting them from the filter is safe. `TOKENIZERS_PARALLELISM` now reaches the worker, which closes the round-5 note.
>
> ## Test: `test_the_worker_gets_an_allow_listed_environment`
>
> - The fixture's `env_report` now prints every variable name. The test asserts that HOME and PATH are present (so the report is complete), that `AR_FAKE_KEEP` and `TOKENIZERS_PARALLELISM` are kept, and that `LLM_API_SECRET`, `HF_TOKEN`, `TORCH_HUB_TOKEN`, `AR_FAKE_API_KEY` and `CUDA_FAKE_PASSWORD` are dropped.
> - I confirm the author's finding: the round-4 assertions were vacuous, because the old report printed only names containing SECRET or starting with AR_FAKE.
>
> **Mutation check** (on the archive copy; the fixture copies the node library from the tree it runs in):
>
> | Variant | Result |
> |---|---|
> | Unmodified | passes |
> | `_ENV_DROP_PARTS = ()` | **fails**, at line 505 (credential names present) |
> | `TOKENIZERS_PARALLELISM` removed from `_ENV_KEEP` | **fails**, at line 503 |
>
> The test now detects both regressions.
>
> ## Remaining open, unchanged and already stated
>
> - The infrastructure-log-pattern route is an author decision.
> - The census must commit `frozen_pin_sha256` before T1.
> - CUDA IPC under the PID namespace is untested here, because this host has no GPU.

---

## Round 7 (report `1d52760c`, documentation)

> # Independent review: R1-HARNESS-ISOLATION unit, round 7 (documentation accuracy)
>
> **What was checked.**
> - The report `docs/r1/reports/HARNESS_ISOLATION_20261117.md` and the review record `docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md`, both at paper-repo commit `1d52760c` on branch `mac-harness-isolation-report-20261117`.
> - Both were checked against the harness code at `eac6846` (unchanged; the worktree is clean) and against my review files `review_r1.md` … `review_r6.md`.
> - Read-only.
>
> ## Verdict: CHANGES REQUESTED (documentation only)
>
> The acceptance of the code at `eac6846` is unaffected. The review record is accurate. The report has:
> - one wrong statement of fact in its status line;
> - wrong outcome reason names in §2;
> - a §5 claim about `isolation.limits` that the code does not bear out;
> - several overstatements in §2, §4 and §5 that need a qualifier;
> - some omissions.
>
> Each item below gives the report line and the correction.
>
> ---
>
> ## Review record (`HARNESS_ISOLATION_REVIEW_20261117.md`)
>
> - **Round texts.** After stripping the block-quote markers, all six round texts match my files byte for byte (checked with a script). Correct.
> - **Table.** Correct: commits, diff bases, verdicts and finding counts (4+4, 1+4, F1–F3, 2 notes, 1 note) all match my reviews.
> - **Coordinator's note on round 3** (the EINVAL retry was the coordinator's own, dropped, replaced by the launcher). Consistent with what I observed and with the round-4 diff.
> - **Full-suite paragraph** (65 identical failures on the base and on `eac6846`). It is attributed to the coordinator, which is right: I did not verify it.
> - **Missing open point.** "Open points for the author" should add a third author item. `autoresearch_fixedtokens` sets `shared_dev_shm`, so its runs are permanently `effective: false`. Under the report's closing rule, the interim rule would therefore apply to that node indefinitely. The author must either accept the exception for T1 (with disclosure) or require a memfd-only path for it; see R-12.
> - **Process paragraph.** After this round it should say "seven rounds (round 7: documentation)".
>
> ## Report (`HARNESS_ISOLATION_20261117.md`)
>
> ### Wrong
>
> **R-1. Status line (l. 3–4): "accepted commit `eac68466` in round 3, closing the follow-ups in rounds 4–6".**
> Round 3 accepted `c5d2358`. Rounds 4, 5 and 6 accepted `be7734e`, `1950d4b` and `eac6846`, the last in round 6, as the record says. Suggested text: "accepted `c5d2358` in round 3 and, after rounds 4–6 on the follow-ups, the tip `eac6846` in round 6; round 7 checked this report."
>
> **R-2. §2 "Result channel" (l. 53–56): wrong reason names.**
> `multiple_metric_lines` is the reason for *plain* runs. For isolated runs the reasons are:
>
> | Case | Reason |
> |---|---|
> | more than one metric line on the channel | `result_channel_metric_lines` |
> | more than one test-metric line | `result_channel_test_metric_lines` |
> | no metric line | the ordinary `no_metric_at_budget` (not a channel-specific reason) |
> | overflow (64 KiB) | `result_channel_overflow` |
> | channel error | `result_channel_error` |
>
> **R-3. §5 heading "Still open, stated in every record's `isolation.limits`" (l. 172): not true for items 5, 8 and 1.**
> `limits_text()` at `eac6846` has seven entries.
> - Item 5 (CUDA IPC untested) is not among them.
> - Item 8 (`/dev` is the host's) is not among them.
> - Item 1's record text is stale and broader than the truth: "the worker can read every file the run's uid can read". Since the allow-list root it can read only the allow-listed paths, which is what the report's item 1 says.
>
> Either add items 5 and 8 to `limits_text()` and update its first entry, or change the heading to "stated in §5 (and, for items 1, 2, 3, 4, 6, 7, 9, in `isolation.limits`)". The code change is a one-line text edit and would not affect the acceptance.
>
> **R-4. §1 (l. 42): "unless the node gives `unisolated_reason`".**
> `unisolated_reason` is an argument of `run_v2_diff_campaign`, given by the caller; it is not a node field. Also, only the v2-diff campaign enforces it: a bare `WorkingCopyRunner` (census, T1 drivers) runs a node without an `isolation` block without refusing. Add: "the T1 and census drivers must enforce the same gate (later unit)".
>
> ### Overstated (needs a qualifier)
>
> **R-5. §2 "As a result the worker … cannot read … the kit" (l. 87–88).**
> The worker reads its own working copy, which contains the kit's files, the frozen parent and node library included. It cannot reach the kit *directory*, the runs tree or HOME.
>
> The same bullet also reads as if the worker "cannot read … the Python installation". It can read the installation (it is bound read-only); it cannot *write* it.
>
> **R-6. §2 "leaves nothing behind, because the kernel kills the whole namespace" (l. 90).**
> No *process* is left behind. Files are: in its working copy (kept under the run directory, never reused as an incumbent because the snapshot is taken before the run) and, with `shared_dev_shm`, in `/dev/shm` (§5.6). Suggested wording: "leaves no process behind".
>
> **R-7. §2 "Non-dumpable parent" (l. 92–95).**
> The parent becomes non-dumpable only when it imports `ar_isolated`. During interpreter start-up it is dumpable, and only Yama `ptrace_scope ≥ 1` keeps an unrelated same-uid process from attaching in that window. The TracerPid and dumpable checks at the accept catch a tracer that is still attached, or a parent left dumpable. Without Yama, though, an early tracer could alter memory and detach before the accept unseen (round 3, note N2). Add the sentence: "This relies on `ptrace_scope ≥ 1`; with the `ptrace_scope` waiver the run is not effective."
>
> **R-8. §5 "Closed by this unit" (l. 162–170).** Two items need qualifiers:
> - "a tracer from outside": closed with `ptrace_scope ≥ 1` (otherwise waived and `effective: false`).
> - "a changed frozen file or kit": closed during a run and within a campaign. A kit changed before a later campaign or runner starts is caught only by comparing `frozen_pin_sha256` with the census (item 7). A fresh runner on a tampered directory still accepted 0.9999 in every round (`r2p1.py` s004).
>
> **R-9. §4 probes (l. 151–155).** Three corrections:
> - **"33 attack scripts"**: there are 33 `.py` files, but `probes3/` and `probes4/` are per-round copies of `probes2/`. The distinct scripts number 18: 16 probes plus 2 helpers (`common.py`, `fake_tmux_server.py`), with about 25 attack modes.
> - **"In round 4 … it re-ran them all"**: round 4 re-ran these:
>   - `r2p8` and `r2p9`;
>   - `r2p1`;
>   - `r2p2` late, early and evade;
>   - `r2p3` envleak, shm, pgkill, cgkill_run, read, sigbus, hopper, precreate and stop_runner.
>
>   Not re-run in round 4: user-site `.pth` (last run in round 2), `infra` and `cgkill_runner` (round 3), and `symlink` and `pgstop` (round 2).
> - **"every one failed or ended in an integrity STOP"**: two probes succeed by design and are listed as open, not failed:
>   - `infra` gives `infrastructure_failure` (§5.4);
>   - `r2p1` s004, the fresh runner on a tampered directory, gives ok 0.9999 (§5.7).
>
>   Round 6 ran a mutation check of the environment test, not a probe.
> - **"Full harness suite"**: mark it as coordinator-run (the record does; the report does not).
>
> ### Missing
>
> **R-10. Timeout (§2, l. 103–109).**
> - The code's own docstring states that a suspension of the whole host or job (for example an HTCondor suspend) also counts as a timeout, which is a proposal failure. The report should repeat this.
> - Under a measured timeout, a *baseline* timeout is `divergent` and therefore stops the campaign at once (`campaign_v2_diff` docstring).
> - The factor-3 rule applies to plain runs too, not only isolated ones.
>
> **R-11. §3 table and checklist.** Add these refusals and checks:
> - The interpreter's `sys.path` must not contain HOME, the runs tree or one of their ancestors. This is a hard `RunnerError` with no waiver; a broad `PYTHONPATH` on the label host will refuse every run.
> - The cgroup must be v2 with `cgroup.kill`, which needs kernel ≥ 5.14.
> - The Ada checklist should add three items:
>   - (5) the run interpreter's `sys.path` holds no home or runs-tree entry;
>   - (6) a smoke run with the sandbox on shows `effective: true` in its record (this is the end-to-end check of items 1–4);
>   - (7) the GPU smoke, with the sandbox on, exercises CUDA IPC across the PID namespace (§5.5).
> - Item 1 is right that AppArmor's `restrict_unprivileged_userns` defeats the sandbox. The runner's sandbox probe catches this and refuses, so the failure is loud, not silent; worth saying.
>
> **R-12. §5.6 and the closing paragraph (l. 186–188, 197–198).**
> `autoresearch_fixedtokens` runs are *always* `effective: false` (exception `shared_dev_shm`). Read literally, the closing rule ("until the kits are deployed with `effective: true`, the interim rule stays") keeps the interim rule on that node forever. State this, and name the author's choice: accept the exception with disclosure, or give the kit a memfd path.
>
> **R-13. §5.9 (trust).**
> Extend the trust statement from "environment and Python installation" to everything outside the run that a later run reads and the run's uid can write:
> - the data (the kits only `chmod` it, and the owner can undo that);
> - the kit before the pin;
> - the harness checkout.
>
> The worker cannot write any of these, but any other process of that uid can.
>
> **R-14. §5 "Closed by this unit".**
> List the censoring routes that rounds 1–3 closed:
> - the worker can no longer kill the parent by signal (own session, PID namespace);
> - it can no longer kill the parent through `cgroup.kill` (cgroupfs hidden);
> - it can no longer SIGBUS the parent through a memfd (sealed).
>
> This makes the remaining infrastructure-log-pattern route (§5.4) stand out as the only one left.
>
> **R-15. Minor.**
> - The private `/tmp` and `/dev/shm` are 8 GiB tmpfs each, limited in practice only by the run cgroup's memory limit; the run should have one.
> - §2's environment list omits `LANG`, `LANGUAGE`, `TZ`, `PYTHONHASHSEED` and `SOURCE_DATE_EPOCH` (kept by name), and the sandbox's own variables (`HOME` and caches in the working copy, the determinism record).
> - §5.2 ("the parent fixes the step or token count and the batches") describes the kits, not this core unit. Mark it as "in the port kits".
>
> ### Correct (checked)
>
> - **§1 header facts.** 14 files, +2,590/−48, all under `src/autoresearch/trackg/`, `configs/trackg/` and `tests/trackg/`; the commit list.
> - **§2 mechanism.** The launcher, the namespaces, the allow-list and `pivot_root`; read-only frozen paths in the working copy; the private `/dev/shm` default; PID 1's `/proc`, capability drop and `no_new_privs`; the environment filter (TOKENIZERS_PARALLELISM by name); the append-only log and classification from verified bytes; the cgroup and the subreaper; the pin and incumbent check with `stop_integrity`; `frozen_pin_sha256`; the elapsed-time timeout in both runners; factor 3 with its waiver.
> - **§3.** The five-row waiver table. `effective` = no waiver, no exception, non-root, cgroup, sandbox. The record fields listed exist; `frozen_files_changed`, `runner_dumpable` and `argv` are also recorded.
> - **§4.** 200 passed + 1; the t0 failure has the same cause as on the base (`langchain-openai` missing); 25 collected tests in `test_trackg_isolation.py` (22 functions, parametrised).
> - **§5 items 1–9.** Their substance matches my reviews, apart from the qualifiers above.

---

## Round 8 (commit `68cdd1a`, report `06692ecc`)

> # Independent review: R1-HARNESS-ISOLATION unit, round 8 (confirmation of the round-7 corrections)
>
> - (a) Harness: reviewed `git diff eac6846..68cdd1a` in `/tmp/pb/wt/hiso`.
> - (b) Report: reviewed `git diff 1d52760c..06692ecc -- docs/r1/reports/HARNESS_ISOLATION_20261117.md` in `/tmp/pb/wt/hisorep`.
> - Read-only.
>
> ## Verdict: ACCEPTED (code commit `68cdd1a`; report at `06692ecc`, with one wording fix)
>
> ## (a) Harness `68cdd1a`
>
> - **Text-only change.** Only `limits_text()` and one sentence of the `isolation.py` module docstring change. No behaviour changes.
> - **`limits_text()` now covers every §5 item**, so the report's heading "Still open (as record text in `isolation.limits`)" is now true:
>   - the first entry names the allow-listed paths (working copy with the kit's files, data, interpreter and system directories);
>   - the trust entry covers the Python installation, the data, the harness checkout and the kit before the pin, and points to the census commit of `frozen_pin_sha256`;
>   - a new entry covers `/dev` (with the private `/dev/shm` default) and the untested CUDA IPC path.
> - **Tests:** `tests/trackg` at `68cdd1a` gives **200 passed, 1 failed** (the known t0 environment failure).
> - **Untracked file (NOTE).** The worktree holds an untracked `paper/tables/artifact_completeness_report.txt`, written at 12:54. It comes from the full `tests/` suite (`tests/test_artifact_completeness_and_manifest.py` / `scripts/check_kdd_artifact_completeness.py`), not from `tests/trackg`, which is all I ran. It is not committed. Do not add it.
>
> ## (b) Report `06692ecc`
>
> R-1 to R-15 are applied correctly:
>
> | Item | Applied |
> |---|---|
> | R-1 | status line and round attribution |
> | R-2 | `result_channel_*` reasons; `no_metric_at_budget`; the plain-run reason |
> | R-3 | heading true with `68cdd1a` |
> | R-4 | `unisolated_reason` as a caller argument; the census and T1 gate left to that unit |
> | R-5 | the working copy holds the kit's files; installation readable, not writable |
> | R-6 | "no process behind"; files can remain |
> | R-7 | `ptrace_scope` dependency of the start-up window |
> | R-8 | qualifiers on "closed" |
> | R-9 | probe counts, round-4 coverage, the two by-design successes, the coordinator-run suite |
> | R-10 | suspension, factor 3 in both runners, baseline STOP |
> | R-11 | hard `sys.path` refusal row, Linux ≥ 5.14, checklist items 5–7, AppArmor caught loudly |
> | R-12 | `autoresearch_fixedtokens` always `effective: false`, the author decision, the interim rule indefinitely |
> | R-13 | trust extended to the data, the kit before the pin and the checkout |
> | R-14 | censoring routes listed as closed |
> | R-15 | tmpfs bounds, full environment list, §5.2 marked as port-kit |
>
> The environment lists, the waiver table, the `effective` rule and the test numbers all match the code at `68cdd1a`.
>
> **One wording fix (§3).** "On the label hosts, check four things before any T1 run" is followed by seven items. Change it to "seven things", or drop the count.
>
> **One claim I cannot verify here.** §5.6 says the CPU path of `autoresearch_fixedtokens` "already uses a sealed memfd". That is a statement about the port kit, outside this unit; it belongs to the port-kit review.
>
> ## For the regenerated record
>
> - Cover rounds 1–8.
> - Add the third open point (the `autoresearch_fixedtokens` exception, report §5.6).
> - Use Code-Commit `68cdd1a`.

---

## Open points for the author

The report's section 5 lists what this unit does not close. Three of them need the author's decision or action before T1
or RL:
- the infrastructure-log-pattern class: an RL reward must not treat it as neutral without an author decision;
- the census must commit `frozen_pin_sha256` for each node;
- `autoresearch_fixedtokens` sets `shared_dev_shm` for CUDA IPC, so its runs are always `effective: false` and the
  interim rule (every diff read) would apply to it indefinitely: accept the exception for T1 with disclosure, or
  require a memfd-only path for that node.

Two more depend on the GPU host and are tested only by the kits' GPU smoke on Ada: CUDA IPC under the PID namespace,
and the label hosts' conditions (user namespaces, `ptrace_scope`, a delegated cgroup, a non-root uid).

---

Code-Commit: 68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e
Verdict: ACCEPTED

Accepted commit: `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` (round 8).
