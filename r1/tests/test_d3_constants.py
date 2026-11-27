"""D.3 G2 constants fitter (``r1.c3.d3_constants``): synthetic sweep-2 tables and train/dev label rows only; no real
table, label block, evaluation block or receipt is opened. The pinned noise summary (noise-floor constants, no label) is
read for sigma_node. AI-assisted (Claude, local worker, 27 Nov 2026)."""
import copy
import json
from pathlib import Path
import random
from fractions import Fraction

import numpy as np
import pytest

from r1.c3 import arms_constants as AC
from r1.c3 import arms_freeze as AF
from r1.c3 import d3_constants as D
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split, release
from r1.c3.features import FEATURES
from r1.harness import REPO

ASSIGN = p3_split.assignment(p3_split.load())
NOISE = D.load_noise(REPO)
SIG = {n: NOISE[n]["sigma_node"] for n in B.ALL_T0}
BASE_COMMIT = "1402f466497c29638c53a3397f44ab9a3e6717ec"


# ------------------------------------------------------------------------------------------- the search, by hand

def test_hand_computed_search():
    """sigma = 0.01; rows (w, delta_label, delta_hat). Kept iff delta_hat > c * 0.01:
    c <= -0.65: all four, U = 0.010 - 0.020 + 0.003 + 0.001 = -0.006;  -0.60 .. 0.40: three, U = -0.007;
    0.45 .. 1.20: two, U = -0.010;  1.25 .. 2.50: one, U = +0.010;  2.55 .. 3.00: none, U = 0.
    Maximum +0.010 on c in [1.25, 2.50]; smallest |c| -> c = 1.25, eta = 1.25 * 0.01."""
    e = [(1.0, 0.010, 0.0253), (1.0, -0.020, 0.0123), (1.0, 0.003, 0.0042), (1.0, 0.001, -0.0063)]
    r = D.ladder_search(e, 0.01)
    assert r["c"] == 1.25 and r["eta"] == 1.25 * 0.01 and r["u_max"] == 0.010
    by_c = {row["c"]: row for row in r["search"]}
    want = {-3.0: (-0.006, 4), -0.65: (-0.006, 4), -0.6: (-0.007, 3), 0.4: (-0.007, 3), 0.45: (-0.010, 2),
            1.2: (-0.010, 2), 1.25: (0.010, 1), 2.5: (0.010, 1), 2.55: (0.0, 0), 3.0: (0.0, 0)}
    for c, (u, k) in want.items():
        assert by_c[c]["keeps"] == k and by_c[c]["U"] == pytest.approx(u, abs=1e-15), c
    assert [row["c"] for row in r["search"]] == list(D.LADDER_GRID)
    assert all(row["eta"] == float(row["c"]) * 0.01 for row in r["search"])
    # row order does not change a bit (fsum)
    assert D.ladder_search(list(reversed(e)), 0.01) == r


def test_ties_smallest_abs_c_then_smallest_c():
    """U(-0.50) = U(+0.50) = 0.003 is the maximum: |c| ties, so the smaller c, -0.50, is chosen.
    A (-0.0052, -0.003) kept iff c <= -0.55; B (-0.0048, +0.003) iff c <= -0.50; C (+0.0048, -0.003) iff c <= 0.45;
    D (+0.0052, +0.003) iff c <= 0.50. U: c <= -0.55: 0; -0.50: B+C+D = 0.003; -0.45 .. 0.45: C+D = 0;
    0.50: D = 0.003; >= 0.55: 0."""
    e = [(1.0, -0.003, -0.0052), (1.0, 0.003, -0.0048), (1.0, -0.003, 0.0048), (1.0, 0.003, 0.0052)]
    r = D.ladder_search(e, 0.01)
    by_c = {row["c"]: row["U"] for row in r["search"]}
    assert by_c[-0.5] == by_c[0.5] == 0.003 and by_c[0.0] == 0.0 and by_c[-0.55] == 0.0
    assert r["c"] == -0.5 and r["eta"] == -0.5 * 0.01
    # a flat objective picks c = 0 (A0's rule); all-negative labels: keep nothing -> the smallest c keeping none
    assert D.ladder_search([(1.0, 0.0, 0.002), (1.0, 0.0, -0.001)], 0.01)["c"] == 0.0
    neg = D.ladder_search([(1.0, -0.004, 0.0213), (1.0, -0.001, -0.0111)], 0.01)
    assert neg["c"] == 2.15 and neg["u_max"] == 0.0        # 2.15 * 0.01 >= 0.0213 > 2.10 * 0.01: nothing kept


