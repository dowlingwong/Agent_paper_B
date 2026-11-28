Verdict: ACCEPTED for desk delivery

# Independent review of the Titanic and MetaMaze G.5 launch-base candidates

Task local/20261128-15. The reviewer took no part in preparing either candidate.
Published main was 2a58f7ac5147dad1259914593901ccb226a147f9. The paper pin
for both specs was 9b044b59f58109b3d1e4eb1822623160958b1d95.

| Node | Candidate tip | Reviewed parent | Simulated merge |
|---|---|---|---|
| Titanic | 88edb84f3c252fc75b760f2650170a14462379f0 | 6e2333e930b1cf5a3139d132bf81e61aefb9fc51 | f64f624ed64a57972e741439468ce03a10c94ab9 |
| MetaMaze | 4ee43037c06efc7398bf4b698489c0648ae3eb0d | 9798799c973ec4dca107bf45fbd2882a97b6d921 | 51558afcdf381d417cdeefd18c114dbfee6a31ca |

The reviewer confirmed the parents, clean checkouts, diff checks and two changed
paths per candidate. Each candidate carries the approved note and a short record.
Both committed notes and specs match published main byte for byte. Each tree
matches the paper pin outside docs/ and its own spec. Strict check-note passed
at K = 10 on both candidates against the real published main.

The real verify_launch_tasl refused both candidates at the publication ancestry
check. The reviewer checked the simulated merge objects, their exact parents and
their docs-only diffs against real published main, then ran the actual validator
with only the simulated origin/main resolution and advertisement. The import
source and launch-row checks passed on both.

Both candidates are unsigned. The Local SOUL, line 22, specifies SSH-signed
launch commits. R1-G1B-TASL-DECISIONS describes LB A as a signed, published
commit, and the primary signed G.5 note, line 54, invokes LB A and requires
the checkout to be at or after publication. The runtime guard in
sweep2/t1_tasl/g1b_tasl.py, lines 1823–1876, performs no cryptographic signature
check. Desk acceptance leaves the signing and publication disposition with the
author and coordinator. Actual ancestry and strict checks precede any job.

No host or sealed evidence was accessed. This is a docs-only delivery.
