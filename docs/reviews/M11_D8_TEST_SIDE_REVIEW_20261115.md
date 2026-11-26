Reviewed base: 1d34de18e427f479314d38ffe8efab865eaadaf5

# M11 D8-TEST: test-side STOP variants — independent review record (15 November 2026)

Branch `mac-m11-d8-test-20261115`, from `mac-m11-d8-alt-20261114` @ `6cbb6ef5`. Unit: `r1/scripts/d8_test_side_sim.py` (sha256 `b3ba8152…`), `reports/M11_D8_TEST_SIDE_20261115.md`, `reports/m11_d8_test_side_20261115/sim_output.{md,json}`. Author queue item 3 of 15 Nov, extended to D8-TEST by the author's choice. Synthetic only; `gate.py` unchanged. Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`66188e6d`): changes requested (2 MAJOR: the left-skew false passes were misread as a non-null — they are IQM false passes, a gate calibration risk, now open question D8-SKEW; overstated false-pass claims — per-arm, within MC error, family-wise higher; 5 MINOR, 1 nit).
- Round 2 (`0e5f76cf`): accepted, with 5 non-blocking MINORs and nits. (The round-2 request first named a wrong hash, `92b6a8c5`, then corrected it to `0e5f76cf`.)
- Round 3 (`1d34de18`, MINORs and nits fixed): **accepted**, no findings; two optional nits (across-node pooled ratio wording; the 0.35–0.38 range is for T1 × 12) left as is.

Accepted commit (round 3, last): 1d34de18e427f479314d38ffe8efab865eaadaf5

The round texts are reproduced unchanged below.

---

# Independent review R1: M11 D8-TEST test-side simulation (15 Nov 2026)

Reviewed base: `66188e6d` on `mac-m11-d8-test-20261115` (one commit on `6cbb6ef5`). Files: `r1/scripts/d8_test_side_sim.py`,
`docs/r1/reports/M11_D8_TEST_SIDE_20261115.md`, `docs/r1/reports/m11_d8_test_side_20261115/sim_output.{md,json}`.
Reviewer: a freshly spawned independent reviewer agent (AI-assisted, Claude). Read-only; scratch work is in `/tmp/pb/rev_d8test/`
(`repro.py`, `repro2.py`, `iqmcheck.py`, `indep.py`, `target.py`, `c1_*.txt`, `c2_*.txt`).

**VERDICT: REVISE**

The script is a faithful, correct implementation of the declared model and variants. The committed outputs reproduce exactly,
and the report's tables match them. Two interpretive problems are MAJOR. They concern the gate's false-pass behaviour, which is
what the author needs in order to choose a D8-TEST option and write the confirmation draft:
- the left-skew explanation is wrong for the IQM half (F1);
- the "false-pass below nominal" claim does not hold up once you look at MC error, the individual components and the two-arm
  Holm verdict (F2).

Neither finding overturns the ordering V1n ≤ V2 on false passes, or V1n's advantage over V0 and V1 in STOPs and power. Both
change what the report tells the author about the gate.

## Findings

### F1 (MAJOR): §3.4 and §4's last bullet. "g = 0 is not a null… a property of the gate's estimand" is wrong for the IQM component

**Location.** Report §3.4, bullets 2–4, and §4 "For the confirmation draft".

**Claim.** With left-skewed noise, a pass at g = 0 is "not a false pass", because "both IQM and PoI respond to the centre of the
distribution". On this reading the gate "tests a central (median-like) gain, not a mean gain".

**Evidence.**
- **PoI: correct.** Its estimand is instance-level: P(a > 0) = P(h > 0) = Φ(0.5) = **0.692** at g = 0. The instance median of h
  is **+0.300**, by my calculation over 2·10⁶ draws. So the PoI null (0.5) really is false under skew, and the PoI component
  rightly rejects: PoI-only rejection is 0.80 (V1n) and 0.94 (V2) in my independent run (P2, T1 × 12, z ≥ 3, μ = 1.5).
- **IQM: not correct.** R1-BX-D8 and `gate.py` define per-node gap closed as a ratio of **means**. In this model every node's
  true gap closed is g = 0. The IQM across nodes of the true node gaps is therefore exactly 0, so **the IQM null is true**.
