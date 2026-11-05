"""Synthetic committed-checkout tests for B1 authority; no server or model."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from r1.exam import runtime
from r1.exam.analyze import RULE_V2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_repo(tmp_path, monkeypatch, plan_template):
    root=tmp_path/'repo'; root.mkdir()
    subprocess.run(['git','init','-q',str(root)],check=True)
    (root/'docs/r1').mkdir(parents=True)
    rule=root/'rule.yaml'; rule.write_bytes(RULE_V2.read_bytes())
    table=root/'stage.json'; table.write_text('{"rows":[]}')
    amendment=root/'amendment.json'; amendment.write_text('{"rows":[]}')
    acceptance=root/'acceptance.md'; acceptance.write_text('test acceptance')
    rule_sha=sha(rule)
    (root/'docs/r1/PLAN.md').write_text(plan_template.format(sha=rule_sha))
    note=root/'author.json'
    cfg={'rule':str(rule),'rule_sha256':rule_sha,'stage_a_table':str(table),
         'stage_a_table_sha256':sha(table),'stage_a_amendment_table':str(amendment),
         'stage_a_amendment_table_sha256':sha(amendment),'stage_a_amendment_acceptance':str(acceptance),
         'stage_a_amendment_acceptance_sha256':sha(acceptance),'nodes':['digits_mlp','openml_credit_approval','openml_ionosphere'],
         'llm_call_cap':80,'workers':20,'instance_seeds':[9001,9002,9003,9004],
         'audit_seeds':[9101,9102,9103,9104], 'authorizations':{'b1':str(note)}}
    data={'author':'Dowling Wong','phase':'b1','approved':True,'rule_sha256':rule_sha,
          'nodes':cfg['nodes'],'llm_call_cap':80,'workers':20,
          'stage_a_table_sha256':sha(table),'stage_a_amendment_table_sha256':sha(amendment),
          'stage_a_amendment_acceptance_sha256':sha(acceptance)}
    note.write_text(json.dumps(data))
    env={**os.environ,'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid',
         'GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}
    subprocess.run(['git','-C',str(root),'add','.'],check=True,env=env)
    subprocess.run(['git','-C',str(root),'commit','-qm','synthetic'],check=True,env=env)
    monkeypatch.setattr(runtime,'REPO',root)
    return root,cfg,rule_sha


TABLE='| ID | Decision |\n|---|---|\n'
VALID='## 10. Open decisions\n### 5 November 2026 — author decision\n'+TABLE+'| R1-EXAM-RULE-X5V2 | "approved {sha}" |\n## 11. Other\n'


def test_committed_dated_row_and_sha_bound_files_pass(tmp_path, monkeypatch):
    root,cfg,rule_sha=setup_repo(tmp_path,monkeypatch,VALID)
    actual=runtime.author_gate(cfg,'b1',rule_sha)
    assert actual==subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()


@pytest.mark.parametrize('plan',[
    '## 10. Open decisions\n### 5 November 2026 — author\nprose R1-EXAM-RULE-X5V2 {sha}\n',
    '## 9. Other\n### 5 November 2026 — author\n| R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n### author decision\n| R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2 | | {sha} |\n',
    '## 10. Open decisions\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2-OTHER | {sha} |\n',
    '## 10. Open decisions\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2 | {sha} |\n| R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n```markdown\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2 | {sha} |\n```\n',
    '## 10. Open decisions\n~~~\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2 | {sha} |\n~~~\n',
    '## 10. Open decisions\n<!--\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2 | {sha} |\n-->\n',
    '## 10. Open decisions\n### 99 Foobar 2099 — author\n| R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n### 5 November 2026 — author\n'+TABLE+'    | R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n### 5 November 2026 — author\n'+TABLE+'\t| R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n### 5 November 2026 — author\n'+TABLE+' \t| R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n### 5 November 2026 — author\n| R1-EXAM-RULE-X5V2 | {sha} |\n',
    '## 10. Open decisions\n<pre>\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2 | {sha} |\n</pre>\n',
    '## 10. Open decisions\n<div>\n### 5 November 2026 — author\n'+TABLE+'| R1-EXAM-RULE-X5V2 | {sha} |\n</div>\n',
])
def test_forged_or_ambiguous_row_rejected(tmp_path,monkeypatch,plan):
    _,cfg,rule_sha=setup_repo(tmp_path,monkeypatch,plan)
    with pytest.raises(RuntimeError,match='dated §10'):
        runtime.author_gate(cfg,'b1',rule_sha)


def test_dirty_checkout_and_changed_data_refused(tmp_path,monkeypatch):
    root,cfg,rule_sha=setup_repo(tmp_path,monkeypatch,VALID)
    (root/'dirty.txt').write_text('x')
    with pytest.raises(RuntimeError,match='clean'):
        runtime.author_gate(cfg,'b1',rule_sha)
    (root/'dirty.txt').rename(tmp_path/'preserved_dirty.txt')
    external=tmp_path/'stage-outside.json';external.write_text('different')
    cfg['stage_a_table']=str(external)
    with pytest.raises(RuntimeError,match='stage_a_table sha256'):
        runtime.author_gate(cfg,'b1',rule_sha)


def test_missing_approval_field_and_wrong_workers_refused(tmp_path,monkeypatch):
    root,cfg,rule_sha=setup_repo(tmp_path,monkeypatch,VALID)
    data=json.loads((root/'author.json').read_text());data['workers']=19
    # Use a fresh committed note; the author choice must bind actual workers.
    (root/'author.json').write_text(json.dumps(data))
    env={**os.environ,'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid',
         'GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}
    subprocess.run(['git','-C',str(root),'add','author.json'],check=True,env=env)
    subprocess.run(['git','-C',str(root),'commit','-qm','fixture change'],check=True,env=env)
    with pytest.raises(RuntimeError,match='worker count'):
        runtime.author_gate(cfg,'b1',rule_sha)
