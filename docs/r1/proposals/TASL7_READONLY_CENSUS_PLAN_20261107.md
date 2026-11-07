# TASL-7 read-only census plan — 7 November 2026

AI-assisted (Codex). **Candidate; independent review required before use.** No host action has been performed by this plan. It refreshes the non-atomic observations in `TASL7_READONLY_REFRESH_20261107_0937.md`, `TASL7_READONLY_CENSUS_20261107.md` and `TASL7_WATCHER_READONLY_20261107.md` under the author's current host-access and no-preemption instructions. It does not launch, reserve a host/GPU, acquire a lock, touch a marker, signal a process, modify a checkout, or authorize B1. Mere unrelated agent presence is not by itself a STOP. Separate reviewed launch and handover gates remain.

Run once after independent review. The following uses a newly created private Mac directory and preserves its transcript even on SSH or command failure. It intentionally does not print process argument vectors, environment variables, secrets, tmux pane contents or the raw transcript into chat. Full STATUS text can itself contain sensitive information; keep the transcript private, inspect it locally, and publish only the necessary reviewed, redacted facts. No remote scratch files are created. For any unavailable command or unreadable STATUS, record `NOT CHECKABLE` with its exit status; do not infer absence or retry an ambiguous connection automatically. Shell-read side effects such as filesystem access times and changes by concurrent operators are not controlled.

```bash
set -u
umask 077
CENSUS_DIR=$(mktemp -d /private/tmp/paper-b-tasl7-census-20261107.XXXXXXXX) || exit 1
printf 'Private census directory: %s\n' "$CENSUS_DIR"
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$CENSUS_DIR/census.txt" 2>&1 <<'REMOTE'
set -u
printf '%s\n' 'UTC / HOST / ID'
date -u; printf 'date_rc=%s\n' "$?"
hostname; printf 'hostname_rc=%s\n' "$?"
id; printf 'id_rc=%s\n' "$?"
printf '%s\n' 'LOCK DIRECTORY'
ls -la "$HOME/r1_locks"; printf 'locks_rc=%s\n' "$?"
printf '%s\n' 'COMPLETE TRACK STATUS FILES'
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  printf 'CHECKOUT %s\n' "$repo"
  file="$repo/docs/r1/STATUS.md"
  if test -f "$file" && test -r "$file"; then
    sha256sum "$file"; printf 'status_sha_rc=%s\n' "$?"
    cat "$file"; printf '\nstatus_read_rc=%s\n' "$?"
  else
    printf '%s\n' 'STATUS_MISSING_OR_UNREADABLE'
  fi
done
printf '%s\n' 'GPU INVENTORY'
nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv; printf 'gpu_inventory_rc=%s\n' "$?"
printf '%s\n' 'GPU COMPUTE APPLICATIONS'
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv; printf 'gpu_compute_rc=%s\n' "$?"
printf '%s\n' 'OWNED TMUX PANES'
tmux list-panes -a -F 'session=#{session_name} pane=#{pane_id} pid=#{pane_pid} command=#{pane_current_command}'; printf 'tmux_panes_rc=%s\n' "$?"
printf '%s\n' 'PROCESS METADATA (NO ARGUMENTS)'
ps -eo user,pid,ppid,etime,comm; printf 'ps_rc=%s\n' "$?"
printf '%s\n' 'GPU LOCK USERS (not a lock acquisition)'
fuser "$HOME/r1_locks/gpu0.lock"; printf 'fuser_rc=%s\n' "$?"
printf '%s\n' 'FILESYSTEM CAPACITY'
df -Pk "$HOME/exam-x/work"; printf 'df_rc=%s\n' "$?"
printf '%s\n' 'WATCHER FILE HASH (not loaded-code proof)'
sha256sum "$HOME/r1_tracks/bin/trks-watch"; printf 'watcher_hash_rc=%s\n' "$?"
REMOTE
ssh_rc=$?
printf 'ssh_exit=%s\n' "$ssh_rc" > "$CENSUS_DIR/ssh-status.txt"
shasum -a 256 "$CENSUS_DIR/census.txt" "$CENSUS_DIR/ssh-status.txt"
printf 'SSH exit: %s; inspect the private transcript and command exit markers.\n' "$ssh_rc"
```

A zero SSH exit means the shell finished, not that every observation succeeded; use the printed per-command statuses and the complete transcript. In particular `fuser` reporting no PID or a nonzero exit does not prove the flock is obtainable. GPU process listings, `ps`/tmux, lock names, STATUS and space are snapshots, not a reservation or assurance that no other job can start. No process arguments are collected, so an ambiguous Python process or shell pane cannot be positively assigned to Track S/P or a safe point from this census. The watcher file hash does not identify the code loaded in a running shell. Before any marker or execution, the operator must separately establish the watcher effects, ownership, no-preemption handover, actual cooperative lease and B1's reviewed preflight under the accepted O2 procedure. If STATUS is absent/unreadable or an essential check fails, the operator reports the gap and performs any later action only under its own applicable gate; this census provides no waiver.
