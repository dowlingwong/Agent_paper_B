"""Pure mocked checks; do not establish site/kernel containment capability."""
import threading
import hashlib
import json
import stat
import unittest
from unittest.mock import Mock, patch

from r1.exam import b1_cgroup as control
from r1.exam import b1_cgroup_bootstrap as bootstrap
from r1.exam import b1_cgroup_guardian as guardian


class BootstrapTests(unittest.TestCase):
    def test_self_enrollment_precedes_grant_and_exec(self):
        operations = []
        def write(fd, data):
            operations.append(('write', fd, data))
            return len(data)
        def close(fd): operations.append(('close', fd))
        def read(fd, count):
            operations.append(('read', fd, count))
            return b'G'
        def dup2(src, dst): operations.append(('dup', src, dst))
        def execve(path, args, env):
            operations.append(('exec', path, args))
            raise RuntimeError('mocked exec')
        with patch.object(bootstrap.os, 'write', side_effect=write), \
             patch.object(bootstrap.os, 'close', side_effect=close), \
             patch.object(bootstrap.os, 'read', side_effect=read), \
             patch.object(bootstrap.os, 'dup2', side_effect=dup2), \
             patch.object(bootstrap.os, 'set_inheritable'), \
             patch.object(bootstrap.os, 'execve', side_effect=execve):
            self.assertEqual(bootstrap.main(['10','11','12','13','14','/bin/fake','--arg']), 2)
        self.assertLess(operations.index(('write', 10, b'0\n')), operations.index(('read', 12, 1)))
        self.assertLess(operations.index(('read', 12, 1)), operations.index(('dup', 13, 1)))
        self.assertLess(operations.index(('dup', 13, 1)), operations.index(('exec', '/bin/fake', ['/bin/fake','--arg'])))

    def test_closed_grant_never_attaches_log_or_executes(self):
        with patch.object(bootstrap.os, 'write', side_effect=lambda fd, data: len(data)), \
             patch.object(bootstrap.os, 'close'), patch.object(bootstrap.os, 'read', return_value=b''), \
             patch.object(bootstrap.os, 'dup2') as dup, patch.object(bootstrap.os, 'execve') as execute:
            self.assertEqual(bootstrap.main(['10','11','12','13','14','/bin/fake']), 2)
        dup.assert_not_called(); execute.assert_not_called()

    def test_short_enrollment_does_not_grant_workload(self):
        with patch.object(bootstrap.os, 'write', return_value=0), patch.object(bootstrap.os, 'read') as read, \
             patch.object(bootstrap.os, 'dup2') as dup:
            self.assertEqual(bootstrap.main(['10','11','12','13','14','/bin/fake']), 2)
        read.assert_not_called(); dup.assert_not_called()


class GuardianTests(unittest.TestCase):
    def test_freeze_waits_for_kernel_frozen_event(self):
        with patch.object(guardian.os, 'lseek'), patch.object(guardian.os, 'write', return_value=2) as write, \
             patch.object(guardian, '_values', side_effect=[{'frozen': 0}, {'frozen': 1}]), \
             patch.object(guardian.time, 'monotonic', side_effect=[0, 0, 1]), patch.object(guardian.time, 'sleep'):
            guardian._freeze(5, 6, timeout=10)
        write.assert_called_once_with(5, b'1\n')

    def test_parent_pidfd_event_freezes_without_waiting_for_socket_eof(self):
        fake_socket = Mock(); fake_socket.fileno.return_value = 3
        fake_poller = Mock(); fake_poller.poll.return_value = [(4, guardian.select.POLLIN)]
        class Done(Exception): pass
        with patch.object(guardian.socket, 'socket', return_value=fake_socket), \
             patch.object(guardian.select, 'poll', return_value=fake_poller), \
             patch.object(guardian, '_freeze') as freeze, \
             patch.object(guardian.time, 'sleep', side_effect=Done):
            with self.assertRaises(Done): guardian.main(['3','4','5','6'])
        freeze.assert_called_once_with(5, 6)
        fake_socket.recv.assert_not_called()

    def test_disconnected_reply_freezes_and_retains_lease(self):
        fake_socket = Mock(); fake_socket.sendall.side_effect = OSError('peer closed')
        class Done(Exception): pass
        with patch.object(guardian, '_freeze') as freeze, \
             patch.object(guardian, '_retain_lease', side_effect=Done):
            with self.assertRaises(Done): guardian._reply(fake_socket, b'FROZEN', 5, 6)
        freeze.assert_called_once_with(5, 6)

    def test_short_freeze_write_cannot_ack_success(self):
        with patch.object(guardian.os, 'lseek'), patch.object(guardian.os, 'write', return_value=1):
            with self.assertRaises(OSError): guardian._freeze(5, 6)


