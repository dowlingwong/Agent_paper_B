# Track P — two-stage E0 v2 driver: short validation DRYRUN on Kev-0.8B (26 Oct 2026, evening)

AI-assisted (Claude Code, Track P agent on zhixu portal). **DRYRUN — not evidence. It validates the mechanics of the two-stage driver; it does not measure E0**, because the step caps are shortened (screen 200, final 400, versus 2,000 / 6,000).

Requested by the author (PLAN §10 R1-P3A-READY): "Validate the two-stage driver with a short DRYRUN on kev-0.8b. Then STOP with rule v2 committed and the branch pushed."

- **Code reviewed:** the code behind the run was reviewed in `docs/r1/reviews/TRACKP_RULEV2_REVIEW_20261026.md`.
- **Last portal GPU run:** this is the last Track P GPU work on the portal (R1-TASL7-TRACKP).

| | |
|---|---|
| Code | paper **`5538b79`**, clean tree in all 8 manifests (`dirty_files: []`); harness `897d83c`; torch 2.6.0+cu124 and the code pins checked at every start |
| Command | `SHORT=1 OUT=~/r1_trackp/runs/p5_e0v2_twostage_short driver.sh kev-0.8b` (`trackp_e0v2_twostage_20261026/driver.sh`) |
| Evidence | `trackp_e0v2_twostage_20261026/runs/kev-0.8b/*/{report,manifest}.json`, curves, `tables.md`; raw runs in `~/r1_trackp/runs/p5_e0v2_twostage_short/` |
| Data | committed E0 set: 2,714 train / 286 val (val cells (1,3), (3,2), (5,4), (8,2), (0,3), (9,3), **disjoint from the 10 held-out test cells**) / 1,000 test |

## What ran

