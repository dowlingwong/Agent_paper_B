"""A5's T1 prompt form (``r1/c3/train/serialize_t1.py``) and the T1 rows in the Track P data path (D7 of the
ARMS-T1FEAT A report). Synthetic G.5 tables only (the world of ``test_t1_g5_seal``); no label, evaluation value or
real ledger is read. ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from r1.tests.test_t1_g5_seal import A, NODE, SIGMA, Engine, assemble_world, lock_for, node_git, world  # noqa: F401
from r1.tests.test_t1_features import bind_summary, g1b_run

import g5_noise as N  # noqa: E402  (sweep2/t1_tasl is on sys.path through test_t1_g5_seal)

from r1.c3 import dataset as D
from r1.c3 import features as F
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split
from r1.c3.arms import is_noop
from r1.c3.train import serialize as S
from r1.c3.train import serialize_t1 as S1
from r1.c3.train import sft_data as SD
from r1.c3.train.types import BIN_OPTIONS, PROMPT_VERSION, QUESTION, DecisionPrompt

W = 20


class _Whitespace:
    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": text.split()}


class _Chars:
    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": list(text)}


TOKS = {"whitespace": _Whitespace()}


@pytest.fixture(autouse=True)
def _control_plane_skip(monkeypatch):
    """As in test_trackp_serialize: stand in for the harness's ``is_control_plane_skip`` when the pin lacks it."""
    try:
        F._is_control_plane_skip({"decision": "kept", "extra": {}})
    except ImportError:
        def stand_in(row):
            c = (row.get("extra") or {}).get("control") or {}
            return row.get("decision") == "skipped" and c.get("action") == "skip" and c.get("reason") != "inactive_key"
        monkeypatch.setattr(F, "_is_control_plane_skip", stand_in)


def older_table(rows, build):
    """A fallback-A table (D7-DIFF A): the rows and build.json the assembly wrote before the D7-DIFF B change
    (``g5_t1_table/1``: no ``proposal_diff`` field, no build record). The B table less the two row fields is that
    table byte for byte (``test_t1_d7_diff_b.test_fallback_a_table_is_the_base_commits_table``)."""
    rows = [{k: v for k, v in r.items() if k not in S1.DIFF_FIELDS} for r in rows]
    build = {k: v for k, v in build.items() if k != "proposal_diff"}
    build.update(schema=S1.TABLE_SCHEMA_A, proposals_sha256=hashlib.sha256(A._lines(rows)).hexdigest())
    return rows, build


def g5_table(world, *, test=False, older=False):
    """The assembled synthetic G.5 table (features filled): rows, label rows, (evaluation rows), build.json. A table
    of this code is D7-DIFF B (``g5_t1_table/2``, rows with ``proposal_diff``); ``older``: the fallback-A shape."""
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s, divergent_label={"S12_6", "S13_6", "S23_6"},  # 5103: train
                                                   divergent_eval={"S13_7"}))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    if test:
        A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()]
    labels = [json.loads(x) for x in (ev / "label_block.jsonl").read_text().splitlines()]
    evals = ([json.loads(x) for x in (ev / "evaluation_block.jsonl").read_text().splitlines()] if test else [])
    build = json.loads((table / "build.json").read_text())
    if older:
        rows, build = older_table(rows, build)
        (table / "proposals.jsonl").write_bytes(A._lines(rows))
        (table / "build.json").write_text(json.dumps(build, indent=1, sort_keys=True) + "\n")
    return {"rows": rows, "labels": labels, "evals": evals, "build": build, "table": table}


def _split(row):
    return p3_split.assignment(p3_split.load())[row["instance"]]["split"]


def _by_step(rows, campaign):
    return {r["budget_index"]: r for r in rows if S1.campaign_key(r["proposal_id"]) == campaign}


# =============================================================================================== T0 unchanged
# The T0 synthetic sweep of test_trackp_sft (no torch needed for the builder). The hashes below were computed with
# this exact construction on the base commit 14f19a09 (origin/main) before this unit, by /tmp/a5t1dev/golden.py.
T0_NODE, T0_SIGMA = "digits_mlp", 0.0075
T0_START = {"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"}
T0_VALUES = {"HIDDEN_UNITS": ["16", "32", "64", "128"], "ALPHA": ["1e-5", "1e-4", "1e-3", "1e-2"],
             "MAX_ITER": ["20", "40", "80", "160"]}
T0_NOISE = {T0_NODE: {"sigma_node": T0_SIGMA, "sigma_structural": T0_SIGMA, "sigma_local": T0_SIGMA}}
T0_GOLDEN = {"n_prompts": 81,
             "prompts_sha256": "a01786ae2874f1a30fada9f5894b0dd139aaad9ce3d0e0a060d295de3206b8c8",
             "rows.jsonl": "bcde820614d5b61b15c1083ce41d328ff16de5ac05c4e271c6ceb45537c39917",
             "sft_data.json": "154a4a44e1abf914acf678252a7d90f1933ac6ba476e8b20ca518161cee844cb",
             "splits.json": "fc821cf6a6df78b0fe1796dff5b88a1083f1d2cbe83fd814c5054a3fc4635476"}


