# Local round close — screening fix and Ada phase-1 STOP

for: coordinator

At the post-task fetch, published main was `85b2421f95b53de3d5405504e7a217733fa4afa0`, the coordinator queue was
`dcca5b56587955eaf501cb664172e03edabe0047`, and Compute's latest receipt branch was `bf57e012ca81792f773f5e602bba90c594afb5d0`. No ready
`tasks/local` card or new direct handoff remained. Local is idle. The assigned
worktree's original checkout is clean at `cb684870f939eec3a32b499a11a6bcce44d4dd57`.
Task checkouts were created under its ignored scratch path with writable temporary Git metadata.

- **`local/20261127-23`** — screening cache fix delivered at
  `e9d7f230016ee32a1a338e83af4c01dfd467aeb2`, exact code `c12136d6`, tier-E **ACCEPTED**.
  83 focused tests passed and the full-suite comparison shows zero new failing/error IDs.
  Compute's fresh rebuild and seed-999 smoke wait for coordinator publication, then the second
  evidence-note re-issue requires the author's signature.
  [Exact handoff](20261127-23-screen-cache-layout.md).
- **`local/20261127-24`** — Ada-only phase-1 draft delivered at
  `68ed7514609d4d88f4b52b5ddb59a515a2d8dac5`, tier-E **ACCEPTED for the blocked desk handoff**.
  The draft remains unsigned. P2, P3, P4 and P5 require the published Kev eligibility disposition,
  runner corrections and pins, the author tick and class choice, and Ada staged smoke/E0 with
  a timing disposition. [Draft and STOP report](20261127-24-p4-phase1-ada-note-stop.md).
- **`local/20261126-01`** — already accepted, full suite compared and fix merged `47df6f55`.
  S14 still requires three sealed attempts on TASL-2 CPUs 0–7, each bit-identical to the sealed
  G.1b reference and within 9.486 s. [Exact Compute rerun](20261126-01-cpuset-fix.md).

| Lane | Latest recorded state and next dependency |
|---|---|
| Expansion G.1b `compute/20261126-10` | Running elsewhere in the 13:20 UTC receipt, run `g1b-x-tasl-20261126-a`. TASL-2 Forest Cover PID `106573` on CPUs 4–7 (88/150 joint) and Titanic PID `106578` on 12–15 (26/150 joint). ETTh1 and MetaMaze are sealed. Check those two exits, seals and assembly, then publish the per-node determinism verdicts. |
| Houseprice and P11 | Houseprice `compute/20261127-15` has no run root after the waiter exited. Compute checks PID `106573` and leases 0–3/4–7 before a fresh capture rerun. Remaining P11 C2/C4/C5/C6/C9/C14/C15 need a valid signed note or a routed synthetic smoke spec. The checked draft refuses at `run_id`. C10 hours and C11 audit-chunk side await an eligible TASL-7 card (`compute/20261127-05/-08`). |
| G.5 | The final render waits for combined P11, exact `paper.commit`, draft check and tier-E review. S9 addendum code waits for the shared launch-code binding. Per-node addenda need released split binding and published G.1b determinism PASS. Shared-card repeats and extra audit hosts stay pending on their recorded decisions. |
| Screening | The attempt `SMEAS_EVIDENCE_20261127T1155Z` remains STOPped at 30/10,164. The next step is the reviewed engineering handoff above. |
| D.3 | HTCondor preflight `compute/20261127-12` is idle without an eligible GPU in the latest receipt. Jobs `760148`, `760149`, `760152` were removed. Check the reviewed request for an L40S/TOpAS A100 match. Revision 4 step (8) and per-arm smoke remain held on screening disposition and dispatch. |
| P.4 | The 4B re-probe `trackp-p4-probe-20261127-b` passed and is merged at `85b2421f`. Prior H200 job `760065` was removed with zero wall time. Phase 1 is pending the draft's pre-signature requirements. |
| Paper C | CPU drafts and E-INT desk preparation are merged. The CPU lanes need author decisions and operator pins. E-INT needs the signed development smoke and an eligible GPU after Paper B's critical work. |

Decided alone: worked on the independent Ada desk card while the screening suite ran. Compute job
states are from committed receipts. Local did not submit any jobs or open any sealed partition.
