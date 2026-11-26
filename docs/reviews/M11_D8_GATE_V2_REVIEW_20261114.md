Reviewed base: 80d70832a81a68e63b401a9d24d877abcef96b2a

# M11 D8 gate v2 — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 1. Paper branch `mac-m11-d8-v2-20261114` (from `83a12b44`). Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested.
- Round 2: **accepted** at `80d70832`. `r1/c3/gate.py` is unchanged since `da264a40` (SHA-256 02fdbdd2d92b290ae1db82cc0c881d5dd43f591bb51c10c1fe89117acfd9c873, blob 232a2835), the commit the confirmation draft names.

Accepted commit (round 2, last): 80d70832a81a68e63b401a9d24d877abcef96b2a

Round-2 notes, not blocking (left for the author; fixing them would move the reviewed base): draft item 4's "about 0.2" holds for normal differences with 6 test instances, while left-skewed differences stay at 0.52–0.63; draft item 15 should say "no T1 node" can reach 10 test instances; four reproduction-table rows in the report keep the old "spread evenly" label; the report's test counts are at `6edbb369` (at the tip the broad run is 610 passed / 35 failed / 23 skipped, the 35 failures outside D8, guard and refusal tests).

The round texts are reproduced unchanged below.

---

# Review: Unit 1, D8 gate v2 (round 1)

Reviewer: independent (Claude subagent). I did not write this unit.
Subject: branch `mac-m11-d8-v2-20261114`, worktree `/tmp/pb/wt/d8v2`, tip `6edbb369abd029f41e07e39ccddd0fb55bbb1946` (code commit `da264a40f929…`, docs commit `6edbb369…`), reviewed as `git diff 83a12b44..6edbb369`.
Inputs: runbook Unit 1 (`gh/docs/runbooks-14nov`), the runbook review's interpretations 1–4 (S1–S5), the author's Q1–Q5 answers as quoted in the start message, `MAC_OVERNIGHT_QUESTIONS_20261110.md` (`gh/mac-overnight-report-20261109`), the draft question list `/tmp/pb/questions_20261114.md`.
I did not modify the branch or worktree (`git status` clean, HEAD unchanged). I read no secrets, no sweep-2/T1 label table and no C3 label-seed data. Scratch was `/tmp/rev_u1/` and has been removed.

## 1. What I ran

