# TASL-7 T1 precheck: environments, harness pin, §6 host checks, G.4 proposer prerequisites (21 November 2026)

**Status: PASS for the setup and for the seven §3 host conditions at harness pin
`c025f89aeafc2199bf3487b4bcaa16678273c702`; the T1 precheck is PASS subject to two launch preconditions that
need an author/reviewed decision before G.1b/G.4 start on this host (P1: jax312 `ptxas` host adaptation for
`mlgym_breakout_minatar`; P2: the G.4 spec's client `server_url` must be the shared-node `100.106.74.50`, not
`.51`). ENGINEERING_ONLY; AI-assisted (DeepSeek Harness agent, `tasl7-t1-prep`, delegated by the lead for
author-signed R1-T1-HOST-TASL / `T1_TASL_PLAN`). Nothing was committed or pushed; the working tree stays
uncommitted on the Mac ops worktree.**

This is the operator record for step 1–2 and the host-test items of `T1_TASL_PLAN.md` §5/§6 on TASL-7. The
binding host-check record it cites is
`docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md`, sha256
**`09945c15df67b2627a97e6cc59239744738aecb14e522f7c52d1f390be4576a4`** — that is the file and sha256 for
`g1b_tasl_spec.json`/`g4_tasl_spec.json` `hosts["TASL-7"].isolation_host_check` once it is published on `main`.

## Authority and inputs

- Task authority: author-signed **R1-T1-HOST-TASL** (published `main` at `d47d1008`), delegated by the lead:
  set up `/home/dowling/r1_tracks/t1_tasl`, install the T1 environments, clone the harness at the pin, run the
  G.1b plan §6 host checks on TASL-7, check the G.4 proposer prerequisites (binary/build-dir manifest/GGUF/
  Tailscale), and write this report. No deletion (move aside only), no push, TASL-2 untouched.
- `T1_TASL_PLAN.md` (`sweep2/t1_tasl/`, sha256
  `fc5606ae75fa486a45af98d1ec848c0ae4ee342d55359024a5184046f0f2867c`) §1 (harness pin, host roles), §2 (the
  census runner and the `host_check_*` precondition), §5 (operator steps), §6 (needs a host test).
- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` (sha256
  `ac3d5cd0abc262efe8d0552770336ef49dc9cd48cd41704c722ed85c08a5473f`) §3/§5.
- Original reviewed TASL-7 check: `TASL7_ISOLATION_HOST_CHECK_20261121.md`, sha256
  `2b703226e6aec430df24b3333ed002940023c99aa8d535392e117aa4b40f2abf`, review
  `18e261cd3641d3ec370599c8f38131862ef8c3e5e1b92659f08c984202fa15d5`. TASL-7 proposer smoke:
  `TASL7_PROPOSER_SMOKE_20261121.md`, sha256
  `be507eb1a57a6de5d1c0636c4e821fb850a07f1c49b162dc1923ae1b48f7b379` (its F1 is the `.50`/`.51` Tailscale
  fact this report re-checks from TASL-7's side).
- Mac ops worktree: `.../.claude-worktrees/main_t1_host_reports_20261121` at HEAD
  `aaf2254a878629fd8a03e388a5d684a290ef4c9b` (on `main` baseline `d47d1008`). The two reports of this task and
  the capture bundle are **untracked** (`??`); no commit, no push.

## 1. Layout created on TASL-7 (new)

`/home/dowling/r1_tracks/t1_tasl/` (all new, no pre-existing file moved or deleted):

```
base/        the two census freeze files (copied from sweep2/g1b/env/)
envs/        torch312/ and jax312/ (uv venvs, Python 3.12.16)
harness/     autoresearch_harness clone, detached at c025f89a, clean
runs/        G.1b/G.4 run root (empty)
sealed_g1b/  G.1b sealed root (empty; sealed_g4 is the G.4 sibling, created by that launch)
data/  proposer/  work/  records/  captures/  scripts/  logs/
```

`data/` is empty (the host's node data is staged by the node's own `setup_command`); `proposer/` holds the
copied `g4_tasl.py` helper tree used for the build-directory manifest (see §4). Nothing is under Track P's
trees: `/home/dowling/r1_trackp/venvs/trackp-gpu` and `/home/dowling/r1_trackp/harness_cond7a_20261121_t7` were
not used or modified by this task (separate T1 envs, no `LD_LIBRARY_PATH`, below).

## 2. Python 3.12.16 and the T1 environments (R1-G1B-CAP / census freezes)

- **uv**: `/home/dowling/.local/bin/uv`, `uv 0.13.6 (x86_64-unknown-linux-gnu)` (not on the non-interactive
  PATH; recorded and invoked by absolute path).
- **Interpreter source**: `uv python install 3.12.16` → `Installed Python 3.12.16` (2.68 s);
  `uv python find 3.12.16` = `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`;
  `uv python dir` = `/home/dowling/.local/share/uv/python`. Both venvs' `bin/python` symlink resolves to that
  standalone build (uv-managed python-build-standalone; `Python 3.12.16 (main, Oct 26 2026, 14:08:45) [Clang
  23.1.3]`). The build lives under `$HOME`, which the unit's `sys.path` hard check permits (C4 below).
- **Build**: `uv venv --python 3.12.16 <env>` then `uv pip sync --python <env>/bin/python base/<env>.freeze.txt`,
  one env at a time, with no `LD_LIBRARY_PATH`/`LD_PRELOAD` in the environment. Separate from the Track P
  `trackp-gpu` venv (3.12.15) by construction; nothing in the T1 tree imports from it.
- **Result** (`c0_envs.json/.txt`; installed size on disk: `torch312` 5.4 GiB, `jax312` 4.9 GiB):

| env | interpreter | Python | freeze file sha256 | installed `uv pip freeze` sha256 | bytes equal | sorted equal | key packages |
|---|---|---|---|---|---|---|---|
| `torch312` | `t1_tasl/envs/torch312/bin/python` | 3.12.16 | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` | **yes** | yes | torch 2.6.0+cu124, CUDA 12.4, `cuda.is_available=True` (77 lines) |
| `jax312` | `t1_tasl/envs/jax312/bin/python` | 3.12.16 | `80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1` | `956d0b4fcf28e48451ae4b92a451a2c2db764805378ffbcd6b01a2649caf8d0a` | no (1 pair order) | **yes** | jax 0.4.35, jaxlib 0.4.34 (68 lines) |

The `jax312` byte difference is **sort order only**: the census file has `optax==0.2.4` before
`opt-einsum==3.4.0`, while `uv 0.13.6`'s freeze sorts `opt-einsum` first (unified diff in
`c0_envs.json` → `envs.jax312.freeze_byte_diff`). The 68 `name==version` lines are the same multiset, and the
launch check is `g1b_lib.compare_freeze`, which sorts both sides before comparing; the `sha256` of the committed
freeze file (the value pinned in the spec) is the census one, `80a455c6…`. Disclosed because the task asked for a
byte-equal check: `torch312` is byte-equal, `jax312` is sorted-equal.

## 3. Harness at the pin (detached, clean)

`/home/dowling/r1_tracks/t1_tasl/harness` — `git clone --branch mac-trackg-t1-tasl-20261121 --single-branch
https://github.com/dowlingwong/autoresearch_harness.git`, then `git checkout --detach
c025f89aeafc2199bf3487b4bcaa16678273c702`:

- HEAD `c025f89aeafc2199bf3487b4bcaa16678273c702` (full), tree
  `fa1526f44c79f9c5dcb6b84ed281814045b7add5`, branch `HEAD` (detached), `git status --porcelain` **empty**.
  Log head: `c025f89` ← `af48080` ← `6843847` ← `a69c8ef` ← `b574706` (the G.1b/G.4 pin) ← …
- `git merge-base --is-ancestor` yes for the accepted isolation core `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e`
  and the accepted Ada host-check fix `5403392e94cb59d732f45d6702fc857531ad8fd5`, and for
  `b5747066`/`68438477`/`af480809`. All seven conditions below ran against this tree
  (`c0_assertions.json`, `host.json`).
- The pin matches `g1b_tasl_spec.json`/`g4_tasl_spec.json` `harness.commit` and the branch name.

## 4. G.1b plan §6 host checks (what the launch precondition needs)

