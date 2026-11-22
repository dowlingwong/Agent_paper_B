"""TASL-2 AR-pin host check: the ar-cond7a environment (procedure section 3).

Records ``uv --version``, ``uv pip freeze`` of the venv, the interpreter version and torch, and compares the
freeze with the committed ``sweep2/g1b/env/ar-cond7a.freeze.txt`` staged next to this run (122 lines,
sha256 11def6ad...).  read-only: nothing is installed, upgraded or copied into the venv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

UV = "/home/dowling/.local/bin/uv"
VENV = "/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python"
EXPECTED_UV = "0.13.6"
EXPECTED_FREEZE_SHA = "11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1"
EXPECTED_FREEZE_LINES = 122
EXPECTED_PYTHON = "3.12.15"
EXPECTED_TORCH = "2.6.0+cu124"
EXPECTED_CUDA = "12.4"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(cmd: list[str], timeout: float = 180.0) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout, "stderr": out.stderr}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", required=True, help="committed ar-cond7a.freeze.txt staged for the comparison")
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--freeze-out", default="", help="where to write the raw uv pip freeze output")
    args = ap.parse_args()
    freeze_committed = Path(args.freeze)

    uv_version = run([UV, "--version"])
    freeze = run([UV, "pip", "freeze", "--python", VENV])
    freeze_raw = freeze.get("stdout", "")
    if args.freeze_out:
        Path(args.freeze_out).write_text(freeze_raw, encoding="utf-8")
    py = run([VENV, "-c", "import sys; print(sys.version)"])
    py_exe = run([VENV, "-c", "import sys, os; print('executable=' + sys.executable); "
                              "print('realpath=' + os.path.realpath(sys.executable)); "
                              "print('prefix=' + sys.prefix); print('base_prefix=' + sys.base_prefix)"])
    torch = run([VENV, "-c", "import torch; print(torch.__version__); print(torch.version.cuda); "
                             "print(torch.cuda.is_available())"])
    uv_find_15 = run([UV, "python", "find", "3.12.15"])
    uv_find_16 = run([UV, "python", "find", "3.12.16"])
    readlink = run(["readlink", "-f", VENV])

    committed_raw = freeze_committed.read_text(encoding="utf-8") if freeze_committed.is_file() else ""
    committed_sha = hashlib.sha256(committed_raw.encode("utf-8")).hexdigest() if freeze_committed.is_file() else None
    freeze_sha = sha256_text(freeze_raw)
    freeze_lines = freeze_raw.count("\n") + (0 if freeze_raw.endswith("\n") or not freeze_raw else 1)
    committed_lines = committed_raw.count("\n") + (0 if committed_raw.endswith("\n") or not committed_raw else 1)
    same_sorted = sorted(freeze_raw.splitlines()) == sorted(committed_raw.splitlines())
    same_raw = freeze_raw == committed_raw
    python_text = (py.get("stdout") or "").strip()
    torch_lines = (torch.get("stdout") or "").splitlines()
    torch_version = torch_lines[0] if torch_lines else ""
    torch_cuda = torch_lines[1] if len(torch_lines) > 1 else ""
    uv_text = (uv_version.get("stdout") or "").strip()

    checks = {
        "uv_0_13_6": uv_text.startswith("uv " + EXPECTED_UV),
        "freeze_122_lines": freeze_lines == EXPECTED_FREEZE_LINES,
        "freeze_sha_11def6ad": freeze_sha == EXPECTED_FREEZE_SHA,
        "freeze_same_sorted": same_sorted,
        "freeze_same_raw": same_raw,
        "python_3_12_15": python_text.startswith(EXPECTED_PYTHON + " ") or python_text == EXPECTED_PYTHON,
        "torch_2_6_0_cu124": torch_version == EXPECTED_TORCH,
        "torch_cuda_12_4": torch_cuda == EXPECTED_CUDA,
    }
    result = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "interpreter": VENV,
        "uv": {"version": uv_text, "rc": uv_version.get("rc"), "stderr": uv_version.get("stderr", "")},
        "freeze": {
            "sha256_raw": freeze_sha, "lines": freeze_lines,
            "committed_file": str(freeze_committed),
            "committed_sha256": committed_sha, "committed_lines": committed_lines,
            "same_raw": same_raw, "same_sorted": same_sorted,
            "uv_stderr": freeze.get("stderr", ""), "uv_rc": freeze.get("rc"),
            "first_lines": freeze_raw.splitlines()[:3], "last_lines": freeze_raw.splitlines()[-3:],
            "diff_lines": [{"uv": a, "committed": b}
                           for a, b in zip(freeze_raw.splitlines(), committed_raw.splitlines()) if a != b][:20],
        },
        "python": {"version": python_text, "detail": py_exe.get("stdout", ""),
                   "rc": py.get("rc"), "stderr": py.get("stderr", "")},
        "torch": {"version": torch_version, "cuda": torch_cuda,
                  "cuda_available": (torch_lines[2] if len(torch_lines) > 2 else ""),
                  "rc": torch.get("rc"), "stderr": torch.get("stderr", "")},
        "uv_python_find_3_12_15": {"stdout": uv_find_15.get("stdout", "").strip(),
                                   "rc": uv_find_15.get("rc")},
        "uv_python_find_3_12_16": {"stdout": uv_find_16.get("stdout", "").strip(),
                                   "rc": uv_find_16.get("rc")},
        "readlink_f_venv": (readlink.get("stdout") or "").strip(),
        "expected": {"uv": EXPECTED_UV, "freeze_sha256": EXPECTED_FREEZE_SHA,
                     "freeze_lines": EXPECTED_FREEZE_LINES, "python": EXPECTED_PYTHON,
                     "torch": EXPECTED_TORCH, "cuda": EXPECTED_CUDA},
        "checks": checks,
        "condition_3_pass": all(checks.values()),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        Path(args.text).write_text(
            f"uv={uv_text!r}\n"
            f"interpreter={VENV}\nreadlink_f={result['readlink_f_venv']}\n"
            f"python={python_text!r}\n{result['python']['detail']}"
            f"torch={torch_version!r} cuda={torch_cuda!r} available={result['torch']['cuda_available']!r}\n"
            f"freeze_sha256={freeze_sha}\nfreeze_lines={freeze_lines}\n"
            f"committed_sha256={committed_sha}\ncommitted_lines={committed_lines}\n"
            f"freeze_same_raw={same_raw} freeze_same_sorted={same_sorted}\n"
            + "".join(f"{k}={v}\n" for k, v in checks.items()) +
            f"condition_3_pass={result['condition_3_pass']}\n",
            encoding="utf-8")
    print("RESULT " + json.dumps({"condition_3_pass": result["condition_3_pass"],
                                  "checks": checks, "uv": uv_text,
                                  "freeze_sha256": freeze_sha, "freeze_lines": freeze_lines,
                                  "python": python_text, "torch": torch_version,
                                  "torch_cuda": torch_cuda,
                                  "readlink_f": result["readlink_f_venv"]}))
    return 0 if result["condition_3_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
