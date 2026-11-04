# Author decision packet — 4 November 2026 (M1)

**Drafted 4 Nov 2026 by the Mac-local agent (Claude), MAC_LOCAL_RUNBOOK_20261104 rev 3.2, M1 step 5; AI-assisted. Nothing here is a decision.** A decision exists only as a dated PLAN §10 row that the author commits, or tells the agent in chat to commit on his behalf (the commit body then quotes his words).

Integration branch: `mac-int-20261104`, based on coordinator `10742f85`, with `docs/runbooks-04nov` @ `c15b1102` (⊃ `docs/main-proposer-03nov` @ `14dc0fea`), later `0abfaf2b` (merged separately, `4ca40393`) and `8e455234` (`210aa99e`), plus `docs/repo-tidy-20261104` @ `d413dc81` (`316ba2a5`), `codex/b2-repair-20261031` @ `f98e315e`, `docs/trackS-decisions-30oct` @ `13badb0d` and `trackS-ops-20261030` @ `f5d5c6b0`. Row check: `reports/MAC_PLAN_ROW_CHECK_20261104.md` (0 missing).

**Already ruled (not repeated here):** (a) R1-HANDOVER-04NOV, amended by R1-SERVER-AGENTS-TWO; (d) R1-EXAM-ALWAYS-ON-SKIP; (d′) R1-EXAM-B1-HARNESS-PIN; (e) R1-B2-REPLAY-GO; (f) R1-P3A-OOM-OPTION3; (g) R1-TRACKS-S01-RERUN (S0.1 re-run procedure, clause (b), rev 3.4/3.5 not of record, marker helper installed, Track S after 15 Dec); the confirmed R1-BX items in R1-BX-PROPOSED-CONFIRM (including the DTQ pass criterion under REVISIONS (f)); R1-1GC-FALLBACK; R1-T1-HOREKA; R1-APPTAINER-HOST.

Each section: what is open, options, a recommendation, and a paste-ready PLAN row. Rows go in a new §10 subsection headed `### 4 November 2026 (<time>) — <topic> (author; recorded by …)`.

---

## 0. Track X work recorded after the handover — **RULED by the author (4 Nov, 15:33 and 15:44)**

> **Recorded in PLAN §10 (4 Nov, 16:13 instruction)** as R1-TRACKX-HANDOVER-RULING, in the form the author set: the decision cell holds only his words "按原定计划走"; the details are under its Consequences. The draft row below is kept as history and is superseded by the committed row.

**What the sources say.**
- R1-HANDOVER-04NOV (11:29): the operator is "the only agent acting on the servers"; "the coordinator, the Track X agent, … stop at their next safe point"; "the **Mac-local agent is the single editor** of `r1/exam/`, `r1/scripts/exam_*` and `r1/c3/train/`". R1-SERVER-AGENTS-TWO (14:58) keeps the operator on TASL-2, TASL-7 and deepthought.
- The coordinator branch then recorded, between 14:09 and 15:29: R1-EXAM-STAGEA-COMPLETE; R1-EXAM-TEMPLATE-FAILURE-MAP; R1-EXAM-TEMPLATE-AMENDMENT-PROPOSAL ("Author chose Option A"); R1-EXAM-TEMPLATE-AMENDMENT-V16; R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED (code `e996af8`, binding `96f1146`; "B1 eligible set = t7h8 8 PASS + anchors + M1-passing rows (author's decision)"); R1-EXAM-STOP9-JOURNAL (code `ab74203`, binding `74a0790`; the declared measurement relaunched on TASL-7 as `r1_stagea_20261104_t7j10`).
- So after 11:29 the Track X agent edited `r1/exam/` and runs on TASL-7. Both sets of rows are kept unchanged in the integration; no row reconciled them.

**Options put to the author.** The Mac agent's chat message of 4 Nov (about 15:30, before the coordinator's STOP 9 commit was known to it) offered, verbatim:

