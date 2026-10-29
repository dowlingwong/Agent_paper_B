"""Track S analysis: campaign-level S3e test of a tuned single-channel dynamic threshold rule against the tuned
static rule (primary), with fork-level learning and attribution as secondaries.

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY until a Track S authorization exists; this script
authorizes nothing and produces no evidence by itself. Spec: runbook
docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md revision 3 as amended through revision 6.1
(coordinator messages of 29 Oct). Choices the spec leaves open: r1/tracks/ANALYSIS_NOTES.md. Raw metric units
everywhere (the threshold grids are declared in σ_node units and converted with the node's σ_node).

PRIMARY, per node:
  1. Dev tuning (dev_roots.jsonl, the same paired dev instances for every configuration: 20, or 40 after the
     one S0.6 resize): m* = best of the 12-configuration static grid ``static:g,h`` (g ∈ {0.05, 0.1, 0.2, 0.4}·σ,
     h ∈ {−0.25, 0, 0.25}·σ; one extension to g = 0.8σ if m* is on the upper edge); then the 4 single-channel
     members anchored at m* (budget, info, keep+, keep−) of ``dynamic:g0,b_budget,b_info,h0,h_budget``:
     execute iff V̂* + b_info·τ_pred > g0 − b_budget·r, keep iff m̂ > h0 − h_budget·r (r = runs remaining
     fraction); π* = best member (the static member is not eligible). Reported: flip rate (overall, E1, E2),
     matched static (mean effective thresholds of π* on its dev campaigns), winner's curse, S0.7 dev σ_D.
  2. Sizing: σ_D,UCL = max(S0.5b UCL, S0.7 dev UCL); n = ceil((2.93·σ_D,UCL/δ_Y)²); B-eligible iff n ≤ n_max
     (300); n and B-eligibility frozen at S0.8 (``freeze_check`` flags a needed S0.6 re-run).
  3. S3e (campaign_roots.jsonl, fresh instances): D_i = Ȳ_i(π*) − Ȳ_i(m*), paired t, one-sided 95 % bounds;
     Holm by p-value over the primary nodes; matched static on all n instances (π* vs matched static with CI).
  4. Outcomes, precedence A > A-small > B > inconclusive: A (a Holm rejection with UB95 ≥ δ_Y on some rejected
     node); A-small (rejections, all with UB95 < δ_Y); B per B-eligible node (UB95 < δ_Y, flip ≥ 10 %, every S0.6
     power LB ≥ 0.6 after ≤ 1 resize, placebos present, S0.6 n = frozen n); inconclusive otherwise.
  5. STOPs: N0 false-positive count ≥ 18 of 200; an exact placebo (same policy and repetition) with D ≠ 0; a
     descriptive placebo (repetitions 1 vs 2) with |z| > 3.5.

SECONDARY (descriptive), fork level (leaves.jsonl): f̂ (ΔQ) and Î (immediate) ridge models cross-fitted at
instance level; π′ (f̂ > 0) vs m̃ (Î above value-tuned thresholds) on total measured Q with a refitting
cluster bootstrap; the revision-3 hybrid score and U_split; channel contrasts; π′ serialised as JSON + sha256.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.stats import beta as beta_dist
from scipy.stats import binom, chi2, norm, t as t_dist

from r1.tracks.schema import (
    E1_ARMS,
    E2_ARMS,
    STATE_FEATURES,
    TRACKS_LEAF_SCHEMA,
    TRACKS_ROOT_SCHEMA,
    LeafRecord,
    Provenance,
    RootRecord,
    leaf_from_dict,
)

ANALYSIS_VERSION = "tracks_analyze/v4"
PREDECLARATION_SCHEMA = "tracks_predeclaration/v4"
POLICY_SCHEMA = "tracks_policy/v1"

# Exact runbook §0 wording; never paraphrase.
INCONCLUSIVE_WORDING = ("Neither a gain ≥ δ_Y nor its absence was shown; gains up to UB₉₅ remain "
                        "compatible with the data.")
ROUTE_A_WORDING = "Route A: sequential structure matters (the tuned dynamic rule beats the tuned static rule)."
A_SMALL_WORDING = ("Route A-small: a real but practically small gain (at least one Holm-adjusted rejection, and "
                   "UB95 < δ_Y on every node with a rejection); reported as a significant gain; for the framing "
                   "headline treated like route B.")
ROUTE_B_WORDING = ("route B on this node: no gain ≥ δ_Y from a single-channel state-dependent threshold over the "
                   "tuned static rule within the tested family (campaign level; UB95 < δ_Y, flip rate ≥ 10 %, S0.6 "
                   "power gates passed). Never \"provably one-step\".")
ROUTE_A_BUDGET_ONLY_WORDING = "a budget-coupled threshold improves on the static price"
ROUTE_A_DAC_CONDITION = "The DAC headline additionally needs a non-budget channel."
VOID_WORDING = ("STOP: a pipeline gate failed (N0 false-positive count at the STOP threshold, an exact placebo with "
                "D ≠ 0, or a placebo |z| > 3.5); both routes are void (runbook §10).")

LABEL_RANK = {"FIXTURE": 0, "ENGINEERING_ONLY": 1, "PILOT": 2, "EVIDENCE": 3}
ROLES = ("primary", "P1", "P2", "N0", "descriptive")
CHANNELS = ("delta_B", "delta_I", "delta_F", "e2_keep")
NON_BUDGET_CHANNELS = ("delta_I", "delta_F", "e2_keep")
Z_SIZING = 2.93  # revision 7: n = ceil((2.93 σ_D,UCL / δ_Y)²), z_0.95 + z_0.90


class TrackSAnalysisError(ValueError):
    """Malformed or inconsistent input; the analysis refuses to run."""


class HostMixingError(TrackSAnalysisError):
    """A node's records come from more than one host (runbook §4, §9: no table mixes hosts)."""


def combine_labels(labels: Iterable[str]) -> str:
    """Weakest label wins: a number is EVIDENCE only if every input is labelled EVIDENCE."""
    labels = list(labels)
    if not labels:
        raise TrackSAnalysisError("no provenance labels")
    for lab in labels:
        if lab not in LABEL_RANK:
            raise TrackSAnalysisError(f"unknown provenance label {lab!r}; expected one of {sorted(LABEL_RANK)}")
    return min(labels, key=lambda s: LABEL_RANK[s])


# ============================================================================================= loading
def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open() as fh:
        for k, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise TrackSAnalysisError(f"{path}:{k}: invalid JSON ({exc})") from exc
    return rows


_LEAF_FIELDS = {f.name for f in dataclasses.fields(LeafRecord)}
_ROOT_FIELDS = {f.name for f in dataclasses.fields(RootRecord)}


def leaf_from_any(d: dict) -> LeafRecord:
    """``leaf_from_dict`` that also accepts the ``policy`` field whether or not schema.py has it yet."""
    d = dict(d)
    pol = d.pop("policy", "") if "policy" not in _LEAF_FIELDS else d.get("policy", "")
    lf = leaf_from_dict(d)
    if "policy" not in _LEAF_FIELDS:
        object.__setattr__(lf, "policy", pol)
    return lf


EXTRA_ROOT_FIELDS = ("policy", "rep", "llm_seed_base")  # proposed for schema.py; accepted either way


def root_from_dict(d: dict) -> RootRecord:
    d = dict(d)
    extra = {k: d.pop(k) for k in EXTRA_ROOT_FIELDS if k in d and k not in _ROOT_FIELDS}
    if d.get("provenance") is not None:
        d["provenance"] = Provenance(**d["provenance"])
    r = RootRecord(**d)
    for k in EXTRA_ROOT_FIELDS:
        if k not in _ROOT_FIELDS:
            object.__setattr__(r, k, extra.get(k, "" if k == "policy" else None))
    return r


def record_to_dict(rec) -> dict:
    d = dataclasses.asdict(rec)
    for k in EXTRA_ROOT_FIELDS:
        if k not in d and getattr(rec, k, None) not in (None, ""):
            d[k] = getattr(rec, k)
    return d


def policy_of(rec) -> str:
    return getattr(rec, "policy", "") or ""


def load_leaves(path: Path) -> list[LeafRecord]:
    out = []
    for d in _read_jsonl(path):
        if d.get("schema") != TRACKS_LEAF_SCHEMA:
            raise TrackSAnalysisError(f"{path}: leaf schema {d.get('schema')!r} != {TRACKS_LEAF_SCHEMA}")
        out.append(leaf_from_any(d))
    return out


def load_roots(path: Path) -> list[RootRecord]:
    path = Path(path)
    if not path.exists():
        return []
    out = []
    for d in _read_jsonl(path):
        if d.get("schema") != TRACKS_ROOT_SCHEMA:
            raise TrackSAnalysisError(f"{path}: root schema {d.get('schema')!r} != {TRACKS_ROOT_SCHEMA}")
        out.append(root_from_dict(d))
    return out


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_hosts(node: str, leaves: Sequence[LeafRecord] = (), roots: Sequence[RootRecord] = ()) -> str:
    hosts = {lf.provenance.host for lf in leaves}
    hosts |= {r.provenance.host for r in roots if r.provenance is not None}
    if not hosts:
        raise TrackSAnalysisError(f"node {node}: no provenance")
    if len(hosts) != 1:
        raise HostMixingError(f"node {node}: records come from hosts {sorted(hosts)}; no node's table may mix hosts")
    return hosts.pop()


# ============================================================================================= threshold policy families
# Policy strings shared with the collector (RootRecord.policy), revision 7 (mean-centred dynamic terms):
#   static:g,h        execute iff V̂* > g;  keep iff m̂ > h
#   dynamic:g0,b_budget,b_info,h0,h_budget,r1bar,taubar,r2bar
#                     execute iff V̂* + b_info·(τ_pred − τ̄) > g0 − b_budget·(r − r̄₁);
#                     keep    iff m̂ > h0 − h_budget·(r − r̄₂)
# r = runs_left / W = 1 − budget_fraction; τ_pred = the base controller's predictive sd of the increment.
# r̄₁, τ̄ (E1) and r̄₂ (E2) are the means over m*'s eligible dev decisions (fixed after S0.7a), so a member has the
# same average threshold as m* and cannot win by a level shift. The 5-value form (revision 6) is the uncentred
# special case r̄ = τ̄ = 0. b_budget > 0 lowers the execute threshold while runs are more plentiful than usual;
# h_budget > 0 ("keep+") keeps more readily then, h_budget < 0 ("keep−") less readily; b_info > 0 is an
# uncertainty (information) bonus.
STATIC_PARAMS = ("g", "h")
DYNAMIC_PARAMS = ("g0", "b_budget", "b_info", "h0", "h_budget", "r1bar", "taubar", "r2bar")
CHANNEL_MEMBERS = ("budget", "info", "keep+", "keep-")


def fmt_num(x: float) -> str:
    return format(round(float(x), 9) + 0.0, ".9g")


def policy_string(kind: str, params: Sequence[float]) -> str:
    ok = (kind == "static" and len(params) == 2) or (kind == "dynamic" and len(params) in (5, 8))
    if not ok:
        raise TrackSAnalysisError(f"bad policy {kind}{tuple(params)}")
    return f"{kind}:" + ",".join(fmt_num(p) for p in params)


def parse_policy(s: str) -> tuple[str, tuple[float, ...]]:
    try:
        kind, rest = s.split(":", 1)
        vals = tuple(float(x) for x in rest.split(","))
    except ValueError as exc:
        raise TrackSAnalysisError(f"bad policy string {s!r}") from exc
    if not ((kind == "static" and len(vals) == 2) or (kind == "dynamic" and len(vals) in (5, 8))):
        raise TrackSAnalysisError(f"bad policy string {s!r}")
    if not all(math.isfinite(v) for v in vals):
        raise TrackSAnalysisError(f"bad policy string {s!r}")
    return kind, vals


def as_dynamic(s: str) -> tuple[float, ...]:
    """8-tuple (g0, b_budget, b_info, h0, h_budget, r̄₁, τ̄, r̄₂); statics and the 5-value form have zero centres."""
    kind, v = parse_policy(s)
    if kind == "static":
        return (v[0], 0.0, 0.0, v[1], 0.0, 0.0, 0.0, 0.0)
    return v if len(v) == 8 else v + (0.0, 0.0, 0.0)


def threshold_act(s: str | tuple, state: dict, epoch: str, tau_pred: float | None = None) -> bool:
    """Decision of a static/dynamic policy at one eligible decision. ``state`` holds STATE_FEATURES;
    ``tau_pred`` (or state['tau_pred']) is needed at E1 when b_info ≠ 0."""
    g0, bb, bi, h0, hb, r1, tb, r2 = as_dynamic(s) if isinstance(s, str) else s
    r = 1.0 - float(state["budget_fraction"])
    x = float(state["index_value"])
    if epoch == "E1":
        tp = tau_pred if tau_pred is not None else state.get("tau_pred")
        if bi != 0.0 and tp is None:
            raise TrackSAnalysisError("threshold_act: b_info ≠ 0 needs tau_pred")
        return x + (bi * (float(tp) - tb) if bi != 0.0 else 0.0) > g0 - bb * (r - r1)
    return x > h0 - hb * (r - r2)


