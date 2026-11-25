#!/usr/bin/env python3
"""Fill the 19 ``TODO_VERIFY_ON_HOST`` values of the HTCondor host config from a host-side input file (F7 of the P.4
cluster test plan ``docs/r1/reports/trackp_p4_runner_20261122/P4_CLUSTER_TEST_PLAN_20261124.md``, its §5.2, T3 and
§6 step 4). ENGINEERING_ONLY; AI-assisted (Claude).

``p4_fill_host_config.py --template`` prints the input form: every value the code forces is written in, the others
read ``FILL: …`` (which this script refuses). The cluster agent copies it, fills and confirms every value on the host,
and commits the filled input with the host-config fill commit (for example as
``docs/r1/reports/trackp_p4_cluster_<YYYYMMDD>/host_fill.json``).

``p4_fill_host_config.py <values.json> [--config <host config>] [--dry-run]``:

* lists the host config's placeholders with the rule ``trackp.py --check-config`` uses (``run.placeholders``: every
  value starting with ``TODO_VERIFY``; ``comment`` keys ignored), and requires exactly the 19 known paths
  (``EXPECTED``): a config that is already partly or wholly filled, or holds another placeholder, is refused;
* requires the input ``{"schema": "trackp_p4_host_fill/1", "values": {<dotted path>: <value>}}`` to name exactly those
  19 paths (a partial fill or an unknown path is refused), each value a non-empty string that is not a placeholder
  (``TODO…``, ``FILL…``, ``PENDING…``, ``TBD…``) and valid under its rule:

  - **forced** (``FIXED``): the six local paths of the P.4 arms are ``models/<registry key>`` (what
    ``p4_lib.check_local_paths`` requires: the job stages there); ``gpu.name`` ``NVIDIA H200``;
    ``gpu.compute_capability`` ``9.0``; ``venv.path`` ``/opt/r1/envs/trackp`` (``p4_lib.ENV3_PYTHON``); ``hf_home``
    ``hf`` and ``models_dir`` ``models`` (the job's ``HF_HOME`` and staging directory, ``p4_lib.offline_env`` and
    ``p4_lib.stage``); ``runs_dir`` ``out`` (the trackp GPU lease writes ``<runs_dir>/gpu_lease_log.jsonl``, which then
    goes into ``out.tar``);
  - **job-relative path** (``work_dir``, ``gpu.lock_path`` and the four bases P.4 never stages, ``laya``,
    ``startlux-0.8b``, ``startlux-2b``, ``startlux-4b``; their values are the coordinating chat's choice, F7): a
    relative path inside the job directory (no absolute path, ``~``, ``..`` or empty segment);
  - ``venv.causal_conv1d``: free text naming version ``1.7.0`` and ``R1-TRACKP-IMAGE-V22-B``;

* replaces exactly those values, checks that nothing else changed, writes the file in the repository's JSON layout
  (indent 1, ASCII escapes, final newline; the file's other bytes are unchanged), and re-checks: no placeholder left,
  every P.4 arm's local paths pass ``p4_lib.check_local_paths``. It prints the new file sha256 (``sha256sum``; the
  value for ``host_config.sha256`` in the spec and the probe spec, and the note's ``host_config:``; not the
  ``config_digest`` that ``--check-config`` prints). ``--dry-run`` does everything except the write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import p4_lib as lib  # noqa: E402

SCHEMA = "trackp_p4_host_fill/1"
FIXED = {"gpu.name": lib.GPU_MODEL, "gpu.compute_capability": "9.0", "venv.path": str(Path(lib.ENV3_PYTHON).parents[1]),
         "hf_home": "hf", "models_dir": "models", "runs_dir": "out"}
for _arm, (_adapter, _base) in lib.ARMS.items():
    FIXED[f"bases.{_arm}.local_path"] = f"models/{_base}"
    if _adapter:
        FIXED[f"bases.{_arm}.adapter_local_path"] = f"models/{_adapter}"
UNUSED_BASES = ("laya", "startlux-0.8b", "startlux-2b", "startlux-4b")
RELATIVE = ("work_dir", "gpu.lock_path", *(f"bases.{b}.local_path" for b in UNUSED_BASES))
FREE_TEXT = {"venv.causal_conv1d": ("1.7.0", "R1-TRACKP-IMAGE-V22-B")}
EXPECTED = frozenset(FIXED) | frozenset(RELATIVE) | frozenset(FREE_TEXT)
HINTS = {"work_dir": "FILL: a job-relative directory (suggested '.')",
         "gpu.lock_path": "FILL: a job-relative lock file (suggested 'gpu0.lock')",
         "venv.causal_conv1d": "FILL: e.g. '1.7.0 built from source in image v2.2, TORCH_CUDA_ARCH_LIST 8.0;8.9;9.0, "
                               "build log sha256 <…> (R1-TRACKP-IMAGE-V22-B)', confirmed by T1 and T2",
         **{f"bases.{b}.local_path": f"FILL: the chat's value for a base P.4 never stages (F7; suggested 'models/{b}')"
            for b in UNUSED_BASES}}


class FillStop(lib.Stop):
    pass


def _placeholders(cfg: dict) -> list[str]:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from r1.c3.train import run as R  # noqa: PLC0415 - the rule trackp.py --check-config applies
    return R.placeholders(cfg)


def _paths(obj, prefix: tuple = ()) -> dict:
    """dotted path (as ``run.placeholders`` spells it) -> key tuple, for every leaf of dictionaries."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_paths(v, (*prefix, str(k))))
    else:
        out[".".join(prefix)] = prefix
    return out


