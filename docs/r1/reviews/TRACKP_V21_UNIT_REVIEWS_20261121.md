# Image v2.1 rerun units — three independent pre-submission reviews (21 November 2026)

Three fresh-context reviewers checked the staged v2.1 units against the tracked staged units and
the R1-TRACKP-IMAGE-V21 authority. All three returned **ACCEPTED** for the unit bytes, with the
sequencing gate explicitly noted (I2/I3 must pass before the smoke, and the smoke before E0).
The reviewers read the repository, the build record, and ghcr.io; none of them modified a file.

## 1. I2 and I3 (`i2/`, `i3_nemo2/`) — ACCEPTED

- i2/probe.jdl differs from its tracked unit only in the cpu digest
  (`08a36eff…` → `c152c329…`); rebuilt JDLs from the tracked units by digest substitution are
  byte-identical.
- i3_nemo2/probe.jdl differs only in the gpu digest (`b1144ece…` → `31478d99…`) and the recorded
  L40S→H200 requirement (R1-TRACKP-I3-H200; the JDL actually submitted for the v2 H200 run,
  `i3_h200_20261121/probe.jdl` sha `65d9ccb…`, differs from the v2.1 JDL only in the digest).
- `i2/s4_run.sh` `c963f696…`, `i3_nemo2/i3_run.sh` `53b79bc6…`: byte-identical; the staged
  `STAGE_SHA256SUMS` verifies 23/23 on the tracked unit.
- Every resource field unchanged (walltime 3600, disk 30,000,000 KB, cpus, memory, 1 GPU, queue).
- Both new digests resolve at ghcr.io as single-platform OCI manifests; no tag is referenced.
- Provenance caveat recorded: the cpu target is an ordinary rebuild (digest differs through
  re-resolved base packages too); I2's PASS certifies the rebuilt cpu image.

## 2. Track P H200 smoke (`smoke_h200/`) — ACCEPTED (unit)

- probe.jdl differs only in line 2 (the gpu digest); 770 bytes total, 60 bytes differ, prefix and
  suffix identical. `probe.sh` `24688a10…` is the accepted script; the `kernels_bound` post-check
  block (`assert report.get("kernels_bound") == ref["kernels_bound"]`, `kernel_import_error` absent,
  numeric checks pass) is byte-identical and not weakened; the reference carries all four fast
  bindings.
- request_disk 35000000, walltime 3600, whole H200 on NEMO2 by device name; no tag fallback.
- Submission held until the v2.1 I2/I3 results exist (R1-TRACKP-IMAGE-V21 order).

## 3. E0 (`e0_h200/`) — ACCEPTED (unit)

- probe.jdl differs only in the gpu digest (`977cd126…` new vs `eeb4606b…` tracked).
- All other unit files byte-identical to `stages/e0_h200/` and to the TASL-7 comparator/reference
  (`compare.py` `bd957c0d…`); the pre-registered tolerances (`width_slope_vs_label` 0.05,
  `mean_slope` 0.05, `rps` 0.10 rel.) and the `data_manifest_sha256` assertion are unchanged.
- Comparator fail-closed check exercised: pass case exit 0; three miss cases exit 1.
- Submission held until the v2.1 I2, I3 and smoke records are committed and accepted.

## Observations carried forward (not unit defects)

- The tracked `stages/*/probe.jdl` still pin the v2 digests; the v2.1 units live in the submission
  staging directory, and the new probe.jdl hashes are recorded with the results.
- The image's `VERSIONS.txt` still carries the source-build diagnostic line
  `env3_causal_conv1d_arch=8.0;8.9;9.0` although v2.1 installs the wheel; the wheel itself is
  `1.7.0`, cp312, `.target sm_90`.
- `probe.sh`'s async `tee` is inherited and unchanged.
