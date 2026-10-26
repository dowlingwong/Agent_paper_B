#!/usr/bin/env bash
# E0 protocol v2 DRYRUN on kev-0.8b and qwen3.5-0.8b-base (R1-E0-PROTOCOL, 26 Oct 2026). AI-assisted (Claude).
# Each trackp.py call is its own GPU job: it reads the Track X marker, STATUS, nvidia-smi and takes the flock.
# Per base: fresh linear12 head, soft labels, lr grid {1e-5, 3e-5, 1e-4}; e0-select picks the lr by val RPS;
# then the hard-label contrast and the native readout at the selected lr; E6 probes (A3 v2 budget) on the
# selected soft model. Usage: driver.sh <base> [<base> ...]
set -euo pipefail
cd /home/dowling/r1_trackp/Agent_paper_B
PY=/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python
OUT=/home/dowling/r1_trackp/runs/p5_e0v2_dryrun
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
for B in "$@"; do
  for LR in 1e-05 3e-05 0.0001; do
    D=$OUT/$B/fresh_soft_lr$LR
    [ -f "$D/report.json" ] || $PY r1/scripts/trackp.py e0 --base "$B" --evidence DRYRUN --variant fresh --lr "$LR" --run-dir "$D"
  done
  $PY r1/scripts/trackp.py e0-select --evidence DRYRUN --run-dir "$OUT/$B/select_fresh_soft" \
      --runs "$OUT/$B"/fresh_soft_lr*
  SEL=$($PY -c "import json,sys;print(json.load(open(sys.argv[1]))['selected']['lr'])" "$OUT/$B/select_fresh_soft/report.json")
  SELDIR=$OUT/$B/fresh_soft_lr$SEL
  [ -f "$OUT/$B/fresh_hard/report.json" ] || $PY r1/scripts/trackp.py e0 --base "$B" --evidence DRYRUN --variant fresh --hard --lr "$SEL" --run-dir "$OUT/$B/fresh_hard"
  [ -f "$OUT/$B/native_soft/report.json" ] || $PY r1/scripts/trackp.py e0 --base "$B" --evidence DRYRUN --variant native --lr "$SEL" --run-dir "$OUT/$B/native_soft"
  [ -f "$OUT/$B/probes/report.json" ] || $PY r1/scripts/trackp.py probes --base "$B" --evidence DRYRUN --head-form linear12 --budget --n-probe 100 --load "$SELDIR/saved" --run-dir "$OUT/$B/probes"
done
