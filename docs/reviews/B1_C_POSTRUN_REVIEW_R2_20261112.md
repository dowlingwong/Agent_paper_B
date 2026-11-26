# Independent re-review — B1 `_c` post-run marker-retirement / completion procedure (rev 2)

**Scope.** Second-round, pre-execution review of
`docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md` (123 lines; file SHA-256
`338c7eed3571c3143a850a2bdbd4bb8855fd1ea132118feaed653595c67290e8`; git blob
`dffe23268707e931454d87891889264dbf4cc9f7`) in repo
`https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, commit
`341f02b77325f6d0912dd88c72a5edd099bb8c1d` (parent `32be3f4e3c39fb2c9aa4d1dc86f2beeec43fed7a`; author and
committer Dowling Wong, 2026-11-13 00:18:40 +0100; subject "B1: fix the _c post-run procedure (review round 1)").
The commit changes only that proposal (`git diff --stat 32be3f4e 341f02b7`: 1 file, 84 insertions, 60 deletions).
The branch is also the TASL-7 bare-repo tip
`/home/dowling/r1_tracks/remotes/Agent_paper_B.git refs/heads/trackS-ops-20261030` = `341f02b7…`.
Reviewer is independent of the author; no file under `/Users/wongdowling/Documents/agent_paper_B` was modified.
TASL-7 checks were read-only (`ls`/`stat`/`cat`/`sha256sum`/`git rev-parse`/`git status`/`tmux`/`flock` probe/`ps`/
`pgrep`/`nvidia-smi`/`wc`/`tail`); the procedure was **not** executed and the running B1 scene was not touched.

## Current run state (read-only, TASL-7 2026-11-12 15:19–15:24 PST)

- `$BATCH=/home/dowling/exam-x/work/b1_4b31_20261112_c`: `batch_state.json` `status=RUNNING`, `phase=b1`,
  `execution_label=EVIDENCE`, `interruptions=[]`; `$RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c`
  has a 0-byte `b1.log`, no `b1.exit`, no `*_after_run.*` file; tmux `b1_4b31_20261112_c` present;
  `pgrep` shows `r1.scripts.exam_runner b1`, one `llama-server` (pid 3843862), no `r1.tracks.collect`;
  `nvidia-smi` shows that server; `flock -n "$HOME/r1_locks/gpu0.lock" true` returns held (LEASE-HELD).
  The procedure is therefore correctly not executable yet; its precondition 1 fails.
- `$RUN_DIR` `_b`→`_c` transition files are present (`marker-retirement.json`, `marker-retirement.note`,
  `marker-receipt.json`, `status-receipt.md`, and the launch/precheck files) and no `*_after_run.*` name exists.
- Checkout `$CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper`
  is at `4b312844962e1106db04d5a60bf996fad0e3e514` and clean (`git status --porcelain --untracked-files=all` empty);
  harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` clean.

## Round-1 finding status

1. **MAJOR 1 — interpreter/preflight: FIXED.** `$PY=/home/dowling/exam-x/work/venv/bin/python` (Python 3.13.4) is
   now used for both verifier and completion usage (`:95`, `:101`); the import preflight is precondition 5
   (`:46–50`) and step 2 (`:61`), **before** retirement (`:62–78`). Verified on TASL-7, from `$CHECKOUT` with
   `AR_HARNESS_ROOT=$HARNESS`: `$PY -B -c 'import r1.exam.runtime, r1.exam.analyze,
   r1.scripts.b1_completion_usage; print("IMPORT_OK")'` prints `IMPORT_OK`, rc 0; the same command with bare
   `python3` (3.10.12) exits 1 with `ModuleNotFoundError: No module named 'strenum'` via
   `autoresearch.memory.schemas`/`StrEnum`. `$PY` also imports `r1.exam.b1_batch`, `r1.scripts.exam_runner`,
   `r1.scripts.b1_candidate_halves`, `r1.scripts.b1_o2_marker` (rc 0).