| Check | Result |
|---|---|
| Commits | Both are by `Dowling Wong <wangdowling@gmail.com>`, with the `Co-Authored-By` and `Claude-Session` trailers. The code commit `da264a40` is an ancestor of the tip. The docs commit touches only the three doc files |
| `git show da264a40:r1/c3/gate.py \| sha256sum` | `02fdbdd2…c873`: matches the draft and the report. The tip and the working tree give the same value. Blob `232a2835feea…`: matches the draft |
| `analysis_guard.py` SHA | `2f6a720e…d213`: matches the draft |
| Superseded SHAs in the draft | `421a1c38` → `a75e08d3…`, `fe453fcb` → `007a484c…`, `050cb9f0` → `a078cf1f…6acd` (the same bytes as the base `83a12b44`): all correct |
| `PLAN.md`, `AUTHOR_DECISIONS_20261104.md` | Not changed in `83a12b44..6edbb369`. No author row is committed |
| 9 Nov draft | Only a 2-line SUPERSEDED banner is added at the top; nothing is removed |
| Parser: old vs new wording (synthetic PLAN, real `_confirmation_commit`) | New parser: the 9 Nov wording gives `None`, the new wording gives the commit, both sentences together give `None`, and the old SHA gives `None`. Base parser: the opposite. So the 9 Nov wording is refused |
| `/tmp/np244` (Python 3.13.18, NumPy 2.4.4) | `test_d8_gate_synthetic.py` + `test_d8_confirm_draft_matches_parser.py`: **71 passed** (as reported). `test_d8_committed_gate_binding`, `test_d8_real_git_binding_synthetic`, `test_d8_point_statistics`, `test_d8_inference_primitives`: 51 passed. (`test_c3_analysis_guard`, the refusal matrix and `legacy_verdict` cannot be collected there because scipy is missing; I ran them in trackg_venv: 197 passed) |
| Broad run, `/tmp/trackg_venv` (NumPy 2.5.3), `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin` (`a3fedbb`), `pytest -k "c3 or d8 or gate or guard or sweep" r1/tests`, in fresh clones | base `83a12b44`: **591 passed / 35 failed / 23 skipped**; tip: **598 / 35 / 23**. **The 35 failure IDs are identical** (`diff` empty). Files: `c3_sweep_table` 9, `c3_evidence_other_boundaries` 10, `c3_evidence_guards` 4, `c3_evidence_seed_isolation` 1, `c3_sweep_dryrun` 6, `c3_launch_provenance` 3, `c3_control_dryrun` 1, `d28_noise_binding` 1. This matches the report |
| New tests against the old gate (base `gate.py` placed in a tip clone) | 12 failed / 57 passed: every new or changed test fails on the old code |
| Mutations of the new gate | `>=` → `>` at DEV_Z_MIN: 1 test fails. ddof 1 → 0: 1 fails. δ_n condition dropped: 3 fail. sd = 0 always ineligible: 24 fail. `n < 2` → `n < 1`: 1 fails. Each mutation is caught |
| Strict JSON | A gate run with `dev_n`, `dev_z` and `sd = 0` nodes passes `json.dumps(..., allow_nan=False)`. `dev_z` is a float or `null` |
| Simulation re-run (`/tmp/np244`, seed 20261114, defaults) | **The tables are byte-identical to the report (l. 41–107)**. 15 s |
| Independent end-to-end check through the real gate (`_validate` → `_point` → `_bootstrap`, 8 T0 + 2 T1 nodes, 600 replicates each) | normal z = 5, n_dev = 20: P(STOP) 0.225 / P(no eligible) 0.04 / E[elig] 2.57 (report: 0.22 / 0.05 / 2.5). n_dev = 10: 0.43 / 0.38 / 0.96 (0.46 / 0.40 / 0.9). z = 3, n_dev = 10: 0.945 / 0.895 / 0.11 (0.96 / 0.90 / 0.1). Left-skewed z = 3, n_dev = 10: 0.80 / 0.05 / 2.76 (0.77 / 0.04 / 2.7). **The combination formula is confirmed** |
| Simulation in the plan-feasible regime (same script, `--n-test 6 --n-dev 2 3 6` and `--n-test 4 --n-dev 2 4`) | See S1 |
| Plan documents for Q4 | C3_DESIGN l. 62/125, TRACK_P §3.6 (l. 172–179), RUNBOOK B.1/B.1b/B.7 + additions (l. 129–196, 235), TRACK_G_RUNBOOK G.2 and **G.5** (l. 90–96), PLAN R1-BX-REVISIONS (f). See S2 |

## 2. Answer-by-answer conformance

- **Q1 (b).** Implemented exactly.
  - Removed: only the whole-gate per-suite STOP (`_check_layout`).
  - Kept: the T0 eight-node pin (with `openml_climate`), the three suite names, and the STOP for a T1 node without a pinned suite ("无套件的 1GC 任务不进 T1").
  - Added: `t1_suites_without_labelled_node`, descriptive only.
  - Changed together: the row sentence, the `analysis_guard.py` regex, the four row-text tests and the draft path. `AUTHOR_DECISIONS_20261104.md` is untouched.
  - A dev-ineligible T1 node still counts as labelled for its suite, which is consistent with the 9 Nov convention.
- **Q2 (b)+(c).** δ_n is kept: eligibility = `dev_denominator >= delta_n` AND dev z ≥ 6.
  - dev z is the paired statistic with ddof 1. n_dev < 2 → `dev_n`. With sd = 0, the sign of the mean decides, and `dev_z` is reported as `null` with `dev_sd_zero` true (for JSON). z = 6 is eligible.
  - The reasons are listed per node and in `ineligible_nodes`, and the no-eligible STOP names them. The denominator-STOP listing is unchanged.
  - The simulation was re-run. Nothing else in the statistic changed: the diff touches only the eligibility list and reporting fields, and the STOP check order (layout → no eligible → point denominators → bootstrap) is unchanged.
