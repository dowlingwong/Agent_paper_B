# G.1b TASL ENGINEERING dry-runs — independent review (21 November 2026)

**Reviewer.** Fresh independent reviewer (`g1b-tasl-dryrun-reviewer`), delegated by the lead; no involvement in writing
the dry-run report, the captures, the pre-launch report/package, the wrapper, the specs, the bindings, the T1 prechecks
or the prior pre-launch review. Read-only: the only file written is this review. No run, no edit of the package, no
commit/push/delete, no HTCondor/deepthought action. Hosts were only read (`ssh -o BatchMode=yes`, commands in §7); no
file was created, changed or deleted on a host; no GPU workload, no lease, no server start/stop, no job was started.

**Object under review.** Worktree `.claude-worktrees/main_t1_host_reports_20261121`, branch
`main-t1-host-reports-20261121` at HEAD `aaf2254a` on `main` baseline `d47d1008`, plus the uncommitted task-2 work
(two modified specs, the untracked reports/captures/wrapper). Sha256 values:

| object | path | sha256 | state |
|---|---|---|---|
| dry-run report | `docs/r1/reports/trackg_g0_20261117/G1B_TASL_DRYRUN_20261121.md` | `38866e0f…2bf93` (38866e0f5295ffdd4f362a55d4aaf8fcf67055c36bb759375e682d22eeb2bf93) | untracked |
| dry-run captures `SHA256SUMS` | `…/G1B_TASL_DRYRUN_20261121_captures/SHA256SUMS` | `4fb0f9c3…0eab9` (4fb0f9c332c7350ab9fdb114b93d65dd248e19a0f6b0c53e4795ec3303f0eab9) | untracked |
| pre-launch report | `docs/r1/reports/trackg_g0_20261117/G1B_TASL_PRELAUNCH_20261121.md` | `9f57bf5e…4adfd` (9f57bf5e106e4dbc187c6020107f117fe981f68ce101cbcd4162cbbf5e94adfd) | untracked |
| G.1b spec | `sweep2/t1_tasl/g1b_tasl_spec.json` | `2f0bdd70…3aeadb` | modified (`M`) |
| G.4 spec | `sweep2/t1_tasl/g4_tasl_spec.json` | `fd5a14b5…ba1b6b` | modified (`M`) |
| TASL-2 binding | `…/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md` | `681011b2…42d7b6b6d` | untracked |
| TASL-7 binding | `…/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md` | `09945c15…be4576a4` | untracked |
| prior pre-launch review | `docs/r1/reviews/G1B_TASL_PRELAUNCH_REVIEW_20261121.md` | `a5679758…b6ec44` | untracked |
| dry-run wrapper | `sweep2/t1_tasl/dry_run_node.py` | `7b504dd3…cd9aae6` | untracked |
| plan | `sweep2/t1_tasl/T1_TASL_PLAN.md` | `fc5606ae…f2867c` | committed |

The wrapper sha differs from the sha in the prior review (`a12d349b…`): its "(184 rows)" comment is now
"(10 rows: default + repeat)" and it is the version that ran on both hosts (live host sha matches).

**Question.** (a) Do the two ENGINEERING dry-runs and their captures establish what the dry-run report says, for the
ENGINEERING-prep purpose? (b) Does the updated pre-launch package now support EVIDENCE / the full G.1b run? The two
answers are separate (verdicts below).

---

## Verdicts

- **ENGINEERING prep: ACCEPTED.** Both dry-runs are real, sealed, machine-checkable and consistent with the report:
  one default part per host (10 rows), 10/10 successful, 0 divergent, no STOP, no timeout, no foreign process, proper
  host/affinity/GPU UUID/driver/uid, delegated 8G/swap0 scope, lease and preflight exercised through the pinned
  `run_node_job`, a partial record (`dry_run_partial:true`), seal receipts whose `job_record_sha256` values equal the
  sealed files, and no attempt left open. TASL-7's `mlgym_breakout_minatar` run is a genuine end-to-end jax312 GPU run
  inside the sandbox with no ptxas error. No BLOCKING or MAJOR finding for the ENGINEERING-prep purpose; the minors
  below do not change any measured fact.
