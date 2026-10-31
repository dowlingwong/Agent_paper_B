"""Candidate dataset-only offline fixture. NOT authorized or accepted.

Launcher requires a published independent review binding this exact fixture,
guard and case record. It must enter fresh private user/mount/network namespaces.
This candidate has not passed Linux mount tests or independent review.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import re
import resource
import signal
import socket
import subprocess
import sys
import stat
from pathlib import Path


def _fail(message):
    raise ValueError('STOP: ' + message)


def directory_nofollow(path: Path) -> None:
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        _fail('unsafe directory')
    current = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=current)
            os.close(current)
            current = nxt
    except OSError as exc:
        raise ValueError('STOP: missing or symlinked directory') from exc
    finally:
        os.close(current)


def read_nofollow(root: Path, relative: str) -> bytes:
    """Open every relative path component with O_NOFOLLOW, never follow links."""
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or any(x in ('', '.', '..') for x in rel.parts):
        _fail('unsafe relative path')
    root = Path(root)
    if not root.is_absolute():
        _fail('root must be absolute')
    parts = root.parts[1:] + rel.parts
    current = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for i, part in enumerate(parts):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
            if i != len(parts) - 1:
                flags |= os.O_DIRECTORY
            nxt = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = nxt
        if not stat.S_ISREG(os.fstat(current).st_mode):
            _fail('not a regular file')
        chunks = []
        while True:
            data = os.read(current, 1024 * 1024)
            if not data:
                return b''.join(chunks)
            chunks.append(data)
    except OSError as exc:
        raise ValueError('STOP: missing, unsafe or symlinked path') from exc
    finally:
        os.close(current)


def manifest(root: Path) -> dict[str, str]:
    """Hash a complete tree, rejecting every symlink, device and special file."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        _fail('cache root missing or symlink')
    directory_nofollow(root)
    result = {}
    def walk_error(exc):
        raise ValueError('STOP: cache traversal failed') from exc
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        directory_nofollow(Path(directory))
        for name in dirs + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                _fail('cache includes symlink or non-regular file')
        for name in files:
            path = Path(directory) / name
            rel = str(path.relative_to(root))
            result[rel] = hashlib.sha256(read_nofollow(root, rel)).hexdigest()
    if not result:
        _fail('empty cache')
    return result


def copy_verified_cache(source: Path, output: Path, expected: dict[str, str]) -> dict:
    """Copy to a *new* scratch directory, checking source and target bytes."""
    before = manifest(source)
    if before != expected:
        _fail('source differs from independently reviewed manifest')
    output = Path(output)
    if not output.is_absolute() or not output.parent.resolve().is_relative_to(Path('/tmp').resolve()):
        _fail('output must be below new local /tmp scratch')
    directory_nofollow(output.parent)
    output.mkdir(mode=0o700, exist_ok=False)
    for rel, sha in sorted(expected.items()):
        data = read_nofollow(source, rel)
        if hashlib.sha256(data).hexdigest() != sha:
            _fail('source changed during copy')
        target = output / rel
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    copy = manifest(output)
    after = manifest(source)
    if copy != before or after != before:
        _fail('source or copied cache changed')
    return {'source_before': before, 'copied_before': copy, 'source_after_copy': after}


def copy_verified_cache_at(source_fd: int, source_relative: str, output: Path,
                           expected: dict[str, str]) -> tuple[dict, int]:
    """Copy from a retained read-only mount FD; never reopen source paths."""
    from r1.scripts.c3_mount_inode_candidate import (manifest_directory_nofollow,
                                                       manifest_relative_nofollow, read_relative_nofollow)
    before = manifest_relative_nofollow(source_fd, source_relative)
    if before != expected:
        _fail('source differs from independently reviewed manifest')
    output = Path(output)
    if not output.is_absolute() or not output.parent.resolve().is_relative_to(Path('/tmp').resolve()):
        _fail('output must be below new local /tmp scratch')
    directory_nofollow(output.parent)
    output.mkdir(mode=0o700, exist_ok=False)
    output_fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for rel, sha in sorted(expected.items()):
            path = Path(rel)
            if path.is_absolute() or not path.parts or '..' in path.parts:
                _fail('unsafe cache relative path')
            data = read_relative_nofollow(source_fd, str(Path(source_relative) / path))
            if hashlib.sha256(data).hexdigest() != sha:
                _fail('source changed during copy')
            parent = os.dup(output_fd)
            try:
                for part in path.parts[:-1]:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=parent)
                    except FileExistsError:
                        pass
                    nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
                    os.close(parent)
                    parent = nxt
                file_fd = os.open(path.parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                                  0o600, dir_fd=parent)
                with os.fdopen(file_fd, 'wb') as stream:
                    stream.write(data)
            finally:
                os.close(parent)
        copied = manifest_directory_nofollow(output_fd)
        after = manifest_relative_nofollow(source_fd, source_relative)
        if copied != before or after != before:
            _fail('source or copied cache changed')
        return {'source_before': before, 'copied_before': copied, 'source_after_copy': after}, output_fd
    except BaseException:
        os.close(output_fd)
        raise


