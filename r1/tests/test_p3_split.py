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
FILE_V2 = REPO / "r1/c3/splits/c3_p3_split_v2.json"


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
    for node in P.T1_NODES_V1:
        order = sorted(range(5101, 5113), key=lambda s: hashlib.sha256(f"c3_t1_split/v1:{node}:{s}".encode())
                       .hexdigest())
        ids = [f"{node}__s{s}" for s in order]
        assert split["t1"]["nodes"][node] == {"test": ids[:6], "dev": ids[6:8], "train": ids[8:]}


def test_t1_nodes_cover_the_g5_table_and_the_joining_node(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "sweep2" / "t1_tasl"))
    import g1b_tasl
    assert set(P.T1_NODES_V1) == set(g1b_tasl.T1_NODES) | set(g1b_tasl.T1_NODES_LATER)


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
    split_cfg = dict(sft_data.DEFAULT_SPLITS)            # trackp_sft/v1: salt trackp_sft/v1, 3 test / 3 val
    assert split_cfg["salt"] == "trackp_sft/v1" and split_cfg["test_instances_per_node"] == 3
    universe = [P.instance_id(n, P.t0_instance_seed(n, k)) for n in P.T0_NODES for k in range(18)]
    old = sft_data.assign_splits(universe, split_cfg, universe=universe)
    assert sorted(set(old.values())) == ["test", "train", "val"]
    p3 = P.load(FILE)["t0"]["nodes"]
    got = [sum(old[i] == "train" for i in p3[n]["test"]) for n in P.T0_NODES]
    assert got == [5, 7, 6, 5, 6, 5, 6, 5]


# ------------------------------------------------------------------------------ version 2 (R1-G5-S9 (1), split A)

def _block(raw: bytes, path: tuple) -> bytes:
    """The rendered bytes of one sub-object of a split file, as they appear inside the file (indent 1, sorted)."""
    obj = json.loads(raw)
    for k in path:
        obj = obj[k]
    text = json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=True)
    return text.replace("\n", "\n" + " " * len(path))


def test_v2_committed_file_is_the_generator_output_with_the_pinned_sha():
    raw = FILE_V2.read_bytes()
    assert raw == P.render(P.build(2))
    assert hashlib.sha256(raw).hexdigest() == P.P3_SPLIT_V2_SHA256 == P.SPLIT_FILES[2]["sha256"]
    assert P.load(FILE_V2)["schema"] == P.SCHEMA_V2 and P.version_of(P.load(FILE_V2)) == 2
    assert P.load(FILE)["schema"] == P.SCHEMA and P.version_of(P.load(FILE)) == 1
    assert P.main(["verify", str(FILE_V2)]) == 0
    assert P.load_pinned({"path": "r1/c3/splits/c3_p3_split_v2.json", "sha256": P.P3_SPLIT_V2_SHA256}) == \
        json.loads(raw)
    from r1.c3.train import sft_data
    assert sft_data.SIGNED_SPLIT_FILES == (P.SPLIT_FILES[1], P.SPLIT_FILES[2])


def test_v2_keeps_t0_and_the_eight_t1_nodes_byte_identical_entry_by_entry():
    """R1-G5-S9 (1): the eight T1 nodes and the whole T0 part are byte-identical to v1."""
    v1, v2 = FILE.read_bytes(), FILE_V2.read_bytes()
    d1, d2 = json.loads(v1), json.loads(v2)
    assert d1["t0"] == d2["t0"]
    assert _block(v1, ("t0",)) == _block(v2, ("t0",)) and _block(v2, ("t0",)).encode() in v2
    for node in d1["t0"]["nodes"]:
        b = _block(v1, ("t0", "nodes", node))
        assert b == _block(v2, ("t0", "nodes", node)) and b.encode() in v1 and b.encode() in v2
    assert sorted(d1["t1"]["nodes"]) == sorted(P.T1_NODES_V1)
    for node in P.T1_NODES_V1:
        b = _block(v1, ("t1", "nodes", node))
        assert d1["t1"]["nodes"][node] == d2["t1"]["nodes"][node]
        assert b == _block(v2, ("t1", "nodes", node)) and b.encode() in v1 and b.encode() in v2
    for k in ("rule", "salt", "counts", "seeds"):
        assert d1["t1"][k] == d2["t1"][k]
    for k in ("instance_id", "missing_instances", "preregistration"):
        assert d1[k] == d2[k]
    a1, a2 = P.assignment(d1), P.assignment(d2)
    assert {i: a2[i] for i in a1} == a1                         # v1 = v2 restricted to the v1 nodes
    assert {v["node"] for i, v in a2.items() if i not in a1} == set(P.T1_EXPANSION_MLGYM + P.T1_EXTRA_TASKS)


