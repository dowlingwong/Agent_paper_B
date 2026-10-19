#!/usr/bin/env bash
# Launch the C3 label sweep (PLAN §10: R1-E1B-RERUN2 revision, R1-C3; C3_DESIGN §4).
#
#   ssh experiment_zhixu 'bash -s -- --prepare' < r1/scripts/c3_label_sweep_launch.sh
#   ssh experiment_zhixu 'bash -s -- --start <batch dir>' < r1/scripts/c3_label_sweep_launch.sh
#
# --prepare makes a fresh batch directory, clones the paper at the remote main
# head and the harness at r1/scripts/HARNESS_PIN_C3, syncs the harness venv,
# writes env.sh (R1_C3_CONFIG may name the JSON config; it is copied into the
# batch) and runs the harness suite and make r1-test there; it starts nothing.
# --start refuses unless prepare.json is clean (accepted environmental failures
# only), then runs the runner in tmux session r1_c3_sweep.  The runner itself
# does the Paper A coordination check, starts the batch's dedicated Ollama and
# enforces D28 first.  AI-assisted (Claude); ENGINEERING_ONLY.
set -euo pipefail
DRYRUN=${R1_DRYRUN:-0}
if [ "$DRYRUN" = 1 ]; then
  [ "$(hostname -s)" != ucrtasl ] || { echo 'STOP: DRYRUN is forbidden on Ada'; exit 1; }
  python3 -c 'from r1.scripts.dryrun_guard import validate_dryrun; validate_dryrun()'
fi
BATCH_ROOT="${R1_C3_BATCH_ROOT:-/data1/dowling/tmp}"
PAPER_REMOTE="${R1_C3_PAPER_REMOTE:-git@github.com:dowlingwong/Agent_paper_B.git}"
HARNESS_REMOTE="${R1_C3_HARNESS_REMOTE:-git@github.com:dowlingwong/autoresearch_harness.git}"
SESSION=r1_c3_sweep
REMOTE=origin; LABEL=ENGINEERING_ONLY
if [ "$DRYRUN" = 1 ]; then REMOTE=dryrun; LABEL=DRYRUN; fi

refuse_duplicates() {
  if tmux has-session -t "$SESSION" 2>/dev/null; then echo "STOP: tmux session $SESSION already exists"; exit 1; fi
}

