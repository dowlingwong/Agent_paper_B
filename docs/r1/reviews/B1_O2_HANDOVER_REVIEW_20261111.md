# Independent review — B1 restart O2 handover, marker transition, STATUS publication and launch (run `fffa_20261111_b`, 11 Nov 2026)

**Reviewer.** Freshly spawned independent reviewer; did not write this unit. Read-only on `tasl7` (no
writes, no signals, no GPU work, no server start, no deletion); writes only under
`/Users/wongdowling/Documents/agent_sys_paper/` and `/tmp`. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified. Local scratch: `/tmp/b1_rev/`,
`/tmp/6835_*.sh`, `/tmp/pb_sim` (a throwaway copy of `/tmp/pb_status`); `/tmp/pb_status` itself was left
untouched, `b06f8a91…` and clean.

**Unit reviewed (exact filled files, sha256).** All under `/tmp/b1_handover_fffa_20261111_fffa_20261111_b/`:

| file | sha256 |
|---|---|
| `PLAN.md` | `fd46749a4a8630ba8ef7677d63a9b519bea56988f041dab43d66e699da943600` |
| `handover_pre.sh` | `42075ccb7b5f6e4322c9b3435406deb231990934e949649fba76c2fe2e433761` |
| `status_publish.sh` | `2279999895bc423ba102711d306414558bac6126c2af97520729b4302e153465` |
| `launch.sh` | `e9d72bf3602f533e16b52afeb248caada276c6c32c81358391fe931f66f2b1bd` |
| `start.sh` | `6e7bfc7a1619e563ef3790a6298515fac1a48a0d8979f9f0ad032bb11f908d1c` |
| `receipt.sh` | `95cccd576b6851dbb8cf0805fb4226ae6a263c0c4cc91a2770b9d3b93116926e` |

Run HEAD `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa`; run ID `fffa_20261111_b`; governing documents read at
the run HEAD in the staged checkout
`/home/dowling/r1_b1_engineering/b1_paper_final_fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa/paper`:
`docs/r1/proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md`,
`docs/r1/proposals/B1_RESTART_HANDOFF_20261109.md` §§0–2,
`docs/r1/reviews/B1_TASL7_O2_REVISED_REVIEW_20261107.md`,
`docs/r1/reviews/B1_O2_AUTHOR_STATUS_REVISION_REVIEW_20261107.md`,
`docs/r1/reports/B1_TASL7_HANDOVER_COMMAND_BOUNDARY_20261107.md`,
`docs/r1/reports/B1_COMMITTER_IDENTITY_INCIDENT_20261107.md`, and PLAN §10 rows
`R1-EXAM-B1-STATUS-FEATURE-07NOV`, `R1-EXAM-B1-NO-DELETION-07NOV`, `R1-TASL7-AGENT-OCCUPANCY-07NOV`.

**Verdict in brief: changes required.** `handover_pre.sh` and `status_publish.sh` are executable and, on
the current site state, the marker retirement/creation and the feature-branch STATUS publication they
implement are safe. The launch leg as filled cannot run at all: `launch.sh` references an undefined `$D`
(aborts under `set -u`) and a prelaunch check that expands the *local* `$HOME`, so it STOPs before any
upload. Two other checks that the plan calls fail-closed are actually print-only or stale. Findings are
numbered below; the launch file is a blocker, the rest should be fixed or explicitly accepted as deviations
before execution.

## 1. What I verified (read-only) on the current site state

All commands were `ls/stat/cat/sha256sum/git rev-parse/status/fsck/ls-remote/tmux ls/nvidia-smi/pgrep/ps/flock`
only; the Python objects in `b1_o2_marker.py` were inspected with `cat`/`git cat-file`, not executed.

- Run checkout: HEAD `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa`; `git status --porcelain
  --untracked-files=all` empty; `git remote` returns 0 entries; `git fsck --connectivity-only` exit 0.
  Staged directory `/home/dowling/r1_b1_engineering/b1_paper_final_fffa45a1…/` contains only `paper/` +
  `paper.tar`.
- Marker helper: text SHA-256 `8beedc2a0394f6153eb141f0e0854974887d4c9153f27a9f1fa5cc52532fc599` at the run
  HEAD; same blob (`2d8ed4a…`) at `68357d3d`; matches the reviewed helper's described behaviour
  (`directory()` parent-chain realpath/`O_NOFOLLOW`/owner checks for lock dir and STATUS parent, marker
  `O_EXCL|O_NOFOLLOW` 0600, creation receipt dev/ino/content-hash; `retire` re-checks dev/ino/sha256 and
  `renameat2(RENAME_NOREPLACE)` into `<lock-dir>/_to_delete/`). `aa32d3d` cited in the review is not an
  object in the staged checkout (no remotes), but the code at the run HEAD is the hardened version the
  review describes.
- Old marker `/home/dowling/r1_locks/trackx_evidence.active`: dev `66306`, ino `56261609`, mode 600,
  size 82, owner `dowling:dowling`, sha256 `092023e438a3c2508574a169becce448fd8d652481547f4a974f20ae5bdca1af`,
  content `{"head": "68357d3d8cd0c9f301005e483a49ecfd05f6e5bb", "run_id": "6835_20261108_a"}`. The creation
  receipt `/home/dowling/r1_b1_engineering/b1_handover_6835_20261108_a/marker-receipt.json` matches these
  dev/ino/sha256 exactly (re-checked in Python: `match: True`).
- Track P: `trackp_evidence.active` absent; `r1_tracks/trks_drill.active` absent; `pgrep -af
  "r1p_|p3a|collect .*--stop-file|llama-server|exam_runner|r1\.tracks"` empty; no compute apps in
  `nvidia-smi --query-compute-apps`; GPU UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, 236 MiB used of
  24,564 MiB, 0 % util.
- Lease `~/r1_locks/gpu0.lock` (0 B, dev 66306, ino 56251186) is free (`flock -n … true` → `LEASE-FREE`).
- `tmux ls` (default socket): only `trks_watch`; `/home/dowling/r1_tracks/bin/trks-watch` sha256
  `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112`, running as pid 1388760. The 6835
  session `b1_6835_20261108_a` still exists on its private socket
  `/home/dowling/r1_b1_engineering/b1_handover_6835_20261108_a/tmux.sock` (idle interactive bash, pane pid
  1570628) — preserved 6835 scene; see residual R1.
- Watcher inventory: exactly one `manifest.json` (`/home/dowling/r1_tracks/out/smoke/manifest.json`) and
  one `STOP` (`/home/dowling/r1_tracks/out/smoke/STOP`, 0 B, mtime 2026-11-07 16:46:56 −0800). The other
  files under `out/tabular_mlp/` are not manifest/STOP and are not touched by the watcher's `find`.
  `r1_tracks/logs/watch.log` has 3 lines; the last is
  `2026-11-08T00:46:56Z priority marker seen (/home/dowling/r1_locks/trackx_evidence.active): pausing`.
- `RUN_DIR /home/dowling/r1_b1_engineering/b1_handover_fffa_20261111_b` absent;
  `BATCH /home/dowling/exam-x/work/b1_fffa_20261111_b` absent; 6835 batch `/home/dowling/exam-x/work/
  b1_6835_20261108_a` intact; `/home/dowling/r1_locks/_to_delete` absent; disk 578,705,440,768 B
  (539 GiB) free.
- Harness `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness` at `a3fedbb…`,
  clean; `/home/dowling/exam-x/work/venv/bin/python` executable; `exam_b1_v2.json` `paper_commit`
  `fb57c6a45eceba1fc468bccb4efcefd5440398b3`.
- Gate+preflight (checked directly, not from summaries): CAP
  `/home/dowling/r1_b1_engineering/b1_final_gate_preflight_fffa_20261111_a` — `gate.exit` = `0`,
  `gate.log` ends `GATE_PASS fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa
  53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad …`; `preflight.exit` = `0`,
  `preflight.log` has 16 validated models, `"contender_refused": true`, `"offloaded_layers": 29` of
  `total_layers: 29`, `head` `fffa45a1…`, `PREFLIGHT_PASS: owned server exited and own lease descriptor
  closed`. OUT tree `/home/dowling/exam-x/work/b1_host_preflight_fffa_20261111_a` exists (PLAN names the
  OUT basename only).
