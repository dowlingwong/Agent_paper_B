"""Label-free exam parts: E0 aleatoric pass-through and E6 architecture probes (RUNBOOK Track P 1.7; spec §5.5-5.6).

ENGINEERING_ONLY; AI-assisted (Claude).

**E0.** Synthetic prompts in the real serialisation (``serialize``'s template
pieces): realistic distractor fields (node, budget, incumbent, history, rule
flags) plus one line ``Forecast note: expected standardised increment m = ...,
noise s = ...`` placed at a random position among the proposal lines. Grid
m in [-2.5, 2.5] x s in [0.1, 1.5], split into 10 x 7 cells; ``HELDOUT`` cells
(interior: interpolation; corners: mild extrapolation) never appear in
training. 3,000 train / 1,000 test items, deterministic (``SEED``). The text
shows m and s to two decimals and the targets use those rounded values:
soft target = N(m, s^2) integrated over ``labels.EDGES`` (bins 1-11; bin 0 is
never active), contrast target = its argmax one-hot.

Metrics on held-out cells (``e0_metrics``): RPS (spec §6.1: bins 1-11
cumulative + bin-0 Brier), slope of the predicted std on s and of the
predicted mean on m (moments over the bin midpoints, ``labels.moments``;
a perfect predictor gives 0.98 / 1.03 on this grid), width ratio (mean
predicted std / mean label std). Pass (``e0_pass``, protocol v1): width slope
>= 0.7 and mean slope >= 0.8.

**E0 protocol v2 (author, 26 Oct; R1-E0-PROTOCOL).** (a) The width slope is the
regression of the predicted std on the *label's own* std (the binned soft
label's std with the same bin representatives), ``width_slope_vs_label``; the
label's own slopes vs s and m are reported as the ceiling
(``label_width_slope_vs_s``, ``label_mean_slope_vs_m``). (b) Validation cells
``VAL_CELLS`` are held out of the training grid (``e0_split``) for early
stopping. Pass (R1-E0-THRESHOLDS, author 26 Oct evening; a floor, not a ranking):
``width_slope_vs_label`` >= 0.6 with its bootstrap 95 % lower bound > 0, and
``mean_slope`` >= 0.8 (``E0_V2_THRESHOLDS``). The lower bound is the 2.5th
percentile of 2,000 resamples of the test prompts (``E0_BOOT``). A4 v2 passes
when >= 95 % of prompts are monotone against the label's std.

**E6** probe constructors with the spec's criteria: A1 branch isolation and A2
sibling-order invariance (max |delta logit| <= 1e-3; packed models only), A3
history-length robustness (0 / 2k / 8k tokens of irrelevant history prepended
to the history block; mean |delta RPS| <= 0.01; protocol v2: 0 / 25 / 50 / 100 %
of the remaining budget under the pool's smallest limit, ``a3_probe_budget``,
with 2k / 8k descriptive only), A4 width monotonicity
(predicted std non-decreasing in s over 5 steps in >= 95 % of prompts; v2 adds
the label reference, ``a4_pass_v2``), A5 slot
bias (options listed in permuted order; belief mapped back to canonical order
within TV 0.02 of the canonical listing). A permuted listing carries
``meta["option_perm"]``: ``options[i] == BIN_OPTIONS[perm[i]]``.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.stats import norm

from r1.c3.features import NODE_INFO
from r1.c3.labels import EDGES, N_BINS, moments
from r1.c3.train.metrics import rps  # the one RPS definition of Track P (metrics.py)
from r1.c3.train.serialize import (budget_line, count_tokens, edit_text, history_line, incumbent_lines, node_lines,
                                   state_text)
from r1.c3.train.types import BIN_OPTIONS, QUESTION, DecisionPrompt

E0_VERSION = "trackp_e0/v1"
SEED = 20261026
M_RANGE, S_RANGE = (-2.5, 2.5), (0.1, 1.5)
M_CELLS, S_CELLS = 10, 7
# (m cell, s cell): interior cells = interpolation, corner cells = mild extrapolation (both dims at the grid edge)
HELDOUT_INTERP = ((2, 1), (3, 4), (4, 2), (5, 5), (6, 1), (7, 3))
HELDOUT_EXTRAP = ((0, 0), (0, 6), (9, 0), (9, 6))
HELDOUT = HELDOUT_INTERP + HELDOUT_EXTRAP
# E0 v2: validation cells held out of the training grid (early stopping): four interior cells and the two m-edge
# cells of the middle s row; none touches a test cell's row-and-column pair
VAL_CELLS = ((1, 3), (3, 2), (5, 4), (8, 2), (0, 3), (9, 3))
assert not set(VAL_CELLS) & set(HELDOUT)
# R1-E0-THRESHOLDS (author, 26 Oct evening); the same values are frozen in r1/c3/rules/p3_rule_v2.yaml
E0_V2_THRESHOLDS: dict | None = {"width_slope_vs_label_min": 0.6, "width_slope_vs_label_lb_gt": 0.0,
                                 "mean_slope_min": 0.8}
E0_BOOT = {"resamples": 2000, "alpha": 0.05, "seed": SEED, "unit": "test prompt"}
A4_V2_MIN_FRAC = 0.95
N_TRAIN, N_TEST = 3000, 1000
DATA = Path(__file__).resolve().parent / "data"
E0_FILE = DATA / "e0_v1.jsonl.gz"
E0_SHA = DATA / "e0_v1.sha256"

E0_WIDTH_SLOPE_MIN, E0_MEAN_SLOPE_MIN = 0.7, 0.8
A12_MAX_ABS = 1e-3
A3_LENGTHS = (0, 2000, 8000)
A3_FRACS = (0.0, 0.25, 0.5, 1.0)          # v2: fractions of the remaining token budget (R1-A3-BUDGET)
A3_DESCRIPTIVE = (2000, 8000)             # v2: longer levels, descriptive only
A3_MAX_DRPS = 0.01
A4_STEPS = 5
A4_MIN_FRAC = 0.95
A5_MAX_TV = 0.02

_MLP_KEYS = {"HIDDEN_UNITS": (16, 32, 64, 128, 256), "ALPHA": (1e-5, 1e-4, 1e-3, 1e-2),
             "MAX_ITER": (40, 80, 160, 300), "LEARNING_RATE_INIT": (1e-4, 1e-3, 3e-3, 1e-2),
             "BATCH_SIZE": (32, 64, 128, 256)}
_OPENML_KEYS = {"C": (0.01, 0.1, 0.3, 1.0, 3.0), "max_iter": (100, 300, 1000, 1500),
                "class_weight": ("none", "balanced"), "scaler": ("none", "standard", "minmax")}
_DECISIONS = ("kept", "discarded", "discarded", "discarded", "skipped")


# ---------------------------------------------------------------- targets

def soft_target(m: float, s: float) -> np.ndarray:
    """N(m, s^2) integrated over the 11 non-inert bins (z scale); bin 0 = 0."""
    y = np.zeros(N_BINS)
    y[1:] = np.diff(norm.cdf((EDGES - m) / s))
    return y / y.sum()


def hard_target(m: float, s: float) -> np.ndarray:
    y = np.zeros(N_BINS)
    y[int(np.argmax(soft_target(m, s)))] = 1.0
    return y


def cell_of(m: float, s: float) -> tuple[int, int]:
    i = min(int((m - M_RANGE[0]) / ((M_RANGE[1] - M_RANGE[0]) / M_CELLS)), M_CELLS - 1)
    j = min(int((s - S_RANGE[0]) / ((S_RANGE[1] - S_RANGE[0]) / S_CELLS)), S_CELLS - 1)
    return i, j


def _sample_in(cell, rng) -> tuple[float, float]:
    """(m, s) uniform in a cell, rounded to the two decimals the prompt shows, still inside the cell."""
    wm, ws = (M_RANGE[1] - M_RANGE[0]) / M_CELLS, (S_RANGE[1] - S_RANGE[0]) / S_CELLS
    while True:
        m = round(float(M_RANGE[0] + (cell[0] + rng.uniform()) * wm), 2)
        s = round(float(S_RANGE[0] + (cell[1] + rng.uniform()) * ws), 2)
        if cell_of(m, s) == tuple(cell) and s > 0:
            return m, s


# ---------------------------------------------------------------- distractor context

def _value(v) -> str:
    return f"{v:g}" if isinstance(v, float) else str(v)


def _context(rng) -> dict:
    """Realistic distractor fields: a node, its sigma, budget, an incumbent configuration and a short history."""
    node = str(rng.choice(sorted(NODE_INFO)))
    keys = _MLP_KEYS if NODE_INFO[node]["family"] == "mlp" else _OPENML_KEYS
    config = {k: v[int(rng.integers(len(v)))] for k, v in keys.items()}
    if NODE_INFO[node]["family"] == "openml":
        config["model_type"] = "logistic_regression"
    W = int(rng.choice([10, 20]))
    b = int(rng.integers(2, W + 1))
    sigma = float(np.round(rng.uniform(0.002, 0.02), 5))
    best = float(np.round(rng.uniform(0.80, 0.99), 6))
    hist = []
    for t in range(1, min(b, 13)):
        k = str(rng.choice(sorted(k for k in keys)))
        vals = keys[k]
        old, new = vals[int(rng.integers(len(vals)))], vals[int(rng.integers(len(vals)))]
        dec = str(rng.choice(_DECISIONS))
        dz = None if dec == "skipped" else float(np.round(rng.normal(0, 1), 2))
        hist.append(history_line(t, {"symbol": k, "old": _value(old), "new": _value(new), "path": "-"}, dec, dz))
    k = str(rng.choice(sorted(keys)))
    vals = keys[k]
    edit = {"symbol": k, "old": _value(config[k]), "new": _value(vals[int(rng.integers(len(vals)))]),
            "path": "train.py" if NODE_INFO[node]["family"] == "mlp" else "config.yaml"}
    head = (node_lines(node, sigma, str(rng.choice(["none", "append_only_summary"]))) + [budget_line(b, W)]
            + incumbent_lines(config, best, best - float(rng.uniform(0, 0.02)), sigma))
    flags = [f"Edited key is active for this node's model; {'structural' if k in ('class_weight', 'scaler') else 'numeric'} key",
             f"Active configuration equals the incumbent: no; evaluated before in this campaign: "
             f"{'yes' if rng.uniform() < 0.1 else 'no'}",
             f"Times this key was edited before: {int(rng.integers(0, 5))}; same edit before: {int(rng.integers(0, 2))}; "
             f"reverses the last edit of this key: {'yes' if rng.uniform() < 0.1 else 'no'}"]
    return {"head": head, "history": hist, "edit": edit, "flags": flags, "note_pos": int(rng.integers(0, 4))}


def note_line(m: float, s: float) -> str:
    return f"Forecast note: expected standardised increment m = {m:+.2f}, noise s = {s:.2f}"


def build_prompt(ctx: dict, m: float, s: float, *, group: str = "", extra_history: Sequence[str] = (),
                 options: Sequence[str] = BIN_OPTIONS, meta: dict | None = None) -> DecisionPrompt:
    lines = list(ctx["flags"])
    lines.insert(ctx["note_pos"], note_line(m, s))
    proposal = "\n".join([f"Edit: {edit_text(ctx['edit'])}"] + lines)
    return DecisionPrompt(state=state_text(ctx["head"], list(extra_history) + list(ctx["history"])), proposal=proposal,
                          question=QUESTION, options=tuple(options), group=group, meta=dict(meta or {}))


# ---------------------------------------------------------------- E0 set

def _prompt_dict(p: DecisionPrompt) -> dict:
    return {"state": p.state, "proposal": p.proposal, "question": p.question, "options": list(p.options),
            "group": p.group}


def prompt_from_dict(d: dict, meta: dict | None = None) -> DecisionPrompt:
    return DecisionPrompt(state=d["state"], proposal=d["proposal"], question=d["question"], options=tuple(d["options"]),
                          group=d["group"], meta=dict(meta or {}))


def generate(seed: int = SEED, n_train: int = N_TRAIN, n_test: int = N_TEST) -> list[dict]:
    """The E0 items (train first, then test), deterministic in ``seed``."""
    rng = np.random.default_rng(seed)
    train_cells = [(i, j) for i in range(M_CELLS) for j in range(S_CELLS) if (i, j) not in HELDOUT]
    items = []
    for split, n, cells in (("train", n_train, train_cells), ("test", n_test, list(HELDOUT))):
        for k in range(n):
            cell = cells[int(rng.integers(len(cells)))]
            m, s = _sample_in(cell, rng)
            ctx = _context(rng)
            p = build_prompt(ctx, m, s, group=f"e0-{split}-{k:05d}")
            kind = None if split == "train" else ("interp" if cell in HELDOUT_INTERP else "extrap")
            items.append({"id": f"e0-{split}-{k:05d}", "version": E0_VERSION, "split": split, "cell": list(cell),
                          "heldout_kind": kind, "m": m, "s": s, "prompt": _prompt_dict(p),
                          "y_soft": soft_target(m, s).round(12).tolist(), "y_hard": hard_target(m, s).tolist()})
    return items


def to_bytes(items: list[dict]) -> bytes:
    """Deterministic gzip (mtime 0) of the JSONL."""
    raw = "".join(json.dumps(it, sort_keys=True) + "\n" for it in items).encode()
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0, compresslevel=9) as gz:
        gz.write(raw)
    return buf.getvalue()


def write(path: Path = E0_FILE, sha_path: Path = E0_SHA, seed: int = SEED) -> str:
    data = to_bytes(generate(seed))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    Path(sha_path).write_text(f"{digest}  {Path(path).name}\n")
    return digest


def load(path: Path = E0_FILE, sha_path: Path = E0_SHA, verify: bool = True) -> list[dict]:
    data = Path(path).read_bytes()
    if verify:
        want = Path(sha_path).read_text().split()[0]
        if hashlib.sha256(data).hexdigest() != want:
            raise ValueError(f"{path}: sha256 does not match {sha_path}")
    return [json.loads(line) for line in gzip.decompress(data).decode().splitlines() if line]


# ---------------------------------------------------------------- metrics

def belief_moments(p) -> tuple[np.ndarray, np.ndarray]:
    """Mean and std (z units) of the non-inert part of bin distributions (bin midpoints, tails at +-4)."""
    _, mu, tau = moments(np.asarray(p, float), 1.0)
    return mu, tau


def _slope(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    return float(np.polyfit(x, y, 1)[0])


def e0_metrics(p_pred, items: Sequence[dict], target: str = "y_soft") -> dict:
    """E0 metrics of predicted distributions [N, 12] on ``items`` (normally the held-out test items)."""
    p = np.asarray(p_pred, float)
    y = np.array([it[target] for it in items], float)
    m = np.array([it["m"] for it in items], float)
    s = np.array([it["s"] for it in items], float)
    mu, tau = belief_moments(p)
    mu_y, tau_y = belief_moments(np.array([it["y_soft"] for it in items], float))
    kinds = np.array([it.get("heldout_kind") or "" for it in items])
    out = {"n": int(len(items)), "rps": float(rps(p, y).mean()), "width_slope": _slope(s, tau),
           "mean_slope": _slope(m, mu), "width_ratio": float(tau.mean() / tau_y.mean()),
           "width_slope_vs_label": _slope(tau_y, tau), "mean_slope_vs_label": _slope(mu_y, mu)}
    for k in ("interp", "extrap"):
        sel = kinds == k
        if sel.sum() >= 2:
            out[f"rps_{k}"] = float(rps(p[sel], y[sel]).mean())
    return out


def e0_pass(metrics: dict) -> bool:
    return metrics["width_slope"] >= E0_WIDTH_SLOPE_MIN and metrics["mean_slope"] >= E0_MEAN_SLOPE_MIN


def e0_split(items: Sequence[dict]) -> tuple[list[dict], list[dict]]:
    """v2: training items outside / inside ``VAL_CELLS``."""
    val = {tuple(c) for c in VAL_CELLS}
    tr = [it for it in items if it["split"] == "train" and tuple(it["cell"]) not in val]
    va = [it for it in items if it["split"] == "train" and tuple(it["cell"]) in val]
    return tr, va


def label_ceiling(items: Sequence[dict]) -> dict:
    """v2 ceiling: the soft label's own std / mean slopes vs the stated s / m (same bin representatives)."""
    mu_y, tau_y = belief_moments(np.array([it["y_soft"] for it in items], float))
    return {"label_width_slope_vs_s": _slope([it["s"] for it in items], tau_y),
            "label_mean_slope_vs_m": _slope([it["m"] for it in items], mu_y)}


