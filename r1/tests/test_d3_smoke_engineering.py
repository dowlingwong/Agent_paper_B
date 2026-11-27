"""Synthetic CPU tests for the D.3 per-arm engineering smoke driver (no GPU, no campaign)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from r1.c3 import d3_analysis as D3
from r1.c3.d3 import adapter as A
from r1.c3.d3 import audit as G
from r1.scripts import d3_smoke_engineering as S


def _manifest():
    return SimpleNamespace(raw={"campaign_model_source": {"path": "x.md", "sha256": "a" * 64}})


def test_smoke_spec_refuses_deployment_seeds_and_unknown_nodes():
    observed = {"host": "TASL-2"}
    good = S._spec("A0", node="digits_mlp", seed=6301, manifest=_manifest(),
                   observed=observed, run_id="test")
    assert good.instance_seeds == (6301,)
    assert good.launcher == "direct"
    assert good.notes["engineering_only"] is True
    with pytest.raises(A.AdapterStop):
        S._spec("A0", node="digits_mlp", seed=6201, manifest=_manifest(),
                observed=observed, run_id="test")
    with pytest.raises(A.AdapterStop):
        S._spec("A0", node="tabular_mlp", seed=6301, manifest=_manifest(),
                observed=observed, run_id="test")


def test_smoke_arms_are_the_seven_declared_rule_arms_and_never_learned():
    assert set(S.SMOKE_ARMS) == set(D3.ARMS_D3A)
    assert not set(S.SMOKE_ARMS) & set(A.LEARNED_ARMS)


def test_smoke_audit_block_is_disjoint_from_every_deployment_block_and_reserved_set():
    smoke = set(G.audit_seeds(6301)) | set(G.audit_seeds(6302))
    deployment = {s for seed in D3.INSTANCE_SEEDS for s in G.audit_seeds(seed)}
    assert not smoke & deployment
    assert smoke == set(range(6391, 6411))
    for block in D3.declared_d3_seeds().values():
        assert not smoke & block


def test_smoke_record_is_self_hashed_and_revalidated(tmp_path):
    record = {"schema": "r1_d3_smoke/v1", "engineering_only": True, "task": "test",
              "run_id": "test", "stage": "a", "node": "digits_mlp", "seed": 6301,
              "arms": list(S.SMOKE_ARMS), "chunks": {}, "sigma_node": 0.0066}
    record["record_sha256"] = S._write_json(tmp_path / "smoke.json", record)
    assert S._validate_smoke(tmp_path)["seed"] == 6301
    tampered = dict(record)
    tampered.pop("record_sha256")
    tampered["seed"] = 6201
    S._write_json(tmp_path / "smoke.json", tampered)
    with pytest.raises(Exception):
        S._validate_smoke(tmp_path)
