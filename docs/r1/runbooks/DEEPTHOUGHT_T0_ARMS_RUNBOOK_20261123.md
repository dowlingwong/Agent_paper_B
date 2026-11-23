# Deepthought runbook: T0 arms on train/dev and the arms-frozen record (23 November 2026)

**Status: DRAFT, for independent review with the arms-readiness unit** (`mac-t0-arms-readiness-20261123`; report
`docs/r1/reports/arms_readiness_20261123/T0_ARMS_READINESS_20261123.md`). Written by the Mac-desk agent (Claude),
AI-assisted. ENGINEERING_ONLY until the record is committed.

**Who and what.** The cluster agent on deepthought. It re-derives the sweep-1 v3 arms table and runs the FEAT-ONE
identity check, trains, selects and calibrates A3 and the fold A3s on train/dev labels, collects the A5 entries from
P.4, writes and checks the arms-frozen record (preregistration §4 step 4), and delivers it on a new branch for the
author. **The test release row comes only after the author**; this runbook never releases, opens or reads a test
label or an evaluation block.

Steps marked **[WAITS: …]** do not start until the named author decision is in a PLAN §10 author row on `main`
(the decision ids are those of the readiness report §3). Every **STOP** ends the run: report what happened, keep all
outputs, change nothing, and return to the author through the coordinating chat.

## 0. Rules for the whole run

- Read only: table `proposals.jsonl`/`configs.json`/`build.json`, the receipted train/dev partitions through
  `r1.c3.arms_freeze` (which calls `release.traindev_labels` with the receipt sha256 pinned), P.4's sealed outputs, and
  committed files. **Never** open a raw `label_block.jsonl`, any `evaluation_block*.jsonl`, any `label_block.test.jsonl`,
  a `runs.jsonl`, or a `test/` release partition; never run `r1.c3.release --stage test`; never print or copy a label
  value. A deliberate read of any of these is a STOP (§6 of the preregistration).
- Nothing is trained, tuned or selected on test or on any evaluation seed (7006–7010).
- One clean checkout at one published commit for the whole run; `git status --porcelain --untracked-files=no` empty
  before every step; no edit to any tracked file.
- Environment, every command: `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
  NUMEXPR_NUM_THREADS=1`, interpreter `$PY` (P2). Record every command, its exit code and its stdout in the run log.
- Outputs go to a new work directory `$W=/work/dwong/arms_t0_<YYYYMMDD>/` and the sealed artefact root
  `$A=/ceph/srv/dwong/paperb/` (the run writes a new `$A/arms_t0_<YYYYMMDD>/`); existing directories are never reused.
- Never push to `main`; deliver on a new branch only.

## 1. Preconditions (all must hold; any failure is a STOP)

