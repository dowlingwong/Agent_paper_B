"""Drop and check Linux bootstrap capabilities; not a sandbox by itself."""
from __future__ import annotations
import ctypes
import os
import platform

PR_CAPBSET_READ=23
PR_CAPBSET_DROP=24
PR_CAP_AMBIENT=47
PR_CAP_AMBIENT_CLEAR_ALL=4
LINUX_CAPABILITY_VERSION_3=0x20080522


class CapabilityStop(RuntimeError): pass


class Header(ctypes.Structure):
    _fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]


class Data(ctypes.Structure):
    _fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]


def drop_and_verify():
    """Clear bounding, ambient, effective, permitted and inheritable caps.

    Irreversible: run only in the trusted bootstrap immediately before seccomp.
    Requires Linux x86-64; any failed step is STOP and the child must exit.
    """
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):
        raise CapabilityStop('STOP: Linux x86-64 required')
    libc=ctypes.CDLL(None,use_errno=True)
    # Kernel publishes the highest capability number; avoid treating unknown
    # prctl errors as proof that the bounding set was dropped.
    try:
        with open('/proc/sys/kernel/cap_last_cap','r',encoding='ascii') as f:cap_last=int(f.read().strip())
    except (OSError,ValueError) as exc:raise CapabilityStop('STOP: cannot inspect kernel capabilities') from exc
    if not 0<=cap_last<=63:raise CapabilityStop('STOP: unsupported capability range')
    if libc.prctl(PR_CAP_AMBIENT,PR_CAP_AMBIENT_CLEAR_ALL,0,0,0)!=0:
        raise CapabilityStop('STOP: cannot clear ambient capabilities')
    for cap in range(cap_last+1):
        if libc.prctl(PR_CAPBSET_DROP,cap,0,0,0)!=0:
            raise CapabilityStop(f'STOP: cannot drop bounding capability {cap}')
    header=Header(LINUX_CAPABILITY_VERSION_3,0);data=(Data*2)()
    # x86-64 capset=126, capget=125.
    if libc.syscall(126,ctypes.byref(header),ctypes.byref(data))!=0:
        raise CapabilityStop('STOP: capset failed')
    observed=(Data*2)()
    if libc.syscall(125,ctypes.byref(header),ctypes.byref(observed))!=0:
        raise CapabilityStop('STOP: capget failed')
    if any(x.effective or x.permitted or x.inheritable for x in observed):
        raise CapabilityStop('STOP: capabilities remain')
    for cap in range(cap_last+1):
        if libc.prctl(PR_CAPBSET_READ,cap,0,0,0)!=0:
            raise CapabilityStop(f'STOP: bounding capability {cap} remains or is unverifiable')
