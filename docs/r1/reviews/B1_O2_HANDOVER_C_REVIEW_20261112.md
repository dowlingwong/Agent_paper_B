# Independent review — B1 `_c` restart O2 handover, marker transition, STATUS publication and launch (run `4b31_20261112_c`, 12 Nov 2026)

**Reviewer.** Freshly spawned independent reviewer; did not write this unit. Read-only on `tasl7`
(`ls`/`stat`/`cat`/`sha256sum`/`git rev-parse`/read-only `git status`/`tmux ls`/`nvidia-smi`/`flock` probe/
`ps`/`pgrep`), no writes, signals, GPU work, server start or deletion; writes only under
`/Users/wongdowling/Documents/agent_sys_paper/` and `/tmp`. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified. `/tmp/pb_status` was left untouched; the STATUS
publication was exercised only on a throwaway clone (`/tmp/pb_sim`) with a local bare remote.
Review times: Mac `2026-11-12T21:39+01:00`; `tasl7` UTC `2026-11-12T20:39Z`, host-local `12:39 PST`.

**Unit reviewed (exact filled files, sha256 recomputed).** All under
`/tmp/b1_handover_c_4b31_20261112_c/`; every value matches the operator's list:

| file | sha256 |
|---|---|
| `PLAN.md` | `b79eb7cac1380a6ab45930c778c6a4f7e93f9e2f5bf3d427f684c3a7801b87f3` |
| `handover_pre.sh` | `8dfe158e18a179d994f16da1c202d44f3d3edb62447d7da45cff1b8e44700e64` |
| `handover_run.sh` | `b267181dc794ce66fdf0a685aa48bad312673ab9fafcf177f5d6f76944759a88` |
| `status_publish.sh` | `648543c1eb9a2dfa015289110aaaa1b7478de1fa1bdb7ddee03a99cde3dcaad0` |
| `launch.sh` | `94ac760060a39df6c603b7c4d86e9cb74b7837e919a09531eb5d70fda769eb68` |
| `launch_precheck.sh` | `2facbc23fd109376e75c4277a6ab51f4dfe34c4cfb84f67b9429eb957e3e1358` |
| `launch_start.sh` | `c811032394af27ee49de0b0da53262356f071a05f509654e4090820119bb6fb2` |
| `start.sh` | `1fa0d5c0ac05c112552d0091fe56122c844c7baf686d44a4a2b6e4bb57426a83` |
| `receipt.sh` | `4da34a18ef81b071e32400e1612936406754c7df3b9992cbcd54c58fd74734e7` |

Governing documents read at the run HEAD in the staged checkout
`/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper`:
`docs/r1/proposals/B1_RESTART_HANDOFF_C_20261111.md` §§0–2 (esp. §2.4), `docs/r1/proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md`,
`docs/r1/reports/B1_TASL7_HANDOVER_COMMAND_BOUNDARY_20261107.md`, `docs/r1/proposals/B1_OPERATOR_MESSAGE_V3_20261107.md`,
and PLAN §10 rows `R1-EXAM-B1-TRUNCATION-INVALID`, `R1-EXAM-B1-ANCHOR-R4`, `R1-EXAM-B1-ANCHOR-R4-H2`
(all present at the run HEAD). The run HEAD `4b312844…` is a one-line prose change to
`docs/r1/authorizations/trackx_b1_20261105.md` only; the config's `paper_commit` is `1334c616…`.

## 1. Current site state (read-only, evidence)

- **Old marker.** `~/r1_locks/trackx_evidence.active`: dev `66306`, ino `56261610`, mode `600`, size `82`,
  nlink 1, owner `dowling:dowling`, sha256 `23fa767be7346809d087d0a2352241e6042abdd04df2f198e476b8f39eab4c9a`,
  content `{"head": "fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa", "run_id": "fffa_20261111_b"}`. The `_b` creation
  receipt `…/b1_handover_fffa_20261111_b/marker-receipt.json` has sha256
  `1cd979aedef534f611963e419a92c02fe385d81f8119d477d4389480459a4405` and fields
  `{dev:66306, ino:56261610, head:fffa45a1…, run_id:fffa_20261111_b, sha256:23fa767b…}` — an exact match.
