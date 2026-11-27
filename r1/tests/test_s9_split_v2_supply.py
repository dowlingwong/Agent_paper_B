"""R1-G5-S9 (1)-(2) on the consumers of the split file: v2 admitted beside v1, the MLGym joiners supplied as suite
MLGym, the 1GC extra tasks refused by the arms freeze and the SFT builder (fail closed). Synthetic only: no table,
label or evaluation value is read."""
import sys
from pathlib import Path

import pytest

from r1.c3 import arms_constants as AC
from r1.c3 import arms_freeze as AF
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split as P
from r1.c3.train import sft_data as SD

sys.path.insert(0, str(Path(__file__).parent))
import test_c3_arms_freeze as TA  # noqa: E402  (the arms-frozen record fixture)

V1, V2 = P.SPLIT_FILES[1], P.SPLIT_FILES[2]
A2 = P.assignment(P.load(P.V2_PATH))


def _traindev(node):
    return sorted(i for i, v in A2.items() if v["node"] == node and v["split"] in ("train", "dev"))


def _t1(suites, instances):
    return {"suites": suites, "modes": ["history"], "d3_k6": False, "instances": instances}


# ------------------------------------------------------------------------------------------------- sft_data

def test_sft_data_admits_v1_and_v2_and_nothing_else():
    assert SD._signed_split({"split_file": dict(V1)}) and SD._signed_split({"split_file": dict(V2)})
    assert not SD._signed_split({"split_file": {"path": V1["path"], "sha256": V2["sha256"]}})
    assert not SD._signed_split({"split_file": {"path": V2["path"], "sha256": "0" * 64}})
    got = SD._split_file_assignment({"mlgym_titanic__s5101"}, {"split_file": dict(V2)})
    assert got["mlgym_titanic__s5101"] in ("train", "val", "test")
    with pytest.raises(SD.SFTDataError, match="outside the P3 split file"):
        SD._split_file_assignment({"mlgym_titanic__s5101"}, {"split_file": dict(V1)})
    with pytest.raises(SD.SFTDataError, match="not the signed"):
        SD._split_file_assignment(set(), {"split_file": {"path": V1["path"], "sha256": V2["sha256"]}})
    # v1's assignment of its own instances is v2's (byte-identical entries)
    v1i = set(P.assignment(P.load()))
    a1 = SD._split_file_assignment(v1i, {"split_file": dict(V1)}, universe=v1i)
    a2 = SD._split_file_assignment(v1i, {"split_file": dict(V2)}, universe=v1i)
    assert a1 == a2


def test_p3_universe_reads_the_named_file():
    assert SD.p3_universe({"mlgym_titanic"}) == []                       # v1 by default: not in it
    assert SD.p3_universe({"mlgym_titanic"}, V2) == sorted(i for i, v in A2.items() if v["node"] == "mlgym_titanic")
    assert len(SD.p3_universe({"mlgym_titanic"}, V2)) == 12
    assert SD.p3_universe({"mlgym_fmnist"}, V1) == SD.p3_universe({"mlgym_fmnist"}, V2)
    with pytest.raises(SD.SFTDataError, match="not a signed P3 split file"):
        SD.p3_universe({"mlgym_fmnist"}, {"path": V1["path"], "sha256": V2["sha256"]})


class _Synthetic:
    def provenance(self):
        return {"kind": "synthetic"}

    def label_records(self):
        return []


@pytest.mark.parametrize("node", P.T1_EXTRA_TASKS)
def test_sft_data_refuses_an_extra_task_row(node, tmp_path):
    with pytest.raises(SD.SFTDataError, match="extra tasks"):
        SD.refuse_extra_tasks(["mlgym_fmnist", node])
    rows = [{"proposal_id": f"g5.history:{node}__s5101:t1", "node": node, "features": {}}]
    with pytest.raises(SD.SFTDataError, match="extra tasks"):
        SD.build_sft_data(rows, _Synthetic(), {}, tmp_path / "out")
    with pytest.raises(SD.SFTDataError, match="extra tasks"):
        SD._t1_forms({"p": rows[0]}, {"p": (object(), None)})
    SD.refuse_extra_tasks(list(P.T1_SUPPLY_NODES))                      # the eight and the MLGym joiners pass


# ------------------------------------------------------------------------------------------------- arms_freeze

@pytest.mark.parametrize("node", P.T1_EXTRA_TASKS)
def test_arms_freeze_refuses_an_extra_task_in_the_t1_set_labels_and_rows(node):
    for suite in ("MLGym", "MLAgentBench", "autoresearch"):
        with pytest.raises(AF.ArmsFreezeError, match="extra task"):
            AF._check_t1(_t1({node: suite}, _traindev(node)), dict(V2))
    inst = _traindev(node)[0]
    with pytest.raises(AF.ArmsFreezeError, match="extra task"):
        AF.check_label_rows([{"proposal_id": f"g5:{inst}:t1", "seeds": [7001]}], A2)
    row = {"proposal_id": f"g5:{inst}:t1", "node": node, "features": {}}
    with pytest.raises(AF.ArmsFreezeError, match="extra task"):
        AF.training_rows("g5", [row], [], assign=A2)


