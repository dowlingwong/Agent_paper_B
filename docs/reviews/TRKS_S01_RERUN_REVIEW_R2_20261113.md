# Independent review — Track S S0.1 record/unit last documentation fixes (round 3), 13 November 2026

**Reviewer.** Fresh, independent; I did not write this unit, its record or its script. Read-only on TASL-7
(`date`, `tmux ls`, `tmux capture-pane -p`, `pgrep`, `nvidia-smi`, `flock -n`, `ls`/`stat`/`sha256sum`/`cat`,
`git rev-parse`); no process, session, marker or file on TASL-7 was started, signalled or written. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified; only this file and `/tmp` were written. Live-state
snapshot **2026-11-13T11:18:33Z**.

## Unit

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, commit
  **`b0f1c6cd4d53057bdd21d65519525dd3d92f9db7`** (parent **`fe4e99add1210acff3baf3951fc9c743992a83cd`**).
  `origin/trackS-ops-20261030`, the TASL-7 bare `refs/heads/trackS-ops-20261030`, and the fetched `/tmp` clone all
  resolve to `b0f1c6cd`; the parent is `fe4e99ad`. One commit; `git diff-tree --no-commit-id --name-only -r
  b0f1c6cd` lists only the five docs below (no code or script path in `git diff fe4e99ad b0f1c6cd`; stat
  +10/−7).
- Blob hashes at `b0f1c6cd`:

```
41a0be1e083bebd9641358d7c910a916151c6670  docs/r1/reports/TRACKS_S01_TASL7_STOP_20261113.md
04a5bad8b20d7992221c4ebf493e69630f48eb29  docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md
73084ef2a7ebcc5b1732945fb324c8914076311a  docs/r1/STATUS.md
51bf29e1f12de31c56f55166cfe8b77b0214f9a5  docs/r1/proposals/PLAN_ROW_R1-TRACKS-DIGITS-HOSTMOVE_REV_20261113.md
24078c9954e5e53796eba9fc033187e63cca645d  docs/r1/proposals/B1_C_STOP_MARKER_RETIREMENT_20261113.md
```

- Script at both `fe4e99ad` and `b0f1c6cd`:
  `c1deee130d8d67b495c4dcf2ad2b46b37153a6ae33224754e7b0e4f1be99c0f8` (blob `4943fa59…`, mode `100755`); the
  deployed TASL-7 `r1/tracks/launch/tasl7_digits_s01_20261113.sh` has the same sha256.
- The B1 STOP report/review cited by the procedure exist on `mac-b1-20261107 @ 3b7d570`: report
  `e935880183bcec2325fd418ae8e0aeef251a9f54fdd9aeb446ea7baf210b1f9c`, review R3
  `51a6ef71d5286e64bcdc9e64f72877582eef5be636d67297811570d1b6179c3f`.

## Checks

1. **Diff scope and the round-3 fixes — FAIL (one required item absent: F1).**
   - S0.1 record: **PASS** for the probe-duration correction (lines 13–15: "full 600-call probe needs ~395 s at
     the measured ~0.658 s/call (the first 200-call pass ≈132 s)"). **FAIL** for the shared-log vs authoritative
     suffixed-JSON note (F1).
   - Host-move header: **PASS**. Line 3 reads "**Author decision recorded here; partly executed (13 Nov: `_c`
     STOP-case marker retirement accepted and executed; S0.1 pending a reviewed operator-error re-run).**"
   - STATUS 12 Nov: **PASS**. Line 23 reads "(rev 4) with the revised PLAN §10 row draft
     (`proposals/PLAN_ROW_R1-TRACKS-DIGITS-HOSTMOVE_REV_20261113.md`)"; no "paste-ready" in that bullet.
   - PLAN row: **PASS**. Line 5 cites `reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` **rev 4**; line 9 says
     "remaining conditions ... (rev 4)".
   - Procedure: **PASS**. Lines 48–50 state the capture commands run on TASL-7 and output is streamed into the
     Mac-local capture dir; lines 34–36 cite `reports/B1_STOP_4B31_20261112.md` (accepted) and
     `reviews/B1_STOP_4B31_REVIEW_R3_20261112.md`, both present on `mac-b1-20261107 @ 3b7d570`.
2. **Stale/wrong wording — PASS for the listed items; residuals R1/R2.** No "not yet executed" in the host-move
   header (the two remaining occurrences are historical review quotes). No "paste-ready" referring to the
   superseded row: it survives only in the host-move operator note for the revised row (line 94) and in old
   reviews. `identity_rate 0.87` appears only in correction context (record lines 6 and 17; STATUS line 12 uses
   the quoted "identity 0.87" as the wrong earlier wording). The STATUS 12 Nov "Preconditions" bullet (line 24)
   still names the 12 Nov normal-end/post-run path (R1), and the prep report still carries the pre-`S01_SUFFIX`
   script digest (R2).
