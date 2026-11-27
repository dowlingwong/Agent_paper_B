# Round status — screening smoke PASS; preflight and Ada blocked; G1 replicate code accepted

**Round start:** `origin/coord/compute` `372d2099`; `origin/main` `e153df24`. **Time:** 27 Nov 2026, 03:05–03:55 UTC.
No evidence campaign, no G.5 label, no sealed read. The G2 branch is based on the later `main` `bad59593`
(addendum-template merge); the screening and blocker branches are based on `e153df24`. Kit c1 and the expansion
note were already published
(`166db0eb`) and the G.1b jobs were running, so `compute/20261126-04` needed no new disposition this round. The
expansion G.1b jobs were left running.

## Delivered

| Task | Result | Branch / tip | Review |
|---|---|---|---|
| `compute/20261127-14` screening smoke again | **PASS**: 168/168 written, `failed_runs = 0`, `stop = null`, cache `tree_sha256` `c0c2a364…`, `MANIFEST.json` `74e688e7…`; `failed_runs.jsonl` absent | `compute-screen-smoke-repeat-20261127` @ `05f3e115` | `compute-screen-smoke-repeat-review-20261127` @ `bd264999`, **ACCEPTED** (5 non-blocking minors) |
| `compute/20261127-12` D.3 HTCondor preflight | **BLOCKED, no match**: L40S `Start = false`; no runnable A100 (175 five free but `Start = false`, 167 one free but `Start`/`Requirements` undefined/error, 179 none free); jobs `760148`, `760152` idle then removed; no container started, no in-job input read | `compute-preflight-blockers-20261127` @ `28352976` | `compute-preflight-blockers-review-20261127` @ `6d0452f5`, **ACCEPTED** (round 5) |
| `compute/20261127-13` Ada P.4 probe preparation | **BLOCKED before the fill**: under `zli538` Apptainer is absent and `docker info` is permission-denied; the reviewed direct launcher accepts only apptainer/docker, so no truthful `direct.container_runtime` exists; venv `a1d0cf74` otherwise accepted | same branch | same review, **ACCEPTED** |
| `compute/20261127-16` G1 replicate-arm code (FIXR3/EGATE) | **ACCEPTED**: recorder `begin_step`/`on_charge`/`write_final_from_state`, `replicate_campaign.py`, chunk replicate branch, G8 trial rows and events, per-step zero-variance, failure classes; 34 G1 unit tests + 75 engine/accounting tests | `compute-d3-g1-replicate-20261127` @ `478c3348` (code reviewed at `02ad2370`; tip adds a docs-only test-count correction) | `compute-d3-g1-replicate-review-20261127` @ `2ba6435e`, **ACCEPTED** (round 2; 6 non-blocking minors) |
| `compute/20261127-17` D.3 G2 constants fit | **PASS**: artifact `d3_constants.json` sha256 `4f5f686b…`; `check` rc 0 and the same sha; independent re-fit byte-identical; all seven 121-row LADDER tables recomputed and equal; reading only the receipted sweep-2 train/dev release (receipt `de95b218…`, partition `7487b627…`); 19/19 focused tests | `compute-d3-g2-constants-20261127` @ `79b0a0ce` | `compute-d3-g2-constants-review-20261127` @ `f8f0c2ac`, **ACCEPTED** (3 non-blocking wording minors) |

The G1 review round 1 was `CHANGES REQUIRED` on `fb101386`; the fixes are a normal new commit (`02ad2370`), no force
push. The preflight review needed five wording/evidence rounds; all findings are closed.

## Tests

- Screening: `test_screen_measure.py` **82 passed**; smoke `manifest.json` records 168/168 and 37 identity flags.
- G1: `test_d3_g1_snapshots.py` 18, `test_d3_g1_chunk.py` 9, `test_d3_g1_replicate.py` 7 = **34 passed**; with
  `test_d3_fixr3.py`, `test_d3_egate.py`, `test_d3_g8_accounting.py` = **109 passed**.
- G2: the fit ran twice with byte-identical output; the artifact's `check` rc 0; the focused fitter tests are
  reviewed by the independent G2 reviewer (19 synthetic tests at the local unit).
- Full `r1/tests` at the final G1 tip `02ad2370` with `--continue-on-collection-errors`: **178 failed, 4477
  passed, 165 skipped, 27 errors**. The base `e153df24` run: **179 failed, 4462 passed, 165 skipped, 27 errors**.
  The sorted FAILED/ERROR id lists show **zero new ids** at the tip: all 205 tip ids are in the base's 206; the
  base-only id is the known flaky `test_t1_tasl_crosscheck.py::test_short_job_on_tasl7_then_compare_with_the_g1b_tasl2_attempt`.
  The `fb101386` intermediate run also had zero new ids (205 vs 206). Environments: Python 3.11.13, pytest 9.2.0,
  `AR_HARNESS_ROOT` at the Mac harness checkout, fresh TMPDIR; the known failures are environment/known-base failures.

