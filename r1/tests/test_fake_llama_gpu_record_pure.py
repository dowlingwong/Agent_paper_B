"""Pure mocked coverage for a synthetic GPU record collision; no server is run."""
import ast
import io
from pathlib import Path
from types import SimpleNamespace
import unittest


class FakePath:
    def __init__(self, name, opened): self.name=name; self.opened=opened
    def __truediv__(self, name): return FakePath(self.name+'/'+str(name),self.opened)
    def mkdir(self, *, exist_ok): self.opened.append(('mkdir',self.name,exist_ok))
    def open(self, mode, *, encoding):
        self.opened.append(('open',self.name,mode,encoding))
        return io.StringIO()


class GPURecordTests(unittest.TestCase):
    def test_record_uses_exclusive_creation(self):
        source=Path(__file__).resolve().parents[1]/'scripts/c3_fake_llama_server.py'
        tree=ast.parse(source.read_text())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='simulate_gpu_memory')
        code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<fixture>', 'exec')
        calls=[]
        ns={'offload_mode':lambda:'gpu','os':SimpleNamespace(environ={},getpid=lambda:123),
            'ARGS':{'-ngl':'1'},'common':SimpleNamespace(ROOT=FakePath('/synthetic',calls))}
        exec(code,ns)
        ns['simulate_gpu_memory']()
        self.assertEqual(calls,[('mkdir','/synthetic/gpu_apps',True),('open','/synthetic/gpu_apps/123.csv','x','utf-8')])

    def test_collision_propagates_and_does_not_write(self):
        source=Path(__file__).resolve().parents[1]/'scripts/c3_fake_llama_server.py'
        tree=ast.parse(source.read_text())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='simulate_gpu_memory')
        code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<fixture>', 'exec')
        calls=[]
        class Collision(FakePath):
            def __truediv__(self,name): return Collision(self.name+'/'+str(name),self.opened)
            def open(self,mode,*,encoding):
                self.opened.append(('open',mode)); raise FileExistsError('retained existing record')
        ns={'offload_mode':lambda:'gpu','os':SimpleNamespace(environ={},getpid=lambda:123),
            'ARGS':{'-ngl':'1'},'common':SimpleNamespace(ROOT=Collision('/synthetic',calls))}
        exec(code,ns)
        with self.assertRaises(FileExistsError): ns['simulate_gpu_memory']()
        self.assertEqual(calls[-1],('open','x'))

if __name__=='__main__': unittest.main()
