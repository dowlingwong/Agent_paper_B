"""A1/A2 constants fitter (``r1.c3.arms_constants``): synthetic tables and label rows only; no real table, label
block, evaluation block or receipt is opened. AI-assisted (Claude, subagent, 23 Nov 2026)."""
import copy
import json
import random

import numpy as np
import pytest

from r1.c3 import arms_constants as AC
from r1.c3 import arms_freeze as AF
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split, release
from r1.c3.arms import ConstantPrior, RulesPrior, is_duplicate, is_noop
from r1.c3.features import FEATURES
from r1.c3.labels import INERT, N_BINS

SIG = {n: 0.01 * (1 + i / 10) for i, n in enumerate(sorted(B.ALL_T0 + ("mlgym_fmnist", "mlab_imdb")))}
ASSIGN = p3_split.assignment(p3_split.load())
T1 = B.Tier1(suites={"mlgym_fmnist": "MLGym", "mlab_imdb": "MLAgentBench"}, modes=("history",))
BASE_COMMIT = "1402f466497c29638c53a3397f44ab9a3e6717ec"


def _row(node, seed, mode, t, kind="audit", src="s2"):
    pid = f"{src}_{mode}:{node}__s{seed}:t{t:03d}"
    rng = random.Random(pid)
    f = {c: rng.random() for c in FEATURES}
    f["active_equals_incumbent"] = float(kind == "noop")
    return {"proposal_id": pid, "instance": f"{node}__s{seed}", "instance_seed": seed, "node": node,
            "source": f"{src}_{mode}", "memory_mode": mode, "budget_index": t, "sigma_node": SIG[node],
            "sigma_cmp": SIG[node] * (1.6 if t % 2 else 1.0),
            "delta_hat": 0.0 if kind == "noop" else rng.gauss(0, SIG[node]), "noop": kind == "noop",
            "duplicate": kind == "dup", "features": f, "incumbent_hash": pid + ":i", "candidate_hash": pid + ":c"}


def _label(row, kind="audit", k=5):
    if row["noop"]:
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "rule_noop",
                "delta_label": 0.0, "se_label": 0.0, "soft_parameters": {"inert": True}}
    seeds = list(B.T0_LABEL_SEEDS)
    if kind == "divergent":
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "divergent", "seeds": seeds}
    s = row["sigma_node"]
    d = random.Random("L" + row["proposal_id"]).gauss(0.2 * s, 1.3 * s)
    return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "audit", "seeds": seeds,
            "delta_label": d, "se_label": 0.004,
            "soft_parameters": {"inert": False, "sigma_node": s, "k_label": k, "delta_label": d, "se_label": 0.004}}


def _evaluation(row):
    return {"proposal_id": row["proposal_id"], "node": row["node"], "seeds": list(B.T0_EVALUATION_SEEDS),
            "delta_evaluation": random.Random("E" + row["proposal_id"]).gauss(0.0, row["sigma_node"])}


def _world(t0_nodes=B.ALL_T0, t1=T1):
    """Gate-source tables (sweep 2: T0, two modes; G.5: T1, one mode), their train/dev label rows, and (for the
    builder comparison only) every label row and the evaluation rows."""
    tables = {"sweep2": [], "g5": []}
    for src, nodes, modes, prefix in (("sweep2", t0_nodes, B.T0_MODES, "s2"),
                                      ("g5", sorted(t1.suites) if t1 else [], t1.modes if t1 else (), "g5")):
        for node in nodes:
            for inst, v in sorted(ASSIGN.items()):
                if v["node"] != node:
                    continue
                seed = int(inst.rsplit("__s", 1)[1])
                for mode in modes:
                    tables[src] += [_row(node, seed, mode, 2, "noop", prefix), _row(node, seed, mode, 3, "dup", prefix)]
                    tables[src] += [_row(node, seed, mode, t, src=prefix) for t in range(4, 10)]
    labels, every, evals = {}, {}, {}
    for src, rows in tables.items():
        live = [r for r in rows if not r["noop"] and not r["duplicate"]]
        dev_live = [r for r in live if ASSIGN[r["instance"]]["split"] == "dev"]
        # chosen per proposal id (not by position), so a world with fewer nodes has the same rows for the rest
        divergent = {r["proposal_id"] for r in dev_live if random.Random("D" + r["proposal_id"]).random() < 0.06}
        partial = {r["proposal_id"] for r in dev_live if random.Random("P" + r["proposal_id"]).random() < 0.1}
        lab = {r["proposal_id"]: _label(r, kind="divergent" if r["proposal_id"] in divergent else "audit",
                                        k=4 if r["proposal_id"] in partial else 5)
               for r in rows if not r["duplicate"]}
        every[src] = list(lab.values())
        labels[src] = [lab[r["proposal_id"]] for r in rows if r["proposal_id"] in lab
                       and ASSIGN[r["instance"]]["split"] != "test"]
        evals[src] = [_evaluation(r) for r in live]
    return {"tables": tables, "labels": labels, "every": every, "evals": evals}


