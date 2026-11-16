# B2 post-run unit — independent re-review (round 11 bytes, pre-execution)

**Round 2 addendum (15 Nov 2026, ≈20:55–21:05 CET):** re-check of commit `83b9c80b` — see §8. The round-1 verdict below is historical; the operative verdict is the final line of §8.

**Reviewer of record:** independent re-review of the round-11 unit, continuing the review lineage of
`B2_OCCUPANCY_LAUNCH_REVIEW_20261115.md` (rounds 1–11). **Reviewed at:** review worktree
`.claude-worktrees/b2-postrun-review-20261115`, detached at `5c3ff87a`, 15 November 2026
(≈20:45–21:25 CET), **before execution** (runner still `RUNNING`, 19/24 roots). **Method:** read-only.
No unit step was executed, nothing was written on TASL-7, and no git write was made.

**Authority.** `proposals/B2_HANDOFF_EXEC_20261115.md` §5.9/§6; the run HEAD
`8709dce792d45bbb5c05d9f7d239e19454efbb15`, run ID `8709_20261115_b2`, rule sha
`53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`; the reviewed B2 code
(`r1/exam/analyze.py`, `r1/exam/b2_batch.py`, `r1/exam/campaign.py`, `r1/scripts/exam_runner.py`,
`r1/scripts/b1_o2_marker.py`, `r1/exam/runtime.py`); the host state on TASL-7.

## 1. Provenance and bytes reviewed

