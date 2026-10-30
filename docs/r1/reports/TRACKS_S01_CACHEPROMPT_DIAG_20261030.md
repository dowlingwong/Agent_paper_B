# Track S — STOP-1 diagnostic: does `cache_prompt: false` restore bit-identical repeats?

**Written 30 Oct 2026 by the Track S operator agent; AI-assisted.** Carried out on the **author's ruling
on STOP 1 (30 Oct), option 2: an authorised diagnostic re-run — not a final STOP and not a halt**.
**ENGINEERING_ONLY / DIAGNOSTIC.** It is **not** a phase: it sets no k, produces no pre-declaration input,
and Phase 3 was not started.

Runbook of record: revision 3.3, sha256 `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`
(docs branch `13badb0d`). Code pins unchanged: paper `9bb64ba`, harness `115df37`, llama.cpp `620d2225`
(v0.7.0), GGUF sha256 `509287f7…4d3c`. Hosts TASL-2 (`digits_mlp`) and TASL-7 (`tabular_mlp`).
Report times UTC; raw log lines keep the hosts' local PDT stamps.

## 0. Question and hypothesised cause

- **Question:** S0.1 failed to reach 100 % within-server identity in the serial setting (0.930 on
  `digits_mlp`, 0.870 on `tabular_mlp`). Is the cause llama-server's default prompt caching, i.e. does
  forcing `cache_prompt: false` restore bit-identical repeats?
