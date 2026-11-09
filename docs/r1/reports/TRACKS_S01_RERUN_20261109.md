# Track S — S0.1 determinism re-run on TASL-2 (`digits_mlp`), 9 November 2026

**Written 9 Nov 2026 by the Track S operator agent (DSH experiment-agent session, Lead: experiment agent); AI-assisted.**
**ENGINEERING_ONLY.** This is not a result and is never quoted as one. It feeds the pre-declaration and the
Phase 1 `k` rule.

**Authority.** Operator runbook **O3** (`prompts/OPERATOR_RUNBOOK_20261104.md`, branch `docs/runbooks-09nov`);
author PLAN §10 row **R1-TRACKS-S01-RERUN** (fresh servers; `k = 2`, serial then concurrent, at
`cache_prompt: false`; probe output suffix; new output directories; identity recomputed from the saved
contents; clause (b) adopted); Track S operator runbook **rev 3.3** at docs commit `13badb0`
(sha256 `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`; rev 3.4/3.5 are not of
record), Phase 1 and §0.1–§0.8; PLAN rows R1-CACHEPROMPT-FALSE, R1-TRACKS-HOST/HOST-2,
R1-TRACKS-S01-FOLLOWUP(-REV), R1-PORTAL-SCHEDULE, R1-COMPUTE. Author's scope, 9 Nov: "S0.1 重跑允许用新会话名，
只追加 watcher 和 server 日志，在 TASL-2 上按 O3 执行。今晚 TASL-7 不跑 Track P。"

