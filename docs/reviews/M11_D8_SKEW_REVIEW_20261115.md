Reviewed base: 4d87d9c829099ec88d646245df02f1a7c82d6a88

# M11 D8-SKEW: four pass rules under skewed and heavy-tailed data — independent review record (15 November 2026)

Branch `mac-m11-d8-skew-20261115`, from `mac-m11-d8-test-20261115` @ `0a6293d2`. Unit:
- declaration `proposals/M11_D8_SKEW_DECLARATION_20261115.md` (`8c84624b`, before any run);
- `r1/scripts/d8_skew_sim.py` (`dc899aad`, sha256 `8ea236d7…`);
- post hoc diagnostic `r1/scripts/d8_skew_b2_diag.py` (`52761c33`, sha256 `a6441c48…`);
- `reports/M11_D8_SKEW_20261115.md` and `reports/m11_d8_skew_20261115/{sim_output,b2_diag}.{md,json}`.

This unit answers the author's request of 15 Nov 21:37. It is synthetic only, and `gate.py` is unchanged. One freshly spawned independent reviewer agent (AI-assisted, Claude) did three rounds.

- **Round 1 (`c25f8025`): changes requested.** 2 MAJOR and 9 MINOR findings.
  - F1: (b2) is calibrated because of its declared +∞ convention, which acts as a denominator-positivity screen, not because of studentizing.
  - F2: under symmetric noise, the primary bounds of (b1), (d) and partly (a) exceed the thresholds, and only the PoI conjunct brings them under.
  - The round-1 request named a wrong hash, `5e0b1faf`, which does not exist. The reviewer reviewed the actual HEAD, `c25f8025`.
  - In response, the post hoc diagnostic script was committed (`52761c33`) before its own run.
- **Round 2 (`e155325e`): accepted.** 5 non-blocking MINORs. N1, a reversed screen wording in §4, was to be fixed before relay.
- **Round 3 (`4d87d9c8`, N1–N5 fixed): accepted.** No findings. One optional cosmetic nit (line wrap width) is left as is.

Accepted commit (round 3, last): 4d87d9c829099ec88d646245df02f1a7c82d6a88

The declared decision rule is unchanged: only (b2) is calibrated, so (b2) is recommended. The choice of rule is the author's.

The round texts are reproduced unchanged below.

---

# Independent review: M11 D8-SKEW (round 1)

Reviewer: independent agent (did not write the work). Read-only on the worktree. Scratch files are in `/tmp/pb/rev_d8skew/` (`check_json.py`, `repro_one.py`, `indep.py`, `runbatch.sh`, `repro_ci5.log`, `indep.log`).

**Reviewed commit.** The brief names `5e0b1faf` as the reviewed base. That object does not exist in the worktree. Branch `mac-m11-d8-skew-20261115` HEAD is **`c25f8025`** ("run output and report"). Its parents are `dc899aad` (script) and `8c84624b` (declaration), from `0a6293d2`. The file list matches the brief. I reviewed `c25f8025`.

## VERDICT: REVISE

There are no BLOCKING findings. Pre-registration order holds, the declared rule is applied exactly, and the numbers reproduce. Two MAJOR findings concern the reading that the author will use to decide. Both need text fixes, plus one post hoc diagnostic labelled as such. They do not change the declared rule's outcome.

---

## Findings

### F1 (MAJOR): (b2) is "calibrated" mainly because of the declared +∞ convention, not because studentizing fixes the skew

