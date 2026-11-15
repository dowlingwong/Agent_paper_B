"""Runbook P2: the seed registry is generated from code, reproducible, and disjoint from Paper B."""
import subprocess
from pathlib import Path

import pytest

from paperc import schema as S
from paperc import seeds

REPO = Path(__file__).resolve().parents[2]


def _have(ref):
    return subprocess.run(["git", "-C", str(REPO), "cat-file", "-e", f"{ref}^{{commit}}"],
                          capture_output=True).returncode == 0


needs_pins = pytest.mark.skipif(not (_have(seeds.CANONICAL) and _have(seeds.TRACKS)),
                                reason="pinned commits not present in this clone (git fetch the two branches)")


@needs_pins
def test_generation_is_reproducible_and_matches_committed_file():
    a = seeds.dumps(seeds.build_registry(REPO))
    b = seeds.dumps(seeds.build_registry(REPO))
    assert a == b
    assert seeds.OUT.read_text() == a, "registry file is stale: run python -m paperc.seeds"


@needs_pins
def test_known_values_from_code():
    by = {b.name: b for b in seeds.paper_b_blocks(REPO)}
    assert (by["c3_audits"].lo, by["c3_audits"].hi) == (7001, 7011)
    assert (by["exam_instances"].lo, by["exam_instances"].hi) == (9001, 9100)
    assert (by["exam_audits"].lo, by["exam_audits"].hi) == (9101, 9300)
    assert (by["tracks_instances_S0.5"].lo, by["tracks_instances_S0.5"].hi) == (30500, 31000)
    assert (by["tracks_audits_fixture"].lo, by["tracks_audits_fixture"].hi) == (700000, 800000)
    assert by["tracks_selection_key"].lo == 35001
    assert by["noise_floor_joint"].lo == 3001
    assert by["e1b_leaf_audits"].lo == 5001
    # e1b formula: 100 + 10k + residue, k < 90 -> [100, 997)
    assert (by["e1b_instances"].lo, by["e1b_instances"].hi) == (100, 997)
    assert (by["tracks_s11_factorial"].lo, by["tracks_s11_factorial"].hi) == (37001, 37031)
    assert (by["tracks_oracle_select"].lo, by["tracks_oracle_eval"].hi) == (1_000_000, 3_000_000)
    assert by["node_default_seed"].lo == 42 and by["e2e_worker_seed_999"].lo == 999
    assert (by["tracks_audits_legacy"].lo, by["tracks_audits_legacy"].hi) == (33001, 35000)
    for key in (20261012, 20261019, 20261026, 20261029, 20261107):
        assert f"rng_key_{key}" in by


@needs_pins
def test_paper_b_has_no_internal_overlap_and_paper_c_is_disjoint():
    pb = seeds.paper_b_blocks(REPO)
    assert seeds.paper_b_overlaps(pb, worker_only=True) == []
    assert seeds.check_disjoint(pb) == []


def test_check_disjoint_detects_collision_and_margin():
    pb = [seeds.Block("b", 49_500, 49_600, "literal", None, None, None)]
    assert seeds.check_disjoint(pb)                        # within the 1000 margin of paperc_instances
    pb = [seeds.Block("b", 40_000, 48_000, "literal", None, None, None)]
    assert seeds.check_disjoint(pb) == []


def test_registry_flags_paper_b_seed_in_check_campaign():
    from test_schema import valid_campaign
    reg = seeds.Registry.load()
    assert reg.paper_b_block("digits_mlp", 30510) == "tracks_instances_S0.5"
    assert reg.paper_b_block("digits_mlp", 50001) is None
    assert reg.paper_c_block(50001) == "paperc_instances"
    viol = S.check_campaign(valid_campaign(campaign="pc-c1", seed=7005), registry=reg)
    assert {v.check for v in viol} == {"seed"}
    assert S.check_campaign(valid_campaign(campaign="pc-c1", seed=50001), registry=reg) == []
    # Paper C membership: a seed in no block at all, and a campaign id without the pc- prefix
    viol = S.check_campaign(valid_campaign(campaign="pc-c1", seed=45000), registry=reg)
    assert {v.check for v in viol} == {"seed"} and any("outside paperc_instances" in v.message for v in viol)
    viol = S.check_campaign(valid_campaign(campaign="c1", seed=50001), registry=reg)
    assert {v.check for v in viol} == {"seed"} and any("prefix" in v.message for v in viol)