- STATUS checkout `/tmp/pb_status`: branch `mac-b-20261107`, HEAD
  `b06f8a91d15d312057fcbe7affd4e26abc5eca7d` = `origin/mac-b-20261107` = `git ls-remote` tip; clean;
  `docs/r1/STATUS.md` ends with the 6835 line
  `Run: \`6835_20261108_a\`; reviewed checkout HEAD: \`68357d3d8cd0c9f301005e483a49ecfd05f6e5bb\`.` +
  newline. The precedent publish is `ccfeb5613e83708441dbafd47f1c295cae9b6427` (author `Dowling Wong
  <wangdowling@gmail.com>`, committer `Codex <noreply@openai.com>`, message `Publish B1 handover running
  status`, 4-line append).
- Host dates: `date -u` `2026-11-11T10:47Z`; `tasl7` local `2026-11-11 02:47 −0800`
  (`/etc/timezone` = `America/Los_Angeles`); Mac local `2026-11-11 11:47 CET`; Python `date.today()` on
  `tasl7` under a plain SSH env returns `2026-11-11`. The run-ID date component `20261111` is consistent.
- `start.sh`/`receipt.sh` compared to the 6835 precedent by `diff`: the only differences are
  `HEAD`, `RUN_ID`, `RUN_DIR` (and the derived `BATCH`) — exactly the permitted fields. The 6835 run
  checkout `/home/dowling/r1_b1_engineering/b1_paper_final_68357d3d…/paper` is clean after that run
  (`status_end` empty), and the staged fffa checkout is likewise clean after the gate/preflight.

## 2. Check results against the five review requirements

1. **Sequence and fail-closed claims — PARTIAL.** The order (absent/dirty/HEAD/date/lease/trackp
   prechecks → retire old marker with its receipt → create new marker with exclusive create → 75 s watcher
   observation → STATUS append/commit/FF push → exclusive script upload + tmux launch) matches the restart
   hand-off §2.4 and the O2 draft's create-then-publish flow; both marker receipts are retained
   (retirement JSON in `RUN_DIR`, old receipt untouched, marker bytes renamed, never deleted); no force
   push; no retry path. **Fail:** the watcher check is stale/fail-open (F3); several "preconditions" are
   print-only (F4); the inventory is not an identity inventory (F5). The launch leg cannot execute (F1/F2).
2. **Site state — PASS** for every listed item (evidence in §1), with residual notes R1–R3.
3. **Command safety — FAIL.** `$D` unbound and `$HOME` expanded locally in `launch.sh` (F1/F2); the
   prelaunch marker check is presence-only (F6); launch does not verify the started session (F10); local
   SSH exit-code capture is not specified (F11). Otherwise: quoting/expansion of `$PAPER`, `$RUN_DIR`,
   `$HEAD`, `$RUN_ID` in double-quoted `ssh` strings is correct (only `$HOME` and `$D` are wrong); all
   create paths are exclusive (`mkdir -m 700`; `set -C` noclobber for `marker-retirement.json`,
   `status-receipt.md`, `marker-receipt.json`, remote `cat >` uploads, `b1.log` via `exec 3>`, `b1.exit`);
   the internal `exec > >(tee -a "$RUN_DIR/prechecks.log") 2>&1` does **not** hide failures (`set -e`
   propagates, `STOP` text is merged into the `tee`'d stream, `HANDOVER_PRE_DONE` is the sentinel) and
   does not print secrets (stat/sha/JSON only; the push prints only the public HTTPS URL).
4. **Run ID/date bindings — PASS now.** `fffa` = first four hex of the accepted HEAD; UTC date `20261111`
   is guarded in `handover_pre.sh:18`; all three relevant clocks read 2026-11-11 at review time. Latent
   timezone risk in F8.
5. **No forbidden effects — PASS.** `status_publish.sh` pushes only `refs/heads/mac-b-20261107` (never
   `main`/`r1`/`exam-x-*`), no `--force`, and verifies the resulting remote tip; `retire` is an atomic
   same-filesystem no-replace rename into `_to_delete` (no deletion); no script sends signals to or alters
   another owner's process/session/evidence; the clean run checkout is only read by `start.sh` (identical
   to the accepted 6835 scripts; `-B`, `PYTHONDONTWRITEBYTECODE`).

## 3. Findings

### F1 — BLOCKING (high): `launch.sh:11–12` uses an undefined `$D`
`launch.sh` has `set -eu` and never assigns `D`; both uploads are `… < "$D/start.sh"` and `… < "$D/receipt.sh"`.
Under `set -u` the second SSH command aborts with `bash: D: unbound variable` (reproduced locally with the
same shell options), so neither reviewed script is uploaded and the run cannot start. It is fail-closed
(nothing remote is written) but the filled plan is not executable as written.
**Minimal fix:** after `set -eu`, add `D=$(cd "$(dirname "$0")" && pwd)` (or
`D=/tmp/b1_handover_fffa_20261111_fffa_20261111_b`) and keep the rest; alternatively spell the two source
paths absolutely.

### F2 — BLOCKING (high): `launch.sh:10` prelaunch check expands the local `$HOME`
The remote command string is double-quoted, and `'$HOME/x'` sits inside *single quotes that are literal
inside double quotes*, so the local shell expands `$HOME` before `ssh`. On the Mac this sends
`set -eu; …; test -x '/Users/wongdowling/x'; …` to `tasl7` (reproduced by expansion), where the path does
not exist; `set -e` makes the SSH command fail and the script prints `STOP: prelaunch checks`. The check can
never pass and is not the intended remote condition.
**Minimal fix:** delete it or replace it with the intended remote check written for remote evaluation, e.g.
`test -x \"\$HOME/exam-x/work/venv/bin/python\"` or `test -d '$PAPER'` (both were verified true), and keep
`PRELAUNCH-CHECKS-PASS` as the last line.

### F3 — MEDIUM: `handover_pre.sh:48–52` watcher observation is stale and fail-open
`BEFORE=$(tail -1 …)` is captured and never used; after the 75 s sleep the script only greps `tail -8` for
`priority marker seen` + `trackx_evidence.active`. The log currently ends with the **2026-11-08** line for the
same marker path, so the check passes on a stale line. Moreover `trks-watch` logs that line only on the
no-marker→marker transition and then sits in `while marker; do sleep 60; done`; because the old marker is
retired and the new one created sub-second (lines 34–43), the watcher never observes absence and **will not
write a new line for this marker**. If the watcher had died or loaded different code, the check would still
pass. This contradicts PLAN step 1 ("the watcher … after the marker it logs `priority marker seen`") and the
O2 review's "observe the actual watcher".
**Minimal fix:** record the log size/line count before `create`, and after the sleep require a **new**
matching line (`tail -n +$((before+1))`); if no new line appears, pass only after explicitly establishing the
already-paused state (watcher pid alive, marker present, manifest/STOP parity unchanged, no `FORCED`) and
record that no new line is expected in the restart; never accept a line that predates marker creation.

### F4 — MEDIUM: `handover_pre.sh:24–26, 30, 32, 55` "all fail-closed" claims are not implemented
The PLAN says the prechecks are "all fail-closed, STOP on any failure", but several are print-only:
`nvidia-smi --query-compute-apps … || true` (line 24), `ps … | grep … || true` (lines 25, 55),
`tmux ls || true` (lines 26, 55), the manifest/STOP inventory (lines 30, 54), and the disk line (32) never
cause a STOP. The PLAN also claims a check of "no `r1p_*` process, no GPU compute, last p3a supervisor
exited 27 Oct", but the script has **no P.3a process check at all** and does not include `r1p_`/`p3a` in
its `ps` pattern. On the current site all of these are clean (verified: no such processes, no compute apps,
only `trks_watch`, 539 GiB free), so this does not change the verdict on this state, but the step is not the
fail-closed gate the reviewed plan claims.
**Minimal fix:** capture and assert: empty `nvidia-smi --query-compute-apps`; empty `pgrep -u dowling -af
'r1p_|p3a|llama-server|r1\.tracks|exam_runner'`; default `tmux ls` equal to `trks_watch` only; a disk
floor; and the before/after inventory comparison in F5. Prefer `comm`/`pgrep -a` patterns to the
full-`cmd` `ps` lines (the command-boundary report asks not to collect arbitrary process arguments).

