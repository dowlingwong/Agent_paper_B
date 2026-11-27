# compute/20261127-13 — Ada P.4 probe preparation as `zli538` (R1-P4-D3-GPU-PREFLIGHT (1))

Owner: compute. PLAN **R1-P4-D3-GPU-PREFLIGHT** (`42af62c6`). The author decided (27 Nov, this session): **Ada runs under `zli538`, and the
name may appear in public records.** Your venv record (`compute-ada-p4-venv-20261127` @ `a1d0cf74`, review R2 ACCEPTED) merges
with this task.

Prepare the probe with the reviewed direct launcher on one RTX 6000 Ada: `zli538` as the launch account; fill
`r1/scripts/configs/trackp_ada_v1.json` from your venv record (paths under `/data1/zli538/paperb_p4_20261127/`), with the Python
3.12.10 vs 3.12.15 difference stated; environment and lease checks; then the synthetic-label probe under R1-P4-TESTPLAN-DECISIONS, with
each base's peak GPU memory and timing, the host configuration and the probe charge. Push the host-config fill as its own reviewed unit
(tier E) before the probe. An empty card first; a shared card only if its free memory fits (R1-CARD-SHARE). The phase-1 note gates any
evidence training.
