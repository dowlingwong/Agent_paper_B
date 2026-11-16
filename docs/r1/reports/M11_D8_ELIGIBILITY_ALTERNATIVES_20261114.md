# M11 D8: eligibility alternatives and split proportions (14 November 2026)

**AI-assisted (Claude, Mac-local agent); synthetic simulation only; not an author decision; the gate code is not
changed.** This report answers the author's message of 14 Nov:

> D8：暂不确认。Q2 的 dev z ≥ 6 在 2–6 个 dev 实例下近乎随机排除节点，不采用为最终规则；请在模拟里比较两种替代
> （i）资格判断用 train+dev 实例（不碰 test），（ii）用 D21 噪声底 σ_node 定门槛，报告各自的 P(STOP)、被排除节点比例和 T1
> 层是否保留，附推荐；Q4 先固定 train/dev/test 比例，再定计划可达的分层下限（选项 d→c）；Q3b 以 uv.lock（NumPy 2.4.4，
> Python 3.13）为准，.python-version 不作约束；ROW 选 (a)。

Branch `mac-m11-d8-alt-20261114` from `mac-m11-d8-v2-20261114` @ `e3c0921e` (gate `da264a40`, unchanged). Script
`r1/scripts/d8_eligibility_alternatives_sim.py`, seed 20261114, run in `/tmp/np244` (Python 3.13.18, NumPy 2.4.4, as
D8-Q3b fixes; `.python-version` is not a constraint). Full output: `reports/m11_d8_alternatives_20261114/sim_output.md`
and `.json`.

## 1. Model (declared)

- **d and units.** Per node, paired per-instance differences d = oracle − A2 with true mean μ and sd 1, so μ is the
  effect in units of the per-instance sd. Normal and left-skewed d, as in the 9/14 Nov simulations. Train, dev and test
  instances independent. δ_n is assumed non-binding.
- **Layout from the plans.** T0 = 8 nodes × 18 instances (RUNBOOK B.1/B.1b). T1 = 10 nodes × 12 instances (TRACK_G
  G.5, "about 12 campaigns per T1 node") or × 6 (if each instance runs in both memory modes, as on T0).
- **Split proportions (Q4 option d).** Two candidates, train : dev : test:
  - P1 = 1/3 : 1/3 : 1/3, i.e. T0 6/6/6, T1 4/4/4 (×12) or 2/2/2 (×6);
  - P2 = 1/2 : 1/6 : 1/3, i.e. T0 9/3/6, T1 6/2/4 (×12) or 3/1/2 (×6).
  Test is 1/3 in both, so the test sizes are the same: T0 6, T1 4 or 2.
- **Eligibility rules.**
  - **R0**, the gate as drafted: dev z = mean / (sd(ddof 1)/√n_dev) ≥ 6.
  - **R1, alternative (i):** the same paired z on **train + dev** instances, test untouched; thresholds 6 and 3.
  - **R2, alternative (ii):** a σ_node threshold, z_σ = mean·√n / σ_node ≥ c, with σ_node the D21 noise floor taken as
    known, so no sd is estimated from the few instances. Applied on dev only (R2-dev) or on train + dev (R2-trdev);
    c = 3 (and 6). σ_node = r × (per-instance sd of d) with r = 1 (and 0.5, 2) as a sensitivity, because the ratio
    of D21's per-run seed noise to the per-instance sd of the utility difference is not known yet.
- **STOP, as in the gate.** An eligible node STOPs the gate if its point test mean or any of 2,000 bootstrap test means
  is ≤ 0. The gate also STOPs when no node is eligible.
- **Outputs.** P(STOP); excluded share for T0 and T1 (1 − mean eligibility); and P(T1 kept), the probability that at
  least one T1 node is eligible (unconditional, not conditional on the gate being read). Each scenario puts every node at the same μ ∈ {0.25, 0.5, 1, 1.5, 2}.

## 2. Results (normal d, T1 × 12; the other cases in the full output)

Cells: P(STOP) / excluded share T0, T1 / P(T1 kept).

**Split P1 (T0 6/6/6, T1 4/4/4)**

