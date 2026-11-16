"""Real CPU worker seed check through the B1 audit preservation path."""
import math
import os
from pathlib import Path

import pytest

from r1.c3 import audit


HARNESS = Path(os.environ.get("AR_HARNESS_ROOT", Path(__file__).resolve().parents[3] / "autoresearch_harness"))


@pytest.mark.skipif(not (HARNESS / "nodes" / "tabular_mlp").exists() or os.environ.get("C3_SKIP_WORKER") == "1",
                    reason="harness checkout not available")
def test_b1_real_worker_run_is_seed_deterministic(tmp_path):
    files = {"train.py": (HARNESS / "nodes" / "tabular_mlp" / "train.py").read_text()}
    results = audit.run_config("tabular_mlp", files, [7001, 7001], str(tmp_path),
                               preserve_node_outputs=True, stop_on_invalid=True)
    assert len(results) == 2 and all(result["success"] for result in results), results
    assert all(math.isfinite(result["metric"]) for result in results), results
    assert results[0]["metric"] == results[1]["metric"], results
