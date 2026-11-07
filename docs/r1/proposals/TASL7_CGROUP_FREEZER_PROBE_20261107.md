# TASL-7 owned cgroup freezer probe — draft, 7 November 2026

AI-assisted (Codex). **DRAFT: no host access or probe execution has occurred. Independent review of the exact script and capture command is required before use.** This is ENGINEERING_ONLY, not B1 or experiment authorization. The author permitted TASL-7 engineering checks subject to preserving other operators, STOPs and all existing B1 gates. Only a freshly created, uniquely named cgroup and its one self-owned harmless child are in scope; no other process, GPU workload, model or server is touched.

## Why this check and its limits

The 08:42 UTC read-only census reported unified membership `0::/user.slice/user-1011.slice/session-61138.scope` and listed controllers; it did not test cgroup ownership, delegation or freezer (`TASL7_SITE_READONLY_20261107_0942.md`). Session membership may differ on a new SSH connection. Current B1 `_parent_dir` requires the *current* unified cgroup to be owned by the current UID, then creates a fresh root and worker leaf (`r1/exam/b1_cgroup.py:57–75,149–170,205–216`). The guardian writes the root `cgroup.freeze` and waits for `cgroup.events` frozen state (`r1/exam/b1_cgroup_guardian.py:24–33`); the bootstrap enrolls itself through inherited leaf `cgroup.procs` before a workload grant (`r1/exam/b1_cgroup_bootstrap.py:11–27`). This probe checks those kernel primitives with an unrelated test child; it does not run the actual guardian, bootstrap, server or worker, establish descriptor/OFD or GPU lease continuity, check `cgroup.kill`, prove descendant containment, prove process quiescence beyond the observed events, or qualify B1.

The script `tasl7_cgroup_probe_20261107/probe.sh`, SHA-256 `5fe5057bf15e9036e0ce53e0d53c0a37e2de773cc9b72d0832249529d06d306b`, verifies host/UID, prints the complete three STATUS files with before/after hashes and checks GPU UUID, observed utilization and compute-app census; an operator must separately inspect all current STATUS and a fresh nonpreemption/process census and disk capacity before any probe. It checks absence of the two evidence markers, opens its actual current unified cgroup through no-follow directory descriptors, verifies cgroup2 and owner, then exclusively creates `paper-b-cgroup-probe-20261107-a94ce1891ef94f93` and its `worker` leaf. Existing names, wrong owner, missing permissions/controls, changed state or any ambiguous result STOP. It opens root freeze/events and leaf procs/events; an owned `python3 -I -S -B` child joins the leaf itself and waits on an anonymous pipe, with no file creation or GPU work. Parent checks its pidfd and start tick, verifies `/proc/<pid>/cgroup`, waits for `populated=1`, requests freeze and observes `frozen=1`, confirms the same live child, thaws and observes `frozen=0`, releases the child by pipe, waits for exit 0 and observes `populated=0`. No signals, process kill, file deletion or cgroup removal occur. Both cgroups and all kernel files remain in place as retained site evidence.

**Failure/lifecycle STOP:** if any step fails, the script does not thaw, signal, kill, remove a cgroup, or retry. It closes only its own descriptors. An unfrozen child normally exits after the parent's pipe closes or its 30-second cooperative timeout; a child already frozen can remain indefinitely frozen even after the parent exits. No normal cleanup or proof of its exit can be inferred in that case. Record the exact cgroup and PID if printed, retain complete capture and remote scene, do not launch B1 or repeat the probe; an authorized operator must inspect the exact owned child and cgroup and decide how to handle it under the user's STOP rules. Waiting on `Popen.wait(timeout=10)` is bounded but Python/kernel/process failure or a lost transport can still leave release and liveness NOT CHECKABLE. This check can leave a retained empty cgroup even on success; the production process also retains its cgroups. Site policy, owner/delegation and whether these retained cgroups are acceptable must be confirmed under current author and site scope before invocation. Do not claim user or administrator consent from this document.

## Operator capture template

Before invoking, independently review exact script bytes and this command, verify the current author scope and full STATUS/occupancy, check that the fixed cgroup name does not exist in the **actual current SSH session membership** where that can be read without mutation, and verify that the local capture path is absent. A new SSH session may have a different membership; the script's own exclusive `mkdir` is authoritative and refuses a collision. Never reuse the local capture or cgroup. The operator must ensure the interpreter actually used is site-qualified and that no outside actor is preempted. The author explicitly instructed continuing despite other observed agent processes, but that does not authorize preemption or touching their work. No GPU lease is acquired, and observations are not reservations.

The local command must run under `/bin/bash`, not zsh, from the checkout containing the reviewed script. It uses a task-specific status variable, checks exclusive open, complete SSH status footer, descriptor close and SHA-256 calculation. Any capture failure, SSH failure, missing/ambiguous footer, script STOP, partial output, loss of transport, unconfirmed child wait or unknown freezer state means STOP, preserve, report and do not retry.

```bash
set -C
capture=/private/tmp/tasl7-cgroup-capability-20261107-a94ce1891ef94f93.txt
if exec 3>"$capture"; then :; else
  printf '%s\n' 'STOP: capture exists or cannot be created; SSH not invoked' >&2
  exit 1
fi
if ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' \
  < docs/r1/proposals/tasl7_cgroup_probe_20261107/probe.sh >&3 2>&1; then
  task_ssh_status=0
else
  task_ssh_status=$?
fi
if printf '\nSSH_EXIT_STATUS=%s\n' "$task_ssh_status" >&3; then :; else
  printf '%s\n' 'STOP: cannot record status; preserve scene' >&2
  exit 1
fi
if exec 3>&-; then :; else
  printf '%s\n' 'STOP: cannot close capture; preserve scene' >&2
  exit 1
fi
if shasum -a 256 "$capture"; then :; else
  printf '%s\n' 'STOP: cannot hash capture; preserve scene' >&2
  exit 1
fi
exit "$task_ssh_status"
```

Save the entire local capture; it contains full STATUS text and may remain local. Report UTC, actual command and interpreter, GPU UUID, complete status and output SHA; independently review the result before relying on it. **Unblock:** a fresh independent reviewer must accept source and lifecycle first; the site operator must establish fresh host scope/occupancy and current cgroup ownership/delegation. If owner or mkdir/control permission fails, the operator preserves the output and asks the site administrator for a delegated cgroup-v2 subtree consistent with the actual reviewed `_parent_dir` requirement; do not create or alter system services. This is a site-dependent administrative action and its time is unknown. If a probe child remains frozen, the authorized operator must investigate the exact owned child and cgroup before any further action; effort depends on the site. Final code, author gate, handover, full no-delete/tests and all other B1 prerequisites remain separate.

Static validation only: `bash -n` and in-memory AST parsing of the embedded parent and child Python. No execution of the probe, real process lifecycle, filesystem modification, remote connection, model, experiment or GPU operation was performed for this draft.