- **EVIDENCE status: BLOCKED — not accepted.** The pre-launch package still lacks the R1-T1-TASL-ENV TASL-7→TASL-2
  crosscheck (B1, unchanged), has no signed note, and its launch sequence must still be staged and re-signed. The
  update correctly *says* this and does not claim launch readiness, so the prior NOT-ACCEPTED-for-EVIDENCE verdict is
  preserved, not overturned. A new MAJOR condition (M2) also exists for the full run: the dry-run attempts occupy the
  real spec `run_id` on the hosts and would block/reject a same-`run_id` G.1b run unless archived or the run id
  changed.

The prior M1 (jax312 + `XLA_FLAGS` in-sandbox end-to-end evidence on TASL-7) is **closed in substance** by the
TASL-7 dry-run; only a capture/text residual remains (§M1 below).

---

## Findings

### B1 — BLOCKING for EVIDENCE (unchanged; correctly disclosed, and not a dry-run defect)

The adopted authority row `R1-T1-TASL-ENV` on published `main` (`docs/r1/PLAN.md:1352`) requires: "The G.1b nodes
measured on TASL-7 also run their default parts on TASL-2, and the metrics must be identical, else STOP and that
node's G.1b is re-measured on TASL-2." Nothing in the package implements it:

- `grep -rn "crosscheck\|cross_host\|cross-host" sweep2/` → no hit; `g1b_tasl.py` has no `crosscheck` subcommand and
  `assemble()` does not compare any TASL-7 default row against a TASL-2 re-run.
- `g1b_tasl_spec.json:70-71` declares only `torch312` under `hosts.TASL-2.env_python`; the jax312 environment the row
  needs on TASL-2 for Breakout is not declared (it exists on the host — I read `envs/jax312/bin/python` = Python
  3.12.16 there read-only — but the spec does not bind it).
- `T1_TASL_PLAN.md:110` says "install jax312 on TASL-2 from its freeze", so the plan anticipated the environment but
  no check consumes it; there is no reviewed `crosscheck` step in the plan, the pre-launch report or the launch
  sequence.
- No PLAN amendment choosing another option is on `main`.

