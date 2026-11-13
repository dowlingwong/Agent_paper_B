#!/bin/bash
# read-only inventory of /ceph/dwong top level; append as each entry finishes so partial results are usable
OUT=/work/dwong/htcondor_prep_20261114/inventory
: > "$OUT/inventory.tsv"
printf 'entry\tbytes\tfiles\tstarted_utc\tfinished_utc\n' >> "$OUT/inventory.tsv"
for e in /ceph/dwong/* /ceph/dwong/.[!.]*; do
  [ -e "$e" ] || continue
  n=$(basename "$e"); s=$(date -u +%H:%M:%S)
  size=$(nice -n 19 ionice -c3 du -sb "$e" 2>/dev/null | awk '{print $1}')
  files=$(nice -n 19 ionice -c3 find "$e" -xdev -type f 2>/dev/null | wc -l)
  printf '%s\t%s\t%s\t%s\t%s\n' "$n" "${size:-0}" "${files:-0}" "$s" "$(date -u +%H:%M:%S)" >> "$OUT/inventory.tsv"
done
echo DONE >> "$OUT/inventory.tsv"