def _t0_metric(cfg):
    h = int(hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8], 16)
    return round(0.85 + (h % 1000) / 10000.0, 4)


def _t0_ledger(inst, n=10):
    rng = np.random.default_rng(int(inst.rsplit("__s", 1)[1]))
    inc = {"HIDDEN_UNITS": "32", "ALPHA": "1e-4", "MAX_ITER": "40"}
    best, rows = None, []
    for b in range(1, n + 1):
        key = list(T0_VALUES)[int(rng.integers(3))]
        new = inc[key] if b == 4 else str(rng.choice([v for v in T0_VALUES[key] if v != inc[key]]))
        cand = {**inc, key: new}
        m = _t0_metric(cand)
        kept = best is None or m > best
        rows.append({"budget_index": b, "decision": "kept" if kept else "discarded",
                     "parsed_metrics": {"val_score": m}, "current_best_before": best,
                     "delta_vs_best": None if best is None else m - best,
                     "extra": {"manager": {"structured_edit": {"symbol": key, "old": inc[key], "new": new,
                                                               "path": "train.py"}}}})
        if kept:
            inc, best = cand, m
    return rows


def t0_sweep(tmp, instances, source="c3_synth_none", toks=None):
    d = tmp / f"sweep_{source}"
    rows = []
    for inst in instances:
        led = _t0_ledger(inst)
        (d / "ledgers" / inst).mkdir(parents=True)
        (d / "ledgers" / inst / "root_trials.jsonl").write_text("".join(json.dumps(r) + "\n" for r in led))
        (d / "roots").mkdir(exist_ok=True)
        (d / "roots" / f"{inst}.json").write_text(json.dumps({"start_files": T0_START}))
        props, _ = F.replay_campaign(led, T0_START, T0_NODE, inst, source, "none", 20, T0_SIGMA)
        rows += [D.row_of(p, T0_NOISE) for p in props]
    spec = {"dir": str(d), "ledgers": "ledgers/*/root_trials.jsonl", "runs": 20, "memory_mode": "none"}
    (tmp / "index.json").write_text("{}")
    inputs = {"index_path": tmp / "index.json", "specs": {source: (spec, d)}, "noise": T0_NOISE}
    return rows, SD.sweep_prompts(inputs, tokenizers=toks or TOKS)


def t0_golden_build(tmp_path):
    rows, prompts = t0_sweep(tmp_path, [f"{T0_NODE}__s{100 + k}" for k in range(9)], toks={"ws": _Whitespace()})
    text = "".join(f"{pid}\n{S.render_text(p)}\n{json.dumps(p.meta, sort_keys=True, default=str)}\n"
                   for pid, (p, _) in sorted(prompts.items()))
    out = tmp_path / "data"
    manifest = SD.build_sft_data(rows, SD.SyntheticLabelSource(rows, seed=3), prompts, out,
                                 split_cfg={"salt": "golden", "test_instances_per_node": 2,
                                            "val_instances_per_node": 2},
                                 table_record={"sha256": {"proposals.jsonl": "0" * 64}},
                                 prompt_record={"n": len(prompts)})
    got = {"n_prompts": len(prompts), "prompts_sha256": hashlib.sha256(text.encode()).hexdigest(),
           **{n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in ("rows.jsonl", "splits.json",
                                                                             "sft_data.json")}}
    return got, manifest


def test_t0_prompts_and_t0_data_directory_byte_identical_to_the_base_commit(tmp_path):
    got, manifest = t0_golden_build(tmp_path)
    assert got == T0_GOLDEN
    assert "t1" not in manifest and manifest["prompt_version"] == PROMPT_VERSION
    assert manifest["label_seeds"] == list(SD.LABEL_SEEDS)


def test_a_t0_build_needs_neither_serialize_t1_nor_sweep2(tmp_path, monkeypatch):
    """Review m2: serialize_t1 (which loads sweep2/t1_tasl/g5_features.py) is imported only when T1 rows exist."""
    import sys
    import r1.c3.train as train_pkg
    monkeypatch.delattr(train_pkg, "serialize_t1", raising=False)
    monkeypatch.setitem(sys.modules, "r1.c3.train.serialize_t1", None)       # any import of it now fails
    with pytest.raises(ImportError):
        from r1.c3.train import serialize_t1  # noqa: F401
    got, _ = t0_golden_build(tmp_path)
    assert got == T0_GOLDEN


def test_the_split_files_t1_nodes_are_the_forms_t1_nodes():
    assert set(S1.T1_NODES) == set(p3_split.T1_NODES) and S1.T1_PROMPT_VERSION == "trackp_prompt_t1/1"


