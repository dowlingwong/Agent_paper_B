# Author decision packet — 4 November 2026 (M1)

**Drafted 4 Nov 2026 by the Mac-local agent (Claude), MAC_LOCAL_RUNBOOK_20261104 rev 3.2, M1 step 5; AI-assisted. Nothing here is a decision.** A decision exists only as a dated PLAN §10 row that the author commits, or tells the agent in chat to commit on his behalf (the commit body then quotes his words).

Integration branch: `mac-int-20261104`, based on coordinator `10742f85`, with `docs/runbooks-04nov` @ `c15b1102` (⊃ `docs/main-proposer-03nov` @ `14dc0fea`), `codex/b2-repair-20261031` @ `f98e315e`, `docs/trackS-decisions-30oct` @ `13badb0d` and `trackS-ops-20261030` @ `f5d5c6b0`. Row check: `reports/MAC_PLAN_ROW_CHECK_20261104.md` (0 missing).

**Already ruled (not repeated here):** (a) R1-HANDOVER-04NOV, amended by R1-SERVER-AGENTS-TWO; (d) R1-EXAM-ALWAYS-ON-SKIP; (d′) R1-EXAM-B1-HARNESS-PIN; (e) R1-B2-REPLAY-GO; (f) R1-P3A-OOM-OPTION3; (g) R1-TRACKS-S01-RERUN (S0.1 re-run procedure, clause (b), rev 3.4/3.5 not of record, marker helper installed, Track S after 15 Dec); the confirmed R1-BX items in R1-BX-PROPOSED-CONFIRM (including the DTQ pass criterion under REVISIONS (f)); R1-1GC-FALLBACK; R1-T1-HOREKA; R1-APPTAINER-HOST.

Each section: what is open, options, a recommendation, and a paste-ready PLAN row. Rows go in a new §10 subsection headed `### 4 November 2026 (<time>) — <topic> (author; recorded by …)`.

---

## 0. NEW — Track X work recorded after the handover (needs a ruling first)

**What the sources say.**
- R1-HANDOVER-04NOV (11:29): the operator is "the only agent acting on the servers"; "the coordinator, the Track X agent, … stop at their next safe point"; "the **Mac-local agent is the single editor** of `r1/exam/`, `r1/scripts/exam_*` and `r1/c3/train/`". R1-SERVER-AGENTS-TWO (14:58) keeps the operator on TASL-2, TASL-7 and deepthought.
- The coordinator branch then recorded, between 14:09 and 15:29: R1-EXAM-STAGEA-COMPLETE; R1-EXAM-TEMPLATE-FAILURE-MAP; R1-EXAM-TEMPLATE-AMENDMENT-PROPOSAL ("Author chose Option A"); R1-EXAM-TEMPLATE-AMENDMENT-V16; R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED (code `e996af8`, binding `96f1146`; "B1 eligible set = t7h8 8 PASS + anchors + M1-passing rows (author's decision)"); R1-EXAM-STOP9-JOURNAL (code `ab74203`, binding `74a0790`; the declared measurement relaunched on TASL-7 as `r1_stagea_20261104_t7j10`).
- So after 11:29 the Track X agent edited `r1/exam/` and runs on TASL-7. Both sets of rows are kept unchanged in the integration. They are not reconciled by any row.

