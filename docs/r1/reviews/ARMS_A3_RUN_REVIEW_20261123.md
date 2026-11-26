# Independent review — T0 arms Run I, A3 only (23 November 2026)

Reviewer: `reviewer-arms-a3`, independent and read-only. Review time 2026-11-23 ≈14:24–14:33 CET.

**Scope.** Branch `ops-arms-a3-20261123` @ `99693214` (parent `89899f76`, published `main` at branch
creation and remote `main` tip at review time), its seven added files under `docs/r1/reports/arms_a3_20261123/`,
the sealed artefact root `/ceph/srv/dwong/paperb/arms_t0_20261123/` on `deepthought.etp.kit.edu` (ceph,
read-only), `docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md` Run I (§0, I.1–I.4) and the authority
row `R1-ARMS-DECISIONS` in `docs/r1/PLAN.md` §10 at `89899f76`.

**Method.** Read-only `ssh` commands on deepthought (`sha256sum`, `sha256sum -c`, `stat`, `find`, `ls`, `cat`,
`python3` stdlib) and local read-only git (`show`, `rev-parse`, `diff`, `cat-file`, `ls-tree`). No job was
submitted, held, edited or removed; nothing was written under `/work` or `/ceph`. The only write is this review
file; the independent identity re-run wrote one `/tmp` file on deepthought (`/tmp/review_identity_*.json`), which
was hashed, compared and deleted immediately. No test label and no evaluation value was printed; the two
receipted train/dev partitions were read programmatically only to count P3 split membership (aggregate counts,
no field values).

## Bottom line

**ACCEPTED.** All six checks pass: (1) the A3 run used a new separate venv with the recorded exact versions and
the recorded `pip freeze` sha256, and the shared B.2/audit venv is untouched; (2) the FEAT-ONE identity check
exits 0, passes, 4,999 vs 4,999 keys, 116 `budget_frac_left` differences, 0 other differences — and I
independently re-ran the identical command and reproduced its output byte for byte (sha256 `039b8360…`); (3) the
sealed `a3/entries.json` holds exactly 8 entries (A3 + 7 leave-one-node-out), all `sweep2_only`, all dev values
finite, `temperature` / `mode_group` / `code_commit 89899f76` / the recorded toolchain on every entry, no T1 row,
and every entry's pinned files re-hash to the sealed `SHA256SUMS`; (4) the sealed root verifies `sha256sum -c`
clean (47 entries, 0 failures), is read-only, and contains no A5 entry, no arms-frozen record and no test-release
artefact; (5) nothing in the sealed outputs or the report carries a label or evaluation value, and the release
locks plus the partitions themselves (train/dev rows only) show no evidence of opening a test or evaluation file;
(6) the report's numbers are accurate, the branch is clean and pushed exactly at the reported commit, and it is
one fast-forward commit ahead of `main`. Five minor, non-material documentation notes follow; none changes the
verdict. **`VERDICT: ACCEPTED`.**

## 1. Environment — verified

| Check | Claimed / expected | Independently found |
|---|---|---|
| Venv path | `/work/dwong/arms_t0_20261123/venv` | exists; created 2026-11-23 14:15:56 CET, before the run |
| Base interpreter | CPython 3.13.15 | `pyvenv.cfg`: `home = /ceph/dwong/r1_prepare_20261025/python/cpython-3.13.15-linux-x86_64-gnu/bin`, `include-system-site-packages = false`, `version = 3.13.15`; that base `python3.13` exists (Oct 25) |
| Python / NumPy / SciPy / sklearn / LightGBM | 3.13.15 / 2.4.4 / 1.17.1 / 1.8.0 / 4.7.0 | `venv/bin/python3 -c …` returns exactly `3.13.15 2.4.4 1.17.1 1.8.0 4.7.0` |
| `pip freeze` | 8 lines, sha256 `e5363669…d685a5` | live `venv/bin/python3 -m pip freeze` = 8 lines, sha256 `e536366970176cddbc297b23bcf13601f39a55bac4695b1f9fabe23f66d685a5` — identical to the sealed/committed `ENVIRONMENT_pip_freeze.txt` (same hash) |
| Shared B.2/audit venv untouched | `/ceph/dwong/r1_prepare_20261025/venv` not modified | no file under it is newer than 2026-11-20; newest mtime is 2026-10-27 14:49. The arms venv is a separate directory created on 23 Nov; the shared venv was not written |
| Environment record | `ENVIRONMENT.md` + freeze copy present | present in the sealed root, in the branch copies, and both are covered by the sealed `SHA256SUMS` |
| Entry toolchain | python 3.13.15 / numpy 2.4.4 / lightgbm 4.7.0 | every one of the 8 entries records exactly this |

