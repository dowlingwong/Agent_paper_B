# Independent review, round 2: Paper C plan addendum of 19 Nov 2026 and PLAN §10 author rows

**AI-assisted (Claude, the round-1 independent reviewer; did not write the amendment).**
- **Reviewed:** commit `0edd7205` on `paperc-plan-amend-20261119`, against round 1 at `946d8120` (`git diff 946d8120 0edd7205`).
- **Files:** `paperC/docs/PLAN_ADDENDUM_20261119.md` (cited as "add."), `docs/r1/PLAN.md` lines 1195–1209, `paperC/README.md`, and the response `PLAN_ADDENDUM_20261119_RESPONSE_R1_20261119.md`.

**VERDICT: NOT ACCEPTED** (1 MAJOR, 8 MINOR)

The revision fixes every round-1 finding in substance. The [recorder]/[correction] marking and §G are an acceptable way to keep the record faithful while giving the executor working defaults (see "Question 3" at the end). One gap blocks acceptance: §B and row R1-PAPERC-RESTORE now state new restore-gate rules as author decisions, unmarked, in place of what the author actually decided ("replay check gating SPT-3 data"). The fix is only marking.

---

## Round-1 findings

| # | Round 1 | Status | Note |
|---|---|---|---|
| 1 | "Round A" consequences; stakes data source; regret clause | **Resolved** | add. 84–85, 120–122; G1–G3; rows 1202/1204 agree |
| 2 | Replay reference and failure path undefined | **Resolved in substance** | add. 150–168 define an A/A replay against the root's live continuation, step-wise match, both arms restored, timing and STOP. Marking: see new finding 1 |
| 3 | K deviation undisclosed; T1 conditional | **Resolved** | add. 100–103 [correction]; G10; row 1203; preamble 1197 |
| 4 | Undecided core-scope sentence | **Resolved** | add. 128; row 1204 "此处不预先决定核心版的任何部分" |
| 5 | Multiplicity, statistic 2, sensitivity, Q3 scope, §9.1 | **Resolved**; G4 needs a default | add. 50–58; G4, G5. See new finding 5 |
| 6 | N6-floor rationale | **Resolved** | add. 70 |
| 7 | SPT-1 cost and set-up | **Resolved**; one wording residue | add. 48, 72–75; G6. 9.6k / 15.6k and 381 forks check. See new finding 8 |
| 8 | Three citations | **Resolved** | add. 64, 65, 91 (58–80 % checks against census §5) |
| 9 | Undefined quantities | **Resolved**; two follow-ups | add. A.0 (31–41). See new findings 3 and 4 |
| 10 | OPE clusters | **Resolved**; the empty-cluster default needs a guard | add. 132–134, 142–143, 125. See new finding 6 |
| 11 | Equivalence details | **Resolved** | add. 97, 99, 104 |
| 12 | Parse failures; informative truncation | **Resolved**; one wording residue | add. 175–177. See new finding 7 |
| 13 | Seeds for (a); proposer for (b) | **Resolved** | add. 116–119; G8 |
| 14 | Forward-referenced pin; cross-references | **Resolved** | add. 221–226; row 1209 |
| 15 | Unconfirmed additions; naming; memo | **Resolved** | The author's confirmation in chat cannot be verified from the repository, but it is now stated and attributed (add. 212, 225). Paper D is named; A2 is renamed; the memo and the review are cited by private Claude Docs links (add. 5, 211) |
| 16 | P-numbers; README | **Resolved** | add. 22–25; README lines 3–4, 73 |

---

## New findings

### 1. MAJOR — The restore-gate rules are unmarked in §B and row 1206, and they replace the author's wording
- **Where:** add. 150, 158–165; PLAN line 1206.
- **Problem:** The author decided "a replay check gating SPT-3 data" (round-1 row: "一致率达到…门槛之前，该节点的 SPT-3 fork 数据不使用"). The revision states the following as decided, without [recorder]/[记录者]:
  - the replay is an A/A replay under the root's behaviour component (B.3);
  - the step-wise match criterion (B.4);
  - the check runs **before SPT-1's go/no-go is read** (header line 150; B.5);
  - below the threshold the run STOPs, and **all** of the node's fork data, including SPT-1's, are withheld from τ̂², N6 and OPE (B.6).

  Row 1206 no longer contains the SPT-3 gate the author decided. These rules came from round-1 finding 2 and are technically sound. But under the recorder's own convention (add. 5–9) they are operational readings and extensions. Only the go/no-go consequence (G9) is listed in §G. This is the "presented as decided when it is not" case.
- **Fix:**
  - Mark B.3–B.6 [recorder], and keep the author's decision visible in one sentence ("author: the replay check gates SPT-3 fork data").
  - Add a §G row, for example: "G12 — replay definition (A/A against the root's live continuation), step-wise match, timing before SPT-1's go/no-go, STOP and withholding of all fork data | as written in §B".
  - In row 1206, add "[记录者]" to the same clauses and restore the SPT-3 gate as the author's wording.

### 2. MINOR — Other unmarked recorder text in author rows
- **Where:** add. 57; PLAN 1201 ("通过 go/no-go 不作为存在余量的证据"); add. 226 and PLAN 1209 (merge procedure).
- **Problem:** The rule that a passed go/no-go is not reported as evidence of headroom is a reporting rule the author did not state. The rebase-before-merge instruction is the recorder's housekeeping, but it sits inside an author row.
- **Fix:** Mark both [recorder]/[记录者] (and add them to G11), or move the merge instruction out of the row into §F only.

