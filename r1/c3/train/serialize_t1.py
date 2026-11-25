"""A5's prompt form for T1 (G.5) proposals: decision D7 of the ARMS-T1FEAT A report. ENGINEERING_ONLY code;
AI-assisted (Claude).

Authority: R1-ARMS-DECISIONS (ARMS-T1FEAT A), the T1 features report
(``docs/r1/reports/arms_t1feat_20261123/T1_FEATURES_20261123.md`` §5, D7) and the decision row that records D7. The
design and the author decisions this form needs are in
``docs/r1/reports/arms_t1feat_20261123/A5_T1_PROMPT_20261123.md``.

**Why a sibling of ``serialize.py``.** The T0 form (``serialize.serialize_view``, ``trackp_prompt/v2``) replays a T0
ledger through ``features.featurize_view`` with a ``NodeContext``; both refuse T1 nodes, and its node block formats
``features.NODE_INFO`` numbers that T1 nodes do not have. A T1 proposal reaches A5 only as a row of the G.5 table
(``proposals.jsonl``, ``sweep2/t1_tasl/g5_assemble.py``) with its ``features`` dict (``g5_features``, the
``g5_t1_features/1`` fields). This module renders that row; ``serialize.py`` is not changed, so every T0 prompt stays
byte-identical. The shared pieces (``fmt``, ``state_text``, ``render_text``, ``fit_history``, the tokenizer pool,
``FRAMING_RESERVE``, ``MAX_TOKENS``, ``QUESTION``, ``BIN_OPTIONS``) are imported from it, not copied.

**What it reads.** Of the proposal's own table row: ``proposal_id``, ``node``, ``memory_mode``, ``budget_index``,
``sigma_node`` and ``features``. Of the rows of the same campaign (same ``proposal_id`` prefix) with a smaller
``budget_index``: ``proposal_id`` (the campaign check), ``budget_index``, ``decision`` and ``delta_hat`` (the history;
the table's Δ̂ is campaign data at the campaign seeds, the same quantity as T0's ``delta_vs_best``). Of
``build.json``: the featurizer description and, per node, ``metric_direction``, ``suite``, ``gate_suite`` and
``sigma_node``. Nothing else: not the row's own ``decision``, ``delta_hat``, ``audit_group``, ``wave``, ``noop``,
``duplicate``, ``candidate_hash`` or ``incumbent_hash``, no later row, no label, no evaluation value. ``ROW_FIELDS`` /
``HISTORY_FIELDS`` list what is read; a test changes the other fields of the own row and those of every later row
(later rows' features too) and checks that the prompt does not change.

**Template** (``T1_PROMPT_VERSION``): the T0 template's sections and lines in the same order, each filled from the T1
source or shown as ``NA`` (the token T0 already prints for a gain it cannot compute) where T1 has no source; a field
without a T1 source is never shown with a T0 value. The fields with no T1 source must be NaN / −1 in the row
(``g5_features.NO_T1_SOURCE``); anything else is refused, so a featurizer change cannot enter the prompt unseen. The
four code-state fields (``cfg_equals_incumbent``, ``active_equals_incumbent``, ``active_seen_before``,
``full_seen_before``) have a T1 source (R1-T1-FEAT-DECISIONS D2 A) and are shown as ``yes`` / ``no``, never ``n/a``;
a NaN there is refused (the assembly STOPs on it, D9 B), and ``build.json``'s two D9 counts must be 0.

    state    = node (suite, tier), metric direction and sigma_node, memory mode, budget in manager calls,
               incumbent (n/a configuration; gain z from recorded_gain_z), history (oldest first; one line per step)
    proposal = edit (n/a), the diff excerpt or "Diff: n/a", the code-state flags, the per-key counts (n/a)
    question + the 12 options in ``BIN_OPTIONS`` order (unchanged)

**Diff text** (optional; D7-DIFF). The G.5 table on main carries no diff text: the unified diff is in the sealed
campaign ledgers only (``proposal.diff``), which ``g5_seal.SealedTree`` opens for the assembly and the release step
only. Without ``diffs`` the proposal shows ``Diff: n/a (not carried by the G.5 table)``. With ``diffs`` ({proposal_id:
unified diff text}, for every rendered row) the excerpt rule is ``diff_excerpt``: line ends normalised to ``\\n``; a
line longer than ``DIFF_LINE_MAX_CHARS`` characters is cut to that length (ending in ``LINE_CUT``); whole lines are
kept from the top while at most ``DIFF_MAX_LINES`` lines and ``DIFF_MAX_CHARS`` characters (Unicode code points,
newlines included) are used; the header states the lines shown and the total. No tokenizer is involved in this step.

**Length rule.** As T0's: ``render_text`` must fit ``max_tokens - FRAMING_RESERVE`` tokens under every tokenizer
given (default: ``serialize.POOL``). If it does not, the oldest history lines are dropped first (``fit_history``); if
it still does not fit with no history, diff lines are dropped from the bottom (largest kept prefix, by bisection); a
prompt that does not fit with neither raises ``serialize.PromptTooLong``. ``meta`` records every count.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
from pathlib import Path
from typing import Mapping, Sequence

from r1.c3.train.serialize import (FRAMING_RESERVE, PromptTooLong, count_tokens, fit_history, fmt, pool_tokenizers,
                                   render_text, state_text)
from r1.c3.train.types import BIN_OPTIONS, MAX_TOKENS, QUESTION, T1_PROMPT_VERSION, DecisionPrompt

NA = "n/a"                     # the token T0's template already prints for a value it cannot compute
DIFF_MAX_CHARS = 1200          # D7-LEN (author decision): characters of diff text kept before the token check
DIFF_MAX_LINES = 40
DIFF_LINE_MAX_CHARS = 160
LINE_CUT = " [cut]"
ROW_FIELDS = ("proposal_id", "node", "memory_mode", "budget_index", "sigma_node", "features")
HISTORY_FIELDS = ("proposal_id", "budget_index", "decision", "delta_hat")
TABLED = ("kept", "discarded", "discarded_divergent", "not_run_inert", "not_run_duplicate")   # g5_assemble.TABLED
DIRECTIONS = {"maximize": "higher", "minimize": "lower"}
D9_COUNTS = ("raw_state_missing", "flag_mismatch")    # g5_assemble.D9_COUNTS: build.json nodes.<node>.features

_G5F = Path(__file__).resolve().parents[3] / "sweep2" / "t1_tasl" / "g5_features.py"


def _load_g5_features():
    """``sweep2/t1_tasl/g5_features.py`` (a module that imports only ``math``), loaded by path under a private name so
    that this module uses the featurizer's own node table, suite mapping and missing-value convention."""
    spec = importlib.util.spec_from_file_location("_a5_t1_g5_features", _G5F)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G5F = _load_g5_features()