# =============================================================================================== the T1 form
def test_every_non_inert_t1_test_proposal_gets_a_well_formed_prompt(world):
    g = g5_table(world)
    rows, build = g["rows"], g["build"]
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    assert set(prompts) == {r["proposal_id"] for r in rows}            # every row, no-ops included (training)
    test_rows = [r for r in rows if _split(r) == "test" and not is_noop(r)]
    assert test_rows and any(r["duplicate"] for r in test_rows)
    assert S1.missing_for_gate(rows, prompts) == []
    for r in test_rows:
        p, feats = prompts[r["proposal_id"]]
        b = r["budget_index"]
        assert isinstance(p, DecisionPrompt) and p.question == QUESTION and p.options == BIN_OPTIONS
        assert feats is r["features"] and SD.features_hash(feats) == SD.features_hash(r["features"])
        lines = p.state.split("\n")
        assert lines[0] == (f"Node: {NODE} (MLAgentBench suite, tier T1, code-level diffs; n/a rows, n/a features, "
                            "n/a classes, minority share n/a)")
        assert lines[1] == ("Metric: n/a (higher is better; z is signed so that positive is better); noise level "
                            f"sigma_node = {S.fmt(SIGMA)}")
        assert lines[2] == "Memory: history" and lines[3] == f"Budget: trial {b}; manager calls used {b - 1} of {W}"
        assert lines[6] == "History (oldest first):"
        hist = lines[7:]
        assert hist == ["(none)"] if b == 1 else [h.split(":")[0] for h in hist] == [f"t{s}" for s in range(1, b)]
        assert p.proposal.split("\n")[0] == "Edit: n/a (code-level diff; no structured key edit)"
        assert p.meta["prompt_version"] == S1.T1_PROMPT_VERSION and p.meta["history_dropped"] == 0
        assert p.meta["proposal_id"] == r["proposal_id"] and p.group == r["proposal_id"]
        text = S.render_text(p)
        assert text.count("\nOptions:\n") == 1 and text.endswith(f"11. {BIN_OPTIONS[11]}")


def test_na_rendering_and_no_t0_values(world):
    g = g5_table(world, older=True)                 # fallback A: "Diff: n/a"; the B proposal: test_t1_d7_diff_b
    rows, build = g["rows"], g["build"]
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    camp = f"g5.history:{NODE}__s5101"
    steps = _by_step(rows, camp)
    p = prompts[steps[3]["proposal_id"]][0]
    assert "Incumbent configuration (active keys): n/a (code-level node; no structured configuration)" in p.state
    gain = steps[3]["features"]["recorded_gain_z"]
    assert f"Incumbent metric: n/a; recorded gain since the first valid trial: z = {gain:+.2f}" in p.state
    prop = p.proposal.split("\n")
    assert prop == ["Edit: n/a (code-level diff; no structured key edit)",
                    "Diff: n/a (not carried by the G.5 table)",
                    "Edited key: n/a (no structured key); key type: n/a",
                    "Active configuration equals the incumbent (normalised code state): no; evaluated before in this "
                    "campaign: no",
                    "Raw code equals the incumbent: no; raw code evaluated before in this campaign: no",
                    "Times this key was edited before: n/a; same edit before: n/a; reverses the last edit of this "
                    "key: n/a"]
    inert = next(r for r in steps.values() if r["noop"])
    assert ("Active configuration equals the incumbent (normalised code state): yes"
            in prompts[inert["proposal_id"]][0].proposal)
    # D2 A: the four code-state fields have a T1 source and the table (D9 B: raw code states in every record) gives
    # each a value, so every T1 prompt shows yes / no on both flag lines, the value the row's features hold, and the
    # active flags agree with the harness's verdicts (noop, duplicate)
    yn = {1.0: "yes", 0.0: "no"}
    for r in rows:
        f, prop = r["features"], prompts[r["proposal_id"]][0].proposal.split("\n")
        assert all(f[k] in yn for k in ("cfg_equals_incumbent", "active_equals_incumbent", "active_seen_before",
                                        "full_seen_before")), r["proposal_id"]
        assert prop[3] == ("Active configuration equals the incumbent (normalised code state): "
                           f"{yn[f['active_equals_incumbent']]}; evaluated before in this campaign: "
                           f"{yn[f['active_seen_before']]}")
        assert prop[4] == (f"Raw code equals the incumbent: {yn[f['cfg_equals_incumbent']]}; raw code evaluated "
                           f"before in this campaign: {yn[f['full_seen_before']]}")
        assert (f["active_equals_incumbent"] == 1.0) == r["noop"]
        assert f["active_seen_before"] == float(r["noop"] or r["duplicate"])
    assert {r["features"]["cfg_equals_incumbent"] for r in rows} == {0.0, 1.0}
    assert {r["features"]["full_seen_before"] for r in rows} == {0.0, 1.0}
    # the yes / no wording is T0's (serialize.serialize_view prints its flags with these two words)
    assert "'yes' if res.noop else 'no'" in __import__("inspect").getsource(S.serialize_view)
    # a NaN code-state flag (a record without raw code states) is refused, never shown as n/a: D9 B STOPs such a table
    for k in ("cfg_equals_incumbent", "full_seen_before", "active_equals_incumbent", "active_seen_before"):
        bad = json.loads(json.dumps(steps[3]))
        bad["features"][k] = float("nan")
        with pytest.raises(S1.T1PromptError, match="code-state flag is NaN"):
            S1.t1_prompt(bad, list(steps.values()), S1.check_build(build)[NODE], budget_w=W, tokenizers=TOKS)
    bad = json.loads(json.dumps(steps[3]))
    bad["features"]["cfg_equals_incumbent"] = 0.5
    with pytest.raises(S1.T1PromptError, match="must be 0 or 1"):
        S1.t1_prompt(bad, list(steps.values()), S1.check_build(build)[NODE], budget_w=W, tokenizers=TOKS)
    # no code-state field is among the fields refused as T1-less
    assert not set(S1.G5F.NO_T1_SOURCE) & {"cfg_equals_incumbent", "active_equals_incumbent", "active_seen_before",
                                           "full_seen_before"}
    # no T0 number anywhere: the node block of a T0 prompt has digits for rows/features/classes/minority
    assert "rows," in p.state and not any(ch.isdigit() for ch in p.state.split("\n")[0].split("tier T1")[1])
    # a field without a T1 source that carries a value is refused, never shown
    for k, v in (("rows_log", 7.5), ("key_code", 3), ("same_edit_count", 0.0)):
        bad = json.loads(json.dumps(steps[3]))
        bad["features"][k] = v
        with pytest.raises(S1.T1PromptError, match="no T1 source"):
            S1.t1_prompt(bad, list(steps.values()), S1.check_build(build)[NODE], budget_w=W, tokenizers=TOKS)


