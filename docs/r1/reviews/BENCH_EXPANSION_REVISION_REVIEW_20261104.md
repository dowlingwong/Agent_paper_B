# Independent review — application of the benchmark-expansion adoption (commit `ed43a90a`)

**Date:** 4 Nov 2026. **Reviewer:** fresh Claude Code agent (AI-assisted; not human review). **Scope:** `git diff fa60704e ed43a90a` on branch `docs/runbooks-04nov`, judged against `docs/r1/proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md` (the "source") and the repository's governance rules. Files read: the source in full; the changed sections of PLAN (§5 note, §6 note, §9 item 5 and milestones note, §10 index, the new 4 Nov subsection with surrounding rows R1-SWEEP-HOST, the 18 Oct C3 gate, R1-FOCUSED-SCOPE, R1-INTERNAL-FREEZES, R1-TRACKG-ROLE/-SCOPE, R1-TABPFN, R1-SWEEP1-CLASSIFY, R1-B2-DECOUPLE, R1-MAIN-PROPOSER, R1-COMPUTE); RUNBOOK in full; both execution runbooks (changed sections plus O0, O5, O6, dependency summary); C3_DESIGN, TRACK_P_POST_TRAINING, TECH_ROUTE, TRACK_G_RUNBOOK, TRACK_S_GPU_EXTENSION, the STATUS top entry and README. No file other than this one was changed; nothing was committed or pushed.

## Summary

The revision is thorough. Every source decision D1–D14 has a PLAN §10 row (R1-BX-D1 … D14), and the §§2–5 and 8 revisions are collected in R1-BX-REVISIONS (a)–(h). The wording is faithful to the source almost everywhere, and the recorder's additions are mostly marked *(proposed)* or *(open)*. The three conditions of the "For the coordinating agent" box are recorded verbatim in spirit (PLAN §10, 4 Nov subsection, "Conditions …" bullet). The recorder also found a real dependency: the D3 check needs sweep-1 B.2 audits, which do not exist. No older PLAN row was deleted. No document authorizes a run: TRACK_G_RUNBOOK says "This file authorizes nothing", G.5 and G.6 need notes, and B.1b keeps "This section authorizes nothing". The cost arithmetic is correct: 50 × 2 min ≈ 1.7 GPU-h; 240 × 2 min = 8; 900 × 2 min = 30; total 40; × 10 nodes = 400; K = 10 audits 1,500 × 2 min = 50; the source's 125 GPU-h = 150 × 10 × 5 min; √(5/3) ≈ 1.29.

Five MAJOR findings remain, so the revision is not accepted yet. Two are routing and execution gaps (porting and the census; the TabPFN host). One is a pre-registration enforcement gap for D8. One is a seed-rule conflict in the proposed D3 check. One is the deepthought proposer-host amendment, which is partly unmarked and leaves B.1b self-contradictory. All five can be fixed in documents only.

## Findings

### MAJOR

**MAJ-1 — Porting is routed to the wrong agent, and the census cannot run as written.**
- *Where.* Source §7 routes "Porting suite task assets into harness nodes; container-free where possible" to the **server agent**. The revision gives the porting code to the Mac agent instead:
  - RUNBOOK G.1: "Mac (code: node specs, parsers, tests on fakes); the operator for host smoke runs";
  - TRACK_G_RUNBOOK §G.1 and "Who does what";
  - MAC_LOCAL M10 step 2 (line 384), "written as census rows arrive from the operator".
  
  Nothing marks this as a deviation. The census also needs code that nobody is assigned to write before it starts. OPERATOR O8 step 1 (line 320) and the dependency line `O0 ──► O8 G.0 census on Ada` (line 338) start G.0 right after STOP 0. But G.0 needs:
  - each task runnable at a **fixed step budget** (autoresearch, for example, ships a wall-clock budget, so a code change is needed);
  - "3–5 representative edits" for the 10-seed noise floor.
  
  The operator "never edit[s] code to make a run work" (operator runbook, intro). As written, either the operator writes code against its own rule, or G.0 stalls until M10, which itself waits for census rows. The plan is circular.