**Pins.** paper `d10b05b738fc0e0dba54e0e692c248bedf095482` (detached), harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`
(`v0.7.0-dev`, build 11669, `b11669-620d2225c`), GGUF sha256
`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`. The launch script is the one extra
ops commit `f5d5c6b0` + this re-run's `87381a6a` on `trackS-ops-20261030`; the **host code checkout stays at
`d10b05b7`** (the suffix is a launch-script feature, not a code change).

**Pin provenance limitation (reviewer MINOR 2).** The probe JSON's `provenance` block records the GGUF
sha256/path, the llama.cpp commit and the server command line, but **not** the paper or harness commits;
`server_props.build_info = b11669-620d2225c` identifies only the llama.cpp build. The paper `d10b05b7` and
harness `a3fedbb` pins therefore rest on (i) the host checkouts verified clean at those commits, (ii) the
host's `trks-status` (`PAPER_SHA=d10b05b7`, `HARNESS_SHA=a3fedbb`, `LLAMA_SHA=620d222`, `GGUF_SHA=509287f7`),
and (iii) the executed code path — `$R/bin/trks` `cd`s into `$R/work/Agent_paper_B` and runs
`python -m r1.tracks.probes.determinism`, and `determinism.py` is unchanged between `d10b05b7` and the
review-time head. This is the same probe design as the accepted Oct-30 run; for the next probe pin, record
the paper and harness SHAs in `provenance` so the committed evidence binds them itself.

## 0. Pre-checks (all passed; nothing started before them)

Run on TASL-2 at `2026-11-08T23:55Z`, read-only unless noted.

| Check | Result |
|---|---|
| `trks-status` pins | paper `d10b05b7` OK, harness `a3fedbb` OK, llama.cpp `620d222` OK, GGUF sha256 OK, **0** tracked-file modifications |
| installed `bin/` scripts vs templates | `trks-run`, `trks-servers`, `trks-watch` byte-identical to the rev-3.3 §11 templates. `trks-status` is **not** a §11 template; it is byte-identical to the committed `r1/tracks/ops/trks-status` at the branch head (`5bd570ff…`), which is newer than the version in the `d10b05b7` checkout (`a217f6b8…`). `trks` differs only in the two required fill-ins (`HOST_LABEL=TASL-2`, `GPU_ID=GPU-4d623e76-7587-ee15-a633-46f60d220d94`, matching `nvidia-smi`) |
| host `launch/*.sh` vs repo | all six byte-identical |
| stale `STOP` files under `$R/out` | none |
| `$R/trks_drill.active` | absent |
| `~/r1_locks/trackx_evidence.active` | absent |
| `~/r1_locks/trackp_evidence.active` | absent |
| llama-server processes / GPU compute apps | none (GPU 436 MiB, 0 %) |
| `flock -n ~/r1_locks/gpu0.lock true` | succeeds (lease free) |
| `trks_llm` / `trks_watch` sessions | none (no tmux server at all) |
| disk `/home/dowling` | 185 G free, 90 % used |

**Watcher restarted (step 2):** `tmux new -d -s trks_watch $R/bin/trks-watch`; `logs/watch.log` (append-only)
gained `2026-11-08T23:58:08Z watch started` (the two earlier `watch started` lines are intact); session and
process alive.

**Pre-use readiness check (disclosed).** Before committing the launch script I ran a ~10 s start/poll/kill
cycle (`trks-servers 2`, `/v1/models` answered on both ports, then `tmux kill-session -t trks_llm`). It proved
the readiness endpoint and the kill/lease path. It appended a short segment to `logs/llama_1810{1,2}.log`
(append-only is allowed); the re-run's own offsets below are taken **after** it, so its evidence segment is
excluded from the re-run's.

## 1. What ran

New launch script, committed **before use**: `r1/tracks/ops/launch/tasl2_s01_rerun_20261109.sh`
(commit `87381a6abf2296f14015124c420fe93468cf9387`), `scp`'d to `$R/launch/` (sha256
`064fa470e39ecd223165ba1ec65c68d64beddaad32e67e4ace1d68d537b4787d`, identical on host and Mac),
run as:

```
ssh portal_zhixu bash /home/dowling/r1_tracks/launch/tasl2_s01_rerun_20261109.sh
```

The script fixes the race that invalidated the 31 Oct attempt: it starts **fresh servers `k = 2`**
(`tmux new -d -s trks_llm $R/bin/trks-servers 2`), **waits (bounded, 900 s) until BOTH
`http://127.0.0.1:18101/v1` and `:18102/v1` answer `/v1/models` with the `r1-manager` alias**, and only then
starts the serial probe. Probe session names are new (`trks_s01_serial_r2`, `trks_s01_conc_r2`), and the
output directory is new (`$OUT/digits_mlp/s01_rerun20261109`), so no Oct-30/31 evidence was overwritten.
The script refuses to run if `serial.json`/`concurrent.json` already exist (it creates the new directory
with `mkdir -p`), if an existing session is present, if a priority/drill marker exists, if a GPU compute
process is present, or if the lease is held.

Probes used the **exact rev-3.3 Phase 1 arguments**:

```
trks probe --url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 --order-seed 1 \
  --proposal-schema manager_proposal/v1 --node digits_mlp --server-args "<18101 server line>" \
  --out $OUT/digits_mlp/s01_rerun20261109/serial.json
trks probe --url http://127.0.0.1:18101/v1 --url http://127.0.0.1:18102/v1 --mode concurrent \
  --clients-per-url 2 --n 200 --repeats 3 --order-seed 2 --proposal-schema manager_proposal/v1 \
  --node digits_mlp --server-args "<18101 line> | <18102 line>" \
  --out $OUT/digits_mlp/s01_rerun20261109/concurrent.json
```

Server line, both ports: `$R/opt/llama.cpp/build/bin/llama-server -m
$R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager --host 127.0.0.1 --port 1810{1,2}
-ngl 999 -c 8192 --parallel 1 --verbose`.

### 1.1 Timeline (UTC) and positive exclusion of the 31 Oct racing class

| Event | Time | Evidence |
|---|---|---|
| fresh servers start (`k = 2`), server pids **6315** (:18101), **6316** (:18102), lease **HELD** | `2026-11-08T23:59:57Z` | `host_logs/s01_rerun_20261109_launch.log` |
| **both** `/v1/models` answer (`r1-manager`), `offloaded 29/29 layers to GPU`, `model loaded` | `2026-11-08T23:59:59Z` | launch log; server log segments |
| readiness wait | **≈2 s** wall clock from server start (the in-script counter reads `0 s` because it starts after the script's own 2 s settle); lease **HELD** before either probe | launch log |
| serial session `trks_s01_serial_r2` starts | `2026-11-08T23:59:59Z` | `logs/trks_s01_serial_r2.cmd` |
| serial `rc=0` | `2026-11-09T00:06:53Z` (6 m 54 s) | `logs/trks_s01_serial_r2.exit` |
| concurrent session `trks_s01_conc_r2` starts | `2026-11-09T00:07:00Z` | `logs/trks_s01_conc_r2.cmd` |
| concurrent `rc=0` | `2026-11-09T00:34:19Z` (27 m 19 s) | `logs/trks_s01_conc_r2.exit` |
| launch script returns 0 | `2026-11-09T00:34:30Z` | launch log |
| servers stopped by the operator; clean state re-checked | `2026-11-09T00:36:14Z` | §3 |

Positive evidence that this was **not** the 31 Oct race: the servers were started **by this script**, both
endpoints answered before the serial session was created, the serial probe recorded `server_props` non-null
and **0** transport errors (the invalid 31 Oct serial had `server_props: null` and 600/600 errors), and the
two probes recorded **0** transport errors in total.

## 2. Results (ENGINEERING_ONLY) — recomputed from the saved JSON

Call shapes: serial 200 prompts × 3 repeats × 1 client = **600 calls**; concurrent 200 prompts × 3 repeats ×
2 clients per URL = **1200 calls per URL, 2400 calls total**.

### 2.1 `cache_prompt` evidence (R1-CACHEPROMPT-FALSE)

| File | top-level `cache_prompt` | `request_example.cache_prompt` | label |
|---|---|---|---|
| `serial.json` | **false** | **false** | `explicit` |
| `concurrent.json` | **false** | **false** | `explicit` |

The full request body (`request_example`) carries `cache_prompt: false` at top level together with
`model=r1-manager`, `temperature=0.2`, the fixed per-prompt seed, `response_format` for
`manager_proposal/v1` and no `max_tokens` — i.e. the harness body as flattened from `extra_body`.

### 2.2 Identity

| Setting | URL | within-server identity | per-client | errors | calls |
|---|---|---|---|---|---|
| serial | :18101 | **1.000 = 200/200** | [1.0] | **0** | 600 |
| concurrent | :18101 | **1.000 = 200/200** (over 6 calls/prompt) | [1.0, 1.0] | **0** | 1200 |
| concurrent | :18102 | **1.000 = 200/200** (over 6 calls/prompt) | [1.0, 1.0] | **0** | 1200 |

| Cross checks | value |
|---|---|
| `cross_server_identity` (:18101 vs :18102, first content) | **1.000 = 200/200** |
| `cross_client_identity` per URL | **1.000** on both URLs |
| serial `order_head` vs 30 Oct valid run and vs 31 Oct invalid run | **identical** (`[[163,1],[7,2],[134,1],[86,0],[0,0]]`), as expected from the fixed `order_seed`/URL/client schedule |

### 2.3 Latency and CPU census

| Setting | URL | n | mean (s) | p95 (s) |
|---|---|---|---|---|
| serial | :18101 | 600 | **0.6883** | **0.7199** |
| concurrent | :18101 | 1200 | **2.7299** | **2.8549** |
| concurrent | :18102 | 1200 | **2.7269** | **2.8521** |

`L_serial = 0.688309` s; `L_concurrent = mean of the two URL means = 2.728421` s.
CPU census (`loadavg` → cores free estimate, 32 CPUs): serial before **30.84** → after **29.38**;
concurrent before **29.51** → after **28.71** (the value used in the projection).

The concurrent latency (~4× serial) is the same qualitative effect as 30 Oct (0.64 → 2.52 s), shifted by the
expected `cache_prompt: false` cost (Oct-30 serial 0.6446 s × 1.06 ≈ 0.683 s here).

### 2.4 Identity verifiability: aggregates in the probe JSON; raw contents recomputed from the append-only server logs

The pinned probe writes **aggregates only**: at paper `d10b05b7`, `r1/tracks/probes/determinism.py:320`
filters `contents` out of the JSON it writes
(`"per_url": {u: {k: v for k, v in r.items() if k != "contents"} ...}`). **The identity rates therefore cannot
be recomputed from the probe JSON.** This is the same pin limitation recorded in the accepted Oct-30
Phase-1 report §"Evidence limitation (reviewer P3)" and its review (`TRACKS_OPS_PHASE1_REVIEW_20261030.md`,
P3; the line was `determinism.py:313` at `9bb64ba`). I did **not** modify the pinned probe or the pin.

**The saved raw contents do exist in the append-only server logs, and they were independently recomputed.**
With `--verbose`, llama-server logs the rendered prompt of every request (`slot launch_slot_ …
"Budget index (trial number): N"`) and every assistant response (`Parsed message: {"role":"assistant",…}`).
The committed launch log records the segment offsets taken immediately before the fresh servers started —
`llama_18101.log` from byte **97,448,571** and `llama_18102.log` from byte **199,241,358** — and the segments
this re-run appended are **295,651,542 B** and **194,782,610 B** respectively. From exactly those segments
the **independent reviewer** recomputed identity (`TRACKS_OPS_S01_RERUN_REVIEW_20261109.md` §2.5):

- serial (:18101, first 600 calls): 600 prompt launches in the recorded schedule order and 600 responses;
  **200/200** prompts with all 3 repeats identical;
- concurrent (:18101 next 1200 calls; :18102 1200 calls): **200/200** on each server with 6 identical calls
  per prompt (the reviewer's exact reconciliation: 199 prompts × 6 and one prompt × 5 in the ordered
  pairing, because llama-server does not log the last request's prompt line on each server; that unpaired
  last response is byte-equal to that prompt's group, giving 6/6);
- cross-server first-content equality: **200/200** (`cross_server_identity = 1.000`);
- a one-call response shift drops the :18102 identity to **2/200** — a discriminating negative control.

My own corroboration that those saved contents are present at the recorded offsets: **1,799** prompt-launch
lines and **1,800** assistant responses in the `llama_18101.log` segment, and **1,199** / **1,200** in the
`llama_18102.log` segment — exactly the documented last-prompt-line-per-server omission (1,799 = 600 serial
+ 1,199 concurrent). The full recomputation is the reviewer's, recorded in the review file §2.5.

What I verified from the **new run's own** saved JSON aggregates (not by copying earlier numbers):

- integer-count consistency: `identity_rate × n_prompts` is an integer for every URL and every per-client
  rate (serial 200/200; concurrent 200/200 per URL, per-client [1.0, 1.0]); `identity_rate_per_client` is
  consistent with the pooled rate; `errors = 0` everywhere;
- call counts are exactly 600 / 1200 / 1200, matching `n × repeats × clients`;
- `cross_server_identity` `1.000` and its integer form 200/200;
- `order_head` reproduces the deterministic schedule of the fixed seeds (and is identical to the 30 Oct and
  31 Oct runs, the difference being the server-readiness fix, not the schedule);
- `server_props` non-null on both URLs (build `b11669-620d2225c`, model path the pinned GGUF).

**Author decision required at STOP 1 (the operator does not decide it).** Row R1-TRACKS-S01-RERUN requires
identity "recomputed from the saved contents". The committed probe JSON is aggregate-only, but the saved
append-only server-log contents were recomputed by the independent reviewer exactly (200/200 on each tier
and 200/200 cross-server; 2/200 negative control). The author must either

- **(a)** confirm that this host-log recomputation satisfies the row — **the reviewer's recommended
  reading** — or
- **(b)** authorise an instrumented-probe pin / PLAN row so future runs carry replayable raw contents in the
  committed evidence.

The operator did not decide this, did not change the pin, and did not alter the served code.

## 3. Host state after (evidence preserved, lease free)

Verified `2026-11-09T00:36:14Z`, after `tmux kill-session -t trks_llm` (only the session this run started):

| Check | Result |
|---|---|
| `trks_llm` | gone; `trks_watch` **left running** (standard resting state) |
| `flock -n ~/r1_locks/gpu0.lock true` | **succeeds** (lease free) |
| GPU compute apps | **none** |
| `:18101` / `:18102` listeners | **none** |
| llama-server processes | **none** |
| priority markers / drill marker | all absent |
| stale `STOP` files under `$R/out` | none |
| disk `/home/dowling` | 184 G free, 90 % used (was 185 G) |

**Server-log cost:** the re-run appended **295,651,542 B** to `logs/llama_18101.log` and **194,782,610 B**
to `logs/llama_18102.log` (offsets recorded in the launch log). Grep of those new segments: **0** error/
failure lines; each server logged `offloaded 29/29 layers to GPU` + `model loaded`, and the last line is a
clean `stop: all tasks already finished`.

**Old evidence preserved (sha256 on the host, unchanged):**

| File | sha256 |
|---|---|
| `out/digits_mlp/s01/serial.json` | `65388dfaa60cc5380733dd15befec4b39c873872b01d4d5088b7ac3068d7b56a` |
| `out/digits_mlp/s01/concurrent.json` | `005cadb3a2b37cb5c7ed6d5136bcced23847fea4fd6815233a1caaf3c6a9b182` |
| `out/digits_mlp/s01_rerun_INVALID_serial_raced_server_start_20261031T112159Z/serial.json` | `93ebdcc1fa57976c6165759a20323bc8a3d209324d238d89e1d011848a29f20a` |
| `out/digits_mlp/s01_rerun_INVALID_serial_raced_server_start_20261031T112159Z/concurrent.json` | `df8612f77590bb11f1912485692124af5a8c031a44bf8cd2099cc098a8db983f` |

(mtimes unchanged at 30 Oct 03:20/03:45 and 31 Oct 04:21 PDT.)

## 4. Projection and `k` decision (Phase 1 "Done when" + R1-TRACKS-S01-RERUN clause (b))

Formula (rev 3.3 Phase 1): `hours = (C × L / k + R × t_run / c) / 3600`, with `C = 80 000` LLM calls,
`R = 60 000` worker/audit runs, `t_run = 0.9091 s` (**the Phase 0 smoke-test value for `digits_mlp`, TASL-2,
n = 77** — not re-measured and not invented), and `c = min(free cores, k × 2)`.

**Formula sanity check (reproduces the 30 Oct digits projections exactly):** with the 30 Oct `s01` JSON,
`L(k=1) = 0.644596` and `L(k=2) = mean(2.521700, 2.527256) = 2.524478`, `free = 28.7456`:
`k=1 → c=2 → 21.90 h`; `k=2 → c=4 → 31.84 h` — matching PLAN R1-TRACKS-S01-RERUN's "21.9 h at k = 1 against
31.8 h at k = 2".

**New projections** (`free = 28.7075` from the concurrent `cpu_after`; the `k × 2` cap binds both rows):

| k | L (s) | c | LLM h | CPU h | **projected total h** |
|---|---|---|---|---|---|
| **1** | 0.688309 (serial mean) | 2 | 15.30 | 7.58 | **22.87** |
| **2** | 2.728421 (mean of concurrent URL means) | 4 | 30.32 | 3.79 | **34.10** |

**`k` rule.** Both tiers pass: serial within-server identity is **100 %**; the concurrent tier has
within-server identity **100 % on both URLs** *and* `cross_server_identity` **100 %**. By the adopted
clause (b), `k` is the tier with the **shorter projected total time**:

> **`k = 1` for `digits_mlp`** — 22.87 h vs 34.10 h at `k = 2` (shorter by **11.23 h**).

This is a procedure output of the Phase 1 rule, not a scientific result. It is consistent in direction with
the 30 Oct projection (k = 1 shorter). Per the runbook, later phases use one server (port 18101) as `k` is
fixed for the node from now on, and the `k = 1` branch is what the review/author will act on at STOP 1.
`k` was **not** set by this operator outside this rule, and no Phase 2/3 work was started.

## 5. Files copied back and hashes

Copied with `rsync -a portal_zhixu:/home/dowling/r1_tracks/out/digits_mlp/s01_rerun20261109/
results/r1/tracks/digits_mlp/s01_rerun20261109/` (plus `host_logs/` for the launch log and the two probe
sessions' `.cmd`/`.log`/`.exit`). `SHA256SUMS` is committed next to them.

| File | sha256 |
|---|---|
| `serial.json` (10,495 B) | `44556b002d309393f18e3274188a4fe18ea66bd178d9c03830a094e3693131af` |
| `concurrent.json` (17,482 B) | `ec9fcb4f64429f161c71ab064305a5a0f2248afe9cad8bb09e11cc51a0f39c86` |
| `host_logs/s01_rerun_20261109_launch.log` | `2098f1244ff38ba4687257096a4c87020eda1f5c6bb13f2395260e77953649f1` |
| `host_logs/trks_s01_serial_r2.cmd` | `d7525dbdfcd66ef0ca7ca02a13e7e2055a356bae8db102cc27e1d1d1daff90e8` |
| `host_logs/trks_s01_serial_r2.log` | `718a07933d9fa4926a7c3dbc239bfd3a6a9886960075bf6485aca09b651980e1` |
| `host_logs/trks_s01_serial_r2.exit` | `e12ed9ffdd84898ee9b821317b6f4626e03d01d44689c88cbde9b931d0738ade` |
| `host_logs/trks_s01_conc_r2.cmd` | `712a0cf14e680e55e72e12998301066da01b7d18a7536943b6199ad9f0259b63` |
| `host_logs/trks_s01_conc_r2.log` | `a26849fe7b2b1a668416040ee13c891ddeff3ec38e99ed89c6d05f6323e7316e` |
| `host_logs/trks_s01_conc_r2.exit` | `e289cbd065d4807d8a14512a0de087884c14e235ec0c0a1159411a228076a731` |

Both JSON files are well under 20 MB, so nothing was gzipped.

## 6. What the independent reviewer must check (STOP 1)

1. The pin checks and the byte-identity of the installed bins (modulo the two documented fill-ins).
2. That the re-run used **new** session names and a new output dir, and that the Oct-30/31 evidence is
   unchanged (sha256/mtimes in §3).
3. That the readiness gate really preceded the serial probe (launch log, §1.1) — i.e. the 31 Oct race class
   is excluded; the invalid run's `server_props: null` + 600/600 errors vs this run's clean probes is the
   contrast.
4. `cache_prompt: false` at top level **and** in `request_example` for both files; `label: explicit`.
5. The identity integers (200/200 everywhere; cross-server 200/200), the call counts, and the per-client
   consistency; the probe-JSON-only limitation (`determinism.py:320`); the reviewer's recomputation from the
   saved append-only server-log contents at the recorded offsets (200/200 each tier, 2/200 negative
   control); and the **author decision** on whether that recomputation satisfies R1-TRACKS-S01-RERUN or an
   instrumented-probe pin is authorised.
6. The projection arithmetic and the clause-(b) `k = 1` decision — including the 30 Oct reproduction
   (21.90 h / 31.84 h) as the interpretation check.
7. The end host state: lease free, no compute app, no listener, watcher running, no markers, no STOP.

## 7. Open items / flags

- **Identity recomputation / residual question (§2.4).** The committed probe JSON is aggregate-only
  (`determinism.py:320`); the identity rates were independently recomputed by the reviewer from the saved
  append-only server-log contents at the recorded offsets (200/200 each tier, cross-server 200/200, 2/200
  negative control). **Author decision at STOP 1:** confirm the row's "identity recomputed from the saved
  contents" is satisfied by that host-log recomputation, or authorise an instrumented-probe pin for future
  committed replayable contents. Not decided by the operator.
- `k = 1` is the Phase 1 procedure output; **Phase 2/3 have not started** and no later phase is authorised
  by this report.
- TASL-7 was **not** touched tonight; no Track P, no B1.
- The Oct-30 `s01` evidence and the 31 Oct `s01_rerun_INVALID_...` directory remain preserved and are not
  superseded or deleted; this re-run is a separate tree.

## 8. Review record (STOP 1)

- **Reviewer:** fresh independent reviewer (`track-s-reviewer`), file
  `docs/r1/reviews/TRACKS_OPS_S01_RERUN_REVIEW_20261109.md` (381 lines, sha256
  `b72892dd9497ff7cfcc9ed79c79357dc5df771fd36c9fd4225eeb79fd2a7e060`).
- **Verdict: accepted** — 0 BLOCKING, 0 MAJOR, 3 MINOR. The reviewer re-derived every number, verified the
  pins / launch script / host state read-only, and recomputed identity from the server-log raw contents.
- **MINOR 1 (wording / raw contents):** answered in §2.4 and the first §7 item — the limitation is now
  stated precisely as **probe-JSON-only**, the reviewer's server-log recomputation is recorded (offsets,
  segment sizes, counts, negative control), and the author decision is put explicitly at STOP 1. (The message
  of commit `72dccc701` carries the earlier, imprecise wording; it is immutable and already pushed, so this
  report is the corrected record.)
- **MINOR 2 (pin provenance):** answered in the "Pin provenance limitation" paragraph — the probe JSON does
  not carry the paper/harness commits; the pins rest on the clean host checkouts, `trks-status`, and the
  executed code path; a future probe pin should record them in `provenance`.
- **MINOR 3 (details):** (i) the §1.1 timeline no longer claims the flock pid (it is not in the committed
  evidence); (ii) §1 now says the script guards on existing `serial.json`/`concurrent.json` (it `mkdir -p`s
  the directory); (iii) §0 now says `trks-status` is not a §11 template and matches the committed
  branch-head script (`5bd570ff…`), not the `d10b05b7` checkout (`a217f6b8…`).