def width_slope_bootstrap(p_pred, items: Sequence[dict], boot: dict = E0_BOOT) -> tuple[float, float]:
    """Percentile interval (two-sided 1 - alpha) of ``width_slope_vs_label`` over resampled test prompts."""
    _, tau = belief_moments(np.asarray(p_pred, float))
    _, tau_y = belief_moments(np.array([it["y_soft"] for it in items], float))
    rng = np.random.default_rng(boot["seed"])
    n = len(tau)
    idx = rng.integers(0, n, size=(boot["resamples"], n))
    x, y = tau_y[idx], tau[idx]
    xc = x - x.mean(axis=1, keepdims=True)
    slopes = (xc * (y - y.mean(axis=1, keepdims=True))).sum(axis=1) / (xc ** 2).sum(axis=1)
    lo, hi = np.quantile(slopes, [boot["alpha"] / 2, 1 - boot["alpha"] / 2])
    return float(lo), float(hi)


def e0_metrics_v2(p_pred, items: Sequence[dict], target: str = "y_soft") -> dict:
    """v2 metrics: the v1 set, the label ceiling and the bootstrap interval of the primary width slope
    (``width_slope_vs_label``)."""
    lo, hi = width_slope_bootstrap(p_pred, items)
    return {**e0_metrics(p_pred, items, target), **label_ceiling(items), "primary_width": "width_slope_vs_label",
            "width_slope_vs_label_lb95": lo, "width_slope_vs_label_ub95": hi}


