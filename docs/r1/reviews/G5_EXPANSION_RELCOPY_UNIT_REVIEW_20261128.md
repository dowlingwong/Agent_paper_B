# Independent tier-E review of the expansion D6 copy unit

Verdict: ACCEPTED
Code-Commit: 3584990916ac32a05394ee8e7c3cea9d0fecf594

Task `local/20261128-01`, base `15fe05b0d0a08ae5c37eb582eb0c3f04d67e0b2a`.
This review covers the `g5_relcopy.py` expansion variant, the `g5_tasl.py rel-copy` CLI
and the synthetic tests in `test_t1_g5_seal.py`.

Fresh Claude review session `2d2a3163-fad4-4d9b-bb84-d68393197425` withheld acceptance
at `ae956c56`. Finding B1 asked to exercise the checks using the actual published
summary and assembly, including the canonical and raw spec digests. The desk confirmed
all metadata predicates and drove the production source checker to the runs-read
boundary with published bytes and simulated host path stats. The patch also pins the
summary and assembly to the specific bytes accepted by the expansion result review.
Independent re-check `4190dadd-32d1-4937-a780-07e6f4702cad` accepted the final candidate,
the metadata check and the command routed to Compute. The independent reviews checked
the supplied code, diff and metadata.

| Published binding | SHA-256 |
|---|---|
| Accepted expansion summary | `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10` |
| Accepted assembly | `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077` |
| Runs SHA in assembly | `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7` |
| Signed G.1b spec file | `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238` |
| Canonical G.1b spec JSON | `0fc29a2e614d131131b7bc00fb2b2f6d0d31d68fd832c1658cf594b361aff894` |
| Published PRE-SPLIT v2 amendment | `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7` |

The two spec digests match their distinct fields in the accepted assembly. All four job
entries carry the signed spec's file digest. The expansion variant requires the exact
TASL-2 run and source path. It uses the existing D6 seed and paired-count checks.
The seven-node and autoresearch variants retain their source and authority routes.
An exclusive destination reservation protects an existing path during publication of
the checked copies. The review considered the case of an abruptly terminated process
leaving an empty reservation. Preserve that scene and report it before a retry.

Compute performs the first live copy, including hashes, seed exclusion and exact node
coverage. It obtains an independent source-to-copy review naming the three copy paths,
three digests, source path and the PRE-SPLIT citation. No local live runs file was opened.
