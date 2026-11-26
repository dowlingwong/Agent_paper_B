"""D7-DIFF B (R1-T1-A5-DECISIONS): the G.5 table carries each step's own proposal diff, A5's T1 prompt form shows a
bounded excerpt of it bound by sha256, fallback A (a table without the field) stays possible, and the cluster's
history-drop report. Synthetic harness-shaped ledgers only (the world of ``test_t1_g5_seal``); no label, evaluation
value, real ledger or tokenizer of the pool is read. ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from r1.tests.test_t1_g5_seal import (A, NODE, Engine, assemble_world, lock_for, node_git,  # noqa: F401
                                      world)
from r1.tests.test_trackp_t1_prompt import (T0_GOLDEN, T0_NODE, TOKS, W, _by_step, _Chars,  # noqa: F401
                                            _control_plane_skip, _split, g5_source, g5_table, older_table,
                                            t0_golden_build, t0_sweep)

import g1b_tasl as G  # noqa: E402  (sweep2/t1_tasl is on sys.path through test_t1_g5_seal)

from r1.c3 import arms_freeze as AF
from r1.c3 import p3_split
from r1.c3 import release as R
from r1.c3.train import serialize as S
from r1.c3.train import serialize_t1 as S1
from r1.c3.train import sft_data as SD
from r1.c3.train.types import PROMPT_VERSION

# sha256 of the synthetic table's proposals.jsonl as the base commit's assembly writes it (g5_assemble.py at
# 3024db3f, origin/main before this unit, run on this test's world and Engine by /tmp/d7bdev/scripts/
# test_base_vs_tip.py): a fallback-A table. The B table less its two diff fields must give exactly these bytes.
BASE_A_PROPOSALS_SHA256 = "25f0ab7832b9c57ae25d740d82541306946a92f9368860790e7f72d5d71aa798"

D1 = ("--- a/train.py\n+++ b/train.py\n@@ -12,7 +12,7 @@ def train(model):\n def train(model):\n-    lr = 3e-4\n"
      "+    lr = 1e-3\n     return fit(model, lr)\n")


def make_diff(k: int, wave: int, s: int) -> str:
    """The manager's diff of step s of instance k (synthetic). Hunk headers carry wrong line counts, as G.4's
    malformed_hunk refusals did (R1-G5-DIFF-RECOUNT): the table keeps the text as written."""
    if s == 1:
        return D1                                           # one kept diff, the same in every instance
    if s == 20:
        return ""                                           # an empty diff: the harness calls it inert
    if s == 6:                                              # long: 60 lines, one of 300 characters, CRLF ends
        body = [f"+    w_{wave}{k}_{i:02d} = {i}" for i in range(56)]
        body[3] = "+    # " + "z" * 293
        return "\r\n".join(["--- a/model.py", "+++ b/model.py", "@@ -40,9 +40,9 @@"] + body + [" pass"]) + "\r\n"
    if s == 7:                                              # the manager quotes a campaign value it was shown
        return (f"--- a/train.py\n+++ b/train.py\n@@ -20,9 +20,9 @@\n # step 2 gave val 0.45 (instance {k})\n"
                f"-    epochs = 5\n+    epochs = 8\n     run()\n")
    return (f"--- a/train.py\n+++ b/train.py\n@@ -20,9 +20,9 @@\n # marker x_{wave}{k}_{s}\n-    a = {s}\n"
            f"+    a = {s + 1}\n     run()\n")


def recounted(text: str) -> str:
    """Stands in for a copy the harness applied after recomputing hunk-header counts (``git apply --recount``)."""
    return text.replace("@@ -20,9 +20,9 @@", "@@ -20,4 +20,4 @@").replace("@@ -12,7 +12,7 @@", "@@ -12,4 +12,4 @@")


class DiffEngine(Engine):
    """The fake engines of test_t1_g5_seal, with multi-line manager diffs in ``proposal.diff`` and, for executed
    runs, a diff provenance whose ``diff_text`` is a recounted copy (never the table's text). ``drop_diff_step`` /
    ``bad_diff_step``: a tabled line without ``proposal.diff`` / with a text UTF-8 cannot encode."""

    def __init__(self, spec, *, drop_diff_step=None, bad_diff_step=None, **kw):
        super().__init__(spec, **kw)
        self.drop_diff_step, self.bad_diff_step = drop_diff_step, bad_diff_step

    def __call__(self, argv, **kw):
        res = super().__call__(argv, **kw)
        if "--campaign" in argv:
            out = Path(argv[argv.index("--out") + 1])
            f = json.loads(Path(argv[argv.index("--campaign") + 1]).read_text())
            for inst in f["instances"]:
                p = next(out.glob(f"instance_{inst['instance']}_*")) / "campaign_ledger.jsonl"
                lines = []
                for line in p.read_text().splitlines():
                    e = json.loads(line)
                    s = e.get("step")
                    if "proposal" in e:
                        text = make_diff(inst["instance"], f["wave"], s)
                        e["proposal"] = {"schema_version": "manager_proposal/v2-diff", "rationale": "r",
                                         "summary": "s", "objective": "o", "diff": text}
                        run = e["runs"][-1]
                        if run.get("executed"):
                            rc = recounted(text)
                            run["diff"] = {"status": "applied", "diff_text": rc,
                                           "diff_sha256": hashlib.sha256(rc.encode()).hexdigest()}
                        if s == self.drop_diff_step:
                            del e["proposal"]["diff"]
                        if s == self.bad_diff_step:
                            e["proposal"]["diff"] = "\ud800"
                    lines.append(json.dumps(e))
                p.write_text("\n".join(lines) + "\n")
        return res


def diff_table(world, engine=None, *, test=False):
    """The assembled D7-DIFF B table of the DiffEngine world, in the shape of ``g5_table``."""
    s = world["spec"]
    engine = engine or DiffEngine(s, divergent_label={"S12_6", "S13_6", "S23_6"}, divergent_eval={"S13_7"})
    table, ev, _ = assemble_world(world, engine)
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    if test:
        A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()]
    labels = [json.loads(x) for x in (ev / "label_block.jsonl").read_text().splitlines()]
    build = json.loads((table / "build.json").read_text())
    return {"rows": rows, "labels": labels, "evals": [], "build": build, "table": table, "evidence": ev}


def _k_s(row):
    """(instance k, step) of a row of the synthetic world (seed 5100 + k)."""
    return row["instance_seed"] - 5100, row["budget_index"]


# =============================================================================================== the table
def test_b_rows_carry_their_own_proposal_diff_and_re_derive(world):
    g = diff_table(world)
    rows, build, table, ev = g["rows"], g["build"], g["table"], g["evidence"]
    assert build["schema"] == A.TABLE_SCHEMA == S1.TABLE_SCHEMA_B == "g5_t1_table/2"
    assert build["proposal_diff"] == A.PROPOSAL_DIFF == S1.PROPOSAL_DIFF
    assert (A.DIFF_FIELD, A.DIFF_SHA_FIELD) == S1.DIFF_FIELDS == (SD.T1_DIFF_FIELD, SD.T1_DIFF_SHA_FIELD)
    assert len(rows) == 12 * 18 and {r["budget_index"] for r in rows}.isdisjoint({4, 12})   # invalid: not tabled
    for r in rows:
        k, s = _k_s(r)
        wave = r["wave"]
        want = make_diff(k, wave, s)
        assert r["proposal_diff"] == want, r["proposal_id"]          # the manager's text, byte for byte
        assert r["proposal_diff_sha256"] == hashlib.sha256(want.encode()).hexdigest() == A.diff_sha256(want)
        if r["decision"] in ("kept", "discarded", "discarded_divergent") and "@@ -20,9" in want:
            assert r["proposal_diff"] != recounted(want)             # not the applied (recounted) copy
    kinds = {r["decision"] for r in rows}
    assert {"not_run_inert", "not_run_duplicate"} <= kinds           # not-run rows carry their diff too
    assert any(r["proposal_diff"] == "" and r["noop"] for r in rows)  # an empty diff is an inert diff
    # the table stays ASCII JSON (non-ASCII would be escaped) and no row carries a label or evaluation value
    raw = (table / "proposals.jsonl").read_bytes()
    raw.decode("ascii")
    AF.check_table_rows(rows)
    # the test stage and the release step's integrity check re-derive the table byte-identically ...
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    assert (table / "proposals.jsonl").read_bytes() == raw
    with R.integrity_context():
        out = A.verify_evidence(table, ev, test=True, lock=lock_for(world, "traindev", "test"), git=node_git(),
                                spec_path=world["sp"])
    assert out["pass"] and out["completion"]["proposals_sha256"] == hashlib.sha256(raw).hexdigest()
    # ... and refuse a table whose diff text was changed
    bad = raw.replace(b"marker x_", b"marker y_", 1)
    assert bad != raw
    (table / "proposals.jsonl").write_bytes(bad)
    with R.integrity_context(), pytest.raises(G.Stop, match="proposals.jsonl differs"):
        A.verify_evidence(table, ev, test=True, lock=lock_for(world, "traindev", "test"), git=node_git(),
                          spec_path=world["sp"])
    (table / "proposals.jsonl").write_bytes(raw)


@pytest.mark.parametrize("kw,match", [({"drop_diff_step": 5}, "no text proposal.diff"),
                                      ({"bad_diff_step": 2}, "not encodable")])
def test_assembly_stops_on_a_tabled_line_without_a_usable_diff(world, kw, match):
    s = world["spec"]
    table, ev, _ = assemble_world(world, DiffEngine(s, **kw))
    with pytest.raises(G.Stop, match=match):
        A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    assert not table.exists() and not ev.exists()


def test_the_row_diff_reads_nothing_post_execution():
    """``proposal_diff`` comes from the line's ``proposal`` only: the outcome, the run records (the applied copy in
    the diff provenance) and the decision do not change it."""
    text = make_diff(3, 1, 10)
    base = {"step": 10, "proposal": {"diff": text}}
    for extra in ({"final_outcome": {"kind": "ok", "value": 0.9}, "decision": "kept"},
                  {"final_outcome": {"kind": "divergent"}, "decision": "discarded_divergent"},
                  {"runs": [{"diff": {"diff_text": recounted(text)}, "outcome": {"value": 0.1}}]}):
        assert A.proposal_diff({**base, **extra}, "x") == (text, hashlib.sha256(text.encode()).hexdigest())


def test_fallback_a_table_is_the_base_commits_table(world):
    """Fallback A is the table the assembly wrote before this unit: the B rows less proposal_diff and
    proposal_diff_sha256 are the base commit's proposals.jsonl byte for byte (golden hash), its build.json is
    g5_t1_table/1 without the record, and the form renders it as A."""
    g = g5_table(world)
    rows, build = older_table(g["rows"], g["build"])
    assert hashlib.sha256(A._lines(rows)).hexdigest() == BASE_A_PROPOSALS_SHA256
    assert build["schema"] == S1.TABLE_SCHEMA_A and "proposal_diff" not in build
    assert S1.table_diff_mode(rows, build) is False
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    assert all(p.meta["diff"] is None and "\nDiff: n/a (not carried by the G.5 table)\n" in p.proposal
               for p, _ in prompts.values())


# =============================================================================================== the form
def test_prompts_show_the_rows_own_excerpt_bound_by_sha256(world):
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    by_id = {r["proposal_id"]: r for r in rows}
    for pid, (p, _) in prompts.items():
        r = by_id[pid]
        kept, rec = S1.diff_excerpt(r["proposal_diff"])
        prop = p.proposal.split("\n")
        assert prop[0] == "Edit: n/a (code-level diff; no structured key edit)"
        assert prop[1] == f"Diff (unified; lines shown {len(kept)} of {rec['lines_total']}):"
        assert prop[2:2 + len(kept)] == kept
        assert prop[2 + len(kept)] == "Edited key: n/a (no structured key); key type: n/a"
        assert p.meta["diff"]["sha256"] == r["proposal_diff_sha256"]
        # only the step's own diff: no earlier or later step's text, history lines show "(diff)"
        k, s = _k_s(r)
        text = S.render_text(p)
        for other in range(2, 20):                # the steps whose diff carries a marker (make_diff)
            if other != s and other not in (4, 6, 7, 12):
                assert f"marker x_{r['wave']}{k}_{other}" not in text
        if s not in (1, 6, 7, 20):
            assert f"marker x_{r['wave']}{k}_{s}" in text
    # the empty diff of an inert step
    inert = next(r for r in rows if r["proposal_diff"] == "")
    assert "\nDiff (unified; lines shown 0 of 0):\nEdited key:" in prompts[inert["proposal_id"]][0].proposal
    # D7-LEN's excerpt rule on the long diff: 40 of 60 lines at most, the 300-character line cut, CRLF normalised
    long = next(r for r in rows if r["budget_index"] == 6)
    p = prompts[long["proposal_id"]][0]
    d = p.meta["diff"]
    assert d["lines_total"] == 60 and d["lines_kept"] <= S1.DIFF_MAX_LINES and d["chars_kept"] <= S1.DIFF_MAX_CHARS
    assert d["long_lines_cut"] == 1 and "\r" not in p.proposal
    cut = [ln for ln in p.proposal.split("\n") if ln.endswith(S1.LINE_CUT)]
    assert len(cut) == 1 and len(cut[0]) == S1.DIFF_LINE_MAX_CHARS
    assert f"Diff (unified; lines shown {d['lines_kept']} of 60):" in p.proposal


def test_sha256_binding(world):
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    info = S1.check_build(build)[NODE]
    camp = f"g5.history:{NODE}__s5101"
    steps = _by_step(rows, camp)
    r = steps[3]
    # the form passes the row's text and sha256; a text whose sha256 differs is refused
    with pytest.raises(S1.T1PromptError, match="binding"):
        S1.t1_prompt(r, list(steps.values()), info, budget_w=W, tokenizers=TOKS, diff=r["proposal_diff"] + " ",
                     diff_sha256_expected=r["proposal_diff_sha256"])
    with pytest.raises(S1.T1PromptError, match="binding"):
        S1.t1_prompt(r, list(steps.values()), info, budget_w=W, tokenizers=TOKS, diff=r["proposal_diff"])
    with pytest.raises(S1.T1PromptError, match="without its diff text"):
        S1.t1_prompt(r, list(steps.values()), info, budget_w=W, tokenizers=TOKS,
                     diff_sha256_expected=r["proposal_diff_sha256"])
    # a table row whose text and sha256 disagree is refused before anything is rendered
    for change in ({"proposal_diff": r["proposal_diff"] + "x"}, {"proposal_diff_sha256": "0" * 64},
                   {"proposal_diff_sha256": r["proposal_diff_sha256"].upper()}, {"proposal_diff": None}):
        bad = [dict(x, **change) if x["proposal_id"] == r["proposal_id"] else x for x in rows]
        with pytest.raises(S1.T1PromptError, match="sha256 is not"):
            S1.table_prompts(bad, build, budget_w=W, tokenizers=TOKS)
    # the data build checks the binding again on every T1 row it writes
    prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    src, _ = g5_source(g)
    p = prompts[r["proposal_id"]][0]
    forged = dict(prompts)
    forged[r["proposal_id"]] = (S1.DecisionPrompt(state=p.state, proposal=p.proposal, question=p.question,
                                                  options=p.options, group=p.group,
                                                  meta={**p.meta, "diff": {**p.meta["diff"], "sha256": "0" * 64}}),
                                prompts[r["proposal_id"]][1])
    import tempfile
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(SD.SFTDataError, match="diff sha256"):
        SD.build_sft_data(rows, src, forged, Path(tmp) / "d", split_cfg={"split_file": SD.SIGNED_SPLIT_FILE})


def test_a_row_is_rendered_only_with_its_own_diff(world):
    """Review m1: t1_prompt checks the text against the row's own proposal_diff_sha256 too, so row Y's diff with
    row Y's sha256 cannot be rendered on row X, and a B row cannot be rendered without its diff."""
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    info = S1.check_build(build)[NODE]
    steps = _by_step(rows, f"g5.history:{NODE}__s5101")
    x, y = steps[3], steps[6]
    assert x["proposal_diff_sha256"] != y["proposal_diff_sha256"]
    with pytest.raises(S1.T1PromptError, match="binding"):
        S1.t1_prompt(x, list(steps.values()), info, budget_w=W, tokenizers=TOKS, diff=y["proposal_diff"],
                     diff_sha256_expected=y["proposal_diff_sha256"])
    with pytest.raises(S1.T1PromptError, match="no diff was given"):
        S1.t1_prompt(x, list(steps.values()), info, budget_w=W, tokenizers=TOKS)
    ok = S1.t1_prompt(x, list(steps.values()), info, budget_w=W, tokenizers=TOKS, diff=x["proposal_diff"],
                      diff_sha256_expected=x["proposal_diff_sha256"])
    assert ok.meta["diff"]["sha256"] == x["proposal_diff_sha256"]