2. **MAJOR/minor retire block: PARTIAL.** `set -euo pipefail` (`:64`), a nominal rc gate (`:69–70`), a non-empty
   check (`:71`), the `TASL-7` statement (`:77`), and the `test ! -e` marker check (`:75`) are present. But under
   `set -e` the `rc=$?` at `:69` is **unreachable on failure**: the shell exits at `:66–68`, after the redirect has
   already created/truncated the final `marker-retirement_after_run.json`, leaving a zero-length receipt, no
   `.rc` file, no `.note`, and no `STOP: retire failed` message. The round-1 "misleading empty record" is therefore
   only superficially fixed; the temp-name/rename-on-success part of the round-1 minimal fix is absent. See finding 1.
3. **Watcher scoping: PARTIAL.** New lines are scoped (`:79–84`), `FORCED` is checked only on new lines (`:80`),
   `priority marker seen` must name `trackx_evidence.active` (`:80–81`), marker-gone vs already-paused handling is
   present (`:81–83`), STOP touches are expected only beside manifests (`:83–84`), and pre-existing STOP files are
   preserved (`:28`, `:84`, `:122`). But the required "line count before the retire" is not captured by any earlier
   step: step 1 only `tail -5`s the log (`:60`), so after step 3 the pre-retire count is unavailable. See finding 2.
4. **Report extras: FIXED.** The complete-batch verifier and completion-usage commands and exit-code reading are
   present (`:88–106`): verifier non-zero rc/invalid JSON = STOP; usage exit 1 = expected cap FAIL, not STOP; exit 2
   = reported. The report step requires `scripted_minus_random` from `batch_state.json` (`:108`), the
   `b1_candidate_halves --work "$BATCH"` table (`:109–110`), the report branch `mac-b1-20261107` with push/remote-tip
   verification (`:107–113`), the order deviation (`:30–33`, `:111`), and fresh independent review before publishing
   manifests/verifier (`:113`). `scripted_minus_random` is actually at `batch_state.json` →
   `anchor_gate.scripted_minus_random` (not top level); the report wording should name that path. Note also that
   usage exit 2 is "reported" while §3 says any inconsistency is a STOP (`:120–123`); the operator should record
   exit 2 as an inconsistency, not as a clean result.
5. **Placement: ADEQUATELY RECORDED for the executed record; residual.** Step 7 places the report on
   `mac-b1-20261107` and requires remote-tip verification (`:107–113`); the current remote tip is
   `57b8d2d532cf0e5249d46929d46e591993ba4235` (no `B1_C_RUN_20261112.md` yet). The procedure commit `341f02b7` remains
   only on `trackS-ops-20261030` (not on `mac-b1-20261107`, and `refs/heads/mac-b1-20261107` is not in the TASL-7
   bare repo). The report should cite `341f02b7…` (and this review) so the executed record on `mac-b1` is traceable;
   copying the procedure to `mac-b1` with the report is the round-1 non-blocking suggestion, still not done.

## Findings requiring changes

1. **MINOR — §2 step 3, `:64–71`: the rc gate is dead and a failed retire still leaves an empty final receipt.**
   `set -euo pipefail` is set at `:64`; if `python3 "$CHECKOUT/r1/scripts/b1_o2_marker.py" retire ...` (`:66–68`)
   returns non-zero, bash exits immediately, so `rc=$?` (`:69`), the gate (`:70`), the non-empty check (`:71`), the
   `.note` (`:72–74`) and the marker-absence test (`:75`) never run; the `> "$RUN_DIR/marker-retirement_after_run.json"`
   has already truncated/created that file to zero bytes. The marker itself is not retired on a validation failure
   (the helper checks dev/ino/sha before `renameat2`), so this is not a destructive failure, but the evidence file is
   misleading and the `.rc` the procedure promises is absent.
   **Minimal fix:** run the helper under an explicit status test, e.g.
   `if "$PY" -B r1/scripts/b1_o2_marker.py retire ... > "$RUN_DIR/marker-retirement_after_run.json.tmp"; then rc=0;
   else rc=$?; fi; printf '%s\n' "$rc" > "$RUN_DIR/marker-retirement_after_run.rc";
   [ "$rc" -eq 0 ] || { echo "STOP: retire failed rc=$rc"; exit 1; };
   [ -s "$RUN_DIR/marker-retirement_after_run.json.tmp" ] || { echo "STOP: empty retirement receipt"; exit 1; };
   mv "$RUN_DIR/marker-retirement_after_run.json.tmp" "$RUN_DIR/marker-retirement_after_run.json";`
   (or `set +e` around the single command); do not create the final receipt name on failure.