I also confirmed the A3 run's only interpreter use is the new venv (`pyvenv.cfg` records
`…/python3.13 -m venv /work/dwong/arms_t0_20261123/venv`), so "separate venv" is literal, not a symlink into the
shared B.2 environment.

## 2. FEAT-ONE identity — verified and independently reproduced

Inputs measured on disk (independently of the report):

| Input | Expected (runbook I-P3/I-P5/I-P7, `trackp_sft.json`) | Measured |
|---|---|---|
| Sealed B.2 table `proposals.jsonl` | `b713c423…57c4` | `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4` |
| Sealed B.2 table `configs.json` | `b585b727…82df` | `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df` |
| Pinned sweep-1 v3 arms table `proposals.jsonl` | `d0048567…d1d5` | `d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5` |
| Pinned sweep-1 v3 arms table `configs.json` | `b585b727…82df` | `b585b727…82df` (same as sealed) |
| sweep-1 v3 `build.json` (recorded, not a STOP) | `7f56619c…b643` | `7f56619c2cc5ef2145ace44350baac3bc7906433e279a284e9627a2452e1b643` |
| sweep-1 train/dev receipt / partition | `f06e37a9…b665c1` / `6a6327a3…7b2a` | both match |
| sweep-2 train/dev receipt / partition | `de95b218…2d9c` / `7487b627…fe82` | both match |
| sweep-2 table `proposals.jsonl` | `379b17ca…97d9` | matches |
| Receipts: stage / `counts.evaluation_rows` | `traindev` / 0 | both receipts: `stage=traindev`, `counts.evaluation_rows=0`, `released_label_rows` 869 (sweep 1) / 1272 (sweep 2) |

I re-ran the exact I.3 command from `/work/dwong/arms_t0_20261123/paper` (clean clone at `89899f76`) with the A3
venv and `PYTHONDONTWRITEBYTECODE=1 OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1`, writing only a `/tmp` scratch file:

```text
stdout: {"pass": true, "n_sealed": 4999, "n_budget_frac_left_differ": 116, "n_other_differences": 0,
         "keys_equal": true, "configs_equal": true}
exit=0
sha256(/tmp scratch) = 039b8360e293f44632e6a55bff79d32f2b4769045c112cfa4d54a596564853df
diff(scratch, sealed feat_one_identity.json) = identical
```

So `pass=true`, `n_sealed=n_arms=4999`, `keys_only_sealed=keys_only_arms=0`, 116 `budget_frac_left` differences,
0 other differences, keys and configs equal; the identity file's sha256 (`039b8360…`) is exactly the value listed
for `arms_t0_20261123/feat_one_identity.json` in the sealed `SHA256SUMS`, and the branch copy has the same hash.
The identity result also binds the two distinct tables (`sealed_proposals_sha256 ≠ arms_proposals_sha256`), so it
is not a table compared with itself.

## 3. A3 and the fold A3s — verified

The sealed `a3/entries.json` (branch copy `A3_entries.json`, same sha256
`9e0efcd7598d31e1f68c365af26e0eae6132615580732370da05091e9f69d058`) contains exactly 8 entries: `A3` (role
`primary`) plus `A3@lono:<node>` for the seven primary T0 nodes `digits_mlp`, `openml_breast_w`,
`openml_climate`, `openml_credit_approval`, `openml_ionosphere`, `openml_sonar`, `tabular_mlp`. The primary T0
set of seven is the C3b result (7/8 D28-liveness nodes; `openml_wdbc` failed — recorded in
`docs/r1/reports/sweep2_20261116/S2_C3B_RUN_20261117.md`), i.e. I-P9 "seven".

