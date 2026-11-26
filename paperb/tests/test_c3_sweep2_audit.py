"""The sweep-2 batch (``r1.c3.sweep2_batch``), the sweep-2 audit profile of ``r1.c3.audit`` and the sweep-2 integrity
check: synthetic sealed chunks only (one node, two instances, both memory modes); no label, audit or evaluation file
of a real sweep is opened. AI-assisted (Claude)."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from r1.c3 import audit, dataset as D, features as F, release_checks, sweep2_batch as SB
from r1.harness import REPO

NODE = "digits_mlp"
SEEDS = (104, 114)
START = {"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"}
VALUES = {"HIDDEN_UNITS": ["16", "32", "64", "128"], "ALPHA": ["1e-5", "1e-4", "1e-3", "1e-2"],
          "MAX_ITER": ["20", "40", "80", "160"]}


@pytest.fixture(autouse=True)
def _control_plane_skip(monkeypatch):
    try:
        F._is_control_plane_skip({"decision": "kept", "extra": {}})
    except ImportError:
        def stand_in(row):
            c = (row.get("extra") or {}).get("control") or {}
            return row.get("decision") == "skipped" and c.get("action") == "skip" and c.get("reason") != "inactive_key"
        monkeypatch.setattr(F, "_is_control_plane_skip", stand_in)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _metric(cfg: dict) -> float:
    h = int(hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8], 16)
    return round(0.85 + (h % 1000) / 10000.0, 4)


def _ledger(inst: str, n: int = 10) -> list[dict]:
    rng = np.random.default_rng(int(inst.rsplit("__s", 1)[1]))
    inc = {"HIDDEN_UNITS": "32", "ALPHA": "1e-4", "MAX_ITER": "40"}
    best, rows = None, []
    for b in range(1, n + 1):
        key = list(VALUES)[int(rng.integers(3))]
        new = inc[key] if b == 4 else str(rng.choice([v for v in VALUES[key] if v != inc[key]]))
        cand = {**inc, key: new}
        m = _metric(cand)
        kept = best is None or m > best
        rows.append({"budget_index": b, "decision": "kept" if kept else "discarded",
                     "parsed_metrics": {"val_score": m}, "current_best_before": best,
                     "delta_vs_best": None if best is None else m - best,
                     "extra": {"manager": {"structured_edit": {"symbol": key, "old": inc[key], "new": new,
                                                               "path": "train.py"}}}})
        if kept:
            inc, best = cand, m
    return rows


@pytest.fixture()
def world(tmp_path, monkeypatch):
    """A paper root (pinned noise summary and sweep-2 authorization copied from the repository) and a synthetic
    sealed run directory in the sweep-2 seal layout."""
    monkeypatch.setattr(SB, "NODES", [NODE])
    monkeypatch.setattr(SB, "INSTANCES", len(SEEDS))
    paper = tmp_path / "paper"
    for rel in (SB.NOISE_SOURCE["path"], SB.AUTHORIZATION["path"]):
        (paper / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, paper / rel)
    sealed = tmp_path / "sealed" / SB.RUN_ID
    monkeypatch.setattr(SB, "SEALED_RUN_DIR", str(sealed))
    from r1.headroom.e1b_collect import node_noise
    noise = node_noise(paper / SB.NOISE_SOURCE["path"], NODE)
    records = {}
    for k, (chunk, node, mode) in enumerate(SB.chunks()):
        c = sealed / chunk
        files = {"job_record.json": json.dumps({
            "schema": "s2_c2_job_record/1", "run_id": SB.RUN_ID, "chunk_id": chunk, "label": "EVIDENCE",
            "paper_commit": SB.PAPER_COMMIT, "image_digest": SB.IMAGE, "harness_commit": SB.HARNESS_COMMIT,
            "b2_audits": "none (no B.2 audits; audit seeds 7001-7010 untouched)",
            "finished_utc": f"2026-11-21T0{k}:00:00Z", "cpu": {"model": "X"}, "site": {"fqdn": "g4401"}})}
        manifest = {"schema": "r1.e1b_headroom/1", "label": "EVIDENCE", "split": "c3_labels",
                    "started_utc": f"2026112{k}", "harness": {"root": f"/srv/{chunk}/harness", "commit": SB.HARNESS_COMMIT, "dirty": False},
                    "manager_backend": "llamacpp", "manager": {"kind": "langgraph", "proposal_schema": "manager_proposal/v1"},
                    "memory_mode": mode, "arm": None, "arm_role": SB.MODES[mode], "seed_policy": "d26",
                    "nodes": [node], "instances": len(SEEDS), "runs": 20, "points": 0, "reps": 0, "audit_seeds": 0,
                    "verify_r": 3, "verify_split_policy": "vary",
                    "noise": {node: {**noise, "source": f"/srv/{chunk}/paper/{SB.NOISE_SOURCE['path']}"}},
                    "host": {"platform": chunk}, "work": f"/srv/{chunk}/work", "sessions": [{"chunk": chunk}],
                    "roots_only": True, "root_failures": "record",
                    "c3_label_sweep": {"schema": "r1.c3_label_sweep/1", "memory_mode": mode,
                                       "arm_role": SB.MODES[mode], "label": "EVIDENCE", "s2_c2": True,
                                       "backend": "llamacpp", "noise_source": dict(SB.NOISE_SOURCE),
                                       "audit": "none", "b2_audits": "none"}}
        files["out/manifest.json"] = json.dumps(manifest)
        for s in SEEDS:
            inst = f"{node}__s{s}"
            files[f"out/roots/{inst}.json"] = json.dumps({"start_files": START})
            files[f"work/roots/{inst}/root_trials.jsonl"] = "".join(json.dumps(r) + "\n" for r in _ledger(inst))
            files[f"work/roots/{inst}/root_events.jsonl"] = "{}\n"
        for rel, text in files.items():
            (c / rel).parent.mkdir(parents=True, exist_ok=True)
            (c / rel).write_text(text)
        (c / "SHA256SUMS").write_text("".join(f"{_sha((c / rel).read_bytes())}  {rel}\n" for rel in sorted(files)))
        (c / "SEAL_RECEIPT.json").write_text(json.dumps({"chunk_id": chunk}))
        records[chunk] = _sha((c / "job_record.json").read_bytes())
    counts = {"run_id": SB.RUN_ID, "paper_commit": SB.PAPER_COMMIT, "chunks": len(SB.chunks()),
              "chunk_record_sha256": records, "admitted_diagnosed_records": []}
    _write_counts(paper, sealed, counts, monkeypatch)
    return {"paper": paper, "sealed": sealed, "tmp": tmp_path}


def _write_counts(paper: Path, sealed: Path, counts: dict, monkeypatch) -> None:
    """The sealed collection counts and their published copy on main (byte-identical, as for the real run)."""
    data = json.dumps(counts).encode()
    (sealed / "collection_counts.json").write_bytes(data)
    (paper / SB.COLLECTION_COUNTS_PUBLISHED).parent.mkdir(parents=True, exist_ok=True)
    (paper / SB.COLLECTION_COUNTS_PUBLISHED).write_bytes(data)
    monkeypatch.setattr(SB, "COLLECTION_COUNTS_SHA256", _sha(data))


def _reseal(chunk_dir: Path) -> None:
    rels = [line.split("  ", 1)[1] for line in (chunk_dir / "SHA256SUMS").read_text().splitlines() if line.strip()]
    (chunk_dir / "SHA256SUMS").write_text("".join(f"{_sha((chunk_dir / r).read_bytes())}  {r}\n" for r in rels))


def test_extract_verify_build_and_plan(world):
    out = SB.extract(world["sealed"], world["paper"])
    index = Path(out["index"])
    assert index.parent == SB.batch_dir(world["paper"]) and index.name == SB.index_name()
    v = SB.verify(index, world["paper"])
    assert v["index_sha256"] == out["index_sha256"] and v["files"] == out["files"]
    data = json.loads(index.read_text())
    assert data["label"] == "EVIDENCE" and data["nodes"] == [NODE] and data["sweep2"]["run_id"] == SB.RUN_ID
    assert [s["memory_mode"] for s in data["sweeps"]] == list(SB.MODES)
    m = json.loads((SB.batch_dir(world["paper"]) / "sweeps/none/manifest.json").read_text())
    assert m["noise"][NODE]["source"] == SB.NOISE_SOURCE["path"] and m["noise"][NODE]["source_at_collection"]
    # the existing table builder reads the batch through the index (no classification sidecar)
    table = world["tmp"] / "table"
    meta = D.build_from_sweep(index, table, paper_root=world["paper"])
    assert meta["label"] == "EVIDENCE" and "classification" not in meta and meta["table_sha256"]
    assert meta["replay_checks_total"]["zero_delta_violations"] == 0
    c = SB.counts(table)
    assert c["proposals"] == meta["n_proposals"] == c["eligible"] + c["duplicates"] + c["noops"]
    assert c["noops"] == 2 * len(SEEDS) and c["seed_runs"] == 10 * c["unique_configs"]
    # the audit's sweep-2 plan: batch re-verified, table equal to a full replay, same partition as sweep 1
    plan, binding = audit.evidence_plan(table, world["paper"], index, None, "sweep2")
    assert binding["source"] == "sweep2" and binding["extract_sha256"] == v["extract_sha256"]
    assert binding["counts"] == {"noops": c["noops"], "duplicates": c["duplicates"], "eligible": c["eligible"]}
    assert len(plan) == c["eligible"] and "classification_sha256" not in binding
    with pytest.raises(ValueError, match="no classification sidecar"):
        audit.evidence_plan(table, world["paper"], index, index, "sweep2")
    # a table not built from this index, or altered, is refused
    meta2 = json.loads((table / "build.json").read_text())
    meta2["sweep_index"]["sha256"] = "0" * 64
    (table / "build.json").write_text(json.dumps(meta2))
    with pytest.raises(ValueError, match="not the sweep-2 EVIDENCE table"):
        audit.evidence_plan(table, world["paper"], index, None, "sweep2")


@pytest.mark.parametrize("case,match", [
    ("ledger_byte", "differs from its sealed SHA256SUMS"),
    ("record_not_counted", "not the one the collection counted"),
    ("record_pins", "job record pins differ"),
    ("audit_seeds", "collector manifest fails"),
    ("noise_value", "noise constants differ"),
    ("root_failure", "root failures"),
    ("missing_campaign", "root ledgers"),
    ("unlisted", "not in its SHA256SUMS"),
    ("counts_file", "not the published, pinned file"),
    ("sealed_copy", "is not the sealed run directory"),
    ("unadmitted_stop", "did not admit"),
    ("suffixed_ledger", "rotated or suffixed root ledgers"),
    ("dirty_harness", "not the clean sweep-2 pin"),
    ("manager", "do not share one manager declaration"),
])
def test_extract_refusals(world, monkeypatch, case, match):
    sealed = world["sealed"]
    chunk = sealed / f"{NODE}-none"
    if case == "ledger_byte":
        p = chunk / f"work/roots/{NODE}__s104/root_trials.jsonl"
        p.write_text(p.read_text().replace('"kept"', '"Kept"', 1))
    elif case in ("record_not_counted", "record_pins"):
        rec = json.loads((chunk / "job_record.json").read_text())
        rec["paper_commit" if case == "record_pins" else "started_utc"] = "x"
        (chunk / "job_record.json").write_text(json.dumps(rec))
        _reseal(chunk)
        if case == "record_pins":      # recount it, so that only the pin check refuses
            counts = json.loads((sealed / "collection_counts.json").read_text())
            counts["chunk_record_sha256"][chunk.name] = _sha((chunk / "job_record.json").read_bytes())
            _write_counts(world["paper"], sealed, counts, monkeypatch)
    elif case in ("audit_seeds", "noise_value"):
        m = json.loads((chunk / "out/manifest.json").read_text())
        if case == "audit_seeds":
            m["audit_seeds"] = 10
        else:
            m["noise"][NODE]["sigma_t"] = 9.0
        (chunk / "out/manifest.json").write_text(json.dumps(m))
        _reseal(chunk)
    elif case == "root_failure":
        (chunk / "out/failures").mkdir()
        (chunk / "out/failures/x.json").write_text("{}")
    elif case == "missing_campaign":
        lines = [x for x in (chunk / "SHA256SUMS").read_text().splitlines() if "__s114" not in x]
        (chunk / "SHA256SUMS").write_text("\n".join(lines) + "\n")
        for p in (chunk / f"work/roots/{NODE}__s114").iterdir():
            p.rename(world["tmp"] / f"moved_{p.name}")
        (chunk / f"work/roots/{NODE}__s114").rmdir()
        (chunk / f"out/roots/{NODE}__s114.json").rename(world["tmp"] / "moved_root.json")
    elif case == "unlisted":
        lines = [x for x in (chunk / "SHA256SUMS").read_text().splitlines() if "out/roots" not in x]
        (chunk / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    elif case == "counts_file":
        monkeypatch.setattr(SB, "COLLECTION_COUNTS_SHA256", "0" * 64)
    elif case == "sealed_copy":
        monkeypatch.setattr(SB, "SEALED_RUN_DIR", "/ceph/srv/dwong/paperb/sweep2/" + SB.RUN_ID)
    elif case == "unadmitted_stop":
        _stop(world, monkeypatch, chunk, admit=False)
    elif case == "suffixed_ledger":
        (chunk / f"work/roots/{NODE}__s104/root_trials.jsonl.1").write_text("{}\n")
        lines = (chunk / "SHA256SUMS").read_text() + f"{_sha(b'{}' + bytes([10]))}  work/roots/{NODE}__s104/root_trials.jsonl.1\n"
        (chunk / "SHA256SUMS").write_text(lines)
    elif case in ("dirty_harness", "manager"):
        m = json.loads((chunk / "out/manifest.json").read_text())
        if case == "dirty_harness":
            m["harness"]["dirty"] = True
        else:
            m["manager"] = {**m["manager"], "proposal_schema": "manager_proposal/v2"}
        (chunk / "out/manifest.json").write_text(json.dumps(m))
        _reseal(chunk)
    with pytest.raises(SB.BatchError, match=match):
        SB.extract(sealed, world["paper"])
    assert not SB.batch_dir(world["paper"]).exists()


def _stop(world, monkeypatch, chunk: Path, admit: bool) -> None:
    """Give a chunk's job record a stop (as the R1-SWEEP2-RTE-DIAG chunks have), recounted, admitted or not."""
    rec = json.loads((chunk / "job_record.json").read_text())
    rec["stop"] = {"reason": "worker_failure"}
    (chunk / "job_record.json").write_text(json.dumps(rec))
    _reseal(chunk)
    counts = json.loads((world["sealed"] / "collection_counts.json").read_text())
    sha = _sha((chunk / "job_record.json").read_bytes())
    counts["chunk_record_sha256"][chunk.name] = sha
    if admit:
        counts["admitted_diagnosed_records"] = [{"chunk": chunk.name, "campaign_id": f"{NODE}__s104",
                                                 "trial_id": "t", "exception": "ParserError", "budget_index": 3,
                                                 "sealed_record_sha256": sha}]
    _write_counts(world["paper"], world["sealed"], counts, monkeypatch)


