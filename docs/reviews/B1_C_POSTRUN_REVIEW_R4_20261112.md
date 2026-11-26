# Independent final re-check — B1 `_c` post-run procedure rev 4 (round-3 fixes)

**Scope.** Narrow, pre-execution re-check of `docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md` at commit
`86fc85f6be3b31f182decfe2db85c196e0f47023` (parent `034be89dd909b9a15d6247be8ef13884245ae73c`; author and committer
Dowling Wong `<wangdowling@gmail.com>`, 2026-11-13 00:30:22 +0100; subject "B1: post-run procedure rev 4 (review
round 3 nits)") in `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`. Rev 4 is 144
lines, SHA-256 `f6bf9d7f93c272ffa95ded90d7a3ba6d5b0717b6b9c64c5de3275ce4d836e297`, git blob
`955fb707deb29d5095164b6abdff57ecb73c0ea1`. Rev 3 (`034be89d…`) is 139 lines, SHA-256
`0ad821635d1ecc3ede3e16d84e24c321a90d2e607d35ae69fdd4663633ab61d9`, blob `e6e0db71`. The branch tip on GitHub and
on the TASL-7 bare repo `/home/dowling/r1_tracks/remotes/Agent_paper_B.git` is `86fc85f…`; it is not an ancestor of
`mac-b1-20261107` (tip `57b8d2d5…`). The reviewer is independent of the author; nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified; the TASL-7 checks were read-only
(`ls`/`stat`/`sha256sum`/`cat`/`find`/`tmux ls`/`pgrep`/`flock -n`), the procedure was not executed and no write or
signal was issued to the running B1 scene.

## 1. Diff scope and claimed fixes (`git diff 034be89d 86fc85f6`)

`--name-status` is one `M docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`; `--stat` is 1 file changed,
7 insertions(+), 2 deletions(-); `--summary` is empty (no mode change); `--check` is clean. There are exactly four
hunks (zero-context old lines 1, 12, 65, 81):

1. `:1` title `… (12 November 2026, rev 2)` → `… (12 November 2026, rev 4)`.
2. `:12–15` appends the rev-3/rev-4 changelog (Rev 3: reachable rc gate with tmp-then-mv, no zero-length receipt,
   pre-retire `watch.log` line count, step-6 paths, three-artifact check, report citations; Rev 4: title/changelog,
   leftover wording, `umask 077`, success-path `.tmp.err` removal).
3. `:69` inserts `   umask 077` as the second line of the step-3 retire block.
4. `:86` inserts `   rm -f "$TMP.err"   # success path only; nothing else removed` after the `mv`.

No other bytes changed. The title and changelog are as claimed; `umask 077` and the `.tmp.err` removal are present.
**However, the claimed removal of the leftover "both the three" wording is not in the diff** (see finding 1), so the
commit body "the leftover 'both the three' wording fixed" and the new `:14–15` sentence "Rev 4 is … the leftover
wording only …" are inaccurate.

## 2. Safety-relevant surface unchanged from `034be89d` (verify by diff)

Because the diff is confined to the four hunks above, every other line is byte-identical to the round-3 file:

| Element | Status |
|---|---|
| Retire if/else rc gate, `rc` written, `-s"$TMP"` gate, `mv` (current `:75–85`) | unchanged |
| Pre-existing-tmp removal only (`rm -f "$TMP"`, `:74`) and tmp+rename pattern | unchanged |
| Frozen `$PY` everywhere; no bare `python3` (bindings `:24–25`; blocks `:72`, `:75`, `:121`, `:130`) | unchanged |
| Pre-retirement import preflight (precondition 5 `:49–53`, step 2 `:65`) still before retirement `:66` | unchanged |
| Pre-retire `watch.log` count/last line (`:63–64`) and new-line-only watcher scoping (step 4 `:94–99`) | unchanged |
| Step-6 path preamble `CHECKOUT`/`RUN_DIR`/`BATCH`/`PY` (`:107–110`) | unchanged |
| Three-artifact post-state check (`:100–101`) — semantics unchanged (wording defect remains) | unchanged |
| Verifier `r1.exam.analyze b1 --batch --config --rule --rule-sha256` (`:115–119`) and usage `--roots --cap 16384` (`:121–122`) | unchanged |
| Usage exit-1 expected / exit-2 reported / verifier failure STOP (`:124–126`) | unchanged |
| No deletion/restoration/B2/X.7/sweep 2/retry/pin change; STOP list (`:31–36`, `:127–137`, `:139–144`) | unchanged |

