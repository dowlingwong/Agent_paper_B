# Track S — `digits_mlp` S0.5 + S0.5b on TASL-7 (host move), 13–14 November 2026 — **STOP 4 submission (digits half)**

**Written 14 Nov 2026 by the Track S operator agent (DSH experiment-agent session, Lead: experiment agent);
AI-assisted. ENGINEERING_ONLY.** Not a result. This records the `digits_mlp` S0.5 pilot and S0.5b truncation
sweep on TASL-7 and is submitted for the fresh independent review. **STOP 4 waits for `tabular_mlp`**; Phase 4
is not "complete" until the tabular half and the S0.5 summary are done. No B2/X.7/sweep 2.

**Authority.** Track S operator runbook rev 3.3 (`13badb0`, sha256 `a93fb84b…`) Phase 4; the host-move record
`reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` (rev 4); the accepted TASL-7 S0.1 result (k=2,
`reports/TRACKS_S01_TASL7_RESULT_20261113.md`); the reviewed k=2 S0.5 unit; the author's no-deletion rule;
PLAN §10 `R1-TRACKS-A2U-STALE` (paper pin move); resume unit **rev 5**
`docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md` (81 lines, sha256 **`f9373cb532…`**, at tip `9b217c53`)
and its launcher-fix reviews `docs/r1/reviews/TRKS_S05_LAUNCHER_FIX_REVIEW_20261114.md` (round 1, **changes
required**) and `_R2_20261114.md` (**accepted**, dated ~10:40Z, sha256 `561c546a…`).

