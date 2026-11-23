# T0 arms readiness: inventory, featurizer (FEAT-ONE), author decisions (23 November 2026)

Written by the Mac-desk agent (Claude), AI-assisted, from published `main` `1402f466` on branch
`mac-t0-arms-readiness-20261123`. ENGINEERING_ONLY. No table, label block, evaluation block or receipt was opened
for this report; every count below is quoted from a committed report or receipt copy. Nothing here decides anything:
§3 lists the author decisions, each with options and a recommendation.

Authority read: the frozen preregistration `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`
(sha256 `aa1a961b…d7cc5`; §1–§4, §9), `docs/r1/C3_DESIGN.md` §5, PLAN rows R1-SWEEP1-RELEASE-COMPAT,
R1-SWEEP2-RELEASE-DECISIONS, R1-S2-LABELS-TRAINDEV-RELEASE, R1-C3-POOL-EXAM, R1-TABPFN, R1-BX-D13,
R1-FOLD-DECISIONS, R1-P3B-EXAM-DECISIONS, R1-TRACKP-P4-DECISIONS, R1-SWEEP2-LABELS-FREEZE, and
`docs/r1/reports/release_20261122/` (the sweep-1 diagnosis and the sweep-2 train/dev release).

This unit adds `r1/c3/arms_freeze.py`, its tests `r1/tests/test_c3_arms_freeze.py` (33, synthetic) and the runbook
`docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md`.

## 1. Inventory: one row per arm or rung

Role: what the frozen preregistration does with the arm in the one primary read. "Gate series" = `gate.SERIES`
(`A2`, `oracle`, `A3`, `A5`). "Secondary" = PRE-SECONDARY A's per-node test tables (each arm frozen in the record).
"Not in this read" = no test read is preregistered for it.

