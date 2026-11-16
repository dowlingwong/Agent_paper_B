# Independent final review — B1 `_c` post-run marker-retirement / completion procedure (rev 3)

**Scope.** Third-round, pre-execution, final review of `docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`
(139 lines; file SHA-256 `0ad821635d1ecc3ede3e16d84e24c321a90d2e607d35ae69fdd4663633ab61d9`; git blob
`e6e0db71ed92bcb489b17af8d0abc07d758fe7c8`) in repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch
`trackS-ops-20261030`, commit `034be89dd909b9a15d6247be8ef13884245ae73c` (parent
`341f02b77325f6d0912dd88c72a5edd099bb8c1d`; author and committer Dowling Wong `<wangdowling@gmail.com>`,
2026-11-13 00:25:53 +0100; subject "B1: fix the _c post-run procedure (review round 2)"). The commit changes only
that proposal (`git diff --name-status 341f02b7 034be89d`: `M docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`;
`--stat` 1 file, 27 insertions, 11 deletions). Rev 2 (reviewed in round 2) is 123 lines, SHA-256
`338c7eed3571c3143a850a2bdbd4bb8855fd1ea132118feaed653595c67290e8`, blob `dffe2326`. The TASL-7 bare repo
`/home/dowling/r1_tracks/remotes/Agent_paper_B.git refs/heads/trackS-ops-20261030` also resolves to `034be89d…`.
The reviewer is independent of the author; no file under `/Users/wongdowling/Documents/agent_paper_B` was modified.
TASL-7 checks were read-only (`stat`/`sha256sum`/`cat`/`ls`/`find`/`git rev-parse`/`git status`/`sed`/`grep`/`tmux`/
`pgrep`/`flock`/`wc`/`tail`); the procedure was **not** executed, no write or signal was issued to the running B1
scene, and the shell block's control flow was exercised only in `/tmp` against stub helpers (no TASL-7 state used).

## Current run state (read-only, TASL-7 2026-11-12 23:27 UTC / 15:27 PST)

- `$BATCH=/home/dowling/exam-x/work/b1_4b31_20261112_c`: `batch_state.json` `status=RUNNING`, `phase=b1`,
  `interruptions=[]`, `completed` present for the trial-level roots only; `anchor_gate.scripted_minus_random` is
  present (`descriptive_only`, `scripted_minus_random_role` = `descriptive_only (R1-EXAM-B1-ANCHOR-R4; ordering STOP
  removed post hoc)`).
- `$RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c` (mode 0700, owner `dowling`): 0-byte
  `b1.log`, **no `b1.exit`**, **no `*_after_run.*`** (`find -maxdepth 1 -name '*_after_run*'` empty); `_b`→`_c`
  transition files present (`marker-receipt.json`, `marker-retirement.json` for `fffa_20261111_b`,
  `marker-retirement.note`, `status-receipt.md`, launch/precheck files).
