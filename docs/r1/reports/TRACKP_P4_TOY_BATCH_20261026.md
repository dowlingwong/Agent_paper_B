# Track P Phase 4 — P.1/P.2 toy batch on every family (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on zhixu portal). **ENGINEERING_ONLY.** **Status: independently reviewed and accepted** (`docs/r1/reviews/TRACKP_4_REVIEW_20261026.md`: 4 minor findings fixed). Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 4 ("the same 64-example toy batch trains for 50 steps on every family that passed P.0, both outputs, through the shared loop; loss decreases; save/reload identical"). Branch `trackp-20261026`. Evidence: `trackp_p4_20261026/<base>/{report,manifest}.json`, `toy_metrics.txt`.

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

Baselines on the same 64 examples (`p4_baselines_output.json`, script `p4_baselines.py`): constant base-rate belief (the mean label) 2.243; best constant action (logit of the |u|-weighted positive fraction 0.640) 0.737.

All 8 families: the total loss, the belief loss and the action loss decrease on the fixed batch, and reload is bit-identical for belief and action. Against the constant baselines: 6 families end far below both. **Laya's belief (2.406) ends above the constant base-rate belief (2.243)** — it starts at 2.551 and learns slowly at lr 2e-5; its action (0.697) ends only just below the best constant (0.737), but its saved action head does rank examples (|u|-weighted AUC 0.785, correlation with u 0.44, CPU). The Qwen control 0.8B's action (0.710) also ends only just below 0.737. Clean trees in every manifest. Losses near 0.001 for the action on 64 examples are memorisation of a toy batch, expected here and meaningless beyond "the output trains". Laya learns slowest (lr 2e-5 on its released head; spec §4). The Qwen control 0.8B run is unstable rather than slow: grad norms 50–170 in the first half, minibatch loss spiking to 6.3 (the 4B control with the same `<exec>`/`<skip>` token readout reaches 0.003); the lr for the control's new token rows (1e-3) and its fresh LoRA (1e-4) should be settled before P.4 (author / first SFT run).

## Attempts

| # | What happened | Cause | Fix |
|---|---|---|---|
| 1 | 7 families pass every output; **Laya's action loss did not decrease (0.743 → 0.748)**; total and belief did | the action head read Laya's [CLS] state after its head layers: norm ~1.1e4 and only ~1.2 % between-prompt variation after LayerNorm (measured on 16 prompts, CPU), i.e. nearly constant input | Laya's new heads (action, cumulative) read the encoder output mean-pooled over valid tokens (~8.7 % variation; trained through the LoRA) — `914ee12`, a change confined to `LayaWrapper` (diff checked), so the other 7 runs at `da42298` stand |
| 2 | Laya passes every output (table) | — | — |

## Deviations / items

1. Laya's new heads (action and, for the cumulative-11 head form, the cumulative head — relevant to E0's head fit and E7) read the mean-pooled encoder output, not the [CLS] state after its head layers (spec §2.2: "Linear (hidden → 1) on the question/decision state"). Measurement (`laya_readout_states_output.txt`, script `laya_readout_states.py`, 16 prompts, CPU): between-prompt variation after LayerNorm — post-head [CLS] 1.2 %, post-head mean 1.6 %, post-head marker mean 1.9 %, encoder [CLS] 8.6 %, encoder mean 8.7 %. Laya's native 12-option readout is unchanged (parity test with Laya's forward passes); the pooled state is the padding-invariant masked mean (test `test_laya_new_heads_read_the_padding_invariant_masked_mean_of_the_encoder`). Author to confirm (Q1).
2. As in P.0, multi-step training on the GPU is not bit-reproducible across runs (non-deterministic CUDA backward kernels); initialisation and pre-training files are.

## Questions for the author

1. Laya's new heads on the mean-pooled encoder output (deviation 1).
2. Learning rates for the Qwen control's new token rows / fresh LoRA before P.4 (instability of the 0.8B run).

## Notes

- The trainer logged the scheduler's lr *after* each step (the next step's lr); fixed — it now logs the lr the step ran at. Step 1 ran at half lr (2 warm-up steps).
- `laya.attempt1/report.json` names the checkpoint under the old directory name (renamed to `laya.attempt1/` after the run).

## GPU use

Phase 4: 9 leased runs, 06:26–06:44 UTC (`gpu_lease_log.txt`); no Track X job, no foreign compute process.

## Next

Phase 5 (P.3a, evidence) needs the author's authorization note `docs/r1/authorizations/trackp_p3a_<date>.md` and is not started (author's overnight instruction; a DRYRUN on one model is permitted). Before it: the E0 head-fit design for released heads and StartLux softmax-12 (P.0 report deviation 5) and the author's StartLux rung decision.
