# Track P — E0 protocol v2 DRYRUN on Kev-0.8B and Qwen-0.8B (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on zhixu portal). **DRYRUN — not evidence.** Asked for by the author (PLAN §10 R1-E0-PROTOCOL: "Re-run the DRYRUN on Kev-0.8B and Qwen-0.8B under the fixed protocol and report. I will set the E0 and A4 thresholds in a PLAN row after seeing it, then write the Phase 5 authorization"). No authorization note exists and no evidence run was started. The code and decision changes behind it were independently reviewed (`docs/r1/reviews/TRACKP_DECISIONS_REVIEW_20261026.md`). This report has no pass/fail verdict: the v2 thresholds are the author's.

- **Commit and runs.** All runs are at commit **`8e13e77`** (clean tree; harness `897d83c` = `HARNESS_PIN_C3`). Each manifest records torch 2.6.0+cu124 and the kev / laya / startlux_decide pin commits, all checked at start.
- **Driver and evidence.** Driver `trackp_e0v2_dryrun_20261026/driver.sh`; every report, manifest, curve and lease record is in `trackp_e0v2_dryrun_20261026/runs/`; tables from `summarize.py`.

## Protocol as run

- **Data.** The committed E0 set (`e0_v1.jsonl.gz`, unchanged): train cells minus 6 validation cells, giving 2,700 train / 300 val. The test set is 1,000 prompts in the 10 held-out cells, 6 interpolation and 4 extrapolation.
- **Fresh head, stage 1.** LayerNorm + Linear(hidden → 12) on each wrapper's readout state, fitted on frozen-backbone states at lr 1e-3.
- **Fresh head, stage 2.** LoRA r = 16 together with that head; adapter lr from the grid {1e-5, 3e-5, 1e-4}, head 1e-3. The Qwen control's 14 token rows stay frozen.
- **Training budget.** Both stages: batch 8, warm-up 5 % plus cosine over the 2,000-step cap. Val RPS every 100 steps (the start included), patience 5, best checkpoint restored. bf16 with gradient checkpointing.
- **lr choice.** `e0-select` picks the lr with the lowest best val RPS on the fresh-head soft run. The hard-label contrast and the native-readout run reuse that lr.
- **Native readout, reported separately.**
  - Kev uses its released pointer head, trained at the adapter lr.
  - The Qwen control uses its bin tokens. The rows are initialised at the mean embedding and trained in fp32 at lr 1e-4.
  - The zero-shot result comes first, then the same LoRA stage.
- **Metrics on the held-out cells.**
  - RPS: 1/(K−1) ordinal part plus the bin-0 Brier term, halved.
  - **Width slope = regression of the predicted std on the label's own std** (the binned soft label with the same bin midpoints and ±4 tails). The label's own slope vs s is reported as the ceiling.
  - Mean slope on m. Also reported: the v1 slope on s and the width ratio.
- **E6 on the selected soft fresh-head model** (n = 100):
  - **A3**: 0 / 25 / 50 / 100 % of the remaining budget under 1,024 tokens. The budget is measured with all four pool families' own renderings and filled to the word. 2k / 8k are descriptive only.
  - **A4**: 5 steps of s, against the label's std.
  - **A5**: bin-token family only.
- One training seed per configuration. GPU training is not bit-reproducible, so differences in the third decimal of slopes are within run-to-run noise.

## E0 results (held-out test cells, 1,000 prompts)

**Ceiling: the label's own width slope vs s is 0.925** (std over the binned label with the same representatives). The label's mean slope vs m is 1.029. A perfect predictor has width slope vs label std = 1.000 by construction. The v1 criterion "width slope vs s ≥ 0.7" corresponds to 0.76 of this ceiling.