- *Fix.* Choose one option and record it:
  - **(a)** Follow source §7. The operator ports the task assets, inside its review loop and as reviewed commits, and an explicit exception to the "never edit code" rule is scoped to Track G porting.
  - **(b)** Keep the Mac as code owner and record this as a *(proposed)* deviation from §7 in R1-BX-REVISIONS (h), with the reason (the 4 Nov split puts all code on the Mac). Add an M10 step 0, the **census kit**: per-candidate fixed-budget wrappers and the representative edits, reviewed before G.0. Change the dependency line to `M10 census kit ──► O8 G.0`.
  
  In both cases, list it in packet (j) for the author.

**MAJ-2 — D8's condition ("committed before any sweep-2 labels are analysed") has no hard gate in the execution path.**
- *Where.* The adopted part of D8 is recorded. Its numbers are *(proposed)* and are to be confirmed before any sweep-2 label is analysed (PLAN R1-BX-D8, line 721; RUNBOOK B.7; packet (j)). But:
  - **(i)** OPERATOR O6 "Needs" and the dependency line `X.7 + O4 + M4 + D28 + projection + note ──► O6 … ──► evidence labels ──► B.3–B.5, B.7` (line 336) do not require the confirmation. The same holds for G.5 (T1 labels) → B.7.
  - **(ii)** The MAC M11 guard (line 398) covers only the gate code and only `y_eval`. Building the label table, B.3 offline values and B.5 training on sweep-2 labels are also analysis of sweep-2 labels.
  - **(iii)** The guard keys on "a PLAN line containing `R1-BX-D8` and the numbers' confirmation". The current row already contains `R1-BX-D8` and the words "the author confirms the numbers in this row", so a naive check would pass today.
- *Fix.*
  - Add "the author's R1-BX-D8 confirmation row" as a prerequisite in O6 "Needs", in G.5 / O8 step 4, and in the dependency summary, before any sweep-2 or T1 label table is built or copied to the Mac.
  - Give the confirmation a distinct id, for example `R1-BX-D8-CONFIRM (date)`, quoting the numbers and the sha256 of the gate code.
  - Make the M11 guard require that id and cover every reader of sweep-2/T1 label tables, not only gate code reading `y_eval`.

**MAJ-3 — The proposed D3 check protocol conflicts with the seed rules, and its ordering against D8 is not fixed.**
- *Where.* PLAN R1-BX-D3 *(proposed)* check protocol (line 716), MAC M12 (line 403):
  - "the evaluation-seed side uses training and dev instances only";
  - criterion (iii), "the R1-BX-D8 gate statistic computed on dev has the same verdict at K = 6 and K = 10".
  
  This uses seeds 7006–7010 to make a design selection (whether T1 runs at K = 6) and to compute a gate verdict on arms trained on sweep-1 labels. R1-B2-DECOUPLE limits 7006–7010 to "B.2 task-level joint-seed retraining and evaluation, never C3/Track P training, tuning or selection". R1-SWEEP1-CLASSIFY says "never used for training or selection of any evidence". R1-MAIN-PROPOSER (e) says Track P on sweep-1 labels uses "label seeds 7001–7005 only and never 7006–7010". The protocol's own disclaimer ("compares only the stability of statistics, never arm values used for selection") does not hold for (iii), which is a verdict on arm values. The recorder did not mark this as *(open)*. In addition:
  - sweep 1 and sweep 2 share instances, splits and audit seeds, and twin proposals get identical labels (R1-MAIN-PROPOSER (e));
  - so computing the D8 statistic on sweep-1 data before the D8 numbers are confirmed lets the gate's numbers be tuned on data that partly coincide with sweep-2 labels;
  - M12 does not require D8 confirmation first.
- *Fix.*
  - Either restrict the check to label seeds 7001–7005 (for example, 3-of-5 subsets against the 5-seed label for the sign of u and μ, and the gate-stability part done by splitting the label seeds into pseudo-label and pseudo-evaluation halves).
  - Or mark the use of 7006–7010 as *(open: needs an explicit author exception to R1-B2-DECOUPLE / R1-SWEEP1-CLASSIFY)*.
  - In both cases, make M12 require the D8 confirmation row (MAJ-2) before it computes any gate statistic.

