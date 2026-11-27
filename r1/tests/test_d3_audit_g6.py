"""Synthetic CPU tests for the D.3 G6 Y/Y(w) audit (no GPU, no label, fake runner)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from r1.c3.d3 import audit as G
from r1.c3.d3.snapshots import config_sha256

STAGE, ARM, NODE, REP = "a", "A0", "digits_mlp", 0
INSTANCE = "digits_mlp__s6201"
SIGMA = 0.005
START = {"train.py": "LEARNING_RATE_INIT = 1e-3\n"}
INC5 = {"train.py": "LEARNING_RATE_INIT = 2e-3\n"}
INC7 = {"train.py": "LEARNING_RATE_INIT = 3e-3\n"}


def snapshot(w, files, *, final=False, ended_on="worker_runs"):
    return {"schema": G.SNAPSHOT_SCHEMA, "stage": STAGE, "arm": ARM, "node": NODE, "repetition": REP,
            "instance_id": INSTANCE, "w": w, "w_actual": w, "incumbent_config": dict(files),
            "start_config": dict(START), "config_sha256": config_sha256(files),
            "final": final, "ended_on": ended_on}


def write_campaign(root: Path, snaps: dict[str, dict]):
    d = root / "campaigns" / INSTANCE / "snapshots"
    d.mkdir(parents=True)
    for name, payload in snaps.items():
        (d / name).write_text(json.dumps(payload))
    return root


class FakeRunner:
    """Deterministic metric = base by config text + 0.001 * seed index; records every call."""

    def __init__(self, base=None, fail_seed=None, drop_seed=None):
        self.base = base or {START["train.py"]: 0.50, INC5["train.py"]: 1.00, INC7["train.py"]: 1.20}
        self.calls = 0
        self.fail_seed = fail_seed
        self.drop_seed = drop_seed

    def __call__(self, node, files, seeds):
        self.calls += 1
        text = files["train.py"]
        out = []
        for i, seed in enumerate(seeds):
            if seed == self.drop_seed:
                continue
            metric = self.base[text] + 0.001 * i
            if seed == self.fail_seed:
                metric = float("nan")
            out.append(G.Run(seed=seed, metric=metric, run_sha256=f"sha-{text[:6]}-{seed}"))
        return out


def test_audit_seeds_cover_the_declared_block():
    assert G.audit_seeds(6201) == tuple(range(6701, 6711))
    assert G.audit_seeds(6218) == tuple(range(6871, 6881))
    with pytest.raises(G.AuditStop):
        G.audit_seeds(6200)


def test_snapshot_self_hash_is_checked(tmp_path):
    bad = snapshot(5, INC5)
    bad["config_sha256"] = "0" * 64
    p = tmp_path / "w5.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(G.AuditStop):
        G.load_snapshot(p)


def test_audit_campaign_writes_rows_and_missing_points(tmp_path):
    root = write_campaign(tmp_path / "chunk", {"w5.json": snapshot(5, INC5),
                                               "final.json": snapshot(7, INC7, final=True)})
    runner = FakeRunner()
    result = G.audit_campaign(root / "campaigns" / INSTANCE, tmp_path / "audit",
                              sigma_node=SIGMA, runner=runner)
    w = {row["w"]: row for row in result["w"]}
    assert w[5]["audited"] is True and w[5]["Y"] == pytest.approx(0.5 / SIGMA)
    assert w[10]["missing_w"] is True and w[10]["Y"] is None
    final = result["final"]
    assert final["w"] == 7 and final["primary"] is True
    assert final["Y"] == pytest.approx(0.7 / SIGMA)
    assert final["audit_record"].endswith(f"w7/{INSTANCE}.json")
    assert (tmp_path / "audit" / STAGE / ARM / f"r{REP}" / "w5" / f"{INSTANCE}.json").is_file()
    assert (tmp_path / "audit" / "Y_final.jsonl").is_file()
    assert (tmp_path / "audit" / "Y_w.jsonl").is_file()
    assert (tmp_path / "audit" / "SHA256SUMS").is_file()
    # 10 seeds x 3 configurations (w5 incumbent, start once, final incumbent; start cached)
    assert runner.calls == 4


def test_w_zero_is_y_zero_without_running(tmp_path):
    root = write_campaign(tmp_path / "chunk", {"final.json": snapshot(0, START, final=True,
                                                                     ended_on="llm_call_cap")})
    runner = FakeRunner()
    result = G.audit_campaign(root / "campaigns" / INSTANCE, tmp_path / "audit",
                              sigma_node=SIGMA, runner=runner)
    assert result["final"]["Y"] == 0.0 and result["final"]["audited"] is False
    assert runner.calls == 0


def test_cache_reuses_runs_across_calls(tmp_path):
    root = write_campaign(tmp_path / "chunk", {"w5.json": snapshot(5, INC5),
                                               "final.json": snapshot(7, INC7, final=True)})
    cache = G.Cache(tmp_path / "cache.jsonl")
    first = FakeRunner()
    G.audit_campaign(root / "campaigns" / INSTANCE, tmp_path / "audit1",
                     sigma_node=SIGMA, runner=first, cache=cache)
    second = FakeRunner()
    result = G.audit_campaign(root / "campaigns" / INSTANCE, tmp_path / "audit2",
                              sigma_node=SIGMA, runner=second, cache=cache)
    assert second.calls == 0
    assert result["final"]["cache"]["incumbent_hits"] == 10
    assert result["w"][0]["cache"]["start_hits"] == 10


def test_final_at_w20_aliases_the_w20_record(tmp_path):
    root = write_campaign(tmp_path / "chunk", {"w5.json": snapshot(5, INC5),
                                               "w10.json": snapshot(10, INC5),
                                               "w15.json": snapshot(15, INC5),
                                               "w20.json": snapshot(20, INC7),
                                               "final.json": snapshot(20, INC7, final=True)})
    result = G.audit_campaign(root / "campaigns" / INSTANCE, tmp_path / "audit",
                              sigma_node=SIGMA, runner=FakeRunner())
    assert result["final"]["alias_of_w"] == 20
    assert result["final"]["audit_record"].endswith(f"w20/{INSTANCE}.json")
    assert not (tmp_path / "audit" / STAGE / ARM / f"r{REP}" / "w20" / f"{INSTANCE}.json").read_text() == ""


def test_a_failed_or_missing_seed_is_a_stop(tmp_path):
    root = write_campaign(tmp_path / "chunk", {"final.json": snapshot(7, INC7, final=True)})
    with pytest.raises(G.AuditStop):
        G.audit_campaign(root / "campaigns" / INSTANCE, tmp_path / "audit", sigma_node=SIGMA,
                         runner=FakeRunner(fail_seed=6701))
    root2 = write_campaign(tmp_path / "chunk2", {"final.json": snapshot(7, INC7, final=True)})
    with pytest.raises(G.AuditStop):
        G.audit_campaign(root2 / "campaigns" / INSTANCE, tmp_path / "audit2", sigma_node=SIGMA,
                         runner=FakeRunner(drop_seed=6701))


def test_final_at_a_w_point_with_a_different_config_gets_its_own_record(tmp_path):
    # w10 is the pre-decision incumbent; the final after the last keep is INC7. Both must survive.
    root = write_campaign(tmp_path / "chunk", {"w5.json": snapshot(5, INC5),
                                               "w10.json": snapshot(10, INC5),
                                               "final.json": snapshot(10, INC7, final=True)})
    result = G.audit_campaign(root / "campaigns" / INSTANCE, tmp_path / "audit",
                              sigma_node=SIGMA, runner=FakeRunner())
    assert result["final"]["audit_record"] == f"{STAGE}/{ARM}/r{REP}/final/w10/{INSTANCE}.json"
    assert (tmp_path / "audit" / STAGE / ARM / f"r{REP}" / "w10" / f"{INSTANCE}.json").is_file()
    w10 = [r for r in result["w"] if r["w"] == 10][0]
    assert w10["config_sha256"] != result["final"]["config_sha256"]
