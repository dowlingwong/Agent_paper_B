# Independent review of the P.4 fresh-run E0 record (R1-P4-E0-CRITERION, option A)

Verdict: ACCEPTED

Reviewed deliverable tip `c22ba02108b57bcf5705e1674d0e7dab27bfb1d4` on
`compute-p4-e0-fresh-20261128`, whose parent is exactly `origin/main` `a70c8872ead621696b8f8f14134319009f0fa3e6`.
The branch is one commit and adds only the 46 files under
`docs/r1/reports/trackp_p4_e0_fresh_20261128/`; no code, plan, tolerance or authorization file is touched.
The criterion row `R1-P4-E0-CRITERION` (option A) is present at `f0e4809a` (merge timestamp 2026-11-28T09:01:24Z)
and is an ancestor of the tip, so the criterion was fixed before the first fresh lease at 10:13:12Z. This review
was read-only; no host workload was run or touched.

## Recomputed from the four fresh reports

Loaded `lora.test` from `ada/e0e{1,2}.report.json` and `tasl7/e0e{1,2}.report.json` and applied the signed
criterion directly (deltas are TASL-7 minus Ada, as in the comparator):

| Pair | Width Δ | Mean Δ | Both abs ≤ 0.05 |
|---|---:|---:|---|
| Ada1 vs TASL-7 run1 | −0.027054466929290477 | +0.003303325821021330 | yes |
| Ada1 vs TASL-7 run2 | −0.016320988710793350 | +0.005576805686686281 | yes |
| Ada2 vs TASL-7 run1 | −0.026591602369569922 | −0.004434438005238572 | yes |
| Ada2 vs TASL-7 run2 | −0.015858124151072794 | −0.002160958139573621 | yes |

Largest width delta 0.027054, largest mean delta 0.005577, so all eight slope checks pass with wide room.

RPS (each host mean over its two fresh runs):

| Host | Run 1 | Run 2 | Mean |
|---|---:|---:|---:|
| Ada | 1.1596670979920207e-4 | 9.51771040713234e-5 | 1.0557190693526274e-4 |
| TASL-7 | 1.5756761371621191e-4 | 1.125646408048218e-4 | 1.3506612726051686e-4 |

Absolute mean difference **2.949422032525412e-5** ≤ 3.04e-5, a margin of 9.0578e-7 (0.0906e-5, 2.98 % of the
limit). This reproduces the record's 2.949422e-5 and the PASS on part (ii), as well as the four pair deltas in its
table. Within-host spreads (relative to the lower run, the convention of the earlier record): Ada 2.078961e-5
(21.84 %), TASL-7 4.500297e-5 (39.98 %); the record's 21.8 % and 39.9 % are truncations of those values.

## Freshness, pins and provenance

- The four run directories (`p5_e0_fresh_20261128_ada/e0e{1,2}`, `p5_e0_fresh_20261128_tasl7/e0e{1,2}`),
  checkpoint paths and manifest `created_utc` values are new; no fresh report is byte-identical to any of the four
  earlier reports stored under `trackp_p5_e0_repeat_20261128/`.
- Each manifest records paper `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`, harness
  `897d83c8efa364ec2fdd37288241cc42e01d7274` (both `dirty: false`, empty `dirty_files`), data manifest
  `b963be2dd378241e0b0689907d4051bfa62922a8e4968aa40061ed7ef275bfef`, base `kev-0.8b` with the same base/adapter
  revisions as the earlier runs, seed 0, stage `final`, `evidence_label: DRYRUN`, and `head_form: linear12`.
- The archived configs are byte-identical to the earlier same-code configs: Ada
  `9773547dc286f638792b53b06cc7133d61209c2d9e92cdfd4982a062c1a2c054` and TASL-7
  `4f47048dd37bb53b4ced22404d749253dd80d96a5c91f3750ab031d01aa35993`. Recomputing
  `sha256(json.dumps(cfg, sort_keys=True))` gives the manifests' `config_sha256` values `754f6854…` and
  `31dd5776…`, so the content, not just the archived bytes, is unchanged.
