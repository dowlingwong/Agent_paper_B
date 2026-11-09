# Track S — independent review of the S0.1 re-run on TASL-2 (`digits_mlp`), STOP 1

**Reviewer.** Fresh independent reviewer (DSH teammate `track-s-reviewer`). I did not see the operator's
work in progress and I did not take its report, STATUS entry or commit messages as evidence. I re-read the
authority documents, re-derived every number from the copied-back JSONs, and re-verified the pins, the
launch script, the logs and the host state directly on TASL-2 (read-only). I did not start/stop anything,
did not write on either host, did not touch TASL-7 and did not run any Track S phase.

**Artifacts under review.**
- Operator worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackS-ops-20261030`,
  branch `trackS-ops-20261030`, head **`72dccc7017fac746df1870f89a46b3aa5816e055`** (clean at review start).
- Commits **`87381a6abf2296f14015124c420fe93468cf9387`** (launch script
  `r1/tracks/ops/launch/tasl2_s01_rerun_20261109.sh`, committed `2026-11-09T00:59:04+01:00` =
  `2026-11-08T23:59:04Z`) and **`72dccc701`** (evidence + report + STATUS, committed
  `2026-11-09T01:37:11+01:00` = `2026-11-09T00:37:11Z`). Base `f5d5c6b06`.
- `docs/r1/reports/TRACKS_S01_RERUN_20261109.md` (280 lines), the 9 Nov `docs/r1/STATUS.md` entry, and
  `results/r1/tracks/digits_mlp/s01_rerun20261109/` (`serial.json`, `concurrent.json`, `SHA256SUMS`,
  `host_logs/`).

**Authority documents read by me, not relayed.**
- Track S operator runbook **rev 3.3** at docs commit **`13badb0`**, sha256
  `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53` (verified against
  `git show 13badb0:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`), Phase 1 and §0.1–§0.8.
- Operator runbook O3 (copy sha256 `e27b36752a5f22a645a070c7720084ea8f157f176dca3b867aea8c54de34f867`,
  identical to `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md` at `origin/docs/runbooks-09nov` =
  `421a93d215a72f6a488358f5587cfa652726a9d8`).
- PLAN §10 at `origin/docs/runbooks-09nov`: row **R1-TRACKS-S01-RERUN** (line 779) — "fresh servers; k = 2,
  serial and then concurrent, at `cache_prompt: false`; the probe's output suffix. **Clause (b) of the k
  rule is adopted:** if both tiers pass, k is the tier with the shorter projected total time (projection of
  30 Oct: digits 21.9 h at k = 1 against 31.8 h at k = 2)." — and row **R1-CACHEPROMPT-FALSE** (lines
  720–724).
- The author's 9 Nov scope (verbatim): "S0.1 重跑允许用新会话名，只追加 watcher 和 server 日志，在 TASL-2 上按 O3
  执行。今晚 TASL-7 不跑 Track P。"

All times UTC unless stated; the host's local clock is PST (UTC−8) and its log timestamps were converted.

## 1. Scope

In scope: the S0.1 re-run only — pins on the host and in the artefacts, launch-script provenance,
fresh-server/readiness provenance and exclusion of the 31 Oct race class, the exact Phase 1 arguments,
`cache_prompt`, identity and call counts, latency and CPU census, the projection and the clause-(b) `k`
decision, copy-back fidelity and preservation of earlier evidence, host end state, and the commits/pushes.
Out of scope: interpreting the S0.1 outcome, any later phase, any k decision beyond the Phase 1 rule.

## 2. Evidence checked

### 2.1 Pins and code state on TASL-2 (`ssh portal_zhixu`, read-only)

| Check | Result |
|---|---|
| paper checkout `$R/work/Agent_paper_B` | HEAD **`d10b05b738fc0e0dba54e0e692c248bedf095482`**, `git status --porcelain` **empty** |
| harness checkout `$R/work/autoresearch_harness` | HEAD **`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`**, clean |
| llama.cpp `$R/opt/llama.cpp` | HEAD **`620d2225cc436ab0b001e3200e590e3b286ef9ab`**, clean; `llama-server --version` = `version: 0.7.0-dev (build 11669, commit 620d2225c)`, `built with GNU 11.4.0 for Linux x86_64` |
| GGUF | sha256 **`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`** = pin |
| installed `bin/trks` | equals the committed `r1/tracks/ops/trks` except the two fill-ins `HOST_LABEL=TASL-2`, `GPU_ID=GPU-4d623e76-7587-ee15-a633-46f60d220d94`; `nvidia-smi` UUID matches; wrapper pins GGUF sha / build / bin |
| installed `trks-run`, `trks-servers`, `trks-watch`, `trks-status` | byte-identical to the committed `r1/tracks/ops/*` at the branch head (sha256 `b53bc811…`, `124316b5…`, `cf68843e…`, `5bd570ff…`); `trks-status` pins `PAPER_SHA=d10b05b7`, `HARNESS_SHA=a3fedbb`, `LLAMA_SHA=620d222`, `GGUF_SHA=509287f7` |
| host `$R/launch/*.sh` | all seven byte-identical to the committed ops-branch versions; the new script sha256 is §2.2 |

The paper and harness pins are therefore verified on the host and on the executed code path (`$R/bin/trks`
`cd $R/work/Agent_paper_B` then `python -m r1.tracks.probes.determinism`). `r1/tracks/probes/determinism.py`
is unchanged between `d10b05b7` and the review-time head (`git diff --stat d10b05b73..HEAD` shows only
docs, ops scripts and results), so the pinned probe ran.

### 2.2 Launch script: provenance, arguments, sessions, output tree

- Commit `87381a6ab` adds only `r1/tracks/ops/launch/tasl2_s01_rerun_20261109.sh` (142 lines). Its blob
  sha256 is **`064fa470e39ecd223165ba1ec65c68d64beddaad32e67e4ace1d68d537b4787d`** at both `87381a6ab` and
  `72dccc701`; the host copy `$R/launch/tasl2_s01_rerun_20261109.sh` has the **same** sha256, so the
  script that ran is the committed one. Host launch-log start **`2026-11-08T23:59:57Z`** is **53 s after**
  the commit time `2026-11-08T23:59:04Z`: committed before use.
- Exact Phase 1 arguments (from `host_logs/*.cmd`, which are `trks-run`'s `printf %q` record of argv):
  - serial: `--url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 --order-seed 1
    --proposal-schema manager_proposal/v1 --node digits_mlp --server-args "<18101 line>" --out
    …/s01_rerun20261109/serial.json`;
  - concurrent: `--url …18101/v1 --url …18102/v1 --mode concurrent --clients-per-url 2 --n 200 --repeats 3
    --order-seed 2 --proposal-schema manager_proposal/v1 --node digits_mlp --server-args "<18101 line> |
    <18102 line>" --out …/s01_rerun20261109/concurrent.json`.
  These are the rev-3.3 Phase 1 arguments verbatim; only the output directory is the authorised new one.
- New session names **`trks_s01_serial_r2`** / **`trks_s01_conc_r2`**, new output directory
  **`$OUT/digits_mlp/s01_rerun20261109`**; the script refuses to run if `serial.json`/`concurrent.json`
  already exist, if any of `trks_llm`/the two sessions exists, if a priority/drill marker exists, if a GPU
  compute app is present, or if the lease is held (lines 34–49). Serial runs first and the concurrent
  session starts only after the serial session is gone (serial `.exit` `rc=0` `00:06:53Z`; concurrent
  `.cmd` written `00:07:00Z`).
- Servers: started by `tmux new -d -s trks_llm $R/bin/trks-servers 2` (k = 2, fresh), pids **6315**
  (:18101) and **6316** (:18102) recorded at readiness together with both GPU compute-app entries
  (5242 MiB each), lease **HELD**; server log segments each show `offloaded 29/29 layers to GPU` and
  `model loaded`. The `--server-args` provenance strings match the installed `trks-servers` command
  (flags, values and order) for the respective port.
- `SHA256SUMS` in the copied-back tree verifies (`sha256sum -c` all OK). Mac and host copies of the two
  JSONs and the seven `host_logs` files are byte-identical (e.g. `serial.json`
  `44556b002d309393f18e3274188a4fe18ea66bd178d9c03830a094e3693131af`, `concurrent.json`
  `ec9fcb4f64429f161c71ab064305a5a0f2248afe9cad8bb09e11cc51a0f39c86`).

### 2.3 Fresh servers, readiness gate and the 31 Oct race class

- Timeline from the launch log and the session files: servers start `23:59:57Z`; **both** `/v1/models`
  endpoints answer with the `r1-manager` alias at **`23:59:59Z`** (server segments: `model loaded` at
  rel. 1.25 s / 1.27 s, first request posted at rel. 2.77 s, first response at rel. 3.43 s); the launch
  log records the readiness lines and then `starting serial probe in tmux session trks_s01_serial_r2`,
  and the serial `.cmd` file was written at `23:59:59.945`. Because `trks-run` creates the tmux session
  only after the readiness lines are logged, the serial probe's first call is necessarily **after** both
  readiness checks. The launch log's in-script counter reads "0 s" because it starts after the script's
  own 2 s settle; the true wall time from server start to both endpoints ready is ≈2 s (as the report
  says).
- Positive exclusion of the 31 Oct class: `server_props` is **non-null for every URL** in both JSONs
  (`build_info = b11669-620d2225c`, `model_alias = r1-manager`, `model_path` = the pinned GGUF, `n_ctx =
  8192`, `total_slots = 1`); transport errors are **0** in all three URL entries; and the launch log
  records both pids and both GPU compute-app entries before either probe starts.
- Contrast with the preserved 31 Oct invalid run (read directly from
  `out/digits_mlp/s01_rerun_INVALID_serial_raced_server_start_20261031T112159Z/`): serial
  `server_props = null`, errors **600/600**, identity 0.0; concurrent `server_props = null`, errors
  **1177/1177 per URL**, identity 0.0, `cross_server_identity` 0.0. The re-run cannot be that class: the
  servers it started were the ones that answered, it recorded pids and GPU memory, and every call
  succeeded.
- The pre-offset tails of both server logs are the disclosed ~10 s pre-use start/poll/kill self-test
  (`model loaded` then shutdown lines), and the re-run segment of each log starts with a fresh
  `initializing …` — the offsets exclude the self-test, as the report states.

### 2.4 `cache_prompt`

- `serial.json` and `concurrent.json`: top-level **`cache_prompt: false`**, `cache_prompt_label:
  "explicit"`; `request_example.cache_prompt: false`, with `model: r1-manager`, `temperature: 0.2`,
  `seed: 1332422715`, `response_format` = `manager_proposal/v1` (`manager_proposal_v1`, `strict: true`),
  one user message and **no** `max_tokens`.
- Pinned harness `a3fedbb`: `src/autoresearch/llm/providers.py` (`llamacpp_cache_prompt()` default
  `False`, env `LLAMACPP_CACHE_PROMPT`) and `src/autoresearch/llm/langchain_client.py:190–199`
  (`extra_body["cache_prompt"] = bool(config.cache_prompt)`, merged into every request body). The probe
  builds its body with the harness's own `chat_payload` (including the `extra_body` merge,
  `determinism.py:60–78`) and posts exactly that payload, so `request_example` is the body that was sent.

### 2.5 Identity, call counts, order — and independent recomputation from raw contents

Reported aggregates (all read from the new JSONs, not from the report):

| Setting | URL | rate | per-client | calls | errors |
|---|---|---|---|---|---|
| serial | :18101 | **1.0** | [1.0] | n = 600 | 0 |
| concurrent | :18101 | **1.0** | [1.0, 1.0] | n = 1200 | 0 |
| concurrent | :18102 | **1.0** | [1.0, 1.0] | n = 1200 | 0 |

`cross_server_identity = 1.0`, `cross_client_identity = 1.0` for both URLs. With `n_prompts = 200`,
`repeats = 3` and `clients_per_url = 1 / 2`, the integer forms are **200/200** per URL (every prompt's
repeats identical), **600/600** per client per URL (concurrent), **200/200** cross-server, 600 serial calls
and 1200 + 1200 = 2400 concurrent calls — exactly the values the report states (`identity_rate == 1.0`
means all prompts had all repeats present and equal; `errors == 0` means no `None` repeat). I reproduced
all five `order_head` entries from the probe's own schedule rule
(`random.Random(f"{seed}|{url_index}|{client}").shuffle`) for serial (`seed 1`, URL index 0) and
concurrent (`seed 2`, URL indices 0/1 × clients 0/1); all match the recorded heads, and the serial head
`[[163,1],[7,2],[134,1],[86,0],[0,0]]` is identical to the Oct-30 and 31 Oct runs.

**Independent recomputation from the saved raw contents.** The pinned probe writes aggregates only:
at `d10b05b7`, `r1/tracks/probes/determinism.py:320` is
`"per_url": {u: {k: v for k, v in r.items() if k != "contents"} …}` — the per-call contents are dropped
after in-process computation (Oct-30 review P3; the line was `:313` at `9bb64ba`). So from the
**committed JSON alone** the rates cannot be recomputed, only checked for consistency as above.

However, the append-only server logs of this run **do** preserve the raw contents: for every request,
llama-server's `--verbose` log records the rendered prompt in the `slot launch_slot_ … "Budget index (trial
number): N"` line, and every assistant response in a following `Parsed message: {"role":"assistant",…}`
line. Using only the documented offsets from the committed launch log
(`llama_18101.log` from byte 97 448 571; `llama_18102.log` from byte 199 241 358), I recomputed identity
from those contents:

- serial (:18101, first 600 calls): 600 prompt launches in the recorded schedule order, 600 responses;
  **200/200** prompts with all 3 repeats identical;
- concurrent (:18101, next 1200 calls; :18102, 1200 calls): **200/200** on each server with 6 identical
  calls per prompt (199 prompts × 6 and one prompt × 5 in the ordered pairing — the last request's prompt
  line is not logged on each server, and its unpaired last response is byte-equal to that prompt's group,
  giving 6/6);
- cross-server first-content equality: **200/200** (`cross_server_identity = 1.000`).
- Negative control: shifting the response alignment by one call drops the 18102 identity to 2/200, so the
  200/200 result is discriminating, not an artefact of the few (34) distinct response strings.

This recomputation is host-side; the committed copy-back still carries aggregates only. See MINOR 1 for the
required report correction and the residual-limitation judgment (§4).

### 2.6 Latency, CPU census, projection, `t_run`, clause-(b) decision

Latency and census from the JSONs (exact stored values): serial mean **0.6883090593914191 s**, p95
0.7199368765577674 s; concurrent means **2.7299385012717297 s** (:18101) and **2.7269037405401466 s**
(:18102), p95 2.854857158847153 / 2.852099632844329 s; `cpu_before`/`cpu_after` `cpus = 32`,
`cores_free_est` 30.837890625 → 29.38330078125 (serial) and 29.51318359375 → 28.70751953125 (concurrent;
`cores_free_est = cpus − loadavg_1m` exactly, e.g. 32 − 3.29248046875 = 28.70751953125). The report's
table rounds these correctly.

Projection: `hours = (C·L/k + R·t_run/c)/3600` with C = 80 000, R = 60 000, `c = min(free, 2k)`,
`L(k=1) = 0.688309059` and `L(k=2) = mean(2.7299385013, 2.7269037405) = 2.728421121` and `free =
28.70751953125`:

| k | L (s) | c | LLM h | CPU h | total h |
|---|---|---|---|---|---|
| 1 | 0.688309059 | 2 | 15.2958 | 7.5758 | **22.8716** |
| 2 | 2.728421121 | 4 | 30.3158 | 3.7879 | **34.1037** |

`t_run = 0.9091 s` provenance checked on the host: `$R/logs/trks_smoke.log` (TASL-2 Phase 0 smoke,
29 Oct) has **77** `run_command finished in …s` lines with mean **0.909091 s** (max 1.9) — the report's
"Phase 0 smoke-test value for `digits_mlp`, TASL-2, n = 77" is correct.

30 Oct reproduction: from the preserved `results/…/s01` JSONs, `L(k=1) = 0.6445961617`,
`L(k=2) = mean(2.5217002518, 2.5272556170) = 2.5244779344`, `free = 28.74560546875` → **21.9002 h** at
k = 1 and **31.8377 h** at k = 2, i.e. the PLAN row's "21.9 h against 31.8 h" exactly.

Rule: both tiers pass (serial 1.000; concurrent 1.000 on both URLs **and** cross-server 1.000). Under the
adopted clause (b) of R1-TRACKS-S01-RERUN the choice is the shorter projected total: **k = 1** (22.87 h vs
34.10 h, 11.23 h shorter). The runbook's unamended Phase-1 ordering would have selected k = 2 first, but
the author's row and O3 replace that ordering with clause (b); the operator applied the adopted rule and
did not set k outside it. The 30 Oct projections are reproduced by the same formula, which is the
interpretation check the report claims.

### 2.7 Earlier evidence preserved; copy-back fidelity

Host sha256 (and mtimes/ctimes unchanged from 30/31 Oct, PST):

| File | sha256 | report |
|---|---|---|
| `out/digits_mlp/s01/serial.json` | `65388dfaa60cc5380733dd15befec4b39c873872b01d4d5088b7ac3068d7b56a` | matches; mtime 2026-10-30 03:20:24 −0700 |
| `out/digits_mlp/s01/concurrent.json` | `005cadb3a2b37cb5c7ed6d5136bcced23847fea4fd6815233a1caaf3c6a9b182` | matches; mtime 2026-10-30 03:45:44 −0700 |
| `…/s01_rerun_INVALID_serial_raced_server_start_20261031T112159Z/serial.json` | `93ebdcc1fa57976c6165759a20323bc8a3d209324d238d89e1d011848a29f20a` | matches; mtime 2026-10-31 04:21:08 −0700 |
| `…/…/concurrent.json` | `df8612f77590bb11f1912485692124af5a8c031a44bf8cd2099cc098a8db983f` | matches; mtime 2026-10-31 04:21:55 −0700 |

The INVALID directory exists and is intact (directory mtime 2026-10-31 04:20:38, ctime 04:21:59). The
Oct-30 `s01` hashes also match the values recorded by the independent Oct-30 Phase-1 review; the INVALID
hashes have no earlier committed baseline, so their intactness rests on the unchanged mtime/ctime and on
the new run writing only to the new directory. The new directory contains only the two JSONs; `$OUT/inputs`,
`$R/scratch`, `$R/work` and `out/smoke` were not modified by the run (`find … -newermt`).

Every Mac copy is byte-identical to the host file (two JSONs and all seven `host_logs` files; `sha256sum -c
SHA256SUMS` OK).

### 2.8 Host end state (checked `2026-11-09T00:40–00:47Z`) and append-only logs

| Check | Result |
|---|---|
| tmux | only `trks_watch` (created `23:58:08Z`, pid 4183646, `bash …/bin/trks-watch`, pane start command the installed script); no `trks_llm`, no probe sessions |
| lease | `flock -n ~/r1_locks/gpu0.lock true` **succeeds** (free) |
| GPU | no compute app; 436 MiB used, 0 % (baseline; no llama-server process) |
| listeners | no listener on 18101/18102 (`ss -ltnp`) |
| STOP files | none under `$R/out` |
| markers | `~/r1_locks` contains only `gpu0.lock`; no `trackx_evidence.active`/`trackp_evidence.active`; no `$R/trks_drill.active` |
| disk | `/home/dowling` 184 G free, 90 % used |
| watcher log | `logs/watch.log` has exactly 3 `watch started` lines (2026-10-30T01:14:12Z, 2026-10-30T11:08:05Z preserved; 2026-11-08T23:58:08Z added) and no `priority marker`/`pausing`/`FORCED` lines — append-only |
| server logs | sizes 393 100 113 B and 394 023 968 B = recorded offsets 97 448 571 + 295 651 542 and 199 241 358 + 194 782 610 — the re-run byte counts in the report are exact; segment starts with a fresh `initializing …`; **0** `E`-level lines in each new segment; 3 `W`-level lines each, all benign (no-API-key/CORS banner; GGUF `</s>` control-token-type warning) so the report's "0 error/failure lines" is consistent |
| files changed on the host | exactly the launch script, one launch log, six probe-session files, `watch.log` and the two llama logs appended, the two new JSONs, and the bare-repo objects from the push; nothing outside `$R` (`find /home/dowling -maxdepth 3 -newermt …` empty) |

This matches the author's "only append watcher and server logs" constraint: no pre-existing file outside
the watcher/server logs was modified, and the new files are the new sessions/output the row authorises.

### 2.9 Commits and pushes

- Branch `trackS-ops-20261030` tip **`72dccc701`**; ancestry `72dccc701 → 87381a6ab → f5d5c6b06 →
  2906b6767 → d10b05b73`; worktree clean before this review file was added.
- GitHub `origin`: `refs/heads/trackS-ops-20261030 = 72dccc701` (`git ls-remote`). Local push reflog shows
  one transition `f5d5c6b06 → 72dccc701` ("update by push"); no force flag; `f5d5c6b06` is an ancestor of
  `72dccc701`, so the push is a fast-forward.
- TASL-2 bare repo `$R/remotes/Agent_paper_B.git`: `refs/heads/trackS-ops-20261030 = 72dccc701`; the only
  other ref is the old tag `trackS-code-9bb64ba = 9bb64ba`; `merge-base --is-ancestor f5d5c6b06
  trackS-ops-20261030` holds; `git fsck --unreachable` reports no unreachable objects (only the
  normal unborn-`master` HEAD note); the local `tasl2/trackS-ops-20261030` reflog records the same single
  `f5d5c6b06 → 72dccc701` update by push. The bare repo has no reflog (`core.logAllRefUpdates` unset),
  so a server-side force-push history cannot be excluded from the bare repo alone; the local push reflog
  (single new entry, direct old→new transition) and the ancestry check are the evidence that it was a
  normal fast-forward.
- No other branch or tag points at `72dccc701`/`87381a6ab` locally or in the bare repo; nothing else was
  pushed (single new push-reflog entry on both remotes).

### 2.10 Report and STATUS

Every number in report §2–§5 reproduces (identity, latencies, census, projections, hashes, byte counts,
timeline). The `STATUS.md` entry's claims are accurate except for the MINOR items below. The report does
not claim any result beyond ENGINEERING_ONLY and does not start any later phase.

## 3. Findings

No **BLOCKING** or **MAJOR** finding. Three **MINOR** items, one of which is the residual limitation; none
changes the `k` decision or any recorded S0.1 number.

### MINOR 1 (evidence limitation / wording of the author's requirement)

- **Location:** report `docs/r1/reports/TRACKS_S01_RERUN_20261109.md` §2.4 and §7 first bullet; STATUS
  "Residual limitation (flagged)" bullet; commit message of `72dccc701`.
- **Issue:** the statements "the identity rates therefore cannot be recomputed from raw per-call
  responses" / "identity cannot be recomputed from saved raw contents" are true for the **pinned probe's
  JSON** (`determinism.py:320` drops `contents`), but not for the run's saved data as a whole: the
  append-only server logs (offsets in the committed launch log) contain the rendered prompt and the
  response of every call, and I recomputed both tiers and the cross-server rate from them exactly
  (200/200 each; §2.5). The author's row R1-TRACKS-S01-RERUN says "identity recomputed from the saved
  contents"; under the pinned probe that is impossible **from the copied-back JSON**, but it is possible
  from the raw contents that exist on the host, and the reviewer has done it.
- **Required answer:** (a) correct the two sentences to state the limitation precisely (probe JSON only),
  (b) record in §2.4 that the raw per-call contents live in the append-only server-log segments at the
  offsets/sizes already recorded in the launch log and that the reviewer recomputed the identity from them,
  and (c) put the residual question to the author at STOP 1: confirm that the row is satisfied by this
  recomputation or authorise an instrumented-probe pin/PLAN row for future committed raw contents. The
  operator cannot satisfy (c) itself and must not change the pin.

### MINOR 2 (provenance completeness of the committed artefacts)

- **Location:** `results/r1/tracks/digits_mlp/s01_rerun20261109/serial.json` / `concurrent.json`
  `provenance`; report "Pins" section.
- **Issue:** the probe's `provenance` records the GGUF sha256/path, the llama.cpp commit and the server
  arguments, but **not** the paper or harness commits; `server_props.build_info = b11669-620d2225c`
  identifies only the llama.cpp build. The paper `d10b05b7` and harness `a3fedbb` pins are verified on the
  host and recorded in the report, but a reader of the committed evidence alone cannot bind them.
- **Required answer:** state this explicitly in the report ("pins rest on the host checkouts and this
  report; the probe JSON does not carry them"), and note for the next probe pin that recording the
  paper/harness SHAs would close the gap. This is the same probe design as the accepted Oct-30 run.

### MINOR 3 (report detail accuracy)

- **Location:** report §1.1 timeline (first row) and §1; §0 pre-check table.
- **Issue (three details):** (i) the timeline row "…flock pid 6310" cites
  `host_logs/s01_rerun_20261109_launch.log`, but that log contains only `lease: HELD` and the two server
  pids — it does not contain `6310` (the flock pid is not in the committed evidence); (ii) §1 says the
  script "refuses to start over an existing output dir", while its guard is on existing
  `serial.json`/`concurrent.json` (it `mkdir -p`s the directory); (iii) §0 calls the installed
  `trks-status` "byte-identical to the rev-3.3 §11 templates", but `trks-status` is not a §11 template —
  it matches the committed `r1/tracks/ops/trks-status` at the branch head (`5bd570ff…`), and the host code
  checkout `d10b05b7` carries a different version (`a217f6b8…`).
- **Required fix:** correct the three sentences (or drop the flock-pid claim). No impact on the evidence.

## 4. Residual-limitation judgment (explicit)

The author's row requires identity "recomputed from the saved contents". The pinned probe
(`determinism.py:320` at `d10b05b7`) computes `identity_rate`, `identity_rate_per_client`,
`cross_client_identity` and `cross_server_identity` in-process from per-call contents and then writes
`per_url` **without** `contents`, so the committed JSON cannot reproduce the rates — this is the known
Oct-30 review P3 limitation (there `determinism.py:313` at `9bb64ba`), which was accepted as a MINOR
evidence limitation, and it was a property of the pin, not an operator error.

**Classification: recorded limitation (MINOR), not BLOCKING.** Reasons:
1. The pin does not allow the literal requirement to be met from the committed copy-back, and changing the
   probe or the pin is not this operator's authority (it would need a new pin/PLAN row); the operator
   correctly did not change it and flagged it.
2. The identity claim itself is nevertheless independently corroborated: the in-process computation is
   internally consistent (integer counts, call counts, per-client/cross-client/cross-server consistency,
   `errors = 0`, reproduced `order_head` schedules), **and** I recomputed it from the raw per-call contents
   preserved in the append-only server logs (200/200 serial; 200/200 on each concurrent URL; 200/200
   cross-server), with a discriminating negative control.
3. The `k` decision is therefore not at risk: both tiers pass and both were verified from raw contents.
4. The remaining obligation is documentary and belongs to the author at STOP 1: either confirm that the
   host-log recomputation satisfies R1-TRACKS-S01-RERUN (and have the report say so, MINOR 1), or
   authorise an instrumented-probe pin so that future runs carry replayable contents in the committed
   evidence. Until that confirmation the limitation stands recorded and must not be quoted as if the
   committed JSON were self-sufficient.

## 5. Acceptance checklist

| Requirement | Status | Evidence |
|---|---|---|
| Pins on host: paper `d10b05b7`, harness `a3fedbb`, llama.cpp `620d222`, GGUF `509287f7…` | **PASS** | §2.1 (clean checkouts, `llama-server --version`) |
| Probe output carries host TASL-2, model `r1-manager`, temperature 0.2, schema, request body | **PASS** | §2.2/§2.4 |
| Launch script committed before use, same sha256 in commit and on host | **PASS** | §2.2 `064fa470…`; commit 23:59:04Z < log 23:59:57Z |
| Exact rev-3.3 Phase 1 arguments; serial then concurrent; new sessions; new output dir | **PASS** | §2.2 `*.cmd`; `.exit` times |
| Fresh servers k = 2, readiness gate on **both** endpoints before serial; 0 transport errors | **PASS** | §2.3 (pids 6315/6316, GPU apps, both `/v1/models`, `server_props` non-null) |
| 31 Oct race class excluded (contrast with 600/1177 errors and null `server_props`) | **PASS** | §2.3 |
| `cache_prompt: false` top level and in `request_example`; label explicit; harness default false | **PASS** | §2.4 |
| Identity integers: 200/200 serial; 200/200 each URL; per-client [1.0,1.0]; cross-client 1.0; cross-server 200/200; errors 0; calls 600/1200+1200 | **PASS** | §2.5, plus raw-content recomputation |
| Latency mean/p95 and free cores match the JSONs | **PASS** | §2.6 |
| `t_run` provenance; both k branches; clause-(b) k = 1; 30 Oct 21.90/31.84 h reproduction | **PASS** | §2.6 |
| Oct-30 `s01` and Oct-31 INVALID evidence untouched (sha256/mtime/ctime); INVALID dir intact | **PASS** | §2.7 |
| Copy-back faithful (`SHA256SUMS`) | **PASS** | §2.2/§2.7 |
| Host end state: servers stopped, lease free, no compute app/listener, watcher running, no markers, no STOP, disk | **PASS** | §2.8 |
| Only the watcher/server logs appended; nothing outside `$R` written | **PASS** | §2.8 |
| Commits/pushes: tip `72dccc701`; origin + TASL-2 bare at `72dccc701`; fast-forward; nothing else pushed; worktree clean | **PASS** | §2.9 |
| No Phase 2/3 started, no pin/GGUF/flag change, no TASL-7 action | **PASS** | §2.1/§2.8; commit contents |
| Review loop at STOP 1 | **PASS** | this file |

## 6. Verdict

The S0.1 re-run on TASL-2 is independently reproducible in every number it reports: the pins and code are
as declared, the launch script is committed and executed verbatim, the servers were fresh and the
readiness gate on both endpoints excludes the 31 Oct race class, both identity tiers are at 100 % (and I
recomputed them from the raw response contents preserved in the server logs), 0 transport errors,
`cache_prompt: false` is carried explicitly, the projection arithmetic and the 30 Oct reproduction are
exact, and the clause-(b) k decision is correctly applied (`k = 1` at 22.87 h vs k = 2 at 34.10 h). The
host is left clean and the earlier evidence is preserved; the branch is pushed fast-forward to
`72dccc701` and the worktree is clean. The residual P3 limitation is a documented property of the pinned
probe with an author decision outstanding at STOP 1, and the MINOR items are documentary corrections.

**Verdict: accepted**
