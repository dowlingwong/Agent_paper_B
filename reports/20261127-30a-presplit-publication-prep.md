# local/20261127-30 unit 1 — PRE-SPLIT v2 publication handoff

for: coordinator

Base `f43823dad358a25608fe27013221eba9aaa7d385`. Branch `mac-g5-presplit-publication-prep-20261127` @
`486d1150bfa41d29f5f065d9eed4cbf53272f7ac`. Reviewed content `75a0834bdeeff7d4fd02d325aa5913ce72dc741a`.
Independent tier-E verdict **ACCEPTED**. Review `docs/r1/reviews/G5_PRESPLIT_PUBLICATION_PREP_REVIEW_20261127.md`
SHA-256 `2aa9eeab00392c07b032b2f0a05786c39e551a134d21c5931f16600e3112090e`.

The amendment in `docs/r1/proposals/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_DRAFT_20261127.md` (SHA-256
`59bf973def0e080f985864ffa9818c12122d5737718c640f163a1adf7218ff21`) implements only R1-G5-S9 (1).
Frozen preregistration SHA-256 `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`
and both split files retain their exact bytes. Split v1 SHA-256
`b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`, split v2 SHA-256
`4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a`.

**Tests.** The real `r1.c3.release.split_v2_amendment` refused the missing, unsigned and approved-but-unpublished
variants in a scratch Git fixture, then accepted the committed approved fixture when the fixture's
`refs/remotes/origin/main` exactly matched its bytes and author row. Existing split tests: 17 passed, 1 skipped
in independent review. `git diff --check` passed. Markdown-only unit.

**Next.** Coordinator applies the existing A§4 publication fields from the authorization record and publishes
`docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md` under R1-G5-S9 (1).
After fetching the published branch, run `python -c 'from r1.c3.release import split_v2_amendment; print(split_v2_amendment())'`
in a clean published checkout, and report the resulting SHA-256. Unit 2's addendum launch binding is separate.

Decided alone to narrow the draft to the signed split citation and exercise the real checker in a synthetic Git
repository. The assigned checkout was used for edits with writable Git metadata in a scratch directory. No sealed
partition was opened and no host job was submitted.
