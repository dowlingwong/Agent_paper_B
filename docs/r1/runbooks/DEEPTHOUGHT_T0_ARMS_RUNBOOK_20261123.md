# Deepthought runbook: T0 arms on train/dev and the arms-frozen record (23 November 2026)

**Status: DRAFT, revised after independent review round 1, for re-review with the arms-readiness unit**
(`mac-t0-arms-readiness-20261123`; report `docs/r1/reports/arms_readiness_20261123/T0_ARMS_READINESS_20261123.md`).
Written by the Mac-desk agent (Claude), AI-assisted. ENGINEERING_ONLY until the record is committed.

**Who and what.** The cluster agent on deepthought, in **two runs**:
- **Run I** (steps 1–3, on one published commit `$C`): check the pinned sweep-1 v3 arms table, run the FEAT-ONE
  identity check, and train, select and calibrate A3 and the fold A3s on train/dev labels. Its artefacts are sealed.
- **Run II** (steps 4–6, a resumed run on a fresh clone of the then-current `main`, `$C2`): collect the A5 entries
  from P.4, write and check the arms-frozen record (preregistration §4 step 4), and deliver it on a new branch for the
  author. Run II can start days later; Run I's artefacts and their code commit carry over.

**The test release row comes only after the author.** Neither run releases, opens or reads a test label or an
evaluation block.

Steps marked **[WAITS: …]** do not start until the named author decision is in a PLAN §10 author row on `main` (the
ids of the readiness report §3). Every **STOP** ends the run: report what happened, keep all outputs, change nothing,
and return to the author through the coordinating chat.

## 0. Rules for both runs

- Read only: table `proposals.jsonl`/`configs.json`/`build.json`; the receipted train/dev partitions through
  `r1.c3.arms_freeze` (which calls `release.traindev_labels` with the receipt sha256 pinned); P.4's sealed outputs;
  committed files. **Never** open a raw `label_block.jsonl`, any `evaluation_block*.jsonl`, any
  `label_block.test.jsonl`, a `runs.jsonl`, or a `test/` release partition; never run `r1.c3.release --stage test`;
  never print or copy a label value. A deliberate read of any of these is a STOP (preregistration §6).
- Nothing is trained, tuned or selected on test or on any evaluation seed (7006–7010).
- Within one run: one clean checkout at one published commit; `git status --porcelain --untracked-files=no` empty
  before every step; no edit to any tracked file of that checkout.
- Environment, every command: `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
  NUMEXPR_NUM_THREADS=1`, interpreter `$PY` (I-P2). Record every command, its exit code and its stdout in the run log.
- Work directories are new for each run (`$W=/work/dwong/arms_t0_<YYYYMMDD>/` for Run I, `$W2=/work/dwong/arms_t0_rec_<YYYYMMDD>/`
  for Run II); the sealed artefact root is `$A=/ceph/srv/dwong/paperb/`, where Run I writes a new
  `$A/arms_t0_<YYYYMMDD>/`. Existing directories are never reused.
- Never push to `main`; deliver on a new branch only.

## Run I

### I.1 Preconditions (any failure is a STOP)

