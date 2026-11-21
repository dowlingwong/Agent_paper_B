Reviewed base: `2f5f4093` (the accepted gate-input builder unit on `mac-p3-split-20261121`, over published `main` `f6baf12c`); accepted at `275d7dcb2e825cf9a4a3e82b462fe23f6c35a453`

# Independent review record — the release step and partition-reading locks (PRE-STAGE A) and the §8 release-row drafts

**Unit.** On `mac-release-20261121`: `r1/c3/release.py`, `r1/c3/release_checks.py`, locks in `r1/c3/audit.py`, `offline_eval.py`,
`env.py`, `ni_masking.py`, `train/sft_data.py`; autouse fixtures in four reader test modules; `r1/tests/test_c3_release.py`;
`docs/r1/proposals/R1_LABEL_RELEASE_ROWS_DRAFT_20261121.md` (approved: false); `docs/r1/reports/release_20261121/RELEASE_20261121.md`.
Authority: the signed preregistration (R1-SWEEP2-PREREG) PRE-STAGE A, §4, §6 (integrity carve-out), §8, §9; the queue of 21 Nov 2026,
item 3.

**Process.** One independent reviewer for all four rounds, read-only, synthetic data only, scratch under `/tmp/rev_rel/` moved to its
`_to_delete/`. Round 1 found unlocked readers of B.2 run logs and legacy `audits.jsonl` (blocking) and six majors; round 2 found the
integrity-check module unbound to published bytes and a freeze-parse bypass; round 3 accepted with four minors (fixed in `275d7dcb`);
round 4 confirmed. The author's agent's unrelated work was kept out of the reviewed worktree from round 2 on.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `f998ced6` | NOT ACCEPTED (B1; M1–M6; m1–m11) |
| 2 | `2461912c` | NOT ACCEPTED (R2-M1, R2-M2; m-a–m-g) |
| 3 | `ebf007f5` | ACCEPTED (n1–n4) |
| 4 | `275d7dcb` | CONFIRMED |

**Open items.** Author points in the drafts: REL-SCOPE, REL-CODE, REL-T1-G1B; conditions before use (sweep-2 and G.5 integrity checks, G.5 extraction and completion schema, G.1b copy-out, the exact freeze-block format). Cosmetic (round 4): the n4 test does not isolate the arms record alone; the code was confirmed by the reviewer's probe.

## Round 1 (`f998ced6`)

