# Independent review of Paper B Sweep 2 integration

**Initial review commit:** `e76e50a97b1cede10516333e9b2b2eaf0dc4832b`

**Code-Commit:** `16e679573a2d00a887e72d99a4bd120861395b14`

**Verdict: ACCEPTED** for the Mission 2a and 2c code integration at the reviewed tip. I found no remaining code blocker after the fixes below. The scheduler operation and authorization prerequisites are tracked in the launch checklist.

## Scope and authority

I compared the integration and its merge resolutions against the base `50176481cbc85fb9e5b5dd97887043dea6e528fb` and checked the four requested inputs `d9ff7813`, `84a0dc30`, `1e3b0320`, and `f77612d1`. I read Mission 2 of the cluster prompt, the published-base PLAN, the three pending decision rows at `f04a7b93`, the Sweep 2 runbook, and S2-M1 v6. I treated the pending rows as the launch specification the integration is intended to support. The local published-main snapshot still points to the base. This review makes no authorization or launch-readiness determination.

I reviewed code and engineering metadata. No jobs were submitted, and no credential or sealed label files were opened. The probes loaded source blobs from the review commits and used temporary synthetic data, a synthetic liveness seal, mocked Git calls, and a mocked submitter. I independently ran the full HTCondor-focused suite at `16e67957` with Python 3.13 and the pinned harness. It passed **376 of 376**. The initial full-suite log contains failures. The operator is running the integrated and baseline suites in the same isolated environment. Their final results and the comparison are pending.

## Findings

1. **Blocking, fixed in the follow-up. C3b cannot produce the required launch-commit record.** `sweep2/s2_c3b_lib.py:53–54,411–415` admits only `9ae6d877` and `50176481`, while `sweep2/s2_c5_switch.py:195–208` requires the exact new launch commit. I replaced both paper-commit fields in the C3b engineering example with `e76e50a9`, which produced a STOP at the hard-coded list. The follow-up uses the full spec-declared commit, checks frozen inputs after checkout, and records the launch binding. The same probe accepted a full dynamic commit on the follow-up.

2. **Blocking, fixed in the follow-up. S2-C5 accepts a different effective submit description.** `sweep2/s2_c5_switch.py:145–155,214–216` checks line membership and a digest supplied by the same spec. The real verifier accepted a synthetic JDL that transferred an alternate spec path and added `request_GPUs = 0` and `queue 2` after the expected lines. It also accepted an arbitrary chunk ID. Canonical renderer equality and the fixed node/memory chunk identity close these cases in the follow-up. The positive synthetic guard path passed.

3. **Blocking, fixed. The runtime launch settings and fallback could diverge from the review.** C2 validated only the first occurrences of exam flags at `sweep2/s2_c2_lib.py:170–186`. A second thinking override survived both validation and construction of the actual server argv. The renderer also honored an unvalidated top-level diagnostic selector on a C2 spec and turned the L40S preference into a hard H200 requirement at `sweep2/render_jdl.py:40–50`. C3b calculated a server-settings binding but omitted it from the record, and S2-C5 accepted a wrong binding digest. The follow-up rejected all three cases using exact flag parsing, replay-only selectors, and the persisted and verified settings hash. The replay validator now checks the complete reviewed argument list and uses the exact no-space thinking flag recorded by both historical H200 runs.

4. **Major, fixed. EVIDENCE labeling and launch settings require exact matching.** The original worker-side `sweep2/s2_c2_lib.py:287–314` accepted the run ID anywhere in the note and looked for an unanchored label substring. A synthetic note for `synthetic-review` classified `synthetic` as EVIDENCE. The launch verifier also accepted an otherwise valid spec with one transport attempt, while S2-M1 v6 fixes three. Both probes now return a STOP. The worker requires exact note fields, and the switch retains its digest and published-blob guards. The current template follows the note publication workflow and the parser requires the P4 decision reference.

5. **Major, fixed. The seal and collection accepted incomplete placement and a different image.** The original `sweep2/s2_c2_lib.py:989–1006` accepted any `ghcr.io/` prefix and only checked a host name. `collect_evidence` checked placement keys without validating values. The seal now requires the v1 image for EVIDENCE, and the reducer checks the GPU floor and placement consistency. The worker requires an unambiguous visible GPU UUID and a site and CPU model. The procfs fallback only uses a single device file. The site can come from the machine ad, the job ad's recorded CloudSite, or the known site hostname. The final probe rejected a different image and a hash-valid record with an incorrect per-campaign GPU UUID. The corresponding valid 16-chunk collection passed.

## Launch checklist items

- The machine-ad capture `sweep2/evidence/condor_status_l40s_20261116.txt:5–8` supports `TARGET.GPUs_DeviceName =?= "NVIDIA L40S"` for ranking. The C2 renderer requests the VRAM and capability floors, keeps eligible hardware as fallback, and limits the model/site pin to the engineering S2-C3 diagnostic in the follow-up. The C2, C3, and C3b dispatch paths retain their respective staged inputs and executables.
- The uniform `17,469 s` request is an allowed Mission 2a choice. An all-H200 measured projection is 25.88 GPU-h. The uniform walltime envelope for 16 jobs is 77.64 GPU-h, which is a resource upper bound. The launch spec must supply a supported GPU-hour and elapsed-time projection for the expected fallback mix before the note may be approved. Published R1-SWEEP2-LAYOUT-H200 lists `32,000 MB`, while S2-M1 v6 flags the pilot memory floor. Attach the actual H200 peak calculation for R1-SWEEP2-RESOURCES to the launch review.
- The pooled worker calculation applies the declared baseline plus five percentage points without the engineering small-sample adjustment. It preserves the zero-success, runtime-error, and per-chunk parse gates. The final reducer uses counts and job metadata. S2-C5's exclusive stage marker blocked a second call before the mocked scheduler could run. A fresh stage after a confirmed eligible interruption remains an operator action. Check scheduler state and STOP precedence before recreating a stage.
- Finish the full-suite comparison and verify the signed decision rows and exact note on published main. The launch spec requires its own independent review, completion of sweep-1 B.2 or an explicit exception, and a fresh sealed C3b 8/8 result at the final launch commit.

## Follow-up review of test isolation

**Code-Commit:** `be9d18b4e2b09f020c5502859575bab49c4ada2f`

**Verdict: ACCEPTED** for the test-isolation follow-up. This is now the accepted code tip for Mission 2a and 2c.

The prior integrated full-suite run exposed a test-order failure. The two shim import helpers deleted live `r1` modules to load a temporary stub package. The tests restored the search path through pytest's monkeypatch fixture but left the stub package in `sys.modules`, so later tests could fail to import the repository's modules. The new fixture snapshots the original `r1` and `yaml` module objects, removes all modules in those namespaces imported during the test, and restores the original objects at teardown. All six users of the shim import helpers request the fixture. This commit changes only the driver tests.

I reran the order that reproduced the leak with Python 3.13 and the pinned harness. The HTCondor tests followed by `r1/tests/test_ada_e1b_rerun2.py` passed **401 of 401** in 36.00 seconds, and the diff whitespace check passed. The full integrated suite is being rerun for comparison with the baseline.
