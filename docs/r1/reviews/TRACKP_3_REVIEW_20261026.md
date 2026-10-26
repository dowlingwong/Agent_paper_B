# Track P Phase 3 (P.0 spikes) — independent review

- **Reviewer:** independent Claude Code subagent on zhixu portal (AI-assisted). It did not see the work while it was in progress.
- **Date:** 26 Oct 2026 (UTC).
- **Scope:** runbook `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` §0 and Phase 3, spec `docs/r1/TRACK_P_POST_TRAINING.md` §0, §2, §4, PLAN rows R1-C3-POST and R1-PORTAL-SCHEDULE. Branch `trackp-20261026`, range `7a4b74b..add7fd6`. Deliverable: `docs/r1/reports/TRACKP_P0_SPIKES_20261026.md` plus `docs/r1/reports/trackp_p0_20261026/`. Run outputs: `~/r1_trackp/runs/p0/`.
- **Evidence label:** ENGINEERING_ONLY.
- **Note on the tree:** while this review ran, the implementation agent's clone had uncommitted Phase 4 edits (`spike.py`, `trackp.py`, `test_trackp_cli.py`), and it committed and pushed `1e3fe3e` ("Phase 4 prep") on top of `add7fd6`. I reviewed only `add7fd6`, using a clean local clone in my scratch directory. Nothing after `add7fd6` is covered here.

## What I re-ran, and the results

| # | Check | Result |
|---|---|---|
| R1 | CPU tests at `add7fd6` (clean clone, `trackp-cpu` venv, `CUDA_VISIBLE_DEVICES=""`, `r1/tests/test_trackp_*.py`) | **153 passed**, 0 failed (3:55). A plain `git archive` copy gives 3 failures, but only because the manifest tests need a git checkout. That is not a code defect. |
| R2 | sha256 of every saved file (`saved/adapter/*`, `heads.safetensors`) against `report.json` `saved_sha256`, for all 8 bases | All match. |
| R3 | Report and manifest copies in `docs/…/trackp_p0_20261026/<base>/` against `~/r1_trackp/runs/p0/<base>/` | Identical for all 8. The committed `gpu_lease_log.txt` is byte-identical to `~/r1_trackp/runs/gpu_lease_log.jsonl` as it stood before my run. |
| R4 | Loss first/last recomputed from `toy_sft/metrics.jsonl`; 10 steps each | Match the table for all 8. |
| R5 | `adapter_config.json`, all 8 | r = 16, α = 32. Qwen3.5-family bases (Kev, control, StartLux): q/k/v/o, gate/up/down plus the 5 DeltaNet projections `in_proj_qkv/z/a/b`, `out_proj`. This target set is identical to Kev's released `adapter_config.json`. Adapter keys cover 36 linear-attention and 12 full-attention modules on 0.8B, and no vision-tower module. Laya: `Wqkv`, `Wo` (attention and MLP), `Wi`. |
| R6 | Manifests, all 8 | Paper commit `c04a237`, `dirty: false`. Harness `264011e` clean. Base and adapter revisions all appear in `r1/c3/train/registry.yaml`. Kev warm-start `weights_sha256` and `head_sha256` equal the registry sha256 of the released v1.0 files. |
| R7 | GPU lease | Every final run and every attempt has a start/end pair in the lease log with a matching pid. 42 pairs and 24.4 min in total, as the report says. `c04a237` was committed at 05:33:20Z and the final batch started at 05:33:21Z. |
| R8 | Actual prompt length of the 1,024-token probe under each family's own tokenizer and framing (CPU, tokenizers only, code at `add7fd6`) | Kev **988** tokens per row (state 697 < `max_state` 1024; strict encode, no cut). Qwen control **1,003**. StartLux **1,047** (chat framing). Laya **1,002**, `truncated: false`, `max_len` 1,024. So "~1,024" holds for every family. |
| R9 | StartLux bf16 noise floor recomputed from `startlux_ref/io_0.8b.json` vs `io_0.8b_fp32.json` (same token ids) | max 0.0933, mean 0.0467. Matches `bf16_noise_0.8b.json`. All three fp32 reference attempts (0.8B, 2B, 4B) fail with "No available kernel", as reported. |
| R10 | **One GPU job:** `trackp.py spike --base startlux-0.8b` from the clean clone at `add7fd6`. Before starting: `origin/main` = GitHub `main` `b5a7aec` (checked with `ls-remote`), STATUS.md showed no running Track X B1/B2 phase, and `nvidia-smi` listed no compute app. The CLI took the lease itself (lease-log lines at 05:55:54Z–05:56:31Z, pid 3592442). Output in my scratch directory. | rc 0. Reproduced exactly: trainable params 10,825,729; peak VRAM **3629.29 MiB** (identical); step time 0.932 s (0.933 originally); packing result; reload identical (belief and action max diff 0.0); data-manifest hash. **Not reproduced:** forward-one action 0.730 (originally 0.647), toy loss 3.591 → 2.194 (originally 3.457 → 2.209), and the adapter and heads sha256. See finding 2. |

