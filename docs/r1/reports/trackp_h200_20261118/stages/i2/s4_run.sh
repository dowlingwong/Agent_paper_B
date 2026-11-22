#!/bin/bash
# S4: local CPU job using our SIF (reviewed unit). I1 = environment import/version check;
# I2 = the 60ecf1da/a3fedbb CPU worker determinism test, run TWICE with every thread count 1,
# compared against 0.922225 (and train_loss 0.314016). The v2 I2 repeat isolates the
# two committed input trees under the fresh per-job output directory.
# Authority: author 14 Nov S4/S6; review HTCONDOR_CHAIN_S4_REVIEW_20261114.md.
set -uo pipefail
JOB="${1:-local.0}"
B=/work/dwong/paperb
OUT="$B/work/s4_${JOB}_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT" "$B/work"
FAIL=0
echo "job=$JOB host=$(hostname -f) date_utc=$(date -u +%FT%TZ)" > "$OUT/identity.txt"
{
  echo "== image identity =="
  echo "sif_sha256_in_identity=$(grep '^sif_sha256=' "$B/images/r1-htc-20261114.identity" 2>/dev/null | cut -d= -f2)"
  echo "sif_sha256_actual=$(sha256sum "$B/images/r1-htc-20261114.sif" 2>/dev/null | awk '{print $1}')"
  echo "sif_bytes=$(stat -c %s "$B/images/r1-htc-20261114.sif" 2>/dev/null)"
  echo "versions_sha256=$(sha256sum /opt/r1/VERSIONS.txt 2>/dev/null | awk '{print $1}')"
  echo "== job ad (placement/runtime) =="
  grep -aiE "^(RemoteHost|LastRemoteHost|ContainerImage|ContainerImageSource|WantContainer|HasSIF|MachineAttrSingularityVersion0|MachineAttrCloudSite0)" "$_CONDOR_JOB_AD" 2>/dev/null | head -12
} >> "$OUT/identity.txt"
# ---- preflight: the two pinned checkouts must exist at the reviewed commits ---------------
for repo in "$B/src/paper:60ecf1dae299ee424aa1bdfe078eab02a881b87e" "$B/src/autoresearch_harness:a3fedbbd44309b3fdf99d853ad841b9ec2c299e2"; do
  dir="${repo%%:*}"; want="${repo##*:}"
  have="$(git -C "$dir" rev-parse HEAD 2>/dev/null || echo MISSING)"
  echo "checkout $dir head=$have want=$want" >> "$OUT/identity.txt"
  if [ "$have" != "$want" ]; then echo "PREFLIGHT_FAIL checkout $dir head=$have want=$want" >> "$OUT/identity.txt"; FAIL=1; fi
  if [ -n "$(git -C "$dir" status --porcelain --untracked-files=no 2>/dev/null)" ]; then
    echo "PREFLIGHT_FAIL tracked checkout dirty: $dir" >> "$OUT/identity.txt"; FAIL=1
  fi
