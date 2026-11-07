"""In-memory contract checks; no real processes, sockets or filesystem writes."""
import copy
import json
import os
import stat
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from r1.exam import b1_worker_contract as contract


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.out='/synthetic/work/batch/anchor/b1/off/digits_mlp__s9001'
        self.job={'out':self.out,'candidate':{'id':'random_valid','kind':'random_valid'},'base_url':None,
                  'mode':'off','node':'digits_mlp','seed':9001}
        self.ctx={'version':'b1_worker_contract/v3','parent_pid':11,'parent_ticks':22,'parent_pidfd':30,
                  'supervisor_pid':13,'supervisor_ticks':22,'supervisor_pidfd':37,'supervisor_live_fd':38,
                  'guardian_pid':14,'guardian_ticks':22,'guardian_pidfd':39,
                  'lease_fd':31,'root_fd':32,'leaf_fd':33,'output_fd':34,'membership':'/user/batch',
                  'leaf':'worker-'+'a'*32,'out':self.out,'job_sha256':contract._job_sha(self.job),'audit_stop_fd':41,'audit_backup_fd':42,
                  'server_pid':None,'server_ticks':None,'server_pidfd':None,'server_leaf_fd':None,'server_url':None}
        self.env={contract.ENV_KEY:json.dumps(self.ctx)}

    def mocked(self):
        stack=ExitStack()
        stack.enter_context(mock.patch.object(contract.os,'getppid',return_value=11))
        stack.enter_context(mock.patch.object(contract.os,'getpid',return_value=12))
        stack.enter_context(mock.patch.object(contract.os,'getuid',return_value=100))
        stack.enter_context(mock.patch.object(contract.os,'fstat',return_value=SimpleNamespace(st_uid=100,st_mode=stat.S_IFDIR|0o700)))
        stack.enter_context(mock.patch('r1.exam.cache_proc.process_start_ticks',return_value=22))
        stack.enter_context(mock.patch('r1.exam.b1_lease.adopt_inherited'))
        stack.enter_context(mock.patch('r1.exam.b1_lease.verify_server_fd'))
        stack.enter_context(mock.patch('r1.exam.b1_audit_stop.require_notify_fds'))
        stack.enter_context(mock.patch.object(contract,'_pidfd_alive',return_value=True))
        stack.enter_context(mock.patch.object(contract,'_fd_quiet',return_value=True))
        stack.enter_context(mock.patch.object(contract,'_parent_runner',return_value=True))
        stack.enter_context(mock.patch.object(contract,'_membership',return_value='/user/batch/worker-'+'a'*32))
        stack.enter_context(mock.patch.object(contract,'_same_dir',return_value=True))
        stack.enter_context(mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p))
        return stack

    def test_parent_bound_software_anchor_passes(self):
        with self.mocked():
            self.assertEqual(contract.verify_worker_contract(self.job,self.env)['out'],self.out)

    def test_direct_entry_without_contract_refuses_before_output(self):
        from r1.exam import campaign
        job={'phase':'b1','dryrun':False,'out':self.out}
        with mock.patch.dict(os.environ,{},clear=True), mock.patch.object(Path,'mkdir') as mkdir:
            with self.assertRaises(contract.WorkerContractStop): campaign._collect_b1_review(job)
        mkdir.assert_not_called()

    def test_changed_job_or_output_refused(self):
        with self.mocked():
            changed=copy.deepcopy(self.job);changed['candidate']['id']='other'
            with self.assertRaises(contract.WorkerContractStop): contract.verify_worker_contract(changed,self.env)
            changed=copy.deepcopy(self.job);changed['out']='/synthetic/work/unowned'
            with self.assertRaises(contract.WorkerContractStop): contract.verify_worker_contract(changed,self.env)

    def test_dead_parent_and_cgroup_mismatch_refused(self):
        with self.mocked():
            with mock.patch.object(contract,'_pidfd_alive',return_value=False):
                with self.assertRaises(contract.WorkerContractStop): contract.verify_worker_contract(self.job,self.env)
            with mock.patch.object(contract,'_membership',return_value='/other/worker'):
                with self.assertRaises(contract.WorkerContractStop): contract.verify_worker_contract(self.job,self.env)

    def test_descriptor_collision_and_non_owned_output_refused(self):
        with self.mocked():
            ctx={**self.ctx,'output_fd':self.ctx['lease_fd']}
            with self.assertRaises(contract.WorkerContractStop): contract.verify_worker_contract(self.job,{contract.ENV_KEY:json.dumps(ctx)})
            with mock.patch.object(contract.os,'fstat',return_value=SimpleNamespace(st_uid=999,st_mode=stat.S_IFDIR|0o700)):
                with self.assertRaises(contract.WorkerContractStop): contract.verify_worker_contract(self.job,self.env)

    def test_owned_server_and_socket_checked(self):
        job=copy.deepcopy(self.job);job['candidate']={'id':'qwen25_coder_7b'};job['base_url']='http://127.0.0.1:1234/v1'
        ctx={**self.ctx,'job_sha256':contract._job_sha(job),'server_pid':55,'server_ticks':66,'server_pidfd':35,
             'server_leaf_fd':36,'server_url':job['base_url']}
        env={contract.ENV_KEY:json.dumps(ctx),'LLAMACPP_BASE_URL':job['base_url']}
        def membership(pid):return '/user/batch/worker-'+'a'*32 if pid==12 else '/user/batch/server-'+'b'*32
        def ticks(pid):return 66 if pid==55 else 22
        with self.mocked(), mock.patch.object(contract,'_membership',side_effect=membership), \
             mock.patch('r1.exam.cache_proc.process_start_ticks',side_effect=ticks), \
             mock.patch.object(contract,'_server_listener',return_value=True) as listener, \
             mock.patch('r1.exam.b1_lease.verify_server_fd') as lease:
            contract.verify_worker_contract(job,env)
            listener.assert_called_once_with(55,job['base_url']);lease.assert_any_call(31,55);lease.assert_any_call(31,14)
            with mock.patch.object(contract,'_server_listener',return_value=False):
                with self.assertRaises(contract.WorkerContractStop):contract.verify_worker_contract(job,env)
            bad={**env,'LLAMACPP_BASE_URL':'http://127.0.0.1:9999/v1'}
            with self.assertRaises(contract.WorkerContractStop):contract.verify_worker_contract(job,bad)

    def test_software_anchor_rejects_server(self):
        ctx={**self.ctx,'server_pid':55}
        with self.mocked():
            with self.assertRaises(contract.WorkerContractStop):contract.verify_worker_contract(self.job,{contract.ENV_KEY:json.dumps(ctx)})


