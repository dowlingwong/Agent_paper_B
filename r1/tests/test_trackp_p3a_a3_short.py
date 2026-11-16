"""CPU-only tests for the P.3a attempt-2 A3-short execution delta (R1-P3A-OOM-OPTION3).

The flag makes the budget-v2 branch of ``exam_run.probes`` skip the descriptive 2k/8k A3 levels that OOMed the
attempt-1 ``qwen3.5-4b-base`` probes unit. No model, tokenizer, GPU or data file is used: the probe constructors
and ``predict`` are stubbed; the A3 budget-v2 path itself is a plain dict fixture.
"""
from __future__ import annotations

import contextlib
from types import SimpleNamespace

import numpy as np
import pytest

from r1.c3.train import exam_run as X
from r1.c3.train import exam_synthetic as E
from r1.scripts import trackp

DESCRIPTIVE = tuple(E.A3_DESCRIPTIVE)


def _model():
    return SimpleNamespace(family="fake", packing=False, head_form="linear12", bin_order=list(range(12)),
                           tok=object())


class Stub:
    """Record which probe constructors/executors ran; return shapes the unchanged code can consume."""

    def __init__(self, monkeypatch, *, fail_descriptive: bool):
        self.a3_probe_calls: list[tuple] = []
        self.a3_rps_keys: list[str] = []
        self.fail_descriptive = fail_descriptive

        def fake_a3_probe_budget(counters, n=100, seed=None):
            return {"targets": [np.zeros(12)], "prompts": {0.0: [SimpleNamespace(meta={})]},
                    "budget": [1024], "tokens": {0.0: [{"fake": 12}]}, "reached": {0.0: [0.0]},
                    "limit": 1024, "families": ["fake"]}

        def recording_a3_probe(tok, n=100, lengths=E.A3_LENGTHS, seed=None):
            self.a3_probe_calls.append(tuple(lengths))
            if self.fail_descriptive:
                raise AssertionError("the descriptive E.a3_probe must not run with a3_short")
            prompts = {L: [SimpleNamespace(meta={})] for L in lengths}
            return {"prompts": prompts, "targets": [np.zeros(12) for _ in prompts[lengths[0]]]}

        def recording_a3_rps(model, prompts, targets, errors, key):
            self.a3_rps_keys.append(str(key))
            if self.fail_descriptive and str(key).startswith("descriptive_"):
                raise AssertionError("a descriptive _a3_rps must not run with a3_short")
            return np.linspace(0.1, 0.2, len(prompts))

        monkeypatch.setattr(E, "a3_probe_budget", fake_a3_probe_budget)
        monkeypatch.setattr(E, "a3_probe", recording_a3_probe)
        monkeypatch.setattr(X, "_a3_rps", recording_a3_rps)
        monkeypatch.setattr(X, "predict",
                            lambda model, prompts, batch_size=16: np.full((len(prompts), 12), 1.0 / 12.0))
        monkeypatch.setattr(E, "belief_moments", lambda p: (np.zeros(2), np.array([1.0, 2.0])))
        monkeypatch.setattr(E, "a4_probe", lambda n=200, steps=None, seed=None: [[SimpleNamespace()]])  # noqa: ARG005
        monkeypatch.setattr(E, "a4_label_std", lambda n=200, steps=None, seed=None: np.array([[1.0, 2.0]]))  # noqa: ARG005


def _probes(monkeypatch, tmp_path, *, a3_short, fail_descriptive=False):
    stub = Stub(monkeypatch, fail_descriptive=fail_descriptive)
    out = X.probes(_model(), tmp_path / "probes", n=1, counters={"fake": lambda p: 1}, a3_short=a3_short)
    return out, stub


