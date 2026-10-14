"""Write the D25 scripted-proposal golden file (run once, from pre-change code).

    python -m r1.scripts.gen_scripted_golden

The generated file is committed and checked by r1/tests/test_scripted_golden.py.
AI-assisted (BUILD_BATCH3, P2); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
from pathlib import Path

from r1.harness import REPO
from r1.headroom.scripted_golden import golden

TARGET = REPO / "r1" / "tests" / "data" / "scripted_proposal_golden_E1b_20261012T161034Z.json"


def main() -> int:
    payload = golden()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(TARGET), "instances": len(payload["instances"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
