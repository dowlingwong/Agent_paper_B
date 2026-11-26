Reviewed base: 82923797c12f8b55f27f4336c51719e2f3bd5fca

# M11 D8: eligibility alternatives and split proportions — independent review record (14 November 2026)

Branch `mac-m11-d8-alt-20261114`, from `mac-m11-d8-v2-20261114` @ `e3c0921e`. Synthetic simulation and report answering the author's 14 Nov D8 message: (i) eligibility on train + dev, (ii) a D21 σ_node threshold; P(STOP), excluded share, P(T1 kept); Q4 proportions and floors; Q3b and ROW recorded. `gate.py` unchanged. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`e1469124`): changes requested (§3.4 attributed all P(STOP) to the test side, false for strict rules at low and middle μ; §3.3 misread the r = 0.5 excluded share). Script and outputs reproduced byte-identically.
- Round 2 (`82923797`): **accepted**; P(STOP) split into "no node eligible" and test-side parts (all 25 cells match the json); round-1 notes N1–N9 addressed; outputs still byte-identical.

Accepted commit (round 2, last): 82923797c12f8b55f27f4336c51719e2f3bd5fca

Notes, not blocking: N10, "z ≥ 3 has the highest P(STOP)" holds from μ = 1 (tied with R2-trdev r ≤ 1), not at μ ≤ 0.5; N11, §4 says R1 "keeps T1" without the μ qualifier that §3.2 now has. The n_test side calculation in §2 is not in the committed script (seed 20261115); the reviewer's independent runs agree within Monte Carlo error.

The round texts are reproduced unchanged below.

---

# Review: D8 eligibility alternatives, round 1

Reviewed commit: e1469124e534718b529fbf1e31b95fee258f2db3
Branch: `mac-m11-d8-alt-20261114` (worktree /tmp/pb/wt/d8alt), base e3c0921e. Independent reviewer (AI-assisted, Claude); read-only.

## What was checked

1. **The script reproduces exactly.** I reran `r1/scripts/d8_eligibility_alternatives_sim.py --json` with `/tmp/np244/bin/python -I` (NumPy 2.4.4, Python 3.13.18) in scratch. Both outputs are byte-identical to the committed files:
   - `sim_output.md` sha256 72a15e9e…7099;
   - `sim_output.json` sha256 e8def174…fda.

   Model checks:
   - **Split sizes.** P1 gives 6/6/6, 4/4/4 and 2/2/2; P2 gives 9/3/6, 6/2/4 and 3/1/2. These are correct.
   - **R0** is the paired t on dev with ddof 1. Like gate.py it treats n_dev < 2 as ineligible and sd = 0 as eligible if the mean is > 0.
   - **R1** is the same statistic on train + dev.
   - **R2** computes z = m·√n / r. Under the model this is N(μ√n/r, 1/r²), so P(eligible) = Φ(μ√n − c·r). An analytic check of every normal R2 cell agrees within MC error.
   - **Test STOP** fires on a point mean ≤ 0, or on any of 2,000 bootstrap means ≤ 0. This matches gate.py `_point`/`_bootstrap`. There, the denominator is mean(oracle) − mean(A2) = mean(d), with shared indices, so every resampled denominator is mean(d[idx]).
   - **Scenario formula.** P(read) = ∏(1 − e_j s_j) − ∏(1 − e_j) is exact for independent nodes, and eligibility and test STOP are independent within a node because the instances are disjoint. Recombining from the per-node JSON values gives a maximum difference of 0.
   - **P(T1 kept)** = 1 − ∏_{T1}(1 − e_j), which is correct as defined.
   - **Independent check of the per-node test STOP.** I enumerated the multinomial resample compositions exactly (462 for n = 6), took 1 − (1 − p)^2000, and integrated over 200k normal samples. The results agree with the script's table to within 0.01–0.013, which is MC error:
     - n = 6: 0.849 / 0.546 / 0.231 / 0.063 at μ = 0.5 / 1 / 1.5 / 2;
     - n = 4: 0.772 / 0.498 / 0.242 / 0.088;
     - n = 2: 0.522 / 0.291 / 0.129 / 0.044.

     The point-only parts equal Φ(−μ√n).

     The mechanism the report gives also holds. For n = 6, P(STOP | some test d < 0) is 0.95 / 0.85 / 0.68 / 0.49. For n ≤ 4 it is 1.00.
