"""Pure in-memory checks of extracted helpers; no pytest execution or real files."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import Mock
import stat


source = Path('r1/tests/b1_preserved_tmp_plugin.py').read_text()
tree = ast.parse(source)
names = {'_identity', '_open_empty_root', '_create_fixture_dir'}
module = ast.fix_missing_locations(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]))
info = SimpleNamespace(st_dev=4, st_ino=5, st_uid=42, st_mode=stat.S_IFDIR | 0o700)


def setup_fake():
    fake = SimpleNamespace(
        O_RDONLY=0, O_DIRECTORY=1, O_NOFOLLOW=2, O_CLOEXEC=4,
        path=SimpleNamespace(isabs=Mock(return_value=True), normpath=Mock(side_effect=lambda p:p), realpath=Mock(side_effect=lambda p:p)),
        open=Mock(return_value=7), fstat=Mock(return_value=info), lstat=Mock(return_value=info),
        getuid=Mock(return_value=42), listdir=Mock(return_value=[]), close=Mock(), mkdir=Mock())
    namespace={'os':fake,'stat':stat,'uuid':SimpleNamespace(uuid4=lambda:SimpleNamespace(hex='fixed')),'Path':Path}
    exec(compile(module, '<fixture-helpers>', 'exec'), namespace)
    return namespace, fake


class PreservationHelpers(TestCase):
    def test_fresh_root_and_exclusive_directory(self):
        ns, fake=setup_fake()
        fd, identity=ns['_open_empty_root']('/root/private')
        self.assertEqual(ns['_create_fixture_dir']('/root/private',fd,identity),Path('/root/private/test_fixed'))
        fake.mkdir.assert_called_once_with('test_fixed',mode=0o700,dir_fd=7)
        fake.close.assert_not_called()

    def test_nonempty_wrong_owner_and_changed_root_refuse(self):
        for change in ('nonempty','owner','changed'):
            ns, fake=setup_fake()
            if change=='nonempty': fake.listdir.return_value=['old']
            elif change=='owner': fake.getuid.return_value=43
            else: fake.lstat.return_value=SimpleNamespace(st_dev=4,st_ino=6,st_uid=42,st_mode=stat.S_IFDIR|0o700)
            with self.assertRaises(RuntimeError): ns['_open_empty_root']('/root/private')
            fake.close.assert_called_once_with(7)
            fake.mkdir.assert_not_called()

    def test_symlink_ancestor_rejected_and_collision_not_retried(self):
        ns,fake=setup_fake()
        fake.path.realpath.side_effect=None
        fake.path.realpath.return_value='/elsewhere'
        with self.assertRaises(RuntimeError): ns['_open_empty_root']('/root/private')
        fake.open.assert_not_called()
        fake.path.realpath.side_effect=None
        fake.path.realpath.return_value='/root/private'
        fd,identity=ns['_open_empty_root']('/root/private')
        fake.mkdir.side_effect=FileExistsError('collision')
        with self.assertRaises(FileExistsError): ns['_create_fixture_dir']('/root/private',fd,identity)
        self.assertEqual(fake.mkdir.call_count,1)


if __name__=='__main__': main()
