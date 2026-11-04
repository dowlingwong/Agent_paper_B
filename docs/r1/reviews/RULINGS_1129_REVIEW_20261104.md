# Review — PLAN §10 "4 November 2026 (11:29)" rulings and runbooks rev 3.1 (4 Nov 2026)

**Reviewer:** independent fresh agent (Claude), AI-assisted. Documents only; no run started, nothing pushed or committed.
**Scope:** commit `467b92d2` (`git diff ce9dd812 467b92d2`) on `docs/runbooks-04nov`: `docs/r1/PLAN.md`, `docs/r1/RUNBOOK.md`, `docs/r1/STATUS.md`, `docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md`, `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md`, `docs/r1/prompts/TRACK_G_RUNBOOK.md`.
**Source of truth for what was adopted:** the chat session's 11:21 recommendation list (A1–H1) and the author's 11:29 reply: "1. 1GC-7RC 仓库是什么仓库，不要说黑话 2. apptainer在deepthought2 3. T1是什么，为什么这么久 4. 其他决定按照你的建议来 5. 标 ⚠ 的缺口，你现在补".

## Summary

| Class | Count |
|---|---|
| BLOCKING | 0 |
| MAJOR | 7 |
| MINOR | 10 |

Most rows are faithful to their recommendation: R1-BX-PORTING-CONFIRM (A2), R1-ADA-CENSUS (A3), R1-EXAM-ALWAYS-ON-SKIP (B1), R1-EXAM-B1-HARNESS-PIN (B3), R1-P3A-OOM-OPTION3 (G1), and the D3, D4, D7, D8, D13, REVISIONS (f) and D14 bullets of R1-BX-PROPOSED-CONFIRM. No document authorizes a run. Seeds 7006–7010 are used only for evaluation, and the D3 check is restricted to 7001–7005. The problems are that some rows add to, or change, what was adopted; one runbook task drops an author gate; and several of the newly filled gaps either lack a host or contradict the canonical RUNBOOK.

## Recommendation → row map (check (a))

| Rec | Recorded as | Verdict |
|---|---|---|
| A1 | R1-HANDOVER-04NOV | Faithful to packet (a), except that it omits naming the b2-repair out-of-scope files (m8) |
| A2 | R1-BX-PORTING-CONFIRM | Faithful |
| A3 | R1-ADA-CENSUS | Faithful |
| A4 | R1-1GC-FALLBACK | Adoption is uncertain (MAJOR-1); substance added (MAJOR-2); "first day" dropped (m6) |
| A5 | R1-APPTAINER-HOST | Faithful to the author's item 2; one consequence is not listed as open (m4) |
| A6 | R1-BX-PROPOSED-CONFIRM | Confirms everything at once instead of item by item; covers items the list never mentioned (MAJOR-2) |
| B1 | R1-EXAM-ALWAYS-ON-SKIP | Faithful |
| B2 | Not in PLAN (Mac runbook note only) | m3 |
| B3 | R1-EXAM-B1-HARNESS-PIN | Faithful |
| C1 | R1-B2-REPLAY-GO | Substance faithful; e2 wording is ambiguous (m5) |
| D1, D2 | PROPOSED-CONFIRM D8 bullet | Faithful |
| D3, E4 (K subsets) | D3 bullet | Faithful in PLAN; M12 drops the author's commit of the protocol (MAJOR-5) |
| E1, E2 | REVISIONS (f) bullet | Faithful |
| E3 | D4 bullet | Faithful |
| E4 | Track G bullet | Faithful, but the bullet adds the G.5 divergence STOP (MAJOR-2) |
| E5 | REVISIONS (c) bullet | Faithful, except for an added gloss "(executed, not kept)" (MAJOR-2) |
| F1 | D7 bullet | Faithful |
| F2 | D13 bullet | Faithful |
| F3 | D6 bullet | Cap changed; constraints dropped (MAJOR-3) |
| G2 | Track P bullet; M13 | The ΔRPS rule is faithful; "T0 never held out" and "A6 descriptive" are added (MAJOR-2) |
| G3 | R1-TRACKS-S01-RERUN | Faithful; one wording issue (m7) |
| G4, G5 | D10 bullet | The timing condition is dropped (MAJOR-4) |
| H1 | D8 and D14 bullets | Faithful in substance; T1 question pending (MAJOR-1); the "write it into D8-CONFIRM" part is not explicit (m3) |