- **`_b` handover directory.** Present; contains `marker-receipt.json` (191 B, 1cd979ae…),
  `marker-retirement.json` (261 B, the **6835** transition, `retired: trackx_evidence.active.c51a7c4388bf469f85155263fb4079f5`),
  `status-receipt.md`, `b1.exit` = `1`, `b1.log` (653 B, the truncation STOP), inventories, scripts and
  `launch-run.txt`/`handover-run.txt`. No `marker-retirement_c.json`. Nothing in the unit writes into this
  directory; the retirement JSON/note paths are under the new `_c` directory.
- **`_to_delete`.** Contains only the 6835 marker `trackx_evidence.active.c51a7c4388bf469f85155263fb4079f5`;
  the `_b` marker is still live, so the retirement is still pending.
- **Watcher.** Default socket `tmux ls` = only `trks_watch` (pane pid `1388760`, `bash …/trks-watch`, alive,
  script sha256 `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112`). `watch.log` has 3 lines;
  last `2026-11-08T00:46:56Z priority marker seen (/home/dowling/r1_locks/trackx_evidence.active): pausing`.
  The watcher is in its inner `while marker; do sleep 60` paused loop; the retire/create gap is sub-second,
  so the expected path is `WATCHER_ALREADY_PAUSED_NO_NEW_LINE`, which the script handles.
- **Inventory.** Exactly one `manifest.json` — `/home/dowling/r1_tracks/out/smoke/manifest.json`
  (dev `66306`, ino `57039147`, `5340` B, `dowling:dowling`, regular `f`, mtime `1793323478.0640841870`) —
  and one `STOP` — `/home/dowling/r1_tracks/out/smoke/STOP` (dev `66306`, ino `57048195`, `0` B, regular `f`,
  mtime `1794098816.7435273490`). No other manifest/STOP.
- **Track P / drill.** `~/r1_locks/trackp_evidence.active` and `~/r1_tracks/trks_drill.active` absent;
  `pgrep -u dowling -af 'r1p_|p3a|llama-server|r1\.tracks|exam_runner'` empty (the script is fed via
  `ssh 'bash -s'`, so no self-match); no P.3a-like process in the full `ps -u dowling`; no `trks_llm` session.
  The O2 draft's caution that an empty `pgrep` is a proxy is noted, but the plan's snapshot, the absent GPU
  compute, the single default session and the 6835 private session (idle interactive bash only) support
  "P.3a absent" on this state.
- **GPU / lease / disk.** No compute apps; GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, 236 MiB used of
  24,564 MiB, 0 % util; `flock -n ~/r1_locks/gpu0.lock true` → LEASE-FREE; disk avail `567,344,525,312` B
  (≥ 100 GB).
- **New paths.** `/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c` and
  `/home/dowling/exam-x/work/b1_4b31_20261112_c` absent; session `b1_4b31_20261112_c` absent.
- **6835 and `_b` scenes.** 6835 handover dir, batch `/home/dowling/exam-x/work/b1_6835_20261108_a`, and its
  private tmux socket/session `b1_6835_20261108_a` intact; `_b` batch `/home/dowling/exam-x/work/b1_fffa_20261111_b`
  intact. No deletion/move of either scene is in the unit.
