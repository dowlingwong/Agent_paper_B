Reviewed base: 8745b75bb9a6ba62bf83a87e24ab34abbfa7d0be

# B2 STOP 6 report template — independent review record (15 November 2026)

Branch `mac-b2-stop6-report-20261115`, from `mac-b2-handoff-exec-20261115` @ `aeeab991`. Unit: `r1/scripts/b2_stop6_report.py` (renderer + `derive-invalid`), `r1/tests/test_b2_stop6_report.py`, `reports/B2_STOP6_REPORT_TEMPLATE_20261115.md`; input formats of `mac-b2-code-20261114` @ `a2cd540c`; no protected path touched. Author queue item 1 of 15 Nov. Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`06a33178`): changes requested (2 MAJOR: the D28 column claimed B2 D28 decides eligibility; the invalid-trial split was not tied to the verified roots; 8 MINOR).
- Round 2 (`78481d20`): accepted, with 2 non-blocking MINORs.
- Round 3 (`8745b75b`, the 2 MINORs fixed): **accepted**, no findings. (The round-3 request first named a wrong hash, `2b2df4f9`, then corrected it to `8745b75b`; the reviewer reviewed `8745b75b`.)

Accepted commit (round 3, last): 8745b75bb9a6ba62bf83a87e24ab34abbfa7d0be

The round texts are reproduced unchanged below.

---

# Review R1: B2 STOP 6 report template (`mac-b2-stop6-report-20261115` @ `06a33178`, base `aeeab991`)

Independent reviewer (AI-assisted, Claude). Read-only; scratch under `/tmp/pb/rev_stop6/` only.
Reviewed base = `06a33178`.

VERDICT: REVISE

Two MAJOR findings. Both are small to fix. The statistics, the format reading and the ranking checks are correct.

## Findings

### 1. MAJOR: the D28 table says B2 thinking-off D28 "decides eligibility"; no B2 code or rule does that
- **Where.** `r1/scripts/b2_stop6_report.py` l. 385: the column header `B2 thinking off (decides eligibility; scope)`. Doc §4 item 4 repeats it: "the B2 thinking-off status (decides eligibility …)".
- **Evidence.**
  - `analyze._b2_summary_v2` (a2cd540c l. 303–357) never reads `d28_pass`. B2 ranks only by final Y, with ties going to lower GPU-h.
  - Eligibility (Stage A + D28, thinking off) was decided in B1 by `choose_finalists` (RUNBOOK X.5; rule `eligibility.d28_scope: thinking_off_only`). STOP 5 then fixed `[gemma4_31b]`.
  - `verify_b2_batch` only checks that the manifest `d28_pass` equals the recomputed value from the primary roots (l. 326–328). It gates nothing.
  - No PLAN row, hand-off text or RUNBOOK X.6/X.7 gives B2 D28 an eligibility role.
- **Why it matters.** If gemma4_31b's B2 thinking-off D28 were `fail`, the report would print "fail (decides eligibility)" next to "is the rule pick whatever its B2 score". That contradicts the rule, and it is an interpretive claim the author might read as binding.
- **Fix.**
  - B2 off column: "B2 thinking off (recorded, `thinking_off_roots_only`; not used by the x5_rule/v2 B2 ranking)".
  - B1 column: "B1 D28 (thinking off; decided eligibility at STOP 5)".
  - Optionally, when the B2 off D28 fails, print a one-line flag for the author.
  - Make the same change in doc §4.

### 2. MAJOR: the per-mode and per-class invalid-trial counts and the LLM calls are not bound to the verified roots, and the docstring overclaims
- **Where.**
  - `derive_invalid` (l. 107–136).
  - `load_and_check` invalid block (l. 174–191).
  - Module docstring l. 3: "recomputes every number it prints from the B2 manifests".
- **Evidence.**
  - `render` checks only three things about `invalid_trials.json`:
    - its rows cover the grid;
    - each row's classes add up to its `invalid`;
    - per-candidate totals over both modes equal the manifest `diagnostics`.
  - The off/on split, the class split, the per-node split and `llm_calls` are not cross-checked against anything. The aggregate manifest carries no per-root diagnostics.
  - Its `batch_manifests_sha256` is copied from the analysis, so it proves nothing about where the rows came from.
  - Probe (`scr/probe.py` §2): I moved all invalid trials from `off` to `on` (off 0, on 48, all `other_invalid`). `render` accepted it and printed the false table.
  - `derive_invalid` is meant to run "on the host (read-only) or on a copy-back of the roots" (doc §2). It checks the batch's `b2_manifests.json` sha, but not:
    - `batch_state.json` against `proof.batch_state_sha256`;
    - each root's `campaign_manifest.json` against `state['completed'][key]['sha256']`;
    - `root_trials.jsonl` / `b1_proposals.jsonl` against the root manifest's `evidence_hashes`.

    So a stale or mismatched copy-back with the same counts passes. These per-mode and per-check counts are exactly what the hand-off §6 and R1-EXAM-B2-INVALID-TRIALS ask the B2 report to give. The STOP 6 reviewer cannot recompute them from `b2_manifests.json` alone.
