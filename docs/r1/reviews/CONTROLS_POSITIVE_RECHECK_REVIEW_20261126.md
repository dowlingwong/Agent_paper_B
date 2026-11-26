# Re-check review: positive control (R1-CONTROLS-ROW), correction round `1baf218d`..`25d5a510` (26 November 2026)

- **Unit:** branch `origin/mac-controls-pos-20261123`, tip `25d5a510`. Correction commits: `1baf218d` (script and tests) and `25d5a510` (report and outputs).
- **First review:** `docs/r1/reviews/CONTROLS_POSITIVE_REVIEW_20261123.md` (on the branch, commit `b9a9ecb4`). It found ACCEPT WITH MINOR, with 0 MAJOR, 6 MINOR and 7 NOTE.
- **Reviewer:** a fresh Claude Code subagent, 26 Nov 2026, AI-assisted. I did not write this work, and this review is not an author decision.
- **Procedure applied:** tier E, as the caller instructed. The review is committed and re-checked until it writes "accepted".

**What I ran**
- `git fetch origin -q`, then `git diff 1baf218d~1 25d5a510` on the report, script, test and outputs.
- `git show origin/main:docs/r1/PLAN.md`, and `git merge-tree --write-tree origin/main origin/mac-controls-pos-20261123`.
- A detached worktree at the tip, removed afterwards. In it, with `/Users/wongdowling/anaconda3/bin/python3.11` (scipy 1.11.1, numpy 1.24.3), `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider` and `--basetemp` in the scratchpad:
  - `python -m pytest r1/tests/test_controls_positive.py -q`;
  - `python -m r1.noise.controls_positive --out <scratch>`, with sha256 and a field-by-field comparison against the committed outputs;
  - small scripts over the committed JSON to check the quoted ranges.
- I opened no sealed partition, test or evaluation data, credential, or `E1_D28_REPAIR` run data.

## 1. Disposition of the first review's findings

Line numbers refer to files at `25d5a510`. "Report" means `docs/r1/reports/CONTROLS_POSITIVE_20261123.md` and "script" means `r1/noise/controls_positive.py`.

### MINOR

| # | Finding | Addressed? | Evidence |
|---|---|---|---|
| m1 | report:3 "reads only the accepted 22 Oct E1 runs" left out the pinned noise source | **Yes** | report:3 now reads "Every per-edit effect comes from the accepted 22 Oct E1 runs only … For the δ_n and σ_node comparison only, the script also reads the sha256-checked pinned T0 noise source `results/r1/noise/D28_REPAIR_20261027/summary.json` … No per-edit effect is read from it". |
| m2 | "of the size the paper cares about" overstated the tested range | **Yes** | The §4.1 heading (report:206) reads "reliably detects large improvements (3.4–12.5 δ_n). Detection of effects near δ_n is moderate". report:207 gives 3.39–12.53 δ_n. New report:213–216 cover the near range (0.58–1.91 δ_n) and state the 1.91–3.39 gap as unmeasured. §4.5 (report:228) uses "eight large improvements (3.4–12.5 δ_n)". I checked the JSON: the current-start "above" improvements give `effect_over_delta_n` from 3.39 to 12.53, and the near edits from 0.58 to 1.91. Both match. |
| m3 | The plug-in sensitivity was quoted at K = 10 only | **Yes** | report:228 has "At Δ̂ − 2 se, the weakest of these cells falls to 0.534 at K = 5 (0.548 at K = 10)". report:240 (Limits) gives "0.548 at K = 10 and 0.534 at K = 5". report:195 already had both. |
| m4 | "a property of the proposals and the arms, not of the measurement" was too strong | **Yes** | report:235 now reads "rules out one explanation … a per-edit audit that cannot see large improvements. The gate's own power, and the audit's moderate sensitivity near δ_n, remain separate explanations". report:232 calls the gate's power "a property of the measurement design". |
| m5 | Optimism was claimed for every reading, but it holds for R-δ and R-0 only | **Yes** | report:123 reads "the resampled R-δ and R-0 probabilities are therefore somewhat optimistic". report:124 adds that this "does not hold for R-t in general" and gives 0.416 vs 0.458 at K = 10 and 0.198 vs 0.255 at K = 5. report:239 (Limits) is updated to match. |
| m6 | Pre-repair rows were pooled without a label (in `tables.md` Table C and the §4.5 near range) | **Yes** | **Script.** script:376–378 adds a header sentence to `tables.md`: the 'class' and 'class, kind' groups pool the pre-repair rows. The committed `tables.md` header carries it. `summarise` (script diff, +1 key) adds the 'class, start' groups. **Report.** §3.2 (report:174 and following) separates current-start rows from pre-repair rows. report:229 and :233 quote the current-start K = 5 near range, 0.413–0.758. That range agrees with the JSON (minimum `openml_ionosphere` harm 0.413, maximum `tabular_mlp` harm 0.758). |