def test_grid_and_eta():
    assert D.LADDER_GRID == tuple(round(-3.0 + 0.05 * k, 2) for k in range(121))   # d3_controllers.LADDER_GRID
    assert len(set(D.LADDER_GRID)) == 121 and D.LADDER_GRID[59:62] == (-0.05, 0.0, 0.05)
    assert D.ladder_eta(-1.35, 0.02) == -1.35 * 0.02
    for c in (0.07, 3.05, -3.05, 1.251):
        with pytest.raises(AF.ArmsFreezeError, match="grid"):
            D.ladder_eta(c, 0.01)
    with pytest.raises(AF.ArmsFreezeError, match="sigma_node"):
        D.ladder_eta(0.5, 0.0)
    with pytest.raises(AF.ArmsFreezeError, match="no eta"):
        D.ladder_search([], 0.01)
    with pytest.raises(AF.ArmsFreezeError, match="finite"):
        D.ladder_search([(1.0, float("nan"), 0.0)], 0.01)


# ------------------------------------------------------------------------------------------- a synthetic world

def _row(node, seed, mode, t, kind="audit"):
    pid = f"s2_{mode}:{node}__s{seed}:t{t:03d}"
    rng = random.Random(pid)
    f = {c: rng.random() for c in FEATURES}
    f["active_equals_incumbent"] = float(kind == "noop")
    return {"proposal_id": pid, "instance": f"{node}__s{seed}", "instance_seed": seed, "node": node,
            "source": f"s2_{mode}", "memory_mode": mode, "budget_index": t, "sigma_node": SIG[node],
            "sigma_cmp": SIG[node], "delta_hat": 0.0 if kind == "noop" else rng.gauss(0.1 * SIG[node], SIG[node]),
            "noop": kind == "noop", "duplicate": kind == "dup", "features": f,
            "incumbent_hash": pid + ":i", "candidate_hash": pid + ":c"}


def _label(row, kind="audit", k=5):
    if row["noop"]:
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "rule_noop",
                "delta_label": 0.0, "se_label": 0.0, "soft_parameters": {"inert": True}}
    seeds = list(B.T0_LABEL_SEEDS)
    if kind == "divergent":
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "divergent", "seeds": seeds}
    s = row["sigma_node"]
    # correlated with delta_hat, so the search has an interior optimum on some nodes
    d = 0.6 * row["delta_hat"] + random.Random("L" + row["proposal_id"]).gauss(-0.1 * s, s)
    return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "audit", "seeds": seeds,
            "delta_label": d, "se_label": 0.004,
            "soft_parameters": {"inert": False, "sigma_node": s, "k_label": k, "delta_label": d, "se_label": 0.004}}


def _world(nodes=B.ALL_T0):
    rows = []
    for node in nodes:
        for inst, v in sorted(ASSIGN.items()):
            if v["node"] != node:
                continue
            seed = int(inst.rsplit("__s", 1)[1])
            for mode in B.T0_MODES:
                rows += [_row(node, seed, mode, 2, "noop"), _row(node, seed, mode, 3, "dup")]
                rows += [_row(node, seed, mode, t) for t in range(4, 12)]
    live = [r for r in rows if not r["noop"] and not r["duplicate"]]
    dev = [r for r in live if ASSIGN[r["instance"]]["split"] == "dev"]
    divergent = {r["proposal_id"] for r in dev if random.Random("D" + r["proposal_id"]).random() < 0.06}
    partial = {r["proposal_id"] for r in dev if random.Random("P" + r["proposal_id"]).random() < 0.1}
    lab = {r["proposal_id"]: _label(r, "divergent" if r["proposal_id"] in divergent else "audit",
                                    4 if r["proposal_id"] in partial else 5) for r in rows if not r["duplicate"]}
    labels = [lab[r["proposal_id"]] for r in rows if r["proposal_id"] in lab and ASSIGN[r["instance"]]["split"] != "test"]
    return {"rows": rows, "labels": labels, "test_labels": [lab[r["proposal_id"]] for r in rows if r["proposal_id"]
                                                            in lab and ASSIGN[r["instance"]]["split"] == "test"]}


@pytest.fixture(scope="module")
def world():
    return _world()


