"""Exam runner plumbing: pinned dedicated service, whole-root resume, watchdog and disk STOP."""
from __future__ import annotations
import copy
import datetime
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
B1_CONFIG_REL='r1/scripts/configs/exam_b1_v2.json'

TEMPLATE_REPAIR_SCHEMA='r1.exam.template_repair/v1'

def report_b1_stop_and_save(runner, original, *, save=True, append_only=False):
    """Best effort only: emit the original error before attempting STOP state I/O.

    Stderr is not proof of durable publication.  Both output channels may fail;
    callers must retain the STOP and must not infer that STATUS was published.
    """
    try:
        print(f'STOP: original exception: {type(original).__name__}: {original}', file=sys.stderr, flush=True)
    except Exception:
        pass
    if save:
        try:
            if append_only:
                runner.save_b1_stop(original)
            else:
                runner.save()
        except Exception as save_error:
            try:
                print(f'STOP: state save failed: {type(save_error).__name__}: {save_error}', file=sys.stderr, flush=True)
            except Exception:
                pass

def report_b1_freeze_failure(original, freeze_error):
    """Best effort; this does not assert quiescence or durable publication."""
    try:
        print(f'STOP: original exception: {type(original).__name__}: {original}; '
              f'containment freeze unverified: {type(freeze_error).__name__}: {freeze_error}',
              file=sys.stderr, flush=True)
    except Exception:
        pass

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
    """Preserve previous Stage A and B1 servers for explicit recovery review."""
    if phase in ('stage-a','b1'):
        raise PreparationStop(f'STOP: live previous {phase} server; preserve without signalling')
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


def copy_dryrun_registry_snapshot(source, destination):
    """Create one synthetic snapshot without replacing existing evidence.

    A failed copy deliberately leaves any newly created partial file in place.
    """
    with source.open('rb') as src, destination.open('xb') as dst:
        shutil.copyfileobj(src, dst)


def placeholders(value, prefix=''):
    if isinstance(value,dict): return [p for k,v in value.items() if k!='comment' for p in placeholders(v,f'{prefix}.{k}')]
    if isinstance(value,list): return [p for i,v in enumerate(value) for p in placeholders(v,f'{prefix}[{i}]')]
    return [prefix] if isinstance(value,str) and value.startswith('TODO_') else []


def worker_environment(base=None):
    """Run node `python3` commands in the same environment as this runner."""
    env=dict(os.environ if base is None else base)
    env.update(PYTHONPATH=str(REPO),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    python_dir=Path(sys.executable).parent
    try:
        python3=python_dir/'python3'
        if not python3.is_file() or not os.access(python3,os.X_OK) or not os.path.samefile(python3,sys.executable):
            raise OSError('python3 is not an executable matching the runner interpreter')
    except OSError as exc:
        raise PreparationStop('STOP: B1 worker python3 does not match the runner interpreter') from exc
    env['PATH']=str(python_dir)+os.pathsep+env.get('PATH','')
    resolved=shutil.which('python3',path=env['PATH'])
    try:
        if not resolved or not os.path.samefile(resolved,sys.executable):
            raise OSError('PATH python3 differs from the runner interpreter')
    except OSError as exc:
        raise PreparationStop('STOP: B1 worker PATH resolves to a different python3') from exc
    return env


def b1_harness_sources(node, expected_commit):
    """Bind B1's editable starting bytes to a clean pinned harness checkout."""
    from r1.harness import harness_root
    from autoresearch.nodes.registry import load_registered_node
    harness=Path(harness_root()).resolve()
    try:
        head=subprocess.check_output(['git','-C',str(harness),'rev-parse','HEAD'],text=True).strip()
        dirty=subprocess.check_output(['git','-C',str(harness),'status','--porcelain'],text=True).strip()
    except (OSError,subprocess.SubprocessError) as exc:
        raise PreparationStop('STOP: B1 harness checkout cannot be verified') from exc
    if head!=expected_commit or dirty:
        raise PreparationStop('STOP: B1 harness checkout must be clean and pinned')
    spec=load_registered_node(node,repo_root=harness)
    node_dir=(harness/'nodes'/node).resolve()
    if not node_dir.is_relative_to(harness): raise PreparationStop('STOP: B1 node path escapes harness')
    result={}
    for rel in spec.editable_paths:
        path=(node_dir/rel).resolve()
        if not path.is_relative_to(node_dir) or not path.is_file(): raise PreparationStop('STOP: B1 editable source escapes node')
        result[rel]=digest_file(path)
    if not result: raise PreparationStop('STOP: B1 node editable sources are missing')
    return result


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
           'stage_a_amendment_table','stage_a_amendment_table_sha256','stage_a_amendment_acceptance','stage_a_amendment_acceptance_sha256',
           'authorizations'}
    common={k:v for k,v in cfg.items() if k not in later}
    if placeholders(common) and not allow_placeholders: raise ValueError(f'unresolved common placeholders: {placeholders(common)}')
    return cfg


