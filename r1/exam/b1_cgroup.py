"""Cooperative cgroup-v2 containment for an owned B1 run.

This is Linux-only and requires site qualification of a delegated writable
cgroup v2 subtree, cgroup.freeze, cgroup.kill and pidfd semantics. It does not
provide adversarial same-UID isolation or prove GPU/DMA quiescence.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
GUARDIAN = REPO / 'r1/exam/b1_cgroup_guardian.py'
BOOTSTRAP = REPO / 'r1/exam/b1_cgroup_bootstrap.py'
CGROUP2_SUPER_MAGIC = 0x63677270


class ContainmentStop(RuntimeError):
    pass


def _open_dir_at(fd, name):
    if not name or name in ('.', '..') or '/' in name:
        raise ContainmentStop('STOP: invalid cgroup component')
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)


def _control(fd, name, flags):
    return os.open(name, flags | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)


def _check_cgroup2(fd):
    # Linux x86-64 fstatfs starts with a native-long f_type. The target site's
    # ABI and delegation must be independently qualified before any B1 use.
    libc = ctypes.CDLL(None, use_errno=True)
    buf = ctypes.create_string_buffer(512)
    if libc.fstatfs(fd, ctypes.byref(buf)) != 0:
        raise OSError(ctypes.get_errno(), 'fstatfs failed')
    if ctypes.c_long.from_buffer(buf).value != CGROUP2_SUPER_MAGIC:
        raise ContainmentStop('STOP: cgroup v2 filesystem required')


def _parent_dir():
    entries = Path('/proc/self/cgroup').read_text().splitlines()
    roots = [line[3:] for line in entries if line.startswith('0::')]
    if len(roots) != 1 or not roots[0].startswith('/'):
        raise ContainmentStop('STOP: unified cgroup membership unavailable')
    components = [part for part in roots[0].split('/') if part]
    if any(part in ('.', '..') for part in components):
        raise ContainmentStop('STOP: cgroup namespace path is not canonical')
    fd = os.open('/sys/fs/cgroup', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        _check_cgroup2(fd)
        for component in components:
            child = _open_dir_at(fd, component)
            os.close(fd)
            fd = child
        if os.fstat(fd).st_uid != os.getuid():
            raise ContainmentStop('STOP: current cgroup is not owned by this UID')
        return fd, roots[0]
    except BaseException:
        os.close(fd)
        raise


def _events(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    result = {}
    for row in os.read(fd, 4096).decode('ascii').splitlines():
        key, value = row.split()
        if key in result:
            raise ContainmentStop('STOP: duplicate cgroup.events field')
        result[key] = int(value)
    return result


def _read_one(fd, timeout):
    readable, _, _ = select.select([fd], [], [], timeout)
    if not readable:
        raise ContainmentStop('STOP: contained bootstrap timed out')
    return os.read(fd, 1)


def retire_runner_lock(path, identity, expected_sha):
    """Retire only the exact newly created B1 lock without replacement.

    Linux renameat2/RENAME_NOREPLACE and same-UID cooperative behavior must be
    checked at the site. Any mismatch fails closed; no cleanup is attempted.
    """
    path = Path(path)
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino, info.st_uid) != identity
            or info.st_uid != os.getuid()):
        raise ContainmentStop('STOP: B1 runner lock identity changed')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha or json.loads(data).get('pid') != os.getpid():
        raise ContainmentStop('STOP: B1 runner lock contents changed')
    retired = path.parent / '_to_delete'
    retired.mkdir(mode=0o700, exist_ok=False)
    destination = retired / 'runner.lock'
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    if rename is None:
        raise ContainmentStop('STOP: renameat2 is unavailable for lock retirement')
    result = rename(ctypes.c_int(-100), ctypes.c_char_p(os.fsencode(path)),
                    ctypes.c_int(-100), ctypes.c_char_p(os.fsencode(destination)), ctypes.c_uint(1))
    if result != 0:
        raise ContainmentStop(f'STOP: runner lock retirement failed (errno={ctypes.get_errno()})')


class B1Containment:
    """One fresh per-batch parent and one fresh leaf per subprocess.

    All directories and process evidence are intentionally retained. Only the
    newly created subtree may be frozen or killed. A same-UID writer is assumed
    cooperative; kernel cgroup-freeze does not prevent explicit migration.
    """
    def initialize(self, lease_fd, receipt):
        if type(lease_fd) is not int or lease_fd < 3:
            raise ContainmentStop('STOP: invalid B1 lease FD for guardian')
        self.guardian = None
        self.control = None
        self._control_lock = threading.RLock()
        self._write_lock = threading.RLock()
        self._spawn_lock = threading.RLock()
        self._grant_lock = threading.RLock()
        self._stop_requested = threading.Event()
        self._frozen = False
        self._leaves = {}
        parent_fd, membership = _parent_dir()
        try:
            name = 'paper-b-b1-' + time.strftime('%Y%m%d') + '-' + uuid.uuid4().hex
            os.mkdir(name, 0o700, dir_fd=parent_fd)
            self.root_fd = _open_dir_at(parent_fd, name)
            self.membership = membership.rstrip('/') + '/' + name
        finally:
            os.close(parent_fd)
        if os.fstat(self.root_fd).st_uid != os.getuid():
            raise ContainmentStop('STOP: newly created cgroup ownership mismatch')
        identity = os.fstat(self.root_fd)
        receipt({'cgroup': self.membership, 'dev': identity.st_dev, 'ino': identity.st_ino,
                 'guardian_pid': None, 'state': 'CREATED'})
        self.freeze_fd = _control(self.root_fd, 'cgroup.freeze', os.O_WRONLY)
        self.events_fd = _control(self.root_fd, 'cgroup.events', os.O_RDONLY)
        if min(self.root_fd, self.freeze_fd, self.events_fd) < 3:
            raise ContainmentStop('STOP: cgroup descriptor collides with standard streams')
        if _events(self.events_fd).get('populated') != 0:
            raise ContainmentStop('STOP: new cgroup unexpectedly populated')
        self.parent_pidfd = os.pidfd_open(os.getpid(), 0)
        if self.parent_pidfd < 3:
            raise ContainmentStop('STOP: parent pidfd collides with standard streams')
        parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        guardian_freeze = _control(self.root_fd, 'cgroup.freeze', os.O_WRONLY)
        guardian_events = _control(self.root_fd, 'cgroup.events', os.O_RDONLY)
        try:
            self.guardian = subprocess.Popen(
                [sys.executable, '-I', '-S', '-B', str(GUARDIAN), str(child.fileno()),
                 str(self.parent_pidfd), str(guardian_freeze), str(guardian_events)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                close_fds=True, pass_fds=(child.fileno(), self.parent_pidfd, guardian_freeze,
                                          guardian_events, lease_fd))
        finally:
            child.close()
            os.close(guardian_freeze)
            os.close(guardian_events)
        self.control = parent
        parent.settimeout(10)
        from r1.exam.cache_proc import process_start_ticks
        receipt({'cgroup': self.membership, 'dev': identity.st_dev, 'ino': identity.st_ino,
                 'guardian_pid': self.guardian.pid, 'guardian_start_ticks':process_start_ticks(self.guardian.pid),
                 'state': 'GUARDIAN_STARTED'})
        if parent.recv(64) != b'READY':
            raise ContainmentStop('STOP: containment guardian not ready')
        ours = os.fstat(lease_fd)
        theirs = os.stat(Path('/proc') / str(self.guardian.pid) / 'fd' / str(lease_fd))
        if (ours.st_dev, ours.st_ino) != (theirs.st_dev, theirs.st_ino):
            raise ContainmentStop('STOP: guardian GPU lease descriptor differs')
        from r1.exam.cooperative_lease import kcmp_file_result
        rc, err = kcmp_file_result(os.getpid(), self.guardian.pid, lease_fd, lease_fd)
        if rc != 0:
            raise ContainmentStop(f'STOP: guardian GPU lease OFD unproved (rc={rc}, errno={err})')

    def _leaf(self, kind):
        if kind not in ('worker', 'server'):
            raise ContainmentStop('STOP: invalid containment leaf kind')
        name = kind + '-' + uuid.uuid4().hex
        os.mkdir(name, 0o700, dir_fd=self.root_fd)
        fd = _open_dir_at(self.root_fd, name)
        if os.fstat(fd).st_uid != os.getuid():
            raise ContainmentStop('STOP: containment leaf ownership mismatch')
        procs = _control(fd, 'cgroup.procs', os.O_WRONLY)
        events = _control(fd, 'cgroup.events', os.O_RDONLY)
        return name, fd, procs, events

    def freeze(self):
        # Set this before any lock: a monitor must not wait for a slow spawn
        # before requesting a kernel freeze. A grant already in flight may
        # execute until the kernel reports frozen; that delay is not hidden.
        # This short section is shared only with the one-byte release write
        # and normal server SIGTERM. Slow enrollment and exec checks are not
        # inside it; the freezer can proceed while a bootstrap is arriving.
        with self._grant_lock:
            self._stop_requested.set()
        with self._control_lock:
            if self._frozen:
                return
            def direct_freeze():
                os.lseek(self.freeze_fd, 0, os.SEEK_SET)
                if os.write(self.freeze_fd, b'1\n') != 2:
                    raise ContainmentStop('STOP: freeze write failed')
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if _events(self.events_fd).get('frozen') == 1:
                        return
                    time.sleep(.01)
                raise ContainmentStop('STOP: freeze not established')
            try:
                self.control.sendall(b'FREEZE')
                response = self.control.recv(64)
            except Exception as exc:
                # Parent independently attempts freeze if guardian is lost.
                try: direct_freeze()
                except Exception as failure:
                    raise ContainmentStop('STOP: freeze not established') from failure
            else:
                if response != b'FROZEN' or _events(self.events_fd).get('frozen') != 1:
                    direct_freeze()
            with self._write_lock:
                self._frozen = True

    def require_guardian(self):
        if self.guardian.poll() is not None:
            self.freeze()
            raise ContainmentStop('STOP: B1 containment guardian exited')

    def observe_check(self, callback):
        # The check and publication of STOP intent share the same very short
        # serialization point as a grant, so a detected failure cannot be
        # followed by a newly issued grant.
        with self._grant_lock:
            try:
                return callback()
            except Exception:
                self._stop_requested.set()
                raise

    def write_active(self, callback):
        # Serialize server-record mutations with STOP freeze. STOP reporting
        # itself uses the runner's separate state/STATUS channel.
        # Guardian verification may itself freeze; never do that while holding
        # the write lock, or it can invert the freeze control/write lock order.
        self.require_guardian()
        with self._write_lock:
            if self._stop_requested.is_set() or self._frozen:
                raise ContainmentStop('STOP: server record write after freeze')
            return callback()

    def spawn(self, kind, argv, *, env, stdout, lease_fd, cwd=None):
        """Launch a migrated bootstrap, then exec the intended command in-place."""
        with self._spawn_lock:
            if self._stop_requested.is_set() or self._frozen or self.guardian.poll() is not None:
                raise ContainmentStop('STOP: containment frozen or guardian dead')
            name, leaf_fd, procs_fd, events_fd = self._leaf(kind)
            ready_r, ready_w = os.pipe()
            grant_r, grant_w = os.pipe()
            exec_r, exec_w = os.pipe()
            process = None
            try:
                if min(leaf_fd,procs_fd,events_fd,ready_r,ready_w,grant_r,grant_w,exec_r,exec_w,stdout.fileno(),lease_fd) < 3:
                    raise ContainmentStop('STOP: B1 launcher descriptor collides with standard streams')
                args = [sys.executable, '-I', '-S', '-B', str(BOOTSTRAP), str(procs_fd),
                        str(ready_w), str(grant_r), str(stdout.fileno()), str(exec_w), *argv]
                process = subprocess.Popen(args, env=env, cwd=cwd, stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                           start_new_session=True, close_fds=True,
                                           pass_fds=(procs_fd, ready_w, grant_r, stdout.fileno(),
                                                     exec_w, lease_fd))
                os.close(ready_w); ready_w = None
                os.close(grant_r); grant_r = None
                os.close(exec_w); exec_w = None
                if _read_one(ready_r, 10) != b'M':
                    raise ContainmentStop('STOP: bootstrap did not enroll')
                actual = Path('/proc') / str(process.pid) / 'cgroup'
                expected = self.membership + '/' + name
                if '0::' + expected not in actual.read_text().splitlines():
                    raise ContainmentStop('STOP: child cgroup membership mismatch')
                ours = os.fstat(lease_fd)
                theirs = os.stat(Path('/proc') / str(process.pid) / 'fd' / str(lease_fd))
                if (ours.st_dev, ours.st_ino) != (theirs.st_dev, theirs.st_ino):
                    raise ContainmentStop('STOP: contained child GPU lease differs')
                from r1.exam.cooperative_lease import kcmp_file_result
                rc, err = kcmp_file_result(os.getpid(), process.pid, lease_fd, lease_fd)
                if rc != 0:
                    raise ContainmentStop(f'STOP: contained child lease OFD unproved (rc={rc}, errno={err})')
                # The bootstrap is still blocked on its grant. Pin the actual
                # child before any workload exec; retain this pidfd for normal
                # server termination instead of signalling a recycled PID.
                process_pidfd = os.pidfd_open(process.pid, 0)
                self.require_guardian()
                with self._grant_lock:
                    if self._stop_requested.is_set():
                        raise ContainmentStop('STOP: grant cancelled by monitor')
                    if os.write(grant_w, b'G') != 1:
                        raise ContainmentStop('STOP: bootstrap release incomplete')
                if self._stop_requested.is_set():
                    raise ContainmentStop('STOP: grant raced with monitor')
                os.close(grant_w); grant_w = None
                # CLOEXEC EOF may also be process exit: verify intended argv
                # before handing its PID to the existing server/worker logic.
                if _read_one(exec_r, 10) != b'':
                    raise ContainmentStop('STOP: bootstrap exec channel invalid')
                if process.poll() is not None:
                    raise ContainmentStop('STOP: contained process exited before exec check')
                cmdline = (Path('/proc') / str(process.pid) / 'cmdline').read_bytes().split(b'\0')
                if cmdline[:len(argv)] != [os.fsencode(a) for a in argv]:
                    raise ContainmentStop('STOP: contained executable argv mismatch')
                self._leaves[process.pid] = (kind, leaf_fd, events_fd, process_pidfd)
                return process
            except BaseException:
                # Any release write may have reached the child. Freeze before
                # exposing STOP; never signal an unverified numeric PID.
                self.freeze()
                raise
            finally:
                for fd in (procs_fd, ready_r, ready_w, grant_r, grant_w, exec_r, exec_w):
                    if fd is not None:
                        try: os.close(fd)
                        except OSError: pass

    def stop_server(self, process):
        with self._spawn_lock:
            leaf = self._leaves.get(process.pid)
            if not leaf or leaf[0] != 'server' or self._frozen:
                raise ContainmentStop('STOP: server leaf is not owned or is frozen')
            _, _, events, pidfd = leaf
            with self._grant_lock:
                if self._stop_requested.is_set():
                    raise ContainmentStop('STOP: normal server shutdown cancelled')
                if process.poll() is None:
                    signal.pidfd_send_signal(pidfd, signal.SIGTERM)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if self._stop_requested.is_set():
                    raise ContainmentStop('STOP: server shutdown interrupted by STOP')
                if _events(events).get('populated') == 0:
                    process.wait(timeout=2)
                    for fd in leaf[1:]:
                        os.close(fd)
                    del self._leaves[process.pid]
                    return
                time.sleep(.01)
            raise ContainmentStop('STOP: server subgroup did not become empty')

    def require_worker_empty(self, process):
        leaf = self._leaves.get(process.pid)
        if not leaf or leaf[0] != 'worker' or _events(leaf[2]).get('populated') != 0:
            raise ContainmentStop('STOP: worker subgroup retains descendants')
        for fd in leaf[1:]:
            os.close(fd)
        del self._leaves[process.pid]

    def verify_live_lease(self, process, lease_fd):
        from r1.exam.cooperative_lease import kcmp_file_result
        ours=os.fstat(lease_fd)
        observed=os.stat(Path('/proc')/str(process.pid)/'fd'/str(lease_fd))
        if (ours.st_dev,ours.st_ino)!=(observed.st_dev,observed.st_ino):
            raise ContainmentStop('STOP: live server lease descriptor differs')
        rc,err=kcmp_file_result(os.getpid(),process.pid,lease_fd,lease_fd)
        if rc!=0:
            raise ContainmentStop(f'STOP: live server lease OFD unproved (rc={rc}, errno={err})')

    def finish(self):
        with self._spawn_lock:
            if self._frozen or _events(self.events_fd).get('populated') != 0:
                raise ContainmentStop('STOP: cannot finish populated/frozen containment')
            self.control.sendall(b'FINISH')
            if self.control.recv(64) != b'FINISHED':
                raise ContainmentStop('STOP: guardian refused normal finish')
            self.guardian.wait(timeout=10)
            self.control.close()

    def require_finish_ready(self):
        with self._spawn_lock:
            self.require_guardian()
            if self._stop_requested.is_set() or self._frozen or _events(self.events_fd).get('populated') != 0:
                raise ContainmentStop('STOP: B1 containment is not ready to finish')
