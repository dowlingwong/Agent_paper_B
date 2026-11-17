# Harness isolation unit for Track G (R1-HARNESS-ISOLATION), 17 November 2026

**Status.** This unit is ENGINEERING_ONLY: nothing was measured and no label run is touched. Independent review:
round 3 accepted `c5d2358` with follow-ups; rounds 4–6 accepted the follow-ups, ending at `eac6846`; round 7 checked
this report and asked for corrections and a text-only change to the record's limits list (`68cdd1a`), which round 8
confirmed. The record is `docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md`. Written by the Mac-desk agent
(Claude), AI-assisted.

**Authority.**
- PLAN row R1-HARNESS-ISOLATION (on `main` `50176481`): before any T1 label run and any RL training, editable code runs
  in a separate process, the metric log is append-only, a timeout kills the whole cgroup, and a run with more than one
  metric line is refused.
- PLAN row R1-TRACKG-PORT-DECISIONS (4): the node timeout is 3 × the census baseline time, and a timeout is a failure of
  the proposal, not an infrastructure rerun.
- Queue of 17 November 2026, item (1).

**Harness branch.** `mac-harness-isolation-20261117` of `autoresearch_harness`, based on `r1-local-trackg-v2-20261114`
@ `717ad835`, with tip `68cdd1a` (full sha in the review record). It touches 14 files, all under
`src/autoresearch/trackg/`, `configs/trackg/node_template.yaml` and `tests/trackg/`; no base (T0) file changes.

- `033b7ad` trackg: harness isolation unit (R1-HARNESS-ISOLATION) and timeout = proposal failure (R1-TRACKG-PORT-DECISIONS (4))
- `99dba0e` review round 1: worker sandbox, pinned frozen files, elapsed timeout, host conditions
- `0b2c892` review round 2: allow-list root for the worker, read-only frozen files, own session, no cgroupfs
- `c5d2358` NumPy imported lazily in the node library (accepted in round 3)
- `be7734e` round 3 follow-ups: single-threaded launcher, allow-listed worker environment, private `/dev/shm`
- `1950d4b` round 4 notes: credential-like names dropped, `shared_dev_shm` recorded as an exception
- `eac6846` round 5 note: `TOKENIZERS_PARALLELISM` kept by name; the environment test checks every name
- `68cdd1a` round 7: the record's limits text brought in line with the allow-list sandbox (text only)

The port kits that use this core (the three suite branches) form a separate unit with their own report,
`TRACKG_PORT_ISOLATION_20261117.md`, and review.

## 1. What a node declares

A node opts in with an `isolation` block in its `trackg_node/v1` spec:

```yaml
isolation:
  entry: run_fixed_budget.py      # frozen parent; never imports editable code
  args: ["--steps", "{budget}"]
  env: {}                         # extra variables for the parent (and, filtered, for the worker)
  shared_dev_shm: false           # true only for CUDA IPC (autoresearch_fixedtokens); recorded as an exception
```

The v2-diff campaign (`run_v2_diff_campaign`) refuses a node without this block unless its caller passes
`unisolated_reason`, which is recorded; that argument is meant only for the legacy fixtures. A bare
`WorkingCopyRunner` runs a node without the block, unisolated, without refusing. **The census and T1 drivers must
enforce the same gate; that is left to the unit that writes them.**

## 2. How an isolated run works

**Two processes.** The runner starts `[python, -s, entry, *args]` itself, with no shell. The entry is the node's frozen
*parent*: it holds the data, the budget loop and the metric. The parent starts the editable code in a *worker* process
and computes the metric from the worker's answers, so the metric code never shares a process with editable code.

**Result channel.** The runner listens on an abstract Unix socket with a random name (`AR_RESULT_SOCKET`). It accepts
one connection, and only from the parent's own pid (checked with `SO_PEERCRED`). The metric, and for test-scored nodes
the test metric, is read **only** from this channel. The run is `divergent` if:
- the channel holds more than one metric line (`result_channel_metric_lines`) or more than one test-metric line
  (`result_channel_test_metric_lines`);
- any line of the run's own output matches the metric regex (`metric_line_in_run_output`);
- the channel overflows 64 KiB (`result_channel_overflow`) or errors (`result_channel_error`).

A channel without a metric line gives the ordinary `no_metric_at_budget`. (For plain, unisolated runs, more than one
metric line in the output is `multiple_metric_lines`.)

