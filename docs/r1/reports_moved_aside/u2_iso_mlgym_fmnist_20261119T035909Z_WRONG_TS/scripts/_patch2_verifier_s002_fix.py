"""Patch 2: verifier s002 special-case + mid-run watcher trigger for remaining U2 nodes."""
import os
from pathlib import Path

E = Path("/home/dowling/r1_engineering/u2_iso_20261119")

# --- verifier: the deliberately divergent s002 must not be checked as outcome kind ok ---
v = E / "scripts" / "verify_u2_records.py"
s = v.read_text()
old = (
    '        if rid == "s002":\n'
    '            checks["outcome divergent/non_finite_loss"] = (\n'
)
new = (
    '        if rid == "s002":\n'
    '            # s002 is the deliberately broken diff: divergent/non_finite_loss, no value\n'
    '            checks.pop("outcome kind ok", None)\n'
    '            checks.pop("outcome.value present", None)\n'
    '            checks["outcome divergent/non_finite_loss"] = (\n'
)
assert s.count(old) == 1, s.count(old)
v.write_text(s.replace(old, new))
print("patched verify_u2_records.py (s002)")

# --- runner: mid-run census watcher triggers on any GPU use, with a 60 s fallback ---
r = E / "scripts" / "run_node.sh"
s = r.read_text()
old = '    if [ "${used:-0}" -gt 1000 ]; then\n'
new = '    if [ "${used:-0}" -gt 100 ] || [ "$((_ * 2))" -ge 60 ]; then\n'
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
r.write_text(s)
print("patched run_node.sh (mid-run watcher: >100 MiB or 60 s fallback)")
for line in s.splitlines():
    if "-gt 100" in line:
        print("  ", line)
