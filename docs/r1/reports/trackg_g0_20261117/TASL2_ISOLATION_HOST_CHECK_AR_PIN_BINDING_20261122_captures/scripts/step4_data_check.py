"""TASL-2 AR-pin host check, procedure section 4 checks: the autoresearch_fixedtokens data staged once under the
T1 layout.

Verifies, with the ar-cond7a interpreter:
  * ``sha256sum <data>/data_manifest.json`` equals ``ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51``;
  * the manifest lists exactly 13 files (11 shards + tokenizer/tokenizer.pkl + tokenizer/token_bytes.pt);
  * the manifest's source revision starts with ``915333b`` (the U1-audited revision prefix);
  * the checkout's only untracked entry is ``nodes/autoresearch_fixedtokens/data``, the link to the data root
    (absolute symlink), and nothing else is untracked or modified;
  * the data directory is read-only (prepare_data's ``make_read_only``).

Read-only: this checker writes only its own JSON/text outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

EXPECTED_MANIFEST_SHA = "ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51"
EXPECTED_FILES = 13
EXPECTED_REVISION_PREFIX = "915333b"
DATA_ROOT = "/home/dowling/r1_tracks/t1_tasl/data"
NODE_REL = "nodes/autoresearch_fixedtokens"


def run(cmd: list[str], cwd: str | None = None) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout.strip(),
                "stderr": out.stderr.strip()}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="the harness_ar checkout")
    ap.add_argument("--data-root", default=DATA_ROOT)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    repo = Path(args.repo)
    data_dir = Path(args.data_root) / "autoresearch_fixedtokens"
    node = repo / NODE_REL
    manifest_path = data_dir / "data_manifest.json"

    manifest = None
    manifest_sha = None
    if manifest_path.is_file():
        manifest_sha = sha256_file(manifest_path)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            manifest = None
    files = (manifest or {}).get("files", {})
    source = (manifest or {}).get("source", {})
    revision = str(source.get("revision", ""))
    link = node / "data"
    data_modes = run(["stat", "-c", "%a %n", str(data_dir)])
    manifest_modes = run(["stat", "-c", "%a %n", str(manifest_path)])
    git_status_untracked = run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"])
    git_status_tracked = run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"])
    untracked = [line for line in (git_status_untracked.get("stdout") or "").splitlines()
                 if line.startswith("??")]
    expected_link_line = f"?? {NODE_REL}/data"
    data_read_only = all((Path(data_dir) / name).stat().st_mode & 0o222 == 0
                         for name in files if (Path(data_dir) / name).is_file())
    checks = {
        "data_dir_exists": data_dir.is_dir(),
        "manifest_sha_matches": manifest_sha == EXPECTED_MANIFEST_SHA,
        "manifest_files_13": len(files) == EXPECTED_FILES,
        "revision_prefix_915333b": revision.startswith(EXPECTED_REVISION_PREFIX),
        "link_is_symlink": link.is_symlink(),
        "link_resolves_to_data_dir": link.is_symlink() and link.resolve() == data_dir.resolve(),
        "only_untracked_is_data_link": untracked == [expected_link_line],
        "no_tracked_changes": (git_status_tracked.get("stdout") or "").strip() == "",
        "data_files_read_only": bool(data_read_only),
    }
    result = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo": str(repo), "data_dir": str(data_dir), "node_data_link": str(link),
        "manifest": {
            "path": str(manifest_path), "sha256": manifest_sha,
            "expected_sha256": EXPECTED_MANIFEST_SHA, "file_count": len(files),
            "expected_file_count": EXPECTED_FILES,
            "source": source, "revision": revision,
            "revision_prefix_expected": EXPECTED_REVISION_PREFIX,
            "file_names": sorted(files),
        },
        "link": {
            "is_symlink": link.is_symlink(),
            "readlink": os.readlink(link) if link.is_symlink() else None,
            "resolves_to": str(link.resolve()) if link.exists() else None,
        },
        "git": {"status_untracked_all": git_status_untracked.get("stdout"),
                "status_tracked": git_status_tracked.get("stdout"),
                "untracked_lines": untracked},
        "modes": {"data_dir": data_modes.get("stdout"), "manifest": manifest_modes.get("stdout")},
        "checks": checks,
        "condition_4_data_pass": all(checks.values()),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        Path(args.text).write_text(
            f"utc={result['utc']} repo={result['repo']}\n"
            f"data_dir={data_dir} manifest={manifest_path}\n"
            f"manifest_sha256={manifest_sha}\nexpected={EXPECTED_MANIFEST_SHA}\n"
            f"file_count={len(files)} expected={EXPECTED_FILES}\n"
            f"revision={revision} prefix_expected={EXPECTED_REVISION_PREFIX}\n"
            f"source={json.dumps(source, default=str)}\n"
            f"link_is_symlink={link.is_symlink()} readlink={os.readlink(link) if link.is_symlink() else None}\n"
            f"untracked={json.dumps(untracked)}\n"
            f"tracked_status={(git_status_tracked.get('stdout') or '')!r}\n"
            f"modes={json.dumps(result['modes'])}\n"
            + "".join(f"{k}={v}\n" for k, v in checks.items()) +
            f"condition_4_data_pass={result['condition_4_data_pass']}\n",
            encoding="utf-8")
    print("RESULT " + json.dumps({"condition_4_data_pass": result["condition_4_data_pass"],
                                  "checks": checks, "manifest_sha256": manifest_sha,
                                  "file_count": len(files), "revision": revision,
                                  "link_readlink": result["link"]["readlink"]}, default=str))
    return 0 if result["condition_4_data_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
