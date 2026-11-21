"""The sweep-2 batch: the 16 sealed chunks of ``s2ev-20261119-a`` copied out into a C3 sweep batch with an index in
sweep 1's schema (``r1.c3_sweep_index/1``), so the sweep-2 table is built by the existing ``dataset build-sweep`` and
audited by ``audit evidence-run --source sweep2``. AI-assisted (Claude). ENGINEERING code; it writes no label and opens
no label, audit or evaluation file (the sweep ledgers hold trial metrics only, which the table replays).

Layout under ``<paper root>/results/r1/evidence/C3_sweep2_batch_<run id>/``:

- ``chunks/<chunk id>/manifest.json``: each chunk's collector manifest, copied byte for byte;
- ``sweeps/<memory mode>/manifest.json``: the per-mode manifest, a pure function of that mode's eight chunk manifests
  (fields equal across the chunks, the eight nodes in the sweep-1 order, the per-node noise constants with their
  ``source`` written as the repository path of the pinned D28 summary; the chunk manifests' own paths are recorded);
- ``sweeps/<memory mode>/roots/<instance>.json`` (start files) and ``sweeps/<memory mode>/ledgers/<instance>/
  root_trials.jsonl``, copied byte for byte from each chunk's ``out/roots/`` and ``work/roots/``;
- ``EXTRACT.json``: every copied file with its sha256 and source path, and per chunk the sealed ``job_record.json``
  sha256 (equal to the sealed collection counts), the ``SEAL_RECEIPT.json`` sha256 and the record's pins;
- ``C3_sweep2_index_<run id>.json``: the index, binding ``EXTRACT.json`` by sha256.

``extract`` reads the sealed run directory (``/ceph/srv/dwong/paperb/sweep2/<run id>/``) and refuses unless:

- the collection counts are the pinned file (sha256 ``3e29382b…``, as published with the sweep-2 report);
- every chunk's ``SHA256SUMS`` verifies, and every file copied is listed in it;
- every ``job_record.json`` sha256 equals the collection counts' value, and the record carries the run id, chunk id,
  ``EVIDENCE``, the launch commit, the frozen image, the harness pin and ``b2_audits`` none;
- every chunk manifest is the sweep-2 collector's (EVIDENCE, ``audit_seeds`` 0, ``b2_audits`` none, the pinned noise
  source, its node and memory mode, 18 instances, 20 runs), with no recorded root failure;
- each chunk has exactly 18 root ledgers and 18 root records, and nothing is overwritten (a new directory).

``verify`` re-derives the per-mode manifests and the index from the copied chunk manifests and ``EXTRACT.json``,
re-hashes every file, and checks every chunk's ``job_record_sha256`` against the collection counts published on main
(``COLLECTION_COUNTS_PUBLISHED``). That is internal consistency only: someone who edits a ledger and rewrites
``EXTRACT.json`` and the index consistently passes it. What ties the batch to the sealed data is the signed B.2
addendum, which pins the index, ``EXTRACT.json`` and table sha256 values recorded after extraction and independently
reviewed (``audit.b2_addendum``/``_sweep2_pins_match``, checked at the audit start and again on consumption); and
``verify --sealed`` re-derives the whole batch from the sealed tree without writing and compares it byte for byte.
``counts`` prints the B.2 plan counts of a built table (eligible, duplicates,
no-ops, unique configurations, seed runs): table fields only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RUN_ID = "s2ev-20261119-a"
PAPER_COMMIT = "4aac52092813b2b01ddb96cd7d135c390aeff645"
HARNESS_COMMIT = "a3fedbbd44309b3fdf99d853ad841b9ec2c299e2"
IMAGE = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296"
AUTHORIZATION = {"path": "docs/r1/authorizations/c3_sweep2_20261119.md",
                 "sha256": "349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a"}
COLLECTION_COUNTS_SHA256 = "3e29382b4d31cef54b92d0cf77a0819b5dedda92aedd528b708f5030b88b6ec7"
COLLECTION_COUNTS_PUBLISHED = "docs/r1/reports/sweep2_20261116/sweep2_report_20261121/collection_counts.json"
SEALED_RUN_DIR = f"/ceph/srv/dwong/paperb/sweep2/{RUN_ID}"     # recorded as a constant, not as typed
NOISE_SOURCE = {"path": "results/r1/noise/D28_REPAIR_20261027/summary.json",
                "sha256": "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"}
NODES = ["digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc",
         "openml_credit_approval", "openml_sonar", "openml_climate"]          # the sweep-1 index order
MODES = {"append_only_summary": "primary", "none": "contrast"}
INSTANCES, RUNS = 18, 20
BATCH_PREFIX = "results/r1/evidence/C3_sweep2_batch_"
INDEX_SCHEMA = "r1.c3_sweep_index/1"
EXTRACT_SCHEMA = "r1.c3_sweep2_extract/1"
MODE_MANIFEST_SCHEMA = "r1.c3_sweep2_mode_manifest/1"
NOISE_KEYS = ("sigma_t", "sigma_s", "sigma_d", "definition")
# Fields that must be equal across the eight chunk manifests of one memory mode, carried into the mode manifest.
COMMON_KEYS = ("schema", "label", "split", "manager_backend", "manager", "memory_mode", "arm", "arm_role",
               "seed_policy", "instances", "runs", "points", "reps", "audit_seeds", "verify_r", "verify_split_policy",
               "roots_only", "root_failures", "c3_label_sweep", "action_versions")


class BatchError(ValueError):
    """A refusal of the sweep-2 batch step."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _jdump(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode()