def test_admitted_stopped_chunk_extracts_and_verifies(world, monkeypatch):
    chunk = world["sealed"] / f"{NODE}-append_only_summary"
    _stop(world, monkeypatch, chunk, admit=True)
    out = SB.extract(world["sealed"], world["paper"])
    ex = json.loads((SB.batch_dir(world["paper"]) / "EXTRACT.json").read_text())
    assert ex["chunks"][chunk.name]["stop"] == {"reason": "worker_failure"}
    assert ex["sealed_run_dir"] == SB.SEALED_RUN_DIR          # a constant, not the path as typed
    assert SB.verify(Path(out["index"]), world["paper"])["index_sha256"] == out["index_sha256"]
    # an admitted record whose sha256 is not the chunk's sealed record, or a stop nobody admitted, is refused
    counts = json.loads((world["sealed"] / "collection_counts.json").read_text())
    SB._check_admitted(ex["chunks"], counts)
    bad = json.loads(json.dumps(counts))
    bad["admitted_diagnosed_records"][0]["sealed_record_sha256"] = "0" * 64
    with pytest.raises(SB.BatchError, match="admitted record sha256"):
        SB._check_admitted(ex["chunks"], bad)
    with pytest.raises(SB.BatchError, match="stopped chunks not admitted"):
        SB._check_admitted(ex["chunks"], {**counts, "admitted_diagnosed_records": []})


