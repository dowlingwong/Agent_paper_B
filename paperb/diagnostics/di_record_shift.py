"""Record-reference check for DI_TEST_E1B_20261019 (coordinating-session review, 19 Oct 2026).

Compares, at digits_mlp E2 points where verify changed the decision, the recorded incumbent value
before the next trial, the next-3 mean delta_hat, and the next-3 mean ABSOLUTE metric between the
continue and verify branches. Usage: python -m r1.diagnostics.di_record_shift [branches dir]
"""
import json,glob,os,statistics as st,collections
import sys
B=sys.argv[1] if len(sys.argv)>1 else 'results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/branches'
def load(d):
    return [json.loads(l) for l in open(os.path.join(B,d,'branch_trials.jsonl'))]
def metric(t):
    pm=t.get('parsed_metrics') or {}
    return pm.get('val_score', pm.get('val_auc'))
pts=collections.defaultdict(dict)
for d in os.listdir(B):
    if not d.startswith('digits'): continue
    inst,b,act,rep=d.rsplit('__',3); p=int(b[1:])
    pts[(inst,p)][(act,rep)]=load(d)
rows=[]
for (inst,p),br in sorted(pts.items()):
    for rep in ('r1','r2'):
        c=br[('continue',rep)]; v=br[('verify',rep)]
        tc=[t for t in c if t['budget_index']==p][0]; tv=[t for t in v if t['budget_index']==p][0]
        changed = tc['decision']!=tv['decision']
        def nxt(L,k=3): return [t for t in L if t['budget_index']>p and metric(t) is not None][:k]
        nc,nv=nxt(c),nxt(v)
        rows.append(dict(inst=inst,p=p,rep=rep,changed=changed,
          rec_c=nc[0]['current_best_before'] if nc else None, rec_v=nv[0]['current_best_before'] if nv else None,
          dh_c=st.mean(t['delta_vs_best'] for t in nc if t['delta_vs_best'] is not None),
          dh_v=st.mean(t['delta_vs_best'] for t in nv if t['delta_vs_best'] is not None),
          m_c=st.mean(metric(t) for t in nc), m_v=st.mean(metric(t) for t in nv)))
for ch in (True,False):
    R=[r for r in rows if r['changed']==ch]
    print(f"changed={ch} n={len(R)}")
    print(f"  record before next trial: continue {st.mean(r['rec_c'] for r in R):.5f}  verify {st.mean(r['rec_v'] for r in R):.5f}  diff(v-c) {st.mean(r['rec_v']-r['rec_c'] for r in R):+.5f}")
    print(f"  next-3 mean delta_hat:     diff(v-c) {st.mean(r['dh_v']-r['dh_c'] for r in R):+.5f}")
    print(f"  next-3 mean ABS metric:    diff(v-c) {st.mean(r['m_v']-r['m_c'] for r in R):+.5f}   |diff| {st.mean(abs(r['m_v']-r['m_c']) for r in R):.5f}")
# null: r1 vs r2 same action, abs metric
null=[]
for (inst,p),br in pts.items():
    for act in ('continue','verify'):
        a=[t for t in br[(act,'r1')] if t['budget_index']>p and metric(t)][:3]; b=[t for t in br[(act,'r2')] if t['budget_index']>p and metric(t)][:3]
        null.append(abs(st.mean(map(metric,a))-st.mean(map(metric,b))))
print(f"null |diff| abs metric (r1 vs r2): {st.mean(null):.5f}")
