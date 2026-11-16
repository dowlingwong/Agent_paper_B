#!/usr/bin/env bash
export TRKS_PORT=18101
/home/dowling/r1_tracks/bin/trks collect --phase S0.5 --node digits_mlp --prior /home/dowling/r1_tracks/out/digits_mlp/a2u_prior_r2_20261111.json --prior-sha256 5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607 --obs-inflation 1.0 --W 40 --instances 20 --policy static:0.00198\,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 --label ENGINEERING_ONLY --deadline 28800 --stop-file /home/dowling/r1_tracks/out/digits_mlp/s05_t7_20261113/STOP --out /home/dowling/r1_tracks/out/digits_mlp/s05_t7_20261113 --work /home/dowling/r1_tracks/scratch/digits_mlp/s05_t7_20261113 >> /home/dowling/r1_tracks/logs/trks_s05_t7.log 2>&1
rc=$?; echo "$(date -u +%FT%TZ) rc=$rc" >> /home/dowling/r1_tracks/logs/trks_s05_t7.exit
