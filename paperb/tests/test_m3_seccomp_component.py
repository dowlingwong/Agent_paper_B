"""Pure filter and supervisor tests; no seccomp installation or workload."""
import errno
import os
import struct
import pytest
from r1.c3 import offline_seccomp as sc


def interpret(program,nr,arch=sc.AUDIT_ARCH_X86_64,arg0=0):
    words={0:nr & 0xffffffff,4:arch,16:arg0 & 0xffffffff,20:(arg0>>32)&0xffffffff}
    accumulator=0;pc=0
    while pc<len(program):
        code,jt,jf,k=program[pc]
        if code==sc._LD_W_ABS: accumulator=words[k]
        elif code==sc._RET_K: return k
        elif code==sc._JMP_JEQ_K: pc += jt if accumulator==k else jf
        elif code==sc._JMP_JGE_K: pc += jt if accumulator>=k else jf
        elif code==sc._JMP_JSET_K: pc += jt if accumulator & k else jf
        else: raise AssertionError(f'unexpected opcode {code}')
        pc+=1
    raise AssertionError('program did not return')


def test_filter_catches_listed_syscalls_and_allows_regular_io():
    program=sc.compile_filter(7)
    for name,nr in sc.SYSCALLS.items():
        assert interpret(program,nr,arg0=8)==sc.SECCOMP_RET_USER_NOTIF,name
    assert interpret(program,0)==sc.SECCOMP_RET_ALLOW  # read
    assert interpret(program,1)==sc.SECCOMP_RET_ALLOW  # write
    assert interpret(program,59)==sc.SECCOMP_RET_ALLOW # execve
    assert interpret(program,sc.SYSCALLS['sendmsg'],arg0=7)==sc.SECCOMP_RET_ALLOW
    assert interpret(program,sc.SYSCALLS['sendmsg'],arg0=8)==sc.SECCOMP_RET_USER_NOTIF


def test_filter_traps_prlimit64_on_another_process_only():
    program=sc.compile_filter(7)
    assert interpret(program,sc.PRLIMIT64_NR,arg0=0)==sc.SECCOMP_RET_ALLOW
    for pid in (1,2,12345,-1):
        assert interpret(program,sc.PRLIMIT64_NR,arg0=pid)==sc.SECCOMP_RET_USER_NOTIF
    for name,nr in sc.SYSCALLS.items():          # the list after the new block is unchanged
        assert interpret(program,nr,arg0=8)==sc.SECCOMP_RET_USER_NOTIF,name
    assert interpret(program,0)==sc.SECCOMP_RET_ALLOW


def test_filter_traps_namespace_clone_and_wrong_arch():
    program=sc.compile_filter(7)
    assert interpret(program,sc.CLONE_NR,arg0=0)==sc.SECCOMP_RET_ALLOW
    for bit in (0x80,0x20000,0x02000000,0x04000000,0x08000000,0x10000000,0x20000000,0x40000000):
        assert interpret(program,sc.CLONE_NR,arg0=bit)==sc.SECCOMP_RET_USER_NOTIF
    assert interpret(program,sc.CLONE_NR,arg0=1<<40)==sc.SECCOMP_RET_USER_NOTIF
    assert interpret(program,0,arch=0x40000003)==sc.SECCOMP_RET_KILL_PROCESS
    assert interpret(program,sc.X32_SYSCALL_BIT)==sc.SECCOMP_RET_KILL_PROCESS
    with pytest.raises(ValueError): sc.compile_filter(2)


def test_monitor_durably_records_before_killing_cgroup():
    calls=[]
    def ioctl(fd,req,buf,mutate):
        assert fd==3 and req==sc.SECCOMP_IOCTL_NOTIF_RECV and mutate
        struct.pack_into('=QIIiI',buf,0,123,456,0,42,sc.AUDIT_ARCH_X86_64)
    def write(fd,data):
        calls.append(('write',fd,bytes(data)))
        return min(len(data),5) if fd==4 else len(data)
    def fsync(fd): calls.append(('fsync',fd))
    result=sc.monitor_one(3,5,4,ioctl=ioctl,write=write,fsync=fsync)
    assert result['pid']==456 and result['syscall']==42 and result['decision']=='STOP'
    assert calls[-2:]==[('fsync',4),('write',5,b'1\n')]
    assert b''.join(x[2][:5] for x in calls if x[0]=='write' and x[1]==4).endswith(b'\n')


@pytest.mark.parametrize('failure',['receive','write','fsync'])
def test_monitor_kills_cgroup_on_failure(failure):
    calls=[]
    def ioctl(fd,req,buf,mutate):
        if failure=='receive': raise OSError(errno.EIO,'receive')
        struct.pack_into('=QIIiI',buf,0,1,2,0,41,sc.AUDIT_ARCH_X86_64)
    def write(fd,data):
        calls.append((fd,bytes(data)))
        if fd==4 and failure=='write': raise OSError(errno.ENOSPC,'write')
        return len(data)
    def fsync(fd):
        if failure=='fsync': raise OSError(errno.EIO,'fsync')
    with pytest.raises(OSError): sc.monitor_one(3,5,4,ioctl=ioctl,write=write,fsync=fsync)
    assert calls[-1]==(5,b'1\n')


def test_install_refuses_non_linux_without_attempting_syscalls(monkeypatch):
    monkeypatch.setattr(sc.platform,'system',lambda:'Darwin')
    with pytest.raises(RuntimeError,match='Linux x86-64 only'): sc.install_listener(7)


def test_listener_handoff_rejects_extra_descriptors_and_closes_them(monkeypatch):
    import array
    import socket
    closed=[];marked=[]
    monkeypatch.setattr(sc.os,'close',lambda fd:closed.append(fd))
    monkeypatch.setattr(sc.os,'set_inheritable',lambda fd,flag:marked.append((fd,flag)))
    class Channel:
        def __init__(self,values,flags=0): self.values=values;self.flags=flags
        def recvmsg(self,*args):
            fds=array.array('i',self.values)
            return b'L',[(socket.SOL_SOCKET,socket.SCM_RIGHTS,fds.tobytes())],self.flags,None
    assert sc.receive_listener(Channel([9]))==9
    assert marked==[(9,False)] and closed==[]
    with pytest.raises(RuntimeError,match='invalid listener handoff'): sc.receive_listener(Channel([10,11]))
    assert closed==[10,11]
    with pytest.raises(RuntimeError,match='invalid listener handoff'): sc.receive_listener(Channel([12],socket.MSG_CTRUNC))
    assert closed==[10,11,12]


def test_send_listener_uses_only_preopened_channel():
    import socket
    class Channel:
        def fileno(self): return 7
        def sendmsg(self,data,ancillary):
            assert data==[b'L'] and ancillary[0][:2]==(socket.SOL_SOCKET,socket.SCM_RIGHTS)
            assert list(ancillary[0][2])==[8]
            return 1
    sc.send_listener(Channel(),8)
