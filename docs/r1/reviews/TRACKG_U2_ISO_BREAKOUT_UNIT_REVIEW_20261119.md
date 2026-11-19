# Independent review — Track G G.0 U2 unit `mlgym_breakout_minatar` (isolated kit, JAX) (19 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-breakout-reviewer`), delegated by the coordinator after the Ada
JAX-environment fix; no involvement in drafting the unit, the JAX fix, the kit update or the five-node campaign.
Read-only: the only file written is this review record (uncommitted). No unit/code edit, no commit/push/delete, no
GPU/U2/census run, no Ada login, no HTCondor/deepthought. One read-only shallow clone of the **published harness kit
branch** was made under `/tmp` (network read only, no repo or Ada write) to verify the tip and the node spec; nothing
was written inside either repository.

**Object under review.** `docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md`, sha256
**`433db1bf2c776b8dde740a9ae0e94b46e8585b1f175bbeae028c3d58d95f4c74`**, **60 lines**, untracked at review time
(mtime `2026-11-19T05:34:48`); status "proposed unit; run only after a fresh independent review accepts it".

**Verdict summary: ACCEPTED — 0 BLOCKING, 0 MAJOR, 14 MINOR.** The unit is a correct one-node `mlgym_breakout_minatar`
U2 raw-cost unit at the level of the accepted five-node pattern: authority/scope, kit identity and both pin roles, the
node-spec values, the JAX environment, the inside-scope cgroup construction and enforcement probe, the exact
`port_smoke_gpu` invocation, GPU co-tenancy/floor, the whole-smoke VRAM upper-bound label, B1/B2 with the 3 × B1 timeout
rule, the 8-executed-plus-refused-diff expectation and the no-retry rule are all present and independently checked
below. The findings are record/evidence gaps of the class the R3 five-unit review treated as MINOR with pre-execution
conditions: the **MLGym CC BY-NC 4.0 / gymnax Apache-2.0 licence and provenance statement is absent**, the **JAX
environment-fix record is an untracked, uncaptured note that the unit does not cite**, and the unit **does not require
a fresh JAX/device/freeze check (or a smoke-entry import check) at launch**. Those, plus a source-wrapping hazard in
the launch command and several result-record fields, must be corrected by conditions C1–C7 below before execution.
This is a conditional acceptance in the R3 sense: the conditions are text/record corrections that change no
procedure, scope, measurement identity, STOP set or kit byte, so no further independent review round is required.
**Execution remains forbidden until C1–C7 are applied.** Acceptance is for this node only, once, with no retry; it does
not authorise autoresearch (C3-blocked), HousePrice (STOP), any other node, a T1/evidence run or another host.

## 1. Authority, method and limits

**Authority read** (all read-only; full shas as verified in this session):