def e0_pass_v2(metrics: dict, thresholds: dict | None = None) -> bool | None:
    """R1-E0-THRESHOLDS: width slope vs label std >= 0.6 and its bootstrap 95 % lower bound > 0; mean slope >= 0.8."""
    t = thresholds if thresholds is not None else E0_V2_THRESHOLDS
    if t is None:
        return None
    return bool(metrics["width_slope_vs_label"] >= t["width_slope_vs_label_min"]
                and metrics["width_slope_vs_label_lb95"] > t["width_slope_vs_label_lb_gt"]
                and metrics["mean_slope"] >= t["mean_slope_min"])


# ---------------------------------------------------------------- E6 probes

def _probe_rng(tag: str, seed: int) -> np.random.Generator:
    return np.random.default_rng([seed, int(hashlib.sha256(tag.encode()).hexdigest()[:8], 16)])


def a1_probe(n_states: int = 32, siblings: int = 7, seed: int = SEED) -> list[dict]:
    """A1: per state, the target branch alone and packed with ``siblings`` siblings (target first)."""
    rng = _probe_rng("A1", seed)
    out = []
    for k in range(n_states):
        ctx = _context(rng)
        ms = [_sample_in((int(rng.integers(M_CELLS)), int(rng.integers(S_CELLS))), rng) for _ in range(siblings + 1)]
        g = f"a1-{k:03d}"
        branches = [build_prompt(ctx, m, s, group=g, meta={"branch": i}) for i, (m, s) in enumerate(ms)]
        out.append({"alone": [branches[0]], "packed": branches})
    return out