| Entry | `n_predictions` | dev `pooled` / `sweep2_only` | PRE-SELECT | `temperature` | dev rows scored | trained nodes |
|---|---|---|---|---|---|---|
| `A3` | 5012 | 0.179159 / **0.217246** | sweep2_only | 1.16451 | 205 | 8 |
| `A3@lono:digits_mlp` | 684 | 0.177744 / **0.222996** | sweep2_only | 1.18865 | 186 | 7 |
| `A3@lono:openml_breast_w` | 596 | 0.187204 / **0.247889** | sweep2_only | 1.17837 | 189 | 7 |
| `A3@lono:openml_climate` | 600 | 0.251135 / **0.308635** | sweep2_only | 1.06653 | 176 | 7 |
| `A3@lono:openml_credit_approval` | 585 | 0.129995 / **0.161519** | sweep2_only | 1.20970 | 176 | 7 |
| `A3@lono:openml_ionosphere` | 610 | 0.177470 / **0.235470** | sweep2_only | 1.13429 | 182 | 7 |
| `A3@lono:openml_sonar` | 637 | 0.203633 / **0.243039** | sweep2_only | 1.20201 | 178 | 7 |
| `A3@lono:tabular_mlp` | 684 | 0.196977 / **0.217015** | sweep2_only | 1.23681 | 167 | 7 |

Checks that passed:

- **Predictions coverage.** The sweep-2 table has 5012 proposal rows; per node: `digits_mlp` 684,
  `openml_breast_w` 596, `openml_climate` 600, `openml_credit_approval` 585, `openml_ionosphere` 610,
  `openml_sonar` 637, `openml_wdbc` 616, `tabular_mlp` 684 (sum 5012). `A3.n_predictions = 5012` (all rows,
  wdbc and test proposals included); each fold's `n_predictions` equals its held-out node's row count; fold sum
  4396; all eight sum 9408 (= RUN_I.md's "total predictions 9408").
- **PRE-SELECT / ARMS-CAL A / ARMS-LEFTOUT A.** All eight choose `sweep2_only`, which is the larger dev value in
  every entry; all dev values are finite. Each `selection.json` `candidates[*].left_out` is present and empty (all
  nodes had scored dev rows and non-zero base rate), and each fold's `per_node` covers the 7 non-held-out nodes.
  Calibration is `temperature`, fitted (after PRE-SELECT) on the 11 non-inert bins over the dev population
  (`fit_rows` 205 for A3 and 167–189 for the folds), temperature in 1.0665–1.2368.
- **ARMS-HP A.** Every entry's `params` are the `r1.c3.arms.LGBMPrior` defaults (rounds 80; multiclass/12 bins;
  lr 0.05; `num_leaves` 4; `min_data_in_leaf` 5; `min_sum_hessian_in_leaf` 0.001; `lambda_l2` 1.0;
  `feature_fraction` 0.9; `bagging_fraction` 1.0; `deterministic` true; `seed` 0; `num_threads` 1) plus the
  30 featurizer column names — no grid, as decided.
- **ARMS-WDBC A / ARMS-TWIN B.** `A3.trained_nodes` is all eight T0 nodes (wdbc included, per the decision that
  the T0 node set governs evaluation only); each fold trains on the 8 minus its held-out node. Every entry has
  `twin_weight=mode_group`; the pooled variant downweights 24–34 twin rows while `sweep2_only` downweights 0, as
  the per-mode twin rule intends. Independent arithmetic: A3 `pooled.n_train_rows` 1443 = sweep-2 train 850 +
  sweep-1 train 593, and `sweep2_only.n_train_rows` 850.
- **No T1.** `inputs` on every entry are exactly `{sweep1, sweep2}`, names contain no `A3@loso:`, and no entry
  carries a `g5` input or T1 rows. This is correct for a T0-only read: there is no `R1-T1-LABELS-UNSEAL` release
  row in PLAN §10 and no G.5 release receipt under `/work` or `/ceph`, so I-P10's T1 precondition is not met and
  `--t1` was correctly omitted.
- **Code/toolchain.** Every entry: `code_commit=89899f765fc4134c05897bf079ced3ecb95314f2`;
  `toolchain={python: 3.13.15, numpy: 2.4.4, lightgbm: 4.7.0}`; `family` A3 LightGBM; `calibration_mode=temperature`;
  `twin_weight=mode_group`.
- **Consistency with the sealed files.** For all 8 arms, each of the 4 pinned files (`model.txt`, `calibration.json`,
  `predictions.json`, `selection.json`) exists, its measured sha256 equals both the entry pin and the sealed
  `SHA256SUMS` value; the per-arm `arm_entry.json` parses equal to the corresponding `entries.json`
  value; each `predictions.json` has schema `r1_c3_arm_predictions/v1`, the right arm and prediction count, and
  every value is a finite 12-vector summing to 1 (to 1e-6). `entries.json` itself is in `SHA256SUMS`
  (`9e0efcd…`) and the sealed A3 log (`logs/train_a3.log`) prints the same choice/count summary.

