"""Pure mock checks for interrupted-root cleanup exception handling."""
import errno
import unittest
from unittest import mock

from r1.exam import dryrun_root_preserve as retire
from r1.tests.stagea_recovery_memory.test_dryrun_root_retire import MemoryFS


class DryrunRootCloseTests(unittest.TestCase):
    def close_with_failure(self, fs):
        def close(fd):
            fs.operations.append(('close', fd))
            if fd == 104:
                raise PermissionError(errno.EPERM, 'synthetic close failure')
        return close

    def test_original_rename_error_survives_secondary_close_failure(self):
        fs = MemoryFS(); fs.fail_rename = True; original = fs.old
        with fs.patches(), mock.patch.object(retire.os, 'close', side_effect=self.close_with_failure(fs)):
            with self.assertRaises(OSError) as caught:
                retire.retire_dryrun_root('/batch', '/batch/a/b/root')
        self.assertEqual(caught.exception.errno, errno.EOPNOTSUPP)
        self.assertIs(fs.old, original)
        self.assertEqual(len([op for op in fs.operations if op[0] == 'close']), 5)

    def test_close_failure_after_success_survives_outer_handled_exception(self):
        fs = MemoryFS(); original = fs.old
        try:
            raise ValueError('outer caller is handling a separate exception')
        except ValueError:
            with fs.patches(), mock.patch.object(retire.os, 'close', side_effect=self.close_with_failure(fs)):
                with self.assertRaises(PermissionError):
                    retire.retire_dryrun_root('/batch', '/batch/a/b/root')
        self.assertIs(fs.target, original)
        self.assertEqual(len([op for op in fs.operations if op[0] == 'close']), 5)


if __name__ == '__main__':
    unittest.main()
