# Track P RL inventory and engineering additions — 14 Nov 2026

Status: ENGINEERING_ONLY. AI-assisted (Claude). Mac overnight runbook unit 4. No label table, no audit, no seed
7001–7010, no exam seed and no real data were read or written. Branch `mac-trackp-rl-20261114` from
`mac-int-20261107` (a15300ca).

## 1. What existed before this branch

| Spec item (TRACK_P_POST_TRAINING.md) | Where | State |
|---|---|---|
| R-A losses: RPS, soft CE, Stage S loss | `r1/c3/train/losses.py` (`rps`, `soft_ce`, `stage_s_loss`) | present |
| R-A1 action loss, R-A2 smoothed rule loss | `losses.py` (`action_loss`, `smoothed_rule_loss`, `rule_value`) | present |
| Action head on every wrapper | `r1/c3/train/model.py` (`_Wrapper(head_form, action_head)`) | present |
| Action/expert disagreement metric | `r1/c3/train/metrics.py` | present |
| R-B demonstration writer | `r1/c3/rb_demos.py` | present |
| R-B wrapper (analysis, then bins) | `model.py` `ReasonThenBinWrapper` (`generate`, `forward`) | present |
| R-B GRPO (§6.4) | — | **missing** |
| R-B warm-up loader for the demonstrations | — | **missing** |
| Stage D DAgger aggregation (§6.5) | — | **missing** |
| Per-token analysis log-probabilities (needed by a per-token PPO surrogate) | — | **missing** (only the per-span sum) |

## 2. What this branch adds

**`r1/c3/train/grpo.py`** — §6.4 as fixed on 28 Oct (R1-RB-GRPO): G = 8; reward
−RPS(p, y_train) + λ_a·1[exec]·clip(u, ±u_max) − 0.5·1[format violation], u_max the 99th percentile of |u| on train;
leave-one-out advantage (primary) and the std-normalised advantage (sensitivity; A = 0 on a constant group);
PPO clipped surrogate ε = 0.2, summed over a completion's tokens, no length normalisation, 2 update epochs per
batch; k3 KL to the reference with β ∈ {0, 0.02} (any other β refused); monitors every step (zero-advantage group
share, clipped-token share, mean per-token KL). `estimator_check` is the §6.3 check (Bernoulli execute, G = 8,
256 prompts, 64 resamples, cosine ≥ 0.95 against the exact gradient of L_action). `rb_group_step` runs one step on
the wrapper interface: G analyses per prompt from `policy.generate`, a format violation when an analysis hits the
256-token cap (read from `last_generated_tokens`, refused if absent), the action sampled from the action logit,
the sequence = analysis tokens + action token, and the exact RPS gradient added for the belief. Constants
LORA_RANK 16, LR_RANGE 1e-6–5e-6, MAX_STEPS 500 are recorded for the run config; nothing here launches a run.

**`r1/c3/train/dagger.py`** — §6.5 one round per RUNBOOK C.2: rollout, expert-label new states, aggregate keyed by
state (first label kept; no relabel, no double count), retrain from scratch on the aggregate. `check_synthetic_seed`
refuses seeds 7001–7010 and ≥ 9001. `offline_rollout` adapts the one-step `OfflineBanditEnv`; on it a round adds no
states beyond the fresh instances, as the module docstring states.

**`r1/c3/train/rb_warmup.py`** — reads `rb_demos` calls into supervised warm-up rows: train split only, analyses
≤ 256 tokens, and a leak guard that the prompt messages equal `build_messages` for the same row;
`format_only_rows` for the format-only warm-up.

**`r1/c3/train/model.py`** (+18 lines) — `_span_token_logprobs`; `forward` extras gain `analysis_token_logprob`
and `analysis_token_mask`. The existing per-span value is unchanged, and a test checks that the per-token values
sum to it.

## 3. Tests

New: `test_trackp_grpo.py` (numpy, 8), `test_trackp_dagger.py` (5), `test_trackp_rb_warmup.py` (9),
`test_trackp_grpo_torch.py` (5): known-answer advantages, surrogate and k3 on toy groups; the estimator check;
autograd agreement of the torch loss; the per-token/per-span identity; `rb_group_step` on a fake wrapper with the
`ReasonThenBinWrapper` interface (belief RPS falls, the action moves towards execute when u > 0, capped analyses
are penalised, missing token counts refused); and a tiny end-to-end GRPO run on a random GPT-2 built from a
config (vocab 8, 1 layer, dropout 0, rank-16 LoRA on c_attn/c_proj/c_fc, Adam 1e-2, 30 steps, β 0.02) in which the
target-token probability rises by more than 0.05 and the late sampled reward exceeds the early one. CPU only;
no download.

Regression check (`-k trackp`, whole `r1/tests`): base a15300ca 11 failed / 112 passed / 83 skipped; this branch
11 failed / 139 passed / 83 skipped. The same 11 tests fail on the base, all from the environment
(`lightgbm` and `kev` not installed; a gzip byte-identity test; 8 TrackPStop guard tests that need the pinned
harness), none from this branch.

Environment: a throwaway Python 3.12 venv in /tmp (torch 2.6.0, transformers 5.19.0, peft 0.21.2, NumPy 2.5.4); not the training image.
transformers 5.19 with torch 2.6 raises on import on a CPU-only machine (`torch.accelerator.current_accelerator`);
the torch test module installs a one-line shim when CUDA is absent, and the regression run used the same shim.
On the training image this does not arise; the shim is test-only.

## 4. Not done / for the author

- No training run, no learning-rate choice inside LR_RANGE, no G = 16 memory test (needs the GPU image).
- `rb_group_step` adds the exact RPS gradient for the belief beside the GRPO term on the analysis and action
  tokens; if the author prefers the belief to be trained only through the reward, removing that term is a one-line change (not made).
- DAgger expert is injected; wiring it to the 10-seed audit (label half 7001–7005) is C.2 server work.