> **Verdict: NOT ACCEPTED.** This covers commit f998ced6 against parent 2f5f4093, in worktree /tmp/pb/wt/gatebase. The reason is one blocking finding and several major ones, listed below.
>
> I worked read-only and used synthetic data only. I opened no real label table, audit file, sealed path or secret. The worktree is still clean.
>
> **Test runs**
> - The command you gave: 307 passed, 1 skipped.
> - I also ran the parent commit's versions of four test modules against the new code, which is the same as removing the autouse fixtures. 21 tests fail:
>   - 20 fail because the new lock fires on the raw path, which is the expected effect.
>   - 1 (`test_evidence_preflight_import_has_trackable_package_origin`) fails only because I ran the file from a different directory.
> - Probe tests I wrote for the row and freeze checks and for the locks are described in the findings.
>
> ## BLOCKING
>
> **B1. Evaluation values (all instances, test included) can still be read before the test release row, through unlocked readers in this repository.**
> - `audit.RunCache` (r1/c3/audit.py:299–309) reads any `runs.jsonl` with no lock. It is used by `audit collect`, `audit run` and `resolve_seeds` (audit.py:360, 392, 1225).
> - `audit collect --plan B2/plan.jsonl --out B2/` reads the B.2 `runs.jsonl` and writes a legacy `audits.jsonl` containing every seed 7001–7010.
> - `guard_raw_label_path` (release.py:279–282) keys on the bare file name, and `audits.jsonl` is not in `RAW_NAMES`. So `ni_masking.load_audits(table, B2/audits.jsonl)` returns everything.
> - `offline_eval.assemble` and `env.label_rows` do the same for a table whose build.json is not EVIDENCE. For EVIDENCE tables they are saved only because `verify_evidence_completion` is locked.
> - Copying or symlinking `label_block.jsonl` to any other name also gets past the name check.
> - I reproduced this synthetically: with only the D8 row present and no release row, `load_audits` returned the evaluation-seed metrics.
> - The module docstring (release.py:25–28) and the report both claim `runs.jsonl` is refused. The report's line "Pilot audits.jsonl tables keep their path" in fact exempts every `audits.jsonl`.
> - **Fix:**
>   - Lock `RunCache.__init__` whenever the file exists and is not empty, unless inside `integrity_context` or an explicit producer context for `evidence_run` or `run_plan` on a fresh directory.
>   - Make `audit collect` refuse an output directory that holds `evidence_completion.json` or `label_block.jsonl`.
>   - Make `guard_raw_label_path` resolve symlinks and refuse any file in a B.2 audit directory (one containing `evidence_completion.json`), including `audits.jsonl`.
>   - Add these readers to `test_locks_on_the_existing_readers`, with the audit hook asserting nothing was opened.
>
> The other readers I found:
> - **Locked:** `LabelBlockSource` (sft_data.py), `assemble`, `label_rows`, `load_audits` and `verify_evidence_completion`, but only for the three raw file names.
> - **Indirectly safe:** `gate_input_builder` gets its data only through `builder_source`; Track P (`trackp.py:319`) goes through `LabelBlockSource`.
> - **Not B.2 label data:** the `sweep2/g1b`, `t1_tasl` and `r1/noise` `runs.jsonl` readers.
> - **Out of PRE-STAGE A scope:** the legacy-pilot `audits.jsonl` (`c3_control_dryrun`, `test_trackp_soft_label_v2`), which is pre-sweep pilot data.
>
> ## MAJOR
>
> **M1. The freeze check can be fooled** (release.py:194–211).
> - It parses every `key: value` line in the whole prereg, and the last occurrence wins. I confirmed three ways through:
>   - The block says `frozen: false`, but a `frozen: true` line added after the code fence passes.
>   - If the block lacks a key, an indented or prose line elsewhere supplies it.
>   - `split_file: <pending: … b5967dd7… >` passes, because the check is only a substring test.
> - On the current prereg (lines 300–318) only the block's lines match, so nothing is wrong today. The check is still not robust.
> - **Fix:** parse only the single final fenced block; require each key exactly once; fullmatch `split_file` against the expected path and sha; also require `pre_stage: A`.
>
> **M2. Any change to release.py invalidates every existing receipt and the T0 row.**
> - `release_row` requires the cited commit's release.py to equal HEAD's (release.py:232–239), and `open_partition` re-checks this on every open.
> - Registering the sweep-2 or G.5 integrity check edits `INTEGRITY_CHECKS` inside release.py. The draft and the report both say this must happen later.
> - I confirmed it: after one edit, opening the sweep-2 traindev partition stops with "release-code commit has other bytes". Re-releasing then hits "a release is written once".
> - A T1-only change also breaks T0.
> - **Fix (pick one):**
>   - Move the integrity checks into a separate module that the receipt binds per source, and check release.py bytes at the receipt's own `release_commit` rather than at HEAD.
>   - Or require all checks to be registered before the first row.
>   - Or use one row per source.
>
>   The drafts should flag this as an author decision.
>
> **M3. Receipts certify themselves** (release.py:385–409; sft_data.py `_load_partition`).
> - I replaced `label_block.traindev.jsonl` with the full block, test rows included, and edited `outputs` in RECEIPT.json to match.
> - `open_partition` and `LabelBlockSource` both accepted it (1440 of 1440 rows).
> - Hand-edits to `integrity.completion` are likewise not detected.
> - **Fix:** on open, re-derive P3 membership of every row from the table (pass `table_dir`, or check in `build_sft_data`, which already has the rows), and/or record each receipt's sha256 in a committed release record that readers verify.
>
> **M4. The T1 lock defaults to the T0 row** (release.py:270, 279).
> - Every existing reader calls `guard_raw_label_path(path)` with tier T0.
> - Once R1-S2-LABELS-TEST-RELEASE exists, a raw G.5 block opens even though R1-T1-LABELS-TEST-RELEASE does not. I confirmed this.
> - **Fix:** derive the tier from the table's provenance, or fail closed by requiring the test row of every tier.
>
> **M5. The §8 T1 train/dev draft omits a binding the signed PRE-DELTA requires.**
> - PRE-DELTA says each T1 node's G.1b summary "path and sha256 [are] recorded in the T1 train/dev release row, before any training".
> - R1-T1-LABELS-UNSEAL (draft, and `row_pattern`) has no room for this.
> - PRE-DELTA also says "on H200", while R1-T1-HOST-TASL moved G.1b to TASL. That is for the author to settle.
> - **Fix:** add the G.1b summary binding to the T1 traindev template and check its sha256.
>
> **M6. The fixtures are justified, but they hide a coverage gap.**
> - The five fixtures make the raw path behave as it will after the test release; they do not hide a functional regression.
> - The cost is that every refusal test (STOP.json, seeds, sha, schema, extra keys, sweep binding, index and classification) now covers only the raw path, which cannot be used before release.
> - The partition path, which is what Track P will actually use before release, has one happy-path test. None of its refusal branches is tested: stage or source mismatch, no completion, seeds, label_block sha, derived sweep, index, classification (sft_data.py `_load_partition`).
> - **Fix:** run the refusal tests over the partition path as well.
>
> ## MINOR
>
> - **m1. Mismatched label block at test release** (release.py:320–323). The test release does not check the label block and proposals sha256 against the traindev receipt. I confirmed a different label block is accepted; `builder_source` catches it later. Add the check in `release()`.
> - **m2. Inputs read several times** (release.py:328–371). The label block is read three times: by the integrity check, by `_lines`, and to hash it. Read once, compare to the completion's `label_block_sha256`, and partition those bytes; do the same for the evaluation block.
> - **m3. `verify_row=False` bypass** (release.py:385). `open_partition(..., verify_row=False)` is public and opens a test partition without the test row; I confirmed this. Remove the parameter or make it private.
> - **m4. No source/stage check in readers** (release.py:412–436). `traindev_labels` and `builder_source` do not check that `receipt["source"]` and `stage` match the directory.
> - **m5. Original exception kept** (release.py:329–330). `raise … from None` still leaves `__context__` holding the original exception and its message. Raise outside the `except` block instead.
> - **m6. Errors escape as the wrong type** (release.py:106–124, 233–237). Only `OSError` and `CalledProcessError` are caught, so `UnicodeError`, `ValueError` and `AttributeError` escape as something other than `ReleaseStop`. Under a test that patched `check_output` to return text, I saw an `AttributeError` at release.py:118. This still fails closed, but `test_released` raises instead of returning False. Catch errors as `analysis_guard` does.
> - **m7. Commit and HEAD checks.** The row's commit is checked only as an ancestor, though the draft says "published commit" (`origin/main`). HEAD stability across the several `rev-parse` calls is not checked, unlike `require_d8_confirmation`.
> - **m8. No D8 check on partition readers.** `open_partition` and `traindev_labels` for sweep-2/g5 partitions do not call `require_d8_confirmation`, and the new readers are not in `test_d8_sweep2_reader_refusal_matrix.py`.
> - **m9. Test hygiene and gaps** (test_c3_release.py).
>   - Line 269: `sys.addaudithook` is permanent and its list grows without bound.
>   - Lines 282–285: the `assemble` and `load_audits` refusals do not assert that nothing was opened.
>   - Missing refusal cases: a row in a code fence, comment or indented block; a row under a non-author heading; a mismatched gate in the prereg; T1 text in a T0 row. My probes show all of these fail closed today.
>   - `_sweep1_integrity` itself is never exercised (the tests replace it with a fake).
> - **m10. One fixture has no effect.** The fixture in test_trackp_soft_label_v2.py does nothing, since the pilot uses `audits.jsonl`. The report's claim that all five modules exercise the raw readers is inaccurate for this one.
> - **m11. Author points for the drafts.**
>   - The test row lifts every raw lock for every reader, whereas the G.5 draft says the test partition goes "to the gate run only".
>   - G.5 outputs live in a sealed tar, and `release()` refuses sealed paths, so a T1 release needs an unseal/extract step that this design does not cover.
>
> ## What holds
>
> - **`author_rows` mirrors `analysis_guard._confirmation_commit`** line for line: fences, HTML, comments, indented code, the §10 and dated-author rules, header strength and column count. It finds the same V31 row on the real PLAN.
> - **Probes on the row check:** all of these were refused:
>   - rows in a fence, a comment or indented code;
>   - rows under a non-author heading or outside §10;
>   - near-miss text (trailing words, wrong scope);
>   - traindev text in a test row, T1 text in a T0 row;
>   - a short commit, an uncommitted PLAN;
>   - a different gate or builder, split or prereg sha;
>   - a release.py commit with different bytes.
> - **Partitions** hold exactly the train+dev label lines (byte-identical, reordered).
> - **No value leaks** through receipts, the CLI print, or integrity output (counts by label_kind are audit/rule_noop only). The one exception is m5.
> - **§6 carve-out:** `verify_evidence_completion` is locked before it opens anything, except inside `integrity_context`.
> - **Robustness:** a leftover `.partial` directory STOPs, re-runs STOP, stage order is enforced, and sealed paths are refused. Symlinked partition directories are accepted, but this matters only together with M3.
> - **§8 drafts:** they cite the prereg sha256 at freeze; the test rows cite the arms-frozen record path and sha256; the split sha matches `P3_SPLIT_SHA256`. They are correctly marked as not author decisions, apart from the flags in M2, M5 and m11.
>
> Scratch (probe tests, the parent-commit test copies, TMPDIR) has been moved to /tmp/rev_rel/_to_delete/. Nothing was deleted.