def test_mode_manifest_needs_equal_chunks(world, monkeypatch):
    """The eight chunk manifests of a mode must agree on every common field; the nodes and noise are merged."""
    monkeypatch.setattr(SB, "NODES", [NODE, "tabular_mlp"])
    from r1.headroom.e1b_collect import node_noise
    pinned = world["paper"] / SB.NOISE_SOURCE["path"]
    base = json.loads((world["sealed"] / f"{NODE}-none/out/manifest.json").read_text())
    other = json.loads(json.dumps(base))
    other["nodes"] = ["tabular_mlp"]
    other["noise"] = {"tabular_mlp": {**node_noise(pinned, "tabular_mlp"), "source": "/x/" + SB.NOISE_SOURCE["path"]}}
    merged = SB.mode_manifest({f"{NODE}-none": base, "tabular_mlp-none": other}, "none", pinned)
    assert merged["nodes"] == [NODE, "tabular_mlp"] and set(merged["noise"]) == {NODE, "tabular_mlp"}
    for key, value in (("verify_split_policy", "fixed"), ("action_versions", {"verify_split": "fixed"})):
        changed = {**other, key: value}
        with pytest.raises(SB.BatchError, match=rf"differs from the other chunks in \['{key}'\]"):
            SB.mode_manifest({f"{NODE}-none": base, "tabular_mlp-none": changed}, "none", pinned)
    with pytest.raises(SB.BatchError, match="chunk manifests"):
        SB.mode_manifest({f"{NODE}-none": base}, "none", pinned)