@pytest.fixture(scope="module")
def fitted(world):
    return D.fit_d3(world["rows"], world["labels"], NOISE, assign=ASSIGN)


def _bits(v):
    return np.asarray(v, dtype=np.float64).tobytes()


def _reference(world, node):
    """An independent implementation of §5.6 in exact rational arithmetic, from the raw world rows: the node's P3 dev
    rows that are not duplicates and whose label is rule_noop (delta 0) or audit."""
    lab = {l["proposal_id"]: l for l in world["labels"]}
    ent = []
    for r in world["rows"]:
        if r["node"] != node or ASSIGN[r["instance"]]["split"] != "dev" or r["duplicate"]:
            continue
        l = lab[r["proposal_id"]]
        if l["label_kind"] == "divergent":
            continue
        ent.append((Fraction(0) if r["noop"] else Fraction(l["delta_label"]), r["delta_hat"]))
    best = None
    for k in range(121):
        c = round(-3.0 + 0.05 * k, 2)
        eta = c * SIG[node]
        u = sum((d for d, h in ent if h > eta), Fraction(0))
        key = (-u, abs(c), c)
        if best is None or key < best[0]:
            best = (key, c, eta)
    return best[1], best[2], len(ent)


def test_ladder_equals_an_exact_reference_on_every_node(world, fitted):
    lad = fitted["ladder"]
    assert set(lad) == set(D.D3_NODES) and "openml_wdbc" not in lad
    chosen = set()
    for n in D.D3_NODES:
        c, eta, rows = _reference(world, n)
        assert lad[n]["c"] == c and lad[n]["eta"] == eta == D.ladder_eta(c, SIG[n]), n
        assert lad[n]["rows"] == rows and lad[n]["sigma_node"] == SIG[n] and lad[n]["noop_rows"] > 0
        chosen.add(c)
    assert len(chosen) > 1 and any(abs(c) not in (0.0, 3.0) for c in chosen)   # the world is not degenerate


def test_a1_a2_equal_the_arms_constants_fit_bitwise_and_the_record_check_accepts_the_file(world, fitted):
    """The seven nodes' vectors equal those arms_constants fits for the arms-frozen record (eight T0 nodes), and
    arms_freeze._check_d3_vectors accepts the D.3 file against them (R1-D3-MIN; §10)."""
    vec8, _ = AC.fit_sources({"sweep2": (world["rows"], world["labels"])}, t1=None, assign=ASSIGN)
    for n in D.D3_NODES:
        for arm in ("A1", "A2"):
            assert _bits(fitted["vectors"][n][arm]) == _bits(vec8[n][arm])
    doc = _doc(fitted)
    ra = {arm: {"vectors": {n: [float(x) for x in vec8[n][arm]] for n in vec8}} for arm in ("A1", "A2")}
    AF._check_d3_vectors(ra, AF._dump(doc))
    ra["A2"]["vectors"]["openml_sonar"][1] = float(np.nextafter(ra["A2"]["vectors"]["openml_sonar"][1], 1.0))
    with pytest.raises(AF.ArmsFreezeError, match="differ from the D.3 constants file"):
        AF._check_d3_vectors(ra, AF._dump(doc))


def test_other_rows_enter_no_computation(world, fitted):
    """Rows of train and test instances and of openml_wdbc are dropped before any use: defects in them (no features,
    other delta_hat, malformed label seeds) change nothing."""
    rows, labs = copy.deepcopy(world["rows"]), copy.deepcopy(world["labels"])
    for r in rows:
        if ASSIGN[r["instance"]]["split"] != "dev" or r["node"] == "openml_wdbc":
            del r["features"]["budget_frac_left"]
            r["delta_hat"] = 9.0
    for l in labs:
        if l.get("label_kind") == "audit" and (ASSIGN[l["proposal_id"].split(":")[1]]["split"] != "dev"
                                               or l["node"] == "openml_wdbc"):
            l["seeds"] = [7001, 7002]
            l["delta_label"] = 1.0
    again = D.fit_d3(rows, labs, NOISE, assign=ASSIGN)
    assert _dump_fit(again) == _dump_fit(fitted)
    # a seven-node world gives the same bytes
    seven = _world(nodes=D.D3_NODES)
    assert _dump_fit(D.fit_d3(seven["rows"], seven["labels"], NOISE, assign=ASSIGN)) == _dump_fit(fitted)