T1_NODES = tuple(G5F.T1_NODE_INFO)


class T1PromptError(ValueError):
    """A G.5 table row (or build record) this form refuses to render."""


# ---------------------------------------------------------------------------------------------- pieces

def yes_no(v) -> str:
    """1.0 -> yes, 0.0 -> no, as T0 prints its flags. Only the four code-state fields are rendered this way; they have
    a T1 source (R1-T1-FEAT-DECISIONS D2 A: the harness's inert and duplicate rules), so they are never ``n/a``. A NaN
    (a record without raw code states) cannot reach an assembled table, which STOPs on a non-zero
    ``raw_state_missing`` count (D9 B), and is refused here rather than shown as ``n/a``."""
    if isinstance(v, float) and math.isnan(v):
        raise T1PromptError("a code-state flag is NaN; under R1-T1-FEAT-DECISIONS D2 A it has a T1 source, and D9 B "
                            "STOPs the assembly on raw_state_missing, so the table is not one g5_assemble writes")
    if v in (1.0, 1, True):
        return "yes"
    if v in (0.0, 0, False):
        return "no"
    raise T1PromptError(f"a code-state flag must be 0 or 1, not {v!r}")


def diff_excerpt(text: str, *, max_chars: int = DIFF_MAX_CHARS, max_lines: int = DIFF_MAX_LINES,
                 line_max: int = DIFF_LINE_MAX_CHARS) -> tuple[list[str], dict]:
    """(kept lines, record) by the deterministic excerpt rule of the module docstring."""
    if not isinstance(text, str):
        raise T1PromptError("a diff must be text")
    src = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = src.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    kept, used, cut = [], 0, 0
    for ln in lines:
        long = len(ln) > line_max
        if long:
            ln = ln[:line_max - len(LINE_CUT)] + LINE_CUT
        if len(kept) == max_lines or used + len(ln) + 1 > max_chars:
            break
        kept.append(ln)
        used += len(ln) + 1
        cut += long
    return kept, {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),     # binds the supplied diff text
                  "lines_total": len(lines), "lines_kept": len(kept), "chars_total": len(src), "chars_kept": used,
                  "long_lines_cut": cut, "rule": {"max_chars": max_chars, "max_lines": max_lines,
                                                  "line_max_chars": line_max}}


