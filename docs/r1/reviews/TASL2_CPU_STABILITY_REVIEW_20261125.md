# TASL-2 CPU stability check — independent review (26 November 2026)

**Reviewer.** Fresh independent reviewer (`tasl2-cpu-stability-reviewer`), delegated by the lead; no involvement in
the check, its driver/launcher, its captures or the record under review. Read-only: the only repository file written
by this review is this review. No run/edit/commit/push/delete of any repo, kit or host artefact; no smoke, no
`run_fixed_baseline`/`ar_worker` execution, no HTCondor/deepthought/TASL-7 action, no GPU workload or lease. TASL-2
was inspected with read-only `ssh -o BatchMode=yes portal_zhixu` commands (`ls`, `find`, `cat`, `stat`, `sha256sum`,
`sha256sum -c`, `apt-cache policy`, `ps`, `systemctl --user list-units`, `python3` JSON reads, and
`git --no-optional-locks -C … rev-parse/status`): nothing under any evidence root, checkout, venv, `~/r1_locks` or
repo was written. The only writes anywhere were two transient rc-capture redirects in `/tmp` on TASL-2
(`/tmp/_r2s_check.txt`, `/tmp/_r2s_check2.txt`), outside every evidence tree and the repo; no `sudo` was used or
available (`sudo -n` → password required).

**Object under review.**

- Record `docs/r1/reports/tasl_chain_20261122/TASL2_CPU_STABILITY_20261125.md` — **298 lines, 26,766 B, sha256
  `9dca2cf3c72185bcfb28eb9010f3d6287c8bdc1c5078ced08a788b16bca7164b`** (matches the sha supplied by the lead). At
  review time the file was present, untracked, in the **main checkout** `agent_paper_B` (branch `exam-x-20261026`,
  HEAD `8a819f75`); it is **not yet present in the `ops-tasl-20261116` worktree** at the nominal path (worktree HEAD
  `9253192f`) — see m1.
- Capture bundle `docs/r1/reports/tasl_chain_20261122/captures/tasl2_cpu_stability_20261125/` — **105 files = 104
  hashed + `SHA256SUMS`**; `SHA256SUMS` 9,897 B, 104 entries, sha256
  **`1a2c80c87eb5b22f28a6585a86f425f891b5cb7c4d7fc879a500b0a2948832df`** (matches the sha supplied by the lead).
  `shasum -a 256 -c` local **rc 0** (104/104 OK); the identical `SHA256SUMS` was verified on TASL-2 with
  `sha256sum -c` **rc 0**; the whole bundle therefore matches the preserved host capture set byte-for-byte.
- Host evidence root `/home/dowling/r1_engineering/metamaze_20261125/tasl2_cpu_stability_20261125` — inspected
  read-only on TASL-2 (1,795 files; `captures/` is the 105-file bundle; `runs/` 22 MB; 12 result JSONs, 12 run
  trees, one validation tree; no other run roots).
- Preserved prior evidence (not touched by the check) — `u2_census_smoke_20261125` (8–11 SIGSEGV),
  `u2_census_smoke_20261125_RETRY` (8–11 SIGILL), `u2_census_smoke_20261125_DIAG_CPUS_0_3` (CPUs 0–3 PASS) —
  re-read read-only to cross-check the record's prior-attempt claims.

**Verdict: ACCEPTED** for the record as a read-only CPU-stability check. **No BLOCKING and no MAJOR finding** was
found: every measured number in the record reproduces from the captures (and from the live host where the check's
claims are about host state), the stress design is the authorised one, the 9/9-pass vs 3/3-fail split is
bit-for-bit reproducible, the failure signature and the native-signal mapping are correctly derived from the
preserved prior attempts, the host facts (microcode, model/stepping, BIOS, kernel, topology, 6.1 GHz cores) are
exact, the dmesg/journal unavailability is disclosed and explicitly not claimed as absence, the validation-only run
is disclosed/excluded, and the hardware attribution is appropriately hedged as a hypothesis. The ten MINOR
findings below are accuracy/housekeeping issues that do not change any result; **m1 must be fixed before the record
is committed/cited** (the record and captures are not yet in the ops worktree the record itself names), and m2/m3/m4
are the wording fixes I would make in a revision.

