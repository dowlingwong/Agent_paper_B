# R1-TRACKG-AR-U2-TASL2 — one isolated option-A smoke of `autoresearch_fixedtokens` on TASL-2 — RESULT (21 November 2026)

**Status: PASS — one clean isolated smoke, `CHECKLIST_E_PASSED`, `effective: true`, `waivers {}`,
`exceptions: []`, private `/dev/shm`, no CUDA IPC, measured option-A slowdown 3.225× B1 / 3.176× whole smoke.**
This is engineering evidence for the option-A gate on TASL-2 for the author-signed **R1-TRACKG-AR-U2-TASL2**
task (delegated by the lead). No U2 run was started, no code was committed or pushed, one smoke only and no
retry. ENGINEERING_ONLY; AI-assisted (DeepSeek Harness agent `tasl2-ar-runner`).

## 1. Authority, scope and STOP rules

- Task authority: author-signed **R1-TRACKG-AR-U2-TASL2** (environment, data, **one** clean isolated smoke,
  measured slowdown, report). Work on **TASL-2** only; do **not** touch TASL-7, the Track P attempt-1
  archive/lease log, HTCondor/deepthought; no deletion (move aside if needed); no push. Paper A is on Ada;
  TASL-2 host checks are accepted.
- Host-condition gate (accepted): `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_20261121.md`
  and its captures, reviewed **ACCEPTED** by
  `docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (0 BLOCKING, 1 MAJOR report-only) with
  conditions **C1–C4**. The gate is for **AR option A only**: §3 item 7 CUDA IPC remains **UNTESTED** and
  §5 item 5/§5.5 remain open; option A does not use CUDA IPC.
- Gate operating conditions (review C4) applied here: every run in a **live delegated cgroup parent**, GPU named
  **by UUID**, `shared_dev_shm: false`.
- STOP rules followed: dataset revision/manifest mismatch or download failure = STOP; co-tenant on the used card
  / OOM / non-effective isolation / code failure = STOP, one smoke, no retry. **None occurred.**
- CPython / torch / data / kit are all outside the paper repo; the smoke runs-root and evidence root are outside
  the repo.

## 2. Host, kit, environment, data

### 2.1 TASL-2 host

`TASL-2` (zhixu portal), Linux `6.8.0-149-generic #149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC` x86_64, Ubuntu
22.04.5 LTS, boot id `86c613a9-b90c-48be-9bd5-a0f99c940dae`; uid/euid/gid `1008(dowling)`, non-root; 32 CPUs;
`MemTotal 65,543,252 kB`; `/` on `/dev/nvme0n1p2`, **362 GiB free** after the smoke; `cgroup2 … nsdelegate`;
systemd 249; userns/AppArmor/Yama sysctls as in the accepted host check (`unprivileged_userns_clone=1`,
`apparmor_restrict_unprivileged_userns=0`, `yama.ptrace_scope=1`). GPU 0: NVIDIA GeForce RTX 4090, 24,564 MiB,
driver `535.309.01` (NVRM 535.309.01), UUID **`GPU-4d623e76-7587-ee15-a633-46f60d220d94`**. All commands over
`ssh -o BatchMode=yes portal_zhixu`; report times are UTC (TASL-2 local clock is PST, UTC−8).

### 2.2 Kit worktree (fixed tree)

`/home/dowling/r1_trackp/harness_cond7a_20261121` @ **`73303380197477df971e865440d0ae11135fe1b3`** (detached,
tracked-clean; only the expected untracked `nodes/autoresearch_fixedtokens/data` link made by setup).
`git merge-base --is-ancestor` confirms it contains accepted isolation core **`68cdd1a`** and accepted Ada fix
**`5403392e`**. Base repo `/home/dowling/r1_trackp/autoresearch_harness` @ `897d83c8`, `trackp-20261026`, clean.
Node spec file sha256 `5bdce00a…`; canonical spec `raw_sha256` **`5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192`**;
representative-edits manifest sha256 `55f2666a…`. Frozen code: `ar_isolated.py` `3ba34c67…`, `ar_worker.py`
`65a4927c…`, `run_fixed_budget.py` `58d80b52…`, `ar_parent.py` `cbef1d38…`, `ar_budget.py` `c76b5d85…`,
`ar_data.py` `85cec63f…`, `prepare.py` `3063fe87…`, `prepare_data.py` `7167e55d…`, `requirements.txt`
`cbfb98e7…`. CUDA-IPC AST scan of the result path: **NONE** for both `run_fixed_budget.py` and `ar_worker.py`.
Pins (code-unit §5/m3 rule): **committed file pin `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc`**
(20 entries, from a `git archive` of HEAD without the data link) and **deployed pin
`ca04908601d672ccf4d631914ea5fe3b3cd210ba3c1ddf7f6eab4baac63476f7`** (21 entries, `data -> /home/dowling/r1_trackp/data/autoresearch_fixedtokens`).
The Ada deployed pin `069e987a…` is the same construction under the **different** Ada data root
(`/home/dowling/r1_trackg_20261117/data`), i.e. path-dependent by design, not a mismatch (see §7.1).

