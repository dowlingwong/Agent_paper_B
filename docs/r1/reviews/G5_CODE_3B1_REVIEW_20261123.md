Reviewed base: `da6cd859` (the accepted part 3a, READY 88); accepted at `4b4e0878`, confirmed at `258f5f7207f6f7d8415f3f56ff83896017bd206d`

# Independent review record — the G.5 code unit, part 3b-1: the G.5 job (two campaign waves with the audits between them), audit planning and chunks, E5 on the label seeds, diagnostics and job records, the STOP counters, K uniformity, the access log, close-attempt, the real runner behind the 3a switch and the proposer start

**Unit.** On `mac-g5-code-3b-20261123` over `da6cd859` (part 3a): `sweep2/t1_tasl/g5_job.py` (new; one call runs one campaign wave or one audit chunk of one node; order enforced (wave 2 only after clean wave-1 checks; a node with a STOP or past the cap refused); preflight (lease, host, GPU, ptrace, scope, family checkout, environment, `/props`) before any attempt directory; `/props` again after the engine (STOP 12); the node environment first on PATH; diagnostics with a full nested schema carrying label-seed outcome counts only and planned evaluation-seed run counts; `out.tar` read by named members only, with an access-log line per opening (STOP 11); the audit plan sealed in `plan.tar` with a clear index of counts and hashes; audit-once across instances and waves, `parent:<state>` units under `reuse_parent_runs: false`; STOPs 1–4 and 6–12 and G.4's timing and `cache_prompt` STOPs from the diagnostics alone; infrastructure rows as STOP 7; the table-wide K lock after the first audit attempt; the GPU-hour meter (worker card; under G5-TASL-GPUH B a lower bound adding campaign wall times); `close-attempt`; engine stop text sealed, clear files carrying a fixed reason; `check_engines` requiring the `ENGINE_CONTRACT` marker in `trackg/audit_g5.py` at the G.5 commit), changes to `g5_tasl.py` (the real runner, `serve`, `cpus`, `logdir`, `wave-checks`, `close-attempt`), `g4_tasl.serve_spec` (a pure refactor of `serve`), the `g5` kind in `t1_tasl_node.sh`, `r1/tests/test_t1_g5_job.py` (23, fakes only, two full waves end to end) and the report `docs/r1/reports/g5_code_20261123/G5_CODE_3B1_20261123.md`. Authority: the G.5 draft revision 8 §2–§6, §8–§10 and its reviews; the coordinating chat's draft queue (unit 3), §9 split into 3a, 3b-1 and 3b-2.

**Process.** One independent reviewer, read-only, synthetic probes and fakes only (no secrets, sealed data, labels or evaluation values; no server access), the harness read by `git show` only. The reviewer confirmed the unit's key finding: at both G.5 harness pins `pilot_g4.py` is hard-wired to the pilot nodes, seeds 4001–4099 and ENGINEERING_ONLY, and `noise_floor.py` reserves 7001–7010, so a reviewed harness unit is a prerequisite for any G.5 job. Round 1 found one blocking issue (the clear audit diagnostics let evaluation-seed divergence counts be recovered) and seven majors (every tar member decoded as text; no PATH; G.4's timing and cache_prompt STOPs not carried; infrastructure rows read as STOP 2; per-proposal parent re-runs under reuse false; the GPUH B meter; no close-attempt) and seven minors. Round 2 accepted with four non-blocking points and two rulings; n1 (engine stop text in clear files) was fixed and confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `030063ad` | NOT ACCEPTED (B1; M1–M7; minors m1–m7) |
| 2 | `4b4e0878` | ACCEPTED (non-blocking n1–n4; rulings 1–2) |
| 3 | `258f5f72` | ACCEPTED (confirmation) |

