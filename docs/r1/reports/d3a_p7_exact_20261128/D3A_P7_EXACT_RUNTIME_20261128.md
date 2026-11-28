# D.3a P7 at the frozen runtime — `openml_climate` 6301/6302 on TASL-2 RTX 4090

**Result: STOP at the P7 worker gate.** The exact frozen runtime starts and fits on the 24 GB
RTX 4090 (`-c 32768`, q8_0 K/V, one slot, 21,977 MiB used at load), and all 14 campaigns complete,
but the two-seed engineering smoke now charges **50 worker failures in 276 runs = 18.12 %**, above
the D.3 pre-declaration §10 STOP of **12.99 %**. The published P7 (8,192 context, no explicit q8_0
K/V) gave 33/271 = 12.18 %. The runtime in frozen rev 4 §2 therefore does not reproduce the P7 gate
that the D.3a note would cite. No signed value was changed, no context lowered and no cache type
altered; the run is reported as measured.

- Task: `compute/20261128-15` (priority first), under `compute/20261128-11` item 2 and PLAN
  R1-P4-D3-GPU-PREFLIGHT / R1-D3-PREDECL-R4.
- Base: `origin/main` `5200647086afc1e65dd65fd9e369e265af154935` (the D.3a note-fill commit; the
  runtime binding is explicitly held in that note).
- Deliverable branch: `compute-d3a-p7-exact-20261128` (tip stated in the `coord/compute` report).
- Host: TASL-2, RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver 535.309.01,
  24,564 MiB. Leases `~/r1_locks/gpu0.lock` and `~/r1_locks/cpus-16-31.lock` held for the server's
  life; driver, every worker and the server ran under `taskset -c 16-31`.
- Harness: `9bb416805175149eb87b71f28d77530572aa4bce`, clean (`harness_actual` HEAD, dirty=false).
- Proposer: `gemma4_31b` Q4_K_M, sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`;
  `llama-server` sha256 `646caa007c99a5c9e644dac1c1a6a75f84ed78c5ca08da39a2fb690073d61e5b`.
- Run roots: `/home/dowling/r1_tracks/work/d3p7c_20261128/run-s6301` (run id
  `d3a-p7-exact-20261128-c`) and `run-s6302` (`d3a-p7-exact-20261128-d`). Receipt window
  2026-11-28T08:38:47Z–09:05:41Z; server span 08:38:34Z–09:06:20Z = 1,666 s.

## 1. The exact runtime that ran

The server was started from the captured command line, not from the older 8,192-context script:

```
/home/dowling/r1_tracks/opt/llama.cpp/build/bin/llama-server \
  -m /home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8095 -ngl 999 -c 32768 -np 1 --jinja \
  --chat-template-kwargs {"enable_thinking":false} \
  --cache-type-k q8_0 --cache-type-v q8_0 --no-webui
