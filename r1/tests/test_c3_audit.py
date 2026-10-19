"""C3 audit: pairing, cache, resumable plan runner. ENGINEERING_ONLY; AI-assisted (Claude)."""
import json
import os
from pathlib import Path

import pytest

from r1.c3 import audit


def test_paired():
    r = audit.paired([1.0, 2.0, None, 4.0], [0.5, 1.0, 1.0, 3.0])
    assert r["k"] == 3 and r["delta_audit"] == pytest.approx((0.5 + 1 + 1) / 3)
    assert audit.paired([None], [1.0])["delta_audit"] is None


def fake_run_config(node, files, seeds, tmp):
    base = float(files["train.py"].split("=")[1])
    return [{"seed": s, "success": True, "failure": None, "metric": base + 0.001 * (s - 7000),
             "changed_files": False, "wall_seconds": 0.0} for s in seeds]


def test_run_plan_caches_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "run_config", fake_run_config)
    monkeypatch.setattr(audit, "ProcessPoolExecutor", _InlinePool)
    configs = {"c": {"node": "n", "files": {"train.py": "X = 0.9"}}, "i": {"node": "n", "files": {"train.py": "X = 0.8"}}}
    plan = [{"proposal_id": "p1", "node": "n", "candidate_hash": "c", "incumbent_hash": "i", "reason": "random"}]
    st = audit.run_plan(plan, configs, tmp_path, seeds=(7001, 7002), workers=1, deadline=100)
    assert st["configs_run_this_call"] == 2 and st["proposals_complete"] == 1
    st2 = audit.run_plan(plan, configs, tmp_path, seeds=(7001, 7002), workers=1, deadline=100)
    assert st2["configs_run_this_call"] == 0
    res = audit.audit_results(plan, audit.RunCache(tmp_path / "runs.jsonl"), (7001, 7002))
    assert res[0]["delta_audit"] == pytest.approx(0.1) and res[0]["se"] == pytest.approx(0.0)
    # deadline 0: nothing submitted, nothing lost
    plan2 = plan + [{"proposal_id": "p2", "node": "n", "candidate_hash": "c", "incumbent_hash": "i", "reason": "x"}]
    st3 = audit.run_plan(plan2, configs, tmp_path, seeds=(7001, 7002, 7003), workers=1, deadline=0)
    assert st3["configs_run_this_call"] == 0 and st3["configs_remaining"] == 2


class _Fut:
    def __init__(self, v):
        self.v = v

    def result(self):
        return self.v

    def done(self):
        return True

    def __hash__(self):
        return id(self)


class _InlinePool:
    def __init__(self, max_workers=1):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def submit(self, fn, *args):
        return _Fut(fn(*args))


@pytest.fixture(autouse=True)
def _inline_wait(monkeypatch):
    monkeypatch.setattr(audit, "wait", lambda futs, return_when=None, timeout=None: (set(futs), set()))


HARNESS = Path(os.environ.get("AR_HARNESS_ROOT", Path(__file__).resolve().parents[3] / "autoresearch_harness"))


@pytest.mark.skipif(not (HARNESS / "nodes" / "tabular_mlp").exists() or os.environ.get("C3_SKIP_WORKER") == "1",
                    reason="harness checkout not available")
def test_real_worker_run_is_seed_deterministic(tmp_path):
    files = {"train.py": (HARNESS / "nodes" / "tabular_mlp" / "train.py").read_text()}
    a = audit.run_config("tabular_mlp", files, [7001, 7001], str(tmp_path))
    assert all(r["success"] for r in a), a
    assert a[0]["metric"] == a[1]["metric"]
