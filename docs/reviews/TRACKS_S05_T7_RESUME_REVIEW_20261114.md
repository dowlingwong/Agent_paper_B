# Independent review — Track S `digits_mlp` S0.5 resume unit (TASL-7), 14 November 2026

**Reviewer.** Fresh and independent; I did not write the unit, the reviewed launch scripts, the pause records or the
context reports. I read a `/tmp` clone of the repository only. The TASL hosts are unreachable in the author's VPN
window and I was instructed not to attempt access, so **no host access was made and nothing was executed**; every
host-side check below is an execution precondition, not a fact this review verified. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified; only `/tmp` and this file were written.

## Unit reviewed

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, tip
  **`2c60b300f10b5243155534448b4f8bd660ca5a55`** ("Prepare (review candidates) the B1 `_d` post-run unit and the
  Track S S0.5 resume unit", parent `d8ac944c980f597b87ab845ac5c1467fc56283e2`). `git diff --stat` of the commit is
  the two proposals only (+143 lines, 0 deletions; the branch tip, the local clone and the log all agree on the SHA).
- New file `docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md`, 59 lines, sha256
  **`33211682c2d7f4fd17cfec3ad4706211c81a0a8e961d49248ec65cd5c0ad46d7`**.
- Bytes it relies on, re-hashed in the clone: S0.5 `r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh`
  `3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151`; S0.5b
  `tasl7_digits_s05b_20261113.sh` `3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a`; empty file
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; prior
  `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`; paper pin
  `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`; harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`; GGUF
  `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`; llama.cpp
  `620d2225cc436ab0b001e3200e590e3b286ef9ab`; Track S runbook rev 3.3
  `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`. The k = 2 decision is the accepted
  `reports/TRACKS_S01_TASL7_RESULT_20261113.md` + `reviews/TRKS_S01_RESULT_AND_S05_K2_REVIEW_20261113.md`.
- Context used: host-move rev 4 (`reports/TRACKS_DIGITS_HOSTMOVE_20261112.md`), the accepted k=2 unit and its
  review, runbook rev 3.3 Phase 4/§0.4/§0.6/§10, the reviewed S0.1 result, the candidate `_d` post-run unit
  (`proposals/B1_D_POSTRUN_RETIREMENT_20261113.md`), and the paused-scene record supplied for the review (S0.5
  started 2026-11-13T12:25:51Z, paused 13:03:00Z by STOP; `done` roots 22 / forks 6 / leaves 0 / failed 0 /
  exhausted 0 / `deadline_hit` false, status `paused`; STOP 0 B, inode 57048847; launcher-session prefix
  workaround `trks_s05t7launch`).

## Verdict summary

| check | result |
|---|---|
| unit identity, hashes, commit/branch, non-executing status | PASS |
| authority and preconditions (B1 `_d` normal end + retirement, quiescent host, lease, markers, scene, pin, prior, k=2, deployed bytes) | PASS (with F1, F4, F5) |
| no-deletion rule for the STOP | PASS on intent and commands (rename, `-n`, mode 700, no `rm`/`unlink`/truncation) — with F6 |
| resume correctness (identical command, resume path, session/prefix, server start, collector session) | **FAIL** (F2, F3) |
| completion path (monitor, servers, S0.5b, copy-back, report/review, pause, STOP table) | PASS with F7–F9 |
| internal consistency / runtime after B1 | **FAIL** (F1, F5) |

## Findings

1. **Major — §0.2 (line 15): the paused-scene check names the wrong artifacts and omits `$WORK`.**
   `root_trials` is not a `$RUN` file: the S0.5/S0.5b leaf phase reads
   `$WORK/s05_t7_20261113/roots/<root_id>/root_trials.jsonl` (`r1/tracks/collect.py:1666`; the same path is
   required by S0.5b), and `b1_proposals` is a B1 run artifact (`proposals/B1_D_POSTRUN_RETIREMENT_20261113.md`
   §2.6), never produced by a Track S run. `$WORK` is not checked anywhere, although a missing or damaged
   `$WORK/{snapshots,roots/<id>/root_trials.jsonl}` makes the resumed leaves fail (retried, then exhausted,
   possibly across the 2 % gate). "unchanged since the pause" also has no baseline to compare against.
   *Minimal fix:* require `$RUN/{roots,forks,leaves,failed_units,audit_runs}.jsonl` (those that exist) plus
   `manifest.json` and `STOP`, and `$WORK/{snapshots,roots/<id>/root_trials.jsonl}` for every committed root;
   assert 22 distinct `root_id` in `roots.jsonl` and 6 distinct `fork_id` in `forks.jsonl` (the `done` counts are
   per session, runbook §0.6), no truncated last line, and no file under `$RUN`/`$WORK` newer than the pause time
   (13:03:00Z) or equal to a recorded pause capture.

2. **Major — §1.1/§1.4 (lines 27–29, 42–43): the "command byte-identical" check cannot be executed as written.**
   `trks-run` writes the command to `$R/logs/trks_s05_t7.cmd` (`r1/tracks/ops/trks-run:9`) and **overwrites** that
   file at every start (`:15`). Once the resume launcher runs, the paused run's `.cmd` is gone; step 1 captures
   `.exit` and the launch-log history but not `.cmd`. The unit's central "any difference from the reviewed bytes =
   STOP" check therefore has nothing to compare against.
   *Minimal fix:* in step 1, copy `$R/logs/trks_s05_t7.cmd` (and `sha256sum`) into the pre-resume capture; in step 4,
   after the launcher starts, compare the regenerated `logs/trks_s05_t7.cmd` byte-for-byte with that copy (mismatch
   = STOP), and keep both in the review bundle.

3. **Major — §1.3 (lines 33–35) with §1.4: servers are started before the reviewed launcher runs its guards.**
   The launcher's own pre-collector guards (priority markers, `$SESSION` collision, non-empty manifest, paper pin
   and clean tree, prior sha256, GPU/lease) are executed only in step 4. If any fails the launcher exits 2 while the
   servers started in step 3 keep both `llama-server` processes and `gpu0.lock`, i.e. the fail-closed STOP leaves an
   orphan GPU job holding the lease, blocking B1/B2 and contradicting "preserve and report".
   *Minimal fix:* delete step 3 and let the reviewed launcher start the servers itself (its `else` branch does the
   marker/GPU/lease checks, runs `trks-servers $K`, and waits up to 900 s on both `/v1/models`); or keep step 3 and
   add "on any non-zero launcher exit: `tmux kill-session -t trks_llm`, re-check `pgrep -f 'llama-server .*--port
   1810[12]'` and `flock -n gpu0.lock`, then STOP".

4. **Minor — §1.1 (line 29): `/private/tmp` is a macOS path; TASL-7 is Linux.** As written, `mkdir
   /private/tmp/...` on the host fails and the unit aborts before anything is resumed. *Fix:* use `/tmp/...` for the
   host capture, or state explicitly that the capture is written on the Mac and only the host output is streamed.

5. **Minor — §0.2 (line 14): the "or the same values with a later count if a short resume already ran" tolerance is
   inconsistent with the rest of the unit.** If a short resume had run, the pause STOP would already have been
   retired (so §1.2's `mv -n "$RUN/STOP"` fails and the scene is not in the assumed shape) and `sessions[-1]` would
   be that later session, not the pause. The scene record's STOP inode (57048847) is also not asserted.
   *Fix:* require the pause session and its values, assert the STOP's inode/size/sha (`57048847`, 0 B,
   `e3b0c442…`), and drop the parenthetical (no resume has run).

6. **Minor — §1.2 (lines 30–32): the post-rename state is not verified.** `mv -n` can exit 0 without moving
   anything, so "failure/leftover = STOP" needs an explicit test. *Fix:* record the source inode before, then
   require `[ ! -e "$RUN/STOP" ] && [ -f "$TARGET" ] && [ "$(stat -c %i "$TARGET")" = "$SRC_INODE" ]` and both
   sha256 = `e3b0c442…`, else STOP and preserve; record the target inode as well as the source inode.

7. **Minor — §3 (lines 56–59): STOP table incomplete/loose.** "exit 3 twice" should be "twice in a row"; the
   runbook's forced-pause exception (a watcher-killed server can produce an exit 3 that does not count) is not
   carried; missing: any other non-zero collector exit, the §10 5-day GPU cap (kept by host-move condition 7), and
   the Phase-4 λ check (the resumed manifest's `obs_inflation` must be 1.0, the prior's value — a difference is a
   STOP). *Fix:* add those four clauses.

8. **Minor — §1.6 (line 46): `status: deadline` is unaddressed.** An 8 h deadline hit is a normal, resumable
   outcome (runbook §0.6: "Restart a stopped or paused session with the identical command"), not a completion.
   *Fix:* state that rc=0 with `done.status=deadline` is resumed by the identical launcher (no scene change) or
   reported, and that rc=0 with any other status is a STOP. Also write `tmux kill-session -t trks_llm` instead of
   "kill `trks_llm`".

9. **Minor — §2 (lines 51–53): the copy-back omits the run logs and the `SHA256SUMS` step.** Without
   `$R/logs/trks_s05_t7.{cmd,exit,log}`, `s05_t7_20261113_launch.log` and the S0.5b log, the fresh review cannot
   verify the byte-identity of finding 2 or the rc history. *Fix:* include those logs in
   `results/r1/tracks/digits_mlp/s05_t7_20261113/` (host_logs/), generate `SHA256SUMS` there, and name the branch
   `trackS-ops-20261030` rather than "trackS-ops".

## Residual notes (not defects of this unit)

1. **Forks arithmetic worth a runtime glance.** With `--forks 1.5` and the S0.5 root pattern
   (primary + static rep 0 + static rep 1 for instances 0–9), 22 committed roots imply ≈8 primary roots and ≈12
   selected forks; the pause record says 6. The unit copies the record, so this is not a unit defect, but the
   runtime scene check should compare `manifest.json`, `roots.jsonl` and `forks.jsonl` and report a genuine
   shortfall rather than silently accepting it (a low fork count is a power issue, not a resume failure).
2. **TASL-2 return.** Host-move rev 4 condition 8 (read-only census, keep both scenes, no host switch) is not
   restated; add it to the monitor note so a returning TASL-2 during the resumed run cannot tempt a switch.
3. **Deviation from runbook §0.4 is intentional and should be recorded.** The runbook's resume step is
   `find $R/out -name STOP -delete`; this unit's rename into `$RUN/_to_delete/` is the author's no-deletion rule
   (as in the `_c` marker retirement) and is the stricter, correct behaviour. The report should say so explicitly
   so the deviation is auditable.
4. **Launcher-session quoting.** `K=2 bash …` inside `tmux new -d -s trks_s05t7resume "…"` must be one quoted
   string; the proposed name avoids the `trks_s05_t7` prefix (tmux `-t` prefix matching), which is correct.
5. Nothing else in the unit invites a `rm`/`unlink`/truncate/overwrite: the only mutation is the `mv -n` rename,
   mode-700 `_to_delete`, and the copy-back. No Track X/P, B2, X.7 or sweep-2 action, and no pin/code change.

VERDICT: changes required
