import json,hashlib,collections
from pathlib import Path
P=Path('/private/tmp/paper-b-o1-evidence');J=P/'j10';prompts={r['trial_id']:r for r in map(json.loads,(P/'prompts.jsonl').read_text().splitlines())};rows=json.loads((J/'stage_a_table.json').read_text())['rows']; errors=[]
for r in rows:
 if r.get('software_anchor'): continue
 n=r['candidate'];f=J/n/'stage-a/32768/d3_false_calls.jsonl';events=collections.defaultdict(dict)
 for s in f.read_text().splitlines():
  e=json.loads(s);events[e['sequence']][e['event']]=e
 count=0
 for i,x in enumerate(r['responses']):
  for j,v in enumerate(x['responses']):
   k=2+i*4+j*2
   for seq in (k,k+1):
    e=events[seq];req=e.get('request_attempt',{});res=e.get('response',{});checked=e.get('checked',{})
    try:
     body=json.loads(req['request_body']);raw=res['response_body'];reply=json.loads(raw);message=reply['choices'][0]['message']; expected=v['raw_content'] if seq==k else v['repeat_message']['content']; reason=v.get('reasoning_content') if seq==k else v['repeat_message'].get('reasoning_content');prompt=prompts[x['prompt_id']]
     good=(req['route']=='/v1/chat/completions' and body.get('cache_prompt') is False and body.get('seed')==v['seed'] and body['messages'][0]['content']==prompt['prompt'] and ('response_format' in body)==v['structured'] and res['http_status']==200 and hashlib.sha256(raw.encode()).hexdigest()==res['response_body_sha256'] and message.get('content')==expected and message.get('reasoning_content')==reason and checked)
     if not good: errors.append((n,seq,'mismatch'))
     count+=bool(good)
    except Exception as ex: errors.append((n,seq,str(ex)))
 print(n,'journal matched',count,'/200', 'extra sequences',len(events)-201)
print('errors',len(errors));print('\n'.join(map(str,errors[:20])))
