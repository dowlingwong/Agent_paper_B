# Independent review — Track S TASL-7 `digits_mlp` S0.1 re-run unit (13 November 2026)

**Reviewer.** Fresh, independent; I did not write the unit, the record or the script. Read-only on TASL-7
(`ls`/`stat`/`cat`/`sha256sum`/`find`/`tmux ls`/`pgrep`/`nvidia-smi`/`flock -n`/`/proc/locks`); no process, script,
marker or file on TASL-7 was started, signalled or written. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified; only this file and `/tmp` were written. The
`S01_SUFFIX=b` exercise was a local `/tmp` harness with the script's `R` redirected and stubs for
`tmux`/`git`/`curl`/`trks-run`, **not** a TASL-7 run.

## Unit

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`; commits
  **`c9a79b77`** (parent `1aae6c3d`) and **`fe4e99ad`** (parent `c9a79b77`); `origin/trackS-ops-20261030` and the
  TASL-7 bare `refs/heads/trackS-ops-20261030` both resolve to **`fe4e99add1210acff3baf3951fc9c743992a83cd`**.
- Exact digests at `fe4e99ad`:

```
c1deee130d8d67b495c4dcf2ad2b46b37153a6ae33224754e7b0e4f1be99c0f8  r1/tracks/ops/launch/tasl7_digits_s01_20261113.sh
ba85a28d82e98314f0a61ffe72f0f06f964e655e1ca8c8b56f7da91b8b913be5  docs/r1/reports/TRACKS_S01_TASL7_STOP_20261113.md
2a4c37925826742002385b8e9a95dcd230d268ebde221bc23761f842e569efe9  docs/r1/proposals/B1_C_STOP_MARKER_RETIREMENT_20261113.md
2ab4d55be2bbce07e8a72e7a9606e68e6ab0e4bb1c589d756d4e3db419e90c03  docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md
7ed20fcabccd67c2b935c2e7821fe98ed8f73345a221e0080f6c5c7ab2620e53  docs/r1/proposals/PLAN_ROW_R1-TRACKS-DIGITS-HOSTMOVE_REV_20261113.md
30b10908b15891430af265aa9671bdc95520fbf014cd1809ebdb73a36a54ae2f  docs/r1/STATUS.md
```

- Script blob `4943fa59…`, mode `100755`; `git diff 1aae6c3d c9a79b77` is only the two comment lines plus
  `S01=s01_t7_20261113${S01_SUFFIX:-}`.

## Checks

1. **S0.1 record accuracy — PASS on the substance; one minor accuracy defect (F2).** The record's 10:50:12Z start,
   10:51:25Z operator stop (73 s), two-line launch log, serial PID 4123514, no `serial.json`, no today-dated
   `rc=` line and empty `$OUT/digits_mlp/s01_t7_20261113/` are all confirmed by the launch log, the
   `trks-s01-t7-stop-20261113T105057Z/capture.log`, the 10:51:25Z stop capture and the live host. The old
   `trks_s01_serial.log` is 822 B, 3 lines, **mtime/ctime 2026-10-31 04:20:50.961 -0700**, and `.exit` ends
   `2026-10-31T11:20:51Z rc=0`; the 0.87/600 lines are the Oct-30/31 `tabular_mlp` log, not a 13 Nov
   `digits_mlp` result. The record makes no TASL-7 determinism claim and does not call this an identity-gate
   failure; the retirement/STOP-scene statements match the live host and the accepted capture.
2. **Revised script — PASS.** `sha256` matches `c1deee13…`; `bash -n` passes; the diff against the parent is
   exactly the `S01_SUFFIX` line + comment; the default is still `s01_t7_20261113`; the refuse-if-existing-dir,
   priority-marker, session-collision, pin `8237fd02`/clean, `trks_llm` k=2, 900 s readiness, probe arguments and
   rc guards are unchanged. Local sandbox: default with the preserved dir present → `REFUSE ... already exists`,
   rc 2; `S01_SUFFIX=b` → `s01_t7_20261113b`, serial/concurrent JSON written there, and the preserved
   `s01_t7_20261113/` inode/mtime/content unchanged.
3. **R3 corrections — FAIL (one explicit checklist item absent: F1).** §2.1 defines
   `CAPTURE=/private/tmp/b1-c-stop-retirement-capture-<UTC>`, a complete `$RUN_DIR` direct-file baseline
   (`-maxdepth 1 -type f`; live 19 = 15 pre-existing + the four `*_stop.*`; no subdirectories), a `$BATCH`
   baseline excluding `_to_delete` (stated), and the staging HEAD/clean check; §2.4 compares both baselines and
   makes any difference outside the four `*_stop.*` files, or in `$BATCH`, a STOP. The retirement-doc header is
   "reviewed (a4e01d2) and executed 2026-11-13T10:49:31Z (rev 4)". The STOP capture cite now says
   `on mac-b1-20261107 @ 3b7d570` (full `3b7d5704d0b489be977d26b0a7d8e462853ae455`). Host-move condition 1 says
   "must be accepted and executed", condition 6 says "STOP-case marker retirement", §5 is retitled and the
   operator note points at the revised PLAN row. **But the host-move header still says "not yet executed"
   (F1).**
4. **Contradictions/leftovers — one leftover (F3).** `post-run` survives only in normal-end/historical contexts
   (host-move line 41, the superseded-row note line 87, STATUS 12 Nov line 24), which is appropriate.
   `identity_rate 0.87` appears only in the correction contexts. `paste-ready` appears in the host-move operator
   note (correct, revised row) and in the 12 Nov STATUS bullet about the **rev-2** row (leftover, F3).
5. **Live read-only facts — PASS.** Marker `~/r1_locks/trackx_evidence.active` absent;
   `_to_delete/trackx_evidence.active.040ffbe17da643a28264bbf90ccd88fe` present (82 B); only `trks_watch`;
   `gpu0.lock` 0 B and `flock -n` free; `$OUT/digits_mlp/s01_t7_20261113/` empty; no
   `llama-server`/`determinism`/`exam_runner` process and no GPU compute app; paper checkout detached at
   `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`, clean; harness `a3fedbb`; prior
   `$OUT/digits_mlp/a2u_prior_r2_20261111.json` sha `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`.
6. **Re-run readiness — PASS for the script.** `S01_SUFFIX=b bash $R/launch/tasl7_digits_s01_20261113.sh` is
   safe for the preserved scene; the preserved empty directory is not deleted or modified. Acceptance (and the
   re-run) should wait for the F1/F2/F3 doc fixes, which need no host change.

## Findings

1. **minor — the host-move header still says "not yet executed".**
   `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:3` reads
   `**Author decision recorded here; not yet executed.**`; there is no "partly executed" sentence anywhere in
   the file (`grep -n partly` → no match), although R3 finding 10 asked for one and `fe4e99ad`'s message claims a
   "partly-executed note". The `1aae6c3d..fe4e99ad` diff only changes the title rev 3→4, condition 1's
   "reviewed"→"accepted", condition 6, the §5 heading and the operator note. **Minimal fix:** replace line 3 with
   a dated header sentence: the STOP-case retirement was executed 2026-11-13T10:49:31Z; the S0.1 probe started
   10:50:12Z and was operator-stopped 10:51:25Z with no result; S0.1/S0.5 remain unexecuted.
2. **minor — the ~395 s estimate is attributed to the "first repeat".**
   `docs/r1/reports/TRACKS_S01_TASL7_STOP_20261113.md:14` says "73 s into a run whose first repeat needs ~395 s
   at the measured ~0.658 s/call". The serial probe is 600 calls (200 prompts × 3 repeats, interleaved;
   `latency.n = 600`); 600 × 0.658 ≈ 395 s is the whole probe, while the first 200-call pass is ≈132 s and 73 s
   ≈ 111 calls. The "no result" conclusion is unaffected. **Minimal fix:** "73 s into a 600-call serial probe that
   needs ≈395 s at the measured ≈0.658 s/call".
3. **minor — a second "paste-ready" reference points at the superseded row.**
   `docs/r1/STATUS.md:23` (12 Nov entry) still calls the host-move rev-2 report's PLAN §10 row "paste-ready";
   host-move §4 now marks that row "Superseded draft — do not use", and the only current paste-ready row is
   `proposals/PLAN_ROW_R1-TRACKS-DIGITS-HOSTMOVE_REV_20261113.md`. **Minimal fix:** point the 12 Nov bullet at
   the revised row (or drop "paste-ready" there).

## Residual notes

- The PLAN row still cites host-move "rev 3" (lines 4–5 and the row's "remaining conditions ... (rev 3)"), while
  the report is rev 4; the row's condition-1 content ("accepted and executed") is consistent. R3 finding 11's
  pointer update is only half done.
- The retirement cite gives branch/commit but not `reports/B1_STOP_4B31_20261112.md` /
  `reviews/B1_STOP_4B31_REVIEW_R3_20261112.md` (R3 finding 3 asked for both); the branch/commit resolves it.
- §2.4 still lacks R3 finding 8's three read-only checks (retired name in `_to_delete` with sha `f8c8624f…`,
  re-hash the creation receipt `e0da112f…` against the note, bind helper/test bytes `8beedc2a…`/`fbeee6de…`).
- R3 finding 7's absolute "without touching ... at all"/"byte-equal" wording remains; it is true of the seven
  captured scene files, while four `*_stop.*` additions exist in `$RUN_DIR`.
- The executed capture `/private/tmp/b1-c-stop-retirement-capture-20261113T104913Z/` has
  `precheck.log`/`precheck.exit`/`retire.log`/`retire.exit` but no `run-dir-baseline.sha256`,
  `batch-baseline.sha256` or `SHA256SUMS`; the corrected §2.1/§2.4 baseline comparison is prospective, while the
  executed verification is the seven scene hashes plus `after_run_or_stop_extra: 0`.
- §2.1's `CAPTURE` is Mac-local (`/private/tmp`) while its `find` paths are TASL-7; `/private/tmp` does not exist
  on TASL-7 (verified), so the doc should state that the `find` runs on TASL-7 with output redirected into the
  Mac-local capture (the existing capture was produced that way).
- The re-run with `S01_SUFFIX=b` still appends to the shared `$R/logs/trks_s01_serial.log`/`.exit` (old Oct-31
  lines stay at the top; `trks_s01_serial.cmd` is replaced); the b-dir `serial.json`/`concurrent.json` are the
  authoritative results. Do not read the old lines as the re-run's.
- The record's "`identity_rate 0.87` and `errors: 600`" groups the 0.87/errors-0 line with the two
  errors-600/identity-0.0 lines; the correction's point (all three are Oct-31 `tabular_mlp`) is right, but
  "the three Oct-31 lines" would be exact.

VERDICT: changes required
