Reviewed base: 2f36614a0f02254774ffcc816a66c5db61d18a8c

# Track P RL (R-B GRPO, Stage D DAgger, R-B warm-up, R-A1 head, stop rule) — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 4. Branch `mac-trackp-rl-20261114` from `mac-int-20261107` (`a15300ca`). Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (three blocking: format penalty missed unclosed analyses and scored a forced tag; eight guard-test failures misdescribed; R-A inventory misstated and R-A1 / stop rule missing).
- Round 2: changes requested (one blocking: no LayerNorm before the new R-A1 head, R1-HEADS-LN).
- Round 3: **accepted** at `2f36614a`.

Accepted commit (round 3, last): 2f36614a0f02254774ffcc816a66c5db61d18a8c

Notes carried to the author (not blocking): the pre-existing `EVAL_COLUMNS` leak-guard gap in `r1/c3/train/run.py` (8 TrackPStop tests fail on mac-int already); sampled analysis ids must be carried into `forward` before any real R-B run (decode/re-encode does not round-trip); the closing tag gets no PPO credit if a tokenizer merges `</analysis>` with the newline (safe direction); Kev as R-B base, the with/without-analysis ablation and the torch-path estimator check are deferred.

The round texts are reproduced unchanged below.

---

Reviewed commit: ce368690a02e2e298f54be5972b97ca4bd21e192

# Independent review: unit 4 (Track P RL), round 1

Branch `mac-trackp-rl-20261114` in /tmp/pb/wt/tprl, base a15300ca (`mac-int-20261107`). Reviewer: independent agent. I did not write this code. I read the commit diff, spec §0.2, §6.3, §6.4 and §6.5, PLAN R1-RB-GRPO, R1-BX-D11 and R1-WORDING-30OCT, RUNBOOK C.2/P.6, and unit 4 of the overnight runbook (69b3576b). I did not edit the repo.

## What I ran

- The new tests: `pytest r1/tests/test_trackp_grpo.py r1/tests/test_trackp_grpo_torch.py r1/tests/test_trackp_dagger.py r1/tests/test_trackp_rb_warmup.py` gave **27 passed** (8 + 5 + 5 + 9, matching the report).
- Regression on the branch (`shim_pytest.py -k trackp r1/tests`, AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin): **11 failed / 139 passed / 83 skipped**.
- Regression on the base: I extracted a15300ca with `git archive` into /tmp/pb/review_u4_base, so no worktree metadata was written into the repo. Result: 12 failed / 111 passed / 83 skipped. The extra failure is `test_trackp_trainer.py::test_manifest_records_commits_and_hashes`, which needs a git checkout and so fails on an archive. Without that artefact the base gives 11 / 112, which agrees with the report. The other 11 failures are the same tests on both sides.
- Versions: Python 3.12.3, torch 2.6.0+cu124, transformers 5.19.0, peft 0.21.2, NumPy 2.5.4. These match the report.
- My own probe (/tmp/pb/review_u4_scratch/rb_probe.py) builds a real `ReasonThenBinWrapper` on a tiny random Llama with an offline-trained BPE tokenizer and runs `rb_group_step` end to end on CPU. It ran. The reference policy was unchanged after the updates.
  - It showed that generation stops at EOS before `</analysis>` (lengths 134 and 24, both texts containing `<eos>`), and such completions are not counted as format violations.
  - It showed that in train mode with LoRA dropout 0.05, two forwards of the same analyses differ by up to 0.010 nat per token after a few updates.
- The repo's own `ReasonThenBinWrapper` tests (`test_trackp_model.py`) are all **skipped** in this environment because the Qwen3.5 tokenizer is not in the HF cache. In-repo, the new model.py forward path is therefore exercised only through the static-method identity test.

## What checks out (no finding)

