import hashlib, os, stat, sys, tarfile
from pathlib import Path, PurePosixPath

def verify(archive, root, expected_sha):
    archive, root = Path(archive), Path(root)
    if root.is_symlink() or not root.is_dir(): raise SystemExit('STOP: unsafe root')
    with archive.open('rb') as src:
        h=hashlib.sha256()
        for part in iter(lambda:src.read(1024*1024),b''): h.update(part)
        if h.hexdigest()!=expected_sha: raise SystemExit('STOP: archive SHA mismatch')
        src.seek(0)
        with tarfile.open(fileobj=src,mode='r:') as tar:
            files={}; dirs={'.'}; names=set()
            for member in tar.getmembers():
                p=PurePosixPath(member.name)
                if p.is_absolute() or not p.parts or '..' in p.parts or not (member.isdir() or member.isfile()):
                    raise SystemExit('STOP: unsafe archive member '+member.name)
                name=p.as_posix()
                if name in names: raise SystemExit('STOP: duplicate archive path '+name)
                names.add(name)
                for parent in p.parents: dirs.add(parent.as_posix())
                if member.isdir(): dirs.add(name)
                else:
                    content=tar.extractfile(member)
                    h=hashlib.sha256()
                    for block in iter(lambda:content.read(1024*1024),b''): h.update(block)
                    files[name]=h.hexdigest()
            seen_files=set(); seen_dirs={'.'}; caches=[]
            for current, subdirs, names in os.walk(root, followlinks=False):
                parent=Path(current).relative_to(root).as_posix()
                for name in subdirs:
                    path=Path(current)/name; rel=path.relative_to(root).as_posix()
                    if not stat.S_ISDIR(path.lstat().st_mode): raise SystemExit('STOP: non-directory or symlink '+rel)
                    if rel in dirs: seen_dirs.add(rel)
                    elif name=='__pycache__' and parent in dirs: caches.append(rel+'/')
                    else: raise SystemExit('STOP: extra directory '+rel)
                for name in names:
                    path=Path(current)/name; rel=path.relative_to(root).as_posix()
                    if not stat.S_ISREG(path.lstat().st_mode): raise SystemExit('STOP: non-regular or symlink '+rel)
                    if rel not in files:
                        if parent.endswith('/__pycache__') and parent.rsplit('/',1)[0] in dirs and name.endswith('.pyc'):
                            caches.append(rel); continue
                        raise SystemExit('STOP: extra file '+rel)
                    fd=os.open(path,os.O_RDONLY | os.O_NOFOLLOW)
                    try:
                        if not stat.S_ISREG(os.fstat(fd).st_mode): raise SystemExit('STOP: non-regular '+rel)
                        h=hashlib.sha256()
                        while True:
                            block=os.read(fd,1024*1024)
                            if not block: break
                            h.update(block)
                    finally: os.close(fd)
                    if h.hexdigest()!=files[rel]: raise SystemExit('STOP: changed file '+rel)
                    seen_files.add(rel)
            if seen_files!=set(files) or seen_dirs!=dirs:
                raise SystemExit('STOP: missing archive files or directories')
            for item in sorted(caches): print('CACHE',item)
            print('PASS archive='+str(archive)+' files='+str(len(files))+' cache_entries='+str(len(caches)))

if len(sys.argv) != 7: raise SystemExit("STOP: expected two archive/root/SHA triples")
verify(*sys.argv[1:4])
verify(*sys.argv[4:7])