> 1. Option A 视为对交接行的例外：Track X agent 完成 A1 修订 + t7i9 测量后再停；`r1/exam/` 交给我从 `96f1146` 起接手（M2 以它为基）。
> 2. 交接行优先：A1 代码已冻结在 `96f1146`，t7i9 由 operator 执行；我从 `96f1146` 起接手 `r1/exam/`。
> 3. 其他。

(1: Option A as an exception to the handover row — the Track X agent finishes the A1 amendment and the t7i9 measurement, then stops; `r1/exam/` passes to the Mac agent from `96f1146`, M2 based on it. 2: the handover row first — A1 code frozen at `96f1146`, t7i9 run by the operator; the Mac agent takes over `r1/exam/` from `96f1146`. 3: other.) The ruling below chose 2, with two changes the author stated: the relaunched `t7j10` is allowed to finish where it runs, and the hand-over point is `74a0790` / `ab74203`, not `96f1146`.

**Author's ruling.** At 15:33 the author wrote "按原定计划走" ("go with the original plan"). At 15:44 he wrote: "裁定：选 2，交接行优先（作者 15:33 "按原定计划走"）。`t7j10` 已在 TASL-7 上运行，允许它跑完，Track X agent 随后停止。`t7j10` 的核验和接收审查、Stage A 验收归 operator 的 O1。你从 `74a0790`（代码 `ab74203`）起接手 `r1/exam/`，M2 以它为基。如果 `ab74203` 还缺独立 review，就按 M5 流程补。B1 候选集为 `t7h8` 的 8 个 PASS + anchors + `t7j10` 的通过者，`t7j10` 要经 operator 验收后才算数。这条裁定写进决策包第一项。整合以 `10742f85` 为底。" The quotation is the author's 15:44 message as received, including its parenthetical citing his 15:33 message; the commit body of `a43e1b47` quotes the same message with elisions marked "…". In English: option 2, the handover row takes precedence; `t7j10`, already running on TASL-7, may run to completion, after which the Track X agent stops; the verification and receiving review of `t7j10` and the Stage A acceptance belong to the operator's O1; the Mac agent takes over `r1/exam/` from `74a0790` (code `ab74203`) and bases M2 on it; if `ab74203` still lacks an independent review, the Mac agent supplies one by the M5 procedure; the B1 candidate set is t7h8's 8 PASS + anchors + the `t7j10` passes, which count only after the operator's acceptance; this ruling goes into the decision packet's first item; the integration is based on `10742f85`.

**Row recording the ruling** (paste-ready; the author commits it, or tells the Mac agent in chat to commit it on his behalf):
```
| R1-TRACKX-HANDOVER-RULING (4 Nov, 15:44) | **The handover row takes precedence** (author: "按原定计划走", 15:33; "选 2，交接行优先", 15:44). The declared measurement `r1_stagea_20261104_t7j10` (code `ab74203`, binding `74a0790`), already running on TASL-7, may run to completion; the Track X agent then stops. The verification and receiving review of `t7j10`, and the Stage A acceptance, belong to the operator's O1. The Mac-local agent takes over `r1/exam/` from `74a0790` (code `ab74203`) and bases M2 on it (with `r1/scripts/exam_*`, as R1-HANDOVER-04NOV already assigns); if `ab74203` lacks an independent review, the Mac agent supplies one by the M5 procedure. **B1 candidate set:** the 8 PASS of `t7h8` + the anchors + the `t7j10` passes, the latter counting only after the operator's acceptance. |
```

## (a) `codex/b2-repair-20261031` files outside its scope

**Open.** R1-HANDOVER-04NOV leaves the acknowledgement open. M1 merged everything else from the branch and **held** these five diffs (`git diff 30303d87 f98e315e -- <file>`). All five come from one commit, `9bab3d6f` ("Prepare guarded C3 evidence provenance and audit").

