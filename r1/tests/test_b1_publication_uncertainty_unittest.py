"""In-memory error ordering checks; no files or processes are created."""
import hashlib
import json
import os
import stat
import importlib.util
import sys
import types
from types import SimpleNamespace
import unittest
from contextlib import nullcontext
from unittest.mock import Mock, patch

from r1.exam import b1_exit_receipt as receipt
from r1.scripts import b1_supervisor as supervisor


class UncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.names=set()
        self.head='a'*40
        self.active=b'active'
        self.state=b'state'
        self.finalized=b'final'
        self.record={'version':'b1_waited_exit/v2','runner_pid':42,'exit_code':0,
                     'supervisor_dir':'/supervisor','supervisor_sha256':'b'*64,
                     'authorization_checkout_head':self.head,
                     'active_sha256':hashlib.sha256(self.active).hexdigest(),
                     'batch_state_sha256':hashlib.sha256(self.state).hexdigest(),
                     'finalization_sha256':hashlib.sha256(self.finalized).hexdigest()}

    def lstat(self,path):
        if str(path) not in self.names: raise FileNotFoundError(str(path))
        return Mock()

    def record_uncertainty(self,path,data):
        self.names.add(str(path))

    def reader(self):
        with patch.object(receipt,'_reader_publication_lock',return_value=nullcontext()), \
             patch.object(receipt,'_require_local_filesystem'), \
             patch.object(receipt.os,'lstat',side_effect=self.lstat), \
             patch.object(receipt.os.path,'lexists',return_value=False), \
             patch.object(receipt,'read_owned_regular',return_value=json.dumps(self.record).encode()), \
             patch.object(receipt,'_supervisor_binding',return_value='b'*64), \
             patch.object(receipt,'active_and_state',return_value=(self.active,self.state)), \
             patch.object(receipt,'_verified_finalization',return_value=self.finalized):
            return receipt.verify_waited_success('/batch',self.head)

    def test_queued_error_confirmed_commit_is_terminal_without_uncertainty(self):
        with patch.object(receipt,'publish_after_wait',side_effect=RuntimeError('queued callback')), \
             patch.object(receipt,'_verify_waited_success_unlocked',return_value=self.record), \
             patch.object(supervisor,'_exclusive_json') as stop:
            supervisor._publish_or_reconcile(Mock(),'/batch',self.head,'/supervisor')
        stop.assert_not_called()

    def test_transient_reconciliation_failure_persists_reader_block(self):
        with patch.object(receipt,'publish_after_wait',side_effect=RuntimeError('queued callback')), \
             patch.object(receipt,'_verify_waited_success_unlocked',side_effect=OSError('transient read')), \
             patch.object(supervisor,'_exclusive_json',side_effect=self.record_uncertainty):
            with self.assertRaises(supervisor.PublicationUncertain):
                supervisor._publish_or_reconcile(Mock(),'/batch',self.head,'/supervisor')
        with self.assertRaisesRegex(RuntimeError,'uncertain'):
            self.reader()

    def test_uncertainty_persistence_failure_is_explicit_limit(self):
        with patch.object(receipt,'publish_after_wait',side_effect=RuntimeError('queued callback')), \
             patch.object(receipt,'_verify_waited_success_unlocked',side_effect=OSError('transient read')), \
             patch.object(supervisor,'_exclusive_json',side_effect=OSError('disk unavailable')), \
             patch('builtins.print') as report:
            with self.assertRaisesRegex(supervisor.PublicationUncertain,'NOT CHECKABLE'):
                supervisor._publish_or_reconcile(Mock(),'/batch',self.head,'/supervisor')
        self.assertIn('NOT CHECKABLE',report.call_args.args[0])
        # Without a persistent name, after reads recover the current reader
        # cannot learn about the uncertainty. This deliberately tests the
        # documented storage-failure limitation; it is not a safety claim.
        self.assertEqual(self.reader(),self.record)

    def test_cannot_stat_uncertainty_path_is_refused(self):
        with patch.object(receipt,'_reader_publication_lock',return_value=nullcontext()), \
             patch.object(receipt,'_require_local_filesystem'), \
             patch.object(receipt.os,'lstat',side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                receipt.verify_waited_success('/batch',self.head)

    def test_outer_post_return_exception_confirms_commit_without_stop(self):
        with patch.object(receipt,'_verify_waited_success_unlocked',return_value=self.record), \
             patch.object(supervisor,'_retain_on_stop') as stop:
            result=supervisor._finish_or_stop('/batch',self.head,True,
                                              RuntimeError('after publisher return'),9,'/supervisor')
        self.assertEqual(result,0)
        stop.assert_not_called()

    def test_outer_post_return_error_unverified_blocks_reader_before_stop(self):
        class Retained(Exception): pass
        def stop(*args):
            self.assertIn('/batch/'+receipt.UNCERTAIN,self.names)
            raise Retained()
        with patch.object(receipt,'_verify_waited_success_unlocked',side_effect=OSError('temporary read error')), \
             patch.object(supervisor,'_exclusive_json',side_effect=self.record_uncertainty), \
             patch.object(supervisor,'_retain_on_stop',side_effect=stop):
            with self.assertRaises(Retained):
                supervisor._finish_or_stop('/batch',self.head,True,
                                           RuntimeError('after publisher return'),9,'/supervisor')
        with self.assertRaisesRegex(RuntimeError,'uncertain'):
            self.reader()

    def test_outer_prepublication_error_stops_without_fake_success(self):
        class Retained(Exception): pass
        with patch.object(supervisor,'_handle_possible_publication_error') as reconcile, \
             patch.object(supervisor,'_retain_on_stop',side_effect=Retained):
            with self.assertRaises(Retained):
                supervisor._finish_or_stop('/batch',self.head,False,RuntimeError('before publication'),9,'/supervisor')
        reconcile.assert_not_called()


class PublicationLockTests(unittest.TestCase):
    def test_reader_rejects_held_lock_before_receipt_read(self):
        info=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=os.getuid(),st_dev=1,st_ino=2)
        with patch.object(receipt.os,'open',return_value=8), \
             patch.object(receipt.os,'fstat',return_value=info), \
             patch.object(receipt.os,'stat',return_value=info), \
             patch.object(receipt.os,'close') as close, \
             patch.object(receipt.fcntl,'flock',side_effect=BlockingIOError('supervisor holds lock')), \
             patch.object(receipt,'_verify_waited_success_unlocked') as read:
            with self.assertRaises(BlockingIOError): receipt.verify_waited_success('/batch','head')
        close.assert_called_once_with(8)
        read.assert_not_called()

    def test_reader_retains_lock_through_whole_verification(self):
        info=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=os.getuid(),st_dev=1,st_ino=2)
        operations=[]
        with patch.object(receipt.os,'open',return_value=8), \
             patch.object(receipt.os,'fstat',return_value=info), \
             patch.object(receipt.os,'stat',return_value=info), \
             patch.object(receipt.os,'close',side_effect=lambda fd: operations.append('close')), \
             patch.object(receipt.fcntl,'flock',side_effect=lambda fd,flags: operations.append('flock')), \
             patch.object(receipt,'_verify_waited_success_unlocked',side_effect=lambda *a: operations.append('verify') or 'ok'):
            self.assertEqual(receipt.verify_waited_success('/batch','head'),'ok')
        self.assertEqual(operations,['flock','verify','close'])

    def test_supervisor_holds_lock_fd_after_acquiring(self):
        with patch.object(supervisor.os,'open',return_value=8), \
             patch.object(supervisor.fcntl,'flock') as flock, \
             patch.object(supervisor.os,'close') as close:
            self.assertEqual(supervisor._hold_publication_lock('/batch'),8)
        flock.assert_called_once()
        close.assert_not_called()


