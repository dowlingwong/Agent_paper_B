"""Tests for the D.3a endpoint identity guard (ENGINEERING, synthetic)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from r1.c3.d3 import endpoint_guard as G

UUID = "GPU-4d623e76-7587-ee15-a633-46f60d220d94"
LEASE = "/home/dowling/r1_locks/gpu0.lock"
MODEL = "/home/dowling/exam-x/models/gemma4_31b/model.gguf"
PORT = 8095


def _manifest() -> dict:
    return {
        "schema": "r1_d3_campaign_manifest/v1",
        "route": {
            "host": "TASL-2",
            "gpu_uuid": UUID,
            "gpu_lease_path": LEASE,
            "server_argv": [
                "/home/dowling/r1_tracks/opt/llama.cpp/build/bin/llama-server",
                "-m", MODEL, "--host", "127.0.0.1", "--port", str(PORT),
                "-ngl", "999", "-c", "32768", "-np", "1", "--jinja",
            ],
        },
    }


def _observed() -> dict:
    return {"gpu_uuid": UUID, "lease": True, "lease_path": LEASE}


class FakeProbe:
    def __init__(self, **overrides):
        self.alive_value = True
        self.listeners = [4242]
        self.props_value = {
            "model_path": MODEL,
            "default_generation_settings": {"n_ctx": 32768},
            "total_slots": 1,
        }
        self.apps = [{"gpu_uuid": UUID, "pid": 4242, "used_memory": "21618 MiB"}]
        self.self_lease = True
        self.server_lease = True
        self.lease_uuid = UUID
        for key, value in overrides.items():
            setattr(self, key, value)

    def alive(self, pid):
        assert pid == 4242
        return self.alive_value

    def listener_pids(self, port):
        assert port == PORT
        return self.listeners

    def props(self, host, port):
        assert (host, port) == ("127.0.0.1", PORT)
        return self.props_value

    def compute_apps(self):
        return self.apps

    def self_holds_lease(self, lease_fd, lease_path):
        assert (lease_fd, lease_path) == (9, LEASE)
        return self.self_lease

    def server_holds_lease(self, pid, lease_path):
        assert (pid, lease_path) == (4242, LEASE)
        return self.server_lease

    def lease_gpu_uuid(self, lease_path):
        assert lease_path == LEASE
        return self.lease_uuid


def _verify(probe=None, **kw):
    return G.verify_endpoint(manifest=_manifest(), observed=_observed(), server_pid=4242,
                             lease_path=LEASE, lease_fd=9, host="127.0.0.1", port=PORT,
                             probe=probe or FakeProbe(), **kw)


def test_success_records_every_check():
    result = _verify()
    assert result.ok
    names = [check.name for check in result.checks]
    assert names == ["lease_path", "observed_uuid", "observed_lease", "server_alive",
                     "guard_lease_fd", "server_lease_fd", "listener_pid", "props_model",
                     "props_n_ctx", "props_slots", "compute_app_pid", "compute_app_uuid",
                     "lease_card_uuid"]
    payload = result.as_dict(server_pid=4242, route=G.expected_route(_manifest()),
                             manifest_sha256="a" * 64, observed_sha256="b" * 64)
    assert payload["schema"] == G.CHECK_SCHEMA
    assert payload["ok"] is True and payload["failed"] is None
    assert payload["expected"]["gpu_uuid"] == UUID


@pytest.mark.parametrize("overrides, failed", [
    ({"alive_value": False}, "server_alive"),
    ({"listeners": [9999]}, "listener_pid"),
    ({"listeners": [4242, 9999]}, "listener_pid"),
    ({"listeners": []}, "listener_pid"),
    ({"props_value": {"model_path": "/models/other.gguf",
                      "default_generation_settings": {"n_ctx": 32768}, "total_slots": 1}},
     "props_model"),
    ({"props_value": {"model_path": MODEL,
                      "default_generation_settings": {"n_ctx": 8192}, "total_slots": 1}},
     "props_n_ctx"),
    ({"props_value": {"model_path": MODEL,
                      "default_generation_settings": {"n_ctx": 32768}, "total_slots": 4}},
     "props_slots"),
    ({"apps": [{"gpu_uuid": UUID, "pid": 9999, "used_memory": "1 MiB"}]}, "compute_app_pid"),
    ({"apps": [{"gpu_uuid": "GPU-00000000-0000-0000-0000-000000000000", "pid": 4242,
                "used_memory": "1 MiB"}]}, "compute_app_uuid"),
    ({"self_lease": False}, "guard_lease_fd"),
    ({"server_lease": False}, "server_lease_fd"),
    ({"lease_uuid": "GPU-00000000-0000-0000-0000-000000000000"}, "lease_card_uuid"),
])
def test_each_identity_failure_stops(overrides, failed):
    with pytest.raises(G.EndpointStop) as excinfo:
        _verify(FakeProbe(**overrides))
    assert str(excinfo.value).startswith(failed + ":")


def test_foreign_responder_after_failed_bind_stops():
    """The local stub's failure: a different process answers /props on the port."""
    probe = FakeProbe(listeners=[31337], props_value={
        "model_path": MODEL, "default_generation_settings": {"n_ctx": 32768}, "total_slots": 1})
    with pytest.raises(G.EndpointStop, match="listener_pid"):
        _verify(probe)


