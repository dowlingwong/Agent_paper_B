# G.1b autoresearch run — `autoresearch_fixedtokens` on TASL-2, run `g1b-ar-tasl-20261122-a` — read-only monitoring and result (24 November 2026)

**Result: DONE, SEALED, PASS — no STOP.** The authorized autoresearch G.1b run `g1b-ar-tasl-20261122-a` ran on
TASL-2 from **2026-11-22T23:49:30Z** and finished **2026-11-24T04:56:35Z** — wall **29 h 07 m 04 s = 104 824 s =
29.1178 h** (29.104 GPU-h of measured run wall; projection 28.227, measured/projection 1.032). It wrote
**460 expected / 460 written / 460 successful / 0 divergent**, ran the parts **default / train / split / joint**
(all `rc 0`, `stop: null`), passed the determinism gate, met the harness-isolation gate on **every part and every
one of the 460 rows** (`effective: true`, `waivers {}`, `exceptions []`), and was **sealed** with seal rc 0 and
`sha256sum -c` rc 0 in both the sealed and the runs attempt directories. `stop: null`, `stop_class: null`;
**no author STOP of any class** occurred (no node, timing, lease, foreign-GPU, harness, environment, data-manifest or
cap STOP). ENGINEERING_ONLY; no label or evaluation file was read. Nothing was launched, retried, stopped or
modified; nothing was deleted or pushed; **TASL-7 was held — no launch** — and the G.1b note2 (TASL-7) path was not
touched.

The run was watched **read-only** by the DeepSeek Harness agent `ar-g1b-monitor` (delegated by the lead): one poll
every 10 min (2 min in the last part), 187 in-run polls, **no writes on the host**. This memo and its captures are
written uncommitted on the Mac ops worktree `ops-tasl-20261116` (HEAD `9eafa66d` at write time); nothing was
committed or pushed.

## 1. Monitoring (what was done, and what was not)

- **Watched, never touched.** Polls read only `logs/ar_g1b_tasl2.{log,status}`, the attempt tree, the sealed tree,
  `nvidia-smi`, the lease file and `pgrep`. No job was started, retried, stopped or modified; no file on TASL-2 was
  created or changed by the watcher.
- **Cadence.** 189 `POLL` lines: one test poll at 2026-11-22T23:55:48Z plus **187 in-run polls** at 600 s, switching
  to 120 s once `joint` reached 140/150 written rows; detection on the file `logs/ar_g1b_tasl2.status`, which the
  authorized driver writes only at the end. Last poll: 2026-11-24T04:58:24Z, `status=DONE`, `sealed=5` files,
  `SEAL_RC rc=0`; the watcher exited at 04:57:48Z local (≈04:58:34Z host) with `reason=done` after harvesting.
- **One transient network hiccup, no run impact.** 5 consecutive SSH poll failures 2026-11-23 09:02:59Z–09:04:24Z
  (logged `SSHFAIL`, alerted); polls resumed at 09:06:02Z and the run was unaffected (train part proceeded
  normally). No other poll failure.
- **No premature exit.** The watcher never saw `STOP` or a second attempt: exactly **attempt-1**, one sealed
  attempt, no `attempt-2`.
- Watcher artifacts: `inputs/monitor_poll.log` (sha256 `2d5875800c06473ddb339269a44b45e147bd34a2fe22d4f072424d9e189429fd`),
  `inputs/monitor_summary.log` (sha256 `468d9d67af14a55c531979bb9306b296ce6517c7f846b2f544b633e3d4dca96b`),
  `inputs/monitor_notes.txt`, `inputs/monitor_harvest_info.txt`; scripts `monitor.sh`
  (sha256 `5fee7603746fc6fd3e2617b2ad779b59ae4b8210c5649d14927ef25d244cbe37`) and `harvest2.sh`
  (sha256 `e04c17011204dccb8ec56fb58ed7f99bec87f40a70ae6e4f000c44ca8284b525`) are in the monitor workspace
  (`/Users/wongdowling/Documents/agent_paper_B/.tmp_ar_g1b_monitor/`).

## 2. Authority and launch binding (verified before and after the run)

