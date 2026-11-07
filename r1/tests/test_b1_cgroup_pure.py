"""Pure mocked checks; do not establish site/kernel containment capability."""
import threading
import hashlib
import json
import stat
import sys
import types
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
            self.assertEqual(bootstrap.main(['10','11','12','13','13','14','/bin/fake','--arg']), 2)
        self.assertLess(operations.index(('write', 10, b'0\n')), operations.index(('read', 12, 1)))
        self.assertLess(operations.index(('read', 12, 1)), operations.index(('dup', 13, 1)))
        self.assertLess(operations.index(('dup', 13, 1)), operations.index(('exec', '/bin/fake', ['/bin/fake','--arg'])))

    def test_closed_grant_never_attaches_log_or_executes(self):
        with patch.object(bootstrap.os, 'write', side_effect=lambda fd, data: len(data)), \
             patch.object(bootstrap.os, 'close'), patch.object(bootstrap.os, 'read', return_value=b''), \
             patch.object(bootstrap.os, 'dup2') as dup, patch.object(bootstrap.os, 'execve') as execute:
            self.assertEqual(bootstrap.main(['10','11','12','13','13','14','/bin/fake']), 2)
        dup.assert_not_called(); execute.assert_not_called()

    def test_short_enrollment_does_not_grant_workload(self):
        with patch.object(bootstrap.os, 'write', return_value=0), patch.object(bootstrap.os, 'read') as read, \
             patch.object(bootstrap.os, 'dup2') as dup:
            self.assertEqual(bootstrap.main(['10','11','12','13','13','14','/bin/fake']), 2)
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
            with self.assertRaises(Done): guardian.main(['3','4','5','6','7','8','9'])
        freeze.assert_called_once_with(5, 6)
        fake_socket.recv.assert_not_called()

    def test_finish_handoff_retains_on_supervisor_death(self):
        control, handoff = Mock(), Mock()
        control.recv.return_value = b'FINISH'
        poller = Mock()
        poller.poll.side_effect = [[], [(3, guardian.select.POLLIN)], [(7, guardian.select.POLLIN)]]
        class Done(Exception): pass
        with patch.object(guardian.socket, 'socket', side_effect=[control, handoff]), \
             patch.object(guardian.select, 'poll', return_value=poller), \
             patch.object(guardian, '_values', return_value={'populated': 0}), \
             patch.object(guardian, '_freeze') as freeze, \
             patch.object(guardian, '_retain_lease', side_effect=Done):
            with self.assertRaises(Done): guardian.main(['3','4','5','6','7','8','9'])
        control.sendall.assert_any_call(b'FINISHED')
        freeze.assert_called_once_with(5, 6)
        handoff.recv.assert_not_called()

    def test_finish_handoff_releases_only_after_supervisor_message(self):
        control, handoff = Mock(), Mock()
        control.recv.return_value = b'FINISH'
        handoff.recv.return_value = b'RELEASE'
        poller = Mock()
        poller.poll.side_effect = [[], [(3, guardian.select.POLLIN)], [(9, guardian.select.POLLIN)]]
        with patch.object(guardian.socket, 'socket', side_effect=[control, handoff]), \
             patch.object(guardian.select, 'poll', return_value=poller), \
             patch.object(guardian, '_values', return_value={'populated': 0}), \
             patch.object(guardian, '_freeze') as freeze:
            self.assertEqual(guardian.main(['3','4','5','6','7','8','9']), 0)
        handoff.sendall.assert_called_once_with(b'RELEASED')
        freeze.assert_not_called()

    def test_supervisor_death_wins_over_simultaneous_release(self):
        control, handoff = Mock(), Mock()
        control.recv.return_value = b'FINISH'
        handoff.recv.return_value = b'RELEASE'
        poller = Mock()
        poller.poll.side_effect = [[], [(3, guardian.select.POLLIN)],
                                   [(7, guardian.select.POLLIN), (9, guardian.select.POLLIN)]]
        class Done(Exception): pass
        with patch.object(guardian.socket, 'socket', side_effect=[control, handoff]), \
             patch.object(guardian.select, 'poll', return_value=poller), \
             patch.object(guardian, '_values', return_value={'populated': 0}), \
             patch.object(guardian, '_freeze') as freeze, \
             patch.object(guardian, '_retain_lease', side_effect=Done):
            with self.assertRaises(Done): guardian.main(['3','4','5','6','7','8','9'])
        freeze.assert_called_once_with(5, 6)
        handoff.recv.assert_not_called()
        handoff.sendall.assert_not_called()

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
    def test_finish_refuses_guardian_nonzero_after_ack(self):
        instance=control.B1Containment.__new__(control.B1Containment)
        instance._spawn_lock=threading.Lock(); instance._frozen=False
        instance.events_fd=7; instance.control=Mock()
        instance.control.recv.return_value=b'FINISHED'
        instance.guardian=Mock(); instance.guardian.poll.return_value=1
        with patch.object(control,'_events',return_value={'populated':0}):
            with self.assertRaises(control.ContainmentStop): instance.finish()
        instance.control.close.assert_not_called()

    def test_invalid_guardian_lease_is_refused_before_cgroup_creation(self):
        instance=control.B1Containment.__new__(control.B1Containment)
        with patch.object(control, '_parent_dir') as parent:
            with self.assertRaises(control.ContainmentStop): instance.initialize(0, Mock(), 8, 9, 10)
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
        directory = Mock(st_dev=1, st_uid=3, st_mode=stat.S_IFDIR | 0o700)
        def lstat(path):
            return info if path.name == 'runner.lock' else directory
        with patch.object(control.Path, 'lstat', autospec=True, side_effect=lstat), \
             patch.object(control.Path, 'read_bytes', return_value=data), \
             patch.object(control.Path, 'mkdir') as mkdir, \
             patch.object(control.os, 'getuid', return_value=3), \
             patch.object(control.os, 'getpid', return_value=55), \
             patch.object(control.ctypes, 'CDLL', return_value=libc):
            control.retire_runner_lock('/owned/runner.lock', (1, 2, 3), hashlib.sha256(data).hexdigest())
        mkdir.assert_called_once_with(mode=0o700, exist_ok=True)
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