def test_extract_never_overwrites_and_verify_catches_tampering(world):
    SB.extract(world["sealed"], world["paper"])
    with pytest.raises(SB.BatchError, match="written once"):
        SB.extract(world["sealed"], world["paper"])
    batch = SB.batch_dir(world["paper"])
    index = batch / SB.index_name()
    ledger = batch / f"sweeps/none/ledgers/{NODE}__s104/root_trials.jsonl"
    original = ledger.read_bytes()
    ledger.write_bytes(original.replace(b'"kept"', b'"Kept"', 1))
    with pytest.raises(SB.BatchError, match="differs from EXTRACT.json"):
        SB.verify(index, world["paper"])
    ledger.write_bytes(original)
    (batch / "sweeps/none/ledgers/extra.txt").write_text("x")
    with pytest.raises(SB.BatchError, match="batch files differ from EXTRACT.json"):
        SB.verify(index, world["paper"])
    (batch / "sweeps/none/ledgers/extra.txt").rename(world["tmp"] / "extra.txt")
    # a mode manifest edited together with its EXTRACT entry and the index binding is still caught (re-derived)
    mpath = batch / "sweeps/none/manifest.json"
    m = json.loads(mpath.read_text())
    m["runs"] = 21
    mpath.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    ex = json.loads((batch / "EXTRACT.json").read_text())
    ex["files"]["sweeps/none/manifest.json"]["sha256"] = _sha(mpath.read_bytes())
    (batch / "EXTRACT.json").write_text(json.dumps(ex, indent=1, sort_keys=True) + "\n")
    idx = json.loads(index.read_text())
    idx["sweep2"]["extract"]["sha256"] = _sha((batch / "EXTRACT.json").read_bytes())
    index.write_text(json.dumps(idx, indent=1, sort_keys=True) + "\n")
    with pytest.raises(SB.BatchError, match="not the derived mode manifest"):
        SB.verify(index, world["paper"])
    with pytest.raises(SB.BatchError, match="not the sweep-2 index"):
        SB.verify(world["tmp"] / "elsewhere.json", world["paper"])


def test_verify_is_internal_consistency_only_and_verify_sealed_binds_the_seal(world):
    """Pins the M1 boundary: a ledger edited together with EXTRACT.json and the index passes ``verify`` (internal
    consistency only); ``verify --sealed`` (and the addendum pins, below) catch it."""
    out = SB.extract(world["sealed"], world["paper"])
    batch, index = SB.batch_dir(world["paper"]), Path(out["index"])
    assert SB.verify_sealed(index, world["paper"], world["sealed"])["sealed_rederivation"] == "equal"
    planted = batch / "sweeps/none/EXTRACT.json"
    planted.write_text("{}")
    with pytest.raises(SB.BatchError, match="batch files differ from EXTRACT.json"):
        SB.verify(index, world["paper"])
    planted.rename(world["tmp"] / "planted.json")
    rel = f"sweeps/none/ledgers/{NODE}__s104/root_trials.jsonl"
    (batch / rel).write_bytes((batch / rel).read_bytes().replace(b'"kept"', b'"Kept"', 1))
    ex = json.loads((batch / "EXTRACT.json").read_text())
    ex["files"][rel]["sha256"] = _sha((batch / rel).read_bytes())
    ex_bytes = (json.dumps(ex, indent=1, sort_keys=True) + "\n").encode()
    (batch / "EXTRACT.json").write_bytes(ex_bytes)
    manifests = {m: (batch / f"sweeps/{m}/manifest.json").read_bytes() for m in SB.MODES}
    index.write_bytes((json.dumps(SB.build_index(manifests, ex_bytes, ex, world["paper"]), indent=1,
                                  sort_keys=True) + "\n").encode())
    forged = SB.verify(index, world["paper"])                    # passes: verify alone cannot see this
    assert forged["index_sha256"] != out["index_sha256"]           # but the index sha256 the addendum pins moved
    with pytest.raises(SB.BatchError, match="sealed re-derivation"):
        SB.verify_sealed(index, world["paper"], world["sealed"])