```

`/props` after readiness: `n_ctx` **32,768**, `total_slots` **1**, build `b11669-620d2225c`, model
file `google_gemma-4-31B-it-Q4_K_M.gguf`. The server loaded in 4.8 s and used **21,977 MiB** of the
24,564 MiB card (21,618 MiB in the compute process), leaving 2,206 MiB free. The exact argv, `/props`,
start/end GPU captures and the server log are in `captures/server2/`.

| Item | Value |
|---|---|
| Context / slots | 32,768 / 1 |
| K/V cache | q8_0 / q8_0 (explicit argv) |
| GGUF / binary | `2959c1b0…` / `646caa00…` |
| Server memory at load | 21,977 MiB used, 2,206 MiB free |
| Server span | 1,666 s ≈ **0.463 GPU-h** |
| CUDA UUID | `GPU-4d623e76-7587-ee15-a633-46f60d220d94` |

The `-ngl 999` model fits; the server does **not** fall back to CPU. The card was empty before the
start (`memory_free` 23,830 MiB, no compute process) and after the end.

## 2. Per-arm and per-seed result

`trials` is the charged worker-run count (success + charged failure). `precheck` counts proposals
rejected before any worker run; `skips` are control-plane skips. The gate column is the per-campaign
completion + finite-success check; the pooled failure-rate check is §3.

| seed | arm | trials | success | worker fail | precheck | skips | keeps | wall s | worker s | LLM calls | campaign |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 6301 | A0 | 20 | 15 | 5 | 1 | 0 | 3 | 127.4 | 22.8 | 21 | complete |
| 6301 | A0R | 20 | 15 | 5 | 0 | 1 | 3 | 143.7 | 24.0 | 21 | complete |
| 6301 | A1 | 20 | 14 | 6 | 1 | 1 | 3 | 134.9 | 22.7 | 22 | complete |
| 6301 | A2 | 20 | 15 | 5 | 0 | 28 | 3 | 275.2 | 22.4 | 48 | complete |
| 6301 | FIXR3 | 18 | 18 | 0 | 0 | 0 | 1 | 50.3 | 21.0 | 7 | complete |
| 6301 | EGATE | 20 | 20 | 0 | 0 | 0 | 1 | 34.6 | 22.2 | 3 | complete |
| 6301 | LADDER | 20 | 19 | 1 | 0 | 0 | 1 | 120.0 | 22.5 | 20 | complete |
| 6302 | A0 | 20 | 12 | 8 | 0 | 0 | 3 | 125.4 | 23.2 | 20 | complete |
| 6302 | A0R | 20 | 14 | 6 | 0 | 2 | 5 | 133.6 | 22.8 | 22 | complete |
| 6302 | A1 | 20 | 12 | 8 | 0 | 0 | 3 | 123.8 | 22.4 | 20 | complete |
| 6302 | A2 | 20 | 14 | 6 | 0 | 2 | 5 | 133.6 | 22.5 | 22 | complete |
| 6302 | FIXR3 | 18 | 18 | 0 | 0 | 0 | 1 | 49.8 | 20.5 | 7 | complete |
| 6302 | EGATE | 20 | 20 | 0 | 0 | 0 | 1 | 36.9 | 24.7 | 3 | complete |
| 6302 | LADDER | 20 | 20 | 0 | 0 | 0 | 1 | 122.8 | 22.9 | 20 | complete |

Total campaign wall **1,611.9 s**, worker time **316.6 s**. The exact runtime was faster than the
published 8,192 run (2,028.7 s wall) and produced a different proposal stream: 34 control-plane skips
against 77, and 50 charged `invalid_config` failures against 33. A2 no longer approached the 80-call
cap in these two seeds (48 and 22 calls), so the difference is not an A2-only effect.

## 3. Worker gate — FAIL

The sweep-2 `gates.worker` shape is used: charged trials, successes, failures, runtime errors,
failures by category, and the pooled charged failure rate against the D.3 pre-declaration §10 limit
of **12.99 %**. Replicate failures count as worker runs and failures in the denominator.

| Item | Value |
|---|---:|
| Charged worker trials | 276 (200 harness + 76 replicate) |
| Successful | 226 |
| Failures | **50** (all `invalid_config`) |
| Failure rate | **50/276 = 18.116 %** (limit 12.99 %) |
| Per seed | 6301 21/135 = 15.56 %; 6302 29/141 = 20.57 % |
| Precheck rejections (uncharged) | 2 |
| Control-plane skips | 34 |
| Admitted runtime errors | 2 (both truncated-mapping `ParserError`, A0R trial-015 and A2 trial-046 on 6301) |
| Unadmitted runtime errors | 0 |
| `gates.worker` | **FAIL** (rate above the declared limit) |

Sensitivity, stated not hidden: on the 200 harness-charged runs alone the rate is **50/200 = 25.00 %**,
also above the limit. Both denominators fail.

**Comparison with the published P7 (same host, model, harness and seeds).** The published run used
`-c 8192` with no explicit q8_0 K/V and recorded 33/271 = 12.18 % (harness-only 33/195 = 16.92 %);
this run at the frozen runtime records 50/276 = 18.12 % (harness-only 25.00 %). The exact runtime
therefore changes the manager's proposal stream enough to move the gate from PASS to FAIL. This is a
property of the measured runtime, not a counting change: `worker_gate.py` is the same corrected
classifier used for the accepted P7 (charged = the worker ran).

## 4. Resource peaks

| Metric | Peak |
|---|---|
| GPU utilisation | 100 % |
| GPU memory used | **21,999 MiB** (2,184 MiB free minimum) |
| Power draw | 392.5 W |
| Temperature | 72 °C |
| GPU samples | 795 (2 s interval) |
| Host RAM used | **14.27 GB** of 67.12 GB total (minimum available 51.96 GB) |
| Scratch (one seed run) | 3.95 MB (6301) / 3.52 MB (6302); OpenML cache 0.12 MB; tree hash `01c8e35a…` |

The host-RAM sampler started at 08:40:20Z, 1 min 33 s after the driver, because the first sampler
used a locale-dependent `free` match; the peak reported here covers the rest of both seeds and is
recorded with that start. The first ~90 s are not sampled. Scratch is the run tree plus the pinned
OpenML cache; this smoke has one instance per arm, so it is **not** a measured 18-instance chunk and
must not be multiplied as if it were one.

At the end of each chunk the recorded "other process" is the run's own `llama-server` (21,618 MiB);
no foreign compute process was on the card at start or end.

## 5. Timing and projection at the exact runtime (engineering only)

Measured proposer-call latency: **202 calls with a latency**, mean **5.107 s**, maximum **11.038 s**;
the largest campaign mean is **5.764 s**. The table uses 18 campaigns × the maximum observed call
count per arm × 5.764 s, under the single-slot `-np 1` serialization assumption. It sets no
scheduler request; it is shown only to record what the exact-runtime sample implies.

| Arm | max calls/campaign | 18-campaign basis (s) | 1.5× request (s) |
|---|---:|---:|---:|
| A0 | 21 | 2,179 | 3,268 |
| A0R | 22 | 2,283 | 3,424 |
| A1 | 22 | 2,283 | 3,424 |
| A2 | 48 | 4,980 | 7,470 |
| FIXR3 | 7 | 726 | 1,089 |
| EGATE | 3 | 311 | 467 |
| LADDER | 20 | 2,075 | 3,113 |

Sum over one node ≈ 14,837 s; seven nodes ≈ **28.85 GPU-h**. Using the observed maximum 11.038 s for
the A0R chunk alone raises it to about **32.91 GPU-h**. The published P7 basis was 38.3/42.5 GPU-h;
the difference comes from the changed call counts, not from a faster card claim. Because the gate
fails, this projection is **not** bound to the D.3a note and is not a replacement for the published
P7 basis.

## 6. Tests

At the base commit with the audit-matching package set and harness `9bb41680`:

```
AR_HARNESS_ROOT=…/harness_9bb_20261127 python -m pytest -q \
  r1/tests/test_d3_smoke_engineering.py r1/tests/test_d3_audit_g6.py