def a1_pass(logits_alone, logits_packed_target) -> dict:
    d = float(np.max(np.abs(np.asarray(logits_alone, float) - np.asarray(logits_packed_target, float))))
    return {"max_abs": d, "pass": d <= A12_MAX_ABS}


def a2_probe(n_states: int = 32, branches: int = 8, perms: int = 5, seed: int = SEED) -> list[dict]:
    """A2: per state, ``branches`` branches in ``perms`` orders (the first is the identity)."""
    rng = _probe_rng("A2", seed)
    out = []
    for k in range(n_states):
        ctx = _context(rng)
        ms = [_sample_in((int(rng.integers(M_CELLS)), int(rng.integers(S_CELLS))), rng) for _ in range(branches)]
        g = f"a2-{k:03d}"
        base = [build_prompt(ctx, m, s, group=g, meta={"branch": i}) for i, (m, s) in enumerate(ms)]
        orders = [list(range(branches))] + [rng.permutation(branches).tolist() for _ in range(perms - 1)]
        out.append({"branches": base, "orders": orders, "packed": [[base[i] for i in o] for o in orders]})
    return out


def a2_pass(logits_by_order, orders) -> dict:
    """``logits_by_order[r]`` [B, 12] in the order ``orders[r]``; compared after mapping back to branch order."""
    aligned = []
    for lg, o in zip(logits_by_order, orders):
        lg = np.asarray(lg, float)
        back = np.empty_like(lg)
        back[np.asarray(o)] = lg
        aligned.append(back)
    d = float(max(np.max(np.abs(a - aligned[0])) for a in aligned))
    return {"max_abs": d, "pass": d <= A12_MAX_ABS}


