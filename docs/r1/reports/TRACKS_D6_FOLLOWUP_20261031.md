# Track S — D6 follow-ups F1 (cold control) and F2 (plain single-server repeat)

**Written 31 Oct 2026 by the Track S operator agent; AI-assisted.** Carried out under the author's
decision **D6 / R1-TRACKS-S01-FOLLOWUP (31 Oct)**: run both STOP-1 follow-ups, on both hosts.
**ENGINEERING_ONLY / DIAGNOSTIC.** Not a phase: **`k` is unset and Phase 3 was not started**; no pinned
code changed (paper `9bb64ba`, harness `115df37`, llama.cpp `620d2225`, GGUF `509287f7…4d3c`).

Runbook of record revision 3.3 (`a93fb84b…`). Hosts: TASL-2 (`digits_mlp`), TASL-7 (`tabular_mlp`).
Report times UTC; raw log lines keep the hosts' local PDT stamps.

## 0. Question

The 30 Oct diagnostic showed `cache_prompt: false` → 1.0000 identity on both hosts, but its `true` control
(1.000 / 0.990) did **not** reproduce S0.1's failure (0.930 / 0.870), so three confounds remained
(review S1): the **server count** (diagnostic 1, S0.1 2), the **cache warmth** (the control ran after the
test run had filled the cache), and the **contrast size**. D6 was designed to isolate them:

- **F1 — cold control:** `cache_prompt: true` on a **freshly started** server, no prior call.
- **F2 — plain repeat:** the plain S0.1 serial probe, **no `cache_prompt` field**, one resident server.

Both: same pinned `fixed_prompts`, per-prompt seeds, `chat_payload` body, and serial interleaved schedule
(`order_seed 1`, `url_index 0`, `client 0`), `n = 200`, `repeats = 3`; `identity_rate` / `latency_stats` /
`cpu_census` imported unchanged from `r1/tracks/probes/determinism.py` at `9bb64ba`.

## 1. How it was run

| Item | Value |
|---|---|
| code | `r1/tracks/ops/diag/cache_prompt_diag.py` (schema v2) via `bin/trks-diag`; launch scripts `r1/tracks/ops/launch/tasl{2,7}_d6.sh` |
| installed hashes (both hosts) | `cache_prompt_diag.py` `c62fdb73…`, `trks-diag` `7ab8b5c9…`, `tasl2_d6.sh` `0f3ca947…`, `tasl7_d6.sh` `06424cb1…` |
| per-invocation server | each script rotates the log, starts its **own** server via `bin/trks-servers 1` (which holds `flock ~/r1_locks/gpu0.lock`), stops it at the end; the lease is **asserted held, never taken** |
| server identification | listener on port 18101 via `ss` → pid → `/proc/<pid>/exe` must be `llama-server` → pid must equal the single `nvidia-smi` compute pid → cmdline must carry `--port 18101` |
| coldness | process-age check (`/proc/<pid>` start ≥ script start) plus zero-first-call-hit evidence; this build does **not** log request paths, so log counting was abandoned (pre-use review B2) |
| pre-use review | three rounds before first use: NOT ACCEPTED (B1/M1–M3), NOT ACCEPTED (B2/N1), **ACCEPTED** (`reviews/TRACKS_OPS_D6_PREUSE_REVIEW_20261031.md`) |
| runs | `f1` then `f2` on each host, one server at a time; all four exited **rc=0**, `D6 f1/f2 DONE` |
| first calls | **0 / 200 cache hits on every run** (every first call re-evaluated its full prompt) — the servers were genuinely cold |

## 2. Results

Identity is the share of the 200 prompts whose 3 repeats returned identical content.

| configuration | servers | cache_prompt | digits_mlp (TASL-2) | tabular_mlp (TASL-7) |
|---|---|---|---|---|
| **S0.1 serial** (30 Oct) | 2 resident | field absent | **0.930** (186/200) | **0.870** (174/200) |
| **F1 cold control** (31 Oct) | 1 | `true` | **0.930** (186/200) | **0.870** (174/200) |
| **F2 plain repeat** (31 Oct) | 1 | field absent | **0.930** (186/200) | **0.870** (174/200) |
| 30 Oct diagnostic, test | 1 | `false` | 1.000 (200/200) | 1.000 (200/200) |
| 30 Oct diagnostic, control | 1 | `true` (cache warm) | 1.000 (200/200) | 0.990 (198/200) |

Latency (mean / p95, s) and tokens:

| run | digits_mlp | tabular_mlp |
|---|---|---|
| F1 (`true`, cold) | 0.6438 / 0.6889; evaluated 99 801 (≈166/call, first-call mean 497) | 0.6573 / 0.7151; evaluated 99 807 |
| F2 (absent, cold) | 0.6428 / 0.6896; evaluated 99 801 | 0.6577 / 0.7159; evaluated 99 807 |
| 30 Oct `false` | 0.6828 / 0.7149; evaluated 383 781 (≈640/call) | 0.6985 / 0.7402; evaluated 387 381 |

