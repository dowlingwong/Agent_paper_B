"""M4 2(e): two-GPU llama-server serving; the single-GPU path unchanged.

No GPU, no LLM: logs, nvidia-smi rows and the HTTP-only fake llama-server
(``r1/scripts/c3_fake_llama_server.py``). AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from r1.scripts import llama_server_instance as lsi

REPO = Path(__file__).resolve().parents[2]
FAKE = REPO / "r1/scripts/c3_fake_llama_server.py"
BASE_COMMIT = "a15300ca"  # mac-int-20261107, the base of this change
U1, U2 = "GPU-11111111-aaaa", "GPU-22222222-bbbb"
DUAL_LOG = """load_tensors: offloaded 29/29 layers to GPU
load_tensors:        CUDA0 model buffer size =  2084.05 MiB
load_tensors:        CUDA1 model buffer size =  2084.04 MiB
"""
SINGLE_LOG = """load_tensors: offloaded 29/29 layers to GPU
load_tensors:        CUDA0 model buffer size =  4168.09 MiB
"""


def make(tmp_path, **kw):
    return lsi.LlamaServerInstance(tmp_path / "batch", "/opt/llama-server", model_path="/m/x.gguf",
                                   alias="r1-manager", port=8123, **kw)


def base_module():
    try:
        source = subprocess.run(["git", "-C", str(REPO), "show", f"{BASE_COMMIT}:r1/scripts/llama_server_instance.py"],
                                capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("base commit not available")
    spec = importlib.util.spec_from_loader("lsi_base", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, "lsi_base.py", "exec"), module.__dict__)
    return module


@pytest.mark.parametrize("kw", [{}, {"gpu_uuid": U1}, {"gpu_uuid": U1, "extra_args": ["--jinja"],
                                                       "thinking_policy": {"mode": "off", "budget": 0,
                                                                           "off_switch": True}}])
def test_single_gpu_argv_and_env_equal_the_base_commit(tmp_path, kw, monkeypatch):
    monkeypatch.setenv("LLAMA_ARG_CTX_SIZE", "1")
    base = base_module()
    old = base.LlamaServerInstance(tmp_path / "batch", "/opt/llama-server", model_path="/m/x.gguf",
                                   alias="r1-manager", port=8123, **kw)
    new = make(tmp_path, **kw)
    assert new.argv == old.argv
    assert new.env() == old.env()
    assert new.gpu_uuids is None and new.tensor_split is None


@pytest.mark.parametrize("kw,msg", [
    ({"gpu_uuids": [U1, U2]}, "both gpu_uuids and tensor_split"),
    ({"tensor_split": [1, 1]}, "both gpu_uuids and tensor_split"),
    ({"gpu_uuid": U1, "gpu_uuids": [U1, U2], "tensor_split": [1, 1]}, "not both"),
    ({"gpu_uuids": [U1], "tensor_split": [1, 1]}, "two distinct"),
    ({"gpu_uuids": [U1, U1], "tensor_split": [1, 1]}, "two distinct"),
    ({"gpu_uuids": [U1, U2 + "," + U1], "tensor_split": [1, 1]}, "two distinct"),
    ({"gpu_uuids": [U1, U2], "tensor_split": [1, 0]}, "positive finite"),
    ({"gpu_uuids": [U1, U2], "tensor_split": [1, float("nan")]}, "positive finite"),
    ({"gpu_uuids": [U1, U2], "tensor_split": [True, 1]}, "positive finite"),
    ({"gpu_uuids": [U1, U2], "tensor_split": [1, 1, 1]}, "positive finite"),
])
def test_dual_settings_are_validated(tmp_path, kw, msg):
    with pytest.raises(ValueError, match=msg):
        make(tmp_path, **kw)


def test_dual_argv_and_env(tmp_path):
    inst = make(tmp_path, gpu_uuids=[U1, U2], tensor_split=[1, 1], extra_args=["--jinja"])
    assert inst.argv == ["/opt/llama-server", "-m", "/m/x.gguf", "--host", "127.0.0.1", "--port", "8123",
                         "-ngl", "999", "-c", "8192", "--alias", "r1-manager", "-np", "1",
                         "--split-mode", "layer", "--tensor-split", "1,1", "--jinja"]
    env, _ = inst.env()
    assert env["CUDA_VISIBLE_DEVICES"] == f"{U1},{U2}"
    assert make(tmp_path, gpu_uuids=[U1, U2], tensor_split=[0.6, 0.4]).argv[-1] == "0.6,0.4"


def rows(*pairs, pid=77):
    return [{"pid": pid, "gpu_uuid": u, "used_mib": m} for u, m in pairs]


def test_dual_route_i_needs_buffers_on_both_cards():
    ok = lsi.offload_check_dual(DUAL_LOG, pid=77, gpu_uuids=[U1, U2], footprint_mib=None,
                                apps=rows((U1, 2600), (U2, 2600)))
    assert ok["full"] and ok["route"] == "log_line" and ok["model_buffer_devices"] == ["CUDA0", "CUDA1"]
    assert [c["listed"] for c in ok["cards"]] == [True, True]
    one = lsi.offload_check_dual(SINGLE_LOG, pid=77, gpu_uuids=[U1, U2], footprint_mib=None, apps=[])
    assert not one["full"] and "not on two cards" in one["reasons"][0]


@pytest.mark.parametrize("log", [
    "load_tensors: offloaded 20/29 layers to GPU\nCUDA0 model buffer size = 1 MiB\nCUDA1 model buffer size = 1 MiB\n",
    DUAL_LOG + "warning: no usable GPU found, --gpu-layers option will be ignored\n",
])
def test_dual_partial_or_cpu_fallback_is_stop_whatever_the_memory(log):
    check = lsi.offload_check_dual(log, pid=77, gpu_uuids=[U1, U2], footprint_mib=[1, 1],
                                   apps=rows((U1, 9999), (U2, 9999)))
    assert not check["full"] and check["route"] is None


def test_dual_route_ii_requires_each_card_at_its_footprint():
    silent = "llama_server: model loaded\n"
    good = lsi.offload_check_dual(silent, pid=77, gpu_uuids=[U1, U2], footprint_mib=[2500, 2400],
                                  apps=rows((U1, 2600), (U2, 2450)))
    assert good["full"] and good["route"] == "gpu_memory"
    short = lsi.offload_check_dual(silent, pid=77, gpu_uuids=[U1, U2], footprint_mib=[2500, 2500],
                                   apps=rows((U1, 2600), (U2, 2450)))
    assert not short["full"] and U2 in short["reasons"][-1]
    missing = lsi.offload_check_dual(silent, pid=77, gpu_uuids=[U1, U2], footprint_mib=[1, 1],
                                     apps=rows((U1, 2600)))
    assert not missing["full"]
    for footprint in (None, 2500, [2500], [2500, 0], [True, 1]):
        refused = lsi.offload_check_dual(silent, pid=77, gpu_uuids=[U1, U2], footprint_mib=footprint,
                                         apps=rows((U1, 2600), (U2, 2600)))
        assert not refused["full"] and "per-card footprint" in refused["reasons"][-1]
    unread = lsi.offload_check_dual(silent, pid=77, gpu_uuids=[U1, U2], footprint_mib=[1, 1], apps=None)
    assert not unread["full"] and "could not be read" in unread["reasons"][-1]


def test_single_gpu_offload_check_unchanged_for_single_instances(tmp_path):
    inst = make(tmp_path, gpu_uuid=U1)
    inst.log_path.parent.mkdir(parents=True)
    inst.log_path.write_text(SINGLE_LOG)
    check = inst.offload(apps=rows((U1, 5000)))
    assert check["full"] and "cards" not in check and check["gpu_memory"]["gpu_uuid"] == U1


@pytest.fixture
def fake(tmp_path, monkeypatch):
    root = tmp_path / "dry"
    root.mkdir()
    (root / ".dryrun").write_text("DRYRUN\n")
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(root))
    monkeypatch.delenv("C3_FAKE_FAULTS", raising=False)
    monkeypatch.delenv("R1_DRYRUN", raising=False)
    binary = tmp_path / "bin" / "llama-server"
    binary.parent.mkdir()
    binary.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n"
                      f"runpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    binary.chmod(0o755)
    model = tmp_path / "models" / "m-Q4_K_M.gguf"
    model.parent.mkdir()
    model.write_bytes(b"GGUF fixture")
    started = []
    yield {"root": root, "binary": binary, "model": model, "tmp": tmp_path, "started": started}
    for inst in started:
        inst.stop(timeout=5)


def test_fake_two_gpu_server_records_and_proves_offload_on_both_cards(fake):
    inst = lsi.LlamaServerInstance(fake["tmp"] / "batch", str(fake["binary"]), model_path=str(fake["model"]),
                                   alias="r1-manager", label="DRYRUN", start_timeout=20,
                                   gpu_uuids=[U1, U2], tensor_split=[1, 1])
    fake["started"].append(inst)
    inst.start(build=lsi.build_info(str(fake["binary"])), model_sha256=lsi.sha256_file(fake["model"]))
    rec = json.loads(inst.record_path.read_text())
    assert rec["gpu_uuid"] is None and rec["gpu_uuids"] == [U1, U2]
    assert rec["tensor_split"] == [1, 1] and rec["split_mode"] == "layer"
    assert rec["argv"][-4:] == ["--split-mode", "layer", "--tensor-split", "1,1"]
    apps = lsi.parse_compute_apps((fake["root"] / "gpu_apps" / f"{rec['pid']}.csv").read_text())
    check = inst.offload(apps=apps)
    assert check["full"] and check["route"] == "log_line"
    assert [c["gpu_uuid"] for c in check["cards"] if c["listed"]] == [U1, U2]


def test_fake_single_gpu_record_has_no_dual_keys(fake):
    inst = lsi.LlamaServerInstance(fake["tmp"] / "batch", str(fake["binary"]), model_path=str(fake["model"]),
                                   alias="r1-manager", label="DRYRUN", start_timeout=20, gpu_uuid=U1)
    fake["started"].append(inst)
    inst.start(build=lsi.build_info(str(fake["binary"])), model_sha256=lsi.sha256_file(fake["model"]))
    rec = json.loads(inst.record_path.read_text())
    assert not {"gpu_uuids", "tensor_split", "split_mode"} & set(rec)
    assert rec["gpu_uuid"] == U1