| base | run | stage | RPS | **width slope vs label std** | v1: vs s | mean slope | width ratio | best / stopped at |
|---|---|---|---|---|---|---|---|---|
| kev-0.8b | fresh, soft, lr 1e-5 | + LoRA | 0.0006 | **0.783** | 0.724 | 1.017 | 1.15 | 2000 / 2000 |
| kev-0.8b | fresh, soft, lr 3e-5 | + LoRA | 0.0003 | **0.853** | 0.797 | 1.024 | 1.12 | 1900 / 2000 |
| kev-0.8b | **fresh, soft, lr 1e-4 (selected)** | head fit (frozen) | 0.0430 | −0.001 | −0.002 | 0.122 | 2.09 | 1600 / 2000 |
| kev-0.8b | **fresh, soft, lr 1e-4 (selected)** | + LoRA | 0.0002 | **0.923** | 0.862 | 1.012 | 1.08 | 1700 / 2000 |
| kev-0.8b | fresh, **hard**, lr 1e-4 | + LoRA | 0.0373 | 0.055 | 0.041 | 0.808 | **0.27** | 100 / 600 |
| kev-0.8b | native (released pointer head), lr 1e-4 | zero-shot | 0.0778 | −0.029 | −0.026 | 0.035 | 2.08 | — |
| kev-0.8b | native (released pointer head), lr 1e-4 | + LoRA | 0.0000 | **0.943** | 0.878 | 1.023 | 1.04 | 1800 / 2000 |
| qwen3.5-0.8b-base | fresh, soft, lr 1e-5 | + LoRA | 0.0014 | **0.646** | 0.599 | 0.955 | 1.11 | 1800 / 2000 |
| qwen3.5-0.8b-base | fresh, soft, lr 3e-5 | + LoRA | 0.0004 | **0.863** | 0.810 | 1.011 | 1.14 | 1800 / 2000 |
| qwen3.5-0.8b-base | **fresh, soft, lr 1e-4 (selected)** | head fit (frozen) | 0.0340 | 0.003 | 0.004 | 0.228 | 1.93 | 2000 / 2000 |
| qwen3.5-0.8b-base | **fresh, soft, lr 1e-4 (selected)** | + LoRA | 0.0002 | **0.971** | 0.910 | 1.009 | 1.11 | 1900 / 2000 |
| qwen3.5-0.8b-base | fresh, **hard**, lr 1e-4 | + LoRA | 0.0383 | 0.023 | 0.016 | 0.831 | **0.20** | 100 / 600 |
| qwen3.5-0.8b-base | native (bin tokens), lr 1e-4 | zero-shot | 0.0585 | −0.000 | −0.000 | 0.000 | 2.63 | — |
| qwen3.5-0.8b-base | native (bin tokens), lr 1e-4 | + LoRA | 0.0002 | **0.813** | 0.758 | 1.026 | 1.11 | 1700 / 2000 |

The head-fit rows are the same at every lr: the head fit does not depend on the adapter lr, and the cached features are identical. Best val RPS per lr, as used by `e0-select`:
- **Kev:** 3.4e-4 (1e-5), 1.2e-4 (3e-5), **4e-5 (1e-4)**.
- **Qwen:** 6.9e-4, 1.3e-4, **6e-5**.

Full per-run JSON, including interpolation and extrapolation RPS, is in `runs/`.

### What the numbers say (no thresholds applied)

1. **The frozen backbone carries no width information through a linear head.** The width slope is ≈ 0 for both bases, and the head predicts one broad distribution (width ratio ≈ 2). It does carry some location: mean slope 0.12 for Kev and 0.23 for Qwen. **Width is learned only once LoRA trains.** A threshold on the head-fit stage would fail every model.
2. **With LoRA, the selected soft runs reach** a width slope vs the label std of **0.92 (Kev) / 0.97 (Qwen)** and a mean slope of 1.01. That is 0.86 / 0.91 against s, compared with the label's own 0.925. The width slope rises with the lr: Kev 0.78 → 0.85 → 0.92, Qwen 0.65 → 0.86 → 0.97.
3. **Convergence within 2,000 steps is not settled.** Every soft LoRA run had its best checkpoint at step 1,700–2,000. Kev at lr 1e-5 was still improving at the cap. Early stopping never triggered on a soft run: all ran to 2,000, and the starting model was never chosen. The hard runs stopped at 600.
   - So the result depends on the 2,000-step budget, and most of all at the low lrs.
   - The lr grid choice and the threshold interact: at 1e-5, Qwen reaches 0.65.
4. **Hard labels collapse the width as the spec expects.** Width ratio 0.27 / 0.20, width slope ≈ 0, best at step 100. This is the appendix contrast.
5. **Native readouts.**
   - Zero-shot, neither base reads the stated noise; Qwen's zero-shot bin tokens are uniform (rows initialised identically).
   - After LoRA, Kev's released pointer head reaches 0.94, slightly above its fresh head.
   - The Qwen bin-token readout reaches 0.81, below its fresh head (0.97), with lr 1e-4 on its rows.