class FullBatchEntryTests(unittest.TestCase):
    def test_full_batch_entry_refuses_when_publication_lock_held(self):
        modules={}
        def fake(name, **members):
            item=types.ModuleType(name)
            item.__dict__.update(members)
            modules[name]=item
        fn=Mock()
        fake('r1.exam.analyze',thinking_off_capable=fn)
        fake('r1.exam.guards',digest_file=fn)
        fake('r1.exam.runtime',author_gate=Mock(return_value='a'*40),read_registry=fn,
             verify_campaign=fn,_verify_b1_root_authority=fn,b1_harness_sources=fn)
        fake('r1.scripts.exam_runner',stage_a_pass_set=fn,anchor_gate=fn,verify_anchor_reference=fn)
        fake('r1.exam.campaign',cache_prompt_evidence=fn,read_rows=fn)
        fake('r1.exam.b1_observer_journal',validate_observer_journal=fn)
        fake('r1.liveness.check',evaluate_ledger_paths=fn)
        fake('r1.harness',harness_root=Mock(return_value='/harness'))
        fake('autoresearch'); modules['autoresearch'].__path__=[]
        fake('autoresearch.nodes'); modules['autoresearch.nodes'].__path__=[]
        fake('autoresearch.nodes.registry',load_registered_node=fn)
        fake('r1.c3.features',replay_campaign=fn,files_hash=fn)
        fake('r1.c3.audit',paired=fn)
        fake('r1.exam.observer',_authorized_candidate=fn)
        spec=importlib.util.spec_from_file_location('synthetic_b1_batch','r1/exam/b1_batch.py')
        module=importlib.util.module_from_spec(spec)
        info=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=os.getuid(),st_dev=1,st_ino=2)
        with patch.dict(sys.modules,modules), \
             patch.object(receipt.os,'open',return_value=8), \
             patch.object(receipt.os,'fstat',return_value=info), \
             patch.object(receipt.os,'stat',return_value=info), \
             patch.object(receipt.os,'close'), \
             patch.object(receipt.fcntl,'flock',side_effect=BlockingIOError('supervisor active')), \
             patch.object(receipt,'_verify_waited_success_unlocked') as read:
            spec.loader.exec_module(module)
            with patch.object(module.Path,'resolve',lambda path,**kw:path), \
                 patch.object(module,'refuse_sealed'),patch.object(module,'_reject_stop_record'), \
                 patch.object(module,'_inside'), \
                 patch.object(module.subprocess,'check_output',side_effect=['pin','']):
                with self.assertRaisesRegex(ValueError,'waited-exit evidence unavailable'):
                    module.verify_batch('/batch',{'nodes':[],'harness_commit':'pin'},'rule')
        read.assert_not_called()


    def test_full_batch_entry_refuses_persisted_supervisor_stop(self):
        modules={}
        def fake(name, **members):
            item=types.ModuleType(name)
            item.__dict__.update(members)
            modules[name]=item
        fn=Mock()
        fake('r1.exam.analyze',thinking_off_capable=fn)
        fake('r1.exam.guards',digest_file=fn)
        fake('r1.exam.runtime',author_gate=Mock(return_value='a'*40),read_registry=fn,
             verify_campaign=fn,_verify_b1_root_authority=fn,b1_harness_sources=fn)
        fake('r1.scripts.exam_runner',stage_a_pass_set=fn,anchor_gate=fn,verify_anchor_reference=fn)
        fake('r1.exam.campaign',cache_prompt_evidence=fn,read_rows=fn)
        fake('r1.exam.b1_observer_journal',validate_observer_journal=fn)
        fake('r1.liveness.check',evaluate_ledger_paths=fn)
        fake('r1.harness',harness_root=Mock(return_value='/harness'))
        fake('autoresearch'); modules['autoresearch'].__path__=[]
        fake('autoresearch.nodes'); modules['autoresearch.nodes'].__path__=[]
        fake('autoresearch.nodes.registry',load_registered_node=fn)
        fake('r1.c3.features',replay_campaign=fn,files_hash=fn)
        fake('r1.c3.audit',paired=fn)
        fake('r1.exam.observer',_authorized_candidate=fn)
        spec=importlib.util.spec_from_file_location('synthetic_b1_batch','r1/exam/b1_batch.py')
        module=importlib.util.module_from_spec(spec)
        info=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=os.getuid(),st_dev=1,st_ino=2)
        binding=SupervisorBindingTests()
        binding.setUp()
        binding.names.add('/work/supervisor/SUPERVISOR_STOP.json')
        with patch.dict(sys.modules,modules), \
             patch.object(receipt.os,'open',return_value=8), \
             patch.object(receipt.os,'fstat',return_value=info), \
             patch.object(receipt.os,'stat',return_value=info), \
             patch.object(receipt.os,'close'), \
             patch.object(receipt.fcntl,'flock'), \
             patch.object(receipt,'_require_local_filesystem'), \
             patch.object(receipt.os,'lstat',side_effect=binding.lstat), \
             patch.object(receipt.os.path,'lexists',return_value=False), \
             patch.object(receipt,'read_owned_regular',side_effect=binding.read), \
             patch.object(receipt,'active_and_state',return_value=(binding.active,binding.state)), \
             patch.object(receipt,'_verified_finalization',return_value=binding.finalized):
            spec.loader.exec_module(module)
            with patch.object(module.Path,'resolve',lambda path,**kw:path), \
                 patch.object(module,'refuse_sealed'),patch.object(module,'_reject_stop_record'), \
                 patch.object(module,'_inside'), \
                 patch.object(module.subprocess,'check_output',side_effect=['pin','']):
                with self.assertRaisesRegex(ValueError,'waited-exit evidence unavailable'):
                    module.verify_batch('/work/batch',{'nodes':[],'harness_commit':'pin'},'rule')



