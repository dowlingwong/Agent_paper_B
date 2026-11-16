#!/usr/bin/env python3
"""Read-only hash check of precisely the staged B1 caches."""
import base64
import sys
from pathlib import Path

scope={'__name__':'loader_verification_only'}
exec(base64.b64decode(sys.argv[1],validate=True),scope)
root=Path('/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness')
for ancestor in [Path('/home'),Path('/home/dowling'),root.parent.parent,root.parent,root]:
 if ancestor.is_symlink() or not ancestor.is_dir(): raise RuntimeError('unsafe root ancestor')
for node,(_,_,files) in scope['FILES'].items():
 local=root/'nodes'/node/'data_cache'
 if local.exists() or local.is_symlink(): raise RuntimeError('node cache shadows fallback')
 for rel,expected in sorted(files.items()):
  path=scope['safe_file'](root,Path(scope['FALLBACK'])/node/'data_cache'/'openml/openml.org'/rel)
  actual=scope['sha'](path)
  print('CURRENT',node,rel,actual,flush=True)
  if actual!=expected: raise RuntimeError('cache digest mismatch')
print('EIGHT_SOURCE_HASHES_MATCH',flush=True)
