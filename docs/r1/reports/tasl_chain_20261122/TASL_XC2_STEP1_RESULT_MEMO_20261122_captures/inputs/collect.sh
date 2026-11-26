set -u
HOST=$(hostname)
B=/home/dowling/r1_tracks/t1_tasl
RUNID=g1b-tasl-20261121-b-xc2-$HOST
C=$B/captures/xc2_20261122/$HOST
mkdir -p "$C"
{
  echo "# collect host=$HOST utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# run_id=$RUNID"
  echo "## sealed tree"; find $B/sealed_g1b -maxdepth 4 -mindepth 1 | sort
  echo "## runs tree"; find $B/runs -maxdepth 4 -mindepth 1 | sort
} > "$C/trees.txt"
for N in mlab_cifar10 mlgym_cifar10 mlgym_breakout_minatar; do
  SD=$B/sealed_g1b/$RUNID/$N/attempt-1
  ( cd "$SD" && sha256sum -c SHA256SUMS ) > "$C/$N.sha256sum_check.txt" 2>&1
  echo "sha256sum_check_rc [$N]=$?" >> "$C/sha256sum_check_rc.txt"
  cp "$SD/job_record.json" "$C/$N.job_record.json"
  cp "$SD/SEAL_RECEIPT.json" "$C/$N.SEAL_RECEIPT.json"
  cp "$SD/node.log" "$C/$N.node.log"
  cp "$SD/SHA256SUMS" "$C/$N.SHA256SUMS"
  cp "$SD/out.tar" "$C/$N.out.tar"
  cp "$B/runs/$RUNID/_specs/$N.json" "$C/$N.derived_spec.json"
  ( cd "$SD" && sha256sum SEAL_RECEIPT.json job_record.json out.tar node.log SHA256SUMS ) > "$C/$N.sealed.sha256" 2>&1
  echo "--- $N ---"
  cat "$C/$N.sealed.sha256"
done
# derived spec sha256 vs job record spec_sha256
/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python - <<'PY' > "$C/spec_sha_binding.txt" 2>&1
import hashlib, json
from pathlib import Path
B = Path("/home/dowling/r1_tracks/t1_tasl")
host = __import__("socket").gethostname()
run = f"g1b-tasl-20261121-b-xc2-{host}"
for node in ("mlab_cifar10", "mlgym_cifar10", "mlgym_breakout_minatar"):
    spec = B/"runs"/run/"_specs"/f"{node}.json"
    rec = json.loads((B/"sealed_g1b"/run/node/"attempt-1"/"job_record.json").read_text())
    print(node, "derived_spec_sha256=", hashlib.sha256(spec.read_bytes()).hexdigest(),
          "job_record_spec_sha256=", rec.get("spec_sha256"),
          "match=", hashlib.sha256(spec.read_bytes()).hexdigest() == rec.get("spec_sha256"),
          "stop_class=", rec.get("stop_class"), "attempt=", rec.get("attempt"))
PY
cat "$C/spec_sha_binding.txt"
# preserve old TASL attempts listing (no touch)
{ echo "## old sealed attempts (not touched)"; find $B/sealed_g1b/g1b-tasl-20261121-a $B/sealed_g1b/g1b-tasl-20261121-b $B/sealed_g1b/g1b-tasl-20261121-b-xc-TASL-7 -maxdepth 3 -type f 2>/dev/null | sort; echo "## old sealed attempts sha of SEAL_RECEIPT/sums"; for f in $(find $B/sealed_g1b/g1b-tasl-20261121-a $B/sealed_g1b/g1b-tasl-20261121-b $B/sealed_g1b/g1b-tasl-20261121-b-xc-TASL-7 -maxdepth 3 -name SEAL_RECEIPT.json 2>/dev/null | sort); do sha256sum "$f"; done; } > "$C/old_attempts.txt" 2>&1
echo COLLECT_OK
