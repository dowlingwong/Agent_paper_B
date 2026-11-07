"""Synthetic M11 reader guards; no real labels or models."""
import hashlib
import copy
import json
import os
import subprocess
from pathlib import Path

import pytest
from r1.c3 import analysis_guard as g
from r1.c3 import dataset as d
from r1.c3 import offline_eval as oe
from r1.c3 import ni_masking as ni
from r1.c3 import audit, accounting



def decision(sha, commit='c'*40):
    return (f'Gate code `r1/c3/gate.py` @ `{commit}`, sha256 `{sha}`, '
            'implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8) '
            'and, if adopted, R1-B7-PARTIAL-T1; T0 and T1 pooled with tier as a stratum. '
            'Sweep-2 label tables may be analysed from this row on.')

def repo(tmp_path,monkeypatch,mode='absent'):
    root=tmp_path/'repo';(root/'docs/r1').mkdir(parents=True);(root/'r1/c3').mkdir(parents=True)
    subprocess.run(['git','init','-q',str(root)],check=True)
    gate=root/'r1/c3/gate.py';gate.write_text('synthetic gate\n');sha=hashlib.sha256(gate.read_bytes()).hexdigest()
    env={**os.environ,'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}
    subprocess.run(['git','-C',str(root),'add','r1/c3/gate.py'],check=True,env=env)
    subprocess.run(['git','-C',str(root),'commit','-qm','synthetic code'],check=True,env=env)
    code_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],env=env,text=True).strip()
    row=f'| R1-BX-D8-CONFIRM | {decision(sha, code_commit)} |\n'
    plan='## 10. Open decisions\n### 5 November 2026 — author decisions\n| ID | Decision |\n|---|---|\n'
    if mode=='valid':plan+=row
    elif mode=='prose':plan+=f'R1-BX-D8-CONFIRM {sha}\n'
    elif mode=='fenced':plan+='```markdown\n'+row+'```\n'
    elif mode=='wrong_sha':plan+=f'| R1-BX-D8-CONFIRM | {decision("a"*64, code_commit)} |\n'
    (root/'docs/r1/PLAN.md').write_text(plan+'## 11. Other\n')
    subprocess.run(['git','-C',str(root),'add','docs/r1/PLAN.md'],check=True,env=env)
    subprocess.run(['git','-C',str(root),'commit','-qm','synthetic author row'],check=True,env=env)
    monkeypatch.setattr(g,'REPO',root)
    return root


@pytest.mark.parametrize('mode',['absent','prose','fenced','wrong_sha'])
def test_sweep2_and_unknown_refused_before_label_file_reads(tmp_path,monkeypatch,mode):
    repo(tmp_path,monkeypatch,mode)
    table=tmp_path/'table';table.mkdir()
    (table/'build.json').write_text(json.dumps({'sweep_index':{'path':'synthetic','sha256':'2'*64}}))
    # No proposal/audit files exist: a label read would instead raise FileNotFoundError.
    for f in (lambda:d.load_table(table),lambda:oe.assemble(table),lambda:ni.load_audits(table)):
        with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'):
            f()
    (table/'build.json').write_text(json.dumps({'label':'ENGINEERING_ONLY'}))
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'):
        d.load_table(table)
    # A caller's pilot label and sources cannot override an actual sweep index.
    forged={'label':'ENGINEERING_ONLY','sources':{'dt4':copy.deepcopy(d.SOURCES['dt4'])},
            'replay_checks_total':{},'sweep_index':{'path':'synthetic','sha256':'2'*64}}
    (table/'build.json').write_text(json.dumps(forged))
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'):
        d.load_table(table)


def test_confirm_row_with_gate_sha_allows_reader(tmp_path,monkeypatch):
    repo(tmp_path,monkeypatch,'valid')
    table=tmp_path/'table';table.mkdir()
    (table/'build.json').write_text(json.dumps({'sweep_index':{'path':'synthetic','sha256':'2'*64}}))
    (table/'proposals.jsonl').write_text('{"proposal_id":"synthetic"}\n')
    assert d.load_table(table)==[{'proposal_id':'synthetic'}]


@pytest.mark.parametrize('header', ['| Artifact | SHA256 |', '| Key | Proposed value |',
                                    '| ID | Proposed decision |', '| ID | Not a decision |'])