- Because the pass rule is an intersection (IQM lb > 0 **and** PoI lb > 0.5), a pass when one component's null is true is a
  false pass. Under skew the PoI side is passed anyway, so the gate's verdict equals the IQM component's rejection. In my run:
  - IQM-only rejection is **0.29 (V1n) and 0.41 (V2)**, identical to P(pass) in those cells;
  - committed P(pass) at g = 0 is 0.25 and 0.415.
- **The IQM's positive drift comes from small samples, not from the estimand.** Mean(a) has expectation 0 at every n_test. But
  the distribution of node-level estimates G = mean(a)/mean(d) is left-skewed when n_test is small, and trimming its tails
  moves the IQM's target upward:

  | n_test | interquartile mean of G at g = 0 (μ = 1.5) |
  |---|---|
  | 4 | 0.069 |
  | 6 | 0.053 |
  | 40 | 0.011 |
  | 60 | 0.008 |

  (`target.py`, 4·10⁵ draws.) The percentile bootstrap adds undercoverage. With 60/40 test instances per T0/T1 node, IQM-only
  rejection at g = 0 is still **0.12** (V0, V1, V1n and V2 range 0.09–0.13; 400 reps).
- **V0 has the same problem.** When V0 reads under skew it passes at g = 0 with P(pass | read) = 0.42 (z ≥ 3, μ = 2) and
  0.46–0.50 (z ≥ 6, μ ≥ 1.5), from the committed JSON. The report is therefore right that the problem is not specific to the
  test-side variants. It is wrong about the cause.
- **Why this matters.** Left-skewed U_arm − U_A2 is a realistic case here: REVISIONS (c) sets the action target of divergent
  proposals to u = −g, which gives a heavy left tail. A false-pass rate of 0.16–0.42 per arm (V1n and V2, all reps, μ ≥ 1) is a
  calibration risk for D8 itself. Framing it as a choice of wording ("say which gain is meant") hides that risk from the author.

**Fix.**
1. Rewrite §3.4 along these lines. Under skew the PoI's null is false: its estimand is instance-majority, about 0.69 here. The
   IQM component, however, rejects at a true per-node gap closed of 0, in 0.16–0.27 (V1n) and 0.31–0.42 (V2) of reps for
   μ ≥ 1. The causes are the upward small-n bias of the IQM of skewed node-level ratio estimates and bootstrap undercoverage.
   So these are false passes of the gate as R1-BX-D8 defines it, and they occur under every test-side variant whenever the gate
   reads.
2. Replace the §4 "confirmation draft" bullet with an open item for the author: the gate's type-I behaviour under skewed
   utility differences at 2–6 test instances. The options can be listed without being decided, for example:
   - a skew sensitivity in the confirmation check;
   - a different interval method;
   - restating the intended estimand.

### F2 (MAJOR): §3.2 and §4 false-pass claims. "≤ 0.01 … below the nominal 0.025" is partly false, beyond MC resolution, and not the gate-level comparison

**Location.** §3.2, bullet "The false-pass rate". §4, "its false-pass rate stays below nominal on normal data". §1, "One arm
at 97.5 % is its first step."

**Evidence.**
- **(a) "≤ 0.01 under V1n on normal data" is false.** V1n at g = 0 is 0.013 and 0.018 for T1 × 12, P2, z ≥ 6, μ = 1.5 and 2
  (`sim_output.md`, lines 17 and 26). The maximum over all normal cells is 0.0225 (T1 × 6, P2, z ≥ 3, μ = 1.5).
- **(b) "Below the nominal 0.025" cannot be resolved for 0.022 at 400 reps** (SE ≈ 0.0074). My independent run of 1,600 reps
  (four seeds; T1 × 6, P2, z ≥ 3, μ = 2, g = 0) gives:

  | Variant | P(pass) at g = 0 |
  |---|---|
  | V1n | **0.030 ± 0.004** |
  | V2 | **0.036 ± 0.005** |
  | V1 | 0.023 |

  The committed V2 value of **0.0325** (T1 × 6, P2, z ≥ 3, μ = 1.5) is above 0.025 and is not mentioned. The report
  contrasts V1n with V2 on power but not on false passes.
