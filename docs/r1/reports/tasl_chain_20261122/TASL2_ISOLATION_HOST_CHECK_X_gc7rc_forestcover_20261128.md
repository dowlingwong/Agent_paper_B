# TASL-2 host check at G.5 harness pin `3f7b09fe` for expansion node `gc7rc_forestcover` (28 November 2026)

**Status: PASS — host-check record for the G.5 expansion addendum.** ENGINEERING_ONLY.
This file is the TASL-2 host-check record the addendum's `host_check` gate reads for `gc7rc_forestcover`; the
coordinator publishes it and Local fills the note's gate as `host check <record> sha256 <its sha256>`.

host_check_host: TASL-2
host_check_harness_commit: 3f7b09febf401a83f3aa881f00eecdd032024416
host_check_items: 1-7 PASS
host_check_verdict: PASS

## What this binds

The seven host conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` section 3 — C1 unprivileged
user/mount/PID/network/cgroup namespaces, C2 Yama `ptrace_scope >= 1`, C3 a delegated cgroup v2 subtree with
`cgroup.kill` (8G / swap 0), C4 non-root and the interpreter `sys.path` hard check, C5 a real sandboxed smoke with
`effective: true`, C6 a GPU smoke with the sandbox on (full UUID, under the exclusive lease), C7 end state — were
checked on TASL-2 at the reviewed exact G.5 harness commit `3f7b09fe…` for `gc7rc_forestcover`, on its G.1b CPU
set 4-7 and its `torch312` environment. All seven passed with no waiver. The node's earlier record covers the G.1b
kit pin `85851664`; this record is the exact G.5 pin the addendum needs.

- Task `compute/20261128-20`; source Local handoff `reports/20261128-14-g5-forestcover-isolation-handoff.md` on
  `coord/local` (`f9193360`), reconciliation `reports/20261128-local-round-forestcover-reconcile.md` (`a3994698`);
  harness review `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md`, verdict ACCEPTED for engineering
  isolation, review SHA-256 `4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- Paper test base `57e6d1ed5945ab48684e24e145b69d333b4f77d4`; round base `origin/main` `7cd65cfa`; queue
  `coord/coordinator` `52fb6892`.
- Harness repository `https://github.com/dowlingwong/autoresearch_harness`, separate clone
  `/home/dowling/r1_tracks/t1_tasl_x/harness_repo`; detached worktree
  `/home/dowling/r1_tracks/t1_tasl_x/harness_forestcover_g5`, HEAD
  `3f7b09febf401a83f3aa881f00eecdd032024416`, tracked-clean. The candidate is one commit above its signed census
  kit `85851664679d10889c5af406843c4a3fc38f7a49`; it adds `src/autoresearch/trackg/audit_g5.py`
  (sha256 `5f384204c34e297191281bb3981db57607d58333222adab6def97e8d099e2690`) and updates
  `src/autoresearch/trackg/campaign_v2_diff.py` (sha256
  `9d4f8e6838c31ebec835fd13434532b8afb8539e3cdd913188e52300d0c0a708`); both hashes equal the reviewed pair in
  `G5_EXPANSION_HARNESS_REVIEW_20261128.md`, and `git diff --stat 85851664 HEAD` shows only those two files.
- Run root `/home/dowling/r1_engineering/t1_tasl_x_hostcheck_g5_20261128_forestcover` (`scripts/`, `captures/`,
  `logs/`, `records/`, `work/`). Same reviewed check scripts as the G.1b expansion host check, with the node row
  and checkout path updated to the G.5 commit.
- Host facts: TASL-2, Ubuntu 22.04.5 LTS, Linux 6.8.0-149-generic, i9-14900KF, 32 logical CPUs, microcode `0x133`;
  uid 1008 non-root; GPU `NVIDIA GeForce RTX 4090`, UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver
  535.309.01; `nvidia-smi --query-compute-apps` empty before and after; 353 MiB desktop reservation; GPU lease
  `~/r1_locks/gpu0.lock` free before and after.
- Data: `/home/dowling/r1_tracks/t1_tasl_x/data/gc7rc_forestcover`, manifest sha256
  `2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d`, 2 files (`X.npy`, `y.npy`), both re-hashed
  and matching; the worktree's only untracked file is the expected `nodes/gc7rc_forestcover/data` symlink.

## Steps 1-4 in the same session

| Step | Result | Key evidence |
|---|---|---|
| 1. checkout at the exact pin | **PASS** | separate clone, detached worktree; `git rev-parse HEAD` = `3f7b09fe…`; `git status --porcelain --untracked-files=all` shows only the `data` link; `merge-base --is-ancestor c025f89a HEAD` rc 0 (`step1_checkout.txt`) |
| 2. pins recomputed at the pin | **PASS** | node spec `ff2a585b69b51b51d0649e7f57b4713c650c46a27c981982dbeb2d09badf0beb`; committed pin `78b48db9d36c5c67e55a4cc65495821e39f70b9d5bf01bb35410037e1b017a33`; edits manifest `0219deb80aab3f839d52a186a6bdedca8d754c111cd964566439af457a83b6ed`; spec file `edd1a076aab8b2cc1f45192860b3555a844400c211581888b9edbcc4e5104e02`; node and master `ar_isolated.py` both `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610`; 16 frozen entries (`pins_gc7rc_forestcover.json`) |
| 3. environment | **PASS** | torch312 `uv pip freeze` 77 lines, sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, Python 3.12.16, equal to `sweep2/g1b/env/torch312.freeze.txt` (`env_torch312.json`) |
| 4. data re-hashed at the pin | **PASS** | node data manifest `2b5cfb15…`, 2 files, both re-hashed and matching, symlink present (`datapins_gc7rc_forestcover.json`); interpreter links resolve to the expected uv CPython 3.12.16 (`c7_final.json`, `interpreter_evidence`) |

