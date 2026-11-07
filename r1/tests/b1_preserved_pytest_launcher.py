"""Unaccepted local pytest launcher candidate; do not use to run tests yet.

A fixed capture mode must reach pytest before its initial-conftest hooks.
The caller supplies only individually reviewed exact test node IDs. This does
not establish safe behavior of tests, native code, child processes or pytest.
"""
import hashlib
import os
import re
import sys
from pathlib import Path

_EXPECTED_PYTHON = '/Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python'
_SITE = Path('/Users/wongdowling/Documents/autoresearch_harness/.venv/lib/python3.11/site-packages')
_EXPECTED_FILES = {
    '_pytest/tmpdir.py': 'b25a80db25476cfd9d58e7c80e8962ac9e39ca628369a1db789a9c81a2261dd9',
    '_pytest/fixtures.py': 'eff80aa15502a5fa38b022f2dd3d3ba760efff16b9c761e7283299bbcf380de6',
    '_pytest/capture.py': '92e96e989751747bbbce8a2c3abe257c747471ee8bb0eb616aef41cabc3cc55e',
    '_pytest/config/__init__.py': '2ea44f1539ed6b72eb61402d4633b92e9fef99895c41ac6347860690516e46cf',
}
_NODE = re.compile(r'r1/tests/test_[A-Za-z0-9_]+\.py(?:::[A-Za-z_][A-Za-z0-9_]*){1,2}(?:\[[A-Za-z0-9_][A-Za-z0-9_.,=+\-]*\])?\Z')


def _validate_environment(environ):
    unexpected = sorted(key for key in environ if key.startswith('PYTEST_')
                        and key != 'PYTEST_DISABLE_PLUGIN_AUTOLOAD')
    if unexpected:
        raise RuntimeError('STOP: unexpected pytest environment: ' + ', '.join(unexpected))
    if environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD') != '1':
        raise RuntimeError('STOP: pytest plugin autoload must be disabled before interpreter startup')


def _fixed_args(root, selectors):
    if not selectors or len(set(selectors)) != len(selectors):
        raise RuntimeError('STOP: provide distinct reviewed exact test node IDs')
    if any(not _NODE.fullmatch(selector) for selector in selectors):
        raise RuntimeError('STOP: invalid or non-exact test node ID')
    return ['-s', '-p', 'no:cacheprovider', '--noconftest',
            '-c', str(root / 'r1/tests/b1_pytest_launcher_20261107.ini'),
            '--rootdir', str(root),
            '-p', 'r1.tests.b1_preserved_tmp_plugin',
            '-p', 'r1.tests.b1_pytest_session_guard', *selectors]


def main(selectors):
    if (not sys.flags.isolated or not sys.flags.no_site or not sys.flags.dont_write_bytecode
            or sys.version_info[:2] != (3, 11)
            or os.path.abspath(sys.executable) != _EXPECTED_PYTHON):
        raise RuntimeError('STOP: start the qualified virtualenv interpreter with -I -S -B')
    _validate_environment(os.environ)
    root = Path(__file__).resolve().parents[2]
    if Path.cwd() != root:
        raise RuntimeError('STOP: launcher must run from its checkout root')
    config = root / 'r1/tests/b1_pytest_launcher_20261107.ini'
    if config.is_symlink() or config.read_bytes() != b'[pytest]\n':
        raise RuntimeError('STOP: launcher pytest configuration changed')
    for relative, expected in _EXPECTED_FILES.items():
        source = _SITE / relative
        if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise RuntimeError('STOP: pinned pytest source changed: ' + relative)
    arguments = _fixed_args(root, selectors)
    # -I removes the checkout and -S omits site-packages. Add only the reviewed
    # checkout and the site path after all option and environment checks.
    sys.path.insert(0, str(root))
    sys.path.insert(1, str(_SITE))
    import pytest
    if pytest.__version__ != '9.0.3':
        raise RuntimeError('STOP: pytest version differs from reviewed source')
    return pytest.main(arguments)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