## MAJOR

**MAJOR-1. The author's reply is quoted selectively, and two adoptions depend on questions he had just asked.**
*Location:* the preamble of PLAN §10 "4 November 2026 (11:29)"; R1-1GC-FALLBACK; R1-BX-PROPOSED-CONFIRM (D8 fallback and D14 bullets); the STATUS entry.
*Finding:* The record quotes only items 2 and 4 of a five-item reply. It omits item 1 ("1GC-7RC 仓库是什么仓库，不要说黑话", which asks what the repository is), item 3 ("T1是什么，为什么这么久", which asks what T1 is and why it takes so long) and item 5 (fill the ⚠ gaps now). Item 4 adopts the "other" decisions. Items 1 and 3 are questions about the subjects of A4 (the 1GC-7RC fallback) and of the T1 timeline (H1: B.7 ≈ 8 Dec, and the R1-BX-D14 dates). Recording A4 and H1 as adopted, without saying that the author had just asked about them, goes beyond the record. Item 3's "why so long" may also signal a reservation about the dates.
*Fix:* Quote the full 11:29 reply verbatim. State that items 1 and 3 were questions, and link where they were answered. Mark R1-1GC-FALLBACK and the H1 items (the B.7 fallback and the D14 bullet) as "adopted under item 4; the author's confirmation after the explanation of items 1 and 3 is pending", or get his one-line confirmation before treating them as decided.

**MAJOR-2. R1-BX-PROPOSED-CONFIRM and R1-1GC-FALLBACK add substance the 11:21 list did not contain.**
*Location:* the Track G, Track P and REVISIONS (c) bullets and the opening sentence of R1-BX-PROPOSED-CONFIRM; R1-1GC-FALLBACK.
*Finding:* A6 recommended "逐项确认" (confirm item by item), with the values in sections D–H. Instead the row opens with a blanket "the *(proposed)* items … are confirmed as written". It then records as decided several items that appear nowhere in A1–H1:
- "G.5 STOPs if a node's divergence rate exceeds twice its census rate" (a *(proposed)* item of TRACK_G_RUNBOOK G.5 and packet (j));
- "T0 is never the held-out suite in leave-one-suite-out" (TRACK_P §3.6 *(proposed)*);
- "E6 probe A6 is descriptive" (TRACK_P §5.6 *(proposed)*).

G2 says only "E6 A6 量化, |ΔRPS| ≤ 0.01 不重跑" (quantify A6; no re-run if |ΔRPS| ≤ 0.01).

Two further additions:
- R1-1GC-FALLBACK lets the 1GC datasets serve "under another suite's label". A4 said only "可以作为额外任务，但不算 suite" (they may be extra tasks, but do not count as a suite). Placing them under another suite's label changes how the folds of the primary leave-one-suite-out analysis are composed.
- REVISIONS (c) glosses u = −g as "(executed, not kept)", which is not in E5.

*Fix:*
- Replace the blanket sentence with an enumerated list. Each confirmed *(proposed)* or *(open)* item should name the recommendation (D1…H1) that adopts it.
- Move the G.5 divergence STOP, "T0 never held out" and "A6 descriptive" to "Still open". Leave their *(proposed)* markers in place.
- In R1-1GC-FALLBACK, use A4's words: "their public datasets may be used as additional tasks, disclosed; they do not count as a suite". Drop "under another suite's label".
- Drop the "(executed, not kept)" gloss, or source it to an existing row.

