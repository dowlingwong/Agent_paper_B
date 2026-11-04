# Independent review — R1-SERVER-AGENTS-TWO and operator runbook rev 3.2 (commit `6d72672a`)

**Reviewer:** a fresh AI agent (Claude), 4 Nov 2026. AI-assisted review, not human review. It changes no file other than this one.
**Scope:** `git show 6d72672a` (PLAN §10 row R1-SERVER-AGENTS-TWO; `prompts/OPERATOR_RUNBOOK_20261104.md` rev 3.2; `RUNBOOK.md`; `prompts/MAC_LOCAL_RUNBOOK_20261104.md`; `STATUS.md`), read against the rest of the tree at that commit: `prompts/TRACK_G_RUNBOOK.md`, `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md`, the PLAN §10 rows of 4 Nov, and the old O8 at `c6774025`.
**Line numbers** are those of each file at `6d72672a`.

## What the commit gets right

- The PLAN row quotes the 14:55 proposal and the 14:58 reply verbatim. It keeps the recording agent's consequences apart from the decision and marks them *(proposed)*.
- The new STATUS entry is accurate and short.
- §0.1's HoreKa 2 row now says "Not yours". §0.2 has "One operator per host". O6 points the T1 part of sweep 2 away from the operator. The O8 heading carries the decision's wording.
- Nothing added authorizes a run. "This runbook authorizes nothing" still stands, and no new note or EVIDENCE path appears.
- The review record (§4) has a 3.1 → 3.2 entry, and the old O8 text can be found at `c6774025`.

The split is still incomplete. The operator runbook keeps several live grants of T1 work, including the porting exception. RUNBOOK Track G, `TRACK_G_RUNBOOK.md` and Mac M10 still route G.0–G.6 to the operator. Some of the new text also decides questions that are still open.

## Findings

### BLOCKING

**B1. The operator runbook still makes the operator the porting agent and the agent for "all experiments".**
*Location:* `OPERATOR_RUNBOOK_20261104.md` line 5 (the intro paragraph). Line 3 (the revision header) still says "Track G becomes the critical path (O8), Ada takes the GPU-node census".
*Problem:* Line 5 still says the operator "runs all experiments of the current plan". It also grants "the one exception": porting the suites' task assets on `ops-trackg-<date>` ("review document §7 routes it to you"). That is exactly what R1-SERVER-AGENTS-TWO amends: "R1-BX-PORTING-CONFIRM (porting is done by the HoreKa agent, on HoreKa)".
Porting is code work, not a run, so "authorizes nothing" does not stop it. The operator can start it as soon as M10 step 0 lands. RUNBOOK G.1, TRACK_G G.1 and Mac M10 step 0 all tell it to do so (see M7–M9). Two agents could then port the same tasks onto different branches. That defeats the purpose of the row.
*Fix:* Rewrite line 5 as follows. The operator "runs the experiments on TASL-2, TASL-7, deepthought and Ada (see §0.2); HoreKa 2 and the T1 tier belong to the separate HoreKa agent (R1-SERVER-AGENTS-TWO)". Replace the porting exception with: "~~porting exception~~ — moved to the HoreKa agent (R1-SERVER-AGENTS-TWO amends R1-BX-PORTING-CONFIRM). You write no node assets." If the author wants the operator to port the Track S GPU nodes (see M10), mark that *(open)* and ask him. Add "(rev 3.2: superseded for T1 by R1-SERVER-AGENTS-TWO)" to the line-3 header.

### MAJOR