**Append-only log.** The run's stdout and stderr go to a pipe that the runner reads. Only the runner appends to
`run.log` (`O_APPEND`, `O_NOFOLLOW`), and it keeps a running sha256. If the file on disk differs from what the runner
wrote, the run is `divergent` (`log_tampered`). The run is classified from the verified bytes, not from the file. The
runner's own last line records the sha256 of the result channel.

**cgroup.** The run joins a fresh cgroup v2 directory under `limits.cgroup_parent`. On a timeout and after every exit
the runner writes `1` to `cgroup.kill` (falling back to SIGKILL of every listed pid) and removes the directory. The
runner is also a child subreaper and kills any child it did not have before the run.

**Worker sandbox.** The parent starts the worker through a launcher: a fresh, single-threaded `python -I -S` running the
node library. A fork of a threaded parent can deadlock, and `unshare(CLONE_NEWUSER)` refuses a multithreaded caller;
the kit smokes ran into both. The launcher creates new user, mount, PID, network and cgroup namespaces and builds a new
root containing only an allow-list:
- read-only: the system directories, the run interpreter and its `sys.path`, the data, and the determinism shim;
- writable: the working copy, except its frozen files, which are mounted read-only again;
- a private `/tmp` (an 8 GiB tmpfs; like the private `/dev/shm` it is bounded in practice only by the run cgroup's
  memory limit, so the run should have one);
- `/sys` without any cgroup file system;
- `/dev`, with a private `/dev/shm` unless `shared_dev_shm` is set.

After `pivot_root` the old root is detached and the new root made read-only. PID 1 of the new PID namespace mounts a
fresh `/proc`, drops every capability, sets `no_new_privs` and execs the worker in its own session. The worker gets an
allow-listed environment:
- by name: `PATH`, `LANG`, `LANGUAGE`, `TZ`, `PYTHONPATH`, `PYTHONHASHSEED`, `SOURCE_DATE_EPOCH`,
  `TOKENIZERS_PARALLELISM`;
- by prefix: `AR_`, `CUDA_`, `NVIDIA_`, `CUBLAS_`, `CUDNN_`, `NCCL_`, `OMP_`, `MKL_`, `OPENBLAS_`, `PYTORCH_`,
  `TORCH`, `XLA_`, `JAX_`, `TF_`, `LC_`, `HF_`, `TRANSFORMERS_`, `TOKENIZERS_`, except any name containing TOKEN, KEY,
  SECRET, PASSWORD, PASSWD, CREDENTIAL, AUTH, COOKIE or SESSION;
- the sandbox's own: `HOME` and the cache directories inside the working copy, and the determinism record.

So the campaign's API keys and `HF_TOKEN` do not reach it.

