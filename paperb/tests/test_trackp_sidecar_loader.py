"""Track P 1.11: the real sidecar loader (TorchLoraLoader) on a tiny model, P.7 pin, fallback unchanged.

ENGINEERING_ONLY; AI-assisted (Claude). CPU; needs the Qwen3.5 tokenizer in the local HF cache (skips otherwise).
"""
from __future__ import annotations

import json
import os
import time

import pytest

torch = pytest.importorskip("torch")  # not in the harness lock; present on the Track P hosts

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

from r1.c3.prior_model import FixedPrior, SidecarPrior  # noqa: E402
from r1.c3.serve import FakeLoader, Pin, PinError, Sidecar, TorchLoraLoader, write_model_pin  # noqa: E402
from r1.c3.train import tiny  # noqa: E402
from r1.c3.train.types import DecisionPrompt  # noqa: E402

A1 = [1 / 12] * 12
PROMPT = {"state": "node digits_mlp; budget 4 of 20 used; incumbent lr=0.01", "proposal": "set lr from 0.01 to 0.003"}


@pytest.fixture(scope="module")
def saved(tmp_path_factory):
    try:
        tiny.tokenizer(*tiny.QWEN)
    except Exception:
        pytest.skip("Qwen3.5 tokenizer not in the local HF cache")
    work = tmp_path_factory.mktemp("tiny")
    model = tiny.build_tiny("kev", work)
    with torch.no_grad():
        for p in model.trainable_parameters():
            p.add_(0.05 * torch.randn_like(p))
    model.save(work / "saved")
    model.eval()
    with torch.no_grad():
        ref = torch.softmax(model([DecisionPrompt(**PROMPT)])["belief_logits"][0], -1).tolist()
    builder = lambda spec: tiny.build_tiny(spec["family"], work)  # noqa: E731
    pin = write_model_pin(work / "saved", work / "A5_pin.json", name="A5", base="tiny/qwen35@0",
                          model={"family": "kev", "base_path": "tiny", "head_form": "softmax12"})
    return {"work": work, "pin": pin, "ref": ref, "builder": builder}


def test_sidecar_serves_the_pinned_model(saved):
    sc = Sidecar(Pin.load(saved["pin"]), TorchLoraLoader(saved["builder"]))
    url = sc.start()
    try:
        prior = SidecarPrior(url, FixedPrior(A1, "A1"), expected_digest=sc.digest, timeout_s=30)
        fc = prior.forecast({"node": "digits_mlp", "features": {}, "prompt": PROMPT})
        assert fc.fallback is None
        assert fc.probs == pytest.approx(saved["ref"], abs=1e-6)
        # a row without the serialised view: the loader refuses, the client falls back to A1 (unchanged path)
        fb = prior.forecast({"node": "digits_mlp", "features": {}})
        assert fb.fallback.startswith("prior_unavailable") and list(fb.probs) == A1
    finally:
        sc.stop()


def test_timeout_fallback_is_unchanged(saved):
    sc = Sidecar(Pin.load(saved["pin"]), TorchLoraLoader(saved["builder"]), delay_s=1.5)
    url = sc.start()
    try:
        fc = SidecarPrior(url, FixedPrior(A1, "A1"), timeout_s=1.0).forecast(
            {"node": "digits_mlp", "features": {}, "prompt": PROMPT})
        assert fc.fallback == "prior_unavailable: timeout" and list(fc.probs) == A1
        time.sleep(1.5)  # let the delayed request finish its forward before the process exits (daemon threads)
    finally:
        sc.stop()


def test_tampered_pin_or_spec_is_refused(saved, tmp_path):
    data = json.loads(saved["pin"].read_text())
    bad = dict(data, files={**data["files"], "head": {**data["files"]["head"], "sha256": "0" * 64}})
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(PinError):
        Sidecar(Pin.load(p), TorchLoraLoader(saved["builder"]))
    nospec = {k: v for k, v in data.items() if k != "model"}
    p.write_text(json.dumps(nospec))
    with pytest.raises(PinError, match="model"):
        Sidecar(Pin.load(p), TorchLoraLoader(saved["builder"]))


def test_fake_pins_still_load_without_a_model_spec(tmp_path):
    from r1.c3.serve import write_fake_pin
    pin = Pin.load(write_fake_pin(tmp_path))
    assert pin.model is None
    sc = Sidecar(pin, FakeLoader({"default": A1}))
    assert sc.predict({"node": "x"}) == A1
