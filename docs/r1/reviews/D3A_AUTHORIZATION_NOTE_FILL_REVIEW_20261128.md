# Independent tier-E review of the D.3a draft handoff

**Task `local/20261128-08`. Reviewed commit `0c1db6d095e9ba8833cf5cd09a904660aecc97f2` against
published base `8fbad26ac68236bbf47d2f099851a906cb4f8427`.** Review by a fresh Codex agent that did
not write the draft. The draft SHA-256 is
`77784011501d4db10e16b3ac954cabd4100bd98b352f90a66e9e891fe1736994`.

**Verdict: ACCEPTED for blocked handoff.**

**Signature readiness: blocked.** The exact runtime and lease, host RAM and scratch sizing, elapsed
projection, fresh run ID and launch SHA, P10/P11 on that SHA and final independent review remain due
before P9.

- P1–P6 and P8 citations were checked against their accepted published records. The frozen declaration,
  checker, analysis, tests, constants and train/dev receipt SHA-256 values match the declared values.
- The accepted P7 worker gate covers 14/14 engineering campaigns, with 33/271 charged failures
  (12.18%), 0.81 percentage points below 12.99%. P7 §5 and the accepted R3 re-check support 38.3 GPU-h
  and 42.5 GPU-h in the reported A0R latency sensitivity. The seven rounded per-node timing bases
  sum to 19,719 seconds, about 38.34 GPU-h across seven nodes. The card's 38.7 GPU-h differs from
  the published receipt and should be disclosed in the handoff.
- The captured `-c 8192` supports the exact-runtime hold. Effective q8_0 K/V remains unverified in
  the captured command. Smoke Python 3.11.17 differs from the comparison in frozen rev 4 §7.2.
  TASL-7's empty-card condition matches the task card for the initial host check.
- Independent checks at the documentation-only candidate passed. The verify checker returned PASS
  for 160 seeds (20010–20801), the analysis suite passed 53 synthetic tests in 2.99 seconds, and
  `git diff --check` passed. The review used published readiness records and synthetic tests only.
