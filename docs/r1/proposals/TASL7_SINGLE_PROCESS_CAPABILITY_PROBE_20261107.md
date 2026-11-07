# TASL-7 single-process capability probe — draft for independent review

AI-assisted (Codex). **Not reviewed, not executed, and not B1 preflight or launch authority.** This proposed ENGINEERING_ONLY probe answers a limited question: can a single host Python process briefly obtain and release the existing cooperative GPU flock, and what do self-pidfd/self-kcmp observations return? It neither starts a server nor invokes a model, GPU workload or campaign. The author allowed host checks on 7 November, and later said “你继续执行，不用管他。只要能跑就去跑”; non-preemption, no-deletion and the remaining B1 gates still apply. The exact separately reviewed host handover remains required before any real B1.

The proposed source is `docs/r1/proposals/tasl7_capability_probe_20261107/probe.sh`, SHA-256 `5c54860556b9e85f4ad4d4627c88e6c06ac00babde4ad8992a06985d46319157`. A fresh independent reviewer must assess the exact script and its scope before the coordinator considers executing it. A real execution also needs a fresh author-allowed host action, visibility of all relevant STATUS/locks, no conflicting actual work, and a unique local output name; the author has not waived those site/protocol conditions. If tool side effects, command provenance or the live host state cannot be established, do not execute.

## Intended execution, not an instruction to launch

Run from the checkout carrying the exact reviewed script, using a new local output path. The preliminary `-e` and `-L` checks plus Bash noclobber prevent ordinary accidental overwrite but are **not atomic exclusion against a same-UID concurrent writer**. Before use, independently review an exclusive local-capture mechanism or establish the local cooperative ownership assumption; never overwrite or remove an existing path. The literal candidate command is:

```bash
output=/private/tmp/tasl7-capability-20261107-UNIQUE.txt
if test -e "$output" || test -L "$output"; then printf 'STOP: capture path exists\n' >&2; exit 1; fi
set -C
if ssh -T -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' \
  < docs/r1/proposals/tasl7_capability_probe_20261107/probe.sh > "$output" 2>&1; then
  result=0
else
  result=$?
fi
shasum -a 256 "$output"
exit "$result"
```

Replace `UNIQUE` with a fresh run-specific value before review/execution; never reuse a previous capture or STOP. Use the actual terminal tool's exit result and preserve the full local stdout/stderr and its SHA-256. An authorized operator must independently record the local command, time, script SHA, output SHA, result, and any STOP; a fresh reviewer checks that report. The script intentionally prints three full STATUS documents before any lock acquisition, so captures may contain user data; avoid publishing another user's process arguments or other sensitive data. There is no remote output redirect, `touch`, write-open, rename, unlink, rmtree, or process signal in the proposed script. The `ssh`, `nvidia-smi`, Python interpreter, standard library and system services may themselves have side effects; their absence is not established by reading this script and must not be claimed without evidence.

## Exact checks and limits

1. The shell checks short host `TASL-7`, UID `1011`, expected home, and lists `~/r1_locks`. It reads and SHA-256-checks the complete STATUS files in the three previously observed exam, Track P and Track S checkouts; missing/unreadable/linked files or a before/after digest difference STOP. These locations and currentness must be checked at execution. Matching hashes are not an atomic snapshot or proof that no later change occurs.
2. It refuses a present or dangling-symlink `trackx_evidence.active` or `trackp_evidence.active` marker, then records the specified GPU UUID, utilization, and the compute-app PID query. An unexpected UUID, nonnumeric or >5% utilization, any listed compute app, or a failed command stops before flock. Marker and GPU checks are snapshots and cannot prove exclusive future occupancy, identify invisible workloads, or prevent a new concurrent start. The script performs no signal or GPU compute. Short nonblocking lock acquisition may nevertheless affect a concurrent cooperative launcher; coordinate with the relevant operators before use and never preempt a running job.
3. `python3 -I -S -B` prints its actual interpreter/version and runs a **single process with no fork or exec**. It lstat-checks the existing `gpu0.lock` as a same-UID, one-link, regular file, opens it `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` without `O_CREAT`, verifies named/open `(device, inode, owner, nlink, type)`, then attempts `LOCK_EX|LOCK_NB`. An unavailable lock is STOP, with no retry. If acquired, a `finally` calls `LOCK_UN` and the outer `finally` closes the descriptor; a successful unlock call is reported, and process termination closes its sole descriptor under the cooperative model. These operations change transient flock state but do not write lock bytes. A crash, blocked process or unforeseen inherited descriptor must not be reported as a successful release without evidence.
4. **Only after unlock**, the same Python process invokes Linux x86-64 `kcmp(KCMP_FILE)` on the same process and same FD and attempts `os.pidfd_open` on itself, reading its own fdinfo and checking the pidfd is not immediately readable. Unsupported ABI STOPs; syscall denial, absence or unexpected results are `NOT_CHECKABLE`, not PASS. These self-checks do not prove ancestor-to-child `kcmp`, inherited lock open-file-description continuity, server descriptors, actual worker Python binding, cgroup/freezer delegation, or any other process's identity. A `probe_complete` line is printed after descriptors are closed, just before returning; it is not proof the remote interpreter has exited until SSH itself returns.
5. The external shell utilities and Python process are normal test-owned process launches. No synthetic child is forked by the Python probe and no timeout signal or process termination is requested; if a utility hangs, do not kill a process whose ownership and current identity are unproved, and report the state. OS-visible job/agent activity, filesystem and GPU state can change after the census. No result from this probe permits touching another operator's work or preempting their job.

This narrow probe intentionally does not attempt the ancestor/child `kcmp` or real-worker determinism tests. Their exact Python interpreter, child lifetimes, inherited FDs, robust STOP preservation, no-deletion behavior, and host execution inputs need their own concrete implementation and independent review. To unblock this proposed probe: a fresh independent reviewer reviews the script, output capture and limits; an authorized operator establishes current no-preemption coordination, known STATUS paths and output ownership, then executes once if those conditions are met. Site response and coordination effort are unknown. A successful result is **engineering-only** and does not close the formal B1 lease/server descriptor or worker tests.