- **(c) The low false-pass rate on normal data comes from the intersection, not from calibrated bounds.** In the same 1,600 reps
  each component is anti-conservative per arm:
  - **IQM-only 0.048** (V1n);
  - **PoI-only 0.080**, about 3× the nominal 0.025.

  This is expected for percentile bounds with 2–6 instances per node: with n = 2, a node's bootstrap variance is half the
  plug-in variance. With 60/40 test instances both components are at or below nominal (0.013 and 0.020). The joint rule hides
  this only while both nulls hold. Once one null is false (skew: F1; or an arm that wins most instances but loses on the mean),
  the other component's excess passes straight through.
- **(d) The Holm stand-in.** In `gate._holm_decision` the first ranking key is "passes at 97.5 %". So the gate's verdict is
  "**some** arm passes at 97.5 %", the union over A3 and A5, not one arm's test.
  - P(STOP) is exactly the gate's, because every STOP rule depends only on d. The single-arm read is also a fair basis for
    comparing the variants.
  - The single-arm P(pass) is, however, a **per-arm** rate: a lower bound on the gate's false-pass rate and on its power.
  - With two null arms correlated 0.5 through the shared A2, my 1,600 reps (same cell) give these gate verdicts, against the
    family-wise nominal 0.05:

    | Variant | Gate false pass (two arms) |
    |---|---|
    | V1n | **0.054 ± 0.006** |
    | V2 | 0.063 |
    | V1 | 0.042 |
    | V0 | 0.031, but it reads in only about 40 % of reps |

**Fix.**
- Correct the range: "≤ 0.023 per arm on normal data, at about nominal within MC error; V2 reaches 0.033".
- Say that the simulated rate is per arm, and that the gate's verdict over two arms can be up to about twice as high. The
  family-wise nominal is 0.05.
- Add one sentence noting that each bound is individually anti-conservative at 2–6 test instances, which links to F1.
- Reword §1: "the gate passes if either arm passes at 97.5 %; one arm is simulated".
- In §4, replace "below nominal" with "at about nominal per arm, and no higher than V2".

### F3 (MINOR): §3.6. "lowers power under every variant" is false

Under z ≥ 6, V0's power is **higher** at μ ≥ 1.5 in all four layout/split blocks:
- T1 × 12, P2, μ = 2: 0.42 vs 0.26;
- T1 × 12, P3, μ = 2: 0.75 vs 0.49.

V1's power is also higher under P2: 0.33 vs 0.15 at μ = 1.5, and 0.86 vs 0.73 at μ = 2. The conclusion still holds for the
recommended variants. **Fix:** "lowers power under V1n and V2 (and adds no-eligible STOPs under all variants)".

### F4 (MINOR): §3.4 ranges and MC error for the skewed run

- "V0 STOPs in 0.94–0.99 at every μ" and "up to 0.27 and 0.42" hold for z ≥ 3 only.
  - Under z ≥ 6, V0's P(STOP) is 0.85–0.94 and V1n passes at g = 0 in up to **0.36**.
  - V1 also passes at g = 0 under skew: 0.06 (z ≥ 3) and 0.15 (z ≥ 6). This supports the report's "not specific to the
    variant" point.
- No SE is given for the 200-rep skewed run: about 0.031 at 0.3 and 0.035 at 0.5.

**Fix:** qualify the ranges as z ≥ 3, give the z ≥ 6 maxima, and state the 200-rep SE.

### F5 (MINOR): §3.2 and §4. The V1n disclosure should state its mechanics precisely

- **(a)** §4 says "No node or resample is removed from the computation". This is mechanically true, but a node whose G\* is −∞
  in the trimmed slots has weight 0 in that resample's IQM. §3.2 says so, and §4 should match ("kept, possibly with weight
  zero").
- **(b) V1n absorbs only a limited number of −∞ nodes.**
  - With k ≤ 3 eligible nodes every IQM weight is positive, so V1n is identical to V1.
  - With k eligible nodes, at most the zero-weight lower slots can absorb −∞ values. For k = 18 that is 4 nodes; a fifth gives
    IQM\* ≈ −5.6·10¹⁰ (`iqmcheck.py`).
- **(c) Worth stating as V1n's justification.** The IQM is an L-statistic with nonnegative weights, so it is nondecreasing in
  each argument. Setting a node's G\* to −∞ can therefore never raise IQM\* above its value for any finite G\* of that node.
  V1n is conservative compared with dropping or imputing the node.

