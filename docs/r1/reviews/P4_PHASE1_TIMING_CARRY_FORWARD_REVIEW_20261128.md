# Independent review of the unsigned Ada P.4 timing carry-forward

Task `local/20261128-13`. Timing-only amendment to the draft at `be602ef3b8d2661406da5b8e17fb76929da2acf5`,
tested against its integration with published `main` `66aa4e10b107d81d6abc305fb1fa16879ff737d7` at
`90483b189e515238c14d4d1a969d6a9434bc1613`. The reviewer did not author the amendment.

**Verdict: ACCEPTED** for the unsigned timing carry-forward. Final phase-1 review awaits the signed P3 spec
and publication of the P5 timing record and review.

- The reviewer checked the draft key lines and confirmed that only P5 changed. The Ada route, label and split
  pins, exact spec and harness SHAs, arms and order, LR grid, readiness and checkpointing, 3.10 GPU-h formal
  probe charge and its receipt hashes are byte-identical. The fresh E0 criterion and its narrow margin stay
  as in the accepted record.
- All 43 timing manifest entries at Compute tip `902ef2c67c2d7f487b951fefde6e0dc9e5cfa02f` verified. The
  reviewer independently matched the four kernel bindings to the staged smoke and recomputed the median
  training-step times from synthetic metrics. In phase-1 arm order they are 1.0230, 5.4855, 1.0528 and 5.6378 s.
  The prior per-arm projections are 2.52, 6.79, 2.51 and 6.75 GPU-h. The 18.57 GPU-h per-arm subtotal and
  2.00 GPU-h startup give the 20.57 GPU-h phase-1 projection. The extra timing rounds consumed 0.3233 GPU-h.
  Together with the existing 3.10 GPU-h probe charge these give 23.99 GPU-h in usage plus projection against
  the 40 GPU-h reporting threshold. The accepted minor wording change calls the four numbers per-arm projections.
- The timing report SHA-256 is `24e0d7137ec29421966d70541e0448e96e6d269287d3ac1baf1f91d634e86bbc`, and its
  independent Compute re-check SHA-256 is `37d4b6dd3f09b0b4e94d9f8cab9a4daac09db0a81bd3e03e3ec40b11996817b5`.
  Both match the cited branch objects.
- The exact reviewed one-file spec candidate `befb58c8b3f5b222a2cf8973e513b252235453fc` is unsigned. Its sole
  parent is `0b46595418bb21dc0e8e5b234b30f2a84ac5082c`, and the spec SHA-256 is
  `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6`. The draft retains `approved: false`.

The review used published engineering records, pending Compute branch artifacts and synthetic timing captures.
