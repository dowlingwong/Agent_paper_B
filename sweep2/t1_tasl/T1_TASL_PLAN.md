# T1 on the TASL pair: G.1b and G.4 as direct host runs (ENGINEERING_ONLY)

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026. Authority: R1-T1-HOST-TASL (branch
`author-decisions-20261121` `e5e452a0`, reaching `main`), R1-TRACKG-G3-EARLY, R1-TRACKG-AR-U2-TASL2, R1-G1B-CAP,
R1-HARNESS-ISOLATION. Replaces the HTCondor plans of `sweep2/g1b/` and `sweep2/g4/` for the T1 table; those stay as
they are (reviewed, unused). Nothing here runs without an author-signed note on `main` and both keys.

## 1. What runs where

| Piece | Host | GPU | Code |
|---|---|---|---|
| G.1b noise floors, 7 nodes | TASL-2: `mlab_imdb`, `mlgym_fmnist`, `mlab_ogbn_arxiv`, `mlgym_houseprice` (CPU, cpus 8–15); TASL-7: `mlgym_breakout_minatar`, `mlgym_cifar10`, `mlab_cifar10` | one RTX 4090 per host, by full UUID | `g1b_tasl.py`, `g1b_tasl_node.sh`, `g1b_tasl_spec.json` |
| G.4 pilot worker, 3 nodes | TASL-2 | TASL-2's 4090 | `g4_tasl.py run-node`, `g4_tasl_spec.json` |
| G.4 proposer `llama-server` | TASL-7, Tailscale address | TASL-7's 4090 (held for the server's life) | `g4_tasl.py serve` |
| R1-BX-D14 recompute | anywhere | — | `g4_tasl.py dates`, `g4_tasl_dates_params.json` |
| G.5 projection table | anywhere | — | `g5_projection_tasl.py` |

