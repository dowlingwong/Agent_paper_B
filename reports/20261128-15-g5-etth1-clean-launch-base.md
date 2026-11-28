# local/20261128-15 — ETTh1 clean launch base and Local round close

for: coordinator

- **Desk delivery ACCEPTED.** Branch `local-20261128-15-g5-launch-base-etth1` at
  `e9441f03128bf6ed7291b854e70773f4c1dd5fba` starts from reviewed draft
  `5e924f81f41beb34dc5ad30ccceedf35620ca474`. Published base
  `7cd65cfa37cc1ece18d773b662a3f9b8c45917ce`, paper pin
  `2a58f7ac5147dad1259914593901ccb226a147f9`, run `c3_t1_labels_20261128_addendum_3`.
- The candidate's two changed paths copy the approved note verbatim and add a launch-base record.
  Note and spec match published main byte for byte. The tree equals the paper pin outside `docs/`
  and its own spec. `git diff --check`, strict `check-note` at K = 10 and `validate --launch` PASS.
  This is a documentation-only change. The checks cover its exact launch binding and content.
- Actual `verify_launch_tasl` at the candidate returns the expected publication ancestry STOP.
  The validator and import-source checks PASS with only the main ref and PLAN read pointed at the
  local two-parent merge `35e99b40eb5add6d9ad1c585a0b13fd053f33be2`. That merge adds only the
  launch-base record relative to published main. The unmodified verifier also PASSes at published
  `7cd65cfa` itself, where the paper pin already contains the two earlier sibling specs.
- Fresh independent tier-E review **ACCEPTED for desk delivery**. Review branch
  `local-20261128-15-g5-etth1-launch-base-review` at `0312b5832f55fb6c808705fcf611e364f5b1a54b`.
  [Independent review](https://github.com/dowlingwong/Agent_paper_B/blob/0312b5832f55fb6c808705fcf611e364f5b1a54b/docs/r1/reviews/G5_EXPANSION_ETTH1_LAUNCH_BASE_REVIEW_20261128.md)
- **Launch STOP.** Both candidate and published tip are unsigned. Local SOUL line 22 and PLAN §10
  `R1-G1B-TASL-DECISIONS` LB A are the signing sources. The primary G.5 note invokes LB A on line 54.
  The runtime guard checks ancestry and tree content. After the author and coordinator resolve the
  G.5 launch-base decision, the coordinator selects the exact ETTh1 checkout and records the signing
  disposition. Compute fetches, rechecks actual ancestry and strict note, then checks the run ledger
  and live TASL leases before any submission. ETTh1's licence line is due before a label table cites it.

| Object | SHA-256 |
|---|---|
| Approved ETTh1 note | `903eb07a42affdd6f660847388ef3b318da3b50e62d0aed4a4ce8cfe05e1093b` |
| ETTh1 spec | `6c3323cae31c1f4e9433412143538dc3045323364f7b29b8d77c003464592758` |
| Launch-base record | `9b1987b597311c2413c16360b8f9bb98a8e5c4d220127c84ea989d1e55d43043` |
| Independent review | `aee35f1a174b11ab8895b2cf50634bf5bb0a905df420c27d5ed28389a19e7bfb` |

The prior ETTh1 draft publication STOP cleared at `7cd65cfa`. The coordinator can use the already
published ETTh1 checkout for the ancestry and tree conditions if its launch and signing disposition
permits it. The new per-node candidate satisfies the requested clean-base delivery with its own record.

## Round state

After pushing delivery and review, Local fetched main `7cd65cfa`, queue
`52fb689281a135032455bca3d73198759d52c1d0`, Compute `b4d2a588` and Writer `94150eb0`.
Local is idle. The next runnable unit requires a new receipt, author decision or assignment.

| Lane | State and next check |
|---|---|
| Forest Cover `local/20261128-14` and `-15` | Compute `20261128-20` still owes the published C1–7 receipt at exact harness `3f7b09febf401a83f3aa881f00eecdd032024416`, TASL-2 CPUs 4–7 and `torch312`. Then complete the addendum review, wait for its approval and prepare its clean launch base. No host-check or campaign job ID is recorded. |
| Primary G.5 and MLGym addenda | `c3_t1_labels_20261128` and `_addendum_1` and `_addendum_2` await the launch-base decision and coordinator publication. Exact candidate tips `2178bc6e`, `88edb84f`, `4ee43037`. No campaign job IDs are recorded. |
| G.5 shared-repeat and additional audit hosts | Shared-repeat implementation awaits the `R1-G5-SHARED-REPEAT` disposition. The extra audit-host path stays parked pending its binding and authorization. |
| Houseprice | Closed. Compute `20261127-33` item 1 passed with three bit-identical attempts on CPUs 0–7 within 9.486 s. Run `tasl2-cpuset-mlgym_houseprice-20261128`, checkout `paperB_cpuset_20261128T001400Z`. Accepted report and seal went to main. [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-04-houseprice-cpuset-pass.md) |
| P.4 phase 1, `local/20261128-13` | `trackp-p4-p1-20261122-a`, P5 timing PASS. P3 awaits the project signature on the reviewed one-file spec bytes `befb58c8` on parent `0b465954`. Local fills P3 and obtains the final review after the signature. No training job ID is recorded. |
| D.3 | Exact engineering runs `d3a-p7-exact-20261128-c` and `-d` closed. D.3a production awaits the manifest and environment or image binding, endpoint-to-card proof, a fresh run ID, review and P9. Prior HTCondor batch `760158.0` is gone. Last exact ETP L40S and TOpAS A100 samples both had `Start=false`. Compute rechecks matching and the next job ID. |
| Paper C, Writer and gate | Paper C CPU work awaits runtime, cache and authorization bindings. E-INT awaits its signed census spec and Ada lease. Writer awaits released results. The gate awaits G.5, train/dev release, proof and consumer checks, arms freeze and explicit test release. |

Compute's last direct sample at 15:00 UTC showed TASL-2 idle and zero Paper B jobs queued or running in
HTCondor. TASL-7 and Ada were last sampled in the preceding round. The held Condor IDs `5045947.0`,
`5045949.0` and `5045952.0` belong to Paper A. [Compute round](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

Decided alone to use the existing writable nested Git checkout after the assigned linked checkout
could not write `FETCH_HEAD`, and to keep the independent review on its own branch so the candidate
retains its two-path diff. Existing project edits in the assigned checkout were preserved. Local
submitted zero jobs and accessed zero sealed partitions.