### F5 — LOW-MEDIUM: `handover_pre.sh:30, 54` inventory lacks identity/parity and nonregular checks
The reviewed command-boundary / O2 material requires recording names, ownership, type, device, inode, size
and timestamps for every `manifest.json` and sibling `STOP`, treating symlinks/nonregular entries and
concurrent changes as STOP. The script records only `%p` for manifests and `%p %T@ %y` for STOPs and never
diffs before/after, so an "unexpected touched path" or a changed identity cannot be detected automatically
(only eyeballed by the operator).
**Minimal fix:** capture `find … -printf '%p %D %i %s %u %g %y %T@\n'` (sorted) for both sets before and
after, diff them, and STOP on any difference outside the directed smoke entry; explicitly STOP on any
symlink/nonregular entry or traversal error.

### F6 — MEDIUM: `launch.sh:10` verifies only the *presence* of `marker-receipt.json`
PLAN step 3 says the launcher "verifies the staged HEAD/cleanliness and the new marker receipt", but the
only marker-related check is `test -f '$RUN_DIR/marker-receipt.json'`. The Track P marker
(`~/r1_locks/trackx_evidence.active`) need not exist, or may have been replaced, and its dev/inode/sha256
and the receipt's `run_id`/`head` are never compared. The launch is the step that actually starts the run
under the marker authority.
**Minimal fix:** additionally `test -f "$HOME/r1_locks/trackx_evidence.active"`, compare
`stat -c '%d %i'` and `sha256sum` to the receipt JSON fields, and check `run_id = fffa_20261111_b` and
`head = fffa45a1…` (read-only), plus require `marker-retirement.json` from the old marker.

### F7 — LOW-MEDIUM: `status_publish.sh:17–18` committer identity deviates from the reviewed draft and precedent
The accepted O2 draft says "commit with the author Dowling Wong and Codex as committer"; precedent
`ccfeb561` has author `Dowling Wong <wangdowling@gmail.com>` and committer `Codex <noreply@openai.com>`,
message `Publish B1 handover running status` (no body). The filled script explicitly sets **both** author
and committer to `Dowling Wong <wangdowling@gmail.com>` and adds a second message paragraph; PLAN.md
repeats that identity. `docs/r1/reports/B1_COMMITTER_IDENTITY_INCIDENT_20261107.md` records the author's
instruction that he remain author and Codex be committer, that such commits must explicitly set
`GIT_COMMITTER_NAME=Codex`/`GIT_COMMITTER_EMAIL=noreply@openai.com`, and that the author/committer must be
verified before pushing; later R4 reviews record committer `Dowling Wong` for Mac-local agent commits, so
the current practice is ambiguous. A simulation of the exact Python+commit block in `/tmp/pb_sim` produced
author = committer = Dowling Wong and a 4-line diff identical to the precedent.
**Minimal fix:** restore the reviewed identity (author Dowling Wong, committer Codex) for this governed
STATUS publication, or record an explicit operator/author decision that the DSH session commits as
Dowling Wong (and doesn't claim Codex), and add a `git log -1 --format='%an <%ae> | %cn <%ce>'` check
before the push.

### F8 — LOW: `handover_pre.sh:18` guards the UTC date, but the marker STATUS heading uses host-local date
The helper `create()` writes `## {datetime.date.today()} — Track X B1 running`, and `date.today()` is
`tasl7`-local (PST, `/etc/timezone` = America/Los_Angeles), while the run-ID date guard and the pushed
heading (`status_publish.sh:13`) use the UTC date `2026-11-11`. Today both are 2026-11-11 (Python
`date.today()` = 2026-11-11), so execution now is consistent. The risk window is 00:00–08:00 UTC
(16:00–24:00 PST previous day), when the local receipt heading would be `2026-11-10` while the run ID and
the pushed STATUS heading say `2026-11-11`; the 6835 local receipt heading `2026-11-08` at 00:46 UTC
suggests a UTC `TZ` was in effect for that run, so the heading date depends on the invoking environment.
**Minimal fix:** add `[ "$(date +%Y%m%d)" = 20261111 ]` alongside the UTC check (and/or run the helper
with `TZ=UTC`), and print/record the exact host-local date in `prechecks.log`.

### F9 — LOW: `status_publish.sh` robustness (duplicate guard, push pipe, branch assertion)
`assert t.endswith('`.\n')` still holds after a first append (the new section also ends with `` `.\n ``),
and there is no "run ID/heading already present" guard, so a retry after a successful push whose
verification failed would append and publish a second `2026-11-11` section. The push is piped through
`tail -2` without `pipefail` (a failed push would be masked, though the subsequent `git ls-remote` check
turns it into a STOP — verified by inspection), and the script does not assert the local branch is
`mac-b-20261107`. The fetch does update the remote-tracking ref for a named branch (verified in a throwaway
local clone), and a failed-push commit remains locally so a retry is refused by the tip check — good.
**Minimal fix:** before appending, `assert 'fffa_20261111_b' not in t and '## 2026-11-11' not in t`;
use `git push --porcelain`/`set -o pipefail` (or drop the `tail`), and assert
`git rev-parse --abbrev-ref HEAD` = `mac-b-20261107`.

### F10 — LOW: `launch.sh:13` does not assert the run session started
`tmux new-session …; sleep 5; tmux ls; echo LAUNCHED` returns success as long as *some* session exists
(`trks_watch` lives on the same default server), so a `b1_fffa_20261111_b` session that exits within the
5 s window (e.g. `receipt.sh` STOP before writing `b1.log`) still prints `LAUNCHED` and exits 0.
**Minimal fix:** add `tmux has-session -t b1_fffa_20261111_b` and `test -s "$RUN_DIR/b1.log"` (and no
`b1.exit` yet) as post-launch assertions, STOP otherwise.

### F11 — LOW: local SSH exit-code capture / pipefail is specified nowhere
The author's `R1-B1-OFFLINE-LOADER-ONCE-08NOV` wrapper (`rc=$?; echo "SSH_EXIT=$rc" | tee -a …`, and
`set -o pipefail` when piping) and the command-boundary report's "capture complete output with exclusive
creation" are not reflected in PLAN steps 1 and 3, which give only `ssh tasl7 'bash -s'` and no capture
recipe for `launch.sh`. `handover_pre.sh`'s internal `tee` and `STOP` text mitigate this (the remote log is
exclusive under the new `RUN_DIR`, and the STOP line reaches the SSH stream), but a local caller using
`ssh … | tee` without `pipefail` would see tee's exit status.
**Minimal fix:** specify the exact local invocations, e.g.
`ssh tasl7 'bash -s' < handover_pre.sh; rc=$?; echo "SSH_EXIT=$rc" | tee -a <local log>; …`, require
`HANDOVER_PRE_DONE` in the output, and record `rc` in `RUN_DIR`.

### F12 — LOW (reviewability): PLAN's ordering/description of the watcher step
PLAN §"Order of execution" places the 75 s watcher observation before STATUS publication, while the
accepted O2 draft/review says "create the marker, then promptly publish the running heading" (publication
is the step stated immediately after creation; the post-creation observation paragraph follows). No safety
impact (the marker is retained if publication fails), but the PLAN's claim that the step "matches the O2
draft" is not literal, and its description of the expected watcher log line does not hold for a watcher
that is already paused (F3). Align the wording (publish promptly after the marker, then validate the
directed watcher effects) or state the deviation.

## 4. Residual notes (non-findings)

