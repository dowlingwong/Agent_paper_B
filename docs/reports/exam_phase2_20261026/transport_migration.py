"""Explicit one-time transport change; only exam download workers and exact pinned partial paths."""
import hashlib,json,os,platform,signal,subprocess,time
from pathlib import Path

assert platform.node().split('.')[0]=='TASL-2'
work=Path('/home/dowling/exam-x/work');models=Path('/home/dowling/exam-x/models')
record=work/'phase2/transport_migration.json'
if record.exists() or record.with_suffix('.planned.json').exists():raise RuntimeError('preserve earlier migration; do not replay')
registry=json.loads((work/'agent_paper_B/r1/exam/registry.yaml').read_text())
rows=registry['candidates']+registry.get('sensitivities',[])
plan={'purpose':'planned transport migration; source pins unchanged; no inference/campaign retry',
      'time':time.time(),'workers':[],'partials':[]}
result=subprocess.run(['pgrep','-u',str(os.getuid()),'-f','r1.exam.download_models'],capture_output=True,text=True)
for value in result.stdout.splitlines():
    pid=int(value);proc=Path('/proc')/value
    args=(proc/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    if not (args[0]=='/home/dowling/exam-x/work/venv/bin/python' and '-m' in args and args[args.index('-m')+1]=='r1.exam.download_models'):continue
    if (proc.stat().st_uid!=os.getuid() or '--out' not in args or args[args.index('--out')+1]!=str(work/'phase2/downloads')):raise RuntimeError('worker ownership/path mismatch')
    stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
    plan['workers'].append({'pid':pid,'uid':os.getuid(),'argv':args,'start_ticks':stat[19]})
if not plan['workers']:raise RuntimeError('no matching active plain HTTPS worker; inspect before migration')
record.parent.mkdir(parents=True,exist_ok=True)
record.with_suffix('.planned.json').write_text(json.dumps(plan,indent=2)+'\n')
for entry in plan['workers']:
    proc=Path('/proc')/str(entry['pid']);stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
    if stat[19]!=entry['start_ticks']:raise RuntimeError('PID identity changed')
    os.kill(entry['pid'],signal.SIGTERM)
for entry in plan['workers']:
    for _ in range(150):
        proc=Path('/proc')/str(entry['pid'])
        if not proc.exists() or (proc/'stat').read_text().rsplit(')',1)[1].split()[0]=='Z':break
        time.sleep(.2)
    else:raise RuntimeError('worker still live; leave all files in place')
archive=work/'phase2/transport_archives'/str(time.time_ns());archive.mkdir(parents=True)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(16<<20),b''):h.update(chunk)
    return h.hexdigest()
for spec in rows:
    target=Path(spec['runtime']['model_path']);partial=target.with_name(target.name+'.partial')
    if not partial.exists():continue
    if partial.is_symlink() or partial.stat().st_uid!=os.getuid() or not partial.parent.resolve().is_relative_to(models):raise RuntimeError('unsafe partial')
    size=partial.stat().st_size;sha=digest(partial);saved=archive/(spec['id']+'__'+partial.name)
    partial.rename(saved)
    if saved.stat().st_size!=size or digest(saved)!=sha:raise RuntimeError('partial preservation check failed')
    plan['partials'].append({'candidate':spec['id'],'original':str(partial),'preserved':str(saved),'size':size,'sha256':sha})
plan['status']='TRANSPORT_CHANGE_COMPLETE_OLD_BYTES_PRESERVED';plan['finished']=time.time()
record.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(plan,indent=2))
