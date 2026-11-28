# Independent review of the P.4 E0 same-code repeatability record

**Verdict: ACCEPTED**

Reviewed deliverable tip `2cd0bd88a236b7025c32f8301a8309036b42667a` on
`compute-p5-e0-repeat-20261128`, against `origin/main` `914e1cf9` (PLAN row
`R1-P4-E0-REPEATABILITY` is present at `2e8d089a` and is an ancestor of the tip).
The tip is `b09268c3` plus one follow-up that force-adds the two `e0e.log` files and the
two lease-event `.jsonl` captures that `.gitignore` had skipped. The record is at
`docs/r1/reports/trackp_p5_e0_repeat_20261128/`.

Both branch commits touch only that record directory; no code, config, tolerance or
authorization file is changed. This review was read-only on both hosts; nothing was
run, submitted or modified there.

## Checks run and results

**1. Record integrity.** `shasum -a 256 -c SHA256SUMS` in the record directory exits 0
with 51/51 `OK`. The record has 52 files at the tip; the only file not covered by
`SHA256SUMS` is `SHA256SUMS` itself, and no listed path is missing. This was the one
defect of `b09268c3` (the logs and lease captures were untracked while already listed);
the follow-up commit fixes it at the reviewed tip.

**2. The four reports are the right runs.**

| Report | SHA-256 | Provenance check |
|---|---|---|
| Ada first | `7df24070ee8a3a0838b3e2b3e71bf264fcbc6d8fa5a531fac2d28c16d8b9e817` | byte-identical to `docs/r1/reports/trackp_p5_ada_20261127/e0e_report.json` on `origin/main` |
| Ada repeat | `d31b36079dd9429b69dcbcf5fa193af8284f0be2e31f66d3ed9aa67cccf6bc1e` | fresh run directory `p5_e0_rep_20261128_ada/e0e` |
| TASL-7 first | `e86dc68589cdc92419acc72bb59a24b52a2e2fd008b329713bc2779989aca2d9` | byte-identical to `docs/r1/reports/trackp_p5_tasl7_20261128/e0e_report.json` at `391c12bc` |
| TASL-7 repeat | `c9ccc2be59842d191fca931146712e905a3070146c06a6df428e6215d359a48b` | fresh run directory `p5_e0_rep_20261128_tasl7/e0e` |

The repeat reports' checkpoint paths, run directories, `created_utc` values and embedded
log JSON all point at the repeat run directories, not copies of the first runs.

**3. Config, manifest and checkout binding.** The Ada config
`ada_repeat_config.json` is `9773547dc286f638792b53b06cc7133d61209c2d9e92cdfd4982a062c1a2c054`
and is byte-identical to the first run's `e0_config_ref.json`; the TASL-7 config
`tasl7_repeat_config.json` is `4f47048dd37bb53b4ced22404d749253dd80d96a5c91f3750ab031d01aa35993`
and is byte-identical to `391c12bc`'s `e0_config_ref_tasl7.json`. The manifests' content
hashes `754f6854…` and `31dd5776…` equal the first runs' manifest content hashes, so the
configuration content is unchanged, not merely the archived byte copies.

Both manifests record paper `c80f83bc5bc93356dfacadcbcb5b186dfb59d028f`, harness
`897d83c8efa364ec2fdd37288241cc42e01d7274`, data manifest
`b963be2dd378241e0b0689907d4051bfa62922a8e4968aa40061ed7ef275bfef`, seed 0, and clean
paper and harness checkouts (`dirty: false`, empty `dirty_files`). Both reports are
`pass: true`, `stopped_at 2000`, `completed: true`, `early_stopped: false`; LoRA best
step is 1,900 in both Ada runs and 1,800 → 2,000 on TASL-7, as stated.

**4. Comparisons recomputed with the existing comparator.** The archived
`p5_compare_ada.py` is byte-identical to the comparator on `origin/main`
(`da5354ed…`), and the archived `compare.py` is byte-identical to the existing
`tasl7_equivalence_20261026` form (`bd957c0d…`); tolerances are unchanged at abs 0.05
for both slopes and rel 0.10 for RPS. Recomputing from the four archived reports
reproduces the record table exactly:

| Comparison | Width Δ | Mean Δ | Rel. RPS | Equivalent | Record |
|---|---:|---:|---:|---|---|
| Ada repeat vs Ada first | −0.019969 | +0.003359 | 9.662 % | yes | matches |
| TASL-7 repeat vs TASL-7 first | −0.034066 | +0.008051 | 26.125 % | no | matches |
| Ada first vs TASL-7 first | −0.002179 | +0.001491 | 23.596 % | no | matches |
| Ada repeat vs TASL-7 repeat | +0.011917 | −0.003201 | 7.463 % | yes | matches |

The stored comparison JSONs carry the same deltas and `equivalent` flags, including
the `compare.py` cross-repeat forms.

**5. Bit-identical claims.** The archived prediction arrays confirm the record: the LoRA
prediction file differs between first and repeat on both hosts (Ada `64b0f31d…` →
`db664b47…`, TASL-7 `1a1c8a77…` → `ef2b6116…`); Ada head-fit predictions are identical
(`c2dca733…` both runs); TASL-7 head-fit predictions differ (`ea0fc4af…` →
`7f75652b…`). The arrays are all `(1000, 12)` float32, and an array-level comparison
finds only the Ada head-fit pair identical.

**6. Lease and GPU-h.** Lease start/end UTC values are Ada 01:31:39–02:09:42
(2,283 s = 0.6342 GPU-h) and TASL-7 01:31:23–01:59:23 (1,680 s = 0.4667 GPU-h), total
1.1008 GPU-h; the arithmetic matches the record. Both lease captures are equal to the
manifests' `gpu_lease` blocks and show `other_processes.count 0` and `memory_mib 0` at
start and end. The GPU before/after captures show no foreign process on either leased
card (Ada card 0 at 5 MiB, TASL-7 card 0 at 44 MiB, with no process line).

**7. Scope.** The record proposes no new E0 criterion and changes no tolerance, seed,
config, data or reference; it explicitly leaves the existing criterion in force and the
P.4 phase-1 note and A5 SFT gated under `R1-P4-PHASE1-SIGNATURE`. The E0 runs use the
standard synthetic E0 dataset of the protocol; the logs and scripts contain no sealed
path, no sweep-2 label table and no test-label read beyond the protocol's own E0
evaluation.

## Minor, non-blocking observations

- The record's sentence naming the comparator outputs mentions the `compare.py` form for
  the TASL-7 within-host comparison but omits the also-present
  `comparison_tasl7_repeat_vs_tasl7_first.json` (`p5_compare_ada.py` form). Both files
  are present and agree; the prose is merely loose.
- The Ada manifest records the harness at `/data1/zli538/paperb_p4_20261127/harness`
  while the run script sets `AR_HARNESS_ROOT=…/p5_20261127_b/harness`. The first Ada run
  records the same manifest path and the same harness commit, so this is a pre-existing
  path/bookkeeping detail, not a repeat-run change; both are `897d83c8` and clean.

These do not affect any claimed result.
