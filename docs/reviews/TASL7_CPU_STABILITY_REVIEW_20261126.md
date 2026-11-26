# TASL-7 CPU-set stability check — independent review (26 November 2026)

**Reviewer.** Fresh independent reviewer (`tasl7-cpu-stability-reviewer`), delegated by the lead; no involvement in
the check, its driver/launcher, its captures or the record under review. Read-only: the only repository file written
by this review is this review. No run/edit/commit/push/delete of any repo, kit or host artefact; no smoke, no
`run_fixed_budget`/`ar_worker` execution, no GPU workload or lease; no HTCondor action. TASL-7 was inspected with
read-only `ssh -o BatchMode=yes tasl7` commands (`ls`, `find`, `cat`, `stat`, `sha256sum`, `sha256sum -c`, `du`, `ps`,
`systemctl --user list-units`, `nvidia-smi`, `git --no-optional-locks rev-parse/status`, `python3 -B` JSON reads and
one read-only import of the kit's own pin helpers with `-B`/`PYTHONDONTWRITEBYTECODE=1`). The only write anywhere was
one transient `/dev/shm/freeze.<pid>` on TASL-7 holding the `pip freeze` stream for its sha256; it was removed
immediately and was outside every evidence root, the repo, kits, venvs and locks (disclosed; see §4). No `sudo` was
used or available (`sudo -n` → password required, `CapEff` 0). Nothing under any evidence root, checkout, venv
`~/r1_locks` or repo was written; no deletion; no GPU lease.

**Object under review.**

- Record `docs/r1/reports/tasl_chain_20261122/TASL7_CPU_STABILITY_20261126.md` — **313 lines, 31,209 B, sha256
  `04153a576791e5f54945ada5d7e01afccde4e62b6acbdebceaa6bbb6dd4a45a7`**. At review time the file was present,
  untracked, in the **main checkout** `agent_paper_B` (branch `exam-x-20261026`, HEAD `8a819f75`); it is **not yet
  present in the `ops-tasl-20261116` worktree** at the record's nominal path (worktree HEAD `9253192f`) — see m1.
- Capture bundle `docs/r1/reports/tasl_chain_20261122/captures/tasl7_cpu_stability_20261126/` — **282 files = 281
  hashed + `SHA256SUMS`** (plus 2 unhashed data symlinks in the validation run tree); `SHA256SUMS` 35,798 B, 281
  entries, sha256 **`0dcfdea70de3e0923eaeb60c33ecacc555da051d5d342821f2ed7b50718e10cd`**. Local
  `shasum -a 256 -c` **rc 0** (281/281 OK); the identical `SHA256SUMS` in the preserved host capture set verifies
  with `sha256sum -c` **rc 0**; **all 281 captured hashes were compared file-by-file against the remote originals
  under the evidence root and match** (results, runs, host, logs, validation, scripts, summary).
- Host evidence root `/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126` — inspected
  read-only on TASL-7: 18 result JSONs, 18 run trees (132 files each, exactly one `s000_baseline` run id each, no
  other run root), 1 validation tree, and the original host/log/script captures (8 host files, 41 log files, 8
  root scripts/commands); the root also holds the 282-file capture set; 43 MB including captures (39 MB pre-capture,
  as captured in the post-check).
- Cross-host reference (read-only, local): accepted TASL-2 record `TASL2_CPU_STABILITY_20261125.md` (sha256
  `9dca2cf3c72185bcfb28eb9010f3d6287c8bdc1c5078ced08a788b16bca7164b`) and its capture bundle
  (`SHA256SUMS` sha256 `1a2c80c87eb5b22f28a6585a86f425f891b5cb7c4d7fc879a500b0a2948832df`, 104 entries, 105 files,
  local `-c` rc 0). Values used for the cross-host comparison: TASL-2 `val_return` 8.703125 / sealed 8.703125,
  `run.log` `8d85dad1…`, channel `9b08312…`; TASL-2 host Intel i9-14900KF (Raptor Lake); same kit HEAD, env freeze
  and data manifest as TASL-7.

**Verdict: ACCEPTED** for the record as a read-only CPU-set stability check. **No BLOCKING and no MAJOR finding.**
All measured claims of the record reproduce from the captures and, where they concern host state, from a live
read-only inspection of TASL-7: the exact census baseline (full 2,000,000-step `s000_baseline`, seeds 8001/8001) ran
**18/18 PASS** on the six 4-CPU groups ×3 sequential repeats, every run `rc 0` with no signal, no timeout, no
kill and no leftover process, own delegated 8 GB/swap-0 scope, `CUDA_VISIBLE_DEVICES=""`, CPU-only JAX, and all 18
produced **one byte-identical `run.log` and one byte-identical result channel** (`val_return` 7.710938, sealed
`test_return` 7.4375, steps 2,000,064). The host facts (Ryzen 9 7900X 24 CPUs, microcode `0xa601203` uniform,
`amd-pstate-epp` + `powersave`/`balance_performance`, identical 5,733,000 kHz max on all 24 CPUs, no reboot, no
system change) are exact; the "other user's GPU job" attribution is correct; the cross-host caveat is present and
correct (TASL-7 bytes are host-local, not comparable to TASL-2). The seven MINOR findings are accuracy/housekeeping
issues that change no result; **m1 (record/captures not yet in the ops worktree) must be fixed before the record is
committed/cited, and m2 (two truncated hashes) before the evidence table is relied on**; m3–m7 are wording/capture
fixes I would make in a revision.

## 1. Requirement-by-requirement verification

### 1.1 The stress — exact baseline, six groups, sequence, determinism

| claim in the record | independent verification | status |
|---|---|---|
| exact reviewed MetaMaze **baseline** run `s000_baseline`, full 2,000,000 steps, seeds 8001/8001 | Every result's `run.run_id = s000_baseline`, `run_budget = {kind: steps, value: 2000000}`, command `python3 -s run_fixed_budget.py --steps 2000000`, `seeds {train: 8001, split: 8001}` (log `AR_SEEDS train=8001 split=8001`), `steps_max = 2,000,064 = (2,000,000 // 64 + 1) × 64` with `num_train_envs: 64`, `steps_full_budget = true`; the driver's own source calls `ps.run_smoke_campaign(spec, work, runs_root, [], lim, train_seed=8001, split_seed=8001)` and asserts exactly one record with `run_id == "s000_baseline"`; each host run tree contains only that one run id. | PASS |
| 6 groups 0–3/4–7/8–11/12–15/16–19/20–23 × 3 repeats, **sequential**, no other smoke | 18 result JSONs and 18 run roots; `affinity` = the group in every record (`cpu_affinity_matches_group` true; groups exactly `[0-3],[4-7],[8-11],[12-15],[16-19],[20-23]`); `logs/ledger.tsv` 18 rows in launcher order; the captures hold 18 console + 18 stderr logs, the host run trees hold 18 `smoke_ledger.jsonl` with one `s000_baseline` each; no `STOP`/`SKIP`/`WARNING` line in `logs/launch_console.log`; UTC starts/ends are strictly sequential and non-overlapping, `07:07:52Z → 07:23:08Z` (15 m 16 s); no other run root or run id exists under the evidence root. | PASS |
| each run in its own delegated 8 GB / swap-0 scope, `taskset -c <group>`, `CUDA_VISIBLE_DEVICES=""`, pinned PATH/interpreter | Every result: unique `cgroup` per run, `memory_max = 8589934592`, `memory_swap_max = 0`, `cuda_visible_devices = ""`, `affinity` = group, `python_executable`/`python3_which` the pinned `venv_jax` interpreter, `ptrace_scope = "1"`; `external_limit` records the `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` unit. The launcher passes exactly that `systemd-run` invocation (captured `commands.txt` and `launch_stress.sh`). `cgroup.subtree_control` enabling failed `EBUSY` (recorded per run; the record discloses it and does not treat it as a waiver — the scope `memory.peak` is the resource number) exactly as the accepted TASL-2 record states. | PASS |
| per-run binding: kit pin, pins, data, env, interpreter, affinity | All 18 records: HEAD `aa354485bff6b5746c48ddadcb50d92e9c6f3645`, branch `mac-trackg-mountaincar-20261125`, `status_porcelain` only `?? third_party/mlgym/nodes/mlgym_metamaze/data`; committed pin `759d6bf0…7d03db`, deployed pin `1eaaeac3…bf9ecb7`, node spec `d97bb182…679dbb9`, spec raw `d46dee59…cb3c59`, edits manifest `6de5741f…66f0b2`, `ar_isolated.py` `37d99ab0…e48b610` (node and master copies equal), run budget steps 2,000,000; data manifest `e2338195…e99c38000`, 9 files re-hashed (`files_all_match` true), `read_only` true, root mode `0o40555` outside the repo; `venv_jax` freeze sha256 `630ed6e1…388f5fdd9` (56 packages), jax/jaxlib 0.4.35, torch absent. **I recomputed the composite pins independently on TASL-7 with the kit's own helpers (read-only): node spec `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9`, committed pin `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db`, deployed pin `1eaaeac351280e16295eae0f50212f352b1aa0c4c3d26a410b58bb0c3bf9ecb7`, 18 frozen files, budget steps 2,000,000 — all match the record and the accepted TASL-2 values.** | PASS |
| all six groups **PASS 3/3** | Group verdicts `PASS 3/3` for all six groups (18/18); every row `verdict PASS`, `outcome.kind ok`, parent `returncode 0`, `signal null`, `timed_out false`, `killed_with null`, `baseline_check.ok true`. | PASS |
| 18/18 **byte-identical** `run.log` and result channel, same metric | One `run.log` sha256 **`f3d6e3a844d0525e1d18643d87467cff942d21911c7941d20ee9e2b0a7fee720`** (26,561 B, 1,904 lines, 947 log loss lines `step … loss …`) for all 18; one channel sha256 **`b60323b4a4710f396cc8464c03227471b2eca835357765d33c8c28ba2852427d`** (59 B, `AR_METRIC val_return=7.710938` / `AR_TEST test_return=7.437500`) for all 18; one `(val_return, sealed_test_return) = (7.710938, 7.4375)` across all 18; every log has exactly one `AR_STEPS env_steps=2000064` and one `AR_WORKER exit=0`; no `Traceback`/`SIGSEGV`/`SIGILL`/`Killed`/`ERROR` token in any log. The record's full hashes, byte counts and channel content are exact. | PASS |
| reviewed `check_baseline_log()` PASS on all 18 | The reviewed check (`tests/trackg/port_support.py:510` on the host) requires ≥1 finite loss line, exactly one metric line in the channel and none in the log, steps ≥ budget, exactly one sealed-test line, no stray CR. I re-applied those invariants to all 18 captured log/channel pairs: 947 finite loss lines each, one channel `AR_METRIC`, none in the log, one `AR_TEST`, max `AR_STEPS` 2,000,064, no `\r`. All pass. | PASS |
| isolation effective 18/18 | Every result: `isolation.effective = true`, `waivers = {}`, `exceptions = []`, `frozen_files_checked = 19`, `frozen_files_changed = []`; cgroup records show the child cgroup removed and `kill` empty/inactive; captured `logs/postcheck.txt` and live `ps`/`systemctl --user list-units` after the check show no leftover kit process or `tasl7-baseline` scope. | PASS |
| no crash / no signal / no timeout / no memory pressure | 18/18 `rc 0`, no signal, not timed out, `baseline_check` ok; peaks **760.2–773.7 MiB** against the 8,589,934,592 B cap and **swap 0** (`memory.swap.max = 0`); no OOM/kill text. | PASS |
| **CPU-only**, no GPU use/lease | Every log: `AR_DEVICE cpu cpu jax=0.4.35 workers=0`, plus the JAX warning "CUDA-enabled jaxlib is not installed. Falling back to cpu."; every binding `cuda_visible_devices = ""`; torch not importable; `nvidia-smi` at launcher start and post-check shows the RTX 4090 held by **another user's** job (PID 1648890, owner `jiachenl`, 5,126 MiB / 100 % at the post-check), while `/home/dowling/r1_locks/gpu0.lock` is 0 B dated 21 Nov and unchanged; live re-check at review shows four GPU compute processes whose executables are under `/home/jiachenl/litian/hf-go2/...` (new PIDs, same other-user job tree) and no `venv_jax` python on the GPU. | PASS |
| validation-only run disclosed and excluded | One reduced-budget run on CPUs 0–3 at `2026-11-26T07:07:36Z–07:07:45Z`, `dryrun_steps = 2048`, `steps_max = 2112`, `returncode 0`, outcome `ok`, `val_return 4.21875`, sealed 3.429688, `baseline_check.ok = false` (expected: no loss lines at that budget), `verdict VALIDATION_CRASH_OR_FAIL`; under `validation/`, not counted in the 18. The record discloses all of this (§2). | PASS |

### 1.2 Host facts, microcode, power, no system change, other user's GPU job

| claim in the record | independent verification | status |
|---|---|---|
| AMD Ryzen 9 7900X 12-Core (Zen 4), family 25 / model 97 / stepping 2, 12 cores / 24 logical CPUs 0–23, SMT2, 2 CCDs (core ids 0–5 and 8–13), L3 64 MiB in 2 instances, 1 NUMA node | Captured `host/cpuinfo.txt`, `host/lscpu.txt`, `host/admin_extra.txt` (`lscpu -e`, per-CPU `topology/core_id`/`thread_siblings_list`); live re-check matches the model name and 24 online CPUs; the per-CPU topology, L3 and NUMA are from the captured `lscpu`. Group mapping: 0–3 = cores 0–3 (CCD0); 4–7 = cores 4,5 + 8,9; 8–11 = cores 10–13 (CCD1); 12–15/16–19/20–23 are the SMT siblings of 0–3/4–7/8–11 — exactly as recorded. | PASS |
| microcode **`0xa601203` on all 24 CPUs**, uniform; installed `amd64-microcode` 3.20191218.1ubuntu2.3; no installed blob contains the loaded patch; loaded revision therefore pre-OS/BIOS-supplied | `/proc/cpuinfo`: 24 × `microcode : 0xa601203`, one unique value before, during and after the check and at review; `host/admin_microcode_probe.txt` + `host/admin_amd_extra.txt`: package version, five `/lib/firmware/amd-ucode` blobs (2019/2024), byte-scan occurrences 0. **I independently scanned the five installed blobs for the raw 32-bit loaded patch id in both endiannesses: 0 occurrences in every blob**, so the record's "not in the installed distro package" statement is exact. The attribution "comes from BIOS/UEFI" is an inference (see m5; the record itself says the exact firmware image and "newest" status are not established read-only). | PASS (wording m5) |
| kernel 6.8.0-149-generic, Ubuntu 22.04.5 LTS, no `mce=`/`idle=` cmdline overrides; booted 2026-11-17 14:53, no reboot during the check; BIOS 1.10.1 dated 2023-12-21 (Alienware Aurora R15 AMD, board 0KDR38) | Captured `cpuinfo.txt` and `admin_extra.txt` (DMI: product/board/BIOS); live: same kernel and `/proc/cmdline`; boot still `2026-11-17 14:53:05`, uptime 8 d 8 h 40 m at review — no reboot since the check (or since 2026-11-17), so the microcode is the boot-loaded revision throughout. | PASS |
| `amd-pstate-epp` active, governor `powersave`, EPP `balance_performance` on all CPUs; **`cpuinfo_max_freq` identical 5,733,000 kHz on all 24 CPUs** (no favoured-core max-frequency split); no `boost` control file | Captured per-CPU topology/frequency table (24 CPUs, `maxfreq=5733000` each; `governor=powersave`, `epp=balance_performance` each); live re-check over all 24 `/sys` entries: `5733000` ×24, `powersave` ×24, `balance_performance` ×24, `amd_pstate status active`, `prefcore enabled` with no exposed ranking, no `boost` file. | PASS |
| read-only kernel/MCE log probes unavailable, failure recorded rather than claimed as absence | `host/admin_readonly_probe.txt`, `host/kernel_log_search_readonly.txt`: uid 1011, `CapEff 0`, `sudo -n` password required, `dmesg_restrict=1`, `dmesg`/`/proc/kmsg` denied, journal visibility hint + `-- No entries --`, `/var/log/{syslog,kern.log}` `0640` denied, `/sys/fs/pstore` denied, no EDAC `mc*`, no coredump, 12 search patterns × journal scopes = 0 matches; record §4 says explicitly the search "is **not** evidence of absence" and claims no MCE record. Live re-check: `dmesg` still denied, `dmesg_restrict=1`, `sudo -n` still requires a password. | PASS |
| shared host; another user's GPU training job (`jiachenl`, PID 1648890, RTX 4090) **not ours**; no GPU lease; no other kit/smoke process | Captured pre-check: GPU 44 MiB / 0 %, no kit process of ours, no kit-pattern process of any user; launcher start and post-check: GPU 5,175 MiB / 100 %, compute app PID 1648890 owner `jiachenl` (5,126 MiB), no `venv_jax` python; `gpu0.lock` 0 B dated 21 Nov untouched. Live at review: GPU compute apps are four processes whose executables are under `/home/jiachenl/litian/hf-go2/...` (PIDs 1662461…, same other-user job tree), with no `dowling`/`venv_jax` GPU process; no leftover scope/process of ours. | PASS |
| **no system change** (BIOS/firmware/kernel/governor/sysctl), no sudo, no deletion, no commit/push | Post-check state equals pre-check captures: microcode ×24 `0xa601203`, governor/EPP unchanged, boot unchanged, kit HEAD/branch/status unchanged (`?? …/data` only), `r1_locks` unchanged, no leftover scopes/processes; live re-check agrees and adds: **no file under the kit, venv or data root is newer than the check start**, kernel cmdline/`dmesg_restrict`/`ptrace_scope` unchanged, `git status` unchanged after my read-only pin recomputation (no file written). No sudo was possible (password required, caps 0). | PASS |

### 1.3 Record/captures accuracy, SHA, copy/verify, cross-host caveat, overclaim

| item | verification | status |
|---|---|---|
| record sha / size | `04153a576791e5f54945ada5d7e01afccde4e62b6acbdebceaa6bbb6dd4a45a7`, 31,209 B, 313 lines — matches the bytes I reviewed (the record at the path the lead asked me to review). | PASS |
| captures sha / count / `-c` both ends | `SHA256SUMS` sha256 `0dcfdea70de3e0923eaeb60c33ecacc555da051d5d342821f2ed7b50718e10cd`, 281 entries, 282 files (281 hashed + `SHA256SUMS`), local `shasum -c` rc 0, host `sha256sum -c` rc 0; the host capture set has the same sha and file count, and **all 281 captured hashes equal the remote originals**. | PASS |
| table values vs per-run records | All 18 rows reproduce exactly: verdict, rc, signal, outcome, `val_return` 7.710938, sealed 7.4375, log/channel sha and byte counts (26,561 / 59), steps 2,000,064, **wall times and peak memory to the recorded precision**, UTC start/end, group affinity, scope peak. No transcription difference found in §6 (wall 42.861–56.802 s; peaks 760.2–773.7 MiB). | PASS |
| validation-only records/sha | `validation/validation.json` sha256 `78c610a1ccf05787d70b46ba944348592832243bdae28740ef85109522e5d2fe` (matches §9); content as disclosed (2,048-step run, CPUs 0–3, val 4.21875, sealed 3.429688, steps 2,112, expected `baseline_check` assertion, `VALIDATION_CRASH_OR_FAIL`). | PASS |
| driver / launcher / script hashes | Driver `c2ed5af60a8e205d394699945d84fefda6b4fe096813fe4a9e5b9240e2e481cf` and launcher `5444865648a3cfe58c3b50713de074846c93e39dd66ddbac11f9567c75b313c8` are exact (full hashes). Of the five §9 script-hash fragments, **three are exact and two are mistyped** — see m2 (evidence unaffected: `SHA256SUMS` carries the full hashes and verifies both ends). | PASS (m2) |
| copy/verify of kit, env, data; pins; interpreter binding | Live TASL-7: kit HEAD/branch/status exactly as recorded; env freeze `630ed6e1…` (56 packages), jax/jaxlib 0.4.35, torch absent, python 3.12.16 realpath `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`; data manifest `e2338195…`, 9/9 files re-hashed and matching, dir `0555`, files `0444`, symlinked outside the repo; composite pins independently recomputed and equal (§1.1); sizes match the record's intent (kit 14 MB, venv 918 MB, data 68 KB block total; content bytes 36,427). | PASS |
| cross-host caveat: TASL-7 metric differs from TASL-2; byte identity is **host-local**; do not compare across hosts | Verified against the accepted TASL-2 record and captures: TASL-2 `val_return` 8.703125 / sealed 8.703125, `run.log` `8d85dad1e13ab0f667e43c242bdf41aee19619043d4df0c6ab6a6bdb090207b8` (26,543 B), channel `9b08312199b96cafcfb171663a2a2271d3d59427cc96bee96435195e084eae14` (59 B), host Intel i9-14900KF; TASL-7 is 7.710938 / 7.4375 with different hashes; same kit HEAD, env freeze and data manifest. The record states the caveat in the header, §6 and §7 and says not to compare across hosts — correct and prominent. The causal sentence is over-stated relative to the record's own "cause not investigated" (m6). | PASS (wording m6) |
| no overclaim of a census measurement / of hardware health | The record is ENGINEERING_ONLY: baseline runs only, no B1↔B2, no census measurement, no hardware-health verdict; §10 lists the limits (3 repeats not a long-run proof; no privileged MCE/dmesg read; shared host; CPU-only; cross-host cause not investigated); §11 lists follow-ups rather than claims. | PASS (wording m5/m6) |

## 2. Findings

### BLOCKING

None.

### MAJOR

None.

### MINOR

- **m1 — the record and captures are not yet in the ops worktree the record names.** The reviewed record and its
  282-file capture bundle live (untracked) only in the sibling main checkout (`agent_paper_B`, branch
  `exam-x-20261026`, HEAD `8a819f75`); at review time
  `docs/r1/reports/tasl_chain_20261122/TASL7_CPU_STABILITY_20261126.md` and its
  `captures/tasl7_cpu_stability_20261126/` do **not** exist in `ops-tasl-20261116` (worktree HEAD `9253192f`),
  although record §8 says the record+captures are "in the Mac ops worktree" and §9 labels the bundle "ops-worktree
  captures". This is a location/housekeeping defect, not a content defect: the reviewed bytes are the correct
  `04153a57…` bytes and the bundle is byte-identical to the preserved host set (`0dcfdea7…`, verified both ends).
  **Fix before commit/citation:** place the record and the 282-file bundle in the ops worktree at the stated paths,
  or correct the location wording. No re-run or re-hash is implied.
- **m2 — two truncated script hashes in §9 are wrong.** `scripts/host_capture_tasl7.sh` is recorded as
  `2ebd8229…f5e4f5aef7`; the captured/host file is
  `2ebd82291ccd67e45b224fe62501698ae64a1d0c16586d3416650f5be4f5aef7` (the recorded suffix should be `5be4f5aef7`).
  `scripts/verify_setup.sh` is recorded as `9d617471…28c302caa98`; the actual file is
  `9d617471da4af6c18254fa9c2d3a5e86061df78d1ab9d42489748f0c302caa98` (suffix `f0c302caa98`). The other three
  fragments in that row (precheck `8f00ea43…131f5fb49b3654`, postcheck `7df04320…42a91a1f4f1d7c`, collect
  `40a4e0bb…4505f392e5535944`) and the full driver/launcher/validation hashes are exact. No evidence is affected —
  `SHA256SUMS` contains the full hashes and verifies rc 0 both ends — but the two fragments should be corrected so
  the quoted hashes do not send a verifier onto a wrong value.
- **m3 — capture-set/path completeness.** §9 lists `logs/preverify.txt` among the captured evidence, but that file
  is **not in the bundle** (it exists only in the host evidence root; it is a useful pre-launch setup-verification
  log, `PRECHECK_RC=0`, covering interpreter, git, pins, data and env, whose substance is superseded by the per-run
  binding fields). Also, the generator of `host/admin_amd_extra.txt` (the AMD microcode/pstate probe) is not among
  the seven captured scripts — `host_capture_tasl7.sh` does not produce that file — although the file's claims are
  independently corroborated (see §1.2). Either capture these two artefacts or correct §9. Two unhashed symlinks in
  the validation run tree (data links) are expected; they are not evidence content.
- **m4 — stale docstring in the captured driver.** `scripts/run_baseline_stability.py` says in its module docstring
  "the launcher runs 4 groups x 3 repeats sequentially"; the launcher, the captures and the record run **6 × 3**.
  Cosmetic only (the record is correct), but a later reader of the captured script could be misled about the design;
  fix the docstring when the driver is committed.
- **m5 — microcode provenance is stated as a conclusion where it is an inference.** §2 says the loaded `0xa601203`
  "→ … comes from BIOS/UEFI". The observable fact is that the five installed `/lib/firmware/amd-ucode` blobs do not
  contain the loaded patch id (byte-scan; my independent LE/BE scan: 0 occurrences), and the record appropriately
  says the exact firmware image and "newest" status are not established. Suggested wording: "not from the installed
  distro package; most consistent with a pre-OS/BIOS load (the exact firmware image was not observable read-only)."
- **m6 — the cross-host causal sentence over-reads the evidence.** §6 says the metric "difference is host/CPU-
  dependent numerics … the 2M-step RL baseline is chaotically sensitive to floating-point rounding, **not** a
  determinism failure", and then closes "The cross-host cause is not investigated here (no claim beyond the
  observation)". The observation (TASL-7 7.710938/7.4375 vs TASL-2 8.703125/8.703125 with the same kit/env/data;
  byte identity is host-local; do not compare across hosts) is verified and important; the causal sentence should
  be phrased as a hypothesis ("consistent with host-dependent numerics/sensitivity") to match the caveat and the
  "no overclaim" requirement.
