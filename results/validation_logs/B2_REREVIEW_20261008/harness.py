from common import *
out={}
dev,test=rows('d',seed=30),rows('t',seed=31)
c=t.ProposedTiming(); model=c.fit(dev);params=e._calibrate(c,model,dev,t.decision_views(dev),.25)
fixed=t.fit_global(dev,c2=params.c2)
a=c.score(model,t.decision_views(test));b=c.score(fixed,t.decision_views(test))
out['continuation_cutoff']=dict(fitted_cutoff=model['c2'],evaluated_cutoff=params.c2,mean_abs_vwait_difference=float(np.mean([abs(a[k]['vwait']-b[k]['vwait']) for k in a])),max_abs_vwait_difference=float(max(abs(a[k]['vwait']-b[k]['vwait']) for k in a)),actual_params=[params.c1,params.c2,params.reserve])
out['harness']=dict(values=e.evaluate_tree(dev,test,n_bootstrap=100).values,budget=60)
# Demonstrate consistency loss: score responds to refitting at deployed cutoff.
out['default_null_global']=[]
for noise in [.5,2.]:
    default=[];zero=[]
    for seed in range(100):
        ds,ts=rows('d',100,seed,null=True,noise=noise),rows('t',100,seed+1000,null=True,noise=noise)
        for cutoff,arr in [(None,default),(0,zero)]:
            m=t.fit_global(ds,c2=cutoff);s=c.score(m,t.decision_views(ts));arr.append(np.mean([v['vwait'] for v in s.values()]))
    out['default_null_global'].append(dict(noise=noise,median_cutoff=ci(default),fixed_zero_cutoff=ci(zero)))
emit(out)
