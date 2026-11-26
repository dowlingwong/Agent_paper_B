# TASL-2 CPU stability check — MetaMaze census baseline, Raptor Lake hypothesis (26 November 2026)

**Verdict: CPUs 0–3, 4–7 and 12–15 PASS (9/9 runs, bitwise identical, `val_return` 8.703125); CPUs 8–11 are
unstable — 3/3 runs fail with the sandboxed JAX worker killed by a native signal 3.9–5.3 s into training (empty
result channel). The failure is reproducibly localised to the two 6.1 GHz favoured P-cores (physical cores 4 and
5, `Cpus_allowed_list` 8–11) — the only P-cores on this host with `cpuinfo_max_freq` 6100 MHz — while the same
kit, environment, data and command pass identically on the other three P-core pairs. Microcode is uniform
`0x133` (Intel 2025-10-08) on all 32 CPUs and is the newest available, so the Raptor Lake microcode
mitigations are present; the crash still localises to the highest-boost cores, which is consistent with
(Vmin-shift-type) degradation of those two cores rather than with a missing microcode fix. This was a
read-only check: no BIOS/firmware/kernel/governor/sysctl change, no sudo, no deletion, no GPU lease, no
commit/push. ENGINEERING_ONLY — no census measurement beyond this stability check.**

Prepared by a delegated agent (AI-assisted) for the lead; independent review is pending (section 10).

## 0. One-line result

| item | value |
|---|---|
| host | TASL-2 (`ssh -o BatchMode=yes portal_zhixu`), Intel Core i9-14900KF, model 183 / stepping 1 (Raptor Lake-S), 32 logical CPUs |
| microcode | **`0x133` on all 32 CPUs** (`/proc/cpuinfo`, per CPU); `intel-microcode` 3.20260210.0ubuntu0.22.04.1; kernel 6.8.0-149-generic, Ubuntu 22.04.5 |
| kit | `/home/dowling/r1_trackg_20261125/harness_metamaze` @ `aa354485bff6b5746c48ddadcb50d92e9c6f3645` (branch `mac-trackg-mountaincar-20261125`) |
| env / data | `venv_jax` freeze `630ed6e1…` (jax 0.4.35, CPU); data manifest `e2338195…` (9 files re-hashed, read-only) |
| test | the reviewed census **baseline run only** (`s000_baseline`), full 2,000,000 steps, seeds 8001/8001, one run per (CPU group, repeat), 4 groups × 3 repeats sequential |
| window | `2026-11-26T01:33:37Z` → `2026-11-26T01:42:18Z`; each run in its own delegated 8 GB / swap-0 scope; `CUDA_VISIBLE_DEVICES=""`; no GPU, no lease, GPU 353 MiB / 0 % before and after |
| **CPUs 0–3** | **PASS 3/3** — 53.5–53.7 s, rc 0, `val_return` 8.703125, sealed 8.703125, bitwise identical outputs |
| **CPUs 4–7** | **PASS 3/3** — 53.4–54.1 s, rc 0, same values, bitwise identical outputs |
| **CPUs 8–11** | **FAIL 3/3** — 3.9–5.3 s, rc 1 (`divergent`/`nonzero_exit`), **no metric**: sandboxed JAX worker killed by a native signal, empty result channel; identical 538-byte log all three runs |
| **CPUs 12–15** | **PASS 3/3** — 53.2–53.4 s, rc 0, same values, bitwise identical outputs |
| determinism | the 9 passing runs are **bitwise identical** (`run.log` sha256 `8d85dad1…07b8`; result channel sha256 `9b08312…eae14`; `val_return` = sealed test 8.703125) and equal the previously accepted CPUs 0–3 diagnostic baseline hashes exactly |
| captures | `docs/r1/reports/tasl_chain_20261122/captures/tasl2_cpu_stability_20261125/` — 104 files, `SHA256SUMS` sha256 **`1a2c80c87eb5b22f28a6585a86f425f891b5cb7c4d7fc879a500b0a2948832df`**; remote `sha256sum -c` rc 0 and local `shasum -a 256 -c` rc 0 |

## 1. Authorisation, scope and what this is

