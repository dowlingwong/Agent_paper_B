# Independent review of the B1 STOP diagnosis unit (mac-b1-diag-20261109-c), 9 Nov 2026

Freshly spawned independent reviewer (Claude subagent; did not write the unit). Status: round 1 changes requested; round 2 **accepted** at `b46ced7c` (diagnosis script SHA-256 `82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93`). Rounds copied verbatim below.

---

## Round 1

# Independent review — B1 STOP diagnosis unit, round 1 (9 Nov 2026)

**Reviewer.** A freshly spawned independent agent (Claude). I did not write this unit. I worked only in the cloud container, read-only on the worktrees, with scratch files under `/tmp/pb/scratch_rev_diag/`. No SSH, no host contact, no dry-run campaign.

**Unit.** Branch `mac-b1-diag-20261109-c`, commits `3c22431a` and `eefc9c86` on top of `d9a11b43`. The hand-off pins the full diagnosis script, so I reviewed the whole `B1_STOP_DIAGNOSIS_20261109.py`, including the parts written in `d9a11b43`. Reviewed against runbook `MAC_OVERNIGHT_RUNBOOK_20261109.md` §0 and §1 steps 1–3, plan `B1_STOP_DIAGNOSIS_PLAN_20261108.md` §2–§4, STOP report `B1_STOP_6835_20261108.md` and the accepted descriptive result review (`origin/mac-b1-stop-descriptive-review-20261108`).

## What I verified independently (holds)

- **Tests.** `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin python -m pytest -q -p no:cacheprovider` on the three named files: 19 passed. The worktree stayed clean afterwards.
- **D5.** In harness `a3fedbb`, all three nodes maximize (`digits_mlp`: `val_score`; `openml_credit_approval` and `openml_ionosphere`: `val_auc`), with `acceptance_rule` `candidate_metric > current_best_metric`. The config blobs are identical at `897d83c`. `r1/c3/audit.py::paired` returns `mean(cand − inc)`. `_collect_b1_review` calls `paired(candidate, incumbent)`. `anchor_gate` calls `paired_instance_bootstrap(scripted, random_valid)` and STOPs on `difference_lower <= 0`. Orientation and sign are correct; the D5 conclusion holds.
- **D6 (the core claims).** I diffed `3b3283f` against `68357d3d`:
  - Blob-identical: `scripted_manager.py` (`1f1af532`), `value_grids.yaml` (`c29138a4`; SHA-256 `7ab60c16…b1ea14` at both commits), `guards.py` (`c153c159`), `registry.yaml`'s `software_anchors` entries, and `r1/c3/features.py`.
  - The body of `anchor_gate` is identical; I extracted and diffed it.
  - Harness blob-identical at `897d83c` and `a3fedbb`: `random_valid.py` (`02c5385a`), `decision.py`, and the three node configs and node sources.
  - New wrappers that I read: `b1_proposal_guard.py`, `b1_editable_preserve.py`, `b1_openml_cache_guard.py`, `b1_node_artifacts.py`, `b1_worker_artifact_guard.py`, and the `audit.py::run_config` changes. Each either leaves the evaluated files unchanged or raises STOP. Seeds still reach the node through `seed_environment`, so the OpenML `runpy` bootstrap does not drop them. Retiring `artifacts/` only touches node output, and the worker's `changed_files` covers only the target file.
  - **The conclusion "no engineering defect visible in the code" holds**, apart from the factual error in F1 and the omissions in F2.
