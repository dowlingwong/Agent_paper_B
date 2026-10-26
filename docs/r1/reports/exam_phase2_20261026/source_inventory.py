import json,urllib.request,urllib.parse,concurrent.futures,time
from pathlib import Path
import yaml
OUT=Path('/Users/wongdowling/Documents/agent_paper_B/docs/r1/reports/exam_phase2_20261026')
REG=Path('/Users/wongdowling/Documents/agent_paper_B/r1/exam/registry.yaml')
def get(path):
    url='https://huggingface.co'+path
    try:
        with urllib.request.urlopen(url,timeout=45) as r:return json.load(r)
    except Exception as e:return {'error':str(e),'url':url}
def scan(row):
    repo=row['base_repo'];author,name=repo.split('/');search=name.removesuffix('-BF16')
    queries=[get('/api/models?'+urllib.parse.urlencode({'author':author,'search':search,'limit':100})),get('/api/models?'+urllib.parse.urlencode({'author':'bartowski','search':search,'limit':100}))]
    names={repo,repo+'-GGUF'}
    for q in queries:
        if isinstance(q,list):names.update(x['id'] for x in q)
    entries=[]
    for name in sorted(names):
        data=get('/api/models/'+name+'?blobs=true')
        files=[s for s in data.get('siblings',[]) if s['rfilename'].lower().endswith('.gguf') and ('q4_k_m' in s['rfilename'].lower() or ('mxfp4' in s['rfilename'].lower() and row['id']=='gpt_oss_20b'))]
        entries.append({'repo':name,'revision':data.get('sha'),'error':data.get('error'),'files':files,
                        'imatrix_files':[s for s in data.get('siblings',[]) if 'imatrix' in s['rfilename'].lower()]})
    result={'id':row['id'],'base_repo':repo,'queries':queries,'entries':entries}
    (OUT/(row['id']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(row['id'],[(e['repo'],len(e['files'])) for e in entries if e['files']],flush=True)
    return result
r=yaml.safe_load(REG.read_text());rows=r['candidates']+r.get('sensitivities',[])
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(scan,rows))
(OUT/'source_inventory.json').write_text(json.dumps(results,indent=2)+'\n')
