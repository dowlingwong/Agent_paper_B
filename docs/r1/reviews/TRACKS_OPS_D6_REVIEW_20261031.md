# Track S — D6 follow-ups F1/F2: independent post-run review (31 Oct 2026)

**Reviewer:** independent (fresh; not the author or the operator; no access to the operator's reasoning or
work in progress). **Reviewed at** worktree `.claude-worktrees/trackS-ops-20261030`, branch
`trackS-ops-20261030`, head **`715febd1`**; paper `9bb64ba`, harness `115df37`, llama.cpp `620d2225`,
GGUF `509287f7…4d3c`; runbook 3.3 `a93fb84b…`. **I did not start a server, run a GPU job, or execute the
diagnostic.** Host access was read-only (`ssh portal_zhixu`, `ssh tasl7`): `git`, `sha256sum`, `ls`, `stat`,
`ss`, `nvidia-smi`, `ps`, `tmux`, `flock -n … true`, `grep`, `find`; nothing was started, stopped or written.

## 1. Scope

The author's **D6 / R1-TRACKS-S01-FOLLOWUP (31 Oct)** authorised two STOP-1 follow-ups on both hosts — **F1**
(`cache_prompt: true`, freshly started server, no prior call) and **F2** (plain S0.1 body, no `cache_prompt`
field, one resident server) — as a **diagnostic, not a phase**: `k` unset, Phase 3 not started, no pinned-code
change, raw responses kept, every GPU job under `flock`, Track X / Track P priority. This review covers the
operator's deliverable for that decision:

- `docs/r1/reports/TRACKS_D6_FOLLOWUP_20261031.md` and the 31 Oct entry at the top of `docs/r1/STATUS.md`;
- the four raw outputs under `results/r1/tracks/{digits_mlp,tabular_mlp}/s01_diag_f{1,2}/`;
- `r1/tracks/ops/diag/cache_prompt_diag.py` (schema v2), `bin/trks-diag`, and
  `r1/tracks/ops/launch/tasl{2,7}_d6.sh`;
- the pre-use review history `docs/r1/reviews/TRACKS_OPS_D6_PREUSE_REVIEW_20261031.md` (three rounds);
- the host originals under `/home/dowling/r1_tracks/out/<node>/s01_diag_f{1,2}/` and live host state.

I judge whether the diagnostic was **executed, recorded and reported faithfully**, not whether the caching
hypothesis is the last word.

## 2. What I re-verified, and how

### 2.1 Every number in §2 recomputed from the raw JSON

