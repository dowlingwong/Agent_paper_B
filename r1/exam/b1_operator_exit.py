"""Classify an observed supervisor exit for an operator, without mutations.

This is not the complete-batch verifier and cannot infer the absence of STOPs
from missing files; the operator must inspect the retained process/log scene.
"""
import argparse
import json
import os
from pathlib import Path
import sys

from r1.exam.b1_exit_receipt import UNCERTAIN, read_owned_regular, verify_waited_success


def _exists_checked(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    return True


def classify_supervisor_exit(batch, supervisor_dir, head, observed_exit):
    """Use bound receipts to classify an exit; actual exit is operator supplied."""
    batch, supervisor_dir = Path(batch), Path(supervisor_dir)
    if (not batch.is_absolute() or not supervisor_dir.is_absolute()
            or batch.resolve(strict=True) != batch or supervisor_dir.resolve(strict=True) != supervisor_dir
            or batch.parent != supervisor_dir.parent or type(observed_exit) is not int):
        raise ValueError('STOP: operator exit inputs are not canonical')
    binding_path=supervisor_dir/'SUPERVISOR.json'
    binding_raw=read_owned_regular(binding_path)
    binding=json.loads(binding_raw)
    if (not isinstance(binding,dict) or binding.get('head')!=head or binding.get('out')!=str(batch)
            or type(binding.get('pid')) is not int or binding['pid']<=0
            or type(binding.get('start_ticks')) is not int or binding['start_ticks']<=0):
        raise ValueError('STOP: supervisor directory does not bind the batch and HEAD')
    stops=(supervisor_dir/'SUPERVISOR_STOP.json', batch/'STOP.json', batch/UNCERTAIN)
    common={'observed_exit':observed_exit,'operator_must_check_logs_for_stop':True,
            'requires_handover_restoration':True,'requires_complete_batch_verifier':True}
    if any(_exists_checked(path) for path in stops):
        return {'classification':'STOP_OR_UNCERTAIN',**common}
    verify_waited_success(batch,head)
    if any(_exists_checked(path) for path in stops) or read_owned_regular(binding_path)!=binding_raw:
        raise ValueError('STOP: supervisor disposition changed while being checked')
    return {'classification':('COMMITTED_NORMAL_EXIT' if observed_exit==0 else
                              'COMMITTED_NONZERO_EXIT_OPERATIONAL_ISSUE'),**common}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',required=True)
    parser.add_argument('--supervisor-dir',required=True)
    parser.add_argument('--head',required=True)
    parser.add_argument('--observed-exit',required=True,type=int)
    args=parser.parse_args(argv)
    try:
        result=classify_supervisor_exit(args.batch,args.supervisor_dir,args.head,args.observed_exit)
    except (OSError,ValueError,RuntimeError,TypeError) as exc:
        print(json.dumps({'classification':'NOT_CHECKABLE','reason':str(exc)},sort_keys=True))
        return 2
    print(json.dumps(result,sort_keys=True))
    return 1 if result['classification']=='STOP_OR_UNCERTAIN' else 0


if __name__=='__main__':
    sys.exit(main())
