# P5 staged Track P smoke on the per-card lease — PASS (Ada card 2)

Follow-up to `compute/20261127-33` item 2 and `compute/20261127-29`. The staged Track P smoke now runs on
the per-card lease path (reviewed `mac-trackp-per-card-lease-20261127`, merged `1f1b5d41`) on an empty Ada
card. ENGINEERING_ONLY.

- Task: `compute/20261127-33` item 2; base `origin/main` `d25938ed`.
- Deliverable branch: `compute-p5-smoke-percard-20261128`.
- Host: Ada `ucrtasl`, `zli538`, venv `/data1/zli538/paperb_p4_20261127/venv`, Python 3.12.10,
  torch `2.6.0+cu124`, transformers `5.19.0`, CUDA runtime 12.4.
- Card: RTX 6000 Ada `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154` (physical index 2), empty at start and
  end (0 foreign compute processes, 0 MiB). Lease 12:15:18–12:15:44Z, 26 s.

## Result

`r1/scripts/trackp_gpu_smoke.py` on paper `c80f83bc`, model `models/qwen3.5-0.8b-base` (the reviewed P5
model; config `trackp_ada_v1.json` sha256 `bb0c7251…`):

| Check | Value | Pass |
|---|---|---|
| `pass` | true | — |
| Device / capability | `NVIDIA RTX 6000 Ada Generation`, `[8, 9]` | — |
| Kernels bound | `causal_conv1d_fn`, `causal_conv1d_update`, `torch_chunk_gated_delta_rule`, `torch_recurrent_gated_delta_rule` | — |
| bf16 matmul relative error | **0.002875** | yes |
| DeltaNet forward fp32 | argmax agreement 1.0; `fast_vs_ref` 0.02802 ≤ 0.04025 | yes |
| DeltaNet forward bf16 | argmax agreement 0.99511; `fast_vs_ref` 0.27163 ≤ 0.63327 | yes |
| Peak memory | 3,345 MiB | — |

The report is `smoke_report.json` sha256 `dd0944fafef3c3aacd4dc46854c49e414abe25071650021fc5516fadcb2bf8af`;
lease `smoke_lease.jsonl` sha256 `9d5cd32323715e426ba3aa849135c94affb5d0da440d2c8b07dadc9df32bf09a`.
The exact command is in `smoke_command.txt`.

## E0 part

The E0 comparison of the earlier P5 record (`compute/20261127-29`, 25.9 % RPS below the 26 Oct reference)
was superseded by the author's **R1-P4-E0-CRITERION** (`f0e4809a`) and its fresh-run test
`compute/20261128-16`: four fresh runs, accepted at `c22ba021` / review `0bd80f7a`, PASS both slope and
RPS parts. This record does not re-run E0 or re-read the old comparator; it cites that unit for the E0
part and records only the staged smoke and lease.

## Timing

The smoke itself is 26 s wall and 3,345 MiB peak. The P4 timing basis is in the fresh E0 runs: Ada
0.9211/0.9142 GPU-h and TASL-7 0.4747/0.4836 GPU-h (`compute/20261128-16`). The reviewed timing
carry-forward for the phase-1 note remains the next P.4 step; this record makes no timing change.

## Captures

`smoke_report.json`, `smoke_lease.jsonl`, `smoke.log`, `gpu_before.txt`, `gpu_after.txt`,
`smoke_command.txt`; root `SHA256SUMS` binds the set. No signed value, request, config or model byte was
changed; no label, test or evaluation value was read.

## What happens next

One fresh review of this smoke record. On acceptance, the staged smoke and the accepted fresh E0 are both
available for the P.4 phase-1 note's P5 line; the timing disposition is the remaining review item before
the note.

Decided alone: Ada card 2 and its full UUID, the per-card lock and lease-log paths, the fresh capture
directory, and the decision to cite the accepted fresh E0 rather than repeat the superseded comparator.
