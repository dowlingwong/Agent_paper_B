"""Exam guards adapted from archived Round-7 machinery; no old outcomes imported."""
from __future__ import annotations
import hashlib
import json
import math
import random
import re
import shutil
from pathlib import Path

MIN_FREE_BYTES = 100_000_000_000  # author STOP 0, decimal GB


def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(16<<20),b''): h.update(block)
    return h.hexdigest()


def frozen_digest(path, expected):
    actual=digest_file(path)
    if not re.fullmatch('[0-9a-f]{64}', str(expected)) or expected != actual:
        raise ValueError(f'frozen rule digest mismatch: {path}')
    return actual


def space_check(path, *, free_bytes=None):
    path=Path(path)
    if not path.exists(): raise RuntimeError(f'STOP: approved filesystem path does not exist: {path}')
    free=shutil.disk_usage(path).free if free_bytes is None else free_bytes
    if free < MIN_FREE_BYTES: raise RuntimeError(f'STOP: available space {free} below 100 GB on {path}')
    return {'path': str(path.resolve()), 'device': path.stat().st_dev, 'available_bytes': free, 'floor_bytes': MIN_FREE_BYTES}


def licence_blockers(candidate, policy):
    entry=(policy or {}).get('candidates',{}).get(candidate)
    if not entry: return [f'{candidate}:licence_not_declared']
    errors=[]
    if entry.get('status') != 'author_approved_research_and_publication': errors.append('licence_not_approved')
    if entry.get('approved_by') != 'Dowling Wong' or not entry.get('approval_ref'): errors.append('licence_approval_unbound')
    if not entry.get('licence'): errors.append('licence_terms_unrecorded')
    return [f'{candidate}:{e}' for e in errors]


def quantization_blockers(spec):
    source=spec.get('quant_source') or {}; q=source.get('quantization')
    if spec['id']=='gpt_oss_20b':
        return [] if q=='MXFP4' and source.get('kind')=='native_mxfp4' else ['gpt-oss requires native MXFP4']
    errors=[]
    if q!='Q4_K_M': errors.append('Q4_K_M required (IQ/GSQ variants are not substitutes)')
    vendor=spec.get('vendor_q4_available')
    if not isinstance(vendor,bool): errors.append('vendor Q4_K_M availability unresolved')
    kind=source.get('kind')
    if vendor is True and (kind!='vendor' or not str(source.get('repo','')).startswith(spec['base_repo'].split('/')[0]+'/')):
        errors.append('vendor Q4_K_M takes precedence')
    if vendor is False and (kind!='bartowski_imatrix' or not str(source.get('repo','')).startswith('bartowski/') or
                            not re.fullmatch('[0-9a-f]{64}',str(source.get('imatrix_sha256','')))):
        errors.append('fallback requires bartowski imatrix with bound evidence')
    return errors


def occupancy_blockers(samples, *, owned_pids=(), devices=(0,), max_baseline_mib=64, max_utilisation=5):
    """Ported Round-7 ownership and unknown-evidence checks; thresholds unchanged."""
    owned=set(owned_pids); errors=[]
    if {s.get('device') for s in samples} != set(devices): errors.append('occupancy_missing_device')
    for s in samples:
        foreign=set(s.get('compute_pids',[]))-owned
        if foreign: errors.append(f'foreign_compute_process:{sorted(foreign)}')
        if s.get('memory_used_mib') is None or s.get('utilisation_percent') is None: errors.append('occupancy_unknown')
        elif not owned.intersection(s.get('compute_pids',[])):
            if s['memory_used_mib'] > max_baseline_mib: errors.append('unexplained_baseline_vram')
            if s['utilisation_percent'] > max_utilisation: errors.append('sustained_utilisation')
    return sorted(set(errors))


def wilson_interval(successes, trials, *, z=1.959963984540054):
    """Port of Round-7 Wilson score interval; descriptive only."""
    n=int(trials); k=int(successes)
    if n<=0 or not 0<=k<=n: raise ValueError('Wilson interval requires 0 <= successes <= trials and trials > 0')
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; w=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return {'successes':k,'trials':n,'point':p,'lower':max(0.,c-w),'upper':min(1.,c+w),
            'method':'wilson_score','z':z,'descriptive_only':True}


def paired_instance_bootstrap(first, second, *, field='value', resamples=2000, seed=20261026):
    """Round-7 paired-template bootstrap adapted to numeric instance-cluster means."""
    def clusters(rows):
        out={}
        for r in rows:
            key=str(r['instance_id']); value=float(r[field])
            if not math.isfinite(value): raise ValueError('non-finite bootstrap input')
            out.setdefault(key,[]).append(value)
        return {k:sum(v)/len(v) for k,v in out.items()}
    a,b=clusters(first),clusters(second)
    if not a or set(a)!=set(b): raise ValueError('paired bootstrap requires identical nonempty instance sets')
    if resamples<100: raise ValueError('at least 100 bootstrap resamples required')
    keys=sorted(a); diffs=[a[k]-b[k] for k in keys];rng=random.Random(seed)
    draws=sorted(sum(rng.choice(diffs) for _ in keys)/len(keys) for _ in range(resamples))
    def pct(p):
        x=(len(draws)-1)*p;l=math.floor(x);h=math.ceil(x)
        return draws[l]*(h-x)+draws[h]*(x-l) if l!=h else draws[l]
    point=sum(diffs)/len(diffs);lo,hi=pct(.025),pct(.975)
    return {'difference_point':point,'difference_lower':lo,'difference_upper':hi,'median':pct(.5),
            'instances':len(keys),'resampling_unit':'instance_pair','bootstrap_resamples':resamples,
            'bootstrap_seed':seed,'point_within_interval':lo<=point<=hi,'bootstrap_unstable':not lo<=point<=hi,
            'descriptive_only':True}