**MAJ-4 — The deepthought proposer-host amendment is partly agent-made and leaves B.1b contradicting itself.**
- *Where.* Source §4 says only "A model can be served across two TITANs, so the main proposer could run there and free 4090 time …". PLAN R1-BX-REVISIONS (f) turns this into an explicit amendment of R1-MAIN-PROPOSER (f) and adds two conditions without marking them:
  - "if the dual-card qualification (operator O5) passes";
  - "within one source the proposer runs on one serving configuration".
  
  The RUNBOOK B.1b table row now offers deepthought, but the B.1b spec body still instructs the old behaviour without a marker:
  - "Host and priority: One 4090 host for the whole sweep: TASL-2 or TASL-7";
  - prerequisite 6, "More than 4 days of one 4090 is a STOP";
  - the differences list ("built for a 4090 (sm_89), not a TITAN X (sm_52)").
  
  The same holds for PLAN R1-MAIN-PROPOSER (c)/(h). The previous review made exactly this a BLOCKING item (operator runbook §4, row "B1: sweep 2 on deepthought contradicts R1-MAIN-PROPOSER (f) and B.1b"). MAC §1 (line 105) now says both "there is no PLAN row yet" and "R1-BX-REVISIONS (f) now amends R1-MAIN-PROPOSER (f)". It is also unclear whether sweep 2's T0 part (B.1b host) and T1 part (G.3 proposer host) form one "source" and must therefore share one serving configuration. No run happens without the author's STOP 5 ruling, so this is not BLOCKING.
- *Fix.*
  - Mark the two conditions in (f) as *(proposed)*.
  - Add a 4 Nov marker to the B.1b "Host and priority" block, to prerequisite 6 (the projection is per host) and to the differences list (sm_52 and the two-card split if deepthought is chosen). Note the same in R1-MAIN-PROPOSER (c)/(h) via the index.
  - Reword MAC §1 line 105 so it no longer contradicts itself.
  - Add to packet (j): whether the T0 and T1 parts of sweep 2 must use one proposer serving configuration.

**MAJ-5 — The TabPFN rows are placed on the Mac, against R1-TABPFN and R1-COMPUTE.**
- *Where.* RUNBOOK B.3 now reads "plus … the TabPFN rows, native and information-matched (R1-BX-D13) | Mac". R1-TABPFN (28 Oct) fixes "Host: TASL-7". The matched view also needs a text-embedding model, which is small-model inference. R1-COMPUTE allows that on the Mac only as a last resort, with the author's approval per use. MAC M11 step 4 implements the view but does not say where it runs.
- *Fix.*
  - B.3: TabPFN rows on TASL-7 (operator O7, Track P scope); the Mac writes code and CPU fixture tests only.
  - M11 step 4: state "code and fixture tests only; embedding and TabPFN runs on TASL-7".
  - Packet (j): the embedding host.

### MINOR

1. **Adoption evidence.** PLAN 4 Nov subsection (line 703 ff.) quotes the author's 01:29 instruction, "你认真阅读，并对我们的现行计划，runbook以及一切相关文档进行修正修改". That is an instruction to revise the documents, not an explicit adoption of D1–D14. The "ADOPTED IN FULL" status line entered the repository in this same commit and does not say who wrote it. The commit body does not quote the author either, which MAC §0 asks for when rows are committed on the author's behalf. *Fix:* quote the author's actual adoption words with a timestamp, or have the author confirm the R1-BX rows in a one-line commit or row. State who wrote the source status line.
2. **"(checked against the MLGym task table)"** (PLAN R1-BX-D2; RUNBOOK Track G T1 row) reads as done. The source says "check against". *Fix:* "(to be checked against the MLGym task table in G.0)".
3. **Recorder operationalisations not marked *(proposed)*:**
   - the divergence definition ("a non-finite loss, or a run that ends without a metric") and its treatment (no label at all; PLAN (c), TRACK_P §3.4, C3_DESIGN §4). Also *(open)*: how divergence enters the belief and u, and what happens when only some seeds diverge;
   - "K = 6 … T1 only", stated without the marker in RUNBOOK B.2, C3_DESIGN box and OPERATOR §0.2;
   - OPERATOR O3 step 5, "Track S may continue, but its result is no longer on the critical path".
   
   *Fix:* add the markers.
