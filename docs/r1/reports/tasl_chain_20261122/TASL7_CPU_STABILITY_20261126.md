# TASL-7 CPU-set stability check — MetaMaze census baseline, six 4-CPU groups (26 November 2026)

**Verdict: all six 4-CPU groups PASS — 18/18 runs, `rc` 0, full 2,000,064-step baseline, byte-identical
`run.log` and result channels, `val_return` 7.710938, sealed `test_return` 7.4375.** On TASL-7 (AMD Ryzen 9
7900X 12C/24T, CPUs 0–23) the reviewed MetaMaze census baseline is deterministic and stable on **every** CPU
group tested — 0–3, 4–7, 8–11, 12–15, 16–19, 20–23 — three sequential repeats each: one `run.log` sha256
(`f3d6e3a844d0525e…`) and one result-channel sha256 (`b60323b4a4710f39…`) for all 18 runs, no signal, no
timeout, no leftover process, isolation enforced 18/18. This is the TASL-7 equivalent of the accepted TASL-2
check and gives the G.5 TASL-7 audits their host-local determinism evidence. Microcode is uniform
`0xa601203` on all 24 CPUs, `cpuinfo_max_freq` is identical (5,733,000 kHz) on all CPUs (no favoured-core
max-frequency asymmetry of the TASL-2 kind), and no kernel/MCE evidence was readable without privilege.
Cross-host note: the TASL-7 metric (7.710938 / sealed 7.4375) is **not** equal to the TASL-2 metric
(8.703125 / 8.703125); byte-identity is host-local across this host's CPU groups, not cross-host. This was a
read-only check: no BIOS/firmware/kernel/governor/sysctl change, no sudo, no deletion, no GPU lease or GPU
use, no G1b/G5/G4 job, no commit/push. ENGINEERING_ONLY — no census measurement beyond this stability check.

Prepared by a delegated agent (AI-assisted) for the lead; independent review is pending (section 11).

## 0. One-line result

| item | value |
|---|---|
| host | TASL-7 (`ssh -o BatchMode=yes tasl7`), **AMD Ryzen 9 7900X 12-Core (Zen 4)**, family 25 / model 97 / stepping 2, 12 cores / 24 logical CPUs 0–23, 2 CCDs, 64 MiB L3, 1 NUMA node |
| microcode | **`0xa601203` on all 24 CPUs** (`/proc/cpuinfo`, per CPU); uniform; not present in any installed `amd-ucode` blob (`amd64-microcode` 3.20191218.1ubuntu2.3, blobs 2019/2024) → the loaded revision comes from BIOS/UEFI; kernel 6.8.0-149-generic; Ubuntu 22.04.5 LTS |
| kit | `/home/dowling/r1_trackg_20261125/harness_metamaze` @ `aa354485bff6b5746c48ddadcb50d92e9c6f3645` (branch `mac-trackg-mountaincar-20261125`), copied from the accepted TASL-2 worktree |
| env / data | `venv_jax` freeze `630ed6e1…388f5fdd9` (jax/jaxlib 0.4.35, CPU; torch absent); data manifest `e2338195…e99c38000` (9 files re-hashed, read-only 0444/0555) |
| test | the reviewed census **baseline run only** (`s000_baseline`), full 2,000,000 steps, seeds 8001/8001, one run per (CPU group, repeat); **6 groups × 3 repeats = 18 runs, sequential** |
| window | `2026-11-26T07:07:52Z` → `2026-11-26T07:23:08Z` (18 runs, ~16 min); each run in its own delegated 8 GB / swap-0 scope; `CUDA_VISIBLE_DEVICES=""`; CPU-only |
| **CPUs 0–3** | **PASS 3/3** — 46.8–47.1 s, rc 0, `val_return` 7.710938, sealed 7.4375, byte-identical |
| **CPUs 4–7** | **PASS 3/3** — 56.0–56.8 s, rc 0, same values, byte-identical |
| **CPUs 8–11** | **PASS 3/3** — 43.0–43.1 s, rc 0, same values, byte-identical |
| **CPUs 12–15** | **PASS 3/3** — 47.5–47.7 s, rc 0, same values, byte-identical |
| **CPUs 16–19** | **PASS 3/3** — 55.6–56.8 s, rc 0, same values, byte-identical |
| **CPUs 20–23** | **PASS 3/3** — 42.9–43.0 s, rc 0, same values, byte-identical |
| determinism | **18/18 bitwise identical** (`run.log` sha256 `f3d6e3a844d0525e1d18643d87467cff942d21911c7941d20ee9e2b0a7fee720`, 26,561 B; result channel sha256 `b60323b4a4710f396cc8464c03227471b2eca835357765d33c8c28ba2852427d`, 59 B); single `val_return` 7.710938 / sealed 7.4375; steps 2,000,064 on all 18 |
| cross-host | TASL-7 metric **differs** from the accepted TASL-2 metric (TASL-2: `val_return` 8.703125, sealed 8.703125, `run.log` `8d85dad1…`); byte-identity here is **host-local** |
| captures | `docs/r1/reports/tasl_chain_20261122/captures/tasl7_cpu_stability_20261126/` — 282 files (281 listed + `SHA256SUMS`), `SHA256SUMS` sha256 **`0dcfdea70de3e0923eaeb60c33ecacc555da051d5d342821f2ed7b50718e10cd`**; remote `sha256sum -c` rc 0 and local `shasum -a 256 -c` rc 0 |

