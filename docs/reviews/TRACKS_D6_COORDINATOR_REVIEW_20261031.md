# Track S D6: coordinator independent read-only check

Date: 2026-10-31. Scope: Git object `9953a62c`, reachable from the locally recorded `origin/trackS-ops-20261030` ref. This record does not assert a fresh remote-head check. No server, diagnostic, GPU job, or other experiment was run; no project file was modified.

## Source and method

The source is `docs/r1/reports/TRACKS_D6_FOLLOWUP_20261031.md`, the independent review `docs/r1/reviews/TRACKS_OPS_D6_REVIEW_20261031.md`, and the six committed JSON files under `results/r1/tracks/{digits_mlp,tabular_mlp}/{s01_diag,s01_diag_f1,s01_diag_f2}/`. The Git objects were read using `git show`. For each mode, identity was recomputed as the number of 200 prompt entries with three identical contents; evaluated tokens were summed from the 600 `calls[].tokens.prompt_n` entries. The F1 and F2 `contents` dictionaries and per-call `prompt_n` sequences were compared directly.

## Recomputed raw results

| Host / node | Mode | Calls | Identical prompts / 200 | Evaluated prompt tokens |
|---|---|---:|---:|---:|
| TASL-2 / digits_mlp | F1 true, cold | 600 | 186 (0.930) | 99,801 |
| TASL-2 / digits_mlp | F2 absent, one server | 600 | 186 (0.930) | 99,801 |
| TASL-2 / digits_mlp | 30 Oct false | 600 | 200 (1.000) | 383,781 |
| TASL-7 / tabular_mlp | F1 true, cold | 600 | 174 (0.870) | 99,807 |
| TASL-7 / tabular_mlp | F2 absent, one server | 600 | 174 (0.870) | 99,807 |
| TASL-7 / tabular_mlp | 30 Oct false | 600 | 200 (1.000) | 387,381 |

On each host F1 and F2 had identical per-prompt, per-repeat contents across all 600 calls and identical per-call `prompt_n` sequences. Differing-prompt indices were digits: 5, 22, 34, 51, 52, 61, 68, 71, 115, 122, 127, 149, 155, 170; tabular: 22, 36, 39, 48, 49, 51, 59, 62, 64, 72, 88, 91, 94, 119, 121, 135, 142, 155, 157, 160, 167, 169, 172, 181, 183, 189.

The earlier independent review reports mean/p95 latency respectively as F1 0.643774/0.688881 s and false 0.6828/0.7149 s on digits, and F1 0.657322/0.715065 s and false 0.6985/0.7402 s on tabular. The D6 report gives false versus cold F1 mean-latency increases of +6.06% and +6.27%. False evaluates approximately 639.6 and 645.6 prompt tokens per call, respectively; these are totals per call, not increases of 640 tokens. F1 averages approximately 166 evaluated tokens per call. These latency figures are cited from the retained report and review, not independently recalculated in this check.

## Interpretation and limits

- In these runs, absence of `cache_prompt` and explicit `true` produced the same recorded contents and token-evaluation sequence. This is behavioral evidence for the tested build and schedule; it does not establish that whole response JSON files are byte-identical or independently verify a documented server default. The retained review states that exact HTTP bodies on the wire were not captured.
- The original S0.1 serial aggregate was 0.930/0.870 with two resident servers; F2 reproduced these aggregate rates with one resident server. Thus two resident servers are not necessary to observe this failure in the tested setting. S0.1 did not retain per-prompt contents, so exact per-prompt reproduction and a general claim that server count has no effect cannot be checked from it.
- In F1 there were 0/200 complete first-call hits per host, but only order 0 evaluated a complete prompt; the other first calls reused a shared prefix. The review describes the `/proc/<pid>` inode timestamp test as a one-sided freshness heuristic. The 30 Oct `false` files do not contain `server` or `freshness` fields; all 600 calls evaluated their full prompts, but the artifacts do not establish that the server process was freshly started.
- The true/default versus false contrast and cache-token evidence support a cache-setting attribution for these probes. They do not independently prove the proposed internal KV-cache/batch-boundary mechanism, universal reproducibility with false, or behavior across other models, servers, or every historical B.1 call.

Runbook `13badb0d:docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`, §2 S0.1, requires within-host identity of 100% in the chosen setting, else STOP. D6 is a diagnostic, not a full S0.1 pass. This review does not change the S0.1 determination, set `k`, start Phase 3, authorize any run or code change, or establish scientific readiness. The author's D3/D5/D6 decisions are recorded separately in the supplied attachment; this independent data check does not alter them.