4. **D8 proposed numbers.** "Holm over the two arms, one-sided α = 0.05" does not fit "the lower 95 % bound": under Holm the first test is at α/2. Gap closed is unstable when U_oracle − U_A2 ≈ 0 on a node. *Fix:* state the bound as the one-sided (1 − α_Holm) bound, and declare a rule for nodes with a near-zero denominator.
5. **Stale text without a marker:**
   - PLAN supersession list (line 730) and §10 index: missing R1-BENCH-HARD ("role … proposed: evaluation and transfer") and the §6 generalisation design;
   - RUNBOOK §1 "The C3 gate is fixed (PLAN §10, 18 Oct)";
   - RUNBOOK H.7 (amended by R1-BX-D9 but unchanged);
   - P.6 "Done when: R-B row in the three-way comparison";
   - Track P "Labels" items 5 (LONO as the only fold) and 6 (B.6 to 8–10k);
   - X.6, which cites the old G.1/G.3/G.5 numbering;
   - the RUNBOOK §3 host table's Ada row, which does not list the Track G census.
   
   *Fix:* add 4 Nov markers.
6. **"The coordinating agent recomputes the dates"** (RUNBOOK G.4, TRACK_G G.4, OPERATOR O8 step 3). Under the 4 Nov split the coordinator stops (packet (a)). MAC packet (i) gives the task to the Mac agent. Similarly, TRACK_P §2.2 says "The Track P agent first checks which order the template used", while MAC M13 gives this to the Mac agent. *Fix:* name the Mac agent in both places.
7. **Packet (j) is incomplete.** Missing:
   - TRACK_P §3.6, "T0 is never the held-out suite" *(proposed)*;
   - §5.6 A6, descriptive *(proposed)*;
   - TRACK_G G.5 memory modes and the divergence STOP factor of 2 *(proposed)*;
   - the K = 6 seed subsets 7001–7003 / 7006–7008 *(proposed)*;
   - the P.3a re-run question *(open)*;
   - the pooled T0 + T1 gate against R1-SWEEP-HOST's "no mixing hosts within one table". Node strata are each on one host, but the rule should be reconciled explicitly.
   
   *Fix:* add them.
8. **§7 items with no code owner:**
   - the API-proposer provider for G.6 (version pin, request/response log, secrets);
   - the S1.1 interaction measurement for code diffs (P3, run in G.5);
   - closed-loop evaluation of the non-qualifying nodes (D12 appendix) has no operator step.
   
   *Fix:* add them to M10/M6 and O8.
9. **API proposer scope.** D6 says "on T1/T2 nodes". RUNBOOK G.6 and the README place it on T2 only, while TRACK_P §7.4 says T1/T2. *Fix:* align them.
10. **Census seeds and Ada census.** G.0 does not declare the seed block for the 10-seed noise floors. It should be disjoint from 7001–7010, the sweep instance seeds and 9001+. OPERATOR O0 does not census Ada (Paper A occupancy) before O8 starts there. *Fix:* declare the block and add Ada to O0.
11. **README.** Two caveats are missing: "the main proposer may be served across two cards" needs "if the dual-card qualification passes (proposed)", and T1's 1GC-7RC is subject to the open repository check. The STATUS top entry cites this review before it exists. *Fix:* add the caveats, and record this review's verdict in the STATUS entry.
12. **Old Track G table deleted.** The RUNBOOK's old Track G table (G.1–G.5, including G.4's author audit-budget step) was deleted rather than struck through. *Fix:* cite `fa60704e` as the location of the old text, as TRACK_G_RUNBOOK does.

## Checks with no finding

- **D1, D2 (apart from MINOR-2), D4–D7, D9–D14** match source §6 and §§2–5 in substance. D3's condition and STOP are recorded in PLAN, RUNBOOK §6, MAC M12 and OPERATOR §0.2/O4.
- **D14:** marked as targets, with recomputation after G.4 and a report before applying (PLAN, RUNBOOK G.4, MAC packet (i), OPERATOR O8).
- **Section 7 routing:** each other item has a home.
  - Mac: PLAN rows, the RUNBOOK revision, D4/D5 (M10), D7/D8/D13 (M11), P13 (M13, or a spec), D3 (M12), manuscript wording (M8).
  - Operator: the census (O8 G.0, Ada first), T1 pilot, sweep and audits (G.4–G.5), Track S GPU (O3 step 4, after the M6 design and an author row), T2 with the API proposer (G.6).
  - The review protocol is kept.
