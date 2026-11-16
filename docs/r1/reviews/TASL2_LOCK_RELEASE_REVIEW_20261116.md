# Independent review — TASL-2 leftover `gpu0.lock` release unit (R1-TASL2-LOCK) — 16 November 2026

**Reviewer role.** Fresh, independent, read-only reviewer, spawned for this exact question. Not the author,
not the unit's proposer, not the census operator. This review did not execute the unit, did not commit,
branch, tag or push anything, and did not delete anything. The only repository file written is this review
(untracked). Read-only SSH to TASL-2 (`ssh portal_zhixu`, user `dowling`) was used only for the independent
comparison in §4; its one non-command side effect is the known SSH-login PipeWire state file, disclosed in
§4.7. No file was created, modified or removed on TASL-2 by any command of this review.

**Verdict: accepted.** The unit is authority-compliant, its preconditions and STOPs fail closed, and its
exact command set is non-destructive: it records the stale file, re-checks that no owner process exists,
creates only `~/r1_locks/_to_delete/`, moves the old lock there with `mv -n` (no delete, no force, no
signal), and restores a fresh empty lease file at the canonical path. The recorded TASL-2 facts are
independently reproduced (inode `120090387`, 0 B, sha256 `e3b0c442…`, mtime/ctime
`2026-10-25T21:35:24.275265604-0700`, no holder, no marker, no tmux server, lease acquirable, scene
preserved). Findings are **MINOR only** (§7); none is a condition on execution.

---

## 1. Scope

In scope: the unit `docs/r1/proposals/TASL2_LOCK_RELEASE_20261116.md` (72 lines) at the canonical commit,
its authority (PLAN §10 `R1-TASL2-LOCK`; `R1-TRACKS-STOP4-CONSEQUENCES` item (4)), its recorded facts, its
preconditions/procedure/STOPs/must-not, the exact commands' safety, the handling of the moved file and the
re-created lease file, the required result record, and a read-only independent re-verification of the
TASL-2 facts.

Out of scope (not reviewed/re-authorized here): the TASL-2 read-only census itself (already accepted,
sha `a00cf7a2…`), the deferred bare-repo push (verified below, not re-run), any Track P work, TASL-7, and
any further use of TASL-2. This review does not authorize any TASL-2 action beyond the lock handling in
the unit.

## 2. Authority and canonical bytes

| Item | Value |
|---|---|
| Repo / worktree | `/Users/wongdowling/Documents/agent_paper_B`, review worktree `.claude-worktrees/ops-tasl-20261116` |
| Branch / commit | `ops-tasl-20261116` = `origin/ops-tasl-20261116` @ **`eb65ac4fb04fa4eff08ee144083a8fce609f342f`** |
| Worktree state | clean at review start; this review is the only untracked file written |
| Unit | `docs/r1/proposals/TASL2_LOCK_RELEASE_20261116.md`, 72 lines, blob `0ebe90b8e44c17e90929e1dd977b1baa69220105`, sha256 **`e0efc29fd63b12b95ddc4010b4dd123f0d51259a27070d361c4924a062bb9be3`** |
| Unit commit | `eb65ac4f`, 2026-11-16 10:46:30 +0100 = 09:46:30Z |

