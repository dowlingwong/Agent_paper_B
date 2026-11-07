"""Candidate-only tmp_path fixture; it does not make pytest deletion-free.

Select explicitly only after independent review and a reviewed execution plan.
All filesystem paths are test-owned. No cleanup or retention pruning is done.
"""
import os
import stat
import uuid
from pathlib import Path

import pytest


def _identity(st):
    return (st.st_dev, st.st_ino, st.st_uid, stat.S_IFMT(st.st_mode))


def _open_empty_root(raw):
    if not raw or not os.path.isabs(raw) or os.path.normpath(raw) != raw:
        raise RuntimeError('STOP: fixture root must be a normalized absolute path')
    if os.path.realpath(raw) != raw:
        raise RuntimeError('STOP: fixture root has a symlinked or ambiguous ancestor')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(raw, flags)
    try:
        opened = os.fstat(fd)
        named = os.lstat(raw)
        if (not stat.S_ISDIR(opened.st_mode) or opened.st_uid != os.getuid()
                or stat.S_IMODE(opened.st_mode) != 0o700 or _identity(opened) != _identity(named)):
            raise RuntimeError('STOP: fixture root is not the named, private owned directory')
        if os.listdir(fd):
            raise RuntimeError('STOP: fixture root is not empty')
        return fd, _identity(opened)
    except BaseException:
        os.close(fd)
        raise


def _create_fixture_dir(raw, fd, expected):
    opened = os.fstat(fd)
    named = os.lstat(raw)
    if (os.path.realpath(raw) != raw or _identity(opened) != expected or _identity(named) != expected
            or stat.S_IMODE(opened.st_mode) != 0o700 or stat.S_IMODE(named.st_mode) != 0o700):
        raise RuntimeError('STOP: fixture root identity or pathname changed')
    name = 'test_' + uuid.uuid4().hex
    os.mkdir(name, mode=0o700, dir_fd=fd)
    return Path(raw) / name


@pytest.fixture(scope='session')
def b1_preserved_fixture_root():
    """Require a pre-created, private, empty root; retain everything on exit."""
    raw = os.environ.get('B1_PRESERVE_TEST_ROOT', '')
    fd, identity = _open_empty_root(raw)
    try:
        yield raw, fd, identity
    finally:
        os.close(fd)


@pytest.fixture
def tmp_path(b1_preserved_fixture_root):
    raw, fd, identity = b1_preserved_fixture_root
    return _create_fixture_dir(raw, fd, identity)


@pytest.fixture
def tmp_path_factory():
    raise RuntimeError('STOP: tmp_path_factory is outside the preservation fixture scope')


@pytest.fixture
def tmpdir():
    raise RuntimeError('STOP: tmpdir is outside the preservation fixture scope')


@pytest.fixture
def tmpdir_factory():
    raise RuntimeError('STOP: tmpdir_factory is outside the preservation fixture scope')


@pytest.fixture
def capfd():
    raise RuntimeError('STOP: fd capture is outside the preservation fixture scope')


@pytest.fixture
def capfdbinary():
    raise RuntimeError('STOP: binary fd capture is outside the preservation fixture scope')
