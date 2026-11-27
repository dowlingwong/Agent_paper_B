# D.3 verify-seed parameter and allocation review — 27 Nov 2026

Independent tier-E review by a fresh Codex agent for `local/20261127-07`. **Verdict: ACCEPTED** for harness
`9bb416805175149eb87b71f28d77530572aa4bce` over `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` and Paper B checker
`71b7d701d00dd67da9ad4a5df86fe31b4721a219` over `8b01ef6a7d2e0687f96022c2f48f12e999d78ef9`.

The live campaign, E0/E1/E2 capture, immediate E2 replay and both continuation paths pass the same validated base.
Legacy snapshots omit the field and read it as 1000. The checker passed for 160 seed values within 20010–20801
and refused five injected conflicts. G1 should use base 20000, two verify pairs, split policy `vary` and a trial
budget of 80. The check covers one-based indexes 1–80 including all indexes the campaign can reach.

## Fixed campaign parity

Run the Python body below twice with Python 3.12, one time per harness checkout, setting
`PYTHONPATH="$HARNESS/src:$HARNESS/tests/stage2"` and passing a new fixture directory as the only argument.
The fake worker's seed-sensitive metric and E2 verify both exercise the real control plane.
Set `PYTHONDONTWRITEBYTECODE=1` if the harness checkout is read-only.

```python
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from autoresearch.control_plane import campaign
from autoresearch.control_plane.snapshot import SnapshotRecorder
from test_r1_d4_action_versions import ScriptedController, _campaign

root = Path(sys.argv[1])
root.mkdir()
recorder = SnapshotRecorder(root / "snaps", epochs=("E2",), take_index=2)
with patch.object(campaign, "_iso_now", return_value="2026-11-27T00:00:00Z"), patch.object(
    campaign, "time", SimpleNamespace(perf_counter=lambda: 0.0)
):
    records, _ = _campaign(
        root, [0.80, 0.81], events=False, snapshot_hook=recorder,
        verify_split_policy="vary", controller=ScriptedController({(2, "E2"): "verify"}),
    )
assert records[1].extra["control"]["verify"]["seeds"] == [1020, 1021]
snapshot = json.loads(recorder.manifest_path.read_text())
snapshot["node_source_root"] = "<fixture node>"
(root / "parity_snapshot.json").write_text(json.dumps(snapshot, sort_keys=True) + "\n")
```

Both checkouts produced byte-identical ledgers and fixture-path-normalized snapshots by `cmp`.

- `trials.jsonl` SHA-256 `124d26f1fbb138ca6a6927f937c3f9df78f3c55fa2719195f31b658999c52c71`
- `parity_snapshot.json` SHA-256 `98ac24672e13bab93730a5424dc482ed4f8df765e291c71f7f953520542c9a46`

The cross-pin full Paper B suite is recorded on the coordination branch. No evidence data was used in the review.