def require_committed_b1_config(path, cfg):
    """Bind production B1's in-memory settings to the reviewed checkout.

    This is a point-in-time check under the existing cooperative checkout
    assumption; it does not protect against a concurrent repository writer.
    """
    expected=REPO/B1_CONFIG_REL
    try:
        # Other relative B1 inputs (rule, anchor JSON, authorization note,
        # value grids and the acceptance record) are consumed by older code
        # relative to cwd; refuse an alternate cwd rather than silently rebase.
        if Path.cwd().resolve() != REPO:
            raise ValueError('production B1 must start from the checkout root')
        supplied=Path(path).absolute()
        if supplied != expected or supplied.resolve(strict=True) != expected:
            raise ValueError('B1 requires the checkout config path without aliases')
        for part in (expected, expected.parent, expected.parent.parent, expected.parent.parent.parent):
            if part.is_symlink(): raise ValueError('B1 config path contains a symlink')
        head=subprocess.check_output(['git','-C',str(REPO),'rev-parse','--verify','HEAD'],text=True).strip()
        if not re.fullmatch(r'[0-9a-f]{40}',head): raise ValueError('invalid checkout HEAD')
        if subprocess.check_output(['git','-C',str(REPO),'status','--porcelain','--untracked-files=all'],text=True).strip():
            raise ValueError('checkout is not clean')
        _require_git_regular(head,B1_CONFIG_REL)
        blob=subprocess.check_output(['git','-C',str(REPO),'show',f'{head}:{B1_CONFIG_REL}'])
        if expected.read_bytes()!=blob or json.loads(blob)!=cfg:
            raise ValueError('config or loaded settings differ from committed HEAD')
        if subprocess.check_output(['git','-C',str(REPO),'rev-parse','--verify','HEAD'],text=True).strip()!=head:
            raise ValueError('checkout HEAD changed during config check')
        return head
    except (OSError,ValueError,TypeError,subprocess.SubprocessError) as exc:
        raise PreparationStop(f'STOP: B1 committed config verification failed: {exc}') from exc


def _require_git_regular(head, rel):
    """Reject a committed symlink, submodule, or unexpected tree entry."""
    row=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-z',head,'--',rel])
    expected_suffix=b'\t'+rel.encode()+b'\0'
    if not row.endswith(expected_suffix) or not re.fullmatch(rb'100(?:644|755) blob [0-9a-f]{40}\t[^\0]+\0',row):
        raise ValueError('committed input is not a regular Git blob')


def require_committed_b1_registry(cfg, head, *, selected_path=None, selected_registry=None):
    """Bind the actual B1 registry path, bytes, and optional parsed object to HEAD."""
    try:
        rel=cfg['registry']
        if not isinstance(rel,str) or not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise ValueError('invalid relative registry path')
        path=REPO/rel
        if path.resolve(strict=True)!=path:
            raise ValueError('registry path has an alias or symlink')
        if selected_path is not None and Path(selected_path)!=path:
            raise ValueError('registry override differs from committed config')
        _require_git_regular(head,rel)
        blob=subprocess.check_output(['git','-C',str(REPO),'show',f'{head}:{rel}'])
        if path.read_bytes()!=blob:
            raise ValueError('registry bytes differ from committed HEAD')
        if selected_registry is not None and selected_registry!=yaml.safe_load(blob):
            raise ValueError('loaded registry differs from committed HEAD')
        return path
    except (KeyError,OSError,ValueError,TypeError,subprocess.SubprocessError,yaml.YAMLError) as exc:
        raise PreparationStop(f'STOP: B1 committed registry verification failed: {exc}') from exc


def read_registry(path):
    data=yaml.safe_load(Path(path).read_text())
    all_rows=data['candidates']+data['software_anchors']
    ids=[x['id'] for x in all_rows]
    if len(set(ids))!=len(ids): raise ValueError('duplicate registry id')
    if {x['id'] for x in all_rows if x['role']=='candidate'}!=EXPECTED_CANDIDATES: raise ValueError('author pool is 20 candidates, no Ornith-31B or Qwopus-v4 substitute')
    if {x['id'] for x in all_rows if x['role']=='anchor'}!={'random_valid','scripted','qwen25_coder_7b'}: raise ValueError('three anchors required')
    return data


def _dryrun_temp_roots():
    """Select known temporary roots without tempfile's create/unlink probe.

    Respect an existing tempfile cache or the first usable POSIX environment
    candidate.  Directory and access checks are point-in-time only; unlike
    tempfile we deliberately do not fall back to the current working directory.
    """
    roots={Path('/tmp').resolve()}
    cached=tempfile.tempdir
    if cached is not None:
        roots.add(Path(os.fsdecode(cached)).absolute().resolve())
        return roots
    candidates=[os.environ.get(k) for k in ('TMPDIR','TEMP','TMP')]
    candidates.extend(['/tmp','/var/tmp','/usr/tmp'])
    for candidate in candidates:
        if not candidate:
            continue
        try:
            path=Path(os.fsdecode(candidate)).absolute()
            if path.is_dir() and os.access(path,os.W_OK | os.X_OK):
                roots.add(path.resolve())
                break
        except (OSError,TypeError,ValueError):
            continue
    return roots


def host_check(cfg, out):
    if cfg.get('dryrun'):
        forbidden={host.casefold() for host in APPROVED_EXAM_HOSTS}|{'ucrtasl'}
        if platform.node().split('.')[0].casefold() in forbidden:
            raise RuntimeError('STOP: EXAM DRYRUN needs a marked temporary root on a development host')
        root=Path(cfg['dryrun_root']).resolve();temps=_dryrun_temp_roots()
        if not any(root!=temp and root.is_relative_to(temp) for temp in temps) or not (root/'.dryrun').is_file():
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


