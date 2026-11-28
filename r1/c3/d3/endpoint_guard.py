"""D.3a production endpoint identity guard (ENGINEERING code).

The production driver starts one ``llama-server`` under the canonical card lease.  Before a
chunk starts, this guard proves that the endpoint the chunk will call is served by *that*
server process and by the leased card, not by some other responder that happened to answer
``/props`` after the intended server failed to bind.

The checks are fail-closed and read-only:

* the server PID is alive;
* the listener on the declared host/port belongs to that PID and to no other process;
* ``/props`` names the manifest's model file, context size and slot count;
* ``nvidia-smi`` lists that PID as a compute process on the manifest's GPU UUID;
* the wrapper's inherited lease descriptor and a descriptor of the server both point at
  the canonical ``~/r1_locks/gpu*.lock`` inode;
* the card named by that lease reports the manifest's UUID.

A mismatch raises :class:`EndpointStop`.  The driver seals the scene and exits with
``STOP_RC`` before the chunk module is imported.  No campaign, label or evaluation value is
read here.

The command binaries and ``/proc`` root may be overridden for the sandboxed engineering test
(``D3_GUARD_SS_BIN``, ``D3_GUARD_NVIDIA_SMI_BIN``, ``D3_GUARD_PROC_ROOT``); production uses the
host defaults.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

CHECK_SCHEMA = "r1_d3_endpoint_check/v1"
STOP_RC = 90
_UUID_RE = re.compile(r"^GPU-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
_LEASE_RE = re.compile(r"^gpu([0-9]+)\.lock$")


class EndpointStop(RuntimeError):
    """The endpoint is not the server the driver started on the leased card."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str | Path) -> str:
    import hashlib

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EndpointStop(f"{path} is not a JSON object")
    return payload


def _argv_value(argv: Sequence[str], *flags: str) -> str | None:
    """Return the value that follows the first of ``flags`` (``--flag=value`` also accepted)."""
    wanted = set(flags)
    for index, token in enumerate(argv):
        text = str(token)
        if text in wanted:
            if index + 1 >= len(argv):
                raise EndpointStop(f"server argv has no value after {text!r}")
            return str(argv[index + 1])
        for flag in flags:
            if text.startswith(flag + "="):
                return text[len(flag) + 1:]
    return None


def server_route(argv: Sequence[str]) -> dict[str, Any]:
    """Read the host, port, model path, context size and slot count from the server argv."""
    argv = [str(token) for token in argv]
    host = _argv_value(argv, "--host", "--hostname") or "127.0.0.1"
    port_text = _argv_value(argv, "--port")
    model = _argv_value(argv, "-m", "--model")
    ctx_text = _argv_value(argv, "-c", "--ctx-size", "--ctx_size")
    slots_text = _argv_value(argv, "-np", "--parallel", "--slots")
    if port_text is None or model is None or ctx_text is None:
        raise EndpointStop("the manifest server argv must carry --port, -m and -c")
    try:
        port = int(port_text)
        n_ctx = int(ctx_text)
        n_slots = int(slots_text) if slots_text is not None else 1
    except ValueError as exc:
        raise EndpointStop(f"the manifest server argv carries a non-numeric port/context/slot: {exc}") from exc
    if not (0 < port < 65536) or n_ctx <= 0 or n_slots <= 0:
        raise EndpointStop("the manifest server argv carries an out-of-range port/context/slot")
    return {"host": host, "port": port, "model_path": model, "n_ctx": n_ctx, "n_slots": n_slots}


