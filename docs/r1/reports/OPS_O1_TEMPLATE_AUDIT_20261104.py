import os,json,hashlib,base64,collections
from pathlib import Path
from transformers import AutoTokenizer
base=Path('/home/dowling/exam-x/work/r1_stagea_20261104_t7j10')
rows=json.loads((base/'stage_a_table.json').read_text())['rows'];errors=[]
for r in rows:
 if r.get('software_anchor'):continue
 n=r['candidate'];root=base/n/'stage-a/32768';spec=json.loads((root/'job.json').read_text())['candidate'];source=spec['chat_template_source'];tokenizer=AutoTokenizer.from_pretrained(source['repo'],revision=source['revision'],trust_remote_code=False,token=False,local_files_only=True);t=tokenizer.get_chat_template();assert hashlib.sha256(t.encode()).hexdigest()==source['template_sha256']
 events=collections.defaultdict(dict)
 for line in (root/'d3_non_generation_calls.jsonl').read_text().splitlines():
  event=json.loads(line);events[event['sequence']][event['event']]=event
 ordered=sorted(events.items());applies=[];tokens={}
 for seq,e in ordered:
  req=e.get('request_attempt',{});res=e.get('response',{});route=req.get('route')
  if route not in ['/apply-template','/tokenize']:continue
  body=json.loads(req['request_body']);raw=base64.b64decode(res['response_body_b64']);assert hashlib.sha256(raw).hexdigest()==res['response_body_sha256']; reply=json.loads(raw)
  if route=='/apply-template':applies.append((seq,body,reply['prompt']))
  if route=='/tokenize':tokens[seq]=(body,reply['tokens'])
 assert len(applies)==55
 good=0
 for (seq,body,actual),e in zip(applies,r['template_check_evidence']):
  expected=tokenizer.apply_chat_template(body['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=spec['thinking_policy']['mode']!='off')
  if actual==expected: ok=e['method']=='byte' and e['byte_equal']
  else:
   bos=tokenizer.bos_token;bosid=tokenizer.bos_token_id; hf=tokenizer(expected,add_special_tokens=False).input_ids;served=tokenizer(actual,add_special_tokens=False).input_ids;prefix=tokenizer(bos,add_special_tokens=False).input_ids;tb,tt=tokens.get(seq+1,({},[]));ok=(isinstance(bos,str) and bool(bos) and expected==bos+actual and len(prefix)==1 and hf==prefix+served and tb=={'content':actual,'add_special':True} and tt==hf and e['method']=='token' and e['prefix_token_id']==bosid and e['tokens_equal'] and e['server_tokenize'])
  if not ok:errors.append((n,seq,e['kind'],e['id']))
  good+=bool(ok)
 print(n,'independently recomputed',good,'/55',flush=True)
print('errors',len(errors),errors,flush=True)