- **Location.** Report §3.3, third bullet ("The likely reasons: …"). Also §2 and §4, which present (b2) as the calibrated rule.
- **Evidence.** I wrote an independent re-implementation of the declared rules (`indep.py`, 400 reps per scenario, independent seeds). It matches the committed rates within MC error (see "What I verified"). It also records two diagnostics:
  - (i) The share of read reps in which more than 2.5 % of resamples contain a node with d̄\* ≤ 0. In those reps q_0.975(t\*) = 10¹², so the bound is −∞ and (b2) fails automatically, whatever the data say about the IQM.
  - (ii) A post hoc variant that drops those resamples instead of setting them to +∞. It is a diagnostic only, not a declared rule.

  | Scenario (T1 × 12, hom) | read reps with automatic fail | median share of bad resamples | (b2) declared, per arm / two-arm | variant (ii), per arm / two-arm |
  |---|---|---|---|---|
  | left-skewed P2 μ=1 g=0 | 0.93 | 0.35 | 0.000 / 0.003 | 0.063 / 0.108 |
  | left-skewed P2 μ=2 g=0 | 0.72 | 0.10 | 0.033 / 0.053 | 0.095 / 0.163 |
  | left-skewed P3 μ=1.5 g=0 | 0.75 | 0.11 | 0.010 / 0.028 | 0.065 / 0.133 |
  | left-skewed P3 μ=2 g=0 | 0.59 | 0.06 | 0.018 / 0.035 | 0.045 / 0.100 |
  | normal P2 μ=1 g=0.3 (power) | 0.97 | 0.33 | 0.010 / 0.010 | 0.34 / 0.46 |
  | normal P3 μ=1.5 g=0.3 (power) | 0.37 | 0.01 | 0.58 / 0.61 | 0.93 / 0.99 |

  - In most read reps, the convention alone decides (b2). (b2) as declared works as a screen: "pass only if fewer than 2.5 % of resamples have any nonpositive node denominator". That screen is close in spirit to `gate.py`'s current resample STOP.
  - Without the convention, the studentized interval is about as anti-conservative under left skew as (c) or (b1), at 0.045–0.095 per arm.
  - The screen is also what removes (b2)'s power at μ = 1 (0.01 against 0.34–0.46).
- **Why it matters.** The author may read "(b2) is calibrated" as "studentizing solves the skew problem", and adopt (b2) for that reason. The evidence says the calibration comes from the denominator screen, which costs power and does nothing about the IQM's upward bias. The report lists the convention as one of three equal "likely reasons", without checking.
- **Fix.**
  - State in §3.3, and in one line in §4, that the +∞ convention dominates: in a majority of read reps it forces the bound to −∞.
  - Either cite these reviewer numbers or add a post hoc diagnostic of your own, labelled as such (e.g. the share of reps with q = BIG). Do not change the declared verdict.
  - Reword "calibrated because it is very conservative" to "calibrated because its declared resample convention acts as a denominator-positivity screen; the studentized interval itself is not shown to be calibrated under left skew".
  - The §4 suggestion "(b2) without the +∞ convention" then becomes the obvious next unit.

### F2 (MAJOR): under symmetric noise, the primary bounds of (b1), (d) and partly (a) exceed the thresholds; the PoI conjunct rescues them; the report omits this

- **Location.**
  - §2, bullet 2 ("In the normal and t3 conditions … every rule stays within both thresholds").
  - §3.1 ("Under t3 heavy tails and under heterogeneous μ, every rule is calibrated").
  - §3.2.
  - §4, last bullet.
- **Evidence.** These are maxima of the primary-bound-only rates over the 8 T1 × 12 scenarios, from `sim_output.json`:

  | Rule | normal hom | normal het | t3 hom | t3 het |
  |---|---|---|---|---|
  | (a) per arm / two-arm | 0.030 / **0.0675** | 0.0325 / 0.050 | **0.0375** / 0.050 | 0.035 / 0.0525 |
  | (b1) | **0.0525 / 0.105** | **0.0525 / 0.085** | **0.070 / 0.135** | **0.075 / 0.120** |
  | (d) | **0.040 / 0.0725** | **0.0425 / 0.0675** | **0.0525 / 0.070** | **0.050 / 0.070** |
  | (c) | 0.030 / 0.055 | **0.040** / 0.050 | **0.0375** / 0.0525 | 0.030 / 0.0475 |
  | (b2) | 0.030 / 0.055 | 0.0225 / 0.0375 | 0.0225 / 0.045 | 0.0175 / 0.0275 |

  - Bold marks a value above 0.035 per arm or 0.065 two-arm.
  - With symmetric noise the true PoI at g = 0 is exactly 0.5. My runs confirm it: P(PoI bound passes) ≈ 0.025–0.05.
  - So the conjunct removes most primary false passes, and the full rule is calibrated only because the PoI sits exactly at its null.
  - As soon as the arm-noise median is above 0 (any skew), that protection is gone (§3.2). The rule is then only as good as its primary bound, and (b1)'s primary bound already exceeds under normal noise.
