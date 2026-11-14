# PLAN §10 row draft — `R1-EXAM-B2-POWER-PLAN` (for the author's signature; 14 November 2026; rev 2)

**AI-assisted (Claude, Mac agent). A draft for the author; it governs nothing until the author commits it in PLAN
§10.** It is a **precision plan**: it sizes B2 so that each per-node mean has a target CI half-width. It makes no
claim about power to separate finalists. The row ID keeps the word "power" only because the B2 code and the
hand-off use that name.

Rev 2 answers review round 1 (`REVIEW_POWER_round1.md`):
- B1: the decision literal now appears once.
- B2: the conservatism wording is corrected.
- N1–N6 are addressed.

The rule, the script and the output are unchanged.

## Format the B2 author gate requires (`r1/exam/runtime.py::_b2_author_rows` / `_dated_author_decisions`, B2 code unit, under review)

- The row sits in PLAN **§10** in a **two-column table**: a header line, a separator line (`|---|---|`) and the row,
  each on **one line**. A blank line or a line break inside the table ends it.
- The table is under a `### ` heading that contains the word **author** and a date written either with the **full
  month name** (`14 November 2026`) or in ISO form (`2026-11-14`). `14 Nov 2026` is not recognised.
- The first cell is exactly **`R1-EXAM-B2-POWER-PLAN`**: no date, no suffix. No cell contains `|`.
- **Only one row in §10 may carry this ID.** So paste **either** the Chinese block **or** the English block, not
  both.
- The decision cell contains **`b2_instances_per_node = <n>` exactly once**, and n equals the B2 config value.

## Inputs (all on `mac-b2-plan-20261114`)

| Item | Value |
|---|---|
| Rule | `docs/r1/proposals/B2_POWER_PLAN_RULE_20261114.md`, sha256 `0294387c0ceacaebe0907ef2c7368d85986052cac8870252bbda96454bd90142`, committed in `b7a4fa40` before any number was computed |
| Script | `r1/scripts/b2_power_plan.py`, sha256 `c74a4252ed952a7ad4fb69d32fbe69ccc0a58626a3fce9ad12b480025e24a59f` (commit `73830064`; 7 synthetic tests) |
| B1 data | `docs/r1/reports/b1_d_20261113_evidence/b1_manifests.json`, sha256 `dc5cd04dfc31758b26bb9ed5ebdec38e80ef06730b304d491c433da18b510e62`, run `7912_20261113_d` |
| σ_node source | `results/r1/pilot/E1_20261022T214606Z/summary.json` (R1-C1-FLOOR), sha256 `eabc2f5c05b08cf900ab988838e41dc7f8db35a4131f4b57e72514e0e5513793` |
| Output | `docs/r1/reports/b2_power_plan_20261114/b2_power_plan.json`, sha256 `1236d805ada9587ffd9a5853252ffaa45d345686fb54c331a9cf1e3d96208a6b` |
| Finalists (STOP 5, accepted at `7bdce776`) | `[gemma4_31b]`, so k = 1 |

**Erratum (the committed rule is not edited).** The rule (§3) and the script docstring call the σ_node function
`r1.c3.dataset.node_noise`. Its actual name is **`r1.c3.dataset.noise_table`**. The computation is the same.

## Result

| Node | roots (dof) | pooled sd of the root final-Y proxy | 80 % UCL sd | σ_node = h | n_j |
|---|---|---|---|---|---|
| digits_mlp | 60 (45) | 0.00282 | 0.00312 | 0.00661 | 4 |
| openml_credit_approval | 60 (45) | 0.00492 | 0.00544 | 0.01462 | 3 |
| openml_ionosphere | 60 (45) | 0.01122 | 0.01239 | 0.04237 | 3 |

**n = max n_j = 4, within the cap of 10.** Instance seeds 9011–9014. No root was excluded.

**How the variance estimate leans:**
- **Conservative:** the seed-noise part. The proxy averages 4 audit seeds, while B2's final Y averages 10.
- **Unknown direction:** the proxy is the last *audited* incumbent, so a keep at or after that trial is missed.
- **Assumed:** pooling assumes equal between-instance variance across candidates. The reviewer's Levene tests found
  no evidence against this, but with 4 instances per candidate the test has little power.
- **gemma4_31b against the pool:** its own B1 sd is 0.00088 / 0.00666 / 0.01922, which is **above** the pooled UCL on
  credit_approval and ionosphere. Its own point estimate still gives n = 4. Per the reviewer, its own 80 % UCL on
  3 dof would give 5.
- **Reviewer sensitivity:** an upper-envelope proxy also gives n = 4.

**Assurance, computed by the round-1 reviewer, not part of the rule.** This is the probability that the realised
half-width at n = 4 is ≤ σ_node:
- **0.85–0.91 on digits_mlp** (true sd at the UCL or at the point estimate);
- **≥ 0.96 on the other two nodes**.

**Scale of the target.** The 1·σ_node half-width is a declared choice. It is coarser than Track S's δ_Y (0.5 σ_node)
and g (0.1 σ_node), so B2's per-node means do not resolve differences on those scales.

**Descriptive only, not the rule:** with ≥ 2 finalists (k = 2) the rule gives 5 / 4 / 4, so n = 5.

**Cost:** 3 nodes × 4 instances = 12 thinking-off roots, plus 12 thinking-on descriptive roots from the code's top-3
rerun (`B1_STOP5_FINALISTS_20261114.md` §4).