| Item | Value |
|---|---|
| Round-11 commit | `b8e2e0ee515a2a2779364b14431efc69435a49dc` (`fix(r1): B2 post-run unit round 11 …`) |
| Branch tip under review | `5c3ff87a5bb18d069cc21dc72c8d23b0deafb719` (`ops-b2-exec-20261115`; origin = same) |
| Linearity / force | `b8e2e0ee` is an ancestor of `5c3ff87a` (1 commit); reflog shows ordinary sequential commits; origin tip equals local; **no force** |
| Post-run tree at both commits | `ec996594116b15c5a4e720c25e08542ebec0e04e` — **byte-identical**; `git diff b8e2e0ee 5c3ff87a -- …/postrun/` is empty |
| Tip-only content | `trks_stop/{NOTE.md,stop_trks_watch.sh,tasl2_readonly_inventory.sh}` and an 82-line round-11 review record appended to `B2_OCCUPANCY_LAUNCH_REVIEW_20261115.md`; no post-run byte changed |
| Review worktree | `5c3ff87a`; clean at review start. This review file is uncommitted and is the only file I created (a sibling's `B2_TRKS_STOP_UNITS_REVIEW_20261115.md` is also untracked and is not mine) |

File SHA-256 of the exact bytes reviewed (these match the hashes cited by the round-10/11 record):

| File | SHA-256 |
|---|---|
| `postrun/README.md` | `02987e921146b39767dd1d9a59cc7cd09374bc0c4c1f8818e94ae27f54540171` |
| `postrun/postrun_collect.sh` | `7c44dfebfbb14a28158b8f044b78e8f8eef5f74df69c9556bd9a8fc058a54d09` |
| `postrun/retire_marker.sh` | `4cfbded2733ce36c038c6698a8513290f8f7c0d7856f8aee8d3d693b4e2bdd03` |
| `postrun/publish_status_done.sh` | `8293635c5bdf416a87a3b7c3e8d464f5319c2b1551df6948be1f587e33db5987` |
| `postrun/stopped/stopped_run_collect.sh` | `579902067f1e0292aaa0c3a717b70c32f37e1298707b54b140f8b35f88ec9ef4` |
| `postrun/stopped/retire_marker_stopped.sh` | `6c1a14fe2910ccd62881f15a048b0958df52296133e06da9d478515b31edd5f2` |
| `postrun/stopped/publish_status_stopped.sh` | `ffc5d18c1f6c79b0c8f61d16304c64055ab2349bfdf7ed69598e0abeedb740c5` |

The round-11 claims are present in these bytes: B-10 `rows += int(pj.get('rows') or 0)`
(`postrun_collect.sh` L55); P-38 `sha256sum -c SHA256SUMS` before the STATUS append
(`publish_status_done.sh` L18); P-39 checked `find … | sort` pipelines and empty-list diagnostics
(`stopped_run_collect.sh` L20–23); P-37/P-40 README wording (no `absent.txt`; pre-created dir case).
All seven scripts pass `bash -n`; the Python heredocs (the invalid-trial aggregation, the stopped-state summary, and both STATUS appends) compile.

## 2. Host prerequisites (read-only, TASL-7)

| Check | Observed |
|---|---|
| `$RUN_DIR/b2.exit` | **absent** (runner still running; correct — the unit must not be used yet) |
| Runner | pid `1050028`, alive, `/home/dowling/exam-x/work/venv/bin/python -B -m r1.scripts.exam_runner b2 --config …/exam_b2_v2.json --out …/b2_8709_20261115_b2` |
| `batch_state.json` | `status=RUNNING`, `phase=b2`, `execution_label=EVIDENCE`, `completed=19` |
| `b2_manifests.json` | absent — expected: it is written by the **runner** at completion (`exam_runner._finish`, `write_json(runner.out/f'{phase}_manifests.json', …)`), and only **read** by the analysis (`b2_batch.verify_b2_batch` L158/L183). It is *not* produced by `r1.exam.analyze`; the collect's L39 post-analysis check is therefore satisfiable exactly when `b2.exit=0` |
| Marker | present, mode 600, owner dowling, nlink 1, dev `66306`, ino `56261620`, sha256 `4ecb2779bc30f40e3bdd1b10dd4365e7b5268d136fe0c146831050299c62726d`; `marker-receipt.json` matches (same dev/ino/sha, run_id/head correct) |
| Marker tool | `$PAPER/r1/scripts/b1_o2_marker.py` sha256 `0d04ca7e4c3f251adb6ea1a4a2eba6446c19a38ae585169fe0a156d392c06d4f` (= run HEAD bytes); `retire` present (`renameat2`, `--receipt`) |
| Staged checkout | `$PAPER` HEAD `8709dce7…`, `git status --porcelain` empty |
| Analysis prerequisites | venv `$PY` present (3.13.4); rule sha `53018aa7…16ad`; `b1_analysis` sha `07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc`; author note, registry, value grids, Stage A tables present; `author_gate`'s clean-checkout requirement is met |
| Watcher | pane pid `1388760`, `bash /home/dowling/r1_tracks/bin/trks-watch`, script sha `cf6884…`; on marker absence it logs `marker gone: resume by hand …` and does **not** auto-resume |
| Pause/retire ordering | `retire_marker.sh` does not consult or depend on the watcher; the watcher waits for marker absence and then only logs. No hidden watcher dependency in the unit |

A real completed root manifest (read-only) confirms the aggregation inputs: `candidate=gemma4_31b`,
`mode=off`, `proposal_journal` is a dict with `rows = 20` (**int**) and `rejected_by_check = {}`.
The B-10 fix and the B-9 keying by the manifest's `candidate`/`mode` are correct against the actual
schema.

## 3. Normal-completion path (`postrun_collect → retire_marker → publish_status_done`)

**Collect (L20–72).** Correct and fail-closed on the main hazards: refuses unless `b2.exit` is exactly
`0` (absent → empty → STOP); requires a non-empty `batch_state.json`; refuses a pre-existing
`analysis.json` or `POSTRUN_COLLECT_OK`; creates `$RUN_DIR/postrun` 0700 itself with an exclusive
`CREATED.txt` (plain-dir/non-symlink check); copies `batch_state.json`; runs the verified analysis with
`--batch/--config/--rule/--rule-sha256` (the CLI path that calls `b2_summary_verified` →
`verify_b2_batch`; stdout/stderr/rc captured) and STOPs unless rc 0; requires `b2_manifests.json`;
aggregates each root manifest's `proposal_journal.rejected_by_check` by that manifest's
`candidate`/`mode` (roots/journals/rows/checks recorded); writes `SHA256SUMS` and the exclusive
`POSTRUN_COLLECT_OK` with the four artifact hashes and `analysis_rc=0`. No deletion, batch read-only.

**Retire (L12–21).** Correct and fail-closed: `b2.exit`=0; non-empty `POSTRUN_COLLECT_OK` containing
`analysis_rc=0`; marker present; no existing receipt; no `exam_runner b2`; calls the reviewed primitive
with the create receipt; non-empty receipt; marker gone afterwards. The primitive re-reads the receipt,
verifies dev/ino/sha256 and moves the marker into `~/r1_locks/_to_delete` (a move, never a delete).

**Publish done — BLOCKING (B-11).** `publish_status_done.sh` cannot pass its own gates on either
machine:

- L14–L15 test `$RUN_DIR/b2.exit` and `$RUN_DIR/marker-retirement.json` **as local files**, where
  `RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2`. On the Mac — the only place
  the clean `mac-b1-20261107` checkout exists (`.claude-worktrees/b1-status-20261115`,
  HEAD `524f0a8a5e150f280fc50a5081f09901c495885a` = origin, clean) and the machine where the
  start-phase `publish_status.sh` explicitly runs ("Run on the Mac", reading host files via
  `ssh tasl7`) — `/home/dowling` **does not exist**, so `[ -s … ]` is false and the script STOPs at
  L14.
- On TASL-7 the host-path gates would pass, but L16–L18 `ssh -o BatchMode=yes tasl7 …` fails
  (`ssh: Could not resolve hostname tasl7: Temporary failure in name resolution`), and there is no
  `mac-b1-20261107` checkout on the host (a scan under `/home/dowling` found only the B1/B2 paper
  checkouts on detached HEADs and the `agent_paper_B` clones at `74a07907…` / `8237fd02…`).

So the normal chain can collect and retire but **cannot publish `Track X B2 done`**. The round-11
ACCEPTED record's claim that the done publication "checks `b2.exit`=0, the marker retirement" is true
of the source text but not executable from the machine that owns the status checkout. Required fix:
move the L14–L15 gates into the ssh block (read both files from the host in one `ssh` call, as
`publish_status.sh` L19–25 does for the marker receipt), and state in the README which machine runs
each step.

## 4. Stopped-run path (`stopped_run_collect → retire_marker_stopped → publish_status_stopped`)

**Collect (L12–38).** Correct: requires `b2.exit` present and ≠0; refuses an existing
`postrun_stopped` (no retry); creates it fresh 0700; preserves `b2.log` (hard STOP if it cannot),
`batch_state.json` (absence recorded), the `campaign_manifest.json` and `b1_proposals.jsonl` path lists
(pipelines checked under `pipefail`, empty lists recorded as `*.empty.txt`), and `STOPPED_STATE.json`;
writes `STOPPED_COLLECT_OK` only after all of that. No analysis, no deletion.

**Retire (L11–19).** Correct: gated on the stopped collection, marker present, no existing receipt, no
runner; same reviewed primitive and receipt; verifies the marker is gone.

**Publish stopped — BLOCKING (B-12).** `publish_status_stopped.sh` contains **no ssh** and gates on
`$RUN_DIR/postrun_stopped/STOPPED_COLLECT_OK` and `$RUN_DIR/marker-retirement-stopped.json` as local
paths (L12–L13). From the Mac those paths do not exist; from the host there is no `mac-b1-20261107`
checkout to pass L9–L11. The stopped publication therefore cannot run as staged. Required fix: use the
same ssh-based host gating as the (fixed) done script, and run both publications from the Mac.

## 5. Findings

### BLOCKING

**B-11 — `publish_status_done.sh` mixes local and remote path contexts; the normal path cannot publish
`B2 done`.** L14–L15 read host files locally; L16–L18 ssh to `tasl7`. Fails at L14 on the Mac
(`/home/dowling` absent) and at L16 on the host (`ssh tasl7` unresolvable, no status checkout).
*Fix:* move the `b2.exit` and `marker-retirement.json` checks into the ssh block (or one combined
`ssh` test), exactly as the start-phase `publish_status.sh` reads the host marker receipt; record the
execution machine in the README.

**B-12 — `publish_status_stopped.sh` cannot be executed from the machine that owns the status
checkout.** No ssh; host-path gates; no host `mac-b1-20261107` checkout. *Fix:* same as B-11.

### MAJOR

**P-42 — `POSTRUN_COLLECT_OK` is not written atomically, and `retire_marker.sh` accepts a partial
receipt.** `postrun_collect.sh` L67–72 creates the file with `{ … } > "$PO/POSTRUN_COLLECT_OK"` before
the block runs. If a copy or hash inside the block fails (e.g. `cp -p` L33/L40, or the `sha256sum` at
L71), the block exits non-zero and the script STOPs, but a **partial file containing
`postrun_collect_ok_utc=…` and `analysis_rc=0`** remains. `retire_marker.sh` L13 tests only `-s` +
`grep -q "analysis_rc=0"`, so it would pass and retire the marker after an incomplete collection
(missing `batch_state.json`/`b2_manifests.json`/artifact hash lines). I reproduced the shell semantics
generically: a `{ … } > OK` group that fails part-way leaves `analysis_rc=0` in a non-empty `OK`, and
the `-s`+grep gate passes. STATUS done remains protected (L16 requires all four artifacts), but marker
retirement is not. Related weaknesses in the same block: `cp -p` L33/L40 unguarded; `sha256sum "$PO"/*`
L65 has `2>/dev/null || true`; `analysis.rc` L37 is an unguarded `>` write under the `set -C` from L27.
*Fix:* build the receipt content first (`out=$(…) || stop`) or write to a temp name and `mv` it into
place (a move, not a delete); require the four hash lines in the retire gate and/or re-run
`sha256sum -c` there; drop the `|| true` on `SHA256SUMS`.

**P-44 — the publish scripts do not bind `$RUN_ID`/`$HEAD` to the run.** `publish_status_done.sh` and
`publish_status_stopped.sh` accept arbitrary argv 2/3 and write them into the STATUS heading and commit
message. The start-phase `publish_status.sh` verified `run_id`/`head` against the host marker receipt
(L19–25); the done/stopped scripts dropped that check. A wrong Run/HEAD can be published even though
`RUN_DIR` is hardcoded to `8709_20261115_b2`. *Fix:* assert `$RUN_ID = 8709_20261115_b2` and
`$HEAD = 8709dce7…`, and/or verify against the marker receipt (as the start script does).

### MINOR

- **P-45 — publication receipts are weaker than the start-phase receipt.** No marker-receipt SHA-256
  or postrun artifact SHA-256s are recorded; `publish_status_done.sh` L34 writes the receipt after the
  push without `|| stop` and without `set -C` (the start script had both). A failed post-push write
  leaves the publication without a receipt that cannot be regenerated (the checkout has advanced).
- **P-46 — failed commit/push recovery is undocumented.** A failed `git commit` leaves the status
  checkout dirty (and the L10 clean guard then blocks a retry); a failed push leaves a local commit so
  L13 (`LOCAL = REMOTE`) blocks a retry. The README documents recovery only for the collect/analysis
  STOP. *Fix:* document the exact recovery (restore the checkout / re-push the existing commit) with
  no force.
- **P-47 — pre-created `postrun` dir is not required to be empty.** L24 accepts a pre-existing plain
  dir; only `analysis.json`/`POSTRUN_COLLECT_OK`/`CREATED.txt` are checked. A pre-created dir
  containing a stale `analysis.rc` makes L37's noclobber write fail silently (no `|| stop`), yielding a
  collection with no `analysis.rc`; a stale `analysis.err` makes the analysis redirect fail with a
  misleading "analysis failed" STOP. *Fix:* require the pre-created dir to be empty (or only the
  reviewed marker files), and guard L37.
- **P-48 — README/script mismatches.** (a) §Recovery says the re-run "records the reason in the new
  attempt" (L35–36) — nothing records a reason; `CREATED.txt` records only the UTC. (b) The README
  never states which machine runs `postrun_collect`/`retire_marker` (host) versus
  `publish_status_*` (Mac) — the gap that produced B-11/B-12. (c) Stopped-path recovery (a failed
  `postrun_stopped` must be moved aside before the stopped script will re-run) is not documented.
  (d) The scope line says the unit hands the report to independent review (STOP 6), while L19–20 say
  the report/review is a separate unit. (e) The stopped empty-list diagnostics
  (`manifests.empty.txt`/`journals.empty.txt`) are not mentioned.
- **P-49 — hardcoded heading date.** The `## 2026-11-15 — Track X B2 done/stopped` heading is a
  literal; if publication happens on a later UTC date, the heading disagrees with the hand-off's
  `## <date>`. Use the run date constant or `date -u` consistently.
- **P-50 — stopped evidence is not integrity-checked.** `STOPPED_COLLECT_OK` contains no hashes and
  `publish_status_stopped.sh` never verifies `SHA256SUMS`; post-collection corruption of the stopped
  evidence would pass. Optional hardening (the stopped path is about preservation, not verification).
- **NIT.** `retire_marker*.sh` `pgrep -f "python.*-B -m r1\.scripts\.exam_runner b2 "` is not anchored
  and can match an operator's own `pgrep -af 'python.*-B -m r1.scripts.exam_runner b2'` (it fails
  closed but would stop a legitimate retirement). The `cd` before `sha256sum -c SHA256SUMS` is
  redundant with the absolute-path lines. `b2.exit` is checked by content only (no SHA/owner check);
  fine for the current trusted-run-dir model.

