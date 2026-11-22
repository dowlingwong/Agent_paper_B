"""The G5-PIN B check (sweep2/t1_tasl/g5_pin_check.py): synthetic harness repos, plus the real pins when available."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
import g5_pin_check as C  # noqa: E402


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          capture_output=True, text=True, check=True).stdout.strip()


def _commit(repo, files: dict, msg: str, parent: str | None = None) -> str:
    if parent:
        _git(repo, "checkout", "-q", "--detach", parent)
    for rel, text in files.items():
        p = repo / rel
        if text is None:
            p.unlink()
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def world(tmp_path):
    repo = tmp_path / "h"
    repo.mkdir()
    _git(repo, "init", "-q")
    p7 = _commit(repo, {"src/engine.py": "e0\n", "nodes/ar/node.py": "n0\n", "node_lib/ar_isolated.py": "i0\n",
                        "nodes/cifar/node.py": "c0\n"}, "pin seven")
    par = _commit(repo, {"nodes/ar/node.py": "n1\n", "node_lib/ar_isolated.py": "i1\n"}, "pin ar", p7)
    g5 = {"src/engine.py": "e1\n", "src/audit_g5.py": "a\n"}
    g7 = _commit(repo, g5, "g5 seven", p7)
    gar = _commit(repo, g5, "g5 ar", par)
    return repo, p7, par, g7, gar, g5


def test_identical_g5_code_on_both_pins_passes(world):
    repo, p7, par, g7, gar, _ = world
    out = C.check(repo, g7, gar, pin_seven=p7, pin_ar=par)
    assert out["pin_delta"] == ["node_lib/ar_isolated.py", "nodes/ar/node.py"]
    assert out["g5_changes"] == ["src/audit_g5.py", "src/engine.py"]


def test_g5_code_that_differs_between_the_families_stops(world):
    repo, p7, par, g7, gar, g5 = world
    other = _commit(repo, {**g5, "src/audit_g5.py": "a-different\n"}, "g5 ar drift", par)
    with pytest.raises(C.Stop, match=r"differ outside the pin delta.*src/audit_g5.py"):
        C.check(repo, g7, other, pin_seven=p7, pin_ar=par)
    added = _commit(repo, {"src/only_here.py": "x\n"}, "g5 ar extra file", gar)
    with pytest.raises(C.Stop, match="only_here.py"):
        C.check(repo, g7, added, pin_seven=p7, pin_ar=par)


def test_g5_changing_a_pin_delta_file_stops(world):
    repo, p7, par, g7, gar, g5 = world
    both = {**g5, "node_lib/ar_isolated.py": "i2\n"}
    g7b = _commit(repo, both, "g5 seven edits pin file", p7)
    garb = _commit(repo, both, "g5 ar edits pin file", par)
    with pytest.raises(C.Stop, match="made equal|a file of the pin delta"):        # equal on both sides now
        C.check(repo, g7b, garb, pin_seven=p7, pin_ar=par)
    g7c = _commit(repo, {**g5, "nodes/ar/node.py": "n9\n"}, "g5 seven edits ar node", p7)
    with pytest.raises(C.Stop, match="a file of the pin delta"):
        C.check(repo, g7c, gar, pin_seven=p7, pin_ar=par)


def test_ancestry_is_required(world):
    repo, p7, par, g7, gar, g5 = world
    with pytest.raises(C.Stop, match="G5-AR .* does not descend from autoresearch's"):
        C.check(repo, g7, g7, pin_seven=p7, pin_ar=par)
    _git(repo, "checkout", "-q", "--orphan", "elsewhere")
    orphan = _commit(repo, {"z": "1\n"}, "unrelated root")
    with pytest.raises(C.Stop, match="G5-7 .* does not descend from the seven"):
        C.check(repo, orphan, gar, pin_seven=p7, pin_ar=par)
    with pytest.raises(C.Stop, match="autoresearch's pin .* does not descend"):
        C.check(repo, g7, gar, pin_seven=p7, pin_ar=orphan)
    with pytest.raises(C.Stop, match="is not a commit"):
        C.check(repo, "0" * 40, gar, pin_seven=p7, pin_ar=par)
    assert C.main([str(repo), g7, g7]) == 2


def test_the_real_pins_pass_with_no_g5_code(capsys):
    """On the real harness the two G.1b pins themselves are a trivially consistent pair (no G.5 code yet)."""
    root = os.environ.get("AR_HARNESS_ROOT")
    if not root or subprocess.run(["git", "-C", root, "cat-file", "-e", C.PIN_AR + "^{commit}"],
                                  capture_output=True).returncode != 0:
        pytest.skip("the harness repo with both pins is not available (set AR_HARNESS_ROOT)")
    assert C.main([root, C.PIN_SEVEN, C.PIN_AR]) == 0
    import json
    out = json.loads(capsys.readouterr().out)
    assert out["g5_changes"] == [] and "src/autoresearch/trackg/node_lib/ar_isolated.py" in out["pin_delta"]
