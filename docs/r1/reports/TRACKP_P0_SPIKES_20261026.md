# Track P Phase 3 — P.0 spikes (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on zhixu portal). **ENGINEERING_ONLY.** **Status: pending independent review (STOP 3); then the author decides the StartLux rung.** Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 3, spec §0, §2, §4. Branch `trackp-20261026`; the final runs are at commit **`c04a237`** (clean tree; recorded in every manifest). Run venv `trackp-gpu` (torch 2.6.0+cu124, transformers 5.19.0, peft 0.21.2, fla 0.5.2, causal-conv1d 1.7.0); bases at the Phase 2 registry pins. Evidence: `trackp_p0_20261026/<base>/{report,manifest}.json`, `toy_sft_metrics.txt`; StartLux comparison in `trackp_p0_20261026/startlux_ref/`.

Procedure per base (`python r1/scripts/trackp.py spike --base <b>`; `r1/c3/train/spike.py`), each under the GPU lease (Track X STATUS check, no foreign compute process, `flock` on `~/r1_locks/gpu0.lock`): load (Kev: Qwen3.5 base + warm start of the released `v1.0` adapter and pointer head through `kev.checkpoint`, base and base revision checked); one 12-option forward; LoRA r = 16, α = 32 (attention, MLP and the five DeltaNet projections on Qwen3.5-family bases; Wqkv/Wo/Wi on Laya — checked in the saved `adapter_config.json`); 10-step toy SFT on 100 synthetic E0 examples, soft targets on both outputs (belief RPS + CE, action cost-weighted BCE on u = m), bf16 with gradient checkpointing, lr per spec §4 (2e-5 for Kev and Laya — released adapter/head; 1e-4 fresh LoRA; 1e-3 only for new heads); save → reload into a freshly built wrapper → belief and action probabilities compared; sha256 of the saved files; peak VRAM and step time of forward+backward at ~1,024 tokens, batch 8, gradient checkpointing; tree-packing self-check.

## Results (final runs, commit `c04a237`)

| Base | family | trainable params | toy SFT loss (10 steps) | save→reload | packing | peak VRAM MiB @1024×8, ckpt | step s |
|---|---|---|---|---|---|---|---|
| kev-0.8b | kev | 11,350,529 | 3.393 → 2.930 | identical | off: linear attention (expected) | 3343 | 0.83 |
| qwen3.5-0.8b-base | qwen_control | 10,836,992 | 4.470 → 4.260 | identical | off: linear attention (expected) | 3553 | 0.85 |
| startlux-0.8b | startlux | 10,825,729 | 3.457 → 2.209 | identical | off: linear attention (expected) | 3629 | 0.93 |
| laya | laya | 33,447,938 | 3.211 → 3.636 | identical | off: encoder packing not implemented | 4463 | 1.00 |
| startlux-2b | startlux | 16,825,345 | 2.798 → 1.808 | identical | off: linear attention (expected) | 7465 | 1.63 |
| kev-4b | kev | 33,783,809 | 2.742 → 2.599 | identical | off: linear attention (expected) | 12872 | 3.29 |
| qwen3.5-4b-base | qwen_control | 32,500,736 | 3.610 → 4.580 | identical | off: linear attention (expected) | 13554 | 3.35 |
| startlux-4b | startlux | 32,472,577 | 3.062 → 1.755 | identical | off: linear attention (expected) | 13746 | 3.61 |

- Every base loads, answers a 12-option question, attaches LoRA, trains on soft targets for both outputs, and reloads to **bit-identical** belief and action probabilities (max diff 0.0); sha256 of adapter, heads and manifest in each `report.json`. No OOM: the largest peak is 13.7 GB of 24 GB (4B bases at 1,024 tokens × 8 with gradient checkpointing). Peak excludes optimizer state (LoRA-sized).
- Tree packing is off on every Qwen3.5-family base (Gated DeltaNet), as the runbook expects; recorded, not a failure. Laya (encoder) has no packing implementation (spec §2.4: little room within 1,024 tokens).
- Toy loss over 10 steps (batches change every step, so first vs last is a noisy signal; P.0 has no loss criterion): falls for 6 bases, **rises for Laya (3.21 → 3.64) and qwen3.5-4b-base (3.61 → 4.58)**. Phase 4 (50 steps on one fixed 64-example batch, "loss decreases") is the test of this; noted here.

## StartLux: training forward with the bidirectional prompt mask

