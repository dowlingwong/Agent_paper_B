# Independent review — candidate B1 `_c` post-run marker-retirement / completion procedure

**Scope.** Pre-execution review of `docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md` (99 lines; blob SHA-256
`d7156887549c556b4bd526f56336de0738a92637e3f2a512f8371c539274238c`), repo
`https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, commit
`32be3f4e3c39fb2c9aa4d1dc86f2beeec43fed7a` (parent `b93aae1e28d83f48cb2db3ea6ed2a61772dfe4d4` = "Record the digits_mlp
host-move reviews (round 1 + R2 accepted)"; commit time 2026-11-13 00:10:19 +0100). Nothing was executed on the run.
Reviewer is independent of the author; no file under `/Users/wongdowling/Documents/agent_paper_B` was modified.
Read-only checks on TASL-7 only (ls/stat/sha256sum/git rev-parse/status/tmux ls/import probes with `-B`); the running
B1 scene was not touched.

**Governing text checked at run HEAD `4b312844962e1106db04d5a60bf996fad0e3e514`** (and, for Track S, at `b93aae1e`):
`proposals/B1_OPERATOR_MESSAGE_V3_20261107.md` "Normal completion"; `proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md`
§"Normal completion versus STOP" (lines 37–51); `proposals/B1_RESTART_HANDOFF_C_20261111.md` §2.4, §3, §4;
`proposals/B1_RESTART_HANDOFF_20261109.md` §3 (halves table); PLAN §10 row `R1-EXAM-B1-TRUNCATION-INVALID`;
`reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` §3 condition 1 (at `b93aae1e`).

## Check 1 — authority and exclusions: PASS

The unit states it is "Candidate for independent review; not an execution and not an authorization" (line 3) and cites
exactly the normal-completion authority (line 5–8): operator message v3 "Normal completion", O2 draft "Normal completion
versus STOP", handoff C §3/§4, and the PLAN row's rationale that the marker is a cooperative lock, renamed (not deleted),
receipts kept. That matches the PLAN row wording at the run HEAD. It excludes abnormal STOP (explicitly routed to the
STOP procedure, lines 27–30, 96–99), deletion, Track P restart, Track S start, B2/X.7/sweep 2, B1 retry and pin/code
changes (lines 22–23, 89–92). The scope note "no Track S start — that is the separate host-move plan" (line 22–23) is
consistent with `reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` §3 condition 1, which gates the move on this procedure
having been written, independently reviewed and executed.

## Check 2 — retirement command and marker identity: PASS (with minor robustness issues, findings 2–3)

- Tool at the run HEAD: `$CHECKOUT/r1/scripts/b1_o2_marker.py`, SHA-256
  `8beedc2a0394f6153eb141f0e0854974887d4c9153f27a9f1fa5cc52532fc599` (git blob at `4b312844`, printed file on TASL-7
  identical). `NAME = 'trackx_evidence.active'`; `retire` refuses non-Linux (lines 61–62), opens the marker `O_NOFOLLOW`,
  requires an owned one-link regular file, reads ≤ 4096 bytes, and requires `(st_dev, st_ino, sha256)` to equal the
  receipt (line 76) with a re-stat identity check (78–80); creates `_to_delete/` 0700 if absent, checks the archive is
  owned and on the same device, then `renameat2(..., RENAME_NOREPLACE)` to a unique
  `trackx_evidence.active.<uuid4hex>` (87–92) and prints `{"retired": name, **receipt}` (93, 114). No delete, no force.
- Live marker verified read-only on TASL-7: `/home/dowling/r1_locks/trackx_evidence.active`, dev `66306`, ino
  `56261618`, mode 600, 82 bytes, SHA-256
  `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, content
  `{"head": "4b312844962e1106db04d5a60bf996fad0e3e514", "run_id": "4b31_20261112_c"}`. Creation receipt
  `$RUN_DIR/marker-receipt.json` SHA-256 `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`, content
  identical to the §0/line 17–19 description (dev 66306, ino 56261618, marker SHA `f8c8624f…`, run_id
  `4b31_20261112_c`, head `4b312844…`). The procedure's `test ! -e "$HOME/r1_locks/trackx_evidence.active"` (line 57)
  uses the correct marker name.
