# Local round close — P.4 P2/P3 and second screening re-issue

for: coordinator

Post-task fetch found published main `523ccfbc982c3c2c80b5fa0120ca114a6b13a56e`,
`coord/coordinator` `1bd386f957ed4917274132b5e9401db5615b307a`, and the latest Compute receipt
`6ec7bccbf3a27fe5905105c6c26113a9fcecd3c7`. The latest Local card is `local/20261127-26`.
There is no runnable Local card or new direct handoff. The Local lane is idle.

| Local task | Disposition |
|---|---|
| `local/20261127-25` P2 | **ACCEPTED** and coordinator-merged at `523ccfbc`. Both Kev bases are eligible, with E0 PASS and no recorded E4 hard-limit exclusion. [P2 record](20261127-25a-p4-p2-kev.md) |
| `local/20261127-25` P3 | Tier-E runner **ACCEPTED** at delivery tip `8c8b9fec`. Full suite adds two passes, with the same 159 failure/error IDs. Both torch files pass 215/215. The Ada-only branch `82940a49` is accepted as a draft. Launch waits for an authorized SSH-signed spec-only commit, the P4 author tick, and P5 Ada staged smoke/E0 with its timing disposition. [P3 runner and launch STOP](20261127-25b-p4-p3-runner-and-launch-stop.md) |
| `local/20261127-26` | Second screening re-issue draft **ACCEPTED** at delivery tip `78dfbada`. Exact-code tests 83/83 and the preflight fixture passed. Author signature and coordinator publication precede Compute's strict preflight and evidence run. [Screening handoff](20261127-26-screen-note-reissue-2.md) |
| `local/20261126-01` | Accepted CPU-set fix is already merged at `47df6f55`. The signed S14 criterion remains three sealed attempts on CPUs 0–7, bit-identical to the sealed G.1b reference and within 9.486 s per run. [Exact `for: compute` rerun](20261126-01-cpuset-fix.md) |

## Running elsewhere and next dependencies

- **Expansion G.1b** `compute/20261126-10`, run `g1b-x-tasl-20261126-a`. At 14:05 UTC ETTh1
  and MetaMaze were sealed. Forest Cover `106573` on CPUs 4–7 was 111/150 joint and Titanic
  `106578` on 12–15 was 45/150. Compute checks those processes on exit, seals each, then
  assembles and publishes determinism when all four are sealed.
- **Houseprice** `compute/20261127-15` waits for Forest Cover to release CPUs 4–7. MetaMaze
  released CPUs 0–3. The prior waiter created no run root. Recheck both leases before the
  fresh capture using the accepted handoff.
- **G.5 and P11** await the outstanding host-test prerequisites and final note. The TASL-2
  checks C2/C4/C5/C6/C9/C14/C15 need a valid signed note or a dispatched synthetic smoke
  spec. The longer C10 and C11 chunk route needs dispatch. TASL-7's card was free in the
  last sample. The final note still needs the combined P11 record, exact `paper.commit`,
  draft check and tier-E review. S9 is signed and v2 is on main. The addendum switch is
  pending the shared launch-code binding, and each node note needs its published
  determinism and split bindings. Shared-card repeats and extra audit hosts remain parked.
- **Screening** has no active evidence attempt in the latest receipt. The previous scene
  `SMEAS_EVIDENCE_20261127T1155Z` is preserved at 30/10,164. The 168/168 engineering smoke
  is accepted and published. The new evidence attempt waits for the second re-issue signature.
- **D.3** `compute/20261127-27` is dispatched for per-arm engineering smoke on one empty
  Ada RTX 6000, with no job ID reported. The separate HTCondor preflight is idle
  without a GPU match. Jobs `760148`, `760149`, `760152` were removed. Step (8) and the
  campaigns remain held on screening under R1-D3-STEP8-HOLD.
- **P.4** synthetic 4B re-probe `trackp-p4-probe-20261127-b` passed and was merged. The
  earlier H200 job `760065` was removed without matching. Phase 1 has no active job in
  the latest receipt and waits on the P3/P4/P5 conditions above.
- **Paper C** CPU drafts and E-INT desk preparation are merged. CPU work waits on author
  decisions and operator pins. E-INT waits on an authorized development smoke and an eligible GPU.

Decided alone: use the accepted Compute receipts for job states. The original assigned worktree
is clean at `cb684870f939eec3a32b499a11a6bcce44d4dd57`. Its shared Git metadata is read-only here.
Task checkouts used its ignored scratch path and writable temporary Git metadata. No job was submitted.
