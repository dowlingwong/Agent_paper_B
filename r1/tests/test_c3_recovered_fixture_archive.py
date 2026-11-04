"""Recovered unsafe candidates are stored only as non-importable data."""
import base64
import hashlib
import json
from pathlib import Path


def test_archive_decodes_to_identical_recorded_blobs():
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / 'docs/r1/recovery/c3-fixtures-20261031/source_data_manifest.json').read_text())
    assert len(manifest['entries']) == 11
    recovered = {}
    for entry in manifest['entries']:
        data_path = root / entry['data_path']
        assert data_path.suffix == '.b64'
        data = base64.b64decode(data_path.read_bytes(), validate=False)
        assert len(data) == entry['bytes']
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry['git_blob_sha1']
        recovered[entry['previous_path']] = entry['git_blob_sha1']
    assert recovered['docs/r1/recovery/c3-fixtures-20261031/dirfd/c3_cache_offline_fixture_00d.py'] == (
        '5afae90e29b5f7dad163fc6322acd86ab970db63')
    assert not list((root / 'docs/r1/recovery/c3-fixtures-20261031').rglob('*.py'))