def irrelevant_history(tok, n_tokens: int, seed: int = SEED) -> list[str]:
    """History lines (trial numbers 1000+, never the campaign's own) totalling at least ``n_tokens`` tokens."""
    if n_tokens <= 0:
        return []
    rng = _probe_rng(f"A3-{n_tokens}", seed)
    lines, total, t = [], 0, 1000
    while total < n_tokens:
        k = str(rng.choice(sorted(_MLP_KEYS)))
        vals = _MLP_KEYS[k]
        dec = str(rng.choice(_DECISIONS))
        ln = history_line(t, {"symbol": k, "old": _value(vals[0]), "new": _value(vals[-1]), "path": "-"}, dec,
                          None if dec == "skipped" else float(np.round(rng.normal(0, 1), 2)))
        lines.append(ln)
        total += count_tokens(tok, ln + "\n")
        t += 1
    return lines


def a3_probe(tok, n: int = 100, lengths: Sequence[int] = A3_LENGTHS, seed: int = SEED) -> dict:
    """A3: ``n`` prompts, each with 0 / 2k / 8k tokens (under ``tok``) of irrelevant history prepended to its history
    block. Prompts above ``MAX_TOKENS`` carry ``meta["over_limit"]``; a model with a shorter context records how it
    handled them. Returns {length: [prompts]} and the soft targets."""
    rng = _probe_rng("A3", seed)
    rows = []
    for _ in range(n):
        cell = (int(rng.integers(M_CELLS)), int(rng.integers(S_CELLS)))
        rows.append((_context(rng), *_sample_in(cell, rng)))
    out = {"targets": [soft_target(m, s) for _, m, s in rows], "prompts": {}}
    for L in lengths:
        extra = irrelevant_history(tok, L, seed)
        out["prompts"][L] = [build_prompt(ctx, m, s, extra_history=extra, group=f"a3-{i:03d}",
                                          meta={"extra_history_tokens": L, "over_limit": L > 0})
                             for i, (ctx, m, s) in enumerate(rows)]
    return out