**MAJOR-3. D6 (the API proposer): the cost cap is changed and adopted constraints are dropped.**
*Location:* the D6 bullet of R1-BX-PROPOSED-CONFIRM.
*Finding:* F3 recommended "先批 €100–200 成本上限" (an initial cap in the €100–200 range). The row fixes it at €200, which is a monetary decision the author did not make. F3 also adopted three constraints that the row omits: calls only from the host the authorization note names, with the full request and the model version logged; and use for closed-loop evaluation only. The row also adds a deadline that F3 did not set ("names the exact model and version before G.6"). R1-BX-D6's *(open)* items on host and request log are therefore neither resolved in the PLAN nor listed as open, although the §10 index claims that all *(open)* items are resolved.
*Fix:* Record the cap as "an initial cap of €100–200, revised after G.4's measured token counts", and add the exact figure to "Still open". Add F3's constraints on host, logging and closed-loop use. Drop "before G.6", or mark it as a suggestion.

**MAJOR-4. D10 (the Track S GPU-node manager): the recommendation's timing condition is dropped.**
*Location:* the D10 bullet of R1-BX-PROPOSED-CONFIRM.
*Finding:* G4 reads "用主 proposer；CPU 节点继续 7B，论文写明；等 G.0/D28 结果后提交行" (commit the row after the G.0/D28 results). The row records the main proposer on the Track S GPU nodes as decided now. Diff liveness (D28) on GPU nodes is exactly what this choice depends on (R1-BX-D4 *(open)*).
*Fix:* Record it as "direction adopted: main proposer on the GPU nodes, 7B on the CPU nodes, disclosed. The row is committed after the G.0/D28 liveness results, together with the Track S GPU-node design revision (R1-BX-D10)". Add the committed row to "Still open".

**MAJOR-5. M12 removes an author gate that R1-BX-D3 requires.**
*Location:* `MAC_LOCAL_RUNBOOK_20261104.md` M12 step 1.
*Finding:* Rev 3 read "The author commits the protocol before you run it". R1-BX-D3 *(proposed)*, now confirmed "as written", says the protocol is "drafted by the Mac agent, reviewed, and committed by the author before it runs". Rev 3.1 replaces this with "Write it as a script with its parameters, have it reviewed, then run it", which drops the author's commit.
*Fix:* Restore it: "… have it reviewed; the author commits the protocol (script, parameters, sha256); then run it."

**MAJOR-6. Hosts for the new phases are missing, or contradict the canonical RUNBOOK without a ruling.**
*Location:* operator O9, O10 (C.2, C.3), O11; RUNBOOK B.4, C.2, C.3, D.3; the PLAN "Still open" list.
*Finding:*
- **C.3** (O10 step 2) has no host at all.
- **D.3** (O11) gives no host for the proposer or for the small-LM arms (A5/A6, the hybrid). RUNBOOK D.3 still reads "deepthought (+ zhixu portal for 4B arms) (3 Nov: 4090 hosts …, to be planned)".
- **B.4's pick row** (O9) adds "deepthought's two TITANs if O5 passed". RUNBOOK B.4 says "4090 host for the pick". R1-MAIN-PROPOSER (f) says "A4, C.2, C.3 and D.3 move to 4090 hosts wherever they run the main proposer (planned in Phase C)". The rulings' REVISIONS (f) bullet covers only the proposer of the sweeps.
- **C.2** (O10 step 1) and the T1/T2 parts of **D.3** are placed on Ada. RUNBOOK C.2 and D.3 were not changed, and no ruling covers this.

None of these choices was in A1–H1, and Phase C/D host planning is not listed as open.
*Fix:* In O9–O11, write "host: to be planned (author row; R1-MAIN-PROPOSER (f) 'planned in Phase C')" wherever no ruling exists. Keep B.4's pick row on a 4090, as the RUNBOOK says, unless the author rules otherwise. Add "Phase C/D host plan" to "Still open" in the PLAN and STATUS. Update RUNBOOK B.4, C.2, C.3 and D.3 only after a ruling.