def test_sweep2_pins_must_match_the_addendum(tmp_path):
    table = tmp_path / "table"
    table.mkdir()
    (table / "proposals.jsonl").write_text("{}\n")
    (table / "configs.json").write_text("{}")
    index = tmp_path / "index.json"
    index.write_text("i")
    pins = {"sweep2_index_sha256": _sha(b"i"), "sweep2_extract_sha256": "e" * 64,
            "table_proposals_sha256": _sha(b"{}\n"), "table_configs_sha256": _sha(b"{}")}
    audit._sweep2_pins_match({"pins": pins}, {"extract_sha256": "e" * 64}, index, table)
    for key in pins:
        with pytest.raises(ValueError, match=f"STOP: .*{key}"):
            audit._sweep2_pins_match({"pins": {**pins, key: "0" * 64}}, {"extract_sha256": "e" * 64}, index, table)


def test_sweep2_addendum_and_start_row(monkeypatch, tmp_path):
    commit = "c" * 40
    pins = "".join(f"{k}: {c * 64}\n" for k, c in zip(audit.SWEEP2_PIN_KEYS, "abcd"))
    good = (f"# Addendum\nR1-SWEEP2-B2-GO; run {SB.RUN_ID}; code {commit}; harness {audit.AUDIT_HARNESS}; K = 10\n"
            f"approved: true\nlabel: EVIDENCE\nsweep2_run_id: {SB.RUN_ID}\nstart_ruling: R1-SWEEP2-B2-GO\n{pins}"
            "precondition2_review: docs/r1/reviews/S2_P2_REVIEW.md\n")
    p2 = ("".join(f"{c * 64}\n" for c in "abcd") + "Verdict: ACCEPTED\n").encode()
    row = ("## 10. Decisions\n\n### Author decisions, 22 November 2026\n\n| ID | Author decision |\n|---|---|\n"
           f"| R1-SWEEP2-B2-GO | sweep-2 B.2 {SB.RUN_ID}: amends R1-SWEEP-HOST-HTC; lifts R1-B2-DECOUPLE; "
           "B6 (a), B4 (a), B1 (a) as for sweep 1 |\n")
    published = {"docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md": good.encode(),
                 "docs/r1/PLAN.md": row.encode(), "docs/r1/reviews/S2_P2_REVIEW.md": p2}
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: published[rel])
    rel = Path("docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md")
    out = audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    assert out == {"path": str(rel), "sha256": _sha(good.encode()),
                   "pins": {k: c * 64 for k, c in zip(audit.SWEEP2_PIN_KEYS, "abcd")},
                   "precondition2_review": {"path": "docs/r1/reviews/S2_P2_REVIEW.md", "sha256": _sha(p2)}}
    for review, match in ((p2.replace(b"Verdict: ACCEPTED", b"Verdict: NOT ACCEPTED"), "precondition-2 review"),
                          (p2.replace(b"d" * 64, b"e" * 64), "precondition-2 review")):
        published["docs/r1/reviews/S2_P2_REVIEW.md"] = review
        with pytest.raises(ValueError, match=match):
            audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    published["docs/r1/reviews/S2_P2_REVIEW.md"] = p2
    published[str(rel)] = good.replace("docs/r1/reviews/S2_P2_REVIEW.md", "elsewhere/x.md").encode()
    with pytest.raises(ValueError, match="precondition2_review"):
        audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    published[str(rel)] = good.encode()
    with pytest.raises(ValueError, match="c3_sweep2_b2_addendum_"):
        audit.b2_addendum(tmp_path, Path("docs/r1/authorizations/c3_b2_addendum_20261122.md"), commit, "sweep2")
    with pytest.raises(ValueError, match="c3_b2_addendum_"):        # and the sweep-1 profile refuses a sweep-2 file
        audit.b2_addendum(tmp_path, rel, commit, "sweep1")
    for text, match in ((good.replace(SB.RUN_ID, "s2ev-x"), "sweep2_run_id"),
                        (good.replace("R1-SWEEP2-B2-GO", "R1-B2-GO"), "R1-SWEEP2-B2-GO"),
                        (good.replace("K = 10", "K = 6"), "K = 10"),
                        (good.replace("approved: true", "approved: false"), "approved: true"),
                        (good.replace("label: EVIDENCE", "label: ENGINEERING"), "label: EVIDENCE"),
                        (good + "approved: true\n", "duplicate addendum field"),
                        (good.replace("a" * 64, "a" * 12), "must pin")):
        published[str(rel)] = text.encode()
        with pytest.raises(ValueError, match=match):
            audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    published[str(rel)] = good.encode()
    for bad_plan in (row.replace("B4 (a), ", ""), row.replace("amends R1-SWEEP-HOST-HTC; ", ""),
                     row + row.splitlines()[-1] + "\n",                       # the row twice
                     "```\n" + row + "```\n"):                              # only in a fenced block
        published["docs/r1/PLAN.md"] = bad_plan.encode()
        with pytest.raises(ValueError, match="start row"):
            audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    published["docs/r1/PLAN.md"] = row.encode()
    with pytest.raises(ValueError, match="unknown audit source"):
        audit.b2_addendum(tmp_path, rel, commit, "sweep3")