2. **Gate code.** `git diff e3c0921e e1469124 --stat` touches only the four new files. The gate.py blob is the same in both commits (232a2835) and was last changed in da264a40.
3. **Numbers in the report.** All §2 table cells match `sim_output.md`. The T1 × 6 / P2 statements match the output. The §2 per-node table matches the JSON: 0.851, 0.548, 0.233, 0.0555, 0.759, 0.5055, 0.2855 and so on, rounded. Q3b and ROW are recorded as the author answered: uv.lock with NumPy 2.4.4 and Python 3.13, `.python-version` not a constraint, and ROW (a).

## Findings

**B1 (BLOCKING): §3.4 "Under every rule, P(STOP) stays high. The cause is the test-side STOP, not eligibility" is false as stated for the stricter rules at low and middle μ.**

P(STOP) is the sum of P(no node eligible) and P(some eligible node STOPs). `p_no_eligible` is already in the JSON. For normal d, T1 × 12, P1, the two parts are:

| rule | μ | P(STOP) | from no node eligible | from test STOP |
|---|---|---|---|---|
| R0 | 0.25 | 0.98 | 0.86 | 0.12 |
| R0 | 0.5 | 0.95 | 0.76 | — |
| R1 z ≥ 6 | 0.5 | 0.98 | 0.91 | — |
| R2-trdev r = 2 | 1 | 0.98 | 0.95 | — |
| R0 | 1 | 0.76 | 0.31 | 0.45 |

So for strict rules below μ ≈ 1, the high P(STOP) comes from eligibility. That outcome is arguably intended.

The claim does hold in the region the recommendation relies on:
- R1 z ≥ 3 from μ = 0.5 (no-eligible part 0.07 at μ = 0.5, 0.00 from μ = 1);
- every rule from μ ≈ 1.5.

There, the test-side STOP sets a floor that no eligibility rule removes. My independent computation confirms this.

**Fix:** add the decomposition, either as a column or a short table from `p_no_eligible`. Then restate §3.4: "Where nodes are eligible (μ ≳ 1, or from μ = 0.5 under R1 z ≥ 3), P(STOP) is driven by the per-node bootstrap test STOP. Below that, strict rules STOP mainly because no node is eligible." Make the same change to the commit-message phrase "dominant cause" if it is reused.

**B2 (BLOCKING): §3.3 "if r = 0.5, it lets in most nodes at μ = 0.25 (T0 excluded share 0.74)" misreads the number.** An excluded share of 0.74 means about a quarter of T0 nodes get in, not most. The permissive direction still holds against R1 z ≥ 3 (0.96 excluded) and R2 r = 1 (0.98 excluded).

**Fix:** "if r = 0.5, it admits about a quarter of T0 nodes at μ = 0.25 (excluded share 0.74) and more than half at μ = 0.5 (0.41)."

**N1 (NON-BLOCKING): §3.5 "P(STOP) stays 0.84–0.99" is true only for R1 z ≥ 3.** It covers both T1 layouts and both splits. Across all rules the left-skewed P(STOP) ranges from 0.49 to 1.00.

**Fix:** "For R1 z ≥ 3, P(STOP) stays 0.84–0.99."

**N2 (NON-BLOCKING): §2 says R1 and R2-trdev under P2 "are identical to P1".** They are identical in the model. The tables differ by Monte Carlo error, because the cache key includes (n_tr, n_dev), so each split gets fresh draws. The largest difference is 0.03, in R2-trdev r = 1, μ = 0.5, P(T1 kept): 0.46 vs 0.43.

**Fix:** "identical in the model; the printed values differ only by MC error (≤ 0.03)."

**N3 (NON-BLOCKING): the "point" figures in the per-node test-STOP table are not in the committed output.** They are the analytic Φ(−μ√n). I checked them all.

**Fix:** state that in the table caption.

**N4 (NON-BLOCKING): "R1 … keeps T1 in every layout" (§3.2 and §4) needs a μ qualifier.**
- R1 z ≥ 6 keeps T1 with probability 0.01–0.11 at μ = 0.25.
- R1 z ≥ 3 keeps it with probability 0.35–0.49 at μ = 0.25.
- At μ ≤ 0.5 under T1 × 12 / P2, R0 keeps T1 more often (0.55 / 0.70).

**Fix:** "R1 can include T1 nodes in every layout. With z ≥ 3 it keeps T1 with probability ≥ 0.98 from μ = 1."

**N5 (NON-BLOCKING): the R2 parametrisation, and another reading of (ii).**

*Parametrisation.* In the model only the product c·r matters. R2 is a known-variance z test at critical value c·r, which is why the rows "c = 3, r = 2" and "c = 6, r = 1" agree. Modelling σ_node as known, with r as a sensitivity, is a fair reading. But "cannot be calibrated" is more precisely: "c can only be set once r, which is σ_node on the utility scale relative to sd(d), is known."