### 2.3 Separate venv `ar-cond7a` (base Track P venv untouched)

`/home/dowling/r1_trackp/venvs/ar-cond7a` is a byte copy of `venvs/trackp-gpu` made for this task; the Track P
venv was **not modified** (its package freeze is byte-identical before/after: 121 package lines, sha
`50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`; `pyvenv.cfg`/venv dir mtimes unchanged
from Oct 25). Python **3.12.15**, torch **2.6.0+cu124** (CUDA 12.4), `torch.cuda.is_available()=True`,
`cuda.is_available()` masked False with `CUDA_VISIBLE_DEVICES=""`. Node requirements installed into the copy with
`uv 0.13.6`: an **offline** attempt failed only because `pyarrow==26.0.1` is not in the local uv cache; the online
uv install from PyPI (HTTP 200 reachable; tiktoken 1.1 MiB, rustbpe 1.0 MiB, pyarrow 52.5 MiB downloaded
into the copy only) then succeeded. Delta: numpy 2.4.4→**2.5.4**, pyarrow 26.0.0→**26.0.1**, tiktoken
0.12.0→**0.14.0**, **rustbpe 0.1.0** added; requests 2.33.1, huggingface_hub 2.2.0, transformers 5.19.0,
pytest 9.0.3 already present. **Env freeze: 122 lines, sha256
`11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1`** (`prep/env_freeze.txt`, also the in-scope
`env_freeze_live.txt`); imports verified for torch, numpy, pyarrow (+parquet), tiktoken, rustbpe, requests,
huggingface_hub; a CUDA allocation+synchronisation probe returned the expected sum (`523776.0`).

### 2.4 Data (the node's frozen `setup_command`, guarded)

Run exactly as the node's `setup_command` in `nodes/autoresearch_fixedtokens` with
`AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackp/data`:
`python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/autoresearch_fixedtokens"` (downloads the first 10
`karpathy/climbmix-400b-shuffle` training shards + validation shard 06542, trains the BPE tokenizer, writes the
data manifest, makes the tree read-only and links it into the node). Guarded before any download: HF dataset
revision = **`915333b4f8b8684f39aeaafea600fea6f43fb703`** (matches the reviewed `915333b` prefix; 6,545 siblings).
Result: **rc 0**; wall **1:46.11** (user 333.61 s, sys 37.77 s, max RSS 1,348,608 kB); manifest sha256
**`ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51` = the expected hash**, **13 manifest
files**, 14 files on disk incl. the manifest, **1,009,004,449 B (963 M)**, source revision `915333b4…`,
tokenizer `vocab_size=8192`, sanity check passed; data dir mode `555`, manifest `444`; node link created; no
deletion, nothing reused from elsewhere. (`logs/setup_data.log`, `prep/setup_time_v.txt`, `data_manifest.txt`.)

## 3. The one smoke (command, scope, controls)

One smoke only, launched **2026-11-21T01:58:19Z**, ended **02:28:10Z**. Inside a live delegated
`systemd-run --user --scope --unit=tasl2_ar_smoke_cond7a -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`,
with `AR_TEST_CGROUP_PARENT` taken from the live scope cgroup (`memory.max=8589934592`, `memory.swap.max=0`,
`memory.peak` and `cgroup.kill` writable), venv `ar-cond7a` first on `PATH` with `VIRTUAL_ENV`/`PATH` set,
`PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=""`, `CC=/usr/bin/gcc`, `CXX=/usr/bin/g++`, and `taskset -c 0-7`.
The one-line command executed under `/usr/bin/time -v`:

```
python -m tests.trackg.port_smoke_gpu --node autoresearch_fixedtokens \
  --gpu-uuid GPU-4d623e76-7587-ee15-a633-46f60d220d94 --cpus 0-7 \
  --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" \
  --runs-root /home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/runs --provisional-timeout 1800
```

