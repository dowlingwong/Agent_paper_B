#!/bin/bash
# S4: local CPU job using our SIF. I1 = environment import/version check; I2 = the 60ecf1da/a3fedbb
# CPU worker determinism test, run TWICE with all thread counts 1, compared against the recorded
# 0.922225; plus the S6 xrootd attempt from a worker. Read-only on the checkouts; writes under
# /work/dwong/paperb/work/. Authority: author 14 Nov S4/S6.
set -uo pipefail
B=/work/dwong/paperb
JOB="${_CONDOR_ClusterId:-local}.${_CONDOR_ProcId:-0}"
OUT="$B/work/s4_${JOB}_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT" "$B/work"
echo "job=$JOB host=$(hostname -f) date_utc=$(date -u +%FT%TZ)" > "$OUT/identity.txt"
echo "container_image=VERSIONS below" >> "$OUT/identity.txt"
# ---- I1: environment import and version check ---------------------------------
{
  echo "== /opt/r1/VERSIONS.txt =="; cat /opt/r1/VERSIONS.txt 2>&1
  for env in harness tracks trackp; do
    echo "== env $env =="
    /opt/r1/envs/$env/bin/python -VV 2>&1
    /opt/r1/envs/$env/bin/python -c "import numpy, sklearn, pandas; print('numpy', numpy.__version__, 'sklearn', sklearn.__version__, 'pandas', pandas.__version__)" 2>&1 | tail -2
  done
  echo "== trackp torch/cuda =="
  /opt/r1/envs/trackp/bin/python -c "import torch; print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available(), 'cuda_version', torch.version.cuda)" 2>&1
  echo "== llama-server =="; llama-server --version 2>&1 | head -3; echo "llama_rc=$?"
  echo "== uv =="; uv --version 2>&1
} > "$OUT/i1_envs.txt" 2>&1
# ---- S6: xrootd from a worker ------------------------------------------------
{
  for ep in ceph-node-j.etp.kit.edu ceph-node-a.etp.kit.edu; do
    echo "== root://$ep =="
    timeout 20 xrdfs "root://$ep" ls /dwong 2>&1 | head -5; echo "ls_rc=$?"
    timeout 30 xrdcp "root://$ep/dwong/paperb/chain_20261114_xrootd_test.txt" "$OUT/xrdcp_readback.txt" --force 2>&1 | tail -2; echo "xrdcp_rc=$?"
    [ -f "$OUT/xrdcp_readback.txt" ] && sha256sum "$OUT/xrdcp_readback.txt" || echo "no readback file"
  done
} > "$OUT/s6_xrootd.txt" 2>&1
# ---- I2: the 60ec CPU worker determinism test, twice, all threads 1 -----------
cd "$B/src/paper" || { echo "paper checkout missing"; exit 3; }
echo "paper_head=$(git rev-parse HEAD) harness_head=$(git -C "$B/src/autoresearch_harness" rev-parse HEAD)" >> "$OUT/identity.txt"
: > "$OUT/i2_summary.txt"
for i in 1 2; do
  mkdir -p "$B/work/home_$i" "$B/work/tmp_$i"
  env -i HOME="$B/work/home_$i" TMPDIR="$B/work/tmp_$i" PATH="/opt/r1/envs/trackp/bin:/usr/bin:/bin" \
    PYTHONPATH="$B/src/paper:$B/src/autoresearch_harness/src" AR_HARNESS_ROOT="$B/src/autoresearch_harness" \
    PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    /opt/r1/envs/trackp/bin/python -m pytest -p no:cacheprovider -v \
      --basetemp="$B/work/s4_pytest_$i" \
      r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic > "$OUT/i2_run$i.log" 2>&1
  rc=$?
  {
    echo "run$i rc=$rc"
    grep -E "val_score|train_loss" "$OUT/i2_run$i.log" | tail -4
    sha256sum "$OUT/i2_run$i.log"
  } >> "$OUT/i2_summary.txt"
done
# compare the two runs and the recorded reference 0.922225
python3 - "$OUT" <<'PY'
import re, sys, pathlib
out = pathlib.Path(sys.argv[1])
vals = []
for i in (1, 2):
    txt = (out / f"i2_run{i}.log").read_text(errors="replace")
    vs = re.findall(r"val_score[=: ]+([0-9.]+)", txt)
    vals.append(vs[-1] if vs else "MISSING")
lines = [f"run{i+1}_val_score={v}" for i, v in enumerate(vals)]
lines.append("recorded_tasl7_reference=0.922225")
lines.append("two_runs_equal=" + str(vals[0] == vals[1]))
lines.append("matches_recorded_reference=" + str(vals[0] == "0.922225"))
(out / "i2_compare.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
PY
echo "S4_DONE out=$OUT"
exit 0