## 1. Authorisation, scope and what this is

The lead authorised a **read-only CPU-set stability check on TASL-7**, equivalent to the accepted TASL-2 one
(`TASL2_CPU_STABILITY_20261125.md`), so that the **G.5 TASL-7 audits have evidence**: work TASL-7 only, the
reviewed MetaMaze kit and the exact census command path, no system change (no BIOS/firmware/kernel/governor/
sysctl), no `sudo`, no deletion, no G1b/G5/G4 jobs, no GPU lease. The check is **CPU-only**. The determinism
stress is: the reviewed MetaMaze **baseline command** (the same census command, one baseline run at the full
2,000,000 steps) pinned in turn to **each 4-CPU group** — 0–3, 4–7, 8–11, 12–15, 16–19 and 20–23 — **three
repeats per group, sequential**, no other smoke, delegated 8 GB scope, `CUDA_VISIBLE_DEVICES=""`, `PATH` with
the pinned env first and the absolute interpreter.

The kit, the `venv_jax` environment and the 68 KB data set were **copied from the accepted TASL-2 worktree**
to TASL-7 under the same paths (section 2), so the run binding is the accepted one; TASL-2 itself was opened
read-only (tar stream) and is unaltered (section 8). No GPU work, no GPU lease, no desktop job, no other
smoke was run.

This record is **not** a census measurement of TASL-7: it is 18 baseline runs of the reviewed census command,
no edits, no B1↔B2 campaign, no census claim beyond the stability evidence.

## 2. Copy and setup verification (new for TASL-7)

TASL-7 initially had no `/home/dowling/r1_trackg_20261125/` at all. The exact kit, env and data were copied
from TASL-2 through the Mac ops host as a `tar` stream (`ssh portal_zhixu 'tar -C … -cf -' | ssh tasl7 'tar
-C … -xpf -'`), preserving modes and symlinks; nothing was written on TASL-2 and nothing else was installed
system-wide. Transfer window `2026-11-26T06:52:19Z` → `07:06:55Z` (kit + data 110 s, `venv_jax` 918 MB
761.6 s). TASL-7 already had the identical uv-managed CPython **3.12.16** at the same absolute path
(`/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`), so the copied venv
resolves unchanged.

