#!/usr/bin/env python3
"""Offline readiness check of the OpenML data caches for the D21 common E1 run.

ENGINEERING_ONLY; AI-assisted (Claude). Not evidence; it fetches nothing.

For every OpenML node in the list it reproduces what E1 does before a run:
``r1.noise.e1_noise_floor._prepare_node`` copies the harness node directory
into a temporary directory (falling back to the L8 pilot cache only when the
node has **no** ``data_cache`` directory), then the node's own frozen loader
``benchmark._load_frame()`` (``fetch_openml(data_id, data_home=<copy>/data_cache)``)
is called with the network disabled in this process (socket connect and
sklearn's ``urlopen`` raise).  The copy is thrown away, so a failed load can
never modify the real cache.

Per node it prints the cache source, the loaded shape, the number of
categorical columns (by the template's dtype rule), the class counts, the
positive label the template scores for AUC (``LabelEncoder`` order, i.e.
``sorted(labels)[1]``) and the minority share, and compares them with
``r1.c3.features.NODE_INFO`` and the node config's D25 ``dataset_excluded``
(imputer must be excluded iff the data has no categorical column).

Exit status: 0 if every OpenML node loaded and matched, 1 otherwise.

Usage (paper repo root; AR_HARNESS_ROOT = the harness checkout E1 will use):
  python -m r1.noise.check_caches
  python -m r1.noise.check_caches --nodes openml_sonar openml_credit_g --json out.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import socket
import sys
import tempfile
from pathlib import Path

from r1.noise import e1_noise_floor as E1

HARNESS = E1.HARNESS

# The D21 common measurement (PLAN §10, 22 Oct): 5 original D21 nodes,
# credit_approval and the four candidates.
COMMON_NODES = (
    "digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc",
    "openml_credit_approval", "openml_credit_g", "openml_sonar", "openml_blood_transfusion",
    "openml_qsar_biodeg",
)


class NetworkDisabled(OSError):
    pass


def _disable_network() -> None:
    def refuse(*_args, **_kwargs):
        raise NetworkDisabled("network disabled by check_caches (offline check)")

    socket.socket.connect = refuse  # type: ignore[assignment]
    socket.socket.connect_ex = refuse  # type: ignore[assignment]
    socket.create_connection = refuse  # type: ignore[assignment]
    import sklearn.datasets._openml as openml_module

    openml_module.urlopen = refuse  # type: ignore[attr-defined]


def _has_files(path: Path) -> bool:
    return path.is_dir() and any(p.is_file() and not p.name.startswith(".") for p in path.rglob("*"))


def cache_source(node: str) -> tuple[str, Path | None]:
    """Which cache E1's _prepare_node would use, without copying anything."""
    own = HARNESS / "nodes" / node / "data_cache"
    if own.exists():
        # _prepare_node never falls back when the directory exists, even if empty.
        return ("node data_cache", own) if _has_files(own) else ("cache missing (node data_cache is empty)", None)
    pilot = HARNESS / E1.PILOT_DATA_CACHE.format(node=node)
    if _has_files(pilot):
        return "L8 pilot fallback", pilot
    return "cache missing (no node data_cache, no L8 pilot cache)", None


