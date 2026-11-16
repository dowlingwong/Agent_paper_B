# Result — leftover `gpu0.lock` on TASL-2 released (16 November 2026)

**Status: executed under the reviewed unit; no file deleted; TASL-2 scene preserved.** AI-assisted,
operator: DeepSeek Harness agent. Authority: PLAN §10 `R1-TASL2-LOCK` (16 Nov, `author-decisions-20261116`
@ `4da73306`) and `R1-TRACKS-STOP4-CONSEQUENCES` item (4). Reviewed unit:
`proposals/TASL2_LOCK_RELEASE_20261116.md`, sha256
`e0efc29fd63b12b95ddc4010b4dd123f0d51259a27070d361c4924a062bb9be3`; accepted review
`reviews/TASL2_LOCK_RELEASE_REVIEW_20261116.md`, sha256
`5e22f1c5494b2f2acbd3b79a10586b919e94a4646a342ca683b62c5e8d301251`, recorded at `03fcf362`.
Capture: `docs/r1/reports/tasl2_lock_release_20261116/` (`capture.txt` sha `3783683b…`, `ssh.log`
`bf5d2f4f…`, `ssh.exit` `9a271f2a…` = `0`, SHA256SUMS).

## 1. Before (TASL-2, 2026-11-16T09:54:43Z, user `dowling`, boot id `86c613a9…`, uptime since 2026-11-15 12:51:25 local)

- `~/r1_locks/gpu0.lock`: dev 66306, **inode 120090387**, 0 B, mode 664, owner dowling:dowling,
  mtime = ctime `2026-10-25 21:35:24.275265604 -0700`, sha256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. `~/r1_locks` held only that file;
  `_to_delete` did not exist.
- **No holder:** `/proc/locks` (38 entries) had no entry for inode 120090387; `lslocks` no `gpu0.lock`;
  no uid-1008 fd to the lock; no `dowling` experiment/Track process, marker or tmux server; no GPU compute
  app. Recorded so the "no owner process" precondition is evidenced, not assumed.
- **Last known holder/time** (preserved launch log, as the accepted review's m-12 asked):
  `/home/dowling/r1_tracks/logs/s05_20261112_launch.log` has `2026-11-12T19:56:02Z lease: HELD` (pid
  1386618, tmux `trks_llm`); that process is gone after the 12–15 Nov outage/reboot. The file itself was
  created 25 Oct and has been an unused leftover since.

## 2. Action (reviewed unit, steps 3–5)

1. `_to_delete` created mode 700 under `~/r1_locks/` (plain dir, not replacing any existing path).
2. `mv -n ~/r1_locks/gpu0.lock ~/r1_locks/_to_delete/gpu0.lock.retired.20261116T095443Z`.
3. Verified: source absent; target present at dev 66306, **same inode 120090387**, 0 B, mode 664,
  sha256 `e3b0c442…` (mtime kept `2026-10-25 21:35:24.275265604 -0700`; ctime changed to the move time).
   **Nothing was deleted; the old file is preserved under `_to_delete/`.**
4. Restored the canonical lease path: `flock -n ~/r1_locks/gpu0.lock true` created a fresh empty
   `gpu0.lock` (dev 66306, **inode 120088542**, 0 B, mode 664) and the lock was acquired/released
   successfully (`LEASE_ACQUIRABLE`). All lease consumers use the path, so the move breaks none.

## 3. After (same session, verified again live at 09:54:51Z)

- `~/r1_locks`: `gpu0.lock` (fresh, 0 B) + `_to_delete/` (mode 700) containing only
  `gpu0.lock.retired.20261116T095443Z` (inode 120090387, 0 B, sha `e3b0c442…`).
- Track S scene unchanged: 4 manifests (`out/smoke/manifest.json` 3,939 B;
  `out/digits_mlp/s05/manifest.json` 2,707 B; `out/digits_mlp/s04_r2_20261111/manifest.json` 3,976 B;
  `out/digits_mlp/s04/manifest.json` 6,776 B), 0 STOP files, subdirs `digits_mlp/` + `smoke/`; no other
  path was moved, chmod'ed or chown'ed, and no git command ran on TASL-2.
- No file was deleted by this unit; `_to_delete` is not emptied.

## 4. Accepted-review findings recorded (not executed as edits; unit bytes unchanged)

The review accepted the unit (`5e22f1c5…`) with 13 MINOR recording/hardening notes. They are dispositioned
here without changing the reviewed unit bytes: (m-1) "read-only SSH" applies to the capture/diagnosis
steps, while steps 3–5 are the reviewed host writes above; (m-2) `_to_delete` type/mode was checked before
use and created 700; (m-3) the target stamp format is `%Y%m%dT%H%M%SZ` (used in the target name); (m-4)
process/marker/fd/GPU queries are recorded in `capture.txt`; (m-5) stat records dev/inode/size/mode/owner/
mtime/ctime and the file is not a symlink; (m-6) the census review and bare-push records live at
`ops-b2-exec-20261115 @ 55fd2652` / `ops-tasl-20261116`; (m-7) the fresh lease file was verified after the
move; (m-8/m-9) STOP conditions and the must-not list were followed (no deletion, no force, no other host
action, no git); (m-10) scene inventory above is the only "other path" check; (m-11) this report is the
result record; (m-12) the last known holder/time is recorded in §1; (m-13) "nothing running" means no
`dowling` experiment process — unrelated other-uid system services (docker/containerd, GDM/pipewire,
mongod, snapd, etc.) run and were untouched.
Disclosure: read-only SSH logins may touch the host's own systemd user session/wireplumber state (outside
`~/r1_locks`, `~/r1_tracks`, markers and the scene), as in the accepted census review.

## 5. Outcome

- The stale leftover is retired **without deletion**; the canonical `~/r1_locks/gpu0.lock` is a fresh empty
  lease file and the lease is acquirable.
- TASL-2 is now clear for its post-`R1-TASL2-LOCK` role: Track P's second card for **non-evidence** work
  only (evidence tables remain TASL-7 only). No Track P run or other TASL-2 action was started.
- Point-in-time result; TASL-2 otherwise untouched.
