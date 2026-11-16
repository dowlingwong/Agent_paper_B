# Unit — release the leftover `gpu0.lock` on TASL-2 (for independent review; 16 November 2026)

**Authority.** PLAN §10 `R1-TASL2-LOCK` (16 Nov 2026, `author-decisions-20261116` @ `4da73306`):
"同意用一个独立审查过的单元处理 TASL-2 遗留的 `gpu0.lock`：记录持有者与时间，仅在无属主进程时释放，
不删除任何文件（移到 `_to_delete/`）。之后 TASL-2 可作 Track P 的第二张卡，只跑不进 evidence 表的工作。"
Also `R1-TRACKS-STOP4-CONSEQUENCES` item (4) (TASL-2 released after the reviewed read-only census; the
census is accepted — `reviews/TASL2_READONLY_CENSUS_REVIEW_20261115.md`, sha `a00cf7a2…`, and the deferred
`trackS-ops-20261030` bare push was done `25907343→fab88fce`). **Not an execution yet**: this unit is
submitted for an independent review; it runs only after acceptance.

## 1. Read-only facts (16 Nov 2026, 09:37Z; user `dowling`)

| Item | Value |
|---|---|
| Host | TASL-2, `portal_zhixu`, hostname `TASL-2`; boot id `86c613a9-b90c-48be-9bd5-a0f99c940dae`, booted 2026-11-15 12:51 local (12h46m uptime at check) |
| Lock path | `/home/dowling/r1_locks/gpu0.lock` |
| inode / size / sha256 | `120090387` / `0 B` / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| mtime / ctime | `2026-10-25T21:35:24.275265604-0700` / same |
| Holder | **none**: `/proc/locks` has no entry for the inode; `lslocks` lists no `gpu0.lock`; no `/proc/*/fd` holder; no `dowling` experiment/Track process and no tmux server |
| Lease probe | `flock -n ~/r1_locks/gpu0.lock true` = `LEASE_ACQUIRABLE` (acquired and released; no content change) |
| Other state | `~/r1_locks` contains only `gpu0.lock`; no marker; nothing running; TASL-2 scene preserved (census accepted 15 Nov) |

Interpretation: the file is a **stale leftover**. It was created on 25 Oct; the host has since rebooted,
it is not locked by any process, and it does not block a lease. `R1-TASL2-LOCK` still asks that it be
recorded and moved aside (not deleted) before TASL-2 is used as Track P's second card.

## 2. Preconditions (all fail-closed)

1. TASL-2 reachable (`ssh portal_zhixu`, user `dowling`); hostname = TASL-2.
2. No owner process: re-check `/proc/locks` (inode), `lslocks`, `/proc/*/fd` for the lock path, and the
   process table — if any holder or a `dowling` experiment/Track process exists → STOP, record, report.
3. No marker (`trackx_evidence.active`, `trackp_evidence.active`, `trks_drill.active`) and no tmux server.
4. Lock file stat matches the record above (inode/size/sha/mtime) — if it changed → STOP.
5. Target `~/r1_locks/_to_delete/` is absent or a plain dir; target
   `~/r1_locks/_to_delete/gpu0.lock.retired.<UTC>` must not exist.
6. The accepted TASL-2 census review is available (sha `a00cf7a2…`); the deferred bare push is done.

## 3. Procedure (host TASL-2, user `dowling`; nothing deleted)

Run from a Mac capture directory (read-only SSH, no other host action):

1. **Capture before**: `date -u`, `hostname`, `id`, `boot_id`, `uptime -s`, `stat`/`sha256sum` of the lock,
   `/proc/locks` (whole), `lslocks`, `/proc/*/fd` scan, `ps` (all), `tmux ls`, marker listing, `df -h`.
2. **Re-verify** preconditions 1–5; any mismatch → STOP.
3. `mkdir -m 700 -p ~/r1_locks/_to_delete` (mkdir only; if `_to_delete` exists, require a plain dir).
4. `mv -n ~/r1_locks/gpu0.lock ~/r1_locks/_to_delete/gpu0.lock.retired.<UTC>`; then verify: source absent,
   target present, same inode, 0 B, same sha256 `e3b0c442…`.
5. **Lease-free check**: `flock -n ~/r1_locks/gpu0.lock true` → this creates a **new empty lease file**
   (the normal state for a lease file; the old file is not deleted but moved aside). Record the new
   inode/size/sha and release the lock (flock releases on process exit).
6. **Capture after**: same inventory; confirm the moved file is in `_to_delete/`, the moved file is byte-
   identical (sha `e3b0c442…`), no process/marker/tmux appeared, and no other path changed.
7. Write a local result record (e.g. `results/r1/engineering/tasl2_lock_release_<stamp>/` or an operator
   capture dir) with `SHA256SUMS`, then report; no retry on any STOP.

## 4. STOPs (preserve, report, no retry)

- Any holder/process/marker appears, hostname mismatch, lock stat/sha mismatch, target exists, `mv`
  fails/no-ops, the moved file's inode/sha differs, or any other TASL-2 action is needed.
- A STOP is preserved as it stands (move-aside, not delete); no retry without a new reviewed unit.

## 5. Must not

- No deletion of the lock file or any other file; no lock released by force; no signal to any process;
  no Track P evidence or GPU job on TASL-2 in this unit; no git push/checkout on TASL-2; no use of TASL-2
  beyond the lock handling above. After this unit, TASL-2 may take Track P **non-evidence** work only.

## 6. Review and execution record

- Independent review: required before execution; the review file records approval of these exact bytes.
- Execution: append the captured before/after facts and the moved-file sha to this unit (or a report),
  commit/push on the operator branch, and report to the author.