**Fix:** add (a)–(c) to the "disclose" text.

### F6 (MINOR): model-scope caveats are missing

- **All nodes share μ and g.** Under a common μ the tier-pooled ratio (V2) and the per-node ratio have the same target. So
  "V2's power is close to V1n's" is measured exactly where V2's estimand change costs nothing.
- **Heterogeneous μ is not simulated.** With heterogeneous μ, nonpositive resampled denominators concentrate on eligible nodes
  with small μ, which may change V1n's −∞ frequency and its trimming behaviour.
- **V2's high STOP rate at μ = 0.5 (0.91)** comes from giving V2 V0's "any resample ≤ 0" STOP. A V2 with V1n-style handling
  was not simulated.
- **δ_n is non-binding.** The report states this, but not its likely effect: if δ_n were binding, some STOPs would move into
  "no node eligible".

**Fix:** add a short limitations paragraph.

### F7 (MINOR): reproducibility record

- The report names only seed 20261115. The skewed run uses **20261116** (`SEED + 1`), which is recorded in the JSON.
- The exact command is not given. It should be
  `python r1/scripts/d8_test_side_sim.py --reps 400 --skewed-reps 200 --json …/sim_output.json`, with the markdown
  captured from stdout.
- The sha256 of `sim_output.md` is not given (`b7031cd2…`).

**Fix:** add all three.

### F8 (NIT)

- `NEG = -1e12` is described as "far below any real gap". A real G\* = a\*/d\* with 0 < d\* ≲ 10⁻¹² could exceed it in
  magnitude, but the probability is about 10⁻¹² per draw and has no effect.
- The comment at script line 125 ends with a stray `"`.

## What I verified

1. **Reproducibility.**
   - The sha256 of the script (`b3ba8152…`) and of `sim_output.json` (`86837b4a…`) match the report's prefixes.
   - Environment: `/tmp/np244`, Python 3.13.18, NumPy 2.4.4.
   - With the committed script and its seeds I reproduced, identical after the JSON round trip:
     - the first 32 normal scenario rows (T1 × 12, P2, z ≥ 3, all μ and g);
     - all 64 left-skewed rows.
   - `sim_output.md` regenerates exactly from the committed JSON.
   - `gate.py` is unchanged in the commit.
2. **Fidelity to `gate.py`.**
   - G = mean(a)/mean(d) per eligible node on test.
   - The IQM weights equal `gate._node_iqm` for k = 1–39 (max |diff| 2.8·10⁻¹⁴).
   - PoI is taken over all nodes, eligible or not. Ties have zero probability with continuous data and are not modelled, which
     is harmless.
   - One shared index draw per node is used for d, a and the wins, and is drawn for ineligible nodes too.
   - Lower bound: `np.quantile(·, 0.025, method="linear")`. The pass rule is strict on both bounds.
   - The single-arm stand-in is fair for P(STOP) and for comparing variants, but not as the gate's false-pass rate (F2d).
3. **Variants.**
   - V0 matches `gate._point` and `gate._bootstrap`.
   - A nonpositive point denominator STOPs V0, V1 and V1n together. V0 is read only when no resample is bad, so its read uses
     only real ratios.
   - V1 sets the whole resample to NEG; V1n sets only that node to NEG.
   - No nan: `np.where` replaces the value before the IQM, and the quantile runs over finite values. Interpolating at index
     49.975 gives the same verdict as −∞ semantics: 50 or more NEG resamples means a fail.
   - V2: the pooled denominator is the mean of node mean(d) over the tier's eligible nodes. Its resamples are built from the
     same per-node indices, and the numerator is per node.
   - The STOP split (no-eligible vs test-side) is correct.
   - Eligibility: z on train + dev, with the sd = 0 convention as in `gate._dev_z`. n ≥ 3, so `dev_n` never applies.
4. **Numbers.** The report's §2 tables match `sim_output.md` cell by cell. Every number in §3 matches, except the ranges in
   F2a, F3 and F4.
