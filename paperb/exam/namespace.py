"""Fail-closed EXAM/C3 separation, including unlabelled exam-seed ledgers."""
import re

INSTANCE_SEEDS = range(9001, 9100)
AUDIT_SEEDS = range(9101, 9300)
EXAM_SEEDS = set(INSTANCE_SEEDS) | set(AUDIT_SEEDS)
_SEED_KEYS = {'seed', 'instance_seed', 'train_seed', 'split_seed', 'seeds', 'instance_seeds', 'audit_seeds'}


def refuse_exam(value, *, context='C3 source', seed_field=False):
    if isinstance(value, dict):
        if str(value.get('label', '')).upper() == 'EXAM':
            raise ValueError(f'{context}: EXAM campaigns must never enter C3')
        for key, item in value.items():
            refuse_exam(item, context=context, seed_field=key in _SEED_KEYS)
    elif isinstance(value, (list, tuple)):
        for item in value:
            refuse_exam(item, context=context, seed_field=seed_field)
    elif (seed_field and isinstance(value, (int, str)) and str(value).isdigit()
          and int(value) in EXAM_SEEDS):
        raise ValueError(f'{context}: exam seed {value} must never enter C3')
    elif isinstance(value, str):
        if any(int(s) in EXAM_SEEDS for s in re.findall(r'__s(\d+)(?:\D|$)', value)):
            raise ValueError(f'{context}: exam instance {value} must never enter C3')


def check_exam_seeds(instances, audits):
    if not instances or len(set(instances)) != len(instances) or not set(instances) <= set(INSTANCE_SEEDS):
        raise ValueError('EXAM instances must be unique seeds 9001–9099')
    if not audits or len(set(audits)) != len(audits) or not set(audits) <= set(AUDIT_SEEDS):
        raise ValueError('EXAM audits must be unique seeds 9101–9299')
