"""A fail-closed building block for future sweep-2 label readers.

AI-assisted (Codex). This does not classify a path as sweep 1, sweep 2, pilot,
or evidence; callers must establish and preserve source provenance separately.
The reader currently stops unconditionally before opening any artifact. Future
implementation must bind a committed author decision, a hash-pinned approved
analysis copy, and sealed-copy provenance; pathname checks alone are inadequate.
"""
from __future__ import annotations

from r1.c3.gate import require_gate_confirmation


def load_sweep2_jsonl(path, *, expected_sha256):
    """Currently unavailable: no PLAN or label artifact is read."""
    require_gate_confirmation()
    raise RuntimeError("STOP: approved analysis-copy provenance is not implemented")
