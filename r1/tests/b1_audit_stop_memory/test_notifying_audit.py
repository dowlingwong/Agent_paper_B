"""In-memory checks of the unwired notification component; no OS pipes."""
import importlib.util
import os
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'exam' / 'b1_audit_stop.py'
spec = importlib.util.spec_from_file_location('b1_audit_stop_memory', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Tests(unittest.TestCase):
    def test_success_and_audit_exception_are_ordered(self):
        events = []
        fdstat = lambda fd: SimpleNamespace(st_mode=stat.S_IFIFO,st_dev=1,st_ino=fd)
        def send(fd, data):
            events.append(('send', fd, data))
            return 1
        def fail(*args):
            events.append(('audit', args))
            raise ValueError('original audit failure')
        flags = os.O_WRONLY | os.O_NONBLOCK
        with patch.object(module.os, 'fstat', side_effect=fdstat), patch.object(module.fcntl, 'fcntl', return_value=flags), patch.object(module.os, 'write', side_effect=send):
            self.assertEqual(module.run_notifying_audit((7, 8), lambda x: x+1, 4), 5)
            self.assertEqual(events, [])
            with self.assertRaisesRegex(ValueError, 'original audit failure'):
                module.run_notifying_audit((7, 8), fail, 'node')
            self.assertEqual(events, [('audit', ('node',)), ('send', 7, b'S'), ('send', 8, b'S')])

    def test_bad_fd_stops_before_work(self):
        work = []
        with patch.object(module.os, 'fstat', return_value=SimpleNamespace(st_mode=stat.S_IFREG)), patch.object(module.fcntl, 'fcntl', return_value=os.O_WRONLY | os.O_NONBLOCK), patch.object(module.os, 'write', return_value=1):
            with self.assertRaises(module.AuditNotificationStop):
                module.run_notifying_audit((7, 8), lambda: work.append('started'))
        self.assertEqual(work, [])

    def test_runner_callback_marks_then_freezes_before_reporting(self):
        events = []
        for token in (b'S', b'', b'X'):
            with self.subTest(token=token), patch.object(module.os, 'read', return_value=token):
                events.clear()
                with self.assertRaises(module.AuditNotificationStop):
                    module.handle_ready_audit_channel(8, lambda: events.append('mark'), lambda: events.append('guardian freeze'))
                self.assertEqual(events, ['mark', 'guardian freeze'])
        with patch.object(module.os, 'read', side_effect=BlockingIOError):
            events.clear()
            self.assertFalse(module.handle_ready_audit_channel(8, lambda: events.append('mark'), lambda: events.append('guardian freeze')))
            self.assertEqual(events, [])

    def test_mark_failure_still_attempts_freeze(self):
        events = []
        def bad_mark():
            raise RuntimeError('mark unavailable')
        with patch.object(module.os, 'read', return_value=b'S'):
            with self.assertRaises(module.AuditNotificationStop):
                module.handle_ready_audit_channel(8, bad_mark, lambda: events.append('guardian freeze'))
        self.assertEqual(events, ['guardian freeze'])

    def test_send_failure_preserves_original_cause(self):
        original = RuntimeError('audit')
        def fail(): raise original
        for send_result in (OSError('pipe unavailable'), 0):
            with self.subTest(send_result=repr(send_result)), patch.object(module.os, 'fstat', side_effect=lambda fd: SimpleNamespace(st_mode=stat.S_IFIFO,st_dev=1,st_ino=fd)), patch.object(module.fcntl, 'fcntl', return_value=os.O_WRONLY | os.O_NONBLOCK), patch.object(module.os, 'write', side_effect=send_result if isinstance(send_result, Exception) else None, return_value=send_result if isinstance(send_result, int) else None):
                with self.assertRaises(module.AuditNotificationStop) as caught:
                    module.run_notifying_audit((7, 8), fail)
                self.assertIs(caught.exception.__cause__, original)

    def test_one_broken_writer_uses_independent_backup(self):
        events=[]
        def send(fd, data):
            events.append(fd)
            if fd == 7: raise OSError('primary write failed')
            return 1
        def fail(): raise ValueError('original audit failure')
        with patch.object(module.os, 'fstat', side_effect=lambda fd: SimpleNamespace(st_mode=stat.S_IFIFO,st_dev=1,st_ino=fd)), patch.object(module.fcntl, 'fcntl', return_value=os.O_WRONLY | os.O_NONBLOCK), patch.object(module.os, 'write', side_effect=send):
            with self.assertRaisesRegex(ValueError, 'original audit failure'):
                module.run_notifying_audit((7,8), fail)
        self.assertEqual(events, [7,8])

    def test_invalid_first_descriptor_reports_to_backup_before_work(self):
        events=[]
        def status(fd):
            if fd == 7: raise OSError('closed primary')
            return SimpleNamespace(st_mode=stat.S_IFIFO)
        def send(fd, data):
            if fd == 7: raise OSError('closed primary')
            events.append(('backup', data, 'sibling still running'))
            return 1
        with patch.object(module.os, 'fstat', side_effect=status), patch.object(module.fcntl, 'fcntl', return_value=os.O_WRONLY | os.O_NONBLOCK), patch.object(module.os, 'write', side_effect=send):
            with self.assertRaises(module.AuditNotificationStop):
                module.run_notifying_audit((7,8), lambda: events.append('work started'))
        self.assertEqual(events, [('backup', b'S', 'sibling still running')])


if __name__ == '__main__': unittest.main()
