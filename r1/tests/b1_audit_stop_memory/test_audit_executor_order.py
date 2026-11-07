"""Execute the production executor branch with fake futures and descriptors."""
import ast
import importlib.util
import os
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('audit_signal_order', ROOT / 'exam' / 'b1_audit_stop.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakePool:
    def __init__(self, events, **kwargs): self.events = events; self.count = 0
    def __enter__(self): return self
    def __exit__(self, *args): self.events.append('pool shutdown'); return False
    def submit(self, wrapper, fd, fn, *args):
        self.count += 1
        return FakeFuture(self.count, self.events)


class FakeFuture:
    def __init__(self, number, events): self.number, self.events = number, events
    def result(self):
        self.events.append('future result ' + str(self.number))
        if self.number == 1: raise RuntimeError('audit failed')
        raise AssertionError('sibling must not be consumed')


class Tests(unittest.TestCase):
    def test_collector_notifies_before_pool_context_wait(self):
        tree = ast.parse((ROOT / 'exam' / 'campaign.py').read_text())
        fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == '_collect_b1_review')
        section = next(x for x in fn.body if isinstance(x, ast.If) and 'ProcessPoolExecutor' in ast.unparse(x))
        section.body = [x for x in section.body if not isinstance(x, ast.ImportFrom)]
        code = compile(ast.fix_missing_locations(ast.Module(body=[section], type_ignores=[])), '<actual-executor-block>', 'exec')
        events = []
        pool_factory = lambda **kwargs: FakePool(events, **kwargs)
        def complete(futures): return list(futures)
        scope = {'job': {'dryrun': False, 'workers': 2, 'audit_seeds': [1]}, 'worker_contract': {'audit_stop_fd': 7, 'audit_backup_fd': 8},
                 'configs': {'a': {'files': {}}, 'b': {'files': {}}}, 'node': 'n', 'out': 'out', 'run_config': lambda *a: None,
                 'ProcessPoolExecutor': pool_factory, 'as_completed': complete, 'get_context': lambda name: name,
                 'run_notifying_audit': module.run_notifying_audit, 'cache': {}, 'save_cache': lambda: None}
        with patch.object(module.os, 'fstat', side_effect=lambda fd: SimpleNamespace(st_mode=stat.S_IFIFO,st_dev=1,st_ino=fd)), patch.object(module.fcntl, 'fcntl', return_value=os.O_WRONLY | os.O_NONBLOCK), patch.object(module.os, 'write', side_effect=lambda fd, data: events.append('notify') or 1):
            with self.assertRaisesRegex(RuntimeError, 'audit failed'):
                exec(code, scope)
        self.assertEqual(events, ['future result 1', 'notify', 'notify', 'pool shutdown'])

    def test_runner_monitor_calls_owned_guardian_before_reporting(self):
        events = []
        process = SimpleNamespace(poll=lambda: None)
        containment = SimpleNamespace(freeze=lambda: events.append('guardian freeze'))
        monitor = module.AuditStopMonitor((8,9), process, containment)
        with patch.object(module.os, 'read', return_value=b'S'):
            monitor._run()
        self.assertEqual(events, ['guardian freeze'])
        self.assertTrue(monitor.stopping.is_set())
        with self.assertRaises(module.AuditNotificationStop): monitor.check()

    def test_unexpected_monitor_failure_attempts_guardian_freeze(self):
        events = []
        process = SimpleNamespace(poll=lambda: None)
        monitor = module.AuditStopMonitor((8,9), process, SimpleNamespace(freeze=lambda: events.append('guardian freeze')))
        with patch.object(module.os, 'read', side_effect=RuntimeError('unexpected failure')):
            monitor._run()
        self.assertEqual(events, ['guardian freeze'])
        with self.assertRaises(module.AuditNotificationStop): monitor.check()

    def test_normal_completion_marker_required_and_eof_after_marker_is_safe(self):
        events = []
        process = SimpleNamespace(poll=lambda: 0)
        monitor = module.AuditStopMonitor((8,9), process, SimpleNamespace(freeze=lambda: events.append('guardian freeze')))
        reads=iter([BlockingIOError(),BlockingIOError(),b'D',BlockingIOError(),b'D',BlockingIOError()])
        def read(fd, size):
            result=next(reads)
            if isinstance(result, BaseException): raise result
            return result
        with patch.object(module.os, 'read', side_effect=read):
            monitor._run()
        self.assertTrue(all(event.is_set() for event in monitor.completed))
        self.assertEqual(events, [])
        with patch.object(module.os, 'read', return_value=b''):
            self.assertFalse(module.handle_ready_audit_channel(8, lambda: events.append('mark'), lambda: events.append('freeze'), complete_seen=lambda: True))
        monitor.thread = SimpleNamespace(join=lambda timeout: None, is_alive=lambda: False)
        monitor.finish()
        monitor.completed[0].clear()
        with self.assertRaises(module.AuditNotificationStop): monitor.finish()

    def test_exit_drain_does_not_accept_a_pending_stop(self):
        events=[]
        monitor=module.AuditStopMonitor((8,9),SimpleNamespace(poll=lambda: 0),
                                       SimpleNamespace(freeze=lambda: events.append('guardian freeze')))
        reads=iter([BlockingIOError(),BlockingIOError(),b'S'])
        def read(fd,size):
            result=next(reads)
            if isinstance(result,BaseException): raise result
            return result
        with patch.object(module.os,'read',side_effect=read):
            monitor._run()
        self.assertEqual(events,['guardian freeze'])
        with self.assertRaises(module.AuditNotificationStop): monitor.check()


if __name__ == '__main__': unittest.main()
