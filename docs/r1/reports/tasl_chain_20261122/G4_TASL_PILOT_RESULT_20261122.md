# G.4 T1 pilot on the TASL pair — result (run `g4-tasl-20261121-a`), 22 November 2026

**Verdict: PASS — all three pilot nodes completed, no STOP, nothing retried, nothing deleted, nothing pushed.** The
pilot ran from the published G.4 launch checkout `6ad899e0` on the freshly fetched published `main` `1402f466`, under
the re-issued signed note `docs/r1/authorizations/g4_t1_tasl_20261123.md`. Prepared by the G4 TASL runner (a delegated
agent, AI-assisted) under the lead's step-3 authorization; ENGINEERING_ONLY; no label, evaluation or sweep-2 file was
read. Captures (records, receipts, logs, no `out.tar`) are in `captures/` beside this file, with
`captures/MANIFEST.sha256` and `captures/pilot_totals.json`.

`check_summary` accepted all three sealed summaries (the `dates` recompute that reads them returned rc 0), each with 60
proposals and no stop. Per-node `run_median` is below the declared timeout basis on every node (no `timing` STOP);
`cache_prompt: false` on all 180 calls; `/props` identical before and after every node; no foreign compute process on
either leased GPU; both leases free after the pilot.

## 1. Inputs, checkouts and launch binding

| item | value |
|---|---|
| published `main` | `1402f466497c29638c53a3397f44ab9a3e6717ec` |
| G.4 launch commit (checkout HEAD on both hosts, detached) | `6ad899e044bd195ea1e3783578f572adf413d77a` |
| `paper_commit` (note) | `b5824240b5cc8a75bd01bf2338890e7c0af6788b` |
| spec | `sweep2/t1_tasl/g4_tasl_spec.json`, sha256 `fd9c6e9d70bfa029d2614e3e2f695c329d312a4e6d5eddb5c38fd99eba71f7c5` |
| signed note | `docs/r1/authorizations/g4_t1_tasl_20261123.md`, sha256 `89e50a9c462cf8661ba3accb777ad1dd63e193012be3caf084d1cafd8b35dfec`, copied byte-identically from `origin/main` |
| harness | `c025f89aeafc2199bf3487b4bcaa16678273c702`, clean on TASL-2 |
| run id | `g4-tasl-20261121-a` |
| TASL-2 worker GPU | `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, RTX 4090, driver `535.309.01` |
| TASL-7 proposer GPU | `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, RTX 4090, driver `580.178.04` |

The old G.4 checkout (detached at `9c2979a2`) was **moved aside, not deleted**, on both hosts, and the launch checkout
was made fresh from its objects, re-pointed at `origin`, fetched and checked out at `6ad899e0` detached:

- TASL-7: `paper_g4.old_9c2979a2_20261122T224911Z` (preserved), `paper_g4` at `6ad899e0`;
- TASL-2: `paper_g4.old_9c2979a2_20261122T225002Z` (preserved), `paper_g4` at `6ad899e0`.

`verify_launch_tasl` (decision G4-LB, rows `R1-T1-HOST-TASL`, `R1-TRACKG-G3-EARLY`, `R1-G1B-TIMEOUT`,
`R1-T1-TASL-ENV`) and `check_note` (P1–P5 PASS, run id and harness commit bound, P4 review files read from
`origin/main`) were run and **PASSed on both hosts** before and after the pilot; the import-source check resolved
`g1b_tasl`, `g1b_lib`, `g4_lib`, `s2_c2_lib` to their reviewed paths. The returned binding was
`{paper_commit: b5824240…, head: 6ad899e0…, main: 1402f466…, spec: sweep2/t1_tasl/g4_tasl_spec.json}`. TASL-2's worker
host record on `main` was `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md`, sha256
`681011b2114f6ff7db679d3265535d1cc2e8a9bdbc231371230f4de42d7b6b6d`, `host_check_items: 1-7 PASS`,
`host_check_verdict: PASS`; it is cited by P1. `captures/preflight_TASL-2.json` and `captures/preflight_TASL-7.json`
record the gate output.