- **Fix (about 10 lines).**
  - In `derive_invalid`, read `batch/'batch_state.json'` and STOP unless its sha equals `proof['batch_state_sha256']`.
  - For each root, STOP unless the sha of `campaign_manifest.json` equals `state['completed'][f'{cid}/b2/{mode}/{node}__s{seed}']['sha256']`, and the shas of `root_trials.jsonl` and `b1_proposals.jsonl` equal `manifest['evidence_hashes'][...]`.
  - Write `batch_state_sha256` into the output, and per row the root manifest sha.
  - In `render`, require `invalid['batch_state_sha256'] == proof['batch_state_sha256']`.
  - Reword the docstring and doc §3/§6: the class, mode and node splits and `llm_calls` are verified at derive time against the verified roots; `render` checks only the totals against the manifests.

### 3. MINOR: comparing B1 and grid finalists in order falsely refuses any batch with two or more finalists
- **Where.** l. 172: `list(b1['finalists']) != list(grid['finalists'])`.
- **Evidence.** `verify_b2_batch` sets `grid['finalists'] = ids`, which is registry order (b2_batch l. 182, 340). B1 `finalists` from `choose_finalists` is in μ̂-rank order, with any family extra appended.
- **Probe.** `scr/probe.py` §3: two finalists, B1 order `['qwen36_27b','gemma4_31b']`, grid in registry order. Result: `STOP: B1 finalists differ from the B2 grid finalists`. The test fixture builds both lists in the same order, so the tests do not catch it.
- **Impact now.** None, with the single finalist.
- **Fix.** Compare `sorted(...)` or sets, and keep the length/duplicate check. Add a test.

### 4. MINOR: "below the scripted anchor" needs qualifying
- **Where.** l. 362–363.
- **Evidence.** On the real frozen B1 file (sha `07cb62de…`, loaded and rendered in `scr/probe.py` §1):
  - gemma4_31b μ̂ −0.000891 [−0.001865, −0.000052];
  - scripted μ̂ −0.000587 [−0.001413, +0.000206];
  - printed difference −0.000304, "(below the scripted anchor)".

  The intervals overlap heavily, and the difference is unpaired with no interval. The line is labelled "point difference, descriptive; not a rule quantity", which is fine. The author note uses the same words. But a bare "below" in a report reads as a finding.
- **Fix.** "(point estimate below the scripted anchor's; the 95 % intervals overlap; no paired test of the difference)". If wanted, the paired instance bootstrap of the difference could be computed from the B1 manifests later; it is not needed for this template.

### 5. MINOR: the invalid-class legend misattributes context overflow, and `other_invalid` is described too narrowly
- **Where.** l. 396–398; doc §2.
- **Evidence.**
  - Context overflow after trial 1 (M19) comes from R1-EXAM-B1-MODEL-OUTPUT-INVALID (13 Nov). The legend puts it under R1-EXAM-B1-TRUNCATION-INVALID.
  - `other_invalid` is described as "harness parse or precondition failure". But the harness's `decide_trial` also gives `failed_invalid` to executed trials with a runtime error or a missing metric. An example is the node's `invalid_config` rejection, as in B1 trials 018/019 cited in the MODEL-OUTPUT row. Those land in `other_invalid` too.
- **Fix.**
  - Correct the attribution.
  - Describe `other_invalid` as "any other `failed_invalid` trial: ordinary parse failure, harness precondition failure, or an executed edit that failed or produced no metric".
  - Better: split `other_invalid` by the ledger record's `failure_category`.

