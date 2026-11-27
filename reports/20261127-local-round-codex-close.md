# Paper B local round close — 27 Nov 2026

Queue checked at `coord/coordinator` `9a080990`, published main `30f9b0ce` and `coord/compute` `8233620e`.
Local is idle after the final queue fetch. No local card is runnable. No cluster job was submitted in this round. Host and scheduler states below are from the latest published Compute receipts.

| Task | Delivery | Next |
|---|---|---|
| `local/20261127-12` | Screening signature packet `mac-screen-note-for-signature-20261127` @ `b2360a7a54591aee99b8811fa9db7aa039ffacdd`, independently ACCEPTED. Draft check PASS and exact code pin 82/82 focused tests. | Author signature and coordinator publication. Then Compute runs the strict preflight and measurement. |
| `local/20261127-13` | D.3 G2 binding `mac-d3-r4-g2-binding-20261127` @ `47e0efc69755fc81f441f91de995f0dcbc49f476`, independently ACCEPTED. Artifact check passed and coordinator merged it at `30f9b0ce`. | Keep rev 4 unfrozen until its remaining prerequisites. |
| `local/20261127-11` | Ada venv launcher `mac-p4-ada-venv-20261127` @ `4a77a45ba0740d0d2ce7285b9bc6890ccb1d0248`, independently ACCEPTED with 204/204 torch-file tests. See the individual report for the full suite comparison and freeze hashes. | Coordinator publication, then the `for: compute` host fill and synthetic probe handoff. |
| `local/20261126-01` | Houseprice fix previously merged at `47df6f55`. Independent acceptance and the exact `for: compute` rerun command are in `reports/20261126-01-cpuset-fix.md`. | `compute/20261127-15` reruns after MetaMaze and Forest Cover seal and release both CPU-set leases. The last waiter timed out before any run root was created. |

## Compute and blocked local work

- Expansion G.1b run `g1b-x-tasl-20261126-a` on TASL-2. ETTh1 was sealed. MetaMaze PID `106579` on CPUs 0–3, Forest Cover `106573` on 4–7 and Titanic `106578` on 12–15 were last reported running. Check their seals, assembly and per-node determinism under `compute/20261126-10`.
- HTCondor P.4 H200 job `760065` was last reported Idle. D.3 preflight jobs `760148`, `760149` and `760152` were removed after sampling and no matching slot started. `compute/20261127-12` checks the next eligible L40S or TOpAS A100 slot. P.4 Ada follows its own host-config, lease and synthetic probe path.
- `local/20261126-08` G.5 final render awaits combined P11, final `paper.commit`, draft and strict checks and independent final review. `local/20261126-12` has a reviewed template and signed S9 choice. The switch and real node addenda await the shared final launch-code binding, exact published per-node G.1b PASS records and the applicable published split amendment. Keep the 1GC output separate. The parked audit-host extension and shared-card repeat monitor await their recorded decisions.
- `local/20261127-08` rev 4 awaits the pinned SMAC3 environment after the G1 adapter at harness `9bb41680` and G6, the exact gate-report path and per-node key, and the screening disposition before full step-(5) review and freeze. HPO-REF also waits for its reviewed interfaces and per-attempt output directories. The per-arm smoke waits for runner and release prerequisites.
- Paper C consolidation awaits author confirmation of its historical PLAN rows. G.5 labels, train/dev release, arms freeze and the single gate read continue in the signed order.