- **Staged checkout / harness.** `…/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper`:
  HEAD `4b312844962e1106db04d5a60bf996fad0e3e514`, `status --porcelain -uall` empty, no remotes,
  `fsck --connectivity-only` rc 0; `r1/scripts/b1_o2_marker.py` sha256
  `8beedc2a0394f6153eb141f0e0854974887d4c9153f27a9f1fa5cc52532fc599`. Harness
  `…/b1_harness_offline_stage_20261107_a/harness` at `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, clean.
- **Gate + preflight.** CAP `b1_final_gate_preflight_4b31_20261112_a`: `gate.exit` `0`, `gate.log` ends
  `GATE_PASS 4b312844962e1106db04d5a60bf996fad0e3e514 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad …`;
  `preflight.exit` `0`, `preflight.log` ends `PREFLIGHT_PASS: owned server exited and own lease descriptor closed`;
  OUT `b1_host_preflight_4b31_20261112_a` present. Run-HEAD, staging and preflight-result reviews all
  `VERDICT: accepted`.
- **STATUS checkout.** `/tmp/pb_status` branch `mac-b1-20261107`, HEAD
  `8af27919a8cb0f9f818acb05528a6727f927eb55` = `origin/mac-b1-20261107` = `git ls-remote` tip; clean.
  `docs/r1/STATUS.md` ends with the 2026-11-11 `fffa_20261111_b` line and `\`.\n`; no `4b31_20261112_c`,
  no `## 2026-11-12`; existing running headings are 2026-11-08 and 2026-11-11.
- **Dates.** UTC `2026-11-12T20:39Z`; `tasl7` local `2026-11-12 12:39 PST`; Mac `2026-11-12 21:39 CET`.
  Both handover date guards (`date -u +%Y%m%d` and `date +%Y%m%d` = 20261112) pass now.

## 2. Check results

1. **Order and fail-closed behaviour — PASS.** The chain is `handover_run.sh` → remote `handover_pre.sh`
   (HOME/RUN_DIR/BATCH/PAPER/HARNESS/HEAD/clean/UTC+host-local date/compute/owned-processes/tmux/Track P+drill/
   lease/disk/old marker-vs-receipt → inventory → `retire` → retirement JSON+note → seed local STATUS →
   `create` → receipt-vs-live-marker → 75 s watcher → re-inventory → post compute/process/lease) → `status_publish.sh`
   → `launch.sh` (`launch_precheck.sh` → exclusive uploads → `launch_start.sh`). Each local wrapper records
   `rc` and requires its sentinel (`HANDOVER_PRE_DONE`; per-step rc plus `LAUNCH_PRECHECK_PASS`/`LAUNCHED`).
   No `rm`, `mv`, `kill`, `--force`, or retry path; the only rename is the reviewed `retire`. The `_b` receipt
   is kept; the retirement JSON and `.note` go to the new `_c` directory; the `_b` directory is only read.
   The old dir's existing `marker-retirement.json` cannot false-STOP the precheck, which looks for
   `marker-retirement_c.json` (absent).
2. **Marker transition correctness — PASS.** `OLD_HANDOVER` is `…/b1_handover_fffa_20261111_b`,
   `OLD_RECEIPT=…/marker-receipt.json` (sha256 `1cd979ae…`). The live marker matches that receipt
   (dev/ino/sha256/content), checked in Python before `retire` and re-checked by `retire`. The new create uses
   `RUN_ID=4b31_20261112_c`, `HEAD=4b312844…`, `TZ=UTC`, `--status RUN_DIR/status-receipt.md`; the receipt is
   asserted against the live marker (dev/ino/sha256, `run_id`/`head`, exact content). The new retirement JSON
   goes to `$RUN_DIR/marker-retirement.json`; the note to `$RUN_DIR/marker-retirement.note` with
   `source_receipt=/home/dowling/r1_b1_engineering/b1_handover_fffa_20261111_b/marker-receipt.json` and
   `source_receipt_sha256=1cd979ae…`. The `_b` directory receives no write. Local helper test (`/private/tmp`)
   confirmed `create` writes `\n## 2026-11-12 — Track X B1 running\n\nRun: \`4b31_20261112_c\`; reviewed
   checkout HEAD: \`4b312844…\`.\n` under `TZ=UTC`, and a second create fails on `O_EXCL`. `retire` is Linux-only
   and was not executed here; the same helper's 6835→`_b` rename on this site (the 6835 marker now in
   `_to_delete`) and the exact live marker/receipt match are the evidence.
