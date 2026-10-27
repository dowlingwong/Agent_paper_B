from xml.etree import ElementTree as ET
from collections import Counter
from pathlib import Path
pre=Path('/private/tmp/paper-b-prescaffold-20261027')
post=Path('/private/tmp/paper-b-corrected-paper-20261027')
def read(path):
 out={}
 for c in ET.parse(path).getroot().iter('testcase'):
  status='passed'; detail=''
  for s in ('failure','error','skipped'):
   e=c.find(s)
   if e is not None:
    status={'failure':'failed','error':'error','skipped':'skipped'}[s]
    detail=(e.get('message') or e.text or '').splitlines()[0]; break
  out[c.get('classname')+'::'+c.get('name')]=(status,detail)
 return out
for file in ('junit.xml','focused-junit.xml'):
 a,b=read(pre/file),read(post/file)
 print('\n'+file+' PRE',dict(Counter(x[0] for x in a.values())),'POST',dict(Counter(x[0] for x in b.values())))
 print('PRE only',len(a.keys()-b.keys()))
 for k in sorted(a.keys()-b.keys()): print('  ',k,a[k])
 print('POST only',len(b.keys()-a.keys()))
 for k in sorted(b.keys()-a.keys()): print('  ',k,b[k])
 common=a.keys()&b.keys(); changes=[(k,a[k],b[k]) for k in sorted(common) if a[k][0]!=b[k][0]]
 print('COMMON',len(common),'status changes',len(changes))
 for k,x,y in changes:print('  ',k,x,'->',y)
 print('SAME STATUS MESSAGE DIFFERENCES')
 for k in sorted(common):
  if a[k][0]==b[k][0] and a[k][1]!=b[k][1]:print('  ',k,a[k],'=>',b[k])
