"""Explicit resolution of the recorded CAS decoder STOP; preserve all remaining state, no restart."""
import hashlib,json,os,platform,shutil,subprocess,time
from pathlib import Path
assert platform.node().split('.')[0]=='TASL-2'
work=Path('/home/dowling/exam-x/work');models=Path('/home/dowling/exam-x/models');base=work/'phase2'
record=base/'xet_stop_resolution.json'
if record.exists() or record.with_suffix('.planned.json').exists():raise RuntimeError('preserve earlier resolution; no replay')
stop=base/'downloads/transport_stop.json';errors=json.loads(stop.read_text())
first=errors['errors'][0];log=base/'downloads'/(first['candidate']+'.transport.log')
expected_first={'candidate':'olmo31_32b','error':"RuntimeError('STOP: HF transport exited 1; preserve its partial cache')"}
secondary=errors['errors'][1:]
if (errors.get('status')!='STOPPED' or first!=expected_first or len(secondary)!=2 or
    {r['candidate'] for r in secondary}!={'gemma4_31b','muse_glimmer_30b'} or
    any(r['error']!="InterruptedError('STOP: cohort transport cancelled')" for r in secondary)):
    raise RuntimeError('STOP does not match the exact independently reviewed failure')
marker='CAS Client Error: Format error: I/O error: error decoding response body'
if not log.read_text().rstrip().endswith(marker):raise RuntimeError('current final failure is not the reviewed CAS decoder error')
stop_sha256=hashlib.sha256(stop.read_bytes()).hexdigest();failure_log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()
# Census every matching owned module, not only children of the main thread.
for module in ('r1.exam.hub_download','r1.exam.download_models'):
    probe=subprocess.run(['pgrep','-u',str(os.getuid()),'-f',module],capture_output=True,text=True)
    if probe.returncode not in (0,1):raise RuntimeError('transport census unavailable')
    if probe.stdout.strip():raise RuntimeError('owned transport still live; no state move')
if models.stat().st_dev!=work.stat().st_dev:raise RuntimeError('unexpected filesystem split')
if shutil.disk_usage(work).free<100_000_000_000:raise RuntimeError('STOP below 100 GB')
reg=json.loads((work/'agent_paper_B/r1/exam/registry.yaml').read_text());rows=reg['candidates']+reg.get('sensitivities',[])
partials=[]
for spec in rows:
    folder=Path(spec['runtime']['model_path']).parent/'.cache/huggingface/download'
    for path in folder.glob('*.incomplete'):
        if path.is_symlink() or path.stat().st_uid!=os.getuid() or spec['quant_source']['sha256'] not in path.name:raise RuntimeError('unknown/unsafe incomplete file')
        partials.append((spec['id'],path))
plan={'purpose':'resolve diagnosed hf_xet decoder-only STOP for same-pin stdlib HTTPS receiving',
      'first_failure':first,'stop_sha256':stop_sha256,'failure_log_sha256':failure_log_sha256,'time':time.time(),'owned_transport_census':'none',
      'source_pins':{s['id']:{k:s['quant_source'][k] for k in ('repo','revision','file','size_bytes','sha256')} for s in rows},
      'library_limitation':'HF2.3.0 creates unique temporary files and automatically unlinks on ordinary failure. Exact bytes removed from failed OLMo temporary file are unavailable; no preservation claim is made for that deleted temporary file.',
      'remaining_partials':[],'history':[]}
record.with_suffix('.planned.json').write_text(json.dumps(plan,indent=2)+'\n')
archive=base/'transport_archives'/('xet_failed_'+str(time.time_ns()));archive.mkdir(parents=True)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(16<<20),b''):h.update(chunk)
    return h.hexdigest()
for index,(candidate,path) in enumerate(partials):
    if shutil.disk_usage(work).free<100_000_000_000:raise RuntimeError('STOP below 100 GB')
    size=path.stat().st_size;digest=sha(path);saved=archive/(str(index)+'__'+path.name)
    path.rename(saved)
    if saved.stat().st_size!=size or sha(saved)!=digest:raise RuntimeError('partial preservation mismatch')
    plan['remaining_partials'].append({'candidate':candidate,'original':str(path),'preserved':str(saved),'size':size,'sha256':digest})
history=list((base/'downloads').glob('*.json'))+list((base/'downloads').glob('*.transport.log'))+[base/'hub_downloads_v2.log',base/'hub_downloads_v2.pid']
for index,path in enumerate(history):
    saved=archive/('history_'+str(index)+'__'+path.name);shutil.copy2(path,saved)
    digest=sha(path)
    if sha(saved)!=digest:raise RuntimeError('history preservation mismatch')
    plan['history'].append({'original':str(path),'preserved':str(saved),'size':path.stat().st_size,'sha256':digest})
# Give the next transport fresh worker-log files while retaining exact originals.
for path in (base/'downloads').glob('*.transport.log'):
    path.rename(archive/('worker_log_original__'+path.name))
# The active STOP marker is moved only after its exact history copy was verified.
stop.rename(archive/'transport_stop.active_original.json')
plan.update(status='CAS_FAILURE_RESOLVED_FOR_EXPLICIT_SAME_PIN_HTTPS_CONTINUATION',archive=str(archive),finished=time.time())
record.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(plan,indent=2))
