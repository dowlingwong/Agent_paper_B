import hashlib
import json
from types import SimpleNamespace

import pytest
import yaml

from r1.c3 import d3_hpo_ref as hpo
from r1.c3.d3 import audit, hpo_runner
from r1.c3.d3.snapshots import config_sha256
from r1.harness import harness_root


def start_hash(node, path):
    start = (harness_root() / "nodes" / node / path).read_text(encoding="utf-8")
    return config_sha256({path: start})


class SyntheticWorker:
    calls = []

    def __init__(self, *, node_root, artifact_dir, timeout_seconds):
        assert timeout_seconds == 600
        self.root = node_root
        self.attempt = artifact_dir.parent.name

    def run_trial_at_seed(self, proposal, spec, index, *, train_seed, split_seed):
        assert train_seed == split_seed == 6201
        if self.attempt == "attempt-001" and index == 2:
            raise hpo.InfrastructureFailure("synthetic worker interruption")
        files = {rel: (self.root / rel).read_text(encoding="utf-8") for rel in spec.editable_paths}
        self.calls.append((self.attempt, index, config_sha256(files), files))
        return SimpleNamespace(success=True, changed_files=(), parsed_metrics={spec.metric_name: metric(files)})


def metric(files):
    digest = config_sha256(files)
    return int(digest[:8], 16) / 16**8


def synthetic_audit(node, files, seeds):
    return [audit.Run(seed=s, metric=metric(files), run_sha256=hashlib.sha256(str(s).encode()).hexdigest())
            for s in seeds]


@pytest.mark.parametrize("arm,node,editable", [("RS", "digits_mlp", "train.py"),
                                                ("SMAC3", "openml_climate", "config.yaml")])
def test_campaign_uses_g1_hash_and_the_real_g6_audit_contract(tmp_path, arm, node, editable):
    if arm == "SMAC3":
        try:
            hpo.require_smac()
        except hpo.SmacUnavailable as exc:
            pytest.skip(str(exc))
    SyntheticWorker.calls = []
    start = start_hash(node, editable)
    root = tmp_path / "run"
    campaign = hpo_runner.run_cpu_campaign(arm, node, 6201, 0, root, expected_start_sha256=start,
                                            worker_factory=SyntheticWorker)
    summary = json.loads((campaign / "summary.json").read_text())
    records = json.loads((campaign / "charged_runs.json").read_text())
    assert summary["start_config_hash"] == start
    assert summary["worker_runs"] == len(records) == 20
    assert summary["infra_attempts"] == 2
    assert (root / "attempt-001" / "infrastructure.json").is_file()
    assert SyntheticWorker.calls[0][2] == SyntheticWorker.calls[1][2]
    assert [r["config_sha256"] for r in records] == [d for _, _, d, _ in SyntheticWorker.calls[1:]]
    if arm == "SMAC3":
        assert len(list(root.glob("attempt-*/smac/**/scenario.json"))) == 2
        initial = {digest for _, _, digest, _ in SyntheticWorker.calls[1:6]}
        assert len(initial) == 5 and start in initial
        assert json.loads((campaign / "runtime.json").read_text())["smac_distributions"] == hpo.SMAC_PINS
        for _, _, _, files in SyntheticWorker.calls:
            assert type(yaml.safe_load(files[editable])["C"]) is float

    calls = []

    def audit_once(node, files, seeds):
        keys = [(config_sha256(files), s) for s in seeds]
        assert not set(keys).intersection(calls)
        calls.extend(keys)
        assert list(seeds) == list(range(6701, 6711))
        return synthetic_audit(node, files, seeds)

    output = tmp_path / "audit"
    row = hpo_runner.audit_cpu_campaign(campaign, output, sigma_node=0.1, scratch=tmp_path,
                                       cache=audit.Cache(tmp_path / "cache.jsonl"), runner=audit_once)
    assert row["start_config_hash"] == start and row["final_config_hash"] == summary["final_config_hash"]
    assert row["y_raw_w"]["20"] == row["y_raw"]
    assert row["worker_runs"] == 20 and row["llm_calls"] == 0
    assert (output / "SHA256SUMS").is_file()
    assert len(list((output / "keeps").glob("*.json"))) == summary["keeps"]
    assert json.loads((output / "outcome_row.json").read_text()) == row


def test_g1_start_hash_mismatch_refuses_before_a_worker_attempt(tmp_path):
    with pytest.raises(hpo.HpoRefError, match="matched G1 start hash"):
        hpo_runner.run_cpu_campaign("RS", "digits_mlp", 6201, 0, tmp_path / "run",
                                    expected_start_sha256="0" * 64, worker_factory=SyntheticWorker)
    assert not (tmp_path / "run").exists()


def test_smac_requires_incumbent_at_the_declared_budget(tmp_path):
    from r1.tests.test_d3_hpo_ref import FakeSmac, start_of, synthetic_space

    class NoIncumbent(FakeSmac):
        def incumbent(self):
            return None

    node = "digits_mlp"
    with pytest.raises(hpo.HpoRefError, match="without naming an incumbent"):
        hpo.run_smac3(synthetic_space(node), start_of(node), 6201, 0, lambda *a: hpo.EvalResult(True, 0.5),
                     backend_factory=NoIncumbent)


def test_seal_detects_modified_snapshot_before_audit(tmp_path):
    node = "digits_mlp"
    campaign = hpo_runner.run_cpu_campaign("RS", node, 6201, 0, tmp_path / "run",
                                           expected_start_sha256=start_hash(node, "train.py"),
                                           worker_factory=SyntheticWorker)
    with (campaign / "snapshots" / "final.json").open("a") as handle:
        handle.write(" ")
    with pytest.raises(hpo.HpoRefError, match="seal does not match"):
        hpo_runner.audit_cpu_campaign(campaign, tmp_path / "audit", sigma_node=0.1, scratch=tmp_path,
                                      cache=audit.Cache(tmp_path / "cache.jsonl"), runner=synthetic_audit)
    assert not (tmp_path / "audit").exists()
