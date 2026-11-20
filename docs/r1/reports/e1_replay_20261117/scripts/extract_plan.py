import json
import pathlib
import sys

R = pathlib.Path(sys.argv[1])
plan = json.loads((R / 'replay_plan.json').read_text())
summary = json.loads((R / 'summary.json').read_text())
mech = plan['openml_offline_mechanism']
env = plan['environment']
m = env['openml_offline_mechanism']

print('== plan top level ==')
for key in ('schema', 'label', 'tolerance', 'comparison', 'llm_requests', 'written_utc', 'harness_commit'):
    print(key, '=', plan.get(key))
print('thread_environment =', plan.get('thread_environment'))
print('cases =', len(plan['cases']))
print()

print('== mechanism declaration ==')
print('token        =', mech.get('token'))
print('row          =', mech.get('row'))
print('state        =', mech.get('state'))
print('report.identity =', json.dumps(m['identity'], sort_keys=True))
print('report.authority =', json.dumps(m['authority'], sort_keys=True))
print('report.written_utc =', m.get('written_utc'))
print('report.environments =', json.dumps(m.get('environments'), sort_keys=True))
print('network (in-plan) =', json.dumps(m['network'], sort_keys=True))
print()

print('== environment checks ==')
for key in ('host', 'wrappers', 'wrapper_target', 'interpreter', 'prefix', 'build', 'versions',
            'uv_lock_sha256', 'freeze', 'difference_from_freeze', 'newest_dist_info_mtime_utc',
            'current_package_list_sha256', 'package_list_sha256_28oct_observation', 'observation_note'):
    print(key, '=', json.dumps(env.get(key), sort_keys=True))
print('harness =', json.dumps({k: v for k, v in env['harness'].items()}, sort_keys=True))
print('resources =', json.dumps(env['resources'], sort_keys=True))
print()

print('== (i)/(ii)/(iii)/(iv) per node ==')
for node in sorted(m['nodes']):
    r = m['nodes'][node]
    print('###', node)
    print(' (i) dataset_id      =', r['dataset_id'])
    print(' (i) dataset_identity=', json.dumps(r['dataset_identity'], sort_keys=True))
    print(' (ii) fingerprint    =', json.dumps(r['loaded_data_fingerprint'], sort_keys=True))
    print(' (iii) arff          =', json.dumps(r['arff'], sort_keys=True))
    print(' (iv) cache_files    =', json.dumps(r['cache_files'], sort_keys=True))
    print(' (iv) tree_digest    =', r['cache_tree_digest'])
    print(' (iv) dotfiles       =', r['cache_dotfiles'])
print()

print('== cases.jsonl ==')
rows = [json.loads(line) for line in (R / 'cases.jsonl').read_text().splitlines() if line.strip()]
print('rows =', len(rows))
ok = True
print('| case_id | seed | metric | recorded | replayed | exact | pass | changed | cache_before_after | wall_s |')
for r in rows:
    checks = r.get('openml_offline_cache_checks') or []
    phases = ','.join(c['phase'] for c in checks)
    tree_ok = all(c.get('tree_digest') for c in checks)
    exact = r['replay_token'] == r['recorded_token']
    ok = ok and exact and r['pass'] and not r['changed_files'] and r['data_cache_unchanged']
    print('|', r['case_id'], '|', r.get('train_seed', r.get('budget_index')), '|', r.get('metric_key', '?'),
          '|', r['recorded_token'], '|', r['replay_token'], '|', exact, '|', r['pass'], '|',
          r['changed_files'], '|', phases, '|', r['wall_seconds'], '|')
print('ALL_PASS_AND_EXACT =', ok)
print('pass count =', sum(r['pass'] for r in rows))
print('success count =', sum(bool(r['success']) for r in rows))
print('changed_files non-empty =', [r['case_id'] for r in rows if r['changed_files']])
print('data_cache_unchanged false =', [r['case_id'] for r in rows if not r['data_cache_unchanged']])
print()
print('== summary ==')
print(json.dumps(summary, indent=1, sort_keys=True))
