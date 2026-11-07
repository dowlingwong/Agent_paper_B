**B1 未启动。**

# 7 November 2026 上午报告（补写）

**09:31 CET 后更新：** 作者已回答 note 顺序“允许此顺序”，并对不删除规则回答“继续严格禁止，先修复”；两条原文及问题范围已独立审查并记录在 PLAN §10（`R1-EXAM-B1-NOTE-ORDER-07NOV`、`R1-EXAM-B1-NO-DELETION-07NOV`）。因此下文关于 note 顺序“需作者澄清”的表述是答复前快照，不再是当前待决事项。只有其他前提准备好后才能提交 `approved:true` 候选；真实 gate、精确 HEAD 审查、主机 preflight、handover 和其他 STOP 未豁免。现仍未创建批准 note，B1 未启动。当前问题清单已标记这两题为已答。

**09:36–09:37 CET 后续：** 作者就 TASL-7 归属问题答复“你继续执行，不用管他。只要能跑就去跑”，已原文记录并独立审查（PLAN §10 `R1-TASL7-AGENT-OCCUPANCY-07NOV`）。继续工作不意味着可抢占任务、修改他人工作或忽略其他 B1 门槛。09:37 的重新只读 census 观察到指定 GPU 236/24564 MiB、0% 利用率且 compute-app 列表为空；这是瞬时观察，不是持有 lease 的证明。此次 census 的完整本地记录 SHA `018fe4fc81bf24495b2834bcfbe8102652b11e29005201e7fa6b8a9c13e87475`，详见 B1 分支 `TASL7_READONLY_REFRESH_20261107_0937.md`；该 census 已由 `TASL7_READONLY_REFRESH_REVIEW_20261107_0937.md` 限定范围独立接受，并推送至 `mac-b1-20261107` 的 `3cf08a17`；完整原始输出因含其他用户进程参数而保留在本机。

**09:42 CET 后续：** 按作者指示做了第五次 TASL-7 只读 SSH：实际 work 路径显示 ext4、Linux 6.8 和 cgroup v2 控制器可见；两份 Stage A 表及 `llama-server` 的 SHA-256 均与配置一致。GPU 快照仍为指定 UUID、236/24564 MiB、0% 利用率且 compute-app 列表为空。它没有取得 lease 或验证 cgroup 委派、freezer、`kcmp`、Python binding 与实时文件稳定性。完整本地 capture SHA `1d6ff1ffa3652eba65ecadd5cdb152076e852ee04cd41ac1e46935170e9632ad`；报告和独立审查在 `mac-b1-20261107` 的 `2a3ef82e`。无意启动或停止任何远程工作，工具副作用与并发变化未独立监测。

09:21 报告后续：DRYRUN 入口临时根修复、独立 launcher 临时根修复及旧 launcher 禁止自动重跑，分别经限定范围审查并推送到 `mac-b1-direct-worker-20261107`（`9c354de3`）及仍未接受的 `mac-b1-combined-20261107`（`2b7e261e`）。这不恢复 Stage A→B1 kill/resume 覆盖，也不证明 launcher、pytest 或整个测试套件符合不删除规则。该次更新时 B1 分支为 `f6146de4`。下文各提交和状态是补写报告时的快照。

会话中断后于 09:21 CET 恢复，本报告晚于原定 08:30；未在中断期间监控或操作主机。§0.3 的测试、最终 checkout、TASL-7 检查、真实 author gate、dry run 和 handover 均未完成。尤其是 §0.3 字面上要求先满足含已批准 note 的最终 HEAD 和真实 gate，才能将 note 设为 `approved: true`，形成顺序循环；需作者明确顺序后才能建立该候选。即使澄清后，其他阻塞仍须逐项解除。当前授权草稿为 `approved: false`，没有创建实际批准 note。

## Q2 固定参考

