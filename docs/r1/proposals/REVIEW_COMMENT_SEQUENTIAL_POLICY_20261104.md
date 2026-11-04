# Review comment: splitting the question into dynamic control, future value, RL and the decision model (received 4 Nov 2026)

**Recorded 4 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted.** This is the comment the author received, verbatim and in Chinese. It is input for a revision, not an adopted plan. Its file links use the `docs/` layout of the Mac working tree; in this repository the same files are under `docs/r1/` (for example `docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`, `docs/r1/TRACK_P_POST_TRAINING.md`), and `r1/c3/env.py` is unchanged.

---

我建议把现行设计改成三个独立但衔接的问题：

1. **动态控制有没有价值？** 在完整 campaign 中，状态依赖策略是否胜过调优后的静态策略？
2. **考虑未来有没有价值？** 在同样的当前信息下，考虑后续预算、提案和 incumbent 变化的策略，是否胜过只优化当前提案的策略？
3. **RL 有没有额外价值？** 在相同状态、动作、训练数据和预算下，多步 RL 是否胜过强动态规则、模型规划和多步监督学习？

这三个问题不能合并。**动态策略可能有用，但一个手工推导的动态阈值就够了；多步价值可能存在，但不一定需要 RL；RL 只有在完整 campaign 中比这些更简单的方案更好，才证明了自己的额外价值。**

我的总体建议是：保留现有 C1/C2/C3 和 Track S 的主体，把 Track S 作为**独立于 C3 单步 gate 的序列性筛查**；然后新增一个受控的“多步策略比较”阶段。不要直接把 Track P 的单步 GRPO 加长、换个名字称为多步 RL。

以下是设计分析和建议，**不是已经通过的计划，也没有改变现有 runbook、STOP 或运行授权**。

---

# 一、先明确：我们到底想证明什么？

我建议把文章中的相关主张分成四级。

| 级别 | 要证明的主张 | 必须看到的证据 |
|---|---|---|
| **L1：动态控制** | 在运行过程中随状态调整决策有收益 | 动态策略胜过经过相同调优资源优化的静态策略 |
| **L2：多步价值** | 当前动作对未来的影响值得纳入决策 | continuation-aware 策略胜过只优化当前收益的强策略；结果在完整 campaign 中成立 |
| **L3：RL 的价值** | 多步 RL 比规则、规划或多步监督学习更好 | 在同一目标、信息、预算和近似匹配训练资源下，RL 稳定胜出 |
| **L4：decision model 的价值** | 理解提案内容的模型优于结构化策略 | 同算法、同数据条件下，decision model 胜过强表格/MLP 模型，或在迁移上显示优势 |

这四级可以分别成立，也可以只成立其中一部分。

例如：

- L1 成立、L2 不明确：动态预算阈值有用，但我们还不能说它通过长期规划获益。
- L2 成立、L3 不成立：未来确实重要，但模型预测控制或 rollout 已经够好。
- L3 成立、L4 不成立：RL 有用，但不需要语言 decision model。
- L4 成立、L3 不成立：理解提案有价值，但 SFT 加规则已足够。

这样写比笼统地问“DAC + RL 有没有用”清晰得多，也使负结果有研究价值。

---

# 二、当前设计为什么还不能回答这些问题？

## 2.1 Track S 回答的是 L1 的一个受限版本

[Track S revision 7.3](/Users/wongdowling/Documents/agent_paper_B/docs/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md) 的主问题是：

> 在指定控制器和环境下，从四个动态阈值成员中选出的策略，是否在最终 campaign 指标上优于调优后的静态阈值？

这个对比是有价值的，因为它比单步离线分数更接近实际部署。

但它有明确限制：

- 动态策略是预先规定的参数化阈值，不是多步 RL；
- 基础控制器 A2-U 是指定模型下的 Bayes-myopic 近似，不是现行部署 C3 的完整实现；
- 只考察有限策略家族；
- `verify` 被关闭；
- 主要节点是两个 CPU MLP 节点；
- 预算被刻意选到较容易绑定；
- 它是一方向筛查：找不到收益，不证明动态性不存在；
- 修订版最终 fixture 中，能按目标校准的正控制只有一类集中式正向 keep-feedback 情形；预算通道和若干其他通道的检测灵敏度并未建立。

所以它可以回答“**这类动态阈值有没有检测到收益**”，不能直接回答“**多步 RL 是否有用**”。

## 2.2 Track P 的主要训练目标仍是单步

现有 [Track P 规格](/Users/wongdowling/Documents/agent_paper_B/docs/TRACK_P_POST_TRAINING.md) 的 belief、action head 和 reasoning arm，主要使用当前提案的审计增量和执行价格。

现有 [离线环境](/Users/wongdowling/Documents/agent_paper_B/r1/c3/env.py) 每步之后终止。它不会模拟：

