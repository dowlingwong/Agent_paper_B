#!/bin/bash
# Candidate for independent review. Run once only after the documented site prerequisites.
set -Eeuo pipefail
umask 077
set -C
OUT=$(mktemp -d /private/tmp/paper-b-worker-once-60ec-20261107.XXXXXXXX)
finish() {
  rc=$?
  trap - EXIT
  printf '%s\n' "$rc" > "$OUT/exit.txt"
  shasum -a 256 "$OUT"/* > "$OUT/SHA256SUMS" || true
  printf 'Private evidence: %s; exit=%s\n' "$OUT" "$rc"
  exit "$rc"
}
trap finish EXIT
printf 'BEGIN_UTC %s\n' "$(date -u +%FT%TZ)" > "$OUT/metadata.txt"
PAPER_DIR=/private/tmp/paper-b-b1-engineering-60ec-20261107
HARNESS_DIR=/private/tmp/paper-b-b1-tests-harness-20261107
CHECKER=/private/tmp/paper-b-wrapper-site-result-review-20261107/docs/r1/proposals/B1_ENGINEERING_VERIFY_ARCHIVE_TREE_20261107.py
PRIOR=/private/tmp/paper-b-worker-tree-check-20261107.vMmiRk5N
PREFLIGHT=/private/tmp/paper-b-b1-engineering-60ec-preflight-20261107.log
SITE=/private/tmp/paper-b-b1-engineering-60ec-site-evidence-20261107.log
sha() { shasum -a 256 "$1" | awk '{print $1}'; }
test "$(git -C "$PAPER_DIR" rev-parse HEAD)" = 60ecf1dae299ee424aa1bdfe078eab02a881b87e
test -z "$(git -C "$PAPER_DIR" status --porcelain)"
test "$(git -C "$HARNESS_DIR" rev-parse HEAD)" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2
test -z "$(git -C "$HARNESS_DIR" status --porcelain --untracked-files=no)"
test "$(sha "$CHECKER")" = 54a381e71b5a394e1b8615e2b8a5987d6bd43909fc857130acb280b22dae5920
test "$(sha "$PREFLIGHT")" = 4ffea5a39866f1b03b4a4e349c4120004a609702438d9f092a9a5102c864ef6f
test "$(sha "$SITE")" = 498b93abf8bd469898001ab15d642d4d467a83705330f0330fd99d0762aa83ae
test "$(sha "$PRIOR/tree-check.log")" = 3b44d8b432f7d87910c01c9bdc9ec281604bace257eead4529a50e5d8c8ad4f0
test "$(sha "$PRIOR/exit.txt")" = 9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa
test "$(cat "$PRIOR/exit.txt")" = 0
# Read-only recheck of the already-extracted source trees; no remote files created.
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'python3 -I -B - /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/paper.tar /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/paper f9d2813fa5a1654c7a0785c08738dd7c23d506f7e2a0c2c0cf90401ae9ace842 /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness.tar /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness 70270971de13dd5c02531bd9c23c90e3179db1862f8e5e8543b23d8c2fb8e2a6' < "$CHECKER" > "$OUT/tree-check.log" 2>&1
test "$(grep -c '^PASS archive=' "$OUT/tree-check.log")" = 2
grep -F 'paper.tar files=263 ' "$OUT/tree-check.log" >/dev/null
grep -F 'harness.tar files=504 ' "$OUT/tree-check.log" >/dev/null
# One invocation only. On failure, the remote log and pytest base are retained.
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$OUT/worker-console.log" 2>&1 <<'REMOTE'
set -euo pipefail
set -o noclobber
base=/home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a
host_python=/home/dowling/exam-x/work/venv/bin/python
venv_bin=/home/dowling/exam-x/work/venv/bin
for p in /home /home/dowling /home/dowling/r1_b1_engineering "$base" "$base/paper" "$base/harness" "$base/tmp" "$base/home"; do
  test -d "$p" && test ! -L "$p"
done
for p in "$base/pytest" "$base/pytest.log" "$base/tmp/worker-pycache"; do
  test ! -e "$p" && test ! -L "$p"
done
test -x "$host_python" && test -x "$venv_bin/python3"
test "$(readlink -f "$host_python")" = "$(readlink -f "$venv_bin/python3")"
clean_python() {
  env -i HOME="$base/home" TMPDIR="$base/tmp" PATH="$venv_bin:/usr/bin:/bin" \
    PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$base/tmp/worker-pycache" \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' "$@"
}
# Both executable paths must resolve to the same venv and dependency stack.
clean_python "$host_python" -I -B -c 'import sys,pytest,numpy,sklearn; print("parent",sys.executable,sys.prefix,sys.version); print("versions",pytest.__version__,numpy.__version__,sklearn.__version__)'
clean_python "$venv_bin/python3" -I -B -c 'import sys,pytest,numpy,sklearn; print("worker",sys.executable,sys.prefix,sys.version); print("versions",pytest.__version__,numpy.__version__,sklearn.__version__)'
test "$(clean_python "$host_python" -I -B -c 'import sys; print(sys.prefix)')" = /home/dowling/exam-x/work/venv
test "$(clean_python "$venv_bin/python3" -I -B -c 'import sys; print(sys.prefix)')" = /home/dowling/exam-x/work/venv
# Isolated imports above do not accept inherited user PYTHONPATH.
cd "$base/paper"
env -i HOME="$base/home" TMPDIR="$base/tmp" PATH="$venv_bin:/usr/bin:/bin" \
  PYTHONPATH="$base/paper:$base/harness/src" AR_HARNESS_ROOT="$base/harness" \
  PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$base/tmp/worker-pycache" \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$host_python" r1/scripts/b1_engineering_timeout.py --seconds 180 "$host_python" -m pytest \
  -p no:cacheprovider --basetemp="$base/pytest" \
  -v r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic > "$base/pytest.log" 2>&1
cat "$base/pytest.log"
find "$base/pytest" -type f -name run.log -print -exec sha256sum {} \; -exec cat {} \;
REMOTE
printf 'END_UTC %s\n' "$(date -u +%FT%TZ)" >> "$OUT/metadata.txt"
