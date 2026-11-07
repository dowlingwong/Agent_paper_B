"""In-memory check of fixed pytest argv and environment preflight."""
import ast
import re
import unittest
from pathlib import Path

source = Path('r1/tests/b1_preserved_pytest_launcher.py').read_text()
tree = ast.parse(source)
wanted = {'_validate_environment', '_fixed_args'}
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
assert {n.name for n in functions} == wanted
ns = {'_NODE': re.compile(r'r1/tests/test_[A-Za-z0-9_]+\.py(?:::[A-Za-z_][A-Za-z0-9_]*){1,2}(?:\[[A-Za-z0-9_][A-Za-z0-9_.,=+\-]*\])?\Z')}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), '<launcher-pure>', 'exec'), ns)

class LaunchBoundary(unittest.TestCase):
    def test_fixed_s_and_plugins_precede_selector(self):
        args = ns['_fixed_args'](Path('/repo'), ['r1/tests/test_example.py::test_case'])
        self.assertEqual(args[:5], ['-s','-p','no:cacheprovider','--noconftest','-c'])
        self.assertIn('r1.tests.b1_pytest_session_guard', args)
        self.assertEqual(args[-1], 'r1/tests/test_example.py::test_case')
    def test_refuse_cli_option_or_path_injection(self):
        for selector in ['--capture=fd', 'r1/tests/test_example.py::test_ok --capture=fd',
                         'r1/tests/../test_example.py::test_ok', 'r1/tests/test_example.py',
                         'r1/tests/test_example.py::test_ok[--capture=fd]']:
            with self.assertRaises(RuntimeError): ns['_fixed_args'](Path('/repo'), [selector])
    def test_reject_empty_duplicate(self):
        for selectors in [[], ['r1/tests/test_x.py::test_y'] * 2]:
            with self.assertRaises(RuntimeError): ns['_fixed_args'](Path('/repo'), selectors)
    def test_reject_external_pytest_inputs(self):
        check=ns['_validate_environment']
        check({'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
        for env in [{}, {'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'0'},
                    {'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTEST_ADDOPTS':'--capture=fd'},
                    {'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTEST_PLUGINS':'x'},
                    {'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTEST_DEBUG_TEMPROOT':'/tmp/x'}]:
            with self.assertRaises(RuntimeError): check(env)

if __name__ == '__main__': unittest.main(verbosity=2)
