# Chat session's recommendations to the author (4 Nov 2026, 11:21), as sent (Chinese, condensed only in layout)

A1 Handover 行（Mac packet (a)）：提交；同时指定 Mac agent 为 r1/exam/ 和 r1/c3/train/ 的唯一编辑者；旧 agent 的长期恢复授权不继承，O0 后由作者书面重新授予 operator，带范围。
A2 operator 移植代码例外（R1-BX-REVISIONS (h)）：确认；只限新节点资产（数据准备、fixed-step 包装、metric parser、NodeSpec、预声明的 3–5 个代表性 edit），ops-trackg-* 分支，逐个独立 review；harness 核心、label 代码、gate 仍归 Mac。
A3 Ada 用于 Track G census：明确允许 G.0/G.1b census 与噪声底，可续跑单元；Paper A 有 campaign 等卡时不启动 Paper B GPU 任务。
A4 1GC-7RC 仓库：operator 在 G.0 第一天查；若仍未公开，用 MLAgentBench 作第三个 suite，不按论文自建；1GC 的公开数据集可以作为额外任务，但不算 suite。
A5 Apptainer 检查主机：跑 hostname；若是 deepthought 再查 deepthought2；优先原生移植。
A6 R1-BX 行里的 (proposed)：写一行 R1-BX-PROPOSED-CONFIRM 逐项确认；建议值见 D 节。
B1 常开思考模型：B1 跳过（always_on_in_b1: skip），附录用 Stage A 报告；进 YAML 后再算 sha。
B2 R1-EXAM-RULE-X5V2：M2 通过后作者提交带 sha 的行。
B3 B1/B2 harness pin 直接用 a3fedbb（packet d′）：确认；B1 不等 sweep-1 B.2。
C1 e1 环境重放授权、e2 B.2 启动裁定：M3 的 gate 表和 replay driver 一通过 review 就授权 e1（ENGINEERING_ONLY，deepthought CPU 1–2 h）；重放零差异后再给 e2。
D1 R1-BX-D8-CONFIRM：接受提议值（gap closed 对 noisy-oracle ceiling；分母 < δ_n 不进 IQM 但留在 PoI；A3 或 A5 对 A2 Holm、family-wise 单侧 α=0.05；IQM 下界 > 0 且 PoI 下界 > 0.5；实际意义阈值 0.1）；等 M11 出 gate 代码 sha 再提交。
D2 T0+T1 合并进一个 gate，tier 为分层变量。
D3 K=6 只用于 T1；T0 保持 10；检查只用标签种子 7001–7005，不开 7006–7010 例外，放弃 gate 稳定性项；不过则保持 K=10。
E1 T1 标签跑在 Ada；proposer 在 deepthought 双 TITAN（若 O5 通过）否则一台 4090；T0 与 T1 不强制共用 proposer 主机，同一 tier 内一种服务配置。
E2 DTQ 通过标准：全层 offload 到两卡；cache_prompt:false 下同服务器一致率 1.000；sweep-2 T0 预测 ≤ 4 天。
E3 schema 名 manager_proposal/v2-diff；pick diff liveness 不过：STOP，作者决定降级单参数或移到 T2，不悄悄丢节点。
E4 census 种子 8001–8010；两种 memory 模式；约 12 campaign；K=6 时 7001–7003 / 7006–7008。
E5 发散：定义 loss 非有限或到固定步数无 metric；belief 不进任何 bin，单列计数；action target u = −g；部分种子发散用其余种子算 μ 并标 partial，超过一半算整体发散；重尾用 Student-t，建标签前声明。
F1 fixed-r：r=3、单侧 Welch、α=0.05、复跑计入预算；A0 若就是 Karpathy default 则改名。
F2 TabPFN 嵌入：小型开源句向量（bge-small 级），pin revision+sha，TASL-7 上跑；PCA 16 维只在训练集拟合；Kev 端同样特征序列化为文本，不给自由 proposal 原文。
F3 API proposer：与主 proposer 不同家族的商用中档模型，不用 DeepSeek；先批 €100–200 成本上限，按 G.4 实测调整；只从授权 note 指定主机调用并记录完整请求与模型版本；只用于闭环评估。
G1 P.3a OOM：选项 3（去掉描述性 2k/8k 探针），保留 attempt 1。
G2 P.3a 序列化顺序：M13 查清；保留结果并标模板版本；E6 A6 量化，|ΔRPS| ≤ 0.01 不重跑。
G3 S0.1 重跑程序：新服务器、k=2 先串行后并发、cache_prompt:false、输出后缀；采纳 clause (b)（k=1 digits 21.9 h vs k=2 31.8 h）；rev 3.4/3.5 不作记录版本；安装 Track P marker helper。
G4 Track S GPU 节点 manager：用主 proposer；CPU 节点继续 7B，论文写明；等 G.0/D28 结果后提交行。
G5 Track S 过 15 Dec 继续，但不在关键路径。
H1 B.7 ≈ 8 Dec：保持目标，G.4 后 Mac 重算报作者；降级方案：若 8 Dec 前只有部分 T1 节点有标签，B.7 用 T0+已有 T1 节点读并披露节点数；建议作者提前写进 D8-CONFIRM。

Gaps flagged in the work table (author asked to fill them): Phase C (C.1 A6, C.2 DAgger on 1–2 T1 nodes, C.3 online pilot), C.4 DI test and debiased-memory A/B, D.1 leave-one-suite-out transfer and D.2 pre-declaration, and B.4's pick row — present in the canonical RUNBOOK but with no phase/owner in the two execution runbooks; also B.3 only indirectly covered on the Mac side.

Author's reply (4 Nov 11:29): "1. 1GC-7RC 仓库是什么仓库，不要说黑话 2. apptainer在deepthought2 3. T1是什么，为什么这么久 4. 其他决定按照你的建议来 5. 标 ⚠ 的缺口，你现在补"
