"""R1-T1-HOST-TASL condition 7: compare the pre/post fingerprints of the Track P attempt-1 archive + lease log.

Read-only over the manifests written by ``fingerprint_attempt1.sh``; writes ``attempt1_compare.{json,txt}``.
The archive/lease log count as untouched only when every recorded stat line, the metadata tree hash and the
full-content aggregate hash are byte-identical between the before and after passes.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def read_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--captures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    cap = Path(args.captures)

    # fingerprint_attempt1.sh writes some manifests with a .txt suffix
    field_files = {"stat": "stat.txt", "tree.sha256": "tree.sha256",
                   "content.sha256": "content.sha256", "nentries": "nentries.txt",
                   "nfiles": "nfiles.txt", "bytes": "bytes.txt"}
    fields = tuple(field_files)
    result: dict = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "archive": "/home/dowling/r1_trackp/runs/p3a_operator_20261027",
                    "files": {}, "differences": []}
    for phase in ("before", "after"):
        result["files"][phase] = {}
        for field in fields:
            path = cap / f"attempt1_{phase}.{field_files[field]}"
            result["files"][phase][field] = read_text(path).strip()
    for field in fields:
        if result["files"]["before"][field] != result["files"]["after"][field]:
            result["differences"].append(field)
    result["identical"] = not result["differences"]
    result["untouched"] = bool(result["identical"])
    result["tree_sha256"] = result["files"]["before"]["tree.sha256"]
    result["content_sha256"] = result["files"]["before"]["content.sha256"]
    result["entries"] = result["files"]["before"]["nentries"]
    result["files_count"] = result["files"]["before"]["nfiles"]
    result["bytes"] = result["files"]["before"]["bytes"]
    result["stat_before"] = result["files"]["before"]["stat"]
    result["stat_after"] = result["files"]["after"]["stat"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text:
        Path(args.text).write_text(
            f"attempt1_archive={result['archive']}\n"
            f"identical={result['identical']} differences={result['differences'] or 'none'}\n"
            f"entries={result['entries']} files={result['files_count']} bytes={result['bytes']}\n"
            f"tree_sha256={result['tree_sha256']}\n"
            f"content_sha256={result['content_sha256']}\n"
            f"--- stat before\n{result['stat_before']}\n"
            f"--- stat after\n{result['stat_after']}\n",
            encoding="utf-8")
    print("RESULT " + json.dumps({"untouched": result["untouched"],
                                  "differences": result["differences"],
                                  "tree_sha256": result["tree_sha256"],
                                  "content_sha256": result["content_sha256"]}))
    return 0 if result["untouched"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
