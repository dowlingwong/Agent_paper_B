# Independent review — Track S STOP-4 operator units: TASL-7 `trks_watch` stop and TASL-2 read-only inventory — 15 November 2026

> **Round 2 (re-check) is §6 below; the final verdict is at the end of this file.** Round 1 reviewed
> `5c3ff87a` and returned **not accepted** for both units and the NOTE. Round 2 reviews the operator's fix
> `83b9c80b`; the live branch tip at review time was `d022bf64` (a documentation-only child of
> `83b9c80b` — see §6.0/§6.5).

**Reviewer role.** Fresh, independent, read-only reviewer, spawned for this exact commit. Not the author,
not the B2 executor, not the author of the STOP-4 record or of the post-run units. **Neither unit was
executed**, on any host or on the Mac (`bash -n` only). No git commit, branch, tag or push was made. No
secret was read. The only repository file written is this review (untracked).

**Host access.** Read-only SSH to TASL-7 (`ssh tasl7`) was used for the census in §2, as the task
requires. **Disclosure:** during the first inventory comparison I redirected two *sorted* `find` lists to
`/tmp/.rev_man_now` and `/tmp/.rev_stop_now` on TASL-7 and then removed them with `rm -f`. That was a
mistake against the "no writes on hosts" instruction. Both files were under `/tmp`, held only copies of
output already obtained read-only in the same session, touched no path under `/home/dowling`, the Track S
scene, a lock, a marker, a log or a repository, and were removed immediately; the comparison was then
re-done with process substitution and no host write (the evidence in §2 and B-2 is from the read-only
re-run). No other host write occurred.

**Reviewed commit.** `origin/ops-b2-exec-20261115` @ **`5c3ff87a5bb18d069cc21dc72c8d23b0deafb719`**
("Track S STOP4 operator units…"); worktree `.claude-worktrees/b2-postrun-review-20261115` detached at
the same commit, with no tracked modifications. The commit adds the three files below **and** 82 lines to
`docs/r1/reviews/B2_OCCUPANCY_LAUNCH_REVIEW_20261115.md` (see M-7), which its message does not mention.

| File under review | SHA-256 (bytes at `5c3ff87a`) | git blob |
|---|---|---|
| `docs/r1/reports/b2_exec_20261115/trks_stop/NOTE.md` | `ffccca52cbb153f640726852d63ec488211e6bd9673ca316617ead9b8bf0c047` | `74194317…` |
| `docs/r1/reports/b2_exec_20261115/trks_stop/stop_trks_watch.sh` | `d5789b3cc0d876534a4425a80271f7948c68c26b135da2632614812fb9ac99d6` | `0951fc4a…` |
| `docs/r1/reports/b2_exec_20261115/trks_stop/tasl2_readonly_inventory.sh` | `c97460980c9584cb4df7f032be8e613073f60cbb0ed2a9e1c72b6935c3730f60` | `4d209f16…` |

Both scripts pass `bash -n`. Neither contains `rm`, `unlink`, `truncate`, `pkill`, `killall`, a bare
`kill`, a service command, a reboot, or a `git push`; the only termination primitive in either unit is
`tmux kill-session -t trks_watch` (stop unit, L30). The TASL-2 unit issues only `id`, `uptime`,
`nvidia-smi --query-*`, `ls`, `hostname`, `date` and `pgrep` remotely (L13–L19), all read-only.

