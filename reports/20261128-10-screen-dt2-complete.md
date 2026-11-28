# compute/20261128-06 — screening on deepthought2: complete, INCONCLUSIVE, decision final

**Result: 10,164/10,164 runs, 0 failures, no STOP; elapsed 1,468.2 s. Pre-declared analysis: `digits_mlp`
INCONCLUSIVE and `openml_climate` INCONCLUSIVE; six nodes `NOT_TESTED` by design. Decision
`R1_THEORY_RHO_2_FINAL` (also seven-node and Bonferroni). No `SHARED` node, so per the note R1-THEORY-RHO (2) is
final and D.3 step (8) proceeds on rev 4.**

- Task: `compute/20261128-06` (R1-SCREEN-DEEPTHOUGHT2, third re-issue).
- Deliverable branch: `compute-screen-dt2-20261128` @ `fa0707dae2f8eed9e8d659616dc7e4967d9b7ae4`.
- Review: running on `compute-screen-dt2-20261128-review`.
- Run: `smeas-20261123-a`, stamp `SMEAS_EVIDENCE_20261128T001405Z`, checkout at code `a7c2f8fb`, deepthought2
  CPU only, 64 workers; `2026-11-28T00:26:06Z`–`00:51:29Z`; data cache tree `3843b53c…`; manifest
  `da2419a5…`; lineage 10,164 rows, sha `c0863b6f…` (equals the manifest's `runs_sha256`); analysis
  `6c72535e…`.
- Per-node: `digits_mlp` estimate 0.08158, 95 % CI [−0.00836, 0.17268] (97.5 % [−0.01764, 0.18492]);
  `openml_climate` 0.05962, 95 % CI [−0.09447, 0.21440]; both include 0 → INCONCLUSIVE. The other six are
  NOT_TESTED by design. No test/evaluation label read.

**Next:** the fresh analysis review; then the coordinator publishes the record and routes the decision. The old
deepthought scenes stay untouched; the run directory is preserved.
