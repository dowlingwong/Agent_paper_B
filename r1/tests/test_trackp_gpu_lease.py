import contextlib
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from r1.c3.train import run as R


GPU_0 = "GPU-00000000-0000-0000-0000-000000000000"
GPU_2 = "GPU-22222222-2222-2222-2222-222222222222"


@pytest.fixture
def lease_world(tmp_path, monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    cards = {"0": GPU_0, "2": GPU_2}
    state = {"processes": f"{GPU_0}, 9020, 1234\n", "query_failed": False, "samples": 0,
             "cuda_uuid": GPU_2}

    def nvidia_smi(argv, **kwargs):
        if argv[0] == sys.executable:
            assert argv[1] == "-c"
            return subprocess.CompletedProcess(argv, 0, state["cuda_uuid"], "")
        assert argv[0] == "nvidia-smi"
        if argv[1] == "--query-gpu=index,uuid":
            selected = next((arg.split("=", 1)[1] for arg in argv if arg.startswith("--id=")), None)
            rows = [f"{i}, {uuid}" for i, uuid in cards.items() if selected in (None, i, uuid)]
            return subprocess.CompletedProcess(argv, 0, "\n".join(rows), "")
        assert argv[1] == "--query-compute-apps=gpu_uuid,pid,used_memory"
        assert argv[2] in (f"--id={GPU_0}", f"--id={GPU_2}")
        state["samples"] += 1
        return subprocess.CompletedProcess(argv, int(state["query_failed"]), state["processes"], "")

    def assert_cuda_mask(uuid):
        assert os.environ["CUDA_VISIBLE_DEVICES"] == uuid

    monkeypatch.setattr(R.subprocess, "run", nvidia_smi)
    monkeypatch.setattr(R, "_check_cuda_card", assert_cuda_mask)
    options = dict(lock_path=tmp_path / "gpu0.lock", log_path=tmp_path / "lease.jsonl",
                   marker_path=tmp_path / "marker", status_text="", run_log=[])
    return state, cards, options


@pytest.mark.parametrize("selector", [2, "2", GPU_2])
def test_lease_checks_selected_card_only_and_logs_count_and_memory(lease_world, selector):
    state, _, options = lease_world
    with R.gpu_lease("smoke", gpu=selector, **options) as lease:
        assert lease["gpu_uuid"] == os.environ["CUDA_VISIBLE_DEVICES"] == GPU_2
        with options["lock_path"].with_name("gpu2.lock").open("a") as locked:
            with pytest.raises(BlockingIOError):
                fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state["processes"] += f"{GPU_2}, {os.getpid()}, 10\n{GPU_2}, 9015, 48\n{GPU_2}, 9016, 12\n"
    assert "CUDA_VISIBLE_DEVICES" not in os.environ
    assert not options["lock_path"].exists()
    start, end = options["run_log"]
    assert [start["gpu_index"], end["gpu_index"]] == [2, 2]
    assert start["other_processes"] == {"count": 0, "memory_mib": 0}
    assert end["other_processes"] == {"count": 2, "memory_mib": 60}
    log = options["log_path"].read_text()
    assert [json.loads(line) for line in log.splitlines()] == options["run_log"]
    assert '"pid": 9015' not in log and '"pid": 9020' not in log


def test_selected_card_busy_and_its_existing_lease_both_refuse(lease_world):
    state, _, options = lease_world
    with options["lock_path"].with_name("gpu2.lock").open("a") as locked:
        fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(R.TrackPStop, match="held by another job"):
            with R.gpu_lease("smoke", gpu="2", **options):
                pytest.fail("entered another job's lease")
    assert state["samples"] == 0
    with pytest.raises(R.TrackPStop, match="needs to be empty") as stop:
        with R.gpu_lease("smoke", gpu="0", **options):
            pytest.fail("entered an occupied card")
    assert "9020" not in str(stop.value)
    assert not options["run_log"]


def test_automatic_single_device_and_scheduler_local_ordinal(lease_world, monkeypatch):
    _, cards, options = lease_world
    with pytest.raises(R.TrackPStop, match="exactly one"):
        with R.gpu_lease("ambiguous", **options):
            pytest.fail("leased without selecting a card on a multi-GPU host")
    del cards["0"]
    with R.gpu_lease("single visible card", **options) as lease:
        assert lease["gpu_index"] == 2
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    with R.gpu_lease("isolated slot", **options) as lease:
        assert lease["gpu_index"] == 2
        assert os.environ["CUDA_VISIBLE_DEVICES"] == GPU_2
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "0"


def test_inherited_cuda_index_is_probed_instead_of_treating_it_as_physical(lease_world, monkeypatch):
    state, _, options = lease_world
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    with R.gpu_lease("CUDA ordinal 0", **options) as lease:
        assert lease["gpu_index"] == 2
    with pytest.raises(R.TrackPStop, match="disagrees with CUDA_VISIBLE_DEVICES"):
        with R.gpu_lease("physical index 0", gpu=0, **options):
            pytest.fail("replaced the CUDA-masked card with the NVML index")
    state["cuda_uuid"] = "unavailable"
    with pytest.raises(R.TrackPStop, match="cannot resolve"):
        with R.gpu_lease("unresolved CUDA ordinal", **options):
            pytest.fail("guessed a GPU for an unresolved CUDA ordinal")


def test_scoped_query_refuses_malformed_records(lease_world):
    state, _, options = lease_world
    state["processes"] = "unidentified record\n"
    with pytest.raises(R.TrackPStop, match="invalid process record"):
        with R.gpu_lease("unknown occupancy", gpu=2, **options):
            pytest.fail("ignored a record from a card-scoped query")


@pytest.mark.parametrize("prefix", ["", "GPU-"])
def test_cuda_runtime_must_match_the_leased_uuid(monkeypatch, prefix):
    cuda = SimpleNamespace(device_count=lambda: 1, get_device_properties=lambda _: SimpleNamespace(
        uuid=prefix + GPU_2.removeprefix("GPU-"),
    ))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda))
    R._check_cuda_card(GPU_2)
    with pytest.raises(R.TrackPStop, match="exactly the leased GPU"):
        R._check_cuda_card(GPU_0)
    cuda.device_count = lambda: 2
    with pytest.raises(R.TrackPStop, match="exactly the leased GPU"):
        R._check_cuda_card(GPU_2)


