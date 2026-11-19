"""Patch 3: mid-run watcher bug — bash resets the special `_` variable each command, so the loop
variable became empty and the arithmetic test made the subshell exit on its first iteration
(no gpu/gpu_mid.txt was written). Use an ordinary loop variable and a precomputed elapsed value."""
from pathlib import Path

E = Path("/home/dowling/r1_engineering/u2_iso_20261119")
p = E / "scripts" / "run_node.sh"
s = p.read_text()
old = """(
  for _ in $(seq 1 1800); do
    used=$(nvidia-smi --query-gpu=uuid,memory.used --format=csv,noheader 2>/dev/null | awk -F', ' -v g="$GPU" '$1==g {print $2}' | tr -dc '0-9')
    if [ "${used:-0}" -gt 100 ] || [ "$((_ * 2))" -ge 60 ]; then
"""
new = """(
  i=0
  while [ "$i" -lt 1800 ]; do
    i=$((i + 1))
    elapsed=$((i * 2))
    used=$(nvidia-smi --query-gpu=uuid,memory.used --format=csv,noheader 2>/dev/null | awk -F', ' -v g="$GPU" '$1==g {print $2}' | tr -dc '0-9')
    if [ "${used:-0}" -gt 100 ] || [ "$elapsed" -ge 60 ]; then
"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
p.write_text(s)
print("patched mid-run watcher loop")
