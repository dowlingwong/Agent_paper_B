# R1-TRACKG-AR-U2-TASL2 host-check review — TASL-2 §3 isolation conditions (21 November 2026)

**Reviewer.** Fresh independent reviewer (`tasl2-hostcheck-reviewer`), delegated by the lead; no involvement in
writing the check, the probes or the unit. Read-only: the only file written is this review. No code/record edit,
no commit/push/delete, no kit or U2/T1 run, no GPU workload, no Ada/TASL-7/HTCondor/deepthought action.
TASL-2 was inspected with read-only `ssh portal_zhixu` commands (`git rev-parse/status/merge-base`, `sha256sum`,
`stat`, file reads, `ps`, `find`, `nvidia-smi` queries); the submitted probes were **not re-run** (that would be a
run). Every claim below is either a recomputation from the delivered bytes or a fresh read of the live host.

**Object under review.** Report
`docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_20261121.md` (369 lines, sha256
`0a1fa3a42dfaa28a2faf3c98fb1f80a7d0d2fc2c2f70447e1f6857c44befed7a`, uncommitted/untracked in
`ops-tasl-20261116`) and its sibling captures
`TASL2_ISOLATION_HOST_CHECK_20261121_captures/` (60 files; `SHA256SUMS` sha256
`0d0b590be35577409e75ec35a9ffb3f7a33d0e3c025eaba1eda4c606d4353f09`, 59 entries). Host evidence root
`/home/dowling/r1_engineering/tasl2_hostcheck_20261121/` — verified live to hold the **same** `SHA256SUMS` sha
and the same 60-file bundle.

**Verdict: ACCEPTED for the autoresearch option-A gate on TASL-2, with conditions C1–C4 (record/gate text only;
no re-run required).** 0 BLOCKING, 1 MAJOR (report-only: the opening/§5.5 coverage claim), 6 MINOR. The seven
host checks the unit ran are real, were run with **no waiver**, and are independently reproducible from the
captures plus the live host. This is **not** a §3 item 7 CUDA-IPC pass (§5 item 5 remains open); it is sufficient
for AR option A because that path uses the CPU `memfd`, not `cuda_share`/`cuda_open` (R1-TRACKG-AR-COND7).

## Authority and inputs

- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (sha256
  `ac3d5cd0abc262efe8d0552770336ef49dc9cd48cd41704c722ed85c08a5473f`, identical at `origin/main`) — §3 host
  conditions and waivers, §5 remaining limits (item 5 CUDA IPC untested), §5.5.
- Accepted isolation core `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` (round-8 review) and the accepted Ada
  host-check fix `5403392e94cb59d732f45d6702fc857531ad8fd5` — review
  `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (sha256
  `c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36`, ACCEPTED with conditions C1–C4, C3
  keeping §3 item 7 BLOCKED/NOT PASS).
- PLAN row `R1-TRACKG-AR-COND7` (option A; present at `origin/main:docs/r1/PLAN.md`). Task authority
  **R1-TRACKG-AR-U2-TASL2** (author-signed, delegated by the lead): HARNESS_ISOLATION §3 host checks on TASL-2
  only, STOP if any fails, do not set up/run the autoresearch kit/U2. The row text is not in the committed
  docs/PLAN at the worktree or `origin/main` (`4aac5209`); see m4.
- Ada precedent: `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md` (sha256
  `6a7005098659e56c103d2f74e76f65979cbf39a1b46e24c3e3e168e38cda97d7`, STOP at §3 condition 6 on bare
  `68cdd1a`, no GPU/CUDA-IPC exercise).

## Independent verification performed

**Fixed tree (host, read-only).** Worktree `/home/dowling/r1_trackp/harness_cond7a_20261121`: HEAD
`73303380197477df971e865440d0ae11135fe1b3`, `## HEAD（非分支）`, clean. `git merge-base --is-ancestor` returns
**yes** for both `68cdd1a…` and `5403392e…`; `origin/mac-trackg-iso-ar-cond7a-20261120` = `7330338`; the recent
history is the COND7 option-A series (`7330338`, `13786d1`, `6f235c4`, `0e0b820`, `448f682`). Base repo
`/home/dowling/r1_trackp/autoresearch_harness` = `897d83c8…` on `trackp-20261026`, clean, and its tree has
**no** `src/autoresearch/trackg` (so the worktree is genuinely the code tree used).

