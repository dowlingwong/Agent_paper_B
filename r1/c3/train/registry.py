"""Track P model registry: download at a pinned revision, verify every file, write registry.yaml (RUNBOOK Track P 2.2).

ENGINEERING_ONLY; AI-assisted (Claude). For each repo @ full commit: ``snapshot_download`` into
``<models_dir>/<org>__<name>@<rev[:12]>``; then every file is checked against the Hub's own record at that revision:
LFS files by their sha256 (the LFS oid), other files by their git blob sha1. The registry records repo, revision,
files, sizes and sha256 of every file. A free-space floor (R1-EXAM-STORAGE: 100 GB on the shared filesystem) is
checked before and after each download.

Usage::

    python -m r1.c3.train.registry --models-dir ~/r1_trackp/models --out r1/c3/train/registry.yaml
    python -m r1.c3.train.registry --verify r1/c3/train/registry.yaml   # re-hash every file
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

import yaml

from r1.c3.analysis_guard import refuse_sealed

FREE_FLOOR_BYTES = 100_000_000_000
# Phase 0 identities and revisions (PORTAL_TRACKP_HOST_FACTS_20261026.md); Kev at its v1.0 release tag
PINS = {
    "kev-0.8b": ("jaredpalmer/kev-0.8b", "788ddbdd65715bb03a56788c822f6c632c9a551d"),
    "kev-4b": ("jaredpalmer/kev-4b", "591dcb5bd6d05eb0b5131ea6608f93f10243335c"),
    "qwen3.5-0.8b-base": ("Qwen/Qwen3.5-0.8B-Base", "dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68"),
    "qwen3.5-4b-base": ("Qwen/Qwen3.5-4B-Base", "1001bb4d826a52d1f399e183466143f4da7b741b"),
    "laya": ("convaiinnovations/laya-typed-decisions", "e929ae5cf69bc34259cd2f95c9e91145b818b1f0"),
    "startlux-0.8b": ("startlux-models/StartLux-Decision-v1.1-0.8B-Instant", "6496ae641cc71b149ce9dad69bd97f2a44e7bf11"),
    "startlux-2b": ("startlux-models/StartLux-Decision-v1.1-2B-Instant", "f1e6cd147dda82c9ffa3e8e725d5c1f175566fb1"),
    "startlux-4b": ("startlux-models/StartLux-Decision-v1.1-4B-Instant", "416088f77cfce09633906a3675c7cd2e5dabcf10"),
}

# Licence notes recorded with the entry (R1-STARTLUX-TRAINABLE, 26 Oct: StartLux is a trainable candidate under
# CC BY-NC 4.0 — research use, non-commercial; noted here and in the appendix). From each repo's LICENSE / README.
LICENCES = {k: "CC-BY-NC-4.0 (LICENSE 'Attribution-NonCommercial 4.0 International'; non-commercial research use)"
            for k in ("startlux-0.8b", "startlux-2b", "startlux-4b")}


class RegistryError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    refuse_sealed(path)
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(path: Path) -> str:
    refuse_sealed(path)
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def hub_tree(repo: str, rev: str) -> dict:
    """{path: {"size", "oid" (git blob sha1), "lfs_sha256" | None}} at ``rev`` (recursive)."""
    url = f"https://huggingface.co/api/models/{repo}/tree/{rev}?recursive=true"
    with urllib.request.urlopen(url, timeout=60) as r:
        items = json.load(r)
    return {it["path"]: {"size": it.get("size"), "oid": it.get("oid"),
                         "lfs_sha256": (it.get("lfs") or {}).get("oid")}
            for it in items if it.get("type") == "file"}


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def check_floor(path: Path) -> None:
    free = free_bytes(path)
    if free < FREE_FLOOR_BYTES:
        raise RegistryError(f"STOP: {free} bytes free on the models filesystem, below the 100 GB floor")


def download(key: str, models_dir: Path) -> dict:
    refuse_sealed(models_dir)
    from huggingface_hub import snapshot_download
    repo, rev = PINS[key]
    models_dir.mkdir(parents=True, exist_ok=True)
    check_floor(models_dir)
    target = models_dir / f"{repo.replace('/', '__')}@{rev[:12]}"
    snapshot_download(repo, revision=rev, local_dir=str(target))
    check_floor(models_dir)
    return verify_dir(key, target)


def verify_dir(key: str, target: Path) -> dict:
    refuse_sealed(target)
    repo, rev = PINS[key]
    tree = hub_tree(repo, rev)
    files, problems = {}, []
    for rel, meta in sorted(tree.items()):
        p = target / rel
        refuse_sealed(p)
        if not p.is_file():
            problems.append(f"missing {rel}")
            continue
        size = p.stat().st_size
        sha = sha256_file(p)
        if meta["size"] is not None and size != meta["size"]:
            problems.append(f"{rel}: size {size} != hub {meta['size']}")
        if meta["lfs_sha256"]:
            if sha != meta["lfs_sha256"]:
                problems.append(f"{rel}: sha256 {sha} != hub LFS {meta['lfs_sha256']}")
        elif meta["oid"] and git_blob_sha1(p) != meta["oid"]:
            problems.append(f"{rel}: git blob sha1 != hub {meta['oid']}")
        files[rel] = {"size": size, "sha256": sha, "verified_against": "lfs_sha256" if meta["lfs_sha256"] else "git_blob_sha1"}
    extra = []
    for p in target.rglob("*"):
        refuse_sealed(p)
        if p.is_file() and ".cache" not in p.parts and str(p.relative_to(target)) not in tree:
            extra.append(str(p.relative_to(target)))
    extra.sort()
    if problems:
        raise RegistryError(f"STOP: {repo}@{rev} failed verification: {problems[:5]}")
    out = {"repo": repo, "revision": rev, "local_path": str(target), "files": files,
           "total_bytes": sum(f["size"] for f in files.values()), "untracked_local_files": extra}
    if key in LICENCES:
        out["licence"] = LICENCES[key]
    return out


def reverify(registry_path: Path) -> list[str]:
    """Re-hash every registered file; returns the list of mismatches (empty = all verified)."""
    refuse_sealed(registry_path)
    reg = yaml.safe_load(Path(registry_path).read_text())
    bad = []
    for key, ent in reg["models"].items():
        for rel, f in ent["files"].items():
            p = Path(ent["local_path"]) / rel
            refuse_sealed(p)
            if not p.is_file() or sha256_file(p) != f["sha256"]:
                bad.append(f"{key}:{rel}")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--models-dir", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--verify", type=Path, help="re-hash every file of an existing registry")
    args = ap.parse_args(argv)
    refuse_sealed(args.verify, args.out, args.models_dir)
    if args.verify:
        bad = reverify(args.verify)
        print(json.dumps({"registry": str(args.verify), "mismatches": bad}))
        return 1 if bad else 0
    reg = yaml.safe_load(args.out.read_text()) if args.out and args.out.is_file() else {}
    reg.setdefault("schema", "trackp_registry/v1")
    reg.setdefault("models", {})
    for key in args.only or PINS:
        print(f"downloading {key} ...", flush=True)
        try:
            reg["models"][key] = download(key, args.models_dir.expanduser())
        except RegistryError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        args.out.write_text(yaml.safe_dump(reg, sort_keys=True))
        print(f"verified {key}: {len(reg['models'][key]['files'])} files, "
              f"{reg['models'][key]['total_bytes'] / 1e9:.2f} GB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
