# Autoresearch isolated-GPU condition-7 decision memo (19 November 2026)

**Status: decision memo only; no GPU/U2 run, no code change; ENGINEERING.** This memo records the two
remaining blockers for the Track G G.0 U2 objective after six isolated nodes passed; it asks the author to
choose the autoresearch path and to supply the House Prices input.

## A. Autoresearch `mlgym_breakout`-style U2 cannot start under the accepted isolation core

Ada host-check/fix result: condition 6 PASS (`effective:true`), **condition 7 (CUDA IPC across user/PID
namespace) BLOCKED** on driver 545.23.08 / torch 2.6.0+cu124. Real GPU smoke: 32,768,000 tokens / 500 steps
(77.6 s) then `RuntimeError: CUDA error: invalid resource handle` at `ar_isolated.cuda_open`; controls show
CUDA IPC works between ordinary processes but fails whenever the consumer is in a new user namespace (and
also for the PID-namespace shapes). The accepted isolation-fix review C3 therefore says: no autoresearch
GPU run until (i) a logits-transfer design decision is recorded and (ii) `cuda_open`'s missing
`torch.cuda.init()` is fixed in the **same reviewed change**. This is a code/authority decision, not a
measurement; all six other isolated nodes are done.

## Options

| option | what it means | cost / risk | notes |
|---|---|---|---|
| **A (recommended for a fully isolated census)** | Remove CUDA IPC from the worker result path: the worker returns logits/answers through the existing socket/CPU buffer (or copies device tensors to CPU before the channel), parent computes the metric; add `torch.cuda.init()` to `cuda_open` if any helper remains. | New reviewed harness/kit change (`ar_isolated.py`/`ar_parent.py`/worker or node-level), kit pins + `frozen_pin_sha256` update, re-run the autoresearch isolated smoke, then U2. Performance penalty for the logits transfer is measured in the U2 row. | Preserves `effective:true`, waivers {}, exceptions `["shared_dev_shm"]` only if still needed; keeps the isolation guarantee. |
| **B** | Documented non-PID-namespace GPU mode with a recorded `isolation_waiver` (e.g. worker shares the parent's namespaces but remains a separate process); fix `cuda_open` init. | Needs an author waiver because U2 requires `effective:true`/no waivers; record would carry `effective:false` and the waiver, so the census row must be labelled differently (or excluded from the isolated-run claim). | Faster but weakens the claimed isolation for the RL/agent threat model; not recommended for a label-adjacent node. |
| **C** | Defer autoresearch U2; census reports the six isolated nodes and lists autoresearch as blocked. | No new code; U2 objective not fully met for this suite. | Acceptable only if the author decides the full per-node U2 set is not required now. |

For A/B the minimal code fix also includes adding `torch.cuda.init()` in `ar_isolated.cuda_open` (the
latent segfault without it was reproduced); this must be part of the same reviewed change per C3. Any change
needs a fresh independent code review, updated kit pins (and the kit-update review's C2/C3 conditions), then
exactly one isolated autoresearch smoke, then the U2 unit/review.

## B. House Prices

`~/r1_inputs/house-prices/train.csv` is still absent on Ada. Per `R1-TRACKG-PORT-DECISIONS (2)` the node must
use that user-provided Kaggle file via `--from-file`; MLGym's copy is refused. When the file appears, the
HousePrice U2 unit follows the same one-node unit → independent review → one smoke → result review path
(CPU/no-GPU per the port report).

## What is complete

D2/Unit B (TASL-7, accepted), SFT trial (TASL-2, engineering PASS), six isolated U2 rows
(mlab_cifar10/imdb/ogbn_arxiv, mlgym_cifar10/fmnist/breakout_minatar; units/result reviews accepted,
committed, census updated). Only A/B (autoresearch) and the House Prices input remain.