**Captures integrity.** Mac bundle: `shasum -a 256 -c SHA256SUMS` → 59/59 `OK`; `SHA256SUMS` sha exactly
`0d0b590b…`; 60 files. Host bundle: same `SHA256SUMS` sha, `sha256sum -c` rc 0. The host-written
`logs/summarize.log` records the earlier (pre-`README.md`) sums sha `f4f41b6a…`; the delivered
`0d0b590b…` is the final on-host file (`README.md` added 17:35, sums regenerated 17:35:18), so the sequence is
consistent and the report cites the delivered value. `c7_final.json`'s embedded
`sha256sums: {count: 58, file: ""}` is the c7-step snapshot before the final `SHA256SUMS` generation; nothing in
the report depends on it.

**Provenance of the code/scripts that ran.** The four captured unit files are byte-identical to the TASL-2
worktree files: `isolation.py` `1b576b94…`, `runner.py` `41b54939…`, `node_lib/ar_isolated.py` `3ba34c67…`,
`tests/trackg/isolated_fixture.py` `0b7769a5…`. All captured `scripts/probe_*.py`, `run_checks.sh`,
`run_gpu_smoke.sh`, `summarize.py` are byte-identical to `$BASE/scripts/` (the scripts actually run). The two
`scripts/ada_originals/*.py` are byte-identical to the Ada host-check captures
(`dc00cf0f…` / `55b9a2ef…`). The C6 record's `node_hashes.ar_isolated.py` = `3ba34c67…`, i.e. the captured
unit and the record agree.

**Record integrity.** The captured `records/gpu_smoke/` files are byte-identical to the host
`records/gpu_smoke_20261121T013358Z/`: `result_channel.txt` sha `4ffec570…` = the record's
`isolation.result_channel_sha256`, `run.log` sha `8a3df720…` = the record's `log_sha256`. The c5
`isolation` block is byte-identical to the host `records/g0_smoke_20261121T013357Z/run_record.json` `isolation`
block (`waivers {}`, `exceptions []`, `effective true`, …); the host g0 record's `result_channel.txt`
(`4ffec570…`) and `run.log` (`9b7c8df0…`) match its record fields.

**End state re-checked now (22:30-ish CET, ~7.5 h after the check).** No `tasl2_hostcheck`/`probe_*`/fixture
process; no `/sys/fs/cgroup/**hostcheck_*` or `*_20261*`; no `/tmp/g0_userns_*`; `/dev/shm` empty; GPU
`353 MiB` used, `0 %`, `--query-compute-apps` empty; `/home` free `368.6 GiB` (368.7 GiB at check; ordinary
drift); `~/r1_locks/gpu0.lock` free, Track X marker absent. Attempt-1 archive
`/home/dowling/r1_trackp/runs/p3a_operator_20261027` mtime `2026-11-17 15:42:26.390938519 -0800`, size 4096;
`_attempt1_gpu_lease_log.jsonl` mtime `2026-11-17 15:42:35.402938959 -0800`, size 55726 — both unchanged since
before the session. Harness worktree still `7330338`, clean, no new commits.

**No kit/U2 run.** All 11 run records are fixture nodes: `fake_isolated` (4× `g0_smoke`) and
`tasl2_gpu_smoke` (7× `gpu_smoke`); no `autoresearch` path exists under the run root; the harness worktree is
clean. This supports "nothing set up/run from the autoresearch kit" and "no U2/T1 run". The report and captures
are untracked (`??`) in the Mac ops worktree, matching "uncommitted".

## §3 conditions — independent result