def validate_dataset_metadata(dataset_bytes: bytes, benchmark_bytes: bytes, expected: dict) -> dict:
    """Bind exact dataset.json and benchmark.py bytes before any dataset access."""
    if hashlib.sha256(dataset_bytes).hexdigest() != expected.get('dataset_json_sha256') or \
       hashlib.sha256(benchmark_bytes).hexdigest() != expected.get('benchmark_py_sha256'):
        _fail('dataset.json or benchmark.py differs from reviewed source')
    try:
        dataset = json.loads(dataset_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('STOP: dataset.json invalid') from exc
    for key in ('node_name', 'dataset_id', 'dataset_name', 'target'):
        if key not in dataset or key not in expected or dataset[key] != expected[key]:
            _fail('dataset identity or target mismatch')
    return dataset


def validate_frame(bunch, expected: dict) -> dict:
    """Validate exact separately reviewed shape, target, column names and dtypes."""
    data, target = getattr(bunch, 'data', None), getattr(bunch, 'target', None)
    if data is None or target is None or len(data) == 0 or len(data) != len(target):
        _fail('missing data or target')
    observed = {'shape': list(data.shape), 'target_length': len(target),
                'columns': list(data.columns), 'feature_dtypes': [str(x) for x in data.dtypes],
                'target_name': getattr(target, 'name', None), 'target_dtype': str(target.dtype)}
    for key, value in observed.items():
        if key not in expected or expected[key] != value:
            _fail(f'dataset attribute {key} differs from reviewed expectation')
    return observed


def check_unchanged(source: Path, copied: Path, before: dict) -> dict:
    source_after, copy_after = manifest(source), manifest(copied)
    if source_after != before or copy_after != before:
        _fail('source or copied cache changed during dataset fetch')
    return {'source_after': source_after, 'copied_after': copy_after}


def _mount_records(text: str) -> list[tuple[Path, set[str], list[str]]]:
    """Decode only mountinfo fields needed for fail-closed mount checks."""
    import re
    records = []
    for line in text.splitlines():
        left, sep, _ = line.partition(' - ')
        fields = left.split()
        if not sep or len(fields) < 6:
            _fail('malformed mountinfo')
        name = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), fields[4])
        records.append((Path(name), set(fields[5].split(',')), fields[6:]))
    return records


def validate_pipe_identity(payload: dict, parent_pid: int, parent_mount: str, parent_net: str,
                           child_mount: str, child_net: str, uid_map: str, gid_map: str) -> dict:
    """Bind child namespace claims to the live direct parent, not arbitrary strings."""
    if not isinstance(payload, dict) or payload.get('parent_pid') != parent_pid or parent_pid <= 1:
        _fail('namespace pipe is not bound to the live direct parent')
    if not isinstance(payload.get('parent_uid'), int) or payload['parent_uid'] <= 0 or \
       not isinstance(payload.get('parent_gid'), int) or payload['parent_gid'] < 0:
        _fail('parent uid or gid is invalid')
    if not isinstance(payload.get('parent_groups'), list) or \
            any(not isinstance(group, int) or group < 0 for group in payload['parent_groups']):
        _fail('parent group evidence invalid')
    for kind, parent, child in (('mnt', parent_mount, child_mount), ('net', parent_net, child_net)):
        if not re.fullmatch(kind + r':\[\d+\]', parent) or not re.fullmatch(kind + r':\[\d+\]', child):
            _fail('malformed namespace identity')
        if payload.get(kind + '_namespace') != parent or parent == child:
            _fail('caller namespace differs from live parent or child namespace is unchanged')
    for mapping, host_id, label in ((uid_map, payload['parent_uid'], 'uid'), (gid_map, payload['parent_gid'], 'gid')):
        try:
            rows = [tuple(int(x) for x in row.split()) for row in mapping.splitlines()]
        except (AttributeError, ValueError) as exc:
            raise ValueError('STOP: malformed user namespace mapping') from exc
        if rows != [(0, host_id, 1)]:
            _fail(f'{label} mapping is not bound to direct parent')
    return {'parent_pid': parent_pid, 'parent_uid': payload['parent_uid'], 'parent_gid': payload['parent_gid'],
            'parent_mount_namespace': parent_mount, 'parent_network_namespace': parent_net,
            'child_mount_namespace': child_mount, 'child_network_namespace': child_net,
            'uid_map': uid_map.strip(), 'gid_map': gid_map.strip(),
            'parent_groups': payload['parent_groups'], 'child_groups': os.getgroups()}