The updated pre-launch report now states this explicitly and does not overclaim: lines 86-92 ("Open precondition for
EVIDENCE (not fixed here)… This pre-launch package therefore does **not** authorize EVIDENCE: a reviewed crosscheck
job (or an author PLAN amendment) is required first; B1 in the pre-launch review records this"), and the dry-run
report lines 41-43 ("EVIDENCE G.1b remains blocked on B1 + the signed note"). That is the correct disclosure. B1 is
a condition before EVIDENCE, not an ENGINEERING-prep defect (the dry-runs are explicitly not noise floors and produce
no evidence).

### M2 — MAJOR before the full G.1b run (not an ENGINEERING-prep finding): the dry-run attempts sit in the real `run_id` namespace and will block/reject a same-`run_id` run

The two dry-runs ran the real spec, so they used `spec.run_id = "g1b-tasl-20261121-a"` (`g1b_tasl_spec.json:4`).
Read-only host inspection shows the attempt-1 dirs are still present under the real roots:

- `/home/dowling/r1_tracks/t1_tasl/runs/g1b-tasl-20261121-a/mlab_ogbn_arxiv/attempt-1` and
  `…/mlgym_breakout_minatar/attempt-1`;
- `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-tasl-20261121-a/{mlab_ogbn_arxiv,mlgym_breakout_minatar}/attempt-1`
  (SEAL_RECEIPT.json and job_record.json shas match the captures).

Both job records have `stop_class: null` (a "complete" attempt). `g1b_tasl.next_attempt` refuses a new attempt when
an earlier one has a stop class in `NO_RETRY = (None, "node", "timing")` (`g1b_tasl.py:460,495-513,681`). Therefore a
full G.1b run with the current spec/`run_id` will STOP at those two nodes ("ended with stop_class None; no new attempt
of this node"). `assemble()` additionally treats a non-`infrastructure` sibling attempt as a STOP
(`g1b_tasl.py:831-838`), so even a manually created attempt-2 would fail assembly while the dry-run attempt-1 is
present. The dry-run report's "must never be assembled/sealed as a G.1b row" (lines 44-45) is a documentary warning,
not a mechanical guard: `assemble()` itself does not inspect `dry_run_partial`. In practice the pipeline is
fail-closed — `summarise()` rejects a subset of nodes and non-exact coverage (`g1b_lib.py:757-787`) — so a partial
attempt cannot become a G.1b row silently.

**Condition (no deletion by this reviewer):** before the full G.1b run, either (a) archive/relocate both dry-run
`attempt-1` dirs from the host `runs/` and `sealed_g1b/` roots, or (b) change `run_id` in both specs and re-take the
spec sha256 through the signed-note/launch sequence. The dry-run report (or pre-launch report) should record this
residue and its handling; the current text says the sealed copies are "for the runner check only" but does not say
they live under the real run id.

### M1 — prior MAJOR: CLOSED in substance by the TASL-7 dry-run; residual capture/text minor

The TASL-7 dry-run is a real end-to-end test of the flagged path:

- All ten `run.log` files of the default part contain `AR_DEVICE gpu NVIDIA GeForce RTX 4090 jax=0.4.35 workers=0`
  (e.g. `…/out/default/runs/c0_default_td_sd/run.log:2`), all end in `AR_WORKER exit=0`, and the engine log reports
  `written_rows 10, stop null`; the search of the whole capture bundle for `ptxas`, `XlaRuntimeError` or a CUDA
  "suitable version" error returns **no hit**.
- The job record binds the environment: `environment.name = "jax312"`, freeze sha
  `80a455c6…` (census), 68 packages (`…/job_record.json:90-95`); rows and chunk_record say `effective: true`,
  `waivers {}`, `exceptions []` (e.g. `…/out/default/runs.jsonl`, `chunk_record.json`); the worker sandbox binds
  `/usr` read-only (so `/usr/local/cuda-12.2` is visible) and keeps `shared_dev_shm: false`.
- The mechanism is present at the pin: the spec sets `hosts.TASL-7.extra_env.XLA_FLAGS =
  --xla_gpu_cuda_data_dir=/usr/local/cuda-12.2` (`g1b_tasl_spec.json:102`); `run_node_job` applies `extra_env` to the
  engine environment (`g1b_tasl.py:696`); the host harness at `c025f89a` (HEAD re-read read-only today) keeps
  `XLA_*`/`JAX_*` in the sandbox worker allow-list (`…/third_party/mlgym/nodes/mlgym_breakout_minatar/ar_isolated.py:107-108`)
  and appends the deterministic flag (`ar_worker.py:12`).
- The flag is genuinely necessary on this host: read-only checks show `/usr/local/cuda` is absent, `ptxas` exists only
  at `/usr/local/cuda-12.2/bin/ptxas`, there is no `nvcc`/`ptxas` on `PATH`, and the jax312 env carries no `ptxas`.
  A successful 2,000,000-step GPU run therefore cannot be explained by a default toolkit lookup.

**Residual minor:** no capture records the *effective* `XLA_FLAGS` value (the job record and run record omit
`hosts.*.extra_env`), so the proof is a success-plus-code audit chain rather than a direct env capture. Recommend
recording the applied `extra_env` (or a single log line) in a follow-up. The pre-launch report §6 cell (line 56) still
reads "GPU-in-sandbox smoke | PASS | PASS (jax GPU smoke too)" without the J1a-as-configured failure / J1b-with-flag
limit; it should cite this dry-run (and/or carry the prior m1 note) so the record is precise.

### Minor findings (ENGINEERING prep; no measured fact changes)

- **m1 — capture count / dangling "recompute".** The report says "Capture bundle: 155 files … (recompute recorded
  below)" (lines 32-33). The bundle has **156** regular files including the top-level `SHA256SUMS` (155 payload + the
  manifest), and the top-level manifest has **151** entries: the four nested per-attempt `SHA256SUMS` are not listed
  in it (`shasum -a 256 -c` 151/151 OK; each nested manifest verifies 2/2). There is no "recompute" section below.
  Fix the text to say 155 payload files + manifest, state/cover the nested manifests (or disclose that they are
  excluded), and remove the dangling "recompute recorded below".
- **m2 — aborted first invocations are in the bundle but not mentioned.** The capture contains earlier per-host
  attempts at 10:31:10Z (TASL-7) / 10:31:41Z (TASL-2) that end in `g1b_lib.Stop: STOP: envs.torch312.freeze must be
  the committed census freeze with that sha256` from `validate_spec` (logs are in both hosts' `logs/` dirs; host
  copies match the captured sha). The successful runs are 10:32:13Z / 10:32:44Z with the final spec sha; the failed
  invocation stopped before the lease and before `next_attempt`, so it created no attempt, no refusal record and no
  lease — "no attempt left open" stands. But the report's Design/Results read as one clean run and do not mention the
  aborted invocation. Add one sentence for completeness (or exclude the failed logs and say so).
