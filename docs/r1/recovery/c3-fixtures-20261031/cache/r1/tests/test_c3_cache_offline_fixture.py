import hashlib
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from r1.scripts import c3_cache_offline_fixture as f


def test_copy_binds_complete_tree_and_detects_modification(tmp_path):
    root = tmp_path / 'input'; root.mkdir(); (root / 'cache.gz').write_bytes(b'data')
    expected = {'cache.gz': hashlib.sha256(b'data').hexdigest()}
    with tempfile.TemporaryDirectory(dir=Path('/tmp').resolve()) as temp:
        output = Path(temp) / 'copy'
        result = f.copy_verified_cache(root, output, expected)
        assert result['copied_before'] == expected
        assert f.check_unchanged(root, output, expected)['source_after'] == expected
        (output / 'extra').write_text('modified')
        with pytest.raises(ValueError, match='changed'):
            f.check_unchanged(root, output, expected)


def test_every_symlink_layer_rejected(tmp_path):
    root = tmp_path / 'input'; root.mkdir(); (root / 'real').mkdir(); (root / 'real' / 'data').write_text('x')
    (root / 'alias').symlink_to(root / 'real', target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        f.read_nofollow(root, 'alias/data')
    with pytest.raises(ValueError, match='symlink'):
        f.manifest(root)


def test_non_tmp_copy_and_existing_target_rejected(tmp_path):
    root = tmp_path / 'input'; root.mkdir(); (root / 'x').write_text('x')
    expected = {'x': hashlib.sha256(b'x').hexdigest()}
    with pytest.raises(ValueError, match='/tmp'):
        f.copy_verified_cache(root, tmp_path / 'output', expected)
    with tempfile.TemporaryDirectory(dir=Path('/tmp').resolve()) as temp:
        with pytest.raises(FileExistsError):
            f.copy_verified_cache(root, Path(temp), expected)


def test_dataset_and_benchmark_are_both_bound():
    d = json.dumps({'node_name':'n','dataset_id':40,'dataset_name':'sonar','target':'Class'}).encode()
    b = b'frozen benchmark'
    proof = {'dataset_json_sha256':hashlib.sha256(d).hexdigest(), 'benchmark_py_sha256':hashlib.sha256(b).hexdigest(),
             'node_name':'n','dataset_id':40,'dataset_name':'sonar','target':'Class'}
    assert f.validate_dataset_metadata(d,b,proof)['dataset_id'] == 40
    with pytest.raises(ValueError, match='benchmark'):
        f.validate_dataset_metadata(d,b+b'!',proof)
    with pytest.raises(ValueError, match='identity'):
        f.validate_dataset_metadata(d,b,{**proof,'target':'wrong'})


def test_data_shape_target_and_dtypes_require_independent_expectations():
    bunch = type('Bunch', (), {'data': pd.DataFrame({'x': [1,2]}), 'target': pd.Series([0,1],name='Class')})()
    expected = {'shape':[2,1],'target_length':2,'columns':['x'],'feature_dtypes':['int64'],
                'target_name':'Class','target_dtype':'int64'}
    assert f.validate_frame(bunch,expected) == expected
    with pytest.raises(ValueError, match='target'):
        f.validate_frame(bunch,{**expected,'target_name':'different'})
    with pytest.raises(ValueError, match='dtypes'):
        f.validate_frame(bunch,{**expected,'feature_dtypes':['float64']})


def test_mountinfo_decoder_and_unprotected_launcher_fail_closed(monkeypatch):
    import sys
    records = f._mount_records('1 2 0:1 / /tmp/foo\\040bar rw - ext4 /dev/x rw')
    assert records[0][0] == Path('/tmp/foo bar')
    monkeypatch.setattr(sys, 'argv', ['fixture'])
    with pytest.raises(SystemExit):
        f.main()


def test_case_uses_only_copied_cache_and_records_stop(tmp_path, monkeypatch):
    import ctypes
    import os
    import sklearn.datasets
    with tempfile.TemporaryDirectory(dir=Path('/tmp').resolve()) as temp:
        root = Path(temp); source = root / 'source'; source.mkdir()
        cache = source / 'cache'; cache.mkdir(); (cache / 'item.gz').write_bytes(b'data')
        node = source / 'node'; node.mkdir()
        d = json.dumps({'node_name':'n','dataset_id':40,'dataset_name':'sonar','target':'Class'}).encode()
        b = b'frozen benchmark'; (node/'dataset.json').write_bytes(d); (node/'benchmark.py').write_bytes(b)
        case = root / 'case_01'; case.mkdir()
        monkeypatch.setenv('HOME', str(case)); monkeypatch.setenv('TMPDIR', str(case))
        monkeypatch.setattr(f, 'require_sources_readonly', lambda paths: None)
        monkeypatch.setattr(f, 'require_socket_denial', lambda: None)
        monkeypatch.setattr(ctypes, 'CDLL', lambda *args, **kwargs: type('C', (), {'prctl': lambda self,*a: 2})())
        frame = {'shape':[2,1], 'target_length':2, 'columns':['x'], 'feature_dtypes':['int64'],
                 'target_name':'Class','target_dtype':'int64'}
        expected = {'case_id':'n-1','node_name':'n','dataset_id':40,'dataset_name':'sonar','target':'Class',
                    'dataset_json_sha256':hashlib.sha256(d).hexdigest(),'benchmark_py_sha256':hashlib.sha256(b).hexdigest(),
                    'cache_sha256':{'item.gz':hashlib.sha256(b'data').hexdigest()},'frame':frame}
        from importlib import metadata
        expected['library_versions'] = {n: metadata.version(n) for n in ('scikit-learn', 'numpy', 'scipy', 'pandas')}
        bunch = type('Bunch', (), {'data':pd.DataFrame({'x':[1,2]}),
                                    'target':pd.Series([0,1],name='Class'),
                                    'details':{'id':'40','name':'sonar'}})()
        def fetch(**kwargs):
            assert kwargs == {'data_id':40,'as_frame':True,'parser':'auto','data_home':str(case/'data_cache')}
            return bunch
        monkeypatch.setattr(sklearn.datasets, 'fetch_openml', fetch)
        assert f.fetch_case(case, cache, node, [source], expected)['status'] == 'PASS_ENGINEERING_ONLY'
        assert (case/'dataset_fixture_result.json').exists()
        with pytest.raises(FileExistsError):
            f.fetch_case(case, cache, node, [source], expected)
        other = root / 'case_02'; other.mkdir()
        monkeypatch.setenv('HOME', str(other)); monkeypatch.setenv('TMPDIR', str(other))
        wrong = {**expected, 'frame': {**frame, 'target_name': 'different'}}
        with pytest.raises(ValueError, match='dataset.json target'):
            f.fetch_case(other, cache, node, [source], wrong)
        assert json.loads((other/'dataset_fixture_STOP.json').read_text())['status'] == 'STOP'


def test_supervisor_records_sigsys_and_stops(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import signal
    monkeypatch.setattr(f.subprocess,'run',lambda *a,**k: SimpleNamespace(returncode=-signal.SIGSYS,stdout='partial',stderr=''))
    with pytest.raises(ValueError, match='killed'):
        f.supervise_guarded_child(['fake'],tmp_path,{})
    assert json.loads((tmp_path/'dataset_supervisor_STOP.json').read_text())['status'] == 'STOP'
    assert (tmp_path/'dataset_fixture_stdout.txt').read_text() == 'partial'


def test_cache_traversal_errors_do_not_silently_pass(tmp_path, monkeypatch):
    root = tmp_path / 'input'; root.mkdir()
    def broken_walk(path, **kwargs):
        kwargs['onerror'](PermissionError('unreadable'))
        return iter(())
    monkeypatch.setattr(f.os, 'walk', broken_walk)
    with pytest.raises(ValueError, match='traversal'):
        f.manifest(root)


def test_supervisor_records_timeout_partial_output(tmp_path, monkeypatch):
    import subprocess
    def timeout(*a,**k):
        raise subprocess.TimeoutExpired('fake', 1, output=b'partial out', stderr=b'partial err')
    monkeypatch.setattr(f.subprocess, 'run', timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        f.supervise_guarded_child(['fake'], tmp_path, {})
    assert json.loads((tmp_path/'dataset_supervisor_STOP.json').read_text())['status'] == 'STOP'
    assert 'partial out' in (tmp_path/'dataset_fixture_stdout.txt').read_text()


@pytest.mark.skipif(__import__('sys').platform != 'linux', reason='requires Linux user/mount namespaces')
def test_linux_readonly_mount_refuses_write_and_nested_mount(tmp_path):
    import os, subprocess, sys
    source = tmp_path / 'source'; source.mkdir(); (source/'file').write_text('safe')
    nested = source/'nested'; nested.mkdir(); other = tmp_path/'other'; other.mkdir()
    def run_case(nested_first):
        reader,writer = os.pipe()
        mount_fd = os.open('/proc/self/ns/mnt', os.O_RDONLY)
        network_fd = os.open('/proc/self/ns/net', os.O_RDONLY)
        payload = {'parent_pid':os.getpid(), 'parent_uid':os.getuid(), 'parent_gid':os.getgid(),
                   'mnt_namespace':os.readlink('/proc/self/ns/mnt'), 'net_namespace':os.readlink('/proc/self/ns/net'),
                   'parent_groups':os.getgroups()}
        code = """import os,subprocess,sys
from pathlib import Path
from r1.scripts.c3_cache_offline_fixture import protect_sources_readonly,read_pipe_attestation
attestation=read_pipe_attestation(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3])); p=Path(sys.argv[4])
if sys.argv[5]=='nested':
 subprocess.run(['mount','--bind',sys.argv[6],str(p/'nested')],check=True)
 try: protect_sources_readonly([p],attestation)
 except ValueError as e:
  assert 'nested mount' in str(e)
 else: raise RuntimeError('nested mount accepted')
else:
 protect_sources_readonly([p],attestation)
 try: fd=os.open(p/'file',os.O_WRONLY)
 except OSError: pass
 else:
  os.close(fd); raise RuntimeError('writable source')
"""
        command=['unshare','--user','--map-root-user','--mount','--net','--propagation','private','--',
                 sys.executable,'-B','-c',code,str(reader),str(mount_fd),str(network_fd),str(source),
                 'nested' if nested_first else 'readonly',str(other)]
        proc=subprocess.Popen(command,pass_fds=(reader,mount_fd,network_fd),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        os.close(reader); os.close(mount_fd); os.close(network_fd)
        os.write(writer,json.dumps(payload).encode()); os.close(writer)
        stdout,stderr=proc.communicate(timeout=30)
        assert proc.returncode == 0, stderr
    run_case(False)
    assert (source/'file').read_text() == 'safe'
    run_case(True)


def test_refuses_to_mount_when_not_root_mapped(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(f.os, 'getuid', lambda: 1000)
    monkeypatch.setattr(f.subprocess, 'run', lambda *a, **k: calls.append(a))
    with pytest.raises(ValueError, match='mount namespace'):
        f.protect_sources_readonly([tmp_path], {})
    assert not calls


def test_socket_filter_probe_rejects_normal_exit(monkeypatch):
    monkeypatch.setattr(f.resource, 'setrlimit', lambda *a: None)
    monkeypatch.setattr(f.os, 'fork', lambda: 1234)
    monkeypatch.setattr(f.os, 'waitpid', lambda *a: (1234, 0))
    with pytest.raises(ValueError, match='seccomp'):
        f.require_socket_denial()


def test_pipe_identity_binds_parent_namespaces_and_uid_gid(monkeypatch):
    monkeypatch.setattr(f.os, 'getgroups', lambda: [65534, 0])
    payload = {'parent_pid':123,'parent_uid':1001,'parent_gid':1002,
               'mnt_namespace':'mnt:[11]','net_namespace':'net:[12]', 'parent_groups':[1002,1003]}
    result = f.validate_pipe_identity(payload,123,'mnt:[11]','net:[12]','mnt:[21]','net:[22]',
                                      '0 1001 1\n','0 1002 1\n')
    assert result['parent_pid'] == 123
    assert result['child_groups'] == [65534,0]
    for bad in ({**payload, 'parent_pid': 124}, {**payload,'mnt_namespace':'mnt:[99]'},
                {**payload,'parent_uid':0}):
        with pytest.raises(ValueError, match='STOP'):
            f.validate_pipe_identity(bad,123,'mnt:[11]','net:[12]','mnt:[21]','net:[22]',
                                     '0 1001 1\n','0 1002 1\n')
    with pytest.raises(ValueError, match='STOP'):
        f.validate_pipe_identity(payload,123,'mnt:[11]','net:[12]','mnt:[11]','net:[22]',
                                 '0 1001 1\n','0 1002 1\n')
    with pytest.raises(ValueError, match='STOP'):
        f.validate_pipe_identity(payload,123,'mnt:[11]','net:[12]','mnt:[21]','net:[22]',
                                 '0 9999 1\n','0 1002 1\n')


def test_non_pipe_or_repeated_record_fails_closed(tmp_path):
    import os
    with (tmp_path/'regular').open('w+') as regular:
        fake = [os.dup(regular.fileno()) for _ in range(3)]
        with pytest.raises(ValueError, match='unverified'):
            f.read_pipe_attestation(*fake)
        for fd in fake:
            with pytest.raises(OSError): os.fstat(fd)
    reader, writer = os.pipe()
    os.write(writer,b'{}{}'); os.close(writer)
    mount_fd, network_fd = os.open(os.devnull, os.O_RDONLY), os.open(os.devnull, os.O_RDONLY)
    with pytest.raises(ValueError, match='unverified'):
        f.read_pipe_attestation(reader,mount_fd,network_fd)
    for fd in (reader,mount_fd,network_fd):
        with pytest.raises(OSError): os.fstat(fd)


def test_pipe_with_missing_parent_fails_closed(monkeypatch):
    import os
    reader, writer = os.pipe()
    os.write(writer, json.dumps({'parent_pid':123}).encode()); os.close(writer)
    monkeypatch.setattr(f.os, 'getppid', lambda: 123)
    def dead(*args):
        raise ProcessLookupError('parent died')
    monkeypatch.setattr(f.os, 'kill', dead)
    mount_fd, network_fd = os.open(os.devnull, os.O_RDONLY), os.open(os.devnull, os.O_RDONLY)
    with pytest.raises(ValueError, match='unverified'):
        f.read_pipe_attestation(reader,mount_fd,network_fd)


def test_pipe_refuses_oversized_payload():
    import os
    import threading
    reader, writer = os.pipe()
    def send():
        try:
            os.write(writer, b' ' * 8193)
        except BrokenPipeError:
            pass
        finally:
            os.close(writer)
    thread = threading.Thread(target=send)
    thread.start()
    mount_fd, network_fd = os.open(os.devnull, os.O_RDONLY), os.open(os.devnull, os.O_RDONLY)
    with pytest.raises(ValueError, match='unverified'):
        f.read_pipe_attestation(reader,mount_fd,network_fd)
    thread.join(timeout=5)
    assert not thread.is_alive()


def test_launcher_closes_namespace_handles_if_readlink_fails(tmp_path, monkeypatch):
    import os
    opened = []
    original_open = os.open
    def fake_open(path, flags, *args, **kwargs):
        if path in ('/proc/self/ns/mnt','/proc/self/ns/net'):
            fd = original_open(os.devnull, os.O_RDONLY)
            opened.append(fd)
            return fd
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(f.os, 'getuid', lambda: 1001)
    monkeypatch.setattr(f.os, 'open', fake_open)
    def fail_link(path):
        raise PermissionError('synthetic denial')
    monkeypatch.setattr(f.os, 'readlink', fail_link)
    with pytest.raises(PermissionError):
        f.launch_bound_namespace(['unused'], tmp_path, {})
    assert len(opened) == 2
    for fd in opened:
        with pytest.raises(OSError): os.fstat(fd)


@pytest.mark.parametrize('same_object', [False, True])
def test_inherited_namespace_kernel_objects_and_handle_closure(monkeypatch, same_object):
    import os
    from types import SimpleNamespace
    reader, writer = os.pipe()
    mount_fd, network_fd = os.open(os.devnull, os.O_RDONLY), os.open(os.devnull, os.O_RDONLY)
    payload = {'parent_pid':123,'parent_uid':1001,'parent_gid':1002,
               'mnt_namespace':'mnt:[11]','net_namespace':'net:[12]', 'parent_groups':[1002]}
    os.write(writer,json.dumps(payload,sort_keys=True).encode()); os.close(writer)
    real_fstat, real_stat, real_readlink = os.fstat, os.stat, os.readlink
    def fake_fstat(fd):
        if fd == mount_fd: return SimpleNamespace(st_ino=11,st_dev=9)
        if fd == network_fd: return SimpleNamespace(st_ino=12,st_dev=9)
        return real_fstat(fd)
    def fake_stat(path, *args, **kwargs):
        if path == '/proc/self/ns/mnt': return SimpleNamespace(st_ino=11 if same_object else 21,st_dev=9)
        if path == '/proc/self/ns/net': return SimpleNamespace(st_ino=22,st_dev=9)
        return real_stat(path, *args, **kwargs)
    def fake_readlink(path, *args, **kwargs):
        if path == f'/proc/self/fd/{mount_fd}': return 'mnt:[11]'
        if path == f'/proc/self/fd/{network_fd}': return 'net:[12]'
        if path == '/proc/self/ns/mnt': return 'mnt:[11]' if same_object else 'mnt:[21]'
        if path == '/proc/self/ns/net': return 'net:[22]'
        return real_readlink(path, *args, **kwargs)
    original_read = Path.read_text
    def fake_read(path, *args, **kwargs):
        if str(path) == '/proc/self/uid_map': return '0 1001 1\n'
        if str(path) == '/proc/self/gid_map': return '0 1002 1\n'
        return original_read(path, *args, **kwargs)
    monkeypatch.setattr(f.os,'getppid',lambda:123)
    monkeypatch.setattr(f.os,'kill',lambda *args:None)
    monkeypatch.setattr(f.os,'getgroups',lambda:[65534,0])
    monkeypatch.setattr(f.os,'fstat',fake_fstat)
    monkeypatch.setattr(f.os,'stat',fake_stat)
    monkeypatch.setattr(f.os,'readlink',fake_readlink)
    monkeypatch.setattr(Path,'read_text',fake_read)
    if same_object:
        with pytest.raises(ValueError,match='unverified'):
            f.read_pipe_attestation(reader,mount_fd,network_fd)
    else:
        observed = f.read_pipe_attestation(reader,mount_fd,network_fd)
        assert observed['parent_namespace_objects'] == [{'dev':9,'ino':11},{'dev':9,'ino':12}]
        assert observed['child_mount_namespace'] == 'mnt:[21]'
    for fd in (reader,mount_fd,network_fd):
        with pytest.raises(OSError): real_fstat(fd)
