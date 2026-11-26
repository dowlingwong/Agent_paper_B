"""A dedicated Ollama server per batch (C3 label sweep; rerun-2 STOP follow-up, 19 Oct 2026).

The rerun-2 STOP showed the model runner of the batch's Ollama server receiving
SIGTERM from an unidentified sender.  This helper gives a batch a server that
nothing else shares:

* its own ``OLLAMA_HOST`` port (refuses if anything already listens there);
* its own ``OLLAMA_MODELS`` directory under the batch directory (optionally
  seeded by hard-linking, else copying, a pinned models directory);
* started in its own process group, health-checked on ``/api/version``;
* PID, process group, port, models directory and times recorded in
  ``<batch>/ollama_instance.json`` (and its log in ``ollama_serve_<port>.log``);
* ``stop()`` signals only that process group, and only after checking the
  PID is still the process it started.  It never touches another server.

Restarts (RUNBOOK A.5/A.8, 24 Oct): ``generation`` > 0 names the record and
log ``ollama_instance_<port>_r<generation>.json`` / ``ollama_serve_<port>_r<g>.log``
so an earlier instance's record is never overwritten, and ``reuse_models``
lets a restarted instance use the batch's existing models directory (the
runner re-checks the digest).  ``orphan_matches`` / ``stop_orphan`` stop a
previous instance of the *same batch* left running by a killed runner, and only
after its pid, process group and environment (port, models directory) match
the batch's record.  Generation 0 without reuse is the historical behaviour.

Fake-able: ``binary`` may be any executable that honours ``OLLAMA_HOST``
(the dry run passes ``r1/scripts/c3_fake_ollama.py`` through a wrapper).

ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def port_is_free(port: int) -> bool:
    """Nothing listens on *port*.  SO_REUSEADDR (as servers bind) so that connections of a stopped
    server still in TIME_WAIT do not count as a server (restart on the same port, RUNBOOK A.5/A.8);
    a listening socket still makes the bind fail."""
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    with socket.socket() as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) != 0


def seed_models(source: Path, target: Path) -> str:
    """Populate *target* from a pinned models directory: hard links when possible, else a copy."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise RuntimeError(f"STOP: models directory already exists: {target}")
    try:
        subprocess.run(["cp", "-al", str(source), str(target)], check=True, capture_output=True)
        return "hardlink"
    except (subprocess.CalledProcessError, FileNotFoundError):
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return "copy"


