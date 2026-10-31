"""Read-only rehash of the 22 pinned Track X GGUF files; no writes on host."""
import hashlib
import json
import os
import sys
from pathlib import Path

root = Path("/home/dowling/exam-x/work/agent_paper_B")
registry = json.loads((root / "r1/exam/registry.yaml").read_text())
models = [x for x in registry["candidates"] + registry["sensitivities"]
          if x.get("quant_source", {}).get("size_bytes")]
if len(models) != 22 or len({x["id"] for x in models}) != 22:
    raise SystemExit("STOP: unexpected registry size or duplicate IDs")
for model in models:
    path = Path(model["runtime"]["model_path"])
    expected = model["quant_source"]
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        before = os.fstat(fd)
        if before.st_size != expected["size_bytes"]:
            raise ValueError("size mismatch")
        sha = hashlib.sha256()
        with os.fdopen(fd, "rb") as stream:
            while chunk := stream.read(8 * 1024 * 1024):
                sha.update(chunk)
            after = os.fstat(stream.fileno())
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, x) != getattr(after, x) for x in fields):
            raise ValueError("file changed during reading")
        result = {"id": model["id"], "path": str(path), "size": before.st_size,
                  "sha256": sha.hexdigest(), "expected": expected["sha256"],
                  "stat": {x: getattr(before, x) for x in fields}}
        result["match"] = result["sha256"] == result["expected"]
        print(json.dumps(result, sort_keys=True), flush=True)
        if not result["match"]:
            raise ValueError("hash mismatch")
    except Exception as exc:
        print(json.dumps({"id": model["id"], "stop": str(exc)}), flush=True)
        sys.exit(1)
print(json.dumps({"event": "complete", "count": len(models)}), flush=True)