**Open items.** (1) Prerequisite for any G.5 job: a reviewed harness unit adding `trackg/audit_g5.py` (both engine subcommands, the `ENGINE_CONTRACT` marker, the contract of report §2, infrastructure rows after 2 reruns, edit-caused failures classed as divergent (ruling 1), truncation-as-invalid in `manager_v2_diff.py`) at both G.5 harness commits. (2) Part 3b-2: the seal (the report's §5 list incl. `plan.tar`, the access log, wrapper logs, `wave_checks_wave<N>.json`, `_k_lock.json`, `_refusals/`, any `out/` left in clear, TASL-7's `server-N/`), the assembly, the two release locks, the REL-T1-G1B copy step with `crosscheck_gate.json`, the `llama-server.log` handling (access-logged seal, or prompt logging off as an author decision), the G5-TASL-GPUH B meter from TASL-7's server spans or a refusal of B (ruling 2), optionally the third-note check under ARPEND B and the close-attempt mtime refinement (n2). (3) Five proposed note lines for the author's signature (report §7: STOP 4 counting, audit-once across waves, baseline divergence in audits, and optionally the reuse-false and GPUH B meter readings) and the P5 citation stating that `audit_g5.py` hosts both subcommands (n4). (4) Disclose in the T1 report that `gpu_seconds`, missed deadlines and the campaign timing state are coarse timeout signals (n3). (5) Cluster: the harness smoke test checks binary outputs, edit-caused OOM/crash classification and normalised code-state hashes; C5 chunk deadlines with timeouts; C9 the meter against real card time incl. closed attempts; C10 a server restart with identical props.

## Round 1 (`030063ad`)

