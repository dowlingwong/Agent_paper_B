Reviewed base: `030b80a0` (mac-t1-features-20261123: the G.5 code on main, READY 91, plus the T1 features, READY 92); accepted at `54bafc4a`, confirmed at `15877e877`

# Independent review record — the G.5 paper-side follow-ups to the reviewed harness engines (harness report §7 items 1–5, the E4 single-row refusal)

**Unit.** On `mac-g5-followups-20261123` (on `030b80a0`): `sweep2/t1_tasl/g5_job.py` (`row_isolated` in `read_rows`: `effective` True, `waivers == {}`, `exceptions == []`, `log_intact` True, no `parent_traced_by`, no `parent_dumpable_at_accept`, no `gate_refusal` on executed rows, else node STOP 2; `ENGINE_STOP_KINDS` / `engine_stop` mapping the engines' structured `stop_kind` (deadline → STOP 9 node, unisolated → STOP 2 node, baseline_failed → STOP 6 node, integrity and transport → STOP 6 infrastructure, others generic infrastructure) in `audit_diagnostics` and `campaign_diagnostics`; after every engine exit, `cgroup.kill` of the scope's `ar_*` children with a SIGKILL fallback, a verified-empty check, a read-only re-check before the tar and a start-of-job refusal while any `ar_*` child of the job's scope or a sibling scope under this user's `user@<uid>.service` holds a process, each failing closed with node STOP 9 and `out/` left untarred; `truncation_invalid_in` = `autoresearch.trackg.audit_g5.TruncationInvalidManager`, also grepped by `check_engines`), `sweep2/t1_tasl/g5_tasl.py` (`decision_row_checks` refuses `decisions_row == e4_amendment_row` under G5-MEM A), `sweep2/t1_tasl/t1_tasl_node.sh` (comment only: no `OOMPolicy=` on scopes under TASL-2's systemd 249), tests in `test_t1_g5_job.py`, `test_t1_g5_seal.py`, `test_t1_g5_tasl.py`, and the report `docs/r1/reports/g5_code_20261123/G5_FOLLOWUPS_20261123.md`. `gate.py`, `gate_input_builder.py`, `release.py`, `r1/liveness/gate.py` and the preregistration are unchanged. Authority: the accepted harness engines (READY 95) report §7; the user's queue of 23 Nov 2026 (14:02), item 2.

**Process.** One independent reviewer, read-only, fakes only, its own detached worktrees and a `git archive` copy of the harness at `52e3c0b0` for the cross-check (`tests/trackg/test_trackg_audit_g5.py` with `AR_G5_PAPER_ROOT` at the reviewed tip: 63 passed in every round). Round 1 found one major (`-p OOMPolicy=continue` on the g5 scope: scopes accept it only from systemd v253, and the repo's captures record systemd 249 on TASL-2, so every g5 job would have failed to start) and four minors plus a nit; round 2 accepted with three minors and a nit, applied and confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `0540420c` | NOT ACCEPTED (M1; minors m1–m4, nit n1) |
| 2 | `54bafc4a` | ACCEPTED (minors m1–m3, nit n1) |
| 3 | `15877e87` | ACCEPTED (confirmation) |

**Open items.** Optional: tighten `SAFE_UNIT` to systemd's exact forms `run-r[0-9a-f]{32}\.scope` / `run-u[0-9]+\.scope` (not a leak). For the author's signature: the `campaign_attribution` note line (harness report §7 item 6, quoted in the report). TASL-2 smoke before any EVIDENCE job: harness report §6 items 1–15 plus this report's additions (the real scope path contains `user@<uid>.service`; the user's `app.slice` siblings are readable; `memory.oom.group` = 0 and systemd-oomd leaves the scope alone; no `ar_*` processes after a deadline STOP and after a deliberate engine kill; a refusal names an old scope in `run-r…`/`run-u…` form). Operator rule: after any orphan STOP, inspect `user@<uid>.service/app.slice/*/ar_*` and clear the scope by hand before any further job.

## Round 1 (`0540420c`)

> Reviewed base: 0540420c (mac-g5-followups-20261123; base 030b80a0)
>
> ## Summary
> The unit is not accepted. One major finding blocks it: the OOMPolicy change in the wrapper will very likely stop every G.5 job from starting on TASL-2. The other five items are sound against the harness, and every test run passed.
>
> ## What I ran
> Detached worktree at `0540420c`. Tests one file at a time: test_t1_g5_job 30 passed; test_t1_g5_seal 32; test_t1_g5_tasl 109; test_t1_features 18 passed, 1 skipped (no lightgbm); test_t1_tasl_g4 30; test_t1_tasl_g1b 45; test_t1_tasl_crosscheck 30. Harness cross-check: the harness at `52e3c0b0` extracted with `git archive` into scratch; `tests/trackg/test_trackg_audit_g5.py` with `AR_G5_PAPER_ROOT` at the worktree: 63 passed, 0 skipped. `audit_g5.py`, `noise_floor.py`, `runner.py` and `isolation.py` are identical at `52e3c0b0` and `00829da1`. The shared checkouts stayed clean.
>
> ## Major
> **M1 — `sweep2/t1_tasl/t1_tasl_node.sh:49` (comment :13–15; report §1 row 4, §3 item 1).** `-p OOMPolicy=continue` will very likely make every g5 scope fail on TASL-2. Scope units accept `OOMPolicy=` only from systemd v253 (upstream 5fa09835; v253 NEWS "Scope units now support OOMPolicy="). The repo's own captures record `systemd 249 (249.11-0ubuntu3.23)` on TASL-2 (`docs/r1/reports/trackg_g0_20261117/TASL2_T1_PRECHECK_20261121_captures/host_facts.txt:44`). No jammy backport found up to 0ubuntu3.12. Failure: `systemd-run --user --scope … -p OOMPolicy=continue` refused as an unknown assignment, wrapper exits 5 before any job. The stated reason ("the default under Delegate=yes") holds only from v253; on 249 scopes have no OOMPolicy and do not act on OOM kills. Fix: drop the property and record this in the report; smoke item 10 still checks `memory.oom.group` = 0 and systemd-oomd. g1b, g4 and xc argv byte-identical; no hash binds the wrapper.
>
> ## Minor
> **m1 — `g5_job.py:1108–1111, 1131` (`_cgroup_populated` :1088).** A scope that exists but cannot be listed counts as "none left": Python 3.12's `Path.glob` swallows `PermissionError`, giving `run_cgroups: []`, `left: []` (reproduced with `os.scandir` patched). The report says the opposite. Fix: `os.scandir` with explicit `except OSError` → `left: None`.
> **m2 — `g5_job.py:1033, 1055`.** After an "orphans" STOP nothing enforces clearing the scope before any further job; the GPU lease is released while a run may be alive; `seal_attempt` does not check the `ar_*` children are empty before tarring and removing `out/`. Strictly better than base; not blocking.
> **m3 — `g5_job.py:989`.** The `ar_*` check runs only on `TimeoutExpired`; on any other abnormal engine exit (OOM kill on the engine, deliberate kill) a frozen parent can survive while `out/` is tarred and removed. Harness §6 item 11 expects no orphans after a deliberate engine kill. Fix: call `kill_run_cgroups` and require `left == []` after every non-zero or abnormal exit.
> **m4 — report §5 "Not run".** The harness cross-check was not run by the author; its prediction is right (63 passed).
>
> ## Nit
> **n1 — `g5_job.py:1127`.** The fallback calls `signal_pid(pid, SIGKILL)` without filtering `pid > 0` and `pid != os.getpid()`; a `0` would kill the job's own process group.
>
> ## Verified correct
> Item 1: `row_isolated` applies exactly `noise_floor.check_effective`'s tests with `_isolation_block`'s names; executed infrastructure rows carry a gate-passed block; never-executed rows keep STOP 7; gate refusal on an infrastructure outcome gives `stop_kind: unisolated` → STOP 2 node; repeated after-`AR_DEVICE` divergent rows pass. Item 2: all eight engine `STOP_KINDS` mapped deliberately; audit and campaign ordering correct; deadline outranking timing is disclosed and acceptable. Item 3: only direct `ar_*` children of the job's own scope; late joins covered by the grace loop; STOP 9 consistent with the tar-failure path. Items 5 and 6 correct. Invariants: 9 files changed; gate.py, gate_input_builder.py, release.py, r1/liveness/gate.py unchanged. The `campaign_attribution` line matches harness §7 item 6 byte for byte.
>
> VERDICT: NOT ACCEPTED

## Round 2 (`54bafc4a`)

> Reviewed base: 54bafc4a (one commit on 0540420c)
>
> ## Summary
> Accepted. All round-1 findings are fixed, every test passes, and nothing new blocks. Three minor points and one nit remain; each can wait for a later unit.
>
> ## What I ran
> Fresh detached worktree at `54bafc4a`. test_t1_g5_job 34 passed; test_t1_g5_seal 32; test_t1_g5_tasl 109; test_t1_features 18 passed, 1 skipped (no lightgbm); test_t1_tasl_g4 30; test_t1_tasl_g1b 45; test_t1_tasl_crosscheck 30. Harness cross-check (`52e3c0b0` via `git archive`, `AR_G5_PAPER_ROOT` at the worktree): 63 passed, 0 skipped; the new `out/run_cgroups_kill.json` member does not upset `tar_members`. Shared checkouts clean.
>
> ## Round-1 findings
> - **M1 fixed.** Against `030b80a0` the wrapper's only change is 5 comment lines; the g5 argv is byte-identical to g1b, g4 and xc and a test asserts this for all four; systemd 249 and the v253 requirement cited correctly.
> - **m1 fixed.** `os.scandir`; read errors give `left: None` (STOP); the test denies the scope and covers an unreadable `cgroup.procs` and a non-pid entry.
> - **m2 fixed** with the before-tar re-check and the start-of-job refusal.
> - **m3 fixed.** `_reap` runs after a timeout, any other exception and every return, rc 0 included; the deadline `NodeStop` cannot be caught twice.
> - **m4 fixed** (63 passed confirmed). **n1 fixed.**
>
> ## The questions put to me
> 1. **Sibling-scope scan.** Bounded to the job user's own `app.slice` (TASL-2 captures: `user.slice/user-1008.slice/user@1008.service/app.slice/run-r….scope`); reads directory names and `cgroup.events` (or `cgroup.procs`), writes nothing, reports a count. Concurrent jobs cannot trigger it: g1b, g1b_ar, g4 and g5 take the same non-blocking `~/r1_locks/gpu0.lock` before the scan. Remaining positives are an earlier job's leftover `ar_*` cgroup (intended) or a same-user harness process without the lease (real foreign load). Fail-closed risk low; in smoke item 3.
> 2. **Before-tar override.** It can hide a more serious stop in the clear records (replaces `record["stop"]` and the diagnostics' stop); almost never fires; minor.
> 3. **Test changes.** Do not weaken anything: fakes must create `ar_*` while running; the dangling `cgroup.kill` symlink still makes the write fail and the test still asserts `sigkill_each` and kills `[6161]`; the OOMPolicy test is replaced by an argv-equality test for all four kinds.
>
> ## Minor
> **m1 — `g5_job.py`, the pre-tar `run_cgroups_left(...) != []` block.** rc 0 with a recorded STOP 2, then a transient `OSError` in the pre-tar re-check, leaves only the generic STOP 9 orphan reason. Fix: keep the earlier reason (`ORPHANS_BEFORE_TAR + "; recorded before: " + prior`).
> **m2 — `orphan_run_cgroups`.** A sibling unit that ends between the `app.slice` listing and `scandir(sibling)` gives `FileNotFoundError` → `None` → false refusal (reproduced). Fails closed before any attempt dir. Fix: treat a vanished sibling as clean, as `_subtree_pids` does.
> **m3 — refusal and orphan STOP text.** Tells the operator to kill processes in `ar_*` children but gives only a count. Fix: name the sibling unit (`run-r….scope`, no seed) or say to inspect `app.slice/*/ar_*` before killing anything.
>
> ## Nit
> **n1 — `orphan_run_cgroups`.** An explicit check that the path lies under `user@<uid>.service` would make the bound self-evident.
>
> ## Cleanup
> Scratch in `/tmp/g5furev/_to_delete/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

## Round 3 (`15877e87`)

> Reviewed base: 15877e87 (one commit on 54bafc4a)
>
> ## Summary
> Accepted. All three round-2 minors and the nit are fixed correctly, the tests pass, and nothing new blocks. One optional nit remains, about how tight the unit-name pattern is.
>
> ## What I ran
> Fresh detached worktree at `15877e87`. test_t1_g5_job 37 passed; test_t1_g5_seal 32; test_t1_g5_tasl 109; test_t1_features 18 passed, 1 skipped (no lightgbm); test_t1_tasl_g4 30; test_t1_tasl_g1b 45; test_t1_tasl_crosscheck 30. Harness cross-check (`52e3c0b0` via `git archive`, `AR_G5_PAPER_ROOT` at the worktree): 63 passed, 0 skipped. Direct probes of `user_manager_scope` and `SAFE_UNIT`. Shared checkouts clean.
>
> ## The points asked about
> **Leaks into `_refusals/` or clear files: none.** `ar_*` names never reach a message; the refusal is built from sibling unit names and a count. A unit name appears only on a full match of `run-[ru][0-9a-f]{1,64}\.scope`, else `<other unit>` (probe: `train-7007.scope`, `run-rABC.scope`, `run-r1.scope/x` rejected); the test checks no `7006`, `7007`, `7008` or `ar_u00`. "Recorded before" appends the job's own earlier `record["stop"]`, already clear; the engines' stop text is never in it. The operator rule is fixed text.
>
> **Exact uid match: yes.** `user_manager_scope` requires `f"user@{os.getuid()}.service"` to equal one whole component of `Path(cgroup_parent).parts[:-1]`. Probed as uid 0: `…/user@0.service/app.slice/run-r1.scope` accepted; `user@00.service`, `xuser@0.service`, `user@0.service.d` and the manager cgroup itself rejected. Outside the manager the scan returns `None` and the job refuses.
>
> **Fixture change: no assertion lost.** The kill-before-tar, untarred-`out/` orphan STOP with operator rule and verifying SHA256SUMS, next-job refusal until cleared, failing kill helper, and unreadable-scope assertions are all present and pass. The unreadable-sibling assertion was rebuilt on a correct layout (it would otherwise return `None` for the wrong reason); stronger.
>
> ## The fixes
> m1 fixed (`…; recorded before: STOP 2` in job_record and diagnostics, class node; nothing appended without a prior stop). m2 fixed (vanished sibling skipped, vanished `ar_*` child empty, other OSError fails closed; tested). m3 fixed (systemd-form names only, count, inspect before killing). n1 fixed.
>
> ## Remaining nit (optional)
> `SAFE_UNIT` accepts 1–64 hex after `run-r` and hex after `run-u` (`run-u7006.scope` accepted). Not a leak: a systemd counter is not seed-derived and only the user can name units. Optional tightening: `run-r[0-9a-f]{32}\.scope` and `run-u[0-9]+\.scope`.
>
> ## Cleanup
> Scratch in `/tmp/g5furev/_to_delete/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

---

Code-Commit: 15877e877
Verdict: ACCEPTED

Accepted at `54bafc4a`, confirmed at `15877e87`.
