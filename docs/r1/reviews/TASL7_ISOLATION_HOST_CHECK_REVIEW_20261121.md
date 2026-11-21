# R1-T1-HOST-TASL TASL-7 host-check review — TASL-7 §3 isolation conditions (21 November 2026)

**Reviewer.** Fresh independent reviewer (`tasl7-hostcheck-reviewer`), delegated by the lead; no involvement in
writing the check, the probes, the report or the unit. Read-only: the only file written is this review. No
code/record edit, no commit/push/delete, no autoresearch kit or proposer/T1 run, no GPU workload, no
HTCondor/deepthought action. TASL-7 was inspected with read-only `ssh -o BatchMode=yes tasl7` commands (git
`rev-parse`/`status`/`merge-base`/`worktree list`/`log`/`show --stat`, `sha256sum`, `stat`, file reads, `ps`,
`find`, `nvidia-smi` queries, `df`, and read-only `python -c` field dumps); the submitted probes were **not**
re-run (that would be a run) and no file was created or modified on TASL-7.

**Object under review.** Report
`docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_20261121.md` (453 lines, 32 058 bytes, sha256
`0150c80a480b1e0f6ddc5f5a32ea57fa33947e07ceb2c40efc2ffc072769a209`, untracked/`??` in the Mac ops worktree
`ops-tasl-20261116` at HEAD `ebe03cd5`) and its sibling captures
`TASL7_ISOLATION_HOST_CHECK_20261121_captures/` (86 files; `SHA256SUMS` 85 entries, sha256
`b0897d28ec2500d4d6f1ca510dba25daaad7653d058a871adf3f3e3456c56956`). Host evidence root
`/home/dowling/r1_engineering/tasl7_hostcheck_20261121/` — verified live to hold the **same** `SHA256SUMS` sha
and the same 86-file bundle (`sha256sum -c` 85/85 OK). The first-orchestration evidence
`captures_precheck_run1_20261121T015718Z/` is preserved on the host (84 files); see m6 for the local copy.

**Verdict: ACCEPTED for the AR option-A host-gate purpose on TASL-7, with conditions C1–C4 (report/record text
only; no re-run required).** 0 BLOCKING, 1 MAJOR (report-only, M1), 7 MINOR. All seven checks the unit ran
(C1–C7) are real, were run with **no waiver**, and are reproducible from the delivered bytes plus the live host.
The §3 host checks (items 1–6: userns, ptrace, cgroup, non-root, `sys.path`, effective smoke) **PASS**, and the
GPU-in-the-sandbox prerequisite for item 7 also passes; C6 is a real GPU-in-the-sandbox pass, but it is **not**
§3 item 7: CUDA IPC across the PID namespace was **not exercised** and §5 item 5 remains open. That is sufficient
for AR option A (CPU `memfd`, `shared_dev_shm: false`) but the report's headline "PASS for all seven TASL-7 host
conditions" must be corrected before the report is committed or cited as the host-condition record (C1). No node
using `cuda_share`/`cuda_open` may start on the strength of it.

## Authority and inputs

- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` (sha256
  `ac3d5cd0abc262efe8d0552770336ef49dc9cd48cd41704c722ed85c08a5473f`) — §3 host conditions and waivers, §5
  remaining limits (item 5 "CUDA IPC under the PID namespace is untested").
- Accepted isolation core `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` (round-8 review
  `docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md`, sha256
  `bf8e9618ea3ea6758a2a0bcff22b7bafa5398d367b3079400f7bcbc6f4e635fb`, ACCEPTED) and accepted Ada host-check fix
  `5403392e94cb59d732f45d6702fc857531ad8fd5` — review
  `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (sha256
  `c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36`, ACCEPTED; **condition C3** requires the
  host-gate record to keep condition 7 **BLOCKED / NOT PASS** and says "the §3 gate must not be reported as fully
  passed").
- PLAN rows `R1-TASL7-TRACKP` (TASL-7 dedicated to Track P; GPU lease `flock ~/r1_locks/gpu0.lock` per host) and
  `R1-TRACKG-AR-COND7` (option A: no CUDA IPC in the result path; CPU `memfd`/socket; `shared_dev_shm: false`).
  Task authority **R1-T1-HOST-TASL** (author-signed, delegated by the lead, R1-TRACKG-AR-U2-TASL2 context); this
  id is not in the committed `docs/r1/PLAN.md` — see m7.
- Ada precedent: `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md` (STOP on bare
  `68cdd1a` at defects A/B) and TASL-2 host check/review `TASL2_ISOLATION_HOST_CHECK_20261121.md` /
  `docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md`.

## Independent verification performed

**Fixed tree (host, read-only).** Worktree `/home/dowling/r1_trackp/harness_cond7a_20261121_t7`: HEAD
`73303380197477df971e865440d0ae11135fe1b3`, detached, `git status --porcelain` 0 lines; `git merge-base
--is-ancestor` returns **rc 0** for both `68cdd1ae…` and `5403392e…`; `refs/remotes/origin/mac-trackg-iso-ar-cond7a-20261120`
= `7330338`; the worktree is a linked worktree of base repo `/home/dowling/r1_trackp/autoresearch_harness` =
`897d83c8efa364ec2fdd37288241cc42e01d7274` on `trackp-20261026`, clean, and that base tree has **no**
`src/autoresearch/trackg` (so the worktree is genuinely the code tree used). `git show --stat 5403392e` confirms
the accepted fix ("keep locked bind mount flags; bind the interpreter symlink chain": 3 files changed,
+154/−3, `ar_isolated.py` / `runner.py` / isolation test). The captured unit files are **byte-identical to HEAD**:
`isolation.py 1b576b94…`, `runner.py 41b54939…`, `ar_isolated.py 3ba34c67…`, `isolated_fixture.py 0b7769a5…`;
all 13 captured `scripts/*` are byte-identical to the 13 scripts in the host run root `…/scripts/` that actually
ran.

**Captures integrity.** Mac: `shasum -a 256 -c SHA256SUMS` → 85/85 `OK`; `SHA256SUMS` sha exactly
`b0897d28…`; 86 files, 1.2 MiB. TASL-7: same `SHA256SUMS` sha, 86 files, `sha256sum -c` 85/85 OK. The host run
root `captures/` is therefore the same bundle as the delivered sibling.

**Record integrity.** Captured `records/` copies match the host run records byte-for-byte:
g0 `run_record.json c7689506…`, `run.log 9b7c8df0…`, `result_channel.txt 4ffec570…`; GPU `run_record.json
efe2a5c0…`, `run.log 40e59245…`, `result_channel.txt 4ffec570…`, `gpu_report.json 98f442a9…`. The records'
`result_channel_sha256` = `4ffec570…` and `log_sha256` match those files, and the captured `c5_smoke.json` /
`c6_gpu_smoke.json` `isolation` blocks are value-identical to the records' `isolation` blocks (the GPU record's
`command` and `outcome` also match). `frozen_pin_sha256 9ebf8fa1…` present in both records.

**Provenance.** The unit files in the captures are the fixed tree's files (hashes above); the probes call the
unit's own `WorkingCopyRunner`, `_sandbox_config`, `isolation.worker_sandbox_available` and `isolation.RunCgroup`
rather than shell imitations; the C6 probe replaces only the **editable** `train.py` of a temp copy of the
`isolated_fixture` node (frozen `parent.py`/`worker.py`/`ar_isolated.py` unchanged; record frozen pin matches the
g0 smoke pin).