*Another reading.* "用 D21 噪声底 σ_node 定门槛" can also be read as an absolute floor on the train+dev denominator, d̄ ≥ k·σ_node, with no √n. That has the same form as D18's δ_n = max(0.002, 0.25 × median paired sd(Δ̂)), which the model assumes non-binding.

Under that reading, P(eligible) = Φ((μ − k·r)√n). It still needs r and a choice of k, and it leaves the test-side STOP unchanged. So it does not change the conclusion that R2 cannot be adopted until σ_node is on the utility scale, nor the D8-TEST conclusion.

**Fix:** add two sentences:
- one on the c·r equivalence;
- one on the absolute-floor reading and its overlap with δ_n. Possibly also say that alternative (ii) under that reading amounts to "δ_n alone, with a σ_node-based value".

**N6 (NON-BLOCKING): the per-node test STOP is non-monotone in n_test.** This affects the D8-TEST option "more test instances" and the Q4 floor remark. I reran the script's `test_stop_prob` at 1,000 reps. For normal d at μ = 0.5 / 1 / 1.5 / 2:

| n_test | μ = 0.5 | μ = 1 | μ = 1.5 | μ = 2 |
|---|---|---|---|---|
| 2 | 0.54 | 0.28 | 0.12 | 0.05 |
| 4 | 0.77 | 0.52 | 0.25 | 0.09 |
| 6 | 0.85 | 0.55 | 0.24 | 0.06 |
| 9 | 0.86 | 0.50 | 0.13 | 0.02 |
| 12 | 0.87 | 0.38 | 0.05 | 0.00 |
| 18 | 0.79 | 0.17 | 0.00 | 0.00 |

Three consequences:
- At plan sizes, more test instances raise the per-node STOP probability. It only falls from about 9–12 test instances per node.
- Under the current rule, a T1 test floor of 4 STOPs more often than a floor of 2 (0.51 vs 0.29 at μ = 1). §4 suggests the author "may prefer a T1 test floor of 4" on informativeness grounds. That is legitimate, but this cost is not stated.
- A larger test share (for example 1/2, so T0 9) would barely change P(STOP).

**Fix:** add this n_test dependence to the D8-TEST paragraph and the Q4 bullets, and qualify "more test instances" as helping only from about 12 per node.

**N7 (NON-BLOCKING): the z ≥ 3 threshold is coupled to D8-TEST.** Under the current test rule, R1 z ≥ 3 has the highest P(STOP) at μ = 1 / 1.5 / 2: 1.00 / 0.99 / 0.73, against 0.77 / 0.69 / 0.53 for z ≥ 6. Under left skew it also admits 28% of T0 nodes at μ = 0.25. The report does make D8-TEST a precondition, and it states the P(STOP) cost, so this is not an overclaim.

**Fix:** say explicitly that the threshold value (3 vs 6) is provisional and should be revisited once the test-side rule is decided. For example, if the test STOP becomes point-only, eligibility is the main guard against unstable ratios, and a stricter z may be preferred.

**N8 (NON-BLOCKING): the `split_sizes` docstring says "largest-remainder".** The code rounds test and dev and gives the remainder to train. This is exact at all sizes used.

**Fix:** correct the docstring wording.

**N9 (NON-BLOCKING): P(T1 kept) is unconditional.** It is the probability that at least one T1 node is eligible, not that T1 is in the IQM of a read gate.

**Fix:** say so in §1 "Outputs". Optionally, also report P(T1 in IQM and gate read).

## Assessment of the recommendation and readings

- **Reading (i)**, the same paired z on train + dev without test, is a faithful reading. It introduces no test leakage, since eligibility uses only oracle − A2 on non-test instances.
- **Reading (ii)**, a known σ_node scale with ratio r as a sensitivity, is a reasonable reading. The absolute-floor alternative (N5) does not change the conclusion.
- **Recommendation.** R1, P2, the floors T0 ≥ 6 and T1 ≥ 4 or 2, and the new question D8-TEST follow from the evidence. The report avoids changing gate.py and defers both decisions to the author. The two blocking items are text errors in the reading section and do not change the recommendation. The script and outputs need no change.

Verdict: changes requested


---

# Review: D8 eligibility alternatives, round 2

Reviewed commit: 82923797c12f8b55f27f4336c51719e2f3bd5fca

