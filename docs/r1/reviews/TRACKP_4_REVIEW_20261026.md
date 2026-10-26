# Track P Phase 4 (P.1/P.2 toy batch on every family) — independent review

- **Reviewer:** independent Claude Code subagent on zhixu portal (AI-assisted). It did not see the work while it was in progress.
- **Date:** 26 Oct 2026 (UTC).
- **Scope:** runbook `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` §0, Phase 3 and Phase 4; spec `docs/r1/TRACK_P_POST_TRAINING.md` §2 and §4. Branch `trackp-20261026`, range `da42298..02dd725`, plus the Phase-4-prep commit `1e3fe3e`. Deliverable: `docs/r1/reports/TRACKP_P4_TOY_BATCH_20261026.md` and `docs/r1/reports/trackp_p4_20261026/`. Run outputs: `~/r1_trackp/runs/p4/`. Context: the accepted `docs/r1/reports/TRACKP_P0_SPIKES_20261026.md`.
- **Evidence label:** ENGINEERING_ONLY.
- **Tree:** the clone was clean at `02dd725`, which equals `origin/trackp-20261026`.

## What I re-ran, and the results

| # | Check | Result |
|---|---|---|
| R1 | CPU tests at `02dd725` (`trackp-cpu` venv, `CUDA_VISIBLE_DEVICES=""`, `r1/tests/test_trackp_*.py`) | **159 passed**, 0 failed (10:13). This includes `test_laya_native_readout_equals_layas_own_forward`, the parity test of Laya's native 12-option readout against `laya.common.DecisionModel.forward`. |
| R2 | **One GPU job:** `trackp.py toy --base laya` into my scratch dir. Before starting I checked that `origin/main` STATUS shows no running Track X B1/B2 phase and that `nvidia-smi` listed no compute process. The CLI took the lease itself: lease log 06:50:05–06:51:07Z, pid 324747. | rc 0, manifest `02dd725` clean. The before-training losses are **bit-identical** to the committed Laya run (total 3.43973, belief 2.55075, action 0.88898), so initialisation is reproducible. After training: total 3.0926, belief 2.3988, action **0.6939**. The committed run had 3.1029 / 2.4056 / 0.6973. All three decrease again, and reload is identical. The small differences after training fit the report's note that the CUDA backward is not deterministic. |
| R3 | sha256 of the saved files (`adapter/*`, `heads.safetensors`) against the manifest `model_files_sha256`, for kev-0.8b, laya, qwen3.5-4b-base, startlux-2b and laya.attempt1 | All 20 files match. |
| R4 | Committed `report.json` / `manifest.json` against `~/r1_trackp/runs/p4/<base>/`, all 9 runs | All byte-identical. Every `toy/metrics.jsonl` has exactly 50 steps. |
| R5 | Table recomputed from `report.json` `batch_loss_before/after` | All 8 rows match to the printed precision. For every family, `loss_decreased`, `belief_loss_decreased`, `action_loss_decreased` and `reload_identical` are all true. Laya attempt 1 shows action 0.7429 → 0.7483 (false), as the report says. |
| R6 | Manifests | All 9 runs have `data_manifest_sha256` `8a8b5614…` and `config_sha256` `39931e2a…`, so every family trained on the same 64-example batch with the same config. Paper tree clean everywhere: 7 runs plus Laya attempt 1 at `da42298`, the final Laya run at `914ee12`. `914ee12` was committed at 06:43:08Z and the run started at 06:43:11Z. Harness `264011e` clean. Every base and adapter revision equals `r1/c3/train/registry.yaml`. |
| R7 | GPU lease | Every run has a start/end pair in `~/r1_trackp/runs/gpu_lease_log.jsonl` with a matching pid: 9 toy runs between 06:26:21 and 06:43:58Z, no overlaps and no foreign job. `driver_logs.txt` shows rc 0 for all of them. |
| R8 | `git show 914ee12` | One file changed (`r1/c3/train/model.py`). The changes are in the module docstring and in `LayaWrapper.forward` / `_core_forward` only. The native logits path (type embedding → head layers → scorer at the markers) is unchanged. So the other 7 runs at `da42298` stay valid. |
| R9 | CPU reproduction of the cause given for the Laya fix: untrained Laya, 16 toy prompts. I applied LayerNorm, then took the mean between-prompt deviation divided by the norm. | [CLS] state after the head layers: norm **1.13e4**, relative variation **0.97 %**. Mean-pooled encoder output: norm 25.2, variation **8.2 %**. The report gives ~1.1e4, ~1.2 % and ~8.7 %. My measure may differ slightly from the agent's, but the numbers agree. |
| R10 | CPU check of the saved Laya model (`runs/p4/laya/saved`, loaded into a freshly built wrapper) on all 64 examples | Action loss 0.697311 and belief loss 2.405589, matching the GPU numbers to about 1e-7. Action logits: mean 0.93, sd 0.24. Weighted AUC against 1[u > 0] is **0.785**, and corr(logit, u) is 0.44. So the action head separates examples. It does more than learn the base rate. |
| R11 | Constant-predictor baselines on the 64-example batch (CPU) | Best constant **action** loss is **0.7367** (π\* = 0.640; 43/64 positive). Best constant **belief** loss (the batch-mean soft label; RPS and CE are both proper) is **2.2432**. |
| R12 | `1e3fe3e` | `batch_losses` computes the `sft_loss` terms in eval mode, in chunks of 8, over all 64 rows. `cmd_toy` calls it before and after `Trainer.train()` on the same model and reports total, belief and action separately. The CLI test asserts the new keys. |