- **Q3.** `NUMPY_VERSION` stays `2.4.4`. `ENVIRONMENT` is recorded in the header and in `protocol`, with no Python check. The `.python-version` 3.11 discrepancy is in the question list. Correct.
- **Q4.** Not implemented. The decision is right, but the evidence is incomplete (S2).
- **Q5.** No change. Correct.

## 3. Findings

### Blocking

None. The gate code is correct, and the draft's commit, SHA and blob are right.

### Should-fix (needed before acceptance; none of them requires changing `gate.py`, so the gate SHA and the draft row can stay)

**S1. The simulation's headline regime is impossible under the plans, and in the feasible regime the dev-z rule behaves differently.**
`docs/r1/reports/M11_D8_GATE_V2_20261114.md:31–39, 110–116`; `r1/scripts/d8_stop_probability_sim.py:130–131` (defaults n_test = 20, n_dev ∈ {10, 20, 60}).

The plans don't fix the split, but they bound it:
- A T0 node has 18 instances in total for train + dev + test (RUNBOOK B.1/B.1b; TRACK_P §3.6 draws val from the training instances).
- A T1 node has "about 12 campaigns" (G.5), i.e. about 6 instances if both memory modes run as on T0.

So n_dev + n_test ≥ 30, which every reported cell assumes, cannot occur on either tier. (Interpretation S4 allowed a {10, 20, 60} grid only "if [split sizes are] not documented"; the bounds are documented.)

With the same script at plan-feasible sizes (my runs, seed 20261114):
- **n_test = 6, normal, P(eligible) by n_dev = 2 / 3 / 6:**
  - true z = 3: 0.23 / 0.14 / 0.10;
  - z = 5: 0.36 / 0.30 / 0.38;
  - z = 8: 0.56 / 0.58 / 0.87.

  At n_dev ≤ 3, dev z (a t-statistic with 1–2 df) is dominated by the sampling noise of the sd. The rule then excludes roughly half the nodes almost independently of their signal. Eligibility is not even monotone in n_dev.
- **Ten nodes, normal, z = 5:** P(STOP) old 0.42 → new 0.19 / 0.18 / 0.19, but E[eligible] is only 3.6 / 3.0 / 3.8 of 10. P(no eligible) stays small (0.01–0.03). That is the **opposite** of conclusion 2 ("P(no eligible node) is 0.40 for 10 nodes at z = 5" with a small dev split).
- **n_dev = 1** (likely for T1 under a block split of about 6 instances): every such node is ineligible (`dev_n`). Under block splits the T1 tier could leave the IQM entirely.

*Fix:*
- Add plan-bounded cells to the declared design and the committed run: T0 with n_test ∈ {4, 6, 9} and n_dev ∈ {2, 3, 6} subject to n_dev + n_test ≤ 16; T1 with n_dev ∈ {1, 2} and n_test ∈ {2, 4}, or state that T1 under block splits yields n_dev ≤ 2.
- Make the plan-feasible cells the headline, and keep the {10, 20, 60} grid as a labelled "if the splits were larger" sensitivity.
- Rewrite conclusions 1–3 accordingly.
- Update item 4 of the draft's "what confirming would mean" list (`R1_BX_D8_CONFIRM_DRAFT_20261114.md:27`), whose "the no-eligible-node STOP grows when the dev split is small" holds only at n_dev ≈ 10.

**S2. The Q4 evidence misses G.5. The decision stands, but the report and the question understate it.**
`M11_D8_GATE_V2_20261114.md:20–25`; `/tmp/pb/questions_20261114.md:3–7`.

The report cites the Track G runbook only for "2 instances × W = 10" (D28) and concludes "Neither the T1 nor the T0 test-block size per node is fixed anywhere". But G.5 (TRACK_G_RUNBOOK l. 92; RUNBOOK l. 235) plans **about 12 campaigns per T1 node**, with both memory modes "as on T0" *(proposed)*. That is ≤ 12, likely about 6, instances per T1 node, so **no split, cross-fitting included, gives a T1 node 10 test instances**. The answer's condition "若有节点计划少于 10 则不实现、回报" is therefore met on the plan evidence for T1, not merely "not excluded".

