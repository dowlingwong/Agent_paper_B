"""Read only lstat metadata of fixed B1 anchor files; never read file contents.

The three names/nodes/seeds are fixed to the accepted B1 configuration and
metadata cannot establish audit outcomes. No writes or gate computation.
"""
import os
import stat
import sys
from datetime import datetime, timezone

ROOT = '/home/dowling/exam-x/work/b1_6835_20261108_a'
ANCHORS = ('random_valid', 'scripted', 'qwen25_coder_7b')
NODES = ('digits_mlp', 'openml_credit_approval', 'openml_ionosphere')
SEEDS = (9001, 9002, 9003, 9004)
ROOT_FILES = ('job.json', 'campaign_manifest.json', 'post_check.json',
              'runner.log', 'root_trials.jsonl', 'root_events.jsonl', 'audit_cache.json')


def _open_chain(parts):
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            if not part or part in ('.', '..') or '/' in part:
                raise ValueError('invalid component')
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


def _file_metadata(fd, name, label):
    try:
        st = os.stat(name, dir_fd=fd, follow_symlinks=False)
        kind = 'REGULAR' if stat.S_ISREG(st.st_mode) else 'NONREGULAR_NOT_CHECKABLE'
        print('FILE', label, kind, 'bytes', st.st_size, 'uid', st.st_uid,
              'dev', st.st_dev, 'ino', st.st_ino, 'mtime_ns', st.st_mtime_ns)
        return kind == 'REGULAR'
    except OSError as exc:
        print('FILE', label, 'NOT_CHECKABLE', type(exc).__name__, 'errno', exc.errno)
        return False


def inspect(root, anchors, nodes, seeds):
    if not os.path.isabs(root) or '..' in root.split('/'):
        raise ValueError('absolute fixed-root path required')
    base = tuple(part for part in root.split('/') if part)
    root_count = 0
    summary_count = 0
    for anchor in anchors:
        try:
            fd = _open_chain(base + (anchor,))
            try:
                summary_count += int(_file_metadata(fd, 'b1_manifest.json', anchor + '/b1_manifest.json'))
            finally:
                os.close(fd)
        except (OSError, ValueError) as exc:
            print('DIRECTORY', anchor, 'NOT_CHECKABLE', type(exc).__name__)
        for node in nodes:
            for seed in seeds:
                label = '%s/b1/off/%s__s%d' % (anchor, node, seed)
                try:
                    fd = _open_chain(base + (anchor, 'b1', 'off', '%s__s%d' % (node, seed)))
                    try:
                        root_count += 1
                        for name in ROOT_FILES:
                            _file_metadata(fd, name, label + '/' + name)
                    finally:
                        os.close(fd)
                except (OSError, ValueError) as exc:
                    print('DIRECTORY', label, 'NOT_CHECKABLE', type(exc).__name__)
    print('METADATA_SUMMARY', 'expected_roots', len(anchors)*len(nodes)*len(seeds),
          'accessible_root_directories', root_count, 'regular_candidate_manifests', summary_count)
    print('AUDIT_FAILURE_COUNTS NOT_CHECKABLE: no audit or ledger content read')
    print('COMPARISON_VALUES NOT_CHECKABLE: no gate or numeric analysis run')


def main():
    print('UTC', datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    try:
        inspect(ROOT, ANCHORS, NODES, SEEDS)
    except (OSError, ValueError) as exc:
        print('STOP: metadata inspection failed', type(exc).__name__, file=sys.stderr)
        return 1
    print('METADATA_CAPTURE_COMPLETE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
