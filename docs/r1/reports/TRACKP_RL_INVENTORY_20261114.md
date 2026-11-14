# Track P RL inventory and engineering additions — 14 Nov 2026

Status: ENGINEERING_ONLY. AI-assisted (Claude). Mac overnight runbook unit 4. No label table, no audit, no seed
7001–7010, no exam seed and no real data were read or written. Branch `mac-trackp-rl-20261114` from
`mac-int-20261107` (a15300ca).

## 1. What existed before this branch

| Spec item (TRACK_P_POST_TRAINING.md) | Where | State |
|---|---|---|
| R-A losses: RPS, soft CE, Stage S loss | `r1/c3/train/losses.py` (`rps`, `soft_ce`, `stage_s_loss`) | present |
| Action loss (cost-sensitive BCE, used by R-A1 and R-A2) | `losses.py` (`action_loss`) | present |
| R-A3 smoothed-rule ablation loss | `losses.py` (`smoothed_rule_loss`, `rule_value`) | present |
| R-A2 shared action head (its loss updates the shared LoRA) | `r1/c3/train/model.py` (`_Wrapper(head_form, action_head)`) | present |
| R-A1 action head on the **stop-gradient** hidden state | — | **missing** |
| Stop / rollback rule for R-A2, R-A3, R-B (§6.4) | — | **missing** |
| Action vs rule-on-own-belief disagreement metric | `r1/c3/train/metrics.py` | present |
| R-B demonstration writer | `r1/c3/rb_demos.py` | present |
| R-B wrapper (analysis, then bins) | `model.py` `ReasonThenBinWrapper` (`generate`, `forward`) | present |
| R-B GRPO (§6.4) | — | **missing** |
| R-B warm-up loader for the demonstrations | — | **missing** |
| Stage D DAgger aggregation (§6.5) | — | **missing** |
| Per-token analysis log-probabilities (needed by a per-token PPO surrogate) | — | **missing** (only the per-span sum) |
| Kev (`PointerWrapper`) as an R-B base (§6.4: Kev's base LM writes the analysis, the pointer head reads the belief) | — | missing (not added here) |

R-A was therefore partial: R-A0 (rule on the belief) and R-A2/R-A3 losses existed; R-A1 and the stop rule did not.

## 2. What this branch adds

**`r1/c3/train/grpo.py`** — §6.4 as fixed on 28 Oct (R1-RB-GRPO): G = 8; reward
−RPS(p, y_train) + λ_a·1[exec]·clip(u, ±u_max) − 0.5·1[format violation], u_max the 99th percentile of |u| on train;
leave-one-out advantage (primary) and the std-normalised advantage (sensitivity; A = 0 on a constant group);
PPO clipped surrogate ε = 0.2, summed over a completion's tokens, no length normalisation, 2 update epochs per
batch; k3 KL to the reference with β ∈ {0, 0.02} (any other β refused); monitors every step (zero-advantage group
share, clipped-token share, mean per-token KL). `estimator_check` is the §6.3 check (Bernoulli execute, G = 8,
256 prompts, 64 resamples, cosine ≥ 0.95 against the exact gradient of L_action). `rb_group_step` runs one step on
the wrapper interface: G analyses per prompt from `policy.generate`; a format violation when the policy did not
close the span itself (EOS or the 256-token cap before `</analysis>`; `generate` records `last_generated_closed`,
refused if absent); the action sampled from the action logit; the PPO sequence = the **sampled** analysis tokens (the
text, plus the closing tag only when the policy sampled it; never the tag appended to an unclosed span or the trailing
newline) + the action token; the exact RPS gradient added for the belief. The policy runs in eval mode for the step
(LoRA dropout off during sampling, pi_old, pi_theta and the reference), and their modes are restored. Known approximation: analyses are
decoded and re-encoded, so where the tokenizer does not round-trip the scored tokens differ from the sampled ids (134 sampled ids re-encoded to 218 tokens in the reviewer's tiny-Llama probe; the sampled ids must be carried into `forward` before any real R-B run). Constants
LORA_RANK 16, LR_RANGE 1e-6–5e-6, MAX_STEPS 500 are recorded for the run config; nothing here launches a run.

**`r1/c3/train/ra.py`** — R-A1 `DetachedActionHead` (LayerNorm + Linear on `state.detach()` at the belief position, R1-HEADS-LN; trained with `action_loss` via
`ra1_loss` on a wrapper output with `return_state=True`; no gradient reaches the belief or adapters) and `stop_rule`
(§6.4 rollback conditions: ECE rise > 0.02, RPS worse by > 1 s.e. without a utility gain, width ratio < 0.8, entropy
> 20 % below Stage S within 100 steps; the caller supplies the validation metrics and restores the checkpoint).

**`r1/c3/train/dagger.py`** — §6.5 one round per RUNBOOK C.2: rollout, expert-label new states (each new state
labelled once; revisited states reuse their stored label, also for the disagreement), aggregate keyed by state (first
label kept; no relabel, no double count), retrain from scratch on the aggregate. `check_synthetic_seed`
refuses seeds 7001–7010 and ≥ 9001. `offline_rollout` adapts the one-step `OfflineBanditEnv`; on it a round adds no
states beyond the fresh instances, as the module docstring states.

**`r1/c3/train/rb_warmup.py`** — reads `rb_demos` calls into supervised warm-up rows: train split only, analyses
≤ 256 tokens, and a leak guard that the prompt messages equal `build_messages` for the same row;
`format_only_rows` for the format-only warm-up.

**`r1/c3/train/model.py`** — `_span_token_logprobs`; `forward` extras gain `analysis_token_logprob`,
`analysis_token_mask`, `analysis_text_tokens` and `analysis_close_tokens`; `ReasonThenBinWrapper.generate` records
`last_generated_closed`. The existing per-span value is unchanged, and a test checks that the per-token values sum
to it. `segments` returns a 4-field span; its only other callers use the token ids.

## 3. Tests

New: `test_trackp_grpo.py` (numpy, 8), `test_trackp_dagger.py` (6), `test_trackp_rb_warmup.py` (9),
`test_trackp_grpo_torch.py` (8), `test_trackp_ra.py` (6): known-answer advantages, surrogate and k3 on toy groups; the
estimator check (and that too little sampling fails it); autograd agreement of the torch loss; the per-token/per-span
identity; the sampled-token mask; `rb_group_step` on a fake wrapper with the `ReasonThenBinWrapper` interface (belief
RPS falls, the action moves towards execute when u > 0, unclosed analyses are penalised, an EOS-unclosed analysis is a
violation and its appended tag is not scored, eval mode during the step, missing closure records refused); DAgger
labels each new state once; R-A1 detached head (no gradient to the trunk) and each stop-rule condition with its
boundaries; and a tiny end-to-end GRPO run on a random GPT-2 built from a config (vocab 8, 1 layer, dropout 0, rank-16
LoRA on c_attn/c_proj/c_fc, Adam 1e-2, 30 steps, β 0.02) in which the target-token probability rises by more than 0.05
and the late sampled reward exceeds the early one. CPU only; no download.

Not covered here: the real `ReasonThenBinWrapper` tests in `test_trackp_model.py` skip in this environment (the Qwen
tokenizer is not cached and there is no network), so `generate`'s new closure record and `segments`' new span fields are
checked only through the fake wrapper; the reviewer exercised the real wrapper on a tiny Llama.

Regression check (`-k trackp`, whole `r1/tests`, with the CPU shim below): base a15300ca 11 failed / 112 passed /
83 skipped; this branch 11 failed / 149 passed / 83 skipped, the same 11 failures as on the base, none caused by this
branch:
- 3 from the environment (`lightgbm` and `kev` not installed; a gzip byte-identity test);
- **8 TrackPStop guard tests in `test_c3_evidence_other_boundaries.py`, which fail with the pinned harness as well.**
  Cause (reviewer's finding, confirmed): `EVAL_COLUMNS` in `r1/c3/train/run.py` l. 37 matches `eval`/`y_eval`/seed-number
  forms only, so evaluation aliases such as `delta_true`, `se_audit`, `delta_audit_all`, `candidate_metrics` and
  `incumbent_metrics` (in prompt meta or nested sequences) pass the Track P leak guard. This is a **pre-existing guard
  gap on mac-int**, not fixed here (it is outside this unit and changes a guard); flagged for the author.

Environment: a throwaway Python 3.12 venv in /tmp (torch 2.6.0, transformers 5.19.0, peft 0.21.2, NumPy 2.5.4); not the training image.
transformers 5.19 with torch 2.6 raises on import on a CPU-only machine (`torch.accelerator.current_accelerator`);
the torch test module installs a one-line shim when CUDA is absent, and the regression run used the same shim.
On the training image this does not arise; the shim is test-only.

## 4. Not done / for the author

- No training run, no learning-rate choice inside LR_RANGE, no G = 16 memory test (needs the GPU image).
- `rb_group_step` adds the exact RPS gradient for the belief beside the GRPO term on the analysis and action
  tokens; if the author prefers the belief to be trained only through the reward, removing that term is a one-line
  change (not made).
- DAgger expert is injected; wiring it to the 10-seed audit (label half 7001–7005) is C.2 server work.
- **Deferred, not implemented:** Kev as an R-B base (the pointer head reading the belief after a sampled analysis);
  the R-B with/without-analysis ablation (§6.4) as a run configuration; the §6.3 estimator check through the torch
  path on a real head (it is checked in numpy and the torch loss is checked by autograd separately).
- The std-normalised sensitivity advantage uses the population std (ddof 0) and A = 0 on a constant group.
- Teacher demonstrations truncated at the 256-token cap are accepted by the warm-up loader; whether to drop them is
  open.
- The `EVAL_COLUMNS` leak-guard gap (§3).
