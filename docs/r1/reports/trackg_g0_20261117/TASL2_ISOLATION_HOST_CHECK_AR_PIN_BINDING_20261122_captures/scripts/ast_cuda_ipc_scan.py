"""TASL-2 AR-pin host check, supplementary AST CUDA-IPC scan at harness pin 2d09f9a9.

Procedure section 5: "§3 item 7 (CUDA IPC) is untested on TASL-2; option A of ``autoresearch_fixedtokens`` uses
no CUDA IPC. U2 confirmed this with an AST scan reporting no hits in ``run_fixed_budget.py`` and ``ar_worker.py``;
repeat that scan at the pin and record it."

For each target file this parses the module and walks every ``ast.Call`` node, resolving the callee name for
``Name`` and ``Attribute`` calls.  Any call whose name is one of ``cuda_share``, ``cuda_open``, ``_new_shared_cuda``
or ``bind_cuda`` is a hit.  Non-call references (imports, bare attribute reads) are recorded separately as
informational only.  The file sha256 binds the scan to the exact node files at the pin.

The helper *definitions* in ``ar_isolated.py`` (kept for compatibility) are reported for context, but the
option-A path under test is ``run_fixed_budget.py``/``ar_worker.py``; a call site there is a FAIL.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import time
from pathlib import Path

FORBIDDEN = ("cuda_share", "cuda_open", "_new_shared_cuda", "bind_cuda")
PRIMARY = ("run_fixed_budget.py", "ar_worker.py")
CONTEXT = ("ar_isolated.py",)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def callee_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def scan_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    call_hits: list[dict] = []
    refs: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = callee_name(node.func)
            if name in FORBIDDEN:
                call_hits.append({"name": name, "lineno": node.lineno,
                                  "col": node.col_offset,
                                  "source_line": text.splitlines()[node.lineno - 1].strip()[:200]})
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN:
            refs.append({"kind": "attribute", "name": node.attr, "lineno": node.lineno})
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN:
            refs.append({"kind": "name", "name": node.id, "lineno": node.lineno})
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name in FORBIDDEN:
                    refs.append({"kind": "import", "name": alias.name, "lineno": node.lineno})
    defs = [{"name": node.name, "lineno": node.lineno}
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FORBIDDEN]
    return {"path": str(path), "sha256": sha256_file(path), "call_hits": call_hits,
            "non_call_references": refs, "function_definitions": defs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-dir", required=True, help="the autoresearch_fixedtokens node directory at the pin")
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    node_dir = Path(args.node_dir)
    result = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "node_dir": str(node_dir),
        "forbidden_names": list(FORBIDDEN),
        "primary_files": {}, "context_files": {},
    }
    for name in PRIMARY:
        path = node_dir / name
        result["primary_files"][name] = scan_file(path) if path.is_file() else {"path": str(path),
                                                                                 "missing": True}
    for name in CONTEXT:
        path = node_dir / name
        if path.is_file():
            result["context_files"][name] = scan_file(path)
    primary_hits = {name: item.get("call_hits", []) for name, item in result["primary_files"].items()}
    result["primary_call_hit_count"] = sum(len(v) for v in primary_hits.values())
    result["condition_scan_pass"] = result["primary_call_hit_count"] == 0
    result["note"] = ("ar_isolated.py keeps cuda_share/cuda_open helper definitions for compatibility; the "
                      "option-A path (run_fixed_budget.py/ar_worker.py) must not call them.")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        lines = [f"utc={result['utc']} node_dir={node_dir}",
                 f"forbidden_names={list(FORBIDDEN)}"]
        for name, item in result["primary_files"].items():
            lines.append(f"--- primary {name}: sha256={item.get('sha256')} "
                         f"call_hits={item.get('call_hits')} refs={item.get('non_call_references')}")
        for name, item in result["context_files"].items():
            lines.append(f"--- context {name}: sha256={item.get('sha256')} "
                         f"call_hits={item.get('call_hits')} "
                         f"definitions={item.get('function_definitions')}")
        lines.append(f"primary_call_hit_count={result['primary_call_hit_count']} "
                     f"condition_scan_pass={result['condition_scan_pass']}")
        Path(args.text).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps({"condition_scan_pass": result["condition_scan_pass"],
                                  "primary_call_hit_count": result["primary_call_hit_count"],
                                  "primary": {n: {"sha256": i.get("sha256"),
                                                  "call_hits": i.get("call_hits")}
                                              for n, i in result["primary_files"].items()},
                                  "context_definitions": {n: i.get("function_definitions")
                                                          for n, i in result["context_files"].items()}},
                                 default=str))
    return 0 if result["condition_scan_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