- **m3 — table labels.** "median wall" 3.893 s / 36.246 s are the job record's `c0_median_wall_s` (the median of the
  two `c0` rows, i.e. the upper of the two), not the part-wide median (3.902 s / 35.667 s); "max wall" is the
  part-wide maximum. The quoted values are correct for the record field, but the header should read "c0 baseline
  median wall" or a note should define it.
- **m4 — procedure not literal.** The report names the wrapper and gives the scope flags, but does not give the exact
  wrapper invocation (`systemd-run --user --scope … taskset … G1B_TASL_NODE_LOG …` with `AR_TEST_CGROUP_PARENT`) nor
  the exact `g1b_tasl.py seal <attempt-dir> <spec> --node <node>` command; the wrapper docstring still does not
  mention the seal step. Prior-review condition m5 asked for these; add them so the run is reproducible.
- **m5 — houseprice CPU path deliberately omitted.** The TASL-2 `mlgym_houseprice` `cpus 8-15` path is not exercised
  (prior-review m6); the pre-launch report says it is "deliberately not in this one-part dry-run" without a reason,
  and the synthetic §6 check (`c6c`) is the only coverage. Acceptable for ENGINEERING prep, but record it as a
  residual condition before the full run.
- **m6 — seal receipt does not bind the node log.** Both `SEAL_RECEIPT.json` files have `node_log_sha256: null`
  because the node log lives in `/home/dowling/r1_tracks/t1_tasl/logs/`, not under `runs/<run_id>/_logs/`. The logs
  are captured and covered by the top-level `SHA256SUMS`; only the seal's own log binding is absent. Minor.

---

## Carried-over pre-EVIDENCE conditions from the prior review (not re-reviewed in depth; confirmed still present where checked)

The prior review's conditions before EVIDENCE remain the authority; the dry-runs do not close them. Verified today:
`G1B_TASL_PRELAUNCH_20261121.md:16-18` still says "this pre-launch engineering run uses the specs as committed here"
while the specs/reports are untracked (prior m3 — launch-commit/staging wording); the note template still has no
`harness_commit` field (prior m4); the TASL-2 binding line 18 still says "all seven passed" with the item-7 CUDA-IPC
limit only in the C6 row rather than up front (prior m1; the pre-launch report itself does disclose "CUDA IPC remains
untested and is not used"); the `.50`/`.51` resolution claim still has no capture in this package (prior m7; I
re-confirmed `getent` live today); the census-sha annotation (m8) and the TASL-2 precheck stale `PENDING` text (m9)
remain. These are EVIDENCE conditions, not dry-run defects.

---

## 5. Verification performed (positive checks)

All worktree reads were local; host checks were read-only `ssh -o BatchMode=yes`. No job, lease, GPU workload, server
or write occurred.