def a3_pass(rps_by_length: dict) -> dict:
    """``rps_by_length[L]`` per-prompt RPS; mean |RPS_L - RPS_0| <= 0.01 for every L > 0."""
    base = np.asarray(rps_by_length[0], float)
    d = {L: float(np.mean(np.abs(np.asarray(v, float) - base))) for L, v in rps_by_length.items() if L}
    return {"mean_abs_drps": d, "pass": all(v <= A3_MAX_DRPS for v in d.values())}


def a3_probe_budget(counters: dict, n: int = 100, fracs: Sequence[float] = A3_FRACS, limit: int | None = None,
                    seed: int = SEED) -> dict:
    """A3 v2: per prompt, irrelevant history at ``fracs`` of the remaining budget ``limit - max_f len_f(prompt)``
    (``counters``: the pool families' input-token counters, ``budget.pool_counters``). A level takes the longest
    prefix, counted in words, of one fixed history stream (whole lines, then the next line cut at a word) whose
    longest rendering is within ``base + frac * budget``. Returns {frac: [prompts]}, the soft targets, per prompt
    the budget, the tokens per level and family, and the fraction of the budget each level actually reached."""
    from r1.c3.train.budget import POOL_LIMIT, max_tokens
    limit = POOL_LIMIT if limit is None else limit
    rng = _probe_rng("A3", seed)
    rows = []
    for _ in range(n):
        cell = (int(rng.integers(M_CELLS)), int(rng.integers(S_CELLS)))
        rows.append((_context(rng), *_sample_in(cell, rng)))
    stream = irrelevant_history(_Words(), 4 * limit, seed)   # far more words than any budget takes
    words = [ln.split(" ") for ln in stream]
    total = sum(len(w) for w in words)

    def history(t: int) -> list[str]:
        out, left = [], t
        for w in words:
            if left <= 0:
                break
            out.append(" ".join(w[:left]))
            left -= len(w)
        return out
    out = {"targets": [soft_target(m, s) for _, m, s in rows], "prompts": {f: [] for f in fracs}, "budget": [],
           "tokens": {f: [] for f in fracs}, "reached": {f: [] for f in fracs}, "limit": limit,
           "families": sorted(counters)}
    for i, (ctx, m, s) in enumerate(rows):
        make = lambda t: build_prompt(ctx, m, s, extra_history=history(t), group=f"a3-{i:03d}")  # noqa: E731
        base = max_tokens(counters, make(0))
        budget = limit - base
        if budget <= 0:
            raise ValueError(f"A3 prompt {i} has no budget before any history ({base} >= {limit})")
        out["budget"].append(budget)
        for f in fracs:
            cap = base + f * budget
            lo, hi = 0, total               # longest word prefix within the cap (token counts grow with words)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if max_tokens(counters, make(mid)) <= cap:
                    lo = mid
                else:
                    hi = mid - 1
            p = build_prompt(ctx, m, s, extra_history=history(lo), group=f"a3-{i:03d}",
                             meta={"a3_frac": f, "extra_history_words": lo})
            tok = {fam: c(p) for fam, c in counters.items()}
            if max(tok.values()) > cap:
                raise RuntimeError(f"A3 prompt {i} level {f}: {max(tok.values())} tokens over the cap {cap}")
            out["prompts"][f].append(p)
            out["tokens"][f].append(tok)
            out["reached"][f].append((max(tok.values()) - base) / budget)
    return out