## Resource samples (read-only, 03:37–03:38 UTC)

- **TASL-7:** RTX 4090 24,564 MiB, 44 MiB used, 0 % util, load 0.00; `gpu0.lock` free; only system/ollama
  processes. Idle for a T1 job that fits 24 GB.
- **Ada:** cards 0 and 2 empty (48,427 MiB free each, 0 %); cards 1/3/4/5 shared by another user (~14.7 GB free,
  100 %); cards 6/7 21.2 GB free (44 %/0 %). The P.4 blocker is the runtime, not memory.
- **ETP pool:** deepthought 2 × TITAN X, deepthought2 1 × L40S (`Unclaimed`, but `START = false`); no H200/H100.
- **TOpAS:** A100 parent `c03-001-175` 5 free but `START = false`; `167`/`179` busy/not runnable.
- **TASL-2:** expansion G.1b CPU jobs on sets 0-3/4-7/12-15; GPU 353 MiB used by a non-job process; no GPU job.

## Still running or waiting

| Item | State | What the next round checks |
|---|---|---|
| Expansion G.1b (`compute/20261126-10`) | `gc7rc_etth1` sealed; `mlgym_metamaze` (pid 106579), `gc7rc_forestcover` (106573), `mlgym_titanic` (106578) still running on TASL-2 CPU sets 0-3/4-7/12-15 | node completion, then `seal`, `assemble`, `summarise`; no GPU used |
| Houseprice CPU-set (`compute/20261127-01`) | blocked: `cpus-0-3`/`cpus-4-7` held by MetaMaze/Forest Cover; the 27 Nov waiter timed out with nothing run | rerun `run_cpuset_check.sh` after both seal; do not take the leases |
| G.5 P11 TASL-2 items (`compute/20261127-05`) | blocked: TASL-2 sets 0-7 busy with expansion and the G.5 note is unpublished | leases free and the G.5 note published |
| G.5 campaigns (`compute/20261126-06`) | blocked on the published G.5 note | note publication |
| D.3 per-arm smoke (`compute/20261126-09`) | blocked on the G1 adapter, G2 constants and local units | those dependencies |
| D.3 preflight (`compute/20261127-12`) | blocked on a runnable L40S/A100; request must not be edited | a card whose `Start` allows jobs |
| Ada P.4 probe (`compute/20261127-13`, `compute/20261126-07`) | blocked on a host runtime: docker group access/Apptainer, or a reviewed venv launch path (Level 2) | the host/author decision |
| Screening evidence run | waits for the author's signed screening note | the signed note |
| G1 adapter / G6 | next G1 unit at harness `9bb416805175149eb87b71f28d77530572aa4bce` with `verify_seed_base=20000`, `verify_runs=2`, `verify_split_policy="vary"`; then G6 | coordinator merges `02ad2370`, then the adapter card |
| G2 artifact review | **ACCEPTED** at `f8f0c2ac`; the coordinator publishes `4f5f686b…` into revision 4 (`local/20261127-08`) | the revision-4 freeze |

## Active jobs and IDs seen

- Expansion G.1b: TASL-2 pids 106573 (forestcover), 106578 (titanic), 106579 (metamaze); CPU-only.
- Pre-existing HTCondor jobs, not ours and not touched: `760142`, `760143`, `760145`, `760147` (`lucid_torch_job.sh`
  on TOpAS A100), idle `759624`, `759625`, `760065` (H200 request).
- Our preflight jobs `760148`, `760149`, `760152` were removed after capture.

## What was decided alone

To treat the Ada runtime and the HTCondor capacity as blockers rather than edit a request or the launcher; to submit
a corrected A100 preflight (`760152`) after the superseded `760149`; to keep the new screening cache for the evidence
run and not touch the STOP scene; to stop the G1 code at the adapter seam and leave the real node/manager/worker
adapter to the next unit. No `main` push and no force push.

## Needs from the coordinator

1. Merge the accepted screening-smoke branch (05f3e115) and the accepted blocker records (28352976); the G1 code is
   accepted at 02ad2370 and can merge after the coordinator's full-suite check.
2. Decide the Ada route: docker-group/Apptainer access or a reviewed venv launch path (Level 2).
3. Queue the G1 adapter after the G1 code merge; keep the houseprice, P11 TASL-2, G.5 and D.3-smoke cards blocked.
4. Retry the D.3 preflight only when a runnable L40S/A100 appears; the 23-slot analyze is the submit pool, not TOpAS.
