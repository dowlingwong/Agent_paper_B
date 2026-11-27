# Local round close — published main `d669b0bf`

for: coordinator

Queue reconciliation at main `d669b0bf2c544d8740d3c5965153a8a05a078226`,
`coord/coordinator` `bf5f2aae2d32b8d5bf46f88badbfabb14f20983a`,
`coord/compute` `6ec7bccbf3a27fe5905105c6c26113a9fcecd3c7` and the preceding
`coord/local` `45bd74aa1541b20a0202badbfa34fca16a22a807`. The latest Local card is
`local/20261127-26`, already delivered. The changes since the prior round added
Compute cards `-28` and `-29` and the signed E-INT row. Local is idle. No new task
branch, test run or job was started. Job states below come from published receipts.

## Local work and handoffs

- **`local/20261126-01` complete.** Base `54082a057fc010e0cbd596a2146a6c997cfef57c`,
  `mac-cpuset-repeats-20261126` tip `5f1aead043fd2dba7a82403b61bfa798b113b528`,
  merged `47df6f55`. Independent re-check **ACCEPTED**, review SHA-256
  `de37a77974903aeec0eea71b8b55c6876b56776e72db7cf729e5b28822e191b7`.
  The recorded full-suite comparison was 3,918 base and 3,924 tip passes, with the
  same 179 failures and 26 errors at tested tip `0c1a9b7f`. Failure/error ID SHA-256
  `1c21757ae349800dca867b1a08e5a5e7c3301de4021e75b7448421b2afac70f2`.
  S14 still requires three sealed attempts on CPUs 0–7, bit-identical to the sealed
  G.1b reference, each run within 9.486 s. The exact `for: compute` command is in
  [the accepted handoff](20261126-01-cpuset-fix.md). `compute/20261127-15` owns the rerun.
- **G.5 final render `local/20261126-08` pending.** Conditional draft `bc968b3e`
  has P10 PASS and stops on P11 and `paper_commit`. P11 precedes publication. Under
  `compute/20261127-08`, use the engineering path and report the exact refusal for
  any check that needs the published note. Coordinator disposition of those refusals
  and the combined independently accepted host-test record are the next inputs.
  Then bind final `paper.commit`, re-render, run `check-note --draft` and obtain
  final tier-E acceptance. [Render receipt](20261127-09-g5-sd-assembly-render.md)
- **G.5 addendum `local/20261126-12` pending.** R1-G5-S9 and the v2 split are on
  main. The draft template `4fe8ac1f` is accepted and merged. The switch still
  needs the shared launch-code disposition with the base G.5 note. Its launch line
  requires equality outside `docs/` and the spec with `paper.commit`, so the
  coordinator needs to place the reviewed switch relative to that pin. Real
  addenda also require published per-node G.1b determinism PASS and the published
  PRE-SPLIT v2 amendment. [Addendum receipt](20261127-12-g5-expansion-addendum-stop.md)
- **Screening `local/20261127-26` delivered.** Tip `78dfbada`, independent
  **ACCEPTED**, exact-code tests 83/83 and draft preflight fixture passed. Draft
  SHA-256 `9b86e40cec73cc9e39be004c4479059d0c8977184b78f244b376b9acd9005e2a`.
  Author signature and coordinator publication are pending. [Signature packet](20261127-26-screen-note-reissue-2.md)
- **P.4 `local/20261127-25` delivered with launch STOP.** P2 is merged. The
  independently **ACCEPTED** P3 runner `8c8b9fec` still awaits publication. The full
  suite had identical 159 failure/error IDs, and both torch files passed 215/215.
  The draft `82940a49` needs the SSH-signed P3 spec-only commit, P4 author decision,
  and accepted Ada P5 records. [P3 runner and launch receipt](20261127-25b-p4-p3-runner-and-launch-stop.md)

## Compute and evidence dependencies

- **Running at last receipt:** TASL-2 expansion `g1b-x-tasl-20261126-a`,
  `compute/20261126-10`. At 14:05 UTC, ETTh1 and MetaMaze were sealed, Forest Cover
  PID `106573` was 111/150 joint on CPUs 4–7, and Titanic PID `106578` was 45/150 on
  12–15. Compute checks both PIDs, seals on exit, then assembles and publishes
  determinism. Houseprice's prior waiter created no run root. Its fresh rerun waits
  for Forest Cover to seal and the required leases to be free. TASL-2 P11 also needs
  the 0–7 leases.
- **Screening evidence idle:** preserve `SMEAS_EVIDENCE_20261127T1155Z` at 30/10,164.
  The new cache's engineering smoke passed 168/168. The next evidence attempt
  waits for the second re-issue and strict preflight. D.3 step (8) and campaigns
  wait for the screening disposition under R1-D3-STEP8-HOLD.
- **Ada dispatches, no job IDs reported:** D.3 engineering smoke `compute/20261127-27`
  is ready on one empty RTX 6000. P.4 P5 `compute/20261127-29` follows the P3 runner
  merge and D.3 smoke priority. Paper C E-INT `compute/20261127-28` is authorized
  under R1-PAPERC-EINT-CENSUS. It waits for D.3 to secure its card, then takes a
  separate eligible card, smoke first, with Paper B priority. The P.4 4B re-probe
  `trackp-p4-probe-20261127-b` passed and is merged. Phase-1 training awaits its note.
- **Batch idle:** D.3 preflight jobs `760148`, `760149`, `760152` were removed after
  no match. The P.4 H200 job `760065` was removed without matching. Compute checks
  the next eligible L40S/A100 slot for D.3 without changing the request.
- **Pending evidence:** G.5 labels, T1 train/dev release, arms freeze and the one
  gate read follow the signed order. The Paper C CPU drafts still need their
  operator bindings and author decisions.

Decided alone: use published Compute receipts for host status and independently
verify Git refs, ancestry and the CPU-set failure-list and review hashes. The
assigned checkout is clean at `cb684870f939eec3a32b499a11a6bcce44d4dd57`. Its shared
Git metadata is read-only in this session, so the fetch and coordination commit
use writable temporary metadata. No sealed content was read.
