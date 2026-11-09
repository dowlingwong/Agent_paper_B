# Independent review of the M11 D8 gate (mac-m11-d8-20261109), 9 Nov 2026

Freshly spawned independent statistical and code reviewer (Claude subagent; did not write the unit). Status: rounds 1–2 changes requested; round 3 **accepted** for gate bytes SHA-256 `a078cf1f862d23e6dcf10fd99135f0840afcd243bb66374645c238ab46006acd` at `050cb9f0` and the draft at `e904d5e3`. The author's questions Q1+Q2, Q3–Q6 remain open; any change to gate.py needs a redraft and re-review. Rounds copied verbatim below.

---

## Round 1

# Independent review — M11 D8 aggregate gate and R1-BX-D8-CONFIRM draft (round 1)

Reviewer: fresh independent reviewer (statistics + code), 9 Nov 2026; AI-assisted. Read-only. Scratch work in `/tmp/pb/scratch_rev_d8/`.
Unit: `/tmp/pb/wt/d8`, branch `mac-m11-d8-20261109`, commits `421a1c38` (gate + tests + report) and `962acd60` (draft).
Governing rows: PLAN §10 R1-BX-D8, R1-BX-PROPOSED-CONFIRM (D8), R1-B7-PARTIAL-T1 (+ its consequence bullets), D18, R1-BX-D1 (suites, T0 testbed); briefing `reports/MAC_M11_B2_AUTHOR_QUESTIONS_20261108.md`; inventory `reports/M11_SWEEP2_READER_INVENTORY_20261108.md`; runbook §0, §4.

## What I verified (no finding)

- Tests: the given command gives 284 passed, 4 failed. The 4 failures are all in `test_c3_evidence_guards.py`, and the same 4 fail on a `git archive` of HEAD~2. All new tests pass.
- Merges `c517696b`, `537ea96e`, `f7b4b699`, `1b6f8e73`: `git show --cc` is empty, so none has a manual resolution. HEAD~2..HEAD only adds files: no deletions, and `PLAN.md` is untouched. Every commit's author is `Dowling Wong <wangdowling@gmail.com>`.
- The draft's SHA-256 `a75e08d3…280e` equals `git show 421a1c38:r1/c3/gate.py | sha256sum`, and also the gate at HEAD. The blob `f23557e1…` matches. The SHAs of `d8_point_statistics.py` and `analysis_guard.py` match the files. The draft is clearly marked non-authority, it is not in PLAN, and it records no author decision. The real guard on the worktree refuses with "STOP: exact affirmative R1-BX-D8-CONFIRM … required".
- Statistic against the rows:
  - gap closed is a ratio of means on test instances;
  - dev eligibility uses the dev mean of oracle minus the dev mean of A2, compared with δ_n;
  - excluded nodes are listed and stay in the PoI;
  - PoI uses ties ½, a per-node share, then a plain mean over all nodes;
  - 2,000 within-node resamples share one index draw across A2, oracle, A3 and A5;
  - 97.5 %/95 % one-sided lower bounds; pass requires strict LB_IQM > 0 and LB_PoI > 0.5; the gate verdict is "first-ranked arm passes";
  - the practical size 0.1 is reported only; tier is reported as a stratum.
- Independent recomputation (`scratch_rev_d8/indep.py`) on the test's `noisy_table`, using my own quantile-integral IQM, my own PoI and my own bootstrap (different RNG, 40,000 resamples):
  - point IQM matches to 1e-6 (numerical integration) and PoI exactly;
  - LB_IQM(A3, 97.5 %): 0.193 (mine) vs 0.199 (gate);
  - LB_PoI(A3): 0.6806 vs 0.6806;
  - A5 at 95 %: LB_IQM −0.0006 vs −0.0025;
  - all within Monte Carlo error.
