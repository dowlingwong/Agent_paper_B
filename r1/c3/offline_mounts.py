"""Private root and immutable file-mount primitives for M3 (no launcher yet).

Call only from a single-threaded trusted bootstrap after entering a private
mount namespace. These irreversible operations do not establish the full
process/IPC/cgroup boundary. The replay STOP remains unchanged.
"""
from __future__ import annotations
import ctypes
import hashlib
import os
from pathlib import Path, PurePosixPath
import platform
import stat

MS_RDONLY=1
MS_NOSUID=2
MS_NODEV=4
MS_NOEXEC=8
MS_REMOUNT=32
MS_BIND=4096


class MountStop(RuntimeError): pass


def _mount(source,target,kind,flags,data):
    if platform.system()!='Linux': raise MountStop('STOP: Linux mounts required')
    libc=ctypes.CDLL(None,use_errno=True)
    mount=libc.mount
    mount.argtypes=(ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_ulong,ctypes.c_char_p)
    mount.restype=ctypes.c_int
    def enc(value): return os.fsencode(value) if value is not None else None
    if mount(enc(source),enc(target),enc(kind),flags,enc(data))!=0:
        raise MountStop(f'STOP: mount failed (errno {ctypes.get_errno()}): {target}')


def _regular_bytes(path):
    path=Path(path)
    try:
        fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode): raise MountStop('STOP: closure input must be regular')
            with os.fdopen(fd,'rb',closefd=False) as f:return f.read()
        finally:os.close(fd)
    except OSError as exc:raise MountStop(f'STOP: closure input unreadable: {path}') from exc


def _target(root,target):
    if not isinstance(target,str) or not target.startswith('/') or target.startswith('//'):
        raise MountStop('STOP: closure target must be an absolute path')
    parts=PurePosixPath(target).parts
    if len(parts)<2 or any(p in ('.','..') for p in target.split('/')):
        raise MountStop('STOP: invalid closure target')
    if parts[1] in ('proc','sys','dev','work','out'):
        raise MountStop('STOP: closure target overlaps a reserved private path')
    return root.joinpath(*parts[1:])


def _private_parents(root,parent):
    """Create target parents one component at a time, rejecting symlinks."""
    current=root
    for part in parent.relative_to(root).parts:
        current=current/part
        try:current.mkdir(mode=0o700)
        except FileExistsError:pass
        st=current.lstat()
        if not stat.S_ISDIR(st.st_mode):raise MountStop('STOP: non-directory target parent')


def create_root(root,size_bytes):
    """Mount fresh private tmpfs on a caller-created empty owner-only directory."""
    if type(size_bytes) is not int or size_bytes<1024*1024:
        raise MountStop('STOP: explicit tmpfs size of at least 1 MiB required')
    root=Path(root)
    try:
        st=root.lstat()
        if not stat.S_ISDIR(st.st_mode) or root.is_symlink() or st.st_uid!=os.geteuid() or st.st_mode&0o077:
            raise MountStop('STOP: root must be owner-only real directory')
        if next(root.iterdir(),None) is not None:raise MountStop('STOP: root is not empty')
    except OSError as exc:raise MountStop('STOP: private root unavailable') from exc
    _mount('tmpfs',root,'tmpfs',MS_NOSUID|MS_NODEV,f'mode=0700,size={size_bytes}')
    for name in ('proc','work','out'): (root/name).mkdir(mode=0o700)


def mount_closure(root,items):
    """Bind explicit hash-pinned regular files, read-only, into private root.

    Only files are supported. No host directories or writable channels are
    exposed. Every declared target must be unique and outside reserved paths.
    The caller must later verify dependency closure and isolate descriptors.
    """
    root=Path(root)
    if not isinstance(items,list) or not items:raise MountStop('STOP: empty runtime closure')
    targets=set()
    for item in items:
        if not isinstance(item,dict) or set(item)!={'source','target','sha256'}:
            raise MountStop('STOP: malformed closure entry')
        target=_target(root,item['target']);target_key=str(target)
        if target_key in targets:raise MountStop('STOP: duplicate closure target')
        targets.add(target_key)
        raw=_regular_bytes(item['source']);expected=item['sha256']
        if not isinstance(expected,str) or len(expected)!=64 or hashlib.sha256(raw).hexdigest()!=expected:
            raise MountStop('STOP: closure source hash mismatch')
        _private_parents(root,target.parent)
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC,0o400);os.close(fd)
        _mount(item['source'],target,None,MS_BIND,None)
        _mount(None,target,None,MS_BIND|MS_REMOUNT|MS_RDONLY|MS_NOSUID|MS_NODEV,None)
        if not (os.statvfs(target).f_flag & os.ST_RDONLY):
            raise MountStop('STOP: bound runtime file is writable')
        if hashlib.sha256(_regular_bytes(target)).hexdigest()!=expected:
            raise MountStop('STOP: mounted runtime file changed')


def mount_pid_proc(root):
    """Mount a new read-only procfs after entering the child PID namespace."""
    _mount('proc',Path(root)/'proc','proc',MS_RDONLY|MS_NOSUID|MS_NODEV|MS_NOEXEC,None)


def populate_work(root,items):
    """Copy explicitly hash-pinned files into the private writable tmpfs workdir."""
    root=Path(root);work=root/'work';targets=set()
    if not isinstance(items,list):raise MountStop('STOP: malformed working-file list')
    for item in items:
        if not isinstance(item,dict) or set(item)!={'source','target','sha256'}:
            raise MountStop('STOP: malformed working-file entry')
        target=item['target']
        if not isinstance(target,str) or not target.startswith('/work/') or any(p in ('.','..') for p in target.split('/')):
            raise MountStop('STOP: invalid working-file target')
        path=work.joinpath(*PurePosixPath(target).parts[2:])
        if str(path) in targets:raise MountStop('STOP: duplicate working-file target')
        targets.add(str(path));raw=_regular_bytes(item['source'])
        if not isinstance(item['sha256'],str) or hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise MountStop('STOP: working-file source hash mismatch')
        _private_parents(work,path.parent)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC,0o600)
        try:
            offset=0
            while offset<len(raw):
                n=os.write(fd,raw[offset:])
                if n<=0:raise MountStop('STOP: short write copying working file')
                offset+=n
        finally:os.close(fd)
        if hashlib.sha256(_regular_bytes(path)).hexdigest()!=item['sha256']:
            raise MountStop('STOP: working-file copy mismatch')
