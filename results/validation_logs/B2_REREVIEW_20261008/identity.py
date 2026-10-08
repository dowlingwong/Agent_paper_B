from common import *
out=[]
for seed in [11,21,31]:
    dev,test=rows('d',seed=seed-1),rows('t',seed=seed)
    report=e.evaluate_tree(dev,test,n_bootstrap=100,seed=901)
    agree=lambda a,b:sum(report.regimes[a][k]==report.regimes[b][k] for k in report.regimes[a])/len(test)
    cs=e._controllers(); bv=cs['bavar'].score(cs['bavar'].fit(dev),t.decision_views(test))
    out.append(dict(seed=seed,vwait_sd=report.diagnostics['vwait_sd'],proposed_myopic_agreement=agree('proposed','myopic'),myopic_constant_agreement=agree('myopic','constant_reserve'),params=report.params,bavar_reached_s2_sd=float(np.std([bv[r['root_id']]['s2'] for r in test if r['reached2']])),contrasts=report.contrasts,readings=report.readings))
emit(out)
