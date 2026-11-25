# G.4b re-pilot on the TASL pair under R1-G5-DIFF-RECOUNT — result (run `g4b-tasl-20261124-a`), 25 November 2026

**Verdict: PASS — all three re-pilot nodes completed, no STOP of any kind, nothing retried, nothing deleted, nothing
pushed to `main`.** The re-pilot ran from the published G.4b launch checkout `0fc96f28` on both hosts, under the
signed note `docs/r1/authorizations/g4_t1_tasl_20261125.md` and the published `main` `912a7e02`, with the harness rule
`R1-G5-DIFF-RECOUNT` checked on `harness_g4b` before every node. The recount raises measured diff liveness from
0.1222 (G.4 strict rule) to 0.70 of proposals; the R1-BX-D14 dates **changed** against G.4's recompute and are
reported to the author, not applied. Prepared by the G.4b TASL runner (a delegated agent, AI-assisted);
ENGINEERING_ONLY; no label, evaluation or sweep-2 file was opened.

Captures (records, receipts, logs, no `out.tar`) are in `G4B_TASL_PILOT_RESULT_20261125_captures/` beside this file,
with `MANIFEST.sha256` and `pilot_totals.json`.

## 1. Inputs, checkouts and launch binding

| item | value |
|---|---|
| published `main` | `912a7e0277d7b816bc111cf90ea10f267f94d3d9` |
| G.4b launch commit (checkout HEAD, both hosts, detached) | `0fc96f28ef99e4819f1dce9e15332afe82ee3520` |
| `paper_commit` (note) | `90d4dceeef0ca603fe1ac0119aca88dd65603b26` |
| spec | `sweep2/t1_tasl/g4b_tasl_spec.json`, sha256 `56f8c293ddd3fa3bbf64b55c36f1139231c0a44631d2b5179b3e5471dcb86a1b` |
| signed note | `docs/r1/authorizations/g4_t1_tasl_20261125.md`, sha256 `df600e3f7e66ea6ea413c549812ccea11a909bb06cb82527a08f5b679d541db2`, copied byte-identically from `origin/main` |
| harness | `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98` (branch `mac-trackg-g5-7-20261124`), `g1b_pin` `c025f89aeafc2199bf3487b4bcaa16678273c702` |
| run id | `g4b-tasl-20261124-a`; projection 11.077 GPU-h, cap 20 |
| TASL-2 worker GPU | `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, RTX 4090, driver `535.309.01` |
| TASL-7 proposer GPU | `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, RTX 4090, driver `580.178.04` |
| TASL-2 host record | `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md`, sha256 `681011b2…`, compared with `g1b_pin` |

New checkouts only; `harness` (`c025f89a`), `harness_g5` (`52e3c0b0`) and `paper_g4` (`6ad899e0`) were left untouched
on both hosts, and the old G.4 checkout `paper_g4` stays where it was.

- **TASL-2:** `harness_g4b` = fresh `--no-checkout` clone of `autoresearch_harness`, fetched
  `mac-trackg-g5-7-20261124`, detached at `cbf7a003`, clean (`c025f89a` is an ancestor). `paper_g4b` = fresh clone of
  the paper repository, fetched, detached at `0fc96f28`, tracked-clean, note copied from `origin/main`.
- **TASL-7:** `paper_g4b` = same fresh clone, fetched, detached at `0fc96f28`, note copied from `origin/main`.
- `verify_launch_tasl` PASSed on TASL-2 before the nodes; the returned binding was
  `{paper_commit: 90d4dcee…, head: 0fc96f28…, main: 912a7e02…, spec: sweep2/t1_tasl/g4b_tasl_spec.json}` with the
  import-source check resolving `g1b_tasl`, `g1b_lib`, `g4_lib`, `g4_tasl`, `g5_pin_check`, `s2_c2_lib` to their
  reviewed paths (`captures/evidence/step2_smoke.log`).

## 2. Smoke checks (TASL-2, before the re-pilot)

- Harness report §10 items 1–3: `harness_g4b` HEAD `cbf7a003`, clean; `measurement_path_check` against `c025f89a`
  PASSes (308 measurement-path files, 15-file `noise_floor` closure, no engine file in it); the pytest files
  `tests/trackg/test_trackg_diff_recount.py tests/trackg/test_trackg_g4_reclassify.py` pass in **torch312** and
  **jax312** (75 passed each, 1.52 s).