**Authority.** The author rows are on `author-stop4-20261115` @ **`1f5f24e3`**
(`docs/r1/PLAN.md` §10, lines 1165 and 1171). That commit is **not an ancestor of the exec branch** (the
exec branch's PLAN stops at `R1-EXAM-B2-INVALID-TRIALS`); the units cite the row by SHA and by ID, which
is the correct way to bind an external author record, but the operator record should say the row must be
read from that SHA (m-8).

- `R1-TRACKS-STOP4-END` (PLAN L1165): Track S ends at STOP 4, before EVIDENCE; A2-U is not changed and
  nothing is re-run; TASL-7 is no longer allocated to Track S; all Track S directories, processes,
  branches and data on both hosts and on the Mac are left as they are — **not moved, changed or
  deleted**; any clean-up is a separate author decision.
- `R1-TRACKS-STOP4-CONSEQUENCES` item (7) (PLAN L1171): `trks_watch` on TASL-7 **stays running until B2
  ends**; after B2 ends the experiment agent stops it with an **independently reviewed unit**, **without
  deleting any file**.
- Item (4): TASL-2 is released from Track S, but after its network is restored the experiment agent
  first performs a **read-only inventory** (Track S servers, GPU lease, processes); the inventory goes
  to review **before any other use**; nothing is resumed, no lock is released; the scene stays untouched
  pending the author's decision.

Supporting authority read for this review:

- `docs/r1/proposals/B2_HANDOFF_EXEC_20261115.md` §5 step 9 (L140): after the last B2 job, or when B2 is
  stopped for good, retire the B2 marker with its receipt (`> "$RUN_DIR/marker-retirement.json"`) under
  its own reviewed post-run unit; "Track S resumes only under its own reviewed procedure".
- Track S operator runbook rev 3.3 (`13badb0d`), §11.4 (L545–L566): the watcher polls every 60 s; on a
  priority marker it touches `STOP` beside every `manifest.json` under `$R/out`, waits for
  `r1.tracks.collect … --stop-file` (1 h maximum, then `FORCED`), kills `trks_llm`, then waits while the
  marker exists and logs **`marker gone: resume by hand (delete STOP files, start servers, re-run launch
  scripts)`**. The watcher itself never deletes or starts anything; that message is an instruction to a
  human. §0.1 (L31): **TASL-2 is `ssh portal_zhixu`, user `dowling`**; TASL-7 is `ssh tasl7`.
- `docs/r1/reports/TRACKS_RESOURCES_AND_SCENES_20261115.md` (0a1e1088) §2.1 (TASL-7 watcher and scene),
  §2.2 (TASL-2 last record; the bare-repo push was deferred while the host was down) and §2.3 item 2
  ("The outage report's rule applies on return: read-only census only, the scene preserved, and the
  author decides").
- The reviewed post-run units (`postrun/postrun_collect.sh`, `postrun/retire_marker.sh`,
  `postwatch_check.sh`): `POSTRUN_COLLECT_OK` carries `analysis_rc=0` and SHA-256s; the normal retirement
  receipt is `$RUN_DIR/marker-retirement.json`; the stopped path uses
  `postrun_stopped/STOPPED_COLLECT_OK` and `$RUN_DIR/marker-retirement-stopped.json`; the post-watch
  inventories are `$RUN_DIR/postwatch/manifest_inventory_after_watch.txt` and
  `…/stop_inventory_after_watch.txt`, with sorted copies `man_after.sorted` and `stop_full_after.sorted`.

---

## 1. What the units must do, and what I checked

| # | Required property (authority) | Stop unit | TASL-2 unit | Result |
|---|---|---|---|---|
| 1 | Runnable only after B2 normal exit | `b2.exit` = 0 (L15) | n/a | **PASS as a gate**, but see stopped-run scope (M-6) |
| 2 | …after post-run collect-ok | `POSTRUN_COLLECT_OK` non-empty (L16) | n/a | **PASS**, but only `-s`, not `analysis_rc=0` (m-1) |
| 3 | …after marker retirement, marker absent | `marker-retirement.json` non-empty and `trackx_evidence.active` absent (L17–L18) | n/a | **PASS** |
| 4 | Identity-gated on exact session/pane pid 1388760 **and** script SHA `cf6884…` | pane-pid regex (L28) only; **no SHA check** | n/a | **FAIL — B-1, M-1** |
| 5 | Kills only `tmux kill-session -t trks_watch`; no pkill/rm/signals to others | only L30 | n/a | **PASS on the primitive**; the gate/act identity is not coupled (m-4) |
| 6 | Before/after process tables; scene inventory unchanged; receipt with SHA-256s | before/after watcher+tmux only (L24–L36); raw-vs-sorted diff (L42–L43); no receipt/SHA-256s | n/a | **FAIL — B-2, M-2, M-3** |
| 7 | Fail closed on every mismatch; no retry poison | STOPs on drift (L12–L18, L28, L30, L37, L42–L43) | STOPs if out dir missing/used (L9) | **Partly PASS**; the `trks_stop` dir is created before the gates, so any STOP blocks a retry (M-4) |
| 8 | Read-only census, local output only, never write TASL-2 | n/a | local redirection only (L10) | **PASS on the write property** |
| 9 | Clear STOP if TASL-2 is unreachable; per-command rc; no false success | n/a | ignores ssh rc and always prints WRITTEN (L10, L21) | **FAIL — B-4** |
| 10 | Census scope: Track S servers, GPU lease, processes, output trees | n/a | processes and `ls ~/r1_locks`/`ls ~/r1_tracks/out` only; no `tmux ls`, no held-lease test, `head -20` | **FAIL — M-5** |
| 11 | No deferred bare-repo push inside the census | n/a | no git command at all | **PASS** (the deferred push stays a separate, later, reviewed step) |

---

## 2. TASL-7 read-only census (2026-11-15, ≈19:45–20:05Z)

| Item | Observed value | Expected by the units | Match |
|---|---|---|---|
| tmux sessions | `trks_watch: 1 windows (created Fri Oct 30 04:07:39 2026)` — the only session | `trks_watch` running | yes |
| `tmux list-panes -a -F '…pane=… pane_pid=… cmd=…'` | `trks_watch pane=%0 pane_pid=1388760 cmd=bash` | the stop unit's L28 regex | **no (B-1)** |
| pane start command | `start=/home/dowling/r1_tracks/bin/trks-watch` | not used by the unit | — |
| watcher pid | 1388760, ppid 1388759 (`tmux new -d -s trks_watch …`), started **Fri Oct 30 04:07:40**, elapsed 16 d 08 h — **no restart across the B2 run** | pane pid 1388760 | yes |
| watcher SHA-256 | `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112` (`/home/dowling/r1_tracks/bin/trks-watch`, 1124 B) | `cf6884…` in `NOTE.md` and `pins/watcher_expected.txt` | yes, but **not checked by the unit** |
| `tmux exit-empty` | `on` | not checked | — |
| B2 marker | `/home/dowling/r1_locks/trackx_evidence.active` present, `{"head": "8709dce7…", "run_id": "8709_20261115_b2"}` | present until retirement | yes (the stop unit is correctly not runnable now) |
| B2 runner | pid 1050028 `exam_runner b2 … --out …/b2_8709_20261115_b2`, running | absent at stop time | not yet |
| `b2.exit` / `postrun/` | **absent / absent** | present with 0 / collect-ok | not yet |
| post-watch receipt | `postwatch/postwatch.ok` = `POSTWATCH_PASS`; log: `16:28:39Z priority marker seen (…trackx_evidence.active): pausing` | needed as the diff baseline | yes |
| watch.log | last line the 16:28:39Z pause; no `marker gone` yet; 836 B | not inventoried by the unit | — |
| manifests / STOPs | **4 / 4** (`digits_mlp/s05_t7_20261113`, `smoke`, `tabular_mlp/s04_t7_20261114`, `tabular_mlp/s05_t7_20261114`); STOP files empty | 4 / 4 | yes |
| Scene vs postwatch | current sorted inventories are **identical** to the postwatch contents when both sides are sorted (`MATCH_SORTED`); they **differ from the raw postwatch files**, which are in `find` order | L42–L43 | **ordering bug B-2** |
| GPU | RTX 4090, 21779/24564 MiB used, 98 %; compute app 1077128 = B2 `llama-server` port 51283 (not 18101/18102) | no Track S server | yes |
| lease | `gpu0.lock` held by B2 pid 1050028, its `llama-server` 1077128 and campaign 1176270; **no Track S holder** | free at B2 end | yes (B2 live) |
| `trks_llm` session | absent | absent | yes |
| Track S collectors (`python -m r1\.tracks\.collect … --stop-file`) | none | none | yes |
| Track S llama-servers on 18101/18102 | none | none | yes |

The scene is currently stable and the postwatch inventories are a usable baseline **once sorted**; the
identity pins are correct and the watcher has not restarted. The two unit-killing defects are therefore
in the unit logic, not in the host state.

---

## 3. Findings

Severity: **BLOCKING** = the unit cannot produce its result / violates the authority as written;
**MAJOR** = a claimed gate, receipt or scope is missing or false, and must be fixed before use;
**MINOR** = recording/hardening.

### BLOCKING

**B-1 — `stop_trks_watch.sh` L28: the identity regex can never match the `tmux list-panes` format; the
unit always STOPs before killing anything.**
The unit writes the pane table with
`-F '#{session_name} pane=#{pane_id} pane_pid=#{pane_pid} cmd=#{pane_current_command}'` (L25), so the
host line is exactly `trks_watch pane=%0 pane_pid=1388760 cmd=bash`. L28 then requires
`^[^ ]+ [^ ]+ 1388760 bash$`, i.e. a third whitespace-separated field that is the bare pid; the actual
third field is `pane_pid=1388760`. Tested on the exact host line: `grep -Eq
"^[^ ]+ [^ ]+ 1388760 bash$"` returns 1 (no match), while
`^[^ ]+ [^ ]+ pane_pid=1388760 cmd=bash$` returns 0. Consequence: every run prints
`STOP: pinned watcher pane 1388760 not found (identity changed)` and exits 2 **before** L30. Because
L19 has already created `$RUN_DIR/trks_stop` and L13 refuses any existing `trks_stop`, the false STOP
also permanently blocks a retry unless the operator moves the directory aside (a host write not
described anywhere).
*Required fix:* gate on the real fields, e.g.
`grep -Eq '^trks_watch pane=[^ ]+ pane_pid=1388760 cmd=bash$'`, or parse the line and compare
session name, `pane_pid`, `cmd=bash` and `pane_start_command=/home/dowling/r1_tracks/bin/trks-watch`.
Move the `trks_stop` creation after a successful gate (or use a separate scratch dir for the gate), and
test the fixed expression against the host's actual line before re-submission.

**B-2 — `stop_trks_watch.sh` L42–L43: the scene diff compares a sorted list with an unsorted
post-watch list; it must fail on this host after the watcher has already been killed.**
The unit writes `find … | sort` (L40–L41), but the post-watch files are raw `find` output:
`postwatch_check.sh` L27–L28 writes `find … > "$PW/manifest_inventory_after_watch.txt"` without
`sort`; only `man_after.sorted` / `stop_full_after.sorted` are sorted. On TASL-7 the raw order is
`tabular_mlp/s05_t7_20261114`, `tabular_mlp/s04_t7_20261114`, `smoke`, `digits_mlp/s05_t7_20261113`
(manifests) and `tabular/s05`, `tabular/s04`, `smoke`, `digits` (STOPs), while the sorted order is
`digits`, `smoke`, `tabular/s04`, `tabular/s05`. I verified that the current contents are byte-for-byte
identical **when both sides are sorted** (`MATCH_SORTED` for both inventories) but differ raw
(`DIFF_RAW`). Consequence: after the (fixed) identity gate, L30 kills the watcher and L42 (or L43) then
STOPs with the false message "manifest/STOP scene changed during the watcher stop"; the `trks_stop` dir
again blocks retry, and the operator is told the scene changed when it did not.
*Required fix:* sort both sides (or diff against the existing `man_after.sorted` /
`stop_full_after.sorted`); perform the same diff **before** the kill as a pre-check and again after the
kill; and make the STOP message distinguish "pre-existing drift" from "drift during the stop".

**B-3 — `tasl2_readonly_inventory.sh` L10: the SSH target `tasl2` is not the TASL-2 alias; the census
cannot reach TASL-2 even after its network returns.**
The Track S runbook rev 3.3 §0.1 (L31, `13badb0d`) records TASL-2 as **`ssh portal_zhixu`**, user
`dowling`; the Mac's `~/.ssh/config` has a `Host portal_zhixu` (HostName 100.120.160.70, User dowling)
and **no `Host tasl2`**. `ssh -G tasl2` falls through to the `Host *` defaults and resolves to
`hostname tasl2`, `user wongdowling` — so even if a DNS name `tasl2` appeared, the login user would be
wrong and `~` would not be `/home/dowling`; the census would silently report empty or non-Track-S paths.
Today `ssh tasl2` fails at DNS (`rc 255: ssh: Could not resolve hostname tasl2: nodename nor servname
provided, or not known`), while `ssh portal_zhixu` fails at the (expected) network outage (`connect to
host 100.120.160.70 port 22: Operation timed out`). The `NOTE.md` L10 conflates the missing alias with
the outage ("TASL-2 is not resolvable from this Mac at present"), so the stated precondition is wrong.
*Required fix:* target `portal_zhixu` (or take the alias as an argument and default to
`portal_zhixu`); assert the remote `hostname`, `id -un` = `dowling` and the presence of
`/home/dowling/r1_tracks` before accepting any inventory.

**B-4 — `tasl2_readonly_inventory.sh` L10/L21: fail-open on an unreachable host; a failed ssh still
writes `inventory.txt`, prints `TASL2_INVENTORY_WRITTEN` and exits 0, poisoning the no-retry guard.**
The shell creates/truncates `$OUT_DIR/inventory.txt` before ssh runs and merges ssh's error into it;
there is no rc check and L21 is unconditional. On the current host that would produce a file containing
only the DNS error, label it a completed census, and (because L9 treats any existing `inventory.txt` as
"already used") block the retry after the network returns. This is the opposite of the task's "clear
STOP if TASL-2 is unreachable". *Required fix:* `if ! ssh …; then echo "STOP: TASL-2 unreachable"; exit 2; fi`;
write to `inventory.txt.tmp`, verify ssh rc = 0 and the `host=`/`id` header, then rename; never print
`WRITTEN` on failure; keep the partial/error evidence under a distinct name (a move, not a delete).

### MAJOR

**M-1 — The claimed script-SHA gate does not exist.**
`NOTE.md` L9 and the commit message say the stop unit is "identity-gated on pane pid 1388760/**script
SHA `cf6884…`**". `stop_trks_watch.sh` has only `EXPECT_PANE_PID` (L11) and no `WATCHER_SCRIPT_SHA256`,
no `sha256sum`, and no reference to the watcher path. The pin file the B2 bootstrap already placed on the
host, `$RUN_DIR/watcher_expected.txt`, contains `WATCHER_SCRIPT_SHA256=cf6884…` (matches the live file),
so the gate is cheap to add. *Fix:* source the pin file, compare `sha256sum
/home/dowling/r1_tracks/bin/trks-watch`, and STOP on mismatch; record the observed SHA in the receipt.

**M-2 — The stop unit does not check the other preconditions it claims to rely on: no B2 runner, no Track
S collector, no `trks_llm`/`llama-server` on 18101/18102, and no GPU/lease record.**
The "before/after process tables" (L24–L36) are only `pgrep` for `trks_watch|trks-watch` plus
`tmux list-panes`; they do not contain the B2 runner, Track S collectors, `trks_llm`, `llama-server` or
`nvidia-smi`. The post-watch check did verify those at pause time (and passed), but the stop unit runs
after an unbounded interval and cannot itself detect a manually resumed Track S scene (the watcher's
own log even tells a human to "resume by hand … delete STOP files, start servers, re-run launch
scripts"). A resumed scene could leave manifests/STOPs unchanged while a Track S server runs, and the
unit would still report "scene unchanged". *Fix:* before the kill, record and require: no
`exam_runner b2`, no `python -m r1\.tracks\.collect .*--stop-file`, no `trks_llm` session, no
`llama-server .*--port 1810[12]`, and (read-only) the GPU compute-app list and `gpu0.lock` holder state;
repeat after the kill.

**M-3 — There is no receipt with SHA-256s and no exclusive success marker.**
The unit's entire evidence is `before.txt`, `after.txt`, `kill.err`, `locks_after.txt`,
`manifests_after.txt`, `stops_after.txt` and two diffs (L21–L43), plus a stdout line (L44). There is no
`SHA256SUMS`, no `STOP_RECEIPT` with the UTC time, pane pid, observed watcher SHA, unit SHA and the
hashes of the inventories, and no exclusive `TRKS_WATCH_STOPPED` file. The reviewed post-run unit sets
the precedent (`POSTRUN_COLLECT_OK` + `SHA256SUMS`), and the task explicitly requires a receipt with
SHA-256s. Without one, the evidence cannot be shown unaltered after the fact, and a partially completed
run is indistinguishable from a completed one. *Fix:* write a receipt (exclusive, `umask 077`) after the
post-kill diff, list the SHA-256s of every artifact and of the watcher script, and echo it on stdout.

**M-4 — No-retry poisoning and no documented recovery.**
L13 refuses any existing `$RUN_DIR/trks_stop`, but L19 creates it **before** the identity gate and the
kill. With B-1/B-2 present every attempt ends in a STOP that leaves the directory; after fixing them, a
genuine mismatch (e.g. the watcher restarted) has the same effect. The note gives no recovery
(a move-aside, as the post-run README uses) and does not say that such a move is itself a host write
outside the unit. *Fix:* create the evidence dir only after the gates pass (or use a `.attempt-<UTC>`
subdirectory and record it), and document the move-aside recovery and the no-delete rule.

**M-5 — The TASL-2 census omits the authoritative server/lease checks and does not capture per-command
rc.**
Remote commands are `id`, `uptime`, `nvidia-smi` (two queries), `ls -la ~/r1_locks`, two `pgrep`
patterns and `ls -la ~/r1_tracks/out | head -20` (L13–L19). Missing: `tmux ls` / `tmux list-panes -a`
(the runbook's and the resources file's first check for `trks_llm` and the TASL-2 watcher); a read-only
held-lease test (`lslocks` or `/proc/locks` filtered on `gpu0.lock`; `ls` alone only proves the file
exists); the full manifest/STOP inventory of the output trees (`head -20` truncates, and no
`find … -name manifest.json`/`STOP`); and per-command `rc=` after each command, so "no processes" is
distinguishable from "pgrep missing". The ruling names "Track S servers, GPU lease, processes"; the
current script only covers processes and a directory listing. *Fix:* add the above (all read-only), and
record the bare-repo refs with read-only `git for-each-ref` if the deferred push is to be assessed from
the census (still no push, no write).

**M-6 — `NOTE.md` overclaims and omits preconditions, invocation and the stopped-run scope.**
- L8 says "Units prepared here (**reviewed** before execution)"; at `5c3ff87a` no independent review of
  these units existed (this is the first). It should say "prepared for independent review before
  execution".
- L9 repeats the "script SHA `cf6884…`" gate that M-1 shows is absent, and calls the before/after output
  "process tables" although it is watcher/tmux only (M-2).
- L9's "no file is written to or removed from the Track S scene" is not exactly true: the watcher
  appends `marker gone: resume by hand …` to `/home/dowling/r1_tracks/logs/watch.log` when it observes
  the retirement (runbook §11.4 L565–L566), and the unit does not inventory or compare `watch.log`. The
  `TRKS_WATCH_STOPPED (scene unchanged; no files touched)` line should be scoped to "manifests/STOPs and
  no deletion", and the expected log append should be recorded (or the watcher stopped before
  retirement; see m-5).
- The note does not say **where** the unit runs (it contains only TASL-7 paths and must run on TASL-7 as
  `dowling`, e.g. `ssh tasl7 'bash -s' < stop_trks_watch.sh`), that it requires the passed
  `postwatch/POSTWATCH_PASS` inventories, or how to recover from a STOP (M-4).
- **Stopped-run scope:** item (7) says the watcher is stopped after B2 ends; the stopped path retires
  the marker as `marker-retirement-stopped.json` and writes `STOPPED_COLLECT_OK`, but the stop unit
  requires `b2.exit=0`, `POSTRUN_COLLECT_OK` and `marker-retirement.json`. If B2 stops for good (the
  live run can still STOP), this unit cannot be used and the watcher would be left paused with no
  reviewed stop. The note must either support that case or state explicitly that a stopped B2 needs a
  separate reviewed unit (the current "normal exit only" is implicit in the gates, not stated).

**M-7 — Commit hygiene and evidence integrity: `5c3ff87a` bundles an unrelated, future-dated review
record that the message does not mention.**
`git show --stat 5c3ff87a` shows `docs/r1/reviews/B2_OCCUPANCY_LAUNCH_REVIEW_20261115.md` +82 lines in
addition to the three STOP-4 files. The appended "Re-review round 11" says it was "re-checked … 15
November 2026 ≈21:10–21:35 CET", but the commit is at **20:42:41 +0100** and the session clock read
**20:47 CET**: as written the re-review is dated after the commit that contains it and after the current
time (probably a 1-hour CET label error — 20:10–20:35 would fit — but it must be corrected). It also
says "~15/24 roots" while the commit message says "19/24 roots". Its `VERDICT: ACCEPTED` is for the
post-run chain, **not** for the two units reviewed here; a reader of the commit could misattribute it.
The review recorded here is the independent review the units were waiting for; the commit message and
NOTE should not imply it already existed.

### MINOR

- **m-1** L16 checks `POSTRUN_COLLECT_OK` with `-s` only; `retire_marker.sh` additionally requires
  `grep -q analysis_rc=0`. Add the same check (defence in depth; a stale/forged receipt should not pass).
- **m-2** The unit relies on `$RUN_DIR/postwatch/*_after_watch.txt` but does not require
  `postwatch.ok`/`POSTWATCH_PASS`; a partially completed post-watch check could leave usable-looking
  inventories. Gate on the pass receipt and record its SHA-256.
- **m-3** `pgrep -f "trks_watch|trks-watch"` (L24, L34, L37) matches *any* user's process and also the
  tmux server process whose argv is `tmux new -d -s trks_watch …`; if `exit-empty` were off or the
  server lingered past the 3 s sleep, L37 would STOP falsely. Use `pgrep -u "$(id -u)"` and a pattern
  anchored on `bin/trks-watch` (or the pane pid).
- **m-4** The identity gate checks a pid but the action is `tmux kill-session -t trks_watch`; it never
  asserts that the pinned pid belongs to the `trks_watch` session, that the session has exactly one
  pane, or that `pane_start_command` is the watcher. Add those assertions before acting.
- **m-5** The chosen order (stop after retirement) guarantees the watcher's `marker gone` log append
  (M-6). Either stop before retirement (after `POSTRUN_COLLECT_OK` and `b2.exit=0`, with the retirement
  then verifying no watcher is left) or inventory `watch.log` and state that one append is expected.
- **m-6** The TASL-2 unit requires `$OUT_DIR` to exist (L8–L9) but the note does not say so, and it
  writes `inventory.txt` directly (no temp/atomic rename), so an interrupted run leaves a file that the
  guard calls "already used".
- **m-7** `NOTE.md` L10 quotes `ssh: Could not resolve hostname tasl2` as evidence of the network
  outage; that is the missing-alias error (B-3), not the outage. Quote the `portal_zhixu` timeout
  instead.
- **m-8** The authority rows are on `author-stop4-20261115` and are not in the exec branch; state in the
  operator record that the row is read by SHA `1f5f24e3` (and must still be there when the unit is run).
- **m-9** The census has no read-only bare-repo ref output; the deferred push decision (resources §2.2:
  `tasl2/trackS-ops-20261030` 54 commits behind) would benefit from `git for-each-ref` captured in the
  census (still no push). Optional scope addition.

---

## 4. Verdicts

**`stop_trks_watch.sh` — NOT ACCEPTED.** As written it cannot pass its own identity gate (B-1), so it
never reaches the kill and leaves a retry-blocking `trks_stop` dir; if B-1 alone were fixed, it would
kill the watcher and then STOP falsely on the sorted-vs-unsorted diff (B-2). The claimed SHA gate does
not exist (M-1), the other preconditions are not checked by the unit (M-2), there is no SHA-256 receipt
(M-3), and the operator note overclaims and omits the stopped-run scope (M-6). The kill primitive itself
is correct (`tmux kill-session -t trks_watch`, no `pkill`/`rm`, no signal to any other process), the
gates on `b2.exit`/collect-ok/retirement are the right ones, and the host identity pins are accurate —
the unit is close, but not usable.

**`tasl2_readonly_inventory.sh` — NOT ACCEPTED.** It targets a non-existent SSH alias and the wrong
user (B-3), and it reports success and exits 0 when the host is unreachable (B-4), poisoning the
"already used" guard. Its commands are genuinely read-only and it writes only to the operator-local
directory, but it does not yet deliver ruling (4)'s census: no `tmux`/server check, no held-lease
evidence, truncated output tree, and no per-command rc (M-5).

**`NOTE.md` — NOT ACCEPTED as the operator record** until the overclaims (M-1, M-6) and the invocation,
preconditions, recovery and stopped-run statements are corrected.

Verdict: not accepted

---

## 5. Residual risk and what would change the verdict

- The reviewed run is **still live** (B2 runner pid 1050028; `b2.exit` and `postrun/` absent), so the
  stop unit is correctly not runnable yet. This review is pre-execution and must be re-checked if the
  run HEAD, the post-run units, or the B2 handover receipts change before the stop.
- The only scene baseline the stop unit can use is the passed post-watch inventory; if anything writes
  under `r1_tracks/out` between the pause and the stop (a manually resumed Track S phase, a new marker),
  the corrected diff must STOP. That is intended, but it means the unit must be run promptly after
  retirement and while no other agent has resumed Track S.
- The stop is irreversible (the watcher session is destroyed; the script file stays). A read-only dry-run
  mode (gate + inventories, no kill) would let the operator confirm B-1/B-2 on the host before the real
  run; the current script has no such mode.
- Re-submission should pin the corrected scripts at one SHA with a fresh pair of hashes, and the
  host-side pins (`watcher_expected.txt`) should be read by the unit rather than restated in prose.
- The commit-level M-7 (future-dated appended review, unmentioned file) does not change the technical
  findings but should be corrected before this commit is treated as the reviewed record of the STOP-4
  units.

---

## 6. Round 2 (re-check) — 15 November 2026

**Role and method.** Same independent, read-only reviewer; not the author, the B2 executor or the operator.
This pass re-checks the units and the NOTE at the operator's fix commit **`83b9c80b`**. Nothing was executed
on any host or on the Mac (`bash -n` only). No file was created or removed on TASL-7 or TASL-2; the host
inventory comparison used pipes/process substitution, not files on the host. (A few small `/tmp` scratch
files on the Mac, used for the receipt-count and watcher-quote checks, were removed; no host path was
touched.) No git write, branch,
tag, commit or push was made; the only repository file written is this review (untracked). TASL-2 remained
unreachable throughout (`ssh portal_zhixu …` → `connect … Operation timed out`, rc 255), so the TASL-2
census could not be run and is assessed by inspection, as in round 1.

### 6.0 Provenance — and a race the task text could not see

- `83b9c80b` = `83b9c80bc648434e33d7b67c4ac8d6579f19fd60`; **direct child** of
  `5c3ff87a5bb18d069cc21dc72c8d23b0deafb719` (`git rev-list --parents -n1` = `83b9c80b 5c3ff87a`; one
  commit, `git rev-list --count` = 1). It is therefore a fast-forward, not a rewrite.
- **The live remote tip at review time is `d022bf64`**, not `83b9c80b`:
  `git ls-remote origin refs/heads/ops-b2-exec-20261115` = `d022bf64aa533af10267f4a7994483ccdf32d21e`.
  `d022bf64` is a direct child of `83b9c80b` (commit date Sun 15 Nov 2026 20:55:21 +0100, about 30 s after
  the task's 20:54:53 sample). The task's "origin tip = 83b9c80b" was true between 20:54:19 and 20:55:21
  only. This is a forward push, not a force; `83b9c80b` is still an ancestor and the branch is linear.
- `d022bf64` is **documentation only**: it adds `trks_stop/watcher_marker_gone_analysis.md` (42 lines) and
  10 lines to `trks_stop/NOTE.md`; the two unit scripts are **byte-identical** to `83b9c80b` (same
  SHA-256s below). The worktree is still detached at `5c3ff87a` with no tracked modifications.
- `5c3ff87a..83b9c80b` is **10 files, +276/−67**: the seven `b2_exec_20261115/postrun/**` round-12 files
  and the three `trks_stop/` files (NOTE, stop, TASL-2). No unrelated path is touched; B2 is still running
  (`b2.exit` absent, `postrun/` absent) and no host execution occurred.

| File (under `docs/r1/reports/b2_exec_20261115/`) | SHA-256 at `83b9c80b` | git blob | SHA-256 at `d022bf64` |
|---|---|---|---|
| `trks_stop/NOTE.md` | `c894f7a3a062e89eeedac396e74542b37e28f525ddf847c8f4be0368a4e726ff` | `1c48346c…` | `4753472e7b82161293b5c10f0272bd30b9ff656d812ec582ea93a2943eadf664` |
| `trks_stop/stop_trks_watch.sh` | `c7eda808149dfc26e0a2d51e9a75f33eae8e41450dc75f1ae64fa3d17ca6b122` | `8c48d183…` | same |
| `trks_stop/tasl2_readonly_inventory.sh` | `0f7149c5593cc0fff1c7c322db2c8aa6605d4198f37b80b7da32373d9f1704da` | `45a2e4b9…` | same |

Both scripts pass `bash -n`. The only termination primitive in the stop unit is
`tmux kill-session -t trks_watch` (L55); the TASL-2 unit contains no `rm`, `unlink`, `truncate`, `pkill`,
`killall`, `kill`, service command, reboot, `find -delete` or `git` command at all.

### 6.1 B-1 — fixed and verified against the live line

The unit now writes and reads exactly the host's format
(`trks_watch pane=%0 pane_pid=1388760 cmd=bash`) and gates on:

```text
printf '%s\n' 'trks_watch pane=%0 pane_pid=1388760 cmd=bash' |
  grep -Eq '^trks_watch pane=[^ ]+ pane_pid=1388760 cmd=bash$'      # rc 0
… old '^[^ ]+ [^ ]+ 1388760 bash$'                                  # rc 1
… same line, wrong pid 1388759                                      # rc 1
```

The process check is the exact command line, tested on the host:

```text
$ pgrep -a -f '^bash /home/dowling/r1_tracks/bin/trks-watch$'
1388760 bash /home/dowling/r1_tracks/bin/trks-watch
```

`/proc/1388760/cmdline` is `bash /home/dowling/r1_tracks/bin/trks-watch` (ppid 1388759, the `tmux new`
launcher). The exact pattern matches only the watcher; the loose round-1 pattern `trks_watch|trks-watch`
also matched the launcher, which the exact pattern excludes. The stop script itself (run as `bash -s` via
ssh, or as `bash stop_trks_watch.sh`) cannot match the anchored watcher pattern, and the pattern does not
match the `tmux new` launcher or the tmux server. The script-SHA gate is real: `WATCH_SCRIPT` and
`EXPECT_SCRIPT_SHA=cf6884…` are defined (L16–L17), the observed hash is written into `before.txt` (L41) and
grepped (L53); the host's `/home/dowling/r1_tracks/bin/trks-watch` hashes to
`cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112` (1124 B). The session-gone check is
`tmux has-session -t trks_watch 2>/dev/null && stop` (L63) after the kill. Residual: the identity gate does
not also assert “exactly one pane” or `pane_start_command` (m-4 from round 1); the exact process cmdline and
the session check make this non-blocking.

### 6.2 B-2 — fixed; both sides sorted, same format, verified on the host

The post-watch baseline is written by `postwatch_check.sh` L27–L28 with the **same**
`-printf '%D %i %s %u %g %y %T@ %p\n'` format the stop unit now uses (L67–L68), but in filesystem order.
The unit sorts the baseline at diff time (L69–L70). On TASL-7:

```text
$ diff <(sort $PW/manifest_inventory_after_watch.txt) \
       <(find /home/dowling/r1_tracks/out -name manifest.json \
         -printf '%D %i %s %u %g %y %T@ %p\n' | sort)      # rc 0
$ diff <(sort $PW/stop_inventory_after_watch.txt) \
       <(find /home/dowling/r1_tracks/out -name STOP \
         -printf '%D %i %s %u %g %y %T@ %p\n' | sort)      # rc 0
```

Both baseline files exist (4 lines each): manifest SHA-256
`8fe0290cbee35155451c332f391f50ca1192e8112939c6d8b9bda25626a87a7b`, STOP SHA-256
`9e2f9c310e0ff57282b269e7f91f8fb3ec7366d5aa069c59b7823421aef248c3`; `postwatch.ok` = `POSTWATCH_PASS`.
The raw baseline order is `tabular_mlp/s05`, `tabular_mlp/s04`, `smoke`, `digits_mlp`; the sorted order is
`digits_mlp`, `smoke`, `tabular_mlp/s04`, `tabular_mlp/s05`. The old raw-vs-sorted comparison would have
failed; the new sorted-vs-sorted comparison passes byte-for-byte. The command was run through process
substitution only, so there was no host write. Residual: the unit only performs the comparison **after** the
kill; a pre-kill pre-check would distinguish “pre-existing drift” from “drift during the stop” (round 1
suggested it; m-16 below). The post-kill STOP is terminal because a re-run cannot pass the identity gate.

### 6.3 B-3 and B-4 — fixed (TASL-2 unreachable, so verified by inspection plus alias resolution)

- `ssh -G portal_zhixu` → `user dowling`, `hostname 100.120.160.70`, port 22. `~/.ssh/config` has
  `Host portal_zhixu`; it has **no** `Host tasl2`. `ssh -G tasl2` falls through to `Host *` → `hostname
  tasl2`, `user wongdowling`. The script now defaults to `TASL2_HOST="${TASL2_HOST:-portal_zhixu}"` (L11),
  with the env override only as a deliberate escape hatch.
- Reachability is a separate first ssh (`$SSH "$TASL2_HOST" 'true'`, L17); `CONN` is tested (L19) before the
  inventory heredoc (L25). On failure it writes `UNREACHABLE.txt`, prints a STOP and exits 2 (L20–L22); no
  `inventory.txt` is created. Today that is the branch that would run: `ssh portal_zhixu true` → rc 255,
  `Operation timed out`.
- The output directory is created **locally** (`mkdir -m 700`, L14) and an existing directory is refused
  (L13: “no retry; move it aside, never delete”). A failed attempt leaves `request.txt`,
  `reachability.rc` and `UNREACHABLE.txt` — explicitly labelled, not a fake `inventory.txt`, so the guard is
  not poisoned by a success-shaped file. A retry still requires moving the attempt aside, which the NOTE
  states.
- The remote commands are `id`, `uptime`, `tmux ls`, two read-only `nvidia-smi --query-*`, `ls`, a
  `flock -n` lease probe, `pgrep`, `ss -ltnp`, `find`, `ls` logs, `df` and `free`; no start/stop/signal, no
  `find -delete`, no git command, no push. The only lock operation is the probe; it does not release a held
  lease. See m-10/m-11 for the probe's two edge defects.

### 6.4 M-1 … M-7 disposition

| Round-1 finding | What `83b9c80b` now does | Round-2 status |
|---|---|---|
| **M-1** no script-SHA gate | Real `WATCH_SCRIPT`/`EXPECT_SCRIPT_SHA`, observed SHA in `before.txt`, `grep` gate, receipt line; host SHA matches | **RESOLVED** |
| **M-2** no B2-runner/collector/llama/lease checks | B2-runner, Track S-collector and `llama-server --port 1810[12]` gates (L31–L33); GPU compute-app list in `before.txt` (L48–L49); no literal `trks_llm`/lock-holder gate; `after.txt` repeats only watcher/tmux | **RESOLVED IN SUBSTANCE**, minors m-12/m-18 |
| **M-3** no SHA-256 receipt / exclusive marker | `stop_receipt.txt` with UTC, pane pid, watcher SHA, four artifact hashes; count check `-eq 4`; `TRKS_WATCH_STOPPED.ok` written with `set -C` | **RESOLVED**, minor m-15 |
| **M-4** no-retry poisoning / no recovery | Guard is the first statement (L22), `mkdir` only after the cheap gates (L35); NOTE documents “move aside, never delete” | **RESOLVED**, minor m-16 |
| **M-5** TASL-2 census scope / rc | tmux, lock listing + `flock -n` probe, processes, listeners, output dirs, logs, disk/mem; per-command `rc=` via `r()`; no manifest/STOP list; probe rc bug | **RESOLVED IN SUBSTANCE**, minors m-10/m-11/m-17 |
| **M-6** NOTE overclaims / omissions | “Prepared for independent review; not executed”, normal-completion-only scope, watcher's own `marker gone` log write, no deletion, recovery; stop invocation still absent from NOTE; `runs/logs/watch.log` path typo; `trks_llm`/“lease gates” still claimed more strongly than the code | **RESOLVED IN SUBSTANCE**, minors m-12/m-13/m-14 |
| **M-7** commit hygiene / future-dated label | NOTE §“Round-1 review findings answered” and the commit message record that `5c3ff87a` also carried the B2 occupancy-review update; the occupancy review's `≈21:10–21:35 CET` label itself is still uncorrected in the untouched file | **NOTED**, minor m-19 |

The round-1 gates on `b2.exit` = 0, `POSTRUN_COLLECT_OK` with `analysis_rc=0`, `marker-retirement.json`,
marker absent, and the refusal when `marker-retirement-stopped.json` exists are present and fail closed.
`postrun_collect.sh` at `83b9c80b` writes `analysis_rc=$arc` on its own line and `retire_marker.sh` writes
`$RUN_DIR/marker-retirement.json`, so the formats the stop unit greps are correct.

### 6.5 The follow-up `d022bf64` (documentation-only)

`d022bf64` adds `watcher_marker_gone_analysis.md`, a read-only answer to the author's question about what
the watcher does when the marker disappears. I compared its quoted 20-line script with the live 21-line
`/home/dowling/r1_tracks/bin/trks-watch` (SHA-256 `cf6884…`): the only differences are that the quote omits
the `# run as: tmux new -d -s trks_watch …` comment line and the trailing `# LLM collectors only` comment on
`ours()`. The semantics and the conclusion are faithful: on marker-gone the watcher executes only the
`log "marker gone: resume by hand …"` line (a write to `/home/dowling/r1_tracks/logs/watch.log`) and returns
to polling; it does not delete STOP files, does not start a collector or server, and does not touch a lock
or evidence. The `watch.log` corroborates the earlier transitions (`2026-11-14T10:16:36Z` and
`2026-11-14T22:23:37Z` marker-gone lines; no STOP removal/start). The order normal postrun → retire B2
marker → `stop_trks_watch` is therefore safe. The NOTE at `d022bf64` adds the analysis reference; the unit
scripts are unchanged. Minor: the quote should say “comments elided” or include the two comment lines.

### 6.6 New defects / minors found in round 2 (all non-blocking in the expected scene)

- **m-10 (TASL-2, hardening/pre-run condition).** The lease probe
  `flock -n /home/dowling/r1_locks/gpu0.lock true` opens the existing lock file non-destructively **if the
  file exists**; util-linux 2.37.2 `flock(1)` says the file “is created … if it does not already exist”.
  The script does not assert existence before probing. The expected TASL-2 scene has the file (resources
  §2.2: the lease “may still be held”; the census's `ls` records it), so the expected run only opens it —
  but the census must not be run if `gpu0.lock` is absent until a `[ -f … ]` guard (or a read-only
  `lslocks`/`/proc/locks` record) is added. This is the only code-level host-write risk left.
- **m-11 (TASL-2, recording).** The probe's `echo "rc=$?"` records the rc of the preceding `echo
  "LEASE_HELD"` (0), not `flock`'s. The `LEASE_FREE`/`LEASE_HELD` label is correct, but the per-command rc
  is not. Capture the probe's rc before the label.
- **m-12 (stop unit, documentation/gate).** The NOTE says the unit refuses while “any `trks_llm` process”
  is alive and the M-1…M-7 answer says “`trks_llm`/lease gates”; the code has no literal `trks_llm` check
  and no `gpu0.lock` holder check. The `llama-server --port 1810[12]` gate is the substantive protection
  for a running Track S server (the `trks_llm` session runs it), and the GPU app list is recorded, so this
  is a wording/defence-in-depth gap: add `pgrep -f 'trks_llm'` / `tmux has-session -t trks_llm` and a
  read-only lock-holder record, or narrow the NOTE.
- **m-13 (stop unit, documentation).** The NOTE/stop header does not give the stop invocation. It must run
  on TASL-7 as `dowling` (all paths are `/home/dowling/…`; tmux is per-user), e.g.
  `ssh tasl7 'bash -s' < stop_trks_watch.sh`. The M-6 answer claims “invocation” was corrected; the TASL-2
  script has an invocation comment, the stop script/NOTE do not. Add one line.
- **m-14 (NOTE, documentation).** `runs/logs/watch.log` should be `r1_tracks/logs/watch.log` (the script
  comment correctly says `$R/logs/watch.log`; `postwatch_check.sh` uses
  `/home/dowling/r1_tracks/logs/watch.log`).
- **m-15 (stop receipt, evidence).** The receipt hashes `before.txt`, `after.txt`, `manifests.diff`,
  `stops.diff` but not `manifests_after.txt`, `stops_after.txt`, `locks_after.txt`, `kill.err`; a separate
  `SHA256SUMS`/`sha256sum -c` would bind the full artifact set. The four hash lines and the `-eq 4` count
  are correct.
- **m-16 (stop unit, hardening).** A STOP **after** the kill is terminal: the watcher is gone, so the
  identity gate can never pass on a re-run. The NOTE's “move it aside and re-run” recovery applies to
  pre-kill STOPs; say so, and state that a post-kill diff failure is preserved and escalated, not retried.
  A pre-kill baseline diff would also catch pre-existing drift before the irreversible step.
- **m-17 (TASL-2, scope/recording).** The census lists output directories (`ls -la out`, `find -maxdepth 2
  -type d`) but not `manifest.json`/`STOP` entries; ruling (4) names servers/lease/processes, so this is an
  optional scope addition, but round-1 M-5 asked for the manifest/STOP inventory. The success path also
  does not assert a non-empty `inventory.txt` or a `host=`/`id` header before `TASL2_INVENTORY_WRITTEN`
  (round-1 B-4 asked for the header check); add `grep -q '^host='` / `-s`.
- **m-18 (stop unit, hardening).** `after.txt` repeats only the watcher/tmux checks, not the B2-runner,
  collector, `llama` and GPU checks; M-2 asked to “repeat after the kill”. The before gates are the
  substantive check and the kill cannot start those processes, so this is defence in depth.
- **m-19 (M-7, documentation).** The B2 occupancy review's `≈21:10–21:35 CET` label (commit
  `5c3ff87a`, commit time 20:42:41 +0100) is still uncorrected; the new commit only notes the file. The
  label and the “~15/24 vs 19/24 roots” wording should be corrected in that file or in a separate note.
- **m-20 (follow-up, documentation).** The `d022bf64` analysis calls its 20-line quote the “full script (21
  lines)”; include the two omitted comment lines or mark them elided (see §6.5).

Checked and **not** defective: the identity regex escaping, the `pgrep` quoting/anchors, `set -u` variables
(all defined), the `grep -c '^[0-9a-f]\{64\}  '` receipt count (4, tested), the `set -C` exclusive
`TRKS_WATCH_STOPPED.ok`, the `bash -n` syntax, the `analysis_rc=0` format against
`postrun_collect.sh`/`retire_marker.sh`, and the `<(...)` process-substitution diffs.

### 6.7 Residual risk (B2 is live; the stop is pre-execution and irreversible)

- B2 is **still running** (runner pid 1050028; `b2.exit` and `postrun/` absent; marker present; 4/4
  manifests/STOPs; B2's `llama-server` 1077128 holds `gpu0.lock` on port 51283). The stop unit is correctly
  not runnable now. This review is pre-execution and must be re-checked if the run HEAD, the postrun units
  or the B2 handover receipts change before the stop; the watcher has not restarted (pid 1388760 since
  30 Oct; script SHA unchanged).
- The stop is **irreversible**: `tmux kill-session -t trks_watch` destroys the session; the script file
  stays. Run it only after `b2.exit` = 0, `POSTRUN_COLLECT_OK` with `analysis_rc=0`, and
  `marker-retirement.json` with the marker absent. The scene baseline must still match the post-watch
  inventory; the watcher's own one-line `marker gone` append to `watch.log` is expected and is not the
  unit's write. A STOP after the kill is terminal (m-16).
- The `trks_stop` directory is no-retry by design: after any STOP, move it aside (`mv`), never delete, and
  preserve the evidence and the scene.
- TASL-2 cannot be censused until its network returns. On return: run only the reviewed unit, confirm the
  `gpu0.lock` existence (m-10) before the probe, keep the census read-only, and send the inventory to
  review **before any other use** (ruling (4)). Nothing is resumed, no lease is released, no push is made.
- The branch tip advanced during the review (`d022bf64`, documentation-only). If the parent/author treats
  `d022bf64` as the tip, the unit bytes are still the reviewed ones and the NOTE at `d022bf64` is a
  superset; the follow-up analysis is accurate except for the two omitted comment lines (m-20).
- The occupancy review's future-dated label remains (m-19); it does not affect the STOP-4 unit bytes but
  should not be treated as a corrected record.

### 6.8 Final verdict (round 2)

**Accepted** — the stop unit, the TASL-2 census unit and the NOTE, with the non-blocking minors
m-10…m-20. The round-1 **BLOCKING** findings B-1 (identity regex/never-matching gate), B-2 (raw-vs-sorted
scene diff), B-3 (`ssh tasl2`) and B-4 (ssh rc fail-open) are fixed and were verified against the live host
line, the live script SHA, the live baseline files and the live `portal_zhixu` resolution. The round-1
**MAJOR** findings M-1 (script-SHA gate), M-3 (receipt/exclusive marker), M-4 (no-retry recovery),
M-2/M-5/M-6 (process gates, census scope, NOTE wording) are resolved in substance, with the residual
defence-in-depth/documentation minors above; M-7 is noted. m-10 is the one code-level write risk left and is
conditional on `gpu0.lock` being absent, which the expected scene does not indicate; confirm the file before
the TASL-2 run or add the one-line guard. The stop unit is accepted for execution after B2 normal
completion, postrun collect-ok and marker retirement, subject to §6.7.

*End of review (round 2).*
