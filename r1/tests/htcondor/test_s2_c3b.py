"""Synthetic tests for the S2-C3b (g)4 D28-liveness + prompt-length unit (no job, no GPU, no network, no server).

Everything here runs on the local checkout: the pinned sweep-1 records are read from the repository (their SHA-256 is
checked by the unit), the llama-server tokenizer client is exercised through a fake HTTP poster, and the seal step's
C2 delegation is monkeypatched so nothing touches /ceph.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sweep2"))
import s2_c2_lib as c2  # noqa: E402
import s2_c3b_lib as c3b  # noqa: E402
import render_jdl  # noqa: E402

SPEC = json.loads((ROOT / "sweep2" / "spec.c3b.example.json").read_text())
SWEEP1_MANIFEST = ROOT / "results/r1/engineering/liveness_c3_20261027T152425Z/manifest.json"


def spec(**over):
    s = copy.deepcopy(SPEC)
    s.update(over)
    return s


def _write_authorization(tmp_path):
    note = tmp_path / "c3_sweep2_20261116.md"
    note.write_text("run: s2c3b-20261116-a\napproved: true\nlabel: EVIDENCE\n")
    return note


# ------------------------------------------------------------------ spec validation
def test_example_spec_is_engineering_only_and_validates():
    validated = c3b.validate_spec(spec())
    assert validated["label"] == "ENGINEERING_ONLY" and validated["kind"] == "liveness"
    assert validated["seed_check"]["prompt_measurement_disjoint"] is True


@pytest.mark.parametrize("change", [
    lambda s: s.__setitem__("kind", "chunk"),
    lambda s: s.__setitem__("label", "EVIDENCE"),
    lambda s: s.__setitem__("b2_audits", "K=10"),
    lambda s: s["image"].__setitem__(
        "digest", "ghcr.io/dowlingwong/r1-htc-gpu@sha256:" + "0" * 64),
    lambda s: s["image"].__setitem__("llama_server_sha256", "1" * 64),
    lambda s: s["model"].__setitem__("sha256", "0" * 64),
    lambda s: s["model"].__setitem__("alias", "other_model"),
    lambda s: s["paper"].__setitem__("commit", "0" * 40),
    lambda s: s["paper"].__setitem__("evidence_ready", True),
    lambda s: s["harness"].__setitem__("commit", "897d83c8efa364ec2fdd37288241cc42e01d7274"),
    lambda s: s["server"].__setitem__("ctx", 16384),
    lambda s: s["server"].__setitem__("n_gpu_layers", 99),
    lambda s: s["liveness"].__setitem__("memory_mode", "none"),
    lambda s: s["liveness"].__setitem__("min_live_nodes", 4),
    lambda s: s["liveness"].__setitem__("nodes", s["liveness"]["nodes"][:2]),
    lambda s: s["liveness"].__setitem__("transport_max_attempts", 1),
    lambda s: s["requirements"].__setitem__("gpu_device_name", "NVIDIA H200"),
    lambda s: s["requirements"].__setitem__("cpu_model_number", 1),
    lambda s: s["requirements"].__setitem__("requires_etp_ceph", True),
    lambda s: s.__setitem__("walltime_s", 60),
    lambda s: s.__setitem__("request_disk_kb", 0),
    lambda s: s.__setitem__("request_memory_mb", 0),
    lambda s: s.__setitem__("transfer_outputs", ["out.tar"]),
    lambda s: s["prompt_measurement"].__setitem__("variants", ["trial_1"]),
    lambda s: s["prompt_measurement"].__setitem__("max_prompt_tokens_stop", 16384),
    lambda s: s["prompt_measurement"]["sweep1"].__setitem__("liveness_sha256", "0" * 64),
    lambda s: s["prompt_measurement"]["sweep1"].__setitem__("prompt_max_tokens", 999),
])
def test_spec_negatives_stop(change):
    s = spec()
    change(s)
    with pytest.raises(c3b.Stop):
        c3b.validate_spec(s)


def test_evidence_label_never_resolves(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    note = _write_authorization(tmp_path)
    s = spec()
    s["label_source"] = {"authorization": "c3_sweep2_20261116.md",
                         "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    s["paper"]["evidence_ready"] = True
    with pytest.raises(c3b.Stop, match="EVIDENCE"):
        c3b.validate_spec(s)


# ------------------------------------------------------------------ seeds
def test_seed_check_declares_the_d28_reuse_and_prompt_disjointness():
    check = c3b.check_seed_disjointness(spec())
    assert check["policy"] == "sweep1_d28_reuse"
    assert check["liveness_disjoint_from_sweep2_instance_seeds"] is False
    assert check["liveness_overlap_is_the_frozen_d28_reuse"] is True
    assert check["liveness_disjoint_from_audit_seeds"] is True
    assert check["prompt_measurement_disjoint"] is True
    expected_overlap = sorted({c3b.instance_seed(node, k) for node in c3b.LIVENESS_NODES for k in (0, 1)})
    assert check["liveness_overlap_with_sweep2_instance_seeds"] == expected_overlap
    assert check["sweep2_instance_seed_count"] == 90
    assert check["sweep2_instance_seed_universe_sha256"] == c3b.SWEEP2_INSTANCE_SEED_UNIVERSE_SHA256
    assert sorted(check["prompt_measurement_seed_values"]) == sorted(c3b.PROMPT_MEASUREMENT_SEEDS.values())
    assert check["liveness_instance_seeds"] == c3b.liveness_instance_seeds()


def test_seed_universe_is_the_c3_sweep_index_shape():
    index = json.loads((ROOT / c3b.SWEEP1_INDEX_PATH).read_text())
    assert index["instances"] == 18 and index["nodes"] == list(c3b.LIVENESS_NODES)
    assert index["audit"]["seeds"] == list(c3b.RESERVED_AUDIT_SEEDS)
    universe = c3b.sweep2_instance_seed_universe()
    assert set(universe) == {c3b.instance_seed(node, k)
                             for node in c3b.LIVENESS_NODES for k in range(index["instances"])}
    assert len(universe) == 90  # 18 k-values per node but only 10 distinct len-sum offsets over the eight nodes
    assert hashlib.sha256(json.dumps(universe, separators=(",", ":")).encode()).hexdigest() \
        == c3b.SWEEP2_INSTANCE_SEED_UNIVERSE_SHA256


def test_seed_manifest_matches_the_real_sweep1_record():
    manifest = json.loads(SWEEP1_MANIFEST.read_text())
    check = c3b.check_seed_disjointness(spec(), sweep1_manifest=manifest)
    assert check["sweep1_liveness_manifest_matches"] is True


def test_seed_manifest_change_is_a_stop():
    manifest = json.loads(SWEEP1_MANIFEST.read_text())
    manifest["campaigns"][0]["seed"] = 999
    with pytest.raises(c3b.Stop, match="manifest seeds"):
        c3b.check_seed_disjointness(spec(), sweep1_manifest=manifest)


@pytest.mark.parametrize("mutation,match", [
    (lambda s: s["seeds"].__setitem__("liveness_seed_policy", "strict_disjoint"), "not implementable"),
    (lambda s: s["seeds"].__setitem__("liveness_seed_policy", "other"), "liveness_seed_policy"),
    (lambda s: s["seeds"].__setitem__("sweep2_instance_seed_universe_sha256", "0" * 64), "sha256"),
    (lambda s: s["seeds"].__setitem__("sweep2_instance_seed_count", 89), "90 seeds"),
    (lambda s: s["seeds"]["liveness_instance_seeds"].__setitem__("digits_mlp", [104, 124]), "pinned D28 seeds"),
    (lambda s: s["seeds"].__setitem__("reserved_audit_seeds", list(range(7001, 7012))), "reserved_audit_seeds"),
])
def test_seed_negatives_stop(mutation, match):
    s = spec()
    mutation(s)
    with pytest.raises(c3b.Stop, match=match):
        c3b.check_seed_disjointness(s)


@pytest.mark.parametrize("colliding,match", [
    (lambda values: values.__setitem__("digits_mlp", 104), "collide"),
    (lambda values: values.__setitem__("digits_mlp", 7005), "collide"),
    (lambda values: values.__setitem__("digits_mlp", 9201), "collide"),
    (lambda values: values.__setitem__("digits_mlp", 8003), "collide"),
    (lambda values: values.__setitem__("digits_mlp", values["tabular_mlp"]), "distinct"),
])
def test_seed_prompt_block_collisions_stop(monkeypatch, colliding, match):
    declared = dict(c3b.PROMPT_MEASUREMENT_SEEDS)
    colliding(declared)
    monkeypatch.setattr(c3b, "PROMPT_MEASUREMENT_SEEDS", declared)
    s = spec()
    s["seeds"]["prompt_measurement_seeds"] = dict(declared)
    with pytest.raises(c3b.Stop, match=match):
        c3b.check_seed_disjointness(s)


# ------------------------------------------------------------------ liveness argv / verdict
def _liveness_cli_flags():
    text = (ROOT / "r1/liveness/__main__.py").read_text()
    return set(re.findall(r'add_argument\(\s*["\'](--[A-Za-z0-9_-]+)["\']', text))


def test_liveness_argv_uses_only_flags_the_pinned_cli_has():
    s = c3b.validate_spec(spec())["spec"]
    argv = c3b.liveness_argv(s)
    cli_flags = _liveness_cli_flags()
    used = {token for token in argv if token.startswith("--")}
    assert used <= cli_flags, f"argv uses flags the liveness CLI does not define: {sorted(used - cli_flags)}"
    assert "--deadline" not in used and "--deadline" not in cli_flags
    assert argv[0] == "/opt/r1/envs/harness/bin/python" and argv[1] == "-B"
    assert argv[2:5] == ["-m", "r1.liveness", "--run"]
    nodes = argv[argv.index("--nodes") + 1:argv.index("--instances")]
    assert nodes == list(c3b.LIVENESS_NODES) and len(nodes) == 8
    assert argv[argv.index("--instances") + 1] == "2"
    assert argv[argv.index("--runs") + 1] == "10"
    assert argv[argv.index("--memory-mode") + 1] == "append_only_summary"
    assert argv[argv.index("--manager-model") + 1] == "llamacpp/gemma4_31b"
    assert argv[argv.index("--proposal-schema") + 1] == "manager_proposal/v1"
    assert argv[argv.index("--transport-max-attempts") + 1] == "3"


def _report(passes):
    return {
        "schema": "r1.liveness/2", "label": "ENGINEERING_ONLY", "manager_kind": "langgraph",
        "memory_mode": "append_only_summary", "generated_utc": "20261116T000000Z",
        "nodes": {node: {"pass": bool(passes.get(node)), "failed_criteria": [] if passes.get(node) else ["invalid_rate"],
                         "n_trials": 20, "criteria": {"invalid_rate": {"observed": 0.0}}}
                  for node in c3b.LIVENESS_NODES},
    }


def test_all_eight_nodes_pass():
    result = c3b.evaluate_liveness(_report({node: True for node in c3b.LIVENESS_NODES}))
    assert result["pass"] is True and result["live_nodes"] == 8 and result["failed_nodes"] == []


def test_eight_node_shortfall_returns_the_failed_nodes_and_is_not_a_pass():
    passes = {node: True for node in c3b.LIVENESS_NODES}
    passes["openml_climate"] = False
    result = c3b.evaluate_liveness(_report(passes))
    assert result["pass"] is False and result["live_nodes"] == 7
    assert result["failed_nodes"] == ["openml_climate"]


@pytest.mark.parametrize("mutation,match", [
    (lambda r: r.__setitem__("label", "EVIDENCE"), "not ENGINEERING_ONLY"),
    (lambda r: r.__setitem__("manager_kind", "scripted"), "LLM-backed"),
    (lambda r: r.__setitem__("memory_mode", "none"), "memory_mode"),
    (lambda r: r["nodes"].pop("openml_climate"), "missing nodes"),
    (lambda r: r["nodes"].__setitem__("openml_climate", {"pass": "yes"}), "boolean pass"),
])
def test_malformed_liveness_reports_stop(mutation, match):
    report = _report({node: True for node in c3b.LIVENESS_NODES})
    mutation(report)
    with pytest.raises(c3b.Stop, match=match):
        c3b.evaluate_liveness(report)


def test_shortfall_stop_persists_the_record_and_tars(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "work").mkdir()
    (tmp_path / "llama-server.log").write_text("server log\n")
    record = {"schema": c3b.RECORD_SCHEMA, "label": "ENGINEERING_ONLY"}
    with pytest.raises(c3b.Stop, match="only 7/8 nodes passed"):
        c3b._stop_with_evidence(record, tmp_path / "job_record.json",
                                "STOP: only 7/8 nodes passed D28 liveness (< 8)")
    saved = json.loads((tmp_path / "job_record.json").read_text())
    assert saved["stop"].startswith("STOP: only 7/8")
    assert (tmp_path / "out.tar").is_file() and (tmp_path / "work.tar").is_file()
    assert (tmp_path / "SHA256SUMS").is_file()
    assert "job_record.json" in (tmp_path / "SHA256SUMS").read_text()


# ------------------------------------------------------------------ tokenizer prompt set / compare math
def test_measure_prompts_tokenizes_exact_text_and_renders_the_template(monkeypatch):
    calls = []

    def fake_post(url, payload, timeout=120.0):
        calls.append((url, payload))
        if url.endswith("/apply-template"):
            content = payload["messages"][0]["content"]
            assert payload["chat_template_kwargs"] == {"enable_thinking": False}
            return {"prompt": "<bos><sys>manager</sys>" + content + "<end>"}
        if url.endswith("/tokenize"):
            text = payload["content"]
            count = 7 if text.startswith("<bos>") else max(1, len(text.split()))
            return {"tokens": list(range(count))}
        raise AssertionError(url)

    monkeypatch.setattr(c3b, "_post_json", fake_post)
    prompts = {"prompt_set_sha256": "a" * 64, "builder_file_sha256": "b" * 64,
               "prompts": [{"node": node, "variant": "trial_1", "budget_index": 1, "prompt_seed": 6101+i,
                            "campaign_id": f"{node}__s{6101+i}", "memory_mode": "append_only_summary",
                            "memory_records": 0, "text": "You are a manager", "text_sha256": "c" * 64,
                            "chars": 17} for i, node in enumerate(c3b.LIVENESS_NODES)]}
    measured = c3b.measure_prompts("http://127.0.0.1:9999/v1", c3b.validate_spec(spec())["spec"], prompts)
    assert len(measured["prompts"]) == 8
    row = measured["prompts"][0]
    assert row["user_text_tokens"] == 4  # "You are a manager"
    assert row["rendered_prompt_tokens"] == 7
    assert row["rendered_prompt"].startswith("<bos><sys>manager</sys>") and row["template_prefix"] == "<bos><sys>manager</sys>"
    assert row["user_text_present_in_rendered"] is True and row["fits_ctx"] is True
    assert measured["max_tokens"] == 7 and measured["all_fit_ctx"] is True
    tokenize_calls = [call for call in calls if call[0].endswith("/tokenize")]
    assert any(call[1]["add_special"] is False for call in tokenize_calls)
    assert any(call[1]["add_special"] is True for call in tokenize_calls)


def test_prompt_that_does_not_fit_ctx_is_flagged(monkeypatch):
    def fake_post(url, payload, timeout=120.0):
        if url.endswith("/apply-template"):
            return {"prompt": payload["messages"][0]["content"]}
        return {"tokens": list(range(c3b.CTX + 1))}

    monkeypatch.setattr(c3b, "_post_json", fake_post)
    prompts = {"prompt_set_sha256": "a" * 64, "builder_file_sha256": "b" * 64,
               "prompts": [{"node": "digits_mlp", "variant": "trial_1", "budget_index": 1, "prompt_seed": 6101,
                            "campaign_id": "digits_mlp__s6101", "memory_mode": "append_only_summary",
                            "memory_records": 0, "text": "x", "text_sha256": "c" * 64, "chars": 1}]}
    measured = c3b.measure_prompts("http://127.0.0.1:9999/v1", c3b.validate_spec(spec())["spec"], prompts)
    assert measured["all_fit_ctx"] is False


@pytest.mark.parametrize("payload", [{}, {"tokens": []}, {"tokens": ["x"]}])
def test_tokenize_malformed_reply_is_a_stop(monkeypatch, payload):
    monkeypatch.setattr(c3b, "_post_json", lambda url, body, timeout=120.0: payload)
    with pytest.raises(c3b.Stop, match="tokens"):
        c3b.tokenize_text("http://127.0.0.1:9999/v1", "some text", True)


def _measured_fixture(rendered=500, memory_on=1100):
    rows = []
    base = ROOT / c3b.SWEEP1_LIVENESS_PATH / "ledgers"
    for i, node in enumerate(c3b.LIVENESS_NODES):
        ledger = base / c3b.SWEEP1_LEDGERS[node]["instance"] / "root_trials.jsonl"
        first = json.loads(ledger.read_text().splitlines()[0])
        context_sha = first["extra"]["manager"]["context_sha256"]
        rows.append({"node": node, "variant": "trial_1", "budget_index": 1, "prompt_seed": 6101 + i,
                     "campaign_id": f"{node}__s{6101+i}", "memory_mode": "append_only_summary",
                     "memory_records": 0, "user_text_tokens": rendered - 10,
                     "user_text_sha256": context_sha, "rendered_prompt_tokens": rendered,
                     "rendered_prompt_sha256": "d" * 64, "fits_ctx": True})
        rows.append({"node": node, "variant": "memory_on_declared_12", "budget_index": 12, "prompt_seed": 6101 + i,
                     "campaign_id": f"{node}__s{6101+i}", "memory_mode": "append_only_summary",
                     "memory_records": 11, "user_text_tokens": memory_on - 10,
                     "user_text_sha256": "e" * 64, "rendered_prompt_tokens": memory_on,
                     "rendered_prompt_sha256": "f" * 64, "fits_ctx": True})
    return {"schema": "s2_c3b_prompt_measurement/1", "ctx": c3b.CTX, "prompts": rows,
            "max_tokens": rendered, "all_fit_ctx": True, "prompt_set_sha256": "a" * 64}


def test_compare_with_sweep1_reads_the_pinned_record_and_computes_deltas():
    comparison = c3b.compare_with_sweep1(ROOT, _measured_fixture(rendered=500, memory_on=1100))
    assert comparison["summary"]["prompt_texts_identical_to_sweep1"] is True
    assert comparison["summary"]["max_pick_trial1_tokens"] == 500
    assert comparison["summary"]["max_pick_memory_on_tokens"] == 1100
    assert comparison["summary"]["max_pick_prompt_tokens"] == 1100
    assert comparison["summary"]["ctx_headroom_tokens"] == c3b.CTX - 1100
    assert comparison["sweep1_record"]["prompt_max"]["prompt_tokens"] == 1345
    digits = next(row for row in comparison["per_node"] if row["node"] == "digits_mlp")
    assert digits["sweep1_trial1_prompt_tokens"] == 514
    assert digits["trial1_delta_tokens"] == 500 - 514
    assert digits["trial1_tokenizer_ratio"] == round(500 / 514, 4)
    assert digits["prompt_texts_identical"] is True


def test_compare_stops_when_the_prompt_text_no_longer_matches_the_sweep1_record():
    measured = _measured_fixture()
    measured["prompts"][0]["user_text_sha256"] = "0" * 64
    with pytest.raises(c3b.Stop, match="does not reproduce the sweep-1"):
        c3b.compare_with_sweep1(ROOT, measured)


def test_compare_stops_when_the_sweep1_record_is_missing(tmp_path):
    with pytest.raises(c3b.Stop, match="missing"):
        c3b.compare_with_sweep1(tmp_path, _measured_fixture())


def test_prompt_report_has_the_comparison_table_and_headroom():
    comparison = c3b.compare_with_sweep1(ROOT, _measured_fixture())
    text = c3b._prompt_report(_measured_fixture(), comparison)
    assert "| node |" in text and "| digits_mlp |" in text
    assert f"headroom {c3b.CTX - 1100}" in text
    assert "1345" in text


# ------------------------------------------------------------------ prompt builder (fake pinned harness)
class _FakeHarness:
    @staticmethod
    def build(monkeypatch):
        import types

        def prepare(state):
            status = state["status"]
            memory = state["memory_context"]
            lines = [f"Node: {state['node_spec'].name}", f"Budget index (trial number): {status['budget_index']}",
                     f"Current best: {status['current_best_metric']}"]
            lines += [f"  {key} = {value}" for key, value in sorted(status["current_constants"].items())]
            memory_text = getattr(memory, "context_text", "")
            if memory_text:
                lines += ["Prior trial memory:", memory_text]
            else:
                lines += ["No prior trial memory available."]
            return {"context_text": "\n".join(lines)}

        fake = {
            "parse_train_constants": lambda path: {"ALPHA": "1e-4", "LEARNING_RATE_INIT": "1e-3"},
            "load_registered_node": lambda node, repo_root=None: types.SimpleNamespace(
                name=node, description=f"{node} description", metric_name="val_score",
                metric_direction="maximize", editable_paths=("train.py",), editable_symbols=("ALPHA",
                                                                                             "LEARNING_RATE_INIT")),
            "build_memory_context": lambda records, mode, node_spec, budget_index:
                types.SimpleNamespace(context_text="\n".join(f"trial-{i}" for i in range(len(records)))),
            "ManagerStatus": lambda **kwargs: kwargs,
            "TrialRecord": lambda **kwargs: kwargs,
            "TrialProvenance": lambda **kwargs: kwargs,
            "ExecutionStatus": types.SimpleNamespace(SUCCESS="success"),
            "ValidityStatus": types.SimpleNamespace(VALID="valid"),
            "TrialDecision": types.SimpleNamespace(KEPT="kept", DISCARDED="discarded"),
            "_prepare_context": prepare,
        }
        monkeypatch.setattr(c3b, "_harness_import", lambda harness_dir: fake)
        return fake


def test_build_prompt_texts_is_deterministic_and_seed_independent(tmp_path, monkeypatch):
    harness = tmp_path / "harness"
    (harness / "src/autoresearch/manager").mkdir(parents=True)
    (harness / "src/autoresearch/manager/langgraph_manager.py").write_text("# pinned builder\n")
    for node in c3b.LIVENESS_NODES:
        (harness / "nodes" / node).mkdir(parents=True)
        (harness / "nodes" / node / "train.py").write_text("ALPHA = 1e-4\nLEARNING_RATE_INIT = 1e-3\n")
        (harness / "configs/nodes").mkdir(parents=True, exist_ok=True)
        (harness / "configs/nodes" / f"{node}.yaml").write_text("{}\n")
    _FakeHarness.build(monkeypatch)
    first = c3b.build_prompt_texts(harness, c3b.validate_spec(spec())["spec"])
    second = c3b.build_prompt_texts(harness, c3b.validate_spec(spec())["spec"])
    assert first["prompt_set_sha256"] == second["prompt_set_sha256"]
    assert len(first["prompts"]) == 2 * len(c3b.LIVENESS_NODES)
    variants = {prompt["variant"] for prompt in first["prompts"]}
    assert variants == set(c3b.PROMPT_VARIANTS)
    trial1 = [prompt for prompt in first["prompts"] if prompt["variant"] == "trial_1"]
    assert all("No prior trial memory available." in prompt["text"] for prompt in trial1)
    assert all(prompt["memory_records"] == 0 for prompt in trial1)
    memory_on = [prompt for prompt in first["prompts"] if prompt["variant"] == "memory_on_declared_12"]
    assert all(prompt["memory_records"] == c3b.DECLARED_MEMORY_ON_RECORDS for prompt in memory_on)
    assert len({prompt["text_sha256"] for prompt in first["prompts"]}) == 2 * len(c3b.LIVENESS_NODES)


# ------------------------------------------------------------------ job outputs / seal / renderer
def test_prompt_outputs_are_written_into_the_transferred_out_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    comparison = c3b.compare_with_sweep1(ROOT, _measured_fixture())
    c3b._write_prompt_outputs(_measured_fixture(), comparison)
    for name in c3b.PROMPT_OUTPUTS:
        assert (tmp_path / "out" / name).is_file()
    c3b._write_prompt_outputs(_measured_fixture(), None)
    assert (tmp_path / "out" / "s2_c3b_prompt_lengths.json").is_file()


def _seal_record(label="ENGINEERING_ONLY", schema=c3b.RECORD_SCHEMA, kind="liveness", touched=None):
    return {"schema": schema, "kind": kind, "label": label, "run_id": "r1", "chunk_id": "liveness-prompt",
            "image_digest": "ghcr.io/x@sha256:" + "0" * 64, "audit_seeds_touched": touched or []}


@pytest.mark.parametrize("record,match", [
    (_seal_record(schema="s2_c2_job_record/1"), "schema"),
    (_seal_record(kind="chunk"), "kind"),
    (_seal_record(label="EVIDENCE"), "ENGINEERING_ONLY"),
    (_seal_record(touched=[7001]), "audit seeds"),
])
def test_seal_guards(tmp_path, record, match):
    (tmp_path / "job_record.json").write_text(json.dumps(record))
    with pytest.raises(c3b.Stop, match=match):
        c3b.seal(tmp_path, "r1", "liveness-prompt")


def test_seal_delegates_to_c2_and_updates_the_receipt(tmp_path, monkeypatch):
    (tmp_path / "job_record.json").write_text(json.dumps(_seal_record()))
    sealed = tmp_path / "sealed"
    sealed.mkdir()

    def fake_c2_seal(job_output, run_id, chunk_id):
        return {"schema": "s2_c2_seal_receipt/1", "run_id": run_id, "chunk_id": chunk_id,
                "sealed_path": str(sealed), "label": "ENGINEERING_ONLY"}

    monkeypatch.setattr(c2, "seal", fake_c2_seal)
    receipt = c3b.seal(tmp_path, "r1", "liveness-prompt")
    assert receipt["schema"] == c3b.SEAL_RECEIPT_SCHEMA and receipt["unit"] == "S2-C3b"
    saved = json.loads((sealed / "SEAL_RECEIPT.json").read_text())
    assert saved["record_schema"] == c3b.RECORD_SCHEMA


def test_renderer_c3b_pins_the_class_and_transfers_the_five_outputs(tmp_path):
    stage = tmp_path / "stage"
    jdl = tmp_path / "s2_c3b_job.jdl"
    render_jdl.main([str(ROOT / "sweep2" / "spec.c3b.example.json"), "--out", str(jdl),
                     "--stage-dir", str(stage), "--kind", "c3b"])
    text = jdl.read_text()
    assert "S2-C3b" in text and "ENGINEERING_ONLY" in text
    assert "universe = container" in text
    assert "container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35" in text
    assert "executable = s2_c3b_job.sh" in text and "arguments = s2_c3b_spec.json" in text
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA L40S"' in text
    assert 'TARGET.CloudSite =?= "BwForCluster-Nemo2"' in text
    assert f"TARGET.CpuFamily =?= {c2.CPU_FAMILY}" in text
    assert f"TARGET.CpuModelNumber =?= {c2.CPU_MODEL_NUMBER}" in text
    assert "request_disk = 42439718" in text and "request_memory = 32000" in text and "request_GPUs = 1" in text
    assert "+RemoteJob = True" in text and "ProvidesEtpCeph" not in text
    assert "transfer_output_files = out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log" in text
    staged = {path.name for path in stage.iterdir()}
    assert {"s2_c3b_job.sh", "s2_c3b_lib.py", "s2_c2_lib.py", "s2_c3b_spec.json"} <= staged


def test_job_entry_precreates_the_transferred_outputs():
    text = (ROOT / "sweep2" / "s2_c3b_job.sh").read_text()
    for name in ("out.tar", "work.tar", "job_record.json", "SHA256SUMS", "llama-server.log"):
        assert name in text
    assert "s2_c3b_lib.py" in text
