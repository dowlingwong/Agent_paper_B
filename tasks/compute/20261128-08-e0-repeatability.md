# compute/20261128-08 — P.4 E0 same-code repeatability: one repeat on Ada, one on TASL-7 (R1-P4-E0-REPEATABILITY)

PLAN **R1-P4-E0-REPEATABILITY** (`main` `2e8d089a`). Run one E0 repeat on each host, identical to that host's first same-code run:
- **Ada** (RTX 6000 Ada, `ssh ada_server` as `zli538`): repeat of `p5_20261127_b/e0e`: paper `c80f83bc`, `e0_config_ref.json` (sha256 `9773547d…`), same data
  manifest `b963be2d…`, base model, seed 0, stage final, per-card lease on an empty card.
- **TASL-7** (RTX 4090): repeat of `p5_e0_ref_20261128/e0e`: same paper, `e0_config_ref_tasl7.json` with byte-identical recipe blocks, same data, model, seed.
Fresh run directories (e.g. `p5_e0_rep_20261128_ada`, `..._tasl7`); nothing overwritten. Both can run at once. ENGINEERING_ONLY (DRYRUN, as the first runs).
Report, with the **existing** comparator and tolerances (none changed): Ada repeat vs Ada first, TASL-7 repeat vs TASL-7 first (within-host differences on
width slope, mean slope, RPS), and cross-host (Ada vs TASL-7, both pairs). Also whether either host is bit-identical run to run. GPU-hours and lease
times per run. Record + captures + SHA256SUMS on a branch, fresh review. Do **not** propose or apply a new criterion in the record; the coordinator brings
any criterion change to the author. Priority: now (GPU; runs beside the CPU screening).
