#!/bin/bash
# Move one /ceph/dwong entry to /work/dwong: copy -> verify -> re-check in-use -> retire into _to_delete -> symlink.
# NO DELETION anywhere. Authority: runbook §1.4, errata A5/A7-F10, MOVE_PLAN.md revision 2 (R1/R2), and the
# author's 14 Nov instruction (file-content byte metric; +directory count, +symlink-list SHA, +permission-list SHA).
# v2.2: the volatile git index cache (*/.git/index) is excluded from the content manifest; repo identity is
#       checked by HEAD + porcelain status. This prevents the verification itself (git status refreshes the index)
#       from producing a false content mismatch.
# Usage: [RESUME=1] [INUSE_FILE=path] move_entry.sh <entry>
set -u
X="${1:?entry name required}"
W=/work/dwong/htcondor_prep_20261114
SRC="/ceph/dwong/$X"; DST="/work/dwong/$X"; RET="/ceph/dwong/_to_delete/${X}.moved_20261114"
LOG="$W/moves/MOVE_LOG.tsv"; TS=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p /ceph/dwong/_to_delete /work/dwong/_to_delete "$W/moves"
if [ ! -f "$LOG" ] || ! head -1 "$LOG" | grep -q 'symlink_sha_equal'; then
  if [ -f "$LOG" ]; then mv "$LOG" "$LOG.v1.${TS}"; fi
  printf 'entry\tbytes\tfiles\tdirs\tpre_free_GiB\tfloor_GiB\tcopy_rc\tcount_equal\tbytes_equal\tdirs_equal\tsymlink_sha_equal\tperm_sha_equal\tmanifest_sha256\tgit_checks\tinuse_hosts\tmoved_to\tsymlink_ok\told_path_ok\tverdict\tnote\n' > "$LOG"