- Live marker `/home/dowling/r1_locks/trackx_evidence.active`: dev `66306`, ino `56261618`, 82 bytes, mode 600,
  SHA-256 `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, content
  `{"head": "4b312844962e1106db04d5a60bf996fad0e3e514", "run_id": "4b31_20261112_c"}`.
  Receipt `$RUN_DIR/marker-receipt.json` SHA-256
  `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`, content dev/ino/sha/head/run_id matching the
  live marker. `_to_delete/` holds the two earlier retired names
  (`…326cfd6dae21466f88d903bd2dd1c404`, `…c51a7c4388bf469f85155263fb4079f5`); this retirement would add a third.
- tmux `b1_4b31_20261112_c` and `trks_watch` alive; `r1.scripts.exam_runner b1` pid 3736030; one `llama-server`
  pid 3843862; no `r1.tracks.collect`; `flock -n "$HOME/r1_locks/gpu0.lock" true` → `LEASE-HELD`;
  `watch.log` has 3 lines, last `2026-11-08T00:46:56Z priority marker seen
  (/home/dowling/r1_locks/trackx_evidence.active): pausing`.
- `$CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper` is at
  `4b312844962e1106db04d5a60bf996fad0e3e514`, `git status --porcelain --untracked-files=all` empty;
  `r1/exam/rules/x5_rule_v2.yaml` = `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad` (also in its
  `.sha256`).
- The unit is therefore **not executable now** (precondition 1 fails); nothing was retired.

## Round-2 finding status (all checked against `git diff 341f02b7 034be89d` and the run HEAD)

1. **MINOR 1 — retire block rc reachability / empty receipt / `.rc`+`.note` / `$PY`: FIXED.** Rev 3 lines 65–86
   replace the bare command with `if "$PY" … retire … > "$TMP" 2> "$TMP.err"; then rc=0; else rc=$?; fi` (71–76),
   write `marker-retirement_after_run.rc` (77), gate on `rc≠0 || ! -s "$TMP"` (78–80), and only then
   `mv "$TMP" …json` (81) plus the `.note` (82–84) and the marker-absence test (85). The helper runs with
   `/home/dowling/exam-x/work/venv/bin/python` (68/71), not bare `python3`. Exercised in `/tmp` with stubs:
   success → `.json` non-empty (78 B), `.rc`=`0`, `.note` written, block exit 0; helper exit 1 → `.rc`=`1`,
   no final `.json`, `.tmp` preserved, `STOP: retire failed rc=1…`, exit 1; exit 0 with no stdout → gate catches
   the empty `.tmp` (STOP, exit 1). The only `rm -f` is line 70 on `"$TMP"` = `$RUN_DIR/marker-retirement_after_run.json.tmp`
   (fixed absolute name, nothing else); `.tmp.err` is only truncated by the redirection. No unsafe deletion.
2. **MINOR 2 — pre-retire `watch.log` count/last line: FIXED.** Step 1 now prints
   `wc -l < "$HOME/r1_tracks/logs/watch.log"` and its last line, explicitly "recorded as the pre-retire line count
   for step 4" (60–61); step 4 (89–94) scopes to lines after it. Currently 3 lines / paused line as above.
3. **MINOR 3 — step 6 self-containment: FIXED.** Lines 102–105 define `CHECKOUT`, `RUN_DIR`, `BATCH`, `PY` inside
   the block before `set -u` use; `bash -n` passes on the extracted block.
4. **MINOR 4 — three post-state artifacts: FIXED (wording defect is finding 2 below).** Lines 95–96 name
   `marker-retirement_after_run.json` / `.rc` / `.note`.
5. **MINOR 5 — report cites the procedure commit and the exact `anchor_gate` path: FIXED.** Line 127 requires
   citing "this procedure commit" (the commit is `034be89d…`, not on `mac-b1-20261107`); line 124 reads
   `scripted_minus_random` from `batch_state.json` `anchor_gate.scripted_minus_random` — confirmed present at that
   path.

## Findings requiring changes

1. **MINOR — `:1` and `:9–12`: the rev-3 artifact still labels itself "rev 2" and its changelog records only the
   round-1 fixes.** Line 1 reads "…candidate for review (12 November 2026, rev 2)" (byte-identical to the rev-2
   title) and lines 9–12 say only "Rev 2 fixes the round-1 review: …". None of the round-2 fixes now present
   (explicit-status retire block with tmp+rename, step-1 `watch.log` count/last line, step-6 path preamble,
   three-artifact post-state check, procedure-commit citation + `anchor_gate.scripted_minus_random`) is recorded.
   In a chain that identifies the unit by revision (round 2 reviewed "rev 2" = `341f02b7`), the executed artifact
   would misstate its own revision and content, and a later auditor cannot tell rev 2 from rev 3 by the file
   itself. **Minimal fix:** change the title to "rev 3" and append one changelog sentence: "Rev 3 fixes the
   round-2 review: the retire block runs the helper under an explicit status test with tmp-name and rename-on-
   success, step 1 records the pre-retire `watch.log` count and last line, step 6 carries its own path preamble,
   the post-state check requires `.json`/`.rc`/`.note`, and the report cites this procedure commit and reads
   `anchor_gate.scripted_minus_random`."
2. **NIT — `:95–96`: "marker absent, both the three `marker-retirement_after_run.json` / `.rc` / `.note` artifacts
   present".** The leftover "both" contradicts "three" and could be read as a two-artifact check.
   **Minimal fix:** delete "both" ("… marker absent, the three … artifacts present").

## Checks performed

| Check | Result |
|---|---|
| Unit identity / parent / diff scope (only the proposal) | PASS — `034be89d…`, parent `341f02b7…`, 1 file, 27+/11− |
| Live marker dev/ino/sha, receipt sha, `_b` transition files, no `*_after_run.*` | PASS — exactly the stated facts (see above) |
| Run still RUNNING; procedure not executed; unit non-executing | PASS — RUNNING, tmux/runner/server present, lease held, no `b1.exit` |
| Retire block: rc reachable under `set -e`, tmp+gate+`mv`, `.rc`, `.note`, `$PY`, `rm -f` scope | PASS — simulated success/failure/empty cases; `rm -f` only the named `.tmp` |
| Step 1 pre-retire `watch.log` count + last line | PASS — `:60–61` |
| Step 6 `CHECKOUT`/`RUN_DIR`/`BATCH`/`PY` inside the block | PASS — `:102–105`; `bash -n` clean |
| Post-state requires `.json`/`.rc`/`.note` | PASS — `:95–96` (wording NIT) |
| Report cites procedure commit; reads `anchor_gate.scripted_minus_random` | PASS — `:124`, `:127`; path confirmed on TASL-7 |
| Verifier CLI at `4b312844`: `r1.exam.analyze b1 --batch --config --rule --rule-sha256` | PASS — `r1/exam/analyze.py:335–337`, dispatch `:342–345` to `b1_summary_verified` with the `53018aa7…` rule |
| `r1.scripts.b1_completion_usage --roots … --cap 16384` | PASS — `b1_completion_usage.py:226–227`; `return 2` on `ValueError/OSError/KeyError/JSONDecodeError` (`:233–234`), `0`/`1` from `cap_check` (`:237`) |
| Usage exit 1 expected/not STOP; exit 2 reported; verifier failure STOP | PASS — `:119–121` |
| Import preflight before retirement, uses `$PY` | PASS — precondition 5 `:46–50`, step 2 `:62`, retirement `:63–86` |
| `r1.scripts.b1_candidate_halves --work "$BATCH"` | PASS — `b1_candidate_halves.py:122` |
| No deletion / restoration / B2 / X.7 / sweep 2 / retry / pin change; STOP conditions | PASS — `:28–33`, `:130–132`, `:134–139`; retirement is `renameat2(RENAME_NOREPLACE)` into `_to_delete/`, no delete |
| Revision label / changelog match the reviewed revision | **FAIL** — finding 1 |
| Post-state sentence grammar | **NIT** — finding 2 |

## Residual notes

- On success the block leaves a zero-byte `$RUN_DIR/marker-retirement_after_run.json.tmp.err` beside the three
  artifacts; step 5 does not mention it. Harmless, but the operator should either add `rm -f "$TMP.err"` after the
  `mv` (it is the named `.tmp.err`, still within the no-deletion bounds) or ignore it explicitly in the report.
- Artifacts created by the block inherit the shell umask (likely 0644) while the `_b` transition files are 0600;
  `$RUN_DIR` is 0700 owned by `dowling`, so this is not an exposure. Optional `umask 077` at the top of the block.
- If `mv` ever failed after a successful retirement, `.rc` would say 0 with no final `.json`; step 5 would catch it.
  Neither the block nor the report prescribes how to re-run after that state — a re-run would fail the helper's
  receipt match (marker already renamed), so the STOP path is correct but the operator should say so.
- `b1_completion_usage` exit 2 stays "reported" while §3 treats any inconsistency as a STOP; that matches the
  required semantics (1 = expected, 2 = reported). The report must record exit 2 as an inconsistency for the fresh
  review, not as a clean result.
- `034be89d…` is on `trackS-ops-20261030` only (not on `mac-b1-20261107`); the report must cite `034be89d…` (and
  ideally copy the procedure to the report branch) so the executed record is self-contained.
- Preconditions still fail (no `b1.exit`, `RUNNING`, lease held, marker present). Do not run this unit until a
  verified normal completion (`b1.exit`=`0`, `status=COMPLETE`, own tmux session gone) exists.

## Verdict rationale

All five round-2 findings are fixed, and the safety-critical surface is sound: the frozen interpreter is used
everywhere, the import preflight still precedes the irreversible retirement, a failed retirement cannot produce a
final zero-length receipt or skip the rc/STOP evidence, the pre-retire watcher count exists, the verifier/usage
blocks are self-contained and match the run HEAD, and the scope still excludes deletion, restoration, B2/X.7,
sweep 2, retry and pin changes. However, the artifact under review still presents itself as "rev 2" and its
changelog does not record the rev-3 fixes, which is a traceability defect in the very record the execution will
cite; with the one-line title/changelog correction (and the "both the three" wording) this procedure is acceptable
for execution after a verified normal completion.

VERDICT: changes required