def chunks() -> list[tuple[str, str, str]]:
    """(chunk id, node, memory mode), sorted by chunk id."""
    return sorted((f"{n}-{m}", n, m) for n in NODES for m in MODES)


def batch_dir(paper_root: Path, run_id: str = RUN_ID) -> Path:
    return Path(paper_root) / f"{BATCH_PREFIX}{run_id}"


def index_name(run_id: str = RUN_ID) -> str:
    return f"C3_sweep2_index_{run_id}.json"


def _no_links(root: Path, path: Path) -> None:
    p = path
    while True:
        if p.is_symlink():
            raise BatchError(f"symlink in the sealed tree: {p}")
        if p == root or p.parent == p:
            break
        p = p.parent


def _sums(chunk_dir: Path) -> dict[str, str]:
    lines = (chunk_dir / "SHA256SUMS").read_text().splitlines()
    out = {}
    for line in lines:
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        if rel in out or rel.startswith("/") or ".." in Path(rel).parts:
            raise BatchError(f"{chunk_dir}/SHA256SUMS: bad or duplicate entry {rel!r}")
        out[rel] = digest
    for rel, digest in out.items():
        path = chunk_dir / rel
        _no_links(chunk_dir, path)
        if not path.is_file() or _sha(path.read_bytes()) != digest:
            raise BatchError(f"{chunk_dir}/{rel}: differs from its sealed SHA256SUMS")
    return out


def _check_record(record: dict, chunk: str, node: str, mode: str, admitted: bool = False) -> dict:
    want = {"schema": "s2_c2_job_record/1", "run_id": RUN_ID, "chunk_id": chunk, "label": "EVIDENCE",
            "paper_commit": PAPER_COMMIT, "image_digest": IMAGE, "harness_commit": HARNESS_COMMIT}
    bad = {k: record.get(k) for k, v in want.items() if record.get(k) != v}
    if bad:
        raise BatchError(f"{chunk}: job record pins differ: {bad}")
    if not str(record.get("b2_audits", "")).startswith("none"):
        raise BatchError(f"{chunk}: job record does not show b2_audits none")
    if record.get("stop") is not None and not admitted:
        raise BatchError(f"{chunk}: job record shows a stop that the collection counts did not admit")
    if not record.get("finished_utc"):
        raise BatchError(f"{chunk}: job record has no finished_utc")
    return {"finished_utc": record["finished_utc"], "node": node, "memory_mode": mode,
            "cpu_model": (record.get("cpu") or {}).get("model"), "host": (record.get("site") or {}).get("fqdn"),
            "stop": record.get("stop")}


