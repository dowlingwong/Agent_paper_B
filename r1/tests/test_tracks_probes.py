"""Track S probes (S0.1 determinism, S1.1 factorial): pure parts only. AI-assisted (Claude, 29 Oct 2026)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from r1.tracks.probes import determinism as D
from r1.tracks.probes import s1_factorial as F


def test_payload_matches_the_harness_request_shape():
    p = D.chat_payload("hi", 123, "r1-manager")
    # Final review MAJOR 6: the harness's own request body (no max_tokens: the harness sets none).
    assert p == {"model": "r1-manager", "messages": [{"content": "hi", "role": "user"}], "temperature": 0.2,
                 "seed": 123, "stream": False}


def test_identity_and_cross_identity():
    # A prompt with a missing or errored repeat is NOT identical (review m7).
    assert D.identity_rate({0: ["a", "a"], 1: ["b", "c"], 2: ["d"]}) == pytest.approx(1 / 3)
    assert D.identity_rate({0: ["a", "a"], 1: ["b", None]}, repeats=2) == 0.5
    assert D.identity_rate({0: ["a", "a"], 1: ["b"]}, repeats=2) == 0.5
    assert D.identity_rate({}) is None
    per = {"u1": {0: ["a", "a"], 1: ["b", "b"]}, "u2": {0: ["a", "x"], 1: ["c", "c"]}}
    assert D.cross_identity(per) == 0.5
    assert D.cross_identity({"u1": {0: [None], 1: ["b"]}, "u2": {0: [None], 1: ["b"]}}) == 0.5
    assert D.cross_identity({"u1": per["u1"]}) is None


def test_latency_stats_nearest_rank_p95():
    s = D.latency_stats([float(i) for i in range(1, 101)])
    assert s["mean_s"] == pytest.approx(50.5) and s["p95_s"] == 95.0 and s["n"] == 100
    assert D.latency_stats([])["p95_s"] is None
    assert D.cpu_census()["cpus"] >= 1


def test_fixed_prompts_are_deterministic_and_seeded():
    a, b = D.fixed_prompts(3), D.fixed_prompts(3)
    assert a == b and len({p["seed"] for p in a}) == 3
    assert "Budget index (trial number): 2" in a[0]["prompt"]
    # Both prompt shapes are probed: empty memory and a memory block (review m7).
    assert "No prior trial memory available." in a[0]["prompt"]
    assert "Prior trial memory:" in a[1]["prompt"] and "skipped by the control plane" in D.memory_text(3)


def test_payload_can_carry_the_sweep1_grammar():
    p = D.chat_payload("hi", 1, "m", proposal_schema="manager_proposal/v1")
    assert p["response_format"]["type"] == "json_schema"
    assert p["response_format"]["json_schema"]["name"] == "manager_proposal_v1"
    assert "response_format" not in D.chat_payload("hi", 1, "m")


def test_factorial_design_and_levels():
    files = {"train.py": "HIDDEN_UNITS = 32\nBATCH_SIZE = 64\nLEARNING_RATE_INIT = 1e-3\n"}
    cells = F.design(files, "HIDDEN_UNITS", "LEARNING_RATE_INIT")
    assert cells["00"] == files
    assert "HIDDEN_UNITS = 64" in cells["10"]["train.py"] and "LEARNING_RATE_INIT = 1e-3" in cells["10"]["train.py"]
    assert "LEARNING_RATE_INIT = 0.002" in cells["01"]["train.py"] and "HIDDEN_UNITS = 32" in cells["01"]["train.py"]
    assert "HIDDEN_UNITS = 64" in cells["11"]["train.py"] and "LEARNING_RATE_INIT = 0.002" in cells["11"]["train.py"]
    custom = F.design(files, "HIDDEN_UNITS", "BATCH_SIZE", F.parse_levels(["BATCH_SIZE=16,128"]))
    assert "BATCH_SIZE = 16" in custom["00"]["train.py"] and "BATCH_SIZE = 128" in custom["01"]["train.py"]
    yaml = {"config.yaml": "C: 0.01\nmax_iter: 100\n"}
    cy = F.design(yaml, "max_iter", "C")
    assert "max_iter: 200" in cy["10"]["config.yaml"] and "C: 0.02" in cy["01"]["config.yaml"]
    assert F.DEFAULT_PAIRS["openml_breast_w"] == [("max_iter", "C")]
    assert len(F.DEFAULT_PAIRS["digits_mlp"]) == 3 and len(F.S11_SEEDS) == 30


def test_interaction_contrast_and_intervals():
    rng = np.random.default_rng(0)
    n = 30
    base = rng.normal(0.9, 0.01, n)
    y = {"00": list(base), "10": list(base + 0.02), "01": list(base + 0.01),
         "11": list(base + 0.03 + 0.005 + rng.normal(0, 0.001, n))}
    r = F.interaction(y)
    assert r["n"] == n and r["interaction"] == pytest.approx(0.005, abs=0.001)
    assert r["ci95_t"][0] < r["interaction"] < r["ci95_t"][1] and r["ci95_boot"][0] < r["ci95_boot"][1]
    assert r["main_A"] == pytest.approx(0.0225, abs=0.001) and r["main_B"] == pytest.approx(0.0125, abs=0.001)
    y["00"][0] = None
    assert F.interaction(y)["n"] == n - 1
