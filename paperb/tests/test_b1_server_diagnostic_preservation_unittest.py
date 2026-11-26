"""In-memory checks of B1 server diagnostic destination selection."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


def diagnostic_branches():
    source = (Path(__file__).parents[1] / 'exam' / 'runtime.py').read_text()
    tree = ast.parse(source)
    server = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_server')
    branches = []
    for node in ast.walk(server):
        if isinstance(node, ast.If) and any(
            isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
            and x.func.id == 'write_exclusive_json' for x in ast.walk(node)
        ):
            # Select only the tight if/else that actually writes a diagnostic.
            if any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                   and x.func.id == 'write_json' for x in ast.walk(node)):
                branches.append(node)
    tight = [n for n in branches if all(not (isinstance(s, ast.If) and
             any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                 and x.func.id == 'write_exclusive_json' for x in ast.walk(s)))
             for s in n.body)]
    assert len(tight) == 2
    for branch in tight:
        branch.body = [s for s in branch.body if not isinstance(s, ast.ImportFrom)]
    return [compile(ast.fix_missing_locations(ast.Module(body=[b], type_ignores=[])),
                    '<diagnostic-branch>', 'exec') for b in tight]


class DiagnosticPreservation(unittest.TestCase):
    def test_two_instances_are_distinct_and_collisions_stop(self):
        files = {}
        def exclusive(path, value):
            path = str(path)
            if path in files:
                raise FileExistsError(path)
            files[path] = value
        def legacy(path, value):
            raise AssertionError('production B1 used legacy writer')
        scope = dict(self=SimpleNamespace(state={'phase': 'b1'}, cfg={'dryrun': False}, out=Path('/batch')),
                     spec={'id': 'candidate'}, occupancy={'gpu': 1}, report={'full': True},
                     inst=SimpleNamespace(batch=Path('/batch/servers/candidate'),
                                          record_path=Path('/batch/servers/candidate/llama_server_1.json')),
                     write_exclusive_json=exclusive, write_json=legacy)
        branches = diagnostic_branches()
        for branch in branches: exec(branch, scope)
        scope['inst'].record_path = Path('/batch/servers/candidate/llama_server_1_r2.json')
        for branch in branches: exec(branch, scope)
        self.assertEqual(len(files), 4)
        for branch in branches:
            with self.assertRaises(FileExistsError): exec(branch, scope)
        self.assertEqual(len(files), 4)

    def test_non_b1_paths_keep_legacy_destinations(self):
        calls = []
        scope = dict(self=SimpleNamespace(state={'phase': 'stage-a'}, cfg={'dryrun': False}, out=Path('/batch')),
                     spec={'id': 'candidate'}, occupancy={}, report={},
                     inst=SimpleNamespace(batch=Path('/batch/servers/candidate'),
                                          record_path=Path('/batch/servers/candidate/llama_server_1.json')),
                     write_exclusive_json=lambda *a: self.fail('non-B1 changed'),
                     write_json=lambda path, value: calls.append(str(path)))
        for branch in diagnostic_branches(): exec(branch, scope)
        self.assertCountEqual(calls, ['/batch/candidate_occupancy_before.json',
                                 '/batch/servers/candidate/exam_offload.json'])


if __name__ == '__main__':
    unittest.main()
