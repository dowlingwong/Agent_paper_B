"""G.5 code unit part 3b-2: the seal (sweep2/t1_tasl/g5_seal.py), the locked assembly (g5_assemble.py), the
REL-T1-G1B copy step (g5_relcopy.py), the G.5 integrity check registered in r1/c3/release_checks.py, and the
G5-TASL-GPUH B spans. Synthetic only: fake host tools, a fake proposer, fake harness engines and synthetic values; no
GPU, no network, no sealed data, no real label. The release rows are faked where a test needs them present; where a
test needs them absent it uses the real ``r1.c3.release.release_row`` on this checkout, whose PLAN has neither T1 row.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
sys.path.insert(0, str(ROOT))
import g5_tasl as S  # noqa: E402
import g5_job as J  # noqa: E402
import g5_seal as SE  # noqa: E402
import g5_assemble as A  # noqa: E402
import g5_relcopy as RC  # noqa: E402
import g1b_tasl as G  # noqa: E402
import g4_tasl as T4  # noqa: E402
from r1.c3 import release as R, release_checks  # noqa: E402

SPEC = json.loads((ROOT / "sweep2" / "t1_tasl" / "g5_tasl_spec.json").read_text())
UUID2 = SPEC["worker"]["gpu_uuid"]
LS = J.LEDGER_SCHEMA
NODE = "mlab_imdb"
SIGMA = 0.0125
NODE_YAML = {"maximize": b"schema: trackg_node/v1\nname: mlab_imdb\nsuite: mlagentbench\nmetric_direction: maximize\n",
             "minimize": b"schema: trackg_node/v1\nname: mlab_imdb\nsuite: mlagentbench\nmetric_direction: minimize\n"}
EVAL = set(range(7006, 7011))
LABEL = set(range(7001, 7006))


def stop(match, fn, *a, exc=J.Stop, **kw):
    with pytest.raises(exc, match=match):
        return fn(*a, **kw)


def value(state: str, seed: int) -> float:
    """A synthetic metric per code state and seed (never a real value)."""
    return int(hashlib.sha256(f"{state}:{seed}".encode()).hexdigest()[:8], 16) % 10000 / 10000.0


# =============================================================================================== fakes
def campaign_ledger(k, wave, *, direction="maximize", divergent=()):
    """Instance k: step 1 keeps the common diff d1 from the baseline B, then discarded, inert, duplicate and invalid
    steps, with campaign values and best_after as the v2-diff engine writes them."""
    better = (lambda a, b: a > b) if direction == "maximize" else (lambda a, b: a < b)
    best = 0.40
    lines = [json.dumps({"schema": LS, "step": 0, "decision": "baseline", "runs": [{"code_state_sha256": "B"}],
                         "final_outcome": {"kind": "ok", "value": best}, "best_after": best})]
    parent = "B"

    def call():
        return {"usage": {"prompt_tokens": 1000, "completion_tokens": 300}, "request": {"cache_prompt": False}}
    for s in range(1, 21):
        e = {"schema": LS, "step": s, "manager_call": call()}
        if s == 1:
            v = 0.50 if direction == "maximize" else 0.30
            e.update(decision="kept", proposal={"diff": "d1"}, final_outcome={"kind": "ok", "value": v},
                     runs=[{"code_state_sha256": "C1", "incumbent_code_state_sha256": "B", "executed": True,
                            "elapsed_seconds_info_only": 10.0}])
            best, parent = v, "C1"
        elif s in (4, 12):
            e.update(decision="invalid_proposal")
        elif s % 4 in (2, 3):
            cand = f"S{wave}{k}_{s}"
            if s in divergent:
                e.update(decision="discarded_divergent", final_outcome={"kind": "divergent", "reason": "timeout"})
            else:
                v = 0.45 if direction == "maximize" else 0.35
                assert not better(v, best)
                e.update(decision="discarded", final_outcome={"kind": "ok", "value": v})
            e.update(proposal={"diff": f"diff-{wave}{k}-{s}"},
                     runs=[{"code_state_sha256": cand, "incumbent_code_state_sha256": parent, "executed": True,
                            "elapsed_seconds_info_only": 10.0}])
        elif s == 5:
            e.update(decision="not_run_duplicate", runs=[{"code_state_sha256": "C1", "executed": False}])
        else:
            e.update(decision="not_run_inert", runs=[{"code_state_sha256": parent, "executed": False}])
        e["best_after"] = best
        lines.append(json.dumps(e))
    return lines


# the isolation block as audit_g5._isolation_block writes it at the G.5 harness commits (all six keys); the
# engines' records carry stop and stop_kind (harness report G5_ENGINES_20261123 §2 items 11, 17)
ISOLATED = {"effective": True, "waivers": {}, "exceptions": [], "log_intact": True, "parent_traced_by": None,
            "parent_dumpable_at_accept": False}


class Engine:
    """Fake harness engines per g5_job.engine_contract(): ledgers, and audit rows whose ok rows carry outcome.value."""

    def __init__(self, spec, *, direction="maximize", divergent_label=(), divergent_eval=(), parent_div=(),
                 campaign_divergent=()):
        self.spec, self.direction = spec, direction
        self.divergent_label, self.divergent_eval = set(divergent_label), set(divergent_eval)
        self.parent_div, self.campaign_divergent = set(parent_div), tuple(campaign_divergent)

    def kind(self, state, seed):
        if seed in LABEL and (state in self.divergent_label or state in self.parent_div):
            return "divergent"
        if seed in EVAL and state in self.divergent_eval:
            return "divergent"
        return "ok"

    def __call__(self, argv, **kw):
        out = Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True)
        if "--campaign" in argv:
            f = json.loads(Path(argv[argv.index("--campaign") + 1]).read_text())
            for inst in f["instances"]:
                d = out / J.campaign_dir_name(inst)
                d.mkdir()
                (d / "campaign_ledger.jsonl").write_text("\n".join(campaign_ledger(
                    inst["instance"], f["wave"], direction=self.direction, divergent=self.campaign_divergent)) + "\n")
            (out / "campaign_record.json").write_text(json.dumps({"stop": None, "stop_kind": None}))
        else:
            chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
            state = {u["unit"]: u["code_state_sha256"] for u in chunk["units"]}
            rows = []
            for r in chunk["runs"]:
                st = state[r["unit"]]
                k = self.kind(st, r["seed"])
                outcome = {"kind": k, "reason": None}
                if k == "ok":
                    outcome["value"] = value(st, r["seed"])
                rows.append(json.dumps({"schema": J.ROW_SCHEMA, "unit": r["unit"], "seed": r["seed"],
                                        "executed": True, "code_state_sha256": st, "outcome": outcome,
                                        "isolation": dict(ISOLATED)}))
            (out / "rows.jsonl").write_text("\n".join(rows) + "\n")
            (out / "chunk_record.json").write_text(json.dumps({"stop": None, "stop_kind": None}))
        return subprocess.CompletedProcess(argv, 0, "engine ok", "")


class Server:
    def __call__(self, url, timeout=10.0):
        if url.endswith("/health"):
            return 200, b'{"status":"ok"}'
        return 200, json.dumps({"default_generation_settings": {"n_ctx": 32768}, "total_slots": 1,
                                "build_info": T4.props_build(SPEC["proposer"]["expected_build"]),
                                "model_path": SPEC["proposer"]["model_path"]}).encode()


@pytest.fixture
def world(tmp_path, monkeypatch):
    s = copy.deepcopy(SPEC)
    s["run_id"] = "c3_t1_labels_20261201"
    s["worker"].update(runs_root=str(tmp_path / "runs"), sealed_root=str(tmp_path / "sealed"),
                       base=str(tmp_path / "base"))
    s["proposer"].update(run_dir=str(tmp_path / "proposer"), sealed_root=str(tmp_path / "proposer_sealed"))
    for fam, c in (("G5-7", "7"), ("G5-AR", "8")):
        s["harness_families"][fam].update(g5_commit=c * 40, harness_dir=str(tmp_path / f"h{c}"))
    S.node_entry(s, NODE)["node_spec_sha256"] = hashlib.sha256(NODE_YAML["maximize"]).hexdigest()
    repo = tmp_path / "repo"                             # the committed REL-T1-G1B copy the row cites
    summary = {"schema": G.SUMMARY_SCHEMA, "label": G.ENGINEERING_ONLY, "run_id": "g1b-tasl-20261121-b",
               "verdicts": {NODE: {"qualifies_D21": True, "sigma_joint": SIGMA}}}
    rel = "docs/r1/reports/g5_rel_t1_g1b_x/seven/summary.json"
    (repo / rel).parent.mkdir(parents=True)
    (repo / rel).write_text(json.dumps(summary))
    s["noise_floor"]["seven"].update(copy=rel, sha256=G.L._sha_file(repo / rel))
    monkeypatch.setattr(S, "REPO_ROOT", repo)
    sp = tmp_path / "g5_spec.json"
    sp.write_text(json.dumps(s))
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path / "home" / p.lstrip("~/")))
    monkeypatch.setattr(G, "host_identity", lambda sh, h: {"host": h})
    monkeypatch.setattr(G, "ptrace_scope", lambda: 1)
    (tmp_path / "cgroup" / "scope").mkdir(parents=True)          # the test's own scope, never a real cgroup path
    monkeypatch.setattr(G, "scope_cgroup", lambda: {"cgroup_parent": str(tmp_path / "cgroup" / "scope")})
    monkeypatch.setattr(G, "harness_checkout", lambda sh, h, git=None: {"commit": sh["harness"]["commit"]})
    monkeypatch.setattr(G, "environment", lambda sh, h, n: {"name": n["env"],
                                                            "python": sh["hosts"][h]["env_python"][n["env"]]})
    monkeypatch.setattr(G, "check_affinity", lambda sh, n, affinity=None: [0])
    monkeypatch.setattr(os, "environ", dict(os.environ))
    p = s["proposer"]
    rec = {"schema": T4.SERVER_RECORD_SCHEMA, "run_id": s["run_id"], "host": "TASL-7", "hostname": p["hostname"],
           "server_url": p["server_url"], "spec_sha256": G.L._sha_file(sp), "binary_sha256": p["binary_sha256"],
           "bin_dir_manifest_sha256": p["bin_dir_manifest_sha256"], "model_sha256": T4.MODEL["sha256"],
           "build": f"version: {p['expected_build']}", "argv": T4.server_argv(s, 8095),
           "gpu": {"uuid": p["gpu_uuid"], "name": T4.GPU_MODEL}, "pid": 7, "started_utc": "2026-12-01T00:00:00Z"}
    srv = tmp_path / "server_record.json"
    srv.write_text(json.dumps(rec))

    def smi(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID2}, NVIDIA GeForce RTX 4090, 535.309.01, 24564\n", "")

    def git(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, "", "")
    return {"spec": s, "sp": sp, "srv": srv, "smi": smi, "git": git, "tmp": tmp_path, "rel": rel, "repo": repo}


def run_node(w, engine, node=NODE):
    """Both waves of one node through the real job code (campaigns, every audit chunk, the wave checks)."""
    for wave in (1, 2):
        J.run_job(w["sp"], node, f"campaigns-wave{wave}", {"K": 10}, smi=w["smi"], engine=engine,
                  setup=lambda h, n, b, o: {"data_root": str(b / "data")}, get=Server(), git=w["git"],
                  server_record=w["srv"])
        while not J.audits_done(w["spec"], node, wave):
            J.run_job(w["sp"], node, f"audits-wave{wave}", {"K": 10}, smi=w["smi"], engine=engine,
                      setup=lambda h, n, b, o: {"data_root": str(b / "data")}, get=Server(), git=w["git"])


def run_node_rest(w, engine, node=NODE):
    """The rest of a node after its wave-1 campaigns."""
    setup = (lambda h, n, b, o: {"data_root": str(b / "data")})
    while not J.audits_done(w["spec"], node, 1):
        J.run_job(w["sp"], node, "audits-wave1", {"K": 10}, smi=w["smi"], engine=engine, setup=setup, get=Server(),
                  git=w["git"])
    J.run_job(w["sp"], node, "campaigns-wave2", {"K": 10}, smi=w["smi"], engine=engine, setup=setup, get=Server(),
              git=w["git"], server_record=w["srv"])
    while not J.audits_done(w["spec"], node, 2):
        J.run_job(w["sp"], node, "audits-wave2", {"K": 10}, smi=w["smi"], engine=engine, setup=setup, get=Server(),
                  git=w["git"])


def seal_node(w, node=NODE):
    for a in SE._node_attempts(w["spec"], node):
        SE.seal_attempt(w["spec"], a)
    return SE.seal_node(w["spec"], node)


def lock_for(w, *stages):
    """A fake release-row check: the stages given exist; any other is a ReleaseStop as the real check gives."""
    rows = {"traindev": {"row_id": SE.UNSEAL_ROW, "decision_sha256": "d" * 64,
                         "g1b_summaries": {NODE: {"path": w["rel"], "sha256": w["spec"]["noise_floor"]["seven"]["sha256"]}}},
            "test": {"row_id": SE.TEST_ROW, "decision_sha256": "e" * 64}}

    def lock(stage):
        if stage not in stages:
            raise R.ReleaseStop(f"STOP: {rows[stage]['row_id']} is absent in PLAN §10 (PRE-STAGE A)")
        return rows[stage]
    return lock


def node_git(direction="maximize"):
    def git(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, NODE_YAML[direction], b"")
    return git


# =============================================================================================== the seal
def test_seal_attempt_receipts_and_refusals(world):
    s = world["spec"]
    run_node(world, Engine(s))
    attempts = SE._node_attempts(s, NODE)
    assert len(attempts) > 4
    rec = SE.seal_attempt(s, attempts[0])
    target = SE.sealed_attempt_of(s, attempts[0])
    assert rec["kind"] == "attempt" and set(rec["files"]) == {"out.tar", "job_record.json", "diagnostics.json",
                                                              "SHA256SUMS"}
    assert SE.verify_sealed(target)["job_record_sha256"] == G.L._sha_file(attempts[0] / "job_record.json")
    stop("exists or has a symlink", SE.seal_attempt, s, attempts[0])                 # never overwrite
    (target / "diagnostics.json").write_text("{}")                                    # a changed sealed file
    stop("differs from its seal receipt", SE.verify_sealed, target)
    (target / "extra.txt").write_text("x")
    stop("differs from its seal receipt", SE.verify_sealed, target)
    other = attempts[1]
    (other / "diagnostics.json").write_text((other / "diagnostics.json").read_text() + " ")
    stop("SHA256SUMS", SE.seal_attempt, s, other)
    stop("is not <run_id>", SE.seal_attempt, s, world["tmp"] / "runs")
    enc = copy.deepcopy(s)
    enc["key_values"]["seal_mode"] = "encryption"
    stop("encryption alternative of §6 is not built", SE.seal_attempt, enc, attempts[2])


def test_seal_out_left_in_clear_and_closed_attempts(world, monkeypatch):
    s = world["spec"]
    monkeypatch.setattr(J, "make_tar", lambda d: False)                    # a tar failure keeps out/ in clear
    stop("out.tar could not be written", J.run_job, world["sp"], NODE, "campaigns-wave1", {"K": 10},
         smi=world["smi"], engine=Engine(s), setup=lambda h, n, b, o: {"data_root": "/d"}, get=Server(),
         git=world["git"], server_record=world["srv"])
    att = J.job_dir(s, NODE, "campaigns-wave1") / "attempt-1"
    n_files = sum(1 for p in (att / "out").rglob("*") if p.is_file())
    rec = SE.seal_attempt(s, att)
    assert rec["out_clear_files"] == n_files and not (att / "out").exists()          # sealed, then removed
    with tarfile.open(SE.sealed_attempt_of(s, att) / "out_clear.tar") as tar:
        assert any(m.name.endswith("campaign_ledger.jsonl") for m in tar)
    # a closed attempt (close-attempt): a record without sums; its partial out/ is sealed too
    _, d = G.next_attempt(J.job_dir(s, NODE, "campaigns-wave1"))
    (d / "out").mkdir()
    (d / "out" / "x.log").write_text("partial")
    stop("has no job record", SE.seal_attempt, s, d)
    J.close_attempt(s, world["sp"], NODE, "campaigns-wave1", d, "OOM kill in the delegated scope",
                    scan=lambda p: [], alive=lambda pid: False)
    r = SE.seal_attempt(s, d)
    assert "SHA256SUMS" not in r["files"] and r["out_clear_files"] == 1 and r["stop_class"] == "infrastructure"


def test_seal_node_and_run(world):
    s = world["spec"]
    J.run_job(world["sp"], NODE, "campaigns-wave1", {"K": 10}, smi=world["smi"], engine=Engine(s),
              setup=lambda h, n, b, o: {"data_root": "/d"}, get=Server(), git=world["git"], server_record=world["srv"])
    stop("has not ended", SE.seal_node, s, NODE)                         # mid-table: its plans are not final
    run_node_rest(world, Engine(s))
    stop("has no SEAL_RECEIPT", SE.seal_node, s, NODE)                   # every attempt sealed first
    rec = seal_node(world)
    assert {"wave1_plan.tar", "wave1_plan_index.json", "wave2_plan.tar", "wave_checks_wave1.json",
            "wave_checks_wave2.json"} <= set(rec["files"]) and rec["ended"] == "wave 2 checked"
    stop("exists", SE.seal_node, s, NODE)
    others = tuple(n for n in S.T1_NODES if n != NODE)
    stop("has not run", SE.seal_run, s, not_run=others[1:])
    stop("not G.5 nodes", SE.seal_run, s, not_run=("x",))
    stop("declared not run", SE.seal_run, s, not_run=others + (NODE,))
    run = SE.seal_run(s, not_run=others)
    assert {"_access_log.jsonl", "_k_lock.json"} <= set(run["files"])
    SE.verify_sealed(SE.sealed_run(s) / "_run")


# =============================================================================================== TASL-7, spans
def make_server_dir(w, n=1):
    s = w["spec"]
    d = Path(s["proposer"]["run_dir"]) / s["run_id"] / f"server-{n}"
    d.mkdir(parents=True)
    rec = {"run_id": s["run_id"], "server_dir": str(d), "pid": 4242, "started_utc": "2026-12-01T00:00:00Z"}
    (d / "server_record.json").write_text(json.dumps(rec))
    (d / "llama-server.log").write_text("prompt: ... step 3 metric 0.8123 ...\n")
    (d / "bin_manifest.txt").write_text("m\n")
    return d


def end_server(d):
    end = {"stopped_utc": "2026-12-01T05:00:00Z", "server_rc": 0, "stop_signal": 15,
           "server_record_sha256": G.L._sha_file(d / "server_record.json"),
           "server_log_sha256": G.L._sha_file(d / "llama-server.log")}
    (d / "server_end.json").write_text(json.dumps(end))


def test_seal_server_and_its_log(world):
    s = world["spec"]
    d = make_server_dir(world)
    stop("has no server_end.json", SE.seal_server, s, d, alive=lambda pid: False)
    end_server(d)
    stop("still alive", SE.seal_server, s, d, alive=lambda pid: True)
    (d / "llama-server.log").write_text("changed after the end\n")
    stop("does not bind", SE.seal_server, s, d, alive=lambda pid: False)
    (d / "llama-server.log").write_text("prompt: ... step 3 metric 0.8123 ...\n")
    r = SE.seal_server(s, d, alive=lambda pid: False)
    assert r["span_seconds"] == 5 * 3600.0 and not (d / "llama-server.log").exists()   # the prompts left clear
    assert (d / "server_record.json").exists()
    stop("has no llama-server.log|exists", SE.seal_server, s, d, alive=lambda pid: False)     # sealed once
    # the sealed log opens only after the test release row (it carries per-step metric values)
    stop("R1-T1-LABELS-UNSEAL", SE.open_server_log, s, "server-1", "server log: STOP 12 diagnosis", exc=R.ReleaseStop)
    stop("R1-T1-LABELS-TEST-RELEASE", SE.open_server_log, s, "server-1", "server log: x",
         lock=lock_for(world, "traindev"), exc=R.ReleaseStop)
    raw = SE.open_server_log(s, "server-1", "server log: after the test release", lock=lock_for(world, "traindev",
                                                                                                     "test"))
    assert b"0.8123" in raw
    assert len(SE.check_access_log(s, root=SE.proposer_sealed_run(s))) == 1
    other = make_server_dir(world, 2)
    stop("not a server-N directory", SE.seal_server, s, other.parent, alive=lambda pid: False)


def test_server_span_registration(world, tmp_path):
    s = world["spec"]
    d = make_server_dir(world)
    end_server(d)
    r = SE.seal_server(s, d, alive=lambda pid: False)
    receipt = tmp_path / "copied_receipt.json"
    receipt.write_bytes((SE.proposer_sealed_run(s) / "server-1" / SE.RECEIPT).read_bytes())
    assert SE.register_server_span(s, receipt)["span_seconds"] == r["span_seconds"]
    assert SE.register_server_span(s, receipt)["server"] == "server-1"           # the same bytes again: accepted
    bad = json.loads(receipt.read_text()) | {"span_seconds": 1.0}
    receipt.write_text(json.dumps(bad))
    stop("does not match its times", SE.register_server_span, s, receipt)
    other = json.loads((SE.proposer_sealed_run(s) / "server-1" / SE.RECEIPT).read_text()) | {"pid": 1}
    receipt.write_text(json.dumps(other, indent=2))
    stop("exists with other content", SE.register_server_span, s, receipt)
    receipt.write_text(json.dumps(other | {"run_id": "c3_t1_labels_20990101"}))
    stop("not a server seal receipt", SE.register_server_span, s, receipt)
    assert SE.proposer_seconds(s)["seconds"] == 5 * 3600.0


def test_gpuh_b_campaign_needs_the_server_start(world):
    s = S.apply_options(world["spec"], {"G5-TASL-GPUH": "B"})
    world["sp"].write_text(json.dumps(s))
    rec = json.loads(world["srv"].read_text())
    rec.pop("started_utc")
    world["srv"].write_text(json.dumps(rec | {"spec_sha256": G.L._sha_file(world["sp"])}))
    stop("has no started_utc", J.run_job, world["sp"], NODE, "campaigns-wave1", {"K": 10}, smi=world["smi"],
         engine=Engine(s), setup=lambda h, n, b, o: {"data_root": "/d"}, get=Server(), git=world["git"],
         server_record=world["srv"])


# =============================================================================================== locks
def test_reader_locks(world, monkeypatch):
    s = world["spec"]
    run_node(world, Engine(s))
    seal_node(world)
    tree = SE.SealedTree(s)                                             # the real row check: no T1 row on PLAN
    camp = SE.sealed_attempt_of(s, J.job_dir(s, NODE, "campaigns-wave1") / "attempt-1")
    stop("STOP 11", tree.ledgers, camp, "curiosity")
    stop("R1-T1-LABELS-UNSEAL", tree.ledgers, camp, "assembly traindev: x", exc=R.ReleaseStop)
    stop("integrity check", tree.ledgers, camp, "release integrity traindev: x")
    t2 = SE.SealedTree(s, lock=lock_for(world, "traindev"))
    stop("R1-T1-LABELS-TEST-RELEASE", t2.ledgers, camp, "assembly test: x", exc=R.ReleaseStop)
    with R.integrity_context():                                          # the carve-out still needs the row
        stop("R1-T1-LABELS-UNSEAL", tree.ledgers, camp, "release integrity traindev: x", exc=R.ReleaseStop)
        assert t2.ledgers(camp, "release integrity traindev: x")
    got = t2.ledgers(camp, "assembly traindev: ledgers")
    assert sorted(got) == [f"instance_{k}_history" for k in range(1, 5)]
    log = SE.check_access_log(s)
    assert len(log) == 2 and all(e["lock"]["rows"][0]["row_id"] == SE.UNSEAL_ROW for e in log)
    assert all(e["what"] == "ledgers" and len(e["members"]) == 4 for e in log)         # member names logged (M1)
    with (SE.sealed_run(s) / SE.ACCESS_LOG).open("a") as fh:          # a forged opening without its lock
        fh.write(json.dumps(log[0] | {"purpose": "assembly test: x"}) + "\n")
    stop("STOP 11", SE.check_access_log, s)


def test_each_purpose_takes_only_its_members_and_no_evaluation_seed_leaves_at_traindev(world):
    """Review M1 (the reviewer's probe): raw rows cannot be asked for; a ledgers opening of a chunk tar refuses; a
    chunk's rows reach a train/dev caller with no evaluation-seed kind or value; the test stage gets them."""
    s = world["spec"]
    run_node(world, Engine(s, divergent_eval={"S13_7"}))
    seal_node(world)
    chunk = SE.sealed_run(s) / NODE / "audits-wave1" / "chunk-0" / "attempt-1"
    t2 = SE.SealedTree(s, lock=lock_for(world, "traindev"))
    stop("STOP 11", t2._open, chunk, "out.tar", "rows", "assembly traindev: rows")
    stop("STOP 11", t2._open, chunk, "plan.tar", "chunk", "assembly traindev: x")
    stop("ledgers members", t2.ledgers, chunk, "assembly traindev: ledgers of a chunk")
    got = t2.chunk_rows(chunk, "assembly traindev: rows")
    assert {sd for _, sd in got["rows"]} <= LABEL and got["evaluation_rows_dropped"] > 0
    assert "out/audit/rows.jsonl" not in got and set(got) == {"chunk", "rows", "evaluation_rows_dropped"}
    raw = t2._open(chunk, "out.tar", "chunk", "assembly traindev: private")     # round-2 n1: the private opener
    assert "out/audit/rows.jsonl" not in raw and {sd for _, sd in raw["rows"]} <= LABEL   # reduces too
    t3 = SE.SealedTree(s, lock=lock_for(world, "traindev", "test"))
    full = t3.chunk_rows(chunk, "assembly test: rows")
    assert {sd for _, sd in full["rows"]} == LABEL | EVAL and full["evaluation_rows_dropped"] == 0
    entry = SE.check_access_log(s)[-1]
    assert entry["what"] == "chunk" and entry["members"] == sorted(SE.CHUNK_MEMBERS)
    assert SE.LEDGER_MEMBER.pattern == J.LEDGER_MEMBER.pattern and SE.CHUNK_MEMBERS == J.CHUNK_MEMBERS


def test_reduce_rows_checks_evaluation_values_without_keeping_them():
    """At train/dev an ok evaluation-seed row must carry a finite numeric outcome.value (review m7, found before the
    arms freeze), but neither it nor the kind is returned; at test both are."""
    plan = J.audit_plan(SPEC, NODE, 1, {"instance_1_history": campaign_ledger(1, 1)[:4]}, k=10)
    chunk = J.audit_chunk_file(SPEC, S.node_entry(SPEC, NODE), plan, 0, J.chunk_plan(plan, {"run_seconds": 1})[0],
                               interpreter="/py", cgroup_parent="/cg", deadline_epoch=1.0)
    state = {u["unit"]: u["code_state_sha256"] for u in chunk["units"]}

    def rows(eval_value):
        return [json.dumps({"schema": J.ROW_SCHEMA, "unit": r["unit"], "seed": r["seed"], "executed": True,
                            "code_state_sha256": state[r["unit"]],
                            "outcome": {"kind": "ok", **({"value": 0.5} if r["seed"] in LABEL else eval_value)},
                            "isolation": dict(ISOLATED)}) for r in chunk["runs"]]
    got = SE.reduce_rows(SPEC, rows({"value": 0.25}), chunk, "traindev")
    assert {sd for _, sd in got["rows"]} == LABEL and all(v == ("ok", 0.5) for v in got["rows"].values())
    stop("finite numeric outcome.value", SE.reduce_rows, SPEC, rows({}), chunk, "traindev")
    stop("finite numeric outcome.value", SE.reduce_rows, SPEC, rows({"value": "0.25"}), chunk, "traindev")
    full = SE.reduce_rows(SPEC, rows({"value": 0.25}), chunk, "test")
    assert {sd for _, sd in full["rows"]} == LABEL | EVAL


# =============================================================================================== the assembly
def sign_note(world, choice):
    """The spec's t1_table_readings choice and a signed note carrying the line (before the run: records bind the
    spec's sha256). Returns the note path and an on_main that compares with the synthetic main (the tmp repo)."""
    s = world["spec"]
    s["key_values"]["t1_table_readings"]["campaign_divergent_delta_hat"] = choice
    world["sp"].write_text(json.dumps(s))
    rec = json.loads(world["srv"].read_text())
    world["srv"].write_text(json.dumps(rec | {"spec_sha256": G.L._sha_file(world["sp"])}))
    note = world["repo"] / "docs/r1/authorizations" / f"{s['run_id']}.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(f"approved: true\nspec_sha256: {G.L._sha_file(world['sp'])}\n"
                    f"t1_table_readings: {S.table_readings_line(s)}\n")
    return note, (lambda rel, raw: (world["repo"] / rel).read_bytes() == raw)


