# Harness isolation unit for Track G (R1-HARNESS-ISOLATION), 17 November 2026

**Status.** This unit is ENGINEERING_ONLY: nothing was measured and no label run is touched. The independent review ran
six rounds and accepted commit `eac68466` in round 3, closing the follow-ups in rounds 4–6. The record is
`docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md`. Written by the Mac-desk agent (Claude), AI-assisted.

**Authority.**
- PLAN row R1-HARNESS-ISOLATION (on `main` `50176481`): before any T1 label run and any RL training, editable code runs
  in a separate process, the metric log is append-only, a timeout kills the whole cgroup, and a run with more than one
  metric line is refused.
- PLAN row R1-TRACKG-PORT-DECISIONS (4): the node timeout is 3 × the census baseline time, and a timeout is a failure of
  the proposal, not an infrastructure rerun.
- Queue of 17 November 2026, item (1).

**Harness branch.** `mac-harness-isolation-20261117` of `autoresearch_harness`, based on `r1-local-trackg-v2-20261114`
@ `717ad835`, with tip `eac684667856034a8e4f3df027ae3bd5c4e26d5a`. It touches 14 files (+2,590 / −48), all under
`src/autoresearch/trackg/`, `configs/trackg/node_template.yaml` and `tests/trackg/`; no base (T0) file changes.

- `033b7ad` trackg: harness isolation unit (R1-HARNESS-ISOLATION) and timeout = proposal failure (R1-TRACKG-PORT-DECISIONS (4))
- `99dba0e` review round 1: worker sandbox, pinned frozen files, elapsed timeout, host conditions
- `0b2c892` review round 2: allow-list root for the worker, read-only frozen files, own session, no cgroupfs
- `c5d2358` NumPy imported lazily in the node library (accepted in round 3)
- `be7734e` round 3 follow-ups: single-threaded launcher, allow-listed worker environment, private `/dev/shm`
- `1950d4b` round 4 notes: credential-like names dropped, `shared_dev_shm` recorded as an exception
- `eac6846` round 5 note: `TOKENIZERS_PARALLELISM` kept by name; the environment test checks every name

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

A Track G campaign refuses a node without this block unless the node gives `unisolated_reason`. That reason is recorded
and is meant only for the legacy fixtures.

## 2. How an isolated run works

**Two processes.** The runner starts `[python, -s, entry, *args]` itself, with no shell. The entry is the node's frozen
*parent*: it holds the data, the budget loop and the metric. The parent starts the editable code in a *worker* process
and computes the metric from the worker's answers, so the metric code never shares a process with editable code.

**Result channel.** The runner listens on an abstract Unix socket with a random name (`AR_RESULT_SOCKET`). It accepts
one connection, and only from the parent's own pid (checked with `SO_PEERCRED`). The metric, and for test-scored nodes
the test metric, is read **only** from this channel. The run is `divergent` if:
- the channel holds no metric line or more than one (`multiple_metric_lines`), or more than one test-metric line;
- any line of the run's own output matches the metric regex (`metric_line_in_run_output`);
- the channel overflows 64 KiB or errors.

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
- a private `/tmp` (8 GiB tmpfs);
- `/sys` without any cgroup file system;
- `/dev`, with a private `/dev/shm` unless `shared_dev_shm` is set.

After `pivot_root` the old root is detached and the new root made read-only. PID 1 of the new PID namespace mounts a
fresh `/proc`, drops every capability, sets `no_new_privs` and execs the worker in its own session. The worker gets an
allow-listed environment: `AR_*`, CUDA and framework prefixes, `PATH`, `PYTHONPATH`, the locale and
`TOKENIZERS_PARALLELISM`. Any prefix-admitted name containing TOKEN, KEY, SECRET, PASSWORD, PASSWD, CREDENTIAL, AUTH,
COOKIE or SESSION is dropped, so the campaign's API keys and `HF_TOKEN` do not reach it.

