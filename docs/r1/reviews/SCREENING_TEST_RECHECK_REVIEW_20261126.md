# Re-check review: ancestor–descendant screening test (R1-D3-CHOICES (1))

- **Unit:** branch `origin/mac-screening-test-20261122`, tip `e7392a61` (correction commits `d5a14013` for MINOR 1 and `e7392a61` for MINOR 2–5 and the NOTEs). First review: `docs/r1/reviews/SCREENING_TEST_REVIEW_20261122.md` (ACCEPT WITH MINOR), committed at `91968af2`.
- **Reviewer:** fresh Claude Code subagent, 26 Nov 2026, AI-assisted. I did not write this unit.
- **Compared against:** `origin/main` @ `95249de3`.
- **What I ran** (in a detached worktree of the tip under the session scratchpad, removed afterwards; Python 3.11, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):
  - `pytest r1/tests/test_screening_test.py -q --basetemp=<scratch>`: **13 passed** (0.8 s). It is the unit's only test file.
  - `python -m r1.noise.screening_test run --out <scratch>/run.json`: **byte-identical** to the committed `run.json`. So the docstring commit changed no code path.
  - `python -m r1.noise.screening_posthoc --out <scratch>/posthoc.json` (8.5 min): every split, count and P(SHARED/NO_SHARED/INCONCLUSIVE) is identical to the committed `posthoc.json`. The only differences are in 6 `mean_estimate` floats, at most 1.7e-16 apart (floating-point summation order).
  - `power_option_a(120, s, nsim=100, n_boot=300)` for each `POWER_SHARES` value: P(SHARED) 0.95 / 1.00 and P(NO_SHARED | kernel) 0.82. These match `posthoc_option_a_k120.json`.
  - `git diff 4b65f91c e7392a61 -- r1/noise/screening_test.py r1/tests/` shows only the 5-line docstring change from `d5a14013`. `design.json` and `run.json` are unchanged since their commits.
  - `git merge-tree --write-tree origin/main origin/mac-screening-test-20261122`: exit 0, tree `0269581f…`, no conflicts.
  - I read the full diffs of `d5a14013` and `e7392a61`, the report at the tip, `r1/noise/screening_posthoc.py`, the two posthoc JSONs, and PLAN rows R1-D3-CHOICES, R1-SCREEN-MEASURE and R1-SCREEN-MEASURE-CHOICES on `origin/main`.
  - I opened no sealed partition, evidence directory or credential file, and used no SSH.

## 1. First-review findings: addressed?

Report = `docs/r1/reports/SCREENING_TEST_20261122.md` at `e7392a61`.

| Item | Addressed? | Evidence |
|---|---|---|
| MINOR 1 (stale c0 docstring) | **Yes** | `r1/noise/screening_test.py:31-34` now states the second-distinct-hash rule and points to `identify_c0`. The §2.6 note that no code path changed is at report:133. My `run` re-run is byte-identical. |
| MINOR 2 (post-hoc comparison depends on the model) | **Yes** | report:173 says the reference puts ϱ = 0.82 on every link, while the realised g–p is 0.37 and p–c is 0.81, so the calibration is "*not supported* … not shown to be less likely". report:174-181 gives the link-kind split, +0.17 (23) / −0.14 (8), matching `posthoc.json` (0.166 / −0.140). The old "sit uneasily" sentence is gone. §4.1 is softened at report:219 as the review asked. |
| MINOR 3 (tabular NO_SHARED comes from near-duplicate links) | **Yes** | report:186: 36 of 38 eligible triples have r_pc ≥ 0.95; −0.04 (19) for triples from c0 against −0.41 (19) for later incumbents. Both match `posthoc.json`. report:187 makes the not-a-small-sample-bias point (symmetric Uniform(−1, 1); exclusions select on \|r\|). report:188 makes the smooth-error-field point. The review's sd figure (0.573 against 0.577) is not quoted, which is acceptable. |
| MINOR 4 (§4.1 moved Track S content into the manuscript) | **Yes** | "name both directions" is removed. report:220-222 keeps only "should not imply that the kernel holds on the T0 nodes". It says the negative direction rests on Track S, barred by R1-TRACKS-STOP4-END and CONSEQUENCES (9), and on unaccepted E1 PILOT data. It allows a mention only once R1-THEORY-RHO (5) is met. |
| MINOR 5 (power table has no record and is optimistic) | **Yes**, with one small record defect (n1 below) | report:237-252: the first table is labelled an **upper bound** with "shared members not modelled". Its call is recorded in `posthoc.json` `power_report_call`, and I reproduced it. An actual-overlap simulation (`screening_posthoc.power_option_a`, 15 configurations, 18 triples) was added. 120 seeds are recommended (0.95 / 1.00 / 0.82). report:249 explains the review's 0.85 against 0.86 (n_boot 200 against 300). I checked that the null kernel r^d gives zero partials for both triples of each child (d = 1, 1, 2). |
| NOTE 1 (c0 rule cannot be dated by git) | **Yes** | report:64-68: git cannot date the change, the collector facts the rule depends on (`collect.py:1008-1009`, `:379-393`), and the weak-safeguard remark. |
| NOTE 2 ("no value read" means used/emitted, not loaded) | **Yes** | report:128-131 says whole rows are parsed, value fields included. It says only the author's statement records that no value was viewed. |
| NOTE 3 (permissions; E1b touches P3 test instances) | **Yes** | report:23, E1b row: the disclosure, and the instruction to list E1b in the arms-frozen disclosure if the test is cited in the D.3 record. |
| NOTE 4 (method) | No action requested | Unchanged and acceptable. |
| NOTE 5 (E1b bootstrap degenerates at K = 6) | No action requested | Unchanged (§3.2 (d) is still descriptive). |
| NOTE 6 (wording) | **Yes** | 0.20 → 0.21 at report:106. Cost at report:256-258 now says "*wall time* … runs × 0.9 s on one worker", which is consistent (1,800 × 0.9 s = 27 min; 14,000 × 0.9 s = 3.5 h). The reserved-namespace addition is at report:236, conditional on adoption. `origin/main` R1-SCREEN-MEASURE-CHOICES (6) has since adopted 3301–3420. |
| NOTE 7 (conclusions) | No action requested | The recommendation is still labelled "recommendation, not a decision" (report:202). It is now firmer: run §4.2 before signing (report:206, 215). The reasons are given at report:210-216 and follow from MINOR 2–3. |