- **Why it matters.**
  - The declaration (§2) promised primary-only rates for exactly this reason. They sit in parentheses in `sim_output.md`, but the report's reading never draws on them.
  - The report argues against (b1) and (d) with weaker evidence: a T1 × 6 two-arm 0.0675, which is within MC error, and BCa's compute failures. Meanwhile it says (b1) "halves (a)'s excess", although under symmetric noise (b1)'s primary bound is worse than (a)'s.
  - For milder skew, which the report says was not simulated, the primary-only behaviour is the relevant guide.
- **Fix.**
  - Add the primary-only maxima for the normal and t3 conditions, as above or condensed, to §2 or §3.2.
  - State that calibration under symmetric noise relies on the PoI null being exactly true.
  - Use this, rather than the T1 × 6 (d) value, as the argument about (b1) and (d) in §4.
  - Label it descriptive: it is not part of the declared decision rule.

### F3 (MINOR): "6–9 test instances" is wrong

- **Location.** §3.1, first bullet.
- **Evidence.** From `split_sizes`: T0 has 6 (P2) or 9 (P3) test instances; T1 × 12 has **4** (P2) or 6 (P3); T1 × 6 has 2 or 3.
- **Fix.** Write "4–9 (T1 × 12 and T0)".

### F4 (MINOR): the stated skewness −6.2 is right for e, not for the arm noise

- **Location.** §1, and §3.4.
- **Evidence.**
  - The skewness of the standardised −lognormal(0, 1) is −(e+2)√(e−1) = −6.18. ✓
  - The arm noise is h = √0.5(c + f), so its skewness is −6.18/√2 = **−4.37** (empirical −4.39 over 4·10⁶ draws).
  - Its PoI at g = 0 is P(h > 0) ≈ **0.656**, not Φ(0.5) ≈ 0.69 as in D8-TEST.
  - The numerator test (c) and the PoI act on h.
- **Fix.** In §1 or §5, add that the arm differences have skewness ≈ −4.4 and a true PoI at g = 0 of ≈ 0.66.

### F5 (MINOR): "the primary bound alone gives the same rates" is nearly, not exactly, true

- **Location.** §2, the sentence above the left-skew table, and §3.2 ("equal").
- **Evidence.** For left-skewed hom, the per-arm rates of (a) at P2 μ=2 are 0.2375 (full) and 0.240 (primary). For (d) at P2 they are 0.110 and 0.1125, and 0.3025 and 0.3075. The largest difference is 0.005.
- **Fix.** Write "within 0.005".

### F6 (MINOR): the explanation of why the excess "grows with μ" is incomplete

- **Location.** §3.1.
- **Evidence.**
  - On T1 × 12, P(no eligible node) = 0 in every left-skew scenario.
  - Under V1n the test-side STOP rate falls with μ: from 0.62 to 0.08 at P2, and from 0.52 to 0.02 at P3. Every rate is unconditional, so fewer STOPs means more reps that can pass falsely.
  - (d) has almost no STOPs at μ ≥ 1, so its growth comes from k.
- **Fix.** Write "because fewer reps STOP on the test side and more nodes become eligible".

