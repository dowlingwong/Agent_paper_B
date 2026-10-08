import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from release_provenance import verify_manifest


class ProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        self.package = Path(self.tmp.name) / 'package'
        self.package.mkdir()
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.PIPE).decode().strip()
        self.git = git
        git('init')
        pin = self.root / 'protocols/paper_a/RELEASE_PIN.yaml'
        pin.parent.mkdir(parents=True)
        pin.write_text('status: candidate\n')
        (self.root / 'sample.txt').write_text('committed evidence\n')
        (self.package / 'sample.txt').write_bytes((self.root / 'sample.txt').read_bytes())
        git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'fixture')
        payload = (self.root / 'sample.txt').read_bytes()
        self.manifest = dict(source_commit=git('rev-parse', 'HEAD'), source_commit_dirty=False,
                             file_count=1, files=[dict(path='sample.txt', bytes=len(payload),
                             sha256=hashlib.sha256(payload).hexdigest())])

    def test_accepts_matching_committed_package(self):
        self.assertEqual(verify_manifest(self.root, self.package, self.manifest), [])

    def test_rejects_package_tampering_even_with_updated_manifest(self):
        data = b'changed evidence\n'
        (self.package / 'sample.txt').write_bytes(data)
        self.manifest['files'][0].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        self.assertTrue(verify_manifest(self.root, self.package, self.manifest))

    def test_rejects_dirty_provenance_and_wrong_count(self):
        self.manifest.update(source_commit_dirty=True, file_count=2)
        self.assertEqual(len(verify_manifest(self.root, self.package, self.manifest)), 2)

    def test_rejects_unmanifested_content(self):
        (self.package / 'private.txt').write_text('extra')
        self.assertTrue(verify_manifest(self.root, self.package, self.manifest))

    def test_rejects_duplicate_or_unsafe_paths(self):
        self.manifest['files'][0]['path'] = '../sample.txt'
        self.assertTrue(verify_manifest(self.root, self.package, self.manifest))

if __name__ == '__main__':
    unittest.main()