- Branch: `mac-m11-d8-alt-20261114` (worktree /tmp/pb/wt/d8alt), on top of e1469124. Round 1: REVIEW_D8ALT_round1.md.
- Independent reviewer (AI-assisted, Claude); read-only. Scratch was under /tmp/rev_d8alt and has been removed.

## What was checked

- **Diff since e1469124.** The report changed, and one docstring line in the script changed (N8). Nothing under `r1/c3` changed, so gate.py is still blob 232a2835.
- **Reproduction at 82923797.** I reran the committed script with `/tmp/np244/bin/python -I` (NumPy 2.4.4, Python 3.13.18). `sim_output.md` and `sim_output.json` are byte-identical to the committed files (`cmp`).
- **B1.** The new split table in §2 (P1, normal, T1 × 12) matches `p_no_eligible` and `p_stop` in the JSON in all 25 cells. I checked each row:
  - R0 0.86/0.98 … 0.00/0.34;
  - R1 z ≥ 6 0.98/1.00 … 0.00/0.53;
  - R1 z ≥ 3 0.47/0.96, 0.07/0.95, 0.00 thereafter;
  - R2-trdev r = 1 0.77/0.98, 0.24/0.92, 0.00 thereafter;
  - R2-trdev r = 2 1.00, 1.00, 0.95/0.98, 0.10/0.49, 0.00/0.50.

  The rewritten §3.4 names both causes and the regimes where each dominates, and its examples are correct. Resolved.
- **B2.** The text now reads "about a quarter of T0 nodes at μ = 0.25 (0.74) and most of them at μ = 0.5 (0.41)", which is correct. Resolved.
- **N1–N9.** All addressed:
  - N1: the left-skew range is now "0.84–0.99 for R1 z ≥ 3; across all rules 0.49–1.00", which checks out.
  - N2: the text now says "MC error, up to 0.03".
  - N3: the point column is labelled as the formula Φ(−μ√n_test).
  - N4: the μ qualifiers in §2 and §3.2 are correct. z ≥ 3 at μ = 1 keeps T1 with probability 1.00 / 0.98 / 0.98, and z ≥ 6 at μ = 2 with 1.00 / 0.97 / 0.97, across the layouts.
  - N5: the c·r equivalence is now stated, along with the absolute-floor / δ_n reading.
  - N6: the side calculation is consistent with my independent runs:
    - μ = 1: n_test = 18 gives 0.20 at 4,000 reps (report 0.21), and n_test = 12 gives 0.38 (report 0.40);
    - μ = 1.5: n_test = 18 gives 0.006 (report 0.01).

    The rise-then-fall shape and the "from about 12" statement hold. The Q4 cost of 0.51 vs 0.29 matches the committed table.
  - N7: the threshold is now marked provisional until D8-TEST.
  - N8: the docstring is corrected.
  - N9: "unconditional" is now stated.

## Findings

**N10 (NON-BLOCKING): "the highest of the rules" overstates.**
- **Where:** §3.4 says "R1 z ≥ 3 is 0.95–1.00 up to μ = 1.5, the highest of the rules", and §4 says "z ≥ 3 has the highest P(STOP)".
- **What the table shows:**
  - At μ = 0.25 and 0.5, R1 z ≥ 3 is not the highest. It has 0.96 and 0.95, against 1.00 for R2-trdev r = 2, c = 6 and r = 0.5.
  - From μ = 1 it is tied for highest with R2-trdev r ≤ 1, within MC error: at μ = 2 it is 0.73 vs 0.74.
- **Part of the cause:** round-1 N7 compared z ≥ 3 only with z ≥ 6, and its wording was loose.
- **Fix:** "from μ = 1 it is among the highest (with R2-trdev r ≤ 1), and above R1 z ≥ 6 and R0."

**N11 (NON-BLOCKING): §4 still lists "keeps T1" for R1 without the μ qualifier added in §3.2.**
- **Fix:** add "(from about μ = 1 with z ≥ 3)".

Neither finding changes a number, the recommendation or the D8-TEST question. Both can be fixed in the next touch of the report.

## Assessment

Both blocking items are resolved, and all round-1 non-blocking items are addressed. The script and outputs reproduce exactly, and gate.py is unchanged.

The recommendation does not overclaim:
- R1, train + dev, z ≥ 3, provisional;
- P2 split;
- tier test floors T0 ≥ 6, T1 ≥ 4 or 2, with the stated cost;
- new question D8-TEST.

Q3b and ROW (a) are recorded as answered.

Verdict: accepted
Accepted commit: 82923797c12f8b55f27f4336c51719e2f3bd5fca