| item | verification result |
|---|---|
| kit | `harness_metamaze` 14 MB at the same path; `git rev-parse HEAD` = **`aa354485bff6b5746c48ddadcb50d92e9c6f3645`**; branch = **`mac-trackg-mountaincar-20261125`**; `git status --porcelain` = only `?? third_party/mlgym/nodes/mlgym_metamaze/data` (the setup data symlink); base commit `c025f89…` is an ancestor |
| env | `venv_jax` 918 MB; interpreter `3.12.16`, realpath `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`; `pip freeze` **56 packages**, sha256 = **`630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`** (matches TASL-2 exactly); jax 0.4.35 / jaxlib 0.4.35 / flax 0.10.2 / optax 0.2.4 / gymnax 0.0.9 / numpy 2.5.4; `torch` **not importable** |
| data | 68 KB at `/home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze`, manifest sha256 **`e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000`**; all **9 files re-hashed and matching** (`__init__.py`, `config.yaml`, `evaluate.py`, `helpers.py`, `networks.py`, `policy.py`, `requirements.txt`, `rlMetaMaze.yaml`, `train.py`); directory mode `0555`, files `0444` (no write bit); symlinked into the kit's node dir, outside the repository |
| pins | `node_spec` raw `d46dee59…cb3c59`, committed pin `759d6bf0…7d03db` / deployed pin `1eaaeac3…bf9ecb7`, edits manifest `6de5741f…66f0b2`, `ar_isolated.py` `37d99ab0…e48b610` (node and master copies equal), run budget `steps 2000000` — all equal to the accepted TASL-2 values (asserted by the driver on every one of the 18 runs) |
| interpreter binding | `PATH` = `…/venv_jax/bin:$PATH`, `VIRTUAL_ENV=…/venv_jax`; `python3` on PATH resolves to the absolute pinned interpreter (asserted per run) |
| data read-only / outside repo | `data_root` resolves outside the kit and every file has no write bit; re-hashed per run (asserted) |

**Validation only (not a census run, excluded from the 18):** one reduced-budget (2,048-step) run on CPUs 0–3 at
`2026-11-26T07:07:36Z` (8.577 s, rc 0, outcome `ok`, `val_return` 4.21875, sealed 3.429688, step counter
2,112) exercised the driver code path once before spending the 18 real runs. Its `check_baseline_log` is
expectedly empty at that budget (no loss lines), recorded as `VALIDATION_CRASH_OR_FAIL`; it is under
`validation/` in the captures and is not part of the stress.

## 3. Host facts (read-only)

| fact | value | source |
|---|---|---|
| CPU | **AMD Ryzen 9 7900X 12-Core Processor (Zen 4)**; family 25, model 97, stepping 2; 12 cores / 24 logical CPUs (CPUs 0–23), SMT2, 2 CCDs (core ids 0–5 and 8–13), L3 64 MiB in 2 instances, 1 NUMA node | `/proc/cpuinfo`, `lscpu`, `lscpu -e`, `topology/core_id`, `thread_siblings_list` |
| **microcode** | **`0xa601203` on every one of the 24 CPUs** (`/proc/cpuinfo` → 24 × `0xa601203`, unique-value count 1; before and after the check) | `/proc/cpuinfo` |
| microcode provenance | `amd64-microcode` **3.20191218.1ubuntu2.3**; blobs in `/lib/firmware/amd-ucode/` (2019/2024 dates; fam19h `2ffd1f89…`); **none of the installed blobs contains the loaded patch id `0xa601203`** (byte-scan), so the loaded revision is supplied by **BIOS/UEFI** early load, not by the distro package. Which firmware image, and whether `0xa601203` is the newest for this silicon, is **not established read-only** | `/lib/firmware/amd-ucode`, `dpkg -l` |
| kernel | Linux **6.8.0-149-generic** `#149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Oct 28 20:58:45 UTC` x86_64; **Ubuntu 22.04.5 LTS** | `uname -a`, `/etc/os-release` |
| kernel cmdline | `BOOT_IMAGE=/boot/vmlinuz-6.8.0-149-generic root=UUID=2d5df1f8-… ro quiet splash vt.handoff=7` (no `mce=`, no `idle=` overrides) | `/proc/cmdline` |
| boot / uptime | booted **2026-11-17 14:53** (`who -b`); 8 d 8 h 14 m at the pre-check; **no reboot during the check** (same boot before and after) | `who -b`, `last -x reboot`, `uptime` |
| BIOS/DMI | Alienware **Aurora R15 AMD**, board `0KDR38`, **BIOS 1.10.1 dated 2023-12-21** | `/sys/class/dmi/id/*` |
| cpufreq / power | **`amd-pstate-epp` active**, governor **`powersave`**, EPP **`balance_performance`** on all CPUs; `amd_pstate` status `active`, `prefcore=enabled`; **`cpuinfo_max_freq` identical on all 24 CPUs: 5,733,000 kHz (5,733 MHz)** — no favoured-core max-frequency asymmetry; no `boost` control file exposed with this driver | `/sys/devices/system/cpu/cpu*/cpufreq/*`, `/sys/devices/system/cpu/amd_pstate/*` |
| group topology | each of the six groups is **4 CPUs = 4 distinct physical cores, one thread each**: `0-3` = cores 0–3 (CCD0), `4-7` = cores 4,5 (CCD0) + 8,9 (CCD1), `8-11` = cores 10–13 (CCD1); `12-15`, `16-19`, `20-23` are the **SMT siblings** of those same cores (`0-3↔12-15`, `4-7↔16-19`, `8-11↔20-23`) | `lscpu -e`, `topology/core_id`, `thread_siblings_list` |
| load / other activity | pre-check load average **1.34/1.24/1.52**, **no other kit or smoke process** (our user and any user matching the kit/smoke patterns: NONE); the host is shared — another user's GPU training job (`jiachenl`, PID 1648890) was reported by `nvidia-smi` at the launcher start and at the post-check (**RTX 4090, 5,126 MiB / 100 %**; 44 MiB / 0 % at the pre-stress instant, 2,210 MiB / 2 % about 16 min earlier) and at a few percent of CPU; load during the runs 2.6–3.9 (mostly this check's own 4 pinned CPUs) | `uptime`, `ps`, `nvidia-smi` |
| memory / swap | 62 GiB RAM; host swap 2 GiB; **each run's scope enforces `memory.max` 8,589,934,592 B and `memory.swap.max` 0`**; run peak 760–774 MiB, swap 0 | scope cgroups, `free` |
| ECC / machine checks | no `edac/mc` instance (no ECC reported); `machinecheck` sysfs has 24 instances, `check_interval` 300 s; AMD exposes no `thermal_throttle` counters and `sensors` is not installed — recorded, not interpreted | `/sys/devices/system/{edac,machinecheck}` |
| systemd / cgroup | systemd user session (`user@1011.service`), unified cgroup v2; `systemd-run --user --scope` with `Delegate=yes` works (probe scope reported `memory.max` 8,589,934,592, `memory.swap.max` 0) | `systemctl --user`, scope probe |

