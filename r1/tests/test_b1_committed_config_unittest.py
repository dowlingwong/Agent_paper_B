"""In-memory checks for the B1 committed-config preflight; no fixture files."""
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from r1.exam import runtime


class ConfigAuthorityTest(unittest.TestCase):
    def setUp(self):
        self.repo=Path('/fake-checkout')
        self.path=self.repo/runtime.B1_CONFIG_REL
        self.head='a'*40
        self.cfg={'root_timeout_seconds':43200,'dryrun':False}
        self.blob=json.dumps(self.cfg).encode()
        self.disk=self.blob
        self.heads=[self.head,self.head]
        self.dirty=''
        self.symlink=False

    def command(self, argv, **kwargs):
        if 'rev-parse' in argv: return self.heads.pop(0)+'\n'
        if 'status' in argv: return self.dirty
        if 'show' in argv: return self.blob
        raise AssertionError(argv)

    def verify(self, path=None, cfg=None):
        with patch.object(runtime,'REPO',self.repo), \
             patch.object(runtime.subprocess,'check_output',side_effect=self.command), \
             patch.object(Path,'resolve',lambda p,**kw:p), \
             patch.object(Path,'is_symlink',lambda p:self.symlink), \
             patch.object(Path,'read_bytes',lambda p:self.disk):
            return runtime.require_committed_b1_config(path or self.path,self.cfg if cfg is None else cfg)

    def test_matching_config_and_head(self):
        self.assertEqual(self.verify(),self.head)

    def test_external_path_refused(self):
        with self.assertRaises(runtime.PreparationStop): self.verify(Path('/tmp/external.json'))

    def test_different_loaded_config_refused(self):
        with self.assertRaises(runtime.PreparationStop): self.verify(cfg={'root_timeout_seconds':1,'dryrun':False})

    def test_changed_bytes_refused(self):
        self.disk=b'{}'
        with self.assertRaises(runtime.PreparationStop): self.verify()

    def test_dirty_head_refused(self):
        self.dirty='?? another-file\n'
        with self.assertRaises(runtime.PreparationStop): self.verify()

    def test_head_change_refused(self):
        self.heads=[self.head,'b'*40]
        with self.assertRaises(runtime.PreparationStop): self.verify()

    def test_symlink_refused(self):
        self.symlink=True
        with self.assertRaises(runtime.PreparationStop): self.verify()

    def test_authorization_head_mismatch_stops_before_output(self):
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.cfg={'dryrun':False}
        runner.rule={'version':'x5_rule/v2'}
        runner.rule_sha='f'*64
        runner.b1_config_head='a'*40
        with patch.object(runtime,'author_gate',return_value='b'*40):
            with self.assertRaises(runtime.PreparationStop): runner.start('b1')


if __name__=='__main__': unittest.main()