3. **No code/script change, pins/STATUS, secrets — PASS; R2.** The diff is docs only; deployed script
   `c1deee13…`; TASL-7 paper pin `8237fd02b09ef2d28016a1c9f6acac3c35bb768b` detached/clean, harness
   `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, prior `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`,
   GGUF `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`, llama.cpp
   `620d2225cc436ab0b001e3200e590e3b286ef9ab` all match. No secret-like strings in the diff.
4. **Read-only TASL-7 — PASS.** Re-run in progress at 11:18:33Z: `trks_s01_launch_b` + `trks_s01_serial`, `trks_llm`
   k=2 servers (pids 4129633/4129634, ports 18101/18102), gpu0 lease held (`flock -n` rc=1; holder 4129628), serial
   determinism pid 4130084 writing `…/s01_t7_20261113b/serial.json`. Old empty
   `out/digits_mlp/s01_t7_20261113/` untouched (empty; mtime 2026-11-13 02:50:12 -0800; inode 56915422). New
   `s01_t7_20261113b/` dir exists (still empty; probe running) and `logs/s01_t7_20261113b_launch.log` has the two
   11:13:01Z lines. Nothing was disturbed.

## Findings

1. **minor (required fix) — the S0.1 record does not note the re-run's shared-log append vs the authoritative
   suffixed JSON.** `docs/r1/reports/TRACKS_S01_TASL7_STOP_20261113.md` lines 26–28 say only that the existing
   `trks_s01_serial.log`/`.exit` are old Oct-31 append-only files not to be read as *that* run's evidence; lines
   40–43 name the new `s01_t7_20261113b` directory but never say that the re-run also appends to the shared
   `trks_s01_serial.log`/`.exit` (old lines stay at the top) and that the authoritative results are
   `out/digits_mlp/s01_t7_20261113b/serial.json` / `concurrent.json`. The commit message claims this note was
   added; the only record change in `fe4e99ad..b0f1c6cd` is the 3-line probe-duration sentence. This is the exact
   attribution hazard behind the original stop, and the current re-run is appending to those shared logs now.
   **Minimal fix:** add one sentence in §3 (or §2) naming both suffixed JSON paths as authoritative and stating
   that the shared log/exit are appended by the re-run.
2. **Residual R1 — the STATUS 12 Nov "Preconditions" bullet still names the normal-end/post-run path.**
   `docs/r1/STATUS.md:24` says "B1 `_c` normal end + a separately reviewed post-run marker retirement"; the actual
   `_c` ended in STOP and the STOP-case retirement was executed (STATUS 13 Nov; host-move rev 4 condition 1).
   Historical, and the 13 Nov entry above supersedes it, but a parenthetical pointer would avoid a reader taking
   the 12 Nov wording as current.
3. **Residual R2 — the prep report's S0.1 digest is stale.** `docs/r1/reports/TRACKS_TASL7_PREP_20261113.md:27`
   (and its review line 21) list `f86ce11e948186c195a687c88d39862dfde3d78695f8d9c2f9ea09658fd740f2` for
   `tasl7_digits_s01_20261113.sh`; the committed/deployed script is
   `c1deee130d8d67b495c4dcf2ad2b46b37153a6ae33224754e7b0e4f1be99c0f8`. The prep report says these are "the
   exact bytes that will run". Not introduced by this commit, but safety-affecting if an operator hashes against
   it; correct it when the S0.1 record is next revised.

## Residual notes

- Live re-run artifacts: `logs/s01b_launch.rc` currently contains `rc=2` (mtime 11:12:20Z), and the default
  `logs/s01_t7_20261113_launch.log` now has a third 11:12:20Z "S0.1 start" line. Both are the aborted unsuffixed
  attempt (the preserved `s01_t7_20261113/` exists, so the script refused with rc 2) one minute before the
  successful 11:13:01Z `S01_SUFFIX=b` launch; neither is the re-run's result. The re-run's authoritative output
  is the b-dir JSON, and its launch log is `s01_t7_20261113b_launch.log` (two lines so far).
- The record's "launch log has exactly two lines" / "(2 lines, today)" is true of the 10:50 run's segment; the
  live default log now has the third aborted-attempt line.
- The re-run still appends to the shared `trks_s01_serial.log`/`.exit`; `trks_s01_serial.cmd` is the new
  11:13:01Z b-dir command, while `serial.log`/`.exit` are still the Oct-31 files (mtime 2026-10-31 04:20:50.961
  -0700 / 04:20:51.279 -0700).
- The five changed docs' pin/status claims match the live host; the only unresolved required item is F1.

VERDICT: changes required
