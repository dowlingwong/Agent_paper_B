import hashlib, json, pathlib, sys
P = pathlib.Path(sys.argv[1]); B = pathlib.Path(sys.argv[2]); H = B / 'autoresearch_harness'
audit = json.loads((P / 'docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_AUDIT.json').read_text())
per = audit['current_cache_observation']['per_file_sha256']
tree_pin = audit['current_cache_observation']['tree_digest_driver_algorithm']
ALLOWED = {'.gitignore', '.gitkeep'}
def tree_digest(root):
    h = hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode() + b'\0' + p.read_bytes() + b'\0')
    return h.hexdigest()
allok = True
for node in sorted(per):
    root = H / 'nodes' / node / 'data_cache'
    files = {}
    for p in sorted(root.rglob('*')):
        if p.is_file():
            rel = str(p.relative_to(root))
            files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    extra = sorted(set(files) - set(per[node]))
    unexpected = [e for e in extra if not (('/' not in e) and e in ALLOWED)]
    missing = sorted(set(per[node]) - set(files))
    mismatch = sorted(k for k, v in per[node].items() if files.get(k) != v)
    td = tree_digest(root)
    ok = not unexpected and not missing and not mismatch and td == tree_pin[node]
    allok = allok and ok
    print(f"{node}: audited_files_match={not missing and not mismatch} allowed_dotfiles={extra} unexpected={unexpected} tree_matches_audit={td == tree_pin[node]} tree={td}")
print("ALL_SIX_CACHES_UNCHANGED_AND_AUDITED =", allok)
