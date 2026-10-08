#!/usr/bin/env python3
"""b_v2 engineering/qualification validator. It validates; it never launches.

Later phases explicitly refuse. Qualification binds a prior engineering report
and authorization, not its own future report. Artifact hashes and lane/phase/
design bindings are checked. Resolved test fixtures are not real authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT=Path(__file__).with_name('contract_v2.yaml')
#: Active contract versions.  b_v3 (runbook step 3) adds the configurator block,
#: the offline/online budgets, the ledger schema and the posttrain partition on
#: top of b_v2; the phase logic is unchanged.
ACTIVE_VERSIONS=('b_v2','b_v3')
V3_REQUIRED_STRUCTURE=(
 'configurator.schema','configurator.feature_set','configurator.encoder','configurator.serialiser_fingerprint',
 'configurator.projection','configurator.fitted_on','configurator.encoder_weights_updated',
 'budgets.offline_collection','budgets.online_verification','ledger_schema','statistics.posttrain_partition')
V3_QUALIFICATION_REQUIRED=(
 'configurator.feature_set','configurator.encoder.slot','configurator.encoder.model','configurator.encoder.revision',
 'configurator.encoder.backend','configurator.serialiser_fingerprint','configurator.projection.mode',
 'budgets.offline_collection','budgets.online_verification','statistics.posttrain_partition')
LANES={'one_step','sequential'}
LATER_PHASES={'pilot','main_collection','final_evaluation'}
BUDGET_CAP_FIELDS=(
 'max_terminal_leaves','max_generated_tokens_all_calls',
 'max_aggregate_collection_wall_seconds','max_accelerator_hours',
 'max_new_retained_bytes','max_new_spend_commitment')
REQUIRED_STRUCTURE=(
 'protocol_version','record_schema','status','population.task_law','population.independent_unit',
 'population.checkpoint_rule','population.reachability_handling','population.condition_mixture',
  'runtime.model_revision','runtime.model_artifact_hash','runtime.harness_commit',
  'runtime.task_generator_hash','runtime.evaluator_revision','runtime.tool_versions',
  'runtime.state_boundary','runtime.continuation_revision','runtime.verifier_revision',
  'runtime.response_rule',
  'actions.continue','actions.verify_and_response','actions.verify_later',
 'outcomes.primary','outcomes.binary_success_definition','outcomes.utility_definition',
 'outcomes.invalid_and_missing_policy','allocation.mode','allocation.primary_capacity',
  'allocation.cost_definition','learning.feature_allowlist','learning.comparator_family',
  'learning.primary_comparators','learning.selection_rule','statistics.split_manifest',
 'statistics.primary_estimand','statistics.independent_unit_count','statistics.repetitions',
 'statistics.inference_method','statistics.multiplicity','statistics.safety_claim_level',
 'resources.runtime_ceiling','resources.storage_ceiling','resources.monetary_ceiling',
 'resources.retry_rule','qualification_report','freeze_commit','engineering','lanes','qualification',
 'replay_allowance.p','replay_allowance.provenance','replay_allowance.R')
QUALIFICATION_REQUIRED=(
 'population.task_law','population.checkpoint_rule','population.condition_mixture',
 'runtime.model_revision','runtime.model_artifact_hash','runtime.harness_commit',
 'runtime.task_generator_hash','runtime.evaluator_revision','runtime.tool_versions',
 'runtime.state_boundary','runtime.continuation_revision','runtime.verifier_revision',
 'runtime.response_rule',
 'outcomes.primary','outcomes.utility_definition','outcomes.invalid_and_missing_policy',
 'statistics.split_manifest','resources.retry_rule','freeze_commit')


def _get(c,key):
    for part in key.split('.'):
        if not isinstance(c,dict) or part not in c:return None,False
        c=c[part]
    return c,True


def load_contract(path=DEFAULT_CONTRACT):
    c=yaml.safe_load(Path(path).read_text())
    if not isinstance(c,dict):raise ValueError('contract must be a mapping')
    if c.get('protocol_version') not in ACTIVE_VERSIONS:raise ValueError(f"unknown protocol_version {c.get('protocol_version')!r}; active: {ACTIVE_VERSIONS}")
    return c


def required_structure(contract):
    keys=list(REQUIRED_STRUCTURE)
    if contract.get('protocol_version')=='b_v3':keys+=list(V3_REQUIRED_STRUCTURE)
    return tuple(keys)


def missing_required_fields(path=DEFAULT_CONTRACT):
    c=load_contract(path)
    return [key for key in required_structure(c) if not _get(c,key)[1]]


def binding_digest(contract,phase,lane):
    # Exclude reports/authorization references to avoid self-referential hashes.
    design={k:v for k,v in contract.items() if k not in {'qualification','qualification_report'}}
    qualification=contract.get('qualification',{}).get(lane,{})
    design['qualification_design']={k:v for k,v in qualification.items() if k not in {'authorization','engineering_report'}}
    payload={'phase':phase,'lane':lane,'contract':design}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _artifact(reference,base):
    if not isinstance(reference,dict) or not {'path','sha256'} <= set(reference):
        raise ValueError('missing artifact path/hash')
    name=reference.get('path');digest=reference.get('sha256')
    if not isinstance(name,str) or not isinstance(digest,str):raise ValueError('invalid artifact path/hash')
    path=(base/name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(base.resolve()):raise ValueError('artifact escapes validation root')
    if not path.is_file():raise ValueError(f'missing artifact: {name}')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError(f'stale artifact hash: {name}')
    data=yaml.safe_load(path.read_text())
    if not isinstance(data,dict):raise ValueError(f'artifact is not a mapping: {name}')
    return data


def _bound_record(reference,contract,phase,lane,base):
    record=_artifact(reference,base)
    if record.get('protocol_version')!=contract.get('protocol_version'):raise ValueError('unknown-version evidence')
    if record.get('lane')!=lane:raise ValueError('cross-lane evidence')
    if record.get('phase')!=phase:raise ValueError('cross-phase evidence')
    if record.get('design_sha256')!=binding_digest(contract,phase,lane):raise ValueError('stale design binding')
    return record


def budget_cap_errors(contract,usage):
    """Check measured usage against the registered budget caps.

    Later live phases call this before and during dispatch to enforce the first
    ceiling reached (terminal leaves, generated tokens, collection wall time,
    accelerator-hours, retained bytes, new-spend commitment).  It validates; it
    never launches.
    """
    caps=contract.get('resources',{}).get('budget_caps')
    if not isinstance(caps,dict):return ['budget_caps missing']
    if not isinstance(usage,dict):return ['usage must be a mapping']
    errors=[]
    for name in BUDGET_CAP_FIELDS:
        cap=caps.get(name)
        if cap is None:
            errors.append(f'missing budget cap: {name}');continue
        if isinstance(cap,bool) or not isinstance(cap,(int,float)) or not math.isfinite(cap) or cap<0:
            errors.append(f'invalid budget cap: {name}');continue
        value=usage.get(name)
        if value is None:
            errors.append(f'missing usage: {name}');continue
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            errors.append(f'invalid usage: {name}');continue
        if value>cap:
            errors.append(f'budget cap exceeded: {name} ({value} > {cap})')
    return errors


def validate_for_phase(contract,phase,lane,*,base_dir=ROOT):
    """Return refusal reasons; an empty list means only this local phase check passes."""
    if phase in LATER_PHASES:return ['phase not yet implemented']
    if phase not in {'engineering','qualification'}:return [f'unknown phase: {phase}']
    if lane not in LANES:return [f'unknown lane: {lane}']
    if not isinstance(contract,dict) or contract.get('protocol_version') not in ACTIVE_VERSIONS:return [f'unknown protocol_version; active: {ACTIVE_VERSIONS}']
    errors=[f'structural gap: {k}' for k in required_structure(contract) if not _get(contract,k)[1]]
    if errors:return errors
    if contract.get('record_schema') not in {'b_branch_v1','b_branch_v2'}:errors.append('unknown branch record_schema')
    if contract.get('status') not in {'draft','frozen'}:errors.append('unknown contract status')
    for section in ('engineering','lanes','qualification','runtime','outcomes','statistics','resources'):
        if not isinstance(contract.get(section),dict):return [f'invalid section: {section}']
    base=Path(base_dir)
    eng=contract.get('engineering',{})
    if not isinstance(eng,dict) or eng.get('banner')!='ENGINEERING_ONLY' or eng.get('backend')!='closed_fixture' or eng.get('external_runtime') is not False or eng.get('model_calls') is not False:
        errors.append('engineering requires ENGINEERING_ONLY closed fixture with no external runtime/model calls')
    lane_config=contract.get('lanes',{}).get(lane,{})
    if not isinstance(lane_config,dict):return ['invalid lane configuration']
    fixture=lane_config.get('engineering_fixture')
    if not isinstance(fixture,str) or not fixture or Path(fixture).is_absolute() or '..' in Path(fixture).parts or not (base/fixture).is_file():
        errors.append('missing lane engineering fixture')
    elif hashlib.sha256((base/fixture).read_bytes()).hexdigest()!=lane_config.get('engineering_fixture_sha256'):
        errors.append('stale engineering fixture hash')
    if lane_config.get('decision_count') != (1 if lane=='one_step' else 2):
        errors.append('invalid lane decision count')
    v3=contract.get('protocol_version')=='b_v3'
    if v3:
        cfg=contract.get('configurator',{})
        if not isinstance(cfg,dict) or cfg.get('schema')!='b_dac_configurator_v1':errors.append('configurator schema must be b_dac_configurator_v1')
        elif cfg.get('encoder_weights_updated') is not False:errors.append('configurator encoder weights must not be updated on evaluation families')
        elif cfg.get('fitted_on')!='development_families_only':errors.append('configurator must be fitted on development families only')
        if contract.get('ledger_schema')!='reliability-1.0':errors.append('unknown ledger_schema')
    if phase=='engineering':return errors
    if contract.get('status')!='frozen':errors.append('qualification requires frozen status; draft launches refused')
    for field in QUALIFICATION_REQUIRED+(V3_QUALIFICATION_REQUIRED if v3 else ()):
        value,present=_get(contract,field)
        if not present or value in (None,'',[],{}):errors.append(f'open qualification binding: {field}')
    if v3:
        fs=contract.get('configurator',{}).get('feature_set')
        if fs not in {'telemetry','embedding','telemetry+embedding'}:errors.append('unknown configurator feature_set')
        slot=contract.get('configurator',{}).get('encoder',{}).get('slot')
        if slot not in {'kev','clm_state_head','backbone_raw'}:errors.append('unknown configurator encoder slot')
    if contract.get('outcomes',{}).get('primary') not in {'S','U'}:errors.append('qualification primary outcome must be S or U')
    if contract.get('statistics',{}).get('safety_claim_level') not in {'empirical','none'}:errors.append('unsupported safety claim')
    for key,zero_allowed in [('runtime_ceiling',False),('storage_ceiling',False),('monetary_ceiling',True)]:
        value=contract.get('resources',{}).get(key)
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or (value<0 if zero_allowed else value<=0):
            errors.append(f'invalid bounded resource: {key}')
    q=contract.get('qualification',{}).get(lane,{})
    if not isinstance(q,dict):return errors+['invalid qualification lane']
    for name in ('pool','checks','units'):
        if q.get(name) in (None,'',[],{}):errors.append(f'missing qualification {name}')
    if type(q.get('units')) is not int or q.get('units',0)<=0:errors.append('qualification units must be a positive integer')
    try:
        pool=_artifact(q.get('pool'),base)
        splits=_artifact(contract.get('statistics',{}).get('split_manifest'),base)
        for record in (pool,splits):
            if record.get('protocol_version')!='b_v2' or record.get('lane')!=lane:
                errors.append('cross-lane or unknown-version qualification pool/split manifest')
        families=pool.get('template_families',[])
        partitions=splits.get('partitions',{})
        if pool.get('split')!='qualification' or not families or len(set(families))!=len(families):
            errors.append('invalid qualification pool')
        if len(families)!=q.get('units') or set(families)!=set(partitions.get('qualification',[])):
            errors.append('qualification pool/count/split mismatch')
        if v3 and 'posttrain' not in partitions:errors.append('b_v3 split manifest must list the posttrain partition')
        seen=set()
        for names in partitions.values():
            if not isinstance(names,list) or any(not isinstance(n,str) for n in names):
                errors.append('invalid split family list')
                continue
            if seen.intersection(names):errors.append('qualification split descendant leakage')
            seen.update(names)
    except (ValueError,OSError,yaml.YAMLError,TypeError,AttributeError) as exc:
        errors.append(f'qualification pool/split: {exc}')
    allowance=contract.get('replay_allowance',{})
    p=allowance.get('p')
    if p is not None and (isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1):errors.append('invalid replay allowance p')
    if type(allowance.get('R')) is not int or allowance.get('R',0)<1:errors.append('qualification requires positive replay R')
    try:
        provenance=_artifact(allowance.get('provenance'),base)
        if provenance.get('kind') not in {'measurement_plan','validated_evidence','sensitivity_assumption'}:
            errors.append('replay provenance requires a declared kind')
        if not provenance.get('method'):errors.append('replay provenance missing method')
        # Qualification may measure p; its own future report is never required.
        if p is None and provenance.get('kind')!='measurement_plan':errors.append('unmeasured p requires a measurement plan')
    except (ValueError,OSError,yaml.YAMLError) as exc:errors.append(f'replay provenance: {exc}')
    for field,record_phase in [('engineering_report','engineering'),('authorization','qualification')]:
        try:
            record=_bound_record(q.get(field),contract,record_phase,lane,base)
            if field=='engineering_report' and (record.get('passed') is not True or record.get('banner')!='ENGINEERING_ONLY'):
                errors.append('prior engineering report did not pass as ENGINEERING_ONLY')
            if field=='authorization' and (record.get('authorized') is not True or not record.get('authorized_by')):
                errors.append('qualification authorization not granted')
        except (ValueError,OSError,yaml.YAMLError) as exc:errors.append(f'{field}: {exc}')
    return errors


def launch_errors(path=DEFAULT_CONTRACT,*,phase='qualification',lane='one_step'):
    if phase=='engineering':return ['engineering validation does not authorize an external launch']
    try:return validate_for_phase(load_contract(path),phase,lane)
    except (ValueError,OSError,yaml.YAMLError) as exc:return [str(exc)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',default=str(DEFAULT_CONTRACT));p.add_argument('--phase',default='qualification')
    p.add_argument('--lane',default='one_step');p.add_argument('--for-launch',action='store_true');a=p.parse_args()
    try:
        c=load_contract(a.contract);missing=missing_required_fields(a.contract)
    except (ValueError,OSError,yaml.YAMLError) as exc:print('B-CONTRACT REFUSED:',exc);return 1
    if missing:print('B-CONTRACT STRUCTURAL FAIL:',missing);return 1
    errors=launch_errors(a.contract,phase=a.phase,lane=a.lane) if a.for_launch else validate_for_phase(c,a.phase,a.lane)
    print('B-CONTRACT structure: OK; phase:',a.phase,'lane:',a.lane)
    for error in errors:print('REFUSAL:',error)
    if not errors:print('B-CONTRACT PHASE CHECK PASS (validation only; no launch performed)')
    return int(bool(errors))


if __name__=='__main__':raise SystemExit(main())