> Reviewed base: da6cd859a1f70ea937953fd9cb6fc2ec57902b9b (diff da6cd859..030063adf1163e4a50ba89b1c294aace0239fb4b: a2a9012d, 0e724879, 030063ad)
>
> ## Summary
>
> The unit is well built in most places:
> - It follows the draft's order of work (§3) closely, and the 3a switch still runs every check before the runner.
> - Each job does its preflight under the lease before it creates an attempt directory.
> - The plan, the ledgers and the audit rows stay out of clear.
> - The `serve_spec` refactor is pure.
> - The author's key claim holds. At both c025f89a and 2d09f9a9, `pilot_g4.py` hard-codes `PILOT_NODES`, `PILOT_SEED_BLOCK = range(4001, 4100)` and `ENGINEERING_ONLY`, and `noise_floor.py` has `RESERVED_SEEDS = (range(7001, 7011), range(9001, 10000))`. So G.5 needs a harness unit first, and the report says so clearly (§2 and Q1).
>
> I ran the targeted tests one file at a time. All pass:
>
> | Test file | Passed |
> |---|---|
> | test_t1_g5_job | 17 |
> | test_t1_g5_tasl | 107 |
> | test_t1_tasl_g4 | 30 |
> | test_t1_tasl_g1b | 45 |
> | htcondor/test_g4_h200 | 67 |
>
> G.4 and G.1b behaviour is unchanged. The worktree is clean.
>
> There is one blocking problem: the clear audit diagnostics let anyone recover evaluation-seed divergence counts, which §6 forbids. There are also several majors:
> - the plan reader breaks on real (binary) engine outputs;
> - PATH handling is missing;
> - two G.4 STOPs were not carried over;
> - infrastructure rows are misclassified as isolation STOPs;
> - `reuse_parent_runs: false` does not match the declared projection;
> - the G5-TASL-GPUH B meter undercounts;
> - there is no close-attempt for G.5.
>
> ## Findings
>
> ### B1. Evaluation-seed divergence counts are in clear `diagnostics.json`
> - **Where:** `g5_job.audit_diagnostics`, which writes `runs`, `runs_ok`, `runs_divergent_label_seeds` and `runs_infrastructure`.
> - **Problem:** `runs_ok` counts `ok` rows over all K seeds, but the divergent count is restricted to the label seeds. So the evaluation-seed divergent count of every chunk is runs − runs_ok − runs_divergent_label_seeds − runs_infrastructure. §6 says "no evaluation-seed count before release". R1-B2-DECOUPLE and PRE-DIV A make evaluation-seed divergence part of y_eval.
> - **Failure scenario:** I confirmed it with a probe on the module's own functions (rows divergent only at 7006 and 7007): `{runs: 40, runs_ok: 32, runs_divergent_label_seeds: 0, runs_infrastructure: 0}`, so 8 evaluation-seed divergent runs can be read from a file every operator, agent and reviewer reads before release.
> - **Fix:**
>   - Report outcome counts for the label seeds only (`runs_ok_label_seeds`, `runs_divergent_label_seeds`), and for the evaluation seeds report only the number of planned or executed runs.
>   - Add a test that no combination of clear fields gives an evaluation-seed outcome count.
>   - While there, make `check_diagnostics` a full nested schema. Today only top-level keys are fixed, so a future list of step indices would pass the "lists of ints" rule.
>
> ### M1. `tar_members` decodes every member under the prefix as UTF-8
> - **Where:** `g5_job.tar_members`, called by `next_chunk` (prefix `out/campaign/`) and by `audit_diagnostics` (prefix `out/`).
> - **Problem:** At c025f89a the campaign engine and `noise_floor.run_chunk` write full working copies (`runs/<id>/work`, `code/`, `run.log`) under their out directory. Any binary file there (a checkpoint, a .npy) raises `UnicodeDecodeError`. Even without binaries, the code reads every log and copy into memory, which is far more sealed content than the declared purpose needs.
> - **Failure scenario:** I confirmed it with a probe: a ledger plus `s001/work/model.pt` in out.tar gives `UnicodeDecodeError`. In `next_chunk` that becomes "unexpected … before the run", so every audit job of the wave refuses. The fix then needs a new paper commit, which means a re-issued note after signature.
> - **Fix:** open only the named members (`instance_*_*/campaign_ledger.jsonl`, `chunk.json`, `audit/rows.jsonl`), stream them with `extractfile`, and add a fake engine that writes a binary file.
>
> ### M2. The node environment's bin directory is not put on PATH
> - **Where:** `run_job`, before `setup(...)` and the engine.
> - **Problem:** G.1b (g1b_tasl.py:861) and G.4 (g4_tasl.py:578) prepend the node environment's bin directory to PATH before the node's shell `setup_command` and the engine. G.5 does not.
> - **Failure scenario:** `setup_command` (for example `python prepare.py`) runs with the orchestrator or system python. Data preparation then fails, or runs in a different environment from the noise floor the labels share.
> - **Fix:** copy G.1b's PATH line and add a test.
>
> ### M3. Two G.4 STOPs are not carried over
> - **Where:** `run_job` and `campaign_diagnostics`; the report's §1 STOP table.
> - **Problem:** §4's preamble applies every G.4 STOP to G.5, including "the 4090 timing STOP". G.4's `run_node_job` STOPs (TimingStop) when the run median exceeds the timeout basis, and STOPs when a recorded request lacked `cache_prompt: false`. G.5 implements neither, and the report does not say so.
> - **Failure scenario:** A slower host turns many runs into timeouts, which E5 counts as divergent, with no timing STOP. A server that caches prompts goes unnoticed.
> - **Fix:** compute both inside the job from the ledgers. Record only the STOP state (and, if the author allows, the run-seconds median) so that no value appears in the diagnostics. Test both.
>
> ### M4. Infrastructure audit rows become a node STOP 2
> - **Where:** `read_rows`; the `audit_g5` contract.
> - **Problem:** `read_rows` checks isolation (STOP 2), then `executed` and the state (integrity), and only then the outcome kind. A launch or kill failure row will usually have no effective isolation block, or `executed: false`. `audit_diagnostics` maps the "STOP 2" prefix to the node class.
> - **Failure scenario:** One transient launch failure in an audit chunk STOPs the node for the author, instead of becoming a STOP 7 infrastructure attempt.
> - **Fix:** check the kind first; let infrastructure rows skip the isolation and execution checks. State in the contract what `executed`, `isolation` and the reruns (draft "after 2 reruns") are for such rows. Add a test.
>
> ### M5. `reuse_parent_runs: false` departs from the declared projection
> - **Where:** `audit_plan`, which gives each group its own `<group>:parent` unit.
> - **Problem:** The draft's "every parent is re-run" cost (§2.4: 188.3 GPU-h for seven nodes, 349.5 for eight) comes from `g4_lib.g5_node`, where parents = 12 + keep_share × ran. That is one re-run per distinct parent state, shared by its children. The code re-runs a parent per audited proposal, so parents ≈ audited.
> - **Failure scenario:** At ran 144 that is about 144 parent units instead of about 41: roughly 1.5 × the audit hours the cap and P7 were sized on. STOP 9 (cap) then fires mid-table under a non-default option the author may sign.
> - **Fix:** use one parent unit per distinct parent state, separate from the candidate units (for example `parent:<state>`), or put the per-group reading to the author and fix the projection. Either way the report must say which.
>
> ### M6. Under G5-TASL-GPUH B the running meter counts only the worker card
> - **Where:** `gpu_hours_consumed`, `check_order` and `evaluate_stops`.
> - **Problem:** 3a allows launching under B ("both cards count"). §2.6 and STOP 9 need the running meter to count per G5-TASL-GPUH. Q7 defers the proposer hours to 3b-2, but STOP 9 acts during the table.
> - **Failure scenario:** Under B the table can pass the 425 GPU-h cap (both cards) by about 55–62 GPU-h before STOP 9 fires.
> - **Fix:** under B, add the proposer card's held span (from the server records, or at least the campaign job wall times) to the meter. Otherwise refuse B launches until 3b-2.
>
> ### M7. No close-attempt for G.5, and crashed attempts are not metered
> - **Where:** the `g5_tasl` CLI and `run_job`.
> - **Problem:** `G.next_attempt` refuses while an attempt has no `job_record.json`. G.1b and G.4 offer `close-attempt` for this; G.5 does not. The orchestrator shares the 8G scope with the engine, so an OOM kill or a reboot is a realistic way to leave such an attempt.
> - **Failure scenario:** One crash blocks that node's job, or that audit chunk, for good unless someone edits the sealed tree by hand. Even with G.1b's `close_attempt`, the record it writes has no `gpu_seconds`, so up to 24 h of worker time goes missing from the cap.
> - **Fix:** add a G.5 close-attempt that writes a record in the G.5 schema with the elapsed seconds, for both job and chunk directories. Test it.
>
> ### m1. STOP 8 for the baseline in audits mixes divergence and timeouts
> - **Where:** `e5`, where `baseline_timeout_seeds` counts every divergent outcome of the baseline.
> - **Fix:** split by the row's reason. A timeout is STOP 8 (timing); any other divergence is a node STOP like `baseline_failed`. Rename the field. See Q5.
>
> ### m2. The K lock is written before the chunk is chosen
> - **Where:** `k_lock` runs in preflight, before `next_chunk` and `next_attempt`.
> - **Problem:** A refused preflight still fixes K, which can block a legitimate K = 6 amendment "before the first audit chunk".
> - **Fix:** write the lock right after `next_attempt`. See Q6.
>
> ### m3. `check_engines` checks only that the files exist
> - **Problem:** `pilot_g4.py` exists at both current commits, so the campaign half of the check always passes.
> - **Fix:** look for a contract marker at the commit, for example `git grep -q 'run-g5'` or an `ENGINE_CONTRACT = "trackg_g5_campaign/v1"` constant. Also consider hosting both subcommands in `audit_g5.py` (P5 allows it), so that the ENGINEERING_ONLY pilot module stays G.4's.
>
> ### m4. The import-source check never covers `g5_job`
> - **Where:** `IMPORT_SOURCES` now lists `g5_job`, but `check_import_sources` skips modules that are not yet imported, and `job_runner` imports `g5_job` lazily after the binding. Run as a script, `g5_tasl` is `__main__`, so the `g5_tasl` that `g5_job` imports is not checked either.
> - **Fix:** run `check_import_sources` again after the import in `job_runner` and `serve`, or import `g5_job` before the binding.
>
> ### m5. Report and code disagree on the class of STOP 9 "past its deadline"
> - **Problem:** The report's table says node; the code raises `Stop`, which is infrastructure.
> - **Failure scenario:** A chunk with many timeouts misses its deadline and is re-run as a new attempt again and again until the cap.
> - **Fix:** make it node (the author decides), or correct the report and say why.
>
> ### m6. Dead code and test gaps
> Dead code:
> - the `"job"` loop in `evaluate_stops` (only complete attempts reach it);
> - the `FORBIDDEN_KEYS` whitelist (none of those keys matches the pattern);
> - `if lock["K"] != context["K"]` after `k_lock`;
> - `check_access_log`, which no production code calls yet.
>
> Test gaps:
> - the STOP 12 test changes `/props` before the wave, so it is refused at preflight; the case "same before, changed after" is untested;
> - no tests for infrastructure rows, a timeout, a tar failure, or the eval-seed leak;
> - the 3a test with `runner=None` now runs real `check_order` against the spec's real `runs_root` (`/home/dowling/...`). On TASL-2 it would read live records, and it can fail with "is complete". Isolate `runs_root`.
>
> ### m7. Smaller issues
> - `wave_checks.json` is rewritten: wave 1 is recomputed at the start of wave 2, and the meter can differ by then. Make it append-only.
> - `check_order` refusals and the "needs the server record" refusal happen before the lease, so they leave no `_refusals/` record.
> - §6 enumerates the clear diagnostics. `partial_label`, `complete_label` and `parent_divergent_seeds` are label-seed-only, so they are low risk, but they go beyond the list. Note them in the report or drop them.
>
> ## Rulings on the author's open questions
>
> 1. **Harness engines.** Correct, and confirmed against the harness. A separate reviewed harness unit is a hard prerequisite. The contracts are mostly well specified and consistent with P5: `audit_g5.py` is one of the two allowed additions, and `pilot_g4.py`, `manager_v2_diff.py` and `campaign_v2_diff.py` are changeable engine files. The contract must also specify:
>    - infrastructure rows (M4);
>    - which members appear in out (M1);
>    - that truncation-as-invalid lands in `manager_v2_diff.py`.
> 2. **"12 baselines".** Agreed: under parent reuse the projection is conservative. The inverse problem under reuse false is M5.
> 3. **STOP 4 "refusals".** The reading is defensible: the G.4 pilot reports `not_run_refused` (diff scope or malformed hunks) apart from `invalid`, and D4 counts it. But it decides what a declared STOP counts, so it needs one line in the note for the author to sign, not a silent code default. Treating "reply at the cap but not invalid" as an infrastructure STOP is fine.
> 4. **Audit-once across waves.** Consistent with §2.4's purpose ("coverage does not depend on job order"). Groups as STOP 1's denominator and for the band match §8's "audited" and the band. Disclose it in the note.
> 5. **Baseline divergence in audits.** Stopping is right and conservative, but the class should follow the reason (m1), and the note should record it, since §4 states it only for campaigns.
> 6. **K timing.** Move the lock to after `next_attempt` (m2).
> 7. **GPU-hour meter.** Whole wall time, CPU-only node included, is the right meter for one worker slot (§2.6 and §2.10). It is acceptable under A. Under B it is insufficient during the run (M6). The proposer-hours report can go to 3b-2.
> 8. **What 3b-2 must seal.** The author's list is right. Add:
>    - `wave_checks.json`, `_k_lock.json` and `_refusals/`;
>    - any `out/` left in clear after a tar failure or timeout;
>    - per wave, TASL-7's `server-N/` (record, end, `llama-server.log`).
>
>    During 3b-1's own lifetime no EVIDENCE job can run (no engines, and the signature needs the full P5 review), so nothing sealed is exposed yet. The one thing in clear that is actually unsafe is the diagnostics content in B1. `llama-server.log` will sit in clear on TASL-7 for the whole table span. That comes with the procedural seal, but 3b-2 must handle it: either access-logged sealing of the server run directory, or, as an author decision because it changes `server_argv`, starting the server with prompt logging off.
>
> On the other review points:
> - **plan.tar:** the right call (the plan shows kept diffs). `plan_index` (counts and hashes) is safe.
> - **Seed handling:** correct. Instances 5101–5112 are guarded, chunks and rows are checked against the K blocks (K = 6 excludes 7004–7005 and 7009–7010), and no exam seed or other seed is used.
> - **STOP counters:** they read only diagnostics, apart from the job-level STOPs 2 and 10 and STOP 11 from the access log.
>
> ## Notes for the cluster agent
> - In the harness unit's smoke test on TASL-2, check:
>   - that the engines' out trees contain binaries (M1);
>   - infrastructure rows with no isolation block (M4);
>   - that re-materialised `code_state_sha256` matches the ledger's normalised hashes (the raw versus normalised hash in `runner.py`).
> - C5: chunk deadlines when runs time out (3 × the slowest census run against 1.875 × `run_seconds` sizing).
> - C10: `/props` cannot detect a server restart with identical props (the same limit as G.4). Consider recording and checking the server pid or start time per wave.
> - C9: compare the meter with the real card time, including crashed attempts (M7).
>
> ## Process
> One independent reviewer, read-only on /tmp/pb/wt/g5b and /tmp/pb/wt/t1h (`git show` only; /tmp/pb/repo not touched). Only synthetic probes and targeted tests, one file at a time, with TMPDIR=/tmp/g5brev/t, PYTHONDONTWRITEBYTECODE=1 and AR_HARNESS_ROOT=/tmp/pb/wt/t1h. No secrets, sealed data, labels, evaluation values or server access. The worktree is clean at 030063ad. Scratch was moved to /tmp/g5brev/_to_delete/ (probe/, t/); nothing was deleted.
>
> VERDICT: NOT ACCEPTED (B1: the clear audit diagnostics let evaluation-seed divergence counts be recovered; fix B1 and M1–M7 in a further round)