5. **Independent implementation** (`indep.py`: own code, different seeds), against the committed values.

   | Case | Committed | Independent |
   |---|---|---|
   | T1 × 12, P2, z ≥ 3, μ = 1, g = 0.3: P(STOP) V1 / V2 | 0.13 / 0.16 | 0.10 / 0.13 |
   | Same case: P(pass) V1n / V2 | 0.25 / 0.39 | 0.25 / 0.43 |
   | Same case: committed P(STOP) at g = 0 (STOP rules do not depend on a) | 0.105 / 0.148 | |
   | μ = 1.5, g = 0.3: P(pass) V1 / V1n / V2 | 0.15 / 0.91 / 0.93 | 0.18 / 0.90 / 0.92 |
   | μ = 2, g = 0: P(pass) V1n | 0.010 | 0.018 |
   | Skewed, μ = 1.5, g = 0: P(pass) V1 / V1n / V2 | 0.02 / 0.25 / 0.415 | 0.03 / 0.29 / 0.41 |

   All agree within MC error.
6. **Interpretation checks.**
   - The rest of §3.2 is supported: V1 collapses the bound, and V1n's trimming absorbs nonpositive resampled denominators.
   - §3.3 is supported: V2 is the estimand change that R1-BX-D8 would need amended.
   - §3.5 is supported: P3 trades about 3 T0 and 2 T1 train instances for power at μ ≈ 1, and the no-eligible STOP is 0.09 vs
     0.07.
   - The recommendation is clearly left to the author, and §5 is marked "not done".

---

# Independent review R2: M11 D8-TEST test-side simulation (15 Nov 2026)

Reviewed base: `0e5f76cf` on `mac-m11-d8-test-20261115`, one commit on `66188e6d` (the R1 base). `git diff --stat
66188e6d 0e5f76cf` touches only `docs/r1/reports/M11_D8_TEST_SIDE_20261115.md`. The sha256 values are unchanged:
- script: `b3ba8152…`;
- `sim_output.json`: `86837b4a…`;
- `sim_output.md`: `b7031cd2…`.

Reviewer: the same independent reviewer agent as in R1 (AI-assisted, Claude). Read-only. Scratch: `/tmp/pb/rev_d8test/r2check.py`.

**VERDICT: ACCEPT**

Both MAJOR findings are resolved. No BLOCKING or MAJOR finding remains. The MINOR items below are worth fixing in the same
pass, but none changes the recommendation or misstates the gate's behaviour.

## Status of the R1 findings

| R1 | Status | Check |
|---|---|---|
| F1 (MAJOR) skew explanation | **Resolved** | See below. |
| F2 (MAJOR) false-pass claims | **Resolved** | See below. |
| F3 (MINOR) z ≥ 6 power | **Partly resolved; new error** | See N1. |
| F4 (MINOR) skew ranges and MC error | **Resolved** | See below. |
| F5 (MINOR) V1n disclosure | **Resolved** | See below. |
| F6 (MINOR) model limits | **Resolved** | Shared μ/g, V2 estimand, V2's inherited STOP and δ_n are added. The heterogeneous-μ effect on V1n's −∞ frequency is not mentioned (nit). |
| F7 (MINOR) reproducibility | **Resolved** | See below. |
| F8 (NIT) | Accepted as left | Leaving the stray quote keeps the sha binding; the note at the end of the report is fine. |

**F1.** §3.4 now says that:
- the PoI null is false under skew (Φ(0.5) ≈ 0.69);
- the IQM null is true, so these passes are false passes;
- the causes are small-n bias and undercoverage;
- V0 shows the same problem when it reads.

D8-SKEW is raised as an open question, and §4 and §5 require it to be decided before confirmation.

**F2.** The maxima are correct against the JSON: V1n 0.0225, V2 0.0325, V1 0.015, V0 0.010. They are described as per-arm
rates, with "below nominal not shown". The reviewer's 1,600-rep, single-bound and two-arm figures are quoted correctly and
attributed. §4 now reads "close to nominal, no worse than V2". The §1 sentence remains (see N4).

**F4.** "0.85–0.99" covers z ≥ 3 and z ≥ 6. The z ≥ 6 maxima (V1n 0.36, V2 0.42, i.e. 0.415) are correct. The 200-rep SE of
0.035 is correct.