## 2. Preflight (before the first job)

- **Spec pins.** `validate --launch` PASS on both hosts; projection 11.077 GPU-h ≤ cap 20.
- **Proposer binary.** `bin_manifest` of `/home/dowling/exam-x/work/llama.cpp/build-exam/bin` =
  `a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170`; `llama-server` sha256
  `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`; `--version`
  `version: 0.7.0-dev (build 1, commit 620d222)`; `ldd` resolves only inside the manifested directory
  (`ldd_outside_bin_dir: []`); GGUF sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`.
- **Tailscale resolution/bind.** TASL-7's tailscale address is `100.106.74.51` (`tasl-7.tail119748.ts.net`) and the
  server bound it; from TASL-2 the shared-node name resolves to `100.106.74.50` and reaches the listener (a temporary
  probe listener on TASL-7:8095 answered HTTP 200 from TASL-2 through both `100.106.74.50` and the name; the probe was
  stopped and port 8095 left free before the real server started). The worker read `/health` and `/props` over the
  name for every node.
- **Environments.** `uv pip freeze` equalled the census freezes: torch312 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`
  (77 packages), jax312 `80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1` (68 packages), both
  Python 3.12.16. jax312 on TASL-2: `0.4.35`, `[CudaDevice(id=0)]`; torch312: `2.6.0+cu124`,
  `cuda.is_available() True`.
- **Node pins.** canonical node-spec shas `mlab_cifar10 90c8364f…`, `mlgym_fmnist 65f229af…`,
  `mlgym_breakout_minatar db57b202…`; data manifests `mlab_cifar10 43fdf860…`, `mlgym_fmnist 24cb3448…`,
  breakout declares none (matches the spec).
- **Hosts.** Yama `ptrace_scope` 1 on TASL-2; GPUs idle and no foreign compute processes on either leased card; both
  `~/r1_locks/gpu0.lock` leases free immediately before the server and before every node.

## 3. Proposer server (TASL-7)

Command (from `/home/dowling/r1_tracks/t1_tasl/paper_g4`, the launch checkout):

```
G4_TASL_ENABLE_REAL=1 python3 sweep2/t1_tasl/g4_tasl.py serve \
  sweep2/t1_tasl/g4_tasl_spec.json --note docs/r1/authorizations/g4_t1_tasl_20261123.md --enable
```

- Held `/home/dowling/r1_locks/gpu0.lock` for its whole life (serve pid 512353; llama-server pid 512464).
- argv as pinned: `-m …/google_gemma-4-31B-it-Q4_K_M.gguf --alias gemma4_31b -c 32768 -ngl 999 -np 1 --jinja
  --chat-template-kwargs {"enable_thinking":false} --cache-type-k q8_0 --cache-type-v q8_0 --no-webui --host
  tasl-7.tail119748.ts.net --port 8095`.
- `server_record.json` sha256 `75384b7fa5ad1f970c1a85df19ec7c59f44dae8e4bf8b955d5259702f1f27daf`; started
  22:53:50Z; VRAM 21,565 MiB with the model loaded (GPU idle between calls); no foreign process before the server.
- `/props` throughout: `n_ctx 32768`, `total_slots 1`, `build_info b1-620d222`, model file
  `google_gemma-4-31B-it-Q4_K_M.gguf`; the worker re-checked it before and after each node and it did not change.
- `/health` latency probe from TASL-2: median 30.2–30.7 ms (max 32.4 ms).
- Server log cross-check: exactly **180** llama-server tasks were served (3 nodes × 60 proposals).
- Stopped with SIGTERM only after the last node finished; `server_rc 0`, `stop_signal 15`, stopped 23:42:45Z;
  `server_end.json` sha256 `9aefe27f8ec8f4ee17daf7064c16d94c2496189f69bf52561ce4d1a62259f946`; `llama-server.log`
  sha256 `f83d4436032eda33f626cf19ea445335ac806139aecfdc3b72a1abe5912ca601`; `bin_manifest.txt` sha256
  `a29c667f…`. Port 8095 free, GPU 44 MiB / 0 %, lease free after the stop.

