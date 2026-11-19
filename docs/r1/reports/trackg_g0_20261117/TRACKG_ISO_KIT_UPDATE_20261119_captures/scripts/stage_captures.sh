#!/bin/bash
# Stage a compact, hashable capture tree of the kit-update evidence under $E/captures/.
# Copies logs/records/JSON only (run trees and data stay in place); then writes captures/SHA256SUMS.
set -u
E=/home/dowling/r1_engineering/iso_kit_update_20261119
C=$E/captures
mkdir -p "$C"/{git,pins,pytest,data,paper_a,gpu,scripts,smoke/attempt1,smoke/attempt2} || exit 3

cp -f "$E"/git/*.txt "$E"/git/*.log "$E"/git/msg_*.txt "$C/git/" 2>/dev/null
cp -f "$E"/pins/*.json "$C/pins/" 2>/dev/null
cp -f "$E"/pytest/*.log "$E"/pytest/*.txt "$E"/pytest/*.json "$C/pytest/" 2>/dev/null
cp -f "$E"/data/*.log "$E"/data/*.txt "$C/data/" 2>/dev/null
cp -f "$E"/paper_a/*.json "$C/paper_a/" 2>/dev/null
cp -f "$E"/gpu/*.txt "$C/gpu/" 2>/dev/null
cp -f "$E"/scripts/*.sh "$E"/scripts/*.py "$C/scripts/" 2>/dev/null

# attempt 1 (PATH defect; partial outputs preserved in place, logs/records copied here)
cp -f "$E"/smoke/*.log "$C/smoke/attempt1/" 2>/dev/null
for d in "$E"/smoke/runs/*/; do
  [ -d "$d" ] || continue
  n=$(basename "$d")
  mkdir -p "$C/smoke/attempt1/$n"
  cp -f "$d"/gpu_*.txt "$C/smoke/attempt1/$n/" 2>/dev/null
  for r in "$d"/runs_smoke/*/ "$d"/runs_edits/*/; do
    [ -d "$r" ] || continue
    rid=$(basename "$r")
    mkdir -p "$C/smoke/attempt1/$n/$rid"
    cp -f "$r"/run_record.json "$r"/run.log "$r"/result_channel.txt "$C/smoke/attempt1/$n/$rid/" 2>/dev/null
  done
done

# attempt 2 (the recorded runs)
cp -f "$E"/smoke/attempt2/*.log "$E"/smoke/attempt2/*.json "$C/smoke/attempt2/" 2>/dev/null
for d in "$E"/smoke/attempt2/runs/*/; do
  [ -d "$d" ] || continue
  n=$(basename "$d")
  mkdir -p "$C/smoke/attempt2/$n"
  cp -f "$d"/gpu_*.txt "$C/smoke/attempt2/$n/" 2>/dev/null
  for r in "$d"/runs_smoke/*/ "$d"/runs_edits/*/; do
    [ -d "$r" ] || continue
    rid=$(basename "$r")
    mkdir -p "$C/smoke/attempt2/$n/$rid"
    cp -f "$r"/run_record.json "$r"/run.log "$r"/result_channel.txt "$C/smoke/attempt2/$n/$rid/" 2>/dev/null
  done
done

cd "$C" || exit 3
find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
echo "captured $(wc -l < SHA256SUMS) files, $(du -sh . | cut -f1)"