- **σ constants.** Commit `511c3797` exists. `git show 511c3797:docs/r1/reports/NOISE_FLOOR_COMMON_20261022.md | sha256sum` gives `9be292b7…c01d`, the same as the file at HEAD. In Table 1, σ_joint is 0.0102 / 0.0279 / 0.0410 and median sd(Δ̂) is 0.0066 / 0.0030 / 0.0160 for digits_mlp / credit_approval / ionosphere. These equal the script's constants.
- **Script SHA.** `sha256sum B1_STOP_DIAGNOSIS_20261109.py` gives `e49ed5501a7c7e715f0adf455c389ca55d2bf97409ac4e0bf2208617fa8393d1`, the same as in the hand-off.
- **Read-only boundary (host mode).**
  - The script only `os.open`s with `O_RDONLY`. Every path component is opened with `O_NOFOLLOW` from `/`. The final file is opened with `O_NOATIME`, with no fallback.
  - The file must be an owned regular file, and its identity must not change during the read.
  - Duplicate JSON keys and non-finite numbers are refused.
  - The job is validated (HEAD, phase, node, seed, audit seeds 9101–9104 in the job and in `authority_config`, rule SHA, W) before the manifest is opened. Then manifest SHA = batch-state entry, job SHA = manifest, and `root_trials.jsonl` = manifest evidence hash.
  - Nothing is printed until all 36 roots validate. No seed outside 9001–9004 / 9101–9104 builds a path, and no per-seed audit vector is output; the synthetic test asserts this too.
- **Field names against the producer code at `68357d3d`.** I checked every new field the script reads against `campaign.py::_collect_b1_review`, `exam_runner.py::anchor_gate`, `features.py::replay_campaign` and harness `TrialRecord`. All exist with the expected types: `diagnostics` keys, `compute_budget.worker_runs`, `termination`, `evidence_hashes['root_trials.jsonl']`, `k`, `candidate_metrics`/`incumbent_metrics`, the `EXAM:<node>__s<seed>:t<bbb>` proposal ID, and `budget_index`/`node_id`/`parsed_metrics`/`decision`. A NaN in `root_trials.jsonl` is not possible, because the harness metric regex accepts only numeric literals.
- **D1 and D7 against the gate.** D1 pools the per-root `audited_proposals` the same way `anchor_gate` pools the candidate manifest. The bootstrap port is textually identical to `guards.py`. D7 = Σ duplicates / Σ evaluated over the qwen roots, as the gate computes it (but see F3 on the bounds).
- **Hand-off command.** I ran the remote command string through `bash -c` locally with the real script. The quoting survives; under `exec` the script runs host mode (`argv == ['-c']`); it refused on the missing root with only a stderr `STOP:` line and exit 1, and printed nothing on stdout.
- **No deletion; authorship.** The partial draft was moved with `R100` to `docs/r1/reports/_to_delete/B1_STOP_DIAGNOSIS_20261109_PARTIAL_DRAFT.md`, and no file was deleted. Author and committer of both commits are `Dowling Wong <wangdowling@gmail.com>`, and the commits carry the attribution lines.

## Findings

### F1 — should-fix — the code-check report states the first-trial mechanics wrongly
`docs/r1/reports/B1_STOP_CODE_CHECKS_20261109.md:52` says the first valid trial is "the first audited proposal … its `delta_audit` is still measured against the start configuration". That is false.

- At `68357d3d`, `r1/c3/features.py::replay_campaign` (docstring: "proposals (trial >= 2 with a parsed metric)") and `_LedgerState.featurize` (`if not (b >= 2 and current_best_before is not None): return None`) produce **no proposal** for the first valid trial. So it is **never audited**.
- Every audited proposal is therefore measured against an incumbent that already contains that unaudited, unconditionally kept first edit. For `random_valid`, that first edit can be a large grid jump.
- This bears directly on H1/H2, and the diagnosis report will inherit the sentence.

**Fix:** replace the bullet with the correct mechanics, citing `features.py:353` and `replay_campaign`'s docstring. Note what follows: a campaign's first edit is outside `delta_audit` for every anchor, and all audited increments are relative to a randomly moved incumbent.

### F2 — should-fix — the D6 file inventory is incomplete (files in the anchor path not listed)
The report (`B1_STOP_CODE_CHECKS_20261109.md:21–48`) omits these files from the anchor path:

