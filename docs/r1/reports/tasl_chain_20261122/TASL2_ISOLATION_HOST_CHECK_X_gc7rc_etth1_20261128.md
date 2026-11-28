# TASL-2 host check at G.5 harness pin `6fc553df` for expansion node `gc7rc_etth1` (28 November 2026)

**Status: PASS — host-check record for the G.5 expansion addendum.** ENGINEERING_ONLY.
This file is the TASL-2 host-check record the addendum's `host_check` gate reads for `gc7rc_etth1`; the coordinator
publishes it and Local fills the note's gate as `host check <record> sha256 <its sha256>`.

host_check_host: TASL-2
host_check_harness_commit: 6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c
host_check_items: 1-7 PASS
host_check_verdict: PASS

## What this binds

The seven host conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` section 3 — C1 unprivileged
user/mount/PID/network/cgroup namespaces, C2 Yama `ptrace_scope >= 1`, C3 a delegated cgroup v2 subtree with
`cgroup.kill` (8G / swap 0), C4 non-root and the interpreter `sys.path` hard check, C5 a real sandboxed smoke with
`effective: true`, C6 a GPU smoke with the sandbox on (full UUID, under the exclusive lease), C7 end state — were
checked on TASL-2 at the reviewed exact G.5 harness commit `6fc553df…` for `gc7rc_etth1`, on its G.1b CPU set
16-31 and its `torch312` environment. All seven passed with no waiver. The node's earlier record covers the G.1b kit
pin `3a06d867`; this record is the exact G.5 pin the addendum needs.

- Task `compute/20261128-20`; source `local/20261128-14-g5-etth1-isolation-handoff` (`coord/local` `150212b1`;
  harness review `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md`, verdict ACCEPTED for engineering
  isolation, review SHA-256 `4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`).
- Paper test base `57e6d1ed5945ab48684e24e145b69d333b4f77d4`; round base `origin/main` `9b044b59`; queue
  `coord/coordinator` `d47cab43`.
- Harness repository `https://github.com/dowlingwong/autoresearch_harness`, separate clone
  `/home/dowling/r1_tracks/t1_tasl_x/harness_repo`; detached worktree
  `/home/dowling/r1_tracks/t1_tasl_x/harness_etth1_g5`, HEAD
  `6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c`, tracked-clean. The candidate changes only
  `campaign_v2_diff.py` and `audit_g5.py` from the node's kit; its six checked engine files are byte-identical to
  signed G5-7 `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98`.
- Run root `/home/dowling/r1_engineering/t1_tasl_x_hostcheck_g5_20261128_etth1` (`scripts/`, `captures/`,
  `logs/`, `records/`, `work/`). Same reviewed check scripts as the G.1b expansion host check, with the node row
  and checkout path updated to the G.5 commit.
- Host facts: TASL-2, Ubuntu 22.04.5 LTS, Linux 6.8.0-149-generic, i9-14900KF, 32 logical CPUs, microcode `0x133`;
  uid 1008 non-root; GPU `NVIDIA GeForce RTX 4090`, UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver
  535.309.01; `nvidia-smi --query-compute-apps` empty before and after; 353 MiB desktop reservation; GPU lease
  `~/r1_locks/gpu0.lock` free before and after.
- Data: `/home/dowling/r1_tracks/t1_tasl_x/data/gc7rc_etth1`, manifest sha256
  `eacc7e69f45fed3e7eb0c9bb76cf5c18387bcae4ba226a24812dc409c0b51e1b`, one file re-hashed and matching; the
  worktree's only untracked file is the expected `nodes/gc7rc_etth1/data` symlink.

## Steps 1-4 in the same session

| Step | Result | Key evidence |
|---|---|---|
| 1. checkout at the exact pin | **PASS** | separate clone, detached worktree; `git rev-parse HEAD` = `6fc553df…`; `git status --porcelain --untracked-files=all` shows only the `data` link; `merge-base --is-ancestor c025f89a HEAD` rc 0 (`step1_checkout.txt`) |
| 2. pins recomputed at the pin | **PASS** | node spec `8f874c50f66273e0655bfc9ccdad24a50c0fdb629f88ba7d4d60b13f2fcf2e0c`; committed pin `818b8f6e8ec6473f15c33ed58393e7cee8b8e8b0a71645576439929efb20bf27`; edits manifest `ba31fed3bb67c0d78825a0d026058cbeb3a0261971fe8a4766f138687b232306`; node and master `ar_isolated.py` both `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610`; 16 frozen entries (`pins_gc7rc_etth1.json`) |
| 3. environment | **PASS** | torch312 `uv pip freeze` 77 lines, sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, Python 3.12.16, equal to `sweep2/g1b/env/torch312.freeze.txt` (`env_torch312.json`) |
| 4. data | **PASS** | node data manifest `eacc7e69…`, 1 file, re-hashed and matching, symlink present (`datapins_gc7rc_etth1.json`); interpreter links resolve to the expected uv CPython 3.12.16 (`c7_final.json`, `interpreter_evidence`) |

