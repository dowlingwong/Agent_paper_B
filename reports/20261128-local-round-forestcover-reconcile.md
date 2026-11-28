# Local round close — Forest Cover handoff reconciliation

for: compute

Published base `7cd65cfa37cc1ece18d773b662a3f9b8c45917ce`, queue
`52fb689281a135032455bca3d73198759d52c1d0`, incoming Local `63ee5931`, Compute `b4d2a588`,
Writer `bc3326e0`.

`local/20261128-14` is at a STOP on the Forest Cover host receipt. The latest Compute round report
lists the Local handoff as pending. The handoff is already on `coord/local` at `f9193360`.
For the existing `compute/20261128-20` card, the exact Forest Cover harness branch is
`local-20261128-14-g5-gc7rc_forestcover` at `3f7b09febf401a83f3aa881f00eecdd032024416`.
Tier-E review **ACCEPTED** the engineering isolation candidate. The full suite returned identical
159 failure/error IDs at base and tip. Review SHA-256
`4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`. Failure/error IDs SHA-256
`3dc18712e00890e9003c6f9bf934caf6b20238dbec83e36aa779fa53d2a5eeea`.
[Original handoff and exact test counts](20261128-14-g5-forestcover-isolation-handoff.md)

Compute reconciles its ledger and live leases with the prepared worktree and run root, then completes
C1–7 on TASL-2 CPUs 4–7 in `torch312` at that pin if the check is still outstanding. This refers to
the existing card. No Forest Cover host-check or campaign job ID is published. Local resumes when
the exact C1–7 PASS, full harness SHA, receipt SHA-256 and independent review are on `main`, then
binds and reviews the unsigned addendum. `local/20261128-15` follows approved publication.

| Lane | Next check |
|---|---|
| Houseprice `local/20261126-01`, `local/20261127-27` | Closed. `tasl2-cpuset-mlgym_houseprice-20261128` passed the signed three-attempt check on TASL-2, checkout `paperB_cpuset_20261128T001400Z`. [PASS receipt](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-04-houseprice-cpuset-pass.md) |
| Primary G.5 and the three published addenda | Await the author's launch-base decision and coordinator publication or signing disposition. Candidate tips `2178bc6e`, `88edb84f`, `4ee43037`, `e9441f03`. No campaign job IDs are recorded. [Launch-base record](20261128-15-g5-etth1-clean-launch-base.md) |
| P.4 `local/20261128-13` | P5 timing PASS. P3 requires the project signature over `befb58c8`'s exact bytes on `0b465954`. No phase-1 job ID. [P.4 STOP](20261128-13-p4-timing-carry-forward-stop.md) |
| D.3a and batch | Exact P7 runs `d3a-p7-exact-20261128-c` and `-d` are closed. Production awaits the manifest, image or environment binding, endpoint-to-card proof, unused run ID, final review and P9. Batch `760158.0` left the queue. ETP L40S and TOpAS A100 last advertised `Start=false`. |
| Other pending cards | Shared-repeat and additional G.5 audit hosts await recorded dispositions. Paper C CPU work needs operator pins and authorization. E-INT needs the bound spec and lease. Writer and gate depend on released results and their respective review and release steps. |

Local is idle. The latest Compute sample at 15:00 UTC recorded no active Paper B job on TASL-2 or
in HTCondor. TASL-7 and Ada were sampled in the preceding round. Held IDs `5045947.0`, `5045949.0`
and `5045952.0` are Paper A. [Compute round](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

Decided alone to reconcile the existing handoff on the report branch. All 16 pre-existing project
changes in the assigned checkout match the historical published tree `1afa7d62` byte for byte and
were preserved. The assigned linked Git directory denied the fetch write, so the fetch and report
used the existing writable nested checkout in the assigned workspace. This round changed only this
report. Local submitted zero jobs and opened zero sealed partitions.
