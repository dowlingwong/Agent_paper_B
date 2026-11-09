# OPS — B1 STOP waiting duty, night of 9 November 2026 (experiment agent)

**Point-in-time operational record; no B1 host action was taken beyond read-only observation.** Authority: `prompts/OPERATOR_RUNBOOK_20261104.md` on `docs/runbooks-09nov`; `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §5–§6; the author's start instruction of 9 November (B1 criterion: if the diagnosis confirms a design problem, adopt R4 — drop the anchor-ordering STOP, keep the 7B duplicate-rate check, disclose the post-hoc amendment in the appendix — and re-run B1 after the fix review passes; poll the Mac-local agent's branches every 30 minutes; during the wait the S0.1 re-run may run on TASL-2 with new session names and append-only watcher/server logs; TASL-7 runs no Track P tonight).

This report covers the night 2026-11-09 00:43–08:00 CET. The recorded B1 STOP report `reports/B1_STOP_6835_20261108.md` remains authoritative for what happened; run `6835_20261108_a` and its scene were not touched.

## 1. TASL-7 baseline (read-only) and invariant state

Capture: private directory `/private/tmp/paper-b-ops-b1-baseline-20261109.je9RU0VR/`, `ssh.log` SHA-256 `1cc752d39717fddddbc5c95479408d865f07feee3393683ade6febe53e98d3eb`, `ssh.rc` 0 (SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`), contains `READONLY_DONE` and `SSH_EXIT=0`; committed with a note under `docs/r1/reports/ops_b1_20261109_captures/baseline_tasl7/` in commit `4005428f1` on branch `ops-b1-20261109` (from `mac-b1-20261107`).

Observed and unchanged at every later check (CET; host local time PST):
- run root `/home/dowling/exam-x/work/b1_6835_20261108_a` present with its top-level entries (`batch_state.json`, `random_valid/`, `scripted/`, `qwen25_coder_7b/`, `servers/`, `registry_snapshot.yaml`, `runner.lock`, `_to_delete/`), not modified;
- `~/r1_locks/trackx_evidence.active` dev `66306`, inode `56261609`, size 82, SHA-256 `092023e438a3c2508574a169becce448fd8d652481547f4a974f20ae5bdca1af`, contents `{"head": "68357d3d8cd0c9f301005e483a49ecfd05f6e5bb", "run_id": "6835_20261108_a"}` — matching the STOP report;
- `~/r1_locks/gpu0.lock` present, no lock holder; GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` at 236 MiB, 0 % utilisation, empty compute-app list;
- tmux: only the Track S watcher `trks_watch` (paused on the Track X marker); no `llama-server`, no STOP files under `$R/out`, disk 585 G free, 118.6 M inodes free, 62 G RAM.

No write, signal, rerun, marker retirement or gate change was made on TASL-7. No Track P work was started.

## 2. Polling record (every 30 min)

`git fetch origin --prune` and inspection of origin/local refs and the known branch names `mac-b1-diag-20261109`, `mac-b1-r4-20261109`, `mac-b1-fix-20261109`.

| Poll (CET) | Mac-local hand-off/fix branch? | Newest origin ref |
|---|---|---|
| 01:00, 01:30, 02:00, 02:30, 03:00, 03:30, 04:00, 04:30, 05:00, 05:30, 06:00, 06:30, 07:00, 07:30, 08:00 (scheduled; a few extra checks were made) | none | `docs/runbooks-09nov` @ `421a93d21` (00:36); `trackS-ops-20261030` push (03:05) |

No `proposals/B1_DIAGNOSIS_HANDOFF_*.md`, no `proposals/B1_RESTART_HANDOFF_*.md`, no Mac-local branch appeared on origin. The Mac-local agent's last origin push was `421a93d21` at 00:36 CET (§6 update); from 00:36 to 08:00 no repository activity from it was visible (Claude application processes stayed active). No B1 diagnosis script was therefore available to run; nothing on TASL-7 was required and nothing was done.

## 3. Track S work performed in the same window (TASL-2 only)

Separate workstream under the author's wait-period authorization; details in `docs/r1/reports/TRACKS_S01_RERUN_20261109.md` and `docs/r1/reports/TRACKS_PHASE3_20261109.md` on `trackS-ops-20261030`.

- **STOP 1 closed** (tip `5f2912a08`): S0.1 re-run on TASL-2/digits_mlp, serial 200/200 and concurrent 200/200 on both URLs plus cross-server 200/200, `cache_prompt: false` confirmed, k = 1 by clause (b) (22.87 h vs 34.10 h; 30 Oct projections reproduced). Independent review ACCEPTED. Author decision (a) then recorded: the append-only server-log recomputation (byte offsets 97,448,571 / 199,241,358, with the 2/200 one-call-shift control) satisfies R1-TRACKS-S01-RERUN's "identity recomputed from the saved contents"; standing instruction recorded that any future probe-pin change must write the response text and the paper/harness version identifiers into the result file.
- **STOP 3 closed** (tip `e7589ed4`): Phase 2 (S1.1) cited from the 30 Oct record after verifying the code path is identical across pins; Phase 3.0 pause drill on TASL-2 PASSED (marker 01:23:21Z, paused 01:27:50Z, lease released 01:28:08Z, 4 m 47 s, no FORCED, recorded STOP files, clean resume); Phase 3 S0.4 hit the 2 % rule (3/(5+0+3) = 37.5 %) on a deterministic pinned-code `ReplayError` (stale manager proposal in `r1/tracks/a2u.py`), a known issue in `TRACKS_HOST_FACTS_20261030.md` §5.1. `liveness`/`fit_prior` deliberately not run on incomplete data. Independent review ACCEPTED (0 BLOCKING/0 MAJOR/4 MINOR fixed). TASL-7 never touched; no Track P; no B1.
- **Open author decision at STOP 3:** fix the pinned code under a new pin + PLAN §10 row and re-run S0.4 in a new out/work directory (preserving the STOP scene), then resume at `liveness`/`fit_prior`, or another ruling. Phase 4 not started.

## 4. Status and next steps

- B1 remains stopped at `6835_20261108_a`; no diagnosis or restart was performed. The B1 criterion remains the author's A1/R4 instruction.
- When `proposals/B1_DIAGNOSIS_HANDOFF_20261109.md` is pushed with an accepted review: run its read-only script on TASL-7 exactly as written, capture the exit code, push the capture and its SHA.
- When `proposals/B1_RESTART_HANDOFF_20261109.md` is pushed and the fix is independently accepted: apply plan §5 (dated PLAN row for the R4 decision, exact new checkout committed/clean/reviewed, `approved: true` candidate note bound to the new HEAD per R1-EXAM-B1-NOTE-ORDER-07NOV, exact-HEAD review, real author gate, fresh occupancy/preflight/handover as for 6835, new run ID `…_b`, fresh output tree, old scene preserved).
- Risk noted to the author at 04:30 and 05:30 CET: the Mac-local agent pushed nothing for ~7.5 h; its session may be blocked on an approval prompt or still working. This operator cannot and did not do Mac-local work.

No STOP occurred on B1 tonight (no run was started). No evidence was modified or deleted.
