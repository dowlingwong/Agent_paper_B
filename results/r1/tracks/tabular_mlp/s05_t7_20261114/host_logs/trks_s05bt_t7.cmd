#!/usr/bin/env bash
/home/dowling/r1_tracks/bin/trks collect --phase S0.5b --node tabular_mlp --truncate-W 8\,10\,12\,20 --out /home/dowling/r1_tracks/out/tabular_mlp/s05_t7_20261114 --work /home/dowling/r1_tracks/scratch/tabular_mlp/s05_t7_20261114 >> /home/dowling/r1_tracks/logs/trks_s05bt_t7.log 2>&1
rc=$?; echo "$(date -u +%FT%TZ) rc=$rc" >> /home/dowling/r1_tracks/logs/trks_s05bt_t7.exit