### F7 (MINOR): one BCa failure condition was not declared, and the failure count needs a gloss

- **Location.** Script lines 146–148; report §3.1.
- **Evidence.**
  - The script also fails the arm when 1 − a(z0 + z_α) ≤ 0. The declaration lists only a jackknife denominator ≤ 0, or a non-finite z0 or a. The extra condition is probably rare, but it is undisclosed.
  - `bca_fail` counts a rep if **either** arm fails.
  - The "up to 58 %" figure is the T1 × 6 secondary scenario (normal hom, P2, μ = 1: 0.578). The T1 × 12 maximum is 0.54.
  - My re-implementation agrees that jackknife denominators ≤ 0 are the dominant cause.
- **Fix.** Disclose the extra condition, and say "either arm" and which layout the 58 % comes from.

### F8 (MINOR): declared but not output, the (c) effect size; and the readings of the request's (c) are not restated in the report

- **Location.** Declaration §2 (c), last bullet ("computed and reported as an effect size only"); script; report §1.
- **Evidence.**
  - The script computes θ̂ but writes no effect-size statistic to the JSON or the markdown.
  - The declaration flags its reading of "the PLAN's Student-t for heavy tails" for the author. In the PLAN, R1-BX-REVISIONS (c) and E5 concern soft labels for heavy-tailed nodes. The report does not repeat the flag.
  - The request says "the mean of a over eligible nodes' test instances". That could mean an instance-pooled mean. The implementation uses a node-equal mean with a stratified variance, as declared. The instance-weighted alternative was not run.
- **Fix.**
  - In §1 or §5, restate both readings and say that they were declared choices.
  - Either note that the effect size was not output (a deviation), or add it post hoc. For reference, my runs give mean θ̂ at g = 0 under left skew, P2 μ = 1, of +0.06. That is a direct measure of the IQM's upward bias.

### F9 (MINOR): what (d) estimates under heterogeneous μ

- **Location.** Declaration §1 ("every per-node gap closed and every pooled ratio equals g").
- **Evidence.**
  - (d) is the IQM over nodes of mean(a_j)/D_T, and E[mean(a_j)]/D_T = g·μ_j/μ̄_T ≠ g.
  - Only the tier-pooled ratio Σ/Σ equals g.
  - At g = 0 the null still holds, so the false-pass results are unaffected. At g = 0.3 under het, (d)'s power refers to an estimand near g (by the symmetry of U(0.5, 1.5)), not exactly g.
- **Fix.** Add one clause to the report's §5.

### F10 (MINOR): wording on what the git history can show

- **Location.** Report header ("committed … **before** the script existed").
- **Evidence.** The commit order is declaration 21:38:54, script 21:40:52, outputs 21:59:59. That shows the declaration was committed before the script was committed and before the run, consistent with a run of about 12 minutes. It cannot show that the script did not exist yet.
- **Fix.** Write "committed before the script was committed and before any run". Also correct the reviewed-base hash in any record that cites `5e0b1faf`; HEAD is `c25f8025`.

### F11 (MINOR): the T1 × 6 (d) exceedance is within MC error

- **Location.** §4, last bullet.
- **Evidence.** 0.0675 against 0.065 is 0.2 SE. The declaration itself says chance exceedances are expected.
- **Fix.** Drop it as an argument, or mark it "within MC error". See F2 for the stronger argument.

---

## What I verified

1. **Pre-registration integrity.**
   - Commit order: `8c84624b` (declaration only), then `dc899aad` (script only), then `c25f8025` (outputs and report).
   - `git diff 8c84624b c25f8025` leaves the declaration unchanged.
   - Every declared element is applied exactly in `evaluate()` and in the report: thresholds 0.035 and 0.065 with strict ">" for exceedance; the T1 × 12 six-condition scope; 8 scenarios per condition; the power metric over T1 × 12, μ ≥ 1, g = 0.3, which gives equal weight to each condition (6 scenarios each); and the tie order (c), (a), (d), (b2), (b1) within 0.02.
   - Recommendation (b2): faithful, and clearly left to the author. The post hoc options are labelled as needing their own declaration.
   - The undeclared use of SciPy is disclosed. The extra BCa condition is not (F7).
