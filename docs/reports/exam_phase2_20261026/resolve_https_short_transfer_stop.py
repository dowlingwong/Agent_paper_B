"""Author-approved exact short-transfer STOP archival; no download or inference."""
import hashlib,json,os,platform,shutil,subprocess,time
from pathlib import Path

EXPECTED={
    'olmo31_32b':18622709760,'devstral_small2_24b':5184159744,
    'glm47_flash':11072962560,'qwen36_35b_a3b':15703474176,
    'lfm25_24b_a2b':10821304320,'nemotron35_30b_a3b':15695959265}
COMPLETED={'qwen38_27b','qwen36_27b','muse_glimmer_30b','gemma4_26b_a4b','gemma4_31b'}

def main():
    if platform.node().split('.')[0]!='TASL-2':raise RuntimeError('portal only')
    work=Path('/home/dowling/exam-x/work');models=Path('/home/dowling/exam-x/models');base=work/'phase2';downloads=base/'downloads'
    record=base/'https_short_stop_resolution.json';planned=record.with_suffix('.planned.json')
    if record.exists() or planned.exists():raise RuntimeError('preserve earlier resolution; no replay')
    stop=downloads/'transport_stop.json';failure=downloads/'nemotron35_30b_a3b.transport.log'
    state=json.loads(stop.read_text());errors=state.get('errors',[])
    first={'candidate':'nemotron35_30b_a3b','error':"RuntimeError('STOP: HTTPS transport exited 1; inspect retained partial and worker log')"}
    if (state.get('status')!='STOPPED' or len(errors)!=3 or errors[0]!=first or
        {e['candidate'] for e in errors[1:]}!={'qwen36_35b_a3b','olmo31_32b'} or
        any(e['error']!="InterruptedError('STOP: cohort transport cancelled')" for e in errors[1:])):
        raise RuntimeError('unexpected STOP; preserve')
    marker='RuntimeError: STOP: downloaded artifact size/digest mismatch; partial retained'
    if not failure.read_text().rstrip().endswith(marker):raise RuntimeError('unexpected final failure')
    for module in ('r1.exam.hub_download','r1.exam.download_models'):
        census=subprocess.run(['pgrep','-u',str(os.getuid()),'-f',module],capture_output=True,text=True)
        if census.returncode not in (0,1) or census.stdout.strip():raise RuntimeError('transport census unavailable or live')
    def floor():
        free=shutil.disk_usage(models).free
        if free<100_000_000_000:raise RuntimeError('STOP below 100 GB')
        return free
    def sha(path):
        h=hashlib.sha256();before=path.stat()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(16<<20),b''):floor();h.update(block)
        after=path.stat()
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        if identity(before)!=identity(after):raise RuntimeError('file changed during hash')
        return h.hexdigest()
    if models.stat().st_dev!=work.stat().st_dev:raise RuntimeError('unexpected filesystem split')
    reg=json.loads((work/'agent_paper_B/r1/exam/registry.yaml').read_text());rows=reg['candidates']+reg.get('sensitivities',[])
    specs={s['id']:s for s in rows};partials=[]
    observed={p.resolve() for p in models.glob('*/*.partial')}
    for candidate,size in EXPECTED.items():
        target=Path(specs[candidate]['runtime']['model_path']);path=target.with_name(target.name+'.partial')
        if (target.exists() or path.is_symlink() or not path.is_file() or path.stat().st_uid!=os.getuid() or
            path.stat().st_size!=size or not path.parent.resolve().is_relative_to(models.resolve())):
            raise RuntimeError('unexpected partial identity')
        partials.append((candidate,path))
    if observed!={p.resolve() for _,p in partials}:raise RuntimeError('unexpected partial set')
    certs={p.stem for p in downloads.glob('*.json') if p.name!='transport_stop.json'}
    if certs!=COMPLETED:raise RuntimeError('unexpected certificate set')
    for candidate in COMPLETED:
        cert=json.loads((downloads/(candidate+'.json')).read_text());target=Path(specs[candidate]['runtime']['model_path'])
        if cert['source']!=specs[candidate]['quant_source'] or target.stat().st_size!=cert['source']['size_bytes']:
            raise RuntimeError('completed artifact identity differs')
    needed=sum(s['quant_source']['size_bytes'] for s in rows if s['id'] not in COMPLETED)
    if floor()<needed+100_000_000_000:raise RuntimeError('fresh retry cannot retain reserve')
    plan={'authority':'Author 26 Oct: Approve archival and same-source retry','status':'ARCHIVAL_PLANNED',
          'first_failure':first,'stop_sha256':sha(stop),'failure_log_sha256':sha(failure),'time':time.time(),
          'owned_transport_census':'none','free_before':floor(),'remaining_download_bytes':needed,
          'source_pins':{s['id']:s['quant_source'] for s in rows},'partials':[],'history':[]}
    planned.write_text(json.dumps(plan,indent=2)+'\n')
    archive=base/'transport_archives'/('https_short_'+str(time.time_ns()));archive.mkdir(parents=True)
    for candidate,path in partials:
        floor();before=path.stat();digest=sha(path);saved=archive/(candidate+'__'+path.name)
        path.rename(saved)
        if saved.stat().st_size!=before.st_size or sha(saved)!=digest:raise RuntimeError('archival verification failed')
        plan['partials'].append({'candidate':candidate,'original':str(path),'preserved':str(saved),'size':before.st_size,'sha256':digest})
        planned.write_text(json.dumps(plan,indent=2)+'\n')
    history=list(downloads.glob('*.json'))+list(downloads.glob('*.transport.log'))+[base/'https_downloads.log',base/'https_downloads.pid']
    for i,path in enumerate(history):
        if path.is_symlink() or path.stat().st_uid!=os.getuid():raise RuntimeError('unsafe history')
        saved=archive/('history_'+str(i)+'__'+path.name);floor();digest=sha(path);shutil.copy2(path,saved)
        if sha(saved)!=digest:raise RuntimeError('history verification failed')
        plan['history'].append({'original':str(path),'preserved':str(saved),'size':path.stat().st_size,'sha256':digest})
    for path in downloads.glob('*.transport.log'):path.rename(archive/('worker_log_original__'+path.name))
    stop.rename(archive/'transport_stop.active_original.json')
    plan.update(status='AUTHOR_APPROVED_SAME_SOURCE_RETRY_READY',archive=str(archive),finished=time.time(),free_after=floor())
    record.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'record':str(record),'archive':str(archive),'partials':len(plan['partials']),'status':plan['status']}))

if __name__=='__main__':main()
