"""B1-only OpenML worker bootstrap and cache failure STOP."""
import dataclasses
import os
from pathlib import Path
import runpy
import shlex
import sys
from urllib.parse import urlparse

MARKER = 'B1_OPENML_CACHE_FAILURE_STOP_20261107'
EXIT = 86
NODES = {'openml_credit_approval', 'openml_ionosphere'}


class CacheStop(BaseException):
    pass


class B1OpenMLCacheStop(SystemExit):
    pass


def _one_attempt(*args, **kwargs):
    def decorate(fn):
        def call(*a, **kw):
            try:
                return fn(*a, **kw)
            except Exception as exc:
                raise CacheStop('OpenML cache or download error') from exc
        return call
    return decorate


def install(cache_root):
    from sklearn.datasets import _openml
    _openml._retry_with_clean_cache = _one_attempt
    _openml._retry_on_network_error = _one_attempt
    open_url = _openml._open_openml_url
    def cached_only(url, data_home, *args, **kwargs):
        if data_home is None:
            raise CacheStop('OpenML cache path unavailable')
        local = Path(_openml._get_local_path(urlparse(url).path.lstrip('/'), data_home))
        if not local.is_file():
            raise CacheStop('OpenML cache file missing')
        return open_url(url, data_home, *args, **kwargs)
    _openml._open_openml_url = cached_only
    cache_root = Path(cache_root).resolve()
    def protect(original):
        def checked(path, *args, **kwargs):
            candidate = Path(os.fsdecode(path))
            if not candidate.is_absolute(): candidate = Path.cwd() / candidate
            if candidate.resolve().is_relative_to(cache_root):
                raise CacheStop('refusing deletion of B1 cache')
            return original(path, *args, **kwargs)
        return checked
    os.unlink = protect(os.unlink)
    os.remove = protect(os.remove)


class B1OpenMLWorkerMixin:
    def _run_command(self, node_spec, artifact_dir, trial_label):
        if node_spec.name not in NODES:
            return super()._run_command(node_spec, artifact_dir, trial_label)
        if node_spec.run_command != 'python3 train.py --config config.yaml':
            raise B1OpenMLCacheStop('STOP: unexpected B1 OpenML command')
        script = shlex.quote(str(Path(__file__).resolve()))
        guarded = dataclasses.replace(node_spec, run_command=f'python3 {script}')
        result = super()._run_command(guarded, artifact_dir, trial_label)
        log_path, success, failure, _, _ = result
        if not success and failure == f'exit code {EXIT}' and log_path is not None:
            if MARKER in log_path.read_text(encoding='utf-8'):
                raise B1OpenMLCacheStop('STOP: B1 OpenML cache failure; see preserved run.log')
        return result


def main():
    try:
        try:
            install(Path.cwd() / 'data_cache')
        except Exception as exc:
            raise CacheStop('OpenML guard initialization failed') from exc
        sys.argv = ['train.py', '--config', 'config.yaml']
        sys.path.insert(0, str(Path.cwd()))
        runpy.run_path('train.py', run_name='__main__')
    except CacheStop as exc:
        print(f'{MARKER}: {exc}', file=sys.stderr, flush=True)
        raise SystemExit(EXIT)


if __name__ == '__main__':
    main()
