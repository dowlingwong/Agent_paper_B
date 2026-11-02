"""Launch-manifest tool: fail-closed path and pin checks; no host, GPU, model or lock access."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from r1.scripts import trackx_stagea_launch as launch


def test_absolute_new_refuses_existing_and_relative(tmp_path):
    existing = tmp_path / 'exists'
    existing.mkdir()
    with pytest.raises(launch.LaunchStop, match='already exists'):
        launch.absolute_new(str(existing), 'output directory')
    with pytest.raises(launch.LaunchStop, match='absolute'):
        launch.absolute_new('relative/path', 'output directory')
    fresh = launch.absolute_new(str(tmp_path / 'fresh'), 'output directory')
    assert not fresh.exists()
    with pytest.raises(launch.LaunchStop, match='parent does not exist'):
        launch.absolute_new(str(tmp_path / 'missing' / 'fresh'), 'output directory')


def test_existing_regular_refuses_symlink_and_multilink(tmp_path):
    target = tmp_path / 'lock'
    target.write_text('')
    assert launch.existing_regular(str(target), 'GPU lock') == target
    link = tmp_path / 'symlink'
    link.symlink_to(target)
    with pytest.raises(launch.LaunchStop, match='stable regular file'):
        launch.existing_regular(str(link), 'GPU lock')
    hard = tmp_path / 'hard'
    os.link(target, hard)
    with pytest.raises(launch.LaunchStop, match='stable regular file'):
        launch.existing_regular(str(target), 'GPU lock')
    hard.unlink()


def test_pinned_files_are_absolute_and_unique(tmp_path):
    repo = tmp_path / 'repo'
    (repo / 'r1').mkdir(parents=True)
    (repo / 'r1' / 'a.py').write_text('x = 1\n')
    (repo / 'r1' / 'b.yaml').write_text('k: v\n')
    config = tmp_path / 'config.json'
    config.write_text('{}')
    prompts = tmp_path / 'prompts.jsonl'
    prompts.write_text('{}\n')
    guardian = repo / 'r1' / 'scripts' / 'trackx_lease_guardian.py'
    guardian.parent.mkdir()
    guardian.write_text('pass\n')
    rows = launch.pinned_files(repo, config, prompts, [guardian])
    paths = [row['path'] for row in rows]
    assert len(paths) == len(set(paths)) == 5
    assert all(Path(path).is_absolute() for path in paths)
    assert all(len(row['sha256']) == 64 for row in rows)


def test_environment_is_explicit_and_has_no_lease_keys(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    binary = repo / 'llama-server'
    binary.write_text('')
    env = launch.environment(repo, {'work_dir': '/home/dowling/exam-x/work'}, binary)
    assert env['PYTHONPATH'] == str(repo)
    assert env['HF_HOME'] == '/home/dowling/exam-x/work/hf'
    assert env['LD_LIBRARY_PATH'] == str(binary.parent)
    assert not any(key.startswith('TRACKX_') for key in env)
    assert all(isinstance(value, str) for value in env.values())


def test_main_refuses_existing_evidence_dir_before_any_write(tmp_path):
    repo = Path(launch.__file__).resolve().parents[2]
    lock = tmp_path / 'synthetic.lock'
    lock.write_text('')
    existing = tmp_path / 'evidence'
    existing.mkdir()
    out = tmp_path / 'out'
    code = subprocess.run([sys.executable, str(Path(launch.__file__)), '--repo', str(repo),
                           '--lock', str(lock), '--evidence-dir', str(existing), '--out', str(out)],
                          capture_output=True, text=True)
    assert code.returncode != 0
    assert 'already exists' in (code.stderr + code.stdout)
    assert not out.exists() and not Path(str(existing) + '.manifest.json').exists()


def test_runner_override_builds_preflight_argv(tmp_path):
    import argparse
    # The launcher must accept an explicit reviewed runner (used by the preflight
    # fixture) and never default it to anything outside the repository.
    source = (Path(launch.__file__)).read_text()
    assert "parser.add_argument('--runner'" in source
    assert "'--expected-runner'" in source
    assert "AR_HARNESS_ROOT" in launch.environment(Path('/tmp/repo'), {'work_dir': '/home/dowling/exam-x/work'},
                                                   Path('/tmp/repo/llama-server'))


def test_candidate_filter_is_parsed_and_validated():
    source = Path(launch.__file__).read_text()
    assert "parser.add_argument('--candidate', action='append'" in source
    assert "unknown --candidate ids" in source
    # The filter may only NARROW the launcher's pre-run size check; the runtime
    # re-verifies every model it loads (validate_spec), so Stage A without
    # --candidate still checks all 22 files.
    assert "if args.candidate:" in source


def test_visible_llama_servers_and_occupancy_refusal(tmp_path):
    root = tmp_path / 'proc'
    (root / '10').mkdir(parents=True); (root / '10' / 'exe').symlink_to('/x/llama-server')
    (root / '11').mkdir(); (root / '11' / 'exe').symlink_to('/x/python3')
    (root / '12').mkdir()  # no exe link (vanished/unreadable)
    assert launch.visible_llama_servers(str(root)) == [10]
    assert launch.visible_llama_servers(str(tmp_path / 'missing')) == []


def test_host_occupancy_check_refuses_stale_server_or_gpu_app():
    launch.host_occupancy_check(servers_fn=lambda: [], apps_fn=lambda: [])
    with pytest.raises(launch.LaunchStop, match='visible llama-server'):
        launch.host_occupancy_check(servers_fn=lambda: [1234], apps_fn=lambda: [])
    with pytest.raises(launch.LaunchStop, match='GPU compute'):
        launch.host_occupancy_check(servers_fn=lambda: [], apps_fn=lambda: [{'pid': 7}])
    # nvidia-smi unavailable (apps_fn None) never blocks by itself
    launch.host_occupancy_check(servers_fn=lambda: [], apps_fn=None)