def test_mask_mismatch_refuses_and_end_query_failure_is_recorded(lease_world, monkeypatch):
    state, _, options = lease_world
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", GPU_0)
    with pytest.raises(R.TrackPStop, match="disagrees with CUDA_VISIBLE_DEVICES"):
        with R.gpu_lease("mismatch", gpu="2", **options):
            pytest.fail("expanded the caller's CUDA mask")

    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", GPU_2)
    with pytest.raises(RuntimeError, match="job failure"):
        with R.gpu_lease("smoke", **options):
            state["query_failed"] = True
            raise RuntimeError("job failure")
    assert "error" in options["run_log"][-1]["other_processes"]
    assert os.environ["CUDA_VISIBLE_DEVICES"] == GPU_2
    with options["lock_path"].with_name("gpu2.lock").open("a") as unlocked:
        fcntl.flock(unlocked, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_no_success_without_end_count_and_memory(lease_world):
    state, _, options = lease_world
    with pytest.raises(R.TrackPStop, match="end occupancy could not be recorded"):
        with R.gpu_lease("smoke", gpu=2, **options):
            state["processes"] = f"{GPU_2}, 9015, [N/A]\n"
    assert options["run_log"][-1]["other_processes"] == {
        "error": "nvidia-smi did not report process memory for the selected GPU",
    }
    assert "CUDA_VISIBLE_DEVICES" not in os.environ


def test_ada_e0_uses_host_lock_for_standalone_and_job_lock_for_direct(tmp_path, monkeypatch):
    from r1.scripts import trackp

    @contextlib.contextmanager
    def capture_lease(job, **kwargs):
        yield kwargs

    monkeypatch.setattr(R, "gpu_lease", capture_lease)
    monkeypatch.setattr(R, "check_environment", lambda cfg: None)
    monkeypatch.delenv("P4_LEASED_GPU_UUID", raising=False)
    args = SimpleNamespace(tiny=False, cmd="e0", base="kev-0.8b", gpu="2", cfg={
        "lease": "direct_gpu_lease", "gpu": {"lock_path": "gpu0.lock"}, "runs_dir": str(tmp_path),
        "direct": {"lock_dir": str(tmp_path / "host-locks")},
    })
    with trackp._lease(args, []) as local:
        assert local["check_processes"] and local["gpu"] == "2"
        assert local["lock_path"] == tmp_path / "host-locks" / "gpu0.lock"
    args.gpu = None
    with pytest.raises(R.TrackPStop, match="select an empty card"):
        with trackp._lease(args, []):
            pytest.fail("entered standalone work without a host lease")

    monkeypatch.setenv("P4_LEASED_GPU_UUID", GPU_2)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", GPU_2)
    with trackp._lease(args, []) as staged:
        assert not staged["check_processes"] and staged["lock_path"] == Path("gpu0.lock")
    monkeypatch.setenv("P4_LEASED_GPU_UUID", "0")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    with pytest.raises(R.TrackPStop, match="outer card lease"):
        with trackp._lease(args, []):
            pytest.fail("accepted an invalid outer GPU UUID")
    monkeypatch.setenv("P4_LEASED_GPU_UUID", GPU_2)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", GPU_2)
    args.gpu = "2"
    with pytest.raises(R.TrackPStop, match="outer card lease"):
        with trackp._lease(args, []):
            pytest.fail("attempted to reselect an externally leased card")
