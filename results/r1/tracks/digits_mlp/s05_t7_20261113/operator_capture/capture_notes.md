# Track S S0.5 resume (TASL-7) — operator capture notes

- **Governance item (record-vs-launch ordering nuance; flag for STOP-4 reviewer):** the S0.5 resume was
  started at 2026-11-14T10:43:33Z by a **parallel operator phase**. The independent review of resume unit
  **rev 5** and the fixed launcher `f823b86a…` was **accepted substantively before the launch**: R2 review
  `docs/r1/reviews/TRKS_S05_LAUNCHER_FIX_REVIEW_R2_20261114.md` is dated "2026-11-14, ~10:40Z" and reviewed
  tip `9b217c53` (unit rev5 cites `f823b86a…`, STOP no-op branch, K clarification; launcher guard fix one
  line) — VERDICT: accepted. But the **commit recording the reviews** landed at **10:44:25Z** (`92680170`),
  i.e. **after** the 10:43:33Z launch. Round-1 review
  `docs/r1/reviews/TRKS_S05_LAUNCHER_FIX_REVIEW_20261114.md` was "changes required" (unit still cited the
  broken launcher sha) and was superseded by R2. Review-file sha256: round1 `0f5cccc0…`, R2 `561c546a…`.
  So this is a **record-vs-launch ordering nuance, not an ungated start**; it must be disclosed in the S0.5
  report/STATUS and flagged for the STOP-4 reviewer, and no second start/restart may be made.
- **Deferred tooling fix:** TASL-7 installed `bin/trks-status` still has `PAPER_SHA=d10b05b7…` (repo/pin
  `8237fd02…`). Approved at GO as a one-line operator-tooling fix, but **deferred to the first safe point
  after the collector exits** (Lead disposition (c)); not applied mid-run.
- **Launch rc history note:** `$R/logs/s05_t7_launch.rc` = `rc=2, rc=2, rc=0`, and the 10:43:33Z launch did
  **not** append a new rc line (the new launcher was invoked outside the wrapper that writes it). Recorded.
- **First failed resume attempt (13:03Z pause; 10:35:27Z rename; rc=1):** the previous launcher revision
  `3e957464…` aborted rc=1 before starting any server/collector because its `LIVE=$(pgrep … | wc -l)` guard
  tripped `set -euo pipefail` with zero servers; the pause STOP had already been renamed into
  `$RUN/_to_delete/STOP.retired.20261114T103527Z` (0 B, inode 57048847, sha e3b0c442…; exactly one retired
  file; rev5 no-op rule applies).
- **`.cmd` must stay** sha `fe9fae36311875470f6682539479ec2496e8be9bfe7bd56c5a32837dbd84054b`.
- **Operator actions:** read-only monitoring only while the run is active; never write on the host during the
  run; no stop/kill/restart of the run while active (process neither the Lead nor the operator started).

## UPDATE 2026-11-14T13:01Z — S0.5 collector exit + S0.5b ALREADY EXECUTED by a parallel phase

- **S0.5 collector exited normally:** `trks_s05_t7.exit` = `2026-11-13T13:03:00Z rc=0` (session #1 pause)
  then `2026-11-14T12:34:03Z rc=0` (session #2 resume). Manifest session #2 end `20261114T123402Z`,
  `done = {roots 28, forks 18, leaves 71, failed 0, exhausted 0, deadline_hit false, status complete}`;
  session #1 paused (22/6/0/0/0) retained. Two sessions total.
- **§1.7 + S0.5b were ALREADY executed by a parallel phase at 13:00:38–54Z** (before/around the Lead's
  13:00:30Z message): `trks_llm` stopped (lease FREE, no llama-server/listener, GPU idle 0 %/243 MiB,
  only `trks_watch`), and `tasl7_digits_s05b_20261113.sh` ran in `trks_s05b_t7` + outer `trks_s05bt7launch`:
  started `13:00:39Z`, collector `rc=0` `13:00:53Z`, launcher "S0.5b DONE" `13:00:54Z`; `s05b_t7_launch.rc`
  = `rc=0`; `trks_s05b_t7.log` reports `{"out": …, "truncated_audits": 200}`.
- **Final outputs:** `roots.jsonl` 50 lines, `forks.jsonl` 24, `leaves.jsonl` 71, `audit_runs.jsonl` 1780,
  `s05_calibration.jsonl` 298 lines (sha `2e4c9a8c…`), `s05b_truncated.jsonl` 200 lines (sha `cd296fd8…`),
  `manifest.json` sha `68a0d6e0…`; no `failed_units.jsonl`; no STOP. `.cmd` unchanged `fe9fae36…`.
- **Resume-launch wrappers (new evidence):** `s05_t7_resume_launch.rc` = `rc=1` (the failed first attempt)
  and `s05_t7_resume_launch2.rc` = `rc=0` + `s05_t7_resume_launch2.stdout` (the successful 10:43:33Z resume).
  This explains the earlier "launch rc not appended to `s05_t7_launch.rc`" note: the parallel phase used its
  own wrapper files.
- **Deferred `bin/trks-status` PAPER_SHA fix: still NOT applied** (`d10b05b7…`); safe point reached but held
  pending the Lead's go-ahead (per "report before acting" on the state divergence).
- **Origin tip still `92680170`; no §2 commits from the parallel phase** (copy-back/report/STATUS not yet done
  by anyone as of 13:01Z). Worktree clean at `92680170`.
