# Independent tier-E review of PRE-SPLIT v2 publication preparation

Task `local/20261127-30`, unit 1. Fresh independent review, base
`f43823dad358a25608fe27013221eba9aaa7d385`, reviewed candidate
`75a0834bdeeff7d4fd02d325aa5913ce72dc741a`.

Verdict: ACCEPTED

The candidate implements R1-G5-S9 (1) only. It cites split v2, retains the v1 rules and salts,
records the identical T0 and original eight T1 entries, and identifies the four added entries.
The frozen preregistration and the two split files have identical Git blobs before and after the
change. The review independently verified all three referenced digests and the draft SHA-256
`59bf973def0e080f985864ffa9818c12122d5737718c640f163a1adf7218ff21`.

The independent reviewer reran the committed synthetic publication fixture. `split_v2_amendment`
refused a missing amendment, an unsigned amendment, and an approved amendment absent from the
fixture's publication ref. It accepted the exact bytes once the fixture's `origin/main` pointed
to the publication. The existing `r1/tests/test_p3_split.py` had 17 passes and 1 skip.
`git diff --check` passed. No blocking or minor findings.

The candidate retains `approved: false` at the proposal path. The coordinator applies A§4 using the
authorization record and publishes the resulting companion. The fixture used synthetic signing
metadata in a private temporary repository. The review opened no sealed data.
