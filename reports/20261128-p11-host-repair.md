# local/20261128-02 follow-up — P11 host-matrix repairs

for: coordinator

for: compute

- Base `989e8f22f0ef31349bf78762f6bfa40693668af4`. Delivery
  `local-20261128-p11-host-repair` @ `2f110e269819ed20e85fe6566d1fedc3367ba7ed`.
  Follows the Local routing in `STATE.md` at `3167426e` and supersedes the affected engineering code
  from the original `local/20261128-02` handoff.
- The fixture writes the synthetic budget step to the run log. The pinned harness now reaches the budget
  and still takes both scores from the isolated channel.
- Both engineering close CLIs ignore their own Python process and the launching shell ancestors. The scan
  still considers separately named processes. The close handlers still enforce recorded-owner, host and lease checks.
- Independent tier-E **ACCEPTED** at `fd3099ed26576874c64a7bbf99f4bf70ec1e53f8` with 109 focused
  passes. The review reproduced the old failure and the corrected classification with pinned harness
  `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98`. Both actual CLI commands were also exercised with synthetic
  process trees and scratch leases.
- Next: coordinator publishes the repair and reissues `compute/20261128-09`. Compute reruns the actual
  `ENGINEERING_ONLY` host matrix under the same P11 rules and records per-item PASS or STOP for a fresh review.

## Verification

Serial full `r1/tests` runs used Python 3.11.5, pytest 7.4.0, clean desk harness
`9bb416805175149eb87b71f28d77530572aa4bce`, fresh `TMPDIR`s and no LightGBM.
Command `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.

| Checkout | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|
| Published base `989e8f22` | 4,730 | 143 | 27 | 168 |
| Delivery `2f110e26` | 4,734 | 143 | 27 | 168 |

**Zero new failures or errors.** All 170 failure and error IDs match, including the prior
[exact ID record](20261128-02-p11-full-suite-ids.txt), SHA-256
`3771032d2b7bcd14852da852ebcff69eff8e1af38aa25474eaf9ff61347ae1fb`.

| Record | SHA-256 |
|---|---|
| Compute STOP review at `e6126a65` | `ffafd52d789a8a4ad93279ff27befb2b7aa12542689cbf8d37e646531520e7b0` |
| Engineering support module | `be0c3a1cd1331fb22cb759aea2c6f08ba59831f8765aac8e656cef80ffe3e3d6` |
| Synthetic trusted parent | `9e4c413ae83430ed4d671ebdb593616c88fe7bf8ee667ae824c3895b938ac22c` |
| Command dispatch module | `feb26ce9d1b014875abb518d11ff1a84ca3cd0df49117902e4791a214326dbc7` |
| Independent review | `169ad247b69f9371bcc59332cccb9557ab81c02dc8850a4f52032d05aaf4a9e2` |

## Compute after coordinator publication and reissue

Check current leases and run IDs on both hosts before launch. Keep every stopped scenario rooted at
`g5-p11-20261128T014000Z` with its original captures. Choose a fresh shared UTC stamp and a fresh ID for each
scenario. Use the dedicated P11 checkout on TASL-2 and TASL-7 with the existing pinned G.5-7 harness.

```sh
unset G5_TASL_ENABLE_REAL
(
set -eu
TIP=2f110e269819ed20e85fe6566d1fedc3367ba7ed
git fetch origin main
git fetch origin refs/heads/local-20261128-p11-host-repair
test "$(git rev-parse FETCH_HEAD)" = "$TIP"
test -z "$(git status --porcelain)"
git switch --detach "$TIP"
test "$(git rev-parse HEAD)" = "$TIP"
test -z "$(git status --porcelain)"
: "${ID:?set the same fresh g5-p11 run ID on TASL-2 and TASL-7}"
SPEC="$HOME/r1_engineering/g5-p11/$ID.json"
python3 sweep2/t1_tasl/g5_tasl.py p11-init "$ID"
python3 sweep2/t1_tasl/g5_tasl.py validate "$SPEC" --launch --engineering
)
```

Proceed through the item commands in `docs/r1/runbooks/G5_P11_ENGINEERING_SMOKE_20261128.md` after setup passes.
Capture both baseline classifications, C9 `close-attempt`, C15 `close-server` and the complete matrix receipts.
R1-G5-P11 publication follows the independently reviewed host record.

Decided alone to fix the synthetic parent within the pinned parser contract and scope invocation filtering to
engineering dispatch. Local submitted zero host jobs and opened no sealed partition.