## Ready to paste — Chinese (one heading line plus three table lines; use either this block or the English one)

```
### 14 November 2026 — B2 instance count (author)

| ID | Decision |
|---|---|
| R1-EXAM-B2-POWER-PLAN | **B2 实例数按预先声明的精度规则确定：b2_instances_per_node = 4（种子 9011–9014）。** 这是精度规划，不就入围模型之间的区分作功效声明。规则见 `proposals/B2_POWER_PLAN_RULE_20261114.md`（sha256 `0294387c…`），在计算任何数字之前提交。估计量：每个 B2 节点上，入围模型 B2 最终审计 Y 的均值（种子 9201–9210，thinking off）；若入围 ≥ 2 个，则为两两的配对差。方差：取 B1 `_d` 全部 thinking-off 候选根的最终 Y 代理值，即最后一次被审计的 incumbent 在 9101–9104 上的平均指标；计算同一候选内、跨实例的合并方差，取单侧 80 % χ² 上限。种子噪声部分偏保守（B1 用 4 个种子，B2 用 10 个）；“最后被审计的 incumbent”的滞后偏差方向未知；合并方差假定各候选方差相同。gemma4_31b 自身的 sd 在 credit_approval 和 ionosphere 上高于合并上限，但用它自身的点估计仍得 n = 4。目标：每个节点双侧 95 % 置信区间半宽 ≤ 1 σ_node（σ_node 为 R1-C1-FLOOR 的节点噪声常数，即重要编辑的 sd_joint 中位数；`E1_20261022T214606Z/summary.json`，sha256 `eabc2f5c…`）。公式：n_j 为满足 t_{0.975,n−1}·√(k·V_j/n) ≤ σ_node,j 的最小 n（n ≥ 2；入围 1 个时 k = 1，≥ 2 个时 k = 2），n 取各节点 n_j 的最大值。每节点上限 10；超过 10 则停下交作者决定，不截断。结果：入围名单为 `[gemma4_31b]`（k = 1），n_j 依次为 4 / 3 / 3（digits_mlp / openml_credit_approval / openml_ionosphere），n = 4。审查员估算的保证概率（n = 4 时实现半宽 ≤ σ_node）：digits_mlp 为 0.85–0.91，另两个节点 ≥ 0.96。依据文件：脚本 `r1/scripts/b2_power_plan.py`（sha256 `c74a4252…`），输出 `reports/b2_power_plan_20261114/b2_power_plan.json`（sha256 `1236d805…`），B1 数据 `b1_manifests.json`（sha256 `dc5cd04d…`）。本行记录作者 11 月 14 日的指示：实例数由 Mac agent 按预先声明的规则从 B1 数据计算，每节点上限 10，超过则停下交作者决定；规则与数字定稿后由作者签字确认。 |
```

## Ready to paste — English (one heading line plus three table lines; use either this block or the Chinese one)

```
### 14 November 2026 — B2 instance count (author)

| ID | Decision |
|---|---|
| R1-EXAM-B2-POWER-PLAN | **B2 instance count by the pre-declared precision rule: b2_instances_per_node = 4 (seeds 9011–9014).** This is a precision plan; it makes no power claim about separating finalists. Rule `proposals/B2_POWER_PLAN_RULE_20261114.md` (sha256 `0294387c…`), committed before any number was computed. Quantity: per B2 node, the finalist's mean B2 final audited Y (seeds 9201–9210, thinking off); with ≥ 2 finalists, their paired difference. Variance: a root-level final-Y proxy (the last audited incumbent's mean metric on seeds 9101–9104) over all B1 `_d` thinking-off candidate roots; the within-candidate, between-instance variance is pooled, at the one-sided 80 % χ² UCL. The seed-noise part of this estimate is conservative (4 seeds against B2's 10). The lag of the last audited incumbent has unknown direction. Pooling assumes equal variance across candidates. gemma4_31b's own sd exceeds the pooled UCL on credit_approval and ionosphere, yet its own point estimate still gives n = 4. Target: two-sided 95 % CI half-width ≤ 1 σ_node per node (σ_node = the R1-C1-FLOOR noise constant, median sd_joint over material edits; `E1_20261022T214606Z/summary.json`, sha256 `eabc2f5c…`). n_j = the smallest n ≥ 2 with t_{0.975,n−1}·√(k·V_j/n) ≤ σ_node,j (k = 1 for one finalist, 2 for ≥ 2); n = max_j n_j. Cap: 10 per node; n > 10 is a STOP for the author and is never clipped. Result with the finalists `[gemma4_31b]` (k = 1): n_j = 4 / 3 / 3 (digits_mlp / openml_credit_approval / openml_ionosphere), n = 4. Assurance, as computed by the reviewer, that the realised half-width at n = 4 is ≤ σ_node: 0.85–0.91 on digits_mlp, ≥ 0.96 on the other two nodes. Script `r1/scripts/b2_power_plan.py` (sha256 `c74a4252…`), output `reports/b2_power_plan_20261114/b2_power_plan.json` (sha256 `1236d805…`), B1 data `b1_manifests.json` (sha256 `dc5cd04d…`). Records the author's instruction of 14 Nov: the instance count comes from B1 data by a pre-declared rule, capped at 10 per node, with a STOP above 10; the author confirms the rule and the number. |
```

The heading date stands for the day the author commits the row. Any date in either accepted form works.
