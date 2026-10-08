"""Hash-bound evidence that the served runtime really is the sm_52 build.

WHY THIS REPLACES A LOG GREP
----------------------------
The previous check grepped the server log for `compute capability 5.2`,
`sm_52`, `compute_52` or `gtx titan x`. The pinned llama.cpp revision does not
emit a device banner into the server log at all, so the check returned a false
negative on a runtime that was demonstrably correct: `binary_digest` matched the
bound sm_52 build, and the same binary prints
`CUDA0: NVIDIA GeForce GTX TITAN X` under `--list-devices`.

The requirement is NOT weakened. A log line is one weak witness -- text a build
happens to print. This bundle replaces it with seven independent ones, several
of which are strictly stronger than any banner:

1. the served binary's SHA-256 equals the bound one;
2. the CUDA/ggml libraries it actually resolves at run time, by path and digest;
3. `cuobjdump --list-elf` over the resolved CUDA library: which SM architectures
   were actually COMPILED INTO it. A banner says what a device is; this says
   what code exists to run on it;
4. the CMakeCache digest and `CMAKE_CUDA_ARCHITECTURES=52`;
5. `--list-devices` from that exact binary;
6. `nvidia-smi` device identity and compute capability;
7. live GPU residency and utilisation during a real kernel request, plus the
   absence of CPU fallback.

Failing any one of them fails the check.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

RUNTIME_EVIDENCE_KIND = "round5_titan_runtime_evidence_bundle"
REQUIRED_CUDA_ARCHITECTURE = 52
REQUIRED_SM = f"sm_{REQUIRED_CUDA_ARCHITECTURE}"
REQUIRED_COMPUTE_CAPABILITY = "5.2"
CUDA_LIBRARY_MARKERS = ("ggml-cuda", "libcudart", "libcublas")
TARGET_CUDA_LIBRARY_MARKER = "ggml-cuda"


def _sha256_file(path: Path | str) -> str | None:
    try:
        digest = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _run(argv: Sequence[str], timeout: float = 120.0) -> dict[str, Any]:
    try:
        out = subprocess.run(list(argv), capture_output=True, text=True,
                             timeout=timeout)
        return {"argv": list(argv), "returncode": out.returncode,
                "stdout": out.stdout[:20000], "stderr": out.stderr[:4000]}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"argv": list(argv), "returncode": None,
                "error": f"{type(exc).__name__}: {exc}"}


def canonical_sha256(payload: Any) -> str:
    """Same canonicalisation the rest of this project uses."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")).hexdigest()


def resolved_libraries(llama_server: Path | str) -> list[dict[str, Any]]:
    """The CUDA/ggml libraries the binary actually resolves, with digests.

    `ldd` rather than the build tree: what matters is what this process will
    load, not what sits next to the binary.
    """
    result = _run(["ldd", str(llama_server)])
    libraries: list[dict[str, Any]] = []
    for line in (result.get("stdout") or "").splitlines():
        if "=>" not in line:
            continue
        soname, _, rest = line.strip().partition("=>")
        path = rest.strip().split(" (")[0].strip()
        soname = soname.strip()
        if not path or not any(m in soname for m in CUDA_LIBRARY_MARKERS):
            continue
        libraries.append({"soname": soname, "path": path,
                          "sha256": _sha256_file(path)})
    libraries.sort(key=lambda row: row["soname"])
    return libraries


def cuobjdump_architectures(library: Path | str, *, cuobjdump: str
                            ) -> dict[str, Any]:
    """Which SM architectures are actually compiled into the CUDA library."""
    result = _run([str(cuobjdump), "--list-elf", str(library)])
    found = sorted(set(re.findall(r"sm_\d+", result.get("stdout") or "")))
    return {"tool": str(cuobjdump), "library": str(library),
            "architectures": found,
            "elf_count": len([l for l in (result.get("stdout") or "").splitlines()
                              if l.strip()]),
            "returncode": result.get("returncode"),
            "error": result.get("error")}


def cmake_cache_evidence(cmake_cache: Path | str) -> dict[str, Any]:
    path = Path(cmake_cache)
    architectures = None
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("CMAKE_CUDA_ARCHITECTURES"):
                architectures = line.split("=", 1)[1].strip()
                break
    except OSError:
        pass
    return {"path": str(path), "sha256": _sha256_file(path),
            "cuda_architectures": architectures}


def list_devices_evidence(llama_server: Path | str) -> dict[str, Any]:
    result = _run([str(llama_server), "--list-devices"], timeout=180.0)
    text = result.get("stdout", "") + result.get("stderr", "")
    devices = [line.strip() for line in text.splitlines()
               if line.strip().startswith("CUDA")]
    return {**result, "cuda_devices": devices}


def nvidia_smi_evidence() -> dict[str, Any]:
    result = _run(["nvidia-smi",
                   "--query-gpu=index,name,uuid,compute_cap,driver_version",
                   "--format=csv,noheader"])
    devices: list[dict[str, Any]] = []
    for line in (result.get("stdout") or "").splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5 and parts[0].isdigit():
            devices.append({"index": int(parts[0]), "name": parts[1],
                            "uuid": parts[2], "compute_cap": parts[3],
                            "driver_version": parts[4]})
    return {"devices": devices, "returncode": result.get("returncode")}