| File | Change | Owner |
|---|---|---|
| `r1/c3/train/run.py` | `EVAL_COLUMNS` also matches `delta_true`, `delta_audit_all`, `se_audit`, `candidate_metrics`, `incumbent_metrics`; `_keys` walks lists; `guard_rows` refuses identifiable sweep EVIDENCE rows except for `p4_final_eval` with its note | Track P (now the Mac agent) |
| `r1/c3/train/trainer.py` | `Trainer` refuses `purpose == "p4_final_eval"` | Track P (now the Mac agent) |
| `r1/c3/env.py` | `OfflineBanditEnv` refuses identifiable sweep EVIDENCE rows | shared |
| `r1/c3/control.py` | `fit_awr_direct` refuses EVIDENCE rows and the evaluation-side value keys | shared |
| `r1/c3/prior_model.py` | `TableArmPrior.fit` refuses EVIDENCE rows | shared |

**Review status.** The only review of that commit, `reviews/C3_EVIDENCE_GUARDS_REVIEW_20261028.md`, gives the verdict **"BLOCK / NOT ACCEPTED FOR B.2 LAUNCH"** for code commit `9bab3d6f`. It states that marker-based boundaries cannot identify stripped rows, so global training/selection isolation is "NOT CHECKABLE", and that the guards are not to be represented as a proof of isolation or as acceptance of later training. No later review on the branch covers these five files.

**Effect.** Most changes refuse rows that carry an EVIDENCE marker. Two do more: the wider `EVAL_COLUMNS` in `run.py` makes `guard_rows` refuse the keys `delta_true`, `delta_audit_all`, `se_audit`, `candidate_metrics`, `incumbent_metrics` on **any** row, marked or not, for every purpose except `p4_final_eval`, and `_keys` now finds such keys inside lists. Track P inputs that carry one of these keys are therefore refused where they were accepted before.

**Overlap.** `trackS-ops-20261030` also changes `r1/c3/prior_model.py` (explicit `cache_prompt` for the A4 client, R1-CACHEPROMPT-FALSE). That change stays on its branch and is used by pin; if the b2-repair change is acknowledged, it is merged three-way into the base version, not on top of the Track S version.

Without the five files, the branch's own tests in `test_c3_evidence_other_boundaries.py` fail on `mac-int-20261104` (11 tests; `reports/MAC_M1_TESTS_20261104.md`).

**Options.**
1. Acknowledge all five now; M1 merges them.
2. Acknowledge the two `r1/c3/train/` files only (the Mac agent is their editor); the three shared files wait.
3. **Defer:** M3 (which continues `codex/b2-repair-20261031`) takes the five changes into its scope and its independent review; the author acknowledges them together with M3's accepted commit.
4. Do not acknowledge; they stay on the branch.

> **Author, 4 Nov 16:13:** "(a) 同意：5 个范围外文件并入 M3 一起审，审完我再决定。" (option 3: reviewed within M3; he decides after that review). Not yet a PLAN row.

**Recommendation: 3.** The changes are protective in intent, but their one review blocked, and `run.py` changes behaviour for unmarked rows. M3's review has to cover the B.2 guard code anyway, so reviewing these five there costs little and gives the acknowledgement a reviewed basis.

**Draft row (option 3).**
```
| R1-B2-REPAIR-SCOPE-ACK (4 Nov) | The five changes of `codex/b2-repair-20261031` outside its scope (commit `9bab3d6f`: `r1/c3/train/run.py`, `r1/c3/train/trainer.py`, `r1/c3/env.py`, `r1/c3/control.py`, `r1/c3/prior_model.py`) are taken into M3's scope and reviewed with it; the author acknowledges them, or not, with M3's accepted commit. Until then they are not merged. Their earlier review (`reviews/C3_EVIDENCE_GUARDS_REVIEW_20261028.md`, BLOCK for B.2 launch) is not an acceptance. |
```

---

## (b) R1-HOSTS-04NOV (host plan)

**Open.** The rows since 26 Oct place hosts piecemeal; R1-SERVER-AGENTS-TWO's host lists are *(proposed)*. A consolidated row:

- **TASL-7:** `t7j10` runs to completion (section 0 ruling) and the operator's O1 accepts it; then Track P (P.3a, option 3 follow-ups), with Track S `tabular_mlp` in the gaps. No Track S GPU job before that.
- **TASL-2:** Track S `digits_mlp`, with Track X B1/B2 first (their campaign worker is TASL-2-only).
- **deepthought:** B.2 environment replay and audits on CPU; DTQ (O5); the A4 7B row; the main proposer across two TITANs if DTQ passes (R1-BX-REVISIONS (f), criterion confirmed in R1-BX-PROPOSED-CONFIRM).
- **Ada:** overflow (R1-ADA-OVERFLOW), C.4, and the T1 whole-table fallback (R1-T1-HOREKA). Resumable units only.
- **HoreKa 2:** the HoreKa agent, the whole T1 tier (R1-T1-HOREKA, R1-SERVER-AGENTS-TWO).

**Speed figures (estimates, background only).** Sweep 1 on one TITAN X made 5,813 proposals in about 11.6 h, about 7 s per proposal of wall throughput, worker CPU included, at `cache_prompt` default; the recorded per-call latency averages about 112 s because 16 workers queue on one `-np 1` server. Track S's serial latency on a 4090 is 0.68–0.70 s per call. These are the 7B; the pick's speed is unmeasured on every host.

**Options.** 1. Adopt as listed. 2. Adopt with Track P starting on TASL-7 in the gaps of O1's acceptance work. 3. Leave per-row placement.

