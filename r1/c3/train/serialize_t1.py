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
``sigma_node`` and ``features``, and under D7-DIFF B ``proposal_diff`` and ``proposal_diff_sha256`` (``DIFF_FIELDS``;
the own row's only). Of the rows of the same campaign (same ``proposal_id`` prefix) with a smaller ``budget_index``:
``proposal_id`` (the campaign check), ``budget_index``, ``decision`` and ``delta_hat`` (the history; the table's Δ̂ is
campaign data at the campaign seeds, the same quantity as T0's ``delta_vs_best``). Of ``build.json``: the featurizer
description and, per node, ``metric_direction``, ``suite``, ``gate_suite`` and ``sigma_node``, the table schema and
the ``proposal_diff`` record. Nothing else: not the row's own ``decision``, ``delta_hat``, ``audit_group``, ``wave``,
``noop``, ``duplicate``, ``candidate_hash`` or ``incumbent_hash``, no earlier or later row's diff, no later row, no
label, no evaluation value. ``ROW_FIELDS`` / ``HISTORY_FIELDS`` list what is read; a test changes the other fields of
the own row and those of every later row (later rows' features too) and checks that the prompt does not change.

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

**Diff text** (R1-T1-A5-DECISIONS: D7-DIFF B with fallback A). The input is decided by the table, never by the
caller (``table_diff_mode``):
- **B**: a ``g5_t1_table/2`` table (``g5_assemble`` with the D7-DIFF B change) records ``proposal_diff`` in
  ``build.json`` and gives every row ``proposal_diff`` (the step's own ``proposal.diff``, pre-execution) and
  ``proposal_diff_sha256``. ``table_prompts`` passes each row's text and sha256 to ``t1_prompt``, which refuses a text
  whose sha256 (``diff_sha256``, the assembly's rule) differs from the sha256 passed or from the row's own
  ``proposal_diff_sha256``: the binding, so no row is rendered with another row's diff. ``meta.diff.sha256`` then
  equals the row's ``proposal_diff_sha256``, and ``sft_data`` checks that again for every T1 row it writes. A text
  strict UTF-8 cannot encode (a lone surrogate) is refused with a fixed message (``check_showable``).
- **A** (fallback): a ``g5_t1_table/1`` table carries no diff field; the proposal shows ``Diff: n/a (not carried by the
  G.5 table)`` and ``meta.diff`` is None (FL1).
- Anything else (a ``/2`` table without the record, a row with the field in an ``/1`` table, some rows with and some
  without) is refused, so one build never mixes A and B.

The excerpt rule is ``diff_excerpt``: line ends normalised to ``\\n``; a line longer than ``DIFF_LINE_MAX_CHARS``
characters is cut to that length (ending in ``LINE_CUT``); whole lines are kept from the top while at most
``DIFF_MAX_LINES`` lines and ``DIFF_MAX_CHARS`` characters (Unicode code points, newlines included) are used; the header
states the lines shown and the total. No tokenizer is involved in this step. History lines show ``(diff)`` for an
earlier step, never its text: a prompt shows only its own step's diff.

**Length rule.** As T0's: ``render_text`` must fit ``max_tokens - FRAMING_RESERVE`` tokens under every tokenizer
given (default: ``serialize.POOL``). If it does not, the oldest history lines are dropped first (``fit_history``); if
it still does not fit with no history, diff lines are dropped from the bottom (largest kept prefix, by bisection); a
prompt that does not fit with neither raises ``serialize.PromptTooLong``. ``meta`` records every count.

**History-drop report** (``history_drop_report``; ``python -m r1.c3.train.serialize_t1 history-drop-report``): per
node, how many prompts of the released G.5 table's train and dev instances lose history lines, lose diff lines, or are
too long, under the pool tokenizers. It reads the table directory (``proposals.jsonl``, ``build.json``), the ``g5``
train/dev release receipt (checked against the table's sha256), the signed P3 split file (which instances are train
and dev) and the pool tokenizers; never an evidence directory, a label partition or a test release. It writes counts
only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
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
DIFF_FIELD, DIFF_SHA_FIELD = "proposal_diff", "proposal_diff_sha256"     # g5_assemble.DIFF_FIELD / DIFF_SHA_FIELD
DIFF_FIELDS = (DIFF_FIELD, DIFF_SHA_FIELD)    # of the own row only, under B (``table_diff_mode``)
TABLE_SCHEMA_A, TABLE_SCHEMA_B = "g5_t1_table/1", "g5_t1_table/2"         # g5_assemble.TABLE_SCHEMA is the B one
PROPOSAL_DIFF = {"field": DIFF_FIELD, "sha256_field": DIFF_SHA_FIELD, "decision": "R1-T1-A5-DECISIONS D7-DIFF B",
                 "source": "the ledger line's proposal.diff: the diff field of the manager's reply as parsed, written "
                           "before the runner applies it (pre-execution); not a recounted or applied copy",
                 "sha256": "sha256 of the text's UTF-8 bytes (surrogateescape), diff_support.apply_diff's diff_sha256"}
REPORT_SCHEMA = "trackp_t1_history_drop/1"
EXIT_OK, EXIT_STOP, EXIT_REFUSED = 0, 1, 2      # the CLI's exit codes (``main``)
REPORT_SPLITS = ("train", "dev")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
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


def diff_sha256(text: str) -> str:
    """The sha256 of a diff text, by ``g5_assemble.diff_sha256``'s rule (UTF-8 with surrogateescape, which is
    ``diff_support.apply_diff``'s ``diff_sha256``); a text that cannot be encoded so is refused."""
    if not isinstance(text, str):
        raise T1PromptError("a diff must be text")
    try:
        return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()
    except UnicodeEncodeError as exc:
        raise T1PromptError("a diff text is not encodable as UTF-8 (surrogateescape)") from exc


SURROGATE_REFUSAL = ("a diff text contains a lone surrogate code point and cannot be shown as UTF-8 text; A5's T1 "
                     "prompt refuses it (D7-DIFF B); the author decides")


def check_showable(text: str, where: str) -> None:
    """Refuse a diff text that strict UTF-8 cannot encode. Such a text can reach a table only as a lone surrogate in
    U+DC80-U+DCFF (``diff_sha256``'s surrogateescape rule hashes it; any other lone surrogate already fails there), and
    a prompt holding it could not be tokenized or written as UTF-8. The message is fixed; it quotes no text."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise T1PromptError(f"{where}: {SURROGATE_REFUSAL}") from None


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
    return kept, {"sha256": diff_sha256(text),                                    # binds the diff text shown
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
    """{node: node info} from the table's ``build.json``, after checking the featurizer it records and the table
    schema (``g5_t1_table/1`` without, ``/2`` with the ``proposal_diff`` record; ``table_diff_mode``)."""
    schema = build.get("schema")
    if schema not in (TABLE_SCHEMA_A, TABLE_SCHEMA_B):
        raise T1PromptError(f"build.json schema {schema!r} is not {TABLE_SCHEMA_A} or {TABLE_SCHEMA_B}")
    if (schema == TABLE_SCHEMA_B) != ("proposal_diff" in build) or \
            ("proposal_diff" in build and build["proposal_diff"] != PROPOSAL_DIFF):
        raise T1PromptError(f"build.json: a {TABLE_SCHEMA_B} table records exactly the proposal_diff record of "
                            f"g5_assemble and a {TABLE_SCHEMA_A} table none (D7-DIFF B / fallback A)")
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
              tokenizers: Mapping | None = None, diff: str | None = None, diff_sha256_expected: str | None = None,
              max_tokens: int = MAX_TOKENS, group: str = "") -> DecisionPrompt:
    """The ``DecisionPrompt`` of one G.5 table row. ``history_rows``: the rows of the same campaign (others are
    refused; rows at or after this step are ignored). ``node_info``: ``check_build(build)[node]``. ``diff``: the row's
    own ``proposal_diff`` under D7-DIFF B (None: fallback A), with ``diff_sha256_expected``, the row's
    ``proposal_diff_sha256`` (``table_prompts`` passes both). The binding: the text's sha256 must equal
    ``diff_sha256_expected``, and, when the row itself carries ``proposal_diff_sha256`` (a B row), that field too, so
    no other row's diff can be rendered on this row; a B row must be rendered with a diff. A row without the field (a
    fallback-A row) may be given a diff only with a matching ``diff_sha256_expected`` (used by tests of the length
    rule; ``table_prompts`` never does it). A diff that cannot be shown as UTF-8 text is refused
    (``check_showable``)."""
    own_sha = row[DIFF_SHA_FIELD] if DIFF_SHA_FIELD in row else None
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
        if diff_sha256_expected is not None:
            raise T1PromptError(f"{pid}: a diff sha256 without its diff text")
        if own_sha is not None:
            raise T1PromptError(f"{pid}: the row carries {DIFF_SHA_FIELD} but no diff was given (D7-DIFF B: a B row "
                                f"is rendered with its own diff)")
        dlines, drec = None, None
    else:
        got = diff_sha256(diff)
        if not _HEX64.fullmatch(str(diff_sha256_expected or "")) or got != diff_sha256_expected or \
                (own_sha is not None and got != own_sha):
            raise T1PromptError(f"{pid}: the diff text's sha256 is not the row's proposal_diff_sha256 (D7-DIFF B "
                                f"binding)")
        check_showable(diff, pid)
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

def table_diff_mode(rows: Sequence[Mapping], build: Mapping) -> bool:
    """True for D7-DIFF B, False for fallback A, decided by the table (module docstring): B needs ``build.json``'s
    ``proposal_diff`` record (``g5_t1_table/2``) and, in every row, a text ``proposal_diff`` with its lower-case hex
    ``proposal_diff_sha256`` equal to ``diff_sha256`` of the text; A needs neither the record nor either field in any
    row. Anything in between (a mixed table) is refused, and so is a B row whose text strict UTF-8 cannot encode
    (``check_showable``)."""
    b = "proposal_diff" in build
    if b and build["proposal_diff"] != PROPOSAL_DIFF:
        raise T1PromptError("build.json's proposal_diff record is not g5_assemble's (D7-DIFF B)")
    for r in rows:
        pid = r.get("proposal_id")
        has = [k in r for k in DIFF_FIELDS]
        if not b:
            if any(has):
                raise T1PromptError(f"{pid}: a row carries {DIFF_FIELD} in a table whose build.json records none "
                                    f"(A and B mixed)")
            continue
        if not all(has):
            raise T1PromptError(f"{pid}: a row without {DIFF_FIELD} / {DIFF_SHA_FIELD} in a {TABLE_SCHEMA_B} table "
                                f"(A and B mixed)")
        if not isinstance(r[DIFF_FIELD], str) or not _HEX64.fullmatch(str(r[DIFF_SHA_FIELD])) or \
                diff_sha256(r[DIFF_FIELD]) != r[DIFF_SHA_FIELD]:
            raise T1PromptError(f"{pid}: {DIFF_FIELD} is not text or its sha256 is not {DIFF_SHA_FIELD}")
        check_showable(r[DIFF_FIELD], str(pid))
    return b


def _table_items(rows: Sequence[Mapping], build: Mapping, *, budget_w: int, wanted: set | None):
    """(row, its campaign's rows, node info, diff text or None, diff sha256 or None) for each row to render, after
    the whole-table checks of ``table_prompts``."""
    info = check_build(build)
    if isinstance(budget_w, bool) or not isinstance(budget_w, int) or budget_w < 1:
        raise T1PromptError("budget_w must be a positive integer (the G.5 spec's campaign.W)")
    with_diff = table_diff_mode(rows, build)
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
    for key in sorted(by_campaign):
        camp = by_campaign[key]
        for r in sorted(camp, key=lambda x: int(x["budget_index"])):
            if wanted is not None and r["proposal_id"] not in wanted:
                continue
            yield (r, camp, info[r["node"]], r[DIFF_FIELD] if with_diff else None,
                   r[DIFF_SHA_FIELD] if with_diff else None)


def table_prompts(rows: Sequence[Mapping], build: Mapping, *, budget_w: int, tokenizers: Mapping | None,
                  wanted: set | None = None, max_tokens: int = MAX_TOKENS) -> dict[str, tuple]:
    """{proposal_id: (DecisionPrompt, features)} for the rows of a G.5 table (``proposals.jsonl`` rows, all of one
    table, so every campaign's earlier steps are present: the row count of every node must equal ``build.json``'s
    ``counts.rows``, else a STOP), the shape ``sft_data.sweep_prompts`` returns, so that
    ``sft_data.build_sft_data`` binds each prompt to its row by ``features_hash``. ``budget_w``: the G.5 spec's
    ``campaign.W`` (G5-W A: 20 manager calls; every row's ``budget_frac_left`` is checked against it). ``wanted``
    limits the prompts rendered (history still reads every row). The diff text is the table's (``table_diff_mode``):
    under D7-DIFF B each row's own ``proposal_diff`` and ``proposal_diff_sha256`` are passed to ``t1_prompt``; on a
    fallback-A table no diff text is shown. No caller supplies diff text from elsewhere."""
    out = {}
    for r, camp, info, diff, dsha in _table_items(rows, build, budget_w=budget_w, wanted=wanted):
        pid = r["proposal_id"]
        p = t1_prompt(r, camp, info, budget_w=budget_w, tokenizers=tokenizers, diff=diff,
                      diff_sha256_expected=dsha, max_tokens=max_tokens, group=pid)
        out[pid] = (p, r["features"])
    return out


def history_drop_report(rows: Sequence[Mapping], build: Mapping, *, budget_w: int, tokenizers: Mapping | None,
                        splits: Sequence[str] = REPORT_SPLITS, assign: Mapping | None = None,
                        max_tokens: int = MAX_TOKENS) -> dict:
    """The cluster's D7-LEN report (R1-T1-A5-DECISIONS: "D7-LEN as built ... history cut before diff"): for the rows
    of the P3 ``splits`` (train and dev; the P3 split file's assignment unless ``assign`` is given), rendered as
    ``table_prompts`` renders them under ``tokenizers`` (None: the pool), per node and in total: the prompts, those
    with history lines dropped and the lines dropped, those with diff lines dropped for length and the lines dropped,
    those whose excerpt rule cut the diff (lines or long lines), and those that raise ``PromptTooLong`` (each counted,
    not raised; any is a STOP for the cluster). ``rows``: the whole table (the history and the row-count check read
    every row; prompts are rendered only for the chosen splits). Besides ``rows`` and ``build`` it reads the signed P3
    split file (unless ``assign`` is given) and the tokenizers (the pool when None). Counts only: no prompt text and no
    value."""
    from r1.c3 import p3_split
    bad = sorted(set(splits) - set(REPORT_SPLITS))
    if bad or not splits:
        raise T1PromptError(f"the history-drop report reads train and dev instances only, not {bad or 'none'}")
    assign = p3_split.assignment(p3_split.load()) if assign is None else assign
    wanted = set()
    for r in rows:
        inst = r.get("instance")
        if inst not in assign:
            raise T1PromptError(f"{r.get('proposal_id')}: instance {inst!r} is not in the P3 split file")
        if assign[inst]["split"] in splits:
            wanted.add(r["proposal_id"])
    toks = pool_tokenizers() if tokenizers is None else tokenizers
    zero = {"prompts": 0, "prompts_history_dropped": 0, "history_lines_total": 0, "history_lines_dropped": 0,
            "prompts_diff_lines_dropped_for_length": 0, "diff_lines_dropped_for_length": 0,
            "prompts_diff_cut_by_excerpt": 0, "prompts_too_long": 0}
    per_node: dict[str, dict] = {}
    hist: dict[str, dict] = {}
    with_diff = None
    for r, camp, info, diff, dsha in _table_items(rows, build, budget_w=budget_w, wanted=wanted):
        with_diff = diff is not None
        c = per_node.setdefault(r["node"], dict(zero))
        h = hist.setdefault(r["node"], {})
        c["prompts"] += 1
        try:
            p = t1_prompt(r, camp, info, budget_w=budget_w, tokenizers=toks, diff=diff, diff_sha256_expected=dsha,
                          max_tokens=max_tokens, group=r["proposal_id"])
        except PromptTooLong:
            c["prompts_too_long"] += 1
            continue
        m = p.meta
        c["history_lines_total"] += m["history_total"]
        c["history_lines_dropped"] += m["history_dropped"]
        c["prompts_history_dropped"] += m["history_dropped"] > 0
        h[str(m["history_dropped"])] = h.get(str(m["history_dropped"]), 0) + 1
        if m["diff"] is not None:
            d = m["diff"]
            c["diff_lines_dropped_for_length"] += d["lines_dropped_for_length"]
            c["prompts_diff_lines_dropped_for_length"] += d["lines_dropped_for_length"] > 0
            c["prompts_diff_cut_by_excerpt"] += d["lines_kept"] < d["lines_total"] or d["long_lines_cut"] > 0
    total = dict(zero)
    for c in per_node.values():
        for k in total:
            total[k] += c[k]
    return {"schema": REPORT_SCHEMA, "label": "ENGINEERING_ONLY", "prompt_version": T1_PROMPT_VERSION,
            "featurizer": G5F.FEATURIZER, "table_schema": build.get("schema"),
            "proposals_sha256": build.get("proposals_sha256"), "d7_diff": None if with_diff is None
            else ("B" if with_diff else "A"), "splits": sorted(splits), "budget_w": budget_w,
            "token_budget": max_tokens - FRAMING_RESERVE, "tokenizers": sorted(toks),
            "excerpt_rule": {"max_chars": DIFF_MAX_CHARS, "max_lines": DIFF_MAX_LINES,
                             "line_max_chars": DIFF_LINE_MAX_CHARS},
            "nodes": {n: {**per_node[n], "history_dropped_distribution": dict(sorted(hist[n].items(),
                                                                                key=lambda kv: int(kv[0])))}
                      for n in sorted(per_node)},
            "total": total, "stop": total["prompts_too_long"] > 0}


def missing_for_gate(rows: Sequence[Mapping], have: Mapping) -> list[str]:
    """Rows that are not no-ops and that ``have`` (prompts or predictions keyed by proposal id) lacks. The frozen
    builder asks for an A5 prediction only for the non-no-op rows of the **test** block it computes (``TEST_SERIES``;
    under the PRE-DUP primary population, less the left-out repeats), so this is a superset of its requirement: an
    empty list guarantees the builder's coverage for every split and both populations."""
    from r1.c3.arms import is_noop
    return sorted(r["proposal_id"] for r in rows if not is_noop(r) and r["proposal_id"] not in have)


# ---------------------------------------------------------------------------------------------- the cluster CLI

def read_released_table(table_dir: Path | str, receipt_path: Path | str) -> tuple[list[dict], dict, str]:
    """(rows, build.json, receipt sha256) of the G.5 table the ``g5`` train/dev release receipt names. Reads the table
    directory (``proposals.jsonl``, ``build.json``) through ``arms_freeze.load_table_rows`` (name guard, sealed-path
    guard, no label or evaluation value in a row) and the receipt file itself; never a label partition, an evidence
    directory or a test release."""
    from r1.c3 import arms_freeze as AF
    from r1.c3 import release as R
    table_dir, receipt_path = Path(table_dir), Path(receipt_path)
    if R.is_evidence_dir(table_dir) or table_dir.resolve() == receipt_path.resolve().parent:
        raise T1PromptError(f"{table_dir} is an evidence or partition directory, not the G.5 table directory")
    raw = receipt_path.read_bytes()
    receipt = json.loads(raw)
    if receipt_path.name != "RECEIPT.json" or receipt.get("schema") != R.RECEIPT_SCHEMA or \
            receipt.get("source") != "g5" or receipt.get("stage") != "traindev" or \
            set(receipt.get("outputs") or {}) != set(R.PARTITIONS["traindev"]):
        raise T1PromptError(f"{receipt_path} is not the g5 train/dev release receipt")
    rows = AF.load_table_rows(table_dir)
    table_sha = hashlib.sha256((table_dir / "proposals.jsonl").read_bytes()).hexdigest()
    if (receipt.get("inputs") or {}).get("proposals_sha256") != table_sha:
        raise T1PromptError(f"{table_dir} is not the table the g5 train/dev receipt released")
    build = json.loads((table_dir / "build.json").read_text())
    if build.get("proposals_sha256") != table_sha:
        raise T1PromptError(f"{table_dir}/build.json does not bind this proposals.jsonl")
    return rows, build, hashlib.sha256(raw).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m r1.c3.train.serialize_t1 history-drop-report --table DIR --receipt RELEASE/g5/traindev/RECEIPT.json
    --budget-w 20 --out FILE``: the D7-LEN history-drop report under the pool tokenizers, written once to FILE (JSON).
    Exit codes: 0, written and no prompt too long; 1, written and at least one prompt raised ``PromptTooLong`` (a STOP:
    D7 report §9); 2, refused or failed, nothing written (FILE exists, not the g5 train/dev receipt, the table's sha256
    differs, a ``T1PromptError``, a bad table directory, any other error; argparse's usage errors also exit 2)."""
    ap = argparse.ArgumentParser(prog="python -m r1.c3.train.serialize_t1")
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("history-drop-report", help="D7-LEN: history and diff lines dropped, per node (counts only)")
    h.add_argument("--table", required=True, help="the G.5 table directory (proposals.jsonl, build.json)")
    h.add_argument("--receipt", required=True, help="the g5 train/dev release RECEIPT.json naming that table")
    h.add_argument("--budget-w", type=int, required=True, help="the G.5 spec's campaign.W (20)")
    h.add_argument("--out", required=True, help="the report file (JSON), written once")
    a = ap.parse_args(argv)
    out = Path(a.out)
    try:
        if out.exists():
            raise T1PromptError(f"{out} exists; the report is written once")
        rows, build, receipt_sha = read_released_table(a.table, a.receipt)
        rep = history_drop_report(rows, build, budget_w=a.budget_w, tokenizers=None)
        rep["receipt_sha256"] = receipt_sha
        text = json.dumps(rep, indent=1, sort_keys=True) + "\n"
        with out.open("x") as fh:
            fh.write(text)
    except Exception as exc:  # noqa: BLE001 - every refusal or failure is exit 2, with its reason on stderr
        print(f"REFUSED ({type(exc).__name__}): {exc}", file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps({"total": rep["total"], "d7_diff": rep["d7_diff"], "stop": rep["stop"]}, sort_keys=True))
    return EXIT_STOP if rep["stop"] else EXIT_OK


__all__ = ["DIFF_FIELDS", "DIFF_LINE_MAX_CHARS", "DIFF_MAX_CHARS", "DIFF_MAX_LINES", "NA", "PROPOSAL_DIFF",
           "T1PromptError", "T1_NODES", "T1_PROMPT_VERSION", "check_build", "diff_excerpt", "diff_sha256",
           "history_drop_report", "missing_for_gate", "read_released_table", "t1_prompt", "table_diff_mode",
           "table_prompts"]


if __name__ == "__main__":
    sys.exit(main())
