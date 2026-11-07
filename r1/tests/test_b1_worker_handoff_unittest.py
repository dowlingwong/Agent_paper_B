"""In-memory handshake tests; no OS pipes, signals, files or subprocesses."""
import copy
import json
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, mock_open

from r1.exam import b1_worker_handoff as h, b1_worker_entry, campaign, runtime


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
        h.consume_verified(self.job)
        with self.assertRaisesRegex(RuntimeError,'bootstrap handoff absent'):
            h.consume_verified(self.job)

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
        with patch.object(h,'consume_verified',side_effect=RuntimeError('STOP: no handoff')), \
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
        child=MagicMock();child.pid=102
        log=mock_open();log.return_value.__enter__.return_value.fileno.return_value=11
        events=[]
        child.wait.side_effect=lambda **kw: events.append('wait') or 2
        with patch.object(Path,'resolve',lambda p,**kw:p),patch.object(Path,'mkdir'), \
             patch.object(Path,'open',log),patch.object(runtime,'write_json'), \
             patch.object(runtime,'worker_environment',return_value={}), \
             patch.object(runtime.os,'pipe',return_value=(8,9)), \
             patch.object(runtime.os,'close',side_effect=lambda fd:events.append(('close',fd))), \
             patch.object(runtime.subprocess,'Popen',return_value=child) as popen, \
             patch.object(h,'make_record') as record,patch.object(h,'release') as release:
            with self.assertRaisesRegex(OSError,'disk'): runner.run_job(job,'r1.exam.campaign')
            record.assert_not_called();release.assert_not_called()
            self.assertEqual(events,[('close',8),('close',9),'wait'])
            self.assertEqual(popen.call_args.kwargs['stdout'],runtime.subprocess.DEVNULL)
            self.assertEqual(popen.call_args.kwargs['stderr'],runtime.subprocess.DEVNULL)
            self.assertEqual(popen.call_args.kwargs['env']['PYTHONDONTWRITEBYTECODE'],'1')

    def test_missing_lease_or_wrong_module_stops_before_root_creation(self):
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.state={'phase':'b1'};runner.cfg={'dryrun':False};runner.out=Path('/work/batch')
        runner.b1_lease_fd=None;runner.space=MagicMock();runner.child=None
        with patch.object(Path,'mkdir') as mkdir,patch.object(runtime,'write_json') as write:
            with self.assertRaisesRegex(runtime.PreparationStop,'lease is missing'):
                runner.run_job({'out':self.job['out']},'r1.exam.campaign')
            runner.b1_lease_fd=7
            with self.assertRaisesRegex(runtime.PreparationStop,'reviewed campaign'):
                runner.run_job({'out':self.job['out']},'r1.exam.other')
            runner.child=MagicMock()
            with self.assertRaisesRegex(runtime.PreparationStop,'previous B1 child'):
                runner.run_job({'out':self.job['out']},'r1.exam.campaign')
            mkdir.assert_not_called();write.assert_not_called()

    def test_release_failure_reaps_child_before_reporting_stop(self):
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.state={'phase':'b1'};runner.cfg={'dryrun':False};runner.out=Path('/work/batch')
        runner.b1_lease_fd=7;runner.service=None;runner.space=MagicMock();runner.save=MagicMock();runner.child=None
        child=MagicMock();child.pid=102
        events=[];child.wait.side_effect=lambda **kw: events.append('wait') or 2
        log=mock_open();log.return_value.__enter__.return_value.fileno.return_value=11
        with patch.object(Path,'resolve',lambda p,**kw:p),patch.object(Path,'mkdir'), \
             patch.object(Path,'open',log),patch.object(runtime,'write_json'), \
             patch.object(runtime,'worker_environment',return_value={}), \
             patch.object(runtime.os,'pipe',return_value=(8,9)), \
             patch.object(runtime.os,'close',side_effect=lambda fd:events.append(('close',fd))), \
             patch.object(runtime.subprocess,'Popen',return_value=child), \
             patch.object(h,'make_record',return_value={}), \
             patch.object(h,'release',side_effect=BrokenPipeError('EOF')):
            with self.assertRaisesRegex(BrokenPipeError,'EOF'): runner.run_job({'out':self.job['out']},'r1.exam.campaign')
            self.assertEqual(events,[('close',8),('close',9),'wait'])
            child.kill.assert_not_called();child.terminate.assert_not_called()

    def test_unreaped_child_is_explicit_stop_without_signal(self):
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.state={'phase':'b1'};runner.cfg={'dryrun':False};runner.out=Path('/work/batch')
        runner.b1_lease_fd=7;runner.service=None;runner.space=MagicMock();runner.save=MagicMock(side_effect=OSError('original'));runner.child=None
        child=MagicMock();child.pid=102;child.wait.side_effect=TimeoutError('wait')
        log=mock_open();log.return_value.__enter__.return_value.fileno.return_value=11
        with patch.object(Path,'resolve',lambda p,**kw:p),patch.object(Path,'mkdir'), \
             patch.object(Path,'open',log),patch.object(runtime,'write_json'), \
             patch.object(runtime,'worker_environment',return_value={}), \
             patch.object(runtime.os,'pipe',return_value=(8,9)),patch.object(runtime.os,'close'), \
             patch.object(runtime.subprocess,'Popen',return_value=child):
            with self.assertRaisesRegex(runtime.PreparationStop,'not reaped.*original'):
                runner.run_job({'out':self.job['out']},'r1.exam.campaign')
            child.kill.assert_not_called();child.terminate.assert_not_called()

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

    def test_raw_output_alias_refused_before_host_or_registry(self):
        cfg={'dryrun':False}
        def resolve(path,**kwargs):
            return Path('/work/newbatch') if path==Path('/work/alias') else path
        with patch.object(Path,'resolve',resolve), \
             patch.object(runtime,'host_check') as host, \
             patch.object(runtime,'read_registry') as registry:
            with self.assertRaisesRegex(runtime.PreparationStop,'alias or symlink'):
                runtime.ExamRunner(cfg,'/work/alias',b1_config_head='a'*40)
            host.assert_not_called();registry.assert_not_called()

    def test_unresolvable_output_refused_before_host(self):
        with patch.object(Path,'resolve',side_effect=RuntimeError('loop')), \
             patch.object(runtime,'host_check') as host:
            with self.assertRaisesRegex(runtime.PreparationStop,'cannot be resolved'):
                runtime.ExamRunner({'dryrun':False},'/work/alias',b1_config_head='a'*40)
            host.assert_not_called()

    def test_bootstrap_handoff_failure_is_silent_and_does_not_attach(self):
        job={'phase':'b1','dryrun':False}
        with patch.object(Path,'read_text',return_value=json.dumps(job)), \
             patch.object(b1_worker_entry,'await_parent',side_effect=RuntimeError('STOP: EOF')), \
             patch.object(b1_worker_entry,'attach_log') as attach, \
             patch.object(campaign,'collect') as collect:
            self.assertEqual(b1_worker_entry.main(['--job','/fake/job.json']),2)
            attach.assert_not_called();collect.assert_not_called()

    def test_log_attaches_only_verified_regular_parent_descriptor(self):
        env={h.LOG_FD_ENV:'11'}
        with patch.dict(h.os.environ,env,clear=True),patch.object(h.os,'fstat',return_value=self.file), \
             patch.object(h.os,'stat',return_value=self.file),patch.object(h.os,'getuid',return_value=501), \
             patch.object(h.os,'dup2') as dup,patch.object(h.os,'close') as close:
            h.attach_log(self.job)
            self.assertEqual([x.args for x in dup.call_args_list],[(11,1),(11,2)])
            close.assert_called_once_with(11)


if __name__=='__main__': unittest.main()