**Recommendation: 1** (it only writes down what the rows already imply, and confirms R1-SERVER-AGENTS-TWO's proposed host lists).

**Draft row.**
```
| R1-HOSTS-04NOV (4 Nov) | **Host plan.** TASL-7: `t7j10` runs to completion and is accepted in O1; then Track P, with Track S `tabular_mlp` in the gaps, and no Track S GPU job before that. TASL-2: Track S `digits_mlp`, Track X B1/B2 first. deepthought: B.2 replay and audits (CPU), DTQ (O5), the A4 7B row, and the main proposer across two TITANs if DTQ passes. Ada: overflow, C.4 and the T1 whole-table fallback, resumable units only. HoreKa 2: the HoreKa agent and the whole T1 tier. The operator acts on TASL-2, TASL-7, deepthought and Ada; the HoreKa agent on HoreKa 2 only; neither acts on the other's hosts. This confirms R1-SERVER-AGENTS-TWO's proposed host lists. |
```

---

## (c) B.1b difference list if sweep 2 runs on deepthought

**Open.** The DTQ pass criterion is confirmed (R1-BX-PROPOSED-CONFIRM, REVISIONS (f)). R1-MAIN-PROPOSER (c) lists the differences of sweep 2 on a 4090. If sweep 2's proposer runs on deepthought across two TITANs, the list changes: same `620d222` sm_52 build as sweep 1 (no sm_52/sm_89 difference), plus the two-card layer split (`--split-mode layer --tensor-split 1,1`). Separately, `deepthought2.etp.kit.edu` (2 × L40S, 48 GB each) is outside the run hosts; a row could add it.

**Options.** 1. Amend R1-MAIN-PROPOSER (c) conditionally as below. 2. Wait until DTQ has run. Separately: add deepthought2 as a sweep-2 host, or not.

**Recommendation: 1; do not add deepthought2 now** (no qualification exists for it).

**Draft row.**
```
| R1-B1B-DIFF-DT (4 Nov) | Amends R1-MAIN-PROPOSER (c): if sweep 2's proposer runs on deepthought (R1-BX-REVISIONS (f), DTQ passed), the stack-difference list records the same llama.cpp `620d222` sm_52 build as sweep 1 instead of "sm_52 against sm_89", and adds one llama-server split across two TITAN X (`--split-mode layer --tensor-split 1,1`). All other items stay. deepthought2 is not a sweep-2 host. |
```

---

## (d) R1-EXAM-RULE-X5V2 (follow-up row, after M2)

**Open.** M2 writes `x5_rule_v2.yaml` with `always_on_in_b1: skip` (R1-EXAM-ALWAYS-ON-SKIP) and computes its sha. The ruling of section 0 fixes the **B1 candidate set** (t7h8's 8 PASS + anchors + the operator-accepted `t7j10` passes). For v2 that means: the set of **Stage A passes** v2 reads is t7h8's PASS ∪ the operator-accepted `t7j10` PASS; the anchors enter B1 as anchors, not as eligible candidates; and v2's other eligibility conditions still apply — D28 pass and able to run with thinking off (R1-MAIN-PROPOSER (a)), and always-thinking models skip B1 (R1-EXAM-ALWAYS-ON-SKIP). Only the sha row remains.

**Draft row (sha filled after M2 and its review; to be committed after R1-TRACKX-HANDOVER-RULING).**
```
| R1-EXAM-RULE-X5V2 (date) | `r1/exam/rules/x5_rule_v2.yaml` sha256 `<sha>` (from `proposals/X5_RULE_V2_DRAFT_20261104.md`; `always_on_in_b1: skip` per R1-EXAM-ALWAYS-ON-SKIP) is frozen for Track X B1/B2, with code `<commit>` and review `reviews/MAC_M2_REVIEW_<date>.md`. The Stage A pass set it reads is the `t7h8` PASS ∪ the operator-accepted `t7j10` PASS (R1-TRACKX-HANDOVER-RULING); anchors run as anchors; the D28 and thinking-off conditions of R1-MAIN-PROPOSER (a) apply unchanged. `x5_rule_v1.yaml` stays as Stage A's rule. |
```

---

## (e) Replay and B.2 notes

Covered by R1-B2-REPLAY-GO. M3 drafts `proposals/AUTH_DRAFT_c3_replay_<date>.md` (e1) and `proposals/AUTH_DRAFT_b2_<date>.md` (e2); nothing to decide now.

---

## (g) Track S — remaining point

One observation, no decision needed unless the author wants one: R1-CACHEPROMPT-FALSE cites the ruling file `docs/prompts/TRACKS_CACHEPROMPT_FIX_PROMPT_20261031.md`, which is on no branch. The §5–6 text of `proposals/TRACKS_NOCACHE_20261030.md` at `8bfd003` (local bundle only) is also not on GitHub; clause (b) is now adopted in R1-TRACKS-S01-RERUN's own words, so the packet does not need to quote it.

---

## (h) R1-MAIN-PROPOSER's *(proposed)* items

| Item | Source | Recommendation |
|---|---|---|
| Sweep 2's fresh-seed audits on deepthought CPUs, with the 50-proposal two-host check as fallback | (f) | confirm |
| Above 4 days projected on one host is a STOP | (h) | confirm (consistent with the DTQ projection limit) |
| Pooled training vs sweep 2 only, chosen on validation before any test read | (e) | confirm |
| Track S keeps `qwen2.5-coder:7b` on CPU nodes; repeat with the pick decided after the outcome | (j); R1-BX-D10 direction | confirm for CPU nodes; GPU-node manager stays with the D10 row after G.0/D28 |
| P.3b exam set drawn from sweep 2's training partition (sweep 1, disclosed, until sweep 2 exists) | MAC M7 | confirm |

**Draft row.**
```
| R1-MAIN-PROPOSER-CONFIRM (4 Nov) | Confirms R1-MAIN-PROPOSER's proposed items: sweep 2's audits on deepthought CPUs (else on the sweep host with 50 proposals audited on both); a projection above 4 days on one host is a STOP; pooled vs sweep-2-only training is fixed on validation before any test read; Track S's CPU nodes keep `qwen2.5-coder:7b` (GPU-node manager per R1-BX-D10's later row); the P.3b exam set is a fixed subset of sweep 2's training partition, or of sweep 1's, disclosed, until sweep 2 exists. |
```

---

## (i) Dates and H1

R1-BX-D14's dates are targets (B.7 ≈ 8 Dec, Track S fallback ≈ 15 Dec, D.3 ≈ 3 Jan, manuscript 10 Jan); they are recomputed after G.4 and shown to the author before they change. **H1 is pending:** if only some T1 nodes have labels at B.7, read B.7 on T0 plus the labelled T1 nodes and disclose the node count, written into R1-BX-D8-CONFIRM in advance.

**Recommendation:** confirm H1 now, so M11 can write it into the gate and the confirm row.

**Draft row.**
```
| R1-B7-PARTIAL-T1 (4 Nov) | Confirms H1: B.7 ≈ 8 Dec stays a target, recomputed after G.4. If only some T1 nodes have labels by then, B.7 is read on T0 plus the labelled T1 nodes, with the node count disclosed; leave-one-suite-out needs at least one labelled T1 node per suite, otherwise STOP. This is written into R1-BX-D8-CONFIRM. |
```

---

## (j) R1-BX and 4 Nov items still *(proposed)* or *(open)*

Items confirmed in R1-BX-PROPOSED-CONFIRM are not repeated. Each item: options → recommendation → paste-ready line, or "no row now". **Numbers marked † are the Mac agent's own proposals with no source in PLAN or the specs; they are starting points for the author, not derived values.**

1. **R1-BX-D8-CONFIRM** — the numbers are accepted (R1-BX-PROPOSED-CONFIRM, D8); the row waits for M11's gate-code sha. **Must be committed before any sweep-2 (T0 or T1) label table is copied back for analysis.**
   `| R1-BX-D8-CONFIRM (date) | Gate code `<path>` @ `<commit>`, sha256 `<sha>`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8) and, if adopted, R1-B7-PARTIAL-T1; T0 and T1 pooled with tier as a stratum. Sweep-2 label tables may be analysed from this row on. |`
2. **D6 exact API model** — R1-BX-PROPOSED-CONFIRM fixes the class (commercial mid-tier, another family than the pick's, not DeepSeek, cap €100–200). Recommendation: the author names the model and its version pin after X.7, once the pick's family is known.
   `| R1-BX-D6-MODEL (date) | API proposer: `<provider/model>`, version pin `<pin>`, cost cap `<€>`, calls only from `<host>` with full request/response and returned model version logged; closed-loop evaluation only. |`
3. **G.5 divergence STOP** (TRACK_G) — options: a per-node share of divergent T1 label proposals above which the node STOPs, or no fixed threshold (STOP on the author's reading of G.5's report). Recommendation: a fixed share, 20 %†, with the node moved to T2 only by an author row.
   `| R1-TRACKG-G5-DIVERGENCE (date) | G.5 STOPs a T1 node for the author when more than <20 %†> of its label proposals are divergent (R1-BX-PROPOSED-CONFIRM, REVISIONS (c)); the node moves to T2 only by an author row. |`
4. **T0 as the held-out suite** in leave-one-suite-out — options: never; also as a secondary fold. Recommendation: never in the primary test; a T0-held-out fold reported as secondary.
   `| R1-LOSO-T0 (date) | T0 is never the held-out suite in the primary leave-one-suite-out test; a T0-held-out fold is reported as secondary. |`
5. **Probe A6** — R1-P3A-OOM-OPTION3 already uses it for the re-run decision (mean |Δ RPS| > 0.01). Recommendation: descriptive otherwise. No row now.
6. **Student-t details beyond E5** — when a node's floor counts as heavy-tailed, and which degrees of freedom. Options: a declared numeric test (e.g. excess kurtosis of the 10-seed floor > 3† on ≥ 2 of the representative edits, ν = 5†), or a per-node author call in the G.3 selection row. Recommendation: the per-node author call in G.3, with the census's kurtosis reported; the numbers† only if the author wants a mechanical rule.
   `| R1-NOISE-STUDENT-T (date) | Heavy-tailed floors are declared per node in the G.3 selection row, with each node's 10-seed excess kurtosis reported; the declared nodes use a Student-t soft label with ν = <ν> before labels are built. |`
7. **Licence check (REVISIONS (e))** — result due from G.0 (HoreKa agent). No row now.
8. **T1/T2 task lists (G.3)** — after the census. No row now.
9. **Container route on run hosts** — Docker on deepthought known; 4090s, Ada and HoreKa 2 unchecked. Recommendation: the operator checks the 4090s and Ada in O0; the HoreKa agent checks HoreKa 2 in its scan; R1-BX-REVISIONS (g)'s order of preference applies.
   `| R1-CONTAINER-CHECKS (date) | The operator checks container availability (Docker, Podman, Apptainer) on TASL-2, TASL-7 and Ada in O0; the HoreKa agent checks HoreKa 2 in its scan; R1-BX-REVISIONS (g)'s order of preference applies. |`
10. **Phase C/D host plan** (B.4 pick row, C.2 on 1–2 T1 nodes, C.3, T2, API closed loop, A4 answers for T1) — Recommendation: plan after G.4 and B.7, as one row with the date recomputation. No row now.
11. **R1-SERVER-AGENTS-TWO (proposed)** — host lists (covered by (b)); amended rows (R1-HANDOVER-04NOV, R1-BX-PORTING-CONFIRM, R1-BX-REVISIONS (h), R1-ADA-CENSUS); the HoreKa agent's working mode (agent-partition node, author-opened tunnel). Recommendation: confirm.
    `| R1-SERVER-AGENTS-TWO-CONFIRM (date) | Confirms R1-SERVER-AGENTS-TWO's proposed consequences: the host lists (see R1-HOSTS-04NOV), the rows it amends (R1-HANDOVER-04NOV, R1-BX-PORTING-CONFIRM, R1-BX-REVISIONS (h), R1-ADA-CENSUS), the HoreKa agent working only from an agent-partition compute node through the author's tunnel, and hand-overs between the two server agents only through the author or pushed branches. |`
12. **R1-SERVER-AGENTS-TWO (open)** — G.0 raw-cost work on Ada for the fallback in the meantime (recommend: no, until the HoreKa scan says HoreKa 2 cannot run T1); Track S GPU nodes' own 4090 noise floor (recommend: yes — one GPU model per table, R1-BX-D5).
    `| R1-ADA-FALLBACK-HOLD (date) | No G.0 work on Ada until the HoreKa scan shows HoreKa 2 cannot run T1. Track S GPU nodes measure their own 4090 noise floor (one GPU model per table, R1-BX-D5). |`
13. **R1-T1-HOREKA (proposed)** — `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` as the design basis, adopted only by a later row after the scan. No row now.
14. **R1-1GC-FALLBACK (open)** — MLAgentBench light tasks as T1 and T2 candidates (recommend: yes, fixed in G.3); the 1GC extra tasks' tier and role (recommend: T2 only, outside the 12–16 count, always training-side in folds); domain coverage (recommend: decide in G.3 with the census).
    `| R1-1GC-FALLBACK-CONFIRM (date) | MLAgentBench light tasks are T1 and T2 candidates, fixed in G.3; 1GC-7RC's public-dataset tasks are T2 only, outside the 12–16 count, and always on the training side of leave-one-suite-out folds; domain coverage is decided in G.3. |`
15. **R1-BX-D10 (Track S manager on GPU nodes)** — committed after G.0/D28 (R1-BX-PROPOSED-CONFIRM). No row now.

---

## (k) M1 exceptions for the author to acknowledge

1. **Tests ran in the cloud workspace, not on the Mac.** The Mac's git cannot reach GitHub through its proxy, so the integration and the CPU suite ran in the chat session's Linux workspace (Python 3.13, fresh venv, harness `897d83c`), both runs in the same environment (`reports/MAC_M1_TESTS_20261104.md`). R1-LOCAL-TEST-SCOPE speaks of the Mac CPU.
> **Author, 4 Nov 16:13:** "(k) 同意：测试在云端跑可以；那 3 个 `test_c3_launch_provenance` 失败只有在 M3 修好的前提下才算已知例外。" (cloud tests accepted; the three failures count as a known exception only once M3 has fixed them). Not yet a PLAN row.

2. **"Failure set equal apart from new tests" is not literally met.** Three failures are in the existing `r1/tests/test_c3_launch_provenance.py`. They fail on `codex/b2-repair-20261031` itself: that branch changed `r1/scripts/c3_label_sweep.py` without updating this test's fixtures. Recommendation: accept as an exception, with the fixture fix assigned to M3.

*Superseded by the author's 16:13 reply (above); kept as history:*
```
| R1-M1-TEST-EXCEPTIONS (4 Nov) | M1's tests may run in the chat session's cloud workspace (CPU, same scope as R1-LOCAL-TEST-SCOPE) while the Mac cannot reach GitHub. The three `test_c3_launch_provenance.py` failures inherited from `codex/b2-repair-20261031` are accepted as an exception to M1's Done-when; M3 fixes the fixtures. |
```

Redrafted to the author's 16:13 condition (paste-ready if he wants a row):
```
| R1-M1-TEST-EXCEPTIONS (4 Nov, 16:13) | M1's tests may run in the chat session's cloud workspace (CPU, same scope as R1-LOCAL-TEST-SCOPE). The three `test_c3_launch_provenance.py` failures inherited from `codex/b2-repair-20261031` count as a known exception to M1's Done-when only once M3 has fixed them (author: "只有在 M3 修好的前提下才算已知例外"). |
```

---

## Hand-off to the operator — gated

The operator is pointed at `mac-int-20261104` only after R1-TRACKX-HANDOVER-RULING, R1-EXAM-A1-M1-REQUIREMENTS and R1-EXAM-A1-ANCHOR-CRITERION are in PLAN §10, independently reviewed and pushed (`reviews/MAC_RULING_ROW_REVIEW_20261104.md`, `reviews/MAC_A1_REQUIREMENTS_REVIEW_20261104.md`, `reviews/MAC_RULINGS_1730_REVIEW_20261104.md`). The integrator gives the author the message with the pushed commit. The author passed on an earlier template (at `009d859a`, without the anchor criterion); the current message supersedes it and says so.

Message template (the integrator fills `<commit>` with the pushed head):

> This supersedes the earlier message that named `009d859a`. Read the plan from `mac-int-20261104` at `<commit>`. It integrates coordinator `10742f85`, `docs/runbooks-04nov` @ `8e455234`, `docs/repo-tidy-20261104` @ `d413dc81`, `codex/b2-repair-20261031` (five out-of-scope files held, under review in M3), the Track S documents and the RUNBOOK §5 pin table. Your runbook is `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md` on that commit. PLAN §10 R1-TRACKX-HANDOVER-RULING (4 Nov 15:44) applies: `t7j10` may run to completion on TASL-7, then the Track X agent stops; the verification and receiving review of `t7j10` and the Stage A acceptance are part of your O1; the B1 candidate set is `t7h8`'s 8 PASS + anchors + the `t7j10` passes you accept. PLAN §10 R1-EXAM-A1-M1-REQUIREMENTS (4 Nov 16:39) adds an acceptance criterion for `t7j10`: the three anchors' Stage A numbers in `t7j10` (`random_valid`, `scripted`, `qwen25_coder_7b`: parse rate, reproducibility, template result) must agree with `t7h8` — per R1-EXAM-A1-ANCHOR-CRITERION (17:30): `qwen25_coder_7b`'s three items exactly equal, `random_valid` and `scripted` compared on result status only; if they do not, `t7j10` is not accepted and you report to the author before anything else. Do not touch the running `t7j10`. No other new server step is unlocked by M1.

## Notes for later tasks (from R1-EXAM-A1-M1-REQUIREMENTS)

- **M4 (sweep code):** at `fe193b3b`, `r1/scripts/c3_label_sweep.py` and `r1/scripts/llama_server_instance.py` have no `template_repair` / `--chat-template-file` handling. If the sweep-2 proposer is one of the three repaired models, M4 must pass the registry's SHA-pinned repair template to the server (refusing a digest mismatch), record its sha in the manifest, and test it — including any HoreKa slurm mode written later. This is the "change the code and add a test" case of requirement (1).
- **M2 (B1/B2):** briefed on requirement (1); the B1/B2 path must be shown by test to pass the repair template through `r1.exam.runtime.template_repair_args`.
- **M8 (manuscript):** the appendix requirement (3).