fi
say(){ printf '%s %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
FAIL=""
file_bytes(){ find "$1" -type f -printf '%s\n' 2>/dev/null | awk '{s+=$1} END{print s+0}'; }
dir_count(){ find "$1" -type d 2>/dev/null | wc -l; }
sha_symlinks(){ ( cd "$1" && find . -type l -printf '%p -> %l\n' 2>/dev/null | LC_ALL=C sort ) | sha256sum | awk '{print $1}'; }
sha_perms(){ ( cd "$1" && find . -printf '%m %p\n' 2>/dev/null | LC_ALL=C sort ) | sha256sum | awk '{print $1}'; }
sha_manifest(){ ( cd "$1" && find . -type f ! -path '*/.git/index' -print0 | sort -z | xargs -0 sha256sum 2>/dev/null ) | sha256sum | awk '{print $1}'; }
inuse_local(){
  local tag="$1"
  local out="$W/moves/inuse_${X}_${tag}_${TS}.txt"
  { echo "host=$(hostname -f) ts=$TS entry=$X"
    pgrep -u dwong -a 2>/dev/null | head -40
    for p in $(pgrep -u dwong); do c=$(readlink "/proc/$p/cwd" 2>/dev/null || true); case "$c" in "$SRC"|"$SRC"/*) echo "HIT cwd pid=$p cwd=$c";; esac; ls -l "/proc/$p/fd" 2>/dev/null | grep -F "$SRC" | sed "s/^/HIT fd pid=$p /" ; done
    tmux ls 2>/dev/null | sed 's/^/tmux: /'; screen -ls 2>/dev/null | sed 's/^/screen: /'
    condor_q dwong -af Iwd Cmd 2>/dev/null | sed 's/^/condor: /'
  } > "$out" 2>&1
  if grep -q 'HIT ' "$out"; then FAIL="in_use_local"; fi
}
inuse_local before
HOSTS="${INUSE_FILE:-$W/moves/inuse_hosts.txt}"
if [ -f "$HOSTS" ]; then cat "$HOSTS" >> "$W/moves/inuse_${X}_before_${TS}.txt"; grep -q '^HIT ' "$HOSTS" && FAIL="in_use_host"; else HOSTS=/dev/null; echo "no host transcript provided" >> "$W/moves/inuse_${X}_before_${TS}.txt"; fi
[ -d "$SRC" ] || { say "SKIP $X: source missing or not a directory"; exit 0; }
case "$FAIL" in in_use_*) say "SKIP $X in use ($FAIL)"; exit 0;; esac
BYTES=$(file_bytes "$SRC"); FILES=$(find "$SRC" -xdev -type f 2>/dev/null | wc -l); DIRS=$(dir_count "$SRC")
WORK_SIZE=$(df -B1 --output=size /work | tail -1 | tr -d ' '); WORK_AVAIL=$(df -B1 --output=avail /work | tail -1 | tr -d ' ')
FLOOR=$(python3 - "$WORK_SIZE" "$BYTES" <<'PY'
import sys
size=int(sys.argv[1]); b=int(sys.argv[2]); print(max(int(0.15*size), b+5*1024**3))
PY
)
FREE_AFTER=$((WORK_AVAIL - BYTES))
if [ "$FREE_AFTER" -lt "$FLOOR" ]; then say "STOP PROGRAMME: $X would leave $((FREE_AFTER/1024**3)) GiB < floor $((FLOOR/1024**3)) GiB"; exit 2; fi
if [ -e "$RET" ] || { [ "${RESUME:-0}" != "1" ] && [ -e "$DST" ]; }; then say "SKIP $X: destination or retirement name exists"; exit 0; fi
RC=0
if [ "${RESUME:-0}" = "1" ] && [ -d "$DST" ]; then say "RESUME: reusing existing /work copy for $X; skipping rsync"
else nice -n 19 ionice -c2 -n7 rsync -aHAX --numeric-ids "$SRC/" "$DST/" > "$W/moves/rsync_${X}_${TS}.log" 2>&1; RC=$?; fi
C1=$(find "$SRC" -xdev -type f 2>/dev/null | wc -l); C2=$(find "$DST" -xdev -type f 2>/dev/null | wc -l)
B1=$(file_bytes "$SRC"); B2=$(file_bytes "$DST")
D1=$(dir_count "$SRC"); D2=$(dir_count "$DST")
L1=$(sha_symlinks "$SRC"); L2=$(sha_symlinks "$DST")
P1=$(sha_perms "$SRC"); P2=$(sha_perms "$DST")
M1=$(sha_manifest "$SRC"); M2=$(sha_manifest "$DST")
GITOK="na(no .git within depth 3)"
GRELR="$(cd "$SRC" && find . -maxdepth 3 -name .git -print -quit 2>/dev/null)"
if [ -n "$GRELR" ]; then
  R1D=$(dirname "$GRELR"); R2D="$DST/${R1D#./}"
  h1=$(git -C "$SRC/$R1D" rev-parse HEAD 2>/dev/null); h2=$(git -C "$R2D" rev-parse HEAD 2>/dev/null)
  s1=$(git -C "$SRC/$R1D" status --porcelain 2>/dev/null | wc -l); s2=$(git -C "$R2D" status --porcelain 2>/dev/null | wc -l)
  [ "$h1" = "$h2" ] && [ "$s1" = "$s2" ] && GITOK="ok($R1D:$h1/$s1)" || GITOK="MISMATCH($R1D:$h1/$s1 vs $h2/$s2)"
fi
VERDICT=ok
[ "$RC" -ne 0 ] && VERDICT="copy_failed(rc=$RC)"
[ "$C1" != "$C2" ] && VERDICT="count_mismatch($C1/$C2)"
[ "$B1" != "$B2" ] && VERDICT="bytes_mismatch($B1/$B2)"
[ "$D1" != "$D2" ] && VERDICT="dir_mismatch($D1/$D2)"
[ "$L1" != "$L2" ] && VERDICT="symlink_mismatch"
[ "$P1" != "$P2" ] && VERDICT="perm_mismatch"
[ "$M1" != "$M2" ] && VERDICT="manifest_mismatch"
case "$GITOK" in MISMATCH*) VERDICT="git_mismatch";; esac
eq(){ [ "$1" = "$2" ] && echo yes || echo no; }
if [ "$VERDICT" != "ok" ]; then
  say "FAILED $X: $VERDICT — leaving both copies, retiring the /work partial copy (no deletion)"
  if [ -d "$DST" ]; then
    FAILED_RET="/work/dwong/_to_delete/${X}.failed_${TS}"; [ -e "$FAILED_RET" ] && FAILED_RET="${FAILED_RET}_1"
    if mv "$DST" "$FAILED_RET" 2>/dev/null; then say "retired /work copy to $FAILED_RET"; else say "WARNING: could not retire /work copy to $FAILED_RET"; fi
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\tno\tno\tfailed\t%s\n' "$X" "$BYTES" "$FILES" "$DIRS" "$((FREE_AFTER/1024**3))" "$((FLOOR/1024**3))" "$RC" "$(eq "$C1" "$C2")" "$(eq "$B1" "$B2")" "$(eq "$D1" "$D2")" "$(eq "$L1" "$L2")" "$(eq "$P1" "$P2")" "$M1" "$GITOK" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" "$VERDICT" >> "$LOG"
  exit 1
fi
inuse_local before_rename
if grep -q 'HIT ' "$W/moves/inuse_${X}_before_rename_${TS}.txt" 2>/dev/null; then
  INUSE_RET="/work/dwong/_to_delete/${X}.inuse_${TS}"; [ -e "$INUSE_RET" ] && INUSE_RET="${INUSE_RET}_1"
  if [ -d "$DST" ] && [ ! -e "$INUSE_RET" ]; then mv "$DST" "$INUSE_RET" && NOTE="retired /work copy to $INUSE_RET" || NOTE="could not retire /work copy"; else NOTE="no /work copy to retire"; fi
  say "SKIP $X: in use appeared after verify (no rename); $NOTE"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\tyes\tyes\tyes\tyes\tyes\t%s\t%s\t%s\t\tno\tyes\tskipped_in_use_after_verify\t%s\n' "$X" "$BYTES" "$FILES" "$DIRS" "$((FREE_AFTER/1024**3))" "$((FLOOR/1024**3))" "$RC" "$M1" "$GITOK" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" "$NOTE" >> "$LOG"
  exit 0
fi
mv "$SRC" "$RET" || { say "FAILED $X: mv to _to_delete failed"; exit 1; }
ln -s "$DST" "$SRC" || { say "FAILED $X: symlink failed (original is retired in _to_delete)"; exit 1; }
OLDOK=no; [ -L "$SRC" ] && [ "$(readlink "$SRC")" = "$DST" ] && [ -d "$SRC" ] && OLDOK=yes
say "DONE $X -> $DST (retired $RET) old_path_ok=$OLDOK"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\tyes\tyes\tyes\tyes\tyes\t%s\t%s\t%s\t%s\tyes\t%s\tmoved\t-\n' "$X" "$BYTES" "$FILES" "$DIRS" "$((FREE_AFTER/1024**3))" "$((FLOOR/1024**3))" "$RC" "$M1" "$GITOK" "$(tr '\n' ';' < "$HOSTS" 2>/dev/null)" "$RET" "$OLDOK" >> "$LOG"
exit 0
