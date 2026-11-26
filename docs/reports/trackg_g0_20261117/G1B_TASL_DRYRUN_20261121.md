# G.1b TASL ENGINEERING dry-runs — result (21 November 2026)

Authority: `R1-T1-HOST-TASL`, `R1-G1B-EDITS`, `R1-G1B-TIMEOUT`, `R1-T1-TASL-ENV`; plan `T1_TASL_PLAN.md` §6.
**ENGINEERING_ONLY; no EVIDENCE, no signed G.1b note, no noise-floor row.** Harness pin
`c025f89aeafc2199bf3487b4bcaa16678273c702`; spec `g1b_tasl_spec.json` sha
`2f0bdd70399c7ec24a9f91de1e00e96fba4d8682e666ff51352d09ea5e3aeadb`; wrapper `sweep2/t1_tasl/dry_run_node.py`.

## Design

One **default part** (10 rows = default + repeat) per host was run via the pinned `run_node_job` inside
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` with `AR_TEST_CGROUP_PARENT`,
`CUDA_VISIBLE_DEVICES=""`, `taskset -c 0-7` and the node log; the wrapper restricts `g1b_lib.PARTS` to `default`
and merges a **partial** record (`dry_run_partial:true`), then `g1b_tasl.py seal` is run. This exercises lease,
scope, preflight (host/affinity/GPU UUID/ptrace/cgroup/harness/env), the pinned engine and seal; it does **not**
run the 460-run node and is not a D21 row. No attempt is left open; both are sealed.

## Results

| host | node | runs | median wall | max wall | 4090/Ada ratio | stop | seal |
|---|---|---|---|---|---|---|---|
| TASL-2 | `mlab_ogbn_arxiv` | 10/10 successful (0 divergent) | 3.893 s | 20.122 s | 0.6889 | none | `g1b_tasl_seal_receipt/1`, job record `e260cc4c…`, sealed UTC 10:37:26Z |
| TASL-7 | `mlgym_breakout_minatar` | 10/10 successful (0 divergent) | 36.246 s | 36.246 s | 0.5918 | none | receipt, job record `49ede5c3…`, sealed UTC 10:40:06Z |

- TASL-2: host `TASL-2`, uid 1008, kernel 6.8.0-149; GPU `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver
  535.309.01; affinity [0..7]; foreign checks before job/before default/after default `[]`; cgroup scope and lease
  were acquired by the pinned runner (no pre-held lock); no timeout.
- TASL-7: host `TASL-7`, uid 1011; GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, driver 580.178.04; affinity
  [0..7]; foreign checks `[]`; no timeout. **This is also the M1 end-to-end proof:** the pinned engine ran the
  `mlgym_breakout_minatar` default part under `jax312` in the sandbox with `XLA_FLAGS=--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2`
  (spec `hosts.TASL-7.extra_env`), GPU JIT/compilation succeeded (no ptxas error), 10/10 rows.
- Both sealed attempts are in `.../G1B_TASL_DRYRUN_20261121_captures/TASL-{2,7}/sealed_g1b/.../attempt-1/` with
  `SEAL_RECEIPT.json` and SHA256SUMS; raw run directories and logs are beside them. Capture bundle: 155 files,
  SHA256SUMS sha256 **`4fb0f9c332c7350ab9fdb114b93d65dd248e19a0f6b0c53e4795ec3303f0eab9`** (recompute recorded below), no evidence/noise labels.

## What this does and does not establish

- Established: the pinned runner + wrapper start under the delegated scope, acquire the exclusive host lease,
  perform the preflight (host/UUID/driver/affinity/ptrace/cgroup/harness/env), launch the pinned engine per part,
  write a 10-row record, pass the seal verification and copy to the sealed root; TASL-7's jax312/XLA path works
  end-to-end; no timeout/no foreign process; GPUs left idle.
- Not established / open: a full 460-run node, D21, EVIDENCE, the TASL-7→TASL-2 **crosscheck of default parts**
  required by `R1-T1-TASL-ENV` (no `crosscheck` job in the pinned code; B1 of the pre-launch review), the full
  §6.3 ratio measurement, and the signed G.1b note. **EVIDENCE G.1b remains blocked on B1 + the signed note.**
- The partial records are explicitly labelled `dry_run_partial:true`; they must never be assembled/sealed as a
  G.1b row. The sealed copies are for the runner check only.
