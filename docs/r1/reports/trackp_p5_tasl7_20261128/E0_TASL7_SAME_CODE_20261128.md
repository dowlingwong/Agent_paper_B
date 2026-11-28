# TASL-7 E0 same-code reference — NOT equivalent on RPS (STOP)

Task `compute/20261128-01`. PLAN **R1-P4-E0-SAME-CODE-REFERENCE** (`main` `15fe05b0`): re-run the P.4 E0
reference on TASL-7 with the same code and configuration as the Ada E0 comparison run, then compare with the
pinned Ada run using the existing comparator and tolerances. ENGINEERING_ONLY (`--evidence DRYRUN`).

**Result: the run completed cleanly (`pass: true`, 2,000 steps, best step 1,800), but the three-criterion
comparison is NOT equivalent: width and mean slopes pass; RPS is 19.09 % below the Ada run against a 10 %
relative tolerance. This is a STOP for the phase-1 note's `ada_smoke_e0` line.**

- **Base:** `origin/main` `a98d2eff1d2847e34f00effe66b53bc00467e936`.
- **Run:** `trackp.py e0 --stage final --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --seed 0
  --gpu 0` on paper `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`; fresh run directory
  `/home/dowling/r1_trackp/runs/p5_e0_ref_20261128/e0e` (nothing resumed).
- **Host / card:** TASL-7, RTX 4090 (sm_89), driver `580.178.04`, UUID
  `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`. Lease `2026-11-28T00:11:43Z`–`00:40:07Z`; 0 foreign processes
  and 0 MiB foreign memory at start and end (empty card).
- **Environment:** venv `/home/dowling/r1_trackp/venvs/trackp-gpu`, torch `2.6.0+cu124`, transformers `5.19.0`,
  peft `0.21.2`; harness `897d83c8efa364ec2fdd37288241cc42e01d7274` (the same harness commit as the Ada run),
  clean.
- **Data:** `data_manifest_sha256 = b963be2dd378241e0b0689907d4051bfa62922a8e4968aa40061ed7ef275bfef`, exactly
  the Ada run's data manifest.
- **Config:** `e0_config_ref_tasl7.json` is `trackp_portal.json` with only `e0.final.max_steps 6000→2000` and
  `patience 10→5`; file sha256 `4f47048dd37bb53b4ced22404d749253dd80d96a5c91f3750ab031d01aa35993`, canonical
  `config_sha256 31dd5776887df8e03c7f6e360f460c47f43c5d3bafc04a22c17f595c3b99b3d4`. The E0-relevant blocks
  (`e0`, `head_lr`, `lora`, `lr_grid`, `token_lr`, Kev base revision) are **identical** to the Ada config;
  only host fields differ (GPU model, lock path, direct block).
- **Run outcome:** `pass: true`; `lora.best_step 1800`, `stopped_at 2000`, `early_stopped false`; head fit is
  descriptive (L-BFGS) and the fresh head is restored before LoRA.

## E0 metrics (held-out test cells, 1,000 prompts)

| Criterion | Ada reference | TASL-7 same-code | Delta | Tolerance | Pass |
|---|---:|---:|---:|---:|---|
| `width_slope_vs_label` | 0.902956 | 0.905136 | +0.002179 | abs ≤ 0.05 | yes |
| `mean_slope` | 1.014162 | 1.012671 | −0.001491 | abs ≤ 0.05 | yes |
| `rps` | 1.438354e-4 | 1.163752e-4 | **−19.09 % rel** | rel ≤ 10 % | **no** |

`equivalent: false` from the existing `p5_compare_ada.py` (tolerances unchanged: absolute 0.05 for the two slopes,
relative 0.10 for RPS), exit status 1. Descriptive differences: LoRA best step 1,900 → 1,800 (both stop at 2,000,
no early stop); head-fit test RPS 0.016919 (Ada) → 0.017788 (TASL-7); `rps_extrap` 3.246e-4 → 2.471e-4;
`rps_interp` 2.973e-5 → 3.383e-5.

## Timing

- Lease span `00:11:43Z`–`00:40:07Z` = **28 min 24 s = 0.4733 GPU-h**, on an empty card.
- This is **not** a parity carry-forward: the E0 comparison failed, so the phase-1 note cannot cite this run as
  the Ada–TASL-7 equivalence or as a reviewed timing carry-forward. A repeat after parity, or an explicitly
  reviewed carry-forward, is still required under R1-P4-PHASE1-SIGNATURE.

## What this means and what happens next

The slopes agree closely and the data, harness, model revision and E0 recipe are identical, so the recipe change
is not the cause of the 19 % RPS gap. The gap is in the near-zero RPS level, where a relative tolerance is sharp
(about 2.7e-5 absolute). Under the existing comparator this is a miss, therefore a STOP: do not widen a tolerance,
re-run for a better value, or change the reference without the author's decision.

Options for the author/coordinator (not chosen here): (a) re-baseline both hosts on the current code and pre-declare
a tolerance appropriate to the RPS level; (b) accept the two-host difference explicitly with its magnitude and
scope; (c) re-scope the Ada P5 check. The phase-1 note and A5 SFT remain gated.

## Files

`e0e_report.json` (sha256 `e86dc68589cdc92419acc72bb59a24b52a2e2fd008b329713bc2779989aca2d9`),
`e0e_manifest.json` (`5da9a353…`), `ada_reference_e0e_report.json` (Ada reference,
`7df24070ee8a3a0838b3e2b3e71bf264fcbc6d8fa5a531fac2d28c16d8b9e817`), `e0_config_ref_tasl7.json`,
`gpu_before.txt`/`gpu_after.txt`, `gpu_lease.jsonl` (the two lease events), `p5_compare_ada.py`,
`comparison_existing_comparator.json` (the comparator's own output, `e85aa003…`), `comparison_e0e.json`
(same numbers, reference/candidate labels corrected, `46805e6c…`). `SHA256SUMS` binds them.

Decided alone: kept the run and the comparator's miss as a STOP scene, added no relaxation, and did not resume or
overwrite anything.