def _check_chunk_manifest(m: dict, chunk: str, node: str, mode: str) -> None:
    sweep = m.get("c3_label_sweep") or {}
    checks = {"label": m.get("label") == "EVIDENCE", "nodes": m.get("nodes") == [node],
              "memory_mode": m.get("memory_mode") == mode and sweep.get("memory_mode") == mode,
              "instances": m.get("instances") == INSTANCES, "runs": m.get("runs") == RUNS,
              "audit_seeds": m.get("audit_seeds") == 0, "b2_audits": sweep.get("b2_audits") == "none",
              "noise_source": sweep.get("noise_source") == NOISE_SOURCE,
              "noise": set(m.get("noise") or {}) == {node},
              "no launch_provenance": "launch_provenance" not in m}
    bad = sorted(k for k, ok in checks.items() if not ok)
    if bad:
        raise BatchError(f"{chunk}: collector manifest fails {bad}")


def _noise_entry(entry: dict, node: str, pinned: Path) -> dict:
    """The chunk's noise constants must equal the pinned D28 summary's; only ``source`` is rewritten (to the
    repository path), and the chunk's own path is kept beside it."""
    from r1.headroom.e1b_collect import node_noise
    expected = node_noise(pinned, node)
    if any(entry.get(k) != expected[k] for k in NOISE_KEYS):
        raise BatchError(f"{node}: chunk noise constants differ from the pinned D28 summary")
    if not str(entry.get("source", "")).endswith(NOISE_SOURCE["path"]):
        raise BatchError(f"{node}: chunk noise source {entry.get('source')!r} is not the pinned D28 summary")
    return {**entry, "source": NOISE_SOURCE["path"], "source_at_collection": entry.get("source")}


def mode_manifest(chunk_manifests: dict[str, dict], mode: str, pinned_noise: Path) -> dict:
    """The per-mode manifest: a pure function of the mode's eight chunk manifests ({chunk id: manifest})."""
    mine = {c: m for c, m in chunk_manifests.items() if c.endswith(f"-{mode}")}
    expected = {f"{n}-{mode}" for n in NODES}
    if set(mine) != expected:
        raise BatchError(f"{mode}: chunk manifests {sorted(mine)} != {sorted(expected)}")
    first = mine[sorted(mine)[0]]
    for c, m in mine.items():
        diff = sorted(k for k in COMMON_KEYS if m.get(k) != first.get(k))
        if diff:
            raise BatchError(f"{mode}: {c} differs from the other chunks in {diff}")
        if (m.get("harness") or {}).get("commit") != HARNESS_COMMIT or (m.get("harness") or {}).get("dirty") is not False:
            raise BatchError(f"{c}: collector harness is not the clean sweep-2 pin")
    noise = {}
    for n in NODES:
        noise[n] = _noise_entry(mine[f"{n}-{mode}"]["noise"][n], n, pinned_noise)
    return {**{k: first.get(k) for k in COMMON_KEYS}, "schema": MODE_MANIFEST_SCHEMA,
            "collector_schema": first.get("schema"), "nodes": list(NODES), "noise": noise,
            "harness": {"commit": HARNESS_COMMIT}, "run_id": RUN_ID,
            "chunks": {c: {"manifest": f"chunks/{c}/manifest.json"} for c in sorted(mine)}}


