# Track S — independent review of the STOP-1 `cache_prompt` diagnostic

**Reviewer:** independent (not the operator; no access to the operator's work in progress).
**Date:** 30 Oct 2026.
**Under review:** worktree `.claude-worktrees/trackS-ops-20261030`, branch `trackS-ops-20261030`,
head `91f30e91` ("Track S STOP-1 diagnostic: cache_prompt=false gives 100 percent identity on both
hosts"). All worktree checks were run in that worktree; the main tree was not touched.
**Runbook of record:** revision 3.3, sha256 `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`
(docs branch `13badb0d`), read with `git show 13badb0d:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`
in this worktree (the file is not on this branch).
**Labels:** the diagnostic is `ENGINEERING_ONLY / DIAGNOSTIC`; it is not a phase.

## 1. Scope

Reviewed as primary evidence: the diagnostic report
[TRACKS_S01_CACHEPROMPT_DIAG_20261030.md](../reports/TRACKS_S01_CACHEPROMPT_DIAG_20261030.md), the STATUS
entry at the top of [STATUS.md](../STATUS.md), the module
[cache_prompt_diag.py](../../../r1/tracks/ops/diag/cache_prompt_diag.py), the runner
[trks-diag](../../../r1/tracks/ops/diag/trks-diag), the launch scripts
[tasl2_diag_cache.sh](../../../r1/tracks/ops/launch/tasl2_diag_cache.sh) /
[tasl7_diag_cache.sh](../../../r1/tracks/ops/launch/tasl7_diag_cache.sh), the raw outputs
`results/r1/tracks/{digits_mlp,tabular_mlp}/s01_diag/cache_prompt.json`, and both hosts directly.

I judged **whether the diagnostic was executed and reported faithfully** and whether the author's
stated trigger ("if `cache_prompt: false` reaches 100 % on both hosts") is correctly established as a
fact of this run. I did **not** judge whether prompt caching is the last word on the S0.1 failure, and I
did **not** re-read or re-apply the Phase 1 STOP rule (per the author's instruction, a STOP rule is
flagged, never re-read, in a report — see §3.5).

## 2. What I ran

Worktree:

```
git rev-parse HEAD; git status --porcelain; git log --oneline -5
git show 13badb0d:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md | sha256sum   # a93fb84b…
git show --stat HEAD; git diff --name-status HEAD^..HEAD; git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests
sha256sum r1/tracks/probes/determinism.py
git show 9bb64ba:r1/tracks/probes/determinism.py | sha256sum                        # 081adb63… (identical)
sha256sum r1/tracks/ops/diag/cache_prompt_diag.py r1/tracks/ops/diag/trks-diag r1/tracks/ops/launch/tasl*_diag_cache.sh
sha256sum results/r1/tracks/*/s01_diag/cache_prompt.json
```

Independent recomputation (Python, read-only, against the raw JSON and nothing else):

- identity per mode **from the per-prompt `contents` arrays** (`len(v)==3 and None not in v and len(set(v))==1`),
  identical/differing counts and indices, cross-checked against `summary.identity_rate`;
- mean/p95 from the per-call `latency_s` list (p95 by the pinned module's nearest-rank rule);
- error lists from `calls[]`, token totals/min/max/mean from `calls[].tokens`;
- the call schedule rebuilt locally with the pinned rule (`random.Random("1|0|0")` over
  `[(i,r) for r in range(3) for i in range(200)]`) and compared with the recorded `calls[].order` /
  `calls[].prompt` / `calls[].repeat`;
- first-occurrence `prompt_n` per prompt in each mode (the cache-warmth check in finding S1).

Hosts (read-only; no server started):

```
ssh portal_zhixu / ssh tasl7:
  git -C $R/work/Agent_paper_B rev-parse HEAD; git -C $R/work/Agent_paper_B status --porcelain
  git -C $R/work/autoresearch_harness rev-parse HEAD; … status --porcelain
  git -C $R/work/Agent_paper_B show 9bb64ba:r1/tracks/probes/determinism.py | sha256sum
  git -C $R/opt/llama.cpp rev-parse HEAD; llama-server --version; sha256sum $R/models/*.gguf
  sha256sum $R/out/<node>/s01_diag/cache_prompt.json
  sha256sum $R/bin/cache_prompt_diag.py $R/bin/trks-diag $R/launch/tasl*_diag_cache.sh
  stat -c "%y %n" (script / launch / output mtimes)
  tmux ls; ls -la ~/r1_locks/; ls -la $R/trks_drill.active; find $R/out -name STOP
  nvidia-smi --query-compute-apps=…; ss -ltnp | grep 1810; flock -n ~/r1_locks/gpu0.lock true
  find /home/dowling -xdev -maxdepth 3 -newermt … ! -path "*/r1_tracks/*"; find /tmp -newermt …
  grep -a "offloaded\|listening" $R/logs/llama_18101.log
```

## 3. Re-verification

### 3.1 Fidelity of the re-use (verified at code level)

The diagnostic imports the pinned module (`from r1.tracks.probes import determinism as D`,
`cache_prompt_diag.py:137`) and calls exactly the functions the pinned serial probe calls:

| pinned element | pinned probe | diagnostic | match |
|---|---|---|---|
| `fixed_prompts(n, node)` | `determinism.py:288` | `cache_prompt_diag.py:139` (`[:args.n]`, as the probe) | yes |
| `chat_payload(prompt, seed, model, temperature=0.2, proposal_schema=…)` | `determinism.py:203` | `cache_prompt_diag.py:140` | yes |
| `schedule(n, repeats, order_seed, url_index, client)` | `determinism.py:205` with `url_index=0, client=0` | `cache_prompt_diag.py:142` — `schedule(200,3,1,0,0)` | yes |
| `identity_rate(contents, repeats)` | `determinism.py:215` (`repeats*clients`, clients=1) | `cache_prompt_diag.py:107` (`repeats`) | yes |
| `latency_stats(latencies)` | `determinism.py:214` | `cache_prompt_diag.py:111` | yes |
| `cpu_census()` | `determinism.py:289,315` | `cache_prompt_diag.py:145,153` | yes |
| `server_props` / `sha256_path` | `determinism.py:221,232` | `cache_prompt_diag.py:164-168` | yes |

The only change to the request is the added field: `payload = dict(payloads[i]); payload["cache_prompt"] = flag`
(`cache_prompt_diag.py:85-86`) — a per-call copy, so the shared payloads are never mutated. The
recording additions (`calls[]`, retained `contents`, `tokens_of`) are instrumentation, not request
changes. `post_full` mirrors the pinned `post` (same URL construction, headers, no retry), and adds the
parsed body so token counts can be stored.

Independent corroboration that the prompt stream was unchanged: the recorded `order_head`
`[[163,1],[7,2],[134,1],[86,0],[0,0]]` is **identical to the S0.1 serial probe's `order_head`** on both
hosts (`results/r1/tracks/*/s01/serial.json`), and my locally rebuilt schedule matches the recorded 600
call positions exactly in both modes and on both hosts. So the prompts, seeds, body, order and client
count are the S0.1 serial ones.

One difference in the other direction (an improvement, not a deviation): the pinned probe drops
`contents` (`determinism.py:313`), so S0.1's 0.930/0.870 cannot be recomputed from its output; the
diagnostic keeps them, and every identity figure below is re-derived from them.

### 3.2 Recomputation from the raw JSON — every reported number reproduces

Computed from `results/r1/tracks/<node>/s01_diag/cache_prompt.json` alone; the report's value is shown
for comparison.

| quantity | digits_mlp recomputed | report | tabular_mlp recomputed | report |
|---|---|---|---|---|
| `false` identity | 1.0000 (200/200) | 1.0000 (200/200) | 1.0000 (200/200) | 1.0000 (200/200) |
| `true` identity | 1.0000 (200/200) | 1.0000 | 0.9900 (198/200) | 0.9900 (198/200) |
| differing prompt indices | none | none | 60, 92 | 60, 92 |
| `false` mean / p95 latency | 0.682794 / 0.714863 s | 0.6828 / 0.7149 | 0.698506 / 0.740193 s | 0.6985 / 0.7402 |
| `true` mean / p95 latency | 0.630916 / 0.669902 s | 0.6309 / 0.6699 | 0.648759 / 0.696252 s | 0.6488 / 0.6963 |
| cost of `false` | +0.051878 s = **+8.22 %** | +0.0519 s (+8.2 %) | +0.049747 s = **+7.67 %** | +0.0497 s (+7.7 %) |
| errors | 0 | 0 | 0 | 0 |
| completion tokens/call, mean | 100.315 / 100.180 | 100.3 / 100.2 | 104.085 / 104.173 | 104.1 / 104.2 |
| `prompt_n` total | 383 781 / 600 | 383 781 / 600 | 387 381 / 4 865 | 387 381 / 4 865 |
| `prompt_n` mean / min / max | 639.6 / 517 / 828 (false); 1.00 / 1 / 1 (true) | same | 645.6 / 523 / 834 (false); 8.11 / 1 / 684 (true) | same |

The per-prompt detail in §2 of the report is exact: prompt 60 repeats are 338, 342, 342 chars (repeat 0
differs), prompt 92 are 375, 375, 329 (repeat 2 differs); in the `false` run prompt 60 is 342×3 and
prompt 92 is 329×3.

sha256 of the two result files (`4ada2f72…3a40`, `4407899844…613f`) matches the report, the committed
files and the **host originals** `$R/out/<node>/s01_diag/cache_prompt.json` on TASL-2 and TASL-7. The
installed `$R/bin/cache_prompt_diag.py` is byte-identical to the committed file (`5012efc4…`), as is
`trks-diag` (`7ab8b5c9…`) and both launch scripts (`0d29c188…`, `58854080…`); their mtimes (04:30–04:34
PDT) precede the outputs (04:47:58 / 04:48:28 PDT), so the committed code was the code in place before
the run.

### 3.3 "The field is honoured" — the argument holds, and is stated within its scope

Verified from the JSON: with `false`, all 600 calls per host fully re-evaluate their prompt (`prompt_n`
600-call totals 383 781 / 387 381; min 517 / 523, so no cache hit anywhere); with `true`, `prompt_n` drops
to 1 on 600/600 digits calls and to a mean of 8.11 (range 1–684) on tabular, with only 8 tabular calls
above 20. That is exactly the report's §2.1 table, and its reading — "almost the whole prompt is served
from the KV cache … the large values being cache misses" — is fair.

A check the report does not make strengthens it further: `usage.prompt_tokens` is **identically
639.635 (digits) and 645.635 (tabular) in both modes** — the same prompts, same byte length, same
requests — while only the *evaluated* count (`timings.prompt_n`) changes. So the field changed caching
behaviour and nothing else in the request. The heading "the server does honour the field (decisive
check)" claims only that, and is not overclaimed: the section's concluding sentence is the modest "the
experiment is not a null test".

### 3.4 The flagged control-vs-original observation — honestly recorded, correctly cautious

- **Accurate.** The `true` control gave 1.000/0.990 against the original S0.1 serial 0.930/0.870; the
  diagnostic ran `trks-servers 1` (port 18101) while the S0.1 serial probe ran with two servers resident.
  I confirmed the second half independently: the 18102 server log on both hosts stops at 03:46 PDT
  (end of Phase 1), while the diagnostic wrote its output at 04:47–04:48 PDT, and the Phase 1 procedure
  and launch scripts start `k = 2` servers before the serial probe. So "only 18101 was used, two were
  resident" is right.
- **Not interpreted.** §3 does not adopt an explanation; it says the runs differ "in at least this
  respect" and that "the server-count difference (or another factor) may matter". It explicitly leaves
  the reading to the coordinating session. STATUS carries the same caveat in the same entry.
- **The causation statement is sound.** "The diagnostic does not by itself establish prompt caching as
  the cause" is correct: the control did not reproduce the failure at all on digits (zero differing
  prompts) and only barely on tabular (2/200 vs 26/200 in S0.1). On the digits host the run contains
  **no true/false contrast whatsoever**, so the entire observed test-vs-control difference rests on two
  tabular prompts. The report gives the counts but does not spell that out; see S1.
- **Does it undermine the author's trigger?** As a *factual condition*, no: "`false` reaches 100 % on
  both hosts" is true, correctly computed, and the test arm is a valid replication of the S0.1 request
  stream under cache-disabled conditions (all 600 calls per host are full re-evaluations, same prompts,
  seeds, order, body). As *evidence that a code change will fix the original S0.1 failure*, the
  diagnostic is much weaker than the headline suggests, because it never reproduced that failure in the
  control. The report says this plainly; I do not find it overstated. If anything it understates the
  incompleteness of its own explanation of *why* the control failed to reproduce — see S1.

### 3.5 Rule discipline — complied

- **No STOP rule re-read.** Neither the report nor STATUS restates, reinterprets or re-applies the Phase 1
  "Done when" rule or any other STOP rule; §4 states only the author's trigger, and §3 explicitly records
  that the operator "has not re-read any STOP rule". The Phase 1 outcome is referred to as a past fact
  (0.930/0.870), not re-decided. Both are consistent with runbook §0.6 ("reports never re-read a STOP
  rule") and the author's instruction.
- **No k set.** Nothing in the report, STATUS, code or host state fixes k; STATUS says so explicitly.
  No later phase exists: both hosts' `$R/out` contain only `inputs/`, `s01/`, `s01_diag/`, `s11/`
  (plus the Phase 0 `smoke/`), and no `s04`.
- **No Phase 3.** No S0.4/tuning/EVIDENCE artifacts, no collector sessions, no k-server layout.
- **No pin change.** Paper `9bb64ba6712668c4bab4a66720cf7f2645e1c672` and harness
  `115df37d2b4581487eb2d911dc4d6a903afcc76a` on both hosts, detached, `git status --porcelain` empty in
  both checkouts; `git show 9bb64ba:r1/tracks/probes/determinism.py` hashes `081adb63…` on both hosts and
  in this worktree; llama.cpp `620d2225…` (`0.7.0-dev`, build 11669) on both; GGUF `509287f7…4d3c` on
  both. The head commit touches only `STATUS.md`, the report, the diag/ops files and the two result
  files; `git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests` is empty. (`r1/tracks/ops/install.sh`
  was extended to install the diagnostic; it is an ops helper, not pinned code.)
- **No next-step implementation.** No harness/collector switch, no new pins, no PLAN row. Matches the
  author's instruction that the operator must not implement the next step.

### 3.6 Safety and state — verified on both hosts

| check | TASL-2 | TASL-7 |
|---|---|---|
| paper / harness HEAD, tracked modifications | `9bb64ba` / `115df37`, clean | same, clean |
| llama.cpp commit / version / GGUF | `620d2225` / 0.7.0-dev / `509287f7…4d3c` | same |
| `trks_llm` session | absent | absent |
| listeners on 18101/18102 | none | none |
| `nvidia-smi --query-compute-apps` | empty | empty |
| `flock -n ~/r1_locks/gpu0.lock true` | succeeds (lease free) | succeeds |
| `trks_watch` | running (since 04:08 PDT) | running (since 04:07 PDT) |
| `$R/trks_drill.active` | absent | absent |
| `~/r1_locks/` | only `gpu0.lock` (no `trackx_*`, no `trackp_*`) | only `gpu0.lock` |
| STOP files under `$R/out` | none | none |

The two TASL-2 `llama-server` processes are Track P's pre-existing dry-run processes on ports 39705 and
60275 (no GPU memory, as recorded in Phase 0); nothing of Track S's is running. One out-of-scope write
exists and is recorded as S5.

## 4. Findings

| id | severity | finding |
|---|---|---|
| S1 | MINOR | The report identifies only the server-count difference as why the control did not reproduce S0.1. Its own data show a second difference: the control ran against a prompt cache pre-populated by the test run. On digits the control yields no contrast at all. |
| S2 | MINOR | STATUS compresses the token evidence as "600 / 4 865 (1–8 per call)", which reads as a per-call range; the observed per-call range is 1–684 on tabular (mean 8.11). The report body is correct. |
| S3 | MINOR | "GET /health → `{"status":"ok"}`" is not evidenced by any retained artifact. |
| S4 | MINOR | The raw JSON carries no run timestamps and no request example/payload hash; the "only added field" claim rests on the committed code plus token counts, not on the file. |
| S5 | MINOR | One write outside the approved work directory is not recorded: `/home/dowling/.claude/.credentials.json` on TASL-2, mtime 04:23:43 PDT. |

No BLOCKING and no MAJOR finding.

**S1 — the control's cache was already warm (MINOR; most consequential of the five).**
Per prompt, the first call of the `true` phase is a cache hit for **200/200** prompts on digits and
**197/200** on tabular (`prompt_n = 1`, or 616/682/617 for the three misses); in the `false` phase
**0/200** first calls are hits (all 600 calls re-evaluate their full prompt). A freshly started server
cannot have those entries: the `false` run populated them, so the control began warm. S0.1's serial probe,
by contrast, was the first client of a freshly started server (cold), so every prompt's first call there
was a full re-evaluation — and a full re-evaluation is exactly where the `true` mode differs from its
otherwise-identical repeats (the two differing tabular prompts are the ones with partial/missed
re-evaluations, `prompt_n` 375). The report says the runs differ "in at least this respect" (server
count) and that "another factor" may matter, so it does not misstate; but the coordinating session should
know that the mismatched cache warmth is a concrete, visible-in-the-data candidate cause of the
non-reproduction, and that a control run alone on a freshly started server (≈7 min on one host) would
settle it — within the diagnostic authorisation, not the code change. Separately, on digits the control's
identity is 1.000 (0 differing), so that host contributes no true/false contrast; the entire contrast is
2 of 200 tabular prompts. The report gives the raw counts but does not draw either point out.

**S2 — STATUS "1–8 per call".** The STATUS bullet reads "…to 600 / 4 865 (1–8 per call) with `true`".
The numbers 1 and 8 are the two per-host means (1.00 and 8.11); the parenthetical can be read as the
observed per-call range, which is 1–684. The report body states it correctly ("1 token per call on digits;
1–684 on tabular"). Suggest "mean 1.0 / 8.1 per call (max 684)" in STATUS.

**S3 — unsupported health claim.** §1 says "both hosts logged … `GET /health` → `{"status":"ok"}`". The
diagnostic never calls `/health` (it calls `/props` and `/chat/completions` only,
`cache_prompt_diag.py:168` and `post_full`), the JSON has no health record, and the server logs contain no
`GET /health` line (they do contain the expected `offloaded 29/29 layers` and `listening on
http://127.0.0.1:18101`). This is presumably a manual `curl`; it should be labelled as such or dropped.
It does not affect any result.

**S4 — provenance gaps in the raw output.** The JSON records no timestamps and no `request_example` (the
pinned probe records one, `determinism.py:309`). Consequently the run's wall-clock timing rests on file
mtimes, and the "only added field" claim cannot be checked from the output file itself — only from the
committed code (whose host copies are byte-identical and predate the output) plus the token-count
evidence in §3.3. Adding `request_example`, start/end timestamps and a script sha256 to the output would
close this cheaply in any future diagnostic.

**S5 — unrecorded out-of-scope write.** TASL-2 `/home/dowling/.claude/.credentials.json` (and its parent
directory) changed at 2026-10-30 04:23:43 PDT, before the diagnostic (04:31–04:48). It is the agent
runtime's own credential state, not something the diagnostic wrote, and TASL-7 shows no equivalent. The
"nothing outside the work directory" claim is therefore not literally true. Record it, or exempt the
agent runtime's own state in the runbook.

## 5. Acceptance checklist

| # | item | result |
|---|---|---|
| 1 | Re-uses the pinned module's `fixed_prompts` / `chat_payload` / `schedule(200,3,1,0,0)` / `identity_rate` / `latency_stats` / `cpu_census` | PASS |
| 2 | The only request change is the added `cache_prompt` field | PASS (code; corroborated by identical `usage.prompt_tokens` across modes) |
| 3 | No pinned file modified (worktree and both hosts) | PASS |
| 4 | Identity recomputable from raw JSON and equal to the report | PASS (exact) |
| 5 | Differing counts/indices, latency, errors, token counts equal to the report | PASS (exact) |
| 6 | Latency-cost percentages correct | PASS (+8.22 %, +7.67 %) |
| 7 | Output sha256s match the files and the host originals | PASS |
| 8 | "The field is honoured" argument sound and not overclaimed | PASS |
| 9 | Control-vs-original discrepancy recorded accurately and without interpretation | PASS (with S1) |
| 10 | "Does not establish prompt caching as the cause" statement sound | PASS |
| 11 | No STOP rule re-read in report or STATUS | PASS |
| 12 | No k set, no Phase 3 started, no pins changed, next step not implemented | PASS |
| 13 | Hosts at the pins with no tracked modifications; GGUF unchanged | PASS |
| 14 | Servers stopped, lease free, no compute apps, watcher running, no drill/Track P marker | PASS |
| 15 | Nothing written outside the approved work directory except as recorded | PASS-with-note (S5) |
| 16 | Raw output self-sufficient as provenance | PARTIAL (S4) |

## 6. Limitations of this review

- The author's ruling (option 2, the trigger sentence, the single-server specification) is relayed
  through STATUS/the report; there is no author artifact in this worktree, so the attribution "as the
  author specified" (one server per host) could not be checked against a primary source. What I could
  check — that one server was in fact used — is confirmed.
- I did not replay requests against a live server (I did not start GPU servers). All numerical checks are
  re-derivations from the stored raw responses plus the host logs; the identity of the prompts with
  S0.1's rests on the shared pinned module, the identical `order_head`, the identical per-call
  `usage.prompt_tokens`, and the committed code — not on a byte comparison of prompt text, which the
  output does not store (S4).
- S0.1's per-prompt contents were never kept (`determinism.py:313`), so the 14/26 differing-prompt counts
  I quote for S0.1 are the complements of its reported rates (200 × (1 − 0.930) and 200 × (1 − 0.870)),
  not independently recomputed responses.
- I did not audit the operator's SSH history or the full `$R/logs` for every command; I checked the
  artifacts the report relies on and the host state it asserts.

## 7. Verdict

The diagnostic is what it says it is: the pinned S0.1 serial request stream, unchanged except for one
added `cache_prompt` field, run once per host with `false` then `true`, with raw responses kept. Every
number in the report and STATUS — identity, differing indices, latency mean/p95 and the cost percentages,
error counts, completion and evaluated token counts, and both file sha256s — reproduces exactly from the
raw JSON, and the JSON on the hosts is byte-identical to the committed copy. The pinned code is untouched
on both hosts, no pin, k, phase or next step was changed, and the host state is clean (servers stopped,
lease free, no compute apps, watcher running, no markers). The control-vs-original discrepancy is
recorded accurately and without interpretation, and the "does not by itself establish causation"
statement is sound; the 100 %-identity trigger is correctly established **as a fact of this run**, though
its evidential force for the original failure is limited, as the report itself says. The five findings are
MINOR: S1 (an incomplete explanation of the control's non-reproduction — the cache was pre-warmed by the
test run, and digits yields no contrast) is worth handing to the coordinating session, and S2–S5 are
wording/provenance/safety-record nits; none changes a number, a conclusion, or the safety state, and none
requires rework of the diagnostic.

REVIEW VERDICT: ACCEPTED