def gpu_sample(cfg, capture=None):
    if cfg.get('dryrun'): return {'used_mib':6000,'free_mib':18000,'compute_pids':[],'device':0}
    argv=['nvidia-smi','--query-gpu=uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits']
    if capture is None:
        done=subprocess.run(argv,capture_output=True,text=True,check=True,timeout=15)
    else:
        done=capture(argv,timeout=15)
        if done.returncode: raise RuntimeError('STOP: contained GPU census failed')
    rows=[line.split(',') for line in done.stdout.splitlines()]
    row=next((r for r in rows if r[0].strip()==cfg['gpu_uuid']),None)
    if not row: raise RuntimeError('STOP: pinned GPU absent from census')
    return {'used_mib':float(row[1]),'free_mib':float(row[2]),'utilisation_percent':float(row[3]),'device':0}


def _x5_author_row(plan, rule_sha):
    """Require one dated §10 author decision row, not a prose mention."""
    section=False; dated=False; matches=[]; fence=None; comment=False; table=False; header=None
    for raw_line in plan.splitlines():
        # Reject raw HTML blocks in section 10 rather than interpreting their
        # contents as Markdown; an author can use ordinary Markdown instead.
        if section and not fence and not comment and re.match(r'^ {0,3}<(?:[A-Za-z][A-Za-z0-9-]*(?:\s|/?>)|\?|![A-Z])',raw_line):
            return False
        opening=re.match(r'^ {0,3}(`{3,}|~{3,})',raw_line)
        if fence:
            if re.match(r'^ {0,3}'+re.escape(fence[0])+r'{'+str(len(fence))+r',}\s*$',raw_line): fence=None
            table=False; header=None
            continue
        if opening:
            fence=opening.group(1); table=False; header=None; continue
        line=''; rest=raw_line
        while rest:
            if comment:
                end=rest.find('-->')
                if end<0: rest=''; break
                comment=False; rest=rest[end+3:]; continue
            start=rest.find('<!--')
            if start<0: line+=rest; break
            line+=rest[:start]; rest=rest[start+4:]; comment=True
        if not line.strip() or line.expandtabs(4).startswith('    '):
            table=False; header=None; continue
        if line.startswith('## '):
            section=bool(re.match(r'^## 10\.(?:\s|$)', line)); dated=False; table=False; header=None
            continue
        if not section:
            continue
        if line.startswith('### '):
            dated=False; table=False; header=None
            date=re.search(r'\b(?:\d{1,2}\s+[A-Za-z]+\s+20\d{2}|20\d{2}-\d{2}-\d{2})\b',line)
            if date and re.search(r'author',line,re.I):
                for fmt in ('%d %B %Y','%Y-%m-%d'):
                    try: datetime.datetime.strptime(date.group(0),fmt); dated=True; break
                    except ValueError: pass
            continue
        if not line.lstrip().startswith('|'):
            table=False; header=None
            continue
        parts=line.strip().split('|')
        cells=parts[1:-1] if parts[-1]=='' else parts[1:]
        separator=len(cells)>=2 and all(re.fullmatch(r'\s*:?-{3,}:?\s*',cell) for cell in cells)
        if separator:
            table=header==len(cells); header=None; continue
        if not table:
            header=len(cells) if len(cells)>=2 else None
            continue
        if len(cells)<2 or cells[0].strip()!='R1-EXAM-RULE-X5V2':
            continue
        decision=cells[1].strip()
        matches.append(dated and bool(decision) and bool(re.search(r'(?<![0-9a-fA-F])'+re.escape(rule_sha)+r'(?![0-9a-fA-F])',decision)))
    return len(matches)==1 and matches[0]