**MAJOR-7. Two of the flagged gaps, C.1 and D.1, are not actually filled.**
*Location:* O10's title and the dependency summary ("B.7 pass ──► O7 C.1 (R-A)"); O7 step 3; M15 step 2; RUNBOOK C.1 and D.1.
*Finding:*
- **C.1** (A6, Stage R-A) is delegated to O7, but O7 has no C.1 step. R-A appears only in step 3, which lists pre-B.7 prerequisites (labels, the exam-set sha, the P.3b note). That contradicts RUNBOOK Phase C ("only if B.7 passes") and the dependency summary, and gives no estimate and no STOP.
- **D.1** is assigned entirely to the Mac (M15: "1 day after the A5/A6 checkpoints"). Leave-one-suite-out for A5 and A6 needs one trained checkpoint per held-out fold, which is GPU training (RUNBOOK D.1 host: zhixu portal; Track P is now on TASL-7). No operator phase owns it.

*Fix:*
- Add an explicit C.1 step to O7: TASL-7; only after B.7 passes (evidence) and the author's note; an estimate; a STOP. Make step 3 distinguish ENGINEERING_ONLY R-A on sweep-1 labels from C.1 evidence.
- Add an operator step for the per-fold A5/A6 training for D.1 (host as in the RUNBOOK and R1-TASL7-TRACKP, with an estimate and a note if it is EVIDENCE). Make M15 step 2 depend on it.

## MINOR

**m1. Stale *(proposed)* and "author picks" markers remain after the rulings.** PLAN precedence resolves them, and they all err on the conservative side, but they make the documents disagree.
- RUNBOOK: B.2 ("scope *proposed*: T1 only"); G.1 ("Starts only after the author confirms (h)", "*(proposed)*"); G.1b (seeds 8001–8010 *proposed*); G.2 ("*(proposed name)*"); G.3 (the author still fixes the T1 GPU model and the proposer host); G.5 (*proposed*); the fixed rules (divergence definition, K scope, the K = 6 seed subsets).
- TRACK_G_RUNBOOK: G.1b, G.2, G.3, G.5.
- Operator runbook: the intro ("in force once the author confirms it"); §0.2 (the handover is "packet item (a)"; seeds "scope *proposed*"); §0.3 (Ada and deepthought "if the author picks … (G.3)"); O1 and O2 ("if the handover makes it the editor", "handover row (a)", "packet row (d′)", "if the author keeps that"); O3 step 5 (*proposed*); O4 ("packet (e1)/(e2)"); O8 steps 2, 3 and 5 and its Hosts line.
- Mac runbook: §1 ("need the author (packet (j))"); the Order list (M13 "waits for packet (a)"); the M2 header ("only if packet (a) makes you editor").

*Fix:* Once the MAJOR findings are resolved, cite the 11:29 row ids in place of these markers.

**m2.** The Mac runbook's "Order" list (§2) does not mention M14 or M15. *Fix:* add them, with their prerequisites (labels and R1-BX-D8-CONFIRM for M14; B.7 passing, O10 and O11 for M15).

**m3.** B2 (R1-EXAM-RULE-X5V2 is committed by the author with its sha once M2 passes) is not recorded in PLAN §10; only the Mac runbook's note has it. H1's "建议作者提前写进 D8-CONFIRM" (the B.7 fallback goes into R1-BX-D8-CONFIRM in advance) is only implied by "restates these numbers". *Fix:* state both explicitly in the 11:29 section.

**m4. The "Still open" lists are incomplete and disagree with each other.**
- The PLAN and STATUS lists omit packet (c)'s B.1b difference list, which the Mac runbook lists.
- The §10 index says the 11:29 rows "resolve the R1-BX rows' *(proposed)* and *(open)* items". REVISIONS (e)'s *(open)* licence item and D6's host and log items (MAJOR-3) are not addressed.
- R1-APPTAINER-HOST leaves Apptainer confirmed only on deepthought2, which is not a run host. O8 step 2 and TRACK_G_RUNBOOK still say containers go "only through Apptainer", so the container route on the run hosts (deepthought, Ada, the 4090s) is now open and should be listed.

