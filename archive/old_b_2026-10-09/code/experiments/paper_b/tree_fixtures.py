#!/usr/bin/env python3
"""CPU-only three-leaf fixture driver; never trains or calls a model."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiment_scaffold/src'))
from causal_branch.control.tree import fixtures, summarize

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('phase_validator',ROOT/'protocols/paper_b/launch_validator.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    c=v.load_contract();errors=v.validate_for_phase(c,'engineering','sequential')
    if errors: raise SystemExit('; '.join(errors))
    trees=fixtures();summary=summarize(trees)
    summary.update(protocol_version='b_v2',lane='sequential',phase='engineering',passed=True,
                   design_sha256=v.binding_digest(c,'engineering','sequential'),
                   note='Fixed fixture regimes only; no sequential learner; no scientific result')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'trees.json').write_text(json.dumps(trees,indent=2)+'\n')
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('ENGINEERING_ONLY: 8 fixed trees validated')

if __name__=='__main__': main()
