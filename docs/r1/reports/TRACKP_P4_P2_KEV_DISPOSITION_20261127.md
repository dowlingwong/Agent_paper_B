# Track P P.4 phase 1 P2 — Kev eligibility

Both Kev bases are eligible under P4-ARMS A and R1-C3-POOL-EXAM. Carry both Kev bases and both
Qwen controls. This record carries the synthetic E0 verdict and the engineering hard-limit
disposition needed by P2.

| Base | P.3a E0 v2 | E4 hard-limit disposition |
|---|---|---|
| `kev-0.8b` | PASS. Final soft-label fresh-head run reports `pass: true` and its A4 probe reports `pass: true`. | No disqualifying failure recorded. Its accepted P.0 spike completed the approximately 1,024-token, batch-8 checkpointed check and reloaded bit-identically. |
| `kev-4b` | PASS. Final soft-label fresh-head run reports `pass: true` and its A4 probe reports `pass: true`. | No disqualifying failure recorded. Its accepted P.0 spike completed the approximately 1,024-token, batch-8 checkpointed check and reloaded bit-identically. |

P.3a exercised E0 and E6. The E4 measurement in §5.4 belongs to E3. The disposition above
applies the exclusion rule in [§5.7](../TRACK_P_POST_TRAINING.md#57-pre-registered-selection-rule) to the available
records. The P.4 Ada staged smoke and E0 equivalence remain P5 checks.

## Sources and SHA-256

The P.3a source is `ops-tasl-20261116` at `2287e4926fe0895b0a55b3a6a61c9afadc701307`.
The Unit B summary is `docs/r1/reports/TRACKP_UNITB_TASL7_D2_RESULT_20261119.md`
(`cb2cdf3f107b8f5e6192f04faa511178e9a51c390df56014f15a83a493fea45d`). It records verification
of the attempt-1 final manifests and saved files for all four bases. Its completed evidence
probe was for the Qwen 4B control. The Kev verdicts come from the attempt-1 records below.

Paths in the table are relative to
`docs/r1/reports/trackp_p3a_attempt1_inventory_20261116/runs/p3a_operator_20261027/EVIDENCE/`
at that same source commit.

| File | SHA-256 |
|---|---|
| `kev-0.8b/final/report.json` | `158d89df5407b7e0ecdc8f8167470a584ae53fd14458977c8c8a22bf481cefdb` |
| `kev-0.8b/probes/report.json` | `f04df4e113d34fc117b4a881b5bfd34da81f711194b24e87c3e2c060c43d6f27` |
| `kev-4b/final/report.json` | `ae6115075213f26965585e3150ccd37e6c27f0e3ead4848d93331a1edd227836` |
| `kev-4b/probes/report.json` | `fae7c9cbda0c7fbeb55e2993445d096c1a86f0aa487637b80d4e8b96edd5033e` |

The engineering source is the [accepted P.0 spike report](TRACKP_P0_SPIKES_20261026.md), SHA-256
`1e304ff19355962ee54171051c9b3bfeef3e6a686da57f5deaff0af54f6e8ad6`, on published main at
`83425c7008826c2a4edb5470c708d8ce083d13f3`.