def test_a_lone_surrogate_diff_is_refused_with_a_fixed_message(world):
    """Review m3: a lone surrogate in U+DC80-U+DCFF hashes under surrogateescape but cannot be written as UTF-8, so
    the form refuses it, in table_diff_mode and in t1_prompt, with a message that quotes no text."""
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    info = S1.check_build(build)[NODE]
    steps = _by_step(rows, f"g5.history:{NODE}__s5101")
    x = steps[3]
    text = x["proposal_diff"] + "+s = '\udc80'\n"
    sha = S1.diff_sha256(text)                     # hashable: surrogateescape maps U+DC80 to byte 0x80
    bad = dict(x, proposal_diff=text, proposal_diff_sha256=sha)
    table = [bad if r["proposal_id"] == x["proposal_id"] else r for r in rows]
    with pytest.raises(S1.T1PromptError) as exc:
        S1.table_diff_mode(table, build)
    assert S1.SURROGATE_REFUSAL in str(exc.value) and "\udc80" not in str(exc.value)
    with pytest.raises(S1.T1PromptError, match="lone surrogate"):
        S1.table_prompts(table, build, budget_w=W, tokenizers=TOKS)
    with pytest.raises(S1.T1PromptError, match="lone surrogate"):
        S1.t1_prompt(bad, list(steps.values()), info, budget_w=W, tokenizers=TOKS, diff=text,
                     diff_sha256_expected=sha)
    with pytest.raises(S1.T1PromptError, match="not encodable"):     # other lone surrogates fail at the hash
        S1.diff_sha256("\ud800")