Controls and captures: `uses the COND7-aware verifier` (see §7.4) and the kit's own checklist E; exclusive
**`flock` on `~/r1_locks/gpu0.lock`** (fd 9) held **01:58:19Z–02:28:10Z**, **no lease-log write**; GPU named by
UUID; **0 compute apps on the card at launch** (353 MiB is the pre-existing desktop allocation, 0 %);
1 s `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory` sampler plus a timestamped companion; a 2 s
cgroup memory sampler; a 2 s **co-tenant monitor** (879 timestamped ticks, **0 foreign compute apps** — abort
policy never triggered); GPU before/mid/after snapshots; runs-root outside the repo.

**Result: `systemd_run_rc=0`, `CHECKLIST_E_PASSED autoresearch_fixedtokens`, 9 run records / 8 executed /
`refused s001` (`scope_violation`), COND7-aware verification `ok: true`, `issues: []`.**

### 3.1 Runs (seeds 8001/8001, full budget 32,768,000 tokens)

| run | decision / outcome | elapsed (s) | `val_bpb` | worker peak VRAM (MB) |
|---|---|---|---|---|
| `s000_baseline` | baseline, ok | **218.951** | **1.293937** | 1,980.1 |
| `s001` | frozen-path diff, **not_run_refused** (`scope_violation`) | — | — | — |
| `s002` | broken diff, **divergent** (`non_finite_loss`, token `nan`) | 216.768 | — | 1,980.1 |
| `s003` | first edit applied, ok | 218.636 | 1.286194 | 1,980.1 |
| `E1` | declared edit 1, ok | 219.565 | 1.286194 | 1,980.1 |
| `E2` | declared edit 2, ok | 255.916 | 1.227064 | 3,720.4 |
| `E3` | declared edit 3, ok | 217.516 | 1.303639 | 1,980.1 |
| `E4` | declared edit 4, ok | 222.584 | 1.277350 | 1,948.1 |
| `B2` | second baseline (repeat), ok | **218.443** | **1.293937** | 1,980.1 |

`B2` repeats `B1` **exactly** (`1.293937`), so the within-host determinism/`CAUSAL_ATOL` requirement holds; the
per-run timings are tight (`mean 223.547 s`, `median 218.951 s`, min `216.768 s`, max `255.916 s`).
Run budget `{kind: tokens, value: 32768000}`; `node_spec_sha256 = 5c1bdf3d…`; deployed `frozen_pin_sha256 =
ca049086…` in every record; `determinism.not_forced = ["dataloader_workers"]`, `shim_loaded true`;
`process.killed_with null`, `timed_out false`, returncode 0; `limits` = GPU UUID `[GPU-4d623e76…]`, `cpu_list
[0–7]`, `memory_method external`, exact external-limit string, `provisional_timeout_seconds 1800.0`,
`timeout_factor 3.0`; no `synthetic` marker.

### 3.2 Isolation record (every executed record, verifier-checked)

`isolation.effective: true`, `waivers {}`, `exceptions []`; `log_intact true`;
`result_channel_overflow false` and `result_channel_sha256` present; `cgroup.kill` method `cgroup.kill`,
`empty_after true`, `removed true`; `worker_sandbox.shared_dev_shm false` (the worker's `/dev/shm` is the private
tmpfs — no host shm); GPU by UUID; worker runs in its own user/mount/PID/network/cgroup namespaces; no CUDA-IPC
marker in any run log. `AR_INFO eval_rows/eval_batch_size/peak_vram_mb` recorded in the logs.

### 3.3 GPU before / mid / after and exclusivity

- Before: `353 MiB used, 23,830 MiB free, 0 %`, **0 compute apps** (only the pre-existing desktop allocation).
- Mid (during the first run): `869 MiB used, 1 %`, compute apps = our own `port_smoke_gpu` PID only.
- After: `353 MiB used, 23,830 MiB free, 0 %`, **0 compute apps**; no co-tenant ever appeared.
- Whole-smoke 1 s sampler **upper bound** (per-sample sum over the used card; **not** a per-run peak, includes our
  own parent+worker by construction): **12,436 MiB max per-sample sum**; max single row **7,848 MiB**; 3,506
  rows / 1,777 samples / 1,786.7 s; `distinct_pids` 16.
