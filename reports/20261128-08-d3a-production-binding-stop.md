# local/20261128-08 — D.3a production binding STOP

for: coordinator

- **Task and base.** `local/20261128-08`, updated by `local/20261128-12`. Published base `c3a484055f717865e4e6826833e405af41771013`, queue `b3d229b94174907aefc2ed08e5db9c87afe033ea`. The accepted Local revision 5 binding is `local-20261128-12-d3-step8-rev5` @ `b7cab83a45125296682315c20dc97030de7e1d0f`, merged at `d5d83198`.
- **Receipt.** Compute `20261128-22` delivered the manifest, endpoint-to-lease capture, resource basis, 49-chunk matrix and engineering checks on `compute-d3a-production-route-20261128` @ `6120d0e7b5f26d2cb8a844cb7c557aacd92c9f9d`. The independent tier-E review is **ACCEPTED WITH MINORS** for the engineering record at `e814b1ab1d9f3c8da42da5ad47cf80101849277f`. Run ID `d3a-prod-20261128-a` is allocated and marked unused. No production job ID is recorded. [Compute handoff](https://github.com/dowlingwong/Agent_paper_B/blob/d76e71cd/reports/20261128-41-d3a-production-route.md) · [Independent review](https://github.com/dowlingwong/Agent_paper_B/blob/e814b1ab/docs/r1/reviews/D3A_PRODUCTION_ROUTE_REVIEW_20261128.md)
- **STOP.** Frozen rev 5 §2 binds the v1 image with Python 3.13.18, and §7.2 records the comparison with deepthought's Python 3.13.15 audit. The TASL-2 direct route uses host Python 3.11.17 with the accepted P7 package versions. Compute found no accessible container runtime on that route. P7 remains **PASS** at 50/276 (18.12%) against 18.53%. A Level 2 author decision is needed to bind the direct environment. The production template also needs the per-chunk checks below before Local can bind the launch.
- **Tests.** Local verified the two Compute SHA-256 manifests (38/38 and 29/29), the unused ledger entry, and the six pinned files listed below for the declaration, note and checks. On a snapshot of `c3a48405`, P10 passed for 160 seeds (20010–20801) and the P11 synthetic analysis suite passed 53 tests. The first test snapshot omitted `sweep2/` and produced one import error. The full selected source snapshot passed all 53. Compute's independent base re-check additionally recorded 97 focused passes. The final-launch P10/P11 remain pending. This report-only follow-up changes no project code. The preceding tier-E Local unit's full suite matched all 190 failure and error IDs across base and tip. [Previous independent review and full-suite comparison](20261128-12-d3-step8-rev5.md)
- **Next.** Coordinator routes the author decision and the template findings. After the approved route and reviewed launch artifact exist, Local binds the exact `paper_commit` and checks that the allocated run ID remains unused. Local then runs P10/P11 at that SHA and obtains independent tier-E review before P9. The author signs P9 and the coordinator publishes. Compute checks the published bytes, run ledger and leases before starting any campaign.

## Route decision and production checks

Recommend an explicit PLAN §10 row allowing the TASL-2 direct Python 3.11.17 route with the
recorded executable and audit-shim digests. The four package versions match the frozen audit
basis, and the accepted exact-runtime P7 used this environment. The row should specify the
change to the campaign/audit comparison in §7.2 and bind the direct route in the D.3a note.
The alternative is an eligible host with the pinned v1 image and a reviewed matched RTX 4090
layout, with the corresponding route checks. No ready v1 route is recorded.

The engineering capture proves the endpoint, process, GPU UUID and canonical lease on one
seven-second start. The template's campaign path was outside the engineering review's execution
scope. A Local shell check with all host commands replaced by stubs reached the chunk stub when
the template's server failed to bind and a separate responder returned success for `/props`.
The same trace showed the chunk scope receiving no CPU affinity argument. The probe and server
both use `taskset -c 16-31`. Before the final launch binding, route the production command for a
fail-closed check of the live listener PID, bound GPU UUID and held leases, and confirm actual
chunk and worker CPU affinity to 16–31 inside the scope. Include a refusal case for a responder
owned by a different PID. The simulation ran no real server, probe or chunk.

| Binding | SHA-256 |
|---|---|
| Frozen rev 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Unsigned D.3a note | `afdc44f9b257ae8971436b2b5061eaffdde5ad73cdf8263bd7702e8fdb3d9cb9` |
| P10 verify-seed checker | `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2` |
| P11 analysis | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| P11 analysis tests | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |
| G2 constants | `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93` |
| Compute record / capture manifests | `9007304fe54bdd25d6a1dc5d5fd1db5febe176218683d9867e64210c6ba7c6ff` / `6690c5f2a3db6e462da109ae71b01c26d8d4c396e7ddc360057dc03f5365ebf9` |
| Campaign manifest | `426705844e6dc35f1a8f16f17a1098df6e384db792014fd0e3e0b516b8eb4fa3` |
| Run ID ledger | `62becc147a2b321cd5c1b082ac451bedd0941662bff93d3cfb06374639cd9d38` |
| Driver template examined | `bd027076cf71f205c059df481b1d0e4f0e0712cdb0a9b762880edf4c726cc7a5` |
| Python 3.11.17 executable / audit shim tree | `ff9b2ac4362b81c68622ffb1730f7138eb269177d9846399c521a44c5daffb0e` / `1737028cdd5868c30d331e6f80133e5ec3b1c76f3d4f95df9de960d67370ef07` |
| Independent Compute engineering review | `1eaf1ee414298839591f4c95af32669afec9d5fb83c2125b6ea1886847f5e70b` |

## Round close

Local has no other runnable card. Compute last recorded zero Paper B jobs on TASL-2, TASL-7
and deepthought/ETP at 19:27–19:29 UTC. Ada's last reachable sample was 18:49 UTC. The exact
P7 runs `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d` are closed. The production
endpoint probe (PID 1673663) ended and released its leases. Writer is idle pending released
evidence and a results card. Publication decisions are with the coordinator.

| Lane | Next check |
|---|---|
| G.5 primary and addenda 1–4 | Author launch-base decision and coordinator disposition for `2178bc6e`, `88edb84f`, `4ee43037`, `e9441f03`, `f96069d0`. Compute `20261128-18` then checks the intended exact checkout, attempt ledger and leases. No G.5 campaign job ID recorded. |
| Houseprice S14 | Closed. `tasl2-cpuset-mlgym_houseprice-20261128` ran in `paperB_cpuset_20261128T001400Z`. All three sealed attempts on CPUs 0–7 were bit-identical to the reference and within 9.486 s. The earlier tier-E fix had zero new suite failures and its exact `for: compute` command was used. [Command and test comparison](20261127-27-houseprice-two-attempts.md#compute-handoff) · [Published PASS record](https://github.com/dowlingwong/Agent_paper_B/blob/c3a48405/docs/r1/reports/g5_cpuset_20261128/G5_TASL2_CPUSET_CHECK_20261128.md) |
| P.4 phase 1 | P5 timing PASS. `local/20261128-13` waits for the author's P3 project signature on the spec bytes at `befb58c8` on parent `0b465954`. No training job is recorded. |
| Batch D.3 and D.3b | `760158.0` left the queue. Compute `20261128-21` checks the exact scheduler request at or after 21:16:04 UTC. The batch route also needs a reviewed image binding. D.3b awaits frozen arms and its own authorization. |
| Other cards | `local/20261126-07` inventory delivered. The G.5 repeat and monitor await `R1-G5-SHARED-REPEAT`; additional audit hosts remain parked pending reviewed placement and launch binding. HPO-REF is published at `c025ee24`. Paper C CPU desk units await operator pins and authorization. E-INT awaits its signed spec and matching lease. The offline gate still follows the G.5 label, release and arms-freeze prerequisites. |

Decided alone to reproduce the template findings with stubs and report the launch hold. The
assigned worktree's linked Git metadata denies writes to `FETCH_HEAD`. The report used the
existing writable nested checkout within the assigned workspace. All 16 pre-existing changed
project paths matched published `1afa7d62` blobs. Local submitted zero jobs and opened zero sealed
partitions.
