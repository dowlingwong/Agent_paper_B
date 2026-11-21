# TASL-2 T1 pre-launch evidence report — G.1b on the TASL pair (21 November 2026)

**Status: PASS — TASL-2 is prepared for the G.1b launch: harness at pin `c025f89a` clean; `torch312`/`jax312`
built with uv from the committed census freezes at Python 3.12.16; the `T1_TASL_PLAN.md` §6 host test items in
scope on TASL-2 pass; the `HARNESS_ISOLATION_20261117.md` §3 items 1–7 pass at the pin.** ENGINEERING_ONLY;
AI-assisted (DeepSeek Harness agent `tasl2-t1-prep`, delegated by the lead). No job was launched, no GPU lease was
held beyond the seconds of the synthetic probes, nothing was committed or pushed, nothing was deleted or moved
aside, and TASL-7, the Track P attempt-1 archive/lease log, HTCondor and deepthought were not touched.

Authority: `R1-T1-HOST-TASL` / `sweep2/t1_tasl/T1_TASL_PLAN.md` §2 (host-check record), §6 (host test), and the
`R1-T1-TASL-ENV` environment row (uv from the census freezes, Python 3.12.16). The launch precondition record is
[`TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md`](TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md) (four
`host_check_*` lines, §3 PASS table at the pin); this report is its pre-launch evidence and covers the §6 items
as well. Both are uncommitted on the Mac ops worktree `main_t1_host_reports_20261121` (baseline `d47d1008`); the
lead commits them to `main`.

## 1. Host identity

`TASL-2` (zhixu portal), Ubuntu 22.04.5 LTS, kernel `6.8.0-149-generic #149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC`,
32 CPUs, 62 GiB RAM, cgroup v2 (`/sys/fs/cgroup` = `cgroup2 rw,…,nsdelegate,memory_recursiveprot`), NVIDIA driver
`535.309.01`. Run uid/euid `1008(dowling)` (non-root, no sudo), groups `1008` only. Local clock PST (UTC−8);
report times UTC.

- GPU: `GPU 0: NVIDIA GeForce RTX 4090 (UUID: GPU-4d623e76-7587-ee15-a633-46f60d220d94)`, 24 564 MiB,
  driver 535.309.01; `--query-compute-apps` empty before/after every step (353 MiB used is the pre-existing
  desktop reservation, 0 % utilisation).
- LSM `lockdown,capability,landlock,yama,apparmor`; `kernel.yama.ptrace_scope=1`;
  `kernel.unprivileged_userns_clone=1`, `kernel.apparmor_restrict_unprivileged_userns=0`,
  `user.max_user_namespaces=254738`.
- Disk `/dev/nvme0n1p2` 1.9 TiB, **354.6 GiB free** after the environments were built (362 GiB before).
- Run root: `/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/` (`scripts/`, `captures/`, `logs/`,
  `records/`, `env_build/`, `work/`).

Exact command (all steps): `ssh -o BatchMode=yes portal_zhixu`, then
`cd /home/dowling/r1_engineering/tasl2_t1_precheck_20261121 && bash scripts/run_checks.sh`. Every step's command
and output is in `captures/`; `captures/step_results.txt` lists the rc of each step (all rc 0).

## 2. What was set up on TASL-2 (G.1b base, environments, harness)

### 2.1 Base directories

`/home/dowling/r1_tracks/t1_tasl/` with `base/`, `runs/`, `sealed_g1b/`, `sealed_g4/`, `data/`, `proposer/`,
`envs/` (and `harness/`, below), owner `dowling:dowling`, mode 775 (`captures/t1_dirs.txt`). The pre-existing
`/home/dowling/r1_tracks/{bin,launch,logs,models,opt,out,remotes,scratch,venv,work}` (Track S, mtimes 29 Oct–12 Nov)
were not modified.

### 2.2 Python 3.12.16 and uv

