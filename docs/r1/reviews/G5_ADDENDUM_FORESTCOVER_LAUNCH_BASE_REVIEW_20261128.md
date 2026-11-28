Verdict: ACCEPTED for desk delivery.

# Independent tier-E review of the Forest Cover G.5 launch base

Task `local/20261128-17` covers run `c3_t1_labels_20261128_addendum_4`.
The reviewer did not write the candidate. This review covers the exact candidate
`f96069d0df2633a35402dd5dc85abf1f8885a6b3`, based directly on the previously
reviewed delivery `9825ee84a9eb28e20be076a4caffbd4f9d1dbb40`. The approved
publication is `c3a484055f717865e4e6826833e405af41771013`. The paper pin is
`f532176f3f0241909c9fb8df63a58e6fbefaefbd`.

| Object | SHA-256 |
|---|---|
| Approved note | `085126933b9cc013f159d76ba7010f9d11acaf9252704554eabea6f8923f0e12` |
| Forest Cover spec | `2834327aac53e5172cef3dce4aafd4f646903c0c3f4af7dc86adfbc7551b1a78` |
| Desk launch-base record | `060beba8643713414d16e41526e7d1e14ca3a3f3c19483a54ecded4d30d78a90` |

The candidate changes two documentation paths relative to its reviewed parent.
It copies the published note byte for byte, which changes only the approval field
relative to the parent, and adds the launch-base record. The spec is unchanged
from the parent and byte-identical to the published spec. The paper pin is an
ancestor of the candidate. Their trees agree outside `docs/` and the one
Forest Cover spec. The checkout was clean and `git diff --check` passed.

At the exact candidate, the stock strict `g5_tasl.py check-note` passed with
K = 10 and stock `g5_tasl.py validate --launch` passed with an empty launch-blocker
list. The G.5 import-source check and the addendum's PLAN-row lookup passed.
The stock `verify_launch_tasl` refused the candidate against the real remote main
at the publication ancestry guard.

I independently reproduced the tree for the two-parent simulated merge
`45d328573601e7a57cba8f904de6e0c0b771be82` with `git merge-tree --write-tree`.
Its parents are the published tip and the exact candidate. The merge adds only the
desk record relative to published main and preserves the approved note and spec.
Its tree still equals the paper pin outside `docs/` and the run's own spec.
A local Git wrapper redirected only the remote main advertisement, resolved main
ref and PLAN read to the simulated merge. The unchanged verifier passed for the
candidate with that simulated main. Repository identity, checkout cleanliness,
ancestry, spec bytes and tree comparison used the actual Git objects and checkout.
The simulation created no publication and ran no host job. The full suite was
unnecessary for the documentation-only delta under R1-AUTONOMY (3).

**Launch STOP.** The exact candidate is unpublished and unsigned. The primary
G.5 note's launch field invokes LB A under R1-G1B-TASL-DECISIONS, which describes
a signed, published checkout. The Local SOUL specifies SSH signing for launch
commits. The verifier checks tree and publication ancestry and contains no
signature verification. The author decides the G.5 launch-base route and the
coordinator records the applicable signing and publication disposition. Compute
then repeats the strict note and actual binding checks from the selected
published checkout and confirms the run ledger and live leases before submission.