**M1. (a) The decision cell holds agent-drafted specifics beyond what the author approved, and its list of amended rows is incomplete.**
*Location:* `PLAN.md` line 804 (the R1-SERVER-AGENTS-TWO row); line 796 (the 14:22 open item).
*Problem:* The author approved a proposal to *draft* a row: "我起草交接修正行（两个服务器 agent，主机不重叠）… O8 改成'T1 归 HoreKa 线程'". The approved substance is: two server agents with disjoint hosts, and O8 becomes "T1 belongs to the HoreKa thread". The cell goes further and presents these as the author's decision:
- the exact host lists;
- "HoreKa 2 only";
- "porting is done by the HoreKa agent, on HoreKa" (R1-T1-HOREKA's list, "census, noise floors, proposer, sweep, audits", does not name porting);
- "the Mac-local agent stays the third thread";
- the list of amended rows.

The quoted proposal contains none of these. If the author saw them in chat before 14:58, that text is not quoted. Two more problems:
- **"HoreKa 2 only" against an open item.** Line 796 still records as *(open)* whether T1 uses legacy-HoreKa A100 nodes. The 14:37 return to HoreKa 2 is recorded only in STATUS, not in PLAN.
- **Incomplete list of amended rows.** It omits R1-BX-REVISIONS (h), which says "all server experiments go to the single SSH operator, including porting". R1-BX-PORTING-CONFIRM only confirms that row. It also omits the T1 parts of R1-ADA-CENSUS and R1-BX-PROPOSED-CONFIRM (the deepthought proposer for T1). Those are covered only by R1-T1-HOREKA's mapping, which calls itself "possibly incomplete".

There is also a wording slip: "Its operator runbook O8" should read "The operator runbook's O8".
*Fix:*
- Reduce the decision cell to what was approved, quoting the proposal.
- Move the host lists, "HoreKa 2 only", "on HoreKa" and the amended-row list into "Consequences noted by the recording agent" as *(proposed)*. Alternatively, quote the fuller chat proposal if the author saw it before 14:58.
- Add R1-BX-REVISIONS (h) to the list of amended rows.
- Raise "HoreKa 2 only" against the open 14:22 item with the author, and record the 14:37 return in PLAN.

**M2. (b) The host tables, O5 and the dependency summary still give the operator T1 work.**
*Location:* `OPERATOR_RUNBOOK` line 33 (§0.1 Ada row); line 95 (§0.3 deepthought row); line 96 (§0.3 Ada row); line 262 (STOP 5); line 367 (dependency summary).
*Problem:*
- **§0.1 Ada row (line 33).** It still reads "Work directories: under the census plan of O8". It still says, in bold, "**and the Track G census and GPU-node noise floors (O8 G.0), which R1-BX-D14 starts on Ada**". O8 G.0 no longer exists.
- **§0.3 Ada row (line 96).** Only the first clause is struck. ", while Track X holds TASL-2 (R1-BX-D14); later **the T1 label runs** (R1-BX-PROPOSED-CONFIRM)" stays live and bold, right after the italic note that says the opposite.
- **§0.3 deepthought row (line 95).** It still says "as the proposer host of the T1 runs (R1-BX-PROPOSED-CONFIRM)".
- **STOP 5 (line 262).** The author is still to decide whether the proposer runs on deepthought "for the T1 runs".
- **Dependency summary (line 367).** It still reads "host decision for the proposer (sweep 2 T0, T1 runs)".

*Fix:*
- Line 33: strike the census clause and set the work directory to "per the phase (O10 C.4; overflow)".
- Line 96: strike the whole old cell text after the italic note.
- Line 95: strike "and as the proposer host of the T1 runs" and add "(T1 proposer: HoreKa agent, R1-T1-HOREKA / R1-SERVER-AGENTS-TWO)".
- Lines 262 and 367: drop "T1".

**M3. (b) Ada's scope is narrowed beyond the decision, and O0's reason for the Ada census is stale.**
*Location:* `OPERATOR_RUNBOOK` line 37 ("Ada (fallback only)"); line 96 ("whole-table T1 fallback only"); line 115 (O0 step 1, "including Ada … for the Track G census"); against line 343 (O10 C.4 "on Ada") and line 374.
*Problem:* The decision says "Ada as fallback". R1-ADA-OVERFLOW is untouched, and C.4's debiased-memory A/B on Ada (RUNBOOK C.4, O10 step 3) still belongs to the operator. "Fallback only" in §0.2 would forbid both, which no author row says.
O0 still justifies the Ada census by "the Track G census". The census itself is still useful: for the fallback, for C.4 and for overflow. Only the reason is wrong.
*Fix:*
- §0.2: "Ada: overflow (R1-ADA-OVERFLOW) and C.4; for T1 only the whole-table fallback (R1-T1-HOREKA)".
- O0 step 1: "including Ada (for overflow, C.4 and the T1 fallback)".
- If the author meant "fallback only" literally, mark that *(open)* and ask him.

**M4. (Governance) An open item was deleted and replaced by a rule the author did not make.**
*Location:* `OPERATOR_RUNBOOK` line 319 (O8 item 2, "Until then nothing of T1 runs on Ada"); line 96 (the italic note "nothing of T1 runs here unless a row moves it"). Compare `c6774025`, old O8 "Hosts" paragraph.
*Problem:* The old O8 left this to the author: "*(open)* Whether Ada raw-cost work (G.0) continues while the HoreKa scan and setup are pending is the author's call". Rev 3.2 deletes the item and replaces it with a firm prohibition. R1-T1-HOREKA and R1-SERVER-AGENTS-TWO make Ada the whole-table fallback. Neither rules on raw-cost measurements there, and a fallback is only usable if its cost on RTX 6000 Ada is known (old G.0 measured "each GPU model available"; R1-BX-D5).
*Fix:* Restore the item as *(open)*, worded for the split: "Whether raw cost on Ada (for the fallback) is measured, and by which agent, is the author's call." Mark the "nothing of T1 runs on Ada" sentences *(proposed)*, or remove them.

**M5. (b)/(Governance) T2, D.3 and Phase C are given to the HoreKa agent without a decision, while C.2 on T1 nodes stays with the operator.**
*Location:* `OPERATOR_RUNBOOK` line 315 ("the T1/T2 closed loop"); line 320 (O8 item 3); line 355 (O11 "Proposers"); line 341 (O10 C.2 on "1–2 T1 nodes"); line 342 (C.3 "qualifying nodes"); line 374.
*Problem:*
- **T2 and the API proposer.** The decision covers "the whole T1 tier". Rev 3.2 also gives T2 and the API proposer's closed loop to the HoreKa agent, unmarked. Line 354 of the same phase says the D.3 hosts "follow the D.2 pre-declaration and the Phase C/D host plan (open)". That host plan is listed as still open in PLAN §10 (11:29).
- **C.2.** C.2 stays with the operator, yet it means T1-node campaigns and audits whose labels merge into the T1 table. One GPU model per table (R1-BX-D5) ties those labels to the T1 GPU model, which is H100 or the Ada fallback. C.2 is therefore T1 work as long as it is not reassigned.
- **C.3.** C.3's "qualifying nodes" may include T1 nodes.

*Fix:*
- Mark the T2 and API-proposer assignment *(open: Phase C/D host plan)*.
- In O10, mark C.2's task runs and audits on T1 nodes as "HoreKa agent (T1 GPU model) *(proposed)*, per the Phase C host plan", and C.3's T1 nodes the same way. Alternatively, put both to the author.

**M6. (c) Dangling references to O8 G.5, and no receiving path for T1 labels.**
*Location:* `OPERATOR_RUNBOOK` line 331 (O9: "Needs the label tables (O4, O6, O8 G.5)"); `MAC_LOCAL_RUNBOOK` line 450 (M14: "every label table the operator copies back (O4, O6, O8 G.5)"); `MAC_LOCAL_RUNBOOK` lines 73–81 ("Hand-off to the operator" and "Results from the operator", which expect only `ops-*` branches).
*Problem:*
- O8 G.5 no longer exists. The PLAN consequence routes T1 labels from the HoreKa agent to the Mac agent, but no runbook says where they arrive, on which branch, or who verifies them.
- O9 (A4) still makes the operator answer the A4 questions for every labelled proposal, T1 included, on a 4090. That may be right, but it is a T1-derived job, and nothing says it is meant.

*Fix:*
- Replace "O8 G.5" with "the HoreKa agent's T1 label table (copied back through the author or a pushed branch, after R1-BX-D8-CONFIRM)".
- Add "Hand-off to / results from the HoreKa agent" bullets to the Mac runbook §0.
- In O9, state *(proposed)* that the A4 answers for T1 proposals stay with the operator, or mark the question *(open)*.

**M7. (d) RUNBOOK Track G still assigns G.0–G.6 to the operator.**
*Location:* `RUNBOOK.md`:
- line 227: "the operator does G.0, the G.1 ports and smoke runs, G.1b and G.4–G.6 (OPERATOR O8)";
- the Host column of G.0, G.1, G.1b, G.4, G.5 and G.6 (lines 216–223: "Operator: Ada…", "Operator (ports, host smoke)", "Operator (+ API)");
- line 217: "The operator holds a scoped exception" and "porting exception is confirmed (R1-BX-PORTING-CONFIRM)", unmarked;
- line 220 (G.3) and line 221 (G.4): the proposer on deepthought for T1;
- line 19: R1-BX-PORTING-CONFIRM listed as decided, with no amendment;
- line 20: "the single SSH operator, both revision 3.1";
- line 51: the Ada host row, "first host of the Track G census".

*Problem:* The pointer on line 18 maps only "Ada → HoreKa 2". It does not map "operator → HoreKa agent", and it says nothing of the deepthought proposer. RUNBOOK ranks above the operator runbook (authority item 2), so an operator who reads line 227 meets a conflict. Its own rule then forces a STOP, and the rest of the Track G text points the wrong way.
*Fix:*
- Extend line 17 or 18: "Wherever Track G below names the operator for G.0–G.6, or deepthought/a 4090 as the T1 proposer host, read the HoreKa agent on HoreKa 2 (R1-SERVER-AGENTS-TWO)."
- Change line 227 to: "the HoreKa agent does G.0, the G.1 ports and smoke runs, G.1b and G.4–G.6 (its runbook follows the scan; operator O8 now holds only X.7's hand-over, the Ada fallback and D.3's T0 part)".
- Line 217 and line 19: add "(amended 4 Nov 14:58 by R1-SERVER-AGENTS-TWO: porting by the HoreKa agent)".
- Line 20: "the operator, rev 3.2, and the HoreKa agent".

**M8. (d) `TRACK_G_RUNBOOK.md` is untouched and contradicts the split.**
*Location:* `prompts/TRACK_G_RUNBOOK.md`:
- line 10 ("Who does what": the operator ports and runs the census, smoke runs, pilot, sweep and closed loop, "phase O8");
- the step headings at lines 47, 53, 61, 86, 90 and 98 ("(operator …)");
- line 49 ("the O0 census of Ada");
- line 51 (raw cost on "RTX 6000 Ada (first), RTX 4090, TITAN X");
- lines 5 and 55 (R1-BX-PORTING-CONFIRM, unmarked).

*Problem:* The Mac runbook names this file as a spec above itself (authority item 4). The operator runbook no longer points to it, but RUNBOOK G does ("holds the step detail"). It now describes an O8 that does not exist.
*Fix:* Add a 4 Nov 14:58 status note under line 5. It should say that G.0–G.1b and G.4–G.6 belong to the HoreKa agent on HoreKa 2, that the operator holds only X.7's hand-over and the Ada fallback, and that R1-BX-PORTING-CONFIRM is amended. Rewrite line 10 accordingly and change "(operator" to "(HoreKa agent" in the step headings. Mark the GPU-model list in G.0 *(open: Ada raw cost, see M4)*.

**M9. (d) Mac runbook M10 and packet (b) still hand the ports to the operator.**
*Location:* `MAC_LOCAL_RUNBOOK`:
- line 392 (M10 step 0: "Shared pieces for the operator's ports (… routes porting itself to the operator) … Hand the commit to the operator for G.1");
- line 400 (step 2: "the operator's ports (G.1, on `ops-trackg-<date>`)");
- line 406 (Done when: "gives the operator the commits for G.1 smoke and G.4");
- line 221 (the open list: "R1-BX-REVISIONS (h): the operator's scoped code exception");
- line 171 (packet (b), the still-open R1-HOSTS-04NOV draft: "Ada: overflow, **plus the Track G census and GPU-node noise floors (G.0)**", with no HoreKa 2 line).

*Problem:* The commit changed only line 12. The task that feeds the ports still routes them to the operator. Packet (b) is a live draft that will reach the author as a paste-ready row, and it contradicts both R1-T1-HOREKA and R1-SERVER-AGENTS-TWO.
*Fix:*
- In M10, replace "operator" with "HoreKa agent" in steps 0 and 2 and in "Done when", or add one pointer line: "Since 14:58 (R1-SERVER-AGENTS-TWO), read 'the HoreKa agent' wherever M10 says the operator for G.1, G.1b and G.4–G.6."
- Line 221: change the item to "porting exception, now the HoreKa agent's".
- Packet (b): drop Ada's census clause, add "HoreKa 2: the HoreKa agent, whole T1 tier", and mark the line as following R1-SERVER-AGENTS-TWO.

**M10. (c) Two cross-thread dependencies of the operator's own work are not recorded.**
*Location:* `OPERATOR_RUNBOOK` line 203 (O3 step 4, the Track S GPU nodes); PLAN line 809 (the hand-over consequence); `TRACK_G_RUNBOOK` line 36 and PLAN §10 11:29 "Still open" (the container check on the 4090 hosts and Ada).
*Problem:*
- **Track S GPU nodes.** These still run on the operator's hosts: "autoresearch short fixed-step; one high-noise RL-type task from the census". They need ported node assets and census results. Those used to be the operator's own G.1/G.1b output and are now produced by the HoreKa agent on HoreKa. R1-BX-PROPOSED-CONFIRM's D10 row is also "committed after the G.0/D28 results".
- **Missing hand-over.** The PLAN consequence lists only X.7's pins going to the HoreKa agent and T1 labels going to the Mac agent. It has no hand-over of ported nodes or census rows to the operator.
- **Container check.** The check on the 4090 hosts and Ada was part of the operator's G.0 and is not reassigned.
- **One GPU model per table.** A floor measured on H100 does not set σ̂ for a 4090 Track S table (R1-BX-D5), so the operator may need its own floor for those nodes.

*Fix:*
- Add a *(proposed)* consequence: the HoreKa agent's reviewed node assets (a pushed branch) and census rows pass to the operator through the author, for O3 step 4.
- Mark *(open)* whether the Track S GPU nodes need their own raw cost and noise floor on the 4090s.
- Keep the container check on the 4090 hosts and Ada with the operator, stated in O0 or O3.

### MINOR

**m1. (e) The amended rows are not marked where they are referenced.**
- **R1-HANDOVER-04NOV:** `OPERATOR_RUNBOOK` line 38 (the handover row, under the "one operator per host" bullet), line 85 ("Reading old markers") and line 111 (O0 Needs); `MAC_LOCAL_RUNBOOK` lines 150, 152 and 157 (packet (a)'s draft "the only agent acting on the servers").
- **R1-BX-PORTING-CONFIRM:** `RUNBOOK` lines 19 and 217; `TRACK_G_RUNBOOK` lines 5 and 55; `HOREKA_T1_JOBS_DRAFT` line 120.
- **R1-ADA-CENSUS:** not named in the runbooks, but applied without its name in `OPERATOR_RUNBOOK` line 33, `RUNBOOK` lines 11 and 51, and Mac packet (b). The HOREKA draft §0 (line 11) already lists it as a row to amend, which is adequate.

*Fix:* Add "(amended 4 Nov 14:58, R1-SERVER-AGENTS-TWO)" at each reference. For R1-ADA-CENSUS, add "(T1 part amended by R1-T1-HOREKA)" at the places that apply it without naming it.

**m2. (Governance) Agent additions in rev 3.2 are unmarked.**
*Location:*
- `OPERATOR_RUNBOOK` line 31: "working only from an `agent`-partition compute node through the tunnel the author opens" is *(proposed)* in PLAN.
- Line 315: "Its execution runbook is written after the read-only scan … and independently reviewed" is *(proposed)* in PLAN.
- Line 318: "is what the HoreKa agent qualifies on H100". The H100 qualification (J1b) is adopted only by a later row. "Report X.7's pins … to the author" is the *(proposed)* hand-over route.
- Line 322: "moves into the HoreKa runbook".
- Line 370: "H100 proposer qualification".

*Fix:* Mark each one *(proposed)*.

**m3. (c) The new T1 line of the dependency summary drops the gates the old chain carried.**
*Location:* `OPERATOR_RUNBOOK` line 370.
*Problem:* The old line carried these gates: M10 step 0's shared pieces, M10's pinned diff support (G.2), the author's G.3 row, the Mac agent's date recomputation, the G.5 authorization note, and R1-BX-D8-CONFIRM before T1 labels are analysed. The new line runs from "X.7" straight to "T1 labels ──► B.7".
*Fix:* Write the line as follows: "X.7 + M10 (shared pieces, G.2 pin) ──► HoreKa agent: ports, census ──► G.3 author row ──► pilot ──► Mac date recomputation ──► T1 sweep (note) ──► audits ──► R1-BX-D8-CONFIRM ──► T1 labels analysed ──► B.7 *(HoreKa runbook, after the scan)*".

**m4. (c) The pointer to old text covers only O8.**
*Location:* `OPERATOR_RUNBOOK` line 322.
*Problem:* The removed §0.1 HoreKa row is also only in git: the alias `hk2`, the user `ka_ir7683`, the downtime 23 Nov – 4 Dec, the rule of polling `squeue` at most once a minute, the *(proposed)* "the author submits, monitors and copies back until NHR@KIT confirms", and the pointer to `HOREKA_T1_JOBS_DRAFT`.
*Fix:* "(The 4 Nov §0.1 HoreKa 2 row and O8 are in git at `c6774025` …)".

**m5. (b) The escalation list still has a T1 trigger.**
*Location:* `OPERATOR_RUNBOOK` line 386: "A census result that changes the T1 list or the cost model by more than a factor of 2, or a T1 node whose divergence rate stays high".
*Fix:* Move it to the HoreKa runbook, or reword it for the operator's own census (Ada, TASL hosts, the Track S GPU nodes).

**m6. Headers and labels lag the change.**
- `MAC_LOCAL_RUNBOOK` line 1 still says revision 3.1, and §4 has no record of the line-12 edit.
- Line 12 lists the operator's hosts without Ada, although the PLAN row includes it.
- `OPERATOR_RUNBOOK` line 348 (the O11 heading, "T0, T1, T2") and line 350 ("Governs: … Track G G.6") now describe a T0-only phase.

*Fix:* Bump the Mac runbook to 3.2 with a review-record line, and add "Ada as fallback" to line 12. Rename O11 "D.3, T0 part".

**m7. The HoreKa job draft still speaks of "the operator".**
*Location:* `HOREKA_T1_JOBS_DRAFT_20261104.md` lines 33 and 72–78 ("The SSH operator does not act on HoreKa…", "The operator only analyses files…", "Only after a positive answer does the operator runbook get a HoreKa section").
*Problem:* The draft is the design basis for the HoreKa runbook. Under the split, these sentences mean the HoreKa agent and its own runbook.
*Fix:* Add a one-line note: "Since 14:58 (R1-SERVER-AGENTS-TWO), read 'the HoreKa agent' and 'the HoreKa runbook' for 'the operator' and 'the operator runbook' here."

## Answers to the five checks

- **(a) Faithful?** The core is faithful: two server agents with disjoint hosts, and O8 becomes "T1 belongs to the HoreKa thread". The decision cell, however, presents agent-drafted specifics as the author's decision, and its list of amended rows misses R1-BX-REVISIONS (h) (M1).
- **(b) No HoreKa or T1 work left?** No. T1 work remains in the intro and its porting exception (B1), in the §0.1 Ada row, in the §0.3 Ada and deepthought rows, at STOP 5 and in the dependency summary (M2), in O0's census reason (M3), in O9's "O8 G.5" (M6), in O10 C.2 (M5) and in the escalation list (m5). O6 and the HoreKa host row are clean. No reference to G.0–G.6 as operator steps survives inside O8 itself, but O9 still cites "O8 G.5".
- **(c) Nothing lost?** Most of it is recoverable from `c6774025`. Not all of it has a destination, though:
  - the Ada raw-cost open item was deleted (M4);
  - the T2 and C.2 owners are undecided (M5);
  - T1 labels have no receiving path (M6);
  - the ported nodes and census rows the operator needs for the Track S GPU nodes, and the container check, are not routed back to it (M10);
  - the dependency gates (m3) and the HoreKa host facts (m4) are dropped.
- **(d) RUNBOOK G, TRACK_G and Mac M10 consistent?** No. "The operator does G.0, the G.1 ports…" remains at RUNBOOK line 227 and needs both a pointer and a rewrite (M7). TRACK_G is untouched (M8). M10 still hands the ports to the operator (M9).
- **(e) The three rows marked as amended?** No. R1-HANDOVER-04NOV and R1-BX-PORTING-CONFIRM are unmarked at every reference outside PLAN. R1-ADA-CENSUS is applied without its name in three files (m1).

**Verdict: NOT ACCEPTED — 1 BLOCKING, 10 MAJOR, 7 MINOR.**

## Fixes applied (executing agent, 4 Nov)

All findings addressed in the follow-up commit: B1 (operator intro and porting exception), M1 (row trimmed; specifics moved to proposed/open consequences, including the 14:37 return to HoreKa 2), M2–M3 (host tables, Ada scope: overflow, C.4, T1 fallback), M4 (Ada raw cost restored as open), M5 (T2/API loop, C.2, C.3, A4 for T1 as open Phase C/D host plan), M6 (O9, M14 and result paths), M7 (RUNBOOK Track G host cells, G.3, G.4, execution line, banner), M8 (TRACK_G who-does-what and headings), M9 (Mac M10 and packet (a)/(b)), M10 (Track S GPU-node dependency and 4090 floor as open; container check owner open), m1 (amended rows marked where referenced), m2 (proposed markers), m3 (dependency gates restored), m4 (removed HoreKa row pointer), m5 (escalation removed), m6 (Mac rev 3.2 and record; O11 heading), m7 (HoreKa draft note).

## Round 2 — re-check of `7a63aead` (same reviewer, 4 Nov)

**Scope.** `git diff 6d72672a HEAD` (HEAD = `7a63aead`). The diff covers PLAN, RUNBOOK, the operator runbook (now rev 3.3), the Mac runbook (now rev 3.2), `TRACK_G_RUNBOOK.md` and the HoreKa job draft. I also grepped all four runbooks for any T1 work still assigned to the operator. Line numbers are those at HEAD. *(Note: the fix commit also committed this review file together with the executing agent's "Fixes applied" paragraph above. That is harmless; this section is appended uncommitted.)*

### Status of the round-1 findings

| Finding | Status | Evidence / residual |
|---|---|---|
| B1 | **Fixed** | Operator line 5 now limits the operator to TASL-2, TASL-7, deepthought and Ada. The porting exception is struck and passed to the HoreKa agent, and operator porting for Track S is marked *(open)*. The line-3 header notes that the census has moved. |
| M1 | **Fixed** | The PLAN decision cell (line 804) now holds only what the author approved. The host lists and the amended rows, now including R1-BX-REVISIONS (h), are *(proposed)* consequences. The open questions are listed as *(open)*. See R2-m2 for the 14:22 marker. |
| M2 | **Fixed** | The §0.1 Ada row (line 33), the §0.3 deepthought and Ada rows (lines 95–96), STOP 5 (line 262) and the dependency line (line 368) no longer give the operator T1 work. |
| M3 | **Fixed** | §0.2 (line 37) now gives Ada as "overflow, C.4, and the T1 fallback". O0 step 1 (line 115) gives the new reasons for the Ada census. |
| M4 | **Fixed** | Ada raw cost is restored as *(open)* in PLAN, in operator §0.1, §0.3 and O8 item 2, in RUNBOOK G.0 and in TRACK_G G.0. |
| M5 | **Partly fixed** | C.2 (line 342), C.3, O9's A4 answers for T1 proposals (line 329), O11 (lines 349 and 356), RUNBOOK G.6 and TRACK_G G.6 are now *(open)*. The O8 intro (line 315) says T2 belongs to the Phase C/D host plan. **Residual:** O8 item 3 (line 321) still says "its T1/T2 part is the HoreKa agent's". This contradicts the line above it and O11. It takes work away from the operator rather than giving it any, so the residual is downgraded to R2-m1. |
| M6 | **Fixed** | O9 (line 332) and M14 (Mac line 451) now cite "the HoreKa agent's T1 tables". The Mac runbook's "Results from the server agents" adds the *(proposed)* `hk2-*` branches. |
| M7 | **Mostly fixed** | The line-18 pointer now covers "operator" and the deepthought/4090 proposer. Line 19 marks PORTING-CONFIRM as amended, and line 20 is corrected. The G.0–G.5 Host cells name the HoreKa agent, G.6 is *(open)*, and line 227 is rewritten. **Residuals:** see R2-m3. |
| M8 | **Mostly fixed** | Line 10 tells the reader to read "operator" as "HoreKa agent". The G.0–G.5 headings and step G.1.2 now name the HoreKa agent, G.6 is *(open)*, and line 55 marks PORTING-CONFIRM as amended. **Residuals:** see R2-m4. |
| M9 | **Mostly fixed** | M10 step 0's hand-off, step 2's ports and "Done when" now name the HoreKa agent. The line-221 open list and packet (b), with its Ada and HoreKa 2 lines, are corrected. **Residual:** see R2-m5. |
| M10 | **Fixed** | PLAN now lists *(open)* items for the Track S GPU nodes and their 4090 floor, and for the owner of the container check. Operator O8 item 4 records the hand-over through the author. |
| m1 | **Partly fixed** | The amendment is now marked at operator line 38, Mac line 156, RUNBOOK lines 19 and 217, TRACK_G lines 5 and 55, operator line 33 and Mac packet (b). **Residual:** see R2-m6. |
| m2 | **Fixed** | *(proposed)* markers are on lines 31, 315, 318, 323 and 371. |
| m3 | **Fixed** | The dependency line (line 371) restores the M10 shared pieces, the G.2 pin, the G.3 row, the date recomputation, the G.5 note and R1-BX-D8-CONFIRM. |
| m4 | **Fixed** | The footnote (line 323) now covers the old §0.1 HoreKa row. |
| m5 | **Fixed** | The T1 escalation trigger is removed. |
| m6 | **Fixed** | The Mac runbook is at rev 3.2 with a review-record entry. Line 12 adds Ada. The O11 heading reads "T0 here". |
| m7 | **Fixed** | The HoreKa draft has a line-3 note: "the operator" acting on HoreKa now means the HoreKa agent. |

### Residual and new findings (all MINOR)

- **R2-m1 (residual M5).** Operator line 321: "its T1/T2 part is the HoreKa agent's". *Fix:* "its T1/T2 part follows the Phase C/D host plan *(open)*".
- **R2-m2 (new).** PLAN line 796 now opens with "*(superseded at 14:37 …)*" as a plain fact. The 14:37 message moved the *scan* target. The item's own last sentence leaves H100 against A100 to be decided after the scan. The new consequence on line 807 states the same supersession as *(proposed)*, so the two places disagree in status. *Fix:* write "*(superseded at 14:37 for the scan target; for the T1 host, see the (proposed) consequence of R1-SERVER-AGENTS-TWO)*".
- **R2-m3 (residual M7).** Three residuals in RUNBOOK:
  - The G.0 cell (line 216) still ends with "**Ada first**, while Track X holds TASL-2; Ada is checked for Paper A occupancy first", which contradicts the "on HoreKa 2 H100" earlier in the same cell. *Fix:* strike that sentence.
  - G.1 (line 217) still names the porting branch `ops-trackg-<date>`. TRACK_G (line 57) proposes `hk2-trackg-<date>`, the Mac runbook proposes `hk2-*`, and `ops-*` is the operator's namespace, which the Mac agent reads as operator output. *Fix:* "its own branch (proposed `hk2-trackg-<date>`)".
  - Lines 11 and 51 still call Ada the "first host of the Track G census". The line-18 pointer covers this reading, so this is cosmetic. *Fix:* optionally mark both with "(moved, R1-T1-HOREKA)".
- **R2-m4 (residual M8).** Two residuals in `TRACK_G_RUNBOOK.md`:
  - Line 49 still makes the operator's O0 census of Ada a precondition of G.0 ("Before G.0 starts on Ada …"). *Fix:* strike it, or recast it as the fallback's precondition.
  - Lines 35–36 send the container checks to "the 4090 hosts and Ada in G.0". Under line 10's blanket "read operator as HoreKa agent", this would put the HoreKa agent on the operator's hosts, against the disjoint-host rule, while PLAN leaves the owner *(open)*. *Fix:* "the container check on the 4090 hosts and Ada: owner *(open)*, PLAN R1-SERVER-AGENTS-TWO consequences".
- **R2-m5 (residual M9).** Mac line 393: the heading of M10 step 0 still reads "Shared pieces for the operator's ports (… routes porting itself to the operator)". Mac line 401 still says "do not edit the operator's branch". *Fix:* write "the HoreKa agent's ports" and "the HoreKa agent's branch".
- **R2-m6 (residual m1).** Three places still lack an amendment marker:
  - R1-HANDOVER-04NOV is unmarked at operator line 85 ("Reading old markers") and line 111 (O0 Needs). Mac lines 150 and 152 cite only its editor clause, which the amendment leaves untouched, so they are acceptable.
  - The HoreKa draft line 122 lists "R1-BX-PORTING-CONFIRM" as a need, unmarked. The line-3 note covers it only indirectly.
  - RUNBOOK lines 11 and 51 apply R1-ADA-CENSUS without naming it (see R2-m3).

  *Fix:* add "(as amended by R1-SERVER-AGENTS-TWO)" in each place.
- **R2-m7 (new).** Operator O8's list (lines 318–321) is numbered 1, 4, 2, 3. *Fix:* renumber it.

### Grep for T1 work still assigned to the operator

- **Operator runbook:** no live grant remains.
  - The remaining T1 mentions are pointers to the HoreKa agent (lines 5, 31, 37, 266, 313–323, 332), *(open)* items (lines 329, 342, 349, 356), rules or descriptions (lines 56–57; line 310, "Stage D is one round on 1–2 T1 nodes", which describes Track P scope), and the history in §4.
  - Line 321 (R2-m1) gives work away rather than to the operator.
- **RUNBOOK Track G:** no Host cell names the operator. The G.0 "Ada first" sentence (R2-m3) is the only text that still implies the operator's host.
  - Outside Track G, the Phase C row C.2 (line 346) and the Phase D row D.3 still name deepthought or a 4090 host for T1-node work. Both are qualified "to be planned", which matches the *(open)* host plan, so I raise no finding.
- **TRACK_G_RUNBOOK:** after line 10's re-reading rule, only line 49 and lines 35–36 (R2-m4) still tie T1 work to the operator's hosts.
- **Mac runbook:** only the step-0 heading and step 2's "operator's branch" (R2-m5) remain. The other "operator" mentions concern T0, Track S, B.2, O9, O10 and O11 work, all of which is still the operator's.

**Verdict (round 2): ACCEPTED. No BLOCKING or MAJOR finding remains open. Seven MINOR items (R2-m1 … R2-m7) should be applied, and they need no further review round.**
