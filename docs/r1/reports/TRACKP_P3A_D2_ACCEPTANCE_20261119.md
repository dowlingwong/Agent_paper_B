# Track P P.3a D2 acceptance and delivery (19 November 2026)

**Status: ACCEPTED and DELIVERED; Unit B run on TASL-7 completed rc 0 (separate result record).**
Authority `R1-TRACKP-D2` on published main `de3de54f`. ENGINEERING_ONLY; no evidence run by this record.

## Code identity (ops handoff)

| Object | Value |
|---|---|
| Base D | `8662e35991659f7a661fb7ed6be4980791d302f3` |
| C2 | `9dc4afbaa29546dafb1d1274e37d3910c5d9ed0e` (code) |
| D2 | `8309b69e81837fb9719fa01b28f0dde94975e4f9` (mechanical delivery-pin child; single parent C2) |
| D2 runner blob sha256 | `d3419e2d2582367b5bb0b53994c9baaf5a04a3815b4b5a47ce38786c25a64750` |
| D2 child script sha256 | `5679ce1bc26721ca129fedf7e9e9bef705d8ce056eb2fac7e745d7879b65aee6` |
| Branch | `trackp-p3a-d2-20261119` (pushed to origin); operator must run **detached** at D2 |

Review rounds: R1 NOT ACCEPTED (1 MAJOR: TASL-2 lease-log conflation; 4 MINOR), R2 NOT ACCEPTED (MAJOR-1
fixed; new MAJOR-2: TASL-7-only driver snapshot/child recording), R3 **ACCEPTED** (0 BLOCKING/MAJOR; 3
MINOR documentation-only). Reviews: `docs/r1/reviews/TRACKP_P3A_D2_CODE_REVIEW_20261119.md`,
`…_R2_20261119.md`, `…_R3_20261119.md`. Tests: C2/D2 **69 passed, 5 failed, 2 skipped** vs base D
**49 passed, 5 failed, 2 skipped**; the same 5 pre-existing torch-missing failures. Scope: only the host
contract (TASL-7/TASL-2 profiles, per-host driver/freeze pin, attempt-1 artifact hashes instead of boot-id
equality, host-aware driver/child/lease recording); probes/units/order/seeds/data/budgets/STOPs/marker/
paper-head/executing pins unchanged.

## Errata / disclosures (R3 MINORs, non-blocking)

1. The delivery record's `Verification commands` paragraph cites two stale intermediate values (`HEAD^ ==
   C2 e8816221…`, runner `f284d233…`); the authoritative values are C2 `9dc4afba…`, D2
   `8309b69e…`, D2 runner blob `d3419e2d…` (the record's Delivered-objects table is correct).
2. The unit report §3 says `test_trackp_gpu_budget_safety.py` is unchanged; the boot-source stub changed
   (host-aware record). Tests still 6 failed/3 passed identically on D and C2.
3. The e2e "only … stubbed" wording omits the E0/rule/config/freeze rebinding and
   `installed_kev_encoder`/`attempt1_environment` stubs; disclosure is materially correct.
These are documentation-only; no code change and no re-review required for operation.

## Delivery and Unit B

D2 was delivered detached at `8309b69e…` in `/home/dowling/r1_trackp/d2_20261119` on TASL-7 (clean,
harness `897d83c8…`, frozen venv freeze `50238e5a…`), and Unit B ran on TASL-7 on 19 Nov 2026: root
`/home/dowling/r1_trackp/runs/p3a_attempt2_20261119T011430Z`, journal 8 events, DRYRUN 17.7276 GPU-s +
EVIDENCE 162.2841 GPU-s, total 130925.3907 GPU-s (36.368 h), A3/A4 pass, A3-descriptive skipped marker,
marker rc0, no STOP. Result: `docs/r1/reports/TRACKP_UNITB_TASL7_D2_RESULT_20261119.md`; captures under
`reports/trackp_unitb_tasl7_d2_20261119T011430Z/`.
