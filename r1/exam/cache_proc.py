"""Linux /proc snapshot evidence for D3; not a continuous census or author gate."""
from pathlib import Path
import errno
import os
import time
import hashlib
import json

CENSUS_METHOD='linux_proc_exe_snapshot'
CENSUS_SCOPE='cooperative same-UID assumption; visible /proc executable basename llama-server only; inaccessible processes, other names, other namespaces and between-sample gaps unobserved'
# Transient/unreadable /proc entries are OBSERVATION GAPS, not evidence that a process
# does not exist (author requirement: record the scope and the gap).  Only errnos that
# are not plausible for /proc races STOP the sample.
CENSUS_GAP_ERRNOS=frozenset({errno.ESRCH,errno.ENOENT,errno.EACCES,errno.EPERM,errno.EINVAL,errno.ENOTDIR,errno.ELOOP})


def census_digest(sample):
    """Detect accidental changes; this digest does not authenticate a sample."""
    body={k:v for k,v in sample.items() if k!='snapshot_sha256'}
    return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_census_snapshot(sample,identity,*,earliest_ns=None,latest_ns=None):
    """Validate a discrete observation; this cannot establish continuity."""
    if (not isinstance(identity,dict) or type(identity.get('pid')) is not int or identity['pid']<=0 or
        type(identity.get('process_start_ticks')) is not int or identity['process_start_ticks']<=0 or
        not isinstance(identity.get('binary'),str) or not identity['binary']):
        raise RuntimeError('STOP: census identity invalid')
    expected={'pid':identity['pid'],'process_start_ticks':identity['process_start_ticks'],'executable':identity['binary']}
    try:
        if (not isinstance(sample,dict) or sample.get('method')!=CENSUS_METHOD or sample.get('scope')!=CENSUS_SCOPE or
            type(sample.get('count')) is not int or sample['count']!=1 or
            type(sample.get('pid')) is not int or sample['pid']!=identity['pid'] or
            type(sample.get('process_start_ticks')) is not int or sample['process_start_ticks']!=identity['process_start_ticks'] or
            type(sample.get('monotonic_ns')) is not int or sample['monotonic_ns']<0 or
            not isinstance(sample.get('observed'),list) or len(sample['observed'])!=1 or
            json.dumps(sample['observed'][0],sort_keys=True,separators=(',',':'))!=json.dumps(expected,sort_keys=True,separators=(',',':')) or
            sample.get('snapshot_sha256')!=census_digest(sample) or
            sample.get('host_global_single_server')!='NOT_CHECKABLE' or
            sample.get('unobserved_same_uid_calls')!='assumed absent by author decision, not measured' or
            type(sample.get('inaccessible_executable_links')) is not int or sample['inaccessible_executable_links']<0 or
            type(sample.get('missing_executable_links')) is not int or sample['missing_executable_links']<0 or
            type(sample.get('unreadable_executable_links')) is not int or sample['unreadable_executable_links']<0 or
            not isinstance(sample.get('unreadable_executable_errnos'),list) or
            not all(isinstance(name,str) and name for name in sample['unreadable_executable_errnos']) or
            not isinstance(sample.get('unreadable_executable_samples'),list) or
            len(sample['unreadable_executable_samples'])>32 or
            (earliest_ns is not None and sample['monotonic_ns']<earliest_ns) or
            (latest_ns is not None and sample['monotonic_ns']>latest_ns)):
            raise RuntimeError('STOP: server census or identity mismatch')
    except (TypeError,ValueError,KeyError) as exc:
        raise RuntimeError('STOP: server census or identity mismatch') from exc
    return sample


def process_start_ticks(pid, *, proc_root='/proc'):
    if type(pid) is not int or pid<=0:
        raise ValueError('STOP: invalid pid')
    try:
        raw=(Path(proc_root)/str(pid)/'stat').read_text()
        fields=raw[raw.rindex(')')+2:].split()
        value=int(fields[19])  # /proc/<pid>/stat field 22; fields starts at field 3
    except (OSError,ValueError,IndexError) as exc:
        raise RuntimeError('STOP: process start time unavailable') from exc
    if value<=0: raise RuntimeError('STOP: invalid process start time')
    return value


def sample_llama_server_processes(identity, *, proc_root='/proc'):
    """Snapshot processes whose /proc executable basename is llama-server.

    Other executable names, namespaces, hidden /proc processes and between-sample
    lifetimes are not covered; callers cannot treat this as a global proof.
    """
    root=Path(proc_root)
    try:
        entries=list(root.iterdir())
        matched=[];inaccessible=0;missing_exe=0;unreadable=[]
        for entry in entries:
            if not entry.name.isdecimal(): continue
            pid=int(entry.name)
            try:
                executable=os.readlink(entry/'exe')
            except FileNotFoundError:
                missing_exe+=1
                continue
            except PermissionError:
                inaccessible+=1
                continue
            except OSError as exc:
                if exc.errno in CENSUS_GAP_ERRNOS:
                    # The pid may have exited between listing and reading, or its
                    # link may be unreadable for this UID: record the gap, do not
                    # claim the process exists or does not exist.
                    unreadable.append({'pid':pid,'errno':exc.errno,
                                       'error':errno.errorcode.get(exc.errno,str(exc.errno))})
                    continue
                raise RuntimeError(f'STOP: unexpected executable census error for pid {pid} '
                                   f'(errno {exc.errno} {errno.errorcode.get(exc.errno,"")})') from exc
            if Path(executable).name=='llama-server':
                matched.append({'pid':pid,'process_start_ticks':process_start_ticks(pid,proc_root=proc_root),
                                'executable':executable})
        current=process_start_ticks(identity['pid'],proc_root=proc_root)
        if current!=identity['process_start_ticks']:
            raise RuntimeError('STOP: server process identity changed')
        if len(matched)!=1 or matched[0]['pid']!=identity['pid'] or matched[0]['process_start_ticks']!=current:
            raise RuntimeError('STOP: observed server count or identity mismatch')
        result={'method':CENSUS_METHOD,'scope':CENSUS_SCOPE,
                'count':len(matched),'pid':identity['pid'],'process_start_ticks':current,
                'observed':matched,'monotonic_ns':time.monotonic_ns(),
                'inaccessible_executable_links':inaccessible,'missing_executable_links':missing_exe,
                'unreadable_executable_links':len(unreadable),
                'unreadable_executable_errnos':sorted({row['error'] for row in unreadable}),
                'unreadable_executable_samples':unreadable[:8],
                'unobserved_same_uid_calls':'assumed absent by author decision, not measured',
                'host_global_single_server':'NOT_CHECKABLE'}
        result['snapshot_sha256']=census_digest(result)
        return result
    except (OSError,KeyError,TypeError) as exc:
        raise RuntimeError('STOP: process census unavailable') from exc