The full record is the bound report `TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md` (path/sha above). Summary:

- **The seven HARNESS_ISOLATION §3 items at the pin: PASS, no waiver, no exception** (captures C1–C7 in the
  bundle map to §3 items as: C1 = item 1 user+mount+PID+network(+cgroup) namespaces with a real tmpfs mount;
  C2 = item 2 `ptrace_scope=1`; C3 = item 3 delegated cgroup v2 scope with `memory.max=8589934592`,
  `memory.swap.max=0`, `cgroup.kill` and the unit's `RunCgroup` create→join→kill→remove; C4 = item 4 non-root
  (euid 1011) and item 5 the interpreter `sys.path` hard check for `/usr/bin/python3`, `torch312` **and**
  `jax312` (`broad_entries []`, sandbox available); C5 = item 6 sandboxed smoke `effective: true`, `waivers {}`,
  `exceptions []`; C6 = item 7 GPU smoke in the sandbox `effective: true`, worker PID 1, RTX 4090 by full UUID,
  `tensor_sum 4096.0`) — with the item-7 **CUDA IPC limit stated** in the bound report (untested, §5.5 open; AR
  option A only). C7 is the end state (no leftovers, GPU idle, worktree clean, disk, Track P untouched), not a
  §3 item; the unit's isolation test file passes **27 passed, 1 skipped**.
- **Environment binding (E1):** PASS — uv/Python/freezes as in §2, no `LD_LIBRARY_PATH`/`LD_PRELOAD`/`LD_AUDIT`.
- **Binding assertions (A0):** PASS — hostname `TASL-7`; harness HEAD/tree/clean/detached/ancestry; GPU
  `nvidia-smi -L` = `GPU 0: NVIDIA GeForce RTX 4090 (UUID: GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1)`, model
  match, **no resident compute process**; `ptrace_scope=1`; cgroup2 mounted with `nsdelegate` and the user slice;
  freezes are the expected bytes; disk ≥ 100 GiB free (507.2 GiB at check time).
- **jax312 GPU (the G.1b `mlgym_breakout_minatar` environment) — two results, both captured:**
  - **J1a FAIL as the environment stands.** JAX sees the GPU (`default_backend gpu`, one CudaDevice, RTX 4090)
    but the first JIT fails: `XlaRuntimeError("NOT_FOUND: Couldn't find a suitable version of ptxas …")`. Cause:
    the census `jax312` freeze ships no `nvidia-cuda-nvcc-cu12` (no bundled `ptxas`), and TASL-7 has its CUDA
    toolkit versioned at `/usr/local/cuda-12.2` with **no `/usr/local/cuda` symlink** (so the backend's default
    search path misses it; `/usr/local/cuda-12.2/bin/ptxas` exists). `c6b_jax_gpu.json`.
  - **J1b PASS with the standard host adaptation.** With
    `XLA_FLAGS="--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2 --xla_gpu_deterministic_ops=true"` the same probe
    runs on the GPU: `tensor_sum 1048576.0`, 32×32 matmul 32.0, `default_backend gpu`, full-UUID
    `CUDA_VISIBLE_DEVICES`, delegated 8 GiB scope, no CUDA error (`c6b_jax_gpu_xla_cuda_dir.json`). The node's
    own `ar_worker.py` **appends** to `XLA_FLAGS` (`os.environ["XLA_FLAGS"] = os.environ.get("XLA_FLAGS","") +
    " --xla_gpu_deterministic_ops=true"`), and the worker sandbox passes `XLA_*` variables by allow-list, so the
    flag survives into the sandboxed worker.
  - Consequence for launch (precondition **P1**): without the flag (or a `ptxas`-providing package/`PATH`), the
    `mlgym_breakout_minatar` G.1b node on TASL-7 will fail in the engine at the first JIT, after the host checks
    pass. This needs the author's environment row (R1-T1-TASL-ENV) to name the host adaptation (the flag is the
    surgical one) and the kit/runbook to set it for the jax node; it is a host/toolkit difference, not an
    isolation defect.
