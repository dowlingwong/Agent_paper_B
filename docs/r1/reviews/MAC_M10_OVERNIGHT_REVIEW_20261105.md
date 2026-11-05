# M10 overnight review — round 1 (5 November 2026)

Independent fresh reviewer, AI-assisted (Codex). Verdict: **NOT ACCEPTED**. Scope: paper branch base `f1e8812` with frozen patch SHA-256 `5ecf6358e635e404a393d954cc8e9b8091dd3b41e3721b6ebab93d9b7363a8c5`. Review compared the author's overnight request, HoreKa runbook §0.4/§1/§3 and the existing PLAN rows. No actual Slurm, host, GPU or model was used. `/usr/bin/python3` 3.9.6 ran `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s r1/tests/hk2 -v`: **26 tests passed**, all fake scheduler operations.

## Findings

### MAJOR 1 — status observations are absent from accounting reconciliation

`hk2_status.main` invokes `query_snapshot` and `update_ledger`, but does not call the observation-persistence logic in `require_submission_accounted`. A user job seen by the status helper can subsequently vanish from `squeue` while `sacct` has not yet recorded a terminal entry; if it was never observed by a submission and was not submitted by this tool, the following submission's `seen` set contains neither it nor its GPU usage. The budget guard can admit another job even though accounting has not aligned. Persist every observed user queue ID during both status and submit snapshots, under the same shared lock; subsequent submission must WAIT until a vanished observed job has a terminal accounting record. Add a status → missing accounting → WAIT → terminal accounting regression. This is separate from the documented HK1 limitation that the tools cannot detect jobs never observed by any query.

### MAJOR 2 — production-phase pilot accepted on dev when self-labelled non-production

`validate_manifest` trusts `production` rather than checking the phase's defined job shape. In the frozen snapshot an `HK5`/`engineering`/`production=false` manifest with `partition=dev-gpu-h100`, 1 GPU, 30 minutes and `argv=['python3','pilot_campaign.py']` returned 1800 seconds. Runbook §1 defines HK5 pilot as J3 and restricts dev to J0 GPU check and J1 smoke. Refuse production phases such as HK3/HK4/HK4b/HK5 on dev independently of the flag; retain permitted HK1 setup and HK2 smoke. Test both valid and invalid phase/partition combinations. A separately documented arbitrary-command classification limitation does not excuse accepting the known HK5 phase on dev.

### MAJOR 3 — empty or undated PLAN row treated as author ruling

`plan_has_row` accepts `## 10. Open decisions` followed by `### Undated` and `| R1-HOREKA-AGENT-SUBMIT | |` as the ruling. It does not require a nonempty decision cell or dated author subsection. Before the actual ruling, this would lift the pre-ruling `gpu-*`/continuation refusals without an author decision, contrary to the specified authority model. Parse a single exact row under a dated author subsection with a nonempty decision cell; test empty cells, prose, wrong section, undated and duplicate rows as well as the genuine row.

### MAJOR 4 — non-finite budget threshold disables the STOP

`load_config` accepts `budget_stop_gpu_h='NaN'`; `1000 > float('NaN')` evaluates false, so even a total far above the ceiling is not refused. It also does not validate positive finite budget and resource values comprehensively. Reject nonfinite, malformed, negative or otherwise invalid thresholds and resource limits before submission. Add tests for NaN, Infinity, negatives and invalid numeric types.

### MAJOR 5 — alternate configuration gives a distinct project lock

`QueryLock` and its throttle/observation state are derived from configurable `results_root`, and `--config` accepts arbitrary configuration paths. Two project submissions using different configuration files whose `results_root` differs therefore take different locks, contrary to the author's explicit unified-submission/shared-lock decision. The state location must be common and stable across the project's authorized configurations or mismatching roots must be refused. Add a cross-configuration lock/state identity or concurrent-submission test. This is not a claim that a local lock can control unrelated direct Slurm submissions: those remain an HK1 operational/site check, as the author requested.

## Scope and remaining checks

The shipped switch defaults off and the test covers a successful fake test-only plus fake submission after enabling it. Submit emits and records the manifest SHA, scrubs `SLURM_*`, `SBATCH_*` and unrelated environment variables, rechecks F/C after test-only, and keeps a durable uncertain-submission marker. Existing tests cover several guards and DEADLINE ledger status. The worker's observed-job reconciliation is promising but not yet complete for status polls. The actual site's `squeue`/`sacct` fields, accounting latency, PrivateData effects and enforceability of the shared project procedure remain HK1 checks, not claims established by mocks. The enabled path currently refuses explicit EVIDENCE jobs until their separate authorization gate is implemented; that is outside the HK1 engineering acceptance scope and must remain clearly documented.

## Round 2 — NOT ACCEPTED