def test_v2_adds_the_four_candidates_by_the_same_rule_and_salt(monkeypatch):
    d = P.load(FILE_V2)
    assert list(P.T1_NODES) == list(P.T1_NODES_V1) + ["mlgym_titanic", "mlgym_metamaze", "gc7rc_etth1",
                                                      "gc7rc_forestcover"]
    assert sorted(d["t1"]["nodes"]) == sorted(P.T1_NODES)
    for node in P.T1_NODES:
        order = sorted(range(5101, 5113), key=lambda s: hashlib.sha256(f"c3_t1_split/v1:{node}:{s}".encode())
                       .hexdigest())
        ids = [f"{node}__s{s}" for s in order]
        assert d["t1"]["nodes"][node] == {"test": ids[:6], "dev": ids[6:8], "train": ids[8:]}
    monkeypatch.syspath_prepend(str(REPO / "sweep2" / "t1_tasl"))
    spec = json.loads((REPO / "sweep2/t1_tasl/g1b_tasl_x_spec.json").read_text())
    assert [n["node"] for n in spec["nodes"]] == list(P.T1_EXPANSION_MLGYM + P.T1_EXTRA_TASKS)
    assign = P.assignment(d)
    assert len(assign) == 8 * 18 + 12 * 12
    assert d["supersedes"] == {"path": "r1/c3/splits/c3_p3_split_v1.json", "sha256": P.P3_SPLIT_SHA256,
                               "identity": d["supersedes"]["identity"]}


def test_v2_membership_is_static_and_gates_the_1gc_nodes():
    m = P.load(FILE_V2)["t1"]["membership"]
    assert sorted(m) == sorted(P.T1_NODES)
    for n in P.T1_NODES_V1:
        assert m[n]["role"] == "g5_note" and m[n]["supply"] == "arms_and_gate" and m[n]["suite"] == P.T1_SUITES[n]
    for n in P.T1_EXPANSION_MLGYM:
        assert m[n] == {"role": "g5_addendum_mlgym", "suite": "MLGym", "supply": "arms_and_gate_after_g5_addendum"}
    for n in P.T1_EXTRA_TASKS:
        assert m[n] == {"role": "g5_addendum_extra_task", "suite": None, "supply": "never"}
    assert set(P.T1_SUPPLY_NODES) == set(P.T1_NODES) - set(P.T1_EXTRA_TASKS)
    from r1.c3 import gate
    assert {v for v in P.T1_SUITES.values() if v is not None} <= set(gate.SUITES)
    # no status that changes with a run is carried (the bytes stay fixed): only the static fields
    assert all(set(v) == {"role", "suite", "supply"} for v in m.values())
    with pytest.raises(P.SplitError):
        P.role_of("openml_wdbc")


def test_suites_agree_with_g5_features(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "sweep2" / "t1_tasl"))
    import g5_features as F
    assert list(F.T1_NODE_INFO) == list(P.T1_NODES)
    for n, v in F.T1_NODE_INFO.items():
        want = None if v["suite"] in F.EXTRA_TASK_SUITES else F.SUITE_NAMES[v["suite"]]
        assert P.T1_SUITES[n] == want


def test_load_accepts_either_pinned_version_and_refuses_crossed_pins(tmp_path):
    with pytest.raises(P.SplitError, match="not the pinned"):
        P.load(FILE_V2, sha256=P.P3_SPLIT_SHA256)
    with pytest.raises(P.SplitError, match="not the pinned"):
        P.load(FILE, sha256=P.P3_SPLIT_V2_SHA256)
    bad = tmp_path / "v2.json"
    bad.write_bytes(FILE_V2.read_bytes().replace(b'"never"', b'"arms_and_gate"', 1))
    with pytest.raises(P.SplitError, match="not the pinned"):
        P.load(bad)
    for pin in ({"path": "r1/c3/splits/c3_p3_split_v1.json", "sha256": P.P3_SPLIT_V2_SHA256},
                {"path": "r1/c3/splits/c3_p3_split_v2.json"}, None, "x"):
        with pytest.raises(P.SplitError, match="not a pinned"):
            P.load_pinned(pin)
    with pytest.raises(P.SplitError):
        P.build(3)
    with pytest.raises(P.SplitError, match="pinned"):
        P.pin_of_sha("0" * 64)
    assert P.pin_of_sha(P.P3_SPLIT_V2_SHA256) == P.SPLIT_FILES[2]
    out = tmp_path / "w.json"
    assert P.main(["write", str(out), "--version", "2"]) == 0 and out.read_bytes() == FILE_V2.read_bytes()


def test_pin_for_nodes():
    assert P.pin_for_nodes(list(P.T0_NODES) + ["mlgym_fmnist"]) == P.SPLIT_FILES[1]
    assert P.pin_for_nodes(["mlgym_titanic"]) == P.SPLIT_FILES[2]
    assert P.pin_for_nodes([]) == P.SPLIT_FILES[1]
    with pytest.raises(P.SplitError, match="no split file"):
        P.pin_for_nodes(["openml_blood_transfusion"])