class ListenerTests(unittest.TestCase):
    def test_owned_loopback_listener_and_wrong_socket(self):
        row='  0: 0100007F:04D2 00000000:0000 0A 00000000:00000000 00:00000000 00000000 100 0 123456 1'
        ns=SimpleNamespace(st_dev=7,st_ino=8)
        with mock.patch.object(contract.os,'stat',return_value=ns), \
             mock.patch.object(Path,'read_text',return_value='header\n'+row+'\n'), \
             mock.patch.object(Path,'iterdir',return_value=[Path('/fake/fd/7')]), \
             mock.patch.object(contract.os,'readlink',return_value='socket:[123456]'):
            self.assertTrue(contract._server_listener(55,'http://127.0.0.1:1234/v1'))
            self.assertFalse(contract._server_listener(55,'http://127.0.0.1:1235/v1'))
            self.assertFalse(contract._server_listener(55,'http://localhost:1234/v1'))


class ParentSpawnTests(unittest.TestCase):
    def test_real_parent_spawn_passes_worker_contract_fds_and_job(self):
        import threading
        from r1.exam import b1_cgroup as control
        instance=control.B1Containment.__new__(control.B1Containment)
        instance._spawn_lock=threading.RLock();instance._grant_lock=threading.RLock()
        instance._stop_requested=threading.Event();instance._frozen=False
        instance.guardian=mock.Mock(pid=222);instance.guardian.poll.return_value=None
        instance.membership='/owned';instance.root_fd=24;instance.parent_pidfd=23;instance._leaves={}
        instance._leaf=mock.Mock(return_value=('worker-'+'a'*32,8,9,10));instance.require_guardian=mock.Mock()
        instance.verify_live_lease=mock.Mock()
        instance.freeze=mock.Mock();process=mock.Mock(pid=123);process.poll.return_value=None;process.returncode=None
        stdout=mock.Mock();stdout.fileno.return_value=30
        info=SimpleNamespace(st_dev=1,st_ino=2,st_uid=100,st_mode=stat.S_IFDIR|0o700)
        job={'out':'/synthetic/root','candidate':{'id':'random_valid','kind':'random_valid'},'base_url':None,
             'mode':'off','node':'digits_mlp','seed':9001}
        supervisor={'pid':333,'start_ticks':444,'pidfd':27,'live_fd':28,'lease_fd':22}
        with mock.patch.object(control.os,'pipe',side_effect=[(11,12),(13,14),(15,16)]), \
             mock.patch.object(control.os,'open',return_value=25),mock.patch.object(control.os,'close'), \
             mock.patch.object(control.os,'getuid',return_value=100),mock.patch.object(control.os,'getpid',return_value=111), \
             mock.patch.object(control.os,'write',side_effect=lambda fd,data:len(data)), \
             mock.patch.object(control.os,'fstat',return_value=info),mock.patch.object(control.os,'stat',return_value=info), \
             mock.patch.object(control.os,'pidfd_open',side_effect=[26,40],create=True), \
             mock.patch('r1.exam.cache_proc.process_start_ticks',return_value=222), \
             mock.patch('r1.exam.b1_audit_stop.require_notify_fds'), \
             mock.patch('r1.exam.cooperative_lease.kcmp_file_result',return_value=(0,0)), \
             mock.patch.object(control.subprocess,'Popen',return_value=process) as popen, \
             mock.patch.object(control,'_read_one',side_effect=[b'M',b'']), \
             mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p), \
             mock.patch.object(Path,'read_text',return_value='0::/owned/worker-'+'a'*32+'\n'), \
             mock.patch.object(Path,'read_bytes',return_value=b'/bin/fake\0'):
            instance.spawn('worker',['/bin/fake'],env={'LLAMACPP_BASE_URL':'http://unowned'},stdout=stdout,
                           lease_fd=22,worker_context={'job':job,'out':Path(job['out']),'server':None,'supervisor':supervisor,'audit_stop_fd':41,'audit_backup_fd':42})
        kwargs=popen.call_args.kwargs
        ctx=json.loads(kwargs['env'][contract.ENV_KEY])
        self.assertEqual(ctx['job_sha256'],contract._job_sha(job))
        self.assertEqual(ctx['out'],job['out'])
        self.assertEqual(ctx['parent_pid'],111)
        self.assertEqual(ctx['audit_stop_fd'],41)
        self.assertEqual(ctx['audit_backup_fd'],42)
        self.assertNotIn('LLAMACPP_BASE_URL',kwargs['env'])
        self.assertTrue({8,22,23,24,25,26,27,28,41,42}.issubset(set(kwargs['pass_fds'])))

    def test_real_parent_binds_owned_server_before_worker_grant(self):
        import threading
        from r1.exam import b1_cgroup as control
        instance=control.B1Containment.__new__(control.B1Containment)
        instance._spawn_lock=threading.RLock();instance._grant_lock=threading.RLock()
        instance._stop_requested=threading.Event();instance._frozen=False
        instance.guardian=mock.Mock(pid=222);instance.guardian.poll.return_value=None
        instance.membership='/owned';instance.root_fd=24;instance.parent_pidfd=23
        instance._leaves={55:('server',36,37,35)}
        instance._leaf=mock.Mock(return_value=('worker-'+'a'*32,8,9,10))
        instance.require_guardian=mock.Mock();instance.verify_live_lease=mock.Mock();instance.freeze=mock.Mock()
        process=mock.Mock(pid=123);process.poll.return_value=None;process.returncode=None
        server=mock.Mock();server.process=mock.Mock(pid=55);server.process.poll.return_value=None
        server.openai_base_url='http://127.0.0.1:1234/v1'
        stdout=mock.Mock();stdout.fileno.return_value=30
        info=SimpleNamespace(st_dev=1,st_ino=2,st_uid=100,st_mode=stat.S_IFDIR|0o700)
        job={'out':'/synthetic/root','candidate':{'id':'candidate'},'base_url':server.openai_base_url,
             'mode':'off','node':'digits_mlp','seed':9001}
        supervisor={'pid':333,'start_ticks':444,'pidfd':27,'live_fd':28,'lease_fd':22}
        with mock.patch.object(control.os,'pipe',side_effect=[(11,12),(13,14),(15,16)]), \
             mock.patch.object(control.os,'open',return_value=25),mock.patch.object(control.os,'close'), \
             mock.patch.object(control.os,'getuid',return_value=100),mock.patch.object(control.os,'getpid',return_value=111), \
             mock.patch.object(control.os,'write',side_effect=lambda fd,data:len(data)), \
             mock.patch.object(control.os,'fstat',return_value=info),mock.patch.object(control.os,'stat',return_value=info), \
             mock.patch.object(control.os,'pidfd_open',side_effect=[26,40],create=True), \
             mock.patch('r1.exam.cache_proc.process_start_ticks',return_value=222), \
             mock.patch('r1.exam.b1_audit_stop.require_notify_fds'), \
             mock.patch('r1.exam.cooperative_lease.kcmp_file_result',return_value=(0,0)), \
             mock.patch.object(contract,'_server_listener',return_value=True) as listener, \
             mock.patch.object(control.subprocess,'Popen',return_value=process) as popen, \
             mock.patch.object(control,'_read_one',side_effect=[b'M',b'']), \
             mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p), \
             mock.patch.object(Path,'read_text',return_value='0::/owned/worker-'+'a'*32+'\n'), \
             mock.patch.object(Path,'read_bytes',return_value=b'/bin/fake\0'):
            instance.spawn('worker',['/bin/fake'],env={},stdout=stdout,lease_fd=22,
                           worker_context={'job':job,'out':Path(job['out']),'server':server,'supervisor':supervisor,'audit_stop_fd':41,'audit_backup_fd':42})
        ctx=json.loads(popen.call_args.kwargs['env'][contract.ENV_KEY])
        self.assertEqual(ctx['server_pid'],55)
        self.assertEqual(ctx['server_url'],server.openai_base_url)
        self.assertEqual(listener.call_count,2)
        self.assertEqual(instance.verify_live_lease.call_count,3)  # guardian, server, server recheck
        self.assertEqual(ctx['audit_stop_fd'],41)
        self.assertEqual(ctx['audit_backup_fd'],42)
        self.assertTrue({22,23,24,25,26,27,28,35,36,41,42}.issubset(set(popen.call_args.kwargs['pass_fds'])))


