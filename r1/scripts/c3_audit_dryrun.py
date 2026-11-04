"""Dry run of the sweep-1 B.2 audit plan (DRYRUN; no worker run). AI-assisted (Claude), M3 of MAC_LOCAL_RUNBOOK_20261104.

Against a *copy* of the frozen B.1 corpus layout (the classification sidecar, the
SHA256-bound index and both relocated sweep directories), this:

1. verifies the copy (index and sidecar SHA256, manifest SHA256, original-blob
   mapping when the copy is a Git checkout);
2. builds the C3 proposal table from the relocated ledgers exactly as
   ``r1.c3.dataset.build_from_sweep`` does (same replay and row format) into a
   temporary directory outside the corpus;
3. partitions the complete population with ``r1.c3.audit.partition_population``
   (the function ``evidence_plan`` uses): rule no-ops, duplicates (never audited,
   never labelled) and eligible proposals (all audited, inclusion probability 1);
4. checks the declared audit design: K = 10, label seeds 7001-7005 and evaluation
   seeds 7006-7010, disjoint, never mixed in one block;
5. runs ``r1.c3.audit.evidence_blocks`` on **synthetic placeholder metrics** (not a
   worker run, never a label) to check the block rules: one label row per no-op
   (``rule_noop``) and per eligible proposal, none per duplicate, evaluation rows only
   for eligible proposals, seeds of each block from its own role only;
6. reports counts by kind (overall, by node, by memory mode), the unique
   configurations and the planned seed runs.

It writes only the report directory given by ``--out``. Nothing here is evidence.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import tempfile
from pathlib import Path

from r1.c3.audit import DEFAULT_SEEDS, evidence_blocks, partition_population, split_seeds

INDEX = 'results/r1/pilot/C3_sweep_index_20261028T033315Z.json'
SIDECAR = 'results/r1/evidence/C3_sweep_classification_20261028.json'
LABEL_SEEDS = tuple(range(7001, 7006))
EVALUATION_SEEDS = tuple(range(7006, 7011))
K = 10


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def design_check() -> dict:
    label, evaluation = split_seeds(DEFAULT_SEEDS)
    if len(DEFAULT_SEEDS) != K or tuple(label) != LABEL_SEEDS or tuple(evaluation) != EVALUATION_SEEDS or \
            set(label) & set(evaluation):
        raise ValueError('audit seed design differs from K = 10, 7001-7005 label, 7006-7010 evaluation')
    return {'k': K, 'label_seeds': list(label), 'evaluation_seeds': list(evaluation), 'disjoint': True}


def build_table(paper: Path, out: Path, *, verify_git: bool = True) -> dict:
    """Same steps as build_from_sweep with the classification, minus its publication check."""
    from r1.c3 import dataset
    paper = Path(paper).resolve()
    index_path = paper / INDEX
    index = json.loads(index_path.read_text())
    decision = json.loads((paper / SIDECAR).read_text())
    if _sha(index_path) != decision['index']['sha256']:
        raise ValueError('index copy differs from the classification sidecar')
    for entry in decision['sweeps']:
        if _sha(paper / entry['new_dir'] / 'manifest.json') != entry['manifest_sha256']:
            raise ValueError(f'manifest copy differs for {entry["memory_mode"]}')
    if verify_git:
        dataset._verify_original_blobs(paper, index, decision['sweeps'])
    specs = dataset.sweep_sources(index, index_path, paper, None, decision)
    noise = dataset.noise_table(paper / index['noise_source']['path'])
    rows, configs, checks = dataset._replay_sources(specs, noise, strict_start_files=True)
    out.mkdir(parents=True, exist_ok=False)
    head = {'label': 'DRYRUN', 'classification': {'sha256': _sha(paper / SIDECAR)},
            'sweep_index': {'sha256': _sha(index_path)}}
    meta = dataset._write_table(out, rows, configs, checks, head, noise)
    return {'index': index, 'meta': meta, 'original_blobs_verified': verify_git}


def synthetic_results(plan: list[dict]) -> list[dict]:
    """Placeholder per-seed metrics shaped like audit_results; deterministic, not from any run."""
    out = []
    for p in plan:
        cm = [0.5 + 0.001 * (i % 3) for i in range(K)]
        im = [0.5 + 0.001 * (i % 2) for i in range(K)]
        out.append({'proposal_id': p['proposal_id'], 'node': p['node'], 'reason': p['reason'],
                    'candidate_hash': p['candidate_hash'], 'incumbent_hash': p['incumbent_hash'],
                    'seeds': list(DEFAULT_SEEDS), 'candidate_metrics': cm, 'incumbent_metrics': im})
    return out


def block_checks(table: Path, rows: list[dict], plan: list[dict]) -> dict:
    from r1.c3.arms import is_duplicate, is_noop
    labels, evaluations = evidence_blocks(table, synthetic_results(plan))
    kinds = {r['proposal_id']: 'noop' if is_noop(r) else 'duplicate' if is_duplicate(r) else 'eligible' for r in rows}
    label_ids = collections.Counter(r['proposal_id'] for r in labels)
    problems = []
    if any(v != 1 for v in label_ids.values()):
        problems.append('a proposal has more than one label row')
    if any(kinds[p] == 'duplicate' for p in label_ids):
        problems.append('a duplicate received a label')
    if {p for p in kinds if kinds[p] != 'duplicate'} != set(label_ids):
        problems.append('label block does not cover every no-op and eligible proposal')
    if any(r['label_kind'] != 'rule_noop' for r in labels if kinds[r['proposal_id']] == 'noop'):
        problems.append('a no-op is not labelled by rule')
    if any(r.get('delta_label') != 0.0 or r.get('se_label') != 0.0 for r in labels if r['label_kind'] == 'rule_noop'):
        problems.append('a rule no-op label is not exactly zero')
    if any(r.get('seeds') != list(LABEL_SEEDS) for r in labels if r['label_kind'] == 'audit'):
        problems.append('an audit label uses seeds outside 7001-7005')
    if any(r.get('seeds') != list(EVALUATION_SEEDS) for r in evaluations):
        problems.append('an evaluation row uses seeds outside 7006-7010')
    if {r['proposal_id'] for r in evaluations} != {p['proposal_id'] for p in plan}:
        problems.append('evaluation block does not equal the eligible set')
    if any(set(r) & {'delta_evaluation', 'se_evaluation'} for r in labels) or \
            any(set(r) & {'delta_label', 'se_label', 'soft_parameters'} for r in evaluations):
        problems.append('a block carries the other role\'s values')
    if problems:
        raise ValueError('; '.join(problems))
    return {'label_rows': len(labels), 'label_rows_rule_noop': sum(r['label_kind'] == 'rule_noop' for r in labels),
            'label_rows_audit': sum(r['label_kind'] == 'audit' for r in labels),
            'evaluation_rows': len(evaluations), 'duplicates_labelled': 0,
            'metrics': 'synthetic placeholders; checks block structure only, never a label value'}


def dryrun(paper: Path, out: Path, *, verify_git: bool = True) -> dict:
    from r1.c3.arms import is_duplicate, is_noop
    from r1.c3.dataset import load_table
    out = Path(out)
    if out.exists():
        raise ValueError('report directory must be new')
    design = design_check()
    with tempfile.TemporaryDirectory(prefix='r1_c3_audit_dryrun_') as tmp:
        table = Path(tmp) / 'table'
        built = build_table(paper, table, verify_git=verify_git)
        rows = load_table(table)
        configs = json.loads((table / 'configs.json').read_text())
        plan, counts = partition_population(rows, configs)
        blocks = block_checks(table, rows, plan)
        by = collections.defaultdict(collections.Counter)
        for r in rows:
            kind = 'noop' if is_noop(r) else 'duplicate' if is_duplicate(r) else 'eligible'
            by[('node', r['node'])][kind] += 1
            by[('memory_mode', r['memory_mode'])][kind] += 1
            by[('noop_kind', r.get('noop_kind') or '-')][kind] += 1 if kind == 'noop' else 0
        unique = len({(p['node'], p[k]) for p in plan for k in ('candidate_hash', 'incumbent_hash')})
        report = {
            'label': 'DRYRUN', 'ai_assisted': 'AI-assisted (Claude)',
            'corpus_copy': str(Path(paper).resolve()),
            'index_sha256': _sha(Path(paper) / INDEX), 'sidecar_sha256': _sha(Path(paper) / SIDECAR),
            'original_blobs_verified': built['original_blobs_verified'],
            'design': design,
            'table': {'proposals': len(rows), 'configs': len(configs),
                      'replay_checks_total': built['meta']['replay_checks_total'],
                      'proposals_sha256': _sha(table / 'proposals.jsonl'), 'configs_sha256': _sha(table / 'configs.json')},
            'counts': counts,
            'counts_by_node': {k[1]: dict(v) for k, v in sorted(by.items()) if k[0] == 'node'},
            'counts_by_memory_mode': {k[1]: dict(v) for k, v in sorted(by.items()) if k[0] == 'memory_mode'},
            'noop_kinds': {k[1]: v['noop'] for k, v in sorted(by.items()) if k[0] == 'noop_kind' and k[1] != '-'},
            'unique_audit_configs': unique, 'planned_seed_runs': unique * K,
            'blocks': blocks,
        }
    out.mkdir(parents=True)
    (out / 'audit_dryrun.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--paper-root', required=True, help='a copy of the frozen corpus layout (Git checkout)')
    ap.add_argument('--out', required=True, help='new report directory')
    ap.add_argument('--no-git', action='store_true', help='skip the original-blob check (copy without history)')
    args = ap.parse_args(argv)
    report = dryrun(Path(args.paper_root), Path(args.out), verify_git=not args.no_git)
    print(json.dumps({k: report[k] for k in ('counts', 'unique_audit_configs', 'planned_seed_runs', 'blocks')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