- uv `/home/dowling/.local/bin/uv`, **`uv 0.13.6 (x86_64-unknown-linux-gnu)`** (not on `PATH` by default; used by
  absolute path as the spec's `hosts.*.uv` names it).
- `uv python install 3.12.16` → `Installed Python 3.12.16 in 3.04s`, rc 0, from the GitHub release download
  (`captures/env_uv.txt`; network reachable: GitHub HTTP 200 and PyPI installs below rc 0).
- Interpreter source: `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`
  (`uv python find 3.12.16`); the uv-managed "3.12" alias directory
  `…/cpython-3.12-linux-x86_64-gnu/bin/python3.12` is a symlink to it (the runner's symlink-chain binding handles it;
  C4 below passes).

### 2.3 `envs/torch312` and `envs/jax312`

Built exactly as the census row requires — `uv venv --python 3.12.16`, then `uv pip sync` from the committed census
freezes staged on the host, then `uv pip freeze` compared with the freeze:

| env | freeze file | committed freeze sha256 | `uv pip freeze` (sorted lines) | Python | interpreter |
|---|---|---|---|---|---|
| `torch312` | `sweep2/g1b/env/torch312.freeze.txt` | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` | equal (77 packages) | 3.12.16 | `envs/torch312/bin/python` → `…/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12` |
| `jax312` | `sweep2/g1b/env/jax312.freeze.txt` | `80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1` | equal (68 packages) | 3.12.16 | `envs/jax312/bin/python` → same uv-managed 3.12.16 |

- `torch312`: **byte-for-byte equal** to the freeze (`uv pip freeze` sha256 = `d2e70fe4…`, same as the freeze);
  torch **2.6.0+cu124** (CUDA 12.4), `torch.cuda.is_available()=True`, device `NVIDIA GeForce RTX 4090`,
  capability (8,9); a synchronised device tensor gave `tensor_sum=4096.0` and a 16×16 matmul `16.0`
  (`captures/env_check.json`). 5.4 GiB.
- `jax312`: **same package set/line multiset** as the freeze (Python `sorted` equality, which is exactly the
  launch check `g1b_lib.compare_freeze`), and **byte-for-byte equal to the committed file in the census host's
  collation**: `uv pip freeze | LC_ALL=en_US.UTF-8 sort` reproduces the committed bytes
  (sha256 `80a455c6…`); uv 0.13.6's own freeze order differs from the committed file only by the adjacent
  `optax` / `opt-einsum` pair (uv bytes sha `956d0b4f…`). No package version differs. jax **0.4.35** with
  `jax-cuda12-plugin` 0.4.35 CUDA-12 (the freeze already excludes `nvidia-cuda-nvcc-cu12`, as the census built it):
  direct `jax.default_backend()=gpu`, `jax.devices()=[CudaDevice(id=0)]`, jitted matmul 16.0; 4.9 GiB.
- **No `LD_LIBRARY_PATH` / `LD_PRELOAD`** is set or needed (recorded in `env_check.json`; the wheels bundle their
  CUDA libraries). Both environments are **separate from the existing venvs**: distinct realpaths/prefixes under
  `/home/dowling/r1_tracks/t1_tasl/envs/`, disjoint from `/home/dowling/r1_trackp/venvs/{ar-cond7a,trackp-gpu,
  trackp-cpu}` (`captures/env_check.json` `separation`). `pyvenv.cfg` of both: `home = …/cpython-3.12.16-…/bin`,
  `uv = 0.13.6`, `version_info = 3.12.16`, `include-system-site-packages = false`.
- `uv pip freeze` outputs are recorded in `captures/env_check.json` (`uv_freeze_sha256`) and the build transcript
  is `captures/logs/env_sync.log`; the freezes' own sha256 on the host are in `captures/env_freeze_sha.txt`.

### 2.4 Harness at the G.1b/T1 pin

Cloned from `https://github.com/dowlingwong/autoresearch_harness.git` and checked out **detached** at
`c025f89aeafc2199bf3487b4bcaa16678273c702` (branch `mac-trackg-t1-tasl-20261121`; tip chain `af48080` →
`6843847` → pin) in `/home/dowling/r1_tracks/t1_tasl/harness`:

- `git rev-parse HEAD` = `c025f89aeafc2199bf3487b4bcaa16678273c702` before and after the checks; `git status
  --porcelain` empty both times; no branch (detached); `origin/mac-trackg-t1-tasl-20261121` resolves to the same
  commit; `PYTHONDONTWRITEBYTECODE=1` for every probe (`captures/harness_pin.txt`,
  `captures/harness_pin_after.txt`, `captures/logs/harness_clone.log`). 29 MiB.

## 3. `T1_TASL_PLAN.md` §6 host test — results on TASL-2

Items 6–8 of §6 concern TASL-7 (the proposer `llama-server`, its `/props`, Tailscale, per-call LLM time) and are
outside this host's scope; the §6.3 4090/Ada ratio is measured by each node job's first part, so pre-launch it is
recorded as DEFERRED with a synthetic proxy. All TASL-2 items pass:

| §6 | Item | Result | Evidence |
|---|---|---|---|
| 1 | delegated scope `systemd-run --user --scope -p Delegate=yes` with `MemoryMax=8G`, `MemorySwapMax=0`, `cgroup.kill`, and the isolation probes inside it | **PASS** | scope `run-r53ad01a5…scope`: `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` exists, `nsdelegate=True`, owner uid 1008; `isolation.RunCgroup` create→join→`cgroup.kill`→empty→removed. The sandboxed smoke/GPU/jax smokes ran inside these scopes (`c3_cgroup.json/.txt`, `c5_smoke.json`, `c6_gpu_smoke.json`, `c6b_jax_gpu_smoke.json`) |
| 2 | `nvidia-smi -L` full UUID; no resident compute process | **PASS** | `GPU 0: NVIDIA GeForce RTX 4090 (UUID: GPU-4d623e76-7587-ee15-a633-46f60d220d94)`; `--query-compute-apps` empty before/after every probe (only our own synthetic processes appear mid-run) (`nvidia_smi_L.txt`, `gpu_state_before/after.txt`, `gpu_compute_apps_*_all.txt`) |
| 3 | 4090/Ada ratio on each node's baseline | **DEFERRED** | measured by the G.1b job's first part (the plan's design); the synthetic GPU load below is the only pre-launch timing proxy |
| 4 | `mlgym_houseprice` on 8 CPU cores (8–15) beside a GPU node, without slowing it past its timeout | **PASS** | synthetic load check: CPU-only MLP pinned `[8..15]` with `CUDA_VISIBLE_DEVICES=""` (no `NVIDIA_VISIBLE_DEVICES`, no `_CONDOR_AssignedGPUs`; the child cannot see CUDA) beside a GPU MLP training loop on `[0..7]` by full UUID: GPU solo 20.0 s → concurrent 20.0 s (**ratio 1.0**, timeout 3× = 60 s), CPU solo 12.0 s → concurrent 12.0 s (ratio 1.0); `cuda_available=False` in the CPU child, GPU child on the 4090 (`c6c_cpu_gpu_coexistence.json/.txt`) |
| 5 | jax312 on TASL-2 from the census freeze (`uv pip freeze` equal); Python 3.12.16 | **PASS** | see §2.3 and §4 (direct GPU and sandboxed jax both pass; freeze line-equal and byte-equal in the census collation) |
| 6–8 | TASL-7 proposer/`/props`/Tailscale/LLM time | **OUT OF SCOPE** | TASL-7 host; not contacted from this task |

Additional TASL-2 pre-launch checks required by the task, all PASS: non-root uid (`euid=1008`, and the sandboxed
records show host euid 1008), `ptrace_scope=1`, harness clean at the pin, census env freezes equal at 3.12.16, and
disk ≥ 20 GiB free (354.6 GiB).

## 4. `HARNESS_ISOLATION_20261117.md` §3 items 1–7 at the pin

| # | Condition | Result | Key values |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces | **PASS** | `unshare(0x72020000)` rc 0 for torch312 3.12.16 and `/usr/bin/python3` 3.10.12; uid 1008→0 map; real tmpfs mount+write; child PID 1 of new PID ns |
| C2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `1`; unrelated same-uid sibling attach `EPERM` |
| C3 | delegated cgroup v2 subtree with `cgroup.kill`, 8G/swap 0 | **PASS** | see §3 item 1 above; `RunCgroup` kill → `empty_after true`, child rc −9, removed |
| C4 | non-root + interpreter `sys.path` hard check | **PASS** | `WorkingCopyRunner._sandbox_config` passes for `/usr/bin/python3`, `envs/torch312`, `envs/jax312`; `broad_entries=[]`; `worker_sandbox_available=True` for all three (`c4_interp.json/.txt`) |
| C5 | real sandboxed smoke, record `effective: true` | **PASS** | `effective true`, `waivers {}`, `exceptions []`, `euid 1008`, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `parent_traced_by null`, `parent_dumpable_at_accept false`; outcome ok 1.0; run `records/g0_smoke_20261121T100420Z` (`c5_smoke.json`, `records/g0_smoke/`) |
| C6 | GPU smoke with the sandbox on | **PASS** | GPU by UUID; `effective true`, `waivers {}`, `exceptions []`; worker PID 1, `cuda_available true`, device 4090, `tensor_sum 4096.0`, matmul 16.0, 33.6 MB allocated, no CUDA error, metric written, cgroup removed (`c6_gpu_smoke.json`, `records/gpu_smoke/`) |
| C7 | end state: GPU before/after, no leftovers, disk, host/kernel, versions | **PASS** | GPU identical (353 MiB, no compute apps, 0 %); six leftover buckets all empty; 354.6 GiB free; harness clean at `c025f89`; Track P archive/lease log `stat`-unchanged (mtimes 2026-11-17); no cgroups/tmp dirs/`/dev/shm` left (`c7_final.json/.txt`) |

Supplementary: the pin's own `tests/trackg/test_trackg_isolation.py` under a delegated scope — **27 passed,
1 skipped in 15.30 s** (`pytest_isolation.json`; skip = root-only `test_unprivileged_end_to_end`). Timeout factor 3
is the unit default, not waived.

### jax312 GPU inside the worker sandbox (Breakout node environment)

`c6b_jax_gpu_smoke.json` / `records/jax_gpu_smoke/`: `effective:true`, `waivers {}`, `exceptions []`, no
exceptions; the editable trainer ran in the sandboxed worker (pid 1, `ppid 0`, own user/mount/PID namespaces,
private `/dev/shm`): jax **0.4.35**, backend **gpu**, `devices ["cuda:0"]`, device kind `NVIDIA GeForce RTX 4090`,
tensor sum 4096.0, jitted matmul 16.0, and `gymnax.make("Breakout-MinAtar")` → `MinBreakout` obs `(10,10,4)` **on
`cuda:0`**. The direct (unsandboxed) jax check in `env_check.json` agrees (`backend=gpu`, `[CudaDevice(id=0)]`).
Note the sandboxed worker shows `uid 0` inside its user namespace (host euid 1008) — that is the isolation mapping,
not a root run.

## 5. End state, scope, and non-authorities

- GPU idle before and after (353 MiB desktop reservation, no compute apps, 0 %); disk **354.6 GiB free**; no
  leftover processes, cgroups, tmp dirs or `/dev/shm` entries from the checks.
- Harness `/home/dowling/r1_tracks/t1_tasl/harness` still detached at `c025f89a`, `git status --porcelain` empty.
- No job was launched; no attempt directory, no `runs/` output, no `sealed_*` content was created. The GPU lease
  `~/r1_locks/gpu0.lock` was held with `flock` only for the seconds of the GPU/jax/coexistence probes; the Track P
  lease log `runs/_attempt1_gpu_lease_log.jsonl` was not written (mtime still 2026-11-17 15:42:35). The Track P
  attempt-1 archive `runs/p3a_operator_20261027` was `stat`-ed only (mtime 2026-11-17 15:42:26, size 4096).
- TASL-7 was not contacted; HTCondor and deepthought were not touched. Nothing was deleted or moved aside; the only
  host changes are the new `/home/dowling/r1_tracks/t1_tasl/` tree (dirs, 2 envs = 11 GiB, harness 29 MiB), the
  uv-managed Python 3.12.16, and the new run root above.
- Nothing was committed or pushed from either side; the reports and the fetched captures are uncommitted in the
  Mac ops worktree. The G.1b spec (`sweep2/t1_tasl/g1b_tasl_spec.json`) still has
  `hosts.TASL-2.isolation_host_check.sha256 = "PENDING"`; the sha256 of the binding file is given below for the
  lead to fill when committing.

## 6. Captures

Sibling directory `TASL2_T1_PRECHECK_20261121_captures/` (fetched from
`/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/captures/`), **91 files**, 724 KiB,
`SHA256SUMS` sha256 **`e604aff7f40815e6d17d415296534b773cf781820125a07cd1e98240ae985eaf`**;
`sha256sum -c SHA256SUMS` rc 0 on TASL-2 and with `shasum -a 256 -c SHA256SUMS` after the fetch. The SHA256SUMS
digest file itself is kept outside the captures on the host
(`/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/SHA256SUMS.sha256`).

- `SUMMARY.json`, `SUMMARY.txt` — the PASS tables above and the GO/STOP verdict.
- `host.json`, `host_facts.txt`, `host_facts` text — host/kernel/uid/cgroup/sysctl/disk/GPU/tool facts and the
  harness pin state; `nvidia_smi_L.txt`, `gpu_state_before/after.txt`, `gpu_compute_apps_*.txt`.
- `harness_pin.txt`, `harness_pin_after.txt`.
- `env_check.json/.txt`, `env_uv.txt`, `env_freeze_sha.txt`, `logs/env_sync.log`, `logs/harness_clone.log`.
- `c1_userns_venv.json`, `c1_userns_syspy.json`, `c2_ptrace.json`, `c3_cgroup.json/.txt`, `c4_interp.json/.txt`,
  `c5_smoke.json`, `c6_gpu_smoke.json`, `c6b_jax_gpu_smoke.json`, `c6c_cpu_gpu_coexistence.json/.txt`,
  `c7_final.json/.txt`.
- `records/g0_smoke/`, `records/gpu_smoke/`, `records/jax_gpu_smoke/` — run records, logs, result channels and
  the GPU/jax reports.
- `pytest_isolation.json`, `logs/pytest_isolation.log`.
- `gpu_lease_status.txt`, `jax_lease_status.txt`, `cpu_gpu_lease_status.txt`; `logs/` for every probe;
  `scripts/` for the orchestration/probes and the exact unit files used (`unit_isolation.py`, `unit_runner.py`,
  `unit_isolated_fixture.py`, `unit_gpu_identity.py`, `unit_noise_floor.py`).

## 7. Findings and residuals

1. **jax freeze byte order (no action needed for launch).** uv 0.13.6 `uv pip freeze` orders `opt-einsum` before
   `optax`; the committed census freeze has `optax` first (the census file is the freeze set in the host's
   `en_US.UTF-8` collation). The launch check `g1b_lib.compare_freeze` compares sorted lines, and the byte-equal
   form is reproduced with `LC_ALL=en_US.UTF-8 sort`; no package or version differs. Recorded in
   `env_check.json`; not a STOP.
2. **§6.3 ratio deferred** to the G.1b job's first part on the 4090, as the plan designs; the synthetic proxy
   (GPU job solo 20.0 s vs beside a full 8-core CPU load 20.0 s) shows no host-level interference.
3. **§6.6–6.8 are TASL-7 items** (proposer server, `/props`, Tailscale reachability/latency, per-call LLM time) and
   are out of scope of this TASL-2 report; the TASL-7 prep/report covers them.
4. **CUDA IPC under the PID namespace remains untested** (`HARNESS_ISOLATION` §5 item 5); C6 exercises device
   allocation/synchronisation, not CUDA IPC. G.1b/G.4 option-A paths use the CPU result channel, and the jax
   Breakout smoke additionally passes inside the sandbox.
5. **Scope of the CPU/GPU coexistence check:** synthetic, short (~12 s CPU / ~20 s GPU), pinned to the declared
   cpusets, not a full node; the real node's first part is the authoritative timing (item 2 above).
6. The uv-managed interpreter is under `$HOME` (read-only bound into the worker); the hard `sys.path` check still
   passes for both new envs (C4), as it did for the prior `trackp-gpu` venv on the fixed tree.
7. No waiver was used anywhere; `timeout factor 3` is the unit default.

## STOP / GO

All TASL-2 `HARNESS_ISOLATION` §3 items and all in-scope `T1_TASL_PLAN` §6 items pass at the pin, so there is no
STOP on this host: **TASL-2 is GO for the G.1b launch once the binding report is on published `main` with its sha256
recorded in the spec and the author's signed note plus both keys exist.** The remaining launch preconditions are
TASL-7's equivalent record and the author authorization, not this host.

**AI-assisted: DeepSeek Harness agent (`tasl2-t1-prep`), 21 Nov 2026. ENGINEERING_ONLY; uncommitted.**