def build_runtime_evidence(
    *, llama_server: Path | str, cmake_cache: Path | str, cuobjdump: str,
    live_residency: Mapping[str, Any] | None = None,
    cpu_fallback_observed: bool | None = None,
    required_architecture: str | int = REQUIRED_CUDA_ARCHITECTURE,
    required_compute_capability: str = REQUIRED_COMPUTE_CAPABILITY,
) -> dict[str, Any]:
    """Assemble the bundle. `bundle_sha256` binds every field above it.

    The two `required_*` arguments are recorded IN the bundle, so the evidence
    says which architecture it was asked to prove rather than leaving a reader
    to assume the Titan one.
    """
    libraries = resolved_libraries(llama_server)
    target = next((row for row in libraries
                   if TARGET_CUDA_LIBRARY_MARKER in row["soname"]), None)
    bundle: dict[str, Any] = {
        "artifact_kind": RUNTIME_EVIDENCE_KIND,
        "required_cuda_architecture": required_architecture,
        "required_compute_capability": required_compute_capability,
        "llama_server": {"path": str(llama_server),
                         "sha256": _sha256_file(llama_server)},
        "resolved_libraries": libraries,
        "target_cuda_library": target,
        "cuobjdump": (cuobjdump_architectures(target["path"], cuobjdump=cuobjdump)
                      if target else
                      {"error": "no ggml-cuda library resolved by the binary"}),
        "cmake_cache": cmake_cache_evidence(cmake_cache),
        "list_devices": list_devices_evidence(llama_server),
        "nvidia_smi": nvidia_smi_evidence(),
        "live_residency": dict(live_residency or {}),
        "cpu_fallback_observed": cpu_fallback_observed,
    }
    bundle["bundle_sha256"] = canonical_sha256(bundle)
    return bundle


def runtime_evidence_blockers(
    bundle: Mapping[str, Any] | None, *, expected_binary_sha256: str | None,
    hardware: str | None = None,
) -> list[str]:
    """Every witness must hold. Nothing here is advisory.

    `hardware` selects WHICH architecture the witnesses must prove. It defaults
    to the Titan profile because that is the round this module was written for,
    and leaving the default in place keeps a caller that forgets it visibly
    wrong rather than quietly permissive.

    On any other host the default is not merely wrong, it is unsatisfiable: a
    Blackwell card cannot report compute capability 5.2 and an sm_120 build
    cannot contain sm_52 cubins, so every candidate failed this check
    identically and the panel produced an empty comparison. Requiring the
    architecture the registry actually froze is what makes the check prove
    something instead of always failing.
    """
    if not isinstance(bundle, Mapping):
        return ["runtime_evidence_bundle_absent"]
    from causal_branch.round5_titan_exam import host_spec
    spec = host_spec(hardware)
    required_arch = str(spec["cuda_architecture"])
    required_sm = f"sm_{required_arch}"
    required_cc = str(spec["compute_capability"])
    blockers: list[str] = []

    served = ((bundle.get("llama_server") or {}).get("sha256"))
    if not served:
        blockers.append("runtime_evidence_binary_digest_unreadable")
    elif expected_binary_sha256 and served != expected_binary_sha256:
        blockers.append(
            f"runtime_evidence_binary_digest_mismatch:{served}:{expected_binary_sha256}")

    target = bundle.get("target_cuda_library")
    if not isinstance(target, Mapping) or not target.get("path"):
        blockers.append("runtime_evidence_no_cuda_library_resolved")
    elif not target.get("sha256"):
        blockers.append("runtime_evidence_cuda_library_digest_unreadable")

    cuobj = bundle.get("cuobjdump") or {}
    architectures = list(cuobj.get("architectures") or [])
    if not architectures:
        blockers.append("runtime_evidence_no_compiled_sm_architectures_found")
    elif not any(str(a).startswith(required_sm) for a in architectures):
        # `startswith`: nvcc emits `sm_120a` for the Blackwell feature-set
        # target, and that IS the required architecture.
        blockers.append(
            f"runtime_evidence_cuda_library_lacks_{required_sm}:{','.join(architectures)}")

    cache = bundle.get("cmake_cache") or {}
    declared = str(cache.get("cuda_architectures") or "")
    if not cache.get("sha256"):
        blockers.append("runtime_evidence_cmake_cache_unreadable")
    if required_arch not in re.findall(r"\d+", declared):
        blockers.append(
            f"runtime_evidence_cmake_cuda_architectures_not_{required_arch}:{declared}")

    if not (bundle.get("list_devices") or {}).get("cuda_devices"):
        blockers.append("runtime_evidence_binary_lists_no_cuda_device")

    devices = (bundle.get("nvidia_smi") or {}).get("devices") or []
    if not devices:
        blockers.append("runtime_evidence_nvidia_smi_reported_no_device")
    elif not any(str(row.get("compute_cap")) == required_cc
                 for row in devices):
        blockers.append(
            "runtime_evidence_no_device_at_compute_capability_"
            + required_cc)

    residency = bundle.get("live_residency") or {}
    used = residency.get("used_memory_mib_during")
    if used is None:
        blockers.append("runtime_evidence_no_live_gpu_residency_measured")
    else:
        try:
            if float(used) <= 0.0:
                blockers.append("runtime_evidence_live_gpu_residency_is_zero")
        except (TypeError, ValueError):
            blockers.append("runtime_evidence_live_gpu_residency_unreadable")

    if bundle.get("cpu_fallback_observed") is None:
        blockers.append("runtime_evidence_cpu_fallback_not_checked")
    elif bundle.get("cpu_fallback_observed"):
        blockers.append("runtime_evidence_cpu_fallback_observed")

    return sorted(set(blockers))