→ 17 passed in 0.47s
```

No repository code changed in this unit. The deliverable's independent review is on
`compute-d3a-p7-exact-20261128-review`.

## 7. Disclosure: one discarded start

A first start at 08:33:15Z used the same exact server and commands but was stopped after A0 and part
of A0R when it was found that the host-RAM and scratch samplers were not running from the first
second. It is **not** the receipt and none of its outputs are used; its status, GPU samples, affinity
probe and the two run logs are kept under `captures/attempt-0-partial/` for transparency. The receipt
is the 08:38:47Z–09:05:41Z run above. No campaign from the discarded start entered the gate.

## 8. What this means

The D.3a authorization draft says P7 is PASS only with the worker gate PASS and asks for the signed
runtime on the selected route to be confirmed before binding. The runtime fits and starts, but its
two-seed gate is **18.12 % > 12.99 %**. Under the signed plan this is a STOP for the P7 item, not a
reason to change the runtime in the record: lowering the context or the cache type is explicitly
forbidden, and re-running to improve a verdict is not allowed.

The runtime choice in frozen rev 4 §2 is the author's. A change to it, or an author decision on how
to read a P7 gate that depends on the runtime, is Level 2 and belongs to the coordinator/author; this
record proposes no change. Until that decision, the D.3a launch binding stays held and no D.3
campaign starts.

## 9. Hashes

| Object | sha256 |
|---|---|
| `manifest.json` | `751a23df324df7fe479a7582be79635073281c2e835d485a594e182942859578` |
| `observed.json` | `7b1900dd4f1ec7d2c692728a86b64bac3b7471aa54541bc5176cd28cc4ea5336` |
| `server2/server_argv.txt` | `9ed9d647a7e2c9ededf14f12a170271577a3f12c2eb5abf8239756bc4f436ab6` |
| `server2/props.json` | `1a8232145d11d8946dcb63a0ab82b7986a535d016c9acafd71b9c6249f613cb7` |
| `worker_gate.json` | `cc1ed95ccdb919080b1685b7970109860f02cdef5670eefd03132ba2f8dc65b1` |
| `p7_summary.json` | `144a09a723df7f2d96e7250025e5f2a240dc822e7e5be453252028f07a9d812d` |
| `host_mem_samples_c.csv` | `e072e98a40a9c1ddaee984c33d0025cd868931b739669146172ab79cc9c6052c` |
| `scratch_samples.csv` | `af79a1422f6bad6ca8be5a25762d18fe60be3fb757e86de1a7e8cd7567f70bcd` |
| OpenML cache tree | `01c8e35a332a05790b1ea90ca31efbd3b019e4090f960b06bcd036ace0bbf290` |
| `captures/SHA256SUMS` | `8fc4906d224dbc2b20db3af248142cefe1f8fbb1fc87da091872b6bc85038e14` (944 entries; all 28 inner sums verify) |
| `SHA256SUMS` (record root) | binds this record and `captures/SHA256SUMS`; see the file |

## 10. Decided alone

The exact server argv and its capture; the fresh work root and run IDs; the whole-job 16–31 CPU set;
the host-RAM and scratch sampler design; the restart after the sampler omission, with the first start
kept as a disclosed non-receipt; and the projection basis. No request, note, seed, signed value,
harness byte or node kit was changed. No label, test or evaluation value was read; no other user's
process was touched.