def test_minimised_metric_says_lower_is_better(world):
    g = g5_table(world)
    build = json.loads(json.dumps(g["build"]))
    build["nodes"][NODE]["metric_direction"] = "minimize"
    r = g["rows"][0]
    p = S1.table_prompts(g["rows"], build, budget_w=W, tokenizers=TOKS, wanted={r["proposal_id"]})
    assert "Metric: n/a (lower is better; z is signed so that positive is better)" in p[r["proposal_id"]][0].state


def test_history_lines_and_no_leak_from_the_own_or_later_rows(world):
    g = g5_table(world)
    rows, build = g["rows"], g["build"]
    camp = f"g5.history:{NODE}__s5101"
    steps = _by_step(rows, camp)
    b = 14
    p = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS, wanted={steps[b]["proposal_id"]})
    hist = p[steps[b]["proposal_id"]][0].state.split("History (oldest first):\n")[1].split("\n")
    assert len(hist) == b - 1
    assert hist[0] == f"t1: (diff); kept, z {steps[1]['delta_hat'] / SIGMA:+.2f}"
    assert hist[3] == "t4: (no tabled proposal); no valid metric"          # invalid reply: not tabled
    assert hist[11] == "t12: (no tabled proposal); no valid metric"
    assert hist[4] == "t5: (diff); not run (duplicate)"
    assert any(h.endswith("not run (inert)") for h in hist)
    assert any(", discarded, z " in h or "; discarded, z " in h for h in hist)
    base = S.render_text(p[steps[b]["proposal_id"]][0])
    # the own row's outcome fields and every later row change: the prompt does not
    mutated = []
    for r in rows:
        r2 = json.loads(json.dumps(r))
        if S1.campaign_key(r["proposal_id"]) == camp and r["budget_index"] >= b:
            r2.update(decision="kept", delta_hat=123.0, audit_group="X", wave=9, candidate_hash="Z",
                      incumbent_hash="Y", noop=not r["noop"], duplicate=not r["duplicate"], inert=True)
            if r["budget_index"] > b:
                r2["features"] = {**r2["features"], "recorded_gain_z": 99.0}
        mutated.append(r2)
    p2 = S1.table_prompts(mutated, build, budget_w=W, tokenizers=TOKS, wanted={steps[b]["proposal_id"]})
    assert S.render_text(p2[steps[b]["proposal_id"]][0]) == base
    # an earlier row's outcome does change it (the history reads the prefix)
    earlier = [dict(r, delta_hat=r["delta_hat"] + SIGMA) if r["proposal_id"] == steps[2]["proposal_id"] else r
               for r in rows]
    p3 = S1.table_prompts(earlier, build, budget_w=W, tokenizers=TOKS, wanted={steps[b]["proposal_id"]})
    assert S.render_text(p3[steps[b]["proposal_id"]][0]) != base