2. **Implementation, checked line by line.**
   - Noise generators: the standardisation is correct; t3/√3 has sd 1 (checked empirically).
   - Heterogeneous μ: drawn per node and per rep.
   - Arms correlated 0.5 through a common factor; e independent of the arms.
   - Eligibility: z on train + dev ≥ 3.
   - V1n point STOP on any eligible node's d̄ ≤ 0. (d) uses only the tier point STOP, with resampled D_T\* ≤ 0 → −∞. A tier STOP implies a node STOP, so (d)'s reads include V1n's.
   - PoI: per arm, over all nodes, shared indices, bound > 0.5, which matches `gate.py`.
   - IQM weights: identical to `gate.py`'s `_node_iqm`.
   - (a): percentile bound with NEG for bad nodes.
   - (b1): z0 with ties counted one half; the paired leave-one-instance-out jackknife; the acceleration formula as declared; the quantile Φ(z0 + (z0+z_α)/(1−a(z0+z_α))); p ∈ {0, 1} → fail.
   - (b2): the delta-method se_j² = [var a + G² var d − 2G cov]/(n d̄²) with ddof 1; sorted-order weights for ŝe and se\*; t\* = (IQM\* − θ̂)/se\*; BIG for bad, zero-se or non-finite resamples; bound θ̂ − q_0.975 ŝe.
   - (c): node-equal Ā; se² = Σ s_j²/(k² n_j); the Welch–Satterthwaite df; the t_0.975 quantile.
   - Holm: `gate.py` ranks a 97.5 % pass first, so the gate passes iff some arm passes at 97.5 %; the two-arm rate is coded as "either arm".
   - I found no variable-shadowing bug, no filter error in `evaluate()` and no markdown error.
3. **Numbers.**
   - Every value in report §2's tables matches `sim_output.json`: maxima, mean powers 0.835 / 0.732 / 0.285 / 0.840 / 0.948, the per-condition powers, the left-skew false-pass table, the normal two-arm power table, and the T1 × 6 (d) exceedance.
   - The sha256 values of the script, JSON and markdown match the report's prefixes.
   - The MC error statements are correct: 0.0078, 0.0109, 0.025. The thresholds are 1.28 SE and 1.38 SE above nominal.
4. **Reproducibility.**
   - I re-ran condition 5 (t3, het) with the committed script, 400 reps and seed 20261117 + 5. All 80 rows are bit-identical to the JSON (0 diffs).
   - The independent re-implementation agrees with the committed rates within MC error on 10 scenarios. Examples:
     - left-skewed P2, μ = 1, g = 0, per arm: (a) 0.088 vs 0.095; (c) 0.040 vs 0.055; (d) 0.258 vs 0.253.
     - P3, μ = 2: (a) 0.175 vs 0.205; (b2) 0.018 vs 0.025.
     - normal P2, μ = 1, g = 0.3, two-arm: (c) 0.495 vs 0.513; (b2) 0.010 vs 0.008.
5. **Interpretation.**
   - (c)'s anti-conservatism under left skew: correct. For a left-skewed variable, the mean and the variance are negatively correlated, so the upper tail of t is heavy.
   - "PoI gives no protection under skew": correct (true PoI ≈ 0.66; the PoI bound passes in 88–96 % of reps). It needs the symmetric-noise counterpart (F2).
   - "(b2) calibrated because conservative": true as stated, but the mechanism is misattributed (F1).
   - The limits section is adequate apart from F4 and F9.