| Arm / rung | Role in this read | Code on `main` | Training / tuning on train/dev | Host | Missing | This unit builds |
|---|---|---|---|---|---|---|
| A0 = prac-1 (Karpathy default: execute all, keep if Δ̂ > 0; C3_DESIGN relabels A0 as prac-1) | not in this read | `offline_eval.rho` | none | — | nothing for the gate | — |
| prac-2 (fixed-r replication + t-test) | not in this read | none | none (needs r runs per candidate; a closed-loop arm) | — | code, if the closed loop uses it | — |
| A1 (constant per-node prior) | not a gate series; the parent of A2 | `arms.ConstantPrior` | none for the gate | — | nothing | — |
| A2 (A1 + rules) | gate series (reference) | `arms.RulesPrior`; fitted by `gate_input_builder.fit_a2` | fitted **by the builder** on the sweep-2 (and G.5) dev label block (PRE-A2 C) | inside the gate build | nothing; nothing to freeze (its code is the builder, sha bound in the record) | — |
| oracle | gate series (ceiling) | `gate_input_builder._prepare` / `_series_rewards` | none (the same proposal's label block, no features) | inside the gate build | nothing | — |
| **A3** (LightGBM, 12 bins, soft labels) | **primary** | `arms.LGBMPrior` (fixed defaults, 80 rounds; no calibration) | train on P3 train; PRE-POOL pooled vs sweep-2-only chosen by PRE-SELECT A on dev; dev calibration (§4 step 3) | deepthought CPU | the PRE-POOL/PRE-SELECT/calibration pipeline, the prediction file for every gate-source proposal, artefact sha256s, the record entry | `arms_freeze.freeze_a3`, `write_arm`, CLI `train-a3` |
| A3 fold arms (LONO per primary T0 node; LOSO per suite) | secondary (PRE-SECONDARY A, R1-FOLD-DECISIONS) | `fold_analysis` consumes `{fold: {"A3": preds}}`; nothing trains them | retrain without the held-out node/suite; PRE-SELECT and calibration on the fold's dev | deepthought CPU | fold training | `arms_freeze.fold_plan`, `freeze_a3(held_out=…)`, CLI `train-a3 --folds` |
| A3-NGBoost (Gaussian variant, C3_DESIGN §5) | not listed by PRE-SECONDARY A | none (`prior_model` states it does not exist) | would be like A3 | deepthought CPU | code, a pinned `ngboost`, a bin integration | — (ARMS-SECONDARY) |
| A4 (proposer LLM zero-shot, typed answers, isotonic map on dev) | secondary | `prior_model.ManagerQuestionPrior`, `IsotonicMap`, `typed_to_bins`, `chat_client` | one LLM call per gate-source proposal (test included: features only); isotonic maps fitted on dev | proposer LLM host (Track X pick, llama.cpp) | a batch runner over the tables, the dev isotonic fit pipeline (targets: soft[0] and P(Δ>0) of the soft label), prediction file, record entry; its prompt carries the featurizer features, so FEAT-ONE applies | — (ARMS-SECONDARY) |
| **A5** Kev-0.8B / Kev-4B (SFT, temperature on dev) | **primary** (one series: PRE-SELECT A over pool × Kev base) | Track P SFT pipeline on `main`; the P.4 phase-1 runner `r1/c3/train/p4_phase1.py` (arm pin `trackp_p4_arm_pin/v2`: `best.json`, checkpoint manifest, `best/` tree sha, `temperature.json`) is on branch `mac-trackp-p4-runner-20261122` @ `7ab79a9d`, **not merged** into `1402f466` | train on P3 train of sweep 2 (sweep-2-only) and sweep 1 + sweep 2 (pooled), each Kev base; PRE-SELECT A; temperature on dev | NEMO2 H200 via P.4 | **a P.4 evidence phase**: phase 1 (R1-TRACKP-P4-DECISIONS) trains on sweep 1 only, is readiness only and takes no gate decision; its bootstrap uses one pooled base rate, not PRE-SELECT A's per-node base; there is no predict-only path for unlabelled (test) proposals; the frozen checkpoint among the seed runs is undefined (ARMS-A5CKPT) | record binding of A5 entries to P.4 arm pins (`a5_pin_binding`, `tree_sha256` = the pin's tree formula); `choose` implements PRE-SELECT A's tie rule for pool × base |
| A5 other Kev base | secondary | as A5 | as A5 (the non-selected base) | NEMO2 H200 via P.4 | as A5 | as A5 |
| A5 Qwen3.5-0.8B/4B-Base controls | secondary | as A5 | as A5 | NEMO2 H200 via P.4 | as A5 | as A5 |
| A5 fold arms (LONO, LOSO) | secondary (H2b, "A5 − A3 on held-out suites", is read here) | none | Kev retrained per fold, PRE-SELECT on the fold's dev | NEMO2 H200 via P.4 | not in P.4's drafted scope (ARMS-A5FOLD) | — |
| A6 (A5 + decision-focused post-training) | not in this read (the gate takes one A5 series; PRE-SECONDARY A does not list A6) | Track P R-B code (not evidence) | — | — | — | — |
| TabPFN in-context (R1-TABPFN (a)) | secondary | none in `r1/` (no adapter; version open: `proposals/TABPFN_PIN_PROPOSAL_20261028.md`) | in-context set = P3 train rows; bins from the predictive distribution | TASL-7 (R1-TABPFN) | package/weights pin (author), featurizer adapter, CPU fixture tests, runner, prediction file | — (ARMS-SECONDARY) |
| TabPFN fine-tuned (R1-TABPFN (b)) | secondary | none | fine-tune with bounded RPS on soft labels; selection on dev | TASL-7 | all of it | — |
| TabPFN information-matched (R1-BX-D13) | secondary | none | needs the text embedding, its pin and the PCA dimension (open in R1-BX-D13), and Kev's matched view | TASL-7 + H200 | all of it, plus three open author items | — |

Two cross-cutting gaps:

- **T1 rows have no featurizer.** `features.NODE_INFO`/`NODE_CODES` hold only the CPU nodes, and
  `features.NodeContext` refuses any other node, so a G.5 table cannot carry the `FEATURES` that A3, A4 and TabPFN
  read, and PRE-JOINT A ("node and tier as features") cannot be met for T1. `training_rows` refuses a row without the
  full feature set. See ARMS-T1FEAT.
