#!/usr/bin/env python3
"""B2 host preflight: the B1 owned-server/anchor probe driven by the B2 config and gate.

The reviewed B1 host preflight (`r1/scripts/b1_host_preflight.py`) hard-codes the B1 config,
phase and code pin; for B2 the hand-off asks for the same pattern "re-reviewed for this HEAD and
run ID". This wrapper keeps every B1 probe step (`b1_host_preflight.run`: idle-GPU/lock checks,
owned anchor server, descriptor/offload checks, owned stop, lease release) and replaces only the
input/gate function with the B2 config, B2 committed-head/gate and B2 pins. Run from the staged
checkout with PYTHONPATH=that checkout and AR_HARNESS_ROOT set.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import r1.scripts.b1_host_preflight as bp
from r1.exam.analyze import load_rule
from r1.exam.guards import space_check
from r1.exam.observer import _authorized_candidate  # noqa: F401 (parity with the B1 module)
from r1.exam.runtime import (B2_CONFIG_REL, REPO, ExamRunner, author_gate, b1_harness_sources,
                             host_check, load_config, read_registry,
                             require_committed_b1_config, require_committed_b1_registry,
                             worker_environment)
from r1.scripts.exam_runner import (check_template_repairs, refuse_cache_prompt_override,
                                    stage_a_pass_set, verify_anchor_reference)


def b2_check_inputs(expected_head, out):
    """B2 twin of b1_host_preflight.check_inputs: same validation, B2 config and phase."""
    cfg = load_config(REPO / B2_CONFIG_REL)
    if cfg.get('dryrun'):
        raise RuntimeError('STOP: preflight requires committed production config')
    head = require_committed_b1_config(REPO / B2_CONFIG_REL, cfg, rel=B2_CONFIG_REL)
    if head != expected_head:
        raise RuntimeError('STOP: reviewed HEAD mismatch')
    registry = read_registry(cfg['registry'])
    require_committed_b1_registry(cfg, head, selected_path=REPO / cfg['registry'],
                                  selected_registry=registry)
    rule, rule_sha = load_rule(cfg['rule'], cfg['rule_sha256'])
    if rule.get('version') != 'x5_rule/v2' or author_gate(cfg, 'b2', rule_sha) != head:
        raise RuntimeError('STOP: committed B2 gate mismatch')
    verify_anchor_reference(cfg)
    env = worker_environment()
    import numpy, sklearn
    print(json.dumps({'phase': 'b2', 'python': sys.executable, 'numpy': numpy.__version__,
                      'sklearn': sklearn.__version__,
                      'worker_python': str(Path(sys.executable).parent / 'python3'),
                      'threads': [env[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                                                  'MKL_NUM_THREADS')]}), flush=True)
    for node in cfg['nodes']:
        b1_harness_sources(node, cfg['harness_commit'])
    host_check(cfg, out)
    if Path(out).absolute().parent != Path(cfg['work_dir']).absolute():
        raise RuntimeError('STOP: preflight directory must be a direct child of work_dir')
    for key in ('models_dir', 'work_dir'):
        space_check(cfg[key])
    rows = registry['candidates'] + registry['software_anchors'] + registry.get('sensitivities', [])
    eligible = stage_a_pass_set(cfg, {s['id'] for s in rows if s.get('role') == 'candidate'}, v2=True)
    bp.check_b1_protocol(cfg, rows, eligible)  # production protocol checks (cache/template/grammar)
    matches = [s for s in rows if s['id'] == 'qwen25_coder_7b' and s.get('role') == 'anchor']
    if len(matches) != 1 or 'qwen25_coder_7b' not in eligible:
        raise RuntimeError('STOP: Stage A approved model anchor unavailable')
    runner = ExamRunner(cfg, out, b1_config_head=head)
    spec = bp.resolve_stage_a_spec(matches[0], cfg, registry, eligible)
    # Match B1's eligible model selection and its declared always-on skip (same protocol for B2).
    validated = []
    for item in rows:
        if item['id'] not in eligible or item.get('kind') in ('random_valid', 'scripted'):
            continue
        if (item.get('role') in ('candidate', 'sensitivity') and
                rule['thinking_mode']['always_on_in_b1'] == 'skip' and
                not bp.thinking_off_capable(item.get('thinking_policy'))):
            continue
        resolved = bp.resolve_stage_a_spec(item, cfg, registry, eligible)
        bp.template_repair_args(resolved)
        runner.validate_spec(resolved)
        validated.append(item['id'])
    if spec['id'] not in validated:
        raise RuntimeError('STOP: model anchor was not validated')
    print(json.dumps({'phase': 'b2', 'validated_models': validated}), flush=True)
    build = runner.validate_spec(spec)
    return cfg, spec, build


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--head', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    bp.check_inputs = b2_check_inputs      # B2 inputs/gate; every probe step below is the B1 code
    bp.run(args.head, args.out)


if __name__ == '__main__':
    main()