| # | Check | How |
|---|---|---|
| P1 | `r1/c3/arms_freeze.py` is on published `main` (this unit reviewed and merged) | clone `origin/main` to `$W/paper`; `git -C $W/paper rev-parse HEAD` = `$C`; `git merge-base --is-ancestor $C origin/main`; record `$C` |
| P2 | Interpreter with numpy, scipy, scikit-learn and LightGBM | `$PY=/ceph/dwong/r1_prepare_20261025/venv/bin/python3` (the release step's); `$PY -c "import numpy, scipy, sklearn, lightgbm; print(numpy.__version__, scipy.__version__, sklearn.__version__, lightgbm.__version__)"`; record the versions. **LightGBM absent: STOP** (the author decides whether it enters that venv or a separate one; do not install into a shared venv on your own) |
| P3 | The sweep-2 train/dev receipt | `$R2=/work/dwong/s2_release_20261122/release_sweep2_traindev_v2`; `sha256sum $R2/sweep2/traindev/RECEIPT.json` = `de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c` (= `docs/r1/reports/release_20261122/RECEIPT_sweep2_traindev_v2.json`); receipt `outputs.label_block.traindev.jsonl` = `7487b627e40edae37022f4467a60867b09bdbd395e61caa20302c090d8e5fe82`, `inputs.proposals_sha256` = `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9`, `counts.evaluation_rows` = 0 (read the receipt's JSON fields only) |
| P4 | The sweep-2 table the receipt released | `$T2=/work/dwong/s2_audit_20261122/table`; `sha256sum $T2/proposals.jsonl` = `379b17ca…97d9` |
| P5 | The sweep-1 train/dev receipt **after the unit-1 fix** (R1-SWEEP1-RELEASE-COMPAT), with its release report committed on `main` | `$R1=<the release root that report names>`; `sha256sum $R1/sweep1/traindev/RECEIPT.json` = the sha256 in that report (`$S1`); receipt `inputs.proposals_sha256` = `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4`, `inputs.label_block_sha256` = `cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca`, `counts.evaluation_rows` = 0. **No such report on `main`: STOP** (do not run the release yourself under this runbook) |
| P6 | The sealed sweep-1 table | `$T1S=/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table`; `sha256sum $T1S/proposals.jsonl` = `b713c423…57c4`, `$T1S/configs.json` = `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df` |
| P7 | The author row with the readiness decisions (FEAT-ONE, ARMS-CAL, ARMS-HP, ARMS-WDBC, ARMS-TWIN, ARMS-T1FEAT, ARMS-A5CKPT, ARMS-A5FOLD, ARMS-SECONDARY) | grep the row id in `$W/paper/docs/r1/PLAN.md` §10; record which decisions it covers. Steps below wait on the ones they name |
| P8 | The primary T0 set | the C3b result at the launch commit (seven nodes without `openml_wdbc`, or all eight if the C3b rerun gave 8/8), from its committed record; record it as `seven` or `eight` |
| P9 | T1 (only if ARMS-T1FEAT A and T1 labels exist) | the R1-T1-LABELS-UNSEAL receipt (`$RG`, sha `$SG`) with its G.1b summaries, the G.5 table with features, the frozen T1 setting `$W/t1.json` = `{"suites": {...}, "modes": [...], "d3_k6": false}`. Otherwise the read is T0-only and `--t1` is omitted |

## 2. Step 1 — re-derive the sweep-1 v3 arms table **[WAITS: FEAT-ONE]**

Only under FEAT-ONE A. (Under C or D this runbook needs a revision first: STOP.)

1. Read the sealed table's `build.json` (metadata only) and record its `sweep_index`, `classification` and noise
   source fields.
2. From `$W/paper`, with `AR_HARNESS_ROOT` the audited harness of the sweep-1 B.2 audit (as the diagnosis replay):

   ```
   $PY -B -m r1.c3.dataset build-sweep \
     --index results/r1/pilot/C3_sweep_index_20261028T033315Z.json \
     --classification results/r1/evidence/C3_sweep_classification_20261028.json \
     --paper-root <the paper root that holds the sweep-1 source directories the index names> \
     --out $W/tables/sweep1_v3_arms
   ```

   with the same noise-source argument the sealed `build.json` records (none if it records the default).
3. Check: `sha256sum $W/tables/sweep1_v3_arms/proposals.jsonl` = `d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5`
   (the diagnosis replay; the `sweep1_v3` pin in `r1/scripts/configs/trackp_sft.json`) and `configs.json` =
   `b585b727…82df`. **Any other value: STOP** (do not fall back to the W2.3 table).

## 3. Step 2 — FEAT-ONE identity check **[WAITS: FEAT-ONE]**

```
$PY -B -m r1.c3.arms_freeze identity --sealed $T1S --arms-table $W/tables/sweep1_v3_arms \
  --out $W/feat_one_identity.json
```

Expected: exit 0; `pass` true; `n_sealed` 4999; `keys_equal` and `configs_equal` true; `n_other_differences` 0;
`n_budget_frac_left_differ` **116** (the diagnosis' count); `sealed_proposals_sha256` = `b713c423…57c4`,
`arms_proposals_sha256` = `d0048567…d1d5`. Exit 3 or any other value: **STOP** (a pass with a count other than 116 is
also a STOP: the inputs are the ones the diagnosis compared). Record `sha256sum $W/feat_one_identity.json`.

## 4. Step 3 — A3 and the fold A3s **[WAITS: ARMS-CAL, ARMS-HP, ARMS-WDBC, ARMS-TWIN; ARMS-T1FEAT if T1]**

The code implements the recommended options (calibration `temperature`, `LGBMPrior` defaults, all T0 nodes in
training and selection, pooled = the union). If the author row chose otherwise for ARMS-HP, ARMS-WDBC or ARMS-TWIN:
STOP (a code change and review come first). ARMS-CAL B is `--calibration none`.

```
mkdir -p $A/arms_t0_<YYYYMMDD>
$PY -B -m r1.c3.arms_freeze train-a3 \
  --release-root sweep1=$R1 --receipt sweep1=$S1 --table sweep1=$W/tables/sweep1_v3_arms \
  --release-root sweep2=$R2 --receipt sweep2=de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c \
  --table sweep2=$T2 \
  --identity $W/feat_one_identity.json \
  [--release-root g5=$RG --receipt g5=$SG --table g5=<G.5 table> --t1 $W/t1.json] \
  --calibration temperature --folds --primary-t0 <seven|eight> \
  --artefact-root $A --out $A/arms_t0_<YYYYMMDD>/a3
```

It refuses (exit non-zero, `ArmsFreezeError` or `ReleaseStop`) on: a receipt other than the pinned one; a partition
that fails `release.open_partition`'s checks; a test label or evaluation field; a sweep-2 table other than the one
released; a sweep-1 table that is not the v3 arms table of a passing identity check against the released sealed table;
a row without the full feature set; a dirty checkout. **Any refusal: STOP.**

Checks on the output (`entries.json`, `selection.json` per arm; no label values are in them):
- arms `A3` and one `A3@lono:<node>` per primary T0 node (plus `A3@loso:<suite>` per suite of the frozen T1 set);
- `A3.n_predictions` = the number of rows in `$T2/proposals.jsonl` (plus the G.5 rows if T1); each fold arm's
  `n_predictions` = the held-out nodes' gate-source rows;
- every `preselect.dev_values` finite; `code_commit` = `$C`;
- `cd $A && sha256sum -c` over the entries' paths passes. Write `$A/arms_t0_<YYYYMMDD>/a3/SHA256SUMS` and make the
  directory read-only (`chmod -R a-w`).

## 5. Step 4 — A5 entries from P.4 **[WAITS: the P.4 evidence phase, ARMS-A5CKPT, ARMS-A5FOLD, ARMS-SECONDARY]**

P.4 phase 1 is readiness only and trains on sweep 1 only; it does not produce A5 evidence arms. This step runs when a
signed P.4 evidence phase has sealed, per A5-family arm (A5, the other Kev base, the Qwen controls, and the A5 fold
arms under ARMS-A5FOLD A): its arm pin (`trackp_p4_arm_pin/v2`), the `best/` checkpoint tree and `temperature.json`
of the run ARMS-A5CKPT names, a predictions file (`{"schema": "r1_c3_arm_predictions/v1", "predictions": {proposal_id:
12 probabilities}}`) covering every gate-source proposal including test proposals, and its PRE-SELECT A record
(choice and dev value per candidate pool × base). Until then: **STOP here** (steps 1–3 stand; nothing is lost).

For each A5-family arm write an entry (paths relative to `$A`):

```
{"role": "primary" | "secondary" | "fold", "code_commit": "<P.4 code commit on main>",
 "checkpoint": {"path": "trackp_p4/<run>/…/best", "sha256": "<the pin run's best_tree_sha256>"},
 "calibration": {"path": "trackp_p4/<run>/…/best/temperature.json", "sha256": "<the pin run's temperature_sha256>"},
 "predictions": {"path": "…", "sha256": "…"}, "p4_arm_pin": {"path": "…", "sha256": "…"},
 "preselect": {"choice": "<pool/base>", "dev_values": {"<pool/base>": <dev value>, …}}}
```

Check each predictions file covers every gate-source proposal id and passes the builder's validation:
`$PY -c "import json,sys; from r1.c3 import gate_input_builder as B; from r1.c3.dataset import load_table; from pathlib import Path; rows=load_table(Path(sys.argv[2])); P=json.load(open(sys.argv[1]))['predictions']; assert set(P)=={r['proposal_id'] for r in rows}; B._rule_layer([P[r['proposal_id']] for r in rows], rows); print('ok', len(P))" <predictions> $T2`
(for the main and secondary arms; a fold arm covers its held-out nodes' rows only). Failure: STOP.

## 6. Step 5 — write and check the record **[WAITS: every decision of P7]**

Assemble `$W/record.json` (no label value enters it):

| Field | Source |
|---|---|
| `schema` | `r1_c3_arms_frozen/v1` |
| `preregistration`, `gate`, `gate_input_builder`, `split_file`, `noise_source` | `{path, sha256}` of the committed files at `$C` (the checker requires the preregistration's bound values) |
| `g1b_summaries` | `{node: {path, sha256}}` from the T1 release receipt's `g1b_summaries`; `{}` if T0-only |
| `t0_nodes` | the P8 set |
| `t1` | `$W/t1.json`, or `{"suites": {}, "modes": [], "d3_k6": false}` if T0-only |
| `label_tables` | per source (`sweep1`, `sweep2`, and `g5` if T1): `label_block_sha256` = receipt `inputs.label_block_sha256`, `traindev_partition_sha256` = receipt `outputs`, `receipt_sha256`, `proposals_sha256` = receipt `inputs.proposals_sha256` |
| `feature_tables` | `{"featurizer": "c3_features/v3", "sweep1": {"sealed_proposals_sha256", "arms_proposals_sha256", "identity_check": <the whole identity JSON>}, "sweep2": {"proposals_sha256"}, ["g5": {...}]}` |
| `arms` | `a3/entries.json` merged with the A5-family entries of step 4 and the secondary entries ARMS-SECONDARY names |
| `fold_arms` | `{"A3": "built", "A5": "built" or "not_built:<author row id>"}` (ARMS-A5FOLD) |
| `secondary_arms` | the arm names ARMS-SECONDARY declares (e.g. `A5-kev-4b`, `A5-qwen3.5-0.8b-base`, `A5-qwen3.5-4b-base`, `A4`) |
| `decisions` | `{decision id: author row id}` for the nine ids of P7 |
| `disclosures` | `{"trackp_sft_v1": …, "exam_set": …}`: the earlier engineering uses of sweep-1 data on P3 test instances (Track P SFT on `trackp_sft/v1`) and the P.3b exam set's provenance (R1-P3B-EXAM-DECISIONS), each citing its committed record; text supplied by the coordinating chat |

Then, from `$W/paper` (relative record path, as the release row cites it):

```
$PY -B -m r1.c3.arms_freeze render --json $W/record.json --out docs/r1/arms_frozen/C3_ARMS_FROZEN_<YYYYMMDD>.md
$PY -B -m r1.c3.arms_freeze check --record docs/r1/arms_frozen/C3_ARMS_FROZEN_<YYYYMMDD>.md --artefact-root $A
```

`render` checks the record before writing and prints its sha256; `check` re-hashes every artefact under `$A`, binds
each A5-family entry to one run of its arm pin, and requires every code commit to be an ancestor of `origin/main`.
Any refusal: fix the input (not the code), rerun, and record both runs; a refusal that needs a code change: STOP.

## 7. Step 6 — deliver for the author

1. On a new branch `ops-arms-frozen-<YYYYMMDD>` from `$C`: commit only the record and a run report
   (`docs/r1/reports/arms_frozen_<YYYYMMDD>/ARMS_FROZEN_RUN_<YYYYMMDD>.md`: commands, exit codes, stdouts without label
   values, environment versions, every sha256 above, the identity result, the PRE-SELECT choices with dev values).
   The working copy of `$W/paper` used for the run stays as it was (commit from a separate worktree).
2. Deliver the branch (new branch only; never `main`). An independent review follows; the coordinating chat publishes
   the record on `main` after it.
3. **Stop there.** The test release row (R1-S2-LABELS-TEST-RELEASE, citing the record's path and sha256) is the
   author's; nothing in this runbook releases or reads a test label or an evaluation block. Once committed, the
   record is never edited; a needed change is a new record and a new author row.