class OllamaInstance:
    def __init__(self, batch_dir: str | Path, binary: str, *, port: int | None = None,
                 models_dir: str | Path | None = None, seed_models_from: str | Path | None = None,
                 gpu_uuid: str | None = None, keep_alive: str = "-1", label: str = "ENGINEERING_ONLY",
                 env_extra: dict[str, str] | None = None, start_timeout: float = 60.0,
                 generation: int = 0, reuse_models: bool = False) -> None:
        self.batch = Path(batch_dir).resolve()
        self.binary = str(binary)
        self.port = int(port) if port else free_port()
        self.models_dir = Path(models_dir).resolve() if models_dir else self.batch / f"ollama_models_{self.port}"
        if not self.models_dir.is_relative_to(self.batch):
            raise ValueError("STOP: OLLAMA_MODELS must live under the batch directory")
        self.seed_models_from = Path(seed_models_from) if seed_models_from else None
        self.gpu_uuid, self.keep_alive, self.label = gpu_uuid, keep_alive, label
        self.env_extra = dict(env_extra or {})
        self.start_timeout = start_timeout
        self.process: subprocess.Popen | None = None
        self.generation, self.reuse_models = int(generation), bool(reuse_models)
        suffix = f"_r{self.generation}" if self.generation else ""
        self.record_path = self.batch / f"ollama_instance_{self.port}{suffix}.json"
        self.log_path = self.batch / f"ollama_serve_{self.port}{suffix}.log"
        self.record: dict = {}

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def env(self) -> dict[str, str]:
        env = dict(os.environ)
        env.update(OLLAMA_HOST=f"127.0.0.1:{self.port}", OLLAMA_MODELS=str(self.models_dir),
                   OLLAMA_KEEP_ALIVE=self.keep_alive, OLLAMA_NUM_PARALLEL="1", OLLAMA_VULKAN="0")
        if self.gpu_uuid:
            env["CUDA_VISIBLE_DEVICES"] = self.gpu_uuid
        env.update(self.env_extra)
        return env

    def _save(self) -> None:
        self.record_path.write_text(json.dumps(self.record, indent=2) + "\n")

    def health(self, timeout: float = 2.0) -> dict | None:
        try:
            with urlopen(self.url + "/api/version", timeout=timeout) as response:
                return json.load(response)
        except (OSError, ValueError):
            return None

    def start(self) -> dict:
        if self.process is not None:
            raise RuntimeError("STOP: this instance was already started")
        if not port_is_free(self.port):
            raise RuntimeError(f"STOP: port {self.port} is in use; a dedicated instance never shares a server")
        self.batch.mkdir(parents=True, exist_ok=True)
        seeded = None
        if self.reuse_models and self.models_dir.is_dir():
            seeded = "reused"
        elif self.seed_models_from is not None:
            seeded = seed_models(self.seed_models_from, self.models_dir)
        else:
            self.models_dir.mkdir(parents=True, exist_ok=True)
        log = self.log_path.open("ab")
        self.process = subprocess.Popen([self.binary, "serve"], env=self.env(), stdout=log,
                                        stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                        start_new_session=True)
        log.close()
        self.record = {"label": self.label, "binary": self.binary, "pid": self.process.pid,
                       "pgid": os.getpgid(self.process.pid), "port": self.port, "url": self.url,
                       "models_dir": str(self.models_dir), "models_seeded": seeded,
                       "seed_models_from": str(self.seed_models_from) if self.seed_models_from else None,
                       "gpu_uuid": self.gpu_uuid, "keep_alive": self.keep_alive,
                       "log": str(self.log_path), "started_utc": _utc()}
        if self.generation:
            self.record["generation"] = self.generation
        self._save()
        deadline = time.monotonic() + self.start_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.record.update(exited_early=self.process.returncode, failed_utc=_utc())
                self._save()
                raise RuntimeError(f"STOP: dedicated Ollama exited during start (rc={self.process.returncode})")
            version = self.health()
            if version is not None:
                self.record.update(healthy_utc=_utc(), version=version)
                self._save()
                return self.record
            time.sleep(0.2)
        self.stop()
        raise RuntimeError("STOP: dedicated Ollama server did not become healthy")

    def alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def pull(self, model: str, log_name: str = "model_pull.log") -> None:
        with (self.batch / log_name).open("a") as f:
            subprocess.run([self.binary, "pull", model], env=self.env(), check=True, stdout=f,
                           stderr=subprocess.STDOUT)

    def stop(self, timeout: float = 20.0) -> dict:
        """Stop only the process group this instance started; record the outcome."""
        if self.process is None:
            return self.record
        if self.process.poll() is None:
            pgid = self.record.get("pgid")
            if pgid != os.getpgid(self.process.pid):
                raise RuntimeError("STOP: process group changed; refusing to signal")
            os.killpg(pgid, signal.SIGTERM)
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(pgid, signal.SIGKILL)
                self.process.wait(timeout=timeout)
                self.record["killed"] = True
        self.record.update(stopped_utc=_utc(), returncode=self.process.returncode)
        self._save()
        return self.record

    def returncode_info(self) -> dict:
        """Exit status of the server process: returncode and, for a signal, its name."""
        rc = None if self.process is None else self.process.poll()
        info: dict = {"returncode": rc}
        if rc is not None and rc < 0:
            try:
                info["signal"] = signal.Signals(-rc).name
            except ValueError:
                info["signal"] = f"signal {-rc}"
        return info

    def __enter__(self) -> "OllamaInstance":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


def pid_alive(pid: int) -> bool:
    """True for a running (non-zombie) process."""
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        stat = Path(f"/proc/{int(pid)}/stat").read_text()
        return stat.rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


def _proc_environ(pid: int) -> dict[str, str]:
    raw = Path(f"/proc/{pid}/environ").read_bytes()
    return dict(item.split("=", 1) for item in raw.decode(errors="replace").split("\0") if "=" in item)


def orphan_matches(record: dict) -> tuple[bool, str]:
    """Is the process in an earlier instance *record* still alive, and provably that instance?

    Returns (alive_and_ours, reason).  Ours means: same pid, same process group
    (the instance was started in its own session), and its environment has the
    record's ``OLLAMA_HOST`` port and ``OLLAMA_MODELS`` directory.  A live pid
    that fails any check is not ours and must never be signalled.
    """
    pid, pgid = record.get("pid"), record.get("pgid")
    if not pid or record.get("stopped_utc"):
        return False, "no live process recorded"
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False, "not running"
    except PermissionError:
        return False, "pid belongs to another user"
    if not pid_alive(int(pid)):
        return False, "not running (zombie)"
    try:
        if os.getpgid(int(pid)) != pgid:
            return False, "process group differs (pid reused)"
        env = _proc_environ(int(pid))
    except (OSError, ValueError) as exc:
        return False, f"cannot inspect pid: {exc!r}"
    if env.get("OLLAMA_HOST") != f"127.0.0.1:{record.get('port')}" or env.get("OLLAMA_MODELS") != record.get("models_dir"):
        return False, "environment differs (not this batch's instance)"
    return True, "alive; pid, process group, port and models directory match"


def stop_orphan(record: dict, timeout: float = 20.0) -> dict:
    """Stop an earlier instance of this batch left running by a killed runner (after ``orphan_matches``)."""
    ours, reason = orphan_matches(record)
    result = {"pid": record.get("pid"), "pgid": record.get("pgid"), "port": record.get("port"), "check": reason,
              "utc": _utc()}
    if not ours:
        result["action"] = "none"
        return result
    pgid = int(record["pgid"])
    os.killpg(pgid, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not pid_alive(int(record["pid"])):
            result["action"] = "SIGTERM"
            return result
        time.sleep(0.2)
    os.killpg(pgid, signal.SIGKILL)
    result["action"] = "SIGKILL"
    return result