| rule | μ = 0.25 | μ = 0.5 | μ = 1 | μ = 1.5 | μ = 2 |
|---|---|---|---|---|---|
| R0 dev z ≥ 6 | 0.98 / 1.00, 0.99 / 0.11 | 0.95 / 0.99, 0.98 / 0.18 | 0.76 / 0.95, 0.93 / 0.52 | 0.55 / 0.83, 0.84 / 0.83 | 0.34 / 0.63, 0.71 / 0.97 |
| R1 train+dev z ≥ 6 | 1.00 / 1.00, 1.00 / 0.01 | 0.98 / 1.00, 0.99 / 0.06 | 0.77 / 0.93, 0.95 / 0.42 | 0.69 / 0.66, 0.80 / 0.90 | 0.53 / 0.25, 0.52 / 1.00 |
| R1 train+dev z ≥ 3 | 0.96 / 0.96, 0.96 / 0.35 | 0.95 / 0.84, 0.88 / 0.72 | 1.00 / 0.32, 0.51 / 1.00 | 0.99 / 0.03, 0.14 / 1.00 | 0.73 / 0.00, 0.02 / 1.00 |
| R2-dev c = 3, r = 1 | 0.99 / 0.99, 0.99 / 0.05 | 0.94 / 0.96, 0.98 / 0.19 | 0.90 / 0.71, 0.84 / 0.82 | 0.94 / 0.25, 0.51 / 1.00 | 0.69 / 0.03, 0.16 / 1.00 |
| R2-trdev c = 3, r = 1 | 0.98 / 0.98, 0.99 / 0.11 | 0.92 / 0.90, 0.94 / 0.46 | 1.00 / 0.32, 0.57 / 1.00 | 0.99 / 0.01, 0.11 / 1.00 | 0.74 / 0.00, 0.00 / 1.00 |
| R2-trdev c = 3, r = 0.5 | 0.99 / 0.74, 0.78 / 0.91 | 1.00 / 0.41, 0.54 / 1.00 | 1.00 / 0.02, 0.09 / 1.00 | 0.99 / 0.00, 0.00 / 1.00 | 0.74 / 0.00, 0.00 / 1.00 |
| R2-trdev c = 3, r = 2 | 1.00 / 1.00, 1.00 / 0.00 | 1.00 / 1.00, 1.00 / 0.00 | 0.98 / 0.99, 1.00 / 0.01 | 0.49 / 0.79, 0.96 / 0.35 | 0.50 / 0.18, 0.63 / 0.99 |

**How P(STOP) splits (P1, normal d, T1 × 12).** P(STOP) = P(no node eligible) + the STOP caused by eligible nodes'
test means. The first part (`p_no_eligible` in the json):

| rule | μ = 0.25 | μ = 0.5 | μ = 1 | μ = 1.5 | μ = 2 |
|---|---|---|---|---|---|
| R0 dev z ≥ 6 | 0.86 of 0.98 | 0.76 of 0.95 | 0.31 of 0.76 | 0.04 of 0.55 | 0.00 of 0.34 |
| R1 train+dev z ≥ 6 | 0.98 of 1.00 | 0.91 of 0.98 | 0.34 of 0.77 | 0.00 of 0.69 | 0.00 of 0.53 |
| R1 train+dev z ≥ 3 | 0.47 of 0.96 | 0.07 of 0.95 | 0.00 of 1.00 | 0.00 of 0.99 | 0.00 of 0.73 |
| R2-trdev c = 3, r = 1 | 0.77 of 0.98 | 0.24 of 0.92 | 0.00 of 1.00 | 0.00 of 0.99 | 0.00 of 0.74 |
| R2-trdev c = 3, r = 2 | 1.00 of 1.00 | 1.00 of 1.00 | 0.95 of 0.98 | 0.10 of 0.49 | 0.00 of 0.50 |

**Split P2 (T0 9/3/6, T1 6/2/4).** In the model, R1 and R2-trdev do not depend on the split (they pool train + dev,
12 and 8 instances either way); the printed P2 values differ from P1 only by Monte Carlo error, up to 0.03. R0 and
R2-dev change because n_dev changes:

