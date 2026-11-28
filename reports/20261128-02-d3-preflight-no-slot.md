# compute/20261128-03 — D.3 HTCondor preflight: still no startable A100/L40S

**Result: not submitted. `c03-001-175` (7 free A100) advertises `Start = false`; the ETP L40S on deepthought2 also
advertises `Start = false`. Exact expressions captured; nothing worked around.** No job id exists for this attempt.

- Task: `compute/20261128-03` (with `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2), ENGINEERING_ONLY.
- Branch: `compute-d3-preflight-20261128` @ `db8eb526bf1ccdc99fc26dc47c52539d10593620` (base `a98d2eff`).
- Host: deepthought submit host; TOpAS collector `c03-001-140.gridka.de`.

| Machine | Device | Free GPUs | Start |
|---|---|---:|---|
| `c03-001-175` | A100-PCIE-40GB | 7 of 8 | **false** (`Requirements = Start && (WithinResourceLimits)`) |
| `c03-001-167` | A100-PCIE-40GB | 0 of 8 (pslot) | undefined (startable) |
| `c03-001-179` | A100-PCIE-40GB | 0 of 8 (pslot) | undefined (startable) |
| `c03-001-159` | V100S-PCIE-32GB | 7 of 56 | undefined (not the named A100/L40S class) |
| `deepthought2` (ETP) | L40S | 1 of 2 | **false** |

- Capture record: `docs/r1/reports/d3_preflight_20261128/D3_HTCONDOR_PREFLIGHT_20261128.md`, sha256
  `b55734e1b83eec6917a078b2bbd1944d755f1d1790ce996449f058c66cf94a72`; full ad `c03001175_slot1.ad`;
  `SHA256SUMS` binds the five captures.
- Container digest, in-container input read and hashes remain unverified on the batch route because no job matched.
- Next check: re-read `condor_status -pool c03-001-140.gridka.de` for `c03-001-175`; submit only when `Start` is
  true. P.4 stays on the direct Ada route (author, 28 Nov).