def build_index(manifests: dict[str, bytes], extract_bytes: bytes, extract: dict, paper_root: Path) -> dict:
    rel = f"{BATCH_PREFIX}{RUN_ID}"
    written = max(c["finished_utc"] for c in extract["chunks"].values()).replace("-", "").replace(":", "")
    first = json.loads(manifests[sorted(manifests)[0]])
    return {"schema": INDEX_SCHEMA, "label": "EVIDENCE", "written_utc": written, "nodes": list(NODES),
            "excluded_nodes": [], "instances": INSTANCES, "runs": RUNS, "harness_commit": HARNESS_COMMIT,
            "sweeps": [{"memory_mode": m, "arm_role": MODES[m], "out": f"{rel}/sweeps/{m}",
                        "manifest": f"{rel}/sweeps/{m}/manifest.json", "ledgers": f"{rel}/sweeps/{m}/ledgers",
                        "commit": PAPER_COMMIT} for m in MODES],
            "noise_source": dict(NOISE_SOURCE),
            "manager": first.get("manager"),
            "audit": {"status": "pending", "seeds": list(range(7001, 7011)), "label_seeds": list(range(7001, 7006)),
                      "evaluation_seeds": list(range(7006, 7011)),
                      "stage": "r1/c3/audit.py evidence-run --source sweep2 (a later authorization; "
                               "R1-SWEEP2-SETTINGS (2))"},
            "sweep2": {"run_id": RUN_ID, "paper_commit": PAPER_COMMIT, "harness_commit": HARNESS_COMMIT,
                       "image_digest": IMAGE, "authorization": dict(AUTHORIZATION),
                       "collection_counts_sha256": COLLECTION_COUNTS_SHA256,
                       "extract": {"path": f"{rel}/EXTRACT.json", "sha256": _sha(extract_bytes)}}}


def _admitted(counts: dict) -> dict[str, set[str]]:
    """{chunk id: sealed job-record sha256 values} of the admitted R1-SWEEP2-RTE-DIAG records."""
    out: dict[str, set[str]] = {}
    for a in counts.get("admitted_diagnosed_records") or []:
        out.setdefault(a["chunk"], set()).add(a["sealed_record_sha256"])
    return out


def _check_admitted(chunk_info: dict, counts: dict) -> None:
    """Every stopped chunk is an admitted one, and every admitted record's sha256 is its chunk's sealed record."""
    admitted = _admitted(counts)
    stopped = {c for c, i in chunk_info.items() if i.get("stop") is not None}
    if not stopped <= set(admitted):
        raise BatchError(f"stopped chunks not admitted by the collection counts: {sorted(stopped - set(admitted))}")
    for c, shas in admitted.items():
        if c not in chunk_info or shas != {chunk_info[c]["job_record_sha256"]}:
            raise BatchError(f"{c}: admitted record sha256 is not the chunk's sealed job record")