- I checked the degenerate known answers by hand (IQM of {.2,.4,.6,.8} = 0.5; the PoI values in the dev-exclusion test, 0.75 and 0.875).
- The Holm logic is valid in principle. With m = 2, ranking by the arms' own p-values and testing the smaller at α/2 is Holm, so the data-dependent ranking is not a problem in itself. The gate verdict ("first-ranked arm passes") is equivalent to min(p_A3, p_A5) ≤ α/2, which is Bonferroni and has FWER ≤ α for any dependence. The per-arm composite p = max(p_IQM, p_PoI) is the intersection-union p-value, matching the "both bounds" pass rule. Validity is asymptotic (percentile bootstrap) and the IUT is conservative. The report leaves this as an open question; it can say this (see note 14). One exact-boundary defect is listed in finding 4.
- The refusal matrix discriminates. With `require_d8_confirmation` replaced by a no-op (`scratch_rev_d8/test_discrim.py`), every reader in the matrix goes on to open label files: `JSONDecodeError` on the synthetic bytes, or `FileNotFoundError` for `evidence_plan`, never a "STOP" `RuntimeError`. With the real guard each one raises "STOP: exact affirmative R1-BX-D8-CONFIRM …". So the refusal really comes from the D8 check, and it comes before label files are opened.
- Prefix versus exact match: the parser requires the first cell to *equal* `R1-BX-D8-CONFIRM`. That is strictly stronger than the runbook's "starts with", so "refuses without a starts-with row" follows. It fails closed, and report line 45 and the draft's "Format constraints" disclose it. I accept this; see note 13 for one more sentence.

## Findings

### Blocking

1. **The gate cannot run on the intended node layout (8 T0 CPU nodes + T1 nodes from three suites). It always STOPs, or it forces a mislabelled suite.** `r1/c3/gate.py:133-135, 168-170`.
   - Every node, T0 included, must carry a `suite` that is in `expected_suites`, and every expected suite needs a T1 node.
   - Under R1-BX-D1 (PLAN l.745-746) the suites are the GPU benchmark suites. The 8 CPU nodes are "tier T0, the controlled testbed" and belong to no suite.
   - Reproduced in `scratch_rev_d8/t1_suite.py` (8 T0 nodes with suite `cpu_testbed`, plus 2 T1 nodes in each of three suites):
     - listing `cpu_testbed` gives `GateStop: suites without a labelled T1 node: ['cpu_testbed']`;
     - leaving it out gives `ValueError: node cpu0 has a suite outside expected_suites`.
   - The only way to get a result is to assign CPU nodes to a GPU suite they do not belong to.
   - The synthetic tests hide this, because they place T0 nodes inside suites that also have T1 nodes (`test_d8_gate_synthetic.py:44-45, 143, 279-285`).
   - **Fix:**
     - allow `suite: null` (or omit the field) for T0 nodes, and require a suite only for T1 nodes;
     - run the per-suite T1 check over the GPU suites in `expected_suites` only;
     - add a test with exactly this layout (T0 nodes without a suite plus three T1 suites passes; one suite without a T1 node STOPs).
   - Also state the semantic point in the report as a preregistration candidate. The R1-B7-PARTIAL-T1 consequence (PLAN l.1007; AUTHOR_DECISIONS_20261104 l.160) ties the "≥ 1 labelled T1 node per suite, otherwise STOP" condition to *leave-one-suite-out*, not to the aggregate D8 gate. The code makes it a whole-gate STOP. The parser's row text ("Each suite must have at least one labelled T1 node, otherwise STOP") supports that reading. Still, the report cites the source as "R1-B7-PARTIAL-T1 and its consequences" (report l.23) without saying that it is extending a LOSO precondition to the aggregate gate. List it among the conventions so the author sees it.

2. **The preregistered statistic is not fully bound by the SHA the author would confirm.** `r1/c3/gate.py:59`; report l.46; draft l.14-16.
   - The IQM definition (fractional-edge trimmed mean, briefing option A) and the point PoI live in `r1/c3/d8_point_statistics.py`, which the guard does not check.
   - After confirmation, an edit to `node_iqm` would change the gate result without invalidating R1-BX-D8-CONFIRM. That defeats the purpose of "the sha of the gate code" in R1-BX-D8.
   - The report discloses this as an "open question", but the fix lies entirely inside this unit and is cheap.
   - **Fix:** either inline the two functions in `gate.py`, or pin `POINT_STATISTICS_SHA256 = '0c90702e…'` in `gate.py` and have `evaluate`/`load_and_evaluate` refuse (STOP) unless both of these equal the pin:
     - the bytes of the imported module file;
     - the committed bytes `git show HEAD:r1/c3/d8_point_statistics.py`.
   - Do the same for NumPy: pin `NUMPY_VERSION = '2.5.3'` (or whatever the analysis venv pins) and STOP on a mismatch, rather than only recording it. The report itself says that `Generator` streams are not stable across versions (report l.31). The pins then fall under the gate SHA. Add tests for both refusals, then redraft the CONFIRM row with the new SHA.

