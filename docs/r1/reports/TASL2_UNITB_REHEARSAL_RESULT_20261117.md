# TASL-2 Unit B DRYRUN rehearsal — RESULT: PASSED (17 November 2026)

**Status: rehearsal clean.** Authority: `R1-TASL2-UNITB-REHEARSAL` (`author-d8-confirm-20261117` @
`26177d82`), `R1-TASL2-REHEARSAL-SCOPE` (`author-decisions-20261117b` @ `33c82351`), `R1-TRACKP-UNITB`
(main `16185b0b`). Unit (rev 5) accepted by review R5
(`reviews/TASL2_UNITB_REHEARSAL_REVIEW_R5_20261117.md`, sha `203d27e1…`, 0 BLOCKING/MAJOR, 8 MINOR
recording fixes applied and recorded). ENGINEERING only; not evidence, not counted.

## Command (Unit B DRYRUN invocation, one difference recorded)

`probes --base kev-0.8b --head-form linear12 --budget --a3-short --n-probe 8 --evidence DRYRUN
--run-dir …/ENGINEERING_rehearsal_20261117T014743Z/DRYRUN/kev-0.8b/probes`
— A2's DRYRUN argv **minus only `--load`** (attempt-1 `EVIDENCE/kev-0.8b/final/saved` is a TASL-7 evidence
input and is absent on TASL-2; base+adapter loaded from the committed config local paths). Frozen venv
(TASL-2 `trackp-gpu`, Python 3.12.15/torch 2.6.0+cu124, freeze 121 lines sha `50238e5a…`), D worktree
`8662e359…` clean, env `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1`.

## Result

- rc 0, **wall 22 s**; scratch `…/ENGINEERING_rehearsal_20261117T014743Z`; report
  `DRYRUN/kev-0.8b/probes/report.json` sha `2d754ee3…`; manifest sha `84c10586…`; stdout `ad0740c3…`,
  stderr `c5aa51e9…`; `SHA256SUMS` in `reports/tasl2_rehearsal_20261117/`.
- `A3.protocol == "v2_budget"`, `A3.pass == True`, limit 1,024, all four families; **`A3_descriptive ==
  {"skipped":"R1-P3A-OOM-OPTION3","levels":[2000,8000],"pass":null}`** (2k/8k never run); `A4` and
  `A4_v1_raw` present; `A1`/`A2` non-packing n/a; `A5` BinToken-only n/a; `A3_errors` absent.
- `manifest.evidence_label == "DRYRUN"`; `manifest.gpu_lease` two entries (start/end, GPU
  `GPU-4d623e76-…`); `model_files_sha256 {}` (no `--load`, expected); `host.device` real RTX 4090.
- Baseline/after: tracked files clean; `.pyc` count unchanged (72); worktrees unchanged; GPU returned to
  353→356 MiB idle; lease released (FREE); **lease log 188 → 191 lines (sha `f813ce66…` →
  `0a4a14ae…`)** — the expected `acquired`/`start`/`end` lines; **FETCH_HEAD created (104 B)** and
  `refs/remotes/origin/main` moved `b5a7aec…` → `26177d82…` by the lease status-gate `git fetch` (recorded,
  expected); scratch contains only report/manifest/stdout/stderr.
- No marker helper/marker, no evidence label/table, no TASL-7 action, nothing outside the recorded lease/
  fetch side effects, no deletion.

## Disposition

The rehearsal **passes**: the A3-short budget path works on TASL-2 with the real kev-0.8b base+adapter, and
no Unit B defect is indicated. Next per `R1-TRACKP-TASL2-HOST`: if TASL-7 stays unreachable, run the
host-equivalence check (ENGINEERING) required by `R1-TASL7-TRACKP`, deliver D to a clean TASL-2 checkout with
the same verification, then Unit B on TASL-2 (one host for the whole table; disclose the host). Note for
Unit B: its `--load` targets attempt-1 `EVIDENCE/<base>/final/saved`, which is a TASL-7 artifact and is **not
yet present on TASL-2** — this must be resolved (copy from TASL-7 when reachable, or an author-approved
route) before Unit B can run there; that is a separate real gap, not a rehearsal failure.
