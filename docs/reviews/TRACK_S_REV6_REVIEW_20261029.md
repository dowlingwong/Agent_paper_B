# Review of Track S runbook, revision 6 (29 Oct 2026)

AI-assisted review (fresh agent); read-only; authorizes nothing.

**Scope.** `RB` = rev-6 runbook; `R5` = rev-5 review. Snapshot spot-checks held: h `campaign.py`:1287 (loop exits on `compute_budget.exhausted`), h `budget.py`:59–75, 105–118 (`worker_runs_remaining`), h `langgraph_manager.py`:122–141 (prompt shows trial index, no runs-left field), apb `c3/control.py`:16–23, `c3/features.py`:257, 385 (trial-indexed `budget_frac_left`).

**Verdict: ACCEPT WITH MINOR CHANGES.** 0 BLOCKING, 0 MAJOR, 10 MINOR. R5's blocker is fixed in the body, and so are the four MAJORs. None of the changes in rev 6 makes a route automatic or invalid.

## 1. Revision 5 → 6 (body checked)

| Finding | Verdict | Reason |
|---|---|---|
| BL-1 | ACCEPT | Threshold g0 − b_budget·r with b_budget > 0 (RB:131, 133). D1′ unit test is in S0.3 (RB:94). h_budget is two-sided (keep±). P0 is in the power gate. N0 is defined by zero oracle gain at non-binding W (RB:98). |
| MA-1 | ACCEPT | The same paired dev instances, 4 single-channel members, S0.6 before S0.7 and the one resize 20 → 40 are all in. Residual: P(correct selection) is not reported, and the dev between-configuration sd is not matched (mi-6). |
| MA-2 | ACCEPT | Two-sided h grid; b_info·τ_pred; matched-static wording rule (RB:30, 160). |
| MA-3 | ACCEPT | Grids are in σ_cmp,vary (RB:97, 99), and δ_Y is a declared raw-unit constant (RB:151). |
| MA-4 | ACCEPT | B is decided per B-eligible node and needs at least one such node (RB:32, 141–147). |
| mi-1 | PARTIAL | Defined on π\*'s dev states, but E1 and E2 are not reported separately. |
| mi-2 | ACCEPT | Holm everywhere; precedence A > A-small > B > inconclusive. |
| mi-3 | PARTIAL | Truncation and the max with the S0.7 dev estimate are in. The audits of the truncated incumbents are not stated, and audited Y at W needs them. |
| mi-4 | ACCEPT | The exact placebo runs first in S3e. |
| mi-5 | PARTIAL | The upper bound is stated. The claim that worker and audit runs are "in parallel with the LLM" holds only if more campaigns run than servers, because worker runs are serial inside a campaign. The tabular run time and the resize are not in the totals. |
| mi-6, mi-7, mi-8 | ACCEPT | The zero member is gone, the binding share is reported and the wording is fixed. The AC-racing citation is optional. |

## 2. Consistency and sign check

**Renumbering.** Every reference matches S0.6 = calibration and S0.7 = tuning: the seed blocks, the S0.5b fallback ("S0.7 + S3e"), S0.6 → "S0.7 tuning design", S0.8, the §3 B conditions, the secondaries, §4, §5 ("dropped before S0.6"), the §9 hosts and schedule, and §0 element (3). The cost rows check out (13 × 20 = 260; 20×2 + 10×2 = 60), with one exception (mi-4). One trivial slip: Provenance says "Four independent reviews" and then lists five.

**Sign on D1′** (N = 2, K = W = 1, V\* ∈ {1, 3} equiprobable; proposals_left includes the current one).

| State | runs_left/W | proposals_left/N | r | Threshold |
|---|---|---|---|---|
| Proposal 1 | 1 | 1 | 0 | g0 ∈ (1, 3) |
| Proposal 2, after a skip | 1 | 0.5 | +0.5 | g0 − 0.5 b |

With b > 2(g0 − 1), the rule executes V\* = 1 at proposal 2 and reaches the optimum, 0.5·3 + 0.5·2 = 2.5. The best static rule gets 0.75·3 = 2.25. These match RB D1′. The direction is correct. The value of r depends on whether proposals_left counts the current proposal (mi-7).

## 3. New issues from rev 6

No new issue is BLOCKING or MAJOR. Two need attention before S0.8.

- **The static g grid was narrowed** to {0.05, 0.1, 0.2} σ_cmp,vary. R5 refers to values up to 0.4, and §11 does not record the change. At a binding W the best static threshold can lie above 0.2. The budget member then wins when r < 0 simply by raising its threshold, which is a static shift. The matched-static wording protects the honesty of A, but on only 30 instances. → mi-1.
- **The scope of the power gate** in S0.6 is global ("route B is unavailable"), but in §3 it is per B-eligible node. Tabular will probably fail the gate and be A-only, and under the S0.6 reading it would block B on digits. → mi-2.

## 4. Minor changes to apply before S0.8

1. **g grid.** Restore 0.4 σ_cmp,vary in the g grid, or pre-declare one extension if m\* falls on the upper edge (decided on dev, before S0.8). Record the change in §11.
2. **Gate scope.** State in S0.6 that the power gate (and the resize) is evaluated per B-eligible node, as §3 already says.
3. **Oracle gains.** Declare how they are computed (large-replication evaluation on the synthetic node, with a tolerance) for N0 (≤ 0) and for the "exactly δ_Y" planting in P0, P1 and P2±.
4. **S3e cost.** The secondaries are matched static, two other channels, π′ and A2-U, so ≈ 5 campaigns per instance, not 3. Fix the row, and add the resize to the totals.
5. **n after S0.8.** If σ_D,UCL rises at S0.8, n and B-eligibility change after S0.6. State that n and B-eligibility are final at S0.8, and re-run S0.6 if n changes.
6. **Report P(CS) and false-B rates.** Report P(correct selection) and P(route B | positive control) next to power, and match the synthetic dev between-configuration sd. A power LB of 0.6 tolerates a false-B rate up to ≈ 0.35. The B wording ("with this tuning budget") is honest about this, but the rate should be visible.
7. **Pin the r convention.** Pin it (proposals_left inclusive of the current proposal, evaluated before the decision) in the D1′ test.
8. **Audits and wall time.** Add K = 5 audits for each truncated incumbent in S0.5b. Recompute the wall time with worker runs serial inside a campaign and with the tabular run time.
9. **Matched-static rule.** The "≥ half the gain" rule on 30 instances is a point-estimate rule (sd ≈ 0.55 δ_Y on digits at σ_D = 0.01). Report its CI, or run the matched static on all n instances.
10. **Wording and the no-binding case.**
    - Describe π\* as "selected among four fixed-coefficient single-channel members".
    - In §5, declare W for the case where no W binds.
    - Split the flip rate into E1 and E2.

## 5. What blocks acceptance

Nothing. No route outcome is automatic or invalid, and B is reachable on digits. With 20 paired dev instances and 4 members, P(CS) ≈ 0.8 at δ_Y/σ_D,mean ≈ 1.5; this is a normal approximation, not a run. Apply items 1–5 before S0.8; items 6–10 can go in with the pre-declaration.