- Lease: `flock` exclusive on `~/r1_locks/gpu0.lock` 01:58:19Z–02:28:10Z, **no lease-log append**; the lock
  file's mtime moved to `2026-11-20 17:58:19` by the truncating open of the documented lock (expected; the
  Track P attempt-1 lease log and archive were not touched — see §9).
- Paper A gate: **not applicable on TASL-2** (Paper A is on Ada); the GPU-exclusivity controls above are the
  substitute the task requires and are recorded in `gate/gate_not_applicable.txt`. Track X evidence marker absent.

## 4. Measured option-A slowdown and peak resources

Reference (accepted 17 Nov 2026 Ada G.0 U2 baseline, `TRACKG_U2_AR_RESULT_20261117.md`): smoke wall **564 s**,
**B1 67.901 s** (B2 64.096 s), baseline worker peak VRAM **5,211.3 MB**, whole-smoke `/usr/bin/time -v`
user 662.47 s / sys 42.78 s / max RSS 2,110,468 kB.

| quantity | measured on TASL-2 (21 Nov) | vs 17 Nov Ada |
|---|---|---|
| B1 `s000_baseline` | **218.951 s** (`val_bpb 1.293937`) | **3.225×**, **+151.05 s** |
| B2 repeat | **218.443 s** (`val_bpb 1.293937`, exact repeat) | vs B1 −0.508 s |
| mean / median executed run | 223.547 s / 218.951 s | — |
| whole smoke wall | **1,791.0 s** (01:58:19→02:28:10); `/usr/bin/time -v` `29:49.26` = 1,789.26 s | **3.176×**, **+1,227 s** |
| transfer surrogate | **0.2345 s/logits-request** = (B1−67.901)/644 | inside the code-unit's predicted 0.15–0.25 s/request band |
| volume (from code-unit §8, not instrumented) | 644 requests/run × 1 GiB = **640 GiB one-way**, ≈**1.9 TiB moved** per run | — |
| peak worker VRAM (baseline; AR_INFO) | **1,980.1 MB** (max over runs 3,720.4 MB on E2) | vs 5,211.3 MB Ada baseline |
| whole-smoke GPU upper bound | **12,436 MiB** (1 s compute-app sampler; upper bound, not per-run) | — |
| cgroup v2 memory (8 GiB scope) | **`memory.peak` 5,550,911,488 B (5.17 GiB)**; sampler max current 5,550,727,168 B; after 231,948,288 B; `events max 0/oom 0/oom_kill 0`; swap 0 | cap **not** hit; no OOM |
| whole-smoke `/usr/bin/time -v` | user **1,529.05 s**, sys **395.16 s**, max RSS **3,204,520 kB (3.06 GiB)**, major faults 201, fs outputs 187,928, exit 0 | — |
| executed unit bytes (on-disk working copies) | 16.6 KB (`s001`, refused) … 22.7 MB; **runs total 158,854,790 B (151.5 MiB)** | — |

So the option-A CPU-`memfd` logits transport costs **≈3.2× the 17 Nov B1** and **≈3.2× the 17 Nov smoke wall**;
this is the measured number the U2/census cost must carry. The B1↔B2 difference (−0.5 s) shows the comparison is
not distorted by a one-time compile: every run gets a fresh working copy/caches, and B1 and B2 are equally warm.

## 5. Isolation and checklist evidence summary

`CHECKLIST_E_PASSED autoresearch_fixedtokens` (kit `port_support.check_smoke`: baseline ok, frozen-path diff
refused `scope_violation`, broken diff divergent, 8/8 executed records complete, `not_forced`
only `dataloader_workers`, B2 metric == B1 metric, no `sealed` in the manager view), and the COND7-aware
verification `ok: true` with **no issues** and **no false STOP**. This is the first clean option-A GPU run of this
node: the 20 Nov Ada attempt failed with a co-tenant CUDA OOM (no clean attempt), the 21 Nov retry session was
an external-contention STOP (0 run records); this TASL-2 run is the measurement those sessions could not obtain.

## 6. Run-record hashes (per-run shas; full list in `record_hashes.txt`)