def test_mixing_a_and_b_is_refused(world, tmp_path):
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    a_rows, a_build = older_table(rows, build)
    # in the table: a B row without its field, an A row with one, a build record without the schema or vice versa
    with pytest.raises(S1.T1PromptError, match="A and B mixed"):
        S1.table_prompts([{k: v for k, v in rows[0].items() if k != "proposal_diff"}] + rows[1:], build,
                         budget_w=W, tokenizers=TOKS)
    with pytest.raises(S1.T1PromptError, match="A and B mixed"):
        S1.table_prompts([dict(a_rows[0], proposal_diff_sha256=rows[0]["proposal_diff_sha256"])] + a_rows[1:],
                         a_build, budget_w=W, tokenizers=TOKS)
    for bad in ({**build, "schema": S1.TABLE_SCHEMA_A}, {**a_build, "schema": S1.TABLE_SCHEMA_B},
                {**build, "proposal_diff": {**build["proposal_diff"], "source": "the applied copy"}},
                {**build, "schema": "g5_t1_table/3"}, {k: v for k, v in build.items() if k != "schema"}):
        with pytest.raises(S1.T1PromptError, match="build.json"):
            S1.table_prompts(rows, bad, budget_w=W, tokenizers=TOKS)
    # in the data build: B rows with A prompts (or A rows with B prompts) are refused
    src, _ = g5_source(g)
    a_prompts = S1.table_prompts(a_rows, a_build, budget_w=W, tokenizers=TOKS)
    with pytest.raises(SD.SFTDataError, match="does not show a diff but its table row carries"):
        SD.build_sft_data(rows, src, a_prompts, tmp_path / "x", split_cfg={"split_file": SD.SIGNED_SPLIT_FILE})
    b_prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    with pytest.raises(SD.SFTDataError, match="shows a diff but its table row does not carry"):
        SD.build_sft_data(a_rows, src, b_prompts, tmp_path / "y", split_cfg={"split_file": SD.SIGNED_SPLIT_FILE})
    # one build, two tables (some prompts with, some without a diff): refused
    half = {pid: (a_prompts if i % 2 else b_prompts)[pid] for i, pid in enumerate(sorted(b_prompts))}
    with pytest.raises(SD.SFTDataError, match="shows a diff|does not show a diff|all or none"):
        SD.build_sft_data(rows, src, half, tmp_path / "z", split_cfg={"split_file": SD.SIGNED_SPLIT_FILE})