def test_refusals(world):
    g = g5_table(world)
    rows, build = g["rows"], g["build"]
    with pytest.raises(S1.T1PromptError, match="budget_frac_left"):
        S1.table_prompts(rows, build, budget_w=19, tokenizers=TOKS)
    bad = json.loads(json.dumps(build))
    bad["featurizer"]["version"] = "c3_features/v3"
    with pytest.raises(S1.T1PromptError, match="featurizer"):
        S1.table_prompts(rows, bad, budget_w=W, tokenizers=TOKS)
    bad = json.loads(json.dumps(build))
    bad["nodes"][NODE]["sigma_node"] = SIGMA * 2
    with pytest.raises(S1.T1PromptError, match="sigma_node"):
        S1.table_prompts(rows, bad, budget_w=W, tokenizers=TOKS)
    for k in S1.D9_COUNTS:                    # R1-T1-FEAT-DECISIONS D9 B: the counts g5_assemble STOPs on
        bad = json.loads(json.dumps(build))
        bad["nodes"][NODE]["features"][k] = 1
        with pytest.raises(S1.T1PromptError, match="D9 counts"):
            S1.table_prompts(rows, bad, budget_w=W, tokenizers=TOKS)
    bad = json.loads(json.dumps(build))
    del bad["nodes"][NODE]["features"]
    with pytest.raises(S1.T1PromptError, match="D9 counts"):
        S1.table_prompts(rows, bad, budget_w=W, tokenizers=TOKS)
    assert S1.D9_COUNTS == A.D9_COUNTS
    with pytest.raises(TypeError):                # no caller-supplied diffs: the diff is the table's (D7-DIFF B)
        S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS, diffs={})
    t0 = dict(rows[0], node="digits_mlp")
    with pytest.raises(S1.T1PromptError, match="not in build.json"):
        S1.table_prompts([t0], build, budget_w=W, tokenizers=TOKS)
    other = dict(rows[0], proposal_id=rows[0]["proposal_id"].replace("s5101", "s5102"))
    with pytest.raises(S1.T1PromptError, match="another campaign"):
        S1.t1_prompt(rows[0], [rows[0], other], S1.check_build(build)[NODE], budget_w=W, tokenizers=TOKS)


def test_table_prompts_needs_the_whole_table(world):
    """Review m1: the history reads every earlier row, so a filtered table (e.g. no-ops dropped) would silently change
    prompts; the row count per node must equal build.json's counts.rows."""
    g = g5_table(world)
    rows, build = g["rows"], g["build"]
    assert build["nodes"][NODE]["counts"]["rows"] == len(rows)
    with pytest.raises(S1.T1PromptError, match="whole G.5 table"):
        S1.table_prompts([r for r in rows if not r["noop"]], build, budget_w=W, tokenizers=TOKS)
    with pytest.raises(S1.T1PromptError, match="whole G.5 table"):
        S1.table_prompts(rows[1:], build, budget_w=W, tokenizers=TOKS, wanted={rows[5]["proposal_id"]})
    bad = json.loads(json.dumps(build))
    del bad["nodes"][NODE]["counts"]["rows"]
    with pytest.raises(S1.T1PromptError, match="row count"):
        S1.table_prompts(rows, bad, budget_w=W, tokenizers=TOKS)


# =============================================================================================== the diff
def test_diff_excerpt_rule_is_deterministic():
    diff = "--- a/train.py\r\n+++ b/train.py\r\n@@ -1 +1 @@\r\n-lr = 0.1\r\n+lr = 0.05\r\n"
    lines, rec = S1.diff_excerpt(diff)
    assert lines == ["--- a/train.py", "+++ b/train.py", "@@ -1 +1 @@", "-lr = 0.1", "+lr = 0.05"]
    assert rec["lines_total"] == rec["lines_kept"] == 5 and rec["long_lines_cut"] == 0
    assert rec["chars_kept"] == sum(len(x) + 1 for x in lines)
    assert S1.diff_excerpt(diff) == (lines, rec) and S1.diff_excerpt(diff.replace("\r\n", "\n"))[0] == lines
    # one long line: cut to exactly DIFF_LINE_MAX_CHARS, ending in the marker
    long = "+" + "x" * 500
    (cut,), rec = S1.diff_excerpt(long)
    assert len(cut) == S1.DIFF_LINE_MAX_CHARS and cut.endswith(S1.LINE_CUT) and cut.startswith("+xxx")
    assert rec["long_lines_cut"] == 1
    # the line cap and the character cap: whole lines from the top, the kept part is a prefix
    many = "\n".join(f"+line {i:03d}" for i in range(100))
    lines, rec = S1.diff_excerpt(many)
    assert lines == [f"+line {i:03d}" for i in range(S1.DIFF_MAX_LINES)] and rec["lines_total"] == 100
    wide = "\n".join("+" + str(i % 10) * 99 for i in range(30))          # 100 chars + newline per line
    lines, rec = S1.diff_excerpt(wide)
    assert len(lines) == S1.DIFF_MAX_CHARS // 101 and rec["chars_kept"] <= S1.DIFF_MAX_CHARS
    assert lines == wide.split("\n")[:len(lines)]
    assert S1.diff_excerpt("") == ([], {**S1.diff_excerpt("")[1], "lines_total": 0, "lines_kept": 0})
    assert S1.diff_block(lines, 30)[0] == f"Diff (unified; lines shown {len(lines)} of 30):"


