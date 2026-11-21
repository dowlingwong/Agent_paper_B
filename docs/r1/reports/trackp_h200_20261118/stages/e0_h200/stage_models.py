"""Materialize the committed model registry pins in HTCondor job scratch."""
import hashlib
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

import yaml


registry = yaml.safe_load(Path("registry.yaml").read_bytes())["models"]
for key in sys.argv[1:]:
    item = registry[key]
    target = Path("models") / key
    target.mkdir(parents=True)
    for name, pin in sorted(item["files"].items()):
        if Path(name).name != name or name in {".", ".."}:
            raise SystemExit(f"STOP: unexpected registry file name {name}")
        dest = target / name
        url = f"https://huggingface.co/{item['repo']}/resolve/{item['revision']}/{quote(name, safe='')}"
        with dest.open("xb") as out:
            subprocess.run(
                ["curl", "--fail", "--silent", "--show-error", "--location", "--retry", "2",
                 "--max-time", "1200", url],
                stdout=out, check=True,
            )
        with dest.open("rb") as inp:
            digest = hashlib.file_digest(inp, "sha256").hexdigest()
        if dest.stat().st_size != pin["size"] or digest != pin["sha256"]:
            raise SystemExit(f"STOP: registry size or SHA mismatch for {key}/{name}")
        print(f"{digest}  {key}/{name}", flush=True)
