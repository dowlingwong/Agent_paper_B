# Independent review of sweep-2 measured GPU placement

Code-Commit: 5b8d1afa5a90d296b6bee1a9b587765a292d88f0

Parent baseline: 72f2f85b

Published authority reviewed: 235cf266ac8dc3642827b6b6467b94741617d8c5

Verdict: ACCEPTED for the measured-placement code and timing-smoke preparation

The delta covers six files. It enforces the currently admitted NVIDIA H200 for sweep-2 EVIDENCE and prepares a two-instance ENGINEERING_ONLY timing smoke for NEMO2 L40S. It does not alter PLAN, classification, image, model, harness, seed selection, or S2-C3/S2-C3b execution policy.

## EVIDENCE placement and layout

- The C2 staging entry point copies and validates the pinned note before emitting the JDL. For an authorized chunk the JDL requires `TARGET.GPUs_DeviceName =?= "NVIDIA H200"` with the existing VRAM, compute, Linux, x86-64 and CPU floors. It requests one GPU and has no L40S rank or site requirement. This admits H200 wherever eligible and discloses actual site, GPU, driver and CPU per campaign. See `sweep2/render_jdl.py:39–55, 74–92, 104–127, 233–243`.
- C2 validates the measured 5,823 s chunk, `ceil(1.5 × 5,823) = 8,735 s` request, 42,460,970 kB disk and 32,000 MB memory. The smoke report records both H200 S2-C4 engineering jobs 759751 and 759752 with real worker runs, a 30,329,264 kB disk peak and an 11,157 MB memory peak. The 16-chunk projection is 25.88 GPU-h and the sum of requested run times is 38.82 h. These quantities exclude queue wait. See published `docs/r1/PLAN.md:1299–1303`, `docs/r1/reports/sweep2_20261116/S2_C4_RESULTS_20261116.md:80–93` and `sweep2/s2_c2_lib.py:264–303`.
- Runtime verifies the allocated GPU model before cloning, then requires one allocated GPU with UUID and driver and a recorded site and CPU. The sealed-record collection independently verifies the admitted GPU class with the per-root placement and fixed chunk set. See `sweep2/s2_c2_lib.py:896–915, 1068–1122`.
- The C5 template remains `approved: false` and cites the current measured-placement and memory rows. C5 requires the matching layout values and now checks the singleton canonical H200 requirements even in check mode when a JDL is supplied. Real submit retains exact staged-byte comparison, a clean launch checkout, published-note verification, current authority rows, an exact-launch sealed C3b pass and both enable keys. See `sweep2/s2_c5_authorization.template.md:5–23` and `sweep2/s2_c5_switch.py:95–109, 125–167, 171–252`.

## NEMO2 L40S timing path

- The override requires `measurement_gpu_model = "NVIDIA L40S"`, `pilot = true`, two instances, `gpu_measured = false` and an ENGINEERING_ONLY chunk. It renders GPU and site requirements for NEMO2 L40S with the 17,469 s engineering measurement envelope. A different model or site produces a STOP record before cloning. See `sweep2/s2_c2_lib.py:213–220, 264–296, 901–904` and `sweep2/render_jdl.py:39–55`.
- The measurement gate now requires both worker root ledgers and successful worker metrics in each. This closes the case where output root count was two and only one worker ledger existed. Existing worker-error, failure-rate and proposal/parse checks still apply. See `sweep2/s2_c2_lib.py:747–798, 950–958`.
- L40S remains outside the production allowlist. Once the NEMO2 slots return, assess sealed timing and worker gates before admitting L40S against the 1.5× per-model walltime and 60 GPU-h / 48 h projections. The current code deliberately does not implement L40S admission or its future placement rank.

## Independent verification

- `git diff --check 72f2f85b 5b8d1afa` passed and the reviewed checkout was tracked-clean.
- `PYTHONDONTWRITEBYTECODE=1 ../testenv/bin/python -m pytest r1/tests/htcondor -q -p no:cacheprovider` passed, 377 tests in 3.80 s.
- `review_s2_measured_probe.py` staged all 16 node/memory pairs with a synthetic authorization and validated the exact production selector, resources and transfer inputs. It staged both memory modes for the NEMO2 L40S engineering smoke. C5 check accepted all 16 canonical fixtures and refused hash-matching JDLs with a wrong, missing or duplicate requirements line. Mocked H200/L40S/site mismatches exercised the runtime STOP before clone and its durable job record.
- A separate synthetic collection probe stopped with one missing ledger, stopped with missing successful metrics in the second ledger, and passed with complete ledgers and metrics for both roots.
- The renderer's pre-existing default first-line comment still says ENGINEERING/dry-run on a C2 EVIDENCE render. This is cosmetic. The staged note and wrapper determine the job record label, and C5 verifies the reviewed canonical render.

This accepts the code delta. Exact 5b8d1afa is not the launch commit, because it does not descend from published 235cf266 and its authority files differ. The production note, byte-identical published authority on the final launch commit, independently reviewed launch material, exact-launch C3b 8/8 and the sweep-1 B.2 prerequisite remain launch gates. This review did not submit jobs, query live slot ads, access sealed cluster data or change external state.