## C1-C7 at the pin — PASS table

| # | Condition | Result | Key evidence |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces usable by the run uid | **PASS** | rc 0 with the torch312 interpreter (3.12.16) and `/usr/bin/python3` (3.10.12); uid 1008 mapped; real tmpfs mount and write; `condition_1_pass: true` (`c1_userns_env.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope >= 1` | **PASS** | `ptrace_scope=1`; parent→child attach ok; unrelated same-uid sibling attach `EPERM`; `condition_2_pass: true` (`c2_ptrace.json`) |
| C3 | delegated cgroup v2 subtree with `cgroup.kill` (8G / swap 0) | **PASS** | `memory_max_8g`, `memory_swap_max_0`, `nsdelegate`, `cgroup.kill` exists, create→join→kill→empty→removed; `condition_3_pass: true` (`c3_cgroup.json`, `.txt`) |
| C4 | non-root and the interpreter `sys.path` hard check | **PASS** | euid/uid 1008; both interpreters pass `probe_interp.py` at the pin; `condition_4_pass: true` (`c4_interp.json`, `.txt`) |
| C5 | real sandboxed CPU smoke with `effective: true`, no waivers/exceptions | **PASS** | outcome ok, `isolation.effective=true`, `waivers={}`, `exceptions=[]`, cgroup removed, run log intact; `condition_5_pass: true` (`c5_smoke.json`, `records/etth1_smoke/`) |
| C6 | GPU smoke with the sandbox on, full UUID, under the exclusive lease | **PASS** | interpreter torch312; full UUID `GPU-4d623e76-…`; sandboxed worker (PID 1 of its namespaces) allocated and synchronised a CUDA tensor (`cuda_available=true`, `device_count=1`, tensor sum 4096.0 correct, torch 2.6.0+cu124, CUDA 12.4), metric written, no CUDA error; lease `~/r1_locks/gpu0.lock`, 14:48:20–14:48:22Z, no lease log; no compute app before or after; `condition_6_pass: true` (`c6_gpu_smoke.json`, `c6_gpu_lease_status.txt`, `records/etth1_gpu_smoke/`) |
| C7 | end state: GPU idle and unleased, no leftovers, disk, checkouts | **PASS** | GPU identical before/after (353 MiB, no compute apps, 0 %); lease free; all six leftover buckets empty; 333.9 GiB free; worktree still at the pin with only the `data` link untracked; seven-node checkout still at `c025f89a…`; Track P harness `897d83c8…` tracked-clean (`c7_final.json`, `.txt`, `checkout_end.txt`) |

Supplementary, not a section-3 condition: the pin's `tests/trackg/test_trackg_isolation.py` in a delegated 8G /
swap-0 scope with torch312: **27 passed, 1 skipped** (the skip is the root-only test); `pytest_isolation.json`.

No CPUs 8-11 were used: every CPU-bound step was pinned with `taskset -c 16-31`. TASL-7, HTCondor, Ada and
deepthought were not contacted. No G.1b/G.5/G.4 chunk ran; no label or evaluation value was read. No deletion,
commit or push was made on the host.

## Captures

Capture set `TASL2_ISOLATION_HOST_CHECK_X_gc7rc_etth1_20261128_captures/` — 35 files + `SHA256SUMS`; `SHA256SUMS`
sha256 **`218005c5f4ab2b52f69868df58e6a44ebf7fba667f57ed1c81646aee761a137a`**; `sha256sum -c` rc 0 on TASL-2 and
`shasum -a 256 -c` rc 0 after fetch. It binds `checkout_end.txt`, `step1_checkout.txt`, `commands.txt`,
`host_facts.json/.txt`, `pins_gc7rc_etth1.json/.txt`, `datapins_gc7rc_etth1.json/.txt`, `env_torch312.json/.txt`,
`torch312.freeze.txt`, `c1`–`c7`, `pytest_isolation.json`, and `records/`.

## What happens next

1. Fresh independent review of this record and captures.
2. Coordinator publishes the record; Local fills the `gc7rc_etth1` addendum gate and runs the draft checks.
3. `gc7rc_forestcover` remains blocked on Local's per-node handoff at `3f7b09fe…`; the other three nodes are
   already on this branch's sibling records (Titanic and MetaMaze PASS, ETTh1 this record).

Decided alone: to reuse the prepared ETTh1 run root and the reviewed check scripts, to keep the same
phase3 matrix, and to add the step 1-4 evidence captures (`step1_checkout`, pins, data pins, environment, host
facts) to the same capture set. No signed value, code or note was changed.

**AI-assisted: DeepSeek compute agent, 28 Nov 2026. ENGINEERING_ONLY.**