def _committed_b1_authority(cfg, note, raw, rule_sha):
    """Verify the host checkout's committed HEAD and local file bindings.

    Repository writers can still forge an approval; independent review and the
    author's instruction are the process boundary, not cryptographic identity.
    """
    if cfg.get('rule_sha256') != rule_sha:
        raise RuntimeError('STOP: configured rule sha256 mismatch')
    head=subprocess.check_output(['git','-C',str(REPO),'rev-parse','--verify','HEAD'],text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}',head): raise RuntimeError('STOP: invalid checkout HEAD')
    if subprocess.check_output(['git','-C',str(REPO),'status','--porcelain','--untracked-files=all'],text=True).strip():
        raise RuntimeError('STOP: host checkout must be clean')
    try:
        rel=note.resolve(strict=True).relative_to(REPO.resolve())
        committed=subprocess.check_output(['git','-C',str(REPO),'show',f'{head}:{rel.as_posix()}'])
        plan_raw=subprocess.check_output(['git','-C',str(REPO),'show',f'{head}:docs/r1/PLAN.md'])
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError('STOP: committed authorization or PLAN not available') from exc
    if committed!=raw: raise RuntimeError('STOP: authorization bytes differ from committed HEAD')
    if not _x5_author_row(plan_raw.decode('utf-8'),rule_sha):
        raise RuntimeError('STOP: dated §10 X5 rule decision and sha required')
    for path_key,sha_key in (('rule','rule_sha256'),('stage_a_table','stage_a_table_sha256'),
                             ('stage_a_amendment_table','stage_a_amendment_table_sha256'),
                             ('stage_a_amendment_acceptance','stage_a_amendment_acceptance_sha256')):
        path=Path(cfg[path_key]); path=path if path.is_absolute() else REPO/path
        expected=cfg[sha_key]
        if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected) or digest_file(path)!=expected:
            raise RuntimeError(f'STOP: {path_key} sha256 mismatch')
    return head


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
    plan_path=REPO/'docs/r1/PLAN.md'
    plan_raw=plan_path.read_bytes()
    plan=plan_raw.decode('utf-8')
    # B1 v2 checks a dated decision row and the clean committed host checkout.
    # Repository-writer forgery remains a process risk handled by independent review.
    try:
        loaded_rule, loaded_sha = load_rule(cfg['rule'], rule_sha)
    except (KeyError, OSError, ValueError, TypeError) as exc:
        raise RuntimeError('STOP: cannot verify authorization rule version') from exc
    if loaded_sha != rule_sha:
        raise RuntimeError('STOP: authorization rule digest mismatch')
    head=None
    if loaded_rule.get('version') == 'x5_rule/v2' and phase=='b1':
        head=_committed_b1_authority(cfg,note,raw,rule_sha)
    elif loaded_rule.get('version') == 'x5_rule/v2':
        raise RuntimeError('STOP: X5 v2 B2 authority and ranking are not implemented')
    elif not any(rule_sha in line and 'R1-EXAM-RULE' in line for line in plan.splitlines()):
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
    if phase=='b1' and loaded_rule.get('version')=='x5_rule/v2' and (type(data.get('workers')) is not int or data['workers']!=cfg.get('workers')):
        raise RuntimeError('STOP: worker count differs from authorization')
    if phase=='b1' and loaded_rule.get('version')=='x5_rule/v2':
        if data.get('host')!=cfg.get('host') or data.get('gpu_uuid')!=cfg.get('gpu_uuid') or not cfg.get('host') or not cfg.get('gpu_uuid'):
            raise RuntimeError('STOP: B1 host or GPU UUID differs from authorization')
        ref=cfg.get('anchor_duplicate_reference')
        if not isinstance(ref,dict) or not isinstance(ref.get('sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',ref['sha256']) or data.get('anchor_duplicate_reference_sha256')!=ref['sha256']:
            raise RuntimeError('STOP: anchor reference digest is not author-bound')
        try:
            source=Path(ref['source']);source=source if source.is_absolute() else REPO/source
            rel=source.resolve(strict=True).relative_to(REPO.resolve())
            recorded=subprocess.check_output(['git','-C',str(REPO),'show',f'{head}:{rel.as_posix()}'])
            actual=source.read_bytes()
        except (KeyError, TypeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
            raise RuntimeError('STOP: committed anchor reference unavailable') from exc
        if recorded!=actual or hashlib.sha256(actual).hexdigest()!=ref['sha256']:
            raise RuntimeError('STOP: committed anchor reference digest mismatch')
    return head


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


def _verify_b1_root_authority(path, expected_head):
    """Refuse roots produced under a different B1 authorization checkout."""
    job=json.loads((Path(path).parent/'job.json').read_text())
    if not re.fullmatch(r'[0-9a-f]{40}',str(expected_head or '')) or job.get('authorization_checkout_head')!=expected_head:
        raise PreparationStop('STOP: completed B1 root authorization HEAD mismatch')


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
    def __init__(self, cfg, out, *, registry_path=None, b1_config_head=None, b1_supervisor=None):
        raw_out=Path(out).expanduser()
        if b1_config_head is not None and not cfg.get('dryrun'):
            if not raw_out.is_absolute() or raw_out.is_symlink() or raw_out.resolve()!=raw_out:
                raise PreparationStop('STOP: production B1 output path must be absolute and non-aliased')
            if raw_out.parent != Path(cfg['work_dir']):
                raise PreparationStop('STOP: production B1 batch must be a direct work-directory child')
        self.cfg=cfg;self.out=raw_out.resolve();host_check(cfg,self.out)
        if b1_config_head is not None and not cfg.get('dryrun'):
            if registry_path is not None:
                raise PreparationStop('STOP: production B1 does not accept a registry override')
            self.registry_path=require_committed_b1_registry(cfg,b1_config_head)
        else:
            self.registry_path=Path(registry_path or cfg['registry']).resolve()
        self.registry=read_registry(self.registry_path)
        self.rule,self.rule_sha=load_rule(cfg['rule'],cfg['rule_sha256'])
        self.binding=hashlib.sha256(json.dumps({'config':cfg,'registry_sha256':digest_file(self.registry_path),'rule_sha256':self.rule_sha,'value_grids_sha256':digest_file(cfg['value_grids'])},sort_keys=True).encode()).hexdigest()
        self.service=None;self.child=None;self.state={};self.lock=None;self.author_head=None;self.b1_lease_fd=None;self.b1_config_head=b1_config_head;self.b1_supervisor=b1_supervisor;self.b1_containment=None;self.b1_batch_owned=False;self.b1_stop_created=False
        self.b1_state_identity=None
        if not cfg.get('dryrun'):
            from r1.harness import harness_root
            actual=subprocess.check_output(['git','-C',str(harness_root()),'rev-parse','HEAD'],text=True).strip()
            if actual!=cfg['harness_commit']: raise RuntimeError('STOP: harness commit mismatch')
            subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',cfg['paper_commit'],'HEAD'],check=True)
            changed=subprocess.check_output(['git','-C',str(REPO),'diff','--name-only',cfg['paper_commit'],'--','r1/exam','r1/scripts/exam_runner.py','r1/scripts/llama_server_instance.py','r1/scripts/llamacpp_probe.py','r1/headroom/e1b_collect.py'],text=True).strip()
            if changed: raise RuntimeError('STOP: exam code differs from pinned code commit')

    def space(self):
        if not self.cfg.get('dryrun'):
            if self.state.get('phase')=='b1' and self.b1_containment is not None:
                self.b1_containment.require_guardian()
            try:
                for key in ('models_dir','work_dir'): space_check(self.cfg[key])
            except (OSError,RuntimeError) as exc: raise PreparationStop(str(exc)) from exc

    def capture_b1_helper(self,argv,*,timeout):
        if self.b1_containment is None or self.b1_lease_fd is None:
            raise PreparationStop('STOP: B1 helper containment or lease unavailable')
        return self.b1_containment.capture_helper(argv,lease_fd=self.b1_lease_fd,timeout=timeout,cwd=REPO,check=self.space)

    def save(self):
        if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
            from r1.exam.b1_state_preserve import publish_state
            self.b1_state_identity=publish_state(self.out/'batch_state.json',self.state,self.b1_state_identity)
        else:
            write_json(self.out/'batch_state.json',self.state)

    def save_b1_stop(self, original):
        """Create one exclusive STOP record without replacing batch evidence."""
        if not self.b1_batch_owned:
            raise PreparationStop('STOP: no exclusively owned B1 batch for STOP record')
        if self.b1_stop_created:
            return
        payload=(json.dumps({'status':'STOPPED','error':f'{type(original).__name__}: {original}',
                             'phase':'b1','state':self.state},sort_keys=True,allow_nan=False)+'\n').encode()
        fd=os.open(self.out/'STOP.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:
            view=memoryview(payload)
            while view:
                written=os.write(fd,view)
                if written<=0: raise OSError('short STOP record write')
                view=view[written:]
            os.fsync(fd)
            self.b1_stop_created=True
        finally:
            os.close(fd)

    def start(self, phase):
        if phase=='stage-a':
            # Defense in depth: the reviewed cooperative D3 context must already
            # be authorized (guardian lease + explicit false) before any output,
            # server or worker exists.
            from r1.exam.cache_runtime import require_authorized_stagea
            require_authorized_stagea()
        if phase=='b2':
            raise PreparationStop('STOP: B2 reviewed observer integration is not implemented')
        if phase=='b1' and self.rule.get('version')!='x5_rule/v2':
            raise PreparationStop('STOP: B1 requires the reviewed x5_rule/v2')
        if phase=='b1':
            if not self.cfg.get('dryrun'):
                checked=require_committed_b1_config(REPO/B1_CONFIG_REL,self.cfg)
                if not self.b1_config_head or checked!=self.b1_config_head:
                    raise PreparationStop('STOP: B1 config HEAD changed before authorization')
                require_committed_b1_registry(self.cfg,checked,selected_path=self.registry_path,selected_registry=self.registry)
            self.author_head=author_gate(self.cfg,phase,self.rule_sha)
            if not self.cfg.get('dryrun') and (not self.b1_config_head or self.author_head!=self.b1_config_head):
                raise PreparationStop('STOP: B1 authorization HEAD differs from committed config HEAD')
        if phase=='b1': worker_environment()
        if phase=='b1' and not self.cfg.get('dryrun'):
            for node in self.cfg['nodes']: b1_harness_sources(node,self.cfg['harness_commit'])
            from r1.exam.b1_supervisor_contract import require_supervisor
            checked_supervisor=require_supervisor()
            if not self.b1_supervisor or checked_supervisor!=self.b1_supervisor:
                raise PreparationStop('STOP: B1 supervisor contract changed before output')
            self.b1_lease_fd=checked_supervisor['lease_fd']
        if phase=='stage-a':refuse_existing_stage_a_output(self.out)
        if phase=='b1' and not self.cfg.get('dryrun'):
            # An existing production batch could contain an unrecorded STOP.
            # Do not infer recovery permission from a missing STOP record.
            if self.out.parent != Path(self.cfg['work_dir']):
                raise PreparationStop('STOP: B1 batch must be a new direct child of the approved work directory')
            from r1.exam.b1_exit_receipt import _require_local_filesystem
            # Check the existing parent before creating any output; checking
            # the new child also detects a changed/overmounted path.  Type
            # checks do not establish rename error semantics or site approval.
            parent_mount=_require_local_filesystem(self.out.parent)
            try:
                self.out.mkdir(mode=0o700,parents=False,exist_ok=False)
                self.b1_batch_owned=True
            except FileExistsError as exc:
                raise PreparationStop('STOP: production B1 existing batch cannot be resumed automatically') from exc
            child_mount=_require_local_filesystem(self.out)
            if child_mount != parent_mount:
                raise PreparationStop('STOP: B1 batch mount differs from the work-directory mount')
            from r1.exam.b1_state_preserve import ACTIVE, write_exclusive_json
            write_exclusive_json(self.out/ACTIVE,{'version':'b1_active/v1','runner_pid':os.getpid(),
                                                  'authorization_checkout_head':self.author_head,
                                                  'mount_identity':list(child_mount)})
        else:
            self.out.mkdir(parents=True,exist_ok=True)
        path=self.out/'batch_state.json'
        if phase=='b1' and not self.cfg.get('dryrun'):
            from r1.exam.b1_state_preserve import existing_identity
            self.b1_state_identity=existing_identity(path)
        if path.exists():
            self.state=json.loads(path.read_text())
            if phase=='b1' and not self.cfg.get('dryrun') and existing_identity(path)!=self.b1_state_identity:
                raise PreparationStop('STOP: B1 batch state changed during resume read')
            reject_stopped_batch(self.state)
            if self.state['binding']!=self.binding or self.state['phase']!=phase: raise RuntimeError('STOP: resume identity/config/rule mismatch')
            for key,entry in self.state['completed'].items():
                if digest_file(entry['path'])!=entry['sha256']: raise RuntimeError(f'STOP: completed root changed: {key}')
                if phase!='stage-a':
                    verify_campaign(entry['path'],self.binding)
                    if digest_file(Path(entry['path']).parent/'post_check.json')!=entry['post_check_sha256']: raise PreparationStop('STOP: receiving certificate changed')
                    if phase=='b1' and not self.cfg.get('dryrun'):
                        _verify_b1_root_authority(entry['path'],self.author_head)
            previous=self.state.get('in_progress') or {}
            if phase=='b1' and not self.cfg.get('dryrun') and previous.get('path'):
                root=Path(previous['path'])
                if root.exists():
                    _verify_b1_root_authority(root/'campaign_manifest.json',self.author_head)
        else:
            snapshot=self.out/'registry_snapshot.yaml'
            if self.cfg.get('dryrun'):
                copy_dryrun_registry_snapshot(self.registry_path,snapshot)
            else:
                shutil.copyfile(self.registry_path,snapshot)
            self.state={'schema':'exam_batch/v1','label':'EXAM','execution_label':'DRYRUN' if self.cfg.get('dryrun') else ('ENGINEERING_ONLY' if phase=='stage-a' else 'EVIDENCE'),
                        'phase':phase,'binding':self.binding,'rule_sha256':self.rule_sha,'completed':{},'interruptions':[],'status':'RUNNING'}
        if phase=='b1' and not self.cfg.get('dryrun'):
            if require_supervisor()!=checked_supervisor:
                raise PreparationStop('STOP: B1 supervisor contract changed before guardian')
            from r1.exam.b1_cgroup import B1Containment
            self.b1_containment=B1Containment.__new__(B1Containment)
            def containment_receipt(record):
                self.state['b1_containment']=record
                self.save()
            self.b1_containment.initialize(self.b1_lease_fd,containment_receipt,
                                           checked_supervisor['pidfd'],checked_supervisor['live_fd'],checked_supervisor['handoff_fd'])
        lock=self.out/'runner.lock'
        if self.cfg.get('dryrun') and os.path.lexists(lock):
            raise RuntimeError('STOP: existing DRYRUN runner lock; preserve and do not resume')
        if lock.exists():
            if self.cfg.get('dryrun'):
                raise RuntimeError('STOP: concurrent DRYRUN runner lock; preserve and do not resume')
            old=json.loads(lock.read_text())
            try: os.kill(old['pid'],0)
            except ProcessLookupError: lock.rename(self.out/f'runner.lock.stale.{time.time_ns()}')
            else: raise RuntimeError('STOP: previous runner still alive; never share a campaign root')
        with lock.open('x') as f: json.dump({'pid':os.getpid(),'host':platform.node()},f)
        self.lock=lock
        if phase=='b1' and not self.cfg.get('dryrun'):
            lock_stat=lock.lstat()
            self.b1_lock_identity=(lock_stat.st_dev,lock_stat.st_ino,lock_stat.st_uid)
            self.b1_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest()
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
        if phase!='b1': author_gate(self.cfg,phase,self.rule_sha)
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
        if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
            build=lsi.build_info(server['binary'],capture=self.capture_b1_helper)
        else:
            build=lsi.build_info(server['binary'])
        if build['version_line']!=server['build']: raise RuntimeError('STOP: llama.cpp build pin mismatch')
        return build

    def _server(self, spec, mode, ctx):
        if self.state.get('phase')=='b1' and not self.cfg.get('dryrun') and getattr(self,'b1_lease_fd',None) is None:
            raise PreparationStop('STOP: B1 GPU lease is missing before server start')
        host_check(self.cfg,self.out)
        build=self.validate_spec(spec)
        model=spec['runtime']['model_path'];server=self.cfg['server']
        thinking={**spec['thinking_policy'],'mode':mode,'budget':2048 if mode!='off' else 0}
        args=list(EXAM_SERVER_ARGS)+template_repair_args(spec)
        inst=lsi.LlamaServerInstance(self.out/'servers'/spec['id'],server['binary'],model_path=model,alias=spec['id'],
                                   ctx_size=ctx,n_gpu_layers=999,gpu_uuid=self.cfg['gpu_uuid'],extra_args=args,
                                   thinking_policy=thinking,generation=len(list((self.out/'servers'/spec['id']).glob('*.json'))),
                                   label=self.state['execution_label'],start_timeout=server['start_timeout'],
                                   env_extra={'R1_SYNTHETIC_PARENT_PID':str(os.getpid())} if self.cfg.get('dryrun') and os.environ.get('C3_FAKE_EXIT_IF_ORPHANED')=='1' else None)
        lease_fd=None
        if self.state.get('phase')=='stage-a':
            # The native server must inherit the verified lease OFD; the start
            # verification STOPs before any request if that chain is unproved.
            from r1.exam.cache_runtime import verified_lease_fd
            lease_fd=verified_lease_fd()
        if not self.cfg.get('dryrun'):
            if self.state.get('phase')=='b1':
                help_result=self.capture_b1_helper([server['binary'],'--help'],timeout=20)
                if help_result.returncode: raise PreparationStop('STOP: contained server --help failed')
                help_text=help_result.stdout+help_result.stderr
            else:
                help_text=subprocess.check_output([server['binary'],'--help'],text=True,stderr=subprocess.STDOUT,timeout=20)
            required=['--chat-template-kwargs'] if thinking.get('off_switch') else []
            if mode!='off': required+=['--reasoning-budget']
            if any(flag not in help_text for flag in required): raise RuntimeError('STOP: pinned build lacks thinking-control flags')
            if self.state.get('phase')=='b1':
                apps=lsi.gpu_compute_apps(capture=self.capture_b1_helper);sample=gpu_sample(self.cfg,capture=self.capture_b1_helper)
            else:
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
                try:
                    if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
                        self.b1_containment.observe_check(self.space)
                    else:
                        self.space()
                except Exception as exc:
                    disk_error.append(str(exc))
                    if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
                        self.b1_containment.freeze()
                    elif self.state.get('phase')!='stage-a' and inst.process is not None and inst.record.get('pgid'): inst.stop()
                    break
        monitor=threading.Thread(target=watch_loading,daemon=True);monitor.start()
        try:
            from r1.exam.b1_lease import B1LeaseStop
            from r1.exam.b1_cgroup import ContainmentStop
            contained = self.state.get('phase')=='b1' and not self.cfg.get('dryrun')
            extra = ({'b1_containment':self.b1_containment, 'b1_cancelled':lambda: bool(disk_error)} if contained else {})
            try: inst.start(build=build,model_sha256=spec['quant_source']['sha256'],
                            preserve_on_failure=self.state.get('phase')=='stage-a' or contained,lease_fd=lease_fd,
                            b1_lease_fd=self.b1_lease_fd if self.state.get('phase')=='b1' and not self.cfg.get('dryrun') else None,
                            **extra)
            except LeaseStop as exc:
                raise PreparationStop(f'STOP: cooperative lease inheritance failed: {exc}') from exc
            except B1LeaseStop as exc:
                raise PreparationStop(str(exc)) from exc
            except ContainmentStop as exc:
                raise PreparationStop(str(exc)) from exc
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
        apps=([] if self.cfg.get('dryrun') else
              lsi.gpu_compute_apps(capture=self.capture_b1_helper) if self.state.get('phase')=='b1' else None)
        report=inst.offload(footprint_mib=spec['runtime']['footprint_mib'],apps=apps)
        write_json(inst.batch/'exam_offload.json',report)
        if not report['full']: raise MechanicalFailure('full GPU offload not established')
        if spec['id'] not in (inst.model_ids() or []): raise PreparationStop('STOP: served alias identity mismatch')
        if (inst.props() or {}).get('model_path')!=model: raise RuntimeError('STOP: served GGUF path mismatch')
        return inst

    def run_job(self, job, module, *, interrupt=False):
        if interrupt and self.state.get('phase')=='stage-a':
            raise PreparationStop('STOP: Stage A workers must not be signalled')
        self.space()
        path=Path(job['out'])
        contained = self.state.get('phase')=='b1' and not self.cfg.get('dryrun')
        def prepare_output():
            # A production batch is exclusive and cannot be resumed.  Refuse an
            # existing campaign root instead of writing into another scene.
            path.mkdir(parents=True,exist_ok=not contained)
            write_json(path/'job.json',job)
        if contained: self.b1_containment.write_active(prepare_output)
        else: prepare_output()
        env=(worker_environment() if self.state.get('phase')=='b1' else
             {**os.environ,'PYTHONPATH':str(REPO),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
        if self.cfg.get('dryrun') and env.get('C3_FAKE_EXIT_IF_ORPHANED')=='1':
            env['R1_SYNTHETIC_PARENT_PID']=str(os.getpid())
        if self.service: env['LLAMACPP_BASE_URL']=self.service.openai_base_url
        kwargs={}
        if self.state.get('phase')=='stage-a':
            from r1.exam.cache_runtime import verified_lease_fd
            kwargs['pass_fds']=(verified_lease_fd(),)
        elif self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
            if self.b1_lease_fd is None: raise PreparationStop('STOP: B1 GPU lease is missing')
            kwargs['pass_fds']=(self.b1_lease_fd,)
        def open_log(): return (path/'runner.log').open('ab')
        log=self.b1_containment.write_active(open_log) if contained else open_log()
        with log:
            argv=[sys.executable,'-m',module,'--job',str(path/'job.json')]
            if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
                self.child=self.b1_containment.spawn('worker',argv,env=env,cwd=REPO,stdout=log,
                                                     lease_fd=self.b1_lease_fd,
                                                     worker_context={'job':job,'out':path,'server':self.service,
                                                                     'supervisor':self.b1_supervisor})
            else:
                self.child=subprocess.Popen(argv,env=env,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,**kwargs)
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
                    if self.state.get('phase')=='b1':
                        from r1.exam.b1_lease import verify_server_fd
                        verify_server_fd(self.b1_lease_fd,self.service.process.pid)
                        self.b1_containment.verify_live_lease(self.service.process,self.b1_lease_fd)
                    if self.state.get('phase')=='b1':
                        apps=lsi.gpu_compute_apps(capture=self.capture_b1_helper);sample=gpu_sample(self.cfg,capture=self.capture_b1_helper)
                    else:
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
            if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
                self.b1_containment.require_worker_empty(self.child)
        except BaseException as exc:
            if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
                try:
                    self.b1_containment.freeze()
                except Exception as freeze_error:
                    report_b1_freeze_failure(exc,freeze_error)
            elif self.child.poll() is None and self.state.get('phase')!='stage-a':
                stop_tree(self.child.pid);self.child.wait(timeout=30)
            self.state['interruptions'].append({'path':str(path),'error':str(exc),'returncode':self.child.returncode,'killed':killed,'time':time.time()})
            if self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
                report_b1_stop_and_save(self,exc,append_only=True)
            else:
                self.save()
            raise
        self.child=None

    def root(self, spec, phase, node, seed, mode, *, interrupt=False):
        self.space()
        key=f'{spec["id"]}/{phase}/{mode}/{node}__s{seed}'
        if key in self.state['completed']:
            saved=self.state['completed'][key]['path']
            result=verify_campaign(saved,self.binding)
            if phase=='b1' and self.rule.get('version')=='x5_rule/v2' and not self.cfg.get('dryrun'):
                _verify_b1_root_authority(saved,self.author_head)
            return result
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
                if phase=='b1' and self.rule.get('version')=='x5_rule/v2' and not self.cfg.get('dryrun'):
                    _verify_b1_root_authority(finished,self.author_head)
                self.state['completed'][key]={'path':str(finished),'sha256':digest_file(finished),'post_check_sha256':digest_file(path/'post_check.json')}
                self.state.pop('in_progress',None);self.save();return recovered
            archived=self.out/'interrupted'/f'{time.time_ns()}_{spec["id"]}_{node}_s{seed}'
            archived.parent.mkdir(exist_ok=True);path.rename(archived)
        job={'out':str(path),'binding':self.binding,'workers':self.cfg['workers'],'host':self.cfg['host'],'phase':phase,'node':node,'seed':seed,'candidate':spec,'mode':mode,
             'dryrun':bool(self.cfg.get('dryrun')),'W':self.cfg['W'],'llm_call_cap':self.cfg['llm_call_cap'],
             'audit_seeds':self.cfg['audit_seeds'] if phase=='b1' else list(range(9201,9211)),
             'base_url':self.service.openai_base_url if self.service else None,'value_grids':self.cfg['value_grids'],
             'proposal_schema':None if self.cfg.get('free_sensitivity') else 'manager_proposal/v1'}
        if phase=='b1' and self.rule.get('version')=='x5_rule/v2':
            if not job['dryrun'] and not re.fullmatch(r'[0-9a-f]{40}',str(self.author_head or '')):
                raise PreparationStop('STOP: B1 worker needs the authorized checkout HEAD')
            job['authority_config']=copy.deepcopy(self.cfg)
            job['authorization_checkout_head']=self.author_head
            if not job['dryrun']:
                job['harness_commit']=self.cfg['harness_commit']
                job['node_source_sha256']=b1_harness_sources(node,self.cfg['harness_commit'])
        self.run_job(job,'r1.exam.campaign',interrupt=interrupt)
        manifest=path/'campaign_manifest.json'
        check={'binding':self.binding,'manifest_sha256':digest_file(manifest),'passed':True,'software_anchor':self.service is None}
        if self.service:
            apps=([] if self.cfg.get('dryrun') else
                  lsi.gpu_compute_apps(capture=self.capture_b1_helper) if phase=='b1' else None)
            report=self.service.offload(footprint_mib=spec['runtime']['footprint_mib'],apps=apps)
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

    def close(self, *, preserve_running=False, defer_b1_lease=False):
        if preserve_running:
            # Preserve server, worker, and marker after STOP for explicit review.
            return
        self.stop_service()
        if self.lock and self.state.get('phase')=='b1' and not self.cfg.get('dryrun'):
            from r1.exam.b1_cgroup import retire_runner_lock
            retire_runner_lock(self.lock,self.b1_lock_identity,self.b1_lock_sha256)
            self.lock=None
        if getattr(self,'b1_containment',None) is not None and defer_b1_lease:
            self.b1_containment.require_finish_ready()
        if getattr(self,'b1_containment',None) is not None and not defer_b1_lease:
            self.b1_containment.finish()
        if self.lock and self.cfg.get('dryrun'):
            # Keep the test-owned lock in place. An existing lock must not be
            # removed merely because a synthetic runner closes: it remains
            # evidence, and an attempted same-process restart must refuse it.
            self.lock=None
        if self.lock: self.lock.unlink(missing_ok=True);self.lock=None
        if getattr(self,'b1_lease_fd',None) is not None and not defer_b1_lease:
            os.close(self.b1_lease_fd);self.b1_lease_fd=None

    def finish_b1_lease(self):
        """Finish only after the final state write; caller retains STOP handling."""
        if self.b1_containment is None or self.b1_lease_fd is None:
            raise PreparationStop('STOP: B1 containment or lease absent at finish')
        self.b1_containment.finish()
        os.close(self.b1_lease_fd);self.b1_lease_fd=None
