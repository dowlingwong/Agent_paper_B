import os,json,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path('/home/dowling/exam-x/work/agent_paper_B')
os.chdir(root);sys.path.insert(0,str(root))
from r1.exam.fit import estimate
R=json.loads((root/'r1/exam/registry.yaml').read_text()); F=json.loads((root/'docs/r1/reports/exam_phase2_20261026/fit_table.json').read_text()); f={x['id']:x for x in F}
cs=[x for x in (R['candidates']+R['sensitivities']) if x.get('quant_source',{}).get('size_bytes')]
print('registry candidates',len(R['candidates']),'pinned',len(cs),'fit',len(F)); print('unresolved',[(x['id'],x.get('phase2_status')) for x in R['candidates'] if x not in cs])
print('id|repo@revision|filename|bytes|sha|journal|disk|fit total bytes|admissible|checks')
for c in cs:
 s=c['quant_source']; id=c['id']; p=Path(c['runtime']['model_path']); j=Path('/home/dowling/exam-x/work/phase2/downloads')/(id+'.json'); issues=[]
 try:
  a=json.loads(j.read_text());
  if a.get('source')!=s: issues.append('source differs')
  if a.get('result',{}).get('sha256')!=s['sha256']: issues.append('result sha differs')
  if a.get('target')!=str(p):issues.append('target differs')
 except Exception as e: issues.append('journal missing/invalid '+str(e))
 try:
  size=p.stat().st_size
  if size!=s['size_bytes']:issues.append('disk size differs')
 except Exception as e: size='MISSING';issues.append('disk missing')
 try:
  entry=f[id]; path=root/entry['source_config']; data=path.read_bytes(); h=hashlib.sha256(data).hexdigest()
  if h!=entry['source_config_sha256'] or h!=c['runtime']['model_config_sha256']:issues.append('config hash differs')
  fit=estimate(json.loads(data),s['size_bytes']);
  if any(entry.get(k)!=v for k,v in fit.items()):issues.append('fit differs')
  tot=entry['total_bytes']; adm=entry['estimated_admissible']
 except Exception as e:tot=adm='ERROR';issues.append('fit error '+str(e))
 print('|'.join(map(str,[id,s['repo']+'@'+s['revision'],s['file'],s['size_bytes'],s['sha256'],j.exists(),size,tot,adm,','.join(issues) or 'ok'])))
print('sum',sum(x['quant_source']['size_bytes'] for x in cs));print('special',[(x['id'],x.get('source_label'),x.get('quant_source',{}).get('kind')) for x in cs if x['id']=='qwen3_coder_30b_a3b'])
