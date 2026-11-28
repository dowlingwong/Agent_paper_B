# TASL-2 host check at G.5 harness pin `3f92d3c3` for expansion node `mlgym_metamaze` (28 November 2026)

**Status: PASS — host-check record for the G.5 expansion addendum.** ENGINEERING_ONLY.
This file is the TASL-2 host-check record the addendum's `host_check` gate reads for `mlgym_metamaze`; the coordinator
publishes it and Local fills the note's gate as `host check <record> sha256 <its sha256>`.

host_check_host: TASL-2
host_check_harness_commit: 3f92d3c3fa9a6c41e583bb6075e3f92f8caed685
host_check_items: 1-7 PASS
host_check_verdict: PASS

## What this binds

The seven host conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` section 3 — C1 unprivileged
user/mount/PID/network/cgroup namespaces, C2 Yama `ptrace_scope >= 1`, C3 a delegated cgroup v2 subtree with
`cgroup.kill` (8G / swap 0), C4 non-root and the interpreter `sys.path` hard check, C5 a real sandboxed smoke with
`effective: true`, C6 a GPU smoke with the sandbox on (full UUID, under the exclusive lease), C7 end state — were
checked on TASL-2 at the reviewed exact G.5 harness commit `3f92d3c3…` for `mlgym_metamaze`, on its G.1b CPU set
0-3 and its `venv_jax` environment (C6 uses the `torch312` interpreter for the GPU check, as in the G.1b record).
All seven passed with no waiver. The node's earlier record covers the G.1b kit pin `aa354485`; this record is the
exact G.5 pin the addendum needs.

- Task `compute/20261128-20`; source `local/20261128-14-g5-metamaze-isolation-handoff` (review
  `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md`, verdict ACCEPTED for engineering isolation).
- Paper base `origin/main` `57e6d1ed5945ab48684e24e145b69d333b4f77d4`; queue `coord/coordinator` `216f33ea`.
- Harness repository `https://github.com/dowlingwong/autoresearch_harness`, separate clone
  `/home/dowling/r1_tracks/t1_tasl_x/harness_repo`; new detached worktree
  `/home/dowling/r1_tracks/t1_tasl_x/harness_metamaze_g5`, HEAD
  `3f92d3c3fa9a6c41e583bb6075e3f92f8caed685`, tracked-clean.
- Run root `/home/dowling/r1_engineering/t1_tasl_x_hostcheck_g5_20261128_metamaze` (`scripts/`, `captures/`,
  `logs/`, `records/`, `work/`). Same reviewed check scripts as the G.1b expansion host check, with the node row
  and checkout path updated to the G.5 commit.
- Host facts: TASL-2, Ubuntu 22.04.5 LTS, Linux 6.8.0-149-generic, i9-14900KF, 32 logical CPUs, microcode `0x133`;
  uid 1008 non-root; GPU `NVIDIA GeForce RTX 4090`, UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver
  535.309.01; `nvidia-smi --query-compute-apps` empty before and after; 353 MiB desktop reservation; GPU lease
  `~/r1_locks/gpu0.lock` free before and after.
