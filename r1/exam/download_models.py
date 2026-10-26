"""Phase 2 approved pinned artifacts only; CPU/network operation, no inference."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import platform
import time
from urllib.parse import quote
from r1.exam.guards import guarded_download, quantization_blockers, space_check


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registry',required=True);p.add_argument('--out',required=True);p.add_argument('--candidate',action='append')
    a=p.parse_args(argv)
    if platform.node().split('.')[0]!='TASL-2': raise RuntimeError('portal only')
    root=Path('/home/dowling/exam-x/models');space_check(root)
    registry=json.loads(Path(a.registry).read_text());rows=registry['candidates']+registry.get('sensitivities',[])
    selected=[s for s in rows if s.get('phase2_status')=='SOURCE_PINNED_NOT_DOWNLOADED']
    if a.candidate:
        selected=[s for s in selected if s['id'] in a.candidate]
        if {s['id'] for s in selected}!=set(a.candidate): raise ValueError('unknown or unresolved candidate requested')
    report=Path(a.out);report.mkdir(parents=True,exist_ok=True)
    if sum(s['quant_source']['size_bytes'] for s in selected)+100_000_000_000>__import__('shutil').disk_usage(root).free:
        raise RuntimeError('STOP: planned downloads would violate 100 GB reserve; inventory existing artifacts before retry')
    def download(s):
        blockers=quantization_blockers(s)
        if blockers: raise RuntimeError(str(blockers))
        source=s['quant_source'];target=Path(s['runtime']['model_path'])
        if not target.parent.resolve().is_relative_to(root): raise RuntimeError('unapproved model target')
        target.parent.mkdir(parents=True,exist_ok=True)
        url=f"https://huggingface.co/{source['repo']}/resolve/{source['revision']}/{quote(source['file'])}"
        start=time.time();print(s['id'],'START',flush=True)
        result=guarded_download(url,target,sha256=source['sha256'],size_bytes=source['size_bytes'],storage_root=root)
        record={'candidate':s['id'],'source':source,'target':str(target),'result':result,'started':start,'finished':time.time(),'space_after':space_check(root)}
        (report/(s['id']+'.json')).write_text(json.dumps(record,indent=2)+'\n')
        print(s['id'],'VERIFIED',flush=True)
        return record
    # Two streams bound resource use; every stream checks the shared free-space floor.
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(download,selected))

if __name__=='__main__': main()