| rule | μ = 0.25 | μ = 0.5 | μ = 1 | μ = 1.5 | μ = 2 |
|---|---|---|---|---|---|
| R0 dev z ≥ 6 | 0.95 / 0.97, 0.92 / 0.55 | 0.91 / 0.96, 0.89 / 0.70 | 0.82 / 0.90, 0.81 / 0.87 | 0.64 / 0.82, 0.73 / 0.96 | 0.36 / 0.71, 0.64 / 0.99 |
| R2-dev c = 3, r = 1 | 0.99 / 1.00, 0.99 / 0.05 | 0.96 / 0.98, 0.99 / 0.12 | 0.76 / 0.89, 0.94 / 0.44 | 0.68 / 0.66, 0.81 / 0.88 | 0.49 / 0.32, 0.56 / 1.00 |

**T1 × 6 with P2 (T1 3/1/2):** R0 can never include a T1 node, because one dev instance gives no sd. P(T1 kept) is
0.00 at every μ. R1 keeps T1 once nodes have signal (0.97 at μ = 2 with z ≥ 6, ≥ 0.98 from μ = 1 with z ≥ 3).

**Per-node test STOP**, the probability that an eligible node STOPs the gate (normal d), from the committed output;
the point-mean part in brackets is the formula Φ(−μ√n_test), not a simulated column:

| n_test | μ = 0.5 | μ = 1 | μ = 1.5 | μ = 2 |
|---|---|---|---|---|
| 6 | 0.85 (point 0.11) | 0.55 (0.007) | 0.23 (0.000) | 0.06 (0.000) |
| 4 | 0.76 (0.16) | 0.51 (0.02) | 0.24 (0.001) | 0.09 (0.000) |
| 2 | 0.52 (0.24) | 0.29 (0.08) | 0.12 (0.02) | 0.04 (0.002) |

The per-node test STOP does **not** fall steadily with more test instances. A side calculation (not in the committed
script; same rule, 2,000 reps × 2,000 resamples, seed 20261115, `/tmp/np244`) gives, for n_test = 2 / 4 / 6 / 9 / 12 /
18: 0.28 / 0.49 / 0.55 / 0.49 / 0.40 / 0.21 at μ = 1, and 0.13 / 0.24 / 0.22 / 0.13 / 0.04 / 0.01 at μ = 1.5. It
rises up to about 6 test instances and falls clearly only from about 12. (The round-1 reviewer found the same shape
independently.)

## 3. Reading

1. **R0 excludes nodes almost independently of their signal.** From μ = 0.25 to μ = 2 its T0 excluded share moves only
   from 1.00 to 0.63 (P1), and from 0.97 to 0.71 (P2). R1 makes eligibility a steep function of μ: with z ≥ 3 on train
   + dev (12 instances on T0), it excludes 96 % of T0 nodes at μ = 0.25, 32 % at μ = 1 and 0 % at μ = 2.
2. **R1 is independent of the train/dev proportion** and, from about μ = 1 (z ≥ 3) or μ = 2 (z ≥ 6), keeps T1 in
   every layout, including T1 × 6, where R0 drops T1 entirely under P2.
3. **R2 cannot be calibrated yet.** Its behaviour is set by r = σ_node / sd(d):
   - if r = 0.5, it already lets in about a quarter of T0 nodes at μ = 0.25 (T0 excluded share 0.74) and most of
     them at μ = 0.5 (0.41);
   - if r = 2, it excludes nearly everything below μ = 1.5.

   D21's σ_node is a per-run seed noise of the metric. It does not contain the instance-to-instance spread of the
   utility difference, so r < 1 is the likely case, which is the permissive one. A known-σ rule also ignores that
   spread, which is part of what eligibility should guard against. R2-trdev with r = 1 behaves almost like R1 with
   z ≥ 3. Only the product c·r matters (c = 3, r = 2 behaves like c = 6, r = 1). Another reading of "用 D21 噪声底
   σ_node 定门槛" is a fixed floor, mean ≥ k·σ_node, of the same form as the existing D18 δ_n criterion (assumed
   non-binding here); it needs r just the same, so the conclusion does not change.
