# local/20261127-28 — Track P per-card GPU lease

for: compute

- Base `35c42b81880a444c55d25d604007366c7533ec82`. Branch `mac-trackp-per-card-lease-20261127` @ `801b2d49432c68f46b3658b1cb27a0d5e99ef9ad`. Independent tier-E re-check **ACCEPTED** at code `fc95186bc7071e7d62622aacea657313ea7145cd`. Review `docs/r1/reviews/TRACKP_PER_CARD_LEASE_REVIEW_20261127.md` SHA-256 `61a90bdf570d487bc7bf2800d468962e93679cf4a9fc5ffe463b1c57f65b43a6`.
- Resolve a physical index or full UUID, hold `gpu<index>.lock`, check only that card's occupancy, and verify its UUID is the sole CUDA device before executing model or kernel work. Resolve an inherited numeric CUDA ordinal through CUDA before comparing it to a physical GPU. Occupancy logging records count and aggregate memory at start and end. An invalid sample refuses success.
- Standalone P5 smoke and E0 take the empty-card path. The staged P.4 job still uses the reviewed outer launcher's free-memory check and occupancy records, the bound UUID and its job-local lock. The Ada configuration SHA-256 is `bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908`.
- First-round review findings covered CUDA and NVML ordinal ordering, invalid occupancy samples, the Ada lock directory and malformed outer-lease UUIDs. The revised path passed independent review and focused CPU fixtures. The original P5 dispatch was refused before GPU work and has no live job ID in the latest receipt.

## Verification

- Independent focused lease, trainer, E0 and P.4 direct fixtures **75 passed, 1 skipped**.
- Serial full `r1/tests` with Python 3.12.8, pytest 9.2.0, torch 2.15.0, LightGBM off the path, harness `9bb416805175149eb87b71f28d77530572aa4bce`, fresh temporary directories and `-q -p no:cacheprovider -rfE --continue-on-collection-errors`.
- Base `35c42b81` **5,013 passed, 120 failed, 3 errors, 167 skipped, 71 subtests passed**. Branch tip `801b2d49` **5,025 passed, 120 failed, 3 errors, 167 skipped, 71 subtests passed**. Identical 123 failure/error IDs and zero new failures. [Failure/error IDs](20261127-27-28-fullsuite-failure-ids.txt) SHA-256 `bdb6d456d3898cc16ae2fcad76e8a7870e2ce20122fc0837bb3e0e8baf216ff4`.
- P.4 torch files `r1/tests/test_trackp_p4_runner.py` and `r1/tests/test_trackp_p4_direct.py` **215 passed**.

## Compute handoff

After the coordinator merges this unit, resume `compute/20261127-29` using the reviewed `zli538` Ada venv, staged weights and inputs, native `nvidia-smi` and a fresh capture directory. Recheck current attempts and choose an empty allowed GPU. Use the same explicit full UUID in both commands. If CUDA visibility is already constrained, confirm it admits that UUID.

- **Smoke:** use the staged `r1/scripts/trackp_gpu_smoke.py` command with `--gpu "$CARD_UUID" --lock /data1/zli538/r1_locks/gpu0.lock`, plus the pinned model and fresh report and lease-log paths. The script resolves `gpu0.lock` to the selected card's index in the reviewed directory.
- **E0:** use the reviewed equivalence invocation of `r1/scripts/trackp.py --config r1/scripts/configs/trackp_ada_v1.json e0`, adding `--gpu "$CARD_UUID"` to its existing arguments. Standalone E0 takes its host lock directory from `direct.lock_dir`. Use its fresh run directory and obtain both samples.

Report the lease UUID and start/end counts and memory, the staged smoke and E0 receipts with accepted reviews, and the timing carry-forward disposition. The phase-1 note follows the signed P3 binding and P5 checks. Publication belongs to the coordinator. This handoff is for P5 engineering work.

Decided alone: kept operator empty-card selection and used one physical lock namespace at the Ada entry points, with CPU fixtures for the two entry paths. This unit launched no host job.
