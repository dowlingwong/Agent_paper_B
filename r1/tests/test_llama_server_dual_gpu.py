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
        # Fail rather than skip: the single-GPU identity check must not vanish in a shallow clone
        # (retarget BASE_COMMIT when this change is rebased).
        pytest.fail(f"base commit {BASE_COMMIT} not available for the single-GPU identity check")
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


def test_single_gpu_argv_literal(tmp_path):
    """Independent of git: the single-GPU argv as written down at the base commit."""
    assert make(tmp_path, gpu_uuid=U1).argv == [
        "/opt/llama-server", "-m", "/m/x.gguf", "--host", "127.0.0.1", "--port", "8123",
        "-ngl", "999", "-c", "8192", "--alias", "r1-manager", "-np", "1"]
    env, _ = make(tmp_path, gpu_uuid=U1).env()
    assert env["CUDA_VISIBLE_DEVICES"] == U1
    # the single path does not apply the dual checks (unchanged behaviour)
    assert make(tmp_path, gpu_uuid="0", extra_args=["--main-gpu", "0"]).argv[-2:] == ["--main-gpu", "0"]


@pytest.mark.parametrize("uuids", [["0", "1"], [" GPU-1111", "GPU-2222"], ["GPU-1111 ", "GPU-2222"],
                                   ["GPU-1111", "gpu-2222"], ["GPU-", "GPU-2222"], ["GPU-1111", "MIG-"],
                                   ["GPU-11/11", "GPU-2222"], [1, "GPU-2222"]])
def test_dual_requires_exact_gpu_or_mig_uuids(tmp_path, uuids):
    with pytest.raises(ValueError, match="GPU-/MIG- uuids"):
        make(tmp_path, gpu_uuids=uuids, tensor_split=[1, 1])


def test_dual_accepts_mig_uuids(tmp_path):
    inst = make(tmp_path, gpu_uuids=["MIG-6f2a1b3c-0d4e-5f60-7a8b-9c0d1e2f3a4b", U2], tensor_split=[1, 1])
    assert inst.env()[0]["CUDA_VISIBLE_DEVICES"].startswith("MIG-")


@pytest.mark.parametrize("extra", [["--tensor-split", "3,1"], ["-ts", "3,1"], ["--split-mode", "row"],
                                   ["-sm", "row"], ["--main-gpu", "1"], ["-mg", "1"], ["--device", "CUDA0"],
                                   ["-dev", "CUDA0"], ["--tensor-split=3,1"], ["--jinja", "--split-mode=row"]])
def test_dual_refuses_conflicting_extra_args(tmp_path, extra):
    with pytest.raises(ValueError, match="may not override"):
        make(tmp_path, gpu_uuids=[U1, U2], tensor_split=[1, 1], extra_args=extra)


def test_dual_refuses_env_device_override(tmp_path):
    with pytest.raises(ValueError, match="CUDA_VISIBLE_DEVICES"):
        make(tmp_path, gpu_uuids=[U1, U2], tensor_split=[1, 1], env_extra={"CUDA_VISIBLE_DEVICES": "0"})
    ok = make(tmp_path, gpu_uuids=[U1, U2], tensor_split=[1, 1], env_extra={"GGML_CUDA_X": "1"})
    assert ok.env()[0]["CUDA_VISIBLE_DEVICES"] == f"{U1},{U2}"


def test_tensor_split_text_round_trips():
    assert lsi.tensor_split_arg([1, 1]) == "1,1"
    assert lsi.tensor_split_arg([0.6, 0.4]) == "0.6,0.4"
    text = lsi.tensor_split_arg([1234567, 0.123456789])
    assert text == "1234567,0.123456789"
    assert [float(x) for x in text.split(",")] == [1234567, 0.123456789]


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


def test_dual_route_i_reads_only_the_last_load_of_a_reused_log():
    old_load = ("llama_model_loader: loaded meta data with 30 key-value pairs\n" + DUAL_LOG)
    new_load = ("llama_model_loader: loaded meta data with 30 key-value pairs\n"
                "load_tensors: offloaded 29/29 layers to GPU\n"
                "load_tensors:        CUDA0 model buffer size =  4168.09 MiB\n")
    check = lsi.offload_check_dual(old_load + new_load, pid=77, gpu_uuids=[U1, U2], footprint_mib=None, apps=[])
    assert not check["full"] and check["model_buffer_devices"] == ["CUDA0"]
    assert lsi.offload_check_dual(new_load + old_load, pid=77, gpu_uuids=[U1, U2], footprint_mib=None,
                                  apps=[])["full"]