def assemble_world(world, engine, *, direction="maximize", choice=None):
    s = world["spec"]
    if direction != "maximize":
        S.node_entry(s, NODE)["node_spec_sha256"] = hashlib.sha256(NODE_YAML[direction]).hexdigest()
        world["sp"].write_text(json.dumps(s))
        rec = json.loads(world["srv"].read_text())
        world["srv"].write_text(json.dumps(rec | {"spec_sha256": G.L._sha_file(world["sp"])}))
    note = sign_note(world, choice) if choice else None
    run_node(world, engine)
    seal_node(world)
    SE.seal_run(s, not_run=tuple(n for n in S.T1_NODES if n != NODE))
    return world["tmp"] / "out" / "table", world["tmp"] / "out" / "evidence", note


def expected_label(cand, parent, sign=1.0):
    d = [sign * (value(cand, sd) - value(parent, sd)) for sd in sorted(LABEL)]
    m = math.fsum(d) / len(d)
    return m, math.sqrt(math.fsum((x - m) ** 2 for x in d) / (len(d) - 1)) / math.sqrt(len(d))


def test_assembly_traindev_then_test(world):
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s, divergent_label={"S12_6"}, divergent_eval={"S13_7"}))
    stop("R1-T1-LABELS-UNSEAL", A.assemble, world["sp"], "traindev", table, ev, git=node_git(), exc=R.ReleaseStop)
    assert not table.exists() and not ev.exists()
    comp = A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    assert comp["schema"] == A.COMPLETION_SCHEMA and not comp["schema"].startswith("r1.c3_audit_completion/")
    assert sorted(p.name for p in ev.iterdir()) == ["evidence_completion.json", "label_block.jsonl"]   # no eval yet
    assert R.evidence_tier(ev) is None and R.is_evidence_dir(ev)          # raw readers need both tiers' test rows
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()]
    labels = {json.loads(x)["proposal_id"]: json.loads(x) for x in (ev / "label_block.jsonl").read_text().splitlines()}
    assert len(rows) == 12 * 18 and not any(r["decision"] == "invalid_proposal" for r in rows)   # invalid: left out
    by = {r["proposal_id"]: r for r in rows}
    first = by[f"g5.history:{NODE}__s5101:t001"]
    assert (first["incumbent_hash"], first["candidate_hash"], first["instance"]) == ("B", "C1", f"{NODE}__s5101")
    m, se = expected_label("C1", "B")
    lab = labels[first["proposal_id"]]
    assert lab["label_kind"] == "audit" and lab["seeds"] == sorted(LABEL) and lab["delta_label"] == pytest.approx(m)
    assert lab["se_label"] == pytest.approx(se) and lab["soft_parameters"]["sigma_node"] == SIGMA == first["sigma_node"]
    assert all(labels[p]["delta_label"] == lab["delta_label"] for p in by if by[p]["candidate_hash"] == "C1"
               and by[p]["decision"] == "kept")                              # every member carries the group label
    assert labels[f"g5.history:{NODE}__s5102:t006"]["label_kind"] == "divergent"    # E5 on the label seeds
    assert labels[f"g5.history:{NODE}__s5103:t007"]["label_kind"] == "audit"       # evaluation divergence ignored
    noop = by[f"g5.history:{NODE}__s5101:t008"]
    assert noop["noop"] and labels[noop["proposal_id"]]["label_kind"] == "rule_noop" and noop["delta_hat"] == 0.0
    dup = by[f"g5.history:{NODE}__s5101:t005"]
    assert dup["duplicate"] and dup["proposal_id"] not in labels and dup["candidate_hash"] == "C1"
    assert first["delta_hat"] == pytest.approx(0.10)
    build = json.loads((table / "build.json").read_text())
    assert build["nodes"][NODE]["counts"]["excluded"] == {"invalid_proposal": 24} and build["K"] == 10
    assert build["readings"]["campaign_divergent_delta_hat"] == "refuse" and build["readings"]["note"] is None
    stop("written once", A.assemble, world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"),
         git=node_git())
    log = SE.sealed_run(s) / SE.ACCESS_LOG                              # STOP 11 before any further read
    good = log.read_text()
    log.write_text(good + json.dumps({"who": "someone", "purpose": "curiosity"}) + "\n")
    stop("STOP 11", A.assemble, world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"),
         git=node_git())
    log.write_text(good)
    # the test stage: both rows; the table and label block re-derived byte-identically, then the evaluation block
    stop("R1-T1-LABELS-TEST-RELEASE", A.assemble, world["sp"], "test", table, ev, lock=lock_for(world, "traindev"),
         git=node_git(), exc=R.ReleaseStop)
    raw = (table / "proposals.jsonl").read_bytes()                     # a re-derivation mismatch (review m1)
    (table / "proposals.jsonl").write_bytes(raw.replace(b'"delta_hat": 0.0', b'"delta_hat": 0.5', 1))
    stop("proposals.jsonl is not the one", A.assemble, world["sp"], "test", table, ev,
         lock=lock_for(world, "traindev", "test"), git=node_git())
    (table / "proposals.jsonl").write_bytes(raw)
    assert not (ev / "evaluation_block.jsonl").exists()
    comp_t = A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    assert comp_t["label_block_sha256"] == comp["label_block_sha256"] and comp_t["evaluation_seeds"] == sorted(EVAL)
    evals = {json.loads(x)["proposal_id"]: json.loads(x) for x in (ev / "evaluation_block.jsonl").read_text().splitlines()}
    assert set(evals) == {p for p, l in labels.items() if l["label_kind"] != "rule_noop"}
    e = evals[f"g5.history:{NODE}__s5103:t007"]
    assert e["delta_evaluation"] is None and e["k_evaluation"] == 0 and e["divergent_seeds"] == sorted(EVAL)
    e1 = evals[first["proposal_id"]]
    want = math.fsum(value("C1", sd) - value("B", sd) for sd in sorted(EVAL)) / 5
    assert e1["delta_evaluation"] == pytest.approx(want) and e1["k_evaluation"] == 5
    log = SE.check_access_log(s)
    assert {e["purpose"].split(":")[0] for e in log} == {"assembly traindev", "assembly test"}
    # reading a block back through this module: both need the test row (the label block holds test labels; B2)
    stop("R1-T1-LABELS-TEST-RELEASE", A.read_evidence, ev, "label_block.jsonl", lock=lock_for(world, "traindev"),
         exc=R.ReleaseStop)
    stop("R1-T1-LABELS-TEST-RELEASE", A.read_evidence, ev, "evaluation_block.jsonl", lock=lock_for(world, "traindev"),
         exc=R.ReleaseStop)
    stop("R1-T1-LABELS-UNSEAL", A.read_evidence, ev, "label_block.jsonl", exc=R.ReleaseStop)
    with R.integrity_context():                     # inside the release step's integrity check: the train/dev row
        assert A.read_evidence(ev, "label_block.jsonl", lock=lock_for(world, "traindev"))
        stop("R1-T1-LABELS-TEST-RELEASE", A.read_evidence, ev, "evaluation_block.jsonl",
             lock=lock_for(world, "traindev"), exc=R.ReleaseStop)
    assert A.read_evidence(ev, "label_block.jsonl", lock=lock_for(world, "traindev", "test"))


