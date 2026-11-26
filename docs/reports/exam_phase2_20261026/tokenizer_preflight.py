"""Pinned tokenizer/template access preflight only; no model load or inference."""
import hashlib,json,os,platform,time,importlib.metadata,threading,signal,argparse
from pathlib import Path
assert platform.node().split('.')[0]=='TASL-2'
parser=argparse.ArgumentParser();parser.add_argument('--candidate',action='append');parser.add_argument('--out-name',default='tokenizer_preflight_1.json');args=parser.parse_args()
if Path(args.out_name).name!=args.out_name:raise ValueError('report basename required')
work=Path('/home/dowling/exam-x/work');out=work/'phase2'/args.out_name
if out.exists():raise RuntimeError('preserve previous preflight attempt')
os.environ.update(HF_HOME=str(work/'hf'),HF_HUB_DISABLE_IMPLICIT_TOKEN='1',HF_HUB_DISABLE_XET='1',CUDA_VISIBLE_DEVICES='')
from transformers import AutoTokenizer
from r1.exam.guards import space_check
stop=threading.Event()
def watch_space():
    while not stop.wait(.2):
        try:space_check(work)
        except Exception as error:
            os.write(2,(str(error)+'\n').encode());os.kill(os.getpid(),signal.SIGTERM);return
threading.Thread(target=watch_space,daemon=True).start()
registry=json.loads((work/'agent_paper_B/r1/exam/registry.yaml').read_text());rows=[];selected=registry['candidates']+registry.get('sensitivities',[])
if args.candidate:
    selected=[s for s in selected if s['id'] in args.candidate]
    if {s['id'] for s in selected}!=set(args.candidate):raise ValueError('unknown candidate')
for spec in selected:
    space_check(work);source=spec['chat_template_source'];started=time.time()
    row={'candidate':spec['id'],'source_label':spec['source_label'],'repo':source['repo'],'revision':source['revision']}
    try:
        tokenizer=AutoTokenizer.from_pretrained(source['repo'],revision=source['revision'],trust_remote_code=False,token=False)
        template=tokenizer.get_chat_template();sha=hashlib.sha256(template.encode()).hexdigest()
        row.update(status='PASS' if sha==source['template_sha256'] else 'PREPARATION_STOP',template_sha256=sha,
                   expected_sha256=source['template_sha256'],tokenizer_class=type(tokenizer).__name__)
        del tokenizer
    except Exception as error:row.update(status='PREPARATION_STOP',error=f'{type(error).__name__}: {error}')
    row['seconds']=time.time()-started;rows.append(row)
    out.write_text(json.dumps({'label':'ENGINEERING_ONLY','scope':'CPU tokenizer/template access only; no inference',
                              'versions':{k:importlib.metadata.version(k) for k in ('transformers','tokenizers','huggingface-hub')},
                              'complete':False,'rows':rows},indent=2)+'\n')
    print(spec['id'],row['status'],flush=True)
result=json.loads(out.read_text());result['complete']=True;result['all_pass']=all(r['status']=='PASS' for r in rows)
out.write_text(json.dumps(result,indent=2)+'\n');stop.set()