**End state re-checked live (~02:07–02:17Z, 7–17 min after the check).** No `tasl7_hostcheck`/`probe_*`/
`isolated_fixture`/`ar_sandbox`/`pytest` process; no `*hostcheck*` or `*_20261*` cgroup; no `/tmp/g0_userns_*`;
GPU `44 MiB`, `0 %`, `--query-compute-apps` empty, UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`; worktree still
`7330338` clean; no llama-server/autoresearch process; run root 3.9 MB. Attempt-1 archive root/EVIDENCE/journal
and both lease-log candidates have **exactly** the pre/post stat values of the check (root mtime
`2026-10-27 06:35:30.703943745 -0700`, inode 56889763; EVIDENCE inode 56890010; journal 28 967 B inode 56889764;
`trackp_evidence.log` 76 B mtime `2026-11-18 17:18:00.997157747 -0800` inode 56265500; `gpu_lease_log.jsonl`
58 863 B mtime `2026-11-18 17:17:59.543236151 -0800` inode 56783856). `/dev/shm` holds exactly the 15 pre-existing
objects named in the report (owners root/`jiachenl`, mtimes 17 and 19 November), identical to the
first-orchestration `c7_final.json`. `~/r1_locks/gpu0.lock` is 0 B with mtime `2026-11-20 17:59:38.612690398
-0800` (= UTC `01:59:38Z`, the lease second) — see m3.

**Live host facts.** `kernel.yama.ptrace_scope=1`, `kernel.unprivileged_userns_clone=1`,
`user.max_user_namespaces=255164`, `kernel.apparmor_restrict_unprivileged_userns=0`,
`kernel.unprivileged_bpf_disabled=2`, `kptr_restrict=1`, `dmesg_restrict=1`, `fs.protected_{hardlinks,symlinks}=1`;
LSM `lockdown,capability,landlock,yama,apparmor`; `6.8.0-149-generic`, Ubuntu 22.04.5 LTS. The two interpreters'
live `sys.path` equal the C4 capture: system `/usr/bin/python3` 3.10.12 with only `/usr/...` entries, and
`trackp-gpu` 3.12.15 with `…/uv/python/cpython-3.12.15-linux-x86_64-gnu/…` + the venv `site-packages` (all under
`$HOME` but none is `$HOME`, the runs tree, or an ancestor of either). The user manager is `running`;
`user@1011.service` is owned by `dowling` (755) with `subtree_control` `memory pids` and `app.slice` owned by
`dowling`; the live session scope is root-owned 755 — consistent with the report's "the session scope is not a
writable parent" and with C3/C5/C6 needing a per-command delegated `systemd-run --user --scope`.

## §3 conditions — independent result

| # | Condition | Result | Independent check |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces, real tmpfs | **PASS** | `c1_userns_{venv,syspy}.json`: both interpreters `unshare(0x72020000 = NEWUSER\|NEWNS\|NEWPID\|NEWNET\|NEWCGROUP)` rc 0, errno 0, uid/gid mapped 0, tmpfs mount rc 0 (`size=16384k,uid=1011,gid=1011`) and write `"userns mount ok"`, child `pid 1, ppid 0, new_pid_namespace true`; the `userns_only` control (0x10000000, no map) is refused `EPERM` as expected. Host sysctls as above |
| C2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `c2_ptrace.json`: `ptrace_scope 1`, `yama_in_lsm true`, parent→child attach ok, same-uid unrelated sibling attach `EPERM` (errno 1), children reaped |
| C3 | delegated cgroup v2 subtree, `memory.max=8589934592`, `swap.max=0`, `cgroup.kill`, unit `RunCgroup` | **PASS** | `c3_cgroup.json/.txt`: scope `run-rc56f1…scope`, owner uid 1011, `nsdelegate true`, `cgroup.procs` writable, `cgroup.kill` exists/writable, `memory.max=8589934592`, `memory.swap.max=0`; unit `isolation.RunCgroup.create → join a live child → cgroup.kill → remove`: `processes_before [179677]`, `kill_method cgroup.kill`, `child_returncode -9`, `empty_after true`, `removed true`. Live `user@1011.service` delegation structure present |
| C4 | non-root; interpreter `sys.path` hard check for `/usr/bin/python3` **and** `trackp-gpu`; no home/runs/ancestor entry; no waiver | **PASS** | `c4_interp.json/.txt`: euid 1011 non-root; unit `WorkingCopyRunner._sandbox_config` called for both interpreters, `broad_entries []`, `sandbox_config_ok true`; `isolation.worker_sandbox_available` `true` for both. I read `runner.py:414–435`: the hard `RunnerError` rejects entries resolving to `/`, `$HOME`, `runs_root` or an ancestor of either, with no waiver path; live `sys.path` matches the capture (m1 corrects the report's prose about *which* uv directory) |
| C5 | real sandboxed smoke, record `effective:true, waivers {}, exceptions []` | **PASS** | Host `records/g0_smoke_20261121T015936Z/run_record.json` (captured byte-identically; `c5_smoke.json` isolation block equal): `effective true`, `waivers {}`, `exceptions []`, `limits.isolation_waivers {}`, `timeout_factor 3.0`, `euid 1011`, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `frozen_files_checked 3`, `parent_traced_by null`, `parent_dumpable_at_accept false`, cgroup `kill.empty_after true` / `removed true`, `outcome ok 1.0`, result channel `4ffec570…` (matches the record and the log line) |
| C6 | GPU smoke with the sandbox on (task's C6: UUID, allocate/sync, `effective:true`, no CUDA error) | **PASS** (GPU-in-sandbox; **not** §3 item 7 CUDA IPC — M1) | `c6_gpu_smoke.json` / `records/gpu_smoke_20261121T015938Z/`: `CUDA_VISIBLE_DEVICES=GPU-ab72fb4a-…` (record and env), worker `pid 1, ppid 0` in new user/mnt/pid ns, `tensor_sum 4096.0` (expected), 16×16 matmul 16.0, `memory_allocated_bytes 33556992`, `cuda_available true`, `cuda_initialized true`, `dev_shm []`, no `CUDA error`/`cudaError` text, metric in the result channel, cgroup removed, `effective true`, `waivers {}`, `exceptions []`; `flock` lease 01:59:38Z–01:59:40Z rc 0 with no lease-log write; GPU 44 MiB / 0 % / no compute apps before and after. **No CUDA IPC was exercised** |
| C7 | end state: GPU/disk/leftovers, worktree clean, attempt-1 archive + lease logs untouched, no deletion | **PASS** (wording caveats m2/m3) | `c7_final.json/.txt`: `no_leftovers true`, all five checked buckets empty, `/dev/shm` 15 pre-existing objects; GPU identical before/after (44 MiB, no compute apps, 0 %); repo `7330338` `## HEAD (no branch)`; disk 514.0 GiB; attempt-1 archive content+metadata fingerprint identical (`tree 299237d0…`, `content af7ede86…`, 1040 entries/724 files/11 925 743 308 B) and both lease-log candidates stat-identical; live re-check confirms all of the above and the pre-existing `/dev/shm` state |