WARN = "ggml_cuda_init: failed to initialize CUDA: no CUDA-capable device is detected\n"
META = "llama_model_loader: loaded meta data with 30 key-value pairs\n"


def test_dual_cpu_fallback_before_the_load_markers_is_still_a_stop():
    """Review round 2, finding 1: llama.cpp prints fallback warnings at startup, before the meta line."""
    full_line = lsi.offload_check_dual(WARN + META + DUAL_LOG, pid=77, gpu_uuids=[U1, U2], footprint_mib=None,
                                       apps=rows((U1, 2600), (U2, 2600)))
    assert not full_line["full"] and full_line["cpu_fallback_lines"] and "CPU fallback reported" in full_line["reasons"]
    silent = lsi.offload_check_dual(WARN + META + "llama_server: model loaded\n", pid=77, gpu_uuids=[U1, U2],
                                    footprint_mib=[1, 1], apps=rows((U1, 2600), (U2, 2600)))
    assert not silent["full"] and silent["route"] is None
    assert lsi.offload_check_dual(META + DUAL_LOG, pid=77, gpu_uuids=[U1, U2], footprint_mib=None,
                                  apps=rows((U1, 2600), (U2, 2600)))["full"]


def test_dual_later_load_with_only_an_offloading_line_drops_the_earlier_buffers():
    """Review round 2, note 2: cut at whichever load marker comes last."""
    later = ("load_tensors: offloading 29 repeating layers to GPU\n"
             "load_tensors: offloaded 29/29 layers to GPU\n"
             "load_tensors:        CUDA0 model buffer size =  4168.09 MiB\n")
    check = lsi.offload_check_dual(META + DUAL_LOG + later, pid=77, gpu_uuids=[U1, U2], footprint_mib=None, apps=[])
    assert not check["full"] and check["model_buffer_devices"] == ["CUDA0"]


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
    assert rec["tensor_split_arg"] == "1,1" and rec["log_offset"] == 0
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


def test_fake_two_gpu_restart_with_a_reused_log_cannot_pass_on_the_old_load(fake, monkeypatch):
    """Same port and generation, log opened for appending: a two-card load already in the log must
    not prove a new load that prints no offload line (the deepthought build's default)."""
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    batch = fake["tmp"] / "batch"
    batch.mkdir()
    (batch / f"llama_server_{port}.log").write_text(
        "llama_model_loader: loaded meta data with 30 key-value pairs\n" + DUAL_LOG)
    monkeypatch.setenv("C3_FAKE_LLAMA_OFFLOAD", "silent")
    inst = lsi.LlamaServerInstance(batch, str(fake["binary"]), model_path=str(fake["model"]),
                                   alias="r1-manager", label="DRYRUN", start_timeout=20, port=port,
                                   gpu_uuids=[U1, U2], tensor_split=[1, 1])
    fake["started"].append(inst)
    inst.start(build=lsi.build_info(str(fake["binary"])), model_sha256=lsi.sha256_file(fake["model"]))
    assert inst.log_offset > 0
    check = inst.offload(apps=[])
    assert not check["full"] and check["route"] is None and check["model_buffer_devices"] == []


@pytest.mark.parametrize("extra", [["-ot", "blk.*=CPU"], ["--override-tensor=exps=CPU"], ["--cpu-moe"], ["--n-cpu-moe", "4"]])
def test_dual_refuses_cpu_placement_flags(tmp_path, extra):
    with pytest.raises(ValueError, match="override"):
        lsi.validate_dual(None, [U1, U2], [1, 1], extra_args=extra)


def test_dual_refuses_llama_arg_env(tmp_path):
    with pytest.raises(ValueError, match="LLAMA_ARG_"):
        lsi.validate_dual(None, [U1, U2], [1, 1], env_extra={"LLAMA_ARG_N_GPU_LAYERS": "0"})
