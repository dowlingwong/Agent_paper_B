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
        self.cwd=self.repo
        self.mode=b'100644'

    def command(self, argv, **kwargs):
        if 'rev-parse' in argv: return self.heads.pop(0)+'\n'
        if 'status' in argv: return self.dirty
        if 'ls-tree' in argv: return self.mode+b' blob '+b'a'*40+b'\t'+argv[-1].encode()+b'\0'
        if 'show' in argv: return self.blob
        raise AssertionError(argv)

    def verify(self, path=None, cfg=None):
        with patch.object(runtime,'REPO',self.repo), \
             patch.object(runtime.subprocess,'check_output',side_effect=self.command), \
             patch.object(Path,'cwd',return_value=self.cwd), \
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

    def test_non_checkout_cwd_refused(self):
        self.cwd=Path('/different')
        with self.assertRaises(runtime.PreparationStop): self.verify()

    def test_committed_symlink_mode_refused(self):
        self.mode=b'120000'
        with self.assertRaises(runtime.PreparationStop): self.verify()

    def test_authorization_head_mismatch_stops_before_output(self):
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.cfg={'dryrun':False}
        runner.rule={'version':'x5_rule/v2'}
        runner.rule_sha='f'*64
        runner.b1_config_head='a'*40
        with patch.object(runtime,'require_committed_b1_config',return_value='a'*40), \
             patch.object(runtime,'require_committed_b1_registry'), \
             patch.object(runtime,'author_gate',return_value='b'*40):
            runner.registry_path=Path('/fake/registry');runner.registry={}
            with self.assertRaises(runtime.PreparationStop): runner.start('b1')

    def test_direct_start_rechecks_config_before_author_gate(self):
        runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.cfg={'dryrun':False}
        runner.rule={'version':'x5_rule/v2'}
        runner.b1_config_head='a'*40
        with patch.object(runtime,'require_committed_b1_config',side_effect=runtime.PreparationStop('STOP')), \
             patch.object(runtime,'author_gate') as gate:
            with self.assertRaises(runtime.PreparationStop): runner.start('b1')
            gate.assert_not_called()


class RegistryAuthorityTest(unittest.TestCase):
    def setUp(self):
        self.repo=Path('/fake-checkout')
        self.head='a'*40
        self.mode=b'100644'
        self.cfg={'registry':'r1/exam/registry.yaml'}
        self.path=self.repo/'r1/exam/registry.yaml'
        self.blob=b'candidates: []\nsoftware_anchors: []\n'
        self.disk=self.blob

    def command(self, argv, **kwargs):
        if 'ls-tree' in argv: return self.mode+b' blob '+b'a'*40+b'\t'+argv[-1].encode()+b'\0'
        if 'show' in argv: return self.blob
        raise AssertionError(argv)

    def check(self, path=None, registry=None):
        with patch.object(runtime,'REPO',self.repo), \
             patch.object(runtime.subprocess,'check_output',side_effect=self.command), \
             patch.object(Path,'resolve',lambda p,**kw:p), \
             patch.object(Path,'read_bytes',lambda p:self.disk):
            return runtime.require_committed_b1_registry(self.cfg,self.head,selected_path=path,selected_registry=registry)

    def test_registry_path_is_checkout_anchored(self):
        self.assertEqual(self.check(),self.path)

    def test_direct_override_refused(self):
        with self.assertRaises(runtime.PreparationStop): self.check(path=Path('/different/registry.yaml'))

    def test_constructor_rejects_override_before_registry_read(self):
        cfg={**self.cfg,'dryrun':False}
        with patch.object(runtime,'host_check'), \
             patch.object(runtime,'read_registry') as read, \
             patch.object(Path,'resolve',lambda p,**kw:p):
            with self.assertRaises(runtime.PreparationStop):
                runtime.ExamRunner(cfg,'/fake-out',registry_path='/different/registry.yaml',b1_config_head=self.head)
            read.assert_not_called()

    def test_registry_file_tampering_refused(self):
        self.disk=b'candidates: [changed]\n'
        with self.assertRaises(runtime.PreparationStop): self.check()

    def test_registry_object_mutation_refused(self):
        with self.assertRaises(runtime.PreparationStop): self.check(registry={'candidates':['changed']})

    def test_registry_git_symlink_refused(self):
        self.mode=b'120000'
        with self.assertRaises(runtime.PreparationStop): self.check()


if __name__=='__main__': unittest.main()