- From `paper_g4b`: `g4_tasl.py harness-check` rc 0 (all three parts of the rule; added files only outside the
  measurement directories; `pilot_g4.py`, `manager_v2_diff.py`, `proposal_v2_diff.py` keep the pin's tree entries;
  `campaign_v2_diff.py` carries `trackg_diff_recount/v1`), and the strict `check-note` rc 0 (`ok: true, mode: strict,
  g4b: true, host_check_commit: c025f89a`).

## 3. Offline re-classification of G.4's refusals (§7)

`harness_g4rc` at `cbf7a003` (fresh clone, clean), `scripts/trackg_g4_reclassify.py`, G.4 sealed attempts
`sealed_g4/g4-tasl-20261121-a/*/attempt-1` verified against the captures on `ops-tasl-20261116` (archived via
`paper_g4b` so `paper_g4` stayed untouched). The run exited 0; JSON
`records/g4-tasl-20261121-a/g4_reclassify_20261124.json` (sha256
`d5a6c4bb23d2f5062f3f050a2e23f1b242b943dba45b0ac0f22ac5d17ff3e660`), schema `trackg_g4_reclassify/v1`,
`script_commit = harness_root_commit = cbf7a003`, both checkouts clean.

Expected smoke values all hold:

- `refused_before` **122 `malformed_hunk` + 33 `malformed_diff`**;
- `g4_rule_replay.matches_ledger` **155**, mismatches 0;
- `incumbent_unverified` **0**;
- `accepted_by_g4_rule` **25** with `accepted_text_unchanged` **25**;
- `with_recounted_headers` 155; `left_to_strict_parser` empty.

