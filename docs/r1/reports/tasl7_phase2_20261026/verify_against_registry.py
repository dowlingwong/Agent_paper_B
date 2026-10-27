"""Re-hash local model files against the committed registry.yaml (sha256 and size per file; no extra files)."""
import hashlib, sys, yaml
from pathlib import Path
reg = yaml.safe_load(open(sys.argv[1]))["models"]; models = Path(sys.argv[2]); only = sys.argv[3:] or list(reg)
bad = 0
for key in only:
    e = reg[key]
    d = Path(e.get("local_path") or "")
    if not d.is_dir():
        cands = [p for p in models.iterdir() if p.name.startswith(e["repo"].replace("/", "__") + "@")]
        d = cands[0]
    local = {str(p.relative_to(d)) for p in d.rglob("*") if p.is_file() and ".cache" not in p.parts}
    n = 0
    for f, rec in e["files"].items():
        p = d / f
        h = hashlib.sha256(); [h.update(c) for c in iter(lambda fh=open(p, "rb"): fh.read(1 << 22), b"")]
        ok = h.hexdigest() == rec["sha256"] and p.stat().st_size == rec["size"]
        n += ok; bad += not ok
        if not ok: print("MISMATCH", key, f)
    extra = local - set(e["files"])
    if extra: print("EXTRA", key, sorted(extra)); bad += len(extra)
    print(f"{key}: {n}/{len(e['files'])} files match ({e['repo']}@{e['revision'][:12]}) dir={d}")
print("ALL OK" if not bad else f"{bad} problems"); sys.exit(1 if bad else 0)