**F5.** The added text covers:
- zero weight within a resample;
- the zero-weight slots only (4 of 18);
- V1n equal to V1 with 3 or fewer eligible nodes;
- conservative relative to dropping the node.

I checked the last claim directly. Over k = 2–39 and 76,000 random cases, the IQM with one node set to NEG never exceeds the
IQM with that node dropped (max difference −0.0012).

**F7.**
- Both seeds are recorded.
- The command is given.
- The `sim_output.md` sha is given.
- The two stdout blocks of `main()` are byte-identical to the committed `sim_output.md`.

## New or remaining findings (all MINOR or NIT)

### N1 (MINOR): §3.6. "lowers power under … V1 for split P3" is false

From `sim_output.json`, P(pass) at g = 0.3 under V1, z ≥ 3 → z ≥ 6, at μ = 0.5 / 1 / 1.5 / 2:

| Layout and split | z ≥ 3 | z ≥ 6 | Reading |
|---|---|---|---|
| T1 × 6, P3 | 0.005 / 0.05 / 0.31 / 0.62 | 0.005 / 0.06 / 0.33 / 0.77 | **higher** at every μ ≥ 1 |
| T1 × 12, P3 | 0.01 / 0.06 / 0.58 / 0.98 | 0.00 / 0.10 / 0.56 / 0.97 | mixed, within MC error |
| T1 × 6, P2 | 0.01 / 0.04 / 0.24 / 0.68 | 0.01 / 0.10 / 0.32 / 0.82 | higher at every μ ≥ 1 (as for T1 × 12, P2) |

**Fix:** "It lowers power under V1n and V2. Under V0 it raises power, and under V1 it is mixed or higher."

### N2 (MINOR): §4 D8-SKEW options

- **"The mean of per-instance ratios" is not a usable estimand here.** The per-instance denominator d_i = μ + e_i is ≤ 0 with
  substantial probability (0.16 at μ = 1 under normal noise). So a_i/d_i is undefined or has unbounded variance. Drop this
  example, or say that it would need a positive per-instance denominator.
- **"More test instances" should carry the evidence against it.** At 40–60 test instances per node the IQM still rejects about
  12 % of the time at g = 0 (§3.4). The plan's P3 (6–9 test instances) would barely help.

### N3 (MINOR): §3.4. The u = −g link is stated more strongly than the sources show

This goes back to my own R1 wording. REVISIONS (c) sets the label's **action target** to u = −g for a divergent proposal. Nothing
I read shows that the gate's one-step utility U inherits that value.

Better support is already in the same row: "a heavy-tailed node uses a Student-t, declared before labels are built". The PLAN
therefore anticipates heavy-tailed nodes. **Fix:** "Skewed or heavy-tailed utility differences are plausible here (REVISIONS (c)
anticipates heavy-tailed nodes, and divergent proposals may enter with u = −g)".

### N4 (MINOR): §1 still says "for the first-ranked arm … One arm at 97.5 % is its first step"

The rest of the report now says "per arm". In §1, however, the gate passes if **either** arm passes at 97.5 %. **Fix:** reword
to "one arm is simulated; the gate passes if either arm passes at 97.5 % (Holm), so pass rates here are per arm".

### N5 (MINOR): §4. "Its power is close to V2's" holds from μ = 1.5, not at μ = 1

At μ = 1, V2's power is clearly higher:

| Layout and split | V1n | V2 |
|---|---|---|
| T1 × 12, P2 | 0.25 | 0.39 |
| T1 × 12, P3 | 0.40 | 0.47 |
| T1 × 6, P2 | 0.16 | 0.29 |
| T1 × 6, P3 | 0.27 | 0.34 |

That gap is a real part of the V1n/V2 trade-off. Under common μ it comes at no estimand cost (§3.3). **Fix:** "close to V2's
from μ = 1.5; lower at μ = 1 (0.25 vs 0.39 for T1 × 12, P2)".

### N6 (NIT)

- **§3.4, "the gate's false-pass rate here equals the IQM's".** Strictly the gate's rate is ≤ the IQM's. They coincided in my
  run. "Is essentially" is more accurate.
- **The roughly 12 % at 40–60 instances** reflects both the remaining bias (target about 0.01) and undercoverage, not
  undercoverage alone. My R1 wording invited this reading.