### Should-fix

3. **The whole-gate STOP on any nonpositive resampled denominator will often make the gate unreadable, and the report does not say so.** `r1/c3/gate.py:219-224`; report l.34, l.48.
   - Dev eligibility (dev denominator ≥ δ_n, a practical size) does not control the *test* denominator's distance from 0 in standard-error units.
   - My simulation (`scratch_rev_d8/stopsim.py`) puts the chance that one node STOPs the gate at:

     | Test denominator, in SE units | P(this node STOPs the gate) |
     |---|---|
     | 3 | about 0.52–0.58 |
     | 4 | about 0.23–0.32 |
     | 5 | about 0.06–0.08 |

     (n = 20–60 instances.) With 10–20 IQM nodes, a STOP is a realistic outcome.
   - The STOP is the briefing's conservative option A and is listed as a convention. But the author would be confirming it without knowing this. The briefing already warned that it "may leave the gate unreadable"; the report drops that warning.
   - **Fix:**
     - add a short, quantified disclosure to the report and the draft (the table above, or your own Monte Carlo study);
     - add the STOP probability in terms of the test denominator's z-score as an explicit author question;
     - list alternatives the author could choose before confirmation, for example: an SE-aware eligibility rule on the dev split; or keeping the STOP but reporting how many nodes would have triggered it.
   - Do not change the rule yourself.

4. **Ranking and pass test disagree at the exact boundary, so the verdict can depend on arm labels.** `r1/c3/gate.py:244-257`.
   - The ranking uses p = P*(θ* ≤ null), but the pass test uses the linearly interpolated quantile. With B = 2000 they agree except when exactly 50 (or 100) draws are ≤ null.
   - Demonstrated in `scratch_rev_d8/holm_tie.py`:
     - A3 and A5 both have composite p = 0.025;
     - A3's interpolated LB is −0.015 and A5's is +1.0;
     - the tie-break ranks A3 first, so the verdict is FAIL;
     - with the labels swapped, the verdict is PASS.
   - This contradicts report l.33 ("the uncentered tail share is the dual quantity").
   - **Fix:** rank by a key that is exactly dual to the pass test, for example `(not passes_at(0.975), p_comp, ARMS.index(arm))`. Alternatively, define pass directly as p_comp < 1 − L. Add the boundary case above as a test. Correct the duality sentence.

5. **The refusal-matrix claim "every visible sweep-2 reader in the 8 November inventory" is not accurate.** `r1/tests/test_d8_sweep2_reader_refusal_matrix.py:101-109`; report l.41.
   - The inventory lists `env.label_rows` (author-held; it can be *called* without editing) and `audit._verify_replay`. Neither is in `READERS`.
   - R1-BX-D8 names "`dataset` build of evaluation columns", that is `dataset.build_from_sweep` (`dataset.py:445-455`). It is not covered either.
   - I checked in `scratch_rev_d8/test_more.py` that `build_from_sweep` and `env.label_rows` do refuse with the D8 message, and that `build_from_sweep` opens no index bytes first. So these are coverage gaps, not live holes.
   - **Fix:**
     - add `env.label_rows`, `dataset.build_from_sweep` (index under `<paper>/results/r1/pilot/`), `audit._verify_replay` and `audit.evidence_blocks` to the matrix;
     - change `match='STOP'` to `match='R1-BX-D8-CONFIRM'`, so each case proves the cause;
     - state in the report that "Track P loaders" (also named in R1-BX-D8) are covered only to the extent the inventory found no Track P sweep-2 table reader.

6. **The draft's list of what confirming "fixes" is incomplete.** Draft l.20; report l.27-35.
   - These choices are not fixed by the PLAN rows (or rest only on a briefing recommendation, which is not an author ruling) but are missing from the convention list:
     - the ratio-of-means reading of "gap closed" (report l.15 cites R1-BX-D8, but the row does not say "mean");
     - the fractional-edge IQM (briefing §1 option A);
     - ties defined by exact floating-point equality;
     - the whole-gate partial-T1 STOP (finding 1);
     - `expected_suites` and the node list being supplied by the caller (finding 7);
     - the dependency pins (finding 2).
   - **Fix:** extend the "Implementation conventions" list and the draft paragraph so the author sees every choice the SHA would freeze.