def test_non_decision_tables_do_not_supply_authority(header):
    sha='a'*64
    plan=('## 10. Author decisions\n### 5 November 2026 — author decisions\n'+header+
          '\n|---|---|\n| R1-BX-D8-CONFIRM | '+decision(sha)+' |\n')
    assert not g._confirm_row(plan,sha)


@pytest.mark.parametrize('heading', ['### 40 November 2026 (author)',
                                     '### 29 February 2025 — author decisions',
                                     '### 5 November 2026 — not author decisions',
                                     '### 5 November 2026 — non-author decisions',
                                     '### 5 November 2026 — no author decision',
                                     '### 5 November 2026 — without author',
                                     '### 5 November 2026 — not an author decision'])
def test_invalid_or_non_author_heading_does_not_supply_authority(heading):
    sha='a'*64
    plan=('## 10. Author decisions\n'+heading+'\n| ID | Decision |\n|---|---|\n'
          '| R1-BX-D8-CONFIRM | '+decision(sha)+' |\n')
    assert not g._confirm_row(plan,sha)


@pytest.mark.parametrize('header', ['| ID | Decision |', "| ID | Author's decision |",
                                    '| Decision | Author decision (4 Nov 2026, 11:29) |',
                                    '| Row | Decision |'])
def test_actual_author_table_header_styles_are_accepted(header):
    sha='a'*64
    plan=('## 10. Author decisions\n### 4 November 2026 (author; recorded by an agent)\n'+header+
          '\n|---|---|\n| R1-BX-D8-CONFIRM | '+decision(sha)+' |\n')
    assert g._confirm_row(plan,sha)


@pytest.mark.parametrize('heading', [
    '### 4 November 2026 (19:03 CET) — second proposer and B1 draft values',
    '### 4 November 2026 (19:08 CET) — J3 and decision packet replies',
    '### 4 November 2026 — T1 divergence STOP',
    '### 4 November 2026 (20:38 CET) — Track S, X.5 sensitivity and HoreKa submission design',
])
def test_actual_dated_headings_with_explicit_author_decision_header(heading):
    sha='a'*64
    row='| R1-BX-D8-CONFIRM | '+decision(sha)+' |\n'
    prefix='## 10. Open decisions\n'+heading+'\n'
    assert g._confirm_row(prefix+"| ID | Author's decision |\n|---|---|\n"+row,sha)
    assert not g._confirm_row(prefix+'| ID | Decision |\n|---|---|\n'+row,sha)


def test_explicit_author_header_cannot_override_negated_or_invalid_heading():
    sha='a'*64
    row="| ID | Author's decision |\n|---|---|\n| R1-BX-D8-CONFIRM | "+decision(sha)+' |\n'
    for heading in ('### 40 November 2026 — author decisions',
                    '### 5 November 2026 — not author decisions'):
        assert not g._confirm_row('## 10. Open decisions\n'+heading+'\n'+row,sha)


def test_sealed_components_casefolded_and_case_insensitive_alias(tmp_path):
    with pytest.raises(RuntimeError,match='r1_sealed'):
        g.refuse_sealed(tmp_path/'R1_SEALED'/'input')
    sealed=tmp_path/'r1_sealed';sealed.mkdir()
    alias=tmp_path/'R1_SEALED'
    if alias.exists() and alias.samefile(sealed):
        with pytest.raises(RuntimeError,match='r1_sealed'):
            g.refuse_sealed(alias/'input')


def test_dirty_plan_and_changed_gate_are_rejected(tmp_path,monkeypatch):
    root=repo(tmp_path,monkeypatch,'valid')
    (root/'docs/r1/PLAN.md').write_text((root/'docs/r1/PLAN.md').read_text()+'changed\n')
    with pytest.raises(RuntimeError,match='differs from committed'):
        g.require_d8_confirmation()
    subprocess.run(['git','-C',str(root),'checkout','--','docs/r1/PLAN.md'],check=True)
    (root/'r1/c3/gate.py').write_text('changed\n')
    with pytest.raises(RuntimeError,match='gate SHA'):
        g.require_d8_confirmation()


