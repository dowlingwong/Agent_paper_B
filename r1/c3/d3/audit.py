"""D.3 G6: the Y / Y(w) audit over campaign snapshots (design §3, pre-declaration §7).

ENGINEERING_ONLY. AI-assisted (compute worker, 27 Nov 2026). Tier E: it fixes the outcome Y, so the unit needs an
accepted independent review before any D.3 campaign is audited.

For one campaign, the audit runs the **incumbent** configuration and the **start** configuration on the instance's
K = 10 audit seeds and returns

    y_raw(w) = (1/K) * sum_k [m(incumbent, a_k) - m(start, a_k)],    Y(w) = y_raw(w) / sigma_node

with the audit seed of instance ``s`` (6201-6218) and index ``k`` (1-10)::

    a_k = 6700 + 10 * (s - 6201) + k          (6701-6880)

The unit reads only a campaign's sealed ``snapshots/`` records and the node's code; it opens no label, evaluation or
test partition. Every audit value is a property of the configuration, never of a proposal's logged metric.

Inputs (the G1 snapshot contract)
--------------------------------
``snapshots/final.json`` is required; ``snapshots/w{5,10,15,20}.json`` are optional (a campaign that ends early has
only the points it reached). Each snapshot carries ``stage``, ``arm``, ``node``, ``repetition``, ``instance_id``,
``w``, ``incumbent_config`` (file texts) and ``start_config`` (file texts). The audit refuses a snapshot whose
declared fields differ from the campaign directory or whose ``config_sha256`` does not hash its own contents.

Records
-------
For every audited point, ``<out>/<stage>/<arm>/r<rep>/w<w>/<instance_id>.json`` with the ten seed runs, the paired
deltas, ``y_raw``, ``sigma_node``, ``Y``, cache flags and each run's sha256; then ``Y_final.jsonl`` (one primary row
per campaign), ``Y_w.jsonl`` (one descriptive row per point; ``missing_w`` where the point does not exist) and
``SHA256SUMS``. When ``final.json`` has the same config as an existing ``w20.json``, the primary row references that
w20 record (no duplicate audit, design §3.3).

Cache
-----
Key ``(node, config_sha256, audit_seed)`` for the incumbent and the start configuration, shared across arms,
repetitions and w points. A cached run is reused only when its ``run_sha256`` is present; a missing provenance is a
STOP. A hit is disclosed per row. The cache is bound to one audit environment: the launcher starts a fresh cache
file per environment record and refuses to mix an environment change into one cache.

This unit does not parallelise. The launcher runs one audit job per ``(stage, arm, repetition)``. Separate
processes may append cache rows, but a JSONL line write is not atomic: the launcher serialises the cache appends and
the ``Y_final``/``Y_w`` row appends, or merges per-instance rows after the jobs.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping

from r1.c3.d3.snapshots import config_sha256

SCHEMA = "r1_d3_audit/v1"
ROW_SCHEMA = "r1_d3_audit_row/v1"
AUDIT_SEED_BASE = 6700
K = 10
W_POINTS = (5, 10, 15, 20)
SNAPSHOT_SCHEMA = "r1_d3_snapshot/v1"
REQUIRED_SNAPSHOT = ("schema", "stage", "arm", "node", "repetition", "instance_id", "w",
                     "incumbent_config", "start_config", "config_sha256")


class AuditStop(RuntimeError):
    """A pre-declared STOP: the audit record is not the run that was authorised."""


@dataclass(frozen=True)
class Run:
    seed: int
    metric: float
    run_sha256: str
    cached: bool = False


Runner = Callable[[str, Mapping[str, str], list[int]], list[Run]]
"""``(node, config files, seeds) -> runs``; every requested seed must come back exactly once."""


# ---------------------------------------------------------------------------
# seeds, snapshots, hashing
# ---------------------------------------------------------------------------

def audit_seeds(instance_seed: int) -> tuple[int, ...]:
    """The instance's ten audit seeds (pre-declaration §4, §7).

    The frozen pre-declaration excludes Y audits of the engineering smoke instances
    (seeds 6301-6302), so those seeds are refused here rather than given an audit block.
    """
    s = int(instance_seed)
    if not 6201 <= s <= 6218:
        raise AuditStop(f"instance seed {s} is outside 6201-6218")
    return tuple(AUDIT_SEED_BASE + 10 * (s - 6201) + k for k in range(1, K + 1))


def _sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_snapshot(path: Path, *, stage: str | None = None, arm: str | None = None, node: str | None = None,
                  repetition: int | None = None, instance_id: str | None = None) -> dict[str, Any]:
    """Read and validate one snapshot; a field mismatch or a self-hash failure is a STOP."""
    payload = json.loads(Path(path).read_text())
    missing = [k for k in REQUIRED_SNAPSHOT if k not in payload]
    if missing:
        raise AuditStop(f"{path}: snapshot misses {missing}")
    if payload["schema"] != SNAPSHOT_SCHEMA:
        raise AuditStop(f"{path}: unknown snapshot schema {payload['schema']!r}")
    for key, want in (("stage", stage), ("arm", arm), ("node", node), ("instance_id", instance_id)):
        if want is not None and str(payload[key]) != str(want):
            raise AuditStop(f"{path}: {key} {payload[key]!r} differs from {want!r}")
    if repetition is not None and int(payload["repetition"]) != int(repetition):
        raise AuditStop(f"{path}: repetition {payload['repetition']!r} differs from {repetition!r}")
    contents = payload["incumbent_config"]
    if not isinstance(contents, Mapping) or not contents:
        raise AuditStop(f"{path}: incumbent_config must be a non-empty file map")
    if config_sha256(contents) != payload["config_sha256"]:
        raise AuditStop(f"{path}: config_sha256 does not hash the incumbent contents")
    start = payload["start_config"]
    if not isinstance(start, Mapping) or not start:
        raise AuditStop(f"{path}: start_config must be a non-empty file map")
    return payload


# ---------------------------------------------------------------------------
# cache
# ---------------------------------------------------------------------------

class Cache:
    """Append-only JSONL cache keyed by (node, config_sha256, audit_seed)."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self.rows: dict[tuple[str, str, int], Run] = {}
        if self.path is not None and self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                run = Run(seed=int(row["seed"]), metric=_check_metric(row["metric"], "cache"),
                          run_sha256=str(row["run_sha256"]), cached=True)
                if not run.run_sha256:
                    raise AuditStop("a cache row without a run_sha256 is refused")
                key = (str(row["node"]), str(row["config_sha256"]), run.seed)
                if key in self.rows and self.rows[key].run_sha256 != run.run_sha256:
                    raise AuditStop(f"cache key {key} has two different run_sha256 values")
                self.rows[key] = run

    def get(self, node: str, sha: str, seed: int) -> Run | None:
        row = self.rows.get((node, sha, int(seed)))
        return replace(row, cached=True) if row is not None else None

    def put(self, node: str, sha: str, run: Run) -> Run:
        if not run.run_sha256:
            raise AuditStop("every cached run needs its run_sha256")
        key = (node, sha, int(run.seed))
        self.rows[key] = run
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"node": node, "config_sha256": sha, "seed": run.seed,
                                     "metric": run.metric, "run_sha256": run.run_sha256}) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        return run


