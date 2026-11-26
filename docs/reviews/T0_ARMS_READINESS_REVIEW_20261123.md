Reviewed base: `1402f466` (published `main`); accepted at `6e8ddaeb`, confirmed at `e5674a38c755714460ff075d221b3cbfdcaa5eac`

# Independent review record — T0 arms readiness: inventory, one featurizer (FEAT-ONE), `r1/c3/arms_freeze.py`, the deepthought T0 arms runbook and the author decisions

**Unit.** On `mac-t0-arms-readiness-20261123` over published `main` `1402f466`, four new files only: `r1/c3/arms_freeze.py` (ENGINEERING_ONLY: A3 training rows built with `gate_input_builder`'s own functions; per-node base rates; the PRE-SELECT A score and tie rule; the PRE-POOL choice on dev; calibration after selection (`--calibration temperature|none`, required); per-mode cross-source twin weighting (`--twin-weight mode_group|none`, required); prediction files for every gate-source proposal; fold A3s for leave-one-node-out and leave-one-suite-out; the FEAT-ONE identity check with the pinned v3 sweep-1 table `d0048567…` and the sealed B.2 table `b713c423…`; the arms-frozen record writer and strict checker, binding every arm's inputs to the record's label and feature tables and A5 entries to exactly one run of their P.4 arm pin), `r1/tests/test_c3_arms_freeze.py` (43, synthetic), the report `docs/r1/reports/arms_readiness_20261123/T0_ARMS_READINESS_20261123.md` (the per-arm inventory, FEAT-ONE, ten author decisions, what blocks the record) and the runbook `docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md` (Run I: A3 on train/dev; Run II: resumed on a fresh clone for A5, the decision rows and the record). No gate, builder, release, release_checks, audit or split file is changed. Authority: the frozen preregistration (`aa1a961b…`), C3_DESIGN §5, the PLAN rows named in the report; the queue of 23 Nov 2026 (01:39) for FEAT-ONE and the coordinating chat's draft queue for the unit.

**Process.** One independent reviewer, read-only, synthetic data only (no table, label block, evaluation block, sealed file or secrets file opened), scratch under `/tmp/armsrev/`. Round 1 found no blocking issue and six majors (FEAT-ONE not enforced in code; the runbook not resumable and `render` not executable; step 1's rebuild underspecified; the record not bound to the arms' inputs; the ARMS-TWIN premise incomplete against R1-MAIN-PROPOSER (e)(3); unstated code costs of two options) and seven minors. Round 2 verified those fixed and found one major (the round-1 twin grouping across memory modes lowered sweep 2's own weight in the pooled variant, and was a code default). Round 3 accepted with two report-wording minors, which the confirmation round confirmed fixed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `63a7c408` | NOT ACCEPTED (M1–M6; minors m1–m7) |
| 2 | `80ba6b83` | NOT ACCEPTED (M1-r2: twin weighting; minors m1–m3) |
| 3 | `6e8ddaeb` | ACCEPTED (wording minors m1–m2) |
| 4 | `e5674a38` | ACCEPTED (confirmation) |

**Open items.** (1) Ten author decisions in one PLAN row (report §3): FEAT-ONE (A), ARMS-CAL (temperature), ARMS-LEFTOUT (A), ARMS-HP (defaults), ARMS-WDBC (all eight T0 nodes), ARMS-TWIN (B, per-mode twin groups), ARMS-T1FEAT (A, a T1 feature unit), ARMS-A5CKPT (A, a pre-declared seed), ARMS-A5FOLD (A, build fold A5s), ARMS-SECONDARY (A; narrows PRE-SECONDARY A, an amendment to disclose); the first five gate A3. (2) The sweep-1 train/dev release must be rerun after the R1-SWEEP1-RELEASE-COMPAT fix is merged; without it there is no pooled variant. (3) A5 needs the P.4 runner merged and a P.4 evidence phase (not drafted): sweep-2-only and pooled training per base, PRE-SELECT A on dev, label-free predictions for every gate-source proposal including test, and a pinned checkpoint. (4) T1 has no featurizer (`features.NODE_INFO`/`NodeContext`); PRE-JOINT A for T1 needs ARMS-T1FEAT or a T0-only read. (5) LightGBM must be present in the deepthought environment (the runbook STOPs otherwise and installs nothing into the shared environment). (6) The disclosure items of §4 step 4 (the Track P SFT uses on `trackp_sft/v1`, the exam set's provenance) are written by the coordinating chat. (7) The cluster agent passes `--calibration` and `--twin-weight` exactly as the author row decides; the sweep-2 receipt `de95b218…` opens only while R1-S2-LABELS-TRAINDEV-RELEASE and `a9d8ff5e` are unchanged. (8) The test release row comes only after the author signs the arms-frozen record.

## Round 1 (`63a7c408`)

> Reviewed base: 63a7c40815f29bb52960213c98c3d45d066718c9 (branch `mac-t0-arms-readiness-20261123`, 3 commits on main `1402f466497c29638c53a3397f44ab9a3e6717ec`)
>
> ## Summary
> The core A3 pipeline in `r1/c3/arms_freeze.py` is correct against the preregistration. I found no data-discipline breach and no blocking findings. But some statements the unit makes to the author or the cluster agent are wrong or incomplete, and the runbook cannot be completed as written.
>
> **What matches the preregistration and the code:**
> - Training rows are built exactly as `gate_input_builder._prepare` builds them. The unit uses the builder's own `_instance`, `_label_ok`, `_seeds` and `soft_label`, and the test compares rows one by one.
> - PRE-SELECT A is implemented correctly: per-node RPS skill against the node's gate-source P3 train base rate, nodes weighted equally, on `primary_dev_population`.
> - The tie rule is correct: within 1e-9, sweep-2-only wins, then the smaller base.
> - PRE-POOL is decided on dev only.
> - Selection uses uncalibrated predictions and calibration is fitted afterwards, as §4 step 3 orders. A test shows the selection does not change with the calibration mode.
> - Predictions cover every gate-source proposal and pass `_rule_layer`, and they feed `B.build`.
> - The fold plan matches `fold_analysis` (leave-one-node-out over the primary T0 set, leave-one-suite-out over `gate.SUITES`).
> - `tree_sha256` uses the same formula as `p4_phase1.arm_pin`.
> - The record checker's gate and builder sha256 values equal the preregistration's final block (`a3f7d002…`, `f67ee5e7…`), and the record path regex equals `release.row_pattern`'s.
>
> **Data discipline:** labels are read only through `release.traindev_labels` with the receipt pinned. Test-instance labels, evaluation fields, evaluation seeds and label values in table rows are all refused, and the tests prove each refusal. Test features are used only to produce predictions, never for any choice.
>
> **Facts I checked on main:**
> - Sweep 2's table (`379b17ca…`, built at `db7f344d`) is v3: `features.py` and `dataset.py` are byte-identical between `db7f344d`, `dc9ad88a` and `1402f466`.
> - The pinned v3 sweep-1 table `d0048567…` is `sweep1_v3` in `r1/scripts/configs/trackp_sft.json`. Its `table_pin` sits in the P.4 note draft, which is on the P.4 branch only.
> - T1 nodes are absent from `features.NODE_INFO`/`NODE_CODES`, and `NodeContext` refuses them.
> - P.4 phase 1 reads only the sweep-1 partition, is readiness only, and its bootstrap uses one pooled base rate. The only test-prediction path (`sft_test_eval.replay_test_prompts`) needs test labels.
>
> Every hash in the runbook matches the committed copies (`de95b218…`, `7487b627…`, `b713c423…57c4`, `cdae9c3f…`, `b585b727…`).
>
> ## Findings
>
> ### B (blocking)
> None.
>
> ### M (major)
>
> **M1. FEAT-ONE is not enforced in code, contrary to the report.**
> - Where: `arms_freeze._train_cmd` (sweep-1 branch), `check_record` (`feature_tables.sweep1`), report §2 ("What the code does under A").
> - Problem: the report says `train-a3` refuses a sweep-1 table that is not the v3 arms table. In fact the code only requires a passing identity JSON whose arms sha equals the table and whose sealed sha equals the receipt's. The value `d0048567…` is pinned nowhere in code.
> - Failure scenario (I ran it with synthetic data): `identity --sealed $T1S --arms-table $T1S` passes with 0 differences, then `train-a3 --table sweep1=$T1S` exits 0 and trains on v2 features. Separately, a record with `arms_proposals_sha256 == sealed_proposals_sha256` passes `check_record`. The permanent record would then say `featurizer: c3_features/v3` while the pooled A3 learned v2. Today only the runbook's manual checks (step 1's sha, step 2's count of 116) stop this.
> - Fix: add a constant `SWEEP1_V3_PROPOSALS_SHA256 = "d0048567…d1d5"` and require it in `train-a3` and in `check_record`. Also require `identity_check.n_budget_frac_left_differ > 0` and arms sha ≠ sealed sha. Add a test for the self-identity case.
>
> **M2. The runbook cannot be completed as written.**
> - Where: runbook §0, P1, step 4's "STOP here", step 5.
> - Problem 1: §0 requires one clean checkout at one published commit (`$C`) for the whole run. But step 4 must STOP until a P.4 evidence phase exists, and step 5 needs author rows and P.4 commits that will land on main later. `check_record` reads PLAN from the checkout and runs `merge-base --is-ancestor` against that clone's `refs/remotes/origin/main`. A resumed run on the old `$C` therefore fails ("decision … must cite an author row" or "not an ancestor of origin/main"), while updating the checkout breaks §0. No resume procedure is given.
> - Problem 2: `render --out docs/r1/arms_frozen/…` writes with `Path.write_text` and no `mkdir`. `docs/r1/arms_frozen/` does not exist on main, so the call fails with FileNotFoundError (reproduced).
> - Problem 3: render writes into `$W/paper`, which step 6 says must stay as it was.
> - Fix: make steps 1–3 a run on `$C`, and steps 4–5 a separate resumed run on a fresh clone of the then-current main. State that the A3 artefacts and their `code_commit` carry over, since they remain ancestors. Create the parent directory in `render` (or add `mkdir -p` to the runbook), and render in the delivery worktree.
>
> **M3. Step 1 of the runbook is underspecified and refuses the existing pinned table without saying why.**
> - Where: runbook §2 (step 1).
> - Problem: `--paper-root <…>` and "`AR_HARNESS_ROOT` the audited harness…" are open placeholders. They are not set up in the preconditions and not marked as to-be-filled with a STOP. The diagnosis notes that `evidence_classification` forces the index and sidecar inside the paper root. Meanwhile `trackp_sft.json` names an existing table with the same pinned bytes (`host_path …/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z`), and the runbook says "do not fall back to the W2.3 table".
> - Failure scenario: the agent guesses a paper root and the replay refuses or differs, so the run STOPs. Or it improvises paths that are not on record.
> - Fix: either use the pinned W2.3 table after `sha256sum` matches `d0048567…`/`b585b727…` (keeping a rebuild as an optional cross-check), or name the paper root, harness root and noise argument as preconditions with explicit STOPs.
>
> **M4. The record checker does not tie the record's tables to what the arms were actually trained on.**
> - Where: `check_record`, the `label_tables` and `feature_tables` blocks.
> - Problem: `label_tables.*` are only checked to be 64-hex strings. They are not compared with each arm entry's `inputs` (`receipt_sha256`, `traindev_partition_sha256`, `table_proposals_sha256`). `feature_tables.sweep1.arms_proposals_sha256` is not compared with A3's `inputs.sweep1.table_proposals_sha256`.
> - Failure scenario (reproduced): a record that cites one receipt while A3 entries carry another passes, and the test release row would cite it permanently.
> - Fix: require, for every A3-family entry, `inputs[src]` to equal `label_tables[src]` (receipt and partition) and the feature-table sha (v3 arms sha for sweep1, released sha otherwise). Optionally re-hash the receipt files under a `--release-root`.
>
> **M5. The ARMS-TWIN recommendation rests on an incomplete statement of the preregistration.**
> - Where: report §3, item 5.
> - Problem: option A says "the preregistration defines no deduplication". But §1 quotes R1-MAIN-PROPOSER (e)(3), "duplicates are grouped across sources by (instance, incumbent hash, edit hash)", and PRE-DUP refers back to it. Whether "grouped" governs pooled training rows is exactly what the author must decide. The options omit the natural grouped-weight option (weight 1/n per twin group).
> - Fix: cite (e)(3), argue why it does or does not apply to training, and add the grouped-weight option. Keep A as the recommendation if the argument holds.
>
> **M6. Two options have code costs the report does not state.**
> - Where: report §3, items 7 and 8.
> - ARMS-A5FOLD B ("the fold analyses report A3 only"): this is not possible with the reviewed `fold_analysis`. `fold_input` → `B.build` runs `TEST_SERIES` including A5, and `_series_rewards` raises when A5 predictions are missing. B therefore needs a change to a reviewed module, plus an author row amending FOLD-LEVELS A ("both arms").
> - ARMS-A5CKPT C (a seed ensemble, "one entry binding three checkpoints"): rejected by `a5_pin_binding`, which needs exactly one grid run.
> - Fix: state both code consequences in the options, and add runbook STOPs for choosing B or C.
>
> ### m (minor)
>
> - **m1. PRE-T1 instances not recorded** (`check_record`, `t1`). PRE-T1 A freezes "the T1 node set and its instances", but the record carries only suites, modes and `d3_k6`. This does not matter while T1 is empty. Add a `t1.instances` list checked against the split file.
> - **m2. G.1b paths re-hashed under the wrong root** (`check_record` with `--artefact-root`). G.1b summaries are committed repo files: `release_row` reads them with `_committed`. The checker re-hashes them under `$A`, so with T1 the check `--artefact-root $A` would fail. Re-hash them against the repo instead.
> - **m3. Toolchain versions not in the arm entry** (`write_arm`). The model bytes depend on LightGBM and NumPy, but their versions appear only in the run log. Add `lightgbm`, `numpy` and the Python version to the entry.
> - **m4. Narrowing the signed scope not called out** (ARMS-SECONDARY). Options A and C narrow the signed PRE-SECONDARY A scope ("TabPFN rows"). Say explicitly that this is an amendment to be disclosed.
> - **m5. Gaps in the inventory** (report §1). The C3_DESIGN ladder rows "ref" (AWR-MLP/PACE), A7, the StartLux/Laya A5 bases (narrowed by R1-C3-POOL-EXAM) and TabPFN R-A0/R-A1 (R1-TABPFN (c)) are missing. Add them as "not in this read", for completeness.
> - **m6. Unregistered left-out rule** (`preselect_score`). Leaving a node out of the mean ("no labelled dev row" or "base-rate RPS is 0") is an engineering reading not in PRE-SELECT A. It is stated in §5, which is fine, but it should be named for the author row.
> - **m7. Smaller issues.**
>   - `freeze_a3` raises `BuilderError`, not `ArmsFreezeError`, when called without `sweep1` and without `primary_dev`.
>   - `_train_cmd` does not check the identity JSON's `schema`/`featurizer`.
>   - `refuse_input_path` is only a name check; the real lock is `open_partition`. That is acceptable, but the docstring overstates it.
>
> **Tests.** 33 tests pass and none is vacuous. Missing tests: the M1 self-identity case, the M4 cross-binding, and calibration being fitted only on the primary-dev audit rows.
>
> ## Notes for the cluster agent
> - Sweep-2 receipt counts: 0 no-ops and 2,512 within-campaign duplicates, so sweep-2 training and selection rows are audit labels only.
> - The sweep-2 receipt (`de95b218…`) opens only while the R1-S2-LABELS-TRAINDEV-RELEASE row text and its release commit `a9d8ff5e` are unchanged (`open_partition` checks `decision_sha256` `860a50e2…`). If the unit-1 fix amends that row, P3 fails: STOP and return to the author.
> - Until M1 is fixed, do not accept any identity result other than 116 differences with arms sha `d0048567…`.
> - Until M2 is fixed, run `mkdir -p docs/r1/arms_frozen` in the delivery worktree before `render`.
> - LightGBM is not known to be present in `/ceph/dwong/r1_prepare_20261025/venv`; P2 STOPs if it is absent.
>
> ## Process
> - Read the unit's four files and the authority on main: the preregistration (sha `aa1a961b…`), C3_DESIGN §5, the PLAN rows, the sweep-1 diagnosis, the sweep-2 receipt copy, `gate_input_builder`, `arms`, `features`, `metrics`, `release`, `fold_analysis`, `audit.evidence_blocks`, `dataset`, `sft_test_eval`, and `p4_phase1.py` from `origin/mac-trackp-p4-runner-20261122` @ `7ab79a9d` via `git show`.
> - Ran only `r1/tests/test_c3_arms_freeze.py` (33 passed) and one synthetic probe script, both with `PYTHONPATH=/tmp/armsdev/pylib` and `TMPDIR=/tmp/armsrev/t`.
> - No secrets, sealed data, real labels or evaluation values were read. The worktree is unchanged (HEAD `63a7c408`; the `__pycache__` dirs predate this review).
> - All scratch was moved to `/tmp/armsrev/_to_delete/`; nothing was deleted.
>
> VERDICT: NOT ACCEPTED (fix M1–M6: enforce the v3 sha in code and checker; make the runbook resumable and the render step executable; specify or replace step 1's rebuild inputs; bind the record's tables to the arms' inputs; correct the ARMS-TWIN premise; state the code costs of ARMS-A5FOLD B and ARMS-A5CKPT C)

## Round 2 (`80ba6b83`)

> Reviewed base: 80ba6b83b4075533d7c61fe374493c311278f691 (round 2; diff `63a7c408..80ba6b83`, commits `c603264f` and `80ba6b83`)
>
> ## Summary
> Round 1's M1–M4 and M6 and all the minors are fixed, and I checked each fix in the code and tests rather than trusting the summary. 41 tests pass.
>
> One new major issue remains: the new default ARMS-TWIN weighting (`--twin-weight group`) does not do what the report says it does, and it shifts sweep 2's own training weights in the pooled variant. So I am not accepting yet, though the fix is narrow.
>
> **What I verified as fixed:**
> - **M1 (FEAT-ONE).** The pins `SWEEP1_V3_PROPOSALS_SHA256` and `SWEEP1_V3_CONFIGS_SHA256` equal `trackp_sft.json`'s `sweep1_v3` entry, and a test ties them together. `require_feat_one` runs in both `train-a3` and `check_record`. It refuses a table compared with itself, an arms table that is not the pinned one, an arms configs file that is not the pinned one, and a wrong schema or featurizer. Tests cover each.
> - **M2 (runbook resumability).** Render now creates the record directory and runs in `$W2/deliver`. The runbook is split into Run I and Run II. I judge the carry-over between them sound; the sub-items are under "Run II carry-over" below.
> - **M3 (step 1).** Step 1 now uses the pinned W2.3 table. Its path equals `trackp_sft.json`'s `host_path`, and the run STOPs if the directory is missing or any hash differs. The rebuild is dropped.
> - **M4 (record binding).** Every A3-family entry's `inputs` must now equal `label_tables` and `feature_tables`, including the v3 sha for sweep 1, and `toolchain` is required. The optional `--release-root` re-hashes each receipt and partition. Tests cover both.
> - **M6.** The code costs of ARMS-A5CKPT C and ARMS-A5FOLD B are stated, and the runbook STOPs on either (II-P4).
> - **Minors.** The new T1 instance check works. G.1b summaries are re-hashed through `release._committed`. The new ladder rows are added. ARMS-LEFTOUT is its own decision. The narrowing of PRE-SECONDARY A is now flagged as an amendment. `ArmsFreezeError` wraps the builder's refusal. The new calibration test correctly shows that only primary-dev audit rows are used.
>
> **The PLAN wording behind M5.** Main's PLAN row R1-MAIN-PROPOSER (e)(3) does say "duplicates are grouped across sources by (instance, incumbent hash, edit hash) **for folds and for deduplication**". The frozen preregistration quotes it without the last five words. Re-arguing ARMS-TWIN from that row is fair.
>
> **The twin key's "edit hash" reading.** Reading "edit hash" as the candidate hash is right on main. PRE-DUP itself says "(e)(3)'s grouping key adds the instance" to `sft_data.dup_key`, which is node | incumbent configuration hash | candidate configuration hash. That makes (instance, incumbent hash, candidate hash) the preregistration's own reading. See m1 for one wrong sentence in the report about this.
>
> ## Findings
>
> ### B (blocking)
> None.
>
> ### M (major)
>
> **M1-r2. The `group` twin weighting changes sweep 2's own weights in the pooled variant, and the report does not say so. It is also the code default.**
> - **Where:** `arms_freeze.twin_weighted` and `freeze_a3`; the `--twin-weight` default `group`; report §3 item 6.
> - **The problem:** groups are keyed by (instance, key) across both memory modes. A group gets weight 1/n only if it spans two sources. So same-key rows within one source stay at weight 1 when the key is sweep-2-only, but are collapsed as soon as sweep 1 also has the key. The report describes the result as "the group counts once" and says "within-source cross-mode repeats are not 'across sources'", which reads as if sweep 2's cross-mode repeats are untouched.
> - **What it does (I ran it with synthetic rows):**
>
>   | Rows sharing one key on one instance | Sweep-2 total weight | Group total weight |
>   |---|---|---|
>   | Sweep 2, both modes | 2 | 2 |
>   | Same, plus sweep 1 in one mode | 0.67 | 1 |
>   | Same, plus sweep 1 in both modes | 0.5 | 1 |
>
>   So adding sweep-1 data lowers the key's total weight below what the sweep-2-only variant gives it.
> - **Why it matters:** PRE-DUP's own disclosure says repeats concentrate on early-campaign proposals. Those proposals likely occur in both modes and both sources, since the first trial's prompt does not depend on memory. Under the default, then, PRE-POOL no longer compares "sweep 2" against "sweep 2 plus sweep 1"; it compares "sweep 2" against "sweep 2 reweighted, plus sweep 1". The default also makes this unsigned reading the silent outcome whenever the flag is left off.
> - **On the default itself:** PRE-POOL in the preregistration is only "pooled versus sweep-2-only, chosen on validation". It does not define how pooled rows are weighted, so either weighting is a reading that ARMS-TWIN must decide. A default is acceptable only if the run must state the choice. The runbook does pass the flag explicitly and checks `twin_weight` in the output, but nothing enforces that.
> - **Fix:**
>   - Define the twin rule so the group's total weight equals what one source contributes. One way is to group by (instance, memory mode, key), which matches how twin campaigns pair: same instance, same mode. Each cross-source twin pair then gets 1/2 per row, and the sweep-2 total stays at 2. If the literal (instance, key) grouping is kept on purpose, state the collapse of cross-mode rows in ARMS-TWIN B and offer the per-mode option.
>   - Add a test for the mixed case: both modes of sweep 2 plus one or two sweep-1 rows.
>   - Remove the default: make `--twin-weight` required, and preferably `--calibration` too, so the author row's choice is typed into the command. Make the `freeze_a3` keyword required as well.
>
> ### m (minor)
> - **m1. Report sentence about the edit hash** (report §3 item 6). "the table carries a candidate-configuration hash, not an edit hash" is imprecise. Main has `sft_data.edit_hash`, which hashes the row's `edit`. Cite PRE-DUP's sentence ("(e)(3)'s grouping key adds the instance" to `dup_key`) as the authority for using the candidate hash instead.
> - **m2. Unused constant** (`arms_freeze.py`). `SWEEP1_SEALED_PROPOSALS_SHA256` is defined but never used. Either use it in `require_feat_one` and `check_record` (requiring `label_tables.sweep1.proposals_sha256` to equal it) or remove it.
> - **m3. Run II carry-over gaps** (runbook II-P2, II-P4):
>   - `feat_one_identity.json` is copied into `$A` after `SHA256SUMS` is written, so it is not covered. Add it to `SHA256SUMS`.
>   - Run II does not check that the A3-gating decision rows it cites (ARMS-CAL, ARMS-LEFTOUT, ARMS-HP, ARMS-WDBC, ARMS-TWIN) are the ones Run I recorded. If a row is amended between runs, the record would cite a decision A3 was not built under. Compare them against `RUN_I.md`, and compare the entries' `twin_weight` and `calibration_mode` with the cited row.
>
> ## Run II carry-over
> Apart from m3, the carry-over is sound:
> - `merge-base --is-ancestor $C origin/main` runs on a fresh clone, and the checker repeats it for every code commit.
> - `sha256sum -c` over Run I's `SHA256SUMS` and a read-only folder protect Run I's files.
> - The A3 artefacts are re-hashed under `$A`, and the inputs, label tables and receipts are bound to each other.
> - The gate, builder and preregistration are frozen, so checking them at `$C2` is equivalent to checking them at `$C`.
> - Running `-m r1.c3.arms_freeze` from `$W2/deliver` makes `REPO` the delivery worktree, so PLAN rows and `origin/main` refs resolve there.
>
> ## Notes for the cluster agent
> - Pass `--twin-weight` and `--calibration` explicitly, exactly as the author row decides, until they become required arguments.
> - Run I has no other changes from round 1's notes.
>
> ## Process
> - Read the diff `63a7c408..80ba6b83` and the revised report and runbook in full. Checked PLAN row R1-MAIN-PROPOSER (e)(3), `sft_data.dup_key`, `sft_data.edit_hash` and the receipt fields.
> - Ran `r1/tests/test_c3_arms_freeze.py` (41 passed) and one synthetic twin-weighting probe, both with `PYTHONPATH=/tmp/armsdev/pylib` and `TMPDIR=/tmp/armsrev/t`.
> - No real data, secrets, sealed files or evaluation values were read. The worktree is unchanged at HEAD `80ba6b83` and no new `.pyc` files were written.
> - Round-2 scratch was moved to `/tmp/armsrev/_to_delete/round2/`. Round 1's moved scratch (`p4.py`, `scripts`, `t`) is no longer in `_to_delete`; I did not delete it, and it seems to have been cleared from the environment between sessions.
>
> VERDICT: NOT ACCEPTED (M1-r2: fix the twin-group weighting so adding sweep 1 does not reduce sweep 2's own weights (or state that effect in ARMS-TWIN B and offer per-mode grouping), add the mixed cross-mode test, and make --twin-weight a required argument)

## Round 3 (`6e8ddaeb`)

> Reviewed base: 6e8ddaeb163b7d6cdc5a31e9f89de3d8f6207ada (round 3; diff `80ba6b83..6e8ddaeb`, commits `e3f59245` and `6e8ddaeb`)
>
> ## Summary
> The round-2 major is fixed and so are m1–m3; I checked each against the code, the tests and main rather than the author's summary. 43 tests pass. I am accepting the unit. Two small wording points remain in the report and need no further round.
>
> **The new twin rule matches the summary.**
> - `twin_weighted` now groups by (instance, `memory_mode`, key). A group that spans k sources gets the total weight T that one source contributes alone, with T the largest per-source row count. Each row of source s gets T/(k·n_s).
> - I recomputed the three test cases by hand. Sweep 2 alone in both modes gives a key total of 2. Adding a sweep-1 twin in one mode gives a key total of 2, with sweep 2 at 1.5 (row weights 0.5, 1, 0.5). Adding sweep-1 twins in both modes gives a key total of 2, with sweep 2 at 1.
> - The new test also covers non-twins (another instance, another mode, another key) and a source with two rows in one group.
>
> **The switches are now required.**
> - `--calibration` and `--twin-weight` are required on the command line, and a test shows that leaving either out exits without writing anything.
> - `calibration` and `twin_weight` are required `freeze_a3` keywords. Both internal callers pass them.
> - The old value `group` is refused.
>
> **The record now carries the A3 settings.**
> - `a3_settings` is a required field of the record.
> - Every A3-family entry's `calibration_mode` and `twin_weight` must equal it, and a test covers this.
>
> **m2: the sealed-table pin.** `SWEEP1_SEALED_PROPOSALS_SHA256` equals line 83 of `docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md`. `require_feat_one` now enforces it, and a test covers this.
>
> **m1: the edit-hash sentence.** The report now cites PRE-DUP's sentence and `dup_key`, and it acknowledges that `sft_data.edit_hash` exists.
>
> **m3: Run II carry-over.**
> - `SHA256SUMS` now covers the A3 artefacts, `feat_one_identity.json` and `RUN_I.md`, and is written before `chmod`.
> - `RUN_I.md` records the five A3-gating decision row ids and the values typed for the two switches.
> - II-P4(a) STOPs if any of those rows has changed or been amended, or if the entries do not match.
>
> ## Your two questions
>
> **Is per-mode grouping the right reading, and is it stated honestly?** Yes to both.
> - My round-2 fix text was wrong. I wrote that "the sweep-2 total stays at 2", which confused the key's total with sweep 2's share. Any rule that counts a cross-source twin once has to move some weight from the sweep-2 row to its sweep-1 twin. Only option C (drop the sweep-1 copy) keeps sweep 2's share and the key total unchanged together.
> - The author's rule keeps the invariant that matters for PRE-POOL: each key's total weight in the pooled variant equals its total in the sweep-2-only variant, so sweep 1 adds weight only where it brings a key sweep 2 lacks.
> - Grouping by (instance, mode) matches how twin campaigns pair: same instance seed, same memory mode, both sources.
> - The report says plainly that inside a twin pair sweep 2's row goes from 1 to 1/2. It shows B-literal with its numbers, and it lists A (plain union) and C.
>
> **Is the reweighting of sweep 2 inside the pooled variant now acceptable?** Yes, as a declared author option rather than a silent change.
> - PRE-POOL does not define how pooled rows are weighted, so this is ARMS-TWIN's to decide.
> - The effect is now described in the report.
> - No default remains: the value must be typed, and it is recorded in `a3_settings` and checked against every entry.
> - The runbook STOPs on B-literal or C, and its II-P4(a) step catches a decision row that changes between the two runs.
> - PLAN's R1-MAIN-PROPOSER (e)(3) wording, "for folds and for deduplication", supports B as the recommendation.
>
> ## Findings
> **B (blocking):** none.
>
> **M (major):** none.
>
> **m (minor), wording in report §3 item 6:**
> - **m1. Twin rows share the label, not the context.** The report says "a twin pair is by design one example with one label in two copies". But (e) itself speaks of a cross-proposer table, so the two sources come from different proposers. Twin rows share the label of (incumbent, candidate), but their history features can differ (`budget_index`, `keeps_so_far`, `recorded_gain_z` and so on). B and C therefore also differ in which context carries the weight, not only in how disagreeing labels are handled, and "the same totals as B when the labels agree" should say so. Fix: one sentence in item 6; no code change.
> - **m2. A note on the T = 1 claim.** "1 in practice" holds for sweep 2, whose receipt counts 0 no-ops. On sweep 1, two identical labelled no-ops in one campaign could make T = 2; the code handles that case correctly (the "odd" test). No action needed beyond optionally saying so.
>
> ## Process
> - Read the diff `80ba6b83..6e8ddaeb` in full: code, tests, report and runbook.
> - Checked PLAN R1-MAIN-PROPOSER (e) and the B.2 audit review's sealed sha. Confirmed that both internal `freeze_a3` callers pass the now-required keywords.
> - Ran `r1/tests/test_c3_arms_freeze.py` only (43 passed) with `PYTHONPATH=/tmp/armsdev/pylib` and `TMPDIR=/tmp/armsrev/t`.
> - No real data, secrets, sealed files or evaluation values were read. The worktree is unchanged at HEAD `6e8ddaeb`, and no new `.pyc` files were written.
> - Round-3 scratch was moved to `/tmp/armsrev/_to_delete/round3/`. As after round 2, the scratch moved in earlier rounds is no longer in `_to_delete`. I did not delete it; it seems to have been cleared between sessions.
>
> VERDICT: ACCEPTED

## Round 4 (`e5674a38`)

> Reviewed base: e5674a38c755714460ff075d221b3cbfdcaa5eac (confirmation round; diff `6e8ddaeb..e5674a38`, report only)
>
> ## Summary
> The change is one file, `docs/r1/reports/arms_readiness_20261123/T0_ARMS_READINESS_20261123.md` §3 item 6, with 9 lines added and 6 removed. No code, test or runbook file changed. Both round-3 minors are fixed correctly.
>
> - **m1 (twins share the label, not the context): fixed.** The report now says a twin pair shares the label of (incumbent, candidate) but not its context. It gives the reason (different proposers) and names example history features. Option C now says it has the same totals as B but puts all the weight on the sweep-2 row's context instead of half on each proposer's. This matches the code and the PLAN (e) wording.
> - **m2 (T = 1 qualified to sweep 2): fixed.** "1 in practice" is now limited to sweep 2, whose receipt counts 0 no-ops. The text adds that two identical labelled no-ops in one sweep-1 campaign could make T = 2, and that the code handles this. The round-3 "odd" test covers that case.
>
> One optional wording nit: the next sentence still says counting both gives "a second copy" of early-campaign proposals. That sits slightly loosely beside "not its context", but it is not misleading.
>
> ## Findings
> - **B (blocking):** none.
> - **M (major):** none.
> - **m (minor):** none beyond the optional nit above.
>
> ## Process
> - I read the diff only. No tests were run, since there was no code change.
> - The worktree is unchanged at HEAD `e5674a38`, and no scratch files were created this round.
> - `/tmp/armsrev/` is now empty and `/tmp/armsrev/_to_delete/` no longer exists. The scratch I moved there in earlier rounds seems to have been cleared between sessions; I did not delete it.
>
> VERDICT: ACCEPTED

---

Code-Commit: e5674a38c755714460ff075d221b3cbfdcaa5eac
Verdict: ACCEPTED

Accepted at `6e8ddaeb`, confirmed at `e5674a38`.