def test_assembly_needs_the_sealed_run(world):
    s = world["spec"]
    run_node(world, Engine(s))
    seal_node(world)
    table, ev = world["tmp"] / "out" / "table", world["tmp"] / "out" / "evidence"
    stop("_run has no SEAL_RECEIPT", A.assemble, world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"),
         git=node_git())
    SE.seal_run(s, not_run=tuple(n for n in S.T1_NODES if n != NODE))
    log = J.run_root(s) / "_access_log.jsonl"                           # the job log grew after the seal (m8)
    log.write_text(log.read_text() + json.dumps({"who": "g5_job", "purpose": "audit planning: late"}) + "\n")
    stop("changed after the run was sealed", A.assemble, world["sp"], "traindev", table, ev,
         lock=lock_for(world, "traindev"), git=node_git())


def test_assembly_readings_are_bound_to_the_signed_note(world):
    s = world["spec"]
    table, ev, (note, on_main) = assemble_world(world, Engine(s, direction="minimize", campaign_divergent=(10,)),
                                                direction="minimize", choice="neg_inf")
    # without the note only refuse applies, whatever the spec says
    stop("diverged or timed out in its campaign", A.assemble, world["sp"], "traindev", table, ev,
         lock=lock_for(world, "traindev"), git=node_git("minimize"))
    stop("not committed byte-identically", A.assemble, world["sp"], "traindev", table, ev, note_path=note,
         on_main=lambda rel, raw: False, lock=lock_for(world, "traindev"), git=node_git("minimize"))
    good = note.read_text()
    note.write_text(good.replace("sigma_cmp = sigma_node", "sigma_cmp = 2 sigma_node"))
    stop("differs from the readings", A.assemble, world["sp"], "traindev", table, ev, note_path=note,
         on_main=on_main, lock=lock_for(world, "traindev"), git=node_git("minimize"))
    note.write_text(good.replace("approved: true", "approved: false"))
    stop("approved: true", A.assemble, world["sp"], "traindev", table, ev, note_path=note, on_main=on_main,
         lock=lock_for(world, "traindev"), git=node_git("minimize"))
    note.write_text(good)
    A.assemble(world["sp"], "traindev", table, ev, note_path=note, on_main=on_main, lock=lock_for(world, "traindev"),
               git=node_git("minimize"))
    rows = {json.loads(x)["proposal_id"]: json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()}
    labels = {json.loads(x)["proposal_id"]: json.loads(x) for x in (ev / "label_block.jsonl").read_text().splitlines()}
    first = rows[f"g5.history:{NODE}__s5101:t001"]
    assert first["delta_hat"] == pytest.approx(0.10)                         # 0.40 -> 0.30 under minimize is +0.10
    assert labels[first["proposal_id"]]["delta_label"] == pytest.approx(expected_label("C1", "B", -1.0)[0])
    div = rows[f"g5.history:{NODE}__s5101:t010"]
    assert div["delta_hat"] == float("-inf") and labels[div["proposal_id"]]["label_kind"] == "audit"
    build = json.loads((table / "build.json").read_text())
    assert build["readings"]["campaign_divergent_delta_hat"] == "neg_inf" and build["readings"]["note"].endswith(
        f"{s['run_id']}.md")
    with R.integrity_context():                     # the release check re-binds the readings to the note
        stop("not committed byte-identically", A.verify_evidence, table, ev, test=False,
             lock=lock_for(world, "traindev"), git=node_git("minimize"), spec_path=world["sp"],
             on_main=lambda rel, raw: False)
        assert A.verify_evidence(table, ev, test=False, lock=lock_for(world, "traindev"), git=node_git("minimize"),
                                 spec_path=world["sp"], on_main=on_main)["pass"]


