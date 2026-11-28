# compute/20261127-33 item 2 — P5 staged smoke on the per-card lease: PASS

**Result: the staged Track P smoke PASSes on Ada card 2 under the per-card lease.** bf16 matmul relative
error 0.002875; both DeltaNet forward checks pass; all four fast kernels bound; 3,345 MiB peak; 26 s
lease, 0 foreign processes at start and end. The E0 part is the accepted fresh-run unit
`compute/20261128-16`, not the superseded 10 %-RPS comparator.

- Task `compute/20261127-33` item 2 (P5 rerun); base `origin/main` `d25938ed`.
- Deliverable branch `compute-p5-smoke-percard-20261128` @ **`1e8b4aecf31ee4f240e697dc6b3e8f355e78bfd4`**;
  record `docs/r1/reports/trackp_p5_smoke_percard_20261128/P5_SMOKE_PERCARD_20261128.md`.
- Review branch `compute-p5-smoke-percard-20261128-review`: **pending**.
- Capture `SHA256SUMS` 7 entries; all verify.
- Host: Ada `ucrtasl`, `zli538` venv, Python 3.12.10, torch 2.6.0+cu124, transformers 5.19.0, CUDA 12.4;
  paper `c80f83bc`, harness `897d83c8`, config `trackp_ada_v1.json` `bb0c7251…`.
- Card 2 `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`; lease 12:15:18–12:15:44Z; command in
  `smoke_command.txt` with `--gpu <UUID> --lock /data1/zli538/r1_locks/gpu0.lock`.

## What this closes

The per-card lease path (`1f1b5d41`) is now exercised on Ada for the P5 smoke. The earlier P5 E0 miss
(25.9 % RPS below the 26 Oct reference) is superseded by **R1-P4-E0-CRITERION** and the accepted fresh
E0 unit: four runs, every slope pair within 0.05, RPS host means differ by 2.9494e-5 ≤ 3.04e-5
(`compute/20261128-16`, review `0bd80f7a` ACCEPTED). The reviewed timing carry-forward is the remaining
P.4 phase-1 item; this record makes no timing change.

## Hashes

| Object | sha256 |
|---|---|
| `smoke_report.json` | `dd0944fafef3c3aacd4dc46854c49e414abe25071650021fc5516fadcb2bf8af` |
| `smoke_lease.jsonl` | `9d5cd32323715e426ba3aa849135c94affb5d0da440d2c8b07dadc9df32bf09a` |
| `captures/SHA256SUMS` (record root) | 7 entries, verified |

No signed value, config or model byte changed; no label, test or evaluation value was read.

## What happens next

One fresh review; then the phase-1 note can cite the smoke and the accepted fresh E0, with the timing
disposition still to be reviewed. The P.4 path then moves to the phase-1 note signature; no new GPU job
is needed for this item.

Decided alone: Ada card 2 and its full UUID, the per-card lock/lease-log paths, the fresh capture
directory, and citing the accepted fresh E0 rather than repeating the superseded comparator.
