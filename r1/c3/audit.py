"""Fresh-seed audits of proposals on CPU (C3_DESIGN §4). ENGINEERING_ONLY; AI-assisted (Claude).

A proposal is audited by running its candidate and its incumbent configuration
on K common fresh *joint* seeds (train seed = split seed = s, as E1's ``joint``
condition and the E1b leaf audits do), giving per-seed paired differences,
Delta_audit = mean and se = sd / sqrt(K). Default seeds 7001..7010 (K = 10,
C3_DESIGN §4) are disjoint from campaign seeds (100..280), E1 seeds (1001+,
2001+, 3001+) and the E1b leaf audit seeds (5001..5006).

Label / evaluation seed split (C3_DESIGN §4; ``split_seeds``): the first half
of an audit's seeds (in the recorded order) gives the training soft label, the
second half the evaluation value Delta_true. K = 10 gives 5 + 5. The 19 Oct
pilot audits were run with K = 6 (7001..7006, ``PILOT_SEEDS``) and split 3 + 3;
they stay readable because every audit row records its own ``seeds`` and the
split is taken from that list, never from the default. ``run`` records the
seeds it used in ``DIR/audit_seeds.json``; ``collect`` without ``--seeds``
reads that file, or, for directories written before it existed, uses the seeds
present in the run cache (the pilot: 7001..7006).

Each configuration is run through the harness ``LocalWorker.run_trial_at_seed``
with a no-edit proposal on an isolated copy of the node whose editable files are
overwritten with the configuration's texts: the mechanism of
``r1.headroom.e1b_collect._audit`` / ``r1.noise.e1_noise_floor.run_one``.

Cache: ``runs.jsonl`` rows keyed by (node, config hash, seed); every run is
written as soon as it finishes, so an interrupted call resumes where it stopped.
For EVIDENCE, raw runs remain in the dedicated audit directory and the completed
audit writes separate label/evaluation blocks, each bound by a SHA256 manifest;
it does not write the legacy mixed ``audits.jsonl``. An EVIDENCE STOP is not
automatically resumed.

e2 (R1-B2-GO, 17 Nov 2026) for the sweep-1 B.2 EVIDENCE audit:
- B6 (a): the environment basis is the published, independently reviewed e1 replay report
  (docs/r1/reports/e1_replay_20261117, ops-e1-replay-amend-20261117 @ 52992b22; pinned bytes) plus a
  re-run, at audit start, of that replay's current-environment checks (c3_env_replay.check_environment),
  whose results must equal the replay's record. It replaces prepare.json:sweep_environment_sha256 and the
  launch-bound freeze, which do not exist; every record carries the disclosure.
- B4 (a): the per-run worker_runtime probe record is accepted; its limitation (it does not attest the task
  process itself) is written into environment.json and evidence_completion.json (schema /3).
- B1 (a): unchanged: authority files must be byte-identical on the published origin/main; the replay
  report, its review, the R1-B2-GO PLAN row and the B.2 addendum are read from origin/main itself.
- The run also requires the author's published B.2 addendum (docs/r1/authorizations/c3_b2_addendum_*.md)
  naming R1-B2-GO, the reviewed code commit, harness 6adf385 and K = 10. Harness, seeds, population and
  every other STOP are unchanged.

Audit working directories remain at their original unique paths on success or
failure to preserve the scene. Node copies, cached datasets, and worker artifacts
accumulate; operators must provision and monitor storage before running.

CLI (time-boxed, resumable):
  python -m r1.c3.audit run --plan DIR/plan.jsonl --configs DIR/configs.json --out DIR \
      --workers 4 --deadline 150
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import stat
import tempfile
import time
import tomllib
from importlib import metadata as import_metadata
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import numpy as np

DEFAULT_SEEDS = tuple(range(7001, 7011))  # K = 10: 5 label + 5 evaluation seeds (C3_DESIGN §4)
PILOT_SEEDS = tuple(range(7001, 7007))  # K = 6 of the 19 Oct pilot audits (3 + 3)
SEEDS_FILE = "audit_seeds.json"
PILOT_DATA_CACHE = "experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache"

# e2 (R1-B2-GO, 17 Nov 2026): the environment basis of the B.2 EVIDENCE audit (B6 (a)). The published,
# independently reviewed e1 environment replay report and its current-environment checks replace the
# launch-bound environment record (prepare.json:sweep_environment_sha256) that does not exist. The report
# files are pinned by the sha256 of their bytes on ops-e1-replay-amend-20261117 @ 52992b22; B1 (a): they,
# the review, the PLAN row and the B.2 addendum must be byte-identical on origin/main.
E1_REPLAY_REPORT_DIR = 'docs/r1/reports/e1_replay_20261117'
E1_REPLAY_REVIEW = 'docs/r1/reviews/E1_AMEND_RUN_REVIEW_20261117.md'
E1_REPLAY_PINNED = {
    'docs/r1/reports/e1_replay_20261117/summary.json': 'ff7fe3c3f7b1d6e37c874dbbd906b3ed3b8890cf114bec6266bc2d89f278a27b',
    'docs/r1/reports/e1_replay_20261117/pins.json': '72aff78d92eed58af0e3563e2207cf1ea1981bcd07f99fd4eb1d6b4350fb78f7',
    'docs/r1/reports/e1_replay_20261117/REPORT.md': '5892913533416e5e8c66ae913a46528a29be69e483eaecd2ca04929b5dad0048',
    'docs/r1/reports/e1_replay_20261117/cases.jsonl': 'ce6ed7b38b987d5bb6ed89472ce295ef76223e90935eb758d8d3c168531d6aba',
    'docs/r1/reports/e1_replay_20261117/SHA256SUMS.txt': '2a46aa714a6a843cce0a487364a871f0667224247f87d82ec37b160d7fb06495',
    'docs/r1/reviews/E1_AMEND_RUN_REVIEW_20261117.md': 'ffaf34aec0ed658441af30c9803b7f4c6b56ded88b4d2efbb8ad0194df6a1cdd',
}
E1_REPLAY_COMMIT = '52992b22b50e496935136b50c5b31a79a17d7f20'   # ops-e1-replay-amend-20261117 (R1-B2-GO)
E1_REPLAY_BATCH = '/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw'
E1_HOST = 'deepthought'
# Untracked paths the e1 record found in the batch harness before its run (pins.json harness.pre_existing_untracked_note):
# the six OpenML data caches and one report file. Accepted only with the caches' tree digests equal to the e1
# post-run record (summary.json openml_offline_mechanism.post_run.source_caches).
E1_OPENML_CACHE_NODES = ('openml_breast_w', 'openml_climate', 'openml_credit_approval', 'openml_ionosphere',
                         'openml_sonar', 'openml_wdbc')
E1_UNTRACKED_FILES = ('paper/tables/artifact_completeness_report.txt',)
ENVIRONMENT_BASIS_DISCLOSURE = (
    'R1-B2-GO B6 (a): no environment freeze bound to the sweep-1 launch exists. The B.2 audit environment is '
    'established by the published, independently reviewed e1 environment replay (docs/r1/reports/e1_replay_20261117/'
    'REPORT.md, sha256 5892913533416e5e8c66ae913a46528a29be69e483eaecd2ca04929b5dad0048, at 52992b22; review '
    'E1_AMEND_RUN_REVIEW_20261117.md ACCEPTED; 16/16 cases at tolerance 0) and by re-running that replay\'s '
    'current-environment checks (r1/scripts/c3_env_replay.py check_environment: wrapper target, Python and library '
    'versions, uv.lock, the 25 Oct freeze plus narwhals, dist-info mtimes) at audit start; the current package list, '
    'interpreter build, prefix, wrapper target and newest dist-info mtime must equal the replay\'s recorded values. '
    'This is a current-state observation, not a launch-bound snapshot. Carried from the replay report (section 9): '
    '(1) dataset identity for the six OpenML nodes rests on the amended evidence of R1-E1-OPENML-AMEND (sweep-1 '
    'data id, sweep-1 loaded-data fingerprint recomputed equal, OpenML md5 self-consistency, and audited cache bytes '
    'unchanged since the 16 Nov audit), not on a file hash recorded by sweep 1; the surviving cache bytes are not '
    'anchored by a hash the sweep-1 launch wrote; (2) the batch .venv executables are wrappers to the shared venv '
    '/ceph/dwong/r1_prepare_20261025/venv, not a separately built venv; (3) the replay is a bounded reproducibility '
    'check of 16 worker evaluations, reconstructed from uv.lock and the batch venv; it is not proof that every '
    'original dependency or all 288 roots were identical, and it says nothing about LLM seed replay. The batch '
    'harness is tracked-clean; its only untracked files are the six OpenML data caches (tree digests required equal '
    'to the e1 post-run record) and paper/tables/artifact_completeness_report.txt, as the e1 record states.')
WORKER_RUNTIME_BASIS = {
    'ruling': 'R1-B2-GO B4 (a)',
    'record': 'runs.jsonl:worker_runtime',
    'what': 'per seed run, a separate probe process started with the worker\'s PATH and command interpreter '
            'records the interpreter, prefix, library versions and package-list hash; every record must equal '
            'the approved venv (validate_worker_records)',
    'limitation': 'the probe does not attest the task process itself ([AS]: NOT CHECKABLE); accepted and '
                  'disclosed under R1-B2-GO B4 (a)',
}
COMPLETION_SCHEMA = 'r1.c3_audit_completion/3'


def _package_list_hash(packages: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(packages, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def worker_runtime(expected: dict, run_command: str, env: dict) -> dict:
    """Probe the same PATH and command interpreter the pinned worker will execute."""
    try:
        tokens = shlex.split(run_command)
    except ValueError as exc:
        raise ValueError('STOP: unsupported worker command') from exc
    if not tokens or tokens[0] != 'python3' or any(c in run_command for c in ';|&<>`\n$'):
        raise ValueError('STOP: worker command is not a direct python3 invocation')
    command = shutil.which(tokens[0], path=env.get('PATH'))
    if not command:
        raise ValueError('STOP: worker python3 is unavailable')
    code = """import hashlib, importlib.metadata as m, json, os, sys