7. **Completeness of the node set is not checked: nodes can be dropped silently by the caller.** `r1/c3/gate.py:114-135`.
   - `expected_suites` and the node list both come from the input file. A caller can leave out an awkward node, or a whole suite together with its nodes. The gate cannot tell, which goes against the PLAN's "no node is dropped silently" principle.
   - The partial-T1 rule means the T1 list cannot be fixed in advance. But the 8 T0 node ids and the suite names are known now.
   - **Fix:** pin `T0_NODES` and `SUITES` as constants (bound by the SHA), and STOP if a T0 node is missing or a suite is unknown. If that is not wanted, disclose it under "Input provenance".
   - Also state that `delta_n` must be in the same 20-run-scaled utility units as U (D18). The gate cannot check this. See also note 10.

### Notes

8. **Very small nodes.** Accepting n_test = 1 (or 2) gives a zero-variance (or nearly zero) bootstrap contribution and a node-equal-weighted PoI of 0, ½ or 1, so tiny nodes carry outsized, falsely certain weight. The percentile bootstrap also understates variance by about (n−1)/n. Consider a predeclared minimum n_test (refuse or STOP below it) as a preregistration candidate. The report already lists small-node behaviour as "not shown".

9. **Overflow of extreme finite inputs.** Finite values near 1e308 make a mean overflow. A NaN `dev_denominator` then makes `nan >= delta_n` False, so the node is *silently excluded* from the IQM (`gate.py:164, 181`). Check that `dev_denominator` and the test means are finite, and raise ValueError otherwise.

10. **Duplicate JSON keys.** `json.load` keeps the last of two duplicate keys silently (`gate.py:325-326`). Use `object_pairs_hook` to refuse duplicates in the gate input.

11. **The accepted primitives are not used.** The gate re-implements resampling and Holm instead of using the accepted `d8_inference_primitives.stratified_indices` and `holm_two`. That is fine (performance, NumPy stream), but the report should say so. A cheap consistency test: pass the composite p-values through `holm_two` and check that the adjusted p ≤ 0.05 agrees with the gate's verdict away from the boundary.

12. **The executing file is not tied to the checked file.** `gate_file_sha256()` reads the executing `__file__`, while the guard checks `REPO/r1/c3/gate.py`. Consider refusing when `Path(__file__).resolve() != REPO/'r1/c3/gate.py'` (or when the SHAs differ). The import-then-check TOCTOU is already disclosed.

13. **The 4 Nov template uses a dated ID cell.** The author's template in `AUTHOR_DECISIONS_20261104.md` l.170 has `| R1-BX-D8-CONFIRM (date) | …` and different wording. Say explicitly in the draft that this form would be *refused*, so the author does not paste the template. Also say that the commit named must survive integration: no squash or rebase of `421a1c38`, or its successor after the fixes.

14. **Report wording.**
    - Report l.33 refers to "§ open questions", which does not exist.
    - Add the Holm/Bonferroni validity argument from "What I verified" above in place of "whether the ranking statistic matters is open".
    - State that the inference is conditional on the fixed node set: nodes are not resampled, so the intervals cover instance noise only, and claims should read "for these nodes".

## Summary

The statistic matches the governing rows, an independent recomputation agrees, the Holm/IUT structure is valid, the refusal matrix really exercises the D8 check, and the draft's SHA, commit and non-authority status are correct. Two defects block acceptance:
- (1) the input schema makes the gate impossible to run on the actual T0 + three-suite layout;
- (2) the IQM/PoI core and NumPy version are outside the bytes the CONFIRM row binds.

Findings 3–7 are disclosure and coverage fixes the author needs before confirming. After the fixes the gate SHA changes, so the draft must be redrafted and re-checked.

VERDICT: changes requested

---

## Round 2

# Independent review — M11 D8 aggregate gate and R1-BX-D8-CONFIRM draft (round 2)

Reviewer: the same independent reviewer as round 1 (statistics + code), 9 Nov 2026; AI-assisted. Read-only. Scratch work in `/tmp/pb/scratch_rev_d8/`.

**What I reviewed.** Two new commits on `mac-m11-d8-20261109`:
- `fe453fcb` — gate, tests, report;
- `e00a1db0` — redrafted draft and `docs/r1/reviews/M11_D8_REVIEW_ANSWERS_20261109.md`.

The round-1 findings are in `REVIEW_M11_D8_round1.md`.

## Basic checks

