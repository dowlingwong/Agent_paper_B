#!/usr/bin/env bash
export TRKS_PORT=18101
/home/dowling/r1_tracks/bin/trks collect --phase S0.4 --node digits_mlp --instances 10 --label ENGINEERING_ONLY --deadline 28800 --stop-file /home/dowling/r1_tracks/out/digits_mlp/s04_r2_20261111/STOP --out /home/dowling/r1_tracks/out/digits_mlp/s04_r2_20261111 --work /home/dowling/r1_tracks/scratch/digits_mlp/s04_r2_20261111 >> /home/dowling/r1_tracks/logs/trks_s04r2.log 2>&1
rc=$?; echo "$(date -u +%FT%TZ) rc=$rc" >> /home/dowling/r1_tracks/logs/trks_s04r2.exit