- Naming: the new outputs `marker-retirement_after_run.json`/`.note` do not collide with the `_b`→`_c` files already in
  `$RUN_DIR` (`marker-retirement.json`: run_id `fffa_20261111_b`, head `fffa45a1…`, retired
  `trackx_evidence.active.326cfd6dae21466f88d903bd2dd1c404`; `marker-retirement.note`: source_receipt
  `/home/dowling/r1_b1_engineering/b1_handover_fffa_20261111_b/marker-receipt.json`, SHA-256
  `1cd979aedef534f611963e419a92c02fe385d81f8119d477d4389480459a4405`), which were not touched by this review and which
  the procedure leaves alone. The `.note` records the creation receipt by path and SHA-256 (lines 54–56).

## Check 3 — verifier and completion-usage commands: FAIL (major, finding 1)

- CLI shape is correct at the run HEAD: `r1/exam/analyze.py:334–346` has positional `phase ∈ {stage-a,b1,b2}` plus
  `--rule`, `--rule-sha256`, `--batch`, `--config`; with `--batch`+`--config` and no manifests it calls
  `b1_summary_verified` → `verify_batch` (b1_batch.py:35, 41, 68), which is read-only. `r1/exam/rules/x5_rule_v2.yaml`
  hashes to the stated `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad` at `4b312844` (also in the
  file's `.sha256` and in the run config). `r1/scripts/b1_completion_usage.py:224–237` has `--roots/--cap` and returns
  0 on PASS, 1 on cap-check FAIL, 2 on `ValueError/OSError/KeyError/JSONDecodeError`; the doc's exit-code reading (1 =
  expected FAIL in the new run, 2 reported, not a STOP) matches both the code and handoff C §3.
- **Defect:** both commands invoke bare `python3`. On TASL-7 `python3` is `/usr/bin/python3` (Python 3.10.12) in both
  non-login and login shells (`.bashrc`/`.profile` only add `~/.local/bin`; no venv activation). `import
  r1.exam.runtime` fails there with `ModuleNotFoundError: No module named 'strenum'` (chain: `b1_batch.verify_batch` →
  `r1.exam.runtime` → `r1.exam.campaign` → `autoresearch.memory.schemas`), so
  `python3 -B -m r1.exam.analyze b1 --batch … --config …` exits non-zero at verification time. The frozen venv used by
  the run, `/home/dowling/exam-x/work/venv/bin/python` (Python 3.13.4, `PY`/`PATH` in `$RUN_DIR/start.sh`), imports
  `r1.exam.analyze`, `r1.exam.b1_batch`, `r1.exam.runtime` and `r1.scripts.b1_candidate_halves` successfully. Because
  step 2 (irreversible retirement) precedes step 5, this bug produces a **false STOP after the marker is gone**.

## Check 4 — normal-completion detection: PASS

`$RUN_DIR/receipt.sh` writes `$RUN_DIR/b1.exit` with the runner's rc after it exits, so `b1.exit` = 0 plus
`batch_state.json` `status` = `COMPLETE` (set only on success, `r1/scripts/exam_runner.py:560`; `STOPPED` on exception,
563) plus the session gone is a sound normal-completion test; any nonzero rc, `STOPPED`, interrupt, or `b1.log` STOP
line is excluded and routed to the STOP procedure (lines 27–30). The runner releases the cooperative lease in
`ExamRunner.close()` after `stop_service()` and before process exit (`r1/exam/runtime.py:958–968`, fd acquired at 650),
so the "lease free after exit" precondition (line 32) is correct. Current live state is consistent with "still
running": no `b1.exit`; `batch_state.json` `status` `RUNNING`; tmux `b1_4b31_20261112_c` present; marker present; harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` clean; checkout `4b312844…` clean (`status --porcelain --untracked-files=all`
empty).

## Check 5 — watcher observation: PASS with wording caveats (finding 5)