- GPU lease used by the GPU and jax probes: `~/r1_locks/gpu0.lock` via `flock` only, about 1–3 s each, a second
  process's non-blocking `flock` returns busy (`second_flock_rc=1`), no lease-log write; the C7 fingerprint of
  both attempt-1 lease-log candidates is stat-identical before/after and the archive is content-identical (see
  the bound report).

## 5. G.4 proposer prerequisites (TASL-7, in place; no G.4 run)

All from `captures/proposer/`, `proposer_precheck.sh`; the *whole* build directory was hashed with the merged
main's own helper `g4_tasl.py bin-manifest` (the script copied from the Mac ops worktree, sha256
`aeaab7b9a5f9ffb726189b21cf5a7bb7e825c83cdf17d3231baf8dd6f6feb996`, run with its sibling imports
`g1b_tasl.py` `90bb260e…`, `g4_lib.py` `6a9cb9ff…`, `g1b_lib.py` `8b1e78c2…`, and the `s2_c2_lib.py` dependency
`640e5e09…` that `g4_lib` imports).

| Item | Value |
|---|---|
| Binary | `/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server` |
| Binary sha256 | `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b` (matches the spec; ELF 64-bit PIE, GNU/Linux) |
| Build (`--version`) | `version: 0.7.0-dev (build 1, commit 620d222)`, `built with GNU 11.4.0 for Linux x86_64` (matches `expected_build`) |
| **Build-directory manifest sha256** (value for `g4_tasl_spec.json` `proposer.bin_dir_manifest_sha256`) | **`a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170`** |
| Manifest file | `proposer/bin_manifest.txt`, 24 lines (23 entries: 6 symlink lines + 17 regular files incl. `llama-server` and `libllama-server-impl.so`), file sha256 `52561323473415cdaa372969ed1a3c4b6a973cdb60e5f185e2c4bc660ce2bff7`; the helper's digest equals the recomputed sha256 of the manifest text |
| `ldd` resolution | rc 0, **0 `not found`**; 8 `libllama*`/`libggml*`/`libmtmd*` lines, **all 8 resolve inside the build directory**, 0 outside; binary `RUNPATH` = `/home/dowling/exam-x/work/llama.cpp/build-exam/bin:` |
| Environment | run with `LD_LIBRARY_PATH` and `LD_PRELOAD` **unset** (recorded `<unset>` in `proposer/identity_inputs.txt`) |
| GGUF | `/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf`, sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`, 19 598 489 952 B (both match the spec) |

The `bin_dir_manifest_sha256` is the one value still `PENDING` in `g4_tasl_spec.json` from this task; the file
itself is being edited by the lead/experiment agent (uncommitted `M`), so this report records the value instead
of editing the spec.

### Tailscale facts and the bind-only test (`captures/proposer/tailscale*`, `captures/bind_test/`)

- TASL-7's own tailnet address is **`100.106.74.51`/32 on `tailscale0`** (`tailscale ip -4`; `ip -4 -o addr`);
  TASL-2 is not a peer in TASL-7's tailnet. TASL-7 is a **shared Tailscale node**: TASL-2's tailnet sees the
  same host under the shared-node alias **`100.106.74.50`** (TASL7_PROPOSER_SMOKE F1). From TASL-7, `.50` is
  **not a local address** — `bind(100.106.74.50)` fails `EADDRNOTAVAIL` (errno 99) while `bind(100.106.74.51)`
  succeeds, and `.51` is `local … dev lo` in the route table; `.50` routes out via the LAN gateway
  (`100.106.74.50 via 10.12.152.1 dev wlp4s0 src 10.12.152.96`).
- **Only viable pair: server bound to `.51`, client using `.50`.** TASL-7 can only bind `.51` (its only tailnet
  address; `.50` cannot be assigned here), and TASL-2 can only reach the node via `.50` (literal `.51` times out
  from TASL-2; established connections to `.50` arrive on TASL-7 with local address `.51`; TASL7_PROPOSER_SMOKE
  F1 and review). The bind test confirms TASL-7's half: one short start of the exact exam server
  (`-c 32768 -ngl 999 -np 1 --jinja --cache-type-k/v q8_0 --no-webui`, 31B GGUF, full-UUID GPU, exclusive
  lease) bound to `.51:8096` only — `ss` listener `100.106.74.51:8096`, **not `0.0.0.0`** (the LAN address
  `10.12.152.96:8096` refuses), `/health` 200 `{"status":"ok"}`, `/props` `build_info b1-620d222`, `n_ctx
  32768`, `total_slots 1`, alias `gemma4_31b`; SIGTERM stop in ≈ 1 s, no compute app after, GPU back to 44 MiB,
  lease released, lease logs unchanged. Started `10:09:13Z`, health `10:09:17Z`, SIGTERM `10:09:17Z`, gone
  `10:09:18Z`.
- **Precondition P2 (G.4 spec):** `g4_tasl_spec.json` currently has `proposer.server_url =
  "http://100.106.74.51:8095"`. The worker on TASL-2 calls `/health`, `/props` and the latency probes on
  `server_url` (`g4_tasl.server_identity`, `latency_probe`) and `check_server_record` compares the record's
  `server_url` to the spec, so with `.51` the G.4 pilot would STOP on TASL-2 at the first call. Keep
  `tailscale_address: 100.106.74.51` (the bind address) and set `server_url` to
  `http://100.106.74.50:8095` (the client address); `serve` takes only the port from `server_url`, so the bind
  is unchanged. This is a spec-field change, not a code change; it needs the experiment agent's edit and the
  author's spec sha binding.