The per-prompt `contents` were read directly; identity is the share of the 200 prompts whose 3 repeats are
non-`None` and identical (`determinism.identity_rate`'s definition), the differing set is the complement,
and latency p95 is the pinned **nearest-rank** statistic (`determinism.latency_stats`, `ceil(0.95·n)`),
not linear interpolation.

```
python3 - <<'PY'
import json, math
def p95(xs):
    xs=sorted(xs); return xs[max(1,math.ceil(0.95*len(xs)))-1]
for p,m in [...four JSONs...]:
    d=json.load(open(p)); r=d['results'][m]; c=r['calls']; ct=r['contents']
    diff=[i for i in range(200) if len(set(ct[str(i)]))!=1]
    first={}
    for x in c: first.setdefault(x['prompt'],x)          # code's definition: chronologically first call
    ...
PY
```

| run | identity | differing prompt indices | mean / p95 (s) | calls | tokens evaluated | first-call hits | first-call `prompt_n` mean | `usage.prompt_tokens` mean |
|---|---|---|---|---|---|---|---|---|
| F1 digits (TASL-2) | **0.9300** (186/200) | 5, 22, 34, 51, 52, 61, 68, 71, 115, 122, 127, 149, 155, 170 | 0.643774 / 0.688881 | 600 | 99 801 | 0/200 | 497.005 | 639.635 |
| F2 digits (TASL-2) | **0.9300** (186/200) | identical set | 0.642765 / 0.689630 | 600 | 99 801 | 0/200 | 497.005 | 639.635 |
| F1 tabular (TASL-7) | **0.8700** (174/200) | 22, 36, 39, 48, 49, 51, 59, 62, 64, 72, 88, 91, 94, 119, 121, 135, 142, 155, 157, 160, 167, 169, 172, 181, 183, 189 | 0.657322 / 0.715065 | 600 | 99 807 | 0/200 | 497.035 | 645.635 |
| F2 tabular (TASL-7) | **0.8700** (174/200) | identical set | 0.657737 / 0.715889 | 600 | 99 807 | 0/200 | 497.035 | 645.635 |
| 30 Oct `false` digits | 1.0000 (200/200) | — | 0.6828 / 0.7149 | 600 | 383 781 | 0/200 | 639.635 | 639.635 |
| 30 Oct `false` tabular | 1.0000 (200/200) | — | 0.6985 / 0.7402 | 600 | 387 381 | 0/200 | 645.635 | 645.635 |
| 30 Oct `true` digits | 1.0000 (200/200) | — | 0.6309 / 0.6699 | 600 | 600 | **200/200** | 1.000 | 639.635 |
| 30 Oct `true` tabular | 0.9900 (198/200) | 60, 92 | 0.6488 / 0.6963 | 600 | 4 865 | **197/200** | 10.560 | 645.635 |
| S0.1 serial digits | 0.93 (aggregate only) | not retained | 0.644596 / 0.691548 | 600 | not retained | not retained | not retained | not retained |
| S0.1 serial tabular | 0.87 (aggregate only) | not retained | 0.658160 / 0.716086 | 600 | not retained | not retained | not retained | not retained |

**The report's §2 table reproduces exactly** (to the four decimals it prints), including the latency, the
token totals, `calls_made`, the first-call statistics, `usage_prompt_tokens_mean`, the `freshness` blocks
(`script_start_epoch == server_start_epoch`, `fresh: true`) and the measured `server` blocks
(`exe …/llama-server`, `cmdline` carrying `--port 18101`, pid equal to the pids in the run logs). The
`30 Oct true` row is confirmed as the warm control: its first `true`-phase call evaluated **1** token for
200/200 prompts on digits and 197/200 on tabular, i.e. the prefix was already cached from the `false` phase.

### 2.2 The central claim: omitting the field equals `cache_prompt: true`

```
python3 - <<'PY'
r1 = json.load(open(.../s01_diag_f1/cache_prompt_true_cold.json))['results']['true']['request_example']
r2 = json.load(open(.../s01_diag_f2/plain_single_absent.json))['results']['absent']['request_example']
assert {k:v for k,v in r1.items() if k!='cache_prompt'} == r2
PY
```

Verified, and stronger than the report claims:

- **Bodies:** F1 keys are `cache_prompt, messages, model, response_format, seed, stream, temperature`; F2 is
  the same dict without `cache_prompt` — exact equality after dropping that key, on both hosts.
- **Schedule:** identical 600-call `(order, prompt, repeat)` sequence, identical `order_head`; the F2 body is
  **byte-identical to the S0.1 serial probe's `request_example`** (same seed 1332422715 for the first
  prompt), so F2 really is the plain S0.1 stream.
- **Tokens:** identical per-call `prompt_n` sequence and identical `tokens_evaluated_total` (99 801 / 99 807).
- **Outputs:** the per-prompt per-repeat `contents` are **identical across F1 and F2 for all 600 calls**, and
  the differing-index sets are identical.

**Verdict on the claim: supported, not overstated.** The behavioural evidence is conclusive: if the absent
field meant `false`, F2 would have returned 1.000 with ~640 evaluated tokens/call (as the 30 Oct `false` run
did); it instead returned 0.930/0.870 with 1 token/call after the first pass, exactly like `true`. The one
sentence that outruns the artifact is the *reason* — "`true` is the server default" is not read from
`server_props` (which records no `cache_prompt`); the equivalence is established behaviourally, which is
what matters. Not a finding, because the equivalence itself is fully evidenced.

### 2.3 The three S1 confound conclusions

- **Server count — no effect.** F2 (one Track S server) gives 0.930/0.870 exactly as S0.1's two-resident
  serial probe. Verified at the aggregate level. The report's extra phrase "**prompt-for-prompt**" is **not
  verifiable**: `results/…/s01/serial.json` retains no per-prompt `contents` and no differing-index list
  (`per_url[*]` has only `latency, errors, identity_rate, clients, identity_rate_per_client,
  cross_client_identity, order_head`). See FND-1.
- **Cache warmth — explains the 30 Oct control.** Verified from the 30 Oct raw file itself: cold `true`
  (F1) = 0.930/0.870; the 30 Oct `true` control = 1.000/0.990 with **200/200** (digits) and **197/200**
  (tabular) *complete* first-call hits and only 600 / 4 865 evaluated tokens. The control was demonstrably
  running against a cache populated by its own `false` phase, so it was not a valid cold control. Strong.