| # | check | result |
|---|---|---|
| 1 | dry-run report / captures / pre-launch / specs / bindings / wrapper shas | **PASS** — all quoted shas reproduce; wrapper `7b504dd3…` is the one on the hosts |
| 2 | TASL-2 `mlab_ogbn_arxiv` default part | **PASS** — 10 rows, 10 successful, 0 divergent, `stop: null`, `stop_class: null`; chunk `expected_runs 10, written_rows 10, successful_rows 10` |
| 3 | TASL-7 `mlgym_breakout_minatar` default part | **PASS** — same 10/10/0, no STOP; each of the ten run records `outcome.kind = ok`, `process.returncode 0`, `timed_out false` |
| 4 | host identity/affinity/GPU/driver/uid | **PASS** — TASL-2 `host TASL-2`, uid 1008, kernel 6.8.0-149, affinity [0..7], `GPU-4d623e76…`, driver 535.309.01; TASL-7 `host TASL-7`, uid 1011, affinity [0..7], `GPU-ab72fb4a…`, driver 580.178.04; all match the live `nvidia-smi` |
| 5 | delegated scope / lease / preflight | **PASS** — job records carry the `systemd-run --user --scope` cgroup parent, `memory.max 8589934592`, `memory.swap.max 0`, `lease` path/pid, `ptrace_scope 1`, harness commit, environment; taken by `run_node_job` (line 681) |
| 6 | foreign checks / no timeout | **PASS** — three `foreign_checks` per host all `[]`; no timeout row; timeout basis 21.8 s / 61.781 s ×3 |
| 7 | `dry_run_partial:true` | **PASS** — present in both job records and produced by the wrapper's `partial_merge` (`dry_run_node.py:19-29`) |
| 8 | seal receipts / job record shas | **PASS** — TASL-2 receipt `job_record_sha256 e260cc4c…` = sealed file sha; TASL-7 `49ede5c3…` = sealed file sha; both captures' copies identical; sealed UTC 10:37:26Z / 10:40:06Z match the report |
| 9 | no attempt left open | **PASS** — only `attempt-1` exists per node on both hosts; each has a finished job record; the recorded PIDs are dead (`ps -p` empty); no `_refusals`; GPUs idle (353 MiB / 44 MiB, 0 %); the attempt's lease pid is dead (I did not take the lease to test it) |
| 10 | capture SHA256SUMS | **PASS** — top-level 151/151 `shasum -c` OK; four nested manifests 2/2 OK each; 156 regular files (155 payload + manifest) |
| 11 | capture ↔ host records/logs | **PASS** — host sealed job records, receipts and both dry-run logs sha-equal the captured copies; host spec sha = `2f0bdd70…` and wrapper sha = `7b504dd3…` = worktree |
| 12 | TASL-2 timing/ratio | **PASS** — `c0_median_wall_s 3.893`, `max_wall_s 20.122`, `ratio_4090_over_ada 0.6889` = 3.893/5.651, as in the report |
| 13 | TASL-7 timing/ratio | **PASS** — `c0_median_wall_s 36.246`, `max_wall_s 36.246`, `ratio 0.5918` = 36.246/61.248, as in the report |
| 14 | M1 end-to-end jax312/XLA | **PASS (substantively)** — ten GPU jax runs, no ptxas/XLA error, `effective:true` sandbox, jax312 freeze bound; flag necessary on this host (no default CUDA symlink, no ptxas on PATH/in env); mechanism verified in code at the pin (see §M1). Residual: effective `XLA_FLAGS` not captured (§M1 residual) |
| 15 | no EVIDENCE / no noise-floor row / no signed note / no launch | **PASS** — zero `"evidence"` text matches in the bundle; all eight `label` fields are `ENGINEERING_ONLY`; no G.1b/TASL `ASSEMBLY.json` or `summary.json` exists (the only `summary.json` files in the tree are older unrelated results); no staged `g1b_t1_tasl_*` note; spec `paper.commit` is the base `d47d1008`; reports do not claim launch readiness |
| 16 | B1 absent | **PASS (as a finding)** — no `crosscheck` code/plan step; TASL-2 spec lacks jax312; report says EVIDENCE blocked |
| 17 | specs validate at launch | **PASS** — `g1b_tasl.py validate … --launch` exit 0, estimate 28.262 GPU-h / sensitivity 41.644 within the 100 cap, per-host 14.06/14.202; `g4_tasl.py validate … --launch` exit 0, 11.077 GPU-h (run with `python3 -B`; no write) |
| 18 | binding/precheck/original/review shas | **PASS** — both binding lines exactly once; originals `83636c03…`/`2b703226…`; host-check reviews `bfe9b231…`/`18e261cd…`; TASL-2 precheck captures 91/91 OK, TASL-7 170/170 OK (`e604aff7…`, `19c4f657…`) |
| 19 | authority row on published main | **PASS** — `R1-T1-TASL-ENV` present once at `d47d1008:docs/r1/PLAN.md:1352`, verbatim matching the report's citation |
| 20 | live environment/host facts | **PASS** — harness HEAD `c025f89a` clean; `getent` TASL-2 `.50` / TASL-7 `.51`; houseprice CSV `1e18addf…929d41`, 460,676 B on TASL-2; Python 3.12.16 in torch312/jax312 envs on both hosts |

---

## 6. Conditions before EVIDENCE / the full G.1b run

1. **B1 (BLOCKING for EVIDENCE).** Implement and independently review the R1-T1-TASL-ENV crosscheck (read the sealed
   TASL-7 default/default_repeat rows, re-run exactly them on TASL-2, compare metrics bit for bit, STOP on difference,
   re-measure on TASL-2 on failure); declare `jax312` under `hosts.TASL-2.env_python` in the G.1b spec; add the step
   to the plan, the pre-launch report and the launch sequence; re-take the spec shas. Alternatively record an author
   PLAN amendment (option B or C) on `main`. No EVIDENCE launch while the cited authority clause is unbuilt.