## 6. End state / preservation

- Disk after setup: **507.2 GiB free** on `/` (the two envs add ≈ 10.3 GiB; the earlier 514.0 GiB figure is
  pre-setup).
- GPU after all GPU work: 44 MiB used, 0 %, **no compute apps** (`gpu_state_after.txt`,
  `gpu_compute_apps_after_all.txt`); no leftover processes, cgroups or tmp dirs (`c7_final.json`).
- Track P: attempt-1 archive `/home/dowling/r1_trackp/runs/p3a_operator_20261027` identical before/after
  (metadata tree `299237d0…`, content `af7ede86…`, 1040 entries / 724 files / 11 925 743 308 B); both attempt-1
  lease-log candidates stat-identical (`trackp_evidence.log` sha256
  `2e762c16c255634342f055d8e9647b6491724e3850ee0ce857b1bcece6842793`, 76 B; `gpu_lease_log.jsonl` sha256
  `e97e03d2a191009b266f3292a24191c5f9b793e8010d870801f5c07405298818`, 58 863 B). No lease-log write.
  `~/r1_locks/gpu0.lock` itself: 0 B, inode 56 251 186 and content unchanged, but its **mtime/ctime were
  refreshed by the first two GPU probes' O_TRUNC open** (before the scripts were changed to append-mode opens);
  disclosed in the bound report, and the launch path (`g4_tasl.py`) opens the lease `a+`.
- TASL-2 was not logged into or touched; HTCondor/deepthought not touched; no file deleted or moved aside; no push.

## 7. Preconditions / blockers before G.1b/G.4 launch

| # | Item | Severity | Action |
|---|---|---|---|
| P1 | `jax312` cannot JIT on TASL-7 as configured (`ptxas` not found; toolkit at `/usr/local/cuda-12.2`, no `ptxas` in the freeze) | **blocks the `mlgym_breakout_minatar` G.1b node on TASL-7** | author/row decision (R1-T1-TASL-ENV) to add the host adaptation — `XLA_FLAGS=--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2` (proven, J1b) or an equivalent reviewed change — and the kit/runbook must set it; everything else on the node path passes |
| P2 | `g4_tasl_spec.json` `server_url` is `.51`, which TASL-2 cannot reach | **blocks G.4** | set `server_url` to `http://100.106.74.50:8095` (bind stays `.51`), then the spec sha binding is re-taken |
| P3 | `g4_tasl_spec.json` `bin_dir_manifest_sha256` = `PENDING` | blocks the proposer start check | use `a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170` |
| P4 | `hosts["TASL-7"].isolation_host_check.sha256` = `PENDING` | blocks the G.1b/G.4 host-check precondition | publish this binding report on `main` and use sha256 `09945c15df67b2627a97e6cc59239744738aecb14e522f7c52d1f390be4576a4` |
| P5 | TASL-2's binding report/sha and its jax312 env (its own task) | blocks TASL-2 nodes | outside this task (TASL-2 untouched); the G.1b spec's TASL-2 host-check sha is `PENDING` |
| — | Author keys/signed notes, both `--enable` keys, both keys per `T1_TASL_PLAN.md` §5 | — | author/operator |