def test_d7_len_history_first_then_diff_lines(world):
    """D7-LEN as built: the excerpt (1,200 characters, 40 lines, 160 per line) first, then the token budget, with
    history cut before diff lines (character tokenizer standing in for the pool)."""
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    camp = f"g5.history:{NODE}__s5101"
    steps = _by_step(rows, camp)
    toks = {"chars": _Chars()}
    r = steps[6]                                  # the long diff at step 6, five history lines
    pid = r["proposal_id"]
    full = S1.table_prompts(rows, build, budget_w=W, tokenizers=toks, wanted={pid}, max_tokens=10 ** 6)[pid][0]
    n_full = len(S.render_text(full))
    assert full.meta["history_dropped"] == 0 and full.meta["diff"]["lines_dropped_for_length"] == 0
    hist = full.state.split("History (oldest first):\n")[1].split("\n")
    assert len(hist) == 5 and hist[0].startswith("t1: (diff); kept")
    one = len(hist[0]) + 1                        # dropping the oldest line saves this many characters
    p = S1.table_prompts(rows, build, budget_w=W, tokenizers=toks, wanted={pid},
                         max_tokens=n_full - one + S.FRAMING_RESERVE)[pid][0]
    assert p.meta["history_dropped"] == 1 and p.meta["diff"]["lines_dropped_for_length"] == 0
    tight = n_full - len("\n".join(hist)) + S.FRAMING_RESERVE - 300
    p = S1.table_prompts(rows, build, budget_w=W, tokenizers=toks, wanted={pid}, max_tokens=tight)[pid][0]
    assert p.meta["history_dropped"] == 5 and p.meta["diff"]["lines_dropped_for_length"] > 0
    assert len(S.render_text(p)) <= tight - S.FRAMING_RESERVE
    with pytest.raises(S.PromptTooLong):
        S1.table_prompts(rows, build, budget_w=W, tokenizers=toks, wanted={pid}, max_tokens=S.FRAMING_RESERVE + 200)


