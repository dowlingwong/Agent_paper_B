# Track P overnight summary — 25/26 Oct 2026

AI-assisted (Claude Code, Track P agent on zhixu portal `TASL-2`), following `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` from Phase 0 under the author's overnight instruction. Everything is on branch **`trackp-20261026`** (paper repo, pushed; harness unchanged); **nothing is merged into `main`**. Work dir `/home/dowling/r1_trackp/`.

## Phases completed and accepted

Every phase went through the independent review loop (a fresh reviewer agent re-ran the checks, fixes, re-check). Each acceptance below is the reviewer's verdict.

| Phase | Result | Report | Review (verdict) |
|---|---|---|---|
| 0 Host facts | RTX 4090 sm_89, driver 535 / CUDA 12.2; all Track P Hub repos public and un-gated; RUNBOOK repo names corrected (Laya = `convaiinnovations/laya-typed-decisions`, Kev weights `jaredpalmer/kev-{0.8b,4b}`, StartLux org `startlux-models`) | `PORTAL_TRACKP_HOST_FACTS_20261026.md` | `TRACKP_0_REVIEW_20261026.md` (6 minor → accepted) |
| 1 Code | Items 1.1–1.11 on tiny CPU models; 160 Track P tests; paper suite 407 → 559 passed, failing set unchanged (environmental) | `TRACKP_PHASE1_CODE_20261026.md`, `overnight/TRACKP_CODE_HANDOFF.md` | `TRACKP_1_REVIEW_20261026.md` (3 blocking + 8 minor → accepted) |
| 2 Env, downloads, pins | venv torch 2.6.0+cu124 + fla + causal-conv1d; 8 repos (26 GB), all 112 files verified against the Hub, Kev also against its GitHub release; config filled | `TRACKP_PHASE2_ENV_PINS_20261026.md` | `TRACKP_2_REVIEW_20261026.md` (6 minor → accepted) |
| 3 P.0 spikes | All 8 bases pass (load, LoRA incl. DeltaNet, toy SFT on both outputs, bit-identical reload, ≤ 13.7 GB at ~1,024 × 8); StartLux trains with the bidirectional mask, port = StartLux's own 5.8 code at bf16 noise | `TRACKP_P0_SPIKES_20261026.md` | `TRACKP_3_REVIEW_20261026.md` (2 blocking + 8 minor → accepted) |
| 4 Toy batch | All 8 families: total, belief and action loss decrease (whole batch, eval mode); reload identical | `TRACKP_P4_TOY_BATCH_20261026.md` | `TRACKP_4_REVIEW_20261026.md` (4 minor → accepted) |
| 5 P.3a | **Not started** (needs `trackp_p3a_<date>.md`). DRYRUN on kev-0.8b only: soft E0 learns the mean (slope 1.00) but not the width (slope 0.11, would fail E0); hard labels collapse width (0.25); A4 fails; A3 blocked by Kev's 1,024-token state limit. Not reviewed (DRYRUN). | `TRACKP_P3A_DRYRUN_20261026.md` | — |

All reports and reviews are under `docs/r1/reports/` and `docs/r1/reviews/`. STATUS entries added for Phases 0–4.

## Commits

43 commits on `trackp-20261026` from `b5a7aec` (= `main`) to this summary. Key points:
- Phase 0: `870e6de`, `f08e5e4`, `ef3e2f3`.
- Phase 1: `4919f59` … `51d0d57` (5 worker branches merged).
- Phase 2: `7285791` … `7a4b74b`.
- Phase 3: final runs at `fcc7d7d`, accepted `da42298`.
- Phase 4: runs at `da42298` / `914ee12` (Laya), accepted `84c37a2`.
- DRYRUN at `84c37a2`.

Every run manifest records its exact commit (clean tree).

## Stops

**No stop condition was hit.**
- The single OOM (attempt 1 of the first spike) was explained: the toy SFT ran without gradient checkpointing, which spec §4 requires. Fixed and recorded.
- No CPU fallback.
- No pinned value mismatched: revisions, sha256 and the Kev base revision all checked.
- The GPU lock was never held by anyone else, and no Track X evidence run was seen.
- `~/.config/r1/secrets.env` is absent but no API step was planned.

Every failed attempt is recorded in the phase reports' attempt tables (P.0: six attempts; Phase 4: Laya twice).

## GPU use

**≈ 57 leased GPU-minutes (≈ 0.95 GPU-hours)**, 71 leased jobs, 04:35–07:15 UTC 26 Oct (`docs/r1/reports/trackp_p3a_dryrun_20261026/gpu_lease_log.txt`). This includes the reviewers' reproducibility re-runs and the DRYRUN. The largest single job was ≈ 3.4 min.

## Questions for the author (decisions that are yours)

1. **StartLux rung:** trainable candidate or inference-only zero-shot rung (runbook STOP 3; PLAN row). The engineering evidence supports "trainable". Licence is CC BY-NC 4.0.
2. **Phase 5 design before the authorization note** (the DRYRUN makes these concrete):
   - the E0 head-fit step for released heads (2e-5, effectively a no-op) and for StartLux softmax-12 (nothing trainable);
   - whether 200 LoRA steps at the spec lr are the intended width test;
   - A3 handling for context-limited models (Kev 1,024-token state, Laya 1,024).
3. **Spec interpretations made in code:**
   - RPS normalisation;
   - 10 finite bin edges vs "11" (cumulative-11 = 1 + 10; the Jev rung adds an inert Noul);
   - exam-rule step 4 (finalist 1 = first of the tied set after tie-breaks).
4. **Model-wrapper choices from P.0/P.4:**
   - LayerNorm before the new heads;
   - Laya's new heads read the mean-pooled encoder output;
   - Kev pointer temperature = 1 (released T only for E1 zero-shot);
   - control learning rates before P.4 (the Qwen-0.8B control is unstable).
5. **Environment:**
   - torch 2.6.0+cu124 on driver 535 through minor-version compatibility (or upgrade the driver);
   - code pins (Kev code is 23 commits after `kev-1.0`);
   - `jev.model = jev-1.14.0`.
6. **Harness pin `6afdb0e` (Track H) is not on GitHub.** Push it to harness `r1`. Until then 4 Track H test modules cannot run on the portal.
7. **Track X STATUS marker:** may the Track X agent write `## <date> — Track X B1 running` / `… done`, which is what the GPU-lease check reads?
8. **Merge `trackp-20261026` into `main`** when you are satisfied (the coordinating session merges).
9. Place `~/.config/r1/secrets.env` before Phase 7 (Jev) and Phase 9 (demonstrations).

## Not done

- Phases 5–9 (evidence; authorization notes).
- The vLLM serving-path comparison for StartLux (vLLM not installed).
- Encoder packing for Laya.
- The Kev variant of reason-then-bin.
- The online controller attaching `row["prompt"]` for the real sidecar (Track H follow-up).
- Deterministic GPU kernels for bit-reproducible multi-step training (to settle before multi-seed evidence).
