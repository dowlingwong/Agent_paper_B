# Draft for the author: cross-proposer disclosure paragraph (sweep 1 vs sweep 2), from X.7(c) (16 November 2026)

**Draft only. AI-assisted (Claude, Mac agent). Not an author decision.** This text is for the author to use or edit in
the cross-proposer tables of the manuscript or its appendix: R1-MAIN-PROPOSER (c) and (i), R1-EXAM-X7 (a) and (c).

**Sources.**
- The X.7(c) appendix (`mac-s2-m5-x7c-20261116`): `reports/X7C_APPENDIX_20261116.md` and `x7c_output.json`. It was
  accepted after three rounds; the declared outcome was "differences".
- One post hoc computation added here: `r1/scripts/x7c_mu_paired.py` (`--b1-analysis` added for its input check), output
  `reports/x7c_appendix_20261116/mu_paired.{json,md}`. It gives paired B1 μ̂ differences with the appendix's own inputs,
  thinking-off filter, paired cluster bootstrap and seed. It is not part of the declared X.7(c) decision.

## Paragraph (English)

> **Proposer differences between the two sweeps, measured on the selection exam.** Sweep 1 used `qwen2.5-coder:7b` as
> its manager. Sweep 2 will use the selected pick, `gemma4_31b` with thinking off (R1-EXAM-X7).
>
> The numbers below come from the selection exam, not from the sweeps: B1 thinking-off roots on three of the eight
> sweep nodes, run on one 4090 stack, and B2 for the pick only. Within B1 every candidate ran on the same stack, so
> those comparisons isolate the proposer.
>
> Between the sweeps the contrast is proposer plus stack (R1-MAIN-PROPOSER (c)). As planned for sweep 2, which is
> not yet authorized:
> - deepthought TITAN X (sm_52) against NEMO2 L40S (sm_89);
> - the CPU host of the in-campaign worker runs;
> - context 8,192 against 32,768;
> - the default KV cache against q8_0, plus `--jinja` and the thinking switch;
> - `cache_prompt` at the default against an explicit `false`;
> - harness `6adf385` against the planned `a3fedbb`;
> - the paper commit and the container image (digest still proposed).
>
> The pick was selected on a direct llama-server on a 4090 and will run in an HTCondor container on an L40S
> (R1-SWEEP-HOST-HTC).
>
> The pick was selected on the B1/B2 data, so these comparisons carry a winner's-curse caveat and say nothing about
> proposer strength. The exam's instance and audit seeds (9001+, 9101+, 9201+) are disjoint from the sweeps' instance
> seeds and audit seeds (7001–7010) (R1-MAIN-PROPOSER (i)).
>
> **Duplicate/no-op skips.** Two C3 premises differ by proposer; this is the first. We bound the share of trials the
> duplicate/no-op rules could skip from above by the share of thinking-off trials that are not audited: repeats,
> no-ops and invalid trials, plus each root's first trial.
> - The bound is 0.175 for the pick (95 % cluster interval 0.129–0.221; 0.188 [0.142, 0.242] on the fresh B2
>   instances).
> - It is 0.545 [0.484, 0.608] for `qwen2.5-coder:7b` and 0.579 [0.524, 0.625] for the `random_valid` anchor. Both
>   finalist − anchor differences exclude zero (B1, 12 paired instance clusters).
> - The scripted anchor's bound, 0.149, is not distinguishable from the pick's.
> - A post hoc decomposition shows that the anchors' replayed repeats alone are 0.351 (`qwen2.5-coder:7b`) and 0.219
>   (`random_valid`). These lower bounds lie above the pick's whole upper bound, so under the pick the rule layer can be
>   expected to have much less to skip in sweep 2 than in sweep 1.
>
> **Dispersion of audited increments.** This is the second premise. The pick's pooled sd is lower than that of
> `qwen2.5-coder:7b`, which comes mostly from `digits_mlp`, and lower than that of `random_valid`, on all three nodes.
> It is higher than the scripted anchor's, mostly because of `openml_ionosphere`.
>
> **A4 forecast calibration.** This is not distinguishable between the pick and `qwen2.5-coder:7b` (Brier 0.239 against
> 0.214).
>
> **B1 audited mean increment.** The pick lies below both the scripted anchor and `qwen2.5-coder:7b`. In paired post hoc
> intervals none of the differences excludes zero:
> - pick μ̂ = −0.00089;
> - scripted μ̂ = −0.00059 (difference −0.00030 [−0.00176, 0.00096]);
> - `qwen2.5-coder:7b` μ̂ = +0.00016 (difference −0.00105 [−0.00497, 0.00296]);
> - against `random_valid`, the difference is +0.00400 [−0.00050, 0.00802], also not distinguishable.
>
> The pick was chosen by the exam's declared rule, not because it beat these anchors on B1.

