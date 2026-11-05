"""Linux seccomp user-notification component for the M3 offline guard.

This is *not* a complete sandbox or an execution authorization.  It must not be
used to start replay until namespace, cgroup, mount, descriptor, supervisor
lifetime and all-case preflight guarantees have separately been implemented and
independently reviewed. In particular the production replay STOP is unchanged.

The x86-64 allow-by-default syscall filter flags every listed network/IPC or
escape operation, including failed attempts. Only the bootstrap's preopened
private handoff socket may use sendmsg, solely to pass the listener before
untrusted code runs; the bootstrap must close that socket before exec and must
ensure no other socket or untrusted descriptor survives. Filter inheritance is
provided by Linux seccomp; the whole required process boundary is not provided
by this module.
"""
from __future__ import annotations

import ctypes
import array
import errno
import json
import os
import platform
import socket
import struct

AUDIT_ARCH_X86_64 = 0xC000003E
X32_SYSCALL_BIT = 0x40000000
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_USER_NOTIF = 0x7FC00000
SECCOMP_RET_ALLOW = 0x7FFF0000

# Linux x86-64 syscall numbers, not portable to other architectures.
SYSCALLS = {
    'socket':41, 'connect':42, 'accept':43, 'sendto':44, 'recvfrom':45,
    'sendmsg':46, 'recvmsg':47, 'shutdown':48, 'bind':49, 'listen':50,
    'getsockname':51, 'getpeername':52, 'socketpair':53, 'setsockopt':54,
    'getsockopt':55, 'semget':64, 'semop':65, 'semctl':66, 'shmdt':67,
    'msgget':68, 'msgsnd':69, 'msgrcv':70, 'msgctl':71, 'shmget':29,
    'shmat':30, 'shmctl':31, 'ptrace':101, 'mount':165, 'umount2':166,
    'add_key':248, 'request_key':249, 'keyctl':250, 'unshare':272,
    'accept4':288, 'recvmmsg':299, 'sendmmsg':307, 'setns':308,
    'process_vm_readv':310, 'process_vm_writev':311, 'seccomp':317,
    'bpf':321, 'userfaultfd':323, 'io_uring_setup':425, 'io_uring_enter':426,
    'io_uring_register':427, 'open_tree':428, 'move_mount':429, 'fsopen':430,
    'fsconfig':431, 'fsmount':432, 'fspick':433, 'pidfd_open':434,
    'clone3':435, 'pidfd_getfd':438, 'pidfd_send_signal':424,
    'mount_setattr':442, 'perf_event_open':298, 'name_to_handle_at':303,
    'open_by_handle_at':304,
}
# clone is permitted for ordinary children/threads; any namespace flag traps.
CLONE_NR = 56
CLONE_NAMESPACE_MASK = 0x7E020080  # NEWCGROUP, NEWUTS, NEWIPC, NEWUSER, NEWPID, NEWNET, NEWNS, NEWTIME

# classic-BPF opcodes
_LD_W_ABS=0x20; _JMP_JEQ_K=0x15; _JMP_JGE_K=0x35; _JMP_JSET_K=0x45; _RET_K=0x06


def compile_filter(handoff_fd):
    """Return (code, jt, jf, k) classic-BPF instructions, for Linux x86-64."""
    if type(handoff_fd) is not int or not 3 <= handoff_fd < 2**31:
        raise ValueError('a dedicated bootstrap handoff FD >= 3 is required')
    result=[(_LD_W_ABS,0,0,4), (_JMP_JEQ_K,1,0,AUDIT_ARCH_X86_64),
            (_RET_K,0,0,SECCOMP_RET_KILL_PROCESS), (_LD_W_ABS,0,0,0),
            (_JMP_JGE_K,0,1,X32_SYSCALL_BIT), (_RET_K,0,0,SECCOMP_RET_KILL_PROCESS),
            # sendmsg may only transfer the listener over the bootstrap FD.
            (_JMP_JEQ_K,0,4,SYSCALLS['sendmsg']), (_LD_W_ABS,0,0,16),
            (_JMP_JEQ_K,0,1,handoff_fd), (_RET_K,0,0,SECCOMP_RET_ALLOW),
            (_RET_K,0,0,SECCOMP_RET_USER_NOTIF), (_LD_W_ABS,0,0,0),
            # clone flags occupy arg0, little-endian low and high words.
            (_JMP_JEQ_K,0,6,CLONE_NR), (_LD_W_ABS,0,0,20),
            (_JMP_JEQ_K,1,0,0), (_RET_K,0,0,SECCOMP_RET_USER_NOTIF),
            (_LD_W_ABS,0,0,16), (_JMP_JSET_K,0,1,CLONE_NAMESPACE_MASK),
            (_RET_K,0,0,SECCOMP_RET_USER_NOTIF), (_LD_W_ABS,0,0,0)]
    for name,nr in sorted(SYSCALLS.items(),key=lambda pair:pair[1]):
        if name=='sendmsg': continue
        result.extend([(_JMP_JEQ_K,0,1,nr),(_RET_K,0,0,SECCOMP_RET_USER_NOTIF)])
    result.append((_RET_K,0,0,SECCOMP_RET_ALLOW))
    return result


class SockFilter(ctypes.Structure):
    _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint32)]


class SockFprog(ctypes.Structure):
    _fields_=[('length',ctypes.c_ushort),('filter',ctypes.POINTER(SockFilter))]