### 6. MINOR: `derive_invalid` does not check that flagged journal rows land on `failed_invalid` trials
- **Where.** `classify_root`.
- **Evidence.** Probe (`scr/probe2.py`): a trial recorded as `discarded` whose last journal row has `truncated: true` is silently left out of the counts, and derive succeeds. The rules (truncation; M19/M20; M5–M9) make every such trial an invalid trial. A disagreement would be an internal inconsistency, and it should STOP rather than vanish.
- **Fix.** STOP if any trial's last journal row is `check == 'rejected'` or has `truncated`, `context_overflow` or `unencodable_reply` set, but its ledger record is missing or is not `failed_invalid`.

### 7. MINOR: the "LLM calls" column includes observer calls
- **Where.** l. 412–419.
- **Evidence.** `compute_budget.llm_calls` counts all `llm_call` / `llm_call_failed` events, observer (A4) calls included (b2_batch l. 269–272). The proposer calls are only the events without `purpose`.
- **Fix.** Label the column "LLM calls charged (proposer + A4 observer)", or add the proposer-call count (`proposal_journal.rows`).

### 8. MINOR: §8 paraphrases X.7 (b) and (c) incompletely and hints at an answer for (b)
- **Where.** l. 450–454.
- **Evidence.** RUNBOOK X.7 (b) reads "the finalist whose proposal distribution … differs most from `qwen2.5-coder:7b` *among those that fit the B.6 sweep host*; if none fits a 12 GB TITAN, the second sweep's host changes". X.7 (c) adds "if the anchors and the finalists do not differ on any C3 quantity beyond CI, the appendix reports that null and B.6 chooses by cost". Both clauses are dropped. "With one finalist there is no other finalist to choose" implies that gemma4_31b cannot be (b). X.7 does not say so. The author note says only that the X.7 role decisions are taken after the B2 report.
- **Fix.** Quote X.7 (a)–(c) verbatim, or cite them. Then: "With one finalist (`gemma4_31b`), the author decides (b), including the host-fit clause."

### 9. MINOR: the per-node B2 μ̂ bootstrap has only 4 clusters
- **Where.** §3 B2 table, per-node rows.
- **Evidence.**
  - B1 μ̂ pooled 12 node-instance clusters. Per node in B2 there are 4, so the percentile interval is coarse (35 distinct multisets) and tends to be too narrow.
  - The text calls it "the same … bootstrap as B1 μ̂". That is accurate for the pooled row only.
- **Fix.** Add "(per node: 4 clusters; interval coarse)", or print per-node intervals only for the pooled row.

### 10. MINOR: test gaps and doc wording
- **Paths the tests do not exercise (my probes show the code is correct on each):**
  - the fixture has no `mode: 'on'` audited proposals, so the `mode == 'off'` filter in §3 is never exercised. Probe §5: they are correctly excluded;
  - no exact final-Y tie. Probe §4: the lower GPU-h wins, and `rule_top` follows it;
  - no B1-order case (finding 3).
- **Refusals with no test:**
  - `invalid_trials.json` with the wrong `batch_manifests_sha256`;
  - `schema_sensitivity_rows` present;
  - `rule_version` / `author_decision_pending`;
  - rerun audits covering the wrong (node, instance) set with the right count;
  - a `thinking_on_descriptive` row with `source: 'manifest'`.
- **Doc wording.** The parametrized case `(3, finalists=['x'])` fires the sha check ("B1 analysis is not the file"), which the `(0, b1_analysis_sha256)` case already covers. The finalists check itself is covered by `test_b1_finalists_mismatch_refused_even_when_bound`. So doc §5's "19 tamperings, each refused with its own message" is slightly off; reword or retarget the case.
- **Robustness nits.**
  - `_rows` lets a raw `JSONDecodeError` / `OSError` through instead of a `STOP:`.
  - `math.isclose(g, None)` raises `TypeError` before the GPU-h STOP.
  - Primary final audits are checked for coverage by count only, while rerun audits are checked by (node, instance) set. This is harmless given the sha binding to verifier-checked manifests, but it is inconsistent.

## Verified as correct
- **Scope.** `git diff --stat aeeab991 06a33178`: only the three new files. No protected path (`r1/exam`, `r1/scripts/exam_runner.py`, configs) is touched. `a2cd540c` is an ancestor of `aeeab991`.
- **Tests.** `PYTHONDONTWRITEBYTECODE=1 … pytest -q -p no:cacheprovider r1/tests/test_b2_stop6_report.py`: 29 passed. The worktree is clean afterwards.
- **Analysis format.**
  - It reads exactly what `_b2_summary_v2` + `b2_summary_verified` + `main` write: `phase`, `label`, `rule_version`, `rule_sha256`, `rows[*].{candidate, final_y, instances, gpu_hours}`, `selection.rule_top`, `schema_sensitivity_rows`, `thinking_on_descriptive[*].{candidate, mode:'on', final_y, instances, source:'top3_thinking_on_rerun', label}`, `author_decision_pending`, `execution_label`.
  - From `batch_verification`: `batch_state_sha256`, `batch_manifests_sha256`, `authorization_checkout_head`, `b1_analysis_sha256`, and `grid` with `{verified, finalists, nodes, seeds, instances_per_node, audit_seeds, modes{cid:['off'(,'on')]}, gpu_hours}`.
  - The tests build the analysis with the real `_b2_summary_v2`.