class HelperRoutingTests(unittest.TestCase):
    def test_version_uses_contained_capture_and_keeps_both_streams(self):
        from r1.scripts import llama_server_instance as lsi
        result=control.subprocess.CompletedProcess(['/fake','--version'],0,'prefix\n','version: 0.7.0 (build 1, commit abcdef)\n')
        capture=Mock(return_value=result)
        with patch.object(lsi.subprocess,'run') as direct:
            observed=lsi.build_info('/fake',capture=capture)
        direct.assert_not_called();capture.assert_called_once_with(['/fake','--version'],timeout=60.0)
        self.assertIn('version: 0.7.0',observed['raw'])

    def test_gpu_queries_use_contained_capture(self):
        from r1.scripts import llama_server_instance as lsi
        from r1.exam import runtime
        apps=control.subprocess.CompletedProcess(['nvidia-smi'],0,'42, GPU-X, 2048\n','')
        sample=control.subprocess.CompletedProcess(['nvidia-smi'],0,'GPU-X, 100, 200, 3\n','')
        capture=Mock(side_effect=[apps,sample])
        with patch.object(lsi.subprocess,'run') as direct:
            self.assertEqual(lsi.gpu_compute_apps(capture=capture)[0]['pid'],42)
            self.assertEqual(runtime.gpu_sample({'gpu_uuid':'GPU-X'},capture=capture)['free_mib'],200)
        direct.assert_not_called()


