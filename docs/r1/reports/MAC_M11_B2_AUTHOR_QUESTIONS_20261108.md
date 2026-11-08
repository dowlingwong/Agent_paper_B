# Author decisions still open: M11 D8 and B2 — 8 November 2026

**Decision briefing only; no author answer, phase approval, or data analysis. Do not ask or record a decision from this document without the author's actual reply.** Sources: `PLAN.md` §10 R1-BX-D8 and R1-BX-PROPOSED-CONFIRM; R1-B7-PARTIAL-T1; R1-MAIN-PROPOSER (a); `docs/r1/reviews/MAC_B2_VERIFIED_RANKING_REVIEW_20261107.md`; local synthetic proposals `M11_D8_POINT_STATISTICS_20261108.md` and `M11_D8_INFERENCE_PRIMITIVES_20261108.md`. The latter provide bounded building blocks, not accepted full gate code or analysis. Present these questions after the independent review and when the author is available; do not interrupt the current B1 operation.

The author has already chosen: node-stratified 2,000 instance resamples with a fixed seed; IQM across nodes for gap closed; PoI per node with ties 1/2 then averaged over nodes; dev-denominator-below-δ nodes excluded from IQM but retained in PoI; two arms A3/A5, Holm family-wise one-sided α=0.05, lower IQM > 0 and lower PoI > 0.5, and practical size 0.1; T0/T1 pooled with tier recorded as a stratum. Partial T1 is adopted with node count disclosure and at least one labelled T1 node per suite, else STOP. The separate R1-BX-D8-CONFIRM code SHA row, preregistration and all analysis gates remain necessary. These decisions must not be presented as open.

## 1. M11 finite-node IQM convention

**Context.** The adopted IQM does not itself specify how to treat quarter boundaries when the number of eligible nodes is not a multiple of four. Two accepted synthetic primitives implement the empirical quantile integral using fractional boundary weights; no real labels were read.

**Options.** (A) Use the empirical 25%–75% trimmed mean with fractional boundary observation weights. (B) Use a different predeclared finite-sample rule, explicitly specified before analysis.

**Recommendation.** A: it has no discontinuous rounding of a node into or out of the retained middle half. The final gate and small-node behavior still need independent statistical review; this is a recommendation, not an author ruling.

**Paste-ready answer:** `R1-D8-IQM-CONVENTION: 采用经验分位数 25%–75% 的截尾均值，边界节点按分数权重计入；实际 gate 仍须预注册、独立审查并由我另行确认 SHA。`

## 2. M11 seed, paired draws and confidence-bound convention

**Context.** D8 fixes 2,000 within-node resamples and says the seed is fixed, but the numeric seed, reproducible generator/version, finite-sample quantile convention and treatment of paired observations are not specified in the cited decisions. These choices affect reproducibility; choosing them now would not itself authorize the gate.

**Options.** (A) Set one numeric seed and record it, RNG algorithm/library version and stable node/instance ordering; use the same within-node draw for A2, oracle, A3 and A5 paired quantities, and use an explicitly specified one-sided percentile lower bound with predeclared finite-sample quantile convention. (B) Choose another fully specified reproducible interval method after a statistician's review.

**Recommendation.** A as a candidate for statistical review: seed `20261108`, NumPy `Generator(PCG64)` with pinned NumPy version, paired within-node draws and the linear empirical percentile convention. The exact 97.5%/95% one-sided levels follow the adopted Holm plan. Predeclare these details before seeing sweep-2 labels and do not treat the synthetic code's `random.Random(1234)` test seed as an author choice. Review finite-sample behavior and how ties affect the test before committing the gate.

**Paste-ready answer:** `R1-D8-BOOTSTRAP-CONVENTION: 候选采用 seed 20261108、NumPy Generator(PCG64) 并固定版本及节点/实例顺序；同节点配对量共享抽样，2,000 次，单侧 percentile 下界使用 linear 分位数；先完成统计独立审查与预注册，再由我确认 gate SHA。`

## 3. M11 undefined resampled oracle gap and two-arm joint inference

**Context.** The already chosen dev-split δ exclusion does not say what to do if a resampled test denominator is zero or negative. D8 also requires both IQM and PoI lower bounds to pass for each arm and Holm across A3/A5, but does not specify the composite test or how the first-ranked arm is chosen from the two component outcomes. Silently discarding problematic resamples or selecting the more favorable criterion could change inference.

**Options.** (A) STOP and report if any required resample has a nonpositive denominator; do not drop resamples or nodes. For the joint two-arm test, obtain an independently reviewed predeclared procedure specifying composite per-arm evidence, arm ordering, the 97.5%/95% bounds and strict comparisons. (B) Adopt another fully specified treatment and joint inference procedure after statistical review.

**Recommendation.** A until a statistician has reviewed an executable proposal; STOP is conservative and preserves the decided dev exclusion, but may leave the gate unreadable if a single resample crosses zero. The exact two-arm procedure should be made concrete and reviewed before asking for its final approval; ordinary Holm arithmetic on two supplied p-values alone does not resolve the joint test.

**Paste-ready answer:** `R1-D8-BOOTSTRAP-ORACLE: 任一所需重采样的 oracle−A2 分母非正时 STOP 并报告，不自动丢弃样本或节点；A3/A5 双指标联合检验和排序先形成具体方案，独立统计审查后再由我决定。`

## 4. B2 instance count, power plan and authorization note

**Context.** B1 is running, so complete verified B1 analysis and its finalist list/digest are not yet available. R1-MAIN-PROPOSER fixes the v2 B2 thinking-off finalist rule and Y ranking, but the actual B2 instances-per-node and power plan are not fixed by the accepted synthetic verifier. An author B2 note must bind the final reviewed rule, config, nodes, exact count, finalized B1 analysis and any other required phase inputs. The note format in the synthetic verifier is a proposal, not your signature. B2 remains STOP; this question does not authorize it.

**Options.** (A) Wait for accepted B1 analysis, then review a predeclared power/cost plan with its assumptions, design, effect size, uncertainty, α/power target, instance count and resource envelope, and sign the exact note after independent runner/observer review. (B) Specify those inputs now, without inferring them from partial B1 outcomes.

**Recommendation.** A: B1 is incomplete, and a numerical count without an explicit power target, effect-size rationale and resource projection would be an unsupported selection. Power calculations based on B1 must disclose selection and uncertainty; evaluate whether a selection-adjusted or conservative assumption is needed. No additional B1 experiment follows from this recommendation.

**Paste-ready answer:** `R1-EXAM-B2-POWER: 等 B1 完成并独立验收后，请给我预先写明假设、目标效应、功效、实例数和成本的方案；我再决定 B2 数量并签署绑定完整输入的 B2 note。`

A separate open issue is the B2 receiving/provenance process: the accepted synthetic verifier has a disclosed clean-HEAD/cooperative process boundary and is not an independently authenticated prior receipt. Bring a concrete, reviewed receiving proposal to the author if a stronger rule or format is needed; do not declare its trust model decided. None of these options authorizes B2, sweep-2 analysis, X.7 or another host action.