## 4. Worker nodes (TASL-2) — command and results

Per node, under the delegated scope (`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`,
CPU affinity 0-7, fresh node log), with both keys:

```
G4_TASL_ENABLE_REAL=1 bash sweep2/t1_tasl/t1_tasl_node.sh g4 \
  sweep2/t1_tasl/g4_tasl_spec.json <node> docs/r1/authorizations/g4_t1_tasl_20261123.md \
  /home/dowling/r1_tracks/t1_tasl/records/g4-tasl-20261121-a/server_record.json --enable
```

The copied `server_record.json` (sha256 `75384b7f…`) was checked against the spec on every node. All three wrapper
runs exited 0 (`NODE_EXIT=0`); there are no `_refusals/` records under the run root. Times are TASL-2's clock
(`started_utc`–`finished_utc`); wall = the full job span (including the preflight and the post-run re-checks).

| node | env | wall (job span) | proposals | ran | kept | discarded | duplicate | refused (hunk / diff) | invalid | inert | divergent | timeline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `mlab_cifar10` | torch312 | 895 s (14 m 55 s) | 60 | 1 | 1 | 0 | 0 | 59 (53 / 6) | 0 | 0 | 0 | 22:55:20–23:10:15Z |
| `mlgym_fmnist` | torch312 | 827 s (13 m 47 s) | 60 | 11 | 8 | 3 | 1 | 48 (45 / 3) | 0 | 0 | 0 | 23:10:35–23:24:22Z |
| `mlgym_breakout_minatar` | jax312 | 1107 s (18 m 27 s) | 60 | 10 | 5 | 5 | 2 | 48 (24 / 24) | 0 | 0 | 0 | 23:24:37–23:43:04Z |
| **total** | | 2829 s (47 m 09 s) | **180** | **22** | **14** | **8** | **3** | **155 (122 / 33)** | 0 | 0 | 0 | |

"ran" counts proposals whose candidate was executed (`kept + discarded + divergent`); "refused" is
`not_run_refused` (the diff was refused before any run), split by the two refusal reasons; `duplicate` is a diff
already seen on the same incumbent. `invalid` counts replies that did not parse as the v2-diff JSON.

| node | diff liveness `ran_of_valid` | `ok_of_proposals` | throughput (proposals/h) | LLM median (s) | run median (s) | timeout basis → timeout (s) | calls | at completion cap | `cache_prompt:false` every call | GPU-h (both cards over span) |
|---|---|---|---|---|---|---|---|---|---|---|
| `mlab_cifar10` | 0.0167 (1/60) | 0.0167 | 241.6 | 15.27 | 5.59 | 13.347 → 40.041 | 60 | 0 | yes | 0.4972 |
| `mlgym_fmnist` | 0.1833 (11/60) | 0.1833 | 261.9 | 12.05 | 12.94 | 40.795 → 122.385 | 60 | 0 | yes | 0.4594 |
| `mlgym_breakout_minatar` | 0.1667 (10/60) | 0.1667 | 195.4 | 12.33 | 30.12 | 61.781 → 185.343 | 60 | 0 | yes | 0.6150 |

Per node: `run_median` is below the declared basis (5.59 < 13.347; 12.94 < 40.795; 30.12 < 61.781) — no `timing` STOP
and no timeout among the runs (`timeouts_of_proposals` 0). Executed runs (including repeats/baselines) were 4, 14 and
13; the worker's in-run GPU time was 5.6 s, 138.8 s and 303.4 s respectively, and the campaign wall was 894.1 s,
824.7 s and 1105.4 s. Prompt/completion medians: 1088/568, 1360/440, 1942/431 tokens; every prompt plus the 4096-token
completion cap fit the 32,768 context (`all_fit_ctx: true`) and no call reached the cap.