- **The record's code commit must be on `main`.** `arms_freeze.py` is on this branch only until it is reviewed and
  merged; the runbook runs from published `main`.

## 2. One featurizer for arms trained on both sources (FEAT-ONE)

**The fact.** Sweep 1's sealed table (`proposals.jsonl` `b713c423…57c4`, built at `ab79b4ce`) is featurizer v2:
`budget_frac_left = 1 − (b−1)/runs_total` (trial-indexed). Sweep 2's table (`379b17ca…97d9`, built at `db7f344d`) is
v3: `budget_frac_left = 1 − worker_runs_used/runs_total` (`features.py` and `dataset.py` are byte-identical between
`db7f344d` and `1402f466`). A v3 replay of sweep 1 from its own ledgers differs from the sealed table in 116 of 4,999
proposals, only in that field, with the same keys and byte-identical `configs.json` (diagnosis, NaN-aware comparison).
That v3 table already exists and is pinned: `proposals.jsonl` `d0048567…d1d5`, `configs.json` `b585b727…82df`
(`r1/scripts/configs/trackp_sft.json`, table `sweep1_v3`; the P.4 phase-1 note's `table_pin`).

Who reads the field: A3 and TabPFN read it as a column; A4's prompt carries the features JSON; A5's prompt
(`trackp_prompt/v2`, `serialize.py`) states "worker runs used k of W", computed from the ledger prefix, so **A5 sees
v3 semantics on both sources whatever the table says**; the online controller computes v3 (`FEATURIZER_VERSION =
c3_features/v3`). A2 uses sweep 2 only (PRE-A2) and reads no feature but the rule flags; the oracle needs no feature.

**Options.**

- **A (recommended; the coordinator's view, which I share): v3 for every arm.** Sweep 1's arm features come from a v3
  arms table re-derived from its source ledgers with `main`'s builder; the sealed v2 table stays the release's
  integrity artefact and is never edited. An identity check must pass before training: the same (node, proposal_id)
  keys, byte-identical `configs.json`, and no field other than `features.budget_frac_left` differing (NaN-aware).
  Labels join by proposal id (the keys are identical, so every released label row finds its row). The record binds
  the sealed table sha256, the v3 arms-table sha256 and the identity-check result. Reasons:
  1. It is the deployment featurizer: the closed loop (D.3) computes v3 online, so a v2-trained arm would be scored
     offline on one meaning of the column and run online on another.
  2. It makes the arms consistent with each other: A5 already sees worker-run budgets on both sources; under any
     other option A3 and A5 would differ in their budget information on sweep 1, which confounds H2a (A5 − A3).
  3. Under v2, `budget_frac_left` is a deterministic function of `budget_index` (W = 20 in both sweeps), so it carries
     no information of its own; v3 is where it adds the worker-run budget (it differs exactly where the prefix holds
     control-plane skips, precheck rejections or verify runs).
  4. It is checkable: the identity check, the P.4 pin `d0048567…` and the diagnosis replay must all agree, and the
     sealed bytes are untouched.
  Cost: one rebuild on deepthought (minutes) and one more table sha in the record. Risk: none to the labels (keys
  identical); the rebuild must reproduce `d0048567…` exactly, else STOP.
- **B: each source as sealed.** The same column means trial-indexed for sweep-1 rows and worker-run-indexed for
  sweep-2 rows; the pooled A3 learns a mixture, and the pooled-vs-sweep-2-only choice then mixes a source effect with a
  feature-definition effect. Not recommended.
- **C: drop `budget_frac_left` from every arm's features** (`LGBMPrior(drop=…)`; A4's prompt edited; TabPFN view
  edited). Removes the only worker-run budget information from the tabular arms while A5 keeps it in its prompt, and
  diverges from the deployment featurizer. Acceptable only if A is judged too costly; it is not.
- **D: v2 for everything** (re-derive sweep 2 with the v2 builder). Contradicts deployment and A5's prompt, and needs
  an old builder on the evidence path. Not recommended.

What the code does under A: `arms_freeze identity` compares the sealed table and the v3 arms table and returns
pass/fail with counts and proposal ids only; `train-a3` refuses a sweep-1 table that is not the v3 arms table of a
passing identity check against the sealed table the sweep-1 receipt released (`inputs.proposals_sha256`), and refuses
a sweep-2 (or G.5) table other than the one its receipt released. The record checker requires
`feature_tables.featurizer = c3_features/v3`, a passing identity check bound to both shas, and the sealed sha equal to
the label table's.

## 3. Author decisions (each with options and a recommendation)

All can be decided in one PLAN §10 row; the record checker requires each decision to cite an author row by id.

1. **FEAT-ONE** — §2. Recommendation: **A** (v3 for every arm, re-derived sweep-1 arms table, identity check).
2. **ARMS-CAL** — A3's dev calibration (§4 step 3, "fit calibration on dev").
   - **A (recommended): temperature scaling** of the 11 non-inert conditional bins, one scalar fitted on the
     labelled non-inert rows of the PRE-DUP primary dev population (`metrics.fit_temperature`, the family of A5's
     temperature; no-ops keep the inert belief). Order as §4 step 3 lists it: PRE-SELECT scores **uncalibrated**
     predictions, then the chosen variant is calibrated on the same dev rows (so selection does not see an in-sample
     temperature). The same order is recommended for every arm, A5 included.
   - B: none (switch `--calibration none`). C: isotonic per bin (more parameters than 3 dev instances per node can
     support; not built).
3. **ARMS-HP** — A3 hyperparameters. **A (recommended):** `arms.LGBMPrior` defaults fixed (80 rounds, 4 leaves,
   learning rate 0.05, …), no dev selection beyond PRE-SELECT's pooled vs sweep-2-only. B: a declared small grid
   scored by PRE-SELECT (more dev reuse on 3 dev instances per node; not built).
4. **ARMS-WDBC** — which nodes A3 trains and selects on, given the seven-node primary T0 set and the eight-node
   sensitivity run (the builder's `runs` passes one prediction dict to both). **A (recommended):** train and select on
   all eight T0 nodes (plus T1), one A3 for the primary and the sensitivity run; the T0 node set governs evaluation
   only. B: leave `openml_wdbc` out of training and selection, which makes its sensitivity row a held-out-node
   prediction.
5. **ARMS-TWIN** — cross-source repeats in pooled training (twin campaigns give the same (instance, incumbent,
   candidate) in both sources). **A (recommended):** pooled = the union of both sources' train rows, weight 1 each, as
   the preregistration defines no deduplication. B: drop sweep-1 train rows whose (instance, incumbent hash, candidate
   hash) occurs in sweep-2 train.
6. **ARMS-T1FEAT** — T1 has no featurizer (§1). Options: **A (recommended):** commission now a reviewed CPU unit
   that gives G.5 rows the `FEATURES` (node codes appended for the T1 nodes, fields that do not apply set to NaN, the
   tier carried by the node code; how code-level diffs map to the edit fields decided in that unit), so T1 nodes can
   enter the arms if their train/dev labels are released before the record; B: declare the primary read T0-only now
   (PRE-T1 A then freezes an empty T1 set; leave-one-suite-out STOPs, the aggregate gate does not). Under PRE-T1 A
   there is one read, so this decides whether T1 can be in it.
7. **ARMS-A5CKPT** — which P.4 checkpoint is "the" A5 (the P.4 grid has 3 seeds per selected learning rate). **A
   (recommended):** a pre-declared seed (the lowest seed at the selected learning rate), because PRE-SELECT names only
   pool and base as dev choices. B: the seed with the best dev value (an extra dev selection, disclosed). C: the seed
   ensemble (mean of the temperature-scaled distributions; one entry binding three checkpoints).
8. **ARMS-A5FOLD** — fold A5s for leave-one-node-out and leave-one-suite-out (Kev retrained per fold on H200).
   **A (recommended):** in the P.4 evidence phase, per fold the full PRE-SELECT candidate set (pool × Kev base) at the
   primary arm's selected learning rate and the ARMS-A5CKPT seed rule; cost to be projected from the P.4 probe
   (7 LONO folds plus up to 3 LOSO folds, 4 candidates each). Reason: H2b (A5 − A3 on held-out suites) is the
   expected main LM result and leave-one-suite-out is the primary transfer test (R1-BX-D1). B: not built; the fold
   analyses report A3 only and the A5 columns as not built (record: `fold_arms.A5 = not_built:<row>`), disclosed.
9. **ARMS-SECONDARY** — which secondary arms are built before the record (each must be frozen in it; an arm not in
   the record cannot read test in this read). **A (recommended):** the other Kev base and both Qwen controls (P.4
   trains them anyway), A4, and TabPFN in-context if its version decision and a reviewed adapter land in time; the
   NGBoost variant, TabPFN fine-tuned and the information-matched row (R1-BX-D13, three open items) are declared not
   in this read. B: all PRE-SECONDARY rungs, with the record waiting for them. C: only the P.4 rows.

## 4. What blocks the arms-frozen record

1. **The sweep-1 train/dev release** (unit 1, the R1-SWEEP1-RELEASE-COMPAT fix in `release_checks.py`, in review),
   then its rerun under R1-S2-LABELS-TRAINDEV-RELEASE. Without the sweep-1 receipt there is no pooled variant, so
   PRE-POOL cannot be decided, and the record has no sweep-1 label table.
2. **The author decisions of §3** (one PLAN row). FEAT-ONE and ARMS-CAL/HP/WDBC/TWIN gate A3; ARMS-A5CKPT,
   ARMS-A5FOLD and ARMS-SECONDARY gate the record's arm list.
3. **A5 from P.4**: the P.4 runner merged; image v2.1 checks and the phase-1 note signed (R1-TRACKP-P4-DECISIONS);
   then a P.4 evidence phase (not drafted) that trains sweep-2-only and pooled per base, scores PRE-SELECT A
   (`arms_freeze.preselect_score`/`choose` can be reused on its dev predictions), writes predictions for every
   gate-source proposal including test proposals (a predict-only path from the prompt, no label), and pins the
   checkpoint by ARMS-A5CKPT. The record checker binds each A5-family entry to exactly one run of its arm pin.
4. **This unit reviewed and merged** (the arms' code commit must be on `main`), and LightGBM present in the
   deepthought environment (its version recorded; the model bytes depend on it).
5. **T1**: the G.5 labels, their train/dev release (R1-T1-LABELS-UNSEAL with the G.1b summaries) and ARMS-T1FEAT,
   unless the read is declared T0-only.
6. **The disclosure items** of §4 step 4: the Track P SFT uses on `trackp_sft/v1` and the exam set's provenance
   (R1-P3B-EXAM-DECISIONS), written by the coordinating chat from the committed records.

## 5. Readings stated (for the reviewer)

- PRE-SELECT A is scored on the gate sources' PRE-DUP primary dev population (`primary_dev_population`), labelled
  rows only (no-ops with their inert label, audit labels; divergent and duplicate rows have no soft label), with the
  base rate of each node's own P3 train label block of the gate source (sweep 2 for T0, G.5 for T1); sweep-1 dev rows
  are used neither for training nor for selection. A node with no scored dev row, or a base-rate RPS of 0, is left out
  of the mean for every candidate and reported.
- "Trained on train": pooled = sweep-1 train + sweep-2 (+ G.5) train rows; dev rows of either source never train.
- Predictions cover every gate-source proposal, test proposals included, from features only, and pass
  `gate_input_builder._rule_layer`; a test feeds them into `gate_input_builder.build`.
- The record is a Markdown file under `docs/r1/` with one fenced JSON block, the path form `release.row_text` cites
  for the test release row (a test checks the row pattern accepts it).