As a result the worker:
- cannot see or signal the runner or the parent;
- has no network;
- cannot reach a daemon's socket outside its root;
- cannot reach the runs tree (other runs' results), the incumbent, the kit directory or the home directory. It does
  read its own working copy, which holds the kit's files, the frozen parent and node library included;
- can read the Python installation (bound read-only) but cannot write it;
- cannot change its own frozen files;
- leaves no process behind, because the kernel kills the whole PID namespace when PID 1 exits. Files can remain: in
  its working copy (kept under the run directory and never reused, since the incumbent snapshot is taken before the
  run) and, with `shared_dev_shm`, in `/dev/shm`.

**Non-dumpable parent; outside interference is a STOP.** The runner and the parent mark themselves non-dumpable, so
`/proc/<pid>/fd`, `pidfd_getfd` and `ptrace` need privilege. At the accept the runner requires the parent's `TracerPid`
to be 0 and the parent to be non-dumpable. Otherwise the record is written and the runner raises `IntegrityError`, a
STOP: a process outside the run interfered. The parent becomes non-dumpable only when it imports `ar_isolated`;
during interpreter start-up only Yama `ptrace_scope ≥ 1` keeps an unrelated process of the same uid from attaching.
Without it an early tracer could change the parent's memory and detach before the accept, unseen. So this relies on
`ptrace_scope ≥ 1`; with the `ptrace_scope` waiver the run is not effective.

**Frozen files and incumbent pinned.** When the runner or campaign is set up, it takes the sha256 of every file under
the node's frozen paths from the kit (the pin). Before the run the working copy must match the pin, and a campaign also
checks the incumbent's raw code-state hash. A mismatch is an integrity STOP: a ledger line `stop_integrity` and an
`IntegrityError`, not a proposal outcome. After the run the frozen files must be unchanged (`frozen_file_changed`).
Every record carries `frozen_pin_sha256`.

**Timeout (R1-TRACKG-PORT-DECISIONS (4)).**
- The timeout is `timeout_factor` × `measured_run_seconds`. The factor must be 3; any other value needs the
  `timeout_factor` waiver.
- A run past a **measured** timeout is `divergent`, reason `timeout`: the proposal failed and is not rerun.
- Only a **provisional** timeout (the census's first, measuring run) gives `infrastructure_failure`.
- Elapsed wall time on the runner's monotonic clock counts too: a run that ends by itself after the timeout, for
  example because the runner was stopped meanwhile, is still a timeout. A suspension of the whole host or batch job
  (an HTCondor suspend, say) therefore also counts as the proposal's timeout.
- These rules, factor 3 included, hold in the isolated and the plain runner.
- Under a measured timeout a **baseline** timeout is `divergent` and therefore stops the v2-diff campaign at once
  (`baseline_failed`): the census measured that baseline, so a timeout means the host or the node changed.

## 3. Host conditions and waivers

Before an isolated run the runner probes the host and refuses the run if a condition is missing. A named waiver in
`limits.isolation_waivers` (`name → reason`) overrides the refusal, and the waiver goes into the record.

| Condition | Waiver |
|---|---|
| a cgroup v2 parent the run's uid can write (`limits.cgroup_parent`) | `no_cgroup` |
| the run is not root | `root` |
| unprivileged user namespaces with mount, PID and network namespaces (the sandbox probe) | `no_worker_sandbox` |
| Yama `ptrace_scope` ≥ 1 | `ptrace_scope` |
| timeout factor 3 | `timeout_factor` |
| the run interpreter's `sys.path` holds no home directory, runs tree or ancestor of either | none: a hard `RunnerError` (a broad `PYTHONPATH` on the label host refuses every run) |

The cgroup must be v2 with `cgroup.kill`, which needs Linux ≥ 5.14.

The record's `isolation` block holds:
- `effective`, which is true only with no waiver, no exception, a non-root uid, a cgroup and the sandbox;
- `waivers` and `exceptions` (`shared_dev_shm`);
- `worker_sandbox`, `euid`, `ptrace_scope`, `nsdelegate`, the cgroup record;
- `log_intact`, `result_channel_sha256`, `frozen_files_checked`;
- `parent_traced_by` and `parent_dumpable_at_accept`;
- `limits`, the not-closed list of §5 as record text.

**For the experiment agent on Ada / TASL-7.** This development host is a root container, so the tests run with the
`root` and `ptrace_scope` waivers, plus one test as uid 65534. On the label hosts, check four things before any T1
run:
1. Unprivileged user namespaces are enabled. Ubuntu 24.04's AppArmor `kernel.apparmor_restrict_unprivileged_userns=1`
   blocks them for unconfined programs and needs a profile or the sysctl.
2. `ptrace_scope` ≥ 1.
3. A delegated cgroup v2 subtree is available: a systemd user slice or `systemd-run --user --scope -p Delegate=yes`.
4. The runs do not run as root.
5. The run interpreter's `sys.path` holds no home-directory or runs-tree entry.
6. A smoke run with the sandbox on shows `effective: true` in its record. This is the end-to-end check of items 1–4.
7. The GPU smoke, with the sandbox on, exercises CUDA IPC across the PID namespace (§5.5).

A missing condition is loud, not silent: the AppArmor case, for example, fails the sandbox probe and the run is
refused. Any T1 label run whose record says `effective: false` must be disclosed with its waivers and exceptions.

## 4. Tests

- `tests/trackg` on `eac6846`: **200 passed, 1 failed**. The failure is `test_trackg_t0_identity::test_manager_proposal_v1_…`,
  which fails identically on the base `717ad835` in this environment.
- `test_trackg_isolation.py` has 25 tests, using a fake node (`isolated_fixture.py`) whose modes attack the run:
  forged metric lines on stdout and through `/proc` (also as an unprivileged uid), a tampered log, edited frozen files,
  a tampered kit or incumbent, an escaped daemon, `kill(0)`, socket and cgroupfs access, environment leakage, a
  `/dev/shm` stash, and a runner stopped past the timeout.
- The reviewer wrote its own probes: 18 distinct scripts (16 probes and 2 helpers in `/tmp/hisorev/probes*/`, with
  per-round copies), about 25 attack modes. They include an outside tracer (early, late, evading the check), a planted
  user-site `.pth`, a connection to an outside daemon, writes to frozen files, pid hopping, memfd shrinking, `kill(0)`
  and `cgroup.kill`. Round 4 (`be7734e`) re-ran most of them. The user-site `.pth`, `symlink` and `pgstop` probes were
  last run in round 2, and `infra` and `cgkill_runner` in round 3. Every probe failed or ended in an integrity STOP
  except two, which succeed by design and are listed as open: the infrastructure log pattern gives
  `infrastructure_failure` (§5.4), and a fresh runner on a tampered directory gives ok 0.9999 (§5.7). Round 6 ran a
  mutation check of the environment test.
- **Full harness suite** (run by the coordinator, not the reviewer: `tests`, `--continue-on-collection-errors`, Python
  3.12): base `717ad835` and `eac6846` give the **same 65 failing or erroring tests**: environment failures (missing
  optional packages, the t0 identity test) and one collection error, `tests/test_legacy_noop_skip.py`. `68cdd1a`
  changes record text only; `tests/trackg` on it: 200 passed, 1 failed (the same t0 failure).

## 5. Threat model after this unit (updates the port kits' threat model, READY 56–58)

**Closed by this unit:**
- forged metric lines from editable code (another process, another channel);
- a second metric line;
- a rewritten log;
- a run surviving its timeout;
- a changed frozen file during a run, and a changed kit or incumbent within a campaign (before a later campaign or
  runner starts, see item 7);
- a tracer from outside, given `ptrace_scope ≥ 1` (otherwise waived and not effective);
- other runs' results;
- the campaign's credentials;
- the censoring routes rounds 1–3 found: killing the parent by signal (own session, PID namespace), through
  `cgroup.kill` (cgroupfs hidden), or by SIGBUS through a shrunk memfd (sealed). The infrastructure log pattern (item
  4) is the only route left by which a run can avoid being registered as evaluated.

**Still open** (as record text in `isolation.limits`, `68cdd1a`):
1. **Data and labels are readable.** The worker can read every file that its read-only binds expose. That includes the
   node's data directory, so the validation and test labels too, wherever a node keeps them there. A read-only mount
   does not hide them. The port kits describe per node what the worker receives through the channel and what lies on
   disk; that report must state this limit for each node.
2. **The budget accounting is partly in the worker.** The worker trains, so loss lines and work done per step stay in
   the editable process. In the port kits the parent fixes the step or token count, but not the compute spent per
   step.
3. **Answers can differ from a fixed model.** The worker can answer evaluation requests differently from training
   requests. The kits' probes (the causality probe and repeat checks) narrow this; they do not close it.
4. **Infrastructure log patterns.** The run's output can contain an infrastructure log pattern, which makes the run an
   `infrastructure_failure` (rerun, not registered as evaluated). **Author decision needed before RL:** an RL reward
   must not treat that class as neutral.
5. **CUDA IPC under the PID namespace is untested.** This host has no GPU; only the kits' GPU smoke on Ada exercises it.
6. **`shared_dev_shm` reopens a channel.** `autoresearch_fixedtokens` needs the host `/dev/shm` for torch's CUDA IPC
   reference counters, so its worker can keep state there between runs. Its runs record the exception and are
   **always** `effective: false`. **Author decision:** accept the exception for T1 with disclosure, or require a
   memfd-only path for this node (its CPU path already uses a sealed memfd).
7. **The census must commit `frozen_pin_sha256`.** The pin is taken from the kit as it is when a runner or campaign
   starts, so a kit changed before a later campaign is caught only by comparing that campaign's `frozen_pin_sha256`
   with the census's.
8. **`/dev` is the host's** (with a private `/dev/shm`). Device nodes are reachable as the run's uid, including the GPU
   nodes the run needs; a minimal `/dev` was left as a note.
9. **What lies outside the run is trusted** as the run's uid left it: the parent's environment, the Python
   installation, the data (the kits only make it read-only, which the owner can undo), the kit before the pin and the
   harness checkout. The worker cannot write any of these; another process of the same uid outside the run could.

Until the kits are deployed with `effective: true` on the label host, the PLAN's interim rule stays in force: the
review of declared edits and the S1 audit read every diff. For `autoresearch_fixedtokens` that means indefinitely,
unless the author decides as in item 6.
