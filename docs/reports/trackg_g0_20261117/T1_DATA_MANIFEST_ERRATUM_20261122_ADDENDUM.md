# Addendum to the T1 data-manifest erratum record (editorial)

Written by the coordinating chat (Claude, AI-assisted), 22 November 2026, when publishing the record. **Editorial only.**
It changes no value and no conclusion. The record `T1_DATA_MANIFEST_ERRATUM_20261122.md` beside this file is published
byte-identical to the reviewed bytes (sha256 `9b40944be4df5f214066d689f7f0537590ed95895f9754b55630d8e774077799`,
branch `ops-t1-data-manifest-20261122` @ `ac298f25`). The re-issued G.1b, cross-check and G.4 notes cite those bytes.

The record's independent review (`docs/r1/reviews/T1_DATA_MANIFEST_ERRATUM_REVIEW_20261122.md`, ACCEPTED) sets three
editorial conditions (§4 of the review). They are met here, outside the record, so that the cited bytes stay the
reviewed ones (path (i) of the TASL launch-chain review, `docs/r1/reviews/TASL_LAUNCH_CHAIN_REVIEW_20261122.md`).

- **C1 (from the review's F1/F3): node-file hash attribution.** Read the record's node-file hashes as the review
  corrects them: `mlgym_fmnist` `e5005358…` and `mlgym_cifar10` `6ff99228…`, both verified byte-for-byte (`cmp`) by
  the reviewer. In §1.1, "every node" means the two erratum nodes, `mlgym_fmnist` and `mlgym_cifar10`.
- **C2 (from F2): reproducibility scope.** §6's sentence "every claim above is reproducible from those captures" is
  narrowed to the following:
  - in the captures: the hashes, the byte comparisons, the manifest diffs, and the setup outputs and times;
  - stated in the record but not captured: the operator's outer invocation (CPU pinning, `HF_HOME`).

  No conclusion of the record rests on the uncaptured `taskset` claim.
- **C3 (from F4): external activity.** The record's paragraph on concurrent activity on TASL-2 (a `gpu0.lock` and
  `harness_ar` writes that were not this session's) is a disclosure, not an attribution. It touched no hash the record
  uses. The paths involved (`harness_ar`, the GPU lease) belong to the TASL-2 AR-pin host check at harness
  `2d09f9a9`, which ran the same day (`ops-t1-ar-pin-20261122`, then `main-t1-ar-pin-binding-20261122`, published
  separately). The coordinating chat has not cross-checked the timing, so this remains a pointer, not an attribution.
