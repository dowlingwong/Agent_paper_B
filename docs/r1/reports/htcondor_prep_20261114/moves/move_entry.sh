#!/bin/bash
# Move one /ceph/dwong entry to /work/dwong with copy-verify, _to_delete retirement and a symlink back.
# NO DELETION anywhere. Authority: runbook §1.4, errata A5/A7-F10, MOVE_PLAN.md revision 2 (incl. R1/R2).
# Usage: move_entry.sh <entry>
set -u
X="${1:?entry name required}"
W=/work/dwong/htcondor_prep_20261114
SRC="/ceph/dwong/$X"; DST="/work/dwong/$X"; RET="/ceph/dwong/_to_delete/${X}.moved_20261114"
LOG="$W/moves/MOVE_LOG.tsv"; TS=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p /ceph/dwong/_to_delete /work/dwong/_to_delete "$W/moves"
[ -f "$LOG" ] || printf 'entry\tbytes\tfiles\tpre_free_GiB\tfloor_GiB\tcopy_rc\tcount_equal\tbytes_equal\tmanifest_sha256\tgit_checks\tinuse_hosts\tmoved_to\tsymlink_ok\told_path_ok\tverdict\tnote\n' > "$LOG"
say(){ printf '%s %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
FAIL=""
inuse_local(){  # deepthought: processes (cwd + open fds), tmux/screen, condor Iwd
  local tag="$1"
  local out="$W/moves/inuse_${X}_${tag}_${TS}.txt"
  { echo "host=$(hostname -f) ts=$TS entry=$X"
    pgrep -u dwong -a 2>/dev/null | head -40
    for p in $(pgrep -u dwong); do c=$(readlink "/proc/$p/cwd" 2>/dev/null || true); case "$c" in "$SRC"|"$SRC"/*) echo "HIT cwd pid=$p cwd=$c";; esac; ls -l "/proc/$p/fd" 2>/dev/null | grep -F "$SRC" | sed "s/^/HIT fd pid=$p /" ; done
    tmux ls 2>/dev/null | sed 's/^/tmux: /'; screen -ls 2>/dev/null | sed 's/^/screen: /'
    condor_q dwong -af Iwd Cmd 2>/dev/null | sed 's/^/condor: /'
  } > "$out" 2>&1
  if grep -q 'HIT ' "$out"; then FAIL="in_use_local"; fi
  echo "$out"
}
# 1) in-use (deepthought + host transcript supplied by the lead)
inuse_local before >/dev/null
HOSTS="$W/moves/inuse_hosts.txt"
[ -f "$HOSTS" ] && { echo "-- other login hosts --" >> "$W/moves/inuse_${X}_before_${TS}.txt"; cat "$HOSTS" >> "$W/moves/inuse_${X}_before_${TS}.txt"; grep -q "HIT" "$HOSTS" && FAIL="in_use_host"; }
[ -d "$SRC" ] || { say "SKIP $X: source missing or not a directory"; exit 0; }
[ "$FAIL" = "in_use_local" ] || [ "$FAIL" = "in_use_host" ] && { say "SKIP $X in use ($FAIL)"; printf '%s\t\t\t\t\t\t\t\t\t\t%s\t\t\t\tskipped_in_use\t%s\n' "$X" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" "$FAIL" >> "$LOG"; exit 0; }
# 2) pre-copy disk gate
BYTES=$(du -sb "$SRC" | awk '{print $1}'); FILES=$(find "$SRC" -xdev -type f 2>/dev/null | wc -l)
WORK_SIZE=$(df -B1 --output=size /work | tail -1 | tr -d ' '); WORK_AVAIL=$(df -B1 --output=avail /work | tail -1 | tr -d ' ')
FLOOR_PY=$(python3 - "$WORK_SIZE" "$BYTES" <<'PY'
import sys
size=int(sys.argv[1]); b=int(sys.argv[2]); floor=max(int(0.15*size), b+5*1024**3); print(floor)
PY
)
FREE_AFTER=$((WORK_AVAIL - BYTES))
if [ "$FREE_AFTER" -lt "$FLOOR_PY" ]; then say "STOP PROGRAMME: $X would leave $((FREE_AFTER/1024**3)) GiB < floor $((FLOOR_PY/1024**3)) GiB"; printf '%s\t%s\t%s\t%s\t%s\t\t\t\t\t\t\t\t\t\tfloor_breach\tmove programme stopped\n' "$X" "$BYTES" "$FILES" "$((FREE_AFTER/1024**3))" "$((FLOOR_PY/1024**3))" >> "$LOG"; exit 2; fi
# 3) collision guards
if [ -e "$DST" ] || [ -e "$RET" ]; then say "SKIP $X: destination or retirement name exists"; printf '%s\t%s\t%s\t\t\t\t\t\t\t\t%s\t\t\t\tcollision\tno action\n' "$X" "$BYTES" "$FILES" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" >> "$LOG"; exit 0; fi
# 4) copy
nice -n 19 ionice -c3 rsync -aHAX --numeric-ids "$SRC/" "$DST/" > "$W/moves/rsync_${X}_${TS}.log" 2>&1; RC=$?
# 5) verify
C1=$(find "$SRC" -xdev -type f 2>/dev/null | wc -l); C2=$(find "$DST" -xdev -type f 2>/dev/null | wc -l)
B1=$(du -sb "$SRC" | awk '{print $1}'); B2=$(du -sb "$DST" | awk '{print $1}')
M1=$( (cd "$SRC" && find . -type f -print0 | sort -z | xargs -0 sha256sum 2>/dev/null) | sha256sum | awk '{print $1}')
M2=$( (cd "$DST" && find . -type f -print0 | sort -z | xargs -0 sha256sum 2>/dev/null) | sha256sum | awk '{print $1}')
GITOK=na
if [ -d "$SRC/.git" ] || git -C "$SRC" rev-parse --git-dir >/dev/null 2>&1; then
  h1=$(git -C "$SRC" rev-parse HEAD 2>/dev/null); h2=$(git -C "$DST" rev-parse HEAD 2>/dev/null)
  s1=$(git -C "$SRC" status --porcelain 2>/dev/null | wc -l); s2=$(git -C "$DST" status --porcelain 2>/dev/null | wc -l)
  [ "$h1" = "$h2" ] && [ "$s1" = "$s2" ] && GITOK="ok($h1/$s1)" || GITOK="MISMATCH($h1/$s1 vs $h2/$s2)"
fi
VERDICT=ok
[ "$RC" -ne 0 ] && VERDICT="copy_failed(rc=$RC)"
[ "$C1" != "$C2" ] && VERDICT="count_mismatch($C1/$C2)"
[ "$B1" != "$B2" ] && VERDICT="bytes_mismatch($B1/$B2)"
[ "$M1" != "$M2" ] && VERDICT="manifest_mismatch"
case "$GITOK" in MISMATCH*) VERDICT="git_mismatch";; esac
if [ "$VERDICT" != "ok" ]; then
  say "FAILED $X: $VERDICT — leaving both copies, retiring the /work partial copy (no deletion)"
  if [ -d "$DST" ]; then mv "$DST" "/work/dwong/_to_delete/${X}.failed_${TS}" 2>/dev/null || true; fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\tno\tno\tfailed\t%s\n' "$X" "$BYTES" "$FILES" "$((FREE_AFTER/1024**3))" "$((FLOOR_PY/1024**3))" "$RC" "$([ "$C1" = "$C2" ] && echo yes || echo no)" "$([ "$B1" = "$B2" ] && echo yes || echo no)" "$M1" "$GITOK" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" "$VERDICT" >> "$LOG"
  exit 1
fi
# 5b) repeat in-use immediately before the rename (R1)
inuse_local before_rename >/dev/null
if grep -q 'HIT ' "$W/moves/inuse_${X}_before_rename_${TS}.txt" 2>/dev/null; then
  say "SKIP $X: in use appeared after verify (no rename; /work copy kept)"
  printf '%s\t%s\t%s\t%s\t%s\t%s\tyes\tyes\t%s\t%s\t%s\t\tno\tyes\tskipped_in_use_after_verify\tno rename\n' "$X" "$BYTES" "$FILES" "$((FREE_AFTER/1024**3))" "$((FLOOR_PY/1024**3))" "$RC" "$M1" "$GITOK" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" >> "$LOG"
  exit 0
fi
# 6) retire original into _to_delete and leave the symlink
mv "$SRC" "$RET" || { say "FAILED $X: mv to _to_delete failed"; exit 1; }
ln -s "$DST" "$SRC" || { say "FAILED $X: symlink failed (original stays retired in _to_delete)"; exit 1; }
# 7) verify through the old path
OLDOK=no; [ -L "$SRC" ] && [ "$(readlink "$SRC")" = "$DST" ] && [ -d "$SRC" ] && OLDOK=yes
say "DONE $X -> $DST (retired $RET) old_path_ok=$OLDOK"
printf '%s\t%s\t%s\t%s\t%s\t%s\tyes\tyes\t%s\t%s\t%s\t%s\tyes\t%s\tmoved\t-\n' "$X" "$BYTES" "$FILES" "$((FREE_AFTER/1024**3))" "$((FLOOR_PY/1024**3))" "$RC" "$M1" "$GITOK" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" "$RET" "$OLDOK" >> "$LOG"
exit 0