*Fix:* align the lists and add the missing items.

**m5.** R1-B2-REPLAY-GO's e2 sentence ("the B.2 start ruling lifts R1-B2-DECOUPLE's 'does not start'") can be read as if this row were the start ruling. C1 says "重放零差异后再给 e2" (e2 is given after a zero-difference replay). *Fix:* "(e1) proceeds once M3 is accepted **and** the author has committed the replay note. (e2) After zero differences and the gate table closed, the author gives the B.2 start ruling and commits the addendum."

**m6.** R1-1GC-FALLBACK drops A4's "G.0 第一天" (on G.0's first day). It also places unsourced factual context (the paper title, the authors, the repository URL, "GitHub answered 'not found'") in the decision cell. *Fix:* restore "on G.0's first day", and move the context to a sourced note outside the decision text.

**m7.** R1-TRACKS-S01-RERUN says the marker helper "is installed on TASL-7", which reads as already done. O7 installs it in step 1 ("first") and again in step 6 ("only after the author's row"). *Fix:* "is to be installed by the operator (O7 step 1)", and delete step 6's duplicate.

**m8.** R1-HANDOVER-04NOV adopts packet (a) but omits the bullet naming the files that `codex/b2-repair-20261031` changes outside its scope (`r1/c3/train/{run,trainer}.py`, `r1/c3/env.py`, `control.py`, `prior_model.py`). *Fix:* add that sentence, keeping the acknowledgement itself open.

**m9. Smaller gaps in the new phases.**
- O10 C.2 hands the table "to the Mac agent and O7 for retraining", but no Mac task covers retraining A3.
- C.3 (PILOT) and the C.4 A/B, as well as O9, do not state their run label or what authorization they need.
- M15 does not state its prerequisites (B.7 passing for C.4; the author's commit for D.2).

*Fix:* add a retraining step to M14 or M15, and state the run labels, notes and prerequisites.

**m10.** O7 step 1 (P.3a under option 3) does not say what is then run, or under which label or authorization (the run labels list "P.3a … evidence" as needing a note). *Fix:* state it, for example "re-score / continue per PORTAL_TRACK_P_RUNBOOK under its label; evidence needs the note".

## Checks (b)–(d)

- **(b) Gap coverage.**
  - B.3: M14, Mac CPU, after labels and D8-CONFIRM, 1–2 days. Covered.
  - B.4 pick row: O9 plus M14. Covered, but the host conflicts with the RUNBOOK (MAJOR-6).
  - C.1: not covered (MAJOR-7).
  - C.2: covered by O10, except the hosts (MAJOR-6) and the retraining owner (m9).
  - C.3: no host (MAJOR-6).
  - C.4: O10 plus M15. Covered; Ada agrees with RUNBOOK C.4 ("zhixu experiment").
  - D.1: the GPU part has no owner (MAJOR-7).
  - D.2 and D.4: M15. Covered.
- **(c) Consistency.**
  - The ids are consistent across PLAN, STATUS and the runbooks.
  - Seeds are consistent: 8001–8010; K = 6 subsets 7001–7003 / 7006–7008; the check on 7001–7005 only.
  - The D8-CONFIRM prerequisite is carried into O9, M14 and O7, and into the dependency summary.
  - Hosts disagree (MAJOR-6, m1). The "Still open" lists disagree (m4).
- **(d) Authorization and seeds.** No document authorizes a run. Every EVIDENCE phase still names an author-committed note: O9, O10 C.2, O11, G.5, G.6, and B.2 e1/e2. m5's wording should still be tightened. There is no use of 7006–7010 outside evaluation; the gate-stability exception is dropped. MAJOR-5 removes an author commit gate on a CPU analysis; it is not a run authorization, but it must be restored.

Verdict: not accepted