The measurement (`new_rule`, per step against G.4's incumbents): **applied 138, duplicate 12, refused
`context_mismatch` 5**; `by_reason` malformed_hunk → applied 110 / duplicate 12, malformed_diff → applied 28 /
`context_mismatch` 5. Per node: `mlab_cifar10` 56 applied + 3 context_mismatch; `mlgym_fmnist` 37 applied +
11 duplicate; `mlgym_breakout_minatar` 45 applied + 1 duplicate + 2 context_mismatch. As declared in `basis`, this is
a static per-step projection, not a G.4b trajectory.

## 4. Worker nodes (TASL-2) — G.4b against G.4

Per node, under the delegated scope (MemoryMax 8G, MemorySwapMax 0, CPU 0–7), from `paper_g4b`:

```
G4_TASL_ENABLE_REAL=1 bash sweep2/t1_tasl/t1_tasl_node.sh g4 \
  sweep2/t1_tasl/g4b_tasl_spec.json <node> docs/r1/authorizations/g4_t1_tasl_20261125.md \
  /home/dowling/r1_tracks/t1_tasl/records/g4b-tasl-20261124-a/server_record.json --enable
```

All three wrapper runs exited 0 (`NODE_EXIT=0`, `systemd_run_rc=0`); there are no `_refusals/` records under the run
root. Times are TASL-2's clock. Times/values are from the job records and the sealed `pilot_summary.json`.

| node | env | span (job) | proposals | ran | kept | discarded | duplicate | refused (hunk / diff / other) | invalid / inert / timeout | liveness `ran_of_valid` | `ok_of_proposals` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `mlab_cifar10` | torch312 | 1140 s (19 m 00 s) | 60 | 40 | 26 | 10 | 5 | **15** (0 / 0 / 15 `context_mismatch`) | 0 / 0 / 0 | **0.6667** | 0.6000 |
| `mlgym_fmnist` | torch312 | 1292 s (21 m 32 s) | 60 | 49 | 17 | 32 | 11 | **0** (0 / 0 / 0) | 0 / 0 / 0 | **0.8167** | 0.8167 |
| `mlgym_breakout_minatar` | jax312 | 2002 s (33 m 22 s) | 60 | 37 | 4 | 33 | 21 | **2** (0 / 0 / 2 `context_mismatch`) | 0 / 0 / 0 | **0.6167** | 0.6167 |
| **total** | | 4434 s (73 m 54 s) | **180** | **126** | **47** | **75** | **37** | **17** (0 / 0 / 17) | 0 / 0 / 0 | **0.7000** | 0.6778 |

"ran" = kept + discarded + divergent (4 divergent, all on `mlab_cifar10`); `discarded` excludes divergent. Refusals
are `not_run_refused`; the recount rule leaves no `malformed_hunk` and no `malformed_diff` refusals in G.4b — the
17 that remain are `context_mismatch` after recounting, i.e. the diff still did not apply to the incumbent.

| node | G.4 ran / 60 | G.4b ran / 60 | G.4 refused | G.4b refused | G.4 `ran_of_valid` | G.4b `ran_of_valid` | G.4 GPU-h | G.4b GPU-h |
|---|---|---|---|---|---|---|---|---|
| `mlab_cifar10` | 1 | 40 | 59 (53 / 6) | 15 | 0.0167 | 0.6667 | 0.4972 | 0.6333 |
| `mlgym_fmnist` | 11 | 49 | 48 (45 / 3) | 0 | 0.1833 | 0.8167 | 0.4594 | 0.7178 |
| `mlgym_breakout_minatar` | 10 | 37 | 48 (24 / 24) | 2 | 0.1667 | 0.6167 | 0.6150 | 1.1122 |
| **total** | 22 | **126** | **155 (122 / 33)** | **17** | 0.1222 | **0.7000** | 1.5717 | **2.4633** |

G.4 columns are from `G4_TASL_PILOT_RESULT_20261122.md`. Diff liveness is **not zero on any node** (lowest 0.6167),
so the D4 node STOP is not triggered. Timing: run medians 7.032 < 13.347, 13.014 < 40.795 and 30.441 < 61.781 s
(declared bases), so no `timing` STOP and no timeout among the runs; `cache_prompt: false` on every one of the 180
calls; every prompt plus the 4,096-token cap fitted the 32,768 context; no call reached the completion cap. The
proposer `/props` were identical before and after every node (context 32,768, one slot, `b1-620d222`, the pinned GGUF),
and the `/health` probe median was ~30.6 ms. Executed runs were 40 / 49 / 37 with in-run GPU time 283.9 / 638.4 /
1208.2 s; campaign wall totals 1137.6 / 1290.4 / 1999.6 s.

**GPU-hours.** By the G.4 convention (both cards over the nodes' spans, `2 × span / 3600`): 0.6333 + 0.7178 + 1.1122
= **2.4633 GPU-h**, under the G.4b projection of 11.077 and far under the 20 GPU-h cap. Worker training GPU time was
0.5918 GPU-h; the TASL-7 card was held 1.4339 h (server span 14:49:56–16:15:58Z).

## 5. `diff_recount` ledger check (harness report §10 item 5, after the first node and each later node)

`captures/<node>/ledger_check.json`. Every proposal line of every node's ledger carries `diff_recount` with
`rule: trackg_diff_recount/v1` (60/60 proposals per node, 180/180 total), `raw_diff_sha256` equals the sha256 of
`proposal.diff`, and where `changed` is true `runs[0].diff.diff_sha256` equals `diff_recount.applied_diff_sha256`
(no mismatch). Where `changed` is false `proposal.diff` equals `runs[0].diff.diff_text` byte for byte. `changed` true
counts: `mlab_cifar10` 41, `mlgym_fmnist` 48, `mlgym_breakout_minatar` 33 (122 of the 180 ledger texts
needed recounting; the other 58 were left as written).

## 6. Proposer server (TASL-7)

From `paper_g4b`, `G4_TASL_ENABLE_REAL=1 python3 sweep2/t1_tasl/g4_tasl.py serve sweep2/t1_tasl/g4b_tasl_spec.json
--note docs/r1/authorizations/g4_t1_tasl_20261125.md --enable`. Held the GPU lease for its whole life (serve pid
1486189; llama-server pid 1486296). `server_record.json` sha256
`cf864800d7f5e24ca3822cea11850adefbbfaaf1e3ec0e4d608abdcb7b1c5677`; `llama-server` sha256 `b70f4882…`, build
`version: 0.7.0-dev (build 1, commit 620d222)`, GGUF sha256 `2959c1b0…`, `bin_manifest` sha256 `a29c667f…`, `ldd`
resolved only inside the manifested directory. Exactly **180** llama-server slot launches were served (3 × 60).
Stopped with **SIGTERM only** after the last node: `server_end.json` sha256
`3fe5f18c4e51287ce1b211c3721758779a61de6be67051ea40e25df783a02521`, `server_rc 0`, `stop_signal 15`, stopped
2026-11-25T16:15:58Z; `llama-server.log` sha256 `ac9dff50537710ce78de1d46084d31a01815ea8a5661703612f6cca8d2eb504d`;
GPU back to idle (44 MiB), lease free, port 8095 closed.

## 7. Seals (TASL-2 `sealed_g4/g4b-tasl-20261124-a/<node>/attempt-1/`)

Each attempt was sealed after the server stopped with `--server-end` and `--server-log`; `sha256sum -c SHA256SUMS`
verified every sealed directory; nothing was overwritten, and G.4's `sealed_g4/g4-tasl-20261121-a/` receipts are
byte-unchanged (sha256 `19050924…`, `bf22fb1b…`, `1ad040e0…`).

| node | SEAL_RECEIPT.json | job_record | out.tar | node.log |
|---|---|---|---|---|
| `mlab_cifar10` | `b795b17da35b45e06c262c07902db229c45ebc9fea34ffd0a46f37f52631101c` | `9fc8e8681cd2b5d03be8c068e460c6aea72454fd0492f6322dbb353402391fa7` | `5f9c2f2a9ceb52d3448f9e69023af47e3c5af300194de646350f8b09694df48a` | `270521193929c32e7088dc1a870da0e7819e08523e8bac693c44fce6155e576f` |
| `mlgym_fmnist` | `da3a24ac83eb1fffc17844cc0c372b9fea223546bcd528ba400b2541b0724ac9` | `13d2f658ab8048a66bf96c2230901c197c6fc0123a7c949c052f4035f9558319` | `5d0b48dd23ff66bdff0472d8d7c433b942d2e2bd142a40ee0b0e1b01b3fd1ed5` | `ea037f1c245712bb68b8cd623f8bb0e3e10189cc14671acc2a45f67c534ffd77` |
| `mlgym_breakout_minatar` | `ad45f5aaca3d02f3b11f6af3e94df0b62a60afcbca5185062a9ea5369a2d2cfe` | `d475e9e5de91c4ca31d40560c369489154a999add1ebaefa0b9326caad91414d` | `8661e5b8184b40ae1c1e7a18e9c39e6cb79657a9d7331f66b1d9f6e3a099a6ef` | `7c1ed5f67dcacd7e7e048335773c8722fc18eef857c1f6f4f90a5c3866ade60c` |

All three receipts carry `stop: null`, `stop_class: null`, the same `server_record_json_sha256 cf864800…`,
`server_end_json_sha256 3fe5f18c…` and `llama_server_log_sha256 ac9dff50…`. The `dates` recompute (below) reads all
three sealed attempts, so `check_summary` accepted all three. Bare `out.tar` copies are kept on TASL-2 only (not in
`captures/`).

## 8. R1-BX-D14 dates recompute — CHANGED against G.4, reported to the author, nothing applied

Both §4/§6-step-9 commands ran from the G.4b launch checkout on TASL-2 with `--today 2026-11-25`, rc 0, stderr empty;
outputs `records/g4b-tasl-20261124-a/dates_g5.{json,err}` (sha256 `e3f6f485…`) and `dates_g4.{json,err}`
(sha256 `75f531ca…`):

| value | G.4 recompute (published) | G.4b binding, eight-node G.5 table | G.4b comparison, seven-node |
|---|---|---|---|
| `labels_done` | 2026-11-30 | 2026-12-11 | 2026-12-05 |
| `B7` | **2026-12-03** | **2026-12-14** | **2026-12-08** |
| `D3` | **2026-12-29** | **2027-01-09** | **2027-01-03** |
| `manuscript` | **2027-01-05** | **2027-01-16** | **2027-01-10** |
| slack to R1-BX-D14 target (`B7` 2026-12-08, `D3` 2027-01-03, `manuscript` 2027-01-10) | +5 d | **−6 d** | 0 d |
| `g5_total_gpu_hours` / cap / `within_cap` | 31.7 / 230 / true | 216.9 / 425 / true | 78.2 / 230 / true |
| `longest_node_gpu_hours` | 7.5 | 138.69 | 21.93 |
| `binding_K` / `ran_share_median` / `keep_share_median` / `dup_factor_used` | 10 / 0.1667 / 0.7273 / 0.9 | 10 / 0.6667 / 0.3469 / 0.9184 | same as binding |
| `llm_seconds_median` / `rtx4090_over_census_run_ratio` | 12.332 / 0.4546 | 11.83 / 0.497 | 11.83 / 0.497 |

**The dates changed against G.4's recompute** (B.7, D.3 and manuscript each +5 days; `labels_done` +5 on the
seven-node comparison, +11 on the eight-node binding). Per R1-BX-D14 (iii) this is **reported to the author before it
can be applied; nothing was applied** — no `main` edit, no commit, no push. Note for the author: the eight-node
binding now lands **6 days after** the R1-BX-D14 B.7/D.3/manuscript targets (the seven-node comparison lands exactly
on them), because the recount raises measured liveness and therefore the estimated GPU-hours of the G.5 table.

## 9. STOPs, preservation and host state

- **No STOP of any kind**: no binding, preflight, lease, harness-rule, environment, timing or node STOP; no retry was
  needed or made; no refusal records; nothing deleted; no `main` push; Track P untouched.
- The only same-name inputs touched were the launches' own **new** checkouts `harness_g4b`, `harness_g4rc` and
  `paper_g4b` on the hosts; `harness` (`c025f89a`), `harness_g5` (`52e3c0b0`), `paper_g4` (`6ad899e0`) and the old
  runs/seals (`runs/g1b-*`, `runs/g4-tasl-20261121-a`, `sealed_g1b/*`, `sealed_g4/g4-tasl-20261121-a`) are
  unchanged. `paper_g4b` is tracked-clean on both hosts (only the copied note is untracked, under `docs/`).
  `harness_g4b` carries two untracked runtime data directories created by the worker's `run_setup`
  (`nodes/mlab_cifar10/data`, `third_party/mlgym/nodes/mlgym_fmnist/data`) — the same in-run data links G.4's
  worker creates; the checkout's commit is `cbf7a003` and `harness_g4rc` is clean.
- After the run: both GPUs idle with no compute processes (TASL-2 353 MiB used, TASL-7 44 MiB), no `llama-server`/`g4_tasl.py`/`pilot_g4`
  processes, both `~/r1_locks/gpu0.lock` leases free, no `_refusals/` directory, port 8095 free.
- The §7 re-classification fetched `origin/ops-tasl-20261116` into `paper_g4b` rather than `paper_g4` (its literal
  recipe), so `paper_g4`'s refs and worktree were not touched; the capture bytes are identical.
- **Clock note.** TASL-2's clock read ~33 s ahead of TASL-7's during the run; all per-node durations are within one
  host's clock and the cross-host order (server stopped after the last node finished) holds.

## 10. Exact paths on the hosts

- TASL-7 (`/home/dowling/r1_tracks/t1_tasl/`): checkout `paper_g4b` @ `0fc96f28`; server dir
  `proposer/g4b-tasl-20261124-a/server-1/{server_record.json,llama-server.log,server_end.json,bin_manifest.txt}`;
  `logs/g4b_20261125/{serve.out,serve.pid,step4_serve_start.log,step5_stop_server.log,step6_dates.log}`.
- TASL-2 (`/home/dowling/r1_tracks/t1_tasl/`): checkouts `paper_g4b` @ `0fc96f28`, `harness_g4b` and `harness_g4rc`
  @ `cbf7a003`; unsealed `runs/g4b-tasl-20261124-a/<node>/attempt-1/`; sealed
  `sealed_g4/g4b-tasl-20261124-a/<node>/attempt-1/`;
  `records/g4b-tasl-20261124-a/{server_record.json,server_end.json,llama-server.log,dates_g5.json,dates_g4.json}`;
  `records/g4-tasl-20261121-a/g4_reclassify_20261124.json`;
  `logs/g4b_20261125/{step2_smoke.log,step3_reclass.log,step5_seal.log,step6_dates.log,ledger_check_*.json}`.

## 11. Captures beside this memo (`G4B_TASL_PILOT_RESULT_20261125_captures/`, ~540 KB, no `out.tar`)

`preflight_TASL-2.json`, `preflight_TASL-7.json`, `final_TASL-2.json`, `final_TASL-7.json`, `pilot_totals.json`,
`dates_g5.{json,err}`, `dates_g4.{json,err}`;
`server/{server_record.json,server_end.json,llama-server.log,bin_manifest.txt,serve.out,serve.pid}`;
`reclass/g4_reclassify_20261124.json`;
`<node>/{job_record.json,pilot_summary.json,node.log,attempt.json,SEAL_RECEIPT.json,SHA256SUMS,sealed_SHA256SUMS,ledger_check.json}`
for `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`;
`evidence/{step1_paper_g4b,step1_harness_g4b,step2_smoke,step3_harness_g4rc,step3_reclass,step4_serve_start,step5_seal,step5_stop_server,step6_dates,node{1,2,3}_start}.log`;
`MANIFEST.sha256` covers every file.