- **Section 8:** the container order, the Apptainer notes and the open host question are recorded (PLAN (g), TRACK_G_RUNBOOK §3). deepthought2 stays out of the run hosts.
- **Superseded rows:** marked in the index and the supersession paragraph. B.6 and the 18 Oct B.7 criterion are struck through in the RUNBOOK. The C3_DESIGN and TECH_ROUTE gate paragraphs are marked superseded. The MLGym 10 Nov container deadline and "evaluation-only" Track G are superseded in RUNBOOK, OPERATOR O8, TECH_ROUTE and TRACK_G_RUNBOOK. R-B is marked as no longer the self-control arm in TRACK_P §6.4, RUNBOOK P.6 and D.2.
- **Seeds:** 7006–7010 stay evaluation-only in every execution document (apart from the proposed D3 check, MAJ-3). Exam seeds stay out of the sweeps.

## Verdict

Five MAJOR findings (MAJ-1 to MAJ-5) remain, with no BLOCKING finding. All are document fixes. A re-review of the fixes for MAJ-1 to MAJ-5 is enough to accept.

Verdict: not accepted

---

## Round 2 (re-check of commit `7a4f4f91`, 4 Nov 2026)

**Scope.** `git diff ed43a90a 7a4f4f91`. I re-read the changed passages of PLAN (4 Nov subsection intro; rows R1-BX-D2, D3, D8, REVISIONS (c), (f), (h); the supersession list), RUNBOOK (§1, §3, B.2, B.3, B.7, B.1b, Track G, Track S, X.6, H.7, P.6, Track P labels 5–6), both execution runbooks, TRACK_G_RUNBOOK, C3_DESIGN, TRACK_P_POST_TRAINING, README and the STATUS top entry. I also checked `r1/exam/runtime.py` `author_gate`, the reading pattern that the new D8 guard is told to copy. Only this section was added; nothing was committed.

### Round 1 findings