3. **Date / run-ID bindings — PASS.** `handover_pre.sh:20–21` assert UTC and host-local `20261112`; the run ID
   is `4b31_20261112_c`; `status_publish.sh:6–7` asserts UTC `2026-11-12`; the local receipt and the pushed
   heading are `## 2026-11-12 — Track X B1 running`; `launch_precheck.sh:16` re-asserts the literal heading.
   A start after 00:00 UTC is a STOP at `handover_pre.sh:20`; a start before midnight that crosses during the
   handover would either create a 13th-dated local receipt (if `create` is after midnight) and then STOP at
   `status_publish.sh:7`, or fail the line-80 heading check (if only the check is after midnight); in either
   case the marker is retained and no launch occurs, i.e. no silent date change (see R5 for the hardening).
4. **STATUS publication — PASS.** On a throwaway clone of `/tmp/pb_status` with a local bare `origin`, the exact
   script (only `cd` path changed) appended the heading and `Run: \`4b31_20261112_c\`; reviewed checkout HEAD:
   \`4b312844…\`.`, committed as author and committer `Dowling Wong <wangdowling@gmail.com>`, pushed FF-only to
   `refs/heads/mac-b1-20261107`, verified the remote tip, and a second run STOPped `run-id-already-published`.
   The real checkout is at the origin tip, clean, with no duplicate run-ID/heading. No push to `main`, `r1` or
   `exam-x`; no force; the body records the operator decision (DSH, not Codex).
5. **Launch leg — PASS (one low residual, R1).** `launch_precheck.sh` asserts staged HEAD/clean, marker
   dev/ino/sha/content and `run_id`/`head`, `marker-retirement.json` presence, local STATUS heading, absent
   BATCH/b1.exit/start.sh/receipt.sh/session. It does **not** require/verify `marker-retirement.note`, although
   PLAN step 3 says it does (R1; the note is written fail-closed by `handover_pre.sh:71`). Uploads use
   `set -C` exclusive create; `launch_start.sh` re-verifies the exact reviewed `start.sh`/`receipt.sh` SHAs
   (`1fa0d5…`, `4da34…`) and syntax, absent BATCH/b1.exit, absent session, starts
   `tmux new-session -d -s b1_4b31_20261112_c "exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /bin/bash '$RUN_DIR/receipt.sh'"`
   and asserts at 8 s and 15 s session alive, `b1.exit` absent, `b1.log` exists, then prints `tmux ls` and
   `LAUNCHED`. `launch.sh` runs each of the four SSH steps through `run_step` with per-step rc and STOP on the
   first nonzero rc (verified with a fake `ssh`: a failing precheck stops before any upload), requires
   `LAUNCH_PRECHECK_PASS` and `LAUNCHED`, writes `SHA256SUMS` and `RUN_DIR/launch-run.txt`.
   `start.sh` checks HEAD/clean, BATCH absent, PAPER/HARNESS/RUN_DIR/PY present, then
   `exec "$PY" -B -m r1.scripts.exam_runner b1 --config "$PAPER/r1/scripts/configs/exam_b1_v2.json" --out "$BATCH"`.
   `receipt.sh` captures `b1.log` and `b1.exit`.
6. **Site / state — PASS.** See §1. Current marker matches the `_b` receipt; P.3a absent; watcher paused on the
   known line; new RUN_DIR/BATCH/session absent; 6835 and `_b` scenes intact; staged checkout, gate, preflight
   and STATUS checkout in the reviewed state; no forbidden effects. A reviewer-spawned read-only
   `grep -rl` under `/home/dowling` (background probe) briefly remained in D state and had exited by
   `20:39Z`; it matched none of the precheck patterns, wrote nothing, and is not present at review close.

## 3. Non-blocking residuals (accepted or recommended hardening)