6. **Request (c) wording.** "Node-stratified test" is implemented as a stratified-variance, node-equal mean test with a Student-t (Welch–Satterthwaite) reference distribution. That is a reasonable, declared reading of "the PLAN's Student-t", which in the PLAN concerns soft labels. The flag should be carried into the report (F8).

No files were created in the worktree. `git status --ignored` is clean.

---

# Independent review: M11 D8-SKEW (round 2)

**Reviewed commit:** `e155325e`, on branch `mac-m11-d8-skew-20261115`. Round 1 reviewed `c25f8025`.

**Changes since round 1:**
- `52761c33`: a post hoc diagnostic script.
- `e155325e`: its output and the revised report.

I worked read-only. `git status --ignored` is clean. Scratch is `/tmp/pb/rev_d8skew/r2_check.py`.

## VERDICT: ACCEPT

All eleven round 1 findings are resolved, and none of the new findings is BLOCKING or MAJOR. One new MINOR (N1) inverts the meaning of the screen in §4, the section the author acts on. It should be fixed before the report is relayed.

## Round 1 findings: status

| ID | Status | Note |
|---|---|---|
| F1 (MAJOR) | **Resolved** | New §3.3 with a post hoc diagnostic. §2 and §4 say the calibration comes from the screen, not from studentizing. The declared verdict is kept. The code and the numbers are verified below. |
| F2 (MAJOR) | **Resolved** | New §3.2 table. Every cell matches `sim_output.json`'s primary-only maxima, including the new T1 × 6 column (e.g. (d) 0.075 / 0.135; (a) 0.050 / 0.080). Bolding is correct. "(b1) halves" is now limited to left skew. §4 uses the primary-bound evidence. |
| F3 | Resolved | Test-instance counts are now 4, 6 and 9. They match `split_sizes`. |
| F4 | Resolved | Skewness −6.2 for e and ≈ −4.4 for the arm noise; P(a > 0) ≈ 0.655. These agree with my round 1 values (−4.39 and 0.6555). The wording is slightly off; see N2. |
| F5 | Resolved | "within 0.005". |
| F6 | Resolved | The test-side STOP rate falls from 0.62 to 0.08 at P2, and no-eligible is 0. This matches the JSON. |
| F7 | Resolved | The extra BCa failure condition is disclosed as a deviation, along with the either-arm count and 54 % (T1 × 12) vs 58 % (T1 × 6). |
| F8 | Resolved | The node-equal reading is restated. The PLAN Student-t flag is carried over. The missing effect-size output is disclosed. |
| F9 | Resolved | Added to §5. |
| F10 | Resolved | "before the script was committed". `git diff 8c84624b e155325e -- docs/r1/proposals` is empty, so the claim "not changed since" holds. |
| F11 | Resolved | Marked as within MC error (SE ≈ 0.012, which is correct). |

## Diagnostic script `d8_skew_b2_diag.py` against the declared (b2)

- **Data generation.** The diagnostic copies `d8_skew_sim.one_rep`'s generation line by line, with the same draw order: optional U, train + dev, d, c, two arm noises, idx. It uses the module's `noise`, `iqm_weights`, `iqm_sorted`, `lower`, `NEG`, `BIG` and `LEVEL`.
- **Read reps.** A rep is read only when an eligible node exists and the V1n point STOP does not fire. That matches the declared run's read definition.
- **The (b2) computation matches the declared script.** Checked items:
  - `node_se` is identical to the declared script's.
  - ŝe uses the sorted-order weights.
  - se\* is ordered by `argsort(G_b)`.
  - The invalid set is `bad | ~(se* > 0) | ~isfinite(t*)`, and invalid resamples get BIG.
  - The bound is θ̂ − q_0.975 ŝe, with the same se_hat = 0 fallback.
  - PoI is computed per arm over all nodes.
  - The rates are unconditional: they are divided by reps.