## 4. Read-only kernel and hardware event log search (dmesg/journal) — **not readable**

No kernel-ring, system-journal or syslog record could be read without `sudo`, so the MCE / invalid-opcode /
segfault search requested for the window **could not be performed from this account**; the attempt and the
reason are recorded rather than the result claimed:

| probe | result |
|---|---|
| `id`, capabilities | uid 1011 (dowling), groups only `dowling`; `CapEff: 0000000000000000`; `sudo -n` → password required |
| `dmesg` | `dmesg: read kernel buffer failed: Operation not permitted`; `/proc/sys/kernel/dmesg_restrict` = **1** |
| `/dev/kmsg`, `/proc/kmsg` | group-readable device but `/proc/kmsg` root-only; no kernel log readable |
| `journalctl -k --since 2026-11-20` | prints the permission hint (“Users in groups 'adm', 'systemd-journal' can see all messages”) and `-- No entries --`; only the user journal is visible |
| `/var/log/syslog`, `/var/log/kern.log`, `/var/log/dmesg` | `syslog:adm` / `root:adm` `0640` — read denied (`head` → permission denied) |
| `/sys/fs/pstore/` | `Permission denied` (no readable firmware crash dump) |
| EDAC / MCE counters | no `edac/mc` instance; machinecheck sysfs exposes only `check_interval`; `coredumpctl`/`rasdaemon`/`mcelog` not installed; `/var/crash` empty |

Term search over the only visible (per-user) journal since 2026-11-20: `mce`, `Machine check`, `Machine Check`,
`trap invalid opcode`, `invalid opcode`, `general protection`, `segfault`, `SIGSEGV`, `SIGILL`, `Hardware
Error`, `MCE`, `microcode` → **0 matches each** (the visible journal holds only session-manager messages, no
kernel log, so this is not evidence of absence). Consequence: no kernel-side MCE/trap record is claimed; the
stability evidence is the 18 run records.

## 5. Method — the reviewed baseline run, 6 groups × 3 repeats

