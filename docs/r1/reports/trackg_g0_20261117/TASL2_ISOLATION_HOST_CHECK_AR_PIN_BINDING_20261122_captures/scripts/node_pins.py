"""TASL-2 AR-pin host check: node pins at harness pin 2d09f9a9 (procedure section 2).

Computed with the ar-cond7a interpreter and PYTHONPATH=<harness_ar>/src, exactly as
``noise_floor.check_node_pins`` does::
    spec = load_trackg_node_spec(root / "configs/trackg/nodes/autoresearch_fixedtokens.yaml")
    pin = isolation.frozen_file_hashes(node, spec.frozen_paths)
    committed = frozen_pin_sha256(committed_view(pin))
    manifest = sha256_file(node / "representative_edits/manifest.json")

The four expected values are the census pins of the AR spec.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

EXPECTED = {
    "spec_file_sha256": "5bdce00ac51718de8547ce2d065c0e5ae83f26406ff9404f01ac42b0e2b866e7",
    "spec_raw_sha256": "5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192",
    "committed_pin_sha256": "147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc",
    "representative_edits_manifest_sha256": "55f2666a3d09aaedb8b8552aef00f8a9c27b84f1bd7df24d886904dad581e5c7",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="the harness_ar checkout")
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    root = Path(args.root)
    spec_path = root / "configs/trackg/nodes/autoresearch_fixedtokens.yaml"
    node = root / "nodes/autoresearch_fixedtokens"

    from autoresearch.trackg import isolation
    from autoresearch.trackg.node_template import load_trackg_node_spec
    from autoresearch.trackg.noise_floor import committed_view, frozen_pin_sha256, sha256_file

    spec = load_trackg_node_spec(spec_path)
    pin = isolation.frozen_file_hashes(node, spec.frozen_paths)
    committed = frozen_pin_sha256(committed_view(pin))
    manifest = sha256_file(node / "representative_edits/manifest.json")
    got = {
        "spec_file_sha256": sha256_file(spec_path),
        "spec_raw_sha256": spec.raw_sha256,
        "committed_pin_sha256": committed,
        "representative_edits_manifest_sha256": manifest,
    }
    link = node / "data"
    result = {
        "utc": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip(),
        "root": str(root),
        "interpreter": sys.executable,
        "python": sys.version.split()[0],
        "spec_path": str(spec_path),
        "node_dir": str(node),
        "spec_name": spec.name,
        "frozen_paths": list(spec.frozen_paths),
        "frozen_entries": len(pin),
        "data_link_present": link.is_symlink() or link.exists(),
        "data_link_target": os.readlink(link) if link.is_symlink() else None,
        "got": got,
        "expected": EXPECTED,
        "checks": {k: got[k] == EXPECTED[k] for k in EXPECTED},
        "condition_2_pass": all(got[k] == EXPECTED[k] for k in EXPECTED),
        "pin_entries": dict(sorted(pin.items())),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text:
        Path(args.text).write_text(
            f"root={root}\ninterpreter={sys.executable} python={sys.version.split()[0]}\n"
            f"spec={spec_path}\n"
            + "".join(f"{k}: got={got[k]} expected={EXPECTED[k]} match={got[k] == EXPECTED[k]}\n"
                      for k in EXPECTED) +
            f"frozen_entries={len(pin)} data_link_present={result['data_link_present']} "
            f"target={result['data_link_target']}\n"
            f"condition_2_pass={result['condition_2_pass']}\n",
            encoding="utf-8")
    print("RESULT " + json.dumps({"condition_2_pass": result["condition_2_pass"],
                                  "got": got, "checks": result["checks"],
                                  "frozen_entries": len(pin),
                                  "data_link_present": result["data_link_present"]}))
    return 0 if result["condition_2_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
