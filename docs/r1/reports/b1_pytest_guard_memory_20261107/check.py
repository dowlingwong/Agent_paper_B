"""Extract guard functions and exercise only in-memory fake pytest objects."""
import ast
import hashlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock

source = Path('r1/tests/b1_pytest_session_guard.py').read_text()
tree = ast.parse(source)
wanted = {'_refuse_factory', '_install_factory_guard', '_require_selected',
          'pytest_configure', 'pytest_collection_modifyitems', 'pytest_fixture_setup',
          'pytest_sessionfinish'}
nodes = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in wanted:
        node.decorator_list = []
        nodes.append(node)
assert {node.name for node in nodes} == wanted
module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))

class FakePath:
    def __init__(self, value): self.value = value
    def resolve(self): return self
    def read_bytes(self): return b'pinned'

fixture_a = object()
fixture_root = object()
helper = types.SimpleNamespace(
    __name__='r1.tests.b1_preserved_tmp_plugin',
    tmp_path=types.SimpleNamespace(_get_wrapped_function=lambda: fixture_a),
    b1_preserved_fixture_root=types.SimpleNamespace(_get_wrapped_function=lambda: fixture_root))
# No import of pytest or the project plugin; guard hooks use a fake package.
fake_r1=types.ModuleType('r1'); fake_r1.__path__=[]
fake_tests=types.ModuleType('r1.tests'); fake_tests.__path__=[]
fake_tests.b1_preserved_tmp_plugin=helper
sys.modules['r1']=fake_r1
sys.modules['r1.tests']=fake_tests
sys.modules['r1.tests.b1_preserved_tmp_plugin']=helper
ns = {'Path': FakePath, 'hashlib': hashlib, '_TMPDIR_SHA256': hashlib.sha256(b'pinned').hexdigest(),
      '_BLOCKED': frozenset(('tmp_path_factory','tmpdir','tmpdir_factory','capfd','capfdbinary')),
      '_FACTORY_INSTALLED': False}
exec(compile(module, '<mock-guard>', 'exec'), ns)

class GuardCases(unittest.TestCase):
    def test_pinned_factory_refuses_direct_access(self):
        factory = type('Factory', (), {'getbasetemp': lambda s: 1, 'mktemp': lambda s: 2})
        ns['_install_factory_guard'](types.SimpleNamespace(__file__='fake',TempPathFactory=factory))
        self.assertTrue(ns['_FACTORY_INSTALLED'])
        with self.assertRaises(RuntimeError): factory().getbasetemp()
        with self.assertRaises(RuntimeError): factory().mktemp('x')
    def test_unpinned_factory_is_not_patched(self):
        factory = type('Factory', (), {'getbasetemp': lambda s: 1, 'mktemp': lambda s: 2})
        old = ns['_TMPDIR_SHA256']; ns['_TMPDIR_SHA256'] = 'wrong'
        try:
            with self.assertRaises(RuntimeError): ns['_install_factory_guard'](types.SimpleNamespace(__file__='fake',TempPathFactory=factory))
            self.assertEqual(factory().getbasetemp(), 1)
        finally: ns['_TMPDIR_SHA256'] = old
    def test_reject_blocked_and_shadowed_fixture(self):
        good = types.SimpleNamespace(argname='tmp_path',func=fixture_a)
        ns['_require_selected'](good, helper)
        for name, fn in [('tmp_path', object()), ('tmp_path_factory', object()),
                         ('b1_preserved_fixture_root', object()), ('capfd', object())]:
            with self.assertRaises(RuntimeError): ns['_require_selected'](types.SimpleNamespace(argname=name,func=fn),helper)
    def test_collection_closure_rejects_shadowed_definition(self):
        good=types.SimpleNamespace(argname='tmp_path',func=fixture_a)
        bad=types.SimpleNamespace(argname='tmp_path',func=object())
        item=types.SimpleNamespace(nodeid='x',_fixtureinfo=types.SimpleNamespace(name2fixturedefs={'tmp_path':[good,bad]}))
        with self.assertRaises(RuntimeError): ns['pytest_collection_modifyitems'](None,None,[item])
    def test_sessionfinish_refuses_active_factory(self):
        session=types.SimpleNamespace(config=types.SimpleNamespace(_tmp_path_factory=types.SimpleNamespace(_basetemp='/existing')))
        with self.assertRaises(RuntimeError): ns['pytest_sessionfinish'](session,0)
        session.config._tmp_path_factory._basetemp=None
        self.assertIsNone(ns['pytest_sessionfinish'](session,0))
    def test_configure_requires_disabled_capture_no_basetemp_cache(self):
        pm=types.SimpleNamespace(hasplugin=lambda name:False,get_plugin=lambda name:helper)
        config=types.SimpleNamespace(getoption=lambda name: {'capture':'no','basetemp':None}[name],pluginmanager=pm,
                                     _tmp_path_factory=types.SimpleNamespace(_basetemp=None))
        ns['_FACTORY_INSTALLED']=True
        ns['pytest_configure'](config)
        config.getoption=lambda name: {'capture':'fd','basetemp':None}[name]
        with self.assertRaises(RuntimeError): ns['pytest_configure'](config)
        config.getoption=lambda name: {'capture':'no','basetemp':'/not-allowed'}[name]
        with self.assertRaises(RuntimeError): ns['pytest_configure'](config)
        config.getoption=lambda name: {'capture':'no','basetemp':None}[name]
        config.pluginmanager.hasplugin=lambda name:True
        with self.assertRaises(RuntimeError): ns['pytest_configure'](config)

if __name__ == '__main__': unittest.main(verbosity=2)