- **Contrast size — resolved.** `false` = 1.000 on both hosts; `true`/default = 0.930/0.870 cold; the
  differing sets are 14 and 26 prompts, i.e. the earlier "2 of 200" was the warm tabular control only
  (prompts 60, 92). Verified. The `false` side rests on the 30 Oct files, which lack the new
  `server`/`freshness` fields; see FND-2 for why that is a caveat, not a defect.

### 2.4 Run conditions and host state

```
ssh portal_zhixu 'sha256sum $R/out/digits_mlp/s01_diag_f{1,2}/*.json; ss -H -ltn "sport = :18101"; \
  nvidia-smi --query-compute-apps=pid; flock -n ~/r1_locks/gpu0.lock true; tmux ls; \
  cd $R/work/Agent_paper_B && git rev-parse HEAD && git status --porcelain'
ssh tasl7 '…same…; sha256sum $R/models/*.gguf'
```

- **Originals match the copies:** all four host sha256 are exactly the report's §6 values
  (`95fb79ac…`, `b5d20832…`, `a08d45ae…`, `f6a19631…`), as are the originals' sizes.
- **Cold start:** 0/200 *complete* first-call hits on all four runs; the very first call of each run
  (order 0) fully re-evaluated its prompt (`prompt_n == prompt_tokens`, 761/761 and 767/767). **However**,
  199/200 remaining "first" calls reused the shared prefix (see FND-3).
- **Own server per invocation:** distinct pids per phase and host (TASL-2 3046137 → 3106561; TASL-7
  1596872 → 1599244), each with its own `lstart`; the log was rotated at 01:21:25Z / 01:27:57Z (TASL-2) and
  01:21:14Z / 01:27:55Z (TASL-7), leaving two ~93.5 MB (TASL-2) / ~95.9 MB (TASL-7) logs of equal size; no
  `trks_llm` session or `llama-server` process remains.
- **Lease asserted, not taken:** `tasl{2,7}_d6.sh:49` runs `flock -n ~/r1_locks/gpu0.lock true` and STOPs if
  it succeeds; `trks-servers` holds the lock with `exec flock -n … bash -c`. No STOP line in the run logs.
- **Server identified:** `tasl{2,7}_d6.sh:52-63` requires exactly one listener on 18101, `exe` ending
  `llama-server`, exactly one `nvidia-smi` compute pid, that pid equal to the listener, and `--port 18101` in
  the cmdline. The JSON `server` blocks record the measured pid/exe/cmdline/start, and the pids match
  `$R/logs/d6_f{1,2}.log` (`server_pid=…`, `D6 f{1,2} DONE`, `f{1,2}_rc=0`).
- **Nothing else disturbed:** TASL-2's two Track P dry-run `llama-server` processes (pids 2945752, 3747685)
  predate the run by ~4.7 days and are still alive; `nvidia-smi` has no compute apps; no
  `trackx_evidence.active` / `trackp_evidence.active` / `$R/trks_drill.active`; `trks_watch` running on both
  hosts; no 18101 listener; lease free.

### 2.5 Rule discipline

```
git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests   # empty
sha256sum r1/tracks/probes/determinism.py                       # 081adb63…
git show 13badb0d:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md | shasum -a 256   # a93fb84b…
```

No pinned code changed; `determinism.py` is `081adb63…` at `9bb64ba`, at HEAD and on both hosts; the runbook
hash is `a93fb84b…`; both hosts are at paper `9bb64ba` / harness `115df37` with clean `git status`; GGUF
`509287f7…4d3c` on both; installed hashes are `c62fdb73…` (diagnostic), `7ab8b5c9…` (`trks-diag`),
`0f3ca947…` / `06424cb1…` (launch scripts), matching the report and the pre-use review's required pre-run
step. The report and STATUS both label the work **ENGINEERING_ONLY / DIAGNOSTIC**, state it is **not a
phase**, `k` unset, Phase 3 not started; no STOP rule is re-read or reinterpreted; nothing was written
outside `$R` (no new `$HOME` files at depth ≤2 since 18:15 local; `.claude/.credentials.json` unchanged in
the run window on either host).

### 2.6 Recommendation (§4)

It is explicitly addressed "for the author; the operator has not acted", states that the operator did not
implement the change, leaves `k` unset and Phase 3 unstarted, and quantifies the cost (≈640 evaluated
tokens/call; ≈6–8 % mean latency). That is a proper operator recommendation — advice, not a decision. The
only defect is the cost range (FND-4).

## 3. Findings

