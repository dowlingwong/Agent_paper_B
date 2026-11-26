Reviewed base: `a9d8ff5e` (the accepted release-step unit `275d7dcb` plus its record, over the accepted builder unit `2f5f4093` and published `main` `f6baf12c`); accepted at `84b86b83586e7461c7080f1785385f920bd261d7`

# Independent review record — Track P evidence builds on P3 (PRE-SPLIT A) and the P.3b exam set inside P3 train

**Unit.** On `mac-trackp-p3-20261121`: `r1/c3/train/sft_data.py` (`split_file` mode, `SIGNED_SPLIT_FILE`, `p3_universe`,
real labels fail closed at build and load), `r1/scripts/configs/trackp_sft.json` (splits bound to P3), `r1/scripts/trackp.py`
(pinned tables only on the signed file), `r1/c3/train/exam_set.py` (membership file, pinned table, source bound to the pin,
label-join check), `r1/tests/test_trackp_p3.py` (23 tests), `r1/tests/test_trackp_sft.py`, `r1/tests/test_p3_split.py`, and
`docs/r1/reports/trackp_p3_20261121/TRACKP_P3_20261121.md` (EX-SOURCE, EX-DUP, EX-SPLIT, EX-STOP, EX-NOOP, EX-ROUND).
Authority: the signed preregistration (R1-SWEEP2-PREREG) PRE-SPLIT A, §6, §9; R1-MAIN-PROPOSER-ITEMS (h); the queue of 21 Nov
2026, item 5.

