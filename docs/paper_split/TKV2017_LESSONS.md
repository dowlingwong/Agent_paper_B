> Copied from the source repository at S = 4154f153, 7 October 2026; the whole file is retained (it covers both papers).
> The source copy in agent-checkpoint-intervention is the historical one.

# Tian–Kong–Valiant (2017): implications for Papers A and B

Recorded 2026-09-29. Primary source: Kevin Tian, Weihao Kong and Gregory Valiant,
[Learning Populations of Parameters, NeurIPS 2017](https://proceedings.neurips.cc/paper_files/paper/2017/file/bc4e356fee1972242c8f7eabf4dff517-Paper.pdf).
Read scope: the ten-page proceedings paper, including its theorem statements,
algorithm and empirical sections. The separate supplement was unavailable;
this is not an independent verification of its appendix proofs.
Bibliography key in both manuscripts: `tian2017populations`.

The key source locations are Proposition 1 (pp. 2–3), Theorem 2 (p. 3),
§§2.1–2.2 (pp. 4–5), and Theorem 3/§2.4 (pp. 6–7). Their distribution-recovery
error has a finite-depth component and a sampling component; the latter can
be large at increasing depth. An asymptotic depth rate is not a finite-budget
guarantee.

## Paper A: what to adopt now

The following is our application analysis, not a claim that TKV proves A.

| Mapping | In A | Consequence for our presentation |
|---|---|---|
| Entity | Checkpoint in one declared population cell | State the independent sampling unit explicitly. |
| Repeated trials | Fixed replay depth R | Extra independent checkpoints improve estimation of the same observation law; changing R changes the observation interface. |
| Latent parameters | Replay success probabilities (x,y), in the independent-fork submodel | Cite the close precedent before introducing our compatible latent-law class. |
| Scientific target | Intended-effect interval and sign, with discrepancy allowance p | Keep the target distinct from estimating a representative latent population. |

**已采用：贡献归属与边界。** 正文 related work、有限重复结果的引导段及理论附录均已引用。
有限矩障碍和多参数建模不能充当 A 的独立新颖性主张。A 应解释：给定相同回放观测，
哪些目标干预效应仍然兼容；哪些额外重复能改变符号判断；哪些偏差只能靠外部证据约束。
保留深度四例子作为这种决策差异的具体说明，不把它说成对所有分布都有效的深度阈值。

**下一步最值得借鉴的是组织方式，而非增加一套分布恢复实验。** A 的 A-R1/A-R4
可以共用一个示例，依次呈现已知观测律的识别区间、有限样本的不确定性、N/R 的不同作用，
以及获得外部参考信息的成本。至少区分：采样误差、有限重复留下的兼容分布、回放与目标过程的偏差。
当 p 不变时，更多重复不等于 p 变小。也不能因为某个潜在分布难以恢复，就直接推出一个
线性总体均值难以估计；需要证明困难落在我们真正关心的端点或符号上。

**可以探索，但本次没有实现或证明：** 将同时有效的观测概率/矩置信约束放进 A 的端点优化，
对所有兼容分布求上下界。这需要覆盖率、非空性、网格误差及独立抽样/聚类条件的明确处理。
直接代入一次拟合分布再输出区间，不能宣称覆盖所有兼容世界，更不能自动获得 sharp confidence interval。
优先使用现有保守有限样本界完成可复现示例，再决定是否值得扩展。

**接口不能偷换。** 独立分支时，R 次每臂观测对应矩形矩集合；允许同一对结果相关时，
应在四分类配对律上推导可观测量。不能把只用边际分布的方法当成利用了完整配对信息，
也不能将我们的矩形基底误称为对方多维定理所逐项使用的基底。含有额外任务上下文时，
还需保持上下文与结果的联合观测律，不能直接继承无信息身份模型的 sharpness。

## Paper B: useful design hypotheses, not established results

**1. 区分两种预算。** 离线数据收集决定用算力增加独立 template families，还是增加
已有 root 的重复深度；在线控制决定现在验证、留待第二个 checkpoint，还是从不验证。
这两种预算相关，但不是同一个动作空间。当前 B 的主实验仍是后者，不因新增引用而改变合同。

**2. 可以加入共享信息的估计基线。** 在 development 数据上拟合跨任务的分层/收缩模型，
用来估计与上下文相关的 action/continuation values，再和既有阈值、reserve 与 fitted-Q
策略比较。它可能帮助小样本任务，也可能在异质任务上引入偏差；这是待检验假设。
共享总体分布不能恢复“哪个任务对应哪个价值”，所以需要上下文或历史到价值的预测模型。
所有估计与超参数选择必须保持 family 级拆分，不得从 test descendants 学习先验。

**3. 不将当前 U 强行二项化。** B 的主要结果是最终候选的有界连续准确率 U，多个
测试项也未必独立同分布。可以使用适合有界效用的分层模型；如果另设二元诊断任务，需
明确它是次要分析，不能替换主效用或把二项模型的保证直接移植过来。

**4. 建议的额外诊断（PLANNED，非新主实验要求）。** 在固定总离线成本下改变独立
family 数和每 root 重复数；冻结在线策略预算；报告测试族上的效用增益、决策稳定性、
不确定性和完整成本。固定一条已有树的下采样只能支持其抽样机制允许的结论。
这项诊断应先通过 B 的当前资格/先导门槛，再决定是否加入预先声明的正式实验。

**5. RL/DAC 的连接由我们另行建立。** 可把任务描述作为 context，把历史、当前候选、
可用动作和剩余验证预算作为状态候选，动作是继续或验证。若这些摘要不满足 Markov 性，
应保留完整历史或采用部分可观测表述。TKV 不验证这个状态定义，也不证明 learned timing
优于调好的规则。当前两-checkpoint设计是有界的控制问题；更一般的采集策略和动态算法配置
属于扩展，不能只靠术语升级成为已完成贡献。

## Scope and closure

A-R2's missing citation and nearest-prior comparison are addressed in the active
manuscript. This closes that bounded editorial/attribution item after build
checks; it is not a comprehensive novelty clearance or a new theorem audit.
A-R1 and A-R3–A-R6 remain separate work. B receives a related-work paragraph;
no method, contract, experiment result or performance claim changes.