## 2. New defects introduced by the correction round

None blocking. Non-blocking notes:

- **n1. The recorded k = 120 command is not valid Python.** In `posthoc_option_a_k120.json`, `"command"` reads `from r1.noise import screening_posthoc as ph; ph.power_option_a(120, s, nsim=100, n_boot=300) for s in POWER_SHARES`. `ast.parse` rejects it (a bare generator, and `POWER_SHARES` is neither imported nor iterated by value). The parameters needed to reproduce (k = 120, nsim = 100, n_boot = 300, s from `POWER_SHARES`) are in the JSON fields, and I reproduced the figures from them. So report:237 "recorded with their calls" holds in substance, but the literal string is pseudo-code. *Fix when convenient:* replace it with a runnable one-liner.
- **n2. The report header is stale.** report:3 still says "Process tier: S … Nobody has reviewed it yet". report:7 cites the review. *Fix when convenient:* one line.
- **n3. The §4.2 power is for `digits_mlp`'s structure only.** It assumes 9 children and 18 triples (`screening_posthoc.DIGITS_EDITS`). report:233 says OpenML nodes give about 4–8 children each, so their power would be lower. The report does not say that the power table is per-digits. This is now overtaken on `main` by R1-SCREEN-MEASURE-CHOICES (1), under which only `digits_mlp` and `openml_climate` are testable. Informational.

`screening_posthoc.py` imports only the frozen `screening_test` functions and changes no pre-specified statistic or decision. Its outputs are labelled `post_hoc: true, reviewed: false` (`screening_posthoc.py:117`), and the report marks every split "post hoc, unreviewed".

## 3. Consistency with `origin/main`

**R1-D3-CHOICES (1)** (`docs/r1/PLAN.md:1468`): "If the test supports a shared component on a node, a seventh D.3a arm … is proposed before the D.3 pre-declaration is signed; otherwise R1-THEORY-RHO (2) stands. A1/A2 and the preregistration are not changed either way."
Branch report:206-208: "**Do not propose the seventh D.3a arm now, and run the §4.2 measurement before D.3 is signed.** Under the pre-specified mapping (§2.4), no node returned SHARED, so the row's 'otherwise' branch formally applies: R1-THEORY-RHO (2) stands. A1/A2, the preregistration and the six arms are unchanged".
→ **Consistent.**

**R1-SCREEN-MEASURE** (`docs/r1/PLAN.md:1470`): "choosing the recommendation of `reports/SCREENING_TEST_20261122.md` §4.2 on branch `mac-screening-test-20261122` … on all eight T0 nodes, the default configuration, its five E1 single edits and two-edit children c0 + e_i + e_j, each on 120 fresh joint seeds; the test of that report (pooled partial correlation of child and grandparent given the parent, bootstrap interval, SHARED above 0.1, NO_SHARED below 0.1), with the corrected power of its §4.2 (0.95 at p = 0.24; 0.82 for NO_SHARED under the kernel) … Host: deepthought CPUs (about 3.5 CPU-hours at one worker …)".
Branch: report:229-234 (c0, five E1 single edits, children c_ij, "**120 joint seeds**"); report:81-83 ("SHARED if the 95 % interval lies entirely above 0.1; NO_SHARED if it lies entirely below 0.1"); report:245 (actual overlap, 120 seeds: **0.95** / 1.00 / **0.82**); report:258 ("all eight T0 nodes: about 14,000 runs, about 3.5 hours"); report:259 (deepthought CPUs).
→ **Consistent.** The 0.95 / 0.82 the row quotes are the corrected actual-overlap figures, not the upper bound. One difference the row resolves on its own: the report proposes tier S (report:261) or, if the measurement is to enter the paper, tier E (report:262). The row chooses tier E, which is the report's second branch. (The digits-only power, n3, applies to the row's "all eight T0 nodes" wording as well. It is resolved downstream by R1-SCREEN-MEASURE-CHOICES (1).)

## 4. Merge

`git merge-tree --write-tree origin/main origin/mac-screening-test-20261122` exits 0 with tree `0269581f3e6693872ea85dfce8e93ccdd6e7c097`, with no conflict entries. The branch is not based on current `main`, but the merge is clean.

## Verdict: ACCEPTED
No blocking findings. The correction round addresses MINOR 1–5 and NOTEs 1, 2, 3 and 6. NOTEs 4, 5 and 7 needed no action. The non-blocking notes n1–n3 above may be fixed at merge time.
