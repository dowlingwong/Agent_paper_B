# G.1b TASL-2 run — `g1b-tasl-20261121-b` (result memo)

**Status: EVIDENCE (execution record, hash-bound) — NOT a valid 4-node G.1b row.** This memo records what the
authorized run did on TASL-2 and what it sealed. It is not a release-grade D21 noise-floor result: `mlgym_fmnist`
STOPped on a data-manifest mismatch, so the G.1b four-node row is **incomplete (3 of 4 nodes)**.

- **Label:** `ENGINEERING_ONLY` — the spec label, and every `job_record.json` in this run carries
  `"label": "ENGINEERING_ONLY"`; `output_use`: "ENGINEERING_ONLY G.1b noise floor (D21) on the TASL pair; no labels read".
- **Run id:** `g1b-tasl-20261121-b` · **host:** TASL-2 (`ssh portal_zhixu`) · **run root:** `/home/dowling/r1_tracks/t1_tasl`
- **Launch checkout:** `/home/dowling/r1_tracks/t1_tasl/paper_launch` @ `985dd45d90e5a0183a31a149886bd0f1cc233699`
  (HEAD **unchanged** before/after; tracked-clean; `origin/main` advanced by the lead's per-node fetches to
  `adeccc29…` then `9c2979a2…`, which is what `NODE_START … main=…` lines record).
  Harness `/home/dowling/r1_tracks/t1_tasl/harness` @ `c025f89aeafc2199bf3487b4bcaa16678273c702`.
- **Spec:** `paper_launch/sweep2/t1_tasl/g1b_tasl_spec.json`, sha256 `060aac91ba452a69e4e898b66b92ebd5bfc0887c2933cfd2e438d93d17ecb465`
  (460 runs/node; 30 seeds per condition; cap 100 GPU-h; `timeout_on_4090: STOP`).
- **Nodes, in order:** `mlab_ogbn_arxiv` (GPU), `mlgym_fmnist` (GPU), `mlab_imdb` (GPU), `mlgym_houseprice` (CPU, cpus 8-15).
- **TASL-7:** not part of this four-node run, not touched by this monitor (**P7 PENDING**); this memo makes no claim about TASL-7.
- **Monitor:** read-only; 5-minute polls 21:49:05Z → 04:06:49Z (77 polls); no job started, retried, stopped or modified; no
  deletion; no push; `TASL-7` untouched; lease probed with `fuser` only.

---

## 1. Outcome at a glance

| | |
|---|---|
| Run finished | `DONE_AFTER_FMNIST 2026-11-22T04:03:59Z` (status file) |
| Run window | 2026-11-21T21:45:28Z → 2026-11-22T04:03:59Z = **6 h 18 m 31 s** (16 h limit not reached) |
| Sealed nodes | `mlab_ogbn_arxiv` ✅, `mlab_imdb` ✅, `mlgym_houseprice` ✅ (one attempt each, `sha256sum -c SHA256SUMS` rc=0) |
| STOP | `mlgym_fmnist` ❌ — data-manifest sha256 mismatch, 0 runs written, **not sealed** (2 infrastructure attempts; see §3) |
| Runs | 1 380 of 1 840 expected (460/460/460/0 across the three sealed nodes; 0 for fmnist) |
| Divergent rows | 0 (all three sealed nodes: `successful == written == expected == 460`, `divergent == 0`) |
| Determinism gate | passed on all three sealed nodes (`deterministic: true`, `divergent_configs_at_default: []`) |
| GPU-hours used | **5.5506 h** of the 100 GPU-h cap (5.6 %); includes the 46 s fmnist lease. `sha256sum -c` rc=0 everywhere |
| CPU core-hours | **5.1489 core-h** (`mlgym_houseprice`, wall 0.6436 h × 8 cores, affinity 8-15) |
| Timeout STOPs | none (`stop_kind`/`stop_class` `timing` never occurred) |

## 2. Per-node results

`runs` = expected/written/successful/divergent. Wall/GPU-h from `job_record.json` `started_utc`/`finished_utc`.

