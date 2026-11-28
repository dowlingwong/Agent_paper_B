# Independent tier-E review — Ada P.4 phase-1 P3 and P5

**Verdict: ACCEPTED.** Reviewed task `local/20261128-19` at
`4b799dfecf98adae9efc82ad2fc33250742d8f5a` against published main
`4196ec47171c4513b5905cc0c2f4d5d77691b621` and the prior accepted P5 draft
`ef11f990aca966808a632237631bdc13b9aa5d8f`. The unsigned note SHA-256 is
`47019d4ce012645f98bace3d6d2a6f4810368b180e569c4dd9648f33bf90d3e5`.

## Findings and scope

- **P3 PASS.** The signed commit `fcfd63f3f6e57c64c7f9c5a233a937dbfbbf6576`
  is an ancestor of the verified remote main and its sole parent is
  `0b46595418bb21dc0e8e5b234b30f2a84ac5082c`. The only file it adds is
  `r1/scripts/htcondor/trackp_p4/p4_spec_ada_phase1_20261127.json`. The tree
  equals the reviewed `befb58c8b3f5b222a2cf8973e513b252235453fc` tree.
  The spec SHA-256 is
  `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6`.
  `git verify-commit` with the published allowlist verified principal
  `r1-p4-phase1-20261128`. The resulting ED25519 fingerprint agrees with
  the published public key and the note
  (`SHA256:4Pw8bY6TGiiEhO0dik670Cj8p0JRCSAgqmiACRKbiA8`).
- **P5 PASS.** The accepted per-card smoke and fresh E0 reviews and the
  accepted-with-minors timing review are on main. All 43 timing manifest
  entries verify. The timing record and its review match the draft's
  SHA-256 values `24e0d7137ec29421966d70541e0448e96e6d269287d3ac1baf1f91d634e86bbc`
  and `37d4b6dd3f09b0b4e94d9f8cab9a4daac09db0a81bd3e03e3ec40b11996817b5`.
  The draft preserves the fresh E0 pass at `2.9494e-5` against `3.04e-5`,
  the cross-host slope bound, and the 21.8% Ada and 39.9% TASL-7
  within-host spreads. The four estimates, the 3.10 GPU-h formal probe
  charge, and the separate 0.3233 GPU-h timing use agree with their sources.
- **Scope.** Relative to the earlier accepted draft, P3 is the only
  structured field that changes. The P5 text, Ada-only lease and venv,
  harness, arms, splits, label pins, readiness, checkpointing and
  first-arm order carry forward. `approved: false` remains in the draft.
  A same-directory Markdown design link in the first candidate would
  have broken at publication. The correction resolves from both
  `docs/r1/proposals/` and `docs/r1/authorizations/`; all relative links
  were checked from both locations. The published-base diff contains
  only the proposal and passes `git diff --check`.

## Independent checks

- The official parser refuses the actual draft at `approved: false`.
  Setting the approval flag in memory for the parser check yields P1–P8
  PASS and passes `check_binding` against the signed spec. Launch-strength
  spec validation passes, as do the published smoke/E0 citation and
  probe hours, amount and charge-file checks, and all four canonical
  Ada descriptor renders. The machine projection is 23.67 GPU-h
  including the formal probe and 29.855 slot-hours.
- `verify_launch_p4` passed in the tracked-clean exact signed checkout
  at `fcfd63f3`, with the live remote main matching the fetched
  `origin/main`. Its `paper_commit` is the unchanged signed spec parent.
- The unmodified official switch `check` passed an isolated end-to-end
  synthetic stage using the Ada descriptors and published prerequisite
  records. The fixture used fabricated table and partition bytes,
  matching fixture hashes, and a simulated published note. A changed
  descriptor and an unpublished, unmatched note were refused. The
  focused pytest collection attempt in the available Python 3.12
  validation environment stopped on the missing `torch` dependency.
  This unit changes documentation. The exact real-input stage check
  belongs to the post-publication launch path.
- No host job, submission, approval change, or access to real label,
  test, or sealed files occurred in this review.

## Publication handoff

The coordinator publishes the authorization under
`docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md` under
R1-P4-PHASE1-SIGNATURE (4). Compute fetches that publication into the
tracked-clean checkout at `fcfd63f3` and copies the exact published note
blob to its authorization path in that checkout. The switch matches the
note bytes to `origin/main`, and the launch-tree check binds the signed
checkout to the spec parent. Compute verifies the actual staged inputs
with the official switch and checks the ledger for
`trackp-p4-p1-20261122-a` before the first-arm handoff.