*Fix:*
- Add G.5 to §2 and to the D8-Q4 question, and say that the condition is met for T1.
- In the question, drop or qualify option (c) "a smaller minimum (e.g. 5) that the 18-instance T0 nodes can meet": T1 cannot meet 5 either under a block split. Note that option (d)'s "6/6/6" applies to T0 only.
- Add the interaction with Q2: at T1 sizes, dev z ≥ 6 makes n_dev = 1 nodes ineligible by rule and n_dev = 2 nodes near-randomly eligible (S1). A paste-ready option should let the author settle the T1 split and evaluation scheme (block vs cross-fitting) before confirming.

**S3. There is no regression test that the 9 Nov wording is refused.**
`r1/tests/test_d8_sweep2_reader_refusal_matrix.py:56–71` and `r1/tests/test_d8_committed_gate_binding.py:123–131`.

The draft asserts that the 9 Nov sentence is refused (`R1_BX_D8_CONFIRM_DRAFT_20261114.md:50`). That is true (checked above), but nothing pins it, and the 9 Nov row is the one most likely to be pasted by mistake.

*Fix:* add a `nov9_wording` variant: the new sentence replaced by `Each suite must have at least one labelled T1 node, otherwise STOP. `. Add it to the refusal-matrix VARIANTS, and add it as a mutation in `test_inexact_negative_extra_prose_or_wrong_hash_cannot_authorize`. This is test-only and the gate SHA is unchanged.

**S4. Report range error.**
`M11_D8_GATE_V2_20261114.md:114`: "P(STOP) stays at 0.66–0.94 for 10 nodes at z ≤ 6". The table gives 0.59 at z = 6, n_dev = 10 (l. 93).
*Fix:* "0.59–0.94", or "z ≤ 5". Recheck after S1.

**S5. The dev-pairing contract is under-stated.**
- `M11_D8_GATE_V2_20261114.md:123` justifies positional pairing "as the gate already requires equal lengths". Equal lengths do not imply pairing.
- Before v2, only the dev means were used, so the order of the dev vectors did not matter. Now a caller that orders dev A2 and dev oracle differently gets a wrong dev z silently: the dev split has no instance ids.

*Fix (docs only):*
- In convention 14 and in item 14 of the draft (`R1_BX_D8_CONFIRM_DRAFT_20261114.md:37`), state: "the caller must supply dev A2 and dev oracle in the same per-instance order; the gate cannot check this (the dev split carries no instance ids)".
- Optionally add an open item: dev `instance_ids` in a later input schema.
- Changing the `gate.py` docstring is not required; l. 67 already says "paired per dev instance".

**S6. The question list should flag that the row does not mention the dev-z rule.**
The CONFIRM row says the gate "implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8)". R1-BX-D8's eligibility text names only δ_n, but the confirmed bytes add dev z ≥ 6. The row binds the rule through the SHA, and the draft lists it as item 14, but PLAN's text would not show the change.

The author's answers changed the row wording for Q1 only, so not changing it is correct ("no more, no less").
*Fix:* add one question with a paste-ready choice:
- (a) keep the row as is, with the dev-z rule bound by the SHA and disclosed in the draft and report; or
- (b) add a sentence such as "IQM eligibility also requires dev z ≥ 6." That needs a parser change, a gate re-review and a redraft.

Recommend (a) or (b) as the author sees fit.

### Notes