1. `r1/c3/features.py`. This is `replay_campaign` / `files_hash`. It decides which proposals are audited (`active_equals_incumbent`, `active_seen_before`) and which candidate/incumbent files are audited. Unchanged since `3b3283f`, but it belongs in the table.
2. `r1/exam/b1_node_artifacts.py::preserve_node_artifacts`. It is called before every in-run worker trial (`B1IntegrityWorker.run_trial`) and before every audit seed (`run_config`). It renames `artifacts/` into `node/_to_delete/`. I checked that the three nodes only *write* `artifacts/`, so it has no effect on metrics, but this needs to be stated.
3. `r1/exam/b1_worker_artifact_guard.py` (`GuardedTrialPath`), which converts an overwrite into a STOP.
4. `r1/exam/runtime.py`'s job construction: `W`, `workers`, `value_grids` path, and the run `binding`, which includes `value_grids_sha256`. Also `r1/exam/b1_batch.py`'s root verification, which already enforces `worker_runs <= W` and termination consistency.
5. On the harness side, `897d83c..a3fedbb` also changes `control_plane/snapshot.py`, `memory/summarizer.py`, `manager/langgraph_manager.py`, `llm/providers.py` and `llm/langchain_client.py`. Only `campaign.py` is listed. They are all opt-in (Track S) or LLM-only. That makes them irrelevant to the software anchors, but `providers.py`/`langgraph_manager.py` (cache_prompt) do touch the 7B anchor behind D7/D8.

The report also does not address the plan §2 H4 item "rejected inactive categorical edits counted as trials". The code answers it:

- `ScriptedRandomManager` can draw an inactive categorical key. Its docstring says so.
- The harness rejects such a proposal before any worker run (`campaign.py:1427–1552`, `reason: inactive_key`) and records a `skipped` trial with no worker run.
- `replay_campaign` drops `skipped` rows, so such a trial is never audited and does not consume `W`. It does consume a budget index.

**Fix:** add these rows with one-line bearings, and add the inactive-key answer. The runbook also asks that the retirement of the partial draft to `reports/_to_delete/` be stated in the report; add one line.

### F3 — should-fix — D7 uses rounded bounds, not the pinned interval the gate uses
`B1_STOP_DIAGNOSIS_20261109.py:52` (`DUP_REF = (0.4239, 0.5800)`) is used at lines 297–298.

- The gate reads `cfg['anchor_duplicate_reference']`. In `r1/scripts/configs/exam_b1_v2.json` at `68357d3d` that is `lower = 0.42386590667728663`, `upper = 0.5800007633587785`, source `B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json`, SHA `84200770…`.
- A rate in [0.423866, 0.4239) or (0.5800, 0.58000076] would be reported `inside: false`, yet it passes the real next gate. D7's stated purpose is to predict that gate exactly.

**Fix:** read `lower`/`upper` from `job['authority_config']['anchor_duplicate_reference']`. That job is already read, hash-bound and validated. Refuse unless it equals the exact committed values (embed them, with the source path and SHA). Report the bounds used. Update `B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py:175` to print them unrounded.

### F4 — should-fix — the batch state is not pinned to the accepted descriptive capture
`B1_STOP_DIAGNOSIS_20261109.py:304–315` accepts any `batch_state.json` that has the right phase, status and reason. The whole hash chain hangs off this mutable file: state → 36 manifest SHAs → job SHAs → ledger SHAs.

The accepted descriptive result review records state SHA `cfe74fafdbbff6f10648f7e015b3df52f0438c435d45caf76e9e8c116d0b5794` for the same preserved scene. Pinning it is free. It binds this capture to the evidence that was already reviewed, and it detects any change to the STOP scene since 8 Nov 10:52 UTC. Today such a change would pass silently.

**Fix:** add `EXPECTED_STATE_SHA = 'cfe74faf…5794'` with its provenance (review file and branch), and refuse on a mismatch before opening any job. Optionally, also refuse if any of the 24 `random_valid`/`scripted` job/manifest SHAs differ from the accepted capture's rows. Add a synthetic test for the mismatch refusal, and state the pin in the hand-off.

### F5 — should-fix — hand-off is not complete: commit placeholder, wrong branch name
`docs/r1/proposals/B1_DIAGNOSIS_HANDOFF_20261109.md:7` reads "branch `mac-b1-diag-20261109` (commit ⟨commit⟩)". The unit is on `mac-b1-diag-20261109-c`, and the commit is unfilled. Line 18 says "Run from a clean checkout of the commit above", which cannot be done as written.

