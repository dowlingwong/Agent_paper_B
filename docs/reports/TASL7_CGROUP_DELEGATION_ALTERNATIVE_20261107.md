# TASL-7 cgroup delegation alternatives: source and evidence assessment

AI-assisted (Codex). **Source assessment and proposed read-only inventory; not executed or independently reviewed.** No host/network access, probe, model, GPU, signal, deletion, overwrite, system-service modification or experiment was performed for this assessment. Current launch remains STOP.

## What the evidence supports

The coordinator's read-only capture `/private/tmp/tasl7-cgroup-preflight-20261107-unique-e73a9.txt` reports that its SSH session belonged to `/user.slice/user-1011.slice/session-61314.scope`; its directory was UID 0, mode 755, and not writable as UID 1011. The earlier capture `/private/tmp/tasl7-site-readonly-20261107-0943.txt` reported another session scope and controllers, but no user-owned delegated scope. These are two point observations, not an inventory of the user's subtree and not evidence that delegation is absent everywhere. The first capture's report is `TASL7_CGROUP_PREFLIGHT_STOP_20261107.md`; its independent review is separate.

The actual combined candidate `r1/exam/b1_cgroup.py:57–75` derives the parent solely from the runner's `/proc/self/cgroup` unified `0::` membership, walks it below `/sys/fs/cgroup` without following components, checks cgroup v2, and requires the **current directory** to be owned by the runner UID. There is no caller-supplied path or environment override in `_parent_dir`. `B1Containment.initialize` then tries to create a fresh child (`:152–161`) and open its freezer controls (`:165–170`); leaf creation and enrollment controls have further requirements (`:205–216`). Thus identifying an owned writable directory somewhere else, or checking `test -w`, cannot on its own make the current root-owned SSH scope pass; the actual runner must begin inside a usable delegated membership, and successful mkdir/control/freezer/descendant behavior still needs the separately reviewed site probe. No change to this guard is proposed or authorized here.

## Proposed strictly read-only bounded discovery

Following a fresh applicable STATUS, occupancy, nonpreemption and disk preflight, an independently reviewed operator may inspect only the current UID's conventional systemd slice, without listing PIDs, reading other users' files, creating scopes, writing `cgroup.procs`, calling `systemd-run`, or altering permissions. The following is a **command candidate for independent review, not an instruction to run it**. Store complete stdout/stderr plus actual SSH status in a fresh exclusive local-only capture as required by the host runbook; preserve a partial capture on any failure. It reports the directory's ownership and ordinary access checks, not permission to migrate processes or proof of cgroup-controller delegation. A new SSH session may have a different current membership.

```bash
set -eu
printf '%s\n' 'CURRENT MEMBERSHIP'
cat /proc/self/cgroup
id
printf '%s\n' 'OWN-USER SLICE CANDIDATES (bounded depth 4)'
base=/sys/fs/cgroup/user.slice/user-1011.slice
if test -L "$base" || ! test -d "$base"; then
  printf '%s\n' 'STOP: own-user slice unavailable or symlink' >&2
  exit 1
fi
find -P "$base" -xdev -maxdepth 4 -type d -uid 1011 -exec sh -c '
  for d do
    stat -c "candidate uid=%u gid=%g mode=%a path=%n" "$d" || exit 1
    if test -w "$d"; then dw=yes; else dw=no; fi
    if test -w "$d/cgroup.procs"; then pw=yes; else pw=no; fi
    printf "candidate_access dir=%s cgroup_procs=%s\n" "$dw" "$pw"
  done
' sh {} +
```

A nonzero `find`/`stat` result, permission-denied traversal, missing base, unrecognized output, a changed mount/namespace, or transport/capture failure makes the inventory incomplete, not evidence of absence. Even exit zero and no listed candidate only establishes no UID-1011-owned directory was reported within this specific depth and accessible slice at that instant. Paths may include the user's other work; do not enter, migrate processes into, freeze, modify, remove, or treat them as available without an attributable ownership/handover and site-approved operating procedure. Local output may contain private path names and should be retained locally, not copied wholesale into Git.

## Unblocking and ownership

If an existing candidate is reported, the site operator and independent reviewer must determine whether its owner has delegated its use, whether a new process can be launched in that exact membership under site policy without disturbing any existing scope, and whether the production guard and full freezer/child/lease preflight pass; simply writing into `cgroup.procs` would itself be a host mutation and is not performed or proposed by this read-only command. Creating a new delegated service or scope, changing its ownership, or modifying system services is outside this inventory and requires an independently reviewed, explicitly authorized site procedure. If no usable current membership is available, the appropriate host administrator must explain or arrange supported user cgroup-v2 delegation; no message to the administrator has been sent. Read-only inventory and review are short, but site/operator coordination and any admin response time are unknown. Actual B1 tests, final pin and checkout, author gate and handover remain separate STOPs.