def test_observed_uuid_or_lease_mismatch_stops():
    manifest = _manifest()
    with pytest.raises(G.EndpointStop, match="observed_uuid"):
        G.verify_endpoint(manifest=manifest,
                          observed={"gpu_uuid": "GPU-00000000-0000-0000-0000-000000000000",
                                    "lease": True, "lease_path": LEASE},
                          server_pid=4242, lease_path=LEASE, lease_fd=9,
                          host="127.0.0.1", port=PORT, probe=FakeProbe())
    with pytest.raises(G.EndpointStop, match="observed_lease"):
        G.verify_endpoint(manifest=manifest, observed={"gpu_uuid": UUID, "lease": False,
                                                       "lease_path": LEASE},
                          server_pid=4242, lease_path=LEASE, lease_fd=9,
                          host="127.0.0.1", port=PORT, probe=FakeProbe())


def test_driver_lease_path_must_match_manifest():
    with pytest.raises(G.EndpointStop, match="lease_path"):
        G.verify_endpoint(manifest=_manifest(), observed=_observed(), server_pid=4242,
                          lease_path="/home/dowling/r1_locks/gpu1.lock", lease_fd=9,
                          host="127.0.0.1", port=PORT, probe=FakeProbe())


def test_guard_cannot_be_pointed_at_another_port():
    with pytest.raises(G.EndpointStop, match="guard port"):
        G.expected_route(_manifest(), port=8096)


def test_server_route_reads_argv():
    route = G.server_route(_manifest()["route"]["server_argv"])
    assert route == {"host": "127.0.0.1", "port": PORT, "model_path": MODEL,
                     "n_ctx": 32768, "n_slots": 1}
    with pytest.raises(G.EndpointStop):
        G.server_route(["-m", MODEL, "-c", "32768"])


def test_parse_ss_listeners():
    text = ('State Recv-Q Send-Q Local Address:Port Peer Address:Port Process\n'
            'LISTEN 0 512 127.0.0.1:8095 0.0.0.0:* '
            'users:(("llama-server",pid=1673663,fd=12))\n')
    assert G.parse_ss_listeners(text, 8095) == [1673663]
    assert G.parse_ss_listeners(text, 8096) == []
    with pytest.raises(G.EndpointStop):
        G.parse_ss_listeners('LISTEN 0 512 127.0.0.1:8095 0.0.0.0:*', 8095)