- **Tests.** The unit's command gives 366 passed and 4 failed. The 4 failures are the same pre-existing ones in `test_c3_evidence_guards.py`.
- **Tests under the pinned NumPy.** I ran `test_d8_gate_synthetic.py` in a scratch venv with NumPy 2.4.4 (the pin): 61 passed.
- **History and authorship.**
  - No deletions.
  - The two commits change no files besides the six named. `PLAN.md`, `env.py`, `analysis_guard.py` and `d8_point_statistics.py` are untouched.
  - Both commits are authored by Dowling Wong <wangdowling@gmail.com>.
- **Draft identifiers.** All three values in the draft are correct:
  - SHA-256 `007a484c…693c` equals `git show fe453fcb:r1/c3/gate.py | sha256sum` and HEAD's gate.
  - Blob `2859f38e…` matches.
  - Commit `fe453fcb` is correct.
- **Draft status.** The draft is still clearly non-authority and is not pasted into PLAN. It now says explicitly that the 4 Nov dated-template form would be refused, and that the named commit must be merged, not squashed or rebased.

## Round-1 findings

| # | Status | Evidence |
|---|---|---|
| 1 Real layout | **Mechanism fixed; pinned content wrong. See new finding R2-1.** | T0 nodes with `suite: null` plus three pinned T1 suites now run (`scratch/t1_suite2.py`). The per-suite STOP runs over T1 suites only. `expected_suites` is gone. |
| 1 Partial-T1 semantics | **Accepted as disclosed.** | The whole-gate STOP is kept. That is stricter than the LOSO scope of the consequence, and it is the reading that the parser-required row text supports. It is disclosed honestly: convention 10, draft item 10, Q1 with options. This is the author's call, and fail-closed is the right default until he decides. |
| 2 SHA binds the whole statistic | **Fixed.** | `_node_iqm` and `_node_poi` are inlined, with an equality test against the accepted core. Imports are pinned (test l.512). Details on the NumPy pin are below. |
| 3 Whole-gate STOP probability | **Fixed (disclosed and quantified).** | The report's table agrees with my `stopsim.py` (normal case: z = 4 gives ≈ 0.23–0.31, z = 5 gives ≈ 0.07–0.08). The gate-level 1 − (1 − p)^m figures are correct. Q3 offers real alternatives, and the gate now lists all offending nodes. The skewed-distribution rows are a useful addition. |
| 4 Holm boundary | **Fixed.** | Ranking key: (fails at 97.5 %, composite p, arm order). See the Holm section below. |
| 5 Refusal coverage | **Fixed.** | Added `env.label_rows` (called only), `audit._verify_replay`, `audit.evidence_blocks` and `dataset.build_from_sweep`. A synthetic sweep-2 index is also checked as not opened. `match='^STOP: .*R1-BX-D8-CONFIRM'` proves the cause. My round-1 no-op check showed the original readers fail later without the guard. The Track P statement is accurate and bounded. |
| 6 Convention list | **Fixed** (13 items in the report and the draft), except that item 9 carries the wrong T0 list (R2-1). |
| 7 Completeness / δ_n units | **Fixed**, with the T1-list limit disclosed. The δ_n units are documented in the docstring and in convention 11. |
| Notes 8–14 | **All addressed.** | Tiny nodes: Q5. Overflow: a 4·n·max\|v\| bound plus a finite dev denominator. JSON: `object_pairs_hook` and `parse_constant`. Primitives: disclosed, with a `holm_two` agreement test. Executing file: bound to `REPO/r1/c3/gate.py` by path and bytes. Template and commit survival: in the draft. Report wording: fixed. |

**Holm (point 3 of the coordinator).** An arm that passes at 97.5 % has a dual p ≤ 0.025, so ranking it first is still Holm on the dual p-values. When both arms pass at 97.5 %, the second also passes at 95 %, because the quantile is monotone in the level. When neither passes, the gate fails whatever the order. So the verdict is exactly "some arm passes at 97.5 %", which is the Bonferroni rule with FWER ≤ α. Checks I ran:
- `holm_tie.py`: PASS under both labellings.
- My own property check (`swap2.py`): 3,000 random boundary cases at 49/50/51 and 99/100/101 draws, also with PoI near the boundary.
  - A label swap changed no verdict and no passing set.
  - The verdict equalled `any(_passes(arm, 0.975))` in every case.

