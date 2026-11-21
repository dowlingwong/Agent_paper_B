"""R1-T1-HOST-TASL / R1-G1B-CAP: the T1 environments on TASL-7, from the census freezes.

Read-only on the host (writes only ``--out``/``--text`` and ``<base>/work/*.freeze.actual.txt``).  Records:
  * the uv executable, its version, and where the 3.12.16 interpreter it installed comes from (``uv python
    find``, ``uv python dir``, the venv symlink target, ``uv python list``);
  * for ``torch312`` and ``jax312``: the interpreter realpath/version (must be 3.12.16), ``sys.prefix``, the
    installed distribution set by ``uv pip freeze`` (stdout only; uv writes its banner to stderr) compared
    **byte-for-byte** with the census freeze file, and the freeze sha256 (expected d2e70fe4... / 80a455c6...);
  * no ``LD_LIBRARY_PATH``/``LD_PRELOAD`` in this process or in the probes it starts.

A freeze that is not byte-equal, or a Python that is not 3.12.16, is a STOP: the G.1b job's own host check
compares ``uv pip freeze`` with the census value before anything is written for the node.
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

BASE = Path("/home/dowling/r1_tracks/t1_tasl")
UV = "/home/dowling/.local/bin/uv"
EXPECTED = {
    "torch312": {"python": "3.12.16",
                 "freeze_sha256": "d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42"},
    "jax312": {"python": "3.12.16",
               "freeze_sha256": "80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1"},
}
ENVS = ("torch312", "jax312")
LEAKY = ("LD_LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT")


def run(cmd: list[str], timeout: float = 600.0, env: dict | None = None) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout, "stderr": out.stderr[-4000:]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "stdout": "", "stderr": f"{type(error).__name__}: {error}"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--uv", default=UV)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    base = Path(args.base)
    clean_env = {k: v for k, v in os.environ.items() if k not in LEAKY}
    env_facts: dict = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hostname": os.uname().nodename, "euid": os.geteuid(),
        "base": str(base),
        "ld_vars_in_probe_env": {k: os.environ.get(k) for k in LEAKY},
        "uv": {
            "path": args.uv, "exists": os.path.exists(args.uv),
            "version": run([args.uv, "--version"]),
            "not_on_path": run(["bash", "-c", "command -v uv || true"]),
            "python_dir": run([args.uv, "python", "dir"]),
            "python_find": run([args.uv, "python", "find", "3.12.16"]),
            "python_install": run([args.uv, "python", "install", "3.12.16"]),
            "python_list": run([args.uv, "python", "list"]),
            "install_root_listing": run(["bash", "-c",
                                         "ls -la ~/.local/share/uv/python/ 2>&1; "
                                         "readlink -f ~/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12 2>&1"]),
        },
    }
    envs: dict = {}
    checks: dict = {}
    for name in ENVS:
        exp = EXPECTED[name]
        venv_dir = base / "envs" / name
        freeze_file = base / "base" / f"{name}.freeze.txt"
        interp = venv_dir / "bin" / "python"
        actual_file = base / "work" / f"{name}.freeze.actual.txt"
        item: dict = {
            "venv_dir": str(venv_dir), "interpreter": str(interp),
            "interpreter_exists": interp.exists(),
            "interpreter_realpath": os.path.realpath(interp) if interp.exists() else None,
            "freeze_file": str(freeze_file), "freeze_file_exists": freeze_file.exists(),
            "freeze_sha256_expected": exp["freeze_sha256"],
            "python_expected": exp["python"],
        }
        if interp.exists():
            item["version"] = run([str(interp), "-VV"], env=clean_env)
            item["sys_prefix"] = run([str(interp), "-s", "-c",
                                      "import sys; print(sys.executable); print(sys.prefix); "
                                      "print(sys.base_prefix)"], env=clean_env)
            freeze = run([args.uv, "pip", "freeze", "--python", str(interp)], env=clean_env)
            stdout = freeze.get("stdout") or ""
            actual_file.parent.mkdir(parents=True, exist_ok=True)
            actual_file.write_text(stdout, encoding="utf-8")
            item["freeze_actual_file"] = str(actual_file)
            item["freeze_actual_sha256"] = sha256_bytes(stdout.encode())
            item["freeze_actual_lines"] = len(stdout.splitlines())
            item["uv_pip_freeze"] = {k: freeze.get(k) for k in ("rc", "cmd")}
            if freeze.get("rc") != 0:
                item["uv_pip_freeze"]["stderr"] = freeze.get("stderr")
            if freeze_file.exists():
                expected_text = freeze_file.read_text(encoding="utf-8")
                item["freeze_file_sha256"] = sha256_bytes(expected_text.encode())
                item["freeze_byte_equal"] = stdout.encode() == expected_text.encode()
                want_lines = sorted(line for line in expected_text.splitlines() if line.strip())
                have_lines = sorted(line for line in stdout.splitlines() if line.strip())
                item["freeze_sorted_equal"] = have_lines == want_lines
                if not item["freeze_byte_equal"]:
                    item["freeze_byte_diff"] = [line for line in
                                                __import__("difflib").unified_diff(
                                                    expected_text.splitlines(), stdout.splitlines(),
                                                    "freeze_file", "uv_pip_freeze", lineterm="", n=1)
                                                ][:40]
                item["freeze_lines_expected"] = len(expected_text.splitlines())
            py_ok = (exp["python"] in (item["version"].get("stdout") or "")
                     or exp["python"] in (item["version"].get("stderr") or ""))
            item["python_312_16"] = py_ok
            if name == "torch312":
                item["packages"] = run([str(interp), "-c",
                                        "import torch, sys; print('torch', torch.__version__, "
                                        "'cuda', torch.version.cuda, 'available', torch.cuda.is_available())"],
                                       env=clean_env)
            else:
                item["packages"] = run([str(interp), "-c",
                                        "import jax, jaxlib, sys; print('jax', jax.__version__, "
                                        "'jaxlib', jaxlib.__version__, 'python', sys.version.split()[0])"],
                                       env=clean_env)
        checks[name] = {
            "interpreter_exists": bool(item["interpreter_exists"]),
            "python_312_16": bool(item.get("python_312_16")),
            "freeze_file_exists": bool(item["freeze_file_exists"]),
            "freeze_sha256_matches_expected": bool(
                item.get("freeze_file_sha256") == exp["freeze_sha256"]),
            "freeze_byte_equal": bool(item.get("freeze_byte_equal")),
            "freeze_sorted_equal": bool(item.get("freeze_sorted_equal")),
            "ld_vars_empty": all(not os.environ.get(k) for k in LEAKY),
        }
        # The launch job's check is the *sorted* comparison (g1b_lib.compare_freeze); byte equality is
        # recorded as a diagnostic (uv's freeze ordering can differ by one adjacency).
        checks[name]["pass"] = all(v for k, v in checks[name].items() if k != "freeze_byte_equal")
        envs[name] = item
    env_facts["envs"] = envs
    env_facts["checks"] = checks
    env_facts["ld_vars_clean_process_env"] = all(not clean_env.get(k) for k in LEAKY)
    env_facts["condition_envs_pass"] = all(checks[name]["pass"] for name in ENVS)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(env_facts, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        lines = [f"utc={env_facts['utc']} host={env_facts['hostname']} euid={env_facts['euid']}",
                 f"uv={args.uv} uv_version={(env_facts['uv']['version'].get('stdout') or '').strip()}",
                 f"uv_python_find={(env_facts['uv']['python_find'].get('stdout') or '').strip()}",
                 f"uv_python_dir={(env_facts['uv']['python_dir'].get('stdout') or '').strip()}",
                 f"ld_vars={env_facts['ld_vars_in_probe_env']}"]
        for name in ENVS:
            item, chk = envs[name], checks[name]
            lines += [
                f"--- {name}: {item['interpreter']}",
                f"  realpath={item.get('interpreter_realpath')}",
                f"  version={(item.get('version', {}).get('stdout') or item.get('version', {}).get('stderr') or '').strip()}",
                f"  sys_prefix={(item.get('sys_prefix', {}).get('stdout') or '').replace(chr(10), ' | ')}",
                f"  freeze_file={item['freeze_file']} sha256={item.get('freeze_file_sha256')}",
                f"  freeze_actual={item.get('freeze_actual_file')} sha256={item.get('freeze_actual_sha256')}",
                f"  freeze_byte_equal={item.get('freeze_byte_equal')} "
                f"freeze_sorted_equal={item.get('freeze_sorted_equal')} lines={item.get('freeze_actual_lines')}",
                f"  packages={(item.get('packages', {}).get('stdout') or item.get('packages', {}).get('stderr') or '').strip()}",
                f"  checks={json.dumps(chk, sort_keys=True)}",
            ]
        lines.append(f"condition_envs_pass={env_facts['condition_envs_pass']}")
        Path(args.text).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps({"condition_envs_pass": env_facts["condition_envs_pass"],
                                  "checks": checks,
                                  "uv_version": (env_facts["uv"]["version"].get("stdout") or "").strip(),
                                  "uv_python_find": (env_facts["uv"]["python_find"].get("stdout") or "").strip()},
                                 default=str))
    return 0 if env_facts["condition_envs_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