## Paragraph (Chinese, for the author's own drafting)

> **两次 sweep 的 proposer 差异（在选拔考试上测得）。** sweep 1 的 manager 是 `qwen2.5-coder:7b`；sweep 2 将使用选拔得到的
> pick `gemma4_31b`（thinking off，R1-EXAM-X7）。
>
> 以下数值来自选拔考试，而不是 sweep 本身：B1 的 thinking-off root，在八个 sweep 节点中的三个上，同一套 4090 环境；B2 只有
> pick。B1 内所有候选在同一环境下运行，因此 B1 内的比较只反映 proposer。
>
> 两次 sweep 之间的对比是 proposer 加环境（R1-MAIN-PROPOSER (c)）。以下是 sweep 2 的计划值，sweep 2 尚未授权：
> - deepthought TITAN X（sm_52）对 NEMO2 L40S（sm_89）；
> - 运行 campaign 内 worker 的 CPU 主机；
> - context 8,192 对 32,768；
> - 默认 KV cache 对 q8_0，以及 `--jinja` 与 thinking 开关；
> - 默认 `cache_prompt` 对显式 `false`；
> - harness `6adf385` 对计划的 `a3fedbb`；
> - paper commit 与容器镜像（digest 仍为提议）。
>
> pick 是在 4090 上用直接运行的 llama-server 选出的，将在 L40S 上的 HTCondor 容器中运行（R1-SWEEP-HOST-HTC）。
>
> pick 是在 B1/B2 数据上选出的，以下比较带有赢家诅咒的保留，不说明 proposer 强弱。考试的实例与审计种子（9001+、9101+、9201+）
> 与 sweep 的实例种子及审计种子（7001–7010）不相交（R1-MAIN-PROPOSER (i)）。
>
> **重复/no-op 跳过。** 两个 C3 前提因 proposer 而不同，这是第一个。重复/no-op 规则可跳过的试验比例，用"未被审计的
> thinking-off 试验比例"作上界（包括重复、no-op、无效试验，以及每个 root 的首个试验）：
> - pick 为 0.175（95% 簇区间 0.129–0.221；新 B2 实例上 0.188 [0.142, 0.242]）；
> - `qwen2.5-coder:7b` 为 0.545 [0.484, 0.608]，`random_valid` 为 0.579 [0.524, 0.625]；这两个 finalist − anchor 的差异区间
>   均不含 0（B1，12 个配对实例簇）；
> - scripted anchor 的上界 0.149 与 pick 无法区分；
> - 事后分解显示，仅 anchor 的重放重复部分就分别为 0.351（`qwen2.5-coder:7b`）与 0.219（`random_valid`）。这两个下界都
>   高于 pick 的整个上界，因此可以预期在 pick 下，sweep 2 中规则层可跳过的远少于 sweep 1。
>
> **审计增量的离散度。** 这是第二个前提。pick 的合并标准差低于 `qwen2.5-coder:7b`（主要来自 `digits_mlp`），也低于
> `random_valid`（三个节点上均如此）；高于 scripted anchor（主要来自 `openml_ionosphere`）。
>
> **A4 预测校准。** pick 与 `qwen2.5-coder:7b` 之间无法区分（Brier 0.239 对 0.214）。
>
> **B1 审计平均增量。** pick 低于 scripted anchor 和 `qwen2.5-coder:7b`，事后配对区间中所有差异均含 0：
> - pick μ̂ = −0.00089；
> - scripted μ̂ = −0.00059（差 −0.00030 [−0.00176, 0.00096]）；
> - `qwen2.5-coder:7b` μ̂ = +0.00016（差 −0.00105 [−0.00497, 0.00296]）；
> - 与 `random_valid` 的差为 +0.00400 [−0.00050, 0.00802]，同样无法区分。
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
- **The μ̂ differences are post hoc** (`x7c_mu_paired.py`, which applies the appendix's input checks and records the
  Python and NumPy versions). The disclosure R1-EXAM-X7 (a) requires is the ordering
  itself. The intervals show that none of these differences, `random_valid` included, excludes zero.
- **Terms to define before manuscript use:** R1-EXAM-X7, C3, A2 (rule layer), A4 (zero-shot forecaster), B1/B2
  (exam stages) and "anchor".