def extract(sealed_run_dir: Path, paper_root: Path, *, write: bool = True) -> dict:
    """Copy the sealed chunks out into a new batch directory (module docstring); returns the extract summary.
    With ``write=False`` nothing is written: the staged bytes are returned (``verify --sealed``)."""
    sealed, root = Path(sealed_run_dir), Path(paper_root).resolve()
    from r1.c3.analysis_guard import refuse_sealed, require_d8_confirmation
    require_d8_confirmation()
    if sealed.resolve() != Path(SEALED_RUN_DIR).resolve():
        raise BatchError(f"{sealed} is not the sealed run directory {SEALED_RUN_DIR} (no copies elsewhere)")
    refuse_sealed(sealed, root)
    _no_links(sealed.parent, sealed)
    counts_bytes = (sealed / "collection_counts.json").read_bytes()
    if _sha(counts_bytes) != COLLECTION_COUNTS_SHA256:
        raise BatchError("the sealed collection counts are not the published, pinned file")
    counts = json.loads(counts_bytes)
    if counts.get("run_id") != RUN_ID or counts.get("paper_commit") != PAPER_COMMIT or counts.get("chunks") != len(chunks()):
        raise BatchError("collection counts do not belong to the sweep-2 EVIDENCE run")
    pinned_noise = root / NOISE_SOURCE["path"]
    if not pinned_noise.is_file() or _sha(pinned_noise.read_bytes()) != NOISE_SOURCE["sha256"]:
        raise BatchError("pinned D28 noise summary missing or changed in the paper root")
    auth = root / AUTHORIZATION["path"]
    if not auth.is_file() or _sha(auth.read_bytes()) != AUTHORIZATION["sha256"]:
        raise BatchError("the sweep-2 authorization note is missing or changed in the paper root")
    dest = batch_dir(root)
    if write and dest.exists():
        raise BatchError(f"{dest} exists; the batch is written once")
    admitted = _admitted(counts)
    staged: dict[str, bytes] = {}            # batch-relative path -> bytes, written only after every check
    files, chunk_info, chunk_manifests = {}, {}, {}
    for chunk, node, mode in chunks():
        cdir = sealed / chunk
        _no_links(sealed, cdir)
        sums = _sums(cdir)
        record_bytes = (cdir / "job_record.json").read_bytes()
        if _sha(record_bytes) != counts["chunk_record_sha256"].get(chunk) or "job_record.json" not in sums:
            raise BatchError(f"{chunk}: job record is not the one the collection counted")
        info = _check_record(json.loads(record_bytes), chunk, node, mode, admitted=chunk in admitted)
        stray = sorted(r for r in sums if r.startswith("work/roots/") and r.rsplit("/", 1)[-1] != "root_trials.jsonl"
                       and r.rsplit("/", 1)[-1].startswith("root_trials.jsonl"))
        if stray:
            raise BatchError(f"{chunk}: rotated or suffixed root ledgers {stray[:3]} (the table reads every "
                             "root_trials.jsonl*; the batch copies exactly one per campaign)")
        receipt = cdir / "SEAL_RECEIPT.json"
        info.update(job_record_sha256=_sha(record_bytes),
                    seal_receipt_sha256=_sha(receipt.read_bytes()) if receipt.is_file() else None)
        if (cdir / "out" / "collection_failures.json").exists() or any(
                p for p in (cdir / "out" / "failures").glob("*.json")):
            raise BatchError(f"{chunk}: the collector recorded root failures; no table from an incomplete sweep")
        manifest_bytes = (cdir / "out" / "manifest.json").read_bytes()
        if "out/manifest.json" not in sums:
            raise BatchError(f"{chunk}: out/manifest.json is not in its SHA256SUMS")
        manifest = json.loads(manifest_bytes)
        _check_chunk_manifest(manifest, chunk, node, mode)
        chunk_manifests[chunk] = manifest
        staged[f"chunks/{chunk}/manifest.json"] = manifest_bytes
        files[f"chunks/{chunk}/manifest.json"] = {"sha256": _sha(manifest_bytes), "from": f"{chunk}/out/manifest.json"}
        insts = sorted(p.name for p in (cdir / "work" / "roots").iterdir() if p.is_dir())
        want = [f"{node}__s{s}" for s in sorted(int(i.rsplit("__s", 1)[1]) for i in insts)]
        roots = sorted(p.stem for p in (cdir / "out" / "roots").glob("*.json"))
        if len(insts) != INSTANCES or sorted(insts) != sorted(want) or roots != insts:
            raise BatchError(f"{chunk}: {len(insts)} root ledgers / {len(roots)} root records, expected "
                             f"{INSTANCES} matching campaigns of {node}")
        for inst in insts:
            for src, dst in ((f"work/roots/{inst}/root_trials.jsonl", f"sweeps/{mode}/ledgers/{inst}/root_trials.jsonl"),
                             (f"out/roots/{inst}.json", f"sweeps/{mode}/roots/{inst}.json")):
                if src not in sums:
                    raise BatchError(f"{chunk}/{src}: not in its SHA256SUMS")
                if dst in staged:
                    raise BatchError(f"{dst}: two chunks write the same file")
                data = (cdir / src).read_bytes()
                staged[dst] = data
                files[dst] = {"sha256": _sha(data), "from": f"{chunk}/{src}"}
        chunk_info[chunk] = info
    _check_admitted(chunk_info, counts)
    managers = {json.dumps(chunk_manifests[f"{n}-{m}"].get("manager"), sort_keys=True) for n in NODES for m in MODES}
    if len(managers) != 1:
        raise BatchError("the two memory modes do not share one manager declaration")
    manifests = {}
    for mode in MODES:
        data = _jdump(mode_manifest(chunk_manifests, mode, pinned_noise))
        manifests[mode] = data
        staged[f"sweeps/{mode}/manifest.json"] = data
        files[f"sweeps/{mode}/manifest.json"] = {"sha256": _sha(data), "from": "mode_manifest()"}
    extract_record = {"schema": EXTRACT_SCHEMA, "run_id": RUN_ID, "sealed_run_dir": SEALED_RUN_DIR,
                      "collection_counts_sha256": COLLECTION_COUNTS_SHA256, "chunks": chunk_info,
                      "files": dict(sorted(files.items())), "label": "EVIDENCE",
                      "note": "copied byte for byte from the sealed chunks; only the per-mode manifests are derived"}
    extract_bytes = _jdump(extract_record)
    index = build_index(manifests, extract_bytes, extract_record, root)
    if not write:
        return {"staged": {**staged, "EXTRACT.json": extract_bytes, index_name(): _jdump(index)}}
    dest.mkdir(parents=True)
    try:
        for rel, data in staged.items():
            p = dest / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        (dest / "EXTRACT.json").write_bytes(extract_bytes)
        (dest / index_name()).write_bytes(_jdump(index))
    except Exception:
        moved = dest.with_name(dest.name + ".incomplete")      # never deleted; a new directory is required
        dest.rename(moved)
        raise
    return {"batch": str(dest), "index": str(dest / index_name()), "files": len(files),
            "index_sha256": _sha((dest / index_name()).read_bytes()), "extract_sha256": _sha(extract_bytes)}


