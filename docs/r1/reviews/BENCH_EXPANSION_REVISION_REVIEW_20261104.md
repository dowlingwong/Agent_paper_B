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
