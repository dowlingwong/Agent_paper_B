"""Pure checks for explicit synthetic crash and failed-scene boundaries."""
import ast
import errno
import pathlib
import signal
import types
import unittest
from unittest import mock

from r1.tests.stagea_recovery_memory.test_synthetic_crash_lock import MemoryFS
from r1.tests.stagea_recovery_memory import synthetic_crash_lock as recovery


class SyntheticCrashLockEdges(unittest.TestCase):
    def test_lock_inode_change_before_retirement_is_refused(self):
        fs=MemoryFS(); original=fs.open; count=0
        def changed(name,flags,*,dir_fd=None):
            nonlocal count
            if (dir_fd,str(name))==(11,'runner.lock'):
                count+=1
                if count==2:
                    fs.files[(11,'runner.lock')][0]=fs.info(999)
            return original(name,flags,dir_fd=dir_fd)
        with fs.patches(),mock.patch.object(recovery.os,'open',side_effect=changed):
            with self.assertRaisesRegex(RuntimeError,'scene changed'):
                fs.call()
        self.assertIsNone(fs.moved)
        self.assertIn((11,'runner.lock'),fs.files)

    def test_symlink_record_fails_before_archive(self):
        fs=MemoryFS();fs.files[(11,'runner.lock')][0].st_mode=0o120777
        with fs.patches(),self.assertRaisesRegex(RuntimeError,'unsafe synthetic crash record'):
            fs.call()
        self.assertIsNone(fs.moved)
        self.assertFalse(any(op[0]=='rename' for op in fs.ops))

    def test_actual_test_has_one_planned_sigkill_and_no_timeout_kill(self):
        tree=ast.parse(pathlib.Path('r1/tests/test_exam_stagea_b1_crash_recovery.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='test_stagea_to_b1_owned_parent_crash_and_recovery')
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
        send=[n for n in calls if isinstance(n.func,ast.Attribute) and ast.unparse(n.func)=='parent.send_signal']
        self.assertEqual(len(send),1)
        self.assertEqual(ast.unparse(send[0].args[0]),'signal.SIGKILL')
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and ast.unparse(n.func) in ('parent.kill','resumed.kill','subprocess.run') for n in calls))
        resume=next(n for n in calls if isinstance(n.func,ast.Attribute) and ast.unparse(n.func)=='resumed.wait')
        self.assertTrue(any(k.arg=='timeout' for k in resume.keywords))
        self.assertIn('preserve still-running synthetic resumed process',ast.unparse(fn))


if __name__=='__main__':unittest.main()
