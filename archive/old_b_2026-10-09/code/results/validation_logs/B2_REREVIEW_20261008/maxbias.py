from common import *
out=[]
for noise in [.5,1.,2.]:
    values={k:[] for k in ['nested','old','naive','naive_minus_nested','naive_minus_old']}
    for seed in range(100):
        rs=rows('n',n=100,seed=seed,null=True,noise=noise)
        new=t.cross_fitted_scores(rs,c2=0).scores
        orig=t._oof_second_stage
        try:
            t._oof_second_stage=old_oof
            old=t.cross_fitted_scores(rs,c2=0).scores
        finally:t._oof_second_stage=orig
        nm=np.mean([new[r['root_id']]['vwait'] for r in rs]); om=np.mean([old[r['root_id']]['vwait'] for r in rs]); nv=np.mean([max(new[r['root_id']]['a2'],0) for r in rs])
        for k,v in [('nested',nm),('old',om),('naive',nv),('naive_minus_nested',nv-nm),('naive_minus_old',nv-om)]:values[k].append(v)
    out.append(dict(noise=noise,repetitions=100,**{k:ci(v) for k,v in values.items()}))
emit(out)