@pytest.mark.parametrize('target',['r1/c3/gate.py','docs/r1/PLAN.md'])
def test_authority_files_resolving_into_sealed_are_refused(tmp_path, monkeypatch, target):
    root=tmp_path/'repo';(root/'r1/c3').mkdir(parents=True);(root/'docs/r1').mkdir(parents=True)
    sealed=tmp_path/'r1_sealed';sealed.mkdir();(sealed/'authority').write_text('synthetic')
    for name in ('r1/c3/gate.py','docs/r1/PLAN.md'):
        path=root/name
        if name==target: path.symlink_to(sealed/'authority')
        else: path.write_text('synthetic')
    monkeypatch.setattr(g,'REPO',root)
    with pytest.raises(RuntimeError,match='r1_sealed'): g.require_d8_confirmation()


def test_sealed_and_symlink_refused_even_after_confirmation(tmp_path,monkeypatch):
    repo(tmp_path,monkeypatch,'valid')
    sealed=tmp_path/'r1_sealed';sealed.mkdir();(sealed/'audits.jsonl').write_text('{}\n')
    alias=tmp_path/'alias';alias.symlink_to(sealed,target_is_directory=True)
    for path in (sealed,alias):
        with pytest.raises(RuntimeError,match='r1_sealed'):
            ni.load_audits(path)
    table=tmp_path/'table';table.mkdir();(table/'proposals.jsonl').symlink_to(sealed/'audits.jsonl')
    with pytest.raises(RuntimeError,match='r1_sealed'):
        d.load_table(table)


def test_evidence_plan_checks_d8_before_reading_table_bytes(tmp_path,monkeypatch):
    repo(tmp_path,monkeypatch)
    table=tmp_path/'table';table.mkdir()
    (table/'build.json').write_text(json.dumps({'sweep_index':{'path':'synthetic','sha256':'2'*64}}))
    # No table files or classification exist: neither can be opened before D8.
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'):
        audit.evidence_plan(table,tmp_path,tmp_path/'missing-index',tmp_path/'missing-classification')


def test_direct_audit_and_accounting_readers_refuse_sealed_aliases(tmp_path):
    sealed=tmp_path/'r1_sealed';sealed.mkdir();(sealed/'data').write_text('{}\n')
    alias=tmp_path/'alias';alias.symlink_to(sealed,target_is_directory=True)
    for path in (sealed/'data',alias/'data'):
        for read in (audit._digest,audit.RunCache,accounting._jsonl):
            with pytest.raises(RuntimeError,match='r1_sealed'): read(path)


def test_resolve_seeds_refuses_sealed_directory_and_seed_symlink(tmp_path):
    sealed=tmp_path/'r1_sealed';sealed.mkdir()
    (sealed/audit.SEEDS_FILE).write_text('{"seeds":[7001]}')
    with pytest.raises(RuntimeError,match='r1_sealed'):
        audit.resolve_seeds(sealed)
    with pytest.raises(RuntimeError,match='r1_sealed'):
        audit.resolve_seeds(sealed,[7001])
    out=tmp_path/'out';out.mkdir();(out/audit.SEEDS_FILE).symlink_to(sealed/audit.SEEDS_FILE)
    with pytest.raises(RuntimeError,match='r1_sealed'):
        audit.resolve_seeds(out)


def test_synthetic_exam_readers_refuse_sealed_inputs(tmp_path):
    from r1.c3.train import exam_analyze, exam_synthetic
    sealed=tmp_path/'r1_sealed';sealed.mkdir()
    alias=tmp_path/'alias';alias.symlink_to(sealed,target_is_directory=True)
    for path in (sealed/'input',alias/'input'):
        with pytest.raises(RuntimeError,match='r1_sealed'): exam_analyze.load_rule(path)
        with pytest.raises(RuntimeError,match='r1_sealed'): exam_synthetic.load(path,path,verify=False)
        with pytest.raises(RuntimeError,match='r1_sealed'): exam_analyze.main([str(path)])


def test_sidecar_input_readers_refuse_sealed_paths(tmp_path):
    from r1.c3 import serve
    sealed=tmp_path/'r1_sealed';sealed.mkdir()
    alias=tmp_path/'alias';alias.symlink_to(sealed,target_is_directory=True)
    for path in (sealed/'input',alias/'input'):
        for read in (serve.sha256_file,serve.Pin.load):
            with pytest.raises(RuntimeError,match='r1_sealed'): read(path)
        with pytest.raises(RuntimeError,match='r1_sealed'):
            serve.main(['--pin',str(path),'--fake',str(path)])
        pin=serve.Pin('fixture','fixture',{k:{'path':'fixture'} for k in ('adapter','head','manifest')},
                      {'base_path':str(path),'family':'fixture'})
        with pytest.raises(RuntimeError,match='r1_sealed'):
            serve.TorchLoraLoader(builder=lambda spec:pytest.fail('model must not be built')).load(pin)


