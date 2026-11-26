# TASL-7 single-process capability result — 7 November 2026, 09:52 CET

AI-assisted (Codex). **ENGINEERING_ONLY, not B1 launch or a server/worker lease qualification.** The author explicitly authorized continuing host work, subject to the non-preemption, no-deletion and B1 gates recorded in PLAN §10. The exact probe script was reviewed and accepted in `TASL7_SINGLE_PROCESS_CAPABILITY_PROBE_R2_REVIEW_20261107.md`; this result needs its own independent review. Script SHA-256 `f8d90cd6c39729e69ef663207c2f609f4404bdb4bd1c4bbf0eecc3608281c266`, B1 feature checkout `2ec16932`.

At 08:52:55 UTC (09:52:55 CET), this exact local command sent that script through SSH and captured its output in a previously absent local file. The SSH command returned **0**; output SHA-256 `c539d7cde1f6b38554e75de4711e72fe1bc41546d8fd5a4bdc95d2b2f894acb9`, retained at `/private/tmp/tasl7-capability-20261107-0953.txt`. The full capture includes historical STATUS text and remains local; no other users' process arguments were requested by this probe.

```bash
output=/private/tmp/tasl7-capability-20261107-0953.txt
if test -e "$output" || test -L "$output"; then printf 'STOP: capture path exists\n' >&2; exit 1; fi
set -C
if ssh -T -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' < docs/r1/proposals/tasl7_capability_probe_20261107/probe.sh > "$output" 2>&1; then
  result=0
else
  result=$?
fi
shasum -a 256 "$output"
printf 'ssh_exit=%s\n' "$result"
exit "$result"
```

The captured script identified TASL-7 and UID 1011, listed `~/r1_locks` and read the complete three expected STATUS files before the lock test. Their begin/end SHA-256 values matched within the capture: exam `65661d28abfc301ac155d9ae7a87f570f196753e1a8b98a1622129915307b1b6`, Track P `dd1c19142ee869568b4a4ba4360ceb878a1d6253bb7ee139da15cac232189317`, Track S `97b7217a49d47d857083ee695d96eeb5fd5a9cf1a275b4f4de0d2dc9a7922faf`. The GPU query recorded `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, 0% utilization and an empty compute-app PID list; it did not measure GPU memory in this invocation.

The probe's Python was `/usr/bin/python3`, version 3.10.12. It recorded lock-directory `(device, inode, uid, nlink, type)` `(66306, 56244535, 1011, 3, 16384)` and the existing lock `(device, inode, uid, nlink)` `(66306, 56251186, 1011, 1)`. It reported `flock_acquire: PASS single-process point-in-time`, `flock_unlock: returned successfully`, `kcmp_self_same_fd: PASS rc=0 errno=0`, and `pidfd_self: PASS pid_matches=True ready=False`, followed by descriptor-close/probe-complete output. SSH returned successfully. This is a brief transient lock observation and a self-comparison only: it is not a held lease, proof of ancestor-child OFD identity, actual worker Python binding, server descriptor inheritance, cgroup delegation, no concurrent host activity, or durable exclusive access.

The reviewed script intentionally performs no remote file creation, unlink, rename or process signal and starts no server, model, GPU workload or campaign. A short-lived advisory flock could affect a concurrently starting cooperative launcher; the query and marker checks are snapshots. Coordination with relevant operators beyond those observed snapshots was not independently established. System utilities, SSH, Python internals, logging and concurrent host changes were not independently traced, so absence of any incidental host side effect is not asserted. No formal B1 runner, guardian, author gate or anchor gate was invoked, and no formal B1 STOP/retry occurred.

**Remaining B1 STOP:** exact combined code and its independent review, strict no-deletion/STOP behavior, actual worker/server OFD and process/endpoint identity, Python binding, determinism, final checkout/note and real gate, site cgroup/filesystem qualification and safe handover remain outstanding. The operator must repeat all applicable checks at launch time; the local engineering/review effort and site-dependent time remain open.
