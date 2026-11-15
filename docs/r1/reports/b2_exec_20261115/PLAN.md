# B2 execution plan — TASL-7 (15 November 2026)

**Run HEAD:** `8709dce792d45bbb5c05d9f7d239e19454efbb15` (branch `ops-b2-20261115`). **Run ID:** `8709_20261115_b2`. **Output tree:** `/home/dowling/exam-x/work/b2_8709_20261115_b2`. **Operator:** DeepSeek Harness agent (AI-assisted). **Nothing of B1's `_a`/`_b`/`_c`/`_d` is moved, overwritten or deleted; Track S stays paused until B2 ends; the marker is created only after the HEAD review, the three-way base check, the post-review author gate and the re-reviewed occupancy/launch plan hold. All host commands below run as `dowling@TASL-7`.**

**Exec record pinning.** These scripts live on branch `ops-b2-exec-20261115` of the Paper B repo. Delivery is pinned to the **accepted exec commit** — `REVIEWED_EXEC_SHA` must equal the commit named in the reviewer's final verdict for this plan (the current accepted commit is recorded there and in `origin/ops-b2-exec-20261115`); `deliver.sh` refuses a dirty worktree, a local HEAD different from that commit, or an `origin/ops-b2-exec-20261115` that differs from it. `deliver.sh` intentionally checks the Mac worktree path and installs `publish_status.sh` nowhere (it runs on the Mac only).

## Bindings

| item | value |
|---|---|
| run HEAD | `8709dce792d45bbb5c05d9f7d239e19454efbb15` |
| reviewed base (`paper_commit`) | `37282ec37a715feaaea48dd621ae08678424accc` |
| staged checkout | `/home/dowling/r1_b1_engineering/b2_paper_final_<HEAD>/paper` (clean exact HEAD) |
| harness | `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness` (`a3fedbb`, clean) |
| frozen venv (B1 `_d`) | `/home/dowling/exam-x/work/venv` (Python 3.13.4; `venv_pins.txt`) |
| RUN_DIR | `/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2` (bootstrap creates it) |
| RUN_DIR subdirs | `prechecks/`, `postmarker/`, `postwatch/`, `monitor/` (bootstrap creates all four) |
| local receipt STATUS | `$RUN_DIR/status-receipt.md` (bootstrap-created empty; the marker tool appends) |
| delivered files | 11 reviewed files (8 host scripts + `expected.txt`, `venv_pins.txt`, `watcher_expected.txt`); `publish_status.sh` stays on the Mac |
| gate capture | `/home/dowling/r1_b1_engineering/b2_final_gate_preflight_8709_20261115_b` (`_a` = pre-review dry run) |
| preflight output | `/home/dowling/exam-x/work/b2_host_preflight_8709_20261115_a` (new direct child of `work_dir`) |
| marker | `~/r1_locks/trackx_evidence.active` |
| published STATUS | branch `mac-b1-20261107`; clean separate checkout `.claude-worktrees/b1-status-20261115` on that branch, HEAD = origin `fcf52c09` |
| host-side confirmations (15 Nov, read-only) | watcher pane pid `1388760` (cmd `bash`), script sha `cf6884…`; harness has 0 untracked files; exam-venv extra pins pytest 9.0.3 / numpy 2.4.4 / scikit-learn 1.8.0 match |

## Order

0. **Prepare (Mac).** Be on the exec worktree at the reviewed exec commit, clean. Bootstrap transport:
   `ssh -o BatchMode=yes tasl7 'bash -s' < bootstrap.sh` (creates `$RUN_DIR`, the four subdirs and the empty owned receipt STATUS; records `bootstrap-receipt.txt`; **no marker**).
   Deliver (from `docs/r1/reports/b2_exec_20261115/`):
   `REVIEWED_EXEC_SHA=<accepted exec commit> bash deliver.sh` — checks local HEAD == that commit, clean worktree, origin exec branch == it, remote hostname `TASL-7`, `$RUN_DIR` a non-symlink dir; installs the 11 files with no-clobber `set -C`, per-file SHA-256 against `git show <commit>:<path>`, and writes the **host** `delivered-receipt.txt` over ssh (commit + every SHA + UTC; checked absent first) and a local `delivered-receipt.local.txt` in the exec worktree.
1. **Prechecks (host, fail-closed; pre-marker).** `bash "$RUN_DIR/prechecks.sh"`. Checks: expected GPU UUID, disk ≥100 GB, lease (`flock -n gpu0.lock` — labelled a transient lease check), locks and `*.active` markers absent, watcher identity compared to `watcher_expected.txt` (pane pid, script SHA-256) with the tmux-client caveat noted, `watch.log` position, no Track S collect/`trks_llm`/P.3a, no GPU compute app, full `ps` census, manifest/STOP inventories with `find` traversal errors as STOP, explicit sibling STOP presence/absence, `_d` predecessor retirement record, STATUS-source hashes, **pre-marker frozen-venv pins** and harness pin/clean. On success writes `PRECHECKS_PASS` + `prechecks/prechecks.ok` (exclusive).
   *Prechecks re-run policy:* a STOP leaves no `.ok`; do not delete. Move the stopped attempt aside (`mv "$RUN_DIR/prechecks" "$RUN_DIR/prechecks.attempt-$(date -u +%Y%m%dT%H%M%SZ)"`, a move) and re-create `prechecks/` before a fresh run; record the reason.
