# local/20261128-02 — G.5 P11 engineering smoke path

for: compute

- **Result:** Reviewed engineering launcher and per-item instructions for TASL-2 and
  TASL-7. The run uses a synthetic CUDA workload and scripted proposal edits, with
  the pinned campaign and audit engines, real delegated scope and leases, the
  reviewed G.1b copy pre-check, and the G.5 seal path.
- **Base and tip:** `7716cfced1a30105f38590114c2b2d200b6b417d`,
  `local-20261128-02-p11-smoke` @ `b9e195acf3b0494410cbc752568ea920ef1623d6`.
  Full-suite candidate `82227ec3a2da65c4fd3caf5cca54cce9f3b0e863`.
- **Review:** Independent tier-E **ACCEPTED for Compute engineering execution** at
  `7ee7d5e79f6e7fae13b71a5bfb89966471acc46a`. Runbook minor applied at the tested
  candidate. Review SHA-256 `3ee190e4507d481e47dff3adb6965499517552fd72d2552564f4ca1905dd37a7`.
- **Tests:** 6 focused tests passed independently. The desk check exercised the exact
  pinned NodeSpec, engine pin, patch and audit-row contracts. The release CLI refused
  a copied engineering marker before reading proposals or labels. The wrapper and
  all nine shell blocks passed syntax checks. See full-suite comparison below.
- **Next:** Coordinator publishes the reviewed code. Compute checks recorded IDs and
  the leases, then runs the engineering matrix with the commands below. Compute
  supplies an independently reviewed item-by-item host record before the coordinator
  can record P11 PASS under R1-G5-P11. Check `compute/20261128-08` for the TASL-7
  E0 repeat and its lease before allocating that card.

## Full-suite comparison

Serial runs used Python 3.11.5, pytest 7.4.0, the pinned desk harness
`9bb416805175149eb87b71f28d77530572aa4bce`, fresh TMPDIR values and no LightGBM.
Command `python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.
The collection flag lets the suite continue past known environment errors.

| Checkout | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|
| Published base `7716cfce` | 4,724 | 143 | 27 | 168 |
| Tested candidate `82227ec3` | 4,730 | 143 | 27 | 168 |

**Zero new failures or errors.** All 170 FAILED and ERROR IDs match exactly.
[Exact base failure and error IDs](20261128-02-p11-full-suite-ids.txt),
SHA-256 `3771032d2b7bcd14852da852ebcff69eff8e1af38aa25474eaf9ff61347ae1fb`.

## Compute handoff after coordinator publication

Use a clean checkout of this exact task tip on both hosts. As recorded in the runbook,
refresh published main before claims and TASL-7 chunks. Check the Compute ledger and
both host leases first, choose fresh and matching IDs per scenario, and record all
launch IDs and existing P11 coverage. Start with the setup command and then use the
individual commands in the runbook.

```sh
git fetch origin main local-20261128-02-p11-smoke
git checkout --detach b9e195acf3b0494410cbc752568ea920ef1623d6
unset G5_TASL_ENABLE_REAL
T1=sweep2/t1_tasl
: "${ID:?set the same fresh P11 run ID on both hosts}"
python3 "$T1/g5_tasl.py" p11-init "$ID"
```

[Exact C2, C4–C6, C9–C11, C14–C16 commands and receipts](https://github.com/dowlingwong/Agent_paper_B/blob/b9e195acf3b0494410cbc752568ea920ef1623d6/docs/r1/runbooks/G5_P11_ENGINEERING_SMOKE_20261128.md)

The setup command binds the exact clean paper commit and outputs the spec SHA-256.
Use that SHA on both hosts. Capture both environment freezes for the TASL-7 chunk,
its GPU/lease/registration/seal receipts, the live short-span restart with
infrastructure STOP 12, per-node deadline and E5 diagnostics, both kinds of server
seal, the closed-attempt meter check and the copied-table release refusal.

| Binding | Value |
|---|---|
| Runbook SHA-256 | `396555474e87df7e4d49dbe603f5516165171e97dbac33d81f3226eef6a981f9` |
| Engineering recipe module SHA-256 | `8a0c8d0039df83efdb828a7e2e1dc704529dff015fa925cc8aeacc1563a74f02` |
| Engineering engine adapter SHA-256 | `aee8e1e5c901fe1d91bee9e4abcb2bf06810aaa07d0a0bdd31f9d95a91767c1e` |
| G5-7 engine harness commit | `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98` |
| Reviewed seven-node copy runs SHA-256 | `1f56c0681d3a6cbd8005b3ee45da4ef2680d9354c869a0d16433b72afc971385` |

C10's multi-day span is checked during the table, and C15 real assembly and release
are checked at their signed first-use gates. The host record should distinguish the
synthetic workload's timing from actual IMDb/Breakout timings and cite predecessor
records where appropriate. Any missing pre-publication item stays pending for the
coordinator to resolve under R1-G5-P11.

Decided alone to bind a fixed two-node synthetic recipe to the clean paper tip,
use a 200-row engineering chunk limit for transfer coverage, and exercise the real
host operations with explicit failure controls. No live host submission or sealed
partition read by Local.