def effective_thresholds(s: str, decisions: Sequence[dict]) -> dict:
    """Mean effective thresholds of a policy over its own eligible decisions (matched-static secondary)."""
    g0, bb, bi, h0, hb, r1, tb, r2 = as_dynamic(s)
    ge = [g0 - bb * ((1 - d["budget_fraction"]) - r1) - bi * (float(d.get("tau_pred") or 0.0) - tb)
          for d in decisions if d.get("eligible") and d["epoch"] == "E1"]
    he = [h0 - hb * ((1 - d["budget_fraction"]) - r2) for d in decisions if d.get("eligible") and d["epoch"] == "E2"]
    return {"g_eff": float(np.mean(ge)) if ge else g0, "h_eff": float(np.mean(he)) if he else h0,
            "n_E1": len(ge), "n_E2": len(he)}


def decision_centres(decisions: Sequence[dict]) -> dict:
    """r̄₁, τ̄ over eligible E1 decisions and r̄₂ over eligible E2 decisions (revision 7, from m*'s dev campaigns)."""
    e1 = [d for d in decisions if d.get("eligible") and d["epoch"] == "E1"]
    e2 = [d for d in decisions if d.get("eligible") and d["epoch"] == "E2"]
    r1 = float(np.mean([1 - d["budget_fraction"] for d in e1])) if e1 else 0.0
    tb = float(np.mean([float(d["tau_pred"]) for d in e1 if d.get("tau_pred") is not None])) if e1 else 0.0
    r2 = float(np.mean([1 - d["budget_fraction"] for d in e2])) if e2 else r1
    return {"r1bar": r1, "taubar": tb, "r2bar": r2, "n_E1": len(e1), "n_E2": len(e2)}


def channel_of(s: str) -> str:
    kind, v = parse_policy(s)
    if kind == "static":
        return "static"
    nz = [name for name, x in (("budget", v[1]), ("info", v[2]), ("keep+" if v[4] > 0 else "keep-", v[4]))
          if x != 0.0]
    return nz[0] if len(nz) == 1 else ("static" if not nz else "mixed")


FIXED_MEMBER_UNITS = {"budget": [1.0], "info": [0.5], "keep+": [0.5], "keep-": [0.5]}
GRID_MEMBER_UNITS = {"budget": [0.5, 1.0, 2.0], "info": [0.25, 0.5, 1.0], "keep+": [0.25, 0.5, 1.0],
                     "keep-": [0.25, 0.5, 1.0]}


@dataclass
class FamilyDecl:
    """Revision 7. Static grid g × h in σ_node units (g = 0 included: 15 configurations; one extension to g_ext
    if m* is on the upper g edge); single-channel dynamic members anchored at m* and mean-centred, with a
    magnitude grid per channel (b_budget, h_budget in σ_node units; b_info dimensionless × τ_pred)."""
    g_units: list[float] = field(default_factory=lambda: [0.0, 0.05, 0.1, 0.2, 0.4])
    h_units: list[float] = field(default_factory=lambda: [-0.25, 0.0, 0.25])
    g_ext_units: float = 0.8
    member_units: dict = field(default_factory=lambda: {k: list(v) for k, v in GRID_MEMBER_UNITS.items()})

    def static_configs(self, sigma_node: float, extended: bool = False) -> list[str]:
        gs = list(self.g_units) + ([self.g_ext_units] if extended else [])
        return [policy_string("static", (g * sigma_node, h * sigma_node)) for g in gs for h in self.h_units]

    def extension_configs(self, sigma_node: float) -> list[str]:
        return [policy_string("static", (self.g_ext_units * sigma_node, h * sigma_node)) for h in self.h_units]

    def on_upper_edge(self, m_star: str, sigma_node: float) -> bool:
        return abs(parse_policy(m_star)[1][0] - max(self.g_units) * sigma_node) <= 1e-12 + 1e-9 * sigma_node

    def members(self, m_star: str, sigma_node: float, centres: dict | None = None) -> dict[str, str]:
        """Single-channel members anchored at m* = static:g*,h* and centred at ``centres`` (the static member is
        not eligible). Names are '<channel>×<size>'."""
        _, (g, h) = parse_policy(m_star)
        c = centres or {"r1bar": 0.0, "taubar": 0.0, "r2bar": 0.0}
        cc = (c["r1bar"], c["taubar"], c["r2bar"])
        out = {}
        for ch, sizes in self.member_units.items():
            for u in sizes:
                if ch == "budget":
                    p = (g, u * sigma_node, 0.0, h, 0.0)
                elif ch == "info":
                    p = (g, 0.0, u, h, 0.0)
                elif ch == "keep+":
                    p = (g, 0.0, 0.0, h, u * sigma_node)
                elif ch == "keep-":
                    p = (g, 0.0, 0.0, h, -u * sigma_node)
                else:
                    raise TrackSAnalysisError(f"unknown channel {ch}")
                out[f"{ch}×{fmt_num(u)}"] = policy_string("dynamic", p + cc)
        return out


def parse_families(d: dict | str | None) -> FamilyDecl:
    if d in (None, "default"):
        return FamilyDecl()
    fd = FamilyDecl(g_units=[float(x) for x in d["g_units"]], h_units=[float(x) for x in d["h_units"]],
                    g_ext_units=float(d["g_ext_units"]),
                    member_units={k: [float(x) for x in v] for k, v in d.get("member_units", GRID_MEMBER_UNITS).items()})
    if len(fd.g_units) < 4 or len(fd.h_units) != 3:
        raise TrackSAnalysisError("families: need >= 4 g values and 3 h values")
    if min(fd.g_units) != 0.0:
        raise TrackSAnalysisError("families: revision 7 includes g = 0 (execute every non-rule proposal)")
    if not (min(fd.h_units) < 0 < max(fd.h_units)):
        raise TrackSAnalysisError("families: the h grid must be two-sided")
    if not fd.g_ext_units > max(fd.g_units):
        raise TrackSAnalysisError("families: g_ext must exceed the grid's largest g")
    if set(fd.member_units) - set(CHANNEL_MEMBERS) or any(u <= 0 for v in fd.member_units.values() for u in v):
        raise TrackSAnalysisError("families: member_units must map channels to positive magnitudes")
    return fd


# ============================================================================================= pre-declaration
@dataclass
class SizingDecl:
    sigma_D_ucl_s05b: float   # S0.5b one-sided 80 % UCL of σ_D at the chosen W (truncated ledgers)
    n_max: int = 300          # largest affordable fresh-instance count; n > n_max -> node not B-eligible


@dataclass
class NodeDecl:
    name: str
    role: str
    delta_Y: float
    k_n: float | None = None
    sigma_node: float | None = None
    budget_positive_control: bool = False
    sizing: SizingDecl | None = None

    @property
    def delta_dec(self) -> float:
        return self.delta_Y / self.k_n if self.k_n else float("nan")


@dataclass
class Predeclaration:
    nodes: dict[str, NodeDecl]
    primary_nodes: list[str]
    families: FamilyDecl = field(default_factory=FamilyDecl)
    folds: int = 5
    ridge_alpha: float = 0.1
    interactions: str = "epoch"
    bootstrap_B: int = 2000
    seed: int = 20261029
    alpha: float = 0.05
    g_grid: list[float] = field(default_factory=lambda: default_grid(-0.004, 0.008))
    h_grid: list[float] = field(default_factory=lambda: default_grid(-0.004, 0.004))
    fallback_active: bool = False
    analysis_script_sha256: str | None = None
    winners_curse_splits: int = 200
    power_lb_min: float = 0.6
    fp_k_stop: int = 19          # of fp_R replications (revision 7: STOP iff ≥ 19 of 200, exact p < 0.01)
    fp_R: int = 200
    placebo_z_stop: float = 3.5
    flip_min: float = 0.10
    n_dev_initial: int = 20
    n_dev_resized: int = 40
    matched_static_share: float = 0.5
    tuning: dict = field(default_factory=lambda: {"procedure": "argmax", "n_dev": 20})
    raw: dict = field(default_factory=dict)


def default_grid(lo: float, hi: float, step: float = 0.0002) -> list[float]:
    n = int(round((hi - lo) / step))
    return [round(lo + k * step, 10) for k in range(n + 1)]


def margin_delta_Y(sigma_node: float) -> float:
    """δ_Y = max(0.002, 0.5 σ_node), raw metric units (runbook §3)."""
    return max(0.002, 0.5 * float(sigma_node))


def parse_predeclaration(d: dict) -> Predeclaration:
    if d.get("schema") != PREDECLARATION_SCHEMA:
        raise TrackSAnalysisError(f"pre-declaration schema {d.get('schema')!r} != {PREDECLARATION_SCHEMA}")
    nodes = {}
    for name, nd in d.get("nodes", {}).items():
        role = nd.get("role")
        if role not in ROLES:
            raise TrackSAnalysisError(f"node {name}: role {role!r} not in {ROLES}")
        sigma = nd.get("sigma_node")
        if "delta_Y" in nd:
            dY = float(nd["delta_Y"])
            if sigma is not None and abs(dY - margin_delta_Y(sigma)) > 1e-9 + 1e-4 * dY:
                raise TrackSAnalysisError(
                    f"node {name}: delta_Y {dY} != max(0.002, 0.5*sigma_node) = {margin_delta_Y(sigma)}")
        elif sigma is not None:
            dY = margin_delta_Y(sigma)
        else:
            raise TrackSAnalysisError(f"node {name}: needs delta_Y or sigma_node")
        k_n = nd.get("k_n")
        if k_n is not None and not float(k_n) > 0:
            raise TrackSAnalysisError(f"node {name}: k_n must be > 0")
        sz = nd.get("sizing")
        sd = SizingDecl(float(sz["sigma_D_ucl_s05b"]), int(sz.get("n_max", 300))) if sz is not None else None
        if role == "primary" and (sd is None or sigma is None):
            raise TrackSAnalysisError(f"node {name}: a primary node needs sigma_node and a sizing declaration")
        nodes[name] = NodeDecl(name, role, dY, float(k_n) if k_n is not None else None, sigma,
                               bool(nd.get("budget_positive_control", False)), sd)
    primary = list(d.get("primary_nodes", []))
    for p in primary:
        if p not in nodes or nodes[p].role != "primary":
            raise TrackSAnalysisError(f"primary node {p!r} must be declared with role 'primary'")
    fallback = bool(d.get("fallback_active", False))
    if fallback and len(primary) != 1:
        raise TrackSAnalysisError("fallback_active requires exactly one primary node (runbook §9 one-node fallback)")
    if not fallback and len(primary) != 2:
        raise TrackSAnalysisError("two primary nodes are required unless fallback_active is true")
    grid = d.get("threshold_grid", {})
    pd = Predeclaration(
        nodes=nodes, primary_nodes=primary, families=parse_families(d.get("families")), folds=int(d.get("folds", 5)),
        ridge_alpha=float(d.get("ridge_alpha", 0.1)), interactions=str(d.get("interactions", "epoch")),
        bootstrap_B=int(d.get("bootstrap_B", 2000)), seed=int(d.get("seed", 20261029)),
        alpha=float(d.get("alpha", 0.05)),
        g_grid=[float(x) for x in grid.get("g", default_grid(-0.004, 0.008))],
        h_grid=[float(x) for x in grid.get("h", default_grid(-0.004, 0.004))],
        fallback_active=fallback, analysis_script_sha256=d.get("analysis_script_sha256"),
        winners_curse_splits=int(d.get("winners_curse_splits", 200)), power_lb_min=float(d.get("power_lb_min", 0.6)),
        fp_k_stop=int(d.get("fp_k_stop", 19)), fp_R=int(d.get("fp_R", 200)),
        placebo_z_stop=float(d.get("placebo_z_stop", 3.5)), flip_min=float(d.get("flip_min", 0.10)),
        n_dev_initial=int(d.get("n_dev_initial", 20)), n_dev_resized=int(d.get("n_dev_resized", 40)),
        matched_static_share=float(d.get("matched_static_share", 0.5)),
        tuning=dict(d.get("tuning", {"procedure": "argmax", "n_dev": 20})), raw=d)
    if pd.interactions not in ("epoch", "none"):
        raise TrackSAnalysisError("interactions must be 'epoch' or 'none'")
    if pd.folds < 2 or pd.bootstrap_B < 1 or not pd.ridge_alpha > 0 or not 0 < pd.alpha < 0.5:
        raise TrackSAnalysisError("need folds >= 2, bootstrap_B >= 1, ridge_alpha > 0, 0 < alpha < 0.5")
    return pd


# ============================================================================================= fork table
@dataclass
class ForkTable:
    node: str
    host: str
    label: str
    fork_id: list[str]
    instance: np.ndarray        # str, cluster ids
    e1: np.ndarray              # bool
    index: np.ndarray           # V-hat* (E1) or m-hat (E2): the base controller's forecast
    w: np.ndarray               # IPW weights 1/p_select
    X: np.ndarray               # n x len(STATE_FEATURES)
    d_rep: np.ndarray           # n x 2: C_act − C_not per repetition (C = y_terminal − immediate_measured)
    q_rep: np.ndarray           # n x 2: Q_act − Q_not (Q = y_terminal) per repetition
    imm_rep: np.ndarray         # n x 2: immediate_measured of the act arm per repetition
    chan_rep: dict[str, np.ndarray]
    myopic_act: np.ndarray
    g_declared: np.ndarray
    counts: dict[str, Any]
    descriptive: dict[str, Any]

    def __len__(self) -> int:
        return len(self.fork_id)

    @property
    def dbar(self) -> np.ndarray:
        return _nanmean_rows(self.d_rep)

    @property
    def qbar(self) -> np.ndarray:
        return _nanmean_rows(self.q_rep)

    @property
    def immbar(self) -> np.ndarray:
        return _nanmean_rows(self.imm_rep)


