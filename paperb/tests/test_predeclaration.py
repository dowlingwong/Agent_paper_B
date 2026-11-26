"""CPU-only checks of declaration hashing and the command-line contract."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
# The published SHA-256 test vector for the three ASCII bytes "abc".
ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "r1.predeclaration", *map(str, args)],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )


def test_hash_and_verify_exact_bytes_without_mutation(tmp_path):
    declaration = tmp_path / "declaration.md"
    declaration.write_bytes(b"abc")
    before = declaration.stat()

    hashed = run_cli("hash", declaration)
    assert (hashed.returncode, hashed.stdout, hashed.stderr) == (0, ABC_SHA256 + "\n", "")
    for expected in (ABC_SHA256, ABC_SHA256.upper()):
        verified = run_cli("verify", declaration, expected)
        assert (verified.returncode, verified.stdout, verified.stderr) == (0, "MATCH\n", "")

    mismatch = run_cli("verify", declaration, "0" * 64)
    assert (mismatch.returncode, mismatch.stdout, mismatch.stderr) == (1, "MISMATCH\n", "")
    after = declaration.stat()
    assert declaration.read_bytes() == b"abc"
    assert (after.st_size, after.st_mtime_ns, after.st_mode) == (
        before.st_size, before.st_mtime_ns, before.st_mode
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == ["declaration.md"]


def test_newline_changes_the_byte_digest(tmp_path):
    declaration = tmp_path / "declaration.md"
    declaration.write_bytes(b"abc\n")
    result = run_cli("verify", declaration, ABC_SHA256)
    assert (result.returncode, result.stdout) == (1, "MISMATCH\n")
    assert declaration.read_bytes() == b"abc\n"


@pytest.mark.parametrize("digest", ["", "0" * 63, "0" * 65, "g" * 64, " " + "0" * 63])
def test_malformed_digest_is_rejected(tmp_path, digest):
    declaration = tmp_path / "declaration.md"
    declaration.write_bytes(b"abc")
    result = run_cli("verify", declaration, digest)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Expected a 64-character hexadecimal SHA-256." in result.stderr
    assert declaration.read_bytes() == b"abc"


@pytest.mark.parametrize("command", ["hash", "verify"])
def test_missing_file_is_rejected_without_creating_it(tmp_path, command):
    missing = tmp_path / "missing.md"
    args = (command, missing, ABC_SHA256) if command == "verify" else (command, missing)
    result = run_cli(*args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Cannot read declaration:" in result.stderr
    assert not missing.exists()


@pytest.mark.parametrize("args", [(), ("hash",), ("verify",), ("verify", "some-file")])
def test_missing_cli_arguments_are_rejected(args):
    result = run_cli(*args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "error:" in result.stderr
