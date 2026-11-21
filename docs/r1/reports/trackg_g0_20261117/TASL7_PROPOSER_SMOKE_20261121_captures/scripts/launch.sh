#!/bin/bash
# Launch the server ONCE inside a live delegated per-command cgroup scope.
# MemoryMax is 48G (not the 8G worker cap): the proposer server must hold a
# 19.6 GB GGUF's page cache plus CUDA host memory on a 62 GB host.
# timeout(1) is a 3600 s watchdog so the server can never be left running.
set -uo pipefail
ROOT=/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121
export XDG_RUNTIME_DIR=/run/user/1011
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1011/bus
cd "$ROOT"
exec systemd-run --user --scope --unit=tasl7-proposer-smoke-20261121 --collect \
  -p Delegate=yes -p MemoryMax=48G -p MemorySwapMax=0 \
  -E XDG_RUNTIME_DIR=/run/user/1011 \
  -E DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1011/bus \
  -E PYTHONDONTWRITEBYTECODE=1 \
  -- timeout --signal=TERM --kill-after=30 3600 \
     bash /home/dowling/r1_engineering/tasl7_proposer_smoke_20261121/scripts/serve.sh