- **R1.** The 6835 private-socket tmux session `b1_6835_20261108_a` still exists (see §1). It is part of
  the preserved 6835 scene, is not visible to the default `tmux ls` that `handover_pre.sh`/the PLAN check,
  and cannot collide with the new default-socket session `b1_fffa_20261111_b`. The PLAN's "only
  `trks_watch`" is accurate for the default socket only.
- **R2.** The watcher's *loaded* code is not provable: the file hash is the historical
  `cf68843e…`, but the file mtime (2026-10-31 04:18:54) is after the running process start
  (2026-10-30 04:07:40), exactly the caveat in the O2 draft/boundary report. Its observable state is
  consistent with the reviewed description: paused since 2026-11-08, `smoke/STOP` present, no collectors,
  no `trks_llm` session. Approving this review does not certify the loaded bytes.
- **R3.** `retire` uses `renameat2(RENAME_NOREPLACE)`; the site filesystem is the ext2/ext3/4 family on
  device 66306, kernel 6.8.0-138-generic, which should support it, but there is no executed site test and
  this is its first use. Failure is fail-closed (helper raises, marker unchanged, `set -e` STOP); the O2
  draft still requires the operator to qualify actual site support before relying on it.
- **R4.** The separate preflight **result** review `_xfer/b1_preflight_result_review_20261111/` does not
  exist yet; PLAN says it must be accepted before execution. The exact-HEAD review
  (`_xfer/b1_runhead_review_20261111/B1_RUN_HEAD_REVIEW_20261111.md`) and the staging/preflight-script
  reviews are accepted. I verified the gate/preflight artifacts directly (§1).
- **R5.** The preflight "OUT" named in PLAN is the basename; the tree is
  `/home/dowling/exam-x/work/b1_host_preflight_fffa_20261111_a` (exists; contains
  `llama_server_35665.json/.log` and `_to_delete/` kept records). Not a defect.
- **R6.** The STATUS route is prepared: clean separate `/tmp/pb_status` on `mac-b-20261107` at the origin
  tip, `docs/r1/STATUS.md` ending with the 6835 append; the append fragment, 4-line diff, author identity
  and FF-only push mechanics were simulated locally (F7 covers the committer deviation).
- **R7.** The run checkout is not modified by the launch path: `start.sh`/`receipt.sh` are the accepted
  6835 scripts modulo the four permitted fields, and the 6835 checkout is clean post-run.
