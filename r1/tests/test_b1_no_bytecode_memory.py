"""AST-only checks; no launched process or filesystem mutation."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

runtime = ast.parse(Path('r1/exam/runtime.py').read_text())
worker = next(n for n in runtime.body if isinstance(n, ast.FunctionDef) and n.name == 'worker_environment')
module = ast.fix_missing_locations(ast.Module(body=[worker], type_ignores=[]))

class FakePath:
    def __init__(self, value): self.value = value
    @property
    def parent(self): return self
    def __truediv__(self, value): return self
    def is_file(self): return True
    def __str__(self): return '/python'

fake_os = SimpleNamespace(environ={'PYTHONDONTWRITEBYTECODE': '0'}, X_OK=1, pathsep=':',
    access=lambda *a: True, path=SimpleNamespace(samefile=lambda *a: True))
scope = {'os': fake_os, 'Path': FakePath, 'sys': SimpleNamespace(executable='/python/python3'),
    'REPO': '/repo', 'shutil': SimpleNamespace(which=lambda *a, **k: '/python/python3'),
    'PreparationStop': RuntimeError}
exec(compile(module, '<worker_environment>', 'exec'), scope)
assert scope['worker_environment']()['PYTHONDONTWRITEBYTECODE'] == '1'
assert scope['worker_environment']({'PYTHONDONTWRITEBYTECODE': '0'})['PYTHONDONTWRITEBYTECODE'] == '1'

supervisor = ast.parse(Path('r1/scripts/b1_supervisor.py').read_text())
guard = next(n for n in supervisor.body if isinstance(n, ast.If) and 'dont_write_bytecode' in ast.unparse(n.test))
code = compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])), '<supervisor-guard>', 'exec')
for name, disabled, stop in [('__main__', False, True), ('__main__', True, False), ('imported', False, False)]:
    try: exec(code, {'__name__': name, 'sys': SimpleNamespace(dont_write_bytecode=disabled)})
    except SystemExit: assert stop
    else: assert not stop

start = next(n for n in ast.walk(runtime) if isinstance(n, ast.FunctionDef) and n.name == 'run_job')
assignment = next(n for n in ast.walk(start) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'argv' for t in n.targets))
code = compile(ast.fix_missing_locations(ast.Module(body=[assignment], type_ignores=[])), '<worker-argv>', 'exec')
for contained in (True, False):
    scope={'sys':SimpleNamespace(executable='/python/python3'),'contained':contained,'module':'worker',
           'path':FakePath('/batch')}
    exec(code, scope)
    assert ('-B' in scope['argv']) == contained
print('PASS: forced worker environment, early supervisor guard and scoped argv (7 cases)')