## Round 2 (`2461912c`)

> **Round 2 verdict: NOT ACCEPTED.** This covers commit 2461912c, reviewed against f998ced6 in worktree /tmp/pb/wt/gatebase, which I left clean at 2461912c. Every round-1 finding is fixed. Two major points remain, both with small fixes, and one of them is a regression caused by the M2 fix.
>
> **Tests**
> - The eight modules you listed (32 tests in test_c3_release.py): 325 passed, 1 skipped.
> - Other synthetic modules that touch the newly locked readers: 92 passed, 12 skipped, 1 deselected. These were test_audit_preservation, test_c3_analysis_guard, test_c3_audit_dryrun, test_c3_ni_masking, test_c3_evidence_split_blocks, test_c3_rule_controller, test_d28_noise_binding, test_d8_legacy_verdict, test_c3_arms_eval and test_c3_audit.
>   - I deselected `test_c3_audit::test_committed_pilot_audits_still_split_3_plus_3` because it reads the committed pilot's `runs.jsonl`.
>   - I did not run test_trackp_soft_label_v2 or test_c3_prior_model, because both read the real pilot `audits.jsonl`.
> - My synthetic probes are described with each finding below.
>
> ## MAJOR
>
> **R2-M1. The integrity-checks module is not bound to reviewed, committed bytes** (release.py:413, 432–442, 489; release_checks.py).
> - This module is the code that runs with the lock open inside the §6 carve-out. In round 1 it was inside release.py, so the row's commit check covered it.
> - Now `release()` never checks it. There is no `_committed(CHECKS_PATH)`, no check against origin/main, and no check that `release_checks.__file__` is the repository's file.
> - The receipt records the sha256 of whatever module was imported, but nothing ever compares that hash to anything.
> - So an uncommitted local edit to release_checks.py, such as a check that simply passes, runs with the lock open and still produces a receipt that looks valid. "Clean checkout of a published commit" is only stated in the draft; nothing enforces it.
> - **Fix:** in `release()`:
>   - require `_committed(CHECKS_PATH)`;
>   - require HEAD's blob of release_checks.py to equal the blob at `refs/remotes/origin/main`;
>   - require `Path(release_checks.__file__).resolve() == (REPO / CHECKS_PATH).resolve()`;
>   - record the published commit and blob id in the receipt.
>   - Add a refusal test with a dirty or unpublished release_checks.py.
>
> **R2-M2. `_final_block` uses the last fenced block in the file, even when it comes after the real decision block** (release.py:231–245, 251–253).
> - I confirmed two bypasses, each with a real block saying `frozen: false`:
>   - An appendix fenced block after it, holding the would-be frozen block ("the block as it will read after freeze"), is accepted as frozen.
>   - The same block wrapped in `<!-- ``` … ``` -->` after the real block is also accepted.
> - **Fix:**
>   - Require the final block to be the last non-blank content of the document.
>   - Ignore fences inside HTML comments, using the same comment handling as `author_rows`.
>   - Optionally, require the block's key set to be exactly the signed set (all `pre_*` keys plus `signed_by`).
>   - Add both cases to `test_release_row_and_freeze_refusals`.
>
> ## MINOR
>
> - **m-a. Seed journals in an evidence directory are not locked** (release.py:377–388; audit.py:305–308).
>   - `is_evidence_dir` looks only at the immediate parent directory.
>   - `B2/seed_journals/<id>.jsonl` holds per-seed metrics for every seed. `audit.RunCache` on such a file read all ten seeds, 7006–7010 included, before any release row; I confirmed this.
>   - No reader in the repository opens seed journals today.
>   - **Fix:** treat a path as protected if any ancestor directory holds a marker, and add a test.
> - **m-b. `RunCache` assumes tier T0** (audit.py:308).
>   - I confirmed that a run log in a G.5 evidence directory opens once only the T0 test row exists.
>   - `RunCache` cannot know the tier, so pass `None` to fail closed, or derive the tier from the completion record.
> - **m-c. A check result without the hash is accepted** (release.py:444, 461).
>   - `completion.get(...) not in (None, sha)` lets a check that returns no `label_block_sha256` (or, at the test stage, no `evaluation_block_sha256`) through. I confirmed this with a check that returns `{}`.
>   - Require both hashes to be present.
> - **m-d. The M6 tests do not reach the reader branch for the label-block hash** (test_c3_release.py:446–453).
>   - The loop accepts a refusal by the writer as well as by the reader.
>   - The label-block-hash case is refused by `release()` (the m2 check), so the reader's own "the receipt's completion binds another label block" branch in `_load_partition` stays untested.
>   - Assert per case which side refuses, and test the reader branch with a hand-edited receipt.
> - **m-e. REL-CODE A covers only edits to the checks module.**
>   - After any edit to release.py, a new write under the same row (for example the sweep-2 traindev after sweep 1) is impossible.
>   - Amending the row to a new commit changes `decision_sha256` and `release_commit`, which voids every earlier receipt.
>   - State this in the REL-CODE text.
> - **m-f. Not enforced:**
>   - The draft asks for "a clean checkout of a published commit that contains the rows", but only the release.py commit is checked against origin/main. The PLAN commit and the cleanliness of the checkout are not checked.
>   - Other code that runs when a release is written is not bound by the receipt: `audit.verify_evidence_completion` and `dataset.load_table`. `p3_split` is bound, because the split file is regenerated and compared.
> - **m-g. Conditions to note in the drafts, not code defects.**
>   - With `tier=None`, `offline_eval`, `env` and `ni_masking` stay locked for good if no T1 test row is ever written. This is fail-closed; it belongs in REL-SCOPE.
>   - PRE-DELTA speaks of "sealed" G.1b summaries, but `_committed` refuses sealed paths and requires the summaries to be committed. The summaries therefore need a reviewed copy-out first; add this to REL-T1-G1B.
>
> ## What holds
>
> - **B1:**
>   - `guard_raw_label_path` now resolves symlinks and locks evidence directories.
>   - `RunCache` locks a non-empty log in an evidence directory.
>   - `audit run` and `collect` refuse an evidence directory.
>   - `evidence_run` reads back its own log only inside `producer_context`.
>   - My round-1 `collect` → `audits.jsonl` route is now refused.
>   - The legacy pilot directory has no evidence markers (I checked file names only), so pilot readers keep working.
> - **M2 readers, M3, M4 and M5:**
>   - Readers now bind each receipt to its own release commit.
>   - P3 membership is re-derived from the proposal id's instance. The real sweep ids, `{source}:{instance}:t{b}` with an instance of the form `<node>__s<seed>`, fit `_instance_of_pid`, and `release()` refuses any mismatch.
>   - My tamper case is refused by both `open_partition` and `LabelBlockSource`.
>   - `tier=None` fails closed.
>   - The T1 row binds the committed G.1b summaries.
> - **The minors:**
>   - m1 to m11 are verified in the code. In particular, `__context__` is None, `test_released` returns False when git misbehaves, and the D8 check runs before anything is opened.
>   - The fixture that did nothing in test_trackp_soft_label_v2 is removed.
> - **The drafts** now carry REL-SCOPE, REL-CODE, REL-T1-G1B and the G.5 extraction condition, all correctly marked as not author decisions.
>
> Scratch is in /tmp/rev_rel/_to_delete/: probe2/ and t2/ from this round, plus probe/, oldtests/ and t/ from round 1. I deleted nothing.