The script SHA binds the script itself. But the experiment agent also needs the exact commit, to check out the analysis script and the review file named at line 3.

**Fix:** after the fixes in this review, fill in the full 40-hex commit and the real branch name. Re-state the new script SHA-256: it changes with F3/F4, and the hand-off must be regenerated from the final file. Keep `reviews/B1_STOP_DIAGNOSIS_SCRIPTS_REVIEW_20261109.md` as a precondition, and commit the accepted review there.

### F6 — should-fix — the "pre-declared before any capture" claim is inaccurate
`B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py:7–8` says "fixed … BEFORE any capture existed (the analysis was written and reviewed against synthetic data only)". The output also carries `rules_fixed_before_capture: True` (line 145). That is not accurate:

- The accepted descriptive capture (8 Nov) already existed.
- Its 24 per-root means are sufficient to compute the D1 point, the per-node standardized means and `positive_nodes`, which are all the inputs of the H1/H3 rules. The diagnosis script's own local mode computes exactly that.
- Its published ranges were known when the thresholds were set: the runbook quotes them, and so do the code-check report (line 54) and the partial draft.

The partial draft says the paired values themselves were not accessible to the agent. That limits the problem, but the claim as written overstates the pre-registration.

**Fix:** reword to "fixed before the diagnosis capture existed. The accepted descriptive capture (24 per-root means, sufficient for D1 and the H1/H3 inputs) already existed. Its published ranges were known when Z_SMALL/Z_DROP/COUNT_RATIO were chosen; its paired values were not read." Rename the flag to something like `rules_fixed_before_diagnosis_capture`, and add a `descriptive_capture_known: 'ranges only'` field.

### F7 — should-fix — the class rules let a flagged H4 anomaly or a failed D7 resolve to an actionable D/R4
`B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py:103, 133–136, 143`:

- **H4 UNDETERMINED still gives class D.** If H4 is `UNDETERMINED` (invalid share > 0.5), the class still resolves to `D` with `r4_applicable_under_A1: True`. Verified in scratch: every invalid share set to 1.0 gives `H4 UNDETERMINED`, `class D`, `r4_applicable_under_A1 True`. Under the A1 line, class D leads to R4 and a restart without the author. That should not follow while a possible engineering defect is flagged.
- **D7 FAIL still gives `r4_applicable_under_A1: True`.** The test at `test_b1_stop_diagnosis_analysis_synthetic.py:85–89` asserts exactly this. Plan §4 routes a D7 failure to the author. R4 keeps the 7B duplicate STOP, so a restart would stop on it.

**Fix:**
- Class `E` if H4 SUPPORTED. Otherwise `REVIEW` (to the author) if H4 UNDETERMINED. Otherwise D/P/UNCLASSIFIED as now.
- `r4_applicable_under_A1 = (class == 'D' and D7 == 'PASS')`, with an explicit `needs_author` list (D7 FAIL, H4 UNDETERMINED).
- Update the docstring and the tests.

### F8 — should-fix — missing or partial capture fields are guessed, not refused
Verified in scratch (`/tmp/pb/scratch_rev_diag/probe.py`, `probe2.py`):

- Line 80, `s.get('D1_gate_recomputed') or {}`: if D1 is missing, the class becomes `E`.
- Line 139, `d7.get('inside') is True`: if `inside` is missing or `None` (zero evaluated), D7 becomes `FAIL`.
- Lines 83 and 87 silently drop `None` per-instance differences.
- `rows` truncated to 5 of 36 still yields `class D`.
- A missing `D3` passes `verdicts()`, and then `tables()` raises an uncaught `KeyError`, because lines 187–189 sit outside the `try` at 182–186. The result is a traceback, not an "analysis refused" line.

The runbook asks for refusal rather than guessing.

