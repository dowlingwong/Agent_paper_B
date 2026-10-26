# Track P Phase 4 — P.1/P.2 toy batch on every family (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on zhixu portal). **ENGINEERING_ONLY.** **Status: pending independent review (STOP 4).** Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 4 ("the same 64-example toy batch trains for 50 steps on every family that passed P.0, both outputs, through the shared loop; loss decreases; save/reload identical"). Branch `trackp-20261026`. Evidence: `trackp_p4_20261026/<base>/{report,manifest}.json`, `toy_metrics.txt`.

Procedure (`python r1/scripts/trackp.py toy --base <b>`, under the GPU lease): the same fixed 64 synthetic E0 training examples (offset 100, disjoint from the P.0 toy set) for every family; 50 optimizer steps, batch 8 (≈ 6 passes), the shared `Trainer`, both outputs (belief: RPS + soft CE; action: cost-weighted BCE on u = m), bf16 + gradient checkpointing, lr per spec §4 (2e-5 Kev/Laya, 1e-4 fresh LoRA, 1e-3 new heads; 2 warm-up steps, cosine). **"Loss decreases" is judged on the whole 64-example batch in eval mode before vs after training** (deterministic; total and each output separately), not on single minibatches. Save → reload into a freshly built wrapper (the trained model moved off the card first) → belief and action probabilities compared. StartLux is included: it passed P.0; its rung is pending the author.

## Results

| Base | total (eval, 64 ex.) before → after | belief | action | reload | commit |
|---|---|---|---|---|---|
| kev-0.8b | 3.642 → 1.911 | 2.904 → 1.666 | 0.738 → 0.245 | identical | da42298 |
| qwen3.5-0.8b-base | 4.329 → 2.901 | 3.583 → 2.191 | 0.746 → 0.710 | identical | da42298 |
| startlux-0.8b | 3.737 → 1.565 | 2.998 → 1.560 | 0.739 → 0.005 | identical | da42298 |
| laya | 3.440 → 3.103 | 2.551 → 2.406 | 0.889 → 0.697 | identical | 914ee12 |
| startlux-2b | 3.312 → 1.527 | 2.505 → 1.525 | 0.807 → 0.002 | identical | da42298 |
| kev-4b | 2.962 → 1.572 | 2.251 → 1.571 | 0.711 → 0.001 | identical | da42298 |
| qwen3.5-4b-base | 3.533 → 1.665 | 2.754 → 1.661 | 0.778 → 0.003 | identical | da42298 |
| startlux-4b | 3.089 → 1.510 | 2.308 → 1.509 | 0.782 → 0.001 | identical | da42298 |

All 8 families: the total loss, the belief loss and the action loss decrease on the fixed batch, and reload is bit-identical for belief and action. Clean trees in every manifest. Losses near 0.001 for the action on 64 examples are memorisation of a toy batch, expected here and meaningless beyond "the output trains". Laya learns slowest (lr 2e-5 on its released head; spec §4). The Qwen control 0.8B action output barely moves in 50 steps (0.746 → 0.710; it reads `<exec>`/`<skip>` token logits, i.e. trains through its new token rows and LoRA, not a fresh head).

## Attempts

| # | What happened | Cause | Fix |
|---|---|---|---|
| 1 | 7 families pass every output; **Laya's action loss did not decrease (0.743 → 0.748)**; total and belief did | the action head read Laya's [CLS] state after its head layers: norm ~1.1e4 and only ~1.2 % between-prompt variation after LayerNorm (measured on 16 prompts, CPU), i.e. nearly constant input | Laya's new heads (action, cumulative) read the encoder output mean-pooled over valid tokens (~8.7 % variation; trained through the LoRA) — `914ee12`, a change confined to `LayaWrapper` (diff checked), so the other 7 runs at `da42298` stand |
| 2 | Laya passes every output (table) | — | — |

## Deviations / items

1. Laya's new heads read the mean-pooled encoder output, not the [CLS] state after its head layers (spec: "Linear (hidden → 1) on the question/decision state"). Laya's native 12-option readout (its own scorer on the marker states) is unchanged (parity test with Laya's forward passes).
2. As in P.0, multi-step training on the GPU is not bit-reproducible across runs (non-deterministic CUDA backward kernels); initialisation and pre-training files are.

## GPU use

Phase 4: 9 leased runs, 06:26–06:44 UTC (`gpu_lease_log.txt`); no Track X job, no foreign compute process.

## Next

Phase 5 (P.3a, evidence) needs the author's authorization note `docs/r1/authorizations/trackp_p3a_<date>.md` and is not started (author's overnight instruction; a DRYRUN on one model is permitted). Before it: the E0 head-fit design for released heads and StartLux softmax-12 (P.0 report deviation 5) and the author's StartLux rung decision.