**Pins.** paper **`8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** (detached/clean), harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (clean), llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`
(`v0.7.0-dev` 11669), GGUF sha256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`,
prior `a2u_prior_r2_20261111.json` sha256 `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`,
**k = 2**; launchers `tasl7_digits_s05_20261113.sh` sha **`f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3`**
and `tasl7_digits_s05b_20261113.sh` sha `3685dfe6…` (repo==host, `bash -n` OK). The run manifest records
`paper_commit = 8237fd02…`, `harness_commit = a3fedbb…`, GGUF/build, `host=TASL-7`,
`gpu=GPU-ab72fb4a-…`, `paper_dirty=false`, `harness_dirty=false`, `obs_inflation=1.0`, `g=0.00066`, phase
`S0.5`, label `ENGINEERING_ONLY`.

## 1. Timeline and what this phase did

| Time (UTC) | Event |
|---|---|
| 2026-11-13T12:25:52Z–13:03:00Z | S0.5 first session (#1) on TASL-7, `status=paused` on a Track X priority marker; done `22 roots / 6 forks / 0 leaves / 0 failed / 0 exhausted`. `$RUN/STOP` created (inode **57048847**, 0 B, sha `e3b0c442…`). |
| 2026-11-14T10:35:27Z | **Failed first resume attempt**: the pre-fix launcher `3e957464…` aborted **rc=1 before starting any server or collector** (`LIVE=$(pgrep … | wc -l)` tripped `set -euo pipefail` with zero servers). The pause STOP had already been **renamed once** into `$RUN/_to_delete/STOP.retired.20261114T103527Z` (0 B, inode 57048847, sha `e3b0c442…`; no deletion); `s05_t7_resume_launch.rc = rc=1`. |
| 2026-11-14T10:43:28–10:43:35Z | Fixed launcher `f823b86a…` deployed (host sha verified); **S0.5 resume** launched by a parallel operator phase: fresh `k=2` servers (pids 666767/666768), collector `trks_s05_t7` pid 666901, endpoints ready 10:43:35Z; `.cmd` rewritten **byte-identically** (sha `fe9fae36…`); `s05_t7_resume_launch2.rc = rc=0`. |
| 2026-11-14T12:34:02–12:34:03Z | S0.5 session #2 ends **`status=complete`**, `done 28 roots / 18 forks / 71 leaves / 0 failed / 0 exhausted`, `deadline_hit=false`; `trks_s05_t7.exit` `12:34:03Z rc=0`. |
| 2026-11-14T13:00:38–13:00:54Z | **§1.7 + S0.5b executed by a parallel operator phase** (see §7): servers stopped (lease free), then `tasl7_digits_s05b_20261113.sh` ran in `trks_s05b_t7` / outer `trks_s05bt7launch`: `rc=0` at 13:00:53Z, "S0.5b DONE" 13:00:54Z, `s05b_t7_launch.rc = rc=0`. |
| 2026-11-14T13:01–13:02Z | **This phase**: verified the completed state read-only (13:01:25Z capture), applied the deferred `trks-status` tooling fix, and did the §2 copy-back/report/bookkeeping only. No duplicate run, no second start. |

## 2. Pause scene verified (rev5 no-op STOP branch)

- Manifest session #1 (the pause) intact: `done 22/6/0/0/0`, `status=paused`, `sessions==1` at pause
  (`len(manifest['sessions'])==1` before the resume).
- `$RUN/STOP` absent; exactly **one** `$RUN/_to_delete/STOP.retired.20261114T103527Z` exists with 0 B,
  inode **57048847**, sha **`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`** — the
  rev-5 **no-op rule** applies (skip the rename, record the verification, do not create a second one).
- **Pause-baseline mtime check** (876 files under `$RUN`/`$WORK`): exactly **one** file is newer than the
  pause `2026-11-13T13:03:00Z` — the `STOP` itself at **`2026-11-13T13:47:35.151Z`**, a **watcher re-touch**
  (explained by `watch.log`: `2026-11-13T13:47:35Z priority marker seen (…/trackx_evidence.active): pausing`);
  content/inode/sha unchanged, all other files within 0.5 s of the second-resolution pause. Recorded as an
  explained re-touch, **not** a scene change (Lead disposition).
- No truncated last lines in any JSONL (`$RUN` ledgers or the 22 `$WORK` root `root_trials.jsonl`).

## 3. Command identity

The resume rewrote `$R/logs/trks_s05_t7.cmd` at 10:43:35Z; its sha256 stayed
**`fe9fae36311875470f6682539479ec2496e8be9bfe7bd56c5a32837dbd84054b`** — **byte-identical** to the
pause-era command (rev5 §1.4). The command carries the prior + sha, `--obs-inflation 1.0`, `--W 40
--instances 20 --policy static:0.00198,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1`,
the ENGINEERING_ONLY label, the 8 h deadline, and the same `--out`/`--work` dirs.

## 4. S0.5 result (manifest `sessions=2`)

| session | start–end (UTC) | done (roots/forks/leaves/failed/exhausted) | status |
|---|---|---|---|
| #1 (13 Nov, paused) | 12:25:52–13:03:00 | 22 / 6 / 0 / 0 / 0 | `paused` |
| #2 (14 Nov, resume) | 10:43:35–12:34:02 | **28 / 18 / 71 / 0 / 0** | **`complete`** |

Totals in `$RUN`: `roots.jsonl` **50** lines (sha `039b6955…`), `forks.jsonl` **24** (`bf638fa6…`),
`leaves.jsonl` **71** (`427faff6…`), `audit_runs.jsonl` **1780** (`93939187…`),
`s05_calibration.jsonl` **298** rows (`2e4c9a8c…`, last line valid), `manifest.json` sha `68a0d6e0…`;
**no `failed_units.jsonl`**; **no STOP**; `exhausted = 0`. `.cmd` unchanged `fe9fae36…`.

## 5. S0.5b result

`tasl7_digits_s05b_20261113.sh` (CPU, no servers) ran 13:00:39→13:00:54Z: `trks_s05b_t7.exit`
`2026-11-14T13:00:53Z rc=0`, `s05b_t7_launch.rc = rc=0`, log
`{"out": "$RUN", "truncated_audits": 200}`; `s05b_truncated.jsonl` **200 rows** (sha `cd296fd8…`, last
line valid). Outputs `s05_calibration.jsonl` and `s05b_truncated.jsonl` both exist and are non-empty.

## 6. STOP checks

No `failed_units.jsonl`; `exhausted = 0`; `deadline_hit = false`; no STOP at `$RUN` (the pause STOP is the
single retired file, inode/sha unchanged); command identity holds; the successful resume produced no launcher
refusal (`s05_t7_resume_launch2.rc = rc=0`) and S0.5b produced none (`s05b_t7_launch.rc = rc=0`). The only
failed attempt is the **pre-fix** first resume (`rc=1`, before any server/collector — see §1/§7); it is not a
collector exit and was not retried on its own (the successful resume used the fixed launcher).

## 7. Governance disclosure — parallel-phase execution and review-record ordering (STOP-4 reviewer)

Recorded for the STOP-4 reviewer; it does not by itself invalidate the run, but it must be disclosed and not
repeated (no second start/restart was made).

- **S0.5 resume launch (10:43:33Z) was executed by a parallel operator phase**, ahead of the Lead's HOLD relay
  (Lead message 10:43:47Z), and the **§1.7 server stop + S0.5b were also executed by a parallel phase** at
  **13:00:38–54Z**, before/around the Lead's 13:00:30Z message. **This phase did not start or re-run anything**;
  it verified the completed state read-only (13:01:25Z capture) and did the §2 bookkeeping.
- **Review-record ordering:** the R2 review of resume unit rev 5 + launcher `f823b86a…` is dated
  **~10:40Z** and **accepted** (reviewed tip `9b217c53`), i.e. the gate was **substantively satisfied before**
  the 10:43:33Z launch; however the **commit recording the reviews** (`92680170`) landed at **10:44:25Z**,
  **after** the launch. This is a **record-vs-launch ordering nuance, not an ungated start**.
- **Precondition host state** at resume: all markers absent, no B1 process, lease free, only `trks_watch`;
  B1 `_d` close-out published on `origin/mac-b1-20261107` @ `d817eb73` (Lead).
- **Deferred tooling fix now applied** (safe point, no run active): TASL-7 `bin/trks-status` `PAPER_SHA`
  `d10b05b7… → 8237fd02…`; script sha **old `5bd570ff…` → new `70fbe8bd312fd7aad3a9020b80dcf9284453a8319dbb2cb523e9f6c06f16cc5f`**
  (= committed repo file); `trks-status` now prints `OK paper 8237fd02`, `OK harness a3fedbb`,
  `OK llama.cpp 620d2225`, GGUF OK, no STOP line. Tooling only — the launcher already enforced the pin
  (`git rev-parse == 8237fd02`, clean).
- **Historical `s05_t7_launch.rc` = `rc=2, rc=2, rc=0`** (pre-run setup refusals on 13 Nov); the resume used
  its own wrappers: `s05_t7_resume_launch.rc = rc=1` (failed first attempt) and `s05_t7_resume_launch2.rc =
  rc=0` (successful resume).

## 8. Host end state (TASL-7, verified 13:01–13:02Z)

Only `trks_watch`; lease **FREE**; no llama-server / compute app; no 18101/18102 listener; no collector
process; no priority/drill markers; GPU idle (0 %, 243 MiB); disk 526 G free (71 %). TASL-2 untouched; no
B2/X.7/sweep 2.

## 9. Evidence (copy-back) and hashes

`results/r1/tracks/digits_mlp/s05_t7_20261113/` — the run tree (`s05_calibration.jsonl`, `s05b_truncated.jsonl`,
`roots/forks/leaves/audit_runs.jsonl`, `manifest.json`, `_to_delete/STOP.retired.20261114T103527Z`),
`host_logs/` (collector `trks_s05_t7.log/.cmd/.exit`, `s05_t7_20261113_launch.log`, `s05_t7_launch.rc/.stdout`,
`s05_t7_resume_launch.rc/.stdout`, `s05_t7_resume_launch2.rc/.stdout`, `s05b_t7_20261113_launch.log`,
`trks_s05b_t7.log/.cmd/.exit`, `s05b_t7_launch.rc/.stdout`, `watch.log`) and `operator_capture/` (preflight,
monitor and anomaly captures + `capture_notes.md`). **`SHA256SUMS` verifies 40/40 locally** (run-tree ledgers, `_to_delete/STOP.retired…`, `host_logs/`, `operator_capture/`
including its nested `SHA256SUMS`, and the two launcher scripts); the run-tree/log files were copied read-only from
TASL-7 and byte-match their recorded hashes. `failed_units.jsonl` absent (recorded). Never the TASL-2 scene.


**Record provenance and host-down gap.** This report merges the parallel-phase result record with the
operator/governance record; the operator capture evidence is under
`results/r1/tracks/digits_mlp/s05_t7_20261113/operator_capture/` (`capture_notes.md`, preflight/monitor/anomaly
captures). **The TASL-2 bare-repo push is deferred:** TASL-2 (`portal_zhixu`, 100.120.160.70) was **unreachable
(TCP timeout)** at 14:10Z, so the TASL-2 bare-repo copy of this record could not be pushed; it will be retried
when TASL-2 returns. Origin carries the record; TASL-2 was not touched.

## 9b. Descriptive numbers (calibration and truncation; added by the Lead phase)

- **Calibration** (`s05_calibration.jsonl`, 298 rows, level 0.8, k=5 audit seeds): overall coverage
  **231/298 = 0.7752**. Stratum detail (covered/total): `HIDDEN_UNITS +, stratum 0` **0/20**;
  `BATCH_SIZE +, stratum 1-2` 20/40; `HIDDEN_UNITS +, stratum 1-2` 31/40; `HIDDEN_UNITS +, stratum >=3` 75/75;
  `LEARNING_RATE_INIT -, stratum 0` 5/11. `delta_audit` mean **−0.0074** (min −0.4123, max 0.1922).
  Descriptive only; the aggregate gate is a Phase-4 decision with `tabular_mlp`, not inferred here.
- **Truncation** (`s05b_truncated.jsonl`, 200 rows): W in {8, 10, 12, 20}; `runs_used / trials` =
  8/8 (W8, 50/50 rows binding), 10/12 (W10, 50/50), 12/22 (W12, 47/50), 16/40 (W20, 2/50); mean `y_terminal`
  per W = 0.963097 / 0.968334 / 0.970830 / 0.972802. The cap binds at the **low** W values; at W20 most rows
  are non-binding (16/40 is the non-binding runs_used/trials count).

## 10. Scope / next

- This is the **digits_mlp half** of Phase 4; **STOP 4 waits for `tabular_mlp`** (and the Mac-side S0.5
  summary). No B2/X.7/sweep 2. TASL-2 is censused read-only only, not resumed or switched to.
- **Not self-accepted:** submitted for a fresh independent review; the governance disclosure (§7) and the
  deferred-fix record must be part of that review.

## 11. Reviewer checklist

1. Pins and manifest provenance (paper `8237fd02`, harness `a3fedbb`, GGUF/llama, dirty=false, TASL-7, k=2);
   launchers `f823b86a…`/`3685dfe6…` repo==host, `bash -n`; unit rev5 sha `f9373cb5…` + R2 review accepted.
2. Pause scene: manifest #1 `22/6/0/0/0 paused`, the single retired STOP (0 B, inode 57048847, sha
   `e3b0c442…`), the explained STOP mtime re-touch, no truncated JSONL.
3. Command identity: `.cmd` sha `fe9fae36…` (pause → resume byte-identical).
4. S0.5 session #2 `28/18/71/0/0 complete`, totals (roots 50, forks 24, leaves 71, audit_runs 1780,
   calibration 298), no failed_units, exhausted 0, deadline false.
5. S0.5b `rc=0`, `truncated_audits 200`, `s05b_truncated.jsonl` 200 rows, `s05_calibration.jsonl` 298 rows.
6. Governance disclosure (§7): parallel-phase resume/§1.7/S0.5b execution; R2 review dated ~10:40Z but
   record-commit 92680170 at 10:44:25Z (record-vs-launch ordering); this phase verified + bookkeeping only.
7. Deferred `trks-status` fix: old→new script sha, `OK paper 8237fd02`, tooling only.
8. Host end state; copy-back `SHA256SUMS` + host==copy; TASL-2 untouched; no B2/X.7/sweep 2.
