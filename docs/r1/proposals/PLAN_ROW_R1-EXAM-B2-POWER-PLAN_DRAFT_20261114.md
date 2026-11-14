# PLAN §10 row draft — `R1-EXAM-B2-POWER-PLAN` (for the author's signature; 14 November 2026)

**AI-assisted (Claude, Mac agent). A draft for the author; it governs nothing until the author commits it in PLAN
§10 under a dated author heading.** The B2 code unit's author gate reads this row: it requires a dated author §10
row `R1-EXAM-B2-POWER-PLAN` whose decision cell contains the literal `b2_instances_per_node = <n>` equal to the
config value.

## Inputs (all on `mac-b2-plan-20261114`)

| Item | Value |
|---|---|
| Rule | `docs/r1/proposals/B2_POWER_PLAN_RULE_20261114.md`, sha256 `0294387c…0142`, committed in `b7a4fa40` before any number was computed |
| Script | `r1/scripts/b2_power_plan.py`, sha256 `c74a4252ed952a7ad4fb69d32fbe69ccc0a58626a3fce9ad12b480025e24a59f` (commit `73830064`; 7 synthetic tests in `r1/tests/test_b2_power_plan.py`) |
| B1 data | `docs/r1/reports/b1_d_20261113_evidence/b1_manifests.json`, sha256 `dc5cd04d…b510e62`, run `7912_20261113_d` |
| σ_node source | `results/r1/pilot/E1_20261022T214606Z/summary.json` (R1-C1-FLOOR), sha256 `eabc2f5c…3793` |
| Output | `docs/r1/reports/b2_power_plan_20261114/b2_power_plan.json`, sha256 `1236d805ada9587ffd9a5853252ffaa45d345686fb54c331a9cf1e3d96208a6b` |
| Finalists (STOP 5) | `[gemma4_31b]`, so k = 1 |

## Result

| Node | roots (dof) | sd of root final-Y proxy (pooled) | 80 % UCL sd | σ_node = h | n_j |
|---|---|---|---|---|---|
| digits_mlp | 60 (45) | 0.00282 | 0.00312 | 0.00661 | **4** |
| openml_credit_approval | 60 (45) | 0.00492 | 0.00544 | 0.01462 | 3 |
| openml_ionosphere | 60 (45) | 0.01122 | 0.01239 | 0.04237 | 3 |

**n = max n_j = 4 ≤ 10 (within the cap).** So `b2_instances_per_node = 4`, with instance seeds 9011–9014. No root was
excluded.

- *Sensitivity, descriptive only, not the rule:* with two or more finalists (k = 2) the rule would give 5 / 4 / 4,
  so n = 5.
- *Cost note:* with one finalist, B2 is 3 nodes × 4 instances = 12 thinking-off roots. The descriptive thinking-on
  rerun of the code (`B1_STOP5_FINALISTS_20261114.md` §4) adds another 12.

## Row text (English, for the table)

| R1-EXAM-B2-POWER-PLAN (⟨date⟩) | **B2 instance count by the pre-declared rule; b2_instances_per_node = 4.** Rule `proposals/B2_POWER_PLAN_RULE_20261114.md` (sha256 `0294387c…`, committed before any number was computed). Quantity: per B2 node, the finalist's mean B2 final audited Y (seeds 9201–9210, thinking off); with ≥ 2 finalists, their paired difference. Variance: the pooled within-candidate between-instance variance of a root-level final-Y proxy (the last audited incumbent's mean metric on 9101–9104) over all B1 `_d` thinking-off candidate roots, at the one-sided 80 % χ² UCL (conservative for B2, which averages 10 seeds, not 4). Target: two-sided 95 % CI half-width ≤ 1 σ_node per node (σ_node = the R1-C1-FLOOR noise constant, median sd_joint over material edits). n_j = smallest n ≥ 2 with t_{0.975,n−1}·√(k·V_j/n) ≤ σ_node,j (k = 1 for one finalist, 2 for ≥ 2); n = max_j n_j; cap 10 per node, and n > 10 is a STOP for the author, never clipped. Result with the STOP 5 finalists `[gemma4_31b]` (k = 1): n_j = 4 / 3 / 3 (digits_mlp / openml_credit_approval / openml_ionosphere), **b2_instances_per_node = 4**, seeds 9011–9014. Script `r1/scripts/b2_power_plan.py` (sha256 `c74a4252…`), output `reports/b2_power_plan_20261114/b2_power_plan.json` (sha256 `1236d805…`), B1 data `b1_manifests.json` (`dc5cd04d…`). Records the author's instruction of 14 Nov (instance count from B1 data by a pre-declared rule, cap 10 per node, STOP above 10, author confirms rule and number). |

## 可直接粘贴的中文（作者签字用）

> **R1-EXAM-B2-POWER-PLAN（⟨日期⟩）：B2 实例数按预先声明的规则确定，b2_instances_per_node = 4。**
>
> **规则：** `proposals/B2_POWER_PLAN_RULE_20261114.md`（sha256 `0294387c…`），在计算任何数字之前提交。
>
> **估计量：** 每个 B2 节点上，入围模型的 B2 最终审计 Y 的均值（种子 9201–9210，thinking off）；若入围 ≥ 2 个，则为两两的配对差。
>
> **方差：** 来自 B1 `_d` 全部 thinking-off 候选根。每个根取最终 Y 的代理值，即最后一次被审计的 incumbent 在 9101–9104 上的平均指标；方差为同一候选内、跨实例的合并方差，取单侧 80 % χ² 上限。B2 用 10 个种子而 B1 只用 4 个，所以这个估计对 B2 偏保守。
>
> **目标：** 每个节点双侧 95 % 置信区间的半宽 ≤ 1 个 σ_node（σ_node 为 R1-C1-FLOOR 的节点噪声常数，即重要编辑的 sd_joint 中位数）。
>
> **公式：** n_j 为满足 t_{0.975,n−1}·√(k·V_j/n) ≤ σ_node,j 的最小 n（n ≥ 2；入围 1 个时 k = 1，≥ 2 个时 k = 2），n = 各节点 n_j 的最大值。每节点上限 10；超过 10 则停下交作者决定，不截断。
>
> **结果：** STOP 5 入围名单为 `[gemma4_31b]`（k = 1），n_j 依次为 4 / 3 / 3（digits_mlp / openml_credit_approval / openml_ionosphere），故 **b2_instances_per_node = 4**，种子 9011–9014。
>
> **依据文件：** 脚本 `r1/scripts/b2_power_plan.py`（sha256 `c74a4252…`），输出 `reports/b2_power_plan_20261114/b2_power_plan.json`（sha256 `1236d805…`），B1 数据 `b1_manifests.json`（`dc5cd04d…`）。