def expected_route(manifest: Mapping[str, Any], *, host: str | None = None,
                   port: int | None = None) -> dict[str, Any]:
    """The route block plus the argv values the endpoint must report."""
    route = manifest.get("route")
    if not isinstance(route, Mapping):
        raise EndpointStop("the campaign manifest has no route block")
    argv = route.get("server_argv")
    if not isinstance(argv, Sequence) or isinstance(argv, (str, bytes)) or not argv:
        raise EndpointStop("the campaign manifest route has no server_argv list")
    parsed = server_route(argv)
    parsed["gpu_uuid"] = str(route.get("gpu_uuid") or "")
    parsed["lease_path"] = str(route.get("gpu_lease_path") or "")
    if not _UUID_RE.fullmatch(parsed["gpu_uuid"]):
        raise EndpointStop("the campaign manifest route has no valid gpu_uuid")
    if not parsed["lease_path"]:
        raise EndpointStop("the campaign manifest route has no gpu_lease_path")
    # A caller may not point the guard at a different endpoint than the server argv names.
    if host is not None and parsed["host"] != host:
        raise EndpointStop(f"the guard host {host!r} differs from the server argv {parsed['host']!r}")
    if port is not None and parsed["port"] != int(port):
        raise EndpointStop(f"the guard port {port} differs from the server argv {parsed['port']}")
    return parsed


def parse_ss_listeners(text: str, port: int) -> list[int]:
    """Return the PIDs that listen on ``port`` in ``ss -ltnp`` output."""
    pids: list[int] = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith(("state", "recv-q")):
            continue
        fields = stripped.split()
        if len(fields) < 4 or fields[0] != "LISTEN":
            continue
        local = fields[3]
        if not local.rsplit(":", 1)[-1] == str(port):
            continue
        found = [int(value) for value in re.findall(r"pid=(\d+)", stripped)]
        if not found:
            # A listening socket with no process detail cannot be attributed; fail closed.
            raise EndpointStop(f"ss reported a listener on port {port} without a PID")
        pids.extend(found)
    return pids


def parse_compute_apps(text: str) -> list[dict[str, Any]]:
    """Parse ``nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory`` output."""
    rows: list[dict[str, Any]] = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("gpu_uuid"):
            continue
        parts = [part.strip() for part in stripped.split(",")]
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[1])
        except ValueError as exc:
            raise EndpointStop(f"nvidia-smi compute-apps carried a non-numeric PID: {stripped!r}") from exc
        rows.append({"gpu_uuid": parts[0], "pid": pid, "used_memory": parts[2] if len(parts) > 2 else ""})
    return rows


class HostProbe:
    """Read-only host observation used by :func:`verify_endpoint`."""

    def __init__(self, *, ss_bin: str | None = None, nvidia_smi_bin: str | None = None,
                 proc_root: str | None = None, timeout: float = 5.0) -> None:
        self.ss_bin = ss_bin or os.environ.get("D3_GUARD_SS_BIN", "ss")
        self.nvidia_smi_bin = nvidia_smi_bin or os.environ.get("D3_GUARD_NVIDIA_SMI_BIN", "nvidia-smi")
        self.proc_root = proc_root or os.environ.get("D3_GUARD_PROC_ROOT", "/proc")
        self.timeout = float(timeout)

    def _run(self, argv: Sequence[str]) -> str:
        try:
            proc = subprocess.run(list(argv), capture_output=True, text=True, timeout=self.timeout)
        except (OSError, subprocess.SubprocessError) as exc:
            raise EndpointStop(f"cannot run {argv[0]!r}: {exc}") from exc
        if proc.returncode != 0:
            raise EndpointStop(f"{argv[0]!r} exited {proc.returncode}: {proc.stderr.strip()}")
        return proc.stdout

    def alive(self, pid: int) -> bool:
        return Path(self.proc_root, str(pid)).is_dir()

    def listener_pids(self, port: int) -> list[int]:
        return parse_ss_listeners(self._run([self.ss_bin, "-ltnp", f"sport = :{port}"]), port)

    def props(self, host: str, port: int) -> dict[str, Any]:
        url = f"http://{host}:{port}/props"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise EndpointStop(f"cannot read {url}: {exc}") from exc
        if not isinstance(payload, dict):
            raise EndpointStop(f"{url} did not return a JSON object")
        return payload

    def compute_apps(self) -> list[dict[str, Any]]:
        text = self._run([self.nvidia_smi_bin, "--query-compute-apps=gpu_uuid,pid,used_memory",
                          "--format=csv,noheader,nounits"])
        return parse_compute_apps(text)

    def _fd_stat(self, path: str) -> os.stat_result:
        try:
            return os.stat(path)
        except OSError as exc:
            raise EndpointStop(f"cannot stat {path}: {exc}") from exc

    def self_holds_lease(self, lease_fd: int, lease_path: str) -> bool:
        try:
            return os.path.samestat(os.fstat(lease_fd), os.stat(lease_path))
        except OSError as exc:
            raise EndpointStop(f"the guard cannot confirm its inherited lease fd {lease_fd}: {exc}") from exc

    def server_holds_lease(self, pid: int, lease_path: str) -> bool:
        lease = self._fd_stat(lease_path)
        fd_dir = Path(self.proc_root, str(pid), "fd")
        try:
            entries = list(fd_dir.iterdir())
        except OSError as exc:
            raise EndpointStop(f"cannot list {fd_dir}: {exc}") from exc
        for entry in entries:
            try:
                if os.path.samestat(os.stat(entry), lease):
                    return True
            except OSError:
                continue
        return False

    def lease_gpu_uuid(self, lease_path: str) -> str:
        name = Path(lease_path).name
        match = _LEASE_RE.fullmatch(name)
        if match:
            index = int(match.group(1))
            text = self._run([self.nvidia_smi_bin, "-i", str(index), "--query-gpu=uuid",
                              "--format=csv,noheader,nounits"]).strip().splitlines()
            if not text:
                raise EndpointStop(f"nvidia-smi reported no UUID for card {index}")
            return text[0].strip()
        if name.endswith(".lock") and _UUID_RE.fullmatch(name[:-5]):
            return name[:-5]
        raise EndpointStop(f"the lease {lease_path!r} does not name a card index or GPU UUID")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    expected: Any = None
    observed: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail,
                "expected": self.expected, "observed": self.observed}