## Per-base check of the P.0 items (at `add7fd6`; evidence = report.json, manifest.json, metrics, saved files, code)

| Item | kev-0.8b | kev-4b | qwen-0.8b | qwen-4b | laya | sl-0.8b | sl-2b | sl-4b |
|---|---|---|---|---|---|---|---|---|
| load (registry revision, clean commit) | ok | ok | ok | ok | ok | ok | ok | ok |
| one 12-option forward (shape [1,12], sum 1) | ok | ok | ok | ok | ok | ok | ok | ok |
| LoRA r=16 (+DeltaNet on Qwen3.5 bases) | ok | ok | ok | ok | ok (Wqkv/Wo/Wi) | ok | ok | ok |
| toy SFT, soft belief targets + action loss | ok | ok | ok | ok (loss up, spiky) | ok (loss up) | ok | ok | ok |
| save → fresh wrapper → reload, belief **and** action identical | ok* | ok* | ok | ok | ok | ok | ok | ok |
| sha256 recorded and re-verified | ok | ok | ok | ok | ok | ok | ok | ok |
| peak VRAM / step time @ ~1,024 tok × 8, grad ckpt | ok | ok | ok | ok | ok | ok | ok | ok |
| packing acceptance (recorded) | off (DeltaNet) | off | off | off | not impl. | off | off | off |

\* Kev's reload is identical only because the rebuild warm-starts again from Kev's `head.pt`. See finding 1.

Code paths checked: `spike.spike` computes `b0, a0` in eval mode on the trained model before saving. It moves the trained model to CPU, then calls `rebuild()`, which is `_build`'s `make()`, a freshly built wrapper on the GPU. `load()` verifies every sha256 and refuses a partial adapter. The check compares belief **and** action with `torch.equal`. Peak and step time come from 3 forward+backward steps at batch 8 with gradient checkpointing enabled through the PEFT model (non-reentrant), with no optimizer step, so the weights do not change before the reload check. The StartLux training forward goes through `StartLuxBidirectional.hidden` → `body(...)` with a per-layer-type mask mapping, so the checkpointed layers receive the bidirectional key mask in training too.

## Findings

### 1. Kev's pointer-head temperature is not in the saved artifact, and trained Kev models are evaluated at T ≠ 1 — **blocking**

- **Claim (report, deviation 2):** "Kev's pointer head carries its calibration temperature from `head.pt` (2.35 / 2.41) … reloaded probabilities and E1 zero-shot use Kev's calibrated head, training sees T = 1."
- **Observation:**
  - `kev.model.PointerHead.temperature` is a plain attribute, not a parameter or buffer. `heads.safetensors` for kev-0.8b holds only `action.*` and `pointer.{q,k}.*`. Neither `saved/manifest.json` nor the run manifest records T or the warm-start source as part of the saved model.
  - The reload in `spike` gives identical probabilities only because `make()` warm-starts again from the released `head.pt`, which restores T. A saved Kev model loaded any other way (for example the H.5 sidecar loader, or a wrapper built without `init_from`) would give different probabilities.
  - Separately, the pointer head is trained at T = 1 and then evaluated (eval mode: `predict`, `probs`, E0 metrics) at Kev's original T = 2.35/2.41. That flattens the trained belief and biases E0's width slope and every Kev calibration metric. This matters from Phase 4/5 on, not for the pass/fail of P.0.
