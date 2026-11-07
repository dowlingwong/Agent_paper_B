#!/bin/bash
# Candidate for independent review. No production B1 or non-owned signal.
set -Eeuo pipefail
umask 077
set -C
OUT=$(mktemp -d /private/tmp/paper-b-linux-stop-60ec-20261107.XXXXXXXX)
finish() {
  rc=$?
  trap - EXIT
  printf '%s\n' "$rc" > "$OUT/exit.txt"
  shasum -a 256 "$OUT"/* > "$OUT/SHA256SUMS" || true
  printf 'Private evidence: %s; exit=%s\n' "$OUT" "$rc"
  exit "$rc"
}
trap finish EXIT
HERE=/private/tmp/paper-b-sweep-integration-review-20261107/docs/r1/proposals
CHECKER=/private/tmp/paper-b-wrapper-site-result-review-20261107/docs/r1/proposals/B1_ENGINEERING_VERIFY_ARCHIVE_TREE_20261107.py
ROOT_TEST="$HERE/B1_STOP_60EC_ROOT_EXIT_20261107.py"
LIVE_TEST="$HERE/B1_STOP_60EC_LIVE_AUDIT_TEST_20261107.py"
sha() { shasum -a 256 "$1" | awk '{print $1}'; }
test "$(sha "$CHECKER")" = 54a381e71b5a394e1b8615e2b8a5987d6bd43909fc857130acb280b22dae5920
test "$(sha "$ROOT_TEST")" = 6c2389603583c2af2aa6bd151b643d8253d4b85445068d3bf6f4256eaef4b44f
test "$(sha "$LIVE_TEST")" = 8834922f606b97ddc83cb676754f6923c9f53ce82acba546c43dc951cdcbc2dd
printf 'BEGIN_UTC %s\n' "$(date -u +%FT%TZ)" > "$OUT/metadata.txt"
# Verify bytes at the existing, already extracted 60ec engineering source.
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'python3 -I -B - /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/paper.tar /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/paper f9d2813fa5a1654c7a0785c08738dd7c23d506f7e2a0c2c0cf90401ae9ace842 /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness.tar /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness 70270971de13dd5c02531bd9c23c90e3179db1862f8e5e8543b23d8c2fb8e2a6' < "$CHECKER" > "$OUT/tree-check.log" 2>&1
test "$(grep -c '^PASS archive=' "$OUT/tree-check.log")" = 2
grep -F 'paper.tar files=263 ' "$OUT/tree-check.log" >/dev/null
grep -F 'harness.tar files=504 ' "$OUT/tree-check.log" >/dev/null
# Exclusively create the owned test directory and test source; no existing paths removed.
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$OUT/prepare.log" 2>&1 <<'REMOTE'
set -euo pipefail
umask 077
base=/home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a
for p in /home /home/dowling /home/dowling/r1_b1_engineering "$base" "$base/paper" "$base/harness" "$base/home" "$base/tmp"; do test -d "$p" && test ! -L "$p"; done
work="$base/stop_qualification_20261107"
test ! -e "$work" && test ! -L "$work"
mkdir -m 700 "$work"
REMOTE
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'set -C; cat > /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/stop_qualification_20261107/test_live.py' < "$LIVE_TEST" > "$OUT/source-upload.log" 2>&1
# The exact reviewed root-exit test executes once and stores its transcript on site.
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'set -eu; set -C; base=/home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a; work="$base/stop_qualification_20261107"; cd "$base/paper"; env -i HOME="$base/home" TMPDIR="$base/tmp" PATH=/home/dowling/exam-x/work/venv/bin:/usr/bin:/bin PYTHONPATH="$base/paper:$base/harness/src" AR_HARNESS_ROOT="$base/harness" EVIDENCE_DIR="$work" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$work/cache" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= /home/dowling/exam-x/work/venv/bin/python - > "$work/root-exit.log" 2>&1' < "$ROOT_TEST" > "$OUT/root-ssh.log" 2>&1
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'cat /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/stop_qualification_20261107/root-exit.log' > "$OUT/root-exit.log" 2>&1
grep -F 'PASS: exited root, TERM-resistant owned descendant stopped, sentinel unaffected' "$OUT/root-exit.log" >/dev/null
# Run the adapted, exact-scope live-audit test only if the first test passed.
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$OUT/live-ssh.log" 2>&1 <<'REMOTE'
set -euo pipefail
set -C
base=/home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a
work="$base/stop_qualification_20261107"
for p in "$work/pytest" "$work/live.log" "$work/cache"; do test ! -e "$p" && test ! -L "$p"; done
test "$(sha256sum "$work/test_live.py" | cut -d ' ' -f 1)" = 8834922f606b97ddc83cb676754f6923c9f53ce82acba546c43dc951cdcbc2dd
cd "$base/paper"
env -i HOME="$base/home" TMPDIR="$base/tmp" PATH=/home/dowling/exam-x/work/venv/bin:/usr/bin:/bin \
 PYTHONPATH="$base/paper:$base/harness/src" AR_HARNESS_ROOT="$base/harness" \
 PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$work/cache" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= \
 /home/dowling/exam-x/work/venv/bin/python r1/scripts/b1_engineering_timeout.py --seconds 90 \
 /home/dowling/exam-x/work/venv/bin/python -m pytest -p no:cacheprovider \
 --basetemp="$work/pytest" -v "$work/test_live.py::test_audit_stop_notifies_parent_and_stops_owned_processes" > "$work/live.log" 2>&1
cat "$work/live.log"
REMOTE
printf 'END_UTC %s\n' "$(date -u +%FT%TZ)" >> "$OUT/metadata.txt"
