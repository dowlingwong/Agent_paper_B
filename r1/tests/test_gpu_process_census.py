"""CPU-only checks of the remote launcher's GPU ownership census."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from xml.etree import ElementTree
import subprocess
import pytest

SOURCE = Path(os.environ.get('R1_CENSUS_SOURCE', str(Path(__file__).parents[1] / 'scripts/deepthought_batch1_resume.py')))
BUSY = '<nvidia_smi_log><gpu><uuid>card</uuid><processes><process_info><pid>42</pid></process_info></processes></gpu></nvidia_smi_log>'
EMPTY = '<nvidia_smi_log><gpu><uuid>card</uuid><processes /></gpu></nvidia_smi_log>'


def checker(outputs):
    func = next(n for n in ast.parse(SOURCE.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'check_gpu')
    fake = Mock()
    fake.check_output.side_effect = outputs
    fake.CalledProcessError = subprocess.CalledProcessError
    namespace = {'subprocess': fake, 'ElementTree': ElementTree,
                 'getpass': SimpleNamespace(getuser=lambda: 'dwong'), 'state': {'gpu': '0, card, GPU, 100'}}
    exec(compile(ast.Module(body=[func], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace['check_gpu']


def test_exited_pid_must_be_absent_from_fresh_gpu_census():
    checker([BUSY, subprocess.CalledProcessError(1, ['ps']), EMPTY, EMPTY])()


def test_unidentified_pid_still_on_card_is_rejected():
    with pytest.raises(RuntimeError, match='STOP'):
        checker([BUSY, subprocess.CalledProcessError(1, ['ps']), BUSY])()


def test_other_user_on_card_is_rejected():
    with pytest.raises(RuntimeError, match='STOP'):
        checker([BUSY, 'another_user\n'])()
