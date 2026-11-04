"""Exam runner plumbing: pinned dedicated service, whole-root resume, watchdog and disk STOP."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import tempfile
from pathlib import Path
import yaml
from r1.exam.analyze import load_rule
from r1.exam.campaign import read_rows, write_json
from r1.exam.guards import digest_file, licence_blockers, quantization_blockers, space_check
from r1.exam.namespace import check_exam_seeds
from r1.exam.cooperative_lease import LeaseStop
from r1.scripts import llama_server_instance as lsi
from r1.scripts.c3_label_sweep import RunnerWatchdog, stop_tree

REPO=Path(__file__).resolve().parents[2]

TEMPLATE_REPAIR_SCHEMA='r1.exam.template_repair/v1'

def template_repair_args(spec) -> list[str]:
    """Declared per-candidate template repair (A1): serve the pinned repair template.

    The declaration is part of the pinned registry (file + sha256); a missing file or a
    digest mismatch is a STOP.  Used by the replay server and the qualification probe so
    that measurement and probe run the same template."""
    repair=(spec or {}).get('template_repair')
    if not repair: return []
    if not isinstance(repair,dict) or repair.get('schema')!=TEMPLATE_REPAIR_SCHEMA:
        raise RuntimeError('STOP: template repair declaration malformed')
    path=Path(str(repair.get('file') or ''))
    if not path.is_absolute(): path=REPO/path
    if not path.is_file(): raise RuntimeError('STOP: template repair file missing')
    if digest_file(path)!=repair.get('sha256'):
        raise RuntimeError('STOP: template repair digest mismatch')
    return ['--chat-template-file', str(path.resolve())]
DEFAULT_CONFIG=REPO/'r1/scripts/configs/exam_portal.json'
# Approved exam hosts.  The author's 1 Nov decision moved the new Stage A attempt to
# TASL-7; both hosts run the same Ubuntu 22.04 + RTX 4090 environment and share the
# approved paths, so the host gate is an allowlist with the config host pinned to the
# actual node (never infer on the Mac).
APPROVED_EXAM_HOSTS=frozenset({'TASL-2','TASL-7'})
EXAM_X_ROOT=Path('/home/dowling/exam-x')
# Exact exam server flags.  ``-lv 4`` is required evidence plumbing, not a tuning
# knob: the pinned llama.cpp build (620d222, v0.7.0-dev) prints the route (i)
# ``load_tensors: offloaded N/N layers to GPU`` line only at verbosity >= 4, and
# the offload check could otherwise only fall back to the stricter route (ii)
# process-memory floor (R1-EXAM-OFFLOAD-ROUTE, 1 Nov).
EXAM_SERVER_ARGS=['--jinja','--cache-type-k','q8_0','--cache-type-v','q8_0','-lv','4']
EXPECTED_CANDIDATES=frozenset('qwen38_27b qwen36_27b gemma4_31b muse_glimmer_30b olmo31_32b devstral_small2_24b qwen36_35b_a3b gemma4_26b_a4b nemotron35_30b_a3b glm47_flash lfm25_24b_a2b laguna_xs21 ornith10_35b qwen3_coder_30b_a3b gpt_oss_20b qwen35_9b gemma4_12b ornith10_9b ministral3_14b rico03_qwen36_27b'.split())


class PreparationStop(RuntimeError):
    """A failed precondition is not a candidate exclusion."""


class MechanicalFailure(RuntimeError):
    """A verified candidate failed its mechanical load/offload probe."""


def handle_live_orphan(record, phase):
    """Stage A must preserve any live prior server and stop for review."""
    if phase=='stage-a':
        raise PreparationStop('STOP: live previous Stage A server; preserve without signalling')
    ours,reason=lsi.orphan_matches(record)
    if not ours: raise PreparationStop(f'STOP: cannot prove orphan ownership: {reason}')
    return lsi.stop_orphan(record)


def reject_stopped_batch(state):
    """Never resume or rewrite a stopped batch; preserve it for review."""
    if not isinstance(state,dict):
        raise PreparationStop('STOP: existing batch state is malformed')
    if str(state.get('status','')).upper() in {'STOP','STOPPED','FAILED'} or state.get('stop_reason') is not None:
        raise PreparationStop('STOP: existing stopped batch must not be resumed')


def refuse_existing_stage_a_output(path):
    """Stage A starts only in an absent or empty output directory.

    A RUNNING state or stale marker can be left by a supervisor killed before
    it wrote STOPPED. Do not rename, overwrite or infer safe recovery.
    """
    path=Path(path)
    if not path.exists():return
    if not path.is_dir():raise PreparationStop('STOP: Stage A output path is not a directory')
    try:
        if next(path.iterdir(),None) is not None:
            raise PreparationStop('STOP: existing Stage A output cannot be resumed or overwritten')
    except OSError as exc:
        raise PreparationStop('STOP: Stage A output cannot be inspected') from exc


def placeholders(value, prefix=''):
    if isinstance(value,dict): return [p for k,v in value.items() if k!='comment' for p in placeholders(v,f'{prefix}.{k}')]
    if isinstance(value,list): return [p for i,v in enumerate(value) for p in placeholders(v,f'{prefix}[{i}]')]
    return [prefix] if isinstance(value,str) and value.startswith('TODO_') else []


def load_config(path, *, allow_placeholders=False):
    cfg=json.loads(Path(path).read_text())
    if cfg['ctx_size']!=32768 or cfg['cache_type_k']!='q8_0' or cfg['cache_type_v']!='q8_0' or cfg['n_gpu_layers']!=999:
        raise ValueError('exam requires 32768 context, q8_0 KV and full offload n_gpu_layers=999')
    if not cfg.get('dryrun') and cfg['W']!=20: raise ValueError('exam W is 20 outside DRYRUN')
    if cfg['temperature']!=.2 or cfg['proposal_schema']!='manager_proposal/v1': raise ValueError('exam sampling/schema mismatch')
    check_exam_seeds(cfg['instance_seeds'],cfg['audit_seeds'])
    if cfg['minimum_free_bytes']!=100_000_000_000: raise ValueError('author disk floor is 100 GB')
    later={'b2_instances_per_node','b1_analysis','b1_analysis_sha256','stage_a_table','stage_a_table_sha256','anchor_duplicate_reference','llm_call_cap','nodes','prompts','prompts_sha256','d22_pick',
           # x5_rule/v2 B1/B2: the operator-accepted A1 amendment table (t7j10) and its acceptance, bound by sha (R1-TRACKX-HANDOVER-RULING)
           'stage_a_amendment_table','stage_a_amendment_table_sha256','stage_a_amendment_acceptance','stage_a_amendment_acceptance_sha256'}
    common={k:v for k,v in cfg.items() if k not in later}
    if placeholders(common) and not allow_placeholders: raise ValueError(f'unresolved common placeholders: {placeholders(common)}')
    return cfg


def read_registry(path):
    data=yaml.safe_load(Path(path).read_text())
    all_rows=data['candidates']+data['software_anchors']
    ids=[x['id'] for x in all_rows]
    if len(set(ids))!=len(ids): raise ValueError('duplicate registry id')
    if {x['id'] for x in all_rows if x['role']=='candidate'}!=EXPECTED_CANDIDATES: raise ValueError('author pool is 20 candidates, no Ornith-31B or Qwopus-v4 substitute')
    if {x['id'] for x in all_rows if x['role']=='anchor'}!={'random_valid','scripted','qwen25_coder_7b'}: raise ValueError('three anchors required')
    return data


def host_check(cfg, out):
    if cfg.get('dryrun'):
        root=Path(cfg['dryrun_root']).resolve();temps={Path(tempfile.gettempdir()).resolve(),Path('/tmp').resolve()}
        if platform.node().split('.')[0] in ('TASL-2','ucrtasl') or not any(root!=temp and root.is_relative_to(temp) for temp in temps) or not (root/'.dryrun').is_file():
            raise RuntimeError('STOP: EXAM DRYRUN needs a marked temporary root on a development host')
        if not Path(out).resolve().is_relative_to(root): raise RuntimeError('STOP: DRYRUN output escapes temporary root')
        return
    if any(os.environ.get(k) for k in ('R1_DRYRUN','R1_FAKE_OLLAMA_ROOT','R1_EXAM_DRYRUN')):
        raise RuntimeError('STOP: DRYRUN environment must not enter a production exam')
    node=platform.node().split('.')[0]
    if node not in APPROVED_EXAM_HOSTS or cfg['host']!=node:
        raise RuntimeError('STOP: the exam runs only on an approved portal host '
                           f'({"/".join(sorted(APPROVED_EXAM_HOSTS))}) and cfg.host must equal the node; never infer on the Mac')
    for key in ('models','work'):
        approved=EXAM_X_ROOT/key
        path=Path(cfg[key+'_dir'])
        if path!=approved or path.resolve()!=approved: raise RuntimeError(f'STOP: {key} storage is not the author-approved path')
        space_check(path)
    if not Path(out).resolve().is_relative_to(Path(cfg['work_dir'])): raise RuntimeError('STOP: output must be under approved work directory')


def gpu_sample(cfg):
    if cfg.get('dryrun'): return {'used_mib':6000,'free_mib':18000,'compute_pids':[],'device':0}
    done=subprocess.run(['nvidia-smi','--query-gpu=uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15)
    rows=[line.split(',') for line in done.stdout.splitlines()]
    row=next((r for r in rows if r[0].strip()==cfg['gpu_uuid']),None)
    if not row: raise RuntimeError('STOP: pinned GPU absent from census')
    return {'used_mib':float(row[1]),'free_mib':float(row[2]),'utilisation_percent':float(row[3]),'device':0}


def author_gate(cfg, phase, rule_sha):
    if cfg.get('dryrun') or phase=='stage-a': return
    note=Path(cfg['authorizations'][phase]);raw=note.read_bytes()
    # Accept a plain JSON note or one JSON block inside an author Markdown note.
    try:
        text=raw.decode();blocks=re.findall(r'```json\s*(.*?)```',text,re.S)
        data=json.loads(blocks[0] if len(blocks)==1 else text)
    except ValueError: raise RuntimeError('STOP: authorization note needs a machine-readable JSON object')
    if data.get('author')!='Dowling Wong' or data.get('phase')!=phase or data.get('approved') is not True or data.get('rule_sha256')!=rule_sha:
        raise RuntimeError('STOP: evidence authorization does not bind author, phase and frozen rule')
    rel=note.resolve().relative_to(REPO)
    committed=subprocess.check_output(['git','-C',str(REPO),'show',f'HEAD:{rel}'])
    if committed!=raw: raise RuntimeError('STOP: authorization bytes are not committed')
    plan=(REPO/'docs/r1/PLAN.md').read_text()
    if not any(rule_sha in line and 'R1-EXAM-RULE' in line for line in plan.splitlines()):
        raise RuntimeError('STOP: accepted frozen rule sha256 absent from author PLAN row')
    if data.get('nodes')!=cfg['nodes'] or data.get('stage_a_table_sha256')!=cfg['stage_a_table_sha256']: raise RuntimeError('STOP: authorization does not bind nodes and accepted Stage A table')
    if 'stage_a_amendment_table_sha256' in cfg and (data.get('stage_a_amendment_table_sha256')!=cfg['stage_a_amendment_table_sha256'] or
                                                    data.get('stage_a_amendment_acceptance_sha256')!=cfg['stage_a_amendment_acceptance_sha256']):
        raise RuntimeError('STOP: authorization does not bind the accepted A1 amendment table')
    if phase=='b2' and data.get('b1_analysis_sha256')!=cfg['b1_analysis_sha256']: raise RuntimeError('STOP: authorization does not bind B1 analysis')
    if not isinstance(cfg['llm_call_cap'],int) or isinstance(cfg['llm_call_cap'],bool) or cfg['llm_call_cap']<2: raise RuntimeError('STOP: positive paired LLM-call cap required')
    if phase=='b1' and (len(cfg['nodes'])!=3 or set(cfg['nodes']) not in ({'digits_mlp','openml_credit_approval','openml_ionosphere'},{'tabular_mlp','openml_credit_approval','openml_ionosphere'})): raise RuntimeError('STOP: B1 requires three protocol nodes')
    if data.get('llm_call_cap')!=cfg['llm_call_cap']: raise RuntimeError('STOP: LLM-call cap is not author-bound')
    if phase=='b1' and (cfg['instance_seeds']!=[9001,9002,9003,9004] or cfg['audit_seeds']!=[9101,9102,9103,9104]): raise RuntimeError('STOP: B1 seeds differ from protocol')
    if phase=='b2' and (not isinstance(cfg['b2_instances_per_node'],int) or isinstance(cfg['b2_instances_per_node'],bool) or not 1<=cfg['b2_instances_per_node']<=89): raise RuntimeError('STOP: B2 instances must fit the fresh 9011–9099 namespace')
    if phase=='b2' and data.get('instances_per_node')!=cfg['b2_instances_per_node']:
        raise RuntimeError('STOP: B2 instance count not author-bound')


def verify_campaign(path, binding):
    path=Path(path);m=json.loads(path.read_text())
    if m.get('status')!='COMPLETE' or m.get('label')!='EXAM' or m.get('job_binding')!=binding:
        raise PreparationStop('STOP: incomplete/unbound campaign manifest')
    if digest_file(path.parent/'job.json')!=m['job_sha256']: raise PreparationStop('STOP: campaign job changed')
    certificate=path.parent/'post_check.json'
    if not certificate.exists(): raise PreparationStop('STOP: completed campaign lacks its post-run receiving check; preserve it for review')
    check=json.loads(certificate.read_text())
    if check.get('binding')!=binding or check.get('manifest_sha256')!=digest_file(path) or not check.get('passed'):
        raise PreparationStop('STOP: post-run receiving check does not bind this completed campaign')
    for name,expected in m['evidence_hashes'].items():
        source=path.parent/name
        if (digest_file(source) if source.exists() else None)!=expected: raise PreparationStop(f'STOP: campaign evidence changed: {name}')
    return m


def require_server_lease_inheritance(instance):
    """Fail closed unless the started native server carries verified lease inheritance.

    Stage A may not issue any request to a server whose inherited lease open
    file description is unproved; this reads the record the server start wrote
    after the ancestor->descendant kcmp and /proc FD checks succeeded.
    """
    from r1.exam.cache_runtime import validate_lease_inheritance_record
    record = getattr(instance, 'record', None)
    inheritance = record.get('lease_inheritance') if isinstance(record, dict) else None
    if not isinstance(inheritance, dict):
        raise PreparationStop('STOP: cooperative server record lacks lease inheritance evidence')
    try:
        validate_lease_inheritance_record(inheritance)
    except LeaseStop as exc:
        raise PreparationStop(f'STOP: lease inheritance evidence invalid: {exc}') from exc
    if record.get('pid') != inheritance.get('server_pid'):
        raise PreparationStop('STOP: lease inheritance server pid mismatch')
    if record.get('start_ticks') != inheritance.get('server_start_ticks'):
        raise PreparationStop('STOP: lease inheritance start ticks mismatch')
    return inheritance


class ExamRunner:
    def __init__(self, cfg, out, *, registry_path=None):
        self.cfg=cfg;self.out=Path(out).resolve();host_check(cfg,self.out)
        self.registry_path=Path(registry_path or cfg['registry']).resolve()
        self.registry=read_registry(self.registry_path)
        self.rule,self.rule_sha=load_rule(cfg['rule'],cfg['rule_sha256'])
        self.binding=hashlib.sha256(json.dumps({'config':cfg,'registry_sha256':digest_file(self.registry_path),'rule_sha256':self.rule_sha,'value_grids_sha256':digest_file(cfg['value_grids'])},sort_keys=True).encode()).hexdigest()
        self.service=None;self.child=None;self.state={};self.lock=None
        if not cfg.get('dryrun'):
            from r1.harness import harness_root
            actual=subprocess.check_output(['git','-C',str(harness_root()),'rev-parse','HEAD'],text=True).strip()
            if actual!=cfg['harness_commit']: raise RuntimeError('STOP: harness commit mismatch')
            subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',cfg['paper_commit'],'HEAD'],check=True)
            changed=subprocess.check_output(['git','-C',str(REPO),'diff','--name-only',cfg['paper_commit'],'--','r1/exam','r1/scripts/exam_runner.py','r1/scripts/llama_server_instance.py','r1/scripts/llamacpp_probe.py','r1/headroom/e1b_collect.py'],text=True).strip()
            if changed: raise RuntimeError('STOP: exam code differs from pinned code commit')

    def space(self):
        if not self.cfg.get('dryrun'):
            try:
                for key in ('models_dir','work_dir'): space_check(self.cfg[key])
            except (OSError,RuntimeError) as exc: raise PreparationStop(str(exc)) from exc

    def save(self): write_json(self.out/'batch_state.json',self.state)

    def start(self, phase):
        if phase=='stage-a':
            # Defense in depth: the reviewed cooperative D3 context must already
            # be authorized (guardian lease + explicit false) before any output,
            # server or worker exists.
            from r1.exam.cache_runtime import require_authorized_stagea
            require_authorized_stagea()
        if phase in ('b1','b2'):
            raise PreparationStop('STOP: B1/B2 reviewed harness pin and observer cache evidence not implemented')
        if phase=='stage-a':refuse_existing_stage_a_output(self.out)
        self.out.mkdir(parents=True,exist_ok=True)
        path=self.out/'batch_state.json'
        if path.exists():
            self.state=json.loads(path.read_text())
            reject_stopped_batch(self.state)
            if self.state['binding']!=self.binding or self.state['phase']!=phase: raise RuntimeError('STOP: resume identity/config/rule mismatch')
            for key,entry in self.state['completed'].items():
                if digest_file(entry['path'])!=entry['sha256']: raise RuntimeError(f'STOP: completed root changed: {key}')
                if phase!='stage-a':
                    verify_campaign(entry['path'],self.binding)
                    if digest_file(Path(entry['path']).parent/'post_check.json')!=entry['post_check_sha256']: raise PreparationStop('STOP: receiving certificate changed')
        else:
            shutil.copyfile(self.registry_path,self.out/'registry_snapshot.yaml')
            self.state={'schema':'exam_batch/v1','label':'EXAM','execution_label':'DRYRUN' if self.cfg.get('dryrun') else ('ENGINEERING_ONLY' if phase=='stage-a' else 'EVIDENCE'),
                        'phase':phase,'binding':self.binding,'rule_sha256':self.rule_sha,'completed':{},'interruptions':[],'status':'RUNNING'}
        lock=self.out/'runner.lock'
        if lock.exists():
            old=json.loads(lock.read_text())
            try: os.kill(old['pid'],0)
            except ProcessLookupError: lock.rename(self.out/f'runner.lock.stale.{time.time_ns()}')
            else: raise RuntimeError('STOP: previous runner still alive; never share a campaign root')
        with lock.open('x') as f: json.dump({'pid':os.getpid(),'host':platform.node()},f)
        self.lock=lock
        previous=self.state.get('in_progress') or {}
        if previous.get('pid'):
            try: os.kill(previous['pid'],0)
            except ProcessLookupError: pass
            else: raise PreparationStop('STOP: earlier campaign worker is still alive')
        recovery=[]
        for record_path in self.out.rglob('llama_server_*.json'):
            record=json.loads(record_path.read_text())
            if not record.get('pid') or record.get('stopped_utc'): continue
            try: os.kill(record['pid'],0)
            except ProcessLookupError: continue
            result=handle_live_orphan(record,phase);recovery.append(result)
            record.update(stopped_utc=result.get('utc'),orphan_cleanup=result);write_json(record_path,record)
        if recovery: self.state.setdefault('orphan_cleanup',[]).extend(recovery)
        for interval in self.state.get('server_intervals',[]):
            if interval['end'] is None:
                interval.update(end=time.time(),recovered_after_interruption=True,cost_is_upper_bound=not bool(recovery))
        self.state['status']='RUNNING';self.save()
        author_gate(self.cfg,phase,self.rule_sha)
        if phase=='stage-a' and not self.cfg.get('dryrun'):
            import importlib.util, importlib.metadata
            if any(importlib.util.find_spec(name) is None for name in ('transformers','jinja2','tokenizers')):
                raise RuntimeError('STOP: Stage A template-reference dependencies are not installed; not a candidate failure')
            versions={name:importlib.metadata.version(name) for name in ('transformers','jinja2','tokenizers')}
            if self.state.get('template_reference_versions') not in (None,versions): raise PreparationStop('STOP: template reference stack changed during a resumed Stage A')
            self.state['template_reference_versions']=versions
            self.save()

    def spec_order(self, selected=None):
        rows=self.registry['software_anchors']+[r for r in self.registry['candidates'] if r['role']=='anchor']+[r for r in self.registry['candidates'] if r['role']=='candidate']+self.registry.get('sensitivities',[])
        if selected:
            unknown=set(selected)-{r['id'] for r in rows}
            if unknown: raise ValueError(f'unknown candidates {unknown}')
            rows=[r for r in rows if r['id'] in selected]
        return rows

    def server(self, spec, mode, ctx=32768):
        try: return self._server(spec,mode,ctx)
        except MechanicalFailure: raise
        except Exception as exc: raise PreparationStop(str(exc)) from exc

    def validate_spec(self, spec, *, allow_pending_footprint=False):
        spec=copy.deepcopy(spec)
        if allow_pending_footprint and (spec['runtime'].get('footprint_mib') is None or placeholders(spec['runtime'].get('footprint_mib'))): spec['runtime']['footprint_mib']=1
        self.space();model=spec['runtime']['model_path'];server=self.cfg['server']
        if not self.cfg.get('dryrun'):
            unresolved=placeholders(spec)
            if unresolved: raise RuntimeError(f'STOP: unresolved candidate pins: {unresolved}')
            policy={'candidates':{spec['id']:{'status':'author_approved_research_and_publication','approved_by':'Dowling Wong','approval_ref':spec['licence_approval'],'licence':spec['licence']}}}
            blockers=licence_blockers(spec['id'],policy)+quantization_blockers(spec)
            source=spec['quant_source']
            if not all(source.get(k) for k in ('repo','revision','file','size_bytes','sha256')) or not re.fullmatch('[0-9a-f]{40}',str(source.get('revision',''))): blockers.append('quant artifact repo/revision/file/size/sha pins required')
            if source.get('base_model')!=spec['base_repo']: blockers.append('quant source does not bind the candidate base model')
            if Path(model).stat().st_size!=source.get('size_bytes'): blockers.append('GGUF file size differs from source pin')
            if blockers: raise RuntimeError(f'STOP: {blockers}')
            if not Path(model).resolve().is_relative_to(Path(self.cfg['models_dir'])): raise RuntimeError('STOP: model outside approved storage')
        if digest_file(model)!=spec['quant_source']['sha256']: raise RuntimeError('STOP: GGUF digest mismatch')
        if digest_file(server['binary'])!=server['binary_sha256']: raise RuntimeError('STOP: server binary digest mismatch')
        if not self.cfg.get('dryrun'):
            with Path(server['binary']).open('rb') as f: native=f.read(4)==b'\x7fELF'
            with Path(model).open('rb') as f: gguf=f.read(4)==b'GGUF'
            if not native or not gguf or 'DRYRUN' in server['build']: raise RuntimeError('STOP: native ELF server and real GGUF required outside DRYRUN')
        build=lsi.build_info(server['binary'])
        if build['version_line']!=server['build']: raise RuntimeError('STOP: llama.cpp build pin mismatch')
        return build

    def _server(self, spec, mode, ctx):
        host_check(self.cfg,self.out)
        build=self.validate_spec(spec)
        model=spec['runtime']['model_path'];server=self.cfg['server']
        thinking={**spec['thinking_policy'],'mode':mode,'budget':2048 if mode!='off' else 0}
        args=list(EXAM_SERVER_ARGS)+template_repair_args(spec)
        inst=lsi.LlamaServerInstance(self.out/'servers'/spec['id'],server['binary'],model_path=model,alias=spec['id'],
                                   ctx_size=ctx,n_gpu_layers=999,gpu_uuid=self.cfg['gpu_uuid'],extra_args=args,
                                   thinking_policy=thinking,generation=len(list((self.out/'servers'/spec['id']).glob('*.json'))),
                                   label=self.state['execution_label'],start_timeout=server['start_timeout'])
        lease_fd=None
        if self.state.get('phase')=='stage-a':
            # The native server must inherit the verified lease OFD; the start
            # verification STOPs before any request if that chain is unproved.
            from r1.exam.cache_runtime import verified_lease_fd
            lease_fd=verified_lease_fd()
        if not self.cfg.get('dryrun'):
            help_text=subprocess.check_output([server['binary'],'--help'],text=True,stderr=subprocess.STDOUT,timeout=20)
            required=['--chat-template-kwargs'] if thinking.get('off_switch') else []
            if mode!='off': required+=['--reasoning-budget']
            if any(flag not in help_text for flag in required): raise RuntimeError('STOP: pinned build lacks thinking-control flags')
            apps=lsi.gpu_compute_apps();sample=gpu_sample(self.cfg)
            write_json(self.out/f'{spec["id"]}_occupancy_before.json',{'compute_apps':apps,'gpu':sample,'graphics_memory_is_part_of_fit_margin':True})
            if sample['free_mib']<1024 or sample['utilisation_percent']>5: raise RuntimeError('STOP: pre-launch GPU memory margin or idle occupancy check failed')
            if apps is None or apps: raise RuntimeError('STOP: unknown or occupied GPU compute census before launch')
        self.service=inst
        self.state.setdefault('server_intervals',[]).append({'candidate':spec['id'],'phase':self.state['phase'],'mode':mode,'context':ctx,'start':time.time(),'end':None})
        self.save()
        import threading
        stopped=threading.Event();disk_error=[]
        def watch_loading():
            while not stopped.wait(.2):
                try: self.space()
                except Exception as exc:
                    disk_error.append(str(exc))
                    if self.state.get('phase')!='stage-a' and inst.process is not None and inst.record.get('pgid'): inst.stop()
                    break
        monitor=threading.Thread(target=watch_loading,daemon=True);monitor.start()
        try:
            try: inst.start(build=build,model_sha256=spec['quant_source']['sha256'],
                            preserve_on_failure=self.state.get('phase')=='stage-a',lease_fd=lease_fd)
            except LeaseStop as exc:
                raise PreparationStop(f'STOP: cooperative lease inheritance failed: {exc}') from exc
            except RuntimeError as exc:
                if disk_error: raise PreparationStop(disk_error[0]) from exc
                if 'port' in str(exc) and 'in use' in str(exc): raise PreparationStop(str(exc)) from exc
                raise MechanicalFailure(str(exc)) from exc
            if disk_error: raise PreparationStop(disk_error[0])
        finally:
            stopped.set();monitor.join(timeout=20)
        if lease_fd is not None:
            # Preserve the proved inheritance row beside the server record: the
            # server JSON record cannot be edited later without invalidating it.
            write_json(inst.batch/'lease_inheritance.json',require_server_lease_inheritance(inst))
        report=inst.offload(footprint_mib=spec['runtime']['footprint_mib'],apps=[] if self.cfg.get('dryrun') else None)
        write_json(inst.batch/'exam_offload.json',report)
        if not report['full']: raise MechanicalFailure('full GPU offload not established')
        if spec['id'] not in (inst.model_ids() or []): raise PreparationStop('STOP: served alias identity mismatch')
        if (inst.props() or {}).get('model_path')!=model: raise RuntimeError('STOP: served GGUF path mismatch')
        return inst

    def run_job(self, job, module, *, interrupt=False):
        if interrupt and self.state.get('phase')=='stage-a':
            raise PreparationStop('STOP: Stage A workers must not be signalled')
        self.space()
        path=Path(job['out']);path.mkdir(parents=True,exist_ok=True)
        write_json(path/'job.json',job)
        env={**os.environ,'PYTHONPATH':str(REPO),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
        if self.service: env['LLAMACPP_BASE_URL']=self.service.openai_base_url
        kwargs={}
        if self.state.get('phase')=='stage-a':
            from r1.exam.cache_runtime import verified_lease_fd
            kwargs['pass_fds']=(verified_lease_fd(),)
        with (path/'runner.log').open('ab') as log:
            self.child=subprocess.Popen([sys.executable,'-m',module,'--job',str(path/'job.json')],env=env,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,**kwargs)
        self.state['in_progress']={'path':str(path),'pid':self.child.pid};self.save()
        watchdog=RunnerWatchdog(self.service,self.cfg['watchdog']) if self.service else None
        started=time.monotonic();killed=False
        try:
            while self.child.poll() is None:
                if self.state.get('phase')=='stage-a':
                    from r1.exam.cache_runtime import reject_unverified_lease
                    reject_unverified_lease()
                self.space()
                if not self.cfg.get('dryrun') and self.service:
                    apps=lsi.gpu_compute_apps();sample=gpu_sample(self.cfg)
                    if apps is None or any(r['pid']!=self.service.process.pid for r in apps) or sample['free_mib']<1024:
                        raise RuntimeError('STOP: GPU census/margin lost during campaign')
                loss=watchdog.check() if watchdog else None
                if loss: raise RuntimeError(f'STOP: dedicated server watchdog: {loss}')
                if time.monotonic()-started>self.cfg['root_timeout_seconds']: raise TimeoutError('STOP: campaign deadline')
                if interrupt and (path/'root_trials.jsonl').exists():
                    os.killpg(self.child.pid,signal.SIGKILL);self.child.wait();killed=True
                    raise InterruptedError('DRYRUN kill-and-resume: root worker killed after first ledger append')
                time.sleep(float(self.cfg['watchdog']['poll_seconds']))
            if self.child.returncode: raise RuntimeError(f'STOP: root worker exit {self.child.returncode}; see {path}/runner.log')
        except BaseException as exc:
            if self.child.poll() is None and self.state.get('phase')!='stage-a':
                stop_tree(self.child.pid);self.child.wait(timeout=30)
            self.state['interruptions'].append({'path':str(path),'error':str(exc),'returncode':self.child.returncode,'killed':killed,'time':time.time()})
            self.save();raise
        self.child=None

    def root(self, spec, phase, node, seed, mode, *, interrupt=False):
        self.space()
        key=f'{spec["id"]}/{phase}/{mode}/{node}__s{seed}'
        if key in self.state['completed']: return verify_campaign(self.state['completed'][key]['path'],self.binding)
        path=self.out/key
        if path.exists():
            old=self.state.get('in_progress') or {}
            if old.get('path')!=str(path): raise RuntimeError('STOP: existing root is not a recorded interrupted attempt')
            if old.get('path')==str(path) and old.get('pid'):
                try: os.kill(old['pid'],0)
                except ProcessLookupError: pass
                else: raise RuntimeError('STOP: earlier root worker still alive')
            finished=path/'campaign_manifest.json'
            if finished.exists():
                recovered=verify_campaign(finished,self.binding)
                self.state['completed'][key]={'path':str(finished),'sha256':digest_file(finished),'post_check_sha256':digest_file(path/'post_check.json')}
                self.state.pop('in_progress',None);self.save();return recovered
            archived=self.out/'interrupted'/f'{time.time_ns()}_{spec["id"]}_{node}_s{seed}'
            archived.parent.mkdir(exist_ok=True);path.rename(archived)
        job={'out':str(path),'binding':self.binding,'workers':self.cfg['workers'],'phase':phase,'node':node,'seed':seed,'candidate':spec,'mode':mode,
             'dryrun':bool(self.cfg.get('dryrun')),'W':self.cfg['W'],'llm_call_cap':self.cfg['llm_call_cap'],
             'audit_seeds':self.cfg['audit_seeds'] if phase=='b1' else list(range(9201,9211)),
             'base_url':self.service.openai_base_url if self.service else None,'value_grids':self.cfg['value_grids'],
             'proposal_schema':None if self.cfg.get('free_sensitivity') else 'manager_proposal/v1'}
        self.run_job(job,'r1.exam.campaign',interrupt=interrupt)
        manifest=path/'campaign_manifest.json'
        check={'binding':self.binding,'manifest_sha256':digest_file(manifest),'passed':True,'software_anchor':self.service is None}
        if self.service:
            report=self.service.offload(footprint_mib=spec['runtime']['footprint_mib'],apps=[] if self.cfg.get('dryrun') else None)
            ids=self.service.model_ids();props=self.service.props()
            check.update(offload=report,model_ids=ids,props=props,server_pid=self.service.process.pid)
            check['passed']=bool(report['full'] and spec['id'] in (ids or []) and (props or {}).get('model_path')==spec['runtime']['model_path'])
        if not check['passed']: raise PreparationStop('STOP: post-run full-offload/model check failed; completed data retained for review')
        write_json(path/'post_check.json',check)
        self.state['completed'][key]={'path':str(manifest),'sha256':digest_file(manifest),'post_check_sha256':digest_file(path/'post_check.json')}
        self.state.pop('in_progress',None);self.save()
        return json.loads(manifest.read_text())

    def stop_service(self):
        if self.service:
            self.service.stop();self.service=None
            for entry in reversed(self.state.get('server_intervals',[])):
                if entry['end'] is None: entry['end']=time.time();break
            self.save()

    def close(self, *, preserve_running=False):
        if preserve_running:
            # Preserve server, worker, and marker after STOP for explicit review.
            return
        self.stop_service()
        if self.lock: self.lock.unlink(missing_ok=True);self.lock=None
