"""B1 v2 synthetic parent/child integration; no real model, Stage A or GPU."""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
import yaml

ROOT=Path(__file__).resolve().parents[2]


def test_b1_v2_parent_to_child_synthetic_receipts(tmp_path, monkeypatch):
    harness=os.environ.get('AR_HARNESS_B1_ROOT')
    if not harness:
        pytest.skip('set AR_HARNESS_B1_ROOT to the pinned local harness')
    head=subprocess.check_output(['git','-C',harness,'rev-parse','HEAD'],text=True).strip()
    assert head=='a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
    monkeypatch.setenv('AR_HARNESS_ROOT',harness)
    from r1.scripts.exam_dryrun import prepare
    from r1.exam.guards import digest_file
    root=tmp_path/'synthetic_b1';config_path=prepare(root)
    cfg=json.loads(config_path.read_text())
    registry=yaml.safe_load(Path(cfg['registry']).read_text())
    rows=registry['software_anchors']+registry['candidates']+registry.get('sensitivities',[])
    cfg.update(rule=str(ROOT/'r1/exam/rules/x5_rule_v2.yaml'),
               rule_sha256=digest_file(ROOT/'r1/exam/rules/x5_rule_v2.yaml'),
               nodes=['digits_mlp'], instance_seeds=[9001], W=2, llm_call_cap=8,
               cache_prompt=False, harness_commit=head,
               authorizations={'b1':str(root/'SYNTHETIC_UNUSED_NOTE')},
               template_repairs={s['id']:s['template_repair']['sha256'] for s in rows if s.get('template_repair')})
    table=root/'SYNTHETIC_stage_a.json';table.write_text(json.dumps({'label':'DRYRUN','rows':[{'candidate':'qwen25_coder_7b','passed':True}]}))
    amendment=root/'SYNTHETIC_amendment.json';amendment.write_text(json.dumps({'label':'ENGINEERING_ONLY','rows':[]}))
    accept=root/'SYNTHETIC_acceptance.txt';accept.write_text('DRYRUN, not author evidence\n'+digest_file(table)+'\n'+digest_file(amendment)+'\n')
    cfg.update(stage_a_table=str(table),stage_a_table_sha256=digest_file(table),
               stage_a_amendment_table=str(amendment),stage_a_amendment_table_sha256=digest_file(amendment),
               stage_a_amendment_acceptance=str(accept),stage_a_amendment_acceptance_sha256=digest_file(accept))
    config_path.write_text(json.dumps(cfg))
    env={**os.environ,'AR_HARNESS_ROOT':harness,'R1_FAKE_OLLAMA_ROOT':str(root),
         'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1'}
    env.pop('LLAMACPP_CACHE_PROMPT',None)
    out=root/'b1'
    proc=subprocess.run([sys.executable,'-m','r1.scripts.exam_runner','b1','--config',str(config_path),
                         '--out',str(out),'--candidate','qwen25_coder_7b'],cwd=ROOT,env=env,
                        capture_output=True,text=True,timeout=180)
    assert proc.returncode==0,proc.stdout+proc.stderr+'\n'+'\n'.join(p.read_text()[-3000:] for p in out.rglob('runner.log'))
    state=json.loads((out/'batch_state.json').read_text())
    assert state['status']=='COMPLETE' and len(state['completed'])==1
    manifest=json.loads((out/'qwen25_coder_7b/b1_manifest.json').read_text())
    assert manifest['execution_label']=='DRYRUN' and manifest['d28_scope']=='thinking_off_roots_only'
    root_manifest=json.loads(Path(next(iter(state['completed'].values()))['path']).read_text())
    assert root_manifest['observer_evidence']['calls']>0
    assert root_manifest['cache_prompt']['all_false'] is True