**Fix:** add a `validate(doc)` step before `verdicts`. It should require:
- exactly 36 rows with the expected (anchor, node, seed) set;
- `summary` keys D1_gate_recomputed (non-null, with finite point/lower/upper), D1_reproduces_stop (bool), D1_per_instance (12 entries, all differences finite), D2/D4 with all 9 keys, D3 with 6, D8 with 3, and D7 with `evaluated > 0` and a bool `inside`.

Refuse otherwise. Also move `tables()` inside the `try`.

Optionally:
- Recompute D1 from `rows[*].proposals` and refuse if it differs from `summary`.
- Check `SSH_EXIT=0` in the log.
- Take the expected script SHA as an argument, and check it against the receipt's SHA line.

### F9 — should-fix — the synthetic analysis tests do not exercise every class with a known answer
`test_falling_increments_support_h2` (`test_b1_stop_diagnosis_analysis_synthetic.py:73–82`) asserts `class in ('D', 'E')`. With that fixture the class is actually **E**: the per-instance differences are identical, so the interval is degenerate above 0, and "D1 does not reproduce the recorded STOP" fires (I verified this). So the H2 → D path is never tested.

Also untested:
- the H2 count-ratio disjunct;
- the H1 second disjunct (point > 0, `mean_z < Z_SMALL`, fewer than three positive nodes);
- `UNCLASSIFIED`;
- H4 `UNDETERMINED`;
- H4 "zero audited proposals";
- the worker-accounting rule.

**Fix:** give each class and each disjunct its own fixture with an exact expected class. For a D-via-H2 case, use per-instance variation so the STOP reproduces (lower ≤ 0) while H1/H3 do not fire. Also test D7 PASS/FAIL interplay with `r4_applicable` (F7) and every refusal path in F8.

### F10 — should-fix — the H4 worker-accounting rule is unreachable and misses the real anomaly
`B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py:99–100` (and docstring line 18–19) flags `termination == 'worker_cap' and worker_runs != W`. At `68357d3d`, `campaign.py:303` sets `worker_cap` iff `worker_runs >= W`, and `b1_batch.py` enforces `0 <= worker_runs <= W` and termination consistency, so this can never fire.

The meaningful plan §2 check ("worker-run accounting with W = 20") is the reverse. Software anchors run with budget 1,000,000 and should all end `worker_cap` with `worker_runs == 20`. A software root that ended `llm_cap_or_reserved_observer_pair`, or with fewer than 20 runs, is an accounting anomaly.

**Fix:** for `anchor in SOFTWARE`, require `termination == 'worker_cap' and worker_runs == W`; otherwise add an H4 reason. For qwen, keep the current behaviour.

### F11 — should-fix — the D2/D3 tables omit plan columns
Plan §3 D2 includes "final incumbent's in-run metric vs start". The script computes `mean_gain_after_first_keep` (diagnosis script line 279), but the analysis D2 table (lines 158–161) does not show it. The D2 table also omits the per-anchor `skipped` count, which is where inactive-key rejections show (see F2 and the H4 item). D3 in the plan asks for "the same divided by σ_node": median/σ is not produced (`_summary`, diagnosis script lines 155–160). The share of harmful proposals is scale-free, which is fine.

**Fix:** aggregate `skipped` (and `decisions`) into D2. Add `mean_gain_after_first_keep` (labelled "in-run gain after the unconditional first keep; no unedited start metric exists") and `skipped` columns to the D2 table. Add `median_over_sigma_joint` to `_summary` and the D3 table.

### F12 — note — diagnosis-script synthetic tests do not cover the boundary refusals of this file
`r1/tests/test_b1_stop_diagnosis_synthetic.py` covers seed mismatch, ledger hash mismatch and delta mismatch. It does not cover these cases for this script's `_read_bytes`:
- a symlinked component or file (`O_NOFOLLOW`);
- a file not owned by the user;
- a file changed during the read;
- `main()` printing nothing on stdout on refusal;
- a manifest status or execution_label mismatch.

**Suggested:** add tests that build a symlink, use a monkeypatched `os.getuid`, and capture stdout from `main()` on a broken fixture. Add the F4 mismatch test.