The added `umask 077` is a tightening, not a safety-relevant semantic change; `rm -f "$TMP.err"` is reached only
after the rc gate and `mv`, so a failed retirement still preserves `.tmp`, `.tmp.err` and the nonzero `.rc`.

## 3. Spot-check of the current file

| Check | Result |
|---|---|
| Title says "rev 4" (`:1`) | PASS |
| Rev-3/rev-4 changelog present (`:12–15`) | PASS (but "leftover wording" claim untrue) |
| `umask 077` before the retire block (`:69`, before `:74–90`) | PASS |
| `rm -f "$TMP.err"` only on the success path (`:86`, after `mv` and after failure `exit 1`) | PASS |
| No "both the three" left | **FAIL — still at `:100–101`** |
| Unit non-executing ("not an execution and not an authorization", `:3–4`; exclusions `:31–36`) | PASS |

## 4. TASL-7 read-only facts (2026-11-12T23:32Z)

- `$BATCH=/home/dowling/exam-x/work/b1_4b31_20261112_c`: `status=RUNNING`, `phase=b1`, `interruptions=[]`,
  trial-level `completed` entries, `anchor_gate` present.
- `$RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c`: no `b1.exit`; `b1.log` 0 bytes, mode 600;
  no `*_after_run.*` (`find -maxdepth 1 -name '*_after_run*'` empty).
- `_b` transition files present: `marker-receipt.json`, `marker-retirement.json`, `marker-retirement.note`,
  `status-receipt.md`, `launch-run.txt`, `handover-run.txt`, `prechecks.log`, `receipt.sh`, `start.sh`,
  `inv_*_before/after.txt`.
- tmux `b1_4b31_20261112_c` and `trks_watch` alive; runner pid 3736030 (`r1.scripts.exam_runner b1`) and
  `llama-server` pid 3843862; `flock -n "$HOME/r1_locks/gpu0.lock" true` → `LEASE-HELD`.
- Live marker `$HOME/r1_locks/trackx_evidence.active`: dev 66306, ino 56261618, 82 bytes, mode 600, SHA-256
  `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, content
  `{"head": "4b312844962e1106db04d5a60bf996fad0e3e514", "run_id": "4b31_20261112_c"}`; receipt
  `$RUN_DIR/marker-receipt.json` SHA-256 `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`,
  dev/ino/sha/head/run_id matching. `_to_delete/` holds the two earlier retired names.
- The unit is therefore still not executable (precondition 1 fails) and nothing was retired.

## Findings

1. **MINOR (documentation/traceability) — `:100–101`: the round-3 "both the three" NIT was not applied.**
   The line still reads "marker absent, **both** / the three `marker-retirement_after_run.json` / `.rc` / `.note`
   artifacts present". The rev-4 diff has no hunk at this location, yet the title/changelog (`:14–15`) and the commit
   body claim the leftover wording was fixed. The executed record would still misdescribe its own revision content,
   and a two-artifact reading of the post-state check remains possible. No safety impact. **Minimal fix:** delete
   "both" so the sentence reads "marker absent, the three … artifacts present"; commit as a new rev (e.g. rev 5),
   and re-check that the diff at this line is the only content change.

## Residual notes

- Commit body says "`umask 077` added to the host blocks" (plural), but only the step-3 block sets it (`:69`); the
  step-6 block (`:105–123`) does not. Its outputs land in the 0700 `$RUN_DIR`, so there is no exposure; either add
  the same line to step 6 or word the message as singular. Cosmetic.
- `rm -f "$TMP.err"` deletes only the file the block itself created on the success path; the failure path preserves
  it with `.tmp` and `.rc`. This stays within the no-deletion bounds stated in round 3.
- `86fc85f…` is on `trackS-ops-20261030` but not an ancestor of `mac-b1-20261107`; the post-run report must cite
  this commit (and ideally copy the procedure to the report branch) so the executed record is self-contained.
- Preconditions still fail (RUNNING, lease held, marker present, no `b1.exit`); do not run this unit until a
  verified normal completion exists.

## Verdict rationale

The safety-critical surface is untouched: the rc-gated tmp+rename retirement, frozen interpreter, pre-retirement
import preflight, watcher scoping, step-6 definitions, three-artifact check and verifier/usage semantics are
byte-identical to the round-3 file, and the two new lines are a tightening and a success-path cleanup. But rev 4
claims to fix the round-3 wording NIT and does not: "both the three" remains, and the new changelog asserts a fix
that is absent. That is the one remaining documentation/traceability defect, so the unit needs one more one-line
revision before it can be accepted for execution.

VERDICT: changes required
