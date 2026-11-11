# Track S A2-U stale fix — committed-root ledger check (test (c)), 11 November 2026

AI-assisted (Claude, Mac-local agent). This records test (c) of `R1-TRACKS-A2U-STALE`, which checks that the fix leaves valid trials unchanged on the five S0.4 committed-root ledgers. It is not the precondition run on TASL-2 that the PLAN row requires before the S0.4 rerun.

## Inputs

- The experiment agent copied the ledgers read-only from the S0.4 run tree on TASL-2 to `Claude outputs/tracks_s04_ledgers_20261111/<root_id>/root_trials.jsonl` on the Mac, together with a `SHA256SUMS` file. `sha256sum -c SHA256SUMS` passed on the Mac and again in the cloud workspace where the test ran:

| root_id | SHA-256 of `root_trials.jsonl` | bytes |
|---|---|---|
| `tracks_S04_digits_mlp__s30001` | `14d586ee58f6613c173c2fbe46a09337e13fcacacb5ce1c9bd7bfe469dc88e41` | 134,487 |
| `tracks_S04_digits_mlp__s30004` | `a8dbbd980d3eff068a799758bf678d570749e2799c30c305fa11a38a2c9ee4d7` | 108,221 |
| `tracks_S04_digits_mlp__s30006` | `cf3843528141fd6a3080ff1f9cb97c700b223329cfe5970b49550105dc3508b1` | 83,731 |
| `tracks_S04_digits_mlp__s30007` | `8ea9e20b34a6f1c1855a744e4f626dc0a575ad5002336d3a959d47389d013896` | 109,043 |
| `tracks_S04_digits_mlp__s30009` | `71c358c63165aeea4a8795f314a97cd42137e9cc4409d786acd8cda2fe11907c` | 98,898 |

- Code: the new Track S paper pin `8237fd02b09ef2d28016a1c9f6acac3c35bb768b` (the test file is identical at the branch tip). Harness `AR_HARNESS_ROOT` = clone of harness `a3fedbb`.

## Command and result

```
PYTHONDONTWRITEBYTECODE=1 AR_HARNESS_ROOT=<harness a3fedbb clone> TRACKS_S04_ROOTS=<copy of tracks_s04_ledgers_20261111> \
  python -m pytest -rs -s -p no:cacheprovider r1/tests/test_tracks_a2u_stale.py -k s04_committed_roots
```

```
collected 17 items / 12 deselected / 5 selected

r1/tests/test_tracks_a2u_stale.py tracks_S04_digits_mlp__s30001: 40 trials identical; ledger sha256 14d586ee58f6613c173c2fbe46a09337e13fcacacb5ce1c9bd7bfe469dc88e41
.tracks_S04_digits_mlp__s30004: 40 trials identical; ledger sha256 a8dbbd980d3eff068a799758bf678d570749e2799c30c305fa11a38a2c9ee4d7
.tracks_S04_digits_mlp__s30006: 40 trials identical; ledger sha256 cf3843528141fd6a3080ff1f9cb97c700b223329cfe5970b49550105dc3508b1
.tracks_S04_digits_mlp__s30007: 40 trials identical; ledger sha256 8ea9e20b34a6f1c1855a744e4f626dc0a575ad5002336d3a959d47389d013896
.tracks_S04_digits_mlp__s30009: 40 trials identical; ledger sha256 71c358c63165aeea4a8795f314a97cd42137e9cc4409d786acd8cda2fe11907c
.

======================= 5 passed, 12 deselected in 3.50s =======================
```

**Result: 5 passed, 0 skipped.** For each ledger, replaying its 40 trials gives decisions and controller log byte-identical between the previous pin `d10b05b7` and the fix. The ledger SHA-256 values printed by the test match `SHA256SUMS`.

## What this does not cover

The copies are not the run tree. The PLAN row's precondition (the same command on TASL-2 against `<S0.4 run.work>/roots`, at the new pin, 5 passed, 0 skipped, output in the rerun report) still has to be run before the S0.4 rerun.
