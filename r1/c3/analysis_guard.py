"""Pre-analysis protection for sweep-2 and sealed artefacts.

The PLAN row and gate bytes in the checkout are authoritative for this check.
Only the frozen sweep-1 index and the declared legacy pilot source definitions
are recognised without it. Unknown provenance fails closed. Metadata is a
process boundary, not a cryptographic guarantee against a repository writer
relabeling both table and provenance; independent review remains necessary.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from r1.harness import REPO

SWEEP1_INDEX_SHA = '812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab'
SWEEP1_INDEX_PATH = 'results/r1/pilot/C3_sweep_index_20261028T033315Z.json'


def refuse_sealed(*paths):
    """Refuse lexical and symlink-resolved r1_sealed paths before opening."""
    for raw in paths:
        if raw is None:
            continue
        path = Path(raw).expanduser()
        if any(part.casefold() == 'r1_sealed' for part in (*path.parts, *path.resolve().parts)):
            raise RuntimeError('STOP: r1_sealed paths are not analysis inputs')


def _author_heading(line):
    """Return 0 for invalid, 1 for dated, 2 for dated with an author marker."""
    match = re.search(r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b', line, re.I)
    if not match:
        return 0
    months = ('january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november', 'december')
    try:
        date(int(match.group(3)), months.index(match.group(2).casefold()) + 1, int(match.group(1)))
    except ValueError:
        return 0
    if re.search(r'\b(?:not|non|no|without|never)[-\s]+(?:an?\s+|the\s+)?author\b', line, re.I):
        return 0
    explicit = re.search(r"\bauthor(?:'s)?\s+(?:decisions?|rulings?|adoption)\b|\(\s*author\s*(?:[;,)])|\bauthor\s*$", line, re.I)
    return 2 if explicit else 1


def _decision_header(cells):
    if len(cells) < 2:
        return False
    first, second = (c.strip().strip('*` ').casefold() for c in cells[:2])
    if first not in {'id', 'decision', 'row'}:
        return 0
    if re.fullmatch(r"author(?:'s)?\s+decision(?:\s*\([^()]*\))?", second):
        return 2
    return 1 if re.fullmatch(r"decision(?:\s*\([^()]*\))?", second) else 0


def _confirm_row(plan, gate_sha):
    section=False; dated_author=False; fenced=None; comment=False; html=None; header=None; table=False
    for raw in plan.splitlines():
        if html:
            if re.search(r'</'+re.escape(html)+r'\s*>',raw,re.I): html=None
            header=None;table=False;continue
        marker=re.match(r'^ {0,3}(`{3,}|~{3,})',raw)
        if fenced:
            if re.match(r'^ {0,3}'+re.escape(fenced[0])+r'{'+str(len(fenced))+r',}\s*$',raw): fenced=None
            header=None;table=False
            continue
        if marker:
            fenced=marker.group(1);header=None;table=False;continue
        line=''; rest=raw
        while rest:
            if comment:
                pos=rest.find('-->')
                if pos<0: rest='';break
                rest=rest[pos+3:];comment=False;continue
            pos=rest.find('<!--')
            if pos<0: line+=rest;break
            line+=rest[:pos];rest=rest[pos+4:];comment=True
        if not line.strip() or line.expandtabs(4).startswith('    '):
            header=None;table=False;continue
        tag=re.match(r'^ {0,3}<([A-Za-z][\w-]*)\b[^>]*>',line)
        if tag:
            if not re.search(r'</'+re.escape(tag.group(1))+r'\s*>',line,re.I): html=tag.group(1)
            header=None;table=False;continue
        if line.startswith('## '):
            section=bool(re.match(r'^## 10\.(?:\s|$)',line));dated_author=False;header=None;table=False;continue
        if line.startswith('### '):
            dated_author=_author_heading(line) if section else 0
            header=None;table=False;continue
        if line.startswith('#'):
            dated_author=False;header=None;table=False;continue
        if not section or not dated_author or not line.lstrip().startswith('|'):
            header=None;table=False;continue
        parts=line.strip().split('|');cells=parts[1:-1] if parts[-1]=='' else parts[1:]
        sep=len(cells)>=2 and all(re.fullmatch(r'\s*:?-{3,}:?\s*',c) for c in cells)
        if sep:
            table=header if header==len(cells) else False;header=None;continue
        if not table:
            strength=_decision_header(cells)
            header=len(cells) if strength and (dated_author==2 or strength==2) else None;continue
        if len(cells)!=table: continue
        first=cells[0].strip().strip('*` ')
        if first != 'R1-BX-D8-CONFIRM': continue
        decision=cells[1].strip()
        if decision and re.search(r'(?<![0-9a-fA-F])'+re.escape(gate_sha)+r'(?![0-9a-fA-F])',decision): return True
    return False


def require_d8_confirmation():
    gate=REPO/'r1/c3/gate.py'; plan=REPO/'docs/r1/PLAN.md'
    refuse_sealed(gate, plan)
    root=REPO.resolve()
    for path in (plan,gate):
        if path.is_symlink() or path.resolve() != root/path.relative_to(REPO):
            raise RuntimeError('STOP: D8 authority path is a symlink or alias')
        if not path.is_file():
            raise RuntimeError('STOP: R1-BX-D8-CONFIRM or gate code absent')
    try:
        head=subprocess.check_output(['git','-C',str(REPO),'rev-parse','--verify','HEAD'],stderr=subprocess.DEVNULL).decode('ascii').strip()
        if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})',head):
            raise ValueError('invalid HEAD object ID')
        paths=('docs/r1/PLAN.md','r1/c3/gate.py')
        entries=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-z',head,'--',*paths],stderr=subprocess.DEVNULL)
        seen={}
        for entry in entries.split(b'\0'):
            if not entry: continue
            meta,name=entry.split(b'\t',1)
            mode,kind,oid=meta.split(b' ')
            if name in seen or mode not in (b'100644',b'100755') or kind!=b'blob' or not re.fullmatch(rb'(?:[0-9a-f]{40}|[0-9a-f]{64})',oid):
                raise ValueError('non-regular or malformed committed authority')
            seen[name]=True
        if set(seen)!={p.encode('ascii') for p in paths}:
            raise ValueError('committed authority entries missing')
        committed_plan=subprocess.check_output(['git','-C',str(REPO),'show',head+':docs/r1/PLAN.md'],stderr=subprocess.DEVNULL)
        committed_gate=subprocess.check_output(['git','-C',str(REPO),'show',head+':r1/c3/gate.py'],stderr=subprocess.DEVNULL)
        if committed_plan != plan.read_bytes():
            raise RuntimeError('STOP: PLAN differs from committed HEAD')
        if committed_gate != gate.read_bytes():
            raise RuntimeError('STOP: gate SHA source differs from committed HEAD')
        gate_sha=hashlib.sha256(committed_gate).hexdigest()
        if not _confirm_row(committed_plan.decode('utf-8'),gate_sha):
            raise RuntimeError('STOP: R1-BX-D8-CONFIRM with current gate SHA required')
        current_head=subprocess.check_output(['git','-C',str(REPO),'rev-parse','--verify','HEAD'],stderr=subprocess.DEVNULL).decode('ascii').strip()
        if head != current_head:
            raise RuntimeError('STOP: checkout HEAD changed during D8 check')
    except (OSError,subprocess.CalledProcessError,UnicodeError,ValueError) as exc:
        raise RuntimeError('STOP: committed PLAN or regular gate code unavailable') from exc
    # The structural parser accepts any nonempty cell containing the SHA, even
    # a negative decision. Until an actual author decision and its meaning have
    # been independently reviewed, matching syntax cannot open this gate.
    raise RuntimeError('STOP: D8 decision semantics require independent review')


def _index_is_frozen_sweep1(meta):
    idx=meta.get('sweep_index')
    if not isinstance(idx,dict) or idx.get('sha256')!=SWEEP1_INDEX_SHA:
        return False
    path=Path(idx.get('path',''))
    refuse_sealed(path)
    suffix=Path(SWEEP1_INDEX_PATH).parts
    if path.resolve().parts[-len(suffix):]!=suffix or not path.is_file(): return False
    return hashlib.sha256(path.read_bytes()).hexdigest()==SWEEP1_INDEX_SHA


def _legacy_pilot(meta):
    # Historical `dataset.build` emits the full frozen source definitions;
    # a bare label supplied by a caller is never enough to identify a pilot.
    from r1.c3.dataset import SOURCES
    sources=meta.get('sources')
    return (not meta.get('sweep_index') and meta.get('label')=='ENGINEERING_ONLY'
            and isinstance(sources,dict) and bool(sources)
            and all(k in SOURCES and v==SOURCES[k] for k,v in sources.items())
            and isinstance(meta.get('replay_checks_total'),dict))


def guard_table(table_dir, *extra_paths):
    """Check provenance before opening proposal/audit label files.

    Metadata inspection is permitted; it must not contain label values. Sweep-2
    and unknown provenance require D8 confirmation. Known sweep-1 and legacy
    pilot source schemas retain their existing paths. All given input paths are
    checked for sealed-tree traversal independently of the D8 row.
    """
    table=Path(table_dir)
    refuse_sealed(table,*extra_paths)
    for path in extra_paths:
        path=Path(path)
        if path.parent.resolve() != table.resolve() or path.resolve().parent != table.resolve():
            require_d8_confirmation()
    meta_path=table/'build.json'
    refuse_sealed(meta_path)
    try:
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        require_d8_confirmation();return
    if not isinstance(meta,dict):
        require_d8_confirmation();return
    if not (_index_is_frozen_sweep1(meta) or _legacy_pilot(meta)):
        require_d8_confirmation()
