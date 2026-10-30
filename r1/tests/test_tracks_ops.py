"""Track S ops-readiness (TRACKS_OPERATOR_RUNBOOK_REVIEW_20261030): one test group per coordinator item 1-16.

CPU only, synthetic nodes, scripted managers; a local fake server for the health check (no real LLM, no network).
ENGINEERING_ONLY; AI-assisted (Claude, 30 Oct 2026).
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import threading
from collections import Counter
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from r1.tracks import a2u
from r1.tracks import analyze as A
from r1.tracks import collect as C
from r1.tracks import simulate_controls as S
from r1.tracks.schema import to_dict

LL = {"mechanism": "loglinear"}
N0 = ["--node", "synthetic_N0", "--W", "10", "--llm-cap", "10", "--synthetic-params", "{}", "--label", "FIXTURE",
      "--host-label", "ci"]


def _c(*args) -> int:
    return C.main([str(a) for a in args])


def _camp(tmp: Path, out: str, *extra) -> Path:
    assert _c("--phase", "campaign", *N0, "--out", tmp / out, "--work", tmp / f"w_{out}", *extra) == 0
    return tmp / out


# ---------------------------------------------------------------------------- 1 sharding
def test_shard_map_is_deterministic():
    assert C.parse_shard("1/3") == (1, 3) and C.parse_shard(None) is None
    for bad in ("3/3", "a/b", "1"):
        with pytest.raises(SystemExit):
            C.parse_shard(bad)
    assert [C.shard_of(k, 3) for k in range(7)] == [0, 1, 2, 0, 1, 2, 0]


def test_shards_placebo_only_and_assemble(tmp_path):
    m = "static:0,0"
    common = ["--policy", m, "--policy", "static:0.00066,0", "--instances", "6", "--placebo-policy", m,
              "--exact-placebo-n", "2", "--rep", "0"]
    pe = _camp(tmp_path, "placebo", *common, "--exact-placebo-only")
    s0 = _camp(tmp_path, "s0", *common, "--shard", "0/2")
    s1 = _camp(tmp_path, "s1", *common, "--shard", "1/2")
    rp = C.read_jsonl(pe / "roots.jsonl")
    assert [(r["policy"], r["rep"], r["root_id"].endswith("_dup")) for r in rp] == [(m, 0, False), (m, 0, True)] * 2
    lo = C.INSTANCE_SEED_BLOCKS["campaign"][0]
    for d, want in ((s0, {0, 2, 4}), (s1, {1, 3, 5})):
        rows = C.read_jsonl(d / "roots.jsonl")
        assert {int(r["instance_id"].rsplit("__s", 1)[1]) - lo for r in rows} == want
        assert not any(r["root_id"].endswith("_dup") for r in rows)
        # the placebo instances' m* rep-0 runs live in the placebo dir only
        assert not any(r["policy"] == m and int(r["instance_id"].rsplit("__s", 1)[1]) - lo < 2 for r in rows)
        assert all(r["provenance"]["shard"] == json.loads((d / "manifest.json").read_text())["shard"] for r in rows)
        assert all(r["provenance"]["server_url"] is None for r in rows)          # scripted: no server
    rep = C.assemble("synthetic_N0", tmp_path / "nd", campaign=[pe, s0, s1])
    assert rep["outputs"]["campaign_roots.jsonl"]["n"] == 4 + 6 * 2 - 2 and rep["shards"]["campaign"] == ["0/2", "1/2"]
    roots = A.load_roots(tmp_path / "nd" / "campaign_roots.jsonl")
    assert A.placebo_exact(roots, m, min_groups=2)["status"] == "pass"
    assert len(A.campaign_pairs(roots, "static:0.00066,0", m)["D"]) == 6       # every instance paired
    # overlapping shards are refused
    bad = tmp_path / "s1_bad"
    shutil.copytree(s0, bad)
    man = json.loads((bad / "manifest.json").read_text())
    (bad / "manifest.json").write_text(json.dumps({**man, "shard": "1/2"}))
    rows = C.read_jsonl(bad / "roots.jsonl")
    (bad / "roots.jsonl").write_text("".join(json.dumps({**r, "root_id": r["root_id"] + "x"}) + "\n" for r in rows))
    with pytest.raises(SystemExit, match="share instances"):
        C.assemble("synthetic_N0", tmp_path / "nd2", campaign=[s0, bad])
    with pytest.raises(SystemExit):
        _c("--phase", "campaign", *N0, "--out", tmp_path / "x", *common, "--exact-placebo-only", "--shard", "0/2")


# ---------------------------------------------------------------------------- 2 stop file, health, breaker
def test_stop_file_pauses(tmp_path):
    stop = tmp_path / "STOP"
    stop.write_text("")
    out = _camp(tmp_path, "o", "--policy", "static:0,0", "--instances", "3", "--stop-file", stop)
    assert not C.read_jsonl(out / "roots.jsonl")
    sess = json.loads((out / "manifest.json").read_text())["sessions"][-1]["done"]
    assert sess["status"] == "paused" and sess["failed"] == 0
    stop.unlink()
    _camp(tmp_path, "o", "--policy", "static:0,0", "--instances", "3", "--stop-file", stop)
    assert len(C.read_jsonl(out / "roots.jsonl")) == 3


def test_transport_failures_trip_the_breaker_without_consuming_retries(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise ConnectionRefusedError("server down")
    monkeypatch.setattr(C, "run_root", boom)
    rc = _c("--phase", "campaign", *N0, "--out", tmp_path / "o", "--work", tmp_path / "w", "--policy", "static:0,0",
            "--instances", "5", "--max-transport-failures", "3")
    assert rc == 3
    sess = json.loads((tmp_path / "o" / "manifest.json").read_text())["sessions"][-1]["done"]
    assert sess["status"] == "STOP: server unhealthy" and sess["transport_failures"] == 3
    assert not C.read_jsonl(tmp_path / "o" / "failed_units.jsonl")             # no retry consumed
    assert C.is_transport_error(RuntimeError("x")) is False


class _Health:
    def __init__(self, ok: bool):
        class H(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                self.send_response(200 if ok else 503)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *a):
                pass
        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


def test_health_check_before_units(monkeypatch):
    good, bad = _Health(True), _Health(False)
    try:
        assert C.server_healthy(good.url) and not C.server_healthy(bad.url) and not C.server_healthy(None)
        run = SimpleNamespace(args=SimpleNamespace(stop_file=None, max_transport_failures=2, health_wait=0.0),
                              manifest={"manager": {"kind": "langgraph"}}, time_left=lambda: True)
        monkeypatch.setenv("LLAMACPP_BASE_URL", good.url)
        done = {}
        assert C._Guard(run, done).proceed()
        monkeypatch.setenv("LLAMACPP_BASE_URL", bad.url)
        done = {}
        assert not C._Guard(run, done).proceed() and done["status"] == "STOP: server unhealthy"
    finally:
        good.close()
        bad.close()


# ---------------------------------------------------------------------------- 3 S0.5b work dir
def test_s05b_uses_the_recorded_work_dir_and_refuses_missing_ledgers(tmp_path):
    base = ["--node", "synthetic_P0", "--synthetic-params", json.dumps(LL), "--label", "FIXTURE", "--host-label", "ci"]
    assert _c("--phase", "S0.5", *base, "--W", "12", "--llm-cap", "12", "--instances", "2", "--forks", "0",
              "--out", tmp_path / "s05", "--work", tmp_path / "w05") == 0
    man = json.loads((tmp_path / "s05" / "manifest.json").read_text())
    assert man["work"] == str((tmp_path / "w05").resolve())
    with pytest.raises(SystemExit, match="differs"):
        _c("--phase", "S0.5b", *base, "--out", tmp_path / "s05", "--work", tmp_path / "other", "--truncate-W", "4")
    assert _c("--phase", "S0.5b", *base, "--out", tmp_path / "s05", "--truncate-W", "4") == 0   # recorded work
    root = C.read_jsonl(tmp_path / "s05" / "roots.jsonl")[0]
    (tmp_path / "w05" / "roots" / root["root_id"] / "root_trials.jsonl").unlink()
    with pytest.raises(SystemExit, match="missing"):
        _c("--phase", "S0.5b", *base, "--out", tmp_path / "s05", "--truncate-W", "6")


# ---------------------------------------------------------------------------- 4 tune configs / extension only
def test_tune_configs_and_extension_only(tmp_path):
    t = ["--phase", "tune", *N0]
    assert _c(*t, "--out", tmp_path / "a", "--work", tmp_path / "w", "--instances", "3",
              "--tune-configs", "static:0,0; static:6.6e-4,0") == 0
    assert Counter(r["policy"] for r in C.read_jsonl(tmp_path / "a" / "roots.jsonl")) == \
        Counter({"static:0,0": 3, "static:0.00066,0": 3})
    assert _c(*t, "--out", tmp_path / "b", "--work", tmp_path / "w", "--instances", "2",
              "--tune-g-extension-only", "--sigma-cmp-vary", "0.0066") == 0
    pols = Counter(r["policy"] for r in C.read_jsonl(tmp_path / "b" / "roots.jsonl"))
    assert set(pols) == set(A.FamilyDecl().extension_configs(0.0066)) and set(pols.values()) == {2}
    ids_a = {r["instance_id"] for r in C.read_jsonl(tmp_path / "a" / "roots.jsonl")}
    assert {r["instance_id"] for r in C.read_jsonl(tmp_path / "b" / "roots.jsonl")} <= ids_a  # same paired instances


# ---------------------------------------------------------------------------- 5 a2 fraction
def test_a2_fraction_defaults_to_zero(tmp_path):
    assert C.A2_FRACTION_DEFAULT == 0.0
    args = ["--phase", "synthetic", "--node", "synthetic_N0", "--W", "10", "--llm-cap", "10", "--instances", "3",
            "--out", tmp_path / "o", "--work", tmp_path / "w", "--label", "FIXTURE", "--dry-run"]
    assert _c(*args) == 0


# ---------------------------------------------------------------------------- 6 manager flags
def test_manager_flags_for_real_nodes_and_evidence(tmp_path):
    real = ["--phase", "S0.4", "--node", "digits_mlp", "--out", tmp_path / "o", "--work", tmp_path / "w",
            "--host-label", "ci"]
    with pytest.raises(SystemExit, match="--manager is required"):
        _c(*real)
    with pytest.raises(SystemExit, match="scripted"):
        _c(*real, "--manager", "scripted")                                     # ENGINEERING_ONLY, not a dry run
    assert _c(*real, "--manager", "scripted", "--dry-run") == 0
    with pytest.raises(SystemExit, match="EVIDENCE"):
        _c("--phase", "campaign", *N0[:-4], "--label", "EVIDENCE", "--host-label", "ci", "--policy", "a2u",
           "--out", tmp_path / "e")
    with pytest.raises(SystemExit, match="llama-server-bin"):
        _c(*real, "--manager", "llamacpp", "--manager-model", "llamacpp/r1-manager", "--label", "EVIDENCE",
           "--gguf-sha256", "ab" * 32, "--llama-build", "b1")


# ---------------------------------------------------------------------------- 7 obs inflation
def test_obs_inflation_is_recorded_and_enforced(tmp_path):
    node = C.make_adapter("synthetic_N0", {}, {}).node
    p0 = tmp_path / "prior.json"
    node.prior().save(p0)
    assert _c("--phase", "set_obs_inflation", "--node", "synthetic_N0", "--prior", p0, "--obs-inflation", "1.5",
              "--prior-out", tmp_path / "p15.json", "--out", tmp_path / "unused") == 0
    p15 = a2u.A2UPrior.load(tmp_path / "p15.json")
    assert p15.meta["obs_inflation"] == 1.5 and p15.meta["model"] == a2u.KEYED_MODEL
    t = ["--phase", "tune", *N0, "--policy", "static:0,0", "--instances", "1", "--prior", tmp_path / "p15.json"]
    with pytest.raises(SystemExit, match="obs-inflation"):
        _c(*t, "--out", tmp_path / "a", "--work", tmp_path / "w")
    assert _c(*t, "--obs-inflation", "1.5", "--out", tmp_path / "b", "--work", tmp_path / "w") == 0
    r = C.read_jsonl(tmp_path / "b" / "roots.jsonl")[0]
    assert r["provenance"]["obs_inflation"] == 1.5
    with pytest.raises(SystemExit):
        _c("--phase", "set_obs_inflation", "--node", "synthetic_N0", "--prior", p0, "--obs-inflation", "0.5",
           "--prior-out", tmp_path / "p05.json", "--out", tmp_path / "unused")


# ---------------------------------------------------------------------------- 8 gz, 9 BLAS
def test_assemble_reads_gz_and_blas_threads_are_pinned(tmp_path, monkeypatch):
    for v in C.BLAS_VARS:
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("MKL_NUM_THREADS", "4")
    d = _camp(tmp_path, "o", "--policy", "static:0,0", "--instances", "2")
    assert os.environ["OMP_NUM_THREADS"] == "1" and os.environ["MKL_NUM_THREADS"] == "4"   # preset values kept
    r = C.read_jsonl(d / "roots.jsonl")[0]
    assert r["provenance"]["blas_threads"] == "OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=4"
    gz = tmp_path / "gz"
    shutil.copytree(d, gz)
    with gzip.open(gz / "roots.jsonl.gz", "wt") as fh:
        fh.write((gz / "roots.jsonl").read_text())
    (gz / "roots.jsonl").unlink()
    rep = C.assemble("synthetic_N0", tmp_path / "nd", campaign=[gz])
    assert rep["outputs"]["campaign_roots.jsonl"]["n"] == 2


# ---------------------------------------------------------------------------- 10 liveness
def test_liveness_phase_over_s04_ledgers(tmp_path):
    base = ["--node", "synthetic_N0", "--synthetic-params", json.dumps({**LL, "mu_step": 0.02, "spread": 0.01}),
            "--label", "FIXTURE", "--host-label", "ci"]
    assert _c("--phase", "S0.4", *base, "--llm-cap", "10", "--instances", "2", "--out", tmp_path / "s04",
              "--work", tmp_path / "w") == 0
    rc = _c("--phase", "liveness", *base, "--out", tmp_path / "s04")
    rep = json.loads((tmp_path / "s04" / "liveness" / "liveness.json").read_text())
    assert rep["manager_kind"] == "scripted" and rep["memory_mode"] == "append_only_summary"
    assert set(rep["nodes"]) == {"digits_mlp"} or rep["nodes"]
    assert rc == (0 if all(v["pass"] for v in rep["nodes"].values()) else 3)


# ---------------------------------------------------------------------------- 11 fit-policy
def _pd(node="planted", **extra):
    return {"schema": A.PREDECLARATION_SCHEMA, "primary_nodes": [node], "fallback_active": True,
            "nodes": {node: {"role": "primary", "sigma_node": 0.0066, "sigma_cmp_vary": 0.0066,
                             "sizing": {"sigma_D_ucl_s05b": 0.0093}}}, **extra}


def test_fit_policy_from_s3a_forks_alone(tmp_path):
    lv = S.planted_forks(n_instances=12, forks_per_instance=6, seed=10, budget=0.001)
    d = tmp_path / "node"
    d.mkdir()
    (d / "leaves.jsonl").write_text("".join(json.dumps(to_dict(x)) + "\n" for x in lv))
    pd = tmp_path / "pd.json"
    pd.write_text(json.dumps(_pd(ridge_alpha_grid=[0.01, 0.1, 1.0])))
    assert A.main(["fit-policy", "--predeclaration", str(pd), "--node", f"planted={d}", "--out-dir",
                   str(tmp_path / "pol")]) == 0
    f = tmp_path / "pol" / "planted.pi_prime.json"
    sha = (tmp_path / "pol" / "planted.pi_prime.sha256").read_text().split()[0]
    pol = A.load_policy(f, sha)
    sel = pol["ridge_alpha_selection"]
    assert pol["ridge_alpha"] in (0.01, 0.1, 1.0) and sel["grid"] == [0.01, 0.1, 1.0]
    assert pol["ridge_alpha"] == min(sel["grid"], key=lambda a: (sel["cv_mse"][str(a)], -a))
    model, sha2 = a2u.load_score_model(f)                                     # the collector's pi_prime: loader
    assert sha2 == sha


# ---------------------------------------------------------------------------- 12 / 16 S0.6 inputs and values
def test_s05_summary_values_between_policy_sd_at_cap_and_near_band(tmp_path):
    p2 = C.policy_string("static", (0.0009, 0.0))
    base = ["--node", "synthetic_P0", "--synthetic-params", json.dumps(LL), "--label", "FIXTURE", "--host-label", "ci"]
    assert _c("--phase", "S0.5", *base, "--W", "12", "--llm-cap", "12", "--instances", "4", "--forks", "0",
              "--policy", p2, "--out", tmp_path / "s05", "--work", tmp_path / "w") == 0
    assert _c("--phase", "S0.5b", *base, "--out", tmp_path / "s05", "--truncate-W", "3,6,12") == 0
    res = A.s05_summary({"synthetic_P0": tmp_path / "s05"}, Ws=(3, 6, 12), min_n=5, stratum_min=3)
    roots = C.read_jsonl(tmp_path / "s05" / "roots.jsonl")
    y = {(r["instance_id"], r["policy"]): r["y_terminal"] for r in roots}
    D = [y[(i, "a2u")] - y[(i, p2)] for (i, p) in y if p == "a2u"]
    v = res["values"]["nodes"]["synthetic_P0"]
    assert v["between_policy_sd_at_cap"] == pytest.approx(float(np.std(D, ddof=1)))
    margins = [abs(d["margin"]) for r in roots if r["policy"] == "a2u" for d in r["decisions"]
               if d["eligible"] and d.get("margin") is not None]
    assert v["near_band_b"] == pytest.approx(0.5 * float(np.median(margins)))
    assert set(res["values"]) == {"W", "budget_binds", "nodes"}
    assert {"sigma_cmp_vary", "sigma_D_ucl_s05b", "calibration_status", "obs_inflation"} <= set(v)


def _dev_roots(cfgs, n=6, seed=1):
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 0.004, n)
    out = []
    for k, c in enumerate(cfgs):
        ys = 0.9 + 0.0001 * k + base + rng.normal(0, 0.001, n)
        out += [S.make_campaign_root("n", f"d{i:04d}", c, 0, float(y), W=10, llm_cap=40, phase="dev_tuning")
                for i, y in enumerate(ys)]
    return out


def test_select_reports_dev_between_sd_as_the_simulator_defines_it():
    fam = A.FamilyDecl()
    cfgs = fam.static_configs(0.0066)
    roots = _dev_roots(cfgs[::-1])               # m* is not on the upper g edge
    pd = A.parse_predeclaration(_pd("n"))
    sel = A.selection_report(roots, pd, pd.nodes["n"])
    Y = {c: np.array(sorted([(r.instance_id, r.y_terminal) for r in roots if r.policy == c]))[:, 1].astype(float)
         for c in cfgs}
    sds = [np.std(Y[a] - Y[b], ddof=1) for i, a in enumerate(cfgs) for b in cfgs[i + 1:]]
    assert sel["dev_between"]["dev_between_sd"] == pytest.approx(float(np.mean(sds)))
    assert sel["dev_between"]["n_pairs"] == 105


# ---------------------------------------------------------------------------- 13 / 14 controls
def test_controls_merge_and_label_does_not_downgrade_the_primary(tmp_path):
    from test_tracks_analyze import controls, fake_campaign
    c = controls(("a", "b"))
    ca = {"label": "FIXTURE", "nodes": {"a": c["nodes"]["a"]}}
    cb = {"label": "FIXTURE", "nodes": {"b": c["nodes"]["b"]}}
    merged = A.merge_controls([ca, cb])
    assert set(merged["nodes"]) == {"a", "b"} and merged["labels"] == {"a": "FIXTURE", "b": "FIXTURE"}
    with pytest.raises(A.TrackSAnalysisError):
        A.merge_controls([ca, ca])
    nd = {x: A.NodeDecl(x, "primary", 0.0033, sigma_node=0.0066, sizing=A.SizingDecl(0.009),
                        sigma_cmp_vary=0.0066) for x in ("a", "b")}
    pd = A.Predeclaration(nodes=nd, primary_nodes=["a", "b"])
    res = {x: {"role": "primary", "campaign": {**fake_campaign(0.006, 0.002, 0.01, 0.004), "label": "PILOT"},
               "fork": None, "label": "PILOT"} for x in ("a", "b")}
    d = A.decide(res, merged, pd)
    assert d["label"] == "PILOT" and d["controls_label"] == "FIXTURE"


# ---------------------------------------------------------------------------- 15 predecl-template
def test_predecl_template_draft_is_accepted_by_select_only(tmp_path):
    s05 = {"values": {"W": 10, "budget_binds": True, "nodes": {"n": {
        "sigma_cmp_vary": 0.0066, "sigma_D_ucl_s05b": 0.0093, "between_policy_sd_at_cap": 0.01,
        "near_band_b": 0.0004, "obs_inflation": 1.0}}}}
    draft = A.predecl_template(s05, sigma_node={"n": 0.0066})
    assert draft["draft"] and A.has_todo(draft) and draft["collection"]["W"] == 10
    assert draft["nodes"]["n"]["sizing"] == {"sigma_D_ucl_s05b": 0.0093, "n": 300}
    with pytest.raises(A.TrackSAnalysisError, match="draft"):
        A.parse_predeclaration(draft)
    pd = A.parse_predeclaration(draft, allow_draft=True)
    assert pd.nodes["n"].sigma_cmp_vary == 0.0066 and pd.nodes["n"].g_declared == pytest.approx(0.00066)
    # select on the draft (CLI), with the machine-readable values printed / written
    d = tmp_path / "node"
    d.mkdir()
    fam = A.FamilyDecl()
    (d / "dev_roots.jsonl").write_text("".join(json.dumps(A.record_to_dict(r)) + "\n"
                                               for r in _dev_roots(fam.static_configs(0.0066)[::-1])))
    (tmp_path / "draft.json").write_text(json.dumps(draft))
    assert A.main(["select", "--predeclaration", str(tmp_path / "draft.json"), "--node", f"n={d}",
                   "--out", str(tmp_path / "sel.json")]) == 0
    sel = json.loads((tmp_path / "sel.json").read_text())
    assert sel["predeclaration_draft"] and sel["values"]["m_star"] == sel["m_star"]
    assert {"pi_star", "centres", "g_eff", "h_eff", "dev_between_sd", "missing_members"} <= set(sel["values"])
    full = A.predecl_template(s05, {"n": sel}, sigma_node={"n": 0.0066})
    assert full["nodes"]["n"]["selection"]["m_star"] == sel["m_star"]