def test_input_order_does_not_change_a_byte(world, fitted):
    rows, labs = copy.deepcopy(world["rows"]), copy.deepcopy(world["labels"])
    random.Random(3).shuffle(rows)
    random.Random(4).shuffle(labs)
    assert _dump_fit(D.fit_d3(rows, labs, NOISE, assign=ASSIGN)) == _dump_fit(fitted)


def test_refusals(world):
    rows, labs = world["rows"], world["labels"]
    with pytest.raises(AF.ArmsFreezeError, match="test label"):
        D.fit_d3(rows, labs + world["test_labels"][:1], NOISE, assign=ASSIGN)
    bad = copy.deepcopy(labs)
    next(l for l in bad if l["label_kind"] == "audit")["delta_evaluation"] = 0.1
    with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
        D.fit_d3(rows, bad, NOISE, assign=ASSIGN)
    bad = copy.deepcopy(labs)
    next(l for l in bad if l["label_kind"] == "audit")["seeds"] = list(B.T0_EVALUATION_SEEDS)
    with pytest.raises(AF.ArmsFreezeError, match="evaluation seeds"):
        D.fit_d3(rows, bad, NOISE, assign=ASSIGN)
    bad_rows = copy.deepcopy(rows)
    bad_rows[5]["delta_true"] = 0.0
    with pytest.raises(AF.ArmsFreezeError, match="label/evaluation values"):
        D.fit_d3(bad_rows, labs, NOISE, assign=ASSIGN)
    # sigma_node of the table differs from the noise table's (even by one ulp)
    noise = copy.deepcopy(NOISE)
    noise["openml_sonar"]["sigma_node"] = float(np.nextafter(noise["openml_sonar"]["sigma_node"], 1.0))
    with pytest.raises(AF.ArmsFreezeError, match="differs from the noise table"):
        D.fit_d3(rows, labs, noise, assign=ASSIGN)
    noise = {n: v for n, v in NOISE.items() if n != "tabular_mlp"}
    with pytest.raises(AF.ArmsFreezeError, match="no noise constants"):
        D.fit_d3(rows, labs, noise, assign=ASSIGN)
    # a non-finite logged delta_hat on a LADDER row
    bad_rows = copy.deepcopy(rows)
    next(r for r in bad_rows if r["node"] == "digits_mlp" and ASSIGN[r["instance"]]["split"] == "dev"
         and not r["noop"] and not r["duplicate"])["delta_hat"] = None
    with pytest.raises(AF.ArmsFreezeError, match="finite"):
        D.fit_d3(bad_rows, labs, NOISE, assign=ASSIGN)
    # a dev row of an undeclared memory mode
    bad_rows = copy.deepcopy(rows)
    next(r for r in bad_rows if r["node"] == "digits_mlp" and ASSIGN[r["instance"]]["split"] == "dev")[
        "memory_mode"] = "history"
    with pytest.raises(AF.ArmsFreezeError, match="undeclared memory modes"):
        D.fit_d3(bad_rows, labs, NOISE, assign=ASSIGN)
    # a D.3 node without a labelled non-inert dev proposal: no constant (STOP, no pooled fallback)
    gone = {r["proposal_id"] for r in rows if r["node"] == "openml_climate" and not r["noop"] and not r["duplicate"]}
    with pytest.raises(AF.ArmsFreezeError, match="no pooled fallback"):
        D.fit_d3([r for r in rows if r["proposal_id"] not in gone], [l for l in labs if l["proposal_id"] not in gone],
                 NOISE, assign=ASSIGN)


def test_weight_other_than_one_is_refused(world, fitted):
    items = copy.deepcopy(fitted["items"])
    it = next(i for i in items if i["row"]["node"] == "digits_mlp" and i["soft"] is not None)
    it["weight"] = 0.5
    trows = AF.training_rows("sweep2", *D.d3_dev_rows(world["rows"], world["labels"], ASSIGN), assign=ASSIGN)
    with pytest.raises(AF.ArmsFreezeError, match="weight"):
        D.ladder_entries(items, trows, world["rows"], world["labels"], "digits_mlp")


# ------------------------------------------------------------------------------------------- the document

META = {"receipt_sha256": "2" * 64, "traindev_partition_sha256": "7" * 64, "label_block_sha256": "6" * 64,
        "proposals_sha256": D.SWEEP2_PROPOSALS_SHA256, "configs_sha256": D.SWEEP2_CONFIGS_SHA256}
