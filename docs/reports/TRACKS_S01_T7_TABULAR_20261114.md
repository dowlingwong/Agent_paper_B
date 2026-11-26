# Track S `tabular_mlp` S0.1 re-run on TASL-7 (14–15 November 2026) — **PASS, k = 2**

**Result of the author-requested re-run (14 Nov amendment, relayed by the Lead).** Engineering-only; this file
records the measurement and the k decision for the TASL-7 host move. **Nothing here starts S0.5.** The STOP-3
(tabular S0.4 + drill) submission is accepted (`docs/r1/reviews/TRACKS_S04_T7_TABULAR_REVIEW_20261114.md`, 306
lines, sha256 `fbf0a874…`); this S0.1 is a separate, new measurement at k = 2.

**Authority.** Author's 14 Nov amendment (relayed by the Lead at 14 Nov ~23:2x CET): add a `tabular_mlp` S0.1
re-run at k=2 after S0.4 and before S0.5, with k fixed by measurement; runbook rev 3.3 Phase 1; the reviewed
digits TASL-7 S0.1 discipline (`reports/TRACKS_S01_TASL7_RESULT_20261113.md`, launcher
`tasl7_digits_s01_20261113.sh`); `R1-CACHEPROMPT-FALSE` (cache_prompt=false via the pinned harness).

**Pins.** paper **`8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** (clean), harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`, GGUF sha256
`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`; `trks-status` OK. Launcher
`r1/tracks/ops/launch/tasl7_tabular_s01_20261114.sh` sha256
**`0f3d05befb05d7736e39fd9704906218371f1228b8f48a5450f9ab8e265fa520`** (committed; deployed byte-identical to
`$R/launch/`, `bash -n` OK). Session names `trks_s01t_serial`/`trks_s01t_conc` (deliberately distinct from the
digits S0.1's `trks_s01_serial`/`trks_s01_conc`, whose log files are digits evidence).

## 1. Run

- Servers: k = 2 in tmux `trks_llm` via `trks-servers 2`; started **2026-11-14T23:11:05Z**; exactly **2 live
  llama-server procs** (pids **817988**, **817989**; `trks-servers` starts 18101 first, so the natural mapping is
  817988=18101 / 817989=18102 — stated as **inferred from start order**; no saved `ps` capture was kept, so the
  mapping is not claimed as measured); both `/v1/models` ready at 23:11:18Z.
- **Server-log offsets recorded for identity recomputation** (append-only `logs/llama_1810{1,2}.log`):
  `OFFSET_START 2026-11-14T23:11:05Z llama_18101=1013600752 llama_18102=398591403`; launcher start
  23:11:18Z (`1014105122` / `399095773`); `OFFSET_END 23:47:41Z llama_18101=1316952707 llama_18102=598535821`.
  The probes' full requests/responses lie in those byte ranges.
- Launcher started 23:11:18Z (`S0.1 start (node tabular_mlp, host TASL-7, k=2 probe period, pin 8237fd02)`).
- **serial**: 23:11:18Z → `trks_s01t_serial.exit` **23:18:18Z rc=0** (data 200 prompts × 3 repeats, order-seed 1);
  output `serial.json` (10511 B, sha `db72234e…`).
- **concurrent**: 23:18:18Z → `trks_s01t_conc.exit` **23:46:26Z rc=0** (clients-per-url 2, order-seed 2); output
  `concurrent.json` (17499 B, sha `8bca98b5…`).
- **`S01 DONE`** in `logs/s01_t7_20261114_launch.log` at 23:46:34Z. `cache_prompt=false` (explicit, label
  `explicit`) in both JSONs; temperature 0.2; `manager_proposal/v1`.

## 2. Measurements

| probe | URL | identity_rate | errors | n | mean (s) | p95 (s) |
|---|---|---|---|---|---|---|
| serial | 18101 | **1.0** | 0 | 600 | 0.698037 | 0.740035 |
| concurrent (2 clients/URL) | 18101 | **1.0** | 0 | 1200 | 2.812054 | 2.994973 |
| concurrent (2 clients/URL) | 18102 | **1.0** | 0 | 1200 | 2.806924 | 2.977901 |

- **`cross_server_identity = 1.0`**; per-URL `cross_client_identity = 1.0` in the concurrent probe; serial has a
  single URL (`cross_server_identity = null`). `order` seeds 1 (serial) / 2 (concurrent), rule "every (prompt,
  repeat) once, shuffled".
