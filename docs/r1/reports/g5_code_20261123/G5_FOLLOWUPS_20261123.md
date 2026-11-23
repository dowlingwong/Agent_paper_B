# G.5 paper-side follow-ups to the reviewed harness engines (23 November 2026)

**Status.** Coded, committed locally and unit-tested with fakes in a CPU container. Nothing is pushed, nothing ran on
TASL-2 or a GPU, and no server was contacted. ENGINEERING_ONLY. AI-assisted (Claude). No label, evaluation value or
sealed file was read. `gate.py`, `gate_input_builder.py`, `release.py` and the preregistration are unchanged.

**Branch.** `mac-g5-followups-20261123`, from `mac-t1-features-20261123` @ `030b80a0` (G.5 code on main, READY 91, plus
the T1 features, READY 92). Code and tests: `3bbf9a17`; this report: the next commit.

**Harness contract followed.** The engines `trackg/audit_g5.py` at G5-7 `52e3c0b0` and G5-AR `00829da1`
(byte-identical `audit_g5.py`), their report `docs/r1/reports/trackg_g5_20261123/G5_ENGINES_20261123.md` (§2 items 11,
14, 15, 17; §6; §7) and their review record `docs/r1/reviews/G5_ENGINES_REVIEW_20261123.md`, all read with
`git show`.

## 1. The items, mapped to the harness report §7

| Harness §7 | What was built | Where | Tests |
|---|---|---|---|
| 1. `read_rows` checks every gate field | `row_isolated(row)`: `effective is True`, `waivers == {}`, `exceptions == []`, `log_intact is True`, `parent_traced_by` falsy, `parent_dumpable_at_accept` falsy, and no `gate_refusal` key. These are the field names `audit_g5._isolation_block` (`ISOLATION_KEYS`) and `audit_g5._row` write at `52e3c0b0`, and the same truth tests as `noise_floor.check_effective`. `read_rows` applies it to every row that is `ok` or `divergent`, every row with `executed: true` (an executed infrastructure row carries its block), and every row carrying `gate_refusal`; a failure is `STOP 2` (node). An infrastructure row that never executed (no isolation block) keeps its path to STOP 7. | `g5_job.row_isolated`, `g5_job.read_rows` | `test_followup_1_read_rows_needs_every_gate_field`; seal: `test_followup_reduce_rows_refuses_a_gate_refused_row` |
| 2. `stop_kind = deadline` → node STOP 9 | `ENGINE_STOP_KINDS` and `engine_stop(crec, engine)` read the structured `stop_kind` of `chunk_record.json` / `campaign_record.json` (never the text) and give a fixed clear reason and class (table in §2). In `audit_diagnostics` a node-class kind comes before the missing-rows check and STOP 7; a node-class row STOP (2 or 10) from `read_rows` keeps its own reason. In `campaign_diagnostics` it comes after the ledger STOP lines and STOP 4's prompt overflow, and before the `cache_prompt` check, the timing check, the ledger-set check and the proposal count. | `g5_job.engine_stop`, `audit_diagnostics`, `campaign_diagnostics` | `test_followup_2_audit_stop_kind_classes`, `test_followup_2_campaign_stop_kind_classes`, `test_followup_2_audit_deadline_through_the_job` |
| 3. Kill the `ar_*` run cgroups on `TimeoutExpired` | `kill_run_cgroups(cgroup_parent)`: writes `1` to `cgroup.kill` of every `ar_*` child of the job scope (the names `isolation.RunCgroup.create` gives), falling back to SIGKILL of each process in its subtree as `RunCgroup.kill` does, waits up to 10 s, then lists every `ar_*` child still populated (`cgroup.events`, else any non-empty `cgroup.procs` below it). `run_job` calls it in the `TimeoutExpired` branch, before the tar, and writes the result to `out/run_cgroups_kill.json` (sealed). If any `ar_*` child is still populated, or the scope cannot be read, or the helper raises: node STOP 9, and `out/` is **not** tarred or removed (a live process may still write there); the seal takes it as `out_clear.tar`, as for a tar failure. Otherwise node STOP 9 as before, with "its ar_* run cgroups were killed (none left)". | `g5_job.kill_run_cgroups`, `run_job` | `test_followup_3_kill_run_cgroups_with_fakes`, `test_followup_3_timeout_kills_run_cgroups_before_the_tar`; seal: `test_followup_seal_takes_out_kept_after_a_deadline_with_left_processes` |
| 4. `-p OOMPolicy=continue` | Added to the `g5` kind's `systemd-run --user --scope` only. g1b, g4 and xc keep `-p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` byte for byte in their argv: their tables ran with that scope, `continue` is already the default under `Delegate=yes`, and the G.1b join binds this file as job code. So a change there is not clearly safe and would buy nothing. | `t1_tasl_node.sh` | `test_followup_4_g5_scope_has_oompolicy_continue` (g5 argv; g1b, g4, xc unchanged) |
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

1. **OOMPolicy on the real scope.** systemd on TASL-2 accepts `-p OOMPolicy=continue` for a `--user --scope`.
   - This was not verified here. An older systemd would refuse the property, and the wrapper would exit 5 (scope
     failure) before any job.
   - Then, as in harness §6 item 10:
     - `systemctl --user show <scope> -p OOMPolicy` reads `continue`;
     - `memory.oom.group` is 0;
     - systemd-oomd does not act on the scope.
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
4. **Real rows through the real gate pass `read_rows`.** Every `ok` and `divergent` row of a real chunk has
   `log_intact: true`, `parent_traced_by` null and `parent_dumpable_at_accept` false or null, and no `gate_refusal`.
   This extends harness §6 item 6. If a gate refusal can be provoked safely, check that it gives STOP 2, node class,
   through the job.
5. **The recorded contract.** `job_record.json` → `engine.truncation_invalid_in` reads
   `autoresearch.trackg.audit_g5.TruncationInvalidManager`, and `check_engines` passes on both family checkouts
   (four needles).
6. **Harness §6 item 15** (one job through the real `run_job` with the `g5` kind of `t1_tasl_node.sh` in a delegated
   scope) now also exercises the `OOMPolicy` property.

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
| `r1/tests/test_t1_g5_job.py` | 30 passed (23 before; 7 new) |
| `r1/tests/test_t1_g5_seal.py` | 32 passed (30 before; 2 new) |
| `r1/tests/test_t1_g5_tasl.py` | 109 passed (one new test) |
| `r1/tests/test_t1_features.py` | 18 passed, 1 skipped (`lightgbm` not installed in this venv) |
| `r1/tests/test_t1_tasl_g4.py` | 30 passed |
| `r1/tests/test_t1_tasl_g1b.py` | 45 passed |
| `r1/tests/test_t1_tasl_crosscheck.py` (extra: the xc kind of the changed wrapper) | 30 passed |

**Not run:**
- the harness's `test_trackg_audit_g5.py` (the harness is read only by `git show` here);
- full suites.

Its paper cross-checks should still pass:
- its real runner and `FakeFactory` write the full six-key isolation block;
- the gate-refusal test expects STOP 2;
- `check_engines` greps only strings present at both commits.

**Residuals.**
- `kill_run_cgroups` sees only `ar_*` children of the scope. A process the dead engine left directly in the scope
  cgroup is not covered (the job itself lives there), nor is one in another cgroup. Smoke item 3 checks for both.
- On an orphan STOP, `out/` stays in clear until the seal. This is the same exposure as the existing tar-failure path.
  `run_cgroups_kill.json` names the `ar_*` cgroups, whose names contain run ids (unit index, seed, attempt). It is
  never copied into a clear record.