class ControlTests(unittest.TestCase):
    def test_invalid_guardian_lease_is_refused_before_cgroup_creation(self):
        instance=control.B1Containment.__new__(control.B1Containment)
        with patch.object(control, '_parent_dir') as parent:
            with self.assertRaises(control.ContainmentStop): instance.initialize(0, Mock())
        parent.assert_not_called()

    def test_failed_monitor_check_publishes_stop_intent(self):
        instance=control.B1Containment.__new__(control.B1Containment)
        instance._grant_lock=threading.RLock();instance._stop_requested=threading.Event()
        callback=Mock(side_effect=OSError('disk'))
        with self.assertRaises(OSError): instance.observe_check(callback)
        self.assertTrue(instance._stop_requested.is_set())

    def test_ack_requires_observed_frozen_value(self):
        instance = control.B1Containment.__new__(control.B1Containment)
        instance._control_lock = threading.RLock(); instance._write_lock = threading.RLock(); instance._spawn_lock = threading.RLock(); instance._grant_lock = threading.RLock(); instance._stop_requested = threading.Event(); instance._frozen = False
        instance.control = Mock(); instance.control.recv.return_value = b'FROZEN'; instance.events_fd = 7; instance.freeze_fd = 8
        with patch.object(control, '_events', return_value={'frozen': 0}), patch.object(control.os, 'lseek'), \
             patch.object(control.os, 'write', return_value=2), patch.object(control.time, 'monotonic', side_effect=[0, 11]):
            with self.assertRaises(control.ContainmentStop): instance.freeze()
        self.assertFalse(instance._frozen)

    def test_guardian_failure_falls_back_to_parent_freeze(self):
        instance = control.B1Containment.__new__(control.B1Containment)
        instance._control_lock = threading.RLock(); instance._write_lock = threading.RLock(); instance._spawn_lock = threading.RLock(); instance._grant_lock = threading.RLock(); instance._stop_requested = threading.Event(); instance._frozen = False
        instance.control = Mock(); instance.control.sendall.side_effect = OSError('dead')
        instance.events_fd = 7; instance.freeze_fd = 8
        with patch.object(control.os, 'lseek'), patch.object(control.os, 'write', return_value=2) as write, \
             patch.object(control, '_events', return_value={'frozen': 1}), \
             patch.object(control.time, 'monotonic', side_effect=[0, 0]):
            instance.freeze()
        self.assertTrue(instance._frozen); write.assert_called_once_with(8, b'1\n')

    def test_live_server_requires_same_ofd_not_only_inode(self):
        instance=control.B1Containment.__new__(control.B1Containment)
        process=Mock(pid=20); identity=Mock(st_dev=1, st_ino=2)
        with patch.object(control.os, 'fstat', return_value=identity), \
             patch.object(control.os, 'stat', return_value=identity), \
             patch('r1.exam.cooperative_lease.kcmp_file_result', return_value=(None, 1)):
            with self.assertRaises(control.ContainmentStop): instance.verify_live_lease(process, 7)

    def test_stop_requested_during_grant_freezes_before_return(self):
        instance = control.B1Containment.__new__(control.B1Containment)
        instance._control_lock = threading.RLock(); instance._write_lock = threading.RLock(); instance._spawn_lock = threading.RLock(); instance._grant_lock = threading.RLock(); instance._stop_requested = threading.Event(); instance._frozen = False
        instance.guardian = Mock(); instance.guardian.poll.return_value = None
        instance.membership = '/owned'; instance._leaves = {}; instance._leaf = Mock(return_value=('worker-1', 8, 9, 10))
        instance.freeze = Mock(); process = Mock(pid=123); process.poll.return_value = None
        output = Mock(); output.fileno.return_value = 30
        identity = Mock(st_dev=1, st_ino=2)
        def write(fd, data):
            instance._stop_requested.set()
            return len(data)
        with patch.object(control.os, 'pipe', side_effect=[(11, 12), (13, 14), (15, 16)]), \
             patch.object(control.os, 'write', side_effect=write), patch.object(control.os, 'close'), \
             patch.object(control.os, 'pidfd_open', return_value=40, create=True), \
             patch.object(control.os, 'fstat', return_value=identity), patch.object(control.os, 'stat', return_value=identity), \
             patch('r1.exam.cooperative_lease.kcmp_file_result', return_value=(0, 0)), \
             patch.object(control.subprocess, 'Popen', return_value=process), \
             patch.object(control, '_read_one', return_value=b'M'), \
             patch.object(control.Path, 'read_text', return_value='0::/owned/worker-1\n'):
            with self.assertRaises(control.ContainmentStop):
                instance.spawn('worker', ['/bin/fake'], env={}, stdout=output, lease_fd=22)
        instance.freeze.assert_called_once()
        self.assertEqual(instance._leaves, {})

    def test_frozen_server_record_never_invokes_write_callback(self):
        instance = control.B1Containment.__new__(control.B1Containment)
        instance._write_lock = threading.RLock(); instance._stop_requested = threading.Event()
        instance._stop_requested.set(); instance._frozen = False
        instance.require_guardian = Mock()
        callback = Mock()
        with self.assertRaises(control.ContainmentStop): instance.write_active(callback)
        callback.assert_not_called()

    def test_server_signal_targets_retained_pidfd_only(self):
        instance = control.B1Containment.__new__(control.B1Containment)
        instance._control_lock = threading.RLock(); instance._write_lock = threading.RLock(); instance._spawn_lock = threading.RLock(); instance._grant_lock = threading.RLock(); instance._stop_requested = threading.Event(); instance._frozen = False
        process = Mock(pid=20); process.poll.return_value = None
        instance._leaves = {20: ('server', 4, 5, 6)}
        with patch.object(control.signal, 'pidfd_send_signal', create=True) as send, \
             patch.object(control, '_events', return_value={'populated': 0}), \
             patch.object(control.os, 'close'), \
             patch.object(control.time, 'monotonic', side_effect=[0, 0]):
            instance.stop_server(process)
        send.assert_called_once_with(6, control.signal.SIGTERM)
        process.wait.assert_called_once()


