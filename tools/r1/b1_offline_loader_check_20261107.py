#!/usr/bin/env python3
"""Engineering-only offline OpenML cache loading; preserve all copied files."""
import hashlib
import os
from pathlib import Path
import shutil
import socket
import sys

FILES = {
 'openml_credit_approval': (29, (690, 15), {
  'api/v1/json/data/qualities/29.gz':'5e3213b47856a86b5087dc7a663624d9641a3bc6145d2dd79308f837890cc827',
  'api/v1/json/data/features/29.gz':'ffc560253f365d1d301d2eeaf86cd9fe1040f52d9e923ab73534adbadd21019c',
  'api/v1/json/data/29.gz':'5229a8b115c8bc536576a6d48086b3ef9bc57b673cb31fa26894cb6682c562dd',
  'data/v1/download/29/credit-approval.arff.gz':'b21f01872e3db3d90f775be77e431ccd3bfd96555ad09bcea49fcd558bb4fc4a'}),
 'openml_ionosphere': (59, (351, 34), {
  'api/v1/json/data/qualities/59.gz':'2e40aafecce975d3d09ead5eabec40956163cd9f81a39e70b78977ac101c9aa7',
  'api/v1/json/data/features/59.gz':'04154009932e0fd7ac67716c604b3d46ef551be85cfe5e47387596b33267ced1',
  'api/v1/json/data/59.gz':'2d18f98c5d0fe9b0f014d8cb6684c49b22d61ee11d398dd48eebefbc035260da',
  'data/v1/download/59/ionosphere.arff.gz':'40b4580d51a1815c9d1bea32cc579d523ea98af8c80a06a345e192729359644e'})}
FALLBACK = 'experiments/r1/pilot/L8_20261009T152916Z/nodes'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()

def safe_file(root,relative):
 cur=root
 for part in relative.parts:
  cur=cur/part
  if cur.is_symlink(): raise RuntimeError('symlink in source path')
 if not cur.is_file(): raise RuntimeError('source is not regular file')
 return cur

def deny(*args,**kwargs):
 raise RuntimeError('network operation denied by offline loader check')

def main(root,dest):
 if root.is_symlink() or not root.is_dir(): raise RuntimeError('unsafe harness root')
 dest.mkdir(mode=0o700)
 for node,(dataid,shape,files) in FILES.items():
  node_cache = root/'nodes'/node/'data_cache'
  if node_cache.exists() or node_cache.is_symlink(): raise RuntimeError('node cache shadows fallback')
  for relative,expected in sorted(files.items()):
   rel=Path(FALLBACK)/node/'data_cache'/'openml/openml.org'/relative
   src=safe_file(root,rel)
   if sha(src)!=expected: raise RuntimeError('source hash mismatch: '+node+'/'+relative)
   dst=dest/node/'openml/openml.org'/relative
   dst.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
   with src.open('rb') as f, dst.open('xb') as g: shutil.copyfileobj(f,g)
   if sha(dst)!=expected: raise RuntimeError('copy hash mismatch')
   print('BEFORE',node,relative,expected,flush=True)
 socket.socket.connect=deny
 socket.socket.connect_ex=deny
 socket.create_connection=deny
 socket.getaddrinfo=deny
 from sklearn.datasets import fetch_openml
 import sklearn
 print('PYTHON',sys.executable,'PREFIX',sys.prefix,'SKLEARN',sklearn.__version__,flush=True)
 if sys.prefix != '/home/dowling/exam-x/work/venv': raise RuntimeError('wrong venv prefix')
 try:
  for node,(dataid,shape,files) in FILES.items():
   data=fetch_openml(data_id=dataid,as_frame=True,parser='auto',data_home=str(dest/node))
   print('LOADED',node,'shape',data.data.shape,'target_length',len(data.target),flush=True)
   if data.data.shape!=shape or len(data.target)!=shape[0]: raise RuntimeError('unexpected shape')
 finally:
  for node,(_,_,files) in FILES.items():
   for relative,expected in sorted(files.items()):
    path=dest/node/'openml/openml.org'/relative
    value=sha(path)
    print('AFTER',node,relative,value,flush=True)
    if value!=expected: raise RuntimeError('cache changed during load')
 print('OFFLINE_LOADER_PASS',flush=True)

if __name__=='__main__':
 if len(sys.argv)!=3: raise SystemExit('usage: HARNESS NEW_DEST')
 main(Path(sys.argv[1]),Path(sys.argv[2]))