- **Reward** (`grpo.py:56-66`): r = −RPS + λ_a·1[exec]·clip(u, ±u_max) − 0.5·1[fv]. The signs are right. RPS is bounded to [0, 1]. There is no log score. `u_max_from_train` (`grpo.py:49-53`) is the 99th percentile of |u|, documented as the symmetric reading.
- **Leave-one-out advantage** (`grpo.py:76-80`): r_i − (Σr − r_i)/(G−1). It is checked against known answers and against the identity G/(G−1)·(r − mean).
- **Std sensitivity variant** (`grpo.py:83-91`) is present.
- **Surrogate**: the PPO clip uses ε = 0.2 with min(ρA, clip(ρ)A). It is summed over a completion's sampled tokens and averaged over completions, so there is no per-length normalisation (`grpo.py:151-158`). `logp_old` and the advantage are detached.
- **Epochs and π_old**: there are 2 epochs. π_old is computed once per batch under `no_grad` and kept fixed across both epochs (`grpo.py:198-209`, `264-273`).
- **k3**: d = log π_ref − log π_θ, k3 = e^d − d − 1, with log π_ref detached (`grpo.py:161-166`). This is the correct direction for KL(π_θ‖π_ref) under samples from the policy.
- **β**: only {0, 0.02} is accepted (`grpo.py:171-172`).
- **Monitors**: zero-advantage share, clipped-token share and mean per-token KL are logged every update.
- **`estimator_check`** (`grpo.py:121-146`) matches §6.3: Bernoulli execute, r = u·execute, G = 8, 256 prompts, 64 resamples, cosine ≥ 0.95. The comparison is against ∇(−πu) = −uπ(1−π), which is the quantity GRPO estimates. The maths is correct: E[A_i(a_i − π)] = uπ(1−π) for the leave-one-out baseline.
- **`rb_group_step` gradient structure** (`grpo.py:214-275`):
  - The reward uses the belief that is read out, not sampled.
  - The PG sequence is the analysis tokens plus the action token. One sequence-level advantage is applied to every token.
  - Adding the exact RPS term to the belief is the pathwise half of ∇E[−RPS] and the score-function term is the other half, so nothing is counted twice.
  - Actions are sampled from a detached logit under `no_grad`.
  - `lp_old` and `lp_ref` are computed under `no_grad` and detached again inside the losses, so no gradient reaches the reference policy (my probe confirms this).
  - Completions are ordered prompt-major throughout: analyses, violations, y and u are all repeated per prompt, and the rewards are reshaped to (n, G). The ordering is consistent.
- **model.py**: `_span_logprob` is untouched. The change only adds two keys (`analysis_token_logprob`, `analysis_token_mask`), so existing outputs and the per-span value are unchanged. The per-token rows sum to the per-span value (tested).
- **dagger.py**:
  - It aggregates keyed by state, keeps the first label and round, and never relabels a stored row.
  - `fit` is called on the whole aggregate each round, so there is no warm start (delegated to `fit` and documented).
  - `check_synthetic_seed` refuses 7001–7010, ≥ 9001 and any non-int (bool, numpy int).
  - It adapts `OfflineBanditEnv` as the runbook asks and states plainly that the one-step env adds no new states.
  - The wording follows R1-WORDING-30OCT.