| Finding | Status | Reason |
|---|---|---|
| MAJ-1 porting routing / census gap | **resolved** | Porting goes to the operator as §7 says, under a scoped exception marked *(proposed)*: PLAN (h), operator intro, TRACK_G "Who does what". The census is split into G.0 (availability and raw cost, with no new code), G.1 (ports, with the representative edits declared and hashed before any measurement, each port reviewed) and G.1b (measurements). MAC M10 step 0 supplies the shared pieces. The dependency line is now executable (`O0 (incl. Ada) ──► G.0 ──► M10 step 0 ──► G.1 ──► G.1b ──► G.3 …`). Two small residues are listed as N2 and N4 below. |
| MAJ-2 D8 enforcement | **resolved** | `R1-BX-D8-CONFIRM` (the numbers plus the gate-code sha) is now a prerequisite for copying back or reading any sweep-2 (T0 or T1) label table. It appears in: OPERATOR §0.2 "Analysis gate", the O6 Needs, O8 step 5, the dependency summary (both chains), RUNBOOK B.7, TRACK_G G.5, MAC M11 step 3 (all readers, including a spec for the Track P loaders), M12 and the packet (j) item. One residue in the guard specification is listed as N1. |
| MAJ-3 D3 check and seed rules | **resolved** | The check now uses label seeds 7001–7005 only, with criteria (i) and (ii). A gate-stability part that would use 7006–7010 is *(open)*. It needs an explicit author exception, runs only after R1-BX-D8-CONFIRM, and appears in packet (j). MAC M12 matches. |
| MAJ-4 deepthought proposer host | **resolved** | In PLAN (f) the conditions are *(proposed)*, and the T0/T1 shared-host question is *(open)*. RUNBOOK B.1b now carries a 4 Nov marker in "Host and priority", in prerequisite 6 (the 4-day STOP applies to the two-TITAN configuration, proposed) and in the differences list (sm_52, two-card split). MAC §1 no longer contradicts itself. PLAN (f) ("within one source, and within one tier") and B.1b ("one serving configuration for the whole T0 part") agree. |
| MAJ-5 TabPFN host | **resolved** | RUNBOOK B.3, MAC M11 step 4 ("code and CPU fixture tests only … never on the Mac") and OPERATOR O7 step 2 put the TabPFN rows and the embedding model on TASL-7. The B.3 host cell still reads "Mac" for A0–A3, and the row text states the TASL-7 exception, which is acceptable. |
| MIN-1 adoption evidence | **resolved** | The PLAN intro and the commit body now quote the author's full 4 Nov message, and the intro states that the status line came with the author's own attachment. I cannot see the attachment; this rests on the coordinator's statement, which the PLAN records. |
| MIN-2 "checked against" | **resolved** | "To be checked … in the census / G.0" in PLAN D2, RUNBOOK T1 and TRACK_G §1. |
| MIN-3 unmarked operationalisations | **partly resolved** | Now marked: the divergence definition and its treatment (*proposed*: PLAN (c), RUNBOOK, TRACK_G §2, C3_DESIGN, TRACK_P §3.4), the T1-only K scope (*proposed* everywhere), and "Track S may continue" (*proposed*, RUNBOOK and OPERATOR O3). Still missing is the *(open)* question I asked for: how a divergent proposal enters the belief and the action target u (for example a separate class the forecaster predicts, or a cost), and what happens when only some audit seeds diverge. Packet (j) lists only "the divergence definition". Remains **MINOR**. |
| MIN-4 Holm / denominator | **resolved** | 97.5 % / 95 % one-sided bounds under Holm; nodes with a near-zero denominator (below δ_n on dev) are excluded from the IQM, listed, and kept in the probability of improvement. Identical in PLAN and C3_DESIGN. |
| MIN-5 stale text | **resolved** | Covered: R1-BENCH-HARD added to the supersession list and to D2; RUNBOOK §1, H.7, P.6, labels 5–6, X.6 and the Ada host row carry 4 Nov markers. (X.6's trailing "(G.5)" still uses the old numbering, but the new marker covers the sentence.) |
| MIN-6 "coordinating agent" | **resolved** | The PLAN intro defines it as the Mac-local agent; RUNBOOK G.4, TRACK_G G.4 and OPERATOR O8 step 4 name the Mac agent; TRACK_P §2.2 names the editor of `r1/c3/train/`. |
| MIN-7 packet (j) | **resolved** | All the items listed in round 1 have been added (D8-CONFIRM, pooled gate, D3 exception, (c), (f), (h), census seeds, G.5 items, K subsets, TRACK_P items, Track S). The pooled-gate question is also *(open)* in the D8 row. |
| MIN-8 missing owners | **resolved** | The API provider (M10 step 5), S1.1 for diffs (M10 step 2, G.2) and the D12 non-qualifying nodes in the closed loop (G.6, M10 step 6) now have owners. |
| MIN-9 API proposer scope | **resolved** | G.6 covers T1 and T2 in RUNBOOK, TRACK_G and OPERATOR; README T1/T2 rows agree. |
| MIN-10 census seeds / Ada in O0 | **resolved** | Seeds 8001–8010 *(proposed)* are disjoint from 7001–7010, the sweep instance seeds and 9001+. O0 step 1 now includes Ada, with the Paper A occupancy check. |
| MIN-11 README / STATUS | **resolved** | README adds the dual-card condition and the open 1GC-7RC check. The STATUS entry records round 1 and points to this file for the verdict. |
| MIN-12 deleted Track G table | **resolved** | RUNBOOK and TRACK_G cite `fa60704e`. |

### New findings (all MINOR)

- **N1 — the D8 guard specification would pass today if implemented as described.**
  - *What the spec says.* MAC M11 step 3 says the guard checks for "a PLAN §10 line containing `R1-BX-D8-CONFIRM` … the same way `runtime.author_gate` reads the PLAN".
  - *Why that fails.* `author_gate` (`r1/exam/runtime.py:109`) accepts any line containing the id and the sha. The current PLAN rows R1-BX-D3 (line 716) and R1-BX-D8 (line 721) already contain the literal string `R1-BX-D8-CONFIRM`, so a substring check passes before the author has confirmed anything.
  - *Mitigation.* The same step requires a test that the current row does *not* satisfy the guard, and the procedural gates in OPERATOR §0.2 and the dependency graph are independent of the code. So this is MINOR, not MAJOR.
  - *Fix.* Specify that the guard matches only a §10 table row whose **first cell begins with `R1-BX-D8-CONFIRM`** and that contains the recorded gate-code sha. Drop "the same way `author_gate` reads the PLAN", or qualify it.
- **N2 — the porting exception has no explicit confirmation step.**
  - *Where.* The exception is *(proposed)*, and the operator intro says "in force once the author confirms it". But OPERATOR O8 step 2, TRACK_G G.1 and the dependency line start G.1 without that confirmation as a prerequisite.
  - *Fix.* Add "the author's confirmation of R1-BX-REVISIONS (h)" to O8 step 2 and to the dependency chain before `G.1 ports`.
- **N3 — the CONFIRM prerequisite is "proposed" in PLAN but stated as settled elsewhere.**
  - *Where.* PLAN R1-BX-D8 marks the R1-BX-D8-CONFIRM hard prerequisite *(proposed)*. RUNBOOK §1 and B.7, OPERATOR §0.2 "Analysis gate", C3_DESIGN and TRACK_P state it as settled. It only restricts, and it implements adopted condition (ii), so it is harmless.
  - *Fix.* Pick one form. Either state in PLAN that the separate row is how adopted condition (ii) is implemented (no *(proposed)*), or add "(proposed)" at the other sites.
- **N4 — G.0 raw cost assumes a step-count argument.**
  - *Where.* G.0 measures "the suite's own baseline script at a candidate step count … No code beyond the suite's own script and a step-count argument". Some candidates have no such argument; autoresearch, for example, ships a wall-clock budget.
  - *Fix.* Add "where the script has no step-count argument, its raw cost is measured after G.1 at the fixed-step wrapper" (RUNBOOK G.0, TRACK_G G.0, OPERATOR O8 step 1).

### Consistency re-check

The fixes are consistent with each other in these places:
- **Ids:** R1-BX-D8-CONFIRM, R1-BX-REVISIONS (f) and (h), G.1b and STOP 8a/8b.
- **Hosts:** TabPFN on TASL-7; the census on Ada after O0; the proposer on a 4090 or on deepthought subject to O5 and STOP 5.
- **K and seeds:** K = 10 until an author row; T1-only scope proposed; label seeds 7001–7005 for the D3 check; census seeds 8001–8010 proposed; 7006–7010 used only for evaluation.
- **Dependencies:** the two dependency chains in the operator runbook match MAC §2 ordering and TRACK_G §4.
- **Governance:** no document authorizes a run. G.0, G.1, G.1b and G.4 are ENGINEERING_ONLY under their track runbook; G.5 and G.6 need notes.
- **Cost figures:** unchanged and still correct.

The only leftovers are MIN-3 (partly resolved) and N1–N4, all MINOR.

### Round 2 verdict

All five MAJOR findings are resolved, and no BLOCKING or MAJOR finding remains. The remaining MINOR items (MIN-3 residue, N1–N4) are worth fixing before the operator starts G.1 or the Mac agent implements the M11 guard, but they do not block acceptance.

Verdict: accepted

## Post-acceptance fixes (executing agent, 4 Nov)

The remaining MINOR items were applied after the round-2 acceptance, without a further round:
- MIN-3: the divergent-proposal treatment (belief, action target u, partial divergence) is an *(open)* item in R1-BX-REVISIONS (c) and packet (j).
- N1: the M11 guard matches a §10 table row whose first cell begins with `R1-BX-D8-CONFIRM` and that carries the gate-code sha; a substring match is ruled out.
- N2: G.1 porting starts only after the author confirms R1-BX-REVISIONS (h) (RUNBOOK G.1, TRACK_G G.1, operator O8 and the dependency chain).
- N3: PLAN R1-BX-D8 now states the R1-BX-D8-CONFIRM row as the implementation of the adopted condition, unmarked, matching the other documents; its numbers remain proposed.
- N4: where a baseline script has no step-count argument, raw cost is measured after G.1 at the fixed-step wrapper (RUNBOOK G.0, TRACK_G G.0, operator O8 step 1).