def test_assembly_leave_out_reading(world):
    s = world["spec"]
    table, ev, (note, on_main) = assemble_world(world, Engine(s, campaign_divergent=(10,)), choice="leave_out")
    A.assemble(world["sp"], "traindev", table, ev, note_path=note, on_main=on_main, lock=lock_for(world, "traindev"),
               git=node_git())
    rows = {json.loads(x)["proposal_id"] for x in (table / "proposals.jsonl").read_text().splitlines()}
    assert f"g5.history:{NODE}__s5101:t010" not in rows and len(rows) == 12 * 17
    build = json.loads((table / "build.json").read_text())
    assert build["nodes"][NODE]["counts"]["excluded"]["discarded_divergent"] == 12


def test_assembly_parent_divergence_stops(world):
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s, parent_div={"C1"}))
    stop("the parent diverged", A.assemble, world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"),
         git=node_git())


def test_assembly_refusals(world):
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s))
    stop("differs from node_spec_sha256", A.assemble, world["sp"], "traindev", table, ev,
         lock=lock_for(world, "traindev"), git=node_git("minimize"))
    sealed = SE.sealed_run(s) / NODE / "campaigns-wave1" / "attempt-1" / "diagnostics.json"
    keep = sealed.read_text()
    sealed.write_text(keep + " ")
    stop("differs from its seal receipt", A.assemble, world["sp"], "traindev", table, ev,
         lock=lock_for(world, "traindev"), git=node_git())
    sealed.write_text(keep)
    b = S.apply_options(s, {"G5-AUDIT": "B"})
    stop("G5-AUDIT B is not built", A.node_rows, b, NODE, {"values": {}, "seeds": {}, "plans": {}, "ledgers": {}},
         {"sign": 1.0}, SIGMA, "traindev", "refuse")
    other = copy.deepcopy(s)                                   # sealed records written under another spec
    other["key_values"]["liveness_floor"] = 0.3
    world["sp"].write_text(json.dumps(other))
    stop("another spec", A.assemble, world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"),
         git=node_git())
    world["sp"].write_text(json.dumps(s))
    inside = SE.sealed_run(s) / "x"
    stop("inside a sealed tree", A.assemble, world["sp"], "traindev", inside / "t", inside / "e",
         lock=lock_for(world, "traindev"), git=node_git())

    def wrong_copy(stage):
        row = lock_for(world, "traindev")(stage)
        return row | {"g1b_summaries": {NODE: {"path": world["rel"], "sha256": "0" * 64}}}
    stop("differs from the sha256 the row cites", A.assemble, world["sp"], "traindev", table, ev, lock=wrong_copy,
         git=node_git())


