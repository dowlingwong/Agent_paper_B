"""Track S final code acceptance (CODE_ACCEPTANCE_20261029): one test group per MAJOR / MINOR item.

CPU only, synthetic nodes, scripted managers, a local fake llama-server for the S0.1 probe (no real LLM, no
network). ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026).
"""
from __future__ import annotations

import hashlib
import json
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from r1.tracks import a2u
from r1.tracks import analyze as A
from r1.tracks import collect as C
from r1.tracks import simulate_controls as S
from r1.tracks.probes import determinism as D
from r1.tracks.schema import STATE_FEATURES

LL = {"mechanism": "loglinear"}
SIGMA = 0.0066


def _run(tmp: Path, *extra: str, node: str = "synthetic_P2p", phase: str = "campaign", out: str = "out",
         W: str = "10", cap: str = "12", params: dict | None = None) -> Path:
    args = ["--phase", phase, "--node", node, "--llm-cap", cap, "--W", W, "--out", str(tmp / out),
            "--work", str(tmp / ("work_" + out)), "--label", "FIXTURE", "--host-label", "ci",
            "--synthetic-params", json.dumps(params if params is not None else {"variant": "concentrated",
                                                                                "strength": 0.012}), *extra]
    assert C.main(args) == 0
    return tmp / out


def _seed(instance_id: str) -> int:
    return int(instance_id.rsplit("__s", 1)[1])


# ---------------------------------------------------------------------------
# MAJOR 1: per-instance audit seeds, shared by every policy and repetition on the instance
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("phase", ["campaign", "tune"])
def test_major1_audit_seeds_are_per_instance_and_shared_across_policies(tmp_path, phase):
    out = _run(tmp_path, "--instances", "3", "--policy", "static:0,0", "--policy", "static:0.00066,0.00165",
               "--rep", "0", "--rep", "1", phase=phase)
    work = tmp_path / "work_out" / "root_meta"
    by_inst: dict[int, set] = {}
    for r in C.read_jsonl(out / "roots.jsonl"):
        meta = json.loads((work / f"{r['root_id']}.json").read_text())
        s = _seed(r["instance_id"])
        assert meta["_audit_seeds"] == list(C.instance_audit_seeds(phase, s, 5))
        by_inst.setdefault(s, set()).add(tuple(meta["_audit_seeds"]))
    assert all(len(v) == 1 for v in by_inst.values())                     # shared by policies and reps
    seeds = [next(iter(v)) for v in by_inst.values()]
    assert len(set().union(*map(set, seeds))) == 5 * len(seeds)           # no two instances share a seed
    # The audit cache holds each instance's own seeds only (real and synthetic nodes use the same rule).
    for row in C.read_jsonl(out / "audit_runs.jsonl"):
        assert row["seed"] in C.instance_audit_seeds(phase, int(row["salt"]), 5)


def test_major1_s05_and_s05b_use_their_block_per_instance(tmp_path):
    out = _run(tmp_path, "--instances", "2", "--forks", "0", node="synthetic_P0", phase="S0.5", W="12",
               params={**LL})
    assert C.main(["--phase", "S0.5b", "--node", "synthetic_P0", "--out", str(out), "--work",
                   str(tmp_path / "work_out"), "--truncate-W", "4"]) == 0
    for r in C.read_jsonl(out / "s05b_truncated.jsonl"):
        assert r["audit_seeds"] == list(C.instance_audit_seeds("S0.5", _seed(r["instance_id"]), 5))
    for r in C.read_jsonl(out / "s05_calibration.jsonl"):
        assert r["audit_seeds"] == list(C.instance_audit_seeds("S0.5", _seed(r["instance"]), 5))


def test_major1_real_and_synthetic_share_the_rule():
    fake = SimpleNamespace(manifest={"phase": "campaign", "K": 5})
    assert C.Run.seeds(fake, 32007) == C.instance_audit_seeds("campaign", 32007, 5)
    assert C.instance_audit_seeds("campaign", 32007, 5) == tuple(range(500000 + 7 * 20, 500000 + 7 * 20 + 5))


# ---------------------------------------------------------------------------
# MAJOR 2 / 3: one repetition convention; the primary uses rep 0 only
# ---------------------------------------------------------------------------

