# Independent review (round 2) — Track G G.0 U2 raw-cost census, node `autoresearch_fixedtokens` (17 November 2026)

**Reviewer.** Fresh independent reviewer (round 2), no prior involvement in this unit, the round-1 review, the port
kits, U0/U1, or the census report; did not write the proposal. **No node execution, no GPU job/lease, no host file
write beyond the one gitignored pytest cache `.pyc` disclosed below, no commit/push, no deletion, no other user's
process or file touched.** The only operations on Ada were
read-only reads plus the transient checks listed under "Access and attestation" below. The only write in the paper
worktree is this local review file (uncommitted); on Ada the only by-product is one gitignored pytest
assertion-rewrite `__pycache__` `.pyc` in `harness_ar/tests/trackg/` from the CPU-only static-test run (see the
attestation; no tracked-file change).

**Review window.** 2026-11-17 ~09:12–09:25 UTC (Ada clock: `ucrtasl`, hence ~01:12–01:25 PST) / ~10:12–10:25 CET
(Europe/Berlin), plus local byte checks. Note the deployment environment was still being created when the review
started: `envs/torch312` and `harness_ar` were written at ~09:08–09:09 UTC and the autoresearch data finished at
09:15:13 UTC; all facts below are the post-write state, re-read at 09:21–09:25 UTC.

**Object under review.** `docs/r1/proposals/TRACKG_U2_RAWCOST_20261117.md`, canonical bytes
**sha256 `86f8e283f768c8f8928e03b774552d81c81ca26b546f9af384271981d4e43413`**, **88 lines** — recomputed in the
worktree; matches the bytes I was asked to review. Revision 2 scopes the unit to exactly
`autoresearch_fixedtokens`; the other seven nodes are explicitly out of scope.

**Prior round.** `docs/r1/reviews/TRACKG_U2_RAWCOST_REVIEW_20261117.md` (sha256
`976bbb1c96bd104dbf51e5e9c6b0eb08887ce200a044c80bda4af1784a2f991d`, 313 lines): NOT ACCEPTED —
1 BLOCKING (unit granularity), 5 MAJOR (env not created; memory cap unenforced; undefined pre-run footprint; raw-cost
attribution; House Prices path), 14 MINOR.

