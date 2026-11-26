# TASL-2 host check at harness pin `aa354485` for expansion node `mlgym_metamaze` (26 November 2026)

**Status: PASS — host-check record for the G.1b expansion unit.** ENGINEERING_ONLY; AI-assisted (DeepSeek
Harness agent `exp-hostcheck-runner`, delegated by the lead). This file is the TASL-2 host-check record the
unit's `host_check` gate reads for `mlgym_metamaze`; the lead commits it to published `main` and fills the note's
gate as `host check <record> sha256 <its sha256>` (written uncommitted on the ops worktree
`ops-g1b-expansion-hostcheck-20261126`, baseline `a1597f70`; no push).

host_check_host: TASL-2
host_check_harness_commit: aa354485bff6b5746c48ddadcb50d92e9c6f3645
host_check_items: 1-7 PASS
host_check_verdict: PASS

## What this binds

The seven host conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` section 3 — C1 unprivileged
user/mount/PID/network/cgroup namespaces, C2 Yama `ptrace_scope >= 1`, C3 a delegated cgroup v2 subtree with
`cgroup.kill` (8G / swap 0), C4 non-root and the interpreter `sys.path` hard check, C5 a real sandboxed smoke
with `effective: true`, C6 a GPU smoke with the sandbox on (full UUID, under the exclusive lease), C7 end
state — were re-checked on TASL-2 at this node's kit pin in one orchestrated session:
2026-11-26T10:06:49Z to 10:11:57Z UTC for the C1-C7 host work on the four pins; the two determinism checks follow as separate records. All seven passed with no waiver. Steps 1-4 of prep report section 9 (checkouts, pins,
environments, data) were checked in the same session. The supplementary `tests/trackg/test_trackg_isolation.py`
passed at the pin. CPUs 8-11 were not used by any step; every CPU-bound step ran under `taskset -c 0-3`
(the node's G.1b set).

This record covers the pin only. The node's fixed-seed CPU-set determinism check (R1-TASL2-CPU) is a
separate record (`docs/r1/reports/tasl_chain_20261122/TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7.md`). This is host evidence, not a launch
authorization; the author's note and the remaining gates are still required.

## Host facts (read-only, `host_facts.json`/`.txt`)

| fact | value |
|---|---|
| host | `TASL-2` (`ssh -o BatchMode=yes portal_zhixu`), Ubuntu 22.04.5 LTS, Linux 6.8.0-149-generic #149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Oct 28 20:58:45 UTC x86_64 |
| CPU | Intel Core i9-14900KF, 32 logical CPUs; `cpuinfo_max_freq` 5,800,000 kHz for CPUs 12-15 and 4-7, 4,400,000 kHz for the E-cores 16-31, 6,100,000 kHz for CPUs 8-11 (excluded) |
| microcode | 0x133 on all 32 CPUs |
| uid | 1008(dowling), unprivileged, no sudo; `CapEff` 0; `sudo -n` password required |
| cgroup | cgroup2fs, controllers `cpuset cpu io memory hugetlb pids rdma misc`, `nsdelegate` in the delegated scope |
| sysctls | `kernel.unprivileged_userns_clone=1`, `kernel.apparmor_restrict_unprivileged_userns=0`, `user.max_user_namespaces=254738`, `kernel.yama.ptrace_scope=1`, `kernel.dmesg_restrict=1` |
| GPU | NVIDIA GeForce RTX 4090, UUID GPU-4d623e76-7587-ee15-a633-46f60d220d94, driver 535.309.01; `nvidia-smi --query-compute-apps` empty before and after; 358 MiB desktop reservation, 0 % |
| GPU lease | `~/r1_locks/gpu0.lock` free before and after; only `flock` was used for C6, the lease log was not written |
| disk | 342.7 GiB free on / |
| Track P harness repository | `/home/dowling/r1_trackp/autoresearch_harness @ 897d83c8efa364ec2fdd37288241cc42e01d7274` — read-only `stat`/`git status` only (tracked tree clean), not touched |
| seven-node checkout | `/home/dowling/r1_tracks/t1_tasl/harness` at `c025f89aeafc2199bf3487b4bcaa16678273c702`, tracked-clean (its pre-existing untracked `data` links are from earlier runs; unchanged) |

## Steps 1-4 (prep report section 9)

| step | result | key evidence |
|---|---|---|
| 1. separate clone and the four worktrees | **PASS** | `git clone --no-checkout https://github.com/dowlingwong/autoresearch_harness.git /home/dowling/r1_tracks/t1_tasl_x/harness_repo` (not Track P's repository); `git fetch origin` for the four kit branches (GitHub `ls-remote` resolves each to its pin); four `git worktree add --detach` under `/home/dowling/r1_tracks/t1_tasl_x/harness_<node>`; `git rev-parse HEAD` = the pin, `git status --porcelain --untracked-files=all` empty, detached, `merge-base --is-ancestor c025f89a HEAD` rc 0 (`step1_checkouts.txt`, `step1_checks.txt`, `checkout_end.txt`) |
| 2. pins recomputed at the pin | **PASS** | with the node's environment interpreter: node spec `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9`, committed pin (without the data link) `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db`, edits manifest `6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2` — all equal to the spec; 19 frozen entries before the data link (`pins_mlgym_metamaze.json`/`.txt`) |
| 3. environments | **PASS** | torch312: `uv pip freeze` 77 lines, raw sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, Python 3.12.16, uv 0.13.6 — equals `sweep2/g1b/env/torch312.freeze.txt` (`env_torch312.json`/`.txt`). venv_jax: `python -m pip --disable-pip-version-check freeze` 56 lines, raw sha256 `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`, Python 3.12.16 — equals `sweep2/g1b/env/venv_jax.freeze.txt`; `readlink -f` of `bin/python`, `bin/python3`, `bin/python3.12` all `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`, target `python --version` 3.12.16, target sha256 `23bc148d2b48964b621c5561ff2b81c1d9c7b717967a7491efbf12f4304882b5`, 31,028,464 B; nothing in venv_jax was modified (`env_venv_jax.json`/`.txt`) |
| 4. data staged under the session data root | **PASS** | the node's own `setup_command` (`prepare_data.py --out $AR_TRACKG_DATA_ROOT/mlgym_metamaze`) with the node's environment first on `PATH`; data manifest `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000`, 9, every file re-hashed and matching, read-only (`datapins_mlgym_metamaze.json`/`.txt`) |