def _check_metric(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise AuditStop(f"{what}: a non-finite or missing metric is a STOP")
    return float(value)


# ---------------------------------------------------------------------------
# one configuration
# ---------------------------------------------------------------------------

def audit_config(node: str, files: Mapping[str, str], seeds: tuple[int, ...], runner: Runner,
                 cache: Cache | None) -> dict[int, Run]:
    """Audit one configuration on ``seeds``, using the cache for every hit."""
    wanted = [int(s) for s in seeds]
    out: dict[int, Run] = {}
    missing: list[int] = []
    for seed in wanted:
        hit = cache.get(node, config_sha256(files), seed) if cache is not None else None
        if hit is not None:
            out[seed] = hit
        else:
            missing.append(seed)
    if missing:
        rows = list(runner(node, files, missing))
        by_seed = {int(r.seed): r for r in rows}
        if sorted(by_seed) != sorted(missing) or len(rows) != len(missing):
            raise AuditStop(f"the runner returned {sorted(by_seed)} for the requested seeds {sorted(missing)}")
        for seed in missing:
            run = by_seed[seed]
            _check_metric(run.metric, f"{node} seed {seed}")
            if not run.run_sha256:
                raise AuditStop(f"{node} seed {seed}: the run has no sha256 (a missing provenance is a STOP)")
            out[seed] = cache.put(node, config_sha256(files), run) if cache is not None else run
    return out


# ---------------------------------------------------------------------------
# one campaign
# ---------------------------------------------------------------------------

def _row_head(snapshot: Mapping[str, Any], sigma_node: float) -> dict[str, Any]:
    return {
        "schema": ROW_SCHEMA, "stage": str(snapshot["stage"]), "arm": str(snapshot["arm"]),
        "node": str(snapshot["node"]), "repetition": int(snapshot["repetition"]),
        "instance_id": str(snapshot["instance_id"]), "sigma_node": float(sigma_node),
    }


def audit_snapshot(snapshot: Mapping[str, Any], *, sigma_node: float, runner: Runner,
                   cache: Cache | None) -> dict[str, Any]:
    """Audit one snapshot's incumbent against its start configuration on the K audit seeds."""
    instance_id = str(snapshot["instance_id"])
    instance_seed = int(instance_id.rsplit("__s", 1)[1])
    seeds = audit_seeds(instance_seed)
    w = int(snapshot["w"])
    incumbent = dict(snapshot["incumbent_config"])
    start = dict(snapshot["start_config"])
    inc_sha, start_sha = config_sha256(incumbent), config_sha256(start)
    if "worker_runs" in snapshot and int(snapshot["worker_runs"]) != w:
        raise AuditStop(f"{instance_id}: snapshot w={w} but worker_runs={snapshot['worker_runs']}")
    row = {**_row_head(snapshot, sigma_node), "w": w, "w_actual": int(snapshot.get("w_actual", w)),
           "ended_on": snapshot.get("ended_on"), "final": bool(snapshot.get("final", False)),
           "config_sha256": inc_sha, "start_config_sha256": start_sha, "k": K, "seeds": list(seeds),
           "runs": [], "y_raw": 0.0, "Y": 0.0, "cache": {"incumbent_hits": 0, "start_hits": 0},
           "audited": False}
    if w == 0 or inc_sha == start_sha:
        # Pre-declaration §7: no audit runs and Y = 0 by rule.
        row["rule"] = "w=0" if w == 0 else "incumbent equals start"
        return row
    inc = audit_config(str(snapshot["node"]), incumbent, seeds, runner, cache)
    st = audit_config(str(snapshot["node"]), start, seeds, runner, cache)
    deltas = []
    for seed in seeds:
        a, b = inc[seed], st[seed]
        delta = a.metric - b.metric
        deltas.append(delta)
        row["runs"].append({
            "seed": seed,
            "incumbent": {"metric": a.metric, "run_sha256": a.run_sha256, "cached": a.cached},
            "start": {"metric": b.metric, "run_sha256": b.run_sha256, "cached": b.cached},
            "delta": delta,
        })
    row["cache"] = {"incumbent_hits": sum(1 for s in seeds if inc[s].cached),
                    "start_hits": sum(1 for s in seeds if st[s].cached)}
    row["y_raw"] = math.fsum(deltas) / K
    row["Y"] = row["y_raw"] / float(sigma_node)
    row["audited"] = True
    return row


def _write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    text = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False) + "\n"
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _campaign_id(row: Mapping[str, Any]) -> str:
    instance = str(row["instance_id"])
    stage = {"a": "D.3a", "b": "D.3b"}.get(str(row["stage"]), str(row["stage"]))
    return f"{stage}__{row['arm']}__{instance}__r{int(row['repetition'])}"