## 6. Could a partial/failed analysis still lead to retirement or `B2 done`?

- **Analysis rc ≠ 0:** `postrun_collect.sh` L38 STOPs before `SHA256SUMS`/`POSTRUN_COLLECT_OK`; the
  retire and done gates then stop. Safe.
- **Analysis rc 0 but aggregation fails (L42):** STOP before the receipt. Safe.
- **Analysis rc 0 then an I/O failure inside the receipt block (L67–72):** the partial receipt passes
  the retire gate (**P-42**), so the marker can be retired after an incomplete collection; the done
  publication still stops because L16 requires all four artifacts. This is the only
  partial-analysis→retirement path found, and it requires an I/O error at that point, but the
  fail-closed guarantee is not met as written.
- **Corrupted artifact after collection:** the retire gate does not re-verify `SHA256SUMS` (P-42
  family); the done script does (P-38 fix). STATUS done is safe; retirement is not.
- **Before `b2.exit` appears:** collect (L20), retire (L12) and the stopped collect (L12) all STOP;
  no premature action. **After a stopped run:** the normal scripts STOP on the exit-0 gate; the
  stopped unit is separate. **No deletion:** there is no `rm`/unlink in the unit; the retire primitive
  moves the marker into `_to_delete` and preserves it.

## 7. Verdicts