def read_pipe_attestation(fd: int, mount_fd: int, network_fd: int) -> dict:
    """Read a bounded pipe and compare inherited namespace kernel objects.

    The reviewed outer launcher opens its own namespace FDs before unshare.
    No /proc/<other-pid> path is used. All three handles close on every exit.
    """
    if len({fd, mount_fd, network_fd}) != 3 or min(fd, mount_fd, network_fd) <= 2:
        for handle in {fd, mount_fd, network_fd}:
            if handle > 2:
                try:
                    os.close(handle)
                except OSError:
                    pass
        _fail('namespace evidence descriptors are not distinct')
    try:
        if not stat.S_ISFIFO(os.fstat(fd).st_mode):
            _fail('namespace attestation fd is not a pipe')
        data = b''
        while True:
            block = os.read(fd, 4096)
            if not block:
                break
            data += block
            if len(data) > 8192:
                _fail('namespace attestation exceeds limit')
        payload = json.loads(data)
        parent = os.getppid()
        os.kill(parent, 0)
        links = [os.readlink(f'/proc/self/fd/{handle}') for handle in (mount_fd, network_fd)]
        stats = [os.fstat(handle) for handle in (mount_fd, network_fd)]
        for kind, link, st in zip(('mnt', 'net'), links, stats):
            match = re.fullmatch(kind + r':\[(\d+)\]', link)
            if match is None or int(match.group(1)) != st.st_ino:
                _fail('inherited descriptor is not the expected namespace object')
        child_mnt = os.readlink('/proc/self/ns/mnt')
        child_net = os.readlink('/proc/self/ns/net')
        for handle_stat, name in zip(stats, ('mnt', 'net')):
            own = os.stat('/proc/self/ns/' + name)
            if (handle_stat.st_dev, handle_stat.st_ino) == (own.st_dev, own.st_ino):
                _fail('inherited and child namespace kernel objects are identical')
        result = validate_pipe_identity(payload, parent, links[0], links[1], child_mnt, child_net,
                                       Path('/proc/self/uid_map').read_text(), Path('/proc/self/gid_map').read_text())
        result['parent_namespace_objects'] = [dict(dev=st.st_dev, ino=st.st_ino) for st in stats]
        result['parent_record_sha256'] = hashlib.sha256(data).hexdigest()
        return result
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError('STOP: unverified caller-bound namespace identity') from exc
    finally:
        for handle in (fd, mount_fd, network_fd):
            os.close(handle)


def protect_sources_readonly(paths: list[Path], namespace_attestation: dict) -> tuple[list[int], list[dict]]:
    """Return retained readonly bind-mount FDs, bound to source inode and mount ID.

    Only called after direct-parent namespace attestation in a private user,
    mount and network namespace. FD-pinned mount(2) behavior remains subject to
    independent Linux review; any unsupported operation raises STOP.
    """
    if os.getuid() != 0 or not namespace_attestation.get('child_mount_namespace'):
        _fail('not in a distinct root-mapped mount namespace')
    from r1.scripts.c3_mount_inode_candidate import bind_readonly_fd_pinned
    descriptors, proofs = [], []
    try:
        for path in paths:
            fd, proof = bind_readonly_fd_pinned(path, namespace_attestation)
            descriptors.append(fd)
            proofs.append(proof)
        return descriptors, proofs
    except BaseException:
        for fd in descriptors:
            os.close(fd)
        raise


