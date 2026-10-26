"""Hash and verify the exact bytes of an author-written declaration.

This tool never writes or adopts a declaration. AI-assisted.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
from pathlib import Path


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    hash_cmd = sub.add_parser("hash", help="print SHA-256 of a file's exact bytes")
    hash_cmd.add_argument("path", type=Path)
    verify_cmd = sub.add_parser("verify", help="compare a SHA-256 with a file's exact bytes")
    verify_cmd.add_argument("path", type=Path)
    verify_cmd.add_argument("sha256")
    args = parser.parse_args()
    try:
        actual = digest_file(args.path)
    except OSError as error:
        parser.exit(2, f"Cannot read declaration: {error}\n")
    if args.command == "hash":
        print(actual)
        return 0
    expected = args.sha256.lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        parser.exit(2, "Expected a 64-character hexadecimal SHA-256.\n")
    if not hmac.compare_digest(actual, expected):
        print("MISMATCH")
        return 1
    print("MATCH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
