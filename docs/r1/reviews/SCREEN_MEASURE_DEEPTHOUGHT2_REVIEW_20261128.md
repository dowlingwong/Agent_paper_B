# Independent tier-E review of the deepthought2 screening re-issue

Verdict: ACCEPTED
Code-Commit: a7c2f8fb7b90b3237e61672c6b48112365dcdb24

Task `local/20261127-31`, published base `15fe05b0d0a08ae5c37eb582eb0c3f04d67e0b2a`.
The accepted draft is `93892f19d8a7a92eafe51157428c54afbb4363f6`, with SHA-256
`84381da7a74f9406b60383c4b07682a4baee6c549cd1551ca8090a0bdc8cebc0`.
The tested candidate `3f373665a2f593024f2e615155b96cc483fa28b5` adds the reviewed fixture
delta. It carries the same production files as the code commit above.

A fresh Claude screening review session `617943fc-85df-4fcf-84d7-9187cc4d20ac` found the
production binding sound. It withheld note acceptance at `6fb72171` because the STOP paragraph
omitted return to the author and could imply permission for another attempt. The independent
delta review `5905664b-ea09-4760-80b9-4e390b15730f` accepted the restored STOP disposition,
the receipt instruction for the three thread controls and the test-only corrections. The desk
confirmed the command sets `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` to 1.

The published note selects the host. The original screening route retains the 16-worker bound.
The deepthought2 route also requires the new PLAN row, exactly the signed worker count, an affinity
mask covering those workers within 64 CPUs and empty CUDA visibility. The admission check reserves
10 cores after accounting for the workers. The 60-second guard uses whole-host load and online CPU
capacity once the launch has bound affinity. The shared batch path, replayed runtime, harness pin,
harness equivalence, cache tree and each worker probe retain their strict checks. The key block
carries the same design and companion hashes and the same seed block.

Desk verification used a private Git publication fixture. An unpublished note and an unsigned
published draft both refused. A simulated signed publication passed with real Git provenance, PLAN,
companion, code pins, design, cache citation and seed checks. Host resources, replay runtime and
harness equivalence were simulated. Fresh candidate targeted checks passed 115/115. The launch
shell block passed `bash -n`. The Claude reviews were static reviews of the supplied code and diffs.

Compute verifies the live scheduler entitlement, CPU affinity, replay paths and caches and captures
the launch receipt under the published note. The previous attempts stay in the ledger and their
data do not enter this measurement. The new host's co-tenancy STOP goes to the author.