def _nanmean_rows(a: np.ndarray) -> np.ndarray:
    ok = ~np.isnan(a)
    n = ok.sum(axis=1)
    s = np.where(ok, a, 0.0).sum(axis=1)
    return np.where(n > 0, s / np.maximum(n, 1), np.nan)


def _leaf_ok(leaf: LeafRecord) -> bool:
    return leaf.status == "ok" and leaf.y_terminal is not None and math.isfinite(leaf.y_terminal)


def _cont(leaf: LeafRecord) -> float:
    return float(leaf.y_terminal) - float(leaf.immediate_measured)


def build_fork_table(node: str, leaves: Sequence[LeafRecord], roots: Sequence[RootRecord] = ()) -> ForkTable:
    if not leaves:
        raise TrackSAnalysisError(f"node {node}: no leaves")
    for lf in leaves:
        if lf.node != node:
            raise TrackSAnalysisError(f"leaf {lf.fork_id}: node {lf.node!r} != {node!r}")
    for r in roots:
        if r.node != node:
            raise TrackSAnalysisError(f"root {r.root_id}: node {r.node!r} != {node!r}")
    host = check_hosts(node, leaves, roots)
    label = combine_labels([lf.provenance.label for lf in leaves]
                           + [r.provenance.label for r in roots if r.provenance is not None])
    by_fork: dict[str, list[LeafRecord]] = {}
    for lf in leaves:
        by_fork.setdefault(lf.fork_id, []).append(lf)
    counts = {"leaves": len(leaves), "leaves_failed": 0, "leaves_aa": 0, "forks_seen": len(by_fork),
              "forks_no_complete_rep": 0, "forks_one_rep_only": 0}
    rows = []
    desc_arm: dict[str, dict[str, list[float]]] = {}
    for fid in sorted(by_fork):
        group = by_fork[fid]
        ref = group[0]
        for lf in group:
            if (lf.instance_id != ref.instance_id or lf.epoch != ref.epoch
                    or lf.fork_trial_index != ref.fork_trial_index or lf.state != ref.state
                    or lf.forecast != ref.forecast or lf.selection != ref.selection
                    or lf.myopic_action != ref.myopic_action):
                raise TrackSAnalysisError(f"fork {fid}: pre-treatment fields differ across its leaves")
        if ref.epoch not in ("E1", "E2"):
            raise TrackSAnalysisError(f"fork {fid}: epoch {ref.epoch!r}")
        allowed = set(E1_ARMS if ref.epoch == "E1" else E2_ARMS) | {"aa"}
        cell: dict[tuple[str, int], LeafRecord] = {}
        for lf in group:
            if lf.arm not in allowed:
                raise TrackSAnalysisError(f"fork {fid}: arm {lf.arm!r} not allowed at {ref.epoch}")
            if lf.rep not in (1, 2):
                raise TrackSAnalysisError(f"fork {fid}: rep {lf.rep} not in (1, 2)")
            if lf.arm == "aa":
                counts["leaves_aa"] += 1
                continue
            if not _leaf_ok(lf):
                counts["leaves_failed"] += 1
                continue
            if (lf.arm, lf.rep) in cell:
                raise TrackSAnalysisError(f"fork {fid}: duplicate leaf ({lf.arm}, rep {lf.rep})")
            cell[(lf.arm, lf.rep)] = lf
            da = desc_arm.setdefault(lf.arm, {"dup_filtered_due_to_fork": [], "nf_c_events": [], "runs_used": [],
                                              "llm_calls": [], "binding": [], "w": []})
            da["dup_filtered_due_to_fork"].append(lf.dup_filtered_due_to_fork)
            da["nf_c_events"].append(lf.nf_c_events)
            da["runs_used"].append(lf.runs_used)
            da["llm_calls"].append(lf.llm_calls)
            da["binding"].append(float(lf.binding))
            da["w"].append(1.0 / lf.selection.p_select)
        act, nac = ("execute", "skip") if ref.epoch == "E1" else ("keep", "discard")
        d, q, im = [np.nan, np.nan], [np.nan, np.nan], [np.nan, np.nan]
        ch = {c: [np.nan, np.nan] for c in CHANNELS}
        for r in (1, 2):
            a, b = cell.get((act, r)), cell.get((nac, r))
            if a is not None and b is not None:
                d[r - 1] = _cont(a) - _cont(b)
                q[r - 1] = float(a.y_terminal) - float(b.y_terminal)
                im[r - 1] = float(a.immediate_measured)
            if ref.epoch == "E1" and ref.selection.channel_arms:
                gh, ct, sk, ex = (cell.get((x, r)) for x in ("ghost", "ctrl_only", "skip", "execute"))
                if sk is not None and gh is not None:
                    ch["delta_B"][r - 1] = _cont(sk) - _cont(gh)
                if ct is not None and gh is not None:
                    ch["delta_I"][r - 1] = _cont(ct) - _cont(gh)
                if ex is not None and ct is not None:
                    ch["delta_F"][r - 1] = _cont(ex) - _cont(ct)
            if ref.epoch == "E2":
                ch["e2_keep"][r - 1] = d[r - 1]
        n_complete = int(sum(not math.isnan(x) for x in d))
        if n_complete == 0:
            counts["forks_no_complete_rep"] += 1
            continue
        if n_complete == 1:
            counts["forks_one_rep_only"] += 1
        p = ref.selection.p_select
        if not (0.0 < p <= 1.0):
            raise TrackSAnalysisError(f"fork {fid}: p_select {p} not in (0, 1]")
        idx = ref.forecast.v_star if ref.epoch == "E1" else ref.forecast.m_hat
        if idx is None or not math.isfinite(idx):
            raise TrackSAnalysisError(f"fork {fid}: missing base-controller forecast")
        missing = [k for k in STATE_FEATURES if k not in ref.state]
        if missing:
            raise TrackSAnalysisError(f"fork {fid}: state lacks {missing}")
        rows.append(dict(fid=fid, inst=ref.instance_id, e1=ref.epoch == "E1", idx=float(idx), w=1.0 / p,
                         x=[float(ref.state[k]) for k in STATE_FEATURES], d=d, q=q, im=im, ch=ch,
                         my=ref.myopic_action in ("execute", "keep"), g=float(ref.forecast.g)))
    if not rows:
        raise TrackSAnalysisError(f"node {node}: no fork has a complete repetition")
    descriptive: dict[str, Any] = {}
    for arm, da in sorted(desc_arm.items()):
        w = np.asarray(da.pop("w"))
        descriptive[arm] = {k: {"mean": float(np.mean(v)), "ipw_mean": float(np.average(v, weights=w))}
                            for k, v in da.items()}
        descriptive[arm]["n_leaves"] = int(len(w))
    if "ctrl_only" in descriptive and "ghost" in descriptive:
        descriptive["delta_I_duplicate_filter_part"] = {
            "dup_filtered_ctrl_minus_ghost": descriptive["ctrl_only"]["dup_filtered_due_to_fork"]["ipw_mean"]
            - descriptive["ghost"]["dup_filtered_due_to_fork"]["ipw_mean"],
            "runs_used_ghost_minus_ctrl": descriptive["ghost"]["runs_used"]["ipw_mean"]
            - descriptive["ctrl_only"]["runs_used"]["ipw_mean"],
            "note": "descriptive only; ghost should be 0 by construction (arm-invariance test 3)"}
    if roots:
        k_meas = [r.eligible_e1 + r.eligible_e2 for r in roots if r.status == "ok"]
        descriptive["roots"] = {"n_roots": len(roots), "k_n_measured_mean": float(np.mean(k_meas)) if k_meas else None,
                                "binding_share": float(np.mean([r.binding for r in roots]))}
    counts["forks_used"] = len(rows)
    return ForkTable(
        node=node, host=host, label=label, fork_id=[r["fid"] for r in rows],
        instance=np.array([r["inst"] for r in rows]), e1=np.array([r["e1"] for r in rows]),
        index=np.array([r["idx"] for r in rows]), w=np.array([r["w"] for r in rows]),
        X=np.array([r["x"] for r in rows], dtype=float), d_rep=np.array([r["d"] for r in rows], dtype=float),
        q_rep=np.array([r["q"] for r in rows], dtype=float), imm_rep=np.array([r["im"] for r in rows], dtype=float),
        chan_rep={c: np.array([r["ch"][c] for r in rows], dtype=float) for c in CHANNELS},
        myopic_act=np.array([r["my"] for r in rows]), g_declared=np.array([r["g"] for r in rows]),
        counts=counts, descriptive=descriptive)


# ============================================================================================= ridge models
@dataclass
class RidgeModel:
    coef: np.ndarray
    mean: dict[bool, np.ndarray]
    sd: dict[bool, np.ndarray]
    trained_epochs: set
    interactions: str


def _wmean(x: np.ndarray, w: np.ndarray) -> float:
    sw = w.sum()
    return float((w * x).sum() / sw) if sw > 0 else float("nan")


def _standardize(X, e1, mean, sd, interactions):
    if interactions == "epoch":
        Z = np.zeros_like(X)
        for ep in (True, False):
            m = e1 == ep
            if m.any() and ep in mean:
                Z[m] = (X[m] - mean[ep]) / sd[ep]
        return Z
    return (X - mean[True]) / sd[True]


def _design(Z, e1, interactions):
    e1f = e1.astype(float)
    e2f = 1.0 - e1f
    if interactions == "epoch":
        D = np.column_stack([e1f, e2f, Z * e1f[:, None], Z * e2f[:, None]])
    else:
        D = np.column_stack([e1f, e2f, Z])
    pen = np.ones(D.shape[1])
    pen[:2] = 0.0
    return D, pen


def fit_ridge(X: np.ndarray, e1: np.ndarray, y: np.ndarray, w: np.ndarray, alpha: float,
              interactions: str = "epoch") -> RidgeModel:
    """Weighted ridge: minimise Σw(y − Dβ)²/Σw + α‖β_slopes‖²; features standardised (weighted) on the
    training rows (per epoch when interactions='epoch'); the two epoch intercepts are unpenalised."""
    mean, sd = {}, {}
    for ep in ([True, False] if interactions == "epoch" else [True]):
        m = (e1 == ep) if interactions == "epoch" else np.ones(len(e1), bool)
        if m.sum() == 0:
            continue
        ww = w[m] / w[m].sum()
        mu = (ww[:, None] * X[m]).sum(axis=0)
        s = np.sqrt((ww[:, None] * (X[m] - mu) ** 2).sum(axis=0))
        mean[ep], sd[ep] = mu, np.where(s > 1e-12, s, np.inf)  # constant feature -> column of zeros
    Z = _standardize(X, e1, mean, sd, interactions)
    D, pen = _design(Z, e1, interactions)
    sw = w.sum()
    M = (D * w[:, None]).T @ D / sw + alpha * np.diag(pen)
    rhs = (D * w[:, None]).T @ y / sw
    present = set(bool(v) for v in np.unique(e1))
    for j, ep in ((0, True), (1, False)):
        if ep not in present:
            M[j, j] = 1.0
    return RidgeModel(np.linalg.solve(M, rhs), mean, sd, present, interactions)


fit_c_hat = fit_ridge  # revision-3 name


def predict_ridge(model: RidgeModel, X: np.ndarray, e1: np.ndarray) -> np.ndarray:
    Z = _standardize(X, e1, model.mean, model.sd, model.interactions)
    D, _ = _design(Z, e1, model.interactions)
    out = D @ model.coef
    for ep in (True, False):
        if ep not in model.trained_epochs:
            out[e1 == ep] = np.nan
    return out


predict_c_hat = predict_ridge


def assign_folds(cluster_keys: Sequence[str], n_folds: int, rng: np.random.Generator) -> dict[str, int]:
    """Instance-level folds: unique cluster keys sorted, permuted by ``rng``, dealt round-robin. A bootstrap
    copy of an instance carries its original id, so all copies land in one fold."""
    keys = sorted(set(cluster_keys))
    if len(keys) < n_folds:
        raise TrackSAnalysisError(f"{len(keys)} instances < {n_folds} folds")
    perm = rng.permutation(len(keys))
    return {keys[p]: k % n_folds for k, p in enumerate(perm)}


# ============================================================================================= value-tuned static rule
def _best_threshold(score: np.ndarray, qbar: np.ndarray, w: np.ndarray, grid: Sequence[float]) -> float:
    """argmax_t Σ w·1{score > t}·ΔQ over a declared grid (IPW total-Q value relative to never acting);
    ties go to the threshold with the smallest |t|, then the smaller t."""
    if score.size == 0:
        return float("nan")
    g = np.asarray(sorted(grid, key=lambda t: (abs(t), t)), dtype=float)
    vals = ((score[None, :] > g[:, None]) * (w * qbar)[None, :]).sum(axis=1)
    return float(g[int(np.argmax(vals))])


def tune_thresholds(ihat, e1, qbar, w, g_grid, h_grid) -> tuple[float, float]:
    return (_best_threshold(ihat[e1], qbar[e1], w[e1], g_grid),
            _best_threshold(ihat[~e1], qbar[~e1], w[~e1], h_grid))


@dataclass
class TotalQFit:
    f_hat: np.ndarray
    i_hat: np.ndarray
    g_row: np.ndarray
    h_row: np.ndarray
    g_folds: list[float]
    h_folds: list[float]