@dataclass
class GuardResult:
    checks: list[Check] = field(default_factory=list)
    failed: str | None = None
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.failed is None

    def add(self, name: str, ok: bool, detail: str, expected: Any = None,
            observed: Any = None) -> None:
        self.checks.append(Check(name, ok, detail, expected, observed))
        if not ok and self.failed is None:
            self.failed = name
            self.reason = detail

    def as_dict(self, *, server_pid: int, route: Mapping[str, Any],
                manifest_sha256: str | None, observed_sha256: str | None) -> dict[str, Any]:
        return {
            "schema": CHECK_SCHEMA,
            "ok": self.ok,
            "utc": utc_now(),
            "server_pid": server_pid,
            "host": route.get("host"),
            "port": route.get("port"),
            "manifest_sha256": manifest_sha256,
            "observed_sha256": observed_sha256,
            "expected": {key: route.get(key) for key in
                         ("model_path", "n_ctx", "n_slots", "gpu_uuid", "lease_path")},
            "failed": self.failed,
            "reason": self.reason,
            "checks": [check.as_dict() for check in self.checks],
        }


def verify_endpoint(*, manifest: Mapping[str, Any], observed: Mapping[str, Any], server_pid: int,
                    lease_path: str, lease_fd: int = 9, host: str | None = None,
                    port: int | None = None, probe: HostProbe | None = None) -> GuardResult:
    """Run every endpoint identity check; raise :class:`EndpointStop` on the first failure."""
    probe = probe or HostProbe()
    route = expected_route(manifest, host=host, port=port)
    result = GuardResult()

    def check(name: str, ok: bool, detail: str, expected: Any = None, observed: Any = None) -> None:
        result.add(name, ok, detail, expected, observed)
        if not ok:
            raise EndpointStop(f"{name}: {detail}")

    check("lease_path", lease_path == route["lease_path"],
          "the driver's lease path must be the manifest route lease",
          route["lease_path"], lease_path)
    check("observed_uuid", str(observed.get("gpu_uuid") or "") == route["gpu_uuid"],
          "the pre-server probe must have observed the manifest GPU",
          route["gpu_uuid"], observed.get("gpu_uuid"))
    check("observed_lease", observed.get("lease") is True
          and str(observed.get("lease_path") or "") == route["lease_path"],
          "the pre-server probe must record the canonical lease",
          {"lease": True, "lease_path": route["lease_path"]},
          {"lease": observed.get("lease"), "lease_path": observed.get("lease_path")})
    check("server_alive", bool(server_pid) and probe.alive(int(server_pid)),
          "the PID the driver started must be alive", True, server_pid)
    check("guard_lease_fd", probe.self_holds_lease(int(lease_fd), route["lease_path"]),
          "the guard must inherit the wrapper's canonical GPU lease",
          route["lease_path"], f"fd {lease_fd}")
    check("server_lease_fd", probe.server_holds_lease(int(server_pid), route["lease_path"]),
          "the server process must hold the canonical GPU lease",
          route["lease_path"], server_pid)

    listeners = probe.listener_pids(route["port"])
    check("listener_pid", listeners == [int(server_pid)],
          "the endpoint port must be served by exactly the started server PID",
          [int(server_pid)], listeners)

    props = probe.props(route["host"], route["port"])
    model_path = str(props.get("model_path") or "")
    check("props_model", model_path == route["model_path"],
          "/props model_path must equal the manifest server argv model",
          route["model_path"], model_path)
    generation = props.get("default_generation_settings")
    if not isinstance(generation, Mapping):
        check("props_n_ctx", False, "/props has no default_generation_settings block")
    check("props_n_ctx", generation.get("n_ctx") == route["n_ctx"],
          "/props n_ctx must equal the manifest server argv context",
          route["n_ctx"], generation.get("n_ctx"))
    check("props_slots", props.get("total_slots") == route["n_slots"],
          "/props total_slots must equal the manifest server argv slot count",
          route["n_slots"], props.get("total_slots"))

    apps = probe.compute_apps()
    on_pid = [row for row in apps if row["pid"] == int(server_pid)]
    check("compute_app_pid", len(on_pid) == 1,
          "nvidia-smi must list the server PID exactly once as a compute process",
          1, on_pid)
    check("compute_app_uuid", on_pid[0]["gpu_uuid"] == route["gpu_uuid"],
          "the server PID must compute on the manifest GPU UUID",
          route["gpu_uuid"], on_pid[0]["gpu_uuid"])
    check("lease_card_uuid", probe.lease_gpu_uuid(route["lease_path"]) == route["gpu_uuid"],
          "the card named by the canonical lease must be the manifest GPU UUID",
          route["gpu_uuid"], probe.lease_gpu_uuid(route["lease_path"]))
    return result


