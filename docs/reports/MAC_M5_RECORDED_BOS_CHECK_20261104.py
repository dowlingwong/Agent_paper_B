"""Read-only BOS identity consistency check on a copied O1 t7j10 bundle.

Usage: python3 MAC_M5_RECORDED_BOS_CHECK_20261104.py /path/to/j10
This checks recorded wire responses and row evidence, not the pinned tokenizers.
AI-assisted (Codex). No network, model, or server calls.
"""
import base64
import collections
import hashlib
import json
import sys
from pathlib import Path

base = Path(sys.argv[1])
rows = json.loads((base / 'stage_a_table.json').read_text())['rows']
total_token = total_byte = 0
for row in rows:
    if row.get('software_anchor'):
        continue
    name = row['candidate']
    root = base / name / 'stage-a' / '32768'
    events = collections.defaultdict(dict)
    for line in (root / 'd3_non_generation_calls.jsonl').read_text().splitlines():
        event = json.loads(line)
        kind = event['event']
        if kind in events[event['sequence']]:
            raise ValueError('duplicate event')
        events[event['sequence']][kind] = event
    applies, tokens = [], {}
    for seq, event in sorted(events.items()):
        req = event.get('request_attempt', {})
        if req.get('route') not in ('/apply-template', '/tokenize'):
            continue
        res = event['response']
        body = json.loads(req['request_body'])
        raw = base64.b64decode(res['response_body_b64'], validate=True)
        if hashlib.sha256(raw).hexdigest() != res['response_body_sha256']:
            raise ValueError('response digest mismatch')
        reply = json.loads(raw)
        if req['route'] == '/apply-template':
            applies.append((seq, reply['prompt']))
        else:
            tokens[seq] = (body, reply['tokens'])
    evidence = row['template_check_evidence']
    if len(applies) != 55 or len(evidence) != 55:
        raise ValueError('incomplete template checks')
    token_count = byte_count = mismatch = 0
    for (seq, actual), entry in zip(applies, evidence):
        if entry['method'] == 'byte':
            if not entry['byte_equal']:
                raise ValueError('inconsistent byte evidence')
            byte_count += 1
        elif entry['method'] == 'token':
            body, ids = tokens[seq + 1]
            if body != {'content': actual, 'add_special': True} or not isinstance(ids, list) or not ids:
                raise ValueError('fallback binding invalid')
            if not entry['tokens_equal'] or not entry['server_tokenize']:
                raise ValueError('unsuccessful token evidence')
            token_count += 1
            mismatch += ids[0] != entry['prefix_token_id']
        else:
            raise ValueError('unknown comparison method')
    print(name, 'byte_checks', byte_count, 'token_checks', token_count, 'first_id_mismatches', mismatch)
    if mismatch:
        raise ValueError('recorded BOS ID mismatch')
    total_byte += byte_count
    total_token += token_count
print('TOTAL', 'byte_checks', total_byte, 'token_checks', total_token)