### 3. MINOR — g and h collide with plan §7.1's tuned (g, h)
- **Where:** add. 38, 40, 82–83, 132; plan line 271 ("N1 | tuned static thresholds (g, h)").
- **Problem:** In the plan, g and h are N1's (and N2's) **tuned** thresholds. In A.0 they are a **declared** price and a declared keep threshold. A.2 line 82 separates the two for g only. An executor writing the SPT-1 pre-declaration and tuning N1 meets two different h's under one symbol.
- **Fix:** Add one sentence to A.0: "g and h here are declared constants, distinct from N1's tuned (g, h) of plan §7.1". Better still, rename them (for example g_decl, h_decl) throughout A.2, A.5 and rows 1202/1205.

### 4. MINOR — The decision-regret criterion is not computed on SPT-1 data
- **Where:** add. 41, 83–84; PLAN 1202.
- **Problem:** A.0 defines decision regret as C1's frozen `decision_regret` (a node-level 30-seed quantity). A.2's "Data" line says the gate is computed on SPT-1's pilot campaigns. The share and the kept increments come from SPT-1; the regret alternative comes from C1.
- **Fix:** In A.2 "Data", add: "the decision-regret alternative uses C1's frozen node value (A.0)".

### 5. MINOR — §G: defaults and deadlines
- **Where:** add. 231, 238, 240.
- **Problem:**
  - Line 231 says "The default holds until the author changes it", but G4 and G6 give "not stated" as the default.
  - G4 does have a default in the plan: §11.2 (plan line 396), Holm across the **two** E-T0 nodes. The recommendation would change that default.
  - Several open points must be settled before a pre-declaration freezes (G7 before SPT-1; G6 before SPT-3; G4 before SPT-5/SPT-6). Otherwise a recorder default becomes binding without the author.
  - The go/no-go does not say whether a check on an epoch that failed A.2, or on a node below A.4's floor, may open the gate (add. 51 vs 85, 120).
- **Fix:**
  - G4 default: "plan §11.2 (both nodes, Holm over 2); recommendation: passing nodes only".
  - G6 default: "N1 and N0, r = 2" (or state "must be decided before the SPT-3 pre-declaration").
  - Add a "decide before" column to §G.
  - Add G13: "do go/no-go checks on epochs or nodes excluded by A.2/A.4 count?" (suggested default: no).

### 6. MINOR — The empty-cluster default can hide extrapolation by the target policy
- **Where:** add. 134; PLAN 1205.
- **Problem:** "A cluster with no eligible decisions is reported as empty, not as a shortfall" judges emptiness on behaviour data. A candidate policy can still reach that cluster. For example, a budget-conserving learner can reach (E2, region, more than half the runs left) late in a campaign, where no behaviour component went. Runbook phase P7's report itself notes that behaviour diagnostics "cannot assess states that no behaviour campaign visits".
- **Fix:** Default: "empty only if no candidate's dev campaigns visit it either; otherwise insufficient data". Update G11 to match.

### 7. MINOR — The truncation list no longer matches "the plan's rules"
- **Where:** add. 175.
- **Problem:** The line says "Truncation keeps the plan's rules", but its list drops plan §3.1's "parse failure beyond retry". Line 176 covers only parse failures charged as invalid trials, so an uncharged parse failure is left unclassified.
- **Fix:** Restore the item as "parse failure beyond retry, where the pinned harness does not charge it as an invalid trial".

### 8. MINOR — Wording residues
- **Where and fix:**
  - add. 77: line 75 now says detection at 60 forks is optimistic, so "unless a real channel is about as strong as … interaction (0.49 σ) or keep_feedback (0.78 σ)" overstates. Write "possibly even then".
  - add. 34: "Track S's comparison-noise unit" can be confused with census §3.1's "comparison noise sd(Δ̂ − Δ_audit)" (3.0 σ_node on digits). Write "Track S's noise unit".
  - add. 48: tuning N1 on development instances before SPT-1 costs real-node campaigns. Include it in the recomputed SPT-1 cost (line 74).

---

## Question 3: is the [recorder]/[correction] + §G approach acceptable?

Yes, as a record with open points, provided three conditions hold.
- **Everything not decided is marked.** New finding 1, and finding 2 for the smaller items.
- **Each §G item has a real default and a deadline before the pre-declaration that depends on it.** New finding 5.
- **English and Chinese carry the same marks.** They do: the marks and the preamble at 1197 agree, and §G is referenced from the rows.

Under these conditions the PLAN rows record what the author decided, and the defaults stay visible as the recorder's. It also stays clear which pre-declaration would freeze them. The decision memo and the directions review are cited as private Claude Docs links (add. 5, 211), so faithfulness cannot be checked from the repository. The marking is what makes that acceptable.

## Checked in round 2 (no change needed)
- **Numbers and sources:**
  - SPT-1 fork calls 60 × 2 × 4 × 20 = 9,600; total 6,000 + 9,600 = 15,600;
  - 381 mean forks in strict_null;
  - OpenML other than climate: 58–80 % and 0.08–0.18 σ_d;
  - theory note: 59.34 %;
  - census §1: σ_d = 1.87 σ_node on tabular;
  - S0.5 keep rule m̂ > 0 (h = 0);
  - R1-BX-D3 conditionality;
  - R1-SWEEP1-CLASSIFY's restriction to 7006–7010.
- **Every [recorder]/[correction] mark in the addendum maps to a §G row:**
  - G7: lines 38 and 40;
  - G5: line 52;
  - G2: line 84;
  - G1: line 85;
  - G10: line 103;
  - G11: line 104;
  - G8: line 119;
  - G1 and G3: lines 121–122;
  - G11: line 134;
  - G9: line 165;
  - G11: line 177.
- **Rows:** 1201–1209 match the English text, apart from new finding 1 and finding 2.
- **README:** the status line and the Extension line are fixed.