@pytest.mark.parametrize("node", P.T1_EXPANSION_MLGYM)
def test_an_mlgym_joiner_is_frozen_as_mlgym_under_v2_only(node):
    AF._check_t1(_t1({node: "MLGym", "mlgym_fmnist": "MLGym"}, _traindev(node) + TA.T1_INST), dict(V2))
    with pytest.raises(AF.ArmsFreezeError, match="its suite is MLGym"):
        AF._check_t1(_t1({node: "MLAgentBench"}, _traindev(node)), dict(V2))
    with pytest.raises(AF.ArmsFreezeError, match="not a split-file instance"):      # v1 does not hold it
        AF._check_t1(_t1({node: "MLGym"}, _traindev(node)), dict(V1))
    with pytest.raises(AF.ArmsFreezeError, match="split_file"):
        AF._check_t1(_t1({node: "MLGym"}, _traindev(node)), {"path": V1["path"], "sha256": V2["sha256"]})


def test_the_eight_keep_their_t1_check_and_their_suites():
    AF._check_t1(_t1({"mlgym_fmnist": "MLGym"}, TA.T1_INST))                   # v1 by default, as before
    AF._check_t1(_t1({"mlgym_fmnist": "MLGym"}, TA.T1_INST), dict(V1))
    AF._check_t1(_t1({"mlgym_fmnist": "MLGym"}, TA.T1_INST), dict(V2))
    with pytest.raises(AF.ArmsFreezeError, match="its suite is MLGym"):
        AF._check_t1(_t1({"mlgym_fmnist": "autoresearch"}, TA.T1_INST))


def test_the_record_may_cite_v2_and_then_needs_the_published_amendment(monkeypatch):
    rec = TA._record()
    rec["split_file"] = dict(V2)
    assert AF.check_record(rec, plan_text=TA.PLAN)["pass"]               # structure: v2 is a pinned split file
    seen = []
    from r1.c3 import release

    def no_amendment(root=None):
        seen.append(root)
        raise release.ReleaseStop("STOP: the split file v2 needs the published PRE-SPLIT amendment")
    monkeypatch.setattr(release, "split_v2_amendment", no_amendment)
    with pytest.raises(AF.ArmsFreezeError, match="PRE-SPLIT amendment"):
        AF.check_record(rec, plan_text=TA.PLAN, verify_committed=True)
    assert seen
    rec["split_file"] = {"path": V2["path"], "sha256": V1["sha256"]}
    with pytest.raises(AF.ArmsFreezeError, match="split_file must be one of"):
        AF.check_record(rec, plan_text=TA.PLAN)


def test_reads_use_v2_whose_v1_entries_are_unchanged():
    a1 = P.assignment(P.load())
    assert {i: AF._assign()[i] for i in a1} == a1


# ------------------------------------------------------------------------------------------------- arms_constants

def test_the_constants_file_names_v1_for_the_eight_and_v2_with_a_joiner():
    """``arms_constants.document`` writes ``pin_for_nodes`` of the T1 set; ``parse`` requires it
    (test_c3_arms_constants::test_parse_refuses_malformed_files has the refusals)."""
    assert P.pin_for_nodes({"mlgym_fmnist", "mlab_imdb"}) == V1
    assert P.pin_for_nodes({"mlgym_fmnist", "mlgym_metamaze"}) == V2
    assert AC.SPLIT_PATH == V1["path"]


def test_gate_tier1_takes_the_mlgym_joiners():
    B.Tier1(suites={"mlgym_titanic": "MLGym", "mlgym_metamaze": "MLGym"}, modes=("history",))


@pytest.mark.parametrize("node", P.T1_EXTRA_TASKS)
def test_the_t1_prompt_form_refuses_a_build_naming_an_extra_task(node):
    from r1.c3.train import serialize_t1 as S1
    build = {"schema": S1.TABLE_SCHEMA_A,
             "featurizer": {"version": S1.G5F.FEATURIZER, "fields": list(S1.G5F.FEATURES_V3),
                            "missing_categorical": S1.G5F.MISSING_CATEGORICAL,
                            "no_t1_source": list(S1.G5F.NO_T1_SOURCE)},
             "nodes": {node: {"suite": "1gc7rc", "gate_suite": None, "metric_direction": "minimize"}}}
    with pytest.raises(S1.T1PromptError, match="extra task"):
        S1.check_build(build)
    assert set(S1.T1_NODES) == set(P.T1_NODES)
