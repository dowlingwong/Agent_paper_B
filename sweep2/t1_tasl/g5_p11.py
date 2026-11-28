"""Engineering-only P11 recipe for the G.5 TASL host checks."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import g5_tasl as S

SCHEMA = "g5_p11_smoke/v1"
LABEL = "ENGINEERING_ONLY"
RUN_ID = re.compile(r"g5-p11-[0-9]{8}T[0-9]{6}Z(?:-[a-z0-9]+)?")
NODES = ("mlab_imdb", "mlgym_breakout_minatar")
TEMPLATE = "sweep2/t1_tasl/g5_tasl_spec.json"
COPY_DIR = "docs/r1/reports/g5_rel_t1_g1b_20261126/seven"
COPY_REVIEW = "docs/r1/reviews/REL_T1_G1B_COPY_REVIEW_20261126.md"
FIXTURE = Path(__file__).with_name("g5_p11_fixture")
ISOLATION_LIB = "src/autoresearch/trackg/node_lib/ar_isolated.py"


def root() -> Path:
    return Path.home() / "r1_engineering" / "g5-p11"


def no_links(path: Path) -> None:
    if path.resolve() != path or any(p.is_symlink() for p in (path, *path.parents)):
        raise S.Stop(f"STOP: engineering path must be absolute and free of symlinks: {path}")


def run_keys(run_id: str) -> tuple[Path, Path]:
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise S.Stop("STOP: P11 run id must be g5-p11-YYYYMMDDThhmmssZ with an optional short suffix")
    base = root()
    no_links(base)
    return base, base / f"{run_id}.json"


def _recipe(path: Path, raw: dict) -> dict:
    run_id = raw.get("run_id")
    base, spec_file = run_keys(run_id)
    if raw != {"schema": SCHEMA, "label": LABEL, "run_id": run_id} or path.absolute() != spec_file:
        raise S.Stop(f"STOP: P11 requires the exact engineering recipe at {spec_file}")
    no_links(spec_file)
    if os.environ.get(S.ENABLE_ENV) == "1":
        raise S.Stop(f"STOP: unset {S.ENABLE_ENV} when running the P11 engineering smoke")
    data = json.loads((S.REPO_ROOT / TEMPLATE).read_bytes())
    data.update(raw)
    data["worker"].update(base=str(base / "scratch" / run_id), runs_root=str(base / "runs"),
                          sealed_root=str(base / "sealed"), extra_env={})
    data["tasl7_audits"].update(base=data["worker"]["base"], runs_root=data["worker"]["runs_root"],
                               node_extra_env={})
    data["proposer"].update(run_dir=str(base / "proposer"), sealed_root=str(base / "sealed-proposer"))
    data["key_values"]["cuda_ipc"]["mode"] = "acceptance"
    data["tasl2_cpus"]["replacements"] = {}
    data["nodes"] = [n | {"data_manifest_sha256": None, "env": "torch312",
                          "spec_path": f"{n['node']}/node.json", "node_dir": n["node"]}
                     for n in data["nodes"] if n["node"] in NODES]
    for name in ("runs", "sealed", "proposer", "sealed-proposer", "scratch", "kit", "table", "incoming"):
        tree = base / name / run_id
        no_links(tree)
        if tree.exists():
            for dirname, dirs, files in os.walk(tree):
                for child in (*dirs, *files):
                    if (Path(dirname) / child).is_symlink():
                        raise S.Stop(f"STOP: symlink in P11 run tree: {Path(dirname) / child}")
    return data


def load(path: Path, raw: dict) -> dict:
    return _recipe(path, raw)


def create(run_id: str) -> dict:
    base, target = run_keys(run_id)
    raw = {"schema": SCHEMA, "label": LABEL, "run_id": run_id}
    _recipe(target, raw)
    base.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as fh:
        json.dump(raw, fh, sort_keys=True)
        fh.write("\n")
    return {"label": LABEL, "spec": str(target), "sha256": S.L._sha_file(target)}


def _file_set(node: str, library: bytes) -> dict[str, bytes]:
    node_spec = json.loads((FIXTURE / "node.json").read_bytes())
    node_spec["name"] = node
    return {"node.json": S._derived_bytes(node_spec), "ar_isolated.py": library,
            **{p.name: p.read_bytes() for p in sorted(FIXTURE.glob("*.py"))}}


def materialize(spec: dict) -> Path:
    """Admit only the exact synthetic kit, with the real harness files left in their pinned checkout."""
    spec_family = spec["harness_families"]["G5-7"]
    harness, commit = Path(spec_family["harness_dir"]), spec_family["g5_commit"]
    library = S.G._sh(["git", "show", f"{commit}:{ISOLATION_LIB}"], cwd=harness)
    if library.returncode:
        raise S.Stop("STOP: P11 requires the pinned G.5 harness isolation library")
    kit = root() / "kit" / spec["run_id"]
    for node in spec["nodes"]:
        directory = kit / node["node"]
        files = _file_set(node["node"], library.stdout.encode())
        if not directory.exists():
            directory.mkdir(parents=True)
            for name, raw in files.items():
                with (directory / name).open("xb") as fh:
                    fh.write(raw)
        if set(p.name for p in directory.iterdir()) != files.keys() or any(
                not (directory / name).is_file() or (directory / name).read_bytes() != raw
                for name, raw in files.items()):
            raise S.Stop(f"STOP: the P11 synthetic kit differs from its recipe: {directory}")
        frozen = {name: S._sha_bytes(files[name]) for name in ("parent.py", "worker.py", "ar_isolated.py")}
        node.update(node_spec_sha256=S._sha_bytes(files["node.json"]),
                    committed_pin_sha256=S._sha_bytes(json.dumps(frozen, sort_keys=True).encode()))
    return kit


def context(spec: dict, node: str, host: str, read_main, list_main) -> dict:
    """Apply published host/copy checks without reading a label or a launch note."""
    fams = spec["harness_families"]
    fam = fams["G5-7"]
    checkout = S.family_checkout(spec, "G5-7")
    pins = S.PC.check(Path(fam["harness_dir"]), fam["g5_commit"], fams["G5-AR"]["g5_commit"])
    result = {"K": 10, "K_row": None, "host": host, "checkout": checkout, "pin_check": pins,
              "label": LABEL, "options": S.options(spec)}
    if host == S.AUDIT_HOST:
        result["crosshost_pass"] = S.check_crosshost_pass(spec, node, read_main, list_main)
        result["host_check"] = S.tasl7_host_check(spec, read_main)
    else:
        result["host_check"] = S.G.check_host_record(
            {"hostname": spec["worker"]["hostname"], "isolation_host_check": fam["isolation_host_check"]},
            S.PC.PIN_SEVEN, read_main)
    copy_record = read_main(f"{COPY_DIR}/COPY_RECORD.json")
    if copy_record is None:
        raise S.Stop("STOP: published seven-node G.1b copy record is missing")
    entry = spec["noise_floor"]["seven"]
    for dotted, value in json.loads(copy_record)["spec_fields"].items():
        prefix, key = dotted.rsplit(".", 1)
        if prefix != "noise_floor.seven":
            raise S.Stop("STOP: unexpected P11 noise-copy field")
        entry[key] = value
    entry["review"] = COPY_REVIEW
    reviewed_copy = S.check_seven_copy(spec, read_main)
    result["noise_precheck"] = S.noise_precheck(reviewed_copy, node, read_main)
    return result


def metrics(spec: dict) -> dict:
    import g5_job as J
    import g5_seal as SE

    return {"label": LABEL, "run_id": spec["run_id"], "W": spec["campaign"]["W"],
            "memory": S.options(spec)["G5-MEM"], "K": 10, "worker_gpu_hours": J.gpu_hours_consumed(spec),
            "proposer": SE.proposer_seconds(spec), "threshold_gpu_hours": spec["key_values"]["cap_gpu_hours"]}


def incoming(spec: dict, path: Path) -> None:
    path = Path(path).absolute()
    no_links(path)
    if root() / "incoming" / spec["run_id"] not in path.parents:
        raise S.Stop(f"STOP: stage P11 transfers under the engineering incoming tree: {path}")


def table_marker(spec: dict) -> dict:
    """Release-negative control, with no access to an evidence table or label archive."""
    path = root() / "table" / spec["run_id"]
    path.mkdir(parents=True, exist_ok=False)
    marker = {"schema": "g5_p11_release_negative_control/v1", "label": LABEL, "run_id": spec["run_id"]}
    with (path / "build.json").open("x", encoding="utf-8") as fh:
        json.dump(marker, fh, sort_keys=True)
        fh.write("\n")
    return marker | {"path": str(path)}


def closed_fixture(spec: dict) -> dict:
    """Leave a synthetic, interrupted attempt for the actual close-attempt command."""
    import g5_job as J

    if S.G.socket.gethostname() != spec["worker"]["hostname"]:
        raise S.Stop("STOP: prepare the C9 closed-attempt fixture on TASL-2")
    path = J.job_dir(spec, NODES[0], "campaigns-wave1")
    with S.G.gpu_lease(spec["worker"]["lease"]):
        attempt, directory = S.G.next_attempt(path)
        out = directory / "out"
        out.mkdir()
        (out / "P11_SYNTHETIC_INTERRUPTION").touch(exist_ok=False)
    return {"label": LABEL, "attempt": attempt, "path": str(directory)}


def probe(spec: dict) -> dict:
    from time import monotonic
    from urllib.error import URLError
    from urllib.request import Request, urlopen

    if S.G.socket.gethostname() != spec["worker"]["hostname"]:
        raise S.Stop("STOP: measure the P11 proposer link from TASL-2")
    identity = S.T4.server_identity(spec)
    request = Request(spec["proposer"]["server_url"] + "/v1/chat/completions",
                      data=json.dumps({"model": S.T4.MODEL["alias"], "max_tokens": 2, "cache_prompt": False,
                                       "messages": [{"role": "user", "content": "P11 synthetic link probe"}]}).encode(),
                      headers={"Content-Type": "application/json"})
    start = monotonic()
    try:
        with urlopen(request, timeout=30) as response:
            document = json.load(response)
    except (URLError, OSError, ValueError) as exc:
        raise S.Stop(f"STOP 12: the engineering proposer probe failed: {exc}") from None
    return {"label": LABEL, "run_id": spec["run_id"], "identity": identity,
            "completion_seconds": monotonic() - start, "usage": document.get("usage"),
            "health": S.T4.latency_probe(spec)}
