# Independent review — worker-run PATH failure fix + worker-success gate (S2-C2 / S2-C3 driver / S2-C3b)

**Reviewer role:** fresh, independent, read-only reviewer (not the author, not the executing agent). I read the
three branches, the pinned B2 harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, the image build, the frozen
sweep-1 ledgers, and the S2-C4/32k-smoke records. I ran only the units' own synthetic test suites. **No job or
server was started, no `condor_*` command was run, nothing was submitted, no git write was made.** The only file
this review creates is this uncommitted review file.

**Date/time of review:** 16 November 2026, 23:50–00:20 CET (Europe/Berlin).

**Units and exact tips** (worktrees under `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/`, all
clean):

| unit | file under review | requested pin | **exact branch tip** | tests |
|---|---|---|---:|---:|
| `sweep2-main-20261116` | `sweep2/s2_c2_lib.py` (collector/liveness env + `collection_gates` worker gate) | `77c6394a` | **`c1a28b10`** (fix `77c6394a` + two docs commits `49499ae0`, `c1a28b10`) | 36 passed |
| `s2c3-driver-fix-20261116` | `sweep2/s2_c3_replay.py` (driver PATH + `worker_audit`) | `ed974238` | **`ed974238`** | 176 passed |
| `s2c3b-fix-20261116` | `sweep2/s2_c3b_lib.py` (liveness PATH + worker audit) | `8df3f5a8` | **`8df3f5a8`** | 129 passed |

> The requested `77c6394a` is the fix commit, not the branch tip: `c1a28b10` is `77c6394a` + two docs-only commits.
> Nothing in the reviewed code differs between `77c6394a` and `c1a28b10` (verified by `git show --stat`).

| file | lines | SHA-256 |
|---|---:|---|
| `sweep2/s2_c2_lib.py` @ `c1a28b10` | 934 | `930624aaeec1a85aed09a086451e39c82ababb39068bd25866c77bd165f03ce7` |
| `r1/tests/htcondor/test_s2_c2_unit.py` @ `c1a28b10` | 382 | `e8dd42f04dcb4caa766de08aa3055695970b0c0548d706fdc6d3c68fdf0eac50` |
| `sweep2/s2_c3_replay.py` @ `ed974238` | 2000 | `aa15cc1bc5a82fbaaca6cbf3bf5fb3e3791a90ba2fdaea37640d9384537df9c6` |
| `sweep2/s2_c3b_lib.py` @ `8df3f5a8` | ~1360 | `67cdf322cb25cf1946c5665b6f7bf07d6c9e36fa899d5403cfe09e4f421e6497` |