The launch is the one authorized by the third G.1b note (R1-G1B-NOTE2-DECISIONS, NOTE2-AR A) with its own
autoresearch-only spec; the binding was captured read-only at 2026-11-22T23:54:47Z (pre-run baseline,
`inputs/baseline_initial_state.txt`, sha256
`e92565ea01bdb08a2549f265286b5d381d512738b04e9ec03cfeba2b2551738b`) and re-checked at 2026-11-24T05:04Z
(`inputs/final_verify.txt`, sha256 `1ffb406de9086424dc75012a481e97d9a433aeedf7203444891347dcdafd48df`).

| item | value |
|---|---|
| Host | TASL-2, uid 1008 (non-root), kernel 6.8.0-149-generic; GPU `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (RTX 4090, driver 535.309.01, 24 564 MiB); lease `~/r1_locks/gpu0.lock` |
| Launch checkout | `/home/dowling/r1_tracks/t1_tasl/paper_ar` — HEAD **`d52c9d9d09d8b0daf2a3d2bc3ddf9b43f4c6707c`**, origin/main `1402f466497c29638c53a3397f44ab9a3e6717ec`; tracked tree clean; only untracked file the signed note |
| Note | `docs/r1/authorizations/g1b_ar_t1_tasl_20261122.md` sha256 **`ac5ee6c5585eab537ed6d01558e2a759bd1a80548913aa4d5520a0f6816a5cde`** (unchanged post-run) |
| Spec | `sweep2/t1_tasl/g1b_tasl_ar_spec.json` sha256 **`65da95db375505506e65abac32eaa99f21be914d5a638870f4a03c5b5173f345`** (unchanged post-run; `spec_sha256` in the job record) |
| Harness checkout | `/home/dowling/r1_tracks/t1_tasl/harness_ar` — HEAD **`2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`**; clean except the allowed untracked link `nodes/autoresearch_fixedtokens/data`; the seven-node checkout `harness` stays at `c025f89a…` |
| Environment | `ar-cond7a` = `/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python`, Python **3.12.15**, freeze sha256 **`11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1`** (122 packages), read-only, checked at job start |
| Node bindings | node_spec `5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192`; committed pin `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc`; edits manifest `55f2666a3d09aaedb8b8552aef00f8a9c27b84f1bd7df24d886904dad581e5c7` (E1–E4); data manifest **`ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`** (setup.log: `AR_DATA manifest_sha256=ab7186d2… files=13`) |
| Timeout basis | `census_slowest_x3` 255.916 s → timeout **767.748 s**, `stop_on_timeout: true`; node deadline 305 753 s |
| Isolation limits | cgroup `memory.max=8589934592`, `memory.swap.max=0`; affinity cpus **0-7**; Yama `ptrace_scope 1`; isolation waivers `{}` |

Driver `/home/dowling/r1_tracks/t1_tasl/run_ar_g1b.sh` (`inputs/driver.sh`) was started with
`setsid nohup bash run_ar_g1b.sh` and logged
`START 2026-11-22T23:49:30Z main=1402f466… HEAD=d52c9d9d…`. The exact launch command (baseline process capture):

```
G1B_TASL_ENABLE_REAL=1 bash /home/dowling/r1_tracks/t1_tasl/paper_ar/sweep2/t1_tasl/t1_tasl_node.sh \
  g1b /home/dowling/r1_tracks/t1_tasl/paper_ar/sweep2/t1_tasl/g1b_tasl_ar_spec.json autoresearch_fixedtokens \
  /home/dowling/r1_tracks/t1_tasl/paper_ar/docs/r1/authorizations/g1b_ar_t1_tasl_20261122.md --enable
```

The wrapper ran the node inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`,
with `AR_TEST_CGROUP_PARENT` set to that scope and `taskset -c 0-7` on python 3.12.15. Full binding:
`inputs/launch_binding.txt`.

## 3. The job

- **Attempt:** `attempt-1` only (`attempt.json`: pid 600474, TASL-2, started **2026-11-22T23:49:31Z**); the lease was
  held by the node pid 600474 for the whole run; sealed at
  `sealed_g1b/g1b-ar-tasl-20261122-a/autoresearch_fixedtokens/attempt-1/`.
- **Parts** — all `rc 0`, `stop: null`, `stop_kind: null`, gate `effective:true, waivers {}, exceptions []`:

| part | expected | written | successful | wall (s) | per-run (s) |
|---|---|---|---|---|---|
| default | 10 | 10 | 10 | 2 267.1 | 226.713 |
| train | 150 | 150 | 150 | 34 075.2 | 227.168 |
| split | 150 | 150 | 150 | 34 171.6 | 227.810 |
| joint | 150 | 150 | 150 | 34 309.4 | 228.729 |

- **Determinism gate: passed.** `deterministic: true`, `divergent_configs_at_default: []`; every config's `default`
  metric equals its `default_repeat` exactly (c0 1.284416, c1 1.287731, c2 1.227431, c3 1.297474, c4 1.266106);
  460 rows, 0 divergent, 0 non-null failures.
- **Timing** (job record; c0 median wall / census `run_seconds` 218.951): default 218.500 s (ratio 0.9979),
  train 218.558 s (0.9982), split 219.295 s (1.0016), joint 220.072 s (1.0051); per-part max wall
  256.122 / 258.429 / 258.606 / 260.146 s — the largest single run (260.1 s) is well below the 767.748 s timeout,
  so **no run reached the timeout** (no timing STOP).
- **Data:** setup staged the manifest `ab7186d2…` (13 files) from the declared root; the engine logs each part
  `expected_runs == written_rows` with `stop: null` (`run/engine_<part>.log`).

## 4. Result at a glance

| | |
|---|---|
| Run window (UTC) | 2026-11-22T23:49:31Z → 2026-11-24T04:56:35Z |
| Wall | **104 824 s = 29 h 07 m 04 s = 29.1178 h** (driver START 23:49:30Z) |
| GPU-hours | **29.1178 GPU-h** (lease held for the whole job); 29.104 GPU-h summed from the 460 per-run `wall_seconds`; median run 220.1 s (min 216.6, max 260.1) |
| Projection / ratio | spec projection 28.227 GPU-h → measured/projection **1.032** |
| Runs | **460 expected / 460 written / 460 successful / 0 divergent** |
| Parts | default 10, train 150, split 150, joint 150; all `rc 0`, `stop: null` |
| Determinism gate | **passed** (`deterministic: true`, `divergent_configs_at_default: []`) |
| Isolation gate | **460/460 rows** `isolation.effective: true`, `waivers {}`, `exceptions []`, `log_intact: true`; every part `gate: effective:true, waivers {}, exceptions []` |
| Foreign-GPU checks | **9/9 empty** (`before the job`, before/after each of the four parts) |
| STOPs | **none** — `stop: null`, `stop_class: null`; no refusal, timing, lease, foreign, harness, environment, data or cap STOP |
| Cap | projection-based cap check at signature: this spec 28.227, G.1b together 58.589 (sensitivity 85.96) ≤ 100 GPU-h (R1-G1B-CAP); measured lease 29.118 h is far below the cap |
| Node deadline | 305 753 s; used 104 824 s |

## 5. Seal

`g1b_tasl.py seal <attempt-1> <spec> --node autoresearch_fixedtokens` (driver, rc 0) copied the attempt to
`sealed_g1b/g1b-ar-tasl-20261122-a/autoresearch_fixedtokens/attempt-1/` (no overwrite) and wrote
`SEAL_RECEIPT.json` binding the record and the wrapper log:

