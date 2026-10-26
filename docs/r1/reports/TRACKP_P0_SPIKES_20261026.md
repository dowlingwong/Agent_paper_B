# Track P Phase 3 — P.0 spikes (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on zhixu portal). **ENGINEERING_ONLY.** **Status: independently reviewed and accepted** (`docs/r1/reviews/TRACKP_3_REVIEW_20261026.md`: 2 blocking + 8 minor findings fixed). **The author decides the StartLux rung** (runbook STOP 3). Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 3, spec §0, §2, §4. Branch `trackp-20261026`; the final runs (attempt 6, after the STOP 3 review fixes) are at commit **`fcc7d7d`** (clean tree; recorded in every manifest). Run venv `trackp-gpu` (torch 2.6.0+cu124, transformers 5.19.0, peft 0.21.2, fla 0.5.2, causal-conv1d 1.7.0); bases at the Phase 2 registry pins. Evidence: `trackp_p0_20261026/<base>/{report,manifest}.json`, `toy_sft_metrics.txt`; StartLux comparison in `trackp_p0_20261026/startlux_ref/`.

Procedure per base (`python r1/scripts/trackp.py spike --base <b>`; `r1/c3/train/spike.py`), each under the GPU lease (Track X STATUS check, no foreign compute process, `flock` on `~/r1_locks/gpu0.lock`): load (Kev: Qwen3.5 base + warm start of the released `v1.0` adapter and pointer head through `kev.checkpoint`, base and base revision checked); one 12-option forward; LoRA r = 16, α = 32 (attention, MLP and the five DeltaNet projections on Qwen3.5-family bases; Wqkv/Wo/Wi on Laya — checked in the saved `adapter_config.json`); 13-step toy SFT (13 × batch 8 = one pass over the 100 synthetic E0 examples), soft targets on both outputs (belief RPS + CE, action cost-weighted BCE on u = m), bf16 with gradient checkpointing, lr per spec §4 (2e-5 for Kev and Laya — released adapter/head; 1e-4 fresh LoRA; 1e-3 only for new heads); save → reload into a freshly built wrapper → belief and action probabilities compared; sha256 of the saved adapter, adapter config and heads (the manifest lists them; it is not hashed itself); the seed is set before the model is built (initialisation reproducible); peak VRAM and step time of forward+backward at ~1,024 tokens, batch 8, gradient checkpointing; tree-packing self-check.

## Results (final runs, commit `fcc7d7d`)

| Base | family | trainable params | toy SFT loss (13 steps = 100 examples) | save→reload | packing | input tokens | peak VRAM MiB @~1,024×8, ckpt | step s |
|---|---|---|---|---|---|---|---|---|
| kev-0.8b | kev | 11,350,529 | 3.370 → 2.601 | identical | off: linear attention (expected) | 988 | 3343 | 0.83 |
| qwen3.5-0.8b-base | qwen_control | 10,836,992 | 4.470 → 3.663 | identical | off: linear attention (expected) | 1003 | 3553 | 0.85 |
| startlux-0.8b | startlux | 10,825,729 | 3.393 → 2.203 | identical | off: linear attention (expected) | 1047 | 3629 | 0.93 |
| laya | laya | 33,447,938 | 3.130 → 3.431 | identical | off: encoder packing not implemented | 1002 | 4463 | 1.00 |
| startlux-2b | startlux | 16,825,345 | 2.975 → 1.814 | identical | off: linear attention (expected) | 1047 | 7465 | 1.63 |
| kev-4b | kev | 33,783,809 | 2.969 → 2.372 | identical | off: linear attention (expected) | 988 | 12872 | 3.29 |
| qwen3.5-4b-base | qwen_control | 32,500,736 | 3.610 → 3.264 | identical | off: linear attention (expected) | 1003 | 13554 | 3.35 |
| startlux-4b | startlux | 32,472,577 | 2.947 → 1.673 | identical | off: linear attention (expected) | 1047 | 13746 | 3.61 |

"input tokens" = what each family's model actually receives for the timing prompt under its own framing (Kev: state 697 within its 1,024-token state limit; StartLux: chat framing; Laya: not truncated).

