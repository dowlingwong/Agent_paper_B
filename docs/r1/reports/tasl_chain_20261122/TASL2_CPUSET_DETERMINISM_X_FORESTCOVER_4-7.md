# TASL-2 fixed-seed CPU-set determinism check for `gc7rc_forestcover` on CPUs 4-7 (26 November 2026)

**Status: PASS — R1-TASL2-CPU determinism record for the G.1b expansion node `gc7rc_forestcover`.** ENGINEERING_ONLY;
AI-assisted (DeepSeek Harness agent `exp-hostcheck-runner`, delegated by the lead). Run on TASL-2 in the same
session as the node's host-check record `TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261126.md`. This is the record
the node's `cpu_determinism` gate reads; the lead commits it to published `main` and, in a later reviewed
note, fills the gate as `determinism check <record> sha256 <its sha256>` (written uncommitted on the ops
worktree `ops-g1b-expansion-hostcheck-20261126`, baseline `a1597f70`; no push).

determinism_check_host: TASL-2
determinism_check_node: gc7rc_forestcover
determinism_check_cpus: 4-7
determinism_check_harness_commit: 85851664679d10889c5af406843c4a3fc38f7a49
determinism_check_runs: 2
determinism_check_result_channel_sha256: bcfc9b5d296a07335f46ec467c68ca7e282355882fccd44f9ea7f68cd628140a
determinism_check_baseline_seconds: 93.510 93.547
determinism_check_verdict: PASS

## Why this check

R1-TASL2-CPU withdraws CPUs 8-11 from every R1 job on TASL-2: the node's census set (8-11) is replaced
by 4-7 — a set of the same size that the TASL-2 CPU stability record
(`docs/r1/reports/tasl_chain_20261122/TASL2_CPU_STABILITY_20261125.md`, sha256 `9dca2cf3…164b`, review
ACCEPTED) passed 3 of 3, bitwise identical. The replacement set needs a fixed-seed determinism check before its
first use; the spec's `nodes[].cpu_replacement.determinism_check` names this record, two runs, and the census
baseline's result-channel sha256 `bcfc9b5d296a07335f46ec467c68ca7e282355882fccd44f9ea7f68cd628140a`. This record is that check for `gc7rc_forestcover`: the reviewed census
baseline step (`s000_baseline`, seeds 8001/8001, the full 8,000-step census budget) run twice on CPUs
4-7 from the node's G.1b checkout at its pin, each in its own delegated 8G/swap-0 scope. The node's
host-check record (C1-C7 at the same pin) is `TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261126.md`.

## Driver and evidence root

