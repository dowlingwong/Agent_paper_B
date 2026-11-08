"""Synthetic stat-only checks; no anchor results or audit values are read."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def module():
    path = Path(__file__).parents[2] / 'docs/r1/proposals/B1_STOP_ANCHOR_METADATA_20261108.py'
    spec = importlib.util.spec_from_file_location('b1_stop_metadata_synthetic', path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def test_only_metadata_no_content_open(tmp_path, module):
    root = tmp_path / 'out'; node = root / 'a/b1/off/node__s9001'; node.mkdir(parents=True)
    (root / 'a/b1_manifest.json').write_text('SYNTHETIC SENTINEL NOT TO BE READ')
    (node / 'campaign_manifest.json').write_text('FORBIDDEN_SYNTHETIC_AUDIT_VALUE')
    output = io.StringIO()
    real_os_open = os.open
    def directories_only(path, flags, *args, **kwargs):
        assert flags & os.O_DIRECTORY, 'only directory descriptors may be opened'
        return real_os_open(path, flags, *args, **kwargs)
    with patch('builtins.open', side_effect=AssertionError('file content access forbidden')), \
         patch.object(module.os, 'open', side_effect=directories_only), contextlib.redirect_stdout(output):
        module.inspect(str(root), ('a',), ('node',), (9001,))
    text = output.getvalue()
    assert 'SYNTHETIC SENTINEL' not in text and 'FORBIDDEN_SYNTHETIC_AUDIT_VALUE' not in text
    assert 'accessible_root_directories 1' in text and 'regular_candidate_manifests 1' in text
    assert 'AUDIT_FAILURE_COUNTS NOT_CHECKABLE' in text


def test_symlinked_root_directory_not_followed(tmp_path, module):
    root = tmp_path / 'out'; root.mkdir(); elsewhere = tmp_path / 'elsewhere'; elsewhere.mkdir()
    (root / 'a').symlink_to(elsewhere, target_is_directory=True)
    output = io.StringIO()
    with contextlib.redirect_stdout(output): module.inspect(str(root), ('a',), ('node',), (9001,))
    assert 'DIRECTORY a NOT_CHECKABLE' in output.getvalue()
    assert 'accessible_root_directories 0' in output.getvalue()


def test_symlinked_file_not_followed(tmp_path, module):
    root = tmp_path / 'out'; node = root / 'a/b1/off/node__s9001'; node.mkdir(parents=True)
    secret = tmp_path / 'secret'; secret.write_text('SYNTHETIC SECRET')
    (node / 'campaign_manifest.json').symlink_to(secret)
    output = io.StringIO()
    with contextlib.redirect_stdout(output): module.inspect(str(root), ('a',), ('node',), (9001,))
    assert 'NONREGULAR_NOT_CHECKABLE' in output.getvalue()
    assert 'SYNTHETIC SECRET' not in output.getvalue()
