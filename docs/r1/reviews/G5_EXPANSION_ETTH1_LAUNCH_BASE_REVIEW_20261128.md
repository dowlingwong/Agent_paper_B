Verdict: ACCEPTED for desk delivery

# Independent tier-E review of the ETTh1 G.5 launch base

Task `local/20261128-15`, run `c3_t1_labels_20261128_addendum_3`. The reviewer
was independent of candidate preparation. Candidate
`e9441f03128bf6ed7291b854e70773f4c1dd5fba` has reviewed draft
`5e924f81f41beb34dc5ad30ccceedf35620ca474` as its sole parent. The paper pin is
`2a58f7ac5147dad1259914593901ccb226a147f9`. Published main was
`7cd65cfa37cc1ece18d773b662a3f9b8c45917ce`.

The candidate checkout was clean and `git diff --check` passed. Its two changed
paths copy the coordinator's approved note and add the launch-base record. The
note and spec match published main byte for byte. The candidate tree matches
the paper pin outside `docs/` and the ETTh1 spec. Strict `check-note` passed
with K = 10 against published main.

| Reviewed object | SHA-256 |
|---|---|
| Approved note | `903eb07a42affdd6f660847388ef3b318da3b50e62d0aed4a4ce8cfe05e1093b` |
| ETTh1 spec | `6c3323cae31c1f4e9433412143538dc3045323364f7b29b8d77c003464592758` |
| Launch-base record | `9b1987b597311c2413c16360b8f9bb98a8e5c4d220127c84ea989d1e55d43043` |

The unmodified `verify_launch_tasl` stopped at the candidate's publication
ancestry check. It passed with local merge `35e99b40eb5add6d9ad1c585a0b13fd053f33be2`
supplied solely for the `origin/main` advertisement, resolution and PLAN read.
The reviewer confirmed both merge parents and that the merge adds only the
launch-base record relative to published main. Launch-mode spec validation and
the import-source check also passed. This is a documentation-only delivery.

The reviewer separately ran the unmodified verifier at the real published
`7cd65cfa`. It passed using the advertised main, exact spec and addendum PLAN
row set. That published tree differs from the ETTh1 paper pin only in docs and
the ETTh1 spec. Both the published commit and the candidate returned Git
signature status `N`.

`canon/agents/local_worker/SOUL.md:22` specifies SSH-signed launch commits.
PLAN §10 `R1-G1B-TASL-DECISIONS` describes LB A as a signed, published commit.
The primary G.5 note invokes LB A on line 54. The runtime guard at
`sweep2/t1_tasl/g1b_tasl.py:1823–1876` checks ancestry and tree content. Signature
verification remains part of the pending launch-base disposition. Compute
verifies the coordinator-selected published tip, strict note, exact run ID and
live leases before submission. The licence line is required before a label
table cites ETTh1. The review used only local Git, published records and desk
validation.
