Reviewed base: `1f9e82324b3d2e89f5128de30caef864b59757a4` (branch `mac-trackp-sft-dup-20261117`; accepted in round 2)

# Independent review record — Track P SFT cross-split duplicate rule (R1-TRACKP-SFT-DUP)

**Unit.** The decided duplicate policy `heldout_excludes_seen` in `r1/c3/train/sft_data.py` (build and load), the
primary/secondary held-out metrics in `r1/c3/train/sft.py`, `sft-dev` in `r1/scripts/trackp.py`, the config
`r1/scripts/configs/trackp_sft.json`, tests in `r1/tests/test_trackp_sft.py`, and the report
`docs/r1/reports/TRACKP_SFT_DUP_20261117.md`, on `mac-trackp-sft-dup-20261117` over `main` `50176481`. Authority:
PLAN row R1-TRACKP-SFT-DUP (on `main` `50176481`); queue of 17 Nov 2026, item (3).

**Process.** One independent reviewer (a separate agent that did not write the code) for both rounds; it edited
nothing (scratch files under `/tmp/sftrev/` only). The round texts are reproduced below as delivered, as block quotes,
so that only this record's own closing lines are read as the acceptance.

| Round | Commit reviewed | Verdict |
|---|---|---|
| 1 | `11599ae6` (diff from `50176481`) | ACCEPTED (2 minor, 3 notes; M1 to fix before real labels) |
| 2 | `1f9e8232` (diff from `11599ae6`: the round-1 findings, report §4) | ACCEPTED (3 notes, optional) |

**Full `r1/tests` suite** (coordinator, Python 3.12 / torch 2.6 environment; failures are environmental —
transformers without the Qwen3.5 classes, no Hugging Face access): base `50176481` 54 failed, 2,538 passed, 195
skipped; `11599ae6` 54 failed, 2,541 passed; `480031a7` (= `1f9e8232` code) 54 failed, 2,542 passed; the same 54
failing tests in all three.

---
## Round 1 (commit `11599ae6`)