def _git(repo, *args):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "PATH": "/usr/bin:/bin"}
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def test_harness_equivalence(monkeypatch, tmp_path):
    h = tmp_path / "harness"
    h.mkdir()
    _git(h, "init", "-q")
    for rel in ("nodes/digits_mlp/train.py", "src/autoresearch/worker/w.py", "src/autoresearch/llm/x.py"):
        (h / rel).parent.mkdir(parents=True, exist_ok=True)
        (h / rel).write_text("a\n")
    _git(h, "add", "-A")
    _git(h, "commit", "-q", "-m", "audit pin")
    a = _git(h, "rev-parse", "HEAD")
    (h / "src/autoresearch/llm/x.py").write_text("b\n")            # outside the audited paths: allowed
    _git(h, "commit", "-q", "-am", "sweep-2 pin")
    b = _git(h, "rev-parse", "HEAD")
    monkeypatch.setattr(audit, "AUDIT_HARNESS", a)
    monkeypatch.setattr(SB, "HARNESS_COMMIT", b)
    out = audit.sweep2_harness_equivalence(h)
    assert out["diff"] == "empty" and out["sweep2_harness"] == b
    (h / "src/autoresearch/worker/w.py").write_text("c\n")
    _git(h, "commit", "-q", "-am", "worker change")
    monkeypatch.setattr(SB, "HARNESS_COMMIT", _git(h, "rev-parse", "HEAD"))
    with pytest.raises(ValueError, match="differs from"):
        audit.sweep2_harness_equivalence(h)
    monkeypatch.setattr(SB, "HARNESS_COMMIT", "f" * 40)
    with pytest.raises(ValueError, match="NOT CHECKABLE"):
        audit.sweep2_harness_equivalence(h)


def _completion_world(tmp_path, monkeypatch, source):
    """The synthetic evidence-run fixture of test_c3_evidence_split_blocks, for either profile."""
    monkeypatch.setattr(audit, "b2_addendum", lambda *a: {"path": "docs/r1/authorizations/x.md", "sha256": "addendum"})
    monkeypatch.setattr(audit, "sweep2_harness_equivalence",
                        lambda h: {"diff": "empty", "paths": list(audit.SWEEP2_EQUAL_PATHS)})
    monkeypatch.setattr(audit, "_sweep2_pins_match", lambda *a: None)
    table = tmp_path / "table"
    table.mkdir(parents=True)
    for name, data in [("build.json", "{}"), ("proposals.jsonl", "{}\n"),
                       ("configs.json", json.dumps({"c": {"files": {}}, "i": {"files": {}}}))]:
        (table / name).write_text(data)
    for rel in ("docs/r1/authorizations/c3_sweep1_20261027.md", SB.AUTHORIZATION["path"]):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(rel)
    index, classification = tmp_path / "index", tmp_path / "classification"
    index.write_text("index")
    classification.write_text("classification")
    rows = [{"proposal_id": "p", "node": "n", "noop": False, "duplicate": False, "sigma_node": 0.5}]
    monkeypatch.setattr(D, "load_table", lambda _: rows)
    plan = [{"proposal_id": "p", "node": "n", "candidate_hash": "c", "incumbent_hash": "i"}]
    env = {"worker_python": "/venv/bin/python3", "worker_prefix": "/venv",
           "worker_versions": {"scikit-learn": "1.8.0", "numpy": "2.4.4", "pandas": "3.0.3", "scipy": "1.17.1"},
           "package_list_sha256": "abc", "harness_root": "/h", "environment_basis": {},
           "harness_untracked": {"data_caches_sha256": {"n": "d"}}}
    monkeypatch.setattr(audit, "evidence_environment", lambda *a: dict(env))
    monkeypatch.setattr(audit, "harness_untracked_state", lambda *a: {"data_caches_sha256": {"n": "d"}})
    monkeypatch.setattr(audit, "evidence_paper_provenance", lambda *a: {})
    binding = {"counts": {"eligible": 1, "noops": 0, "duplicates": 0}}
    if source == "sweep2":
        binding.update(source="sweep2", extract_sha256="e" * 64)
    monkeypatch.setattr(audit, "evidence_plan", lambda *a: (plan, binding))
    monkeypatch.setattr(audit, "evidence_resources", lambda *a: {})
    monkeypatch.setattr(audit, "monitor_evidence_resources", lambda *a: {})

    class Future:
        def __init__(self, key): self.key = key
        def result(self):
            runtime = {"worker_python": env["worker_python"], "prefix": env["worker_prefix"], "base_prefix": "/s",
                       "versions": env["worker_versions"], "package_list_sha256": env["package_list_sha256"],
                       "worker_command_python": "/w/python3", "worker_python_realpath": "/s/python3"}
            return [{"seed": s, "success": True, "changed_files": False, "metric": float(s) + (self.key == "c"),
                     "wall_seconds": 1.0, "worker_runtime": runtime} for s in audit.DEFAULT_SEEDS]

    class Pool:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def submit(self, fn, node, files, seeds, scratch, stop, journal, identity): return Future(identity["config_hash"])
    monkeypatch.setattr(audit, "ProcessPoolExecutor", Pool)
    monkeypatch.setattr(audit, "wait", lambda pending, **kw: ({pending[0]}, set(pending[1:])))
    out = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_fake"
    audit.evidence_run(table, tmp_path, index, None if source == "sweep2" else classification, out, 1, 300,
                       scratch_root=tmp_path / "scratch", source=source)
    shutil.rmtree(tmp_path / "scratch")         # local fixture scratch only
    return json.loads((out / "evidence_completion.json").read_text()), out


SWEEP1_KEYS = ["schema", "label", "authorization_sha256", "b2_addendum_sha256", "classification_sha256",
               "index_sha256", "build_sha256", "proposals_sha256", "configs_sha256", "plan_sha256",
               "label_block_sha256", "evaluation_block_sha256", "runs_sha256", "environment_sha256",
               "per_run_worker_runtime", "worker_runtime_basis", "environment_basis", "resources_sha256", "counts",
               "label_seeds", "evaluation_seeds"]