- **Manifest format.**
  - Fields read: `final_audits`, `sensitivity_final_audits`, `audited_proposals` (both modes, with `mode`; correctly filtered to `off`), `d28_pass`, `d28_scope`, `thinking_on_d28{pass, roots, role}`, `diagnostics` (eight keys), `gpu_hours`.
  - These match `exam_runner` l. 449–474 and `verify_b2_batch`. `diagnostics.invalid` is exactly `sum(decision == 'failed_invalid')` (b2_batch l. 251; campaign.py l. 312).
- **Real B1 file.** The real frozen B1 analysis (`fcf52c09:…/complete_batch_verifier.json`, sha `07cb62de…`) has every field used: `phase` b1, `execution_label` EVIDENCE, `rule_sha256` `53018aa7…` (equal to `x5_rule_v2.yaml.sha256`), `finalists ['gemma4_31b']`, a `scripted` row with role `anchor`, `mu_hat`, `cluster_interval.{lower,upper}` and `d28_pass`. It renders end to end (probe §1).
- **`derive-invalid` reading of the roots.**
  - Paths `batch/cid/b2/mode/node__sSEED/…` match `expected_paths`.
  - Last-row-per-trial semantics match `validate_proposal_journal`; revisions are handled (tested).
  - Truncated, context-overflow and unencodable replies are forced to `parse_failed`, so their journal `check` is `not_applicable`. They therefore cannot also be `rejected`, and the class priority is immaterial.
  - Rejections are final, and the validator forces every rejected trial to be `failed_invalid`. So comparing model-output classes over `failed_invalid` trials with the root's `proposal_journal.rejected_by_check` (which counts rows) is a sound check.
  - The `diagnostics.invalid` / `trials` cross-check is sound.
- **Statistics.**
  - The Student-t interval uses `t.ppf(0.975, n−1)·sd/√n` with ddof 1 (test against 3.1824…). The per-node mean with a t interval over instances matches the power-plan estimator (R1-EXAM-B2-POWER-PLAN).
  - B2 μ̂ is computed by `analyze.bootstrap_mean` with the frozen rule's seed and resamples. The rule bytes are checked against the analysis sha.
  - Final Y is recomputed from the ten metrics (abs 1e-12) and per row from the manifest. GPU-h is checked three ways.
  - The ranking (−final_y, gpu_hours) and `rule_top` are recomputed, and the tie-break is right (probe §4).
  - The thinking-on descriptive means are recomputed from the metrics of the rerun audits.
- **Requested content.**
  - Finalist and rule pick.
  - μ̂ against the scripted anchor: B1-only, labelled descriptive. The B2 μ̂ carries the caveat that no anchor ran in B2 and that instances and seeds differ.
  - D28 for both modes plus B1, subject to finding 1.
  - Invalid trials per candidate × mode × class and per node.
  - The thinking-on rerun in its own section, marked "never enters the ranking".
  - The single-finalist sentence ("the rule pick whatever its B2 score … no second proposer among the finalists") is accurate to the hand-off §0 and the authorization note. §8 leaves X.7 to the author, subject to finding 8.
- **Doc.** Accurate to the code apart from findings 1, 2 (overclaim), 5 and 10. The limits it states (no root re-verification in derive; no precision-against-plan line; draft is not the report) are true.

## Scratch
`/tmp/pb/rev_stop6/b1.json` (real B1 analysis copy), `scr/probe.py`, `scr/probe2.py` and their fixture directories.

---

# Review R2: B2 STOP 6 report template (`mac-b2-stop6-report-20261115` @ `78481d20`, base `06a33178`)

Independent reviewer (AI-assisted, Claude). Read-only; scratch under `/tmp/pb/rev_stop6/` (`scr2/`) only.
Reviewed base = `78481d20`.

VERDICT: ACCEPT