| # | Condition | Result | Independent check |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces, real tmpfs | **PASS** | `c1_userns_{venv,syspy}.json`: both interpreters `unshare(0x72020000)` rc 0, errno 0, uid/gid mapped 0, child `pid 1 ppid 0 new_pid_namespace true`, tmpfs `mount rc 0` (`size=16m,uid=1008,gid=1008`) and write `"userns mount ok"`; the `userns_only` control (0x10000000, no map) is refused EPERM as expected. Host sysctls `unprivileged_userns_clone=1`, `apparmor_restrict_unprivileged_userns=0`; euid 1008 |
| C2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `c2_ptrace.json`: `ptrace_scope 1`, `yama_in_lsm true`, parent→child attach ok, same-uid unrelated sibling attach `EPERM` (errno 1); children reaped |
| C3 | delegated cgroup v2 subtree, `memory.max=8589934592`, `swap.max=0`, `cgroup.kill`, unit `RunCgroup` join/kill/remove | **PASS** | `c3_cgroup.json/.txt`: scope `run-ra8dc…scope`, owner uid 1008, `nsdelegate true`, `cgroup.procs` writable, `cgroup.kill` exists/writable; unit `isolation.RunCgroup.create→join a live child→cgroup.kill→remove`: `processes_before [pid]`, `child_returncode -9`, `empty_after true`, `removed true`, `kill_method cgroup.kill` |
| C4 | non-root euid; interpreter `sys.path` hard check for `/usr/bin/python3` and the `trackp-gpu` venv; no home/runs/ancestor entries; no waiver | **PASS** | `c4_interp.json/.txt`: euid/uid 1008; unit `WorkingCopyRunner._sandbox_config` called for both interpreters, `broad_entries []`, `sandbox_config_ok true`; `isolation.worker_sandbox_available` `true` for both. I read `runner.py:429–434`: the hard `RunnerError` rejects entries resolving to `/`, `$HOME`, `runs_root` or an ancestor of either; the uv alias + versioned install are in the sandbox `ro` list (fix B), and this check has **no waiver** |
| C5 | real sandboxed smoke, record `effective:true, waivers {}, exceptions []` | **PASS** | Host `g0_smoke_20261121T013357Z/run_record.json` (isolation block byte-identical in `c5_smoke.json`): `effective true`, `waivers {}`, `exceptions []`, `euid 1008`, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `frozen_files_checked 3`, `parent_traced_by null`, `parent_dumpable_at_accept false`, cgroup `kill.empty_after true`, `removed true`, `outcome ok 1.0`, result channel `4ffec570…`; `frozen_pin_sha256 9ebf8fa1…` present |
| C6 | GPU smoke with the sandbox on | **PASS** (GPU-in-sandbox; **not** CUDA IPC) | `gpu_lease_status.txt`: `flock` exclusive 01:33:58Z–01:34:00Z rc 0, no lease-log write; compute apps empty pre/post; `CUDA_VISIBLE_DEVICES=GPU-4d623e76-…`; worker `pid 1, ppid 0` in new user/mnt/pid ns (`ns_pid pid:[4026533002]`); `tensor_sum 4096.0` (expected), `matmul 16.0`, `memory_allocated_bytes 33556992`, `cuda_available true`, `dev_shm []`, no CUDA error text; `effective true`, `waivers {}`, `exceptions []`, cgroup removed; record/log/result hashes consistent (see above). The smoke **does not** exercise CUDA IPC — §5 item 5 remains open (M1) |
| C7 | end state: GPU/disk, leftovers, worktree/pins, attempt-1 archive untouched | **PASS** (two evidence caveats m1/m2) | `c7_final.json/.txt`: `no_leftovers true`, six buckets empty, GPU identical before/after (`353 MiB`, no compute apps, `0 %`), disk `368.7 GiB`, repo `7330338` clean, attempt-1 archive mtime `2026-11-17 15:42:26 -0800`, Track X marker absent, lease log not written. Re-verified live: see "End state" above |

