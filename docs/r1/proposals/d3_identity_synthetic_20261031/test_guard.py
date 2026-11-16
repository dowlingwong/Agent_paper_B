import hashlib, os, tempfile, unittest
from pathlib import Path
from unittest import mock
import guard

class GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Path(tempfile.mkdtemp(prefix='d3_input_synthetic_', dir='/private/tmp'))
        cls.uid=os.getuid()
    def setup_case(self):
        d=Path(tempfile.mkdtemp(prefix='case_',dir=self.base)); d.chmod(0o700)
        return d
    def setup_input(self):
        d=self.setup_case(); (d/'dir').mkdir(mode=0o700); (d/'dir'/'item').write_bytes(b'fixed data')
        return d,hashlib.sha256(b'fixed data').hexdigest()
    def test_holds_checked_bytes(self):
        d,h=self.setup_input(); root=guard.open_root(str(d),uid=self.uid)
        try:
            fd,identity=guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
            try:
                guard.validate_held_fd(fd,identity,h); self.assertEqual(os.read(fd,100),b'fixed data')
            finally: os.close(fd)
        finally: os.close(root)
    def test_refuses_path_traversal(self):
        d,h=self.setup_input(); root=guard.open_root(str(d),uid=self.uid)
        try:
            for path in ('../etc/passwd','/etc/passwd','dir/../item','dir//item'):
                with self.subTest(path=path), self.assertRaises(guard.GuardStop): guard.open_input(root,path,uid=self.uid,expected_sha256=h)
        finally:os.close(root)
    def test_refuses_file_and_directory_symlinks(self):
        d,h=self.setup_input(); (d/'link').symlink_to('dir',target_is_directory=True); (d/'dir'/'s').symlink_to('item'); root=guard.open_root(str(d),uid=self.uid)
        try:
            for path in ('link/item','dir/s'):
                with self.subTest(path=path), self.assertRaises(guard.GuardStop):guard.open_input(root,path,uid=self.uid,expected_sha256=h)
        finally:os.close(root)
    def test_refuses_hardlink(self):
        d,h=self.setup_input();os.link(d/'dir'/'item',d/'dir'/'alias');root=guard.open_root(str(d),uid=self.uid)
        try:
            with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
        finally:os.close(root)
    def test_refuses_writable_directory_and_wrong_owner(self):
        d,h=self.setup_input();root=guard.open_root(str(d),uid=self.uid);(d/'dir').chmod(0o777)
        try:
            with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
        finally:os.close(root)
        with self.assertRaises(guard.GuardStop):guard.open_root(str(d),uid=self.uid+1)
    def test_detects_wrong_hash_and_post_open_edit(self):
        d,h=self.setup_input();root=guard.open_root(str(d),uid=self.uid)
        try:
            with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256='0'*64)
            fd,identity=guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
            try:
                (d/'dir'/'item').write_bytes(b'other data')
                with self.assertRaises(guard.GuardStop):guard.validate_held_fd(fd,identity,h)
            finally:os.close(fd)
        finally:os.close(root)
    def test_detects_path_replacement_limitation_and_held_fd_binding(self):
        d,h=self.setup_input();root=guard.open_root(str(d),uid=self.uid);fd,identity=guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
        try:
            os.rename(d/'dir'/'item',d/'dir'/'old_item');(d/'dir'/'item').write_bytes(b'not same')
            # Renaming may update ctime; either fail closed or read the original
            # held object, never accept changed bytes from the new path.
            try:
                guard.validate_held_fd(fd,identity,h)
                self.assertEqual(os.read(fd,100),b'fixed data')
            except guard.GuardStop: pass
            with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
        finally:os.close(fd);os.close(root)
    def test_kcmp_unavailable_is_not_checkable(self):
        with mock.patch.object(guard.os,'uname',return_value=type('U',(),{'sysname':'Darwin','machine':'x86_64'})()):
            self.assertEqual(guard.kcmp_file_verdict(1,2,3,4),'NOT_CHECKABLE')
    def test_refuses_fifo_without_blocking(self):
        d=self.setup_case(); os.mkfifo(d/'pipe'); root=guard.open_root(str(d),uid=self.uid)
        try:
            with self.assertRaises(guard.GuardStop):guard.open_input(root,'pipe',uid=self.uid,expected_sha256='0'*64)
        finally:os.close(root)
    def test_kcmp_syscall_results_are_not_inferred_from_inode(self):
        class Call:
            restype=None
            def __init__(self,value):self.value=value
            def __call__(self,*args):return self.value
        class Lib:
            def __init__(self,value):self.syscall=Call(value)
        uname=type('U',(),{'sysname':'Linux','machine':'x86_64'})()
        for value,expected in [(0,'SAME'),(1,'DIFFERENT'),(-1,'NOT_CHECKABLE')]:
            with self.subTest(value=value), mock.patch.object(guard.os,'uname',return_value=uname), mock.patch.object(guard.ctypes,'CDLL',return_value=Lib(value)):
                self.assertEqual(guard.kcmp_file_verdict(1,2,3,4),expected)
    def test_root_symlink_and_malformed_digest_fail_closed(self):
        d,h=self.setup_input(); parent=self.setup_case(); (parent/'rootlink').symlink_to(d, target_is_directory=True)
        with self.assertRaises(guard.GuardStop):guard.open_root(str(parent/'rootlink'),uid=self.uid)
        root=guard.open_root(str(d),uid=self.uid)
        try:
            for value in (None, '', 'G'*64, 9):
                with self.subTest(value=value), self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=value)
        finally:os.close(root)
    def test_input_read_failure_maps_to_stop_and_closes(self):
        d,h=self.setup_input();root=guard.open_root(str(d),uid=self.uid)
        try:
            with mock.patch.object(guard.os,'read',side_effect=OSError('synthetic read failure')):
                with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
        finally:os.close(root)
    def test_kcmp_library_load_failure_is_not_checkable(self):
        uname=type('U',(),{'sysname':'Linux','machine':'x86_64'})()
        with mock.patch.object(guard.os,'uname',return_value=uname), mock.patch.object(guard.ctypes,'CDLL',side_effect=OSError('synthetic missing libc')):
            self.assertEqual(guard.kcmp_file_verdict(1,2,3,4),'NOT_CHECKABLE')
    def test_kcmp_unknown_architecture_and_external_nr_fail_closed(self):
        uname=type('U',(),{'sysname':'Linux','machine':'aarch64'})()
        with mock.patch.object(guard.os,'uname',return_value=uname), mock.patch.object(guard.ctypes,'CDLL') as lib:
            self.assertEqual(guard.kcmp_file_verdict(1,2,3,4),'NOT_CHECKABLE')
            lib.assert_not_called()
        with self.assertRaises(TypeError): guard.kcmp_file_verdict(1,2,3,4,syscall_nr=999)
    def test_dup_and_root_fstat_failure_map_to_stop(self):
        d,h=self.setup_input();root=guard.open_root(str(d),uid=self.uid)
        try:
            with mock.patch.object(guard.os,'dup',side_effect=OSError('synthetic dup failure')):
                with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
        finally:os.close(root)
        with mock.patch.object(guard.os,'fstat',side_effect=OSError('synthetic fstat failure')):
            with self.assertRaises(guard.GuardStop):guard.open_root(str(d),uid=self.uid)
    def test_kcmp_uname_failure_not_checkable(self):
        with mock.patch.object(guard.os,'uname',side_effect=OSError('synthetic uname failure')):
            self.assertEqual(guard.kcmp_file_verdict(1,2,3,4),'NOT_CHECKABLE')
    def test_close_failure_does_not_retry_ambiguous_fd_and_closes_new_fd(self):
        d,h=self.setup_input(); root=guard.open_root(str(d),uid=self.uid)
        actual_dup=guard.os.dup; actual_open=guard.os.open; actual_close=guard.os.close
        state={'old':None,'new':None,'calls':[]}
        def duper(fd):
            x=actual_dup(fd);state['old']=x;return x
        def opener(path,flags,*args,**kwargs):
            x=actual_open(path,flags,*args,**kwargs)
            if kwargs.get('dir_fd') is not None and path=='dir':state['new']=x
            return x
        def closer(fd):
            state['calls'].append(fd)
            if fd==state['old']:raise OSError('synthetic uncertain close')
            return actual_close(fd)
        try:
            with mock.patch.object(guard.os,'dup',side_effect=duper), mock.patch.object(guard.os,'open',side_effect=opener), mock.patch.object(guard.os,'close',side_effect=closer):
                with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
            self.assertIsNotNone(state['new'])
            self.assertEqual(state['calls'].count(state['old']),1)
            self.assertEqual(state['calls'].count(state['new']),1)
            with self.assertRaises(OSError):os.fstat(state['new'])
        finally:
            # Our fake close failed before invoking the real syscall; only this
            # synthetic test therefore knows the descriptor is still open.
            if state['old'] is not None:actual_close(state['old'])
            actual_close(root)
    def test_directory_close_failure_before_return_closes_file_once(self):
        d,h=self.setup_input(); root=guard.open_root(str(d),uid=self.uid)
        actual_open=guard.os.open; actual_close=guard.os.close
        state={'dir':None,'file':None,'calls':[]}
        def opener(path,flags,*args,**kwargs):
            x=actual_open(path,flags,*args,**kwargs)
            if kwargs.get('dir_fd') is not None:
                if path=='dir':state['dir']=x
                if path=='item':state['file']=x
            return x
        def closer(fd):
            state['calls'].append((fd,state['file'] is not None))
            if fd==state['dir']:raise OSError('synthetic uncertain directory close')
            return actual_close(fd)
        try:
            with mock.patch.object(guard.os,'open',side_effect=opener), mock.patch.object(guard.os,'close',side_effect=closer):
                with self.assertRaises(guard.GuardStop):guard.open_input(root,'dir/item',uid=self.uid,expected_sha256=h)
            self.assertIsNotNone(state['file'])
            self.assertEqual(state['calls'].count((state['dir'],True)),1)
            # FD numbers can be reused after the previous directory closes.
            self.assertEqual(state['calls'].count((state['file'],True)),1)
            with self.assertRaises(OSError):os.fstat(state['file'])
        finally:
            # Only the synthetic fake proves the real dir close was not called.
            if state['dir'] is not None:actual_close(state['dir'])
            actual_close(root)
    def test_kcmp_rejects_invalid_values_without_ffi(self):
        uname=type('U',(),{'sysname':'Linux','machine':'x86_64'})()
        with mock.patch.object(guard.os,'uname',return_value=uname), mock.patch.object(guard.ctypes,'CDLL') as lib:
            for values in [(0,2,3,4),(-1,2,3,4),(2**32+1,2,3,4),(1,True,3,4),(1,2,-1,4),(1,2,3,2**31),(1,2,3,'4')]:
                with self.subTest(values=values):self.assertEqual(guard.kcmp_file_verdict(*values),'NOT_CHECKABLE')
            lib.assert_not_called()
    def test_prod_entry_always_stops(self):
        with self.assertRaises(guard.GuardStop):guard.production_entry()

if __name__=='__main__': unittest.main(verbosity=2)