- 这次 action 之后还有多少预算；
- 哪个 incumbent 留下来；
- proposer 下一次会提出什么；
- 新历史如何影响后续决策。

因此，我们还没有一个能用来训练完整 campaign 策略的多步环境与数据协议。

## 2.3 单步 gate 不能决定序列研究是否值得做

目前 C3 gate 主要问：学习到的提案预测是否比 A2 带来足够的**单步离线价值**。

这与以下问题不同：

> 当前提案本身是否有正收益，与执行它对未来机会的影响相比，哪个更重要？

因此，**C3 gate 失败不能逻辑性地否决 Track S 或序列控制问题**。反过来，Track S 若没有发现动态收益，也不应自动终止所有单步 belief 研究。

这应是设计上的第一处修改：

> **把 C3 单步 gate 与 Track S 序列筛查改成并行、各自有意义的分支。**

这不意味着绕过既有 author gate 或授权。要正式改变执行依赖，仍需要在计划中明确记录为新的作者决策。

---

# 三、先固定完整 campaign 的状态、动作和目标

多步实验开始之前，要先把问题定义清楚。我建议第一版保持小而可审计。

## 3.1 一个 episode 是一个完整 campaign

\[
\text{episode}
=
\text{从初始配置到预算用完或达到提案上限}
\]

最终结果：

\[
Y
=
\text{最终 incumbent 在独立审计种子上的表现}
\]

不同策略在相同任务实例、初始条件、worker run cap 和 LLM-call cap 下比较。

Track S 使用 raw metric 的最终审计值；原总计划部分地方使用相对初始值并按节点归一化。**这些定义不能静默混用。** 我建议：

- **每个节点的主要对比：** 配对的 raw audited \(Y\) 差值；
- **跨节点汇总：** 使用预先定义的归一化指标，明确噪声尺度和实际意义；
- 不把不同单位直接取平均。

## 3.2 状态至少包含什么？

在每次决策时，允许控制器看到：

\[
s_t=
\{
\text{proposal},
\text{incumbent},
\text{history},
\text{remaining resources},
\text{noise information}
\}
\]

具体包括：

- 当前提案的 diff 或结构化参数变化；
- 当前 incumbent 的配置和历史观测；
- 已用及剩余 **worker runs**；
- 已用及剩余 proposer/LLM calls；
- 剩余 proposal slots；
- 最近接受/拒绝情况；
- 之前执行过的配置、重复标记；
- 可用的噪声估计及其来源；
- 如果使用多步模型，必要的预测不确定性和历史摘要。

特别要修正或隔离 Track S 已发现的问题：旧 `budget_frac_left` 是 trial-indexed，不是真正的 worker runs remaining。研究预算决策时，不能把它当真实剩余预算。

**信息原则：** 所有比较臂在同一决策点必须得到相同合法信息；不能让 RL 看完整历史，而简单基线只看到当前提案，再把差异解释为 RL 的优势。

## 3.3 第一版动作空间不要同时放太多东西

建议分两轮：

### 第一轮：E1 的 `execute / skip`

执行后使用所有策略共享的、冻结的 acceptance rule。

这能先隔离：

> 预算分配与当前提案筛选是否需要多步决策？

### 第二轮：增加 E2 的 `keep / reject` 或 `verify`

这是另一个更复杂的问题，因为：

- E2 的可用信息比 E1 多；
- verify 可能需要同时重新运行 candidate 和 incumbent，成本不一定是一次 worker run；
- keep/reject 会改变 incumbent 与 proposer 的未来上下文；
- 当前 harness 的接口未必直接支持所有强制动作，需要额外实现和验证。

**不建议第一版就把 skip、revise、verify、keep、stop、memory switch 全部交给 RL。** 否则即使 RL 有收益，也很难知道来自哪个动作，而且数据覆盖与训练成本会迅速膨胀。

## 3.4 奖励要与最终目的对齐

最干净的第一版多步 reward：

\[
r_t=0 \quad (t<T),
\qquad
r_T=Y_{\text{final}}-Y_{\text{start}}
\]

对一个固定任务实例，减去相同的初始表现只是平移目标，便于解释。

这样做的优点是目标清楚：最大化最终结果。

缺点是 reward 稀疏、方差大。因此可以在训练中比较适当的辅助信号或 reward shaping，但要预先声明：

- shaping 是训练工具；
- 最终评价仍以未修改的 audited terminal \(Y\) 为准；
- 中间奖励不能使用部署时不可见的未来审计结果，除非明确属于训练监督；
- 如果使用 potential-based shaping，必须核对终止状态、折扣和实际实现条件，不能仅凭名称声称最优策略必然不变。

第一版在预算固定的情况下，不建议同时把固定价格 \(g\) 当作主目标中的额外惩罚，否则可能混入“结果好”和“省预算”两个不同目标。执行数量和耗时可以作为成本指标单独报告。

---

# 四、怎样修改 Track S，让它真正检验动态 DAC？