4. **P(STOP) stays high under every rule, for two different reasons** (split table in §2).
   - **No node eligible.** For the strict rules at low and middle μ, most of P(STOP) is this part: R0 at μ = 0.25,
     0.86 of 0.98; R1 z ≥ 6 at μ = 0.5, 0.91 of 0.98; R2-trdev r = 2 at μ = 1, 0.95 of 0.98.
   - **Test-side STOP of eligible nodes.** Where nodes are eligible (R1 z ≥ 3 from μ = 0.5, every rule from about
     μ = 1.5) the cause is the test side. An eligible node with 2–6 test instances STOPs the gate with probability
     0.55 at μ = 1 and 0.23 at μ = 1.5 (n_test = 6). That comes almost entirely from the "any of 2,000 bootstrap
     means ≤ 0" part: with so few instances, some resamples repeat the smallest difference, so one negative test
     difference is usually enough.

   So a better eligibility rule moves P(STOP) from the first part to the second and can **raise** it: R1 z ≥ 3 is
   0.95–1.00 up to μ = 1.5, the highest of the rules. Only excluding most nodes, as R0 does, lowers the second part.
5. **Left-skewed d** (full output): every z-based rule lets in more null-ish nodes, because a skewed sample inflates the
   t statistic. For example, R1 z ≥ 3 has a T0 excluded share of 0.72 at μ = 0.25. P(STOP) for R1 z ≥ 3 stays
   0.84–0.99; across all rules it is 0.49–1.00.

## 4. Recommendation

- **Eligibility: R1 (alternative i), train + dev pooled, paired z ≥ 3, plus δ_n.** It is sharp in μ, independent of
  the train/dev proportion, keeps T1, and needs no unknown scale. Do not adopt R2 until D21's σ_node can be put on the
  utility scale and compared with the per-instance spread. If a stricter screen is wanted, z ≥ 6 on train + dev is
  coherent but excludes most nodes below μ ≈ 2. Under the current test-side rule z ≥ 3 has the highest P(STOP), so
  the threshold is provisional until D8-TEST is decided.
- **Before confirming D8, the test-side STOP needs a decision as well** (new question D8-TEST). With 2–6 test instances
  per node, the per-node bootstrap STOP makes the whole gate STOP with high probability whenever enough nodes are
  eligible, whatever the eligibility rule. Options include:
  - STOP only on the point test denominator per node, and keep the bootstrap for the IQM interval;
  - a tier-level or pooled bootstrap of the denominator;
  - more test instances, which the plans do not allow (Q4), and which help only from about 12 test instances per
    node (see the side calculation in §2).

  This is the author's call. Nothing is changed in `gate.py`.
- **Q4 (d → c): proportions train : dev : test = 1/2 : 1/6 : 1/3 (P2).**
  - Under R1 the train/dev division does not affect eligibility, so it can favour Track P training (9 vs 6 train
    instances on T0).
  - Test at 1/3 gives the plan-achievable tier floors **T0 ≥ 6 test instances; T1 ≥ 4 if T1 nodes have about 12
    instances, ≥ 2 if about 6**.
  - A floor of 2 makes the test denominator on such a node nearly uninformative. If T1 runs each instance in both
    memory modes, the author may prefer a T1 test floor of 4 and so 12 distinct instances per T1 node (a G.5 plan
    change). Under the current test-side rule that has a cost: an eligible node with 4 test instances STOPs more
    often than one with 2 (0.51 vs 0.29 at μ = 1), so this choice depends on D8-TEST.
  - Under R0, P2 would leave T1 × 6 with one dev instance and drop T1 entirely: another reason not to keep R0.
- **D8-Q3b:** recorded as answered: environment = harness uv.lock (NumPy 2.4.4, Python 3.13); `.python-version` not a
  constraint. **D8-ROW:** (a), the row as drafted binds the gate by SHA. Both are carried into the next gate change and
  confirmation draft; nothing is redrafted now, since D8 is not being confirmed.

## 5. What the next gate change would be (not done)

If the author adopts R1:
- `gate.py` takes the train-split arrays as an input and computes the eligibility z on train + dev;
- `DEV_Z_MIN` becomes `ELIG_Z_MIN` = 3 (or the chosen value);
- tests, the analysis-guard row text and the confirmation draft follow, with a new gate SHA and review.

If the author changes the test-side STOP, that change goes in the same unit.