**Authority.** `author-decisions-20261116` @ **`4da73306`** ("docs(r1): author decisions 16 Nov —
… R1-TASL2-LOCK …"), merged into the canonical branch. The authority bytes are identical in the canonical
tree: `docs/r1/PLAN.md` blob **`8cf5fb4b140f913f48426576e7a67a0b4ebb1e0f`**, sha256
**`993cc0a3c3407341b367f613225e32535721bfd24002201be30fb22d66742289`** at both `4da73306` and `eb65ac4f`.

- `PLAN.md` L**1210**, `R1-TASL2-LOCK`, verbatim: “**同意用一个独立审查过的单元处理 TASL-2 遗留的
  `gpu0.lock`：记录持有者与时间，仅在无属主进程时释放，不删除任何文件（移到 `_to_delete/`）。** 之后
  TASL-2 可作 Track P 的第二张卡，只跑不进 evidence 表的工作（R1-TASL7-TRACKP：evidence 表只在 TASL-7
  产出）。”
- `PLAN.md` L**1171**, `R1-TRACKS-STOP4-CONSEQUENCES` item (4), verbatim in the operative part: “TASL-7 对
  Track S 的分配结束；**TASL-2 同样从 Track S 释放，但须在其恢复联网后先由实验 agent 只读清点（Track S
  服务器、GPU lease、进程），清点经审查后才可另作他用；两台主机上的 Track S 现场保持不动。**”

The unit's §1 quote of `R1-TASL2-LOCK` is exact; its citation of `R1-TRACKS-STOP4-CONSEQUENCES` item (4) is
correct (the reviewed census is the gate, and it is satisfied: §4.6).

**Supporting accepted artifacts (cross-branch, read-only).**

| Artifact | Value |
|---|---|
| Census review (`docs/r1/reviews/TASL2_READONLY_CENSUS_REVIEW_20261115.md`) | at `55fd2652` (branch `origin/ops-b2-exec-20261115`), 460 lines, sha256 **`a00cf7a2fc12c739cb94b00e2113e56148c0eb4556f873d7ef798600319ffc90`**, verdict **accepted** |
| Bare-push receipt (`…/trks_stop/tasl2_bare_push_receipt.txt`) | at `55fd2652`: `before=25907343728fe48fbe9f1543b6b3a0921eb7012d`, `after=fab88fced839c5fb794ed62a0742b4646cb76ea2`, `delta=52 commits, fast-forward`, `force=no`, verified `git ls-remote` → `fab88fce` |
| Live TASL-2 bare ref (read-only `git show-ref` on the host) | `refs/heads/trackS-ops-20261030` = **`fab88fced839c5fb794ed62a0742b4646cb76ea2`**; `mac-tracks-a2u-stale-20261111` = `c8b13b5d63d3d30f5afa642928f1458e863e8935` |

The push is therefore done as the unit's precondition 6 states (52-commit fast-forward, no force). Note that
the two supporting artifacts live on another branch, not in the canonical tree — see m-6.

## 3. Method and limits

- Inspected the unit and the authority rows at the exact commits/blobs above.
- Extracted the census review and push receipt from git object `55fd2652` (read-only) and hashed them.
- Ran read-only SSH to TASL-2 (`ssh portal_zhixu`, alias `HostName 100.120.160.70`, `User dowling` per
  `~/.ssh/config`): hostname/id/boot id/uptime, `stat`/`sha256sum` of the lock, whole `/proc/locks`,
  `lslocks`, `/proc/*/fd` scan, full `ps`, `tmux ls`, marker listings, `~/r1_locks` listing, scene listing,
  `nvidia-smi --query-compute-apps`, `who`/`last -x`, the bare-repo ref, and the preserved S0.5 launch log.
- Acquired and released one transient `flock -n ~/r1_locks/gpu0.lock true` probe, guarded by `[ -e … ]` so
  it could not create the file. It returned rc 0 and left the file byte-, inode- and mtime-identical
  (§4.5). This is a normal transient lease acquire/release, not a content change.
- No file was created, modified or removed on TASL-2 by any command; no process was started, stopped or
  signalled; no lock was force-released; no git write; no commit.
- Read-only SSH login on this GDM/PipeWire host starts the `dowling` systemd user session, which writes
  `~/.local/state/wireplumber/restore-stream` (205 B) — the census review's m-4 artifact, outside
  `~/r1_locks`, `~/r1_tracks`, the marker and the bare repo (§4.7). If literal zero host writes are
  required, that is impossible for any SSH check; the claims below are scoped accordingly.

## 4. Independent read-only verification of TASL-2 (2026-11-16, 09:48–09:52Z)

Host clock at first capture: `2026年 11月 16日 星期一 09:48:58 UTC`.

### 4.1 Host identity

| Item | Observed | Unit §1 | Match |
|---|---|---|---|
| Hostname | `TASL-2` | `TASL-2` | ✅ |
| User | `uid=1008(dowling) gid=1008(dowling)` | user `dowling` | ✅ |
| Boot id | `86c613a9-b90c-48be-9bd5-a0f99c940dae` | same | ✅ |
| Boot time | `uptime -s` = `2026-11-15 12:51:25` local (host TZ UTC-8 → 20:51:25Z); `up 12:57, 0 users` | booted 2026-11-15 12:51 local; 12h46m at 09:37Z | ✅ (09:37Z − 20:51:25Z = 12h45m35s) |
| `who` | empty | — | ✅ no interactive login |

### 4.2 Lock file — exact values

```
/home/dowling/r1_locks/gpu0.lock  inode=120090387 size=0 mode=664 owner=dowling uid=1008
  mtime=2026-10-25 21:35:24.275265604 -0700  ctime=2026-10-25 21:35:24.275265604 -0700  links=1
  dev=66306 (major:minor 259:2; /proc/locks renders this device as 103:02)
sha256 = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

`~/r1_locks` contains **only** `gpu0.lock` (dir inode `120090385`, mtime/ctime
`2026-10-25 21:35:24.275265604 -0700`); **`_to_delete` is absent**. All values match unit §1 exactly
(inode, 0 B, sha, mtime/ctime).

### 4.3 No holder

- `/proc/locks` at check: 38 entries, **none** for the lock's device:inode (`103:02:120090387`);
  `grep 120090387` and `grep gpu0` both return nothing. `/proc/locks` is host-wide (FLOCK and POSIX), so
  this covers holders of any uid.
- `lslocks`: **no** `gpu0`/`r1_locks` path.
- `/proc/*/fd` scan (uid-1008 scope, the only unprivileged scope available): **no** descriptor to
  `~/r1_locks`; the global `/proc/locks`+`lslocks` checks are the authoritative holder test.
- `ps -eo pid,user,etimes,args`: the only `dowling` processes are my SSH login's session helpers
  (`systemd --user`, `sd-pam`, `pipewire`, `pipewire-pulse`, `wireplumber`, `snapd-desktop-integration`,
  session dbus, xdg portals, `sshd`, `bash -s`, `ps`). **No experiment/Track process.** `pgrep -a -f` for
  `exam_runner`, `llama-server`, `trks`, `trackp`, `r1_tracks`, `r1_locks`, `gpu0` all rc=1/no output.
- `tmux ls` → `error connecting to /tmp/tmux-1008/default (No such file or directory)`, rc=1 (no server).
- `nvidia-smi --query-compute-apps=pid,process_name,used_memory` → **empty** (no GPU compute app).
- Markers: **none** in `~/r1_locks/*.active`, `~/r1_tracks/*.active` (covers `trackx_evidence.active`,
  `trackp_evidence.active`, `trks_drill.active`) or `~/*.active`.
- The host's other-uid services (root, `gdm`, `www-data`, uid 999: the Overleaf docker stack, `mongod`,
  `redis`, GDM/gnome, monitoring) are present and are **not ours**; none touches `~/r1_locks` (no lock, no
  fd, no compute app). The unit's claim is scoped to `dowling` experiment/Track processes; that claim
  holds.

### 4.4 Lease probe

Guarded `[ -e ~/r1_locks/gpu0.lock ]` → true, then `flock -n ~/r1_locks/gpu0.lock true` → **rc=0**
(LEASE_ACQUIRABLE). After the probe:

```
inode=120090387 size=0 mtime=2026-10-25 21:35:24.275265604 -0700 ctime=same
sha256 = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Identical to before: no content, inode, mtime or ctime change; no file created. This reproduces the unit's
§1 probe row.

### 4.5 Scene preserved

- `~/r1_tracks` present with `bin/ launch/ logs/ models/ opt/ out/ remotes/ scratch/ venv/ work/`
  (mtimes Nov 8–12, pre-outage).
- `~/r1_tracks/out`: `digits_mlp/` (11 subdirectories: `inputs`, `s01`, `s01_diag`, `s01_diag_f1`,
  `s01_diag_f2`, `s01_rerun20261109`, `s01_rerun_INVALID_serial_raced_server_start_20261031T112159Z`,
  `s04`, `s04_r2_20261111`, `s05`, `s11`) and `smoke/`.
- 4 `manifest.json`: `s05` 2707 B, `smoke` 3939 B, `s04_r2_20261111` 3976 B, `s04` 6776 B — same sizes as
  the accepted census review.
- No `*stop*` path under `out`; `watch.log` 360 B, last line `2026-11-09T01:29:08Z`; `llama_18101.log`
  587,235,328 B (mtime Nov 12 12:14 local), `llama_18102.log` 394,023,968 B (Nov 8 16:34),
  `s05_20261112_launch.log` 622 B, `trks_s05.log` 303,104 B. Pre-outage mtimes; no post-outage writes.
- Last preserved lease record: `logs/s05_20261112_launch.log` —
  `2026-11-12T19:56:02Z lease: HELD` with `server pid: 1386618` in tmux `trks_llm`; `last -x` shows the
  reboot `Sun Nov 15 12:51` local and the pre-reboot `dowling` tmux sessions ending in `crash`. That holder
  is gone after the outage/reboot. **See m-12**: the unit does not record this last known holder/time.

### 4.6 Census gate and bare push

- Census review at `55fd2652` hashes to `a00cf7a2…` (460 lines) and its verdict is **accepted** — matches
  unit §1 and precondition 6.
- Live TASL-2 bare ref `trackS-ops-20261030` = `fab88fce…`; the receipt records the fast-forward
  `25907343→fab88fce`, 52 commits, no force — matches the unit's claim.
- The census is therefore reviewed before any further TASL-2 use, satisfying `R1-TRACKS-STOP4-CONSEQUENCES`
  item (4)'s “清点经审查后才可另作他用”.

### 4.7 Login-session side effect (disclosure)

`~/.local/state/wireplumber/restore-stream` (inode `120088542`, 205 B) had mtime
`2026-11-16 01:48:54.889277802 -0800` = `09:48:54Z`, inside my first login window. This is the known
PipeWire/wireplumber SSH-login artifact documented as census review m-4; it is outside `~/r1_locks`,
`~/r1_tracks`, the markers and the bare repo, and no command of this review wrote to the host.

## 5. Unit's claims checked

| Unit claim (location) | Result |
|---|---|
| Host/boot id/reboot 15 Nov (§1) | ✅ reproduced (§4.1) |
| inode `120090387`, 0 B, sha `e3b0c442…`, mtime/ctime `2026-10-25T21:35:24.275265604-0700` (§1) | ✅ exact (§4.2) |
| Holder none: `/proc/locks`, `lslocks`, `/proc/*/fd`, process table, no tmux (§1) | ✅ (§4.3; fd scan is uid-scoped — see m-4) |
| Lease probe `LEASE_ACQUIRABLE`, no content change (§1) | ✅ rc=0, bytes/inode/mtime unchanged (§4.4) |
| `~/r1_locks` contains only `gpu0.lock`; no marker; scene preserved (§1) | ✅ `_to_delete` absent; no markers; scene intact (§4.5) |
| Census review accepted, sha `a00cf7a2…`; bare push `25907343→fab88fce` done (precondition 6) | ✅ (§4.6) |
| Interpretation: stale leftover, created 25 Oct, host rebooted, no holder, does not block a lease | ✅ for current state; the file's last known lease use was 12 Nov (m-12) |
| Procedure commands: `mkdir -m 700 -p`, `mv -n`, `flock -n … true`, captures only | ✅ §6.3 |
| Nothing deleted; move-aside to `_to_delete/`; new empty lease file is the normal lease file | ✅ §6.3–§6.4 |
| No TASL-2 action beyond lock handling (§5) | ✅ §6.5 |

No factual claim in the unit was found false. The identified gaps are recording/completeness items (§7).

## 6. Assessment of the unit

### 6.1 Authority fit

The unit implements exactly `R1-TASL2-LOCK`: it records holder/time, releases (retires) the leftover file
only if no owner process exists, and deletes nothing (move to `_to_delete/`). It correctly treats the
review as the gate and execution as post-acceptance. It states that after the unit TASL-2 may take Track P
**non-evidence** work only, matching the row's “只跑不进 evidence 表的工作”. It does not authorize any
Track P run or any other TASL-2 action — good.

### 6.2 Preconditions

All five in-domain preconditions are fail-closed (hostname; no holder/process; no marker/tmux; stat/sha/
mtime match; target absent/plain dir), plus the external census/push check. The preconditions are
re-checked immediately before the move, and any mismatch is a STOP. Gaps are recording precision (exact
paths/patterns, symlink/owner checks, probe failure) — m-2, m-4, m-5, m-7.

### 6.3 Exact commands — safety

The command set is `mkdir -m 700 -p ~/r1_locks/_to_delete`, `mv -n ~/r1_locks/gpu0.lock
~/r1_locks/_to_delete/gpu0.lock.retired.<UTC>`, `flock -n ~/r1_locks/gpu0.lock true`, and read-only
captures (`date`, `hostname`, `id`, `boot_id`, `uptime`, `stat`, `sha256sum`, `/proc/locks`, `lslocks`,
`/proc/*/fd`, `ps`, `tmux ls`, marker listing, `df -h`). There is **no** `rm`/`rmdir`, no `-f`/force, no
`kill`/`pkill`/`killall`, no signal, no `chmod`/`chown`, no service/`systemctl` command, no `git` command,
and no write outside `~/r1_locks`. The move is `mv -n` on the same filesystem (`~/r1_locks/_to_delete/` is
inside `~/r1_locks`), so it is a rename that preserves the inode; step 4 verifies source absent, target
present, same inode, 0 B and same sha. Step 5's `flock -n` creates the fresh empty lease file at the
canonical path (the normal lease-file state; the old file is preserved in `_to_delete/`), acquires and
releases the lock, and step 6 captures the after state. This is safe as written.

### 6.4 STOPs and must-not

§4's STOP list covers holder/process/marker appearance, hostname mismatch, stat/sha mismatch, existing
target, `mv` failure/no-op, moved inode/sha mismatch, and “any other TASL-2 action is needed”; a STOP is
preserved (move-aside, not delete) with no retry without a new reviewed unit. §5 forbids deletion, force
release, signals, Track P evidence/GPU work, and git push/checkout on TASL-2. Gaps: SSH-unreachable/capture
failure, probe rc≠0, `_to_delete` not a plain dir, and new-lease-file anomalies are not explicitly in the
STOP list (m-8); the must-not list should also name “no other file moved/renamed/chmod/chown” and “no git
command at all on TASL-2” (m-9). These are hardening, not unsafe-by-omission: the procedure simply does not
contain such commands, and “any other action needed” already STOPs.

### 6.5 “Nothing deleted” / “release” meaning

The unit contains no delete command; the old file is moved to `_to_delete/` and verified there by path,
inode, size and sha; the new `gpu0.lock` is a new empty file. “Release” here means retiring the stale
advisory path and restoring a fresh lease file — there was no live lock to release (`flock -n` acquirable;
no `/proc/locks` entry). This matches the authority's conditional (“仅在无属主进程时释放”) and preserves
the old bytes. I verified that no committed or host-side lease consumer requires `~/r1_locks` to contain
only `gpu0.lock`: the repo's lease users (`r1/exam/runtime.py`, `r1/c3/train/run.py`,
`r1/scripts/b1_host_preflight.py`) and the host scripts (`~/r1_tracks/bin/trks-servers`, `trks-watch`,
launch scripts) all use path-based `flock ~/r1_locks/gpu0.lock` plus `[ -e marker ]` checks, so the extra
`_to_delete/` directory does not break them.

### 6.6 Result record

§3 step 7 + §6 require a local capture with `SHA256SUMS`, before/after facts, the moved-file sha, and a
commit/push/report on the operator branch. That is adequate in substance, but under-specified (m-11):
the output path is only “e.g.”, and the record should explicitly require the reviewed unit/review bytes
hash, precondition rc values, the moved file's path/inode/sha, the **new lease file's** inode/size/sha/mode,
the `_to_delete/` listing, and the explicit statements “no holder” and “nothing deleted”.

## 7. Findings

**BLOCKING: none. MAJOR: none.** All findings are **MINOR** (recording/hardening); none makes the
procedure unsafe, unauthorized or non-fail-closed. Each has an exact location and a required fix; they
should be folded into the operator record and the next unit revision.

### m-1 — “read-only SSH, no other host action” is inaccurate for this unit (L40)
`§3` opens: “Run from a Mac capture directory (read-only SSH, no other host action)”, but steps 3–5 are
three deliberate host writes (`mkdir`, `mv`, `flock`-created lease file) by this unit. *Required fix:*
reword to “capture commands are read-only; steps 3–5 are the only host writes and all are inside
`~/r1_locks`; no other host action” (and disclose the login-session PipeWire write, see m-10).

### m-2 — Existing `_to_delete` only has to be a “plain dir” (L34–35, L45)
`mkdir -m 700 -p` does not tighten an existing directory's mode, so a pre-existing wider-permission
`_to_delete` would be accepted. *Required fix:* require an existing `_to_delete` to be a real directory, not
a symlink (`[ -d ] && [ ! -L ]`), owned by `dowling`, mode `700`; otherwise STOP (no `chmod`).

### m-3 — `<UTC>` timestamp format is not defined (L35, L46)
The target name `gpu0.lock.retired.<UTC>` has no concrete format; a shell could create a literal
`gpu0.lock.retired.<UTC>`, or a second `date` call could give a different stamp for the record.
*Required fix:* capture `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` once at the start and use `${STAMP}` for both the
move target and the result record.

### m-4 — Process patterns and marker paths are not specified (L30–32)
Precondition 2 says “any … `dowling` experiment/Track process” without naming the patterns; precondition 3
names the markers without paths (`trackx_evidence.active`/`trackp_evidence.active` live in `~/r1_locks/`;
`trks_drill.active` in `~/r1_tracks/`); `pgrep` rc=2 (usage error) is indistinguishable from rc=1 (no
match); the `/proc/*/fd` scan is uid-scoped. *Required fix:* name the exact `pgrep -a -f` patterns
(`exam_runner|llama-server|trks|trackp|r1_tracks`), treat rc=2 as STOP, give the three absolute marker
paths, add `who`/`uptime` (0 users) and `nvidia-smi --query-compute-apps` empty, and state that the
global holder test is `/proc/locks`+`lslocks` (fd scan is uid-scoped).

### m-5 — Stat/sha checks follow symlinks; file identity is thinner than the recorded facts (L33)
`stat`/`sha256sum` follow symlinks, so a replaced symlink could satisfy inode/size/sha. The recorded facts
also omit owner/mode/device (now observed: uid 1008, mode 664, dev 259:2). *Required fix:* require
`[ -f ] && [ ! -L ]`, owner `dowling` uid 1008, mode `664`, and record the device/inode in the before/after
capture.

### m-6 — Precondition-6 artifacts are not in the canonical tree (L36)
`reviews/TASL2_READONLY_CENSUS_REVIEW_20261115.md` (sha `a00cf7a2…`) and the push receipt are at
`origin/ops-b2-exec-20261115` @ `55fd2652`, not at `eb65ac4f`; an operator on the canonical worktree cannot
find them by the path as written. *Required fix:* cite `55fd2652:docs/r1/reviews/...` and
`55fd2652:docs/r1/reports/b2_exec_20261115/trks_stop/tasl2_bare_push_receipt.txt`, verify with
`git cat-file -e`/`git show`, and record the live bare-ref `fab88fce`.

### m-7 — Lease-probe failure modes are not handled (L48–50)
Step 5 does not say what happens if the probe returns non-zero (someone took the lease) or the new file is
not created as a regular 0 B file owned by `dowling`. *Required fix:* `[ -e ]`-guard the probe (m-10
analogue), require `PROBE_RC=0`, then require the new `gpu0.lock` to be a regular file, size 0, owner
`dowling`, and record its inode/device/mode/sha; any deviation → STOP.

### m-8 — STOP list is incomplete (L56–60)
Not in the STOP list: SSH unreachable or any capture command failing, `_to_delete` not a plain dir, probe
rc≠0, new lease file missing/non-empty, or any command returning an unexpected rc. *Required fix:* add
those explicitly (SSH rc≠0 → STOP with no capture, mirroring the census unit's `UNREACHABLE.txt` rule).

### m-9 — Must-not list should name the remaining prohibitions (L62–66)
It says no deletion, no force release, no signals, no Track P evidence/GPU job, no git push/checkout on
TASL-2. *Required fix:* add “no other file is moved, renamed, modified, chmod'ed or chown'ed; `_to_delete/`
is never emptied; the moved file is never deleted (also not in later cleanup); **no git command at all** on
TASL-2 in this unit” and note that any later Track P non-evidence work needs its own reviewed unit.

### m-10 — “No other path changed” is not verifiable from the listed captures (L51–52)
Step 6 claims “no other path changed”, but the listed captures only cover `~/r1_locks`, markers, tmux, ps
and the lock. *Required fix:* scope the claim to “no other path in `~/r1_locks`, the marker set, the
process table, the Track S scene (`~/r1_tracks/out` inventories/mtimes) changed; the SSH login may touch
`~/.local/state/wireplumber/restore-stream`, which is outside all of those”, and compare before/after lists.

### m-11 — Result record is under-specified (L53–54; §6 L68–72)
The output is “e.g. `results/r1/engineering/tasl2_lock_release_<stamp>/` or an operator capture dir”, and
the required fields are only “before/after facts and the moved-file sha”. *Required fix:* fix the path
(UTC stamp), require `SHA256SUMS`, and require the record to include: the reviewed unit sha256 and this
review's sha256; boot id/hostname/uptime; precondition rc table; before/after `~/r1_locks` listings; moved
file path/inode/size/sha; new lease file path/inode/size/mode/sha; `_to_delete/` listing; explicit “no
holder” and “nothing deleted” statements; and “no TASL-2 action beyond lock handling”.

### m-12 — “Record holder and time” is only partially satisfied (L17–18, L23–25)
The unit records current holder = none and the file's mtime/ctime (Oct 25), but not the last **known**
lease holder/time, which the preserved records do give: `~/r1_tracks/logs/s05_20261112_launch.log`
`2026-11-12T19:56:02Z lease: HELD`, server pid 1386618 in tmux `trks_llm`, gone after the outage and the
15 Nov 12:51 local reboot. Without it, “created 25 Oct” can be misread as the last lease use. *Required
fix:* add one line: “no current holder; the file's inode/mtime/ctime are 2026-10-25T21:35:24 -0700; the last
known lease use is the 12 Nov S0.5 run (`lease: HELD`, pid 1386618), which did not survive the outage/
reboot; the post-reboot state has no holder.” This directly serves the authority's “记录持有者与时间”.

### m-13 — “Nothing running” overclaims (L21)
“Other state: … nothing running” is literally false on this host: the Overleaf docker stack, mongod, GDM
and other root/services run as other uids. *Required fix:* scope to “nothing of ours running: no `dowling`
experiment/Track process, no tmux server, no GPU compute app; unrelated host services (other uids) are
present”.

## 8. Residual risks

1. **Review-to-execution drift.** The facts above are as of 09:48–09:52Z. The unit re-checks hostname,
   holder, markers, stat/sha/mtime and target before moving; any drift → STOP. A reboot between review and
   execution does not itself invalidate the file check (the file survives with the same inode/bytes), but
   the operator must re-run all preconditions, not rely on this review's values.
2. **Other users' activity / TOCTOU.** TASL-2 is a shared host with unrelated services under other uids. A
   process appearing between precondition 2 and the `mv` is a small race; `mv` would still rename the path,
   and step 4's inode/sha verification plus step 6's process check would catch a moved-file mismatch and
   STOP. No signal is permitted, so a STOP is the only handling.
3. **The file is recreated.** After the unit, `gpu0.lock` is a **new** 0 B inode; the old inode is retired in
   `_to_delete/`. All committed and host-side lease consumers are path-based `flock` on
   `~/r1_locks/gpu0.lock` (verified), so the new file is the canonical lease path; a process still holding
   an fd to the old inode could lock that inode, but none exists now. `~/r1_locks` will additionally
   contain `_to_delete/`; no lease script asserts otherwise.
4. **Meaning of “release” for a stale advisory file.** There is no live lock to release; the unit's
   semantics (retire the stale path, restore an empty lease file) is the only meaningful “release” and is
   consistent with the authority and the lease protocol. Not a delete, not a force-release.
5. **`flock -n` probe creates a file.** This is a deliberate host write (the normal lease file), not a
   read-only probe; only run it after the move, and only with the `[ -e ]` guard the unit implies.
6. **Login-session write.** Any SSH login may rewrite `~/.local/state/wireplumber/restore-stream` (census
   m-4); it is outside all scoped paths. The unit should scope its “read-only” wording accordingly (m-1,
   m-10).
7. **STOP after the move.** If a STOP occurs after `mv` (e.g. moved-file verification), the canonical
   `gpu0.lock` path may be absent until a reviewed follow-up recreates it; the moved file is preserved and
   no retry is allowed without a new reviewed unit. This is the intended fail-closed behavior; note it in
   the STOP record.
8. **The historical holder/time is only recoverable from preserved logs** (m-12); record it now, while the
   logs are intact.

## 9. Explicit statements

- **“No holder.”** As of 2026-11-16 09:48–09:52Z, `~/r1_locks/gpu0.lock` (inode 120090387, 0 B, sha256
  `e3b0c442…`) is **not held**: no `/proc/locks` entry for device:inode `103:02:120090387`, no `lslocks`
  entry, no `dowling` experiment/Track process, no tmux server, no GPU compute app, and the lease is
  acquirable (`flock -n` rc 0, file unchanged). The unit's “Holder: none” is correct, and “release only if
  no owner process exists” is satisfied. The last known holder (12 Nov S0.5, pid 1386618) is dead and is
  not recorded in the unit (m-12).
- **“Nothing deleted.”** This review deleted nothing (no `rm`/delete by any command; the only host access
  was read-only plus one transient acquire/release `flock` probe that changed no byte, inode or mtime). The
  unit's procedure also deletes nothing: it only creates `_to_delete/`, renames the old lock into it and
  creates a fresh empty `gpu0.lock`; the old file is preserved and verified by inode/size/sha. Nothing was
  committed, pushed or checked out in git; this review file is untracked.
- **Execution gate.** The unit may be executed **only after this review is accepted and recorded** (unit
  §6 requires a review before execution). The reviewed bytes are the committed unit at `eb65ac4f`, sha256
  `e0efc29fd63b12b95ddc4010b4dd123f0d51259a27070d361c4924a062bb9be3`. If the unit is edited after this
  review, the changed procedure/safety bytes require a fresh review; the MINOR items above are
  recommendations to fold into the operator record, not preconditions.

## 10. Final verdict

**Verdict: accepted.**

BLOCKING: none. MAJOR: none. MINOR: m-1 … m-13.

The unit is authority-compliant, fail-closed, and safe to run exactly as written: it records the stale
lock (inode 120090387, 0 B, sha `e3b0c442…`, mtime/ctime 2026-10-25, no holder, no marker, no tmux, lease
acquirable), re-checks that no owner process exists, moves the old file into `~/r1_locks/_to_delete/` with
`mv -n` (nothing deleted, no force, no signal), verifies the moved inode/bytes, and restores a fresh empty
lease file at the canonical path. Independent read-only verification reproduced every recorded fact and
confirmed the scene is preserved, the census review is accepted (`a00cf7a2…`) and the deferred bare push
reached `fab88fce`. The thirteen MINOR findings are recording/hardening items (read-only wording,
timestamp format, symlink/`_to_delete` checks, exact patterns/paths, STOP-list coverage, must-not wording,
record fields, and the last-known-holder line); they should be folded into the execution record and the
next unit revision, and none blocks this acceptance.

*End of review.*