def verify(index_path: Path, paper_root: Path) -> dict:
    """Re-derive and re-hash the batch an index names (module docstring); returns its binding."""
    from r1.c3.analysis_guard import refuse_sealed
    index_path, root = Path(index_path), Path(paper_root).resolve()
    refuse_sealed(index_path, root)
    dest = batch_dir(root)
    if index_path.resolve() != (dest / index_name()).resolve():
        raise BatchError(f"{index_path} is not the sweep-2 index of {dest}")
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes)
    s2 = index.get("sweep2") or {}
    if index.get("schema") != INDEX_SCHEMA or index.get("label") != "EVIDENCE" or s2.get("run_id") != RUN_ID or \
            s2.get("collection_counts_sha256") != COLLECTION_COUNTS_SHA256 or s2.get("authorization") != AUTHORIZATION:
        raise BatchError("index does not bind the sweep-2 EVIDENCE run")
    extract_bytes = (dest / "EXTRACT.json").read_bytes()
    if s2.get("extract") != {"path": f"{BATCH_PREFIX}{RUN_ID}/EXTRACT.json", "sha256": _sha(extract_bytes)}:
        raise BatchError("index does not bind this EXTRACT.json")
    record = json.loads(extract_bytes)
    files = record.get("files") or {}
    on_disk = sorted(str(p.relative_to(dest)) for p in dest.rglob("*")
                     if (p.is_file() or p.is_symlink()) and str(p.relative_to(dest)) not in ("EXTRACT.json", index_name()))
    if on_disk != sorted(files):
        raise BatchError(f"batch files differ from EXTRACT.json: extra {sorted(set(on_disk) - set(files))[:3]}, "
                         f"missing {sorted(set(files) - set(on_disk))[:3]}")
    for rel, entry in files.items():
        p = dest / rel
        if p.is_symlink() or _sha(p.read_bytes()) != entry["sha256"]:
            raise BatchError(f"{rel}: differs from EXTRACT.json")
    published = root / COLLECTION_COUNTS_PUBLISHED
    if not published.is_file() or _sha(published.read_bytes()) != COLLECTION_COUNTS_SHA256:
        raise BatchError("the published sweep-2 collection counts are missing or changed in the paper root")
    counts = json.loads(published.read_bytes())
    info = record.get("chunks") or {}
    if record.get("sealed_run_dir") != SEALED_RUN_DIR or sorted(info) != sorted(c for c, _, _ in chunks()) or any(
            info[c].get("job_record_sha256") != counts["chunk_record_sha256"].get(c) for c in info):
        raise BatchError("EXTRACT.json chunk records differ from the published collection counts")
    _check_admitted(info, counts)
    pinned_noise = root / NOISE_SOURCE["path"]
    chunk_manifests = {c: json.loads((dest / f"chunks/{c}/manifest.json").read_bytes()) for c, _, _ in chunks()}
    for c, n, m in chunks():
        _check_chunk_manifest(chunk_manifests[c], c, n, m)
    manifests = {}
    for mode in MODES:
        derived = _jdump(mode_manifest(chunk_manifests, mode, pinned_noise))
        if derived != (dest / f"sweeps/{mode}/manifest.json").read_bytes():
            raise BatchError(f"sweeps/{mode}/manifest.json is not the derived mode manifest")
        manifests[mode] = derived
    if _jdump(build_index(manifests, extract_bytes, record, root)) != index_bytes:
        raise BatchError("the index is not the one derived from the batch")
    return {"index_sha256": _sha(index_bytes), "extract_sha256": _sha(extract_bytes), "run_id": RUN_ID,
            "files": len(files), "collection_counts_sha256": COLLECTION_COUNTS_SHA256}


