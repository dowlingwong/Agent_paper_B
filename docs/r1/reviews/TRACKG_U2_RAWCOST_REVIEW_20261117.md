# Independent review — Track G G.0 U2 raw-cost census on Ada (17 November 2026)

**Reviewer.** Fresh independent reviewer agent (no prior involvement in this unit, the port kits, U0/U1, or the
census report; did not write the proposal and has never run anything on Ada).
**Review window.** 2026-11-17, ~08:59–09:15 UTC (Ada clock) / ~09:59–10:15 CET (Europe/Berlin).
**Object under review.** `docs/r1/proposals/TRACKG_U2_RAWCOST_20261117.md`, canonical bytes **sha256
`bb06acd58136c22cc6ad001daa5a0c33229d776796d364e9c9a6de7994e3cdec`**, **68 lines** — recomputed in the worktree;
matches the bytes I was asked to review.
**Worktree / state.** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`, HEAD
`841d5393a29eef0228ba8e1c6c3238e23872576b`; the proposal is **untracked** (`??`), as its status line says it is
uncommitted. I made no commit/push; this review file is uncommitted.
**Authority read.** `R1-TRACKG-G0-GO` (PLAN.md line 1258), `R1-TRACKG-PORT-OWNER` (1259), `R1-TRACKG-LICENCES` (1269),
`R1-TRACKG-G1B-HOST` (1209) in `HEAD:docs/r1/PLAN.md`; `R1-TRACKG-PORT-DECISIONS` (**line 1289 only at paper `main`
`50176481`**, added by that commit's `docs/r1/PLAN.md` hunk — **not in worktree HEAD 841d5393**); `R1-ADA-CENSUS`
(PLAN.md:773); `prompts/TRACKG_PORT_CHECKLIST.md`; `TRACKG_G0_ADA_CENSUS_20261116.md` §5;
`reports/trackg_g0_20261117/TRACKG_U0_RESULT_20261117.md` (sha256 `d3b590a7…`) and `u0_status_20261117.json`
(`6b62dd2a…`).
**Access and attestation.** Read-only SSH `experiment_zhixu` (user `dowling`, uid 1030, host `ucrtasl`): `ls`,
`stat`, `cat/head/tail/sed/grep`, `sha256sum`, `wc`, `df`, `free`, `command -v`, `git rev-parse / status
--no-optional-locks / diff --name-status / ls-files / worktree list / branch -a`, `nvidia-smi --query-*`, reads of
`/proc/self/cgroup` and `/sys/fs/cgroup/*`, `/usr/bin/time -v /bin/true`, and two short-lived capability probes
`systemd-run --user --scope … /bin/true` / `/bin/sh -c …` (rc 0; transient scopes, no file written, no GPU). **No node execution, no GPU
job/lease, no host file write, no commit/push, no deletion, no other user's process or file touched.** The only
write is this local review file.

## Verdict

**NOT ACCEPTED — 1 BLOCKING, 5 MAJOR, 14 MINOR.** The *procedure's intent* is mostly right and the deployment bytes
that do exist are correct (harness worktrees clean at the reviewed tips; paper `main` `50176481` carries the reports,
reviews and checklist F; Python 3.12.16 via uv is installed). But the unit cannot be executed as written and, in its
current scope, it is **not the unit the authority authorises**: `R1-TRACKG-G0-GO` says U2 is *one node per unit,
each unit independently reviewed*, while this one unit authorises all eight nodes and one combined result file.
Separately, the environment/data prep it describes as done does not exist yet, the memory cap it records is not
enforced, the free-VRAM gate uses a quantity that is undefined before the measured run, the raw-cost sampling does
not isolate the baseline run, and the House Prices data path as executable still defaults to the MLGym copy the
`R1-TRACKG-PORT-DECISIONS` (2) forbids.

None of the fixes requires changing the frozen kit. After BLOCKING-1 and MAJOR-1…5 are fixed, the remaining items
are text/procedure edits (MINOR), and this is the right way to run the census on Ada.

---

## 1. Authority / scope (VERIFY 1)

**PASS in substance, FAIL in unit granularity (BLOCKING-1).**

The unit's authority citations resolve: `R1-TRACKG-G0-GO` authorises the U0 → U1 → U2 → U4 sequence, ENGINEERING_ONLY,
no noise floor / no D21 / no D28 on Ada (G.1b is on NEMO2 L40S per `R1-TRACKG-G1B-HOST`), Paper A first, resumable
units, one node per unit, no disturbance of other users; `R1-TRACKG-PORT-OWNER` assigns Mac kit / experiment-agent
deployment+smoke; `R1-TRACKG-LICENCES` fixes the licence handling; `R1-TRACKG-PORT-DECISIONS` (1)–(4) fixes MLGym
licence placement, House Prices via Kaggle `--from-file`, imdb baseline provenance, timeout = census baseline ×3
(timeout = failed proposal, not an infrastructure retry) and Python 3.12 for the census. The unit reproduces all of
these correctly and correctly keeps G.1b's noise-floor/D21/D28 work off Ada. It also correctly says "no evidence"
(§4) and that the result is ENGINEERING_ONLY on Ada.

**BLOCKING-1 (scope / unit granularity).** `R1-TRACKG-G0-GO` line 1258: "U2（逐节点原始成本，**每单元一个节点**…）…
**每单元独立审查**" — per-node raw cost, one node per unit, each unit independently reviewed. The proposal is a single
unit that (a) authorises running **all eight** nodes (`§2` lists
`autoresearch_fixedtokens, mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv, mlgym_cifar10, mlgym_fmnist, mlgym_houseprice,
mlgym_breakout_minatar`), (b) says "For each node (in an order …)" and "continue with the next node" after a per-node
STOP, and (c) produces one combined result file (`§5` `TRACKG_U2_RAWCOST_RESULT_20261117.md` with all rows). The
`§2` heading "(one node per unit, resumable)" states the rule but the body does not implement it. One review of an
eight-node execution is not "每单元独立审查".
**Exact fix.** Scope this unit to exactly **one named node** (recommend `autoresearch_fixedtokens`, the single
autoresearch candidate), keep `§2` as the shared per-node procedure, and state that each of the other seven nodes
runs under its **own** reviewed unit (same procedure) with its own result record; `U4` then compiles the per-node
rows into `TRACKG_CENSUS_20261117.md`. If the author truly wants one authorisation for all eight, that needs a new
dated PLAN row superseding "每单元一个节点" (not a U2 proposal edit). Do not execute more than the named node under
this review's authority.

Everything else in VERIFY 1 is PASS: ENGINEERING, no T1 label/sweep runs, no noise floor/D21/D28 on Ada (they are
explicitly assigned to L40S), Paper-A-first and co-tenancy are present, Python 3.12 is required, House Prices is
required to be the Kaggle download via `--from-file`, and no MLGym copy is permitted in text.

## 2. Kit / deployment facts (VERIFY 2)

### 2.1 Verified correct (PASS)

| Item | Observed |
|---|---|
| Paper `main` `50176481` | present as `origin/main` (`50176481cbc85fb9e5b5dd97887043dea6e528fb`, 2026-11-17 09:47:53 +0100); it contains `docs/r1/reports/TRACKG_U3_PORT_{AUTORESEARCH,MLAB,MLGYM}_20261117.md` (blobs `94b35728…`, `90b3325f…`, `cd631ad6…`), their review records (`4fc66756…`, `dc70af1e…`, `d3eb7ed1…`, each "accepted in round 8/8/6" at the stated harness tips), and `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md` **section F**; kit branches were merged at `0ea061d1` (ar), `c0cbc4ae` (mlab), `145e30b9` (mlgym) before `50176481`. Ada paper checkout `…/Agent_paper_B_main_50176481` is at `50176481` and clean. |
| Harness base | `/home/dowling/r1_trackg_20261117/autoresearch_harness` @ `717ad835df32bbe1047d032fb5bb8dde5384a258`, branch `r1-local-trackg-v2-20261114`, clean; the three port worktrees are linked worktrees of it. |
| Harness worktrees | `harness_ar` @ `08d065077d40087114452697d5d596e66a0578be`, `harness_mlab` @ `8596a0ec730b4924e031adf90cb0c38a9a897399`, `harness_mlgym` @ `334c89ce0e036022cd1f993830a84809092ca44c` — detached HEAD at exactly the reviewed tips; `git status --porcelain` **empty** for all three; `rev-list --count 717ad835..HEAD` = 10 / 10 / 8 (matches the report commit lists); `git diff --name-status 717ad835..HEAD` is **all `A`** and only under `nodes/`, `configs/trackg/nodes/`, `tests/trackg/` (20 / 45 / 60 added files; no existing harness file changed). `origin/mac-trackg-port-{ar,mlab,mlgym}-20261117b` also resolve to those tips. |
| Python on Ada | `uv 0.13.8`; `~/.local/bin/python3.12` = **Python 3.12.16**; `envs/torch312/pyvenv.cfg` records CPython 3.12.16 (uv 0.13.8). |

### 2.2 Not true as written (MAJOR-1)

**MAJOR-1 (environment/data prep is not done, but §1 says "done as prep; verified bytes").** What exists on Ada:
`envs/torch312` is an **empty** uv venv (`uv pip list` → no packages; `import torch` and `import jax` both
`ModuleNotFoundError`); there is **no JAX environment** (`envs/` contains only `torch312`); the system interpreter is
Python **3.10.12** with **no pytest** (PyYAML 5.4.1 and numpy 1.21.5 happen to be present, but pytest is not, and 3.10 is not the mandated 3.12); there is no `data/` symlink, no recorded `AR_TRACKG_DATA_ROOT` path,
no prepared data directory, and no Kaggle file/credentials (`~/.kaggle` absent; bounded `find` under `/home/dowling`
for `*kaggle*` found nothing). `logs/` is empty and the deployment root has had no writes since 00:59Z, ~8 h before
this review, so "being deployed" is not an accurate description either. Consequences: the static-test command, data
setup, and `port_smoke_gpu` **cannot run as written**; the report's JAX requirement (`requirements_gpu.txt`) and the
torch env are still just a plan; the unit's first real step has no engine.
**Exact fix.** Make env creation an explicit **step 0** of the unit (or complete it before re-review):
torch env = one `uv pip install` resolver call for the union of the suite requirements with a CUDA 12.4 build of
`torch==2.6.0` plus `pytest`/`PyYAML`; JAX env = one resolver call from
`harness_mlgym/nodes/mlgym_breakout_minatar/requirements_gpu.txt`; record `uv pip freeze` (sha256) for both, the
interpreter path/version, and a one-line `torch.cuda.is_available()` / JAX-device check; set and record
`AR_TRACKG_DATA_ROOT=<absolute path outside the repo>` (see M5/M8); add a per-node STOP for PyPI/HF/OGB/Kaggle
download or credential failure (M10). Also note the host driver is `545.23.08` (CUDA 12.3-era) and the planned
cu124 wheels ride CUDA's 12.x minor-version compatibility — verify this once in the env check and record it, or pin
a build the driver is known-good with.

## 3. Procedure correctness (VERIFY 3)

The *tool* and the stated invocation are consistent: `tests/trackg/port_smoke_gpu.py` (sha256
`347e3a4bdb30d982c57dcc58eaf0d58db52d86500406ddc9b7b4ac98db69ea72`, identical in all three worktrees) accepts
`--node/--gpu-uuid/--cpus/--memory-limit/--runs-root/--provisional-timeout`, requires `--gpu-uuid` for every node
except `mlgym_houseprice` (the only `CPU_ONLY_NODES` member), imports the node's suite test module from the
worktree, refuses a missing real `data/` symlink where the suite's smoke table needs data, runs the baseline + one
frozen-path diff (refused) + one broken diff + the first declared edit through the stub manager, then every declared
edit and a second baseline with the same seeds, checks checklist E (`check_smoke`), prints one JSON line per run and
`CHECKLIST_E_PASSED <node>`. That is exactly the checklist-E smoke the reports describe. Issues:

**MAJOR-2 (memory cap is recorded, not enforced).** `--memory-limit` is passed into
`port_support.limits(...)` → `ResourceLimits(memory_bytes=None, memory_method="external", external_limit=<string>)`
and is therefore only a **recorded string**; `ResourceLimits.__post_init__` merely refuses an empty string. The smoke
helper hard-codes `external` and gives no way to use `rlimit_data`, and there is no `uncapped_reason` path in the
smoke CLI. Checklist D requires a real cap ("CPUs and memory cap set … external_limit naming what enforces it";
"rlimit_data is for hosts without a cgroup cap"), and co-tenancy ("never disturb other users") makes an unenforced
cap material, not cosmetic. There is no sudo/cgroup management from a normal shell, **but Ada does expose the
user-level cgroup v2 memory controller** (verified: `/sys/fs/cgroup/cgroup.controllers` contains `memory`; the session
scope's `memory.max` is `max`; `systemd-run --user --scope -p MemoryMax=2G /bin/sh -c …` returns rc 0 and the transient scope's `memory.max` reads back `2147483648`; host RAM 503 GiB,
285 GiB available). **Exact fix.** Wrap the whole smoke command in a real cap, e.g.
`systemd-run --user --scope -p MemoryMax=64G -p MemorySwapMax=0 -- bash -lc '… port_smoke_gpu … --memory-limit
"systemd-run --user --scope -p MemoryMax=64G (whole unit)"'`; verify enforcement once with a small overshoot probe
(operator step; record it), and choose/record the value (e.g. 64 GiB, comfortably above any node's need and below the
503 GiB host). If the cap cannot be enforced, the unit must STOP — a descriptive string is not a cap.

**MAJOR-3 (co-tenancy gate uses a quantity that does not exist before the run).** §2.1 says "choose a GPU whose free
VRAM ≥ the node's **observed footprint** + 2 GiB", and §2.2 measures the peak only during the run. Before the first
run of a node there is no observed footprint: the port reports measured nothing (`ENGINEERING_ONLY`), the kit's
synthetic smoke ran on CPU, and no per-node VRAM estimate exists in the reviewed records. So the gate cannot be
evaluated for run 1 of each node (and with the card occupancy seen now — 9,953–35,204 MiB used per card, free
14–39 GiB — it matters). **Exact fix.** Declare a per-node pre-run footprint estimate (or a fixed run-1 floor, e.g.
"≥ 24 GiB free for GPU nodes, ≥ footprint estimate + 2 GiB"), record its basis; record `nvidia-smi
--query-gpu=uuid,memory.free,memory.used` immediately before launch and require free ≥ estimate + 2 GiB; record the
free/used pair again after the smoke; for later units/runs use the measured peak + 2 GiB. Also record co-tenant
change over the run window, and if the card fills mid-run treat it as a STOP (do not retry on another card without
recording the change).

**MAJOR-4 (raw-cost sampling does not isolate the baseline run).** §2.2 says "peak VRAM from an `nvidia-smi
--query-gpu=memory.used` 1 s sampler **around the run**, and CPU/RAM from `/usr/bin/time -v` (max RSS, user+sys,
elapsed)". But the smoke executes **7–9 full-budget runs** (baseline + broken + first edit + all 3–5 edits + repeat
baseline; frozen diff is refused, not run): a sampler around "the run" is around the whole smoke, so `memory.used`
gives the card total (including other users' jobs) and the max over *edited* runs, not the baseline's footprint;
`/usr/bin/time -v` around the smoke gives whole-smoke elapsed/CPU and the max RSS of the largest child, not the
baseline's. The baseline's `elapsed_seconds_info_only` is available in
`<runs-root>/runs_smoke/s000_baseline/run_record.json` (the printed JSON lines include elapsed only for the per-edit
records), so time is recoverable; VRAM/CPU/RAM attribution is not. **Exact fix.** State all of: (a) baseline time =
`elapsed_seconds_info_only` from `s000_baseline/run_record.json` (path and run id in the result); (b) VRAM = max of
`nvidia-smi --query-compute-apps=pid,used_memory` sampled at 1 s and filtered to the baseline run's process tree (use
the run-dir creation/`run_record.json` mtimes to delimit the baseline window), or, if sampling the whole smoke, label
the number **"max over all smoke runs / card total (upper bound, includes co-tenants)"** and never call it the
baseline footprint; (c) CPU/RAM = either `/usr/bin/time -v` on a dedicated baseline run (one extra full-budget run,
still inside the one-node unit) or the whole-smoke aggregate explicitly labelled as such. Record the sampler command,
interval, attribution rule and co-tenant baseline alongside the numbers.

**MAJOR-5 (House Prices data path is not compliant as executable).** The unit's text is right ("must be the user's
Kaggle download passed via `prepare_data.py --from-file <Kaggle train.csv>` — not MLGym's redistributed copy"), but
the frozen node's `setup_command` and `prepare_data.py` **fetch MLGym's copy by default**
(`https://raw.githubusercontent.com/facebookresearch/MLGym/9d40c1b5…/data/regressionKaggleHousePrice/_helpers/train.csv`),
and `--from-file` is documented as taking "the same file from a local MLGym checkout" and requires the pinned
MLGym sha256 `1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41` / md5
`80ccab65fb115cbad143dbbd2bcd5577`; the manifest it writes always records `source = MLGym repo/commit/path`. So a
run that follows the node's own setup command uses the forbidden copy, and even a compliant Kaggle `--from-file` run
records MLGym as the manifest source. **Exact fix.** Forbid running this node's `setup_command` verbatim; specify the
exact command `AR_TRACKG_DATA_ROOT=<root> python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_houseprice"
--from-file '<author-provided Kaggle train.csv>'`; require the Kaggle file's sha256 to equal the pin (record it and
the file bytes/date), else per-node STOP (no substitution); record the Kaggle competition URL
(`kaggle.com/competitions/house-prices-advanced-regression-techniques`), the download date, the manifest sha256, and
a note that the manifest's `source` field names the MLGym repo path (so the provenance is the hash identity, not the
manifest's label). Keep the unit's disposition for missing Kaggle data — **per-node STOP, "Kaggle data unavailable;
pending author", never MLGym's copy** — that is the correct disposition under one-node-per-unit; the author should
be asked for the file before U4 closes the row.

**MINOR-1 (static-test command wrong per worktree).** §1 gives
`PYTHONPATH=src python3 -m pytest tests/trackg/test_port_{autoresearch,mlagentbench,mlgym}.py -k "not smoke"`, but
each worktree contains **only its own** suite file (`harness_ar/tests/trackg/test_port_autoresearch.py`;
`harness_mlab/.../test_port_mlagentbench.py`; `harness_mlgym/.../test_port_mlgym.py`). Pytest errors on the two
missing paths and collects nothing. Fix: per worktree `… pytest tests/trackg/test_port_<suite>.py -k "not smoke"`,
and state the node→worktree map (all nodes of a suite must be smoked from that suite's worktree; `port_smoke_gpu`
only finds `SMOKE` entries in modules present in the worktree). The synthetic smoke test is named
`test_synthetic_smoke`, so `-k "not smoke"` does exclude it, as intended.
**MINOR-2 (authority pin).** `R1-TRACKG-PORT-DECISIONS` is not in worktree HEAD `841d5393` (it is line 1289 only at
paper `main` `50176481`), and the U3 reports/reviews are likewise only on that main; the unit should cite
`main 50176481` for the row and the report blob shas (or the merge commits) so the authority and kit bytes are
reproducible from the unit itself.
**MINOR-3 (which baseline).** The smoke produces two baselines (B1 and the same-seed repeat B2). Define the
timeout basis as the **first** baseline B1 (`s000_baseline`), record both `elapsed_seconds_info_only` values, and say
the repeat is a determinism check only; "census baseline runtime × 3" otherwise has two possible inputs.
**MINOR-4 (timeout classification).** `R1-TRACKG-PORT-DECISIONS` (4) says a timeout is a **failed proposal**, not an
infrastructure retry, but the harness (and the MLGYM/AR port reports' open points) currently classifies timeouts as
`infrastructure_failure` and re-runs them; a port cannot change the outcome class. State that in U2 any timeout is
recorded **both** as the harness outcome and as a manual "failed proposal / per-node STOP" reclassification, with
the basis, and that no retry occurs.
**MINOR-5 (disk budget).** The census report (`TRACKG_CENSUS_20261117.md` §1) says "the U2 budget cap of 100 GB";
the unit only has "disk <50 GB" as a STOP. Add the 100 GB accounting (per unit and total), the exact filesystems
(Ada home 1.8 T with **131 GiB free**, 93 % used; `/tmp` local), the runs-root and data-root paths, measure
`df`/du before and after, and a no-deletion retention rule for interrupted directories.
**MINOR-6 (raw-record locations).** State that per-run `run_record.json`/`run.log` under `<runs-root>` are preserved
(never deleted) and that the result record gives their paths and sha256 (the result `.md` cannot carry all raw JSON).
**MINOR-7 (gate capture per node).** §2.1 references the U0 three checks but does not require recording the re-run
capture for each node. Add: re-run the U0 gate immediately before launch, record the capture JSON path/sha256 and
UTC, and use the self-excluded `pgrep` form (the U0 result warns a naive `ssh "pgrep …"` matches its own `bash -c`
line — I reproduced that self-match in this review).
**MINOR-8 (environment version record).** §2.4 says "env versions" but not the exact capture: `python -V`, `uv pip
freeze`/`pip list` sha, `torch.__version__`/`torch.version.cuda`, JAX version + `jax.devices()` (Breakout), GPU
name/UUID/driver (`545.23.08`), CPU model, OS/kernel, and the two env paths. Record all in the result.
**MINOR-9 (worktree cleanliness after setup).** Data setup adds untracked `nodes/<node>/data` symlinks (not
gitignored — `git check-ignore` returns nothing) and `__pycache__`. Say "clean at start" means **no tracked
changes** (`git status --porcelain --untracked-files=no` empty, or record the untracked data links), and that a
tracked-file `M/D` is the STOP; record each worktree's tip/cleanliness before each node.
**MINOR-10 (data-setup failure modes).** §3 STOPs list "data setup sha mismatch; missing data/credentials" but not
network/egress failure (HF/Xet, PyPI, OGB, Kaggle) or setup timeout; add them as per-node STOPs with the preserved
setup log.
**MINOR-11 (resumability semantics).** State that the unit's granularity is one node; an interrupted unit re-runs
whole from a new `<runs-root>` (old directory moved aside, not deleted), and that a STOP is not resumed — only
restarted under a new reviewed unit.
**MINOR-12 (smoke run count/duration).** State explicitly that the smoke executes **4 + N** runs (N = 3–5 declared
edits → 7–9 full-budget runs, plus the refused frozen diff) and give the expected per-node wall time and GPU-time, so
the unit's cost is explicit. The raw cost still comes from the baseline only; the other runs are checklist E, and one
node's smoke is within the one-node unit.
**MINOR-13 (result-record completeness).** §2.4's row omits several required fields — see §5 below for the list to
add (env/driver/OS, gate capture, data provenance, runs-root/records, sampler method, timeout classification, disk,
one-node statement).
**MINOR-14 (interpreter selection).** Ada's `python3` is 3.10.12; record how each node's interpreter is selected
(activate the node's env so `python3` on `PATH` is that env's 3.12; state the `PATH`/`VIRTUAL_ENV` for JAX vs torch
runs), or the Python 3.12 mandate and the manifest-reproduction checks silently run on 3.10.

**Items that are correct and should stay:** the per-node Paper-A-first + co-tenancy steps ("every time"), the
GPU-by-UUID invocation, the CPU-only House Prices exception (`--gpu-uuid` may be omitted), full-budget smoke with
seeds 8001, `CHECKLIST_E_PASSED` + one JSON per run, OOM/CPU-fallback/non-passing-checklist-E/kit-failure as per-node
STOPs, the "no card after re-checks" STOP, "no T1 label/sweep", "no noise floor/D21/D28 on Ada", "no other host", "no
deletion", "nothing counted as evidence", and the G.1b-on-L40S division. Note the smoke is a port/checklist-E
verification (not a T1 label run) even though it runs declared edits at full budget — that is within G.0.

## 4. Gaps and risks (VERIFY 4) — answers to the specific questions

- **Kaggle data unavailable → per-node STOP, pending author.** Yes, this is the right disposition: one node per
  unit, no substitute, and no MLGym copy. Make it "pending author (Kaggle train.csv)" with the exact ask (file,
  download date/URL, sha256 to compare with the pin), not a dead end (MAJOR-5).
- **Memory-limit "what enforces it".** A recorded non-enforced string is **not acceptable** as a memory cap: it does
  not satisfy checklist D and does not protect co-tenants. User-level cgroup v2 is available on Ada
  (`systemd-run --user --scope -p MemoryMax=…` works), so use it and record it; otherwise STOP (MAJOR-2).
- **GPU UUID selection / free-VRAM measurement.** UUID selection is right; the gate's "observed footprint" is
  undefined before run 1 — define a pre-run estimate/floor and re-check free VRAM every node (MAJOR-3).
- **Smoke runs multiple full-budget runs (not just baseline).** Yes, 7–9; that is checklist E and gives the baseline
  `elapsed_seconds_info_only`, but VRAM/RAM must be attributed to the baseline run (or labelled as whole-smoke upper
  bounds); the unit stays within one-node granularity (MAJOR-4, MINOR-12).
- **Environment versions/records.** Plan exists; capture is underspecified; environments **not created** yet
  (MAJOR-1, MINOR-8).
- **Data manifest sha.** Required in text, but the manifest's `source` label is MLGym's repo even for a Kaggle
  `--from-file` run — record the actual Kaggle provenance separately (MAJOR-5).
- **Co-tenancy re-check each node.** Present ("every time"), but the footprint basis is the problem (MAJOR-3).
- **Disk ≤100 GB.** Not in the unit; only "<50 GB" STOP. Add the 100 GB cap/accounting (MINOR-5); at review time
  131 GiB free, so there is headroom, but the 100 GB cap must be recorded, not inferred.
- **Failure/triage definitions.** Mostly present (per-node STOPs); add network/data-download failures, timeout
  reclassification, and interrupted-unit rerun semantics (MINOR-4/10/11).
- **Can the unit be executed as written?** **No**: envs/JAX env/data/static-test prerequisites are absent, the
  per-worktree test command as written fails, the memory cap is unenforced, the free-VRAM gate is undefined for run
  1, and one unit authorises eight nodes. All are fixable without changing the frozen kit; see §5.

## 5. Verdict and exact fixes

**NOT ACCEPTED.** Required before execution: **BLOCKING-1** (scope the unit to one named node; separate reviewed
units for the rest) and **MAJOR-1…5** (env step + records; real memory cap; run-1 free-VRAM basis; baseline-attributed
raw-cost sampling; executable House Prices Kaggle `--from-file` path with provenance). Apply the MINORs as text edits
in the same revision; a new review round is enough (no kit bytes change).

**If accepted on a later round, the per-node result record must contain at least:**

1. Unit id/date, `ENGINEERING_ONLY`, "on Ada / RTX 6000 Ada", "no evidence", "no T1 label / no noise floor / no
   D21/D28 on Ada"; the node named by the unit (one node).
2. Node: name, suite, budget (kind/value), node YAML sha256, declared-edit manifest sha256, suite test module sha256.
3. Bytes: harness repo + branch + **tip sha** + base `717ad835`, paper `main`/ops commit, worktree tip/cleanliness
   at start (tracked changes only) and expected untracked `data/` links.
4. Environment: interpreter path/version (3.12.16 via uv), torch `2.6.0` + CUDA build + `torch.cuda.is_available()`,
   JAX env pins/`jax.devices()` for Breakout, `uv pip freeze` shas, driver `545.23.08`, GPU name/UUID, CPU model,
   OS/kernel, CPU list, threads, `AR_TRACKG_DATA_ROOT` path.
5. Paper-A-first gate: U0 result/capture path + sha256, re-run capture path/sha256 + UTC, newest v4 live dir,
   pgrep result (self-excluded form), verdict `clear_*`/`paper_a_live_waiting_for_card:false`.
6. Co-tenancy: GPU UUID, pre-run free/used VRAM, footprint estimate basis (run 1), post-run used, measured peak
   (method/attribution), co-tenant change, decision.
7. Data: exact setup command, data root, `data_manifest.json` sha256, every file sha256, source (Kaggle URL/date/
   bytes/sha vs MLGym pin; manifest `source` caveat for houseprice), no-MLGym-copy confirmation.
8. Run: runs-root path (outside repo, preserved), provisional timeout, run count, baseline run id + record path,
   baseline `elapsed_seconds_info_only` (B1 and B2), peak VRAM (sampler command/interval/attribution), CPU/RAM
   (`/usr/bin/time -v` or aggregate label), checklist-E result + the `CHECKLIST_E_PASSED` line, one JSON line per
   run, `killed_with`, `determinism.not_forced` for the node class (torch vs JAX per the yaml notes).
9. Timeout basis: B1 seconds, timeout = 3 × B1, the manual "timeout = failed proposal" reclassification note, no
   retry.
10. Disk: free before/after, data + runs-root footprints, U2 100 GB cap accounting, no deletion.
11. Static-test commands/results (per worktree) and env install record (MAJOR-1).
12. STOP/pending rows with the preserved paths and the reason; what was not run and why; raw-record locations/shas;
    result file sha256.

## 6. What this review did and did not do

I verified the canonical proposal bytes and line count, the authority rows (including the fact that
`R1-TRACKG-PORT-DECISIONS` lives only at paper `main` `50176481` and not in the worktree HEAD), the merge state of
the three kit branches and the reports/reviews/checklist-F bytes on `50176481`, the three harness worktrees on Ada
(tips, base, cleanliness, addition-only diffs, origin branch tips), the paper checkout on Ada, the Python/uv
versions, the (empty) env state, the absence of JAX env/data/Kaggle, host/GPU/disk/cgroup facts, the
`port_smoke_gpu` CLI and checklist-E semantics, the per-worktree static-test file set, the House Prices
`prepare_data.py` default path/`--from-file` hash pin and manifest source, the House Prices YAML, and the
U0 gate basis (Paper A live dir, finalize marker, branch). I did **not** run static tests, smoke, or any node; did
not test network egress from Ada; did not verify GPU peak-VRAM sampling on the host; did not re-run the U0 gate
script; and did not touch any other user's files/processes. If anything here conflicts with a dated PLAN row, the
PLAN row wins.