- **Normal-completion path: NOT ACCEPTED.** `postrun_collect.sh` and `retire_marker.sh` are executable
  and fail-closed on the host (with the P-42 atomicity caveat), but the final publication
  `publish_status_done.sh` cannot pass on either machine (B-11), so the path cannot reach
  `Track X B2 done`. Do not run the normal unit after `b2.exit` appears until B-11 is fixed.
- **Stopped-run path: NOT ACCEPTED as a whole.** The stopped collection and retirement are executable
  on the host as written; the stopped publication cannot run from the Mac or the host (B-12).

Verdict: not accepted

Acceptance, if later given, would apply to the post-run unit only — not to execution authorisation,
the B2 report/STOP 6, the Track S STOP-4 unit, or any host action. No host write, no unit execution
and no git write were performed for this review.

---

## 8. Round 2 — re-check of `83b9c80b` (15 November 2026, ≈20:54–21:05 CET)

**Scope and method.** Round 1 (above) reviewed `5c3ff87a` and found B-11, B-12, P-42, P-44 blocking/major
plus P-45–P-50 and a NIT. This round re-checks **only whether those findings are fixed**, from the bytes of
`83b9c80b` read with `git show` (the review worktree stayed detached at `5c3ff87a`; no checkout/reset, no
host write, no unit execution, no git write, no signal). The round-1 file's SHA-256 before this addendum was
`2cb44815476e925bae73e4511fe1cfab830c29ab6f27b78c779d43d76befce8d`, matching the round-2 request.