FITTER = {"path": D.FITTER_PATH, "sha256": "f" * 64, "code_commit": BASE_COMMIT}
A1A2 = {"path": AC.FITTER_PATH, "sha256": "a" * 64}
TOOLS = {"python": "3.x", "numpy": "1.x", "scipy": "1.x", "interpreter": "/py"}


def _doc(fit):
    return D.document(fit, source_meta=META, fitter=FITTER, a1a2_fitter=A1A2, builder_sha256="e" * 64, tools=TOOLS)


def _dump_fit(fit):
    return AF._dump(_doc(fit))


def test_document_round_trip_and_parse_refusals(fitted):
    doc = _doc(fitted)
    p = D.parse(AF._dump(doc))
    assert p["ladder_c"] == {n: fitted["ladder"][n]["c"] for n in D.D3_NODES}
    assert D.ladder_constant(p, "openml_sonar") == (fitted["ladder"]["openml_sonar"]["c"],
                                                    fitted["ladder"]["openml_sonar"]["eta"])
    for n in D.D3_NODES:
        assert _bits(p["vectors"]["A2"][n]) == _bits(fitted["vectors"][n]["A2"])
        assert p["nodes"][n]["noise"] == {k: NOISE[n][k] for k in D.NOISE_KEYS}
    n0 = "openml_ionosphere"
    lad = doc["nodes"][n0]["LADDER"]
    other = next(c for c in D.LADDER_GRID if c != lad["c"])

    def setc(d):
        d["nodes"][n0]["LADDER"].update(c=other, eta=D.ladder_eta(other, d["nodes"][n0]["sigma_node"]))
    muts = [lambda d: d.__setitem__("schema", "r1_c3_rule_arm_constants/v1"),
            lambda d: d.pop("toolchain"),
            lambda d: d["fitter"].__setitem__("path", AC.FITTER_PATH),
            lambda d: d["fitter"].__setitem__("code_commit", "abc"),
            lambda d: d["a1a2_fitter"].__setitem__("sha256", "x"),
            lambda d: d["predeclaration"].__setitem__("revision", 3),
            lambda d: d["source"].__setitem__("proposals_sha256", "0" * 64),
            lambda d: d["source"].__setitem__("configs_sha256", "0" * 64),
            lambda d: d["source"].__setitem__("receipt_sha256", "x"),
            lambda d: d["noise_source"].__setitem__("sha256", "0" * 64),
            lambda d: d["split_file"].__setitem__("sha256", "0" * 64),
            lambda d: d.__setitem__("ladder_grid", d["ladder_grid"][1:]),
            lambda d: d.__setitem__("ladder_tie", "largest c"),
            lambda d: d["nodes"].pop("tabular_mlp"),
            lambda d: d["nodes"].__setitem__("openml_wdbc", copy.deepcopy(d["nodes"]["openml_sonar"])),
            lambda d: d["nodes"][n0]["A2"].__setitem__(0, 0.01),
            lambda d: d["nodes"][n0]["noise"].pop("delta_n"),
            setc,                                                         # c not the §5.6 choice of its table
            lambda d: d["nodes"][n0]["LADDER"].__setitem__("c", 0.07),    # off the grid
            lambda d: d["nodes"][n0]["LADDER"].__setitem__("eta", float(np.nextafter(lad["eta"], 1.0))),
            lambda d: d["nodes"][n0]["LADDER"].__setitem__("sigma_node", 0.5),
            lambda d: d["nodes"][n0]["LADDER"].__setitem__("rows", lad["rows"] - 1),
            lambda d: d["nodes"][n0]["LADDER"]["search"][10].__setitem__("U", 1e9),
            lambda d: d["nodes"][n0]["LADDER"]["search"][10].__setitem__("c", 0.0),
            lambda d: d["nodes"][n0]["LADDER"]["search"][10].__setitem__("eta", 0.0),
            lambda d: d["nodes"][n0]["LADDER"]["search"].pop(),
            lambda d: d["nodes"][n0]["LADDER"]["search"][0].__setitem__("keeps", 0),
            lambda d: d["nodes"][n0]["LADDER"].pop("search")]
    for i, m in enumerate(muts):
        d = copy.deepcopy(doc)
        m(d)
        with pytest.raises(AF.ArmsFreezeError):
            D.parse(json.dumps(d).encode())
            pytest.fail(f"mutation {i} accepted")
    with pytest.raises(AF.ArmsFreezeError, match="not JSON"):
        D.parse(b"{")


