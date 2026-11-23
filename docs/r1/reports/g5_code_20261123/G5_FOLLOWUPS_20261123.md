# G.5 paper-side follow-ups to the reviewed harness engines (23 November 2026)

**Status.** Revised after review round 1 (NOT ACCEPTED: one major, four minors, one nit) and round 2 (ACCEPTED with
three minors and one nit, applied); §9 maps each finding to its fix.
Coded, committed locally and unit-tested with fakes in a CPU container. Nothing is pushed, nothing ran on
TASL-2 or a GPU, and no server was contacted. ENGINEERING_ONLY. AI-assisted (Claude). No label, evaluation value or
sealed file was read. `gate.py`, `gate_input_builder.py`, `release.py` and the preregistration are unchanged.

**Branch.** `mac-g5-followups-20261123`, from `mac-t1-features-20261123` @ `030b80a0` (G.5 code on main, READY 91, plus
the T1 features, READY 92). Round 0: code and tests `3bbf9a17`, report `0540420c`. Round 1 fixes: `54bafc4a`. Round 2 points: the next commit.

**Harness contract followed.** The engines `trackg/audit_g5.py` at G5-7 `52e3c0b0` and G5-AR `00829da1`
(byte-identical `audit_g5.py`), their report `docs/r1/reports/trackg_g5_20261123/G5_ENGINES_20261123.md` (§2 items 11,
14, 15, 17; §6; §7) and their review record `docs/r1/reviews/G5_ENGINES_REVIEW_20261123.md`, all read with
`git show`.

## 1. The items, mapped to the harness report §7