def test_a_diff_shows_what_the_manager_wrote_and_nothing_post_execution(world):
    """The diff is the manager's code change: it can hold any text the manager wrote, here a campaign value it was
    shown (step 7: "val 0.45"), and the form shows it as written (no filter). It is pre-execution: the own row's
    outcome fields and every later row (their diffs included) do not change the prompt; nor do the diffs of earlier
    rows of the same campaign (history lines show "(diff)") or anything in other campaigns' rows; the own diff does."""
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    camp = f"g5.history:{NODE}__s5101"
    steps = _by_step(rows, camp)
    pid = steps[7]["proposal_id"]
    base = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS, wanted={pid})[pid][0]
    assert "\n # step 2 gave val 0.45 (instance 1)\n" in base.proposal
    mutated = []
    for r in rows:
        r2 = json.loads(json.dumps(r))
        if S1.campaign_key(r["proposal_id"]) == camp and r["budget_index"] >= 7:
            r2.update(decision="kept", delta_hat=1.0, audit_group="X", wave=9, candidate_hash="Z")
            if r["budget_index"] > 7:
                d = r2["proposal_diff"] + "\n+leak = 'later step outcome'\n"
                r2.update(proposal_diff=d, proposal_diff_sha256=S1.diff_sha256(d))
        mutated.append(r2)
    p2 = S1.table_prompts(mutated, build, budget_w=W, tokenizers=TOKS, wanted={pid})[pid][0]
    assert S.render_text(p2) == S.render_text(base) and p2.meta == base.meta
    # earlier rows of the same campaign: their diff text (not their outcome, which the history shows as z)
    # and every row of every other campaign (diff, outcome, decision, hashes)
    mutated2 = []
    for r in rows:
        r2 = json.loads(json.dumps(r))
        same = S1.campaign_key(r["proposal_id"]) == camp
        if (same and r["budget_index"] < 7) or not same:
            d = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 'changed elsewhere'\n"
            r2.update(proposal_diff=d, proposal_diff_sha256=S1.diff_sha256(d))
        if not same:
            r2.update(decision="kept", delta_hat=5.0, audit_group="Q", candidate_hash="W", incumbent_hash="V")
        mutated2.append(r2)
    p4 = S1.table_prompts(mutated2, build, budget_w=W, tokenizers=TOKS, wanted={pid})[pid][0]
    assert S.render_text(p4) == S.render_text(base) and p4.meta == base.meta
    assert "changed elsewhere" not in S.render_text(p4)
    own = [dict(r, proposal_diff=r["proposal_diff"] + "+b = 2\n",
                proposal_diff_sha256=S1.diff_sha256(r["proposal_diff"] + "+b = 2\n"))
           if r["proposal_id"] == pid else r for r in rows]
    p3 = S1.table_prompts(own, build, budget_w=W, tokenizers=TOKS, wanted={pid})[pid][0]
    assert S.render_text(p3) != S.render_text(base) and p3.meta["diff"]["sha256"] != base.meta["diff"]["sha256"]


