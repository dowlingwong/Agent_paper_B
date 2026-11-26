#!/usr/bin/env bash
# Launch the fresh DT4 attempt on Ada (PLAN §10, 13 Oct 2026). Run on ucrtasl.
# It clones origin/main into a new batch directory, reuses the DT1 harness venv and the
# pinned model files, and starts the runner in tmux session r1_dt4_rerun.
set -euo pipefail
[ "$(hostname -s)" = ucrtasl ] || { echo 'STOP: run this on Ada (ucrtasl)'; exit 1; }
OLD=/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh
PREV=/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_idle_20261013_khbc3ro5
PY=$OLD/autoresearch_harness/.venv/bin/python
for p in "$PY" "$OLD/ollama_models" "$PREV/batch_state.json" "$PREV/deepthought_disabled.json" /usr/local/bin/ollama; do
  [ -e "$p" ] || { echo "STOP: missing $p"; exit 1; }
done
tmux has-session -t r1_dt4_rerun 2>/dev/null && { echo 'STOP: tmux session r1_dt4_rerun already exists'; exit 1; }
BATCH=$(mktemp -d "/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_$(date -u +%Y%m%d)_XXXXXX")
git clone -q git@github.com:dowlingwong/Agent_paper_B.git "$BATCH/agent_paper_B"
cat > "$BATCH/env.sh" <<ENV
export R1_BATCH_DIRECTORY=$BATCH R1_PREVIOUS_BATCH=$PREV R1_PAPER_ROOT=$BATCH/agent_paper_B
export AR_HARNESS_ROOT=$OLD/autoresearch_harness R1_OLLAMA_BINARY=/usr/local/bin/ollama R1_OLLAMA_MODELS=$OLD/ollama_models
export R1_GPU_UUID=auto R1_EXECUTOR='Claude (runner) on Ada, started by the author'
export R1_COAUTHOR='Claude Opus 5.5 <noreply@anthropic.com>'
ENV
tmux new-session -d -s r1_dt4_rerun "bash -c '. $BATCH/env.sh && cd $BATCH/agent_paper_B && $PY r1/scripts/ada_rerun_dt4.py > $BATCH/runner.log 2>&1'"
echo "Launched. Batch: $BATCH"
echo "Follow:  tail -f $BATCH/runner.log   |   GPU census: $BATCH/gpu_census.jsonl"