## 4. Sealing — verified

- Sealed root `/ceph/srv/dwong/paperb/arms_t0_20261123`: `SHA256SUMS` sha256
  `5884816200f64bdb819834ba24bd51b5a76516ee8f49c570653da2ad42b49c9b`, 47 lines; `sha256sum -c
  arms_t0_20261123/SHA256SUMS` from `/ceph/srv/dwong/paperb` exits 0 with 0 failures (all 47 OK). The branch copy
  of `SHA256SUMS` has the same sha256.
- **Coverage is exact.** The tree holds 48 files = the 47 listed + `SHA256SUMS` itself; set difference in both
  directions is empty, so every artefact file is covered and nothing is listed that does not exist. The 47 cover
  the runbook's mandatory set (41 files under `a3/` = `entries.json` + 8 arms × 5, `feat_one_identity.json`,
  `RUN_I.md`) plus `ENVIRONMENT.md`, `ENVIRONMENT_pip_freeze.txt` and the two run logs.
- **Read-only.** Every directory is `dr-xr-xr-x` and every file `-r--r--r--`; `find … -perm -u+w` returns nothing
  and `os.access(dir/file, W_OK)` is `False` for owner `dwong`, so the seal cannot be written through by the run
  user.
- **No A5 / record / test release.** No file or directory name under the sealed root matches
  `a5`, `P.4`/`p4`, `record`, `frozen` or `test`; the tree contains only the A3 run. No arms-frozen record exists
  on the branch or on `main` (`git ls-tree` finds no `arms_frozen`/`ARMS_FROZEN` path); the branch diff against
  `89899f76` is exactly seven added documentation files (978 lines) with no code, PLAN or release-row change, and
  neither release root has a `test/` partition.
- **Copies match the seal.** The six branch copies are byte-identical to the sealed files (equal sha256):
  `A3_entries.json` `9e0efcd…`, `ENVIRONMENT.md` `340813c7…`, `ENVIRONMENT_pip_freeze.txt` `e5363669…`,
  `RUN_I.md` `cd74a507…`, `SHA256SUMS` `58848162…`, `feat_one_identity.json` `039b8360…`; the `/work` run logs
  (`identity.log` `99a8028b…`, `run_i_a3.log` `3a1b069e…`) also equal their sealed copies.

## 5. Label discipline — no evidence of a test or evaluation read

What the code at `89899f76` enforces (blob `r1/c3/arms_freeze.py` sha256
`aaea25fd3f28ddd08515e5b75966f40a92db46bddd9d5060f7f921075153c72f`, identical in the run clone and in the
commit; the branch changes no code):

- input-path refusal for `label_block.jsonl`, `evaluation_block*.jsonl`, `label_block.test.jsonl`, `runs.jsonl`,
  or any path with `test` in its name/parent (`refuse_input_path`);
- released label rows only: an evaluation field, an evaluation seed (7006–7010), or a P3 **test-split** instance
  raises (`check_label_rows`); table rows carrying label/evaluation values raise (`check_table_rows`);
- labels are read only through `release.traindev_labels`, which goes through `release.open_partition` with the
  pinned receipt (`receipt_sha256` required), re-hashes the receipt and partition, checks the receipt against its
  PLAN row text, and accepts only `train`/`dev` rows in a `label_block.traindev.jsonl`; `arms_freeze` further
  requires `stage=traindev` and `counts.evaluation_rows=0`;
- training rows skip any test split and refuse a test label if one appears; predictions are model inference on
  table `features` only, and PRE-SELECT/calibration use dev rows only;
- the run is bound to a clean checkout (`_code_commit`).

