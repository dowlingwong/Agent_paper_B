# TASL-7 rename capability: cross-directory amendment — 7 November 2026

AI-assisted (Codex). **Candidate only; not reviewed or executed.** This amendment supersedes the source script and capture command in both earlier rename-probe proposal documents; their full preconditions, STOP rules, no-deletion, fresh operator census, no-preemption, evidence retention, independent review and scope limits continue to apply. Those earlier files and script are retained as history, not a second test or permission to retry. The replacement script is `tasl7_rename_probe_20261107/probe_crossdir.sh`, SHA-256 `b28605fbb94362d9bc424e91e4cb087fdf7ebc6b9e11225f19ec79ce5723c4cb`; shell syntax and embedded Python AST pass locally, but it has not run.

The original draft tested the two flags within one directory. Production also moves between a working directory and `_to_delete`, so this amendment creates a private `_to_delete` inside the single exclusive probe directory, checks ownership, permissions, device and mount identity, and performs NOREPLACE move and EXCHANGE across those two open directory descriptors. It fsyncs both directories after each cross-directory rename. Collision checking still tests the existing `b` in the probe directory, ensuring both original files are unchanged before the successful move. After a successful exchange, original A is retained at `b`, and original B at `_to_delete/c`. All names, partial data, and directories remain after any failure; no cleanup is allowed. An error after a successful rename can leave either valid arrangement; STOP and preserve without retry, with no inference about completion.

Before a host action, a fresh independent reviewer must review the exact amended script and this capture command, including the cross-directory identity checks and error paths; the operator must separately inspect current STATUS and nonpreemption/occupancy and verify script SHA. Neither this document nor review grants B1 readiness. A pre-existing output capture or probe directory is STOP and must not be replaced or worked around.

```bash
set -C
capture=/private/tmp/tasl7-rename-capability-20261107-7d322b6c3a1e4c2f.txt
exec 3>"$capture" || exit 1
if ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' \
  < docs/r1/proposals/tasl7_rename_probe_20261107/probe_crossdir.sh >&3 2>&1; then
  ssh_status=0
else
  ssh_status=$?
fi
printf '\nSSH_EXIT_STATUS=%s\n' "$ssh_status" >&3
exec 3>&-
shasum -a 256 "$capture"
exit "$ssh_status"
```

Capture includes complete STATUS files. Exit 255, interrupted capture, changed STATUS, unsupported flags, an fsync failure or any ambiguity is STOP: retain all outputs and the probe directory; no deletion, signal or retry. A successful check proves only these syscalls and retained bytes/inodes at this time, not crash recovery, physical locality, formal B1 lease, cgroup, complete no-deletion execution or any final B1 gate. Site operator must record UTC time, UUID, exact command, script and output hashes, status and disposition; obtain independent review of the result before relying on it.
