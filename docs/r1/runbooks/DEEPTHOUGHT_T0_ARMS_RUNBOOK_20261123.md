# Deepthought runbook: T0 arms on train/dev and the arms-frozen record (23 November 2026)

**Status: DRAFT, revised after independent review rounds 1 and 2, for re-review with the arms-readiness unit**
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

**Revision of 23 Nov 2026 (post-freeze reads amendment, units 1 and 2; AI-assisted, Claude, subagent; revised after
the units' review `docs/r1/reviews/POSTFREEZE_UNITS12_REVIEW_20261123.md`).** The arms-frozen record now also carries
`amendments` and `rule_arms` (amendment `docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_20261123.md`,
A§8 units 1–2, A§9).

**Order, before Run II starts** (each step complete on `main` before the next):
1. The author rows deciding ARMS-A5CKPT, ARMS-A5FOLD and ARMS-SECONDARY are on `main` (R1-ARMS-DECISIONS, on `main`
   since `89899f76`, decides all three as option A), and **every change to `r1/c3/arms_freeze.py` that they, the P.4
   evidence phase or any II-P4 remedy needs is reviewed and merged**. On the code as it stands, options A need none.
2. Units 1 and 2 are reviewed and merged; the amendment's A§13 is filled with the sha256s of the **merged**
   `r1/c3/arms_constants.py` and `r1/c3/arms_freeze.py`, set `frozen: true` with `frozen_utc` (and `signed_utc`), and
   committed on `main`. A§13 pins `arms_freeze.py`'s sha256, so any later change to `arms_freeze.py` makes `check`
   refuse the record, and a frozen amendment has no procedure for being edited.
3. Only then does Run II clone `$C2` (II-P1).

**Once the record pins the amendment, the amendment file never changes.** The checker re-hashes the committed file
against the record's pin, so any later edit, including filling the units 3–5 sha256s, makes every re-run of `check`
fail. From then on, units 3–5 are bound only by CONFIRM-type author rows (A§12 item 22's fallback), not by A§13.

**With unit 2 on `main`, no arms-frozen record can be written without the frozen, signed amendment.** `check_record`
requires `amendments` and `rule_arms`, and `render` and `check` require the committed, frozen, signed amendment. A§12
items 22 and 23 describe a record that goes ahead without units 1–2 or without the signed amendment (A1's rows and
(d), or (a)–(d), listed as omissions). With unit 2 merged, that path needs an author row **and** a reviewed change to
unit 2. This runbook waits for the amendment because R1-POSTFREEZE-READS says it is "signed … before the arms-frozen
record", and because the code then requires it. If the amendment would miss R1-ARMS-FREEZE-CUTOFF (20 Dec 2026),
return to the author well before.

What the Run II operator does differently:
1. **II-P7 (new):** the order above is complete at `$C2`: R1-POSTFREEZE-READS on PLAN, the amendment frozen and
   signed with units 1 and 2 bound. Not so: STOP.
2. **Step 4b (new), T0 only:** run the constants fitter (`python -m r1.c3.arms_constants fit`) with Run I's arms
   interpreter on the sweep-2 train/dev partition; seal its output under `$A`; write the two new fields with
   `python -m r1.c3.arms_freeze postfreeze-fields`. The record is T0-only because Run I was (`cfe59c26`, no `--t1`).
3. **Step 5:** copy the two fields of step 4b into the record unchanged. Both CLI commands now refuse to pass without
   the file checks: `render` needs `--constants-root $A`, and `check` needs `--artefact-root $A` (or
   `--constants-root`). Both always check the committed amendment; `--no-git` skips only commit ancestry.
4. **Step 6:** the run report adds the constants file's and the fitter's sha256s, the toolchain, and the amendment's
   path and sha256.
Run I is unchanged.

Steps marked **[WAITS: …]** do not start until the named author decision is in a PLAN §10 author row on `main` (the
ids of the readiness report §3). Every **STOP** ends the run: report what happened, keep all outputs, change nothing,
and return to the author through the coordinating chat.

## 0. Rules for both runs

- Read only: table `proposals.jsonl`/`configs.json`/`build.json`; the receipted train/dev partitions through
  `r1.c3.arms_freeze` or `r1.c3.arms_constants` (both call `release.traindev_labels` with the receipt sha256 pinned);
  P.4's sealed outputs; committed files. **Never** open a raw `label_block.jsonl`, any `evaluation_block*.jsonl`, any
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
`mode_group` (ARMS-TWIN B, per-mode twin groups) or `none` (A). `--calibration` and `--twin-weight` are required
arguments: type the values the author row decides. If the author row chose ARMS-LEFTOUT B, ARMS-HP B, ARMS-WDBC B,
ARMS-TWIN B-literal or C: **STOP** (a code change and review come first). Record in the run log the author row id that
decides each of ARMS-CAL, ARMS-LEFTOUT, ARMS-HP, ARMS-WDBC and ARMS-TWIN.

```
mkdir -p $A/arms_t0_<YYYYMMDD>
$PY -B -m r1.c3.arms_freeze train-a3 \
  --release-root sweep1=$R1 --receipt sweep1=$S1 --table sweep1=$T1V \
  --release-root sweep2=$R2 --receipt sweep2=de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c \
  --table sweep2=$T2 \
  --identity $W/feat_one_identity.json \
  [--release-root g5=$RG --receipt g5=$SG --table g5=<G.5 table> --t1 $W/t1.json] \
  --calibration <temperature|none> --twin-weight <mode_group|none> --folds --primary-t0 <seven|eight> \
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
- every `preselect.dev_values` finite; `code_commit` = `$C`; `toolchain` = the I-P2 versions; `twin_weight` and
  `calibration_mode` as typed;
- `cd $A && sha256sum -c` over the entries' paths passes.

Then freeze Run I's outputs, in this order:
1. copy `$W/feat_one_identity.json` to `$A/arms_t0_<YYYYMMDD>/feat_one_identity.json`;
2. write `$A/arms_t0_<YYYYMMDD>/RUN_I.md`: commands, exit codes, stdouts, `$C`, versions, every sha256, and the author
   row id deciding each of ARMS-CAL, ARMS-LEFTOUT, ARMS-HP, ARMS-WDBC and ARMS-TWIN (with the values typed for
   `--calibration` and `--twin-weight`);
3. write `$A/arms_t0_<YYYYMMDD>/SHA256SUMS` (paths relative to `$A`) covering every file under
   `arms_t0_<YYYYMMDD>/a3/`, `feat_one_identity.json` and `RUN_I.md`;
4. `chmod -R a-w $A/arms_t0_<YYYYMMDD>`.

Report to the coordinating chat. If P.4's A5 arms are not yet sealed, stop here; nothing is lost.

## Run II (resumed)

### II.1 Preconditions (any failure is a STOP)

| # | Check | How |
|---|---|---|
| II-P1 | A fresh clone of the then-current `main` | clone to `$W2/paper`; `$C2=$(git -C $W2/paper rev-parse HEAD)`; record it. All Run II commands run from a delivery worktree of this clone (II-P6) |
| II-P2 | Run I carries over | `git -C $W2/paper merge-base --is-ancestor $C origin/main` (Run I's code commit is still published; the record checker repeats this for every code commit); `cd $A && sha256sum -c arms_t0_<YYYYMMDD>/SHA256SUMS` passes (it covers the A3 artefacts, `feat_one_identity.json` and `RUN_I.md`); the directory is still read-only. If `r1/c3/arms_freeze.py` differs between `$C` and `$C2` (`git -C $W2/paper diff --stat $C $C2 -- r1/c3/arms_freeze.py`), record the diff; Run I's artefacts stand (they are bound to `$C`), and Run II uses `$C2`'s checker |
| II-P3 | The same receipts still open | repeat I-P3 and I-P5's hash checks (the sweep-2 receipt note of I-P3 applies) |
| II-P4 | The author rows | (a) **A3's decisions unchanged:** the row ids deciding ARMS-CAL, ARMS-LEFTOUT, ARMS-HP, ARMS-WDBC and ARMS-TWIN at `$C2` equal those `RUN_I.md` records, no later author row amends them, and the A3 entries' `calibration_mode` and `twin_weight` equal the values those rows decide (and `RUN_I.md` records). Any difference: STOP (A3 was built under other decisions; a rerun of Run I needs the author). (b) The row with ARMS-A5CKPT, ARMS-A5FOLD and ARMS-SECONDARY: grep its id in `$W2/paper/docs/r1/PLAN.md` §10. **ARMS-A5CKPT C (a seed ensemble) chosen: STOP**: the checker binds each A5 entry to exactly one run of its arm pin (`a5_pin_binding`), so C needs a reviewed schema and checker change first. **ARMS-A5FOLD B (no fold A5s) chosen: STOP** until a reviewed change to `fold_analysis` lets the fold analyses run on A3 alone (`fold_input` → `B.build` computes every test series, A5 included, and refuses missing A5 predictions) **and** an author row amends FOLD-LEVELS A of R1-FOLD-DECISIONS ("both arms"). **ARMS-SECONDARY A or C chosen**: the same or another author row must state the amendment of PRE-SECONDARY A it makes (dropping TabPFN rows, or A4 and TabPFN); without that statement: STOP |
| II-P5 | P.4's A5-family arms are sealed | for each arm ARMS-SECONDARY and ARMS-A5FOLD require (A5, the other Kev base, the Qwen controls, the A5 fold arms): its arm pin (`trackp_p4_arm_pin/v2`), the `best/` checkpoint tree and `temperature.json` of the run ARMS-A5CKPT names, a predictions file (`{"schema": "r1_c3_arm_predictions/v1", "predictions": {proposal_id: 12 probabilities}}`) covering every gate-source proposal including test proposals, and its PRE-SELECT A record (choice and dev value per candidate pool × base), all under `$A` and produced by a signed P.4 evidence phase whose code commit is on `main`. P.4 phase 1 (readiness, sweep 1 only) does not produce these. Missing: STOP |
| II-P6 | The delivery worktree | `git -C $W2/paper worktree add $W2/deliver -b ops-arms-frozen-<YYYYMMDD> $C2`; every Run II command below runs from `$W2/deliver` (the record is written there; `$W2/paper` stays untouched) |
| II-P7 | The post-freeze reads amendment is signed and frozen and binds units 1 and 2 at `$C2` (the order of the revision note is complete) | (a) the row R1-POSTFREEZE-READS is in a dated author table of `$W2/paper/docs/r1/PLAN.md` §10 (grep its id); (b) the signed amendment `$AM` = `docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_20261123.md` (exactly this file; never the `…_DRAFT_20261123.md` file, which the checker refuses; record `sha256sum $AM`) **ends** with its fenced final block (A§13), with nothing after the closing fence and no blank or free-text line inside it, reading: `frozen: true` (nothing after `true`); `plan_row: R1-POSTFREEZE-READS`; `amends: docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961b…d7cc5`; a `signed_by` that is not `<…>`; `signed_utc` and `frozen_utc` each in the form `YYYY-MM-DDTHH:MM[:SS]Z` (UTC with `Z`, no offset such as `+00:00`, no fraction of a second), with `signed_utc` no later than `frozen_utc`; (c) its `constants_fitter_sha256` = `sha256sum $W2/deliver/r1/c3/arms_constants.py` and its `arms_freeze_sha256` = `sha256sum $W2/deliver/r1/c3/arms_freeze.py`, each a bare 64-hex value (read the block's lines only). The `status:` line is not checked by the code, but should say at the freeze that the code sha256 fields are filled. Any of these missing or different: **STOP** — the record must not be written. With unit 2 on `main` the record checker refuses any record without the frozen, signed amendment; the path of A§12 items 22–23 (a record without it, with the losses listed as omissions) needs an author row and a reviewed change to unit 2 (revision note). Also record whether the D.3 pre-declaration is signed at `$C2` and, if so, the constants file its key block pins (`constants_file_sha256`); see step 4b for `$D3C` |

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

### II.2b Step 4b — A1/A2 constants and the post-freeze reads fields **[WAITS: II-P7]**

Unit 1 (`r1/c3/arms_constants.py`) fits A1's and A2's per-node 12-bin vectors exactly as
`gate_input_builder.fit_a2` fits A2, on the **dev** label block of the gate sources, and writes one constants file. It
reads only the receipted train/dev partition (receipt pinned) and the released table. It refuses: sweep 1; a test or
evaluation row; a table other than the one the receipt released (for sweep 2 also other than `379b17ca…97d9`); a
required node without a labelled non-inert dev proposal; a checkout whose `gate_input_builder.py` is not the one the
preregistration binds; a dirty checkout.

**T0 only.** Run I (`cfe59c26`, `A3_RUN_20261123.md`) ran without `--t1` and used no T1 rows, so the record is T0-only:
its `t1` is `{"suites": {}, "modes": [], "d3_k6": false, "instances": []}` and the fit takes sweep 2 alone, with no G.5
argument. If T1 nodes are to be frozen later, that needs the author and a new Run I (A3 trained with `--t1`, with its
`A3@loso:<suite>` folds and `g5` inputs); only then does step 4b add `--release-root g5=$RG --receipt g5=$SG
--table g5=<G.5 table> --t1 $W/t1.json` with the same `t1.json`, and the record carries the T1 nodes' vectors. A T1 fit
here on top of a T0-only Run I gives a record the checker refuses.

**Interpreter.** Steps 4b and 5 (the fitter, `postfreeze-fields`, `render` and `check`) use one interpreter, Run I's arms venv, `$PYA=/work/dwong/arms_t0_20261123/venv/bin/python3` (review R-N1; `$PY` of I-P2 is the release-step interpreter; step 4's validation line is unchanged) (CPython 3.13.15,
NumPy 2.4.4, SciPy 1.17.1; `docs/r1/reports/arms_a3_20261123/ENVIRONMENT.md`). The vectors' bits depend on NumPy and on
SciPy's `norm.cdf` (`labels.soft_label`). The constants file records `toolchain` (Python, NumPy, SciPy and this
interpreter's path), and unit 3's bitwise re-check after step 6 must run with the same versions. Another interpreter
only if the author designates it; record which and why.

From `$W2/deliver`:

```
mkdir $A/arms_rule_constants_<YYYYMMDD>
$PYA -B -m r1.c3.arms_constants fit \
  --release-root sweep2=$R2 --receipt sweep2=de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c \
  --table sweep2=$T2 \
  --out $A/arms_rule_constants_<YYYYMMDD>/C3_RULE_ARM_CONSTANTS_<YYYYMMDD>.json
```

Expected:
- exit 0;
- the printed `nodes` are exactly the eight T0 nodes;
- `code_commit` = `$C2`;
- `fitter_sha256` = the amendment's `constants_fitter_sha256` (II-P7);
- `toolchain` = Python 3.13.15, NumPy 2.4.4, SciPy 1.17.1, interpreter `$PYA` (or the designated one).

Record the printed `sha256` and `toolchain`. The file holds the per-node vectors (means of released dev soft labels;
they enter the record by A§9): do not print them into the run log. Any refusal (`ArmsFreezeError`, `ReleaseStop`):
**STOP**.

**D.3 constants file (`$D3C`).** If the D.3 pre-declaration is signed at `$C2` and pins a constants file, that file is
an earlier one: step 4b's file does not exist before this step. Copy it into `$A/arms_rule_constants_<YYYYMMDD>/`
before sealing, check that its sha256 equals the D.3 key block's `constants_file_sha256`, and let `$D3C` be its path
relative to `$A`. The checker compares only the seven D.3 nodes' A1 and A2 vectors, bit for bit, not the file bytes;
the bytes differ whenever its `fitter.code_commit` or `toolchain` differs. If D.3 is not signed, there is no `$D3C`.

Then seal: `cd $A && sha256sum arms_rule_constants_<YYYYMMDD>/* > arms_rule_constants_<YYYYMMDD>/SHA256SUMS &&
chmod -R a-w arms_rule_constants_<YYYYMMDD>`.

Write the two record fields. The command re-reads the constants file and reads the committed amendment. It refuses
unless the amendment is committed, frozen and signed, cites R1-POSTFREEZE-READS on PLAN, and binds this fitter (also
checked against its code commit) and this `arms_freeze.py`:

```
$PYA -B -m r1.c3.arms_freeze postfreeze-fields --constants-root $A \
  --constants arms_rule_constants_<YYYYMMDD>/C3_RULE_ARM_CONSTANTS_<YYYYMMDD>.json \
  --amendment $AM [--d3-constants $D3C] --out $W2/postfreeze_fields.json
```

Pass `--d3-constants $D3C` only if there is one; otherwise `rule_arms.d3_constants` is null, and the D.3
pre-declaration must later pin vectors equal to the record's for its seven nodes (A§9). A D.3 file whose seven nodes'
vectors differ from this step's in any bit is refused: **STOP**. Record the printed sha256s.

### II.3 Step 5 — write and check the record **[WAITS: every decision of I-P8 and II-P4]**

Assemble `$W2/record.json` (no individual label value enters it; the per-node A1/A2 vectors of step 4b, which are
means of released dev soft labels, enter `rule_arms` as the amendment's A§9 requires):

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
| `decisions` | `{decision id: author row id}` for the ten ids of the readiness report §3 (the five A3 ids as `RUN_I.md` records them) |
| `a3_settings` | `{"calibration": …, "twin_weight": …}`: the values typed in step 3 (the checker requires every A3-family entry to match) |
| `disclosures` | `{"trackp_sft_v1": …, "exam_set": …}`: the earlier engineering uses of sweep-1 data on P3 test instances (Track P SFT on `trackp_sft/v1`) and the P.3b exam set's provenance (R1-P3B-EXAM-DECISIONS), each citing its committed record; text supplied by the coordinating chat |
| `amendments`, `rule_arms` | the two keys of `$W2/postfreeze_fields.json` (step 4b), copied unchanged (e.g. `$PYA -c "import json,sys; r=json.load(open(sys.argv[1])); f=json.load(open(sys.argv[2])); assert not set(f) & set(r); r.update(f); json.dump(r, open(sys.argv[1], 'w'), indent=1, sort_keys=True)" $W2/record.json $W2/postfreeze_fields.json`). Do not edit them: the checker compares every vector bit with the constants file. `arms` stays as above: A0 and A1 are not arms of the record |

Then, from `$W2/deliver` (relative record path, the form the release row cites; `render` creates
`docs/r1/arms_frozen/`):

```
$PYA -B -m r1.c3.arms_freeze render --json $W2/record.json --constants-root $A \
  --out docs/r1/arms_frozen/C3_ARMS_FROZEN_<YYYYMMDD>.md
$PYA -B -m r1.c3.arms_freeze check --record docs/r1/arms_frozen/C3_ARMS_FROZEN_<YYYYMMDD>.md --artefact-root $A \
  --release-root sweep1=$R1 --release-root sweep2=$R2
```

(T0-only record, step 4b; with a T1 record, after a new Run I, `check` also takes `--release-root g5=$RG`.)

`render` checks the record before writing and prints its sha256. `check` re-hashes every arm artefact under `$A`,
re-hashes the receipts and partitions under the release roots, re-hashes the G.1b summaries in the checkout, binds
each A5-family entry to one run of its arm pin, and requires every code commit (`$C` for A3, P.4's for A5, `$C2` for
the constants fitter) to be an ancestor of `origin/main` in this clone.

For the post-freeze reads fields, both commands do the following:
- require R1-POSTFREEZE-READS on PLAN;
- require the committed, frozen, signed amendment binding this checkout's committed `arms_freeze.py` and the record's
  fitter, whose sha256 is also checked at its code commit;
- with `--constants-root $A` (`check`: by default `--artefact-root`), re-hash the constants file (and the D.3 constants
  file) and compare every vector bit, the builder pin, the receipts, partitions and tables of the fit with the record,
  and the T1 nodes' dev instances with `t1.instances`.

Both commands **refuse** a record with these fields if they cannot run both file checks: `render` without
`--constants-root`, `check` without `--artefact-root` or `--constants-root`. The committed-amendment check has no
opt-out: `--no-git` skips only the commit-ancestry check, and this runbook does not use it. Expected in `check`'s
summary: `constants_files_rehashed` 1 (2 with a D.3 constants file) and `amendments_rehashed` 1. Any refusal: fix the
input (not the code), rerun, record both runs; a refusal that needs a code change: STOP.

### II.4 Step 6 — deliver for the author

1. In `$W2/deliver` (branch `ops-arms-frozen-<YYYYMMDD>` from `$C2`), commit only the record and a run report
   (`docs/r1/reports/arms_frozen_<YYYYMMDD>/ARMS_FROZEN_RUN_<YYYYMMDD>.md`: both runs' commands, exit codes, stdouts
   without label values, environment versions, `$C` and `$C2`, every sha256 above, the identity result, the PRE-SELECT
   choices with dev values, and for step 4b the constants file's path and sha256, the fitter's sha256, the constants
   file's `toolchain`, the amendment's path and sha256, and whether `rule_arms.d3_constants` is pinned or null).
2. Deliver the branch (new branch only; never `main`). An independent review follows; the coordinating chat publishes
   the record on `main` after it.
3. **Stop there.** The test release row (R1-S2-LABELS-TEST-RELEASE, citing the record's path and sha256) is the
   author's; nothing in this runbook releases or reads a test label or an evaluation block. Once committed, the
   record is never edited; a needed change is a new record and a new author row.
