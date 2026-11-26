"""Freeze a caller-provided real-ledger prompt set before Stage A; never manufacture source provenance."""
import argparse
import json
from pathlib import Path
from r1.exam.guards import digest_file
from r1.exam.stage_a import load_prompts


def freeze(source, target):
    source=Path(source);target=Path(target)
    if target.exists() or Path(str(target)+'.sha256').exists(): raise ValueError('preserve existing frozen prompt set')
    sha=digest_file(source)
    # Production validation includes exact source hashes, memory mode, 50 prompts and >=4 nodes.
    load_prompts(source,sha)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    Path(str(target)+'.sha256').write_text(sha+'  '+target.name+'\n')
    return sha


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    a=p.parse_args(argv);print(freeze(a.source,a.out))

if __name__=='__main__': main()