As a result the worker:
- cannot see or signal the runner or the parent;
- has no network;
- cannot reach a daemon's socket outside its root;
- cannot read the runs tree (other runs' results), the incumbent, the kit, the home directory or the Python
  installation outside its read-only binds;
- cannot change its own frozen files;
- leaves nothing behind, because the kernel kills the whole namespace when PID 1 exits.

**Non-dumpable parent; outside interference is a STOP.** The runner and the parent mark themselves non-dumpable, so
`/proc/<pid>/fd`, `pidfd_getfd` and `ptrace` need privilege. At the accept the runner requires the parent's `TracerPid`
to be 0 and the parent to be non-dumpable. Otherwise the record is written and the runner raises `IntegrityError`, a
STOP: a process outside the run interfered.

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
  example because the runner was stopped meanwhile, is still a timeout. This holds in the isolated and the plain runner.

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

The record's `isolation` block holds:
- `effective`, which is true only with no waiver, no exception, a non-root uid, a cgroup and the sandbox;
- `waivers` and `exceptions` (`shared_dev_shm`);
- `worker_sandbox`, `euid`, `ptrace_scope`, `nsdelegate`, the cgroup record;
- `log_intact`, `result_channel_sha256`, `frozen_files_checked`;
- `parent_traced_by` and `parent_dumpable_at_accept`;
- `limits`, the not-closed list of §5.

**For the experiment agent on Ada / TASL-7.** This development host is a root container, so the tests run with the
`root` and `ptrace_scope` waivers, plus one test as uid 65534. On the label hosts, check four things before any T1
run:
1. Unprivileged user namespaces are enabled. Ubuntu 24.04's AppArmor `kernel.apparmor_restrict_unprivileged_userns=1`
   blocks them for unconfined programs and needs a profile or the sysctl.
2. `ptrace_scope` ≥ 1.
3. A delegated cgroup v2 subtree is available: a systemd user slice or `systemd-run --user --scope -p Delegate=yes`.
4. The runs do not run as root.

Any T1 label run whose record says `effective: false` must be disclosed with its waivers.

## 4. Tests

- `tests/trackg` on `eac6846`: **200 passed, 1 failed**. The failure is `test_trackg_t0_identity::test_manager_proposal_v1_…`,
  which fails identically on the base `717ad835` in this environment.
- `test_trackg_isolation.py` has 25 tests, using a fake node (`isolated_fixture.py`) whose modes attack the run:
  forged metric lines on stdout and through `/proc` (also as an unprivileged uid), a tampered log, edited frozen files,
  a tampered kit or incumbent, an escaped daemon, `kill(0)`, socket and cgroupfs access, environment leakage, a
  `/dev/shm` stash, and a runner stopped past the timeout.
- The reviewer wrote its own probes (33 attack scripts in `/tmp/hisorev/probes*/`), including an outside tracer early,
  late and evading the check, a planted `.pth`, a connection to an outside daemon, writes to frozen files, pid
  hopping and memfd shrinking. In round 4 (`be7734e`) it re-ran them all: every one failed or ended in an integrity
  STOP. Rounds 5 and 6 changed only the environment filter and the record, and the reviewer re-ran the probes that
  filter affects.
- **Full harness suite** (`tests`, `--continue-on-collection-errors`, Python 3.12): base `717ad835` and `eac6846` give
  the **same 65 failing or erroring tests**: environment failures (missing optional packages, the t0 identity test) and
  one collection error, `tests/test_legacy_noop_skip.py`.

## 5. Threat model after this unit (updates the port kits' threat model, READY 56–58)

**Closed by this unit:**
- forged metric lines from editable code (another process, another channel);
- a second metric line;
- a rewritten log;
- a run surviving its timeout;
- a changed frozen file or kit;
- a tracer from outside;
- other runs' results;
- the campaign's credentials.

**Still open, stated in every record's `isolation.limits`:**
1. **Data and labels are readable.** The worker can read every file that its read-only binds expose. That includes the
   node's data directory, so the validation and test labels too, wherever a node keeps them there. A read-only mount
   does not hide them. The port kits describe per node what the worker receives through the channel and what lies on
   disk; that report must state this limit for each node.
2. **The budget accounting is partly in the worker.** The worker trains, so loss lines and work done per step stay in
   the editable process. The parent fixes the step or token count and the batches it hands out, but not the compute
   spent per step.
3. **Answers can differ from a fixed model.** The worker can answer evaluation requests differently from training
   requests. The kits' probes (the causality probe and repeat checks) narrow this; they do not close it.
4. **Infrastructure log patterns.** The run's output can contain an infrastructure log pattern, which makes the run an
   `infrastructure_failure` (rerun, not registered as evaluated). **Author decision needed before RL:** an RL reward
   must not treat that class as neutral.
5. **CUDA IPC under the PID namespace is untested.** This host has no GPU; only the kits' GPU smoke on Ada exercises it.
6. **`shared_dev_shm` reopens a channel.** `autoresearch_fixedtokens` needs the host `/dev/shm` for torch's CUDA IPC
   reference counters, so its worker can keep state there between runs. Its runs record the exception and
   `effective: false`.
7. **The census must commit `frozen_pin_sha256`.** The pin is taken from the kit as it is when a runner or campaign
   starts, so a kit changed before a later campaign is caught only by comparing that campaign's `frozen_pin_sha256`
   with the census's.
8. **`/dev` is the host's** (with a private `/dev/shm`). Device nodes are reachable as the run's uid, including the GPU
   nodes the run needs; a minimal `/dev` was left as a note.
9. **The parent's environment and Python installation are trusted** as the run's uid left them before the campaign.
   The worker cannot write them; another process of the same uid outside the run could.

Until the kits are deployed with `effective: true` on the label host, the PLAN's interim rule stays in force: the
review of declared edits and the S1 audit read every diff.