## 1. Requirement-by-requirement verification

### 1.1 Microcode, model/stepping, BIOS, kernel; dmesg/journal; no system change

| claim in the record | independent verification | status |
|---|---|---|
| `0x133` on **all 32 CPUs** | Live TASL-2 `/proc/cpuinfo`: `grep '^microcode'` → 32 lines, one unique value, **`0x133`**; `/sys/devices/system/cpu/cpu0/microcode/version` = `0x133`. Captured `host/cpuinfo.txt` says the same (32 × `0x133`, unique count 1). | PASS |
| model 183 / stepping 1 (Raptor Lake-S) | `cpuinfo.txt`: 32 × `model 183`, 32 × `stepping 1`, `cpu family 6`, 32 processors/logical CPUs, 24 cores. Live: same. | PASS |
| microcode provenance: `intel-microcode 3.20260210.0ubuntu0.22.04.1`; `/lib/firmware/intel-ucode/06-b7-01` sha `e73efa95…`, 219,136 B, rev `0x133`, sig `0xb0671`, date `0x10082025` | Captured probes give the dpkg version, the file sha/size, the raw header and the Debian-changelog line `sig 0x000b0671, pf_mask 0x32, 2025-10-08, rev 0x0133, size 219136`. Live re-read at review: same sha256 (`e73efa954b94a0c09a63b010ed8abf82d3e714fc55dfad708f7a8a4067fe97d2`), same size; raw header bytes `33 01 00 00` / date bytes `25 20 08 10`. | PASS |
| "newest available" microcode | Not evidenced in the capture set (no `apt-cache`/upstream check). Reviewer re-checked read-only: `apt-cache policy intel-microcode` → installed **and candidate** `3.20260210.0ubuntu0.22.04.1`; `apt list --upgradable` has no microcode entry. So the claim holds on the configured, cached repositories, but this check should be added to the evidence (m6). | PASS (evidence gap, m6) |
| kernel 6.8.0-149-generic / Ubuntu 22.04.5 | `uname -a` live and captured: `6.8.0-149-generic #149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Oct 28 20:58:45 UTC`, Ubuntu 22.04.5 LTS. `/proc/cmdline` has no `mce=`/`idle=` override. | PASS |
| BIOS 2.4.0 dated 2023-12-11; Alienware Aurora R16, board 0RF96M | Captured DMI: `bios_version 2.4.0`, `bios_date 12/11/2023`, `product_name Alienware Aurora R16`, `board_name 0RF96M`; live: same. (SMBIOS MM/DD → 2023-12-11, as recorded.) | PASS |
| dmesg/journal **unreadable without sudo**, and no absence claimed | Captured `host/kernel_log_search_readonly.txt`: uid 1008, `CapEff 0000…`, `sudo -n` password required, `dmesg: read kernel buffer failed: Operation not permitted`, `dmesg_restrict=1`, `/dev/kmsg`/`/proc/kmsg` denied, `journalctl -k` permission hint + `-- No entries --`, `syslog:kern.log:syslog 0640` denied, `/sys/fs/pstore` denied, EDAC no `mc*`, no coredump. Record §3 says explicitly "**not evidence of absence**". Live re-check: `dmesg` still denied, `dmesg_restrict=1`, `sudo -n` still requires a password. | PASS |
| no system change (BIOS/firmware/kernel/governor/sysctl), no sudo, no deletion, no GPU lease, no GPU, no commit/push | Live post-check state matches the pre-check captures: microcode `0x133` ×32, **no reboot since 2026-11-15 12:51 PST** (so the microcode is the boot-loaded one), kernel cmdline, governor `powersave`, `no_turbo=0`, BIOS/DMI unchanged; kit HEAD `aa354485…`, branch `mac-trackg-mountaincar-20261125`, status only `?? third_party/mlgym/nodes/mlgym_metamaze/data`; `~/r1_locks/gpu0.lock` still 0 B with mtime 2026-11-22 06:58:52 −0800; no kit process alive; prior evidence roots have **0 files** newer than the check start (re-run with the intended UTC window: `find … -newermt "2026-11-25 17:25:00"` local PST = 01:25Z → 0). No sudo was possible. | PASS |

