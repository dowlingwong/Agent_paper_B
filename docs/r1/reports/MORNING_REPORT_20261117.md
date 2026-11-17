# MORNING REPORT — 17 November 2026 (overnight run)

**Authority.** main `16185b0b`; `author-d8-confirm-20261117` @ `26177d82` (`R1-BX-D8-CONFIRM`,
`R1-TRACKG-G0-GO`, `R1-TRACKG-PORT-OWNER`, `R1-TASL2-UNITB-REHEARSAL`); main `R1-TRACKP-UNITB`; scope
TASL-7/TASL-2/Ada only. Branch `ops-tasl-20261116`. AI-assisted; no GPU evidence runs; no HTCondor.

## A. TASL-7 — Track P Unit B: BLOCKED (host unreachable all night)

- TASL-7 remained unreachable throughout: `ssh 100.106.74.51:22` timeouts; Tailscale shows
  `tasl-7 ... active; relay "lax", tx ... rx 0` (same signature as the 15 Nov outage). TASL-2 and Ada were
  reachable throughout.
- Low-rate retries every 30 min are still running (background job `bash-b174323ae382455e`); no host was
  touched, the TASL-7 checkout is still `b9ad6f8f`/`trackp-20261026`, **D `8662e359` was not delivered and
  Unit B was not started**.
- Ready for the moment it answers: fetch `trackp-p3a-code-20261116` (pushed at D), checkout exactly D,
  verify HEAD==D/clean/`b9ad6f8f` ancestor/runner sha `c045475b…`, record before/after; then run Unit B
  (`trackp_p3a_guarded.py --probes-only --base qwen3.5-4b-base --attempt1-root … --a3-short
  --authorization-amend-sha256 cd867e95… --root ~/r1_trackp/runs/p3a_attempt2_<UTC>`; DRYRUN kev-0.8b first,
  then EVIDENCE; 45-h projection; marker; no retry), then `TRACKP_P3A_<date>.md` + STOP 5 review (disclose
  A6 deferral and the 2k/8k omission).
- If it stays down: nothing else to do on TASL-7; the retry log is the record.

## B. TASL-2 — Unit B rehearsal: B1 DONE; B2/B3 STOP (reviewed defect)

- **B1 done:** the existing `trackp-gpu` venv is byte-identical to the committed portal freeze (121 lines,
  sha `50238e5a…`, sorted diff empty; torch 2.6.0+cu124); D worktree at `8662e359` clean; runner/child/config
  shas recorded; no install needed.
- **B2/B3 STOP:** three independent reviews (rounds 1–3) established that the proposed tiny kev DRYRUN
  cannot succeed on D: without `--budget` A3 v1 runs 0/2k/8k, the tiny kev `PointerWrapper` has
  `max_state=1024` and strict Kev encoding raises `ContextOverflow` at 2k/8k; `exam_run` only treats the
  *descriptive string* keys as non-fatal, so rc 1 with no report. This is the committed
  `TRACKP_P3A_DRYRUN_20261026` limitation (commit `08aeaff9`). **Not executed**; no host writes beyond
  read-only checks; no GPU; no attempt-2 root; nothing deleted/moved.
- **Decision needed:** (a) re-scope the rehearsal (e.g. qwen tiny success + kev expected-defect STOP + guard)
  with a recorded authority deviation, or (b) authorize the C2 + new D2 + `R1-TRACKP-UNITB` amendment path.
- Record: `reports/TASL2_UNITB_REHEARSAL_STOP_20261117.md`; reviews `TASL2_UNITB_REHEARSAL_REVIEW{,_R2,_R3}_20261117.md`.

## C. Ada — Track G G.0: U0/U1 done; U2/U3 pending port kits

- **U0 ACCEPTED / verified:** harness `r1-local-trackg-v2-20261114` @ `717ad835` deployed clean; Paper A gate
  three-check verified (newest v4 `live_*` == configured run dir, no Paper A process, `paper_a_status.py`
  `clear_finished`/key false/unidentified 0); fail-closed `nvidia-smi` wrapper `7e0ec81a…`; deployed config
  `c75bf9c3…` equals the committed blob; capture `6b62dd2a…`; R3 review `00529912…`. Residual risks and the
  mandatory per-U2 gate are in `reports/trackg_g0_20261117/TRACKG_U0_RESULT_20261117.md`.
- **U1 ACCEPTED:** docs-only licence/availability audit (`U1_LICENCE_AVAILABILITY_20261117.md`, review
  `66177ee5…`), 9 MINOR editorial fixes applied. Author decisions: MLGym CC-BY-NC acceptance; CIFAR-10/IMDb/
  AG News unstated terms; ETTh1 licence choice; Kaggle House Price terms; 1GC-7RC 404 (keep 4 Nov fallback).
  Coordinator: add a licence/provenance step to `TRACKG_PORT_CHECKLIST.md`.
- **U2/U3 PENDING:** no Track G port kit branches exist on `origin` or in the harness repo at 17 Nov
  01:45Z (checked `trackg|port|g0|census`); `R1-TRACKG-PORT-OWNER` assigns them to the Mac agent. No GPU
  job, no noise floor, no D21/D28 on Ada.
- **U4 census draft:** `reports/trackg_g0_20261117/TRACKG_CENSUS_20261117.md` (candidate rows pending kits;
  1GC-7RC extras not a suite).

## Author / coordinator decisions needed

1. TASL-7 network: whether the host needs manual recovery (we can only retry); then Unit B proceeds as
   authorized.
2. TASL-2 rehearsal: choose (a) re-scope with authority deviation or (b) C2/D2 + `R1-TRACKP-UNITB` amendment.
3. U1 licence decisions listed above; coordinator to amend the port checklist.
4. U2 requires the Mac agent's port kits; none appeared overnight.

## Records / state

- Branch `ops-tasl-20261116` pushed (latest before this report: `507b5279`; this report and U0 result are the
  next commit). Code branch `trackp-p3a-code-20261116` = D `8662e359` pushed.
- No force push; no main/exam-x push; no deletion; no HTCondor/deepthought action; no evidence run; TASL-2
  lock release from 16 Nov remains in `reports/TASL2_LOCK_RELEASE_RESULT_20261116.md`.