class SupervisorBindingTests(unittest.TestCase):
    def setUp(self):
        self.head='a'*40
        self.binding=json.dumps({'head':self.head,'out':'/work/batch','pid':42,'start_ticks':77}).encode()
        self.binding_sha=hashlib.sha256(self.binding).hexdigest()
        self.active=b'active';self.state=b'state';self.finalized=b'final'
        self.record={'version':'b1_waited_exit/v2','runner_pid':42,'exit_code':0,
                     'authorization_checkout_head':self.head,'supervisor_dir':'/work/supervisor',
                     'supervisor_sha256':self.binding_sha,'active_sha256':hashlib.sha256(self.active).hexdigest(),
                     'batch_state_sha256':hashlib.sha256(self.state).hexdigest(),
                     'finalization_sha256':hashlib.sha256(self.finalized).hexdigest()}
        self.names=set()

    def lstat(self,path):
        if str(path)=='/work/supervisor':
            return SimpleNamespace(st_mode=stat.S_IFDIR|0o700,st_uid=os.getuid())
        if str(path) in self.names: return Mock()
        raise FileNotFoundError(str(path))

    def read(self,path):
        if str(path).endswith('/SUPERVISOR.json'): return self.binding
        return json.dumps(self.record).encode()

    def verify(self):
        with patch.object(receipt,'_reader_publication_lock',return_value=nullcontext()), \
             patch.object(receipt,'_require_local_filesystem'), \
             patch.object(receipt.Path,'resolve',lambda p,**kw:p), \
             patch.object(receipt.os,'lstat',side_effect=self.lstat), \
             patch.object(receipt.os.path,'lexists',return_value=False), \
             patch.object(receipt,'read_owned_regular',side_effect=self.read), \
             patch.object(receipt,'active_and_state',return_value=(self.active,self.state)), \
             patch.object(receipt,'_verified_finalization',return_value=self.finalized):
            return receipt.verify_waited_success('/work/batch',self.head)

    def test_valid_receipt_with_bound_supervisor(self):
        self.assertEqual(self.verify(),self.record)

    def test_persisted_supervisor_stop_refuses_valid_receipt(self):
        self.names.add('/work/supervisor/SUPERVISOR_STOP.json')
        with self.assertRaisesRegex(RuntimeError,'supervisor STOP'): self.verify()

    def test_bad_or_missing_binding_refuses_receipt(self):
        for bad in (b'{', json.dumps({'head':self.head,'out':'/work/wrong','pid':42,'start_ticks':77}).encode()):
            with self.subTest(binding=bad):
                self.binding=bad
                with self.assertRaises(RuntimeError): self.verify()
        self.binding=json.dumps({'head':self.head,'out':'/work/batch','pid':42,'start_ticks':77}).encode()
        self.record['supervisor_dir']='/different/supervisor'
        with self.assertRaisesRegex(RuntimeError,'canonical sibling'): self.verify()

    def test_failed_uncertainty_write_then_persisted_supervisor_stop_refuses(self):
        class Retained(Exception): pass
        def retain(*args):
            self.names.add('/work/supervisor/SUPERVISOR_STOP.json')
            raise Retained()
        with patch.object(receipt,'_verify_waited_success_unlocked',side_effect=OSError('transient read')), \
             patch.object(supervisor,'_exclusive_json',side_effect=OSError('batch write failed')), \
             patch.object(supervisor,'_retain_on_stop',side_effect=retain), \
             patch('builtins.print'):
            with self.assertRaises(Retained):
                supervisor._finish_or_stop('/work/batch',self.head,True,RuntimeError('callback'),9,'/work/supervisor')
        self.assertNotIn('/work/batch/'+receipt.UNCERTAIN,self.names)
        with self.assertRaisesRegex(RuntimeError,'supervisor STOP'): self.verify()
