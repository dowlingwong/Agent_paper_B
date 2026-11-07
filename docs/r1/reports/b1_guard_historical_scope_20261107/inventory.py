"""Read-only metadata inventory of the 54 Q2 frozen proposal-event ledgers.

No training metric or evaluation audit value is parsed or emitted. This is not
an estimate of historical guard failures. It cannot reconstruct missing fields.
"""
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

source_repo, reference = sys.argv[1:]
reference_bytes = Path(reference).read_bytes()
assert hashlib.sha256(reference_bytes).hexdigest() == '84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd'
ref = json.loads(reference_bytes)
revision = ref['source_commit']
tree = subprocess.check_output(['git', '-C', source_repo, 'rev-parse', revision + ':' + ref['source']], text=True).strip()
assert tree == ref['source_tree']
counts = collections.Counter()
event_keys = collections.Counter()
payload_keys = collections.Counter()
markers = ('structured_edit', 'objective', 'target_files', 'old_value', 'new_value')
for node, campaigns in sorted(ref['campaigns'].items()):
    assert len(campaigns) == 18
    for campaign in campaigns:
        path = campaign['path']
        assert path.endswith('/root_events.jsonl') and path.startswith(ref['source'] + '/')
        blob = subprocess.check_output(['git', '-C', source_repo, 'show', revision + ':' + path])
        assert hashlib.sha256(blob).hexdigest() == campaign['sha256']
        counts['verified_ledgers'] += 1
        for line in blob.splitlines():
            # Skip all other event types before JSON decoding; do not parse metrics.
            if b'proposal_created' not in line:
                continue
            row = json.loads(line)
            if row.get('event_type') != 'proposal_created':
                continue
            counts[node] += 1
            event_keys.update(row.keys())
            payload = row['payload']
            assert isinstance(payload, dict)
            payload_keys.update(payload.keys())
            value = payload.get('summary')
            counts['summary_type_' + type(value).__name__] += 1
            if isinstance(value, str):
                for marker in markers:
                    counts['summary_contains_' + marker] += int(marker in value)
print(json.dumps({'source_commit': revision, 'source_tree': tree, 'q2_reference_sha256': hashlib.sha256(reference_bytes).hexdigest(), 'counts': dict(sorted(counts.items())), 'event_keys': dict(sorted(event_keys.items())), 'payload_keys': dict(sorted(payload_keys.items())), 'interpretation': 'metadata inventory only; not a historical guard-failure rate'}, indent=2, sort_keys=True))