**Aggregate:** 180 proposals, 22 ran (12.22 % of proposals), 14 kept (63.64 % of ran), 8 discarded, 155 refused
(86.11 %: 122 `malformed_hunk`, 33 `malformed_diff`), 3 cross-incumbent duplicates (1.67 %), 0 inert, 0 divergent,
0 invalid, 0 timeouts. Aggregate throughput 229.45 proposals/h; 2,231.2 s of LLM time and 447.8 s of in-run GPU time;
**1.5717 GPU-h** on both cards over the nodes' spans (0.1244 GPU-h of actual worker training GPU time; 48 m 55 s of
proposer server span). The measured pilot is far under the 20 GPU-h cap (the 11.077 GPU-h projection assumed a 60 s
LLM call; the measured median was 12–15 s).

Cross-instance duplicates (G5-AUDIT input): `mlgym_fmnist` 3 groups covering 8 of 11 ran; breakout 1 group covering 2
of 10; `mlab_cifar10` none. The `dates` recompute used the resulting `dup_factor` 0.9.

**Observation for the author (not a STOP).** Diff liveness is low overall and very low on `mlab_cifar10` (1 of 60
proposals ran). The model's replies were well-formed JSON with correct-looking context lines but wrong unified-diff
hunk headers (`counts do not match its header`, e.g. `@@ -21,18 +21,25 @@` over 17 old/21 new lines), and 33 replies
had a diff-structure error (`malformed_diff`). The code's liveness STOP is exactly zero; one valid run (1/60 =
0.0167) kept the node inside the authorized threshold, so the pilot completed and the low liveness is a **measurement
to carry to the author**, not a hidden failure and not a retried attempt.

## 5. Seals (TASL-2 `sealed_g4/g4-tasl-20261121-a/<node>/attempt-1/`)

Each attempt was sealed after the server stopped with `--server-end` and `--server-log`; `sha256sum -c SHA256SUMS`
verified every sealed directory; nothing was overwritten.

```
python3 sweep2/t1_tasl/g4_tasl.py seal runs/g4-tasl-20261121-a/<node>/attempt-1 \
  sweep2/t1_tasl/g4_tasl_spec.json --node <node> \
  --server-end  records/g4-tasl-20261121-a/server_end.json \
  --server-log  records/g4-tasl-20261121-a/llama-server.log
```

| node | SEAL_RECEIPT.json sha256 | job_record sha256 | out.tar sha256 | node.log sha256 |
|---|---|---|---|---|
| `mlab_cifar10` | `190509248458d2dda81c05fe6aa7cebd88c59c74d3031a75efa83310f5052e3a` | `64fa0b0ec844a700d61fc069dcba951d1e7c7d2e57aff688fb3df5abdae7bf52` | `09566310919dee91ddcbcfcf462bffe240a928cac8337a0ef38a8ee410e54543` | `bf302025fe6578fcc8c1ac857370bbdcd06d55288ddbbf347bd5b2197d81717e` |
| `mlgym_fmnist` | `1ad040e002afc618c2e67d34a433a024e7fcf6de0aa4dbc5b3a49320d1759626` | `e22cc965ef2a8e55ec79335549cffacdcf9df11afb62cfed3eaf4c49469e2853` | `fecf36e40097d831e28568c58bd91d58d8e1449adae61f2f3ef377c9c4570c13` | `5353a3f8a240a1ca0eae2996500cfd378f7ffa935a1a25e94919726a5f9e23a8` |
| `mlgym_breakout_minatar` | `bf22fb1bfe2f4b8069192e4af309b380d6531312cb055c383ebdc4af2b693d2a` | `8b46e9c55a6b584ba64f0a4e947ebd2935086a5ea5d9e97be4fc3f2889bd19a2` | `bf19d40158996c5390c6d4583ec0e4aed04162672834c49aba93d2d06900e1bd` | `accf7c833029a652813b716d158714c4b6337e2927479f34d321a368d1ffe7f5` |

All three receipts carry the same values for the copy TASL-2 was given:
`server_record_json_sha256 75384b7f…`, `server_end_json_sha256 9aefe27f…`,
`llama_server_log_sha256 f83d4436…`; `stop: null`, `stop_class: null`, `sealed_utc 2026-11-22T23:44:24Z`.
Bare `out.tar` copies are kept on TASL-2 only (not copied into `captures/`).

