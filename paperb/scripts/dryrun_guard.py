"""Fail-closed boundary for the desktop-only rerun-2 integration fixture."""
import os
from pathlib import Path
import platform
import subprocess
import tempfile


def validate_dryrun():
    if os.environ.get('R1_DRYRUN') != '1':
        return False
    if platform.node().split('.')[0] == 'ucrtasl':
        raise RuntimeError('STOP: DRYRUN is forbidden on Ada')
    root = Path(os.environ.get('R1_DRYRUN_ROOT', '/')).resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if root == temp or not root.is_relative_to(temp) or not (root / '.dryrun').is_file():
        raise RuntimeError('STOP: DRYRUN requires a marked temporary directory')
    for key in ('R1_BATCH_DIRECTORY', 'R1_PAPER_ROOT', 'AR_HARNESS_ROOT',
                'R1_RERUN2_BATCH_ROOT', 'R1_RERUN2_PINNED_BATCH', 'R1_RERUN2_OLLAMA_BINARY',
                'R1_RERUN2_PAPER_REMOTE', 'R1_RERUN2_HARNESS_REMOTE',
                'R1_C3_BATCH_ROOT', 'R1_C3_PAPER_REMOTE', 'R1_C3_HARNESS_REMOTE', 'R1_FAKE_OLLAMA_ROOT'):
        if key in os.environ and not Path(os.environ[key]).resolve().is_relative_to(root):
            raise RuntimeError(f'STOP: DRYRUN {key} escapes the temporary directory')
    for key in ('R1_RERUN2_PAPER_REMOTE', 'R1_RERUN2_HARNESS_REMOTE', 'R1_C3_PAPER_REMOTE', 'R1_C3_HARNESS_REMOTE'):
        if key in os.environ and not Path(os.environ[key]).is_absolute():
            raise RuntimeError('STOP: DRYRUN remotes must be absolute local paths')
    for key in ('R1_PAPER_ROOT', 'AR_HARNESS_ROOT'):
        if key not in os.environ:
            continue
        repo = Path(os.environ[key])
        remote = subprocess.check_output(['git', '-C', str(repo), 'remote', 'get-url', 'dryrun'], text=True).strip()
        push_urls = subprocess.check_output(['git', '-C', str(repo), 'remote', 'get-url', '--push', '--all', 'dryrun'], text=True).splitlines()
        if not push_urls:
            raise RuntimeError('STOP: DRYRUN remote has no push URL')
        for url in [remote, *push_urls]:
            path = Path(url).resolve()
            if not Path(url).is_absolute() or not path.is_relative_to(root):
                raise RuntimeError('STOP: DRYRUN may push only to a local temporary bare remote')
            if subprocess.check_output(['git', '-C', str(path), 'rev-parse', '--is-bare-repository'], text=True).strip() != 'true':
                raise RuntimeError('STOP: DRYRUN remote must be bare')
    return True
