"""RUNBOOK A.4: C3 sweep index -> ``dataset`` table (file-only). ENGINEERING_ONLY; AI-assisted (Claude).

The 19 Oct pilot sources ``dt4`` (memory none) and ``rerun2A`` (memory on) were
collected by the same collector the C3 sweep uses and have the sweep's layout
(``manifest.json``, ``roots/<instance>.json``, ``provenance/ledgers/roots``), so a
sweep index pointing at them is a fixture derived from the pilot table: the
adapter must reproduce ``dataset.build``'s rows and configs byte for byte, and
the rows of the 19 Oct split-recheck table (local, git-ignored) apart from the
``noop_kind`` field that was added on 22 Oct.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys

import pytest

from r1.c3 import dataset as D
from r1.harness import REPO

E1_12OCT = REPO / "results/r1/pilot/E1_20261012T145353Z/summary.json"  # build-time noise of the 19 Oct table
PILOT_19OCT = REPO / "results/r1/engineering/c3_split_recheck_20261019"
needs_pilot = pytest.mark.skipif(not all((REPO / D.SOURCES[s]["dir"]).exists() for s in ("dt4", "rerun2A")),
                                 reason="pilot ledgers not present")


def _pilot_index(source: str, mode: str) -> dict:
    d = D.SOURCES[source]["dir"]
    manifest = json.loads((REPO / d / "manifest.json").read_text())
    return {"schema": D.SWEEP_INDEX_SCHEMA, "label": "PILOT", "written_utc": "20261019T000000Z",
            "nodes": manifest["nodes"], "excluded_nodes": [], "instances": manifest["instances"],
            "runs": manifest["runs"], "harness_commit": manifest["harness"]["commit"],
            "sweeps": [{"memory_mode": mode, "arm_role": "fixture", "out": d, "manifest": f"{d}/manifest.json",
                        "ledgers": f"{d}/provenance/ledgers/roots", "commit": None}],
            "audit": {"status": "pending", "seeds": list(range(7001, 7011))}}


@needs_pilot
@pytest.mark.parametrize("source,mode", [("dt4", "none"), ("rerun2A", "append_only_summary")])
def test_sweep_adapter_reproduces_build_byte_for_byte(tmp_path, source, mode):
    index = tmp_path / "C3_sweep_index_fixture.json"
    index.write_text(json.dumps(_pilot_index(source, mode)))
    ref, new = tmp_path / "ref", tmp_path / "new"
    D.build(ref, (source,), e1_summary=E1_12OCT)
    meta = D.build_from_sweep(index, new, paper_root=REPO, e1_summary=E1_12OCT, source_names={mode: source})
    assert (new / "proposals.jsonl").read_bytes() == (ref / "proposals.jsonl").read_bytes()
    assert (new / "configs.json").read_bytes() == (ref / "configs.json").read_bytes()
    built = json.loads((ref / "build.json").read_text())
    assert meta["replay_checks"] == built["replay_checks"] and meta["noise"] == built["noise"]
    assert meta["n_proposals"] == built["n_proposals"] > 100
    assert meta["sweep_index"]["audit"]["seeds"] == list(range(7001, 7011))
    assert meta["sources"][source]["memory_mode"] == mode and meta["label"] == "PILOT"


@needs_pilot
@pytest.mark.skipif(not (PILOT_19OCT / "proposals.jsonl").exists(), reason="19 Oct pilot table is local only")
def test_sweep_adapter_matches_the_19oct_pilot_table(tmp_path):
    ref_rows = (PILOT_19OCT / "proposals.jsonl").read_text().splitlines()
    rebuilt = []
    for source, mode in (("dt4", "none"), ("rerun2A", "append_only_summary")):
        index = tmp_path / f"C3_sweep_index_{source}.json"
        index.write_text(json.dumps(_pilot_index(source, mode)))
        out = tmp_path / source
        D.build_from_sweep(index, out, paper_root=REPO, e1_summary=E1_12OCT, source_names={mode: source})
        rebuilt += (out / "proposals.jsonl").read_text().splitlines()
    ref = [r for r in ref_rows if json.loads(r)["source"] in ("dt4", "rerun2A")]
    assert len(rebuilt) == len(ref) > 1000
    stripped = [json.dumps({k: v for k, v in json.loads(r).items() if k != "noop_kind"}) for r in rebuilt]
    assert stripped == ref  # identical bytes apart from the 22 Oct ``noop_kind`` field
    ref_configs = json.loads((PILOT_19OCT / "configs.json").read_text())
    for source in ("dt4", "rerun2A"):
        configs = json.loads((tmp_path / source / "configs.json").read_text())
        assert all(ref_configs[h] == v for h, v in configs.items())


def _mini_sweep(root, *, nodes=("digits_mlp",), instances=1, mode="none", real=True, missing_ledger=False):
    """A one-root sweep tree under ``root`` (paper layout) copied from the dt4 pilot."""
    src = REPO / D.SOURCES["dt4"]["dir"]
    out_rel = f"results/r1/pilot/C3_sweep_{mode}_20261101T000000Z"
    out = root / out_rel
    (out / "roots").mkdir(parents=True)
    insts = sorted(p.name for p in (src / "provenance/ledgers/roots").iterdir() if p.name.startswith(nodes[0]))
    for inst in insts[:instances]:
        if missing_ledger:
            (out / "provenance/ledgers/roots").mkdir(parents=True, exist_ok=True)
        else:
            shutil.copytree(src / "provenance/ledgers/roots" / inst, out / "provenance/ledgers/roots" / inst)
        shutil.copy2(src / "roots" / f"{inst}.json", out / "roots" / f"{inst}.json")
    manifest = {"label": "DRYRUN", "memory_mode": mode, "runs": 20, "instances": instances, "nodes": list(nodes),
                "noise": {}}
    if real:
        manifest["c3_label_sweep"] = {"schema": "r1.c3_label_sweep/1", "memory_mode": mode}
    (out / "manifest.json").write_text(json.dumps(manifest))
    index = {"schema": D.SWEEP_INDEX_SCHEMA, "label": "DRYRUN", "written_utc": "20261101T010203Z",
             "nodes": list(nodes), "excluded_nodes": [], "instances": instances, "runs": 20,
             "sweeps": [{"memory_mode": mode, "out": out_rel, "manifest": f"{out_rel}/manifest.json",
                         "ledgers": f"{out_rel}/provenance/ledgers/roots"}], "audit": {"status": "pending"}}
    path = root / "results/r1/pilot/C3_sweep_index_20261101T010203Z.json"
    path.write_text(json.dumps(index))
    return path, out


@needs_pilot
def test_sweep_adapter_paths_names_and_batch_directory(tmp_path):
    paper = tmp_path / "batch" / "agent_paper_B"
    index, _ = _mini_sweep(paper)
    meta = D.build_from_sweep(index, tmp_path / "t1", e1_summary=E1_12OCT)  # paper root inferred from the path
    assert list(meta["sources"]) == ["c3_20261101T010203Z_none"]
    rows = D.load_table(tmp_path / "t1")
    assert rows and all(r["proposal_id"].startswith("c3_20261101T010203Z_none:digits_mlp__s") for r in rows)
    batch = tmp_path / "batch"
    (batch / "batch_state.json").write_text(json.dumps({"steps": {"index": {"completed": True,
                                                                             "path": "/elsewhere/" + index.name}}}))
    done = subprocess.run([sys.executable, "-m", "r1.c3.dataset", "build-sweep", "--index", str(batch),
                           "--out", str(tmp_path / "t2"), "--e1-summary", str(E1_12OCT)],
                          cwd=REPO, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr[-2000:]
    assert (tmp_path / "t2/proposals.jsonl").read_bytes() == (tmp_path / "t1/proposals.jsonl").read_bytes()
    (batch / "batch_state.json").write_text(json.dumps({"steps": {"index": {"completed": False}}}))
    with pytest.raises(ValueError, match="not completed"):
        D.build_from_sweep(batch, tmp_path / "t3", e1_summary=E1_12OCT)


@needs_pilot
@pytest.mark.parametrize("breakage", ["failure_record", "mode", "missing_ledger", "index_nodes", "schema", "name"])
def test_sweep_adapter_refuses_inconsistent_sweeps(tmp_path, breakage):
    index_path, out = _mini_sweep(tmp_path, missing_ledger=(breakage == "missing_ledger"))
    index = json.loads(index_path.read_text())
    names = None
    if breakage == "failure_record":
        (out / "failures").mkdir()
        (out / "failures/root__digits_mlp__s104.json").write_text("{}")
    elif breakage == "mode":
        index["sweeps"][0]["memory_mode"] = "append_only_summary"
    elif breakage == "missing_ledger":
        assert not any((out / "provenance/ledgers/roots").iterdir())
    elif breakage == "index_nodes":
        index["nodes"] = ["digits_mlp", "tabular_mlp"]
    elif breakage == "schema":
        index["schema"] = "r1.c3_sweep_index/0"
    elif breakage == "name":
        names = {"none": "bad:name"}
    index_path.write_text(json.dumps(index))
    match = "0 root ledgers, expected 1" if breakage == "missing_ledger" else None
    with pytest.raises(ValueError, match=match):
        D.build_from_sweep(index_path, tmp_path / "t", e1_summary=E1_12OCT, source_names=names)