def test_only_known_sweep1_and_full_legacy_source_schema_are_exempt(tmp_path,monkeypatch):
    root=repo(tmp_path,monkeypatch)
    index=root/'results/r1/pilot/C3_sweep_index_20261028T033315Z.json';index.parent.mkdir(parents=True);index.write_text('{"synthetic":"index"}')
    monkeypatch.setattr(g,'SWEEP1_INDEX_SHA',hashlib.sha256(index.read_bytes()).hexdigest())
    table=tmp_path/'table';table.mkdir();(table/'proposals.jsonl').write_text('{"proposal_id":"one"}\n')
    meta={'sweep_index':{'path':str(index),'sha256':g.SWEEP1_INDEX_SHA}}
    (table/'build.json').write_text(json.dumps(meta));assert d.load_table(table)[0]['proposal_id']=='one'
    index.write_text('{"altered":true}')
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'):d.load_table(table)
    pilot={'label':'ENGINEERING_ONLY','sources':{'dt4':copy.deepcopy(d.SOURCES['dt4'])},'replay_checks_total':{'test':0}}
    (table/'build.json').write_text(json.dumps(pilot));assert d.load_table(table)[0]['proposal_id']=='one'
    pilot['sources']['dt4']['runs']=999
    (table/'build.json').write_text(json.dumps(pilot))
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'):d.load_table(table)


def test_unrelated_and_symlinked_audits_require_confirmation(tmp_path, monkeypatch):
    repo(tmp_path, monkeypatch)
    table=tmp_path/'table';table.mkdir()
    (table/'build.json').write_text(json.dumps({'label':'ENGINEERING_ONLY','sources':{'dt4':copy.deepcopy(d.SOURCES['dt4'])},'replay_checks_total':{}}))
    external=tmp_path/'external.jsonl';external.write_text('{"proposal_id":"sweep2"}\n')
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'): ni.load_audits(table, external)
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'): oe.assemble(table, external)
    (table/'audits.jsonl').symlink_to(external)
    with pytest.raises(RuntimeError,match='R1-BX-D8-CONFIRM'): ni.load_audits(table)


def test_sealed_index_and_configs_are_refused_before_read(tmp_path, monkeypatch):
    repo(tmp_path, monkeypatch)
    sealed=tmp_path/'r1_sealed';index=sealed/g.SWEEP1_INDEX_PATH
    index.parent.mkdir(parents=True);index.write_text('synthetic')
    monkeypatch.setattr(g,'SWEEP1_INDEX_SHA',hashlib.sha256(index.read_bytes()).hexdigest())
    table=tmp_path/'table';table.mkdir()
    (table/'build.json').write_text(json.dumps({'sweep_index':{'path':str(index),'sha256':g.SWEEP1_INDEX_SHA}}))
    with pytest.raises(RuntimeError,match='r1_sealed'): d.load_table(table)
    pilot={'label':'ENGINEERING_ONLY','sources':{'dt4':copy.deepcopy(d.SOURCES['dt4'])},'replay_checks_total':{}}
    (table/'build.json').write_text(json.dumps(pilot));(table/'proposals.jsonl').write_text('')
    (sealed/'configs.json').write_text('{}');(table/'configs.json').symlink_to(sealed/'configs.json')
    with pytest.raises(RuntimeError,match='r1_sealed'): d.plan(table,{},False)


def test_confirmation_must_be_actual_dated_author_table_and_sha_in_decision():
    sha='a'*64; table=f'| ID | Decision | Notes |\n|---|---|---|\n| R1-BX-D8-CONFIRM | {decision(sha)} | |\n'
    assert g._confirm_row('## 10. Open decisions\n### 5 November 2026 — author\n'+table,sha)
    assert not g._confirm_row('## 10. Open decisions\n'+table,sha)
    assert not g._confirm_row('## 10. Open decisions\n### 5 November 2026 — author\n<pre>\n'+table+'</pre>\n',sha)
    assert not g._confirm_row('## 10. Open decisions\n### 5 November 2026 — author\n'+table.replace(decision(sha),'approved').replace('| |',f'| {sha} |'),sha)