## Round 3 (`ebf007f5`)

> **Round 3 verdict: ACCEPTED.** This covers commit ebf007f5 on mac-release-20261121, reviewed with `git diff 2461912c ebf007f5`. The worktree is clean at ebf007f5. Both round-2 majors are fixed, and so are m-a through m-g. Four minors remain; none blocks acceptance.
>
> **Tests**
> - The 40 tests in test_c3_release.py plus 17 reader modules: 425 passed, 13 skipped, 1 deselected. The reader modules were:
>   - the eight from rounds 1 and 2: test_trackp_sft, test_c3_evidence_seed_isolation, test_c3_evidence_guards, test_c3_evidence_attestation_stop, test_d8_sweep2_reader_refusal_matrix, test_c3_env, test_c3_offline_eval_guard_order;
>   - test_audit_preservation, test_c3_analysis_guard, test_c3_audit_dryrun, test_c3_ni_masking, test_c3_evidence_split_blocks, test_c3_rule_controller, test_d28_noise_binding, test_d8_legacy_verdict, test_c3_arms_eval and test_c3_audit.
> - The deselected test is `test_c3_audit::test_committed_pilot_audits_still_split_3_plus_3`, because it reads the real pilot's run log.
> - I also ran the new freeze parse on the real signed prereg, which is a document only. It gives exactly the 19 signed keys, each once, with every decision matching `SIGNED_DECISIONS`. `prereg_frozen` correctly refuses it, because it is still `frozen: false`.
>
> ## How the round-2 findings were checked
>
> **R2-M1: the integrity checks are now bound** (release.py:469–489, 513, 571–572). `_published_clean` checks four things:
> - `release_checks.__file__` resolves to the repository's `release_checks.py`;
> - that file is the committed one;
> - the tracked checkout is clean;
> - the listed paths have no diff against origin/main. That list covers the checks module, `audit` (which holds `verify_evidence_completion`), `dataset`, `p3_split`, the split file, the gate, the builder, PLAN and the prereg. A missing origin/main makes git return 128, which is refused.
>
> A check result without the label hash (or, at the test stage, the evaluation hash) is now refused.
>
> **R2-M2: the freeze check is robust** (release.py:240–282). I re-derived these cases:
> - HTML comments are stripped first. My commented-block bypass now meets the visible `frozen: false` block and STOPs.
> - Exactly one fenced block may hold a `frozen:` line, so an appended example block makes two and STOPs.
> - That block must end the document.
> - Fake blocks with a different fence style, or nested in a four-backtick fence, still count as a second block and STOP.
> - The key set must be exactly the signed one, with the signed decision values.
>
> **m-a, m-b, m-d:**
> - `evidence_root` walks every ancestor, both the lexical and the resolved path. Seed journals are now locked and tested.
> - `RunCache` takes its tier from the completion schema; a directory of unknown tier needs both test rows.
> - In the M6 tests, writer refusals and reader refusals are now asserted separately. The reader's "binds another label block" branch is tested through a hand-edited receipt.
>
> **m-e, m-f, m-g** are written into the drafts and the report: the release.py and REL-CODE limit, the published-and-clean list, the permanent `tier=None` lock under REL-SCOPE, and the G.1b copy-out under REL-T1-G1B.
>
> ## MINOR (non-blocking)
>
> - **n1. Untracked shadow modules are not refused** (release.py:479–483).
>   - `git status --untracked-files=no` ignores untracked files, and only `release_checks.__file__` is checked against the repository path.
>   - An untracked package such as `r1/c3/audit/__init__.py` would shadow `audit.py` while the status and diff checks still pass. This needs a deliberate act.
>   - **Fix:** also check `__file__` for `audit`, `dataset`, `p3_split` and `analysis_guard`, or refuse untracked files under `r1/`.
> - **n2. A G.5 audit could be treated as T0** (release.py `evidence_tier`).
>   - The tier is inferred from the `r1.c3_audit_completion/` schema prefix. A G.5 audit that reuses `audit.evidence_run`'s schema would count as T0, so its run log would open with only the T0 test row.
>   - **Fix:** bind the tier to the index sha (the sweep-1 or sweep-2 index) or to an explicit tier field, or state this in the G.5 conditions.
> - **n3. One test does not isolate what it names** (test_c3_release.py, the `unpublished_checks` case).
>   - It moves origin/main back past the PLAN commit as well, so it does not show that a difference in `release_checks.py` alone is refused.
>   - Add a case where only `release_checks.py` differs from origin/main.
> - **n4. Two cited files are checked as committed but not published.**
>   - The arms-frozen record and the G.1b summaries are checked against their committed bytes, but they are not in `PUBLISHED_PATHS`.
>   - Adding them is optional; it would match the "published" rule applied to PLAN and the prereg.
>
> Scratch from all three rounds is in /tmp/rev_rel/_to_delete/ (oldtests, probe, probe2, t, t2, t3). I deleted nothing.

