from common import *
from unittest.mock import patch
from causal_branch.control.allocator import AllocatorRoot,AllocatorParams,allocate,budget_for
out={}
dev,test=rows('d',seed=20),rows('t',seed=21)
# Spy establishes actual harness path inputs, independently of contrast p-grid.
orig=e.path_allowance; calls=[]
def spy(a,b):calls.append([a.p,b.p,a.provenance_kind,b.provenance_kind]);return orig(a,b)
with patch.object(e,'path_allowance',spy):r=e.evaluate_tree(dev,test,n_bootstrap=100,p_grid=(.10,))
out['allowance_calls']=calls; out['empty_surviving_grid']=r.n1
out['tax_checks']={k:dict(lcb=v['adjusted_lcb'],reported=r.n1['population_bound_at_working_p'][k],expected=max(-1,min(1,v['adjusted_lcb']-.24))) for k,v in r.contrasts.items()}
with patch.object(e,'WORKING_P',0):zero=e.evaluate_tree(dev,test,n_bootstrap=30,p_grid=(0,))
out['zero_allowance']=dict(p_path=zero.n1['p_path'],tax=zero.n1['population_tax_2mp'],bounds=zero.n1['population_bound_at_working_p'],lcbs={k:v['adjusted_lcb'] for k,v in zero.contrasts.items()})
# Force a genuinely identical policy implementation in scratch memory.
with patch.object(e,'ProposedTiming',t.RepeatedMyopicComparator):ident=e.evaluate_tree(dev,test,n_bootstrap=50)
out['identical_policies']=dict(contrasts=ident.contrasts,readings=ident.readings)
# Poison leaves after fitting; raw row scoring must refuse.
c=t.ProposedTiming();model=c.fit(dev);original=c.score(model,t.decision_views(test)); poisoned=[dict(x,u_now=float('nan'),u_later=float('nan'),u_never=float('nan')) for x in test]
out['scoring_outcome_invariance']=original==c.score(model,t.decision_views(poisoned))
try:c.score(model,{x['root_id']:x for x in test});out['raw_rows_refused']=False
except t.TimingError:out['raw_rows_refused']=True
# All infeasible input: compare evaluated adapter with direct allocator.
masked=[dict(x,feasible1=False,feasible2=False) for x in test]
scores={x['root_id']:dict(s1=1.,s2=1.) for x in test};params=AllocatorParams(0.,0.,0)
actual=e._run_allocator(masked,scores,params,.25)
direct=allocate([AllocatorRoot(root_id=x['root_id'],s1=1,s2=1,reached2=x['reached2'],feasible1=False,feasible2=False) for x in masked],budget=60,params=params,q=.25)
out['all_infeasible_adapter']=dict(evaluated_calls=sum(v!='never' for v in actual.values()),direct_calls=direct.realized_calls)
allreport=e.evaluate_tree([dict(x,feasible1=False,feasible2=False) for x in dev],masked,n_bootstrap=30)
out['all_infeasible_harness_calls']={k:sum(v!='never' for v in d.values()) for k,d in allreport.regimes.items()}
# Report should preserve negative bounds, not only qualifying positive ones.
_,all_bounds=rv.simultaneous_family_bounds({'negative':np.full(12,-.1)},.05,0)
qualifying,_=rv.simultaneous_family_bounds({'negative':np.full(12,-.1)},.05,0)
out['family_bounds_return_order']=dict(qualifying=qualifying,all_bounds=all_bounds,reported_field=r.n1['family_bounds_at_p0'])
# Independent single-field perturbations; no built-in displacement helper.
rng=np.random.default_rng(42);worst=0;trials=0
from dataclasses import replace
for i in range(500):
    rr=[AllocatorRoot(str(j),float(rng.normal()),float(rng.normal()),feasible1=bool(rng.integers(2)),feasible2=bool(rng.integers(2)),reached2=bool(rng.integers(2)),terminated=False) for j in range(24)]
    pp=AllocatorParams(0,0,int(rng.integers(7))); base=allocate(rr,budget=6,params=pp,q=.25).regimes
    for j in range(24):
        for field,value in [('s1',float(rng.normal()*5)),('s2',float(rng.normal()*5)),('reached2',not rr[j].reached2),('feasible1',not rr[j].feasible1),('feasible2',not rr[j].feasible2),('terminated',True)]:
            changed=list(rr);changed[j]=replace(rr[j],**{field:value});new=allocate(changed,budget=6,params=pp,q=.25).regimes
            worst=max(worst,sum(base[k]!=new[k] for k in base));trials+=1
out['independent_displacement']=dict(trials=trials,max_changed_roots=worst)
emit(out)