def test_major2_natural_rep1_run_gives_passing_placebos(tmp_path):
    m_star = "static:0,0"
    out = _run(tmp_path, "--instances", "15", "--policy", m_star, "--rep", "0", "--rep", "1",
               "--placebo-policy", m_star, "--exact-placebo-n", "10", node="synthetic_N0", W="10", cap="10",
               params={})
    roots = A.load_roots(out / "roots.jsonl")
    assert Counter(r.rep for r in roots) == Counter({0: 25, 1: 15})
    ex = A.placebo_exact(roots, m_star, min_groups=10)
    de = A.placebo_descriptive(roots, m_star, min_n=15)
    assert ex["status"] == "pass" and ex["n_groups"] == 10                  # same rep twice: identical
    assert de["status"] == "pass" and de["n"] == 15                         # rep 0 vs rep 1
    # The two repetitions really differ (different D26 seed bases, different scripted streams).
    assert len({r.llm_seed_base for r in roots if r.instance_id == roots[0].instance_id}) == 2


def test_major3_primary_D_uses_the_primary_repetition_only():
    roots = [S.make_campaign_root("n", f"c{k:04d}", "pi", 0, 0.91, W=10, llm_cap=40) for k in range(4)]
    roots += [S.make_campaign_root("n", f"c{k:04d}", "m", 0, 0.90, W=10, llm_cap=40) for k in range(4)]
    roots += [S.make_campaign_root("n", f"c{k:04d}", "m", 1, 0.80, W=10, llm_cap=40) for k in range(2)]
    pr = A.campaign_pairs(roots, "pi", "m")
    assert np.allclose(pr["D"], 0.01) and len(pr["D"]) == 4
    assert A.per_instance_means(roots, "m", rep=1) == {"c0000": 0.8, "c0001": 0.8}


# ---------------------------------------------------------------------------
# MAJOR 4: n = 300 fixed
# ---------------------------------------------------------------------------

def test_major4_n_fixed_at_300_and_no_rerun_warning():
    assert A.SizingDecl(0.0093).n == 300 and S.Plan().n == 300
    sz = A.plan_sizing(A.SizingDecl(0.0093), 0.0033, dev_ucl=None)
    assert sz["n_run_target"] == 300 and sz["n_formula"] == A.campaign_n(0.0093, 0.0033) < 300
    assert sz["mde_at_run"] == pytest.approx(2.93 * 0.0093 / np.sqrt(300))
    assert not A.freeze_check(sz, {"n": 300})["rerun_s06"]
    pd = A.parse_predeclaration({"schema": A.PREDECLARATION_SCHEMA, "primary_nodes": ["n"], "fallback_active": True,
                                 "nodes": {"n": {"role": "primary", "sigma_node": SIGMA, "sigma_cmp_vary": SIGMA,
                                                 "sizing": {"sigma_D_ucl_s05b": 0.0093}}}})
    assert pd.nodes["n"].sizing.n == 300


# ---------------------------------------------------------------------------
# MAJOR 5: S0.5 / S0.5b summary
# ---------------------------------------------------------------------------

def test_major5_calibration_gate():
    def rows(n, cov, stratum="0"):
        return [{"covered": i < round(cov * n), "stratum": stratum} for i in range(n)]
    assert A.calibration_gate(rows(120, 0.8))["status"] == "pass"
    assert A.calibration_gate(rows(120, 0.95))["status"] == "fail"
    assert A.calibration_gate(rows(60, 0.8))["status"] == "insufficient"
    mixed = rows(100, 0.8, "0") + rows(25, 0.5, ">=3")                      # a gated stratum out of band
    g = A.calibration_gate(mixed)
    assert g["by_stratum"][">=3"]["gated"] and g["status"] == "fail"
    small = rows(110, 0.8, "0") + rows(10, 0.3, "1-2")                      # < 20 predictions: not gated
    assert A.calibration_gate(small)["status"] == "pass"