def diff_block(lines: Sequence[str] | None, total: int | None) -> list[str]:
    if lines is None:
        return [f"Diff: {NA} (not carried by the G.5 table)"]
    return [f"Diff (unified; lines shown {len(lines)} of {total}):"] + list(lines)


def node_lines_t1(node: str, info: Mapping, sigma_node: float, memory_mode: str) -> list[str]:
    better = DIRECTIONS[info["metric_direction"]]
    return [f"Node: {node} ({info['gate_suite']} suite, tier T1, code-level diffs; {NA} rows, {NA} features, "
            f"{NA} classes, minority share {NA})",
            f"Metric: {NA} ({better} is better; z is signed so that positive is better); noise level sigma_node = "
            f"{fmt(float(sigma_node))}",
            f"Memory: {memory_mode}"]


def budget_line_t1(b: int, budget_w: int) -> str:
    """T1 campaigns stop on W manager calls (G5-W A); every step before b was one charged call."""
    return f"Budget: trial {b}; manager calls used {b - 1} of {budget_w}"


def incumbent_lines_t1(gain_z: float) -> list[str]:
    return [f"Incumbent configuration (active keys): {NA} (code-level node; no structured configuration)",
            f"Incumbent metric: {NA}; recorded gain since the first valid trial: z = {gain_z:+.2f}"]


def history_line_t1(step: int, row: Mapping | None, sigma_node: float) -> str:
    """One line per earlier step. A step without a tabled row (an invalid reply, a refused diff, an infrastructure
    failure, or a divergent run left out of the table) has no metric."""
    if row is None:
        return f"t{step}: (no tabled proposal); no valid metric"
    dec, d = row["decision"], row.get("delta_hat")
    if dec in ("kept", "discarded"):
        if not (isinstance(d, (int, float)) and math.isfinite(d)):
            raise T1PromptError(f"step {step}: a {dec} row without a finite delta_hat")
        return f"t{step}: (diff); {dec}, z {float(d) / sigma_node:+.2f}"
    if dec == "discarded_divergent":
        return f"t{step}: (diff); no valid metric"
    if dec == "not_run_inert":
        return f"t{step}: (diff); not run (inert)"
    if dec == "not_run_duplicate":
        return f"t{step}: (diff); not run (duplicate)"
    raise T1PromptError(f"step {step}: decision {dec!r} is not a tabled decision")


# ---------------------------------------------------------------------------------------------- checks