**Command path (unchanged from the accepted census command):** `tests/trackg/port_smoke_gpu.main()` →
`port_support.run_smoke()` → `smoke.run_smoke_campaign()`. The driver calls the kit's **own
`run_smoke_campaign()` with an empty proposal list**, which runs exactly its first step — `s000_baseline` at
the full 2,000,000-step budget, seeds 8001/8001, real pinned data, the node's isolation and limits — and
nothing else; the reviewed `check_baseline_log()` is then applied to the run's log and result channel. No
repository file is changed (imports only; the kit's frozen pin, node spec, data and env are re-verified per
run).

**Per run (each in its own delegated scope, sequential):**

```
systemd-run --user --scope --unit=tasl7-baseline-<group>_r<n>-<utc> --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=…/harness_metamaze/src \
    PATH=…/venv_jax/bin:$PATH VIRTUAL_ENV=…/venv_jax HOME=/home/dowling \
  taskset -c <group> …/venv_jax/bin/python run_baseline_stability.py \
    --group <group> --repeat <n> --runs-root <evidence>/runs/g<group>_r<n> --out <evidence>/results/g<group>_r<n>.json
```

Driver sha256 `c2ed5af60a8e205d394699945d84fefda6b4fe096813fe4a9e5b9240e2e481cf`; launcher sha256
`5444865648a3cfe58c3b50713de074846c93e39dd66ddbac11f9567c75b313c8` (full list in section 9).

**Per-run binding checks (asserted before every run; all passed on all 18):** git HEAD `aa354485…` on
`mac-trackg-mountaincar-20261125`, worktree clean apart from the setup data link; the committed/deployed
frozen pins, node spec, spec raw, edits manifest and `ar_isolated.py` as accepted; data manifest `e2338195…`
with all 9 files re-hashed and read-only outside the repo; `venv_jax` freeze `630ed6e1…` (jax 0.4.35 /
jaxlib 0.4.35, torch absent); affinity == the group; scope `memory.max` = 8,589,934,592 B and `memory.swap.max`
= 0; `ptrace_scope` = 1; `CUDA_VISIBLE_DEVICES=""`; `python3` on PATH resolves to the absolute pinned
interpreter. The driver sets `AR_TEST_CGROUP_PARENT` to its own scope; enabling the `memory` controller in the
scope's `cgroup.subtree_control` failed `EBUSY` exactly as in the accepted TASL-2 runs (recorded, not a
waiver — the scope `memory.peak` is the resource number). Per-run records: `binding`, process/exit/signal/
wall, log and channel sha256, metric, isolation, scope memory peak (`results/g<group>_r<n>.json`).

## 6. Results

Each row: wall time of the whole isolated run, parent exit code, parent signal, outcome, `val_return`, sealed
`test_return`, `run.log` sha256 (short), log bytes, result-channel sha256 (short), channel bytes, max
`AR_STEPS`, scope `memory.peak`, reviewed baseline-log check.

| group | rep | utc start–end | wall s | rc | sig | outcome | val_return | sealed | log sha256 | log B | channel sha256 | ch B | steps | peak MiB | check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-3 | 1 | 07:07:52–07:08:39 | 46.898 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 772.5 | PASS |
| 0-3 | 2 | 07:08:41–07:09:28 | 46.821 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 762.6 | PASS |
| 0-3 | 3 | 07:09:30–07:10:17 | 47.097 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 766.8 | PASS |
| 4-7 | 1 | 07:10:19–07:11:15 | 55.974 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 765.0 | PASS |
| 4-7 | 2 | 07:11:17–07:12:14 | 56.627 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 764.4 | PASS |
| 4-7 | 3 | 07:12:16–07:13:13 | 56.802 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 773.7 | PASS |
| 8-11 | 1 | 07:13:15–07:13:58 | 43.100 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 767.1 | PASS |
| 8-11 | 2 | 07:14:00–07:14:43 | 43.020 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 766.9 | PASS |
| 8-11 | 3 | 07:14:45–07:15:28 | 43.000 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 769.8 | PASS |
| 12-15 | 1 | 07:15:31–07:16:18 | 47.547 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 762.7 | PASS |
| 12-15 | 2 | 07:16:20–07:17:08 | 47.562 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 761.3 | PASS |
| 12-15 | 3 | 07:17:10–07:17:58 | 47.665 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 762.5 | PASS |
| 16-19 | 1 | 07:18:00–07:18:56 | 56.801 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 770.8 | PASS |
| 16-19 | 2 | 07:18:59–07:19:55 | 56.487 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 762.9 | PASS |
| 16-19 | 3 | 07:19:57–07:20:53 | 55.553 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 764.0 | PASS |
| 20-23 | 1 | 07:20:55–07:21:38 | 42.861 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 768.4 | PASS |
| 20-23 | 2 | 07:21:40–07:22:23 | 42.909 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 760.2 | PASS |
| 20-23 | 3 | 07:22:25–07:23:08 | 43.036 | 0 | – | ok | 7.710938 | 7.4375 | `f3d6e3a844d0…` | 26561 | `b60323b4a471…` | 59 | 2000064 | 764.3 | PASS |

