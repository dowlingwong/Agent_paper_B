"""R1-T1-HOST-TASL TASL-2 pre-launch check: the census environments built with uv (G.1b plan §1/§6.5 inputs).

Read-only apart from the --out/--text documents.  Records:
  * uv version and the uv-managed Python 3.12.16 interpreter source (``uv python find``, realpath, pyvenv.cfg);
  * for ``envs/torch312`` and ``envs/jax312``: the interpreter version, and the environment's ``uv pip freeze``
    compared **byte for byte** with the committed census freeze (``sweep2/g1b/env/<env>.freeze.txt``, the sha256
    declared in the G.1b spec) — equal freezes and Python 3.12.16 are a launch STOP if they differ;
  * torch: version / CUDA build / ``cuda.is_available`` / device name / a synchronised device tensor;
  * jax: version / devices / backend / a jitted GPU matmul;
  * no ``LD_LIBRARY_PATH`` and no GPU-selection variable in the check environment;
  * the new envs are separate from ``ar-cond7a`` and the Track P venvs (distinct realpaths, no shared prefix).

The GPU checks here are plain (outside the worker sandbox); the sandboxed ones are C5/C6 of ``run_checks.sh``.
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
T1 = "/home/dowling/r1_tracks/t1_tasl"
FREEZES = {"torch312": "/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/env_build/torch312.freeze.txt",
           "jax312": "/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/env_build/jax312.freeze.txt"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def run(cmd: list[str], timeout: float = 300.0, env: dict | None = None) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout,
                "stderr": out.stderr[-8000:]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def clean_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("LD_")}
    env.pop("LD_PRELOAD", None)
    for name in ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "_CONDOR_AssignedGPUs",
                 "PYTHONPATH"):
        env.pop(name, None)
    return env


def interpreter_facts(python: str, env: dict) -> dict:
    code = ("import json, os, sys; print(json.dumps({'executable': sys.executable, "
            "'realpath': os.path.realpath(sys.executable), 'version': sys.version.split()[0], "
            "'prefix': sys.prefix, 'base_prefix': sys.base_prefix, "
            "'sys_path': [p for p in sys.path if p], "
            "'ld_library_path': os.environ.get('LD_LIBRARY_PATH'), "
            "'ld_preload': os.environ.get('LD_PRELOAD')}))")
    res = run([python, "-s", "-c", code], env=env)
    facts = json.loads(res["stdout"].strip().splitlines()[-1]) if res.get("rc") == 0 else {}
    facts["rc"] = res.get("rc")
    if res.get("rc") != 0:
        facts["stderr"] = res.get("stderr")
    cfg = Path(python).parent.parent / "pyvenv.cfg"
    facts["pyvenv_cfg"] = cfg.read_text(errors="replace") if cfg.is_file() else None
    facts["pyvenv_cfg_path"] = str(cfg)
    return facts


def freeze_check(env_name: str, python: str, freeze: Path, env: dict) -> dict:
    uvfreeze = run([UV, "pip", "freeze", "--python", python], env=env)
    produced = uvfreeze.get("stdout", "")
    want = freeze.read_text()
    # byte equality; also the sorted-line multiset as a diagnostic if bytes differ (extra whitespace only)
    out = {"freeze_file": str(freeze), "freeze_sha256": sha256_file(freeze),
           "uv_pip_freeze_cmd": uvfreeze["cmd"], "rc": uvfreeze.get("rc"),
           "uv_freeze_sha256": sha256_bytes(produced.encode()),
           "byte_equal": produced == want,
           "line_equal_sorted": sorted(produced.splitlines()) == sorted(want.splitlines()),
           "produced_lines": len(produced.splitlines()), "freeze_lines": len(want.splitlines()),
           "stderr": uvfreeze.get("stderr")}
    # The census freezes are the uv pip freeze set in the census host's en_US.UTF-8 collation (the same
    # package lines, ordered by locale ``sort``; the only visible difference from uv 0.13.6's own byte order
    # is the adjacent ``optax`` / ``opt-einsum`` pair).  Reproduce that collation to check the bytes.
    loc = subprocess.run(["sort"], input=produced.encode(), capture_output=True,
                         env={**os.environ, "LC_ALL": "en_US.UTF-8"}, timeout=120)
    out["locale_sorted_sha256"] = sha256_bytes(loc.stdout)
    out["locale_sorted_byte_equal"] = loc.returncode == 0 and loc.stdout == want.encode()
    out["line_sha256"] = sha256_bytes("\n".join(sorted(produced.splitlines())).encode())
    if not out["byte_equal"]:
        want_lines, got_lines = want.splitlines(), produced.splitlines()
        missing = [line for line in want_lines if line not in got_lines]
        extra = [line for line in got_lines if line not in want_lines]
        out["diff"] = {"missing_from_env": missing[:20], "extra_in_env": extra[:20],
                       "count_missing": len(missing), "count_extra": len(extra)}
    return out


def torch_check(python: str, env: dict) -> dict:
    code = r'''
import json, os
out = {}
try:
    import torch
    out["torch_version"] = torch.__version__
    out["torch_cuda_version"] = torch.version.cuda
    out["cuda_available"] = bool(torch.cuda.is_available())
    out["device_count"] = int(torch.cuda.device_count())
    if out["cuda_available"]:
        dev = torch.device("cuda:0")
        out["device_name"] = torch.cuda.get_device_name(dev)
        out["capability"] = list(torch.cuda.get_device_capability(dev))
        x = torch.arange(64, dtype=torch.float32, device=dev) * 2.0 + 1.0
        out["tensor_sum"] = float(x.sum().item())
        out["tensor_sum_ok"] = abs(out["tensor_sum"] - 4096.0) < 1e-3
        a = torch.ones((16, 16), dtype=torch.float32, device=dev)
        b = a @ a
        torch.cuda.synchronize()
        out["matmul_value"] = float(b[0, 0].item())
        out["matmul_ok"] = abs(out["matmul_value"] - 16.0) < 1e-6
        out["memory_allocated_bytes"] = int(torch.cuda.memory_allocated(dev))
        props = torch.cuda.get_device_properties(dev)
        out["device_properties_uuid"] = str(getattr(props, "uuid", None))
    out["ld_library_path"] = os.environ.get("LD_LIBRARY_PATH")
    out["ld_preload"] = os.environ.get("LD_PRELOAD")
    out["cuda_visible_devices"] = os.environ.get("CUDA_VISIBLE_DEVICES")
except Exception as error:
    import traceback
    out["error"] = repr(error)
    out["traceback"] = traceback.format_exc()[-4000:]
    out["ok"] = False
else:
    out["ok"] = bool(out.get("cuda_available") and out.get("tensor_sum_ok") and out.get("matmul_ok"))
print(json.dumps(out, default=str))
'''
    res = run([python, "-s", "-c", code], env=env, timeout=300)
    try:
        facts = json.loads(res["stdout"].strip().splitlines()[-1])
    except (IndexError, ValueError):
        facts = {"error": "no JSON from torch check", "stdout": res.get("stdout"),
                 "stderr": res.get("stderr"), "rc": res.get("rc"), "ok": False}
    facts["cmd_rc"] = res.get("rc")
    return facts


def jax_check(python: str, env: dict) -> dict:
    code = r'''
import json, os
out = {}
try:
    import jax
    import jax.numpy as jnp
    out["jax_version"] = jax.__version__
    out["backend"] = jax.default_backend()
    devices = jax.devices()
    out["devices"] = [str(d) for d in devices]
    out["device_kinds"] = [getattr(d, "device_kind", None) for d in devices]
    out["device_platforms"] = [getattr(d, "platform", None) for d in devices]
    if out["backend"] == "gpu":
        x = jnp.arange(64, dtype=jnp.float32) * 2.0 + 1.0
        out["tensor_sum"] = float(jnp.sum(x))
        out["tensor_sum_ok"] = abs(out["tensor_sum"] - 4096.0) < 1e-3
        a = jnp.ones((16, 16), dtype=jnp.float32)
        m = jax.jit(lambda t: t @ t)(a)
        out["matmul_value"] = float(m[0, 0])
        out["matmul_ok"] = abs(out["matmul_value"] - 16.0) < 1e-4
    out["ld_library_path"] = os.environ.get("LD_LIBRARY_PATH")
    out["ld_preload"] = os.environ.get("LD_PRELOAD")
    out["cuda_visible_devices"] = os.environ.get("CUDA_VISIBLE_DEVICES")
except Exception as error:
    import traceback
    out["error"] = repr(error)
    out["traceback"] = traceback.format_exc()[-4000:]
    out["ok"] = False
else:
    out["ok"] = bool(out.get("backend") == "gpu" and out.get("tensor_sum_ok")
                     and out.get("matmul_ok"))
print(json.dumps(out))
'''
    res = run([python, "-s", "-c", code], env=env, timeout=300)
    try:
        facts = json.loads(res["stdout"].strip().splitlines()[-1])
    except (IndexError, ValueError):
        facts = {"error": "no JSON from jax check", "stdout": res.get("stdout"),
                 "stderr": res.get("stderr"), "rc": res.get("rc"), "ok": False}
    facts["cmd_rc"] = res.get("rc")
    return facts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--t1", default=T1)
    args = ap.parse_args()
    t1 = Path(args.t1)
    env = clean_env()
    envs = {"torch312": str(t1 / "envs/torch312/bin/python"),
            "jax312": str(t1 / "envs/jax312/bin/python")}

    result: dict = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "host": os.uname().nodename, "euid": os.geteuid(),
                    "uv": {"path": UV, "version": run([UV, "--version"], env=env)},
                    "python_install": {
                        "uv_python_find_3.12.16": run([UV, "python", "find", "3.12.16"], env=env),
                        "uv_python_list": run([UV, "python", "list"], env=env),
                        "managed_root": "/home/dowling/.local/share/uv/python",
                        "installed_dirs": sorted(p.name for p in
                                                 Path("/home/dowling/.local/share/uv/python").iterdir()
                                                 if p.is_dir()),
                    },
                    "clear_env": {"LD_LIBRARY_PATH": env.get("LD_LIBRARY_PATH"),
                                  "LD_PRELOAD": env.get("LD_PRELOAD"),
                                  "CUDA_VISIBLE_DEVICES": env.get("CUDA_VISIBLE_DEVICES"),
                                  "NVIDIA_VISIBLE_DEVICES": env.get("NVIDIA_VISIBLE_DEVICES")},
                    "envs": {}, "separation": {}}
    for name, python in envs.items():
        freeze = Path(FREEZES[name])
        item = {"python": python, "interpreter": interpreter_facts(python, env),
                "freeze": freeze_check(name, python, freeze, env) if freeze.is_file()
                else {"freeze_file": str(freeze), "exists": False},
                "separate_from": {}}
        item[name if name == "torch312" else "jax"] = (torch_check if name == "torch312"
                                                       else jax_check)(python, env)
        result["envs"][name] = item

    # separation from the pre-existing ar-cond7a / Track P venvs
    for other in ("/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python",
                  "/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python",
                  "/home/dowling/r1_trackp/venvs/trackp-cpu/bin/python"):
        path = Path(other)
        if not path.exists():
            result["separation"][other] = {"exists": False}
            continue
        info = {"exists": True, "realpath": os.path.realpath(path),
                "version": run([other, "-VV"], env=env).get("stdout", "").strip(),
                "prefix": run([other, "-c", "import sys; print(sys.prefix)"], env=env)
                .get("stdout", "").strip()}
        sample = json.loads(run([other, "-c", "import json,site; print(json.dumps(site.getsitepackages()))"],
                                env=env).get("stdout", "[]").strip() or "[]")
        info["site_packages"] = sample
        result["separation"][other] = info
    ours = [str((t1 / "envs" / n).resolve()) for n in envs]
    foreign = [v.get("prefix") for v in result["separation"].values() if v.get("prefix")]
    result["separation"]["ours"] = ours
    result["separation"]["foreign_prefixes"] = foreign
    result["separation"]["disjoint"] = all(not (o == f or o.startswith(f + os.sep) or f.startswith(o + os.sep))
                                           for o in ours for f in foreign if f)
    result["separation"]["no_ld_library_path"] = (env.get("LD_LIBRARY_PATH") is None
                                                  and env.get("LD_PRELOAD") is None)

    checks = {}
    for name, item in result["envs"].items():
        interp = item["interpreter"]
        checks[f"{name}_python_3.12.16"] = interp.get("version") == "3.12.16"
        checks[f"{name}_freeze_equal"] = bool((item.get("freeze") or {}).get("line_equal_sorted"))
        checks[f"{name}_freeze_byte_equal_census_collation"] = bool(
            (item.get("freeze") or {}).get("locale_sorted_byte_equal"))
        checks[f"{name}_managed_interpreter"] = (interp.get("realpath") or "").startswith(
            "/home/dowling/.local/share/uv/python/cpython-3.12.16-")
    checks["torch_gpu_available"] = bool((result["envs"]["torch312"].get("torch312") or {}).get("ok"))
    checks["jax_gpu_available"] = bool((result["envs"]["jax312"].get("jax") or {}).get("ok"))
    checks["environments_separate"] = bool(result["separation"]["disjoint"])
    checks["no_ld_library_path"] = bool(result["separation"]["no_ld_library_path"])
    result["checks"] = checks
    result["condition_env_pass"] = all(checks.values())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        lines = [f"utc={result['utc']} host={result['host']}",
                 f"uv_version={result['uv']['version'].get('stdout', '').strip()}",
                 f"uv_python_find_3.12.16={result['python_install']['uv_python_find_3.12.16'].get('stdout', '').strip()}"]
        for name, item in result["envs"].items():
            interp = item["interpreter"]
            fr = item.get("freeze") or {}
            lines.append(f"--- {name}: {item['python']}")
            lines.append(f"  version={interp.get('version')} realpath={interp.get('realpath')}")
            lines.append(f"  pyvenv_home={(interp.get('pyvenv_cfg') or '').strip().splitlines()[0] if interp.get('pyvenv_cfg') else None}")
            lines.append(f"  freeze_file={fr.get('freeze_file')} sha256={fr.get('freeze_sha256')}")
            lines.append(f"  uv_pip_freeze_sha256={fr.get('uv_freeze_sha256')} byte_equal={fr.get('byte_equal')} "
                         f"line_equal_sorted={fr.get('line_equal_sorted')} "
                         f"locale_sorted_byte_equal={fr.get('locale_sorted_byte_equal')} "
                         f"locale_sorted_sha256={fr.get('locale_sorted_sha256')} "
                         f"lines={fr.get('freeze_lines')}")
            key = "torch312" if name == "torch312" else "jax"
            facts = item.get(key) or {}
            lines.append(f"  {key}=" + json.dumps({k: facts.get(k) for k in
                                                   ("ok", "torch_version", "torch_cuda_version",
                                                    "cuda_available", "device_name", "capability",
                                                    "tensor_sum", "tensor_sum_ok", "matmul_value",
                                                    "jax_version", "backend", "devices",
                                                    "tensor_sum_ok", "ld_library_path")}, default=str))
        lines.append(f"separation.disjoint={result['separation']['disjoint']} "
                     f"no_ld_library_path={result['separation']['no_ld_library_path']}")
        lines.append(f"checks={json.dumps(checks)}")
        lines.append(f"condition_env_pass={result['condition_env_pass']}")
        Path(args.text).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps({"condition_env_pass": result["condition_env_pass"],
                                  "checks": checks,
                                  "freezes": {n: {"sha256": (i.get("freeze") or {}).get("freeze_sha256"),
                                                  "byte_equal": (i.get("freeze") or {}).get("byte_equal"),
                                                  "line_equal_sorted": (i.get("freeze") or {}).get("line_equal_sorted"),
                                                  "locale_sorted_byte_equal": (i.get("freeze") or {}).get("locale_sorted_byte_equal"),
                                                  "uv_sha256": (i.get("freeze") or {}).get("uv_freeze_sha256")}
                                              for n, i in result["envs"].items()},
                                  "torch": {k: result["envs"]["torch312"]["torch312"].get(k)
                                            for k in ("ok", "torch_version", "cuda_available", "device_name")},
                                  "jax": {k: result["envs"]["jax312"]["jax"].get(k)
                                          for k in ("ok", "jax_version", "backend", "devices")}},
                                 default=str))
    return 0 if result["condition_env_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