p={}
for d in m.distributions():
 n=(d.metadata.get('Name') or '').lower().replace('_','-')
 if not n or n in p: raise ValueError('duplicate or missing package name')
 p[n]=d.version
v={n:m.version(n) for n in ('scikit-learn','numpy','scipy','pandas')}
print(json.dumps({'worker_python':sys.executable,'worker_python_realpath':os.path.realpath(sys.executable),
 'prefix':sys.prefix,'base_prefix':sys.base_prefix,
 'versions':v,'package_list_sha256':hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()}))
"""
    try:
        observed = json.loads(subprocess.check_output([command, '-B', '-c', code], env=env, text=True, timeout=30))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ValueError('STOP: worker python probe failed') from exc
    observed['worker_command_python'] = command
    if not observed.get('worker_python_realpath') or observed.get('prefix') == observed.get('base_prefix') or \
            observed.get('worker_python') != expected.get('worker_python') or \
            observed.get('prefix') != expected.get('worker_prefix') or \
            observed.get('versions') != expected.get('worker_versions') or \
            observed.get('package_list_sha256') != expected.get('package_list_sha256'):
        raise ValueError('STOP: worker interpreter, versions, or package list mismatch')
    return observed


def _copy_audit_node(source: Path, destination: Path, files: dict[str, str], editable_paths) -> None:
    """Copy unedited files, then exclusively create the selected configuration.

    This prevents replacing a freshly copied editable file. It assumes a
    cooperative, unchanged source and destination tree during the copy.
    """
    source, destination = Path(source), Path(destination)
    selected = {}
    for rel, text in files.items():
        if rel not in editable_paths:
            raise ValueError(f"{rel} is not editable")
        p = PurePosixPath(rel)
        if p.is_absolute() or p.as_posix() != rel or any(part in ('', '.', '..') for part in p.parts):
            raise ValueError(f"unsafe editable path: {rel}")
        if not isinstance(text, str):
            raise ValueError(f"editable content is not text: {rel}")
        current = source
        for part in p.parts[:-1]:
            current = current / part
            if current.is_symlink() or not current.is_dir():
                raise ValueError(f"unsafe editable parent: {rel}")
        original = source.joinpath(*p.parts)
        if original.is_symlink():
            raise ValueError(f"symlink editable file: {rel}")
        try:
            mode = stat.S_IMODE(original.stat().st_mode)
            if not original.is_file():
                raise ValueError(f"non-regular editable file: {rel}")
        except FileNotFoundError:
            mode = None
        selected[rel] = (p, text, mode)

    default_ignore = shutil.ignore_patterns('__pycache__', '.autoresearch_artifacts')
    def ignore(directory, names):
        ignored = set(default_ignore(directory, names))
        parent = Path(directory).relative_to(source)
        for name in names:
            if (parent / name).as_posix() in selected:
                ignored.add(name)
        return ignored

    shutil.copytree(source, destination, ignore=ignore)
    for p, text, mode in selected.values():
        target = destination.joinpath(*p.parts)
        # Exclusive creation leaves a partial file intact on error and refuses
        # an existing entry, including a symlink. No failure cleanup is done.
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            if mode is not None:
                os.fchmod(handle.fileno(), mode)
            handle.write(text)


def run_config(node: str, files: dict[str, str], seeds: list[int], tmp: str, stop_on_failure: bool = False,
               journal: str | None = None, journal_identity: dict | None = None, *,
               preserve_node_outputs: bool = False, stop_on_invalid: bool = False) -> list[dict]:
    """Run one configuration at the given joint seeds (subprocess-safe)."""
    from r1.harness import import_harness
    harness = import_harness()
    from autoresearch.manager.base import ManagerProposal
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import LocalWorker

    spec = load_registered_node(node, repo_root=harness)
    work = Path(tempfile.mkdtemp(prefix=f"c3a_{node}_", dir=tmp))
    # Preserve the entire scene in place, including after asynchronous STOP.
    # Unique work directories and copied artifacts consume increasing storage.
    out = []
    node_dir = work / node
    _copy_audit_node(harness / "nodes" / node, node_dir, files, spec.editable_paths)
    if node.startswith("openml_") and not (node_dir / "data_cache").exists():
        cache = harness / PILOT_DATA_CACHE.format(node=node)
        if cache.exists():
            shutil.copytree(cache, node_dir / "data_cache")
    worker_type = LocalWorker
    if preserve_node_outputs:
        from r1.exam.b1_worker_artifact_guard import GuardedTrialPath

        from r1.exam.b1_openml_cache_guard import B1OpenMLWorkerMixin

        class B1AuditWorker(B1OpenMLWorkerMixin, LocalWorker):
            def _resolve_artifact_dir(self, trial_label):
                return GuardedTrialPath(super()._resolve_artifact_dir(trial_label))

        worker_type = B1AuditWorker
    worker = worker_type(node_root=node_dir, artifact_dir=work / "art", timeout_seconds=600)
    noedit = ManagerProposal(manager_mode="c3_audit", proposal_summary="audit", proposal_rationale="",
                             target_files=spec.editable_paths, objective="Audit run; no change.")
    for i, s in enumerate(seeds):
        runtime = None
        if stop_on_failure:
            from autoresearch.worker.seeds import seed_environment
            runtime = worker_runtime((journal_identity or {}).get('expected_worker', {}),
                                     spec.run_command, seed_environment(s, s))
        t0 = time.perf_counter()
        if preserve_node_outputs:
            from r1.exam.b1_node_artifacts import preserve_node_artifacts
            preserve_node_artifacts(node_dir)
        res = worker.run_trial_at_seed(noedit, spec, i + 1, train_seed=s, split_seed=s)
        out.append({"seed": s, "success": bool(res.success), "failure": res.failure_message,
                    "metric": res.parsed_metrics.get(spec.metric_name) if res.success else None,
                    "changed_files": bool(res.changed_files),
                    "wall_seconds": round(time.perf_counter() - t0, 4),
                    **({'worker_runtime': runtime} if runtime is not None else {})})
        if journal:
            with open(journal, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps({**(journal_identity or {}), **out[-1]}) + '\n')
                fh.flush()
                os.fsync(fh.fileno())
        if stop_on_failure:
            value = out[-1]['metric']
            if not out[-1]['success'] or out[-1]['changed_files'] or value is None or not math.isfinite(float(value)):
                break
        if stop_on_invalid:
            metric = out[-1]['metric']
            if not out[-1]['success'] or isinstance(metric, bool) or not isinstance(metric, (int, float)) or not math.isfinite(metric):
                raise RuntimeError(f'STOP: invalid B1 audit result at seed {s}')
    return out


class RunCache:
    def __init__(self, path: Path):
        self.path = Path(path)
        from r1.c3.analysis_guard import refuse_sealed
        refuse_sealed(self.path)
        self.rows: dict[tuple, dict] = {}
        if self.path.exists() and self.path.stat().st_size > 0:
            from r1.c3.release import guard_raw_label_path, is_evidence_dir
            if is_evidence_dir(self.path.resolve().parent) or is_evidence_dir(self.path.parent):
                guard_raw_label_path(self.path, "T0")   # PRE-STAGE A: a B.2 run log holds both seed blocks
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.rows[(r["node"], r["config_hash"], int(r["seed"]))] = r

    def get(self, node, h, seed):
        return self.rows.get((node, h, int(seed)))

    def add(self, rows: list[dict]):
        with open(self.path, "a", encoding="utf-8") as fh:
            for r in rows:
                self.rows[(r["node"], r["config_hash"], int(r["seed"]))] = r
                fh.write(json.dumps(r) + "\n")


def paired(cand: list[float | None], inc: list[float | None]) -> dict:
    """Delta_audit and se from per-seed metrics (failed seeds dropped pairwise)."""
    d = [c - i for c, i in zip(cand, inc) if c is not None and i is not None]
    if not d:
        return {"delta_audit": None, "se": None, "k": 0}
    d = np.asarray(d, float)
    se = float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None
    return {"delta_audit": float(d.mean()), "se": se, "k": int(len(d)), "sd": float(d.std(ddof=1)) if len(d) > 1 else None}


def split_seeds(seeds) -> tuple[tuple, tuple]:
    """(label seeds, evaluation seeds): first half for labels, second half for evaluation.

    K must be even and >= 2, so that both roles get the same number of seeds.
    """
    seeds = tuple(seeds)
    if len(seeds) < 2 or len(seeds) % 2:
        raise ValueError(f"label/evaluation split needs an even K >= 2, got K = {len(seeds)}")
    h = len(seeds) // 2
    return seeds[:h], seeds[h:]


def split_audit(a: dict) -> tuple[dict, dict]:
    """Paired results (label part, evaluation part) of one audit row, split by its recorded seeds."""
    lab, ev = split_seeds(a["seeds"])
    h = len(lab)
    return (paired(a["candidate_metrics"][:h], a["incumbent_metrics"][:h]),
            paired(a["candidate_metrics"][h:], a["incumbent_metrics"][h:]))


def resolve_seeds(out: Path, seeds=None) -> tuple:
    """Seeds for ``collect``: explicit, else DIR/audit_seeds.json, else the seeds present in the cache."""
    from r1.c3.analysis_guard import refuse_sealed
    f = Path(out) / SEEDS_FILE
    refuse_sealed(out, f)
    if seeds:
        return tuple(seeds)
    if f.exists():
        return tuple(json.loads(f.read_text())["seeds"])
    cache = RunCache(Path(out) / "runs.jsonl")
    present = tuple(sorted({k[2] for k in cache.rows}))
    if not present:
        raise ValueError(f"no seeds recorded and no cached runs in {out}")
    return present


def audit_results(plan: list[dict], cache: RunCache, seeds=DEFAULT_SEEDS) -> list[dict]:
    """Assemble per-proposal audit results for plan rows whose runs are all cached."""
    out = []
    for p in plan:
        rc = [cache.get(p["node"], p["candidate_hash"], s) for s in seeds]
        ri = [cache.get(p["node"], p["incumbent_hash"], s) for s in seeds]
        if any(r is None for r in rc + ri):
            continue
        cm, im = [r["metric"] for r in rc], [r["metric"] for r in ri]
        out.append({"proposal_id": p["proposal_id"], "node": p["node"], "reason": p.get("reason"),
                    "candidate_hash": p["candidate_hash"], "incumbent_hash": p["incumbent_hash"],
                    "seeds": list(seeds), "candidate_metrics": cm, "incumbent_metrics": im,
                    "wall_seconds": sum(r["wall_seconds"] for r in rc + ri), **paired(cm, im)})
    return out


def run_plan(plan: list[dict], configs: dict, out: Path, seeds=DEFAULT_SEEDS, workers: int = 4,
             deadline: float = 150.0, tmp: str | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    # The seeds of the latest ``run`` call (what ``collect`` assembles by default).
    # Extending an older directory (e.g. the K = 6 pilot) to more seeds is allowed:
    # cached runs are reused and only the missing seeds run.
    (out / SEEDS_FILE).write_text(json.dumps({"seeds": list(seeds), "k": len(seeds),
                                              "label_seeds": list(seeds[:len(seeds) // 2]),
                                              "evaluation_seeds": list(seeds[len(seeds) // 2:])}) + "\n")
    cache = RunCache(out / "runs.jsonl")
    tmp = tmp or tempfile.mkdtemp(prefix="c3_audit_tmp_")
    Path(tmp).mkdir(parents=True, exist_ok=True)
    jobs, queued = [], set()
    for p in plan:
        for h in (p["candidate_hash"], p["incumbent_hash"]):
            missing = [s for s in seeds if cache.get(p["node"], h, s) is None]
            if missing and (p["node"], h) not in queued:
                queued.add((p["node"], h))
                jobs.append((p["node"], h, missing))
    t0, done = time.time(), 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        while (jobs or pending):
            while jobs and len(pending) < workers and time.time() - t0 < deadline:
                node, h, missing = jobs.pop(0)
                fut = pool.submit(run_config, node, configs[h]["files"], missing, tmp)
                pending[fut] = (node, h)
            if not pending:
                break
            finished, _ = wait(list(pending), return_when=FIRST_COMPLETED, timeout=5)
            for fut in finished:
                node, h = pending.pop(fut)
                rows = [{"node": node, "config_hash": h, **r} for r in fut.result()]
                cache.add(rows)
                done += 1
    results = audit_results(plan, cache, seeds)
    return {"configs_run_this_call": done, "configs_remaining": len(jobs),
            "proposals_complete": len(results), "proposals_planned": len(plan),
            "elapsed_seconds": round(time.time() - t0, 1)}


def _digest(path: Path) -> str:
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _local_scratch_mount(parent: Path) -> list[str]:
    filesystem = subprocess.check_output(['findmnt', '-n', '-o', 'FSTYPE,SOURCE', '--target',
                                          str(parent)], text=True, timeout=20).strip().split()
    if len(filesystem) < 2 or filesystem[0] not in {'xfs', 'ext4', 'btrfs'} or 'ceph' in ' '.join(filesystem).lower():
        raise ValueError('scratch mount is not verified local')
    return filesystem


def _verify_replay(table: Path, paper_root: Path, index: Path, classification: Path) -> None:
    """A table's self-declared digest cannot establish completeness."""
    from r1.c3.analysis_guard import guard_table, refuse_sealed
    refuse_sealed(paper_root, index, classification)
    guard_table(table, Path(table)/'proposals.jsonl', Path(table)/'configs.json')
    from r1.c3.dataset import build_from_sweep
    local = Path('/tmp')
    _local_scratch_mount(local)
    minimum = sum((table / name).stat().st_size for name in ('proposals.jsonl', 'configs.json')) * 2
    if shutil.disk_usage(local).free < minimum:
        raise ValueError('local scratch capacity insufficient for verification replay')
    with tempfile.TemporaryDirectory(prefix='r1_c3_evidence_replay_', dir=str(local)) as temp:
        rebuilt = Path(temp) / 'table'
        build_from_sweep(index, rebuilt, paper_root=paper_root, classification=classification)
        for name in ('proposals.jsonl', 'configs.json'):
            if (rebuilt / name).read_bytes() != (table / name).read_bytes():
                raise ValueError(f'evidence table differs from full source replay: {name}')
        rebuilt_meta = json.loads((rebuilt / 'build.json').read_text())
        existing_meta = json.loads((table / 'build.json').read_text())
        # The current working commit can advance after publication; the actual
        # science, paths, source digests and all replay checks must remain equal.
        rebuilt_meta.pop('commit', None)
        existing_meta.pop('commit', None)
        if rebuilt_meta != existing_meta:
            raise ValueError('evidence build metadata differs from full source replay')