**Worktree / state.** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`, HEAD
`841d5393a29eef0228ba8e1c6c3238e23872576b`; the proposal and the round-1 review are **untracked** (`??`), as is this
review. No commit/push. All local worktree reads were at this HEAD.

**Authority read.** Paper `main` `50176481cbc85fb9e5b5dd97887043dea6e528fb` (= `origin/main`/HEAD, 2026-11-17
09:47:53 +0100): `R1-TRACKG-G0-GO` (PLAN.md:1258), `R1-TRACKG-PORT-OWNER` (1259), `R1-TRACKG-G1B-HOST` (1209),
`R1-TRACKG-LICENCES` (1269), and `R1-TRACKG-PORT-DECISIONS` (**line 1289 only at `50176481`; not in worktree HEAD
`841d5393`** — the only authority row the unit needs that is not in the worktree). The unit's authority citations
resolve, including the timeout rule (4) = census baseline × 3 and "timeout is a failed proposal, not an
infrastructure retry", and Python 3.12 for the census. Kit bytes at `50176481`:
`docs/r1/reports/TRACKG_U3_PORT_AUTORESEARCH_20261117.md` blob `94b35728…`,
`docs/r1/reviews/TRACKG_U3_PORT_AUTORESEARCH_REVIEW_20261117.md` blob `4fc66756…`, merge commit `0ea061d1`
(ancestor of `50176481`). U0 basis on `ops-tasl-20261116`: `TRACKG_U0_RESULT_20261117.md` sha256
`d3b590a7…`, `u0_status_20261117.json` sha256 `6b62dd2a…` (both re-hashed locally and on Ada). Ada paper checkout
`/home/dowling/r1_trackg_20261117/Agent_paper_B_main_50176481` is at `50176481`, clean.

**Access and attestation.** Read-only SSH `experiment_zhixu` (user `dowling`, uid 1030, host `ucrtasl`): `git
rev-parse/status/diff/ls-files/worktree list`, `ls/stat/find/du/df/free/nproc`, `cat/head/sed/grep`, `sha256sum`,
`nvidia-smi --query-*`, reads of `/proc/self/cgroup` and `/sys/fs/cgroup/*`, `uv pip freeze` (the env has **no
pip**; `uv` is `~/.local/bin/uv 0.13.8`), and one CPU-only static-test run with `-p no:cacheprovider` and
`PYTHONDONTWRITEBYTECODE=1`. That run wrote (or refreshed) one file on Ada:
`harness_ar/tests/trackg/__pycache__/test_port_autoresearch.cpython-312-pytest-9.2.0.pyc` (43,940 B, mtime
01:18:01 PST = 09:18:01 UTC), pytest's assertion-rewrite cache; it is **gitignored** (`git check-ignore` →
`.gitignore:2:__pycache__/`) and `git status --porcelain` still shows only the expected
`?? nodes/autoresearch_fixedtokens/data` (no tracked change). No other file under the repo or data root changed
after 01:16 PST; the pytest temp dirs were transient. Three transient
memory-only cgroup capability probes with `systemd-run --user --scope` (a `/bin/true`-style scope, a 64 MiB scope
read of `memory.max`/`memory.swap.max`, and one 200 MB allocation under a 64 MiB cap; no files, no GPU). I did **not**
run the data setup, the smoke, any node, or any GPU work; did not write on the host other than that one gitignored
pytest cache file; did not commit/push.

## Verdict

**ACCEPTED — 0 BLOCKING, 0 MAJOR, 12 MINOR.** Every round-1 BLOCKING/MAJOR item is fixed in substance:

- **BLOCKING-1 fixed:** the unit is scoped to exactly one node and claims no cross-node authorisation (§1 header,
  §2 heading, §4, §5); the other seven nodes are deferred to their own reviewed units and U4 compiles rows.
- **MAJOR-1 fixed:** the torch env exists on Ada and every recorded fact is true (torch `2.6.0+cu124`,
  `torch.cuda.is_available() == True`, 8 devices, the eight recorded package versions, Python 3.12.16 via uv
  0.13.8, driver 545.23.08; `uv pip freeze` = 77 packages, sha256 `dea8a9df…`). The JAX env now exists too but is
  not needed for this node (the unit says so).
- **MAJOR-2 fixed:** a real user-cgroup cap is available and enforceable (verified: `memory.max=67108864`,
  `memory.swap.max=0`; a 200 MB allocation under a 64 MiB cap is SIGKILLed, rc 137). The unit's wrap, probe and
  STOP are the right construction.
- **MAJOR-3 fixed:** the undefined pre-run footprint is replaced by a declared 24 GiB free run-1 floor with a
  before/after `nvidia-smi` record and a measured-peak+2 GiB rule for later units; 4 of 8 cards currently meet
  the floor.
- **MAJOR-4 fixed:** baseline time is pinned to B1's `s000_baseline/run_record.json`
  `elapsed_seconds_info_only`; VRAM is attributed to the baseline process tree with an explicit, labelled
  whole-smoke upper-bound fallback; CPU/RAM is explicitly labelled whole-smoke or a dedicated baseline run;
  sampler/commands/intervals/co-tenant baseline are required.
- **MAJOR-5 resolved by scope:** House Prices is out of this unit and is forbidden here (no MLGym copy); it
  belongs to that node's own unit.

The remaining 12 MINOR findings are command-text corrections (M1–M3, already validated on Ada during this review) and
result-record/recording additions (M4–M12); none changes the procedure, scope, measurement, STOPs, or the kit bytes,
and none needs another independent review round. **The unit may be executed once for `autoresearch_fixedtokens` (one
node, one smoke; no retry) after M1–M3 are applied to the operator's commands and all of M4–M12 are satisfied in the
result record.** If the author prefers the canonical bytes to be self-contained, fold M1–M3 in as a revision-3 text
edit; that is a text-only change covered by this review.

---

## 1. Scope / unit granularity (VERIFY 1) — PASS; BLOCKING-1 fixed

The unit is now **one node**: the header says "one node only"; §1 status says "Scope: exactly
`autoresearch_fixedtokens`; each of the other seven nodes runs under its own reviewed unit with the same per-node
procedure; U4 compiles the rows"; §2 is headed "(this node only)"; §3 says "STOPs (this node)" and "stop this node
only"; §4 says "No other node"; §5 says "This unit yields the `autoresearch_fixedtokens` row only … no cross-node
authorisation is claimed here." This implements `R1-TRACKG-G0-GO` "逐节点原始成本，**每单元一个节点**… **每单元独立
审查**". No residual language authorises a second node: the mentions of the other seven nodes are all explicit
deferrals ("under its own reviewed unit"), and the House Prices sentence in §4 is a prohibition on *this* unit, not
authorisation for that node. The unit correctly keeps ENGINEERING_ONLY, Paper-A-first/co-tenancy, no noise
floor/D21/D28 on Ada (G.1b is L40S), no T1 label/sweep, and nothing counted as evidence.

## 2. Environment / kit / data (VERIFY 2) — MAJOR-1 fixed (M1–M3 residual)

Verified on Ada (read-only), against the unit's §1 claims:

| Claim in revision 2 | Observed |
|---|---|
| Ada Python **3.12.16** via uv | `~/.local/bin/python3.12` = Python 3.12.16; `~/.local/bin/uv` = **uv 0.13.8** (uv is not on the non-login SSH PATH; use `~/.local/bin/uv`) |
| `envs/torch312` created from the suite-requirements union + CUDA 12.4 torch 2.6.0 (+pytest, PyYAML) | `$R/envs/torch312` exists (built 09:08 UTC); `torch.__version__` = **2.6.0+cu124**, `torch.version.cuda` = **12.4**, `torch.cuda.is_available()` = **True**, `torch.cuda.device_count()` = **8**; `uv pip freeze` = **77 packages**, sha256 **`dea8a9df3a92f233009d5480921c9685c24ecd1e91e932d9efdfe53fb860eecd`** (sorted; `torch==2.6.0` in freeze, `+cu124` only in `torch.__version__` — normal) |
| numpy 2.5.4, transformers 4.49.0, datasets 5.0.1, sklearn 1.9.1, pandas 3.1.1, tiktoken 0.14.0, pyarrow 26.0.1 | **all true** (`scikit-learn==1.9.1`); pytest 9.2.0, PyYAML 6.0.3 also present |
| driver **545.23.08** | `nvidia-smi` reports 545.23.08 on all 8× RTX 6000 Ada (49,140 MiB); CUDA-12.x minor-version-compat caveat still to be recorded in the result |
| JAX env only needed for Breakout's own unit | `$R/envs/jax312` now exists (66 packages) but is **not required here**; this node is torch-only |
| `harness_ar` = `mac-trackg-port-ar-20261117b` @ `08d06507…` (base `717ad835`, only adds nodes/configs/tests; clean) | detached HEAD `08d065077d40087114452697d5d596e66a0578be`; `git rev-list --count 717ad835..HEAD` = 10; `git diff --name-status 717ad835..HEAD` = **20 × A**, only under `nodes/`, `configs/trackg/nodes/`, `tests/trackg/`; `origin/mac-trackg-port-ar-20261117b` = same tip; **tracked-clean** (`git status --porcelain` = only `?? nodes/autoresearch_fixedtokens/data`, the setup symlink the unit says is recorded not a STOP) |
| paper `main` `50176481` has the kit report/review | confirmed as above; note the unit's phrase "blob/per the main commit `0ea061d1`" is vague — cite the actual blobs (`94b35728…` report, `4fc66756…` review; merge `0ea061d1` is an ancestor of `50176481`) — see M10 |
| Data path/command | `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the repo); the deployment already completed the setup at 09:15:13 UTC: `…/data/autoresearch_fixedtokens/data_manifest.json` sha256 **`ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`**, **13 manifest files** (11 parquet shards + 2 tokenizer files; 963 M on disk, 14 files including the manifest), source revision `915333b4f8b8684f39aeaafea600fea6f43fb703` (matches U1's `915333b` prefix), directory **read-only** `dr-xr-xr-x`, node `data` symlink created. See M3. |

**Static test (the exact §1 command is not runnable as written).** The written command is, from `harness_ar`,
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src envs/torch312/bin/python -m pytest tests/trackg/test_port_autoresearch.py
-k "not smoke"`. `envs/torch312` is a **sibling** of `harness_ar` under `$R`, not inside it, so from `harness_ar`
this is `bash: envs/torch312/bin/python: No such file or directory` (rc 127, reproduced). The suite test file itself
is correct (each worktree has only its own file: `tests/trackg/test_port_autoresearch.py`; `-k "not smoke"` excludes
the one synthetic-smoke test). With the corrected command —
`cd $R/harness_ar && CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
$R/envs/torch312/bin/python -m pytest tests/trackg/test_port_autoresearch.py -k "not smoke" -p no:cacheprovider` —
I got **25 passed, 1 deselected, 75.87 s** (CPU-only; torch imported but no GPU touched). The `CUDA_VISIBLE_DEVICES=`
part is required: the deployment's CPU-masked run left `.pytest_cache/v/cache/{nodeids,lastfailed}` with **25
nodeids** and **lastfailed `{}`** at 09:14:10 UTC, and the deployment reports 9 failures in the unmasked (GPU-visible)
mode because the kit tests must run CPU-side. See M1.

**M1 (static-test command: absolute interpreter + CUDA mask) — required correction.** Use the corrected command
above; record the mask (`CUDA_VISIBLE_DEVICES=`), the interpreter path/version, and the result in the result file
(the deployment's 25-passed cache may be cited as the deployment run, but the unit's own run should be recorded with
the mask).

**M2 (per-run interpreter/PATH is not stated; this is execution-critical).** `port_smoke_gpu` launches the smoke with
the node's interpreter, but the harness runner builds the per-run environment as `env = dict(os.environ)` and runs
the node's `run_command`, which is `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python3 run_fixed_budget.py
--tokens …`. The runner does **not** put the env's `bin` on `PATH` and the `interpreter` argument is only used for the
new-file shadowing check. Ada's `python3` on the standard PATH is **3.10.12 with no torch**; unless the env is
activated or `PATH`/`VIRTUAL_ENV` is exported (or the launcher and the inner `bash` use the absolute env path), every
full-budget run fails at import. Also the unit's §2.2 wrap uses `bash -lc` (a login shell, which can reset `PATH`;
prefer `bash -c` or an absolute interpreter inside it). **Fix:** state `source $R/envs/torch312/bin/activate` (or
`export PATH="$R/envs/torch312/bin:$PATH" VIRTUAL_ENV="$R/envs/torch312"`) before the wrap and preserve it inside the
scope; record `which python python3`, `python -V`, `PATH`, `VIRTUAL_ENV`, and the launcher's absolute path. This is
the round-1 MINOR-14 item, still open.

**M3 (data setup is already done; record it and do not re-download).** The unit's §1 data sentence reads as a step to
run; the data now already exist, created by the deployment with the node's setup command and the env interpreter
(`envs/torch312/bin/python prepare_data.py --out $AR_TRACKG_DATA_ROOT/autoresearch_fixedtokens`). Re-running
`prepare_data.py` on a complete `--out` is safe — the frozen code only re-verifies the manifest and re-links the node
`data` — but the unit should say so, record the existing manifest sha (`ab7186d2…`), 13 files/963 M, read-only bit and
`du/df`, and record the setup/re-verify log. Note the host `logs/` directory is **empty**; the original setup log is
not preserved on the host, so the unit must capture a re-run/verify log under `<runs-root>` (or cite the deployment
log) and give its path/sha256. Without this the "record the setup log" requirement is unfulfillable as written.

## 3. Memory cap (VERIFY 3) — MAJOR-2 fixed (M4 record-only)

The unit wraps the smoke in `systemd-run --user --scope -p MemoryMax=64G -p MemorySwapMax=0 -- bash -lc '…'` and
passes `--memory-limit "systemd-run --user --scope -p MemoryMax=64G (whole unit)"`, verifies enforcement once with an
overshoot probe, and STOPs if not enforceable. This is the right construction and it **is real** on Ada: the cgroup
v2 memory controller is delegated to `user@1030.service` (`cgroup.controllers = memory pids`), `systemd-run --user
--scope -p MemoryMax=64M -p MemorySwapMax=0 -- bash -lc …` gives `memory.max = 67108864` and `memory.swap.max = 0`
inside the scope, and a 200 MB allocation under that 64 MiB cap is SIGKILLed (rc 137). The outer scope covers every
descendant of the smoke (including forked download workers and `torch.compile` subprocesses); a `setsid` child cannot
escape a cgroup. 64 GiB is comfortably above this node's need and below the 503 GiB host (288 GiB available).

**M4 (label/probe scope).** (a) The recorded `external_limit` string says "(whole unit)" but the cap wraps only the
smoke, not the data setup or static test. Say "whole smoke / `port_smoke_gpu` process tree" (or wrap the setup and
static test too) so the record matches what is enforced. (b) An overshoot of a 64 GiB cap would allocate ~64 GiB
transiently on a shared host; specify a small, dedicated probe (e.g., a 128 MiB cap with a 256 MiB allocation) and
record the exact command/result, rather than a 64 GiB transient. (c) Record the outer command, the
`memory.max`/`memory.swap.max` read inside the scope, and the probe result in the result file.

## 4. Pre-run footprint / co-tenancy (VERIFY 4) — MAJOR-3 fixed (M5 record-only)

§2.1 now defines the run-1 gate as **≥ 24 GiB free** with the stated basis ("no measured footprint exists yet"), a
before-launch `nvidia-smi --query-gpu=uuid,index,memory.free,memory.used` record, a wait/re-check/other-card rule, and
"later units use measured peak + 2 GiB"; the result records free/used before and after. At review time 4 of 8 cards
met the floor (free 13.2–38.5 GiB; `GPU-…` of cards 1, 4, 6, 7 ≥ 24 GiB), so the gate is evaluable and passable; the
choice of card/floor is recorded. That fixes the round-1 "undefined per-run-1 footprint" problem.

**M5 (co-tenant change / card fill mid-run / utilisation).** Round-1's fix also required "record the co-tenant change
over the run window, and if the card fills mid-run treat it as a STOP (do not retry on another card without recording
the change)"; revision 2 records only before/after free/used. Add: sample the co-tenant list and
`nvidia-smi --query-gpu=utilization.gpu,memory.free,memory.used` at least at launch, once mid-smoke (ideally in the
baseline window) and at the end; record the co-tenant apps/pids and their `used_memory` (the wrapper
`/home/dowling/r1_trackg_20261117/bin/nvidia-smi-live` filters 0-MiB stale entries if used); if free VRAM falls below
the measured baseline peak + 2 GiB or the baseline VRAM sample is contaminated by a new co-tenant, STOP and record,
with no unrecorded card switch. Also state the floor's rationale (24 GiB is a conservative run-1 floor, not a
measured peak). GPU timing on a shared card is also affected by co-tenant *compute*; record utilisation at the
baseline window so B1 is interpretable.

## 5. Raw-cost attribution (VERIFY 5) — MAJOR-4 fixed (M6–M7 record-only)

The itemised method is now correct in structure: (a) baseline time = `elapsed_seconds_info_only` from
`<runs-root>/runs_smoke/s000_baseline/run_record.json` (the runner writes `run_record.json` and that field; the run id
is `s000_baseline`, and B2 is a determinism check only, both values recorded); (b) VRAM = 1 s
`nvidia-smi --query-compute-apps=pid,used_memory` filtered to the baseline's process tree, or else the whole-smoke
maximum explicitly labelled "max over all smoke runs / card total (upper bound, includes co-tenants)", never called
the baseline's footprint; (c) CPU/RAM = `/usr/bin/time -v` on the smoke labelled whole-smoke, or an extra dedicated
baseline run whose `/usr/bin/time -v` is the baseline CPU/RAM; sampler/commands/intervals and co-tenant baseline
recorded. `nvidia-smi --query-compute-apps=pid,used_memory,process_name` works on Ada and lists co-tenant pids
(including other users'), so attribution and co-tenant recording are feasible.

**M6 (exact sampler / attribution / timing rules).** Add the exact sampler command and script (1 s loop appending
`nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader` with a UTC timestamp), the attribution rule
(e.g., pids whose `/proc/<pid>/cgroup` is the smoke's scope and whose start time is within the baseline window), and
the baseline-window delimitation: the **run-directory `mtime` is written at the end** and does not delimit the start;
use the baseline run's start (run.log first line / the runner's start) to open the window and the record write to
close it. Also: `/usr/bin/time -v`'s max-RSS is the timed process's (direct child's) RSS and does not necessarily
include the deepest grandchild (the training process) — the GNU `ru_maxrss` of the launcher can under-report; if a
dedicated baseline is used, run it so the training process itself is the timed command (or use the scope cgroup's
`memory.stat`/`memory.current` sampling; note this kernel 5.15 has no `memory.peak`), and/or label the number as a
lower-bound/`time -v` figure. The "extra dedicated baseline run is allowed" has **no invocation** in the kit: the
smoke CLI only runs the whole 8-run battery, so state the exact one-baseline command/script (e.g., call
`WorkingCopyRunner.run("s000_baseline", limits, train_seed=8001, split_seed=8001)` from a short script) or drop the
option and use the labelled whole-smoke aggregate.

**M7 (provisional timeout vs B1×3).** B1 as the timeout basis and B2 determinism-only is fixed, but the smoke's
`--provisional-timeout <s>` input is not specified or recorded: `ResourceLimits.timeout()` uses
`provisional_timeout_seconds` for the first measuring run and records `timeout_seconds: <value> (provisional
(measuring run))`; the node timeout = 3 × B1 is a **derived result for later runs/units**, not applied mid-smoke.
State the provisional value used (the CLI default is 1800 s; any chosen value must be ≥ a generous bound for the
slowest edit, e.g. the depth-6 edit ≈2.5× baseline compute), record it as provisional, and record 3 × B1 for the
census row.

## 6. Round-1 MINOR status (VERIFY 6)

| Round-1 MINOR | Status in revision 2 |
|---|---|
| 1 static-test per-worktree path | Per-worktree file list **fixed** (only `tests/trackg/test_port_autoresearch.py`, `-k "not smoke"`); the command is still **not runnable as written** (relative `envs/…` path; no CUDA mask) → see **M1** |
| 2 authority pin `main 50176481` | **Mostly fixed** (main `50176481` cited for the row/report; `0ea061d1` cited) but the blob shas are still vague → **M10** |
| 3 which baseline | **Fixed** (B1 named, B2 determinism only, both recorded); provisional-timeout value still unspecified → **M7** |
| 4 timeout reclassification | **Fixed** (recorded as harness outcome + manual failed-proposal/per-node STOP; no retry) |
| 5 disk 100 GB accounting | **Partial** — cap and <50 GB STOP present; exact filesystems, runs-root, expected footprint/total accounting still missing; current free 118 GiB (93 % used) vs a 100 GB cap → **M8** |
| 6 raw-record locations | **Fixed** (preserve `run_record.json`/`run.log`, never delete, paths/sha256 in the result) |
| 7 gate capture per node | **Fixed** (re-run U0 three-check gate immediately before launch, capture JSON path/sha/UTC, self-excluded `pgrep`); the exact self-exclusion form is inherited from the U0 result, whose warning is real — a naive literal `pgrep` self-matches (I reproduced a self-match) |
| 8 environment version capture | **Fixed** (python -V, freeze sha, torch/cuda, driver, CPU model, OS/kernel; CPU list/threads to add → **M9**) |
| 9 worktree cleanliness (tracked only) | **Fixed** (STOP on any tracked-file change; untracked `data` links/`__pycache__` recorded, not STOP) |
| 10 data-setup failure modes | **Fixed** (egress/setup timeout HF/Xet, PyPI, OGB, Kaggle listed) |
| 11 resumability | **Partial** (interrupted unit re-runs whole from a new `<runs-root>`, old moved aside; "STOP is not resumed — only restarted under a new reviewed unit" still not stated) → **M11** |
| 12 smoke run count/wall time | **Partial** (7–9 formula stated; this node has exactly 4 edits → **8 executed full-budget runs**, not stated; expected wall/GPU time still absent) → **M12** |
| 13 result-record completeness | **Partial** — many fields added; several still missing → **M9** |
| 14 interpreter selection | **Partial/central gap** — env paths given, but no activation/`PATH`/`VIRTUAL_ENV` statement and no per-run interpretation of `python3` → **M2** |

## 7. Host facts read-only (VERIFY 7)

| Item | Observed (2026-11-17 09:12–09:25 UTC) |
|---|---|
| Host | `ucrtasl`; user `dowling` (uid 1030); Ubuntu 22.04.5 LTS; kernel 5.15.0-151; 96 CPUs; 503 GiB RAM (288 GiB available, swap 17 GiB full) |
| Disk | `/dev/md0p3` 1.8 T, **118 GiB free, 93 % used** (`/home` and `/tmp` same fs); data 963 M; `df` is ≥ 50 GB |
| GPUs | 8× RTX 6000 Ada 49,140 MiB, driver 545.23.08; current free 13.2–38.5 GiB; **4 cards ≥ 24 GiB** (index 1, 4, 6, 7); co-tenant Ray/RL jobs and other users' pythons present; `nvidia-smi --query-compute-apps` works and shows pids/used memory |
| Memory controller / cgroup | cgroup v2; `user-1030.slice` controllers `memory pids`; `user@1030.service` has `memory pids` and `memory.max=max`; `systemd-run --user --scope` works; `MemoryMax`/`MemorySwapMax=0` observable and enforced; **no `memory.peak`** on this kernel |
| `harness_ar` | tip `08d06507…`, base `717ad835…`, 10 commits, diff = 20 × A only under nodes/configs/tests, origin tip identical, tracked-clean; only untracked `nodes/autoresearch_fixedtokens/data` (expected setup symlink) |
| Paper checkout | `Agent_paper_B_main_50176481` at `50176481`, clean |
| Data root | `$R/data/autoresearch_fixedtokens` — 13 manifest entries, 963 M, read-only, manifest sha `ab7186d2…`, source revision `915333b4…`; node `data` symlink present |
| Attempt / evidence root | **none**: no `EVIDENCE`, no `attempt*`, no `u2_*` `<runs-root>` anywhere under `/home/dowling`; `logs/` empty; no Track G process |
| Paper A / U0 gate | newest `live_*` == configured run dir (`…/live_20261018T234416Z`), `panel/finalize.json` present; U0 capture `6b62dd2a…`: `verdict clear_finished`, `paper_a_live_waiting_for_card:false`, `unidentified_apps:0`, no Paper A process; re-run requirement is in the unit |
| TASL-7 | irrelevant to this unit (no interaction, as §4 states) |

## 8. Findings and exact fixes

**M1 — static-test command as written is not runnable; needs the CUDA mask.** From `harness_ar`, the relative
`envs/torch312/bin/python` does not exist (rc 127), and the command lacks `CUDA_VISIBLE_DEVICES=`. **Fix:** use
`cd $R/harness_ar && CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $R/envs/torch312/bin/python -m
pytest tests/trackg/test_port_autoresearch.py -k "not smoke" -p no:cacheprovider`; record the mask and the result
(verified here: 25 passed, 1 deselected, 75.87 s; the deployment's cache shows `lastfailed {}` / 25 nodeids at
09:14:10 UTC).

**M2 — per-run interpreter/PATH unspecified.** The runner runs `python3 run_fixed_budget.py` with the inherited
environment; Ada's PATH `python3` is 3.10.12 without torch. **Fix:** activate the env (or export `PATH`/`VIRTUAL_ENV`)
for the smoke and inside the systemd-run scope (prefer `bash -c` or an absolute interpreter), and record
`which python python3`, `python -V`, `PATH`, `VIRTUAL_ENV`, launcher path.

**M3 — data already prepared; capture/record it.** **Fix:** state the data were completed by deployment step 0;
record the manifest sha `ab7186d2…`, 13 files/963 M, read-only bit, source revision `915333b4…`, `du/df`; run the
idempotent `prepare_data.py --out …` re-verify only if a log is needed, capture it under `<runs-root>`, and record
the log path/sha (host `logs/` is empty; the original setup log was not preserved).

**M4 — memory-cap label/probe scope.** **Fix:** record `external_limit` as the smoke's cap (not "whole unit") or cap
the prep too; specify and record a small dedicated overshoot probe (e.g., 128 MiB cap + 256 MiB allocation) and the
`memory.max`/`memory.swap.max` read inside the scope, not only a 64 GiB transient.

**M5 — co-tenant change / card fill mid-run / utilisation.** **Fix:** record co-tenant apps/pids and
`utilization.gpu,memory.free,memory.used` at launch, once mid-smoke (baseline window) and at the end; STOP and record
if free VRAM drops below measured baseline peak + 2 GiB or the sample is contaminated; no unrecorded card switch.

**M6 — raw-cost CPU/RAM/sampler details.** **Fix:** give the exact 1 s sampler command/script and attribution rule;
use the baseline run's start (not run-dir mtime) to open the window; note `/usr/bin/time -v` max-RSS semantics and
either time the training process directly for a dedicated baseline or label the aggregate/lower-bound; give the
single-baseline invocation if the dedicated run is used (the kit has no single-baseline CLI).

**M7 — provisional timeout value.** **Fix:** state the `--provisional-timeout` value used (default 1800 s or chosen
≥ generated bound for the slowest edit), record it as provisional, and record that node timeout = 3 × B1 is a derived
census result, not applied mid-smoke.

**M8 — disk accounting.** **Fix:** state the filesystem(s) and runs-root path, expected data + runs footprint
(≈1 GB data + <1 GB records), the 100 GB unit/total cap and the actual `du`/`df` before/after; note that a 100 GB use
with only 118 GiB free would also trip the <50 GB STOP, so the cap is a ceiling, not an expected use; no deletion.

**M9 — result-record fields still missing.** **Fix:** add node YAML sha256 (`774042dcb7a7e0c8…`), declared-edit
manifest sha256 (`d8f89c32…`, 4 edits E1–E4), suite test module sha256 (`55d218ae…`), CPU list/threads, worktree
tip + tracked-cleanliness at start and the expected untracked `data` link, `killed_with` and
`determinism.not_forced`, one JSON line per run, setup/static-test commands + results + mask/interpreter, the
baseline peak VRAM number or the explicit upper-bound label, sampler command/interval/attribution, co-tenant data,
provisional timeout, and the execution-time freeze sha (now `dea8a9df…`, 77 packages).

**M10 — authority pin blob detail.** **Fix:** cite the report/review blob shas as seen at `main 50176481`
(`94b35728…` and `4fc66756…`; merge `0ea061d1` is an ancestor of `50176481`), not only "blob/per the main commit".

**M11 — STOP/resumability semantics.** **Fix:** add that a per-node STOP ends this unit and is not resumed; restart
requires a new reviewed unit; an interrupted run re-runs whole from a new `<runs-root>` with the old directory moved
aside, not deleted.

**M12 — smoke cost expectation.** **Fix:** for this node state **8 executed full-budget runs** (baseline, broken
diff, E1 through the stub manager, E1–E4, B2) plus the refused frozen diff (9 records total), and an expected wall
time/GPU-hours bracket (the U3 estimate is ~1 min training + `torch.compile` + 21 M-token eval per run on an L40S;
the census measures it) — the census's raw cost still uses B1 only.

## 9. Verdict conditions and required result record

**Verdict: ACCEPTED** (0 BLOCKING, 0 MAJOR, 12 MINOR). The unit may be executed **once** for
`autoresearch_fixedtokens` (one node), no retry, after M1–M3 are applied to the operator's commands (they are
literal, already-validated fixes) and with M4–M12 satisfied in the result record. No new independent review round is
needed for those text/recording fixes; they do not change the reviewed procedure, scope, measurement, STOPs, kit
bytes, or authority. Any other node is **not** authorised by this review.

**`TRACKG_U2_AR_RESULT_20261117.md` (or the per-node row file) must contain at least:**

1. Unit id/date; `ENGINEERING_ONLY`; node `autoresearch_fixedtokens`, suite `autoresearch`; "on Ada / RTX 6000 Ada";
   "no evidence", "no T1 label", "no noise floor / no D21 / no D28 on Ada"; the one-node statement and "no
   cross-node authorisation".
2. Node: name/suite; budget `tokens 32,768,000`; node YAML sha256; representative-edit manifest sha256 (E1–E4,
   `measured:false`); suite test module sha256.
3. Bytes: harness repo + branch + tip `08d06507…` + base `717ad835…` + origin tip; paper main `50176481` (+ report
   blob `94b35728…`, review blob `4fc66756…`, merge `0ea061d1`); `harness_ar` tracked-cleanliness at start and the
   expected untracked node `data` link.
4. Environment: interpreter path/version (`$R/envs/torch312/bin/python`, 3.12.16), uv 0.13.8, `uv pip freeze`
   sha256 (and command, sorted or raw), torch `2.6.0+cu124` / `torch.version.cuda 12.4` /
   `torch.cuda.is_available() == True` / 8 devices, driver `545.23.08` + CUDA-12.x minor-compatibility note, OS/
   kernel, CPU model, CPU list, threads, `PATH`/`VIRTUAL_ENV`/`which python3`, `AR_TRACKG_DATA_ROOT`.
5. Paper-A-first gate: re-run capture path/sha256 + UTC; newest `live_*` == configured run dir; self-excluded pgrep
   form + result (empty); status verdict `clear_*`, key false, `unidentified_apps: 0`; `paper_a_live_waiting_for_card:
   false`.
6. Co-tenancy: GPU UUID/index, pre-run free/used VRAM, 24 GiB floor basis, post-run free/used, measured baseline
   peak (method/attribution) or the labelled whole-smoke upper bound, co-tenant apps/utilisation at launch/mid/end,
   card-fill decision; no unrecorded switch.
7. Data: exact setup command + interpreter; `AR_TRACKG_DATA_ROOT`; manifest sha256 (`ab7186d2…` now; re-verified at
   execution); every file sha256 (13 entries); file count/size; read-only bit; source dataset/revision
   (`915333b4…`); `du`/`df`; setup/re-verify log path + sha256; no re-download/no MLGym copy.
8. Memory cap: exact outer `systemd-run` command; probe command/result; `external_limit` string; cap value/units;
   the reading of `memory.max`/`memory.swap.max` inside the scope; STOP if not enforceable.
9. Run: runs-root path (outside the repo, preserved); provisional timeout; executed run count (8) + refused frozen
   diff; per-run `run_record.json`/`run.log` paths + sha256; baseline run id/path; B1 and B2
   `elapsed_seconds_info_only`; baseline peak VRAM (sampler command/interval/attribution) or labelled upper bound;
   CPU/RAM (`/usr/bin/time -v`, labelled, or dedicated baseline); checklist-E result + the `CHECKLIST_E_PASSED
   autoresearch_fixedtokens` line; one JSON line per run; `killed_with`; `determinism.not_forced` (torch: only
   `dataloader_workers`).
10. Timeout: B1 seconds; 3 × B1 derived basis; provisional value used; the manual "timeout = failed proposal /
    per-node STOP" reclassification note; no retry.
11. Disk: free before/after; data + runs-root footprint; 100 GB unit/total cap accounting; no deletion.
12. Static tests: command (absolute interpreter + `CUDA_VISIBLE_DEVICES=`), result (25 passed / 1 deselected here);
    env install record; mask recorded; the deployment cache evidence if cited.
13. STOP/pending rows with reason and preserved paths; raw-record locations/sha256; result-file sha256; the
    one-node/no-cross-node statement; what was not run and why.

## 10. What this review did and did not do

Verified: the canonical proposal bytes/line count and prior-review bytes; the authority rows at worktree HEAD and
paper `main 50176481` (including that `R1-TRACKG-PORT-DECISIONS` exists only at `50176481`, and the U3 report/review
blobs); the Ada host, disk, RAM/swap, CPU, cgroup delegation and a memory-cap enforcement probe; the harness base
repo and `harness_ar` (tip/base/origin/cleanliness/diff shape); the paper checkout at `50176481`; the torch env's
versions, freeze, interpreter, torch/CUDA state and driver; the now-created JAX env (not needed here); the data root,
manifest, read-only state, node `data` link and source revision; the static tests CPU-masked (25 passed) and the
written command's failure; the smoke CLI/record structure, `limits`/`ResourceLimits` timeout basis, the per-run
environment construction (`PATH` not set), `elapsed_seconds_info_only`, and the kit file shas; the U0 gate basis and
capture; the absence of any attempt/evidence/runs root. I did **not** run the smoke, any node, any GPU work, the
data setup, or the U0 gate re-run; did not verify the 9 GPU-mode static-test failures (no GPU use) — that is the
deployment's report, consistent with the CPU-masked cache evidence; did not verify the cu124 kernel launch under
driver 545.23.08 (no GPU use; the smoke is the intended check and a failure is a STOP); did not touch another user's
processes or files. If anything here conflicts with a dated PLAN row, the PLAN row wins.
