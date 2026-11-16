# Independent review, round 2 — Track S `digits_mlp` S0.5 resume unit (rev 2), 14 November 2026

**Reviewer.** Fresh and independent; I did not write the unit, the reviewed launchers, the pause record or the reports.
I read a `/tmp` clone only. The TASL hosts are unreachable in the author's VPN window and I was told not to attempt
access, so **no host access was made and nothing was executed**; every host-side check below is an execution
precondition. Nothing under `/Users/wongdowling/Documents/agent_paper_B` was modified; only `/tmp` and this file were
written.

## Unit reviewed

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030` (confirmed containing the tip),
  tip **`d799201917ff9368aff5c0cfe0921fd0a46af1e4`** ("Track S S0.5 resume unit rev 2"), parent
  `491e12416622f2d84580995cf96c90ec3a922471`, round-1 commit `2c60b300f10b5243155534448b4f8bd660ca5a55`.
- `docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md`, blob `890bae84c6eb4308b72d78886483ee87fe7a547c`, 64 lines,
  6146 B, sha256 **`3e7d613439d9ecd758396f4133eecffe8c6bcbd33ac7b3305aa404e36d09d1c6`**. Rev 1 was blob
  `fa04f8c60ec821a7cacd719461771aae1308eaff`, sha256 `33211682c2d7f4fd17cfec3ad4706211c81a0a8e961d49248ec65cd5c0ad46d7`
  — the hash the round-1 review recorded, so this is the same artefact, revised.
- `git show --stat d799201` = **one file** (unit, +55/−50). The range `2c60b300..d799201` is two files because the
  sibling B1 `_d` post-run unit rev 2 landed in `491e1241`; no code, pin, STATUS or runbook byte changes, no secrets,
  non-executing.
- Bytes the unit relies on, re-hashed in the clone: `tasl7_digits_s05_20261113.sh` `3e957464…` (79 lines),
  `tasl7_digits_s05b_20261113.sh` `3685dfe6…`, `r1/tracks/ops/trks-run` `b53bc811…`, `r1/tracks/collect.py`
  `d09cf1f4…`.

## Round-1 findings

| # | finding | status |
|---|---|---|
| 1 | Major, scene check names wrong artifacts/omits `$WORK` | **fixed** (F2, F3 remain) |
| 2 | Major, `.cmd` capture unexecutable | **fixed** (F4 remains) |
| 3 | Major, servers started before launcher guards | **fixed** (F5 remains) |
| 4 | Minor, `/private/tmp` is macOS | **fixed** |
| 5 | Minor, "later count" tolerance, STOP inode | **fixed** (wording gone; inode/sha/size pinned) |
| 6 | Minor, post-`mv -n` verification | **fixed** (source absent/target present/same ino+sha) |
| 7 | Minor, STOP table | **fixed** (in-a-row, forced-pause exception, 5-day cap); λ implicit only — F6 |
| 8 | Minor, `status=deadline` | **fixed**; rc=0+`paused` still unhandled — F6 |
| 9 | Minor, copy-back logs/SHA256SUMS/branch | **regressed** by the new copy list — **F1** |

## Findings

1. **Major — §2 (line 53): the copy-back glob `$RUN/sp05*` matches nothing, so the deliverable step fails.** The S0.5
   artefacts are `$RUN/s05_calibration.jsonl` (`collect.py:1017`) and `$RUN/s05b_truncated.jsonl` (`:944`); no file in
   `$RUN` starts with `sp05`. Executed as written, `cp $RUN/sp05* …` is "No such file or directory" (or copies nothing
   under a swallowed error), and the two JSONL that S0.5/S0.5b exist to produce never reach
   `results/r1/tracks/digits_mlp/s05_t7_20261113/`. This is new in rev 2 (rev 1 said "copy `$RUN`") and is the step
   that runs after the whole multi-hour resume. The same list also **drops the ledgers** (`roots.jsonl`, `forks.jsonl`,
   `leaves.jsonl`, `failed_units.jsonl`, `audit_runs.jsonl`) that rev 1's "copy `$RUN`" carried and that an independent
   S0.5 review needs to map the calibration rows to roots/leaves. *Fix:* `cp "$RUN"/s05_calibration.jsonl
   "$RUN"/s05b_truncated.jsonl "$RUN"/manifest.json "$RUN"/*.jsonl` (or copy `$RUN` minus `_to_delete`), plus the logs
   and `SHA256SUMS`; assert each named file exists after the copy.
2. **Minor — §0.2 (lines 13–18): the scene check is right in substance but imprecise where it will be executed.**
   `sessions[-1].done` holds **counts** (`{"roots","forks","leaves","failed","exhausted","status"}`, `collect.py:1618`),
   not "root ids"/"fork ids"; snapshots live at `$WORK/roots/<id>/snapshots` (`:839`), not `$WORK/snapshots`; and the
   pause's own `done.status == "paused"` (and a single session) is never asserted, although that is the one field that
   distinguishes this scene from a deadline/complete one. A literal checker can therefore false-STOP on a missing
   `$WORK/snapshots`. *Fix:* say `sessions[-1].done = {roots:22, forks:6, leaves:0, failed:0, status:"paused"}`,
   `$WORK/roots/<id>/{root_trials.jsonl,snapshots}`, and `len(sessions)==1`.
3. **Minor — §1.4 (line 43): the `.cmd` tolerance is not implementable and weakens the check it was added to make.**
   `trks-run` writes `$R/logs/trks_s05_t7.cmd` as shebang + optional `export TRKS_PORT=` + `printf '%q '` of the fixed
   argument vector + the log redirect + the rc line (`trks-run:9-15`); there is **no timestamp and no session line**
   anywhere in it. The correct rule is byte-identical (`sha256` equality), which is also what the paused and resumed
   launcher invocations will produce (same port 18101, same hardcoded argv). As written, the "only a new `grks-run`
   timestamp/session line may differ" clause invites excusing a real difference. *Fix:* "the regenerated `.cmd` must be
   byte-identical (`sha256sum` equal); any difference = STOP" (also fixes the `grks-run` typo).
4. **Minor — §1.3 (lines 38–39): the collector session name is wrong.** The launcher hardcodes `SESSION=trks_s05_t7`
   (line 13) and starts the collector as `trks-run "$SESSION" …` (line 77), so the resumed collector session **is**
   `trks_s05_t7`, not "not prefixed by `trks_s05_t7`, e.g. `trks_s05t7resume`". The `trks_s05t7…` form is the name for
   the *outer* tmux session; if the operator gives that name to the collector's own session it cannot work, and if the
   outer session is instead named `trks_s05_t7resume` the launcher's prefix-matched `has-session -t trks_s05_t7`
   (line 20) refuses (exit 2, fail-closed). *Fix:* "the collector session is `trks_s05_t7`; run the launcher in an
   outer tmux session named without the `trks_s05_t7` prefix (e.g. `trks_s05t7launch`)."
5. **Minor — §0.5/§1.4: only exit 2 is treated as the cleanup trigger, but the launcher can leave `trks_llm` behind on
   exit 3 or 1.** Guards precede the server start (so the round-1 orphan case is genuinely gone), but the readiness
   timeout (`:68`), "trks_llm exited immediately" (`:56`) and a failed `trks-run` all exit non-zero after or around the
   server start; exit 3 in particular can leave a live `trks_llm` session, which then blocks S0.5b (`s05b:17` refuses)
   and any retry. §0.5 says "any launcher refusal" but §1.4 narrows it to "(exit 2)", and the STOP table says only
   "launcher refusal". *Fix:* "any non-zero launcher exit (2 or 3): if `trks_llm` exists, kill only it, verify no own
   `llama-server` and `gpu0.lock` free, then STOP and report" (the unit's own no-orphan intent applies to exit 3 too).
6. **Minor — §1.5/§1.6: the completion gate is complete/deadline only.** The collector returns rc 0 for both `paused`
   and `deadline` (`collect.py:2130`, statuses at `:1614`); step 6 fires only on `complete` and step 5 covers
   `deadline`, so a resumed run paused again by a newly appearing priority marker (rc 0, `status=paused`) falls between
   the two and the new `$RUN/STOP` is not routed back into §1.2/§2. *Fix:* "`complete` → §1.6; `deadline` → renewed
   decision; `paused` → re-pause, keep the new STOP, report; any other status → STOP."
7. **Minor — §0/§3: the Phase-4 λ check is still implicit.** `--obs-inflation 1.0` appears in the command (so §1.4's
   byte-identity check does cover it, and `obs_inflation` is a `MANIFEST_KEYS` member that makes `collect.py:2092`
   refuse a difference), but the unit never asks for the manifest's `obs_inflation` to equal 1.0, which round 1
   requested. *Fix:* add one clause to §0.2 — "manifest `obs_inflation` = 1.0 (the prior's value); a difference = STOP".

## Residual notes (not defects that must change the unit)

1. The `$RUN`/`$WORK` "mtime <= 2026-11-13T13:03:00Z" fallback baseline is tight: `manifest.json` is rewritten in the
   `finally` after `end_utc` is sampled (`collect.py:2117-2124`), so a second-boundary roll can show 13:03:01. Prefer
   the pause capture; treat a single boundary-second mismatch as a reportable anomaly, not evidence of a mutation.
2. Fork arithmetic worth one runtime glance (carried from round 1): 22 roots / 6 forks is accepted verbatim as the
   expected scene; the operator should print `roots.jsonl`/`forks.jsonl` counts rather than silently accept a shortfall.
3. The no-deletion rename is now recorded in the header as a deliberate deviation from runbook §0.4's `find -delete`;
   that is the correct, stricter choice and is auditable.
4. Nothing in the unit invites a `rm`/`unlink`/truncate: the only mutations are the `mv -n`, mode-700 `_to_delete`, and
   the copy-back. No B2/X.7/sweep-2 action, no pin/code change, no secret, no TASL-2 switch (census-only rule is now
   stated).

VERDICT: changes required