- Data: `/home/dowling/r1_tracks/t1_tasl_x/data/mlgym_metamaze`, manifest sha256
  `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000` (TASL-2's host-specific manifest), 9 files;
  the worktree's only untracked file is the expected `third_party/mlgym/nodes/mlgym_metamaze/data` symlink.

## Steps 1-4 in the same session

| Step | Result | Key evidence |
|---|---|---|
| 1. checkout at the exact pin | **PASS** | separate clone, new detached worktree; `git rev-parse HEAD` = `3f92d3c3…`; `git status --porcelain --untracked-files=all` shows only the `data` link; `merge-base --is-ancestor c025f89a HEAD` rc 0 |
| 2. pins recomputed at the pin | **PASS** | node spec `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9`; committed pin `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db`; edits manifest `6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2`; node and master `ar_isolated.py` both `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610`; 19 frozen entries (`pins_mlgym_metamaze.json`) |
| 3. environment | **PASS** | venv_jax `python -m pip freeze` 56 lines, sha256 `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`, Python 3.12.16, equal to `sweep2/g1b/env/venv_jax.freeze.txt`; all three links resolve to the same target, sha256 `23bc148d…` (`env_venv_jax.json`) |
| 4. data | **PASS** | node data manifest `e2338195…`, 9 files, every file re-hashed and matching (`pins_mlgym_metamaze.json`, `host_facts.json`) |

## C1-C7 at the pin — PASS table

| # | Condition | Result | Key evidence |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces usable by the run uid | **PASS** | rc 0 with the venv_jax interpreter (3.12.16) and `/usr/bin/python3`; uid 1008 mapped; real tmpfs mount and write; `condition_1_pass: true` (`c1_userns_env.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope >= 1` | **PASS** | parent→child attach ok; unrelated same-uid sibling attach `EPERM`; `condition_2_pass: true` (`c2_ptrace.json`) |
| C3 | delegated cgroup v2 subtree with `cgroup.kill` (8G / swap 0) | **PASS** | `memory.max=8G`, `memory.swap.max=0`, `nsdelegate`, `cgroup.kill` exists, create→join→kill→empty→removed; `condition_3_pass: true` (`c3_cgroup.json`, `.txt`) |
| C4 | non-root and the interpreter `sys.path` hard check | **PASS** | euid/uid 1008; both interpreters pass `probe_interp.py` at the pin; `condition_4_pass: true` (`c4_interp.json`, `.txt`) |
| C5 | real sandboxed CPU smoke with `effective: true`, no waivers/exceptions | **PASS** | outcome ok, `isolation.effective=true`, `exceptions=[]`, cgroup removed, run log intact; `condition_5_pass: true` (`c5_smoke.json`, `records/metamaze_smoke/`) |
| C6 | GPU smoke with the sandbox on, full UUID, under the exclusive lease | **PASS** | torch312 interpreter; full UUID `GPU-4d623e76-…`; sandboxed worker (PID 1 of its namespaces) allocated and synchronised a CUDA tensor, metric written, no CUDA error; lease `~/r1_locks/gpu0.lock`, 14:10:43–14:10:45Z, no lease log; no compute app before or after; `condition_6_pass: true` (`c6_gpu_smoke.json`, `c6_gpu_lease_status.txt`, `records/metamaze_gpu_smoke/`) |
| C7 | end state: GPU idle and unleased, no leftovers, disk, checkouts | **PASS** | GPU identical before/after (353 MiB, no compute apps); lease free; all six leftover buckets empty; 333.9 GiB free; worktree still at the pin with only the `data` link untracked; seven-node checkout still at `c025f89a…`; Track P harness `897d83c8…` tracked-clean (`c7_final.json`, `.txt`, `checkout_end.txt`) |

Supplementary, not a section-3 condition: the pin's `tests/trackg/test_trackg_isolation.py` in a delegated 8G /
swap-0 scope with venv_jax: **27 passed, 1 skipped** (the skip is the root-only test); `pytest_isolation.json`.

No CPUs 8-11 were used: every CPU-bound step was pinned with `taskset -c 0-3`. TASL-7, HTCondor, Ada and
deepthought were not contacted. No G.1b/G.5/G.4 chunk ran; no label or evaluation value was read. No deletion,
commit or push was made on the host.

## Captures

Capture set `TASL2_ISOLATION_HOST_CHECK_X_mlgym_metamaze_20261128_captures/` — 31 files + `SHA256SUMS`; `SHA256SUMS`
binds every capture. `checkout_end.txt`, `host_facts.json/.txt`, `pins_mlgym_metamaze.json/.txt`,
`env_venv_jax.json/.txt`, `venv_jax.freeze.txt`, `c1`–`c7`, `pytest_isolation.json`, `records/`.

## What happens next

1. Fresh independent review of this record and captures.
2. Coordinator publishes the record; Local fills the `mlgym_metamaze` addendum gate and runs the draft checks.
3. `mlgym_titanic` is delivered separately; `gc7rc_etth1` and `gc7rc_forestcover` wait for Local's per-node handoff
   at `6fc553df…` and `3f7b09fe…`.

Decided alone: to use a separate new worktree for the G.5 pin and a fresh run root, to keep the same reviewed check
scripts, and to run the C6 GPU check with torch312 as the G.1b record did.

**AI-assisted: DeepSeek compute agent, 28 Nov 2026. ENGINEERING_ONLY.**
