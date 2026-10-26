"""RUNBOOK Track P 1.7: E0 generator (hashed, committed) and E6 probe constructors with the spec's criteria.

ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import hashlib

import numpy as np
import pytest

from r1.c3.labels import EDGES
from r1.c3.train import exam_synthetic as E
from r1.c3.train import serialize as S
from r1.c3.train.types import BIN_OPTIONS, MAX_TOKENS


@pytest.fixture(scope="module")
def items():
    return E.load()


@pytest.fixture(scope="module")
def pool():
    try:
        return S.pool_tokenizers()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"pool tokenizers unavailable: {exc}")


def test_committed_set_matches_its_hash_and_regenerates_byte_identically(items):
    data = E.E0_FILE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == E.E0_SHA.read_text().split()[0]
    assert E.to_bytes(E.generate()) == data
    assert len(items) == E.N_TRAIN + E.N_TEST and all(it["version"] == E.E0_VERSION for it in items)


def test_grid_split_and_held_out_cells(items):
    train = [it for it in items if it["split"] == "train"]
    test = [it for it in items if it["split"] == "test"]
    assert len(train) == 3000 and len(test) == 1000
    held = {tuple(c) for c in E.HELDOUT}
    assert not any(tuple(it["cell"]) in held for it in train)
    assert all(tuple(it["cell"]) in held for it in test)
    assert {it["heldout_kind"] for it in test} == {"interp", "extrap"}
    for it in items:
        assert -2.5 <= it["m"] <= 2.5 and 0.1 <= it["s"] <= 1.5
        assert E.cell_of(it["m"], it["s"]) == tuple(it["cell"])
        assert E.note_line(it["m"], it["s"]) in it["prompt"]["proposal"].splitlines()
        assert it["prompt"]["options"] == list(BIN_OPTIONS)


def test_targets_are_the_binned_normal_and_its_argmax(items):
    from scipy.stats import norm
    for it in items[::97]:
        y = np.array(it["y_soft"])
        ref = np.diff(norm.cdf((EDGES - it["m"]) / it["s"]))
        assert y[0] == 0 and abs(y.sum() - 1) < 1e-9 and np.allclose(y[1:], ref / ref.sum(), atol=1e-12)
        h = np.array(it["y_hard"])
        assert h.sum() == 1 and h.argmax() == y.argmax() and h[0] == 0


def test_rps_hand_computed():
    p = np.zeros(12); p[0] = 0.2; p[3] = 0.8
    y = np.zeros(12); y[5] = 1.0
    # cumulative over bins 1..11: P = 0,0,.8,.8,.8,... ; Y = 0,0,0,0,1,...  -> 2 * .64 + 7 * .04 ; Brier .04
    assert E.rps(p, y) == pytest.approx(2 * 0.64 + 7 * 0.04 + 0.04)
    assert E.rps(y, y) == 0


def test_perfect_predictor_passes_e0_and_hard_labels_collapse(items):
    test = [it for it in items if it["split"] == "test"]
    perfect = E.e0_metrics(np.array([it["y_soft"] for it in test]), test)
    assert perfect["rps"] == pytest.approx(0, abs=1e-12) and perfect["width_ratio"] == pytest.approx(1)
    assert E.e0_pass(perfect)
    hard = E.e0_metrics(np.array([it["y_hard"] for it in test]), test)
    assert hard["width_ratio"] == 0 and not E.e0_pass(hard)
    # a predictor that ignores s (fixed width) fails the width criterion
    fixed = np.array([E.soft_target(it["m"], 0.8) for it in test])
    assert not E.e0_pass(E.e0_metrics(fixed, test))


def test_every_e0_prompt_fits_every_pool_tokenizer(items, pool):
    texts = [S.render_text(E.prompt_from_dict(it["prompt"])) for it in items]
    for name, tok in pool.items():
        assert max(S.count_tokens(tok, t) for t in texts) <= MAX_TOKENS - S.FRAMING_RESERVE, name


def test_a1_a2_constructors_and_criteria():
    a1 = E.a1_probe(n_states=4)
    for st in a1:
        assert st["alone"][0] == st["packed"][0] and len(st["packed"]) == 8
        assert len({p.state for p in st["packed"]}) == 1 and len({p.group for p in st["packed"]}) == 1
        assert len({p.proposal for p in st["packed"]}) > 1
    z = np.random.default_rng(0).normal(size=12)
    assert E.a1_pass(z, z + 5e-4)["pass"] and not E.a1_pass(z, z + 2e-3)["pass"]
    a2 = E.a2_probe(n_states=3)
    st = a2[0]
    assert st["orders"][0] == list(range(8)) and len(st["orders"]) == 5
    logits = np.random.default_rng(1).normal(size=(8, 12))
    by_order = [logits[np.asarray(o)] for o in st["orders"]]       # a perfectly order-invariant model
    assert E.a2_pass(by_order, st["orders"])["pass"]
    by_order[2] = by_order[2] + 0.01
    assert not E.a2_pass(by_order, st["orders"])["pass"]


def test_a3_prepends_irrelevant_history_of_the_stated_length(pool):
    tok = pool["qwen3.5-0.8b-base"]
    a3 = E.a3_probe(tok, n=5)
    base = a3["prompts"][0]
    for L in E.A3_LENGTHS[1:]:
        for b, p in zip(base, a3["prompts"][L]):
            assert p.proposal == b.proposal and p.meta["over_limit"]
            extra = S.count_tokens(tok, p.state) - S.count_tokens(tok, b.state)
            assert L <= extra <= L + 100
            hist = p.state.split("History (oldest first):\n")[1].splitlines()
            assert hist[0].startswith("t1000:")
    r0 = np.full(5, 0.10)
    assert E.a3_pass({0: r0, 2000: r0 + 0.005, 8000: r0 - 0.009})["pass"]
    assert not E.a3_pass({0: r0, 2000: r0 + 0.02, 8000: r0})["pass"]


def test_a4_steps_and_criterion():
    a4 = E.a4_probe(n=3)
    for row in a4:
        notes = [ln for p in row for ln in p.proposal.splitlines() if ln.startswith("Forecast note")]
        ms = {n.split("m = ")[1].split(",")[0] for n in notes}
        ss = [float(n.split("s = ")[1]) for n in notes]
        assert len(ms) == 1 and ss == sorted(ss) and len(ss) == E.A4_STEPS
    std = np.tile(np.linspace(0.2, 1.0, 5), (100, 1))
    assert E.a4_pass(std)["pass"]
    std[:6, 3] = 0.0    # 6 % of prompts not monotone
    assert not E.a4_pass(std)["pass"]


def test_a5_permutations_and_unpermute():
    a5 = E.a5_probe(n=3)
    for row in a5:
        assert row[0].options == BIN_OPTIONS
        for p in row:
            perm = p.meta["option_perm"]
            assert list(p.options) == [BIN_OPTIONS[i] for i in perm]
    belief = E.soft_target(0.3, 0.6)
    perm = a5[0][1].meta["option_perm"]
    listed = belief[np.asarray(perm)]
    assert np.allclose(E.unpermute(listed, perm), belief)
    b = np.stack([np.stack([belief] * 5)] * 4)
    assert E.a5_pass(b)["pass"]
    b[0, 2, 1] += 0.05
    b[0, 2, 2] -= 0.05
    assert not E.a5_pass(b)["pass"]
