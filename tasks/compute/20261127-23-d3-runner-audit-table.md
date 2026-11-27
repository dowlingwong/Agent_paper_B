# compute/20261127-23 — D.3: the runner → audit → outcome-table integration (blocks revision 4's freeze)

Owner: compute (G1 and G6 are yours). Base: `main` `840ad01d`. Read `docs/r1/reviews/D3_PREDECL_R4_STEP5_REPEAT_REVIEW_20261127.md` and the
replays on `main`.

The G1 terminal fix is confirmed. Two integration gaps remain:
1. **G1 → G7 summary.** G7 rejects the production G1 summaries because their keys differ from G7's required schema. Emit the exact G7 summary
   from the real ledger and accounting (G8) in G1, field for field as G7 reads it.
2. **Per-keep audits.** Revision 4 item 25 (signed: "audit every kept incumbent") needs an audit of each kept incumbent with its charged-run
   index and the declared seeds. Production G6 emits only the terminal and w-point audits. Add per-keep audits in G6 (cache-aware, as the item
   says), in the record form G7 reads.
Then assemble an outcome table directly from real G1 and G6 output, on the seven synthetic cases of the review, without fixture summaries or
hand-supplied audits, and show that G7 and the pinned analysis accept it. **Prefer changes in G1 and G6 only.** G7 and the analysis script are
hash-pinned in revision 4: if either must change, stop and say why before changing it. Tests (the review's cases as regression tests), full
suite at harness `9bb41680`, fresh tier-E review. Then the local worker repeats step (5).