@pytest.fixture(scope="module")
def world():
    return _world()


@pytest.fixture(scope="module")
def fitted(world):
    return AC.fit_sources({s: (world["tables"][s], world["labels"][s]) for s in ("sweep2", "g5")}, t1=T1,
                          assign=ASSIGN)


def _builder_prepared(world, t1=T1):
    srcs = [B.Source(s, world["tables"][s], world["every"][s], world["evals"][s]) for s in ("sweep2", "g5")
            if world["tables"][s]]
    prepared, _, _ = B._prepare(srcs, ASSIGN, t1)
    return prepared


def _bits(v):
    return np.asarray(v, dtype=np.float64).tobytes()


# ------------------------------------------------------------------------------------------- equality with fit_a2

def test_a2_vectors_equal_fit_a2_bitwise_and_a1_is_constant_prior_on_the_same_rows(world, fitted):
    vec, items = fitted
    prepared = _builder_prepared(world)
    a2 = B.fit_a2(prepared)                                   # what step 6 fits, from the builder's own rows
    dev = [{"node": r["row"]["node"], "noop": is_noop(r["row"]), "duplicate": is_duplicate(r["row"]),
            "features": r["row"].get("features", {}), "soft": r["soft"], "weight": r["weight"]}
           for r in prepared if r["split"] == "dev" and r["soft"] is not None]
    a1 = ConstantPrior().fit(dev)
    nodes = set(B.ALL_T0) | set(T1.suites)
    assert set(vec) == nodes == set(a2.by_node)
    for n in nodes:
        assert _bits(vec[n]["A2"]) == _bits(a2.by_node[n])        # bitwise, not approximately
        assert _bits(vec[n]["A1"]) == _bits(a1.by_node[n])
        assert vec[n]["A2"][INERT] == 0.0 and vec[n]["A1"][INERT] > 0   # the synthetic world has no-ops
    # the copy of fit_a2's comprehension reproduces fit_a2 on the unit's own items
    own = RulesPrior().fit(AC.fit_rows(items))
    assert all(_bits(own.by_node[n]) == _bits(vec[n]["A2"]) for n in nodes)
    # the rows entering the fit are exactly the builder's dev rows with a soft label, in proposal_id order
    want = [r["row"]["proposal_id"] for r in prepared if r["split"] == "dev"]
    assert [it["row"]["proposal_id"] for it in items] == want
    # partial labels (k_label 4) and divergent labels are present and treated as the builder treats them
    assert any(r["soft"] is None and not r["row"]["duplicate"] and not r["row"]["noop"] for r in prepared
               if r["split"] == "dev")


def test_input_order_does_not_change_a_bit(world, fitted):
    vec, _ = fitted
    shuffled = {}
    for s in ("sweep2", "g5"):
        rows, labs = copy.deepcopy(world["tables"][s]), copy.deepcopy(world["labels"][s])
        random.Random(7).shuffle(rows)
        random.Random(8).shuffle(labs)
        shuffled[s] = (rows, labs)
    again, _ = AC.fit_sources(shuffled, t1=T1, assign=ASSIGN)
    assert all(_bits(again[n][a]) == _bits(vec[n][a]) for n in vec for a in ("A1", "A2"))


