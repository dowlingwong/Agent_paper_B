"""Synthetic tests for the S2-C3b (g)4 D28-liveness + prompt-length unit (no job, no GPU, no network, no server).

Everything here runs on the local checkout: the pinned sweep-1 records are read from the repository (their SHA-256 is
checked by the unit), the llama-server tokenizer client is exercised through a fake HTTP poster, and the seal step's
C2 delegation is monkeypatched so nothing touches /ceph.
"""
import copy
import hashlib
import json
import re
import subprocess
import sys
import types
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
    lambda s: s["prompt_measurement"]["sweep1"].__setitem__("b012_tokens", 999),
    lambda s: s["prompt_measurement"]["sweep1"].__setitem__("w20_max_tokens", 1878),
    lambda s: s["prompt_measurement"]["sweep1"].__setitem__("w20_ledger_budget20_tokens", 1345),
    lambda s: s["prompt_measurement"].__setitem__("variants", ["trial_1", "memory_on_declared_12"]),
])
def test_spec_negatives_stop(change):
    s = spec()
    change(s)
    with pytest.raises(c3b.Stop):
        c3b.validate_spec(s)


def test_spec_with_extra_server_chat_template_kwargs_is_refused():
    """M3: the rebased accepted wrapper requires `--chat-template-kwargs` to be exactly {"enable_thinking": false}.

    An extra server-level template kwarg would make the measured prompt differ from what the server renders for the
    manager call (the per-request /apply-template kwargs stay fixed), so the C3b gate must refuse it.
    """
    s = spec()
    extra = s["server"]["extra_args"]
    index = extra.index("--chat-template-kwargs") + 1
    kwargs = json.loads(extra[index])
    kwargs["add_generation_prompt"] = True
    extra[index] = json.dumps(kwargs)
    with pytest.raises(c3b.Stop, match="chat-template-kwargs"):
        c3b.validate_spec(s)


@pytest.mark.parametrize("key,bad", [("request_disk_kb", 30314083), ("request_memory_mb", 10852)])
def test_spec_below_the_measured_layout_floors_is_refused(key, bad):
    """M3: the rebased accepted wrapper refuses a layout below the measured S2-C4 disk/memory floors."""
    s = spec()
    s[key] = bad
    with pytest.raises(c3b.Stop, match=key):
        c3b.validate_spec(s)


def test_spec_with_the_superseded_s2c4_16k_layout_is_refused():
    """M1: the S2-C4 16k layout is superseded by R1-SWEEP2-LAYOUT; it must not validate for the C3b unit."""
    s = spec()
    s["walltime_s"], s["request_disk_kb"] = 10776, 42439718
    with pytest.raises(c3b.Stop, match="R1-SWEEP2-LAYOUT"):
        c3b.validate_spec(s)


def test_spec_carries_the_accepted_32k_layout_and_validator_returns_it():
    """M1/minor m5: the accepted 32k layout is pinned in the spec and exposed for the job record."""
    validated = c3b.validate_spec(spec())
    assert validated["level_layout"] == c3b.ACCEPTED_LEVEL_LAYOUT
    assert validated["level_layout"] == {"request_walltime_s": 12203, "request_disk_kb": 42460977,
                                         "request_memory_mb": 32000}


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
    (lambda values: values.__setitem__("digits_mlp", 9400), "collide"),  # open-ended guard beyond the 9001-9303 block
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


def test_evaluate_liveness_requires_the_pinned_report_schema():
    """m6: the schema is checked, not merely recorded."""
    report = _report({node: True for node in c3b.LIVENESS_NODES})
    report["schema"] = "r1.liveness/1"
    with pytest.raises(c3b.Stop, match="schema"):
        c3b.evaluate_liveness(report)


def test_evaluate_liveness_refuses_unexpected_extra_nodes():
    """m6: extra nodes are refused explicitly, not silently ignored."""
    report = _report({node: True for node in c3b.LIVENESS_NODES})
    report["nodes"]["rogue_node"] = {"pass": True, "failed_criteria": [], "n_trials": 20, "criteria": {}}
    with pytest.raises(c3b.Stop, match="unexpected nodes"):
        c3b.evaluate_liveness(report)