class SupervisorContractTests(unittest.TestCase):
    def test_publication_exception_is_reconciled_only_with_verified_commit(self):
        from r1.scripts import b1_supervisor
        module=types.ModuleType('r1.exam.b1_exit_receipt')
        module.publish_after_wait=Mock(side_effect=RuntimeError('queued callback'))
        module.verify_waited_success=Mock()
        module.UNCERTAIN='B1_COMMIT_UNCERTAIN.json'
        with patch.dict(sys.modules, {'r1.exam.b1_exit_receipt':module}):
            b1_supervisor._publish_or_reconcile(Mock(),'/batch','head')
            module.verify_waited_success.assert_called_once_with('/batch','head')
            module.verify_waited_success.side_effect=RuntimeError('ACTIVE still present')
            with patch.object(b1_supervisor, '_exclusive_json') as write:
                with self.assertRaisesRegex(b1_supervisor.PublicationUncertain,'commit uncertain'):
                    b1_supervisor._publish_or_reconcile(Mock(),'/batch','head')
            write.assert_called_once()

    def test_filesystem_preflight_refuses_before_lease_and_runner(self):
        from r1.scripts import b1_supervisor
        from r1.exam import runtime, analyze, b1_lease
        check=Mock(side_effect=RuntimeError('unsupported work filesystem'))
        module=types.ModuleType('r1.exam.b1_exit_receipt')
        module._require_local_filesystem=check
        cfg={'dryrun':False,'rule':'rule','rule_sha256':'sha','work_dir':'/work'}
        with patch.dict(sys.modules, {'r1.exam.b1_exit_receipt':module}), \
             patch.object(runtime,'load_config',return_value=cfg), \
             patch.object(runtime,'require_committed_b1_config',return_value='head'), \
             patch.object(runtime,'host_check'), patch.object(runtime,'author_gate',return_value='head'), \
             patch.object(analyze,'load_rule',return_value=({'version':'x5_rule/v2'},'sha')), \
             patch.object(b1_supervisor.Path,'resolve',lambda p: p), \
             patch.object(b1_supervisor.os.path,'lexists',return_value=False), \
             patch.object(b1_lease,'acquire') as acquire, \
             patch.object(b1_supervisor.subprocess,'Popen') as popen:
            with self.assertRaisesRegex(RuntimeError,'unsupported work filesystem'):
                b1_supervisor.main(['--config','cfg','--out','/work/batch'])
        check.assert_called_once_with(b1_supervisor.Path('/work'))
        acquire.assert_not_called(); popen.assert_not_called()

    def _env(self):
        return {'R1_B1_SUPERVISOR_PID':'42','R1_B1_SUPERVISOR_TICKS':'99',
                'R1_B1_SUPERVISOR_PIDFD':'8','R1_B1_SUPERVISOR_LIVE_FD':'9','R1_B1_LEASE_FD':'10',
                'R1_B1_GUARDIAN_HANDOFF_FD':'11'}

    def test_release_ack_failure_does_not_publish_success(self):
        from r1.scripts import b1_supervisor
        handoff=Mock();handoff.recv.side_effect=OSError('lost ack')
        with patch.object(b1_supervisor,'_publish_or_reconcile') as publish:
            with self.assertRaises(OSError):
                b1_supervisor._release_then_publish(Mock(),'/batch','head',handoff)
        handoff.sendall.assert_called_once_with(b'RELEASE')
        publish.assert_not_called()

    def test_release_send_failure_even_with_stop_write_failure_never_publishes(self):
        from r1.scripts import b1_supervisor
        handoff=Mock();handoff.sendall.side_effect=OSError('send failed')
        stop_write=Mock(side_effect=OSError('disk full'))
        with patch.object(b1_supervisor,'_publish_or_reconcile') as publish:
            try:
                b1_supervisor._release_then_publish(Mock(),'/batch','head',handoff)
            except OSError:
                try: stop_write()
                except OSError: pass
        stop_write.assert_called_once()
        handoff.recv.assert_not_called()
        publish.assert_not_called()

    def test_success_publication_occurs_after_release_ack(self):
        from r1.scripts import b1_supervisor
        calls=[]
        handoff=Mock()
        handoff.sendall.side_effect=lambda message: calls.append(('send',message))
        handoff.recv.side_effect=lambda limit: calls.append(('ack',limit)) or b'RELEASED'
        with patch.object(b1_supervisor,'_publish_or_reconcile',side_effect=lambda *args: calls.append(('publish',))):
            b1_supervisor._release_then_publish(Mock(),'/batch','head',handoff)
        self.assertEqual(calls,[('send',b'RELEASE'),('ack',64),('publish',)])

    def test_wrong_release_ack_does_not_publish_success(self):
        from r1.scripts import b1_supervisor
        handoff=Mock();handoff.recv.return_value=b'FAILED'
        with patch.object(b1_supervisor,'_publish_or_reconcile') as publish:
            with self.assertRaises(RuntimeError):
                b1_supervisor._release_then_publish(Mock(),'/batch','head',handoff)
        publish.assert_not_called()

    def test_contract_refuses_supervisor_stop_before_adopting_lease(self):
        from r1.exam import b1_supervisor_contract as contract
        poller=Mock();poller.poll.return_value=[(9,1)]
        with patch.object(contract.os,'getppid',return_value=42), \
             patch.object(contract,'process_start_ticks',return_value=99), \
             patch.object(contract.Path,'read_text',return_value='Pid:\t42\n'), \
             patch.object(contract.select,'poll',return_value=poller), \
             patch.object(contract,'adopt_inherited') as adopt:
            with self.assertRaises(contract.SupervisorStop): contract.require_supervisor(self._env())
        adopt.assert_not_called()

    def test_contract_adopts_inherited_fd_only_with_live_matching_parent(self):
        from r1.exam import b1_supervisor_contract as contract
        poller=Mock();poller.poll.return_value=[]
        with patch.object(contract.os,'getppid',return_value=42), \
             patch.object(contract,'process_start_ticks',return_value=99), \
             patch.object(contract.Path,'read_text',return_value='Pid:\t42\n'), \
             patch.object(contract.select,'poll',return_value=poller), \
             patch.object(contract,'adopt_inherited') as adopt:
            observed=contract.require_supervisor(self._env())
        self.assertEqual(observed['lease_fd'],10);adopt.assert_called_once()

    def test_supervisor_checks_same_ofd_not_inode_only(self):
        from r1.scripts import b1_supervisor
        identity=Mock(st_dev=1,st_ino=2)
        with patch.object(b1_supervisor.os,'fstat',return_value=identity), \
             patch.object(b1_supervisor.os,'stat',return_value=identity), \
             patch('r1.exam.cooperative_lease.kcmp_file_result',return_value=(None,1)):
            with self.assertRaises(RuntimeError): b1_supervisor._same_inherited_fd(23,10,'lease')

    def test_inherited_lease_is_not_reopened(self):
        from r1.exam import b1_lease
        info=Mock(st_mode=stat.S_IFREG|0o600,st_nlink=1,st_uid=3,st_dev=4,st_ino=5)
        with patch.object(b1_lease.os,'fstat',return_value=info), \
             patch.object(b1_lease.os,'stat',return_value=info), \
             patch.object(b1_lease.os,'getuid',return_value=3), \
             patch.object(b1_lease.os,'open') as op, patch.object(b1_lease.fcntl,'flock') as flock:
            self.assertEqual(b1_lease.adopt_inherited(10,'/lock'),10)
        op.assert_not_called();flock.assert_called_once()


