"""The G.5 projection table (G.5 draft §2.8) for the TASL pair: ``sweep2/g4/g5_projection.table`` with the TASL dates
params (the seven passed census nodes; RTX 4090 worker on TASL-2, one slot). Pre-pilot; ENGINEERING_ONLY. The
GPU-hours are worker-card hours; the proposer card on TASL-7 is held for the campaign spans (G5-TASL-GPUH).
Usage: python sweep2/t1_tasl/g5_projection_tasl.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "g4"))
import g5_projection  # noqa: E402

PARAMS = json.loads((HERE / "g4_tasl_dates_params.json").read_text())


def table() -> dict:
    g5_projection.PARAMS = PARAMS
    return g5_projection.table()


if __name__ == "__main__":
    print(json.dumps(table(), indent=1))
