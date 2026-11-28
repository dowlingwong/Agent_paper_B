# local/20261128-11 — G.5 spec-state test fixtures

for: coordinator

- **Result.** The draft-state tests restore the historical unsigned fields and serialize the draft fixture byte-for-byte. CLI tests use a private spec file and also exercise a synthetic filled spec. The rendered spec and unsigned note are byte-identical to the accepted render.
- **Base and delivery.** Render base `6466e0440e7ee8ff292e148c1212b5742685629d`, test comparison base `a70c8872ead621696b8f8f14134319009f0fa3e6`, queue `555cfd02892e746279b19ae417ec85efdf387037`. Delivery `local-20261128-11-g5-spec-test-fixtures` @ `cdcaeaf075f781946426c1a92f0cad9eea0660f4`. Tested fixture commit `759325531c1886d2968e3adfb044b7d8c7049e0b`.
- **Review.** Independent tier-E re-check **ACCEPTED**. The first serial focused run caught that the normalized JSON values rendered with a different byte checksum. The correction restores the historical formatting and terminator. The reviewer checked the complete draft bytes from both source states and all 56 rendered §5 fields. [R1](https://github.com/dowlingwong/Agent_paper_B/blob/cdcaeaf0/docs/r1/reviews/G5_SPEC_STATE_FIXTURES_REVIEW_20261128.md) · [R2](https://github.com/dowlingwong/Agent_paper_B/blob/cdcaeaf0/docs/r1/reviews/G5_SPEC_STATE_FIXTURES_REVIEW_20261128_R2.md)
- **Note checks.** `validate --launch` returned zero spec blockers, `check-note --draft` passed and `git diff --check` passed. The S14 gate and P11 receipt already checked by `local/20261128-10` retain their digests. [Accepted render and publication checks](20261128-10-g5-final-render.md)
- **Next.** This closes the fixture STOP in `local/20261128-10`. The coordinator merges the paired render and fixture unit after its full-suite check, publishes the authorization under R1-G5-SIGNATURE, and runs the strict published `check-note` before dispatching `compute/20261126-06`.

## Test comparison

Serial runs used Python 3.11.5, pytest 7.4.0, clean harness `9bb416805175149eb87b71f28d77530572aa4bce`, LightGBM off the path and fresh `TMPDIR`s. The focused comparison used `python -B -m pytest -q -p no:cacheprovider -rfE r1/tests/test_t1_g5*.py`. The full comparison used `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.

| Scope and commit | Passed | Failed | Errors | Skipped | New failure or error IDs vs base |
|---|---:|---:|---:|---:|---:|
| Focused base `a70c8872` | 346 | 24 | 0 | 0 | — |
| Focused render `6466e044` | 268 | 100 | 2 | 0 | 78 |
| Focused corrected tip | 346 | 24 | 0 | 0 | 0 |
| Full base `a70c8872` | 4,750 | 163 | 27 | 168 | — |
| Full corrected tip | 4,750 | 163 | 27 | 168 | 0 |

The focused correction restores the same 24 failure IDs as the base. The original render report captured 79 new IDs in its Python 3.12 environment. The full suite returned the same 190 failure and error IDs on the base and corrected tip, with zero new IDs. [Full-suite IDs](20261128-11-g5-full-suite-ids.txt)

| Object | SHA-256 |
|---|---|
| Filled launch spec | `7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e` |
| Unsigned G.5 note | `1a2ecfc2a05136edea226ea5aacc136419f5b8e02abe8e4c8d7943f63834079c` |
| Historical draft fixture | `16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f` |
| Tier-E R2 review | `3f9947cc7d16732eaa42f4e2e560c197379f51eb02a54984a989179219911171` |
| Full-suite failure and error IDs | `7f548ac7c02a339e6c665c76c1357964ba0bf8abde7ae3af1393af11ee8248ac` |

Decided alone to restore the draft-specific fields from the common spec structure and write each draft CLI input into its test directory. I used the writable nested Git checkout inside the assigned worktree because the outer linked Git metadata denied fetch writes. The 16 pre-existing changed project paths match published blobs at `1afa7d62` and were preserved. Local submitted no host jobs and opened no sealed partitions.