Host topology and "favoured 6.1 GHz" facts check out: `lscpu -e` / `admin_extra.txt` show `cpuinfo_max_freq` **6100 MHz
only for CPUs 8–11** (the two P-cores with `core_id` 16 and 20), 5800 MHz for CPUs 0–7 and 12–15, 4400 MHz for the 16
E-cores (CPUs 16–31); CPUs 0–15 are eight SMT pairs, 16–31 single-threaded; L3 36 MiB, 24 cores. The record's group
mapping (0–3 = P-cores #0–1, 4–7 = #2–3, 8–11 = #4–5, 12–15 = #6–7) matches `lscpu -e`, `topology/core_id` and
`thread_siblings_list`. The "favoured/preferred" designation is an inference from the 6100 MHz max (m9).

### 1.2 The stress — design, sequence, outcomes

| requirement | verification | status |
|---|---|---|
| exact reviewed MetaMaze baseline, 2,000,000 steps | Every stress run is `s000_baseline` at `run_budget = {kind: steps, value: 2000000}`, command `run_fixed_budget.py --steps 2000000`; node config `num_train_envs: 64`; executed `steps_max = 2,000,064 = (2,000,000 // 64 + 1) × 64`, `steps_full_budget=true`, seeds 8001/8001 (`AR_SEEDS train=8001 split=8001`), real pinned data manifest `e2338195…`, `AR_DEVICE cpu`, no GPU. Driver imports the kit's own `run_smoke_campaign()` with an empty proposal list and asserts exactly one record (`s000_baseline`) — the reviewed baseline step, not the full checklist-E smoke (record §4 states this correctly). | PASS |
| 4 groups (0–3/4–7/8–11/12–15) × 3 repeats, sequential, no other smoke | 12 result JSONs, 12 run trees, each tree exactly `s000_baseline/ + smoke_ledger.jsonl`; `affinity`/`cpu_affinity_matches_group` match 0–3, 4–7, 8–11, 12–15 in the fixed order; ledger/console timestamps are strictly sequential with no overlap (01:33:37→01:42:18Z) and print `=== DONE i/12`; no other run root exists. The one 2,048-env-step validation run at 01:32:59Z precedes the 12 and is disclosed/excluded (see 1.3). | PASS |
| each run in its own delegated 8 GB/swap-0 scope, `CUDA_VISIBLE_DEVICES=""`, taskset group, pinned PATH/interpreter | `external_limit`/`memory_max=8589934592`/`memory_swap_max=0` in every result; unique scope unit per run; `cuda_visible_devices=""`; `affinity` equals the group; `python_executable`/`python3_which` the pinned `venv_jax` interpreter; `ptrace_scope=1`. `cgroup.subtree_control` enabling failed `EBUSY` exactly as in the accepted DIAG run (verified: the DIAG raw summary has the same `[Errno 16] Device or resource busy`). | PASS |
| per-run binding (kit pin/pins/data/env) | All 12 results: HEAD `aa354485bff6b5746c48ddadcb50d92e9c6f3645`, branch `mac-trackg-mountaincar-20261125`, committed pin `759d6bf0…`, deployed pin `1eaaeac3…`, node spec `d97bb182…`, spec raw `d46dee59…`, edits manifest `6de5741f…`, `ar_isolated.py` `37d99ab0…`, data manifest `e2338195…` with 9 files re-hashed/read-only, freeze `630ed6e1…` (jax 0.4.35, torch absent). | PASS |
| 0–3/4–7/12–15 **3/3 PASS**, bitwise identical log/channel/metric | 9/9 records: rc 0, `outcome ok`, no signal/timeout/kill, `isolation.effective=true`, waivers `{}`, exceptions `[]`, frozen files 19/changed `[]`; one single `run.log` sha `8d85dad1e13ab0f667e43c242bdf41aee19619043d4df0c6ab6a6bdb090207b8` (26,543 B), one channel sha `9b08312199b96cafcfb171663a2a2271d3d59427cc96bee96435195e084eae14` (59 B, `val_return=8.703125`, `test_return=8.703125`), one `(val, sealed) = (8.703125, 8.703125)` across all nine. Direct host re-check of the **previously accepted CPUs 0–3 DIAG baseline**: `run.log` = the same `8d85dad1…`, channel = the same `9b08312…`, val/sealed 8.703125 — so the record's "equal to the accepted baseline exactly" claim is exact. | PASS |
| 8–11 **3/3 FAIL**, identical 538 B log, empty channel, no metric, native-signal class | 3/3 records: rc 1, `outcome divergent`, reason `nonzero_exit`, `elapsed_seconds_info_only` 5.257/4.414/3.872 s (wall 5.463/4.618/4.076 s), one single `run.log` sha `e11e7fc4ecdf5724cb8033b836812ee7e65fa15e8ec7ae269fcf33faaf9d1fe1` (**538 B**, matches the record's quoted content line-for-line), empty result channel (`e3b0c442…`, 0 B), `val/sealed = None`, `steps_max = None`, `baseline_check.ok=false`. No worker traceback in the captured log (worker stdout/stderr are inherited, so a Python traceback would appear). The record's launcher analysis is textually exact: `ar_isolated.py::_launch` line 668 is `os._exit(os.waitstatus_to_exitcode(status) & 0xFF if os.WIFEXITED(status) else 1)`, and the worker is PID 1 of a fresh PID namespace — a signalled PID-1 worker maps to launcher exit 1, which the parent then reports as `AR_ERROR worker train: connection closed (worker exit 1)`. | PASS (wording m3) |
| no OOM | Failing scope `memory.peak` 508.3–629.4 MiB vs cap 8,589,934,592 B; passing 759.0–763.8 MiB; `memory.swap.max=0`; no OOM/timeout/kill flags, no `oom`/`killed by`/`MemoryError` text in logs or records. Deaths are not memory-pressure kills. | PASS |
| no GPU | `CUDA_VISIBLE_DEVICES=""` in every binding; `AR_DEVICE cpu cpu` in logs; no torch/CUDA jaxlib; `nvidia-smi` before/after identical (RTX 4090, 353 MiB, 0 %); `gpu0.lock` untouched. | PASS |
| prior attempts consistent | Read-only on TASL-2: attempt A `s000_baseline` returncode **−11 (SIGSEGV)**, elapsed 51.934 s; retry `s000_baseline` returncode **−4 (SIGILL)**, elapsed 50.674 s; the other executed runs of both attempts died with rc 1 in 3.554–5.567 s (A) / 3.691–4.161 s (retry) — exactly the record's "3.5–5.6 s" early-death class. The prior-attempt evidence roots were not modified during this check (0 files newer than 01:25Z). The CPUs-0–3 DIAG PASS reproduces the same hashes as the stress passes. | PASS |

### 1.3 Record/captures accuracy, SHA, validation disclosure, overclaim

| item | verification | status |
|---|---|---|
| record sha / captures sha | `9dca2cf3…` matches the supplied record sha and the reviewed bytes; `1a2c80c8…` matches the supplied captures sha, 104 entries, local `shasum -c` rc 0, host `sha256sum -c` rc 0, 105 files total (104 hashed + `SHA256SUMS`). The record's §8 SHA/count claims are exact (driver `848fcb9f…`, launcher `01b74a1a…`, validation `2510b4a0…` all verified; driver/launcher identical in the host root and in `captures/scripts/`). | PASS |
| table values vs records | All 12 rows reproduce: verdict, rc, outcome, val/sealed, log bytes/sha, channel bytes/sha, steps, wall times, peak memory — with **two 0.1 MiB transcription errors** (m5): 12–15 r2 peak recorded 760.7 MiB, actual 797,732,864 B = 760.8 MiB; 8–11 r1 recorded 629.5 MiB, actual 660,017,152 B = 629.4 MiB. | PASS (m5) |
| validation-only 2k-step run disclosed/excluded | Record §4 discloses it (2,048 executed env steps / 2,000 budget at 01:32:59Z, 6.167 s info-only, val 1.632812, included under `validation/`, excluded from the 12). Captured `validation/validation.json` + `validation/runs_validation/` confirm it ran on CPUs 0–3 with `dryrun_steps=2000`, `steps_max=2048`, outcome `ok`, val 1.632812. It is **not** counted in the stress; the driver asserts exactly one record per stress invocation. But its own verdict is `VALIDATION_CRASH_OR_FAIL` with `baseline_check.ok=false` (`AssertionError: loss_regex matched no line of the baseline log`) — expected at this budget, but not quite what the record's "run-level ok"/"check_baseline_log is expectedly empty" wording conveys (m2). | PASS (m2) |
| no overclaim of hardware cause | The record says "consistent with (Vmin-shift-type) degradation", "the pattern the Raptor Lake hypothesis predicts", and explicitly: "**Not established read-only:** whether the fault is that degradation or another core-local hardware defect, and the exact signal/faulting instruction". §9 lists the limits (masked signal, no MCE/dmesg read, 3/3 not long-run proof). This is correctly hedged; the host facts (uniform `0x133` microcode, no reboot, only CPUs 8–11 at 6100 MHz, 8–11 reproducibly failing while the other three pairs pass) are exact. | PASS |
| CPU topology / favoured 6.1 GHz cores | Verified against live host and captures (see 1.1); "favoured/preferred" and "highest voltage" are inferences from the 6100 MHz max, not separately read (m9). | PASS (m9) |

## 2. Findings

### BLOCKING

None.

### MAJOR

None.

### MINOR

- **m1 — the record and captures are not yet in the ops worktree the record names.** The reviewed record and its
  capture bundle live (untracked) only in the sibling main checkout (`agent_paper_B`, branch `exam-x-20261026`); at
  review time `docs/r1/reports/tasl_chain_20261122/TASL2_CPU_STABILITY_20261125.md` and its
  `captures/tasl2_cpu_stability_20261125/` do **not** exist in `ops-tasl-20261116`, although the record §7 says the
  report+captures are "in the ops worktree" and §8 labels the captures "ops-worktree captures". This is a
  location/housekeeping defect, not a content defect: the reviewed bytes are the correct `9dca2cf3…` bytes and the
  capture bundle is byte-identical to the preserved host set (`1a2c80c8…`, verified both ends). **Fix before
  commit/citation:** place the record and the 105-file bundle in the ops worktree at the stated paths, or correct
  the location wording. No re-run or re-hash is implied.
- **m2 — validation-only run description is slightly inaccurate.** `validation/validation.json` has
  `"verdict": "VALIDATION_CRASH_OR_FAIL"` and `baseline_check = {ok: false, error: "AssertionError: loss_regex matched
  no line of the baseline log"}`; the record says "run-level `ok`" and "its `check_baseline_log` is expectedly empty
  at that budget (no loss lines)". The run outcome is indeed `ok` and the failure is expected at 2,000 steps, but a
  reader comparing the JSON sees a CRASH_OR_FAIL validation record; say so explicitly ("the reduced-budget
  validation's baseline log has no loss lines, so `check_baseline_log` raises by design and its record verdict is
  `VALIDATION_CRASH_OR_FAIL`; excluded from the 12"). Also note the budget is 2,000 with 2,048 executed env steps
  (record calls it "2,048-step"), not 2,048 budget.
- **m3 — "not a Python-level exit" is stronger than the launcher code proves.** `ar_isolated.py::_launch` maps
  `os.waitstatus_to_exitcode(status) & 0xFF` for `WIFEXITED` **and** 1 otherwise; a normal Python exit code 1 and a
  signalled worker both surface as launcher exit 1. The record's inference is well supported (no worker traceback in
  the inherited stdout/stderr; the same `AR_ERROR worker train: connection closed (worker exit 1)` appears in the
  prior attempts where the direct child demonstrably died of SIGSEGV/SIGILL), and §9 already says the signal is
  masked. Wording fix: "consistent with a signalled worker rather than a Python-level exception" instead of "not a
  Python-level exit".
- **m4 — two time bases are used without labels.** §0/§6 headline ranges are `elapsed_seconds_info_only` (0–3:
  53.463–53.716 → "53.5–53.7"; 4–7: 53.365–54.131 → "53.4–54.1"; 12–15: 53.205–53.249 → the record's "53.2–53.4"
  mixes in the 53.456 wall; 8–11: 3.872–5.257 → "3.9–5.3"), while the §5 table is wall seconds (0–3:
  53.671–53.925; 4–7: 53.573–54.347; 12–15: 53.413–53.456; 8–11: 4.076–5.463). Both sets are correct for their
  fields; label the headline ranges as
  elapsed (or use wall consistently). This is the only place where a reader can think a table row contradicts the
  headline.
- **m5 — two peak-memory transcriptions.** 12–15 r2: record 760.7 MiB, actual
  `scope_memory_peak_bytes = 797,732,864` = 760.8 MiB; 8–11 r1: record 629.5 MiB, actual `660,017,152` = 629.4 MiB.
  Every other peak rounds as recorded; 0.1 MiB, no interpretation depends on it.
- **m6 — "newest available" microcode is asserted, not captured.** The capture set has the installed package and
  its changelog but no `apt-cache policy`/upgradable check; "newest available" is therefore only "newest in the
  installed package" in the evidence. I verified read-only that the apt candidate equals the installed
  `3.20260210.0ubuntu0.22.04.1` and there is no upgradable microcode, so the claim is true as of review; add the
  `apt-cache policy` line to the captures (or reword to "newest in the installed package/repositories") before the
  record is cited on this point. This matters because it closes the "update microcode first" alternative.
- **m7 — the first (aborted) launcher invocation is not disclosed.** `logs/launch_console.log` shows a
  `[2026-11-26T01:33:19Z] STOP: another kit process is running; refusing to start: 3363283 grep -E
  run_fixed_budget\.py|…` — a self-match of the process probe (PID 3363283, the launcher's own search pattern; it is a
  `grep`, not a kit process), followed by the real start at
  01:33:37Z. No run executed, so nothing in the 12 results or the conclusions is affected, and the record's "no other
  kit process" is true; but the record frames 01:33:37 as "launcher start" without mentioning the 18 s earlier
  abort. Disclose it (one sentence) and fix the guard (`grep -v` on the pipeline's own pid, or `pgrep -f` with a
  self-exclusion) so a future launch cannot halt on its own probe.
- **m8 — the `find -newermt` attestation lacks a timezone.** §7 quotes
  `find … -newermt "2026-11-26 01:25:00"`. The host is PST (UTC−8), so that parses as 09:25Z **after** the check,
  and the recorded "0 files modified" would be vacuous. I re-ran the intended window read-only (files newer than
  17:25 PST = 01:25Z) over the four prior evidence roots: **0 files**, so the claim is true; the quoted command
  should be fixed to `-newermt "2026-11-26 01:25:00Z"` or run with `TZ=UTC`.
- **m9 — the favoured/preferred and "highest voltage" characterisation is inferred, and the core naming is easy to
  misread.** The only directly observed fact is `cpuinfo_max_freq = 6,100,000` for CPUs 8–11 and 5,800,000 for the
  other P-core CPUs (plus `lscpu -e`), which the record reports correctly; "favoured/preferred" (Turbo Boost Max
  3.0) is an inference from that, and "run at the highest voltage/frequency" is not measured in this check. Also
  "physical cores 4 and 5" refers to P-core ordinals while the kernel `core_id`s are 16 and 20 (the record gives both
  in §2, so this is presentation, not error). Suggested wording: "P-cores #4–5 (core_id 16, 20; CPUs 8–11), the only
  cores with a 6.1 GHz `cpuinfo_max_freq`; the favoured-core interpretation is inferred from that max".
- **m10 — the summary capture's `utc_last_end` is wrong.** `summary.json` has
  `"utc_last_end": "2026-11-26T01:39:32Z"` (the last row in its sorted order, 8–11 r3) rather than 01:42:18Z
  (12–15 r3); `summary.txt` and the record have the correct window. The record does not rely on the field, so this
  is a capture-generation defect; fix the generator or regenerate the bundle if the summary is cited as-is
  (regenerating changes the bundle sha, so it is not required for this record).

### Observations (no action required)

- The stress's 8–11 failures all landed **early** in the worker (3.9–5.3 s), whereas the preserved prior attempts'
  baseline runs trained the full 2M steps and then died in evaluation (SIGSEGV/SIGILL). The record states this
  difference and argues the same native-crash class; that is reasonable (the prior attempts also had the same early
  worker deaths at 3.5–5.6 s), but the exact faulting stage/signal in these three runs is unobservable read-only —
  as the record's §9 says.
- `apt-cache` lists were last refreshed 2026-11-19, one week before the check; "newest" therefore means "newest in
  the host's cached repositories". A privileged/online microcode check remains part of the follow-up.
- The record's "5 independent failures" counts two prior launches + three stress runs; the prior attempts each also
  had several worker deaths. The count is defensible at launch granularity, but "five failed launches" is clearer.
- The `loadavg` values at run start rise from 0.31 to ~3.6–4.0 during the sequence; this is consistent with the
  run's own 4 threads (`workers.threads: 4`) and the record's own journal probes, not with another kit; the 12–15
  runs after 8–11 still pass bit-for-bit, and the prior 8–11 failures occurred on an idle host (load < 0.1). No
  contention confound is indicated.

## 3. Recommendation and workaround

1. **Operational workaround (safe now):** do not run the MetaMaze census (or other JAX-heavy work) pinned to CPUs
   8–11 on TASL-2. Use CPUs 0–3 (strongest: the previously accepted DIAG census and this check both reproduce
   `8d85dad1…` / `9b08312…` / 8.703125; three 2M-step baselines 3/3), or 4–7 / 12–15 (each 3/3 at 2M steps). Prefer
   0–3 until the privileged diagnosis is done; the 3/3 result is not a long-run stability proof for 4–7/12–15
   (record §9).
2. **Privileged diagnosis (needed to name the cause):** with `sudo`, read `dmesg`/journal since 20 Nov for
   `mce`/`Machine check`/`trap invalid opcode`/`general protection`/`SIGSEGV` naming CPUs 8–11; run
   `rasdaemon`/`mcelog`; run a dedicated core-pinned stress on cores 4/5 (and on a passing pair as control) with
   signal-level capture (e.g. `taskset` + `dmesg -w` + `perf`), so the masked worker signal becomes visible. The
   read-only account cannot do this.
3. **Microcode/BIOS:** `0x133` is the candidate/installed microcode and the 2025-10-08 Raptor Lake revision, newer
   than the 2023-12-11 BIOS — so there is no "apply the missing microcode" fix left on this host within its cached
   repositories; the record's conclusion that the microcode mitigation is present is sound. A BIOS update is an
   admin decision, not an established remedy, and would need its own evidence.
4. **Hardware path:** if the privileged diagnosis confirms core-local faults, service/RMA the CPU under Intel's
   Raptor Lake extended-warranty programme; keep the census off CPUs 8–11 until then. This check is
   **ENGINEERING_ONLY** and makes no census/measurement claim; no system change and no census run should be inferred
   from it.

## 4. Limits of this review

- I did not re-run any kit/smoke or reproduce the stress; this review verifies the record against its captures and
  against the live host state read-only at ~2026-11-26T01:55Z (≈13 min after the check ended), not by rerunning.
- The exact worker signal of the three 8–11 failures is not observable through the isolation launcher; I verified
  the record's masking analysis and its consistency with the prior SIGSEGV/SIGILL records, not the signal itself.
- Host "no change" is established from matching pre-check captures and post-check host state plus the no-reboot /
  no-sudo facts; a full audit trail of every syscall is not possible read-only.
- The record and captures were read from the main checkout copy (m1); the bytes are the sha-verified reviewed bytes,
  and the capture bundle verifies identically on the host, so m1 does not affect any finding.
- Transient writes: two `/tmp` rc-capture redirects on TASL-2 (disclosed above); nothing under any evidence root,
  repo, kit or lock was written; no deletion; no GPU lease; no HTCondor.

## 5. Evidence index for this review

| item | value |
|---|---|
| record | 298 lines / 26,766 B / sha256 `9dca2cf3c72185bcfb28eb9010f3d6287c8bdc1c5078ced08a788b16bca7164b` |
| captures | 105 files (104 hashed); `SHA256SUMS` 9,897 B / 104 entries / sha256 `1a2c80c87eb5b22f28a6585a86f425f891b5cb7c4d7fc879a500b0a2948832df`; local and host `-c` rc 0 |
| host evidence root | `/home/dowling/r1_engineering/metamaze_20261125/tasl2_cpu_stability_20261125` (runs 22 MB; 12 results; 12 run trees; 1 validation tree) |
| stress records | `results/g<group>_r<n>.json` ×12; `runs/g<group>_r<n>/{run.log,run_record.json,result_channel.txt,determinism_shim.json}` |
| passing runs | log `8d85dad1e13ab0f667e43c242bdf41aee19619043d4df0c6ab6a6bdb090207b8` (26,543 B); channel `9b08312199b96cafcfb171663a2a2271d3d59427cc96bee96435195e084eae14` (59 B); val/sealed 8.703125; 9/9 |
| failing runs | log `e11e7fc4ecdf5724cb8033b836812ee7e65fa15e8ec7ae269fcf33faaf9d1fe1` (538 B); channel `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (0 B); rc 1/divergent; 3/3 |
| prior evidence | attempt A `s000_baseline` rc −11 (SIGSEGV) 51.934 s; retry `s000_baseline` rc −4 (SIGILL) 50.674 s; DIAG 0–3 PASS with the same `8d85dad1…`/`9b08312…`/8.703125 |
| host facts | 32 × microcode `0x133`; model 183 / stepping 1; kernel 6.8.0-149; BIOS 2.4.0 2023-12-11; boot 2026-11-15 12:51 PST, no reboot; governor powersave, `no_turbo=0`; 6100 MHz only CPUs 8–11; `intel-microcode 3.20260210.0ubuntu0.22.04.1` = apt candidate |
| scripts | driver `848fcb9f72f5c6d4b53f23754f7e4b5e10bb67f86233f7f12825243e4014258b`; launcher `01b74a1af43e0ced6d99c15161a9b7453ac8754f6b308d0dc65948158b421692` |
| evidence sealing | data manifest `e2338195…`; venv freeze `630ed6e1…`; validated per-run via `isolation.effective=true`, waivers `{}`, frozen files 19/changed `[]` |