def check_build(build: Mapping) -> dict:
    """{node: node info} from the table's ``build.json``, after checking the featurizer it records."""
    feat = build.get("featurizer") or {}
    if feat.get("version") != G5F.FEATURIZER or list(feat.get("fields") or []) != list(G5F.FEATURES_V3) or \
            feat.get("missing_categorical") != G5F.MISSING_CATEGORICAL or \
            list(feat.get("no_t1_source") or []) != list(G5F.NO_T1_SOURCE):
        raise T1PromptError(f"build.json does not record the featurizer {G5F.FEATURIZER} this form renders")
    nodes = build.get("nodes") or {}
    out = {}
    for node, info in nodes.items():
        if node not in G5F.T1_NODE_INFO:
            raise T1PromptError(f"build.json names {node}, not a declared T1 node")
        if info.get("suite") != G5F.T1_NODE_INFO[node]["suite"] or \
                info.get("gate_suite") != G5F.SUITE_NAMES[info.get("suite")]:
            raise T1PromptError(f"{node}: build.json suite/gate_suite differ from g5_features")
        if info.get("metric_direction") not in DIRECTIONS:
            raise T1PromptError(f"{node}: metric_direction {info.get('metric_direction')!r}")
        if info.get("features") != {k: 0 for k in D9_COUNTS}:     # R1-T1-FEAT-DECISIONS D9 B, as g5_assemble STOPs
            raise T1PromptError(f"{node}: build.json's D9 counts {info.get('features')!r} are not "
                                f"{ {k: 0 for k in D9_COUNTS} }")
        n_rows = (info.get("counts") or {}).get("rows")
        if isinstance(n_rows, bool) or not isinstance(n_rows, int) or n_rows < 0:
            raise T1PromptError(f"{node}: build.json records no row count (counts.rows)")
        out[node] = {k: info[k] for k in ("suite", "gate_suite", "metric_direction", "sigma_node")}
        out[node]["rows"] = n_rows
    return out


def _check_features(pid: str, row: Mapping, f: Mapping, budget_w: int) -> None:
    if list(sorted(f)) != sorted(G5F.FEATURES_V3):
        raise T1PromptError(f"{pid}: the features are not the v3 field set")
    if f["node_code"] != G5F.T1_NODE_CODES[row["node"]]:
        raise T1PromptError(f"{pid}: node_code {f['node_code']} is not {row['node']}'s T1 code")
    for k in G5F.NO_T1_SOURCE:       # D1: a field without a T1 source is NaN (numeric) or -1 (categorical)
        v = f[k]
        ok = v == G5F.MISSING_CATEGORICAL if k in G5F.CAT_FEATURES_V3 else (isinstance(v, float) and math.isnan(v))
        if not ok:
            raise T1PromptError(f"{pid}: {k} = {v!r}, but it has no T1 source (NaN / -1 expected)")
    b = int(row["budget_index"])
    if f["budget_index"] != float(b) or abs(f["budget_frac_left"] - (1.0 - (b - 1) / budget_w)) > 1e-12:
        raise T1PromptError(f"{pid}: budget_index / budget_frac_left do not match step {b} of W = {budget_w}")
    if not (isinstance(f["recorded_gain_z"], float) and math.isfinite(f["recorded_gain_z"])):
        raise T1PromptError(f"{pid}: recorded_gain_z must be finite")


def campaign_key(pid: str) -> str:
    """``g5.<mode>:<node>__s<seed>`` of ``g5.<mode>:<node>__s<seed>:t<step>``."""
    return pid.rsplit(":", 1)[0]


# ---------------------------------------------------------------------------------------------- one prompt