| Harness §7 | What was built | Where | Tests |
|---|---|---|---|
| 1. `read_rows` checks every gate field | `row_isolated(row)`: `effective is True`, `waivers == {}`, `exceptions == []`, `log_intact is True`, `parent_traced_by` falsy, `parent_dumpable_at_accept` falsy, and no `gate_refusal` key. These are the field names `audit_g5._isolation_block` (`ISOLATION_KEYS`) and `audit_g5._row` write at `52e3c0b0`, and the same truth tests as `noise_floor.check_effective`. `read_rows` applies it to every row that is `ok` or `divergent`, every row with `executed: true` (an executed infrastructure row carries its block), and every row carrying `gate_refusal`; a failure is `STOP 2` (node). An infrastructure row that never executed (no isolation block) keeps its path to STOP 7. | `g5_job.row_isolated`, `g5_job.read_rows` | `test_followup_1_read_rows_needs_every_gate_field`; seal: `test_followup_reduce_rows_refuses_a_gate_refused_row` |
| 2. `stop_kind = deadline` → node STOP 9 | `ENGINE_STOP_KINDS` and `engine_stop(crec, engine)` read the structured `stop_kind` of `chunk_record.json` / `campaign_record.json` (never the text) and give a fixed clear reason and class (table in §2). In `audit_diagnostics` a node-class kind comes before the missing-rows check and STOP 7; a node-class row STOP (2 or 10) from `read_rows` keeps its own reason. In `campaign_diagnostics` it comes after the ledger STOP lines and STOP 4's prompt overflow, and before the `cache_prompt` check, the timing check, the ledger-set check and the proposal count. | `g5_job.engine_stop`, `audit_diagnostics`, `campaign_diagnostics` | `test_followup_2_audit_stop_kind_classes`, `test_followup_2_campaign_stop_kind_classes`, `test_followup_2_audit_deadline_through_the_job` |
| 3. Kill the `ar_*` run cgroups (round 1: after every engine exit) | `kill_run_cgroups(cgroup_parent)`: lists the `ar_*` children of the job scope with `os.scandir` (the names `isolation.RunCgroup.create` gives), writes `1` to each `cgroup.kill`, falls back to SIGKILL of each process in its subtree as `RunCgroup.kill` does (never pid ≤ 0, never the job itself), waits up to 10 s, then lists every `ar_*` child still populated (`cgroup.events`, else any pid in a `cgroup.procs` below it). Any read error (an unlistable scope, an unreadable `cgroup.procs`, a non-pid entry) gives `left: None`, "not verified". `run_job` calls it after **every** engine exit, before anything is read or tarred: the job's deadline kill (`TimeoutExpired`), any other exception from the engine call, and every return, rc 0 included (one `scandir` when the scope is clean; review m3). It writes the result to `out/run_cgroups_kill.json` (sealed). If `left` is not `[]`, or the helper raises: node STOP 9, and `out/` is **not** tarred or removed (a live process may still write there); the seal takes it as `out_clear.tar`, as for a tar failure. A second, read-only check (`run_cgroups_left`) runs just before the tar, and a start-of-job check (`orphan_run_cgroups`) refuses a job while any `ar_*` child of this or a sibling scope holds a process (review m2). | `g5_job.kill_run_cgroups`, `run_cgroups_left`, `orphan_run_cgroups`, `_reap`, `run_job` | `test_followup_3_kill_run_cgroups_with_fakes`, `test_followup_3_timeout_kills_run_cgroups_before_the_tar`, `test_review_m1_unlistable_scope_is_not_verified`, `test_review_m2_start_of_job_and_before_tar_checks`, `test_review_m3_run_cgroups_checked_after_every_engine_exit`, `test_review_n1_sigkill_fallback_skips_pid_0_and_itself`; seal: `test_followup_seal_takes_out_kept_after_a_deadline_with_left_processes` |
| 4. `-p OOMPolicy=continue` | **Not built (round 1, review M1).** Scope units accept `OOMPolicy=` only from systemd v253 (upstream `5fa09835`; v253 NEWS "Scope units now support OOMPolicy="), and TASL-2 runs `systemd 249 (249.11-0ubuntu3.23)` (`docs/r1/reports/trackg_g0_20261117/TASL2_T1_PRECHECK_20261121_captures/host_facts.txt`, line 44). On 249 a scope has no OOMPolicy and systemd does not act on an OOM kill inside it, so the property would most likely have made every g5 scope fail, and it buys nothing there. The "default under `Delegate=yes`" reason holds only from v253. The g5 argv is now identical to g1b's, g4's and xc's (`--user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`); only a comment in the wrapper records this. Smoke item 10 still checks `memory.oom.group` = 0 and that systemd-oomd leaves the scope alone. | `t1_tasl_node.sh` (comment only) | `test_review_M1_g5_scope_matches_the_other_kinds` (replaces the OOMPolicy test) |
| 5. `truncation_invalid_in` | `engine_contract()["truncation_invalid_in"]` is now `autoresearch.trackg.audit_g5.TruncationInvalidManager` (was `src/autoresearch/trackg/manager_v2_diff.py`); the module and contract docstrings say where the rule lives and that `manager_v2_diff.py` is unchanged. `check_engines` also greps `class TruncationInvalidManager(` in `audit_g5.py` at the family's G.5 commit, so the contract text recorded in every job record is checked against the harness (present once at both `52e3c0b0` and `00829da1`, checked with `git show`). `g5_tasl.ENGINE_FILES` (P5's list) keeps `manager_v2_diff.py`. | `g5_job.engine_contract`, `check_engines` | `test_engine_contract_and_wrapper` (updated) |
| 6. `campaign_attribution` note line | Not code: listed in §4 for the author's signature. | — | — |
| (wording fix) | `decision_row_checks` now refuses `decisions_row == e4_amendment_row` under G5-MEM A ("must be two rows"). Its docstring, the 3A report's amendment and the G.5-on-main merge report now say what the code does: `plan_row` strips only the id cell, so a row whose text names its own id, "E4" and "memory modes" would have passed the two term checks. The explicit refusal was simple, so it is built and tested. Note: the merge report did not itself claim that such a row "is refused"; a one-line note was added there. The 3A amendment did, and is corrected. The review records keep their wording. | `g5_tasl.decision_row_checks`; `G5_CODE_3A_20261123.md`, `G5_CODE_MAIN_MERGE_20261123.md` | `test_followup_6_one_row_cannot_serve_as_decisions_and_e4_row` (the term checks alone pass the self-citing row; the helper and the switch refuse it, before any job) |