- **m7 — validation-run time base is unlabelled.** §2 quotes the validation run as "8.577 s", which is
  `run.elapsed_seconds_info_only`; the result's `wall_seconds` is 8.812 s, and the §6 table uses wall seconds.
  Label the time base (or use wall) so a reader comparing the numbers does not see an apparent inconsistency.

### Observations (no action required)

- Author-reported process facts that are not captured and were not independently verifiable: the copy window
  `2026-11-26T06:52:19Z → 07:06:55Z` and durations (kit+data 110 s, venv 761.6 s), "TASL-7 initially had no
  `/home/dowling/r1_trackg_20261125/` at all", "TASL-2 was opened read-only (tar stream) and is unaltered", the GPU
  state "2,210 MiB / 2 % about 16 min earlier", and the "3.3 MB" bundle size (regular-file bytes are 2.74 MB;
  block-rounded `du` 3.4 MB — the record's figure is consistent with a block-rounded size, not a byte count). None
  affects the stability verdict: the copy end state is established by the verified kit HEAD, env freeze, data
  manifest, pins and per-run binding, which are the substantive copy evidence.
- `dmesg_rc=0` printed next to "Operation not permitted" in `host/admin_readonly_probe.txt` is a pipeline artifact
  (the rc of the trailing `head`), not a successful dmesg; the record relies on the message, not the rc.
- No aborted launcher invocation (unlike the TASL-2 check's self-match stop): `launch_console.log` has one launcher
  start at `07:07:52Z`, no `STOP`/`SKIP`/`WARNING`, 18 `=== RUN i/18` / `=== DONE i/18` pairs; the idle guard works
  as written. `summary.json`'s `utc_last_end` is correct this time (`07:23:08Z`), unlike the TASL-2 capture bug.
- Two unhashed symlinks in the validation run tree point at the read-only data snapshot
  (`…/data/mlgym_metamaze`); they are capture-layout symlinks, not evidence content.
- The frozen-file count in the isolation records is 19 while the recomputed node pin has 18 entries; this is the
  kit's isolation accounting (frozen-file check count versus the 18-entry node pin), identical in the accepted
  TASL-2 runs (19 frozen files checked, `changed []` there too), and no change is reported in any run here.

## 3. Recommendation for G.5 TASL-7 audits

1. **Use the TASL-7 host-local reference from this record.** The reference is the single reviewed baseline
   `s000_baseline` at the full 2,000,000-step budget, seeds 8001/8001, 64 envs (executed 2,000,064 env steps):
   `val_return` **7.710938**, sealed `test_return` **7.4375**, `run.log` sha256
   **`f3d6e3a844d0525e1d18643d87467cff942d21911c7941d20ee9e2b0a7fee720`** (26,561 B), result channel sha256
   **`b60323b4a4710f396cc8464c03227471b2eca835357765d33c8c28ba2852427d`** (59 B). All six 4-CPU groups are valid
   audit groups: 18/18 runs, including the SMT-sibling groups, are bitwise identical.
2. **Do not use TASL-2's 8.703125 / 8.703125 or its hashes (`8d85dad1…` / `9b08312…`) as a TASL-7 reference.**
   Treat cross-host metric equality as not expected; compare a TASL-7 audit only against the TASL-7 reference above.
   The same kit/env/data still produce a different host-local trajectory on TASL-7 — that is the observed fact the
   record is built around.
3. **Re-assert the binding before using an audit result.** Kit HEAD `aa354485bff6b5746c48ddadcb50d92e9c6f3645` on
   `mac-trackg-mountaincar-20261125` (clean except the data symlink); env freeze
   `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9` (jax/jaxlib 0.4.35 CPU, torch absent); data
   manifest `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000` (9 files, 0444/0555); committed pin
   `759d6bf0…`, deployed pin `1eaaeac3…`, node spec `d97bb182…`, spec raw `d46dee59…`, edits manifest `6de5741f…`,
   `ar_isolated.py` `37d99ab0…`. Any binding change invalidates the byte reference and needs a new baseline.
4. **Check host drift first if an audit does not reproduce the reference.** TASL-7 host state that must hold:
   microcode `0xa601203` uniform on all 24 CPUs; `amd-pstate-epp` active with `powersave` / `balance_performance`;
   identical `cpuinfo_max_freq` 5,733,000 kHz on all 24 CPUs; same boot (2026-11-17 14:53, no reboot) and same
   host/BIOS (Alienware Aurora R15 AMD, BIOS 1.10.1 2023-12-21). Record the CPU group used. A future audit that
   misses these hashes but matches the binding is still a real divergence to investigate, not noise.
5. **Treat any mismatch as a stop/investigate, not an averaging problem.** Order of checks: binding hashes and git
   state, host state/CPU group, then kit/CPU. Keep the audit sequential and pinned to the audit group (one run at a
   time, no concurrent kit runs), in its own delegated 8 GB/swap-0 scope with `CUDA_VISIBLE_DEVICES=""`, so the
   comparison stays apples-to-apples. Do not rerun until it matches.
6. **Three repeats per group is a stress, not a long-run proof** (the record says so in §10). For G.5, this record is
   sufficient to fix the TASL-7 reference and to show all six groups are usable; it is not a long-duration stability
   claim and not a hardware-health verdict.
7. **Optional follow-ups (not needed for the stability verdict, outside this read-only check):** a privileged
   `dmesg`/journal/MCE review since the 2026-11-17 boot, and a firmware/microcode provenance check (BIOS 1.10.1 vs
   loaded `0xa601203`) — the record lists both in §11 and correctly does not claim them. The shared host had another
   user's GPU job active and a load of 2.6–3.9 during the runs; future audits should note the host load, though it
   had no effect on the byte-identical outputs here.

## 4. Limits of this review

- I did not re-run any kit/smoke or reproduce the stress; this review verifies the record against its captures and
  against the live host state read-only within about 5–20 minutes after the check ended (~2026-11-26T07:28–07:42Z),
  not by reproduction. The 18-run design itself is verified from the captured per-run records and the preserved run
  trees.
- The host is shared and its other-user GPU job changed between the post-check capture and my review (PID 1648890,
  5,126 MiB at post-check; new `jiachenl` PIDs at review). The attribution "another user's job, not ours" is
  verified, but my live GPU snapshot is not the same instant as the post-check.
- No privileged kernel-log/MCE access is available to this account, and no hardware-side fault attribution is
  claimed by the record or by this review.
- The microcode statement is limited to "the installed `/lib/firmware/amd-ucode` blobs do not contain the loaded
  patch id (byte-scan, re-performed read-only)"; I did not inspect the initrd contents or the firmware image, so
  the pre-OS source remains an inference (m5).
- Host "no change" is established from matching pre-check captures, post-check state, the same boot, no sudo/caps,
  unchanged kit/env/data state and no leftover scope/process — plus a live re-check; a full syscall-level audit trail
  is not possible read-only.
- The record/captures were read from the main-checkout copy (m1); the bytes are the sha-verified reviewed bytes, and
  the capture bundle verifies identically on the host, so m1 does not affect any finding.
- Transient write: one `/dev/shm/freeze.<pid>` on TASL-7 for the `pip freeze | sha256sum` measurement (removed
  immediately, outside every evidence root); nothing under any evidence root, repo, kit, venv, data or lock directory
  was written; no deletion; no GPU lease; no HTCondor.

## 5. Evidence index for this review

| item | value |
|---|---|
| record | 313 lines / 31,209 B / sha256 `04153a576791e5f54945ada5d7e01afccde4e62b6acbdebceaa6bbb6dd4a45a7` |
| captures | 282 files (281 hashed + `SHA256SUMS`); `SHA256SUMS` 35,798 B / 281 entries / sha256 `0dcfdea70de3e0923eaeb60c33ecacc555da051d5d342821f2ed7b50718e10cd`; local `-c` rc 0, host `-c` rc 0, all 281 hashes equal remote originals; 2 unhashed data symlinks |
| host evidence root | `/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126` — 18 results, 18 run trees (132 files each, one `s000_baseline` each), 1 validation tree, capture set; 43 MB including captures (39 MB pre-capture) |
| stress records | captures: `results/g<group>_r<n>.json` ×18 and `runs/g<group>_r<n>/{run.log,run_record.json,result_channel.txt,determinism_shim.json}` ×18; the host run trees additionally hold `smoke_ledger.jsonl` ×18 and the full per-run work/code trees |
| passing runs | log `f3d6e3a844d0525e1d18643d87467cff942d21911c7941d20ee9e2b0a7fee720` (26,561 B); channel `b60323b4a4710f396cc8464c03227471b2eca835357765d33c8c28ba2852427d` (59 B); `val_return` 7.710938 / sealed 7.4375; steps 2,000,064; 18/18 |
| validation | `validation/validation.json` sha256 `78c610a1ccf05787d70b46ba944348592832243bdae28740ef85109522e5d2fe`; 2,048-step, CPUs 0–3, val 4.21875 / sealed 3.429688, steps 2,112, `VALIDATION_CRASH_OR_FAIL` (expected), excluded |
| host facts | 24 CPUs, Ryzen 9 7900X, family 25 / model 97 / stepping 2; 24 × microcode `0xa601203`; boot 2026-11-17 14:53:05, no reboot; `amd-pstate-epp`, powersave / balance_performance; 5,733,000 kHz max ×24; kernel 6.8.0-149; Ubuntu 22.04.5; BIOS 1.10.1 2023-12-21; no leftover scope/process; GPU held by `jiachenl` job, not ours |
| kit / env / data | kit `aa354485bff6b5746c48ddadcb50d92e9c6f3645` on `mac-trackg-mountaincar-20261125`, status only `?? …/data`; freeze `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9` (56 pkgs, jax/jaxlib 0.4.35, torch absent, python 3.12.16); data manifest `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000` (9 files match, 0444/0555, outside repo) |
| pins (independently recomputed read-only) | committed `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db`; deployed `1eaaeac351280e16295eae0f50212f352b1aa0c4c3d26a410b58bb0c3bf9ecb7`; node spec `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9`; spec raw `d46dee59960f6959587e822c9dd663864006d2b48d7e5a67a2f7022f21cb3c59`; edits `6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2`; `ar_isolated.py` `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610`; budget steps 2,000,000 |
| scripts | driver `c2ed5af60a8e205d394699945d84fefda6b4fe096813fe4a9e5b9240e2e481cf`; launcher `5444865648a3cfe58c3b50713de074846c93e39dd66ddbac11f9567c75b313c8`; host_capture `2ebd82291ccd67e45b224fe62501698ae64a1d0c16586d3416650f5be4f5aef7`; verify `9d617471da4af6c18254fa9c2d3a5e86061df78d1ab9d42489748f0c302caa98`; precheck `8f00ea433294a2a989050f173bbd51119fd5e0d928c72984fd131f5fb49b3654`; postcheck `7df04320e86b9ec566b9059330652a74294048365a8f2ec1dc42a91a1f4f1d7c`; collect `40a4e0bb6e78ab9bf107d09badc7bc861d089e80079105234505f392e5535944` |
| cross-host (TASL-2) | record sha256 `9dca2cf3c72185bcfb28eb9010f3d6287c8bdc1c5078ced08a788b16bca7164b`; captures `SHA256SUMS` sha256 `1a2c80c87eb5b22f28a6585a86f425f891b5cb7c4d7fc879a500b0a2948832df` (104 entries, 105 files, local `-c` rc 0); TASL-2 8.703125 / 8.703125, log `8d85dad1…`, channel `9b08312…`, i9-14900KF |
| no-change attestation | microcode/governor/EPP/boot unchanged; kit HEAD/branch/status unchanged; no kit/env/data file newer than the check start; no leftover scope/process; `gpu0.lock` 0 B 21 Nov untouched; no sudo/caps; no commit/push |
