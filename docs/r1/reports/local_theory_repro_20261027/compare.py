import json, pathlib, math, collections, difflib
root=pathlib.Path('.')
ref3=root/'results/r1/engineering/T3_20261012T161444Z'; out3=root/'output-t3'
ref5=root/'results/r1/engineering/T5_20261019T004918Z'; out5=root/'output-t5'
def compare(a,b,path='',diff=None):
 if diff is None: diff=[]
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(set(a)|set(b)):
   if k=='_seconds': continue
   if k not in a or k not in b: diff.append((path+'/'+k,'missing',None)); continue
   compare(a[k],b[k],path+'/'+k,diff)
 elif isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b): diff.append((path,'length', (len(a),len(b))))
  for i,(x,y) in enumerate(zip(a,b)): compare(x,y,path+'/'+str(i),diff)
 elif isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
  if a!=b and not (math.isnan(a) and math.isnan(b)): diff.append((path,'numeric',(a,b,abs(a-b))))
 elif a!=b: diff.append((path,'other',(a,b)))
 return diff
for label,r,o in [('T3',ref3,out3),('T5',ref5,out5)]:
 if label=='T3': pairs=[('results.json',r/'results.json',o/'results.json')]; tables=['table.md']
 else:
  names=sorted({p.name for p in (r/'parts').glob('*.json')} | {p.name for p in (o/'parts').glob('*.json')}); pairs=[(n,r/'parts'/n,o/'parts'/n) for n in names]; tables=['tables.md']
 all_diff=[]; missing=[]
 for n,a,b in pairs:
  if not a.exists() or not b.exists(): missing.append(n); continue
  ds=compare(json.loads(a.read_text()),json.loads(b.read_text()))
  all_diff.extend((n,*d) for d in ds)
 print(label,'files_compared',len(pairs)-len(missing),'missing',len(missing),'fields_differing',len(all_diff),'kinds',dict(collections.Counter(x[2] for x in all_diff)))
 nums=[x for x in all_diff if x[2]=='numeric']; nums.sort(key=lambda x:x[3][2],reverse=True)
 print('numeric_differences',nums); print('other_differences',[x for x in all_diff if x[2]!='numeric'])
 for t in tables:
  if (o/t).exists():
   x=(r/t).read_text().splitlines(); y=(o/t).read_text().splitlines(); diff=list(difflib.unified_diff(x,y,fromfile='reference',tofile='regenerated',lineterm='')); print(t,'identical',x==y,'diff_lines',len(diff)); (root/(label.lower()+'-table.diff')).write_text('\n'.join(diff)+'\n')
