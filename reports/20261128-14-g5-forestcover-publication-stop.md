# local/20261128-14 — Forest Cover host check passed, publication STOP

for: coordinator

Base `7cd65cfa37cc1ece18d773b662a3f9b8c45917ce`, queue `52fb689281a135032455bca3d73198759d52c1d0`,
Compute `dc7880b129d29d6a5806cefd9df33825f69f7a83`, Writer `49d905acd7448cf36c534845555406c3e053f121`.
This updates the [previous Local round](20261128-local-round-forestcover-reconcile.md).

- **Host check complete.** `compute/20261128-20` delivered C1–7 PASS on TASL-2, CPUs 4–7, `torch312`, exact
  harness `3f7b09febf401a83f3aa881f00eecdd032024416`. Receipt branch
  `compute-g5-expansion-isolation-forestcover-20261128` @ `3a334d528d4be799c049d3748b8fec4c8c01f58b`.
  Independent re-check **ACCEPTED WITH MINORS** (documentation) on
  `compute-g5-expansion-isolation-forestcover-20261128-review` @ `eb34c563e36f8f55058d49a0cc1a97edeb7e377a`.
  The passing capture is `20261128T173716Z`. [Compute handoff](https://github.com/dowlingwong/Agent_paper_B/blob/dc7880b1/reports/20261128-37-g5-forestcover-isolation.md)
- **Publication STOP.** Both tips are outside published `main`. The actual `g1b_tasl.check_host_record` in the
  clean paper-base snapshot refuses the missing published receipt. The same checker accepts its host, harness,
  verdict fields and hash with the delivered record as a desk fixture. The full addendum draft check and its
  tier-E review are pending. Local produced no new task branch tip or code change. The exact harness suite
  comparison remains 5,071 passed, 156 failed, 3 errors, 164 skipped and 71 subtests passed on each side.
  All 159 failure/error IDs match, SHA-256 `3dc18712e00890e9003c6f9bf934caf6b20238dbec83e36aa779fa53d2a5eeea`.
  [Harness tier-E acceptance and suite](20261128-14-g5-forestcover-isolation-handoff.md)
- **Next.** The coordinator publishes the host record and independent review. Local fetches the new main tip,
  binds the Forest Cover spec and unsigned addendum on a task branch, runs the draft check, and obtains the
  tier-E review. `local/20261128-15` follows approved publication. The host check has no scheduler ID.

| Verified blob | SHA-256 |
|---|---|
| Host receipt | `00b84d688d1b167bab1817709919fa7b8c8237ccaff3d60a1245e10a5c27eb12` |
| Capture `SHA256SUMS` | `95fb1af5f2d0aef4633a872cffde35dd9a5bea14796e930dadfe71096285e736` |
| Independent host review | `42702d3a8414bc6827a886474fff5182a6e4808a785f20bb3baf82d2210545cf` |

## Round close

No other Local card is runnable. Compute's latest round sampled TASL-2, TASL-7, Ada and HTCondor and reported
zero Paper B jobs running or queued. Held HTCondor jobs `5045947.0`, `5045949.0` and `5045952.0` belong to Paper A.
[Compute ledger](https://github.com/dowlingwong/Agent_paper_B/blob/dc7880b1/reports/20261128-38-round-status.md)

| Lane | Next check |
|---|---|
| Houseprice CPU-set `local/20261126-01` and `local/20261127-27` | Closed. Run `tasl2-cpuset-mlgym_houseprice-20261128`, checkout `paperB_cpuset_20261128T001400Z`, passed the signed three-attempt check. [Reviewed exact handoff](20261127-27-houseprice-two-attempts.md) · [PASS receipt](https://github.com/dowlingwong/Agent_paper_B/blob/dc7880b1/reports/20261128-04-houseprice-cpuset-pass.md) |
| Primary G.5 and the three published addenda | Check the author's launch-base decision and coordinator publication/signing disposition for `2178bc6e`, `88edb84f`, `4ee43037`, `e9441f03`. No campaign job IDs are recorded. [Launch-base checks](20261128-15-g5-etth1-clean-launch-base.md) |
| P.4 `local/20261128-13` | P5 timing PASS. P3 awaits the project signature over the exact spec bytes at `befb58c8` on `0b465954`. No phase-1 job ID. [P.4 STOP](20261128-13-p4-timing-carry-forward-stop.md) |
| D.3a and batch | Exact P7 runs `d3a-p7-exact-20261128-c` and `-d` are closed. Production awaits the manifest, environment/image binding, endpoint-to-card proof, fresh run ID, review and P9. Batch `760158.0` left the queue. On Compute recheck 5, ETP L40S and TOpAS A100 had `Start=false`. |
| Remaining cards | Shared-repeat and extra audit hosts await their recorded dispositions. Paper C CPU work awaits operator pins and authorization. E-INT awaits the signed census spec and a fitting lease. Writer and the gate await their evidence prerequisites. |

Decided alone to verify the received record with the existing checker in a clean snapshot. The assigned linked
Git directory denied `FETCH_HEAD` writes, so fetch and report used the existing writable nested repository.
All 16 pre-existing changed project files match historical published commit `1afa7d62` byte for byte and were
preserved. Local submitted zero jobs and opened zero sealed partitions.
