set -u
B=/home/dowling/r1_tracks/t1_tasl
P=$B/paper_xc2
PY=$B/envs/torch312/bin/python
SPEC=$P/sweep2/t1_tasl/g1b_crosscheck_spec.json
RUN7=g1b-tasl-20261121-b-xc2-TASL-7
RUN2=g1b-tasl-20261121-b-xc2-TASL-2
PEER=$B/captures/xc2_20261122/peer_TASL-2/$RUN2
VD=$B/captures/xc2_20261122/verdicts
mkdir -p "$VD"
cd "$P" || exit 9
export PYTHONDONTWRITEBYTECODE=1
echo "# compare run $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
echo "# checkout=$P HEAD=$(git rev-parse HEAD) origin_main=$(git rev-parse origin/main)"
echo "# spec=$SPEC sha256=$(sha256sum "$SPEC" | cut -d' ' -f1)"
echo "# TASL-7 sealed run=$RUN7"
echo "# TASL-2 peer=$PEER (source: TASL-2 sealed_g1b/$RUN2, SHA256SUMS verified on transfer)"
for N in mlab_cifar10 mlgym_cifar10 mlgym_breakout_minatar; do
  echo "=== compare $N ==="
  "$PY" sweep2/t1_tasl/g1b_crosscheck.py compare "$SPEC" --mode xc --node "$N" \
    --a "$B/sealed_g1b/$RUN7/$N/attempt-1" \
    --b "$PEER/$N/attempt-1" \
    --out "$VD/$N.xc.verdict.json"
  rc=$?
  echo "COMPARE_RC $N=$rc"
done
echo "=== verdicts ==="
ls -la "$VD"
sha256sum "$VD"/*.json
