# local/20261128-14 — two G.5 addenda filled and accepted, review publication STOP

for: coordinator

- Paper base `9b044b59f58109b3d1e4eb1822623160958b1d95`, queue `d47cab43`. The published exact-pin TASL-2
  isolation records and reviews bind Titanic and MetaMaze. The two unsigned notes use the published primary
  note and spec, G.1b determinism receipts, reviewed expansion D6 copy, PRE-SPLIT v2 and signed P10 laws.
- Fresh independent tier-E **ACCEPTED** for the two exact specs and unsigned drafts. Review-only branch
  `local-20261128-14-g5-titanic-metamaze-launch-review` @ `c7788764718219b19135dcb2365d4355535dc945`,
  review SHA-256 `de343ac4e6d10d29b2f7a8c3d1493e1a2f5bb3916008a35ca1d398bc9ba3a9cb`.
- The actual binder and validator passed both engineering checks with only review publication simulated.
  The official `check-note --draft` on both committed unsigned drafts returns exit 2 because the exact review
  file is absent from published main. The base note, spec/host digests, and each spec-only code-tree diff passed.
  The harness full-suite comparisons found zero new IDs for each node. [Titanic](20261128-14-g5-titanic-isolation-handoff.md) · [MetaMaze](20261128-14-g5-metamaze-isolation-handoff.md)

| Node / run | Branch and tip | Spec commit and SHA-256 | Unsigned note SHA-256 |
|---|---|---|---|
| Titanic, `c3_t1_labels_20261128_addendum_1` | `local-20261128-14-g5-addendum-titanic` @ `6e2333e930b1cf5a3139d132bf81e61aefb9fc51` | `6257fa376f7c325047e2511cb466086431d1b250`, `2b68a4f40212acbc30a84867486e07ae6485efd4134a4cb778392f2e9f50ad5b` | `381d3899c7b4ede1b7a2cdb207cc2b70cf07b887f667ca7df58e82f4e58d5d32` |
| MetaMaze, `c3_t1_labels_20261128_addendum_2` | `local-20261128-14-g5-addendum-metamaze` @ `9798799c973ec4dca107bf45fbd2882a97b6d921` | `2963d276436cbeda1025826b52c8de68a6b14d0d`, `4112e44995dedf1136d1c926c57c9d9bd052a07be339cd0d93a134e070d0f85d` | `17d91d30e205ab0c2cdd0126e1d9434e1d1150d456e0d0e497882086a880c7e3` |

The exact host checks have SHA-256 `3d76372dc02ccfe01dfccb15f4c9180fbf59c2d33fa035d5a66faee9d3ece1f2`
(Titanic) and `80581d24da323dd9a9ef212585bfe3908165b72f583bd6f40e09b9bf6f1231c0` (MetaMaze).

Next: publish **only the review branch** so Local can run the official draft command on each unchanged tip.
The spec-only commits are unsigned desk candidates. The local SOUL describes SSH-signed launch commits and
Compute reports no configured project identity. For signed publication, keep the reviewed spec bytes and exact
parent, publish each approved note on its own spec's lineage, and preserve the separate launch tips with
merge commits. A checkout carrying both specs fails the one-spec launch-tree binding. Before any job,
Compute confirms the two run IDs are unused in its live ledger and checks current leases. The last published
ledger shows no primary or expansion G.5 campaign submission.

Decided alone to assign suffixes 1 and 2, which are unused on published main and absent from the published
job ledger, and to project CPU worker-slot and TASL-7 proposer hours separately with the existing G.5 formula.
No host submission or sealed evidence access occurred.