- **Required fix:** decide and record the T policy, for example T = 1 for any model whose pointer head we trained, with T kept only for E1 zero-shot. Save T with the heads, or in the saved manifest, and have `load()` set it. Add a test that reloads a saved Kev model into a wrapper whose T differs from the saved one (or that is built without `init_from`) and gets identical probabilities. Update deviation 2.

### 2. The run seed does not control initialisation, so runs at a fixed seed are not reproducible — **blocking (cheap)**

- **Claim:** every manifest records `"seed": 0`, and spec §4 asks for three training seeds with mean ± s.e.
- **Observation:** my re-run of `startlux-0.8b` at the same commit and seed gave a different forward-one action (0.730 vs 0.647), a different toy loss trajectory (3.591 vs 3.457 at step 1), and different adapter and heads sha256. Cause: `trackp.py _build()` creates the wrapper (random LoRA A matrices, new action/cumulative heads) **before** `spike()` calls `seed_everything(seed)`. `cmd_toy` and `cmd_e0` have the same order. Peak VRAM, step time, reload identity and the data hash did reproduce. Cosmetic side issue: `adapter_config.json` stores `target_modules` in set order, which changes between processes, so its sha256 also differs between identical runs.
- **Required fix:** seed before building the model in every subcommand (`spike`, `toy`, `e0`, `probes`). Add a tiny-model test showing that two builds and short trains at the same seed give identical saved sha256 (excluding or normalising `adapter_config.json`). State in the report that the P.0 numbers come from one unseeded initialisation. The P.0 items do not need a rerun.

### 3. The measured probe length is not recorded — minor