Tests were run with the existing venv
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/sweep2-cluster-20261116/.venv-test/bin/python`
(Python 3.13.4), `-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`.

---

## 1. Diagnosis — is the PATH / harness-venv explanation correct?

**Yes.** The diagnostic claim reproduces from the pinned sources without needing the sealed logs:

- `autoresearch/worker/local_worker.py` @ `a3fedbb`: `_run_command` runs `subprocess.run(cmd, shell=True,
  cwd=self._node_root, capture_output=True, text=True, timeout=…, env=env)` with
  `cmd = node_spec.run_command` and `env = seed_environment(self._train_seed, self._split_seed)`. `seed_environment`
  (`autoresearch/worker/seeds.py`) is literally `dict(os.environ)` plus `AR_TRAIN_SEED`/`AR_SPLIT_SEED`; it neither
  prepends a venv nor normalises `PATH`.
- The pinned node registry (`configs/nodes/*.yaml` @ `a3fedbb`) uses `run_command = "python3 train.py"` for
  `digits_mlp`/`tabular_mlp` and `"python3 train.py --config config.yaml"` for every OpenML node. Therefore the only
  thing that selects the interpreter is the inherited `PATH`.
- The pinned node benchmark modules (`nodes/<node>/benchmark.py`) import `numpy`/`sklearn`; the image builds
  `/opt/r1/envs/harness` with `UV_PROJECT_ENVIRONMENT=/opt/r1/envs/harness uv sync --frozen --extra dev --python 3.13`
  and the Dockerfile asserts `numpy, sklearn, pandas, pytest` import from `/opt/r1/envs/harness/bin/python`
  (`r1/scripts/htcondor/docker/Dockerfile` @ `htc-image-v2-20261115`). The GPU image `ENV PATH` is
  `/opt/uv:/opt/r1/llama/bin:$PATH` — **it does not contain `/opt/r1/envs/harness/bin`**. The job shell
  (`sweep2/s2_c2_job.sh`) invokes the wrapper with the absolute `/opt/r1/envs/harness/bin/python` but never exports
  that bin directory. The collector then builds `dict(os.environ, …)`, which inherits the container `PATH`; its
  workers' `python3 train.py` resolves to the container system Python (no numpy) and fails at import in ~0.1 s.

**Repo evidence (corroborating, not the literal traceback):**
`docs/r1/reports/sweep2_20261116/s2c4_run_20261116/job_record_{none,append_only_summary}.json` (16k pilot) each show
10 `run_command finished in 0.0–0.1s; success=False metrics={}` lines; the 32k smoke records
(`smoke_20261116/job_record_*.json`) each show 9 more, while `gates` passed with `root_failures: 0` and no worker
statistics. **Verification limitation:** the literal `ModuleNotFoundError: No module named 'numpy'` line lives only in
the sealed `/ceph/.../s2smoke-20261116-a/` `work.tar`/`out.tar`, which is not copied into the repo and is not
readable from this Mac checkout; I could not re-open it without job/server access. The diagnosis nevertheless
follows mechanically from the pinned code, and the observed signature (sub-0.1 s, exit nonzero, empty metrics,
container-only difference vs sweep-1) is uniquely explained by the interpreter/venv selection.

**Does the fix cover the real worker path (not just the outer process)? Yes — all four paths:**
1. C2 chunk collector: `run_job` → `_worker_env` → `subprocess.run(collector, env=env)` (`s2_c2_lib.py:781-784`);
   the harness worker inherits it through `seed_environment(os.environ)`. **Fixed.**
2. C2 D28 liveness kind: `run_liveness` → `_worker_env` (`s2_c2_lib.py:711-715`) → `r1.liveness` → `e1b_collect` →
   `LocalWorker`. **Fixed.**
3. S2-C3 driver: `campaign_env` now sets `PATH=_worker_path()` (`s2_c3_replay.py:1231-1243`), used for the
   shadow-runner `Popen` that runs `r1.exam.campaign` → `B1IntegrityWorker` → harness worker. **Fixed.**
4. S2-C3b: `run_liveness_job` env now prepends the venv bin (`s2_c3b_lib.py:1226-1231`) → `r1.liveness` → workers.
   **Fixed.**

The outer job-wrapper processes already use the absolute `/opt/r1/envs/harness/bin/python`; the repair
is correctly applied at the worker-parent boundary rather than only to the outer script.

**Is prepending the venv bin sufficient? Mostly yes, with one hardening gap.** A `uv`-created venv has
`bin/python`, `bin/python3` and `bin/python3.X` symlinks (verified on the local `uv` 0.11.2 `_harness_venv`; the image
is built with `uv 0.13.6`), so prepending `/opt/r1/envs/harness/bin` makes `python3 train.py` use the venv interpreter
whose site-packages contain numpy/scikit-learn — that is sufficient. No additional `PYTHONPATH` is needed for node
imports: the node directory is the shell's `cwd`, `benchmark.py` is beside `train.py`, and the collector/liveness
processes themselves are run with the absolute venv interpreter + `PYTHONPATH=<paper checkout>`. Thread caps
(`OMP`/`OPENBLAS`/`MKL`), `AR_HARNESS_ROOT`, `LLAMACPP_BASE_URL` and the `LLAMACPP_CACHE_PROMPT` removal are all
preserved by `_worker_env`.

**Finding m1 (minor, C2/C3 hardening):** `_worker_env` only requires *either* `bin/python3` *or* `bin/python`, and
the second `elif (venv_bin / "python").is_file()` branch is dead code (`s2_c2_lib.py:513-523`); the driver
`_worker_path` has the same `python3 or python` condition. If an image venv ever lacked the `python3` name, the code
would not STOP, would still prepend the bin dir, and `python3 train.py` would silently fall back to the system
Python — the exact bug again. The guard should require `bin/python3` to exist and be executable (or verify
`shutil.which("python3", path=env["PATH"])` resolves inside the venv).

## 2. Sweep-1 baseline — independently recomputed

I recomputed the baseline from the frozen sweep-1 corpus on `main`, not from the comment:
`results/r1/evidence/C3_sweep_{append_only_summary_20261027T154834Z,none_20261027T224356Z}/provenance/ledgers/roots/*/root_trials.jsonl`
(288 files = 144 root campaigns per memory mode; 16,384 context run, main corpus).

| memory mode | roots | trials | `execution_status=success` | failed `invalid_config` | failed `proposal_precondition_failed` |
|---|---:|---:|---:|---:|---:|
| append_only_summary | 144 | 2,933 | 2,555 | 325 | 53 |
| none | 144 | 2,880 | 2,732 | 148 | 0 |
| **total** | **288** | **5,813** | **5,287** | **473** | **53** |

- **5,287 / 5,813 = 0.90951316 → 90.95 % success, 9.0487 % failure is exactly correct.** The +5 pp cap is
  `1 − 5287/5813 + 0.05 = 0.14048684` (14.05 %), also correct arithmetic.
- Every success has non-empty `parsed_metrics`; there are **no successful-with-empty-metrics trials and no
  `runtime_error` trials** in sweep-1 (all 526 failures are the two categories above).
- No sweep-1 campaign has zero successes; the minimum campaign success rate is 0.35 (7/20).

**The threshold quantity is the right one (non-success / trials), but the population is wrong (BLOCKING 1).**
The C2 unit is a *single* (node, memory mode) chunk: `spec.example.json` `collector.node = digits_mlp`,
`memory_mode = append_only_summary`, `instances = 18` (2 for the pilot), `runs = 20`, and `S2_C2_UNIT.md` says one job
= one (node, memory mode) chunk. Sweep-1 is strongly heterogeneous per node/mode, so comparing a one-node chunk to a
pooled 8-node × 2-mode baseline is not the "sweep-1 rate" for that chunk:

| node | append_only fail | none fail | pooled fail | pooled cap 14.05 %? |
|---|---:|---:|---:|---|
| digits_mlp | 9.55 % (38/398; all `proposal_precondition_failed`) | 0.00 % | 5.01 % | ok |
| tabular_mlp | 2.96 % | 0.00 % | 1.50 % | ok |
| openml_breast_w | 11.67 % | 0.00 % | 5.83 % | ok |
| openml_credit_approval | 5.83 % | 7.50 % | 6.67 % | ok |
| openml_sonar | 9.17 % | 0.00 % | 4.58 % | ok |
| openml_wdbc | 9.62 % | 0.00 % | 4.83 % | ok |
| **openml_climate** | **24.17 %** | **17.22 %** | **20.69 %** | **breaches** |
| **openml_ionosphere** | **30.83 %** | **16.39 %** | **23.61 %** | **breaches** |

Consequences (exact binomial, one-sided, using the sweep-1 rate as the healthy expectation and the implemented cap
`failure_rate > 0.140487`):

| chunk (n = instances × 20 trials) | healthy sweep-1 fail rate | P(gate falsely STOPs a healthy chunk) |
|---|---:|---:|
| full chunk (n=360) ionosphere append_only | 30.83 % | ~1.000 |
| full chunk (n=360) climate append_only | 24.17 % | ~1.000 |
| full chunk (n=360) climate none | 17.22 % | 0.949 |
| full chunk (n=360) ionosphere none | 16.39 % | 0.889 |
| **2-instance 32k smoke (n=40) digits append_only** | 9.55 % | **0.178** |
| 2-instance 32k smoke (n=40) digits none | 0.00 % | 0.000 |

So as written the gate will systematically STOP four of the sixteen full chunks even when the workers are exactly
sweep-1-healthy, and the queued re-measurement smoke has an ~18 % chance of a spurious STOP on its `append_only`
job (the `none` job is safe). This is not a fail-closed guard on a broken system; it is a guard that cannot
distinguish "normal sweep-1 invalid-config rate on a hard node" from "worker crash", because it mixes node
populations and does not account for n = 40 sampling noise. **The baseline must be per (node, memory_mode)**
(or at minimum per node), and the small-n cap needs an exact-binomial or count-headroom rule (e.g. require the
observed failure count to exceed both the per-chunk expected count and `+2σ`, or simply require `n ≥ 100` for the
rate test and let the 2-instance smoke use the zero-success/no-metrics/`runtime_error` checks only).

**Should `invalid_config` / `proposal_precondition_failed` count as worker failures?**
- `proposal_precondition_failed` records carry `extra.worker.worker_skipped = true` and a structured-edit
  precondition message (`"structured edit precondition failed for HIDDEN_UNITS: expected 2048, found 4096"`): the
  worker **did not run**. Counting these as worker failures is wrong for a worker-health gate; they are
  control-plane/proposal failures. They are also the whole of digits_mlp's `append_only` 9.55 % and thus the direct
  cause of the smoke false-STOP risk.
- `invalid_config` records are real worker executions (`worker_failure_message: "exit code 2"`, the node rejected the
  edited configuration). They may legitimately count as worker-run failures, but they are node-specific and must be
  compared against the same node's sweep-1 rate, not the pooled rate.
- Neither is an infrastructure failure. The observed numpy bug maps to `failure_category=runtime_error` (worker ran,
  nonzero exit, no `FAILURE_CATEGORY=` line in the log), and sweep-1 has **zero** `runtime_error`. A cheap
  `runtime_error` sub-gate (`any runtime_error > 0`, or rate > 0) would catch this exact bug class sharply and with
  essentially no invalid-config false positives. This should be added alongside (not instead of) the author's
  requested formula.

## 3. Gate semantics

**What is implemented (C2, `s2_c2_lib.py:594-672`):**
- `worker` statistics per campaign from `work/roots/*/root_trials.jsonl`: trials, successes, successes-with-metrics,
  failures by category, success/failure rate, sweep-1 and max rates, written into `out/collection_checks.json`.
- STOP on **zero successful runs in any campaign** (`zero_success`) → `out/worker_failure.json` then `Stop`.
- STOP when the job has **no successful run with metrics** (`successful_with_metrics == 0`) → same file then `Stop`.
- STOP when **failure rate > 14.05 %** → same file then `Stop`.

**Ordering / evidence persistence — correct.** `collection_checks.json` is written before any gate raises;
`worker_failure.json` is written before each worker STOP; `run_job` catches the `Stop` (`s2_c2_lib.py:801-805`), sets
`record["gates"] = {"status": "FAIL", …}` and calls `_stop_with_evidence`, which writes `job_record.json`, then
`out.tar`, `work.tar` and `SHA256SUMS` **before** re-raising (`s2_c2_lib.py:580-590`). `worker_failure.json` is
inside `out/` and therefore inside `out.tar`, so the STOP is transferred and sealable. The existing
`test_stop_with_evidence_persists_record_and_tars` covers the mechanism generically.

**Slip-throughs / gaps (see findings):**
1. **Success status with empty metrics can slip through.** The harness sets
   `execution_status = SUCCESS if worker_result.success else FAILED` (`campaign.py:2396`), and `worker_result.success`
   is only `returncode == 0`; a worker that exits 0 without printing a metric is recorded as `success` with
   `parsed_metrics = {}` and `validity_status=invalid/failure_category=metric_missing`. The C2 gate counts that trial
   as a *success* (it is in `worker["successful"]`, not in `failure_rate`) and only rejects it through the
   **job-global** `successful_with_metrics == 0` check. With ≥2 campaigns, one healthy-with-metrics campaign masks
   another campaign whose 20 runs all exited 0 without metrics → gate passes although that campaign trained nothing.
   The gate already has per-campaign `successful_with_metrics` in `worker["roots"]`; make it a per-campaign STOP
   (and/or count success-without-metrics as failure).
2. **A campaign with no `root_trials.jsonl` is invisible.** `worker["roots"]` is built from files found under
   `work/roots`; a campaign directory with no ledger is not in `zero_success`, and only the `out/roots` count /
   `out/failures` gates catch the usual cases. Compare the worker root set to the expected campaign set explicitly.
3. **Crashes without "Traceback" markers are still caught by C2** because the gate uses the ledger
   `execution_status`, not log text. That part of the question is fine for C2.
4. **Tests:** the synthetic test exercises the zero-success STOP and the failure-rate STOP and writes
   `worker_failure.json`; it does **not** exercise the no-metrics STOP, the missing-venv STOP, the multi-campaign
   per-campaign metrics case, or worker stats on a legitimate multi-campaign PASS. The `_worker_env` test only covers
   the positive path (a fake `venvbin/python3`), not the STOP.

## 4. S2-C3 driver and S2-C3b audits

**S2-C3 driver (`worker_audit`, `s2_c3_replay.py:1570-1595`):** located correctly. The B2 campaign is launched with
`B1IntegrityWorker(node_root=out/'node', artifact_dir=out/'art')`, and the harness writes
`<artifact_dir>/trial-XXX/run.log`, so the logs live under `cwd/out/<root>/art/trial-*/run.log`; the audit's
`rglob("run.log")` over `cwd/out/<root>` finds them (B2 audit `run_config` scratch dirs are also under
`out/<root>/c3a_*/art`, also found). `CRASH_MARKERS` includes `Traceback (most recent call last)` and
`ModuleNotFoundError`, so the observed failure is caught. A normal successful node run does not print those markers,
so no obvious false positives. A `Stop` from the audit is caught by the outer `except (Stop, lib.Stop)`
(`s2_c3_replay.py:1725-1731`), which writes the record and calls `package(cwd)` (out.tar/work.tar/SHA256SUMS) before
re-raising; `seal_replay` accepts `STOP` records, so the STOP is sealable.

Driver caveats:
- **m2 (minor):** the crash cap reuses `1 − 5287/5813 + 0.05 = 14.05 %`. Sweep-1 had **zero** `runtime_error`
  trials, so the comparable crash rate is ~0 %, not 9.05 %; as written up to ~14 % of the inspected logs may crash and
  still pass. The two hard STOPs (`no run.log`, `all logs crashed`) still catch the observed all-failure mode, so this
  is a leniency, not a hole for the total-failure case.
- **m3 (minor):** a failed run whose log lacks all four markers (timeout/SIGKILL/non-Python failure/`run_command
  timed out after …s` written by the worker) is counted as `assumed_successful`; the heuristic measures "Python
  traceback rate", not "failure rate". The all-crashed and no-logs STOPs remain the important backstops.
- **m4 (minor):** `sweep2/s2_c3_compare.py` never reads `record["worker_audit"]`; an untrained replay is rejected only
  indirectly (the B2 campaign's final-Y audit needs 10 successful `run_config` runs; all-None raises
  `STOP: incomplete final Y audit` → root rc ≠ 0 → driver STOP; `validate_campaign_manifest` also requires numeric
  `final_y`). That indirect path means a *partially* untrained replay could still compare. Add an explicit
  `worker_audit` presence/bound assertion in `load_job_output` so pre-fix records (no `worker_audit`) cannot be
  compared at all.

**S2-C3b worker audit (`s2_c3b_lib.py:1238-1246`) — MAJOR: it scans the wrong directory and is vacuous.**
`run_liveness_job` runs `r1.liveness` with `--out <sandbox>/out --work <sandbox>/work`
(`liveness_argv`, `s2_c3b_lib.py:455-465`); `r1/liveness/__main__.py` then does
`work = Path(args.work)/f"liveness_{stamp}"`, and `e1b_collect._run_root` builds
`root = work/"roots"/inst` and `LocalWorker(node_root=node_dir, artifact_dir=root/"art")`, so every liveness worker
log is at **`work/liveness_<stamp>/roots/<inst>/art/trial-*/run.log`**. `r1.liveness` copies only
`root_trials.jsonl` and `root_events.jsonl` into `out/ledgers/` — an `out` tree never contains `run.log` (confirmed
against the sweep-1 liveness record `results/r1/engineering/liveness_c3_20261027T152425Z`, which contains
`ledgers/*/root_trials.jsonl` and no `run.log` anywhere). The audit's `logs = list(Path("out").rglob("run.log"))` is
therefore always empty, `record["worker_audit"]` is written as `{"total_run_logs": 0, "crashed": 0}`, and the only
STOP condition (`if logs and len(crashed) == len(logs)`) never fires. **The claimed "STOP if all liveness worker
runs crashed" defense does not exist.** This is not a pass-for-untrained-workers hole (the liveness verdict requires
`keep_after_trial_1`: at least one kept trial with `budget_index > 1`, which requires a successful metric-bearing
worker run, so an all-crashed liveness run fails `evaluate_liveness` and STOPs), but the new control is dead code and
was not tested. Fix: scan `<sandbox>/work` (rglob), add a `total == 0` STOP like the driver, include `SyntaxError`
in the marker set, and add a synthetic test with the real `work/liveness_*/roots/...` layout — a single such test
would have caught this.
The C3b PATH fix itself is correct; it is only weaker than C2/driver (literal `PATH=...` prepend, no STOP if the
venv bin is missing — the job shell's `[ -x /opt/r1/envs/harness/bin/python ]` catches a missing venv at entry, so
the practical gap is small). (m5, minor.)

## 5. Tests run (independently)

| branch | tip | command | result |
|---|---|---|---|
| `sweep2-main-20261116` | `c1a28b10` | `pytest r1/tests/htcondor -q -p no:cacheprovider` | **36 passed** (30 `test_s2_c2_unit.py` + 6 `test_s2_c4_pilot.py`) |
| `s2c3-driver-fix-20261116` | `ed974238` | same | **176 passed** (26 C2 + 31 driver + 113 replay + 6 C4) |
| `s2c3b-fix-20261116` | `8df3f5a8` | same | **129 passed** (29 C2 + 94 C3b + 6 C4) |

The counts match the task's requested expectations (36 = 30 C2 + 6 C4; 176; 129). Remaining test-coverage gaps:
- **MAJOR:** no test exercises the driver `worker_audit` (no-logs STOP / all-crashed STOP / rate STOP / passing
  audit) or `_worker_path`'s STOP; no test exercises the C3b worker audit or its STOP; no test exercises the C3b
  PATH prepend. The only driver test change is
  `test_replay_env_is_the_only_shim_switch` monkeypatching `_worker_path` so the dev host without `/opt` still runs
  (this is why the suite is green on the Mac); it does not test the audit at all.
- **MINOR:** C2's new no-metrics STOP and `_worker_env`'s missing-venv STOP are untested; the gate's multi-campaign
  behaviour is untested.
- **MINOR (docs):** `S2_C2_UNIT.md:153` still says "tests now **34** (28 S2-C2 + 6 S2-C4)" while the branch actually
  has 30 + 6 = 36 (the fix commit message says "30 C2 tests pass"); `SWEEP2_HANDOFF_20261116.md` still lists
  `sweep2-main-20261116` @ `2e932c9c`, "35 C2/C4 tests", "**32k smoke SUCCESS**" and the pre-fix driver/C3b tips, and
  `SWEEP2_LAUNCH_CHECKLIST_20261116.md` P5 carries the internally inconsistent "VOID / RE-MEASURING" status cell with
  the old accepted-layout sentence. These are stale after the fix commits; the hand-off should be re-cut before the
  next operator picks it up.

## 6. Re-measurement status (queued 32k smoke) and operator checklist

The fix commits' docs state that the fixed 2-instance 32k smoke is submitted as **`s2smoke2-20261116-a`,
clusters 759739/759740**, and is idle because there are **no NEMO2 L40S ads** (`g36xx` absent; only H200 `g44xx`,
deepthought2 portal L40S and CPU `n3xxx` were advertised at the last capture,
`sweep2/evidence/condor_status_l40s_20261116.txt`). This matches the launch checklist/hand-off environment block. I
could not independently query the queue (no `condor_*` execution and no job access in this review), and **no
stage directory or spec for `s2smoke2-20261116-a` is committed to the repo**; the run is visible only in the two
docs files. Two operational cautions follow:

1. **Confirm the queued sandbox really contains the fixed code.** The pre-fix 32k record's `gates` object has **no
   `worker` key** (verified in `smoke_20261116/job_record_*.json`). When 759739/759740 run, the operator must see
   `job_record.json["gates"]["worker"]` (and `out/collection_checks.json["worker"]`) with `trials > 0`,
   `successful > 0`, `successful_with_metrics > 0`. If the `worker` key is absent, the staged `s2_c2_lib.py` is the
   old code and the smoke is void again — do not accept its layout numbers.
2. **Do not over-interpret a failure-rate STOP.** Because of BLOCKING 1, a `append_only` STOP can be a normal
   sweep-1 invalid-config/precondition rate on a 40-trial chunk. Inspect `out/worker_failure.json`
   `failures_by_category` before concluding the PATH fix failed: `runtime_error` (or `unknown`) means real worker
   crashes; `invalid_config` / `proposal_precondition_failed` with non-empty metrics elsewhere means the gate
   calibration, not the fix.

**The unit is otherwise code-ready to produce the worker-success evidence**, and once it runs the operator should
check, in order:
1. `gates.worker` present with successes and non-empty `successful_with_metrics`; no `out/worker_failure.json`;
   gate PASS recorded;
2. collector stderr (job record `collector.stderr_tail`): `run_command finished in` times that are *training* times
   (≫0.1 s, node-dependent) with `success=True` and real `metrics={'val_score': …}`; and, inside `work.tar`/`out.tar`,
   `work/roots/*/art/trial-*/run.log` containing metric lines and **no** `ModuleNotFoundError`;
3. `out.tar`/`work.tar` + `job_record.json` + `SHA256SUMS` present and verified, `ENGINEERING_ONLY`, sealed copy and
   `SEAL_RECEIPT.json` produced with the reviewable STOP-capable machinery;
4. re-measure the layout from `timing.json`: queue wait, wall, GGUF fetch, collector seconds, disk/memory peaks,
   KV buffer (should be ≈1,360 MiB at 32k) and offload 61/61; re-scale 2 → 18 instances, recompute full-chunk wall
   and total GPU-hours, amend `R1-SWEEP2-LAYOUT`/the spec layout, and explicitly mark 8,289 s / 9,387 s / 36.84 /
   41.72 GPU-h as superseded (the current 32k records in the repo are pre-fix and their `gates` do not even contain
   worker stats; the literal numpy traceback is sealed-only).

## 7. Findings summary

- **BLOCKING 1 — the worker-failure-rate gate is calibrated on the wrong population and does not account for
  small n.** It compares a one-(node, memory mode) chunk's all-failure rate to the pooled 8-node × 2-mode sweep-1
  rate (9.05 % + 5 pp = 14.05 %). Sweep-1 per-(node, mode) failure rates range from 0 % to 30.8 %
  (ionosphere append 30.8 %, climate append 24.2 %, ionosphere none 16.4 %, climate none 17.2 %), so four of the
  sixteen healthy full chunks will systematically STOP (P ≈ 0.89–1.00), and the queued 2-instance 32k smoke's
  `append_only` job has P ≈ 0.18 of a false STOP. In addition, `proposal_precondition_failed` records have
  `worker_skipped: true` (the worker never ran) and are being counted as worker failures; they are the entire
  digits_mlp append_only 9.55 % and a direct cause of the smoke false-STOP. Required fix: compute and apply the
  baseline per (node, memory_mode) from the frozen ledgers, exclude `worker_skipped` control-plane failures from
  both numerator and baseline (count them separately), and use an exact-binomial / minimum-n or count-headroom rule
  for small chunks (the 2-instance smoke has only 40 trials). Add a `runtime_error`-specific sub-gate: sweep-1 has
  zero `runtime_error`, and the observed bug maps there, so it is a sharp, zero-false-positive detector for this
  exact failure class.
- **MAJOR 2 — the S2-C3b worker-crash audit is non-functional.** It scans `Path("out").rglob("run.log")`, but
  `r1.liveness` writes worker logs under `work/liveness_<stamp>/roots/<inst>/art/trial-*/run.log` and copies only
  ledgers into `out/`. `logs` is therefore always empty, the audit records `total_run_logs: 0` and never STOPs. It
  does not create a pass-for-untrained-workers hole (the liveness `keep_after_trial_1` criterion catches that), but
  the advertised defense does not exist; fix it to scan `work/`, add a no-logs STOP, add `SyntaxError`, and test it
  against the real `work/liveness_*/roots/...` layout.
- **MAJOR 3 — no synthetic coverage for the new S2-C3 driver / S2-C3b worker audits (or `_worker_path`'s STOP), and
  none for several new C2 gate paths** (no-metrics STOP, missing-venv STOP, multi-campaign metrics). A driver audit
  test and a C3b layout test are cheap and would have caught MAJOR 2.
- **MAJOR 4 — the failure-rate gate conflates control-plane skips and node-specific `invalid_config` with worker
  infrastructure failures** and does not report a separate worker-executed/infra failure rate; this both inflates
  the rate (false STOPs) and dilutes the signal for the bug class being fixed (see BLOCKING 1).
- **Minor findings:** m1 `_worker_env`/`_worker_path` accept a `python`-only venv (and `_worker_env` has a dead
  `elif`) instead of requiring `bin/python3`; m2 driver crash cap (14.05 %) is derived from the total-failure
  baseline although sweep-1 has zero crashes (compare to ~0/5 pp, not 9.05+5); m3 crash text heuristics miss
  non-marker failures/timeouts and count them as `assumed_successful`; m4 `s2_c3_compare.py` does not assert
  `worker_audit` presence/bounds (untrained is rejected only indirectly through final-Y/COMPLETE); m5 C3b PATH
  prepend has no missing-venv STOP and omits `SyntaxError`; m6 C2 missing-venv STOP is not persisted through
  `_stop_with_evidence` (a bare `Stop` after the server started, so the pre-created empty outputs are not a
  sealable evidence record); m7 per-campaign no-metrics gate and missing-campaign set check; m8 stale docs
  (`S2_C2_UNIT.md` 34 vs actual 36 tests; `SWEEP2_HANDOFF_20261116.md` old tips/32k-success; checklist P5 status
  contradiction); m9 the literal `ModuleNotFoundError: numpy` line is sealed-only and not independently readable
  from the repo (diagnosis verified from code + failure signature instead).
- **Positive:** the diagnosis is correct and the `_worker_env`/`_worker_path`/C3b PATH repairs cover the real
  collector, C2 liveness, S2-C3 campaign and S2-C3b liveness worker paths (not just the outer process); prepending
  the uv venv bin is sufficient for the pinned node imports; the sweep-1 count 5,287/5,813 = 90.95 % is exactly
  right; the C2 zero-success and failure-rate STOPs are implemented, recorded, and their evidence is persisted as
  record + out/work tars + SHA256SUMS before the raise; the C2 ledger-based gate is not fooled by missing traceback
  text; the S2-C3 driver audit finds the correct B2 run.log tree and would catch the observed `ModuleNotFoundError`
  (and its STOP is persisted/sealable); all three branch suites pass at the expected counts.

**Prioritised next steps:** (1) recalibrate the C2 gate per (node, memory_mode), exclude `worker_skipped` from the
worker-failure numerator/baseline, add small-n handling and a `runtime_error` sub-gate; (2) fix the C3b audit path
and add its STOP/test; (3) add driver-audit and C2 gate-path tests; (4) only then let 759739/759740 produce the
worker-success evidence and re-measure R1-SWEEP2-LAYOUT, checking `gates.worker` presence as the pre-fix/fixed
discriminator; (5) re-cut the stale hand-off/unit test-count docs. The PATH fix itself is correct and can be kept —
the unit is not acceptable as a whole until the gate is calibrated and the C3b audit actually runs.

VERDICT: NOT ACCEPTED

---

# Round-2 re-review — recalibrated worker gate + S2-C3 driver / S2-C3b audit fixes

**Reviewer role / method:** same independent, read-only reviewer. I read the round-2 diffs, the frozen sweep-1
ledgers, the pinned harness `a3fedbb` failure mapping, and re-ran the three unit suites. No job, server or
`condor_*` execution; no git write. The only change this round made is appending this section to this review file
(the file is now an uncommitted modification; `git status` shows only this file).

**Exact round-2 tips (branch tips, not just the requested pins):**

| unit | requested pin | **exact tip** | delta vs round 1 | suite |
|---|---|---|---:|---:|
| `sweep2-main-20261116` | `e17b0437` | **`c9813d9f`** | `e17b0437` (gate code) + `c9813d9f` (docs only: smoke pair renumbered) | 36 passed |
| `s2c3-driver-fix-20261116` | `882362a6` | **`882362a6`** | tests only added | 178 passed |
| `s2c3b-fix-20261116` | `0f5c3fdd` | **`0f5c3fdd`** | audit scan fix + test | 130 passed |

All three worktrees otherwise clean. Updated hashes: `s2_c2_lib.py` `83fb11e7281e13a1da811cf0471d30493dfef36992b6e3353c35fa99061064db`;
`test_s2_c2_unit.py` `329cb6d6bb08ae45072164c2b0d1a3251969461d0cd43f74b1da41c31d2ac1db`;
`test_s2_c3_driver.py` `2afe86c4c2fe5b6b038d950a9714acc2ecb2ba6d3e9ca0ed9d7e7f0c40e69532`;
`s2_c3b_lib.py` `62bb0d1a4acd86ed61077f00401b5da5cf6d612235fdafb993ec7f837bcb2567`;
`test_s2_c3b.py` `fc0223b79fc9ed93ed80e3d0e4d2697454c525bd63d11fe1455b33c6c59c8d55`.

## Round-1 findings — status

| round-1 finding | round-2 status |
|---|---|
| **BLOCKING 1** pooled baseline / small-n / skipped-vs-invalid conflation | **partially fixed:** per-(node, mode) baseline table, `runtime_error` sub-gate and exact-binomial small-n control are correct, but the `worker_skipped` exclusion is wired to a field that does not exist → **R2-B1 remains blocking** |
| **MAJOR 2** C3b audit vacuous | **fixed by inspection** (now scans `out/` + `work/`, STOPs on no logs / all crashed, adds `SyntaxError`); the added test does not exercise it → **R2-M1 remains a test-quality major** |
| **MAJOR 3** no driver/C3b audit tests | **partially fixed:** driver tests are genuine (no-logs, all-crashed, clean, missing-venv); C3b test is tautological (R2-M1); driver rate-STOP branch still untested |
| **MAJOR 4** conflates control-plane skips / node `invalid_config` with infra failures | **partially fixed:** `runtime_error` is now separated and zero-tolerance; skip exclusion intended but broken (R2-B1) |
| **minors** (per-campaign metrics, `_worker_env` python-only, C3b PATH no STOP, compare, docs) | docs remain stale (R2-M2); most others unchanged/acceptable; see R2-m |

## R2-B1 (BLOCKING) — `worker_skipped` is read from the wrong schema path; the skip exclusion never fires

The live gate checks `trial.get("worker_skipped") is True` (`sweep2/s2_c2_lib.py:666`). In the frozen corpus the
field is **never top-level** (0/5,813) — it lives at `extra.worker.worker_skipped is True` in exactly the 53
`proposal_precondition_failed` records. The harness creates it in `WorkerResult.extra` (`worker_skipped: True` in
`campaign.py:_structured_failure_result` @ `a3fedbb`), the campaign wraps that as `extra={"worker":
worker_result.extra, …}`, and the ledger `TrialRecord.to_dict` does **not** flatten `extra`. So the new exclusion
can never match: `worker["skipped"]` stays 0 and all 53 precondition skips are counted as worker failures.

This makes the gate internally inconsistent, because the hardcoded `SWEEP1_WORKER_BASELINE` table **was** computed
with skips excluded. I verified all 16 table rows against my independent recomputation (including the `skipped`
counts: 38, 4, 11) — **exact match** — then reproduced the consequence with a healthy sweep-1-equivalent
`digits_mlp/append_only_summary` ledger (360 successes + 38 nested `worker_skipped` preconditions):

```
STOP: STOP: worker failure rate 0.095 exceeds the sweep-1 baseline for digits_mlp/append_only_summary
      0.000 + 0.05 (allowed failures <= 0)