Full hashes: `run.log` = `f3d6e3a844d0525e1d18643d87467cff942d21911c7941d20ee9e2b0a7fee720` (26,561 B);
result channel = `b60323b4a4710f396cc8464c03227471b2eca835357765d33c8c28ba2852427d` (59 B; content `AR_METRIC
val_return=7.710938` / `AR_TEST test_return=7.437500`).

### Per-group summary: CPU-to-physical-core mapping, wall time and peak memory

| group | CPUs mapped to physical cores | wall s (3 repeats) | peak MiB | verdict |
|---|---|---|---|---|
| 0-3 | cores 0,1,2,3 (CCD0), one thread each | 46.821–47.097 | 762.6–772.5 | PASS 3/3 |
| 4-7 | cores 4,5 (CCD0) + 8,9 (CCD1), one thread each | 55.974–56.802 | 764.4–773.7 | PASS 3/3 |
| 8-11 | cores 10,11,12,13 (CCD1), one thread each | 43.000–43.100 | 766.9–769.8 | PASS 3/3 |
| 12-15 | SMT siblings of 0-3 (cores 0,1,2,3) | 47.547–47.665 | 761.3–762.7 | PASS 3/3 |
| 16-19 | SMT siblings of 4-7 (cores 4,5,8,9) | 55.553–56.801 | 762.9–770.8 | PASS 3/3 |
| 20-23 | SMT siblings of 8-11 (cores 10,11,12,13) | 42.861–43.036 | 760.2–768.4 | PASS 3/3 |

### Determinism comparison

- **18/18 runs are bitwise identical** in both result channels and both logs — one `run.log` hash, one channel
  hash, one metric `val_return` 7.710938, one sealed `test_return` 7.4375 — across **all six CPU groups** and all
  three repeats each. This includes the SMT-sibling groups (12–15, 16–19, 20–23) matching their primary-thread
  groups (0–3, 4–7, 8–11) exactly, and the two groups that have no TASL-2 counterpart (16–19 and 20–23).
- Every run: `outcome.kind` `ok`, parent `returncode` 0, **no signal**, no timeout, no kill, no leftover
  process; `isolation.effective` true, waivers `{}`, exceptions `[]`, frozen files checked **19**, changed
  `[]`; steps **2,000,064** = the expected `(budget // envs + 1) × envs` with 64 envs; peak memory 760.2–773.7
  MiB of the 8,589,934,592 B cap and **swap 0**; reviewed `check_baseline_log()` PASS on all 18.
- No failure signature exists to compare: every run reached the full budget and emitted exactly one metric line
  and one sealed-test line in the result channel and none in the log; the driver's `baseline_check` is `ok` for
  all 18.