- **R1 (low) `launch_precheck.sh:13–16`.** It checks `marker-retirement.json` but not `marker-retirement.note`,
  contrary to PLAN step 3. The note is created fail-closed by `handover_pre.sh:71–72` and is present before
  launch, so handoff C's "naming the `_b` receipt by path and SHA-256" is implemented; the launch leg does not
  re-verify it. Minimal fix: add `[ -f "$RUN_DIR/marker-retirement.note" ] || fail no-retirement-note` and grep
  for `source_receipt=…/b1_handover_fffa_20261111_b/marker-receipt.json` and
  `source_receipt_sha256=1cd979ae…`.
- **R2 (low) `handover_pre.sh:45–53,71`.** The known `_b` receipt SHA-256 `1cd979ae…` is not hardcoded; the
  script trusts the receipt's fields against the live marker and records the computed SHA in the note. The
  current marker/receipt match is exact. Minimal fix: assert `sha256sum "$OLD_RECEIPT"` = `1cd979ae…` before
  `retire`.
- **R3 (low) `handover_pre.sh` prechecks.** The `b1_4b31_20261112_c` session absence is checked only in
  `launch_precheck.sh:31`, after the marker transition and STATUS publication; PLAN's "session absent" is a
  pre-transition precondition. Current state absent. Minimal fix: add the `tmux has-session` check to
  `handover_pre.sh` before `retire`.
- **R4 (low) `handover_pre.sh:119`.** The inventory diff allows changes to `smoke/manifest.json` as well as
  `smoke/STOP`; the directed watcher effect is the STOP touch only. The manifest is read, not written, by the
  watcher; current inventory unchanged. Minimal fix: filter only `smoke/STOP`.
- **R5 (low) `handover_pre.sh:80`.** The local heading check uses `date -u +%F` rather than the literal
  `2026-11-12`; a pre-midnight start that crosses UTC midnight could create a 13th-dated local receipt (if
  `create` is after midnight) and then STOP at `status_publish.sh:7`, or fail the line-80 check (if only the
  check is after midnight); either way no launch. Current time leaves ~3 h 20 m. Minimal fix: literal date.
- **R6 (low) `launch.sh:17–20` (prior N11).** A missing/unreadable local input fails the `< "$D/…"` redirection
  before `run_step`; with no `set -e`, the later steps still run, and a missing `launch_precheck.sh` lets the
  launch step start the run before the post-step `LAUNCH_PRECHECK_PASS` sentinel STOPs. All four files are
  present/readable and hash-verified at review time. Minimal fix: `[ -r … ]` guards or `|| { echo STOP; exit 1; }`
  on each `run_step` call, and check `LAUNCH_PRECHECK_PASS` immediately after the precheck.
- **R7 (low) prior diff-error residual.** An empty `*.diff` from a `diff` failure yields empty `BADM`/`BADS`
  and `INVENTORY_DIRECTED_ONLY`; the inventory inputs are produced fail-closed, so this is negligible.
- **R8 (info).** `handover_run.sh:7` does not check the `printf | tee` status; `status_publish.sh` prints but
  does not persist the STATUS commit SHA into `RUN_DIR` (operator capture records it).
- **R9 (info).** `start.sh` does not assert the harness HEAD `a3fedbb`; the gate/preflight and the reviewed
  staged harness (`a3fedbb`, clean) cover it.

## 4. Bottom line

On the current site state the marker transition is correct and implementable: the `_b` marker matches its
creation receipt exactly, the retirement/creation order is fail-closed, the retirement JSON and the note naming
the `_b` receipt path+sha go to the new `_c` directory, and the `_b` directory is not written. The STATUS
publication and launch leg are executable as filled and fail-closed (per-step rc/sentinels, exclusive upload,
exact run-script SHAs, 8 s/15 s session assertions). The residuals above are non-blocking evidence/robustness
items; R1 (the note is not re-verified at launch) is the only claim-vs-code mismatch and does not prevent the
handoff C evidence (the note is created) or make execution unsafe. No force, deletion, retry, preemption or
other-track effect is present. Executing exactly these files in the stated order on this site state implements
handoff C for `4b31_20261112_c`, with STOP preservation respected.

VERDICT: accepted
