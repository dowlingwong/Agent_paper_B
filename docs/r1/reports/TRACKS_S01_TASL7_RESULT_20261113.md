# Track S `digits_mlp` S0.1 result on TASL-7 (13 November 2026) — PASS, k = 2

**Result of the reviewed operator-error re-run.** Engineering-only; this file records the measurement and the k
decision for the TASL-7 host move. Nothing here starts S0.5.

## 1. Run

- Reviewed S0.1 script `r1/tracks/ops/launch/tasl7_digits_s01_20261113.sh` @ `c1deee13…` (`S01_SUFFIX=b`), started
  2026-11-13T11:13:01Z in tmux `trks_s01_launch_b`, k=2 servers (`trks_llm`: 18101/18102, `trks-servers 2`), pin
  `8237fd02`, GGUF `509287f7…`, harness `a3fedbb`.
- serial: the `.exit` rc line is 11:19:47Z and the launch-log line 11:20:02Z; concurrent: `.exit` 11:47:13Z and
the launch-log line 11:47:17Z (the small gaps are the wrapper's post-probe bookkeeping); `S01 DONE` recorded in
  `$R/logs/s01_t7_20261113b_launch.log`; outputs `$OUT/digits_mlp/s01_t7_20261113b/serial.json` (10,493 B) and
  `concurrent.json` (17,482 B). The preserved empty `s01_t7_20261113/` was not touched.
- The 11:12Z first attempt had exited rc=2 because the host still had the pre-suffix script; the revised script was
  deployed (sha `c1deee13…`), the old `rc=2` line is kept as history, and this run is the reviewed re-run.

## 2. Measurements

| probe | URL | identity_rate | errors | n | mean (s) | p95 (s) |
|---|---|---|---|---|---|---|
| serial | 18101 | **1.0** | 0 | 600 | 0.675453 | 0.706379 |
| concurrent (2 clients/URL) | 18101 | **1.0** | 0 | 1200 | 2.717904 | 2.843610 |
| concurrent (2 clients/URL) | 18102 | **1.0** | 0 | 1200 | 2.714058 | 2.838630 |

- `cross_server_identity = 1.0`; temperature 0.2, fixed D26 seeds, `cache_prompt` recorded in the JSON.
- CPU census: 24 CPUs; load ~0.15 before serial (≈23.85 cores free) and ~1.0 after (≈22.99 free); concurrent before
  ~0.86 (≈23.14 free), after ~1.93 (≈22.07 free).
- host TASL-7; model `r1-manager`; the JSONs contain the request example and provenance (GGUF/llama build/server args).

## 2b. Projection (reported; not a gate)

Runbook rev 3.3 Phase 1 projection, with C ≈ 80,000 LLM calls, R ≈ 60,000 worker/audit runs, the smoke-test
`t_run = 0.9091 s` and `c = min(free cores, 2k)`: the k=1 estimate was ~22.6 h and the k=2 estimate ~34.0 h for the
rest of the node work. Recorded for the author; the numbers come from the reviewed Phase 1 formula, not from a
measurement of this run.

## 3. k decision

Runbook rev 3.3 Phase 1: **k = 2** because within-server identity is 100 % on both URLs **and**
`cross_server_identity` is 100 %. This overrides the earlier k=1 assumption that came from the TASL-2 S0.1
(TASL-2 had decided k=1); all later TASL-7 phases must therefore run with **k = 2 servers**, and the reviewed
TASL-7 S0.5 launch unit (written for k=1) has been revised accordingly (below) for independent review.

## 4. Next steps (no S0.5 until both reviews accept)

1. Fresh independent review of this S0.1 result (identity, cross, latency, CPU census, k=2 decision, no host
   disturbance).
2. Fresh independent review of the revised k=2 S0.5 unit (`tasl7_digits_s05_20261113.sh` now takes `K`, default 2,
   waits for both endpoints, and refuses to reuse a `trks_llm` whose live server count ≠ K). **This review has since
   been accepted**, the revised script was deployed to TASL-7 (sha `3e957464…`, `bash -n` OK) and S0.5 started at
   2026-11-13T12:25:51Z with the existing k=2 `trks_llm`.
3. Then start S0.5 with k=2 (existing `trks_llm` started with `trks-servers 2` is kept; collector on 18101; new dirs
   `s05_t7_20261113`), monitor to completion, S0.5b after stopping servers, copy-back/report/review, then pause.
4. The `_c` STOP scene and B1 remain untouched; B1 `_d` still takes priority when its D-B1R arrives (READY/origin
   polling every 30 min); TASL-2 remains unreachable (census-only if it returns).
