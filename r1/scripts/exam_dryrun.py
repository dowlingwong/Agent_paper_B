#!/usr/bin/env python3
"""Two fake model candidates + three anchors, Stage A/B1, one killed root and whole-root resume."""
from __future__ import annotations
import argparse
import copy
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import yaml
from r1.harness import import_harness
import_harness()
from autoresearch.manager.langgraph_manager import manager_seed
from r1.exam.guards import digest_file
from r1.exam.campaign import write_json
from r1.exam.runtime import APPROVED_EXAM_HOSTS, DEFAULT_CONFIG, REPO, _dryrun_temp_roots

SELECTED=['random_valid','scripted','qwen25_coder_7b','qwen38_27b','gemma4_31b']


def _require_development_host():
    if platform.node().split('.')[0].casefold() in ({host.casefold() for host in APPROVED_EXAM_HOSTS}|{'ucrtasl'}):
        raise RuntimeError('development host only')


def prepare(root):
    _require_development_host()
    root=Path(root).resolve()
    if not any(root!=t and root.is_relative_to(t) for t in _dryrun_temp_roots()): raise RuntimeError('DRYRUN root must be a temporary child directory')
    if root.exists() and any(root.iterdir()): raise RuntimeError('preserve the earlier DRYRUN; use a fresh root')
    root.mkdir(parents=True,exist_ok=True);(root/'.dryrun').write_text('EXAM DRYRUN; no inference\n')
    models=root/'models';models.mkdir(exist_ok=True)
    binary=root/'fake_llama_server'
    binary.write_text(f'#!{sys.executable}\nimport runpy\nrunpy.run_path({str(REPO/"r1/scripts/c3_fake_llama_server.py")!r},run_name="__main__")\n')
    binary.chmod(0o755)
    registry=yaml.safe_load((REPO/'r1/exam/registry.yaml').read_text())
    for row in registry['candidates']:
        if row['id'] in SELECTED:
            model=models/(row['id']+'.gguf');model.write_bytes(b'EXAM DRYRUN fixture; no tensors\n')
            row['runtime']={'model_path':str(model),'footprint_mib':'TODO_VERIFY_ON_HOST' if row['id']=='qwen38_27b' else 1}
            row['quant_source']={'sha256':digest_file(model),'quantization':'Q4_K_M','kind':'DRYRUN'}
            row['thinking_policy']={'mode':'off','budget':0,'off_switch':True,'switchable':row['id']=='qwen38_27b'}
    registry_path=root/'registry.yaml';registry_path.write_text(json.dumps(registry,indent=2))
    prompts=root/'prompts.jsonl';rows=[]
    nodes=['digits_mlp','openml_credit_approval','openml_ionosphere','tabular_mlp']
    for i in range(50):
        node=nodes[i%4];key='C' if node.startswith('openml_') else 'MAX_ITER';old='1.0' if key=='C' else '40'
        rows.append({'id':i,'node':node,'active_keys':[key],
                     'prompt':f'Node: {node}\nBudget index (trial number): {i+1}\n  {key} = {old}\n',
                     'seed':manager_seed(f'{node}__s9001',i+1),'source':'DRYRUN_SYNTHETIC_NOT_LEDGER_EVIDENCE'})
    prompts.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    cfg=json.loads(DEFAULT_CONFIG.read_text())
    cfg.update(dryrun=True,dryrun_root=str(root),host='DRYRUN',models_dir=str(models),work_dir=str(root/'work'),gpu_uuid='GPU-DRYRUN',
               registry=str(registry_path),rule=str(REPO/'r1/exam/rules/x5_rule_v1.yaml'),value_grids=str(REPO/'r1/exam/value_grids.yaml'),
               paper_commit='DRYRUN',harness_commit='DRYRUN',prompts=str(prompts),prompts_sha256=digest_file(prompts),
               W=4,llm_call_cap=24,nodes=['digits_mlp','openml_credit_approval'],instance_seeds=[9001],
               stage_a_table=str(root/'stage-a/stage_a_table.json'),
               anchor_duplicate_reference={'source':'DRYRUN','sha256':'DRYRUN','lower':0.,'upper':1.})
    cfg['server']={'binary':str(binary),'binary_sha256':digest_file(binary),'build':'version: 0 (DRYRUN)','start_timeout':10}
    path=root/'config.json';write_json(path,cfg)
    return path


def run(root):
    _require_development_host()
    root=Path(root).resolve()
    config=prepare(root)
    env={**os.environ,'R1_FAKE_OLLAMA_ROOT':str(root),'PYTHONPATH':str(REPO),'PYTHONDONTWRITEBYTECODE':'1'}
    args=[sys.executable,'-m','r1.scripts.exam_runner']
    selected=[arg for name in SELECTED for arg in ('--candidate',name)]
    def command(phase,out,*extra):
        with (root/f'{phase}_{len(list(root.glob(phase+"_*.log")))}.log').open('w') as log:
            return subprocess.run([*args,phase,'--config',str(config),'--out',str(out),*selected,*extra],cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
    stage_code=command('stage-a',root/'stage-a')
    if stage_code: raise RuntimeError(f'Stage A DRYRUN failed; see {root}/stage-a_0.log')
    cfg=json.loads(config.read_text());cfg['stage_a_table_sha256']=digest_file(root/'stage-a/stage_a_table.json');write_json(config,cfg)
    interrupted=command('b1',root/'b1','--interrupt-root')
    before=json.loads((root/'b1/batch_state.json').read_text())
    preserved={key:digest_file(entry['path']) for key,entry in before['completed'].items()}
    resumed=command('b1',root/'b1')
    after=json.loads((root/'b1/batch_state.json').read_text())
    stages=json.loads((root/'stage-a/stage_a_table.json').read_text())['rows']
    checks={'stage_a_five_rows':len(stages)==5,'stage_a_all_fake_checks_pass':all(r['passed'] for r in stages),
            'native_prefill_reserve_recorded':all(r.get('declared_context_tokens')==32768 and
                r.get('prefill_tokens')==32767 and r.get('prefill_generated_tokens')==1 and
                r.get('native_api_reserve_tokens')==1 for r in stages if r['candidate'] in SELECTED[2:]),
            'one_kill_logged':interrupted==1 and len(after['interruptions'])==1 and after['interruptions'][0]['killed'],
            'resume_complete':resumed==0 and after['status']=='COMPLETE','eleven_campaign_roots_with_thinking_sensitivity':len(after['completed'])==11,
            'completed_roots_unchanged':bool(preserved) and all(digest_file(after['completed'][k]['path'])==v for k,v in preserved.items()),
            'partial_attempt_preserved':bool(list((root/'b1/interrupted').glob('*'))),
            'all_exam_labels':all(json.loads(Path(e['path']).read_text())['label']=='EXAM' for e in after['completed'].values())}
    summary={'label':'DRYRUN','synthetic_metrics':True,'checks':checks,'pass':all(checks.values()),'root':str(root)}
    write_json(root/'summary.json',summary);return summary


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);a=p.parse_args(argv)
    summary=run(a.root);print(json.dumps(summary,indent=2));return 0 if summary['pass'] else 1

if __name__=='__main__': raise SystemExit(main())
