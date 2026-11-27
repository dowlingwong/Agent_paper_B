"""Synthetic tests for the S9 expansion switch, CPU admission and assembly."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from r1.c3 import p3_split

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2/t1_tasl"))
import g5_addendum as A  # noqa: E402
import g5_assemble as AS  # noqa: E402
import g5_job as J  # noqa: E402
import g5_seal as SE  # noqa: E402
import g5_tasl as S  # noqa: E402

BASE = "c3_t1_labels_20261127"
RUN = BASE + "_addendum_1"
BASE_SPEC = "sweep2/t1_tasl/g5_tasl_spec.json"
BASE_NOTE = f"{S.NOTE_DIR}/{BASE}.md"
ADD_NOTE = f"{S.NOTE_DIR}/{RUN}.md"
K = {"_K": 10, "_K_row": None, "_freeze": "2027-12-31"}
G1B = json.loads((ROOT / A.G1B_SPEC).read_text())
MLGYM = "mlgym_metamaze"
EXTRA = "gc7rc_forestcover"


@pytest.mark.parametrize(("node", "cpus", "mode", "env"), [
    ("mlgym_titanic", "12-15", "harness_list", "torch312"),
    (MLGYM, "0-3", "census_override", "venv_jax"),
    ("gc7rc_etth1", "16-31", "census_override", "torch312"),
    (EXTRA, "4-7", "census_override", "torch312"),
])
def test_census_deployment(node, cpus, mode, env):
    deploy = A.deployment(G1B, node)
    assert (deploy["node"]["cpus"], deploy["node"]["cpu_only"], deploy["node"]["env"]) == (cpus, mode, env)
    assert deploy["lease"] == f"~/r1_locks/cpus-{cpus}.lock"
    assert deploy["environment"]["freeze_tool"] == ("pip" if env == "venv_jax" else "uv")
    assert J.node_timeout_basis(deploy["node"]) == max(A.G.node_entry(G1B, node)["census_seconds"].values())
    assert J.TIMEOUT_FACTOR == 3


def test_incompatible_placement_refused():
    spec = json.loads(json.dumps(G1B))
    next(n for n in spec["nodes"] if n["node"] == MLGYM)["cpus"] = "8-11"
    with pytest.raises(S.Stop, match="8.11"):
        A.deployment(spec, MLGYM)


@pytest.mark.parametrize("command, flag", [("campaign", "--campaign"), ("audit", "--chunk")])
def test_cpu_override_reaches_engine_only_for_the_declared_node(tmp_path, command, flag):
    module = tmp_path / "autoresearch/trackg"
    module.mkdir(parents=True)
    (module / "noise_floor.py").write_text("CPU_ONLY_NODES = {'mlgym_titanic'}\n")
    (module / "audit_g5.py").write_text(
        "from autoresearch.trackg.noise_floor import CPU_ONLY_NODES\n"
        "def main(argv):\n"
        "    assert argv[0] in {'campaign', 'audit'}\n"
        "    assert CPU_ONLY_NODES == {'mlgym_titanic', 'mlgym_metamaze'}\n"
        "    print('engine entered')\n"
        "    return 0\n"
    )
    infile = tmp_path / "input.json"
    args = [sys.executable, "-c", J.CPU_ONLY_ENGINE, MLGYM, command, flag, str(infile)]
    infile.write_text(json.dumps({"node": MLGYM}))
    passed = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert passed.returncode == 0 and passed.stdout == "engine entered\n", passed.stderr
    refused = subprocess.run([*args, "--gpu-uuid", "GPU-fixture"], cwd=tmp_path, capture_output=True, text=True)
    assert refused.returncode != 0 and "invalid CPU-only" in refused.stderr
    infile.write_text(json.dumps({"node": EXTRA}))
    refused = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert refused.returncode != 0 and "names another node" in refused.stderr


def test_successful_expansion_receipt_matches_exact_assembly():
    pin, canonical = "a" * 64, "c" * 64
    receipt = {"schema": A.G.RECEIPT_SCHEMA, "node": MLGYM, "host": S.WORKER_HOST, "run_id": "g1b-x-fixture",
               "attempt": 1, "job_record_sha256": "b" * 64, "sealed_path": "/test/attempt-1"}
    job = dict(receipt, spec_sha256=pin, sealed=receipt["sealed_path"], device="cpu")
    assembly = {"schema": A.G.X_ASSEMBLY_SCHEMA, "run_id": receipt["run_id"], "spec_json_sha256": canonical, "jobs": [job]}
    A._receipt(receipt, assembly, MLGYM, receipt["run_id"], pin, canonical)
    with pytest.raises(S.Stop, match="no successful"):
        A._receipt(dict(receipt, stop="synthetic failure"), assembly, MLGYM, receipt["run_id"], pin, canonical)
    with pytest.raises(S.Stop, match="different attempts"):
        A._receipt(dict(receipt, attempt=2), assembly, MLGYM, receipt["run_id"], pin, canonical)
    with pytest.raises(S.Stop, match="published G.1b spec/run"):
        A._receipt(receipt, dict(assembly, jobs=[]), MLGYM, receipt["run_id"], pin, canonical)


def test_published_g1b_engineering_receipts_bind_raw_and_canonical_digests():
    directory = ROOT / "docs/r1/reports/g1b_x_20261127"
    assembly = json.loads((directory / "ASSEMBLY.json").read_bytes())
    raw = S._sha_bytes((ROOT / A.G1B_SPEC).read_bytes())
    canonical = S._sha_bytes(json.dumps(G1B, sort_keys=True).encode())
    assert raw != canonical
    for node in G1B["nodes"]:
        name = node["node"]
        stem = "titanic" if name == "mlgym_titanic" else name
        receipt = json.loads((directory / f"SEAL_RECEIPT_{stem}.json").read_bytes())
        A._receipt(receipt, assembly, name, G1B["run_id"], raw, canonical)


@pytest.fixture
def filled(tmp_path, monkeypatch):
    """Bind synthetic publication metadata. Base G.5, G.1b and PRE-SPLIT each have dedicated checker tests."""
    base = json.loads((ROOT / BASE_SPEC).read_bytes())
    base.update(run_id=BASE, paper=dict(base["paper"], commit="a" * 40))
    files = {BASE_SPEC: json.dumps(base).encode(), BASE_NOTE: b"approved: true\n"}
    isolation = "docs/r1/reports/host.md"
    context = {"host_check_host": base["worker"]["hostname"], "host_check_harness_commit": "b" * 40,
               "host_check_items": "1-7 PASS", "host_check_verdict": "PASS"}
    files[isolation] = "".join(f"{key}: {value}\n" for key, value in context.items()).encode()
    amendment = A.release.SPLIT_AMENDMENT_PATH
    files[amendment] = b"synthetic PRE-SPLIT amendment\n"
    files["docs/r1/PLAN.md"] = (ROOT / "docs/r1/PLAN.md").read_bytes().replace(
        b"## 11. Relation to Paper A",
        b"### 27 November 2026 (fixture) (author)\n\n| ID | Decision |\n|---|---|\n"
        b"| R1-G5-TEST-P10 | mlgym_metamaze gaussian |\n\n## 11. Relation to Paper A")
    citation = lambda path: f"{path} sha256 {S._sha_bytes(files[path])}"
    config = {"schema": A.SCHEMA, "run_id": RUN, "node": MLGYM, "supply": p3_split.role_of(MLGYM),
              "paper": dict(base["paper"], commit="c" * 40), "base_g5_spec": citation(BASE_SPEC),
              "base_g5_note": citation(BASE_NOTE), "pre_split_amendment": citation(amendment),
              "g1b_note": "fixture", "g1b_spec": "fixture", "g1b_receipt": "fixture", "g1b_copy": {},
              "instance_split": dict(p3_split.SPLIT_FILES[2]), "tail": {"tails": "gaussian", "authority": "R1-G5-TEST-P10"},
              "harness": {"g1b_pin": A.deployment(G1B, MLGYM)["harness_pin"], "g5_commit": "b" * 40,
                          "harness_dir": "/test/addendum-harness",
                          "isolation_host_check": {"record": isolation, "sha256": S._sha_bytes(files[isolation])}}}
    for path in (BASE_SPEC, BASE_NOTE):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(files[path])
    monkeypatch.setattr(S, "validate_spec", lambda *a, **kw: {})
    monkeypatch.setattr(S, "check_note", lambda *a, **kw: K)
    monkeypatch.setattr(A.release, "split_v2_amendment", lambda root: {
        "path": amendment, "sha256": S._sha_bytes(files[amendment])})
    monkeypatch.setattr(A, "_g1b", lambda config, name, root, read_main: (A.deployment(G1B, name), {}))
    spec_path = tmp_path / "addendum.json"
    note_path = tmp_path / ADD_NOTE

    def render(*, approved="true", publish=True, fields=None):
        spec_path.write_text(json.dumps(config))
        bind = {key: config[key] for key in ("run_id", "node", "base_g5_note", "base_g5_spec", "pre_split_amendment", "supply")}
        sha = S._sha_bytes(spec_path.read_bytes())
        review = "docs/r1/reviews/addendum.md"
        files[review] = f"Verdict: ACCEPTED\n{RUN} {sha} {config['paper']['commit']}\n".encode()
        bind.update(approved=approved, paper_commit=config["paper"]["commit"], spec_sha256=sha, review=citation(review),
                    instance_split=f"r1/c3/splits/c3_p3_split_v2.json sha256 {p3_split.P3_SPLIT_V2_SHA256}")
        bind.update(fields or {})
        note_path.write_text("".join(f"{key}: {value}\n" for key, value in bind.items()))
        if publish:
            files[ADD_NOTE] = note_path.read_bytes()
        else:
            files.pop(ADD_NOTE, None)
        return A.bind(spec_path, note_path, root=tmp_path, read_main=files.get)

    return config, base, render


def test_addendum_uses_own_pin_and_inherits_settings(filled):
    config, base, render = filled
    spec = render()
    assert spec["paper"] == config["paper"] and spec["run_id"] == RUN
    for key in ("campaign", "memory", "audit", "key_values", "decisions", "proposer"):
        assert spec[key] == base[key]
    assert spec["_addendum"]["_K"] == 10
    assert spec["nodes"][0]["env"] == "venv_jax"


@pytest.mark.parametrize(("kwargs", "match"), [
    ({"publish": False}, "byte-identical"),
    ({"approved": "false"}, "approved"),
    ({"fields": {"paper_commit": "d" * 40}}, "exact spec fields"),
])
def test_addendum_approval_and_launch_digest(filled, kwargs, match):
    with pytest.raises(S.Stop, match=match):
        filled[2](**kwargs)


@pytest.mark.parametrize(("field", "value", "match"), [
    ("supply", "g5_addendum_extra_task", "S9 role"),
    ("instance_split", p3_split.SPLIT_FILES[1], "exact P3 split v2"),
    ("harness", {"g1b_pin": "d" * 40}, "needs the kit pin"),
])
def test_addendum_refuses_wrong_binding(filled, field, value, match):
    config, _, render = filled
    config[field] = value
    with pytest.raises(S.Stop, match=match):
        render()


def test_attempt_is_bound_to_exact_note_spec_and_run(filled, tmp_path):
    spec = filled[2]()
    spec["worker"]["runs_root"] = str(tmp_path / "runs")
    attempt = SE.run_root(spec) / MLGYM / "campaigns-wave1" / "attempt-1"
    attempt.mkdir(parents=True)
    record = {"schema": J.RECORD_SCHEMA, "label": S.EVIDENCE, "node": MLGYM, "run_id": RUN,
              "job": "campaigns-wave1", "chunk": None, "attempt": 1, "spec_sha256": "a" * 64,
              "addendum_note_sha256": spec["_addendum"]["note_sha256"]}
    (attempt / "job_record.json").write_text(json.dumps(record))
    with pytest.raises(S.Stop, match="another G.5 addendum spec, note or run"):
        SE.seal_attempt(spec, attempt)
    with pytest.raises(S.Stop, match="another G.5 addendum spec, note or run"):
        SE.addendum_binding(spec, {**SE.addendum_binding(spec), "run_id": BASE})


def test_release_routes_mlgym_to_primary_and_1gc_to_own_output(tmp_path, monkeypatch):
    base = {"run_id": BASE, "key_values": {"t1_table_readings": {"campaign_divergent_delta_hat": "refuse"}}}
    row = {"split_sha256": p3_split.P3_SPLIT_V2_SHA256, "row_id": "synthetic", "decision_sha256": "s",
           "g1b_summaries": {n: {} for n in ("mlgym_fmnist", MLGYM, EXTRA)}}
    addenda = {n: {"run_id": f"{BASE}_addendum_{i}", "_addendum": {
        **K, "note": f"{n}.md", "note_sha256": "a" * 64, "base_note": BASE_NOTE, "role": p3_split.role_of(n)},
        **{k: v for k, v in base.items() if k != "run_id"}} for i, n in enumerate((MLGYM, EXTRA), 1)}
    bindings = {n: {"spec_path": f"{n}.json", "spec_sha256": "a" * 64, "role": p3_split.role_of(n)} for n in addenda}
    calls = []

    def derive(spec, sha, stage, tree, filtered, **kwargs):
        name, = filtered["g1b_summaries"]
        calls.append((name, stage))
        suite = None if name == EXTRA else "MLGym"
        row_bytes = AS._lines([{"proposal_id": name}])
        build = {"schema": AS.TABLE_SCHEMA, "source": "g5", "spec_sha256": sha,
                 "readings": {"note": BASE_NOTE}, "proposals_sha256": S._sha_bytes(row_bytes)}
        return {"build": json.dumps(build).encode(), "K": 10, "seeds": {"label": [7001], "evaluation": [7006]},
                "nodes": {name: {"counts": {}, "gate_suite": suite}}, "proposals": row_bytes,
                "label_block": row_bytes, "evaluation_block": row_bytes, "eval_counts": {name: {}}}

    monkeypatch.setattr(AS, "_addendum_specs", lambda *a, **kw: (addenda, bindings))
    monkeypatch.setattr(AS, "derive", derive)
    monkeypatch.setattr(AS.SE, "SealedTree", lambda *a, **kw: object())
    result, extra = AS._derive_runs(base, "base-sha", "traindev", row, purpose_head="assembly traindev:",
                                    readings={"note": BASE_NOTE}, check=None, git=None, ar_record=None, addendum_paths=[])
    assert set(result["nodes"]) == {"mlgym_fmnist", MLGYM}
    assert set(extra) == {EXTRA} and EXTRA.encode() not in result["label_block"]
    assert json.loads(extra[EXTRA]["build"])["source"] == "g5_extra_task"
    assert [table.relative_to(tmp_path).as_posix() for table, _, _ in
            AS._tables(tmp_path / "table", tmp_path / "evidence", result, extra)] == [
                "table", f"table/extra_tasks/{EXTRA}"]
    assert all(stage == "traindev" for _, stage in calls)
    with pytest.raises(S.Stop, match="same P3 split v2"):
        AS._check_addendum_stage(row, {"split_sha256": p3_split.P3_SPLIT_SHA256}, True)


def test_published_launch_checkout_checks_its_own_parent_and_spec(tmp_path):
    remote, repo = tmp_path / "remote", tmp_path / "checkout"

    def git(directory, *args):
        return subprocess.check_output(["git", "-C", str(directory), *args], text=True).strip()

    def commit(files):
        git(repo, "add", "--", *files)
        git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
        return git(repo, "rev-parse", "HEAD")

    remote.mkdir()
    repo.mkdir()
    git(remote, "init", "-q", "--bare")
    git(repo, "init", "-q")
    git(repo, "remote", "add", "origin", str(remote))
    (repo / "docs/r1").mkdir(parents=True)
    (repo / "docs/r1/PLAN.md").write_text("| R1-G5-S9 | synthetic |\n")
    code = repo / "run.py"
    code.write_text("fixture = 1\n")
    paper = commit(["docs/r1/PLAN.md", "run.py"])
    spec = {"paper": {"commit": paper, "repo": str(remote)}}
    path = repo / "addendum.json"
    path.write_text(json.dumps(spec))
    head = commit([path.name])
    git(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
    git(repo, "fetch", "-q", "origin")
    checked = A.G.verify_launch_tasl(repo, spec, ("R1-G5-S9",), spec_path=path)
    assert (checked["head"], checked["paper_commit"], checked["spec"]) == (head, paper, path.name)
    code.write_text("fixture = 2\n")
    commit(["run.py"])
    git(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
    git(repo, "fetch", "-q", "origin")
    with pytest.raises(S.Stop, match="differs from the paper commit"):
        A.G.verify_launch_tasl(repo, spec, ("R1-G5-S9",), spec_path=path)


def test_switch_uses_full_pilot_and_own_launch_pin(filled, tmp_path, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    config, base, render = filled
    spec = render()
    published_noise = b"synthetic engineering noise summary"
    spec["_addendum"]["noise"] = {"copy": "fixture.json", "scope": {MLGYM: {"d21": False}},
                                  "sha256": S._sha_bytes(published_noise)}
    monkeypatch.setenv(S.ENABLE_ENV, "1")
    monkeypatch.setattr(S, "load_spec", lambda *a, **kw: spec)
    monkeypatch.setattr(S, "plan_row", lambda *a, **kw: "fixture")
    monkeypatch.setattr(S, "noise_precheck", lambda *a, **kw: {})
    monkeypatch.setattr(S, "freeze_wait_check", lambda *a, **kw: {})
    monkeypatch.setattr(J, "check_engines", lambda *a, **kw: {})
    monkeypatch.setattr(S.G, "_sh", lambda *a, **kw: SimpleNamespace(returncode=0))
    seen = []

    def pilot(actual, read_main):
        assert actual == base and [n["node"] for n in actual["nodes"]] == list(S.T1_NODES)
        seen.append("pilot")
        return {"passed": True}

    def bind(repo, bound, rows, *, spec_path):
        assert bound["paper"] == config["paper"] and bound["run_id"] == RUN
        assert spec_path == tmp_path / "addendum.json" and "R1-G5-S9" in rows
        seen.append("pin")
        return {"paper_commit": bound["paper"]["commit"]}

    def run(spec_path, node, job, context):
        assert (node, job, context["K"], context["host"]) == (MLGYM, "campaigns-wave1", 10, S.WORKER_HOST)
        seen.append("runner")
        return {"started": True}

    monkeypatch.setattr(S.G, "verify_launch_tasl", bind)
    got = S.launch(tmp_path / "addendum.json", tmp_path / ADD_NOTE, MLGYM, job="campaigns-wave1",
                   enable=True, today=date(2026, 11, 27), read_main=lambda path: published_noise, pilot_check=pilot,
                   checkout=lambda *a: {}, mpath_check=lambda *a: {"g5_commit": config["harness"]["g5_commit"]},
                   runner=run)
    assert got["started"] and seen == ["pilot", "pin", "runner"]


def test_audit_plan_refuses_foreign_attempt_and_index(filled, tmp_path, monkeypatch):
    spec = filled[2]()
    node = spec["nodes"][0]
    spec["worker"]["runs_root"] = str(tmp_path / "runs")
    camp = J.job_dir(spec, MLGYM, "campaigns-wave1") / "attempt-1"
    camp.mkdir(parents=True)
    (camp / "job_record.json").write_text(json.dumps({"run_id": BASE, "stop": None}))
    (camp / "diagnostics.json").write_text("{}")

    def must_not_open(*args, **kwargs):
        pytest.fail("unbound archive was opened")

    monkeypatch.setattr(J, "tar_members", must_not_open)
    with pytest.raises(S.Stop, match="another G.5 addendum spec, note or run"):
        J.next_chunk(spec, node, 1, 10)
    index = J.plan_path(spec, MLGYM, 1)
    index.parent.mkdir(parents=True)
    index.write_text(json.dumps({"run_id": BASE, "K": 10}))
    monkeypatch.setattr(J, "access", must_not_open)
    with pytest.raises(S.Stop, match="another G.5 addendum spec, note or run"):
        J.next_chunk(spec, node, 1, 10)


def test_gate_noise_uses_only_exact_mlgym_addendum_bindings(tmp_path, monkeypatch):
    from g5_noise import builder_noise, derive

    base = {"run_id": BASE}
    path = tmp_path / "main_spec.json"
    path.write_text(json.dumps(base))
    row = {"split_sha256": p3_split.P3_SPLIT_V2_SHA256,
           "g1b_summaries": {name: {"path": name} for name in ("mlgym_fmnist", MLGYM, EXTRA)}}
    addenda = {MLGYM: {"run_id": RUN}, EXTRA: {"run_id": BASE + "_addendum_2"}}

    def specs(spec, sha, signed, paths):
        assert spec == base and sha == S._sha_bytes(path.read_bytes())
        assert signed == row and paths == ["signed specs"]
        return addenda, {}

    def noise(spec, narrowed, **kwargs):
        name, = narrowed["g1b_summaries"]
        assert name != EXTRA and spec == (base if name == "mlgym_fmnist" else addenda[MLGYM])
        return {name: {"delta_n": 0.25, "sigma_node": 2.0, "sigma_node_t0_definition": 2.0,
                       "sigma_node_rule": AS.N.T1_SIGMA_NODE}}

    monkeypatch.setattr(AS, "_addendum_specs", specs)
    monkeypatch.setattr(AS, "noise_by_node", noise)
    record = derive(base, row, spec_path=path, addendum_paths=["signed specs"])
    assert set(builder_noise(record)) == {"mlgym_fmnist", MLGYM}
    record["nodes"][EXTRA] = record["nodes"][MLGYM]
    with pytest.raises(S.Stop, match="outside the gate noise record"):
        builder_noise(record)
