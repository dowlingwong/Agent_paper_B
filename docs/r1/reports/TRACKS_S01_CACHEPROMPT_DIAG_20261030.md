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
- **Provenance gaps in the raw file (review S4).** The output JSON records no run timestamps and no
  `request_example`/payload hash (the pinned probe records a `request_example`). So the "only added field"
  claim is checkable from the committed code plus the token evidence (§2.1), not from the output file, and
  the run's wall-clock timing rests on file mtimes and the session logs. Any future diagnostic should add
  `request_example`, start/end timestamps and a script sha256.
- Server: `llama-server … --alias r1-manager --host 127.0.0.1 --port 18101 -ngl 999 -c 8192 --parallel 1
  --verbose`; both hosts logged `offloaded 29/29 layers to GPU`. A **manual** `curl -s …/health` returned
  `{"status":"ok"}` before the run (recorded here as a live observation; the diagnostic itself does not
  call `/health` and no artifact retains it — review S3). `GET /props` exposes no `cache_prompt` key, so
  the server's default could not be read from there.
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

A stronger check (suggested by the reviewer): **`usage.prompt_tokens` is identical across the two modes**
(mean 639.635 on digits, 645.635 on tabular), so the prompts and the request body were unchanged and only
the number of *evaluated* tokens fell. That is what distinguishes the two modes.

### 2.2 Output sha256

| file | sha256 |
|---|---|
| `results/r1/tracks/digits_mlp/s01_diag/cache_prompt.json` | `4ada2f72b17524903a3adac7865918f399cb9017f0ef8435b8ea734c98313a40` |
| `results/r1/tracks/tabular_mlp/s01_diag/cache_prompt.json` | `4407899844d3e2940d5fee3d283875580de460d334c5ae8076031f6910da613f` |

## 3. An observation that must not be read as a conclusion

The control run (`cache_prompt: true`) gave **1.000 / 0.990**, but the original S0.1 serial probe — whose
body carries **no** `cache_prompt` field and is otherwise the same request — gave **0.930 / 0.870** on
the same hosts, same GGUF and same build. The data show **three** differences between the two, not one:

1. **Server count.** The diagnostic ran with one server (`trks-servers 1`, as the author specified);
   S0.1's serial probe ran while two servers were resident (`trks-servers 2`; only 18101 was used).
2. **Cache warmth (review S1; visible in this run's own data).** The control ran *after* the test run, so
   its cache was already populated: per prompt, the first `true`-phase call was a cache hit for **200/200**
   prompts on digits and **197/200** on tabular (`prompt_n = 1`, or 616/682/617 for the three misses),
   whereas in the `false` phase **0/200** first calls hit. S0.1's serial probe was the first client of a
   freshly started server, i.e. **cold**, so every prompt's first call there was a full re-evaluation.
3. **No contrast on digits.** On `digits_mlp` the control is 1.000 with zero differing prompts, so that
   host contributes **no** true/false contrast at all; the entire contrast in this diagnostic is **2 of
   200 `tabular_mlp` prompts**.

Consequence, stated plainly and **not interpreted by the operator**: the diagnostic establishes that
`cache_prompt: false` yields 100 % identity under the single-server configuration — the author's trigger
condition is met as a **fact of this run** — but it does **not** establish that prompt caching is the cause
of the original 0.930/0.870, because neither mode reproduced that failure. Two cheap follow-ups would
settle it and both are **outside what the operator was authorised to run**, so neither was run:

- a **control-only run on a freshly started (cold) server** (~7 min on one host) — this isolates cache
  warmth from the true/false comparison;
- a **single-server repeat of the plain S0.1 serial probe** (no `cache_prompt` field) — this isolates the
  server-count difference.

Whether either is needed before the coordinating session's code change is its call; the operator has
taken no reading of any STOP rule.

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

**One out-of-scope write observed and recorded (review S5).** On TASL-2,
`/home/dowling/.claude/.credentials.json` (and its parent) has mtime 04:23:43 PDT. It is a Claude Code
credentials cache; **no Track S command writes it** (the operator's TASL-2 commands are `ssh`, `git`,
`sha256sum`, `python`, `tmux`, `curl`, `scp`, `nvidia-smi`, `flock`). The most plausible writer is the
long-running interactive `claude` session in tmux `12` on TASL-2, which predates Phase 0 and was left
untouched. The operator did not open the file and does not attribute it with certainty; it is flagged for
the author. TASL-7 is clean.

## 6. Files

- `docs/r1/reports/TRACKS_S01_CACHEPROMPT_DIAG_20261030.md` (this report)
- `r1/tracks/ops/diag/cache_prompt_diag.py`, `r1/tracks/ops/diag/trks-diag`
- `r1/tracks/ops/launch/tasl{2,7}_diag_cache.sh`
- `results/r1/tracks/{digits_mlp,tabular_mlp}/s01_diag/cache_prompt.json`

## 7. Review record

**Round 1** (`docs/r1/reviews/TRACKS_OPS_S01DIAG_REVIEW_20261030.md`, fresh independent reviewer):
**ACCEPTED** — 0 BLOCKING, 0 MAJOR, **5 MINOR** (S1–S5). The reviewer re-read the committed diagnostic
against the pinned probe, recomputed every reported number from the raw JSON (identity, differing indices,
latencies, token counts), confirmed the output sha256s against the hosts, confirmed the installed scripts
are byte-identical to the committed code and predate the outputs, verified that `usage.prompt_tokens` is
identical across modes (so the prompts/body were unchanged), and confirmed the hosts' state, pins and that
no k was set and no later phase started.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| S1 | MINOR | The report blamed the control's non-reproduction only on the server count; the control's cache was pre-warmed by the test run, and on digits the control is already 1.000 so the whole contrast is 2/200 tabular prompts | **Fixed** — §3 now lists all three differences (server count, cache warmth with the 200/200 vs 0/200 hit counts, and no digits contrast) and names the two cheap follow-ups the operator was not authorised to run |
| S2 | MINOR | STATUS's "1–8 per call" reads as a per-call range; the actual range is 1–684 (mean 8.11) | **Fixed** — STATUS now says "mean 1.0 / 8.1 per call (max 684)"; the report body was already right |
| S3 | MINOR | "`GET /health` → `{"status":"ok"}`" had no retained artifact | **Fixed** — §1 now labels it a manual `curl` observation, notes the diagnostic does not call `/health`, and records that no artifact retains it |
| S4 | MINOR | The raw JSON has no timestamps and no `request_example`/payload hash | **Recorded** — §1 states the gap and what the "only added field" claim rests on; future diagnostics should add `request_example`, start/end times and a script sha256 |
| S5 | MINOR | An unrecorded out-of-scope write: TASL-2 `/home/dowling/.claude/.credentials.json` | **Recorded** — §5 states the mtime, that no Track S command writes it, the most plausible (interactive `claude` tmux `12`) writer, and that it is flagged for the author; the file was not opened |

The reviewer also noted it could not verify the author's own ruling text (it is relayed, with no author
artifact in the repo) and did not replay requests live; neither affects the reported numbers.