2. **MINOR — §2 step 4, `:79` vs step 3: the pre-retirement `watch.log` line count is never taken before the
   retirement.** Step 4 says "Record the line count of `watch.log` before the retire and read only lines after it",
   but step 4 executes after step 3, and step 1 only captures `tail -5 "$HOME/r1_tracks/logs/watch.log"` (`:60`), not
   the count or the last line. After retirement the operator cannot reliably distinguish new lines from the
   pre-existing paused line (currently 3 lines; last
   `2026-11-08T00:46:56Z priority marker seen (/home/dowling/r1_locks/trackx_evidence.active): pausing`).
   **Minimal fix:** in step 1 add `wc -l "$HOME/r1_tracks/logs/watch.log"` and `tail -1 …`, record the number as
   `WATCH_N`, and in step 4 read `tail -n +$((WATCH_N+1))` (after re-reading only after the 90–120 s wait).
3. **MINOR — §2 step 3, `:66`: bare `python3` contradicts the §0 binding (`:21–22`, "never use it here").** The
   helper is stdlib-only and does run under `/usr/bin/python3` 3.10.12 (verified with `--help`, rc 0), so this is not
   a functional failure today; but the procedure's own rule is to use the frozen venv, and a future helper import of
   a local module would fail. **Minimal fix:** use `"$PY" -B r1/scripts/b1_o2_marker.py retire ...`.
4. **MINOR — §2 step 6, `:89–103`: the verifier/usage block assumes exported variables that §0 only lists.** The block
   uses `$CHECKOUT`, `$PY`, `$BATCH`, `$RUN_DIR` after `set -uo pipefail` (`:90`) without defining/exporting them;
   §0 (`:17–22`) is a bullet list, not a shell preamble. A fresh `ssh tasl7 'bash -s'` with `set -u` aborts on an
   unbound variable, which would be a post-retirement false STOP. **Minimal fix:** add a short export preamble
   (`CHECKOUT=...; HARNESS=...; RUN_DIR=...; BATCH=...; PY=...; export ...`) to each block, or make the block
   self-contained with the literal paths.
5. **MINOR — §2 step 5, `:85–86`: "both `marker-retirement_after_run.*` files" but success writes three.** The
   retirement writes `.json`, `.rc`, and `.note` (`:68–74`). The post-state check should name/require all three (or
   say "receipt, rc and note"), so a missing `.rc`/`.note` is caught. **Minimal fix:** wording/check update.

## Checks performed