def crossfit_total_q(X, e1, qbar, immbar, w, fold_row, n_folds, pd: Predeclaration, rng: np.random.Generator,
                     cluster_keys: np.ndarray, min_train: int = 2) -> TotalQFit:
    """Outer instance-level cross-fit of f̂ (ΔQ) and Î (immediate); (ĝ, ĥ) tuned inside each outer training
    set on inner cross-fitted Î (nested), so the held-out fold never informs its own thresholds."""
    n = len(qbar)
    f_hat, i_hat = np.full(n, np.nan), np.full(n, np.nan)
    g_row, h_row = np.full(n, np.nan), np.full(n, np.nan)
    gs, hs = [], []
    inner_seed = int(rng.integers(0, 2 ** 31 - 1))
    for k in range(n_folds):
        te = fold_row == k
        tr = ~te
        if not te.any():
            gs.append(float("nan"))
            hs.append(float("nan"))
            continue
        fm = fit_ridge(X[tr], e1[tr], qbar[tr], w[tr], pd.ridge_alpha, pd.interactions)
        im = fit_ridge(X[tr], e1[tr], immbar[tr], w[tr], pd.ridge_alpha, pd.interactions)
        f_hat[te] = predict_ridge(fm, X[te], e1[te])
        i_hat[te] = predict_ridge(im, X[te], e1[te])
        for ep in (True, False):
            if (tr & (e1 == ep)).sum() < min_train:
                f_hat[te & (e1 == ep)] = np.nan
                i_hat[te & (e1 == ep)] = np.nan
        # inner cross-fit of Î on the training set for threshold tuning
        tr_idx = np.flatnonzero(tr)
        keys_tr = cluster_keys[tr_idx]
        n_inner = min(n_folds - 1, len(set(keys_tr.tolist())))
        ihat_in = np.full(len(tr_idx), np.nan)
        if n_inner >= 2:
            imap = assign_folds(keys_tr.tolist(), n_inner, np.random.default_rng([inner_seed, k]))
            ifold = np.array([imap[c] for c in keys_tr])
            for j in range(n_inner):
                ite, itr = ifold == j, ifold != j
                mdl = fit_ridge(X[tr_idx][itr], e1[tr_idx][itr], immbar[tr_idx][itr], w[tr_idx][itr],
                                pd.ridge_alpha, pd.interactions)
                ihat_in[ite] = predict_ridge(mdl, X[tr_idx][ite], e1[tr_idx][ite])
        ok = ~np.isnan(ihat_in)
        g, h = tune_thresholds(ihat_in[ok], e1[tr_idx][ok], qbar[tr_idx][ok], w[tr_idx][ok], pd.g_grid, pd.h_grid)
        gs.append(g)
        hs.append(h)
        g_row[te], h_row[te] = g, h
    return TotalQFit(f_hat, i_hat, g_row, h_row, gs, hs)


def pi_prime_act(f_hat: np.ndarray) -> np.ndarray:
    """π′: execute / keep iff f̂(s) > 0."""
    return f_hat > 0


def m_tilde_act(e1, i_hat, g_row, h_row) -> np.ndarray:
    """m̃: execute iff Î(s) > ĝ (E1); keep iff Î(s) > ĥ (E2)."""
    return np.where(e1, i_hat > g_row, i_hat > h_row)


# ============================================================================================= revision-3 hybrid (secondary)
def cross_fit_hybrid(X, e1, index, dbar, w, fold_row, n_folds, alpha, interactions, min_train=2):
    """Revision-3 secondary: Ĉ on ΔC and ĝ_fold = −mean training-fold E1 ΔC."""
    n = len(index)
    c_hat, ghat_row, ghats = np.full(n, np.nan), np.full(n, np.nan), []
    for k in range(n_folds):
        te = fold_row == k
        tr = ~te
        if not te.any():
            ghats.append(float("nan"))
            continue
        tr_e1 = tr & e1
        ghat = -_wmean(dbar[tr_e1], w[tr_e1]) if tr_e1.sum() >= min_train else float("nan")
        ghats.append(ghat)
        ghat_row[te] = ghat
        model = fit_ridge(X[tr], e1[tr], dbar[tr], w[tr], alpha, interactions)
        pred = predict_ridge(model, X[te], e1[te])
        for ep in (True, False):
            if (tr & (e1 == ep)).sum() < min_train:
                pred[e1[te] == ep] = np.nan
        c_hat[te] = pred
    return c_hat, ghat_row, ghats


def myopic_policy(e1, index, ghat_row):
    """Revision-3 m_ĝ: execute iff V̂* ≥ ĝ (E1); keep iff m̂ > 0 (E2)."""
    return np.where(e1, index >= ghat_row, index > 0)


def improved_policy(index, c_hat):
    """Revision-3 hybrid π′: act iff index + Ĉ(s) > 0."""
    return index + c_hat > 0


def u_split(index, d_rep, m_act, w) -> tuple[float, int]:
    """Split-repetition quantity (descriptive): choose by rep-1 hybrid score, evaluate on rep 2 against m; swap;
    average. Unbiased for the gain of that rep-1-chooser over m (choice and evaluation are independent given s)."""
    both = ~np.isnan(d_rep).any(axis=1)
    if not both.any():
        return float("nan"), 0
    s1, s2 = index[both] + d_rep[both, 0], index[both] + d_rep[both, 1]
    m = m_act[both]
    a1, a2 = s1 > 0, s2 > 0
    u = 0.5 * ((a1 != m) * np.where(a1, 1.0, -1.0) * s2 + (a2 != m) * np.where(a2, 1.0, -1.0) * s1)
    return _wmean(u, w[both]), int(both.sum())


def _nanmean_list(x) -> float:
    a = np.asarray(x, float)
    a = a[~np.isnan(a)]
    return float(a.mean()) if a.size else float("nan")


def _flip_value(p_act, m_act, diff, w) -> float:
    return _wmean((p_act != m_act) * np.where(p_act, 1.0, -1.0) * diff, w)


# ============================================================================================= one fit (point or replicate)
FORK_KEYS = ("TQ_pi_vs_mtilde", "flip_rate_pi_vs_mtilde", "g_tilde", "h_tilde", "TQ_pi_vs_root_myopic",
             "hybrid_I_seq", "hybrid_total_Q", "hybrid_cont_only", "U_split", "hybrid_ghat") + CHANNELS + (
    "e1_exec_minus_skip_Q",)


def channel_means(ft: ForkTable, rows: np.ndarray) -> dict[str, float]:
    out = {}
    for c in CHANNELS:
        v = _nanmean_rows(ft.chan_rep[c][rows])
        ok = ~np.isnan(v)
        out[c] = _wmean(v[ok], ft.w[rows][ok]) if ok.any() else float("nan")
    e1 = ft.e1[rows]
    out["e1_exec_minus_skip_Q"] = _wmean(ft.qbar[rows][e1], ft.w[rows][e1]) if e1.any() else float("nan")
    return out


def fork_fit(ft: ForkTable, pd: Predeclaration, rows: np.ndarray | None = None,
             rng: np.random.Generator | None = None) -> dict:
    if rows is None:
        rows = np.arange(len(ft))
    rng = rng if rng is not None else np.random.default_rng(pd.seed)
    keys = ft.instance[rows]
    fmap = assign_folds(keys.tolist(), pd.folds, rng)
    fold_row = np.array([fmap[k] for k in keys])
    X, e1, idx, w = ft.X[rows], ft.e1[rows], ft.index[rows], ft.w[rows]
    qbar, dbar, imm, d_rep = ft.qbar[rows], ft.dbar[rows], ft.immbar[rows], ft.d_rep[rows]
    tq = crossfit_total_q(X, e1, qbar, imm, w, fold_row, pd.folds, pd, rng, keys)
    c_hat, ghat_row, ghats = cross_fit_hybrid(X, e1, idx, dbar, w, fold_row, pd.folds, pd.ridge_alpha,
                                              pd.interactions)
    est: dict[str, float] = {}
    bad = np.isnan(tq.f_hat).any() or np.isnan(tq.i_hat).any() or np.isnan(c_hat).any()
    if bad:
        est = {k: float("nan") for k in FORK_KEYS}
    else:
        p = pi_prime_act(tq.f_hat)
        m = m_tilde_act(e1, tq.i_hat, tq.g_row, tq.h_row)
        est["TQ_pi_vs_mtilde"] = _flip_value(p, m, qbar, w)
        est["flip_rate_pi_vs_mtilde"] = _wmean((p != m).astype(float), w)
        est["TQ_pi_vs_root_myopic"] = _flip_value(p, ft.myopic_act[rows], qbar, w)
        est["g_tilde"] = _nanmean_list(tq.g_folds)
        est["h_tilde"] = _nanmean_list(tq.h_folds)
        mh = myopic_policy(e1, idx, ghat_row)
        ph = improved_policy(idx, c_hat)
        est["hybrid_I_seq"] = _flip_value(ph, mh, idx + dbar, w)
        est["hybrid_total_Q"] = _flip_value(ph, mh, qbar, w)
        est["hybrid_cont_only"] = _flip_value(ph, mh, dbar, w)
        est["U_split"] = u_split(idx, d_rep, mh, w)[0]
        est["hybrid_ghat"] = _nanmean_list(ghats)
    est.update(channel_means(ft, rows))
    return {"est": est, "tq": tq, "c_hat": c_hat, "ghat_row": ghat_row}


def refitting_bootstrap(ft: ForkTable, pd: Predeclaration) -> dict:
    """Instance-cluster bootstrap; every replicate redraws folds from (seed, b) and refits f̂, Î, (ĝ, ĥ), Ĉ, ĝ.
    Duplicated clusters keep their original id, hence share a fold."""
    insts = sorted(set(ft.instance.tolist()))
    rows_of = {i: np.flatnonzero(ft.instance == i) for i in insts}
    draws = {k: [] for k in FORK_KEYS}
    degenerate = 0
    for b in range(pd.bootstrap_B):
        rng = np.random.default_rng([pd.seed, b + 1])
        picked = rng.choice(len(insts), size=len(insts), replace=True)
        rows = np.concatenate([rows_of[insts[k]] for k in picked])
        try:
            est = fork_fit(ft, pd, rows, rng)["est"]
        except TrackSAnalysisError:
            degenerate += 1
            continue
        if math.isnan(est["TQ_pi_vs_mtilde"]):
            degenerate += 1
            continue
        for k in FORK_KEYS:
            draws[k].append(est[k])
    return {"draws": {k: np.asarray(v) for k, v in draws.items()}, "n_boot": pd.bootstrap_B,
            "n_degenerate": degenerate}


def _q(x: np.ndarray, p: float) -> float:
    x = x[~np.isnan(x)]
    return float(np.quantile(x, p)) if x.size else float("nan")


def summarize(est: float, draws: np.ndarray, label: str) -> dict:
    return {"est": est, "lb975": _q(draws, 0.025), "lb95": _q(draws, 0.05), "ub95": _q(draws, 0.95),
            "ci95": [_q(draws, 0.025), _q(draws, 0.975)], "n_draws": int((~np.isnan(draws)).sum()), "label": label}


def analyze_forks(ft: ForkTable, decl: NodeDecl, pd: Predeclaration) -> dict:
    point = fork_fit(ft, pd)
    boot = refitting_bootstrap(ft, pd)
    lab = ft.label
    s = {k: summarize(point["est"][k], boot["draws"][k], lab) for k in FORK_KEYS}
    return {"label": lab, "host": ft.host, "n_instances": int(len(set(ft.instance.tolist()))), "n_forks": len(ft),
            "n_forks_E1": int(ft.e1.sum()), "n_forks_E2": int((~ft.e1).sum()), "counts": ft.counts,
            "estimates": s, "g_tilde_folds": point["tq"].g_folds, "h_tilde_folds": point["tq"].h_folds,
            "n_boot": boot["n_boot"], "n_degenerate": boot["n_degenerate"], "descriptive": ft.descriptive,
            "delta_dec_rev3": decl.delta_dec, "note": "descriptive / attribution only; does not decide the route"}


# ============================================================================================= policy serialisation
def _ridge_to_json(m: RidgeModel) -> dict:
    std = {}
    for ep, name in ((True, "E1"), (False, "E2")):
        if ep in m.mean:
            sd = m.sd[ep]
            std[name if m.interactions == "epoch" else "all"] = {
                "mean": m.mean[ep].tolist(), "sd": [float(x) if math.isfinite(x) else None for x in sd]}
    return {"coef": m.coef.tolist(), "standardization": std, "trained_epochs": sorted("E1" if e else "E2" for e in
                                                                                       m.trained_epochs)}


def _ridge_from_json(d: dict, interactions: str) -> RidgeModel:
    mean, sd = {}, {}
    for name, ep in (("E1", True), ("E2", False), ("all", True)):
        if name in d["standardization"]:
            st = d["standardization"][name]
            mean[ep] = np.asarray(st["mean"], float)
            sd[ep] = np.asarray([np.inf if x is None else x for x in st["sd"]], float)
    return RidgeModel(np.asarray(d["coef"], float), mean, sd, {e == "E1" for e in d["trained_epochs"]}, interactions)


