"""Mock-only checks for the extracted DRYRUN exclusive snapshot function."""
import ast
import io
from pathlib import Path
import shutil
import unittest


def _load_helper():
    path = Path(__file__).resolve().parents[1] / 'exam' / 'runtime.py'
    tree = ast.parse(path.read_text())
    node = next(item for item in tree.body
                if isinstance(item, ast.FunctionDef)
                and item.name == 'copy_dryrun_registry_snapshot')
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    namespace = {'shutil': shutil}
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace['copy_dryrun_registry_snapshot']


class RetainedBuffer(io.BytesIO):
    def close(self):
        pass  # Test-owned memory only; keep bytes available for assertions.


class MemoryPath:
    def __init__(self, initial=None, fail_on_write=False):
        self.data = initial
        self.fail_on_write = fail_on_write

    def open(self, mode):
        if mode == 'rb':
            return RetainedBuffer(self.data)
        if mode != 'xb':
            raise AssertionError('unexpected open mode')
        if self.data is not None:
            raise FileExistsError('existing synthetic snapshot')
        self.data = RetainedBuffer()
        if self.fail_on_write:
            def fail_after_partial(chunk):
                self.data.write_original(chunk[:2])
                raise OSError('synthetic write failure')
            self.data.write_original = self.data.write
            self.data.write = fail_after_partial
        return self.data


class TestSnapshotPreservation(unittest.TestCase):
    def test_copy_creates_new_snapshot(self):
        dst = MemoryPath()
        _load_helper()(MemoryPath(b'registry'), dst)
        self.assertEqual(dst.data.getvalue(), b'registry')

    def test_existing_snapshot_is_unchanged(self):
        dst = MemoryPath(b'old')
        with self.assertRaises(FileExistsError):
            _load_helper()(MemoryPath(b'new'), dst)
        self.assertEqual(dst.data, b'old')

    def test_failed_copy_retains_partial(self):
        dst = MemoryPath(fail_on_write=True)
        with self.assertRaises(OSError):
            _load_helper()(MemoryPath(b'registry'), dst)
        self.assertEqual(dst.data.getvalue(), b're')


if __name__ == '__main__':
    unittest.main()