def test_the_tables_diffs_enter_the_proposal(world):
    """D7-DIFF B: each row's own proposal_diff (here the synthetic world's one-line texts) is the excerpt shown, and
    meta.diff.sha256 is the row's proposal_diff_sha256 (multi-line diffs: test_t1_d7_diff_b)."""
    g = g5_table(world)
    rows, build = g["rows"], g["build"]
    assert build["schema"] == S1.TABLE_SCHEMA_B and S1.table_diff_mode(rows, build) is True
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    for r in rows:
        p = prompts[r["proposal_id"]][0]
        prop = p.proposal.split("\n")
        assert prop[1] == "Diff (unified; lines shown 1 of 1):" and prop[2] == r["proposal_diff"]
        assert p.meta["diff"]["lines_kept"] == 1 and p.meta["diff"]["lines_dropped_for_length"] == 0
        assert p.meta["diff"]["sha256"] == r["proposal_diff_sha256"] == \
            hashlib.sha256(r["proposal_diff"].encode()).hexdigest()


def test_length_rule_history_first_then_diff_lines(world):
    g = g5_table(world, older=True)       # a fallback-A row given a test diff: a B row takes only its own (review m1)
    rows, build = g["rows"], g["build"]
    camp = f"g5.history:{NODE}__s5101"
    steps = _by_step(rows, camp)
    row = steps[18]
    info = S1.check_build(build)[NODE]
    diff = "\n".join(f"+line {i:02d} " + "y" * 20 for i in range(30))
    dsha = S1.diff_sha256(diff)                    # the row's proposal_diff_sha256 under D7-DIFF B
    toks = {"chars": _Chars()}
    full = S1.t1_prompt(row, list(steps.values()), info, budget_w=W, tokenizers=toks, diff=diff,
                        diff_sha256_expected=dsha, max_tokens=10 ** 6)
    n_full = len(S.render_text(full))
    hist_full = full.state.split("History (oldest first):\n")[1].split("\n")
    # a budget that keeps a few history lines: the most recent ones survive
    budget = n_full - len("\n".join(hist_full[:10])) - 1 + S.FRAMING_RESERVE
    p = S1.t1_prompt(row, list(steps.values()), info, budget_w=W, tokenizers=toks, diff=diff,
                     diff_sha256_expected=dsha, max_tokens=budget)
    kept = p.state.split("History (oldest first):\n")[1].split("\n")
    assert kept == hist_full[len(hist_full) - len(kept):] and 0 < len(kept) < len(hist_full)
    assert p.meta["history_dropped"] == len(hist_full) - len(kept)
    assert len(S.render_text(p)) <= budget - S.FRAMING_RESERVE
    assert p.meta["diff"]["lines_dropped_for_length"] == 0
    # no history fits: diff lines are dropped from the bottom
    no_hist = S1.t1_prompt(row, list(steps.values()), info, budget_w=W, tokenizers=toks, diff=diff,
                           diff_sha256_expected=dsha,
                           max_tokens=n_full - len("\n".join(hist_full)) + S.FRAMING_RESERVE - 200)
    assert no_hist.state.endswith("History (oldest first):\n(none)")
    assert no_hist.meta["history_dropped"] == len(hist_full)
    dl = no_hist.meta["diff"]
    shown = no_hist.proposal.split("\n")[2:2 + dl["lines_kept"] - dl["lines_dropped_for_length"]]
    assert 0 < dl["lines_dropped_for_length"] < 30 and shown == diff.split("\n")[:len(shown)]
    assert f"lines shown {len(shown)} of 30" in no_hist.proposal
    # same inputs, same prompt
    again = S1.t1_prompt(row, list(steps.values()), info, budget_w=W, tokenizers=toks, diff=diff,
                         diff_sha256_expected=dsha,
                         max_tokens=n_full - len("\n".join(hist_full)) + S.FRAMING_RESERVE - 200)
    assert S.render_text(again) == S.render_text(no_hist) and again.meta == no_hist.meta
    with pytest.raises(S.PromptTooLong):
        S1.t1_prompt(row, list(steps.values()), info, budget_w=W, tokenizers=toks, diff=diff,
                     diff_sha256_expected=dsha, max_tokens=S.FRAMING_RESERVE + 300)


def test_longest_t1_prompt_without_diff_in_characters(world):
    """The token check needs the pool tokenizers (cluster); here a character bound: the longest no-diff T1 prompt of
    the synthetic table (step 20, 19 history lines) is well under the budget at any rate above 3 chars/token."""
    g = g5_table(world, older=True)
    prompts = S1.table_prompts(g["rows"], g["build"], budget_w=W, tokenizers=TOKS)
    longest = max(len(S.render_text(p)) for p, _ in prompts.values())
    assert longest < 3 * (S.MAX_TOKENS - S.FRAMING_RESERVE)


