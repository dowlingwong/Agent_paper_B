# Independent review — TASL-2 read-only census (R1-TRACKS-STOP4-CONSEQUENCES item (4)) — 15 November 2026

**Reviewer role.** Fresh, independent, read-only reviewer, spawned for this exact question. Not the author,
not the B2 executor, not the operator who ran the census. This review did not execute the census unit, did
not execute the TASL-7 stop unit, and did not commit, branch, tag or push. The only repository file written
is this review (untracked). No lock was released, no process was started/stopped/signalled, and no file was
created or removed in the Track S scene on TASL-2. Read-only SSH to TASL-2 (`ssh portal_zhixu`, user
`dowling`) was used only for the live comparison in §5; the one non-command side effect of those logins is
disclosed in §4.3.

**Verdict: accepted.** The capture is complete, internally consistent and hash-verified; the remote command
set is read-only; the Track S scene, the lock file and the bare repo are untouched; no process, lease,
listener or git ref was changed. The deferred `trackS-ops-20261030` push is still owed (live TASL-2 tip
`25907343`, 52 commits behind `fab88fce`, a fast-forward) and remains a separate, later, reviewed step.
Findings are **MINOR** only (§8); none changes the ruling-(4) outcome.

---

## 1. Authority, unit and provenance

**Authority.** The author rows are on `origin/author-stop4-20261115` @ **`1f5f24e3`**
(`docs/r1/PLAN.md` §10, lines **1165** and **1171**). Item (4) of `R1-TRACKS-STOP4-CONSEQUENCES` (L1171)
reads, verbatim: “TASL-2 同样从 Track S 释放，但须在其恢复联网后先由实验 agent 只读清点（Track S
服务器、GPU lease、进程），清点经审查后才可另作他用；两台主机上的 Track S 现场保持不动。” The
operative parts are: a **read-only inventory** of Track S servers, the GPU lease and processes after the
network returns; the inventory goes to **review before any other use**; the Track S scene on both hosts
stays untouched. The task's added “nothing is resumed, no lock is released” is consistent with that row and
with the operator NOTE; it is not contradicted by anything in the capture.

**Accepted census unit.** `docs/r1/reports/b2_exec_20261115/trks_stop/tasl2_readonly_inventory.sh`
at **`83b9c80b`**, SHA-256 **`0f7149c5593cc0fff1c7c322db2c8aa6605d4198f37b80b7da32373d9f1704da`**
(git blob `45a2e4b9…`, 1357 B, `bash -n` clean). The same bytes are at the current exec tip
`b46f4509` (`origin/ops-b2-exec-20261115`) and at `d022bf64`.