def test_per_node_vectors_do_not_change_when_other_nodes_are_added(fitted):
    """The seven D.3 nodes' vectors are the same whether the fit covers them alone (the D.3 draft's G2 population,
    sweep 2 only) or all eight T0 nodes and the T1 nodes (this unit's population)."""
    vec, _ = fitted
    seven = _world(t0_nodes=AC.D3_NODES, t1=None)
    rows = seven["tables"]["sweep2"]
    items = AC.fit_items({"sweep2": AF.training_rows("sweep2", *AC.dev_only(rows, seven["labels"]["sweep2"], ASSIGN),
                                                     assign=ASSIGN)})
    alone = AC.fit(items, AC.D3_NODES)
    assert set(alone) == set(AC.D3_NODES) and "openml_wdbc" not in alone
    for n in AC.D3_NODES:
        assert _bits(alone[n]["A1"]) == _bits(vec[n]["A1"]) and _bits(alone[n]["A2"]) == _bits(vec[n]["A2"])
    # and the D.3 nodes' A2 equals fit_a2 on the seven-node builder rows too
    a2 = B.fit_a2(_builder_prepared(seven, t1=None))
    assert all(_bits(a2.by_node[n]) == _bits(vec[n]["A2"]) for n in AC.D3_NODES)


def test_train_and_test_rows_enter_no_computation(world, fitted):
    """Rows are filtered to P3 dev instances first: a malformed train label row or a train/test table row without
    features would be refused by the row construction, but is dropped before it."""
    vec, _ = fitted
    rows, labs = copy.deepcopy(world["tables"]["sweep2"]), copy.deepcopy(world["labels"]["sweep2"])
    i = next(k for k, l in enumerate(labs) if l["label_kind"] == "audit"
             and ASSIGN[l["proposal_id"].split(":")[1]]["split"] == "train")
    labs[i]["seeds"] = [7001, 7002, 7003]                       # label seeds the builder refuses
    for r in rows:
        if ASSIGN[r["instance"]]["split"] != "dev":
            del r["features"]["budget_frac_left"]
    got, _ = AC.fit_sources({"sweep2": (rows, labs), "g5": (world["tables"]["g5"], world["labels"]["g5"])},
                            t1=T1, assign=ASSIGN)
    assert all(_bits(got[n][a]) == _bits(vec[n][a]) for n in vec for a in ("A1", "A2"))
    # the same defect on a dev row is refused (the dev rows are built by the builder's construction)
    j = next(k for k, l in enumerate(labs) if l["label_kind"] == "audit"
             and ASSIGN[l["proposal_id"].split(":")[1]]["split"] == "dev")
    labs[j]["seeds"] = [7001, 7002, 7003]
    with pytest.raises(AF.ArmsFreezeError, match="label seeds"):
        AC.fit_sources({"sweep2": (rows, labs), "g5": (world["tables"]["g5"], world["labels"]["g5"])},
                       t1=T1, assign=ASSIGN)


# ------------------------------------------------------------------------------------------- refusals

def _src(world, **over):
    out = {s: (copy.deepcopy(world["tables"][s]), copy.deepcopy(world["labels"][s])) for s in ("sweep2", "g5")}
    out.update(over)
    return out


