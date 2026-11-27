# Review of the P.4 direct-launch unit (branch `mac-p4-direct-20261126`, tip f90c1bff), round 1

Summary written by the implementer from the coordinator's relay of the fresh tier-E review; the coordinator will
replace it with the reviewer's full text after the re-check. AI-assisted (Claude).

Verdict: NOT ACCEPTED (round 1)

## Blockers

- **B1 (R1-QTORCH-AMEND).** One Track P smoke and one E0 equivalence check are required per GPU model actually used
  (the H200 host config comment repeats it). The unit admitted `ada_rtx6000` (sm_89) while the note and the switch knew
  only `h200_smoke_e0:`. Requested fix (a): a per-class smoke/E0 key line, required by the switch for every admitted
  class and citing that class's records on `origin/main`; a matching note-draft line and a P5 sentence; the Ada
  smoke/E0 precede the Ada probe. Alternative (b) for the coordinator: read R1-QTORCH-AMEND ("on HTCondor") as not
  binding the direct launch. Recommended (a).
- **B2.** `p4_render_jdl.render` requested `+RequestWalltime = arm_walltime_s(spec, arm)`, the largest over the
  classes, while `validate_spec` checks 86,400 s per HTCondor class with that class's own estimate: with Ada kev-4b at
  16.0 h the H200 JDL requested 88,200 s and validation passed. Fix: render the class's own value; keep the largest
  only for the projection, the pending-submission charge and the incomplete-record bound; a test with unequal
  per-class estimates.

## Minors

- **M1.** A SIGKILLed launcher releases the flock while the container runs: pass the lease descriptor to the child
  (apptainer); for docker, `launch` refuses and `cards` reports a running P.4 container.
- **M2.** Create the once-only launch marker after the lease and card checks succeed, or document that any refusal
  uses up the stage.
- **M3.** `threshold_report` used `>`; reaching the figure is reported (`>=`); report the threshold at seal and in
  the `validate` CLI too.
- **M4.** Refuse sealing an attempt as HTCondor when `p4_run.log` names a direct host class and no launcher record is
  present.
- **M5.** State that the seal receipt's `stop_class` is authoritative after reclassification.
- **M6.** The note draft's P7 must cover `trackp_ada_v1.json` too.
- **M7.** State that changing `direct.min_free_mib` after the fill needs a hand edit and a reviewed commit (new
  sha256).
- **M8.** The Ada probe runs on an empty card, or its record flags `card_shared` and marks the fit unreliable.
- **M9.** Create the intermediate `work_root/<run_id>` directories with mode 0700 explicitly.

The corrections are listed in `docs/r1/reports/trackp_p4_direct_20261126/P4_DIRECT_UNIT_20261126.md`
("Review round 1 corrections").