class FinalizationTests(unittest.TestCase):
    def test_receipt_accepts_only_exact_state_head_and_canonical_bytes(self):
        from r1.exam import b1_finalization as final
        head='a'*40
        state=b'{"status":"COMPLETE","phase":"b1"}\n'
        receipt=final._payload(state,head)
        raw=(json.dumps(receipt,sort_keys=True,separators=(',', ':'))+'\n').encode()
        def read(path): return raw if path.name=='FINALIZED.json' else state
        with patch.object(final.Path,'is_symlink',return_value=False), \
             patch.object(final.Path,'is_file',return_value=True), \
             patch.object(final.Path,'read_bytes',autospec=True,side_effect=read):
            self.assertEqual(final.verify_finalization('/owned',head),receipt)
            with self.assertRaises(ValueError): final.verify_finalization('/owned','b'*40)

    def test_partial_receipt_is_rejected(self):
        from r1.exam import b1_finalization as final
        def read(path): return b'{"version":' if path.name=='FINALIZED.json' else b'{"status":"COMPLETE","phase":"b1"}'
        with patch.object(final.Path,'is_symlink',return_value=False), \
             patch.object(final.Path,'is_file',return_value=True), \
             patch.object(final.Path,'read_bytes',autospec=True,side_effect=read):
            with self.assertRaises(ValueError): final.verify_finalization('/owned','a'*40)


class CompletionTests(unittest.TestCase):
    def _invoke(self, save_error=None, finish_error=None):
        from r1.scripts import exam_runner
        from r1.exam import analyze
        cfg={'dryrun':False, 'authorizations':{'b1':'note'}, 'rule':'x', 'rule_sha256':'s',
             'stage_a_table':'t', 'stage_a_table_sha256':'h', 'nodes':['n'], 'llm_call_cap':80, 'anchor_duplicate_reference':{}}
        runner=Mock(); runner.state={'status':'RUNNING'}; runner.lock=None
        runner.b1_containment=Mock(); runner.b1_batch_owned=True; runner.out=control.Path('/owned');runner.author_head='a'*40
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
             patch('r1.exam.b1_supervisor_contract.require_supervisor', return_value={'lease_fd':7}), \
             patch.object(analyze, 'load_rule', return_value=({}, 's')), \
             patch.object(exam_runner, 'is_v2', return_value=False), \
             patch.object(exam_runner, 'placeholders', return_value=[]), \
             patch.object(exam_runner, 'verify_anchor_reference'), \
             patch.object(exam_runner, 'ExamRunner', return_value=runner), \
             patch.object(exam_runner, 'evidence'), \
             patch('r1.exam.b1_finalization.write_finalization', side_effect=lambda *args: calls.append(('receipt',))), \
             patch.object(exam_runner, 'report_b1_stop_and_save') as report:
            result=exam_runner.main(['b1','--out','/owned'])
        return result, runner, calls, report

    def test_lease_guardian_still_held_when_complete_state_is_saved(self):
        result, runner, calls, report=self._invoke()
        self.assertEqual(result, 0)
        self.assertEqual(calls, [('close', {'preserve_running':False,'defer_b1_lease':True}, 'RUNNING'),
                                 ('save','COMPLETE'), ('finish',), ('receipt',)])
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
