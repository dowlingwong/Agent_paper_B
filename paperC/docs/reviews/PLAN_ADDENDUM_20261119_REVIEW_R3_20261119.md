# Independent review, round 3: Paper C plan addendum of 19 Nov 2026 and PLAN §10 author rows

**AI-assisted (Claude, the independent reviewer of rounds 1 and 2; did not write the amendment).**
- **Reviewed:** commit `78478676` on `paperc-plan-amend-20261119`, against round 2 at `0edd7205` (`git diff 0edd7205 78478676`).
- **Files:** `paperC/docs/PLAN_ADDENDUM_20261119.md` (cited as "add."), `docs/r1/PLAN.md` lines 1195–1211, and the response `PLAN_ADDENDUM_20261119_RESPONSE_R2_20261119.md`.

**VERDICT: ACCEPT** (0 MAJOR, 2 MINOR; the recorder may fix the minors after acceptance)

**Correction noted.** The round-1 request summarised the author's restore decision as "a replay check gating SPT-3 data". The coordinator has since said that this was its own draft. The author's decision, as now recorded, is: restore the random-stream positions when a fork restores a state, and compare a run continued "as is" from the restored state with the original run. Round-2 finding 1 was framed against the earlier wording. Its point still stands, and it is now met: the record keeps the author's decision separate from the recorder's check definition. I cannot verify the chat. I take the author's wording as the coordinator and the recorder state it.

---

## Round-2 findings

| # | Round 2 | Status | Where |
|---|---|---|---|
| 1 | MAJOR: restore-gate rules unmarked | **Resolved** | add. 157 states the author's decision, and it is confined to item 1 and the core of item 3. Items 2–6, the timing and the gate are marked [recorder] (add. 160–169) and listed as G12 (add. 250). Row 1206 states the author's decision first, then "以下为记录者补出的检查定义 [记录者，addendum §G12]" |
| 2 | Other unmarked additions | **Resolved** | add. 58 [recorder, §G11]; row 1201 [记录者]. The merge instruction is marked [recorder: housekeeping] in §F (add. 230) and moved out of row 1209 into a recorder's note below the table (PLAN 1211) |
| 3 | g, h clash with plan §7.1 | **Resolved** | add. 41; row 1202 |
| 4 | Regret data | **Resolved** | add. 85; G2; row 1202 |
| 5 | §G defaults and deadlines | **Resolved**, with one residue (finding 1 below) | "Decide before" column (add. 237–251). G4 default is plan §11.2; G6 default is N1/N0 with r = 2; G7 is declared in SPT-1. G13 added. The PLAN preamble (1197) says open points are settled before the named pre-declaration |
| 6 | Empty-cluster default | **Resolved** | add. 135; G11; row 1205 |
| 7 | Truncation list | **Resolved** | add. 179; row 1207 |
| 8 | Wording | **Resolved** | add. 34, 75, 78 |

Nothing in the revision changes a number. The English addendum and the Chinese rows agree, including all [recorder]/[记录者] and [correction]/[更正] marks. Every mark maps to a §G row.

## MINOR (non-blocking; for the recorder after acceptance)

### 1. G13's default is not written in A.1 or row 1201
- **Where:** add. 52 (A.1 item 5), add. 251 (G13), PLAN 1201.
- **Problem:** G13's column is headed "Default written above", and its default is "no": checks on an epoch that failed A.2, or on a node below A.4's floor, do not open the gate. But A.1 item 5 and row 1201 still read "if either statistic passes on either E-T0 node". The two texts disagree until the default is written in.
- **Fix:** Append to A.1 item 5: "[recorder, §G13: checks on an epoch that failed A.2, or on a node below A.4's floor, do not count; statistic 2 then sums only the epochs still controlled]". Add the matching [记录者] clause to row 1201.

### 2. The change summary for §B still presents the recorder's check as the change
- **Where:** add. 13 ("an A/A replay at fork points before fork data are used").
- **Problem:** §B and row 1206 now separate the author's decision from the recorder's check definition and gate. The summary line does not.
- **Fix:** Reword the line to: "restore random-stream positions in fork snapshots and compare an 'as is' continuation from the restored state with the original run (author); the replay definition and the gate on fork data [recorder, §G12]".

## On acceptance as a record with open points

Accepting the amendment means:
- **What is accepted.** The amendment is accepted as the record of the author's 19 Nov decisions. Everything the author did not decide is marked as a recorder default, listed in §G with a deadline, and the Chinese rows carry the same marks.
- **What is not decided.** The §G defaults are not author decisions. Each must be confirmed or changed before the pre-declaration named in its "Decide before" column: G2, G5, G7, G10, G11 and G13 before the SPT-1 pre-declaration; G9 and G12 before B11's runbook.
- **Before merging.** The rebase of the 15 Nov and 19 Nov Paper C sections into `main`'s §10 (add. 230; PLAN 1211) remains a precondition for merging. This review does not cover it.