# ------------------------------------------------------------------------------------------- the CLI

@pytest.fixture()
def cli(monkeypatch, world, tmp_path):
    d = tmp_path / "sweep2_table"
    d.mkdir()
    (d / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in world["rows"]))
    (d / "configs.json").write_bytes(b'{"configs": {}}\n')
    sha = AF._sha_file(d / "proposals.jsonl")
    receipt = "2" * 64
    state = {"sha": sha, "calls": []}

    def fake(root, source, receipt_sha256=None):
        state["calls"].append((source, receipt_sha256))
        assert source == "sweep2" and receipt_sha256 == receipt and str(root).endswith("rel")
        return copy.deepcopy(world["labels"]), {
            "stage": "traindev", "source": source, "counts": {"evaluation_rows": 0},
            "inputs": {"proposals_sha256": state["sha"], "label_block_sha256": "6" * 64},
            "outputs": {"label_block.traindev.jsonl": "7" * 64}}
    monkeypatch.setattr(release, "traindev_labels", fake)
    monkeypatch.setattr(D, "_code", lambda: (BASE_COMMIT, dict(FITTER), dict(A1A2)))
    monkeypatch.setattr(D, "SWEEP2_PROPOSALS_SHA256", sha)
    monkeypatch.setattr(D, "SWEEP2_CONFIGS_SHA256", AF._sha(b'{"configs": {}}\n'))
    args = ["fit", "--release-root", str(tmp_path / "rel"), "--receipt", receipt, "--table", str(d)]
    return {"args": args, "dir": d, "tmp": tmp_path, "state": state}


