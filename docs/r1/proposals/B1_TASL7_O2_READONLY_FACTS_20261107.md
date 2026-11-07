# TASL-7 O2 handover: concrete read-only facts and command candidate

AI-assisted (Codex). **Candidate for independent review before host execution.** This is an observation procedure, not a marker action, reservation, handover or B1 launch. No host operation was performed in preparing it. It uses the author's permission to continue despite unrelated agents, and does not require new owner authentication, cgroups, freezer, supervisor or durability guarantees. It must not preempt anyone. The author permits the Track S watcher's ordinary pause, log append and STOP touches; preserve their prior contents and record actual effects.

## What existing evidence says

At **21:59:31 UTC on 7 November**, the independently reviewed prior census (`TASL7_CENSUS_RESULT_REVIEW_20261107.md`) saw `trks_watch` in tmux, no listed priority marker, GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` with no reported compute process and about 585 GiB free on the B1 work filesystem. `fuser` returned 1 with no output; it did not prove a free flock. The three checkout STATUS files were readable but their latest headings were historical. This is a snapshot, not current evidence of an inactive collector, absent P.3a or a safe point.

The previously read watcher file (`reports/tasl7_census_20261107/watcher.txt`, SHA-256 `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112`) tests Track X/P/drill markers, appends to `r1_tracks/logs/watch.log`, touches `STOP` beside every `manifest.json` it finds under `r1_tracks/out`, waits while same-user commands match its collector pattern, then attempts `tmux kill-session -t trks_llm`; after 3,600 seconds it attempts that even if collectors remain. It waits for markers to disappear and says resume by hand. The file digest and tmux pane do not prove the running shell's loaded contents. Check current files and processes, and do not claim a forced pause is safe.

## One read-only refresh

After this exact plan is independently reviewed, run the following once near the handover, retaining the private capture. It records path metadata and matching PIDs, not process command arguments, pane contents or environment. STATUS contents, path names and process metadata may be sensitive; inspect locally and publish only needed reviewed facts. All remote commands read only; no marker, STOP, lease, process, watcher or tracked file is changed intentionally. Missing commands, unreadable paths, unexpected watcher changes and failed observations are reported with their exit status, not treated as absence. No output can prevent a concurrent actor from starting later.

```bash
set -u
umask 077
HANDOVER_FACTS=$(mktemp -d /private/tmp/paper-b-tasl7-o2-facts-20261107.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$HANDOVER_FACTS/facts.txt" 2>&1 <<'REMOTE'
set -u
set -o pipefail
printf '%s\n' 'UTC / HOST / ID'
date -u; hostname; id
printf '%s\n' 'LOCK DIRECTORY AND PRIORITY MARKERS'
ls -la "$HOME/r1_locks"; printf 'locks_rc=%s\n' "$?"
for name in trackx_evidence.active trackp_evidence.active; do
  path="$HOME/r1_locks/$name"
  if test -e "$path" || test -L "$path"; then ls -ld "$path"; else printf 'ABSENT %s\n' "$path"; fi
done
printf '%s\n' 'TRACK X / P / S STATUS (private transcript)'
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  file="$repo/docs/r1/STATUS.md"; printf 'STATUS %s\n' "$file"
  if test -f "$file" && test -r "$file"; then sha256sum "$file"; cat "$file"; printf '\nstatus_rc=%s\n' "$?"; else printf '%s\n' 'STATUS_MISSING_OR_UNREADABLE'; fi
done
printf '%s\n' 'CURRENT WATCHER FILE AND TMUX METADATA'
watch="$HOME/r1_tracks/bin/trks-watch"
if test -f "$watch" && test -r "$watch"; then sha256sum "$watch"; sed -n '1,120p' "$watch"; printf 'watcher_rc=%s\n' "$?"; else printf '%s\n' 'WATCHER_FILE_MISSING_OR_UNREADABLE'; fi
tmux list-panes -a -F 'session=#{session_name} pane=#{pane_id} pid=#{pane_pid} command=#{pane_current_command}'; printf 'tmux_rc=%s\n' "$?"
printf '%s\n' 'COLLECTOR PIDS USING HISTORICAL WATCHER MATCH (no arguments)'
pgrep -u "$(id -u)" -f 'python -m r1\.tracks\.collect .*--stop-file'; printf 'collector_pgrep_rc=%s\n' "$?"
printf '%s\n' 'TRACK P / P3A CANDIDATE PIDS (no arguments)'
pgrep -u "$(id -u)" -f 'r1[._/-]trackp|r1_trackp|[pP][._-]?3a'; printf 'trackp_pgrep_rc=%s\n' "$?"
printf '%s\n' 'PROCESS METADATA (no arguments)'
ps -eo user,pid,ppid,etime,comm; printf 'ps_rc=%s\n' "$?"
printf '%s\n' 'WATCHER-REACHABLE MANIFEST AND STOP METADATA'
if test -d "$HOME/r1_tracks/out" && test ! -L "$HOME/r1_tracks/out"; then
  find "$HOME/r1_tracks/out" -name manifest.json -print0 | while IFS= read -r -d '' manifest; do
    printf 'MANIFEST %s\n' "$manifest"
    ls -ld "$manifest"; printf 'manifest_ls_rc=%s\n' "$?"
    stop="${manifest%/*}/STOP"
    if test -e "$stop" || test -L "$stop"; then
      ls -ld "$stop"; printf 'stop_ls_rc=%s\n' "$?"
      if test -L "$stop"; then printf 'STOP_LINK_TARGET '; readlink "$stop"; printf 'readlink_rc=%s\n' "$?"; fi
    else printf 'STOP_ABSENT %s\n' "$stop"; fi
  done
  printf 'find_inventory_rc=%s\n' "$?"
else printf '%s\n' 'OUTPUT_ROOT_MISSING_UNREADABLE_OR_SYMLINK'; fi
printf '%s\n' 'GPU AND WORK FILESYSTEM'
nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv; printf 'gpu_rc=%s\n' "$?"
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv; printf 'compute_rc=%s\n' "$?"
df -Pk "$HOME/exam-x/work"; printf 'df_rc=%s\n' "$?"
REMOTE
ssh_rc=$?
printf 'ssh_exit=%s\n' "$ssh_rc" > "$HANDOVER_FACTS/ssh-status.txt"
shasum -a 256 "$HANDOVER_FACTS/facts.txt" "$HANDOVER_FACTS/ssh-status.txt"
printf 'Private capture: %s; SSH exit: %s\n' "$HANDOVER_FACTS" "$ssh_rc"
```

`pgrep` exit 1 means no match for that pattern at that instant; a different error is NOT CHECKABLE. Track P may use a command that matches neither spelling, a different user, or a wrapper; no matching PID is not by itself proof P.3a is absent. Use the current Track P STATUS, known P.3a session/work evidence and GPU/lease state to distinguish absent, safely paused, active or uncertain. If a potentially active P.3a job cannot be identified as paused at a documented safe point, wait rather than killing it. Same for a collector that may still run when the watcher reaches its one-hour forced-server-stop behavior. No new authentication condition is introduced: the author already allowed the watcher pause; use actual existing handover information and safe process state.

Before creating the marker under the accepted O2 procedure, compare the current watcher behavior to the historical script, and assess each reachable STOP: ordinary existing regular STOP touches and watcher log append are within the directed routine handover; do not truncate or delete their contents. A symlink, special-file target, unreachable manifest directory, changed watcher behavior or unclear effect needs a concrete safe resolution before acting, not a guess. Recheck occupancy just before the marker, hold B1's cooperative GPU lease through the actual run, and record expected and actual watcher effects. Publish B1 running STATUS to the author-approved feature branch as specified in the updated O2 plan; do not push main. A failed publication or unexpected effect after marker creation is STOP and preserve the scene. Retiring only this run's marker and restoring Track S/P at normal completion still follows the separately reviewed no-deletion O2 procedure. This refresh does not satisfy the author gate or final B1 preflight.
