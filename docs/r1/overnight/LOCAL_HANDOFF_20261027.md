# Local R1 handoff — 27 October 2026

AI-assisted. Paper branch `local-20261026` and the separate `r1-local-*` harness branches are for coordinator review and merge; the pinned harness `897d83c` remains unchanged. PLAN §10 records the 27 Oct author rulings. Existing repo tests may run on CPU within R1-LOCAL-TEST-SCOPE; LLM inference, real-weight downloads, GPU/MPS, evidence or label runs and remote hosts remain excluded.

## Accepted for their stated purposes

- L0 original baseline is an accurate historical test record. The incident is **closed within scope after clarification**; the original observations and unknown subprocess outcomes remain in `docs/r1/reports/LOCAL_TEST_SCOPE_INCIDENT_20261027.md`. A corrected-environment baseline and comparisons are recorded separately in `docs/r1/reports/LOCAL_BASELINE_CLARIFIED_20261027.md`.
- L1 route/proposals, L2 proof audit and simulation reproduction, L3 conditional timeline proposal and L5 Track P feasibility proposal were independently accepted for their limited purposes. Author decisions now supersede corresponding proposals in PLAN §10; none is an evidence authorization or author proof check.
- `docs/r1/reports/LOCAL_RESUME_STAMP_TRACE_20261027.md` and independent review confirm the conditional resumed E1/skip defect at the old pin. The author says it does not apply to sweep 1; `SWEEP1_RESUME_STAMP_NOTE_20261027.md` gives source and limits. The fix at harness `r1-local-20261027` commit `7567215` is independently accepted; E2 live/resume verify rescue and veto now restamp final records. Historical impact is unestablished. Integrate as a new pin only after sweep 1 and B.2, before C.3 (R1-RESUME-STAMP).
- `docs/r1/proposals/THEORY_CORRECTIONS_20261027.md` is independently accepted for **author proof check only**; the T2/T4 claim files remain unedited. The author must choose and check the one-step or strong interventional formulation.

## Outstanding author/coordinator questions

1. Which of the proposed corrected theory statements and DI formulations survive the author's proof check?
2. Can the coordinator obtain revision-pinned authoritative 1GC task/evaluator sources, and what Track G audit budget and container availability should be used? Track G role is already decided: evaluation/transfer only, validation-only selection for test-scored tasks; G.3 on Ada. MLGym is deferred unless a container is available by 10 Nov.
3. For the H.8 table split column, does train/val use `z_train` and test use `z_eval`? The author-authorized final attempt was independently rejected for mixed-split episode exposure, no-op execution and stale reset state. Further H.8 implementation needs a new author ruling; Track P takes accepted integration through main after coordinator merge.
4. How should the retained byte-identity and other environment failures be investigated on the full-environment host after merge? The author accepted the restricted Mac comparison criterion specifically for L4.4 and L4.5.

## Incomplete work

- L4.1: 1GC source and adapters remain unavailable; real MLGym integration is conditional. The autoresearch fake CLI smoke at `d63cb91` is independently accepted as a subitem. Three isolated harness branches are pushed (`r1-local-20261027-autoresearch`, `-1gc`, `-mlgym`), not merged; overall L4.1 remains unaccepted.
- L4.2: the author-authorized final attempt `d9a4338` computes table utility, but independent `LOCAL_L4_2_FINAL_REVIEW_20261027.md` remains **NOT ACCEPTED** for split exposure, no-op execution and stale reset. No further attempt is authorized by the one-more-attempt ruling. The prior pilot-table fixture-scope incident remains recorded.
- L4.3: partial source-traced pilot renderer and focused tests exist; full pipeline and acceptance are pending. The noise sigma transformation from committed pilot runs is independently accepted as a limited engineering check, with loaded-code provenance caveats. The historical offline evaluator trains LightGBM and is not to be run as an evidence or label job on the Mac. Pilot outputs are not the current gate.
- L4.4 and L4.5 are independently accepted under the author-amended restricted Mac comparison criterion. Pre-scaffold selected outcomes match, and item fixtures pass. Restricted comparisons predate some later changes; do not infer full-suite equivalence. The full-environment comparison is required after merge.
- L6: anonymous draft builds with the 2026 placeholder style; author-checked theory statements/proofs, companion metadata and documented bibliography uncertainties remain open. L6 is not accepted.
- L7: the route, specification, manuscript outline and post-decision scan were independently accepted after corrections; see `LOCAL_L7_REVIEW_20261027.md`. This does not accept L4.2 or L6.

Internal targets are labels 3 Nov, B.7 26 Nov, D.3 complete 20 Dec and manuscript 10 Jan (R1-INTERNAL-FREEZES), not official conference deadlines. The author has decided DAC framing, focused C1–C3 scope, Track P essential/ablation stages and H.8 design. The one additional H.8 implementation attempt was independently rejected; a further attempt needs a new author ruling.
