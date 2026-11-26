Reviewed base: `162c1c6c6` (READY 100: READY 98 on main 3024db3f); accepted at `8f4f7f3a8`, confirmed at `c2b53b7e0`

# Independent review record — D7-DIFF B before the G.5 launch: each step's own proposal diff in the G.5 table, the bound excerpt in A5's T1 prompt, the history-drop report

**Unit.** On `mac-d7-diff-b-20261124` (on `162c1c6c6`): `sweep2/t1_tasl/g5_assemble.py` (every table row gets `proposal_diff`, the ledger line's `proposal.diff` — the manager's parsed reply, written by `campaign_v2_diff` before the step runs, not the run record's applied or a recounted text — and `proposal_diff_sha256` by the harness's `diff_sha256` rule (UTF-8 with surrogateescape, no newline normalisation); `build.json` gains a `proposal_diff` record and schema `g5_t1_table/2`; the assembly STOPs on a tabled row without a text diff); `r1/c3/train/serialize_t1.py` (the table decides the input: a /2 table with bound diffs gives D7-DIFF B, a /1 table gives fallback A, mixed is refused; `table_prompts` passes each row's own text and hash and `t1_prompt` checks both the argument and the row's own `proposal_diff_sha256`, so `meta.diff.sha256` equals the row's hash; the D7-LEN excerpt rule (1,200 characters, 40 lines, 160 per line, history cut before diff) unchanged; the `diffs=` argument removed; `check_showable` refuses a diff strict UTF-8 cannot encode; `history_drop_report`, `read_released_table` and the CLI `python -m r1.c3.train.serialize_t1 history-drop-report` with exit codes 0/1/2); `r1/c3/train/sft_data.py` (a T1 prompt shows a diff exactly when its row carries one, with the row's hash; `check_t1_manifest` requires `diff_shown`); tests `test_t1_d7_diff_b.py` (19) and updates to `test_trackp_t1_prompt.py` and `test_t1_g5_seal.py`; report `docs/r1/reports/arms_t1feat_20261123/D7_DIFF_B_20261124.md` (design, diff-text choice, leakage analysis, FL2 disclosure text §10, the cluster command §9, open items O1–O5). Rows minus the two new fields are byte-identical to the base table; the label and evaluation blocks are identical. `gate.py`, `gate_input_builder.py`, `release.py`, `serialize.py`, `g5_features.py`, `g5_tasl.py` and its spec, and the preregistration are unchanged. Authority: R1-T1-A5-DECISIONS (D7-DIFF B with fallback A); the user's message of 24 Nov 2026 (00:20), item 2.

**Full `r1/tests` suite** (LightGBM off the path, fresh TMPDIR, sequential): base 3024db3f 58 failed / 3 errors / 3823 passed (committed list); tip `d7b410b8` 58 / 3 / 3858 / 197 skipped; `FULLSUITE_D7B_TIP.txt` = `FULLSUITE_BASE_3024db3f.txt` (61 entries): zero new failures. The confirmed fix commit `c2b53b7e0` changes only `serialize_t1.py`, its tests and the report.

**Process.** One independent reviewer, read-only, own detached worktrees at the tip, at the base and a mixed tip-plus-base-assembler copy, synthetic data only, harness read at G5-7 `52e3c0b0`. Round 1 accepted with four minors (own-row binding, CLI exit codes, lone surrogates, wording); the fixes were confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `8f4f7f3a8` | ACCEPTED (minors m1–m4) |
| 2 | `c2b53b7e0` | ACCEPTED (confirmation) |

**Open items (report §11).** O1: the future recount harness unit (R1-G5-DIFF-RECOUNT) must keep `proposal.diff` as the manager's parsed text, and the audit's re-materialisation (`g5_job.parse_ledger` / `audit_plan`) must use the same recount semantics; to be checked in that unit's review. O2: whether the signed `t1_table_readings` line should mention the diff (recommended: leave it; it stays true). O3: FL2's cross-instance repeat recognition (recommended: disclose; read the PRE-DUP primary population first). O4: nothing yet compares the signed D7-DIFF option with the manifest's `diff_shown` (for the evidence-phase or record unit). O5: a diff with a lone surrogate would stop A5's T1 prompts for the whole table (not the assembly, release, A3 or the gate builder); the author decides if it occurs. Timing: `d7b410b83` and `c2b53b7e0` must be on main before the commit that publishes the signed G.5 note and spec; if they miss the launch, the input is fallback A with FL1, and the `g5_assemble.py` part must not be merged afterwards. The history-drop report is run by the cluster after the train/dev release (§9) and committed at `docs/r1/reports/arms_t1feat_20261123/T1_HISTORY_DROP_<YYYYMMDD>.json`; it is descriptive (changing D7-LEN after reading it would be a post-hoc author decision). Residual: a failed write after `open("x")` could leave a partial file alongside exit 2.