Supplementary (not a §3 host condition): the unit's own `tests/trackg/test_trackg_isolation.py` in a delegated
scope ran **27 passed, 1 skipped in 14.89 s** (`pytest_isolation.json`, `logs/pytest_isolation.log`); the skip is
the root-only `test_unprivileged_end_to_end_forgery_through_proc_fails`
(`@pytest.mark.skipif(not ROOT, reason="needs root to drop to uid 65534 and delegate a cgroup")`, line 506). The
§3 `timeout factor 3` row is the unit default (`ResourceLimits.timeout_factor = 3.0` in both records) and is
unwaived.

## Explicit requirements checked

- **PASS/FAIL per condition and STOP rule.** The report's §3 table states PASS for C1–C7; `SUMMARY.json` has
  `failed_conditions: []`, `overall PASS`; `SUMMARY.txt` says `FAILED: none`; STOP/GO says no STOP. Clear, subject
  to M1 (the item-7 scope of the word "all seven").
- **No waiver.** Both final records: `waivers {}`, `exceptions []`, `effective true`; `limits.isolation_waivers
  {}`; timeout factor 3 unwaived. No `isolation_waivers` entry anywhere.
- **No kit/proposer run.** Run root `records/` holds only the four fixture run dirs (two `g0_smoke`, two
  `gpu_smoke`, the two first-orchestration copies included); `work/` holds only fixture node copies + `precheck`;
  no `autoresearch` path, no server log, no llama-server process. The report's "the proposer llama-server was not
  started" is supported by absence, not by a positive capture.
- **Evidence paths/hashes match.** Yes: report sha above; captures 85/85 verify on both hosts with the cited sha;
  records match their captures; the host evidence root is the same bundle. m6 covers the local first-run copy.