## C1-C7 at the pin — PASS table

| # | condition | result | key evidence |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces usable by the run uid | **PASS** | `unshare(CLONE_NEWUSER|CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWCGROUP)` rc 0 with the node interpreter (`venv_jax`) and `/usr/bin/python3` (3.10.12); uid 1008 mapped to 0; a real tmpfs mount + write rc 0; the child is PID 1 of the new PID namespace; all namespace inodes changed (`c1_userns_env.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope >= 1` (host-wide; run once and recorded here) | **PASS** | `kernel.yama.ptrace_scope=1`, `yama` in LSM `lockdown,capability,landlock,yama,apparmor`; parent→child attach ok; an unrelated same-uid sibling attach `EPERM` (`c2_ptrace.json`) |
| C3 | delegated cgroup v2 subtree with `cgroup.kill` (8G / swap 0) | **PASS** | `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`: scope `run-r0d00c09a631947d392760ab59c583154.scope`, `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` exists, `nsdelegate=True`, owner uid 1008; the unit's own `isolation.RunCgroup` create→join→`cgroup.kill`→empty→removed (`c3_cgroup.json`/`.txt`) |
| C4 | not root; the interpreter's `sys.path` holds no home dir, runs tree or ancestor | **PASS** | euid 1008 (non-root); the unit's `WorkingCopyRunner._sandbox_config` passes for `venv_jax` interpreter (3.12.16) and `/usr/bin/python3` (3.10.12): `broad_entries=[]`, `sandbox_config_ok=True`, `isolation.worker_sandbox_available=True` for both (`c4_interp.json`/`.txt`) |
| C5 | a real sandboxed CPU smoke whose record shows `effective: true`, empty waivers and exceptions | **PASS** | from this checkout, run in a delegated 8G/swap-0 scope pinned to CPUs 0-3 with the venv_jax interpreter: outcome ok, `isolation.effective=true`, `waivers={}`, `exceptions=[]`, `worker_sandbox` present, `log_intact=true`, `parent_dumpable_at_accept=false`, `euid=1008`, `ptrace_scope=1`, `nsdelegate=true`, run cgroup removed (`c5_smoke.json`; `records/metamaze_smoke/`) |
| C6 | GPU smoke with the sandbox on (full UUID, under the exclusive lease) | **PASS** | interpreter torch312 at this pin; GPU by full UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94`; the sandboxed worker (PID 1 of its namespaces) allocated and synchronised a CUDA tensor (`cuda_available=true`, `device_count=1`, tensor sum correct, metric written, no CUDA error), `effective=true`, `waivers={}`, `exceptions=[]`, cgroup removed; no compute app before or after (`c6_gpu_smoke.json`, `c6_gpu_lease_status.txt`, `gpu_compute_apps_pre_c6.txt`/`post_c6.txt`, `records/metamaze_gpu_smoke/`) |
| C7 | end state: GPU idle and unleased, no leftovers, disk, checkouts | **PASS** | GPU identical before/after (358 MiB, no compute apps, 0 %); lease `gpu0.lock` free; all six leftover buckets empty (run processes, sleeps, run/scope cgroups, tmp dirs, `/dev/shm`); `/` 342.7 GiB free; the node checkout still at the pin with only the setup `data` link untracked; the seven-node checkout still at `c025f89aeafc2199bf3487b4bcaa16678273c702`; Track P's harness repository only `stat`-ed and tracked-clean (`c7_final.json`/`.txt`) |

Supplementary, not a section-3 condition: the pin's own `tests/trackg/test_trackg_isolation.py` in a
delegated 8G/swap-0 scope with the venv_jax interpreter: **27 passed, 1 skipped** (the skip is the root-only
`test_unprivileged_end_to_end`; `pytest_isolation.json`, `logs/metamaze_pytest_isolation.log`).

## Capture evidence

- Run root on TASL-2: `/home/dowling/r1_engineering/t1_tasl_x_hostcheck_20261126` (`scripts/`, `captures/`, `logs/`, `records/`, `work/`).
- Capture set: `TASL2_ISOLATION_HOST_CHECK_X_mlgym_metamaze_20261126_captures/` — 47 files + `SHA256SUMS`; `SHA256SUMS` sha256 **`4f1cda113bb37e65e4583a8195423491452574ef64f2a86fab3d115ef0f0017c`**;
  `sha256sum -c` rc 0 on TASL-2 and `shasum -a 256 -c` rc 0 after fetch.
- The record's `host_check_harness_commit` line is the pin the checks ran at; the two determinism records
  for Titanic and Forest Cover are separate files with their own captures.

## Scope and non-authorities

Only TASL-2 was used (`ssh -o BatchMode=yes portal_zhixu`); TASL-7, HTCondor and deepthought were not
contacted. No CPUs 8-11 were used: every CPU-bound step was pinned with `taskset` to CPUs 0-3. The GPU
was used only for C6, under `flock ~/r1_locks/gpu0.lock`, and the lease log was not written; the card was
never shared and no foreign compute ran. Nothing was deleted, committed or pushed; Track P's harness
repository `/home/dowling/r1_trackp/autoresearch_harness` was read only once (`git rev-parse`/`git status`
and `stat`; head `897d83c8`, mtime 2026-10-25). This is host evidence, not a launch authorization.

**AI-assisted: DeepSeek Harness agent `exp-hostcheck-runner`, 26 Nov 2026. ENGINEERING_ONLY; uncommitted.**