done
[ "$FAIL" -eq 0 ] || exit 3
[ -x /opt/r1/envs/harness/bin/python ] || { echo "PREFLIGHT_FAIL no harness env" >> "$OUT/identity.txt"; FAIL=1; }
# cpu image has no llama-server/trackp (by design); do not fail preflight on them
# ---- I1: environment import and version check ---------------------------------
{
  echo "== /opt/r1/VERSIONS.txt =="; cat /opt/r1/VERSIONS.txt 2>&1
  for env in harness tracks trackp; do
    echo "== env $env =="
    if [ -x "/opt/r1/envs/$env/bin/python" ]; then
      /opt/r1/envs/$env/bin/python -VV 2>&1
      /opt/r1/envs/$env/bin/python -c "import numpy, sklearn, pandas, pytest; print('numpy', numpy.__version__, 'sklearn', sklearn.__version__, 'pandas', pandas.__version__, 'pytest', pytest.__version__)" 2>&1 | tail -2
    else
      echo "ABSENT in this image (cpu target carries envs 1+2 only, by design)"
    fi
  done
  if [ -x /opt/r1/envs/trackp/bin/python ]; then
    echo "== trackp torch/cuda =="
    /opt/r1/envs/trackp/bin/python -c "import torch; print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available(), 'cuda_version', torch.version.cuda)" 2>&1
  fi
  echo "== llama-server =="; command -v llama-server >/dev/null 2>&1 && { llama-server --version 2>&1 | head -3; } || echo "ABSENT in this image (cpu target has no llama-server, by design)"
  echo "== uv =="; uv --version 2>&1
} > "$OUT/i1_envs.txt" 2>&1
# ---- I2: isolated archive copies of the two pinned commits ----------------------------
PAPER_COMMIT=60ecf1dae299ee424aa1bdfe078eab02a881b87e
HARNESS_COMMIT=a3fedbbd44309b3fdf99d853ad841b9ec2c299e2
PAPER="$OUT/src/paper"
HARNESS="$OUT/src/autoresearch_harness"
mkdir -p "$PAPER" "$HARNESS" || exit 3
git -C "$B/src/paper" archive "$PAPER_COMMIT" r1 | tar -x -C "$PAPER" || exit 3
git -C "$B/src/autoresearch_harness" archive "$HARNESS_COMMIT" | tar -x -C "$HARNESS" || exit 3
cd "$PAPER" || exit 3
{
  echo "archive_paper_head=$PAPER_COMMIT archive_harness_head=$HARNESS_COMMIT"
  echo "reference: val_score 0.922225 / train_loss 0.314016 (TASL-7, Python 3.13.4, numpy 2.4.4, sklearn 1.8.0, pytest 9.0.3)"
  echo "env choice: harness env1 = the 0.922225 reference stack (Python 3.13, numpy 2.4.4, sklearn 1.8.0, pytest 9.0.3); env2 tracks = numpy 2.4.6/sklearn 1.9.1/pytest 9.2.0; env3 trackp = Python 3.12"
} >> "$OUT/identity.txt"
: > "$OUT/i2_summary.txt"
for i in 1 2; do
  H="$OUT/home_$i"; T="$OUT/tmp_$i"; mkdir -p "$H" "$T"
  env -i HOME="$H" TMPDIR="$T" PATH="/opt/r1/envs/harness/bin:/usr/bin:/bin" \
    PYTHONPATH="$PAPER:$HARNESS/src" AR_HARNESS_ROOT="$HARNESS" \
    PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    timeout 600 /opt/r1/envs/harness/bin/python -m pytest -p no:cacheprovider -v \
      --basetemp="$OUT/pytest_$i" \
      r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic > "$OUT/i2_run$i.log" 2>&1
  rc=$?
  echo "run$i pytest_rc=$rc" >> "$OUT/i2_summary.txt"
  grep -E "skipped|SKIPPED|passed|failed|error" "$OUT/i2_run$i.log" | tail -3 >> "$OUT/i2_summary.txt"
  # the metric lives in the preserved worker run.log files, not in pytest stdout
  found=0
  while IFS= read -r f; do
    found=$((found+1))
    echo "run$i run.log=$f sha256=$(sha256sum "$f" | awk '{print $1}')" >> "$OUT/i2_summary.txt"
    grep -E "val_score|train_loss" "$f" >> "$OUT/i2_summary.txt" 2>&1
  done < <(find "$OUT/pytest_$i" -type f -name run.log 2>/dev/null | sort)
  [ "$found" -eq 2 ] || { echo "run$i unexpected_run_logs=$found" >> "$OUT/i2_summary.txt"; FAIL=1; }
  [ "$rc" -ne 0 ] && FAIL=1
done
# ---- verdict --------------------------------------------------------------------------------
/opt/r1/envs/harness/bin/python - "$OUT" <<'PY' || FAIL=1
import pathlib, re, sys
out = pathlib.Path(sys.argv[1])
vs, tl = [], []
for line in (out / "i2_summary.txt").read_text(errors="replace").splitlines():
    m = re.search(r"val_score[=: ]+([0-9.]+)", line)
    if m: vs.append(m.group(1))
    m = re.search(r"train_loss[=: ]+([0-9.]+)", line)
    if m: tl.append(m.group(1))
ok = (len(vs) == 4 and len(set(vs)) == 1 and vs[0] == "0.922225"
      and len(tl) == 4 and len(set(tl)) == 1 and (not tl or tl[0] == "0.314016"))
lines = [f"val_scores={vs}", f"train_losses={tl}", "expected_val_score=0.922225",
         "expected_train_loss=0.314016", "I2_" + ("PASS" if ok else "FAIL")]
(out / "i2_compare.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
sys.exit(0 if ok else 1)
PY
[ "$FAIL" -ne 0 ] && echo "S4_FAIL"
echo "S4_DONE out=$OUT fail=$FAIL"
# evidence stays on the shared /work filesystem; only output/error/log are transferred back
exit "$FAIL"