def test_parse_compute_apps():
    text = "GPU-4d623e76-7587-ee15-a633-46f60d220d94, 1673663, 21618\n"
    assert G.parse_compute_apps(text) == [
        {"gpu_uuid": UUID, "pid": 1673663, "used_memory": "21618"}]
    assert G.parse_compute_apps("gpu_uuid, pid, used_memory\n") == []


def test_cli_writes_stop_record_and_returns_90(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    observed = tmp_path / "observed.json"
    manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
    observed.write_text(json.dumps(_observed()), encoding="utf-8")
    out = tmp_path / "check.json"

    def failing(**kwargs):
        raise G.EndpointStop("listener_pid: foreign responder")

    monkeypatch.setattr(G, "verify_endpoint", failing)
    rc = G.main(["--manifest", str(manifest), "--observed", str(observed),
                 "--server-pid", "4242", "--lease-path", LEASE, "--host", "127.0.0.1",
                 "--port", str(PORT), "--out", str(out)])
    assert rc == G.STOP_RC
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["failed"] == "guard"
    assert payload["reason"] == "listener_pid: foreign responder"


def test_production_driver_invokes_guard_before_each_chunk():
    root = Path(__file__).resolve().parents[2]
    text = (root / "docs/r1/reports/d3a_production_route_20261128/production_driver.sh").read_text(
        encoding="utf-8")
    run_start = text.index("run_chunk_checked() {")
    verify_at = text.index('verify_endpoint "chunk_${tag}"', run_start)
    chunk_at = text.index("-m r1.c3.d3.campaign_chunk", run_start)
    assert verify_at < chunk_at, "the guard must run before the chunk module"
    assert 'verify_endpoint "ready"' in text
    assert text.index('verify_endpoint "ready"') < text.index('if [ "${RUN_CHUNK:-0}" = "1" ]')
    assert "seal_scene" in text and "STOP_RC=90" in text


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="needs /proc and Linux tools")
def test_host_probe_success_against_fake_binaries_and_real_props(tmp_path):
    """Real HostProbe: fake ss/nvidia-smi, a real /props HTTP response, a real lease inode."""
    import http.server
    import threading

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            body = json.dumps({"model_path": MODEL,
                               "default_generation_settings": {"n_ctx": 32768},
                               "total_slots": 1}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            return

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    lease = tmp_path / "gpu0.lock"
    lease.write_text("")
    lease_fh = lease.open("r+")
    ss = tmp_path / "ss"
    ss.write_text(f"#!/bin/sh\necho 'LISTEN 0 512 127.0.0.1:{port} 0.0.0.0:* "
                  f"users:((\"llama-server\",pid={os.getpid()},fd=1))'\n")
    smi = tmp_path / "nvidia-smi"
    smi.write_text("#!/bin/sh\n"
                   "case \"$*\" in\n"
                   "-i*) echo 'GPU-4d623e76-7587-ee15-a633-46f60d220d94' ;;\n"
                   "*) echo 'GPU-4d623e76-7587-ee15-a633-46f60d220d94, "
                   f"{os.getpid()}, 21618' ;;\n"
                   "esac\n")
    for path in (ss, smi):
        path.chmod(0o755)

    manifest = _manifest()
    manifest["route"]["server_argv"][manifest["route"]["server_argv"].index("--port") + 1] = str(port)
    manifest["route"]["gpu_lease_path"] = str(lease)
    observed = dict(_observed(), lease_path=str(lease))
    probe = G.HostProbe(ss_bin=str(ss), nvidia_smi_bin=str(smi), proc_root="/proc")
    try:
        result = G.verify_endpoint(manifest=manifest, observed=observed,
                                   server_pid=os.getpid(), lease_path=str(lease),
                                   lease_fd=lease_fh.fileno(), host="127.0.0.1", port=port,
                                   probe=probe)
        assert result.ok
    finally:
        lease_fh.close()
        server.shutdown()
