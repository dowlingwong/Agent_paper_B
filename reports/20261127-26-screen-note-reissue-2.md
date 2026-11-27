# local/20261127-26 — second screening note re-issue ready for signature

for: coordinator

- Published base `523ccfbc982c3c2c80b5fa0120ca114a6b13a56e`.
  Branch `mac-screen-note-reissue-2-20261127` at `78dfbada39584927b08767a52a96dedef3542ed3`.
  Reviewed draft commit `68bbee155663ff3b6f61be7e6ee3218c33bbcec7`.
- Draft `docs/r1/authorizations/screen_measure_20261127_reissue_2.md`, SHA-256
  `9b86e40cec73cc9e39be004c4479059d0c8977184b78f244b376b9acd9005e2a`.
  Independent tier-E diff re-check **ACCEPTED**, review
  `docs/r1/reviews/SCREEN_MEASURE_REISSUE_2_REVIEW_20261127.md`, SHA-256
  `bac83f85c1b7bb0d0d8772fbacdd2c88e731aeb9c84d8c8ff9f325427b9694aa`.
- Exact code `c12136d664ae588a2539b76b2602e36742979ce8`, published exact-code acceptance
  `docs/r1/reviews/SCREEN_MEASURE_CACHE_LAYOUT_REVIEW_20261127.md`,
  runner SHA-256 `ba05e1a4a1ff5ee643e749e60fbd6e3aa4e6681209ef2f5af940e6cafd4fdb69`.
  Cache tree `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07`,
  cache manifest `1987cc004aba9ead9705788d98cf05720855c5c0977be5c8eb3404f375382c21`,
  smoke manifest `3c6dd543314aa58b0e5dad266c18769f92c881befe8af9dc17e64f955f44d580`,
  worker runtime SHA-256 `4633b06b663d0f8cd30d7ffea2238e8e75dec1169d613a27f086ff7a32180141`.
- The second re-issue references the cache STOP at 30/10,164 and binds the new cache and
  168/168 engineering smoke. The dependent review pointer, runner hash and P3/P8 receipts
  follow the exact new code and smoke. Python `python3`, the design, seeds 3301–3420,
  the harness and analysis and STOP rules carry over. The unchanged companion SHA-256 is
  `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`.
  The pre-declaration does not bind a runner SHA. Both prior authorization blobs remain as published.

**Checks.** Exact-code screening tests **83/83**, `git diff --check` passed. Production
preflight refused the unpublished note and, with the draft bytes supplied as a publication
fixture, refused `approved: false`. With only that field changed in memory, preflight passed
real Git provenance, PLAN, companion, design, code hashes and seed check using host,
harness-equivalence and co-tenancy fixtures. The reviewer matched the cache trees, four ARFF
content pins, 168 runtime receipts and the 37 identity flags.

**Author line.** Recommended reply `签 screening 二次重发 + 推 main`, approving the exact
draft named above with `approved: true` and the author's signature wording. The coordinator
records the decision and publishes the signed note. Compute then checks the active jobs and
attempt ledger and runs the strict preflight on deepthought from the exact declared code.
Use one fresh UTC stamp for the note's launch, scratch and analysis paths, distinct from
`20261127T1032Z` and `20261127T1155Z`. R1-D3-STEP8-HOLD remains in force.

Decided alone: use the accepted smoke's exact code commit, `_reissue_2` filename and a
single fresh stamp. No live run was submitted.