**NumPy pin (point 2 of the coordinator).**
- **How tests handle the container's 2.5.3.** The `confirmed` fixture sets `gate.NUMPY_VERSION` to the running version. The pin itself has dedicated tests: a mismatch STOPs before the file is opened, and a match runs. This is sound.
- **Verified independently.** In a scratch venv with NumPy 2.4.4, `_evaluate` output on six noisy real-layout tables was **byte-identical** to 2.5.3 (`dump_np244.json` against the 2.5.3 dump). The synthetic test file passes under 2.4.4.
- **Is 2.4.4 defensible?** Yes, as a fail-closed placeholder.
  - It is the harness `uv.lock` pin.
  - The paper repo has no lock of its own (`pyproject.toml`: `numpy>=1.24`).
  - A wrong pin produces a STOP, never a silently different result.
  - It is correctly an **author question (Q4)**: the pin must equal the NumPy of the venv that will actually run the gate, and only the author or operator can name that venv.
- **Not a finding.** Recording the 2.4.4 vs 2.5.3 identity check in the report is enough. Answering Q4 with a different version changes the SHA, as the draft says.

## New findings

### Blocking

**R2-1. `T0_NODES` pins the wrong eighth node. The authorized sweep set has `openml_climate`, not `openml_blood_transfusion`.**
- **Where:**
  - `r1/c3/gate.py:96-98` (and the docstring at l.31-33);
  - report convention 9 and Q2;
  - draft item 9.
- **What the gate pins:** the R1-DT-PIN (26 Oct) list.
- **Why that list is out of date.** R1-DT-PIN was superseded for the run that actually happened by R1-DT-PIN-SWEEP1 (27 Oct), which defers to `docs/r1/authorizations/c3_sweep1_20261027.md`. That authorization says:
  - l.8: "Eight nodes: … `openml_sonar`, `openml_climate`. Climate substitutes for blood_transfusion, which failed D21, after passing its own D21 and D28."
- **Other sources that agree with the authorization:**
  - `docs/r1/reports/DT_SWEEP1_READINESS_20261027.md` l.7 and l.22: blood_transfusion "is not re-run or used".
  - The accepted evidence classifier `r1/c3/dataset.py:303-304`, which requires exactly those eight, with climate.
  - `r1/scripts/configs/c3_sweep_deepthought.json`.
- **Why sweep 2 uses the same set.** Sweep 2 is "the B.1 design … on the same instances" (RUNBOOK B.1b). Its T0 nodes are therefore the sweep-1 eight.
- **Reproduced** (`scratch_rev_d8/t1_suite2.py`). A real-layout table built from the authorized eight STOPs with "missing ['openml_blood_transfusion'], unexpected ['openml_climate']".
- **Why this is blocking.** The outcome fails closed, so it is not a silent wrong result. But:
  - the draft asks the author to confirm a node list that contradicts his own authorization;
  - Q2 recommends "confirm the pins";
  - once confirmed, the gate could never be read on the real data without a new SHA and a new CONFIRM row.
- **Likely source.** The stale `D21_NODES` constant in `r1/scripts/c3_label_sweep.py:119`. That file is not in this unit; mention it in the report as a known stale constant, and do not edit it here.
- **Fix:**
  1. Set `T0_NODES` to `digits_mlp, openml_breast_w, openml_climate, openml_credit_approval, openml_ionosphere, openml_sonar, openml_wdbc, tabular_mlp`. Cite R1-DT-PIN-SWEEP1, `c3_sweep1_20261027.md` and R1-D28-REPAIR (substitution) in the code and in convention 9.
  2. Add a test asserting that `set(gate.T0_NODES)` equals the node list required by the accepted classifier (`dataset.py:303-304`) and the deepthought sweep config. A future drift then breaks a test instead of the gate.
  3. Update Q2. State the substitution explicitly, and keep it a question whether sweep 2's T0 set is the sweep-1 set: recommended yes, per B.1b.
  4. Re-hash, redraft the row with the new commit, SHA and blob, and update the answers file.

### Notes

**R2-2. Extreme magnitudes in the ratio.** A tiny positive test denominator with a large numerator can still give an infinite gap. `_node_iqm` then raises `ValueError` (fail-closed, not a STOP). This is acceptable; one sentence under convention 12 would make it explicit.

**R2-3. Interaction of Q1 and Q2.** If the author later allows suite-less 1GC dataset T1 nodes (Q2), the per-suite rule (Q1) and the T1 suite check both need changing. The recommendation text already says this; just keep the two questions together when presenting them to the author.