def test_no_pooled_fallback_and_no_stray_node(world):
    rows, labs = copy.deepcopy(world["tables"]["sweep2"]), copy.deepcopy(world["labels"]["sweep2"])
    # openml_sonar's dev instances keep only no-ops and duplicates: A1 has rows, A2 has none -> refused
    gone = {r["proposal_id"] for r in rows if r["node"] == "openml_sonar" and ASSIGN[r["instance"]]["split"] == "dev"
            and not r["noop"] and not r["duplicate"]}
    with pytest.raises(AF.ArmsFreezeError, match="no pooled fallback"):
        AC.fit_sources(_src(world, sweep2=([r for r in rows if r["proposal_id"] not in gone],
                                           [l for l in labs if l["proposal_id"] not in gone])), t1=T1, assign=ASSIGN)
    # a required node without rows at all
    with pytest.raises(AF.ArmsFreezeError, match="no pooled fallback"):
        AC.fit_sources(_src(world, sweep2=([r for r in rows if r["node"] != "openml_wdbc"],
                                           [l for l in labs if l["node"] != "openml_wdbc"])), t1=T1, assign=ASSIGN)
    # G.5 rows of a T1 node outside the frozen set
    with pytest.raises(AF.ArmsFreezeError, match="outside the required set"):
        AC.fit_sources(_src(world), t1=B.Tier1(suites={"mlgym_fmnist": "MLGym"}, modes=("history",)), assign=ASSIGN)
    # sources: G.5 exactly when T1 is frozen; no sweep 1
    with pytest.raises(AF.ArmsFreezeError, match="sources must be exactly"):
        AC.fit_sources(_src(world), t1=None, assign=ASSIGN)
    with pytest.raises(AF.ArmsFreezeError, match="sources must be exactly"):
        AC.fit_sources({"sweep2": (rows, labs)}, t1=T1, assign=ASSIGN)
    with pytest.raises(AF.ArmsFreezeError, match="gate sources only"):
        AC.fit_items({"sweep1": []})


def test_dev_rows_of_undeclared_memory_modes_are_refused(world):
    """A§3.1: both T0 memory modes, T1 its declared mode; the builder refuses rows of another mode."""
    rows, labs = copy.deepcopy(world["tables"]["sweep2"]), copy.deepcopy(world["labels"]["sweep2"])
    dev = next(r for r in rows if ASSIGN[r["instance"]]["split"] == "dev" and not r["noop"] and not r["duplicate"])
    dev["memory_mode"] = "history"
    with pytest.raises(AF.ArmsFreezeError, match=r"sweep2: dev rows of undeclared memory modes \['history'\]"):
        AC.fit_sources(_src(world, sweep2=(rows, labs)), t1=T1, assign=ASSIGN)
    with pytest.raises(AF.ArmsFreezeError, match=r"g5: dev rows of undeclared memory modes \['history'\]"):
        AC.fit_sources(_src(world), t1=B.Tier1(suites=T1.suites, modes=("none",)), assign=ASSIGN)
    # a train or test row of another mode is not a fit row (filtered first)
    rows, labs = copy.deepcopy(world["tables"]["sweep2"]), copy.deepcopy(world["labels"]["sweep2"])
    next(r for r in rows if ASSIGN[r["instance"]]["split"] == "train")["memory_mode"] = "history"
    assert AC.fit_sources(_src(world, sweep2=(rows, labs)), t1=T1, assign=ASSIGN)[0]


def test_refuses_test_and_evaluation_rows(world):
    rows, labs = copy.deepcopy(world["tables"]["sweep2"]), copy.deepcopy(world["labels"]["sweep2"])
    test_row = next(r for r in rows if ASSIGN[r["instance"]]["split"] == "test" and not r["noop"]
                    and not r["duplicate"])
    with pytest.raises(AF.ArmsFreezeError, match="test label"):
        AC.fit_sources(_src(world, sweep2=(rows, labs + [_label(test_row)])), t1=T1, assign=ASSIGN)
    bad = copy.deepcopy(labs)
    bad[3]["delta_evaluation"] = 0.1
    with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
        AC.fit_sources(_src(world, sweep2=(rows, bad)), t1=T1, assign=ASSIGN)
    with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
        AC.fit_sources(_src(world, sweep2=(rows, labs + [world["evals"]["sweep2"][0]])), t1=T1, assign=ASSIGN)
    bad = copy.deepcopy(labs)
    k = next(i for i, l in enumerate(bad) if l["label_kind"] == "audit")
    bad[k]["seeds"] = list(B.T0_EVALUATION_SEEDS)
    with pytest.raises(AF.ArmsFreezeError, match="evaluation seeds"):
        AC.fit_sources(_src(world, sweep2=(rows, bad)), t1=T1, assign=ASSIGN)
    bad_rows = copy.deepcopy(rows)
    bad_rows[0]["delta_true"] = 0.0
    with pytest.raises(AF.ArmsFreezeError, match="label/evaluation values"):
        AC.fit_sources(_src(world, sweep2=(bad_rows, labs)), t1=T1, assign=ASSIGN)
    bad_rows = copy.deepcopy(rows)
    bad_rows[0].update(instance_seed=99999, instance=f"{bad_rows[0]['node']}__s99999")
    with pytest.raises(AF.ArmsFreezeError, match="split file"):
        AC.fit_sources(_src(world, sweep2=(bad_rows, labs)), t1=T1, assign=ASSIGN)