class EvidenceTests(unittest.TestCase):
    def test_lock_retirement_is_nonreplacing_and_checks_owned_bytes(self):
        data = json.dumps({'pid': 55, 'host': 'fake'}).encode()
        info = Mock(st_dev=1, st_ino=2, st_uid=3, st_mode=stat.S_IFREG | 0o600)
        rename = Mock(return_value=0); libc = Mock(renameat2=rename)
        with patch.object(control.Path, 'lstat', return_value=info), \
             patch.object(control.Path, 'read_bytes', return_value=data), \
             patch.object(control.Path, 'mkdir') as mkdir, \
             patch.object(control.os, 'getuid', return_value=3), \
             patch.object(control.os, 'getpid', return_value=55), \
             patch.object(control.ctypes, 'CDLL', return_value=libc):
            control.retire_runner_lock('/owned/runner.lock', (1, 2, 3), hashlib.sha256(data).hexdigest())
        mkdir.assert_called_once_with(mode=0o700, exist_ok=False)
        self.assertEqual(rename.call_args.args[-1].value, 1)

    def test_lock_retirement_refuses_changed_inode_before_creating_directory(self):
        info = Mock(st_dev=1, st_ino=99, st_uid=3, st_mode=stat.S_IFREG | 0o600)
        with patch.object(control.Path, 'lstat', return_value=info), \
             patch.object(control.Path, 'mkdir') as mkdir, \
             patch.object(control.os, 'getuid', return_value=3):
            with self.assertRaises(control.ContainmentStop):
                control.retire_runner_lock('/owned/runner.lock', (1, 2, 3), '0' * 64)
        mkdir.assert_not_called()

    def test_stop_record_is_exclusive_and_never_rewritten(self):
        from r1.exam import runtime
        runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.b1_batch_owned = True; runner.b1_stop_created = False
        runner.state = {'phase': 'b1'}; runner.out = control.Path('/owned')
        with patch.object(runtime.os, 'open', return_value=7) as op, \
             patch.object(runtime.os, 'write', side_effect=lambda fd, data: len(data)), \
             patch.object(runtime.os, 'fsync'), patch.object(runtime.os, 'close'):
            runner.save_b1_stop(RuntimeError('first'))
            runner.save_b1_stop(RuntimeError('second'))
        self.assertEqual(op.call_count, 1)
        self.assertTrue(op.call_args.args[1] & runtime.os.O_EXCL)

    def test_no_stop_record_written_for_unowned_batch(self):
        from r1.exam import runtime
        runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.b1_batch_owned = False
        with patch.object(runtime.os, 'open') as op:
            with self.assertRaises(runtime.PreparationStop): runner.save_b1_stop(RuntimeError('x'))
        op.assert_not_called()

    def test_batch_verifier_refuses_any_stop_record_including_symlink(self):
        from r1.exam import b1_batch
        with patch.object(b1_batch.os.path, 'lexists', return_value=True):
            with self.assertRaisesRegex(ValueError, 'STOP record exists'):
                b1_batch._reject_stop_record('/owned')