| run | `run_record.json` sha256 | worker peak VRAM |
|---|---|---|
| `s000_baseline` | `012037bcbf8413c0b5fe1c02e4bcd2e36f6aa462f11530e72d754c52783092de` | 1,980.1 MB |
| `s001` | `8f11aa481945cf7e8cd25db205421b94fe9a6fd724ca842195a7d0750753bd45` | — |
| `s002` | `c5a32056c204e130bf95151fdd92e6beea333cacc90215601eccd831eab24ac6` | 1,980.1 MB |
| `s003` | `15ca197234ea19b77232935198bf9ad856638b7a6eca608e14b57ef40734df38` | 1,980.1 MB |
| `E1` | `eac45937e196fc9a2d98707a9fcd556bc7c1a936ca36194af9c517b4dee6195d` | 1,980.1 MB |
| `E2` | `bfbe0b865ea381a3e38af1c40707bc3a6bfb9970d49168c8cb81cbec132ed65b` | 3,720.4 MB |
| `E3` | `6853955078abce8f9a5bfa3f1cdddc5843a73976d92fb422985d46d93d483f10` | 1,980.1 MB |
| `E4` | `3eeb0a564cb3f761e1798e8305420b1fe8a6e3807998b32659794591ac1b864b` | 1,948.1 MB |
| `B2` | `d6b46960f98cf0eb712208feac5b71eff2911cc2651689f676a93b880b539aff` | 1,980.1 MB |

`record_hashes.txt` (25 lines) covers every `run_record.json`, `run.log` and `result_channel.txt`.

## 7. Deviations, differences and notes (all disclosed)

1. **Deployed pin differs from the Ada value by construction.** TASL-2's deployed pin is
   `ca04908601d672ccf4d631914ea5fe3b3cd210ba3c1ddf7f6eab4baac63476f7` (21 entries, data link target
   `/home/dowling/r1_trackp/data/autoresearch_fixedtokens`), not the Ada `069e987a…` (different data root).
   The committed 20-entry pin is **exactly** `147f0d35…`. Per code-unit §5/m3 a record must be compared with the
   deployed pin recomputed on the same host/data root; that is what was done (and re-verified independently
   before and after the smoke). This is not a mismatch.
2. **A false STOP was recorded and corrected.** The launcher's first `RESULT_STATUS.txt` said
   `STOP: slowdown analysis rc=1`, caused by the operator's slowdown-analysis script crashing on
   `/usr/bin/time -v`'s `29:49.26` elapsed string (a script bug, not a unit failure). The initial file is
   preserved as `RESULT_STATUS.initial_false_stop.txt` (+ `slowdown.stderr.txt`); the script was fixed and
   re-run (`slowdown_rc=0`), and the smoke was **not** re-run. Final status is PASS.