# =============================================================================================== the data path
def test_end_to_end_assembly_table_prompts_joint_t0_t1_build(world, tmp_path):
    """Synthetic harness-shaped ledgers with diffs -> the assembly -> the table -> prompts with excerpts -> a joint
    T0+T1 data build (PRE-JOINT A): diff_shown true, each T1 prompt bound to its row's sha256, T0 prompts unchanged."""
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    t0_rows, t0_prompts = t0_sweep(tmp_path, SD.p3_universe([T0_NODE]))
    t1_prompts = S1.table_prompts(rows, build, budget_w=W, tokenizers=TOKS)
    assert S1.missing_for_gate(rows, t1_prompts) == []
    src = SD.CompositeLabelSource([SD.SyntheticLabelSource(t0_rows, seed=5), g5_source(g)[0]])
    out = tmp_path / "joint"
    manifest = SD.build_sft_data(t0_rows + rows, src, {**t0_prompts, **t1_prompts}, out,
                                 split_cfg={"split_file": SD.SIGNED_SPLIT_FILE})
    assert manifest["t1"]["diff_shown"] is True and manifest["t1"]["rows"]["train"] > 0
    SD.check_t1_manifest(manifest, diff_shown=True)
    by_id = {r["proposal_id"]: r for r in rows}
    out_rows = [json.loads(x) for x in (out / "rows.jsonl").read_text().splitlines()]
    t1_out = [r for r in out_rows if r["node"] == NODE]
    assert t1_out and all(_split(by_id[r["proposal_id"]]) != "test" for r in t1_out)
    for r in t1_out:
        meta = r["prompt"]["meta"]
        assert meta["diff"]["sha256"] == by_id[r["proposal_id"]]["proposal_diff_sha256"]
        assert "Diff (unified; lines shown " in r["prompt"]["proposal"]
    for r in out_rows:
        if r["node"] == T0_NODE:
            assert r["prompt"] == json.loads(json.dumps(SD.prompt_to_dict(t0_prompts[r["proposal_id"]][0])))
            assert r["prompt"]["meta"]["prompt_version"] == PROMPT_VERSION


def test_fallback_a_data_build_states_diff_shown_false(world, tmp_path):
    g = g5_table(world, older=True)
    src, _ = g5_source(g)
    prompts = S1.table_prompts(g["rows"], g["build"], budget_w=W, tokenizers=TOKS)
    manifest = SD.build_sft_data(g["rows"], src, prompts, tmp_path / "a", split_cfg={"split_file":
                                                                                     SD.SIGNED_SPLIT_FILE})
    assert manifest["t1"]["diff_shown"] is False
    SD.check_t1_manifest(manifest, diff_shown=False)
    with pytest.raises(SD.SFTDataError, match="expected True"):
        SD.check_t1_manifest(manifest, diff_shown=True)