- **rb_warmup.py**:
  - Only `split == "train"` rows are accepted.
  - Analyses longer than 256 tokens (caller's tokenizer) are refused.
  - The leak guard requires the logged messages to equal `rb_demos.build_messages(prompt)`, which is built from state and proposal only. That check is meaningful and a tampered request is tested.
  - Refusals are listed, not dropped.
  - The format-only fallback is present.
- **Constraints**: the diff contains no read of label seeds, exam seeds, secrets, label tables or `results/`, and no network call. The only file read is `read_calls(path)`, with a caller-supplied path.

## Findings

### B1 — BLOCKING — the format-violation detector misses unclosed analyses that end at EOS
`r1/c3/train/grpo.py:239-240` defines a violation as `last_generated_tokens >= 256`. `ReasonThenBinWrapper.generate` (`model.py:746-755`) does not stop at `</analysis>`; it stops at EOS or at 256 new tokens.

- When the model emits EOS before closing the span, `new` keeps the EOS token, its length is below 256, and **no 0.5 penalty is applied** although the analysis was never closed. My probe confirms this: both sampled analyses ended in `<eos>` well under the cap.
- `segments()` (`model.py:655-657`) then appends a `</analysis>\n` that was never sampled and scores it as part of the PPO sequence.

For a 0.8–4B base that has never produced this format, EOS-before-close is the most likely violation, so the §6.4 reward is wrong in its most common failure mode.

Fix:
- Have `generate` record per completion whether the stop sequence was found, for example `last_closed`.
- Set violation = `not closed`. This covers both the cap and EOS. Strip EOS from the analysis text.
- For unclosed completions, mask out the appended closing-tag tokens and the trailing newline in `analysis_token_mask`.
- Add a test where a fake policy returns an EOS-terminated, unclosed analysis and assert that exactly that completion's reward is 0.5 lower.

### B2 — BLOCKING — the report calls the 8 TrackPStop guard failures environmental; they are code failures
`docs/r1/reports/TRACKP_RL_INVENTORY_20261114.md:61-63` says all 11 shared failures come "from the environment", including "8 TrackPStop guard tests that need the pinned harness".

I ran with AR_HARNESS_ROOT set to the pinned harness and the 8 tests still fail with `DID NOT RAISE TrackPStop`. The cause is in the code: `EVAL_COLUMNS` (`r1/c3/train/run.py:37`) does not match `delta_true`, `delta_audit_all`, `se_audit`, `candidate_metrics`, `incumbent_metrics` or the `_evidence_seed_split` marker, so `guard_rows` lets them through.

This is pre-existing on a15300ca and not caused by this branch. Still, it is the Track P evaluation-field leak guard, and calling it an environment issue would let it go unnoticed through the unit 7 integration.

Fix: reword the report.
- 3 failures are environmental: `lightgbm` absent, `kev` absent, and gzip byte-identity.
- 8 are a pre-existing mismatch between `run.guard_rows`/`EVAL_COLUMNS` and its tests, identical on the base and not touched here.
- Add this to the question/attention list for the author. Do not change `run.py` in this unit unless authorised.

### B3 — BLOCKING — the inventory misstates R-A and omits gaps that the runbook's step 4 depends on
Runbook unit 4 step 4 says R-A is to be implemented "only if the inventory shows it missing or partial". The inventory (§1) reports R-A as present, but:

- `TRACKP_RL_INVENTORY_20261114.md:12` labels `smoothed_rule_loss` as "R-A2". It is the R-A3 ablation (`losses.py:72` docstring; spec §6.3).
- `:14` calls `metrics.disagreement_rate` an "Action/expert disagreement metric". It measures action versus rule disagreement (`metrics.py:145`; spec §6.3 key metrics).
- No row checks the R-A arms themselves. Nothing implements R-A1's action head on a **stop-gradient** hidden state; the bin-token family's action is read from the LM head with no detach. There is no R-A2 shared-training path with the R1-RA2-MONITOR rollback, and no stop/rollback rule (§6.4 "Stop rule (R-A2, R-A3, R-B)") anywhere in `r1/c3/train/`. Only the losses and the action head exist, so R-A is **partial**.
- §4 "Not done" omits several things:
  - the R-B stop/rollback rule;
  - R-B on Kev (PointerWrapper), which §6.4 makes eligible but `rb_group_step` supports only for the bin-token wrapper interface;
  - the R-B with/without-analysis ablation and the action/rule disagreement report for R-B;
  - the fact that the real `ReasonThenBinWrapper` path, including the new model.py forward keys, is never exercised by the repo tests here, because the Qwen tokenizer is absent and all 6 related tests skip.

Fix:
- Correct rows 12 and 14.
- Mark R-A as partial and list the missing R-A1 detach path and the stop rule.
- Then either implement exactly what §6.3 specifies for R-A1 (a detached LayerNorm + Linear head on `return_state` states, trained with `losses.action_loss`), or record an explicit deferral with its reason in the question list.
- Add the omitted items to §4.

### N1 — NON-BLOCKING — the wrong-sign "detection" test is a tautology
`r1/tests/test_trackp_grpo.py:66-68` calls `estimator_check` again with the same inputs and asserts `-cosine <= -0.95`. That only restates the previous assertion; no wrong-sign estimator is ever fed in.

Fix: add a parameter or test hook that flips the advantage sign (or uses `-A`), and assert that cosine ≤ −0.95 and `passes` is False. Alternatively, delete the claim.

### N2 — NON-BLOCKING — LoRA dropout is active during R-B sampling and ratio computation
`grpo.py:256-267` computes `lp_old`, `lp_ref`, the rewards and `lp_new` in whatever mode the policy is in. With `LORA_DROPOUT = 0.05` (`model.py:65`) in train mode:
- ρ ≠ 1 at epoch 0. My probe measured up to 0.010 nat per token after 3 updates, and this grows with training.
- The clip-share monitor is inflated.
- The reward's belief is noisy.

The GPT-2 end-to-end test sets every dropout to 0, so it cannot show this.

Fix: run sampling, `lp_old`, `lp_ref` and the reward in `eval()` and the updates with dropout disabled (or set `lora_dropout = 0` for R-B), and document the choice. This is standard for PPO/GRPO on LMs.

### N3 — NON-BLOCKING — the PPO sequence contains tokens that were not sampled
- The `"\n"` after `</analysis>` (`model.py:656`) is never sampled.
- The decode-and-re-encode round trip (`model.py:755` then `model.py:656`) can produce token ids that differ from the sampled ids.

Fix: return the sampled ids from `generate` and score those, or at least mask the forced newline. B1 covers the forced closing tag.

### N4 — NON-BLOCKING — `run_dagger` calls the expert twice per new state, and on states already labelled
`dagger.py:79-80` calls `expert(s)` for the disagreement metric on every visited state, then calls it again in `data.add` for the new ones. With the C.2 expert (a 10-seed audit) this repeats audits and audits states that are already stored, which contradicts "nothing is relabelled" in spirit even though stored labels do not change.

Fix: label each new state once, reuse stored labels for known keys, and compute the disagreement from those labels. Add a call-count test.

### N5 — NON-BLOCKING — the `rb_group_step` test is weak on alignment and on the policy-gradient path
`test_trackp_grpo_torch.py:131-153` asserts only that `format_violations > 0`, that the belief RPS falls (which the exact RPS term alone produces) and that the action moves towards execute. It does not check:
- that a given completion's violation lowers that completion's reward by exactly 0.5;
- the advantage per group;
- that the analysis parameters (`FakeReasoner.word`) receive a PG update in the right direction;
- that `ref` is unchanged.

Fix: add a deterministic known-answer case with fixed analyses, actions and rewards that checks rewards, advantages and the sign of the update on `word`, plus a check that `ref` is unchanged.

### N6 — NON-BLOCKING — the std variant's convention
`std_advantages` (`grpo.py:83-91`) uses the population std (ddof = 0) and sets A = 0 on constant groups. The original GRPO code usually divides by the sample std plus a small ε. Either is a reading of "std_G r", and the docstring states the choice. Record it in the report so the sensitivity row is reproducible.

### N7 — NON-BLOCKING — `estimator_check` does not go through the torch training path
The §6.3 check (`grpo.py:121-146`) is numpy on synthetic logits. `test_estimator_check_through_autograd` covers `clipped_surrogate` at ρ = 1, but nothing runs the check through `grpo_loss`/`ppo_update` on an actual R-A1 head and its parameters, which is what "validates the RL machinery before R-B" suggests. Consider a CPU version on a tiny head (gradient with respect to head parameters, cosine ≥ 0.95).

### N8 — NON-BLOCKING — `rb_warmup` accepts teacher outputs cut off at max_tokens
`rb_warmup.py:50-65` does not check `response.choices[0].finish_reason`. A demonstration cut at the teacher's 256-token cap (`rb_demos.py:63`) is accepted mid-sentence. Fix: refuse or flag records with `finish_reason == "length"`.

### N9 — NON-BLOCKING — minor items
- The `params` argument of `ppo_update` (`grpo.py:188`) is unused.
- The exact RPS term has a fixed weight of 1 and is applied in both epochs without clipping. That is fine, but state it in the run config or report next to the existing note in §4 of the report.
- `generate` calls `torch.manual_seed` on the global RNG (`model.py:740`; pre-existing).

## Constraint check
- No label seeds 7001–7010, exam seeds, secrets, label tables, `results/` reads or network calls appear in the diff.
- `check_synthetic_seed` protects the synthetic paths.
- I did not read `~/.config/r1/secrets.env` or any key file.
- Scratch files are only in /tmp/pb/review_u4_base, /tmp/pb/review_u4_scratch and /tmp/pb/review_u4_base.txt.

Verdict: changes requested

---

Reviewed commit: 0af337a603700b84812c1e62f82a71b4748a85b2

# Independent review: unit 4 (Track P RL), round 2

Branch `mac-trackp-rl-20261114` (worktree /tmp/pb/wt/tprl). HEAD 0af337a6 sits on ce368690, with base a15300ca. I checked each round-1 fix and looked for new problems. Read-only: no stash and no edits.

## What I ran

- **New tests.** The new and changed test files gave **37 passed**: grpo 8, grpo_torch 8, dagger 6, rb_warmup 9, ra 6. These counts match the report.
- **Regression.** `shim_pytest.py -k trackp r1/tests` with AR_HARNESS_ROOT=harness-pin gave **11 failed / 149 passed / 83 skipped**. The 11 failures are the same tests as on the base.
  - My base run from `git archive` showed a 12th failure, `test_manifest_records_commits_and_hashes`. That test needs a git checkout, so it is an artefact of the archive.
- **Real-wrapper probe.** I ran `ReasonThenBinWrapper` on a tiny random Llama with an offline BPE tokenizer, on CPU (scratch dir /tmp/pb/review_u4_scratch, now removed).
  - **Closure record.** Generations that stopped at EOS (134 and 24 tokens) and one that hit the cap (256 tokens) all give `last_generated_closed = False`. All 6 completions per step are counted as violations.
  - **Closed span.** I patched `lm.generate` to return text + `</analysis>` + junk. The result is `closed = True`, length 8, junk discarded. The scored ids are exactly the sampled ids: 8 text tokens plus the 4 tag tokens, with the trailing newline excluded.
  - **Span fields.** `analysis_text_tokens` and `analysis_close_tokens` agree with `segments`. The tag is a 4-token prefix of `</analysis>\n`.
  - **Eval mode.** The policy's train mode is restored after the step. Two eval-mode forwards are identical (max |Δlogp| = 0). Clip share at epoch 0 is 0.
  - **Reference unchanged.** No gradient reaches the reference policy.
- **Constraint scan of the round-2 diff.** No secrets, network, label/exam seeds, label tables or `results/` reads.

## Round-1 findings: status

- **B1 — fixed.**
  - `generate` records `last_generated_closed` (`model.py:758-765`), and `rb_group_step` sets violation = not closed (`grpo.py:271-272`).
  - `sampled_analysis_mask` (`grpo.py:214-229`) scores the text tokens. It scores the tag only when the policy sampled it, and never the newline.
  - The mask's consistency check raises if the counts exceed the scored span.
  - Tests cover the mask, an EOS-unclosed completion (penalised, forced tag unscored) and the missing-record refusal. My probe confirms the behaviour on the real wrapper.
- **B2 — fixed.** Report §3 now attributes the 8 TrackPStop failures to the pre-existing `EVAL_COLUMNS` gap at `run.py:37`, unchanged and flagged for the author. The 3 environment failures are listed correctly.
- **B3 — mostly fixed.**
  - The inventory rows are corrected: R-A3 smoothed rule, action-vs-rule disagreement, R-A1 and the stop rule marked missing, Kev R-B missing, R-A marked partial.
  - Kev R-B, the analysis ablation and the torch-path estimator check are explicitly deferred.
  - The skipped real-wrapper tests are disclosed.
  - `ra.py` adds the R-A1 head and `stop_rule`. The head has a new problem, R2-B1 below.
- **N1 — fixed.** The tautology is replaced by a non-trivial check: G = 2 with 1 resample fails the threshold.
- **N2 — fixed for the policy.** It is still open for the reference policy; see R2-N1.
- **N3 — partly fixed.** The forced tag and newline are now excluded. The decode/re-encode approximation is disclosed in the docstring and the report; see R2-N3 for its size.
- **N4 — fixed.** Each new state is labelled once and stored labels are reused for the disagreement (`dagger.py:79-83`). A call-count test was added.
- **N5 — improved.** There are now tests for mask alignment, the EOS violation and eval mode.
- **N6 — recorded in the report.**
- **N7 — deferred and disclosed.**
- **N8 — listed as open.**

## New findings

### R2-B1 — BLOCKING — the R-A1 head has no LayerNorm, against R1-HEADS-LN
`r1/c3/train/ra.py:28-35`: `DetachedActionHead` is `nn.Linear(hidden, 1)` on `state.detach()`. The spec says otherwise:
- Spec §2.2, l. 92: "Every new head (action, cumulative, the E0 linear belief head) reads a LayerNorm-ed state (26 Oct, R1-HEADS-LN)".
- PLAN l. 559: "A LayerNorm before every new head (action, …): accepted".
- The wrapper table also specifies "LayerNorm + Linear (hidden → 1)" for action readouts, and `_Wrapper._add_heads` (`model.py:152-161`) follows it.

The repo's own P.0 finding gives the reason: raw readout states differ in scale by orders of magnitude across families, and a fresh Linear head can give logits around −300.

Fix:
- Change the head to `nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, 1))` applied to `state.detach().float()`.
- Update the docstring and report §2 ("Linear on `state.detach()`").
- Add an assertion in `test_trackp_ra.py` that the head normalises its input, for example that its output is invariant to rescaling the state.

### R2-N1 — NON-BLOCKING — the reference policy is not put in eval mode
`grpo.py:254-258` and `289-291` put only the policy in eval mode. If the caller passes `ref_policy` in train mode with a non-zero LoRA (the SFT warm-up checkpoint), dropout makes `lp_ref` noisy. My probe measured up to 0.018 nat per token between two train-mode forwards of a trained reference.

Fix: call `ref_policy.eval()` (and restore its mode afterwards) in the same place, or assert `not ref_policy.training`.

### R2-N2 — NON-BLOCKING — mode restore is not exception-safe
`grpo.py:307-308` restores train mode only on the success path. Wrap the step in `try/finally`.

### R2-N3 — NON-BLOCKING — the decode/re-encode mismatch can be large
In the probe, an EOS-terminated sample of 134 sampled ids re-encoded to 218 text tokens. A random model emits odd byte sequences, so this exaggerates the effect, but it shows the disclosed approximation is not always small. The PPO ratio then refers to a different token sequence than the one sampled.

Before any real R-B run, carry the sampled ids from `generate` into `forward` and score those. This can stay in the "for the author" list.

### R2-N4 — NON-BLOCKING — the closing tag gets no credit when the tokenizer merges it with the newline
`model.py:657-661` sets `analysis_close_tokens = 0` when `</analysis>` is not a token prefix of `</analysis>\n`. A sampled closing tag then gets no PPO credit, although the completion is still not penalised. The current tokenizers avoid this (the probe tokenizer splits the newline off), and the conservative direction is safe. Encode the tag and the newline separately to remove the dependency.

### R2-N5 — NON-BLOCKING — which state R-A1 reads
`ra1_loss` reads `out["state"]`. For `BinTokenWrapper` that is the **belief-position** state `hb` (`model.py:711`), not the action-position state. For Kev the `<decide>` state is both. State the choice in the `ra.py` docstring, or return the action-position state for this use.

### Report
- The test and regression counts, the version line and the failure attributions are accurate.
- "R-A was therefore partial" is accurate.
- The note that "the reviewer exercised the real wrapper on a tiny Llama" is now true for the round-2 code (this review).
- After the R2-B1 fix, update the `ra.py` description in §2.

## Constraint check
- The round-2 diff has no reads of secrets, label or exam seeds, label tables or `results/`, and no network calls.
- I did not read `~/.config/r1/secrets.env` or any key file.
- I removed my scratch directories (/tmp/pb/review_u4_base, /tmp/pb/review_u4_scratch) and the result lists /tmp/pb/review_u4_base.txt and /tmp/pb/review_u4_head2.txt.

Verdict: changes requested

---

Reviewed commit: 2f36614a0f02254774ffcc816a66c5db61d18a8c

# Independent review: unit 4 (Track P RL), round 3

Branch `mac-trackp-rl-20261114` (worktree /tmp/pb/wt/tprl). HEAD 2f36614a sits on 0af337a6 → ce368690, with base a15300ca. I reviewed read-only. The worktree was clean before and after.

## What I ran

- **New tests.** The 5 new and changed test files gave **37 passed**.
- **Regression.** `shim_pytest.py -k trackp r1/tests` with AR_HARNESS_ROOT=harness-pin gave **11 failed / 149 passed / 83 skipped**.
  - These are the same 11 failures as in rounds 1–2 and on the base: 3 environmental, and 8 from the pre-existing `EVAL_COLUMNS` guard gap that the report now discloses.
  - There are no new failures and no change in the pass count against round 2.
- **Scratch check** (in /tmp/pb/review_u4_scratch, since removed), using the test module's `FakeReasoner`:
  - Both the policy and the reference ran in eval mode during the step, and both train modes were restored afterwards.
  - When the policy's `forward` raised an exception, the policy's train mode was restored and the reference's eval mode was kept.

## Round-2 findings: status

- **R2-B1 (BLOCKING) — fixed.**
  - `ra.py:30-39`: `DetachedActionHead` is now `LayerNorm(hidden) → Linear(hidden, 1)` on `state.detach().float()`, as R1-HEADS-LN and spec §2.2 require.
  - `test_trackp_ra.py:25-28` asserts that the LayerNorm is present and that the output is unchanged when the input is scaled by 7.5. This test is not vacuous: without the LayerNorm the output would change.
  - The stop-gradient assertion (`trunk.weight.grad is None`) still holds.
  - The docstring and report §2 are updated.
- **R2-N1 — fixed.** `grpo.py:254-256` puts the reference policy in eval mode too, so π_ref is deterministic.
- **R2-N2 — fixed.**
  - `rb_group_step` (`grpo.py:253-263`) records each model's mode, sets eval, calls `_rb_group_step`, and restores the modes in `finally`. My scratch check confirms the restore also happens on an exception.
  - The body of `_rb_group_step` is the round-2 body with only the old mode handling removed. Arguments are passed through by keyword, so nothing was dropped.
- **R2-N3 — disclosed.** The 134→218 re-encode observation and the instruction to carry the sampled ids into `forward` before any real R-B run are in the docstring (`grpo.py:248-250`) and in report §2.
- **R2-N5 — fixed.** The `ra.py` docstring states that the head reads the belief-position state.
- **R2-N4 — remains NON-BLOCKING.** The closing tag gets no PPO credit when a tokenizer merges `</analysis>` with the newline. This errs in the safe direction and does not affect the current tokenizers.

## New findings

None. No regressions.

Open items for the author, all disclosed in report §4 and not blocking this engineering-only unit:
- the `EVAL_COLUMNS` guard gap;
- the decode/re-encode approximation, to be removed before any real R-B run;
- truncated teacher demonstrations;
- Kev as an R-B base, the analysis ablation, and the torch-path estimator check.

## Constraint check

- The round-3 diff has no secrets, network calls, label or exam seeds, label tables or `results/` reads.
- I did not read `~/.config/r1/secrets.env` or any key file.
- I removed all my scratch under `/tmp/pb/review_u4_*`.

Verdict: accepted
Accepted commit: 2f36614a0f02254774ffcc816a66c5db61d18a8c