**Fakes.** The fake engines in `test_t1_g5_job.py` and `test_t1_g5_seal.py` now write `stop_kind` beside `stop` in
both records, as the real engines do, and their rows carry the six-key isolation block (`log_intact: true`,
`parent_traced_by: null`, `parent_dumpable_at_accept: false`). Both tests' fixtures use a scope cgroup under
`tmp_path`, so the deadline path never writes `cgroup.kill` under a real `/sys/fs/cgroup` path. One existing test's
engine stop text was `ManagerTransportStop: …`; it now reads `RuntimeError: …` with kind `error`, since a transport
stop is now classed by its kind (tested separately). `test_t1_features.py`'s `RealisticEngine` (READY 92's file)
still writes `{"stop": null}` without `stop_kind`; that is read as no stop, and the file was left untouched.

## 2. `stop_kind` → STOP and class

From the harness report §2 item 17 (the values) and the 3b-1 report's STOP table (the classes). The clear diagnostics
and job record carry only the fixed reason; the engine's own `stop` text stays in `out.tar`.

| `stop_kind` | STOP | Class | Clear reason (fixed) | Basis |
|---|---|---|---|---|
| `deadline` | 9 | node | "the {campaign\|audit} engine stopped at the job deadline, as no further run or manager call could finish before it" | 3b-1 table, STOP 9 "a job past its deadline"; 3b-1 review m5 and C5; harness review decision 3 |
| `unisolated` | 2 | node | "… stopped on the isolation gate (stop_unisolated)" | 3b-1 table, STOP 2 |
| `baseline_failed` | 6 | node | "… stopped on a failed baseline (baseline_failed)" | 3b-1 table, STOP 6 `baseline_failed` |
| `integrity` | 6 | infrastructure | "… stopped on an integrity check (stop_integrity)" | 3b-1 table, STOP 6 `stop_integrity` |
| `transport` | 6 | infrastructure | "… stopped on the proposer transport (stop_transport)" | 3b-1 table, STOP 6 `stop_transport` |
| `refused`, `runner`, `error` | — | infrastructure | `ENGINE_STOP_CAMPAIGN` / `ENGINE_STOP_AUDIT` (unchanged) | not defined in 3b-1 / 3b-2; as before |
| absent, `null` with a `stop`, or an unknown value | — | infrastructure | as above (an unknown value is never echoed) | as before |

**Precedence.**
- **Audit.** A node-class row STOP from `read_rows` (2 or 10) keeps its own reason. Otherwise a node-class kind wins
  over every infrastructure-class row result: missing rows, an integrity row, a schema error, or STOP 7.
  - A deadline stop always leaves planned runs without a row.
  - So does a gate refusal on an infrastructure outcome: the engine writes no row for it.
  - Before this unit, both of these reached the job as infrastructure.
- **Campaign.** The ledger STOP lines (2, 8, 6) and STOP 4's prompt overflow come first. These are a different stop of
  the same wave, and the first STOP ends the wave. Then a node-class kind. Then the `cache_prompt` (infrastructure)
  and timing checks, the generic engine stop, the ledger set and the proposal count.
  - **Disclosed choice:** a deadline also outranks the timing STOP. Both stop the node (`node_stopped` treats node and
    timing alike).
  - In a campaign, `unisolated` and `baseline_failed` already come with their ledger lines, which are caught first.
    The kind mapping there is a backstop.

## 3. What the TASL-2 smoke must still check

All 15 items of the harness report §6 are still open; nothing here ran on TASL-2. The paper side adds or sharpens these:

1. **systemd OOM handling on the real scope** (harness §6 item 10, adjusted for systemd 249; round 1, review M1).
   No `OOMPolicy=` is passed: TASL-2's systemd 249 has none for scopes and does not act on an OOM kill inside one
   (`host_facts.txt` line 44). Check instead:
   - `systemd-run --version` still reports 249 (if TASL-2 moves to v253 or later, `OOMPolicy` of a delegated scope
     defaults to `continue`; `systemctl --user show <scope> -p OOMPolicy` then shows it);
   - the scope's `memory.oom.group` is 0;
   - systemd-oomd (`oomctl`, `ManagedOOMMemoryPressure` on `user@.service`) does not act on the scope.
2. **The engine's own deadline STOP through the job, both engines.** A campaign wave and an audit chunk run with a
   deliberately short deadline. Check:
   - the job record shows `STOP 9: the … engine stopped at the job deadline … (stop_kind deadline; …)`, class `node`;
   - `node_stopped` refuses the next job of the node;
   - no engine text reaches a clear file.