def write_result(path: str | Path, result: GuardResult, *, server_pid: int,
                 route: Mapping[str, Any], manifest_sha256: str | None,
                 observed_sha256: str | None) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result.as_dict(server_pid=server_pid, route=route,
                                     manifest_sha256=manifest_sha256,
                                     observed_sha256=observed_sha256),
                      indent=1, sort_keys=True, allow_nan=False) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return sha256_file(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="D.3a endpoint identity guard (ENGINEERING)")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--observed", required=True)
    parser.add_argument("--server-pid", required=True, type=int)
    parser.add_argument("--lease-path", required=True)
    parser.add_argument("--lease-fd", type=int, default=9)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    manifest_path, observed_path = Path(args.manifest), Path(args.observed)
    manifest = _read_json(manifest_path)
    observed = _read_json(observed_path)
    try:
        route = expected_route(manifest, host=args.host, port=args.port)
        result = verify_endpoint(manifest=manifest, observed=observed, server_pid=args.server_pid,
                                 lease_path=args.lease_path, lease_fd=args.lease_fd,
                                 host=args.host, port=args.port)
    except EndpointStop as exc:
        try:
            route = expected_route(manifest, host=args.host, port=args.port)
        except EndpointStop:
            route = {"host": args.host, "port": args.port}
        result = GuardResult()
        result.add("guard", False, str(exc))
        write_result(args.out, result, server_pid=args.server_pid, route=route,
                     manifest_sha256=sha256_file(manifest_path),
                     observed_sha256=sha256_file(observed_path))
        print(f"STOP endpoint_guard: {exc}", file=sys.stderr)
        return STOP_RC
    write_result(args.out, result, server_pid=args.server_pid, route=route,
                 manifest_sha256=sha256_file(manifest_path),
                 observed_sha256=sha256_file(observed_path))
    print(json.dumps({"ok": True, "server_pid": args.server_pid, "port": route["port"],
                      "gpu_uuid": route["gpu_uuid"]}, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
