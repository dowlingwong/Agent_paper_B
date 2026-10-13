"""CPU-only checks of the remote launcher's GPU rules.

Since the author's co-tenancy decision of 13 Oct 2026 (PLAN §10), other users' processes
on the selected card are allowed and only logged; a STOP happens on insufficient free
memory or when the pinned model is not fully offloaded.
"""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from xml.etree import ElementTree
import subprocess
import pytest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
SOURCE = Path(os.environ.get('R1_CENSUS_SOURCE', str(SCRIPTS / 'deepthought_batch1_resume.py')))
BUSY = '<nvidia_smi_log><gpu><uuid>card</uuid><processes><process_info><pid>42</pid><used_memory>9000 MiB</used_memory></process_info></processes></gpu></nvidia_smi_log>'
EMPTY = '<nvidia_smi_log><gpu><uuid>card</uuid><processes /></gpu></nvidia_smi_log>'
NAMES = {'gpu_rows', 'gpu_census', 'check_gpu', 'assert_full_offload', 'stamp'}
CONSTANTS = {'MODEL_FOOTPRINT_MIB', 'MARGIN_MIB'}


def load(outputs, tmp_path, loaded=False):
    body = [n for n in ast.parse(SOURCE.read_text()).body
            if (isinstance(n, ast.FunctionDef) and n.name in NAMES)
            or (isinstance(n, ast.Assign) and {getattr(t, 'id', None) for t in n.targets} & CONSTANTS)]
    fake = Mock()
    fake.check_output.side_effect = outputs
    fake.CalledProcessError = subprocess.CalledProcessError
    from datetime import datetime, timezone
    ns = {'subprocess': fake, 'ElementTree': ElementTree, 'json': json, 'BATCH': tmp_path,
          'datetime': datetime, 'timezone': timezone,
          'getpass': SimpleNamespace(getuser=lambda: 'dwong'),
          'state': {'gpu': '0, card, GPU, 100', 'model_loaded': loaded}}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(SOURCE), 'exec'), ns)
    return ns


def csv(free):
    return f'0, card, NVIDIA RTX 6000 Ada Generation, {free}\n'


def test_other_user_on_card_is_allowed_and_logged(tmp_path):
    ns = load([csv(30000), BUSY, 'another_user\n'], tmp_path)
    record = ns['check_gpu']()
    assert record['other_owners_on_selected'] == ['another_user']
    logged = [json.loads(line) for line in (tmp_path / 'gpu_census.jsonl').read_text().splitlines()]
    assert logged[0]['cards'][0]['processes'][0]['owner'] == 'another_user'


def test_exited_pid_is_recorded_without_stop(tmp_path):
    ns = load([csv(30000), BUSY, subprocess.CalledProcessError(1, ['ps'])], tmp_path)
    record = ns['check_gpu']()
    assert record['cards'][0]['processes'][0]['owner'] is None


def test_too_little_memory_before_load_is_a_stop(tmp_path):
    ns = load([csv(7000), EMPTY], tmp_path)  # needs 5304 + 2048 = 7352 MiB
    with pytest.raises(RuntimeError, match='STOP'):
        ns['check_gpu']()


def test_loaded_model_needs_only_the_margin(tmp_path):
    load([csv(3000), BUSY, 'another_user\n'], tmp_path, loaded=True)['check_gpu']()
    with pytest.raises(RuntimeError, match='STOP'):
        load([csv(1000), BUSY, 'another_user\n'], tmp_path, loaded=True)['check_gpu']()


def test_card_selection_filters_by_free_memory(tmp_path):
    rows = '0, a, GPU, 7000\n1, b, GPU, 30000\n'
    all_rows, eligible = load([rows], tmp_path)['gpu_rows']()
    assert len(all_rows) == 2 and [r.split(',')[1].strip() for r in eligible] == ['b']


def test_partial_or_missing_offload_is_a_stop(tmp_path):
    check = load([], tmp_path)['assert_full_offload']
    check({'size': 5560907776, 'size_vram': 5560907776}, 'probe')
    for bad in (None, {'size': 10, 'size_vram': 0}, {'size': 10, 'size_vram': 6}):
        with pytest.raises(RuntimeError, match='STOP'):
            check(bad, 'probe')


def test_dt4_rerun_entrypoint_uses_shared_dt4_and_resident_model():
    source = SOURCE.read_text()
    tree = ast.parse(source)
    order = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    assert order.index('run_dt4') < order.index('main')
    rerun = (SCRIPTS / 'ada_rerun_dt4.py').read_text()
    ast.parse(rerun)
    assert 'run_dt4(meta, version)' in rerun and 'OLLAMA_KEEP_ALIVE=-1' in rerun
    assert 'no shared-card launch' not in source and 'another user process' not in source