- Published paper main **`de3de54fd22dcdd86215be0924307e36a64ed08b`** (`origin/main`; worktree HEAD `eb65fd8d`,
  merge-base with published main `45fb94cc`). `R1-TRACKG-G0-GO` (`origin/main:docs/r1/PLAN.md:1258`),
  `R1-TRACKG-LICENCES` (`:1269`), `R1-TRACKG-PORT-DECISIONS` (`:1289`), `R1-HARNESS-ISOLATION` (`:1290`); port report
  `origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7 and its review (round 4 ACCEPTED).
- Accepted kit update report `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`, sha256
  **`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`** (committed at HEAD `eb65fd8d`; reviewed
  bytes were `3c3ae74a3788e86f0645e316b7c66392ac8bec45c01b8e0a5f4ed26a01f04bd7`; conditions C-K1…C-K5) and its review
  `docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md`, sha256
  **`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`**, **ACCEPTED** (0 BLOCKING / 0 MAJOR).
- Harness-isolation fix review `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md`, sha256
  **`c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36`**, **ACCEPTED** (condition 6 PASS, condition 7
  BLOCKED/documented; C3 keeps the autoresearch U2 GPU run blocked).
- Server host-check report `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md`, sha256
  **`6a7005098659e56c103d2f74e76f65979cbf39a1b46e24c3e3e168e38cda97d7`** — records
  `envs/jax312/bin/python` as **Python 3.12.16** (`:76`), which corroborates the unit's interpreter claim.
- Accepted five-node U2 unit pattern and review: `docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_{CIFAR10,FMNIST}...`
  (amended revision 3, committed at HEAD; executed-unit sha `82e90b7c…` for mlgym_cifar10) and
  `docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md`, sha256
  **`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`**, **ACCEPTED** with conditions
  (mR1 launch command, mR7 metric names) and residual MINORs mR2–mR10.
- JAX environment fix note `docs/r1/reports/trackg_g0_20261117/JAX_ENV_FIX_20261119.md`, sha256
  **`ad2d139a9b891ebdfedb89ef6056f8aac7491a73d965c2aa6ed74cd9afc1f391`** — **untracked** at review time
  (`git status --short`: `?? …/JAX_ENV_FIX_20261119.md`; mtime `05:34:58`, ten seconds after the unit); 16 lines, no
  captures.

**Method and limits.** Paper review plus independent recomputation from the published kit branch. The kit branch
`mac-trackg-iso-mlgym-20261117` is now published on the harness origin; I read it with a shallow clone under `/tmp`
(read-only) and verified: origin tip **`f07875de79a5a57739227b13e0fd52d31646edaf`** (and the ar/mlab tips
`448f6820…`/`fb6e7d73…`), the node spec, the frozen-file hashes and the committed-file pin. I did **not** log in to
Ada and claim no live-host state: the warm start, the JAX device check, the env freeze content and the running
GPU/co-tenant state are not independently verified here; the unit's launch checks and the record requirements below
are what must capture them. No GPU/U2/census job was started. Severity follows the delegation rule: any MAJOR/BLOCKING
makes the unit NOT ACCEPTED; here there are none.

## 2. Authority and scope — PASS

`unit:3-9` carries exactly the accepted authorities: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed),
`R1-HARNESS-ISOLATION`, `R1-TRACKG-PORT-DECISIONS` (timeout = 3 × census B1; a timeout is a failed proposal, not an
infrastructure retry), the port report §2/§7 by path, and the accepted kit update report/review with the
current-vs-reviewed sha convention (`fe232e2b…`/`3c3ae74a…` plus C-K1…C-K4). ENGINEERING_ONLY, "no
evidence/noise/D21/D28", "no T1", "no HTCondor/deepthought", "no deletion", "no force push", "no cross-node pooling"
are all present. The unit names exactly **one** node (`mlgym_breakout_minatar`) and one suite; no other node is
authorised, and no U3/unisolated/T1 claim is made. This matches `R1-TRACKG-G0-GO` and the accepted five-node scope.
Residual MINORs are M-14 (no "no push", no "no other host", no no-resume wording) — pattern residues the R3 review
already accepted for the five units.

## 3. Kit identity, tip, launch check and pin convention — PASS with MINORs

**Kit identity/tip — verified.** The unit's `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf`
(`unit:13-14`) is the tip the accepted kit update review accepted. The published harness origin now has
`refs/heads/mac-trackg-iso-mlgym-20261117` = `f07875de…` (ar/mlab = `448f6820…`/`fb6e7d73…`), and the shallow clone's
HEAD is `f07875de…`. At that tip I verified the kit's own hashes against the accepted captures:

| file | sha256 at `f07875de` | check |
|---|---|---|
| `third_party/mlgym/configs/trackg/nodes/mlgym_breakout_minatar.yaml` | `b3cedcd6bbb0f306eb6a536037fafbd8e8a374e42f0d30b7b2e104a2ea539f1c` | node spec read below |
| `third_party/mlgym/nodes/mlgym_breakout_minatar/ar_isolated.py` | `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` | = fixed master / accepted kit update §3 |
| `…/LICENCES.md` | `9767de116925fcf410d789c555344a92a38d838176a34943be65bc6dc27be9bc` | matches `pins/new_mlgym.json` |
| `…/requirements_gpu.txt` | `725a25f231f981725b88a699b4962aea9d1f5802a034c1b87f674844aefcae40` | pins `jax[cuda12]==0.4.35` |

**Committed-file pin — independently recomputed.** Using the branch's own spec frozen list (18 committed entries,
including `LICENCES.md`, `policy.py`, `helpers.py`, `evaluate_policy.py`, the four representative edits and the two
superseded manifests), `sha256(json.dumps(files, sort_keys=True))` =
**`cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4`**, which equals the accepted kit update §3
committed-file pin for `mlgym_breakout_minatar` and the captured `pins/new_mlgym.json` files exactly. The unit's
instruction to record the committed-file pin as the census value and the deployed run-record pin separately
(`unit:15-16`) is the correct convention (kit update §3/§10.2; review C-K5).

**Launch check — MINOR M-5.** `unit:13-14` says "(accepted kit update, clean; HEAD==tip at launch)" and `unit:52-54` has
the "wrong/dirty kit" STOP, but it does not state the accepted form: `git rev-parse HEAD` == tip **and**
`git status --porcelain --untracked-files=no` empty. This matters: the mlgym kit worktree is expected to carry
**untracked runtime `data` symlinks** from the earlier per-node setups (kit update §11; the accepted
`u2_iso_mlgym_cifar10…/kit.txt` shows `tracked_dirty_lines=0` with `?? …/mlgym_cifar10/data`), so a "fully clean"
reading would falsely STOP. Condition C4.

**Pin convention — MINOR M-6.** For this node `setup_command` is empty (`yaml:36`), so no `data` symlink is created and
the deployed run-record `frozen_pin_sha256` should **equal** the committed-file pin `cec562e6…`; the kit update's
deployed-vs-committed difference exists only for nodes whose setup links `data/` (kit update §3 deployed-pin note).
The unit's "record both, do not interchange" is safe but inherited from the torch nodes; it should say the two are
expected to be equal here and treat a difference as a data-link/pin anomaly. Condition C4.

## 4. Node-spec values — PASS on four of five; the licence/notice is absent (M-1)

Verified directly from the kit tip (`yaml` lines as cited):

- `metric_name: val_return` (`yaml:44`), `metric_direction: maximize` — the unit's "`val_return`" (`unit:17`) is right;
  the baseline/repeat record `outcome.value` is the validation mean return (`run_fixed_budget.py` writes one
  `AR_METRIC val_return=` line).
- `selection.test_scored: true` (`yaml:64`) with `test_metric_name: test_return` (`yaml:66`) and
  `test_metric_regex: '^AR_TEST test_return=(\S+)$'` — the unit's "test `test_return`" and "sealed `test_return`"
  (`unit:17`, `:48`) are right; the sealed line is only in the run's result channel (the manager view deliberately
  never carries it — `port_support.check_smoke` asserts `"sealed" not in record`).
- `run_budget.kind: steps`, `value: 2000000` (`yaml:56-57`) — "budget 2,000,000 env steps" (`unit:18`) is right, and
  `port_smoke_gpu` runs the baseline/repeat at this **full** budget (`run_smoke(..., budget=None)` loads the spec),
  not at the synthetic test's 17,000-step budget.
- `setup_command: ""` (`yaml:36`) and `external_benchmark.data: none (simulated environment gymnax Breakout-MinAtar)`
  (`yaml:96`) — "no data setup: simulated gymnax Breakout-MinAtar" (`unit:18`) is right.

**MINOR M-1 — licence/notice and provenance are not represented anywhere in the unit.** The node spec declares
`external_benchmark.license: "CC-BY-NC-4.0 (non-commercial; attribution and changes in LICENCES.md)"` (`yaml:95`), and
the frozen `nodes/mlgym_breakout_minatar/LICENCES.md` states the MLGym CC BY-NC 4.0 scope and the gymnax/gymnax-blines
**Apache-2.0** attribution for the PPO/evaluation code (`third_party/mlgym/LICENSE-APACHE-2.0`; port report §3(1)).
The unit's section heading is "Kit / host / **env** / data", whereas the accepted MLGym pattern's heading is
"Kit / host / data / **licence**", and the accepted unit line — `MLGym subtree CC BY-NC 4.0 non-commercial with
notice (R1-TRACKG-LICENCES); …; the gymnax-derived Apache-2.0 parts are not used by this node`
(`U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md:28`) — has no counterpart in this unit, nor is there any licence field in the
result list (`unit:48-51`). This is the one check-2 node-spec value that is **not** correctly represented. Note that a
copy of the torch-node sentence would be **wrong** here: this node *does* use the gymnax/gymnax-blines Apache-2.0
parts (PPO adapted from gymnax-blines), and no external dataset is downloaded. The kit itself carries the licence
text, so this is a record/census/appendix omission, not a licensing defect of the run; by the R2/R3 precedent (m6,
mR8b, C4 in `U2_ISO_RECORD_CORRECTIONS_20261119.md`, which added a licence line to the mlab_cifar10 result) it is a
MINOR — but a **mandatory pre-execution** one. Condition C1.

**MINOR M-7 — "no data setup" vs the accepted reports' "MinAtar data" wording.** The unit's no-data statement is the
correct one (node spec `setup_command: ""`; committed data-prep report
`docs/r1/reports/trackg_g0_20261117/TRACKG_U2_DATA_PREP_20261117.md:30`: "`mlgym_breakout_minatar` has no data setup
(`setup_command` empty); its U2 needs the JAX env"), and the port report §2 states the rollout runs in the CPU-JAX
parent. However, the accepted kit update report says "there is no `data/mlgym_breakout_minatar` tree … fetching the
MinAtar data is required" (§9, lines 290-295) and "Breakout needs its JAX env and data" (§10.4, line 310), and the
accepted ISO results line 29-30 also says "no data". The unit should cite the data-prep report (or the node spec)
next to its no-data claim so the operator does not expect a data tree and the census does not record a stale reason.
No action beyond citation.

## 5. JAX environment — specified, but under-recorded; fresh launch check required (M-2…M-4)

**What is independently consistent.** `unit:21-24` gives `/home/dowling/r1_trackg_20261117/envs/jax312`, Python 3.12.16,
`jax 0.4.35` with the CUDA-12 plugin, the removal of the incompatible `nvidia-cuda-nvcc-cu12` package, the working
`jax.devices()` (8 Ada RTX 6000 devices) and the freeze sha `d33c9612…`; "Do not use `envs/torch312` for this node."
These match the JAX fix note (16 lines: `import jax` failed with `jax 0.4.35` + `nvidia-cuda-nvcc-cu12 12.9.86` through
`jax._src.lib._try_cuda_nvcc_import`; removing only that package fixed it; freeze after fix = **65 lines, sha
`d33c96120c0be3cf20fcb2b9d783ac5366d6b0d3313e6cfe4c90583f89940217`**), the kit pin `requirements_gpu.txt`
(`jax[cuda12]==0.4.35`), the node spec note "`python_env: jax` (separate environment from the torch nodes)" (`yaml:99`),
and the accepted host-check report's `envs/jax312/bin/python` = **3.12.16** (`:76`). `jax.devices()` returning 8 is
consistent with the census host (8× RTX 6000 Ada, `TRACKG_CENSUS_20261117.md:11`). The kit tip includes the accepted
isolation fix `5403392`, whose whole point includes binding the uv venv realpath chain for `envs/jax312` in the worker
sandbox (fix report `:112`), so the unit's use of the post-fix tip is the right one. No torch-env use is authorised.

**MINOR M-2 — the JAX fix record is not cited and is not in the repository.** The only record of the fix is the 16-line
`JAX_ENV_FIX_20261119.md`, which is **untracked** at review time, has **no captures** (no freeze text, no
`jax.devices()` output, no interpreter/version listing, no removal command), and is **not cited by the unit** by path
or sha (`unit:21-24` describes the fix only in prose). The fixed environment is the unit's single gating dependency:
without the capture, an independent reviewer or a later census reader cannot verify the freeze/device state from the
record, and the fix note itself could be lost. This is the mR8-class citation/evidence MINOR of the R3 pattern, but it
must be closed before execution. Condition C2.

**MINOR M-3 — no fresh JAX/device/freeze check is required at launch.** The unit's only launch control is the STOP
"JAX import/device failure" (`unit:52-54`); it does not require the operator to *record* a fresh check (or a fresh
freeze sha comparison) immediately before the smoke. The recorded device check predates the run and the environment is
a shared, mutable venv under `/home/dowling/r1_trackg_20261117/envs/`; a drift (or a package reinstalled between the
fix and the run) must be detectable. Also note the check must be run with the card visible: the launch command
exports `CUDA_VISIBLE_DEVICES=""` for the launcher (correct for the port smoke), so a `jax.devices()` run inside the
masked scope would see CPU only; the fresh check has to be done before the mask (as the fix note did) or in the
worker's GPU-visible context, and recorded. Required check: `envs/jax312/bin/python` version 3.12.16,
`jax`/`jaxlib`/CUDA-plugin versions, `jax.devices()` count/backend (8 GPU), freeze sha == `d33c9612…`, `which python`
= `envs/jax312`, before launch; STOP/record on any mismatch. Condition C3.

**MINOR M-4 — the smoke entry point's import/test dependencies in `envs/jax312` are unverified.** The unit's command
(`unit:32-39`) runs `python -m tests.trackg.port_smoke_gpu`; that module resolves the node's smoke entry by importing
`tests/trackg/test_port_mlgym.py`, which imports `pytest`, and `port_support` imports `yaml`. The node's pinned
`requirements_gpu.txt` (the env's declared pins) contains **neither pytest nor the harness's dev extra**; the
torch312 freeze used for the accepted five-node smokes does contain `pytest==9.2.0` (captured `env_freeze.txt:53`),
but the JAX env's 65-line freeze is not captured, so whether the smoke can even import in `envs/jax312` is unverified.
If pytest is absent, `port_smoke_gpu` fails before any run with "no SMOKE entry for mlgym_breakout_minatar", and a
later `pip install pytest` would silently change the freeze sha. Required: a recorded pre-launch dry-run under
`envs/jax312` with `PYTHONPATH=src`, e.g.
`python -c "from tests.trackg import port_smoke_gpu as p; print(p.smoke_entry('mlgym_breakout_minatar'))"` (and
`python -c "import tests.trackg.test_port_mlgym"`), plus the resulting freeze sha; if a test-only dependency has to be
added, record the new 65+-line freeze and say so. Condition C3.

## 6. Isolation and cgroup — PASS (construction and probe are the accepted ones)

`unit:31-41` is the accepted construction: the outer
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`, with `CG` and
`AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG` computed **inside** the scope, `echo scope_cgroup=$AR_TEST_CGROUP_PARENT`,
`cd <kit worktree root>`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, the JAX env first on `PATH` with `VIRTUAL_ENV`,
`CUDA_VISIBLE_DEVICES=""` for the launcher and `taskset -c <cpus>`; the `--memory-limit` value is on one line and its
text equals the accepted `smoke_one.sh:35` and the captured records' `limits.external_limit`
(`"external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)"`). The memory probe
(`memory.max` 8G / `memory.swap.max` 0, mismatch = STOP, `unit:40-41`), the runs-root outside the repository, and the
`CHECKLIST_E_PASSED` + 8 executed + refused frozen diff expectation (`unit:26-27`) are all the accepted requirements.
The 8-executed count is verified against the kit code: `port_smoke_gpu` runs baseline, a frozen-path diff (refused,
`executed:false`), the broken diff, the first edit, then the four declared edits and a second baseline (B2) — 8
executed records plus the refused `s001`, and for this node `SMOKE["mlgym_breakout_minatar"]` has `make=None,
files=[]`, so the no-data path is exercised (the `data` symlink check is skipped exactly because `make is None`).
`isolation.effective: true`, `waivers == {}`, `exceptions == []` are achievable for this node (its spec's isolation
block has no exception and the kit smoke runs as non-root `dowling`; the accepted `smoke_one.sh` shows the same).

