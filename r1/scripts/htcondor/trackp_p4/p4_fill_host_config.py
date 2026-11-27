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

**Per host class (R1-HOST-FREE).** Everything above is the ``nemo2_h200`` class (``trackp_p4_host_fill/1``, its 19
paths, unchanged). The other classes of ``p4_lib.HOST_CLASSES`` fill their own host config from an input of schema
``trackp_p4_host_fill/2`` that names the class (``{"schema": "trackp_p4_host_fill/2", "host_class": <class>,
"values": {...}}``); ``--template --host-class <class>`` prints its form and ``--host-class`` (optional; it must agree
with the input) picks the default config. The ``ada_rtx6000`` class (``r1/scripts/configs/trackp_ada_v1.json``, filled
from the compute agent's survey of Ada) has 26 values:

  - **forced**: as for H200 (the six local paths, ``venv.path``, ``hf_home``, ``models_dir``, ``runs_dir``) with
    ``gpu.name`` ``NVIDIA RTX 6000 Ada Generation`` and ``gpu.compute_capability`` ``8.9``, and ``direct.ssh_alias``
    ``experiment_zhixu`` (COMPUTE.md);
  - **job-relative path** and **free text**: as for H200 (``work_dir``, ``gpu.lock_path``, the four unused bases;
    ``venv.causal_conv1d``);
  - **host values of the direct launch** (read by ``p4_render_jdl.render_direct`` into the stage descriptor, then by
    ``p4_direct.py`` on the host): ``direct.container_runtime`` ``apptainer`` or ``docker`` (anything else is refused);
    ``direct.work_root`` (the root of the fresh job directories) and ``direct.lock_dir`` (the host's GPU lease files
    ``gpu<N>.lock``), each an absolute path or one under ``~/`` without ``..``; ``direct.hostname`` (what ``hostname``
    prints on the host, e.g. ``ucrtasl``); ``direct.shm_size`` (docker's ``--shm-size``, e.g. ``16g``);
    ``direct.min_free_mib`` (the free memory in MiB a job needs on its card, a positive integer: the launcher checks
    free memory, not an empty card, R1-CARD-SHARE (1)).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import p4_lib as lib  # noqa: E402

SCHEMA = "trackp_p4_host_fill/1"                 # the nemo2_h200 class (unchanged)
SCHEMA_V2 = "trackp_p4_host_fill/2"              # any class, named in the input
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


ABSOLUTE: tuple = ()                             # nemo2_h200 has none; see CLASS_RULES
CHOICE: dict = {}
PATTERN: dict = {}
ADA_FIXED = {**{k: v for k, v in FIXED.items() if k not in ("gpu.name", "gpu.compute_capability")},
             "gpu.name": lib.HOST_CLASSES["ada_rtx6000"]["gpu_name"],
             "gpu.compute_capability": lib.HOST_CLASSES["ada_rtx6000"]["compute_capability"],
             "direct.ssh_alias": "experiment_zhixu"}
ADA_CHOICE = {"direct.container_runtime": ("apptainer", "docker")}
ADA_ABSOLUTE = ("direct.work_root", "direct.lock_dir")
ADA_PATTERN = {"direct.hostname": r"^[A-Za-z0-9][A-Za-z0-9.-]*$", "direct.shm_size": r"^[1-9][0-9]*[mg]$",
               "direct.min_free_mib": r"^[1-9][0-9]*$"}
ADA_HINTS = {**HINTS,
             "direct.container_runtime": "FILL: 'apptainer' or 'docker', whichever the survey shows usable by the "
                                         "account without sudo (docker needs the docker group; apptainer needs --nvccli)",
             "direct.work_root": "FILL: an absolute directory for the fresh job directories, e.g. "
                                 "'/data1/dowling/r1_trackp_p4/jobs'",
             "direct.lock_dir": "FILL: the host's GPU lease directory (files gpu<N>.lock), e.g. '~/r1_locks'",
             "direct.hostname": "FILL: what `hostname` prints on the host (COMPUTE.md: ucrtasl)",
             "direct.shm_size": "FILL: docker --shm-size, e.g. '16g'",
             "direct.min_free_mib": "FILL: MiB a job needs free on its card (R1-CARD-SHARE (1)); before the Ada probe "
                                    "the whole card, e.g. '46000'; after it, the probe's peak memory with headroom"}
CLASS_RULES = {
    "nemo2_h200": {"config": lib.HOST_CONFIG, "fixed": FIXED, "relative": RELATIVE, "free_text": FREE_TEXT,
                   "choice": CHOICE, "absolute": ABSOLUTE, "pattern": PATTERN, "hints": HINTS},
    "ada_rtx6000": {"config": lib.ADA_HOST_CONFIG, "fixed": ADA_FIXED, "relative": RELATIVE, "free_text": FREE_TEXT,
                    "choice": ADA_CHOICE, "absolute": ADA_ABSOLUTE, "pattern": ADA_PATTERN, "hints": ADA_HINTS},
}
assert set(CLASS_RULES) == set(lib.HOST_CLASSES)


def expected(host_class: str = "nemo2_h200") -> frozenset:
    """The dotted paths the class's host config holds as placeholders (``EXPECTED`` for nemo2_h200)."""
    r = CLASS_RULES[host_class]
    return frozenset(r["fixed"]) | frozenset(r["relative"]) | frozenset(r["free_text"]) | frozenset(r["choice"]) | \
        frozenset(r["absolute"]) | frozenset(r["pattern"])


assert expected("nemo2_h200") == EXPECTED and len(EXPECTED) == 19


class FillStop(lib.Stop):
    pass


def _placeholders(cfg: dict) -> list[str]:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from r1.c3.train import run as R  # noqa: PLC0415 - the rule trackp.py --check-config applies
    return R.placeholders(cfg)


def _leaves(obj, prefix: tuple = ()) -> list[tuple[str, tuple]]:
    """(dotted path as ``run.placeholders`` spells it, key tuple) for every leaf of dictionaries."""
    if isinstance(obj, dict):
        return [x for k, v in obj.items() for x in _leaves(v, (*prefix, str(k)))]
    return [(".".join(prefix), prefix)]


def _paths(obj) -> dict:
    """dotted path -> key tuple; two leaves with the same dotted spelling (a key holding a dot can collide) is a STOP,
    since a dotted input path would then not name one value."""
    leaves = _leaves(obj)
    out = dict(leaves)
    if len(out) != len(leaves):
        dup = sorted({d for d, _ in leaves if sum(1 for e, _ in leaves if e == d) > 1})
        raise FillStop(f"STOP: the host config's dotted paths are ambiguous: {dup}")
    return out


def _relative_ok(value: str) -> bool:
    if value == ".":
        return True
    parts = value.split("/")
    return not value.startswith(("/", "~")) and "\\" not in value and all(p not in ("", ".", "..") for p in parts) \
        and all(c.isalnum() or c in "._-/" for c in value)


def _absolute_ok(value: str) -> bool:
    body = value[2:] if value.startswith("~/") else value[1:] if value.startswith("/") else None
    return bool(body) and all(p not in ("", ".", "..") for p in body.split("/")) and \
        all(c.isalnum() or c in "._-/" for c in body)


def check_value(path: str, value, host_class: str = "nemo2_h200") -> None:
    r = CLASS_RULES[host_class]
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FillStop(f"STOP: {path}: a non-empty string without surrounding blanks is required")
    if value.startswith("TODO_VERIFY") or lib._placeholder(value):
        raise FillStop(f"STOP: {path}: {value!r} is still a placeholder")
    if path in r["fixed"] and value != r["fixed"][path]:
        raise FillStop(f"STOP: {path} must be {r['fixed'][path]!r} (forced by the job), not {value!r}")
    if path in r["relative"] and not _relative_ok(value):
        raise FillStop(f"STOP: {path}: {value!r} is not a relative path inside the job directory")
    if path in r["free_text"] and not all(n in value for n in r["free_text"][path]):
        raise FillStop(f"STOP: {path} must name {' and '.join(r['free_text'][path])}")
    if path in r["choice"] and value not in r["choice"][path]:
        raise FillStop(f"STOP: {path} must be one of {r['choice'][path]} (the launcher refuses any other), not "
                       f"{value!r}")
    if path in r["absolute"] and not _absolute_ok(value):
        raise FillStop(f"STOP: {path}: {value!r} is not an absolute path (or one under ~/) without '..'")
    if path in r["pattern"] and not re.fullmatch(r["pattern"][path], value):
        raise FillStop(f"STOP: {path}: {value!r} does not match {r['pattern'][path]}")


def template(host_class: str = "nemo2_h200") -> dict:
    if host_class == "nemo2_h200":                  # the H200 form, unchanged
        return {"schema": SCHEMA, "comment": "Host-side input of r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py; "
                                             "every value confirmed on the host by the cluster agent (§5.2 of the P.4 "
                                             "cluster test plan); the FILL values must be replaced.",
                "values": {p: FIXED.get(p, HINTS.get(p, "FILL")) for p in sorted(EXPECTED)}}
    r = CLASS_RULES[host_class]
    return {"schema": SCHEMA_V2, "host_class": host_class,
            "comment": f"Host-side input of r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py for {host_class} "
                       f"({r['config']}); every value confirmed on the host by the compute agent's survey "
                       "(R1-HOST-FREE); the FILL values must be replaced.",
            "values": {p: r["fixed"].get(p, r["hints"].get(p, "FILL")) for p in sorted(expected(host_class))}}


def input_class(doc, values_path, host_class: str | None) -> str:
    """The host class an input fills: ``trackp_p4_host_fill/1`` is nemo2_h200; ``/2`` names its class. A
    ``host_class`` given on the command line must agree."""
    if not isinstance(doc, dict) or not isinstance(doc.get("values"), dict) or doc.get("schema") not in (SCHEMA,
                                                                                                         SCHEMA_V2):
        raise FillStop(f"STOP: {values_path} must be {{'schema': '{SCHEMA}', 'values': {{<path>: <value>}}}} (the "
                       f"nemo2_h200 class) or {{'schema': '{SCHEMA_V2}', 'host_class': <class>, 'values': ...}}")
    cls = "nemo2_h200" if doc["schema"] == SCHEMA else doc.get("host_class")
    if cls not in CLASS_RULES:
        raise FillStop(f"STOP: {values_path}: host_class must be one of {sorted(CLASS_RULES)}")
    if host_class is not None and host_class != cls:
        raise FillStop(f"STOP: --host-class {host_class} is not the input's class {cls}")
    return cls


def fill(values_path: Path, config: Path | None = None, *, dry_run: bool = False,
         host_class: str | None = None) -> dict:
    doc = json.loads(Path(values_path).read_bytes())
    cls = input_class(doc, values_path, host_class)
    rules = CLASS_RULES[cls]
    want_paths = expected(cls)
    config = Path(config) if config is not None else REPO_ROOT / rules["config"]
    raw = Path(config).read_bytes()
    cfg = json.loads(raw)
    want = set(_placeholders(cfg))
    if want != want_paths:
        raise FillStop(f"STOP: {config} must hold exactly the {len(want_paths)} known TODO_VERIFY_ON_HOST values; "
                       f"missing {sorted(want_paths - want)}, other {sorted(want - want_paths)} (no partial fill)")
    given = doc["values"]
    if set(given) != want_paths:
        raise FillStop(f"STOP: the input must fill exactly the {len(want_paths)} placeholders; missing "
                       f"{sorted(want_paths - set(given))}, unknown {sorted(set(given) - want_paths)} (no partial fill)")
    for path in sorted(given):
        check_value(path, given[path], cls)
    keys = _paths(cfg)
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
    with tempfile.TemporaryDirectory() as tmp:            # p4_lib.check_local_paths reads <clone>/<host config>
        clone = Path(tmp)
        (clone / rules["config"]).parent.mkdir(parents=True)
        (clone / rules["config"]).write_bytes(text)
        job = Path("/nonexistent/condor/execute/dir_0")
        local = {arm: lib.check_local_paths(arm, clone, job, host_config=rules["config"]) for arm in lib.ARMS}
    if not dry_run:
        tmp_out = Path(config).with_name(Path(config).name + ".fill-tmp")
        tmp_out.write_bytes(text)
        shutil.move(str(tmp_out), str(config))
    return {"config": str(config), "host_class": cls, "written": not dry_run, "filled": len(given),
            "previous_sha256": hashlib.sha256(raw).hexdigest(), "sha256": hashlib.sha256(text).hexdigest(),
            "placeholders_left": left, "local_paths": local,
            "values_sha256": hashlib.sha256(Path(values_path).read_bytes()).hexdigest()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("values", nargs="?", type=Path, help="the host-side input file")
    ap.add_argument("--config", type=Path, default=None, help="default: the input class's host config")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--template", action="store_true", help="print the input form and exit")
    ap.add_argument("--host-class", choices=sorted(CLASS_RULES), default=None,
                    help="the host class (R1-HOST-FREE); --template: the form to print (default nemo2_h200); a fill: "
                         "must agree with the input's class")
    a = ap.parse_args(argv)
    if a.template:
        print(json.dumps(template(a.host_class or "nemo2_h200"), indent=1))
        return 0
    if a.values is None:
        ap.error("the input file is required (or --template)")
    try:
        print(json.dumps(fill(a.values, a.config, dry_run=a.dry_run, host_class=a.host_class), indent=1))
    except (lib.Stop, ValueError, OSError) as exc:
        print(str(exc) if str(exc).startswith("STOP") else f"STOP: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