def t1_prompt(row: Mapping, history_rows: Sequence[Mapping], node_info: Mapping, *, budget_w: int,
              tokenizers: Mapping | None = None, diff: str | None = None, max_tokens: int = MAX_TOKENS,
              group: str = "") -> DecisionPrompt:
    """The ``DecisionPrompt`` of one G.5 table row. ``history_rows``: the rows of the same campaign (others are
    refused; rows at or after this step are ignored). ``node_info``: ``check_build(build)[node]``."""
    row = {k: row[k] for k in ROW_FIELDS}
    pid, node, b = row["proposal_id"], row["node"], int(row["budget_index"])
    if node not in G5F.T1_NODE_INFO:
        raise T1PromptError(f"{pid}: {node} is not a T1 node (T0 rows use serialize.serialize_view)")
    sigma = float(row["sigma_node"])
    if not (math.isfinite(sigma) and sigma > 0) or sigma != float(node_info["sigma_node"]):
        raise T1PromptError(f"{pid}: sigma_node differs from build.json's or is not positive")
    f = row["features"]
    _check_features(pid, row, f, budget_w)
    if not 1 <= b <= budget_w:
        raise T1PromptError(f"{pid}: step {b} outside 1..{budget_w}")
    by_step = {}
    for h in history_rows:
        if campaign_key(h["proposal_id"]) != campaign_key(pid):
            raise T1PromptError(f"{pid}: a history row of another campaign ({h['proposal_id']})")
        s = int(h["budget_index"])
        if s < b:
            if s in by_step:
                raise T1PromptError(f"{pid}: two rows for step {s}")
            by_step[s] = {k: h.get(k) for k in HISTORY_FIELDS}
    history = [history_line_t1(s, by_step.get(s), sigma) for s in range(1, b)]
    head = (node_lines_t1(node, node_info, sigma, row["memory_mode"]) + [budget_line_t1(b, budget_w)]
            + incumbent_lines_t1(float(f["recorded_gain_z"])))
    flags = [f"Edited key: {NA} (no structured key); key type: {NA}",
             f"Active configuration equals the incumbent (normalised code state): "
             f"{yes_no(f['active_equals_incumbent'])}; evaluated before in this campaign: "
             f"{yes_no(f['active_seen_before'])}",
             f"Raw code equals the incumbent: {yes_no(f['cfg_equals_incumbent'])}; raw code evaluated before in this "
             f"campaign: {yes_no(f['full_seen_before'])}",
             f"Times this key was edited before: {NA}; same edit before: {NA}; reverses the last edit of this key: "
             f"{NA}"]
    if diff is None:
        dlines, drec = None, None
    else:
        dlines, drec = diff_excerpt(diff)

    def make_with(kept_diff):
        proposal = "\n".join([f"Edit: {NA} (code-level diff; no structured key edit)"]
                             + diff_block(kept_diff, None if drec is None else drec["lines_total"]) + flags)

        def make(kept_history):
            return DecisionPrompt(state=state_text(head, kept_history), proposal=proposal, question=QUESTION,
                                  options=BIN_OPTIONS, group=group)
        return make

    toks = pool_tokenizers() if tokenizers is None else tokenizers
    budget = max_tokens - FRAMING_RESERVE
    diff_dropped = 0
    try:
        prompt, dropped = fit_history(make_with(dlines), history, toks, budget)
    except PromptTooLong:
        if not dlines:
            raise
        prompt, kept = _fit_diff(make_with, dlines, toks, budget)    # no history line fits: cut the diff
        dropped, diff_dropped = len(history), len(dlines) - kept
    meta = {"prompt_version": T1_PROMPT_VERSION, "tier": "T1", "proposal_id": pid, "budget_index": b,
            "history_total": len(history), "history_dropped": dropped, "token_budget": budget,
            "tokenizers": sorted(toks), "featurizer": G5F.FEATURIZER,
            "diff": None if drec is None else {**drec, "lines_dropped_for_length": diff_dropped}}
    return DecisionPrompt(state=prompt.state, proposal=prompt.proposal, question=prompt.question,
                          options=prompt.options, group=group, meta=meta)


def _fit_diff(make_with, dlines: Sequence[str], toks: Mapping, budget: int) -> tuple[DecisionPrompt, int]:
    """With no history: the prompt with the largest prefix of the diff lines that fits (bisection); (prompt, kept)."""
    def fits(k: int) -> bool:
        text = render_text(make_with(list(dlines[:k]))([]))
        return all(count_tokens(t, text) <= budget for t in toks.values())

    if not fits(0):
        raise PromptTooLong(f"T1 prompt exceeds {budget} tokens with no history and no diff line")
    lo, hi = 0, len(dlines)          # fits(lo); not fits(hi) (the caller found the full prompt too long)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if fits(mid) else (lo, mid)
    return make_with(list(dlines[:lo]))([]), lo


# ---------------------------------------------------------------------------------------------- a table

