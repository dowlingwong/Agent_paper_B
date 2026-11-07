"""Candidate pytest tmp_path override for isolated no-deletion test runs.

Unreviewed and not a full-suite deletion guard: it does not cover tmp_path_factory,
subprocesses, package finalizers, pytest internals or indirect cleanup.  The caller
must create a new empty directory exclusively, then set R1_TEST_PRESERVE_TMP_ROOT.
"""
from __future__ import annotations

import os
from pathlib import Path
import stat
import uuid

import pytest


def _fixture_root() -> Path:
    raw = os.environ.get('R1_TEST_PRESERVE_TMP_ROOT', '')
    if not raw or not Path(raw).is_absolute():
        raise RuntimeError('preservation fixture requires an absolute root')
    root = Path(raw)
    st = root.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid():
        raise RuntimeError('preservation fixture root must be an owned directory')
    return root


@pytest.fixture
def tmp_path():
    """Create one fresh owned directory without pytest's numbered symlinks."""
    root = _fixture_root()
    path = root / ('case_' + uuid.uuid4().hex)
    path.mkdir(mode=0o700)  # fails closed on collision; no cleanup or retry
    return path
