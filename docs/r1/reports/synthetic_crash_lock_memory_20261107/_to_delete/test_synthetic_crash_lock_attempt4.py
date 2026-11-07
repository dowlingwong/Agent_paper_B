"""Pure in-memory checks of explicit test-owned synthetic lock retirement."""
import ast
import errno
import json
import os
import pathlib
import signal
import stat
import sys
import types
import unittest
from contextlib import ExitStack
from unittest import mock

from r1.exam import b1_state_preserve
from r1.tests.stagea_recovery_memory import synthetic_crash_lock as recovery


class MemoryFS:
    def __init__(self):
        self.uid=os.getuid();self.device=7;self.ops=[];self.fd_next=20;self.fds={};self.offset={}
        self.root='/synthetic';self.batch=self.root+'/b1';self.partial=self.batch+'/q/b'
        self.server=self.batch+'/servers/qwen25_coder_7b/llama_server_123.json'
        self.parent=41;self.worker=42;self.server_pid=43
        def info(ino, *, directory=False, mode=0o600, device=7):
            return types.SimpleNamespace(st_mode=(stat.S_IFDIR if directory else stat.S_IFREG)|mode,
                st_uid=self.uid,st_dev=device,st_ino=ino,st_nlink=1)
        self.info=info
        self.rootinfo=info(1,directory=True,mode=0o700);self.batchinfo=info(2,directory=True,mode=0o700)
        self.serverdir=info(3,directory=True,mode=0o700);self.aliasdir=info(4,directory=True,mode=0o700)
        self.archiveinfo=info(5,directory=True,mode=0o700)
        state={'status':'RUNNING','stop_reason':None,'phase':'b1','execution_label':'DRYRUN',
               'in_progress':{'pid':self.worker,'path':self.partial}}
        cfg={'dryrun':True,'host':'DRYRUN','dryrun_root':self.root}
        server={'label':'DRYRUN','pid':self.server_pid,'alias':'qwen25_coder_7b',
                'binary':self.root+'/fake_llama_server',
                'model_path':self.root+'/models/qwen25_coder_7b.gguf'}
        self.files={(10,'.dryrun'):[info(10),b'EXAM DRYRUN; no inference\n'],
                    (10,'SYNTHETIC_parent_first.log'):[info(15),b'normal synthetic parent output\n'],
                    (10,'config.json'):[info(11),json.dumps(cfg).encode()],
                    (11,'batch_state.json'):[info(12),json.dumps(state).encode()],
                    (11,'runner.lock'):[info(13),json.dumps({'pid':self.parent,'host':'fixture'}).encode()],
                    (17,'llama_server_123.json'):[info(14),json.dumps(server).encode()]}
        self.closed=[];self.exists_stop=False;self.active_pid=None;self.fail_rename=False
        self.collision=False;self.fsync_failure=False;self.change_state=False;self.state_open_count=0
        self.archive_created=False;self.moved=None

    def open(self, name, flags, *, dir_fd=None):
        self.ops.append(('open',str(name),dir_fd))
        mapping={(None,self.root):(10,self.rootinfo),(10,'b1'):(11,self.batchinfo),
                 (11,'servers'):(16,self.serverdir),(16,'qwen25_coder_7b'):(17,self.aliasdir),
                 (11,'_to_delete'):(19,self.archiveinfo)}
        key=(dir_fd,str(name))
        if key in mapping:
            fd,info=mapping[key];self.fds[fd]=[info,None];return fd
        if key not in self.files: raise FileNotFoundError(name)
        info,data=self.files[key]
        if key==(11,'batch_state.json'):
            self.state_open_count+=1
            if self.change_state and self.state_open_count>1: data=data+b' '
        self.fd_next+=1;fd=self.fd_next;self.fds[fd]=[info,data];self.offset[fd]=0
        return fd

    def fstat(self, fd): return self.fds[fd][0]
    def read(self, fd, size):
        data=self.fds[fd][1];offset=self.offset[fd]
        result=data[offset:offset+size];self.offset[fd]+=len(result);return result
    def stat(self, name, *, dir_fd, follow_symlinks):
        assert follow_symlinks is False
        if dir_fd==11 and name in ('STOP.json','B1_COMMIT_UNCERTAIN.json'):
            if self.exists_stop:return self.info(99)
            raise FileNotFoundError(name)
        if dir_fd==19 and name=='crashed_runner_lock.'+'a'*32+'.json' and self.moved is not None:
            return self.moved[0]
        key=(dir_fd,str(name))
        if key not in self.files: raise FileNotFoundError(name)
        return self.files[key][0]
    def kill(self, pid, sig):
        self.ops.append(('kill',pid,sig));assert sig==0
        if pid==self.active_pid:return None
        raise ProcessLookupError(pid)
    def mkdir(self, name, mode, *, dir_fd):
        self.ops.append(('mkdir',name,mode,dir_fd))
        if self.archive_created:raise FileExistsError(name)
        self.archive_created=True
    def rename(self, oldfd, old, newfd, new, flags):
        self.ops.append(('rename',oldfd,old,newfd,new,flags))
        if self.collision:raise FileExistsError(new)
        if self.fail_rename:raise OSError(errno.EOPNOTSUPP,'unsupported')
        assert (oldfd,old,newfd,flags)==(11,'runner.lock',19,b1_state_preserve._NOREPLACE)
        self.moved=self.files.pop((11,'runner.lock'))
    def fsync(self,fd):
        self.ops.append(('fsync',fd))
        if self.fsync_failure:raise OSError(errno.EIO,'synthetic fsync')
    def close(self,fd):self.closed.append(fd)

    def patches(self):
        stack=ExitStack()
        for name,fn in (('open',self.open),('fstat',self.fstat),('read',self.read),('stat',self.stat),
                        ('kill',self.kill),('mkdir',self.mkdir),('fsync',self.fsync),('close',self.close)):
            stack.enter_context(mock.patch.object(recovery.os,name,side_effect=fn))
        stack.enter_context(mock.patch.object(pathlib.Path,'resolve',lambda path,strict=False:path))
        stack.enter_context(mock.patch.object(b1_state_preserve,'_renameat_dryrun',side_effect=self.rename))
        stack.enter_context(mock.patch.object(recovery.uuid,'uuid4',return_value=types.SimpleNamespace(hex='a'*32)))
        fake=types.ModuleType('r1.exam.runtime');fake.host_check=mock.Mock()
        stack.enter_context(mock.patch.dict(sys.modules,{'r1.exam.runtime':fake}))
        return stack

    def call(self, **changes):
        values={'parent_pid':self.parent,'parent_returncode':-signal.SIGKILL,
                'worker_pid':self.worker,'server_pid':self.server_pid};values.update(changes)
        return recovery.retire_test_owned_crash_lock(self.root,self.batch,self.partial,self.server,**values)


