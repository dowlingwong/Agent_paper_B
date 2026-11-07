"""Pure in-memory checks for changed fixture-root mode."""
import runpy
import stat
from types import SimpleNamespace
from unittest import TestCase, main

helpers=runpy.run_path('r1/tests/b1_preserved_tmp_memory/test_fixture_helpers.py')


class RootMode(TestCase):
    def test_each_root_view_mode_is_rechecked(self):
        for changed in ('fstat','lstat'):
            ns,fake=helpers['setup_fake']()
            fd,identity=ns['_open_empty_root']('/root/private')
            bad=SimpleNamespace(st_dev=4,st_ino=5,st_uid=42,st_mode=stat.S_IFDIR | 0o755)
            getattr(fake,changed).return_value=bad
            with self.assertRaises(RuntimeError): ns['_create_fixture_dir']('/root/private',fd,identity)
            fake.mkdir.assert_not_called()


if __name__=='__main__': main()