### 8.1 Provenance — one caveat: origin advanced during this review

| Item | Observed |
|---|---|
| Reviewed commit | `83b9c80bc648434e33d7b67c4ac8d6579f19fd60` (`fix(r1): B2 post-run unit round 12 …`); parent `5c3ff87a5bb18d069cc21dc72c8d23b0deafb719` — a direct child, no intermediate commit |
| Changed paths | exactly 10: the seven `postrun/` files below + `trks_stop/{NOTE.md,stop_trks_watch.sh,tasl2_readonly_inventory.sh}`; no other path, no host artifact |
| Origin tip at request time | `83b9c80b` (as stated in the round-2 request) |
| Origin tip now | **`d022bf64aa533af10267f4a7994483ccdf32d21e`** — it advanced by a fast-forward push at 20:55:23 CET, ≈40 s after this review began. Remote reflog (`.git/logs/refs/remotes/origin/ops-b2-exec-20261115`): `5c3ff87a → 83b9c80b` (`update by push`, epoch 1794772476) then `83b9c80b → d022bf64` (`update by push`, epoch 1794772523). Both old→new entries are fast-forwards; **no force** |
| What `d022bf64` changes | only `trks_stop/NOTE.md` (+10 lines) and a new `trks_stop/watcher_marker_gone_analysis.md` (42 lines). `git diff 83b9c80b d022bf64 -- …/postrun/` is empty |
| Postrun tree | `0f3fe46c228935a5659a188a9cc7d55fc44c14cd` at **both** `83b9c80b` and `d022bf64` (round-11 tree was `ec996594116b15c5a4e720c25e08542ebec0e04e`). The fix bytes reviewed here are therefore on origin; the reviewed commit is an ancestor of the tip |
| Host runs | none: `b2.exit` absent, no `postrun/` or `postrun_stopped/`, `marker-retirement*.json` absent, runner `RUNNING` 19/24, `b2.log` mtime 08:45 |
| Worktree | still detached at `5c3ff87a`; only the two untracked review files; this review file is the only file this round wrote |

File SHA-256 of the exact bytes reviewed (identical at `83b9c80b` and at the current origin tip `d022bf64`):

| File | SHA-256 |
|---|---|
| `postrun/README.md` | `bc28c7a1c6c78e3a9027385089cc4354091b4f455af79421df885707cd9e9733` |
| `postrun/postrun_collect.sh` | `b0c24212f80852bec5ebebbb6022918ea6d5462647bf5cd50cfc7b5160877533` |
| `postrun/retire_marker.sh` | `52941e5bb2277adf54e2a36259d4ad56271a93a2413e4425fe8372fec700689b` |
| `postrun/publish_status_done.sh` | `eadd1988b9fd8d0a2209cfce67a757da94afa852679862c57c0d6eabb56bcc99` |
| `postrun/stopped/stopped_run_collect.sh` | `62460fda7b6ad2f78e80a0c693bc9efe3f6fbf7a86696a99c7e55a144dc20358` |
| `postrun/stopped/retire_marker_stopped.sh` | `bd9f9d3e89e7ee86b41f7ee8cad4ebf5326e709ca238db7ac360a11edfaf6ec3` |
| `postrun/stopped/publish_status_stopped.sh` | `8e4d5a6d2bb0fda191bed5366a184ad3fee4fcdb2fb5c06831dd2c37195ac767` |

All six shell scripts pass `bash -n`; every Python heredoc (collect aggregation, stopped summary, the four
`run_id`/`head` binders, the two STATUS append bodies) compiles.

### 8.2 B-11 / B-12 — fixed

**`publish_status_done.sh` now runs on the Mac and reads every host gate over ssh.** L2–L4 say so; L10
defines `SSH="ssh -o BatchMode=yes -o ConnectTimeout=20 tasl7"`; L16–L30 contain **all** the host gates, and
every `$RUN_DIR` use after the L9 definition is inside a `$SSH` argument (line-by-line check: L17, L18,
L20, L26, L27, L28, L29, L30). There is **no remaining local host-path gate**:

1. `b2.exit` exists and is exactly `0` (L17);
2. `marker-retirement.json` is non-empty (L18);
3. the caller's `RUN_ID`/`HEAD` are bound to the run's own `marker-receipt.json` (L20–L25);
4. all five post-run files are non-empty (L26);
5. `analysis_rc=0` exact (L27);
6. exactly four artifact-hash lines (L28);
7. each of the four artifact names has its own hash line (L29);
8. `sha256sum -c SHA256SUMS` (L30).

**`publish_status_stopped.sh` has the same structure** (L9 `SSH`; L15–L23 the ssh gates; no local
`$RUN_DIR`; the stopped publish now also verifies `SHA256SUMS`, L23). The stopped script's commit
(L32–L33) also gained `|| stop "commit failed"`.

