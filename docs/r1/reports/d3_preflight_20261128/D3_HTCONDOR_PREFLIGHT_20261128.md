# D.3 single-GPU HTCondor preflight — no startable slot (28 Nov 2026)

Task `compute/20261128-03` (with `compute/20261127-12`) under PLAN **R1-P4-D3-GPU-PREFLIGHT (2)**: one matched ETP
L40S or TOpAS A100, ENGINEERING_ONLY. Base `origin/main` `a98d2eff`. Submit host deepthought.

**Result: no job submitted. The only GPU machine with free A100s advertises `Start = false`; the ETP L40S also
advertises `Start = false`.** Per the card, the exact expressions are reported and nothing was worked around: no
request was edited, no other GPU class was substituted.

## Observations (2026-11-28T00:17Z)

### TOpAS collector `c03-001-140.gridka.de`

`c03-001-175.gridka.de` is the machine the author reported as having free A100s. The pslot has
`TotalGPUs = 8`, `GPUs = 7` (7 free), `State = Unclaimed`, `Activity = Idle`, `GPUs_DeviceName =
"NVIDIA A100-PCIE-40GB"`, `GPUs_DriverVersion = 13.3`, `GPUs_GlobalMemoryMb = 40464`. But:

```
Start = false
Requirements = Start && (WithinResourceLimits)
```

The two child slots on the same machine also carry `Start = false` (`slot1_5` Claimed/Busy, `slot1_16`
Claimed/Busy). The full ad is captured in `c03001175_slot1.ad`.

Other TOpAS GPU machines at the same time:

| Machine | Device | Free GPUs | State | Start |
|---|---|---|---|---|
| `c03-001-167` | A100-PCIE-40GB | 0 of 8 (pslot) | Unclaimed/Idle | undefined (= startable) |
| `c03-001-179` | A100-PCIE-40GB | 0 of 8 (pslot) | Unclaimed/Idle | undefined |
| `c03-001-159` | Tesla V100S-PCIE-32GB | 7 of 56 | Unclaimed/Idle | undefined |

`c03-001-167` and `c03-001-179` have no free GPU on their pslot; `c03-001-159` is a V100S, not the A100/L40S the
row names. `topas_gpu_slots.txt` holds the raw rows.

### ETP collector

```
deepthought2.etp.kit.edu   NVIDIA L40S              1 of 2 free   Unclaimed/Idle   Start = false
deepthought.etp.kit.edu    NVIDIA GeForce GTX TITAN X  2 of 4 free   Unclaimed/Idle   Start = false
```

The ETP L40S on deepthought2 is not startable either. Raw rows in `etp_gpu_slots.txt`.

## What this means

The scheduler still does not match the D.3 preflight request, so the task's fallback applies: **report the exact
expressions; do not work around them.** No job id exists for this attempt because no job was submitted. The
pinned candidate container digest, in-container input read and hashes therefore remain unverified on the batch
route; the D.3 preflight stays open.

**Next check:** re-read `condor_status -pool c03-001-140.gridka.de` for `c03-001-175`; submit only when its
`Start` is true. P.4 stays on the direct Ada route (author, 28 Nov).

## Files

`date_utc.txt`, `c03001175_slot1.ad`, `c03001175_summary.txt`, `topas_gpu_slots.txt`, `etp_gpu_slots.txt`.
`SHA256SUMS` binds them.

Decided alone: no submission and no substitution of a non-named GPU class when `Start` was false, exactly as the
card directs.
