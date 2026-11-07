"""Mock-only tests of probe directory binding; never opens site paths."""
import ast
import os
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPT = Path(__file__).with_name('probe.sh')
source = SCRIPT.read_text().split("python3 -I -S -B - <<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
tree = ast.parse(source)
names = {'identity', 'verify_directory_chain', 'open_trusted_lock_directory', 'require_no_markers'}
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in functions} == names
code = compile(ast.Module(body=functions, type_ignores=[]), str(SCRIPT), 'exec')


def info(inode, uid, mode=stat.S_IFDIR | 0o755):
    return SimpleNamespace(st_dev=10, st_ino=inode, st_uid=uid, st_nlink=2, st_mode=mode)


class FakeOS:
    O_RDONLY = os.O_RDONLY
    O_DIRECTORY = os.O_DIRECTORY
    O_NOFOLLOW = os.O_NOFOLLOW
    O_CLOEXEC = os.O_CLOEXEC
    O_CREAT = os.O_CREAT

    def __init__(self):
        self.names = {(None, '/'): info(1, 0), (10, 'home'): info(2, 0),
                      (11, 'dowling'): info(3, 1011), (12, 'r1_locks'): info(4, 1011)}
        self.opened = {}
        self.closed = []
        self.calls = []
        self.next_fd = 10

    def getuid(self):
        return 1011

    def stat(self, name, *, dir_fd=None, follow_symlinks=True):
        self.calls.append(('stat', name, dir_fd, follow_symlinks))
        if (dir_fd, name) not in self.names:
            raise FileNotFoundError(name)
        return self.names[(dir_fd, name)]

    def open(self, name, flags, *, dir_fd=None):
        self.calls.append(('open', name, dir_fd, flags))
        if flags & self.O_CREAT or not flags & self.O_NOFOLLOW or not flags & self.O_DIRECTORY:
            raise AssertionError('unsafe directory flags')
        source = self.names[(dir_fd, name)]
        if not stat.S_ISDIR(source.st_mode):
            raise OSError('not a directory')
        fd = self.next_fd
        self.next_fd += 1
        self.opened[fd] = info(source.st_ino, source.st_uid, source.st_mode)
        return fd

    def fstat(self, fd):
        return self.opened[fd]

    def close(self, fd):
        self.closed.append(fd)


class ProbeDirectoryBindingTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeOS()
        self.g = {'os': self.fake, 'stat': stat}
        exec(code, self.g)

    def test_opens_entire_chain_relative_and_without_creation(self):
        chain = self.g['open_trusted_lock_directory']()
        self.assertEqual([entry[1] for entry in chain], ['/', 'home', 'dowling', 'r1_locks'])
        self.assertEqual([(x[1], x[2]) for x in self.fake.calls if x[0] == 'open'],
                         [('/', None), ('home', 10), ('dowling', 11), ('r1_locks', 12)])
        self.g['require_no_markers'](chain[-1][0])

    def test_symlink_ancestor_refused_before_follow(self):
        self.fake.names[(11, 'dowling')] = info(3, 1011, stat.S_IFLNK | 0o777)
        with self.assertRaisesRegex(RuntimeError, 'unsafe lock directory component'):
            self.g['open_trusted_lock_directory']()
        self.assertEqual(self.fake.closed, [11, 10])
        self.assertNotIn('dowling', [x[1] for x in self.fake.calls if x[0] == 'open'])

    def test_wrong_owner_and_replaced_component_fail_closed(self):
        self.fake.names[(12, 'r1_locks')] = info(4, 9999)
        with self.assertRaisesRegex(RuntimeError, 'unsafe lock directory component'):
            self.g['open_trusted_lock_directory']()
        self.assertEqual(self.fake.closed, [12, 11, 10])
        self.fake = FakeOS()
        self.g['os'] = self.fake
        chain = self.g['open_trusted_lock_directory']()
        self.fake.names[(12, 'r1_locks')] = info(77, 1011)
        with self.assertRaisesRegex(RuntimeError, 'ancestor identity changed'):
            self.g['verify_directory_chain'](chain)

    def test_dangling_marker_symlink_and_inaccessible_marker_refused(self):
        chain = self.g['open_trusted_lock_directory']()
        lockdir = chain[-1][0]
        self.fake.names[(lockdir, 'trackx_evidence.active')] = info(80, 1011, stat.S_IFLNK | 0o777)
        with self.assertRaisesRegex(RuntimeError, 'active or ambiguous marker'):
            self.g['require_no_markers'](lockdir)
        original = self.fake.stat
        def blocked(name, **kwargs):
            if name == 'trackx_evidence.active':
                raise PermissionError(name)
            return original(name, **kwargs)
        self.fake.stat = blocked
        with self.assertRaises(PermissionError):
            self.g['require_no_markers'](lockdir)


if __name__ == '__main__':
    unittest.main()
