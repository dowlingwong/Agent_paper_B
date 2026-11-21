# G.1b on the TASL pair — pre-launch report (21 November 2026, ENGINEERING_ONLY)

Authority: `R1-T1-HOST-TASL`, `R1-G1B-EDITS` (460 runs/node), `R1-G1B-TIMEOUT` (`census_slowest_x3`),
`R1-T1-TASL-ENV`, `R1-G1B-CAP`, `R1-HARNESS-ISOLATION`; plan `sweep2/t1_tasl/T1_TASL_PLAN.md`; harness
`c025f89aeafc2199bf3487b4bcaa16678273c702` (branch `mac-trackg-t1-tasl-20261121`). No EVIDENCE launch; no
author-signed G.1b note is used or assumed.

## Authorizing rows and scope

- `R1-G1B-EDITS` / `R1-G1B-TIMEOUT` / `R1-T1-TASL-ENV` are on main `d47d1008`; `G1b` spec authorities now name
  them.
- Hosts: TASL-2 `TASL-2` / RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94`; TASL-7 `TASL-7` / RTX 4090
  `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`. Driver TASL-2 535.309.01, TASL-7 580.178.04.
- G.1b nodes: TASL-2 `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_fmnist` (GPU) and `mlgym_houseprice` (CPU cpus
  8-15); TASL-7 `mlgym_breakout_minatar`, `mlgym_cifar10`, `mlab_cifar10` (GPU). 460 runs/node, 4 declared edits.
- Paper commit in both specs: `d47d1008509f9730cd8728b68a2cc560ce81e0e0` (main baseline). A launch commit must be
  the branch commit once these specs/reports are committed; this pre-launch engineering run uses the specs as
  committed here.

## Host checks at the harness pin (bindable from main)

Both hosts were re-checked at **c025f89a** (the G.1b pin) and PASS all seven `HARNESS_ISOLATION_20261117.md` §3
items, no waivers; CUDA IPC remains untested (§5.5 open) and is not used.

- TASL-2 binding: `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md` sha
  **`681011b2…`**; original report sha `83636c03…`.
- TASL-7 binding: `docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md` sha
  **`09945c15…`**; original report sha `2b703226…`.
Both bindings contain exactly `host_check_host: TASL-2|TASL-7`, `host_check_harness_commit: c025f89a…`,
`host_check_items: 1-7 PASS`, `host_check_verdict: PASS`; spec fields point at them and carry the shas.

## Environments (uv, from the census freezes)

- uv 0.13.6; `uv python install 3.12.16`; envs `/home/dowling/r1_tracks/t1_tasl/envs/{torch312,jax312}` on both
  hosts, Python 3.12.16, `uv venv --python 3.12.16` + `uv pip sync` from `sweep2/g1b/env` freezes
  `d2e70fe4…`/`80a455c6…`.
- TASL-2: torch312 byte-equal, torch 2.6.0+cu124 CUDA ok; jax312 68-line set equal, jax 0.4.35/jaxlib 0.4.34 CUDA
  backend gpu; sandboxed jax smoke for Breakout env passes effective:true.
- TASL-7: torch312 byte-equal; jax312 sorted-equal (uv's `opt-einsum`/`optax` order only), jax GPU works.
- P1: TASL-7's jax312 needs `XLA_FLAGS=--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2` (no ptxas in freeze; TASL-7
  has versioned CUDA 12.2, no default symlink). The spec now sets this in `hosts.TASL-7.extra_env`; the runner passes
  `XLA_*` through the sandbox and the node's worker appends it. **This is a disclosed environment-level necessity,
  not a waiver of the isolation gate.**
- Harness at `/home/dowling/r1_tracks/t1_tasl/harness` on both hosts: detached c025f89a, clean; isolation tests
  at pin 27 passed/1 root-only skip.

## §6 host checks (G.1b plan)

| item | TASL-2 | TASL-7 |
|---|---|---|
| delegated scope 8G/swap0/cgroup.kill | PASS | PASS |
| GPU UUID/no resident compute | PASS `GPU-4d623e76…` | PASS `GPU-ab72fb4a…` |
| ptrace_scope/non-root/harness clean | PASS | PASS |
| env freezes (torch312/jax312) | PASS (jax set-equal) | PASS (jax sorted-equal) |
| isolation sandboxed smoke at pin | PASS effective:true | PASS effective:true |
| GPU-in-sandbox smoke | PASS | PASS (jax GPU smoke too) |
| houseprice CPU 8–15 beside GPU node | PASS synthetic 20 s/20 s, CPU 12/12 s | n/a (node on TASL-2) |
| 4090/Ada ratio first part | DEFERRED to job (plan §6.3) | DEFERRED to job |
| disk / cleanup | 354.6 GiB / clean | 507.2 GiB / clean |

## Spec TODO fields filled

- G.1b: host names/UUIDs, isolation binding records+shas, authorities, extra env
  `AR_HOUSEPRICE_TRAIN_CSV=/home/dowling/r1_inputs/house-prices/train.csv` (author Kaggle file copied byte-identically
  to TASL-2, sha `1e18addf…929d41`, 460,676 B), TASL-7 `XLA_FLAGS`. `validate --launch` passes.
- G.4: worker TASL-2 fields, proposer TASL-7 fields, `tailscale_address` = `tasl-7.tail119748.ts.net`
  (resolves `.51` on TASL-7 for bind and `.50` on TASL-2 for the client; the only viable pair), `server_url` =
  `http://tasl-7.tail119748.ts.net:8095`, bin-dir manifest **`a29c667f…`** (23 entries; binary `b70f4882…`, build
  0.7.0-dev build1 620d222), `XLA_FLAGS` not needed on worker; `validate --launch` passes.