`tmux` `trks_watch` is alive; `~/r1_tracks/logs/watch.log` has three lines, last
`2026-11-08T00:46:56Z priority marker seen (/home/dowling/r1_locks/trackx_evidence.active): pausing` — the paused state
the doc expects (line 35–36), though it predates the `_c` marker. The reviewed census script
(`docs/r1/reports/tasl7_census_20261107/watcher.txt`) touches `STOP` beside every `manifest.json` under `r1_tracks/out`
at pause time, logs `FORCED` only after 3600 s of surviving collectors, kills `trks_llm`, then waits for the marker to
disappear and logs `marker gone: resume by hand (delete STOP files, start servers, re-run launch scripts)`. So
retirement should produce exactly one new `marker gone…` line and **no** new STOP touches (the pause already happened);
the doc's "expected: the watcher may touch `STOP` beside its manifests" (line 63–64) is a harmless hedge. `FORCED`
is treated as STOP (line 63, 96), but a `FORCED`/`priority marker seen` line already in the log could be misread; the
check should be scoped to lines added after retirement. Pre-existing STOP files are preserved (lines 63–64, 96–99).

## Check 6 — completeness and safety: PASS (minor gaps, findings 2–4)

Evidence capture comes first and read-only (lines 42–47); post-state checks cover compute apps, lease, marker absence,
retirement files, `_to_delete`, batch tree and the 6835/`_b` scenes (65–66); the report/STATUS/fresh-review sequence is
present (86–89); STOP conditions are complete and fail-closed (94–99); no secret material is printed by any listed
command. "No Track S/P restoration by this unit" (90–92) is consistent with the author's 12 Nov host-move decision:
Track P stays paused as during B1/B2 and the TASL-2 scene is preserved, never resumed; Track S's move is gated on this
retirement by `TRACKS_DIGITS_HOSTMOVE_20261112.md` §3.1 ("marker … must be gone and its retirement documented"), which
this unit produces. No deletion of STOP files is performed anywhere.

## Findings

1. **MAJOR — §2 step 5, lines 73–81 (also line 80): the verifier/usage commands use the wrong interpreter.**
   Bare `python3` is `/usr/bin/python3` 3.10.12 on TASL-7 and cannot import the verifier (`ModuleNotFoundError:
   strenum`, via `b1_batch` → `runtime` → `campaign` → `autoresearch.memory.schemas`), while the run's frozen venv
   `/home/dowling/exam-x/work/venv/bin/python` (3.13.4) imports the whole chain. Since retirement (step 2) precedes the
   verifier, this deterministically yields a false "verifier failure" STOP with the marker already retired.
   **Minimal fix:** `PY=/home/dowling/exam-x/work/venv/bin/python`; run `"$PY" -B -m r1.exam.analyze …` and
   `"$PY" -B -m r1.scripts.b1_completion_usage …` (or export `PATH=/home/dowling/exam-x/work/venv/bin:$PATH` as
   `start.sh` does), and add a pre-retirement preflight `"$PY" -c 'import r1.exam.analyze, r1.exam.runtime'` to step 1
   so the interpreter is proven before any irreversible step.

2. **MINOR — §2 step 2, lines 48–60: the retirement block is not fail-fast and can leave a misleading empty
   record.** Only `set -C` is set: if `retire` fails, the shell has already created/truncated
   `marker-retirement_after_run.json`, still writes the `.note`, and relies on the final `test ! -e` to stop; run off-host
   (the helper refuses non-Linux) that test passes vacuously. **Minimal fix:** `set -eu`, capture the retire rc and gate
   on it (`rc=$?; [ "$rc" -eq 0 ] || { echo "STOP: retire rc=$rc"; exit 1; }`), write the JSON to a temporary name and
   rename into place only on success, and state that the block runs on TASL-7.

3. **MINOR — §0 lines 12–16: `$CHECKOUT` is used but never defined as a shell variable** (only `$RUN_DIR=` and
   `$BATCH=` are given). **Minimal fix:** add
   `CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper` as an
   export beside the other two, and say that steps 2–5 execute there, not on the Mac.