| node | host / device | attempt | sealed | runs e/w/s/d | started → finished (UTC) | wall | GPU-h (lease) / core-h | stop_class | `sha256sum -c` (sealed / runs) |
|---|---|---|---|---|---|---|---|---|---|
| `mlab_ogbn_arxiv` | TASL-2 / gpu RTX 4090 | attempt-1 | **yes** | 460/460/460/0 | 21:45:28 → 22:41:03 | 55 m 35 s | 0.9264 GPU-h | `null` | rc=0 / rc=0 |
| `mlgym_fmnist` | TASL-2 / gpu RTX 4090 | attempt-1 | no | — (0 written; default rc=3) | 22:42:03 → 22:42:49 | 46 s | 0.0128 GPU-h | `infrastructure` | — / rc=0 |
| `mlgym_fmnist` | TASL-2 / gpu RTX 4090 | attempt-2 | no | — (0 written; default rc=3) | 22:42:50 → 22:42:50 | 0 s | 0.0000 GPU-h | `infrastructure` | — / rc=0 |
| `mlab_imdb` | TASL-2 / gpu RTX 4090 | attempt-1 | **yes** | 460/460/460/0 | 22:48:40 → 03:25:21 | 4 h 36 m 41 s | 4.6114 GPU-h | `null` | rc=0 / rc=0 |
| `mlgym_houseprice` | TASL-2 / cpu cpus 8-15 | attempt-1 | **yes** | 460/460/460/0 | 03:25:22 → 04:03:59 | 38 m 37 s | 0.6436 h → **5.1489 core-h** | `null` | rc=0 / rc=0 |
| **total** | | | 3 sealed | 1380/1380/1380/**0** | | 6.31 h | **5.5506 GPU-h** | 1 STOP | |

Parts (all four parts `expected/written/successful`, all `rc=0`):

| node | default | train | split | joint | determinism |
|---|---|---|---|---|---|
| `mlab_ogbn_arxiv` | 10/10/10 | 150/150/150 | 150/150/150 | 150/150/150 | deterministic, no divergent configs |
| `mlab_imdb` | 10/10/10 | 150/150/150 | 150/150/150 | 150/150/150 | deterministic, no divergent configs |
| `mlgym_houseprice` | 10/10/10 | 150/150/150 | 150/150/150 | 150/150/150 | deterministic, no divergent configs |
| `mlgym_fmnist` | 10 expected, **0 written**, stop | — | — | — | — |

Per-run timing (from each record's `timing[]`, `c0_median_wall_s`, measured 4090/Ada ratio):
arxiv 3.87-3.92 s (ratio 0.684-0.694); imdb 36.32-36.49 s (ratio 0.566-0.569); houseprice 4.80-4.87 s
(ratio 0.949-0.963). Per-node run timeout basis (`census_slowest_x3`): arxiv 21.8→65.4 s, imdb 65.156→195.47 s,
houseprice 6.794→20.38 s, fmnist 40.795→122.39 s. No timeout was reached.

## 3. STOPs — exhaustive (verified: no STOP except as recorded)

`status` file (`logs/g1b_tasl2.status`) final content:

```
STOP mlgym_fmnist try=1 class=missing
STOP mlgym_fmnist try=2 class=infrastructure
DONE_AFTER_FMNIST 2026-11-22T04:03:59Z
```

1. **Recorded, non-final refusal (no attempt created), 22:41:03Z** — `STOP: fetch published main before launch; local
   origin/main differs or could not be verified` (`stop_class` reported as `missing` because no `job_record`/attempt
   exists; node log `…/mlgym_fmnist-20261121T224103Z-3326850.node.log`, `NODE_EXIT=2`). This is the
   `verify_launch_tasl` binding: `git ls-remote origin refs/heads/main` must equal the locally fetched `origin/main`
   (`g1b_tasl.py:976`). The lead fetched `origin/main` and relaunched the remaining nodes with fetch-before-node
   (`run_g1b_rest.sh`, then `run_g1b_after_fmnist.sh`); this refusal spent no runs and no attempt.
2. **Data-manifest STOP, `mlgym_fmnist` attempt-1 (22:42:03→22:42:49Z) and attempt-2 (22:42:50→22:42:50Z)** —
   `stop_class: infrastructure`, part `default` `rc=3`, `successful_rows=0`, `written_rows=0`. Exact text:
   `STOP: mlgym_fmnist part default: NoiseFloorStop: STOP: data manifest sha256 24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32 differs from the census 8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c (the data bytes differ from the census data)`.
   The job's setup had just (re)generated `/home/dowling/r1_tracks/t1_tasl/data/mlgym_fmnist`
   (`out/setup.log`: "wrote … data_manifest.json sha256 24cb3448…", HF generation of train/test splits; manifest
   `source.dataset=zalando-datasets/fashion_mnist`, `source.datasets=3.6.0`,
   `source.revision=531be5e2ccc9dba0c201ad3ae567a4f3d16ecdd2`). The census expected `8d28287b…`.
   Per the lead's cross-check (TASL-2 + a separate TASL-7 MLGym cross-check): the manifest differs **only** in
   `source.datasets` (`3.6.0` on TASL vs `5.0.1` recorded by the census) while the four `.npy` sha256/bytes match.
   The lead decided **not to fix or fake the data**, so `mlgym_fmnist` is an authored data-provenance STOP.
   **No seal** (the wrapper seals only `rc=0`), so there is no `SEAL_RECEIPT.json` for this node; both attempts' records
   and sums are preserved unsealed in the runs tree and captured as evidence (§6).
   The monitor did not retry or start anything; the second attempt was the runner's own single permitted
   `infrastructure` retry.
3. Nothing else: no `STOP_FETCH`/`STOP_SEAL`, no `timing` STOP, no refusal after 22:43Z, no node-level STOP on the
   other three nodes (`stop: null` in their records).

## 4. Seal receipts and sha256s

`sha256sum -c SHA256SUMS` was run **on the host in the sealed directory and in the runs attempt directory** for each
sealed node (both rc=0; output captured in `_harvest/remote_harvest.txt`). The local copies were independently
re-hashed and match the remote values.

| node / attempt | `SEAL_RECEIPT.json` sha256 | `job_record.json` sha256 | `SHA256SUMS` sha256 | `node.log` sha256 | `out.tar` sha256 (not copied) | sealed_utc |
|---|---|---|---|---|---|---|
| `mlab_ogbn_arxiv` attempt-1 | `76000bae7c967174539c868851fa4397c768c2e25d871c4c08466db6edebda63` | `45583b2717b1b0817c4e2c1e5cec7202a47b718b4ffd4d52e71dc66b249c0cac` | `88677a1af994929f539e110e5c84197286ceb4a8295102f2984403aea2e53bcf` | `9745777e43cc57140e3b4574430f26880f392f8ad622c9e2692d621ef67c236e` | `04f2d0c73b0d1e510e8fe1998581814e1d6ce73cbc1d402efae22e6b19681386` | 22:41:03Z |
| `mlab_imdb` attempt-1 | `afc4445c1e4f11d7da52a23c378fb27b4b1c143c0d07f15f93a08c955d1956e5` | `4468021ac41507b4a9161746e8f178d0ae98c938e18e3b91167d1d806d3c4eae` | `8415daa8a0f722aae737607ac1790cd1bbc38c5a4c71ec806e177e82e9e141e5` | `a93d63f33fd9be93053ec1092d89e89c1951eae5d8d16be4832bec95e238df59` | `0faf572dc7bad127bdc3557d74159c66bf357fb325e8608039af1a57eeeaebc7` | 03:25:21Z |
| `mlgym_houseprice` attempt-1 | `1f1b6f8393414a88805c4a7cce3c10cd1c65af6d0ce5d81fdb3fb061306b7fd8` | `15b7beea61f7829d396a9aa0415462e80c3aabd6c62c9c3327b2528af2a690aa` | `0109ecc20bae3c70965060cafa9e41e772c4b069199f61cae22f4835a71e0695` | `701d1435438fe8b42fec92c6c0e475a06fe62dacc212dbd12bbcfe9c554803c0` | `2588cd305aee352febdc708522ec368fc70cb3d703d2d184612df4d2bea2e0d1` | 04:03:59Z |

Each receipt binds its record and node log: `receipt.job_record_sha256`/`receipt.node_log_sha256` equal the file
hashes above (cross-checked locally, all OK); every receipt has `stop: null`, `stop_class: null`, and the same
`run_id`/`host: TASL-2`.

`mlgym_fmnist` (STOP — **no seal receipt**, unsealed attempt records preserved and captured):
attempt-1 `job_record.json` `8c2fe155102bb7621846fb0a7551b5b5b16184aa09b64298af3bacea277b2f51`,
`SHA256SUMS` `74c4f9bb9e080b33f73d840617c4fd768255c2603ef9b869902b3383db811ac5`;
attempt-2 `job_record.json` `571b540394ad69422655cddc29caff4e5413df885ba5f4a73e8715ca501540f4`,
`SHA256SUMS` `75dabbc78affa8e94dfa2a16331f60814ddb469f02831e9b9d7ffe44ea3caafa`; both `sha256sum -c` rc=0.

## 5. Exact commands used (from the captured runner scripts and logs)

```bash
# launch: run_g1b_tasl2.sh (first runner), log start 2026-11-21T21:45:28Z HEAD=985dd45d90e5a0183a31a149886bd0f1cc233699
export G1B_TASL_ENABLE_REAL=1
for N in mlab_ogbn_arxiv mlgym_fmnist mlab_imdb mlgym_houseprice; do
  bash "$P/sweep2/t1_tasl/t1_tasl_node.sh" g1b "$SPEC" "$N" "$NOTE" --enable
  A=$(ls -dt "$B"/runs/g1b-tasl-20261121-b/"$N"/attempt-* | head -1)
  "$TORCH312/bin/python" "$P/sweep2/t1_tasl/g1b_tasl.py" seal "$A" "$SPEC" --node "$N"
done
# with P=/home/dowling/r1_tracks/t1_tasl/paper_launch, SPEC=$P/sweep2/t1_tasl/g1b_tasl_spec.json,
#      NOTE=$P/docs/r1/authorizations/g1b_t1_tasl_20261121.md, B=/home/dowling/r1_tracks/t1_tasl

# t1_tasl_node.sh inner command (verbatim from the captured wrapper), inside the delegated user scope:
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  env T1_CPUS="$CPUS" T1_PY="$PY" T1_LOG="$LOG" bash -c '
    CG=$(sed -n "s/^0:://p" /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
    export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" G1B_TASL_NODE_LOG="$T1_LOG"
    unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
    taskset -c "$T1_CPUS" "$T1_PY" "$@"' t1_tasl "$HERE/g1b_tasl.py" \
    run-node "$SPEC" --node "$N" --note "$NOTE" --enable

# engine, one process per part (observed in ps; CUDA_VISIBLE_DEVICES="" with explicit --gpu-uuid):
"$HARNESS_ENV_PYTHON" -m autoresearch.trackg.noise_floor --chunk "$A/out/chunk_<part>.json" \
  --harness-root /home/dowling/r1_tracks/t1_tasl/harness --out "$A/out/<part>" \
  --gpu-uuid GPU-4d623e76-7587-ee15-a633-46f60d220d94          # GPU nodes only

# restarts after the fmnist STOP (lead), each with fetch-before-node; both preserved fmnist attempts/records:
cd "$P" && git fetch -q origin main
# run_g1b_rest.sh      : for N in mlgym_fmnist mlab_imdb mlgym_houseprice   (22:42:03Z; fmnist STOPped, exited)
# run_g1b_after_fmnist.sh : for N in mlab_imdb mlgym_houseprice             (22:48:39Z; both sealed, DONE_AFTER_FMNIST)

# verification used by this monitor (read-only):
cd <sealed_root>/g1b-tasl-20261121-b/<node>/attempt-1 && sha256sum -c SHA256SUMS
cd <runs_root>/g1b-tasl-20261121-b/<node>/attempt-1   && sha256sum -c SHA256SUMS
fuser /home/dowling/r1_locks/gpu0.lock            # lease held?  (held by the node job on GPU nodes; free on CPU node)
nvidia-smi --query-compute-apps=pid,process_name,used_memory,gpu_uuid --format=csv,noheader
tail -n 15 logs/g1b_tasl2_20261121.log ; tail -n 8 runs/g1b-tasl-20261121-b/_logs/<node>-<utc>-<pid>.node.log
scp portal_zhixu:<attempt>/{job_record.json,SEAL_RECEIPT.json,SHA256SUMS,node.log} <captures>/<node>/<attempt>/
```

## 6. Evidence (small files only — `out.tar` and the `out/` tree were **not** copied)

Capture directory (Mac ops worktree):
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116/docs/r1/reports/trackg_g0_20261117/G1B_TASL2_RESULT_20261121_captures/`

| path | contents |
|---|---|
| `mlab_ogbn_arxiv/attempt-1/` | sealed `job_record.json`, `SEAL_RECEIPT.json`, `SHA256SUMS`, `node.log` |
| `mlab_imdb/attempt-1/` | sealed `job_record.json`, `SEAL_RECEIPT.json`, `SHA256SUMS`, `node.log` |
| `mlgym_houseprice/attempt-1/` | sealed `job_record.json`, `SEAL_RECEIPT.json`, `SHA256SUMS`, `node.log`, `attempt.json` |
| `mlgym_fmnist/attempt-1/`, `attempt-2/` | unsealed `job_record.json`, `SHA256SUMS`, `attempt.json`, `out_info/{out_setup.log,out_engine_default.log,out_default_chunk_record.json,out_chunk_default.json}` |
| `_run/` | `run_g1b_tasl2.sh.txt`, `run_g1b_rest.sh.txt`, `run_g1b_after_fmnist.sh.txt`, `g1b_tasl2_20261121.log.txt`, `g1b_tasl2.status.txt`, `node_logs_all.txt`, `runs_extra_listing.txt` |
| `_node_logs/` | all six `_logs/<node>-<utc>-<pid>.node.log` wrapper logs |
| `_harvest/remote_harvest.txt` | per-node remote paths, `sha256sum -c` output+rc, remote sha256s |
| `_monitor/` | `poll_loop.sh`, `harvest_collect.sh`, `summarize.py`, `polls.log` (77 polls, full snapshots), `timeline.tsv`, `verdict` |

Integrity: every captured `job_record.json`/`SEAL_RECEIPT.json`/`SHA256SUMS` local sha256 equals the remote
`sha256sum` value, and every receipt's `job_record_sha256`/`node_log_sha256` matches the captured files
(**all cross-checks PASS**). `sha256sum -c SHA256SUMS` rc=0 on the host for all three sealed directories *and* all
five runs attempt directories (including the two unsealed fmnist attempts).

## 7. Timeline (UTC)

| time | event |
|---|---|
| 21:45:28 | run starts at HEAD `985dd45d`; `mlab_ogbn_arxiv` begins (lease held) |
| 22:41:03 | `mlab_ogbn_arxiv` sealed (460/460) |
| 22:41:03 | `mlgym_fmnist` try=1 refused before any attempt (`origin/main` not freshly fetched), rc=4, no attempt |
| 22:42:03 / 22:42:49 / 22:42:50 | lead restarts (`run_g1b_rest.sh`, fetch-before-node); fmnist attempt-1 STOP, attempt-2 STOP (data manifest) |
| 22:48:39 | lead starts `run_g1b_after_fmnist.sh` (imdb + houseprice only; fmnist preserved) |
| 22:48:40 | `mlab_imdb` begins (lease held) |
| 03:25:21 | `mlab_imdb` sealed (460/460) |
| 03:25:22 | `mlgym_houseprice` begins (CPU, no GPU lease — lease free, as expected) |
| 04:03:59 | `mlgym_houseprice` sealed (460/460); `DONE_AFTER_FMNIST` written to status |
| 04:06:49 | monitor's 77th and last poll sees the terminal status; monitoring ends |

## 8. Monitor method and per-poll data

Read-only throughout. One SSH snapshot every 5 minutes (~77 polls) captured: the `status` file content (or its
absence), current node + attempt (from `NODE_START` events and the `attempt-N` dir + `attempt.json`), per-part row
progress (`default/train/split/joint`), the `_logs/*.node.log` tail, `nvidia-smi --query-compute-apps` and GPU
utilisation, and whether the GPU lease `/home/dowling/r1_locks/gpu0.lock` was held (`fuser`). Observed throughout:
the lease was held by the node job only during GPU nodes (CPU node: free — expected); the only GPU compute process
in every sample was the run's own `envs/torch312/bin/python` — no foreign/shared-card process was observed. Nothing
was started, retried, stopped, deleted or pushed by the monitor.

**Cap check:** GPU-hours 0.9264 (arxiv) + 4.6114 (imdb) + 0.0128 (fmnist aborts) = **5.5506 h ≤ 100 GPU-h** (5.6 %).

## 9. What this does and does not establish

- **Establishes (EVIDENCE):** on TASL-2, `mlab_ogbn_arxiv`, `mlab_imdb` (GPU) and `mlgym_houseprice` (CPU) each
  completed all 460 declared runs with 0 divergent rows, passed the determinism gate, and sealed hash-bound attempts;
  `mlgym_fmnist` STOPped before producing any row on a data-manifest mismatch that is a `source.datasets`
  provenance difference, not a run failure; no timeout STOP occurred; the run used 5.55 of 100 GPU-h.
- **Does not establish:** a complete G.1b four-node row (fmnist has no runs) or any cross-host/release-grade D21
  statement. The fmnist data-provenance question is an author decision (census manifest `8d28287b…` vs locally
  generated `24cb3448…`); nothing was fixed, faked, retried or deleted to work around it.