def test_major5_s05_summary_on_a_pilot_fixture(tmp_path):
    p2 = C.policy_string("static", (0.3 * 0.003, 0.0))   # A2-U at 0.3 sigma (log-linear P0: sigma_run 0.003)
    nodes = {}
    for name in ("synthetic_P0", "synthetic_P2p"):
        out = _run(tmp_path, "--instances", "4", "--forks", "0", "--policy", p2, "--rep", "0", "--rep", "1",
                   "--rep-instances", "2", node=name, phase="S0.5", W="12", cap="12", out=name, params={**LL})
        assert C.main(["--phase", "S0.5b", "--node", name, "--out", str(out), "--work", str(tmp_path / f"work_{name}"),
                       "--truncate-W", "3,6,12"]) == 0
        nodes[name] = out
        roots = C.read_jsonl(out / "roots.jsonl")
        # MINOR 9: the repetition subset runs on the first 2 instances only
        assert Counter(r["rep"] for r in roots) == Counter({0: 8, 1: 2})   # p2 at rep 1 on instances 0, 1
    res = A.s05_summary(nodes, Ws=(3, 6, 12), min_n=5, stratum_min=3)
    assert res["schema"] == A.S05_SCHEMA and res["W_chosen"] in (3, 6, 12)
    for name, v in res["nodes"].items():
        shares = v["binding_shares"]
        assert set(shares) == {3, 6, 12} and shares[3] >= shares[12]
        ok = [w for w in (3, 6, 12) if all(res["nodes"][n]["binding_shares"][w] >= 0.5 for n in nodes)]
        assert res["W_chosen"] == (max(ok) if ok else 12) and res["budget_binds"] == bool(ok)
        assert v["sigma_cmp_vary"] is not None and v["sigma_cmp_vary_n"] > 0
        bp = v["sigma_D_at_W"]["between_policies"]
        assert bp["m"] == 4 and bp["ucl"] >= bp["sigma_hat"]
        br = v["sigma_D_at_W"]["between_repetitions"]
        assert set(br) == {p2} and br[p2]["m"] == 2
        assert v["calibration"]["status"] in ("pass", "fail", "insufficient") and v["calibration"]["n"] > 0
    out = tmp_path / "s05.json"
    assert A.main(["s05-summary", *sum((["--node", f"{n}={d}"] for n, d in nodes.items()), []),
                   "--W-candidates", "3,6,12", "--min-predictions", "5", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["W_chosen"] == res["W_chosen"]


# ---------------------------------------------------------------------------
# MAJOR 6: the S0.1 probe
# ---------------------------------------------------------------------------

class _FakeServer:
    """A local stand-in for llama-server: deterministic content from the request; records every body."""

    def __init__(self):
        bodies = self.bodies = []
        lock = threading.Lock()

        class H(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                with lock:
                    bodies.append(body)
                text = hashlib.sha256(json.dumps([body["messages"], body["seed"]]).encode()).hexdigest()
                data = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):  # noqa: N802
                data = json.dumps({"build_info": "b9999-fake"}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


def test_major6_probe_interleaves_two_clients_and_records_provenance(tmp_path):
    prompts = tmp_path / "p.jsonl"
    prompts.write_text("".join(json.dumps({"prompt": f"prompt {i}", "seed": 1000 + i}) + "\n" for i in range(6)))
    srv = _FakeServer()
    try:
        out = tmp_path / "r.json"
        args = ["--url", srv.url, "--prompts", str(prompts), "--n", "6", "--repeats", "3", "--clients-per-url", "2",
                "--host-label", "ci", "--gguf-sha256", "ab" * 32, "--llama-build", "b9999", "--server-args",
                "-np 1 -c 8192", "--proposal-schema", "manager_proposal/v1", "--out", str(out)]
        assert D.main(args) == 0
        with pytest.raises(SystemExit):           # provenance is required ("unknown" refused)
            D.main([a if a != "b9999" else "unknown" for a in args])
    finally:
        srv.close()
    rep = json.loads(out.read_text())
    u = rep["per_url"][srv.url]
    assert rep["schema"] == "tracks_s01_probe/v2" and u["clients"] == 2 and u["identity_rate"] == 1.0
    assert rep["provenance"] == {"gguf_sha256": "ab" * 32, "gguf_path": None, "llama_build": "b9999",
                                 "server_args": "-np 1 -c 8192"}
    assert rep["server_props"][srv.url] == {"build_info": "b9999-fake"}
    assert len(srv.bodies) >= 6 * 3 * 2
    # The exact harness request: no max_tokens, the grammar, seed and temperature as the harness sends them.
    harness_body = D.chat_payload("prompt 0", 1000, "r1-manager", proposal_schema="manager_proposal/v1")
    assert "max_tokens" not in harness_body and harness_body in srv.bodies
    assert rep["request_example"] == harness_body
    # Randomised, interleaved order per client (recorded seed), different between the two clients.
    o0, o1 = D.schedule(6, 3, 20261029, 0, 0), D.schedule(6, 3, 20261029, 0, 1)
    assert sorted(o0) == sorted((i, r) for r in range(3) for i in range(6)) and o0 != o1
    assert [x for x, _ in o0[:6]] != list(range(6))
    assert u["order_head"] == [[list(x) for x in o0[:5]], [list(x) for x in o1[:5]]]


# ---------------------------------------------------------------------------
# MINOR 2: pi' handoff (tracks_policy/v1) and the nesting test
# ---------------------------------------------------------------------------

def _nesting_policy(g: float, h: float) -> dict:
    p = len(STATE_FEATURES)
    j = STATE_FEATURES.index("index_value")
    slopes = [1.0 if k == j else 0.0 for k in range(p)]
    std = {"mean": [0.0] * p, "sd": [1.0] * p}
    return {"schema": A.POLICY_SCHEMA, "node": "synthetic_P2p", "features": list(STATE_FEATURES),
            "interactions": "epoch", "ridge_alpha": 0.1, "label": "FIXTURE", "host": "ci", "kind": "pi_prime",
            "coef": [0.0, 0.0] + slopes + slopes, "standardization": {"E1": std, "E2": std},
            "trained_epochs": ["E1", "E2"], "thresholds": {"E1": g, "E2": h}}


def test_minor2_pi_prime_from_the_analysis_file_nests_the_static_rule(tmp_path):
    g, h = 0.00066, 0.00165
    pol = _nesting_policy(g, h)
    path = tmp_path / "pi.json"
    sha = A.write_policy(pol, path)
    model, sha2 = a2u.load_score_model(path)
    assert sha2 == sha and isinstance(model, a2u.PolicyFileScore)
    st = {**{k: 0.0 for k in STATE_FEATURES}, "index_value": 0.001, "epoch": "E1"}
    assert model(st) == pytest.approx(A.policy_score(A.load_policy(path, sha), st, "E1"))
    static = C.policy_string("static", (g, h))
    out = _run(tmp_path, "--instances", "3", "--policy", f"pi_prime:{path}", "--policy", static, cap="20")
    roots = C.read_jsonl(out / "roots.jsonl")
    by: dict = {}
    for r in roots:
        by.setdefault(r["instance_id"], {})["pi" if r["policy"].startswith("pi_prime") else "st"] = r
    for v in by.values():   # pi' with score = V* - g (E1), m_hat - h (E2) takes the static rule's decisions
        acts = lambda r: [(d["index"], d["epoch"], d["action"]) for d in r["decisions"]]  # noqa: E731
        assert acts(v["pi"]) == acts(v["st"]) and v["pi"]["y_terminal"] == v["st"]["y_terminal"]


# ---------------------------------------------------------------------------
# MINOR 4 / 8: labels, host resume key, exact placebo first and STOP
# ---------------------------------------------------------------------------

def test_minor4_label_is_validated(tmp_path):
    with pytest.raises(SystemExit):
        C.main(["--phase", "campaign", "--node", "synthetic_N0", "--W", "10", "--llm-cap", "10", "--policy", "a2u",
                "--out", str(tmp_path / "o"), "--label", "evidence-ish"])


def test_minor8_host_is_a_resume_key_and_exact_placebo_mismatch_stops(tmp_path):
    out = _run(tmp_path, "--instances", "1", "--policy", "static:0,0", node="synthetic_N0", W="10", cap="10", params={})
    with pytest.raises(SystemExit, match="host"):
        C.main(["--phase", "campaign", "--node", "synthetic_N0", "--W", "10", "--llm-cap", "10", "--policy",
                "static:0,0", "--instances", "1", "--out", str(out), "--work", str(tmp_path / "work_out"),
                "--label", "FIXTURE", "--host-label", "other", "--synthetic-params", "{}"])
    roots = C.read_jsonl(out / "roots.jsonl")
    dup = dict(roots[0], root_id=roots[0]["root_id"] + "_dup")
    run = SimpleNamespace(out=out)
    C.check_exact_placebo(run, dup)                                         # identical: no STOP
    with pytest.raises(C.Stop, match="exact placebo"):
        C.check_exact_placebo(run, dict(dup, y_terminal=dup["y_terminal"] + 1e-9))


def test_minor1_assemble_refuses_mixed_nodes_and_phases(tmp_path):
    a = _run(tmp_path, "--instances", "1", "--policy", "static:0,0", node="synthetic_N0", W="10", cap="10",
             params={}, out="a", phase="tune")
    with pytest.raises(SystemExit, match="phase"):
        C.assemble("synthetic_N0", tmp_path / "nd", campaign=[a])
    with pytest.raises(SystemExit, match="node"):
        C.assemble("synthetic_P2p", tmp_path / "nd", dev=[a])
    rep = C.assemble("synthetic_N0", tmp_path / "nd", dev=[a, a])          # the same root twice is kept once
    assert rep["outputs"]["dev_roots.jsonl"]["n"] == 1 and rep["hosts"] == ["ci"]
    assert A.load_roots(tmp_path / "nd" / "dev_roots.jsonl")[0].policy == "static:0,0"