def test_t0_build_is_unchanged(tmp_path):
    """T0 byte identity (the golden hashes of test_trackp_t1_prompt, computed on 14f19a09 and re-checked on
    3024db3f): this unit changes no T0 path."""
    got, manifest = t0_golden_build(tmp_path)
    assert got == T0_GOLDEN and "t1" not in manifest


# =============================================================================================== the report
def _expected_counts(rows, build, toks, max_tokens, splits=("train", "dev")):
    by_campaign = {}
    for r in rows:
        by_campaign.setdefault(S1.campaign_key(r["proposal_id"]), []).append(r)
    info = S1.check_build(build)
    want = {"prompts": 0, "prompts_history_dropped": 0, "history_lines_dropped": 0, "prompts_too_long": 0,
            "diff_lines_dropped_for_length": 0}
    for r in rows:
        if _split(r) not in splits:
            continue
        want["prompts"] += 1
        try:
            p = S1.t1_prompt(r, by_campaign[S1.campaign_key(r["proposal_id"])], info[r["node"]], budget_w=W,
                             tokenizers=toks, diff=r.get("proposal_diff"),
                             diff_sha256_expected=r.get("proposal_diff_sha256"), max_tokens=max_tokens)
        except S.PromptTooLong:
            want["prompts_too_long"] += 1
            continue
        want["prompts_history_dropped"] += p.meta["history_dropped"] > 0
        want["history_lines_dropped"] += p.meta["history_dropped"]
        want["diff_lines_dropped_for_length"] += (p.meta["diff"] or {}).get("lines_dropped_for_length", 0)
    return want


def test_history_drop_report_counts_train_and_dev_only(world):
    g = diff_table(world)
    rows, build = g["rows"], g["build"]
    toks = {"chars": _Chars()}
    n_td = sum(_split(r) in ("train", "dev") for r in rows)
    assert 0 < n_td < len(rows)                               # the table has test-instance rows; not counted
    for max_tokens in (10 ** 6, 2500, 2000, 1500):           # the synthetic prompts are 1,684 to 2,608 characters
        rep = S1.history_drop_report(rows, build, budget_w=W, tokenizers=toks, max_tokens=max_tokens)
        want = _expected_counts(rows, build, toks, max_tokens)
        assert {k: rep["total"][k] for k in want} == want and rep["total"]["prompts"] == n_td
        assert rep["nodes"][NODE]["prompts"] == n_td and rep["d7_diff"] == "B" and rep["splits"] == ["dev", "train"]
        assert rep["stop"] is (want["prompts_too_long"] > 0)
        assert sum(rep["nodes"][NODE]["history_dropped_distribution"].values()) == n_td - want["prompts_too_long"]
        assert rep["label"] == "ENGINEERING_ONLY" and rep["proposals_sha256"] == build["proposals_sha256"]
    assert S1.history_drop_report(rows, build, budget_w=W, tokenizers=toks, max_tokens=10 ** 6)["total"][
        "prompts_history_dropped"] == 0
    tight = S1.history_drop_report(rows, build, budget_w=W, tokenizers=toks, max_tokens=2000)["total"]
    assert tight["prompts_history_dropped"] > 0 and tight["prompts_diff_lines_dropped_for_length"] > 0
    assert tight["prompts_too_long"] == 0
    assert S1.history_drop_report(rows, build, budget_w=W, tokenizers=toks, max_tokens=1500)["stop"] is True
    assert S1.history_drop_report(rows, build, budget_w=W, tokenizers=toks, max_tokens=10 ** 6)["total"][
        "prompts_diff_cut_by_excerpt"] == sum(_split(r) != "test" and r["budget_index"] == 6 for r in rows) > 0
    # fallback A: the same report, no diff counts
    a_rows, a_build = older_table(rows, build)
    rep_a = S1.history_drop_report(a_rows, a_build, budget_w=W, tokenizers=toks)
    assert rep_a["d7_diff"] == "A" and rep_a["total"]["diff_lines_dropped_for_length"] == 0
    for bad in (("test",), ("train", "dev", "test"), ()):
        with pytest.raises(S1.T1PromptError, match="train and dev instances only"):
            S1.history_drop_report(rows, build, budget_w=W, tokenizers=toks, splits=bad)


