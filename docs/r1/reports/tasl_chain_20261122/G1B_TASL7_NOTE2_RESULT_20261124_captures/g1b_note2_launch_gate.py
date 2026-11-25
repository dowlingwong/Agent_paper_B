"""The strict launch gate for the three TASL-7 nodes of note 2, without running a job:
G.launch() runs validate_spec(launch), check_note (note on origin/main, spec sha, run_id, harness, P1-P6),
the P7 R1-T1-TASL-ENV gate, both keys, both host-check records, and verify_launch_tasl; the runner is a stub."""
import json
import sys
from pathlib import Path

checkout = Path(sys.argv[1])
sys.path.insert(0, str(checkout / "sweep2" / "t1_tasl"))
import g1b_tasl as G  # noqa: E402

spec = Path(sys.argv[2])
note = Path(sys.argv[3])
out = {}
for node in sys.argv[4:]:
    rec = G.launch(spec, note, node, enable=True, runner=lambda s, n: {})
    out[node] = {"ok": True, "launch": rec["launch"]}
print(json.dumps(out, indent=1, sort_keys=True))