> # Independent review: Track P SFT cross-split duplicate rule R1-TRACKP-SFT-DUP (11599ae6 vs main 50176481)
>
> Code-Commit: 11599ae68d0e49991397f411d69347686a6c2c0b
>
> **Verdict: ACCEPTED**
>
> Two minor findings are below. I recommend fixing M1 before any data directory with real labels is trained on.
>
> Reviewer: independent code reviewer (AI-assisted, Claude). I did not write this code.
>
> Scope: `git diff 50176481..11599ae6`, 7 files, +214 / −35.
> - Worktree: `/tmp/pb/wt/sftdup`, branch `mac-trackp-sft-dup-20261117`.
> - Authority: PLAN row `R1-TRACKP-SFT-DUP`, `docs/r1/PLAN.md:1288` on main 50176481.
> - The worktree is untouched: HEAD is 11599ae6 and `git status` is clean.
> - Scratch files are under `/tmp/sftrev/` only.
> - I read no seed-7001–7010 data and no secrets. The probes use the test suite's synthetic fixtures, plus the pinned `c3_features/v3` table with `SyntheticLabelSource`, the same inputs as the coordinator's smoke run.
>
> ## What I ran
>
> - **Tests:** `test_trackp_sft.py` + `test_trackp_cli.py` + `test_d8_sweep2_reader_refusal_matrix.py` (`TMPDIR=/tmp/sftrev`, `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin`, `-p no:cacheprovider`): **231 passed, 9 skipped**.
>   - That is the report's 34 passed / 9 skipped, plus the 197 D8-matrix cases, all passing.
>   - The 9 skips are the environment-dependent `test_trackp_cli` cases.
> - **Probe tests** in `/tmp/sftrev/probe/test_probe_dup.py` (output in `probe_out.txt`): 3 passed.
>   1. **Same run with and without `val_secondary`:**
>      - Identical: `selected`, `temperature`, `selected_temperature_scaled`, `train_config_sha256`, `total_steps`, best step and best value.
>      - `metrics.jsonl` is identical except the wall-clock `step_s`.
>      - The only extra report keys are `selected_full_heldout` and `selected_full_heldout_temperature_scaled`.
>   2. **Data directory built with `drop_from_train`, then run through `run_stage_s`:** accepted, and the report says `heldout_rule: "R1-TRACKP-SFT-DUP: …"`. See M1.
>   3. **Real `LabelBlockSource` (synthetic fixture):**
>      - The decided policy builds.
>      - `drop_from_train` and `exclude_from_heldout` raise `SFTDataError`, and nothing is written.
> - **Which reading of "seen" the decision means** (`/tmp/sftrev/probe/seen_reading.py`, output in `seen_reading.txt`). On the sweep-1 table with the configured splits:
>
>   | reading | primary labelled test |
>   |---|---|
>   | seen = train + val | **74** |
>   | seen = train only | **77** |
>
>   Primary val is 47 under either reading. Building the duplicate keys from all table rows or from labelled rows only gives the same numbers on this table.
> - **Coordinator's smoke log** (`/tmp/sftwork/dup/run1.log`, script `/tmp/sftwork/scripts/dup_smoke.py`):
>   - The counts equal the report's §2 table: 1,176 / 47 / 240 / 287 / 262 / 188 / 674.
>   - I compared `run1/run/sft_report.json` with the earlier `exclude_from_heldout` smoke (`/tmp/sftwork/real/smoke2/run/sft_report.json`). `selected`, `selected_temperature_scaled`, the temperature (0.4603), best step 370 and best value are identical, so the report's claim holds.
>   - `train_config_sha256` differs between the two only because the older run predates `TrainConfig.extra`.
>
> ## Checks requested by the coordinator
>
> **1. The rule against the decision.**
> - **Train:** every labelled train row is kept. Matches the decision.
> - **Primary val:** val rows whose key is not on a train instance; the duplicates are written as `val_seen`. Matches.
> - **Secondary val:** `val` + `val_seen`. Matches.
> - **Primary test:** test proposals whose key is on no train or val instance; the excluded ids are listed in `splits.json`. **Secondary test:** every test proposal.
> - **Your reading in report §3(1)** (seen for test includes val) is **correct**. The PLAN row's own pilot size, 74 of 262, is reproduced only by the train + val reading; train only gives 77. 74 is also the figure in the earlier DEV report's `exclude_from_heldout` column, which the decision adopted with 1,176 / 47. The report says the train-only population "would be larger than 74"; it could say 77.
> - **Sweep 2:** gets the same rule through the default.
>
> **2. Can the secondary rows influence selection?** No.
> - `Trainer` gets `train` only. The `evaluate` closure (early stopping, best checkpoint) and the temperature fit use primary `val_prompts` and `logits` only.
> - `val_secondary` is used only after `report["selected"]` and the temperature exist, and only to add the two report keys and `pred_val_seen_logits.npy`.
> - It is not part of `TrainConfig`. `extra` holds only `sft_data_sha256`, the data identity, which correctly changes with the data directory.
> - `select_lr` reads `train.best_value`, which is primary val.
> - Probe 1 confirms all of this, including identical `train_config_sha256` and step metrics.
>
> **3. Can the CLI bypass the refusal of the earlier policies with real labels?**
> - **At build time: no.**
>   - `build_sft_data` is the only writer. It refuses any policy other than `heldout_excludes_seen` unless `label_source.provenance()["kind"] == "synthetic"`. A missing `kind` is also refused (fail closed).
>   - The refusal comes before anything is written.
>   - The CLI builds either `SyntheticLabelSource` (`--labels synthetic`) or `LabelBlockSource` (kind `label_block`). A custom `--sft-config` with `drop_from_train` and a real block is therefore refused, and becomes a STOP because `SFTDataError` is a `ValueError` wrapped by `_sft_errors`.
> - **At consumption time: yes.** `sft-dev` accepts any existing data directory whatever its policy. See M1.
>
> **4. Manifest and `splits.json` fields.**
> - `splits.json` gains `cross_split_duplicates`, `heldout_populations` (decided policy only), and `test_proposals_seen_in_train_or_val`. That list is all test-instance table rows whose key is seen (674); the primary labelled test is 262 − 188 = 74.
> - Manifest counts gain `val_seen` and `val_full`.
> - The policy is named in `splits.json` (`config` and top level), and `splits.json` is bound by `splits_sha256`. That is adequate.
> - A code reader from 50176481 refuses a new data directory ("row of split 'val_seen'"), so the format change fails closed.
>
> **5. Tests.** Adequate for the decision. Details in M2 and N2.
>
> **6. Report.**
> - Accurate: §1, §2 (counts, the 34/9 test count, the smoke equality), §3, and the DEV report's §3(1) pointer.
> - §4 (full suite) is still a placeholder; you said you will fill it.
>
> ## Findings
>
> No BLOCKING findings.
>
> ### M1. MINOR — `sft-dev` accepts data directories built under an earlier policy, and labels the run with the decided rule anyway
>
> - **Location:**
>   - `r1/scripts/trackp.py:350` (`_stage_s`);
>   - `r1/c3/train/sft_data.py:580ff` (`load_sft_data`);
>   - `r1/c3/train/sft.py:145` (`heldout_rule`).
> - **Failure scenario:**
>   - Neither `load_sft_data` nor `_stage_s` reads the data directory's `cross_split_duplicates`. That field is in `splits.json`, which `load_sft_data` already reads and hash-checks.
>   - So suppose a data directory was built with real labels under base 50176481 or earlier, where `drop_from_train` was the default. `sft-dev` trains on it, and its val is treated as "primary".
>   - `run_stage_s` then writes the fixed string `heldout_rule: "R1-TRACKP-SFT-DUP: primary = val without training duplicates …"` into `sft_report.json`. Probe 2 shows this on a `drop_from_train` directory.
>   - The record would then claim the decided rule for a run that did not follow it. This is the consumption-side way around "earlier policies refused with real labels".
>   - Impact today is limited: `sft-dev` is ENGINEERING_ONLY, P.4 `sft` is "not yet", and I am not aware that any real-label data directory exists. That is why this is minor and not blocking.
> - **Fix:**
>   - In `load_sft_data`, or in `_stage_s` from the already-loaded `splits.json`, read `config.cross_split_duplicates`.
>   - Refuse when it is not `DECIDED_DUPLICATE_POLICY` and `manifest["labels"]["kind"] != "synthetic"`. Treat a directory without the field as an earlier policy.
>   - Have `run_stage_s` record the data's actual policy, passed in from the manifest or `splits.json`, instead of the fixed `heldout_rule` text. At least write the rule text only when the policy is the decided one.
>   - Add a test: a synthetic `drop_from_train` directory with the manifest's label kind patched to `label_block` is refused by `sft-dev`.
>
> ### M2. MINOR — no CLI-level test of the policy refusal
>
> - **Location:** `r1/tests/test_trackp_sft.py::test_earlier_policies_refused_with_real_labels`.
> - **What:** the test calls `build_sft_data` directly. The CLI path is short and I verified it by reading the code: custom `--sft-config`, then the `cmd_sft_data` split filter, then `build_sft_data`, then STOP.
> - **Fix (optional):** one `stop([...sft-data --sft-config <copy with drop_from_train> --labels <fixture block> ...], "R1-TRACKP-SFT-DUP")` case in `test_cli_dry_run_end_to_end`. This depends on the fixture block being acceptable to the CLI, which `sweep_replay_inputs` is stubbed for.
>
> ### N1. NOTE — "seen" uses every table row of a train/val instance, not only the rows actually trained on
>
> - **Location:** `sft_data.py`. `keys = {s: {dup_key(r) for r in table_rows …}}` covers unlabelled rows too.
> - **What:**
>   - The decision says "duplicates of the training set". The code counts a key as seen if it occurs on any row of a train (or val) instance, labelled or not.
>   - On sweep 1 both readings give 47 / 74, as my probe shows: a key's eligibility is the same across instances here. So the result is unaffected.
>   - On sweep 2 they could in principle diverge.
> - **Fix (optional):** state this in the docstring and report. Or build `keys["train"]` and `keys["val"]` from labelled rows; that is identical on sweep 1.
>
> ### N2. NOTE — test strength
>
> `test_stage_s_reports_secondary_full_heldout` compares `selected` between runs with and without the secondary rows.
> - Adding `temperature`, `train_config_sha256` and `train.best_step` to the equality would close the remaining paths cheaply. Probe 1 shows they are equal today.
> - The "selection on primary val only" assertion (`selected.val_rps == train.best_value`) is a weak proxy; the two-run equality is the real check.
>
> ### N3. NOTE — small items
>
> - `trackp.py:328` is now 137 characters; the comprehension could be wrapped. The file already has other lines over 120.
> - `SFT_DATA_SCHEMA` was not bumped although rows can now carry `val_seen`. Older readers already refuse the new split, so this is optional.
> - Report §3(1) could state the concrete alternative: primary labelled test 77 if only train counts.
>
> ## Conclusion
>
> The implementation matches R1-TRACKP-SFT-DUP:
> - every train row is kept;
> - the primary val and test populations exclude training duplicates;
> - the full populations are reported as secondary;
> - the pilot sizes 1,176 / 47 / 74 of 262 are reproduced.
>
> Your reading that test "seen" includes val is the reading that matches the decision's own 74; train only gives 77.
>
> The secondary rows provably cannot affect training, early stopping, temperature, `select_lr` or the training-config digest. The earlier policies cannot be selected with real labels when building through the CLI.
>
> The one gap is on the consumption side (M1): `sft-dev` does not check the data directory's policy and stamps the decided rule on any run. Fix it before real labels are used. The report is accurate except for the §4 placeholder.
>
> ## Scratch artefacts
>
> - `/tmp/sftrev/review_dup.md`: this review.
> - `/tmp/sftrev/probe/test_probe_dup.py` and `probe_out.txt`.
> - `/tmp/sftrev/probe/seen_reading.py` and `seen_reading.txt`.