def verify_sealed(index_path: Path, paper_root: Path, sealed_run_dir: Path) -> dict:
    """``verify`` plus a full re-derivation from the sealed tree (nothing written): every batch file, ``EXTRACT.json``
    and the index must equal what ``extract`` would write now, byte for byte."""
    out = verify(index_path, paper_root)
    staged = extract(sealed_run_dir, paper_root, write=False)["staged"]
    dest = batch_dir(Path(paper_root).resolve())
    on_disk = {str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()}
    if on_disk != set(staged):
        raise BatchError(f"batch file set differs from the sealed re-derivation: {sorted(on_disk ^ set(staged))[:3]}")
    bad = sorted(rel for rel, data in staged.items() if (dest / rel).read_bytes() != data)
    if bad:
        raise BatchError(f"batch differs from the sealed re-derivation: {bad[:3]}")
    return {**out, "sealed_rederivation": "equal"}


def counts(table_dir: Path) -> dict:
    """The B.2 plan counts of a built table: table fields only (no label, audit or evaluation file)."""
    from r1.c3 import audit
    from r1.c3.dataset import load_table
    rows = load_table(Path(table_dir))
    configs = json.loads((Path(table_dir) / "configs.json").read_text())
    selected, c = audit.partition_population(rows, configs)
    unique = len({(p["node"], p[k]) for p in selected for k in ("candidate_hash", "incumbent_hash")})
    return {**c, "proposals": len(rows), "unique_configs": unique,
            "seed_runs": unique * len(audit.DEFAULT_SEEDS)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--sealed", required=True, help=f"the sealed run directory .../sweep2/{RUN_ID}")
    e.add_argument("--paper-root", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--index", required=True)
    v.add_argument("--paper-root", required=True)
    v.add_argument("--sealed", help="also re-derive the batch from this sealed run directory (nothing written)")
    c = sub.add_parser("counts")
    c.add_argument("--table", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "extract":
            out = extract(Path(a.sealed), Path(a.paper_root))
        elif a.cmd == "verify":
            out = (verify_sealed(Path(a.index), Path(a.paper_root), Path(a.sealed)) if a.sealed
                   else verify(Path(a.index), Path(a.paper_root)))
        else:
            out = counts(Path(a.table))
    except (BatchError, OSError, ValueError, KeyError) as exc:
        print(f"STOP: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