class ParentIdentityTests(unittest.TestCase):
    def test_runner_command_batch_and_supervisor_are_bound(self):
        repo=Path(contract.__file__).resolve().parents[2]
        batch='/synthetic/work/batch'
        job={'out':batch+'/random_valid/b1/off/digits_mlp__s9001',
             'candidate':{'id':'random_valid'},'mode':'off','node':'digits_mlp','seed':9001}
        args=['/synthetic/python','-B',str(repo/'r1/scripts/exam_runner.py'),'b1','--config',
              str(repo/'r1/scripts/configs/exam_b1_v2.json'),'--out',batch]
        cmd=b'\0'.join(x.encode() for x in args)+b'\0'
        ident=SimpleNamespace(st_dev=1,st_ino=2)
        with mock.patch.object(Path,'read_bytes',return_value=cmd), \
             mock.patch.object(Path,'read_text',return_value='11 (python) S 13'), \
             mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p), \
             mock.patch.object(contract.os,'stat',return_value=ident), \
             mock.patch.object(contract.os,'readlink',return_value=str(repo)):
            self.assertTrue(contract._parent_runner(11,13,job))
            self.assertFalse(contract._parent_runner(11,14,job))
            bad={**job,'out':'/synthetic/work/other'}
            self.assertFalse(contract._parent_runner(11,13,bad))
            bad={**job,'candidate':{'id':'../other'}}
            self.assertFalse(contract._parent_runner(11,13,bad))


if __name__ == '__main__':
    unittest.main()