def _relative_ok(value: str) -> bool:
    if value == ".":
        return True
    parts = value.split("/")
    return not value.startswith(("/", "~")) and "\\" not in value and all(p not in ("", ".", "..") for p in parts) \
        and all(c.isalnum() or c in "._-/" for c in value)


def check_value(path: str, value) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FillStop(f"STOP: {path}: a non-empty string without surrounding blanks is required")
    if value.startswith("TODO_VERIFY") or lib._placeholder(value):
        raise FillStop(f"STOP: {path}: {value!r} is still a placeholder")
    if path in FIXED and value != FIXED[path]:
        raise FillStop(f"STOP: {path} must be {FIXED[path]!r} (forced by the job), not {value!r}")
    if path in RELATIVE and not _relative_ok(value):
        raise FillStop(f"STOP: {path}: {value!r} is not a relative path inside the job directory")
    if path in FREE_TEXT and not all(n in value for n in FREE_TEXT[path]):
        raise FillStop(f"STOP: {path} must name {' and '.join(FREE_TEXT[path])}")


def template() -> dict:
    return {"schema": SCHEMA, "comment": "Host-side input of r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py; "
                                         "every value confirmed on the host by the cluster agent (§5.2 of the P.4 "
                                         "cluster test plan); the FILL values must be replaced.",
            "values": {p: FIXED.get(p, HINTS.get(p, "FILL")) for p in sorted(EXPECTED)}}


def fill(values_path: Path, config: Path, *, dry_run: bool = False) -> dict:
    raw = Path(config).read_bytes()
    cfg = json.loads(raw)
    want = set(_placeholders(cfg))
    if want != EXPECTED:
        raise FillStop(f"STOP: {config} must hold exactly the {len(EXPECTED)} known TODO_VERIFY_ON_HOST values; "
                       f"missing {sorted(EXPECTED - want)}, other {sorted(want - EXPECTED)} (no partial fill)")
    doc = json.loads(Path(values_path).read_bytes())
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not isinstance(doc.get("values"), dict):
        raise FillStop(f"STOP: {values_path} must be {{'schema': '{SCHEMA}', 'values': {{<path>: <value>}}}}")
    given = doc["values"]
    if set(given) != EXPECTED:
        raise FillStop(f"STOP: the input must fill exactly the {len(EXPECTED)} placeholders; missing "
                       f"{sorted(EXPECTED - set(given))}, unknown {sorted(set(given) - EXPECTED)} (no partial fill)")
    for path in sorted(given):
        check_value(path, given[path])
    keys = _paths(cfg)
    if len(keys) != len({v for v in keys.values()}) or not EXPECTED <= set(keys):
        raise FillStop("STOP: the host config's dotted paths are ambiguous")
    new = json.loads(raw)
    for path, value in given.items():
        *parent, leaf = keys[path]
        node = new
        for k in parent:
            node = node[k]
        node[leaf] = value
    text = (json.dumps(new, indent=1, ensure_ascii=True) + "\n").encode()
    back = json.loads(text)                               # nothing else changed: put the placeholders back
    for path in given:
        *parent, leaf = keys[path]
        node, old = back, cfg
        for k in parent:
            node, old = node[k], old[k]
        node[leaf] = old[leaf]
    if back != cfg:
        raise FillStop("STOP: the fill would change more than the placeholders")
    left = _placeholders(json.loads(text))
    if left:
        raise FillStop(f"STOP: placeholders left after the fill: {left}")
    with tempfile.TemporaryDirectory() as tmp:            # p4_lib.check_local_paths reads <clone>/<HOST_CONFIG>
        clone = Path(tmp)
        (clone / lib.HOST_CONFIG).parent.mkdir(parents=True)
        (clone / lib.HOST_CONFIG).write_bytes(text)
        job = Path("/nonexistent/condor/execute/dir_0")
        local = {arm: lib.check_local_paths(arm, clone, job) for arm in lib.ARMS}
    if not dry_run:
        tmp_out = Path(config).with_name(Path(config).name + ".fill-tmp")
        tmp_out.write_bytes(text)
        shutil.move(str(tmp_out), str(config))
    return {"config": str(config), "written": not dry_run, "filled": len(given),
            "previous_sha256": hashlib.sha256(raw).hexdigest(), "sha256": hashlib.sha256(text).hexdigest(),
            "placeholders_left": left, "local_paths": local,
            "values_sha256": hashlib.sha256(Path(values_path).read_bytes()).hexdigest()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("values", nargs="?", type=Path, help="the host-side input file")
    ap.add_argument("--config", type=Path, default=REPO_ROOT / lib.HOST_CONFIG)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--template", action="store_true", help="print the input form and exit")
    a = ap.parse_args(argv)
    if a.template:
        print(json.dumps(template(), indent=1))
        return 0
    if a.values is None:
        ap.error("the input file is required (or --template)")
    try:
        print(json.dumps(fill(a.values, a.config, dry_run=a.dry_run), indent=1))
    except (lib.Stop, ValueError, OSError) as exc:
        print(str(exc) if str(exc).startswith("STOP") else f"STOP: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