- **Fixed tree.** Verified: `7330338` contains `68cdd1a` **and** `5403392e` (`merge-base --is-ancestor` rc 0 for
  both), unit-file hashes match, base repo as claimed. A gate that fixes the baseline at bare `68cdd1a` would be
  stale/wrong: on bare `68cdd1a` the Ada defect A/B checks fail, so the TASL-7 C4/C5/C6 results are only
  meaningful for the fixed tree (report Finding 1 says this conditionally; C1 upgrades it to affirmative).
- **Lease usage / paused Track P.** Verified: exclusive `flock` on `~/r1_locks/gpu0.lock` 01:59:38Z–01:59:40Z
  (rc 0), no lease-log write (both candidates stat-identical before/after/now), attempt-1 archive
  content-identical, Track X evidence marker absent, no compute apps at either sample; `gpu0.lock` mtime moved
  to the lease second (m3).
- **No overclaim.** Mostly careful body, but M1: the status line/§3-table and the C6 row label "(§5.5)" overstate
  §3 item 7; the body correctly discloses that CUDA IPC is untested. The report does **not** say the gate expects
  `7330338`; Finding 1 raises the bare-`68cdd1a` question conditionally — C1 resolves it affirmatively.
- **No deletion / first-run preservation.** The host `captures_precheck_run1_…` is preserved (84 files); the
  local sibling is partial and does not verify (m6). No evidence of deletion of pre-existing host work.

## Findings

### BLOCKING

None.

### MAJOR

- **M1 (report-only) — "PASS for all seven TASL-7 host conditions" is not the §3 item-7 result; C6 is a
  GPU-in-sandbox pass, not a CUDA-IPC pass.** `HARNESS_ISOLATION_20261117.md` §3 item 7 is "The GPU smoke, with
  the sandbox on, exercises CUDA IPC across the PID namespace (§5.5)", and the accepted fix review's condition
  C3 says "the host-gate record must keep condition 7 as BLOCKED / NOT PASS … the §3 gate must not be reported as
  fully passed". This check exercises CUDA *device allocation/synchronisation* in the sandboxed worker (C6), not
  CUDA IPC; the body says so ("Scope of C6 / §5.5", Finding 4) and §5 item 5 remains open. The status line, the
  C6 row label "(§5.5)" and the STOP/GO sentence "No §3 condition failed … the host-condition gate for TASL-7 is
  PASS" must be corrected (C1). This does not block acceptance for AR option A (CPU `memfd`,
  `shared_dev_shm: false`), which the check does support; no `cuda_share`/`cuda_open` node may start on the
  strength of the report.

### MINOR

- **m1 — the uv-alias sentence is wrong for TASL-7.** Report lines 51–54 and 224–229 say "the venv `sys.path`
  holds the uv alias directory `/home/dowling/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu`" and that
  this alias "in `sys.path` is exactly the path that broke the Ada check". The captured and live `sys.path` holds
  the **versioned** installation `…/cpython-3.12.15-linux-x86_64-gnu`; the unversioned alias
  `…/cpython-3.12-linux-x86_64-gnu` is a separate symlink that is neither in `sys.path` nor on this venv's
  interpreter chain (`venv/bin/python → …/cpython-3.12.15-…/bin/python3.12`). Ada defect B was the *symlink-chain
  bind*, not a `sys.path` entry. C4's `broad_entries=[]`, `sandbox_config_ok`, `sandbox_available` results are
  unaffected; correct the two sentences (say "the versioned uv installation under $HOME").
- **m2 — "attempt-1 archive + lease logs byte-identical pre/post" is content-proved for the archive only.** The
  `tree_sha256`/`content_sha256` fingerprint covers `/home/dowling/r1_trackp/runs/p3a_operator_20261027` (724
  files, 11.9 GB); the two lease-log candidates are compared by `stat` only (mtime/ctime/size/inode/owner/mode),
  which is strong (ctime unchanged since 18 Nov, so no write/rename) but is not a content hash. Reword to
  "archive content-identical; lease logs metadata-identical", or add the two small content hashes in a future
  check. The "nothing was written" conclusion stands.