- **CPU census:** 24 CPUs; serial before loadavg 1 m 0.2246 → 23.78 free cores, after 1.1138 → 22.89 free;
  concurrent before 1.1045 → 22.90 free, after 2.0054 → 21.99 free.
- Provenance in both JSONs: GGUF `509287f7…`, llama build `620d2225…`, full `server_args` (18101 single /
  18101|18102 concurrent), host `TASL-7`, label `ENGINEERING_ONLY`.

## 3. k decision

Runbook rev 3.3 Phase 1: **k = 2**, because **within-server identity is 100 % on both URLs** (concurrent 18101
and 18102 = 1.0; serial 18101 = 1.0) **and `cross_server_identity` is 100 %** (1.0). This fixes k = 2 for
`tabular_mlp` on TASL-7; it overrides the earlier k = 1 assumption (which came from the TASL-2 digits S0.1 /
the STOP-1 decision (a) reading). **No k = 1 fallback is used.** The author's rule is explicit: **any identity <100 % in any
required cell is a STOP for the author** (recorded in the earlier S0.4 STATUS entry and the S0.1 launcher header); whether
another k attempt or host is chosen is the author's decision. All later tabular phases on TASL-7 must run
**k = 2 servers**.

## 4. Host end state

Servers stopped after the probes: **lease FREE**, 0 llama-server, no `trks_llm`, compute apps empty, **0**
listeners on 1810x, only `trks_watch`; no markers; **0 STOP** under `$R/out`; GPU idle (0 %, 243 MiB).

## 5. Copy-back (never TASL-2)

`results/r1/tracks/tabular_mlp/s01_t7_20261114/`: `serial.json`, `concurrent.json`, `host_logs/`
(`s01_t7_20261114_launch.log` incl. the `OFFSET_START`/`OFFSET_END` lines, `trks_s01t_serial.{cmd,log,exit}`,
`trks_s01t_conc.{cmd,log,exit}`) and `operator_capture/` (`s01_waiter.log`). **`SHA256SUMS` verifies 10/10;
host==copy verified for all 9 JSON/log files.** TASL-2 is **down** (TCP timeout) and was not touched; its
bare-repo push remains deferred.

## 6. Scope / next

- New `out/tabular_mlp/s01_t7_20261114` (S0.1 writes only `--out`; **no scratch dir was created**); the Oct-30 `s01`/INVALID scenes
  and the digits S0.1 logs were not touched. The reviewed STOP-3 record (`fbf0a874…`) remains accepted; this
  S0.1 submission awaits its own fresh independent review.
- **§3.0b Track P integration check: OPEN** (not performed; gates Phase 6 / 0.3(c), not this S0.1).
- B2 hand-off draft is **NOT ARMED**; no `trackx_evidence.active`. TASL-2 down/deferred. No B2/X.7/sweep 2.
- **No S0.5 until the S0.1 review accepts**; then S0.5/S0.5b at **k = 2**.

## 7. Reviewer checklist

1. Pins/clean; launcher sha `0f3d05be…` repo==host, `bash -n`; k=2 servers, exactly 2 procs; offsets recorded.
2. Serial rc=0 (23:18:18Z), concurrent rc=0 (23:46:26Z), `S01 DONE` 23:46:34Z; `cache_prompt=false`.
3. Identity 1.0 on 18101 serial, 18101/18102 concurrent; `cross_server_identity` 1.0; errors 0; n 600/1200.
4. Latency/CPU census as tabulated; host end state idle.
5. Copy-back `SHA256SUMS` 10/10, host==copy 9/9; old scenes + digits logs untouched; TASL-2 untouched.
6. **k = 2** by measurement; no k=1 fallback; no S0.5 until this review accepts; §3.0b OPEN; B2 not armed.