- **N1.** `r1/c3/gate.py:72` lists the reasons as "`delta_n`, `dev_z` and `dev_n`", but l. 278–280 emit them in the order `delta_n`, `dev_n`, `dev_z`. This is harmless (`dev_n` and `dev_z` are exclusive). Align the wording at the next gate change.
- **N2.** `r1/c3/gate.py:314, 319`: the dev-z `ValueError` lacks the node name. It can newly fire on overflow-sized inputs (|v| ≳ 1e154, where `std` squares overflow), which the old gate accepted. It fails closed, which is fine. Add the node name at the next gate change.
- **N3.** `r1/scripts/d8_stop_probability_sim.py:91–93`: the scenario "z spread evenly over 3..8" is evenly spread over **grid points** (3, 3.5, 4, 4.5, 5, 6, 7, 8), so it over-weights z ≤ 5. Relabel it ("over the grid points 3–8").
- **N4.** "Reproduces 0.66" (report l. 39): the 15-node value is 0.67 from s = 0.071 (MC SE ≈ 0.004). That is within MC error of 1 − 0.93¹⁵ = 0.663, and the report discloses it. Fine.
- **N5.** Report l. 12: `excluded_from_iqm` is described as "unchanged". Its key is unchanged, but its content now also covers dev-z exclusions. Say so.
- **N6.** The question list's "D8 observation" (l. 13–14) conflates two effects: a large n_dev weakens the rule for every distribution, and left skew defeats it at every n_dev. Rewrite it after S1. The S1 findings are themselves an observation the author needs before confirming.
- **N7.** The report and commit messages cite the answers as given "in the start message of 13 Nov" and record nothing as PLAN rows: conforms to N9 of the runbook review. The Q3 handling conforms to N3.
- **N8.** The left-skewed eligibility figures (e.g. 0.27 at true z = 3, n_dev = 10) are plausible. With lognormal(0, 1) the left tail is often absent from a small dev sample, so the sample sd is small and the mean is high (rough analytic check: typical sd ≈ 0.3σ, mean ≈ μ + 0.15σ → z ≈ 8). The report's explanation is right.

## 4. Summary

The code change implements Q1–Q3 exactly, with Q4 correctly not implemented and Q5 unchanged. It is correct, fail-closed and JSON-safe, and its tests discriminate. The draft's commit, SHA and blob are correct. The reported test numbers and simulation tables reproduce exactly, and the combination formula checks out end to end through the real gate.

Changes are needed in the documents and the simulation, not in `gate.py`:
- the simulation's headline regime is infeasible under the plans, and the feasible regime changes the conclusions (S1);
- the Q4 evidence omits G.5's T1 size (S2);
- a missing regression test for the 9 Nov wording (S3);
- a factual range error (S4);
- the dev-pairing contract (S5);
- one added question (S6).

Verdict: changes requested

---

# Review: Unit 1, D8 gate v2 (round 2)

Reviewer: the same independent reviewer as round 1 (`REVIEW_U1_D8V2_round1.md`).

Subject: branch `mac-m11-d8-v2-20261114`, tip `80d70832a81a68e63b401a9d24d877abcef96b2a`. It adds two commits on `6edbb369`:
- `556460e2` (fixes);
- `80d70832` (report test note).

I did not modify the branch or worktree: `git status` is clean and HEAD is unchanged. I read no secrets, no sweep-2/T1 label table and no label-seed data. Scratch was `/tmp/rev_u1/` and has been removed.

## 1. What I ran

| Check | Result |
|---|---|
| Commits | Both are authored by `Dowling Wong <wangdowling@gmail.com>` with the `Co-Authored-By` and `Claude-Session` trailers |
| `git show 80d70832:r1/c3/gate.py \| sha256sum` | `02fdbdd2…c873`: **unchanged**. `gate.py` and `analysis_guard.py` are not touched in `6edbb369..80d70832` |
| Scope of the round-2 diff | Five files: the draft, the report, the simulation (scenario label only), and two test files (new cases only) |
| Draft row | Unchanged. `test_d8_confirm_draft_matches_parser.py` passes against the real guard |
| `/tmp/np244` (NumPy 2.4.4), in a fresh clone of the tip | `test_d8_gate_synthetic`, `test_d8_confirm_draft_matches_parser`, `test_d8_committed_gate_binding`, `test_d8_real_git_binding_synthetic`: **97 passed** |
| `/tmp/trackg_venv`: refusal matrix, `test_c3_analysis_guard`, committed binding | 175 passed (selection) |
| **Do the new 9 Nov-wording cases discriminate?** | I put the 9 Nov sentence back into a scratch copy of the guard regex. Every `nov9_partial_t1_wording` reader case then fails: `gate.evaluate`, `gate.load_and_evaluate`, `ni_masking.load_audits`, `offline_eval.assemble`, … So does the new committed-binding mutation. The cases are real, not no-op replaces |
| Broad run, trackg_venv, `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin` (`a3fedbb`), `-k "c3 or d8 or gate or guard or sweep"` | **610 passed / 35 failed / 23 skipped**. That is 598 + 12 new refusal cases. The failure distribution by file is identical to round 1's base and tip (whose failure IDs were identical), and none of the failures is a D8, guard or refusal test |
| Simulation, re-run with the commands in report §3 | `--n-test 6 --n-dev 2 4 6`, `--n-test 4 --n-dev 2 4` and `--n-test 2 --n-dev 2`: **every headline cell in the report matches**. Defaults: the reproduction tables match row-for-row except the 4 "spread" labels (N3) |
| Conclusions 1–5 against the per-node output | z = 3 eligibility is 0.094–0.369 (report: "0.09–0.37"). z = 8 is 0.557–0.857 ("0.56–0.86"). 10 nodes at z = 5, n_test = 6: 0.41 → 0.17–0.19. Spread: 0.75 → 0.20–0.30. P(no eligible) is 0.00–0.03 at z ≥ 5 and at most 0.37 at z = 3. **All correct** |