def test_history_drop_report_cli(world, tmp_path, monkeypatch):
    g = diff_table(world)
    table = g["table"]
    table_sha = hashlib.sha256((table / "proposals.jsonl").read_bytes()).hexdigest()
    part = tmp_path / "release" / "g5" / "traindev"
    part.mkdir(parents=True)
    receipt = {"schema": R.RECEIPT_SCHEMA, "source": "g5", "stage": "traindev",
               "outputs": {"label_block.traindev.jsonl": "d" * 64}, "inputs": {"proposals_sha256": table_sha}}
    (part / "RECEIPT.json").write_text(json.dumps(receipt))
    class _Third:                                 # about 3 characters per token, like the pool (cluster only)
        def __call__(self, text, add_special_tokens=False):
            return {"input_ids": list(range(len(text) // 3))}
    monkeypatch.setattr(S1, "pool_tokenizers", lambda: {"third": _Third()})
    out = tmp_path / "T1_HISTORY_DROP.json"
    args = ["history-drop-report", "--table", str(table), "--receipt", str(part / "RECEIPT.json"),
            "--budget-w", str(W), "--out", str(out)]
    assert S1.main(args) == S1.EXIT_OK == 0
    rep = json.loads(out.read_text())
    assert rep["schema"] == S1.REPORT_SCHEMA and rep["tokenizers"] == ["third"] and rep["stop"] is False
    assert rep["receipt_sha256"] == hashlib.sha256((part / "RECEIPT.json").read_bytes()).hexdigest()
    text = json.dumps(rep)                         # counts only: no prompt text, no diff text, no value
    assert S1.QUESTION not in text and "marker x_" not in text and "Diff (unified" not in text
    assert all(isinstance(v, int) for c in [rep["total"], *rep["nodes"].values()] for k, v in c.items()
               if k != "history_dropped_distribution")
    before = out.read_bytes()
    assert S1.main(args) == S1.EXIT_REFUSED == 2 and out.read_bytes() == before   # written once (review m2)
    for change, match in (({"inputs": {"proposals_sha256": "0" * 64}}, "not the table"),
                          ({"stage": "test"}, "train/dev release receipt"),
                          ({"outputs": {"label_block.test.jsonl": "d" * 64}}, "train/dev release receipt")):
        (part / "RECEIPT.json").write_text(json.dumps({**receipt, **change}))
        with pytest.raises(S1.T1PromptError, match=match):
            S1.read_released_table(table, part / "RECEIPT.json")
    (part / "RECEIPT.json").write_text(json.dumps(receipt))
    with pytest.raises(S1.T1PromptError, match="evidence or partition"):
        S1.read_released_table(g["evidence"], part / "RECEIPT.json")
    # review m2: through the CLI every refusal is exit 2 and writes nothing
    n = 0
    for change in ({"inputs": {"proposals_sha256": "0" * 64}}, {"stage": "test"},
                   {"outputs": {"label_block.test.jsonl": "d" * 64}}):
        (part / "RECEIPT.json").write_text(json.dumps({**receipt, **change}))
        n += 1
        o = tmp_path / f"refused_{n}.json"
        assert S1.main(args[:-1] + [str(o)]) == 2 and not o.exists()
    (part / "RECEIPT.json").write_text(json.dumps(receipt))
    for bad_table in (g["evidence"], tmp_path / "missing"):
        n += 1
        o = tmp_path / f"refused_{n}.json"
        cli = ["history-drop-report", "--table", str(bad_table), "--receipt", str(part / "RECEIPT.json"),
               "--budget-w", str(W), "--out", str(o)]
        assert S1.main(cli) == 2 and not o.exists()
    o = tmp_path / "refused_w.json"
    assert S1.main(args[:-3] + ["19", "--out", str(o)]) == 2 and not o.exists()     # a T1PromptError (W)
    # a too-long prompt is a STOP: exit 1 (a tokenizer that counts four tokens per character)
    class _Heavy:
        def __call__(self, text, add_special_tokens=False):
            return {"input_ids": list(text) * 4}
    monkeypatch.setattr(S1, "pool_tokenizers", lambda: {"heavy": _Heavy()})
    again = tmp_path / "again.json"
    assert S1.main(args[:-1] + [str(again)]) == S1.EXIT_STOP == 1
    assert json.loads(again.read_text())["total"]["prompts_too_long"] > 0


def test_the_cli_runs_as_a_module(tmp_path):
    """``python -m r1.c3.train.serialize_t1 --help`` (the cluster entry point) imports and parses."""
    import sys
    root = Path(__file__).resolve().parents[2]
    res = subprocess.run([sys.executable, "-m", "r1.c3.train.serialize_t1", "history-drop-report", "--help"],
                         cwd=root, capture_output=True, text=True, timeout=120)
    assert res.returncode == 0 and "--receipt" in res.stdout and "--budget-w" in res.stdout


def test_split_file_assignment_is_the_reports_source():
    assign = p3_split.assignment(p3_split.load())
    t1 = {v["split"] for k, v in assign.items() if v["node"] == NODE}
    assert t1 == {"train", "dev", "test"}
