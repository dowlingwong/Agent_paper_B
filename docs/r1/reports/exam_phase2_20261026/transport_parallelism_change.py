"""One explicit owned-controller stop; preserve HF partial snapshots and receiving/log history."""
from pathlib import Path
import hashlib,json,os,platform,signal,subprocess,time
assert platform.node().split('.')[0]=='TASL-2'
work=Path('/home/dowling/exam-x/work');models=Path('/home/dowling/exam-x/models');base=work/'phase2'
record=base/'transport_parallelism_change.json'
if record.exists() or record.with_suffix('.planned.json').exists():raise RuntimeError('preserve prior operation; no replay')
pid=int((base/'hub_downloads.pid').read_text().strip());proc=Path('/proc')/str(pid)
args=proc.joinpath('cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
if proc.stat().st_uid!=os.getuid() or args[:4]!=[str(work/'venv/bin/python'),'-u','-m','r1.exam.hub_download'] or '--worker' in args:raise RuntimeError('controller identity mismatch')
stat=proc.joinpath('stat').read_text().rsplit(')',1)[1].split();ticks=stat[19]
children=sorted({int(child) for task in proc.joinpath('task').iterdir()
                 for child in task.joinpath('children').read_text().split()})
plan={'purpose':'explicit transport concurrency change 2 to 6; immutable source pins unchanged','time':time.time(),
      'pid':pid,'uid':os.getuid(),'argv':args,'start_ticks':ticks,'owned_children':children,'preserved':[]}
for child in children:
    childproc=Path('/proc')/str(child);raw=childproc.joinpath('cmdline').read_bytes().decode()
    if childproc.stat().st_uid!=os.getuid() or 'r1.exam.hub_download\0--worker\0' not in raw:raise RuntimeError('unexpected child; inspect before stop')
record.with_suffix('.planned.json').write_text(json.dumps(plan,indent=2)+'\n')
if proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]!=ticks:raise RuntimeError('controller PID changed')
os.kill(pid,signal.SIGTERM)
for _ in range(225):
    if not proc.exists() or proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[0]=='Z':break
    time.sleep(.2)
else:raise RuntimeError('controller did not finish cleanup; leave state')
if any((Path('/proc')/str(child)).exists() for child in children):raise RuntimeError('owned children not reaped; leave state')
archive=base/'transport_archives'/('parallelism_'+str(time.time_ns()));archive.mkdir(parents=True)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(16<<20),b''):h.update(chunk)
    return h.hexdigest()
paths=list((base/'downloads').glob('*.json'))+[base/'hub_downloads.log',base/'hub_downloads.pid']
paths+=list(models.glob('*/.cache/huggingface/download/*.incomplete'))
paths+=list(models.glob('*/.cache/huggingface/download/*.metadata'))
for index,path in enumerate(paths):
    if path.is_symlink() or path.stat().st_uid!=os.getuid():raise RuntimeError('unsafe snapshot source')
    before=(path.stat().st_size,sha(path));saved=archive/(str(index)+'__'+path.name)
    subprocess.run(['cp','--reflink=auto','--sparse=always',str(path),str(saved)],check=True)
    if before!=(saved.stat().st_size,sha(saved)):raise RuntimeError('snapshot mismatch')
    plan['preserved'].append({'original':str(path),'preserved':str(saved),'size':before[0],'sha256':before[1]})
# Move only the intentional transport STOP record out of the active certificate directory.
stop=base/'downloads/transport_stop.json'
if stop.exists():stop.rename(archive/'transport_stop.active_original.json')
plan.update(status='READY_FOR_SAME_PIN_CACHE_CONTINUATION',archive=str(archive),finished=time.time())
record.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(plan,indent=2))