| # | Check | How |
|---|---|---|
| I-P1 | `r1/c3/arms_freeze.py` is on published `main` (this unit reviewed and merged) | `git clone` the repo to `$W/paper` at `origin/main`; `$C=$(git -C $W/paper rev-parse HEAD)`; `git -C $W/paper merge-base --is-ancestor $C origin/main`; record `$C` |
| I-P2 | Interpreter with numpy, scipy, scikit-learn and LightGBM | `$PY=/ceph/dwong/r1_prepare_20261025/venv/bin/python3` (the release step's); `$PY -c "import platform, numpy, scipy, sklearn, lightgbm; print(platform.python_version(), numpy.__version__, scipy.__version__, sklearn.__version__, lightgbm.__version__)"`; record. **LightGBM is not known to be present in this venv. Absent: STOP** (the author decides whether it enters that venv or a separate one; do not install into a shared venv on your own). The versions also go into every A3 entry (`toolchain`) |
| I-P3 | The sweep-2 train/dev receipt opens | `$R2=/work/dwong/s2_release_20261122/release_sweep2_traindev_v2`; `sha256sum $R2/sweep2/traindev/RECEIPT.json` = `de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c` (= `docs/r1/reports/release_20261122/RECEIPT_sweep2_traindev_v2.json`); its `outputs.label_block.traindev.jsonl` = `7487b627e40edae37022f4467a60867b09bdbd395e61caa20302c090d8e5fe82`, `inputs.proposals_sha256` = `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9`, `counts.evaluation_rows` = 0 (read the receipt's JSON fields only). **Note:** the receipt opens only while the R1-S2-LABELS-TRAINDEV-RELEASE row text in PLAN §10 and its release commit `a9d8ff5e` are unchanged (`release.open_partition` compares the row's `decision_sha256`). Unit 1 changes only `r1/c3/release_checks.py`, not that row. If the row has changed on `main`, the receipt will not open: STOP and return to the author |
| I-P4 | The sweep-2 table the receipt released | `$T2=/work/dwong/s2_audit_20261122/table`; `sha256sum $T2/proposals.jsonl` = `379b17ca…97d9`. (Sweep 2's receipt counts 0 no-ops and only audit labels, so its training and selection rows are audit labels; within-campaign duplicates carry no label.) |
| I-P5 | The sweep-1 train/dev receipt **after the unit-1 fix** (R1-SWEEP1-RELEASE-COMPAT), with its release report committed on `main` | `$R1=` the release root that report names; `$S1=` the receipt sha256 that report gives; `sha256sum $R1/sweep1/traindev/RECEIPT.json` = `$S1`; receipt `inputs.proposals_sha256` = `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4`, `inputs.label_block_sha256` = `cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca`, `counts.evaluation_rows` = 0. **No such report on `main`: STOP** (this runbook does not run the release) |
| I-P6 | The sealed sweep-1 table | `$T1S=/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table`; `sha256sum $T1S/proposals.jsonl` = `b713c423…57c4`, `$T1S/configs.json` = `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df` |
| I-P7 | The pinned sweep-1 v3 arms table (the W2.3 rebuild named in `r1/scripts/configs/trackp_sft.json`, `tables.sweep1_v3.host_path`) | `$T1V=/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z`; `sha256sum $T1V/proposals.jsonl` = `d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5` and `$T1V/configs.json` = `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df` (the two files `trackp_sft.json` pins; `build.json` is recorded, not pinned). Directory absent or any hash different: **STOP** (do not rebuild in its place under this runbook) |
| I-P8 | The author row with the readiness decisions | grep its id in `$W/paper/docs/r1/PLAN.md` §10; record which of FEAT-ONE, ARMS-CAL, ARMS-LEFTOUT, ARMS-HP, ARMS-WDBC, ARMS-TWIN, ARMS-T1FEAT it decides |
| I-P9 | The primary T0 set | the C3b result at the launch commit (seven nodes without `openml_wdbc`, or all eight if the C3b rerun gave 8/8), from its committed record; record `seven` or `eight` |
| I-P10 | T1 (only if ARMS-T1FEAT A and T1 labels exist) | the R1-T1-LABELS-UNSEAL receipt (`$RG`, sha `$SG`), the G.5 table with features, and the frozen T1 setting `$W/t1.json` = `{"suites": {...}, "modes": [...], "d3_k6": false}`. Otherwise the read is T0-only and `--t1` is omitted |

### I.2 Step 1 — the sweep-1 v3 arms table **[WAITS: FEAT-ONE]**

Only under FEAT-ONE A (under C or D this runbook needs a revision first: STOP). The arms table is `$T1V`, checked in
I-P7; nothing is rebuilt. (The code also refuses any sweep-1 table whose bytes differ from the pin
`SWEEP1_V3_PROPOSALS_SHA256`.) Record `$T1V`'s `build.json` sha256 (expected `7f56619c2cc5ef2145ace44350baac3bc7906433e279a284e9627a2452e1b643`
per `trackp_sft.json`; recorded, not a STOP, since `build.json` holds paths).

### I.3 Step 2 — FEAT-ONE identity check **[WAITS: FEAT-ONE]**

From `$W/paper`:

```
$PY -B -m r1.c3.arms_freeze identity --sealed $T1S --arms-table $T1V --out $W/feat_one_identity.json
```

Expected: exit 0; `pass` true; `n_sealed` 4999; `keys_equal` and `configs_equal` true; `n_other_differences` 0;
`n_budget_frac_left_differ` **116** (the diagnosis' count); `sealed_proposals_sha256` = `b713c423…57c4`,
`arms_proposals_sha256` = `d0048567…d1d5`. Exit 3, or any other value: **STOP** (a pass with a count other than 116
is also a STOP: the inputs are the ones the diagnosis compared). Record `sha256sum $W/feat_one_identity.json`.

### I.4 Step 3 — A3 and the fold A3s **[WAITS: ARMS-CAL, ARMS-LEFTOUT, ARMS-HP, ARMS-WDBC, ARMS-TWIN; ARMS-T1FEAT if T1]**

The code implements: calibration `temperature` (ARMS-CAL A) or `none` (B); the left-out-node rule of ARMS-LEFTOUT A;
the `LGBMPrior` defaults (ARMS-HP A); all T0 nodes in training and selection (ARMS-WDBC A); twin weighting
`group` (ARMS-TWIN B) or `none` (A). If the author row chose ARMS-LEFTOUT B, ARMS-HP B, ARMS-WDBC B or ARMS-TWIN C:
**STOP** (a code change and review come first).

```
mkdir -p $A/arms_t0_<YYYYMMDD>
$PY -B -m r1.c3.arms_freeze train-a3 \
  --release-root sweep1=$R1 --receipt sweep1=$S1 --table sweep1=$T1V \
  --release-root sweep2=$R2 --receipt sweep2=de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c \
  --table sweep2=$T2 \
  --identity $W/feat_one_identity.json \
  [--release-root g5=$RG --receipt g5=$SG --table g5=<G.5 table> --t1 $W/t1.json] \
  --calibration <temperature|none> --twin-weight <group|none> --folds --primary-t0 <seven|eight> \
  --artefact-root $A --out $A/arms_t0_<YYYYMMDD>/a3
```

It refuses (non-zero exit, `ArmsFreezeError` or `ReleaseStop`) on: a receipt other than the pinned one; a partition
that fails `release.open_partition`'s checks; a test label or an evaluation field; a sweep-2 table other than the
one released; a sweep-1 table other than the pinned v3 table, or an identity result that does not bind it to the
released sealed table with at least one difference; a row without the full feature set; a dirty checkout. **Any
refusal: STOP.**

Checks on the output (`entries.json` and each arm's `selection.json`; they hold no label value):
- arms `A3` and one `A3@lono:<node>` per primary T0 node (plus `A3@loso:<suite>` per suite of the frozen T1 set);
- `A3.n_predictions` = the number of rows in `$T2/proposals.jsonl` (plus the G.5 rows if T1); each fold arm's
  `n_predictions` = its held-out nodes' gate-source rows;
- every `preselect.dev_values` finite; `code_commit` = `$C`; `toolchain` = the I-P2 versions; `twin_weight` as decided;
- `cd $A && sha256sum -c` over the entries' paths passes. Write `$A/arms_t0_<YYYYMMDD>/a3/SHA256SUMS`, copy
  `$W/feat_one_identity.json` and the run log beside it, and make the directory read-only (`chmod -R a-w`).

End of Run I: write `$A/arms_t0_<YYYYMMDD>/RUN_I.md` (commands, exit codes, stdouts, `$C`, versions, every sha256) and
report to the coordinating chat. If P.4's A5 arms are not yet sealed, stop here; nothing is lost.

## Run II (resumed)

### II.1 Preconditions (any failure is a STOP)

| # | Check | How |
|---|---|---|
| II-P1 | A fresh clone of the then-current `main` | clone to `$W2/paper`; `$C2=$(git -C $W2/paper rev-parse HEAD)`; record it. All Run II commands run from a delivery worktree of this clone (II-P6) |
| II-P2 | Run I carries over | `git -C $W2/paper merge-base --is-ancestor $C origin/main` (Run I's code commit is still published; the record checker repeats this for every code commit); `cd $A && sha256sum -c arms_t0_<YYYYMMDD>/a3/SHA256SUMS` passes; the directory is still read-only. If `r1/c3/arms_freeze.py` differs between `$C` and `$C2` (`git -C $W2/paper diff --stat $C $C2 -- r1/c3/arms_freeze.py`), record the diff; Run I's artefacts stand (they are bound to `$C`), and Run II uses `$C2`'s checker |
| II-P3 | The same receipts still open | repeat I-P3 and I-P5's hash checks (the sweep-2 receipt note of I-P3 applies) |
| II-P4 | The author row with ARMS-A5CKPT, ARMS-A5FOLD and ARMS-SECONDARY | grep its id in `$W2/paper/docs/r1/PLAN.md` §10. **ARMS-A5CKPT C (a seed ensemble) chosen: STOP**: the checker binds each A5 entry to exactly one run of its arm pin (`a5_pin_binding`), so C needs a reviewed schema and checker change first. **ARMS-A5FOLD B (no fold A5s) chosen: STOP** until a reviewed change to `fold_analysis` lets the fold analyses run on A3 alone (`fold_input` → `B.build` computes every test series, A5 included, and refuses missing A5 predictions) **and** an author row amends FOLD-LEVELS A of R1-FOLD-DECISIONS ("both arms"). **ARMS-SECONDARY A or C chosen**: the same or another author row must state the amendment of PRE-SECONDARY A it makes (dropping TabPFN rows, or A4 and TabPFN); without that statement: STOP |
| II-P5 | P.4's A5-family arms are sealed | for each arm ARMS-SECONDARY and ARMS-A5FOLD require (A5, the other Kev base, the Qwen controls, the A5 fold arms): its arm pin (`trackp_p4_arm_pin/v2`), the `best/` checkpoint tree and `temperature.json` of the run ARMS-A5CKPT names, a predictions file (`{"schema": "r1_c3_arm_predictions/v1", "predictions": {proposal_id: 12 probabilities}}`) covering every gate-source proposal including test proposals, and its PRE-SELECT A record (choice and dev value per candidate pool × base), all under `$A` and produced by a signed P.4 evidence phase whose code commit is on `main`. P.4 phase 1 (readiness, sweep 1 only) does not produce these. Missing: STOP |
| II-P6 | The delivery worktree | `git -C $W2/paper worktree add $W2/deliver -b ops-arms-frozen-<YYYYMMDD> $C2`; every Run II command below runs from `$W2/deliver` (the record is written there; `$W2/paper` stays untouched) |

### II.2 Step 4 — A5-family entries from P.4 **[WAITS: ARMS-A5CKPT, ARMS-A5FOLD, ARMS-SECONDARY]**

For each A5-family arm write an entry (paths relative to `$A`):

```
{"role": "primary" | "secondary" | "fold", "code_commit": "<P.4 code commit on main>",
 "checkpoint": {"path": "trackp_p4/<run>/…/best", "sha256": "<the pin run's best_tree_sha256>"},
 "calibration": {"path": "trackp_p4/<run>/…/best/temperature.json", "sha256": "<the pin run's temperature_sha256>"},
 "predictions": {"path": "…", "sha256": "…"}, "p4_arm_pin": {"path": "…", "sha256": "…"},
 "preselect": {"choice": "<pool/base>", "dev_values": {"<pool/base>": <dev value>, …}}}
```

Check each predictions file covers every gate-source proposal id and passes the builder's validation:

```
$PY -c "import json,sys; from pathlib import Path; from r1.c3 import gate_input_builder as B; from r1.c3.dataset import load_table; rows=load_table(Path(sys.argv[2])); P=json.load(open(sys.argv[1]))['predictions']; assert set(P)=={r['proposal_id'] for r in rows}; B._rule_layer([P[r['proposal_id']] for r in rows], rows); print('ok', len(P))" <predictions> $T2
```

(for the main and secondary arms; a fold arm covers its held-out nodes' rows only). Failure: STOP.

### II.3 Step 5 — write and check the record **[WAITS: every decision of I-P8 and II-P4]**

Assemble `$W2/record.json` (no label value enters it):

| Field | Source |
|---|---|
| `schema` | `r1_c3_arms_frozen/v1` |
| `preregistration`, `gate`, `gate_input_builder`, `split_file`, `noise_source` | `{path, sha256}` of the committed files (the checker requires the preregistration's bound values) |
| `g1b_summaries` | `{node: {path, sha256}}` from the T1 release receipt's `g1b_summaries` (committed repository files; the checker re-hashes them in the checkout); `{}` if T0-only |
| `t0_nodes` | the I-P9 set |
| `t1` | `{"suites", "modes", "d3_k6", "instances"}`: `$W/t1.json` plus the frozen T1 instance ids (every T1 instance supplied, from the G.5 table; each node with a train and a dev instance); `{"suites": {}, "modes": [], "d3_k6": false, "instances": []}` if T0-only |
| `label_tables` | per source (`sweep1`, `sweep2`, and `g5` if T1): `label_block_sha256` = receipt `inputs.label_block_sha256`, `traindev_partition_sha256` = receipt `outputs.label_block.traindev.jsonl`, `receipt_sha256`, `proposals_sha256` = receipt `inputs.proposals_sha256` |
| `feature_tables` | `{"featurizer": "c3_features/v3", "sweep1": {"sealed_proposals_sha256", "arms_proposals_sha256", "identity_check": <the whole identity JSON of step 2>}, "sweep2": {"proposals_sha256"}, ["g5": {...}]}` |
| `arms` | `a3/entries.json` merged with the A5-family entries of step 4 and the secondary entries ARMS-SECONDARY names (the checker requires each A3 entry's `inputs` to equal `label_tables` and `feature_tables`) |
| `fold_arms` | `{"A3": "built", "A5": "built" or "not_built:<author row id>"}` (ARMS-A5FOLD; `not_built` only after II-P4's conditions) |
| `secondary_arms` | the arm names ARMS-SECONDARY declares (e.g. `A5-kev-4b`, `A5-qwen3.5-0.8b-base`, `A5-qwen3.5-4b-base`, `A4`) |
| `decisions` | `{decision id: author row id}` for the ten ids of the readiness report §3 |
| `disclosures` | `{"trackp_sft_v1": …, "exam_set": …}`: the earlier engineering uses of sweep-1 data on P3 test instances (Track P SFT on `trackp_sft/v1`) and the P.3b exam set's provenance (R1-P3B-EXAM-DECISIONS), each citing its committed record; text supplied by the coordinating chat |

Then, from `$W2/deliver` (relative record path, the form the release row cites; `render` creates
`docs/r1/arms_frozen/`):

```
$PY -B -m r1.c3.arms_freeze render --json $W2/record.json --out docs/r1/arms_frozen/C3_ARMS_FROZEN_<YYYYMMDD>.md
$PY -B -m r1.c3.arms_freeze check --record docs/r1/arms_frozen/C3_ARMS_FROZEN_<YYYYMMDD>.md --artefact-root $A \
  --release-root sweep1=$R1 --release-root sweep2=$R2 [--release-root g5=$RG]
```

`render` checks the record before writing and prints its sha256. `check` re-hashes every arm artefact under `$A`,
re-hashes the receipts and partitions under the release roots, re-hashes the G.1b summaries in the checkout, binds
each A5-family entry to one run of its arm pin, and requires every code commit (`$C` for A3, P.4's for A5) to be an
ancestor of `origin/main` in this clone. Any refusal: fix the input (not the code), rerun, record both runs; a refusal
that needs a code change: STOP.

### II.4 Step 6 — deliver for the author

1. In `$W2/deliver` (branch `ops-arms-frozen-<YYYYMMDD>` from `$C2`), commit only the record and a run report
   (`docs/r1/reports/arms_frozen_<YYYYMMDD>/ARMS_FROZEN_RUN_<YYYYMMDD>.md`: both runs' commands, exit codes, stdouts
   without label values, environment versions, `$C` and `$C2`, every sha256 above, the identity result, the PRE-SELECT
   choices with dev values).
2. Deliver the branch (new branch only; never `main`). An independent review follows; the coordinating chat publishes
   the record on `main` after it.
3. **Stop there.** The test release row (R1-S2-LABELS-TEST-RELEASE, citing the record's path and sha256) is the
   author's; nothing in this runbook releases or reads a test label or an evaluation block. Once committed, the
   record is never edited; a needed change is a new record and a new author row.
