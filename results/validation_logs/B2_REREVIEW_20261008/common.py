import json, os, sys
from pathlib import Path
import numpy as np
ROOT=Path(os.environ.get('B2_REVIEW_ROOT','/private/tmp/B2_rereview_20261008'))
sys.path.insert(0,str(ROOT/'experiment_scaffold/src'))
from causal_branch.control import timing as t, evaluate_tree as e, replay_validity as rv

def rows(prefix,n=240,seed=0,null=False,noise=.05):
    rng=np.random.default_rng(seed); out=[]
    for i in range(n):
        x,z,w=rng.uniform(0,1,3); reached=True if null else rng.uniform()<.8
        later=.5+rng.normal(0,noise) if null else np.clip(.5+.7*(z-.4)+rng.normal(0,noise),0,1)
        out.append(dict(root_id=f'{prefix}{i}',family=f'{prefix}f{i%12}',h1={'x':x,'z':z},h2={'x':x,'z':z,'w':w},u_now=np.clip(.5+.6*(x-.5)+rng.normal(0,.03),0,1),u_never=.5,u_later=later if reached else .5,reached2=reached,terminated=not reached))
    return out

def ci(v):
    v=np.asarray(v); mean=float(v.mean()); se=float(v.std(ddof=1)/np.sqrt(len(v)))
    return dict(mean=mean,ci95=[mean-1.96*se,mean+1.96*se],ci3se=[mean-3*se,mean+3*se])

def old_oof(rows,keys,l2,n_folds):
    # Reconstruction of described old in-sample decision; not historical bytes.
    reached=[r for r in rows if r['reached2']]
    if not reached:return {}
    w=t._fit(t._design(reached,keys,2),[r['u_later']-r['u_never'] for r in reached],l2)
    return {r['root_id']:float(t._predict(w,t._design([r],keys,2))[0]) for r in reached}

def emit(value): print(json.dumps(value,indent=2,default=lambda x:float(x)))
