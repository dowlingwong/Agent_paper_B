#!/bin/bash
set -u
echo "I3 v2 start $(date -u +%FT%TZ) host=$(hostname)"
id
nvidia-smi 2>/dev/null | head -5 || echo "no nvidia-smi"
/opt/r1/envs/trackp/bin/python -B "$(dirname "$0")/i3_v2.py"
rc=$?
echo "I3 v2 end $(date -u +%FT%TZ) rc=$rc"
exit $rc
