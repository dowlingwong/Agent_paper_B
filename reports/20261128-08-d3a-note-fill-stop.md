# local/20261128-08 — D.3a unsigned note and launch-binding STOP

for: coordinator

- **Base** `8fbad26ac68236bbf47d2f099851a906cb4f8427`. Card at `11d09ddffaaa7f26341a5d8ae16d8b434790efe0`. **Delivery** `local-20261128-08-d3a-note-fill` @ `feb3c132526e3614b13ec0c6a629ae1c4038d961`. Draft commit `0c1db6d095e9ba8833cf5cd09a904660aecc97f2`, SHA-256 `77784011501d4db10e16b3ac954cabd4100bd98b352f90a66e9e891fe1736994`.
- **Result:** The draft cites the published P1–P8 records, including the P7 worker-gate PASS on all 14 prescribed RTX 4090 engineering campaigns. The rate was 33/271 = **12.18%**, **0.81 percentage points** below the separate stage STOP above 12.99%. The scope of the STOP here is the pre-launch binding. The evidence stage has zero campaigns.
- **STOP:** The accepted smoke ran at `-c 8192`, while frozen rev 4 §2 specifies `-c 32768` and q8_0 K/V. The smoke command carries no explicit q8_0 K/V settings. The record gives 21,607 MiB peak VRAM. Peak host RAM and scratch, exact direct campaign runtime and lease/endpoint binding, launch commit and fresh evidence run ID remain open.
- **Checks:** At `8fbad26a`, `python -B -m r1.c3.d3_verify_namespaces` returned PASS (160 seeds, 20010–20801). `python -B -m pytest -q -p no:cacheprovider -rfE r1/tests/test_d3_analysis.py` passed **53** synthetic tests. Draft structure, citations, hashes and `git diff --check` passed. Documentation-only diff, so the full software suite comparison is inapplicable. Independent tier-E review **ACCEPTED for blocked handoff**, SHA-256 `b4cc1430859d99ca7ab333a523307f72bf513890bbfc1e9862cba9d3d0343d96`. P10/P11 remain pending at the actual launch commit. [Review](https://github.com/dowlingwong/Agent_paper_B/blob/feb3c132/docs/r1/reviews/D3A_AUTHORIZATION_NOTE_FILL_REVIEW_20261128.md)
- **Next:** Coordinator routes exact-runtime engineering verification on the selected RTX 4090 route and resolves the direct-runtime comparison with frozen rev 4 §§2 and 7.2. Local then binds the exact commit and unused ID, records P10/P11 there and obtains fresh tier-E review before P9. P9 is the author's signature. The coordinator publishes the signed note before any evidence launch.

## Runtime and sizing handoff

The [accepted P7 receipt](https://github.com/dowlingwong/Agent_paper_B/blob/8fbad26a/docs/r1/reports/d3a_p7_20261128/D3A_P7_20261128.md) covers `d3a-p7-20261128-c` and `d3a-p7-20261128-d` under `d3p7b_20261128`, both complete. Its per-arm 18-campaign timing estimates use the largest observed campaign-mean latency and observed call counts, with a 1.5× scheduler request. Its primary projection is **38.3 GPU-h** and its A0R latency sensitivity is **42.5 GPU-h**, against the 140 GPU-h reporting threshold. The task card's 38.7 GPU-h differs from the accepted receipt. The draft uses the accepted receipt's numbers as engineering projections. Final elapsed wall time needs the bound placement and schedule.

For the follow-up, record environment and exact proposer settings, signed context and cache settings, GGUF and binary digests, code and input pins, endpoint-to-leased-device UUID proof, CPU affinity, and peak VRAM, RAM and scratch. Bind the reviewed deployment path that holds the leases for the applicable server and campaign scope. Use Compute's current ledger, leases and recorded IDs before any attempt. TASL-2's measured route used CPUs 16–31. TASL-7 needs its own RTX 4090 route check and the card requests its initial check on an empty card. If the selected runtime requires changing a frozen setting, route the specific change to the author. The existing worker-gate PASS remains the engineering record.

| Binding | SHA-256 |
|---|---|
| Frozen rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| G2 constants | `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93` |
| Verify seed checker | `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2` |
| Analysis | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| Analysis tests | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |
| P7 receipt and capture manifest | `a73ea6359afd5789ecf2853cf66ca0b25cfe6263eb7da82b56ca0423267d2d72`, `af84ce0d520ffb70e289521c3f11c8bf73f29f61c2a780851edbb8593019a8cf` |
| P7 accepted R3 review | `351de7f64ddc73a28e83421cc104283da16847e110e22a162991b3412dfbd94d` |
| P8 record | `72f2b9bdf65803c7b15f77acec13518bdad2048f7dac943e0eec1e273243ad17` |
| Train/dev receipt v2 | `de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c` |

Decided alone to deliver the independently reviewed unsigned draft with the launch binding held, cite the accepted P7 projection, and keep the T0 stage-failure threshold. The assigned linked Git metadata denied write access. The task and report used the writable nested Git worktrees inside the assigned workspace. All 16 pre-existing changed project paths matched published blobs at `1afa7d62` and were preserved. Local submitted zero jobs and opened zero sealed partitions.

## Round close

Fetched after pushing the task branch. Published main `8fbad26a`, coordinator `11d09ddf`, incoming Local `6916514e`, Compute `ece384d9`, Writer `079a5282`. **Local is idle with no other runnable card.** Compute's 07:56–07:57 UTC check recorded no active Paper B job. Writer is idle awaiting released results and a result-table card. [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/ece384d9/reports/20261128-23-round-status.md) · [Writer status](https://github.com/dowlingwong/Agent_paper_B/blob/079a5282/reports/20261128-writer-round-8bf88a02.md)

| Lane | Dependency or prior run to check next round |
|---|---|
| Local `20261128-08` and D.3a | The exact-runtime record and launch binding above. Prior P7 run IDs `d3a-p7-20261128-c` and `-d` are complete. Check for a routed engineering card and a newly recorded ID before any follow-up attempt. |
| G.5 final render `local/20261126-08` and experiments `compute/20261126-06` | `compute/20261128-12` still needs TASL-7 `-determinism`, `-restart`, `-tar` and `-closeserver` for `g5-p11-20261128T033600Z`, then accepted complete two-host review. Last read saw foreign compute on TASL-7. Local still needs the final `paper.commit`. Expansion addenda await the base note and per-node bindings. [Existing final-render STOP](20261128-08-g5-render-p11-stop.md) |
| Houseprice `local/20261126-01` and `local/20261127-27` | Both fixes and the S14 verdict are published. `tasl2-cpuset-mlgym_houseprice-20261128` at `paperB_cpuset_20261128T001400Z` has three distinct sealed attempts, bit-identical to the reference and within 9.486 s. Original comparison 5,013 → 5,016 passed with identical 120 failure and 3 error IDs. The accepted exact rerun command is retained in the earlier Compute handoff. [Houseprice handoff](20261127-27-houseprice-two-attempts.md#compute-handoff) |
| Local `20261126-07` and `20261126-06` audit-host follow-up | Rows (g) inventory delivered. Repeat-list and monitor await `R1-G5-SHARED-REPEAT`. Additional audit hosts remain parked on reviewed placement and launch binding. [Rows (g) report](20261127-07-rows-g.md) |
| Batch `compute/20261128-03` | TOpAS `c03-001-175` had `Start=false` and no startable ETP L40S was advertised. Prior engineering job `760158.0` has left the queue. There is no replacement submission. Check eligibility and the ledger. |
| P.4 and Paper C | P.4 phase 1 and A5 await the author's E0 criterion. Paper C CPU measurements await operator pins and authorization. E-INT `compute/20261127-28` awaits a bound census spec, staged inputs, matching Ada lease and engineering smoke. |
| Offline gate | G.5, downstream bindings, proof checks, arms freeze and explicit release remain prerequisites. |