- **Hypothesis (author's):** llama-server's default prompt caching (`cache_prompt` true) reuses the
  slot's KV prefix from the previous request, so batch boundaries depend on the predecessor and outputs
  are not bit-identical. The harness request body sends no `cache_prompt` field.

## 1. Method

The diagnostic reuses the **pinned** S0.1 probe unchanged (`r1/tracks/probes/determinism.py` at
`9bb64ba`): its fixed prompts (`fixed_prompts`), its per-prompt seeds, the harness `chat_payload` body,
its **serial interleaved schedule** (`schedule`, `order_seed = 1`, `url_index = 0`, `client = 0`), and its
`identity_rate` / `latency_stats` / `cpu_census`. **The only change is one added request field,
`"cache_prompt"`** — `false` for the test run, `true` for the control — with identical prompts, seeds,
body and call order in both. Both modes ran in one invocation, **test first**, on one server per host
(`trks-servers 1`, port 18101, under the lease).

- Script (committed): `r1/tracks/ops/diag/cache_prompt_diag.py`; runner `r1/tracks/ops/diag/trks-diag`;
  launch scripts `r1/tracks/ops/launch/tasl{2,7}_diag_cache.sh`.
- Parameters: `n = 200` prompts, `repeats = 3`, `order_seed = 1`, `temperature 0.2`,
  `proposal_schema manager_proposal/v1`, one serial client.
- **Raw responses are kept** per call: call-order position, prompt index, repeat, latency, content
  sha256 and length, and the server's reported token counts; and per prompt, its per-repeat contents, so
  identity can be re-derived from the file.
- Server: `llama-server … --alias r1-manager --host 127.0.0.1 --port 18101 -ngl 999 -c 8192 --parallel 1
  --verbose`; both hosts logged `offloaded 29/29 layers to GPU` and `GET /health` → `{"status":"ok"}`.
  `GET /props` exposes no `cache_prompt` key, so the server's default could not be read from there.
- Pre-checks (§0.4): `~/r1_locks` held only `gpu0.lock` (no `trackx_…`, no `trackp_…`),
  `$R/trks_drill.active` absent, no compute process, no `trks_llm` session (before starting).

## 2. Results

| | digits_mlp (TASL-2) | tabular_mlp (TASL-7) |
|---|---|---|
| **`cache_prompt: false` identity** | **1.0000** (200/200) | **1.0000** (200/200) |
| `cache_prompt: true` (control) identity | 1.0000 (200/200) | 0.9900 (198/200) |
| latency mean / p95 — false | 0.6828 s / 0.7149 s | 0.6985 s / 0.7402 s |
| latency mean / p95 — true | 0.6309 s / 0.6699 s | 0.6488 s / 0.6963 s |
| **latency cost of `false`** | **+0.0519 s (+8.2 %)** | **+0.0497 s (+7.7 %)** |
| errors | 0 / 0 | 0 / 0 |
| completion tokens per call (mean) | 100.3 / 100.2 | 104.1 / 104.2 |

**`cache_prompt: false` reaches 100 % identity on both hosts.** The control run with `cache_prompt: true`
did not: `tabular_mlp` had 2 of 200 prompts non-identical (indices 60 and 92; prompt 60: repeat 0 differs
from repeats 1–2, lengths 338 vs 342; prompt 92: repeat 2 differs, length 329 vs 375).

### 2.1 The server does honour the field (decisive check)

Tokens **evaluated** (`timings.prompt_n`, summed over the 600 calls per mode):

| host | `cache_prompt: false` | `cache_prompt: true` |
|---|---|---|
| digits_mlp | **383 781** (mean 639.6 / call; min 517, max 828) | **600** (mean 1.00 / call) |
| tabular_mlp | **387 381** (mean 645.6 / call; min 523, max 834) | **4 865** (mean 8.11 / call; min 1, max 684) |

With `false`, the full prompt is re-evaluated on every call (~640 tokens). With `true`, almost the whole
prompt is served from the KV cache (1 token per call on digits; 1–684 on tabular, the large values being
cache misses). So the two runs really did differ in prompt-cache behaviour — the experiment is not a
null test.

### 2.2 Output sha256

| file | sha256 |
|---|---|
| `results/r1/tracks/digits_mlp/s01_diag/cache_prompt.json` | `4ada2f72b17524903a3adac7865918f399cb9017f0ef8435b8ea734c98313a40` |
| `results/r1/tracks/tabular_mlp/s01_diag/cache_prompt.json` | `4407899844d3e2940d5fee3d283875580de460d334c5ae8076031f6910da613f` |

## 3. An observation that must not be read as a conclusion

The control run (`cache_prompt: true`) gave **1.000 / 0.990**, but the original S0.1 serial probe — whose
body carries **no** `cache_prompt` field and is otherwise the same request — gave **0.930 / 0.870** on
the same hosts, same GGUF and same build. The two runs differ in at least this respect: **the diagnostic
ran with one server (`trks-servers 1`) as the author specified, whereas the S0.1 serial probe ran while
two servers were resident (`trks-servers 2`; only 18101 was used).**

Consequence, stated plainly and **not interpreted by the operator**: the diagnostic establishes that
`cache_prompt: false` yields 100 % identity under the single-server configuration, but it does **not**
establish that prompt caching is the cause of the original 0.930/0.870 — the control did not reproduce
that failure. The server-count difference (or another factor) may matter. Whether that matters for the
author's "if false reaches 100 %, do a code change and a full S0.1 re-run" rule is the coordinating
session's call; the operator has not taken it, and per the author's instruction has not re-read any STOP
rule.

## 4. Trigger condition and what the operator did not do

- The author's stated trigger — **"If false reaches 100 % on both hosts"** — **is met** (1.0000 on both).
- The stated next step is therefore **a code change by the coordinating session** (a harness/collector
  switch, review, new pins, a PLAN row) and then a **full S0.1 re-run**. **The operator did not
  implement it** and did not change `9bb64ba` / `115df37`.
- **k was not set. Phase 3 was not started.** No S0.4, tuning or EVIDENCE work exists on either host.

## 5. State after the diagnostic

Servers stopped, GPU lease **released and verified free**, no compute apps, no `trks_llm` session,
`trks_watch` still running on both hosts, drill marker absent, lock directory holding only `gpu0.lock`.
Results copied back under `results/r1/tracks/*/s01_diag/`. Both hosts remain at paper `9bb64ba` and
harness `115df37` with no tracked-file modifications.

## 6. Files

- `docs/r1/reports/TRACKS_S01_CACHEPROMPT_DIAG_20261030.md` (this report)
- `r1/tracks/ops/diag/cache_prompt_diag.py`, `r1/tracks/ops/diag/trks-diag`
- `r1/tracks/ops/launch/tasl{2,7}_diag_cache.sh`
- `results/r1/tracks/{digits_mlp,tabular_mlp}/s01_diag/cache_prompt.json`