## Is the criterion from `1e3fe3e` a faithful reading of "loss decreases"?

Yes, and it is stronger than the alternatives. The runbook says only "loss decreases". The old check compared the training loss of the first and last minibatch. Those batches differ (Laya: 3.04 vs 2.79, but its per-step curve is flat with noise of ±0.4), so that check could pass or fail by chance. The new check evaluates the whole fixed batch before and after training, deterministically, with dropout off. It also requires each output to decrease separately, which the runbook does not ask for. The thresholds are unchanged and nothing was relaxed. Attempt 1 failed under this stricter check and was reported as a failure.

One limit remains. The criterion can be met by a head that learns only the base rate (finding 1).

## Findings

1. **Minor.** *Claim:* "All 8 families: the total loss, the belief loss and the action loss decrease". *Observation:* this is true. However, for two families the decrease is mostly a move toward the base rate, and the report gives no baselines.
   - Laya action ends at 0.697 against a best-constant loss of 0.737. Its start of 0.889 was above that constant. Laya belief ends at **2.406, which is worse than predicting the batch-mean label for every example (2.243)**.
   - Qwen3.5-0.8B-Base action ends at 0.710, against the same 0.737.

   My R10 check shows that Laya's action head does separate examples (weighted AUC 0.785), so "the output trains" holds. Still, a reader of the table cannot see how weak these two runs are. *Required fix:* add the two constant baselines (action 0.737, belief 2.243) to the report. State that Laya belief is still above the constant baseline after 50 steps at lr 2e-5, and that the Laya and Qwen-0.8B action losses are only just below theirs. Quote or reproduce the AUC check.

2. **Minor.** *Claim:* the Qwen control 0.8B action "barely moves … it reads `<exec>`/`<skip>` token logits, i.e. trains through its new token rows and LoRA, not a fresh head". *Observation:* Qwen3.5-4B-Base uses the same `BinTokenWrapper` readout and reaches action loss 0.003. So the readout type does not explain the 0.8B result. The 0.8B training is unstable: grad norm 50–170 for most of the run, and loss spikes to 6.4 at step 8 and to 5.6 at step 28. *Required fix:* reword the sentence. Say the cause is not established. Note the instability, which looks like an lr or token-row step-size issue, as an item to settle before P.4 chooses its lr for the control.