No STOP condition of `T1_TASL_PLAN.md` §7 was triggered on TASL-7: the seven host checks pass, the lease was free
and exclusive, no foreign compute process was seen before or after any GPU part, and no disk/leftover problem
exists. The two preconditions above are decisions/edits, not host failures.

## 8. Captures

Sibling bundle `TASL7_T1_PRECHECK_20261121_captures/`: **170 files, 1.7 MiB**, `SHA256SUMS` sha256
**`19c4f6574782ace3ac24a6ff2754fd77858b07000cd169d3fdf05eccd11d3e8a`** (170/170 verified `sha256sum -c` on
TASL-7 and locally). Key paths inside the bundle: `c0_envs.json/.txt`, `c0_assertions.json/.txt`, `c1`–`c7`
probe files, `c6b_jax_gpu.json` (J1a), `c6b_jax_gpu_xla_cuda_dir.json` (J1b), `SUMMARY.json/.txt`,
`step_results.txt`, `records/` (unit run records), `proposer/` (binary, build-dir manifest, ldd, GGUF,
Tailscale, bind probe), `bind_test/` (start/stop, listeners, health, `/props`, lease), `attempt1_*` (Track P
preservation), `scripts/` (the exact run scripts). Host run root: `/home/dowling/r1_tracks/t1_tasl/`.

## 9. Deviations

1. `jax312` freeze byte-order (§2) — sorted-equal, the launch check sorts; disclosed in `c0_envs.json`.
2. `gpu0.lock` mtime/ctime refreshed by the first two GPU probes' O_TRUNC open; content/inode unchanged, no
   lease-log write; append-mode open afterwards (bound report deviation 1).
3. `captures/scripts/run_checks_t1.sh` is the post-run copy with the SHA256SUMS ordering fix (SHA256SUMS is the
   last write under `captures/`); the executed version differed only in that two-line epilogue. The bundle's
   `SHA256SUMS` was re-computed as the final write.
4. `g4_tasl.py bin-manifest` required the `s2_c2_lib.py` import dependency of `g4_lib`; it was copied next to
   the helper in `proposer/scripts/` (its sha recorded in §5). `bin_manifest_sha256` is unaffected (it hashes
   only the build directory).
5. The bind test used the exact exam binary and GGUF with the exam flags (the model was page-cache warm: load
   ≈ 1 s, total start→stop ≈ 5 s); it is a bind/identity test, not a G.4 run. TASL-2's side of the pair was
   cited from the reviewed proposer smoke, not re-run (no touch of TASL-2).
6. `proposer/` and the other extra dirs under the run root are for this precheck only; the spec's
   `proposer.run_dir` points there and the launch creates its own `run_id` subdirectory (`mkdir(exist_ok=False)`),
   so a pre-existing empty `proposer/` is harmless.

## 10. Verification

```
# Mac ops worktree, this report's directory
shasum -a 256 -c TASL7_T1_PRECHECK_20261121_captures/SHA256SUMS        # 170/170 OK
shasum -a 256 docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md
# TASL-7 (read-only)
/home/dowling/.local/bin/uv --version                                  # uv 0.13.6
/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python -VV           # 3.12.16
/home/dowling/r1_tracks/t1_tasl/envs/jax312/bin/python -VV             # 3.12.16
git -C /home/dowling/r1_tracks/t1_tasl/harness rev-parse HEAD          # c025f89a…
git -C /home/dowling/r1_tracks/t1_tasl/harness status --porcelain       # empty
/usr/bin/python3 /home/dowling/r1_tracks/t1_tasl/proposer/scripts/t1_tasl/g4_tasl.py \
  bin-manifest /home/dowling/exam-x/work/llama.cpp/build-exam/bin     # manifest_sha256: a29c667f…
cat /home/dowling/r1_tracks/t1_tasl/captures/SUMMARY.txt
```