def test_autoresearch_summary_bound_to_the_completion_record(world):
    """Review m10: under G5-ARPEND A the row's autoresearch summary must be the completion record's noise_floor_copy."""
    s = world["spec"]
    rel = "docs/r1/reports/g5_rel_t1_g1b_x/ar/summary.json"
    (world["repo"] / rel).parent.mkdir(parents=True)
    (world["repo"] / rel).write_text(json.dumps({"schema": G.AR_SUMMARY_SCHEMA, "label": G.ENGINEERING_ONLY,
                                                 "run_id": "g1b-ar-tasl-20261122-a",
                                                 "verdicts": {S.AR: {"qualifies_D21": True, "sigma_joint": 0.03}}}))
    sha = G.L._sha_file(world["repo"] / rel)
    row = {"g1b_summaries": {S.AR: {"path": rel, "sha256": sha}}}
    stop("needs its completion record", A.noise_by_node, s, row)
    stop("not the completion record's noise_floor_copy", A.noise_by_node, s, row,
         ar_record=lambda: {"noise_floor": {"copy": rel, "sha256": "0" * 64}})
    got = A.noise_by_node(s, row, ar_record=lambda: {"noise_floor": {"copy": rel, "sha256": sha}})
    assert got[S.AR]["sigma_node"] == 0.03