def test_constants_reader_does_not_import():
    src = "import os\nos.system('false')\nA = 3\nB = range(A, A + 2)\nC = {'x': (1, 2)}\nD = os.getcwd()\n"
    c = seeds.constants(src, ["A", "B", "C"])
    assert c["B"] == range(3, 5) and c["C"] == {"x": (1, 2)}
    with pytest.raises(KeyError):
        seeds.constants(src, ["D"])


@needs_pins
def test_every_seed_constant_in_code_is_accounted_for():
    pb = seeds.paper_b_blocks(REPO)
    assert seeds.unaccounted(REPO, pb) == []


def test_unaccounted_detects_new_constants_and_range_gaps():
    blocks = [seeds.Block("a", 100, 200, "literal", None, None, None), seeds.Block("b", 300, 400, "literal", None,
                                                                                  None, None)]
    fake = [{"ref": "x" * 40, "path": "r1/new.py", "name": "SEED", "value": 45000},
            {"ref": "x" * 40, "path": "r1/new.py", "name": "RANGE_SEEDS", "value": range(150, 350)},
            {"ref": "x" * 40, "path": "r1/new.py", "name": "OK_SEEDS", "value": range(120, 180)},
            {"ref": "x" * 40, "path": "r1/new.py", "name": "SEEDS_FILE", "value": "audit_seeds.json"}]
    out = seeds.unaccounted(REPO, blocks, fake)
    assert out == ["r1/new.py:RANGE_SEEDS at xxxxxxxx: [(200, 299)] outside every block",
                   "r1/new.py:SEED at xxxxxxxx: [(45000, 45000)] outside every block"]
    assert seeds.skipped_textual(fake) == ["r1/new.py:SEEDS_FILE"]


def test_scan_name_matches_bare_seed():
    for n in ("SEED", "PLAN_SEED", "AUDIT_SEED_BASE", "SEED_BASE", "S11_SEEDS", "ORACLE_EVAL_BASE"):
        assert seeds.SCAN_NAME.match(n), n


def test_function_compiles_in_isolation():
    src = "import os\n@decorator_that_does_not_exist\ndef f(node: Foo, k: int = os.getpid()) -> Bar:\n    return 100 + 10 * k + (sum(map(ord, node)) % 7)\n"
    f = seeds.function(src, "f")
    assert f("abc", 3) == 100 + 30 + (sum(map(ord, "abc")) % 7)


def test_real_node_rows_need_an_explicit_worker_seed():
    from test_schema import valid_campaign
    reg = seeds.Registry.load()
    rows = valid_campaign(campaign="pc-c1", seed=50001)
    for r in rows:
        r["identity"]["tier"] = "E-T0"
    viol = S.check_campaign(rows, registry=reg)
    assert {v.check for v in viol} == {"seed"} and any("worker_seed must be explicit" in v.message for v in viol)
    for r in rows:
        r["seeds"]["worker_seed"] = 50001
    assert S.check_campaign(rows, registry=reg) == []


def test_scan_finds_argparse_and_rng_constructor_seeds():
    src = ("import argparse, numpy as np, torch\np = argparse.ArgumentParser()\n"
           "p.add_argument('--order-seed', type=int, default=20261029)\n"
           "torch.manual_seed(1234)\nrng = np.random.default_rng(4242)\n"
           "def f(base_seed=777, n=3):\n    return base_seed\n")
    assert seeds._seed_literals(src, "argparse:") == [20261029]
    assert seeds._seed_literals(src, "rngcall:") == [1234, 4242]
    assert seeds._seed_literals(src, "anydef:") == [777]