What I measured (not taking the report's word):

- Both release roots contain **only** their `traindev/` partition directory (`RECEIPT.json` +
  `label_block.traindev.jsonl`); there is no `test/` partition to open in either.
- The two released train/dev partitions hold, by P3 split membership, sweep 1: 869 rows = 593 train + 276 dev;
  sweep 2: 1272 rows = 850 train + 422 dev. There are **0** test-split rows, **0** evaluation fields and **0**
  evaluation seeds in either partition. The receipts' `counts.label_rows.test` (856 / 1228) are metadata about the
  sealed label block and are not in the released partitions.
- Scanning every key path of `a3/entries.json` (440 paths over the 8 entries), all eight
  `selection.json`/`calibration.json`/`predictions.json` files, and `feat_one_identity.json` finds no
  label/target/soft/evaluation/RPS field: the only scientific results are the aggregate dev PRE-SELECT scores
  and the calibration temperatures, and the predictions files are `proposal_id → 12 calibrated probabilities`
  only; the remaining numbers are feature names, LightGBM hyper-parameters, counts and hashes.
- The recorded commands name only tables (`proposals.jsonl`/`configs.json`), receipts, the identity JSON and the
  artefact root; the sealed logs echo only the aggregate stdout; `/work/dwong/arms_t0_20261123/` contains the
  clean clone, the identity JSON, the two logs and the freeze — no test or evaluation file.
- Limitation stated plainly: there is no shell/process audit trail for the 23 Nov session (the only
  `~/.bash_history` on deepthought stops at 15 Nov and does not cover the run), so "nothing was read" rests on the
  enforced code locks plus the fact that every artefact, partition and receipt I can inspect is free of test-row
  or evaluation content. I found no evidence of a test or evaluation read and no contradiction of the report's
  claim.

## 6. Report accuracy and push readiness — verified

**Accuracy.** The report `A3_RUN_20261123.md`, its copies and `RUN_I.md`/`ENVIRONMENT.md` agree with the measured
facts on every substantive point: run from `89899f76`; separate venv and versions; `pip freeze` sha256
`e5363669…`; identity exit 0 / pass true / 4,999 keys / 116 differences / 0 other / both shas; 8 entries, all
`sweep2_only`, A3 `n_predictions=5012`, fold total 4,396 (all entries 9,408); `temperature`, `mode_group`,
`code_commit 89899f76`, toolchain; sealed `SHA256SUMS` sha `58848162…` with 47 entries, `sha256sum -c` clean and
the directory read-only; no A5, no record, no test release. The authority row `R1-ARMS-DECISIONS` (PLAN §10)
decides exactly the values typed (`ARMS-CAL A` → `temperature`, `ARMS-TWIN B` → `mode_group`, `ARMS-WDBC A` →
all eight T0 nodes in training/selection with the node set governing evaluation, so folds over the seven,
`ARMS-LEFTOUT A`, `ARMS-HP A`, `FEAT-ONE A`, `ARMS-T1FEAT A`).

**Push readiness.** In the report worktree: `HEAD = 9969321443d58e1cbfc8da07ddef5dad50bd09b1` equals
`refs/heads/ops-arms-a3-20261123` on `origin`; parent `89899f76` equals `origin/main` (still the remote main tip at
review time); before this file was added `git status --porcelain` was empty, and it now shows only this review
file as untracked (no tracked-file change, `git diff` empty); the branch adds only the seven report files (no
code, no PLAN, no other doc). The report's own "Independent review pending" line is satisfied by this file. After
this review is committed and pushed, the branch is content-complete and one fast-forward commit ahead of `main`;
I see nothing else blocking push or merge.

## Minor notes (non-blocking)

1. `RUN_I.md` line 4 carries a stray template line `Code commit C: paper` immediately above the correct
   `Code commit C: 89899f76…`. Cosmetic; the correct commit is stated and matches.
2. `A3_RUN_20261123.md` §"A3 + fold A3s" says the folds predict their held-out rows "(total 9,408 rows)".
   9,408 is the total over all eight entries (5,012 + 4,396); the folds alone are 4,396. `RUN_I.md`'s "total
   predictions 9408" is correct. Cosmetic wording.
3. `RUN_I.md` does not record the sweep-1 v3 table's `build.json` sha256 although I.2 asks for it to be recorded
   (not a STOP). I measured it on disk: `7f56619c…b643`, the expected value, so no factual error — only the record
   is missing.
4. The sealed-artefact inventories in `A3_RUN_20261123.md` and `RUN_I.md` omit the per-arm `arm_entry.json`
   (present under each `a3/<arm>/`, covered by `SHA256SUMS`, and equal to the `entries.json` value). Documentation
   completeness only.
5. The per-command thread environment (`OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`) is
   asserted in `ENVIRONMENT.md` but not echoed in the sealed logs; I could not independently evidence it. Nothing
   contradicts it, and the entries pin LightGBM's `num_threads=1`.

## Verdict

All six requested checks pass, including an independent reproduction of the FEAT-ONE identity result and a full
re-hash of the sealed root. The five notes above are documentation/wording items that affect no artefact, hash,
decision or claim.

`VERDICT: ACCEPTED`
