# Screening rerun — blocked by deepthought co-tenancy (6 infrastructure stops, `compute/20261127-35`)

**Result: not measured. Six launch attempts under the same signed note stopped at the co-tenancy guard; each
scene is sealed, 0 runs failed, and no analysis was run.** This is an infrastructure loss under
R1-SCREEN-COTENANCY-INFRA, not an evidence STOP. The host had about 45 cores of foreign load (load1 ~60 with our
15 workers) at every breach; the note requires at least 10 cores free for others at launch and every 60 s.

- **Task:** `compute/20261127-35`, first in the 27 Nov queue.
- **Note:** `docs/r1/authorizations/screen_measure_20261127_reissue_2.md`, `approved: true`, sha256
  `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9`.
- **Code / cache / harness:** `c12136d664ae588a2539b76b2602e36742979ce8`; cache
  `/work/dwong/screen_fix_20261127/data_cache_20261127T134927Z` (tree `3843b53c…`); harness `6adf3859…`.
- **Host:** deepthought, 16 workers, CPUs only, batch venv `/ceph/dwong/r1_prepare_20261025/venv`.

## Scenes (all kept, none analysed)

| Run id | Written / planned | Failed | Stop | manifest.json sha256 |
|---|---:|---:|---|---|
| `SMEAS_EVIDENCE_20261127T1822Z` | 108 / 10,164 | 0 | `cotenancy -2.95 cores left` | `37670927…f89d2` |
| `SMEAS_EVIDENCE_20261127T1837Z` | 439 / 10,164 | 0 | `cotenancy 2.11 cores left` | `5eede42d…0d2` |
| `SMEAS_EVIDENCE_20261127T1840Z` | 442 / 10,164 | 0 | `cotenancy -0.89 cores left` | `ecdf2ea0…a4ab` |
| `SMEAS_EVIDENCE_20261127T1842Z` | 223 / 10,164 | 0 | `cotenancy 2.95 cores left` | `d1a36d8b…16e1` |
| `SMEAS_EVIDENCE_20261127T1845Z` | 440 / 10,164 | 0 | `cotenancy -4.79 cores left` | `95a10740d31177402ab687742747d8547a2111ebefb67cc580d28e2732a28418` |

The pre-existing `SMEAS_EVIDENCE_20261127T1550Z` (186 written, stop 9.87) stays as recorded in
`20261127-30-screen-stop-cotenancy.md`. A `20261127T1816Z` attempt was a strict-preflight refusal only
(`origin/main` stale in the checkout); it created no output directory and is not a run. After `git fetch`, the
`1822Z` attempt passed the preflight and started.

Each scene is at `/work/dwong/screen_measure_20261127/paper_c12136d6/results/r1/screen_measure/<run id>/`
(`design.json` `29396f5b…` in every scene, `lineage_runs.jsonl`, `worker_runtime.jsonl`, `cotenancy.log`,
`manifest.json`). No scene was resumed, patched or analysed.

## Observed host condition

`cotenancy.log` samples every 60 s. Representative readings:

| UTC | load1 | our workers | free for others | ok |
|---|---:|---:|---:|---|
| 18:41:59 (1842 launch) | 19.14 | 0 | 20.86 | true |
| 18:42:59 | 52.05 | 15 | 2.95 | false |
| 18:45:09 (1845 launch) | 11.88 | 0 | 28.12 | true |
| 18:46:09 | 38.90 | 15 | 16.10 | true |
| 18:47:09 | 59.79 | 15 | -4.79 | false |

The breaches are foreign load: the 16-worker job is the same in every attempt and the pre-launch readings pass.
`ps` at 19:41 showed only about 5 cores of named CPU users, so the load also reflects other users' short-lived
and I/O-bound processes. The guard is doing what the note requires; no assertion was relaxed and no `--workers`
value was changed.

## What happens next

- Retry the same note/code/cache with a **new** `SMEAS_EVIDENCE_<stamp>` when `cpus - 1-min load` is high enough
  that the 60 s samples can stay above 10 (observed safe starts were 20.9–28.1 free, and even those breached
  within 1–2 minutes). The next round should check `uptime` and `cotenancy.log` before a new stamp.
- If the host cannot supply a stable window, this becomes a scheduling/placement question for the coordinator
  and author, not a change to the note (R1-NO-TIMEOUT: no clock decides it).
- No analysis command was run; no manifest statistic is used. The D.3 step (8) hold remains.

Decided alone: to retry the pre-authorized infrastructure rerun whenever the preflight found room, with a fresh
stamp each time, and to stop retrying after the sixth breach in this round rather than spawn more scenes. Every
stopped scene is kept.
