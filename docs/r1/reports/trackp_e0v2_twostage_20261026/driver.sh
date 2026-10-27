#!/usr/bin/env bash
# E0 v2 two-stage driver (R1-E0-BUDGET, 26 Oct 2026 evening). AI-assisted (Claude).
# Per base: (1) lr screen on the grid, fresh LayerNorm + linear head, soft labels, <= 2,000 steps (config e0.screen);
# e0-select picks the lr by val RPS; (2) ONE final run at the selected lr (config e0.final: cap 6,000, eval every
# 100, patience 10) — the E0 metrics; then the hard-label contrast and the native readout at the selected lr with
# the final budget; E6 probes (A3 v2 budget) on the final model. Every trackp.py call is its own GPU job (Track X
# marker, STATUS, nvidia-smi, flock, environment pins). SHORT=1: the validation DRYRUN with capped steps.
# Usage: [SHORT=1] [OUT=dir] driver.sh <base> [<base> ...]
set -euo pipefail
cd /home/dowling/r1_trackp/Agent_paper_B
PY=/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python
OUT=${OUT:-/home/dowling/r1_trackp/runs/p5_e0v2_twostage}
EV=${EVIDENCE:-DRYRUN}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
if [ "${SHORT:-0}" = 1 ]; then SCREEN=(--steps 200); FINAL=(--steps 400); NPROBE=32; else SCREEN=(); FINAL=(); NPROBE=100; fi
for B in "$@"; do
  for LR in 1e-05 3e-05 0.0001; do
    D=$OUT/$B/screen_lr$LR
    [ -f "$D/report.json" ] || $PY r1/scripts/trackp.py e0 --base "$B" --evidence "$EV" --stage screen --variant fresh --lr "$LR" "${SCREEN[@]}" --run-dir "$D"
  done
  $PY r1/scripts/trackp.py e0-select --evidence "$EV" --run-dir "$OUT/$B/select" --runs "$OUT/$B"/screen_lr*
  SEL=$($PY -c "import json,sys;print(json.load(open(sys.argv[1]))['selected']['lr'])" "$OUT/$B/select/report.json")
  for R in final:--variant:fresh hard:--variant:fresh:--hard native:--variant:native; do
    NAME=${R%%:*}
    D=$OUT/$B/$NAME
    [ -f "$D/report.json" ] || $PY r1/scripts/trackp.py e0 --base "$B" --evidence "$EV" --stage final $(echo ${R#*:} | tr ':' ' ') --lr "$SEL" "${FINAL[@]}" --run-dir "$D"
  done
  [ -f "$OUT/$B/probes/report.json" ] || $PY r1/scripts/trackp.py probes --base "$B" --evidence "$EV" --head-form linear12 --budget --n-probe "$NPROBE" --load "$OUT/$B/final/saved" --run-dir "$OUT/$B/probes"
done