## E6 results (selected soft fresh-head model, n = 100)

| probe | kev-0.8b | qwen3.5-0.8b-base |
|---|---|---|
| **A3 (v2)**: mean \|ΔRPS\| at 25 / 50 / 100 % of budget (criterion ≤ 0.01) | 2.1e-5 / 2.4e-5 / 2.9e-5 (meets 0.01) | 2.6e-5 / 2.5e-5 / 2.6e-5 (meets 0.01) |
| A3 budget actually reached, mean (min) | 0.24 (0.23) / 0.49 (0.48) / 1.00 (0.98) | same prompts |
| A3 descriptive 2k / 8k | refused: Kev `ContextOverflow` (state 2,383 / 8,400 > 1,024) | 4.2e-5 / 6.0e-5 |
| **A4 (v2)**: share of prompts whose predicted std never decreases where the label's std increases | **1.00** (label ceiling 1.00; median slope of predicted std on label std 1.04) | **1.00** (ceiling 1.00; median slope 1.05) |
| A5 slot bias (bin-token family; TV ≤ 0.02) | n/a | **max TV 0.20 (fails)** |
| A1 / A2 | n/a (no packing on hybrid bases) | n/a |

- **A3 budget.** Per prompt, the budget is 194–496 tokens (mean 374). StartLux's chat framing is the longest rendering: 830 tokens at level 0, 1,024 at the maximum. Kev reaches 965, Qwen 980 and Laya 871, with no truncation.
- **A5.** The probe was run on the fresh-head model, whose belief comes from the linear head, not the bin tokens. The listing order of the bins in the prompt then moves the belief by up to 0.20 TV. Whether A5 should be read on the fresh head or on the bin-token readout is open (question 4 below). A5 is recorded, never disqualifying (spec §5.7.1).

## Attempts

| # | What happened | Cause | Action |
|---|---|---|---|
| 1 | GPU smoke at `70b7580` (40 steps, 160 examples) on both bases: ran; ≈ 0.61 s per step | — | full driver started |
| 2 | Full driver started at `70b7580`. Stopped by me after 1,500 steps of the first run (kev lr 1e-5); output kept in `~/r1_trackp/runs/p5_e0v2_dryrun_attempt1_aborted/` | The decisions review arrived. Findings 4 (the start of the LoRA stage was never evaluated) and 10 (Qwen token rows trained in the fresh run) change the protocol | Fixed at `8e13e77`, restarted from scratch |
| 3 | All 10 E0 runs, 2 selections and 2 probe runs completed (`EXIT=0`) | — | this report |

## GPU use

- **Leased jobs:** 14 jobs, 09:33–13:49 UTC, **3.69 GPU-h** (`runs/*/manifest.json` → `gpu_lease`; `~/r1_trackp/runs/gpu_lease_log.jsonl`).
- **Aborted attempt 2:** ≈ 0.5 h more. Its lease has no end record because the job was killed with its tmux session.
- **Checks:** at every start the Track X marker was absent and no foreign compute process was running.

## Questions for the author (before the threshold row and the Phase 5 authorization)

1. **E0 and A4 thresholds**, against the ceiling (label width slope vs s = 0.925; perfect = 1.000 vs the label std).
2. **Training budget.** The soft LoRA runs peak at 1,700–2,000 of 2,000 steps, and early stopping never triggered.
   - Keep 2,000?
   - Or raise the cap / judge only the selected lr?
   - The low-lr grid points have clearly not converged.
3. **Head-fit stage.** It shows ≈ 0 width for both bases. Should it be reported only (descriptive), with thresholds on the LoRA stage?
4. **A5 for the Qwen control.** Read it on the fresh-head model, as run here, or on its bin-token readout? Also: should the bin tokens still be listed in the control's prompt when the belief comes from the fresh head?
5. **My implementation choices**, listed under the 26 Oct PLAN rows. They include:
   - val cells;
   - eval every 100 steps, patience 5;
   - the 2,000-step cap per stage;
   - the lr reused for the hard and native runs;
   - frozen Qwen token rows in the fresh run;
   - token-row lr 1e-4;
   - released heads on the adapter grid;
   - the A4 criterion form.

## Not done

- No evidence run.
- No StartLux or Laya E0, since the DRYRUN scope is the two bases the author named.
- Multi-seed variation not measured.