3. **The job's own deadline kill (`TimeoutExpired`).** Force the job's subprocess timeout while a run is in flight (a
   slow edit). Check:
   - `out.tar` holds `out/run_cgroups_kill.json`, with that run's `ar_*` cgroup listed in `run_cgroups` and
     `left: []`;
   - `ls <scope>/ar_*` shows none populated afterwards;
   - the job user can write `cgroup.kill` of the runner's `ar_*` children in the delegated scope;
   - no process of the run survives (`nvidia-smi --query-compute-apps` empty).

   This covers harness §6 item 11 for the job's kill. The engine's own deadline STOP (item 2 above) should leave no
   `ar_*` child at all.
   - **Deliberate engine kill** (harness §6 item 11; review m3): kill the engine process by hand mid-run. The job
     sees a non-zero exit, runs the same kill, and `run_cgroups_kill.json` shows `left: []`.
   - **Orphan rule** (review m2): with an `ar_*` child of an old scope deliberately kept populated (for example a
     stopped `sleep` moved into it), a new job through the wrapper refuses before any attempt with "…hold processes…;
     operator rule: …", and runs again once it is cleared. This also checks that the start-of-job scan can read the
     sibling scopes under the user's `app.slice` (if it cannot, every job refuses, fail-closed).
4. **Real rows through the real gate pass `read_rows`.** Every `ok` and `divergent` row of a real chunk has
   `log_intact: true`, `parent_traced_by` null and `parent_dumpable_at_accept` false or null, and no `gate_refusal`.
   This extends harness §6 item 6. If a gate refusal can be provoked safely, check that it gives STOP 2, node class,
   through the job.
5. **The recorded contract.** `job_record.json` → `engine.truncation_invalid_in` reads
   `autoresearch.trackg.audit_g5.TruncationInvalidManager`, and `check_engines` passes on both family checkouts
   (four needles).
6. **Harness §6 item 15** (one job through the real `run_job` with the `g5` kind of `t1_tasl_node.sh` in a delegated
   scope) also shows the exit-time check on a clean exit: `run_cgroups_kill.json` in `out.tar` with `left: []`.

## 4. For the author's signature

The harness report §7 item 6 proposes this note line (review decision 4). It is quoted verbatim, for the author to
sign or amend:

```
campaign_attribution: in G.5 campaigns, a frozen parent killed at the job scope's memory limit (oom and oom_kill both rose), a fault signal of the frozen parent that recurs on the rerun of the same code state and seed, and a default infrastructure log pattern that appears only after AR_DEVICE and recurs on that rerun are discarded_divergent (audited, tabled, counted in divergent_in_campaign), not infrastructure_failure_final
```

Nothing in this unit adds a note line. The classes in §2 follow the 3b-1 table, which the note's existing STOP lines
already cite.

## 5. Checks run

One file at a time, using `/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider`, with
`TMPDIR=/tmp/g5fudev/t`, `PYTHONDONTWRITEBYTECODE=1` and `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`:

| File | Result |
|---|---|
| `r1/tests/test_t1_g5_job.py` | 37 passed (34 after round 1) |
| `r1/tests/test_t1_g5_seal.py` | 32 passed |
| `r1/tests/test_t1_g5_tasl.py` | 109 passed |
| `r1/tests/test_t1_features.py` | 18 passed, 1 skipped (the skip: `lightgbm` not installed in this venv) |
| `r1/tests/test_t1_tasl_g4.py` | 30 passed |
| `r1/tests/test_t1_tasl_g1b.py` | 45 passed |
| `r1/tests/test_t1_tasl_crosscheck.py` (the xc kind of the wrapper) | 30 passed |

Round 0 had 30 / 32 / 109 in the first three files (23 / 30 / 108 before this unit).

**Harness cross-check (round 1, review m4).** The harness at G5-7 `52e3c0b0` was extracted with
`git -C /tmp/pb/harness archive 52e3c0b0 | tar -x -C /tmp/g5fudev/h`. The shared checkout was not touched. Then, in
`/tmp/g5fudev/h`, the same environment and `AR_G5_PAPER_ROOT=/tmp/pb/wt/g5fu`, `tests/trackg/test_trackg_audit_g5.py`:
**63 passed** (about 89 s after round 1; again 63 passed, about 92 s, after round 2). A probe confirmed the imports: `autoresearch.trackg.audit_g5` from `/tmp/g5fudev/h/src`, `g5_job` from
`/tmp/pb/wt/g5fu/sweep2/t1_tasl`, with this unit's `truncation_invalid_in`. Its paper cross-checks therefore pass
against this branch: the real-runner end-to-end tests through `campaign_file`, `campaign_diagnostics`,
`tar_members`, `read_rows` and `reduce_rows`; the gate-refusal row giving STOP 2; and the contract constants.