**Acceptance review.** `docs/r1/reviews/B2_TRKS_STOP_UNITS_REVIEW_20261115.md`, SHA-256
**`1c0251c705c33bfa18c7110d4324dfa9f98051f64a965fdae6baaff35a22c5cc`** (592 lines; committed by
`099dbdfd`, 2026-11-15 21:04:21 +0100 = 20:04:21Z). Its round-2 final verdict (§6.8) is **Accepted** with
non-blocking minors m-10…m-20 (the accepted review's numbering). The accepted review's m-10 is the
operative precondition: the `flock -n` probe on `~/r1_locks/gpu0.lock` must not be run if the file is
absent, because `flock(1)` would create it; the operator says it was confirmed present (`LOCK_PRESENT`).
Its m-11 notes the probe's recorded `rc` is the rc of the label `echo`, not of `flock`.

**Timeline (all UTC unless marked).**

| Time | Event | Evidence |
|---|---|---|
| 2026-11-15 20:03:52Z | accepted review file written | file mtime 21:03:52 +0100 |
| 2026-11-15 20:04:21Z | `099dbdfd` records the acceptance | commit date 21:04:21 +0100 |
| 2026-11-15 20:51Z | TASL-2 reboot | live `last -x`: reboot Sun Nov 15 12:51 local (UTC-8) |
| 2026-11-15 21:10:38Z | census request written | `request.txt` |
| 2026-11-15 21:10:40Z | reachability ssh returns 0 | `reachability.rc` |
| 2026-11-15 21:10:43Z | inventory capture complete (Mac mtime) | `inventory.txt` mtime 22:10:43 +0100 |
| 2026-11-15 21:11:14Z | remote `date -u` header (host clock; see m-1) | `inventory.txt` L1 |
| 2026-11-15 21:12:46Z | live read-only re-check | this review §5 |

The unit was accepted **before** it was run; the run happened only after TASL-2 became reachable. The
inventory is now under review before any other use, which is exactly item (4)'s order.

**Capture.** `/private/tmp/tasl2-census-20261115T2111Z/` (mode `drwx------`, files `-rw-------`, owner
`wongdowling:wheel`). It is the only `tasl2-census-*` directory under `/private/tmp` (the macOS `/tmp`
symlink resolves there); no other copy was found in the checked paths.

---

## 2. Capture integrity

`shasum -a 256 -c SHA256SUMS` in the capture directory: **all four files OK**.

| File | Bytes | SHA-256 | mtime (+0100) |
|---|---:|---|---|
| `request.txt` | 69 | `13f76f703074deea3dcd4bb171b0218f5bd97397c4254ca4fef72caa4b4ac060` | 22:10:38 |
| `reachability.rc` | 9 | `d88f87c504c9acad5c9a0a724bdb4170d221cebd03f6c10267426f555ac1933f` | 22:10:40 |
| `inventory.rc` | 19 | `3691e32aade5d9f5b5500654a028df7a2896f33076a5fe9a10acd65e247fa406` | 22:10:43 |
| `inventory.txt` | 8257 | `b5c737c542e82c560e822a2f56dca5eef5037b409bf635dd5a9195ca61b2c658` | 22:10:43 |
| `SHA256SUMS` (not self-listed) | 319 | `2189cdaa8606b6d2bc0dd017639f83da6011d438fb9087740bf863b8856b1832` | 22:10:43 |

- `request.txt`: `inventory_requested_utc=2026-11-15T21:10:38Z`, `host_alias=portal_zhixu`.
- `reachability.rc`: `ssh_rc=0`. `inventory.rc`: `inventory_ssh_rc=0`. No `UNREACHABLE.txt` exists.
- Host/user: `host=TASL-2 utc=2026-11-15T21:11:14Z` (L1); `uid=1008(dowling) gid=1008(dowling)` (L4).
  The alias resolves correctly: `ssh -G portal_zhixu` → `user dowling`, `hostname 100.120.160.70`,
  `port 22`. The live host confirms `hostname` = TASL-2 and `id` = dowling (§5).
- Uptime/reboot: L7 `13:11:14 up 19 min, 0 users` — the host timezone is **UTC-8**, so 13:11:14 local is
  21:11:14Z; boot ≈ 20:52 host time. The live `last -x` records `reboot … Sun Nov 15 12:51` local
  (20:51Z), and the live uptime at 21:12:46Z is 21 min (boot ≈ 20:51:46Z). The 19-min/reboot pair is
  consistent within the minute. This is a genuine post-reboot census, not a stale session.
- The 31 s difference between the host header (21:11:14Z) and the Mac file mtime (21:10:43Z) is a
  post-reboot clock skew, not an inconsistency in the capture's own logic; the host `date`, `uptime` and
  the `last -x` reboot agree with each other. The 21:12:46Z live header is consistent with the Mac-side
  call time (21:12–21:13Z), so the skew looks like a post-reboot transient rather than a capture defect.
  See m-1.

**Per-command rc.** `inventory.txt` has 15 `rc=` lines: one for each of `id`, `uptime`, `tmux ls`,
`nvidia-smi` GPU, `nvidia-smi` compute apps, `ls r1_locks`, `pgrep` Track S, `pgrep` exam/llama, `ss`,
`ls out`, `find out`, `ls logs`, `df`, `free`, plus the lease probe's `rc=`. Every command emitted an rc;
the only error text is `tmux ls`'s expected “no server” message, which is itself the evidence of no tmux
server. The probe's `rc=0` is nevertheless the rc of the preceding `echo`, not of
`flock` (m-2, inherited from the accepted review's m-11). The `LEASE_FREE` label itself is correct and the
live check independently confirms `flock -n … gpu0.lock` returns 0 and `lslocks` has no `gpu0` entry.

---

## 3. Full inventory — what the capture actually shows

The whole 152-line file was read, not just the head. The section order matches the accepted unit's
heredoc exactly (`user/host`, `tmux`, `gpu`, `gpu compute apps`, `r1_locks`, lease probe, Track S
processes, exam/llama, listeners, output trees, run logs, disk/mem), which is how the executed bytes are
identified as `0f7149c5…` and not the older round-1 script.

| Section (capture lines) | Observed | Assessment |
|---|---|---|
| user/host (L2–L8) | `dowling`; `13:11:14 up 19 min, 0 users`, load 0.87/0.33/0.18 | correct host/user; post-reboot |
| tmux (L9–L12) | `error connecting to /tmp/tmux-1008/default (No such file or directory)`, `rc=1` | **no tmux server and no session** |
| GPU (L13–L16) | `0, GPU-4d623e76-7587-ee15-a633-46f60d220d94, 353 MiB, 24564 MiB, 0 %` | correct uuid, **idle**; 353 MiB is display/GDM overhead |
| GPU compute apps (L17–L19) | empty, `rc=0` | **no compute app / no Track S server** |
| `~/r1_locks` (L20–L26) | only `.`, `..`, `gpu0.lock` (0 B, mtime Oct 25 21:35) | **only the expected lock**, unchanged |
| lease probe (L27–L30) | `LEASE_FREE` | **lease free**; no holder |
| Track S processes (L31–L33) | no output, `rc=1` | **none** (`r1.tracks`, `trks_llm`, `trks-watch`, `trks_watch`) |
| exam/llama (L34–L36) | no output, `rc=1` | **none** (`exam_runner`, `llama-server`) |
| listeners (L37–L51) | 22, 6868, 53 (systemd-resolve), 9091, tailscale 61040/59939, 631, 80, 127.0.0.1:42383 | **no 18101/18102**; 42383 is an extra localhost-only listener (m-5) |
| output trees (L52–L75) | `digits_mlp` + `smoke` only; 11 subdirs under `digits_mlp` | matches TASL-2's scene; TASL-7's `tabular_mlp` dirs are correctly absent |
| run logs (L76–L141) | `watch.log` 360 B; `llama_18101.log` 587 MB (Nov 12 12:14); `llama_18102.log` 394 MB (Nov 8); `s05_20261112_launch.log` 623 B; many `trks_s*` logs; `watch_started` 0 B | listing preserved; no post-outage activity |
| disk/mem (L142–L151) | `/dev/nvme0n1p2` 1.9T, 1.4T used, 375G avail, 79%; 62G RAM, 2G used, 57G free, 1G swap | correct; 79 % disk is the residual capacity risk |

This covers exactly what ruling (4) names: **Track S servers** (tmux + `pgrep` + port scan), **GPU lease**
(`ls` of the lock directory plus the `flock -n` probe plus the GPU compute-app list), and **processes**
(Track S, `exam_runner`, `llama-server`). It also records the output trees, logs and host capacity. The
one scope omission is a per-scene `manifest.json`/`STOP` list (m-6); ruling (4) does not require it, and
the live check in §5 supplies it.

---

## 4. Read-only compliance and scene preservation

### 4.1 Static analysis of the executed unit

The accepted unit's remote heredoc (L25–L43) issues only: `hostname`, `date -u`, `id`, `uptime`,
`tmux ls`, two `nvidia-smi --query-*`, `ls -la /home/dowling/r1_locks`, `flock -n
/home/dowling/r1_locks/gpu0.lock true`, `pgrep -a -f` (two patterns), `ss -ltnp`, `ls -la` of
`r1_tracks/out` and `r1_tracks/logs`, `find … -maxdepth 2 -type d`, `df -h`, `free -g`. There is **no**
`rm`, `unlink`, `truncate`, `find -delete`, `find -exec`, `touch`, `tee`, `mkdir`, `cp`, `mv`, `chmod`,
`chown`, `dd`, `pkill`, `killall`, a bare `kill`, `systemctl`, a service command, a reboot, a `git`
command, or a push. The only remote redirections are `2>&1` inside the `r()` helper (stderr to stdout,
not to a file). All local redirections write only under the newly created `$OUT_DIR`; the local
`mkdir -m 700` and the `SHA256SUMS`/`sha256sum -c` run on the Mac, not TASL-2.

The only remote file **open** is the `flock -n` probe on the existing `gpu0.lock`. The file was present
(the m-10 precondition): capture L25 shows `-rw-rw-r-- … 0 Oct 25 21:35 gpu0.lock`; live `stat` shows
`size=0 mtime=2026-10-25 21:35:24.275265604 -0700 ctime=…`. The probe cannot change the content, size,
mtime or ctime of an existing file; it only takes and immediately drops an advisory lock that nobody
held. There was no lease to release: `lslocks` has no `gpu0` entry and `flock -n` returns 0.

### 4.2 Scene preservation

The captured scene paths and mtimes are pre-outage, not census-time:

- `~/r1_tracks/out`: directory mtime Oct 30 03:13; `digits_mlp` Nov 12 11:55; `smoke` Nov 8 17:29.
- 11 subdirectories under `digits_mlp` (`s01`, `s01_diag`, `s01_diag_f1`, `s01_diag_f2`,
  `s01_rerun20261109`, `s01_rerun_INVALID_serial_raced_server_start_20261031T112159Z`, `s04`,
  `s04_r2_20261111`, `s05`, `s11`, `inputs`) — all present in the live check, same set.
- `~/r1_tracks/logs`: `watch.log` 360 B (last line 2026-11-09T01:29:08Z), `watch_started` 0 B,
  `llama_18101.log` 587 MB (Nov 12 12:14), `llama_18102.log` 394 MB (Nov 8 16:34),
  `s05_20261112_launch.log` (Nov 12 11:56). No post-outage writes.
- `~/r1_locks`: only `gpu0.lock`, 0 B, mtime Oct 25 21:35; directory mtime Oct 25 21:35. No new file.

The live check (§5) found the same directory set and the same four `manifest.json` files
(`s05` 2707 B, `smoke` 3939 B, `s04_r2_20261111` 3976 B, `s04` 6776 B) with their Nov 8–12 mtimes. No
`STOP` file exists anywhere under `out` (live `find -iname '*stop*'` returned nothing). The 9 Nov STOP 3
scene (`s04`) is preserved as its output tree; `watch.log` records the 9 Nov stop and the “marker gone:
resume by hand (delete STOP files, …)” instruction. The live tree has no STOP file, which is consistent
with a post-9-Nov cleanup, but the capture/log does not prove who removed them; treat `s04` as preserved
output, not as a live STOP-paused scene. The 12 Nov
S0.5 scene (`s05`) is a partial pre-crash run (`manifest.json` 19:56Z, `roots.jsonl` 20:14Z) with no STOP
and no process; it is preserved and must not be resumed.

### 4.3 No writes attributable to the unit's commands

The only new path under `/home/dowling` observed after 21:05Z was the wireplumber state path: its
directory mtime was 21:11:06Z during the census window, and my own logins wrote
`/home/dowling/.local/state/wireplumber/restore-stream` (205 B) at 21:12:47Z and 21:13:02Z. This is a
**PipeWire/wireplumber desktop-session state file**, not a Track S path, not `~/r1_locks`, not a marker,
not the bare repo, and not produced by any command in the unit. It is written because the SSH login
activates the `dowling` systemd user session (`loginctl` shows a `dowling` session and a GDM session;
`systemctl --user` shows `pipewire.service`/`wireplumber.service` running). This is an environmental
side effect of any SSH login on this host, not a census command write. It is disclosed here for
completeness (m-4).

The unit itself contains **no** git command, so it cannot push or fetch. The deferred bare-repo push was
not performed by the census, and §7 shows it is still owed.

### 4.4 Capture locality

The capture exists only under `/private/tmp/tasl2-census-20261115T2111Z/` on the Mac, mode 700/600, and
no other `tasl2-census-*` path exists. Nothing was written on TASL-2 for the capture; the inventory was
streamed to the Mac's local `$OUT_DIR`. The only host-side effect of the census was the login-session
artifact in §4.3.

---

## 5. Live host re-check (read-only, 2026-11-15T21:12:46Z)

`ssh portal_zhixu` with read-only commands only; no files created **by the commands** (the login-session
artifact in §4.3 is the only host-side effect), no process/lock/ref touched. The live values match the
capture; **no material drift**.

| Item | Capture (21:11:14Z host) | Live (21:12:46Z) | Drift |
|---|---|---|---|
| host/user | TASL-2 / dowling (uid 1008) | TASL-2 / dowling (uid 1008) | none |
| uptime | up 19 min, 0 users | up 21 min, 0 users; load 0.21/0.25/0.17 | expected +2 min |
| tmux | `tmux ls` rc=1, no socket | same rc=1, no socket | none |
| GPU | `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, 353 MiB, 0 % | same uuid, 353 MiB, 0 % | none |
| GPU compute apps | empty, rc=0 | empty, rc=0 | none |
| `r1_locks` | only `gpu0.lock`, 0 B, Oct 25 21:35 | only `gpu0.lock`, 0 B, size 0, mtime 2026-10-25 21:35:24 -0700 | none |
| lease | `LEASE_FREE` (probe) | `lslocks` no `gpu0` entry; `flock -n` rc=0 | none |
| Track S processes | none, rc=1 | none, rc=1 | none |
| exam/llama | none, rc=1 | none, rc=1 | none |
| listeners | 22, 6868, 53, 9091, tailscale 61040/59939, 631, 80, 42383 | identical set | none |
| `out` trees | `digits_mlp` + `smoke`, 11 subdirs | identical set | none |
| manifests | not listed by the census | 4: `s05`, `smoke`, `s04_r2_20261111`, `s04` (2707/3939/3976/6776 B) | added evidence |
| STOP files | not listed | **none** under `out` (`find -iname '*stop*'` empty) | m-6 |
| disk/mem | 1.4T/375G/79%; 62G/2G/57G/1G | identical | none |
| logs | `watch.log` 360 B; `llama_18101.log` 587 MB; `s05` launch Nov 12 | paths present; `watch.log` and `s05`/`trks_s05` tails read (last activity 12 Nov; watch.log last line 2026-11-09T01:29:08Z); full sizes not re-stat'ed | none |

Additional live evidence:

- `last -x`: `reboot … Sun Nov 15 12:51` local (20:51Z), previous logins Nov 12 11:56 (the crash), so
  the host was down from 12 Nov to 15 Nov. This is consistent with the outage record and the reboot.
- `s05` launch log: `2026-11-12T19:55:59Z … starting fresh server k=1 in tmux session trks_llm`,
  `server pid: 1386618`, `lease: HELD`, `starting S0.5 collector in tmux session trks_s05`. Today there is
  no `trks_llm`/`trks_s05` session, no server pid, and the lease is free: the crash/reboot cleared them.
- `watch.log`: last line `2026-11-09T01:29:08Z marker gone: resume by hand (delete STOP files, start
  servers, re-run launch scripts)`; no entries after 9 Nov. The TASL-2 watcher did not log during the
  12 Nov S0.5 attempt, and no tmux server exists now.
- `loginctl` shows a `dowling` session (my SSH) and a GDM session; `systemctl --user` shows
  `pipewire`/`wireplumber` running — the source of the §4.3 state file.
- The extra listener `127.0.0.1:42383` is localhost-only and not 18101/18102; `ss -p`/`lsof` did not
  identify the owner under the unprivileged check. It is not Track S, but it is unexplained (m-5).

**Inconsistencies/missing elements/write evidence.** No material capture-vs-live inconsistency. Minor
ones: the 31 s host-clock skew at capture (m-1), the probe's misattributed `rc` (m-2), the missing
per-scene manifest/STOP list (m-6), the unidentified 42383 listener (m-5), and the login-session
`wireplumber` write (m-4). No evidence of a census **command** writing on TASL-2.

---

## 6. Ruling (4) fit

| Requirement (item (4) / task) | Result | Evidence |
|---|---|---|
| Read-only inventory of Track S **servers** | **Met** | `tmux ls` (no server), `ss -ltnp` (no 18101/18102), `pgrep` (no `trks_llm`/`trks-watch`/`r1.tracks`) |
| Read-only inventory of the **GPU lease** | **Met** | `ls ~/r1_locks` (only `gpu0.lock`, 0 B), `flock -n` → `LEASE_FREE`, `nvidia-smi --query-compute-apps` empty, GPU idle |
| Read-only inventory of **processes** | **Met** | `pgrep` Track S and `exam_runner|llama-server`, both rc=1/no output |
| Inventory goes to **review before any other use** | **Met** | unit accepted 20:04Z; census 21:10Z; this review; no post-census use on the host |
| **Scene untouched** (TASL-2; TASL-7 out of scope) | **Met for TASL-2** | 4 manifests + 11 subdirs + logs preserved; no STOP; no post-outage mtimes; TASL-7 is out of scope here and its stop unit was not executed |
| Nothing resumed | **Met** | no tmux, no Track S/exam/llama process, no GPU compute app |
| No lock released | **Met** | `gpu0.lock` 0 B, same mtime; `lslocks` no holder; probe only |
| No start/stop/signal | **Met** | unit contains none; live state unchanged |
| Deferred push only **after** this review | **Met / still owed** | no push performed; §7 |

The accepted review's m-10 precondition is satisfied by the evidence: the lock file was present before
the probe (capture L25) and is present now (live `stat`, 0 B). The literal token `LOCK_PRESENT` is not
recorded in the capture or the repo; the fact it asserts is independently established (m-3). The capture
does not record a pre-run `[ -f … ]` check, so the unit still relies on the operator having confirmed it;
that remains a non-blocking hardening item, not a reason to reject this run.

---

## 7. Deferred `trackS-ops-20261030` bare-repo push — ref delta

Read-only `git ls-remote` (no fetch, no push, no ref update):

| Ref | Tip | Source |
|---|---|---|
| TASL-2 bare repo `refs/heads/trackS-ops-20261030` | **`25907343728fe48fbe9f1543b6b3a0921eb7012d`** | live `git ls-remote tasl2` |
| `origin` `refs/heads/trackS-ops-20261030` | **`fab88fced839c5fb794ed62a0742b4646cb76ea2`** | live `git ls-remote origin` |
| Mac local `trackS-ops-20261030` | `fab88fced839c5fb794ed62a0742b4646cb76ea2` | `git show-ref` |
| Mac remote-tracking `refs/remotes/tasl2/trackS-ops-20261030` | `78a1b65e05edc8ab92f04f19f3fa7d4fbcec4b11` (stale) | `git show-ref` |
| TASL-2 other head `mac-tracks-a2u-stale-20261111` | `c8b13b5d63d3d30f5afa642928f1458e863e8935` | live `git ls-remote tasl2` |

- `25907343` **is an ancestor of** `fab88fce`; `git rev-list --left-right --count
  25907343...fab88fce` = **0 52**. The push is a clean **fast-forward of 52 commits**, no force, no
  divergence.
- The live TASL-2 tip is **2 commits ahead** of the stale remote-tracking ref `78a1b65e`:
  `24765b2b` (“restore the reviewed S0.4 rerun record; retire the duplicate copy-back”) and `25907343`
  (“S0.5 launch script (L1 Phase 4)”, 2026-11-12 20:54:50 +0100). The resources/scenes record's “54
  commits behind” (`docs/r1/reports/TRACKS_RESOURCES_AND_SCENES_20261115.md` §2.2 L105 and §3 L140, at
  `0a1e1088`) is based on that stale ref; the correct live delta is **52**. See m-7.
- The census did **not** push, fetch or run any git command on TASL-2. The push remains owed and is a
  separate, later, author-authorized step. This review does not perform or authorize it; it records that
  the item (4) review gate is now satisfied.

---

## 8. Findings

**BLOCKING: none.**

**MAJOR: none.**

All findings are **MINOR** (recording, hardening or residual-risk notes); none invalidates the census,
the read-only character of the command set, or the scene-preservation conclusion.

### m-1 — Host/Mac clock skew at capture; the host header is 31 s ahead of the Mac file mtime
`inventory.txt` L1 says `utc=2026-11-15T21:11:14Z`; the Mac `inventory.txt` mtime is 21:10:43Z. The host's
`uptime` (19 min) and the live `last -x` reboot (20:51Z) are consistent with each other, and the
21:12:46Z live check shows the host clock in step with the Mac-side check (21:12–21:13Z), so this is a
post-reboot clock step, not a data inconsistency. It is worth recording because a reader comparing the
header to the file mtime could think the capture was back-dated. *Hardening:* record the Mac-side start/end time in `request.txt` too, or note the skew in the
operator record.

### m-2 — The lease probe's recorded `rc=0` is the rc of the label `echo`, not of `flock`
`inventory.txt` L27–L30; accepted unit L34. The `LEASE_FREE` label is correct (the `&&` branch ran), and
the live check independently shows `flock -n` rc=0 and no `gpu0` entry in `lslocks`, so the lease
conclusion is sound. This is the accepted review's m-11, still present in the executed bytes.
*Hardening:* `flock -n … true; frc=$?; echo "rc=$frc"; [ "$frc" -eq 0 ] && echo LEASE_FREE || echo
LEASE_HELD`.

### m-3 — The accepted review's `gpu0.lock`-present precondition is not itself recorded
The review's m-10 requires confirming the file exists before the probe; the operator says `LOCK_PRESENT`.
The capture shows the file (L25) and the live `stat` confirms it (0 B, mtime 2026-10-25 21:35:24 -0700),
so the precondition held. But there is no separate `LOCK_PRESENT` token/artifact in the capture or the
repo; the claim is only inferable from the `ls` line. *Hardening:* add a `[ -f … ]` guard in the unit (the
accepted review's recommended fix) and record the check's rc; or record `LOCK_PRESENT` in
`request.txt`/`reachability.rc`.

### m-4 — “No writes on TASL-2” is imprecise: the SSH login writes a desktop-session state file
The unit comment (L3) and NOTE (`tasl2_readonly_inventory.sh` section) say “no file writes on TASL-2”.
The command set is read-only, but the login starts the `dowling` systemd user session and
`wireplumber.service` writes `~/.local/state/wireplumber/restore-stream` (205 B; directory mtime
21:11:06Z during the census, and 21:12:47Z/21:13:02Z during my own read-only logins). This is outside
`~/r1_locks`, `~/r1_tracks`, the marker and the bare repo; it does not change the scene or the lease, and
it is not caused by any command in the unit. It is unavoidable with a normal SSH login on this
GDM/PipeWire host. *Hardening:* scope the claim to “no writes to the Track S scene, locks, marker or
repo; the SSH login may touch desktop user-session state under `~/.local/state`”.

### m-5 — Unidentified localhost listener `127.0.0.1:42383`
`inventory.txt` L50; live `ss -ltnp` shows the same. It is localhost-only, not 18101/18102, and not
Track S. `ss -p`/`lsof` under the unprivileged check did not identify the owner. It could be a
remote-dev/desktop service, but it should be identified before any other use of the host. The census
correctly records it; the omission is identification, not capture.

### m-6 — The census does not list `manifest.json`/`STOP` per scene
The census lists directories (`ls -la out`, `find -maxdepth 2 -type d`), logs, disk and memory, but not
the per-scene manifest/STOP inventory (the accepted review's m-17). Ruling (4) names servers, lease and
processes, so this is optional; the live check in §5 supplies the missing evidence (4 manifests, no
STOP). *Hardening:* add a read-only `find … -name manifest.json -printf …` / `-name STOP` listing to the
unit. This would also have made the “no STOP files” fact part of the capture rather than a follow-up.

### m-7 — The resources/scenes record's push delta is stale; the live TASL-2 tip is 2 commits further
`docs/r1/reports/TRACKS_RESOURCES_AND_SCENES_20261115.md` §2.2 (L105) and §3 (L140), at `0a1e1088`, say
`tasl2/… = 78a1b65e`, 54 commits behind `fab88fce`. The live bare repo is at `25907343` (2 commits
ahead: `24765b2b`, `25907343`), so the true fast-forward delta is **52**, and the Mac's
`refs/remotes/tasl2/trackS-ops-20261030` is stale at `78a1b65e`. This does not affect the census, but the
deferred-push note must use the live tip. *Action:* update the resources record (or make the push unit
read `git ls-remote` live); do not rely on the cached ref.

### m-8 — `pgrep` rc=1 is the only “none” signal; rc=1 vs rc=2 is not distinguished
`inventory.txt` L31–L36. The unit's `r()` prints `rc=1` for no match, but `pgrep` also returns 2 on a
usage error; there is no “none” label and no error-text check. In this capture there is no error text, so
the interpretation is sound. *Hardening:* print `none` when rc=1 and stop if rc=2, or use `pgrep … ||
[ $? -eq 1 ]`.

### m-9 — Localized output (`总计`, `组`, `文件系统`, `内存`, `交换`)
`inventory.txt` L4, L22, L78, L144, L148. The remote locale is Chinese, so the labels are localized; the
numeric values are correct and unambiguous. A parser expecting `total`/`Filesystem`/`Mem` would fail.
*Hardening:* `export LC_ALL=C` at the top of the remote heredoc for deterministic output.

### m-10 — The operator NOTE still says the census is “not executed”; the capture is only in `/private/tmp`
`docs/r1/reports/b2_exec_20261115/trks_stop/NOTE.md` at `b46f4509` still says “prepared for independent
review; not executed” and “strictly read-only … no writes on TASL-2”. That was true when the NOTE was
written (`83b9c80b`, 19:54Z) and at the `b46f4509` tip (20:50Z), but the census has since run. The capture
is not in the repo; it exists only under
`/private/tmp`. *Action:* after this review, update the operator record with the execution time, the
capture hashes and the acceptance, and preserve the capture (copy it into the repo or an archive) before
`/private/tmp` is cleaned. This is a durability/record issue, not a census defect.

### m-11 — An unmerged branch contains a different, weaker census unit (repository-side note)
`ops-b2-exec-round13-unmerged` @ `69391b29` has `tasl2_readonly_inventory.sh` at
`4a6bf5e0aa4ff59f98fd224b39018c14988fd3372c495069b1f49cca5f8fe857` — a variant that lacks the `tmux`,
`flock` lease-probe, `ss` and `find`/logs sections. It is not the exec tip (`b46f4509`), was not used for
this census, and must not be merged over the accepted unit without a fresh review. Recorded so the
author does not mistake it for the accepted bytes.

### Note (not a finding) — no STOP files on TASL-2
The task's residual-risk prompt anticipated “old STOP files”. The live check found **none** under
`~/r1_tracks/out` (`find -iname '*stop*'` empty). The 9 Nov STOP 3 scene (`s04`) is preserved as its
output tree, and `watch.log` records the 9 Nov stop plus the “delete STOP files” resume instruction; the
12 Nov S0.5 `s05` scene is a partial pre-crash run with no STOP. So the author/reviewer does **not** need
to remove stale STOP files on TASL-2; the risk is the opposite — the partial `s05` scene must not be
resumed.

---

## 9. Residual risks and what the author/reviewer should know before any other use

1. **The reboot erased pre-reboot process/lease state.** Uptime 19 min at capture; `last -x` reboot
   20:51Z. The 12 Nov S0.5 server (pid 1386618) and collector are gone; `gpu0.lock` is a plain 0 B file,
   not a held lease. The capture can prove the post-reboot state and that the scene files survived; it
   cannot prove what the pre-reboot lease holders were. The scene is the only trustworthy pre-outage
   state.
2. **The S0.5 scene is partial and must not be resumed.** `s05/manifest.json` (19:56Z), `roots.jsonl`
   (20:14Z), `audit_runs.jsonl`/`s05_calibration.jsonl` (20:12Z) are pre-crash fragments. No STOP marks
   them; the “resume by hand” instruction in the old `watch.log` does not apply. Any future use must
   treat `s05` as an incomplete engineering-only run and must not re-run or overwrite it.
3. **The `s04` 9 Nov STOP 3 scene is preserved as output but has no STOP file.** The resources doc's
   “STOP scene” label is historical; do not expect a STOP marker to delete.
4. **No Track S watcher/server is running on TASL-2 now.** `tmux ls` rc=1, no `trks_llm`/`trks-watch`,
   no 18101/18102, no GPU compute app. The `watch.log` last line is 9 Nov. Nothing needs stopping.
5. **The lease is free and the lock file is unchanged** (0 B, mtime Oct 25 21:35:24 -0700). The census's
   `flock -n` probe did not release a held lease; it acquired and dropped an unheld advisory lock.
6. **The only host write observed is the login-session `wireplumber` state file** (205 B), outside the
   scene; the census command set wrote nothing. If the author requires literal zero host writes, the
   census must be run in a way that suppresses the systemd user session (or the record must scope the
   claim as in m-4).
7. **Disk is 79 % used** (1.4T/1.9T, 375G free) and the old llama logs are ~1.5 GB; the census does not
   change this, but any future use should account for it.
8. **The capture is a point-in-time snapshot** (21:10:43Z Mac / 21:11:14Z host). The live check at
   21:12:46Z matches, but future changes are not covered by this review.
9. **The deferred push is a 52-commit fast-forward** from `25907343` to `fab88fce`. It is still owed and
   must be a separate, reviewed, author-authorized step; this review does not push and does not release
   the bare repo for arbitrary writes.
10. **The capture lives only in `/private/tmp`.** Preserve it (copy into the repo or an archive) before
    the temporary directory is cleaned; the hashes in §2 are the integrity anchor.
11. **The exec worktree is detached at `5c3ff87a`**, so the on-disk `tasl2_readonly_inventory.sh` hashes
    to the round-1 `c9746098…`, not the executed `0f7149c5…`. Verify the unit with `git show
    83b9c80b:docs/r1/reports/b2_exec_20261115/trks_stop/tasl2_readonly_inventory.sh` (or check out the
    accepted commit), not with a bare `sha256sum` in this worktree. This is the provenance note in §6.0
    of the earlier review; it remains true.
12. **The host clock was ~31 s ahead at capture** (m-1). If a later workflow correlates the census with
    Mac-side logs, use the host header and the reboot pair, not a strict equality of the two clocks.

---

## 10. Final verdict

**Verdict: accepted.**

The accepted unit `0f7149c5…` (`83b9c80b`) was run after its review was accepted (`1c0251c7…`,
`099dbdfd`), and the capture in `/private/tmp/tasl2-census-20261115T2111Z/` is complete and
hash-verified: `SHA256SUMS` verifies for all four files, `reachability.rc=0`, `inventory.rc=0`, the host
is TASL-2 and the user is `dowling`, the timestamps/uptime are consistent with a 20:51Z reboot, and every
command's rc is recorded. The full inventory shows no tmux server/session, the expected GPU uuid idle with
no compute apps, only `gpu0.lock` (0 B) in `~/r1_locks`, `LEASE_FREE`, no Track S/exam/llama process, no
18101/18102 listener, and the preserved `digits_mlp`+`smoke` output trees, logs, disk and memory. The
remote command set contains no write, start/stop/signal, lock release, git or push; the only remote file
open is the `flock -n` probe on the existing lock, which left it unchanged. The live read-only re-check at
21:12:46Z matches the capture (no material drift) and the scene is preserved (4 manifests, 11 subdirs, no
STOP, pre-outage mtimes). The only host write observed is the SSH-login `wireplumber` state file outside
the scene (m-4), not a census command.

The item (4) gate is therefore satisfied: the inventory exists and is reviewed before any other use;
nothing was resumed, no lock was released, no file in the scene was moved/changed/deleted, and no push was
made. The deferred `trackS-ops-20261030` push remains owed and is a clean 52-commit fast-forward from the
live TASL-2 tip `25907343` to `fab88fce`; it should be considered only as a separate, reviewed step after
this acceptance, and must not use the stale `78a1b65e`/“54 behind” cache. The MINOR findings m-1…m-11
(clock-skew note, probe rc, lock precondition recording, login-session write scoping, 42383 listener,
manifest/STOP listing, stale push delta, `pgrep` rc, localized output, stale NOTE/capture durability,
unmerged round-13 branch) should be folded into the operator record and the next unit revision; none is a
condition on this acceptance.

*End of review.*
