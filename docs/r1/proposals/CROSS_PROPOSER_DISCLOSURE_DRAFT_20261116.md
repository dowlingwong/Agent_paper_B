# Draft for the author: cross-proposer disclosure paragraph (sweep 1 vs sweep 2), from X.7(c) (16 November 2026)

**Draft only. AI-assisted (Claude, Mac agent). Not an author decision.** This text is for the author to use or edit in
the cross-proposer tables of the manuscript or its appendix: R1-MAIN-PROPOSER (c) and (i), R1-EXAM-X7 (a) and (c).

**Sources.**
- The X.7(c) appendix (`mac-s2-m5-x7c-20261116`): `reports/X7C_APPENDIX_20261116.md` and `x7c_output.json`. It was
  accepted after three rounds; the declared outcome was "differences".
- One post hoc computation added here: `r1/scripts/x7c_mu_paired.py`, output
  `reports/x7c_appendix_20261116/mu_paired.{json,md}`. It gives paired B1 μ̂ differences with the appendix's own inputs,
  thinking-off filter, paired cluster bootstrap and seed. It is not part of the declared X.7(c) decision.

## Paragraph (English)

> **Proposer differences between the two sweeps.** Sweep 1 used `qwen2.5-coder:7b` as the manager; sweep 2 uses the
> selected pick, `gemma4_31b` with thinking off (R1-EXAM-X7). The pick was selected on the B1/B2 exam data, so the
> comparisons below carry a winner's-curse caveat and say nothing about proposer strength.
>
> Two C3 premises differ by proposer.
>
> The first is the share of trials the duplicate/no-op rules could skip. We bound it from above by the share of
> thinking-off trials that are not audited: repeats, no-ops and invalid trials, plus each root's first trial. The bound
> is 0.175 for the pick (95 % cluster interval 0.129–0.221; 0.188 [0.142, 0.242] on the fresh B2 instances). For
> `qwen2.5-coder:7b` it is 0.545 [0.484, 0.608], and for the `random_valid` anchor 0.579 [0.524, 0.625]. Both
> finalist − anchor differences exclude zero (B1, 12 paired instance clusters); the scripted anchor's bound, 0.149, does
> not differ from the pick's. Under the pick the rule layer therefore has much
> less to skip than in sweep 1.
>
> The second is the dispersion of audited increments. Its pooled difference comes mostly from one node.
>
> The A4 forecast calibration does not differ (Brier 0.239 vs 0.214 for `qwen2.5-coder:7b`).
>
> On B1's audited mean increment, the pick lies below both the scripted anchor and `qwen2.5-coder:7b`, and none of
> these differences excludes zero:
> - pick μ̂ = −0.00089;
> - scripted μ̂ = −0.00059 (difference −0.00030 [−0.00177, 0.00096]);
> - `qwen2.5-coder:7b` μ̂ = +0.00016 (difference −0.00105 [−0.00497, 0.00296]).
>
> The pick was chosen by the exam's declared rule, not because it beat these anchors on B1.

## Paragraph (Chinese, for the author's own drafting)

> **两次 sweep 的 proposer 差异。** sweep 1 的 manager 是 `qwen2.5-coder:7b`，sweep 2 是选拔得到的 pick
> `gemma4_31b`（thinking off，R1-EXAM-X7）。pick 是在 B1/B2 考试数据上选出的，以下比较带有赢家诅咒的保留，不说明 proposer 强弱。
>
> 两个 C3 前提因 proposer 而不同。
>
> 第一，重复/no-op 规则可跳过的试验比例。上界用"未被审计的 thinking-off 试验比例"来定（包括重复、no-op、无效试验，以及每个
> root 的首个试验）：pick 为 0.175（95% 簇区间 0.129–0.221；新 B2 实例上 0.188 [0.142, 0.242]），`qwen2.5-coder:7b` 为
> 0.545 [0.484, 0.608]，`random_valid` 为 0.579 [0.524, 0.625]；这两个 finalist − anchor 的差异区间均不含 0（B1，12 个配对实例簇）；scripted anchor 的上界 0.149 与 pick 无差异。
> 因此在 pick 下，规则层可跳过的远少于 sweep 1。
>
> 第二，审计增量的离散度。其合并差异主要来自一个节点。
>
> A4 预测校准没有差异（Brier 0.239 对 0.214）。
>
> 在 B1 审计平均增量上，pick 低于 scripted anchor 和 `qwen2.5-coder:7b`，所有差异的区间均含 0：
> - pick μ̂ = −0.00089；
> - scripted μ̂ = −0.00059（差 −0.00030 [−0.00177, 0.00096]）；
> - `qwen2.5-coder:7b` μ̂ = +0.00016（差 −0.00105 [−0.00497, 0.00296]）。
>
> pick 是按考试预声明的规则选出的，而不是因为它在 B1 上胜过这些 anchor。

## Notes for the author

- **The skip bound is an upper bound** (X.7(c) report §2.1, erratum). It counts invalid trials and each root's first
  trial. By the reviewer's decomposition, the replayed-repeat parts alone are 0.351 for `qwen2.5-coder:7b` and 0.219 for
  `random_valid`, above the pick's whole bound. That comparison makes the direction hold even under the bound's
  slack. In B1 the pick's own split into parts is only bounded, because its diagnostics pool thinking-on and
  thinking-off roots.
- **The intervals** are 95 % percentile intervals from a paired cluster bootstrap over the 12 B1 instance clusters
  (10,000 resamples, seed 20261116). Twelve clusters can undercover.
- **The μ̂ differences are post hoc** (`x7c_mu_paired.py`). The disclosure R1-EXAM-X7 (a) requires is the ordering
  itself. The intervals show that none of these differences, `random_valid` included, excludes zero.
