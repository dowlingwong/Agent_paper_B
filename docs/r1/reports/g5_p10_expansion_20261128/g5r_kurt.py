import json,sys,math,collections
rows=[json.loads(l) for l in open(sys.argv[1])]
def G2(x):
    n=len(x); m=sum(x)/n; d=[v-m for v in x]; m2=sum(v*v for v in d)/n; m4=sum(v**4 for v in d)/n
    if m2==0: return float('nan'), 0.0
    g2=m4/m2**2-3
    G=((n+1)*g2+6)*(n-1)/((n-2)*(n-3))
    s=math.sqrt(m2*n/(n-1)); return G, max(abs(v)/s for v in d)
J=collections.defaultdict(dict); bad=collections.Counter()
for r in rows:
    if r['condition']!='joint': continue
    if not r['success'] or r['metric'] is None or not math.isfinite(r['metric']): bad[(r['node'],r['config'])]+=1; continue
    J[(r['node'],r['config'])][r['run_id'].split('_',1)[1]]=r['metric']
print("bad",dict(bad))
nodes=sorted({k[0] for k in J})
n=30; se=math.sqrt(24*n*(n-1)**2/((n-3)*(n-2)*(n+3)*(n+5)))
print(f"SE(G2) n=30: {se:.3f}")
print("| node | c0 | c1 | c2 | c3 | c4 | paired c1-c0 | c2-c0 | c3-c0 | c4-c0 | max raw | max paired | n>2 |")
for nd in nodes:
    raw=[];pr=[];mz=[]
    for c in ['c0','c1','c2','c3','c4']:
        d=J[(nd,c)]; pass
        g,z=G2(list(d.values())); raw.append(g); mz.append(z)
    for c in ['c1','c2','c3','c4']:
        d=J[(nd,c)]; b=J[(nd,'c0')]
        g,z=G2([d[k]-b[k] for k in sorted(d) if k in b]); pr.append(g)
    f=lambda v: 'nan(const)' if v!=v else f"{v:+.2f}"
    allv=[v for v in raw+pr if v==v]
    print(f"| {nd} | "+" | ".join(f(v) for v in raw)+" | "+" | ".join(f(v) for v in pr)+f" | {max(allv):+.2f} | | {sum(v>2*se for v in allv)}/{len(allv)} |")