worker stats: {'trials': 398, 'successful': 360, 'failures': 38, 'skipped': 0, ...}
failures_by_category: {'proposal_precondition_failed': 38}
```

A healthy full `digits_mlp/append_only_summary` chunk (18 instances, ~398 trials, sweep-1 had 38 skips) will
therefore almost certainly STOP. `tabular_mlp/append_only` (11 skips, 2.96 % < 5 %) and `openml_wdbc/append_only`
(4 skips, rate under the +5 pp cap) happen not to trip; every other (node, mode) group has zero skips. The smoke is
mostly safe (`digits` baselines are 0/360; a false rate STOP needs ≥3 precondition skips in 40 trials, expected
≈0.5) but not guaranteed, and the full sweep is blocked on this chunk.

**Fix (one line + one test):** `if ((trial.get("extra") or {}).get("worker") or {}).get("worker_skipped") is True:`
(optionally fall back to the top-level key). Add a test row using the real nested schema, asserting
`worker["skipped"] == 1`, that a healthy campaign with skips passes, and that an all-skipped campaign still trips
the zero-success STOP. Also consider excluding control-plane `_skipped_record` rows (`decision == "skipped"`,
`failure_category is None`) — sweep-1 has none, but they would be counted as `unknown` failures if they appear. The
`r1/tests/htcondor/test_s2_c2_unit.py` suite contains **no** skipped-schema row, so this bug passed the round-2
suite.

## Verified round-2 positives (all independently checked)

- **Per-(node, mode) baseline table is correct.** All 16 `SWEEP1_WORKER_BASELINE` rows match my recomputation exactly
  (`worker_trials`, `successes`, `failures`, `skipped`, `runtime_errors = 0`, `invalid_config`) from the 288 frozen
  `root_trials.jsonl` files.
- **`runtime_error` is the correct sharp detector.** Pinned harness `campaign.py:2366` assigns
  `failure_category = runtime_error` when the worker failed and no `FAILURE_CATEGORY=` line was parsed — exactly the
  observed `ModuleNotFoundError: numpy` case — and sweep-1 has zero `runtime_error` records. The new
  `worker["runtime_errors"] > 0` STOP (`s2_c2_lib.py:705-708`) is therefore a sharp, false-positive-free detector for
  this bug class, separate from node-specific `invalid_config`.
- **Binomial small-n control is mathematically correct.** `_binomial_allowed` returns the largest k with
  P(X ≥ k) > α and the gate stops only when observed > k (one-sided tail < 1 %). Spot checks: n=40, p=0 → 0;
  n=40, p=42/360 → 10; n=360, p=111/360 → 132; n=360, p=87/360 → 106; n=360, p=59/360 → 76 (P(X≥76)=0.0111>0.01,
  P(X≥77)=0.0078<0.01). The `AND` with the +5 pp rate cap is as specified.
- **After R2-B1 is fixed, the calibration is adequate.** Two-instance smoke on digits: rate gate needs 3 failures in
  40 (7.5 % > 5 %), binomial bound 0, `runtime_error` zero-tolerance — no realistic false STOP from normal
  invalid-config noise. Full 16-chunk sweep exact-binomial false-STOP risk from the +5 pp rate cap is ≈3.2 % total
  (per chunk ≤0.92 %; largest: climate/append 0.92 %, ionosphere/append 0.77 %, breast/append 0.19 %; zero for the
  zero-failure groups). That is acceptable fail-closed behavior for the author-specified +5 pp band.
- **Gate ordering/evidence unchanged and correct:** `collection_checks.json` written before the gates (L689);
  `worker_failure.json` written before each STOP; `run_job` catches the Stop and persists `job_record.json` +
  `out.tar` + `work.tar` + `SHA256SUMS` before raising. (Minor: `worker.update({baseline, threshold,
  binomial_allowed})` happens at L718, i.e. *after* `collection_checks.json` is written at L689, so the on-disk
  checks file lacks those fields — they are present in `worker_failure.json` on a rate STOP and in the job
  record's `gates.worker` on PASS. Consider attaching them before the write.)

## R2-M1 (MAJOR, test quality) — the added C3b test does not exercise the fixed code

`test_worker_audit_scans_work_and_stops_on_all_crash` (`r1/tests/htcondor/test_s2_c3b.py:761`) creates
`work/.../run.log` and then re-implements the scan inline in the test body
(`logs = [Path("out").rglob(...)] + [Path("work").rglob(...)]; crashed = [p for p in logs if "ModuleNotFoundError"
in p.read_text()]`), asserting on that local copy. It never calls `s2_c3b_lib.run_liveness_job` or any audit helper,
and `import s2_c3b_lib as c3b` is unused. It cannot detect a regression in the production scan path or in the new
`no logs` / `all crashed` STOPs — the exact round-1 defect. The production fix itself is correct by inspection:
`s2_c3b_lib.py:1240-1249` scans `out/` **and** `work/`, records `scanned: ["out/", "work/"]`, STOPs when
`not logs` and when `len(crashed) == len(logs)`, adds `SyntaxError`, and routes the STOP through
`stop()` → `_stop_with_evidence` (record + out/work tars + SHA256SUMS before raise), so it is persisted and
sealable. Recommendation: extract the scan into a module-level `audit_worker_logs(bases=("out","work"))` that
raises `Stop`, and test it for no-logs STOP, all-crashed STOP, partial-crash PASS, and the `work/` location.

## S2-C3 driver (`882362a6`) — accepted with residual leniencies

Tests are genuine and call production functions: `test_worker_audit_stops_on_no_logs_and_all_crashed` exercises the
no-logs STOP, all-crashed STOP and clean PASS of `replay.worker_audit` (`test_s2_c3_driver.py:623`);
`test_worker_path_stops_without_the_venv` exercises the missing-venv STOP of `replay._worker_path` (:636). The audit
code is unchanged from round 1, which I verified locates the correct B2 tree (`out/<root>/art/trial-*/run.log`), and
its STOP is persisted and sealable. Residuals (non-blocking): (i) the crash-rate cap still uses the total-failure
baseline (9.05 % + 5 pp = 14.05 %) although sweep-1 crash rate is 0 — lenient, but for this bug class the B2
campaign's final-Y audit (any of its 40 final-audit runs returning None raises `STOP: incomplete final Y audit`) and
the no-logs/all-crashed STOPs are the binding detectors; (ii) the rate branch of `worker_audit` has no test;
(iii) text markers still miss non-Python/timeout failures and count them as `assumed_successful`. Accept for the
ENGINEERING run with these recorded.

**`s2_c3_compare.py` / `worker_audit`:** I accept the lead's position as sufficient for the current run **provided**
the three queued S2-C3 jobs (`759736-759738`, staged on the pre-fix driver `52e023e6`, before the PATH and audit
commits) are cancelled and resubmitted from `882362a6`, and the S2-C3b staged asset (`s2c3b_run_20261116_a/`, staged
at `f1dff01f`, before the liveness PATH/audit fixes) is restaged from `0f5c3fdd`. With no pre-fix C3 records in
existence, a `COMPLETE` record implies the fixed driver ran and `worker_audit` passed, so compare's COMPLETE
requirement blocks a failed-audit result. A cheap hardening (assert `record["worker_audit"]["total_run_logs"] > 0`
and bounded `crashed`) would make the invariant explicit and is recommended but not blocking.

## R2-M2 (minor, operator-facing docs) — the unit doc was not actually updated

The lead's statement that `S2_C2_UNIT.md` baseline text was corrected is not what the commit did: `e17b0437`
changed only the test count (34 → 36). The "Worker-success fix" section still describes the **round-1 pooled gate**
("failure rate exceeds sweep-1's failure rate + 5 pp … 5,287/5,813 = 90.95 % … max 14.05 %") and still names smoke
clusters **759739/759740** (`s2smoke2-20261116-a`), contradicting both the code and
`S2_C4_RESULTS_20261116.md`, which now says the live pair is **759741/759742** (`s2smoke2-20261116-b`, recalibrated
gate; 759739/759740 "staged on an intermediate gate revision, was cancelled and moved aside"). Also
`SWEEP2_HANDOFF_20261116.md` (tip `2e932c9c`, 35 tests, "32k smoke SUCCESS") and
`SWEEP2_LAUNCH_CHECKLIST_20261116.md` P4/P5 (old driver tip `3e2ebbf0`/176 tests; P5 still carries the accepted
9,387 s layout sentence) are stale after both fix rounds. Re-cut these before an operator uses them.

## Re-measurement status (round 2)

- The branch docs at the exact tip (`c9813d9f`) say the live re-measurement smoke is **759741/759742
  (`s2smoke2-20261116-b`)**, with **759739/759740 cancelled/moved aside**. The lead's message instead says
  759739/759740 are queued/idle — please reconcile which pair is actually in the queue; the trigger/evidence
  requirements are the same either way.
- Because the pair is idle, the cheapest path is: apply the R2-B1 one-line fix + nested-skip test, then cancel and
  re-stage the idle pair (`s2smoke2-20261116-c`) so the smoke runs gate code without the skip defect. If a currently
  staged `b` pair runs first it will almost certainly pass (digits baselines are 0/360; a false rate STOP needs ≥3
  precondition skips in 40 trials, expected ≈0.5) and the PATH fix + `runtime_error` gate are present — but the full
  `digits_mlp/append_only` chunk would STOP, so the fix is needed before the sweep regardless.
- Operator checks otherwise as in round 1, plus: `job_record.json["gates"]["worker"]` must exist (pre-fix records
  lack it); after the skip fix, `worker.skipped` should equal the observed `proposal_precondition_failed` count
  (~0-2 for the smoke, ~38 for a full digits/append chunk), `failures_by_category` should show zero `runtime_error`,
  and `worker_failure.json` should be absent on PASS; `run.log`s in `work.tar`/`out.tar` must show real metric lines
  and training times ≫0.1 s; then re-measure and amend R1-SWEEP2-LAYOUT (8,289 s / 9,387 s / 36.84 / 41.72 GPU-h
  remain void).

## Round-2 summary

The recalibration is right in design: all 16 per-(node, mode) baseline rows are independently correct, the
`runtime_error` zero-tolerance sub-gate is the sharp detector for the actual bug class (sweep-1 has zero
`runtime_error`), the binomial small-n control correctly removes the round-1 smoke false-STOP risk, the C3b audit
now scans the real `work/` tree and STOPs on no-logs/all-crashed, and the driver audit now has genuine tests. Two
things still block acceptance: (R2-B1) the skip exclusion reads a non-existent top-level `worker_skipped` field, so
the gate will false-STOP a healthy `digits_mlp/append_only` chunk and under-report skips; and (R2-M1) the C3b test
does not call the code it claims to cover. The stale unit/hand-off/checklist docs (R2-M2) are operator-facing and
should be re-cut. Everything else is accepted; the PATH fix remains correct and keepable.

ROUND-2 VERDICT: NOT ACCEPTED

---

# Round-3 final confirmation — ACCEPTED

**Reviewer:** same independent read-only reviewer; no job/server execution, no git write; this append is the only
change (uncommitted). Pins verified: C2 branch tip **`42ebe3fc`** (fix `ce9210d3`, docs `42ebe3fc`; 37 tests), driver
**`882362a6`** (unchanged; 178 tests), C3b **`4ecc416e`** (130 tests). All three worktrees otherwise clean; all three
suites pass.

- **R2-B1 fixed and verified.** `sweep2/s2_c2_lib.py:666-667` now reads
  `((trial.get("extra") or {}).get("worker") or {}).get("worker_skipped") is True` (plus `decision == "skipped"`).
  New test `test_worker_skipped_nested_schema_is_excluded_from_the_gate` uses the real harness schema (8 successes +
  2 nested `extra.worker.worker_skipped` rows → `worker["skipped"] == 2`, `worker["trials"] == 8`,
  `failure_rate == 0.0`). The hardcoded per-(node, mode) baseline was independently verified correct in round 2, so
  the gate is now internally consistent. R2-B1 closed.
- **R2-M1 fixed and verified.** C3b now has a module-level `audit_worker_logs(bases=("out","work"))`
  (`sweep2/s2_c3b_lib.py:1160`) called by the production path (`:1258`); the test calls the real helper and exercises
  the no-logs STOP, the all-crashed STOP, and an out+work partial PASS (2 logs / 1 crashed). R2-M1 closed.
- **R2-M2 fixed.** `S2_C2_UNIT.md` now describes the per-(node, mode) gate, the nested skip exclusion, the
  `runtime_error` sub-gate, the 1 % exact-binomial small-n control and smoke pair 759743/759744 (`s2smoke2-20261116-c`);
  the hand-off and launch checklist record the worker bug, the void layout, the cancelled pre-fix S2-C3 jobs
  759736-759738 and the current branch tips. R2-M2 closed.
- **Accepted non-blocking residuals (as recorded in the round-2 section):** no explicit `worker_audit` assertion in
  `s2_c3_compare.py` (fine: the fixed driver STOPs before COMPLETE and the pre-fix S2-C3 jobs were cancelled); driver
  crash-cap remains the lenient total-failure baseline and its rate branch is untested; `runtime_error`
  zero-tolerance is intentionally strict; the C3b staged asset must be restaged from `0f5c3fdd`/`4ecc416e` after the
  re-measured smoke.

**Operator note:** the re-measurement smoke (759743/759744) is staged from the fixed code and idle for a NEMO2 L40S
slot. When it runs, check `job_record.json["gates"]["worker"]` is present with `worker["skipped"]` equal to the
observed `proposal_precondition_failed` count and zero `runtime_error`, real metric lines/training times in the
worker `run.log`s inside `work.tar`/`out.tar`, and no `out/worker_failure.json`; then re-measure and amend
R1-SWEEP2-LAYOUT (8,289 s / 9,387 s and 36.84 / 41.72 GPU-h remain void). Resubmit S2-C3 (from `882362a6`) and
restage S2-C3b (from `4ecc416e`) only after the re-measurement.

FINAL VERDICT: ACCEPTED