- **R8.** No secret is printed by the reviewed commands (stat/sha/JSON/URL only); the `ps … cmd` lines in
  `handover_pre.sh` are filtered to matching processes but could still expose a matching argv (folded into
  F4's `comm` recommendation).
- **R9.** All remote actions above were read-only; the only local writes are this review and `/tmp`
  scratch. `/tmp/pb_status` remains at `b06f8a91…` clean.

## 5. Bottom line

On the current site state the marker retirement (old marker identity matches its receipt exactly), the new
marker creation and the feature-branch STATUS publication are implementable safely, and the STOP/no-deletion
and no-forbidden-effect properties hold. However, **`launch.sh` cannot execute as filled** (F1, F2), and
two reviewed checks are not fail-closed/stale (F3, F4). Fix F1–F6 (and, before execution, F7–F11 or record
acceptance with reasons), then re-review the changed files and re-verify the site snapshot; execution of the
current exact files is not authorized by this review.

VERDICT: changes required

---

## Round 2 — rev 2 re-review (11 Nov)

**Reviewer.** Same independent reviewer (did not write rev 2). Round-1 section above is retained as history and
superseded by this round. Read-only on `tasl7` (no writes, no signals, no GPU work, no server start, no
deletion); local writes only under `/tmp` and this `_xfer` directory. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified.

**Rev 2 unit recomputed sha256** (all under `/tmp/b1_handover_fffa_20261111_fffa_20261111_b/`; every value
matches the operator's list):

| file | sha256 |
|---|---|
| `PLAN.md` | `2afd770921ef2e5a70e1cdf6978536404e98a4a713b346548f304b4b52dcb559` |
| `handover_pre.sh` | `fc9b1a64eb3614d10f497e3c7a9e23db3b02b80ff365a10e04226969dbf1f2ca` |
| `handover_run.sh` | `359fbbaa67425cd0a09993e85a06229ebd3db54b09a9c428bdac24134283fe64` |
| `status_publish.sh` | `8ca54f917c192af49a744177ecf2651fefcee5142b4b7e3f883604c193df0d38` |
| `launch_precheck.sh` | `cd2e7b488292496a17eb48efa9705ef4453ea3a654ab816a8137510031779931` |
| `launch_start.sh` | `0c106e2794f0ebcbae2165920ff857a2b7ad2d45737bf66c6779f253f538bf66` |
| `launch.sh` | `7a2d5d28bf121a0eaf12a46c522750f79740fb160ed6f63bb82905bfac30553d` |
| `start.sh` | `6e7bfc7a1619e563ef3790a6298515fac1a48a0d8979f9f0ad032bb11f908d1c` (unchanged) |
| `receipt.sh` | `95cccd576b6851dbb8cf0805fb4226ae6a263c0c4cc91a2770b9d3b93116926e` (unchanged) |

Local checks: `bash -n` passes on all eight scripts; `mktemp -d /private/tmp/paper-b-b1-handover-capture-20261111.XXXXXXXX`
works on this Mac (0700); the `<<'PY'` heredoc inside a script fed via `bash -s` was exercised locally (works);
`pgrep -f` patterns do **not** self-match when fed via `bash -s` on `tasl7` (tested: rc 1, no output);
`wc -l < watch.log` = `3`, `tail -n +4` = empty; the `%y` inventory regex classifies both current entries as
regular `f`. PLAN's listed SHAs all match the actual files.

### Resolution of the round-1 findings

| finding | status |
|---|---|
| F1 (`$D` undefined in `launch.sh`) | **resolved** — `launch.sh:2` `D=$(cd "$(dirname "$0")" && pwd)`; all four local sources use `"$D/..."`. |
| F2 (local `$HOME` expansion) | **resolved** — stray `test -x '$HOME/x'` gone; the remote checks moved to `launch_precheck.sh`, fed via `ssh 'bash -s'` so `$HOME` is evaluated remotely; verified all remote assertions are literal/remote-side. |
| F3 (stale watcher check) | **resolved** (minor residuals) — pre-create `WLOG_LINES_BEFORE=$(wc -l)` and `WATCH_PID` (handover_pre:55–58); after 75 s, new lines must be `priority marker seen` + `trackx_evidence.active`, no `FORCED` (84–88); the empty-new-line case only passes after re-establishing the paused state (watcher PID alive, marker present, last log line is `priority marker seen`) (89–94). On the current log (3 lines, last = the 2026-11-08 pause line, no new line) the script would correctly take `WATCHER_ALREADY_PAUSED_NO_NEW_LINE`; a stale line can no longer satisfy the new-line branch. Residuals N3/N5. |
| F4 ("all fail-closed" not implemented) | **resolved** — compute apps (25–26), owned processes incl. `r1p_|p3a` (28–29), default tmux exactly `trks_watch` (30–32), Track P/drill markers (33–34), lease (35), 100 GB disk floor (37–39), post-checks (107–110) are asserted; no `|| true` on a decision path. Residual N6. |
| F5 (inventory identity/parity) | **resolved** — identity-rich sorted `%p %D %i %s %u %g %y %T@` inventories (59–60, 95–96), nonregular gate (61), `cmp` parity plus diff allowing only the smoke entries (97–106). Residuals N2/N4. |
| F6 (marker receipt presence-only) | **resolved** — `launch_precheck.sh:21–30` checks live marker dev/ino/sha256/content against the new receipt, its `run_id`/`head`, requires `marker-retirement.json`, and rejects pre-existing `start.sh`/`receipt.sh`/`b1.exit`/session (13–20, 31). |
| F7 (committer identity deviation) | **resolved as a documented operator decision** — `status_publish.sh:26–31` commits as author `Dowling Wong <wangdowling@gmail.com>`, committer this operator session, with the decision stated in the body ("no Codex process participated"), and asserts `%an <%ae> | %cn <%ce>` before the push. **Judgment:** an explicit *author* ruling is not strictly required for this feature-branch operational STATUS commit: it is not a history rewrite or force push, the body is transparent, and the nearest precedent for this restart's Mac-local agent commits (`B1_R4_REVIEW_202609`, 9 Nov) records author = committer `Dowling Wong` for DSH-era commits. It does deviate from the O2 draft's literal "Codex as committer"; the plan records the deviation. Recommend citing the R4 precedent; if the author wants the O2 wording preserved, that is an author choice. |
| F8 (UTC vs host-local heading date) | **resolved** — marker created with `TZ=UTC` (handover_pre:73–74), heading asserted against `date -u +%F` (77); both UTC and host-local dates asserted 20261111 (20–21); `status_publish.sh:6–7` asserts the UTC date. |
| F9 (STATUS robustness) | **partially resolved → F13** — duplicate run-ID/heading guards (13–14), `set -o pipefail`, `git push --porcelain` without a masking `tail`, remote-tip verification (32–36) are all present, but the newly added branch assertion targets the wrong branch name (F13). |
| F10 (no post-launch assertion) | **resolved** — `launch_start.sh` asserts session alive and `b1.exit` absent at 8 s and 15 s, `b1.log` exists, prints `tmux ls` and log size (18–27). |
| F11 (SSH rc capture / wrapper) | **resolved** — `handover_run.sh` is the specified wrapper: exclusive `mktemp` capture dir, `ssh 'bash -s' < handover_pre.sh`, `rc=$?`, `SSH_EXIT=`, requires `HANDOVER_PRE_DONE`, writes `RUN_DIR/handover-run.txt` and `SHA256SUMS`. Residual N1. |
| F12 (ordering deviation) | **resolved** — recorded in PLAN rev 2 §"Ordering deviation (recorded, non-blocking)". |

### F13 — BLOCKING (high): `status_publish.sh:11` asserts the wrong branch name
`status_publish.sh:11` compares `git rev-parse --abbrev-ref HEAD` to `mac-b-20261107`, but the actual branch is
`mac-b1-20261107` (verified: `/tmp/pb_status` branch `mac-b1-20261107`; `git ls-remote origin
refs/heads/mac-b1-20261107` = `b06f8a91…`; the governing O2 draft lines 15/17 and the restart hand-off line 31
say `mac-b1-20261107`; the same script's lines 8/9/34/35 correctly use `mac-b1-20261107`). The assertion
therefore **always fails**, printing `STOP: wrong-branch` and exiting before the append/commit/push, so step 2
of the plan cannot execute and the STATUS publication never occurs. It is fail-closed (marker retained, no
branch advance) but the filled plan is not executable as written. PLAN rev 2 lines 52 and 58 repeat the same
wrong name ("`mac-b-20261107`" and "`refs/heads/mac-b-20261107`").
**Minimal fix:** change `mac-b-20261107` → `mac-b1-20261107` in `status_publish.sh:11`, PLAN.md:52 and
PLAN.md:58 (no other change), then recompute the two SHAs and re-run the read-only branch/tip check.

### Remaining low-severity findings (non-blocking on the current state)

- **N1 (low) `handover_run.sh:11`** — `set -uo pipefail` has no `-e`; if the remote write of
  `RUN_DIR/handover-run.txt` fails, the wrapper ignores it and still prints `HANDOVER_PRE_PASSED` and exits 0
  (the handover itself would have succeeded). Fix: append `|| { echo "STOP: cannot write handover-run.txt";
  exit 1; }` or add `set -e` after the `rc` handling.
- **N2 (low) `handover_pre.sh:59–60, 95–96, 101–104`** — `find … | sort` and `diff … | grep …` are judged by
  the pipeline's last command (no `pipefail`), so a `find`/`diff` failure could be recorded as
  `INVENTORY_UNCHANGED`/`DIRECTED_ONLY`. Fix: capture the raw output with an explicit rc (`find … > raw ||
  fail inventory-find`; `sort raw > …`; `diff … > d; rc=$?`) and branch on `rc`, not on a pipeline.
- **N3 (low) `handover_pre.sh:55–56, 90`** — `pgrep -u dowling -f 'trks-watch' | head -1` selects the tmux
  server (pid 1388759, whose argv contains the script path) rather than the watcher shell (pid 1388760);
  `kill -0` is therefore an indirect proxy. Fix: use `tmux list-panes -t trks_watch -F '#{pane_pid}'` or
  `pgrep -f '^bash /home/dowling/r1_tracks/bin/trks-watch$'`.
- **N4 (low) `handover_pre.sh:61`** — the nonregular gate `grep -vE ' [fd] [0-9.]+$'` permits directories (`d`)
  as well as regular files (`f`); a directory named `manifest.json`/`STOP` would pass. Fix: restrict to ` f `.
- **N5 (low) `handover_pre.sh:92`** — the already-paused branch checks only that the last line contains
  `priority marker seen`, not its marker path/recency; acceptable for the current single-marker log but could
  be tightened to `trackx_evidence.active`.
- **N6 (low) `handover_pre.sh:109`** — the post-check process pattern omits `r1p_|p3a` (the pre-check at line
  28 includes them); a P.3a process appearing during the 75 s window would not be caught. Reuse the same
  pattern.
- **N7 (low) `launch.sh`** — unlike `handover_run.sh`, the launch orchestrator has no local exclusive
  capture/rc record; its four SSH steps run under `set -e`, so failures abort, but a caller piping
  `launch.sh | tee` without `pipefail` would mask its exit status. Recommend the same wrapper pattern or an
  explicit runbook capture instruction.
- **N8 (info) `handover_pre.sh:111–114`** — the new marker identity is printed but not compared to
  `marker-receipt.json`; `launch_precheck.sh:21–30` does compare it, so this is covered downstream.

### Current site-state re-verification (read-only, at `2026-11-11T10:5xZ`)

- Old marker **unchanged**: dev `66306`, ino `56261609`, mode 600, 82 B,
  sha256 `092023e438a3c2508574a169becce448fd8d652481547f4a974f20ae5bdca1af`, content
  `{"head": "68357d3d…", "run_id": "6835_20261108_a"}`; the 6835 creation receipt still matches exactly
  (dev/ino/sha256/content); no `marker-retirement.json` yet.
- `trackp_evidence.active` and `r1_tracks/trks_drill.active` absent; `pgrep -u dowling -af
  'r1p_|p3a|llama-server|r1\.tracks|exam_runner'` (fed via `bash -s`, no self-match) empty; no GPU compute
  apps; GPU `GPU-ab72fb4a-…`, 236 MiB used, 0 %.
- Default `tmux ls` = only `trks_watch`; the preserved 6835 private-socket session `b1_6835_20261108_a` is
  unchanged. `~/r1_locks/gpu0.lock` free (`flock -n` → LEASE-FREE); disk 578,705,235,968 B (539 GiB) ≥ 100 GB.
- `watch.log` still 3 lines, last `2026-11-08T00:46:56Z priority marker seen
  (…/trackx_evidence.active): pausing`; `wc -l` = 3, `tail -n +4` empty — so rev 2's already-paused branch
  would be taken and would pass (watcher PID alive, marker present, last line matches).
- `r1_tracks/out` inventory unchanged: exactly `smoke/manifest.json` (dev 66306, ino 57039147, 5340 B,
  dowling:dowling, regular, mtime 1793323478.0640841870) and `smoke/STOP` (dev 66306, ino 57048195, 0 B,
  regular, mtime 1794098816.7435273490); no other manifest/STOP, no `_to_delete`.
- `RUN_DIR /home/dowling/r1_b1_engineering/b1_handover_fffa_20261111_b` and `BATCH
  /home/dowling/exam-x/work/b1_fffa_20261111_b` absent; 6835 batch and handover directory intact (same files,
  `b1.exit`=1, `tmux.sock` present).
- Staged checkout `fffa45a1…`: HEAD exact, clean (`-uall`), 0 remotes, `fsck --connectivity-only` rc 0; marker
  helper sha256 still `8beedc2a…`.
- Gate/preflight CAP unchanged (read-only hashes): `gate.exit`/`preflight.exit` sha256
  `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` (content `0\n`), `gate.log` sha256
  `da5d3a676d04b0a520f9792ead04451cfb948d003fa942b20b16b431f37f9196` (mtime 2026-11-11 02:32:41 −0800),
  `preflight.log` sha256 `b48a639d60bc3f54e5d2622566b0f4fffe4cc5bd1cd42e1b5c8f1d4e8071f151`.
- Preflight **result** review now present and accepted:
  `_xfer/b1_preflight_result_review_20261111/B1_PREFLIGHT_RESULT_REVIEW_20261111.md` (VERDICT: accepted);
  run-HEAD review remains accepted.
- STATUS checkout `/tmp/pb_status`: branch `mac-b1-20261107`, HEAD `b06f8a91…` = `origin/mac-b1-20261107` =
  `git ls-remote origin refs/heads/mac-b1-20261107` tip, clean; `docs/r1/STATUS.md` has no `## 2026-11-11`
  and no `fffa_20261111_b`, and still ends with the 6835 line.
- Host dates unchanged: `date -u` `2026-11-11T10:5xZ`; `tasl7` local `2026-11-11 02:5x −0800`; both date guards
  would pass. Only read-only commands were used on `tasl7`; local scratch was `/tmp/inv_test.txt` and a
  removed `/private/tmp` `mktemp` probe. No functional site change since round 1 was observed.

### Bottom line

Rev 2 resolves F1–F12 (F9 except for its new branch assertion) and is substantially more fail-closed and
reviewable; the site state still satisfies every precondition, including the already-paused watcher that rev 2
now handles explicitly. One blocking typo remains: `status_publish.sh:11` (and PLAN.md:52/58) name
`mac-b-20261107` instead of `mac-b1-20261107`, so executing exactly these files STOPs at step 2 before the
STATUS append/commit/push. Fix F13 (one string in three places), recompute the two SHAs, and re-run the
read-only branch/tip check; no other blocking change was found, and the remaining N1–N8 are low-severity
robustness/evidence items that can be accepted as recorded residuals if not fixed.

VERDICT: changes required

---

## Round 3 — rev 3 re-review (11 Nov)

**Reviewer.** Same independent reviewer (did not write rev 3). Round-1 and Round-2 sections above are retained
as history and superseded by this round. Read-only on `tasl7` (no writes, no signals, no GPU work, no server
start, no deletion); local writes only under `/tmp` and this `_xfer` directory. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified.

**Rev 3 unit recomputed sha256** (all under `/tmp/b1_handover_fffa_20261111_fffa_20261111_b/`; every value
matches the operator's list):

| file | sha256 | vs rev 2 |
|---|---|---|
| `PLAN.md` | `f6486213d3784bd307239d2fbf28bb37cbe45d1219dc0a8c9cc7dee2f91ba3e6` | changed |
| `handover_pre.sh` | `819e6d7fcbb2b3e6ddc1909640b213f3adad0a8fad39e8c85084adbc55b0edf1` | changed |
| `handover_run.sh` | `6c4a7894df1c9ca6f27f33230158641fa23a95ab8ebe5a349d092f8b1b59a1c9` | changed |
| `status_publish.sh` | `2474344fb5c521054781bf11f925d58d613b11692c99dedce3733eb02b8ce12d` | changed |
| `launch.sh` | `f3514c867fbdd6a5a8320e3a0860fe287cc0a4bec581bd6b9e18df8ec79dd6a2` | changed |
| `launch_precheck.sh` | `cd2e7b488292496a17eb48efa9705ef4453ea3a654ab816a8137510031779931` | unchanged |
| `launch_start.sh` | `0c106e2794f0ebcbae2165920ff857a2b7ad2d45737bf66c6779f253f538bf66` | unchanged |
| `start.sh` | `6e7bfc7a1619e563ef3790a6298515fac1a48a0d8979f9f0ad032bb11f908d1c` | unchanged |
| `receipt.sh` | `95cccd576b6851dbb8cf0805fb4226ae6a263c0c4cc91a2770b9d3b93116926e` | unchanged |

Only the six listed files changed vs rev 2; `launch_precheck.sh`/`launch_start.sh`/`start.sh`/`receipt.sh` are
byte-identical to the round-2-reviewed versions. `bash -n` passes on all eight scripts; PLAN's listed SHAs all
match the actual files.

### Resolution status

- **F13 — resolved.** `status_publish.sh:11` now asserts `mac-b1-20261107`; lines 8/9/34/35 were already
  correct. PLAN.md:52/58 now say `mac-b1-20261107`; the only remaining `mac-b-20261107` string is the F13
  explanation (PLAN.md:90). Verified against the live checkout: `/tmp/pb_status` is on `mac-b1-20261107` and the
  remote branch is `refs/heads/mac-b1-20261107` = `b06f8a91…`, so the assertion will pass.
- **N1 — resolved.** `handover_run.sh:11–13` now STOPs if `RUN_DIR/handover-run.txt` cannot be written.
- **N2 — partially resolved (residual N2R).** The explicit `BADM`/`BADS` emptiness checks in
  `handover_pre.sh:117–121` are correct, and the diff outputs are captured under `RUN_DIR/`. However, the
  `find … | sort > … || fail …` lines (60–61, 108–109) still mask a `find` failure because `handover_pre.sh`
  does not set `pipefail` (the pipeline status is `sort`'s), so a traversal/read error is not stopped at the
  inventory step; a failed `diff` similarly writes an empty `.diff`, yielding empty `BADM`/`BADS` and
  `INVENTORY_DIRECTED_ONLY`. Low on the current readable tree, but the claimed fix is not complete.
- **N3 — resolved.** `handover_pre.sh:55–57` uses `tmux list-panes -t trks_watch -F '#{pane_pid}'`; on site
  this is pid 1388760 (`bash …/trks-watch`), verified alive.
- **N4 — resolved.** The gate is now `grep -vE ' f [0-9.]+$'` (regular files only).
- **N5 — resolved.** The already-paused branch also requires `trackx_evidence.active` in the last watch.log
  line (`handover_pre.sh:103–105`).
- **N6 — resolved.** The post-create process pattern includes `r1p_|p3a` (`handover_pre.sh:125`).
- **N7 — implemented but with a blocking regression (F14)** plus minor residuals: the local capture and
  `RUN_DIR/launch-run.txt` are present, but the four SSH steps are no longer fail-closed (see F14), the
  `shasum` summary at `launch.sh:14` is unguarded, and the script requires only `LAUNCHED`, not
  `LAUNCH_PRECHECK_PASS`.
- **N8 — resolved.** `handover_pre.sh:79–88` asserts `NEW_MARKER_MATCHES_RECEIPT` (dev/ino/sha256/content vs
  the new receipt, `run_id`/`head`) immediately after `create`.

### F14 — BLOCKING (high): rev 3 `launch.sh` lost fail-closed sequencing

Rev 2's `launch.sh` ran the four SSH steps as separate commands under `set -euo pipefail`, so a failed
`launch_precheck.sh` aborted before any upload or launch. Rev 3 changed the shebang line to
`set -uo pipefail` (no `-e`) and wrapped the four SSH commands in one group whose status is captured only
afterwards:

```sh
set -uo pipefail                       # launch.sh:1 — no -e
CAP=$(mktemp -d …)                     # launch.sh:4
{                                      # launch.sh:6
  ssh … 'bash -s' < "$D/launch_precheck.sh"          # :7
  ssh … "… cat > '$RUN_DIR/start.sh'" < "$D/start.sh"  # :8
  ssh … "… cat > '$RUN_DIR/receipt.sh'" < "$D/receipt.sh" # :9
  ssh … 'bash -s' < "$D/launch_start.sh"             # :10
} > "$CAP/launch.log" 2>&1             # :11
rc=$?                                  # :12 — status of the LAST command only
```

Without `-e`, every step runs unconditionally and `rc` reflects only the final `launch_start.sh`. Consequences:

1. A **failed `launch_precheck.sh`** (staged HEAD changed, marker/receipt mismatch, missing retirement receipt,
   missing STATUS heading, pre-existing `start.sh`/`receipt.sh`/`b1.exit`/session) does **not** stop the
   sequence: the uploads still run and `launch_start.sh` can then print `LAUNCHED` and start the run with the
   marker authority unverified. `launch_start.sh` does not re-check the marker, HEAD, receipts or STATUS
   heading, so nothing downstream catches it. The `grep -q 'LAUNCHED'` at line 15 and the `rc` at line 12 both
   pass.
2. A failed upload is likewise not stopped; `launch_start.sh` checks the SHAs, but if the pre-existing
   `start.sh`/`receipt.sh` are the reviewed bytes (e.g. a previous partial launch left them behind, which is
   exactly why `launch_precheck.sh:19–20` rejects them), it will launch anyway — the no-retry guard is
   bypassed.
3. A precheck STOP additionally leaves `RUN_DIR/start.sh`/`receipt.sh` partially written after the STOP,
   contradicting the plan's "any failure preserves the scene".

Demonstrated locally with the same shell options: a group whose first command fails but whose last command
succeeds yields `rc=0` and the following `grep 'LAUNCHED'` passes.

**Minimal fix:** capture each step's exit status separately and STOP on the first nonzero, e.g. for each of the
four steps append `>> "$CAP/launch.log" 2>&1 || { rc=$?; printf 'SSH_RC=%s\n' "$rc" | tee -a "$CAP/launch.log";
echo "STOP: launch step failed rc=$rc; capture $CAP"; exit 1; }`, or open `exec 3>"$CAP/launch.log"` and run
`ssh … >&3 2>&1 || { rc=$?; …; exit 1; }` per step; additionally require `LAUNCH_PRECHECK_PASS` after the
precheck and guard the `shasum` at line 14. Recompute the `launch.sh` SHA and re-review only that file.

### Other residuals (low, non-blocking)

- **N2R** as above: add `set -o pipefail` to `handover_pre.sh` (or capture `find`/`diff` rc explicitly), so the
  inventory steps are genuinely fail-closed.
- **N7R** as above: guard `launch.sh:14` (`shasum … || STOP`) and require `LAUNCH_PRECHECK_PASS`; the exclusive
  capture itself (`CAP`/`SSH_RC`/`SHA256SUMS`/`launch-run.txt`) is correct and does not write secrets.
- **N9 (info) PLAN rev label**: PLAN.md:1 still reads "(11 Nov 2026, rev 2)" and line 6 says "Rev 2 answers
  … F1–F12"; the rev 3 fixes are in a separate section. Cosmetic; bump the title/round to rev 3 so the
  reviewed document and the reviewed SHAs are unambiguous.
- **N10 (low) `handover_run.sh:8`**: the local `shasum … > SHA256SUMS` is unguarded under `set -uo pipefail`
  (no `-e`); a failure continues to the (successful) final echo. Add `|| { echo "STOP: shasum"; exit 1; }`.

### Current site-state re-verification (read-only, `2026-11-11T10:57Z`)

- STATUS: `/tmp/pb_status` on branch `mac-b1-20261107`, HEAD `b06f8a91d15d312057fcbe7affd4e26abc5eca7d` =
  `origin/mac-b1-20261107` = `git ls-remote origin refs/heads/mac-b1-20261107` tip; clean (0 changes); no
  `## 2026-11-11` heading, no `fffa_20261111_b` in `docs/r1/STATUS.md`; still ends with `…68357d3d…`. The F13
  assertion (line 11) would pass on this checkout.
- Old marker `/home/dowling/r1_locks/trackx_evidence.active` unchanged: dev 66306, ino 56261609, mode 600,
  82 B, sha256 `092023e438a3c2508574a169becce448fd8d652481547f4a974f20ae5bdca1af`, content
  `{"head": "68357d3d…", "run_id": "6835_20261108_a"}`; the 6835 receipt still matches; no retirement receipt.
- Watcher: `tmux list-panes -t trks_watch -F '#{pane_pid}'` = 1388760 (`bash …/trks-watch`), alive; `watch.log`
  still 3 lines, last `2026-11-08T00:46:56Z priority marker seen (…/trackx_evidence.active): pausing`; so
  rev 3's already-paused branch would be taken and pass (`WATCH_PID` alive, marker present, last line matches
  the marker path).
- No owned/compute processes: `pgrep -u dowling -af 'r1p_|p3a|llama-server|r1\.tracks|exam_runner'` (fed via
  `bash -s`, no self-match) empty; `nvidia-smi --query-compute-apps` empty; GPU UUID `GPU-ab72fb4a-…`, 236 MiB
  used. Default `tmux ls` = only `trks_watch`. `trackp_evidence.active` and `trks_drill.active` absent.
- Lease free (`flock -n` → LEASE-FREE); disk 578,705,154,048 B (539 GiB) ≥ 100 GB.
- `RUN_DIR /home/dowling/r1_b1_engineering/b1_handover_fffa_20261111_b` and `BATCH
  /home/dowling/exam-x/work/b1_fffa_20261111_b` absent; `_to_delete` absent.
- 6835 scene intact: batch, handover dir (`b1.exit`=1, `b1.log`, receipts, `start.sh`, `receipt.sh`,
  `tmux.sock`), private-socket session `b1_6835_20261108_a` alive.
- `r1_tracks/out` inventory unchanged: exactly `smoke/manifest.json` (dev 66306, ino 57039147, 5340 B,
  dowling:dowling, regular, mtime 1793323478.0640841870) and `smoke/STOP` (dev 66306, ino 57048195, 0 B,
  regular, mtime 1794098816.7435273490).
- Staged checkout `fffa45a1…`: HEAD exact, clean (`-uall`), 0 remotes, `fsck` rc 0; marker helper still
  `8beedc2a…`. Host dates: UTC `2026-11-11T10:57Z`, host-local PST `2026-11-11 02:57` — both date guards pass.
- Only read-only commands were used on `tasl7`; no site write or signal was sent; local scratch was a removed
  `/tmp/grp_demo.*` group-semantics demo.

### Bottom line

Rev 3 fixes F13 and N1–N8 (N2 and N7 with residuals), and the current site state still satisfies every
precondition. However, rev 3's `launch.sh` regressed the round-2 fail-closed sequencing: without `set -e`, the
single grouped `rc` reflects only the last SSH step, so a failed `launch_precheck.sh` (or a failed upload) no
longer stops the sequence and `LAUNCHED` can be printed and the run started with the precheck's marker/HEAD/
STATUS guarantees unverified. That must be fixed (per-step rc checks plus a `LAUNCH_PRECHECK_PASS`/
`SHA256SUMS`/`shasum` guard) and `launch.sh` re-reviewed before this plan can be accepted.

VERDICT: changes required

---

## Round 4 — rev 4 re-review (11 Nov)

**Reviewer.** Same independent reviewer (did not write rev 4). Rounds 1–3 above are retained as history and
superseded by this round. Read-only on `tasl7` (no writes, no signals, no GPU work, no server start, no
deletion); local writes only under `/tmp` and this `_xfer` directory. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified.

**Rev 4 unit recomputed sha256** (all under `/tmp/b1_handover_fffa_20261111_fffa_20261111_b/`; every value
matches the operator's list):

| file | sha256 | vs rev 3 |
|---|---|---|
| `PLAN.md` | `e96f853927d6b3b0bce607e3b8ac3cab85ac82b35c8f94341cec88b784f04194` | changed |
| `handover_pre.sh` | `29435dedf0a9ea4f2539664e632bf84336db931c40307f854b9cc6d79c866877` | changed |
| `handover_run.sh` | `bb41f2554f38a778e9e16039867d3011434df71f8ec194abb924e89bb0e422a7` | changed |
| `launch.sh` | `a821b47dd85ddcb12600c7e7942d56059939b69a1e29b047d22b66794fb5aa43` | changed |
| `status_publish.sh` | `2474344fb5c521054781bf11f925d58d613b11692c99dedce3733eb02b8ce12d` | unchanged (rev-3 F13 fix) |
| `launch_precheck.sh` | `cd2e7b488292496a17eb48efa9705ef4453ea3a654ab816a8137510031779931` | unchanged |
| `launch_start.sh` | `0c106e2794f0ebcbae2165920ff857a2b7ad2d45737bf66c6779f253f538bf66` | unchanged |
| `start.sh` | `6e7bfc7a1619e563ef3790a6298515fac1a48a0d8979f9f0ad032bb11f908d1c` | unchanged |
| `receipt.sh` | `95cccd576b6851dbb8cf0805fb4226ae6a263c0c4cc91a2770b9d3b93116926e` | unchanged |

Verified changed set vs rev 3 is exactly **four** files (`PLAN.md`, `handover_pre.sh`, `handover_run.sh`,
`launch.sh`); the other five (including the F13-fixed `status_publish.sh`) are byte-identical to the
round-3-reviewed versions. (The hand-off message's "six files" over-counts; no unexpected file changed.)
`bash -n` passes on all eight scripts; PLAN's listed SHAs all match the actual files; PLAN title/header now
reads rev 4.

### F14 — resolved (with one low residual, N11)

`launch.sh` rev 4 replaces the grouped sequence with `run_step()` (lines 6–16): each call runs one command with
its output appended to `$CAP/launch.log`, records `<step> RC=<n>`, appends `SSH_RC=<n>` and exits with
`STOP: launch step '<desc>' failed rc=<n>` on the first nonzero rc; the four steps (precheck, upload-start,
upload-receipt, launch) are separate calls (lines 17–20). After them it requires `LAUNCH_PRECHECK_PASS`
(line 22), requires `LAUNCHED` (line 23), guards the `SHA256SUMS` write (lines 24–26), appends `SSH_RC=0`
(line 21) and records `RUN_DIR/launch-run.txt` (lines 27–29). I exercised the function pattern locally with the
same shell options: on success the capture contains the step output and `<step> RC=0`; on a failing precheck the
function exits 1 and **no subsequent step runs** (no upload output in the capture), so a failed precheck now
stops before any upload; the stdin redirection on the function call is inherited by `"$@"` (verified), so each
remote script is still delivered via `ssh 'bash -s' < file`.

- **N11 (low, residual):** the `< "$D/…"` redirection is attached to the `run_step` *call*, so if one of the
  four local inputs is missing/unreadable the shell fails the call **before** entering `run_step`; with no
  `set -e` the script then continues and the sentinel checks (lines 22–23) run only after the launch step. All
  four files are present and hash-verified at review time, so this is not reachable for the exact reviewed
  file set; for hardening add `[ -r "$D/launch_precheck.sh" ] && [ -r "$D/start.sh" ] && …` before the steps
  (or `|| { echo STOP; exit 1; }` on each `run_step` call) and consider checking `LAUNCH_PRECHECK_PASS`
  immediately after the precheck. Not blocking.

### N2, N9, N10 — resolved

- **N2:** `handover_pre.sh` now starts `set -euo pipefail`; the `find … | sort > file || fail …` guards
  (lines 60–61, 108–109) now fire on a failed `find` (pipeline status is `find`'s under `pipefail`; verified
  with a local pipeline test and the site's GNU `find -printf` form). The diff block is unchanged; an empty
  `*.diff` from a rare `diff` failure would still yield empty `BADM`/`BADS`, but the inputs are now produced
  fail-closed, so this residual is negligible.
- **N9:** PLAN title/header and intro now read rev 4, with a separate "Rev 4 fixes (F14 + N2/N9/N10)" section.
- **N10:** `handover_run.sh:8` guards the `shasum` write with `if ! shasum …; then STOP`.

### Remaining residuals (all low, non-blocking)

- N11 above (redirection failure on a missing local input; hardening only).
- The old `N2` diff-error path noted above (empty diff ⇒ empty `BADM`/`BADS`); negligible with fail-closed find.
- `handover_run.sh` still runs `set -uo pipefail` without `-e` by design (it checks the handover rc explicitly);
  its line 7 `printf | tee` and the pre-existing "run-scripts are byte-identical to 6835" items are unchanged.

### Current site-state re-verification (read-only, `2026-11-11T11:00:56Z`)

- STATUS: `/tmp/pb_status` on branch `mac-b1-20261107`, HEAD `b06f8a91d15d312057fcbe7affd4e26abc5eca7d` =
  `origin/mac-b1-20261107` = `git ls-remote origin refs/heads/mac-b1-20261107` tip; clean (0 changes); no
  `## 2026-11-11` heading and no `fffa_20261111_b` in `docs/r1/STATUS.md`; still ends with the 6835 line. The
  F13 assertion (`status_publish.sh:11`) would pass.
- Old marker unchanged: dev 66306, ino 56261609, mode 600, 82 B,
  sha256 `092023e438a3c2508574a169becce448fd8d652481547f4a974f20ae5bdca1af`, content
  `{"head": "68357d3d…", "run_id": "6835_20261108_a"}`; the 6835 receipt still matches; no retirement receipt.
- Watcher: pane pid 1388760 (`bash …/trks-watch`) alive; `watch.log` still 3 lines, last
  `2026-11-08T00:46:56Z priority marker seen (…/trackx_evidence.active): pausing`; rev 4's already-paused branch
  would be taken and pass.
- No owned/compute processes: `pgrep -u dowling -af 'r1p_|p3a|llama-server|r1\.tracks|exam_runner'` (fed via
  `bash -s`, no self-match) empty; `nvidia-smi --query-compute-apps` empty; GPU UUID `GPU-ab72fb4a-…`, 236 MiB
  used. Default `tmux ls` = only `trks_watch`; Track P and drill markers absent. Lease free (`flock -n`);
  disk 578,705,072,128 B (539 GiB) ≥ 100 GB.
- `RUN_DIR`/`BATCH`/`~/r1_locks/_to_delete` absent; `r1_tracks/out` inventory exactly
  `smoke/manifest.json` (dev 66306, ino 57039147, 5340 B, dowling:dowling, regular, mtime
  1793323478.0640841870) and `smoke/STOP` (dev 66306, ino 57048195, 0 B, regular, mtime
  1794098816.7435273490).
- 6835 scene intact (batch, handover dir with `b1.exit`=1 / `b1.log` / receipts / scripts / `tmux.sock`,
  private-socket session `b1_6835_20261108_a` alive).
- Staged checkout `fffa45a1…`: HEAD exact, clean (`-uall`), 0 remotes, `fsck --connectivity-only` rc 0; marker
  helper still `8beedc2a…`. Host dates: UTC `2026-11-11T11:00Z`, host-local PST `2026-11-11 03:00` — both date
  guards pass. Only read-only commands were used on `tasl7`; local scratch was removed `/tmp` test dirs.

### Bottom line

Rev 4 fixes F14 with an explicit per-step fail-closed `run_step` (verified: a failing precheck stops before any
upload, and each step's rc is captured and reported), fixes N2 (find failures now stop under
`set -euo pipefail`), N9 and N10, and leaves the previously resolved F1–F13/N1/N3–N8/N10 items intact; only the
four listed files changed and every SHA matches. The current site state still satisfies every precondition
(clean staged checkout at the accepted HEAD, old marker identity matching its receipt, paused watcher with the
directed `smoke/STOP`, no owned/compute processes, free lease, absent run/batch trees, intact 6835 scene and
STATUS checkout at the feature-branch tip). Executing exactly these rev-4 files in the stated order on this
site state is safe and implements the reviewed O2 handover, marker transition, STATUS publication and launch,
with STOP preservation respected; the residuals above (N11 and the negligible diff-error path) are non-blocking
hardening notes.

VERDICT: accepted