---

## Round 2 (commit `1f9e8232`)

> # Independent review, round 2: R1-TRACKP-SFT-DUP fixes (1f9e8232 vs 11599ae6)
>
> Code-Commit: 1f9e82324b3d2e89f5128de30caef864b59757a4
>
> **Verdict: ACCEPTED**
>
> Reviewer: independent code reviewer (AI-assisted, Claude).
>
> Scope: `git diff 11599ae6..1f9e8232`, covering 480031a7 (round-1 fixes) and 1f9e8232 (report §4). 5 files, +77 / −14:
> - `r1/c3/train/sft.py`
> - `r1/c3/train/sft_data.py`
> - `r1/scripts/trackp.py`
> - `r1/tests/test_trackp_sft.py`
> - `docs/r1/reports/TRACKP_SFT_DUP_20261117.md`
>
> The worktree is untouched: HEAD is 1f9e8232 and `git status` is clean. Scratch files are under `/tmp/sftrev/` only. I read no seed data and no secrets; all probes use synthetic fixtures.
>
> ## What I ran
>
> - **`test_trackp_sft.py` + `test_trackp_cli.py`** (same environment and flags as round 1): **35 passed, 9 skipped**. This equals the report's round-1 line: 34 + the 1 new test function.
> - **New probes** in `/tmp/sftrev/probe/test_probe_dup_r2.py`: both pass.
>   1. **A real `LabelBlockSource` data directory under the decided policy:**
>      - loads, with `manifest["cross_split_duplicates"] == "heldout_excludes_seen"` and kind `label_block`;
>      - the policy is added to the returned copy only; `sft_data.json` on disk is unchanged, so the data sha and resume binding are unaffected;
>      - `run_stage_s` with `duplicate_policy=` records the policy and the rule text.
>   2. **Edge cases:**
>      - labels without `kind` and a non-decided policy: refused (fail closed);
>      - `splits.json` with `"config": null`: treated as `drop_from_train` and refused;
>      - `splits.json` edited without re-hashing: refused by the sha check first, so the policy cannot be changed on disk silently.
> - **Round-1 probe 2, rerun:** a `drop_from_train` data directory run through `run_stage_s` without a policy now gets `heldout_rule = None`. The probe's old assertion (that the rule text is present) fails as intended, which confirms the M1 fix. The other two round-1 probes still pass. Output is in `/tmp/sftrev/probe/probe_r2_out.txt`.
> - **Report §4 against the coordinator's logs** in `/tmp/sftwork`:
>
>   | log | failed | passed | skipped |
>   |---|---|---|---|
>   | `full_b5017.log` | 54 | 2,538 | 195 |
>   | `full_dup.log` | 54 | 2,541 | 195 |
>   | `full_dup2.log` | 54 | 2,542 | 195 |
>
>   - The failing ids are identical in all three: I compared the sorted `FAILED` lines of `full_b5017.log` and `full_dup2.log`, and the existing `fail_b5017.txt` and `fail_dup.txt`.
>   - The deltas match the added test functions: 3 in 11599ae6 and 1 in 480031a7.
>   - I cannot verify from the logs themselves which commit each was run at.
>
> ## Round-1 findings: status
>
> | # | round-1 finding | status | verification |
> |---|---|---|---|
> | M1 | `sft-dev` accepted data directories with an earlier policy and stamped the decided rule on them | **fixed** | See "How M1 is fixed" after the table. |
> | M2 | no CLI-level test of the policy refusal | **fixed (consumption side)** | See "How M2 is fixed" after the table. |
> | N1 | "seen" uses all table rows | **addressed** | The `sft_data` docstring and report §3(4) now state it, with the sweep-1 equality 47 / 74. |
> | N2 | test strength | **fixed** | The two-run equality now also covers `temperature`, `train_config_sha256`, `total_steps`, `selected_temperature_scaled` and `train.best_step`. |
> | N3 | small items | **addressed** | The `trackp.py` comprehension is wrapped, and report §3(1) states 77. `SFT_DATA_SCHEMA` is not bumped; that was optional and older readers fail closed. |
>
> ### How M1 is fixed
>
> - `load_sft_data` reads `config.cross_split_duplicates` from the hash-verified `splits.json` bytes. A missing field means `drop_from_train`, the base default.
> - The check runs before any row is parsed, for both the `secondary=False` and `secondary=True` forms.
> - It refuses any policy other than the decided one unless `manifest.labels.kind == "synthetic"`, and puts the policy into the returned manifest.
> - `_stage_s` passes it on as `duplicate_policy`. `run_stage_s` records `cross_split_duplicates` and writes `heldout_rule` only for `heldout_excludes_seen`.
> - The policy is report-only: it is not in `TrainConfig`, so the digest and selection are unchanged.
> - Tests:
>   - the unit test `test_load_refuses_an_earlier_policy_with_real_labels` covers synthetic allowed, real refused, and a missing field;
>   - the `sft-dev` STOP case in `test_cli_dry_run_end_to_end` covers the CLI path;
>   - the CLI test also asserts the recorded policy and rule.
> - `SFTDataError` is a `ValueError`, so the CLI converts it to a STOP.
>
> ### How M2 is fixed
>
> - The CLI refusal is now tested at `sft-dev` time.
> - Your reason for not testing the `sft-data` build path through the CLI is correct: real labels require a pinned table and the pool tokenizers, which this environment cannot provide.
> - The build-time refusal is still unit-tested directly, and the CLI path to it is a straight call that I verified by reading the code in round 1.
>
> ## New findings
>
> No BLOCKING, MAJOR or MINOR findings.
>
> ### N1. NOTE — the decided-policy name is a string literal in `sft.py`
>
> - **Location:** `r1/c3/train/sft.py:148`, `if duplicate_policy == "heldout_excludes_seen"`.
> - **What:** this duplicates `sft_data.DECIDED_DUPLICATE_POLICY`. If the constant were ever renamed, the rule text would silently drop to `None`. Today the CLI test catches that, because it asserts `heldout_rule` starts with "R1-TRACKP-SFT-DUP".
> - **Fix (optional):** import the constant. `sft.py` does not import `sft_data` today, but `sft_data` does not import `sft` either, so there is no import cycle.
>
> ### N2. NOTE — direct callers of `run_stage_s` get no rule text unless they pass the policy
>
> - **What:** this is correct behaviour; the rule is no longer claimed without evidence. Note that `test_stage_s_reports_secondary_full_heldout` and other direct callers now produce reports with `cross_split_duplicates: null` and `heldout_rule: null`, even when they pass `val_secondary`.
> - **Fix (optional):** none needed. A future P.4 runner should pass `dm["cross_split_duplicates"]` the way `_stage_s` does.
>
> ### N3. NOTE — cosmetic
>
> - The edited `sft_data` docstring paragraph has two short ragged lines ("…both when a / data directory is built and when it is loaded): every train / row is kept…").
> - One new test line is 124 characters.
>
> ## Conclusion
>
> Both round-1 minors are fixed and tested:
> - a data directory built under an earlier policy can no longer be trained with real labels, at build time or at load time;
> - the report no longer claims the decided rule for data that did not follow it.
>
> The notes are addressed. The secondary rows still cannot influence selection, and the policy is report-only. The report's §1–§4 match the code and the coordinator's full-suite logs: the same 54 environmental failures on base 50176481, 11599ae6 and 480031a7.
>
> ## Scratch artefacts
>
> - `/tmp/sftrev/review_dup_r2.md`: this review.
> - `/tmp/sftrev/probe/test_probe_dup_r2.py`, plus the earlier probes, and `probe_r2_out.txt`.
> - `/tmp/sftrev/fail_dup2.txt` and `/tmp/sftrev/fail_b5017_mine.txt`: the failing-id lists I extracted for the §4 check.

---

## Open points for the author

Report §3: "seen" for test includes val (the only reading that reproduces the decision's 74; train only gives 77);
no test evaluator exists yet (P.4 must read `splits.json`'s exclusion list for the primary test number); "seen" uses
every table row of a train/val instance (same populations on sweep 1). The round-2 notes (the policy name as a string
literal in `sft.py`; direct callers of `run_stage_s` must pass the policy; two ragged docstring lines) are left as
they are.

---

Code-Commit: 1f9e82324b3d2e89f5128de30caef864b59757a4
Verdict: ACCEPTED

Accepted commit: `1f9e82324b3d2e89f5128de30caef864b59757a4` (round 2).