## 2. Round-1 findings

| Finding | Status |
|---|---|
| S1: plan-feasible regime | **Resolved.** The plan-bounded cells lead §3, the commands are listed, and conclusions 1–5 are rewritten and correct. The n_test = 20 cells are labelled as unreachable reproduction. Draft item 4 is updated |
| S2: Q4 evidence | **Resolved.** G.5 and RUNBOOK l. 235 are cited, and the condition is stated as met for T1, with the T0 arithmetic kept. D8-Q4 now has per-tier option (c) and notes the dev-z interaction |
| S3: 9 Nov wording test | **Resolved.** The refusal-matrix variant and the committed-binding mutation are added, and both discriminate |
| S4: range error | **Resolved.** The sentence is replaced |
| S5: dev pairing | **Resolved.** It is stated in convention 14 and in draft item 14 |
| S6: question on the row text | **Resolved.** D8-ROW is added, with options and a paste-ready line. The draft also notes that the row names neither rule |
| N1, N2 (gate wording) | Deferred to the next gate change so the SHA stays. Acceptable |
| N3 | Partly done. The script label is changed; see N3 below |
| N5, N6 | Done |

## 3. Remaining notes (non-blocking; fix when the files are next touched)

- **N-a.** `R1_BX_D8_CONFIRM_DRAFT_20261114.md:27` (item 4): "falls to about 0.2 for 10 nodes at 5 test SE" holds for normal differences with n_test = 6. With n_test = 4 or 2 it is lower (0.10, 0.00). Under left-skewed differences it stays at 0.52–0.63, which item 4 does not mention; report §3 conclusion 5 covers it.
  - *Suggested:* "…about 0.2 or less under normal differences (left-skewed: 0.5–0.6)…".
- **N-b.** Draft item 15 (l. 38): "so no node can reach 10 test instances" overstates the case for T0. A T0 node can reach 10 if train and dev together take at most 8 of its 18 instances, as report §2 correctly says.
  - *Suggested:* "so no T1 node can reach 10 test instances".
- **N3 (remainder).** The reproduction tables in report §3 still carry the old label "z spread evenly over 3..8" (4 rows), while the committed script now prints "z spread over the grid points 3..8". Otherwise they are row-identical to the script's default output.
  - *Suggested:* regenerate the tables or relabel the rows, so that they byte-match the committed script.
- **N-c.** The report's test line (§5) gives counts at `6edbb369`. At the tip the broad run is 610 / 35 / 23, with the same failure set. Optionally state that figure.

None of these affects the gate bytes, the draft row or the correctness of the conclusions.

## 4. Summary

`gate.py` is unchanged at SHA `02fdbdd2d92b290ae1db82cc0c881d5dd43f591bb51c10c1fe89117acfd9c873`, blob `232a2835feea…`, in commit `da264a40f929b114f7090da9d618402e74d94e3a`, which is the commit the draft names. All six round-1 should-fix items are resolved and verified by re-running the code. The 9 Nov wording is now refused by test. Tests pass in the pinned NumPy 2.4.4 environment, and the broad selection shows no new failures. The remaining items are wording notes.

Verdict: accepted
Accepted commit: 80d70832a81a68e63b401a9d24d877abcef96b2a