def _published_bytes_ref(root: Path) -> str:
    """The published main commit; the fetched origin/main must equal the remote (fail closed)."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, timeout=30)
    try:
        remote = git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
        fetched = git('rev-parse', 'refs/remotes/origin/main').decode().strip()
    except (OSError, IndexError, subprocess.SubprocessError) as exc:
        raise ValueError('NOT CHECKABLE: published origin/main is not reachable') from exc
    if fetched != remote:
        raise ValueError('origin/main is stale or missing; fetch before evidence use')
    return remote


def _published_bytes(root: Path, rel: str) -> bytes:
    """B1 (a): the bytes of *rel* on the current, remotely published main (fetched origin/main must
    equal the remote). Authority files published after the reviewed code commit are read from there,
    so the operator's checkout of the code commit need not contain them."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, timeout=30)
    remote = _published_bytes_ref(root)
    try:
        return git('show', f'{remote}:{rel}')
    except subprocess.CalledProcessError as exc:
        raise ValueError(f'NOT CHECKABLE: {rel} is not published on origin/main') from exc


def _pinned_e1_bytes(root: Path, rel: str) -> bytes:
    """A pinned e1 report file at the reviewed e1 commit, which must be an ancestor of the published main.

    Read at the commit, not at main's tip, so that a later erratum on main neither blocks the audit nor makes its
    evidence unconsumable (review round 1, finding 3)."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, timeout=30)
    remote = _published_bytes_ref(root)
    try:
        subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', E1_REPLAY_COMMIT, remote],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('NOT CHECKABLE: the reviewed e1 replay commit is not an ancestor of published main') from exc
    try:
        return git('show', f'{E1_REPLAY_COMMIT}:{rel}')
    except subprocess.CalledProcessError as exc:
        raise ValueError(f'NOT CHECKABLE: {rel} is not in the reviewed e1 replay commit') from exc


def replay_environment_basis(paper_root: Path) -> dict:
    """B6 (a) and B1 (a): the published, reviewed e1 replay report replaces the launch-bound freeze.

    Reads the pinned report files and review at the reviewed e1 commit (exact reviewed bytes; the commit must be
    an ancestor of the published origin/main), and from the published origin/main docs/r1/PLAN.md with the
    R1-B2-GO row naming the report branch and commit; requires a PASS of 16/16 cases at tolerance 0 without STOP,
    an ACCEPTED review, and pins that match the sweep-1 runtime."""
    root = Path(paper_root).resolve()
    published = {}
    for rel, expected in E1_REPLAY_PINNED.items():
        data = _pinned_e1_bytes(root, rel)
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'e1 replay report file differs from the reviewed bytes: {rel}')
        published[rel] = data
    rows = _published_bytes(root, 'docs/r1/PLAN.md').decode('utf-8').splitlines()
    if not any(line.startswith('| R1-B2-GO |') and 'ops-e1-replay-amend-20261117' in line and '52992b22' in line
               and 'B6 (a)' in line and 'B4 (a)' in line and 'B1 (a)' in line for line in rows):
        raise ValueError('matching author PLAN row R1-B2-GO missing')
    summary = json.loads(published[f'{E1_REPLAY_REPORT_DIR}/summary.json'])
    if summary.get('verdict') != 'PASS' or summary.get('stop') is not None or summary.get('tolerance') != 0 or \
            not (summary.get('cases_planned') == summary.get('cases_run') == summary.get('cases_passed') == 16) or \
            summary.get('openml_offline_mechanism', {}).get('row') != 'R1-E1-OPENML-AMEND':
        raise ValueError('e1 replay report is not a 16/16 PASS at tolerance 0 under R1-E1-OPENML-AMEND')
    review_lines = [x.strip() for x in published[E1_REPLAY_REVIEW].decode('utf-8').splitlines() if x.strip()]
    if not review_lines or review_lines[-1] != 'VERDICT: ACCEPTED':
        raise ValueError('e1 replay review does not end with VERDICT: ACCEPTED')
    pins = json.loads(published[f'{E1_REPLAY_REPORT_DIR}/pins.json'])
    interpreter, harness = pins.get('interpreter', {}), pins.get('harness', {})
    if harness.get('commit') != '6adf3859de66c4814fcf376eed59880fbd8eeaf7' or \
            harness.get('uv_lock_sha256') != 'dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090' or \
            interpreter.get('python_version') != '3.13.15' or \
            interpreter.get('library_versions') != {'numpy': '2.4.4', 'pandas': '3.0.3', 'scikit-learn': '1.8.0',
                                                    'scipy': '1.17.1'} or \
            not interpreter.get('package_list_sha256') or not interpreter.get('build') or \
            not interpreter.get('prefix') or not interpreter.get('wrapper_target') or \
            not interpreter.get('newest_dist_info_mtime_utc') or not harness.get('path') or \
            pins.get('preserved_batch', {}).get('path') != E1_REPLAY_BATCH:
        raise ValueError('e1 replay pins do not match the sweep-1 runtime')
    caches = (summary.get('openml_offline_mechanism', {}).get('post_run') or {}).get('source_caches') or {}
    if sorted(caches) != sorted(E1_OPENML_CACHE_NODES) or harness.get('tracked_clean') is not True or \
            harness.get('pre_existing_untracked_caches') is not True:
        raise ValueError('e1 replay record lacks the six OpenML cache digests or the harness state')
    return {'ruling': 'R1-B2-GO B6 (a)', 'report_dir': E1_REPLAY_REPORT_DIR, 'review': E1_REPLAY_REVIEW,
            'e1_commit': E1_REPLAY_COMMIT, 'files_sha256': dict(E1_REPLAY_PINNED), 'harness_path': harness['path'],
            'data_caches_sha256': dict(caches),
            'interpreter': {k: interpreter[k] for k in ('build', 'prefix', 'wrapper_target', 'package_list_sha256',
                                                       'newest_dist_info_mtime_utc', 'python_version')},
            'disclosure': ENVIRONMENT_BASIS_DISCLOSURE}


def replay_environment_checks(basis: dict) -> dict:
    """Re-run the e1 replay's current-environment checks now and require the replay's recorded values."""
    from r1.scripts.c3_env_replay import Stop, check_environment
    batch = Path(E1_REPLAY_BATCH)
    harness = Path(os.environ.get('AR_HARNESS_ROOT', '')).resolve()
    if str(harness) != str(Path(basis['harness_path']).resolve()):
        raise ValueError('AR_HARNESS_ROOT is not the harness the e1 replay checked')
    try:
        current = check_environment(batch, batch / 'autoresearch_harness')
    except Stop as exc:
        raise ValueError(f'STOP: e1 replay environment check failed now: {exc}') from exc
    recorded = basis['interpreter']
    observed = {'build': current['build'], 'prefix': current['prefix'], 'wrapper_target': current['wrapper_target'],
                'package_list_sha256': current['current_package_list_sha256'],
                'newest_dist_info_mtime_utc': current['newest_dist_info_mtime_utc']}
    expected = {k: recorded[k] for k in observed}
    if observed != expected:
        raise ValueError(f'current environment differs from the e1 replay record: {observed} != {expected}')
    if sys.version != recorded['build'] or Path(sys.prefix).resolve() != Path(recorded['prefix']).resolve():
        raise ValueError('the audit does not run in the interpreter the e1 replay checked')
    return {'checked_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), **observed}


def harness_untracked_state(harness: Path, basis: dict) -> dict:
    """The batch harness's untracked files must be exactly what the e1 record found: files under the six OpenML
    data caches, whose tree digests equal the e1 post-run record, and E1_UNTRACKED_FILES (review round 1,
    finding 1). Anything else untracked is a STOP, as before."""
    from r1.scripts.c3_env_replay import tree_digest
    listed = subprocess.check_output(['git', '-C', str(harness), 'ls-files', '--others', '--exclude-standard', '-z'],
                                     timeout=60).decode().split('\0')
    prefixes = tuple(f'nodes/{node}/data_cache/' for node in E1_OPENML_CACHE_NODES)
    stray = sorted(p for p in listed if p and not p.startswith(prefixes) and p not in E1_UNTRACKED_FILES)
    if stray:
        raise ValueError(f'harness has untracked files outside the e1 record: {stray[:5]}')
    # Like the e1 mechanism, refuse every symlink: a linked directory would be neither listed nor hashed.
    for rel in [p for p in listed if p] + list(E1_UNTRACKED_FILES):
        if (harness / rel).is_symlink():
            raise ValueError(f'harness untracked path is a symlink: {rel}')
    for node in E1_OPENML_CACHE_NODES:
        root = harness / 'nodes' / node / 'data_cache'
        if root.is_symlink():
            raise ValueError(f'harness OpenML cache is a symlink: {node}')
        for base, dirs, files in os.walk(root, followlinks=False):
            for name in dirs + files:
                if (Path(base) / name).is_symlink():
                    raise ValueError(f'harness OpenML cache contains a symlink: {node}/{name}')
    digests = {node: tree_digest(harness / 'nodes' / node / 'data_cache') for node in E1_OPENML_CACHE_NODES}
    if digests != basis['data_caches_sha256']:
        raise ValueError('harness OpenML data caches differ from the e1 post-run tree digests')
    return {'basis': 'tracked-clean; untracked = the six OpenML data caches (tree digests = e1 post-run) and '
                     + ', '.join(E1_UNTRACKED_FILES), 'data_caches_sha256': digests,
            'untracked_count': sum(1 for p in listed if p)}


def worker_runtime_basis() -> dict:
    """B4 (a): the per-run probe record is accepted; its limitation is carried into every record."""
    return dict(WORKER_RUNTIME_BASIS)


def evidence_environment(paper_root: Path) -> dict:
    """Bind the audit to the e1-replayed runtime (R1-B2-GO B6 (a)), clean harness and locked sklearn."""
    basis = replay_environment_basis(paper_root)
    installed = {}
    for distribution in import_metadata.distributions():
        name = (distribution.metadata.get('Name') or '').lower().replace('_', '-')
        if not name or name in installed:
            raise ValueError('environment contains missing or duplicate package names')
        installed[name] = distribution.version
    if sys.version != basis['interpreter']['build']:
        raise ValueError('installed environment differs from the e1-replayed environment')
    from r1.scripts.c3_env_replay import canonical_packages
    probe_names = {}
    for distribution in import_metadata.distributions():   # the replay probe's normalisation (c3_env_replay.PROBE)
        name = re.sub(r'[-_.]+', '-', distribution.metadata.get('Name') or '').lower()
        if not name or name in probe_names:
            raise ValueError('environment contains missing or duplicate package names')
        probe_names[name] = distribution.version
    if canonical_packages(probe_names)[1] != basis['interpreter']['package_list_sha256']:
        raise ValueError('the audit process package list differs from the e1-replayed package list')
    if platform.node().split('.')[0] != E1_HOST:
        raise ValueError(f'the audit must run on {E1_HOST} (R1-B2-GO), the e1 replay host')
    raw = os.environ.get('AR_HARNESS_ROOT')
    if not raw:
        raise ValueError('AR_HARNESS_ROOT missing')
    harness = Path(raw).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(harness), *args], text=True).strip()
    commit = git('rev-parse', 'HEAD')
    if commit != '6adf3859de66c4814fcf376eed59880fbd8eeaf7' or git('status', '--porcelain', '--untracked-files=no'):
        raise ValueError('harness commit mismatch or dirty harness')
    untracked = harness_untracked_state(harness, basis)
    ignored = git('ls-files', '--others', '--ignored', '--exclude-standard', '--', 'src').splitlines()
    if any(Path(p).suffix in {'.py', '.so', '.pyd', '.dll', '.dylib'} for p in ignored):
        raise ValueError('ignored executable harness code can shadow pinned imports')
    from r1.harness import import_harness
    import_harness()
    for name in ('autoresearch.manager.base', 'autoresearch.nodes.registry', 'autoresearch.worker.local_worker'):
        importlib.import_module(name)
    for name, module in list(sys.modules.items()):
        if name != 'autoresearch' and not name.startswith('autoresearch.'):
            continue
        if not getattr(module, '__file__', None):
            raise ValueError('unverifiable harness module import')
        path = Path(module.__file__).resolve()
        if not path.is_relative_to(harness / 'src') or path.suffix != '.py':
            raise ValueError('harness import outside pinned checkout')
        rel = str(path.relative_to(harness))
        if subprocess.check_output(['git', '-C', str(harness), 'show', f'{commit}:{rel}']) != path.read_bytes():
            raise ValueError('harness import differs from pinned blob')
    lock = tomllib.loads((harness / 'uv.lock').read_text())
    versions = [p['version'] for p in lock.get('package', []) if p.get('name') == 'scikit-learn']
    actual = import_metadata.version('scikit-learn')
    if len(versions) != 1 or versions[0] != actual or actual != '1.8.0' or sys.version_info[:2] != (3, 13):
        raise ValueError('Python or sklearn version differs from sweep locked environment')
    numerical_versions = {name: import_metadata.version(name) for name in ('scikit-learn', 'numpy', 'scipy', 'pandas')}
    if sys.prefix == sys.base_prefix or numerical_versions != {'scikit-learn': '1.8.0', 'numpy': '2.4.4',
                                                                'scipy': '1.17.1', 'pandas': '3.0.3'}:
        raise ValueError('STOP: audit is not in the expected numerical venv or versions differ')
    checks = replay_environment_checks(basis)
    return {'harness_commit': commit, 'harness_dirty': False, 'harness_root': str(harness),
            'harness_untracked': untracked,
            'uv_lock_sha256': _digest(harness / 'uv.lock'), 'python': sys.version, 'scikit_learn': actual,
            'worker_python': sys.executable, 'worker_prefix': sys.prefix, 'worker_versions': numerical_versions,
            'package_list_sha256': _package_list_hash(installed),
            'environment_basis': basis, 'environment_checks_at_start': checks,
            'worker_runtime_basis': worker_runtime_basis()}


def evidence_paper_provenance(paper_root: Path, code_commit: str | None, review_path: str | None) -> dict:
    """Bind executing imports to a clean, published and independently reviewed commit."""
    root = Path(paper_root).resolve()
    if not code_commit or len(code_commit) != 40 or not review_path:
        raise ValueError('full reviewed code commit and review path required')
    review = Path(review_path)
    if review.is_absolute() or '..' in review.parts or review.parts[:3] != ('docs', 'r1', 'reviews'):
        raise ValueError('review must be repository-relative under docs/r1/reviews')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, timeout=30)
    head = git('rev-parse', 'HEAD').decode().strip()
    published = git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
    if head != code_commit or git('rev-parse', 'refs/remotes/origin/main').decode().strip() != published:
        raise ValueError('paper code HEAD or published main mismatch')
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', code_commit, published],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if git('status', '--porcelain', '--untracked-files=all', '--', 'r1').strip():
        raise ValueError('paper code has tracked or untracked changes')
    ignored = git('ls-files', '--others', '--ignored', '--exclude-standard', '--', 'r1').decode().splitlines()
    if any(Path(p).suffix in {'.py', '.so', '.pyd', '.dll', '.dylib'} for p in ignored):
        raise ValueError('ignored executable code can shadow reviewed imports')
    from r1.c3 import arms, dataset, features, labels  # load all evidence-side helpers before checking
    import r1.scripts.c3_env_replay  # noqa: F401  (the B6 (a) checks run its code; check its bytes too)
    allowed = [root, Path(os.environ['AR_HARNESS_ROOT']).resolve() / 'src',
               Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    for entry in sys.path:
        location = Path(entry or os.getcwd()).resolve()
        if not any(location == p or location.is_relative_to(p) for p in allowed):
            raise ValueError(f'untrusted Python import path: {location}')
    modules = [m for name, m in sys.modules.items() if name == 'r1' or name.startswith('r1.')]
    for module in modules:
        if not getattr(module, '__file__', None):
            raise ValueError('unverifiable paper module import')
        path = Path(module.__file__).resolve()
        if not path.is_relative_to(root / 'r1') or path.suffix != '.py':
            raise ValueError('executing paper import is outside reviewed checkout')
        rel = str(path.relative_to(root))
        if git('show', f'{code_commit}:{rel}') != path.read_bytes():
            raise ValueError(f'paper import differs from reviewed commit: {rel}')
    review_bytes = git('show', f'{published}:{review_path}')
    review_lines = review_bytes.decode('utf-8').splitlines()
    if f'Code-Commit: {code_commit}' not in review_lines or 'Verdict: ACCEPTED' not in review_lines:
        raise ValueError('published independent review does not accept exact code commit')
    return {'paper_code_commit': code_commit, 'published_main': published, 'paper_code_clean': True,
            'review_path': review_path, 'review_sha256': hashlib.sha256(review_bytes).hexdigest()}


def evidence_output_path(paper_root: Path, out: Path) -> Path:
    root, out = Path(paper_root).resolve(), Path(out)
    # Disallow any symlink in the requested path, including the output itself.
    for p in (out, *out.parents):
        if p.is_symlink():
            raise ValueError('symlink in evidence output path')
    parent = root / 'results/r1/evidence'
    if out.parent.resolve() != parent or not out.name.startswith('C3_audit_EVIDENCE_') or out.exists():
        raise ValueError('evidence output must be a new dedicated directory in results/r1/evidence')
    return out


def evidence_resources(plan: list[dict], workers: int, deadline: float, scratch_root: Path,
                       required_scratch_bytes: int, ceph_reserve_files: int) -> dict:
    """Operator timeout is not a protocol budget; enforce existing host floors."""
    if not math.isfinite(deadline) or deadline <= 0:
        raise ValueError('operator deadline must be finite and positive')
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)
    if workers < 1 or workers > 16 or workers >= cpus:
        raise ValueError('workers exceed authorized or co-tenancy limit')
    scratch_root = Path(scratch_root)
    if any(p.is_symlink() for p in (scratch_root, *scratch_root.parents)) or \
            scratch_root.parent.resolve() != Path('/tmp').resolve() or scratch_root.exists() or \
            not scratch_root.name.startswith('r1_c3_audit_EVIDENCE_'):
        raise ValueError('scratch must be a new dedicated directory directly under local /tmp')
    filesystem = _local_scratch_mount(scratch_root.parent)
    if required_scratch_bytes <= 0 or shutil.disk_usage(scratch_root.parent).free < required_scratch_bytes:
        raise ValueError('local scratch capacity below operator estimate')
    ceph = Path('/ceph/dwong')
    if shutil.disk_usage(ceph).free < 50 * 1024**3:
        raise ValueError('Ceph free space below authorized 50 GiB floor')
    def attr(name):
        return int(subprocess.check_output(['getfattr', '-n', name, '--only-values', str(ceph)], text=True).strip())
    files_used, files_max = attr('ceph.dir.rfiles'), attr('ceph.quota.max_files')
    unique_configs = len({(p['node'], p[k]) for p in plan for k in ('candidate_hash', 'incumbent_hash')})
    estimated_files = unique_configs + 12  # one durable seed journal per config plus run metadata
    if files_max <= 0 or ceph_reserve_files < estimated_files or files_max - files_used < ceph_reserve_files:
        raise ValueError('Ceph file-count headroom below operator reserve')
    return {'workers': workers, 'available_cpus': cpus, 'operator_deadline_seconds': deadline,
            'operator_deadline_is_protocol_budget': False, 'unique_configs': unique_configs,
            'planned_seed_runs': unique_configs * len(DEFAULT_SEEDS), 'estimated_ceph_files': estimated_files,
            'ceph_files_used': files_used, 'ceph_files_max': files_max, 'ceph_reserve_files': ceph_reserve_files,
            'scratch_root': str(scratch_root), 'scratch_mount': filesystem,
            'required_scratch_bytes': required_scratch_bytes,
            'scratch_free_bytes': shutil.disk_usage(scratch_root.parent).free}


def partition_population(rows: list[dict], configs: dict) -> tuple[list[dict], dict]:
    """Complete, non-sampled partition: rule no-ops, duplicates (never audited), eligible (all audited)."""
    from r1.c3.arms import is_duplicate, is_noop
    if not rows or len({r['proposal_id'] for r in rows}) != len(rows):
        raise ValueError('empty table or duplicate proposal IDs')
    counts = {'noops': 0, 'duplicates': 0, 'eligible': 0}
    selected = []
    for row in rows:
        if is_noop(row):
            counts['noops'] += 1
        elif is_duplicate(row):
            counts['duplicates'] += 1
        else:
            for name in ('candidate_hash', 'incumbent_hash'):
                if row[name] not in configs:
                    raise ValueError('eligible proposal lacks configuration')
            selected.append({k: row[k] for k in ('proposal_id', 'node', 'candidate_hash', 'incumbent_hash')})
            selected[-1]['reason'] = 'full_population'
            selected[-1]['inclusion_probability'] = 1.0
            counts['eligible'] += 1
    if not selected or sum(counts.values()) != len(rows):
        raise ValueError('evidence plan has no eligible proposals or incomplete partition')
    return selected, counts


def evidence_plan(table: Path, paper_root: Path, index: Path, classification: Path) -> tuple[list[dict], dict]:
    """Build the complete, non-sampled eligible plan and bind it to author provenance."""
    from r1.c3.analysis_guard import guard_table, refuse_sealed
    refuse_sealed(paper_root, index, classification)
    guard_table(table, Path(table)/'proposals.jsonl', Path(table)/'configs.json')
    from r1.c3.dataset import evidence_classification, load_table
    evidence_classification(index, paper_root, classification)
    table = Path(table)
    metadata = json.loads((table / 'build.json').read_text())
    expected = metadata.get('classification') or {}
    if metadata.get('label') != 'EVIDENCE' or expected.get('sha256') != _digest(classification) or \
            metadata.get('sweep_index', {}).get('sha256') != _digest(index):
        raise ValueError('table does not match authorized evidence classification')
    if metadata.get('table_sha256') != {name: _digest(table / name) for name in ('proposals.jsonl', 'configs.json')}:
        raise ValueError('evidence table contents differ from build record')
    _verify_replay(table, paper_root, index, classification)
    rows = load_table(table)
    configs = json.loads((table / 'configs.json').read_text())
    selected, counts = partition_population(rows, configs)
    binding = {'label': 'EVIDENCE', 'index_sha256': _digest(index),
               'classification_sha256': _digest(classification), 'proposals_sha256': _digest(table / 'proposals.jsonl'),
               'configs_sha256': _digest(table / 'configs.json'), 'counts': counts,
               'label_seeds': list(DEFAULT_SEEDS[:5]), 'evaluation_seeds': list(DEFAULT_SEEDS[5:])}
    return selected, binding


def validate_evidence_results(plan: list[dict], cache: RunCache) -> list[dict]:
    """Reject missing, failed, non-finite or mismatched records; never drop seeds."""
    for proposal in plan:
        for key in ('candidate_hash', 'incumbent_hash'):
            for seed in DEFAULT_SEEDS:
                row = cache.get(proposal['node'], proposal[key], seed)
                if row is None or row.get('success') is not True or row.get('changed_files') is not False or \
                        row.get('metric') is None or not math.isfinite(float(row['metric'])):
                    raise ValueError('missing or invalid evidence audit run')
    result = audit_results(plan, cache, DEFAULT_SEEDS)
    if len(result) != len(plan) or any(r['k'] != 10 or r['seeds'] != list(DEFAULT_SEEDS) for r in result):
        raise ValueError('evidence audit is incomplete')
    return result


def evidence_blocks(table: Path, results: list[dict]) -> tuple[list[dict], list[dict]]:
    """Build disjoint role blocks; only rule-noops and auditable proposals get labels."""
    from r1.c3.arms import is_duplicate, is_noop
    from r1.c3.dataset import load_table
    rows = load_table(Path(table))
    audits = {row['proposal_id']: row for row in results}
    if len(audits) != len(results):
        raise ValueError('duplicate proposal ID in audit results')
    labels, evaluations, used = [], [], set()
    for row in rows:
        pid, node = row['proposal_id'], row['node']
        if is_noop(row):
            labels.append({'proposal_id': pid, 'node': node, 'label_kind': 'rule_noop',
                           'delta_label': 0.0, 'se_label': 0.0,
                           'soft_parameters': {'inert': True}})
        elif is_duplicate(row):
            if pid in audits:
                raise ValueError('duplicate proposal must not receive an audit label')
        else:
            result = audits.get(pid)
            if result is None or result.get('node') != node or result.get('seeds') != list(DEFAULT_SEEDS):
                raise ValueError('evidence result does not cover eligible table rows')
            label, evaluation = split_audit(result)
            if label['k'] != 5 or evaluation['k'] != 5 or label['se'] is None or evaluation['se'] is None:
                raise ValueError('evidence result lacks complete 5+5 paired values')
            sigma = float(row['sigma_node'])
            if not math.isfinite(sigma) or sigma <= 0:
                raise ValueError('invalid node sigma for evidence soft-label parameters')
            labels.append({'proposal_id': pid, 'node': node, 'label_kind': 'audit',
                           'seeds': list(DEFAULT_SEEDS[:5]), 'delta_label': label['delta_audit'],
                           'se_label': label['se'], 'soft_parameters': {'inert': False,
                               'sigma_node': sigma, 'k_label': 5,
                               'delta_label': label['delta_audit'], 'se_label': label['se']}})
            evaluations.append({'proposal_id': pid, 'node': node, 'seeds': list(DEFAULT_SEEDS[5:]),
                                'delta_evaluation': evaluation['delta_audit'], 'se_evaluation': evaluation['se']})
            used.add(pid)
    if used != set(audits):
        raise ValueError('audit results contain unexpected proposal IDs')
    return labels, evaluations


def evidence_cache(plan: list[dict], path: Path) -> RunCache:
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    expected = {(p['node'], p[k], seed) for p in plan
                for k in ('candidate_hash', 'incumbent_hash') for seed in DEFAULT_SEEDS}
    seen = set()
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        key = (row['node'], row['config_hash'], int(row['seed']))
        if key in seen or key not in expected:
            raise ValueError('duplicate or unexpected evidence cache entry')
        seen.add(key)
    if seen != expected:
        raise ValueError('evidence cache key set incomplete')
    return RunCache(path)


def validate_worker_records(path: Path, environment: dict) -> None:
    """Every worker seed record must identify the approved venv and package snapshot."""
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    expected = {k: environment.get(k) for k in
                ('worker_python', 'worker_prefix', 'worker_versions', 'package_list_sha256')}
    if not all(expected.values()):
        raise ValueError('missing expected worker runtime')
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        runtime = json.loads(line).get('worker_runtime') or {}
        if runtime.get('worker_python') != expected['worker_python'] or \
                runtime.get('prefix') != expected['worker_prefix'] or \
                runtime.get('prefix') == runtime.get('base_prefix') or \
                runtime.get('versions') != expected['worker_versions'] or \
                runtime.get('package_list_sha256') != expected['package_list_sha256'] or \
                not runtime.get('worker_command_python') or not runtime.get('worker_python_realpath'):
            raise ValueError('worker runtime record differs from approved venv')


def monitor_evidence_resources(scratch: Path, required_scratch_bytes: int, ceph_reserve_files: int) -> dict:
    """Bounded live check; any unavailable measurement fails closed."""
    _local_scratch_mount(scratch)
    scratch_free = shutil.disk_usage(scratch).free
    ceph_free = shutil.disk_usage('/ceph/dwong').free
    def attr(name):
        return int(subprocess.check_output(['getfattr', '-n', name, '--only-values', '/ceph/dwong'],
                                           text=True, timeout=20).strip())
    used, maximum = attr('ceph.dir.rfiles'), attr('ceph.quota.max_files')
    if scratch_free < required_scratch_bytes or ceph_free < 50 * 1024**3 or maximum <= 0 or maximum - used < ceph_reserve_files:
        raise ValueError('live scratch or Ceph resource floor reached')
    return {'scratch_free_bytes': scratch_free, 'ceph_free_bytes': ceph_free,
            'ceph_files_used': used, 'ceph_files_max': maximum}


@contextmanager
def evidence_scratch(out: Path, scratch_root: Path, provenance: dict):
    scratch = str(scratch_root)
    created = False
    try:
        scratch_root.mkdir(parents=False, exist_ok=False)
        created = True
        (out / 'scratch.json').write_text(json.dumps({'scratch': scratch}) + '\n')
        yield scratch
    except BaseException as exc:
        # Keep all artifacts and attempt a durable STOP in both locations.
        payload = json.dumps({'label': 'EVIDENCE', 'reason': f'{type(exc).__name__}: {exc}',
                              'scratch': scratch, 'paper_provenance': provenance}, indent=2) + '\n'
        targets = [out / 'STOP.json'] + ([scratch_root / 'STOP.json'] if created else [])
        for target in targets:
            try:
                if not target.exists():
                    target.write_text(payload)
            except OSError:
                pass
        raise


def b2_addendum(paper_root: Path, addendum: Path | None, code_commit: str | None) -> dict:
    """The author's B.2 authorization addendum (R1-B2-GO precondition): published on origin/main, under
    docs/r1/authorizations, naming R1-B2-GO, the reviewed paper code commit, the harness pin and K = 10."""
    root = Path(paper_root).resolve()
    if addendum is None:
        raise ValueError('B.2 authorization addendum required (R1-B2-GO)')
    rel = PurePosixPath(str(addendum))
    if rel.is_absolute() or '..' in rel.parts or len(rel.parts) != 4 or rel.parts[:3] != ('docs', 'r1', 'authorizations') or \
            not rel.name.startswith('c3_b2_addendum_') or rel.suffix != '.md':
        raise ValueError('addendum must be docs/r1/authorizations/c3_b2_addendum_<date>.md (repository-relative)')
    data = _published_bytes(root, str(rel))
    text = data.decode('utf-8')
    if 'R1-B2-GO' not in text or not code_commit or code_commit not in text or \
            '6adf3859de66c4814fcf376eed59880fbd8eeaf7' not in text or 'K = 10' not in text:
        raise ValueError('addendum does not bind R1-B2-GO, the reviewed code commit, the harness pin and K = 10')
    return {'path': str(rel), 'sha256': hashlib.sha256(data).hexdigest()}


def evidence_run(table: Path, paper_root: Path, index: Path, classification: Path, out: Path,
                 workers: int, deadline: float, *, code_commit: str | None = None,
                 code_review: str | None = None, addendum: Path | None = None,
                 scratch_root: Path | None = None, required_scratch_bytes: int = 0,
                 ceph_reserve_files: int = 0) -> dict:
    """One fresh audit output; no pilot cache, existing directory, or automatic resume."""
    if workers < 1 or not math.isfinite(deadline) or deadline <= 0:
        raise ValueError('workers and deadline must be positive')
    provenance = evidence_paper_provenance(paper_root, code_commit, code_review)
    authorization = b2_addendum(paper_root, addendum, code_commit)
    environment = {**evidence_environment(paper_root), **provenance, 'b2_addendum': authorization}
    plan, binding = evidence_plan(table, paper_root, index, classification)
    if scratch_root is None:
        raise ValueError('explicit local scratch root is required')
    resources = evidence_resources(plan, workers, deadline, scratch_root, required_scratch_bytes, ceph_reserve_files)
    out = evidence_output_path(paper_root, out)
    out.mkdir(parents=True, exist_ok=False)
    # Local scratch is dedicated to this single call; no prior batch cache is read.
    with evidence_scratch(out, Path(scratch_root), provenance) as scratch:
        (out / 'plan.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in plan))
        (out / 'evidence_binding.json').write_text(json.dumps(binding, indent=2) + '\n')
        (out / 'environment.json').write_text(json.dumps(environment, indent=2) + '\n')
        (out / 'resources.json').write_text(json.dumps(resources, indent=2) + '\n')
        configs = json.loads((Path(table) / 'configs.json').read_text())
        jobs = sorted({(p['node'], p[k]) for p in plan for k in ('candidate_hash', 'incumbent_hash')})
        cache = RunCache(out / 'runs.jsonl')
        started, failure, done = time.monotonic(), None, 0
        (out / 'seed_journals').mkdir()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            pending = {}
            next_resource_check = 0.0
            while jobs or pending:
                if failure is None and time.monotonic() - started >= deadline:
                    failure = 'audit deadline exceeded'
                if failure is None and time.monotonic() >= next_resource_check:
                    try:
                        sample = monitor_evidence_resources(Path(scratch), required_scratch_bytes, ceph_reserve_files)
                        with (out / 'resource_monitor.jsonl').open('a') as fh:
                            fh.write(json.dumps({'utc': time.time(), **sample}) + '\n')
                        next_resource_check = time.monotonic() + 30.0
                    except Exception as exc:
                        failure = f'resource monitoring STOP: {type(exc).__name__}: {exc}'
                while failure is None and jobs and len(pending) < workers:
                    node, h = jobs.pop(0)
                    journal_id = hashlib.sha256(json.dumps([node, h]).encode()).hexdigest()
                    journal = out / 'seed_journals' / f'{journal_id}.jsonl'
                    expected_worker = {k: environment[k] for k in
                                       ('worker_python', 'worker_prefix', 'worker_versions', 'package_list_sha256')}
                    pending[pool.submit(run_config, node, configs[h]['files'], list(DEFAULT_SEEDS), scratch, True,
                                        str(journal), {'node': node, 'config_hash': h,
                                                       'expected_worker': expected_worker})] = (node, h)
                if not pending:
                    break
                finished, _ = wait(list(pending), return_when=FIRST_COMPLETED, timeout=5)
                for future in finished:
                    node, h = pending.pop(future)
                    try:
                        rows = [{'node': node, 'config_hash': h, **r} for r in future.result()]
                        cache.add(rows)  # preserve actual failed rows as well
                        if len(rows) != 10 or [r.get('seed') for r in rows] != list(DEFAULT_SEEDS) or any(
                            r.get('success') is not True or r.get('changed_files') is not False or
                            r.get('metric') is None or not math.isfinite(float(r['metric'])) for r in rows):
                            failure = failure or f'invalid audit result for {node}/{h}'
                    except Exception as exc:
                        failure = failure or f'audit worker failure: {type(exc).__name__}: {exc}'
                    done += 1
            if time.monotonic() - started >= deadline:
                failure = failure or 'audit deadline exceeded'
            if failure is not None:
                (out / 'STOP.json').write_text(json.dumps({'label': 'EVIDENCE', 'reason': failure,
                    'unscheduled': len(jobs), 'configs_completed': done, 'scratch': scratch,
                    'paper_provenance': provenance}, indent=2) + '\n')
                raise ValueError(f'{failure}; in-flight work preserved; STOP')
        monitor_evidence_resources(Path(scratch), required_scratch_bytes, ceph_reserve_files)
        # The audited OpenML caches must be unchanged after the runs, as the e1 replay re-checked after its run.
        try:
            after = harness_untracked_state(Path(environment['harness_root']), environment['environment_basis'])
            if after['data_caches_sha256'] != environment['harness_untracked']['data_caches_sha256']:
                raise ValueError('OpenML cache digests changed during the audit')
        except Exception as exc:
            (out / 'STOP.json').write_text(json.dumps({'label': 'EVIDENCE', 'reason': f'post-run cache check: {exc}',
                'unscheduled': 0, 'configs_completed': done, 'scratch': scratch,
                'paper_provenance': provenance}, indent=2) + '\n')
            raise ValueError(f'post-run cache check failed: {exc}; STOP') from exc
        from r1.c3.release import producer_context
        with producer_context():                       # the writer reads back its own fresh run log
            validate_worker_records(out / 'runs.jsonl', environment)
            result = validate_evidence_results(plan, evidence_cache(plan, out / 'runs.jsonl'))
        labels, evaluations = evidence_blocks(table, result)
        (out / 'label_block.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in labels))
        (out / 'evaluation_block.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in evaluations))
        status = {'configs_run_this_call': done, 'configs_remaining': len(jobs),
                  'proposals_complete': len(result), 'proposals_planned': len(plan)}
        completion = {'schema': COMPLETION_SCHEMA, 'label': 'EVIDENCE',
            'authorization_sha256': _digest(Path(paper_root) / 'docs/r1/authorizations/c3_sweep1_20261027.md'),
            'b2_addendum_sha256': authorization['sha256'],
            'classification_sha256': _digest(classification), 'index_sha256': _digest(index),
            'build_sha256': _digest(Path(table) / 'build.json'),
            'proposals_sha256': _digest(Path(table) / 'proposals.jsonl'),
            'configs_sha256': _digest(Path(table) / 'configs.json'),
            'plan_sha256': _digest(out / 'plan.jsonl'),
            'label_block_sha256': _digest(out / 'label_block.jsonl'),
            'evaluation_block_sha256': _digest(out / 'evaluation_block.jsonl'),
            'runs_sha256': _digest(out / 'runs.jsonl'), 'environment_sha256': _digest(out / 'environment.json'),
            'per_run_worker_runtime': 'runs.jsonl:worker_runtime',
            'worker_runtime_basis': worker_runtime_basis(),
            'environment_basis': {'ruling': 'R1-B2-GO B6 (a)', 'report_dir': E1_REPLAY_REPORT_DIR,
                                  'disclosure': ENVIRONMENT_BASIS_DISCLOSURE},
            'resources_sha256': _digest(out / 'resources.json'),
            'counts': binding['counts'], 'label_seeds': list(DEFAULT_SEEDS[:5]),
            'evaluation_seeds': list(DEFAULT_SEEDS[5:])}
        tmp = out / '.evidence_completion.tmp'
        tmp.write_text(json.dumps(completion, indent=2) + '\n')
        tmp.replace(out / 'evidence_completion.json')
    return {**status, 'label': 'EVIDENCE', 'counts': binding['counts']}


def verify_evidence_completion(table: Path, audits_path: Path, paper_root: Path, index: Path,
                               classification: Path) -> dict:
    """Validate complete evidence on consumption; never trust summary metrics alone.

    runs.jsonl worker_runtime values come from a separate probe; under R1-B2-GO B4 (a) they are accepted
    with that limitation, which the completion and environment records carry (worker_runtime_basis).

    It opens ``runs.jsonl`` and ``evaluation_block.jsonl``: before the T0 test release row it runs only inside the
    release step (PRE-STAGE A, §6 integrity carve-out; ``release.require_integrity_or_test_release``)."""
    from r1.c3.release import require_integrity_or_test_release
    require_integrity_or_test_release("T0", "evaluation-seed values (verify_evidence_completion)")
    table, audits_path = Path(table), Path(audits_path)
    out = audits_path.parent
    if audits_path.name != 'label_block.jsonl' or (out / 'STOP.json').exists() or (out / 'audits.jsonl').exists():
        raise ValueError('audit stopped, mixed audit file present, or unexpected label block path')
    completion = json.loads((out / 'evidence_completion.json').read_text())
    plan, binding = evidence_plan(table, paper_root, index, classification)
    environment = json.loads((out / 'environment.json').read_text())
    addendum = environment.get('b2_addendum') or {}
    if b2_addendum(paper_root, addendum.get('path'), environment.get('paper_code_commit')) != addendum:
        raise ValueError('recorded B.2 addendum missing or changed')
    expected = {'schema': COMPLETION_SCHEMA, 'label': 'EVIDENCE',
        'authorization_sha256': _digest(Path(paper_root) / 'docs/r1/authorizations/c3_sweep1_20261027.md'),
        'b2_addendum_sha256': addendum['sha256'],
        'classification_sha256': _digest(classification), 'index_sha256': _digest(index),
        'build_sha256': _digest(table / 'build.json'), 'proposals_sha256': _digest(table / 'proposals.jsonl'),
        'configs_sha256': _digest(table / 'configs.json'), 'plan_sha256': _digest(out / 'plan.jsonl'),
        'label_block_sha256': _digest(audits_path),
        'evaluation_block_sha256': _digest(out / 'evaluation_block.jsonl'),
        'runs_sha256': _digest(out / 'runs.jsonl'), 'per_run_worker_runtime': 'runs.jsonl:worker_runtime',
        'worker_runtime_basis': worker_runtime_basis(),
        'environment_basis': {'ruling': 'R1-B2-GO B6 (a)', 'report_dir': E1_REPLAY_REPORT_DIR,
                              'disclosure': ENVIRONMENT_BASIS_DISCLOSURE},
        'environment_sha256': _digest(out / 'environment.json'), 'resources_sha256': _digest(out / 'resources.json'),
        'counts': binding['counts'],
        'label_seeds': list(DEFAULT_SEEDS[:5]), 'evaluation_seeds': list(DEFAULT_SEEDS[5:])}
    if completion != expected:
        raise ValueError('evidence completion metadata mismatch')
    recorded_plan = [json.loads(x) for x in (out / 'plan.jsonl').read_text().splitlines() if x.strip()]
    if recorded_plan != plan:
        raise ValueError('evidence plan differs from complete replay')
    if environment.get('harness_commit') != '6adf3859de66c4814fcf376eed59880fbd8eeaf7' or \
            environment.get('harness_dirty') is not False or environment.get('scikit_learn') != '1.8.0' or \
            not environment.get('python', '').startswith('3.13.') or not environment.get('uv_lock_sha256') or \
            environment.get('paper_code_clean') is not True:
        raise ValueError('recorded evidence environment is invalid')
    validate_worker_records(out / 'runs.jsonl', environment)
    basis = replay_environment_basis(paper_root)
    at_start = environment.get('environment_checks_at_start') or {}
    observed_keys = ('build', 'prefix', 'wrapper_target', 'package_list_sha256', 'newest_dist_info_mtime_utc')
    untracked = environment.get('harness_untracked') or {}
    if environment.get('environment_basis') != basis or environment.get('python') != basis['interpreter']['build'] or \
            environment.get('worker_runtime_basis') != worker_runtime_basis() or \
            {k: at_start.get(k) for k in observed_keys} != {k: basis['interpreter'][k] for k in observed_keys} or \
            untracked.get('data_caches_sha256') != basis['data_caches_sha256']:
        raise ValueError('audit environment does not bind the e1-replayed environment basis')
    reviewed_commit = environment.get('paper_code_commit', '')
    review_path = environment.get('review_path', '')
    review_rel = Path(review_path)
    if len(reviewed_commit) != 40 or review_rel.is_absolute() or '..' in review_rel.parts or \
            review_rel.parts[:3] != ('docs', 'r1', 'reviews'):
        raise ValueError('recorded audit review is invalid')
    root = Path(paper_root)
    published = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'origin/main'], text=True).strip()
    review_bytes = subprocess.check_output(['git', '-C', str(root), 'show', f'{published}:{review_path}'])
    review_lines = review_bytes.decode('utf-8').splitlines()
    if hashlib.sha256(review_bytes).hexdigest() != environment.get('review_sha256') or \
            f'Code-Commit: {reviewed_commit}' not in review_lines or 'Verdict: ACCEPTED' not in review_lines:
        raise ValueError('recorded audit review is not published or does not accept code')
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', reviewed_commit, published],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    recomputed = validate_evidence_results(plan, evidence_cache(plan, out / 'runs.jsonl'))
    expected_labels, expected_evaluations = evidence_blocks(table, recomputed)
    recorded_labels = [json.loads(x) for x in audits_path.read_text().splitlines() if x.strip()]
    recorded_evaluations = [json.loads(x) for x in (out / 'evaluation_block.jsonl').read_text().splitlines() if x.strip()]
    if recorded_labels != expected_labels or recorded_evaluations != expected_evaluations:
        raise ValueError('evidence role blocks differ from raw seed results')
    return completion


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--plan", required=True)
    r.add_argument("--configs", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)))
    r.add_argument("--deadline", type=float, default=150.0)
    r.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    c = sub.add_parser("collect")
    c.add_argument("--plan", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--seeds", type=int, nargs="+", default=None,
                   help="default: DIR/audit_seeds.json, else the seeds present in DIR/runs.jsonl")
    e = sub.add_parser('evidence-run', help='fresh authorized complete audit; no resume')
    e.add_argument('--table', required=True)
    e.add_argument('--paper-root', required=True)
    e.add_argument('--index', required=True)
    e.add_argument('--classification', required=True)
    e.add_argument('--out', required=True)
    e.add_argument('--workers', type=int, required=True)
    e.add_argument('--deadline', type=float, required=True)
    e.add_argument('--code-commit', required=True, help='published full reviewed paper code commit')
    e.add_argument('--code-review', required=True, help='published independent review path')
    e.add_argument('--addendum', required=True,
                   help='published B.2 authorization addendum docs/r1/authorizations/c3_b2_addendum_<date>.md')
    e.add_argument('--scratch-root', required=True, help='new dedicated local directory directly under /tmp')
    e.add_argument('--required-scratch-bytes', type=int, required=True, help='independently estimated local scratch requirement')
    e.add_argument('--ceph-reserve-files', type=int, required=True, help='operator file-count reserve including estimated outputs')
    args = ap.parse_args(argv)
    if args.cmd == 'evidence-run':
        print(json.dumps(evidence_run(Path(args.table), Path(args.paper_root), Path(args.index),
                                      Path(args.classification), Path(args.out), args.workers, args.deadline,
                                      code_commit=args.code_commit, code_review=args.code_review,
                                      addendum=Path(args.addendum), scratch_root=Path(args.scratch_root),
                                      required_scratch_bytes=args.required_scratch_bytes, ceph_reserve_files=args.ceph_reserve_files)))
        return 0
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(args.plan, getattr(args,'configs',None), args.out)
    from r1.c3.release import ReleaseStop, is_evidence_dir
    if is_evidence_dir(args.out) or is_evidence_dir(Path(args.out).resolve()):
        raise ReleaseStop(f"STOP: {args.out} is an evidence audit directory; '{args.cmd}' would mix a legacy run log or "
                          "audits.jsonl into it (PRE-STAGE A)")
    plan = [json.loads(x) for x in Path(args.plan).read_text().splitlines() if x.strip()]
    if args.cmd == "run":
        configs = json.loads(Path(args.configs).read_text())
        status = run_plan(plan, configs, Path(args.out), tuple(args.seeds), args.workers, args.deadline)
        print(json.dumps(status))
    else:
        res = audit_results(plan, RunCache(Path(args.out) / "runs.jsonl"), resolve_seeds(Path(args.out), args.seeds))
        (Path(args.out) / "audits.jsonl").write_text("".join(json.dumps(x) + "\n" for x in res))
        print(json.dumps({"audited": len(res), "planned": len(plan)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
