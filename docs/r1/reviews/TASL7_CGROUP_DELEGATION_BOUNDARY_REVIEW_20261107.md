# Independent pre-execution review: TASL-7 cgroup delegation boundary — 7 November 2026

**Verdict: ACCEPTED for the exact read-only script and capture command below, conditional on a fresh complete operator preflight and the stated stable-path/cooperative assumptions.** Reviewed proposal commit `372b2ae7`, `docs/r1/proposals/tasl7_cgroup_delegation_boundary_20261107/inspect.sh`, SHA-256 `a5dc93b1cc5fea1f5e09c8c63443915cb285efe9d4dbf58e896698e16db837c8`. The report and script had not been executed. I did not access TASL-7, run the script or tests, send signals, delete, or overwrite files. This approval is for observation only, not for a cgroup creation, process migration, systemd change, freezer probe, or B1 launch.

## Source and scope

The combined candidate's `_parent_dir()` reads its own `/proc/self/cgroup`, requires one canonical unified `0::` membership, traverses the cgroup v2 mount by no-follow directory descriptors, and rejects a current cgroup directory whose owner differs from the process UID (`r1/exam/b1_cgroup.py:57–75`; reviewed file SHA-256 `279272a443902b6688c9d3ecbf968f0500fc339985b9c48536275c493d059818`). It has no caller-selected parent override. An owned directory elsewhere alone therefore does not pass that gate. Under the [kernel's cgroup-v2 delegation rules](https://docs.kernel.org/admin-guide/cgroup-v2.html), an unprivileged migration requires write permission on the destination and the common ancestor's `cgroup.procs`; the proposal correctly presents failure as an inference if the relevant permission is absent, not an observed migration. The [systemd delegation guidance](https://systemd.io/CGROUP_DELEGATION/) describes the single-writer and explicit delegation boundaries; it does not establish that this project's use of the user's existing manager subtree is authorized. An xattr observation by itself cannot establish present-day site policy or subdelegation ownership.

The exact script verifies TASL-7, UID 1011 and home; reads the caller's unified membership, stats only `/sys/fs/cgroup`, `user.slice`, `user-1011.slice`, and `user@1011.service`; reads the named `cgroup.type` and `cgroup.subtree_control` controls, and reports ordinary `-w` checks on two `cgroup.procs` files. It checks final components for symlinks and reads no cgroup PID lists. Python is started with `-I -S -B` solely to read `user.delegate`; every `OSError` is reported as `NOT_CHECKABLE`, not an absence claim. No intentional remote create, write, rename, delete, cgroup membership change, service action, model, or GPU workload appears. This is source review, not a trace of SSH, system utilities, incidental host effects, or concurrency. The path checks do not bind inode identities across reads and assume stable cooperative ancestry; `test -w` and file metadata are point observations, not an effective migration probe or proof of delegation.

## Mandatory operator preconditions and exact capture

Before invocation, the operator must independently inspect a fresh complete set of applicable STATUS files, host and identity, GPU and compute-app census, relevant process/nonpreemption census, and work-disk capacity. Do not run if any applicable STOP, conflicting ownership, unexpected output, or lack of scoped authority is present. Confirm the committed checkout is clean and the exact script SHA above; confirm the following capture name has not been used. Use `/bin/bash` from that checkout, with no terminal allocation. This exact single invocation preserves stdout, stderr and the SSH status in an exclusively created local file; retain the file on all errors. It does not retry a probe or change any host state.

```bash
set -C
capture=/private/tmp/tasl7-cgroup-boundary-20261107-unique-d48f6.txt
if exec 3>"$capture"; then :; else
  printf '%s\n' 'STOP: capture exists or cannot be created; SSH not invoked' >&2
  exit 1
fi
if ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' \
  < docs/r1/proposals/tasl7_cgroup_delegation_boundary_20261107/inspect.sh >&3 2>&1; then
  task_ssh_status=0
else
  task_ssh_status=$?
fi
if printf '\nSSH_EXIT_STATUS=%s\n' "$task_ssh_status" >&3; then :; else
  printf '%s\n' 'STOP: status write failed; retain capture' >&2
  exit 1
fi
if exec 3>&-; then :; else
  printf '%s\n' 'STOP: capture close failed; retain capture' >&2
  exit 1
fi
if shasum -a 256 "$capture"; then :; else
  printf '%s\n' 'STOP: capture hash failed; retain capture' >&2
  exit 1
fi
exit "$task_ssh_status"
```

Afterward inspect the complete output, footer, identity and all STOP/NOT_CHECKABLE values; a zero exit by itself is not evidence that `user.delegate` was readable, the session membership is reusable, or migration is permitted. Preserve the capture locally, especially if it identifies other user-owned paths. Capture collision, failed write/close/hash, SSH failure, incomplete output, or inconsistent or unstable paths is STOP with the partial record retained. Obtain a fresh independent review of the result before relying on it. A successful observation remains no authority to enter or manipulate the existing service subtree; the site operator must establish an attributable supported delegation and review an exact safe launch procedure. If no authorized scope can be established, an appropriate administrator must provide guidance or delegation; response time is unknown. B1's independent tests, final pin/checkout, gate and handover remain separate.