- **The bias figures** are for μ = 1.5. Say so.
- **"Up to 0.50 of those reads"** rests on very few reads: V0 STOPs in 0.93 of 200 reps there. Say "of the few reads".
- **δ_n:** "does not change the skew issue" is an expectation, not a result. Use "is not expected to".
- **The review record** `M11_D8_TEST_SIDE_REVIEW_20261115.md` cited in §3.2 does not exist in the worktree yet. It must be
  committed under that name, as was done for the 14 Nov unit.

## What I verified in R2

- The scope of the diff is the report only. All three sha256 values are unchanged and match the report.
- Every new number in §3.2, §3.4, §3.6 and §4 was checked against `sim_output.json` or my R1 runs. The exceptions are N1 and
  N5.
- The F5 claim "conservative relative to dropping" was checked numerically, as above.
- `sim_output.md` equals the stdout of the stated command, byte for byte.
- The recommendation is still left to the author. D8-SKEW is presented as open, with options and no decision, and §5 makes it
  a precondition of confirmation.

---

# Independent review R3: M11 D8-TEST test-side simulation (15 Nov 2026)

Reviewed base: `1d34de18` on `mac-m11-d8-test-20261115`, one commit on `0e5f76cf` (the R2 base). `git diff --stat 0e5f76cf
1d34de18` touches only `docs/r1/reports/M11_D8_TEST_SIDE_20261115.md`. The sha256 values are unchanged and match the report:
- script: `b3ba8152…`;
- `sim_output.json`: `86837b4a…`;
- `sim_output.md`: `b7031cd2…`.

Reviewer: the same independent reviewer agent as in R1 and R2 (AI-assisted, Claude). Read-only.

**VERDICT: ACCEPT**

All R2 MINOR findings and nits are addressed. No BLOCKING, MAJOR or MINOR finding remains.

## Status of the R2 findings

| R2 | Status | Check |
|---|---|---|
| N1 §3.6 z ≥ 6 under V1 | **Resolved** | Now "lowers power under V1n and V2; raises under V0; mixed or higher under V1". The example (T1 × 6, P3, μ = 2: 0.77 vs 0.62) matches the JSON (0.7725 / 0.62). |
| N2 D8-SKEW options | **Resolved** | "More test instances" now carries the about 12 % at 40–60 and "P3's 6–9 would barely help". The mean of per-instance ratios is marked unusable, with P(d_i ≤ 0) = Φ(−1) ≈ 0.16 at μ = 1 (correct for normal noise). |
| N3 u = −g link | **Resolved** | Removed. "Plausible" now rests on the PLAN's Student-t for heavy-tailed nodes (REVISIONS (c)). |
| N4 §1 Holm sentence | **Resolved** | "One simulated arm; pass rates per arm; the gate passes if either arm passes at 97.5 %; family-wise rate higher (§3.2)". |
| N5 V1n vs V2 power | **Resolved** | "Close from μ = 1.5". The μ = 1 figures (0.39/0.25, 0.47/0.40, 0.29/0.16) match the JSON. |
| N6 nits | **Resolved** | "Essentially"; bias and undercoverage together; μ = 1.5 named for the bias figures; "very few reads" for V0; δ_n given as an expectation, not simulated. The review record is to be committed as `M11_D8_TEST_SIDE_REVIEW_20261115.md` after acceptance, which matches the §3.2 citation. |

## Optional nits (no change required)

- **§4 D8-SKEW, "a different per-node estimand, such as a pooled ratio".**
  - Per-node gap closed is already a ratio of means pooled over instances. The pooled ratio presumably means one pooled across
    nodes (Σ numerators / Σ denominators, overall or per tier as in V2), which is not a per-node estimand.
  - Suggested wording: "a different estimand, such as an across-node pooled ratio".
  - Its own behaviour under skew is untested.
- **§3.6, "0.35–0.38 at μ = 1".** This range is for T1 × 12. On T1 × 6 the no-eligible STOP is 0.21–0.28.

## What I verified in R3

- The scope of the diff is the report only, and the three sha256 values are unchanged.
- Each changed sentence was checked against `sim_output.json` or my R1 and R2 runs.
- The recommendation is still left to the author. D8-SKEW stays open, with options, and is a precondition of confirmation (§5).

---