## C1-C7 at the pin — PASS table

| # | Condition | Result | Key evidence |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces usable by the run uid | **PASS** | rc 0 with the torch312 interpreter (3.12.16) and `/usr/bin/python3` (3.10.12); uid 1008 mapped; real tmpfs mount and write; `condition_1_pass: true` (`c1_userns_env.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope >= 1` | **PASS** | `ptrace_scope=1`; parent→child attach ok; unrelated same-uid sibling attach `EPERM`; `condition_2_pass: true` (`c2_ptrace.json`) |
| C3 | delegated cgroup v2 subtree with `cgroup.kill` (8G / swap 0) | **PASS** | `memory.max=8589934592`, `memory.swap.max=0`, `nsdelegate`, `cgroup.kill` exists, owner uid 1008; create→join→kill→empty→removed (`child_returncode=-9`); `condition_3_pass: true` (`c3_cgroup.json`, `.txt`) |
| C4 | non-root and the interpreter `sys.path` hard check | **PASS** | euid/uid 1008; `broad_entries=[]` and `sandbox_config_ok=True` for both interpreters; `condition_4_pass: true` (`c4_interp.json`, `.txt`) |
| C5 | real sandboxed CPU smoke with `effective: true`, no waivers/exceptions | **PASS** | outcome ok, `isolation.effective=true`, `waivers={}`, `exceptions=[]`, `frozen_files_changed=[]`, cgroup removed, run log intact; `condition_5_pass: true` (`c5_smoke.json`, `records/forestcover_smoke/`) |
| C6 | GPU smoke with the sandbox on, full UUID, under the exclusive lease | **PASS** | interpreter torch312; full UUID `GPU-4d623e76-…`; sandboxed worker (PID 1 of its namespaces) allocated and synchronised a CUDA tensor (`cuda_available=true`, `device_count=1`, tensor sum 4096.0 correct, matmul 16.0, torch 2.6.0+cu124, CUDA 12.4), metric written, no CUDA error; lease `~/r1_locks/gpu0.lock`, 17:37:33–17:37:35Z; no compute app before or after; `condition_6_pass: true` (`c6_gpu_smoke.json`, `c6_gpu_lease_status.txt`, `records/forestcover_gpu_smoke/`) |
| C7 | end state: GPU idle and unleased, no leftovers, disk, checkouts | **PASS** | GPU identical before/after (353 MiB, no compute apps, 0 %); lease free; all six leftover buckets empty; 333.8 GiB free; worktree still at the pin with only the `data` link untracked; seven-node checkout still at `c025f89a…`; Track P harness `897d83c8…` tracked-clean (`c7_final.json`, `.txt`, `checkout_end.txt`) |

Supplementary, not a section-3 condition: the pin's `tests/trackg/test_trackg_isolation.py` in a delegated 8G /
swap-0 scope with torch312: **27 passed, 1 skipped** in 14.11 s (the skip is the root-only test);
`pytest_isolation.json`.

## CPU pinning and the discarded first attempt

Attempt 1 (session stamp `20261128T173529Z`) is kept in the run root as
`captures_attempt1_20261128T173529Z/` and is **not** evidence: the copied `phase3_checks.sh` still pinned the
session-wide C2 probe to 16-31, and its supplementary pytest and the C6 GPU smoke ran inside their scopes without
`taskset`. Before attempt 2 the script was corrected so C2 and the pytest use the node's set 4-7, and
`run_gpu_smoke.sh` wraps the sandboxed probe in `taskset -c 4-7`. Attempt 2 (`20261128T173716Z`) is the evidence
session. Every catch in this record is from attempt 2; attempt 1 changed no value and produced no STOP.

In attempt 2 every C1-C6 step and every step-1-4 capture is `taskset -c 4-7`; no CPUs 8-11 were used. The host was
idle (load average 0.22 at session start), no other job held the four CPUs or the card, and no G.1b/G.5/G.4 chunk
ran. No label, test or evaluation value was read. No deletion, commit or push was made on the host.

## Captures

Capture set `TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261128_captures/` — 35 files + `SHA256SUMS`; `SHA256SUMS`
sha256 **`95fb1af5f2d0aef4633a872cffde35dd9a5bea14796e930dadfe71096285e736`**; `sha256sum -c` rc 0 on TASL-2 and
`shasum -a 256 -c` rc 0 after fetch. It binds `checkout_end.txt`, `step1_checkout.txt`, `commands.txt`,
`host_facts.json/.txt`, `pins_gc7rc_forestcover.json/.txt`, `datapins_gc7rc_forestcover.json/.txt`,
`env_torch312.json/.txt`, `torch312.freeze.txt`, `c1`–`c7`, `pytest_isolation.json`, and `records/`.

## What happens next

1. Fresh independent review of this record and captures.
2. Coordinator publishes the record; Local fills the `gc7rc_forestcover` addendum gate and runs the draft checks.
3. This closes the fourth and last expansion addendum host check (Titanic, MetaMaze and ETTh1 already PASS).
   Campaigns still wait on the G.5 launch decision; no compute job ID is associated with this check.

Decided alone: to reuse the prepared Forest Cover run root and the reviewed check scripts, to keep the same
phase3 matrix, to correct the C2/pytest/GPU-smoke CPU pinning and rerun the session rather than publish a check
whose pinning did not match the node's set, and to keep attempt 1 in the run root for the record. No signed value,
code, spec or note was changed.

**AI-assisted: DeepSeek compute agent, 28 Nov 2026. ENGINEERING_ONLY.**