class SyntheticCrashLockTests(unittest.TestCase):
    def test_valid_crash_retains_exact_lock_without_signal(self):
        fs=MemoryFS();old=fs.files[(11,'runner.lock')][1]
        with fs.patches(): result=fs.call()
        self.assertEqual(str(result),fs.batch+'/_to_delete/crashed_runner_lock.'+'a'*32+'.json')
        self.assertEqual(fs.moved[1],old);self.assertNotIn((11,'runner.lock'),fs.files)
        self.assertEqual([x[2] for x in fs.ops if x[0]=='kill'],[0]*6)
        self.assertEqual(len(fs.closed),len(fs.fds))

    def test_recorded_stop_or_live_process_refused_before_rename(self):
        for case in ('stop','alive'):
            fs=MemoryFS();fs.exists_stop=case=='stop';fs.active_pid=fs.worker if case=='alive' else None
            with fs.patches(),self.assertRaises(RuntimeError):fs.call()
            self.assertIn((11,'runner.lock'),fs.files);self.assertIsNone(fs.moved)
            self.assertFalse(any(op[0]=='rename' for op in fs.ops))

    def test_state_change_before_retirement_is_refused(self):
        fs=MemoryFS();fs.change_state=True
        with fs.patches(),self.assertRaises(RuntimeError):fs.call()
        self.assertIn((11,'runner.lock'),fs.files);self.assertIsNone(fs.moved)

    def test_wrong_pid_status_marker_or_server_is_refused(self):
        for case in ('parent','status','marker','server','returncode','duplicate_pid','logstop'):
            fs=MemoryFS();kwargs={}
            if case=='parent':fs.files[(11,'runner.lock')][1]=b'{"pid": 999}'
            if case=='status':fs.files[(11,'batch_state.json')][1]=b'{"status":"STOPPED"}'
            if case=='marker':fs.files[(10,'.dryrun')][1]=b'wrong'
            if case=='logstop':fs.files[(10,'SYNTHETIC_parent_first.log')][1]=b'STOP: synthetic error'
            if case=='server':fs.files[(17,'llama_server_123.json')][1]=b'{"label":"EVIDENCE"}'
            if case=='returncode':kwargs['parent_returncode']=0
            if case=='duplicate_pid':kwargs['worker_pid']=fs.parent
            with fs.patches(),self.assertRaises(RuntimeError):fs.call(**kwargs)
            self.assertIn((11,'runner.lock'),fs.files);self.assertIsNone(fs.moved)

    def test_collision_and_unsupported_keep_lock(self):
        for collision in (True,False):
            fs=MemoryFS();fs.collision=collision;fs.fail_rename=not collision
            with fs.patches(),self.assertRaises(OSError):fs.call()
            self.assertIn((11,'runner.lock'),fs.files);self.assertIsNone(fs.moved)

    def test_post_rename_fsync_failure_preserves_archived_bytes(self):
        fs=MemoryFS();old=fs.files[(11,'runner.lock')][1];fs.fsync_failure=True
        with fs.patches(),self.assertRaises(OSError):fs.call()
        self.assertEqual(fs.moved[1],old);self.assertNotIn((11,'runner.lock'),fs.files)

    def test_actual_test_calls_helper_after_wait_before_resume(self):
        tree=ast.parse(pathlib.Path('r1/tests/test_exam_stagea_b1_crash_recovery.py').read_text())
        fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='test_stagea_to_b1_owned_parent_crash_and_recovery')
        calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call)]
        action=next(x for x in calls if isinstance(x.func,ast.Name) and x.func.id=='retire_test_owned_crash_lock')
        resume=next(x for x in calls if isinstance(x.func,ast.Attribute) and ast.unparse(x.func)=='subprocess.Popen' and x.lineno>action.lineno)
        wait=next(x for x in calls if isinstance(x.func,ast.Attribute) and ast.unparse(x.func)=='parent.wait')
        self.assertLess(wait.lineno,action.lineno);self.assertLess(action.lineno,resume.lineno)
        self.assertIn('retired_lock.read_bytes() == old_lock',ast.unparse(fn))


if __name__=='__main__': unittest.main()
