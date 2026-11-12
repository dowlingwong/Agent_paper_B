# Track S S0.4 rerun at the A2-U pin — 11–12 November 2026 (ENGINEERING_ONLY)

**ENGINEERING_ONLY; not a scientific result.** This report records the S0.4 rerun authorised by the STOP-3 ruling (author decision (a), `docs/r1/reports/TRACKS_PHASE3_20261109.md` §11; PLAN §10 `R1-TRACKS-A2U-STALE`) at the new paper pin. The old `s04` STOP scene was not read or written.

## Provenance and pins

- Delivery D-S: branch `mac-tracks-a2u-stale-20261111`, tip `c8b13b5d63d3d30f5afa642928f1458e863e8935` (review record on top of accepted commit `fe651e589c2d6bafafc3a27e8eb7d8599845a7df`); review `docs/r1/reviews/R1_TRACKS_A2U_STALE_REVIEW_20261111.md`, rounds 1–3 **accepted**; PLAN §10 row `R1-TRACKS-A2U-STALE` names the new pin.
- **Paper pin `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`**, checked out **detached** on TASL-2 in `/home/dowling/r1_tracks/work/Agent_paper_B`; `git status --porcelain` empty. Recorded in a STATUS entry before the run.
- Harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (clean); llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab` (v0.7.0, server `0.7.0-dev (build …, commit 620d2225c)`); GGUF sha256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`; server flags per rev 3.3 §0.2; k = 1 (port 18101).
- Launch script `r1/tracks/ops/launch/tasl2_s04r2_20261111.sh` committed at `3899b8ac6d20384dc6b32387b3a3db79011a6eaf`, deployed to `$R/launch/` with host sha256 `9ac5d584d35eed402bba2e39c913ff62d594bb2cf5b78cdf4731d80768cf8b60` = committed blob.
- The manifest's `sessions[0].provenance` records `paper_commit = 8237fd02…`, `harness_commit = a3fedbb…`, `manager_gguf_sha256 = 509287f7…`, `llama_build = 620d2225…`, `obs_inflation = 1.0`, `g_declared = g0 = 0.00066`, `label ENGINEERING_ONLY`.

## Precondition test (c) on TASL-2 (read-only on the old run tree)

At the pin, `TRACKS_S04_ROOTS=/home/dowling/r1_tracks/scratch/digits_mlp/s04/roots`, `AR_HARNESS_ROOT` at the harness pin, pytest from a scratch `--target` directory (frozen venv untouched; `PYTHONDONTWRITEBYTECODE=1`): **5 passed, 0 skipped**; the five printed ledger SHA-256 values equal `docs/r1/reports/TRACKS_A2U_STALE_S04_CHECK_20261111.md`; the checkout stayed clean. Full log `/tmp/trks_a2u_precondition_20261111.log` on TASL-2.

## Run

- Start `2026-11-11T23:14:13Z`, collector exit `2026-11-11T23:58:32Z` with **rc 0** (`trks_s04r2`).
- Manifest `sessions[0].done = {"roots": 10, "forks": 0, "leaves": 0, "failed": 0, "exhausted": 0, "deadline_hit": false, "status": "complete"}`.
- Dry run (`trks_s04r2_dry`, identical command with `--dry-run`): **roots_todo = 0, leaves_todo = 0, exhausted = 0**; rc 0. 2 % rule: exhausted 0.
- All ten roots committed; every root `status ok`, `llm_calls = 40`, no `error`. No STOP file in the new phase directory; old `s04` manifest mtime unchanged (`2026-11-08T17:43:23-0800`).
- Close-out server observation: at close-out the `trks_llm` session and `llama-server` were already absent (GPU idle, cooperative lease free). The server log ends at `2026-11-11T23:57:12Z` with `stop: all tasks already finished, no need to cancel` and no error/cleanup marker; no operator kill was issued by this runbook step and the Track S watcher logged no new marker. The exact cause is not established by the retained evidence; it did not truncate the campaign (all ten roots completed at the 40-call cap). Recorded as an observation.

## Checks

- `liveness` (CPU): `pass: true`, 400 trials; novelty 0.875 (≥0.5), invalid rate 0.0625 (<0.3), 75 keeps after trial 1.
- `fit_prior`: `/home/dowling/r1_tracks/out/digits_mlp/a2u_prior_r2_20261111.json`, sha256 `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`; `kinds.local = {mu0: -0.0011366265, tau0: 0.00099, sigma_cmp: 0.0186225072, tau_w: 0.0492852208}`.
- Copy-back: `results/r1/tracks/digits_mlp/s04_r2_20261111/` with the whole out tree, the prior and `host_logs/` (launch log, collector cmd/exit/log, dry-run log/exit, llama log tail, host evidence), plus `SHA256SUMS` (see that directory; `sha256sum -c` passes).

## Next

Fresh independent review of this rerun (runbook §2.1 step 8). Only after that review is accepted does line L1 continue to Phase 4: S0.5 and S0.5b for `digits_mlp` in new directories, copy back, then pause and report; the S0.5 summary and STOP 4 wait for `tabular_mlp`. The old `s04` scene, its STOP files and the run-6835/B1 scenes remain preserved.