| id | severity | finding | evidence |
|---|---|---|---|
| **FND-1** | MINOR | "**prompt-for-prompt**" reproduction of S0.1 is asserted but not verifiable: the S0.1 raw file keeps no per-prompt contents or differing indices. The aggregate identity does match. | `results/r1/tracks/{digits_mlp,tabular_mlp}/s01/serial.json` → `per_url["http://127.0.0.1:18101/v1"]` has only `latency, errors, identity_rate, clients, identity_rate_per_client, cross_client_identity, order_head`; no `contents`/diff list anywhere. Report §3 and STATUS. |
| **FND-2** | MINOR | "At the same cold state" / "cold on both sides" for the `false` side rests on the 30 Oct file, which has no `server`, `freshness` or `resident_server_count`; its launch script takes an already-running `SERVER_PID`. Cold is defensible for cache-reuse purposes (every call re-evaluated its full prompt; `false` ran first), but server-process freshness is not evidenced and the report does not say so. | 30 Oct JSON keys (no `server`/`freshness`); `mode_order: ["false","true"]`; `tokens_evaluated_total` 383 781 / 387 381 and 0/200 complete hits on `false`; `tasl2_diag_cache.sh:5-6` requires `SERVER_PID`/`SCRIPT_START_EPOCH`. |
| **FND-3** | MINOR | "Every first call re-evaluated its full prompt" is false. Only the order-0 call did; 199/200 first calls partially reused the shared prefix (~22.3 % of digits tokens, ~23.0 % of tabular). "0/200 cache hits" is correct only as *complete* hits (`prompt_n == 1`). | First-call `prompt_n` mean 497.005 / 497.035 vs `usage.prompt_tokens` mean 639.635 / 645.635; full-re-eval count 1/200, partial 199/200 on all four files; order-0 `prompt_n == prompt_tokens` (761/761, 767/767). Report §1 "runs" row. |
| **FND-4** | MINOR | "+6 to +8 %" mixes baselines: the two ratios the report cites are +6.06 % (0.6828/0.6438) and +6.27 % (0.6985/0.6573); 8 % requires the *warm* 30 Oct control (0.6309 / 0.6488 → +8.22 % / +7.67 %). The honest cold-vs-cold cost is ~6 %. | Report §3 "Cost of the determinism setting" and §4.2; recomputed ratios above. |
| **FND-5** | MINOR | The coldness signal is described as "`/proc/<pid>` start" / "process-age check", but `/proc/<pid>` `st_mtime` is the procfs inode timestamp, not the process start; the pre-use review recorded this as n1. It cannot fail for a fresh server, and the coldness conclusion does not depend on it. | `cache_prompt_diag.py:172` (`stat().st_mtime`); `tasl{2,7}_d6.sh:66` (`stat -c %Y`); pre-use review n1; order-0 full re-evaluation and 0/200 complete hits are the independent evidence. |
| **FND-6** | MINOR | The pre-use review file was edited **in the results commit** (`715febd1`), so the ACCEPTED record is not frozen as of its timestamp. The edits are wording/factual corrections to round 3; the verdict and findings are unchanged. | `git show HEAD -- docs/r1/reviews/TRACKS_OPS_D6_PREUSE_REVIEW_20261031.md` (3 hunks: bash-access wording, `5.25→5.26` days / pid 1058558, "three-line window"→"short window"); verdict `ACCEPTED` unchanged. |

No BLOCKING and no MAJOR finding. FND-3 is the most consequential: correct the sentence to "0/200 *complete*
first-call hits; only the order-0 call re-evaluated its full prompt, and later first calls reused the common
prefix (~22–23 % of tokens)". FND-1/FND-2 should be corrected in the report and STATUS (drop
"prompt-for-prompt"; say the 30 Oct `false` side is cold *for cache reuse* and that its server freshness is
not recorded). FND-4 should read "≈+6 % versus the cold default (≈+8 % versus the warm 30 Oct control)".
FND-5 should say "procfs inode timestamp". FND-6 should be noted as a record-keeping lapse.

## 4. Acceptance checklist (D6 rules)