def _load_module(node_dir: Path):
    spec = importlib.util.spec_from_file_location(f"check_caches_{node_dir.name}", node_dir / "benchmark.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_node(node: str, tmp_root: Path) -> dict:
    from r1.c3.features import NODE_INFO

    row: dict = {"node": node}
    if not node.startswith("openml_"):
        row.update(status="skipped", reason="not an OpenML node (data generated or bundled with sklearn)")
        return row
    config_path = HARNESS / "configs" / "nodes" / f"{node}.yaml"
    if not config_path.is_file() or not (HARNESS / "nodes" / node).is_dir():
        row.update(status="not in harness", reason=f"no node config/directory in {HARNESS}")
        return row
    config = json.loads(config_path.read_text())
    row["dataset_id"] = config.get("dataset", {}).get("dataset_id")
    source, path = cache_source(node)
    row["cache_source"] = source
    row["cache_path"] = str(path) if path else None
    if path is None:
        row["status"] = "cache missing"
        return row
    work = Path(tempfile.mkdtemp(prefix=f"cc_{node}_", dir=tmp_root))
    try:
        node_dir = E1._prepare_node(node, work)
        module = _load_module(node_dir)
        if int(module.DATA_ID) != int(row["dataset_id"]):
            row.update(status="mismatch", reason=f"benchmark DATA_ID {module.DATA_ID} != config {row['dataset_id']}")
            return row
        try:
            x, y = module._load_frame()
        except Exception as exc:  # noqa: BLE001 - reported, never hidden
            row.update(status="load failed", reason=f"{type(exc).__name__}: {exc}")
            return row
    finally:
        shutil.rmtree(work, ignore_errors=True)
    counts = {str(k): int(v) for k, v in y.astype(str).value_counts().sort_index().items()}
    categorical = [c for c in x.columns if str(x[c].dtype) in {"category", "object", "bool"}]
    labels = sorted(counts)
    minority = min(counts.values()) / sum(counts.values())
    row.update(
        rows=int(x.shape[0]), features=int(x.shape[1]), categorical_columns=len(categorical),
        missing_values=int(x.isna().sum().sum()), target_name=str(y.name), class_counts=counts,
        positive_label=labels[1] if len(labels) == 2 else None, minority_share=round(minority, 4),
    )
    problems = []
    if len(labels) != 2:
        problems.append(f"target is not binary: {labels}")
    excluded = set(config.get("active_keys", {}).get("dataset_excluded", []))
    if bool(categorical) == ("imputer" in excluded):
        problems.append(f"D25: {len(categorical)} categorical columns but dataset_excluded={sorted(excluded)}")
    info = NODE_INFO.get(node)
    if info is None:
        problems.append("no NODE_INFO entry in r1.c3.features")
    else:
        for key, have in (("rows", row["rows"]), ("features", row["features"])):
            if info[key] != have:
                problems.append(f"NODE_INFO {key}={info[key]} but data has {have}")
        if abs(info["minority"] - minority) > 0.0015:
            problems.append(f"NODE_INFO minority={info['minority']} but data has {minority:.4f}")
    row["problems"] = problems
    row["status"] = "ok" if not problems else "loaded, metadata mismatch"
    return row


def _line(row: dict) -> str:
    head = f"{row['node']:<26} {row['status']}"
    if row["status"] == "skipped":
        return f"{head}: {row['reason']}"
    if "rows" not in row:
        extra = row.get("reason") or row.get("cache_source")
        return f"{head}  [id {row.get('dataset_id')}; {extra}]"
    text = (f"{head}  [id {row['dataset_id']}; {row['cache_source']}] shape {row['rows']} x {row['features']}, "
            f"categorical {row['categorical_columns']}, missing {row['missing_values']}, "
            f"classes {row['class_counts']}, positive '{row['positive_label']}', minority {row['minority_share']:.3f}")
    for problem in row.get("problems", []):
        text += f"\n{'':<27}! {problem}"
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nodes", nargs="+", default=list(COMMON_NODES))
    parser.add_argument("--json", default=None, help="Also write the rows to this JSON file.")
    args = parser.parse_args()

    _disable_network()
    import numpy
    import pandas
    import sklearn

    versions = {"python": platform.python_version(), "sklearn": sklearn.__version__,
                "numpy": numpy.__version__, "pandas": pandas.__version__}
    print(f"harness: {HARNESS}  versions: {versions}  (network disabled in this process)")
    rows = []
    with tempfile.TemporaryDirectory(prefix="check_caches_") as tmp:
        for node in args.nodes:
            row = check_node(node, Path(tmp))
            rows.append(row)
            print(_line(row))
    openml_rows = [r for r in rows if r["status"] != "skipped"]
    ready = [r["node"] for r in openml_rows if r["status"] == "ok"]
    print(f"ready: {len(ready)}/{len(openml_rows)} OpenML nodes")
    if args.json:
        Path(args.json).write_text(json.dumps({"harness": str(HARNESS), "versions": versions, "nodes": rows},
                                              indent=2) + "\n")
    return 0 if len(ready) == len(openml_rows) else 1


if __name__ == "__main__":
    sys.exit(main())
