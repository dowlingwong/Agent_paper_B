"""Recompute each node kit's frozen pin exactly as WorkingCopyRunner does (kit's own spec + isolation module).

Usage (from a kit root):  PYTHONPATH=src python3 compute_pins.py <kit> <node1> <node2> ...
Prints JSON {node: {pin, files, node_dir}}.
"""
import hashlib
import json
import sys
from pathlib import Path

from autoresearch.trackg.node_template import load_trackg_node_spec
from autoresearch.trackg import isolation

KIT = sys.argv[1]
ROOT = Path.cwd()
HOME = (ROOT / "third_party" / "mlgym") if KIT == "mlgym" else ROOT
out = {}
for node in sys.argv[2:]:
    spec = load_trackg_node_spec(HOME / "configs" / "trackg" / "nodes" / f"{node}.yaml")
    node_dir = HOME / "nodes" / node
    files = isolation.frozen_file_hashes(node_dir, spec.frozen_paths)
    out[node] = {
        "pin": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        "files": files,
        "node_dir": str(node_dir),
    }
print(json.dumps(out, indent=2, sort_keys=True))