def test_cli_writes_once_prints_the_sha256_and_is_deterministic(cli, fitted, capsys):
    out1, out2 = cli["tmp"] / "c1" / "D3.json", cli["tmp"] / "c2" / "D3.json"
    assert D.main(cli["args"] + ["--out", str(out1)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert D.main(cli["args"] + ["--out", str(out2)]) == 0
    capsys.readouterr()
    data = out1.read_bytes()
    assert data == out2.read_bytes()                                   # same inputs -> identical bytes
    assert printed["sha256"] == AF._sha(data) and printed["code_commit"] == BASE_COMMIT
    assert printed["ladder_c"] == {n: fitted["ladder"][n]["c"] for n in D.D3_NODES}
    p = D.parse(data)
    assert p["source"] == {"name": "sweep2", "receipt_sha256": "2" * 64, "traindev_partition_sha256": "7" * 64,
                           "label_block_sha256": "6" * 64, "proposals_sha256": cli["state"]["sha"],
                           "configs_sha256": D.SWEEP2_CONFIGS_SHA256}
    assert p["toolchain"] == AC.toolchain()
    assert p["gate_input_builder"] == {"path": AC.BUILDER_PATH, "sha256": AF._sha_file(REPO / AC.BUILDER_PATH)}
    for n in D.D3_NODES:
        assert _bits(p["vectors"]["A1"][n]) == _bits(fitted["vectors"][n]["A1"])
        assert p["nodes"][n]["LADDER"]["eta"] == fitted["ladder"][n]["eta"]
    with pytest.raises(AF.ArmsFreezeError, match="written once"):
        D.main(cli["args"] + ["--out", str(out1)])
    assert out1.read_bytes() == data
    assert D.main(["check", str(out1)]) == 0
    assert json.loads(capsys.readouterr().out)["sha256"] == printed["sha256"]


def test_write_exclusive_refuses_a_file_created_in_between(tmp_path):
    f = tmp_path / "x.json"
    D.write_exclusive(f, b"a")
    with pytest.raises(AF.ArmsFreezeError, match="written once"):
        D.write_exclusive(f, b"b")
    assert f.read_bytes() == b"a"


def test_cli_refusals(cli, monkeypatch):
    tmp, d = cli["tmp"], cli["dir"]
    for name in ("label_block.jsonl", "evaluation_block.all.jsonl", "label_block.test.jsonl", "runs.jsonl"):
        with pytest.raises(AF.ArmsFreezeError, match="not arms inputs"):
            D.main(cli["args"] + ["--out", str(tmp / name)])
    bad = [a.replace(str(tmp / "rel"), str(tmp / "sweep2" / "test")) for a in cli["args"]]
    with pytest.raises(AF.ArmsFreezeError, match="not arms inputs"):
        D.main(bad + ["--out", str(tmp / "a.json")])
    with pytest.raises(RuntimeError, match="r1_sealed"):
        D.main(cli["args"] + ["--out", str(tmp / "r1_sealed" / "b.json")])
    real = cli["state"]["sha"]
    cli["state"]["sha"] = "0" * 64
    with pytest.raises(AF.ArmsFreezeError, match="receipt released"):
        D.main(cli["args"] + ["--out", str(tmp / "c.json")])
    cli["state"]["sha"] = real
    monkeypatch.setattr(D, "SWEEP2_PROPOSALS_SHA256", "0" * 64)
    with pytest.raises(AF.ArmsFreezeError, match="pinned sweep-2 table"):
        D.main(cli["args"] + ["--out", str(tmp / "d.json")])
    monkeypatch.setattr(D, "SWEEP2_PROPOSALS_SHA256", real)
    (d / "configs.json").write_bytes(b"{}\n")
    with pytest.raises(AF.ArmsFreezeError, match="configs.json"):
        D.main(cli["args"] + ["--out", str(tmp / "e.json")])
    (d / "configs.json").unlink()
    with pytest.raises(AF.ArmsFreezeError, match="configs.json"):
        D.main(cli["args"] + ["--out", str(tmp / "f.json")])
    (d / "configs.json").write_bytes(b'{"configs": {}}\n')
    monkeypatch.setattr(D, "NOISE_SHA256", "0" * 64)
    with pytest.raises(AF.ArmsFreezeError, match="noise summary"):
        D.main(cli["args"] + ["--out", str(tmp / "g.json")])
    monkeypatch.setattr(D, "NOISE_SHA256", AF._sha_file(REPO / D.NOISE_PATH))
    real_block = AF._prereg_block
    monkeypatch.setattr(AF, "_prereg_block", lambda repo: {"gate_input_builder_sha256": "0" * 64})
    with pytest.raises(AF.ArmsFreezeError, match="preregistration binds"):
        D.main(cli["args"] + ["--out", str(tmp / "h.json")])
    monkeypatch.setattr(AF, "_prereg_block", real_block)
    monkeypatch.setattr(release, "traindev_labels",
                        lambda *a, **k: ([], {"stage": "traindev", "source": "sweep2",
                                              "counts": {"evaluation_rows": 4}}))
    with pytest.raises(AF.ArmsFreezeError, match="without evaluation rows"):
        D.main(cli["args"] + ["--out", str(tmp / "i.json")])
    assert not any((tmp / f"{c}.json").exists() for c in "abcdefghi")


@pytest.mark.parametrize("relative", [
    "sweep2_table/proposals.jsonl",
    "sweep2_table/configs.json",
    "sweep2_table/build.json",
    "rel/sweep2/traindev/RECEIPT.json",
    "rel/sweep2/traindev/label_block.traindev.jsonl",
])
def test_fit_refuses_symlinked_inputs_before_open(cli, monkeypatch, relative):
    tmp = cli["tmp"]
    fake_sealed = tmp / "r1_sealed" / "evaluation_block.all.jsonl"
    fake_sealed.parent.mkdir()
    fake_sealed.write_text("synthetic sentinel, not evidence")
    leaf = tmp / relative
    leaf.parent.mkdir(parents=True, exist_ok=True)
    if leaf.exists():
        leaf.rename(leaf.with_suffix(".original"))
    leaf.symlink_to(fake_sealed)
    open_file = Path.open

    def watch_open(path, *args, **kwargs):
        assert path.resolve() != fake_sealed
        return open_file(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", watch_open)
    with pytest.raises(AF.ArmsFreezeError, match="symlink is not a staged input"):
        D.main(cli["args"] + ["--out", str(tmp / "constants.json")])
    assert not cli["state"]["calls"]


def test_check_refuses_a_raw_block_or_a_symlink_before_open(tmp_path, monkeypatch):
    raw = tmp_path / "label_block.test.jsonl"
    raw.write_text("synthetic sentinel, not evidence")
    alias = tmp_path / "constants.json"
    alias.symlink_to(raw)
    open_file = Path.open

    def watch_open(path, *args, **kwargs):
        assert path.resolve() != raw
        return open_file(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", watch_open)
    with pytest.raises(AF.ArmsFreezeError, match="not arms inputs"):
        D.main(["check", str(raw)])
    with pytest.raises(AF.ArmsFreezeError, match="symlink is not a staged input"):
        D.main(["check", str(alias)])