Both MAJOR findings of R1 are fixed. Two new MINOR findings and one residual note remain. None of them blocks.

## Re-check of the R1 findings

| R1 | Status | Evidence |
|---|---|---|
| 1 MAJOR, D28 "decides eligibility" | **Fixed** | The header now reads "B2 thinking off (recorded; scope)". A new sentence says eligibility, D28 included, was decided in B1 at STOP 5 and that the B2 values are not used by the B2 ranking. The B1 column reads "decided eligibility at STOP 5". Doc §4 matches. I rendered it with the real B1 file. |
| 2 MAJOR, invalid split not bound to the verified roots | **Fixed** (see new finding A) | `derive_invalid` checks `batch_state.json` against `proof.batch_state_sha256`, then each root manifest against `completed[key].sha256` (key format equal to `verify_b2_batch`), then `root_trials.jsonl` and `b1_proposals.jsonl` against `evidence_hashes`, all before parsing. The output carries `batch_state_sha256` and `render` requires it. The docstring no longer overclaims. Tests: changed state, root manifest not in state, ledger hash mismatch, each firing its own message. |
| 3 B1 finalist order | **Fixed** | The lists are compared sorted. The new tie test uses a B1 order different from the grid's. |
| 4 anchor wording | **Fixed** (see new finding B) | Real B1 data renders: "−0.000304, a point estimate below the anchor's. Unpaired and descriptive, not a rule quantity; the two 95 % intervals overlap, so no difference is claimed." |
| 5 legend and `other_invalid` | **Fixed** | `context_overflow` and `unencodable_reply` now sit under MODEL-OUTPUT-INVALID. `other_invalid:<failure_category>` reads the ledger's `failure_category`. I confirmed that this is a top-level field of real harness ledger rows (`/tmp/pb/s04roots/*/root_trials.jsonl`). Its enum includes `proposal_precondition_failed`, `runtime_error`, `edit_failed`, `metric_missing` and `invalid_config`. |
| 6 flagged row on a non-invalid trial | **Fixed** for trials with a ledger row (residual note C) | `classify_root` STOPs. Tested for a truncated row and for a rejected row. |
| 7 LLM calls label | **Fixed** | "LLM calls (incl. A4 observer calls)". |
| 8 X.7 | **Fixed** | `X7_TEXT` is byte-identical to the X.7 cell of `RUNBOOK.md` at `aeeab991` (checked programmatically). §8 now says only "The rule pick for (a) is `gemma4_31b` (§1). Nothing in this draft decides (a), (b) or (c)." |
| 9 coarse per-node μ̂ | **Fixed** | A sentence was added. |
| 10 tests and nits | **Fixed** | 42 passed. Unreadable JSON is now a STOP. A `None` GPU-h is now a STOP. |

On the new tests:
- I traced each new tamper case. Each fires its intended check, not an earlier one:
  - `rule_version` and `author_decision_pending` fire "not an x5_rule/v2 ranking";
  - the schema rows fire their own message;
  - `source: 'manifest'` fires the descriptive-rows check;
  - `gpu_hours = None` fires "GPU-h differs";
  - changing the rerun node fires "rerun audits do not cover the grid" before any `_final_y` call;
  - the invalid file's `batch_state_sha256` fires the binding check.
- The tie test is exact: both finalists have the same metrics, so their final Y floats are identical.
- The thinking-on audited proposals in the fixture (`delta_audit` 5.0) are excluded, and the expected value is recomputed independently.
- Doc §5's count of 25 tamperings equals 18 + 7 parametrized cases.

## New findings

### A. MINOR: a hand-edit of `invalid_trials.json` after derive is still invisible to `render`; the doc's "bound to this batch" overstates
- **Where.** Doc §3, "Invalid trials": "The file is bound to this batch: its `batch_manifests_sha256` and `batch_state_sha256` equal the analysis's".
- **Evidence.** `render` compares only the declared sha strings and the per-candidate totals. My R1 per-mode swap probe still renders (`scr2/p.py`). This cannot be fixed inside `render` without the roots, so it is a limit to state, not a defect.
- **Mitigation already available.** The `derive-invalid` output is deterministic: two runs gave byte-identical files (`sort_keys`, sorted classes, fixed row order). §0 of the draft prints the file's sha256.
- **Fix.** Add to doc §6 Limits: "`render` cannot detect an edit of `invalid_trials.json` after derive. The STOP 6 reviewer re-runs `derive-invalid` on the roots and compares the sha256 printed in §0." The §3 bullet could say "declares the batch state and manifests of this batch".