- The training forward runs in plain transformers 5.19 with the prompt-bidirectional mask of our port (`StartLuxBidirectional`: non-causal key mask for the full-attention layers, stock mask for DeltaNet), whose three self-checks (causal loop = stock forward, padding invariance, a late token reaches position 0) pass on the real weights (`check_report` in `startlux_ref/ref_*.json`), and it trains (loss above) with identical reload.
- **Port vs StartLux's own code.** StartLux's `bidirectional.py` runs only under transformers 5.8, so a second venv `trackp-sl58` (torch 2.6.0+cu124, transformers 5.8.1, the same fla/causal-conv1d) loads each Instant folder as `startlux_decide.backends.transformers` does, calls `bidirectional.enable` (its self-checks pass) and `text_forward`; letter logits at the last token on the same 20 prompts (E0 test prompts in StartLux's trained format), bf16:

| size | max \|Δ logit\| port vs reference | mean of per-prompt max | max TV distance |
|---|---|---|---|
| 0.8B | 0.109 | 0.065 | 0.021 |
| 2B | 0.141 | 0.081 | 0.019 |
| 4B | 0.119 | 0.075 | 0.022 |

  Controls (0.8B): our port's own bf16 vs fp32 deviation (bf16 noise floor) max 0.093, mean 0.047; StartLux's reference with the **causal** mask vs its bidirectional read-out (what a mask error looks like) max 1.66, mean 1.10. The port agrees with the reference at the bf16 noise level, an order of magnitude below a mask error. Attempt 1 of this comparison in fp32 failed in the reference code itself ("No available kernel": StartLux restricts SDPA to flash/memory-efficient kernels, unavailable for fp32 + GQA under torch 2.6); rerun in bf16 (their release precision).
- **vLLM-plugin path: not run.** vLLM (0.31.0 / 0.19.1) is not installed on the portal; installing it is a new tool outside the runbook and its CUDA requirements exceed driver 535. Recorded per the runbook's "if that path can be run".
- **Rung decision (trainable candidate vs inference-only zero-shot rung): pending author** (runbook STOP 3). Engineering evidence above supports "trainable"; licence CC BY-NC 4.0 (research use).

## Attempts (recorded per the author's overnight rule; every attempt is in `attempts_driver_logs.txt` and `~/r1_trackp/runs/p0/attempt*`)

| # | What happened | Cause | Fix |
|---|---|---|---|
| 1 | kev-0.8b OOM in the toy SFT (20.7 GB allocated) | toy SFT trained without gradient checkpointing (spec §4 requires it); explained | spike enables gradient checkpointing on the card (`fd251e1`) |
| 2 | kev-0.8b passed, manifest `dirty` | uncommitted fix | committed; rerun from a clean tree |
| 3 | 3 passed (kev-0.8b, laya, kev-4b); StartLux ×3 `Expected x.is_cuda()`; Qwen ×2 `Qwen3_5Config has no vocab_size`; Laya loss 6 → 91, kev-4b rising | StartLux/Qwen bases were loaded on CPU, so the wrapper's self-check hit the CUDA-only causal-conv1d kernel; the packing check read the composite (multimodal) config instead of its text config — which would also have hidden the linear-attention layers; the spike hard-coded lr 1e-4 for everything | load on the target device; read `text_config`; lr groups per spec §4 via `new_head_parameters` (`c95feb5`) |
| 4 | all 8 ran; Laya initial loss 54 | Laya's [CLS] state after its head layers is large: a fresh linear action head started at logit ≈ −309 (cost-weighted BCE ≈ 106) | new heads (action, cumulative) read a LayerNorm-ed state (`c04a237`); Laya's initial action loss 106 → 0.72 |
| 5 | all 8 pass (table above) | — | — |

## Deviations / items for the reviewer and the author

1. New-head parametrisation: LayerNorm before the action and cumulative heads (spec: "Linear (hidden → 1)"), all families (attempt 4).
2. Kev's pointer head carries its calibration temperature from `head.pt` (2.35 / 2.41); `kev.model` applies it only in eval mode, so reloaded probabilities and E1 zero-shot use Kev's calibrated head, training sees T = 1 (Kev's own behaviour).
3. Qwen3.5 base checkpoints (and StartLux) load as `*ForConditionalGeneration` with their vision towers resident (unused); memory numbers include them.
4. Laya's toy loss rose and its [CLS]-based action logits are nearly constant across prompts at init (0.3 for all 8) — the action readout for Laya may need another state (e.g. the mean of the marker states); Phase 4 will show whether it trains.

## GPU use

Lease log `trackp_p0_20261026/gpu_lease_log.txt`: 42 leased jobs since Phase 2 began, 24.4 minutes in total (all of Phases 2–3), no Track X job and no foreign compute process seen at any start.

## Questions for the author

1. **StartLux rung: trainable candidate or inference-only zero-shot rung** (runbook STOP 3; PLAN row).
2. The LayerNorm on the new heads (deviation 1).
