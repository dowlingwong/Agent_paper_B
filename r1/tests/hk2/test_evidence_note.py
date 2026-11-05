"""Synthetic temporary-repository tests; no Slurm, model, or host work."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'hk2'))
import hk2_evidence_note as check


class EvidenceNoteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.manifest = {'schema': 'hk2_job/v1', 'kind': 'evidence', 'phase': 'HK6', 'argv': ['fixture']}
        self.raw = json.dumps(self.manifest).encode()
        self.note = {'schema': 'hk2_evidence_authorization/v1', 'author': 'Dowling Wong',
                     'approved': True, 'phase': 'HK6', 'manifest_sha256': hashlib.sha256(self.raw).hexdigest(),
                     'node_count': 3, 'audit_k': 10, 'budget_gpu_hours': 120}
        self.write_and_commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.DEVNULL)

    def write_and_commit(self):
        (self.root / 'manifest.json').write_bytes(self.raw)
        (self.root / 'note.json').write_text(json.dumps(self.note))
        self.git('add', 'manifest.json', 'note.json')
        self.git('commit', '-qm', 'fixture', '--allow-empty')

    def verify(self, **kwargs):
        return check.verify_note(self.root, 'note.json', 'manifest.json', 'HK6',
                                 max_nodes=8, max_budget_gpu_hours=300, **kwargs)

    def test_exact_committed_binding(self):
        result = self.verify()
        self.assertEqual(result['head'], self.git('rev-parse', 'HEAD').decode().strip())
        self.assertEqual(result['manifest_sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(result['node_count'], 3)

    def test_dirty_or_untracked_checkout_stops(self):
        (self.root / 'note.json').write_text('{}')
        with self.assertRaisesRegex(check.EvidenceNoteError, 'clean'):
            self.verify()
        self.git('checkout', '--', 'note.json')
        (self.root / 'unknown').write_text('fixture')
        with self.assertRaisesRegex(check.EvidenceNoteError, 'clean'):
            self.verify()

    def test_bad_note_fields_and_bounds_stop(self):
        cases = [('author', 'someone else'), ('approved', False), ('approved', 1),
                 ('phase', 'HK7'), ('manifest_sha256', '0' * 64),
                 ('node_count', True), ('node_count', 0), ('node_count', 9),
                 ('audit_k', True), ('audit_k', 7), ('budget_gpu_hours', 0),
                 ('budget_gpu_hours', 301), ('budget_gpu_hours', float('nan'))]
        original = dict(self.note)
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.note = dict(original, **{key: value})
                self.write_and_commit()
                with self.assertRaises(check.EvidenceNoteError):
                    self.verify()

    def test_wrong_manifest_phase_and_kind_stop(self):
        for key, value in [('phase', 'HK7'), ('kind', 'engineering')]:
            with self.subTest(key=key):
                self.raw = json.dumps(dict(self.manifest, **{key: value})).encode()
                self.note['manifest_sha256'] = hashlib.sha256(self.raw).hexdigest()
                self.write_and_commit()
                with self.assertRaises(check.EvidenceNoteError):
                    self.verify()

    def test_symlink_and_untracked_paths_stop(self):
        (self.root / 'link').symlink_to('note.json')
        self.git('add', 'link')
        self.git('commit', '-qm', 'symlink')
        with self.assertRaisesRegex(check.EvidenceNoteError, 'symlink'):
            check.verify_note(self.root, 'link', 'manifest.json', 'HK6', max_nodes=8, max_budget_gpu_hours=300)
        with self.assertRaises(check.EvidenceNoteError):
            check.verify_note(self.root, '../note.json', 'manifest.json', 'HK6', max_nodes=8, max_budget_gpu_hours=300)

    def test_limits_must_be_explicit_and_well_typed(self):
        for nodes, budget in [(True, 300), (0, 300), (8, True), (8, float('inf')), (8, 0)]:
            with self.subTest(nodes=nodes, budget=budget):
                with self.assertRaises(check.EvidenceNoteError):
                    check.verify_note(self.root, 'note.json', 'manifest.json', 'HK6', max_nodes=nodes, max_budget_gpu_hours=budget)

    def test_duplicate_json_keys_are_refused(self):
        original = json.dumps(self.note)
        (self.root / 'note.json').write_text(original[:-1] + ', "approved": true}')
        self.git('add', 'note.json')
        self.git('commit', '-qm', 'duplicate field')
        with self.assertRaisesRegex(check.EvidenceNoteError, 'duplicate'):
            self.verify()
