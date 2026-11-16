# Read-only capture of accepted Stage A footprint fields

**Candidate for independent review, not executed.** The production B1 `stage_a_pass_set` and observer use the two exact Stage A tables whose hashes were accepted in O1. Individual footprint numbers are not present in the local O1 summary. This bounded read-only command obtains only the table hashes and non-sensitive qualification fields; it does not use GPU, load a model, write remote files, mutate Stage A, read evaluation audit values or authorize B1. Independently review the command before one use, and first perform the author-required fresh applicable STATUS/lock/process census. Preserve the private local capture and independently review it. No result may be inferred from this proposal.

```bash
set -u
umask 077
OUT=$(mktemp -d /private/tmp/paper-b-stagea-footprints-20261107.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'python3 -I -B -' > "$OUT/fields.jsonl" 2> "$OUT/stderr.txt" <<'PY'
import hashlib, json, math
from pathlib import Path

sources = [
 ('t7h8', Path('/home/dowling/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json'),
  '00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c'),
 ('t7j10', Path('/home/dowling/exam-x/work/r1_stagea_20261104_t7j10/stage_a_table.json'),
  '71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103'),
]
for name, path, expected in sources:
    data=path.read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if digest != expected: raise SystemExit('STOP: '+name+' table sha256 mismatch')
    table=json.loads(data)
    if not isinstance(table,dict) or not isinstance(table.get('rows'),list):
        raise SystemExit('STOP: '+name+' table rows malformed')
    if name=='t7j10' and table.get('label')!='ENGINEERING_ONLY':
        raise SystemExit('STOP: amendment table label mismatch')
    print(json.dumps({'table':name,'sha256':digest,'row_count':len(table['rows'])},sort_keys=True),flush=True)
    for row in table['rows']:
        if not isinstance(row,dict) or not isinstance(row.get('candidate'),str) or type(row.get('passed')) is not bool:
            raise SystemExit('STOP: '+name+' row malformed')
        if not row['passed']: continue
        qualification=row.get('qualification')
        if qualification is not None and not isinstance(qualification,dict):
            raise SystemExit('STOP: '+name+' qualification malformed')
        qualification=qualification or {}
        value=qualification.get('footprint_mib')
        valid=type(value) in (int,float) and math.isfinite(value) and value>0
        print(json.dumps({'table':name,'candidate':row['candidate'],'passed':True,
            'model_sha256':row.get('model_sha256'),'build':row.get('build'),
            'footprint_mib':value if valid else None,'positive_finite':valid,
            'qualification_status':qualification.get('status'),
            'qualification_context':qualification.get('context'),
            'cpu_pool_only':row.get('cpu_pool_only'),
            'thinking_disabled_due_grammar':row.get('thinking_disabled_due_grammar')},
            sort_keys=True,allow_nan=False),flush=True)
PY
rc=$?
printf '%s\n' "$rc" > "$OUT/exit.txt"
shasum -a 256 "$OUT/fields.jsonl" "$OUT/stderr.txt" "$OUT/exit.txt"
printf 'Private capture: %s; SSH exit=%s\n' "$OUT" "$rc"
```

Review the capture and exit code before use: both expected table SHA-256 values must match, rows must be complete, and every actual B1-eligible model's selected PASS row must supply a positive finite footprint with model SHA and build matching the final reviewed registry/config. The qwen25 anchor comes from t7h8; the v2 loader unions t7j10 only for candidate rows and prefers an existing t7h8 PASS. Software anchors do not use a model footprint. The independently reviewed preflight code should use `stage_a_pass_set` and the existing observer binding instead of trusting this diagnostic's own row ordering. A missing/invalid field, unexpected identity or changed table is STOP and retained evidence; do not infer a footprint, edit the tables, remeasure automatically or retry the same capture. Failure of one unrelated always-on/noneligible candidate is not silently treated as a B1 candidate failure; apply the actual frozen eligibility and skip rules.

The accepted A1 receipt is `docs/r1/reports/OPS_O1_20261104.md`, SHA-256 `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`; the real gate checks its digest and both named table hashes on the final host checkout. The site fields confirm the recorded numbers and provenance only; the independently reviewed final checkout, accepted note, real author gate, full preflight, handover and all other B1 conditions remain.