- **Variant drop-bad.** It takes the quantile over the valid t\* only, and fails when none are left. That is as described.
- **Auto-fail definition.** It counts reps with bad share > 0.025. Two nits, both negligible:
  - Exactly 50 of 2000 bad resamples also forces a fail: linear interpolation gives about 0.025·10¹².
  - Resamples that are invalid only because se\* = 0 are not counted.
- **Commit order.** The script was committed at 22:11:52 and the output at 22:15:52. One scenario takes about 13 s on one core (my timing). So 32 scenarios on 2 processes take about 3.5 min, which is consistent with the two timestamps.
- **Exact reproduction.** I imported the committed diagnostic and re-ran scenarios 3, 10, 19 and 31, which cover left-skewed and normal noise at g = 0 and g = 0.3. Every field is identical to `b2_diag.json`.
- **sha256 values.** The script, JSON and markdown match the prefixes in the report (`a6441c48…`, `995e654a…`, `9a878984…`). The sim script and sim outputs are unchanged.

## Report numbers against `b2_diag.json` and `sim_output.json`

All §3.3 figures are correct:

| Claim | Value in the report | Checked |
|---|---|---|
| Auto-fail share of read reps, left-skewed, g = 0 | 0.59–0.95 | ✓ |
| Auto-fail share of read reps, normal, g = 0.3, μ ≤ 1 | 0.81–0.96 | ✓ |
| Auto-fail share of read reps, normal, g = 0.3, μ = 2 | 0.03–0.20 | ✓ |
| Drop-bad false pass, left-skewed: per arm / two-arm | 0.048–0.090 / 0.085–0.152 | ✓ |
| Drop-bad false pass, normal: per arm / two-arm | ≤ 0.020 / ≤ 0.033 | ✓ |
| Normal, μ = 1, two-arm power: drop-bad (P2, P3) | 0.44 and 0.61 | ✓ |
| Normal, μ = 1, two-arm power: declared (P2, P3) | 0.01 and 0.06 | ✓ |

The §2 tables did not change; they were checked in round 1. The §3.2 table matches, as noted under F2.

## Post hoc labelling

Adequate. The post hoc status is stated in:
- the report header block;
- the §3.3 heading paragraph ("a diagnostic, not a rule");
- the script docstring ("POST HOC … not part of the declared decision rule");
- §4, where every alternative route needs its own declaration;
- §5, which limits the diagnostic to homogeneous μ.

The declared verdict, (b2) recommended, is unchanged and is reported as the declared result.

## New findings

### N1 (MINOR, fix before relay): §4 states the screen backwards

- **Location:** §4, first bullet, third sub-bullet.
- **Evidence:** It reads "fail unless at most 2.5 % of resamples keep every eligible node denominator positive". The rule actually fails unless at least 97.5 % of resamples keep every denominator positive. Equivalently, it fails if more than 2.5 % of resamples have a nonpositive node denominator. §3.3 states this correctly.
- **Fix:** Write "fail if more than 2.5 % of resamples have an eligible node with mean(d\*) ≤ 0".

### N2 (MINOR): "the average of two such draws"

- **Location:** §1.
- **Evidence:** The arm noise is √0.5·(c + f), which is a scaled sum with sd 1. An average, (c + f)/2, would have sd 1/√2. The skewness and P(> 0) values are unaffected, because both are scale-free.
- **Fix:** Write "√0.5 times the sum of two such draws (sd 1)".

### N3 (MINOR): "within MC error" for the declared rows should be quantified

- **Location:** §3.3, "The declared (b2) rows of the diagnostic agree with `sim_output.json` within MC error."
- **Evidence:** Over 32 scenarios, the two-sample |z| reaches 3.0. The worst case is normal, g = 0.3, P3, μ = 1.5: 0.6425 vs 0.5375. A χ² test over 26 per-arm z values (scenarios with a nonzero pooled rate) gives χ² = 40.9 (p ≈ 0.03), with mean z +0.35 and mixed signs.
  - The code is identical and the two runs use different seeds, so this is most likely chance.
  - My independent implementation gives 0.58 for the worst-case scenario, between the two runs.