def g7_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The exact six-key audit rows G7's ``build_table`` accepts.

    ``Y_*.jsonl`` keep the full audit record; this projection is the table input: final, every
    reached w point and every keep (``keep_run``).  A ``missing_w`` row is omitted, as G7
    expects no audit for a point the campaign did not reach.
    """
    rows: list[dict[str, Any]] = []

    def add(point: str, row: Mapping[str, Any], keep_run: int | None = None) -> None:
        rows.append({
            "schema": ROW_SCHEMA, "campaign_id": _campaign_id(row), "point": point,
            "keep_run": keep_run, "config_sha256": str(row["config_sha256"]),
            "y_raw": float(row["y_raw"]),
        })

    # G7 forbids any audit row for a campaign with no charged run (§10; build_row's runs==0
    # branch expects an empty audit).  The descriptive Y_final.jsonl row is still written.
    if int(result["final"].get("w", 0)) != 0:
        add("final", result["final"])
    for row in result["w"]:
        if not row.get("missing_w"):
            add(str(row["w"]), row)
    for row in result.get("keep", []):
        add("keep", row, int(row["keep_run"]))
    return rows


def audit_campaign(campaign_dir: Path | str, out_dir: Path | str, *, sigma_node: float, runner: Runner,
                   cache: Cache | None = None) -> dict[str, Any]:
    """Audit one campaign directory and write its Y_final / Y_w rows.

    ``out_dir`` is the audit output root; the campaign's records are written below
    ``<out>/<stage>/<arm>/r<rep>/w<w>/<instance>.json``.  Returns the two row lists.
    """
    cdir = Path(campaign_dir)
    snaps = cdir / "snapshots"
    final_path = snaps / "final.json"
    if not final_path.is_file():
        raise AuditStop(f"{cdir}: no snapshots/final.json (the campaign is not sealed)")
    bare = final_path
    final = load_snapshot(bare)
    stage, arm, node = str(final["stage"]), str(final["arm"]), str(final["node"])
    rep, instance = int(final["repetition"]), str(final["instance_id"])
    if Path(cdir).name != instance:
        raise AuditStop(f"{cdir}: directory name differs from instance_id {instance!r}")
    final = load_snapshot(bare, stage=stage, arm=arm, node=node, repetition=rep, instance_id=instance)
    if not math.isfinite(float(sigma_node)) or float(sigma_node) <= 0:
        raise AuditStop("sigma_node must be a positive finite number")
    start_sha = config_sha256(final["start_config"])
    final_w = int(final["w"])

    out = Path(out_dir)
    rows_w: list[dict[str, Any]] = []
    written: dict[int, Path] = {}
    for w in W_POINTS:
        path = snaps / f"w{w}.json"
        if not path.is_file():
            rows_w.append({**_row_head(final, sigma_node), "w": w, "w_actual": None, "missing_w": True,
                           "audited": False, "y_raw": None, "Y": None})
            continue
        snap = load_snapshot(path, stage=stage, arm=arm, node=node, repetition=rep, instance_id=instance)
        if int(snap["w"]) != w:
            raise AuditStop(f"{path}: w={snap['w']} but the file is w{w}.json")
        if w > final_w:
            raise AuditStop(f"{path}: w={w} is above the campaign's final w={final_w}")
        if config_sha256(snap["start_config"]) != start_sha:
            raise AuditStop(f"{path}: start_config differs from final.json's start configuration")
        row = audit_snapshot(snap, sigma_node=sigma_node, runner=runner, cache=cache)
        target = out / stage / arm / f"r{rep}" / f"w{w}" / f"{instance}.json"
        if target.exists():
            raise AuditStop(f"{target} exists: a rerun takes a new output directory")
        row["record_sha256"] = _write_json(target, row)
        written[w] = target
        rows_w.append(row)

    by_w = {row["w"]: row for row in rows_w}
    if final_w in written and config_sha256(final["incumbent_config"]) == by_w[final_w]["config_sha256"]:
        # Decide the alias before any audit: never run the same configuration a second time.
        import copy
        final_row = copy.deepcopy(by_w[final_w])
        final_row["ended_on"] = final.get("ended_on")
        final_row["final"] = True
        final_row["primary"] = True
        final_row["alias_of_w"] = final_w
        final_row["audit_record"] = str(written[final_w].relative_to(out))
    else:
        final_row = audit_snapshot(final, sigma_node=sigma_node, runner=runner, cache=cache)
        final_row["primary"] = True
        if final_w == 0:
            # Design §3.3: a w=0 final has no audit path; Y=0 by rule.
            final_row["audit_record"] = None
        else:
            # The final incumbent can differ from the pre-decision w snapshot (a keep on the last
            # run), so a distinct final record is written under final/w<w>/ rather than overwriting
            # the descriptive w record.
            target = out / stage / arm / f"r{rep}" / "final" / f"w{final_w}" / f"{instance}.json"
            if target.exists():
                raise AuditStop(f"{target} exists: a rerun takes a new output directory")
            final_row["record_sha256"] = _write_json(target, final_row)
            final_row["audit_record"] = str(target.relative_to(out))

    rows_keep: list[dict[str, Any]] = []
    keep_dir = cdir / "keeps"
    if keep_dir.is_dir():
        for path in sorted(keep_dir.glob("keep-*.json"),
                           key=lambda p: int(p.stem.rsplit("-", 1)[1])):
            payload = json.loads(path.read_text(encoding="utf-8"))
            run, files = int(payload["keep_run"]), dict(payload["files"])
            sha = config_sha256(files)
            if sha != str(payload["config_sha256"]):
                raise AuditStop(f"{path}: the keep configuration sha256 differs from its record")
            snapshot = {
                "schema": SNAPSHOT_SCHEMA, "stage": stage, "arm": arm, "node": node,
                "repetition": rep, "instance_id": instance, "w": run,
                "incumbent_config": files, "start_config": final["start_config"],
                "worker_runs": run, "final": False,
            }
            row = audit_snapshot(snapshot, sigma_node=sigma_node, runner=runner, cache=cache)
            row["point"] = "keep"
            row["keep_run"] = run
            target = out / stage / arm / f"r{rep}" / "keep" / str(run) / f"{instance}.json"
            if target.exists():
                raise AuditStop(f"{target} exists: a rerun takes a new output directory")
            row["record_sha256"] = _write_json(target, row)
            rows_keep.append(row)

    y_final = out / "Y_final.jsonl"
    y_w = out / "Y_w.jsonl"
    y_keep = out / "Y_keep.jsonl"
    y_final.parent.mkdir(parents=True, exist_ok=True)
    with y_final.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(final_row, sort_keys=True) + "\n")
    with y_w.open("a", encoding="utf-8") as fh:
        for row in rows_w:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    with y_keep.open("a", encoding="utf-8") as fh:
        for row in rows_keep:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    result = {"final": final_row, "w": rows_w, "keep": rows_keep}
    g7 = g7_rows(result)
    with (out / "g7_rows.jsonl").open("a", encoding="utf-8") as fh:
        for row in g7:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    _sums(out)
    return result


def _sums(root: Path) -> None:
    entries = {}
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.name in ("SHA256SUMS", "SHA256SUMS.tmp"):
            continue
        entries[path.relative_to(root).as_posix()] = _sha256_file(path)
    text = "".join(f"{digest}  {rel}\n" for rel, digest in sorted(entries.items()))
    (Path(root) / "SHA256SUMS").write_text(text, encoding="utf-8")


def audit_chunk(chunk_dir: Path | str, out_dir: Path | str, *, sigma_node: float, runner: Runner,
                cache: Cache | None = None) -> list[dict[str, Any]]:
    """Audit every campaign in one G1 chunk (``<chunk>/campaigns/<instance>/``), sorted by instance."""
    campaigns = Path(chunk_dir) / "campaigns"
    if not campaigns.is_dir():
        raise AuditStop(f"{chunk_dir}: no campaigns/ directory")
    out = []
    for cdir in sorted(p for p in campaigns.iterdir() if p.is_dir()):
        out.append(audit_campaign(cdir, out_dir, sigma_node=sigma_node, runner=runner, cache=cache))
    return out


# ---------------------------------------------------------------------------
# the production runner (deepthought; no label)
# ---------------------------------------------------------------------------

def harness_runner(tmp: Path | str, *, prepare_cache=None, expected_worker: dict | None = None) -> Runner:
    """The default runner: ``r1.c3.audit.run_config`` one configuration at a time.

    ``run_config`` copies the harness node, overwrites the editable files with the configuration's texts and runs the
    node's own train command at each joint seed.  It reads no label or evaluation value.
    """
    from r1.c3.audit import run_config

    def runner(node: str, files: Mapping[str, str], seeds: list[int]) -> list[Run]:
        runner_kwargs = {}
        if prepare_cache is not None:
            runner_kwargs["prepare_cache"] = prepare_cache
        if expected_worker is not None:
            runner_kwargs["journal_identity"] = {"expected_worker": expected_worker}
        rows = run_config(node, dict(files), [int(s) for s in seeds], str(tmp),
                          stop_on_failure=True, stop_on_invalid=True, **runner_kwargs)
        out = []
        for row in rows:
            metric = row.get("metric")
            if not row.get("success"):
                raise AuditStop(f"{node}: audit run failed at seed {row.get('seed')}: {row.get('failure')!r}")
            if row.get("changed_files") is not False:
                raise AuditStop(f"{node}: audit run changed editable files at seed {row.get('seed')}")
            out.append(Run(seed=int(row["seed"]), metric=_check_metric(metric, f"{node} {row.get('seed')}"),
                           run_sha256=_sha256_json(row)))
        return out

    return runner