## Round 1 (`8f4f7f3a8`)

> Reviewed base: 8f4f7f3a8 (mac-d7-diff-b-20261124; base 162c1c6c6)
>
> ## Summary
> No blocking findings. The unit does what R1-T1-A5-DECISIONS asks: each step's own pre-execution `proposal.diff` goes into the G.5 table, A5's T1 prompt binds a D7-LEN excerpt of it by sha256, the table decides between B and fallback A, the history-drop report exists, and the full suite has no new failures. Four minor findings.
>
> ## What I checked
> 1. **Pre-execution content (G5-7 `52e3c0b0`).** In `campaign_v2_diff.py`, `entry["proposal"] = {..., "diff": proposal.diff}` is set before `run_with_retries`; `parse_v2_diff_reply` requires str fields; nothing changes `entry["proposal"]` before the line is appended (`run_with_retries` touches `runs`/`decision_hint`; `G5CampaignRunner` only the run record; `audit_g5` never rewrites a ledger). Every tabled decision (kept, discarded, discarded_divergent incl. timeout_repeated, not_run_inert, not_run_duplicate) carries `proposal.diff`; truncated replies become `invalid_proposal` and are not tabled. The new STOP cannot fire wrongly on real ledgers; the "not encodable" branch is unreachable.
> 2. **Hash rule** byte-identical to the harness's `diff_sha256` (`sha256(text.encode("utf-8", errors="surrogateescape"))`, no newline normalisation); `meta.diff.sha256` is the full raw text's hash; the excerpt from the CR-normalised text.
> 3. **D7-LEN** constants and `diff_excerpt`, `fit_history`, `_fit_diff` unchanged apart from the hash line.
> 4. **Leakage.** History lines read only `HISTORY_FIELDS` and print `(diff)`; my probe changed every other row's diff (earlier steps, other campaigns) and the prompt and `meta` did not change; `manager_v2_diff.build_prompt` shows the incumbent's files, metric name and direction, and up to 12 earlier summaries with `.6g` values — the author's account is right.
> 5. **Table bytes.** Tip rows minus the two fields equal the base bytes (`25f0ab78…`); label and evaluation blocks identical; in `build.json` only `schema`, `proposal_diff`, `proposals_sha256` differ (others only by tmp path); the table is ASCII.
> 6. **T0 byte identity** with my own script (two builds differing from the golden one): identical on base and tip; no `t1` record. `serialize.py`, `gate.py`, `gate_input_builder.py`, `release.py`, `g5_features.py`, `g5_tasl.py`, the spec unchanged.
> 7. **Release path.** `verify_evidence` compares full `proposals.jsonl` bytes, requires `build.schema == TABLE_SCHEMA`, refuses a changed diff byte; nothing else refers to `g5_t1_table/1`; row guards look at keys only; spec sha256 and `t1_table_readings` untouched (O2 (a) holds).
> 8. **Fallback A analysis** correct (`_g5_published` and the freeze rule, authorization draft line 794); landing the `r1/c3` part alone optional.
> 9. **History-drop CLI** run end to end (runpy, stand-in tokenizer and receipt): exit 0, counts only, train/dev only; refuses test receipts, sha mismatches, evidence or partition dirs; test-instance rows loaded and hash-checked, never rendered (already released features and Δ̂).
> 10. **Full suite.** `FULLSUITE_D7B_TIP.txt` = `FULLSUITE_BASE_3024db3f.txt` (`df956efa…`); not rerun.
> 11. **Tests.** test_t1_d7_diff_b 17; test_trackp_t1_prompt 17; test_t1_g5_seal 36; test_t1_g5_tasl 115; test_gate_input_builder 41; test_c3_arms_freeze (LightGBM) 56; test_c3_release 43; test_trackp_sft 35; test_trackp_sft_test_eval 48; test_t1_features 30 + 1 skipped (31 with LightGBM).
>
> ## Minor findings
> - **m1** `serialize_t1.py:327-330`: `t1_prompt` checks `diff` against its argument `diff_sha256_expected`, not the row's own `proposal_diff_sha256` (a caller passing row Y's text and hash for row X is accepted; `sft_data._t1_forms`, `sft_data.py:851-853`, catches it via `meta` only). Through `table_prompts` the guarantee holds; docstrings claim more. Fix: compare against the row's field, or narrow the docstrings.
> - **m2** CLI `main()` returns 1 on a PromptTooLong STOP, and every refusal is an uncaught exception also exiting 1. Fix: distinct code (e.g. 2) for refusals, or the runbook checks for the written file.
> - **m3** A lone surrogate U+DC80–U+DCFF in a diff passes the harness, the assembly, `table_diff_mode` and `t1_prompt`, but the rendered prompt cannot be encoded to UTF-8 (probe). Very unlikely; a one-line check in `table_diff_mode` or a note would close it.
> - **m4** FL2 should name that the diff's context and removed lines show parts of the incumbent code while the form prints "Incumbent configuration: n/a"; the docstring's "reads the table directory only" omits the receipt, the signed P3 split file and the pool tokenizers.
>
> ## Notes
> The leakage test changes only later rows of the same campaign; adding earlier rows and other campaigns is cheap. O1 correctly flagged (`g5_job.parse_ledger` / `audit_plan` must use the recount unit's semantics).
>
> ## Cleanup
> Three worktrees removed; scratch in `/tmp/d7brev/_to_delete/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

## Round 2 (`c2b53b7e0`)

> Reviewed base: c2b53b7e0 (on 8f4f7f3a8)
>
> ## Summary
> All four minors (m1–m4) and the leakage-test note are fixed correctly. No new findings.
>
> **Scope.** `git diff --stat 8f4f7f3a8 c2b53b7e0`: `serialize_t1.py` (+76/−), `test_t1_d7_diff_b.py` (+86), one line of `test_trackp_t1_prompt.py`, the report (+66: §14 and O5). Unchanged: everything under `sweep2/` (so `g5_assemble.py` and the table bytes), `sft_data.py`, `serialize.py`, `release.py`, `release_checks.py`, `arms_freeze.py`.
>
> **Tests.** test_t1_d7_diff_b 19 passed; test_trackp_t1_prompt 17 passed.
>
> **Own probes** (scratch pytest against `c2b53b7e0`; 4 tests passed):
> - **m1.** Row Y's diff with Y's hash on row X is refused ("binding"); a B row with no diff is refused. The fallback-A allowance cannot be misused: `_table_items` never passes a diff on an A table (`meta.diff is None`); A rows rendered with a forged diff (one row, or every row so `diff_shown` is uniformly true) are refused by `build_sft_data` ("does not carry"); a row carrying `proposal_diff` but no hash is refused on the hash check; a B row stripped of only its hash is accepted by `t1_prompt` directly but refused by `table_diff_mode` and `sft_data` (unreachable), as stated.
> - **m2.** Through `main`: 0 written and fine; 2 when the output exists (file unchanged), for a test receipt and for a wrong `--budget-w`, nothing written; 1 on a too-long prompt, file written. Residual: a failed write after `open("x")` (disk full) could leave a partial file alongside exit 2.
> - **m3.** `check_showable` is called only in `serialize_t1` (`table_diff_mode`, `t1_prompt`); nothing in the assembly, release path or A3 calls it, and those files are unchanged. A lone surrogate in a test-instance row blocks A5's T1 prompts for the whole table, as O5 discloses. The message is the fixed `SURROGATE_REFUSAL` (my marker did not appear). Valid non-ASCII text is still shown.
> - **m4.** FL2 and §5 name the incumbent code shown in context and removed lines; the CLI docstrings and §9 list the table directory, the receipt, the signed P3 split file and the pool tokenizers.
> - **Leakage test** now changes earlier same-campaign rows and every row of every other campaign (diff, outcome, decision, hashes) and checks `render_text` and `meta` unchanged: adequate.
> - **T0 identity.** My two-build script on `c2b53b7e0` is byte-identical to the base `162c1c6c6` output from round 1.
>
> Worktree removed; scratch in `/tmp/d7brev/_to_delete/r2/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

---

Code-Commit: c2b53b7e0
Verdict: ACCEPTED

Accepted at `8f4f7f3a8`, confirmed at `c2b53b7e0`.
