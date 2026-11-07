"""Unaccepted pytest 9.0.3 guard candidate; not a safe-suite authorization.

The separately reviewed command and selected tests must establish the rest of
process, native-library and fixture behavior before any pytest execution.
"""
import hashlib
import os
from pathlib import Path

import pytest

_TMPDIR_SHA256 = 'b25a80db25476cfd9d58e7c80e8962ac9e39ca628369a1db789a9c81a2261dd9'
_BLOCKED = frozenset(('tmp_path_factory', 'tmpdir', 'tmpdir_factory', 'capfd', 'capfdbinary'))
_FACTORY_INSTALLED = False


def _refuse_factory(*args, **kwargs):
    raise RuntimeError('STOP: pytest temporary factory is outside preservation scope')


def _install_factory_guard(module):
    """Replace the pinned factory methods before pytest's configure hook."""
    global _FACTORY_INSTALLED
    path = Path(module.__file__).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest() != _TMPDIR_SHA256:
        raise RuntimeError('STOP: pytest tmpdir source differs from reviewed version')
    factory = module.TempPathFactory
    factory.getbasetemp = _refuse_factory
    factory.mktemp = _refuse_factory
    _FACTORY_INSTALLED = True


def _require_selected(fixturedef, helper):
    name = fixturedef.argname
    if name in _BLOCKED:
        raise RuntimeError('STOP: unreviewed fixture selected: ' + name)
    if name == 'tmp_path':
        expected = helper.tmp_path._get_wrapped_function()
        if fixturedef.func is not expected:
            raise RuntimeError('STOP: tmp_path was shadowed by another fixture')
    if name == 'b1_preserved_fixture_root':
        expected = helper.b1_preserved_fixture_root._get_wrapped_function()
        if fixturedef.func is not expected:
            raise RuntimeError('STOP: retained fixture root was shadowed')


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):
    if os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD') != '1':
        raise RuntimeError('STOP: pytest plugin autoload must be disabled before startup')
    if os.environ.get('PYTEST_ADDOPTS') or os.environ.get('PYTEST_PLUGINS'):
        raise RuntimeError('STOP: pytest environment options and plugins must be absent')
    import _pytest.tmpdir as tmpdir
    _install_factory_guard(tmpdir)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    if not _FACTORY_INSTALLED:
        raise RuntimeError('STOP: temporary factory guard was not installed early')
    if config.getoption('capture') != 'no' or config.getoption('basetemp') is not None:
        raise RuntimeError('STOP: global capture or explicit basetemp is not allowed')
    if config.pluginmanager.hasplugin('cacheprovider'):
        raise RuntimeError('STOP: pytest cacheprovider is not allowed')
    from r1.tests import b1_preserved_tmp_plugin as helper
    if config.pluginmanager.get_plugin(helper.__name__) is not helper:
        raise RuntimeError('STOP: reviewed preserved fixture plugin is not registered')
    factory = config._tmp_path_factory
    if factory._basetemp is not None:
        raise RuntimeError('STOP: pytest temporary factory was already activated')


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    from r1.tests import b1_preserved_tmp_plugin as helper
    for item in items:
        info = getattr(item, '_fixtureinfo', None)
        if info is None:
            raise RuntimeError('STOP: fixture closure unavailable for ' + item.nodeid)
        for name, definitions in info.name2fixturedefs.items():
            if name in _BLOCKED or name in ('tmp_path', 'b1_preserved_fixture_root'):
                if not definitions:
                    raise RuntimeError('STOP: fixture definition unavailable: ' + name)
                _require_selected(definitions[-1], helper)


@pytest.hookimpl(tryfirst=True)
def pytest_fixture_setup(fixturedef, request):
    from r1.tests import b1_preserved_tmp_plugin as helper
    _require_selected(fixturedef, helper)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    if session.config._tmp_path_factory._basetemp is not None:
        raise RuntimeError('STOP: pytest temporary factory became active; retain scene')