**MINOR M-9 — the command is source-wrapped inside the single-quoted `bash -c` script.** `unit:32-39` breaks the
script across source lines at places that are command-internal: line 33 ends `&& export` and line 34 begins
`AR_TEST_CGROUP_PARENT=…`; line 34 ends `&& export` and line 35 begins `PYTHONPATH=…`; line 37 ends `--gpu-uuid <UUID>`
and line 38 begins `--cpus <cpus> …`. A faithful copy of the displayed text makes the inner shell run `export` with no
arguments, then an assignment-only `AR_TEST_CGROUP_PARENT=… && …` that does **not** export the variable (so
`port_support.limits()` sees no cgroup → `no_cgroup` waiver → `effective:false` → the unit's own STOP), and splits the
`port_smoke_gpu` argument list (`--cpus` would be a new command). The amended accepted unit
(`U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md:38`) and `smoke_one.sh` give the invocation as one line (or with proper
multi-line form where each line is a complete command / backslash continuation). Give the launch command on one line
or as a script; this is the mR1(e) class of condition, not a construction error. Condition C3.

**MINOR M-10 — probe values and read path.** `unit:40-41` says read `$AR_TEST_CGROUP_PARENT/memory.max` "(8G)" and
`memory.swap.max` "(0)". The file content is `8589934592` (the `8G` is the systemd property suffix) and `0`; and
`$AR_TEST_CGROUP_PARENT` is set only inside the scope's shell, so the launching shell must use the echoed
`scope_cgroup=…` path (the unit does echo it — good) — state both explicitly (R3 mR1(c)/(d)). Condition C3.

## 7. Command, GPU, timeout and record — PASS with MINORs

**Exact invocation.** `unit:32-39` uses `python -m tests.trackg.port_smoke_gpu --node mlgym_breakout_minatar
--gpu-uuid <UUID> --cpus <cpus> --memory-limit "…" --runs-root <outside-repo>/u2_iso_mlgym_breakout_minatar_<UTC>
--provisional-timeout 1800`, with `taskset -c <cpus>`, the env's `bin` first on `PATH`, `VIRTUAL_ENV`, `PYTHONPATH=src`
and `CUDA_VISIBLE_DEVICES=""`; `--gpu-uuid` is required by the smoke for any non-CPU-only node
(`port_smoke_gpu.py:59-60`), `--cpus/--memory-limit/--runs-root` are required, and the JAX env substitution is the
port report §7 step 3 instruction ("Breakout has a separate JAX environment"). Omitting `AR_TRACKG_DATA_ROOT` is
correct for this node (no data setup; the runner does not consume that variable), unlike the torch nodes. The
accepted attempt-2 records and `smoke_one.sh` are matched element-for-element. MINOR M-9 above (source wrapping) and
m11 below (timeout wording) are the only command-text findings.

**GPU floor/co-tenancy (`unit:42-44`).** ≥ 8 GiB free, no other user's compute app, before/mid/after `nvidia-smi` and
compute-app census, "no unrecorded card switch", and a 1 s
`nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` whole-smoke sampler with its maximum
explicitly labelled a **whole-smoke upper bound, not a per-run peak** — all present. Because this is the first GPU run
of the JAX worker, the baseline has no measured footprint; condition C6 requires the record to carry the three-point
census and the sampler fields. Residual MINOR M-13 (accepted mR9): the 8 GiB floor's basis is unstated, and "no
unrecorded card switch" permits a *recorded* switch; add the basis and "no switch from the launch card" + a mid-run
contamination rule (free VRAM below baseline peak + 2 GiB, or a new co-tenant in the baseline window → STOP/record).
The port report §6 item 7 flags this node's GPU worker + CPU-JAX parent as untested; the unit's "JAX import/device
failure" STOP and the node-spec `AR_INFRA` worker check are the right fail-closed controls, and the port report/unit
correctly treat a failure as a failed proposal, not an infrastructure retry.

**Timeout (`unit:46-47`).** The unit records that the kit update's Breakout smoke did not run and that there is **no
accepted pre-run baseline** — honest and correct (kit update §9; the JAX env was broken then). It requires B1/B2 and
the 3 × B1 node timeout with no timeout/OOM retry. MINOR M-11: "node timeout = 3 × B1 (provisional 1800 s)" conflates
two things — the 1800 s is the smoke's **provisional per-run timeout** for the measuring runs
(`limits.provisional_timeout_seconds: 1800.0`, `timeout_factor: 3.0` in the accepted records) while the census node
timeout is 3 × measured B1; state both, as the amended accepted unit does (`:49-51`), and say a timeout/OOM is the
proposal's failure.

**Result/captures (`unit:48-51`).** B1/B2 `elapsed_seconds_info_only`, `val_return` (`outcome.value`), the sealed
`test_return`, all edit outcomes, labelled whole-smoke CPU/RAM, GPU census, cgroup probe, sampler fields, env freeze,
data/none, kit tip + both pins, gate, disk, isolation fields and one-node/no-evidence/no-noise statements are all
required, and the captures go under `docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_breakout_minatar_<UTC>/` with
`SHA256SUMS` and preserve. MINOR M-12: the list is thinner than the accepted result standard (R3 mR4–mR6 and the
accepted result layout) — it omits host/boot/driver, the gate JSON path/sha/UTC and newest `live_*` check, per-run
`run_record.json`/`run.log` paths+sha, `killed_with`, `determinism.not_forced` (for this JAX node the node-spec notes
give the `torch_absent` reason), one JSON line per run, the node-spec sha + representative-edit manifest sha, the
sealed-value source (`result_channel.txt`, not the manager view), the result-file name/path/sha, `time -v`, the
record-verification outputs, and the executed amended unit bytes (the five accepted results preserve them under
`unit/`; S10 of `U2_ISO_RECORD_CORRECTIONS_20261119.md`). Carry the accepted standard in the result record. Condition
C6.

## 8. Facts checked independently (summary)

| Unit claim | Independent check | Result |
|---|---|---|
| kit branch @ `f07875de…`, clean, HEAD==tip | published harness origin head = `f07875de…`; kit tip files match captured pins; node spec/frozen hashes match | correct |
| committed-file pin `cec562e6…` (census value) and deployed pin separately | recomputed pin from the tip's own 18 frozen entries = `cec562e6…` = kit update §3 = `pins/new_mlgym.json` | correct (see M-6) |
| `val_return`, sealed `test_return`, 2,000,000 env steps, no data setup | node spec `yaml:44,64,66,56-57,36,96`; `run_fixed_budget.py` writes `AR_METRIC val_return=`/`AR_TEST test_return=`; `port_smoke_gpu` runs at the full spec budget | correct |
| CC BY-NC 4.0 licence/notice and Apache-2.0 provenance | node spec `yaml:95` + `LICENCES.md`; absent from the unit | **not represented — m1** |
| `envs/jax312`, Python 3.12.16, jax 0.4.35/CUDA-12, nvcc removal, 8 devices, freeze `d33c9612…` | matches the JAX fix note; `requirements_gpu.txt` pins `jax[cuda12]==0.4.35`; accepted host-check report records jax312 = Python 3.12.16; the device result and freeze content are uncaptured | specified correctly; record gap M-2/M-3 |
| isolation: inside-scope `CG`/`AR_TEST_CGROUP_PARENT`, 8G/0 probe, one-line `--memory-limit`, runs-root outside, `effective:true`/waivers {}/exceptions [], `CHECKLIST_E_PASSED` + 8 executed + refused diff | matches accepted `smoke_one.sh`/records; 8-executed count verified from `port_smoke_gpu.py`+`SMOKE` (baseline, broken, E1, E1–E4, B2; `s001` refused) | correct (M-9/M-10 on the text) |
| exact `port_smoke_gpu` invocation, taskset/cpus, GPU floor/co-tenancy/1 s sampler/whole-smoke upper bound, B1/B2, 3 × B1, no retry, captures/SHA256SUMS | matches accepted attempt-2 invocation and records; sampler label present; no retry stated | correct (M-9/M-11/M-13) |
| one node only, ENGINEERING_ONLY, no evidence/noise/T1/HTCondor/deletion/cross-node | `unit:3-9,13` | correct (M-14 wording) |

## 9. Findings (all MINOR; no BLOCKING, no MAJOR)

| ID | Severity | Unit lines | Finding |
|---|---|---|---|
| M-1 | MINOR (mandatory before execution) | `unit:11-27`, `:48-51` | MLGym CC BY-NC 4.0 notice and the gymnax/gymnax-blines Apache-2.0 provenance are not represented; a template copy would be factually wrong for this node. Add the licence/provenance line and a result field (R1-TRACKG-LICENCES; port decision (1); `LICENCES.md`). |
| M-2 | MINOR (mandatory) | `unit:21-24` | The JAX fix record (`JAX_ENV_FIX_20261119.md`, sha `ad2d139a…`) is untracked, uncaptured and uncited. Commit it with the freeze/device/interpreter captures and cite it by path+sha in the unit. |
| M-3 | MINOR (mandatory) | `unit:21-24`, `:52-54` | No recorded fresh launch check: `jax`/`jaxlib`/plugin versions, `jax.devices()` 8/GPU (outside the `CUDA_VISIBLE_DEVICES=""` mask or in the worker context), freeze sha == `d33c9612…`, `which python` = jax312; STOP on mismatch. |
| M-4 | MINOR (mandatory) | `unit:21-24`, `:37` | The smoke entry point's import/test deps in `envs/jax312` are unverified (`test_port_mlgym` imports `pytest`; not in `requirements_gpu.txt`; freeze uncaptured). Record the `smoke_entry` import dry-run and the resulting freeze. |
| M-5 | MINOR | `unit:13-14`, `:52-54` | State the accepted launch check: `git rev-parse HEAD` == `f07875de…` and `git status --porcelain --untracked-files=no` empty (untracked runtime `data` links permitted — they exist in the mlgym kit). |
| M-6 | MINOR | `unit:15-16` | For this no-data node the deployed run-record pin should equal the committed-file pin `cec562e6…`; record both full values and treat a difference as a data-link/pin anomaly (do not hardcode). |
| M-7 | MINOR | `unit:17-18` | Cite the node spec / data-prep report for "no data setup"; the accepted kit update report §9/§10.4 and ISO results still say "no data"/"MinAtar data" — note the stale wording so no data tree is expected. |
| M-8 | MINOR | `unit:19` | Paper A gate is too vague: add the exact command (`paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`), `clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`, and the captured JSON/UTC immediately before launch (accepted pattern `:20-22`; R3 mR5). |
| M-9 | MINOR | `unit:32-39` | The command is source-wrapped inside the single-quoted `bash -c` script; a literal copy splits `export` from its assignment and splits the argument list. Give it on one line (or as a script) like the amended accepted unit `:38` / `smoke_one.sh`. |
| M-10 | MINOR | `unit:40-41` | State the expected probe contents `8589934592` / `0` and that they are read from the echoed `scope_cgroup=` path (the launcher does not carry `$AR_TEST_CGROUP_PARENT`). |
| M-11 | MINOR | `unit:46-47` | Separate the smoke's provisional 1800 s per-run timeout from the census node timeout = 3 × measured B1; record both and the no-retry rule (accepted pattern `:49-51`). |
| M-12 | MINOR | `unit:48-51` | Result/capture list omits the accepted standard fields (host/boot/driver, gate JSON path/sha/UTC, per-run record/log paths+sha, `killed_with`, `determinism.not_forced`, one JSON line per run, node-spec/representative-edit shas, sealed-value source, result-file path/sha, `time -v`, record verification, executed-unit bytes, SHA256SUMS). |
| M-13 | MINOR | `unit:42-44` | 8 GiB GPU floor basis unstated and "no unrecorded card switch" permits a recorded switch; add the basis and "no switch from the launch card"/mid-run contamination rule (accepted mR9). |
| M-14 | MINOR | `unit:8`, `:52-54` | Scope/STOP residues (accepted mR10): "no push" (not only "no force push"), no explicit "no other host" beyond HTCondor/deepthought, no no-resume statement, STOPs omit "other users would be disturbed" and an env-freeze mismatch, disk threshold without the 100 GiB cap/filesystem accounting. |

## 10. Conditions

All conditions are text/record corrections; none changes the procedure, scope, measurement identity, STOP set or kit
byte (the R3 precedent for its mR1/mR7 conditions). **No execution until C1–C5 are applied to the unit/launch notes;
C6–C7 are satisfied in the result record.**

- **C1 (M-1, mandatory).** Add the licence/provenance line: MLGym CC BY-NC 4.0 non-commercial with notice
  (`R1-TRACKG-LICENCES`); PPO/evaluation adapted from gymnax/gymnax-blines under Apache-2.0 (this node **uses** those
  parts); no external dataset (simulated gymnax Breakout-MinAtar); cite `nodes/mlgym_breakout_minatar/LICENCES.md` and
  the node spec. Add a licence/provenance field to the result list and the census row/appendix.
- **C2 (M-2, mandatory).** Commit the JAX env fix record with the captured evidence (the 65-line `uv pip freeze`,
  sha `d33c9612…`; `envs/jax312` interpreter/version; `jax`/`jaxlib`/CUDA-plugin versions; the
  `nvidia-cuda-nvcc-cu12` removal command; `jax.devices()` 8 GPU) and cite it by path+sha in the unit.
- **C3 (M-3/M-4/M-9/M-10, mandatory).** Before the smoke, record: the fresh JAX/device/freeze check (M-3), the
  `smoke_entry` import dry-run in `envs/jax312` (M-4) and any test-only dependency added to the env (with the new
  freeze sha), and give the launch command on one line with the probe values `8589934592`/`0` read from the echoed
  `scope_cgroup` path (M-9/M-10). Any mismatch/import failure = STOP, not a reason to run.
- **C4 (M-5/M-6/M-7/M-8).** State the exact tracked-clean + `HEAD == f07875de…` launch check, the pin equality/STOP
  rule for this no-data node, the data-prep citation for "no data", and the exact Paper A three-check command/criteria
  and capture.
- **C5 (M-11/M-13/M-14).** Correct the provisional-vs-3×B1 wording; add the 8 GiB floor basis, no-switch/contamination
  rule; add "no push", "no other host", no-resume, the other-users/env-freeze STOPs and the disk cap/footprints.
- **C6 (M-12).** The result record must carry the full accepted result/capture standard above (including host/driver,
  gate JSON+UTC, per-run records/logs with shas, `killed_with`, `determinism.not_forced` with the JAX `torch_absent`
  reason, one JSON line per run, node-spec sha + representative-edit manifest sha, `val_return`/sealed `test_return`
  from the result channel, env freeze, both pins, cgroup probe bytes, three-point GPU census, sampler
  command/interval/output/max labelled whole-smoke upper bound, `time -v`, disk before/after, isolation fields,
  `CHECKLIST_E_PASSED` + 8 executed + refused diff, one-node/no-evidence/no-noise, no retry), preserve the executed
  amended unit bytes under the result directory, and write `SHA256SUMS`.
- **C7 (execution rule).** One smoke only for this node, no retry; no other node or host; no T1/evidence/noise/D21/D28
  use; no deletion/push; captures preserved. A timeout/OOM or a non-effective record is a STOP, not an
  infrastructure re-run. Acceptance of this unit does not authorise autoresearch (C3-blocked), HousePrice (STOP),
  any other node or a cross-node comparison.

## 11. Verdict

**ACCEPTED — 0 BLOCKING, 0 MAJOR, 14 MINOR, conditional on C1–C7.** The unit's scope, kit identity/tip and both pin
roles, node-spec values (except the absent licence/notice — M-1), inside-scope cgroup construction and enforcement
probe, exact `port_smoke_gpu` invocation for the separate JAX environment, GPU floor/co-tenancy and the 1 s
whole-smoke upper-bound sampler, B1/B2 with the 3 × B1 rule, the 8-executed-plus-refused-diff expectation, captures
and the no-retry rule are all correct and independently checked. The JAX env fix is specified coherently in the unit
but is under-recorded and needs a fresh launch check; the licence/notice is missing; and the command/result text
needs the corrections above. These are pre-execution MINOR conditions in the accepted five-unit workflow, not a new
MAJOR/BLOCKING. **Do not execute until C1–C5 are applied and recorded; the result must satisfy C6–C7.**

## 12. Attestation and command record

This review is the only file written (uncommitted). I did not run the smoke or any GPU/U2/census job, did not edit
the unit or any code, did not commit/push or delete any repository, unit, evidence or capture file, did not log in
to Ada and did not touch HTCondor or
deepthought. Read-only operations (19 Nov 2026, Europe/Berlin): `sha256sum` of the unit (`433db1bf…`), the kit
update report (`fe232e2b…`), its review (`d8c68f9f…`), the fix review (`c8e468c7…`), the host-check report
(`6a700509…`), the JAX fix note (`ad2d139a…`) and the R3 review (`99daf16d…`); `git status`/`git log`/`git show`/
`git rev-parse origin/main` in the paper repo (`origin/main` = `de3de54f…`, HEAD = `eb65fd8d…`); `git ls-remote origin`
in the harness repo (kit-branch tips) plus a read-only shallow clone of the harness origin
(`git clone --depth 1 --branch mac-trackg-iso-mlgym-20261117`) and its tip
`f07875de79a5a57739227b13e0fd52d31646edaf`, node spec, frozen-file shas and recomputed pin `cec562e6…`; reads of the
accepted five-node units and R3 review, the accepted kit update report/review and captures
(`SHA256SUMS`/`pins`/`smoke`/`scripts/smoke_one.sh`), the port report §2/§3/§6/§7, the JAX fix note and the host-check
report; `python3` recomputation of the node spec's frozen files/pin and of the smoke campaign's executed-record count.
No live-host state is claimed beyond what the accepted records and the published kit branch show.