def fit_policies(ft: ForkTable, pd: Predeclaration) -> dict[str, dict]:
    """Fit π′ (f̂ on all forks) and m̃ (Î on all forks, (ĝ, ĥ) tuned on cross-fitted Î) for deployment."""
    X, e1, w = ft.X, ft.e1, ft.w
    fm = fit_ridge(X, e1, ft.qbar, w, pd.ridge_alpha, pd.interactions)
    im = fit_ridge(X, e1, ft.immbar, w, pd.ridge_alpha, pd.interactions)
    rng = np.random.default_rng(pd.seed)
    fmap = assign_folds(ft.instance.tolist(), pd.folds, rng)
    fold_row = np.array([fmap[k] for k in ft.instance])
    ihat = np.full(len(ft), np.nan)
    for k in range(pd.folds):
        te = fold_row == k
        ihat[te] = predict_ridge(fit_ridge(X[~te], e1[~te], ft.immbar[~te], w[~te], pd.ridge_alpha, pd.interactions),
                                 X[te], e1[te])
    ok = ~np.isnan(ihat)
    g, h = tune_thresholds(ihat[ok], e1[ok], ft.qbar[ok], w[ok], pd.g_grid, pd.h_grid)
    common = {"schema": POLICY_SCHEMA, "node": ft.node, "features": list(STATE_FEATURES),
              "interactions": pd.interactions, "ridge_alpha": pd.ridge_alpha, "label": ft.label, "host": ft.host,
              "n_forks": len(ft), "fork_ids_sha256": hashlib.sha256("\n".join(ft.fork_id).encode()).hexdigest()}
    return {"pi_prime": {**common, "kind": "pi_prime", "target": "Q_act - Q_not", **_ridge_to_json(fm),
                         "thresholds": {"E1": 0.0, "E2": 0.0}},
            "m_tilde": {**common, "kind": "m_tilde", "target": "immediate_measured(act)", **_ridge_to_json(im),
                        "thresholds": {"E1": g, "E2": h}}}


