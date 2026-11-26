# PLAN §10 row draft — `R1-TRACKS-STOP4-END` (for the author's commit; 15 November 2026)

**AI-assisted (Claude, Mac agent). A draft for the author; it governs nothing until the author commits it in PLAN
§10.** The row records the author's STOP 4 decision of 15 November 2026 (chat message, not quoted): option (c-iii) of
the two-node S0.5 summary. Track S ends before EVIDENCE; A2-U is not changed; nothing is re-run; TASL-7 is no longer
allocated to Track S.

**Sources.**
- The two-node S0.5 summary `reports/TRACKS_S05_SUMMARY_20261115.md` (branch `mac-tracks-s05-summary-both-20261115`
  @ `1417807b`, accepted at `74808c0a`; review `reviews/TRACKS_S05_SUMMARY_2NODE_REVIEW_20261115.md`). That branch
  was delivered by bundle; it must be on origin before the row's file references resolve there.
- The accepted per-node records: `reports/TRACKS_S05_T7_RESULT_20261114.md` (digits, review
  `TRACKS_S05_T7_STOP4_REVIEW_20261114.md`) and `reports/TRACKS_S05_T7_TABULAR_20261114.md` (tabular, review
  `TRACKS_S05_T7_TABULAR_REVIEW_20261114.md`), both on `trackS-ops-20261030` @ `fab88fce`.
- PLAN as of `ops-b2-20261115` @ `8709dce7`, the latest commit that touches `docs/r1/PLAN.md`. Its last §10 table is
  `R1-EXAM-B2-INVALID-TRIALS`, followed by `## 11. Relation to Paper A`. PLAN on `trackS-ops-20261030` is older
  (last touched `2906b676`, 31 Oct).
- Rows this decision bears on: `R1-TRACKS-HOST`, `R1-TRACKS-HOST-2`, `R1-TRACKS-ADOPT`, `R1-TRACKS-S02`,
  `R1-TRACKS-FRAMING`, `R1-BX-D10`, `R1-BX-D14`, `R1-TRACKS-PICK-REPEAT-DEFER`, `R1-T4-DI-FIX`.

## Where to paste, and the format

- In PLAN §10, after the `R1-EXAM-B2-INVALID-TRIALS` table and before `## 11. Relation to Paper A`. The format is the
  same as the 15 November B2 rows: a `### ` heading with the full date and "(author)", a blank line, then a two-column
  table (header, `|---|---|`, one row, each on one line, no `|` inside a cell).
- The first cell is the bare ID `R1-TRACKS-STOP4-END`. Paste **either** the Chinese block **or** the English block.
- No code reads this row. Nothing gates on it.

## Ready to paste — Chinese