## Summary

Every round-1 finding is fixed or honestly disclosed as an author question:
- the layout mechanism, the inlined statistic, the NumPy pin, the Holm key, the refusal coverage, the STOP quantification and the convention list;
- the whole-gate partial-T1 STOP and the 2.4.4 pin are acceptable as disclosed, fail-closed author questions (Q1, Q4).

One new blocking defect remains: the pinned T0 node list names `openml_blood_transfusion` where the authorized sweep set (and the accepted evidence classifier) has `openml_climate`. After that one-constant fix, the drift test, the Q2 wording and the redraft, I expect to accept.

VERDICT: changes requested

---

## Round 3

# Independent review — M11 D8 aggregate gate and R1-BX-D8-CONFIRM draft (round 3)

Reviewer: the same independent reviewer as rounds 1–2 (statistics + code), 9 Nov 2026; AI-assisted. Read-only. Scratch work in `/tmp/pb/scratch_rev_d8/`.

What I reviewed: `050cb9f0` (T0 pin, test, report) and `e904d5e3` (redrafted row, answers for round 2) on `mac-m11-d8-20261109`.

## Checks

- **Tests:** the unit's command gives 367 passed and 4 failed. The 4 failures are the same pre-existing ones in `test_c3_evidence_guards.py`.
  - Under NumPy 2.4.4 (scratch venv), `test_d8_gate_synthetic.py` gives 62 passed.
- **The gate diff is limited to the R2-1 fix:**
  - `T0_NODES` now holds `openml_climate` instead of `openml_blood_transfusion`;
  - the docstring and comment cite R1-DT-PIN-SWEEP1, `c3_sweep1_20261027.md`, R1-D28-REPAIR and DT_SWEEP1_READINESS.
  - No other code changed.
- **The T0 set is now the authorized sweep set:**
  - my `t1_suite2.py` table, built from the authorized eight with three T1 suites, now PASSes instead of STOPping;
  - the new test `test_t0_nodes_equal_the_classifier_and_the_authorized_sweep_config` parses the literal `nodes` list inside `dataset.evidence_classification` (AST, exactly one assignment) and reads `c3_sweep_deepthought.json`. It asserts set equality, 8 unique ids and no pending nodes, so future drift breaks a test.
  - The extra-node test now uses `openml_blood_transfusion`, which is correct.
- **Holm:** I re-ran my boundary property check (`swap2.py`, 3,000 cases). A label swap changed no verdict and no set of passing arms.
- **The draft names the new bytes correctly:**
  - commit `050cb9f0`;
  - SHA-256 `a078cf1f…6acd`, which equals `git show 050cb9f0:r1/c3/gate.py | sha256sum` and the gate at HEAD;
  - blob `7ae776ea…`.
  - The parser-match test passes with these values.
  - Item 9 lists climate and the substitution.
  - The draft is still marked non-authority, and PLAN has no `R1-BX-D8-CONFIRM` table row.
- **Report and answers:**
  - convention 9 and its sources are updated;
  - convention 12 now states that an infinite gap gives a fail-closed `ValueError`;
  - Q1 and Q2 are merged into one question, with their interaction and the sweep-2 T0 question stated;
  - the stale `D21_NODES` in `r1/scripts/c3_label_sweep.py` is mentioned in the report only, and that file is unchanged;
  - the answers file has a round-2 section.
- **No deletions; nothing outside the unit touched:**
  - no files deleted;
  - `PLAN.md`, `r1/scripts` and `dataset.py` are untouched;
  - both commits are authored by Dowling Wong <wangdowling@gmail.com>.

## Findings

None blocking and none should-fix.

**Note:** the author questions Q1+Q2 and Q3–Q6 must be answered before the row is pasted, as the report and the draft already say. An answer that changes `gate.py` changes the SHA and needs a redraft and a re-review. This acceptance covers the gate bytes `a078cf1f…6acd` at `050cb9f0` and the draft at `e904d5e3` as they stand.

## Summary

R2-1 is fixed, and a drift test now guards it. Both round-2 notes are addressed. All round-1 fixes still hold: the layout mechanism, the inlined statistic and NumPy pin, the Holm key that ranks an arm passing at 97.5 % first, the extended refusal matrix, the quantified STOP probability and the convention list. The draft correctly names the reviewed bytes and stays non-authority.

VERDICT: accepted
