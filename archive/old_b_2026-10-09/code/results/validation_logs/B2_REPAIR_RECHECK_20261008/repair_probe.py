import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'B2_REREVIEW_20261008'))
from common import *
from unittest.mock import patch
out={};dev,test=rows('d',seed=30),rows('t',seed=31)
seen=[];original=t.ProposedTiming.score

def observe(c,m,v):
    seen.append(dict(c2=m['c2'],split='test' if 't0' in v else 'dev'))
    return original(c,m,v)
with patch.object(t.ProposedTiming,'score',observe):report=e.evaluate_tree(dev,test,n_bootstrap=20)
out['cutoff']=dict(score_calls=seen,selected=report.params['proposed'][1],diagnostic=report.diagnostics['continuation_target_c2'])
assert [x['c2'] for x in seen if x['split']=='test']==[report.params['proposed'][1]]
assert {x['c2'] for x in seen if x['split']=='dev'}==set(t.GRID_C)
assert report.diagnostics['continuation_target_c2']==report.params['proposed'][1]
out['grids']={k:dict(count=c.tuning_configs,l2=c.l2,folds=c.n_folds,tuples=[(p.c1,p.c2,p.reserve) for p in c.grid()]) for k,c in e._controllers().items()}
assert all(x['count']==27 and x['l2']==.01 and x['folds']==5 for x in out['grids'].values())
out['mask_checks']=[]
for masks in [dict(feasible1=False,feasible2=False),dict(feasible1=False),dict(feasible2=False)]:
    ds=[dict(r,**masks) for r in dev];ts=[dict(r,**masks) for r in test];allocs=[];orig=e.allocate
    def alloc(roots,**kw):
        result=orig(roots,**kw);allocs.append((roots,result));return result
    with patch.object(e,'allocate',alloc):r=e.evaluate_tree(ds,ts,n_bootstrap=20)
    for roots,result in allocs:
        for root in roots:
            assert all(getattr(root,k)==v for k,v in masks.items())
            if masks.get('feasible1') is False:assert result.regimes[root.root_id]!='now'
            if masks.get('feasible2') is False:assert result.regimes[root.root_id]!='later'
    assert any('__' in x.root_id for rr,_ in allocs for x in rr)
    for name,reg in r.regimes.items():
        a=r.resource_accounting[name];calls=sum(v!='never' for v in reg.values())
        assert a['realized_calls']==calls and a['unspent_calls']==r.budget-calls and a['allocator_work']==calls
        assert a['work_per_call']==1 and 'excludes fitting, model tokens and elapsed time' in a['scope']
    if len(masks)==2:
        assert all(result.realized_calls==0 for _,result in allocs)
        assert set(r.n1['family_bounds_at_p0'])==set(r.contrasts)
        assert all(v<0 for v in r.n1['family_bounds_at_p0'].values())
        assert all(v==.5 for v in r.values.values())
    out['mask_checks'].append(dict(masks=masks,allocation_calls=len(allocs),bootstrap_allocation_calls=sum(any('__' in x.root_id for x in rr) for rr,_ in allocs),n_roots=r.n_roots,budget=r.budget,resource_accounting=r.resource_accounting,family_bounds=r.n1['family_bounds_at_p0']))
out['passed']=True
emit(out)
