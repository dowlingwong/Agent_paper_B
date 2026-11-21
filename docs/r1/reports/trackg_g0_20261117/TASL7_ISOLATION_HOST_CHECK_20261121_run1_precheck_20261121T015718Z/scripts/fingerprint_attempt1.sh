#!/bin/bash
# R1-T1-HOST-TASL condition 7: read-only pre/post fingerprint of the Track P attempt-1 archive and lease log.
#
# The attempt-1 archive /home/dowling/r1_trackp/runs/p3a_operator_20261027 (and its EVIDENCE) and the attempt-1
# lease log must be untouched by this host check.  This script NEVER writes to, moves, renames or deletes
# anything under the archive: it only reads file metadata and file content and writes manifests into the
# host-check captures directory.  atime is deliberately excluded from the fingerprint (a read may update it on
# relatime); mtime/ctime/size/inode/mode/owner and the full content sha256 are recorded.
#
# usage: fingerprint_attempt1.sh <before|after>
set -uo pipefail
umask 077

BASE=/home/dowling/r1_engineering/tasl7_hostcheck_20261121
CAP="$BASE/captures"
ARCHIVE=/home/dowling/r1_trackp/runs/p3a_operator_20261027
LEASELOG=/home/dowling/r1_locks/trackp_evidence.log
GPULEASE=/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl

phase="${1:?usage: fingerprint_attempt1.sh <before|after>}"
out="$CAP/attempt1_${phase}"
mkdir -p "$CAP"

# stat of the archive root, its EVIDENCE, its journal, and both lease-log candidates
for p in "$ARCHIVE" "$ARCHIVE/EVIDENCE" "$ARCHIVE/journal.jsonl" "$LEASELOG" "$GPULEASE"; do
  stat -c "%n|%F|%s|%Y|%Z|%y|%z|%U|%G|%a|%i" "$p" 2>&1
done > "$out.stat.txt"

# metadata tree fingerprint: path|type|size|mtime_ns|ctime_ns|mode|uid|gid|nlink|inode, sorted; no atime
find "$ARCHIVE" -printf "%p|%y|%s|%T@|%C@|%m|%U|%G|%n|%i\n" 2>/dev/null \
  | LC_ALL=C sort > "$out.tree.txt"
sha256sum "$out.tree.txt" | cut -d' ' -f1 > "$out.tree.sha256"

# content fingerprint of every regular file (sorted by path) and its aggregate
find "$ARCHIVE" -type f -print0 2>/dev/null | LC_ALL=C sort -z \
  | xargs -0 -r sha256sum > "$out.content.txt"
sha256sum "$out.content.txt" | cut -d' ' -f1 > "$out.content.sha256"

find "$ARCHIVE" -mindepth 1 2>/dev/null | wc -l > "$out.nentries.txt"
find "$ARCHIVE" -type f 2>/dev/null | wc -l > "$out.nfiles.txt"
du -sb "$ARCHIVE" 2>/dev/null | cut -f1 > "$out.bytes.txt"
date -u +%FT%TZ > "$out.utc.txt"
echo "fingerprint phase=$phase entries=$(cat "$out.nentries.txt") files=$(cat "$out.nfiles.txt") tree_sha256=$(cat "$out.tree.sha256") content_sha256=$(cat "$out.content.sha256")"