### B. MINOR: the anchor sentence is illogical when the intervals do not overlap
- **Where.** l. ~402.
- **Evidence.** Probe output with non-overlapping intervals: "the two 95 % intervals do not overlap, so no difference is claimed". The "so" does not follow in that branch. The real data overlap, so the current B2 draft prints the correct branch.
- **Fix.** Use "overlap, so no difference is claimed" in one branch and "do not overlap; the comparison is still unpaired and untested, so it is descriptive only" in the other.

### C. Note (not a finding): flagged journal rows with no ledger row
`classify_root` iterates over ledger records. A truncated, overflow or unencodable last row whose `trial_id` has no ledger record is not checked: `classify_root(records=[t1 kept], journal=[t2 truncated])` returns `(0, {})`. A rejected row of that kind is still caught, because `rejected_by_check` counts journal rows. The case needs a proposer call with no trial record. The pinned harness flow creates the record in the same trial, so I consider it unreachable. Optional: iterate over `last` too.

## Verified as correct (in addition to R1's list, which still holds)
- **Scope.** `git diff --stat aeeab991 78481d20`: only the three unit files. No protected path is touched. The worktree is clean after the tests.
- **Tests.** `PYTHONDONTWRITEBYTECODE=1 … pytest -q -p no:cacheprovider r1/tests/test_b2_stop6_report.py`: 42 passed.
- **End-to-end render with the real frozen B1 analysis** (sha `07cb62de…`): §3, §4, §5 and §8 as quoted above.
- **No regression.** The analysis, manifest and rule checks are unchanged apart from the GPU-h type guard and the sorted finalist comparison.
- **D25 path and the new flagged-row STOP.** A parse-failed revision (truncated or unencodable) leaves the harness D25 loop and becomes `proposal_precondition_failed` → `failed_invalid`, so the STOP will not fire falsely there. I checked against the harness `campaign.py` D25 loop. That copy is a later harness revision than the pin `a3fedbb`, but its structure is the same.
- **The §1 single-finalist sentence** still matches the authorization note.

---

# Review R3: B2 STOP 6 report template (`mac-b2-stop6-report-20261115` @ `8745b75b`, base `78481d20`)

Independent reviewer (AI-assisted, Claude). Read-only; scratch only under `/tmp/pb/rev_stop6/`.
Reviewed base = `8745b75b`.

The first round-3 message named `2b2df4f9`. No object with that name exists in the worktree or in `/tmp/pb/repo`. The branch HEAD is `8745b75b`, one commit on `78481d20`, and the coordinator's correction confirms it.

VERDICT: ACCEPT

## Round 2 findings, re-checked
- **A (a `render` limit to state): fixed.**
  - Doc §3 now says the file "declares this batch". It adds that `render` checks the declaration, not the per-row content.
  - Doc §6 Limits now says `render` cannot detect an edit made after derive that keeps the per-candidate totals, such as moving trials between modes or nodes. The STOP 6 reviewer re-runs `derive-invalid` and compares the sha256 that §0 prints.
  - This is accurate. My probe confirms both halves: an off/on swap still renders, and two `derive-invalid` runs give byte-identical output.
- **B (anchor wording when the intervals do not overlap): fixed.** Both branches now read correctly (probe `scr2/p.py`):
  - real B1 data, where the intervals overlap: "…the two 95 % intervals overlap, so no difference is claimed.";
  - synthetic intervals that do not overlap: "…the two 95 % intervals do not overlap; the comparison is still unpaired and untested, so it is descriptive only."

  Only the sentence tail changed; the overlap test is unchanged and still correct.
- **C (note only):** left as it was, as agreed. A flagged truncated, overflow or unencodable journal row whose trial has no ledger row is not checked. I consider this unreachable in the pinned harness.

## Nothing new wrong
- `git diff --stat 78481d20 8745b75b`: one doc file (+5/−1) and `r1/scripts/b2_stop6_report.py` (+4/−2), nothing else.
- `git diff --stat aeeab991 8745b75b`: only the three unit files. No protected path is touched.
- `PYTHONDONTWRITEBYTECODE=1 … pytest -q -p no:cacheprovider r1/tests/test_b2_stop6_report.py`: 42 passed. The worktree is clean afterwards.
- The existing test assertion on the overlap wording still holds.
- Everything verified in R1 and R2 still applies, because the code is otherwise unchanged.

---