class _Words:
    """Whitespace token count: sizes the history stream only (the budget itself uses the pool counters)."""

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": text.split()}


def a4_probe(n: int = 200, steps: int = A4_STEPS, seed: int = SEED) -> list[list[DecisionPrompt]]:
    """A4: the same prompt with s increased in ``steps`` steps (0.2 -> 1.4), m fixed."""
    rng = _probe_rng("A4", seed)
    out = []
    for k in range(n):
        ctx = _context(rng)
        m = round(float(rng.uniform(*M_RANGE)), 2)
        out.append([build_prompt(ctx, m, round(float(s), 2), group=f"a4-{k:03d}")
                    for s in np.linspace(0.2, 1.4, steps)])
    return out


def a4_pass(pred_std, tol: float = 0.0) -> dict:
    """``pred_std`` [n, steps]; a prompt passes when its predicted std never decreases (by more than ``tol``)."""
    d = np.diff(np.asarray(pred_std, float), axis=1)
    frac = float(np.mean((d >= -tol).all(axis=1)))
    return {"frac_monotone": frac, "pass": frac >= A4_MIN_FRAC}


def a4_label_std(n: int = 200, steps: int = A4_STEPS, seed: int = SEED) -> np.ndarray:
    """[n, steps] std of the soft label of each A4 prompt (same (m, s) as ``a4_probe``, same bin representatives)."""
    out = []
    for row in a4_probe(n, steps, seed):
        ms = [_note_values(p.proposal) for p in row]
        out.append(belief_moments(np.array([soft_target(m, s) for m, s in ms]))[1])
    return np.array(out)


