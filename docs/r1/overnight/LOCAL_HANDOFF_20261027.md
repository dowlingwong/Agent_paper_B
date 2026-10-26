# Local R1 handoff — 27 October 2026

AI-assisted. Paper branch `local-20261026` and the separate `r1-local-*` harness branches are for coordinator review and merge; the pinned harness `897d83c` remains unchanged. PLAN §10 records the 27 Oct author rulings. Existing repo tests may run on CPU within R1-LOCAL-TEST-SCOPE; LLM inference, real-weight downloads, GPU/MPS, evidence or label runs and remote hosts remain excluded.

## Accepted for their stated purposes

- L0 original baseline is an accurate historical test record. The incident is **closed within scope after clarification**; the original observations and unknown subprocess outcomes remain in `docs/r1/reports/LOCAL_TEST_SCOPE_INCIDENT_20261027.md`. A corrected-environment baseline and comparisons are recorded separately in `docs/r1/reports/LOCAL_BASELINE_CLARIFIED_20261027.md`.
- L1 route/proposals, L2 proof audit and simulation reproduction, L3 conditional timeline proposal and L5 Track P feasibility proposal were independently accepted for their limited purposes. Author decisions now supersede corresponding proposals in PLAN §10; none is an evidence authorization or author proof check.
- `docs/r1/reports/LOCAL_RESUME_STAMP_TRACE_20261027.md` and its independent review confirm a conditional resumed E1/skip `repeated_bad_count` defect at the pin; historical impact and E2 verify behavior are unestablished. Integrate harness fixes only after sweep 1 and B.2 as a new pin (R1-HARNESS-NEXT-PIN).
- `docs/r1/proposals/THEORY_CORRECTIONS_20261027.md` is independently accepted for **author proof check only**; the T2/T4 claim files remain unedited. The author must choose and check the one-step or strong interventional formulation.

## Outstanding author/coordinator questions

1. Which of the proposed corrected theory statements and DI formulations survive the author's proof check?
2. Can the coordinator obtain revision-pinned authoritative 1GC task/evaluator sources, and what Track G audit budget and container availability should be used? Track G role is already decided: evaluation/transfer only, validation-only selection for test-scored tasks; G.3 on Ada. MLGym is deferred unless a container is available by 10 Nov.
3. How should the Track P utility producer prove fixed-A1 reference, label/evaluation split and price provenance? H.8 is approved and edits are made, but the third independent review rejects acceptance until this is established. Track P takes accepted integration through main after coordinator merge.
4. What response is appropriate for the retained byte-identity failures, restricted paper comparison exclusions and other recorded environment failures? Do not relax an acceptance criterion.

## Incomplete work

- L4.1: 1GC source and adapters remain unavailable; real MLGym integration is conditional. Three isolated harness branches are pushed (`r1-local-20261027-autoresearch`, `-1gc`, `-mlgym`), not merged; see `LOCAL_L4_1_HANDOFF.md` and review.
- L4.2: H.8 code and fixture tests exist; independent review remains **NOT ACCEPTED** for unverified utility provenance after three engineering attempts. See `LOCAL_L4_2_HANDOFF.md` and implementation review. A reviewer also ran one pilot-table test file outside the H.8 fixture-only instruction; the review preserves the incident and results.
- L4.3: partial source-traced pilot renderer and focused tests exist; full pipeline and acceptance are pending. The historical offline evaluator trains LightGBM and is not to be run as an evidence or label job on the Mac. Pilot outputs are not the current gate.
- L4.4 and L4.5: corrected harness and restricted paper baseline/repeat match outcome IDs and were independently checked. Both tasks remain unaccepted: excluded cases prevent a full-suite comparison; a fresh restricted pre-scaffold comparison matches all 581 common outcomes and 13 new predeclaration cases pass, but matching IDs do not imply identical test code. See the item reviews and `LOCAL_BASELINE_CLARIFIED_20261027.md`.
- L6: anonymous draft builds with the 2026 placeholder style; author-checked theory statements/proofs, companion metadata and documented bibliography uncertainties remain open. L6 is not accepted.
- L7: the route, specification, manuscript outline and post-decision scan were independently accepted after corrections; see `LOCAL_L7_REVIEW_20261027.md`. This does not accept L4.2 or L6.

Internal targets are labels 3 Nov, B.7 26 Nov, D.3 complete 20 Dec and manuscript 10 Jan (R1-INTERNAL-FREEZES), not official conference deadlines. The author has decided DAC framing, focused C1–C3 scope, Track P essential/ablation stages and H.8; no further permission is required for those already authorized choices.
