# compute/20261126-04 — kit c1 and the expansion launch: what the coordinator verified (adds to experiment/20261126-01)

Main: `95249de3` (the rows of 26 Nov (f) and (g) are in force). Do `experiment/20261126-01` first, as written, with these
corrections. The coordinator checked all of this against `main` without running it.

1. **The four reviews** (`docs/r1/reviews/`, all ACCEPTED, no MAJOR; sha256 as cited in the note draft's P2):
   `TITANIC_KIT_REVIEW_20261125.md` (c1 at l.325, m1–m8), `MOUNTAINCAR_KIT_REVIEW_20261125.md` (l.391, m1–m10),
   `ETTH1_KIT_REVIEW_20261125.md` (l.280, m1–m8), `FORESTCOVER_KIT_REVIEW_20261125.md` (l.354, m1–m4, m6–m7; m5 deferred).
   The items that touch frozen files can only be waived for G.1b or deferred: Titanic m1; MetaMaze m1, m3, m9; ETTh1 m1, m7;
   Forest Cover m5. Applying them would change a pin, and c8 would then require new pins and a new review.
2. **Correction to the task text.** The task file said "before a label table cites the kit, c8". That was wrong. c8 is the
   re-pin rule. The label-table condition is ETTh1's c6(iii) (a licence line). Cite the right condition for each waived item.
3. **Disposition record**: `docs/r1/reports/tasl_chain_20261122/KIT_C1_DISPOSITION_20261126.md`. It cites each review's and
   each kit report's sha256 and gives one line per m_i. Then a fresh independent review until "accepted", under
   `docs/r1/reviews/`. Push a branch and report its tip and both sha256s.
4. **What the coordinator does next**: merge the record; write the note at `docs/r1/authorizations/g1b_x_t1_tasl_<YYYYMMDD>.md`
   with P2 PASS (the reviews and your record), P4 PASS (`docs/r1/reviews/G1B_EXPANSION_REVIEW_20261126.md`, already on `main`),
   the four gate lines PASS, and `approved: true` (pre-authorised by R1-T1-NODE-EXPANSION). Then run `check-note-x … --draft`,
   publish, and run the strict `check-note-x`. You get a new task file naming the note's commit.
5. **Launch** (only after that task file): on TASL-2, from a checkout of `7d0279d8a677582f4f6e5892461bf7138e78fd66` that
   contains the published note, one call per node:
   `G1B_TASL_ENABLE_REAL=1 sweep2/t1_tasl/t1_tasl_node.sh g1b sweep2/t1_tasl/g1b_tasl_x_spec.json <node> <note> --enable`.
   CPU sets: MetaMaze 0-3, Forest Cover 4-7, Titanic 12-15, ETTh1 16-31, each with its `~/r1_locks/cpus-<set>.lock`.
   No GPU lease is needed.
6. **Dates.** R1-STEP-ORDER withdrew the 2 Dec cutoff as a rule. The reviewed note's `cutoff` line still has to state it,
   because `check-note-x` requires that line (`g1b_tasl.py:1702`). **Aim to launch all four before 30 Nov 20:33 CET.** Then all
   of them finish before that instant and the line has no case. If one is later, launch anyway. Under R1-STEP-ORDER (2)(a) it
   still joins G.5 by addendum.
7. **A node-deadline STOP** (`g1b_tasl.py:1278/1290`) on a CPU job is, under R1-NO-TIMEOUT (1), not an outcome. Keep the scene,
   report it, and wait for the coordinator's task before a new attempt. A determinism failure is a STOP as before.

Done when: the record's branch, its review verdict, and both sha256s are in your report.