Supplementary: the unit's `tests/trackg/test_trackg_isolation.py` in a delegated scope ran `27 passed, 1 skipped
in 15.83 s` (`pytest_isolation.json`, `logs/pytest_isolation.log`); the skip is the root-only
`test_unprivileged_end_to_end` (`skipif(not ROOT, reason="needs root to drop to uid 65534 and delegate a
cgroup")`, `test_trackg_isolation.py:506`), as the report says. The §3 `timeout factor 3` row is the unit default
(`ResourceLimits.timeout_factor = 3.0`) and appears unwaived as `"60 (3 x measured 20 s)"` in both final records.

## Explicit requirements checked

- **PASS/FAIL per condition and STOP rule.** The report's §3 table states PASS for C1–C7; `SUMMARY.json` has
  `failed_conditions: []`, `overall PASS`; `SUMMARY.txt` says `FAILED: none`; STOP/GO says no STOP and "had any
  condition failed, … STOP". Clear.
- **No waiver.** Both final records: `waivers {}`, `exceptions []`, `effective true`; no `isolation_waivers` in
  any record; the word "waiver" in the records is only the `isolation.limits` text. Timeout factor 3 unwaived.
- **No kit/U2 run.** Verified (fixture-only records; no `autoresearch` path in the run root).
- **Evidence paths/hashes match.** Yes, with the two text/capture exceptions m1/m2; the delivered
  `SHA256SUMS` sha and all 59 entries verify on both hosts.
- **Fixed tree.** Verified on the host by `merge-base --is-ancestor`: `7330338` contains `68cdd1a` **and**
  `5403392e`; condition C2 records it. A gate that fixes bare `68cdd1a` would be wrong/stale.
- **Lease usage.** Verified: exclusive `flock` on `~/r1_locks/gpu0.lock` for the GPU smoke only
  (01:33:58Z–01:34:00Z, rc 0), no write to `_attempt1_gpu_lease_log.jsonl` (mtime unchanged), attempt-1
  archive untouched, Track X evidence marker absent before/after. Condition C3 records it.
- **No overclaim.** Mostly careful, but M1: the opening "The seven conditions of HARNESS_ISOLATION_20261117.md §3
  were checked" and the C6 row label "(§5.5)" overstate §3 item 7; the body does disclose CUDA IPC untested. The
  report does **not** say the gate expects `7330338`; it raises the bare-`68cdd1a` question conditionally
  (Finding 1) — C2 resolves it.

## Findings

### BLOCKING

None.

### MAJOR

- **M1 (report-only) — C6 is not the §3 item 7 CUDA-IPC test, but the report's top line and C6 label read as if
  all seven §3 items were checked.** `HARNESS_ISOLATION_20261117.md` §3 item 7 is "The GPU smoke, with the
  sandbox on, exercises CUDA IPC across the PID namespace (§5.5)"; the TASL-2 C6 exercises CUDA *device
  allocation/synchronisation* in the sandboxed worker, not CUDA IPC (as its own "Scope of C6 / §5.5" note says).
  The Ada-fix review C3 also says the host-gate record must keep condition 7 BLOCKED/NOT PASS. The body
  disclosure and Finding 4 are correct, and AR option A does not need CUDA IPC, so this does not block
  acceptance **for the option-A gate**; but the opening sentence and the C6 row label must be corrected before
  the report is cited as a host-condition record (C1). No CUDA-IPC node may be started on the strength of it.

### MINOR

- **m1 — C5 evidence reference is wrong.** The §3-table C5 row and the C5 section cite `records/g0_smoke/` and say
  "the record, run.log, result_channel.txt and gpu_report.json … are copied into the captures"; the delivered
  captures contain only `records/gpu_smoke/` (no `records/g0_smoke/`). The g0 `run_record.json`/`run.log`/
  `result_channel.txt` exist only on TASL-2; the c5 `isolation` block is byte-identical in `c5_smoke.json`. Fix
  the text or copy the three g0 files and regenerate `SHA256SUMS` (which changes the cited sha; C2).
- **m2 — argument-1 archive "stat before/after" is only half-captured.** `host.json` has no attempt-1 stat;
  only `c7_final.json` has the after stat. The mtime predates the session by three days, so "untouched" is
  supported, but the report should cite the after stat (and the operator's pre-session value if it is to be
  called "before/after"), or reword.
- **m3 — "no host state modified beyond the run root" omits the lease lock file, and "GPU idle after" is
  slightly strong.** `~/r1_locks/gpu0.lock` mtime moved to `2026-11-20 17:33:58` (the `exec 9>lock` truncating
  open of the documented lease; expected, but should be listed as the one exception outside the run root). The
  C6 post-smoke query at 01:34:00 shows `5 %` utilisation (no compute apps) while the report says "idle before
  and after"; `c7` at 01:34:16 shows `0 %` and no compute apps. Reword to "no compute apps; 0 % at C7".
- **m4 — the authorizing row is not in the record trail.** `R1-TRACKG-AR-U2-TASL2` (and the lead's delegation)
  is not in the committed `docs/r1/PLAN.md` at the worktree HEAD or `origin/main` (`4aac5209`); only the report
  and captures mention it. Record the row/delegation text so the gate is auditable (C3).
- **m5 — README overstates where the no-UUID diagnostic attempt is recorded.** `captures/README.md` says the
  first attempt without the UUID is "recorded … only in this bundle's SUMMARY prose"; `SUMMARY.txt`/`.
  json` contain no such prose. The attempt is in the TASL-2 preliminary records
  `gpu_smoke_20261121T012925Z/013024Z` (divergent, rc 4) and in the report's C6 prose, not in the bundle. Correct
  the README/report.
- **m6 — "480 KiB" is allocated size, not content.** The bundle is 60 files / 344.4 KiB of content
  (`du -sh` 480K on the Mac, 504K on TASL-2); state "60 files" or cite the `du` basis.

## Conditions

- **C1 (report text, before the report is committed or cited as the host-condition record).** Correct the
  opening and C6 row/label to say: the six §3 host checks PASS **plus** the GPU-in-sandbox prerequisite for item
  7; §3 item 7 CUDA IPC is **UNTESTED** and §5 item 5/§5.5 remain open; no node using `cuda_share`/`cuda_open`
  may start on the strength of this report (Ada-fix review C3). State affirmatively (upgrade Finding 1) that the
  gate binds the fixed tree `7330338` — contains accepted core `68cdd1a` and accepted fix `5403392e`, verified on
  TASL-2 by `merge-base --is-ancestor`; bare `68cdd1a` is not a valid gate baseline.
- **C2 (captures/report accuracy).** Fix m1 (or copy the g0 record files and regenerate `SHA256SUMS`, then
  report the new sha and re-verify), and apply the m2/m3/m5/m6 text corrections. No re-run of the checks is
  required.
- **C3 (authorization and lease record).** Record the author-signed `R1-TRACKG-AR-U2-TASL2` row (m4) and the
  lease facts verified here: exclusive `flock` on `~/r1_locks/gpu0.lock` 01:33:58Z–01:34:00Z (rc 0), **no**
  lease-log write, attempt-1 archive and `_attempt1_gpu_lease_log.jsonl` unchanged, Track X marker absent.
- **C4 (gate operating condition for U2/kit smoke).** Every run must use a live delegated cgroup parent
  (`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`, or
  `AR_TEST_CGROUP_PARENT` at a live delegated directory), name the GPU by UUID (`gpu_uuids`/`--gpu-uuid`), and
  keep `shared_dev_shm: false`; otherwise `effective: true` / `exceptions []` is not reproducible. The report
  already states this; the gate carries it.

## Verdict

**ACCEPTED** for the R1-TRACKG-AR-U2-TASL2 purpose: the TASL-2 host conditions are verified with **no waiver**,
on a tree that contains the accepted isolation core **and** the accepted Ada fix, with matching evidence, a
clean end state, and an untouched attempt-1 archive/lease log. The gate is for the **AR option-A** kit smoke/U2
only: CUDA IPC across the PID namespace is not tested and §5.5 remains open; the report must not be cited as a
§3 item 7 pass. Conditions C1–C4 are record/gate/text conditions; none requires re-running the checks.

---

### Reviewer's command record (21/22 Nov 2026, Europe/Berlin)

- Mac: `shasum -a 256 -c SHA256SUMS` in the captures dir (59/59 OK; `SHA256SUMS` sha `0d0b590b…`); report/captures
  sha256; hashes of `scripts/unit_*` and `scripts/ada_originals/*`; comparison with the Ada captures; reads of the
  report, `SUMMARY.*`, `c1–c7` JSON/TXT, `logs/*`, `host.json`, `records/gpu_smoke/*`, all probes,
  `run_checks.sh`, `run_gpu_smoke.sh`; `git status`/`git log`/`git show origin/main:…` in the ops worktree.
- TASL-2 (`ssh -o BatchMode=yes portal_zhixu`, read-only): `git -C … rev-parse HEAD`/`status`/`log`/
  `merge-base --is-ancestor`/`branch -a --contains`/`rev-list --count` for the harness worktree and base repo;
  `sha256sum` of the worktree `isolation.py`/`runner.py`/`node_lib/ar_isolated.py`/`tests/trackg/
  isolated_fixture.py`; `sha256sum -c captures/SHA256SUMS`; `find`/`stat` on captures, run root, records,
  `~/r1_locks`, the attempt-1 archive, the lease log; `ps`, `find /sys/fs/cgroup`, `/tmp`, `/dev/shm`;
  `nvidia-smi` queries (read-only); `python3 -c` field dumps of the g0/gpu records and `c5_smoke.json`; host
  facts (`nproc`, `/proc/meminfo`, `uname -r`, `/etc/os-release`); comparison of `$BASE/scripts/*` with
  `captures/scripts/*`. No probe, test, smoke or kit/U2 job was run; no file was written on any host.
