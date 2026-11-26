#!/usr/bin/env bash
/home/dowling/r1_tracks/bin/trks collect --phase S0.5b --node digits_mlp --truncate-W 8\,10\,12\,20 --out /home/dowling/r1_tracks/out/digits_mlp/s05_t7_20261113 --work /home/dowling/r1_tracks/scratch/digits_mlp/s05_t7_20261113 >> /home/dowling/r1_tracks/logs/trks_s05b_t7.log 2>&1
rc=$?; echo "$(date -u +%FT%TZ) rc=$rc" >> /home/dowling/r1_tracks/logs/trks_s05b_t7.exit