class CompletionTests(unittest.TestCase):
    def _invoke(self, save_error=None, finish_error=None):
        from r1.scripts import exam_runner
        from r1.exam import analyze
        cfg={'dryrun':False, 'authorizations':{'b1':'note'}, 'rule':'x', 'rule_sha256':'s',
             'stage_a_table':'t', 'stage_a_table_sha256':'h', 'nodes':['n'], 'llm_call_cap':80, 'anchor_duplicate_reference':{}}
        runner=Mock(); runner.state={'status':'RUNNING'}; runner.lock=None
        runner.b1_containment=Mock(); runner.b1_batch_owned=True
        calls=[]
        def close(**kwargs):
            calls.append(('close', dict(kwargs), runner.state['status']))
        def save():
            calls.append(('save', runner.state['status']))
            if save_error: raise save_error
        runner.close.side_effect=close; runner.save.side_effect=save
        def finish():
            calls.append(('finish',))
            if finish_error: raise finish_error
        runner.finish_b1_lease.side_effect=finish
        with patch.object(exam_runner, 'load_config', return_value=cfg), \
             patch.object(exam_runner, 'require_committed_b1_config', return_value='h'), \
             patch.object(analyze, 'load_rule', return_value=({}, 's')), \
             patch.object(exam_runner, 'is_v2', return_value=False), \
             patch.object(exam_runner, 'placeholders', return_value=[]), \
             patch.object(exam_runner, 'verify_anchor_reference'), \
             patch.object(exam_runner, 'ExamRunner', return_value=runner), \
             patch.object(exam_runner, 'evidence'), \
             patch.object(exam_runner, 'report_b1_stop_and_save') as report:
            result=exam_runner.main(['b1','--out','/owned'])
        return result, runner, calls, report

    def test_lease_guardian_still_held_when_complete_state_is_saved(self):
        result, runner, calls, report=self._invoke()
        self.assertEqual(result, 0)
        self.assertEqual(calls, [('close', {'preserve_running':False,'defer_b1_lease':True}, 'RUNNING'),
                                 ('save','COMPLETE'), ('finish',)])
        report.assert_not_called()

    def test_failed_final_save_does_not_finish_guardian(self):
        result, runner, calls, report=self._invoke(OSError('full'))
        self.assertEqual(result, 1)
        runner.finish_b1_lease.assert_not_called()
        runner.b1_containment.freeze.assert_called()
        self.assertEqual(runner.state['status'], 'STOPPED')
        self.assertTrue(report.call_args.kwargs['append_only'])

    def test_failed_guardian_finish_records_stop_after_complete_write(self):
        result, runner, calls, report=self._invoke(finish_error=OSError('guardian lost'))
        self.assertEqual(result, 1)
        self.assertIn(('save','COMPLETE'), calls)
        self.assertEqual(runner.state['status'], 'STOPPED')
        runner.b1_containment.freeze.assert_called()
        self.assertTrue(report.call_args.kwargs['append_only'])


if __name__ == '__main__':
    unittest.main()