def test_integrity_check_and_registration(world):
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    td = lock_for(world, "traindev")
    stop("integrity check", A.verify_evidence, table, ev, test=False, lock=td, git=node_git(), spec_path=world["sp"])
    with R.integrity_context():
        out = A.verify_evidence(table, ev, test=False, lock=td, git=node_git(), spec_path=world["sp"])
        assert out["pass"] and out["completion"]["label_block_sha256"] == G.L._sha_file(ev / "label_block.jsonl")
        assert "evaluation_block_sha256" not in out["completion"]
        stop("R1-T1-LABELS-TEST-RELEASE", A.verify_evidence, table, ev, test=True, lock=td, git=node_git(),
             spec_path=world["sp"], exc=R.ReleaseStop)
        lb = (ev / "label_block.jsonl").read_bytes()
        (ev / "label_block.jsonl").write_bytes(lb.replace(b'"delta_label": ', b'"delta_label": 1', 1))
        stop("label_block.jsonl differs", A.verify_evidence, table, ev, test=False, lock=td, git=node_git(),
             spec_path=world["sp"])
        (ev / "label_block.jsonl").write_bytes(lb)
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    with R.integrity_context():
        stop("before R1-T1-LABELS-TEST-RELEASE", A.verify_evidence, table, ev, test=False, lock=td, git=node_git(),
             spec_path=world["sp"])
        out = A.verify_evidence(table, ev, test=True, lock=lock_for(world, "traindev", "test"), git=node_git(),
                                spec_path=world["sp"])
        assert out["completion"]["evaluation_block_sha256"] == G.L._sha_file(ev / "evaluation_block.jsonl")
    assert release_checks.INTEGRITY_CHECKS["g5"] is release_checks.g5_integrity
    assert R.SOURCES["g5"] == "T1"


def _git_stub(*, differs=0, dirty=""):
    calls = []

    def git(repo, *args):
        calls.append(args)
        if args[0] == "diff":
            return subprocess.CompletedProcess(args, differs, "", "")
        return subprocess.CompletedProcess(args, 0, dirty, "")
    return git, calls


def test_registered_check_refuses_unpublished_g5_code(monkeypatch):
    """Review B1: the 'differs' and 'dirty' conditions are made on purpose (the git calls are stubbed), so the test
    does not depend on this branch differing from origin/main; each refuses before anything is imported or read."""
    for kw, what in (({"differs": 1}, "differs"), ({"dirty": " M sweep2/t1_tasl/g5_job.py"}, "dirty")):
        git, calls = _git_stub(**kw)
        monkeypatch.setattr(release_checks, "_g5_git", git)
        with pytest.raises(ValueError, match="differs from origin/main or is modified"):
            release_checks.g5_integrity(Path("/nonexistent/table"), Path("/nonexistent/audit"))
        assert calls and all(set(release_checks.G5_PATHS) <= set(c) for c in calls)
    assert "sweep2/s2_c2_lib.py" in release_checks.G5_PATHS                        # review m4


def test_registered_check_on_a_published_checkout_runs_verify_evidence(monkeypatch):
    """Review B1: on a published checkout the check goes on to ``g5_assemble.verify_evidence`` (stubbed), inside the
    integrity context, with the stage from ``release.test_released('T1')``; the derived module paths are checked too."""
    git, calls = _git_stub()
    monkeypatch.setattr(release_checks, "_g5_git", git)
    monkeypatch.setattr(R, "test_released", lambda tier="T0", root=None: False)
    seen = {}

    def fake_verify(table, audit, *, test):
        seen.update(table=table, test=test, context=SE.in_integrity_context())
        return {"check": "g5_assemble.verify_evidence", "pass": True, "stage": "traindev", "completion_sha256": "c" * 64,
                "completion": {"schema": A.COMPLETION_SCHEMA, "label_block_sha256": "l" * 64, "secret": "x"}}
    monkeypatch.setattr(A, "verify_evidence", fake_verify)
    out = release_checks.g5_integrity(Path("/t"), Path("/a"))
    assert out["pass"] and out["completion"] == {"schema": A.COMPLETION_SCHEMA, "label_block_sha256": "l" * 64}
    assert seen == {"table": Path("/t"), "test": False, "context": True}
    derived = calls[-2]                                                # the second check: the module files by name
    assert "sweep2/t1_tasl/g5_assemble.py" in derived and "sweep2/s2_c2_lib.py" in derived
    assert "sweep2/t1_tasl/g5_tasl_spec.json" in derived


def test_table_fits_the_release_step_and_the_frozen_builder(world):
    """The T1 table and blocks have the shapes ``r1.c3.release`` partitions and ``gate_input_builder.build`` takes:
    proposal ids carry the P3 instance, every label row names its node, and the frozen builder builds a gate input
    from them (T1 only, the empty T0 node set of gate v3.1)."""
    from r1.c3 import gate_input_builder as B, p3_split
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s, divergent_label={"S12_6"}, divergent_eval={"S13_7"}))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()]
    labels = [json.loads(x) for x in (ev / "label_block.jsonl").read_text().splitlines()]
    evals = [json.loads(x) for x in (ev / "evaluation_block.jsonl").read_text().splitlines()]
    assign = p3_split.assignment(p3_split.load())
    for r in rows:
        inst = p3_split.instance_id(r["node"], r["instance_seed"])
        assert inst in assign and R._instance_of_pid(r["proposal_id"]) == inst
    splits = {assign[R._instance_of_pid(l["proposal_id"])]["split"] for l in labels}
    assert splits == {"train", "dev", "test"} and all(l["node"] == NODE for l in labels + evals)
    preds = {r["proposal_id"]: [1 / 12] * 12 for r in rows if not r["noop"]}
    gate_input, report = B.build([B.Source("g5", rows, labels, evals)], {"A3": preds, "A5": preds},
                                 {NODE: {"delta_n": 0.003, "sigma_node": SIGMA}}, t0_nodes=[],
                                 t1=B.Tier1(suites={NODE: "MLAgentBench"}, modes=("history",)))
    node = gate_input["nodes"][0]
    assert node["node"] == NODE and node["tier"] == "T1"
    assert [len(node[sp]["instance_ids"]) for sp in ("train", "dev", "test")] == [4, 2, 6]
    assert report["nodes"][NODE]["label_divergent"] > 0 and report["nodes"][NODE]["evaluation_divergent"] > 0


# =============================================================================================== REL-T1-G1B copy
def sealed_g1b_run(root: Path, kind="seven"):
    """A synthetic gated, joined G.1b run directory under a sealed root."""
    d = root / ("g1b-tasl-20261121-b" if kind == "seven" else "g1b-ar-tasl-20261122-a") / "_assembled"
    d.mkdir(parents=True)
    (d / "runs.jsonl").write_text('{"node": "x"}\n')
    schema = G.ASSEMBLY_SCHEMA if kind == "seven" else G.AR_ASSEMBLY_SCHEMA
    run_id = RC.KINDS[kind][1]
    (d / "ASSEMBLY.json").write_text(json.dumps({"schema": schema, "run_id": run_id,
                                                 "runs_sha256": G.L._sha_file(d / "runs.jsonl")}))
    nodes = RC.KINDS[kind][2]
    summary = {"schema": RC.KINDS[kind][0], "label": G.ENGINEERING_ONLY, "run_id": run_id,
               "assembly_sha256": G.L._sha_file(d / "ASSEMBLY.json"),
               "verdicts": {n: {"qualifies_D21": True, "sigma_joint": 0.01} for n in nodes}}
    (d / "summary.json").write_text(json.dumps(summary))
    if kind == "seven":
        xs = SPEC["noise_floor"]["seven"]["crosscheck_spec"]
        xc = json.loads((ROOT / xs["path"]).read_text())
        gate = {"schema": "g1b_tasl_crosscheck_gate/1", "rule": "R1-T1-TASL-ENV",
                "nodes": {n: {"verdict": "v"} for n in xc["nodes"]}, "g1b_spec_sha256": xc["g1b_spec"]["sha256"],
                "crosscheck_run_id": xc["run_id"], "assembly_json_sha256": G.L._sha_file(d / "ASSEMBLY.json"),
                "runs_jsonl_sha256": G.L._sha_file(d / "runs.jsonl")}
        (d / "crosscheck_gate.json").write_text(json.dumps(gate, indent=1, sort_keys=True) + "\n")
    return d / "summary.json"