def test_vector_checks():
    ok = [0.0] + [1.0 / 11] * 11
    AC.check_vector(ok, "v", a2=True)
    for bad in (ok[:-1], ok + [0.0], [float("nan")] + ok[1:], [-1e-3, 1e-3] + ok[2:], [0.5] + ok[1:],
                [True] + ok[1:], "x"):
        with pytest.raises(AF.ArmsFreezeError):
            AC.check_vector(bad, "v", a2=False)
    with pytest.raises(AF.ArmsFreezeError, match="no-op bin"):
        AC.check_vector([0.1] + [0.9 / 11] * 11, "v", a2=True)
    assert AC.same_bits(ok, list(ok)) and not AC.same_bits(ok, [np.nextafter(ok[0], 1.0)] + ok[1:])


# ------------------------------------------------------------------------------------------- the CLI and the file

def _table_dir(root, name, rows):
    d = root / name
    d.mkdir()
    (d / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return d


@pytest.fixture()
def cli(monkeypatch, world, tmp_path):
    dirs = {s: _table_dir(tmp_path, f"{s}_table", world["tables"][s]) for s in ("sweep2", "g5")}
    (dirs["sweep2"] / "configs.json").write_bytes(b'{"configs": {}}\n')       # G.5 table without one: null
    shas = {s: AF._sha_file(d / "proposals.jsonl") for s, d in dirs.items()}
    receipts = {"sweep2": "2" * 64, "g5": "5" * 64}
    calls = []

    def fake(root, source, receipt_sha256=None):
        calls.append((source, receipt_sha256))
        assert receipt_sha256 == receipts[source] and str(root).endswith(f"rel_{source}")
        return copy.deepcopy(world["labels"][source]), {
            "stage": "traindev", "source": source, "counts": {"evaluation_rows": 0},
            "inputs": {"proposals_sha256": shas[source], "label_block_sha256": "6" * 64},
            "outputs": {"label_block.traindev.jsonl": "7" * 64}}
    monkeypatch.setattr(release, "traindev_labels", fake)
    monkeypatch.setattr(AC, "_code_commit", lambda: (BASE_COMMIT, "f" * 64))
    monkeypatch.setattr(AC, "SWEEP2_PROPOSALS_SHA256", shas["sweep2"])
    (tmp_path / "t1.json").write_text(json.dumps({"suites": T1.suites, "modes": list(T1.modes), "d3_k6": False}))
    args = []
    for s in ("sweep2", "g5"):
        args += ["--release-root", f"{s}={tmp_path / f'rel_{s}'}", "--receipt", f"{s}={receipts[s]}",
                 "--table", f"{s}={dirs[s]}"]
    return {"args": ["fit", *args, "--t1", str(tmp_path / "t1.json")], "dirs": dirs, "shas": shas, "calls": calls,
            "tmp": tmp_path, "receipts": receipts}


def test_cli_writes_a_file_whose_vectors_equal_fit_a2_bitwise(cli, world, capsys):
    out = cli["tmp"] / "const" / "C.json"
    assert AC.main(cli["args"] + ["--out", str(out)]) == 0
    printed = json.loads(capsys.readouterr().out)
    data = out.read_bytes()
    assert printed["sha256"] == AF._sha(data) and sorted(cli["calls"]) == [("g5", "5" * 64), ("sweep2", "2" * 64)]
    c = AC.parse(data)
    assert c["fitter"] == {"path": AC.FITTER_PATH, "sha256": "f" * 64, "code_commit": BASE_COMMIT}
    assert c["sources"]["sweep2"] == {"receipt_sha256": "2" * 64, "traindev_partition_sha256": "7" * 64,
                                      "label_block_sha256": "6" * 64, "proposals_sha256": cli["shas"]["sweep2"],
                                      "configs_sha256": AF._sha(b'{"configs": {}}\n')}
    assert c["sources"]["g5"]["configs_sha256"] is None
    assert c["toolchain"] == AC.toolchain() == printed["toolchain"]               # M3: the running interpreter
    from r1.harness import REPO
    assert c["gate_input_builder"] == {"path": AC.BUILDER_PATH, "sha256": AF._sha_file(REPO / AC.BUILDER_PATH)}
    assert c["t1"] == {"suites": T1.suites, "modes": ["history"], "d3_k6": False}
    a2 = B.fit_a2(_builder_prepared(world))
    for n, e in c["nodes"].items():                                  # after the JSON round trip
        assert _bits(e["A2"]) == _bits(a2.by_node[n]) and e["sigma_node"] == SIG[n]
        assert e["tier"] == ("T1" if n in T1.suites else "T0")
        assert e["dev_instances"] == sorted(i for i, v in ASSIGN.items() if v["node"] == n and v["split"] == "dev")
        assert e["rows"]["A2"] < e["rows"]["A1"] < e["rows"]["dev"]
    assert c["d3_nodes"] == list(B.SEVEN_T0) and c["t0_nodes"] == list(B.ALL_T0)
    with pytest.raises(AF.ArmsFreezeError, match="written once"):
        AC.main(cli["args"] + ["--out", str(out)])


def test_cli_refusals(cli, monkeypatch):
    tmp = cli["tmp"]
    with pytest.raises(AF.ArmsFreezeError, match="pinned sweep-2 table"):
        monkeypatch.setattr(AC, "SWEEP2_PROPOSALS_SHA256", "0" * 64)
        AC.main(cli["args"] + ["--out", str(tmp / "a.json")])
    monkeypatch.setattr(AC, "SWEEP2_PROPOSALS_SHA256", cli["shas"]["sweep2"])
    real = AF._prereg_block
    with pytest.raises(AF.ArmsFreezeError, match="preregistration binds"):     # fit_a2 must be the bound builder
        monkeypatch.setattr(AF, "_prereg_block", lambda repo: {"gate_input_builder_sha256": "0" * 64})
        AC.main(cli["args"] + ["--out", str(tmp / "g.json")])
    monkeypatch.setattr(AF, "_prereg_block", real)
    with pytest.raises(AF.ArmsFreezeError, match="receipt released"):
        cli["shas"]["g5"] = "0" * 64
        AC.main(cli["args"] + ["--out", str(tmp / "b.json")])
    with pytest.raises(AF.ArmsFreezeError, match="sweep 1 does not enter"):
        AC.main(cli["args"] + ["--release-root", "sweep1=x", "--receipt", "sweep1=" + "1" * 64,
                               "--table", "sweep1=y", "--out", str(tmp / "c.json")])
    args = [a for a in cli["args"]]
    i = args.index("--t1")
    with pytest.raises(AF.ArmsFreezeError, match="sources must be exactly"):     # G.5 given, no frozen T1 set
        cli["shas"]["g5"] = AF._sha_file(cli["dirs"]["g5"] / "proposals.jsonl")
        AC.main(args[:i] + args[i + 2:] + ["--out", str(tmp / "d.json")])
    for name in ("label_block.jsonl", "evaluation_block.all.jsonl", "label_block.test.jsonl"):
        with pytest.raises(AF.ArmsFreezeError, match="not arms inputs"):
            AC.main(cli["args"] + ["--out", str(tmp / name)])
    bad = [a.replace(f"sweep2={tmp / 'rel_sweep2'}", f"sweep2={tmp / 'sweep2' / 'test'}") for a in cli["args"]]
    with pytest.raises(AF.ArmsFreezeError, match="not arms inputs"):
        AC.main(bad + ["--out", str(tmp / "e.json")])
    monkeypatch.setattr(release, "traindev_labels",
                        lambda *a, **k: ([], {"stage": "traindev", "source": "sweep2",
                                              "counts": {"evaluation_rows": 4}}))
    with pytest.raises(AF.ArmsFreezeError, match="without evaluation rows"):
        AC.main(cli["args"] + ["--out", str(tmp / "f.json")])
    assert not any((tmp / n).exists() for n in ("a.json", "b.json", "c.json", "d.json", "e.json", "f.json", "g.json"))


def test_parse_refuses_malformed_files(fitted):
    vec, items = fitted
    meta = {s: {"receipt_sha256": "1" * 64, "traindev_partition_sha256": "2" * 64, "label_block_sha256": "3" * 64,
                "proposals_sha256": "4" * 64, "configs_sha256": None} for s in ("sweep2", "g5")}
    doc = AC.document(vec, items, sources_meta=meta, t1=T1,
                      fitter={"path": AC.FITTER_PATH, "sha256": "f" * 64, "code_commit": BASE_COMMIT},
                      builder_sha256="e" * 64)
    AC.parse(AF._dump(doc))
    muts = [lambda d: d.__setitem__("schema", "other/v1"),
            lambda d: d["fitter"].__setitem__("path", "r1/c3/other.py"),
            lambda d: d["fitter"].__setitem__("code_commit", "abc"),
            lambda d: d.__setitem__("fit_population", "train"),
            lambda d: d["split_file"].__setitem__("sha256", "0" * 64),
            lambda d: d["sources"].pop("g5"),
            lambda d: d["sources"]["sweep2"].__setitem__("receipt_sha256", "x"),
            lambda d: d["nodes"].pop("openml_wdbc"),
            lambda d: d["nodes"]["digits_mlp"]["A2"].__setitem__(0, 0.01),
            lambda d: d["nodes"]["digits_mlp"]["A1"].append(0.0),
            lambda d: d["nodes"]["digits_mlp"].__setitem__("dev_instances", []),
            # M3: the toolchain record; N2: builder pin, rules, row order, node lists, tier, source, counts
            lambda d: d.pop("toolchain"),
            lambda d: d["toolchain"].pop("scipy"),
            lambda d: d["toolchain"].__setitem__("interpreter", ""),
            lambda d: d["gate_input_builder"].__setitem__("path", "r1/c3/gate.py"),
            lambda d: d["gate_input_builder"].__setitem__("sha256", "b"),
            lambda d: d["rules"].__setitem__("A1", "other"),
            lambda d: d.__setitem__("row_order", "instance"),
            lambda d: d.__setitem__("t0_nodes", list(B.SEVEN_T0)),
            lambda d: d.__setitem__("d3_nodes", list(B.ALL_T0)),
            lambda d: d["nodes"]["digits_mlp"].__setitem__("tier", "T1"),
            lambda d: d["nodes"]["mlgym_fmnist"].__setitem__("source", "sweep2"),
            lambda d: d["nodes"]["digits_mlp"]["rows"].__setitem__("A2", d["nodes"]["digits_mlp"]["rows"]["A1"] + 1),
            lambda d: d["nodes"]["digits_mlp"]["rows"].__setitem__("A2", True),
            lambda d: d["sources"]["sweep2"].__setitem__("configs_sha256", "x"),
            lambda d: d["sources"]["sweep2"].pop("configs_sha256")]
    for m in muts:
        d = copy.deepcopy(doc)
        m(d)
        with pytest.raises(AF.ArmsFreezeError):
            AC.parse(json.dumps(d).encode())
    with pytest.raises(AF.ArmsFreezeError, match="not JSON"):
        AC.parse(b"{")
