"""In-memory handshake tests; no OS pipes, signals, files or subprocesses."""
import copy
import json
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, mock_open

from r1.exam import b1_worker_handoff as h, campaign, runtime


def inode(dev=10,ino=20,uid=501,mode=stat.S_IFREG|0o600,nlink=1):
    return SimpleNamespace(st_dev=dev,st_ino=ino,st_uid=uid,st_mode=mode,st_nlink=nlink)


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.job={'out':'/work/batch/a/b1/off/digits_mlp__s9001','base_url':None,'phase':'b1','dryrun':False}
        self.fd=7; self.pipe=8; self.parent=101; self.child=102
        self.record={'version':'b1-worker-handoff/v1','job_sha256':h._digest_job(self.job),
                     'parent_pid':self.parent,'parent_start_ticks':1101,
                     'child_pid':self.child,'child_start_ticks':1102,
                     'lease_fd':self.fd,'lease_dev':10,'lease_ino':20,'lease_uid':501,
                     'root':self.job['out'],'root_dev':30,'root_ino':40,'root_uid':501,'server':None}
        self.env={h.HANDOFF_FD_ENV:str(self.pipe),h.LEASE_FD_ENV:str(self.fd)}
        self.file=inode();self.root=(30,40,501,stat.S_IFDIR|0o700)

    def wait(self, record=None, job=None, *, ready=True, raw=None, parent=101, lease=None, root=None):
        record=self.record if record is None else record
        payload=raw if raw is not None else (json.dumps(record)+'\n').encode()
        lease=self.file if lease is None else lease
        with patch.dict(h.os.environ,self.env,clear=True), \
             patch.object(h.select,'select',return_value=([self.pipe] if ready else [],[],[])), \
             patch.object(h.os,'read',return_value=payload), patch.object(h.os,'close'), \
             patch.object(h.os,'getppid',return_value=parent), patch.object(h.os,'getpid',return_value=self.child), \
             patch.object(h.os,'getuid',return_value=501),patch.object(h.os,'fstat',return_value=lease), \
             patch.object(h.os,'stat',return_value=self.file), \
             patch.object(h,'_identity',return_value=root or self.root), \
             patch.object(h,'process_start_ticks',side_effect=lambda pid:pid+1000), \
             patch.object(Path,'resolve',lambda p,**kw:p),patch.object(Path,'home',return_value=Path('/home/me')):
            return h.await_parent(self.job if job is None else job)

    def test_valid_software_anchor(self):
        self.assertEqual(self.wait(),self.record)

    def test_parent_binds_child_lease_and_new_root(self):
        from r1.exam import b1_lease
        with patch.object(h.os,'getpid',return_value=self.parent), \
             patch.object(h.os,'getuid',return_value=501), \
             patch.object(h.os,'fstat',return_value=self.file), \
             patch.object(h.os,'stat',return_value=self.file), \
             patch.object(h,'_identity',return_value=self.root), \
             patch.object(h,'process_start_ticks',side_effect=lambda pid:pid+1000), \
             patch.object(Path,'resolve',lambda p,**kw:p), \
             patch.object(Path,'home',return_value=Path('/home/me')), \
             patch.object(b1_lease,'verify_server_fd') as check:
            record=h.make_record(self.job,self.child,self.fd,Path(self.job['out']),None)
            self.assertEqual(record,self.record)
            check.assert_called_once_with(self.fd,self.child)

    def test_missing_fds_refused_before_read(self):
        with patch.dict(h.os.environ,{},clear=True),patch.object(h.os,'read') as read:
            with self.assertRaisesRegex(RuntimeError,'no inherited'):
                h.await_parent(self.job)
            read.assert_not_called()

    def test_timeout_and_eof_refused(self):
        with self.assertRaisesRegex(RuntimeError,'timed out'): self.wait(ready=False)
        with self.assertRaisesRegex(RuntimeError,'handoff'): self.wait(raw=b'')

    def test_job_parent_lease_and_root_mismatches_refused(self):
        cases=[('job_sha256','0'*64),('parent_pid',999),('child_pid',999),
               ('parent_start_ticks',9),('child_start_ticks',9),('lease_fd',4),
               ('lease_ino',21),('root_ino',41),('root','/work/other')]
        for key,value in cases:
            altered=copy.deepcopy(self.record);altered[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(RuntimeError,'STOP:'):
                self.wait(altered)

    def test_llm_server_requires_matching_endpoint_parent_and_fd(self):
        job={**self.job,'base_url':'http://127.0.0.1:1234/v1'}
        record=copy.deepcopy(self.record);record['job_sha256']=h._digest_job(job)
        record['server']={'pid':103,'start_ticks':1103,'base_url':job['base_url']}
        self.env['LLAMACPP_BASE_URL']=job['base_url']
        with patch.object(h,'_proc_ppid',return_value=self.parent):
            self.assertEqual(self.wait(record,job),record)
        with patch.object(h,'_proc_ppid',return_value=999):
            with self.assertRaisesRegex(RuntimeError,'server lifetime'): self.wait(record,job)
        self.env['LLAMACPP_BASE_URL']='http://127.0.0.1:9999/v1'
        with self.assertRaisesRegex(RuntimeError,'endpoint'): self.wait(record,job)

    def test_child_does_not_mutate_before_handoff(self):
        job={'phase':'b1','dryrun':False,'out':self.job['out']}
        with patch.object(h,'await_parent',side_effect=RuntimeError('STOP: no handoff')), \
             patch.object(campaign,'_verify_b1_worker_input') as auth, \
             patch.object(Path,'mkdir') as mkdir,patch.object(campaign,'B1IntegrityWorker') as worker:
            with self.assertRaisesRegex(RuntimeError,'handoff'): campaign._collect_b1_review(job)
            auth.assert_not_called();mkdir.assert_not_called();worker.assert_not_called()

    def test_parent_save_failure_closes_pipe_without_release(self):
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.state={'phase':'b1'};runner.cfg={'dryrun':False};runner.out=Path('/work/batch')
        runner.b1_lease_fd=7;runner.service=None;runner.space=MagicMock();runner.save=MagicMock(side_effect=OSError('disk'))
        runner.child=None
        job={'out':self.job['out'],'base_url':None}
        child=SimpleNamespace(pid=102)
        with patch.object(Path,'resolve',lambda p,**kw:p),patch.object(Path,'mkdir'), \
             patch.object(Path,'open',mock_open()),patch.object(runtime,'write_json'), \
             patch.object(runtime,'worker_environment',return_value={}), \
             patch.object(runtime.os,'pipe',return_value=(8,9)),patch.object(runtime.os,'close') as close, \
             patch.object(runtime.subprocess,'Popen',return_value=child), \
             patch.object(h,'make_record') as record,patch.object(h,'release') as release:
            with self.assertRaisesRegex(OSError,'disk'): runner.run_job(job,'r1.exam.campaign')
            record.assert_not_called();release.assert_not_called()
            self.assertEqual([x.args[0] for x in close.call_args_list],[8,9])

    def test_existing_batch_stops_before_lease(self):
        from r1.exam import b1_lease
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.state={};runner.cfg={'dryrun':False,'work_dir':'/work','nodes':[]}
        runner.out=Path('/work/existing');runner.rule={'version':'x5_rule/v2'}
        runner.rule_sha='f'*64;runner.b1_config_head='a'*40;runner.registry_path=Path('/fake');runner.registry={}
        with patch.object(runtime,'require_committed_b1_config',return_value='a'*40), \
             patch.object(runtime,'require_committed_b1_registry'), \
             patch.object(runtime,'author_gate',return_value='a'*40), \
             patch.object(runtime,'worker_environment'), \
             patch.object(Path,'mkdir',side_effect=FileExistsError), \
             patch.object(b1_lease,'acquire') as acquire:
            with self.assertRaisesRegex(runtime.PreparationStop,'already exists'):
                runner.start('b1')
            acquire.assert_not_called()


if __name__=='__main__': unittest.main()
