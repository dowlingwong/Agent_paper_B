# Final precheck review — B1 `_d` launch (run `7912_20261113_d`, 13 Nov 2026)

**Reviewer.** Fresh, independent; I did not write the unit and took no part in rounds 1–3. Narrow confirmation of the `_d` launch precheck only, before launch. Read-only on TASL-7 (`ls`, `stat`, `cat`, `sha256sum`, `git rev-parse/status`, `tmux`, `ps`, `nvidia-smi`, `flock -n`, and one read-only execution of the precheck itself); no writes, signals, marker/STOP touch, deletion, or server/tmux start, and `launch.sh`/`launch_start.sh` were not run. I wrote only under `/Users/wongdowling/Documents/agent_sys_paper/` and `/private/tmp`; nothing under `/Users/wongdowling/Documents/agent_paper_B`. Review window: Mac `2026-11-13T14:49–15:02+01:00`; `tasl7` UTC `13:49–14:02Z`.

## 1. Final artifact

`/tmp/b1_handover_d_7912_20261113_d/launch_precheck.sh`: 3375 B, `-rwx------`, mtime `2026-11-13T14:48:54+01:00`, **sha256 `89385c41d17e17682540d040ebfd29f9a86ee1d5db4e50094b38095a60609820`**, matches the operator value. The other eight files are byte-identical to the round-3 table:

| file | sha256 |
|---|---|
| `handover_pre.sh` | `7ec04c72722805418f08a16305d41e9866e43514730556fb361f6b70ca815994` |
| `handover_run.sh` | `6d1da9443ccc42a3c6a90d06d33278d4a24541a26c1b1bc0865dab00174dc89b` |
| `status_publish.sh` | `582adb3ae585e7d2910ff906a317014012a99a64569e7e978af59411af5e8949` |
| `launch.sh` | `1ade789ddc3e727c3974a21fb657756702d67f3c95dd9d174e20d30bfa6c24ce` |
| `launch_start.sh` | `10f9be100aa57f27b7f3a4b19a00f5acb0f8979b75c48dfba724121caa3236c9` |
| `start.sh` | `4a545a756820df3d73c03aaf3557df18e14cfdba6bccefb96274ff087bb9eb5f` |
| `receipt.sh` | `2e6ad2abce0027699c61f0461a37122742a521b08370d2993921c16c0130c94a` |
| `PLAN.md` | `72f3ec714770d277b6a97e61e9ca9958066502a16f3643af3447919a0c56c48e` |

## 2. Delta vs round 3 (`3f828051…`)

The round-3 bytes are **not retained** anywhere I can search (`/private/tmp` recursive, `agent_sys_paper`, `agent_paper_B`, `~/.Trash`, home tree); the prior rounds had the same limitation. A byte-exact `diff` is therefore not reproducible, and I say so rather than claim it. What is verified:

- **(a) Note check replaced.** The final `:45–49` checks content: `NOTE=$RUN_DIR/marker-retirement.note`, `[ -f ]`, `grep -q 'source_receipt=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c/marker-receipt.json'`, `grep -q 'source_receipt_sha256=e0da112f…'`, echo `PREDECESSOR_NOTE_OK`. There is no fixed-sha assert. The rejected round-3 assertion could never pass: it compared the `_d` note (437 B, `b7d91e24…`) to the `_c` `marker-retirement_stop.note` (182 B, `4b86ba34…`). The 14:48:13 capture `/private/tmp/paper-b-b1-launch-capture-20261113.nWfxSdNl/launch.log` records exactly that failure (`AssertionError: predecessor note re-hash`, stdin line 14).
- **(b) Stray `PY` removed.** The file has exactly two heredoc openers (`:21`, `:32`) and two terminators (`:30`, `:44`); the follow-up's extra terminator is absent.
- **Nothing else.** The other eight artifacts are byte-identical to the round-3 hash table. Line-by-line read of the final file shows no third edit region: marker block `:21–30`, session `:31`, record block `:32–44`, note `:45–49`, pass `:50` — all consistent with the round-3 description; no new command, path, or check appears. Residual: without the round-3 bytes, "only (a) and (b)" rests on the exact final hash, the 8/9 byte-identical companions, the removed-block evidence, and this read, not on a byte diff.

## 3. Syntax and safety

`bash -n` passes. The precheck is read-only until the pass: the only redirection is `2>/dev/null` at `:31`; `git` is called with `--no-optional-locks`; there is no `rm`/`mv`/`unlink`/`truncate`/`shred`/`find -delete`/`git clean|reset`/`--force`/`dd`/`chmod`/`mkdir`/`tee`, and no write path. `umask 077` is process-local. A live execution through `ssh tasl7 'bash -s' < launch_precheck.sh` (read-only) printed `MARKER_RECEIPT_OK` / `PREDECESSOR_RECORD_OK` / `PREDECESSOR_NOTE_OK` / `LAUNCH_PRECHECK_PASS`, rc 0, in two runs.