2. **M2 (MAJOR).** Archive/relocate the dry-run `attempt-1` dirs from both hosts' `runs/g1b-tasl-20261121-a/` and
   `sealed_g1b/g1b-tasl-20261121-a/` (or change `run_id` and re-take the spec sha through the note sequence); record
   the handling in the package. Do not delete without the operator's authority.
3. **Signed note / launch staging.** No signed note exists; before EVIDENCE, commit the specs/reports/bindings and the
   note, stage a spec whose `paper.commit` is the launch commit, sign the note with that commit and the staged spec
   sha, push to `main`, and launch from a clean checkout at the launch commit (this also fixes the still-wrong "as
   committed here" sentence; prior m3). The host-check bindings must be on `origin/main` because `check_host_record`
   reads it. The note should name the harness commit (prior m4).
4. **M1 residual text/capture.** Add the dry-run as the §6 jax-GPU evidence (or note J1a-as-configured FAIL / J1b PASS
   with the flag) and, preferably, record the effective `extra_env` in the job record or a log line.
5. **Dry-run report minors.** Fix the 155/156/151 count and the dangling "recompute recorded below" (m1); disclose or
   exclude the aborted 10:31Z invocations (m2); clarify the "median wall" label (m3); add the literal wrapper and seal
   commands (m4); record the houseprice omission reason (m5). No measured value changes.
6. **Carried-over package conditions.** Prior m1 (TASL-2 binding item-7 wording), m7 (`.50`/`.51` resolution capture),
   m8 (census-sha annotation), m9 (stale `PENDING` text), plus the prior review's remaining conditions. Then re-review
   the EVIDENCE package.

---

## 7. Review record (commands; Europe/Berlin, 21 November 2026)

- **Worktree (read-only):** `git -C … rev-parse HEAD` / `log`; `git status --short` (unchanged before/after: two `M`
  specs and the untracked package; this review is the only added file); `shasum -a 256` on the report, captures
  manifest, pre-launch report, both bindings, both specs, the wrapper, the plan, both T1 prechecks, the originals and
  both host-check reviews; `shasum -a 256 -c SHA256SUMS` in the new bundle (151/151) and the two precheck bundles
  (91/91, 170/170); `shasum -a 256 -c` in all four nested attempt manifests (2/2 each); Python JSON reads of both
  job records, both sealed job records, both receipts, both attempts/chunk records/runs/chunk_records/edits,
  `AR_DEVICE`/`AR_WORKER` scan of all 20 run logs, and a `ptxas`/`XlaRuntimeError` scan of the whole bundle;
  `grep` for `crosscheck`/`cross_host` (none), `EVIDENCE` (none), and the binding/authority lines;
  `python3 -B sweep2/t1_tasl/{g1b,g4}_tasl.py validate … --launch` (both exit 0; `-B` so no bytecode write).
- **TASL-2 (`ssh -o BatchMode=yes portal_zhixu`, read-only):** `hostname`, `date -u`; `sha256sum` of the host spec and
  wrapper; `ls`/`find` of `runs/g1b-tasl-20261121-a/` and `sealed_g1b/g1b-tasl-20261121-a/`; `sha256sum` of the
  sealed job record; `cat` of the receipt; `ps -p 2549101`; `ls ~/r1_locks/`; `nvidia-smi --query-gpu`; `sha256sum`
  of the home-price CSV and `stat -c %s`; `getent hosts tasl-7.tail119748.ts.net`; Python versions.
- **TASL-7 (`ssh -o BatchMode=yes tasl7`, read-only):** the same directory/record/pid/lease/GPU checks (pid 231481),
  node-log shas, `git -C harness rev-parse HEAD` and `git --no-optional-locks … status --porcelain` (clean),
  `ar_isolated.py:107-108`, `ar_worker.py:12`, `/usr/local/cuda*`, `ptxas`/`nvcc` presence, `getent`, Python versions.
- **Not done:** no run/dry-run, no lease, no GPU workload, no server start/stop, no file edit outside this review, no
  commit/push/delete, no HTCondor/deepthought, no host write of any kind. The failed 10:31 logs are data, not actions.

**AI-assisted: DeepSeek Harness agent (`g1b-tasl-dryrun-reviewer`), 21 Nov 2026. ENGINEERING_ONLY; the only file
written is this review.**
