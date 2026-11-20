# Track P P.4 (A5 SFT, belief only): authorization draft (approved: false)

**Status: DRAFT for the author's signature. `approved: false`. Authorizes nothing.**
- On signature, the coordinating chat publishes the final version to `main` as
  `docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md`, with every prerequisite in §7 recorded as PASS. The CLI command
  `trackp.py sft` stays "not yet" until then (`NOT_YET["sft"]` names this file).
- Written by the Mac-desk agent (Claude), AI-assisted. Execution is the Track P agent's (R1-TRACKP-RUNBOOK-SCOPE: the
  Mac runs no Track P training); this draft and the test evaluator are desk work.
- Values marked *(proposed)* are recommendations. Four author decisions are open (§2).

## 1. Authority (published `main`; `df58bcd5`, PLAN unchanged since `94db94bb`)

| Row | What it fixes here |
|---|---|
| RUNBOOK P.4 | A5 SFT (belief only) on the finalists + control: soft-label RPS + CE on the B.2 labels; LoRA r = 16; adapter lr from {1e-5, 3e-5, 1e-4} by val RPS for every family; early stop on dev RPS; best checkpoint; temperature recalibration on dev; report RPS skill, NLL, all-bins and top-1 ECE, PIT, width ratio, then offline one-step value through `rules.decide`; learning curve 250/500/1k/2k. **RL gate** for P.5/P.6: RPS skill > 0 significantly, > 99 % mass on bin outputs over 3 seeds, all-bins ECE ≤ 0.05, width ratio in [0.8, 1.25]. |
| R1-C3-POOL, R1-C3-POOL-EXAM | The A5 candidates are Kev-0.8B and Kev-4B. "Both Kev sizes go on to P.3b and A5 unless one fails E0 or an E4 hard limit; the Qwen control is carried as before." |
| R1-C3-CONTROL, R1-CONTROL-READOUT | Qwen3.5-0.8B-Base and -4B-Base + LoRA, always carried as an ablation arm, not a candidate; the primary belief readout is a fresh LayerNorm + linear head. |
| R1-SOFT-SIGMA, R1-LR-GRID, R1-TEMPERATURE | Soft label s = σ̂_node/√K_label (pooled σ̂); one lr grid; post-hoc temperature scaling on dev for all models. |
| R1-TRACKP-SFT-DEV | Build and trial-run the SFT pipeline on the sweep-1 table now (ENGINEERING); plug in the sweep-1 B.2 label block when it exists; readiness only — not used for any evidence, selection or tuning; the 7006–7010 evaluation block is not read. "Train directly once the sweep-2 labels are in place." |
| R1-TRACKP-SFT-DUP | Held-out without training duplicates is the primary result; the full held-out is secondary (sweep 1: train 1,176 / val 47 / test 74 of 262 labelled test proposals; sweep 2 the same rule). |
| R1-MAIN-PROPOSER (e) | The A5/A6 evidence checkpoints use sweep 2; sweep 1 is added as a stratum; pooled versus sweep-2-only training is chosen on validation before any test read *(proposed in that row)*. Until sweep 2 exists, Track P may run its pipeline on sweep-1 labels as ENGINEERING_ONLY, label seeds 7001–7005 only, never 7006–7010. |
| R1-BX-D8, R1-BX-D8-CONFIRM | Sweep-2 label tables may be analysed (CONFIRM is committed); "existing preregistration and analysis gates remain in force". |
| R1-TASL7-TRACKP, R1-TRACKP-TASL2-HOST | Track P evidence tables on TASL-7 or TASL-2 (both RTX 4090; TASL-2's frozen `trackp-gpu` env verified byte-identical); one host per table, named in the report. |
| R1-QTORCH-AMEND, R1-TRACKP-I3-H200 | Image v2 approved for Track P on HTCondor, after I2/I3 on v2 and a Track P smoke and E0 equivalence check per GPU model (H200 first). |
| R1-W2-3-STOP | Every Track P source ledger uses exactly W = 20 worker runs (sweep data rebuild). |

**What exists now.**
- The SFT pipeline (`r1/c3/train/sft_data.py`, `sft.py`, `trackp.py sft-data|sft-dev|sft-select`) with the
  decided policy `heldout_excludes_seen`, on `main`.
- The ENGINEERING trial on TASL-2 (`ops-tasl-20261116` @ `f557f985`, synthetic labels): kev-0.8b, lr 3e-5, seed 0;
  the default micro-batch 8 OOMed on the 24 GB card; micro-batch 4 (effective batch 16 unchanged) ran in 159 s
  (370 steps, peak 16.5 GB).
- The sweep-1 label block (`label_block.jsonl`, sha256 `cdae9c3f…9aca`), with its freeze record drafted and accepted
  for signature (READY 62).
- **New in this unit:** the P.4 test evaluator `r1/c3/train/sft_test_eval.py` (§5).

## 2. Author decisions

### P4-DATA: which labels, with which status (recommendation: A)

- **A (recommended): two phases.**
  - **Phase 1, sweep 1, ENGINEERING_ONLY, now** (after the sweep-1 freeze is signed): the full P.4 protocol on the
    four bases with the real sweep-1 label block, as readiness under R1-TRACKP-SFT-DEV and R1-MAIN-PROPOSER (e).
    Outputs are not used for evidence, selection or tuning; the test evaluator runs, and its numbers are
    ENGINEERING_ONLY.
  - **Phase 2, sweep 2 (+ sweep 1 as a stratum), EVIDENCE**: when the sweep-2 B.2 labels exist, are frozen and are
    released to Track P by an author row (the sweep-2 analysis preregistration fixes when). Pooled versus
    sweep-2-only training is chosen on validation before any test read.
- **B: phase 2 only.** Wait for the sweep-2 labels; no real-label readiness run. Saves a few GPU-hours, but the first
  run on real labels is then an evidence run.

### P4-ARMS: which bases (recommendation: A)

- **A (recommended): as R1-C3-POOL-EXAM:** `kev-0.8b`, `kev-4b`, and the controls `qwen3.5-0.8b-base`,
  `qwen3.5-4b-base`, minus any base whose P.3a record shows an E0 failure or an E4 hard limit (cited per base in P2).
  P.3b (the labelled exam) runs alongside as the appendix table; it no longer selects (R1-C3-POOL-EXAM), so it is not a
  gate for P.4.
- **B: Kev only** (no control arms in phase 1). Halves phase 1, but A5(Kev) − A5(control), the measure of Kev's
  decision pre-training, is then unavailable until phase 2.

### P4-HOST: where (recommendation: A, with B as the whole-table fallback)

One host per table (R1-TRACKP-TASL2-HOST); a table is one phase.

- **A (recommended): TASL-2 or TASL-7 (RTX 4090, the frozen `trackp-gpu` environment).** Host equivalence passed;
  the trial ran there. Risk: the 4B bases at 1,024 tokens on 24 GB without gradient checkpointing. The first step is
  a one-run memory probe per 4B base at micro-batch 1–4 (effective batch 16); if a 4B base cannot fit at micro-batch 1,
  that is a STOP, and the author moves **the whole table** to B.
- **B: NEMO2 H200 with image v2.** 141 GB removes the memory risk and is the T1 tables' model. It needs, before any P.4
  run: I2/I3 on v2, the Track P smoke and the E0 equivalence check on H200 (R1-QTORCH-AMEND), an HTCondor Track P job
  with a reviewed switch, and the queue. Not ready now.
- **C: split by base size (0.8B on 4090, 4B on H200).** Two hosts in one table; not allowed by R1-TRACKP-TASL2-HOST.

### P4-CAP: GPU budget per phase *(proposed: 40 GPU-h for phase 1, 80 GPU-h for phase 2)*

**Phase 1 runs (sweep 1, 1,176 train / 47 primary val):** per base, the lr grid 3 × 3 seeds (9 runs) and the learning
curve 250/500/1k/2k examples × 3 seeds at the selected lr (12 runs): 21 runs per base, 84 in all.
- 0.8B bases: 159 s per run measured (kev-0.8b) → about 42 × 3 min ≈ 2.1 h with evaluation overhead.
- 4B bases: unmeasured; *(assumed)* 5 × the 0.8B time (parameter ratio) and micro-batch 1–2 → about 42 × 15 min ≈ 10.5 h.
- Test evaluation: predictions on the test proposals only, minutes per arm.
- Total about 13 GPU-h; the cap of 40 leaves room for the 4B uncertainty and the memory probes.

**Phase 2** scales with the sweep-2 training set (sweep 2 has the same instance design and both memory modes; pooled
training adds sweep 1), *(assumed)* 2–3 × → about 26–39 GPU-h; cap 80. Both caps bound the projection and the GPU-hours
consumed (the lease log), and a run that would exceed the cap is not started.

## 3. Protocol (unchanged from RUNBOOK P.4 and the SFT pipeline)

- Data: `trackp.py sft-data` on the pinned `c3_features/v3` table with `trackp_prompt/v2`, the label block bound to
  its sweep index and classification, the decided policy `heldout_excludes_seen`, the split over the fixed instance
  universe (8 nodes × 18 instances; 3 test, 3 validation per node).
- Training: `sft-dev` (phase 1) / `sft` (phase 2, enabled by the signed note): loss RPS + CE on the soft label; LoRA
  r = 16; effective batch 16 (the host may set the micro-batch only); ≤ 5 epochs; evaluation every ¼ epoch; early
  stopping on **primary** val RPS (patience 2); best checkpoint; temperature fitted on primary val.
- Selection: `sft-select` picks the lr by mean best primary val RPS over 3 seeds (R1-LR-GRID); under phase 1 its
  output selects nothing (ENGINEERING_ONLY).
- Report per arm: primary and secondary val metrics, the learning curve, the RL-gate quantities.
- **Test:** after the arm is fixed (lr, seed set, checkpoint, temperature), one read per arm with the test evaluator
  (§5): primary (exclusion list applied) and secondary (full) populations.
- Offline one-step value through `rules.decide` uses the evaluation half of the audit (7006–7010) and is therefore
  **not** part of phase 1 (R1-MAIN-PROPOSER (e)); in phase 2 it follows the sweep-2 analysis preregistration.

## 4. STOPs

- The label block's sha256 differs from its freeze record (sweep 1: `cdae9c3f…9aca`), or the freeze is not signed.
- Any read of the evaluation block, `runs.jsonl`, or the 7006–7010 values (the loaders refuse them by name; any other
  route is a STOP).
- A data directory built under a policy other than `heldout_excludes_seen` with real labels (refused at build and
  load).
- A sealed path (`r1_sealed`) or a sweep-2 file without the R1-BX-D8-CONFIRM line; a sweep-2 label read before the
  author row that releases sweep-2 labels to Track P.
- A host other than the one named for the table; a frozen-environment mismatch (R1-ENV-PIN).
- CUDA OOM at micro-batch 1 for a base (P4-HOST); any change of the effective batch, lr grid, epochs, patience or
  loss (the run records a protocol deviation and is not reported as P.4).
- A second test read of the same arm (the evaluator writes once); predictions that do not cover exactly the
  labelled test proposals; an exclusion list that differs from its recomputation (§5).
- The cap (P4-CAP).
- Every STOP keeps its outputs; there is no deletion and no silent retry.

## 5. The P.4 test evaluator (implemented and tested in this unit)

`r1/c3/train/sft_test_eval.py` (branch `mac-trackp-p4-20261120`), tests `r1/tests/test_trackp_sft_test_eval.py`
(21 tests, CPU only; the tiny `hashbag` model for the prediction path).

- **`evaluate_test(data_dir, table_dir, label_source, predictions, out_dir, suite_of=…)`** writes
  `test_report.json` (`trackp_sft_test_report/v1`) once:
  - **primary** metrics (`test_*`): the labelled test proposals not in `splits.json`
    `test_proposals_seen_in_train_or_val` — the headline number of R1-TRACKP-SFT-DUP;
  - **secondary** metrics (`test_full_*`): every labelled test proposal;
  - the Stage S belief metrics (RPS, RPS skill against the training base rate, NLL, all-bins and top-1 ECE, PIT,
    predictive and label sd, width ratio), by node and by suite on the primary population with both counts;
  - the population counts and the sha256 of the primary, secondary and excluded id lists.
- **Bindings, each a STOP:** the data directory's hashes and policy; the table, loaded with the data manifest's table
  hashes as pins (R1-BX-D8 and sealed-path guards); **the exclusion list recomputed from the table and the recorded
  split** (a key is seen if it occurs on any table row of a train or validation instance) and compared with
  `splits.json`; the label source's provenance equal to the data manifest's (same label block and completion, or the
  same synthetic seed); predictions bound to the data directory and covering exactly the labelled test proposals with
  valid 12-bin vectors; a new output directory.
- **No evaluation-seed value is read:** the test targets are the label-seed (7001–7005) soft labels of the test
  instances, read through `LabelBlockSource`, which never opens evaluation files (a test spies on every `open`).
- **`replay_test_prompts`** replays the test proposals' prompts from the sweep, and **`predict_test`** writes the
  predictions file from a trained model at the arm's temperature. The phase-2 `sft` command wires these into the CLI in
  the P.4 runner unit.
- The mutation check run here (primary set to the full set; "seen" from train only; a loose probability check; a
  label-provenance check on `kind` only) is caught by the tests.

## 6. Evidence labels

- Phase 1: every output is **ENGINEERING_ONLY** (the data manifest's `label_status`, the run manifests, the test
  report). Nothing from phase 1 is cited as a result, or used to choose the phase-2 lr, seeds or arms.
- Phase 2: **EVIDENCE** for the A5 table (B.5), with the host, the frozen environment, the label-block and freeze
  hashes, the data-manifest sha256 and each arm's pins (P.7) recorded.

## 7. Prerequisites (each PASS in the final note)

- **P1** — the sweep-1 label freeze signed (`docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md`), with its
  final verification PASS. For phase 2: the sweep-2 label freeze and the author row releasing it to Track P.
- **P2** — per base, the P.3a record: E0 verdict (pass/fail) and any E4 hard limit, cited from the attempt-1 final
  reports and Unit B (`TRACKP_UNITB_TASL7_D2_RESULT_20261119.md`).
- **P3** — the P.4 runner unit (the `sft` command enabled by this note's file, the test evaluator wired in, the
  per-arm pin file) independently reviewed at the launch commit.
- **P4** — **the Track P per-suite logging branch** merged and reviewed: the Stage S run log and the selection report
  break the val metrics down by suite (T0 CPU nodes now; MLAgentBench, MLGym and autoresearch once T1 labels join),
  as the test evaluator already does for the test read. Precondition for phase 2; for phase 1 (one suite) it is
  recorded as not applicable.
- **P5** — the host named (P4-HOST) and, for 4B bases on a 4090, the memory probe recorded.
- **P6** — author decisions P4-DATA, P4-ARMS, P4-HOST and P4-CAP recorded.
- **P7** — `trackp.py --check-config` clean on the host config; the frozen-environment check (R1-ENV-PIN) PASS.

## 8. Key values (the final note carries these lines)

```
approved: false
label: <ENGINEERING_ONLY (phase 1) | EVIDENCE (phase 2)>
phase: <1 | 2>
labels: <docs/r1/reports/b2_audit_20261119/label_block.jsonl sha256 cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca | the sweep-2 block>
label_freeze: <signed freeze record path and sha256>
table_pin: sweep1_v3 (c3_features/v3, trackp_prompt/v2)
duplicate_policy: heldout_excludes_seen (R1-TRACKP-SFT-DUP)
arms: <P4-ARMS>
lr_grid: 1e-5,3e-5,1e-4; seeds per lr: 3; learning curve: 250,500,1000,2000
host: <TASL-2 | TASL-7 | NEMO2 H200 image v2>
code_commit: <the reviewed P.4 runner commit>
harness_commit: <the frozen harness of the host>
gpu_hours_cap: <P4-CAP>
evaluation_seeds_read: none
```

## 9. Needs a host test (not a cluster test)

- The 4B memory probe on the 4090 at micro-batch 1–4, 1,024 tokens (P4-HOST).
- The per-run time of a 4B base (P4-CAP's assumption).
- For P4-HOST B only: the Track P smoke and E0 equivalence on H200 with image v2 (R1-QTORCH-AMEND).