### NOTE

| # | Finding | Addressed? | Evidence |
|---|---|---|---|
| n1 | What §1 fixed versus what `b1d0eb61` fixed | **Yes** | The new paragraph at report:104 attributes the ±2 se rule and the start flag to `b1d0eb61`. It discloses one earlier uncommitted trial run, and says that "current-start only = informative" was written after the computation. |
| n2 | The governing row was on an unpushed branch | **Yes, resolved outside the unit** | R1-CONTROLS-ROW is now on `origin/main`, `docs/r1/PLAN.md:1473`. See §3 below. Report:5 still says that the row was read on local `aaaabba3` and is not on the branch base. That is historically true but now stale (see N2 below). |
| n3 | "i.e. S = 1" needed the metric-units qualifier | **Yes** | report:49 reads "i.e. S = 1, with δ_n read in metric units on y_raw". report:9 discloses that this one clause of §1 changed after computation. |
| n4 | Audit seed sets | **Yes** | report:242 names "seeds 7001–7010" (sweep audits) and "per-instance seeds 6701–6880 (D.3 pre-declaration draft §7.2)". |
| n5 | Sonar at the pinned δ_n | **Yes** | report:225 reads "falls to 0.940 at K = 10 and 0.823 at K = 5, so the bound becomes ≥ 0.940". The JSON `Rdelta_at_pinned_delta_n` for sonar C 0.15→0.3 gives 0.940 and 0.823 (pinned δ_n 0.0034158). |
| n6 | Which copy the test compares | **Yes, by changing the test** | `test_t0_nodes_match_the_gate` (test:226–229) now imports `r1.c3.gate.T0_NODES` directly. report:74 says so. The test passes. |
| n7 | A direct source for the current-start claim | **Yes** | report:86 and :249 cite R1-D28-REPAIR (`PLAN.md:595`). On both the branch and `origin/main`, line 595 is the R1-D28-REPAIR row. |

The first review's "Not checked" item "the report's uncommitted ad-hoc K = 5 Monte Carlo check" is also resolved. The check is now committed code (`monte_carlo_check`, script:219–238), output (JSON `checks`, `tables.md` header) and a test (`test_monte_carlo_check_against_exhaustive`).

## 2. New defects from the correction round

**Diff read.** The script changes are additive:
- `CHECK_SEED_OFFSET`;
- `monte_carlo_check`;
- the `check_cases` collection;
- one extra summary key;
- header lines in `tables.md`;
- the `reviewed` field.

No existing computation path changed. The check uses its own RNG stream (`seed + 1000 + K`), so it does not disturb the K = 10 subsets (`seed + 10`). It returns `None` for non-exhaustive K, and `run()` writes checks only for exhaustive K. The new test covers both branches.

**Tests:** 15 collected, **14 passed, 1 failed**.
- The failing test is `ConstantsTests::test_critical_values`. It asserts t_{0.95,4} = 2.1318467863266495 to 10 decimal places, and this environment's scipy 1.11.1 gives 2.13184678133629, a difference of 5.0e-9.
- This test is unchanged by the correction round: it is identical at `1baf218d~1`, test:213–215.
- It is an environment-dependent tolerance, not a defect of the correction. The first reviewer ran it in a different environment and got 14/14.

**Re-run of the script at the tip.**
- `tables.md` is byte-identical: sha256 `828865bf…`, the same as the committed file.
- The committed JSON's `script_sha256` (`41978e6e…`) equals the script at the tip.
- The JSON is not byte-identical in this environment. 113 lines differ, and only in analytic float fields (`Rt_super_nct`, `*_super`, `*_fpc`) and the two `t_crit` parameters, by at most 5.0e-9. Every resampled detection probability and every `checks` value is identical.
- This is the same scipy-version effect as the failing test.