**The ssh forms are correct, not just syntactically plausible.** I expanded the exact double-quoted
arguments with a printer in place of `ssh` and read back the remote strings, then ran them read-only on
TASL-7:

- `test -s '…/b2.exit' && [ "$(cat '…/b2.exit')" = 0 ]` — remote `$(…)` is not expanded locally; rc=1 now
  because `b2.exit` is legitimately absent (fail-closed);
- `python3 - '…/marker-receipt.json' '8709_20261115_b2' '8709dce7…' <<'PY' … PY` — the here-doc survives
  the ssh transport (the remote bash 5.1.16 accepts the `PY` delimiter at end-of-string), rc=0 with the real
  receipt; with a wrong HEAD it prints `STOP: marker receipt run_id/head mismatch` and returns rc=1;
- `test "$(grep -c '^[0-9a-f]\{64\}  ' '…/POSTRUN_COLLECT_OK')" -eq 4` — the local `\\{` becomes the GNU
  `\{64\}` BRE on the host; tested rc=0 with four synthetic hash lines;
- `for a in analysis.json …; do grep -Eq '^[0-9a-f]{64}  '$a'$' … || exit 1; done` — tested rc=0, and rc=1
  with a wrong line;
- an unreachable alias returns 255, and each `$SSH …` is followed by `|| stop`; with `set -eu` the
  `LOCAL=$(…)`/`REMOTE=$(…)` probes also abort on git/network failure. The scripts therefore fail closed if
  ssh or the host is unavailable.

`README.md` L16 ("**Machine contexts**") now states explicitly: collect and both retire scripts run on
TASL-7; both publish scripts run **on the Mac**, reading every host gate over `ssh tasl7`, failing closed if
the host is unreachable, and writing nothing on the host. L14 repeats "**run on the Mac**" on the done row.

### 8.3 P-42 — fixed (atomic receipts, and the retire gates now match the receipt)

**`postrun_collect.sh` L76–L89** builds `POSTRUN_COLLECT_OK` in `POSTRUN_COLLECT_OK.tmp` (`{ … } > "$TMP" ||
stop`), checks `grep -c '^[0-9a-f]\{64\}  '` equals 4, checks `^analysis_rc=0$`, and only then
`mv "$TMP" "$OK"` (same-directory atomic rename). A failure at any earlier point (analysis, aggregation,
artifact checks, `SHA256SUMS` write/verify, temp write, line checks) leaves **no** `POSTRUN_COLLECT_OK`; a
partial temp file is not accepted by anything. The hash write is no longer silenced: L74 writes a fixed
four-file list without `2>/dev/null || true`, and L75 re-verifies it. L71–L73 require all four artifacts to
be non-empty before hashing.

**`retire_marker.sh` L13–L25** now requires: exact `analysis_rc=0`; exactly four hash lines; each of the four
artifact names present with a 64-hex digest; `sha256sum -c SHA256SUMS` re-verified; and the marker receipt's
`run_id`/`head` bound, before the marker is touched. The round-1 partial-receipt fail-open is gone: a
receipt truncated to `postrun_collect_ok_utc=…` + `analysis_rc=0` is rejected by the four-line count; a
receipt with three hash lines is rejected; a corrupted artifact is rejected by `sha256sum -c`.

**Stopped path on the same pattern:** `stopped_run_collect.sh` L37–L51 builds the artifact list
(`STOPPED.txt`, `STOPPED_STATE.json`, and `batch_state.json` or `batch_state.absent.txt`), writes and
verifies `SHA256SUMS` unsilenced, then builds `STOPPED_COLLECT_OK.tmp`, checks at least two hash lines, and
renames atomically. `retire_marker_stopped.sh` L11–L18 verifies `SHA256SUMS` and binds `run_id`/`head`
before retiring. (The stopped `-ge 2` check is lenient, but the block is still fail-closed under
`pipefail`, and both the retire and the stopped publish verify `SHA256SUMS` over the full artifact list.)

I exercised the receipt parsing in a throwaway local fixture (removed immediately; nothing created on
TASL-7): four hash lines → count 4, all names found, `sha256sum -c` passes; one corrupted artifact →
`sha256sum -c` fails; three hash lines → rejected; zero hash lines with `analysis_rc=0` → rejected; the
`sed 's# .*/# #'` is a no-op for the bare filenames used here.

### 8.4 P-44 — fixed (done/stopped publish are bound to run/head)

Both publish scripts now bind the caller's `$RUN_ID`/`$HEAD` to the host `marker-receipt.json` over ssh
(done L20–L25; stopped L17–L22): a mismatch exits non-zero and the script STOPs before appending anything.
`RUN_DIR` is hardcoded to `8709_20261115_b2`, so a caller cannot point the publication at another run. The
real-receipt test returned 0; a wrong HEAD returned 1. The same binding was added to both retire scripts
(L20–L25 / L13–L18), so retirement is also run-bound.

### 8.5 P-45 … P-50 and the NIT — dispositions

