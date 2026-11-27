# local/20261127-11 — Ada P.4 venv launcher

for: compute

- Base `98c571d22251a9d57a6d157950bd5ac8c340e17b`. Branch `mac-p4-ada-venv-20261127` @ `4a77a45ba0740d0d2ce7285b9bc6890ccb1d0248`. Exact reviewed and tested code `8f6c9ec25883df45a1014c1e48e8cfff26648553`. The tip adds the review.
- The staged entry scripts use the reviewed Ada venv at `/data1/zli538/paperb_p4_20261127/venv/bin/python`. Ada runs Python 3.12.10 and image v2.2 uses 3.12.15. Native execution verifies the active interpreter, the pinned Ada config, the exact live package freeze and one CUDA device matching the GPU lease before staging job inputs. The records capture the live freeze hash, interpreter, host, device and driver. The native launcher and its training descendants retain the lease and interruption is sealed as infrastructure.
- Independent tier-E **ACCEPTED**. Review `docs/r1/reviews/P4_ADA_VENV_LAUNCHER_REVIEW_20261127.md` sha256 `ec35c6b1b0a46cbb2b431ec6a7f346c68e8d24e11dfcb780bceaa6380b64f461`. Independent direct tests passed 45/45. Both Track P test files passed 204/204 in the local torch environment. Bash syntax, both real shell entry fixtures, the process-group interrupt, the inherited flock and the late-record infrastructure classification passed review.
- Ada host template sha256 `b04e9fa313962273288ca2ead9abe751157221db507e6d2740ecbdfdcb3d1dd4`. Raw package lock sha256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`. Canonical sorted lock sha256 `e607c1d87221999015c1cd988c38dbc2e8deb51938403e2ca2c0c2832755419b`.
- After coordinator publication, `compute/20261127-13` confirms the authorized Ada account, live interpreter and `uv` on its tool path, then fills and independently reviews `trackp_ada_v1.json` using `python3 r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py --template --host-class ada_rtx6000`. Use `direct.container_runtime=venv` and the approved launch route. Verify the current lease and run the separately scoped synthetic probe on a suitable Ada card. Job `760065` was last reported Idle and is independent of Ada. The phase-1 note needs the actual runtime and the applicable Ada smoke and E0 records before evidence training.

Decided alone: use the exact reviewed Ada environment and carry both normalized and raw freeze hashes. Preserve the existing stage and use a native process group with inherited lease handling for interruptions. Local fixtures ran without a live host call, cluster submission or sealed input read.

## Full suite

The base and exact code tip ran serially from isolated Git checkouts under Python 3.12.8, pytest 9.0.3 and
torch 2.11.0. Both used harness `897d83c8efa364ec2fdd37288241cc42e01d7274`, a fresh `TMPDIR` and no LightGBM.

```
python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests
```

| Checkout | Passed | Failed | Errors | Skipped | Subtests passed |
|---|---:|---:|---:|---:|---:|
| Base `98c571d2` | 4,829 | 193 | 3 | 161 | 71 |
| Exact code `8f6c9ec2` | 4,833 | 193 | 3 | 161 | 71 |

Zero new failures or errors. All 196 failed/error IDs are identical. SHA-256 of the sorted ID list
`2fca5b51576a0bc4a63242c259f8b1ce0ef368246dc74b464c2d8b1b96a0a03e`.
An initial baseline run inherited Git metadata into fixture subprocesses and was interrupted. The comparison uses
the complete isolated reruns only.