2. **Marker first.** `bash "$RUN_DIR/create_marker.sh"` — requires `prechecks.ok`, empty owned regular receipt STATUS, absent marker, clean exact HEAD; `b1_o2_marker.py create --phase b2`; validates receipt (`run_id`/`head`/dev/ino/64-hex sha); runs `inventory_after.sh` (post-marker inventory).
3. **Publish the running STATUS** (Mac):
   `bash publish_status.sh /Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/b1-status-20261115 8709_20261115_b2 8709dce792d45bbb5c05d9f7d239e19454efbb15`
   Requires: host marker receipt readable and binding run_id/head/dev/ino/sha; status checkout clean on `mac-b1-20261107` with HEAD == origin; appends `## 2026-11-15 — Track X B2 running` + Run/HEAD; commit identity `Dowling Wong <wangdowling@gmail.com>`; `git push origin HEAD:refs/heads/mac-b1-20261107` (**no force**); verifies remote SHA; writes `$B2_STATUS_RECEIPT` (default `/tmp/b2_status_receipt.txt`) with the marker-receipt SHA-256. Dirty/advanced/push mismatch = STOP, marker preserved, no force/retry.
4. **Observe the watcher, then the handover check.** `bash "$RUN_DIR/postwatch_check.sh"` — requires `watch.log` growth and `priority marker seen`, `FORCED` is a STOP, `servers stopped; lease released` or no `trks_llm`; takes a **fresh** manifest/STOP inventory after the pause, requires the manifest inventory unchanged, every new/changed STOP to be a sibling of a known manifest, no STOP disappearance (no-deletion), no GPU compute app, lease free, P.3a absent, marker present; writes `postwatch/postwatch.ok` (exclusive) + log.
5. **Host preflight.** `bash "$RUN_DIR/preflight.sh"` — env hygiene, CAP/OUT/CACHE/PAPER/HARNESS/PY checks, `prechecks.ok` + `postwatch.ok` + marker, exact `GATE_PASS <HEAD> <rule-sha>` and `gate.exit` 0, harness pin/clean and frozen-venv pins, no compute app + lease free; runs `python -B -m r1.scripts.b1_host_preflight --head <HEAD> --out <new child>` with no-clobber capture; requires `PREFLIGHT_PASS` **and** rc 0, re-checks GPU/lease; writes `preflight.ok` exclusively; exits with the preflight rc.
6. **Launch.** `nohup bash "$RUN_DIR/receipt.sh" >/dev/null 2>&1 &` — `receipt.sh` refuses existing `b2.log`/`b2.exit`, writes the log + `B2_EXIT=<rc>` + `b2.exit`; `start.sh` re-checks `prechecks.ok`, post-marker inventory, `postwatch.ok`, `preflight.ok`/exit/PREFLIGHT_PASS, exact GATE_PASS, marker receipt run_id/head, P.3a absent, no compute app, clean exact HEAD, harness pin; unsets `LLAMACPP_CACHE_PROMPT`; `exec python -B -m r1.scripts.exam_runner b2 --config <checkout>/r1/scripts/configs/exam_b2_v2.json --out <output tree>`.
7. **Monitor every ≤30 min** with `bash "$RUN_DIR/monitor.sh"` (append-only captures under `$RUN_DIR/monitor/<UTC>/`: runner/exit/log tail/batch_state/manifests/journal/GPU/lease/marker). A STOP is preserved and reported, never retried; Track S/P stay paused.
8. **After the run** (or a stopped run): retire the marker with `b1_o2_marker.py retire` + receipt under a reviewed post-run unit; publish `B2 done`/`B2 stopped` on the STATUS branch; hand back per hand-off §6 and send the B2 report to independent review (STOP 6). Malformed retirement = STOP (marker preserved).

## STOP conditions (preserve, report, no retry)

Any prechecks STOP; empty/failed marker receipt; STATUS checkout dirty/advanced/push failure or receipt mismatch; `FORCED`/unexpected touched path/STOP disappearance; missing POSTWATCH_PASS; preflight rc≠0 or missing PREFLIGHT_PASS; dirty/mismatched run checkout or harness; existing batch tree/log/exit; any launch-condition mismatch. Nothing is deleted, the marker is not retired on an abnormal stop, and no retry is automatic.

## Three-way base and gate (closed)

`reviews/B2_CODE_UNIT_REVIEW_20261114.md` `Reviewed base:` and last `Accepted commit:` = `37282ec3…`; Mac `Claude outputs/READY.txt` item 26 `Reviewed base:` = `37282ec3…` (SHA-256 `0ad9dd6f…`, `READY_RECORD.md`); config `paper_commit` = `37282ec3…`. Post-review author gate on the staged checkout: `GATE_PASS 8709dce7… 53018aa7… phase b2` in the `_b` capture.