- **Claim:** "peak VRAM and step time of forward+backward at ~1,024 tokens".
- **Observation:** `report.json` records `probe_tokens: 1024`, which is the target length of the neutral text, not the length of the sequence the model actually received. My measurement (R8) confirms ~1,024 for every family: Kev 988, Qwen 1,003, StartLux 1,047, Laya 1,002 untruncated.
- **Required fix:** record the actual input length per base in `peak_and_step_time` (and Laya's `truncated` flag), and put the values in the report table.

### 4. "Peak excludes optimizer state" is inaccurate — minor

- **Observation:** during the measurement the `Trainer` object `tr`, and with it its AdamW state, is still alive. `reset_peak_memory_stats` therefore starts from an allocation that includes the optimizer state. What the measurement leaves out is the transient memory of an optimizer step.
- **Required fix:** correct the sentence, or free the trainer before measuring and say so.

### 5. Report wording on sha256 and "100-example" — minor

- "sha256 of adapter, heads and manifest in each `report.json`": `saved_sha256` lists the adapter files and `heads.safetensors`. The saved `manifest.json` is not hashed in the report. Fix the wording or add its hash.
- The toy SFT runs 10 steps × batch 8 = 80 examples. Twenty of the 100 rows hashed in the data manifest are never trained on. Say "10 steps drawn from a 100-example set", or run one full epoch (13 steps).

### 6. StartLux comparison: provenance and wording — minor

- **Claim:** "The port agrees with the reference at the bf16 noise level, an order of magnitude below a mask error."
- **Observation:** the evidence is sound. Port vs StartLux's own 5.8 code gives max |Δ| 0.109 / 0.141 / 0.119. The reference's own causal mask gives 1.66 (mean 1.10). Our own self-checks (causal = stock, padding invariance, late-token reach) and StartLux's checks pass on the real weights. The comparison uses StartLux's trained prompt format from its own `startlux_decide.prompt`. However:
  1. Port vs reference (0.8B: max 0.109, mean 0.065) is about 1.2–1.4× our bf16-vs-fp32 floor (0.093 / 0.047), not within it. The floor was measured only on 0.8B and only for our port.
  2. The `--ours` / `--reference` and control jobs ran before `c04a237`, at `c95feb5` by timing. That is a heads-only change and does not affect letter logits. But no output records the commit, the bf16-noise calculation has no committed script, and the seven "(flock)" lease entries have no pid and no record that the STATUS and `nvidia-smi` checks were done.
  3. The comparison runs in eval mode with a zero-initialised LoRA. That is fine for "correct mask". The training forward itself is evidenced by the spike (finite loss, training, reload), not by the comparison.
- **Required fix:** reword to "close to the bf16 noise floor (≈1.2–1.4×), ≥ 10× below a mask error". Record the commit and the exact commands (and how the Track X / foreign-process checks were done) for the startlux_ref jobs, and commit the noise-floor snippet or describe it.

### 7. vLLM statement — minor

- **Claim:** "vLLM … is not installed on the portal; installing it is a new tool outside the runbook and its CUDA requirements exceed driver 535."
- **Observation:** the first half is correct and sufficient: the runbook says "if that path can be run", and installs are outside scope. The driver claim is not substantiated. CUDA 12 minor-version compatibility lets CUDA 12.x builds run on 535, and torch cu124 runs on this driver.
- **Required fix:** drop or substantiate the driver claim. Tell the author explicitly that StartLux's serving path (vLLM plugin) remains unverified. This matters if the author picks the inference-only rung. The 5.8 transformers backend from StartLux's own package is the stand-in reference.

### 8. E0 head-fit learning rates changed in passing (`c95feb5`) — minor (decide before Phase 5)

- **Observation:** in `exam_run.e0` the frozen-backbone head-fit step now trains released belief heads (Kev pointer, Laya scorer/head) at the base lr of 2e-5 instead of 1e-3. Only new heads keep 1e-3. That follows spec §4 literally, but 200 steps at 2e-5 make §5.5's "train the belief head (frozen backbone)" close to a no-op for Kev and Laya. Separately, and already the case before Phase 3: for StartLux with softmax-12, the belief readout (letter embeddings) has no trainable parameter in the head-fit step.
- **Required fix:** list this as a deviation in the report and put it to the author/Phase 5 as a decision. It is not a P.0 defect.

### 9. No unit tests for the Phase 3 code changes — minor

- **Observation:** `7a4b74b..add7fd6` changes `model.py`, `packing.py`, `spike.py`, `exam_run.py` and `trackp.py` but no test. The existing 153 tests pass.
- **Required fix:** add small CPU tests for:
  - `new_head_parameters`: excludes released heads and includes the action/cumulative heads and the Qwen token rows;
  - `packing.text_config` / `has_linear_attention` on a composite config with `text_config.layer_types`;
  - the LayerNorm head shape and the save/load key names.

### 10. Toy-loss behaviour is only partly described — minor

- **Observation:** the report notes that loss rose for Laya and qwen3.5-4b. It does not mention that both Qwen control runs spike at step 2 (loss 11.4 and 19.8, grad norm 235 and 302) with no warm-up (`warmup_frac` 0.05 × 10 steps = 0). That points to 1e-3 on the new token rows. Laya's action logits are nearly constant at init, which the report does mention.
- **Required fix:** mention the spikes and keep both points as watch items for Phase 4. There is no P.0 criterion on loss, so this is not a failure.

### 11. LayerNorm before the new heads (`c04a237`) — observation, no fix required

- The change is sound: it removes the logit ≈ −300 initial state on Laya's [CLS] (attempt 4, verified in `attempt4/laya/report.json`, forward action 1.0, loss 54 → final 3.2). It is correctly flagged as a spec deviation for the author.
- Side effect: head key names changed (`action.weight` → `action.{0,1}.*`), so heads saved before `c04a237` no longer load. No evidence checkpoint predates it.

### Other code changes, judged correct

- Gradient checkpointing in `spike` and `toy`: spec §4; attempt 1's OOM is explained.
- Loading on the target device with `device_map={"": device}`: fixes attempt 3's CPU-tensor causal-conv1d error.
- `text_config` in the packing check: fixes the `vocab_size` error and, as the report correctly notes, would otherwise have hidden the DeltaNet layers.
- `new_head_parameters` lr groups: spec §4.
- Reload with never two copies on the card.
- OOM recorded as an E4 data point.

I found no regression beyond findings 1, 2 and 8.

## Honesty, attempts and ground rules

- **Attempts table:** complete and matches the driver logs, the lease log and the run directories: attempt 1 OOM (log shows 20.67 GiB allocated); attempt 2 dirty at `a1b69b4`; attempt 3 at `fd251e1` with 3 passes, 3× `Expected x.is_cuda()`, 2× `Qwen3_5Config has no vocab_size`; attempt 4 at `c95feb5`; attempt 5 at `c04a237`. The fp32 StartLux reference attempt is reported. All three sizes failed, but only the 0.8B log is committed; the others are in `runs/p0/startlux_ref/attempt1_fp32/`.
- **Criteria:** none relaxed. No failure is hidden. The loss rises are disclosed.
- **Commits:** all five in range are authored and committed by `Dowling Wong <wangdowling@gmail.com>` and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Pushes:** only `trackp-20261026` is this agent's. `main` is unchanged at `b5a7aec`.
- **Secrets:** the diff and the run outputs contain no secrets or references to the secrets file.
- **Track X priority:** `gpu_lease` checks STATUS on `origin/main` and foreign compute processes before every `trackp.py` job. No Track X phase was running. For the "(flock)" StartLux reference jobs, see finding 6.2.

## Verdict

**Verdict: pending fixes.** Blocking: findings 1 (Kev temperature not saved; train/eval T mismatch) and 2 (seed applied after model construction). Minor: 3–10. The P.0 engineering evidence itself holds: all 8 bases load, forward, train on soft belief targets with the action loss, reload bit-identically (belief and action), fit in ≤ 13.7 GB at ~1,024 tokens × 8 with checkpointing, and record packing. The StartLux bidirectional training forward in plain transformers is shown and agrees with StartLux's own 5.8 implementation close to bf16 noise. None of the fixes requires re-running the P.0 spikes, except optionally to record the measured probe lengths (finding 3).


## Implementation agent's response (26 Oct)

Code fixes in `fcc7d7d`; P.0 re-run at that commit (attempt 6, all 8 pass) and the StartLux comparisons re-run under the lease; report and evidence updated.

1. Partly a report error, fixed in both. Measured on the real Kev-0.8B: `warm_start` loads the head's state dict but never sets `temperature`; it was 1.0 in train and eval mode, so training and evaluation agreed and the reload was consistent — the report's deviation 2 (which said the released T was applied in eval) was wrong. The real gap — an implicit, unsaved policy — is fixed: T = 1 by default; `native_temperature=True` applies the released T (E1 zero-shot only); released and active T recorded in the manifest and restored by `load` (the saved policy wins); test `test_kev_pointer_temperature_policy_is_explicit_and_saved`. Report deviation 2 corrected; author Q3.
2. Fixed: `seed_everything(args.seed)` before `_build` in spike/toy/e0/probes; `adapter_config.json` written with sorted `target_modules`; tests `test_seed_controls_initialisation_and_saved_files_are_reproducible` (in process) and `test_same_seed_in_two_processes_saves_identical_files` (two processes: adapter and heads sha256 equal; config equal apart from the tiny stand-in's base path).
3. Fixed: `engineering.input_tokens` = tokens the family's model actually receives (988 / 1003 / 1047 / 1002), in every report and in the table.
4. Wording fixed: the peak includes the resident AdamW state of the toy run.
5. Wording fixed (manifest not hashed itself); spike now 13 steps = one pass over the 100 examples (config `spike.steps`).
6. Fixed: the report says 1.2–1.4 × the noise floor and 12–19 × below a mask error; the comparison script now takes the GPU lease itself (checks, pid), records commit and exact command of both steps, and computes the causal-mask control for every size; re-run at `fcc7d7d` (numbers unchanged).
7. Fixed: vLLM wording ("not installed; outside the runbook's tool set"); the author is told the serving path is unverified.
8. Recorded as a decision before Phase 5 (report deviation 5, Q4): no code change now.
9. Fixed: tests for `new_head_parameters`, LayerNorm heads, composite-config packing check, temperature policy, seed reproducibility (5 + 1 new tests; CPU suite 159 passed).
10. Recorded in the report (warm-up rounds to 0 steps in a 13-step run; Adam's first step on the new token rows).
