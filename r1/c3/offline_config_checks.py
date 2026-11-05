"""Non-numerical configuration checks for all 16 M3 replay cases.

These checks never call a worker, estimator, model or network. They validate
against the actual pinned harness nodes but cannot establish dependency
closure, a complete data cache or absence of configuration-dependent I/O during
worker execution. This is not offline-executability evidence; STOP remains.
"""
from __future__ import annotations
import ast
import copy
import json
import math
import subprocess

import yaml
from r1.c3.offline_cases import bind_cases, CaseStop
from r1.c3.offline_preflight import HARNESS_COMMIT


class ConfigStop(RuntimeError): pass


def _git(harness, *args):
    try:return subprocess.check_output(['git','-C',str(harness),*args],stderr=subprocess.DEVNULL)
    except (OSError,subprocess.CalledProcessError) as exc:raise ConfigStop('STOP: pinned harness content unavailable') from exc


def _openml_config(text,spec):
    try:cfg=yaml.safe_load(text)
    except yaml.YAMLError as exc:raise ConfigStop('STOP: invalid YAML configuration') from exc
    if not isinstance(cfg,dict):raise ConfigStop('STOP: configuration must be a mapping')
    allowed=spec.get('allowed_values') or {};ranges=spec.get('allowed_ranges') or {}
    required=set(allowed)|set(ranges)
    if not required or not required<=set(cfg):raise ConfigStop('STOP: missing configuration keys')
    for key,values in allowed.items():
        if cfg[key] not in values:raise ConfigStop(f'STOP: invalid configuration value for {key}')
    for key,bounds in ranges.items():
        try:value=float(cfg[key])
        except (TypeError,ValueError) as exc:raise ConfigStop(f'STOP: invalid numeric configuration for {key}') from exc
        if not math.isfinite(value) or not bounds[0]<=value<=bounds[1]:
            raise ConfigStop(f'STOP: out-of-range configuration for {key}')


def _mlp_config(text,baseline,spec):
    names=set(spec.get('editable_symbols') or [])
    if names!={'HIDDEN_UNITS','ALPHA','LEARNING_RATE_INIT','BATCH_SIZE','MAX_ITER'}:
        raise ConfigStop('STOP: unknown editable MLP symbols')
    try:tree=ast.parse(text);fixed=ast.parse(baseline)
    except SyntaxError as exc:raise ConfigStop('STOP: invalid MLP source syntax') from exc
    def normalized(tree):
        tree=copy.deepcopy(tree);values={}
        for statement in tree.body:
            if not isinstance(statement,ast.Assign) or len(statement.targets)!=1 or not isinstance(statement.targets[0],ast.Name):continue
            name=statement.targets[0].id
            if name not in names:continue
            if name in values:raise ConfigStop('STOP: duplicate editable MLP symbol')
            try:value=ast.literal_eval(statement.value)
            except (ValueError,TypeError) as exc:raise ConfigStop('STOP: MLP symbol must be a literal') from exc
            if type(value) not in (int,float) or not math.isfinite(value):
                raise ConfigStop('STOP: MLP symbol must be finite numeric')
            values[name]=value;statement.value=ast.Constant(value=0)
        if set(values)!=names:raise ConfigStop('STOP: missing editable MLP symbol')
        if any(values[k]<=0 for k in ('HIDDEN_UNITS','LEARNING_RATE_INIT','BATCH_SIZE','MAX_ITER')) or values['ALPHA']<0:
            raise ConfigStop('STOP: invalid MLP parameter range')
        return ast.dump(tree,include_attributes=False)
    if normalized(tree)!=normalized(fixed):raise ConfigStop('STOP: non-editable MLP code changed')


def check_cases(cases,cache_snapshots,harness):
    """Check every selected config against pinned node schema and source."""
    try:binding=bind_cases(cases,cache_snapshots)
    except CaseStop as exc:raise ConfigStop(str(exc)) from exc
    if _git(harness,'rev-parse','HEAD').decode().strip()!=HARNESS_COMMIT:
        raise ConfigStop('STOP: wrong harness commit')
    checks=[]
    for case in cases:
        node=case['node']
        if not isinstance(node,str) or not node.replace('_','').isalnum():
            raise ConfigStop('STOP: invalid node identity')
        try:spec=json.loads(_git(harness,'show',f'{HARNESS_COMMIT}:configs/nodes/{node}.yaml'))
        except (ValueError,TypeError) as exc:raise ConfigStop('STOP: invalid pinned node schema') from exc
        if spec.get('name')!=node or spec.get('run_command')!=case['worker_command']:
            raise ConfigStop('STOP: node identity or worker command mismatch')
        if set(spec.get('editable_paths') or [])!=set(case['files']):
            raise ConfigStop('STOP: editable file scope mismatch')
        if node.startswith('openml_'):
            if set(case['files'])!={'config.yaml'}:raise ConfigStop('STOP: unexpected OpenML editable files')
            _openml_config(case['files']['config.yaml'],spec)
        elif node in ('digits_mlp','tabular_mlp'):
            if set(case['files'])!={'train.py'}:raise ConfigStop('STOP: unexpected MLP editable files')
            baseline=_git(harness,'show',f'{HARNESS_COMMIT}:nodes/{node}/train.py').decode()
            _mlp_config(case['files']['train.py'],baseline,spec)
        else:raise ConfigStop('STOP: unsupported selected node')
        checks.append({'case_id':case['case_id'],'node':node,'configuration_shape':'PASS',
                       'command':case['worker_command']})
    return {'schema':'m3_config_check/v1','binding_sha256':binding['binding_sha256'],
            'checks':sorted(checks,key=lambda item:item['case_id']),
            'offline_executability':'NOT_ESTABLISHED'}
