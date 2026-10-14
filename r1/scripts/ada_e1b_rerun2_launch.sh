#!/usr/bin/env bash
# Launch the E1b rerun-2 on Ada (R1-E1B-RERUN2, PLAN §10, 14 Oct 2026).
#
#   ssh experiment_zhixu 'bash -s -- --prepare' < r1/scripts/ada_e1b_rerun2_launch.sh
#   ssh experiment_zhixu 'bash -s -- --start <batch dir>' < r1/scripts/ada_e1b_rerun2_launch.sh
#
# --prepare creates a fresh batch directory under /data1/dowling/tmp/, clones
# the paper at origin/main and the harness at the r1/scripts/HARNESS_PIN_RERUN2
# head, syncs the harness venv, writes env.sh and runs the harness suite and
# make r1-test there; it starts nothing and writes prepare.json.  --start
# refuses unless prepare.json shows no test failure outside the accepted
# environmental set, then starts tmux r1_e1b_rerun2.  It refuses to start if
# that session or one of our r1_ollama_* sessions already exists.
set -euo pipefail
[ "$(hostname -s)" = ucrtasl ] || { echo 'STOP: run this on Ada (ucrtasl)'; exit 1; }

BATCH_ROOT="${R1_RERUN2_BATCH_ROOT:-/data1/dowling/tmp}"
OLD="${R1_RERUN2_PINNED_BATCH:-/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh}"
MODELS=$OLD/ollama_models
OLLAMA_BIN="${R1_RERUN2_OLLAMA_BINARY:-/usr/local/bin/ollama}"
PAPER_REMOTE="${R1_RERUN2_PAPER_REMOTE:-git@github.com:dowlingwong/Agent_paper_B.git}"
HARNESS_REMOTE="${R1_RERUN2_HARNESS_REMOTE:-git@github.com:dowlingwong/autoresearch_harness.git}"
SESSION=r1_e1b_rerun2
EXECUTOR="${R1_EXECUTOR:-the launching agent on Ada}"
COAUTHOR="${R1_COAUTHOR:-AI-assisted <noreply@example.com>}"

refuse_duplicates() {
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "STOP: tmux session $SESSION already exists"; exit 1
  fi
  if tmux ls 2>/dev/null | grep -q '^r1_ollama_'; then
    echo 'STOP: one of our r1_ollama_* sessions already exists'; exit 1
  fi
}

write_prepare_json() {
  local batch="$1" harness_rc="$2" paper_rc="$3" paper_head="$4" harness_head="$5"
  python3 - "$batch" "$harness_rc" "$paper_rc" "$paper_head" "$harness_head" <<'PY'
import json, re, sys
from pathlib import Path

batch, harness_rc, paper_rc = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
accepted = [
    "tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns",
    "tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist",
    "tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist",
    "tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance",
    "tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance",
    "tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance",
    "tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links",
    "tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance",
    "tests/test_legacy_noop_skip.py",
    # Author-approved environmental exception (PLAN §10, 12 Oct): Ada has no /bin/zsh.
    "tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm",
]

def failures(log):
    ids = []
    for line in log.splitlines():
        match = re.match(r"^(?:FAILED|ERROR)\s+(\S+)", line.strip())
        if match:
            ids.append(match.group(1))
    return ids

def summary(log):
    for line in reversed(log.splitlines()):
        text = line.strip()
        if re.search(r"\d+ (passed|failed|error)", text):
            return text
    return "(no summary line)"

harness_log = (batch / "harness_tests.log").read_text(errors="replace")
paper_log = (batch / "paper_tests.log").read_text(errors="replace")
harness_failures = failures(harness_log)
unexpected = [f for f in harness_failures if f not in accepted]
if harness_rc != 0 and not harness_failures:
    # A crash, interruption or usage error that writes no per-test line must
    # never look clean (review F8).
    unexpected.append(f"harness suite exited {harness_rc} with no parsed FAILED/ERROR lines")
paper_failures = failures(paper_log)
if paper_rc != 0:
    unexpected += [f"r1-test: {f}" for f in (paper_failures or [f"exited {paper_rc} with no parsed failures"])]
payload = {
    "batch": str(batch),
    "paper_head": sys.argv[4] if len(sys.argv) > 4 else None,
    "harness_head": sys.argv[5] if len(sys.argv) > 5 else None,
    "harness_tests": {"returncode": harness_rc, "summary": summary(harness_log),
                      "failures": harness_failures, "unexpected": unexpected},
    "r1_tests": {"returncode": paper_rc, "summary": summary(paper_log),
                 "failures": paper_failures},
    "accepted_failures": accepted,
    "ok": not unexpected,
}
(batch / "prepare.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"ok": payload["ok"], "unexpected": unexpected,
                  "harness_tests": payload["harness_tests"]["summary"],
                  "r1_tests": payload["r1_tests"]["summary"]}, indent=2))
PY
}