Order: G.1b on both hosts (TASL-7's G.1b nodes finish first) → the proposer server on TASL-7 → the G.4 pilot on
TASL-2 → dates. The lease (`~/r1_locks/gpu0.lock`, exclusive non-blocking `flock`) enforces it: a G.1b job on TASL-7
and the server cannot overlap; a busy lease is a STOP, not a wait.

**Harness pin** `af480809` (branch `mac-trackg-t1-tasl-20261121`, from the G.1b/G.4 pin `b5747066` via `68438477`):
`noise_floor.py` and `pilot_g4.py` take `--gpu-uuid` (a full UUID, checked against `nvidia-smi -L`, with
`CUDA_VISIBLE_DEVICES` empty and no scheduler variable), and `noise_floor.py` accepts CPU-only chunks
(`device: cpu`: no GPU, no GPU variable). Nothing else in the measurement path changes.

## 2. The isolated census runner, as reused

Each G.1b node job is started by `g1b_tasl_node.sh`, which wraps the census pattern:
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`, `AR_TEST_CGROUP_PARENT` = the scope,
`CUDA_VISIBLE_DEVICES=""`, `taskset -c <cpus>`. Inside, `g1b_tasl.py run-node` checks, before any run: host name,
non-root uid, the GPU by UUID and model (RTX 4090), no foreign compute process on it, the lease, Yama
`ptrace_scope ≥ 1`, the scope's `memory.max` = 8 GiB and `memory.swap.max` = 0, the harness checkout at `af480809`
and clean, the environment's `uv pip freeze` equal to the census freeze (torch312 `d2e70fe4…`, jax312 `80a455c6…`),
Python 3.12.16, then the node's own `setup_command` and (in the engine) the data manifest against the census value.
Every run goes through `WorkingCopyRunner`; a record that is not `effective: true` with empty waivers and exceptions
is refused (the engine's gate). The foreign-process check is repeated before and after every part.

## 3. G.1b

- **Runs per node.** `(n_edits + 1) × 92`. Every node declares **4** edits, so **460** runs per node, not the 552 of
  the queue (552 needs a fifth declared edit per node). R1-G1B-EDITS decides (drafted with options).
- **Timeout.** 3 × the declared basis (R1-G1B-TIMEOUT): the census B1 baseline time, or the slowest executed census
  record of the node (the spec defaults to the latter, the draft row's recommendation). Under the baseline basis
  `mlab_ogbn_arxiv`'s E4 (21.8 s on Ada) would exceed 3 × 5.651 s = 16.95 s, so the job would STOP on that node.
- **Timing STOP.** The census times are RTX 6000 Ada; on the 4090 they are an estimate. Any run that reaches the
  declared timeout is a STOP (`stop_class: timing`), not a divergent row. Each part records the 4090/Ada ratio of its
  baseline runs.
- **Projection** (estimate ratio 1.0; sensitivity 1.5): 28.3 GPU-h (41.6 at 1.5) for the six GPU nodes, plus
  `mlgym_houseprice` on 8 CPU cores (0.9 h). Per host: TASL-2 15.0 h, TASL-7 14.2 h of GPU wall. Cap R1-G1B-CAP
  100 GPU-h: within at both ratios.
- **Outputs.** Per node `<runs_root>/<run_id>/<node>/` with `out/`, `job_record.json` (`g1b_tasl_job_record/1`),
  `out.tar`, `SHA256SUMS`, and the wrapper log `<node>.node.log`. `seal` copies them to the host's sealed root (no
  overwrite, no symlink component) with a receipt binding the record and the log. `assemble` joins the sealed node
  directories of both hosts (each checked against its receipt, the run id, the spec sha256, the assigned host, the
  4090, the harness pin, and no infrastructure or timing STOP); `summarise` applies the D21 rule
  (`g1b_lib.summarise`, the reviewed H200 logic).

## 4. G.4

- **Proposer** (`serve`, TASL-7): under TASL-7's lease, the binary and the GGUF by sha256 (`2959c1b0…`), the build
  from `--version`, then `llama-server -m <gguf> --alias gemma4_31b -c 32768 -ngl 999 -np 1 --jinja
  --chat-template-kwargs {"enable_thinking":false} --cache-type-k q8_0 --cache-type-v q8_0 --no-webui --host
  <tailscale address> --port <port>`; `server_record.json` (argv, shas, build, GPU, pid, start) and, on exit,
  `server_end.json` (rc, signal, record and log shas).
- **Worker** (`run-node`, TASL-2): the host checks of §2, the copied `server_record.json` checked against the spec,
  `/health` and `/props` (context 32,768, 1 slot, the expected build, the GGUF file name) before and after (equal),
  a 20-request latency probe before and after, then `pilot_g4 run --gpu-uuid`. Recorded: the server URL, build and
  settings (from the server record and `/props`), per-call latency (median, p95, max, total over every manager call),
  the probes, `cache_prompt: false` on every call (else STOP).
- **Nodes.** `mlab_cifar10`, `mlgym_fmnist`, and `mlgym_breakout_minatar` until `autoresearch_fixedtokens`' U2 passes
  on TASL-2 (R1-TRACKG-AR-U2-TASL2). Breakout needs the jax312 environment **on TASL-2** (G.1b runs it on TASL-7).
- **Timing.** The pilot's timeout is 3 × the same basis as G.1b; a pilot run median above the basis is a timing STOP.
- **Projection.** 11.1 GPU-h (both cards over 5.5 h of span); pilot cap 20.
- **Dates.** `g4_tasl.py dates` = `g4_lib.recompute_dates` with **one** worker slot (TASL-7 serves the proposer for
  G.5), seven nodes (`mlgym_houseprice` joins under R1-TRACKG-G3-EARLY), no queue days, the ratio relabelled 4090 over
  Ada. Pre-pilot: labels done 4 Dec, B.7 7 Dec (1 day slack) at ran share 0.6 and 60 s per call; 9 Dec at share 0.8
  or 120 s per call. The 4090's per-call LLM time for a 31B Q4 model is the main unknown.

## 5. Operator steps (experiment agent)

1. Host checks on TASL-2 (and TASL-7, since G.1b runs workers there): the harness-isolation host checks of the census
   (READY 60 §3) at `af480809`; record the report path and sha256 in `hosts.<h>.isolation_host_check`.
2. Fill the TODO fields of `g1b_tasl_spec.json` (host names, GPU UUIDs, the Kaggle `train.csv` path on TASL-2) and
   `g4_tasl_spec.json` (TASL-7's Tailscale address and port, `llama-server` binary sha256 and build, the GGUF in place);
   install jax312 on TASL-2 from its freeze; check out the harness at `af480809`.
3. The author signs `docs/r1/authorizations/g1b_t1_tasl_<date>.md` (template `g1b_tasl_authorization.template.md`)
   and `g4_t1_tasl_<date>.md`; the rows R1-G1B-EDITS, R1-G1B-TIMEOUT and R1-T1-TASL-ENV are on `main`.
4. G.1b: per node, on its host, `G1B_TASL_ENABLE_REAL=1 g1b_tasl_node.sh <spec> <node> <note> --enable`; then `seal`.
   Then `assemble` and `summarise`.
5. G.4: on TASL-7 `G4_TASL_ENABLE_REAL=1 python g4_tasl.py serve <spec> --note <note> --enable`; copy
   `server_record.json` to TASL-2; per node on TASL-2, inside a `systemd-run` scope as in `g1b_tasl_node.sh`,
   `python g4_tasl.py run-node <spec> --node <n> --server-record <copy> --note <note> --enable`; stop the server;
   `seal` with `--server-end` and `--server-log`; `dates`.

## 6. Needs a host test

1. The delegated scope on both hosts (`systemd-run --user --scope -p Delegate=yes` with `MemoryMax=8G`,
   `MemorySwapMax=0`, `cgroup.kill`), and the isolation probes passing inside it.
2. `nvidia-smi -L` UUIDs on both hosts; `--query-compute-apps` shows no resident process (no display server on the
   card).
3. The 4090/Ada ratio on each node's baseline (first part), against the declared timeout.
4. `mlgym_houseprice` on 8 CPU cores beside a GPU node on TASL-2, without slowing it past its timeout.
5. jax312 on TASL-2 from the census freeze (`uv pip freeze` equal).
6. `llama-server` on TASL-7 with `-ngl 999 -np 1` and context 32,768 in 24 GB with q8_0 KV (full offload of the
   19.6 GB GGUF), and `/props` fields as the worker checks them on that build.
7. Tailscale: reachability from TASL-2, latency, and a server bound to the Tailscale address only.
8. Per-call LLM time on the 4090, which sets the dates.

## 7. STOPs

Every check of §2 and §4; a busy lease; a foreign compute process before or after a part; the node deadline; a
timeout on the 4090 (timing); fixed-seed non-determinism at the default seeds (node; D21 makes the node fail and the
author decides); zero diff liveness or a context overflow in the pilot (node); `/props` changing during the pilot;
the projection above the cap. A STOPped job keeps its outputs and is never resumed; a new attempt needs a new run id.

## 8. Author decisions

- **R1-G1B-EDITS** — 460 (four declared edits) or 552 (a fifth edit per node, new edits reviewed).
- **R1-G1B-TIMEOUT** — census baseline × 3 or slowest census record × 3.
- **R1-T1-TASL-ENV** — the host/environment row in place of the image row.
- **G.5** — re-targeted draft (`docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` rev 6, `approved: false`)
  adds G5-TASL-GPUH (which card's hours count) and G5-SLOT (one worker slot).