def _note_values(proposal: str) -> tuple[float, float]:
    line = next(ln for ln in proposal.splitlines() if ln.startswith("Forecast note:"))
    m = float(line.split("m = ")[1].split(",")[0])
    s = float(line.split("noise s = ")[1])
    return m, s


def a4_pass_v2(pred_std, label_std, tol: float = 0.0) -> dict:
    """v2 (label reference): a prompt passes when its predicted std does not decrease (by more than ``tol``) at any
    step where the label's std increases; the label's own fraction of monotone prompts is the ceiling. Also the
    median per-prompt slope of predicted std on label std. Pass: >= 95 % of prompts (R1-E0-THRESHOLDS)."""
    pred, lab = np.asarray(pred_std, float), np.asarray(label_std, float)
    dp, dl = np.diff(pred, axis=1), np.diff(lab, axis=1)
    up = dl > 0
    ok = ((dp >= -tol) | ~up).all(axis=1)
    slopes = [float(np.polyfit(lab[i], pred[i], 1)[0]) if np.ptp(lab[i]) > 0 else float("nan") for i in range(len(lab))]
    return {"frac_monotone_vs_label": float(ok.mean()), "label_ceiling_frac": float((dl >= 0).all(axis=1).mean()),
            "frac_monotone_raw": float((dp >= -tol).all(axis=1).mean()),
            "median_slope_vs_label": float(np.nanmedian(slopes)), "pass": bool(ok.mean() >= A4_V2_MIN_FRAC)}


def a5_probe(n: int = 100, perms: int = 5, seed: int = SEED) -> list[list[DecisionPrompt]]:
    """A5: the same prompt with its options listed in ``perms`` orders (the first canonical)."""
    rng = _probe_rng("A5", seed)
    out = []
    for k in range(n):
        ctx = _context(rng)
        m, s = _sample_in((int(rng.integers(M_CELLS)), int(rng.integers(S_CELLS))), rng)
        orders = [list(range(N_BINS))] + [rng.permutation(N_BINS).tolist() for _ in range(perms - 1)]
        out.append([build_prompt(ctx, m, s, group=f"a5-{k:03d}", options=[BIN_OPTIONS[i] for i in o],
                                 meta={"option_perm": o}) for o in orders])
    return out


def unpermute(belief_listed, perm) -> np.ndarray:
    """A belief over the listed options (``options[i] == BIN_OPTIONS[perm[i]]``) in canonical bin order."""
    b = np.asarray(belief_listed, float)
    out = np.empty_like(b)
    out[..., np.asarray(perm)] = b
    return out


def a5_pass(beliefs_canonical) -> dict:
    """``beliefs_canonical`` [n, perms, 12] already in canonical order; TV to the canonical listing <= 0.02."""
    b = np.asarray(beliefs_canonical, float)
    tv = 0.5 * np.abs(b - b[:, :1]).sum(-1).max(axis=1)
    return {"max_tv": float(tv.max()), "pass": bool(tv.max() <= A5_MAX_TV)}