# =============================================================================================== the data path
def g5_source(g, *, t1=None):
    """``G5LabelSource`` on the world's train/dev label rows; the loader stands in for ``arms_freeze.load_traindev``
    (the receipted partition and its release row are tested in test_c3_release / test_c3_arms_freeze)."""
    assign = p3_split.assignment(p3_split.load())
    td = [lab for lab in g["labels"] if assign[lab["proposal_id"].split(":")[1]]["split"] != "test"]
    receipt = {"inputs": {"proposals_sha256": hashlib.sha256((g["table"] / "proposals.jsonl").read_bytes()).hexdigest(),
                          "label_block_sha256": "c" * 64},
               "outputs": {SD.PARTITION_NAME: "d" * 64}, "row_id": "R1-T1-LABELS-UNSEAL"}

    def loader(root, source, sha):
        assert source == "g5" and sha == "e" * 64
        return td, receipt
    tier1 = t1 or B.Tier1(suites={NODE: "MLAgentBench"}, modes=("history",))
    return SD.G5LabelSource("unused", receipt_sha256="e" * 64, table_rows=g["rows"], t1=tier1,
                            table_sha256=receipt["inputs"]["proposals_sha256"], loader=loader), td


def test_p4_data_path_carries_t1_rows_with_the_t1_form(world, tmp_path):
    from r1.c3 import arms_freeze as AF
    g = g5_table(world)
    rows, build = g["rows"], g["build"]
    src, td = g5_source(g)
    recs = src.label_records()
    prov = src.provenance()
    assert prov["kind"] == "g5_traindev_partition"
    assert prov["n_divergent_without_record"] == sum(lab["label_kind"] == "divergent" for lab in td) > 0
    assert any("divergent_seeds" in lab for lab in td)          # the G.5 row shape (label-seed divergences)
    assert all(r["label_kind"] in ("rule_noop", "audit") for r in recs)
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    out = tmp_path / "data"
    manifest = SD.build_sft_data(rows, src, prompts, out, split_cfg={"split_file": SD.SIGNED_SPLIT_FILE},
                                 table_record={"sha256": {"proposals.jsonl": prov["completion"]["proposals_sha256"]}})
    assert manifest["t1"] == {"prompt_version": S1.T1_PROMPT_VERSION, "featurizer_version": "g5_t1_features/1",
                              "diff_shown": True, "rows": {"train": manifest["counts"]["train"],
                                                            "val": manifest["counts"]["val"],
                                                            "val_seen": manifest["counts"]["val_seen"]}}
    assert manifest["table_matches_audit_table"] is True and manifest["counts"]["train"] > 0
    assert manifest["label_seeds"] == {"T0": None, "T1": sorted({s for lab in td for s in lab.get("seeds") or ()})}
    out_rows = [json.loads(x) for x in (out / "rows.jsonl").read_text().splitlines()]
    assert out_rows and {r["split"] for r in out_rows} <= {"train", "val", "val_seen"}
    for r in out_rows:
        p = SD.prompt_from_dict(r["prompt"])
        assert p.meta["prompt_version"] == S1.T1_PROMPT_VERSION and S.render_text(p) == \
            S.render_text(prompts[r["proposal_id"]][0])
    # the soft labels equal A3's training rows' (one label path for both arms)
    soft = {r["proposal_id"]: r["soft"] for r in AF.training_rows("g5", rows, td, t1=src.t1) if r["soft"] is not None}
    for r in out_rows:
        assert np.allclose(r["y"], soft[r["proposal_id"]])
    SD.check_t1_manifest(manifest)
    SD.check_t1_manifest(manifest, diff_shown=True)
    with pytest.raises(SD.SFTDataError, match="expected False"):
        SD.check_t1_manifest(manifest, diff_shown=False)
    with pytest.raises(SD.SFTDataError, match="does not state diff_shown"):
        SD.check_t1_manifest({**manifest, "t1": {k: v for k, v in manifest["t1"].items() if k != "diff_shown"}})
    with pytest.raises(SD.SFTDataError, match="T1 rows built with"):
        SD.check_t1_manifest({**manifest, "t1": {**manifest["t1"], "prompt_version": "trackp_prompt_t1/0"}})
    with pytest.raises(SD.SFTDataError, match="per tier"):
        SD.check_t1_manifest({**manifest, "label_seeds": list(SD.LABEL_SEEDS)})
    # a T1 row with a T0-form prompt (or the converse) is refused
    wrong = dict(prompts)
    pid = out_rows[0]["proposal_id"]
    p = prompts[pid][0]
    wrong[pid] = (DecisionPrompt(state=p.state, proposal=p.proposal, meta={"prompt_version": PROMPT_VERSION}),
                  prompts[pid][1])
    with pytest.raises(SD.SFTDataError, match="needs the trackp_prompt_t1/1 prompt form"):
        SD.build_sft_data(rows, src, wrong, tmp_path / "data2", split_cfg={"split_file": SD.SIGNED_SPLIT_FILE})