def require_socket_denial() -> None:
    """Prove the current process's inherited filter kills socket creation.

    Forked probes inherit precisely the same seccomp filters as the dataset
    process. No task data or model is loaded in these probes.
    """
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    for family in (socket.AF_UNIX, socket.AF_INET, socket.AF_INET6):
        pid = os.fork()
        if pid == 0:
            try:
                socket.socket(family, socket.SOCK_STREAM)
            finally:
                os._exit(0)
        _, status = os.waitpid(pid, 0)
        if not os.WIFSIGNALED(status) or os.WTERMSIG(status) != signal.SIGSYS:
            _fail(f'current process seccomp did not kill socket family {family}')


def fetch_case(case_dir: Path, source_fds: list[int], mount_proofs: list[dict], expected: dict) -> dict:
    """Run one dataset-only case using only retained readonly mount descriptors."""
    import ctypes
    from r1.scripts.c3_mount_inode_candidate import (manifest_directory_nofollow,
            manifest_relative_nofollow, read_relative_nofollow, verify_retained_mount)
    case_dir = Path(case_dir)
    if not case_dir.is_absolute() or not case_dir.resolve().is_relative_to(Path('/tmp').resolve()):
        _fail('case directory outside local scratch')
    directory_nofollow(case_dir)
    if os.environ.get('HOME') != str(case_dir) or os.environ.get('TMPDIR') != str(case_dir):
        _fail('HOME and TMPDIR do not match future replay case')
    if len(source_fds) != 2 or len(mount_proofs) != 2 or len(set(source_fds)) != 2:
        _fail('two distinct readonly mount descriptors required')
    for fd, proof in zip(source_fds, mount_proofs):
        verify_retained_mount(fd, proof)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(21, 0, 0, 0, 0) != 2:
        _fail('network/Unix-socket seccomp filter is not active')
    require_socket_denial()
    marker = case_dir / 'dataset_fixture_started.json'
    with marker.open('x', encoding='utf-8') as stream:
        json.dump({'status': 'RUNNING', 'case': expected.get('case_id')}, stream)
    copied_fd = -1
    try:
        node, instance = expected.get('node_name'), expected.get('instance')
        if not isinstance(node, str) or not re.fullmatch(r'openml_[a-z0-9_]+', node) or \
           not isinstance(instance, str) or not re.fullmatch(re.escape(node) + r'__s\d+', instance):
            _fail('invalid source node or instance')
        node_path = Path('autoresearch_harness/nodes') / node
        dataset_bytes = read_relative_nofollow(source_fds[1], str(node_path / 'dataset.json'))
        benchmark_bytes = read_relative_nofollow(source_fds[1], str(node_path / 'benchmark.py'))
        dataset = validate_dataset_metadata(dataset_bytes, benchmark_bytes, expected)
        if expected.get('frame', {}).get('target_name') != dataset['target']:
            _fail('reviewed target differs from dataset.json target')
        source_relative = str(Path(instance) / 'node/data_cache')
        copied = case_dir / 'data_cache'
        before, copied_fd = copy_verified_cache_at(source_fds[0], source_relative, copied, expected['cache_sha256'])
        # Linux procfd path resolves to the retained local copy, not to an
        # untrusted source pathname. Independent numeric review is required.
        pinned_copy = f'/proc/self/fd/{copied_fd}'
        from sklearn.datasets import fetch_openml
        bunch = fetch_openml(data_id=dataset['dataset_id'], as_frame=True, parser='auto', data_home=pinned_copy)
        attrs = validate_frame(bunch, expected['frame'])
        details = getattr(bunch, 'details', None)
        if not isinstance(details, dict) or str(details.get('id')) != str(dataset['dataset_id']) or \
                details.get('name') != dataset['dataset_name']:
            _fail('loaded dataset metadata does not match reviewed dataset.json')
        source_after = manifest_relative_nofollow(source_fds[0], source_relative)
        copy_after = manifest_directory_nofollow(copied_fd)
        if source_after != before['source_before'] or copy_after != before['copied_before']:
            _fail('source or copied cache changed during dataset fetch')
        for fd, proof in zip(source_fds, mount_proofs):
            verify_retained_mount(fd, proof)
        from importlib import metadata
        versions = {n: metadata.version(n) for n in ('scikit-learn', 'numpy', 'scipy', 'pandas')}
        if versions != expected.get('library_versions'):
            _fail('actual dataset fixture library versions differ')
        result = {'status': 'PASS_ENGINEERING_ONLY', 'dataset': dataset, 'attributes': attrs,
                  'cache_manifests': {**before, 'source_after': source_after, 'copied_after': copy_after},
                  'mount_proofs': mount_proofs, 'historical_freeze': 'not available',
                  'dataset_json_sha256': hashlib.sha256(dataset_bytes).hexdigest(),
                  'benchmark_py_sha256': hashlib.sha256(benchmark_bytes).hexdigest(),
                  'uid': os.getuid(), 'gid': os.getgid(), 'groups': os.getgroups(),
                  'orchestrator_python': sys.executable, 'seccomp_socket_denial': 'verified in child probes',
                  'library_versions': versions,
                  'fixture_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'fetch': {'data_id': dataset['dataset_id'], 'as_frame': True, 'parser': 'auto',
                            'data_home': pinned_copy, 'local_copy': str(copied)}}
        (case_dir / 'dataset_fixture_result.json').write_text(json.dumps(result, sort_keys=True) + '\n')
        return result
    except BaseException as exc:
        (case_dir / 'dataset_fixture_STOP.json').write_text(json.dumps({'status': 'STOP', 'reason': str(exc)}) + '\n')
        raise
    finally:
        if copied_fd >= 0:
            os.close(copied_fd)


