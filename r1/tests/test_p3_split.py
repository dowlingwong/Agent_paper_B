"""The P3 split file (PRE-SPLIT A): committed bytes = generator output, pinned sha256, the T0 rule as the SFT
builder computes it, the T1 rule as G5-SPLIT states it, refusals. No table, label or evaluation value is read."""
import hashlib
import json
import os
from pathlib import Path

import pytest

from r1.c3 import p3_split as P
from r1.harness import REPO

FILE = REPO / "r1/c3/splits/c3_p3_split_v1.json"


def test_committed_file_is_the_generator_output_with_the_pinned_sha():
    raw = FILE.read_bytes()
    assert raw == P.render(P.build())
    assert hashlib.sha256(raw).hexdigest() == P.P3_SPLIT_SHA256
    assert P.load(FILE)["schema"] == P.SCHEMA
    assert P.main(["verify", str(FILE)]) == 0


def test_load_refuses_other_bytes(tmp_path):
    other = tmp_path / "split.json"
    other.write_bytes(FILE.read_bytes().replace(b'"test"', b'"Test"', 1))
    with pytest.raises(P.SplitError, match="not the pinned"):
        P.load(other)
    with pytest.raises(P.SplitError, match="does not equal"):      # matching sha supplied for altered bytes -> generator-equality check
        P.load(other, sha256=hashlib.sha256(other.read_bytes()).hexdigest())
    assert P.main(["verify", str(other)]) == 2


def test_t0_nodes_and_seeds_match_the_gate_and_the_collector():
    from r1.c3 import gate
    assert P.T0_NODES == gate.T0_NODES
    if not (Path(os.environ.get("AR_HARNESS_ROOT", REPO.parent / "autoresearch_harness")) / "src").is_dir():
        pytest.skip("harness checkout needed for e1b_collect")
    from r1.headroom.e1b_collect import _instance_seed
    for node in P.T0_NODES:
        assert [P.t0_instance_seed(node, k) for k in range(18)] == [_instance_seed(node, k) for k in range(18)]


def test_t0_equals_the_sft_builder_with_the_p3_salt():
    from r1.c3.train import sft_data
    split = P.load(FILE)
    universe = [P.instance_id(n, P.t0_instance_seed(n, k)) for n in P.T0_NODES for k in range(18)]
    got = sft_data.assign_splits(universe, {"salt": "c3_p3_split/v1", "test_instances_per_node": 9,
                                            "val_instances_per_node": 3}, universe=universe)
    mine = {i: v["split"] for i, v in P.assignment(split).items() if v["tier"] == "T0"}
    assert mine == {i: ("dev" if s == "val" else s) for i, s in got.items()}


def test_t1_follows_g5_split_exactly():
    split = P.load(FILE)
    for node in P.T1_NODES:
        order = sorted(range(5101, 5113), key=lambda s: hashlib.sha256(f"c3_t1_split/v1:{node}:{s}".encode())
                       .hexdigest())
        ids = [f"{node}__s{s}" for s in order]
        assert split["t1"]["nodes"][node] == {"test": ids[:6], "dev": ids[6:8], "train": ids[8:]}


def test_t1_nodes_cover_the_g5_table_and_the_joining_node(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "sweep2" / "t1_tasl"))
    import g1b_tasl
    assert set(P.T1_NODES) == set(g1b_tasl.T1_NODES) | set(g1b_tasl.T1_NODES_LATER)


def test_counts_disjointness_and_coverage():
    split = P.load(FILE)
    assign = P.assignment(split)
    assert len(assign) == 8 * 18 + 8 * 12
    for tier, counts, n in (("t0", P.T0_COUNTS, 18), ("t1", P.T1_COUNTS, 12)):
        for node, parts in split[tier]["nodes"].items():
            assert {k: len(v) for k, v in parts.items()} == counts
            assert len(set(sum(parts.values(), []))) == n
            assert all(i.startswith(f"{node}__s") for i in sum(parts.values(), []))


def test_an_instance_outside_the_file_is_refused():
    assign = P.assignment(P.load(FILE))
    assert P.split_of(assign, "digits_mlp__s104") in P.SPLITS
    for bad in ("digits_mlp__s30000", "digits_mlp__s0104", "mlab_cifar10__s5113", "openml_blood_transfusion__s100"):
        with pytest.raises(P.SplitError, match="not in the P3 split file"):
            P.split_of(assign, bad)


def test_split_of_loads_the_pinned_file_and_assignment_refuses_other_dicts():
    assert P.split_of(None, "digits_mlp__s204") == "test"
    assert P.split_of(None, "digits_mlp__s214") == "dev"
    for bad in ({}, {"schema": "other", "t0": {}, "t1": {}}, json.loads(FILE.read_text()) | {"schema": "x"}):
        with pytest.raises(P.SplitError, match="use load"):
            P.assignment(bad)
    with pytest.raises(P.SplitError, match="not in the P3 split file"):
        P.split_of(None, "digits_mlp__s9011")


def test_partition_refuses_wrong_counts():
    with pytest.raises(P.SplitError):
        P._partition(["a", "b"], P.T0_COUNTS)


def test_disclosed_trackp_sft_overlap_with_p3_test():
    """The report's disclosure: trackp_sft/v1 training instances among each node's 9 P3 test instances."""
    from r1.c3.train import sft_data
    cfg = json.loads((REPO / "r1/scripts/configs/trackp_sft.json").read_text())
    split_cfg = cfg.get("splits", cfg.get("split", cfg))
    universe = [P.instance_id(n, P.t0_instance_seed(n, k)) for n in P.T0_NODES for k in range(18)]
    old = sft_data.assign_splits(universe, split_cfg, universe=universe)
    assert sorted(set(old.values())) == ["test", "train", "val"]
    p3 = P.load(FILE)["t0"]["nodes"]
    got = [sum(old[i] == "train" for i in p3[n]["test"]) for n in P.T0_NODES]
    assert got == [5, 7, 6, 5, 6, 5, 6, 5]
