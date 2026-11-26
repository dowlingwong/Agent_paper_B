"""Exact exam server flags: ``-lv 4`` restores route (i) offload evidence.

The pinned llama.cpp build (620d222, v0.7.0-dev) prints
``load_tensors: offloaded N/N layers to GPU`` only at verbosity >= 4; at the default
verbosity the offload check can only use the stricter route (ii) process-memory
floor, which stopped the first cooperative Stage A attempt (5782 MiB measured on a
new instance vs 5784 MiB pinned by its own qualification).  These tests pin the
flag and the log shape that route (i) depends on; no GPU or model is used.
"""
import json

from r1.exam import qualify as q
from r1.exam.runtime import EXAM_SERVER_ARGS
from r1.scripts import llama_server_instance as lsi

REAL_LV4_LOG = (
    "0.00.010.423 I cmn  common_param: common_params_print_info: verbosity = 4 (adjust with the `-lv N` CLI arg)\n"
    "0.00.433.602 I load_tensors: offloading output layer to GPU\n"
    "0.00.433.604 I load_tensors: offloading 27 repeating layers to GPU\n"
    "0.00.433.604 I load_tensors: offloaded 29/29 layers to GPU\n"
    "0.00.433.608 I load_tensors:   CPU_Mapped model buffer size =   292.36 MiB\n"
    "0.00.433.609 I load_tensors:        CUDA0 model buffer size =  4168.09 MiB\n"
    "0.00.738.607 I llama_kv_cache:      CUDA0 KV buffer size =   952.00 MiB\n"
)


def test_exam_server_args_request_route_one_evidence():
    assert EXAM_SERVER_ARGS[:5] == ['--jinja', '--cache-type-k', 'q8_0', '--cache-type-v', 'q8_0']
    assert EXAM_SERVER_ARGS[-2:] == ['-lv', '4']
    assert EXAM_SERVER_ARGS.count('-lv') == 1


def test_real_lv4_log_passes_route_one_even_below_the_old_memory_floor():
    check = lsi.offload_check(REAL_LV4_LOG, pid=7, gpu_uuid='GPU-x', footprint_mib=5784,
                              apps=[{'pid': 7, 'gpu_uuid': 'GPU-x', 'used_mib': 5782}])
    assert check['full'] and check['route'] == 'log_line'
    assert check['offloaded_layers'] == 29 and check['total_layers'] == 29
    assert check['gpu_model_buffers'] and check['kv_buffers']


def test_partial_route_one_line_still_stops():
    log = REAL_LV4_LOG.replace('offloaded 29/29', 'offloaded 28/29')
    check = lsi.offload_check(log, pid=7, gpu_uuid='GPU-x', footprint_mib=1, apps=[])
    assert not check['full'] and check['route'] is None


def test_qualification_passes_the_same_pinned_args_to_the_probe(tmp_path, monkeypatch):
    from r1.exam import cache_runtime
    captured = {}

    def probe_main(argv):
        captured['argv'] = argv
        (tmp_path / 'probe_fixture.json').write_text(json.dumps({'footprint_mib_to_pin': 123.0}))
        return 0

    monkeypatch.setattr(q.llamacpp_probe, 'main', probe_main)
    monkeypatch.setattr(q, 'free_port', lambda: 18481)
    monkeypatch.setattr(q.lsi, 'gpu_compute_apps', lambda: [])
    token = cache_runtime._authorized.set(True)
    try:
        result = q.qualify({'config': {'server': {'binary': 'fixture', 'build': 'fixture',
                                                  'binary_sha256': '0' * 64},
                                       'gpu_uuid': 'GPU-x'},
                            'candidate': {'id': 'fixture', 'thinking_policy': {'mode': 'off'},
                                          'runtime': {'model_path': 'fixture.gguf'},
                                          'quant_source': {'size_bytes': 100, 'sha256': '0' * 64}},
                            'out': str(tmp_path), 'ctx': 32768})
    finally:
        cache_runtime._authorized.reset(token)
    argv = captured['argv']
    assert '--server-extra-args' in argv
    assert json.loads(argv[argv.index('--server-extra-args') + 1]) == EXAM_SERVER_ARGS
    assert result['status'] == 'PASS'