按作者 7 Nov 固定规则读取 54 个冻结 sweep-1 proposal 事件账本，10,000 次分层重采样、seed `20261107`，99% predictive interval 为 **[0.42386590667728663, 0.5800007633587785]**；未使用 fallback。参考 JSON SHA-256 `84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd`；B1 分支的 `B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json`、`B1_ANCHOR_DUPLICATE_REFERENCE_REPORT_20261107.md` 及 `B1_ANCHOR_DUPLICATE_REFERENCE_REVIEW_20261107.md` 记录计算与独立审查。后来的安全 guard 不改变该区间或重复率定义；历史账本能否满足相同 guard、条件完成批次的实际覆盖率不可核查，见 `B1_GUARD_HISTORICAL_LEDGER_SCOPE_20261107.md` 和 `B1_PROPOSAL_GUARD_SCIENTIFIC_REVIEW_20261107.md`。

## 已接受与已推送的限定单元

各项接受范围以对应独立审查为准，不表示 B1 或后续阶段可运行。

| 单元 | 分支与提交 | 审查和限制 |
|---|---|---|
| B1 Q2、授权与配置绑定 | `mac-b1-20261107`，截至 `8ffe7611`；Q2 复核 `2c69f20`，配置/registry `3e712c40`，worker 输入 `811520bc`、工作目录边界 `dbaa964c`，pin `f43c6f4f` | `B1_ANCHOR_DUPLICATE_REFERENCE_REVIEW_20261107.md`、`B1_COMMITTED_CONFIG_AUTHORITY_R2_REVIEW_20261107.md`、`B1_WORKER_INPUT_AUTHORITY_REVIEW_20261107.md`、`B1_WORKER_OUTPUT_BOUNDARY_REVIEW_20261107.md`。实际父进程、lease、server、目录归属及最终 HEAD 仍未证明。 |
| B1 执行前提议一致性 guard | `mac-b1-20261107`，`119e16ec` | `B1_PROPOSAL_GUARD_R2_REVIEW_20261107.md`、`B1_PROPOSAL_GUARD_SCIENTIFIC_REVIEW_20261107.md`；guard STOP 时批次不完整，不能重跑、丢弃或改 Q2。 |
| B1 audit 保留、错误报告和部分测试夹具 | `mac-b1-20261107`，`5f8b8f93`、`18cd64f1`、`bcded1c5`、`2e401188`、`a89873fc` | 分别见 `B1_AUDIT_PRESERVATION_R2_REVIEW_20261107.md`、`B1_STOP_REPORTING_R2_REVIEW_20261107.md`、`B1_MAC_SUITE_FIXTURE_*REVIEW*`；并不证明完整 suite、STOP 状态或所有清理已安全。 |
| Stage A DRYRUN 日志期望 | `mac-b1-20261107`，`e7d4e806` | `B1_STAGEA_JOURNAL_EXPECTATION_REVIEW_20261107.md`；只修非生成请求期望，未恢复完整 kill/resume。 |
| B2 ranking / received-grid verifier | `mac-b2-ranking-20261107`，`5477427`，审查记录 `cfb0779` | `MAC_B2_VERIFIED_RANKING_REVIEW_20261107.md` 限于代码和合成 fixture；B2 runner、observer、计划与授权未完成，B2 未获授权。 |
| M3 pidfd 有界等待 | `mac-m3-pidfd-wait-20261107`，`af20df0`，审查记录 `4ad0b6e` | `MAC_M3_PIDFD_WAIT_REVIEW_20261107.md`；完整 Linux supervisor、16 cases、离线 replay 和现场资格仍 STOP。另一个 SIGCHLD 候选未接受，保存在 `mac-m3-sigchld-20261107`。 |
| M11 | `mac-int-20261107`，旧 D18 verdict `06a8f5d`，部分 T1 决策绑定 `f0274ef`，审查 `7bb6061`；当前 `bf523e1` | `M11_D8_LEGACY_VERDICT_REVIEW_20261107.md`、`M11_D8_PARTIAL_T1_BINDING_REVIEW_20261107.md`；完整 D8 gate、统计推断、受保护 reader 和作者确认仍 STOP。 |
| M10 | `mac-int-20261107` 的 `eb26e4b` 为已审查 HK6 状态；`mac-m10-hk6-20261107` 的 `971f4b9` 为独立未接线的 GPU selector | `MAC_M10_HK6_CHECKPOINT_REVIEW_20261107.md`、`MAC_M10_J3_VISIBLE_GPUS_R2_REVIEW_20261107.md`；HK6 EVIDENCE 仍拒绝，真实提交开关关闭，未访问 HoreKa。 |