def test_rel_t1_g1b_copy_seven_passes_the_switch_check(tmp_path, monkeypatch):
    sealed = tmp_path / "sealed_g1b"
    monkeypatch.setattr(RC, "_sealed_roots", lambda spec, fam: {sealed.resolve()})
    summary = sealed_g1b_run(sealed)
    repo = tmp_path / "repo"
    rec = RC.copy_summary(SPEC, "seven", summary, "docs/r1/reports/g5_rel_t1_g1b_20261201/seven", repo=repo)
    assert (repo / rec["copy"]).read_bytes() == summary.read_bytes()
    assert (repo / rec["gate_copy"]).read_bytes() == (summary.parent / "crosscheck_gate.json").read_bytes()
    stop("written once", RC.copy_summary, SPEC, "seven", summary, "docs/r1/reports/g5_rel_t1_g1b_20261201/seven",
         repo=repo)
    # 3a's switch check accepts the copy as filled into the spec, once committed with an accepted review
    s = copy.deepcopy(SPEC)
    s["noise_floor"]["seven"].update({k.split(".")[-1]: v for k, v in rec["spec_fields"].items()},
                                     review="docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md")
    review = ("\n".join(rec["review_must_name"]) + "\nVerdict: ACCEPTED\n").encode()
    files = {rec["copy"]: (repo / rec["copy"]).read_bytes(), rec["gate_copy"]: (repo / rec["gate_copy"]).read_bytes(),
             "docs/r1/reviews/REL_T1_G1B_COPY_REVIEW.md": review}
    got = S.check_seven_copy(s, files.get)
    assert got["qualifies_D21"] == {n: True for n in S.SEVEN}


def test_rel_t1_g1b_copy_refusals_and_ar(tmp_path, monkeypatch):
    sealed = tmp_path / "sealed_g1b"
    monkeypatch.setattr(RC, "_sealed_roots", lambda spec, fam: {sealed.resolve()})
    outside = sealed_g1b_run(tmp_path / "elsewhere")
    stop("not in the sealed G.1b tree", RC.check_source, SPEC, "seven", outside)
    summary = sealed_g1b_run(sealed)
    gate = json.loads((summary.parent / "crosscheck_gate.json").read_text())
    (summary.parent / "crosscheck_gate.json").write_text(json.dumps(gate | {"runs_jsonl_sha256": "0" * 64}))
    stop("runs_jsonl_sha256", RC.check_source, SPEC, "seven", summary)
    (summary.parent / "crosscheck_gate.json").unlink()
    stop("no crosscheck_gate.json", RC.check_source, SPEC, "seven", summary)
    stop("dest must be", RC.copy_summary, SPEC, "seven", summary, "../escape", repo=tmp_path / "repo")
    ar = sealed_g1b_run(sealed, "ar")
    stop("is not the g1b_tasl_summary/1", RC.check_source, SPEC, "seven", ar)
    rec = RC.copy_summary(SPEC, "ar", ar, "docs/r1/reports/g5_rel_t1_g1b_20261201/ar", repo=tmp_path / "repo")
    for line in rec["completion_record_lines"]:                    # the completion record's '<path> sha256 <hex>'
        key, val = line.split(": ", 1)
        assert S.CITED.fullmatch(val) and key in ("noise_floor_copy", "g1b_sealed_summary")
    assert rec["d21_verdict"] == {S.AR: "qualifies"}


# =============================================================================================== the CLI gates
def test_cli_commands_are_behind_the_gates(tmp_path, capsys):
    """The draft spec is unsigned: every seal and assembly command refuses at the launch validation; the copy step
    (before the signature) validates without launch and then refuses the missing summary."""
    sp = str(ROOT / "sweep2" / "t1_tasl" / "g5_tasl_spec.json")
    for argv in (["seal-attempt", sp, str(tmp_path)], ["seal-node", sp, "--node", NODE], ["seal-run", sp],
                 ["seal-server", sp, str(tmp_path)], ["server-span", sp, str(tmp_path / "r.json")],
                 ["assemble", sp, "--stage", "traindev", "--table", str(tmp_path / "t"), "--evidence",
                  str(tmp_path / "e")]):
        assert S.main(argv) == 2
        assert capsys.readouterr().err.startswith("STOP: ")         # the launch validation of the unsigned spec
    assert S.main(["rel-copy", sp, "--kind", "seven", "--summary", str(tmp_path / "none.json"), "--dest",
                   "docs/r1/reports/x/seven"]) == 2
    assert "is not a file" in capsys.readouterr().err                # validated without launch, then the copy
    assert not (tmp_path / "t").exists()


def test_spec_names_the_proposer_sealed_root():
    assert S.validate_spec(SPEC)["options"]["G5-TASL-GPUH"] == "A"
    for bad in (SPEC["proposer"]["run_dir"], SPEC["proposer"]["run_dir"] + "/sealed", "relative/path"):
        s = copy.deepcopy(SPEC)
        s["proposer"]["sealed_root"] = bad
        stop("proposer.sealed_root", S.validate_spec, s)


# =============================================================================================== review round 1
def test_partial_seals_and_tampered_receipts(world, monkeypatch):
    """Review m1/m2: a seal interrupted after its directory exists leaves only ``<target>.partial`` and a re-run STOPs
    (the target is never half-written); a tampered receipt is a STOP."""
    s = world["spec"]
    run_node(world, Engine(s))
    attempts = SE._node_attempts(s, NODE)
    real = SE._write_receipt

    def crash(*a, **kw):
        raise RuntimeError("power cut")
    monkeypatch.setattr(SE, "_write_receipt", crash)
    with pytest.raises(RuntimeError):
        SE.seal_attempt(s, attempts[0])
    target = SE.sealed_attempt_of(s, attempts[0])
    assert SE.partial_of(target).is_dir() and not target.exists()
    monkeypatch.setattr(SE, "_write_receipt", real)
    stop("interrupted seal", SE.seal_attempt, s, attempts[0])
    SE.partial_of(target).rename(world["tmp"] / "moved_aside")          # the operator's action after inspection
    SE.seal_attempt(s, attempts[0])
    for a in attempts[1:]:
        SE.seal_attempt(s, a)
    monkeypatch.setattr(SE, "_write_receipt", crash)                    # a partial seal_node
    with pytest.raises(RuntimeError):
        SE.seal_node(s, NODE)
    monkeypatch.setattr(SE, "_write_receipt", real)
    stop("interrupted seal", SE.seal_node, s, NODE)
    assert not (SE.sealed_run(s) / NODE / "_node").exists()
    rp = target / SE.RECEIPT
    receipt = json.loads(rp.read_text())
    rp.write_text(json.dumps(receipt | {"files": receipt["files"] | {"out.tar": "0" * 64}}))
    stop("differs from its seal receipt", SE.verify_sealed, target)
    rp.write_text(json.dumps(receipt | {"sealed_path": "/elsewhere"}))
    stop("names another sealed path", SE.verify_sealed, target)


def test_tar_members_are_checked_by_sha256(tmp_path, monkeypatch):
    """Review m3: a tar whose member names match but whose content differs from the source is a STOP (before any
    source is removed)."""
    src = tmp_path / "a" / "out"
    src.mkdir(parents=True)
    (src / "ledger.jsonl").write_text("the real bytes\n")
    assert SE._tar_dir(src.parent, "out", tmp_path / "ok.tar") == 1
    other = tmp_path / "b" / "out"
    other.mkdir(parents=True)
    (other / "ledger.jsonl").write_text("other bytes\n")
    real_run = subprocess.run

    def wrong_tar(argv, **kw):
        if argv[0] == "tar":
            argv = [argv[0], argv[1], argv[2], "-C", str(other.parent), "out"]
        return real_run(argv, **kw)
    monkeypatch.setattr(SE.subprocess, "run", wrong_tar)
    stop("with their sha256", SE._tar_dir, src.parent, "out", tmp_path / "bad.tar")
    assert (src / "ledger.jsonl").is_file()