3. **Minor.** *Claim:* deviation 1 (Laya's new heads read the mean-pooled encoder output). *Observation:* the fix is justified by evidence:
   - attempt 1 failed;
   - my R9 check confirms the near-constant [CLS] state;
   - attempt 2 passes, and my R2 rerun repeats the pass;
   - parity of the native readout is kept (R1, R8).

   I found no hidden regression in the 7 other families or in Laya's native path. However, this is a departure from spec §2.2 ("Linear (hidden → 1) on the question/decision state"). It also changes what Laya's `cumulative11` head reads, which matters for the E0 head-fit design in P.3a. The report lists it as a deviation but not among the items for the author, and the runbook says a disagreement with the spec is reported. The measurement behind "~1.2 % / ~8.7 %" is not committed either. *Required fix:* add the deviation to "Next" as an author question (or a spec note), and say that it also covers Laya's cumulative head. Record how the variation was measured: a short snippet or the method, so the cause can be reproduced from the repo.

4. **Minor.** *Observation:* no test covers the new Laya pooled state. The parity test covers the native logits only. A regression such as pad tokens leaking into the mean, or the heads reading the post-head state again, would pass CI. *Required fix:* add a CPU test with the tiny Laya config:
   - the state the new heads read equals the masked mean of the encoder's last hidden state;
   - it does not change when padding is added to the batch, i.e. a prompt gives the same action logit alone and next to a longer one.

5. **Informational (no fix required for Phase 4).** The step lr in `trainer.py` metrics is written after `sched.step()`, so it is the *next* step's lr. Step 1 is logged as 2e-5 / 1e-4, but it ran at half that because of the 2-step warm-up (λ(0) = 0.5). The report's "2 warm-up steps" is correct. Only the logged column is shifted by one step. This is worth fixing before evidence runs, where the lr column may be quoted.

6. **Informational.** These are cosmetic and need no fix:
   - `laya.attempt1/report.json` still gives the checkpoint as `runs/p4/laya/toy/ckpt/...`, because the directory was renamed after the run;
   - `~/r1_trackp/runs/p4/run_all.sh` calls itself "Track P Phase 3".

## Ground rules

- **Commits:** `1e3fe3e`, `914ee12` and `02dd725` are authored by `Dowling Wong <wangdowling@gmail.com>` and end with the Claude co-author line.
- **Pushes:** only `trackp-20261026` is pushed, at `02dd725`. The other remote branches belong to other tracks.
- **Secrets:** the diff and the run outputs contain no secrets and no references to the secrets file. I did not read the secrets file.
- **Track X priority:** every GPU job ran under the lease, and none overlapped another job.
- **Attempts table:** complete. The lease log has exactly 9 toy runs (7 + Laya × 2), and the table accounts for all of them.
- **Honesty:** attempt 1 is reported as a failure, with its evidence committed.
- **Not covered by this review:** "Done when" for Phase 4 has no further items.

## Verdict

**Verdict: pending fixes.** No blocking finding. Every runbook item holds for all 8 families:
- the same 64-example batch;
- 50 steps;
- both outputs;
- the shared `Trainer` via `trackp.py toy`;
- total, belief and action loss decrease on the whole batch in eval mode;
- belief and action are bit-identical after reload into a freshly built wrapper.

The Laya fix is justified and confined to `LayaWrapper`. Acceptance needs findings 1–4 fixed or answered here. Findings 1–3 are report and documentation changes. Finding 4 is one small test.


## Implementation agent's response (26 Oct)

1. Fixed: the report gives the constant baselines (belief 2.243, action 0.737; `p4_baselines_output.json` + script) and states that Laya's belief ends above the base rate and Laya's / Qwen-0.8B's action just below the best constant, with Laya's action AUC 0.785 and correlation 0.44.
2. Fixed: reworded as instability (grad norms 50–170, minibatch spikes to 6.3; the 4B control with the same readout reaches 0.003); lr question for the control's token rows / fresh LoRA put to the author before P.4.
3. Fixed: deviation 1 now covers the cumulative head too and is an author question (Q1); the variation measurement is committed (`laya_readout_states.py` and its output).
4. Fixed: `test_laya_new_heads_read_the_padding_invariant_masked_mean_of_the_encoder` (action and belief unchanged when batched with a longer prompt; action equals the head on the masked mean of the encoder output).
Informational items: the trainer now logs the lr the step ran at; `run_all.sh` label fixed; the attempt-1 checkpoint path noted in the report.