我建议**保留原 Track S 的主对比、筛查规则和已有 preregistration 逻辑**。新增内容作为独立的扩展，不应看完原主结果后临时改主分析。

## 4.1 原 Track S 保留什么？

保留：

- 调优的静态家族 \(m^*\)；
- 四个指定动态阈值成员中选出的 \(\pi^*\)；
- 在 fresh instances 上进行完整 campaign 比较；
- matched-static secondary；
- 一方向结论；
- seed block、placebo、A/A、预算校验、训练/测试隔离；
- S3a 的 fork 和 S4 的反馈机制诊断。

这样可以明确回答：

> 在这类状态依赖阈值中，动态配置是否比调过的静态配置有额外收益？

**不能改写成**“如果 Track S 阴性，就证明不需要多步决策”。

## 4.2 增加一个“强动态非 RL”比较组

Track S 当前的四个动态成员是合理筛查，但对于后续 RL 评价还不够。

建议新增两个类型：

### B1：预算动态规划 / stochastic knapsack baseline

假设未来提案价值服从可估计分布，利用：

- 剩余 worker runs；
- 剩余提案机会；
- 当前提案的预期收益；
- 从训练集估计的未来机会分布；

计算“现在执行”和“保留预算”的机会成本。

它可以简化为：

\[
\text{execute iff }
\widehat V_{\text{current}}
>
\widehat{\text{value of preserving one run}}
\]

第一版可以在离散预算和简化收益分布上做动态规划；这是一个很强的对照，因为它不需要 RL，却直接处理预算序列性。

**解释边界：** 如果未来提案分布会依赖 incumbent 和历史，固定分布 DP 只是模型近似；不能把它称为完整最优策略。

### B2：有限 horizon 的 model-based rollout

用训练集拟合一个简单转移模型：

- 当前执行后 candidate 是否可能被保留；
- 保留或拒绝后 incumbent 如何变化；
- 下一条提案的类别和估计价值如何变化；
- 预算如何变化。

然后针对每个动作向前模拟少数步，再用一个冻结的基线策略完成余下步骤。

它回答的是：

> 即使用一个简单模型显式考虑未来，能否超过纯即时决策？

需要报告模型误差；模拟器本身不能作为最终效果证据。最终仍然要在真实 proposer + worker 的完整闭环上评价。

## 4.3 加入一个真正受控的“未来影响”对比

比较两种策略时，让它们使用**同一份当前 proposal value 模型**：

- **Myopic：** 只用当前 proposal 的即时价值和固定价格。
- **Continuation-aware：** 使用同样的即时估计，再加未来预算和状态变化的估计。

形式上：

\[
\widehat Q_{\text{multi}}(s,a)
=
\widehat r_{\text{immediate}}(s,a)
+
\widehat C_{\text{future}}(s,a)
\]

对照应尽量只改变是否使用 \(\widehat C_{\text{future}}\)。

这比把“一个小模型 SFT”与“另一个大模型 RL”直接比较更有解释力：否则模型大小、信息、调参和训练数据都会混在一起。

但是也不能过度解释：如果 continuation-aware 胜出，说明加入未来信息的这套**完整方法**更好；要单独归因于具体机制，仍需下面的干预和消融。

## 4.4 先改善正控制的覆盖

当前 Track S 最终 fixture 的限制很重要：只有一种较集中的正向 keep-feedback 控制按目标效果校准，预算和若干信息通道的敏感度不明。

扩展前应新增可控模拟环境，分别植入：

1. **预算机会成本：** 当前小收益会消耗未来高收益机会。
2. **信息价值：** 当前执行虽收益一般，但能改善后续决策。
3. **incumbent 交互：** 先接受 A 才能使 B 有价值，或 A 会阻碍 B。
4. **proposer 反馈：** 历史中的接受/拒绝会改变后续提案分布。
5. **严格单步/null：** 动作不影响未来机会，且简单策略已足够。

每个正控制要先用大规模模拟估计真实目标效应，再校准到预先设定的 campaign 级效应大小。不能只观察“RL 在人工环境能赢”，因为这可能只是环境按 RL 的偏好构造。

每个控制至少报告：

- 真实策略差；
- 检测功效与置信区间；
- 选中正确策略的概率；
- RL 和对照的训练失败率；
- 不可校准的通道；
- 多重比较的假阳性率。

**这些只是 pipeline 和灵敏度验证，不是自然 autoresearch 环境的效果证据。**

---

# 五、怎样新增一个真正的多步 RL 实验？

我建议新增一个独立阶段，暂称 **Sequential Policy Track**。它可以借用 Track S 的环境、预算、分支工具和最终审计，但不能把 Track S 的现有主试验悄悄改成 RL 试验。

## 5.1 数据不是“单步标签表”，而是完整 transition

每条记录最少需要：

\[
(s_t,a_t,r_t,s_{t+1},\text{terminated},\text{truncated})
\]

