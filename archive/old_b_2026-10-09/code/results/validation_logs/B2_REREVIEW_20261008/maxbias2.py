from common import *
# Distinct deployed-model check: independent null test roots; explicit c2=0.
values={k:[] for k in ['oof','old','naive','naive_minus_oof']}
for seed in range(100):
    dev,test=rows('d',100,seed,null=True,noise=2),rows('t',100,seed+1000,null=True,noise=2)
    new=t.fit_global(dev,c2=0); orig=t._oof_second_stage
    try:
        t._oof_second_stage=old_oof; old=t.fit_global(dev,c2=0)
    finally:t._oof_second_stage=orig
    views=t.decision_views(test); ns=t.ProposedTiming().score(new,views); os=t.ProposedTiming().score(old,views)
    a=np.mean([s['vwait'] for s in ns.values()]); b=np.mean([s['vwait'] for s in os.values()]); c=np.mean([max(s['a2'],0) for s in ns.values()])
    for k,v in [('oof',a),('old',b),('naive',c),('naive_minus_oof',c-a)]:values[k].append(v)
emit({k:ci(v) for k,v in values.items()})