- **m3 — "no host state modified beyond the new run root" is imprecise.** Findings 6 and Deviation 4 ("Only the
  new run root … was created") omit: (a) the new harness worktree
  `/home/dowling/r1_trackp/harness_cond7a_20261121_t7` and the fetched
  `refs/remotes/origin/mac-trackg-iso-ar-cond7a-20261120` (both disclosed elsewhere in the report); (b)
  `~/r1_locks/gpu0.lock` mtime `2026-11-20 17:59:38 -0800` from the `exec 9>` flock open (a pre-existing path).
  List these as the exceptions to the run-root statement. (The first-run capture set is preserved in
  `captures_precheck_…`, and the first-run `records/`/`work/` dirs remain in place — the rotation is not a
  deletion — but say "capture set", not only "capture directory".)
- **m4 — "no compute apps before, during or after" oversamples.** Only a pre-lease sample and post-smoke samples
  exist (`gpu_compute_apps_{pre,post}_gpu_smoke.txt`, both empty); nothing samples "during". Say "no compute apps
  before or after (and none other at either sample)".
- **m5 — "the sandboxed worker's own `/dev/shm` was empty in both smokes (`gpu_report.dev_shm: []`)" is
  evidenced for the GPU smoke only.** The g0 smoke has no worker-side `/dev/shm` listing; what is proven for both
  is that the host `/dev/shm` after both runs holds only the 15 pre-existing objects (c7). Reword.
- **m6 — the local first-orchestration "preserved" copy is partial and does not verify; README misplaces it.**
  Host `captures_precheck_run1_20261121T015718Z/` is preserved (84 files; its `SHA256SUMS`, sha
  `299abd46…`, verifies 82/83 with the known `logs/summarize.log` sums-ordering mismatch). The Mac sibling
  `TASL7_ISOLATION_HOST_CHECK_20261121_run1_precheck_20261121T015718Z/` has only 81 files: 3 files listed in its
  `SHA256SUMS` are absent (`attempt1_before.tree.sha256`, `c2_ptrace.json`,
  `gpu_compute_apps_post_gpu_smoke.txt`) and `logs/summarize.log` fails its hash (79/83 OK). Deviation 1's
  "preserved … locally as the sibling" and `captures/README.md`'s "in this bundle under
  `run1_precheck_20261121T015718Z/`" should say the host copy is the authoritative preserved first run and the
  local sibling is partial (it is a sibling directory, not inside the captures bundle). The first-run
  `attempt1_compare.json` does corroborate the reported comparison-script bug (empty stat/nentries/nfiles/bytes,
  hashes identical).
- **m7 — authority trail.** `R1-T1-HOST-TASL` is not in the committed `docs/r1/PLAN.md` (the repo has
  `R1-TASL7-TRACKP` and `R1-TRACKG-AR-COND7` but no `R1-T1-HOST-TASL`); only this report and its captures mention
  it. Record the author-signed/delegated text (or its packet reference) in the record trail for auditability
  (same class as TASL-2 review m4/C3). Also, the report's "TASL-2 … HTCondor/deepthought … were not touched"
  claims are not independently verifiable from TASL-7; I found no contrary evidence on TASL-7.

## Conditions

- **C1 (report text, before the report is committed or cited as the host-condition record).** Correct the
  opening/status, the C6 row/label and the STOP/GO text to say: the six §3 host checks (items 1–6) **PASS** plus
  the GPU-in-sandbox prerequisite for item 7; §3 **item 7 (CUDA IPC across the PID namespace) is
  UNTESTED / NOT PASS**, and §5 item 5 remains open; no node using `cuda_share`/`cuda_open` may start on the
  strength of this report. State affirmatively (upgrade Finding 1) that the gate binds the fixed tree
  `7330338` — contains the accepted core `68cdd1a` and the accepted fix `5403392e`, verified on TASL-7 by
  `merge-base --is-ancestor` rc 0; bare `68cdd1a` is not a valid baseline (it fails Ada defects A/B).
- **C2 (report/captures accuracy).** Apply the m1–m6 text corrections (uv-alias wording; lease-log
  metadata-vs-content wording; host-state exceptions incl. the worktree/ref and `gpu0.lock` mtime; "during"
  compute-apps wording; g0 `/dev/shm` wording; local precheck sibling and README placement). No re-run of the
  checks is required.
- **C3 (authorization and lease record).** Record the author-signed `R1-T1-HOST-TASL` / delegated scope text
  (m7) and the lease/state facts verified here: exclusive `flock` on `~/r1_locks/gpu0.lock`
  `01:59:38Z–01:59:40Z` rc 0; **no** write to either lease-log candidate (both stat-identical before, after and
  now); attempt-1 archive content-identical (`tree 299237d0…`, `content af7ede86…`, 1040 entries / 724 files /
  11 925 743 308 B); Track X marker absent; `gpu0.lock` mtime as the one pre-existing-path metadata change.
- **C4 (gate operating condition for the proposer/kit smoke).** Every run must use a live delegated cgroup
  parent (`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`, or
  `AR_TEST_CGROUP_PARENT` at a live delegated directory), name the GPU by UUID (`gpu_uuids`/`--gpu-uuid`), keep
  `shared_dev_shm: false`, and not require CUDA IPC; keep the documented `flock` lease plus the
  no-compute-apps preflight. C6 is **not** evidence for `cuda_share`/`cuda_open`/CUDA IPC.

## Verdict

**ACCEPTED** for the R1-T1-HOST-TASL / R1-TRACKG-AR-U2-TASL2 **AR option-A** host-gate purpose on TASL-7: the
host conditions are verified with **no waiver**, on a tree that contains the accepted isolation core **and** the
accepted Ada fix, with a complete and hash-verified evidence bundle whose records match the live host, a clean end
state, and an attempt-1 archive/lease log provably untouched. This is **not** a §3 item 7 CUDA-IPC pass; §5
item 5 remains open, and the report must not be cited as a full §3 pass until C1 is applied. Conditions C1–C4 are
report/record/gate-text conditions; none requires re-running the check.

---

### Reviewer's command record (21 November 2026, Europe/Berlin; 02:0x–02:2xZ)

- Mac (`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`): `shasum -a 256 -c
  SHA256SUMS` in the captures dir (85/85 OK; `SHA256SUMS` sha `b0897d28…`); report sha256/line/byte counts;
  hashes of `scripts/unit_*` and all captured `scripts/*`; reads of the report, `SUMMARY.*`, `README.md`,
  `c1–c7` JSON/TXT, `host.json`/`host_facts.txt`, `attempt1_*`, `records/{g0,gpu}_smoke/*`, all logs, the probes,
  `run_checks.sh`, `run_gpu_smoke.sh`, `summarize.py`, `fingerprint_attempt1.sh`, `compare_attempt1.py`;
  comparison with the first-run precheck sibling and its `SHA256SUMS` verification; `git status`/`git log` in
  the ops worktree; grep of `docs/r1/PLAN.md` and the review/report trail.
- TASL-7 (`ssh -o BatchMode=yes tasl7`, read-only): `sha256sum`/`find` on `captures`, `captures_precheck_*`,
  run root, `records`, `scripts`; `sha256sum -c captures/SHA256SUMS`; `git -C` harness worktree
  `rev-parse`/`status`/`log`/`merge-base --is-ancestor`/`show --stat`/`worktree list`/`for-each-ref`; base repo
  `rev-parse`/`branch`/`status`/`ls-tree`; `stat` of the attempt-1 archive/EVIDENCE/journal, both lease logs and
  `gpu0.lock`; `sha256sum` of the lease logs; `/dev/shm` listing; `ps`, `find /sys/fs/cgroup`, `/tmp` leftovers;
  `nvidia-smi` queries; `df`; `uname`/`/etc/os-release`/`/proc/sys` reads; `systemctl --user is-system-running`;
  `user@1011.service`/`session-*.scope` stat and `cgroup.subtree_control`; read-only `python -c` field dumps of
  `sys.path` and of the captured records/captures. No probe, test, smoke, kit or proposer job was run; no file
  was written on TASL-7.
