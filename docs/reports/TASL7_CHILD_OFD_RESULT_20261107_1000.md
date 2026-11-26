# TASL-7 parent-child OFD capability result — 7 November 2026, 10:00 CET

AI-assisted (Codex). **ENGINEERING_ONLY; result pending independent review.** This was the author-authorized, narrowly scoped engineering check described in `TASL7_CHILD_OFD_PROBE_REVIEW_20261107.md`, not a B1 launch. The reviewed script at feature commit `a9f09f05` has SHA-256 `b01fd732060db980b1035d96490094687635ffef643033aa37ae67f8a744e398`.

Immediately beforehand, a separate read-only census at 08:59:53 UTC captured the complete three STATUS files, lock directory, GPU and process census. Its local file `/private/tmp/tasl7-child-preflight-20261107-unique-1010.txt` has SHA-256 `c3f54ebd25ec8d27571947f42d0441c25459da185467ddb37af673806a46944d`. The GPU showed UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, 236/24564 MiB, 0% utilization and no listed compute application; the previously observed watcher and other users' processes remained visible. Full STATUS hashes matched the independently reviewed 09:37 CET snapshot. This is a point-in-time census, not a reservation or a guarantee of other operators' actions. The raw census remains local because it includes other people's process arguments.

At 09:00:09 UTC the following invocation started the exact script once; `set -C` protects the new local evidence file against an existing regular-file target. The local file contains combined stdout/stderr and the actual SSH exit status. No remote output file was requested.

```bash
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' < docs/r1/proposals/tasl7_child_ofd_probe_20261107/probe.sh > /private/tmp/tasl7-child-ofd-20261107-unique-0901-utc.txt 2>&1
result=$?
printf '\nSSH_EXIT_STATUS=%s\n' "$result" >> /private/tmp/tasl7-child-ofd-20261107-unique-0901-utc.txt
shasum -a 256 /private/tmp/tasl7-child-ofd-20261107-unique-0901-utc.txt
exit "$result"
```

The capture SHA-256 is `d64e65fb849da697f7011c1fdd53ac1337e803fae1ad0ed9d6ea0638e27e791d`, SSH exit 0. TASL-7 and UID 1011 matched; each complete STATUS file's before/after hashes matched the census. The probe observed the specified GPU at 0% and no compute-app PIDs. `/usr/bin/python3` 3.10.12 reported `flock_acquire: PASS`, `kcmp_parent_child: PASS rc=0 errno=0`, parent and child identity/liveness PASS, `owned_child_wait: 0`, successful unlock return and `probe_complete`. The actual recorded lock device/inode were 66306/56251186. The child check used the inherited descriptor under the acquired lock and is stronger than the prior self-comparison, but it tests only this parent and its own child at this time.

The script intentionally creates no remote files, issues no deletion or process signals, and starts no model, server, GPU workload or campaign. An advisory lock could briefly affect a concurrent cooperative launcher; incidental system/SSH utility side effects and other concurrent changes were not traced. This does not prove the production guardian/runner/worker/server chain, cgroup delegation, ongoing exclusivity, host handover or B1 readiness. Prior recorded experimental STOPs remain applicable to their respective phases; no formal B1 runner, author gate or anchor gate was invoked.

**B1 remains STOP:** the implementer and independent reviewer must resolve pinned harness deletion/truncation and cross-process STOP preservation, accepted combined code and final pins, real worker/server and site qualification, final note/gate, and reviewed handover. Site timing is occupancy-dependent; implementation/review effort remains uncertain. Recheck all applicable conditions at any future launch.