- Every base loads, answers a 12-option question, attaches LoRA, trains on soft targets for both outputs, and reloads to **bit-identical** belief and action probabilities (max diff 0.0); sha256 of adapter, heads and manifest in each `report.json`. No OOM: the largest peak is 13.7 GB of 24 GB (4B bases at ~1,024 tokens × 8 with gradient checkpointing). The measurement runs after the toy SFT, whose AdamW state (LoRA- and head-sized) is still resident, so the peak includes it.
- Tree packing is off on every Qwen3.5-family base (Gated DeltaNet), as the runbook expects; recorded, not a failure. Laya (encoder) has no packing implementation (spec §2.4: little room within 1,024 tokens).
- Toy loss over the 13 steps (batches change every step, so first vs last is a noisy signal; P.0 has no loss criterion): falls for 7 bases, **rises for Laya (3.13 → 3.43)**. Phase 4 (50 steps on one fixed 64-example batch; "loss decreases" judged on the whole batch in eval mode) is the test of this.
- Both Qwen-control runs spike at step 2 (loss 4.47 → 11.36 / 3.61 → 19.74, grad norm 236 / 301) and recover by step 3: the 5 % warm-up rounds to 0 steps for a 13-step run, so Adam's first step moves the new bin-token rows by ~lr = 1e-3 at once. Phase 4's 50 steps get 2 warm-up steps; recorded.

## StartLux: training forward with the bidirectional prompt mask

