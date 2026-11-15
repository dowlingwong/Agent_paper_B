#!/bin/bash
# B2 post-run collection (host, staged checkout): verify exit 0, collect batch_state/b2_manifests,
# run the verified B2 analysis (grid verifier), and aggregate invalid-trial counts per
# candidate/mode/check from the proposal journals. Read-only on the batch; writes only RUN_DIR/postrun.
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RULE_SHA=53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad
RUN_ID=8709_20261115_b2
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
PY=/home/dowling/exam-x/work/venv/bin/python
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
BATCH="/home/dowling/exam-x/work/b2_${RUN_ID}"
PO="$RUN_DIR/postrun"
stop() { echo "STOP: $*" >&2; exit 2; }
[ -d "$PO" ] && [ ! -L "$PO" ] || stop "missing postrun dir"
[ ! -e "$PO/analysis.json" ] || stop "postrun already collected (no retry)"
[ "$(cat "$RUN_DIR/b2.exit" 2>/dev/null)" = 0 ] || stop "b2.exit is not 0 (STOP; do not retire)"
[ -s "$BATCH/batch_state.json" ] || stop "batch_state.json missing"
cd "$PAPER" || stop "cannot enter checkout"
export AR_HARNESS_ROOT="$HARNESS" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
unset LLAMACPP_CACHE_PROMPT PYTHONPATH PYTHONHOME
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
cp -p "$BATCH/batch_state.json" "$PO/batch_state.json"
[ -s "$BATCH/b2_manifests.json" ] && cp -p "$BATCH/b2_manifests.json" "$PO/b2_manifests.json" || echo "no b2_manifests.json yet" > "$PO/b2_manifests.absent.txt"
# verified analysis: ranks only if the grid verifier passes (exits non-zero on failure)
if "$PY" -B -m r1.exam.analyze b2 --batch "$BATCH" --config "$PAPER/r1/scripts/configs/exam_b2_v2.json" \
     --rule r1/exam/rules/x5_rule_v2.yaml --rule-sha256 "$RULE_SHA" > "$PO/analysis.json" 2> "$PO/analysis.err"; then arc=0; else arc=$?; fi
printf '%s\n' "$arc" > "$PO/analysis.rc"
[ "$arc" -eq 0 ] || stop "verified B2 analysis failed (rc=$arc; see postrun/analysis.err)"
# invalid-trial counts per candidate/mode/check from the proposal journals
"$PY" - "$BATCH" "$PO/invalid_trials.json" <<'PY'
import json, sys
from collections import Counter
from pathlib import Path
batch = Path(sys.argv[1])
counts = Counter(); total = 0; journals = 0
for j in sorted(batch.rglob('b1_proposals.jsonl')):
    journals += 1
    for line in j.read_text(errors='replace').splitlines():
        line = line.strip()
        if not line: continue
        try: row = json.loads(line)
        except json.JSONDecodeError: continue
        total += 1
        check = row.get('check') or row.get('outcome') or 'unknown'
        if str(check).lower() in ('ok', 'pass', 'accepted', 'executed', 'none', ''): continue
        parts = j.relative_to(batch).parts
        cand = parts[0] if parts else '?'
        mode = parts[1] if len(parts) > 1 else '?'
        counts[f"{cand}/{mode}/{check}"] += 1
out = {'journals': journals, 'proposal_rows': total, 'rejected_by_check': dict(sorted(counts.items()))}
Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + '\n')
print(json.dumps(out, indent=1))
PY
sha256sum "$PO"/* > "$PO/SHA256SUMS" 2>/dev/null || true
echo "POSTRUN_COLLECT_OK $PO"
