"""Small-model forecast sidecar for the A5/A6 arms (RUNBOOK Track H.5). ENGINEERING_ONLY; AI-assisted (Claude).

A stdlib HTTP service (no web framework) that loads one pinned model through a
loader interface and answers ``POST /forecast`` with 12 bin probabilities:

* **Pin.** A pin file (JSON) names ``base`` (model id and revision), ``adapter``
  (LoRA weights) and ``head`` paths with their ``sha256``; the service refuses to
  start (``PinError``, exit code 2) when a file's sha256 differs from the pin.
  The service ``digest`` is the sha256 of the pin's sorted (name, sha256) pairs;
  ``SidecarPrior(expected_digest=...)`` refuses any other digest.
* **Loader.** ``Loader.load(pin) -> predict(row) -> 12 probabilities``.
  ``FakeLoader`` serves fixed distributions (dry runs and tests; no model).
  ``TorchLoraLoader`` (Track P 1.11) builds the pinned decision model
  (``r1.c3.train.model.build_model`` from the pin's ``model`` spec: family,
  base path, head form) and loads the saved adapter + heads (the directory of
  the pinned ``manifest``; ``model.load`` re-checks every sha256). It answers
  only rows that carry the serialised view, ``row["prompt"] = {"state",
  "proposal"}`` (``r1.c3.train.serialize``); a row without it is a 500, so the
  client falls back to A1 exactly as on a timeout.
* **Endpoints.** ``GET /health`` -> ``{"status": "ok", "version", "digest"}``;
  ``POST /forecast`` with ``{"row": {"node", "features", "edit"?, "prompt"?}}`` ->
  ``{"probs": [12], "version", "digest", "compute_s"}``.  A loader output that is
  not 12 finite non-negative numbers summing to 1 (after normalisation of a
  positive sum) is a 500.
* **Fault injection** (fake only, for the timeout tests and dry runs):
  ``delay_s`` sleeps before answering (every call, or only the call numbers in
  ``delay_calls``); ``fail`` answers 500.

The client is ``r1.c3.prior_model.SidecarPrior`` (1 s timeout, falls back to the
A1 prior and logs ``prior_unavailable``).  Co-residency and the deepthought
smoke are outside this module (RUNBOOK H.5).

Usage:
  python -m r1.c3.serve --pin PIN.json --port 8765 --fake FIXED.json [--delay-s 0]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

N_BINS = 12
SERVE_VERSION = "c3_sidecar/v1"


class PinError(RuntimeError):
    """A pinned file is missing or its sha256 differs from the pin."""


def sha256_file(path: Path | str) -> str:
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class Pin:
    name: str                 # arm name, e.g. "A5" or "A6"
    base: str                 # base model id and revision (recorded; TorchLoraLoader builds from ``model``)
    files: dict               # {"adapter": {"path", "sha256"}, "head": {"path", "sha256"}, ...}
    model: dict = None        # TorchLoraLoader only: {"family", "base_path", "head_form", "dtype"?}

    @classmethod
    def load(cls, path: Path | str) -> "Pin":
        from r1.c3.analysis_guard import refuse_sealed
        refuse_sealed(path)
        data = json.loads(Path(path).read_text())
        root = Path(path).resolve().parent
        files = {}
        for key, spec in data["files"].items():
            p = Path(spec["path"])
            files[key] = {"path": str(p if p.is_absolute() else root / p), "sha256": str(spec["sha256"])}
        if "adapter" not in files:
            raise PinError("a pin must name the adapter")
        return cls(name=str(data["name"]), base=str(data["base"]), files=files, model=data.get("model"))

    def verify(self) -> None:
        for key, spec in self.files.items():
            if not Path(spec["path"]).exists():
                raise PinError(f"pinned {key} missing: {spec['path']}")
            actual = sha256_file(spec["path"])
            if actual != spec["sha256"]:
                raise PinError(f"{key} sha256 {actual} does not match the pin {spec['sha256']}")

    @property
    def digest(self) -> str:
        pairs = sorted((k, v["sha256"]) for k, v in self.files.items())
        return hashlib.sha256(json.dumps({"base": self.base, "files": pairs}).encode()).hexdigest()


class Loader(Protocol):
    def load(self, pin: Pin) -> Callable[[Mapping[str, Any]], list]: ...


class FakeLoader:
    """Fixed distributions, by node or a default (``{"default": [12], "by_node": {node: [12]}}``)."""

    def __init__(self, table: Mapping[str, Any]) -> None:
        self.table = dict(table)

    def load(self, pin: Pin):
        default, by_node = self.table.get("default"), dict(self.table.get("by_node") or {})

        def predict(row):
            return list(by_node.get(row.get("node"), default))
        return predict


class TorchLoraLoader:
    """Track P 1.11: the pinned decision model (base + LoRA adapter + heads) answering rows with a serialised view.

    ``builder(model_spec) -> wrapper`` builds the un-trained wrapper (default: ``build_model`` from the spec's
    ``family`` / ``base_path`` / ``head_form`` on CUDA when available); the saved adapter + heads are then loaded from
    the directory of the pinned ``manifest`` file. Forecast = softmax of the belief logits in ``BIN_OPTIONS`` order.
    """

    PIN_KEYS = ("adapter", "head", "manifest")

    def __init__(self, builder: Callable[[dict], Any] | None = None) -> None:
        self.builder = builder

    def _build(self, spec: dict):
        if self.builder is not None:
            return self.builder(spec)
        import torch
        from r1.c3.train.model import build_model
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        kw = {"head_form": spec.get("head_form", "softmax12"), "device": dev}
        if spec["family"] != "laya":
            kw["dtype"] = getattr(torch, spec.get("dtype", "bfloat16" if dev == "cuda" else "float32"))
        return build_model(spec["family"], spec["base_path"], **kw)

    def load(self, pin: Pin):
        # Validate the pin before importing torch: an invalid pin is refused without the
        # optional dependency, and a bad pin fails fast rather than after a model build.
        missing = [k for k in self.PIN_KEYS if k not in pin.files]
        if missing or not pin.model:
            raise PinError(f"a model pin needs files {self.PIN_KEYS} and a 'model' spec (missing: {missing or 'model'})")
        import torch
        from r1.c3.train.types import DecisionPrompt
        saved = Path(pin.files["manifest"]["path"]).parent
        model = self._build(dict(pin.model))
        model.load(saved)
        model.eval()
        lock = threading.Lock()   # one forward at a time (ThreadingHTTPServer)

        def predict(row):
            prompt = row.get("prompt")
            if not isinstance(prompt, Mapping) or not prompt.get("state") or not prompt.get("proposal"):
                raise ValueError("TorchLoraLoader needs row['prompt'] = {'state', 'proposal'} (the serialised view)")
            p = DecisionPrompt(state=str(prompt["state"]), proposal=str(prompt["proposal"]))
            with lock, torch.no_grad():
                logits = model([p])["belief_logits"][0].float()
            return torch.softmax(logits, -1).cpu().tolist()
        return predict


def write_model_pin(saved_dir: Path | str, pin_path: Path | str, *, name: str, base: str, model: dict) -> Path:
    """P.7 pin over a saved Track P model directory (``model.save``): adapter, heads and manifest with sha256."""
    saved = Path(saved_dir).resolve()
    files = {"adapter": saved / "adapter" / "adapter_model.safetensors", "head": saved / "heads.safetensors",
             "manifest": saved / "manifest.json"}
    pin = {"name": name, "base": base, "model": dict(model),
           "files": {k: {"path": str(v), "sha256": sha256_file(v)} for k, v in files.items()}}
    Path(pin_path).write_text(json.dumps(pin, indent=1, sort_keys=True))
    return Path(pin_path)


def _validate(probs) -> list:
    p = [float(x) for x in probs]
    if len(p) != N_BINS or not all(math.isfinite(x) and x >= 0 for x in p) or sum(p) <= 0:
        raise ValueError("the loader must return 12 finite non-negative numbers with a positive sum")
    s = sum(p)
    return [x / s for x in p]


class Sidecar:
    """The service: verify the pin, load the model, serve forecasts."""

    def __init__(self, pin: Pin, loader: Loader, *, delay_s: float = 0.0, fail: bool = False,
                 delay_calls: set | None = None) -> None:
        pin.verify()  # refuse before loading anything
        self.pin, self.predict = pin, loader.load(pin)
        self.version = f"{pin.name}/{SERVE_VERSION}/{pin.base}"
        self.digest = pin.digest
        self.delay_s, self.fail = float(delay_s), bool(fail)
        self.delay_calls = None if delay_calls is None else set(delay_calls)  # delay only these call numbers
        self.calls = 0
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def handler(self):
        sidecar = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):  # quiet
                pass

            def _send(self, code, payload):
                body = json.dumps(payload).encode()
                try:
                    self.send_response(code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):  # the client timed out and left
                    pass

            def do_GET(self):
                if self.path == "/health":
                    return self._send(200, {"status": "ok", "version": sidecar.version, "digest": sidecar.digest})
                return self._send(404, {"error": "not found"})

            def do_POST(self):
                if self.path != "/forecast":
                    return self._send(404, {"error": "not found"})
                sidecar.calls += 1
                t0 = time.perf_counter()
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    row = json.loads(self.rfile.read(n).decode())["row"]
                    if sidecar.delay_s and (sidecar.delay_calls is None or sidecar.calls in sidecar.delay_calls):
                        time.sleep(sidecar.delay_s)
                    if sidecar.fail:
                        raise RuntimeError("injected failure")
                    probs = _validate(sidecar.predict(row))
                except Exception as exc:  # noqa: BLE001 - the client falls back on any error
                    return self._send(500, {"error": repr(exc)[:300]})
                return self._send(200, {"probs": probs, "version": sidecar.version, "digest": sidecar.digest,
                                        "compute_s": time.perf_counter() - t0})
        return Handler

    def start(self, host: str = "127.0.0.1", port: int = 0) -> str:
        self.server = ThreadingHTTPServer((host, port), self.handler())
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://{host}:{self.server.server_address[1]}"

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None


def write_fake_pin(directory: Path | str, name: str = "A5", base: str = "fake-base@0") -> Path:
    """A pin over fixture adapter/head files (for dry runs and tests; the bytes are not a model)."""
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    files = {}
    for key in ("adapter", "head"):
        f = d / f"{name}_{key}.fixture"
        f.write_bytes(f"DRYRUN {name} {key}; not a model\n".encode())
        files[key] = {"path": f.name, "sha256": sha256_file(f)}
    pin = d / f"{name}_pin.json"
    pin.write_text(json.dumps({"name": name, "base": base, "files": files}, indent=1, sort_keys=True))
    return pin


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pin", required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--fake", help="JSON table of fixed distributions (FakeLoader)")
    src.add_argument("--torch", action="store_true", help="TorchLoraLoader: the pin's model spec and saved files")
    ap.add_argument("--delay-s", type=float, default=0.0)
    ap.add_argument("--ready-file", default=None, help="write the URL here once serving")
    args = ap.parse_args(argv)
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(args.pin, args.fake, args.ready_file)
    try:
        loader = TorchLoraLoader() if args.torch else FakeLoader(json.loads(Path(args.fake).read_text()))
        sidecar = Sidecar(Pin.load(args.pin), loader, delay_s=args.delay_s)
    except PinError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    url = sidecar.start(args.host, args.port)
    if args.ready_file:
        Path(args.ready_file).write_text(url + "\n")
    print(json.dumps({"url": url, "version": sidecar.version, "digest": sidecar.digest}), flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        sidecar.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
