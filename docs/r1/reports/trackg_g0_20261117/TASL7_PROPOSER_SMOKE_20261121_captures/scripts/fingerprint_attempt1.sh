#!/bin/bash
# Read-only pre/post fingerprint of the Track P attempt-1 archive and lease logs
# (never writes to the archive). Method mirrors the accepted host-check fingerprint.
set -uo pipefail
umask 077
ROOT=/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121
CAP="$ROOT/captures"
ARCHIVE=/home/dowling/r1_trackp/runs/p3a_operator_20261027
LEASELOG=/home/dowling/r1_locks/trackp_evidence.log
GPULEASE=/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl
GPU0LOCK=/home/dowling/r1_locks/gpu0.lock
phase="${1:?usage: fingerprint_attempt1.sh <before|after>}"
mkdir -p "$CAP"
out="$CAP/attempt1_${phase}"
for p in "$ARCHIVE" "$ARCHIVE/EVIDENCE" "$ARCHIVE/journal.jsonl" "$LEASELOG" "$GPULEASE" "$GPU0LOCK"; do
  stat -c "%n|%F|%s|%Y|%Z|%y|%z|%U|%G|%a|%i" "$p" 2>&1
done > "$out.stat.txt"
find "$ARCHIVE" -printf "%p|%y|%s|%T@|%C@|%m|%U|%G|%n|%i\n" 2>/dev/null | LC_ALL=C sort > "$out.tree.txt"
sha256sum "$out.tree.txt" | cut -d' ' -f1 > "$out.tree.sha256"
find "$ARCHIVE" -type f -print0 2>/dev/null | LC_ALL=C sort -z | xargs -0 -r sha256sum > "$out.content.txt"
sha256sum "$out.content.txt" | cut -d' ' -f1 > "$out.content.sha256"
find "$ARCHIVE" -mindepth 1 2>/dev/null | wc -l > "$out.nentries.txt"
find "$ARCHIVE" -type f 2>/dev/null | wc -l > "$out.nfiles.txt"
du -sb "$ARCHIVE" 2>/dev/null | cut -f1 > "$out.bytes.txt"
sha256sum "$LEASELOG" "$GPULEASE" > "$out.leaselogs.sha256" 2>&1
date -u +%FT%TZ > "$out.utc.txt"
echo "fingerprint phase=$phase entries=$(cat "$out.nentries.txt") files=$(cat "$out.nfiles.txt") tree_sha256=$(cat "$out.tree.sha256") content_sha256=$(cat "$out.content.sha256")"
