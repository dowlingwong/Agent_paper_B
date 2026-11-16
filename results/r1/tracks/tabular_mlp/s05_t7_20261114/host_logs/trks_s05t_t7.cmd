#!/usr/bin/env bash
export TRKS_PORT=18101
/home/dowling/r1_tracks/bin/trks collect --phase S0.5 --node tabular_mlp --prior /home/dowling/r1_tracks/out/tabular_mlp/s04_t7_20261114/a2u_prior.json --prior-sha256 ba8f7783d8a57e8650c6f5d6c8db38192e19cf1aeedd43c052687e16ba15732f --obs-inflation 1.0 --W 40 --instances 20 --policy static:0.00057\,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 --label ENGINEERING_ONLY --deadline 28800 --stop-file /home/dowling/r1_tracks/out/tabular_mlp/s05_t7_20261114/STOP --out /home/dowling/r1_tracks/out/tabular_mlp/s05_t7_20261114 --work /home/dowling/r1_tracks/scratch/tabular_mlp/s05_t7_20261114 >> /home/dowling/r1_tracks/logs/trks_s05t_t7.log 2>&1
rc=$?; echo "$(date -u +%FT%TZ) rc=$rc" >> /home/dowling/r1_tracks/logs/trks_s05t_t7.exit