3. **Verifier choice.** The kit's `verify_records.py` / `collect_smoke_summary.py` used in earlier sessions live
   under `/home/dowling/r1_engineering/iso_kit_update_20261119/scripts/` on **Ada** and are absent on TASL-2.
   The **COND7-aware** `verify_ar_cond7a.py` from the accepted option-A sessions was used instead (and the smoke
   module's own kit checklist-E `check_smoke` also passed). Result: `ok: true`, `issues: []`, so no false STOP
   came from the verifier.
4. **Cross-host metric/VRAM differences.** B1 `val_bpb` here is `1.293937` vs Ada `1.291068`, and baseline worker
   peak VRAM is 1,980.1 MB vs Ada 5,211.3 MB — different GPU (RTX 4090 24 GiB vs L40S 48 GiB), different
   driver/kernel and a different CUDA context layout; the **within-host** determinism gate (B2 == B1 exactly)
   passes. These are recorded, not normalised.
5. **Operator bug in the outer launcher's top-level env capture.** The launcher's `PATH` entry for `uv` was the
   binary path instead of its directory, so the outer `env.txt`/`env_freeze.txt` capture initially failed. The
   canonical env freeze is the **in-scope** `env_freeze_live.txt` (122 lines, sha `11def6ad…`, identical to the
   installation check), copied to `env_freeze.txt`; `env.txt` was corrected and says so.
6. **No prewarm step.** To respect "one smoke only", no separate GPU prewarm/compile run was made; as shown in
   §4, B1≈B2, so this does not distort the B1 comparison.
7. `nvidia-smi --version` is not recognised by driver 535.309.01 (the `host.txt` capture keeps the error); the
   driver version is recorded via `--query-gpu` and `/proc/driver/nvidia/version`.
8. **Paper A gate not applicable on TASL-2** (task wording); the substitute GPU-exclusivity controls are in
   §3.3 / `gate/gate_not_applicable.txt`.
9. One smoke, **no retry**; no co-tenant, no OOM, no code/unit failure triggered the STOP rules.

## 8. Evidence and preservation

- TASL-2 evidence root (new): **`/home/dowling/r1_engineering/tasl2_ar_cond7a_20261121/`** — `scripts/`,
  `prep/` (setup log, time -v, pins, env), `logs/` (data setup, smoke log, launcher), `gate/`, `gpu/`
  (before/qualify/mid/after, lease, 879-tick co-tenant monitor), `sampler/` (1 s compute-app samplers,
  sampler-max, 2 s cgroup sampler), `runs/` (9 records + working copies), `references/` (the accepted Ada 17 Nov
  result, option-A code-unit report, TASL-2 host-check report + review, the Ada 20 Nov failure result and the
  retry STOP result).
- Bundle: **7,056 files, 161,531,825 B (~154 MiB; 170 MiB `du`)**; `SHA256SUMS` (7,055 entries) sha256
  **`32f5009a347264bb1d820c420dedeaf0d2dd5fe8822516597f1bba53a3ca0aeb`**, verified with
  `sha256sum -c` on TASL-2 and with `shasum -a 256 -c` on the Mac copy. Key captures: `RESULT_STATUS.txt`
  (PASS), `final_state.txt`, `base_venv_unchanged.txt`, `lease_attestation.txt`, `isolation_runs.txt`,
  `bundle_info.txt`, `verify_full.json`/`.summary.txt`, `slowdown.json`, `facts.json`, `prep/pins_*`,
  `data_manifest.txt`, `executed_unit_bytes.txt`, `record_hashes.txt`, `gpu/*`, `sampler/*`, `runs/*`.
- Mac ops worktree `ops-tasl-20261116` (uncommitted, no push): sibling captures
  `docs/r1/reports/trackg_g0_20261117/TASL2_AR_COND7A_RESULT_20261121_captures/` (byte-identical copy) and this
  report. Verify with:
  `cd …/TASL2_AR_COND7A_RESULT_20261121_captures && shasum -a 256 -c SHA256SUMS` (Linux: `sha256sum -c`).
- Workspace changes on TASL-2: the new evidence root, the copied `ar-cond7a` venv, the new data tree under
  `/home/dowling/r1_trackp/data/`, and the untracked `nodes/autoresearch_fixedtokens/data` link in the kit
  worktree. **Nothing deleted or moved aside; no push; no commit.**

## 9. Attestations (non-authorities untouched)

- **Track P attempt-1 archive** `/home/dowling/r1_trackp/runs/p3a_operator_20261027`: mtime unchanged
  `2026-11-17 15:42:26.390938519 -0800`, `journal.jsonl` sha256 `1e73e80f…`; **attempt-1 lease log**
  `/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl` **not appended** (size 55,726 B, mtime
  `2026-11-17 15:42:35.402938959 -0800`, matching the accepted host check). The only lease action was the
  exclusive `flock` on `~/r1_locks/gpu0.lock` (which moved that lock file's mtime, expected and documented);
  **no lease-log write** (`gpu/gpu_lease_status.txt`).
- **TASL-7 not accessed/touched; HTCondor/deepthought not touched; no forced GPU sharing; no other user's
  process touched; no secrets/credentials read.**
- Track P `trackp-gpu` venv unmodified (`base_venv_unchanged.txt`); base repo clean at `897d83c8`; kit worktree
  at `7330338` clean apart from the expected untracked data link; GPU after = before (353 MiB desktop, 0 %, no
  compute apps); no leftover processes/cgroup scopes/tmp dirs; `/dev/shm` empty; disk 362 GiB free.

## 10. STOP / GO

**No STOP condition occurred: this TASL-2 option-A smoke is a PASS** (`CHECKLIST_E_PASSED`, `effective:true`,
`waivers {}`, `exceptions []`, private `/dev/shm`, no CUDA IPC, no co-tenant, no OOM, measured slowdown). The
author-signed task asked only for env + data + **one** clean isolated smoke + measured slowdown + report;
**U2 was not run** and is not authorised by this report. Carry forward: the measured **3.225× B1 / 3.176× smoke
wall / 0.2345 s per 1 GiB logits request** option-A cost, 1,980.1 MB baseline peak VRAM, 5.17 GiB of the 8 GiB
cgroup cap, and the disclosed deviations in §7. §3 item 7 CUDA IPC remains untested/not passed; no
`cuda_share`/`cuda_open` node may start on the strength of this report.

---

**AI-assisted: DeepSeek Harness agent (`tasl2-ar-runner`), 21 Nov 2026. ENGINEERING_ONLY; uncommitted;
no push.**