| Check | Result |
|---|---|
| Unit identity / commit / parent / diff scope (only proposal) | PASS — `341f02b7…`, parent `32be3f4e…`, 1 file |
| `$PY` import preflight (runtime, analyze, completion_usage) | PASS — `IMPORT_OK`, rc 0 |
| Bare `python3` import | PASS as designed — fails `ModuleNotFoundError: strenum`, rc 1 |
| Verifier/usage interpreter uses `$PY` | PASS — `:95`, `:101` |
| Preflight precedes retirement | PASS — precondition 5 / step 2 before step 3 |
| Retire block `set -euo pipefail`, rc gate, non-empty check | PARTIAL — lines present; rc gate dead (finding 1) |
| `$CHECKOUT`/`$PY`/`$HARNESS`/`$RUN_DIR`/`$BATCH` defined | PASS in §0; not exported into step 6 (finding 4) |
| Host TASL-7 stated | PASS — `:16`, `:53`, `:77` |
| Flock probe concrete | PASS — `flock -n "$HOME/r1_locks/gpu0.lock" true` (`:42`, `:58`) |
| Watcher new-line scoping / `FORCED` / marker-gone / STOP handling | PASS in text; pre-retire count missing (finding 2) |
| Report extras (verifier/usage semantics, halves, branch, remote tip, deviation, fresh review) | PASS — `:88–113`; `scripted_minus_random` path note |
| Placement on `mac-b1-20261107` recorded | PASS for the report; procedure commit not on `mac-b1` (note) |
| CLI matches run HEAD: `r1.exam.analyze b1 --batch --config --rule --rule-sha256` | PASS — parser at `4b312844`: `phase`/`--batch`/`--config`/`--rule`/`--rule-sha256`; `b1_summary_verified` |
| `r1.scripts.b1_completion_usage --roots --cap` | PASS — parser and exit 0/1/2 semantics match |
| `r1.scripts.b1_candidate_halves --work` | PASS — parser and read-only docstring match |
| Rule SHA at `4b312844` | PASS — `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`, also `.sha256` |
| Helper `b1_o2_marker.py` retire semantics | PASS — Linux `renameat2(RENAME_NOREPLACE)`, `O_NOFOLLOW`, owned one-link file, dev/ino/sha receipt match, `_to_delete/`, no delete |
| Live marker/receipt identity | PASS — marker dev `66306`, ino `56261618`, 82 bytes, SHA-256 `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`; receipt SHA-256 `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`, content run_id `4b31_20261112_c`, head `4b312844…` |
| `_b` transition files / new `*_after_run.*` names | PASS — `marker-retirement.json` and `.note` present; no `_after_run.*`; no collision |
| Run still running / procedure not executed | PASS — RUNNING, no `b1.exit`, tmux present, lease held, marker present |
| Scope/exclusions/STOP conditions | PASS — no deletion/restoration/B2/X.7/sweep 2/retry/pin changes; STOP conditions cover the main failures |
| Diff scope | PASS — only `docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md` |

## Residual notes

- `$RUN_DIR/marker-receipt.json` currently has the exact round-1/§0 identity; the helper's `retire` will check it
  against the live marker. The `_to_delete/` archive currently has two prior files
  (`trackx_evidence.active.326cfd6dae21466f88d903bd2dd1c404`, `…c51a7c4388bf469f85155263fb4079f5`); retirement adds
  a third unique name.
- `$RUN_DIR/b1.exit` is written by `receipt.sh` only after `start.sh` exits; normal completion is `0` plus
  `batch_state.json status=COMPLETE`. The current run has neither; do not apply the unit until both exist and the
  tmux session is gone.
- The watcher `/home/dowling/r1_tracks/bin/trks-watch` logs `marker gone: resume by hand (delete STOP files, start
  servers, re-run launch scripts)` after the marker disappears, touches `STOP` beside every `r1_tracks/out/**/manifest.json`
  at pause time, and logs `FORCED` only after 3600 s of surviving collectors. Since the pause happened on 8 Nov, the
  expected retirement result is exactly one new `marker gone` line and no new STOP touches; the procedure should
  record that expectation explicitly (finding 2).
- The report step's `scripted_minus_random` value is `batch_state.json` → `anchor_gate.scripted_minus_random`, not a
  top-level key; name the exact path in the report to avoid an empty lookup.
- `b1_completion_usage` exit 2 is an inconsistent/incomplete input condition; the procedure says "reported" while
  §3 says "any inconsistency" is a STOP. The task-required semantics are exit 1 = expected, exit 2 = reported; the
  report should state the exit 2 finding and treat it as an inconsistency for the fresh review, without pretending
  the run was clean.
- The proposal commit `341f02b7…` is not on `mac-b1-20261107`; cite it in the report (and optionally copy the
  procedure there) so the executed record is self-contained. This was a non-blocking round-1 placement suggestion.

## Verdict rationale

No safety-critical hole of the round-1 kind remains: the frozen interpreter is now used, the import preflight is
before the irreversible retirement, the host and flock probe are concrete, and the verifier/usage/report sequence is
present. However, round-1 finding 2 is only partially fixed (dead rc gate, empty final receipt on failure, no
temp/rename) and the watcher observation is not actually scoped to new lines because the pre-retire count is never
taken before step 3. Those are small but direct correctness defects in the evidence trail; fix findings 1–2 (and the
easy 3–5 wording/self-containment items) before executing the unit after normal completion.

VERDICT: changes required