| # | D6 rule | Result |
|---|---|---|
| 1 | Diagnostic, not a phase; `k` unset; Phase 3 not started | **PASS** — labels `DIAGNOSTIC` / `ENGINEERING_ONLY`, `phase_label f1/f2`, `k` unset, Phase 3 unstarted; no phase artifacts. |
| 2 | No pinned-code change | **PASS** — `git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests` empty; `determinism.py` `081adb63…` at both ends and on both hosts. |
| 3 | Run F1 cold control (`true`, freshly started, no prior call, one server) on both hosts | **PASS with note** — own server per invocation, order-0 full re-evaluation, 0/200 complete hits; FND-3 on the "every first call" wording. |
| 4 | Run F2 plain S0.1 serial probe (no `cache_prompt`, one resident server) on both hosts | **PASS** — body byte-identical to the S0.1 probe's `request_example`; one Track S server; 600 calls. |
| 5 | Pinned prompts/seeds/`chat_payload`/schedule (`order_seed 1`, `url_index 0`, `client 0`, n=200, repeats=3) | **PASS** — `D.fixed_prompts`, `D.chat_payload`, `D.schedule(200,3,1,0,0)`; identical `order_head` and first-prompt seed; `usage.prompt_tokens` identical to S0.1. |
| 6 | Keep raw responses | **PASS** — `contents` for every prompt/repeat, `calls[].tokens`, per-call UTC, `server`, `freshness`, `request_example`, `payload_sha256`, `script_sha256`. |
| 7 | Record evaluated tokens vs `usage.prompt_tokens`, first-call hits, resident count, timestamps | **PASS with note** — all present and recomputed; `resident_server_count` is an asserted argument, made effectively measured by the 0-before/1-after GPU-pid gates (pre-use m6). |
| 8 | Every GPU job under `flock` | **PASS** — `trks-servers` holds `exec flock -n`; the script asserts and never takes; release checked in the script (`:87`), lease free now. |
| 9 | Track X / Track P keep priority | **PASS** — markers checked at start; Track P pids untouched since 26 Oct; no compute apps; watcher running. |
| 10 | Pre-use review before first use (three rounds) | **PASS** — rounds recorded at `64a13270`, `adadc4b1`, `5a9197e8`; final `ACCEPTED` committed 02:19:42 +0100, first server start 01:21:14Z (02:21 CET). FND-6 on the post-hoc edit. |
| 11 | Raw outputs copied back and hashed | **PASS** — four sha256 match the host originals exactly; §6 table correct. |
| 12 | Report/STATUS faithful; recommendation advisory; cost stated | **PASS with notes** — all numbers reproduce; §4 is advice; FND-1/FND-2/FND-3/FND-4 are wording corrections. |
| 13 | Host state safe and clean | **PASS** — both hosts at the pins, clean; servers stopped; lease free; no compute apps; no 18101 listener; `trks_watch` running; no markers; no out-of-scope writes found. |

## 5. What I could not verify

- **The 30 Oct `false` run's server-process freshness.** The file has no `server`/`freshness` block and its
  launch script takes an already-running `SERVER_PID`. I can verify it ran first (`mode_order`) and that
  every one of its 600 calls re-evaluated its full prompt (0 complete hits; 383 781 / 387 381 evaluated
  tokens), which makes it cold **for cache reuse** — the respect in which it matters — but not that the
  server had just started.
- **S0.1's per-prompt differing set**, hence the "prompt-for-prompt" wording (FND-1).
- **The exact HTTP bodies on the wire**, beyond the retained `request_example` (which is the same dict the
  calls are built from); no raw request capture exists.
- **"Nothing written outside the work directory" in full**, only for `$HOME` at depth ≤2 since 18:15 local
  and the credentials file; a system-wide scan was not attempted.
- **`cache_prompt`'s documented default** as a server property; the artifact establishes the behavioural
  equivalence, not the default declaration.
- The runbook file itself is not on this branch; I verified its `a93fb84b…` hash from the docs branch object
  `13badb0d` (`git show 13badb0d:…`), which is what the STATUS records.

## 6. Verdict

The diagnostic was executed and recorded faithfully: every number in §2 reproduces from the raw JSON, the
four host originals are byte-identical, F1 and F2 are genuinely the same setting (identical bodies modulo
the `cache_prompt` key, identical schedule, identical token sequence and identical outputs), the warm 30 Oct
control is explained by its own 200/200 and 197/200 complete cache hits, and the state/rules are clean
(`k` unset, Phase 3 unstarted, pins and GGUF intact, lease free, servers stopped, no markers). The
"omitting the field equals `cache_prompt: true`" claim and all three S1 confound conclusions hold. The six
MINOR findings are precision and record-keeping corrections — the false "every first call re-evaluated its
full prompt" gloss, the unverifiable "prompt-for-prompt" wording, the unrecorded freshness of the 30 Oct
`false` side, the mixed-baseline "+6 to +8 %", the `/proc/<pid>` mtime mislabel, and the post-hoc edit of
the pre-use review — none of which changes a result, a conclusion or the recommendation. The recommendation
is proper advice to the author and states the cost of the setting.

REVIEW VERDICT: ACCEPTED