| file | sha256 |
|---|---|
| `SEAL_RECEIPT.json` | **`c76774c607b146ed49005e7f46111338c1b82d6fb7d4ce1e544faebe3fda56f8`** |
| `job_record.json` | **`d4d080185cb3608a457cf0ebd605c486880fb83446c851909fb85b01cbfca77c`** |
| `SHA256SUMS` | `5df2876e93337623b9768fd07abc6697e358b4bf329cc96832969e6df20c66e3` |
| `node.log` | `a540ef29837a59ba251cac35415260735e1b57f981c5f11fef241b4f259833ec` (matches the receipt's `node_log_sha256`) |
| `out.tar` (not copied to the captures) | `3619361ed14ff86fe5a86436aeecfba4ec4f1820b77e3a020486a5c7457f4e7c` |

Receipt: `schema g1b_tasl_seal_receipt/1`, `run_id g1b-ar-tasl-20261122-a`, `node autoresearch_fixedtokens`,
`host TASL-2`, `attempt 1`, `stop: null`, `stop_class: null`, `sealed_utc 2026-11-24T04:56:35Z`.
`sha256sum -c SHA256SUMS` passes **rc 0 in the sealed directory and rc 0 in the runs attempt directory** (both list
`out.tar` and `job_record.json`); the runs-tree `job_record.json` is byte-identical to the sealed one
(`inputs/seal_verify.txt`). Job record: `schema g1b_tasl_job_record/1`, `spec_schema g1b_tasl_ar_job/v1`,
`spec_sha256 65da95db…`, `harness_commit 2d09f9a9…`, `label ENGINEERING_ONLY`, runs
`{expected 460, written 460, successful 460, divergent 0}`, env `ar-cond7a`/3.12.15/freeze `11def6ad…`,
GPU `RTX 4090 / GPU-4d623e76… / driver 535.309.01`, host TASL-2 (kernel 6.8.0-149-generic, uid 1008),
cgroup 8 GiB / swap 0. The sealed node log ends `NODE_EXIT=0`, `systemd_run_rc=0`, `# end=2026-11-24T04:56:35Z`.

## 6. What was kept, and what was not done

- **Old sealed G1b attempts untouched.** All **35 files** of the 7 pre-existing sealed attempts under
  `sealed_g1b/` (`g1b-tasl-20261121-b/{mlab_imdb,mlab_ogbn_arxiv,mlgym_fmnist/attempt-3,mlgym_houseprice}/attempt-1`
  and `g1b-tasl-20261121-b-xc2-TASL-2/{mlab_cifar10,mlgym_breakout_minatar,mlgym_cifar10}/attempt-1`) are
  byte-identical and have identical size/mtime before and after; the empty directory
  `sealed_g1b/g1b-tasl-20261121-a/mlab_ogbn_arxiv` is also unchanged. The run/sealed trees gained **only** the new
  `g1b-ar-tasl-20261122-a/autoresearch_fixedtokens/attempt-1/` paths.
- **Track P archive untouched.** All **1 676 files** under `/home/dowling/r1_trackp/Agent_paper_B/archive` have
  identical sha256 and identical path/size/mtime; the lease logs `_attempt1_gpu_lease_log.jsonl`
  (sha256 `6950509182f4230dd2c7e2bad4253748415fa969e84ef9bdac21e19242b55077`) and `gpu_lease_log.jsonl`
  (sha256 `a043399807e6a799d7d9ae84689fb18533fc6a2557441db1da67f45f12204d18`) are unchanged; nothing under
  `/home/dowling/r1_trackp` was written. Evidence: `inputs/untouched_confirmation.txt`,
  `inputs/old_sealed_manifest_post.txt`, `inputs/baseline_initial_state.txt`, `inputs/final_verify.txt`.
- **TASL-7 held, not launched.** Post-run TASL-7 check: no job process, `~/r1_locks/gpu0.lock` untouched
  (mtime 2026-11-21 02:07:04 -0800), no new run/log trees (newest log 2026-11-22 12:55). The G.1b note2 (TASL-7)
  remains unlaunched, as instructed. (The TASL-2 run uses its own checkout and the shared TASL-2 lease only.)
- **Nothing else run.** No `assemble`, `summarise`, `compare`, G.4 pilot or other node; no commit and no push; no
  deletion anywhere.

## 7. Host end state (captured 2026-11-24T05:03:54Z; `inputs/host_end_state.txt`)

TASL-2 idle: GPU `353 MiB, 0 %`, `nvidia-smi --query-compute-apps` empty, lease `~/r1_locks/gpu0.lock`
**`LEASE_FREE`** (no holder), no G.1b/noise-floor process of the user, disk 350 GiB free. Checkouts unchanged:
`paper_ar` HEAD `d52c9d9d` / origin/main `1402f466`, tracked-clean with only the untracked note;
`harness_ar` `2d09f9a9` clean except the allowed `nodes/autoresearch_fixedtokens/data` link.

## 8. Captures

`docs/r1/reports/tasl_chain_20261122/AR_G1B_TASL2_RESULT_20261122_captures/` — 44 payload files (the sealed
attempt's own `SHA256SUMS` included) plus a `SHA256SUMS` (own sha256
**`025cc75dfbab822737fbdd37559f116477aefd81ee047b886f87661b9ca13546`**; `shasum -a 256 -c` passes, rc 0):

| path | contents |
|---|---|
| `sealed/` | `SEAL_RECEIPT.json`, `job_record.json`, `SHA256SUMS`, `node.log` (the sealed attempt; **no `out.tar`**) |
| `run/` | `attempt.json`, `setup.log` (`ab7186d2…` manifest), the merged `runs.jsonl` (all 460 rows) and per-part `default|train|split|joint/{chunk_record.json,runs.jsonl,edits.json}`, `chunk_<part>.json`, `engine_<part>.log`, `edits.json`, the runs-tree `job_record.json`/`SHA256SUMS` |
| `logs/` | driver log `ar_g1b_tasl2.log`, `status` (`DONE 2026-11-24T04:56:35Z`), the wrapper node log |
| `inputs/` | `launch_binding.txt`, `baseline_initial_state.txt` (pre-run), `final_verify.txt` (post-run verification), `local_verification.txt` (untouched-tree + metric checks), `untouched_confirmation.txt`, `old_sealed_manifest_post.txt`, `seal_verify.txt`, `host_end_state.txt`, `driver.sh`, `g1b_tasl_ar_spec.json`, `monitor_poll.log`, `monitor_summary.log`, `monitor_notes.txt`, `monitor_harvest_info.txt` |

Host-side originals remain on TASL-2 under `/home/dowling/r1_tracks/t1_tasl/`:
`runs/g1b-ar-tasl-20261122-a/autoresearch_fixedtokens/attempt-1/` (40 MB `out.tar` kept there, not copied),
`sealed_g1b/g1b-ar-tasl-20261122-a/autoresearch_fixedtokens/attempt-1/`, `logs/ar_g1b_tasl2.{log,status}`,
`runs/g1b-ar-tasl-20261122-a/_logs/autoresearch_fixedtokens-20261122T234930Z-600458.node.log`, and the launch
checkout `paper_ar/`. Provenance note: the watcher's first automatic harvest (05:00Z) used a flat sealed path and
missed the `run_id/node/attempt-1` level; the corrected harvest/verification at 05:03Z is the evidence set here
(nothing on the host was changed by either).

## 9. Reproduce

1. Read the state: `cat logs/ar_g1b_tasl2.status` on TASL-2 (or poll it every 10 min from the Mac as the watcher
   did: `ssh portal_zhixu 'cat /home/dowling/r1_tracks/t1_tasl/logs/ar_g1b_tasl2.status'`).
2. Verify the sealed attempt (read-only):
   `cd /home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-ar-tasl-20261122-a/autoresearch_fixedtokens/attempt-1 && sha256sum -c SHA256SUMS`
   (rc 0) and the runs attempt directory likewise; compare `job_record.json` against `SEAL_RECEIPT.json`'s
   `job_record_sha256` (`d4d08018…`), `node.log` against `node_log_sha256` (`a540ef29…`).
3. Re-verify the untouched trees by comparing the pre-run baseline sha256/manifests in
   `inputs/baseline_initial_state.txt` with the post-run lists in `inputs/final_verify.txt` (as `inputs/local_verification.txt`
   does: 35/35 old sealed files identical, 1 676/1 676 Track P archive files identical).
4. Cross-check the result: `runs/.../attempt-1/job_record.json` (runs, parts, timing, determinism, foreign checks)
   and `out/runs.jsonl` (460 rows; `isolation.effective`/`waivers`/`exceptions` on every row).

## 10. What this does and does not establish

- **Establishes (EVIDENCE, ENGINEERING_ONLY):** the authorized G.1b autoresearch noise-floor run for
  `autoresearch_fixedtokens` on TASL-2 (`g1b-ar-tasl-20261122-a`) completed its declared **460 runs**
  (10 default + 150 train + 150 split + 150 joint), deterministic at the default part, under the isolator with
  `effective:true, waivers {}, exceptions []` on every part and row, at a measured 4090/Ada ratio ≈ 1.00
  (c0 medians 218.5–220.1 s vs census 218.951 s), in 29.1178 h / 29.118 GPU-h, sealed with rc 0 and verified
  `sha256sum -c` — with no author STOP.
- **Does not establish:** any label, evaluation or sweep-2 reading (ENGINEERING_ONLY, `labels_read: none`); any
  assembly/summary across the G.1b nodes (this memo does not run `assemble`/`summarise`; per the spec the D21 noise
  floor joins the seven nodes' table later, by node, as its own run record); any TASL-7 launch or the publication
  of the G.1b note2.