**Process.** One independent reviewer for three rounds, read-only, synthetic records only (B.2's report and totals only), scratch
under `/tmp/rev_tp3/` moved to its `_to_delete/`. Round 1 found the P.4 evaluator's recomputation refused by the split-file mode
(blocking), no fail-closed guard against `trackp_sft/v1` with real labels, a misquoted EX-SOURCE and unstated scientific
choices; round 2 accepted with three optional nits, fixed in `84b86b83`; round 3 confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `867a53e5 / 04e9dc7f` | NOT ACCEPTED (B1; M1–M3; m1–m8) |
| 2 | `d70df3ca` | ACCEPTED (n1–n3, optional) |
| 3 | `84b86b83` | CONFIRMED |

**Open items.** Author decisions in the report: EX-SOURCE (recommended A, sweep 1 disclosed until sweep 2 exists), EX-DUP, EX-SPLIT, EX-STOP, EX-NOOP, EX-ROUND. Before the P.4 draft merges, its P4-P1SPLIT A text must drop the salt-mode wording (its evaluator already passes on a P3 build). The arms-frozen record must disclose the exam set's provenance ("first drawn after the signature, within P3 train") and the earlier `trackp_sft/v1` engineering uses. Cosmetic (round 3): `from_table` hashes the SFT config from a second read.

## Round 1 (`867a53e5 / 04e9dc7f`)

> **Verdict: NOT ACCEPTED.** There is 1 blocking finding and 3 major ones. All of them have small fixes.
>
> The default path is correct. With the shipped config, every pinned `sft-data` build uses the signed P3 file. That file is checked by sha256 and against the generator's output. A salt, counts or a separate universe given beside it is refused, and so is an instance outside it. `holdout_nodes` is handled correctly: whole nodes go to test, the other nodes keep P3, and an unknown node is refused. The unpinned dry run is safe, because `--table-pin none` still requires `--labels synthetic` (trackp.py:297-300). The exam set lies inside P3 train (T0) and reads only table rows, never a label or evaluation value. The problems are an integration break with the P.4 draft, a missing fail-closed guard, and an author-decision framing that misquotes the adopted text.
>
> **Runs**
> - The three requested files: 59 passed.
> - The other 11 `test_trackp_*` modules, run once on this commit: 20 failed, 109 passed, 70 skipped. This matches the report's figure of 20. The causes I sampled are environmental (missing `kev` and `lightgbm` modules, a gzip/zlib byte difference). None of these modules touch the changed code. I did not run the parent.
>
> ---
>
> ### BLOCKING
>
> **B1. The P.4 evaluator refuses every P3 build, so the report's P.4-prerequisite claim is false (report:27-29, sft_data.py:493-496).**
> - In `mac-trackp-p4-20261120`, `sft_test_eval._check_assignment` always calls `SD.assign_splits(union, splits["config"], universe=union)`. In split_file mode, `assign_splits` refuses any universe.
> - I checked this by running it. A synthetic `build_sft_data(split_cfg={"split_file": ...})` followed by the P.4 `_check_assignment` gives `TestEvalError: the recorded split config cannot be recomputed: split_file excludes a separate universe`. The same code is on `mac-trackp-p4-h200-20261121`.
> - The draft's P4-P1SPLIT A (and its §3 "over the fixed instance universe", key value `split: c3_p3_split/v1 9/3/6`) describes the salt mode plus universe. This config no longer offers that mode, and split_file mode refuses it.
> - So the claim "once merged, its runner can bind the same file through this split_file mode" does not hold.
> - **Fix:** in `assign_splits`' split_file branch, accept a `universe` exactly equal to the file's instance set and refuse any other. Alternatively, have `_check_assignment` omit `universe` when `split_file` is in the config. Add a test that runs the P.4 recomputation on a split_file build. Correct the report: the P.4 draft's A text and its evaluator need this change before merge.
>
> ### MAJOR
>
> **M1. Nothing fails closed against `trackp_sft/v1` with real labels (sft_data.py:115 and 558, trackp.py:308-312, sft_data.py:670).**
> - The library default (`DEFAULT_SPLITS`) is still `trackp_sft/v1`.
> - `cmd_sft_data` still has the universe branch: a pinned table with a different `--sft-config` that lacks `split_file` builds on the old salt split with a real `LabelBlockSource`. Before step 5 those are P3 train/dev labels re-split against the signed file (a §6 STOP if used). After the T0 test row, the raw `label_block.jsonl` path is accepted too.
> - `load_sft_data` / `sft-dev` do not check the split binding. Pre-signature data directories built on `trackp_sft/v1` with real labels (the 1,176/47/74 trial) hold P3-test-instance labels in train and val, and can still be trained on. That conflicts with §6's narrowing of R1-TRACKP-SFT-DEV to P3 train and dev.
> - **Fix:**
>   - In `build_sft_data`, refuse any non-synthetic label source unless `split_file` equals the signed {path, sha256}.
>   - In `cmd_sft_data`, refuse pinned tables or real labels without it, and drop the universe branch.
>   - In `load_sft_data`, refuse a real-label directory whose `splits.json` config lacks the signed `split_file`.
>   - Add tests for each.
>
> **M2. EX-SOURCE misquotes the adopted text, and option C cannot be built (report:51-58).**
> - The (h) item adopted by R1-MAIN-PROPOSER-ITEMS reads "draw the P.3b exam set from sweep 2's training partition, **or from sweep 1's with disclosure until sweep 2 exists**" (PLAN:1005; RUNBOOK:347). The report quotes only "sweep 2's training partition".
> - So option A is already within the adopted item, but it needs disclosure and probably replacement once sweep 2 exists. The report should say both.
> - "P.3b is a screening step that precedes P.4" contradicts R1-C3-POOL-EXAM and the P.4 draft's P4-ARMS: P.3b no longer selects and is not a gate for P.4.
> - Option C (pooled) is offered, but `draw` takes one table, and `SOURCES` has no "both". The cross-source grouping by (instance, incumbent, edit), R1-MAIN-PROPOSER (e)(3), is not implemented.
> - `source` is a label only: the same rows are accepted as "sweep2" (I checked this).
> - **Fix:** quote the full item, add "disclosed" (and "until sweep 2 exists") to A, mark C as needing a further code unit, and bind `source` to the table pin or sweep index.
>
> **M3. Scientific choices in the exam rule are presented as following the spec (report:46; exam_set.py:13-24, 78-94).**
> The salt is new, not from the spec. These choices should go to the author as proposed items:
> - **(a)** Applying R1-TRACKP-SFT-DUP's `val_seen` to the exam, with the (node, incumbent, candidate) key rather than §5.3's "edit hash". Also unstated: which exam-val population P.3b's E2/E3/E5 read.
> - **(b)** The 70/30 is by instance count, not proposal count, and is not stratified by node. A node can appear only in exam-val or only in exam-train.
> - **(c)** Stopping at the first prefix of 400 or more (the low end of ≈400–500). When the 3-node condition forces a larger prefix, it is only flagged: I built a synthetic case that reached 1,101 items with `above_target` and no STOP.
> - **(d)** Rule no-ops are excluded. Sweep 1 has 0, but SFT trains on `rule_noop` rows.
> - **(e)** The rounding rule (see m1).
> - **(f)** Feasibility. From B.2's counts (1,725 eligible of 4,999 over 144 instances), P3 train has roughly 575 eligible sweep-1 proposals, so the exam takes about 70% of P3 train. A skewed distribution could set `below_target`. The report should state this estimate.
>
> **Fix:** list (a)–(e) as EX-* items with recommendations, and add (f) to the report.
>
> ### MINOR
>
> - **m1. The internal split's rounding is unspecified and float-dependent (exam_set.py:87, docstring:21, rule text:102-103).** The code's `floor(0.7n + 0.5)` gives 11 for n=15 and 25 for n=35, where Python's `round` gives 10 and 24. For n=45 it gives 31, where exact round-half-up gives 32. **Fix:** use `(7*n + 5)//10` and state it in the rule.
> - **m2. The exam CLI does not pin the table (exam_set.py:116-131).** `from_table(pins=None)` means membership is bound only after the fact, through `table_proposals_sha256`. **Fix:** add `--table-pin` against `trackp_sft.json` `tables`.
> - **m3. `write` exits 0 and prints only the sha256 when `below_target` or `above_target` is set (exam_set.py:132-139).** The docstring calls `below_target` a STOP. An empty exam-val (one chosen instance) is not flagged. **Fix:** exit non-zero or print the flags, and refuse an empty exam-val.
> - **m4. No check that every member is actually labelled.** Membership is "not rule-skip". That equals "audited" for sweep 1 by B.2's counts, but it is not checked. **Fix:** at P.3b label join, STOP if any member lacks a `y_train` record (by id only).
> - **m5. P3 builds record all 240 instances (including 96 T1) in `splits.json` (sft_data.py:485, 636-647).** The test-instance counts downstream are therefore inflated, for example in the P.4 `populations.test_instances`. **Fix:** document this, or restrict the recorded instances to the table's tier.
> - **m6. "Redraw" framing (report:46-47).** I confirm no exam set, membership file or `exam_member` column exists on any branch or in history, so the report is accurate on that. It should add that the arms-frozen record's §4/§6 item "the exam set's provenance" is then "first drawn after the signature, within P3 train; no earlier membership". The config comment's "are disclosed in the arms-frozen record" should read "to be disclosed"; that record does not exist yet.
> - **m7. Missing tests:**
>   - a CLI test that a pinned build binds P3;
>   - the P.4 recomputation compatibility test (B1);
>   - T1, dev and test rows ignored by `draw`;
>   - `val_seen` produced by a rule-skip exam-train row;
>   - the 3-node condition extending the prefix;
>   - `above_target`;
>   - `write`/`verify` (including refusal to overwrite).
>
>   I checked the first three behaviours with synthetic probes, and they are correct now. Otherwise the existing tests test what they claim.
> - **m8. Small text issues.** The sft_data.py docstring at lines 41-45 has a run-on: "its instances the universe salt and counts are refused". `867a53e5` is labelled "wip"; consider squashing it.
>
> Scratch is in /tmp/rev_tp3/_to_delete/ (17 MB): two synthetic probe scripts, the extracted P.4 draft and evaluator, and the tmp dir. I made no edits to the worktree or repository, and opened no real label, evaluation, table or sealed file. I used only B.2's REPORT.md and the totals in counts.json.

## Round 2 (`d70df3ca`)

> **Verdict: ACCEPTED** for `d70df3ca` on top of `a9d8ff5e`, reviewed with `git diff a9d8ff5e d70df3ca`. Every round-1 finding is fixed. No blocking or major issues remain; there are 3 optional minor nits.
>
> **Runs**
> - The three requested modules (`test_trackp_p3`, `test_p3_split`, `test_trackp_sft`): 69 passed, nothing skipped. Torch is present, so the `load_sft_data` paths do run.
> - `test_trackp_cli`, `test_c3_release`, `test_trackp_exam_analyze` and `test_trackp_trainer`, run once: 75 passed, 9 skipped.
> - I did not re-run the full set of Track P modules. Round 1 already confirmed the 20 environmental failures, and none of those modules touch the changed code.
>
> **Round-1 findings, checked**
> - **B1 (P.4 evaluator).** I re-ran round 1's probe using the actual `sft_test_eval._check_assignment` from `mac-trackp-p4-20261120` on a split_file build. It now passes. The recorded universe is 144 instances with no T1, so m5 is also fixed.
>   - A universe that leaves out a table instance is refused. A universe outside the P3 file is refused.
>   - A subset universe cannot change the assignment, because each instance's split still comes from the file.
>   - The report now correctly says the P.4 draft's P4-P1SPLIT A text must drop its salt-mode wording before merge.
> - **M1 (fail closed on real labels).** All three gates are present and tested:
>   - `build_sft_data` treats any source not marked synthetic as real.
>   - `load_sft_data` refuses a real-label directory without the signed file, which covers the old `trackp_sft/v1` trial directories.
>   - `cmd_sft_data` STOPs a pinned table whose config lacks the file, and the universe branch is gone.
>   - `SIGNED_SPLIT_FILE` matches `p3_split.P3_SPLIT_SHA256` and the file path.
>   - Real labels with `holdout_nodes` still build correctly, so leave-one-node-out is unaffected.
> - **The `p3_gate_bypassed` fixture: acceptable.** It is named, documented, function-scoped through `monkeypatch` (so it is reverted after each test), and used only by the four label-block tests on non-design synthetic instances. The gate itself is tested on design instances, at build and at load, with a real-looking source in `test_trackp_p3`.
> - **M2 (EX-SOURCE).** The full (h) item is quoted. Option A now reads "sweep 1, disclosed, until sweep 2 exists". The "precedes P.4" claim is replaced by R1-C3-POOL-EXAM. Option C is marked as needing a further code unit. `from_table` binds the source to the table pin.
> - **M3 (scientific choices).** EX-DUP, EX-SPLIT, EX-STOP, EX-NOOP and EX-ROUND are framed correctly as author decisions with recommendations, and the ~575 feasibility estimate is in the report.
> - **m1–m8.** All verified:
>   - rounding is `(7n+5)//10`;
>   - `--table-pin` is required and checked;
>   - `write` refuses and writes nothing when `below_target` is set or exam-val is empty, and prints `above_target`;
>   - `check_labelled` exists;
>   - the provenance wording is fixed;
>   - the new tests cover what they claim;
>   - the commits are squashed.
> - **Round-1 exam edge cases, re-run on the new code:** they behave as described. The 3-node condition extends the prefix; T1, dev and test rows are ignored; a rule-skip exam-train row makes `val_seen`.
>
> **Optional minor nits (none needed for acceptance)**
> - **n1.** `draw()` still records whatever `source` it is given. Only `from_table` binds it to the pin (`exam_set.py:65` vs `:138`). Moving the pin check into `draw`, or calling `draw` from the CLI only, would close the library path.
> - **n2.** The membership records `table_pin` but not the sha256 of the `--sft-config` that defined the pin (`exam_set.py:132-143`). Since `--sft-config` can be any file, record the config sha256 or the pin's `sha256` dict as well. `table_proposals_sha256` already partly covers this.
> - **n3.** EX-ROUND's alternative example reads "10 / 24 / 32". The 32 for n = 45 is Python's `round(7n/10)`, but `round(0.7*45)` gives 31 because of floating point. Say which expression is meant.
>
> Scratch is in /tmp/rev_tp3/_to_delete/; the round-2 files are in `round2/`. Nothing was deleted, the worktree is clean, and I opened no real table, label, evaluation or sealed file.

## Round 3 (`84b86b83`)

> CONFIRMED: all three nits are fixed at `84b86b83`, and nothing is still open. I reviewed it with `git diff d70df3ca 84b86b83`.
>
> - **n1:** `draw()` now requires `table_pin` and refuses a source that is not the pin's sweep before it loads the split. `from_table` passes the pin through, and the duplicate check there is gone. One test calls `draw` with a mismatch (test_trackp_p3.py:157) and one goes through the CLI with `--source sweep2` (:365); both expect the refusal.
> - **n2:** The membership file now holds `table_pin_record`, with the pin's sha256 dict and the sha256 of the SFT config. The CLI test checks both values (:351).
> - **n3:** The EX-ROUND text now names `round(7 * n / 10)` (10 / 24 / 32) and notes that the float form `round(0.7 * n)` gives 31 for n = 45. Both are correct.
>
> The three test modules (`test_trackp_p3`, `test_p3_split`, `test_trackp_sft`) give 69 passed, the same as your run.
>
> One cosmetic point, not needed: `from_table` reads the config twice, once to parse it and once to hash it (exam_set.py:137 and :143). Hashing the same bytes it parses would guarantee the recorded sha256 is of the config actually used.
>
> Scratch is in /tmp/rev_tp3/_to_delete/round3/. The worktree is clean, and I opened no real table, label or evaluation file.

---

Code-Commit: 84b86b83586e7461c7080f1785385f920bd261d7
Verdict: ACCEPTED

Accepted: Track P on P3 and the P.3b exam-set code at `84b86b83`; no exam membership is drawn or committed by this unit.