## 主机动作与 GPU

截至 09:21 的原报告记录三次 TASL-7 只读 SSH；09:37 的第四次见上方更新。原先的三次为：两次 00:00:32/00:00:55 UTC 的 census 和一次 00:15:05 UTC watcher 检查；命令、原始输出、时间与 SHA 分别在 B1 分支 `TASL7_READONLY_CENSUS_20261107.md`、`TASL7_WATCHER_READONLY_20261107.md`，独立审查为 `NOV7_AUTHORITY_CENSUS_REVIEW_20261107.md`、`TASL7_WATCHER_READONLY_REVIEW_20261107.md`。首次快照见 GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`、236/24564 MiB、无列出的 compute app；快照同时看到 `trks_watch` 与其他用户 agent 进程，**不能据此证明主机无人持有**。没有启动 GPU 服务、模型或实验，没有创建 Track X marker、停止其他人任务或更改远程数据；没有登录 HoreKa、TASL-2 或 deepthought。

## 仍未解除的阻塞

| 阻塞 | 解除条件、责任人和工作量 |
|---|---|
| §0.3 note 顺序循环 | 作者明确允许先将 note 作为候选提交、再审查同一 HEAD 并执行真实 gate，或指定其他顺序；随后实现者与独立审查员核对。作者一条答复，加上后续 checkout/host 验证；其他阻塞不会因此自动关闭。见 `B1_AUTHORIZATION_ORDER_REVIEW_20261107.md` 和问题清单。 |
| 禁止删除与现有 B1/test 行为 | 固定 harness `a3fedbb` 的 pending guard 尝试 unlink、失败后截断；测试和子进程也有删除、pytest 有 `current` 链接清理。实现者与独立审查员需完成兼容性修复并证明实际进程树；若须更改固定 pin 或规则，作者先决定。工程和现场时间未知。见 `B1_PENDING_GUARD_PRESERVATION_20261107.md`、`MAC_FULL_SUITE_NO_DELETION_AUDIT_20261107.md`、`B1_PYTEST_PRESERVATION_STATIC_20261107.md`。 |
| STOP、状态发布和 lease | `mac-b1-combined-20261107` 当前 `fbc8baf5` 是**未接受候选**；直接 worker 绑定与正常快照保留有分别限定的审查，但整体 STOP、写入并发、guardian/supervisor 收尾、最终回执和站点能力仍未通过。实现者修复、独立审查员复审，授权现场操作员验证；数小时至多日，站点时间未知。见 `B1_COMBINED_STATE_CONTAINMENT_REVIEW_20261107.md` 和相关分支审查。 |
| §0.3 测试 | 完整 Mac CPU suite 及与历史 39 个失败 ID 的差集尚未运行；Stage A→B1 原 kill/resume 覆盖未恢复；TASL-7 真实 worker determinism 未跑。实现者先解决无删除测试及子进程覆盖并独立审查；现场实际作业、lease 与安全交接条件核实后才可由授权操作员验证。耗时未确定。见 `B1_HISTORICAL_FAILURE_FOLLOWUP_20261107.md`、`B1_STAGEA_RECOVERY_PRESERVATION_BLOCKER_20261107.md`。 |
| TASL-7 归属、handover、preflight | 按作者 09:36 回复继续操作，但须先确认实际任务/lease 占用并避免抢占；明确 watcher 实际加载状态、Track S 不强制中断、Track P 安全点、无新作业协调和可保留式恢复；再执行经审查的 lease、server FD、Python、GPU UUID、磁盘和 dry-run 检查。责任人为主机 operator/实现者与独立审查员；作者如需帮助协调安全交接。现场时间未知。见 `B1_TASL7_HANDOVER_COMMAND_BOUNDARY_20261107.md`。 |
| 最终 checkout / note / author gate | 在其他实现稳定且作者澄清顺序后，绑定最终代码 pin、note 和全部输入，独立审查精确干净 HEAD，执行真实 author gate 和主机 dry run；实现者、审查员及 operator 负责。耗时取决于前项。 |
| B2 后续 | 实现并独立审查实际 runner/observer 和授权路径；作者另行决定 B2 note 与实例数/功效方案，获得独立阶段授权后由 operator 执行。责任人为 B2 实现者、审查员、作者和 operator；按 ranking 审查估计数个工程/审查日，另加作者答复与现场时间。B1 完成前仍不得启动 B2。 |
| M3→M4、M11、M10 | M3 需完成 supervisor、通知撤回/HUP、16 cases 和 site qualification；M4 全部工作因现有顺序冲突暂缓，直到 M3 接受或作者明确修改顺序；共享 `c3_label_sweep.py` 编辑亦按指令等待 M3。M11 仍缺完整 D8/statistics/reader 和作者确认。M10 HK6 需 M3 后的 Slurm host mode、J3 工作身份、HK5 后作者范围和 HoreKa 现场审查；不登录 HoreKa。责任人为实现者和独立审查员；作者负责所需决定，现场部分由各自授权的操作员负责。详见各报告，工程通常多日，作者/现场等待时间未知。 |

## 保留与透明记录

两次不同的合成 crash-recovery 执行在正常完成时删除了各自测试自有的 `runner.lock`，违反“不得删除任何东西”；不能从事后归档恢复。一次较早的合成 STOP 临时目录在共享 pytest 临时根保留窗口内消失，只有两文件留存；未观察到移除者，不能断言原因。后来审查发现 pytest 可能 unlink 测试自有的 `current` 符号链接，以及两次默认 FD capture 可能创建后 unlink 临时文件；这些操作是否成功、次数均未被系统调用追踪。没有证据显示真实 B1 或远程文件受到这些清理影响。原始可保留的合成归档、相关日志和审查在 `mac-b1-stagea-synthetic-20261107` 与 B1 分支中；未复用已记录的 STOP。详见 `B1_HISTORICAL_FAILURE_FOLLOWUP_20261107.md`、`B1_STOP_REPORTING_CANDIDATE_20261107.md` 和各审查。

DRYRUN 入口候选 `490835ea` 经独立审查 **NOT ACCEPTED**：新增的 `host_check` 在拒绝 exam 主机之前可能调用 `tempfile.gettempdir()`；本机 CPython 首次探测可能创建后 unlink 临时文件，目标主机是否发生此事未核验。先前一次审查派发遇到用量限制，09:23 后重新派发并取得 `B1_DRYRUN_DIRECT_ENTRY_REVIEW_20261107.md`（已推送 B1 分支）；实现者正修正主机检查顺序和临时根确定方式，随后须独立复审。工程工作量待修复与复核，未授权新一轮 host 测试。

## 问题清单

`docs/r1/reports/MAC_OVERNIGHT_QUESTIONS_20261107.md`（`mac-int-20261107`）按 B1 优先保留 note 顺序、禁止删除与固定 harness、TASL-7 归属及 M4 顺序的背景、选项、建议和可粘贴答复；前三项已按后续作者答复标为已答，M4 顺序仍未决定。`MAC_AUTHOR_QUESTION_RECONCILIATION_20261107.md` 区分已答事项和旧清单余项；不会重问已确定的阈值、模型选择和其他决定。
