# Independent final confirmation — B1 `_c` post-run procedure rev 5

**Unit.** `docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md` at commit
`78c6fd7d9286fa64840650baa7cb5ee0e6844cc6` (parent `86fc85f6be3b31f182decfe2db85c196e0f47023`, both on
`https://github.com/dowlingwong/Agent_paper_B.git` branch `trackS-ops-20261030`; author and committer Dowling Wong
`<wangdowling@gmail.com>`, 2026-11-13 00:33:51 +0100; subject "B1: post-run procedure rev 5 (remove leftover
wording)"). Rev 5 is 143 lines, SHA-256
`b86d2386af67cd5096adb33da2b221d78002386ae29082b8c64e99efa99d08a9`, git blob
`ed4861d22583e1277a2514209ee6b9dcaa6ad167`. Rev 4 is 144 lines, SHA-256
`f6bf9d7f93c272ffa95ded90d7a3ba6d5b0717b6b9c64c5de3275ce4d836e297`, blob `955fb707`. The branch tip in the
GitHub clone and in the TASL-7 bare repo `/home/dowling/r1_tracks/remotes/Agent_paper_B.git` is `78c6fd7d…`, and
the file at that commit hashes to `b86d2386…` in both places. This reviewer is independent of the author; nothing
under `/Users/wongdowling/Documents/agent_paper_B` was modified; the TASL-7 checks were read-only
(`ls`/`stat`/`cat`/`sha256sum`/`find`/`tmux ls`/`pgrep`/`flock -n`/`git show`/`rev-parse`, and a read-only JSON
parse). The procedure was not executed; no write or signal was issued to the running B1 scene.

## 1. Diff scope — one file, one hunk, one word

- `git diff --name-only 86fc85f6 78c6fd7d` → exactly `docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`.
- `--stat` 1 file changed, 1 insertion(+), 2 deletions(-); exactly one hunk, `@@ -97,8 +97,7 @@`; `--summary`
  empty (no mode change); `git diff --check` output 0 bytes (clean).
- The sole content change is the deletion of the word `both` and the reflow of that sentence
  (`git diff -w` still shows only this hunk):

  ```
  -... lease free, marker absent, both
  -   the three `marker-retirement_after_run.json` / `.rc` / `.note` artifacts present, ...
  +... lease free, marker absent, the three `marker-retirement_after_run.json` / `.rc` / `.note` artifacts present, ...
  ```

  The post-state sentence now reads "marker absent, the three … artifacts present", i.e. the round-3/round-4
  "both the three" defect is gone; `grep -n both` finds no occurrence anywhere in the rev-5 file.
- Deterministic proof of "nothing else changed": taking rev 4, deleting the 5 bytes ` both` from line 100 and
  joining the same two source lines reproduces the rev-5 file byte-for-byte (`reconstruction_matches_rev5: True`).
  The only other bytes affected are the line-join whitespace/newline (markdown rendering unchanged).

## 2. No safety-relevant change vs `86fc85f6` (verify by diff)

The single hunk does not touch any safety block; byte-comparison of the corresponding line ranges of
`86fc85f6` and `78c6fd7d` returns True for each:

| Element | Location (rev 5) | Result |
|---|---|---|
| Retire if/else rc gate, `rc` write, `-s "$TMP"` gate, tmp+`mv`, `rm -f "$TMP.err"` (success path only) | `:66–93` (`:68–91` block) | unchanged (`retire_block_equal: True`) |
| `umask 077` in the retire block (not step 6) | `:69` | unchanged |
| Frozen `$PY` everywhere; no bare `python3` | `:24–25`, `:72`, `:75`, `:121`, `:130` | unchanged |
| Pre-retirement import preflight (precondition 5, step 2) still precedes retirement (step 3) | `:49–55`, `:65–66` | unchanged (`preconditions_equal: True`) |
| Watcher new-line scoping and pre-retire `watch.log` count/last line | `:63–64`, `:94–99` | unchanged |
| Step-6 path definitions `CHECKOUT`/`RUN_DIR`/`BATCH`/`PY` and verifier/usage commands | `:103–125` | unchanged (`step6_equal: True`) |
| Three-artifact post-state check | `:100` | semantics unchanged; only the leftover `both` removed (this is the fix) |
| Usage exit-1 expected / exit-2 reported / verifier-failure STOP | `:123–125` | unchanged |
| Scope exclusions and STOP list | `:31–36`, `:138–143` | unchanged (`stop_list_equal: True`) |