| Finding | State in `83b9c80b` | Disposition |
|---|---|---|
| **P-45** publication receipt weaker than start phase | Partly. Done/stopped receipts still record only branch/commit/run_id/head/published_utc (no marker or artifact SHA-256s), and there is no `set -C`; but `set -eu` is on and `[ ! -e "$OUT" ]` guards the name. A post-push receipt-write failure leaves no receipt, though the publication itself is already remote-verified and recoverable from the commit | **Non-blocking hardening.** No fail-open; the start-phase parity is not required for correctness |
| **P-46** failed commit/push recovery undocumented | Partly. README L43–L46 adds a recovery paragraph. However, after a **successful commit but failed push**, "re-run the publication step" cannot work: L14–L15 see `LOCAL ≠ REMOTE` and STOP at "status branch advanced". The correct recovery is to push the existing commit (`git -C "$SC" push origin HEAD:refs/heads/mac-b1-20261107`) and verify, not to re-run the script. The failed-commit case (revert the dirty STATUS change, then re-run) is covered | **Non-blocking documentary.** The script fails closed and never force-pushes; the operator can recover with normal git. Worth correcting in the README before use |
| **P-47** pre-created `postrun` dir not required empty | **Fixed.** L24–L29 require a pre-existing `postrun` to be a plain non-symlink **empty** dir; a stale `analysis.rc`/`analysis.err` can no longer exist. L42's `> analysis.rc` is still unguarded, but the fresh-dir requirement plus `set -C` make a silent stale write impossible; `analysis.rc` is diagnostic, not a gate | **Resolved** |
| **P-48** README/script mismatches | Partly. (b) Machine contexts are fixed (L16). (a) "records the reason in the new attempt" is still not implemented — `CREATED.txt` records only the UTC; (c) stopped-path recovery (move a failed `postrun_stopped` aside before the no-retry script will re-run) is still not documented; (d) the scope line still says the report/review is handed over here while L21–L22 call it a separate unit; (e) the stopped `*.empty.txt` diagnostics are still unmentioned | **Non-blocking documentary** (the unit's behaviour is correct; the text is incomplete) |
| **P-49** hardcoded heading date | **Script fixed.** `DAY=$(date -u +%F)` (L7) is used in the heading (L34), so the heading follows the publication date. README L14/L30 still show the literal `## 2026-11-15 — …` for both done and stopped | **Resolved in the script; README literal is documentary** (if publication slips past UTC midnight the README's example heading differs from the script's real one) |
| **P-50** stopped evidence not integrity-checked | **Fixed.** The stopped receipt now lists hash lines (L46–L50), collection verifies them (L41), and the stopped publish verifies `sha256sum -c SHA256SUMS` (L23); the stopped retire verifies too (L12) | **Resolved** |
| **NIT** unanchored `pgrep` | Remains: `pgrep -f "python.*-B -m r1\.scripts\.exam_runner b2 "` can still match an operator's monitoring command. It fails closed (stops a legitimate retirement) and cannot cause a false retirement | **Non-blocking, cosmetic** |

### 8.6 New-bug scan of the fixes

- No `diff <(…)`, `eval`, `source`, or process substitution was introduced; the ssh quoting is correct (the
  expanded remote strings above), including the remote here-doc and the `$a` loop variable.
- `grep -c` is used exactly where the receipt has one line per artifact; `\{64\}` under BRE and `{64}` under
  ERE were both exercised on the host. The `sed 's# .*/# #'` is a harmless no-op for bare names.
- The pre-created-dir emptiness check, the dynamic date, `set -C`, `set -o pipefail`, and the `umask 077`
  are consistent; there is no `rm`/`unlink`/`rmdir` anywhere in the unit (verified by grep).
- The `.tmp` receipt can be left behind if a line check fails, but it is not the final receipt; retire and
  publish read only `POSTRUN_COLLECT_OK`/`STOPPED_COLLECT_OK`.
- `analysis.rc` is not in `SHA256SUMS` (diagnostic only); no gate depends on it. The stopped `-ge 2` count is
  lenient but the block fails closed under `pipefail`, and the downstream SHA-256 check covers all artifacts.
- The retirement receipt is the primitive's single success `print`; a failed retire leaves a 0-byte file
  (rejected by the publish `test -s`), and `retire_marker.sh` itself verifies the marker is gone. The publish
  done gate checks the receipt, not marker absence, but the trusted-run-dir model and the 0-byte behaviour
  make this adequate.

### 8.7 Invariants re-run (read-only) and end-to-end executability

| Check | Observed at 20:54–21:00 CET |
|---|---|
| `$RUN_DIR/b2.exit` | **absent** — correct, the runner has not finished |
| Runner | pid `1050028`, alive, `python -B -m r1.scripts.exam_runner b2 --config …/exam_b2_v2.json --out …/b2_8709_20261115_b2` |
| `batch_state.json` | `status=RUNNING`, `phase=b2`, `execution_label=EVIDENCE`, `completed=19` (12 off-mode + 7 on-mode) |
| `b2_manifests.json` | absent — expected; `exam_runner` writes `{phase}_manifests.json` in `_finish` (L484), so the collect's post-analysis requirement is satisfiable at completion |
| Marker | present; mode 600, owner dowling, nlink 1, dev `66306`, ino `56261620`, sha256 `4ecb2779bc30f40e3bdd1b10dd4365e7b5268d136fe0c146831050299c62726d`; `marker-receipt.json` matches (dev/ino/sha, `run_id=8709_20261115_b2`, `head=8709dce7…`) |
| Prerequisites | paper checkout HEAD `8709dce7…`, clean; venv Python 3.13.4; rule sha `53018aa7…16ad`; config `exam_b2_v2.json` present; `r1.exam.analyze`/`b2_batch` present; marker tool sha `0d04ca7e…`; watcher `1388760` alive |
| Post-run state | no `postrun/`, no `postrun_stopped/`, no `marker-retirement*.json`; `b2.log` 18 bytes at 08:45 — no host run attempted |
| Status checkout | `.claude-worktrees/b1-status-20261115` on `mac-b1-20261107`, HEAD `524f0a8a5e150f280fc50a5081f09901c495885a` = `origin/mac-b1-20261107`, `git status --porcelain` empty, `docs/r1/STATUS.md` present, `Track X B2 done` heading absent |
| ssh alias | `ssh -G tasl7` → host `tasl7`, user `dowling`, hostname `100.106.74.51`, port 22, key `~/.ssh/id_ed25519`; the scripts use exactly `tasl7` |

**Round-10/11 content is still present at the new tip.** B-8 (the collect creates its own `postrun` dir,
L24–L29), B-9/B-10 (the invalid-trial aggregation keyed by each manifest's `candidate`/`mode`, with
`rows += int(pj.get('rows') or 0)`, L47–L69), P-31 (collect-ok gating), P-30 (the separate stopped unit),
P-38 (`sha256sum -c` before the STATUS append, done L30), and P-39 (the checked
`find … -printf … | sort` stopped lists, L20–L23) are all unchanged in these bytes. The collect gates above
are unchanged; nothing acts before `b2.exit`, and the stopped path remains a separate directory and script
set (the normal scripts stop on a non-zero or absent exit).

**Normal completion is now executable end-to-end on the intended machines.** The already-running
`receipt.sh` writes `b2.exit` when the runner exits (it is the wrapper that launched `start.sh`, and its
`printf '%s\n' "$rc" > "$RUN_DIR/b2.exit"` is the only writer). Then on TASL-7:
`postrun/postrun_collect.sh` → `postrun/retire_marker.sh` (both host-path scripts, fail-closed); then on the
Mac: `postrun/publish_status_done.sh .claude-worktrees/b1-status-20261115 8709_20261115_b2
8709dce792d45bbb5c05d9f7d239e19454efbb15`. The Mac script's L12–L15 preflight passes on that checkout now
(clean, branch, HEAD = origin), its host gates are readable over `ssh tasl7`, and the STATUS append target
exists and does not yet contain the heading. The stopped path is separate: `postrun_stopped/…` on the host,
`publish_status_stopped.sh` on the Mac. Nothing was executed for this review (the runner is still running;
a real collect would be premature).

### 8.8 Residual, non-blocking risks

1. **Origin advanced during the review** to `d022bf64` (child of `83b9c80b`, trks_stop-only, additive). The
   postrun tree is byte-identical, so this does not change the reviewed unit; any record should cite
   `83b9c80b` for the fix and note that the current tip is `d022bf64`. Do not describe the tip as
   `83b9c80b` any more.
2. **P-46 recovery wording** (above): after a successful commit + failed push, re-running the script stops
   at "status branch advanced"; the correct action is to push the existing commit and verify. Documentary.
3. **P-45 receipt strength**: no marker/artifact SHA-256s and no `set -C`; `set -eu` covers the common
   failures. Hardening only.
4. **P-48 documentary residuals**: the "records the reason" claim, stopped-path recovery, the scope/separate
   unit wording, and the `*.empty.txt` diagnostics.
5. **P-49 README literal date** vs the script's `date -u +%F` heading.
6. **NIT unanchored `pgrep`** (fails closed).
7. The publish done gate checks the retirement **receipt** rather than marker absence; the primitive prints
   the receipt once on success and a failed retire leaves a 0-byte file rejected by `test -s`, so this is
   adequate for the trusted-run-dir model.
8. The stopped collect records a failed `cp` of `batch_state.json` as `batch_state.absent.txt`; the original
   remains on the host, so no evidence is lost, but the marker can mean "copy failed" rather than "absent"
   (pre-existing, not introduced here).
9. `analysis.rc` is not hashed; a write failure there would not stop the collect (fresh dir + `set -C` make
   it unlikely; the file is diagnostic).

**Verdict for the round-12 bytes:** the two BLOCKING findings (B-11, B-12) and the two MAJOR findings
(P-42, P-44) are resolved in the reviewed bytes, and the remaining items are documentary/hardening only.

Acceptance applies to the post-run unit's postrun bytes of `83b9c80b` (byte-identical at the current origin
tip `d022bf64`) only — not to execution authorisation, the B2 report/STOP 6, the Track S STOP-4 unit, or
any host action. No host write, no unit execution and no git write were performed for this round; only this
review file was written.

Verdict: accepted