Frozen patch SHA-256 `b2552a1ea12d2dd0666888df26bdb7466dacc49c10f6b14b24ac455c52acb3df` against `f1e8812`. Same reviewer independently ran `/usr/bin/python3` 3.9.6 with `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s r1/tests/hk2 -v`: **31 passed**, all mocked; no real Slurm or server calls.

All five round-1 findings have direct fixes and regression tests: both status and submit normally persist observed IDs, production phases are refused on dev, dated/nonempty unique PLAN rows are required, numeric settings are finite and bounded, and configured state roots are constrained to one canonical project root. The enabled fake path also covers normal submit and a WAIT on delayed accounting.

**MAJOR R2-1 — a failed sacct query discards a successfully observed queue snapshot.** `query_snapshot` evaluates `squeue_jobs` and then `sacct_jobs` before returning to `status.main` or `check_guards`, where `record_observed_jobs` runs. If `squeue` succeeds with an outstanding job but `sacct` fails, the job was observed but never persisted. If it leaves the queue before retry while accounting is still delayed, the next submission can miss both records and skip the required wait. Persist the successful queue observation under the same lock before issuing sacct, even when the latter fails. Add a full fake-query regression: successful queue → failed sacct → disappeared queue and absent accounting → WAIT. This is a concrete tool-observation case, not a demand to detect unrelated jobs that were never observed.

**MINOR R2-2 — D is parsed but not checked or surfaced.** The user's overnight request includes F/C/D. Validate chronological F ≤ C ≤ D, and expose the copy-back deadline and its due/overdue state in status without automatically copying or authorizing any operation. This is an operational display/validation requirement; actual site copy-back remains a separate phase.

The actual Slurm query formats, lag, PrivateData and controls over unrelated submitters remain HK1 checks, not established by these mocks. EVIDENCE gate remains separate from HK1 engineering scope. No production use or switch enablement is approved by this review.

## Round 3 — ACCEPTED for the requested submission/status code unit

The same reviewer froze patch SHA-256 `2b9c8c3f1feca6860cdc9fa393aa2c2f9772695415995bd71a42cbe403bc2b40` on `f1e8812`, independently ran `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s r1/tests/hk2 -v` using Python 3.9.6, and observed **33 passed**. Every scheduler interaction was mocked; no server or live Slurm was used.

Round-2 MAJOR R2-1 is fixed: `query_snapshot` persists successful `squeue` observations under the lock, with file and directory sync, before invoking `sacct`; the regression covers sacct failure followed by vanished queue, WAIT and eventual terminal accounting. F ≤ C ≤ D is validated and `hk2_status` reports D and its time state. The five round-1 fixes remain present. The real-submit configuration switch is off by default; a mocked enabled-path test checks test-only, scrubbing, records and submission. Prior PLAN, dev, budget, F/C, TRES, uncertainty and throttle guards remain exercised. This acceptance is for this code/test unit and does not authorize or execute a job.

**Integration and HK1 checks (required before enabling the switch):**

1. Integrate the reviewed code with the current `mac-int-20261104` PLAN or explicitly supply that pinned PLAN in the operational checkout. The standalone `f1e8812` branch's `docs/r1/PLAN.md` predates both HoreKa submission rows; its default PLAN correctly refuses submission. Confirm the integrated PLAN contains the actual dated `R1-HOREKA-AGENT-SUBMIT` and `R1-HOREKA-UNIFIED-SUBMISSION` rows, and re-review the integration.
2. Confirm the canonical project state/lock path is shared and writable by all project submissions; the author's one-tool/one-lock decision is a project procedure, not technical control over unrelated tools. The guard uses one snapshot before `sbatch --test-only`; independent unrelated user submissions could change queue/budget during that interval. Coordinate those submissions and test this assumption at HK1. No mock proves account-wide exclusion.
3. Validate the actual site's squeue/sacct formats, accounting lag, per-user visibility and PrivateData behavior, and the proposed campaign-start/config values. The reconciler waits for jobs it has observed or submitted; it cannot prove that no unrelated, never-observed job is awaiting accounting. Do not claim the mock results establish complete accounting for such jobs.
4. Manifest phase, kind and production are declarations; the guard blocks known production phases on dev, but does not infer an arbitrary argv's semantics. Use reviewed, correctly classified manifests. Explicit EVIDENCE work is separately refused pending its required author authorization mechanism and is outside HK1 engineering scope.
5. `copyback_state=overdue` means the D clock time has passed; the status helper does not observe whether copy-back was completed. The operator must check copy-back artifacts rather than infer completion or noncompletion from that time label alone. The D value remains proposed pending the author's decision.

The tests do not establish production-node behavior, signal handling on Slurm, accounting completeness or permission to run EVIDENCE. Those are HK1/site or later-stage checks as the author specified; they are not reasons to mislabel the code's mocked validation as real-world execution.