case "${1:-}" in
--prepare)
  refuse_duplicates
  for p in "$MODELS" "$OLLAMA_BIN"; do
    [ -e "$p" ] || { echo "STOP: missing $p"; exit 1; }
  done
  command -v uv >/dev/null 2>&1 || { echo 'STOP: uv is not installed'; exit 1; }
  command -v python3 >/dev/null 2>&1 || { echo 'STOP: python3 is not installed'; exit 1; }
  BATCH=$(mktemp -d "$BATCH_ROOT/r1_e1b_rerun2_ENGINEERING_ONLY_$(date -u +%Y%m%d)_XXXXXX")
  git clone -q "$PAPER_REMOTE" "$BATCH/agent_paper_B"
  PAPER_HEAD=$(git -C "$BATCH/agent_paper_B" rev-parse HEAD)
  PIN=$(tr -d '[:space:]' < "$BATCH/agent_paper_B/r1/scripts/HARNESS_PIN_RERUN2")
  [ -n "$PIN" ] || { echo 'STOP: HARNESS_PIN_RERUN2 is empty'; exit 1; }
  git clone -q "$HARNESS_REMOTE" "$BATCH/autoresearch_harness"
  git -C "$BATCH/autoresearch_harness" checkout -q "$PIN"
  HARNESS_HEAD=$(git -C "$BATCH/autoresearch_harness" rev-parse HEAD)
  [ "$HARNESS_HEAD" = "$PIN" ] || { echo "STOP: harness checkout is $HARNESS_HEAD, pin is $PIN"; exit 1; }
  ( cd "$BATCH/autoresearch_harness" && uv sync ) > "$BATCH/uv_sync.log" 2>&1 || {
    echo 'STOP: uv sync failed; see uv_sync.log'; exit 1; }
  PY=$BATCH/autoresearch_harness/.venv/bin/python
  [ -x "$PY" ] || { echo 'STOP: harness venv missing after uv sync'; exit 1; }
  cat > "$BATCH/env.sh" <<ENV
export R1_BATCH_DIRECTORY=$BATCH
export R1_PAPER_ROOT=$BATCH/agent_paper_B
export AR_HARNESS_ROOT=$BATCH/autoresearch_harness
export R1_OLLAMA_BINARY=$OLLAMA_BIN
export R1_OLLAMA_MODELS=$MODELS
export R1_GPU_UUID=auto
export R1_EXECUTOR='$EXECUTOR'
export R1_COAUTHOR='$COAUTHOR'
ENV
  set +e
  ( cd "$BATCH/autoresearch_harness" && uv run python -m pytest --continue-on-collection-errors \
      -p no:cacheprovider -q ) > "$BATCH/harness_tests.log" 2>&1
  HARNESS_RC=$?
  ( cd "$BATCH/agent_paper_B" && make r1-test AR_HARNESS_ROOT="$BATCH/autoresearch_harness" \
      R1_PY="$PY" ) > "$BATCH/paper_tests.log" 2>&1
  PAPER_RC=$?
  set -e
  write_prepare_json "$BATCH" "$HARNESS_RC" "$PAPER_RC" "$PAPER_HEAD" "$HARNESS_HEAD"
  echo "PREPARED. Batch: $BATCH"
  echo "Review $BATCH/prepare.json, then: --start $BATCH"
  ;;
--start)
  refuse_duplicates
  B="${2:?usage: $0 --start <batch dir>}"
  [ -d "$B" ] || { echo "STOP: $B is not a directory"; exit 1; }
  [ -f "$B/prepare.json" ] || { echo "STOP: $B/prepare.json is missing; run --prepare first"; exit 1; }
  [ -f "$B/env.sh" ] || { echo "STOP: $B/env.sh is missing; run --prepare first"; exit 1; }
  PY=$B/autoresearch_harness/.venv/bin/python
  [ -x "$PY" ] || { echo 'STOP: harness venv is missing; re-run --prepare'; exit 1; }
  python3 - "$B" <<'PY'
import json, sys
from pathlib import Path
batch = Path(sys.argv[1])
payload = json.loads((batch / "prepare.json").read_text())
unexpected = payload.get("harness_tests", {}).get("unexpected", [])
if not payload.get("ok") or unexpected:
    print("STOP: test failures outside the accepted environmental set:")
    for failure in unexpected or ["prepare.json says ok=false"]:
        print("  -", failure)
    sys.exit(1)
print("prepare.json: no test failure outside the accepted environmental set")
PY
  tmux new-session -d -s "$SESSION" \
    "bash -c '. $B/env.sh && cd $B/agent_paper_B && $PY r1/scripts/ada_e1b_rerun2.py > $B/runner.log 2>&1'"
  echo "Launched. Batch: $B"
  echo "Follow:  tail -f $B/runner.log   |   GPU census: $B/gpu_census.jsonl"
  ;;
*)
  echo "usage: $0 --prepare | $0 --start <batch dir>"
  exit 1
  ;;
esac