### F13 — note — smaller points (no change required for acceptance)
- **Hash check versus bytes sent.** The hand-off wrapper hashes `$SCRIPT` and then re-reads it for base64 (lines 25–26), which leaves a TOCTOU gap. Computing the SHA from the same bytes that are base64-encoded (one Python call that prints both) closes it. The accepted descriptive wrapper has the same pattern.
- **Value-grid link to the run.** The run `binding` includes `value_grids_sha256`. Recomputing the binding from `authority_config`, the registry SHA, `RULE` and `7ab60c16…` would tie the run's value grid to the D6 hash. Only report it as a boolean, because `cfg` may have been augmented after binding. Optional.
- **Directory ownership.** Directory components are not ownership-checked, only the final file. This matches the accepted descriptive reader and the disclosed cooperative boundary.
- **D0 inventory.** Plan D0 "files present / audit-cache completeness" is realised as refusal (status, label, `k`), not as an inventory. That is acceptable given the 36-root COMPLETE state, but the report should say so.
- **H2 count-ratio disjunct.** It lets class D follow from audited-count differences alone (`analysis:122–126`). Count differences are an expected consequence of the two proposal laws (duplicates and no-ops), not by themselves evidence that the mean increment is non-monotone in quality. The plan lists counts as H2 evidence, so this is within the plan. Still, report this disjunct as a separate reason in the verdict, so the diagnosis reviewer can weigh it apart from the D4 drop.
- **Hand-off line 45** asks the experiment agent to commit `ssh.log`, which holds every per-proposal `delta_audit`, including the 7B values. That is consistent with the plan's "raw per-instance numbers in a JSON file", but committing only the SHA and the private path until the diagnosis review is accepted would mirror the descriptive capture's practice.

## Summary
The static D5/D6 conclusion ("no engineering defect visible in the code") is confirmed. The read-only boundary of the diagnosis script is enforced as described. The σ constants and the script SHA are correct, and the hand-off command works mechanically.

Changes are needed before acceptance:
- a factual error about the first-trial audit (F1) and an incomplete D6 inventory (F2);
- D7 using rounded bounds (F3) and the batch state not pinned to the accepted capture (F4);
- an unfilled hand-off commit and the wrong branch name (F5);
- an overstated pre-registration claim (F6);
- class rules that let a flagged H4 or a failed D7 become an actionable D/R4 (F7);
- guessing on partial captures (F8);
- class tests that do not exercise D-via-H2 or several rule branches (F9);
- a dead H4 accounting rule (F10);
- missing plan columns (F11).

VERDICT: changes requested

---

## Round 2

# Independent review — B1 STOP diagnosis unit, round 2 (9 Nov 2026)

**Reviewer.** The same independent agent as round 1, re-checking fixes. Worktrees read-only; scratch files only under `/tmp/pb/scratch_rev_diag/`; no SSH, no host contact, no dry run.

**Unit.** Branch `mac-b1-diag-20261109-c`, with two new commits:
- `81c81289` changes the scripts, the tests and the code-check report.
- `b46ced7c` regenerates the hand-off and adds the answer file `docs/r1/reviews/B1_DIAG_REVIEW_ANSWERS_20261109.md`.

`3c22431a` and `eefc9c86` are not rewritten.

## Mechanical checks
- **Tests.** The three named files give **49 passed**, and the worktree stays clean.
- **Script SHAs.**
  - Diagnosis script SHA-256 = `82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93`, the same as the hand-off and the answer file.
  - Analysis script SHA-256 = `2537099f…2ffd07`, as stated.
  - `git diff 81c81289 HEAD` on both scripts is empty, so the hand-off's "last changed in 81c81289" holds.
- **Authorship, no deletion.** Both commits are authored and committed by Dowling Wong <wangdowling@gmail.com> and carry the attribution lines. Name-status shows only M/A, no D.
- **Hand-off wrapper.** I extracted it verbatim from the hand-off and ran it with `ssh` stubbed by a local `bash -c` and `shasum` mapped to `sha256sum`.
  - It printed `SENT_SCRIPT_SHA256=82140eea…`, and the script SHA it printed matched.
  - The script refused on the missing root with only a stderr line. `ssh.log` ended with `SSH_EXIT=1`, and the wrapper exited 1.
  - The bytes that are hashed are the bytes that are sent.