- The training forward runs in plain transformers 5.19 with the prompt-bidirectional mask of our port (`StartLuxBidirectional`: non-causal key mask for the full-attention layers, stock mask for DeltaNet), whose three self-checks (causal loop = stock forward, padding invariance, a late token reaches position 0) pass on the real weights (`ours_check` in `startlux_ref/ref_*.json`), and it trains (loss above) with identical reload.
- **Port vs StartLux's own code.** StartLux's `bidirectional.py` runs only under transformers 5.8, so a second venv `trackp-sl58` (torch 2.6.0+cu124, transformers 5.8.1, the same fla/causal-conv1d) loads each Instant folder as `startlux_decide.backends.transformers` does, calls `bidirectional.enable` (its self-checks pass) and `text_forward`; letter logits at the last token on the same 20 prompts (E0 test prompts in StartLux's trained format), bf16:

| size | max \|Δ logit\| port vs reference | mean of per-prompt max | max TV | control: causal vs bidirectional mask (max / mean) |
|---|---|---|---|---|
| 0.8B | 0.109 | 0.065 | 0.021 | 1.66 / 1.10 |
| 2B | 0.141 | 0.081 | 0.019 | 2.44 / 0.88 |
| 4B | 0.119 | 0.075 | 0.022 | 2.69 / 1.49 |

  bf16 noise floor (0.8B): our port bf16 vs fp32, max 0.093, mean 0.047. The port agrees with StartLux's own code at about 1.2–1.4 × the bf16 noise floor (two independent bf16 paths, each carrying its own rounding), and 12–19 × below what a mask error produces (the control column). The comparison runs were re-run at commit `fcc7d7d` under the GPU lease (Track X and process checks, pid logged), and each `ref_*.json` records the commit and exact command of both steps. Attempt 1 of this comparison in fp32 failed in the reference code itself ("No available kernel": StartLux restricts SDPA to flash/memory-efficient kernels, unavailable for fp32 + GQA under torch 2.6); run in bf16 (their release precision).
- **vLLM-plugin path: not run.** vLLM (0.31.0 / 0.19.1) is not installed on the portal, and installing it is outside the runbook's tool set; recorded per the runbook's "if that path can be run". So StartLux's own serving path is unverified here; the comparison above is against StartLux's transformers reference instead.
- **Rung decision (trainable candidate vs inference-only zero-shot rung): pending author** (runbook STOP 3). Engineering evidence above supports "trainable"; licence CC BY-NC 4.0 (research use).

## Attempts (recorded per the author's overnight rule; every attempt is in `attempts_driver_logs.txt` and `~/r1_trackp/runs/p0/attempt*`)

| # | What happened | Cause | Fix |
|---|---|---|---|
| 1 | kev-0.8b OOM in the toy SFT (20.7 GB allocated) | toy SFT trained without gradient checkpointing (spec §4 requires it); explained | spike enables gradient checkpointing on the card (`fd251e1`) |
| 2 | kev-0.8b passed, manifest `dirty` | uncommitted fix | committed; rerun from a clean tree |
| 3 | 3 passed (kev-0.8b, laya, kev-4b); StartLux ×3 `Expected x.is_cuda()`; Qwen ×2 `Qwen3_5Config has no vocab_size`; Laya loss 6 → 91, kev-4b rising | StartLux/Qwen bases were loaded on CPU, so the wrapper's self-check hit the CUDA-only causal-conv1d kernel; the packing check read the composite (multimodal) config instead of its text config — which would also have hidden the linear-attention layers; the spike hard-coded lr 1e-4 for everything | load on the target device; read `text_config`; lr groups per spec §4 via `new_head_parameters` (`c95feb5`) |
| 4 | all 8 ran; Laya initial loss 54 | Laya's [CLS] state after its head layers is large: a fresh linear action head started at logit ≈ −309 (cost-weighted BCE ≈ 106) | new heads (action, cumulative) read a LayerNorm-ed state (`c04a237`); Laya's initial action loss 106 → 0.72 |
| 5 | all 8 pass | — | STOP 3 review: seed set after the model was built (init not reproducible), 80 of 100 toy examples used, probe length not recorded, Kev pointer temperature implicit; fixed at `fcc7d7d` |
| 6 | all 8 pass (table above); StartLux comparisons re-run under the lease | — | — |

## Deviations / items for the reviewer and the author

1. New-head parametrisation: LayerNorm before the action and cumulative heads (spec: "Linear (hidden → 1)"), all families (attempt 4).
2. Kev pointer temperature (corrected; the first version of this report said the released temperature was applied in eval mode — it was not: `warm_start` does not set it, and T = 1 was measured in train and eval mode). Policy now explicit: T = 1 for training and evaluation (calibration is ours: E5 temperature scaling); `native_temperature=True` applies Kev's released T (2.35 / 2.41) for the E1 zero-shot rung only; released and active T are recorded in the saved manifest and restored by `load` (tests). Author to confirm (Q3).
3. Qwen3.5 base checkpoints (and StartLux) load as `*ForConditionalGeneration` with their vision towers resident (unused); memory numbers include them.
4. Laya's toy loss rose and its [CLS]-based action logits are nearly constant across prompts at init (0.3 for all 8) — the action readout for Laya may need another state (e.g. the mean of the marker states); Phase 4 will show whether it trains.
5. For Phase 5 (E0), to be decided before it runs: with the spec §4 lr policy the E0 head-fit step trains released heads (Kev's pointer head, Laya's decision head) at 2e-5, close to a no-op in 200 steps; StartLux's softmax-12 readout (tied letter embeddings) has nothing trainable in the head-fit step.

## Reproducibility note (reviewer's re-run)

On the GPU the same seed reproduces the initialisation, the first forward, step-1 loss, peak memory and every pre-training file exactly; after 13 training steps the weights differ in the last digits (final loss 2.20324 vs 2.20330 for startlux-0.8b) — non-deterministic CUDA backward kernels. Before the multi-seed evidence phases (P.3a/P.4) either enable deterministic algorithms where available or state this in the appendix. (`bf16_noise_0.8b.json` was derived offline from the two committed `io` files of the comparison runs.)

## GPU use

Lease log `trackp_p0_20261026/gpu_lease_log.txt`: 58 leased jobs since Phase 2 began (incl. the reviewers' re-runs), 33.8 minutes in total (all of Phases 2–3), no Track X job and no foreign compute process seen at any start.

## Questions for the author

1. **StartLux rung: trainable candidate or inference-only zero-shot rung** (runbook STOP 3; PLAN row).
2. The LayerNorm on the new heads (deviation 1).
3. Kev pointer temperature policy (deviation 2).
4. E0 head-fit design for released heads and StartLux softmax-12 (deviation 5), before Phase 5.
