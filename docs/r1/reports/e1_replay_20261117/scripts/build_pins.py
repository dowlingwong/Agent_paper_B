"""Build pins.json for the e1 amended replay ops report (read-only inputs)."""
import hashlib
import json
import pathlib
import subprocess
import sys

PAPER = pathlib.Path(sys.argv[1])            # deployment checkout (reviewed tip)
OPS = pathlib.Path(sys.argv[2])              # ops report clone (branch)
RD = OPS / 'docs/r1/reports/e1_replay_20261117'
B = pathlib.Path('/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw')
H = B / 'autoresearch_harness'
REAL = pathlib.Path(sys.argv[3])
DRY = pathlib.Path(sys.argv[4])


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def git(cwd, *args):
    return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()


plan = json.loads((REAL / 'replay_plan.json').read_text())
summary = json.loads((REAL / 'summary.json').read_text())
dry = json.loads((DRY / 'replay_plan.json').read_text())
env = plan['environment']

pins = {
    'label': 'ENGINEERING_ONLY',
    'what': 'C3 B.1 e1 environment replay (16 predeclared cases) under R1-E1-OPENML-AMEND',
    'operator_session': {
        'date_utc': '2026-11-17',
        'host': 'deepthought.etp.kit.edu',
        'deployment_root': '/ceph/dwong/r1_e1_20261117',
        'one_operator': True,
        'other_deepthought_work': 'pre-existing same-user and other-user jobs were running '
                                  '(jepa_noise r2 diagnostics, paperc headroom audit); they are not '
                                  'part of this work; co-tenancy floor was met at both checks '
                                  '(see co_tenancy). No e1 job other than this one was started.',
    },
    'authority': {
        'row': 'R1-E1-OPENML-AMEND',
        'amends_row': 'R1-E1-OPENML',
        'under_row': 'R1-E1-AUTH',
        'authorization': {'file': 'docs/r1/authorizations/c3_env_replay_20261116.md',
                          'sha256': sha(OPS / 'docs/r1/authorizations/c3_env_replay_20261116.md')},
        'protocol': {'file': 'docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md',
                     'sha256': sha(OPS / 'docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md')},
        'origin_main_base_of_amend_branch': git(PAPER, 'rev-parse', '16185b0b'),
        'origin_main_at_report': git(OPS, 'rev-parse', 'origin/main'),
        'amend_review': {'file': 'docs/r1/reviews/E1_AMEND_REVIEW_20261117.md',
                         'commit': 'bbcfc4a9d337717c6f03ca6e8929fbbbb929cf3d',
                         'verdict': 'ACCEPTED (round 2, at reviewed code commit 5bddab73)'},
        'basis_audit': {'branch': 'e1-openml-20261116', 'commit': '5d73550a',
                        'audit_sha256': '9f14c879973ff4080655a2e108e6e7a1aad2b031d96d4f96e914921ddaa190b7'},
        'basis_stop': {'branch': 'ops-e1-replay-20261116', 'commit': 'fc7d8e4e'},
    },
    'paper_code': {
        'deployed_branch': 'r1-e1-openml-amend-20261117',
        'remote_branch_tip': git(PAPER, 'rev-parse', 'origin/r1-e1-openml-amend-20261117'),
        'checked_out_head': git(PAPER, 'rev-parse', 'HEAD'),
        'reviewed_code_commit': '5bddab731f6b4fa226e37dd8dc6d7e6f202232e1',
        'code_delta_reviewed_vs_deployed': 'git diff 5bddab73 bbcfc4a9 = '
                                           'docs/r1/reviews/E1_AMEND_REVIEW_20261117.md only (+133 lines)',
        'ancestry_verified': bool(subprocess.run(['git', '-C', str(PAPER), 'merge-base', '--is-ancestor',
                                                   '16185b0b', 'HEAD']).returncode == 0),
        'worktree_clean_at_deployment': True,
        'deployment_path': str(PAPER),
        'driver': {
            'path': 'r1/scripts/c3_env_replay.py',
            'sha256': sha(PAPER / 'r1/scripts/c3_env_replay.py'),
            'git_blob': git(PAPER, 'rev-parse', 'HEAD:r1/scripts/c3_env_replay.py'),
            'note': 'AMENDED pin, cited under row R1-E1-OPENML-AMEND. The e1 authorization\'s '
                    '5ef9db16 / a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8 '
                    'predates the amendment and is NOT the driver that ran.',
        },
        'mechanism_module': {'path': 'r1/c3/e1_openml_offline.py',
                             'sha256': sha(PAPER / 'r1/c3/e1_openml_offline.py')},
        'network_module': {'path': 'r1/c3/e1_offline_network.py',
                           'sha256': sha(PAPER / 'r1/c3/e1_offline_network.py')},
        'test_modules': {
            f: sha(PAPER / f) for f in
            ('r1/tests/test_e1_openml_offline_mechanism.py', 'r1/tests/test_e1_offline_network.py',
             'r1/tests/test_e1_openml_offline_wiring.py')},
        'committed_audit': {'path': 'docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_AUDIT.json',
                            'sha256': sha(PAPER / 'docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_AUDIT.json')},
    },
    'harness': {
        'path': str(H),
        'commit': git(H, 'rev-parse', 'HEAD'),
        'tracked_clean': (git(H, 'status', '--porcelain', '--untracked-files=no') == ''),
        'uv_lock_sha256': sha(H / 'uv.lock'),
        'ls_files_sha256': subprocess.check_output(
            ['bash', '-c', f'git -C {H} ls-files -s | sha256sum'], text=True).split()[0],
        'pre_existing_untracked_caches': True,
        'pre_existing_untracked_note': 'the six nodes/*/data_cache directories and '
                                       'paper/tables/artifact_completeness_report.txt were already '
                                       'untracked before this run; the driver\'s tracked-clean test '
                                       'ignores untracked files',
    },
    'interpreter': {
        'batch_wrappers': env['wrappers'],
        'wrapper_target': env['wrapper_target'],
        'interpreter': env['interpreter'],
        'prefix': env['prefix'],
        'build': env['build'],
        'python_version': env['versions']['python'] if 'python' in env['versions'] else '3.13.15',
        'library_versions': env['versions'],
        'package_list_sha256': env['current_package_list_sha256'],
        'package_list_sha256_28oct_observation': env['package_list_sha256_28oct_observation'],
        'newest_dist_info_mtime_utc': env['newest_dist_info_mtime_utc'],
        'driver_prefix_matched_batch_venv': env['prefix'] == '/ceph/dwong/r1_prepare_20261025/venv',
        'difference_from_25oct_freeze': env['difference_from_freeze'],
    },
    'package_baseline': {'freeze': env['freeze'], 'allowed_addition': 'narwhals==2.27.1'},
    'preserved_batch': {
        'path': str(B),
        'cache_check_json': {'sha256': sha(B / 'cache_check.json'),
                             'mtime_utc': '2026-10-27T15:22:39Z',
                             'launch_utc': '2026-10-27T15:48:34Z',
                             'before_launch': True},
        'files_sha256': {name: sha(B / name) for name in
                         ('env.sh', 'c3_config.json', 'c3_sweep_summary.json', 'batch_state.json',
                          'uv_sync.log', 'prepare.json') if (B / name).exists()},
        'read_only': 'the run only read the batch; the driver\'s own git read commands may refresh '
                     'transient .git metadata, no tracked or cache content changed (see REPORT.md).',
    },
    'sources': {k: v for k, v in plan['corpus'].items() if k != 'index_doc'},
    'host': {
        'node': env['host'],
        'kernel': subprocess.check_output(['uname', '-r'], text=True).strip(),
        'machine': subprocess.check_output(['uname', '-m'], text=True).strip(),
        'cpus': int(subprocess.check_output(['nproc', '--all'], text=True).strip()),
        'workers': 1,
        'cuda_visible_devices': '',
        'thread_environment': plan['thread_environment'],
        'llm_requests': plan['llm_requests'],
    },
    'co_tenancy': {
        'policy': 'authorization / operator runbook O4: leave at least 10 of 40 cores free',
        'checks': [
            {'when_utc': '2026-11-17T00:47:18Z', 'when': 'immediately before dry run',
             'load_1min': 15.79, 'cpus': 40, 'approx_free_cores': 24.21, 'result': 'PASS'},
            {'when_utc': '2026-11-17T00:48:07Z', 'when': 'immediately before real run',
             'load_1min': 16.63, 'cpus': 40, 'approx_free_cores': 23.37, 'result': 'PASS'},
        ],
        'result': 'PASS at both checks (>= 10 free); observed pre-existing jobs listed in '
                  'logs/cotenancy.log',
    },
    'seccomp': {
        'linux_only_test': 'r1/tests/test_e1_offline_network.py::test_linux_install_denies_sockets',
        'linux_only_test_result': 'PASSED (deepthought, Linux x86_64, kernel '
                                  '4.18.0-553.156.1.el8_10.x86_64, pytest 9.0.3, batch venv Python 3.13.15)',
        'first_invocation_note': 'the first invocation of the module failed only because the batch '
                                 'env.sh exports PYTHONPATH=<batch>/agent_paper_B (the stale sweep '
                                 'paper checkout, 22cc8936) which shadows the deployed reviewed checkout '
                                 'for the test\'s disposable child script; it is an ImportError before '
                                 'any seccomp install. With the reviewed checkout prepended to '
                                 'PYTHONPATH for that child, 15 passed / 1 Linux-skip and the specific '
                                 'test PASSED. Both logs are retained (logs/seccomp_attempt1.log, '
                                 'logs/seccomp_attempt2.log, logs/seccomp_specific_test.log).',
        'kernel_actions_available': 'kill_process kill_thread trap errno trace log allow',
        'in_run_in_process': json.loads((REAL / 'summary.json').read_text())['openml_offline_mechanism']['post_run']['network'],
        'in_run_worker_subprocess': env['openml_offline_mechanism']['network']['worker_subprocess'],
        'post_run_reverify': json.loads((REAL / 'summary.json').read_text())['openml_offline_mechanism']['post_run']['network'],
        'blocked_syscalls': env['openml_offline_mechanism']['network']['blocked_syscalls'],
        'denied_errno': 101,
        'denied_errname': 'ENETUNREACH',
        'seccomp_mode_in_run': 2,
    },
    'run': {
        'dry_run': {
            'out': str(DRY),
            'replay_plan_sha256': sha(DRY / 'replay_plan.json'),
            'label': dry['label'],
            'cases': len(dry['cases']),
            'mechanism_state': dry['openml_offline_mechanism']['state'],
            'environment': dry['environment'],
            'exit_code': 0,
            'started_utc': '2026-11-17T00:47:18Z',
            'ended_utc': '2026-11-17T00:47:39Z',
        },
        'real_run': {
            'out': str(REAL),
            'replay_plan_sha256': sha(REAL / 'replay_plan.json'),
            'cases_sha256': sha(REAL / 'cases.jsonl'),
            'summary_sha256': sha(REAL / 'summary.json'),
            'verdict': summary['verdict'],
            'cases_planned': summary['cases_planned'],
            'cases_run': summary['cases_run'],
            'cases_passed': summary['cases_passed'],
            'stop': summary['stop'],
            'mechanism_state': plan['openml_offline_mechanism']['state'],
            'mechanism_report_sha256': summary['openml_offline_mechanism']['report_sha256'],
            'exit_code': 0,
            'plan_written_utc': plan['written_utc'],
            'mechanism_report_written_utc': env['openml_offline_mechanism']['written_utc'],
            'out_dir_birth_utc': '2026-11-17T00:48:32.946924436Z',
            'plan_file_birth_utc': '2026-11-17T00:48:32.949924447Z',
            'first_case_log_mtime_utc': '2026-11-17T00:48:36.101936Z',
            'last_case_log_mtime_utc': '2026-11-17T00:49:10.912066Z',
            'summary_mtime_utc': '2026-11-17T00:49:11.103Z',
            'scratch': '/tmp/r1_c3_env_replay_20261117T004807Z_amend_real (retained)',
            'min_free_bytes': 2147483648,
        },
    },
    'report_branch': {
        'name': 'ops-e1-replay-amend-20261117',
        'base': 'origin/main @ ' + git(OPS, 'rev-parse', 'origin/main'),
        'files': 'docs/r1/reports/e1_replay_20261117/',
    },
    'no_side_effects': {
        'b2_started': False, 'audit_performed': False, 'labels': False,
        'deletions': False, 'main_modified': False, 'batch_or_cache_written': False,
    },
}

(RD / 'pins.json').write_text(json.dumps(pins, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: pins[k] for k in ('paper_code', 'run')}, indent=1)[:2000])
print('wrote', RD / 'pins.json')
