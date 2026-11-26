# B2 power-plan rule (proposal for the author's PLAN §10 row; 14 November 2026)

**AI-assisted (Claude, Mac agent). A proposal, not an author decision.** It governs nothing until the author commits
the PLAN §10 row `R1-EXAM-B2-POWER-PLAN` with the rule and the number.

The author signed (14 Nov) that the Mac agent computes the B2 instance count from B1 data by a pre-declared rule. The
cap is 10 per node; if the rule requires more than 10, it stops and the author decides; the author confirms the rule
and the number once they are final.

**This file is committed before any number is computed from B1 data.** The script
`r1/scripts/b2_power_plan.py` implements it unchanged.

## 1. What B2 estimates

- For each B2 node *j* and finalist *c*: the mean over instances of the B2 **final audited Y**. That is the mean of
  the ten metrics on seeds 9201–9210 of the root's final incumbent, thinking off. X.7 (a) ranks finalists by B2 final
  audited Y.
- **One finalist:** the target is the precision of that finalist's per-node mean.
- **Two or more finalists:** the target is the precision of the per-node difference between two finalists, paired by
  instance.

## 2. Variance from B1 (`b1_manifests.json`, run `7912_20261113_d`)

B1 has no final-Y audits (`final_audits` is empty in B1), so a root-level proxy is used.

- **Roots used:** every B1 thinking-off root of a registry `candidate` (not the anchors) in the manifests. These are
  the 15 Stage A-passing, thinking-off-capable candidates. They are pooled whatever their D28 or finalist status,
  because the variance is a property of the node and the protocol, not of the selection.
- **Root proxy Y_r:** the mean of `incumbent_metrics` (4 seeds, 9101–9104) of the root's **last audited proposal**
  (largest trial index). That is the last incumbent the audits observed. A root with no audited proposal is left out
  and counted.
- **Biases, stated:**
  1. A keep at the last audited proposal, or at a later unaudited trial, is missed, so Y_r can lag the true final
     incumbent. The direction of the effect on the variance is not known.
  2. Y_r averages 4 audit seeds while B2's final Y averages 10, so the seed-noise part of Var(Y_r) is 10/4 times
     larger than in B2. This makes the estimate conservative (too large) for B2.
- **Per (candidate, node):** s²_cj = sample variance (ddof 1) of Y_r over its instances, for cells with ≥ 2
  instances.
- **Pooled per node:** V̂_j = Σ_c (n_cj − 1) s²_cj / Σ_c (n_cj − 1), with dof_j = Σ_c (n_cj − 1).
- **Upper limit:** V_j = V̂_j · dof_j / χ²_{0.20}(dof_j), the one-sided 80 % χ² upper confidence limit, the same
  convention as Track S's σ_D UCL.

## 3. Target, α and effect-size basis

- **Effect-size basis:** σ_node,j, the per-node noise constant of the accepted C1 noise-floor table
  (R1-C1-FLOOR, 24 Oct; `results/r1/pilot/E1_20261022T214606Z/summary.json`). It is computed as in
  `r1.c3.dataset.node_noise`: the median `sd_joint` over the node's material edits. This is a declared, pre-existing
  per-node unit, fixed before B1, that the project already uses to standardise effects (C3 labels, Track S g).
- **Target:** the two-sided 95 % confidence interval (α = 0.05, Student t) of the B2 quantity of §1 has half-width
  ≤ **h_j = 1 · σ_node,j**.

## 4. Formula

- k = 1 with one finalist, k = 2 with two or more. k = 2 is the variance of a paired difference bounded by
  2 V_j, which ignores the positive within-instance correlation and so is conservative.
- **n_j** = the smallest integer n ≥ 2 with t_{0.975, n−1} · √(k · V_j / n) ≤ h_j.
- **n = max_j n_j** over the B2 nodes, which are the three B1 nodes `digits_mlp`, `openml_credit_approval` and
  `openml_ionosphere`.

## 5. Cap

- If n ≤ 10, then `b2_instances_per_node = n`, with instance seeds 9011 … 9010 + n.
- If **n > 10**, the rule's result is a **STOP for the author**. The number is **not** clipped to 10. The author
  decides (for example a different target, a different basis, or an explicit exception).
- n must also fit the code's fresh namespace, 1 ≤ n ≤ 89; with the cap this always holds.

## 6. What is reported with the number

- Per node: the number of roots and of excluded roots, dof_j, V̂_j, V_j, σ_node,j, n_j.
- n, the cap status, the sha256 of `b1_manifests.json` and of the script, and the script output file with its sha256.