def test_g5_label_source_refuses_another_table(world):
    g = g5_table(world)
    src, _ = g5_source(g)
    src.table_sha256 = "0" * 64
    with pytest.raises(SD.SFTDataError, match="not the one its train/dev partition"):
        src.label_records()
    kw = {"receipt_sha256": "e" * 64, "table_rows": g["rows"], "t1": src.t1, "loader": src.loader}
    with pytest.raises(TypeError):                                 # review m8: the table hash is required
        SD.G5LabelSource("unused", **kw)
    for bad in (None, "", "x" * 64, "A" * 64):
        with pytest.raises(SD.SFTDataError, match="sha256 of the G.5 table"):
            SD.G5LabelSource("unused", table_sha256=bad, **kw)


def test_joint_t0_t1_build_keeps_t0_prompts_byte_identical(world, tmp_path):
    """PRE-JOINT A: one data directory over both tiers; the T0 rows carry exactly their trackp_prompt/v2 prompts."""
    g = g5_table(world)
    t0_instances = SD.p3_universe([T0_NODE])
    t0_rows, t0_prompts = t0_sweep(tmp_path, t0_instances)
    t1_prompts = S1.table_prompts(g["rows"], g["build"], budget_w=W, tokenizers=TOKS)
    src = SD.CompositeLabelSource([SD.SyntheticLabelSource(t0_rows, seed=5), g5_source(g)[0]])
    out = tmp_path / "joint"
    manifest = SD.build_sft_data(t0_rows + g["rows"], src, {**t0_prompts, **t1_prompts}, out,
                                 split_cfg={"split_file": SD.SIGNED_SPLIT_FILE})
    out_rows = [json.loads(x) for x in (out / "rows.jsonl").read_text().splitlines()]
    t0_out = [r for r in out_rows if r["node"] == T0_NODE]
    t1_out = [r for r in out_rows if r["node"] == NODE]
    assert t0_out and t1_out and manifest["t1"]["rows"]["train"] == sum(r["split"] == "train" for r in t1_out)
    for r in t0_out:
        assert r["prompt"] == json.loads(json.dumps(SD.prompt_to_dict(t0_prompts[r["proposal_id"]][0])))
        assert r["prompt"]["meta"]["prompt_version"] == PROMPT_VERSION
    assert manifest["labels"]["kind"] == "composite" and len(manifest["labels"]["parts"]) == 2
    assert manifest["label_seeds"]["T0"] == list(SD.LABEL_SEEDS) and manifest["label_seeds"]["T1"]
    with pytest.raises(SD.SFTDataError, match="labelled by two"):
        SD.CompositeLabelSource([g5_source(g)[0], g5_source(g)[0]]).label_records()


# =============================================================================================== the gate read
def test_gate_coverage_is_met_for_a_t1_node_through_the_frozen_builder(world):
    """A synthetic A5 that reads only the T1 prompts covers every non-inert T1 proposal, so the frozen builder's test
    block (TEST_SERIES: A2, oracle, A3, A5) is computed for the T1 node; a missing A5 prediction is refused."""
    from r1.tests import test_gate_input_builder as TB
    s = world["spec"]
    d, extra = g1b_run(world, NODE)            # READY 97's signature: the copies go beside the world's summary (D6 A)
    row = bind_summary(world, d, extra)
    g = g5_table(world, test=True)
    rows, build = g["rows"], g["build"]
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)

    def fake_a5(prompt):                     # a deterministic stand-in for Kev: 12 probabilities from the text
        h = hashlib.sha256(S.render_text(prompt).encode()).digest()
        z = np.frombuffer(h[:12], dtype=np.uint8).astype(float) / 64.0
        e = np.exp(z - z.max())
        return list(e / e.sum())
    (sweep2, sweep1), preds, t0_noise = TB._world()
    need = [r["proposal_id"] for r in rows if not is_noop(r)]
    preds["A5"].update({pid: fake_a5(prompts[pid][0]) for pid in need})
    preds["A3"].update({pid: [1 / 12] * 12 for pid in need})
    t1 = B.Tier1(suites={NODE: "MLAgentBench"}, modes=("history",))
    t1_noise = N.builder_noise(N.derive(s, row, {NODE: d}))
    assert t1_noise[NODE]["sigma_node"] == build["nodes"][NODE]["sigma_node"] == rows[0]["sigma_node"]   # D6-σ B
    noise = N.merge_noise(t0_noise, t1_noise)
    sources = [sweep2, sweep1, B.Source("g5", rows, g["labels"], g["evals"])]
    gi, rep = B.build(sources, preds, noise, t0_nodes=B.SEVEN_T0, t1=t1)
    node = next(n for n in gi["nodes"] if n["node"] == NODE)
    assert node["tier"] == "T1" and set(B.TEST_SERIES) <= set(node["test"]) and rep["t1_not_supplied"] == {}
    assert node["test"]["instance_ids"]
    gone = next(pid for pid in need if _split(next(r for r in rows if r["proposal_id"] == pid)) == "test")
    short = {**preds, "A5": {k: v for k, v in preds["A5"].items() if k != gone}}
    with pytest.raises(B.BuilderError, match="A5: no prediction"):     # the full test population (PRE-DUP secondary)
        B.build(sources, short, noise, t0_nodes=B.SEVEN_T0, t1=t1, population="full")
