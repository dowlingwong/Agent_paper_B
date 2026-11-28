#!/bin/bash
B=/home/dowling/r1_tracks/work/d3p7c_20261128
while true; do
  ts=$(date -u +%FT%TZ)
  m=$(LC_ALL=C free -b | awk "/^Mem:/{print \$2\",\"\$3\",\"\$4\",\"\$6\",\"\$7}")
  echo "$ts,$m" >> "$B/host_mem_samples_c.csv"
  sleep 2
done
