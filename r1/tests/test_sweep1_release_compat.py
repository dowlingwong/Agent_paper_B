"""Sweep-1 release compatibility replay (R1-SWEEP1-RELEASE-COMPAT option A): synthetic only.

The sealed sweep-1 table was built at ab79b4ce (v2 featurizer); main is v3.  These tests use synthetic table bytes
and a fake v2/v3 replay builder, never a real label/evaluation value or a sealed file.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from r1.c3 import analysis_guard, audit


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _meta(proposals: bytes, configs: bytes, classification: bytes, index: bytes, root: str) -> dict:
    return {
        "schema": "synthetic",
        "label": "EVIDENCE",
        "commit": "ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74",
        "classification": {"path": f"{root}/results/r1/evidence/C3_sweep_classification_20261028.json",
                           "sha256": _sha(classification), "native_index_label": "ENGINEERING_ONLY"},
        "sweep_index": {"path": "results/r1/pilot/C3_sweep_index_20261028T033315Z.json",
                        "sha256": _sha(index), "label": "ENGINEERING_ONLY"},
        "table_sha256": {"proposals.jsonl": _sha(proposals), "configs.json": _sha(configs)},
        "n_proposals": 2,
    }


class Fixture:
    def __init__(self, tmp_path: Path):
        self.table = tmp_path / "table"; self.table.mkdir()
        self.index = tmp_path / "index.json"; self.index.write_bytes(b'{"synthetic": "index"}\n')
        self.classification = tmp_path / "classification.json"
        self.classification.write_bytes(b'{"synthetic": "classification"}\n')
        self.proposals = b'{"proposal_id": "p1"}\n{"proposal_id": "p2"}\n'
        self.configs = b'{"c1": {}}\n'
        self.meta = _meta(self.proposals, self.configs, self.classification.read_bytes(), self.index.read_bytes(),
                          "/ceph/srv/sealed/paper")
        self._write(self.meta)

    def _write(self, meta: dict, *, proposals=None, configs=None, classification=None):
        proposals = self.proposals if proposals is None else proposals
        configs = self.configs if configs is None else configs
        (self.table / "proposals.jsonl").write_bytes(proposals)
        (self.table / "configs.json").write_bytes(configs)
        (self.table / "build.json").write_text(json.dumps(meta, sort_keys=True) + "\n")
        if classification is not None:
            self.classification.write_bytes(classification)

    def replay(self, *, proposals=None, configs=None, root="/work/dwong/paper", drop_commit=False):
        proposals = self.proposals if proposals is None else proposals
        configs = self.configs if configs is None else configs
        meta = copy.deepcopy(self.meta)
        meta["classification"]["path"] = f"{root}/results/r1/evidence/C3_sweep_classification_20261028.json"
        meta["sweep_index"]["path"] = f"{root}/results/r1/pilot/C3_sweep_index_20261028T033315Z.json"
        if drop_commit:
            meta.pop("commit", None)

        def builder(*, index, paper_root, classification, out):
            out = Path(out); out.mkdir()
            (out / "proposals.jsonl").write_bytes(proposals)
            (out / "configs.json").write_bytes(configs)
            (out / "build.json").write_text(json.dumps(meta, sort_keys=True) + "\n")
        return builder


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis_guard, "refuse_sealed", lambda *a: None)
    monkeypatch.setattr(analysis_guard, "guard_table", lambda *a, **k: None)
    monkeypatch.setattr(audit, "_local_scratch_mount", lambda p: ["xfs", "/dev/x"])
    return Fixture(tmp_path)


def test_compat_accepts_v2_table_with_work_root_provenance(fixture):
    audit._verify_replay(fixture.table, fixture.table.parent, fixture.index, fixture.classification,
                         replay_builder=fixture.replay(drop_commit=True))


def test_default_builder_refuses_v3_table(fixture, monkeypatch):
    def v3_builder(index, out, *, paper_root, classification):
        out = Path(out); out.mkdir()
        (out / "proposals.jsonl").write_bytes(fixture.proposals.replace(b"p2", b"v3"))
        (out / "configs.json").write_bytes(fixture.configs)
        (out / "build.json").write_text(json.dumps(fixture.meta))
    monkeypatch.setattr("r1.c3.dataset.build_from_sweep", v3_builder)
    with pytest.raises(ValueError, match="differs from full source replay"):
        audit._verify_replay(fixture.table, fixture.table.parent, fixture.index, fixture.classification)


def test_compat_refuses_tampered_proposals(fixture):
    with pytest.raises(ValueError, match="proposals.jsonl"):
        audit._verify_replay(fixture.table, fixture.table.parent, fixture.index, fixture.classification,
                             replay_builder=fixture.replay(proposals=fixture.proposals + b'{"proposal_id": "x"}\n'))


def test_compat_refuses_tampered_configs(fixture):
    with pytest.raises(ValueError, match="configs.json"):
        audit._verify_replay(fixture.table, fixture.table.parent, fixture.index, fixture.classification,
                             replay_builder=fixture.replay(configs=b'{"tampered": true}\n'))


def test_compat_refuses_tampered_classification_bytes(fixture):
    fixture._write(fixture.meta, classification=b'{"tampered": true}\n')
    with pytest.raises(ValueError, match="classification bytes"):
        audit._verify_replay(fixture.table, fixture.table.parent, fixture.index, fixture.classification,
                             replay_builder=fixture.replay())


def test_compat_builder_refuses_missing_commit_or_existing_out(tmp_path):
    from r1.c3 import sweep1_compat
    import subprocess
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    with pytest.raises(ValueError, match="not available"):
        sweep1_compat.rebuild_v2_table(index=tmp_path / "i", paper_root=tmp_path, classification=tmp_path / "c",
                                       out=tmp_path / "o")


def test_compat_builder_refuses_existing_output(tmp_path, monkeypatch):
    from r1.c3 import sweep1_compat
    out = tmp_path / "out"; out.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        sweep1_compat.rebuild_v2_table(index=tmp_path / "i", paper_root=tmp_path, classification=tmp_path / "c",
                                       out=out)
