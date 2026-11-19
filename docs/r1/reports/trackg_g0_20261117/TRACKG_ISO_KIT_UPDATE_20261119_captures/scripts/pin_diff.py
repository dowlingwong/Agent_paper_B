"""Compare the pre-/post-update frozen pins: which frozen file changed per node, old/new pin values."""
import json
from pathlib import Path

E = Path("/home/dowling/r1_engineering/iso_kit_update_20261119")
old, new = {}, {}
for kit in ("ar", "mlab", "mlgym"):
    old.update(json.load(open(E / f"pins/old_{kit}.json")))
    new.update(json.load(open(E / f"pins/new_{kit}.json")))
out = {}
for node in sorted(old):
    o, n = old[node]["files"], new[node]["files"]
    changed = sorted(p for p in set(o) | set(n) if o.get(p) != n.get(p))
    out[node] = {
        "old_pin": old[node]["pin"],
        "new_pin": new[node]["pin"],
        "changed_frozen_files": changed,
        "old_ar_isolated": o.get("ar_isolated.py"),
        "new_ar_isolated": n.get("ar_isolated.py"),
        "frozen_files": len(n),
    }
print(json.dumps(out, indent=2, sort_keys=True))