No deletion, no restoration, no B2/X.7/sweep-2, no retry or pin change are introduced.

## 3. Commit body correction and non-execution

- Body: "umask 077 is in the retire block" — accurate: `umask 077` appears once, at `:69`, inside the step-3
  fenced retire block; the step-6 block (`:105–122`) has `set -uo pipefail` and no `umask`. This correctly
  replaces the rev-4 body's plural overstatement ("added to the host blocks").
- Body: "step-6 outputs land in the 0700 RUN_DIR" — accurate: step 6 writes only
  `$RUN_DIR/complete_batch_verifier.json`, `.err`, `.rc` and `$RUN_DIR/completion_usage.txt` (`:118–121`), and
  `$RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c` is live `700 dowling:dowling`.
- Body: "the original text broke the phrase across a newline" — accurate (line 100 ended in `both`, line 101
  began `the three`).
- Unit non-executing: markdown-only change (`:3–4` "not an execution and not an authorization"; scope
  `:31–36`); no script/code path in the commit; the run is still RUNNING, so precondition 1 fails today.

## 4. TASL-7 read-only facts (observed 2026-11-12T23:34:56Z)

- `$BATCH=/home/dowling/exam-x/work/b1_4b31_20261112_c`: `batch_state.json` (mode 600) `status=RUNNING`,
  `phase=b1`, `interruptions=[]`, 64 `completed` entries, `anchor_gate` present.
- `$RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c`: mode 700; **no `b1.exit`**;
  `find -maxdepth 1 -name '*_after_run*'` → 0 hits.
- `_b` transition files present: `marker-receipt.json` (191 B), `marker-retirement.json` (261 B),
  `marker-retirement.note` (182 B), plus `status-receipt.md`, `launch-run.txt`, `handover-run.txt`,
  `prechecks.log`, `receipt.sh`, `start.sh`, `inv_manifests_before/after.txt`, `inv_stop_before/after.txt`.
- tmux: `b1_4b31_20261112_c` and `trks_watch` both alive; `exam_runner` pid 3736030 and `llama-server` pid
  3843862 running; `flock -n "$HOME/r1_locks/gpu0.lock" true` → `LEASE-HELD`.
- Live marker `$HOME/r1_locks/trackx_evidence.active`: dev 66306, ino 56261618, 82 B, mode 600, SHA-256
  `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, content
  `{"head": "4b312844962e1106db04d5a60bf996fad0e3e514", "run_id": "4b31_20261112_c"}`; receipt
  `$RUN_DIR/marker-receipt.json` SHA-256
  `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`; `$HOME/r1_locks/_to_delete/` holds the two
  earlier retired names only.
- Consequence: preconditions still fail (RUNNING, lease held, marker present, no `b1.exit`); the unit is not
  executable and nothing was retired.

## Findings

None. The round-4 wording defect is fixed, the diff is the one-word removal it claims to be, the safety surface
is byte-identical to `86fc85f6`, and the commit body's correction is accurate.

## Residual notes (non-blocking; no action requested for this confirmation)

- The file's own header (`:1`) and changelog (`:12–15`) still say "rev 4" while the commit subject/body say
  "rev 5". This is a stale label, not a safety or semantic issue: the post-run report cites the procedure commit
  SHA (`:131`), which is unambiguous. Noted for traceability only; not raised as a finding.
- The joined line `:100` is now 209 characters (other lines wrap near ~110). Cosmetic markdown reflow only; the
  rendered sentence is unchanged.
- `78c6fd7d…` is on `trackS-ops-20261030` but is not an ancestor of `mac-b1-20261107`; the executed report must
  cite the full commit SHA `78c6fd7d9286fa64840650baa7cb5ee0e6844cc6` (as the procedure already requires).

VERDICT: accepted
