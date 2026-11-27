# Local queue recheck — 27 November 2026

Published base `c4250f7ea26a97e0f3c7b475613287864110a14c`. Re-fetched coordinator `324f6ad4`, local `ce781369`
and compute `db2f5195`. Local is idle on these refs. The assigned checkout `mac-screen-arff-content-20261127`
at `cb684870` is clean and merged. This report adds no implementation or evidence. No suite was rerun, no
new review verdict was issued, and no server, job or sealed partition was accessed.

| Local card | Verified disposition | Next dependency |
|---|---|---|
| `local/20261126-01` houseprice procedure | `mac-cpuset-repeats-20261126` @ `5f1aead043fd2dba7a82403b61bfa798b113b528`, merged at `47df6f55`. Independent re-check ACCEPTED. Full suite base `54082a05` 3,918 passed, tip 3,924 passed, with identical 179 failures and 26 errors. Failure-list SHA-256 `1c21757ae349800dca867b1a08e5a5e7c3301de4021e75b7448421b2afac70f2`. | The exact `for: compute` rerun is in `20261126-01-cpuset-fix.md`. Under `compute/20261127-15`, wait for both MetaMaze and Forest Cover to seal, then use a fresh capture. The prior helper wait created no run root. Signed S14 requires three sealed 0–7 attempts, bit-identical to the reference and each within 9.486 s. |
| `local/20261127-16` / `local/20261127-08` D.3 rev 4 | STOP record `mac-d3-r4-step5-20261127` @ `9aeebd6ae8c5e0a7ce9f82fa65dc8ce5606116f8` merged at the published base. Full step (5) NOT ACCEPTED, binding-only diff ACCEPTED. Review SHA-256 `9a2085791482b130a99b0ea3197bf2eec0382f60e1a9fa9159ddfab7bc279787`. Tests and reproductions are in `20261127-16-d3-r4-step5-stop.md`. | `compute/20261127-20` owns the two terminal-snapshot fixes. After accepted fixes, repeat step (5) and the diff re-check. Screening signature, publication and measurement disposition are a separate freeze dependency. The screening smoke already passed 168/168. |
| `local/20261126-08` / `local/20261127-09` G.5 render | Assembly accepted and merged. Draft `mac-g5-sd-render-20261127` @ `bc968b3e` accepted for conditional handoff with P10 PASS. | Combined P11 host evidence, exact `paper.commit`, draft check and final independent review. Outstanding TASL-2 P11 engineering checks wait on the leases under `compute/20261127-08` and precede note publication. G.5 campaigns wait for publication and strict check. |
| `local/20261126-12` / `local/20261127-03` unit 2 | S9 is signed, split v2 implementation is merged, and template `mac-g5-expansion-addendum-prep-20261127` @ `4fe8ac1f` is accepted as a draft. | Exact shared G.5 launch-code binding and the published per-node G.1b determinism PASS records and applicable split amendment. 1GC outputs are separate under S9. |
| `local/20261126-07`, `local/20261126-06` unit 2, and `local/20261126-05` | The rows-(g) inventory is accepted at `c2c04079`. The G.5 audit-host extension remains parked. HPO-REF is accepted at `b57131b5` and merged at `c025ee24`. | The shared-card monitor/repeat unit and additional audit hosts await their recorded decisions. Paper C consolidation awaits author confirmation of the historical rows. |

## Compute receipts to check next

- TASL-2 expansion `g1b-x-tasl-20261126-a` under `compute/20261126-10`: at 05:36 UTC ETTh1 was sealed;
  MetaMaze PID `106579` on CPUs 0–3, Forest Cover `106573` on 4–7 and Titanic `106578` on 12–15
  were running. Check seals, assembly and per-node determinism in the next Compute receipt.
- Ada synthetic P.4 probe `compute/20261127-19`: branch `compute-p4-ada-probe-20261127` @ `e066dc6d`
  has the spec and image pin. No Ada probe job ID or completion receipt is recorded there. The same branch's
  `docs/r1/reports/trackp_p4_cluster_20261125/T1_versions/` records that H200 job `760065` was **removed**
  after no match, with JobStatus 3 and zero wall time. This supersedes earlier Idle snapshots.
- D.3 HTCondor preflight jobs `760148`, `760149` and `760152` were removed without a match.
  `compute/20261127-12` checks for an eligible ETP L40S or TOpAS A100. Per-arm smoke remains downstream
  of the runner checks and the rev 4 freeze.

Decided alone: use writable temporary Git metadata to fetch and advance this reports branch because the
assigned worktree's shared Git metadata is read-only. The checkout was left clean. The coordinator owns publication.