def test_close_server_then_seal(world, monkeypatch):
    """Review M3: a server that ended without server_end.json is closed, guarded like close-attempt, with the closing
    time as its end (the log's latest mtime beside it), and can then be sealed."""
    import socket
    s = world["spec"]
    d = make_server_dir(world)
    os.utime(d / "llama-server.log", (SE.parse_utc("2026-12-01T03:00:00Z"),) * 2)
    stop("is not TASL-7|not .*close the server there", SE.close_server, s, d, "the serve wrapper was OOM-killed",
         alive=lambda pid: False, scan=lambda p: [])
    here = copy.deepcopy(s)
    here["proposer"]["hostname"] = socket.gethostname()
    stop("reason", SE.close_server, here, d, "short", alive=lambda pid: False, scan=lambda p: [])
    stop("still alive", SE.close_server, here, d, "the serve wrapper was OOM-killed", alive=lambda pid: True,
         scan=lambda p: [])
    stop("still name", SE.close_server, here, d, "the serve wrapper was OOM-killed", alive=lambda pid: False,
         scan=lambda p: [1234])
    closed_at = SE.parse_utc("2026-12-01T09:00:00Z")
    end = SE.close_server(here, d, "the serve wrapper was OOM-killed", alive=lambda pid: False, scan=lambda p: [],
                          now=lambda: closed_at)
    assert end["closed"] and end["stopped_utc"] == "2026-12-01T09:00:00Z"
    assert end["latest_log_mtime_utc"] == "2026-12-01T03:00:00Z"
    stop("server_end.json already", SE.close_server, here, d, "the serve wrapper was OOM-killed",
         alive=lambda pid: False, scan=lambda p: [])
    r = SE.seal_server(s, d, alive=lambda pid: False)
    assert r["closed"] and r["span_seconds"] == 9 * 3600.0 and not (d / "llama-server.log").exists()


def test_span_gaps_count_as_open(world, tmp_path):
    """Review m5: servers are numbered server-1..N; a gap in the registered numbers is an unknown span, counted open
    until now, and an audit job under B refuses until it is registered."""
    s = world["spec"]
    for n in (1, 2):
        d = make_server_dir(world, n)
        end_server(d)
        SE.seal_server(s, d, alive=lambda pid: False)
    r2 = tmp_path / "r2.json"
    r2.write_bytes((SE.proposer_sealed_run(s) / "server-2" / SE.RECEIPT).read_bytes())
    SE.register_server_span(s, r2)
    assert SE.span_gaps(s) == [1]
    stop("server number", SE.require_server_spans, s)
    t0 = SE.parse_utc("2026-12-01T00:00:00Z")
    got = SE.proposer_seconds(s, now=lambda: t0 + 10 * 3600)
    assert got["gaps"] == [1] and got["seconds"] == 5 * 3600 + 10 * 3600   # server-2's span + the gap open since t0
    r1 = tmp_path / "r1.json"
    r1.write_bytes((SE.proposer_sealed_run(s) / "server-1" / SE.RECEIPT).read_bytes())
    SE.register_server_span(s, r1)
    assert SE.span_gaps(s) == [] and SE.require_server_spans(s)["registered"] == 2
    assert SE.proposer_seconds(s, now=lambda: t0 + 99 * 3600)["seconds"] == 10 * 3600


def test_tasl7_access_log_is_stop_11(world):
    """Review m6: TASL-7's sealed access log is checked (STOP 11) before every seal and every log opening there."""
    s = world["spec"]
    d = make_server_dir(world)
    end_server(d)
    SE.seal_server(s, d, alive=lambda pid: False)
    both = lock_for(world, "traindev", "test")
    SE.open_server_log(s, "server-1", "server log: diagnosis", lock=both)
    entry = SE.check_access_log(s, root=SE.proposer_sealed_run(s))[0]
    assert entry["what"] == "server_log" and entry["members"] == ["server-1/llama-server.log"]
    with (SE.proposer_sealed_run(s) / SE.ACCESS_LOG).open("a") as fh:
        fh.write(json.dumps(entry | {"who": "someone"}) + "\n")
    stop("STOP 11", SE.open_server_log, s, "server-1", "server log: again", lock=both)
    d2 = make_server_dir(world, 2)
    end_server(d2)
    stop("STOP 11", SE.seal_server, s, d2, alive=lambda pid: False)


def test_note_carries_the_table_readings_and_server_log_lines():
    """Review M2: the readings and the server-log handling are note lines the author signs; the choice is one of the
    three options, and option (b) of the server log is refused as not built."""
    lines = S.note_lines(SPEC)
    assert lines["t1_table_readings"] == S.table_readings_line(SPEC)
    assert lines["t1_table_readings"].endswith("; campaign-divergent delta_hat: refuse")
    assert all(v in lines["t1_table_readings"] for v in S.TABLE_READINGS.values())
    assert lines["server_log"].startswith("(a) sealed per server at its stop")
    for choice in S.DELTA_HAT_OPTIONS:
        s = copy.deepcopy(SPEC)
        s["key_values"]["t1_table_readings"]["campaign_divergent_delta_hat"] = choice
        S.validate_spec(s)
        assert A.CHOICE.search(S.table_readings_line(s)).group(1) == choice
    s = copy.deepcopy(SPEC)
    s["key_values"]["t1_table_readings"]["campaign_divergent_delta_hat"] = "zero"
    stop("t1_table_readings", S.validate_spec, s)
    s = copy.deepcopy(SPEC)
    s["key_values"]["server_log"] = "b"
    stop("not built", S.validate_spec, s)


# =============================================================================================== G.5 follow-ups
def test_followup_reduce_rows_refuses_a_gate_refused_row():
    """g5_seal.reduce_rows goes through g5_job.read_rows, so a row the engine's gate refused on log_intact,
    parent_traced_by or parent_dumpable_at_accept, or any row carrying gate_refusal, is STOP 2 there too."""
    plan = J.audit_plan(SPEC, NODE, 1, {"instance_1_history": campaign_ledger(1, 1)[:4]}, k=10)
    chunk = J.audit_chunk_file(SPEC, S.node_entry(SPEC, NODE), plan, 0, J.chunk_plan(plan, {"run_seconds": 1})[0],
                               interpreter="/py", cgroup_parent="/cg", deadline_epoch=1.0)
    state = {u["unit"]: u["code_state_sha256"] for u in chunk["units"]}
    rows = [{"schema": J.ROW_SCHEMA, "unit": r["unit"], "seed": r["seed"], "executed": True,
             "code_state_sha256": state[r["unit"]], "outcome": {"kind": "ok", "value": 0.5},
             "isolation": dict(ISOLATED)} for r in chunk["runs"]]
    assert SE.reduce_rows(SPEC, [json.dumps(r) for r in rows], chunk, "traindev")["rows"]
    for change in ({"isolation": dict(ISOLATED, log_intact=False)},
                   {"isolation": dict(ISOLATED, parent_traced_by=99)},
                   {"isolation": dict(ISOLATED, parent_dumpable_at_accept=True)},
                   {"gate_refusal": "not effectively isolated", "outcome": {"kind": "divergent", "reason": "x"}}):
        stop("STOP 2", SE.reduce_rows, SPEC, [json.dumps(rows[0] | change)] + [json.dumps(r) for r in rows[1:]],
             chunk, "traindev")


def test_followup_seal_takes_out_kept_after_a_deadline_with_left_processes(world):
    """When ar_* run cgroups still hold processes after the deadline kill, the job keeps out/ untarred (node STOP 9);
    the seal takes it as out_clear.tar like any out/ left in clear."""
    s = world["spec"]

    def timeout(argv, **kw):
        out = Path(argv[argv.index("--out") + 1])
        (out / "instance_1_history").mkdir(parents=True)
        (out / "instance_1_history" / "campaign_ledger.jsonl").write_text("{}\n")
        raise subprocess.TimeoutExpired(argv, 1, output="o", stderr="e")
    stop("still hold processes", J.run_job, world["sp"], NODE, "campaigns-wave1", {"K": 10}, smi=world["smi"],
         engine=timeout, setup=lambda h, n, b, o: {"data_root": "/d"}, get=Server(), git=world["git"],
         server_record=world["srv"], kill_cgroups=lambda parent: {"left": ["ar_x"]})
    att = J.job_dir(s, NODE, "campaigns-wave1") / "attempt-1"
    assert (att / "out").is_dir() and not (att / "out.tar").exists()
    rec = SE.seal_attempt(s, att)
    assert rec["stop_class"] == "node" and rec["out_clear_files"] >= 3 and not (att / "out").exists()
    with tarfile.open(SE.sealed_attempt_of(s, att) / "out_clear.tar") as tar:
        names = {m.name for m in tar}
    assert any(n.endswith("run_cgroups_kill.json") for n in names)
    assert any(n.endswith("campaign_ledger.jsonl") for n in names)