```
### 15 November 2026 — Track S ends at STOP 4 (author)

| ID | Decision |
|---|---|
| R1-TRACKS-STOP4-END | **Track S 在 STOP 4 结束，不进入 EVIDENCE：不修改 A2-U，不重跑任何阶段；TASL-7 不再分配给 Track S。** 依据是两节点合并的 S0.5 摘要 `reports/TRACKS_S05_SUMMARY_20261115.md`（独立审查接受于 `74808c0a`）中的两项发现。(1) **校准门两节点都未通过**（design S0.5 (iii)：80 % 区间的覆盖率须在 [0.70, 0.90] 内，总体及每个 ≥ 20 条预测的分层都要满足）。digits_mlp（n = 298）：分层 0 为 0.538，1-2 为 0.674，≥ 3 为 0.944，总体 0.775。tabular_mlp（n = 330）：分层 0 为 0.368，1-2 为 0.653，≥ 3 为 0.831，总体 0.700。两节点的分层 0 都过低；按 runbook rev 3.3 Phase 4，这是交作者决定的 STOP，λ₂ 修正无法改变分层 0。(2) **E1 筛选不起作用。** 两节点拟合的先验中 τ0 都落在下限（0.15 σ_node），因为 τ_A2 < τ_w。因此 A2-U 对每个提议算出的 V\* 几乎相同（在全部合格的非重复 E1 决定上的极差：digits 0.036 σ_node，tabular 0.018 σ_node），并且远高于运行价格 g = 0.1 σ_node：V\* − g 在 digits 上为 2.58–2.61 σ_node，在 tabular 上为 4.04–4.06 σ_node。没有任何决定落在 g 或静态阈值（0.3 σ_node）以下或其 ±0.5 σ_node 之内；所有 E1 跳过都是规则判定的重复提议。两条 pilot 策略（a2u 与 static:0.3 σ_node,0）在两节点各 20 个实例上的动作序列逐条相同，截断到 W = 8/10/12/20 时结果也相同；S0.5b 中两条策略之间的 σ_D 及其 UCL 为 0，W = 40 时的 between_policy_sd_at_cap 也为 0。只有 E2 的 keep 是真实的决定。作者从摘要的三个选项中选 (c-iii)：不改 A2-U 的先验或方差结构，不调运行价格或预算，也不缩小为只比较 E2。此后的阶段均不进行，包括 S0.6、S0.7、S0.8 预声明、S0.9 授权、S3 和 S4，不产生 EVIDENCE。Track S 的全部数据（Phase 0–4，含 smoke、S0.1、S1.1、S0.4、S0.5 和 S0.5b）保持 ENGINEERING_ONLY，只在附录中作为说明 Track S 为何停止的 pilot 发现披露，不作为结果引用（RUNBOOK §1：ENGINEERING_ONLY/PILOT 运行不作为结果引用；草稿 `reports/TRACKS_PILOT_FINDINGS_APPENDIX_DRAFT_20261115.md`）：附录如实报告 A2-U 校准失败，不对 A2-U 本身作任何主张。Track S 在两台主机及 Mac 上留下的目录、进程、分支和数据原样保留，不移动、不修改、不删除（清单见 `reports/TRACKS_RESOURCES_AND_SCENES_20261115.md`）；如需清理，另由作者决定。本行记录作者 11 月 15 日的决定。 |
```

## Ready to paste — English

```
### 15 November 2026 — Track S ends at STOP 4 (author)

| ID | Decision |
|---|---|
| R1-TRACKS-STOP4-END | **Track S ends at STOP 4, before EVIDENCE. A2-U is not changed and no phase is re-run. TASL-7 is no longer allocated to Track S.** The basis is two findings of the two-node S0.5 summary `reports/TRACKS_S05_SUMMARY_20261115.md` (independent review accepted at `74808c0a`). (1) **The calibration gate fails on both nodes** (design S0.5 (iii): coverage of the 80 % intervals in [0.70, 0.90], overall and in every stratum with ≥ 20 predictions). digits_mlp (n = 298): stratum 0 0.538, 1-2 0.674, ≥ 3 0.944, overall 0.775. tabular_mlp (n = 330): stratum 0 0.368, 1-2 0.653, ≥ 3 0.831, overall 0.700. Stratum 0 is too low on both nodes; under runbook rev 3.3 Phase 4 that is a STOP for the author, and the λ₂ revision cannot change stratum 0. (2) **E1 screening is inert.** On both nodes the fitted prior has τ0 at its floor (0.15 σ_node), because τ_A2 < τ_w. A2-U's V\* is therefore nearly the same for every proposal (range over all eligible non-duplicate E1 decisions: digits 0.036 σ_node, tabular 0.018 σ_node), and far above the run price g = 0.1 σ_node: V\* − g is 2.58–2.61 σ_node on digits and 4.04–4.06 σ_node on tabular. No decision falls below, or within ±0.5 σ_node of, g or the static threshold (0.3 σ_node); every E1 skip is a rule-detected duplicate. The two pilot policies (a2u and static:0.3 σ_node,0) take identical action sequences on all 20 instances of each node, and give identical results at each truncation W = 8/10/12/20. σ_D between the two policies in S0.5b, and its UCL, are 0, as is between_policy_sd_at_cap at W = 40. Only the E2 keep is a real decision. Of the summary's three options the author chose (c-iii): no change to A2-U's prior or variance structure, no change to the run price or budgets, and no narrowing to an E2-only comparison. No later phase takes place, including S0.6, S0.7, the S0.8 pre-declaration, the S0.9 authorization, S3 and S4, and no EVIDENCE is produced. All Track S data (Phases 0–4: smoke, S0.1, S1.1, S0.4, S0.5 and S0.5b) stay ENGINEERING_ONLY and appear in the appendix only as pilot findings that disclose why Track S stopped, not as results (RUNBOOK §1: ENGINEERING_ONLY and PILOT runs are never quoted as results; draft `reports/TRACKS_PILOT_FINDINGS_APPENDIX_DRAFT_20261115.md`). The appendix reports A2-U's calibration failure as it is and makes no claim about A2-U itself. Track S's directories, processes, branches and data on both hosts and on the Mac are left as they are, not moved, changed or deleted (inventory `reports/TRACKS_RESOURCES_AND_SCENES_20261115.md`); any clean-up is a separate author decision. This row records the author's decision of 15 November 2026. |
```

