# Report — expansion G.1b launch: four nodes started (running)

**Task:** `compute/20261126-10` (the task `compute/20261126-04` item 5 waited for).
**Result: STARTED / RUNNING.** All four expansion nodes are running on TASL-2, one attempt each, CPU-only, on
disjoint CPU sets. No GPU lease. This report records the start; the seal and verdict follow when each job ends.

- **Note:** `docs/r1/authorizations/g1b_x_t1_tasl_20261126.md` on `main` `166db0eb`, sha256
  `16d31f48c48b5cffa26c13d988362e36a4e3241a17f15f41a9ad1ad7dd043539`, `approved: true`. Re-verified sha256 in the
  launch checkout at 23:36Z.
- **Strict check:** PASS in the launch checkout; `gates` all four PASS; `spec_sha256`
  `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`.
- **Launch commit:** `7d0279d8a677582f4f6e5892461bf7138e78fd66`, from a fresh clone whose `origin` is the spec's
  `https://github.com/dowlingwong/Agent_paper_B.git`; the published note is an untracked file there, byte-identical
  (sha256 above). `origin/main` in that clone is `166db0eb`.
- **Run root:** `/home/dowling/r1_tracks/t1_tasl_x/runs/g1b-x-tasl-20261126-a`
- **Harness checkouts:** the four worktrees at their kit pins, clean apart from the `data` links (re-verified at
  23:36Z): Titanic `3a67042b`, MetaMaze `aa354485`, ETTh1 `3a06d867`, Forest Cover `85851664`.

| Node | CPU set | Launch (UTC) | Attempt recorded (UTC) | Attempt directory | State at 23:36Z |
|---|---|---|---|---|---|
| `mlgym_metamaze` | 0-3 | 2026-11-26T22:53:26Z | 2026-11-26T22:53:32Z | `…/mlgym_metamaze/attempt-1` | running (pid 106579) |
| `gc7rc_forestcover` | 4-7 | 2026-11-26T22:53:26Z | 2026-11-26T22:53:32Z | `…/gc7rc_forestcover/attempt-1` | running (pid 106573) |
| `mlgym_titanic` | 12-15 | 2026-11-26T22:53:26Z | 2026-11-26T22:53:32Z | `…/mlgym_titanic/attempt-1` | running (pid 106578) |
| `gc7rc_etth1` | 16-31 | 2026-11-26T22:53:26Z | 2026-11-26T22:53:32Z | `…/gc7rc_etth1/attempt-1` | running (pid 106577) |

The four CPU-set leases are held by the node orchestrators (pids above); at 23:36Z the four active worker processes
were verified with `taskset -cp` on 0-3, 4-7, 12-15 and 16-31 respectively. No node uses CPUs 8-11.
`CUDA_VISIBLE_DEVICES` is empty; the 4090 is untouched and no GPU lease is taken.

## The one refusal before the start

The first launch at 22:52:49Z was refused by the reviewed launch check in all four nodes, rc 4, with no attempt
directory:

```
STOP: origin (/home/dowling/r1_tracks/remotes/Agent_paper_B.git) is not the spec's paper repository
https://github.com/dowlingwong/Agent_paper_B.git
```

The checkout I first used was a worktree of the local bare mirror, not a clone of the spec's paper repository. The
logs are kept under `…/g1b-x-tasl-20261126-a/_logs/<node>-20261126T225249Z-*.node.log`; no attempt was created and
nothing was consumed. I did not edit the check or fake the origin: I made a fresh clone of the spec's repository at
`7d0279d8`, copied the published note byte-identically, re-ran the strict check (PASS), and launched from there at
22:53:26Z. This is an infrastructure/setup refusal, not a scientific STOP; if the coordinator reads it otherwise,
the four running jobs are to be stopped.

## What happens next

Each node runs its 460-run D21 chunk (projected 1.675–18.378 h by record; the four sets are disjoint). On completion
I seal each attempt, then `assemble` and `summarise` per the note, and report the per-node determinism verdict and
the summary sha256. A node-deadline STOP is not an outcome (keep scene, report, wait for a task); a determinism
failure or a node STOP is reported as such. The GPU-hour figure is 0 projected and 0 consumed (CPU-only).

**Decided alone:** to relaunch from a fresh clone of the spec's repository after the origin-check refusal, rather
than edit the check or point the old checkout at a different origin; attempt 1 in the new run root is the first
attempt (the refused launch created none).
