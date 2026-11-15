#!/bin/bash
# B2 post-run collection (host, staged checkout): verify exit 0, collect batch_state + b2_manifests,
# run the verified B2 analysis (grid verifier), aggregate the authoritative per-manifest
# proposal_journal.rejected_by_check by candidate/mode/check, and write the hand-back receipts.
# Creates $RUN_DIR/postrun itself (fresh/absent). Read-only on the batch; no retry (STOP -> move
# the whole postrun dir aside, re-create, record the reason; never delete).
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
[ "$(cat "$RUN_DIR/b2.exit" 2>/dev/null)" = 0 ] || stop "b2.exit is not 0 (STOP: preserve; do not collect/retire)"
[ -s "$BATCH/batch_state.json" ] || stop "batch_state.json missing"
[ ! -e "$PO/analysis.json" ] || stop "analysis.json already exists (no retry; move the postrun dir aside and re-create)"
[ ! -e "$PO/POSTRUN_COLLECT_OK" ] || stop "POSTRUN_COLLECT_OK already exists"
if [ -e "$PO" ]; then [ -d "$PO" ] && [ ! -L "$PO" ] || stop "postrun path exists and is not a plain dir"; else mkdir -m 700 "$PO" || stop "cannot create postrun dir"; fi
# postrun dir created by us (B-8); record it exclusively
[ ! -e "$PO/CREATED.txt" ] || stop "postrun dir already initialised"
set -C; printf 'postrun_dir_created_utc=%s\n' "$(date -u +%FT%TZ)" > "$PO/CREATED.txt" || stop "cannot write CREATED.txt"
cd "$PAPER" || stop "cannot enter checkout"
export AR_HARNESS_ROOT="$HARNESS" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
unset LLAMACPP_CACHE_PROMPT PYTHONPATH PYTHONHOME
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
cp -p "$BATCH/batch_state.json" "$PO/batch_state.json"
# verified analysis: ranks only after the B2 grid verifier passes; non-zero rc is a STOP
if "$PY" -B -m r1.exam.analyze b2 --batch "$BATCH" --config "$PAPER/r1/scripts/configs/exam_b2_v2.json" \
     --rule r1/exam/rules/x5_rule_v2.yaml --rule-sha256 "$RULE_SHA" > "$PO/analysis.json" 2> "$PO/analysis.err"; then arc=0; else arc=$?; fi
printf '%s\n' "$arc" > "$PO/analysis.rc"
[ "$arc" -eq 0 ] || stop "verified B2 analysis failed (rc=$arc; move postrun aside, preserve partial JSON, re-create)"
[ -s "$BATCH/b2_manifests.json" ] || stop "b2_manifests.json missing after a successful verified analysis (unexpected)"
cp -p "$BATCH/b2_manifests.json" "$PO/b2_manifests.json"
# authoritative invalid-trial table: per-manifest proposal_journal.rejected_by_check
"$PY" - "$BATCH" "$PO/invalid_trials.json" <<'PY' || stop "invalid-trial aggregation failed"
import json, sys
from collections import Counter
from pathlib import Path
batch, out = Path(sys.argv[1]), Path(sys.argv[2])
agg = Counter(); roots = 0; journals = 0; rows = 0; checks_seen = set()
for m in sorted(batch.rglob('campaign_manifest.json')):
    d = json.loads(m.read_text())
    pj = d.get('proposal_journal') or {}
    cand = d.get('candidate') or m.relative_to(batch).parts[0]
    mode = d.get('mode') or (m.relative_to(batch).parts[2] if len(m.relative_to(batch).parts) > 2 else '?')
    roots += 1
    journals += 1 if pj else 0
    rows += len(pj.get('rows') or [])
    for check, n in (pj.get('rejected_by_check') or {}).items():
        agg[f"{cand}/{mode}/{check}"] += int(n)
        checks_seen.add(check)
summary = {'roots_scanned': roots, 'journals': journals, 'journal_rows': rows,
           'rejected_by_check': dict(sorted(agg.items())),
           'checks_seen': sorted(checks_seen)}
out.write_text(json.dumps(summary, indent=1) + '\n')
print(json.dumps(summary, indent=1))
PY
sha256sum "$PO"/* > "$PO/SHA256SUMS" 2>/dev/null || true
# collect-ok receipt: only after every artifact above succeeded
set -C
{
  echo "postrun_collect_ok_utc=$(date -u +%FT%TZ)"
  echo "analysis_rc=$arc"
  sha256sum "$PO/analysis.json" "$PO/batch_state.json" "$PO/b2_manifests.json" "$PO/invalid_trials.json" | sed 's# .*/# #'
} > "$PO/POSTRUN_COLLECT_OK" || stop "cannot write POSTRUN_COLLECT_OK"
echo "POSTRUN_COLLECT_OK $PO"