## Round 4 (`275d7dcb`)

> **CONFIRMED.** Commit 275d7dcb (checked with `git diff ebf007f5 275d7dcb`) closes all four round-3 minors, and the unit stays ACCEPTED. The worktree is clean at 275d7dcb.
>
> **Tests:** I ran `test_c3_release.py` (41 tests) together with the same 17 reader modules as in round 3: 426 passed, 13 skipped, 1 deselected. The deselected test is `test_c3_audit::test_committed_pilot_audits_still_split_3_plus_3`, because it reads the real pilot's run log.
>
> **How each fix was checked:**
> - **n1 (shadowing packages):** `_published_clean` (release.py:475–487) now requires `analysis_guard`, `audit`, `dataset` and `p3_split` to be the plain `.py` files in the same folder as `release.py`. A shadowing package is refused, and this is tested.
> - **n2 (G.5 tier):** the `evidence_tier` docstring and the drafts now say a G.5 writer must use its own completion schema. This was a condition to state, not a code change, and it is now stated.
> - **n3 (unpublished checks):** the `unpublished_checks` case now commits only a `release_checks.py` change after publication. So it isolates a checks-only difference from origin/main.
> - **n4 (cited files published):** the arms-frozen record and the G.1b summary paths are now passed into the published-diff check (release.py:523–525). I confirmed it with a probe of my own:
>   - I arranged the history so the arms-frozen record was the only file differing from origin/main.
>   - The test release was refused as "not published".
>   - After publishing, it went through.
>
> **One cosmetic point, non-blocking:** the new test `test_cited_files_must_be_published_and_modules_not_shadowed` (test_c3_release.py:511–518) does not isolate n4.
> - Its unpublished commit changes both the arms record and PLAN, so the refusal could come from PLAN alone.
> - The regex also accepts either refusal message.
> - The code is correct, as my probe shows. If you want, publish a PLAN that already cites the new arms sha first, then commit only the arms record.
>
> Scratch from all four rounds is in /tmp/rev_rel/_to_delete/ (oldtests, probe, probe2, probe4, t, t2, t3, t4). I deleted nothing.

---

Code-Commit: 275d7dcb2e825cf9a4a3e82b462fe23f6c35a453
Verdict: ACCEPTED

Accepted: the release step, partition readers and locks at `275d7dcb`; the §8 rows remain drafts (approved: false).
