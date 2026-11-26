# TASL-7 rename capability probe — candidate, 7 November 2026

AI-assisted (Codex). **ENGINEERING_ONLY proposal; not executed, not independently reviewed, not B1 readiness or launch approval.** The author explicitly allowed site engineering on TASL-7 subject to no preemption, strict no deletion, and the existing B1 gates; the recent instruction permits continuing despite observed unrelated agents but does not permit touching others' work. This script may be considered only after a fresh independent reviewer accepts the exact bytes and the operator satisfies the conditions below. Do not use it to resolve a formal B1 STOP or retry a stopped probe.

## Scope and retained objects

Script `tasl7_rename_probe_20261107/probe.sh` SHA-256 `87fc27bef6583a09bcb1314ee539072c5b460d0d857b003f34bec9530536ecca` is a fixed single-use test. The shell checks TASL-7/UID/home, reads all three complete STATUS files with before/after hashes, lists the existing lock directory, and requires the specified GPU UUID, observed utilization at most 5%, and no listed compute application. The embedded Python checks both evidence markers immediately before creation; marker absence and GPU observations are point-in-time, not host reservations. It does not acquire the GPU flock or run GPU work. Before invocation, the operator must perform and inspect a separate fresh full STATUS, nonpreemption and occupancy census, and resolve every applicable STOP and actual operator coordination question. The program prints STATUS but does not parse its prose or prove that no other person owns or will start work. Do not infer that the preconditions hold from the 09:00 snapshot.

Python opens root and the explicit `/home/dowling/exam-x/work` components by directory FDs with `O_NOFOLLOW`, checks owners and named/opened identities, and binds the actual work directory to `/proc/self/fdinfo` mount ID and `/proc/self/mountinfo`. The script requires the observed filesystem to be ext4, as the prior point-in-time site observation showed, but the label does not itself prove storage locality, durability, or error atomicity. It then exclusively creates exactly one owned private directory, `/home/dowling/exam-x/work/rename_capability_probe_20261107_7d322b6c3a1e4c2f`, and two exclusive regular test files. Their initial bytes, SHA-256 and inode identities are printed. It calls actual libc `renameat2` with `RENAME_NOREPLACE` against an existing destination and requires `EEXIST` with both files unchanged; then moves `a` to absent `c` with NOREPLACE, and exchanges `b` and `c` with `RENAME_EXCHANGE`, verifying inode and bytes after each operation. It checks the probe mount ID equals the work mount ID, and fsyncs files, the work directory and the probe directory at the stated points. It retains both data files under `b` and `c` on normal completion, as well as the directory and all partials on failure. There is no intentional file overwrite, deletion, model, GPU workload, server, signal or cleanup.

These checks only show the result of the particular syscalls on this mount at this time under cooperative stable paths. The script verifies inode/bytes in its process but does not simulate a power failure, verify crash recovery, rule out a concurrent same-UID path replacement, establish parent/guardian lease or bind any production B1 files. A short filesystem operation can interact with concurrent activity; the operator must not touch or preempt anyone else's process or files. SSH, system utilities, Python internals and other concurrent host effects are not independently traced.

## Operator prerequisites, command and STOP

The independent reviewer must assess the entire source, including ancestor checks, exclusive creation, absence checks, collision errno, identity/bytes checks, rename flags, mount matching, fsync failures, cleanup/close error paths, and whether any operation can overwrite or delete. The current script's `bash -n` and embedded Python `ast.parse` checks passed locally; those are syntax checks only and are not a behavioral test or review. Exact script digest must be rechecked in the committed clean operator checkout against the independently reviewed digest immediately before use. If the work tree, source, host, account, mount, markers, occupancy, known STOP, ownership or coordination is ambiguous, do not invoke it.

Only after review and a fresh operator preflight, the following Bash capture uses a new local-only fixed path and noclobber. It opens the capture *before* SSH, so a collision fails before any host action. It captures combined output and SSH status; exit 255 or lost/partial transport makes the remote outcome ambiguous. It does not create a remote transcript or delete the local capture. Run at most once; preserve partial output and the entire remote probe directory on any failure. Do not use a different probe name, retry, signal, clean up or proceed to B1 after any probe STOP or ambiguous interruption; an operator must inspect the owned scene and seek the author's instructions as appropriate. One site check cannot establish future availability.

```bash
set -C
capture=/private/tmp/tasl7-rename-capability-20261107-7d322b6c3a1e4c2f.txt
exec 3>"$capture" || exit 1
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' \
  < docs/r1/proposals/tasl7_rename_probe_20261107/probe.sh >&3 2>&1
ssh_status=$?
printf '\nSSH_EXIT_STATUS=%s\n' "$ssh_status" >&3
exec 3>&-
shasum -a 256 "$capture"
exit "$ssh_status"
```

The operator records UTC invocation time, exact command, reviewed SHA, GPU UUID, local complete output path and SHA, actual SSH status and disposition. A fresh independent reviewer checks the result and retained evidence before any later claim. Raw output includes complete project STATUS; any separate census with other users' arguments stays local and is not pushed. Site behavior, the full B1 checkout/pin, complete tests, real-worker determinism, real author gate and reviewed handover are separate prerequisites. This proposal leaves all of them STOP.