- The Ada head-fit prediction hash `c2dca733…` equals the earlier Ada runs' hash, while the LoRA prediction
  hashes (`183edbbe…`, `2ae23843…`, `3121b4be…`, `45ab5e0b…`) differ from the earlier runs' hashes
  (`64b0f31d…`, `db664b47…`, `1a1c8a77…`, `ef2b6116…`) and from each other. This matches the record's statement.
- The `model_files_sha256` blocks differ from the earlier manifests because they hash each run's saved outputs
  (`saved/`), not the pinned input; the input is bound by the base revisions. The record does not use them as an
  input pin, so this is not a discrepancy.

## Lease and GPU-h

All eight lease events (four per host) record `other_processes.count 0` and `memory_mib 0` at start and end, and
each manifest's `gpu_lease` block equals the corresponding two `lease_events.jsonl` records. Cards are
Ada card 2 / `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154` and TASL-7 card 0 /
`GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, matching the table. Durations from the lease UTCs are 55 m 16 s,
54 m 51 s, 28 m 29 s and 29 m 01 s = 0.921111, 0.914167, 0.474722 and 0.483611 GPU-h; the record's 0.9211,
0.9142, 0.4747, 0.4836 and total 2.7936 all reproduce (exact total 2.793611). The before captures show Ada card 2
at 5 MiB used / 48,427 MiB free and TASL-7 at 44 MiB display use, with no foreign process line; the after captures
are present and show the same leased-card state (only unleased Ada cards 6 and 7 changed).

## Capture integrity

From a clean checkout of the tip: `shasum -a 256 -c SHA256SUMS` in the record directory is 45/45 `OK`; the nested
`ada/SHA256SUMS` and `tasl7/SHA256SUMS` are 20/20 `OK` each. The record directory has 46 tracked files and the
on-disk file set is identical to `git ls-files` at the tip; `git status --ignored` reports nothing, so no ignored
file is missing from git. The only file not listed in the root sums is `SHA256SUMS` itself, as expected.

## Comparator

`compare_e0_fresh.py` is new and read-only (stdout only). It reads only the four fresh `report.json` files and
implements the signed criterion exactly: absolute 0.05 on `width_slope_vs_label` and `mean_slope_vs_label` for
every one of the four Ada×TASL-7 pairs, and the absolute difference of the two two-run host means of
`lora.test.rps` against 3.04e-5. It contains no 10 % relative RPS band and no reference to the earlier comparator's
tolerance. Running it on the four archived reports exits 0 and reproduces `comparison_fresh_runs.json`
byte-for-byte, including `"equivalent": true`.

## Findings

- **B (blocking):** none.
- **M (major):** none. The arithmetic, freshness, pins, lease evidence, capture integrity and comparator all check
  out, and both parts of the criterion hold on the fresh runs only.
- **m (minor, non-blocking):**
  1. The TASL-7 within-host absolute RPS spread (4.5003e-5) is itself larger than the 3.04e-5 cross-host limit, so
     the pass depends on the two host means cancelling. The record states the percentage spreads and the explicit
     caveat that this is "not evidence that the RPS comparison is stable", which satisfies the honesty requirement,
     but it does not spell out the absolute within-host comparison. Worth carrying into the timing review.
  2. The record's 39.9 % is truncated from 39.978 % (one decimal would round to 40.0 %); Ada 21.84 % is likewise
     truncated to 21.8 %. Both are conservative and consistent with the earlier record's convention.
  3. "The Ada card was empty at card 2" while `gpu_before.txt` shows 5 MiB resident; this matches the earlier
     records' treatment of display/context memory as empty, and the lease still counts 0 foreign compute
     processes.
  4. `compare_e0_fresh.py` leaves its `open()` handles to the interpreter; a style point only, with no effect on
     the result.

No blocking or major finding. The record's verdict is a correct pass of R1-P4-E0-CRITERION option A on the four
fresh runs, and its qualifications about the narrow margin and the large within-host spreads are present and
accurate.
