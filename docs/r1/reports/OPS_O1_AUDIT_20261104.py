import json, hashlib, re, collections
from pathlib import Path
P=Path('/private/tmp/paper-b-o1-evidence'); J=P/'j10'; H=P/'h8'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(cond,msg):
 if not cond: problems.append(msg)
problems=[]; a=read(H/'stage_a_table.json'); b=read(J/'stage_a_table.json'); rows={r['candidate']:r for r in b['rows']}; old={r['candidate']:r for r in a['rows']}; batch=read(J/'batch_state.json');manifest=P/'r1_stagea_lease_20261104_t7j10.manifest.json';m=read(manifest);lease=P/'r1_stagea_lease_20261104_t7j10';com=read(lease/'lease_completion.json');release=read(lease/'lease_release.json');prompts={x['trial_id']:x for x in map(json.loads,(P/'prompts.jsonl').read_text().splitlines())}
ck(sha(manifest)==batch['amendment_measurement']['manifest_sha256'], 'manifest hash');ck(sha(J/'batch_state.json')==com['batch_state_sha256'],'batch hash');ck(sha(lease/'lease_completion.json')==release['completion']['completion_sha256'],'completion hash');ck(release['released'] and release['reason']=='validated_completion','lease release');ck(batch['status']=='COMPLETE' and len(rows)==10 and not batch['interruptions'],'batch completeness');ck(sha(P/'prompts.jsonl')==batch['amendment_measurement']['prompts_sha256'],'prompt sha');
for x in com['servers']:
 f=J/Path(x['record_path']).relative_to('/home/dowling/exam-x/work/r1_stagea_20261104_t7j10');ck(f.exists() and sha(f)==x['record_sha256'],'server record '+str(f))
allrecords=list(J.rglob('llama_server_*.json'));ck(len(allrecords)==len(com['servers'])==16,'server records count')
for name,sha_expected in batch['amendment_measurement']['repairs'].items():
 f=P/'code/templates/repairs'/f'{name}.jinja';actual=sha(f);mp=[x['sha256'] for x in m['files'] if x['path'].endswith('/'+name+'.jinja')];ck(actual==sha_expected and mp==[actual],'repair '+name);print('REPAIR',name,actual,'MATCH',actual==sha_expected and mp==[actual])
keys=['passed','prompts','free_parse_successes','schema_parse_successes','active_key_successes','free_active_key_successes','seed_reproducible','free_seed_reproducible','template_checks','failure_classes']
for n in ('random_valid','scripted','qwen25_coder_7b'):
 mismatches=[k for k in keys if old[n].get(k,'N/A')!=rows[n].get(k,'N/A')];ck(not mismatches,'anchor mismatch '+n+' '+str(mismatches));print('ANCHOR',n,'mismatches',mismatches)
print('name free/schema parse active free/schema reproducibility template min_free offload grammar issues')
for n,r in rows.items():
 ck(r['passed'] and not r['failure_classes'],n+' pass/failure'); q=batch['completed'][n+'/stage-a'];file=J/Path(q['path']).relative_to('/home/dowling/exam-x/work/r1_stagea_20261104_t7j10');ck(file.exists() and sha(file)==q['sha256'],n+' row digest');ck(read(file)==r,n+' row/table equality')
 if r.get('software_anchor'): continue
 prior=len(problems);root=J/n/'stage-a/32768';qual=read(root/'qualification/qualification.json');raw=J/Path(qual['raw_probe']).relative_to('/home/dowling/exam-x/work/r1_stagea_20261104_t7j10');off=read(J/'servers'/n/'exam_offload.json')
 ck(qual['status']=='PASS' and sha(raw)==qual['raw_probe_sha256'] and qual['model_sha256']==r['model_sha256'],n+' qualification');ck(off['full'] and off['route']=='log_line' and not off['cpu_fallback_lines'],n+' offload');ck(r['prefill_tokens']==32767 and r['prefill_generated_tokens']==1 and r['declared_context_tokens']==32768,n+' prefill');ck(min(x['free_mib'] for x in r['gpu_samples'])==r['min_free_mib'] and r['min_free_mib']>=1024,n+' vram')
 e=r['template_check_evidence'];ck(len(e)==55 and collections.Counter(x['kind'] for x in e)=={'fixed':5,'frozen':50} and all((x['method']=='byte' and x['byte_equal']) or (x['method']=='token' and not x['byte_equal'] and x['tokens_equal'] and x['server_tokenize'] and x['prefix_token_id'] is not None) for x in e),n+' template');ck(all(r['template_checks']) and len(r['template_checks_frozen'])==50 and all(r['template_checks_frozen']),n+' template booleans')
 rr=r['responses'];ck(len(rr)==50 and set(x['prompt_id'] for x in rr)==set(prompts),n+' prompt coverage');counts=collections.Counter();invalid=[];repro=[]
 for x in rr:
  for v in x['responses']:
   st=v['structured'];counts[('parse',st)]+=bool(v.get('parse_ok'));rep=v.get('repeat_message') or {};repro.append(rep.get('content')==v.get('raw_content') and rep.get('reasoning_content')==v.get('reasoning_content'))
   s=re.sub(r'<think>.*?</think>\s*','',v['raw_content'],flags=re.S).strip();s=re.sub(r'^```(?:json)?\s*|\s*```$','',s,flags=re.I)
   try:
    d=json.loads(s); key=d.get('param'); valid=key is not None and key.lower() in {str(k).lower() for k in prompts[x['prompt_id']]['active_keys']}; counts[('active',st)]+=bool(valid)
    if st: ck(set(d)=={'rationale','summary','objective','param','old_value','new_value'} and all(isinstance(z,str) for z in d.values()),n+' schema')
   except Exception: invalid.append((x['prompt_id'],st))
 ck(all(repro) and len(repro)==100,n+' repeat mismatch'); ck(counts['parse',False]==r['free_parse_successes'] and counts['parse',True]==r['schema_parse_successes'],n+' parse counts');ck(counts['active',True]==r['active_key_successes'],n+' structured active');ck(r['seed_reproducible'] and r['free_seed_reproducible'],n+' seed flags');ck(not invalid,n+' JSON extraction '+str(len(invalid)))
 if r['thinking_policy'].get('switchable'):ck(r.get('thinking_grammar_probe',{}).get('passed') is True,n+' grammar probe')
 print(n, counts['parse',False],counts['parse',True],counts['active',False],counts['active',True],sum(repro),len(e),r['min_free_mib'],off['full'],r.get('thinking_grammar_probe',{}).get('passed','N/A'),problems[prior:])
print('RESULT',len(problems),'issues')
for x in problems: print('ISSUE',x)
