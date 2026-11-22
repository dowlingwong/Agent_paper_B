"""TASL-2 AR-pin host check: ar-cond7a interpreter evidence before/after (read-only).

The lead's authorised R1-G1B-AR-PY option-A fix re-pointed the venv's ``bin/python``, ``bin/python3`` and
``bin/python3.12`` symlinks at the versioned uv CPython
``/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12``.  This script records the
target chain, the resolved interpreter's sha256 and size, ``python -V``, ``torch``, the committed-shape freeze
sha256 and the pyvenv.cfg, so the check can show the same interpreter before and after and that the venv was not
edited (no install, upgrade or copy).  Writes only its own outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

VENV = Path("/home/dowling/r1_trackp/venvs/ar-cond7a")
VENV_PY = VENV / "bin" / "python"
UV = "/home/dowling/.local/bin/uv"
EXPECTED_INTERPRETER_SHA = "0a97d28d3635c7dfd143de6d00b09c0cb382249c020b28ee33fb4002db1efb9c"
EXPECTED_INTERPRETER_BYTES = 31_027_176
EXPECTED_PYTHON = "3.12.15"
EXPECTED_FREEZE_SHA = "11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1"


def run(cmd: list[str], timeout: float = 180.0) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout, "stderr": out.stderr}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot() -> dict:
    links = {}
    for name in ("python", "python3", "python3.12"):
        path = VENV / "bin" / name
        links[name] = {"readlink": os.readlink(path) if path.is_symlink() else None,
                       "resolved": str(path.resolve()) if path.exists() else None,
                       "exists": path.exists(), "is_symlink": path.is_symlink()}
    resolved = VENV_PY.resolve()
    freeze = run([UV, "pip", "freeze", "--python", str(VENV_PY)])
    freeze_raw = freeze.get("stdout", "")
    pyvenv = (VENV / "pyvenv.cfg")
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "venv": str(VENV),
        "interpreter": str(VENV_PY),
        "links": links,
        "resolved_interpreter": str(resolved),
        "interpreter_sha256": sha256_file(resolved) if resolved.is_file() else None,
        "interpreter_bytes": resolved.stat().st_size if resolved.is_file() else None,
        "python_version": (run([str(VENV_PY), "-V"]).get("stdout") or "").strip(),
        "torch": (run([str(VENV_PY), "-c",
                       "import torch; print(torch.__version__, torch.version.cuda, "
                       "torch.cuda.is_available())"]).get("stdout") or "").strip(),
        "freeze_sha256": hashlib.sha256(freeze_raw.encode("utf-8")).hexdigest(),
        "freeze_lines": len(freeze_raw.splitlines()),
        "pyvenv_cfg_path": str(pyvenv),
        "pyvenv_cfg_sha256": sha256_file(pyvenv) if pyvenv.is_file() else None,
        "pyvenv_cfg": pyvenv.read_text(errors="replace") if pyvenv.is_file() else None,
        "uv_version": (run([UV, "--version"]).get("stdout") or "").strip(),
        "site_packages_dir": str(VENV / "lib" / "python3.12" / "site-packages"),
        "site_packages_exists": (VENV / "lib" / "python3.12" / "site-packages").is_dir(),
        "expected": {
            "resolved_interpreter_suffix": "cpython-3.12.15-linux-x86_64-gnu/bin/python3.12",
            "interpreter_sha256": EXPECTED_INTERPRETER_SHA,
            "interpreter_bytes": EXPECTED_INTERPRETER_BYTES,
            "python": EXPECTED_PYTHON,
            "freeze_sha256": EXPECTED_FREEZE_SHA,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    snap = snapshot()
    snap["tag"] = args.tag
    checks = {
        "python_3_12_15": EXPECTED_PYTHON in (snap["python_version"] or ""),
        "interpreter_sha_0a97d28d": snap["interpreter_sha256"] == EXPECTED_INTERPRETER_SHA,
        "interpreter_bytes_31027176": snap["interpreter_bytes"] == EXPECTED_INTERPRETER_BYTES,
        "resolved_versioned_3_12_15": "cpython-3.12.15-linux-x86_64-gnu" in (snap["resolved_interpreter"] or ""),
        "freeze_sha_11def6ad": snap["freeze_sha256"] == EXPECTED_FREEZE_SHA,
    }
    snap["checks"] = checks
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        Path(args.text).write_text(
            f"tag={args.tag} utc={snap['utc']} venv={snap['venv']}\n"
            f"resolved_interpreter={snap['resolved_interpreter']}\n"
            f"interpreter_sha256={snap['interpreter_sha256']} bytes={snap['interpreter_bytes']}\n"
            f"python={snap['python_version']!r} torch={snap['torch']!r}\n"
            f"freeze_sha256={snap['freeze_sha256']} lines={snap['freeze_lines']}\n"
            f"pyvenv_cfg_sha256={snap['pyvenv_cfg_sha256']}\n"
            f"links={json.dumps(snap['links'], default=str)}\n"
            + "".join(f"{k}={v}\n" for k, v in checks.items()),
            encoding="utf-8")
    print("RESULT " + json.dumps({"tag": args.tag, "checks": checks,
                                  "resolved": snap["resolved_interpreter"],
                                  "sha256": snap["interpreter_sha256"],
                                  "bytes": snap["interpreter_bytes"],
                                  "python": snap["python_version"],
                                  "freeze_sha256": snap["freeze_sha256"]}, default=str))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