- **Fix:** Add "(largest difference 0.105, |z| ≈ 3.0, at normal g = 0.3 P3 μ = 1.5; signs mixed)".

### N4 (MINOR): "heterogeneous μ" is ambiguous in §4

- **Location:** §4, "adopt (c)": "Under normal, t3 and heterogeneous μ it is calibrated".
- **Evidence:** (c) fails under left-skewed heterogeneous μ (max 0.055 per arm, 0.11 two-arm).
- **Fix:** Write "under normal and t3 noise, with homogeneous or heterogeneous μ".

### N5 (nit): two attributions

- **§3.1, BCa failures.** "Mostly because a jackknife denominator is ≤ 0" is not recorded by the committed outputs. It comes from the reviewer's re-implementation (round 1). Say so, or drop "mostly".
- **§3.3, drop-bad power.** "Its power is close to that of (c)" overstates it slightly. At normal, μ = 1, drop-bad has 0.44 / 0.61 against (c)'s 0.51 / 0.72, from different seeds. "Somewhat below (c)" is more accurate.

## What I verified

1. **Unchanged files.** The declaration, `d8_skew_sim.py` and `sim_output.*` are unchanged since round 1. Their sha256 values are the same.
2. **Diagnostic code.** Checked line by line against the declared (b2) in `d8_skew_sim.py`; equivalent, except for the intended drop-bad variant and the auto-fail counter.
3. **Diagnostic reproduction.** Four scenarios reproduce bit-identically. The commit timing is consistent with committing before the run.
4. **Report numbers.** Every number that is new or changed in the revised report checks out against `b2_diag.json` and `sim_output.json`.
5. **Labelling and verdict.** The post hoc labelling is adequate, and the declared verdict is preserved.

---

# Independent review: M11 D8-SKEW (round 3)

**Reviewed commit:** `4d87d9c8`, on branch `mac-m11-d8-skew-20261115`. It is a single commit on top of `e155325e`.

I worked read-only; `git status --ignored` is clean.

## VERDICT: ACCEPT

`git diff --stat e155325e 4d87d9c8` lists one file: `docs/r1/reports/M11_D8_SKEW_20261115.md` (16 insertions, 9 deletions). The script, the declaration, the outputs and the diagnostic are unchanged.

## Round 2 findings: status

| ID | Status | Note |
|---|---|---|
| N1 | Resolved | §4 now reads "fail if more than 2.5 % of resamples have an eligible node with mean(d\*) ≤ 0". This is correct and matches §3.3. |
| N2 | Resolved | §1 now reads "√0.5 times the sum of two such draws (sd 1)". |
| N3 | Resolved | §3.3 gives the largest gap: 0.643 vs 0.538, \|z\| ≈ 3.0, at normal, g = 0.3, P3, μ = 1.5. It also gives χ² = 40.9 on 26 df (p ≈ 0.03) and says the signs are mixed. These figures match my round 2 computation. It states that the conclusions rest on the within-rep contrast between the declared rule and drop-bad, which is the right basis. Your message mentions sign counts (15 positive, 8 negative), but the report does not state them, so there was nothing to verify. |
| N4 | Resolved | §4 now reads "Under normal and t3 noise, with homogeneous or heterogeneous μ". |
| N5 | Resolved | The jackknife-cause statement is credited to the reviewer's re-implementation, and the report notes that the committed outputs do not split failures by cause. "Somewhat below that of (c)" replaces "close to". |

## New findings

None that affect content.

One cosmetic nit: a few edited lines now exceed the file's usual wrap width (§1, §3.1 and §4). This is optional and does not affect the verdict.

## Result

There are no open BLOCKING, MAJOR or MINOR findings across rounds 1–3. The diff introduces nothing new: every change is confined to the five noted spots, and no numbers outside them changed.