def supervise_guarded_child(command: list[str], case_dir: Path, env: dict, source_fds: tuple[int, ...] = ()) -> None:
    """Persist a fail-closed STOP if a sandboxed fixture exits or is SIGSYS-killed."""
    try:
        child = subprocess.run(command, env=env, capture_output=True, text=True, timeout=180,
                               stdin=subprocess.DEVNULL, close_fds=True, pass_fds=source_fds)
        (case_dir / 'dataset_fixture_stdout.txt').write_text(child.stdout)
        (case_dir / 'dataset_fixture_stderr.txt').write_text(child.stderr)
        if child.returncode != 0:
            _fail(f'dataset fixture exited or was killed: {child.returncode}')
        if not (case_dir / 'dataset_fixture_result.json').is_file():
            _fail('dataset fixture success record missing')
    except BaseException as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            (case_dir / 'dataset_fixture_stdout.txt').write_text(str(exc.stdout or ''))
            (case_dir / 'dataset_fixture_stderr.txt').write_text(str(exc.stderr or ''))
        (case_dir / 'dataset_supervisor_STOP.json').write_text(json.dumps({'status': 'STOP', 'reason': str(exc)}) + '\n')
        raise


def verify_fixture_review(repo: Path, commit: str, review_path: str, case_bytes: bytes, guard: Path):
    rel = Path(review_path)
    if rel.is_absolute() or '..' in rel.parts or rel.parts[:3] != ('docs', 'r1', 'reviews'):
        _fail('review path invalid')
    try:
        text = subprocess.check_output(['git', '-C', str(repo), 'show', f'{commit}:{review_path}'],
                                       text=True, timeout=30)
        subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', commit,
                        'origin/ops/c3-sweep1-classify-20261028'], check=True,
                       capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('STOP: fixture review not published on operations branch') from exc
    wanted = ('Verdict: ACCEPTED',
              'Cache-Fixture-SHA256: ' + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'Cache-Case-SHA256: ' + hashlib.sha256(case_bytes).hexdigest(),
              'Offline-Guard-SHA256: ' + hashlib.sha256(guard.read_bytes()).hexdigest(),
              'Mount-Inode-Guard-SHA256: ' + hashlib.sha256((repo / 'r1/scripts/c3_mount_inode_candidate.py').read_bytes()).hexdigest())
    if not all(line in text.splitlines() for line in wanted):
        _fail('published review does not bind fixture, guard and exact case')


