#!/usr/bin/env python3
"""Paper B figure slot: risk_vs_advantage (PLANNED)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _slot import require_dataset  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(require_dataset("risk_vs_advantage"))
