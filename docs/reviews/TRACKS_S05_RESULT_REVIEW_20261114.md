# Independent review — Track S `digits_mlp` S0.5 result and copy-back (14 November 2026)

**Reviewer.** Fresh and independent; I did not write the report, the copy-back, the STATUS entry or the run. I read a
`/tmp` clone of the repo and TASL-7 **read-only** (`cat`, `stat`, `sha256sum`, `python3`, `tmux ls`, `pgrep`,
`nvidia-smi`, `flock -n`), and wrote only this file and `/tmp`. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified. One `flock` probe used a non-lease scratch path and created
a 0-byte `scratch/gpu0.lock`; I removed that file at once. The lease path `~/r1_locks/gpu0.lock` was only opened/probed;
no run, log, ledger or lease file was changed.

## Unit

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch **`trackS-ops-20261030`**, tip
  **`e008abfb35ca722c9498b15f0b944af58131533c`** ("Track S S0.5 pilot resumed and complete on TASL-7; copy back the
  results; L1 pause"), 16 files / +449.
- Report `docs/r1/reports/TRACKS_S05_T7_RESULT_20261114.md` sha256
  `70cadf035117286d59039e85fcdd98826fd2fefd3cf1a6a4c013dedc0f64cc00`; STATUS
  `2fbbe1aea7759d0867be3b0c89815c95d32854a89550f6d5d74329dd45a8cf4e`; copy-back `SHA256SUMS` blob
  `6bd9097daebb879cf50bbf1e9d9d62f6ce37a8f346d645a8c99c0498e8cffb34` (23 entries).
- Host scene `/home/dowling/r1_tracks/out/digits_mlp/s05_t7_20261113`; host clock 2026-11-14T13:02Z during review.

## Checks

### 1. Completion — PASS

- `logs/trks_s05_t7.exit` has two lines; the resume line is `2026-11-14T12:34:03Z rc=0`.
- `manifest.json` (sha `68a0d6e077891f22e0a2e40b5b589dd680a1efdd0be19f7f79f2ade18e6e187c`): `sessions` length 2;
  session 0 `paused` 22/6/0/0/0; session 1 `done` = 28 roots / 18 forks / 71 leaves / 0 failed / 0 exhausted,
  `deadline_hit=false`, `status=complete`.
- Ledgers: roots 50/50 `ok`, 0 `error`; forks 24, 5 `aa`; leaves 71/71 `ok`, 0 `error`; no `failed_units.jsonl`;
  deadline not hit. All 50/24/71 rows parse and the last line of each JSONL is complete.
- Servers stopped: only `trks_watch` in tmux; no `llama-server .*--port 1810[12]`; no GPU compute app;
  `~/r1_locks/gpu0.lock` is 0 B and `flock -n` reports free.
- S0.5b: `13:00:39Z` start, `.exit` `2026-11-14T13:00:53Z rc=0`, launcher `13:00:54Z`; it ran only after
  `S0.5 manifest complete` and with `trks_llm` absent/collectors clear (its own guards plus the launch log).

### 2. Copy-back — FAIL

The commit contains only **13 of the 23 files** named in `SHA256SUMS`. `sha256sum -c SHA256SUMS` in the checkout
returns 13 `OK` and 10 `No such file or directory`. Missing (with the sums line):

| SHA256SUMS line | path | pinned sha256 |
|---|---|---|
| 1 | `./_to_delete/STOP.retired.20261114T103527Z` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2 | `./audit_runs.jsonl` | `93939187ee1c681972ca0233a1d2c1fbf7508a3fe78bbaecc122f88eed85aed8` |
| 3 | `./forks.jsonl` | `bf638fa6718b6910565710459fe2caa326692d463f50c06c5cac8075cbab7267` |
| 4 | `./leaves.jsonl` | `427faff6a7d266dd58a312f53ef1cf4ea6421e1def19e6ffa38a080f664df3bc` |
| 5 | `./logs/s05_t7_20261113_launch.log` | `65a7c019e33cf30883029d91c535bd2f081ccedfe98f22d4c69467ae819ca42c` |
| 14 | `./logs/trks_s05_t7.log` | `9ebfce7c9d76f46a3f5c79e276c2b594000f8dfa700394f0437e3b0b67b290a4` |
| 17 | `./logs/trks_s05b_t7.log` | `d712ab20cc3778c9e8f774015b55c7ef293c686872de327f230a359576248165` |
| 19 | `./roots.jsonl` | `039b69556d6b4c14c93fdb52982ffe136d9ac7c3ee4e6714a7434b8750569da5` |
| 20 | `./s05_calibration.jsonl` | `2e4c9a8c40ef5fb9a740ad5b4ad12e2d7026c42fdc19b4467ddeefbaacc50a2b` |
| 21 | `./s05b_truncated.jsonl` | `cd296fd8f2029266015d536f0f561521e13da36f83d7f00c84a9439d4c1ce135` |

The bytes exist on the host and match these sums (roots 50, forks 24, leaves 71, audit_runs 1,780, calibration 298,
truncated 200 rows; collector log 1,617,214 B, S0.5b log 3,979 B, launch log 1,475 B). But they are not in the commit,
so the calibration/truncation/roots/forks/leaves hashes cannot be verified from the record and the report's §4 claim
(lines 33–39) and STATUS line 8 are false as committed. The cause is visible in `.gitignore`: line `*.jsonl`
(root/forks/leaves/audit/calibration/truncated), line `*.log` (the three logs) and line `_to_delete/` (the STOP);
the commit did not force-add them, so those paths were silently dropped. The two scripts and the small rc/stdout/cmd/
exit files do match: `f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3`,
`3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a`, `.cmd`
`fe9fae36311875470f6682539479ec2496e8be9bfe7bd56c5a32837dbd84054b` (786 B, byte-identical to the 10:35:08Z capture),
exit `02b5ae59b5c3edb9a6998a44bd59c44bf34174f42fe79f3c8be090a7bc45f3d0`.

### 3. Report numbers — PASS (one wording error, F3)

- Calibration: 298 rows; level 0.8 all; k 5 all; covered 231/298 = 0.775167785… = 0.7752. Strata reproduce exactly:
  `HIDDEN_UNITS + 0` 0/20, `BATCH_SIZE + 1-2` 20/40, `HIDDEN_UNITS + 1-2` 31/40, `HIDDEN_UNITS + >=3` 75/75,
  `LEARNING_RATE_INIT - 0` 5/11. `delta_audit` mean −0.007418, min −0.412256, max 0.192200.
- Truncation: 200 rows; 50 per W; W ∈ {8,10,12,20}; policies `a2u` and `static:0.00198,0`; reps 0/1; per-W
  `y_terminal` means 0.963097 / 0.968334 / 0.970830 / 0.972802. The quoted `runs_used/trials` 8/8, 10/12, 12/22, 16/40
  are the rep-0 cells (a2u and static; F3 on the interpretation).
- No deletion found; descriptive-only language; no gate claim (the report explicitly defers the aggregate gate to
  Phase 4 with `tabular_mlp`). No secret in the committed files; the 1.6 MB collector log would be acceptable
  uncompressed, but it is one of the missing files.

### 4. Run history — PASS on the mechanics; F2/F4 wording/disclosure

- First attempt: `s05_t7_resume_launch.rc` = `rc=1`, stdout 0 B, no launch-log entry, collector log/exit untouched
  since 13 Nov; nothing was started. STOP was renamed (not deleted) to
  `_to_delete/STOP.retired.20261114T103527Z`, 0 B, inode 57048847, sha `e3b0c442…`, mtime 2026-11-13 05:47:35 −0800.
- Second attempt: launch log `10:43:33Z`, endpoints 18101..18102 ready, collector started; `.cmd` is byte-identical to
  the 10:35:08Z capture (`cmp` clean, `fe9fae36…`). S0.5b started 26 min after the S0.5 exit, after manifest complete
  and with no servers; its own guards and the launch log agree.
- F2 (ordering disclosure) and F4 (pause-cause wording) below.

## Findings

**F1 — High — copy-back incomplete / report and STATUS overstate it.**
Location: `results/r1/tracks/digits_mlp/s05_t7_20261113/SHA256SUMS` lines 1–5, 14, 17, 19–21;
`docs/r1/reports/TRACKS_S05_T7_RESULT_20261114.md` lines 33–39; `docs/r1/STATUS.md` line 8.
Issue: 10 of the 23 pinned files are absent from `e008abfb`; `sha256sum -c SHA256SUMS` fails 10 entries. The report
says they were copied back and the STATUS says "with SHA256SUMS/logs/scripts and the retired STOP". `.gitignore`
(`*.jsonl`, `*.log`, `_to_delete/`) silently excluded them.
Minimal fix: force-add the ten files at the exact paths already in `SHA256SUMS` (top-level `roots.jsonl`, `forks.jsonl`,
`leaves.jsonl`, `audit_runs.jsonl`, `s05_calibration.jsonl`, `s05b_truncated.jsonl`; `logs/s05_t7_20261113_launch.log`,
`logs/trks_s05_t7.log`, `logs/trks_s05b_t7.log`; `_to_delete/STOP.retired.20261114T103527Z`), then require
`sha256sum -c SHA256SUMS` = 23/23 `OK`; amend `e008abfb` or add a follow-up commit on `trackS-ops-20261030`. Do not
commit the untracked `host_logs/`-layout tree as-is (see residual note) and do not alter the host scene.

**F2 — Medium — the record-vs-launch ordering nuance is not disclosed.**
Location: report §1 line 9 ("Resume under the reviewed rev-5 unit"); `docs/r1/STATUS.md` line 5.
Issue: the resume started `10:43:33Z`, but the commit recording the accepted R2 review (`92680170`) is dated
`2026-11-14T11:44:25+01:00` = `10:44:25Z`, 52 s after the launch; the R2 review itself is dated "~10:40Z". The
operator capture notes of 13:01Z say this nuance "must be disclosed in the S0.5 report/STATUS and flagged for the
STOP-4 reviewer". Neither does. The verdict did precede the launch, so this is not an ungated start, but it is an
omitted governance fact.
Minimal fix: add one sentence with the three times (R2 verdict ~10:40Z, launch 10:43:33Z, review-record commit
10:44:25Z) and explicitly flag it for STOP-4.

**F3 — Low — "cap binding is visible at the higher W" is backwards.**
Location: report §3 lines 29–31; `docs/r1/STATUS.md` line 7.
Issue: `binding=true` for 50/50 rows at W8, 50/50 at W10, 47/50 at W12, but only 2/50 at W20; the quoted 16/40 at W20
is a rep-0 row (a2u and static both show 16/40) with `runs_used` 16 < W 20, i.e. not cap-bound. Per-W single values
also hide the other rows (e.g. W8 static rep-1 is 8/9; W20 static rep-1 is 15/40).
Minimal fix: say that the cap binds at W8–W12 (`runs_used = W`), and at W20 the rep-0 cells used 16/40
(48/50 rows `binding=false`); name the slice or report the range.

**F4 — Low — pause cause/time conflicts with the retained watch log.**
Location: report §1 line 7 ("Pause: 2026-11-13T13:03:00Z (watch-triggered STOP on the B1 `_d` marker)").
Issue: `logs/watch.log` records the only 13 Nov pause event at `2026-11-13T13:47:35Z` ("priority marker seen …
pausing"), and the STOP file's mtime is 13:47:35Z (same inode 57048847), 44 min after the 13:03:00Z collector exit.
Either the 13:03 pause had a different trigger and the watch later touched that STOP, or the watch's STOP was created
only at 13:47:35Z after the collector had already stopped; in neither case does `watch.log` support a 13:03:00Z
watch-triggered STOP.
Minimal fix: record the actual 13:03 trigger with its evidence and the 13:47:35Z watch touch, or drop the cause.
The inode/sha of the STOP are correct.

## Residual notes (non-blocking)

1. `audit_runs.jsonl` has 1,780 unique rows; manifest session counts sum to 1,770 (700 + 1,070). The 10-row difference
   is consistent with S0.5b appending audits after session 1 was closed (only two sessions are recorded), but the
   record does not say so. A one-line note would remove the apparent mismatch.
2. During review a fuller copy-back tree was present untracked in
   `.claude-worktrees/trackS-ops-20261030/results/r1/tracks/digits_mlp/s05_t7_20261113/` (that worktree is still at
   `92680170`), with `host_logs/` and `operator_capture/`. It is not in `e008abfb` and its paths differ from the pinned
   `SHA256SUMS`; if used, remap the bytes to the pinned `logs/`/top-level paths (preferred) or regenerate the sums and
   update the report.
3. S0.5b `.exit` says 13:00:53Z while the launcher log says 13:00:54Z; a one-second read-after-exit difference, not a
   factual error in the result.
4. TASL-2 could not be resolved from this environment (no `tasl2` aliases), so "TASL-2 was not reachable / preserved"
   is consistent with the evidence here but the scene preservation itself was not re-censused.

## Concurrent local record (not the reviewed unit)

While this review ran, a second, **unpushed** commit appeared in
`.claude-worktrees/trackS-ops-20261030`: `e7417c5e9b11ba157f83e0f7a3bfe557358aa7a1` (2026-11-14T13:05:55Z, parent
`92680170`; origin is still `e008abfb`). It is not the unit and I did not switch to it, but it changes what the parent
should push, so it is recorded here:

- It has 41 changed files, including the full run tree, `_to_delete/STOP.retired.20261114T103527Z`, `host_logs/` (17)
  and `operator_capture/` (12); its 37-entry `SHA256SUMS` verifies **37/37 `OK`**.
- Its report is `docs/r1/reports/TRACKS_S05_T7_20261114.md` (146 lines, sha
  `ba8f4929ce5c8089847a8fafbe7090af0ea35d1601d4306311a22b3e1ec45549`), not `TRACKS_S05_T7_RESULT_20261114.md`; it
  explicitly discloses the parallel-phase / record-vs-launch ordering (§7) and the 13:47:35Z STOP re-touch (§2), so
  F2 and F4 are addressed there.
- It has **no `scripts/` directory** and **no calibration/truncation numeric summary** (no 0.7752 / 0.963097 /
  `delta_audit`); the reviewed launchers live only at `r1/tracks/ops/launch/`.
- The two records are therefore complementary, not interchangeable: `e008abfb` has the `scripts/` and the numeric
  summary but lacks 10 data/log files; `e7417c5e` has the data and the governance disclosure but lacks `scripts/` and
  the numeric summary. Pushing both would duplicate the report/STATUS entry. Recommended: rebase/cherry-pick
  `e7417c5e` onto `e008abfb` (or the reverse), keep one report/STATUS (rename the surviving report to
  `TRACKS_S05_T7_RESULT_20261114.md` to match the unit), add `scripts/` and the §2/§3 summary with F3
  corrected, then re-review the merged tip. The verdict below applies to `e008abfb` only.

## Conclusion

The completion facts, ledger totals, server/lease shutdown, calibration and truncation numbers, first-attempt abort,
STOP rename, `.cmd` identity and S0.5b ordering all reproduce. The record still does not support the L1 pause because
the copy-back is incomplete (F1: 10 of 23 files absent, `SHA256SUMS` fails, report/STATUS overstate it), and the
descriptive/governance statements need correction (F2–F4). After F1 is committed and `sha256sum -c` is clean (and the
wording fixes are made), the result would support the pause with S0.5 summary/STOP 4 deferred to `tabular_mlp`. If the
parent instead adopts the fuller `e7417c5e` record, merge it first (it is not on `e008abfb` and lacks `scripts/` and
the numeric summary); this verdict does not transfer to that commit without a fresh review.

VERDICT: changes required