def test_completion_records_by_profile(tmp_path, monkeypatch):
    c1, _ = _completion_world(tmp_path / "s1", monkeypatch, "sweep1")
    assert list(c1) == SWEEP1_KEYS and c1["schema"] == "r1.c3_audit_completion/3"     # sweep 1 unchanged
    assert c1["authorization_sha256"] == _sha(b"docs/r1/authorizations/c3_sweep1_20261027.md")
    c2, out2 = _completion_world(tmp_path / "s2", monkeypatch, "sweep2")
    assert c2["schema"] == audit.SWEEP2_COMPLETION_SCHEMA and c2["source"] == "sweep2"
    assert c2["extract_sha256"] == "e" * 64 and "classification_sha256" not in c2
    assert c2["authorization_sha256"] == _sha(SB.AUTHORIZATION["path"].encode())
    assert list(c2) == [k for k in SWEEP1_KEYS if k != "classification_sha256"][:4] + ["source", "extract_sha256"] + \
        SWEEP1_KEYS[5:]
    env = json.loads((out2 / "environment.json").read_text())
    assert env["source"] == "sweep2" and env["sweep2_harness_equivalence"]["diff"] == "empty"
    from r1.c3 import release
    assert release.evidence_tier(out2) == "T0"            # the run log stays locked as T0


def test_sweep2_integrity_is_registered_and_wraps_the_verifier(monkeypatch, tmp_path):
    assert release_checks.INTEGRITY_CHECKS["sweep2"] is release_checks.sweep2_integrity
    assert release_checks.INTEGRITY_CHECKS["sweep1"] is release_checks.sweep1_integrity
    seen = {}

    def verify(table, block, paper_root, index, classification, source="sweep1"):
        seen.update(table=table, block=block, classification=classification, source=source)
        return {"schema": audit.SWEEP2_COMPLETION_SCHEMA, "source": "sweep2", "label_block_sha256": "l",
                "extract_sha256": "e", "index_sha256": "i", "counts": {}, "secret": "never copied"}
    monkeypatch.setattr(audit, "verify_evidence_completion", verify)
    monkeypatch.setattr(release_checks, "_sweep2_batch_published", lambda: None)
    (tmp_path / "evidence_completion.json").write_text("{}")
    out = release_checks.sweep2_integrity(tmp_path, tmp_path, paper_root=tmp_path, index=tmp_path / "i.json")
    assert seen == {"table": tmp_path, "block": tmp_path / "label_block.jsonl", "classification": None,
                    "source": "sweep2"}
    assert out["pass"] and out["completion"] == {"schema": audit.SWEEP2_COMPLETION_SCHEMA, "source": "sweep2",
                                                 "label_block_sha256": "l", "extract_sha256": "e",
                                                 "index_sha256": "i", "counts": {}}
    monkeypatch.setattr(audit, "verify_evidence_completion",
                        lambda *a, **k: {"schema": "r1.c3_audit_completion/3", "label_block_sha256": "l"})
    with pytest.raises(ValueError, match="not a sweep-2 audit completion"):
        release_checks.sweep2_integrity(tmp_path, tmp_path, paper_root=tmp_path, index=tmp_path / "i.json")


def test_sweep2_batch_must_be_the_module_beside_the_checks(monkeypatch):
    monkeypatch.setattr(SB, "__file__", "/elsewhere/sweep2_batch.py")
    with pytest.raises(ValueError, match="shadowed"):
        release_checks._sweep2_batch_published()


def test_verify_completion_refuses_a_profile_mismatch(tmp_path, monkeypatch):
    """A sweep-2 audit cannot be consumed as sweep 1, nor a sweep-1 audit as sweep 2 (environment source record)."""
    c2, out2 = _completion_world(tmp_path / "s2", monkeypatch, "sweep2")
    table, index = tmp_path / "s2/table", tmp_path / "s2/index"
    monkeypatch.setattr(audit, "require_integrity_or_test_release", lambda *a: None, raising=False)
    from r1.c3 import release
    monkeypatch.setattr(release, "require_integrity_or_test_release", lambda *a: None)
    with pytest.raises(ValueError, match="offered as sweep 1"):
        audit.verify_evidence_completion(table, out2 / "label_block.jsonl", tmp_path / "s2", index,
                                         tmp_path / "s2/classification", "sweep1")
    c1, out1 = _completion_world(tmp_path / "s1", monkeypatch, "sweep1")
    with pytest.raises(ValueError, match="sweep-2 source or harness-equivalence"):
        audit.verify_evidence_completion(tmp_path / "s1/table", out1 / "label_block.jsonl", tmp_path / "s1",
                                         tmp_path / "s1/index", None, "sweep2")


def test_sweep2_batch_published_git_checks(monkeypatch):
    """The module must equal origin/main and be unmodified (both git answers are consulted)."""
    calls = []

    def fake_run(answers):
        def run(cmd, **kw):
            calls.append(cmd)
            rc, out = answers["diff" if "diff" in cmd else "status"]
            return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr="")
        return run
    monkeypatch.setattr(subprocess, "run", fake_run({"diff": (0, ""), "status": (0, "")}))
    release_checks._sweep2_batch_published()
    assert any("refs/remotes/origin/main" in c for c in calls)
    for answers in ({"diff": (1, ""), "status": (0, "")}, {"diff": (0, ""), "status": (0, " M r1/c3/sweep2_batch.py")}):
        monkeypatch.setattr(subprocess, "run", fake_run(answers))
        with pytest.raises(ValueError, match="differs from origin/main or is modified"):
            release_checks._sweep2_batch_published()


