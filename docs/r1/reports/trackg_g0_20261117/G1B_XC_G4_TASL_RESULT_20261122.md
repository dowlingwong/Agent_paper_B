# G.1b cross-host check and G.4 pilot on the TASL pair — STOP (22 November 2026)

**Both are stopped by the same MLGym data-manifest metadata mismatch that stopped `mlgym_fmnist` in G.1b.**
No verdict files were produced; no G.4 server/pilot was started. Authority: `g1b_xc_t1_tasl_20261122.md`
(run_id `g1b-tasl-20261121-b-xc`, paper_commit `ea34b1ab…`, launch checkout `02abb367`) and
`g4_t1_tasl_20261122.md` (paper_commit `02abb367`, launch checkout `9c2979a2..`).

## G.1b cross-host check (XC)

Launch checkout on TASL-7: `02abb367` detached (note/spec shas match: xc spec `2521f7d2…`), harness `c025f89a`;
TASL-2 checkout prepared at `02abb367` but no TASL-2 xc job was started after the STOP.

| host | node | result |
|---|---|---|
| TASL-7 | `mlab_cifar10` | **PASS part**: 10/10 default rows, 0 divergent, no stop; sealed attempt-1 receipt sha256 `0695daf81dc8862e46e4b43f97565d7cbf2ee7677fd1153faa3b55a2d854d103` |
| TASL-7 | `mlgym_cifar10` | **STOP**: data manifest sha `54d3a74d…` vs census `c0ef1168…`, `stop_class infrastructure`; 0/10 rows, not sealed |
| TASL-7 | `mlgym_breakout_minatar` | **not run** (script stopped at mlgym_cifar10) |
| TASL-2 | all three | **not run** (same STOP; no six-job check can pass) |

Cause: identical to fmnist — the four `.npy` file sha256/bytes are identical to the census; only
`source.datasets` differs (`3.6.0` on TASL vs `5.0.1` recorded in the census manifest; the census host env is also
`3.6.0`). The runner compares the whole `data_manifest.json` hash, so it stops. No data was altered/faked.

Consequently no `compare --mode xc` verdict was produced; the three step-1 verdict files do not exist; the second
G.1b note (TASL-7 nodes) and the cross-check remain blocked. Evidence: `G1B_XC_G4_TASL_RESULT_20261122_captures/`
(91 files; SHA256SUMS sha `1cdde91954a50400de94f4da12510a34a5cfe854bc2f22cb7bb9feed27b93e6a`) and host root
`/home/dowling/r1_tracks/t1_tasl/`.

## G.4 pilot

Pre-flight checks (jax312 on TASL-2, TASL-7 llama-server build manifest `a29c667f…`, Tailscale DNS
`tasl-7.tail119748.ts.net`) were already established by the pre-launch crate, but **no server was started and no
pilot job ran**, because the pilot's `mlgym_fmnist`/`mlgym_breakout_minatar` data path (`mlgym_fmnist` is a G.4
node) hits the same MLGym manifest mismatch; a three-node pilot cannot pass. No G.4 GPU-h consumed. Evidence:
none beyond the pre-launch reports.

## Author decision needed

The census MLGym `data_manifest.json` says `datasets: 5.0.1`, while the frozen `torch312` environment and both
TASL hosts have `datasets==3.6.0`; the actual four data arrays are byte-identical. Options: (A) amend the
census/spec manifest metadata (and the comparison rule) to the data-file hashes + the true environment version,
with a reviewed record; or (B) regenerate the census MLGym data under a checked environment so the whole manifest
matches, and re-run U2/rows if that is material. Until then `mlgym_fmnist`, `mlgym_cifar10` G.1b/xc and G.4 are
stopped; arxiv/imdb/houseprice G.1b results are unaffected.