1. **lr screen** (stage "screen"): fresh LayerNorm + linear head and LoRA, soft labels, lr ∈ {1e-5, 3e-5, 1e-4}, 200 steps each, eval every 100, patience 5. No head fit in the screen.
2. **`e0-select`**: lowest best val RPS among the three. It picked lr 1e-4 (val RPS 1.13e-3, against 1.45e-3 at 3e-5 and 3.2e-3 at 1e-5).
3. **Final** (stage "final") at lr 1e-4, capped at 400 here (6,000 in the real run), eval every 100, patience 10. It first runs the descriptive L-BFGS head fit on cached frozen features on CPU: 390 outer iterations, converged. **The fresh head is restored before LoRA.** This run carries the E0 pass flag.
4. **Hard-label contrast** and **native readout** (Kev's released pointer head) at the selected lr, with the final-stage budget.
5. **E6 probes** on the final model, n = 32: A3 at the pool budget, A4 against the label std, A5 n/a for Kev.

Every step exited 0; `driver.log` ends `EXIT=0`.

## Results (held-out test cells; shortened budget, so these are not E0 numbers)

| run | stage | RPS | width slope vs label std (lb95) | mean slope | width ratio | best / stopped |
|---|---|---|---|---|---|---|
| screen lr 1e-5 | LoRA 200 | 0.0062 | −0.010 | 0.848 | 1.26 | 200 / 200 |
| screen lr 3e-5 | LoRA 200 | 0.0037 | −0.013 | 0.925 | 1.31 | 200 / 200 |
| screen lr 1e-4 (selected) | LoRA 200 | 0.0028 | −0.012 | 0.968 | 1.26 | 200 / 200 |
| final | head fit (L-BFGS, descriptive) | 0.0166 | 0.007 | 0.870 | 0.78 | 390 outer, converged |
| **final** | LoRA 400 | 0.0025 | −0.021 (−0.029) | 1.028 | 1.28 | 400 / 400 → `pass: false` |
| hard | LoRA 400 | 0.0344 | 0.003 | 0.835 | 0.66 | 100 / 400 |
| native (pointer head) | zero-shot | 0.0778 | −0.029 | 0.035 | 2.08 | — |
| native (pointer head) | LoRA 400 | 0.0002 | 0.862 | 1.019 | 1.12 | 400 / 400 |

**E6.**
- A3 v2: mean |ΔRPS| ≤ 1.4e-4 at 25/50/100 % of the budget (criterion met). The budget reached 0.24 / 0.49 / 1.00, and no family exceeds 1,024 tokens.
- A3 2k/8k: Kev refuses (`ContextOverflow`), descriptive.
- A4 v2: 0.25 of prompts monotone (fails the 95 % criterion). This fits a fresh head that has not yet learned width in 400 steps.

### What this shows

- **Mechanics.**
  - The selection reads only screen runs.
  - The final-stage budget is applied, and the override is recorded (`budget_override`).
  - The descriptive head fit runs once per base and does not feed LoRA.
  - Only the soft final fresh-head run carries `pass`; screen, hard and native runs have `pass: null`.
  - The rule-v2 fields are present: `width_slope_vs_label_lb95/ub95`.
- **Timing.**
  - Screen jobs ≈ 3.1 min for 200 steps.
  - The final job took 12.6 min, including the CPU L-BFGS head fit (the fit alone took ~30 min in attempt 1, while the CPU was shared with the reviewer).
  - The real run (3 × ≤ 2,000 + 3 × ≤ 6,000 steps) is estimated at ≤ 6 GPU-h per 0.8B base.
- **A behaviour to watch.** The fresh head trained from scratch with LoRA learns location within 200–400 steps but no width. Kev's released pointer head learns width within 400 steps (0.86).
  - In the full-length portal DRYRUN, the LoRA stage started from an Adam-fitted head, and width only appeared at steps 1,700–2,000.
  - Whether the 6,000-step final cap is enough for the fresh head to learn width is untested. The first full two-stage run on TASL-7 will show it.

## Attempts

| # | What happened | Cause | Action |
|---|---|---|---|
| 1 | `471f93f`. Screen lr 1e-5: the L-BFGS head reached val RPS 0.014. LoRA diverged over the first ~11 LoRA steps (gradient norms 11–120, loss 0.017 → ≈ 0.12) and then saturated the softmax (gradient norm → 1e-14); val RPS went from 0.014 to 0.119 and stayed there; early stopping returned step 0, the head fit. Each job also spent ~30 min of CPU L-BFGS while holding the GPU lease. Stopped by me during the second screen job; kept in `~/r1_trackp/runs/p5_e0v2_twostage_short_attempt1/`. | LoRA started from the L-BFGS head. Starting from its sharp, unregularised optimum, LoRA diverged and then saturated, the gradients vanished, and the descriptive head fit decided the E0 result. | The head fit stays descriptive: the fresh head is restored before LoRA, and the fit runs once per base (soft final run). Committed with the rule-v2 review fixes. |
| 2 | `5538b79`: all 8 jobs ran (this report). | — | — |

## GPU use (portal, this step)

- **Attempt 2:** 8 jobs, 22:56–23:30 UTC, 0.58 GPU-h.
- **Attempt 1:** one closed job of 37 min, plus one job killed with its tmux session after ≈ 25 min (no end record).
- **Total:** ≈ 1.6 GPU-h. The Track X marker was absent at every start.

## Host-equivalence configuration for TASL-7 (author's question)

Reproduce the **selected Kev-0.8B run of the portal E0 v2 DRYRUN**. The TASL-7 agent has already pre-declared it (`docs/r1/reports/tasl7_equivalence_20261026/PREDECLARATION.md`, `f3567e9`), and I agree with that choice.

| Item | Value |
|---|---|
| Portal run | `trackp_e0v2_dryrun_20261026/runs/kev-0.8b/fresh_soft_lr0.0001/` |
| Code / config | paper `8e13e77` (detached), harness `897d83c`, config identical |
| Command | `trackp.py e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001` |
| Base / lr / seed | kev-0.8b (Qwen3.5-0.8B-Base `dc7cdfe2ee41` + kev-0.8b `788ddbdd6571`), fresh LN + linear head, soft labels; adapter lr 1e-4, head lr 1e-3; seed 0 |
| Steps | head fit (Adam, ≤ 2,000) then LoRA ≤ 2,000; eval every 100, patience 5, batch 8 (portal: head best 1,600 / LoRA best 1,700, both stopped at 2,000) |
| Portal results (`lora.test`) | width slope vs label std **0.9230**; mean slope **1.0116**; RPS **1.989e-4**; v1 width slope vs s 0.862; width ratio 1.08 |

**Why this configuration.**
- It is the only full-length portal run of a selected configuration.
- In one ~25-minute job it exercises LoRA with gradient checkpointing, the DeltaNet kernels and the held-out metrics.
- The current two-stage code (`5538b79`) has only the shortened validation run on the portal, which measures mechanics, not E0.

**Optional second check of the current code.** Re-run this short validation DRYRUN on TASL-7 (`SHORT=1 driver.sh kev-0.8b` at `5538b79`, ≈ 35 min) and compare against the table above.
- GPU training is not bit-reproducible, so compare within the pre-declared tolerances, not exactly.
- Apart from that noise, the L-BFGS head fit and the screen selection are deterministic.

## Open for the author

Before writing `trackp_p3a_<date>.md`:
1. **My reading of "head fit descriptive only"**: LoRA starts from the fresh head, not the L-BFGS head (attempt 1 shows why).
2. **The other agent's readings marked in the spec:**
   - the bootstrap lower bound is two-sided at the 2.5th percentile, resampling test prompts;
   - A4 ≥ 95 % is recorded under E6 and does not disqualify;
   - the hard-label and native runs use the final-stage budget.
3. **Whether 6,000 steps let the fresh head learn width.** Unknown. The first TASL-7 run measures it.
