# local/20261128-13 — Ada P.4 timing carry-forward accepted, P3 signature STOP

for: coordinator

- Published base `66aa4e10b107d81d6abc305fb1fa16879ff737d7`, queue `216f33ea6c09f856b1e3ddaf9789a852a075a7df`.
  Unsigned draft branch `local-20261128-13-p4-phase1-note` @ `f1c94030a5b052fdcc7f6321b4aac040577a1101`,
  superseding the draft at `be602ef3` for timing. Draft SHA-256
  `dd3431d19998c95b9751673feb46525503eb1f24b8a6af2770a066a2965b6f8c`.
- Fresh independent tier-E review **ACCEPTED** the timing carry-forward paragraphs and the pending P5 line.
  Review SHA-256 `11a977db3376702ac5de380a5a1e0bfeefe8a74130a9f381af5823cee3367d77`.
  [Draft review](https://github.com/dowlingwong/Agent_paper_B/blob/f1c94030/docs/r1/reviews/P4_PHASE1_TIMING_CARRY_FORWARD_REVIEW_20261128.md)
- All 43 capture hashes verified. Launch-strength spec and note binding checks passed. The official parser
  refused the unsigned draft at P3 as expected. Only P5 among the structured note fields changed. This unit
  changes the proposal and review documents. The previously accepted runner and spec suite remains in the
  [P3 handoff](20261127-25b-p4-p3-runner-and-launch-stop.md).
- **P5:** Compute timing PASS at `902ef2c67c2d7f487b951fefde6e0dc9e5cfa02f`, SHA-256
  `24e0d7137ec29421966d70541e0448e96e6d269287d3ac1baf1f91d634e86bbc`; Compute review at `8a5316f1`, SHA-256
  `37d4b6dd3f09b0b4e94d9f8cab9a4daac09db0a81bd3e03e3ec40b11996817b5`. The four original per-arm estimates
  carry forward. New synthetic timing usage was 0.3233 GPU-h, for about 23.99 GPU-h when added to the
  formal 3.10 GPU-h probe charge and 20.57 GPU-h phase-1 projection. P5 stays pending in the draft until the
  timing artifacts are on `main`. [Compute report](https://github.com/dowlingwong/Agent_paper_B/blob/3f045219/reports/20261128-32-p4-p3-p5-timing.md)
- **P3 STOP:** Compute found no configured project signing identity. The authorized signer must reproduce the
  exact one-file spec in `befb58c8b3f5b222a2cf8973e513b252235453fc` on parent
  `0b46595418bb21dc0e8e5b234b30f2a84ac5082c` with the project SSH signature. Spec SHA-256
  `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6`.

Next: the coordinator publishes the timing records and routes the spec signature to the author. Local fills P3
and P5, runs the final checks, and obtains independent acceptance under R1-P4-PHASE1-SIGNATURE (4). The
phase-1 run `trackp-p4-p1-20261122-a` is still gated. Compute checks its ledger before any submission.

Decided alone to carry the original per-arm figures as planning estimates and report the new engineering usage
alongside the formal charge. No host job or sealed data access in this Local unit.