@pytest.mark.parametrize("mutation,match", [
    (lambda r: r.__setitem__("label", "EVIDENCE"), "not ENGINEERING_ONLY"),
    (lambda r: r.__setitem__("manager_kind", "scripted"), "LLM-backed"),
    (lambda r: r.__setitem__("memory_mode", "none"), "memory_mode"),
    (lambda r: r.__setitem__("schema", "r1.liveness/2 "), "schema"),
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


def test_measure_prompts_stops_when_the_template_drops_the_user_text(monkeypatch):
    """m2: a template that mangles/normalises the user text must STOP, not record a quiet non-measurement."""

    def fake_post(url, payload, timeout=120.0):
        if url.endswith("/apply-template"):
            return {"prompt": "<bos><start_of_turn>user\n a mangled rendering <end>"}
        return {"tokens": [1, 2, 3]}

    monkeypatch.setattr(c3b, "_post_json", fake_post)
    prompts = {"prompt_set_sha256": "a" * 64, "builder_file_sha256": "b" * 64,
               "prompts": [{"node": "digits_mlp", "variant": "trial_1", "budget_index": 1, "prompt_seed": 6101,
                            "campaign_id": "digits_mlp__s6101", "memory_mode": "append_only_summary",
                            "memory_records": 0, "text": "exact user text", "text_sha256": "c" * 64,
                            "chars": 15}]}
    with pytest.raises(c3b.Stop, match="does not contain the user text"):
        c3b.measure_prompts("http://127.0.0.1:9999/v1", c3b.validate_spec(spec())["spec"], prompts)


@pytest.mark.parametrize("payload", [{}, {"tokens": []}, {"tokens": ["x"]}])
def test_tokenize_malformed_reply_is_a_stop(monkeypatch, payload):
    monkeypatch.setattr(c3b, "_post_json", lambda url, body, timeout=120.0: payload)
    with pytest.raises(c3b.Stop, match="tokens"):
        c3b.tokenize_text("http://127.0.0.1:9999/v1", "some text", True)


def _measured_fixture(rendered=500, memory_on=1100, w20=1500, drop_w20=False):
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
        if not drop_w20:
            rows.append({"node": node, "variant": "memory_on_budget_20", "budget_index": 20,
                         "prompt_seed": 6101 + i, "campaign_id": f"{node}__s{6101+i}",
                         "memory_mode": "append_only_summary", "memory_records": 19,
                         "user_text_tokens": w20 - 10, "user_text_sha256": "g" * 64,
                         "rendered_prompt_tokens": w20, "rendered_prompt_sha256": "h" * 64, "fits_ctx": True})
    return {"schema": "s2_c3b_prompt_measurement/1", "ctx": c3b.CTX, "prompts": rows,
            "max_tokens": max(w20, memory_on, rendered), "all_fit_ctx": True, "prompt_set_sha256": "a" * 64}


def test_verify_sweep1_prompt_record_pins_the_b012_value_and_the_true_w20_maximum():
    """M2: 1,345 is the 14 Oct rerun-2 budget-12 value; the true W=20 maximum is 1,886 over 54 root ledgers."""
    record = c3b.verify_sweep1_prompt_record(ROOT)
    assert record["b012"]["prompt_tokens"] == 1345 and record["b012"]["budget_index"] == 12
    assert record["w20"]["root_count"] == 54 and record["w20"]["roots_sha256"] == c3b.SWEEP1_W20_ROOTS_SHA256
    assert record["w20"]["ledger_budget12_tokens"] == 1345
    assert record["w20"]["ledger_budget20_tokens"] == 1878
    assert record["w20"]["max_tokens"] == 1886
    assert record["w20"]["max_instance"] == "tabular_mlp__s112"
    assert record["w20"]["max_budget_index"] == 20
    assert "14 Oct" in record["b012"]["prompt_set"] and "NOT a maximum" in record["b012"]["meaning"]
    # the corrected comparison: the 14 Oct rerun-2 text is not the 27 Oct liveness/sweep-2 text
    rerun2, sweep2 = record["rerun2_breast_w_trial1"], record["sweep2_breast_w_trial1"]
    assert rerun2["context_sha256"] == c3b.RERUN2_BREAST_W_TRIAL1_SHA256 and rerun2["prompt_tokens"] == 483
    assert sweep2["context_sha256"] == c3b.SWEEP1_LIVENESS_BREAST_W_TRIAL1_SHA256 and sweep2["prompt_tokens"] == 482
    assert rerun2["context_sha256"] != sweep2["context_sha256"]
    assert "not the 27 Oct" in record["prompt_set_note"]


@pytest.mark.parametrize("name,value,match", [
    ("SWEEP1_W20_MAX_TOKENS", 1878, "W=20 maximum"),
    ("SWEEP1_W20_ROOTS_SHA256", "0" * 64, "root-ledger set sha256"),
    ("SWEEP1_W20_LEDGER_SHA256", "0" * 64, "sha256"),
    ("SWEEP1_PROMPT_B012_TOKENS", 1878, "b012"),  # snapshot read still errors on the file value first
])
def test_verify_sweep1_prompt_record_stops_on_a_changed_pinned_record(monkeypatch, name, value, match):
    monkeypatch.setattr(c3b, name, value)
    with pytest.raises(c3b.Stop, match=match):
        c3b.verify_sweep1_prompt_record(ROOT)


def test_compare_with_sweep1_reads_the_pinned_record_and_computes_deltas():
    comparison = c3b.compare_with_sweep1(ROOT, _measured_fixture(rendered=500, memory_on=1100, w20=1500))
    assert comparison["summary"]["prompt_texts_identical_to_sweep1"] is True
    assert comparison["summary"]["max_pick_trial1_tokens"] == 500
    assert comparison["summary"]["max_pick_memory_on_declared_12_tokens"] == 1100
    assert comparison["summary"]["max_pick_memory_on_budget_20_tokens"] == 1500
    assert comparison["summary"]["max_pick_prompt_tokens"] == 1500
    assert comparison["summary"]["max_pick_memory_on_tokens"] == 1500
    assert comparison["summary"]["sweep1_b012_tokens"] == 1345
    assert comparison["summary"]["sweep1_w20_max_tokens"] == 1886
    assert comparison["summary"]["ratio_vs_sweep1_w20_max"] == round(1500 / 1886, 4)
    assert comparison["summary"]["ratio_vs_sweep1_b012"] == round(1100 / 1345, 4)
    assert comparison["summary"]["ctx_headroom_tokens"] == c3b.CTX - 1500
    assert comparison["summary"]["longest_prompt_class_measured"] is True
    assert comparison["sweep1_record"]["b012"]["prompt_tokens"] == 1345
    assert comparison["sweep1_record"]["w20"]["max_tokens"] == 1886
    assert "14 Oct" in comparison["sweep1_record"]["prompt_set_note"]
    digits = next(row for row in comparison["per_node"] if row["node"] == "digits_mlp")
    assert digits["sweep1_trial1_prompt_tokens"] == 514
    assert digits["trial1_delta_tokens"] == 500 - 514
    assert digits["trial1_tokenizer_ratio"] == round(500 / 514, 4)
    assert digits["prompt_texts_identical"] is True
    assert digits["pick_memory_on_budget_20_tokens"] == 1500


def test_compare_stops_when_the_w20_longest_class_was_not_measured():
    """M2: the 11-record fixture alone is a middle class; the W=20 / 19-record class is required."""
    with pytest.raises(c3b.Stop, match="W=20"):
        c3b.compare_with_sweep1(ROOT, _measured_fixture(drop_w20=True))


def test_compare_carries_the_in_run_usage_cross_check():
    cross = {"schema": "s2_c3b_liveness_usage_cross_check/1", "available": True, "nodes_checked": 8,
             "max_abs_delta_tokens": 0, "all_bos_consistent_within_1_token": True}
    comparison = c3b.compare_with_sweep1(ROOT, _measured_fixture(), cross_check=cross)
    assert comparison["liveness_usage_cross_check"] == cross


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
    assert f"headroom {c3b.CTX - 1500}" in text
    assert "1,345" in text and "1,886" in text and "not a maximum" in text.lower()
    assert "W=20" in text


def test_cross_check_reads_the_jobs_own_liveness_ledgers(tmp_path):
    """m3: compare /tokenize(add_special=True) against the job's own usage.prompt_tokens, where available."""
    ledgers = tmp_path / "ledgers"
    for i, node in enumerate(c3b.LIVENESS_NODES):
        ledger = ledgers / f"{node}__s{104 + i}"
        ledger.mkdir(parents=True)
        for k, usage in ((1, 500 + i), (2, 510 + i)):  # trial-1 matches the fixture; trial 2 must be ignored
            (ledger / "root_trials.jsonl").open("a").write(json.dumps(
                {"budget_index": k, "campaign_id": f"{node}__s{104+i}", "extra": {"manager":
                 {"llm_call": {"prompt_tokens": usage}}}}) + "\n")
    measured = {"prompts": [{"node": node, "variant": "trial_1", "rendered_prompt_tokens": 500 + i}
                            for i, node in enumerate(c3b.LIVENESS_NODES)]}
    check = c3b.cross_check_liveness_usage(tmp_path, measured)
    assert check["available"] is True and check["nodes_checked"] == 8
    assert check["max_abs_delta_tokens"] == 0
    assert check["all_bos_consistent_within_1_token"] is True
    assert check["per_node"]["digits_mlp"]["liveness_usage_prompt_tokens"] == 500
    assert check["per_node"]["digits_mlp"]["delta_tokens"] == 0


def test_cross_check_records_a_one_token_bos_delta_and_a_missing_ledger_is_not_available(tmp_path):
    assert c3b.cross_check_liveness_usage(tmp_path, {"prompts": []})["available"] is False
    ledger = tmp_path / "ledgers" / "digits_mlp__s104"
    ledger.mkdir(parents=True)
    (ledger / "root_trials.jsonl").write_text(json.dumps(
        {"budget_index": 1, "campaign_id": "digits_mlp__s104",
         "extra": {"manager": {"llm_call": {"prompt_tokens": 499}}}}) + "\n")
    check = c3b.cross_check_liveness_usage(tmp_path, {"prompts": [
        {"node": "digits_mlp", "variant": "trial_1", "rendered_prompt_tokens": 500}]})
    entry = check["per_node"]["digits_mlp"]
    assert entry["delta_tokens"] == 1 and entry["bos_consistent"] is True


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
    assert len(first["prompts"]) == len(c3b.PROMPT_VARIANTS) * len(c3b.LIVENESS_NODES)
    variants = {prompt["variant"] for prompt in first["prompts"]}
    assert variants == set(c3b.PROMPT_VARIANTS)
    trial1 = [prompt for prompt in first["prompts"] if prompt["variant"] == "trial_1"]
    assert all("No prior trial memory available." in prompt["text"] for prompt in trial1)
    assert all(prompt["memory_records"] == 0 for prompt in trial1)
    middle = [prompt for prompt in first["prompts"] if prompt["variant"] == "memory_on_declared_12"]
    assert all(prompt["memory_records"] == c3b.DECLARED_MEMORY_ON_RECORDS for prompt in middle)
    assert all(prompt["budget_index"] == 12 for prompt in middle)
    # M2: the longest class is the W=20 / 19-record variant, not the 11-record middle class
    longest = [prompt for prompt in first["prompts"] if prompt["variant"] == "memory_on_budget_20"]
    assert len(longest) == len(c3b.LIVENESS_NODES)
    assert all(prompt["memory_records"] == c3b.W20_RECORDS == 19 for prompt in longest)
    assert all(prompt["budget_index"] == 20 for prompt in longest)
    for node in c3b.LIVENESS_NODES:
        by_variant = {prompt["variant"]: prompt for prompt in first["prompts"] if prompt["node"] == node}
        assert len(by_variant["memory_on_budget_20"]["text"]) > len(by_variant["memory_on_declared_12"]["text"])
        assert len(by_variant["memory_on_declared_12"]["text"]) > len(by_variant["trial_1"]["text"])
    assert len({prompt["text_sha256"] for prompt in first["prompts"]}) == len(c3b.PROMPT_VARIANTS) * len(c3b.LIVENESS_NODES)


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


def test_run_liveness_job_stop_kills_the_server_before_sums_and_the_result_seals(tmp_path, monkeypatch):
    """M4 / minor m4: end-to-end synthetic STOP (fake server + failing liveness) proving the seal path.

    The fake server appends a final log line when it is killed.  The test asserts the kill happens before
    `_persist` hashes `llama-server.log` into `SHA256SUMS`, then runs the REAL C2 seal (real `sha256sum -c`
    verification; only the sealed /ceph root is redirected into tmp), so the transferred sums verify and the
    shortfall/failure evidence is sealable.
    """
    monkeypatch.chdir(tmp_path)
    events = []
    log_path = tmp_path / "llama-server.log"
    log_path.write_text("server start\n")
    (tmp_path / "out").mkdir()
    (tmp_path / "work").mkdir()
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(SPEC))

    manifest = json.loads(SWEEP1_MANIFEST.read_text())
    monkeypatch.setattr(c3b, "verify_sweep1_record", lambda paper_dir: {
        "path": c3b.SWEEP1_LIVENESS_PATH, "liveness_sha256": c3b.SWEEP1_LIVENESS_SHA256,
        "manifest_sha256": c3b.SWEEP1_MANIFEST_SHA256, "manifest": manifest})
    monkeypatch.setattr(c3b, "verify_sweep1_prompt_record", lambda paper_dir: {"ok": True})
    monkeypatch.setattr(c3b.c2, "clone_at", lambda repo, commit, dest: dest.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(c3b.c2, "image_identity", lambda spec: {"versions_sha256": "0" * 64})
    monkeypatch.setattr(c3b.c2, "host_identity",
                        lambda: {"hostname": "test", "fqdn": "test.invalid", "logical_cpus": 16})
    monkeypatch.setattr(c3b.c2, "gpu_identity", lambda model: {"name": "NVIDIA L40S", "uuid": "gpu-test"})
    monkeypatch.setattr(c3b.c2, "cpu_identity", lambda *a: {"model": "test", "logical_cpus": 16})
    monkeypatch.setattr(c3b.c2, "fetch_model", lambda model, dest: {"sha256": model["sha256"], "size": 1})
    proc = types.SimpleNamespace(pid=424242)
    monkeypatch.setattr(c3b.c2, "start_server", lambda spec, model, log: {
        "proc": proc, "pid": proc.pid, "base_url": "http://127.0.0.1:18111/v1", "build": "test",
        "offloaded_layers": 61, "total_layers": 61, "cuda_lines": [], "log": "llama-server.log"})

    def kill(handle):
        if handle is not None:
            log_path.write_text(log_path.read_text() + "server shutdown (written by the dying server)\n")
        events.append(("kill", handle))

    monkeypatch.setattr(c3b.c2, "_kill", kill)
    real_write_sums = c2._write_sums

    def write_sums(root):
        events.append(("sums", root))
        real_write_sums(root)

    monkeypatch.setattr(c3b.c2, "_write_sums", write_sums)
    real_run = subprocess.run

    def fake_run(argv, *a, **kw):
        if isinstance(argv, (list, tuple)) and argv and argv[0] in ("tar", "sha256sum"):
            return real_run(argv, *a, **kw)  # real tar / real sums verification, never faked away
        events.append(("r1.liveness", None))
        return types.SimpleNamespace(returncode=1, stdout="liveness failed", stderr="synthetic failure")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(c3b.Stop, match="r1.liveness rc=1"):
        c3b.run_liveness_job(spec_path)

    kinds = [name for name, _ in events]
    assert "kill" in kinds and "sums" in kinds
    assert kinds.index("kill") < kinds.index("sums"), f"the server was not killed before SHA256SUMS: {events}"
    assert events[kinds.index("kill")][1] is proc
    record = json.loads((tmp_path / "job_record.json").read_text())
    assert record["stop"].startswith("STOP: r1.liveness rc=1")
    assert record["level_layout"] == c3b.ACCEPTED_LEVEL_LAYOUT
    for name in ("out.tar", "work.tar", "job_record.json", "SHA256SUMS", "llama-server.log"):
        assert (tmp_path / name).is_file(), f"missing transferred output {name}"
    sums = (tmp_path / "SHA256SUMS").read_text()
    assert "llama-server.log" in sums and "job_record.json" in sums
    assert "server shutdown (written by the dying server)" in log_path.read_text()

    sealed = tmp_path / "sealed" / "s2c3b-20261116-a" / "liveness-prompt"
    monkeypatch.setattr(c3b.c2, "_sealed_target", lambda run_id, chunk_id: sealed)
    receipt = c3b.seal(tmp_path, "s2c3b-20261116-a", "liveness-prompt")
    assert receipt["schema"] == c3b.SEAL_RECEIPT_SCHEMA and receipt["unit"] == "S2-C3b"
    assert receipt["sealed_path"] == str(sealed)
    assert (sealed / "SEAL_RECEIPT.json").is_file()
    assert (sealed / "job_record.json").is_file()
    assert (sealed / "out").is_dir() and (sealed / "work").is_dir()


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
    assert "TARGET.GPUs_GlobalMemoryMb >= 24576" in text and "TARGET.GPUs_Capability >= 7.0" in text
    assert "TARGET.GPUs_DeviceName" not in text
    assert "TARGET.CloudSite" not in text
    assert "TARGET.CpuFamily" not in text
    assert "TARGET.CpuModelNumber" not in text
    assert "request_disk = 42460977" in text and "request_memory = 32000" in text and "request_GPUs = 1" in text
    assert "+RequestWalltime = 12203" in text
    assert "+RemoteJob = True" in text and "ProvidesEtpCeph" not in text
    assert "transfer_output_files = out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log" in text
    staged = {path.name for path in stage.iterdir()}
    assert {"s2_c3b_job.sh", "s2_c3b_lib.py", "s2_c2_lib.py", "s2_c3b_spec.json"} <= staged


def test_job_entry_precreates_the_transferred_outputs():
    text = (ROOT / "sweep2" / "s2_c3b_job.sh").read_text()
    for name in ("out.tar", "work.tar", "job_record.json", "SHA256SUMS", "llama-server.log"):
        assert name in text
    assert "s2_c3b_lib.py" in text


def test_worker_audit_helper_scans_work_and_out(tmp_path, monkeypatch):
    import s2_c3b_lib as c3b
    monkeypatch.chdir(tmp_path)
    with pytest.raises(c3b.Stop, match="no liveness worker run.log"):
        c3b.audit_worker_logs()
    log = tmp_path / "work" / "roots" / "x" / "art" / "trial-001" / "run.log"
    log.parent.mkdir(parents=True)
    log.write_text("Traceback (most recent call last):\nModuleNotFoundError: No module named 'numpy'\n")
    with pytest.raises(c3b.Stop, match="all liveness worker runs crashed"):
        c3b.audit_worker_logs()
    other = tmp_path / "out" / "roots" / "x" / "art" / "trial-002" / "run.log"
    other.parent.mkdir(parents=True)
    other.write_text("val_score 0.91\n")
    audit = c3b.audit_worker_logs()
    assert audit["total_run_logs"] == 2 and audit["crashed"] == 1


def test_launch_binding_must_match_the_launch_spec(tmp_path):
    import json as _json
    import s2_c3b_lib as c3b
    spec = _json.loads((__import__("pathlib").Path(__file__).resolve().parents[3] / "sweep2" / "spec.c3b.example.json").read_text())
    v = c3b.validate_spec(spec)
    assert v["launch_binding"]["server_settings_sha256"] == c3b.server_settings_sha256(spec)
    bad = _json.loads(_json.dumps(spec)); bad["launch_binding"]["server_settings_sha256"] = "0" * 64
    with pytest.raises(c3b.Stop, match="launch_binding.server_settings_sha256"):
        c3b.validate_spec(bad)
    bad = _json.loads(_json.dumps(spec)); del bad["launch_binding"]
    with pytest.raises(c3b.Stop, match="launch_binding is required"):
        c3b.validate_spec(bad)