## 6. R1-BX-D14 dates recompute

```
python3 sweep2/t1_tasl/g4_tasl.py dates sweep2/t1_tasl/g4_tasl_spec.json \
  sweep2/t1_tasl/g4_tasl_dates_params.json \
  sealed_g4/g4-tasl-20261121-a/mlab_cifar10/attempt-1 \
  sealed_g4/g4-tasl-20261121-a/mlgym_fmnist/attempt-1 \
  sealed_g4/g4-tasl-20261121-a/mlgym_breakout_minatar/attempt-1 \
  --today 2026-11-22
```

rc 0 (stderr empty), output saved `records/g4-tasl-20261121-a/dates_recompute.json` (sha256 `90dc8bf8…`, also
`captures/dates_recompute.json`). Basis **measured** (G.4 pilot: worker TASL-2 RTX 4090, proposer TASL-7);
`binding_K` 10; `g5_total_gpu_hours` **31.7** (K = 10; K = 6 gives 25.4) within the 230 GPU-h cap;
`rtx4090_over_census_run_ratio` 0.4546; `llm_seconds_median` 12.332 s; `ran_share_median` 0.1667;
`keep_share_median` 0.7273; `dup_factor_used` 0.9; `longest_node_gpu_hours` 7.5; dates `labels_done` 2026-11-30,
`B7` **2026-12-03** (target 2026-12-08, slack 5 d), `D3` 2026-12-29, `manuscript` 2027-01-05.

## 7. STOPs and preservation

- **No STOP of any kind.** No binding, preflight, lease, row, timing or node STOP; no retry was needed or made; no
  refusal records; nothing deleted; no `main` push; Track P untouched; the old sealed G.1b attempts
  (`sealed_g1b/…`, `runs/g1b-…`) and the old G.4 checkout are preserved. Both GPUs idle, both leases free, port 8095
  free, no `g4_tasl.py`/`llama-server`/`pilot_g4` processes left on either host after the run.
- The only same-name entry touched was `paper_g4`, which the authorization allowed to replace: the `9c2979a2`
  checkout was renamed (kept), not deleted.
- **Clock note.** TASL-2's clock read ~34 s ahead of TASL-7's during the run (observed 2026-11-22T23:43:33.9Z vs
  23:42:59.7Z); all per-node durations above are within one host's clock, and the cross-host order (server stopped
  after the last node finished) holds under that skew.

## 8. Exact paths on the hosts

- TASL-7 (`/home/dowling/r1_tracks/t1_tasl/`): checkout `paper_g4` @ `6ad899e0`; old checkout
  `paper_g4.old_9c2979a2_20261122T224911Z`; server dir
  `proposer/g4-tasl-20261121-a/server-1/{server_record.json,llama-server.log,server_end.json,bin_manifest.txt}`;
  `records/g4-tasl-20261121-a/{serve.out,serve.pid,serve_start_utc.txt}`.
- TASL-2 (`/home/dowling/r1_tracks/t1_tasl/`): checkout `paper_g4` @ `6ad899e0`; old checkout
  `paper_g4.old_9c2979a2_20261122T225002Z`; unsealed job dirs
  `runs/g4-tasl-20261121-a/<node>/attempt-1/` (with `_logs/`); sealed
  `sealed_g4/g4-tasl-20261121-a/<node>/attempt-1/`; `records/g4-tasl-20261121-a/{server_record.json,server_end.json,
  llama-server.log,dates_recompute.json,dates_recompute.err}`.

## 9. Captures beside this memo (`captures/`, 400 KB, no out.tar)

`preflight_TASL-7.json`, `preflight_TASL-2.json`, `pilot_totals.json`, `dates_recompute.{json,err}`;
`server/{server_record.json,server_end.json,llama-server.log,bin_manifest.txt,serve.out,serve.pid,serve_start_utc.txt}`;
`<node>/{job_record.json,pilot_summary.json,node.log,SEAL_RECEIPT.json,SHA256SUMS (job dir),sealed_SHA256SUMS}` for
`mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`; `MANIFEST.sha256` covers every file.