- P2/P3: G.4's literal `.51` server_url is replaced by the shared-node DNS name; the server binds TASL-7's own
  resolution `.51` only and the TASL-2 client resolves `.50` (verified with a short `llama-server` health/props
  bind test; no G.4 run). CUDA IPC still untested and not used.

## Dry-run plan and limits

- ENGINEERING dry-runs only: one node **default part** per host (TASL-2 `mlab_ogbn_arxiv`, TASL-7
  `mlgym_breakout_minatar`), via `sweep2/t1_tasl/dry_run_node.py` around the pinned `run_node_job` inside
  `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` with `AR_TEST_CGROUP_PARENT`,
  `CUDA_VISIBLE_DEVICES=""`, `taskset`, and then `g1b_tasl.py seal` on the resulting attempt. The wrapper runs only
  `default` (10 rows: default + repeat) and merges a partial record; it is never used for a G.1b row. No signed note,
  no `launch`, no EVIDENCE. It exercises lease, delegated scope, preflight (host/affinity/GPU/ptrace/cgroup/harness/
  env), the pinned engine's timeout flag and seal. **The TASL-7 breakout run is also the M1 end-to-end jax312 +
  XLA_FLAGS sandbox proof; the TASL-2 CPU cpus 8-15 houseprice path is deliberately not in this one-part dry-run.**
- A node STOP or timeout in a dry-run is reported, not retried; no attempt is left unclosed.

## Open precondition for EVIDENCE (not fixed here)

`R1-T1-TASL-ENV` requires the TASL-7-measured G.1b nodes to rerun their **default parts on TASL-2** with identical
metrics (or be re-measured on TASL-2). The reviewed `g1b_tasl.py` has no `crosscheck` job and the spec has no
TASL-2 jax312 env entry. This pre-launch package therefore does **not** authorize EVIDENCE: a reviewed crosscheck job
(or an author PLAN amendment) is required first; B1 in the pre-launch review records this. The ENGINEERING dry-runs
below are unaffected.
- Launch-commit sequence: this report/specs are committed on the publication branch, the branch commit becomes
  `paper.commit` in both specs, then the signed note binds the spec sha256; the current `d47d1008` paper field is the
  base commit only.
