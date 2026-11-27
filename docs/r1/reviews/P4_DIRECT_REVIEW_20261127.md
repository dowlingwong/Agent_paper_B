# P.4 direct-launch unit review (R1-HOST-FREE, rows (g)): round 1 and re-check, 27 Nov 2026

ENGINEERING_ONLY. Independent tier-E review, AI-assisted: a fresh Claude agent that did not write the unit.

**Scope:** card `local/20261126-06` unit 1, and rows (g) of card `-07` items 3–4.

**Branch:** `mac-p4-direct-20261126`.
- Round 1: `f90c1bff` (code `df6aef36`, a merge of `main` `47df6f55`, the report).
- Re-check: `00920c68`.

**Authority rows:** R1-HOST-FREE, R1-CARD-SHARE, R1-NO-TIMEOUT, R1-STEP-ORDER, R1-TRACKP-P4-DECISIONS, R1-TRACKP-P4-RUNNER-DECISIONS, R1-P4-PROBE-CHARGE, R1-TRACKP-IMAGE-V22-B, R1-T1-HOST-TASL, R1-S2-LABELS-TRAINDEV-RELEASE, R1-QTORCH-AMEND, R1-HTC-QTORCH.

**Conduct:** read-only. No credential, label, test-partition or evaluation file was read, and nothing ran on a host.

**Record:** the local worker transcribed this from the reviewer's full text. It replaces the implementer's abridged summary, which the reviewer found faithful but incomplete.

## Round 1 (`git diff 47df6f55 f90c1bff`)

### Tests

- **`test_trackp_p4_direct.py`:** 36 passed.
- **`test_trackp_p4_runner.py`:** 159 passed, with torch (`~/anaconda3/envs/hupdate/bin/python`) and `AR_HARNESS_ROOT` set.
- **Removed assertions:** every one belongs to an intended change: the spec shape, the third `p4_job.sh` argument, the note's host lines, and cap refusals replaced by threshold reports. No unrelated assertion was weakened.

### Blocking findings

**B1. A new GPU model (Ada, sm_89) is admitted for training without the per-model smoke and E0 check.**
- R1-QTORCH-AMEND requires one Track P smoke and one E0 equivalence check per GPU model actually used.
- The unit had only `h200_smoke_e0:`, and the switch required only that line (`p4_switch.py:73`).
- Image v2.2 builds 8.0;8.9;9.0, but only 9.0 has been run (smoke 759997 with `kernels_bound`, E0 760000).
- **Failure scenario:** the arms train on sm_89 with no check that the kernels bind or match the reference. The probe records only timing and memory, so it does not catch this.
- **Fix:** either
  - (a) a per-class key line, required by the switch, with records on `main`, run before the Ada probe; or
  - (b) a recorded coordinator reading that the row does not bind a direct launch.

**B2. The H200 JDL took the walltime maximum across classes.**
- `p4_render_jdl.py:107` used the maximum over classes, while validation checks each class's own value.
- **Reproduction:** with Ada kev-4b at 16.0 h, validation passed and the H200 JDL requested 88,200 s, over the pool's 86,400 s per job.
- **Fix:** render each class's own value, keep the maximum for charges only, and add a test.

### Minor findings

- **M1:** a SIGKILLed launcher released the flock while the container kept running.
- **M2:** any refusal used up the stage.
- **M3:** the threshold report used `>` instead of `>=`, with no report at seal or from the `validate` CLI.
- **M4:** a direct attempt could be sealed as an HTCondor one.
- **M5:** state that the receipt's `stop_class` is authoritative.
- **M6:** note P7 lacked the Ada config.
- **M7:** `min_free_mib` cannot be refilled after the fill.
- **M8:** a probe on a shared card gives invalid fit and timing.
- **M9:** intermediate directories took the umask default.

### Found sound

- **The HTCondor path,** apart from B2.
- **Fail-closed identity:** exactly one GPU of the declared class; the lease UUID bound into seal and assembly; env3 and image identity unchanged.
- **`p4_direct.py`:**
  - refuses root;
  - checks the manifest, the digest and runtime allow-list, the hostname and the marker;
  - launches once per stage into a fresh directory, under `flock -n`;
  - checks free memory and shares a card when it must;
  - uses docker with `--gpus device`, or apptainer with `--nvccli`;
  - sets no timeout;
  - if all eight cards are visible, the identity check STOPs.
- **Seal and charges:**
  - a complete record is charged max(lease span, record hours); an incomplete one max(span, walltime, record hours);
  - a direct record without a launcher record is a STOP;
  - both launch kinds are summed;
  - nothing refuses at 40 or 64.
- **The OOM reclassification is metric-blind.** It acts only on the CUDA-OOM `ArmStop`.
- **Host configs:** H200 has 19 values, Ada 26.
- **Note draft:** correct apart from B1 and M6.

### D1–D3

- **D1:** agree with A. Mixed GPU models across arms are recorded; no analysis by hardware class without an amendment (R1-HOST-FREE (4)).
- **D2:** agree with A, level 1. No row restricts where released train/dev labels are copied. Keep owner-only modes.
- **D3:** keep (0, 20] h until the Ada probe.

Round-1 verdict: not accepted.

## Re-check (`git diff f90c1bff 00920c68`)

### Tests

- **`test_trackp_p4_direct.py`:** 41 passed (5 new).
- **`test_trackp_p4_runner.py`:** 159 passed with torch.
- **Removed test:** `test_a_refused_launch_is_sealed_at_its_launcher_wall_clock`, intended under M2.

### Blocking findings

**B1 resolved, with option (a).**
- Each class has a `smoke_label`. The switch requires each admitted class's line, citing `docs/r1/…md` records that exist on `origin/main`. A class the spec does not admit reads `none`.
- The note has an `ada_smoke_e0:` line and a P5 sentence.
- The Ada smoke and E0 come before the Ada probe.

**B2 resolved.** In the same scenario the H200 JDL requests 37,656 s, its own value. The maximum, 88,200 s, stays for the charges. A test is added.

### Minor findings

- **M1:** fixed, with `pass_fds` for the lease and a docker label guard.
- **M2:** fixed. The order is now prepare, then acquire, then an O_EXCL claim; a refusal before the claim writes nothing.
- **M3:** fixed, with `>=`, and a report from the `validate` and `seal` CLIs.
- **M4:** fixed.
- **M5:** stated.
- **M6:** fixed.
- **M7:** stated.
- **M8:** fixed: `card_shared_arms` and `fit_and_timing_reliable`.
- **M9:** fixed: every directory level is 0700.

### Open after the re-check

- **R1 (minor).** The `ada_smoke_e0:` check is syntactic: a line citing the H200 record would pass. The signature and the review of the cited records must confirm the records are Ada-specific. Optional hardening: require a `smoke_host_class: <class>` line in the cited record.
- **M1 residual.** Whether apptainer's starter keeps the inherited lease descriptor open is unverified. The Ada survey can confirm it with `lsof`.

Verdict: ACCEPTED WITH MINORS