- **Wall time is the only group-dependent variable** (42.9–56.8 s; ~16 min for all 18 sequential runs). Groups
  reproduce their sibling's wall time closely (`0-3` 46.8–47.1 vs `12-15` 47.5–47.7; `4-7` 56.0–56.8 vs `16-19`
  55.6–56.8; `8-11` 43.0–43.1 vs `20-23` 42.9–43.0), consistent with per-physical-core speed/placement
  differences and the shared host (another user's GPU training job was active; load 2.6–3.9) rather than with
  SMT contention — and it had **no effect on the outputs**, which are identical.
- **Cross-host comparison with TASL-2 (read-only, for information):** the accepted TASL-2 runs gave
  `val_return` 8.703125 and sealed 8.703125 with `run.log` `8d85dad1…` / channel `9b08312…`; TASL-7 gives
  7.710938 and 7.4375 with different hashes. The kit, env (identical freeze), data and command are the same, so
  the difference is host/CPU-dependent numerics (the two hosts are different microarchitectures — Zen 4
  including AVX-512 vs Raptor Lake without it — and the 2M-step RL baseline is chaotically sensitive to
  floating-point rounding), **not** a determinism failure on either host. It means byte-identity evidence is
  **host-local**: do not compare a TASL-7 metric to the TASL-2 metric as if it should be equal. The
  cross-host cause is not investigated here (no claim beyond the observation).

## 7. Conclusion

1. **All six TASL-7 4-CPU groups are stable on the reviewed MetaMaze baseline** — 18/18 PASS, full
   2,000,064 steps, bitwise identical outputs across every repeat and group, `val_return` 7.710938 / sealed
   7.4375, no crash, no signal, no timeout, no memory pressure (peak 760–774 MiB of an 8 GiB cap, swap 0).
   There is **no TASL-7 analogue of the TASL-2 CPUs 8–11 failure**: no group failed and no group's outputs
   differed.
2. **The run binding is the accepted one.** The kit (HEAD `aa354485…`, branch, clean worktree except the data
   link), the environment (freeze `630ed6e1…`, jax 0.4.35 CPU, torch absent), the data (manifest `e2338195…`,
   9 files re-hashed, read-only) and all committed/deployed pins were re-verified inside every run scope.
3. **Host-side facts:** microcode `0xa601203` uniform on all 24 CPUs (loaded from BIOS/UEFI — the installed
   `amd64-microcode` package does not contain it; not fixable/upgradeable read-only); `amd-pstate-epp` with
   `powersave` governor and `balance_performance` EPP; **identical `cpuinfo_max_freq` (5,733 MHz) on all CPUs**,
   so there is no favoured-core max-frequency split on this host of the kind that localised the TASL-2 failure.
   This is a statement about the observed frequencies/microcode, **not** a hardware-health verdict.
4. **G.5 TASL-7 audit evidence:** the reviewed census baseline is deterministic on TASL-7 and reproduces
   bit-for-bit on all six 4-CPU groups and on both SMT threads of every physical core; any of the six groups is
   therefore a valid reference group for TASL-7 audit runs, and this 18-run record is the host-local reference
   to compare future TASL-7 audits against. A future TASL-7 audit that does not reproduce these hashes would be
   a real divergence worth investigating.
5. **Cross-host caveat:** do not use the TASL-2 metric/hashes as the TASL-7 reference (they differ by host, as
   observed above); compare TASL-7 runs to this record.

## 8. No-change attestation

- No BIOS/firmware/kernel/governor/sysctl change, no `sudo` (password required), **no deletion of any
  pre-existing file or evidence** (the only removals were the capture collector's own transient `captures/`
  staging directory when the set was regenerated), no GPU lease and no GPU use (`CUDA_VISIBLE_DEVICES=""` on
  every run; the RTX 4090 was busy with **another user's** job, PID 1648890 user `jiachenl`, 5,126 MiB / 100 %
  at launcher start and at the post-check; `/home/dowling/r1_locks/gpu0.lock` is 0 B dated 21 Nov, untouched),
  no G1b/G5/G4 job, no commit/push.
- Post-check (`logs/postcheck.txt`): **no leftover kit processes**, **no leftover `tasl7-baseline` scopes**; kit
  worktree HEAD `aa354485…` / branch / status (`?? …/data` only) identical to before, **no file under the kit
  newer than the check start**; microcode still `0xa601203` ×24; governor/EPP unchanged; no reboot during;
  `r1_locks` unchanged.
- TASL-2 was **not altered**: only read-only `tar` reads; its worktree is still HEAD `aa354485…` with only the
  data symlink untracked, and no file under `tasl2_cpu_stability_20261125` is newer than the check window.
- New files created: the TASL-7 evidence root
  `/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126/` (39 MB: runs, results, logs,
  host, validation) and this record plus its captures in the Mac ops worktree (3.3 MB, 282 files).

## 9. Evidence paths and SHAs

| item | path / sha256 |
|---|---|
| remote evidence root (preserved) | `/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126` |
| ops-worktree captures (282 files = 281 + `SHA256SUMS`) | `docs/r1/reports/tasl_chain_20261122/captures/tasl7_cpu_stability_20261126/` |
| captures `SHA256SUMS` sha256 | **`0dcfdea70de3e0923eaeb60c33ecacc555da051d5d342821f2ed7b50718e10cd`** (`sha256sum -c` rc 0 remote; `shasum -a 256 -c` rc 0 local) |
| driver / launcher | `scripts/run_baseline_stability.py` sha256 `c2ed5af60a8e205d394699945d84fefda6b4fe096813fe4a9e5b9240e2e481cf`; `scripts/launch_stress.sh` sha256 `5444865648a3cfe58c3b50713de074846c93e39dd66ddbac11f9567c75b313c8` |
| host/capture/verify scripts | `scripts/host_capture_tasl7.sh` `2ebd8229…f5e4f5aef7`; `scripts/verify_setup.sh` `9d617471…28c302caa98`; `scripts/precheck_tasl7.sh` `8f00ea43…131f5fb49b3654`; `scripts/postcheck_tasl7.sh` `7df04320…42a91a1f4f1d7c`; `scripts/collect_captures.sh` `40a4e0bb…4505f392e5535944` |
| per-run results | `results/g<group>_r<n>.json` (18) — full binding, process/exit/signal, hashes, log tail, isolation, scope memory peak |
| per-run records and outputs | `runs/<group>_r<n>/run_record.json`, `run.log`, `result_channel.txt`, `determinism_shim.json` (18 each) |
| ledger / launcher log | `logs/ledger.tsv`, `logs/launch_console.log`, `logs/<group>_r<n>.console.txt` / `.stderr.txt`, `logs/precheck.txt`, `logs/postcheck.txt`, `logs/preverify.txt` |
| summary | `summary.txt`, `summary.json` (`tasl7_cpu_stability_summary/v1`) |
| host facts | `host/cpuinfo.txt`, `host/lscpu.txt`, `host/lscpu.json`, `host/admin_extra.txt`, `host/admin_amd_extra.txt`, `host/admin_microcode_probe.txt`, `host/admin_readonly_probe.txt`, `host/kernel_log_search_readonly.txt` |
| validation-only run | `validation/validation.json` sha256 `78c610a1ccf05787d70b46ba944348592832243bdae28740ef85109522e5d2fe` (+ `validation/runs_validation/`) |
| launch commands/authorisation | `commands.txt` |

## 10. Limits of this check

- One baseline run per repeat, three repeats per group; no edits, no B1↔B2, no census measurement. Three
  passing runs per group are not a proof of long-run stability; they are the same stress that separated the
  TASL-2 groups, and here every group passed with bitwise-identical output.
- The check is **CPU-only** and does not test the GPU, the node's isolation beyond the reviewed baseline step,
  or any edit; it ran on a shared host with another user's GPU job active (recorded; outputs unaffected).
- Microcode is uniform and the loaded revision is BIOS-supplied, but **whether it is the newest available for
  this silicon, and the exact firmware image/patch set, could not be verified read-only**; no MCE/dmesg/journal
  record is obtainable from this account (section 4), so no hardware-side fault attribution is claimed.
- The cross-host metric difference (TASL-7 vs TASL-2) is reported as observed; its numerical cause is not
  investigated here.
- Independent review is pending (lead). No commit/push was made.

## 11. Independent review and points for the lead (not acted on here)

Review status: **pending** — this record is prepared for the lead's independent review.

Points for the lead (not acted on here):

1. **Evidence for G.5 TASL-7 audits is in place:** the reviewed baseline is bitwise deterministic on all six
   4-CPU groups of TASL-7 (`f3d6e3a8…`, `b60323b4…`, 7.710938 / 7.4375). Use these as the TASL-7 host-local
   reference; any of the six groups is a valid audit group.
2. **Do not compare TASL-7 metrics/hashes to TASL-2's** — they differ by host microarchitecture (7.710938 vs
   8.703125); treat cross-host metric equality as not expected, and compare audits within TASL-7.
3. **Optional follow-up (needs the lead / privilege), not part of this check:** whether the BIOS-supplied
   microcode `0xa601203` is the newest for this Ryzen 9 7900X, and a read-only admin check of dmesg/MCE since
   the boot for any hardware errors while the baseline runs; neither is needed for the stability verdict
   above, which rests on the 18 identical runs.