def test_sweep2_completion_verifies_end_to_end(tmp_path, monkeypatch):
    """Positive round trip of ``verify_evidence_completion(source='sweep2')`` on a synthetic audit directory (the
    reviewer's probe, with the addendum pins and the harness-equivalence paths it now checks)."""
    from r1.c3 import release
    from r1.tests.test_c3_evidence_guards import FAKE_ENV, fake_basis, sha
    monkeypatch.setattr(release, "require_integrity_or_test_release", lambda *a: None)
    table = tmp_path / "table"
    table.mkdir()
    for name in ("build.json", "proposals.jsonl", "configs.json"):
        (table / name).write_text("{}")
    auth = tmp_path / SB.AUTHORIZATION["path"]
    auth.parent.mkdir(parents=True)
    auth.write_text("auth2")
    addendum = auth.parent / "c3_sweep2_b2_addendum_x.md"
    addendum.write_text("addendum")
    index = tmp_path / "index"
    index.write_text("index")
    plan = [{"proposal_id": "x", "node": "n", "candidate_hash": "c", "incumbent_hash": "i",
             "reason": "full_population", "inclusion_probability": 1.0}]
    binding = {"counts": {"eligible": 1, "noops": 0, "duplicates": 0}, "source": "sweep2", "extract_sha256": "e" * 64}
    monkeypatch.setattr(audit, "evidence_plan", lambda *args: (plan, binding))
    out = tmp_path / "audits"
    out.mkdir()
    (out / "plan.jsonl").write_text("".join(json.dumps(x) + "\n" for x in plan))
    cache = audit.RunCache(out / "runs.jsonl")
    runtime = {"worker_python": FAKE_ENV["worker_python"], "prefix": FAKE_ENV["worker_prefix"],
               "base_prefix": "/base", "versions": FAKE_ENV["worker_versions"],
               "package_list_sha256": FAKE_ENV["package_list_sha256"], "worker_command_python": "/wrapper/python3",
               "worker_python_realpath": "/system/python3"}
    cache.add([{"node": "n", "config_hash": h, "seed": s, "success": True, "changed_files": False,
                "metric": float(s), "wall_seconds": 1, "worker_runtime": runtime}
               for h in ("c", "i") for s in audit.DEFAULT_SEEDS])
    result = audit.validate_evidence_results(plan, cache)

    def blocks(_table, values):
        return ([{"proposal_id": "x", "delta_label": values[0]["delta_audit"]}],
                [{"proposal_id": "x", "delta_evaluation": values[0]["delta_audit"]}])
    monkeypatch.setattr(audit, "evidence_blocks", blocks)
    labels, evaluations = blocks(table, result)
    (out / "label_block.jsonl").write_text("".join(json.dumps(x) + "\n" for x in labels))
    (out / "evaluation_block.jsonl").write_text("".join(json.dumps(x) + "\n" for x in evaluations))
    pins = {"sweep2_index_sha256": sha(index), "sweep2_extract_sha256": "e" * 64,
            "table_proposals_sha256": sha(table / "proposals.jsonl"), "table_configs_sha256": sha(table / "configs.json")}
    environment = {"harness_commit": audit.AUDIT_HARNESS, "harness_dirty": False,
                   "scikit_learn": "1.8.0", "python": "3.13.2", "uv_lock_sha256": "locked",
                   "paper_code_clean": True, "paper_code_commit": "a" * 40, "review_path": "docs/r1/reviews/test.md",
                   "environment_basis": fake_basis("3.13.2"),
                   "environment_checks_at_start": {k: fake_basis("3.13.2")["interpreter"][k] for k in
                                                   ("build", "prefix", "wrapper_target", "package_list_sha256",
                                                    "newest_dist_info_mtime_utc")},
                   "harness_untracked": {"data_caches_sha256": fake_basis()["data_caches_sha256"]},
                   "worker_runtime_basis": audit.worker_runtime_basis(),
                   "b2_addendum": {"path": "docs/r1/authorizations/c3_sweep2_b2_addendum_x.md",
                                   "sha256": sha(addendum), "pins": pins},
                   "source": "sweep2",
                   "sweep2_harness_equivalence": {"diff": "empty", "paths": list(audit.SWEEP2_EQUAL_PATHS)},
                   **FAKE_ENV}
    environment.pop("harness_root", None)
    monkeypatch.setattr(audit, "replay_environment_basis", lambda *a: fake_basis("3.13.2"))
    monkeypatch.setattr(audit, "b2_addendum", lambda *a: dict(environment["b2_addendum"]))
    review = b"Code-Commit: " + b"a" * 40 + b"\nVerdict: ACCEPTED\n"
    environment["review_sha256"] = hashlib.sha256(review).hexdigest()
    monkeypatch.setattr(audit.subprocess, "check_output",
                        lambda cmd, **kw: "published\n" if "rev-parse" in cmd else review)
    real_run = subprocess.run
    monkeypatch.setattr(audit.subprocess, "run", lambda *args, **kw: None)
    (out / "environment.json").write_text(json.dumps(environment))
    (out / "resources.json").write_text("{}")
    completion = audit._completion("sweep2", paper_root=tmp_path, table=table, out=out, index=index,
                                   classification=None, binding=binding, addendum_sha256=sha(addendum),
                                   label_block=out / "label_block.jsonl")
    (out / "evidence_completion.json").write_text(json.dumps(completion, indent=2) + "\n")
    got = audit.verify_evidence_completion(table, out / "label_block.jsonl", tmp_path, index, None, "sweep2")
    assert got["source"] == "sweep2" and release.evidence_tier(out) == "T0"
    # the same audit with an index other than the pinned one is refused on consumption
    index.write_text("index2")
    with pytest.raises(ValueError, match="differs from the addendum's pins"):
        audit.verify_evidence_completion(table, out / "label_block.jsonl", tmp_path, index, None, "sweep2")
    monkeypatch.setattr(audit.subprocess, "run", real_run)