def test_a3_short_with_counters_skips_every_descriptive_call(monkeypatch, tmp_path):
    out, stub = _probes(monkeypatch, tmp_path, a3_short=True, fail_descriptive=True)
    assert stub.a3_probe_calls == []                        # E.a3_probe never called (and would have failed)
    assert not any(k.startswith("descriptive_") for k in stub.a3_rps_keys)
    assert out["A3_descriptive"] == {"skipped": "R1-P3A-OOM-OPTION3", "levels": list(E.A3_DESCRIPTIVE),
                                     "pass": None}
    # the A3 budget-v2 path itself ran (only the descriptive levels are skipped)
    assert out["A3"]["protocol"] == "v2_budget"
    assert out["A3"]["limit"] == 1024
    assert "frac_0.0" in stub.a3_rps_keys or "frac_0" in stub.a3_rps_keys


def test_flag_off_runs_descriptive_exactly_as_before(monkeypatch, tmp_path):
    out, stub = _probes(monkeypatch, tmp_path, a3_short=False)
    assert stub.a3_probe_calls == [(0,) + DESCRIPTIVE]      # lengths=(0,)+E.A3_DESCRIPTIVE
    assert {"descriptive_2000", "descriptive_8000"} <= set(stub.a3_rps_keys)
    assert "skipped" not in out["A3_descriptive"]
    assert out["A3_descriptive"]["pass"] is None
    assert out["A3_descriptive"]["mean_abs_drps"] == {2000: pytest.approx(0.0), 8000: pytest.approx(0.0)}


def test_a3_short_changes_no_other_output_key(monkeypatch, tmp_path):
    off, _ = _probes(monkeypatch, tmp_path, a3_short=False)
    on, _ = _probes(monkeypatch, tmp_path, a3_short=True)
    assert set(on) == set(off)
    assert {k: v for k, v in on.items() if k != "A3_descriptive"} == \
        {k: v for k, v in off.items() if k != "A3_descriptive"}
    assert set(on["A3_descriptive"]) == {"skipped", "levels", "pass"}


def test_a3_short_without_counters_is_refused(tmp_path):
    with pytest.raises(ValueError, match="counters"):
        X.probes(_model(), tmp_path / "probes", counters=None, a3_short=True)


def test_cli_refuses_a3_short_without_budget(tmp_path, capsys):
    rc = trackp.main(["probes", "--base", "kev-0.8b", "--run-dir", str(tmp_path / "probes"), "--a3-short"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "STOP" in err and "--budget" in err
    assert not (tmp_path / "probes").exists()


def test_cli_refuses_a3_short_with_tiny(tmp_path, capsys):
    """--tiny never takes the budget-v2 counters, so it would silently reach the v1 A3 0/2k/8k path."""
    rc = trackp.main(["probes", "--tiny", "--family", "kev", "--allow-placeholders", "--run-dir",
                      str(tmp_path / "probes"), "--budget", "--a3-short"])
    assert rc == 2
    assert "--budget" in capsys.readouterr().err


def test_a3_short_is_probes_only(tmp_path):
    with pytest.raises(SystemExit):
        trackp.main(["e0", "--base", "kev-0.8b", "--run-dir", str(tmp_path / "e0"), "--a3-short"])


def test_cmd_probes_forwards_the_flag(monkeypatch, tmp_path):
    seen: dict = {}
    monkeypatch.setattr(trackp, "_lease", lambda args, lease_log: contextlib.nullcontext(None))
    monkeypatch.setattr(trackp, "seed_everything", lambda seed: None)
    monkeypatch.setattr(trackp, "_build",
                        lambda args, cfg: (SimpleNamespace(load=lambda p: None), None, None, {"family": "kev"}))
    monkeypatch.setattr(trackp, "_counters", lambda cfg: {"fake": lambda p: 1})
    monkeypatch.setattr(X, "probes",
                        lambda model, run_dir, **kw: seen.update(kw) or {"A3": {}, "A3_descriptive": {}})
    base = dict(seed=0, tiny=False, budget=True, run_dir=tmp_path, n_probe=100, load=None)
    trackp.cmd_probes(SimpleNamespace(**base, a3_short=True), {})
    assert seen["n"] == 100 and set(seen["counters"]) == {"fake"} and seen["a3_short"] is True
    seen.clear()
    trackp.cmd_probes(SimpleNamespace(**base, a3_short=False), {})
    assert seen["a3_short"] is False