**Not run:** full suites.

**Residuals.**
- `kill_run_cgroups` sees only `ar_*` children of the scope. A process the dead engine left directly in the scope
  cgroup is not covered (the job itself lives there), nor is one in another cgroup. Smoke item 3 checks for both.
- After an orphan STOP, the job does not clear the scope itself. The rule is the operator's ("clear the scope by hand
  … before any further job"), stated in the clear STOP reason. The start-of-job check makes a later job refuse while
  an orphan remains. The seal (`g5_seal.seal_attempt`) does not check processes: the operator clears the scope before
  sealing such an attempt. On a GPU node, an orphan on the card is also caught by the existing `check_no_foreign`.
- On an orphan STOP, `out/` stays in clear until the seal. This is the same exposure as the existing tar-failure path.
  `run_cgroups_kill.json` names the `ar_*` cgroups, whose names contain run ids (unit index, seed, attempt). It is
  never copied into a clear record.

## 9. Review round 1 (NOT ACCEPTED: M1, m1–m4, n1) and the fixes

| Finding | Fix | Tests |
|---|---|---|
| **M1** `-p OOMPolicy=continue` would most likely make every g5 scope fail on TASL-2 (scopes accept it only from systemd v253; TASL-2 runs 249) | Property dropped. The g5 argv now equals the other kinds'. The wrapper comment and §1 row 4 / §3 item 1 record that on systemd 249 scopes have no OOMPolicy and systemd does not act on an OOM kill inside them, citing `host_facts.txt` line 44. Smoke item 10 keeps `memory.oom.group` = 0 and systemd-oomd. | `test_review_M1_g5_scope_matches_the_other_kinds` (the OOMPolicy test removed; g5, g1b, g4, xc argv identical) |
| **m1** `Path.glob` swallows `PermissionError`, so an unlistable scope gave `left: []` | `_run_cgroup_names` lists with `os.scandir`; `_subtree_pids` reads `cgroup.procs` and walks with `os.scandir`; `_cgroup_populated` lets read errors through. `kill_run_cgroups`, `run_cgroups_left` and `orphan_run_cgroups` catch `OSError` explicitly and give `left: None` / `None`, which is the STOP. A cgroup that is gone holds nothing; a non-pid entry counts as unreadable. | `test_review_m1_unlistable_scope_is_not_verified` (`os.scandir` patched to deny the scope; unreadable `cgroup.procs`; a non-pid entry; an unreadable sibling) |
| **m3** the `ar_*` check ran only on `TimeoutExpired` | `run_job` runs the kill and requires `left == []` after every engine exit: the deadline kill, any other exception from the engine call, and every return. **Choice:** rc 0 is checked too; it costs one `scandir` on a clean scope. Otherwise: node STOP 9 (`ORPHANS_EXIT` / `ORPHANS_DEADLINE`), `out/` untarred. | `test_review_m3_run_cgroups_checked_after_every_engine_exit` (rc 0, 3 and −9 with a left-over child; an engine call that raises; a clean rc 0 run has `left: []` in `out.tar`) |
| **m2** nothing enforced clearing the scope after an orphan STOP | Three checks. (1) The exit-time kill (m3). (2) Just before the tar, a read-only `run_cgroups_left` of the scope; if not `[]`: node STOP 9 (`ORPHANS_BEFORE_TAR`), `out/` untarred. (3) At the start of every job, before any attempt directory, `orphan_run_cgroups` scans the `ar_*` children of this scope **and its sibling cgroups**, since each job runs in a fresh scope and an earlier job's orphan lives in its old one. If any holds a process, or they cannot be read, the job refuses: a count only, no cgroup names, so no seed reaches `_refusals/`. The clear reasons state the operator rule ("clear the scope by hand (kill every process in its ar_* child cgroups) before any further job; a job refuses to start while one holds a process"). **Not built:** the job does not kill an earlier job's orphans itself, and the seal does not check processes. Both are left to the operator rule (§5 residuals). | `test_review_m2_start_of_job_and_before_tar_checks` (a sibling scope's orphan refuses the job and leaves no seed in the refusal; a non-`ar_*` child is ignored; a child populated after the exit-time kill STOPs before the tar); `test_followup_3_timeout_kills_run_cgroups_before_the_tar` (after an orphan STOP the next job refuses until the orphan is cleared) |
| **m4** harness cross-check not run | Run from a `git archive` extraction of `52e3c0b0` in `/tmp/g5fudev/h`, with `AR_G5_PAPER_ROOT` at this worktree: 63 passed (§5). | — |
| **n1** SIGKILL fallback could signal pid 0 or the job | The fallback skips `pid <= 0` and `os.getpid()`. | `test_review_n1_sigkill_fallback_skips_pid_0_and_itself` |

The fake tests were adjusted so the fake engine creates its `ar_*` run cgroup while it runs, as the real runner does.
A populated child created before the job would now, correctly, refuse the job at its start. The sigkill-fallback fake
makes `cgroup.kill` a dangling symlink instead of a directory, since a directory is now walked as a child cgroup.

### Round 2 (ACCEPTED `54bafc4a`; three minors and one nit, applied)

| Point | Change | Tests (`test_t1_g5_job.py`) |
|---|---|---|
| **m1** the pre-tar orphan STOP replaced an earlier recorded stop | The earlier reason is kept: `ORPHANS_BEFORE_TAR + "; recorded before: " + prior`, class node. It reaches `job_record.json` and `diagnostics.json` alike, since the diagnostics take the record's stop. The earlier stops are the job's fixed, clear-safe reasons. | `test_round2_m1_before_tar_stop_keeps_the_earlier_reason` (an audit chunk with rc 0 and a recorded STOP 2, then a pre-tar re-check that cannot read a child: both reasons in both files) |
| **m2** a sibling unit ending during the start-of-job scan gave a false refusal | In `orphan_run_cgroups`, a sibling whose `scandir` raises `FileNotFoundError` and that no longer exists is skipped. An `ar_*` child that is gone already counts as clean (`_cgroup_populated`). Every other `OSError`, including `FileNotFoundError` on a path that still exists, still fails closed. | `test_round2_m2_a_sibling_that_ends_during_the_scan_is_clean` (a unit that ends between the listing and its scan; an `ar_*` child removed after its listing; a permission error still gives None) |
| **m3** the refusal gave only a count | **Chosen:** name the sibling units, never the `ar_*` cgroups. The `ar_*` names carry run ids; an audit run is `u<unit>_s<seed>_a<attempt>`, so a seed would reach `_refusals/`. A unit name is given only when it has systemd-run's own form (`run-r<hex>.scope` / `run-u<n>.scope`, `SAFE_UNIT`), which carries no seed or value. Any other unit is written `<other unit>`, because its name cannot be vouched for. The operator rule in every orphan text now says "inspect user@<uid>.service/app.slice/*/ar_* (this job's scope is the record's cgroup.cgroup_parent) before killing anything". The sealing constraint wins over naming. | `test_review_m2_start_of_job_and_before_tar_checks` (two orphans: `run-u77.scope` is named, a `train-7007.scope` unit is `<other unit>`; no seed, `ar_*` name or odd unit name in `_refusals/`) |
| **n1** the sibling scan ran wherever the scope was | `user_manager_scope`: the sibling scan runs only if the scope lies under this user's `user@<uid>.service` (a path component of a parent; `os.getuid()`). Otherwise `orphan_run_cgroups` gives None, so the job refuses (fail-closed). The fakes in `test_t1_g5_job.py` and `test_t1_g5_seal.py` now use `tmp_path/user.slice/user-<uid>.slice/user@<uid>.service/app.slice/run-r1a2b.scope`. | `test_round2_n1_sibling_scan_only_under_the_user_manager` (a `system.slice` scope, another uid's manager, this user's manager) |

**Smoke (§3 item 3, orphan rule):** also check that the real scope path contains `user@<uid>.service` for the
job's user, and that the refusal names the old scope as `run-r….scope` or `run-u….scope`.