| item | value |
|---|---|
| driver | `run_baseline_determinism_gc7rc_forestcover_4-7.py`, sha256 `485c7db661b768ff345ec2bfb0ab553f8d3161e55215ef2ce93e31eb886a0174` |
| source driver | `captures/tasl2_cpu_stability_20261125/scripts/run_baseline_stability.py` (26 Nov stability record), sha256 `848fcb9f72f5c6d4b53f23754f7e4b5e10bb67f86233f7f12825243e4014258b` |
| adapted-driver diff | `host/driver.diff` against the stability driver, sha256 `36de7b65970ab29961cd6857c9a7580aec4a4b7077a0ca66208a868908777390` (153 lines): only constants (harness checkout, pin and branch, the torch312 environment, the data root, the node's spec pin values, the census provisional timeout, the evidence root, the run budget, the frozen-entry and data-file counts, the torch (not JAX) environment expectation, and — for Forest Cover only — the in-process `tests.trackg.port_smoke_gpu.CPU_ONLY_NODES` addition its census driver made). The driver accepts the section-9 detached worktree through the `HEAD` branch constant, asserted together with the pin. |
| evidence root on TASL-2 (preserved) | `/home/dowling/r1_engineering/g1bx_cpuset_determinism_20261126/gc7rc_forestcover_4-7/` (`scripts/`, `runs/`, `results/`, `logs/`, `host/`, `validation/`, `determinism_summary.json/.txt`) |
| driver validation | one reduced-budget (511 steps) run per node exercised the driver code path and the binding checks; not one of the two determinism runs (`validation/`) |

The driver calls the kit's own `run_smoke_campaign()` with an **empty proposal list**, so only its first run,
`s000_baseline` (seeds 8001/8001, real pinned data, isolation, limits), runs, and nothing else; the reviewed
`check_baseline_log()` is then applied. No repository file is changed; the kit is only imported.

## Per-run wrapper (both runs)

For each run (repeat 1, 2, sequential within the node): first sample `/proc/stat` for 5 s and go on only if no
CPU of the set was busier than 0.2; hold `flock -n ~/r1_locks/cpus-4-7.lock` for the run (so no G.1b job of
that set can start); then, inside

```
systemd-run --user --scope --unit=g1bx-det-forestcover-r1-20261126T101547Z --collect -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0
```

with `CUDA_VISIBLE_DEVICES=` (hidden: CPU-only), torch312 first on `PATH`, `VIRTUAL_ENV` and
`AR_TRACKG_DATA_ROOT=/home/dowling/r1_tracks/t1_tasl_x/data` set, `taskset -c 4-7` and the node's census provisional timeout, the adapted
driver runs `--group 4-7 --repeat <n> --runs-root <evidence>/runs/r<n> --out <evidence>/results/r<n>.json`.
The driver sets `AR_TEST_CGROUP_PARENT` to its own scope, as the census and stability runs did. The two nodes'
checks (Titanic on 4-7 and Forest Cover on 4-7) may run concurrently because the sets are disjoint; the two
runs of one node ran one after another.

## Runs

| run | window (UTC) | launcher wall s | `elapsed_seconds_info_only` | rc / outcome | `result_channel_sha256` | `log` sha256 | frozen checked / changed | `memory.max` / swap | affinity | busy sample (set max) | load average |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-26T10:15:47Z-10:17:22Z | 94.453 | 93.510 | 0 / ok | `bcfc9b5d296a…` | `07c6557e5a66…` | 16 / `[]` | 8589934592 / 0 | `[4, 5, 6, 7]` | 0.012 (0.005 mean) | 0.31 / 0.34 / 0.28 |
| 2 | 2026-11-26T10:17:29Z-10:19:03Z | 94.479 | 93.547 | 0 / ok | `bcfc9b5d296a…` | `07c6557e5a66…` | 16 / `[]` | 8589934592 / 0 | `[4, 5, 6, 7]` | 0.002 (0.001 mean) | 6.23 / 2.49 / 1.06 |

Both runs: `isolation.effective=true`, `waivers={}`, `exceptions=[]`, `frozen_files_changed=[]`, scope
`memory.max=8589934592` B, `memory.swap.max=0`, affinity exactly `[4, 5, 6, 7]`, checkouts at their pins with
only the setup `data` link untracked. The census baseline's result channel is 63 bytes in both runs.
Hashes and wall times only are recorded: no metric value is copied into this record or its captures.

## Pass criterion (spec section 9 step 7) — PASS

| criterion | required | run 1 | run 2 |
|---|---|---|---|
| exit / outcome | rc 0 and outcome ok | 0 / ok | 0 / ok |
| isolation | `effective:true`, waivers `{}`, exceptions `[]` | as required | as required |
| frozen files changed | `[]` | `[]` | `[]` |
| `result_channel_sha256` | `bcfc9b5d296a07335f46ec467c68ca7e282355882fccd44f9ea7f68cd628140a` (the census baseline's) | **equal** | **equal** |
| `elapsed_seconds_info_only` | at most 140.109 s (1.5 × census B1 93.406 s) | 93.510 s | 93.547 s |
| affinity | exactly the set `4-7` | `[4, 5, 6, 7]` | `[4, 5, 6, 7]` |
| scope | 8 GiB / swap 0 | 8589934592 B / 0 | 8589934592 B / 0 |
| checkout | at `85851664679d10889c5af406843c4a3fc38f7a49`, clean apart from the data link | as required | as required |

**Verdict: PASS.** Both result channels equal the census baseline's result-channel sha256, and both
`run.log`s are byte-identical across the two runs (same sha256), i.e. the census baseline is reproduced
bit-for-bit on the R1-TASL2-CPU replacement set. The measured baselines are well inside the 1.5 × census B1
bound.

## End state (spec section 9 step 8) — PASS

`session_end_state.txt`: after both determinism checks the GPU was idle and unleased
(`gpu0.lock` free, no compute apps, 358 MiB desktop reservation, 0 %), the CPU-set leases `cpus-0-3`,
`cpus-4-7` and `cpus-12-15` were free, no `g1bx-*` scope, no `ar_*` run cgroup and no determinism process
was left; all four node checkouts were at their pins with only their `data` links untracked; the seven-node
checkout `/home/dowling/r1_tracks/t1_tasl/harness` was at `c025f89aeafc2199bf3487b4bcaa16678273c702` clean; Track P's harness repository
`/home/dowling/r1_trackp/autoresearch_harness` was only `stat`-ed/`git status` read (tracked-clean, mtime 2026-10-25); `/` had 343 GiB free.
(Titanic's and Forest Cover's checks ran concurrently on disjoint sets, so Forest Cover's `host/host_after.txt`
was taken while Titanic's run 2 was still running; the two-node end state is `session_end_state.txt`.)

## Capture evidence

- Capture set: `TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7_captures/` — 23 files including `SHA256SUMS`;
  `SHA256SUMS` sha256 **`f2165904dbdf8ed9441ab58c720dbc8a5c0fb77bdda5d32e08c925d2d3bf2320`**; `sha256sum -c` rc 0 on TASL-2 and `shasum -a 256 -c` rc 0 after fetch.
- Key files: `determinism_summary.json/.txt`, `ledger.tsv`, `busy_r1_attempt1.json` / `busy_r2_attempt1.json`,
  `logs/r1.console.sanitized.txt` / `r2...` (metric values redacted), `scripts/` (the adapted driver, the
  stability source driver, `busy_sample.py`, `collect_det.py`), `host/driver.diff`, `host/driver_sha256.txt`,
  `host/host_before.txt`, `host/host_after.txt`, `session_end_state.txt`.
- The full evidence root (with the run records, logs and result channels that contain the metric value) is
  preserved on TASL-2 at `/home/dowling/r1_engineering/g1bx_cpuset_determinism_20261126/gc7rc_forestcover_4-7/` and was not copied, so that no metric value enters this
  record or its captures.

## Scope and non-authorities

Only TASL-2 was used (`ssh -o BatchMode=yes portal_zhixu`); TASL-7, HTCondor and deepthought were not
contacted. CPU only: `CUDA_VISIBLE_DEVICES=` for every run, no GPU and no GPU lease; CPUs 8-11 were never
used. Nothing was deleted, committed or pushed; no G.1b chunk, no label read, nothing in Track P's repository
changed. This is a determinism (gate) record, not a launch authorization: the node's other gates are still
required and the coordinating chat publishes it.

**AI-assisted: DeepSeek Harness agent `exp-hostcheck-runner`, 26 Nov 2026. ENGINEERING_ONLY; uncommitted.**
