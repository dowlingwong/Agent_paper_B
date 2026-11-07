"""Mock-only checks of actual DRYRUN checkpoint load/skip; no recovery authority."""
import ast
import copy
import hashlib
import io
import json
import os
import pathlib
import types
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[2] / 'exam' / 'runtime.py'
TREE = ast.parse(SOURCE.read_text())
RUNNER = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == 'ExamRunner')
NAMES = {'start', 'root'}
METHODS = [copy.deepcopy(n) for n in RUNNER.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
REJECT = copy.deepcopy(next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'reject_stopped_batch'))
MODULE = ast.Module(body=[REJECT, ast.ClassDef(name='MemoryRunner', bases=[], keywords=[], body=METHODS, decorator_list=[])], type_ignores=[])


class MemoryFile(io.StringIO):
    def __init__(self, fs, name):
        super().__init__()
        self.fs, self.name = fs, name
    def close(self):
        if not self.closed:
            self.fs[self.name] = self.getvalue()
        super().close()


class MemoryFS:
    def __init__(self, files):
        self.files = dict(files)
        self.actions = []
    def path(self, value):
        fs = self
        class P:
            def __init__(self, text): self.text = str(text)
            def __truediv__(self, other): return P(self.text.rstrip('/') + '/' + str(other))
            def __str__(self): return self.text
            @property
            def parent(self): return P(self.text.rsplit('/', 1)[0])
            def exists(self): return self.text in fs.files
            def read_text(self): return fs.files[self.text]
            def mkdir(self, **kw): fs.actions.append(('mkdir', self.text))
            def rglob(self, pattern): return []
            def open(self, mode):
                assert mode == 'x' and self.text not in fs.files
                fs.actions.append(('create', self.text))
                return MemoryFile(fs.files, self.text)
            def rename(self, dest):
                raise AssertionError('renaming not expected in this test')
        return P(value)


def build(fs, gate):
    class PreparationStop(RuntimeError): pass
    fake_os = types.SimpleNamespace(path=types.SimpleNamespace(lexists=lambda path: str(path) in fs.files),
                                    getpid=lambda: 123, kill=lambda *a: (_ for _ in ()).throw(AssertionError('unexpected process lookup')))
    def digest(path): return hashlib.sha256(fs.files[str(path)].encode()).hexdigest()
    def verify(path, binding):
        assert binding == 'test-binding'
        return json.loads(fs.files[str(path)])
    scope = {'PreparationStop':PreparationStop, 'Path':fs.path, 'os':fake_os, 'json':json,
             'platform':types.SimpleNamespace(node=lambda:'synthetic'), 'worker_environment':lambda:None,
             '_dryrun_existing_state_identity':lambda path: str(path) if path.exists() else None,
             'author_gate':gate, 'digest_file':digest, 'verify_campaign':verify}
    exec(compile(ast.fix_missing_locations(copy.deepcopy(MODULE)), '<actual-runtime-methods>', 'exec'), scope)
    return scope['MemoryRunner'], PreparationStop, digest


class CopiedCheckpointTest(unittest.TestCase):
    def setUp(self):
        # This is a synthetic, caller-provided copy in memory. The old root is
        # retained and the copied root is deliberately missing runner.lock.
        self.old_manifest = '/old/completed/manifest.json'
        self.old_post = '/old/completed/post_check.json'
        self.table = '/old/stage-a/stage_a_table.json'
        self.manifest = json.dumps({'label':'DRYRUN', 'synthetic':True})
        self.post = '{"passed":true}'
        self.fs = MemoryFS({self.old_manifest:self.manifest, self.old_post:self.post,
                            self.table:'{"rows":[{"passed":true}]}',
                            '/old/b1/runner.lock':'{"pid":77}',
                            '/old/b1/partial/root_trials.jsonl':'partial-prefix'})
        self.before_old = {k:v for k,v in self.fs.files.items() if k.startswith('/old/')}
        self.gates = []
        def gate(cfg, phase, sha):
            self.gates.append((cfg['stage_a_table'], cfg['stage_a_table_sha256'], phase, sha))
            assert hashlib.sha256(self.fs.files[cfg['stage_a_table']].encode()).hexdigest() == cfg['stage_a_table_sha256']
            return 'synthetic-author-head'
        Runner, self.Stop, digest = build(self.fs, gate)
        self.runner = Runner()
        self.runner.cfg = {'dryrun':True, 'stage_a_table':self.table, 'stage_a_table_sha256':digest(self.table)}
        self.runner.rule = {'version':'x5_rule/v2'}
        self.runner.rule_sha = 'synthetic-rule-sha'
        self.runner.out = self.fs.path('/copy/b1')
        self.runner.binding = 'test-binding'
        self.runner.author_head = None
        self.runner.service = None
        self.runner.space = lambda: None
        self.runner.save = lambda: self.fs.actions.append(('save', '/copy/b1'))
        self.key = 'random_valid/b1/off/digits_mlp__s9001'
        self.state = {'status':'RUNNING', 'binding':'test-binding', 'phase':'b1', 'completed':{
            self.key:{'path':self.old_manifest, 'sha256':digest(self.old_manifest), 'post_check_sha256':digest(self.old_post)}}}
        self.fs.files['/copy/b1/batch_state.json'] = json.dumps(self.state)

    def old_unchanged(self):
        self.assertEqual({k:v for k,v in self.fs.files.items() if k.startswith('/old/')}, self.before_old)

    def test_copied_unrecorded_checkpoint_loads_and_skips_completed_root(self):
        self.runner.start('b1')
        self.assertEqual(self.gates[0][0], self.table)
        result = self.runner.root({'id':'random_valid'}, 'b1', 'digits_mlp', 9001, 'off')
        self.assertEqual(result, {'label':'DRYRUN', 'synthetic':True})
        self.assertEqual(self.runner.state['completed'][self.key]['path'], self.old_manifest)
        self.assertEqual(sum(action[0] == 'create' for action in self.fs.actions), 1)
        self.old_unchanged()

    def test_stopped_checkpoint_is_refused_before_copy_lock_creation(self):
        self.state['status'] = 'STOPPED'
        self.fs.files['/copy/b1/batch_state.json'] = json.dumps(self.state)
        with self.assertRaisesRegex(self.Stop, 'stopped batch must not be resumed'):
            self.runner.start('b1')
        self.assertNotIn(('create', '/copy/b1/runner.lock'), self.fs.actions)
        self.old_unchanged()

    def test_copied_prior_lock_is_refused_without_replacement(self):
        self.fs.files['/copy/b1/runner.lock'] = '{"pid":77}'
        with self.assertRaisesRegex(RuntimeError, 'existing DRYRUN runner lock'):
            self.runner.start('b1')
        self.assertEqual(self.fs.files['/copy/b1/runner.lock'], '{"pid":77}')
        self.old_unchanged()

    def test_changed_completed_root_is_refused_before_copy_lock_creation(self):
        self.fs.files[self.old_manifest] = '{"synthetic":"changed"}'
        with self.assertRaisesRegex(RuntimeError, 'completed root changed'):
            self.runner.start('b1')
        self.assertNotIn(('create', '/copy/b1/runner.lock'), self.fs.actions)
        self.assertEqual(self.fs.files['/old/b1/partial/root_trials.jsonl'], 'partial-prefix')


if __name__ == '__main__':
    unittest.main()