def fixture_paths(case: dict) -> tuple[Path, Path, list[Path]]:
    roots = Path('/tmp/r1_sweep1_dwong_20261026/r1_c3_f7323c5a858490a81668/c3_append_only_summary_work/roots')
    batch = Path('/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw')
    node, instance = case.get('node_name'), case.get('instance')
    if not isinstance(node, str) or not re.fullmatch(r'openml_[a-z0-9_]+', node) or \
       not isinstance(instance, str) or not re.fullmatch(re.escape(node) + r'__s\d+', instance):
        _fail('invalid original node or instance identity')
    return roots / instance / 'node/data_cache', batch / 'autoresearch_harness/nodes' / node, [roots, batch]


def launch_bound_namespace(command: list[str], case_dir: Path, env: dict) -> None:
    """Capture this launcher's live identities and send them over a private pipe."""
    if os.getuid() == 0:
        _fail('fixture requires an unprivileged host caller')
    mount_fd = os.open('/proc/self/ns/mnt', os.O_RDONLY | os.O_CLOEXEC)
    try:
        network_fd = os.open('/proc/self/ns/net', os.O_RDONLY | os.O_CLOEXEC)
        try:
            _launch_with_namespace_handles(command, case_dir, env, mount_fd, network_fd)
        finally:
            os.close(network_fd)
    finally:
        os.close(mount_fd)