def policy_bytes(pol: dict) -> bytes:
    return json.dumps(pol, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def policy_sha256(pol: dict) -> str:
    return hashlib.sha256(policy_bytes(pol)).hexdigest()


def write_policy(pol: dict, path: Path) -> str:
    """Write the canonical JSON bytes; return their sha256 (the collector's ``pi_prime:<model_file>``)."""
    b = policy_bytes(pol)
    Path(path).write_bytes(b)
    return hashlib.sha256(b).hexdigest()


def load_policy(path: Path, sha256: str | None = None) -> dict:
    b = Path(path).read_bytes()
    if sha256 is not None and hashlib.sha256(b).hexdigest() != sha256:
        raise TrackSAnalysisError(f"policy file {path}: sha256 mismatch")
    pol = json.loads(b)
    if pol.get("schema") != POLICY_SCHEMA or pol.get("features") != list(STATE_FEATURES):
        raise TrackSAnalysisError(f"policy file {path}: schema or feature order mismatch")
    return pol


def policy_score(pol: dict, state: dict, epoch: str) -> float:
    """Model output minus the epoch's threshold; act iff > 0."""
    model = _ridge_from_json(pol, pol["interactions"])
    x = np.asarray([[float(state[k]) for k in pol["features"]]])
    e1 = np.asarray([epoch == "E1"])
    return float(predict_ridge(model, x, e1)[0] - pol["thresholds"][epoch])


def policy_act(pol: dict, state: dict, epoch: str) -> bool:
    return policy_score(pol, state, epoch) > 0


# ============================================================================================= campaign level: records
def rep_of(r) -> int:
    return int(getattr(r, "rep", 1) or 1)


def _ok_root(r) -> bool:
    return r.status == "ok" and r.y_terminal is not None and math.isfinite(r.y_terminal)


def per_instance_means(roots: Sequence[RootRecord], policy: str) -> dict[str, float]:
    """Mean Y per instance over distinct LLM repetitions (a duplicate root of the same repetition — the exact
    placebo — is not counted twice)."""
    by: dict[str, dict[int, float]] = {}
    for r in roots:
        if policy_of(r) == policy and _ok_root(r):
            by.setdefault(r.instance_id, {}).setdefault(rep_of(r), float(r.y_terminal))
    return {i: float(np.mean(list(v.values()))) for i, v in by.items()}


def campaign_pairs(roots: Sequence[RootRecord], candidate: str, comparator: str) -> dict:
    """D_i = Ȳ_i(candidate) − Ȳ_i(comparator), paired by instance (means over LLM repetitions)."""
    a, b = per_instance_means(roots, candidate), per_instance_means(roots, comparator)
    paired = sorted(set(a) & set(b))
    failed = sum(1 for r in roots if policy_of(r) in (candidate, comparator) and not _ok_root(r))
    return {"instances": paired, "D": np.array([a[i] - b[i] for i in paired]),
            "n_unpaired": len(set(a) ^ set(b)), "n_failed": failed}


def mean_test(D: np.ndarray, *, alpha: float = 0.05) -> dict:
    """Paired one-sample t over instances: one-sided LB/UB at 1 − alpha, one-sided p for mean > 0, z = mean/se."""
    D = np.asarray(D, float)
    n = len(D)
    if n < 2:
        raise TrackSAnalysisError(f"campaign test needs >= 2 paired instances, got {n}")
    m, sd = float(D.mean()), float(D.std(ddof=1))
    se = sd / math.sqrt(n)
    q, q2 = float(t_dist.ppf(1 - alpha, n - 1)), float(t_dist.ppf(1 - alpha / 2, n - 1))
    if se > 0:
        z = m / se
        p_one, p_two = float(t_dist.sf(z, n - 1)), float(2 * t_dist.sf(abs(z), n - 1))
    else:
        z = 0.0 if m == 0 else math.copysign(math.inf, m)
        p_one, p_two = (0.0 if m > 0 else 1.0), (0.0 if m != 0 else 1.0)
    return {"n": n, "mean": m, "sd": sd, "se": se, "z": z, "lb": m - q * se, "ub": m + q * se,
            "ci_two_sided": [m - q2 * se, m + q2 * se], "p_one_sided": p_one, "p_two_sided": p_two,
            "alpha": alpha, "method": "paired t (instances iid)"}


def campaign_route(test: dict, delta_Y: float) -> str:
    """Single-node outcome at the test's alpha (no Holm, no B gates): A (LB > 0, UB ≥ δ_Y), A-small (LB > 0,
    UB < δ_Y), B-bound (UB < δ_Y; B proper needs the gates), else inconclusive. Used for controls."""
    if test["lb"] > 0:
        return "A-small" if test["ub"] < delta_Y else "A"
    if test["ub"] < delta_Y:
        return "B"
    return "inconclusive"


# ============================================================================================= selection (dev tuning)
def family_matrix(dev_roots: Sequence[RootRecord], configs: Sequence[str]) -> dict:
    means = {c: per_instance_means(dev_roots, c) for c in configs}
    insts = sorted(set().union(*[set(m) for m in means.values()])) if means else []
    Y = np.full((len(configs), len(insts)), np.nan)
    for a, c in enumerate(configs):
        for b, i in enumerate(insts):
            if i in means[c]:
                Y[a, b] = means[c][i]
    return {"configs": list(configs), "instances": insts, "Y": Y}


def _row_means(Y: np.ndarray) -> np.ndarray:
    return np.array([np.nanmean(row) if np.isfinite(row).any() else np.nan for row in Y])


def _argmax_simplest(configs: Sequence[str], vals: np.ndarray) -> int:
    """Highest mean; exact ties go to the simpler member (smaller |parameters|, then string order)."""
    best = np.nanmax(vals)
    tied = [k for k, v in enumerate(vals) if np.isfinite(v) and abs(v - best) <= 1e-12]
    return min(tied, key=lambda k: (sum(abs(x) for x in parse_policy(configs[k])[1]), configs[k]))


def select_static(dev_roots: Sequence[RootRecord], fam: FamilyDecl, sigma_node: float) -> dict:
    """m* = highest mean dev Y on the 12-configuration grid; if m* is on the upper g edge, the grid is extended
    once to g_ext (3 more configurations, same dev instances) and m* is re-selected over the 15."""
    cfgs = fam.static_configs(sigma_node)
    fm = family_matrix(dev_roots, cfgs)
    if fm["Y"].size == 0 or np.isnan(fm["Y"]).all():
        raise TrackSAnalysisError("selection: no dev campaigns for the static grid")
    vals = _row_means(fm["Y"])
    k = _argmax_simplest(cfgs, vals)
    out = {"extended": False, "extension_needed": False}
    if fam.on_upper_edge(cfgs[k], sigma_node):
        ext = fam.extension_configs(sigma_node)
        have = {policy_of(r) for r in dev_roots}
        if not all(c in have for c in ext):
            out.update(extension_needed=True, extension_configs=ext)
        else:
            cfgs = fam.static_configs(sigma_node, extended=True)
            fm = family_matrix(dev_roots, cfgs)
            vals = _row_means(fm["Y"])
            k = _argmax_simplest(cfgs, vals)
            out["extended"] = True
    out.update(m_star=cfgs[k], m_star_dev_mean=float(vals[k]), means=dict(zip(cfgs, map(float, vals))), _matrix=fm)
    return out


class MissingDev(Exception):
    """A tuning step needs dev campaigns that are not in the data: ``needed`` = [(policy, instance_id), ...]."""

    def __init__(self, needed):
        super().__init__(f"{len(needed)} dev campaigns needed")
        self.needed = needed


def _dev_lookup(dev_roots: Sequence[RootRecord]) -> tuple[dict, list[str]]:
    table: dict[tuple[str, str], float] = {}
    for r in dev_roots:
        if _ok_root(r):
            table.setdefault((policy_of(r), r.instance_id), float(r.y_terminal))
    insts = sorted({i for _, i in table} | {r.instance_id for r in dev_roots})
    return table, insts


def halving_schedule(n_members: int, budget: int) -> list[tuple[int, int]]:
    """Successive halving: [(survivors, cumulative instances per survivor)] per round; equal budget per round."""
    rounds, m, sched, cum = max(1, math.ceil(math.log2(max(n_members, 2)))), n_members, [], 0
    per_round = budget / rounds
    for _ in range(rounds):
        cum += max(1, int(per_round // m))
        sched.append((m, cum))
        m = max(1, math.ceil(m / 2))
        if len(sched) == rounds:
            break
    return sched


def tune_members(get, members: dict[str, str], tuning: dict) -> dict:
    """Select π* among ``members`` (name -> policy) with the declared procedure; ``get(policy, k)`` returns the dev
    Y of a policy on paired dev instance k (raises KeyError if missing). Returns winner, campaigns used, log."""
    names = list(members)
    used: set[tuple[str, int]] = set()
    needed: list[tuple[str, int]] = []

    def means(sub, k):
        out = []
        for nm in sub:
            vals = []
            for i in range(k):
                try:
                    vals.append(get(members[nm], i))
                    used.add((members[nm], i))
                except KeyError:
                    needed.append((members[nm], i))
            out.append(float(np.mean(vals)) if vals else float("nan"))
        if needed:
            raise MissingDev(list(needed))
        return np.asarray(out)

    def best(sub, vals):
        cf = [members[nm] for nm in sub]
        return sub[_argmax_simplest(cf, vals)]

    proc = tuning.get("procedure", "argmax")
    log = []
    if proc == "argmax":
        n = int(tuning.get("n_dev", 20))
        v = means(names, n)
        win = best(names, v)
        log.append({"round": 1, "members": names, "n": n, "means": v.tolist()})
    elif proc == "halving":
        sub = names
        for rnd, (m, cum) in enumerate(halving_schedule(len(names), int(tuning["member_budget"])), 1):
            v = means(sub, cum)
            log.append({"round": rnd, "members": list(sub), "n": cum, "means": v.tolist()})
            if len(sub) == 1:
                break
            keep = max(1, math.ceil(len(sub) / 2))
            order = sorted(range(len(sub)), key=lambda k: (-v[k], complexity_key(members[sub[k]])))
            sub = [sub[k] for k in order[:keep]]
        if len(sub) > 1:
            v = means(sub, log[-1]["n"])
            sub = [best(sub, v)]
        win = sub[0]
    elif proc == "channel_first":
        n1, n2 = int(tuning.get("n1", 20)), int(tuning.get("n2", 60))
        chans = sorted({nm.split("×")[0] for nm in names})
        mids = []
        for ch in chans:
            sizes = [nm for nm in names if nm.split("×")[0] == ch]
            mids.append(sizes[len(sizes) // 2])
        v = means(mids, n1)
        ch = best(mids, v).split("×")[0]
        log.append({"round": 1, "members": mids, "n": n1, "means": v.tolist()})
        sizes = [nm for nm in names if nm.split("×")[0] == ch]
        v = means(sizes, n2)
        win = best(sizes, v)
        log.append({"round": 2, "members": sizes, "n": n2, "means": v.tolist()})
    else:
        raise TrackSAnalysisError(f"unknown tuning procedure {proc!r}")
    return {"winner": win, "policy": members[win], "campaigns": len(used), "log": log, "procedure": proc}


def complexity_key(s: str) -> tuple:
    return (sum(abs(x) for x in parse_policy(s)[1][:5]), s)


def select_dynamic(dev_roots: Sequence[RootRecord], fam: FamilyDecl, m_star: str, sigma_node: float,
                   tuning: dict | None = None) -> dict:
    """Members anchored at m* and centred at m*'s dev decision means; π* by the declared tuning procedure."""
    centres = decision_centres(_decisions_of(dev_roots, m_star))
    members = fam.members(m_star, sigma_node, centres)
    table, insts = _dev_lookup(dev_roots)

    def inst_id(k):  # paired dev instances in sorted id order; beyond the data, the collector's naming d0000…
        return insts[k] if k < len(insts) else f"d{k:04d}"

    def get(pol, k):
        return table[(pol, inst_id(k))]

    try:
        t = tune_members(get, members, tuning or {"procedure": "argmax", "n_dev": 20})
    except MissingDev as m:
        return {"status": "members_needed", "members": members, "centres": centres,
                "missing": sorted({(p, inst_id(k)) for p, k in m.needed})}
    name = t["winner"]
    pi_vals = [table[(t["policy"], i)] for i in insts if (t["policy"], i) in table]
    return {"status": "ok", "members": members, "centres": centres, "pi_star": t["policy"],
            "pi_star_channel": name.split("×")[0], "pi_star_member": name,
            "pi_star_dev_mean": float(np.mean(pi_vals)), "tuning": {k: v for k, v in t.items() if k != "policy"},
            "_table": table, "_insts": insts}


def _decisions_of(roots: Sequence[RootRecord], policy: str) -> list[dict]:
    out = []
    for r in roots:
        if policy_of(r) == policy and _ok_root(r):
            out += [d for d in (r.decisions or []) if d.get("eligible")]
    return out


def flip_rate(dev_roots: Sequence[RootRecord], pi_star: str, m_star: str) -> dict:
    """Share of π*'s eligible dev decisions at which m* would have acted differently (same state)."""
    ds = _decisions_of(dev_roots, pi_star)
    need = ("epoch", "action", "index_value", "budget_fraction")
    usable = [d for d in ds if all(k in d for k in need) and (d["epoch"] == "E2" or "tau_pred" in d
                                                              or as_dynamic(m_star)[2] == 0.0)]
    if not usable:
        return {"flip_rate": None, "n": 0, "note": "dev decisions lack state fields (epoch, action, index_value, "
                                                    "budget_fraction, tau_pred)"}
    flips, eps = [], []
    for d in usable:
        st = {"budget_fraction": d["budget_fraction"], "index_value": d["index_value"]}
        pi_act = d["action"] in ("execute", "keep")
        flips.append(threshold_act(m_star, st, d["epoch"], d.get("tau_pred")) != pi_act)
        eps.append(d["epoch"])
    f, e = np.asarray(flips, float), np.asarray(eps)
    by = {ep: (float(f[e == ep].mean()) if (e == ep).any() else None) for ep in ("E1", "E2")}
    return {"flip_rate": float(f.mean()), "flip_rate_E1": by["E1"], "flip_rate_E2": by["E2"], "n": len(flips),
            "n_E1": int((e == "E1").sum()), "n_E2": int((e == "E2").sum()),
            "note": "the ≥ 10 % B condition applies to the overall rate"}


def matched_static(dev_roots: Sequence[RootRecord], pi_star: str) -> dict:
    eff = effective_thresholds(pi_star, _decisions_of(dev_roots, pi_star))
    eff["policy"] = policy_string("static", (eff["g_eff"], eff["h_eff"]))
    return eff


def dev_sigma_ucl(sel_s: dict, sel_d: dict, conf: float = 0.8) -> dict:
    """S0.7 dev estimate: sd over the paired dev instances (where both ran) of Y(π*) − Y(m*), with its UCL."""
    table = sel_d["_table"]
    D = [table[(sel_d["pi_star"], i)] - table[(sel_s["m_star"], i)] for i in sel_d["_insts"]
         if (sel_d["pi_star"], i) in table and (sel_s["m_star"], i) in table]
    D = np.asarray(D, float)
    if len(D) < 2:
        return {"sigma_hat": None, "ucl": None, "m": len(D)}
    s = float(D.std(ddof=1))
    return {"sigma_hat": s, "ucl": sigma_D_ucl(s, len(D), conf) if s > 0 else 0.0, "m": len(D),
            "dev_gap": float(D.mean())}


def winners_curse(sel_s: dict, sel_d: dict, fresh_gap: float | None, *, splits: int = 200, seed: int = 0) -> dict:
    """Dev gap of the winners on their common dev instances vs the fresh gap; split-half optimism of the static
    stage (select on one half of the paired dev instances, evaluate on the other)."""
    table = sel_d["_table"]
    common = [i for i in sel_d["_insts"] if (sel_d["pi_star"], i) in table and (sel_s["m_star"], i) in table]
    dev_gap = float(np.mean([table[(sel_d["pi_star"], i)] - table[(sel_s["m_star"], i)] for i in common])) \
        if common else None
    Ms = sel_s["_matrix"]
    Ys, n = Ms["Y"], len(Ms["instances"])
    rng = np.random.default_rng([seed, 4242])
    opt = []
    for _ in range(splits if n >= 4 else 0):
        perm = rng.permutation(n)
        h1, h2 = perm[: n // 2], perm[n // 2:]
        v1 = np.nanmean(Ys[:, h1], axis=1)
        k = _argmax_simplest(Ms["configs"], v1)
        opt.append(float(v1[k] - np.nanmean(Ys[k, h2])))
    return {"dev_gap_winners": dev_gap, "fresh_gap": fresh_gap,
            "shrinkage_dev_minus_fresh": (dev_gap - fresh_gap) if (dev_gap is not None and fresh_gap is not None)
            else None, "split_half_optimism": {"static": float(np.mean(opt)) if opt else None, "gap": None},
            "member_tuning_log": sel_d.get("tuning", {}).get("log"),
            "note": "the fresh S3e test is free of selection bias; these numbers describe dev optimism only"}


# ============================================================================================= placebos and gates
def placebo_exact(roots: Sequence[RootRecord], policy: str) -> dict:
    """Same policy, same instance, same LLM repetition run twice: D must be exactly 0; anything else is a STOP."""
    by: dict[tuple[str, int], list[float]] = {}
    for r in roots:
        if policy_of(r) == policy and _ok_root(r):
            by.setdefault((r.instance_id, rep_of(r)), []).append(float(r.y_terminal))
    groups = {k: v for k, v in by.items() if len(v) >= 2}
    bad = sorted(f"{i}/rep{rp}" for (i, rp), v in groups.items() if any(x != v[0] for x in v))
    status = "missing" if not groups else ("STOP" if bad else "pass")
    return {"policy": policy, "n_groups": len(groups), "mismatches": bad[:20], "n_mismatch": len(bad),
            "status": status}


def placebo_descriptive(roots: Sequence[RootRecord], policy: str, *, z_stop: float = 3.5, alpha: float = 0.05) -> dict:
    """Same policy at LLM repetitions 1 and 2 on the same instances: z of mean D reported; STOP only if |z| > z_stop."""
    reps: dict[str, dict[int, float]] = {}
    for r in roots:
        if policy_of(r) == policy and _ok_root(r):
            reps.setdefault(r.instance_id, {}).setdefault(rep_of(r), float(r.y_terminal))
    D = [v[1] - v[2] for v in reps.values() if 1 in v and 2 in v]
    if len(D) < 2:
        return {"policy": policy, "status": "missing", "n": len(D), "z": None}
    t = mean_test(np.asarray(D), alpha=alpha)
    return {"policy": policy, "test": t, "z": t["z"], "status": "STOP" if abs(t["z"]) > z_stop else "pass",
            "z_stop": z_stop, "n": t["n"]}


def fp_gate(k_A: int, R: int, *, alpha: float = 0.05, k_stop: int = 19, R_decl: int = 200,
            p_crit: float = 0.01) -> dict:
    """S0.6 false-positive check on N0 (STOP only on a significantly high route-A rate). At the declared R the
    declared count rule applies (revision 7: ≥ 19 of 200, i.e. exact one-sided binomial p < 0.01); otherwise the
    exact p < p_crit."""
    p = float(binom.sf(k_A - 1, R, alpha)) if k_A > 0 else 1.0
    stop = (k_A >= k_stop) if R == R_decl else (p < p_crit)
    return {"k_A": k_A, "R": R, "rate": k_A / R, "rate_ci95": list(clopper_pearson(k_A, R)), "p_binom": p,
            "stop": bool(stop), "rule": f"k >= {k_stop} of {R_decl}" if R == R_decl else f"exact p < {p_crit}",
            "alpha": alpha}


def power_gate(k_A: int, R: int, *, lb_min: float = 0.6) -> dict:
    lo, hi = clopper_pearson(k_A, R)
    return {"k_A": k_A, "R": R, "power": k_A / R, "ci95": [lo, hi], "lb_min": lb_min, "ok": bool(lo >= lb_min)}


CONTROL_VARIANTS = tuple((c, v) for c in ("P0", "P1", "P2+", "P2-") for v in ("diffuse", "concentrated"))


def resize_rule(gates_initial: dict[str, dict], n_initial: int = 20, n_resized: int = 40) -> dict:
    """The one pre-declared resize: if any P variant's power LB < 0.6 at n_dev = n_initial, resize to n_resized
    once (the gates are then rerun at n_resized and are final)."""
    failing = sorted(k for k, g in gates_initial.items() if not g["ok"])
    return {"resize": bool(failing), "n_dev": n_resized if failing else n_initial, "failing_at_initial": failing}


# ============================================================================================= sizing
def sigma_D_ucl(sigma_hat: float, m_pairs: int, conf: float = 0.8) -> float:
    """One-sided `conf` upper confidence limit of σ_D from m pairs: σ̂·sqrt((m−1)/χ²_{1−conf, m−1})."""
    if m_pairs < 2:
        raise ValueError("need >= 2 pairs")
    return float(sigma_hat * math.sqrt((m_pairs - 1) / chi2.ppf(1 - conf, m_pairs - 1)))


def campaign_n(sigma_D: float, delta_Y: float, z: float = Z_SIZING) -> int:
    """Fresh instances per node: n = ceil((z·σ_D,UCL / δ_Y)²), z = 2.93 (revision 7)."""
    if not sigma_D > 0 or not delta_Y > 0:
        raise ValueError("sigma_D and delta_Y must be positive")
    return int(math.ceil((z * sigma_D / delta_Y) ** 2))


def plan_sizing(sz: SizingDecl, delta_Y: float, dev_ucl: float | None) -> dict:
    """σ_D,UCL = max(S0.5b UCL at the chosen W, S0.7 dev UCL); B-eligible iff n ≤ n_max."""
    ucl = max(sz.sigma_D_ucl_s05b, dev_ucl or 0.0)
    n = campaign_n(ucl, delta_Y)
    return {"sigma_D_ucl_s05b": sz.sigma_D_ucl_s05b, "sigma_D_ucl_s07_dev": dev_ucl, "sigma_D_ucl": ucl,
            "n_planned": n, "n_max": sz.n_max, "n_run_target": min(n, sz.n_max), "b_eligible": bool(n <= sz.n_max),
            "z": Z_SIZING}


def freeze_check(sizing: dict | None, s06: dict | None) -> dict:
    """S0.8 freeze: n and B-eligibility are frozen from the final sizing; S0.6 (controls simulated at its own n)
    must be re-run if either differs."""
    if not sizing or not s06 or s06.get("n") is None:
        return {"rerun_s06": True, "reason": "sizing or the S0.6 n is missing"}
    n_frozen, b_frozen = sizing["n_run_target"], sizing["b_eligible"]
    n06, b06 = int(s06["n"]), s06.get("b_eligible", b_frozen)
    diff = []
    if n06 != n_frozen:
        diff.append(f"n {n06} (S0.6) ≠ {n_frozen} (S0.8)")
    if bool(b06) != bool(b_frozen):
        diff.append(f"B-eligibility {b06} (S0.6) ≠ {b_frozen} (S0.8)")
    return {"rerun_s06": bool(diff), "reason": "; ".join(diff), "n_frozen": n_frozen, "b_eligible_frozen": b_frozen,
            "n_s06": n06}


def forks_for_usplit_power(sigma_d: float, delta_dec: float, *, power: float = 0.8, level: float = 0.95,
                           mu_null: float = 0.0, deff: float = 1.0) -> int:
    """Revision-3 helper (kept for the record): forks for P(UB(U_split) < δ_dec) = power at E[U] = mu_null."""
    gap = delta_dec - mu_null
    if not gap > 0:
        raise ValueError("delta_dec must exceed mu_null")
    return int(math.ceil(deff * ((norm.ppf(level) + norm.ppf(power)) * sigma_d / gap) ** 2))


def clopper_pearson(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    a = 1 - level
    lo = 0.0 if k == 0 else float(beta_dist.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta_dist.ppf(1 - a / 2, k + 1, n - k))
    return lo, hi


def holm_by_p(pvals: dict[str, float], alpha: float) -> dict[str, dict]:
    """Holm step-down ordered by p-value: the k-th smallest p is tested at alpha / (m − k + 1)."""
    order = sorted(pvals, key=lambda k: (pvals[k], k))
    m = len(order)
    out, stop = {}, False
    for k, name in enumerate(order):
        lvl = alpha / (m - k)
        rej = (not stop) and pvals[name] <= lvl
        stop = stop or not rej
        out[name] = {"p": pvals[name], "rank": k + 1, "alpha_level": lvl, "rejected": bool(rej)}
    return out


# ============================================================================================= per-node S3e analysis
def selection_report(dev_roots: Sequence[RootRecord], pd: Predeclaration, decl: NodeDecl | None = None) -> dict:
    """Everything decided from dev data before S3e: m*, the 4 members, π*, flip rate, matched static, σ_D,UCL, n."""
    if decl is None or decl.sigma_node is None:
        raise TrackSAnalysisError("selection needs the node's sigma_node (the grids are in σ_node units)")
    sn = decl.sigma_node
    ss = select_static(dev_roots, pd.families, sn)
    if ss["extension_needed"]:
        return {"status": "extension_needed", "m_star_provisional": ss["m_star"],
                "extension_configs": ss["extension_configs"], "_static": ss}
    sd = select_dynamic(dev_roots, pd.families, ss["m_star"], sn, pd.tuning)
    out = {"m_star": ss["m_star"], "m_star_dev_mean": ss["m_star_dev_mean"], "static_means": ss["means"],
           "static_extended": ss["extended"], "members": sd["members"], "centres": sd["centres"],
           "status": sd["status"], "n_dev_instances": len(ss["_matrix"]["instances"]), "_static": ss, "_dynamic": sd}
    if sd["status"] != "ok":
        out["missing_members"] = sd["missing"]
        return out
    out["paired_dev_instances"] = bool(not np.isnan(ss["_matrix"]["Y"]).any())
    out.update(pi_star=sd["pi_star"], pi_star_channel=sd["pi_star_channel"], pi_star_member=sd["pi_star_member"],
               pi_star_dev_mean=sd["pi_star_dev_mean"], tuning=sd["tuning"],
               flip=flip_rate(dev_roots, sd["pi_star"], ss["m_star"]),
               matched_static=matched_static(dev_roots, sd["pi_star"]), dev_sigma=dev_sigma_ucl(ss, sd))
    if decl is not None and decl.sizing is not None:
        out["sizing"] = plan_sizing(decl.sizing, decl.delta_Y, out["dev_sigma"]["ucl"])
    return out


def public(sel: dict) -> dict:
    return {k: v for k, v in sel.items() if not k.startswith("_")}


def analyze_s3e(node: str, dev_roots: Sequence[RootRecord], fresh_roots: Sequence[RootRecord], decl: NodeDecl,
                pd: Predeclaration) -> dict:
    """Select m* and π* on dev data; test D = Y(π*) − Y(m*) on fresh instances; secondaries and placebos."""
    sel = selection_report(dev_roots, pd, decl)
    if sel["status"] != "ok":
        raise TrackSAnalysisError(f"node {node}: dev selection incomplete ({sel['status']}): "
                                  f"{sel.get('missing_members') or sel.get('extension_configs')}")
    pi_star, m_star = sel["pi_star"], sel["m_star"]
    overlap = sorted({r.instance_id for r in dev_roots} & {r.instance_id for r in fresh_roots})
    if overlap:
        raise TrackSAnalysisError(f"node {node}: fresh S3e instances overlap the dev instances: {overlap[:5]}")
    fresh_pols = {policy_of(r) for r in fresh_roots}
    for want in (pi_star, m_star):
        if want not in fresh_pols:
            raise TrackSAnalysisError(f"node {node}: no fresh campaigns for the selected policy {want!r}")
    used = [r for r in list(fresh_roots) + list(dev_roots) if r.provenance is not None]
    label = combine_labels([r.provenance.label for r in used] or ["FIXTURE"])
    pr = campaign_pairs(fresh_roots, pi_star, m_star)
    test = mean_test(pr["D"], alpha=pd.alpha)
    sizing = sel.get("sizing")
    out = {"label": label, "pi_star": pi_star, "pi_star_channel": sel["pi_star_channel"], "m_star": m_star,
           "n_unpaired": pr["n_unpaired"], "n_failed": pr["n_failed"], "test": test, "delta_Y": decl.delta_Y,
           "route_single_node": campaign_route(test, decl.delta_Y),
           "worded_ge_delta_Y": bool(test["mean"] >= decl.delta_Y), "sizing": sizing,
           "underpowered_vs_plan": bool(sizing and test["n"] < sizing["n_run_target"]),
           "selection": public(sel),
           "winners_curse": winners_curse(sel["_static"], sel["_dynamic"], test["mean"],
                                          splits=pd.winners_curse_splits, seed=pd.seed),
           "placebo_exact": placebo_exact(fresh_roots, m_star),
           "placebo_descriptive": placebo_descriptive(fresh_roots, m_star, z_stop=pd.placebo_z_stop, alpha=pd.alpha)}
    ms = sel["matched_static"]["policy"]
    out["matched_static_runs"] = {"n_instances": len(per_instance_means(fresh_roots, ms)), "n_planned": test["n"]}
    if ms in fresh_pols and ms != m_star:
        a = campaign_pairs(fresh_roots, ms, m_star)
        b = campaign_pairs(fresh_roots, pi_star, ms)
        out["matched_static"] = {"policy": ms, **{k: sel["matched_static"][k] for k in ("g_eff", "h_eff")},
                                 "matched_minus_m_star": mean_test(a["D"], alpha=pd.alpha) if len(a["D"]) >= 2 else None,
                                 "pi_star_minus_matched": mean_test(b["D"], alpha=pd.alpha) if len(b["D"]) >= 2 else None}
        mm = out["matched_static"]["matched_minus_m_star"]
        out["matched_static"]["recovers_share"] = (float(mm["mean"] / test["mean"]) if mm and test["mean"] > 0
                                                   else None)
    elif ms == m_star:
        out["matched_static"] = {"policy": ms, "note": "matched static equals m*", "recovers_share": 0.0}
    else:
        out["matched_static"] = {"policy": ms, "note": "no fresh campaigns for the matched static rule"}
    return out


# ============================================================================================= decision rule
CHANNEL_WORDING = {
    "budget": "a budget-coupled threshold improves on the static price",
    "info": "an uncertainty-coupled (information) execute threshold improves on the static price",
    "keep+": "a run-coupled keep threshold (keeping more while runs are plentiful) improves on the static keep rule",
    "keep-": "a run-coupled keep threshold (keeping less while runs are plentiful) improves on the static keep rule",
}


def channel_wording(c: dict, share: float = 0.5) -> dict:
    ms = c.get("matched_static") or {}
    rec = ms.get("recovers_share")
    if rec is not None and rec >= share:
        return {"wording": f"a threshold-level shift: the matched static rule ({ms['policy']}) recovers "
                           f"{rec:.0%} ≥ {share:.0%} of π*'s point gain over m*", "threshold_level_shift": True}
    w = CHANNEL_WORDING.get(c["pi_star_channel"], c["pi_star_channel"])
    if rec is None:
        w += " (matched-static check not available; wording provisional)"
    return {"wording": w, "threshold_level_shift": False, "channel": c["pi_star_channel"]}


def decide(results: dict[str, dict], controls: dict | None, pd: Predeclaration) -> dict:
    """Revision-6 rule: A > A-small > B (per B-eligible node) > inconclusive; STOP gates first."""
    primaries = pd.primary_nodes
    for p in primaries:
        if p not in results or results[p].get("campaign") is None:
            raise TrackSAnalysisError(f"primary node {p} has no S3e campaign result")
    out: dict[str, Any] = {"primary_nodes": primaries, "fallback_active": pd.fallback_active, "level": "campaign",
                           "comparison": "tuned single-channel dynamic π* vs tuned static m*"}
    controls = controls or {}
    stops, gates = [], {}
    node_b_fail: dict[str, list[str]] = {p: [] for p in primaries}
    ctl_nodes = controls.get("nodes", {})
    for p in primaries:
        c_node = ctl_nodes.get(p)
        g_node: dict[str, Any] = {}
        gates[p] = g_node
        if not c_node:
            node_b_fail[p].append("S0.6 controls for this node missing")
            continue
        n0 = c_node.get("N0")
        if n0:
            g_node["N0_fp"] = fp_gate(int(n0["k_A"]), int(n0["R"]), alpha=pd.alpha, k_stop=pd.fp_k_stop,
                                      R_decl=pd.fp_R)
            g_node["N0_fp"]["oracle_gain"] = n0.get("oracle_gain")
            if g_node["N0_fp"]["stop"]:
                stops.append(f"{p}: N0 route-A count {n0['k_A']}/{n0['R']} ({g_node['N0_fp']['rule']})")
        else:
            node_b_fail[p].append("N0 false-positive check missing")
        g_node["resize"] = c_node.get("resize") or "missing"
        for ctl, variant in CONTROL_VARIANTS:
            v = (c_node.get(ctl) or {}).get(variant)
            if not v:
                node_b_fail[p].append(f"{ctl} {variant} power missing")
                continue
            g = power_gate(int(v["k_A"]), int(v["R"]), lb_min=pd.power_lb_min)
            g.update({k: v.get(k) for k in ("planted_gain", "n_dev", "p_correct_selection", "p_route_B")})
            g_node[f"{ctl}_{variant}_power"] = g
            if not g["ok"]:
                node_b_fail[p].append(f"{ctl} {variant} power LB {g['ci95'][0]:.2f} < {pd.power_lb_min} "
                                      "(after ≤ 1 resize)")
        sz = results[p]["campaign"].get("sizing")
        g_node["freeze"] = freeze_check(sz, c_node)
        if g_node["freeze"]["rerun_s06"]:
            node_b_fail[p].append("S0.6 must be re-run: " + g_node["freeze"]["reason"])
        nd = results[p]["campaign"]["selection"]["n_dev_instances"]
        if c_node.get("n_dev") is not None and nd != c_node["n_dev"]:
            node_b_fail[p].append(f"dev instances {nd} ≠ the S0.6 n_dev {c_node['n_dev']}")
    bpc = {}
    for n, d in pd.nodes.items():
        if d.budget_positive_control and n in results and results[n].get("fork") is not None:
            lb = results[n]["fork"]["estimates"]["delta_B"]["lb95"]
            bpc[n] = {"delta_B_lb95": lb, "pass": bool(lb > 0) if not math.isnan(lb) else False}
    gates["budget_positive_control_descriptive"] = bpc or "missing"
    for p in primaries:
        c = results[p]["campaign"]
        ex, ds = c["placebo_exact"], c["placebo_descriptive"]
        if ex["status"] == "STOP":
            stops.append(f"{p}: exact placebo D ≠ 0 at {ex['n_mismatch']} instance(s)")
        elif ex["status"] == "missing":
            node_b_fail[p].append("exact placebo missing")
        if ds["status"] == "STOP":
            stops.append(f"{p}: placebo |z| = {abs(ds['z']):.2f} > {pd.placebo_z_stop}")
        elif ds["status"] == "missing":
            node_b_fail[p].append("descriptive placebo missing")
        sz = c.get("sizing")
        if not sz or not sz["b_eligible"]:
            node_b_fail[p].append(f"not B-eligible (n {sz['n_planned'] if sz else '—'} > n_max "
                                  f"{sz['n_max'] if sz else '—'})")
        if c.get("underpowered_vs_plan"):
            node_b_fail[p].append(f"{c['test']['n']} fresh pairs < planned {sz['n_run_target']}")
        fr = c["selection"]["flip"]["flip_rate"]
        if fr is None or fr < pd.flip_min:
            node_b_fail[p].append(f"flip rate {fr if fr is None else round(fr, 3)} < {pd.flip_min}")
        if not c["selection"].get("paired_dev_instances", False):
            node_b_fail[p].append("dev configurations not run on the same paired instances")
        if not (c["test"]["ub"] < pd.nodes[p].delta_Y):
            node_b_fail[p].append(f"UB95 {c['test']['ub']:.4g} ≥ δ_Y {pd.nodes[p].delta_Y:.4g}")
    out.update(gates=gates, node_B_failures=node_b_fail)
    labels = [results[p]["campaign"]["label"] for p in primaries] + ([controls["label"]] if controls.get("label")
                                                                     else [])
    out["label"] = combine_labels(labels)
    if stops:
        out.update(route="VOID_STOP", wording=VOID_WORDING, void_reasons=stops)
        return out
    tests = {p: results[p]["campaign"]["test"] for p in primaries}
    holm = holm_by_p({p: t["p_one_sided"] for p, t in tests.items()}, pd.alpha)
    rejected = [p for p in primaries if holm[p]["rejected"]]
    out.update(holm=holm, rejected_nodes=rejected)
    if rejected:
        parts, chans = [], {}
        for p in rejected:
            c, t, dY = results[p]["campaign"], tests[p], pd.nodes[p].delta_Y
            chans[p] = channel_wording(c, pd.matched_static_share)
            size = (f"gain {t['mean']:.4g} ≥ δ_Y = {dY:.4g}" if t["mean"] >= dY else
                    f"gain {t['mean']:.4g} > 0 (point estimate below δ_Y = {dY:.4g}; not worded as ≥ δ_Y)")
            parts.append(f"{p}: {size}, LB95 {t['lb']:.4g}, UB95 {t['ub']:.4g}; π* = {c['pi_star']}; "
                         f"{chans[p]['wording']}")
        out["channels"] = chans
        if all(tests[p]["ub"] < pd.nodes[p].delta_Y for p in rejected):
            out.update(route="A-small", wording=A_SMALL_WORDING + " " + " | ".join(parts))
        else:
            out.update(route="A", wording=ROUTE_A_WORDING + " " + " | ".join(parts) + " " + ROUTE_A_DAC_CONDITION)
        return out
    per_node = {p: ("B" if not node_b_fail[p] else "inconclusive") for p in primaries}
    out["per_node"] = per_node
    eligible = [p for p in primaries if (results[p]["campaign"].get("sizing") or {}).get("b_eligible")]
    out["B_eligible_nodes"] = eligible
    b_nodes = [p for p in primaries if per_node[p] == "B"]
    if b_nodes and eligible:
        words = [f"{p}: {ROUTE_B_WORDING}" if per_node[p] == "B" else
                 f"{p}: inconclusive ({'; '.join(node_b_fail[p])}). {INCONCLUSIVE_WORDING}" for p in primaries]
        scope = f" (one-node fallback: {primaries[0]} only)" if pd.fallback_active else ""
        out.update(route="B", wording=" | ".join(words) + scope, B_nodes=b_nodes)
        return out
    out.update(route="inconclusive", wording=INCONCLUSIVE_WORDING, ub95={p: tests[p]["ub"] for p in primaries})
    return out


# ============================================================================================= report and CLI
def _fmt(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, (bool, np.bool_)):
        return str(bool(x))
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{x:.4g}"


def markdown_report(result: dict) -> str:
    d = result["decision"]
    lines = [f"# Track S analysis ({ANALYSIS_VERSION})", "",
             f"Overall label: **{d['label']}** (never EVIDENCE unless every input is). AI-assisted analysis output.",
             "", f"**Route:** {d['route']}", "", f"> {d['wording']}", ""]
    for k in ("void_reasons", "node_B_failures", "per_node"):
        if d.get(k):
            lines += [f"{k}: {d[k]}", ""]
    lines += ["## Primary: S3e, tuned dynamic π* vs tuned static m* on fresh instances (raw metric units)", "",
              "| Node | π* (channel) | m* | n | mean D | LB95 | UB95 | p (one-sided) | δ_Y | Node outcome | Holm | Label |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in result["nodes"].items():
        c = r.get("campaign")
        if not c:
            continue
        t = c["test"]
        h = d.get("holm", {}).get(name)
        hs = f"α={h['alpha_level']:.4g} {'rejected' if h['rejected'] else 'kept'}" if h else "—"
        lines.append(f"| {name} | `{c['pi_star']}` ({c['pi_star_channel']}) | `{c['m_star']}` | {t['n']} | "
                     f"{_fmt(t['mean'])} | {_fmt(t['lb'])} | {_fmt(t['ub'])} | {_fmt(t['p_one_sided'])} | "
                     f"{_fmt(c['delta_Y'])} | {c['route_single_node']} | {hs} | {c['label']} |")
    lines += ["", "### Selection, sizing, winner's curse, matched static, placebos", "",
              "| Node | flip rate | σ_D,UCL | n planned | n_max | B-eligible | dev gap | split-half optimism | "
              "matched static (share) | exact placebo | placebo z | Label |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in result["nodes"].items():
        c = r.get("campaign")
        if not c:
            continue
        sz, wc, ms = c.get("sizing") or {}, c["winners_curse"], c.get("matched_static") or {}
        lines.append(f"| {name} | {_fmt(c['selection']['flip']['flip_rate'])} | {_fmt(sz.get('sigma_D_ucl'))} | "
                     f"{_fmt(sz.get('n_planned'))} | {_fmt(sz.get('n_max'))} | {_fmt(sz.get('b_eligible'))} | "
                     f"{_fmt(wc['dev_gap_winners'])} | {_fmt(wc['split_half_optimism']['gap'])} | "
                     f"`{ms.get('policy', '—')}` ({_fmt(ms.get('recovers_share'))}) | {c['placebo_exact']['status']} | "
                     f"{_fmt(c['placebo_descriptive'].get('z'))} | {c['label']} |")
    if d.get("gates"):
        lines += ["", "### S0.6 gates (controls, per node)", "", "| Node | Gate | k / R | rate or power | 95 % CI | "
                  "Verdict |", "|---|---|---|---|---|---|"]
        for nname, gn in d["gates"].items():
            for gname, g in (gn.items() if isinstance(gn, dict) else ()):
                if not (isinstance(g, dict) and "R" in g):
                    continue
                rate = g.get("rate", g.get("power"))
                ci = g.get("rate_ci95", g.get("ci95"))
                verdict = ("STOP" if g.get("stop") else "ok") if "stop" in g else ("ok" if g["ok"] else "B unavailable")
                lines.append(f"| {nname} | {gname} | {g['k_A']}/{g['R']} | {_fmt(rate)} | [{_fmt(ci[0])}, "
                             f"{_fmt(ci[1])}] | {verdict} |")
    lines += ["", "## Secondary: fork level (descriptive; does not decide the route)", "",
              "| Node | Quantity | Estimate | 95 % CI | LB95 | UB95 | Label |", "|---|---|---|---|---|---|---|"]
    for name, r in result["nodes"].items():
        f = r.get("fork")
        if not f:
            continue
        for q in FORK_KEYS:
            e = f["estimates"][q]
            lines.append(f"| {name} | {q} | {_fmt(e['est'])} | [{_fmt(e['ci95'][0])}, {_fmt(e['ci95'][1])}] | "
                         f"{_fmt(e['lb95'])} | {_fmt(e['ub95'])} | {e['label']} |")
    lines += ["", f"Analysis script sha256: `{result['analysis_script_sha256']}`", ""]
    return "\n".join(lines)


def _load_node_dir(name: str, d: Path) -> dict:
    d = Path(d)
    out = {"leaves": load_leaves(d / "leaves.jsonl") if (d / "leaves.jsonl").exists() else [],
           "roots": load_roots(d / "roots.jsonl"), "dev": load_roots(d / "dev_roots.jsonl"),
           "fresh": load_roots(d / "campaign_roots.jsonl")}
    if not (out["leaves"] or out["roots"] or out["dev"] or out["fresh"]):
        raise TrackSAnalysisError(f"node {name}: no input files in {d}")
    check_hosts(name, out["leaves"], list(out["roots"]) + list(out["dev"]) + list(out["fresh"]))
    for kind in ("roots", "dev", "fresh"):
        for r in out[kind]:
            if r.node != name:
                raise TrackSAnalysisError(f"{kind} root {r.root_id}: node {r.node!r} != {name!r}")
    out["sha256"] = {f: file_sha256(d / f) for f in ("leaves.jsonl", "roots.jsonl", "dev_roots.jsonl",
                                                     "campaign_roots.jsonl") if (d / f).exists()}
    return out


def run_analysis(node_dirs: dict[str, Path], pd: Predeclaration, *, controls: dict | None = None,
                 check_script_hash: bool = True, policy_out: Path | None = None) -> dict:
    """Per node directory: leaves.jsonl + roots.jsonl (fork phase; secondary), dev_roots.jsonl (dev tuning: the
    3 × 3 static grid and the 4 members anchored at m*), campaign_roots.jsonl (S3e fresh-instance campaigns)."""
    script_hash = file_sha256(Path(__file__))
    if check_script_hash and pd.analysis_script_sha256 and pd.analysis_script_sha256 != script_hash:
        raise TrackSAnalysisError(f"analysis script sha256 {script_hash} != pre-declared {pd.analysis_script_sha256}")
    results, inputs, policies = {}, {}, {}
    for name, d in node_dirs.items():
        if name not in pd.nodes:
            raise TrackSAnalysisError(f"node {name} not in the pre-declaration")
        decl = pd.nodes[name]
        data = _load_node_dir(name, d)
        inputs[name] = data["sha256"]
        res: dict[str, Any] = {"role": decl.role, "fork": None, "campaign": None}
        if data["leaves"]:
            ft = build_fork_table(name, data["leaves"], data["roots"])
            res["fork"] = analyze_forks(ft, decl, pd)
            if policy_out is not None:
                policy_out.mkdir(parents=True, exist_ok=True)
                for kind, pol in fit_policies(ft, pd).items():
                    policies[f"{name}/{kind}"] = write_policy(pol, policy_out / f"{name}.{kind}.json")
        if data["dev"] and data["fresh"]:
            res["campaign"] = analyze_s3e(name, data["dev"], data["fresh"], decl, pd)
        labs = [x["label"] for x in (res["fork"], res["campaign"]) if x]
        res["label"] = combine_labels(labs) if labs else "FIXTURE"
        results[name] = res
    return {"analysis_version": ANALYSIS_VERSION, "analysis_script_sha256": script_hash, "inputs": inputs,
            "policies_sha256": policies, "nodes": results, "controls_input": controls,
            "decision": decide(results, controls, pd)}


def _json_default(o):
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, set):
        return sorted(o)
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select", help="dev selection: m* from the static grid; then the 4 members; then π*")
    s.add_argument("--predeclaration", type=Path, required=True)
    s.add_argument("--node", required=True, metavar="NAME=DIR")
    s.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("analyze", help="full analysis and decision")
    a.add_argument("--predeclaration", type=Path, required=True)
    a.add_argument("--node", action="append", default=[], metavar="NAME=DIR")
    a.add_argument("--controls", type=Path, default=None, help="S0.6 controls summary JSON (tracks_controls/v2, per node)")
    a.add_argument("--out-json", type=Path, required=True)
    a.add_argument("--out-md", type=Path, required=True)
    a.add_argument("--policy-out", type=Path, default=None, help="write the secondary π′ and m̃ JSON here")
    a.add_argument("--bootstrap-B", type=int, default=None, help="override (engineering runs only; recorded)")
    args = ap.parse_args(argv)
    pd = parse_predeclaration(json.loads(args.predeclaration.read_text()))
    try:
        if args.cmd == "select":
            name, d = args.node.split("=", 1)
            if name not in pd.nodes:
                raise TrackSAnalysisError(f"node {name} not in the pre-declaration")
            data = _load_node_dir(name, Path(d))
            sel = public(selection_report(data["dev"], pd, pd.nodes[name]))
            sel.update(node=name, dev_roots_sha256=data["sha256"].get("dev_roots.jsonl"),
                       label=combine_labels([r.provenance.label for r in data["dev"] if r.provenance] or ["FIXTURE"]),
                       predeclaration_sha256=file_sha256(args.predeclaration))
            args.out.write_text(json.dumps(sel, indent=2, default=_json_default))
            print(f"status={sel['status']} m_star={sel['m_star']} pi_star={sel.get('pi_star')}")
            return 0
        if args.bootstrap_B is not None:
            pd.bootstrap_B = args.bootstrap_B
        dirs = dict(spec.split("=", 1) for spec in args.node)
        controls = json.loads(args.controls.read_text()) if args.controls else None
        result = run_analysis({k: Path(v) for k, v in dirs.items()}, pd, controls=controls,
                              policy_out=args.policy_out)
    except TrackSAnalysisError as exc:
        ap.exit(2, f"Track S analysis refused: {exc}\n")
    result["predeclaration_sha256"] = file_sha256(args.predeclaration)
    result["bootstrap_B_override"] = args.bootstrap_B
    args.out_json.write_text(json.dumps(result, indent=2, default=_json_default, ensure_ascii=False))
    args.out_md.write_text(markdown_report(result))
    print(f"route={result['decision']['route']} label={result['decision']['label']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# =============================================================================================
# IMPLEMENTATION NOTES (the content intended for r1/tracks/ANALYSIS_NOTES.md; AI-assisted, 29 Oct 2026)
#
# Spec: runbook rev. 3 + amendments rev. 4, 5, 6, 6.1 (later wins). Choices needing the author's confirmation:
#  1. Members anchored at m*: each of budget / info / keep+ / keep− is m* plus one channel, so tuning is
#     two-stage (statics incl. the one g-edge extension, then members; `select` CLI reports the next stage).
#  2. Overall B with mixed nodes: overall B if >= 1 B-eligible node meets every B condition and there is no Holm
#     rejection; each node is worded separately ("B on X; inconclusive on Y").
#  3. FPR STOP: the declared count (>= 18 of 200) is used; P(X >= 18 | 200, 0.05) = 0.0121, so "p < 0.01" would
#     need >= 19. The exact p is reported; p < 0.01 is used only when R != 200.
#  4. z = 2.90 as declared (z.95 + z.90 = 2.93; z.95 + z.80 = 2.49).
#  5. The inconclusive sentence is the exact runbook §0 text, which still says δ_dec although the margin is δ_Y.
#  6. τ_pred is not in STATE_FEATURES; it is read from the decision record (`tau_pred`).
#  7. The real-node budget positive control (Δ_B > 0) is no longer a rev-6 B condition: reported descriptively.
#  8. Flip rate: π*'s eligible dev decisions where m* would act differently; overall (gate) and E1 / E2.
#  9. Matched static = mean effective thresholds of π* over its eligible dev decisions; "threshold-level shift"
#     wording if (matched − m*) >= 0.5 (π* − m*) on point estimates; CIs reported.
# 10. Grids are in σ_node units (g ∈ {0.05, 0.1, 0.2, 0.4}, h ∈ {−0.25, 0, 0.25}; b_budget 0.3, h_budget 0.6;
#     b_info 0.3 dimensionless) and converted with the declared sigma_node.
# 11. Fork level (secondary): ridge with epoch interactions, per-epoch weighted standardisation, unpenalised
#     intercepts, normalised objective; 5 instance-level folds; m~ thresholds tuned nested; bootstrap copies of a
#     cluster share a fold. U_split is unbiased for the gain of the rep-1 chooser (<= 0 under the null, not 0).
# Proposed schema additions: RootRecord.policy, rep, llm_seed_base; decisions[*] with epoch, action,
#   index_value, eligible, budget_fraction, tau_pred; E2 state measured after the fork trial's run;
#   provenance.phase values "dev_tuning" and "campaign".
# =============================================================================================