## 4. Live read-only state (TASL-7, 13:49–14:02Z)

- Marker `~/r1_locks/trackx_evidence.active` present: dev `66306`, ino `56261619`, 82 B, sha `60cd40fba5000330c6155859b861594bf4e4902e684f3efc4e6b5e32a9ddca7b`, content `{"head":"7912b7ff…","run_id":"7912_20261113_d"}`; matches `RUN_DIR/marker-receipt.json`. `trackp` and drill markers absent.
- No `b1_7912_20261113_d` tmux session (`tmux ls` = only `trks_watch`). The paused `b1_6835_20261108_a` server lives on its private socket `…/b1_handover_6835_20261108_a/tmux.sock`; unrelated.
- `BATCH /home/dowling/exam-x/work/b1_7912_20261113_d` absent; no `b1.exit`, `b1.log`, `start.sh`, or `receipt.sh` in `RUN_DIR` (launch has not run).
- Lease free (`flock -n ~/r1_locks/gpu0.lock`); GPU `NVIDIA GeForce RTX 4090`, 236 MiB used, 0 % util; no compute/owned processes beyond the watcher (host services only).
- Staged checkout `…/b1_paper_final_7912b7ff…/paper`: HEAD `7912b7fffb4c1adeb39688bdb3852a919bdc71c8`, `status --porcelain -uall` empty (0 lines).
- `RUN_DIR` `/home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d` (0700) holds `marker-receipt.json` (`a28f0f78…`), `marker-retirement.json` (`f3082aa7…`), `marker-retirement.note` (`b7d91e24…`), `status-receipt.md` (`c81e6db9…`, heading `## 2026-11-13 — Track X B1 running`), `prechecks.log` (`fce6a3b4…`), both inventory pairs, and `handover-run.txt` (`905f111d…`, `SSH_EXIT=0`).
- Paused scenes untouched: `_c` `…/b1_handover_4b31_20261112_c` intact (creation receipt `e0da112f…`, `marker-retirement_stop.json` `2bfc6542…`, `_stop.note` `4b86ba34…`, rc `0`, err empty); `_b` dir mtime 11 Nov; `b1_6835_20261108_a` batch mtime 7 Nov. Track S: two manifests (inos `57037945`/`57039147`, sizes 4180/5340) unchanged, two STOPs (inos `57048847`/`57048195`, 0 B, sha `e3b0c442…` each). STOP mtimes moved to `…655.15` when the watcher saw the `_d` marker at 13:47:35Z — mtime-only, explicitly allowed; content and identities unchanged.
- STATUS checkout `/tmp/pb_status`: branch `mac-b1-20261107`, HEAD `6d6e8bba9336a161b8ddf5c5a22eadbd825669d2` ("Publish B1 handover running status"), clean. Gate/preflight for `7912b7ff…`: `gate.exit=0` (`GATE_PASS`), `preflight.exit=0` (`PREFLIGHT_PASS: owned server exited and own lease descriptor closed`).

## 5. Next action

`bash /tmp/b1_handover_d_7912_20261113_d/launch.sh`. That script runs this precheck first (stdin over ssh), uploads `start.sh`/`receipt.sh` with `set -C` (no overwrite), runs `launch_start.sh` (re-asserts SHAs, batch/session absence), starts tmux `b1_7912_20261113_d` via `receipt.sh`, and asserts a live session at 8 s and 15 s before printing `LAUNCHED`. That matches the stated next action.

## Residual notes (non-blocking)

- Round-3 bytes unavailable, so the "only (a) and (b)" delta is evidenced as in §2, not byte-diffed. The other eight files are pinned byte-exactly.
- `launch_precheck.sh:45–49` validates the note's two content lines but not the note file's own sha; the enforced predecessor pin remains the retirement record (JSON) plus `handover_pre`'s on-disk `_c` receipt checks. A note that keeps those two lines but differs elsewhere would pass — wording/defence-in-depth only.
- The 14:48:13 failed attempt left only `/private/tmp/paper-b-b1-launch-capture-20261113.nWfxSdNl/launch.log` (no SHA256SUMS, since `launch.sh` writes it only after success); this is the expected shape of a failed precheck and wrote nothing into `RUN_DIR` or `BATCH`.
- `_c` `marker-retirement.note` is `7166c05a…`, while `4b86ba34…` is `marker-retirement_stop.note`; the final note check correctly relies on content, not on that ambiguity.

VERDICT: accepted