`usage.prompt_tokens` is the same in every mode (639.635 digits, 645.635 tabular), so the prompts and the
request body were unchanged throughout; only the number of *evaluated* tokens moved.

### 2.1 F1 and F2 are the same setting

The two runs are identical in outcome, not merely similar:

- same identity (0.9300 / 0.8700) and **the identical set of differing prompt indices**
  (digits: 5, 22, 34, 51, 52, 61, 68, 71, 115, 122, 127, 149, 155, 170; tabular: 26 prompts);
- identical `tokens_evaluated_total` (99 801 / 99 807) and identical first-call statistics;
- the request bodies differ **only** by the presence of the `cache_prompt` key
  (F1 keys: `cache_prompt, messages, model, response_format, seed, stream, temperature`;
  F2 keys: the same without `cache_prompt`).

**So omitting the field is indistinguishable from sending `cache_prompt: true`: `true` is the server
default, and the harness body (which sends no such field) therefore runs in the cached mode.**

## 3. Which of the S1 differences the data isolates

| S1 difference | Verdict | Evidence |
|---|---|---|
| **Server count** | **isolated — no effect** | F2 ran with **one** server and gave exactly S0.1's two-server numbers (0.930 / 0.870), prompt-for-prompt. |
| **Cache warmth** | **isolated — explains the 30 Oct control** | Cold `true` (F1) = 0.930 / 0.870; the same setting with a **warm** cache (30 Oct control) = 1.000 / 0.990. Warmth raises apparent identity, so the 30 Oct control was not a valid control. |
| **Contrast size** | **resolved** | The true contrast is `false` vs `true`/default at the same cold state: **1.000 vs 0.930** (digits) and **1.000 vs 0.870** (tabular) — 14 and 26 of 200 prompts differ. The earlier "2 of 200" was an artefact of the warm control. |

**Conclusion (facts, not a decision):** with the server count, the cache state and the request body held
fixed, `cache_prompt: false` yields **100 % identity on both hosts** while `cache_prompt: true` — the
server default, and what the harness body currently gets — yields 0.930 / 0.870. The 30 Oct finding
therefore stands on a clean comparison, and the author's D6 trigger condition is met with the confounds
removed.

Cost of the determinism setting: `false` re-evaluates the full prompt each call (≈640 tokens/call) and was
measured at **+6 to +8 %** mean latency versus the cached mode (0.6828 vs 0.6438 s on digits; 0.6985 vs
0.6573 s on tabular).

## 4. Recommendation (for the author; the operator has not acted)

1. **Accept the diagnosis**: `cache_prompt` is the cause of the S0.1 non-identity, and the harness request
   body must set it explicitly.
2. Proceed with the **code change** the author already described — a harness/collector switch declaring
   `cache_prompt: false`, independent review, **new pins**, a PLAN row — and then a **full S0.1 re-run**
   under the new pins. The operator did not implement it.
3. Note for that re-run: expect ≈6–8 % higher per-call latency and ≈640 evaluated prompt tokens per call;
   the Phase 1 projection's `L` will rise accordingly.
4. `k` remains unset; Phase 3 stays unstarted until S0.1 passes under the new pins.

## 5. State

Servers stopped on both hosts by their own scripts; **lease free**, no GPU compute process, no listener on
18101, no `trks_llm` session, watcher running, drill/priority markers absent. Both hosts remain at paper
`9bb64ba` / harness `115df37` with clean tracked state. Outputs copied back; `$WORK` untouched.

## 6. Files and hashes

| file | sha256 |
|---|---|
| `results/r1/tracks/digits_mlp/s01_diag_f1/cache_prompt_true_cold.json` | `95fb79acc7af41bd8edfc4587cfbaca6ae5832da041c7185a3e6bb61af209b36` |
| `results/r1/tracks/digits_mlp/s01_diag_f2/plain_single_absent.json` | `b5d2083242ab8f6e4f97358853aa82e4669cd3b09cbd5c63b947c7986806139c` |
| `results/r1/tracks/tabular_mlp/s01_diag_f1/cache_prompt_true_cold.json` | `a08d45aea509749f3e06b9eb115dff60764eae92265f19efbaf90f83f1ffefc8` |
| `results/r1/tracks/tabular_mlp/s01_diag_f2/plain_single_absent.json` | `f6a196310e317b586f6688941e7b81ce5d100004cbef89972305ec3d2bd1428b` |

Each raw file keeps every call (order, prompt, repeat, UTC, latency, content sha256/length, token counts),
the per-prompt per-repeat contents, the measured `server` block, `freshness`, `phase_label`,
`script_sha256` and per-mode `payload_sha256`.

## 7. Review record

_To be completed by the independent post-run reviewer._