## Round-1 findings
| # | Status | Verification |
|---|---|---|
| F1 | **resolved** | The code-check report now says the first valid trial is never audited, citing `features.py:353` and `:471`. I re-confirmed both. The consequences are stated, and the retired draft's identical error is disclosed. |
| F2 | **resolved** | Rows added: `features.py` (blob `7a6bde19` at both commits, which I verified), `b1_node_artifacts.py`, `b1_worker_artifact_guard.py`, `runtime.py` job/binding (the binding formula is identical to Stage A's `3b3283f:runtime.py:215`, verified), `b1_batch.py`, and the harness Track S / LLM-path files. The H4 inactive-key item is answered. I verified `campaign.py:1427–1475` at `a3fedbb`: a deterministic manager gets no revision, so the trial is skipped with `inactive_key` and no worker run. The draft retirement is stated. |
| F3 | **resolved** | `DUP_REF_PINNED` equals the `anchor_duplicate_reference` object in `68357d3d:r1/scripts/configs/exam_b1_v2.json`: same four keys, float bounds, and source file SHA `84200770…` (verified). D7 uses the unrounded bounds and adds `passes_next_gate`. The tests cover the 0.42387 boundary and a job carrying rounded bounds. |
| F4 | **resolved** | `EXPECTED_STATE_SHA = cfe74faf…5794` is checked on the raw bytes before parsing and before any job is opened. Provenance is commented. The mismatch test asserts that no job is read. Dropping the optional per-row pin is reasonable: those rows are not committed, and the state pin covers them transitively. |
| F5 | **resolved** | Branch `-c`, script commit `81c81289…` and the new SHA are named. The hand-off asks the agent to use the reviewed tip and to check that the diff on the scripts is empty. That is an acceptable way to deal with the fact that a commit cannot contain its own SHA. |
| F6 | **resolved** | The docstring states the provenance correctly. The output flag is renamed, and `descriptive_capture_known: 'ranges only …'` is added. |
| F7 | **resolved** | Class order is E, then REVIEW, then D, P, UNCLASSIFIED. `r4_applicable_under_A1 = class D ∧ H1 SUPPORTED ∧ D7 PASS`, and `needs_author` lists the other routes. Tests cover REVIEW and D7 FAIL. |
| F8 | **resolved** | `validate()` runs inside `verdicts()`. `tables()` and the JSON dump are inside the `try`, and `SSH_EXIT=0` is required. My round-1 probes now all refuse: truncated rows, missing D1, missing D7 `inside`, missing D3. Per-instance means, D1 point, D2 counts, D0 counters and D7 are recomputed from the rows. |
| F9 | **resolved** | Each class and each rule branch has its own fixture with an exact expected class, including D via H2 alone and D via the count ratio alone (neither is R4), the H1 second disjunct, UNCLASSIFIED, P, E (several causes) and REVIEW. Ten parametrised refusal cases. |
| F10 | **resolved** | Software anchors must end `worker_cap` with exactly 20 runs; qwen keeps the original check. Both directions are tested. |
| F11 | **resolved** | D2 has `skipped`, `decisions`, the in-run gain and the number of roots with a gain. The table has the new columns and an explanatory note. `median_over_sigma_joint` is added in D3/D4 and shown in the table. |
| F12 | **resolved** | Tests added: symlinked file, symlinked directory component, file not owned, file changed during read, no stdout on refusal, manifest status/label mismatch, state pin, rounded reference. |
| F13 | **resolved / acknowledged** | The wrapper now hashes and sends the same bytes. The count-ratio reasons carry `kind`. `ssh.log` is committed by SHA and path only. The value-grid binding boolean is reasonably declined (the registry SHA at run start is not in the job). D0 is now documented as refusal. |

## Judgement on the coordinator's three points

1. **The two deliberate non-refusals are acceptable.**
   - *Zero audited proposals in a software root.* Validation accepts `D1_gate_recomputed: null` only together with an empty software root, a string `D1_error` and `D1_reproduces_stop: null`, all cross-checked against the rows. The verdict is the conservative class E: fix plus review, no change of criterion, no STOP dropped. For the real capture this pattern cannot arise. With a missing instance, the real `anchor_gate` bootstrap would have raised `ValueError`, so the recorded `stop_reason` would differ, and the pinned state and reason check refuses first. It is harmless and keeps the plan's H4 rule reachable on synthetic data.
   - *Zero evaluated 7B proposals gives D7 FAIL.* This matches `anchor_gate` exactly (`rate is None` → STOP), and the route is to the author. Acceptable.
2. **`REVIEW` is acceptable.** Plan §4 has no row for "H4 undetermined". `REVIEW` is strictly more conservative than any plan route: it goes to the author and never to E/P/D, and it blocks R4. The diagnosis report should name it as an addition to the plan §4 table (see N2).
3. **The state pin and the reference pin are correct, even though a refusal costs the single run.**
   - *State pin.* If `batch_state.json` has changed since the reviewed 8 Nov 10:52 UTC capture, the preserved STOP scene has been touched. A refusal is then the finding, and the hand-off already says to report it and not rerun. The permitted shutdown-time writes happened at about 01:17–01:19 UTC on 8 Nov, before that capture, so they are inside the pinned state.
   - *Reference pin.* The refusal cannot fire spuriously. Every completed root passed `campaign._verify_b1_worker_input`, which calls `require_committed_b1_config(..., job['authority_config'])`. That requires `json.loads(committed blob) == cfg` (`runtime.py` at `68357d3d`), and I verified that the committed object equals `DUP_REF_PINNED`, float types included.
   - The descriptive capture also passed the same job checks on 24 of the 36 roots.

**R4 applicability.** The rule `class D ∧ H1 SUPPORTED ∧ D7 PASS` matches PLAN row `R1-EXAM-B1-ANCHOR-R4` on `/tmp/pb/wt/r4` (HEAD `5f8c5136`). Its wording: "class D with H1 supported … A class-D verdict resting on H2 alone … goes to the author; so does class P, and so does any D7 failure". A class D with both H1 and H2 supported is R4-applicable, which matches "class D with H1 supported". E and REVIEW never are.

## Remaining notes (no change required for acceptance)
- **N1 — note.** `validate()` checks the per-instance `difference_over_sigma_joint`, the D4/D3 summary values and the D7 `reference` bounds for type only. It does not recompute them from the rows, and it does not compare the bounds to the pinned constants. In scratch, tampering a D4 `mean_over_sigma_joint`, a per-instance z, or the D7 lower bound to 0.4239 was accepted. These values feed H1/H2. The capture comes from the reviewed script under a SHA receipt, so the risk is low. Still, three cheap checks would close it:
  - z = difference / σ_joint(node);
  - recompute the D4 halves and the D3 summaries from `rows[*].proposals`;
  - `reference == {lower: 0.42386590667728663, upper: 0.5800007633587785}`.
- **N2 — note.** When the diagnosis report is written, list `REVIEW` and the zero-audited / zero-evaluated handling as the analysis's additions to plan §4, so the diagnosis reviewer sees them as declared choices.
- **N3 — note (outside this unit).** PLAN row `R1-EXAM-B1-ANCHOR-R4` on the R4 branch still writes the 7B interval as "[0.4239, 0.5800]". The gate and this unit use the unrounded `[0.42386590667728663, 0.5800007633587785]`. Aligning that wording belongs to the R4 unit's reviewer.
- **N4 — note.** `SENT_SCRIPT_SHA256=` is printed to the wrapper's stdout, not into `ssh.log`, so the analysis cannot check it. The hand-off asks for it to be sent back, which suffices.

## Summary
All 13 round-1 findings are resolved or reasonably answered. The deliberate non-refusals, the `REVIEW` class and the two pins are sound and conservative. R4 applicability matches the PLAN row. The read-only boundary, the hash chain (now anchored to the accepted capture's state SHA) and the hand-off command are verified.

VERDICT: accepted
