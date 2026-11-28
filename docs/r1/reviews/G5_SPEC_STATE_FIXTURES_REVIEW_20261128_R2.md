# Independent tier-E re-check of the G.5 spec-state test fixtures

Task `local/20261128-11`. Independent reviewer `Codex /root/g5_fixture_review`. Re-checked correction
`759325531c1886d2968e3adfb044b7d8c7049e0b` following the initial review of
`7939e98a44a65bb8b56f280af930000788f270ae`.

Verdict: ACCEPTED

The focused comparison exposed a byte-level regression in the first fixture. I reproduced it by writing the normalized
spec with the original single-line serialization. `key-lines` then differed from the draft's fenced §5 block on exactly
the `spec_sha256` line. The correction restores one-space indentation and the terminal newline.

I independently called the corrected fixture with the historical `a70c8872` draft blob and the rendered filled spec as
sources. In each case the generated file matched all 26,114 bytes of the historical draft Git blob and had SHA-256
`16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f`. The `key-lines` CLI handler reproduced 56/56
fenced §5 fields from each generated file, with the expected `approved: true` render header.

`git diff --check` passed. The formatted fixture and the recorded review are the only changes since the originally
reviewed code commit. The accepted render's filled spec still has SHA-256
`7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e` and its unsigned note still has SHA-256
`1a2ecfc2a05136edea226ea5aacc136419f5b8e02abe8e4c8d7943f63834079c`. The focused and full suite comparisons remain
separate publication checks recorded in the `coord/local` handoff. The re-check used local spec fixtures and submitted
no jobs.