def table_prompts(rows: Sequence[Mapping], build: Mapping, *, budget_w: int, tokenizers: Mapping | None,
                  diffs: Mapping[str, str] | None = None, wanted: set | None = None,
                  max_tokens: int = MAX_TOKENS) -> dict[str, tuple]:
    """{proposal_id: (DecisionPrompt, features)} for the rows of a G.5 table (``proposals.jsonl`` rows, all of one
    table, so every campaign's earlier steps are present: the row count of every node must equal ``build.json``'s
    ``counts.rows``, else a STOP), the shape ``sft_data.sweep_prompts`` returns, so that
    ``sft_data.build_sft_data`` binds each prompt to its row by ``features_hash``. ``budget_w``: the G.5 spec's
    ``campaign.W`` (G5-W A: 20 manager calls; every row's ``budget_frac_left`` is checked against it). ``wanted``
    limits the prompts rendered (history still reads every row). ``diffs``: {proposal_id: diff text} for every rendered
    row, or None (D7-DIFF; the table on main carries none)."""
    info = check_build(build)
    if isinstance(budget_w, bool) or not isinstance(budget_w, int) or budget_w < 1:
        raise T1PromptError("budget_w must be a positive integer (the G.5 spec's campaign.W)")
    by_campaign: dict[str, list] = {}
    ids = set()
    for r in rows:
        pid = r["proposal_id"]
        if pid in ids:
            raise T1PromptError(f"duplicate proposal id {pid}")
        ids.add(pid)
        if r.get("node") not in info:
            raise T1PromptError(f"{pid}: node {r.get('node')!r} is not in build.json")
        if r.get("source") not in (None, "g5"):
            raise T1PromptError(f"{pid}: source {r.get('source')!r} is not g5")
        by_campaign.setdefault(campaign_key(pid), []).append(r)
    per_node = {n: sum(1 for r in rows if r["node"] == n) for n in info}
    short = {n: (per_node[n], info[n]["rows"]) for n in info if per_node[n] != info[n]["rows"]}
    if short:                           # the history reads every earlier row: a filtered table would change prompts
        raise T1PromptError(f"table_prompts needs the whole G.5 table; rows given vs build.json counts.rows: {short}")
    stray = sorted(set(wanted or ()) - ids)
    if stray:
        raise T1PromptError(f"{len(stray)} wanted proposals are not in the table, e.g. {stray[:3]}")
    out = {}
    for key in sorted(by_campaign):
        camp = by_campaign[key]
        for r in sorted(camp, key=lambda x: int(x["budget_index"])):
            pid = r["proposal_id"]
            if wanted is not None and pid not in wanted:
                continue
            diff = None
            if diffs is not None:
                if pid not in diffs:
                    raise T1PromptError(f"{pid}: diffs were supplied but not for this proposal")
                diff = diffs[pid]
            p = t1_prompt(r, camp, info[r["node"]], budget_w=budget_w, tokenizers=tokenizers, diff=diff,
                          max_tokens=max_tokens, group=pid)
            out[pid] = (p, r["features"])
    return out


def missing_for_gate(rows: Sequence[Mapping], have: Mapping) -> list[str]:
    """Rows that are not no-ops and that ``have`` (prompts or predictions keyed by proposal id) lacks. The frozen
    builder asks for an A5 prediction only for the non-no-op rows of the **test** block it computes (``TEST_SERIES``;
    under the PRE-DUP primary population, less the left-out repeats), so this is a superset of its requirement: an
    empty list guarantees the builder's coverage for every split and both populations."""
    from r1.c3.arms import is_noop
    return sorted(r["proposal_id"] for r in rows if not is_noop(r) and r["proposal_id"] not in have)


__all__ = ["DIFF_LINE_MAX_CHARS", "DIFF_MAX_CHARS", "DIFF_MAX_LINES", "NA", "T1PromptError", "T1_NODES",
           "T1_PROMPT_VERSION", "check_build", "diff_excerpt", "missing_for_gate", "t1_prompt", "table_prompts"]
