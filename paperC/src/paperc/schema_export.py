"""Write paperC/schemas/spt_transition_v1.json from paperc.schema (runbook P1). ENGINEERING_ONLY."""
import json
from pathlib import Path

from paperc.schema import to_json_schema

OUT = Path(__file__).resolve().parents[2] / "schemas" / "spt_transition_v1.json"


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(to_json_schema(), indent=2, sort_keys=True) + "\n")
    return OUT


if __name__ == "__main__":
    print(main())