def install_listener(handoff_fd):
    """Install a non-removable Linux filter; call ONLY from the trusted bootstrap.

    This changes the calling process irreversibly. No production caller is
    currently wired to it. Returns a listener FD or raises OSError.
    """
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):
        raise RuntimeError('STOP: seccomp component supports Linux x86-64 only')
    instructions=compile_filter(handoff_fd)
    code=(SockFilter*len(instructions))(*(SockFilter(*ins) for ins in instructions))
    prog=SockFprog(len(instructions),code)
    libc=ctypes.CDLL(None,use_errno=True)
    # PR_SET_NO_NEW_PRIVS=38; SECCOMP_SET_MODE_FILTER=1;
    # SECCOMP_FILTER_FLAG_NEW_LISTENER=8; x86-64 __NR_seccomp=317.
    if libc.prctl(38,1,0,0,0)!=0:
        e=ctypes.get_errno();raise OSError(e,os.strerror(e))
    fd=libc.syscall(317,1,8,ctypes.byref(prog))
    if fd<0:
        e=ctypes.get_errno();raise OSError(e,os.strerror(e))
    return int(fd)


def send_listener(channel, listener_fd):
    """Transfer exactly one listener over a trusted, preopened private socket.

    The caller must wait for the supervisor's readiness acknowledgement and
    close the channel and its copy of the listener before any untrusted exec.
    The channel's numeric FD must be the bootstrap exemption in compile_filter.
    """
    if channel.fileno()<3 or type(listener_fd) is not int or listener_fd<0:
        raise ValueError('invalid bootstrap channel or listener')
    fds=array.array('i',[listener_fd])
    if channel.sendmsg([b'L'],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,fds)])!=1:
        raise RuntimeError('STOP: incomplete listener transfer')


def receive_listener(channel):
    """Receive exactly one descriptor; reject truncation and extra descriptors.

    Caller owns the resulting FD and must validate that the monitor and cgroup
    are ready before sending the bootstrap an acknowledgement. This function
    does not itself launch, acknowledge, or validate namespace containment.
    """
    fds=array.array('i');received=[];unexpected=False
    try:
        data,ancillary,flags,_=channel.recvmsg(1,socket.CMSG_SPACE(fds.itemsize*4))
        for level,kind,payload in ancillary:
            if level==socket.SOL_SOCKET and kind==socket.SCM_RIGHTS:
                fds=array.array('i');usable=len(payload)-(len(payload)%fds.itemsize)
                unexpected |= usable!=len(payload)
                fds.frombytes(payload[:usable]);received.extend(fds)
            else:
                unexpected=True
        if unexpected or data!=b'L' or flags & (socket.MSG_TRUNC|socket.MSG_CTRUNC) or len(received)!=1:
            raise RuntimeError('STOP: invalid listener handoff')
        os.set_inheritable(received[0],False)
        return received.pop()
    finally:
        for fd in received: os.close(fd)


def _ioctl_req(direction,number,size):
    return (direction<<30)|(size<<16)|(ord('!')<<8)|number


# `struct seccomp_notif`: u64 id, u32 pid, u32 flags, seccomp_data (64 bytes).
NOTIF_SIZE=80
SECCOMP_IOCTL_NOTIF_RECV=_ioctl_req(3,0,NOTIF_SIZE)
SECCOMP_IOCTL_NOTIF_ID_VALID=_ioctl_req(1,2,8)


def verify_listener(listener_fd, *, ioctl=None):
    """Confirm the FD is a seccomp listener using an impossible ID (zero)."""
    if ioctl is None:
        import fcntl
        ioctl=fcntl.ioctl
    try:
        ioctl(listener_fd,SECCOMP_IOCTL_NOTIF_ID_VALID,struct.pack('=Q',0))
    except OSError as exc:
        if exc.errno==errno.ENOENT:return
        raise RuntimeError('STOP: listener verification failed') from exc
    raise RuntimeError('STOP: invalid zero seccomp notification ID unexpectedly accepted')


def monitor_one(listener_fd, cgroup_kill_fd, audit_fd, *, ioctl=None, write=None, fsync=None):
    """One violation: persist its identity, then kill the delegated cgroup.

    Intended to run in the trusted supervisor. It refuses to classify or ignore
    any notification; any read/audit error also triggers cgroup kill. On audit
    failure the caller must retain STOP and cannot claim a durable event. This
    helper alone does not make supervisor death crash-safe.
    """
    if ioctl is None:
        import fcntl
        ioctl=fcntl.ioctl
    write=write or os.write;fsync=fsync or os.fsync
    raw=bytearray(NOTIF_SIZE); observed=None
    try:
        ioctl(listener_fd,SECCOMP_IOCTL_NOTIF_RECV,raw,True)
        ident,pid,flags,nr,arch=struct.unpack_from('=QIIiI',raw)
        observed={'event':'prohibited_syscall','id':ident,'pid':pid,'flags':flags,
                  'syscall':nr,'arch':arch,'decision':'STOP'}
        encoded=(json.dumps(observed,sort_keys=True)+'\n').encode()
        done=0
        while done<len(encoded):
            written=write(audit_fd,encoded[done:])
            if type(written) is not int or written<=0: raise OSError(errno.EIO,'short audit write')
            done+=written
        fsync(audit_fd)
    finally:
        if write(cgroup_kill_fd,b'1\n')!=2:
            raise OSError(errno.EIO,'cannot kill delegated cgroup')
    return observed
