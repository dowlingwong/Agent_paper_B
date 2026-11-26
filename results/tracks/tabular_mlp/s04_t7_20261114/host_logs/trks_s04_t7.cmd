#!/usr/bin/env bash
export TRKS_PORT=18101
/home/dowling/r1_tracks/bin/trks collect --phase S0.4 --node tabular_mlp --instances 10 --label ENGINEERING_ONLY --deadline 28800 --stop-file /home/dowling/r1_tracks/out/tabular_mlp/s04_t7_20261114/STOP --out /home/dowling/r1_tracks/out/tabular_mlp/s04_t7_20261114 --work /home/dowling/r1_tracks/scratch/tabular_mlp/s04_t7_20261114 >> /home/dowling/r1_tracks/logs/trks_s04_t7.log 2>&1
rc=$?; echo "$(date -u +%FT%TZ) rc=$rc" >> /home/dowling/r1_tracks/logs/trks_s04_t7.exit