附带：

- campaign ID、instance ID、step index；
- behavior policy 版本；
- 采样 action 的概率或确定性规则；
- worker 与 LLM 预算变化；
- proposal 和 incumbent 的版本/hash；
- 模型、运行环境和随机种子；
- action 后的真实日志和下一个状态；
- 最终独立审计值；
- 对失败、超时、无效输出的处理方式。

要特别区分：

- **terminated：** 任务按协议自然结束；
- **truncated：** 由于外部限制或异常提前截断。

如果把异常中断当作正常结束，会污染 return 和 value target。

## 5.2 不要以为现有 B.1 足够训练离线 RL

现有 B.1 轨迹可以是重要数据来源，但可能有两个问题：

1. **action coverage 不够。** 如果数据几乎都由默认策略产生，就可能缺少同一类状态下的 skip 或不同决策。
2. **state coverage 不够。** 即使给某个状态补一个单步审计，也不知道换动作后会访问哪些后续状态。

对离线 RL 来说，新的策略可能选择数据很少覆盖的动作或状态，导致价值高估。[IQL 原论文](https://arxiv.org/abs/2110.06169)和 [CQL 原论文](https://arxiv.org/abs/2006.04779)都把数据分布与新策略分布之间的偏移视为核心问题；采用这些算法也不能自动消除我们的覆盖缺口。

因此，若要训练离线 RL，需要额外设计**行为策略混合**，例如：

- execute-all；
- 静态阈值；
- 预算动态阈值；
- 受限随机探索；
- 现有学习型单步策略。

所有策略必须在训练实例上采集，并记录 action probability。对于确定性策略，如果某些状态只出现一种动作，就不能仅凭 propensity logging 创造缺失的反事实。

## 5.3 用 Track S 的 fork 补充多步数据

Track S 的 S3a 有一个很好的基础：

- 从相同 root state 分出 skip 和 execute；
- 在部分 fork 上增加 ghost / controller-only；
- 再继续运行后续 campaign；
- 比较最终 \(Y\)。

这可以构建：

\[
\widehat Q^{\pi_b}(s,\text{execute})
-
\widehat Q^{\pi_b}(s,\text{skip})
\]

这里上标 \(\pi_b\) 很重要：它估计的是**当前动作之后，按某个指定 continuation policy 继续时的动作价值差**，不是全局最优 \(Q^*\)。

由于一个状态下多次 rollout 仍可能很吵，应在试点中估计：

- 同一 fork、同一 action 的重复方差；
- 不同 fork 之间的方差；
- proposer seed 与 worker seed 的贡献；
- 强制动作后恢复状态是否一致。

现有 Track S 计划约 **150 个 fork / node**，主要用于描述和归因。是否足以训练 RL 或 continuation model，需要根据 pilot 方差和学习曲线决定，不能直接假设够用。

## 5.4 多步 RL 算法：先从小而透明的模型开始

我建议第一版不要直接从 4B decision model 的多步 GRPO 开始。先用小型状态编码器或 MLP，原因是：

- 动作空间很小；
- 数据大概率有限；
- 更容易检查 Bellman target、动作覆盖和错误；
- 便于与同规模的监督学习模型公平比较；
- 失败时更容易定位是数据、目标还是模型问题。

可以预先选一个主算法、一个备选：

- **主候选：** IQL 或带保守约束的离线 value-learning 方法；
- **备选：** 一个简单、受行为策略约束的 actor-critic / AWR 类策略；
- 算法选择应在训练数据和开发验证上决定，最终测试集不能用于挑选。

必须记录：

- 训练 seed；
- checkpoint 选择规则；
- 每次更新的环境步数和计算量；
- 数据过滤与归一化；
- 违规动作如何处理；
- 最终策略是否发生 unsupported action；
- 训练失败或坍缩的次数。

RL 的训练信号应来自**多步 return 或多步 bootstrap target**。如果只是重新使用每条提案的即时 \(u_j\)，即便调用了 IQL、PPO 或 GRPO，也不能说它解决了多步决策。

## 5.5 是否需要在线 RL？

这是更强、也更贵的一步。

离线 RL 之后，可以设计一个有预算上限的在线 fine-tuning 对照：

- 所有在线交互只发生在训练实例；
- 限定新增 worker runs、LLM calls 和审计预算；
- 对照策略也获得同样数量的环境交互和调参机会；
- 在完全独立的 test instances 上冻结评价；
- 预算达到上限或触发 STOP 就结束。

在线 RL 的优势可能来自**更多真实交互**，也可能来自 RL 算法本身，所以至少要分开报告：

1. 只用原有离线数据；
2. 加同样数量新数据的监督/规划基线；
3. 加同样数量新数据的在线 RL。

这样才能判断是“多了数据”还是“RL 更好地利用数据”。

**这属于新执行阶段，需要新的作者决定和明确授权；不能从现有 Track S 或 Track P 的授权推导出来。**

---

# 六、需要增加哪些强基线？

这是整个设计最重要的部分之一。下面按其回答的问题排列。

## 6.1 控制策略基线

| 基线 | 核心能力 | 为什么必须有 |
|---|---|---|
| **默认规则** | 当前 harness 的标准行为 | 判断新系统相比现状是否有实际价值 |
| **Execute-all / no controller** | 除规则过滤外全部执行 | 检查复杂控制是否真的值得 |
| **随机策略** | 在匹配预算下随机执行 | 最低参照；不能作为唯一对手 |
| **调优静态阈值** | 固定阈值，充分使用训练/开发预算 | Track S 已有；检验动态性的必要基线 |
| **噪声感知 myopic 规则** | 用当前收益分布、噪声和成本 | 是当前 C2/C3 的核心对照 |
| **A2-U 或更强历史统计模型** | 利用历史更新收益分布 | 防止把“用了历史”误说成 RL 优势 |
| **动态预算阈值** | 根据剩余资源调整阈值 | 检验简单动态启发式能否解释收益 |
| **预算 DP / stochastic knapsack** | 显式计算未来机会成本 | 强非 RL 序列基线 |
| **模型预测控制 / rollout** | 使用转移模型和有限步前瞻 | 检验多步价值是否需要 RL |
| **racing / sequential verification** | 对不确定候选追加测量 | 只在开放 verify 的实验中比较 |
| **LLM self-control** | proposer 或独立模型自行判断 | 对应现有论文设计，但调用成本必须计入 |

特别注意：Track S 当前 A2 是近似节点常量，A2-U 是更强的历史模型。**如果 RL 只超过 A2，却输给 A2-U 或动态预算规则，不能说 RL 找到了有价值的序列结构。**

## 6.2 学习方式基线

为了识别“RL 本身”的价值，我建议至少比较：

### 1. 单步 SFT + 规则

现行 C3 主线。相同输入、相同 belief 标签，规则做动作。

### 2. 单步 action head

同一数据上用即时收益训练 execute/skip，作为 contextual-bandit 式学习对照。

### 3. 多步监督 / rollout regression

利用训练 fork 的：

\[
\widehat Q^{\pi_b}(s,\text{execute})
-
\widehat Q^{\pi_b}(s,\text{skip})
\]

直接监督一个模型预测动作价值差，然后选动作。

这是非常重要的强基线：它使用了多步结果，却不需要 Bellman 式 RL。若它与 RL 表现相当，说明多步监督可能已经足够。

### 4. 行为克隆

用相同模型模仿强动态基线，确认 RL 是否真的超出“复制一个已经不错的策略”。

### 5. DAgger 或 on-policy 数据聚合

让监督模型在自己访问的状态上补充标签，并与 RL 在**相同新增交互预算**下比较。

DAgger 本来就是为缓解策略导致的状态分布偏移而提出的；它并不自动优化长期 reward。[DAgger 原论文](https://proceedings.mlr.press/v15/ross11a.html)

### 6. 离线 RL

用相同 transition 数据和多步目标训练。

### 7. 在线 RL

如果预算允许，作为独立的扩展；必须与等交互预算的数据聚合或模型规划对照。

## 6.3 模型架构基线

如果想证明 decision model 有用，而不是只证明某种策略学习有用，还需要：

- 结构化特征 + logistic/线性模型；
- LightGBM 等表格模型；
- 小型 MLP；
- 不使用提案文本、只使用结构化 edit 特征的模型；
- 使用相同文本、但没有专门 decision pretraining 的普通小语言模型；
- decision model 的 belief-only 与 action-only 消融。

最好保持：

- 同一训练/验证实例；
- 同一动作空间；
- 同一数据量；
- 同样的模型选择预算；
- 报告参数规模、训练时间、部署延迟和 LLM token 成本。

否则“decision model 比表格模型好”可能只是因为它看到了更多信息或消耗了更多计算。

## 6.4 上界应如何使用？

可以增加两个仅供诊断的 upper bound：

- **单步 hindsight oracle：** 使用当前 proposal 的审计结果做理想单步选择。
- **小型合成环境的动态规划 oracle：** 在状态空间足够小、转移已知时计算最优策略。

但它们不能部署，不能与真实策略共用未来信息。现实环境中的有限 fork hindsight 也不是全局最优 oracle；只能作为对应分支集和 continuation policy 下的参考。

---

# 七、怎样区分“预算效应”“信息效应”和“proposer 反馈”？

如果 RL 胜出，审稿人自然会问：**为什么胜出？**

我建议用 Track S 的现有分支设计，再加有限的机制干预。

## 7.1 预算效应

**问题：** 策略是不是只是更会保留 worker runs？

设计：

- 相同 proposer、相同 acceptance rule；
- 改变 worker-run cap，保持 LLM-call cap 的定义固定；
- 比较宽松预算和绑定预算；
- 报告预算绑定比例、每步执行率和剩余预算。

预期：

- 如果优势只在预算紧时出现，并可由预算 DP 恢复，很可能主要是预算配置收益；
- 这仍然是 DAC 收益，但不能自动说是复杂 proposer feedback 或 RL 独有收益。

**注意：** 预算水平是实验因素，不能等看见结果后只挑 RL 赢的预算报告。

## 7.2 信息效应

**问题：** 一次执行有没有帮助我们改善后续判断，即使本次不被保留？

可以比较：

- 执行且信息可进入控制器状态；
- 类似 ghost 的执行，但严格控制哪些结果可见；
- 相同预算下的其他控制版本。

这里必须定义好干预，否则“既用了一个 worker run，又改变了历史，又更新了 incumbent”，无法把作用归到信息本身。

## 7.3 Proposer 反馈

**问题：** 当前控制决定是否改变 proposer 后续提出什么？

Track S 的 ghost / controller-only 和 prompt display ablation 可以帮助拆分：

- worker 资源消耗；
- 控制器获得的信息；
- proposer 能看到的历史；
- incumbent 的改变。

但这些是机制实验中的**人工干预臂**，不是部署策略。要验证它们确实只改变预期通道，包括：

- prompt 内容；
- novelty/seen set；
- metric 是否泄漏；
- worker 预算；
- incumbent 与文件恢复；
- 控制器内部状态；
- 后续随机种子的映射。

即使两个分支在 fork 时共用种子，分叉后的 prompt 和状态不同，共同随机数也**不能保证**以后生成相同提案；配对减少方差的效果要实测。

## 7.4 多步交互

Track S 已提出对关键超参数做 factorial 测试。我建议保留，并增加：

- A 单独修改；
- B 单独修改；
- A+B 组合；
- 不同顺序下的完整 campaign。

这样可以测量提案之间是否存在交互。如果任务本身几乎没有 edit–edit interaction，那么寻找复杂的长期策略很可能没有足够 headroom。

**但不应只为了让 RL 看起来有用而人为挑选复杂任务。** 可以预先定义两类：

1. 真实、可复现的简单节点；
2. 真实或明确标为合成的、存在可测交互的困难节点。

分别报告，不混为一个平均分。

---

# 八、完整实验矩阵应该怎样设计？

如果不限制规模，实验矩阵会爆炸。我建议分层。

## 8.1 第一层：便宜的受控验证

**环境：** 合成/fixture。

**目的：**

- 验证实现；
- 校准假阳性；
- 确认每种机制下是否能检测到预定效果；
- 比较模型规划、多步监督、RL 在不同机制下的表现。

**不能得出的结论：** RL 在真实 autoresearch 中有效。

## 8.2 第二层：复用 Track S 的 CPU 环境

先使用 Track S 指定节点与其约束：

- 绑定预算；
- 相同 proposer；
- `vary` split；
- verify off；
- 最终 K=5 鲜种子审计；
- 完整 campaign 为评价单位。

建议第一版主表只放少数策略：

| 组 | 策略 |
|---|---|
| B0 | 默认 / execute-all |
| B1 | 调优静态阈值 |
| B2 | 强动态预算规则或 DP |
| B3 | 单步 SFT + 规则 |
| B4 | 多步 rollout regression |
| B5 | 多步 RL |

Track S 原有 \(\pi^*\) 和 \(m^*\) 主对比应保持原定义。新增组需要自己的开发集、调参计划和独立 test，而不能在读完 S3e 后拿同一数据继续选模型。

## 8.3 第三层：更难任务和迁移

CPU 节点可以告诉我们系统是否可运行，但不能单独证明跨环境价值。

下一层至少要有：

- 一个具有不同任务结构或编辑空间的真实节点；
- 一个更强或不同的 proposer；
- 一个预先保留的跨节点或跨 benchmark 测试；
- 成本可承受的独立审计。

如果现有 MLGym / autoresearch adapter 尚未准备好，就应该先把它们列为**待完成的环境准备与验收**，不能在方案里直接算作已有迁移证据。

更难任务也不意味着必须马上全量 GPU 审计。可以先：

1. 测量单次 worker 成本和噪声；
2. 验证动作是否实际触发；
3. 估计多步效果可检测性；
4. 再决定正式比较规模。

这只是建议流程，不是启动资源的授权。

---

# 九、统计设计怎样做才可信？

## 9.1 真正的独立样本单位是 campaign instance

同一 campaign 中有 20 或 40 条提案，不等于 20 或 40 个独立实验单位。

最终策略比较的单位应是独立的：

\[
i=(\text{task node, instance seed, initial configuration, …})
\]

在同一个 instance 上运行多个策略，形成配对差：

\[
D_i
=
Y_i(\pi_{\mathrm{RL}})
-
Y_i(\pi_{\mathrm{baseline}})
\]

再按 instance 聚合和推断。多个训练 seed、多个 proposer repetition 或多个 audit seed 需要明确嵌套，不能都当成互相独立的 campaign。

## 9.2 训练、开发、测试要彻底隔离

至少分：

- **训练实例：** 收集轨迹、fork、训练 SFT/RL；
- **开发实例：** 调阈值、选超参数、checkpoint 和模型；
- **最终测试实例：** 只运行冻结策略并做预定分析；
- **最终审计种子：** 不用于模型训练与选择。

如果同一 edit 模板或初始配置跨集合高度重复，还要检查更高层次泄漏：仅仅把 instance seed 分开不一定足够。

已有的 7001–7005 / 7006–7010 规则必须保留在其原有数据用途上；新增多步轨迹需要**另行冻结清楚的 instance、worker、proposer、fork 与 audit seed block**，不能随意复用旧评价块当训练数据。

## 9.3 明确主要比较与多重比较

我建议预先指定两个核心比较：

1. **动态价值：** 最强预先指定动态非 RL 策略 vs 调优静态策略。
2. **RL 额外价值：** 多步 RL vs 最强预先指定非 RL 多步基线。

“最强”不能通过查看测试集后决定。可在开发集依据固定规则选一个，或者预先指定多个比较并进行多重性控制。

如果同时在多个节点和多个 baseline 上检验，要预先声明：

- 主要 endpoint；
- 单侧或双侧检验；
- 多重比较方法；
- 实际意义阈值；
- 失败和缺失数据处理；
- 如何报告节点间异质性。

Track S 的 Holm 规则与 one-way screen 应保留在其原试验中。新增 RL 比较不应偷用 Track S 原有的假阳性预算。

## 9.4 样本量不能直接照搬 Track S 的 300

Track S 计划的 \(n=300\) 是为它自己的策略选择、节点、噪声和 one-way screen 设计的。RL vs rollout-regression 的配对方差、策略不稳定性、训练 seed 差异可能完全不同。

因此新增实验要先用**不进入最终测试的 pilot**估计：

- 策略间 campaign 差值的方差；
- 训练 seed 之间的差异；
- proposer 重复波动；
- audit 噪声；
- 策略选择造成的 winner’s curse；
- 预算与节点的异质性。

然后通过包含“训练、调参、选择、最终测试”的完整模拟，估计实际功效，而不只是套一个固定策略的公式。

如果预算不足以识别某个实际有意义的差距，应预先把它定位为探索性结果，而不是完成后解释成“没有收益”。

## 9.5 模型训练随机性要进入结论

如果只训练一个 RL seed，结果可能来自幸运初始化或数据顺序。建议在成本允许时：

- 对 RL、SFT、rollout regression 使用多个独立训练 seed；
- 每个 seed 的训练预算相同；
- 预先规定是评价平均策略、随机训练结果，还是通过开发集选一个 checkpoint；
- 避免只报告最好 seed。

这不是要求在每个 instance 上跑所有组合；具体设计可以用分层或嵌套分析控制成本，但训练波动必须可见。

---

# 十、资源预算和现实可行性

Track S 的 runbook 对每个节点给出的历史计划上限约为 **79k LLM calls**，其中已经包括调参、fork、campaign 和部分 secondary；具体 wall time 取决于实际 latency、并发和 CPU 开销。这个数是**当时的规划估计，不是当前实时资源承诺或可用性**。

新增 RL 实验可能比 Track S 更贵，主要不是训练 MLP 的 GPU 时间，而是：

1. 收集不同策略的完整 campaign；
2. 在相同状态 fork 并继续多条分支；
3. 重复 proposer 以估计分支噪声；
4. 对每个最终 incumbent 做独立审计；
5. 每个基线都需要公平的开发和调参预算；
6. 一旦允许在线 RL，还会有额外交互成本。

一个粗略计费式是：

\[
\text{总成本}
=
\text{训练轨迹}
+
\text{fork continuations}
+
\text{基线调参}
+
\text{测试 campaign}
+
\text{独立审计}
\]

建议把成本分别记录为：

- worker runs；
- proposer calls 和 tokens；
- audit runs；
- controller inference time；
- 训练 GPU/CPU 时间；
- wall time；
- 如果涉及商业 API，实际费用和模型版本。

然后至少报告两种比较：

1. **同部署预算：** 看上线后每个 campaign 的收益。
2. **包含训练与开发成本：** 看需要多少次部署才能摊回策略开发开销。

如果 RL 只在部署阶段多赢一点，却消耗极多训练与审计资源，也应该如实报告。

---

# 十一、主要风险与对应的解决办法

| 风险 | 后果 | 对策 |
|---|---|---|
| **状态/action 覆盖不足** | 离线 RL 对未见动作高估 | 混合行为策略、记录概率、测支持度；必要时限制策略偏离 |
| **训练/测试泄漏** | 分数虚高 | 实例、edit、seed、fork 和审计块分离并做机械检查 |
| **动态收益来自简单预算规则** | RL 的额外贡献不存在 | 加 DP、动态阈值和 rollout 强基线 |
| **调参机会不平等** | 最复杂策略靠更多搜索赢 | 预先分配数据、交互、算力和调参预算；同时报告成本 |
| **proposer 不可重复** | 配对与 fork 结果方差过大 | A/A、exact placebo、重复和 seed 记录；失败则 STOP 或修订协议 |
| **恢复/分支不一致** | 因果比较无效 | 文件、ledger、novelty set、预算、控制状态的 arm-invariance 检查 |
| **审计噪声与 winner’s curse** | 最终结果被选中噪声抬高 | 独立鲜种子最终审计；不把 in-run best 当真值 |
| **任务太简单** | 检测不到多步 headroom | 先测交互与预算绑定；加入预定义的困难环境 |
| **任务太贵或信号太小** | 大量计算后仍无判断力 | 先用 pilot 方差与正控制做功效/成本分析 |
| **RL reward 与论文目标不一致** | 离线分数提升但最终结果不提升 | 以 terminal audited \(Y\) 为主，shaping 单列 |
| **多种机制同时变化** | 无法解释收益来源 | 分阶段开放动作，使用 Track S 机制干预 |
| **合成 simulator 偏差** | 模拟器里成功，真实闭环失败 | simulator 只用于训练/诊断，结论以真实闭环 fresh test 为准 |

还有一个已有的具体工程风险：[Track S 的 cache 诊断](/Users/wongdowling/Documents/agent_paper_B/docs/proposals/TRACKS_NOCACHE_20261030.md)记录过相同 prompt 和 seed 的输出身份问题。禁用 prompt cache 的一次诊断取得了 100% 身份率，但原始失败原因并未完全建立，仍需按正式协议重新做完整检查。我们不能假设“seed 相同”本身就保证分支可复现。

---

# 十二、我推荐的实际修改顺序

## 第一步：修订文章问题与 gate 关系

在计划中明确写：

- C3：学习当前 proposal 的收益分布；
- Track S：动态阈值与静态阈值的 campaign 级筛查；
- 新多步 track：多步监督、规划和 RL 的比较；
- C3 失败不自动否决 Track S；
- Track S 阴性不证明全体动态策略无效；
- Track S 阳性不自动证明 RL 有价值；
- DAgger 的分布变化不是多步价值的充分证据。

这是最便宜、也最重要的概念修订。

## 第二步：先做状态、动作和数据契约

在动训练代码前，冻结：

- episode 边界；
- 完整状态；
- E1/E2 动作；
- 预算账本；
- transition 格式；
- 最终指标；
- 数据隔离；
- fork 复现；
- 各模型可见信息。

同时处理旧 bin-action 环境与 Track P 新 belief/action 接口的不一致。

## 第三步：完成 Track S 原有筛查与机制诊断

按已经批准的版本和 gate 执行；若要改动设计，应先完成新的预声明和作者决定。不要把已有证据阶段的结果拿来事后重新设计主假设。

## 第四步：加入强非 RL 多步基线

优先顺序：

1. 动态预算阈值；
2. 预算 DP；
3. fork rollout regression；
4. 简单 model-based rollout。

如果这些方法已经解释并获得大部分动态收益，RL 研究问题就变得更尖锐：**RL 是否还在这些强对照之上提供增益？**

## 第五步：仅在数据覆盖和成本可行后训练多步 RL

先用小 MLP 和有限 action space。训练目标是 campaign return，多 seed，做严格离线数据检查，再在独立 campaign 上评价。

如果支持度不够，不应该靠更复杂的离线算法掩盖，而应该把结果标为“数据不足以可靠训练或评价该策略”。

## 第六步：最后才测试大 decision model 的多步 RL

只有当：

- 多步结构有足够 headroom；
- 强非 RL 基线已建立；
- transition 数据合格；
- 小模型结果有解释性；
- 任务与预算确实需要提案文本理解；

才值得测试 LoRA decision model 的多步 RL。

否则我们会同时改变表示、算法和数据，既昂贵，又难解释结果。

---

# 最后给你的判断

**最有价值的修改，不是把现有 GRPO 变成更长的 GRPO，而是把研究问题拆成“动态有没有用—未来有没有用—RL 有没有额外用—decision model 有没有额外用”。**

我会保留现有 C3 作为单步噪声决策主线，保留 Track S 作为独立的动态筛查，再新增以完整 campaign return 为目标的多步比较。最关键的新对手是：**调优静态规则、动态预算规则/DP、模型 rollout、多步监督学习、DAgger 和小型离线 RL**。只有 RL 在这些对手及公平预算下仍改善独立审计的最终结果，文章才有依据把“多步 RL 的价值”作为实证结论。