## Round 2 (`4b4e0878`)

> Reviewed base: 030063adf1163e4a50ba89b1c294aace0239fb4b (round 2: the diff 030063ad..4b4e0878a00ad24af09c8f984c3fb3f3aed8ce5b, commits 467b9c47 and 4b4e0878; round 1 reviewed da6cd859..030063ad)
>
> ## Summary
> Every round-1 finding is fixed, and I checked each fix in the code and the tests. The author's summary is accurate. Targeted tests, one file at a time, all pass:
>
> | Test file | Passed |
> |---|---|
> | test_t1_g5_job | 23 |
> | test_t1_g5_tasl | 107 |
> | test_t1_tasl_g4 | 30 |
> | test_t1_tasl_g1b | 45 |
> | htcondor/test_g4_h200 | 67 |
>
> The worktree is clean at 4b4e0878. Nothing new blocks the unit. Four minor points follow; none needs another round.
>
> ## Round-1 findings: verified
> - **B1 (evaluation-seed outcomes in clear diagnostics): fixed.**
>   - Audit diagnostics now carry:
>     - `label_seed_runs`: ok, divergent and infrastructure counts on the label seeds only;
>     - `runs_planned_label` and `runs_planned_evaluation`, taken from the chunk plan rather than from the rows;
>     - `seeds_planned`.
>   - A missing row still STOPs the chunk.
>   - `check_diagnostics` is now a full nested schema: exact keys at every level, typed leaves, and seed lists limited to 7001–7010.
>   - `test_b1_…` checks that the diagnostics are identical whether the evaluation seeds are all ok, all divergent, or divergent except the baseline.
>   - `wave_e5` uses the label seeds only. I found no remaining field from which an evaluation-seed outcome count can be computed.
> - **M1 (decoding every tar member): fixed.** Only the named members are opened: the ledger pattern `instance_\d+_(history|none)/campaign_ledger.jsonl`, plus `out/chunk.json` and `out/audit/rows.jsonl`. They are streamed through `extractfile`, and a missing member is a STOP. The fake engines now write binary files.
> - **M2 (PATH): fixed,** as in G.1b and G.4, and tested.
> - **M3 (G.4's timing and cache_prompt STOPs): fixed in-job.**
>   - The diagnostics record only the states: a 0/1 for the median against the timeout basis, and the count of requests without `cache_prompt: false`.
>   - The median itself is never written.
>   - The timing STOP is timing class; the cache_prompt STOP is infrastructure.
> - **M4 (infrastructure rows read as STOP 2): fixed.** The row kind is checked first, and infrastructure rows become STOP 7, infrastructure class. The contract now says what such rows look like.
> - **M5 (`reuse_parent_runs: false`): fixed.** Each distinct parent state gets one `parent:<state>` unit, reused across the node's waves. Candidate units stay per group. This matches the projection `g4_lib.g5_node` uses for the cap (parents = 12 + keep share × ran).
> - **M6 (meter under G5-TASL-GPUH B): fixed** as a lower bound; ruling below.
> - **M7 (close-attempt): fixed.** `close_attempt` is on the CLI and works for job and chunk directories. It:
>   - checks the attempt's path;
>   - refuses if a process names the attempt, its pid is alive, it ran on another host, or the lease is held;
>   - writes a G.5-schema record that the meter counts.
> - **Minors:**
>   - m1: the baseline is split by reason (timeout → STOP 8 timing; other divergence → node STOP).
>   - m2: a read-only K check runs before the chunk; the lock is written after `next_attempt`.
>   - m3: both subcommands are in `audit_g5.py`; `check_engines` greps for the marker and both schemas.
>   - m4: the import check runs again after the lazy `g5_job` import.
>   - m5: deadline STOPs are node class.
>   - m6: the dead code is gone; `check_access_log` runs at every job start; the 3a test uses an isolated runs tree.
>   - m7: wave checks are append-only; refusals before the lease are recorded.
>   - New tests cover a STOP 12 change after the wave, an engine timeout, a tar failure, infrastructure rows and the leak.
>
> ## Rulings
> 1. **The one infrastructure bit (author's judgment call): acceptable.**
>    - An infrastructure failure is not an evaluation outcome.
>    - The chunk is re-run, so nothing from that run reaches y_eval.
>    - The bit is needed for STOP 7.
>    - Condition, for the harness contract and the cluster test: edit-caused failures (non-finite values, no metric, timeouts, crashes of the edited code, and an OOM kill caused by the edit) must be classed as divergent, never as infrastructure. Otherwise the bit becomes an outcome, and the chunk would be re-run in a loop.
>    - Optional hardening: drop `label_seed_runs.infrastructure`. Any infrastructure row already STOPs the chunk, so the field only lets a reader tell that the bit came from an evaluation seed.
> 2. **M6's lower bound: acceptable for 3b-1. Refusing B launches is not needed now.**
>    - No EVIDENCE job can launch before 3b-2 is reviewed (P5) and the note is signed. So the lower bound never governs a real run unless 3b-2 leaves it in place.
>    - 3b-2 must either replace it with TASL-7's server spans (`server_record` start to `server_end`) or make the switch refuse G5-TASL-GPUH B. Record this as a 3b-2 open item, beside the proposed `gpuh_b_meter` note line.
>
> ## Minor points (non-blocking)
> - **n1. Engine stop text reaches the clear files verbatim.** `campaign_record.stop` and `chunk_record.stop` from the harness go word for word into the clear `stop` field of the diagnostics and the job record. Fix: the harness contract should require stop text without values or per-seed outcomes (a fixed set of reasons is best), or the job should map it to a fixed set.
> - **n2. close-attempt overcounts.** It meters the time from the attempt's start to the moment it is closed, so a crash noticed late overcounts. That errs on the safe side for the cap but can trigger STOP 9 too early. Better: use the latest modification time under the attempt as the end, and record both.
> - **n3. Timing side channel (draft-sanctioned, disclose).** `gpu_seconds`, a missed deadline (STOP 9), and in campaigns the timing state are coarse signals of timeouts, and timeouts are divergent outcomes, including at evaluation seeds. §6 lists GPU-seconds explicitly, so this is allowed. The T1 report should disclose it.
> - **n4. Disclose in the P5 citation that `audit_g5.py` also runs campaigns.** Running the campaign subcommand from `audit_g5.py` meets P5's letter: it is a declared addition, outside `noise_floor`'s import closure. But P5 describes that file as "the audit runner", so the note's P5 citation should say it hosts both subcommands.
>
> ## Notes for the cluster agent
> - The harness unit's smoke test should check:
>   - how the runner classifies an OOM or crash caused by the edit (ruling 1);
>   - that only the named members are read from out.tar;
>   - that the ledger's normalised code-state hashes match the re-materialised states.
> - C5: chunk deadlines when runs time out. A missed deadline is now a node STOP.
> - C9: compare the meter with the real card time, closed attempts included, and under B with TASL-7's server spans.
>
> ## Open items carried to 3b-2 and the signature
> - Replace the G5-TASL-GPUH B lower bound (ruling 2).
> - The `llama-server.log` handling (the report's §5 item 8).
> - Seal everything in the report's §5 seal list.
> - The five proposed note lines in report §7 need the author's signature.
>
> ## Process
> - Read-only on /tmp/pb/wt/g5b and /tmp/pb/wt/t1h. Targeted tests only, with TMPDIR=/tmp/g5brev/t, PYTHONDONTWRITEBYTECODE=1 and AR_HARNESS_ROOT=/tmp/pb/wt/t1h. No secrets, sealed data, labels, evaluation values or server access.
> - Round-2 scratch was moved to /tmp/g5brev/_to_delete/t_round2.
> - The round-1 scratch I had moved to /tmp/g5brev/_to_delete/ (probe/, t/) is no longer there. I did not delete it; the environment's /tmp was probably cleared between rounds.
>
> VERDICT: ACCEPTED

## Round 3 (`258f5f72`)

> Reviewed base: 4b4e0878a00ad24af09c8f984c3fb3f3aed8ce5b (confirmation round: the diff 4b4e0878..258f5f7207f6f7d8415f3f56ff83896017bd206d, one commit, 258f5f72)
>
> ## Summary
> n1 is fixed. The report's new §9 records the open items accurately. No new problems.
>
> **n1, the code.** When an engine reports a stop, `campaign_diagnostics` and `audit_diagnostics` now write a fixed reason (`ENGINE_STOP_CAMPAIGN` or `ENGINE_STOP_AUDIT`) in place of the engine's own text. I checked where that text could still reach a clear file:
> - The record's `stop` comes from the diagnostics, so the job record carries the same fixed reason.
> - What the job raises, and so what the wrapper log shows, is the record's `stop`, so it is fixed as well.
> - The engine's stdout and stderr, and its `campaign_record.json` / `chunk_record.json`, exist only under `out/` and so only in `out.tar`.
> - The only other engine-related message is the exit code ("the engine exited N").
> - The two constants are defined after the functions that use them, but at module level, so they exist by the time those functions run.
>
> **n1, the test.** `test_job_stops_and_refusals` feeds an engine stop that names a seed and a value ("seed 7006 metric 0.81"). It then checks that neither appears in any clear JSON of the attempt, and that the job record carries the fixed reason. The test does its job.
>
> **Report §9** states the following correctly:
> - n2 is left open by choice. Overcounting errs toward the cap, the operator should close crashed attempts promptly, and the mtime refinement can come in 3b-2.
> - n3 is a disclosure item.
> - n4 is the wording of the note's P5 citation.
> - Ruling 1: the harness must class every edit-caused failure as divergent, never as infrastructure, in both its contract and its smoke test.
> - Ruling 2: 3b-2 replaces the lower bound with TASL-7's server spans, or the switch refuses G5-TASL-GPUH B.
> - It also lists the items carried to 3b-2 and the signature, and the harness unit as the prerequisite for any G.5 job.
>
> **Tests.** Run one file at a time with TMPDIR=/tmp/g5brev/t, PYTHONDONTWRITEBYTECODE=1 and AR_HARNESS_ROOT=/tmp/pb/wt/t1h:
>
> | File | Result |
> |---|---|
> | test_t1_g5_job | 23 passed |
> | test_t1_g5_tasl | 107 passed |
>
> The worktree is clean at 258f5f72. This commit changes only `g5_job.py` and the tests, which G.4 and G.1b don't import, so I didn't re-run the G.4 and G.1b tests.
>
> **Process.** Read-only on the worktree. No secrets, sealed data, labels, evaluation values or server access. Scratch is in /tmp/g5brev/_to_delete/t_round3. Nothing was deleted.
>
> VERDICT: ACCEPTED

---

Code-Commit: 258f5f7207f6f7d8415f3f56ff83896017bd206d
Verdict: ACCEPTED

Accepted at `4b4e0878`, confirmed at `258f5f72`.