case "${1:-}" in
--prepare)
  refuse_duplicates
  [ -n "${R1_GIT_NAME:-}" ] && [ -n "${R1_GIT_EMAIL:-}" ] || { echo 'STOP: R1_GIT_NAME and R1_GIT_EMAIL are required'; exit 1; }
  BATCH=$(mktemp -d "$BATCH_ROOT/r1_c3_sweep_${LABEL}_$(date -u +%Y%m%d)_XXXXXX")
  git clone -q "$PAPER_REMOTE" "$BATCH/agent_paper_B"
  PAPER_HEAD=$(git -C "$BATCH/agent_paper_B" rev-parse HEAD)
  PIN=$(tr -d '[:space:]' < "$BATCH/agent_paper_B/r1/scripts/HARNESS_PIN_C3")
  [ -n "$PIN" ] || { echo 'STOP: HARNESS_PIN_C3 is empty'; exit 1; }
  git clone -q "$HARNESS_REMOTE" "$BATCH/autoresearch_harness"
  git -C "$BATCH/autoresearch_harness" checkout -q "$PIN"
  [ "$(git -C "$BATCH/autoresearch_harness" rev-parse HEAD)" = "$PIN" ] || { echo 'STOP: harness pin checkout failed'; exit 1; }
  for repo in "$BATCH/agent_paper_B" "$BATCH/autoresearch_harness"; do
    if [ "$DRYRUN" = 1 ]; then git -C "$repo" remote rename origin dryrun; fi
    git -C "$repo" config --local user.name "$R1_GIT_NAME"
    git -C "$repo" config --local user.email "$R1_GIT_EMAIL"
  done
  if [ "$DRYRUN" = 1 ]; then
    export R1_BATCH_DIRECTORY="$BATCH" R1_PAPER_ROOT="$BATCH/agent_paper_B" AR_HARNESS_ROOT="$BATCH/autoresearch_harness"
    python3 -c 'from r1.scripts.dryrun_guard import validate_dryrun; validate_dryrun()'
  fi
  git -C "$BATCH/agent_paper_B" push --dry-run "$REMOTE" HEAD:refs/heads/main > "$BATCH/push_dry_run.log" 2>&1 || { echo 'STOP: paper push dry run failed'; exit 1; }
  if [ -n "${R1_C3_VENV_PYTHON:-}" ]; then
    # DRYRUN or a prepared host: use an existing interpreter with the harness deps.
    mkdir -p "$BATCH/autoresearch_harness/.venv/bin"
    ln -s "$R1_C3_VENV_PYTHON" "$BATCH/autoresearch_harness/.venv/bin/python"
    echo "venv: symlink to $R1_C3_VENV_PYTHON" > "$BATCH/uv_sync.log"
  else
    ( cd "$BATCH/autoresearch_harness" && uv sync --extra dev ) > "$BATCH/uv_sync.log" 2>&1 || { echo 'STOP: uv sync failed'; exit 1; }
  fi
  PY=$BATCH/autoresearch_harness/.venv/bin/python
  if [ -n "${R1_C3_CONFIG:-}" ]; then cp "$R1_C3_CONFIG" "$BATCH/c3_config.json"; fi
  {
    echo "export R1_BATCH_DIRECTORY=$BATCH"
    echo "export R1_PAPER_ROOT=$BATCH/agent_paper_B"
    echo "export AR_HARNESS_ROOT=$BATCH/autoresearch_harness"
    echo "export R1_C3_PY=$PY"
    echo "export PYTHONPATH=$BATCH/autoresearch_harness/src:$BATCH/agent_paper_B"
    echo "export PATH=$(dirname "$PY"):\$PATH"
    [ -f "$BATCH/c3_config.json" ] && echo "export R1_C3_CONFIG=$BATCH/c3_config.json"
    echo "export R1_COAUTHOR='${R1_COAUTHOR:-AI-assisted <noreply@example.com>}'"
    if [ "$DRYRUN" = 1 ]; then
      printf 'export R1_DRYRUN=1\nexport R1_DRYRUN_ROOT=%q\nexport R1_DRYRUN_CHILD=1\nexport R1_FAKE_OLLAMA_ROOT=%q\n' "$R1_DRYRUN_ROOT" "$R1_DRYRUN_ROOT"
      [ -n "${C3_FAKE_FAULTS:-}" ] && printf 'export C3_FAKE_FAULTS=%q\n' "$C3_FAKE_FAULTS"
    fi
    true
  } > "$BATCH/env.sh"
  if [ "${R1_C3_SKIP_SUITES:-0}" = 1 ]; then
    [ "$DRYRUN" = 1 ] || { echo 'STOP: test suites may be skipped only in DRYRUN'; exit 1; }
    echo 'SKIPPED (DRYRUN: suites run separately)' > "$BATCH/harness_tests.log"
    echo 'SKIPPED (DRYRUN: suites run separately)' > "$BATCH/paper_tests.log"
    HARNESS_RC=0; PAPER_RC=0
  else
    set +e
    ( cd "$BATCH/autoresearch_harness" && env -u R1_DRYRUN PYTHONPATH="$BATCH/autoresearch_harness/src" PATH="$(dirname "$PY"):$PATH" \
        "$PY" -m pytest --continue-on-collection-errors -p no:cacheprovider -q ) > "$BATCH/harness_tests.log" 2>&1
    HARNESS_RC=$?
    ( cd "$BATCH/agent_paper_B" && env -u R1_DRYRUN R1_DRYRUN_CHILD=1 PATH="$(dirname "$PY"):$PATH" \
        make r1-test AR_HARNESS_ROOT="$BATCH/autoresearch_harness" R1_PY="$PY" ) > "$BATCH/paper_tests.log" 2>&1
    PAPER_RC=$?
    set -e
  fi
  "$PY" "$BATCH/agent_paper_B/r1/scripts/c3_prepare_check.py" "$BATCH" "$HARNESS_RC" "$PAPER_RC" "$PAPER_HEAD" "$PIN" "${R1_C3_SKIP_SUITES:-0}"
  echo "PREPARED. Batch: $BATCH"
  ;;
--start)
  refuse_duplicates
  B="${2:?usage: $0 --start <batch dir>}"
  [ -f "$B/prepare.json" ] && [ -f "$B/env.sh" ] || { echo "STOP: run --prepare first"; exit 1; }
  if [ "$DRYRUN" = 1 ]; then
    export R1_BATCH_DIRECTORY="$B" R1_PAPER_ROOT="$B/agent_paper_B" AR_HARNESS_ROOT="$B/autoresearch_harness"
    python3 -c 'from r1.scripts.dryrun_guard import validate_dryrun; validate_dryrun()'
  fi
  python3 -c "import json,sys; p=json.load(open('$B/prepare.json')); sys.exit(0 if p.get('ok') else 'STOP: prepare.json is not clean: ' + str(p.get('unexpected')))"
  tmux new-session -d -s "$SESSION" "bash -c '. $B/env.sh && cd $B/agent_paper_B && \$R1_C3_PY r1/scripts/c3_label_sweep.py > $B/runner.log 2>&1'"
  echo "Launched. Batch: $B"
  ;;
*)
  echo "usage: $0 --prepare | $0 --start <batch dir>"; exit 1;;
esac