The lead authorised a **read-only CPU stability check** for the MetaMaze census crashes: work on TASL-2 only,
the reviewed MetaMaze kit and the exact census command path, no system change (no BIOS/firmware/kernel/
governor/sysctl), no `sudo`, no deletion, no G1b/G5/G4 jobs, no GPU lease. The determinism stress is: the
reviewed MetaMaze **baseline command** (the same census command, one baseline run at the full 2,000,000 steps)
pinned in turn to CPUs 0–3, 4–7, 8–11 and 12–15, **three repeats per group, sequential**, no other smoke,
delegated 8 GB scope, `CUDA_VISIBLE_DEVICES=""`, `PATH` with the pinned env first and the absolute interpreter.

Context from the prior attempts on this host (preserved, not touched): the same kit passed a checklist-E smoke
on CPUs 0–3 (`u2_census_smoke_20261125_DIAG_CPUS_0_3`, corrected verdict PASS), and STOPped twice on CPUs 8–11
(`u2_census_smoke_20261125`, SIGSEGV; `u2_census_smoke_20261125_RETRY`, SIGILL — both with the 2M-step baseline
trained and then the parent killed at evaluation, and the other runs' workers dying at 3.5–5.6 s). The question
here is whether the 8–11 instability is reproducible and whether it is localised to that core group.

This record is **not** a census measurement of the node: it is three 2M-step baselines per core group, no
edits, no B1↔B2 campaign, no census claim. No GPU was used and no GPU lease was taken.

## 2. Host facts (read-only)

| fact | value | source |
|---|---|---|
| CPU | Intel(R) Core(TM) i9-14900KF; family 6, **model 183 (0xB7), stepping 1**; 32 logical CPUs (8 P-cores with SMT = CPUs 0–15; 16 E-cores = CPUs 16–31); 24 cores, 36 MiB L3 | `/proc/cpuinfo`, `lscpu`, `lscpu -e` |
| **microcode** | **`0x133` on every one of the 32 CPUs** (`grep microcode /proc/cpuinfo` → 32 × `0x133`; unique-value count 1) | `/proc/cpuinfo` |
| microcode provenance | `intel-microcode` **3.20260210.0ubuntu0.22.04.1**; `/lib/firmware/intel-ucode/06-b7-01` sha256 `e73efa954b94a0c09a63b010ed8abf82d3e714fc55dfad708f7a8a4067fe97d2` (219,136 B) → header revision `0x133`, signature `0xb0671` (= this CPU), date field `0x10082025`; Debian changelog: `sig 0x000b0671 … 2025-10-08, rev 0x0133` | `/lib/firmware`, dpkg changelog |
| kernel | Linux 6.8.0-149-generic `#149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Oct 28 20:58:45 UTC` x86_64; Ubuntu 22.04.5 LTS | `uname -a`, `/etc/os-release` |
| kernel cmdline | `BOOT_IMAGE=/boot/vmlinuz-6.8.0-149-generic root=… ro quiet splash vt.handoff=7` (no `mce=`, no `idle=` overrides) | `/proc/cmdline` |
| boot / uptime | booted **2026-11-15 12:51** (`who -b`); 10 d 4 h 52 m at check end; **no reboot since** (all prior 8–11 crashes and this check are in the same boot) | `who -b`, `last -x reboot`, `uptime` |
| BIOS/DMI | Alienware Aurora R16, board 0RF96M, **BIOS 2.4.0 dated 2023-12-11** (OS-loaded microcode `0x133` is newer than the firmware) | `/sys/class/dmi/id/*` |
| cpufreq | `intel_pstate` active, governor `powersave`, `no_turbo=0`; `cpuinfo_max_freq` 5,800,000 kHz for cores 0–3, 6, 7 and **6,100,000 kHz for cores 4–5 (CPUs 8–11)** — the two favoured/preferred P-cores | `/sys/devices/system/cpu/cpufreq/*` |
| group topology | CPUs 0–3 = physical cores 0–1 (`core_id` 0, 4); 4–7 = cores 2–3 (`core_id` 8, 12); **8–11 = cores 4–5 (`core_id` 16, 20)**; 12–15 = cores 6–7 (`core_id` 24, 28); each group is two complete SMT pairs | `lscpu -e`, `topology/core_id`, `thread_siblings_list` |
| load / other activity | load average 0.20/0.20/0.21 at the pre-check (0.31/0.25/0.23 at launcher start), no other kit or smoke process, GPU 353 MiB / 0 %; idle check run before the stress | `uptime`, `ps`, `nvidia-smi` |
| package throttle counter (context only) | packages: `package_throttle_count` 19,843 (cpu0), 19,398 (cpu8/cpu12) since boot — a package-wide counter, not per-core; recorded, not interpreted | `/sys/devices/system/cpu/cpu*/thermal_throttle/*` |

Microcode `0x133` is the newest Raptor Lake microcode in the installed (February 2026) `intel-microcode`
package, i.e. it includes Intel's 0x12B-era Vmin-shift mitigation and later updates. It was already loaded
uniformly on all 32 CPUs for the whole 10-day boot, so the prior 8–11 crashes and this check ran under that
same microcode.

## 3. Read-only kernel and hardware event log search (dmesg/journal) — **not readable**

No kernel-ring, system-journal or syslog record could be read without `sudo`, so the MCE / invalid-opcode /
segfault search requested for 20 Nov onward **could not be performed from this account**; the attempt and the
reason are recorded rather than the result claimed:

| probe | result |
|---|---|
| `id`, capabilities | uid 1008 (dowling); groups only `dowling`; `CapEff: 0000000000000000`; `sudo -n` → password required |
| `dmesg` | `dmesg: read kernel buffer failed: Operation not permitted`; `/proc/sys/kernel/dmesg_restrict` = **1** |
| `/dev/kmsg`, `/proc/kmsg` | `Operation not permitted` / `Permission denied` |
| `journalctl -k --since 2026-11-20` | prints the permission hint (“Users in groups 'adm', 'systemd-journal' can see all messages”) and `-- No entries --`; only the user journal is visible |
| journal files | `/var/log/journal/*/system@*.journal` — `root:systemd-journal` `0640`, plus ACLs; not readable |
| `/var/log/syslog`, `/var/log/kern.log`, `/var/log/dmesg` | `syslog:adm` / `root:adm` `0640` — read denied (`head` → permission denied) |
| `/sys/fs/pstore/` | `Permission denied` (no readable firmware crash dump) |
| EDAC / MCE counters | `/sys/devices/system/edac/mc/` has no `mc*` instance (no ECC on this consumer board); machinecheck sysfs exposes only `check_interval` (300 s), not counters |
| coredumps | `coredumpctl` not installed; `ulimit -c` = 0; `/var/crash` empty; `/var/lib/systemd/coredump` root-only |

Term search over the only visible (per-user) journal since 2026-11-20: `mce`, `Machine check`, `Machine Check`,
`trap invalid opcode`, `invalid opcode`, `general protection`, `segfault`, `SIGSEGV`, `SIGILL`, `Hardware
Error`, `MCE`, `microcode` → **0 matches each** (the visible journal holds only session-manager messages, no
kernel log, so this is not evidence of absence). Consequence: any MCE/trap/segfault kernel record that may
exist for 20–26 Nov is **not obtainable read-only**; the crash evidence available is the run records (this
check and the preserved prior attempts).

## 4. Method — the reviewed baseline run, 4 groups × 3 repeats

**Command path (unchanged):** `tests/trackg/port_smoke_gpu.main()` → `port_support.run_smoke()` →
`smoke.run_smoke_campaign()`. The equivalent reviewed invocation for one group is
`PYTHONPATH=src python3 -m tests.trackg.port_smoke_gpu --node mlgym_metamaze --cpus <group> --memory-limit "<scope>" --runs-root <runs> --provisional-timeout 900`
(the baseline is its first run); the driver stops at that first step. The driver calls the kit's **own `run_smoke_campaign()` with an empty proposal
list**, which runs exactly its first step — `s000_baseline` at the full 2,000,000-step budget, seeds
8001/8001, real pinned data, the node's isolation and limits — and nothing else; the reviewed
`check_baseline_log()` is then applied to the run's log and result channel. No repository file is changed
(imports only; the kit's frozen pin, node spec, data and env are verified per run). This is the reviewed
census baseline step, not the full 9-run checklist-E smoke; the task asked for one baseline run per repeat.

**Per run (each in its own delegated scope, sequential):**

```
systemd-run --user --scope --unit=tasl2-baseline-<group>_r<n>-<utc> --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=…/harness_metamaze/src \
    PATH=…/venv_jax/bin:$PATH VIRTUAL_ENV=…/venv_jax \
  taskset -c <group> …/venv_jax/bin/python run_baseline_stability.py \
    --group <group> --repeat <n> --runs-root <evidence>/runs/g<group>_r<n> --out <evidence>/results/g<group>_r<n>.json
```

Driver sha256 `848fcb9f72f5c6d4b53f23754f7e4b5e10bb67f86233f7f12825243e4014258b`; launcher sha256
`01b74a1af43e0ced6d99c15161a9b7453ac8754f6b308d0dc65948158b421692`.

**Per-run binding checks (asserted before the run; all passed on every run):** git HEAD
`aa354485bff6b5746c48ddadcb50d92e9c6f3645` on `mac-trackg-mountaincar-20261125`, worktree clean apart from
the setup data link; the committed/deployed frozen pins (`759d6bf0…` / `1eaaeac3…`), node spec
(`d97bb182…`), spec raw (`d46dee59…`), edits manifest (`6de5741f…`), `ar_isolated.py` (`37d99ab0…`) all as
accepted; data manifest `e2338195…` with all 9 files re-hashed and read-only outside the repo; `venv_jax`
freeze `630ed6e1…` (jax 0.4.35 / jaxlib 0.4.35, torch absent); affinity == the group; scope `memory.max` =
8,589,934,592 B and `memory.swap.max` = 0; `ptrace_scope` = 1; `CUDA_VISIBLE_DEVICES=""`; `python3` on PATH
resolves to the absolute pinned interpreter. The only per-run deviation from the accepted launches is that
the driver sets `AR_TEST_CGROUP_PARENT` to its own scope (as the accepted runs did); enabling the `memory`
controller in the scope's `cgroup.subtree_control` failed `EBUSY` exactly as in the accepted runs (recorded,
not a waiver — the scope `memory.peak` is the resource number).

**Validation only (not a census run, excluded from the 3 repeats):** one reduced-budget (2,048-step) run on
CPUs 0–3 at `2026-11-26T01:32:59Z` (6.167 s, run-level `ok`, `val_return` 1.632812) exercised the driver code
path once before spending the 12 real runs; its `check_baseline_log` is expectedly empty at that budget (no
loss lines). Its result is included in the captures under `validation/`; it is not part of the stress.

## 5. Results

Each row: wall time of the whole isolated run, parent exit code, parent-signal, `elapsed_seconds_info_only`,
outcome, metric, `run.log` sha256 (short), log bytes, result-channel sha256 (short), channel bytes, max
`AR_STEPS`, scope `memory.peak`, reviewed baseline-log check.

| group | rep | utc start–end | wall s | rc | sig | outcome | val_return | sealed | log sha256 | log B | channel sha256 | ch B | steps | peak MiB | check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0–3 | 1 | 01:33:37–01:34:31 | 53.671 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 761.1 | PASS |
| 0–3 | 2 | 01:34:33–01:35:27 | 53.925 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 763.3 | PASS |
| 0–3 | 3 | 01:35:29–01:36:23 | 53.924 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 762.6 | PASS |
| 4–7 | 1 | 01:36:25–01:37:20 | 54.347 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 763.8 | PASS |
| 4–7 | 2 | 01:37:22–01:38:16 | 53.694 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 759.0 | PASS |
| 4–7 | 3 | 01:38:18–01:39:11 | 53.573 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 760.8 | PASS |
| **8–11** | 1 | 01:39:13–01:39:19 | **5.463** | **1** | – | **divergent/nonzero_exit** | – | – | `e11e7fc4…d1fe1` | **538** | `e3b0c442…` (empty) | **0** | – | 629.5 | **FAIL** |
| **8–11** | 2 | 01:39:21–01:39:26 | **4.618** | **1** | – | **divergent/nonzero_exit** | – | – | `e11e7fc4…d1fe1` | **538** | `e3b0c442…` (empty) | **0** | – | 555.2 | **FAIL** |
| **8–11** | 3 | 01:39:28–01:39:32 | **4.076** | **1** | – | **divergent/nonzero_exit** | – | – | `e11e7fc4…d1fe1` | **538** | `e3b0c442…` (empty) | **0** | – | 508.3 | **FAIL** |
| 12–15 | 1 | 01:39:34–01:40:27 | 53.413 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 760.4 | PASS |
| 12–15 | 2 | 01:40:29–01:41:23 | 53.456 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 760.7 | PASS |
| 12–15 | 3 | 01:41:25–01:42:18 | 53.427 | 0 | – | ok | 8.703125 | 8.703125 | `8d85dad1…07b8` | 26543 | `9b08312…eae14` | 59 | 2000064 | 762.3 | PASS |

Full hashes: passing `run.log` = `8d85dad1e13ab0f667e43c242bdf41aee19619043d4df0c6ab6a6bdb090207b8`; passing result
channel = `9b08312199b96cafcfb171663a2a2271d3d59427cc96bee96435195e084eae14` (content: `AR_METRIC
val_return=8.703125` / `AR_TEST test_return=8.703125`); failing `run.log` =
`e11e7fc4ecdf5724cb8033b836812ee7e65fa15e8ec7ae269fcf33faaf9d1fe1` (538 B); failing result channel =
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (sha256 of the empty file, 0 B).

### Determinism comparison

- **9/9 passing runs are bitwise identical** in both result channels and both logs, across all three passing
  groups and all repeats: one `run.log` hash, one channel hash, one metric `val_return` 8.703125 and one
  sealed `test_return` 8.703125. They are also **equal to the previously accepted CPUs 0–3 diagnostic
  baseline** (`run.log` `8d85dad1…`, channel `9b08312…`, 8.703125/8.703125), i.e. this stress reproduced the
  accepted result exactly, including on the two groups that had never run this baseline before.
- **3/3 failing runs are bitwise identical to each other** (same 538-byte log, same empty channel), so the
  8–11 failure is deterministic at the observed granularity (worker start → data verify → death), even though
  its wall time varies 3.9–5.3 s.
- Every passing record: `isolation.effective` true, waivers `{}`, exceptions `[]`, frozen files checked 19,
  changed `[]`, process not killed or timed out, steps 2,000,064 = the expected `(budget // envs + 1) × envs`,
  peak memory 508–764 MiB of the 8,589,934,592 B cap and swap 0. The failing records keep the same isolation
  facts except that no metric exists; their peak memory (508–630 MiB) is far below the cap, so the deaths are
  not memory-pressure kills.

### The CPUs 8–11 failure signature

The identical failing log is (all three runs):

```
AR_SEEDS train=8001 split=8001
AR_DATA manifest_sha256=e2338195… files=9
An NVIDIA GPU may be present on this machine, but a CUDA-enabled jaxlib is not installed. Falling back to cpu.
AR_DEVICE cpu cpu jax=0.4.35 workers=0
AR_DATA manifest_sha256=e2338195… files=9
AR_ERROR worker train: connection closed (worker exit 1)

AR_RUNNER result_channel_sha256=e3b0c442… bytes=0
```

The parent started the sandboxed worker, the worker verified the data and began training, then the worker's
connection closed. The parent's `call()` prints the worker process's exit status; `worker exit 1` here is the
**sandbox launcher's mapping of a signalled worker**, not a Python-level exit: `ar_isolated.py::_launch` ends
with `os._exit(os.waitstatus_to_exitcode(status) & 0xFF if os.WIFEXITED(status) else 1)` — a worker (PID 1 of
its namespace) killed by a signal makes the launcher exit 1, and the parent then reports exit 1. No worker
traceback appears in the run log (the worker's stdout/stderr are captured there), which is consistent with a
native signal rather than a Python exception. The exactly equal prior-attempt evidence shows the same class:
the failed 8–11 launches recorded SIGSEGV (attempt 1, parent return code −11) and SIGILL (retry, −4) at the
process level, and their early worker deaths carried the same `AR_ERROR worker train: connection closed
(worker exit 1)` message at 3.5–5.6 s. In this baseline-only stress the three failures all landed early in
the worker; the previously observed later failure (full 2M training, then a SIGSEGV/SIGILL during evaluation)
is the same native-crash class on the same core group.

## 6. Conclusion

1. **CPUs 8–11 are unstable and reproducible.** Three independent sequential runs of the reviewed MetaMaze
   baseline, same kit/env/data/pins, each in a fresh 8 GB scope pinned to `taskset -c 8-11`, all failed within
   3.9–5.3 s with the sandboxed JAX worker killed by a native signal (identical 538-byte log, empty result
   channel). Together with the two preserved prior 8–11 launches (attempt 1: SIGSEGV; clean retry: SIGILL) this is
   five independent failures of this kit on CPUs 8–11 and none on any other core group.
2. **CPUs 0–3, 4–7 and 12–15 are stable under the same command** (9/9 PASS, bitwise identical, metric
   8.703125, sealed 8.703125, full 2,000,064 steps, ~53–54 s). The failure is therefore **not** a kit-wide,
   env-wide, data-wide or argument-level defect, and not attributable to CPU contention: the runs were
   sequential, the host was idle at launch (load 0.31/0.25/0.23, no other kit process), and the failing group was tested
   in the middle of the passing groups.
3. **The instability is localised to the two physical P-cores 4 and 5 (CPUs 8–11)** — the *only* cores on this
   host with `cpuinfo_max_freq` 6100 MHz (all other P-cores report 5800 MHz). They are the favoured/preferred
   cores, i.e. the ones that boost highest and run at the highest voltage/frequency. This is the pattern the
   Raptor Lake hypothesis predicts: the cores most exposed to Vmin-shift degradation are the first to fault.
4. **Microcode is already the newest available and uniform.** `0x133` on all 32 CPUs (Intel 2025-10-08
   update, `intel-microcode` 3.20260210), loaded for the whole 10-day boot, i.e. the 0x12B-era Vmin-shift
   mitigation is present on the host — and the host still faults on the highest-boost cores. Intel's
   microcode updates *prevent further* degradation and cannot repair already-degraded silicon, so this is
   consistent with degradation already present in those two cores. **Not established read-only:** whether the
   fault is that degradation or another core-local hardware defect, and the exact signal/faulting instruction
   in these three runs (the sandbox masks the worker's signal, and MCE/dmesg evidence is unreadable without
   `sudo`). No MCE record was obtainable (section 3).
5. **Practical consequence for the census:** do not run the MetaMaze census (or any JAX-heavy run) on CPUs
   8–11 on this host until a privileged diagnosis or hardware service. The previously accepted CPUs 0–3
   diagnostic baseline is reproducible bit-for-bit here, as are CPUs 4–7 and 12–15; any of those is a valid
   core group for the census workaround. This check makes no change to the host and no census claim.

## 7. No-change attestation

- No BIOS/firmware/kernel/governor/sysctl change, no `sudo` (password required), no deletion, no GPU lease, no
  GPU use (`CUDA_VISIBLE_DEVICES=""`; RTX 4090 at 353 MiB / 0 % before and after), no G1b/G5/G4 job, no
  commit/push.
- Kit worktree after the check: HEAD `aa354485bff6b5746c48ddadcb50d92e9c6f3645`, status only
  `?? third_party/mlgym/nodes/mlgym_metamaze/data` (the pre-existing setup data link), no new files under the
  kit; microcode still `0x133` on all 32 CPUs; no reboot; no leftover kit processes; prior evidence roots
  (`u2_census_smoke_20261125`, `…_RETRY`, `…_DIAG_CPUS_0_3`, `cpu_smoke_20261125`, the data snapshot) had
  **0 files modified** after this check began (`find … -newermt "2026-11-26 01:25:00"`).
- New files created: the remote evidence root
  `/home/dowling/r1_engineering/metamaze_20261125/tasl2_cpu_stability_20261125/` (runs 22 MB, results, host
  captures, logs, validation) and this report plus its captures in the ops worktree.

## 8. Evidence paths and SHAs

| item | path / sha256 |
|---|---|
| remote evidence root (preserved) | `/home/dowling/r1_engineering/metamaze_20261125/tasl2_cpu_stability_20261125` |
| ops-worktree captures (104 files + `SHA256SUMS`) | `docs/r1/reports/tasl_chain_20261122/captures/tasl2_cpu_stability_20261125/` |
| captures `SHA256SUMS` sha256 | **`1a2c80c87eb5b22f28a6585a86f425f891b5cb7c4d7fc879a500b0a2948832df`** (`sha256sum -c` rc 0 remote; `shasum -a 256 -c` rc 0 local) |
| driver / launcher | `scripts/run_baseline_stability.py` sha256 `848fcb9f72f5c6d4b53f23754f7e4b5e10bb67f86233f7f12825243e4014258b`; `scripts/launch_stress.sh` sha256 `01b74a1af43e0ced6d99c15161a9b7453ac8754f6b308d0dc65948158b421692` |
| per-run results | `results/g<group>_r<n>.json` (12) — full binding, process/exit/signal, hashes, log tail, isolation, scope memory peak |
| per-run records and outputs | `runs/<group>_r<n>/run_record.json`, `run.log`, `result_channel.txt`, `determinism_shim.json` (12 each) |
| ledger / launcher log | `logs/ledger.tsv`, `logs/launch_console.log`, `logs/<group>_r<n>.console.txt` / `.stderr.txt` |
| summary | `summary.txt`, `summary.json` (`tasl2_cpu_stability_summary/v1`) |
| host facts | `host/cpuinfo.txt`, `host/lscpu.txt`, `host/lscpu.json`, `host/admin_extra.txt`, `host/admin_microcode_probe*.txt`, `host/admin_readonly_probe.txt`, `host/kernel_log_search_readonly.txt` |
| validation-only run | `validation/validation.json` (+ `validation/runs_validation/`), sha256 `2510b4a083157da9ec1344fcbdacae902372b76ede44fe559c14b218c2c7cc5a` |
| launch commands/authorisation | `commands.txt` |
| preserved prior evidence (untouched) | `u2_census_smoke_20261125_DIAG_CPUS_0_3` (CPUs 0–3 PASS), `u2_census_smoke_20261125` (8–11 SIGSEGV STOP), `u2_census_smoke_20261125_RETRY` (8–11 SIGILL STOP) |

## 9. Limits of this check

- One baseline run per repeat, three repeats per group; no edits, no B1↔B2, no census measurement. Three
  passing groups at 3/3 is not a proof of long-run stability; it is enough to separate them from 8–11, which
  failed 3/3 in the same sequence.
- The exact worker signal in the three 8–11 runs is masked by the isolation launcher; the signal class comes
  from the preserved prior records (SIGSEGV, SIGILL) and from the launcher's exit-code mapping.
- No MCE/dmesg/journal record could be read (section 3), so the hardware-side attribution rests on the
  core-group localisation and the microcode/BIOS facts, not on machine-check counters.
- The only non-kit host activity during the window was this check's own read-only journal/dmesg probes (a few
  seconds of user-journal scans around 01:35–01:39Z, overlapping runs of groups 0–3/4–7); those runs are
  bitwise identical to the others, so no effect is visible.
- Independent review is pending (lead). No commit/push was made.

## 10. Independent review and options for the lead (not taken here)

Review status: **pending** — this record is prepared for the lead's independent review.

Options, for the lead (not acted on here):

1. **Workaround:** treat CPUs 8–11 as unusable for MetaMaze/JAX runs on TASL-2; run the census baseline on
   CPUs 0–3 (whose accepted diagnostic baseline this check reproduced bit-for-bit) or on 4–7/12–15.
2. **Diagnosis (needs privilege the check did not have):** as an admin, `sudo dmesg`/journal since 20 Nov for
   `mce`/`Machine check`/`trap invalid opcode`/`general protection` naming CPUs 8–11, plus
   `rasdaemon`/`mcelog` and a dedicated CPU stress test pinned to cores 4–5. That would name the signal and
   the MCE bank, which this read-only account cannot see.
3. **Hardware path:** if the two favoured cores are confirmed degraded, service/RMA the CPU under Intel's
   Raptor Lake extended-warranty programme and keep the census off that core group until then.