## Consequences noted by the recording agent (not part of the decision; for the author to confirm or rule)

1. **`R1-TRACKS-FRAMING`** declared what each Track S *outcome* means. Ending before EVIDENCE is none of its outcomes
   (A on a channel, A on the budget member, A as a threshold shift, A-small or no gain found). The row applies none
   of them.
2. **`R1-BX-D10`** sets a fallback for "no campaign-level result by ≈ 15 Dec 2026": the DAC-reduction argument rests
   on the theorem plus synthetic controls, and the paper says so explicitly. Track S now gives no campaign-level
   result, so this fallback's condition is met early. Its GPU-node additions (autoresearch, an RL-type task) and its
   open manager question no longer arise.
3. **`R1-TRACKS-PICK-REPEAT-DEFER`** ("decide after the Track S result whether to repeat with the exam pick") has no
   result to wait for.
4. **`R1-TRACKS-HOST` / `-HOST-2`.** Track S's TASL-7 allocation ends; the row says so, as the author instructed.
   TASL-2 (zhixu portal) is not named in the instruction. Track S's `digits_mlp` had already moved off it (12 Nov,
   TASL-2 down), but Track S servers and the TASL-2 GPU lease may still be held there if the outage was
   network-only (inventory §2.3). Whether TASL-2 is also released is the author's call.
5. **`R1-T4-DI-FIX`.** The appendix draft reads the pilot through Proposition 8′
   (`proposals/T4_PROP10_REVISION_20261028.md`). Under that row, no theory claim enters the manuscript until the
   author's proof check, which the PLAN does not yet record.
6. **`R1-BX-D14`** lists a "Track S fallback ≈ 15 Dec 2026" target. That date no longer gates anything.
7. **The TASL-7 watcher.** As written, the row keeps Track S's `trks_watch` running on TASL-7. When B2 creates
   `~/r1_locks/trackx_evidence.active`, the watcher will touch a `STOP` file in every finished Track S directory on
   that host that has a `manifest.json` (runbook §11.4). The B2 execution plan already inventories those touches
   (step 5). Stopping the watcher would change a Track S process, so under this row it needs an author decision.
8. **`R1-TRACKS-ADOPT`** ("Track S is adopted and will be run") is superseded in its "will be run" part by this row.
   The 15 Nov format uses a bare ID, so the amendment cannot go in the ID cell; the decision text ("Track S ends at
   STOP 4, before EVIDENCE") carries it, and the author may add the row name to the text if wanted.
9. **RUNBOOK §1** says ENGINEERING_ONLY and PILOT runs are "never quoted as results", and that all written documents
   are in English. The row keeps the pilot numbers in the appendix as a disclosure, not a result. The B2 rows of
   15 Nov set the precedent for a Chinese row; the English block is there if the author prefers it.
