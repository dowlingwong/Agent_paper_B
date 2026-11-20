# Track P P.4 (A5 SFT, belief only), phase 1: authorization draft (approved: false)

**Status: DRAFT for the author's signature. `approved: false`. Authorizes nothing.** Revision 2, after round 1 of the
independent review.
- **Scope: phase 1 only** — the full P.4 protocol on the sweep-1 B.2 labels as ENGINEERING_ONLY readiness. The
  evidence phase (sweep 2, A5 for the C3 gate and B.5) needs its own note after the sweep-2 analysis preregistration;
  §9 lists what that note must decide.
- On signature, the coordinating chat publishes the final version to `main` as
  `docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md`, with every prerequisite in §7 recorded as PASS. The CLI command
  `trackp.py sft` stays "not yet" until then (`NOT_YET["sft"]` names this file).
- Written by the Mac-desk agent (Claude), AI-assisted. Execution is the Track P agent's (R1-TRACKP-RUNBOOK-SCOPE: the
  Mac runs no Track P training); this draft and the test evaluator are desk work.
- Values marked *(proposed)* are recommendations. Six author decisions are open (§2).

## 1. Authority (published `main` `4aac5209`; PLAN as at `94db94bb` plus R1-S2C3B-WDBC)

| Row | What it fixes here |
|---|---|
| RUNBOOK P.4 | A5 SFT (belief only) on the finalists + control: soft-label RPS + CE on the B.2 labels; LoRA r = 16; adapter lr from {1e-5, 3e-5, 1e-4} by val RPS for every family; early stop on dev RPS; best checkpoint; temperature / isotonic recalibration on dev (R1-TEMPERATURE fixes post-hoc temperature scaling for all models, so no isotonic step); report RPS skill, NLL, all-bins and top-1 ECE, PIT, width ratio, then offline one-step value through `rules.decide`; learning curve 250/500/1k/2k. **RL gate** for P.5/P.6: RPS skill > 0 significantly, > 99 % mass on bin outputs over 3 seeds, all-bins ECE ≤ 0.05, width ratio in [0.8, 1.25]. |
| R1-C3-POOL, R1-C3-POOL-EXAM | The A5 candidates are Kev-0.8B and Kev-4B: "both Kev sizes go on to P.3b and A5 unless one fails E0 or an E4 hard limit; the Qwen control is carried as before." |
| R1-C3-CONTROL, R1-CONTROL-READOUT | Qwen3.5-0.8B-Base and -4B-Base + LoRA, always carried as an ablation arm, not a candidate; the primary belief readout is a fresh LayerNorm + linear head, with the bin-token readout as the secondary row. |
| R1-SOFT-SIGMA, R1-LR-GRID, R1-TEMPERATURE | Soft label s = σ̂_node/√K_label (pooled σ̂); one lr grid; post-hoc temperature scaling on dev for all models. |
| R1-TRACKP-SFT-DEV | Build and trial-run the SFT pipeline on the sweep-1 table now (ENGINEERING); plug in the sweep-1 B.2 label block when it exists; readiness only — not used for any evidence, selection or tuning; the 7006–7010 evaluation block is not read. "Train directly once the sweep-2 labels are in place." |
| R1-TRACKP-SFT-DUP | Held-out without duplicates of the training set is the primary result; the full held-out is secondary (sweep 1: train 1,176 / val 47 / test 74 of 262 labelled test proposals). The builder and the evaluator read "seen" for test as seen on a **train or val** instance: only that reading gives 74 (train only gives 77). |
| R1-MAIN-PROPOSER (e) | The A5/A6 evidence checkpoints use sweep 2; sweep 1 is added as a stratum; both sources use **one instance → train/dev/test assignment**, and twin campaigns give the same (instance, incumbent, edit) the same label in both sources. Until sweep 2 exists, Track P may run its pipeline on sweep-1 labels as ENGINEERING_ONLY, label seeds 7001–7005 only, never 7006–7010. |
| R1-BX-D8-V3-A/B, R1-BX-D8-CONFIRM | A5 is a C3 gate arm; the gate split is P3 (1/3 : 1/6 : 1/2 per tier, written into the analysis preregistration), with ≥ 9 T0 test instances per node. The sweep-2 analysis preregistration draft (`mac-sweep2-prereg-20261121`, PRE-SPLIT A) proposes P3 for every evidence arm, Track P included. |
| R1-TASL7-TRACKP, R1-TRACKP-TASL2-HOST | Track P evidence tables on TASL-7 or TASL-2 (both RTX 4090; TASL-2's frozen `trackp-gpu` env verified byte-identical); one host per table, named in the report. |
| R1-QTORCH-AMEND, R1-TRACKP-I3-H200 | Image v2 approved for Track P on HTCondor, after I2/I3 on v2 and a Track P smoke and E0 equivalence check per GPU model (H200 first). |

**What exists now.**
- The SFT pipeline (`r1/c3/train/sft_data.py`, `sft.py`, `trackp.py sft-data|sft-dev|sft-select`) with the
  decided policy `heldout_excludes_seen`, on `main`.
- The ENGINEERING trial on TASL-2 (`ops-tasl-20261116` @ `f557f985`, synthetic labels): kev-0.8b, lr 3e-5, seed 0,
  1,176 training rows (74 steps per epoch, 370 planned); the default micro-batch 8 OOMed on the 24 GB card;
  micro-batch 4 (effective batch 16 unchanged) **early-stopped at step 126 of 370** (best step 90) in 159 s wall,
  peak 16,511 MiB. Finding 1 of that trial: `_stage_s` never enables gradient checkpointing, although the host config
  sets `gpu.gradient_checkpointing: true` and the E0 path applies it.
- P.3a ran the 4B bases through the E0 path on a 24 GB 4090 (TASL-7; Unit B, `TRACKP_UNITB_TASL7_D2_RESULT_20261119.md`
  on `ops-tasl-20261116` @ `2287e492`, campaign lease 130,925 GPU-s); those records give the 4B memory and step-time
  reference with gradient checkpointing on.
- The sweep-1 label block (`label_block.jsonl`, sha256 `cdae9c3f…9aca`), with its freeze record drafted and accepted
  for signature (READY 62).
- **New in this unit:** the P.4 test evaluator `r1/c3/train/sft_test_eval.py` (§5).

## 2. Author decisions (phase 1)

### P4-PHASE1-TEST: a real-label test read in phase 1? (recommendation: A)

Sweep 1 and sweep 2 share one instance assignment and twin campaigns share labels (R1-MAIN-PROPOSER (e)), so the
sweep-1 test instances are the sweep-2 test instances, with the same labels on twin proposals. R1-MAIN-PROPOSER (e)
fixes the pooled-versus-sweep-2-only choice on validation "before any test read".
- **A (recommended): no real-label test read in phase 1.** The test evaluator runs in phase 1 on synthetic labels only
  (as its tests do), to show the path works on the host. The evaluator enforces this: it refuses real labels on
  ENGINEERING_ONLY data.
- **B: a phase-1 test read on the real sweep-1 labels.** It uses up the evidence test partition before the phase-2
  arm, data variant, lr, seed set, checkpoint and temperature are fixed; anyone who sees it knows test performance on
  the partition the gate and B.5 will use. Needs the evaluator's `allow_engineering_real_label_read=True`, recorded in
  the note.

### P4-P1SPLIT: which instances phase 1 trains and validates on (recommendation: A, if PRE-SPLIT A is signed)

- **A (recommended): the P3 assignment.** The builder's split config becomes salt `c3_p3_split/v1`, 9 test and 3
  validation instances per node (the remaining 6 train), which reproduces the preregistration's P3 ordering
  (sha256 of `c3_p3_split/v1:<instance id>`). No sweep-1 label of a P3 test instance enters phase-1 training or
  validation. About half the training rows of the trial (exact counts from the build).
- **B: the current `trackp_sft/v1` split** (3 test, 3 validation, 12 train per node). Allowed by R1-MAIN-PROPOSER (e)
  as ENGINEERING_ONLY, but it trains on the labels of 4–7 P3 test instances per node (computed from seeds and salts
  only, by the preregistration's reviewer), and its instance assignment differs from the evidence one.

### P4-ARMS: which bases (recommendation: A)

- **A (recommended):** `kev-0.8b` and `kev-4b`, minus a Kev base whose P.3a record shows an E0 failure or an E4 hard
  limit (cited per base in P2); the controls `qwen3.5-0.8b-base` and `qwen3.5-4b-base` are **always carried**
  (R1-C3-CONTROL). A control that cannot be trained is a STOP for the author, not a silent drop. P.3b (the labelled
  exam) runs alongside as the appendix table; it no longer selects (R1-C3-POOL-EXAM), so it is not a gate for P.4.
- **B: Kev only in phase 1.** Halves phase 1, but the A5(Kev) − A5(control) readiness comparison is then missing
  until the evidence phase.

### P4-HOST: where (recommendation: A, then A′, with B as the whole-table fallback)

One host per table (R1-TRACKP-TASL2-HOST); phase 1 is one table.
- **A (recommended): TASL-2 or TASL-7 (RTX 4090, the frozen `trackp-gpu` environment).** Host equivalence passed;
  the trial ran there. First step: a one-run memory probe per 4B base at micro-batch 1–4 (effective batch 16).
- **A′ (if a 4B base does not fit at micro-batch 1 under A):** enable gradient checkpointing in the SFT path — a
  reviewed code change in the P.4 runner unit (P3), applied when the host config sets
  `gpu.gradient_checkpointing: true`, recorded in the run manifest; effective batch, loss, lr and schedule unchanged
  (a host-fit knob like the micro-batch). The probe is repeated with it. P.3a's E0 records show 4B bases fit a
  24 GB 4090 with gradient checkpointing.
- **B: NEMO2 H200 with image v2 for the whole table**, only if A′ fails. It needs I2/I3 on v2, the Track P smoke
  and the E0 equivalence check on H200 (R1-QTORCH-AMEND), an HTCondor Track P job with a reviewed switch, and the
  queue. Not ready now.
- **C: split by base size (0.8B on 4090, 4B on H200).** Two hosts in one table; not allowed by R1-TRACKP-TASL2-HOST.

### P4-LC: the learning curve on a small training set (recommendation: A)

RUNBOOK P.4's curve is 250/500/1k/2k examples; phase 1 has 1,176 training rows under P4-P1SPLIT B and about half that
under A, so the larger points cannot be run.
- **A (recommended):** run the points below the training-set size and add the full training set as the last point
  (it is the selected-lr grid run, so it costs nothing extra); "examples" = training rows of the data directory,
  rule no-ops included, drawn by a fixed seed per point.
- **B:** omit the learning curve in phase 1.

### P4-CAP: GPU budget for phase 1 *(proposed: 40 GPU-h)*

Runs per base: the lr grid 3 × 3 seeds (9 runs) plus, under P4-LC A, the learning-curve points below the training set
× 3 seeds. Cost scales with the training rows (steps = rows × 5 epochs / 16).
- Measured: 126 steps (early stop) in 159 s at 0.8B including the step-0 evaluation and model load, i.e. about
  1.26 s per step; a full 5-epoch run on 1,176 rows (370 steps) would take about 7.8 min.
- **Without early stopping** (the conservative case):
  - P4-P1SPLIT B (1,176 rows): per base 9 + 3 × (250 + 500 + 1,000)/1,176 ≈ 13.5 full-run equivalents; 0.8B bases
    2 × 13.5 × 7.8 min ≈ 3.5 h; 4B bases *(assumed 5 × the 0.8B time; to be replaced by the P.3a and probe
    timings)* ≈ 17.5 h; **≈ 21 GPU-h**.
  - P4-P1SPLIT A (≈ 590 rows): per base 9 + 3 × (250 + 500)/590 ≈ 12.8 full-run equivalents of ≈ 3.9 min; **≈ 10 GPU-h**.
- **With early stopping as in the trial** (about a third of the steps): about 7 and 3.5 GPU-h respectively.
- Memory probes, the host checks and the synthetic test-path run: under 2 GPU-h.
- The cap of 40 covers the conservative case even if the 4B runs take 8 × the 0.8B time (B: ≈ 31.5 GPU-h). It
  bounds the projection and the GPU-hours consumed (the lease log); a run that would exceed it is not started.

## 3. Protocol (RUNBOOK P.4 and the SFT pipeline; phase 1)

- Data: `trackp.py sft-data` on the pinned `c3_features/v3` table with `trackp_prompt/v2`, the sweep-1 label block
  bound to its sweep index and classification, the decided policy `heldout_excludes_seen`, the split of P4-P1SPLIT
  over the fixed instance universe (8 nodes × 18 instances).
- Training: `sft-dev`: loss RPS + CE on the soft label; LoRA r = 16; effective batch 16 (the host may set the
  micro-batch and, under P4-HOST A′, gradient checkpointing only); ≤ 5 epochs; evaluation every ¼ epoch; early
  stopping on **primary** val RPS (patience 2); best checkpoint; temperature fitted on primary val.
- Selection: `sft-select` picks the lr by mean best primary val RPS over 3 seeds (R1-LR-GRID); in phase 1 its output
  selects nothing for the evidence phase (ENGINEERING_ONLY).
- Report per arm: primary and secondary val metrics (raw and temperature-scaled), the learning curve (P4-LC), the
  RL-gate quantities on **primary val** with an instance-cluster bootstrap 95 % interval for RPS skill (2,000
  resamples, seed 20261108) as readiness — **no gate decision is taken in phase 1**; for the controls, the
  bin-token readout as the secondary row (R1-CONTROL-READOUT).
- **Test:** under P4-PHASE1-TEST A, no real-label test read; the evaluator runs once on a synthetic-label build on
  the host as a path check.
- Offline one-step value through `rules.decide` uses the evaluation half of the audit (7006–7010) and is not part of
  phase 1 (R1-MAIN-PROPOSER (e)).

## 4. STOPs

- The label block's sha256 differs from its freeze record (`cdae9c3f…9aca`), or the freeze is not signed.
- Any read of the evaluation block, `runs.jsonl`, or the 7006–7010 values (the loaders refuse them by name; any other
  route is a STOP).
- Any real-label test read in phase 1 (under P4-PHASE1-TEST A; the evaluator refuses it).
- A data directory built under a policy other than `heldout_excludes_seen` with real labels (refused at build and
  load), or a split other than the one P4-P1SPLIT names.
- A sealed path (`r1_sealed`); any sweep-2 file.
- A host other than the one named for the table; a frozen-environment mismatch (R1-ENV-PIN).
- CUDA OOM at micro-batch 1 for a base after A′ (P4-HOST); any change of the effective batch, lr grid, epochs,
  patience or loss (the run records a protocol deviation and is not reported as P.4).
- A control arm that cannot be trained (P4-ARMS).
- The cap (P4-CAP).
- Every STOP keeps its outputs; there is no deletion and no silent retry.

## 5. The P.4 test evaluator (implemented and tested in this unit)

`r1/c3/train/sft_test_eval.py` (branch `mac-trackp-p4-20261120`), tests `r1/tests/test_trackp_sft_test_eval.py`
(35 tests, CPU only; the tiny `hashbag` model for the prediction path). It is built for the evidence phase and used
in phase 1 only on synthetic labels.

- **`evaluate_test(data_dir, table_dir, label_source, logits, run_dir, out_dir, arm=…, ledger=…, suite_of=…)`**
  writes `test_report.json` (`trackp_sft_test_report/v2`) once and appends the read to the test-read ledger:
  - **primary** metrics (`test_*`): the labelled test proposals not in `splits.json`
    `test_proposals_seen_in_train_or_val`; **secondary** (`test_full_*`): every labelled test proposal;
  - both at the arm's fitted temperature (headline) and raw, from one logits file;
  - the Stage S belief metrics, by node and by suite on the primary population with both counts (a given suite
    mapping must name every node); the counts include the rule no-ops per population; NaN is written as null.
- **Bindings, each a STOP:**
  - the data directory's hashes, versions and policy;
  - the split recomputed from its config and universe record;
  - the table, loaded with the data manifest's table hashes as pins, with unique ids;
  - **the exclusion list recomputed** from the table and the split (a key is seen if it occurs on any table row of a
    train or validation instance, labelled or not) and compared with `splits.json`;
  - the label source's provenance (kind, sha256, seed, shift_z, sweep, completion) equal to the data manifest's;
  - **the arm:** the run's `sft_report.json` names this data directory; the temperature comes from
    `best/temperature.json`; the logits file carries the sha256 of `sft_report.json`, `best.json`,
    `best/temperature.json` and the `best/` tree as they are at evaluation, the arm id, and the replay record (table
    hashes, sweep index sha256, ids);
  - **one test read per arm:** the ledger refuses a second read of the same arm id, or of the same best checkpoint
    under another id, on the same data directory; the output directory must be new;
  - phase 1: real labels on ENGINEERING_ONLY data are refused (P4-PHASE1-TEST).
- **Test target:** the label-seed (7001–7005) soft labels of the test instances, read through `LabelBlockSource`,
  which never opens evaluation files (a test spies on every `open`). This is the phase-1 target; the report records
  `test_target`. The evidence target is the phase-2 note's P4-TARGET (§9).
- **`replay_test_prompts`** replays the test proposals' prompts from the sweep against the pinned table and checks
  every replayed proposal's features against its table row; **`predict_test`** writes the logits file from the arm's
  best model with the run binding and the replay record. The phase-2 `sft` command wires these into the CLI in the
  P.4 runner unit.
- Mutation check run here (20 mutations of the evaluator, all caught): base rate uniform; "seen" from labelled rows
  only; temperature ignored; policy, version, sweep, completion, arm, sweep-index, best-tree, split-recomputation,
  duplicate-id, feature-binding and phase-1 checks removed; the ledger removed or keyed on the arm only; primary set
  to the full set; unmapped suites allowed; NaN kept; groups present only among the excluded proposals dropped.

## 6. Evidence labels

Every phase-1 output is **ENGINEERING_ONLY** (the data manifest's `label_status`, the run manifests, the synthetic
test report). Nothing from phase 1 is cited as a result, or used to choose the evidence phase's lr, seeds or arms.

## 7. Prerequisites (each PASS in the final note)

- **P1** — the sweep-1 label freeze signed (`docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md`), with its
  final verification PASS.
- **P2** — per Kev base, the P.3a record: E0 verdict and any E4 hard limit, cited from the attempt-1 final reports
  and Unit B (`ops-tasl-20261116` @ `2287e492`); the 4B step times and memory of those records.
- **P3** — the P.4 runner unit, independently reviewed at the launch commit: the split config of P4-P1SPLIT, the
  learning-curve sampler of P4-LC, gradient checkpointing in the SFT path (P4-HOST A′), the bootstrap interval of §3,
  the test evaluator wired in with a ledger path per table, and the per-arm pin file.
- **P4** — the Track P per-suite logging unit (Stage S run log and selection report broken down by suite; still to
  be written, by the Track P runner unit or a Mac-desk unit): **not applicable to phase 1** (T0 is one suite) — an
  explicit author tick in the final note; a precondition of the evidence phase.
- **P5** — the host named (P4-HOST) and, for 4B bases on a 4090, the memory probe recorded.
- **P6** — author decisions P4-PHASE1-TEST, P4-P1SPLIT, P4-ARMS, P4-HOST, P4-LC and P4-CAP recorded.
- **P7** — `trackp.py --check-config` clean on the host config; the frozen-environment check (R1-ENV-PIN) PASS.

## 8. Key values (the final note carries these lines)

```
approved: false
label: ENGINEERING_ONLY
phase: 1
labels: docs/r1/reports/b2_audit_20261119/label_block.jsonl sha256 cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca
label_freeze: <signed freeze record path and sha256>
table_pin: sweep1_v3 (c3_features/v3, trackp_prompt/v2)
duplicate_policy: heldout_excludes_seen (R1-TRACKP-SFT-DUP)
split: <P4-P1SPLIT: c3_p3_split/v1 9/3/6 | trackp_sft/v1 3/3/12>
arms: <P4-ARMS>
lr_grid: 1e-5,3e-5,1e-4; seeds per lr: 3; learning curve: <P4-LC>
host: <TASL-2 | TASL-7 | NEMO2 H200 image v2>; gradient_checkpointing: <off | on (A′)>
real_label_test_read: <none (P4-PHASE1-TEST A) | allowed (B)>
code_commit: <the reviewed P.4 runner commit>
harness_commit: <the frozen harness of the host>
gpu_hours_cap: 40
evaluation_seeds_read: none
```

## 9. What the evidence-phase note must decide (not authorized here)

- **P4-TARGET:** the test belief metrics against `y_eval` (7006–7010) as spec §7.1 declares, read through a
  separately guarded evaluation-block path after the arm is fixed (recommended), or label-seed targets with a PLAN row
  amending spec §7.1.
- **The split and data composition:** the preregistration's P3 split (PRE-SPLIT); T0 sweep 2 with sweep 1 as a
  stratum, T1 labels with tier as a stratum; pooled versus sweep-2-only chosen on validation (PRE-POOL); the source
  stratum and the within-test grouping of cross-source duplicates by (instance, incumbent hash, edit hash).
- **The RL gate:** its population (primary test) and interval (instance-cluster bootstrap, R1-MAIN-PROPOSER (e)4),
  and the held-out-node / leave-one-suite-out reports (spec §7.2, R1-BX-D1).
- **The release of sweep-2 labels to Track P:** *(proposed, new gate)* an author row citing the preregistration, as
  its PRE-STAGE does; R1-TRACKP-SFT-DEV alone says to train once the labels are in place.
- **The host:** whether an evidence table on H200 needs a row naming H200 beside TASL-2 and TASL-7
  (R1-TRACKP-TASL2-HOST).
- The budget with each multiplier listed (training rows, both data variants, T1, folds).

## 10. Needs a host test (not a cluster test)

- The 4B memory probe on the 4090 at micro-batch 1–4, 1,024 tokens, with and without gradient checkpointing.
- The per-run time of a 4B base (P4-CAP's assumption; P.3a's records first).
- The synthetic-label test-path run of the evaluator on the host.
- For P4-HOST B only: the Track P smoke and E0 equivalence on H200 with image v2 (R1-QTORCH-AMEND).