4. **MINOR — §2 step 6, lines 86–89: the report is under-specified relative to handoff C §3.** It gives no command for
   the required first-/second-half table (`python -m r1.scripts.b1_candidate_halves --work "$BATCH"`,
   `B1_RESTART_HANDOFF_20261109.md:40`; `b1_candidate_halves.py:120–122` takes `--work`), does not require
   `scripted_minus_random` from `batch_state.json`, does not name the branch for `docs/r1/reports/B1_C_RUN_20261112.md`,
   and does not require verifying the remote `mac-b1-20261107` commit (or forbidding a `main` push) after the STATUS
   entry. **Minimal fix:** add the exact halves command (same frozen interpreter), state the report is committed on
   `mac-b1-20261107` with the STATUS, and add "push `mac-b1-20261107` and verify the remote commit; never push `main`";
   also cite `TRACKS_DIGITS_HOSTMOVE_20261112.md` §3.1 as the reason no Track S/P restoration is due here.

5. **MINOR — §2 step 3, lines 61–64: watcher expectations are not scoped to the new transition.** STOP touches happen at
   pause, not at marker-gone, and the pause line already existed on 2026-11-08; requiring only "a documented
   marker-gone observation or the documented paused state" lets the stale line stand in, and "a `FORCED` line is a STOP"
   would fire on a historical line. **Minimal fix:** require a *new* `marker gone: resume by hand …
   (delete STOP files, …)` line (remembering that deletion is forbidden) within ~120 s; treat any *new* `priority marker
   seen` or `FORCED` line as STOP; state that no new STOP touches are expected and re-check the before/after STOP
   inventories.

6. **MINOR — §2 step 1, line 44: `flock -n ~/r1_locks/gpu0.lock` is not a runnable probe** (flock needs a command).
   **Minimal fix:** `flock -n "$HOME/r1_locks/gpu0.lock" true; echo "gpu0 lock free rc=$?"` (probe only; no write).

7. **MINOR (placement) — the unit is the tip of `trackS-ops-20261030`, not a B1 branch.** Its parent is the Track S
   host-move review record, while the record it instructs (report + STATUS) goes to `mac-b1-20261107`, which does not
   carry the procedure. Substantively acceptable — the doc is content-only, executable from the frozen run checkout,
   and the host-move condition 1 only requires a reviewed procedure — but it splits the B1 record and a B1-only
   checkout may not contain it. **Minimal fix (non-blocking):** also commit the accepted procedure (or its commit
   `32be3f4e3c39fb2c9aa4d1dc86f2beeec43fed7a` plus this verdict) on `mac-b1-20261107` with the B1 report, and cite that
   commit in the report.

## Residual notes

- The watcher's last line (`2026-11-08T00:46:56Z … pausing`) predates the `_c` marker; no new `priority marker seen`
  line exists for `_c`, which is consistent with the watcher still sitting in its marker-present wait loop from 8 Nov.
  Retirement should therefore add exactly one `marker gone` line and no STOP touches; that expectation is what step 3
  should assert (finding 5).
- `~/r1_locks/_to_delete/` currently holds two archives (`…c51a7c4388bf469f85155263fb4079f5`, mtime 7 Nov 16:46;
  `…326cfd6dae21466f88d903bd2dd1c404`, mtime 11 Nov 03:01); retirement adds a third, uniquely named, and touches nothing
  else in `~/r1_locks`.
- The batch tree is mid-run (4 candidate directories, 4 `b1_manifest.json` so far); this review did not run the
  verifier or the usage script against it, and no write of any kind was made on TASL-7. The checkout at `4b312844…`
  remained clean after the read-only import probes (`git status --porcelain --untracked-files=all` empty).
- The operator-message order is retire → restore → verifier/publish; this unit does retire → verify → report/publish and
  defers restoration with reasons. That is acceptable only on the record above (Track P paused through B2; Track S
  preserved and moved under its own reviewed plan), and the report should state it explicitly rather than leave the
  deviation implicit.

VERDICT: changes required