**Options.**
1. **Option A is an exception to the handover for the A1 amendment only.** The Track X agent finishes `t7j10` and its receiving review, then stops; `r1/exam/` passes to the Mac agent at the reviewed head of `codex/trackx-stagea-cooperative-20261031`; B1/B2 run under the operator.
2. **The handover wins now.** `t7j10` continues under the operator (who takes over the running attempt's guardian and lease as they stand); `r1/exam/` passes to the Mac agent at `74a0790`.
3. Pause `t7j10` until the ownership is settled.

**Recommendation: 1.** The attempt is already running under a reviewed guardian, and moving a live lease between agents is the riskier step. Stating the end point in a row keeps one editor per file from then on.

**Draft row.**
```
| R1-TRACKX-AMENDMENT-SCOPE (4 Nov) | **The Track X agent's A1 amendment work is an exception to R1-HANDOVER-04NOV, limited to the declared measurement `r1_stagea_20261104_t7j10` (code `ab74203`, binding `74a0790`) and its receiving review.** It makes no other change to `r1/exam/` or `r1/scripts/exam_*` and starts no other server job. After the receiving review it stops; from then the Mac-local agent is the single editor of `r1/exam/` and `r1/scripts/exam_*`, starting from the reviewed head of `codex/trackx-stagea-cooperative-20261031`, and Track X B1/B2 run under the operator. |
```

---

## (a) `codex/b2-repair-20261031` files outside its scope

**Open.** R1-HANDOVER-04NOV leaves the acknowledgement open. M1 merged everything else from the branch and **held** these five diffs (`git diff 30303d87 f98e315e -- <file>`):

| File | Change | Owner |
|---|---|---|
| `r1/c3/train/run.py` | `EVAL_COLUMNS` also matches `delta_true`, `delta_audit_all`, `se_audit`, `candidate_metrics`, `incumbent_metrics`; `_keys` walks lists; `guard_rows` refuses identifiable sweep EVIDENCE rows except for `p4_final_eval` with its note | Track P (now the Mac agent) |
| `r1/c3/train/trainer.py` | `Trainer` refuses `purpose == "p4_final_eval"` | Track P (now the Mac agent) |
| `r1/c3/env.py` | `OfflineBanditEnv` refuses identifiable sweep EVIDENCE rows | shared |
| `r1/c3/control.py` | `fit_awr_direct` refuses EVIDENCE rows and the evaluation-side value keys | shared |
| `r1/c3/prior_model.py` | `TableArmPrior.fit` refuses EVIDENCE rows | shared |

All five only add fail-closed refusals through the new `r1/c3/evidence_boundary.py` (merged). They were reviewed with the branch (`reviews/C3_EVIDENCE_GUARDS_REVIEW_20261028.md`). Without them, the branch's own tests that exercise these boundaries fail on `mac-int-20261104` (see the M1 test comparison).

**Options.** 1. Acknowledge all five; M1 merges them. 2. Acknowledge the two `r1/c3/train/` files only (the Mac agent is their editor); the three shared files wait. 3. Acknowledge none.

**Recommendation: 1.** The changes only refuse inputs; they do not change any result on rows without EVIDENCE markers.

**Draft row.**
```
| R1-B2-REPAIR-SCOPE-ACK (4 Nov) | The author acknowledges the five changes of `codex/b2-repair-20261031` (`f98e315e`) outside that branch's scope — `r1/c3/train/run.py`, `r1/c3/train/trainer.py`, `r1/c3/env.py`, `r1/c3/control.py`, `r1/c3/prior_model.py` — as reviewed in `reviews/C3_EVIDENCE_GUARDS_REVIEW_20261028.md`. They are merged into `mac-int-20261104` unchanged. |
```

---

## (b) R1-HOSTS-04NOV (host plan)

**Open.** The rows since 26 Oct place hosts piecemeal; R1-SERVER-AGENTS-TWO's host lists are *(proposed)*. A consolidated row:

- **TASL-7:** Track X until the A1 measurement (`t7j10`) is received (section 0); then Track P (P.3a, option 3 follow-ups), with Track S `tabular_mlp` in the gaps. No Track S GPU job before that.
- **TASL-2:** Track S `digits_mlp`, with Track X B1/B2 first (their campaign worker is TASL-2-only).
- **deepthought:** B.2 environment replay and audits on CPU; DTQ (O5); the A4 7B row; the main proposer across two TITANs if DTQ passes (R1-BX-REVISIONS (f), criterion confirmed in R1-BX-PROPOSED-CONFIRM).
- **Ada:** overflow (R1-ADA-OVERFLOW), C.4, and the T1 whole-table fallback (R1-T1-HOREKA). Resumable units only.
- **HoreKa 2:** the HoreKa agent, the whole T1 tier (R1-T1-HOREKA, R1-SERVER-AGENTS-TWO).

**Speed figures (estimates, background only).** Sweep 1 on one TITAN X made 5,813 proposals in about 11.6 h, about 7 s per proposal of wall throughput, worker CPU included, at `cache_prompt` default; the recorded per-call latency averages about 112 s because 16 workers queue on one `-np 1` server. Track S's serial latency on a 4090 is 0.68–0.70 s per call. These are the 7B; the pick's speed is unmeasured on every host.

**Options.** 1. Adopt as listed. 2. Adopt with TASL-7 handed to Track P now and the A1 measurement moved to TASL-2. 3. Leave per-row placement.

**Recommendation: 1** (it only writes down what the rows already imply, and confirms R1-SERVER-AGENTS-TWO's proposed host lists).

**Draft row.**
```
| R1-HOSTS-04NOV (4 Nov) | **Host plan.** TASL-7: Track X until the A1 measurement `t7j10` is received; then Track P, with Track S `tabular_mlp` in the gaps, and no Track S GPU job before that. TASL-2: Track S `digits_mlp`, Track X B1/B2 first. deepthought: B.2 replay and audits (CPU), DTQ (O5), the A4 7B row, and the main proposer across two TITANs if DTQ passes. Ada: overflow, C.4 and the T1 whole-table fallback, resumable units only. HoreKa 2: the HoreKa agent and the whole T1 tier. The operator acts on TASL-2, TASL-7, deepthought and Ada; the HoreKa agent on HoreKa 2 only; neither acts on the other's hosts. This confirms R1-SERVER-AGENTS-TWO's proposed host lists. |
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

**Open.** M2 writes `x5_rule_v2.yaml` with `always_on_in_b1: skip` (R1-EXAM-ALWAYS-ON-SKIP) and computes its sha. A point for the author: R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED defines the B1 eligible set as "t7h8 8 PASS + anchors + M1-passing rows". v2's eligibility reads "Stage A pass". M2 will make v2 read the amendment measurement's pass rows as Stage A passes only if the author says so.

**Options.** 1. v2 eligibility = t7h8 PASS ∪ received `t7j10` PASS (as the amendment row says). 2. t7h8 PASS only.

**Recommendation: 1** (the amendment row records it as the author's decision).

**Draft row (sha filled after M2 and its review).**
```
| R1-EXAM-RULE-X5V2 (date) | `r1/exam/rules/x5_rule_v2.yaml` sha256 `<sha>` (from `proposals/X5_RULE_V2_DRAFT_20261104.md`; `always_on_in_b1: skip` per R1-EXAM-ALWAYS-ON-SKIP; eligibility includes the received A1 measurement's PASS rows per R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED) is frozen for Track X B1/B2, with code `<commit>` and review `reviews/MAC_M2_REVIEW_<date>.md`. `x5_rule_v1.yaml` stays as Stage A's rule. |
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

Items confirmed in R1-BX-PROPOSED-CONFIRM are not repeated. One line each: options → recommendation.

1. **R1-BX-D8-CONFIRM** — the numbers are accepted; the row waits for M11's gate-code sha. Draft: `| R1-BX-D8-CONFIRM (date) | Gate code `<path>` @ `<commit>`, sha256 `<sha>`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8) and R1-B7-PARTIAL-T1; T0 and T1 pooled with tier as a stratum. Sweep-2 label tables may be analysed from this row on. |` — **must be committed before any sweep-2 (T0 or T1) label table is copied back for analysis.**
2. **D6 exact API model** — R1-BX-PROPOSED-CONFIRM fixes the class (commercial mid-tier, another family than the pick's, not DeepSeek, cap €100–200). Recommendation: the author names the model and its version pin after X.7, once the pick's family is known.
3. **G.5 divergence STOP** (TRACK_G) — STOP if > X % of T1 label proposals diverge on a node. Recommendation: 20 % per node, node moves to T2 by author row.
4. **T0 never the held-out suite** in leave-one-suite-out — options: never / also as a secondary fold. Recommendation: never in the primary test; a T0-held-out fold reported as secondary.
5. **Probe A6** — R1-P3A-OOM-OPTION3 already uses it for the re-run decision (mean |Δ RPS| > 0.01). Recommendation: descriptive otherwise; no further row.
6. **Student-t details beyond E5** — when a floor counts as heavy-tailed. Recommendation: excess kurtosis of the 10-seed floor > 3 on ≥ 2 of the 3–5 representative edits; ν fixed at 5; declared in the G.3 selection row.
7. **Licence check (REVISIONS (e))** — result due from G.0 (HoreKa agent). Nothing to decide now.
8. **T1/T2 task lists (G.3)** — after the census. Nothing to decide now.
9. **Container route on run hosts** — Docker on deepthought known; 4090s, Ada and HoreKa 2 unchecked. Recommendation: the operator checks the 4090s and Ada in O0, the HoreKa agent checks HoreKa 2 in its scan; R1-BX-REVISIONS (g)'s order of preference applies.
10. **Phase C/D host plan** (B.4 pick row, C.2 on 1–2 T1 nodes, C.3, T2, API closed loop, A4 answers for T1) — Recommendation: plan after G.4 and B.7, as one row with the date recomputation.
11. **R1-SERVER-AGENTS-TWO (proposed)** — host lists (covered by (b)); amended rows (R1-HANDOVER-04NOV, R1-BX-PORTING-CONFIRM, R1-BX-REVISIONS (h), R1-ADA-CENSUS); the HoreKa agent's working mode (agent-partition node, author-opened tunnel). Recommendation: confirm in the (b) row or a one-line confirmation.
12. **R1-SERVER-AGENTS-TWO (open)** — G.0 raw-cost work on Ada for the fallback in the meantime (recommend: no, until the HoreKa scan says HoreKa 2 cannot run T1); Track S GPU nodes' own 4090 noise floor (recommend: yes — one GPU model per table, R1-BX-D5).
13. **R1-T1-HOREKA (proposed)** — `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` as the design basis; adopted only by a later row after the scan. Nothing to decide now.
14. **R1-1GC-FALLBACK (open)** — MLAgentBench light tasks as T1 and T2 candidates (recommend: yes, fixed in G.3); the 1GC extra tasks' tier and role (recommend: T2 only, outside the 12–16 count, always training-side in folds); domain coverage (recommend: decide in G.3 with the census).
15. **R1-BX-D10 (Track S manager on GPU nodes)** — committed after G.0/D28 (R1-BX-PROPOSED-CONFIRM). Nothing to decide now.

---

## Paste-ready message to the operator (after the author commits the rows he chooses)

> Read the plan from `mac-int-20261104` at `<commit>`. It integrates coordinator `10742f85`, `docs/runbooks-04nov` @ `c15b1102`, `codex/b2-repair-20261031`, Track S docs and the RUNBOOK §5 pin table. Your runbook is `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md` on that commit. No new server step is unlocked by M1 itself.
