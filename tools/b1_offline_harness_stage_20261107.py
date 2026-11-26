#!/usr/bin/env python3
"""Pack locally; receive and extract once on site. Never touches existing checkout."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

PIN = 'a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
FALLBACK = 'experiments/r1/pilot/L8_20261009T152916Z/nodes'
FILES = {
 'openml_credit_approval/openml/openml.org/api/v1/json/data/qualities/29.gz':'5e3213b47856a86b5087dc7a663624d9641a3bc6145d2dd79308f837890cc827',
 'openml_credit_approval/openml/openml.org/api/v1/json/data/features/29.gz':'ffc560253f365d1d301d2eeaf86cd9fe1040f52d9e923ab73534adbadd21019c',
 'openml_credit_approval/openml/openml.org/api/v1/json/data/29.gz':'5229a8b115c8bc536576a6d48086b3ef9bc57b673cb31fa26894cb6682c562dd',
 'openml_credit_approval/openml/openml.org/data/v1/download/29/credit-approval.arff.gz':'b21f01872e3db3d90f775be77e431ccd3bfd96555ad09bcea49fcd558bb4fc4a',
 'openml_ionosphere/openml/openml.org/api/v1/json/data/qualities/59.gz':'2e40aafecce975d3d09ead5eabec40956163cd9f81a39e70b78977ac101c9aa7',
 'openml_ionosphere/openml/openml.org/api/v1/json/data/features/59.gz':'04154009932e0fd7ac67716c604b3d46ef551be85cfe5e47387596b33267ced1',
 'openml_ionosphere/openml/openml.org/api/v1/json/data/59.gz':'2d18f98c5d0fe9b0f014d8cb6684c49b22d61ee11d398dd48eebefbc035260da',
 'openml_ionosphere/openml/openml.org/data/v1/download/59/ionosphere.arff.gz':'40b4580d51a1815c9d1bea32cc579d523ea98af8c80a06a345e192729359644e'}

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()

def cache_path(root, name):
 node,rel=name.split('/',1)
 return root/FALLBACK/node/'data_cache'/rel

def check(root):
 out=subprocess.check_output(['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),'rev-parse','HEAD'],text=True).strip()
 if out!=PIN: raise RuntimeError('wrong HEAD')
 out=subprocess.check_output(['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),'status','--porcelain','--untracked-files=all'],text=True)
 if out: raise RuntimeError('dirty checkout: '+out)
 for name,sha in FILES.items():
  p=cache_path(root,name)
  if not p.is_file() or p.is_symlink() or digest(p)!=sha: raise RuntimeError('cache mismatch: '+name)
 print('PIN, clean status and eight cache SHA256: PASS',flush=True)

def pack(source,caches,dest):
 dest.mkdir(mode=0o700) # exclusive destination; preserve on any failure
 root=dest/'harness'
 subprocess.run(['git','clone','--no-local','--no-hardlinks','--no-checkout',str(source),str(root)],check=True)
 subprocess.run(['git','-C',str(root),'checkout','--detach',PIN],check=True)
 subprocess.run(['git','-C',str(root),'remote','remove','origin'],check=True)
 for name,sha in FILES.items():
  src=cache_path(caches,name)
  if src.is_symlink() or digest(src)!=sha: raise RuntimeError('source cache mismatch: '+name)
  dst=cache_path(root,name); dst.parent.mkdir(parents=True,exist_ok=True)
  with src.open('rb') as f, dst.open('xb') as g: shutil.copyfileobj(f,g)
 check(root)
 archive=dest/'payload.tar'
 with tarfile.open(archive,'x') as tar:
  for parent,dirs,files in os.walk(root,followlinks=False,onerror=lambda e: (_ for _ in ()).throw(e)):
   dirs.sort(); files.sort()
   for item in dirs+files:
    p=Path(parent)/item
    if p.is_symlink() or not (p.is_dir() or p.is_file()): raise RuntimeError('unsafe entry: '+str(p))
    tar.add(p,arcname=str(p.relative_to(dest)),recursive=False)
 print('PAYLOAD',archive,'SHA256',digest(archive),flush=True)

def receive(dest,expected):
 # Parent is fixed by operator and checked before starting; never reuse destination.
 dest.mkdir(mode=0o700)
 archive=dest/'payload.tar'
 with archive.open('xb') as f: shutil.copyfileobj(sys.stdin.buffer,f)
 if digest(archive)!=expected: raise RuntimeError('payload hash mismatch')
 with tarfile.open(archive,'r:') as tar:
  entries=tar.getmembers(); seen=set()
  for m in entries:
   p=PurePosixPath(m.name)
   if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0]!='harness' or m.name in seen or not (m.isfile() or m.isdir()): raise RuntimeError('unsafe archive member: '+m.name)
   seen.add(m.name)
  (dest/'harness').mkdir(mode=0o700)
  for m in entries:
   p=dest.joinpath(*PurePosixPath(m.name).parts)
   if m.isdir(): p.mkdir(mode=0o700,parents=True,exist_ok=True)
   else:
    p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with tar.extractfile(m) as src, p.open('xb') as dst: shutil.copyfileobj(src,dst)
    os.chmod(p,m.mode & 0o777)
 check(dest/'harness')
 print('STAGED',dest/'harness',flush=True)

if __name__=='__main__':
 if len(sys.argv)==5 and sys.argv[1]=='pack': pack(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]))
 elif len(sys.argv)==4 and sys.argv[1]=='receive': receive(Path(sys.argv[2]),sys.argv[3])
 else: raise SystemExit('usage: pack SOURCE CACHE_ROOT NEW_DEST | receive NEW_DEST SHA256')
