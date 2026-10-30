# Track P evidence marker on TASL-7 — helper script and proposed runbook text (draft, 30 Oct 2026)

**Draft by the chat session (Claude), at the author's request; AI-assisted.** Nothing here applies until the author installs the helper on TASL-7, pastes the runbook text into `TRACK_P_POST_TRAINING.md` and commits the PLAN row below.

## Why

Track S runs `tabular_mlp` on TASL-7 for several days (R1-TRACKS-HOST-2). Track P evidence keeps priority there (R1-TASL7-TRACKP). The Track S watcher yields only when `~/r1_locks/trackp_evidence.active` exists. **Today nothing on the Track P side creates that file** (Track S Phase 0 review, n3). Without it:
- the lease `flock ~/r1_locks/gpu0.lock` still keeps two GPU jobs apart;
- but a Track P evidence job would wait or fail for as long as Track S's servers hold the card, which can be days. That inverts the priority.

This is the TASL-7 counterpart of the TASL-2 rule for Track X: a marker created before the first evidence job and removed after the last (R1-PORTAL-SCHEDULE amendment, 26 Oct).

## The helper

The file is `docs/r1/proposals/trackp-evidence.sh`. Install it on TASL-7 as `~/r1_locks/bin/trackp-evidence` and `chmod +x` it.

| Command | Effect |
|---|---|
| `trackp-evidence begin <phase>` | Creates the marker, with the phase, time, host and user as one JSON line. Refuses if a marker already exists; the write is atomic (`set -C`), so two concurrent `begin`s cannot both succeed |
| `trackp-evidence run [--wait S] -- <cmd …>` | Runs one GPU job under `gpu0.lock` with `flock -o`. Waits up to S whole seconds (default 4200 = Track S's 1 h forced stop plus margin) for the lease. Then waits up to 60 s for GPU 0 to show no compute process; a failing `nvidia-smi` counts as busy. Then it runs the job. It needs an open phase. Exit 75: lease not obtained; exit 76: GPU 0 still busy or `nvidia-smi` failing; otherwise the job's own exit code. A job that itself exits 75 or 76 is told apart by the log: only a started job has a `job starting` line |
| `trackp-evidence end <phase>` | Removes the marker. Refuses if the marker belongs to another phase (exact match, not a pattern) |
| `trackp-evidence status` | Shows the marker, whether the lease is free, and GPU 0's compute processes |

Every action, and every job's exit code, is logged to `~/r1_locks/trackp_evidence.log` with the helper's process id.

**Tested** in the chat session's container, with a stub `nvidia-smi` (revision 2, after an independent review):
- `begin` refuses a second marker, including two concurrent `begin`s;
- `run` refuses without an open phase and refuses a non-numeric `--wait`;
- `run` passes arguments with spaces intact and returns the job's exit code;
- `run` waits for a held lease (3 s) and gives up with exit 75 after `--wait`;
- `run` waits for a busy GPU to clear, and returns 76 after 60 s when `nvidia-smi` fails;
- the lease is held while the job runs and is free afterwards, even when the job leaves a background child;
- `end` refuses the wrong phase, including a near-match such as `P.3x` for `P.3a`.

It has **not** been run on TASL-7.

## Proposed text for `TRACK_P_POST_TRAINING.md` (a new subsection under the host / lease rules)

> **Evidence marker on TASL-7 (R1-TASL7-TRACKP-MARKER).** Track P evidence phases on TASL-7 (P.3a and later, A5, A6, R-B, LONO retraining, sidecar arms) run between `trackp-evidence begin <phase>` and `trackp-evidence end <phase>`.
> - **Begin** before the first evidence job of the phase.
> - **End** after its last job, or when the phase is stopped for good. Not between jobs: a gap would let other tracks restart.
> - **GPU jobs** of the phase run as `trackp-evidence run -- <command>`. A job that takes `gpu0.lock` itself must not be wrapped, because a second `flock` on the same file from inside the wrapper would wait on itself. Such a job keeps its own lock, but with a wait (`flock -o -w 4200`), not `flock -n`. Keep `-o`: without it, any child the job leaves running inherits the lock and holds the lease after the job has ended.
> - **If a Track P session dies** with the marker in place, the marker stays and other tracks stay paused. This is the safe default. End the phase by hand once its state has been checked.
> - ENGINEERING_ONLY and DRYRUN work does not need the marker.

## Proposed PLAN §10 row (the author writes and commits it)

```
| R1-TASL7-TRACKP-MARKER (<date>) | On TASL-7, Track P evidence phases create `~/r1_locks/trackp_evidence.active` before their first evidence job and remove it after their last (or when stopped for good), through `~/r1_locks/bin/trackp-evidence` (`proposals/TRACKP_EVIDENCE_MARKER_20261030.md`); their GPU jobs take `~/r1_locks/gpu0.lock` with a wait, not `-n`. The marker is authoritative for other tracks on TASL-7 (Track S yields to it, R1-TRACKS-HOST-2). Only Track P creates it, except a Track S integration check through the helper with the author's permission (Track S operator runbook 3.0b). |
```

## Open points for the author

1. **The jobs.** Which Track P jobs on TASL-7 already take `gpu0.lock` themselves? Those are not wrapped (see above).
2. **The integration check.** Once the helper is installed and Track P is idle, the Track S operator can run its integration check, runbook 3.0b. That is the only time anyone other than Track P creates the marker.
