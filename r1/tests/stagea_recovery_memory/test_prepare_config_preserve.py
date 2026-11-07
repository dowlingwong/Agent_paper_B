"""Pure in-memory checks of the synthetic prepare-config preservation helper."""
import ast
import io
import json
import unittest
from pathlib import Path


class MemoryPath:
    files = {}
    dirs = set()

    def __init__(self, value):
        self.value = str(value)

    @property
    def name(self):
        return self.value.rsplit('/', 1)[-1]

    def __truediv__(self, name):
        return MemoryPath(self.value + '/' + str(name))

    def mkdir(self, mode):
        if self.value in self.dirs or self.value in self.files:
            raise FileExistsError(self.value)
        self.dirs.add(self.value)

    def rename(self, target):
        if self.value not in self.files:
            raise FileNotFoundError(self.value)
        self.files[target.value] = self.files.pop(self.value)

    def open(self, mode, encoding):
        assert mode == 'x' and encoding == 'utf-8'
        if self.value in self.files:
            raise FileExistsError(self.value)
        owner = self
        class Sink(io.StringIO):
            def close(self):
                owner.files[owner.value] = self.getvalue()
                super().close()
        return Sink()


class PrepareConfigPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path('r1/tests/test_exam_stagea_b1_crash_recovery.py').read_text()
        tree = ast.parse(source)
        helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                      and node.name == '_preserve_prepare_config')
        module = ast.fix_missing_locations(ast.Module(body=[helper], type_ignores=[]))
        namespace = {'json': json}
        exec(compile(module, '<extracted-helper>', 'exec'), namespace)
        cls.helper = staticmethod(namespace['_preserve_prepare_config'])

    def setUp(self):
        MemoryPath.files = {'root/config.json': '{"initial": true}'}
        MemoryPath.dirs = {'root'}

    def test_archives_old_config_and_creates_changed_config(self):
        self.helper(MemoryPath('root/config.json'), MemoryPath('_to_delete'), {'changed': 7})
        self.assertEqual(MemoryPath.files['_to_delete/config.json'], '{"initial": true}')
        self.assertEqual(json.loads(MemoryPath.files['root/config.json']), {'changed': 7})

    def test_existing_archive_refuses_without_changing_config(self):
        MemoryPath.dirs.add('_to_delete')
        with self.assertRaises(FileExistsError):
            self.helper(MemoryPath('root/config.json'), MemoryPath('_to_delete'), {'changed': 7})
        self.assertEqual(MemoryPath.files, {'root/config.json': '{"initial": true}'})

    def test_exclusive_recreation_failure_retains_old_bytes(self):
        original = MemoryPath.open
        def collision(self, mode, encoding):
            raise FileExistsError(self.value)
        MemoryPath.open = collision
        try:
            with self.assertRaises(FileExistsError):
                self.helper(MemoryPath('root/config.json'), MemoryPath('_to_delete'), {'changed': 7})
        finally:
            MemoryPath.open = original
        self.assertEqual(MemoryPath.files['_to_delete/config.json'], '{"initial": true}')


if __name__ == '__main__':
    unittest.main()