def _launch_with_namespace_handles(command: list[str], case_dir: Path, env: dict, mount_fd: int, network_fd: int) -> None:
    caller = {'parent_pid': os.getpid(), 'parent_uid': os.getuid(), 'parent_gid': os.getgid(),
              'mnt_namespace': os.readlink(f'/proc/self/fd/{mount_fd}'),
              'net_namespace': os.readlink(f'/proc/self/fd/{network_fd}'), 'parent_groups': os.getgroups()}
    if caller['mnt_namespace'] != os.readlink('/proc/self/ns/mnt') or \
       caller['net_namespace'] != os.readlink('/proc/self/ns/net'):
        _fail('namespace handles differ from caller identities')
    record = case_dir / 'dataset_namespace_parent.json'
    with record.open('x', encoding='utf-8') as stream:
        json.dump(caller, stream, sort_keys=True)
    reader, writer = os.pipe()
    process = None
    try:
        argv = ['unshare', '--user', '--map-root-user', '--mount', '--net', '--propagation', 'private', '--',
                *command, '--isolated-fd', str(reader), '--isolated-mount-fd', str(mount_fd),
                '--isolated-network-fd', str(network_fd)]
        process = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, close_fds=True,
                                   pass_fds=(reader, mount_fd, network_fd),
                                   start_new_session=True)
        os.close(reader)
        reader = -1
        payload = json.dumps(caller, sort_keys=True).encode()
        if os.write(writer, payload) != len(payload):
            _fail('namespace pipe write incomplete')
        os.close(writer)
        writer = -1
        try:
            stdout, stderr = process.communicate(timeout=240)
        except subprocess.TimeoutExpired:
            # The process group contains only this newly created synthetic fixture.
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            (case_dir / 'dataset_namespace_stdout.txt').write_text(stdout or '')
            (case_dir / 'dataset_namespace_stderr.txt').write_text(stderr or '')
            _fail('namespace fixture timed out; partial state retained')
        (case_dir / 'dataset_namespace_stdout.txt').write_text(stdout or '')
        (case_dir / 'dataset_namespace_stderr.txt').write_text(stderr or '')
        if process.returncode != 0:
            _fail(f'namespace fixture stopped or was killed: {process.returncode}')
        if not (case_dir / 'dataset_fixture_result.json').is_file():
            _fail('namespace fixture returned without a result')
    finally:
        if reader >= 0:
            os.close(reader)
        if writer >= 0:
            os.close(writer)
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-dir', required=True, type=Path)
    parser.add_argument('--case-record', required=True, type=Path)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--review-commit', required=True)
    parser.add_argument('--review-path', required=True)
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--isolated-fd', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--isolated-mount-fd', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--isolated-network-fd', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--roots-fd', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--batch-fd', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--mount-proof-sha256', help=argparse.SUPPRESS)
    args = parser.parse_args()
    case_dir = args.case_dir
    directory_nofollow(case_dir)
    if not case_dir.is_absolute() or not case_dir.is_relative_to(Path('/tmp')):
        _fail('case directory must be under /tmp')
    if os.environ.get('HOME') != str(case_dir) or os.environ.get('TMPDIR') != str(case_dir):
        _fail('fixture HOME and TMPDIR must be the actual case directory')
    if args.case_record.is_symlink() or not args.case_record.is_file() or \
       not args.case_record.resolve().is_relative_to(case_dir):
        _fail('case record must be a regular file in the new case directory')
    case_bytes = args.case_record.read_bytes()
    case = json.loads(case_bytes)
    source_cache, harness_node, roots = fixture_paths(case)
    repo = args.repo.resolve()
    guard = repo / 'r1/scripts/c3_replay_seccomp_candidate.py'
    if guard.is_symlink() or not guard.is_file() or Path(__file__).resolve().parents[2] != repo:
        _fail('fixture or guard is outside reviewed checkout')
    if args.child:
        if args.roots_fd is None or args.batch_fd is None or args.mount_proof_sha256 is None or \
                args.roots_fd <= 2 or args.batch_fd <= 2 or args.roots_fd == args.batch_fd:
            _fail('readonly source descriptor set incomplete')
        try:
            verify_fixture_review(repo, args.review_commit, args.review_path, case_bytes, guard)
            proof_path = case_dir / 'dataset_mount_proofs.json'
            if proof_path.is_symlink() or not proof_path.is_file():
                _fail('mount proof record missing')
            proof_bytes = proof_path.read_bytes()
            if hashlib.sha256(proof_bytes).hexdigest() != args.mount_proof_sha256:
                _fail('mount proof record differs from parent binding')
            fetch_case(case_dir, [args.roots_fd, args.batch_fd], json.loads(proof_bytes), case)
            return
        finally:
            os.close(args.roots_fd)
            os.close(args.batch_fd)
    try:
        verify_fixture_review(repo, args.review_commit, args.review_path, case_bytes, guard)
        base_args = ['--case-dir', str(case_dir), '--case-record', str(args.case_record), '--repo', str(repo),
                     '--review-commit', args.review_commit, '--review-path', args.review_path]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
        if args.isolated_fd is None:
            if args.isolated_mount_fd is not None or args.isolated_network_fd is not None:
                _fail('namespace descriptor set incomplete')
            command = [sys.executable, '-B', str(Path(__file__).resolve()), *base_args]
            launch_bound_namespace(command, case_dir, env)
        else:
            if args.isolated_mount_fd is None or args.isolated_network_fd is None:
                _fail('namespace descriptor set incomplete')
            attestation = read_pipe_attestation(args.isolated_fd, args.isolated_mount_fd, args.isolated_network_fd)
            parent_record = case_dir / 'dataset_namespace_parent.json'
            if parent_record.is_symlink() or hashlib.sha256(parent_record.read_bytes()).hexdigest() != attestation['parent_record_sha256']:
                _fail('namespace pipe does not match parent evidence record')
            with (case_dir / 'dataset_namespace_child.json').open('x', encoding='utf-8') as stream:
                json.dump(attestation, stream, sort_keys=True)
            source_fds, proofs = protect_sources_readonly(roots, attestation)
            try:
                proof_path = case_dir / 'dataset_mount_proofs.json'
                with proof_path.open('x', encoding='utf-8') as stream:
                    json.dump(proofs, stream, sort_keys=True)
                proof_sha = hashlib.sha256(proof_path.read_bytes()).hexdigest()
                command = [sys.executable, '-I', '-S', str(guard), sys.executable, '-B', str(Path(__file__).resolve()),
                           '--child', '--roots-fd', str(source_fds[0]), '--batch-fd', str(source_fds[1]),
                           '--mount-proof-sha256', proof_sha, *base_args]
                supervise_guarded_child(command, case_dir, env, tuple(source_fds))
            finally:
                for fd in source_fds:
                    os.close(fd)
    except BaseException as exc:
        stop_name = 'dataset_namespace_STOP.json' if args.isolated_fd is not None else 'dataset_launcher_STOP.json'
        with (case_dir / stop_name).open('x', encoding='utf-8') as stream:
            json.dump({'status': 'STOP', 'reason': str(exc)}, stream)
        raise


if __name__ == '__main__':
    raise SystemExit('STOP: recovered fixture is not authorized for execution')