**Check figures.** The quoted figures at report:110–111 match the JSON `checks`:
- maximum absolute difference 0.0030 (R-t and R-δt);
- in Monte Carlo standard errors, 1.91 (R-0), 2.54 (R-δ) and 3.40 (R-t, R-δt).

**The "probability about 0.09" claim (report:112).** It assumes 140 comparisons, but only 113 of the 140 K = 5 cells have 0 < p < 1. With 113 cells, the chance of a two-sided maximum ≥ 3.40 is 0.073 rather than 0.090. The report already caveats the claim as not independent, and the reading does not change.

**No new defect that changes a number or a reading was found.**

## 3. R1-CONTROLS-ROW on origin/main

R1-CONTROLS-ROW is present at `origin/main` (`95249de3`), `docs/r1/PLAN.md:1473`:

> | R1-CONTROLS-ROW | **One positive and one negative control per node, reported in the appendix** (author, 23 Nov; not quoted; after Skill2Env's Oracle/NOP gate, done with noise in view). *Positive control:* for each T0 node, the probability that the K = 10 fresh-seed audit, read with the paper's audit statistic, detects each E1 single edit whose effect is known from the accepted 22 Oct runs (R1-E1-PILOT-ACCEPT), computed by resampling 10 of the 30 joint seeds; it reads only those accepted runs and can be done now (tier S). *Negative control:* … Neither control is a test or changes any gate, and neither reads a test label or evaluation value. Optional under R1-SUBMISSION-MIN's 3 Jan rule, except that the positive control is done first because it costs no runs and supports the reading of a negative gate result. |

Three related rows on `origin/main` bear on it:
- **R1-CONTROLS-NEG-DROP (PLAN.md:1476)** drops the negative control and names this branch's report as the positive control.
- **R1-STEP-ORDER (PLAN.md:1587)** withdraws the 3 Jan rule for R1-CONTROLS-ROW.
- **R1-PROCESS-TIERS (PLAN.md:1463)** covers the tier.

The unit's content matches the row as written. The row's phrase "reads only those accepted runs" is narrowed honestly by report:3, which discloses the pinned noise source.

## 4. Merge onto origin/main

`git merge-tree --write-tree origin/main origin/mac-controls-pos-20261123` exits 0 and writes tree `f83aa460325229e0665f6656f31fbe362cab4fc7`. There are no conflicts. The merge base is `53e2fe41`.

## Non-blocking notes (new)

- **N1. The tier label does not match the procedure applied.**
  - The PLAN row says "(tier S)". report:3, script:2, `tables.md` and the JSON `reviewed` field say "tier S … reviewed once … under tier S no further review follows".
  - The caller applies tier E, and R1-PROCESS-TIERS says the higher tier applies when unsure.
  - If the coordinator classifies the unit as tier E, report:3's "under tier S no further review follows" and "Reviewed once" become inaccurate after this re-check. They can be updated at merge, which would be a documentation-only change. The `reviewed` field in the JSON/script would need a regenerate, or can be left as a historical marker.
- **N2. report:5 is stale.** It says the row is not on the base branch. The row is now on `origin/main:docs/r1/PLAN.md:1473`, so a one-line update at merge is suggested.
- **N3. Brittle test and the "byte-identical" claim.**
  - `test_critical_values` uses `places=10`, which fails under scipy 1.11.1. Suggested fix: `places=7`.
  - The "byte-identical on re-run" claim (report:64) holds for the authors' library versions only. Under another scipy, the JSON analytic fields move in the 9th digit.
  - R1-AUTONOMY (3) requires zero new `r1/tests` failures for a coordinator merge. That holds only in an environment like the authors', so state the environment or relax the tolerance before relying on that clause.
- **N4. report:112.** "140 … about 0.09" would read more accurately as "113 non-degenerate cells … about 0.07". This is cosmetic.

None of these changes a number, a reading or the scope that the row and the first review set. The MINOR findings the first review raised are all fixed.

## Verdict: ACCEPTED
No blocking findings (no M#/m# items). The non-blocking notes N1–N4 are recommended at merge.
