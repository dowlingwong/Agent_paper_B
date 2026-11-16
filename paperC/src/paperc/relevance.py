"""Decision-relevance check on ``spt_transition/v1`` records (build runbook P5; BUILD_LIST B10; plan addendum §B.3).
Revised after review rounds 1 and 2.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

Paper B's Track S stopped at STOP 4 because no E1 decision was near its threshold: V* - g lay 2.6-4.1 sigma above
the price everywhere, so every eligible proposal was executed and every E1 skip was a rule duplicate (E2, by
contrast, had 11-15 % of its margins within 0.5 sigma). Before any sequential-policy collection, this module
measures, per node, how many logged decisions are close enough to their threshold for a different policy to change
them.

**Rows counted.** Only epochs E1 and E2. Excluded and counted separately: rule-forced rows (E1 rule skips are the
rule-skip share; the first trial's forced execute and keep are excluded), forced rows (fork arms and interventions:
not decisions of the logged policy), and E2 rows whose candidate is invalid or divergent (the schema forces their
discard). Fork continuations (non-empty ``branch_path``) are a designed sample that over-represents states near the
threshold: by default (``forks="root"``) only root trajectories are counted, which estimates the share among the logged
policy's own states. ``forks="weighted"`` adds single-level continuation rows (``len(branch_path) == 1``; deeper forks
are refused) with weight 1 / ``fork.p_select`` (0 < p_select <= 1). Its estimand is **not** the logged policy's share:
it is a ratio of Horvitz-Thompson totals over the root states plus the continuation states that every root step
would generate if it were forked (arms x replicates x continuation policies per fork), so continuation states
dominate it. Row counts (eligible rows, E1 rows, rule skips, policy skips and executes) are unweighted in either
mode; only shares and quantiles are weighted.

**Statistics** (distances in ``state.sigma_node``):

* E1: |V* - g| <= b sigma for the declared bands b (default 0.25, 0.5, 1.0), for every declared threshold (the run
  price, and e.g. a static rule's threshold); the distribution of (V* - g) / sigma; the eligible rows' policy skips
  and executes;
* E2: the keep margin |stat - h| <= b sigma, where stat is the belief's m_hat (default) or the raw observed increment
  (``e2_stat="delta_hat"``, the margin of Paper B's default keep), and h is the keep threshold (a number or a mapping
  node -> number; default 0; a mapping must cover every node with eligible E2 rows);
* the rule-skip share (rule-forced E1 skips over counted E1 rows) and its breakdown by rule;
* every share carries a 95 % interval clustered by ``cluster`` (default ``identity.instance_id``, the schema's cluster:
  policies run on the same instance seeds are correlated; ``cluster="campaign_id"`` is the alternative). The interval
  is a Wilson score interval with a design-effect effective sample size n_eff = p (1 - p) / se^2 (se: linearised
  CR1 cluster-robust standard error of the weighted ratio; n_eff capped at the row count) and a t quantile with k - 1
  degrees of freedom (k clusters). At a share of 0 or 1 the standard error carries no design-effect information and
  n_eff is set to k (one observation per cluster, conservative). With fewer than 2 clusters there is no interval.

**Verdict per epoch and threshold:** "not assessed" when there is no eligible row; **"no decision-relevant states"**
when no eligible row lies within the widest band; else the share within the widest band. The share that would gate
SPT-2 is **not** set here: it is a proposal for the author (runbook P5).

**Inputs per row** (dicts as written by ``schema.to_dict``, or ``Transition`` objects): ``identity.node``,
``identity.epoch``, ``identity.campaign_id``, ``identity.branch_path``, ``state.rule_forced``,
``state.sigma_node``, ``state.candidate_invalid``, ``state.candidate_divergent``, ``state.candidate_delta_hat``,
``state.forecasts[<belief>]`` (``v_star`` on eligible E1 rows; ``m_hat`` on eligible E2 rows), ``action.action``,
``action.rule``, ``action.forced``, ``fork.p_select`` (weighted mode), and optionally ``env.W``, ``policy.policy``.
**What the B5 loader must provide** for real Paper B / Track S records: these fields, with the common belief's
forecast (the C3 belief on real nodes, A2-U on Track S) on every eligible row and invalid / divergent candidates
flagged. The belief is chosen with ``belief=``; when omitted, the rows must carry exactly one non-privileged belief.

**Thresholds.** ``g`` (the run price) is a number, or a mapping node -> number; when a node is missing from the
mapping or no value is given, the forecast's ``g`` field, then ``env.constants["g"]``. Extra thresholds
(``thresholds={"static": ...}``) need an explicit value for every node with eligible E1 rows: only ``g`` falls back.
Passing ``g=`` together with a ``thresholds`` mapping that already contains ``g`` is an error. The source of every
threshold value and of h is reported.
``validate=True`` (the default) first runs ``schema.check_campaign`` and refuses invalid input; values that are not
finite are refused in any case.

CLI: ``python -m paperc.relevance rows.jsonl [...] --out report.md [--json out.json] [--g 0.001 | --g-json p.json]
[--threshold static=0.002 ...] [--h 0 | --h-json h.json] [--e2-stat m_hat|delta_hat] [--forks root|weighted]
[--cluster instance_id|campaign_id] [--belief a2u] [--bands 0.25,0.5,1.0] [--no-validate]``. Input errors exit with
code 2 and a message; nothing is written unless both outputs could be built.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
from scipy import stats as _stats

from paperc import schema as S

BANDS = (0.25, 0.5, 1.0)
QUANTILES = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)
PRIVILEGED_PREFIX = "privileged:"
CLUSTERS = ("instance_id", "campaign_id")


class RelevanceInputError(ValueError):
    pass


def _row(r) -> dict:
    return S.to_dict(r) if isinstance(r, S.Transition) else r


def _where(r) -> str:
    try:
        return f"{r['identity'].get('campaign_id')}#{r['identity'].get('step_index')}"
    except Exception:                                    # noqa: BLE001 - only for messages
        return "<unidentified row>"


def _finite(x, what, r=None):
    if x is None or not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(float(x)):
        where = _where(r) if isinstance(r, dict) else (r or "input")
        raise RelevanceInputError(f"{where}: {what} is {x!r} (need a finite number)")
    return float(x)


def _wquantile(z: np.ndarray, w: np.ndarray, q: float) -> float:
    o = np.argsort(z)
    z, w = z[o], w[o]
    c = np.cumsum(w) / w.sum()
    return float(z[min(np.searchsorted(c, q - 1e-12), len(z) - 1)])


def wilson_cluster(p: float, se: float, n: int, k: int) -> tuple[float, float] | None:
    """95 % Wilson score interval with effective sample size p (1 - p) / se^2 (capped at n; k at p in {0, 1}) and a
    t quantile with k - 1 degrees of freedom; None with fewer than 2 clusters."""
    if k < 2:
        return None
    t = float(_stats.t.ppf(0.975, k - 1))
    n_eff = min(float(n), p * (1 - p) / se ** 2) if 0 < p < 1 and se > 0 else float(k)
    den = 1 + t * t / n_eff
    centre = (p + t * t / (2 * n_eff)) / den
    half = t / den * math.sqrt(p * (1 - p) / n_eff + t * t / (4 * n_eff * n_eff))
    return max(0.0, centre - half), min(1.0, centre + half)


def _pct(iv) -> str:
    return "[—]" if iv is None else f"[{iv[0]:.1%}, {iv[1]:.1%}]"


@dataclass
class EpochSummary:
    n_eligible: int = 0
    weight: float = 0.0
    clusters: int = 0
    shares: dict = field(default_factory=dict)        # band -> weighted share (None when not assessed)
    counts: dict = field(default_factory=dict)        # band -> unweighted row count
    se: dict = field(default_factory=dict)            # band -> cluster-robust standard error
    intervals: dict = field(default_factory=dict)     # band -> (lo, hi) or None
    quantiles: dict = field(default_factory=dict)
    widest: float = 1.0

    @property
    def assessed(self) -> bool:
        return self.n_eligible > 0

    @property
    def status(self) -> str:
        if not self.assessed:
            return "not assessed (no eligible rows)"
        if self.counts[self.widest] == 0:
            iv = self.intervals[self.widest]
            return (f"no decision-relevant states (0 of {self.n_eligible} eligible rows within {self.widest} sigma; "
                    f"95 % upper bound {'— (fewer than 2 clusters)' if iv is None else f'{iv[1]:.1%}'})")
        return (f"{self.shares[self.widest]:.1%} {_pct(self.intervals[self.widest])} of {self.n_eligible} eligible "
                f"rows within {self.widest} sigma")

    def to_dict(self) -> dict:
        a = self.assessed
        return {"n_eligible": self.n_eligible, "weight": self.weight, "clusters": self.clusters,
                "shares": {str(k): (v if a else None) for k, v in self.shares.items()},
                "counts": {str(k): v for k, v in self.counts.items()},
                "se": {str(k): (v if a else None) for k, v in self.se.items()},
                "intervals": {str(k): (list(v) if a and v is not None else None) for k, v in self.intervals.items()},
                "quantiles": {str(k): v for k, v in self.quantiles.items()},
                "any_within_widest_band": a and self.counts[self.widest] > 0,
                "status": self.status}


def _summarise(z, w, cl, bands) -> EpochSummary:
    z, w = np.asarray(z, float), np.asarray(w, float)
    s = EpochSummary(n_eligible=len(z), weight=float(w.sum()), clusters=len(set(cl)), widest=max(bands))
    for b in bands:
        inside = (np.abs(z) <= b).astype(float) if len(z) else np.zeros(0)
        s.counts[b] = int(inside.sum())
        if len(z):
            p = float((w * inside).sum() / w.sum())
            # linearised CR1 cluster-robust standard error of a weighted ratio estimator
            res = defaultdict(float)
            for c, wi, ii in zip(cl, w, inside):
                res[c] += wi * (ii - p)
            k = len(res)
            se = math.sqrt(sum(v * v for v in res.values()) * (k / (k - 1) if k > 1 else 1.0)) / w.sum()
            s.shares[b], s.se[b], s.intervals[b] = p, se, wilson_cluster(p, se, len(z), k)
        else:
            s.shares[b], s.se[b], s.intervals[b] = None, None, None
    if len(z):
        s.quantiles = {q: _wquantile(z, w, q) for q in QUANTILES}
    return s


@dataclass
class NodeSummary:
    node: str
    belief: str
    e1: dict                      # threshold label -> EpochSummary
    e2: EpochSummary
    price: dict                   # threshold label -> value, "varies" or None
    price_source: dict            # threshold label -> Counter of sources
    h: float | None               # None when an h mapping lacks the node (allowed only without eligible E2 rows)
    h_source: str                 # "argument", "mapping", "default" or "missing"
    e2_stat: str
    n_e1_rows: int
    rule_skips: dict
    policy_skips: int
    policy_executes: int
    n_forced_rows: int
    n_fork_rows_excluded: int
    n_invalid_discards: int
    campaigns: int
    policies: list
    W: list
    cluster: str = "instance_id"
    forks: str = "root"

    @property
    def rule_skip_share(self) -> float | None:
        return sum(self.rule_skips.values()) / self.n_e1_rows if self.n_e1_rows else None

    def verdict(self) -> list[str]:
        out = [f"E1 vs {lab}: {ep.status}" for lab, ep in self.e1.items()]
        out.append(f"E2 ({self.e2_stat} - h): {self.e2.status}")
        return out

    def to_dict(self) -> dict:
        return {"node": self.node, "belief": self.belief, "E1": {k: v.to_dict() for k, v in self.e1.items()},
                "E2": self.e2.to_dict(), "price": self.price,
                "price_source": {k: dict(v) for k, v in self.price_source.items()}, "h": self.h,
                "h_source": self.h_source, "e2_stat": self.e2_stat, "cluster": self.cluster, "forks": self.forks, "n_e1_rows": self.n_e1_rows, "rule_skip_share": self.rule_skip_share,
                "rule_skips": self.rule_skips, "policy_skips": self.policy_skips,
                "policy_executes": self.policy_executes, "n_forced_rows": self.n_forced_rows,
                "n_fork_rows_excluded": self.n_fork_rows_excluded, "n_invalid_discards": self.n_invalid_discards,
                "campaigns": self.campaigns, "policies": self.policies, "W": self.W, "verdict": self.verdict()}


def _beliefs(rows) -> set:
    names = set()
    for r in rows:
        names |= {k for k in ((r.get("state") or {}).get("forecasts") or {}) if not k.startswith(PRIVILEGED_PREFIX)}
    return names


def relevance(rows: Iterable, *, g: float | Mapping[str, float] | None = None,
              thresholds: Mapping[str, float | Mapping[str, float] | None] | None = None,
              h: float | Mapping[str, float] | None = None, belief: str | None = None, bands=BANDS,
              e2_stat: str = "m_hat", forks: str = "root", cluster: str = "instance_id",
              validate: bool = True) -> dict[str, NodeSummary]:
    rows = [_row(r) for r in rows]
    if not rows:
        raise RelevanceInputError("no rows")
    bands = tuple(sorted(float(b) for b in bands))
    if not bands or bands[0] <= 0:
        raise RelevanceInputError(f"bands must be positive numbers, got {bands}")
    if e2_stat not in ("m_hat", "delta_hat"):
        raise RelevanceInputError(f"e2_stat must be 'm_hat' or 'delta_hat', got {e2_stat!r}")
    if forks not in ("root", "weighted"):
        raise RelevanceInputError(f"forks must be 'root' or 'weighted', got {forks!r}")
    if cluster not in CLUSTERS:
        raise RelevanceInputError(f"cluster must be one of {CLUSTERS}, got {cluster!r}")
    if isinstance(h, Mapping):
        for k_, v_ in h.items():
            _finite(v_, f"h for node {k_!r}")
    elif h is not None:
        _finite(h, "h")
    if validate:
        v = S.check_campaign(rows)
        if v:
            raise RelevanceInputError(f"{len(v)} schema violations, first: {v[0]}")
    if belief is None:
        names = _beliefs(rows)
        if len(names) != 1:
            raise RelevanceInputError(f"rows carry beliefs {sorted(names)}: choose one with belief=")
        belief = names.pop()
    if thresholds is None:
        thr = {"g": g}
    else:
        thr = dict(thresholds)
        if g is not None:
            if "g" in thr:
                raise RelevanceInputError("g given both as g= and in thresholds=: give it once")
            thr = {"g": g, **thr}
    if not thr or any(not isinstance(lab, str) or not lab for lab in thr):
        raise RelevanceInputError(f"threshold labels must be non-empty strings, got {list(thr)}")
    by_node: dict[str, list] = defaultdict(list)
    for r in rows:
        try:
            by_node[r["identity"]["node"]].append(r)
        except (KeyError, TypeError, AttributeError) as e:
            raise RelevanceInputError(f"{_where(r)}: malformed row ({e!r})") from None
    out = {}
    for node, rs in sorted(by_node.items()):
        if isinstance(h, Mapping):
            hv, h_src = (float(h[node]), "mapping") if node in h else (None, "missing")
        else:
            hv, h_src = (0.0, "default") if h is None else (float(h), "argument")
        e1z = {lab: ([], [], []) for lab in thr}
        e2z = ([], [], [])
        prices = {lab: set() for lab in thr}
        sources = {lab: Counter() for lab in thr}
        skips, n_e1 = Counter(), 0
        pol_skip = pol_exec = n_forced = n_fork_excl = n_invalid = 0
        camps, pols, Ws = set(), set(), set()
        for r in rs:
            try:
                idn, st, act = r["identity"], r["state"], r["action"]
                ep = idn["epoch"]
                if ep not in ("E1", "E2"):
                    continue
                weight = 1.0
                bp = idn.get("branch_path")
                if bp:
                    if forks == "root":
                        n_fork_excl += 1
                        continue
                    if len(bp) > 1:
                        raise RelevanceInputError(f"{_where(r)}: weighted mode handles single-level forks only "
                                                  f"(branch_path {bp}); a nested fork's weight needs the product of "
                                                  f"p_select along its path")
                    ps = _finite((r.get("fork") or {}).get("p_select"), "fork.p_select", r)
                    if not 0 < ps <= 1:
                        raise RelevanceInputError(f"{_where(r)}: fork.p_select {ps} outside (0, 1]")
                    weight = 1.0 / ps
                camps.add(idn.get("campaign_id"))
                pols.add((r.get("policy") or {}).get("policy"))
                Ws.add((r.get("env") or {}).get("W"))
                if act.get("forced"):
                    n_forced += 1
                    continue
                if ep == "E1":
                    n_e1 += 1
                if st["rule_forced"]:
                    if ep == "E1" and act["action"] == "skip":
                        skips[act["rule"]] += 1
                    continue
                cl = idn.get(cluster)
                if cl is None:
                    raise RelevanceInputError(f"{_where(r)}: identity.{cluster} missing (cluster key)")
                if ep == "E2" and (st.get("candidate_invalid") or st.get("candidate_divergent")):
                    n_invalid += 1
                    continue
                sig = _finite(st.get("sigma_node"), "state.sigma_node", r)
                if sig <= 0:
                    raise RelevanceInputError(f"{_where(r)}: sigma_node must be positive")
                f = (st.get("forecasts") or {}).get(belief) or {}
                if ep == "E1":
                    v = _finite(f.get("v_star"), f"forecasts[{belief}].v_star", r)
                    pol_skip += act["action"] == "skip"
                    pol_exec += act["action"] == "execute"
                    for lab, spec in thr.items():
                        p, src = (spec.get(node), "mapping") if isinstance(spec, Mapping) else (spec, "argument")
                        if p is None and lab == "g":
                            p, src = f.get("g"), "forecast"
                            if p is None:
                                p, src = ((r.get("env") or {}).get("constants") or {}).get("g"), "env"
                        if p is None:
                            raise RelevanceInputError(
                                f"{_where(r)}: no value for threshold '{lab}' on node {node!r}" +
                                (" (argument, mapping, forecast g or env constant)" if lab == "g" else
                                 " (extra thresholds need an explicit value per node; only g falls back)"))
                        p = _finite(p, f"threshold '{lab}'", r)
                        prices[lab].add(p)
                        sources[lab][src] += 1
                        e1z[lab][0].append((v - p) / sig)
                        e1z[lab][1].append(weight)
                        e1z[lab][2].append(cl)
                else:
                    if hv is None:
                        raise RelevanceInputError(f"{_where(r)}: the h mapping has no value for node {node!r}, "
                                                  f"which has eligible E2 rows")
                    stat = f.get("m_hat") if e2_stat == "m_hat" else st.get("candidate_delta_hat")
                    stat = _finite(stat, f"E2 statistic {e2_stat}", r)
                    e2z[0].append((stat - hv) / sig)
                    e2z[1].append(weight)
                    e2z[2].append(cl)
            except (KeyError, TypeError, AttributeError) as e:
                raise RelevanceInputError(f"{_where(r)}: malformed row ({e!r})") from None
        out[node] = NodeSummary(
            node=node, belief=belief, e1={lab: _summarise(*e1z[lab], bands) for lab in thr},
            e2=_summarise(*e2z, bands),
            price={lab: (next(iter(ps)) if len(ps) == 1 else (None if not ps else "varies")) for lab, ps in prices.items()},
            price_source=sources, h=hv, h_source=h_src, e2_stat=e2_stat, n_e1_rows=n_e1, rule_skips=dict(skips),
            policy_skips=pol_skip, policy_executes=pol_exec, n_forced_rows=n_forced,
            n_fork_rows_excluded=n_fork_excl, n_invalid_discards=n_invalid, campaigns=len(camps),
            policies=sorted(p for p in pols if p is not None), W=sorted(w for w in Ws if w is not None),
            cluster=cluster, forks=forks)
    return out


def markdown(summary: dict[str, NodeSummary], *, title: str | None = None, inputs: list | None = None,
             validated: bool | None = None) -> str:
    any_node = next(iter(summary.values()))
    bands = tuple(sorted(any_node.e2.counts)) or BANDS
    forks, cluster = any_node.forks, any_node.cluster
    fork_text = ("root trajectories only (the logged policy's own states)" if forks == "root" else
                 "weighted by 1 / p_select (estimand: root states plus the continuation states every root step would "
                 "generate if forked, not the logged policy's share)")
    lines = [f"# {title or 'Decision-relevance check'}", "",
             "ENGINEERING_ONLY. Generated by `paperc.relevance` (build runbook P5). Distances in sigma_node. Shares are "
             "weighted (weights differ from 1 only for weighted fork continuations); counts in parentheses are rows. "
             f"95 % intervals are clustered by `{cluster}`: Wilson score intervals with a design-effect effective "
             "sample size and a t quantile with k − 1 degrees of freedom; at a share of 0 or 1 the effective sample "
             "size is the number of clusters; no interval (—) with fewer than 2 clusters. Verdict per epoch and "
             "threshold: *not assessed* without eligible rows; *no decision-relevant states* when no eligible row lies "
             f"within the widest band ({max(bands)} sigma); else the share within it. Fork continuations: {fork_text}. "
             "Rule and policy skip columns are unweighted row counts. The share that would gate SPT-2 is not set "
             "here.", ""]
    if inputs is not None:
        lines += ["**Inputs**" + (f" (schema validation: {'on' if validated else 'off'})" if validated is not None
                                  else "") + ":", ""]
        lines += [f"- `{i['path']}`: {i['rows']} rows, sha256 `{i['sha256'][:16]}`" for i in inputs] + [""]
    head = "| Node | Decision | Eligible rows (clusters) | " + " | ".join(f"within {b} σ" for b in bands) + \
        " | min | 5 % | median | 95 % | max |"
    lines += [head, "|" + "---|" * (head.count("|") - 1)]
    for node, s in summary.items():
        eps = [(f"E1: V\\* − {lab}", ep) for lab, ep in s.e1.items()] + [(f"E2: {s.e2_stat} − h", s.e2)]
        for name, ep in eps:
            qs = [ep.quantiles.get(q) for q in (0.0, 0.05, 0.5, 0.95, 1.0)]
            qtxt = " | ".join("—" if q is None else f"{q:+.2f}" for q in qs)
            if ep.assessed:
                share = " | ".join(f"{ep.shares[b]:.1%} {_pct(ep.intervals[b])} ({ep.counts[b]})" for b in bands)
            else:
                share = " | ".join("—" for _ in bands)
            lines.append(f"| {node} | {name} | {ep.n_eligible} ({ep.clusters}) | {share} | {qtxt} |")
    lines += ["", "| Node | Belief | Campaigns | Policies | W | Thresholds (source) | h (source) | E1 rows | Rule skips | "
                  "Policy skips / executes | Excluded | Verdict |", "|" + "---|" * 12]
    for node, s in summary.items():
        thr = "; ".join(f"{lab} = {s.price[lab]} ({', '.join(f'{k}: {v}' for k, v in s.price_source[lab].items())})"
                        for lab in s.e1)
        rs = "—" if s.rule_skip_share is None else \
            f"{s.rule_skip_share:.1%} ({', '.join(f'{k}: {v}' for k, v in sorted(s.rule_skips.items())) or 'none'})"
        pol = ", ".join(s.policies[:3]) + (f" (+{len(s.policies) - 3})" if len(s.policies) > 3 else "")
        exc = (f"forced {s.n_forced_rows}, fork rows {s.n_fork_rows_excluded}, invalid/divergent E2 "
               f"{s.n_invalid_discards}")
        htxt = "—" if s.h is None else f"{s.h:g}"
        lines.append(f"| {node} | {s.belief} | {s.campaigns} | `{pol}` | {', '.join(map(str, s.W)) or '—'} | {thr} | "
                     f"{htxt} ({s.h_source}) | {s.n_e1_rows} | {rs} | {s.policy_skips} / {s.policy_executes} | {exc} | "
                     f"{'; '.join(s.verdict())} |")
    return "\n".join(lines) + "\n"


def _read(paths) -> tuple[list[dict], list[dict]]:
    rows, inputs = [], []
    for p in paths:
        data = Path(p).read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as e:
            raise RelevanceInputError(f"{p}: not UTF-8 text ({e.reason} at byte {e.start})") from None
        n = 0
        for ln, line in enumerate(text.splitlines(), 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise RelevanceInputError(f"{p}:{ln}: not JSON ({e.msg})") from None
                n += 1
        inputs.append({"path": str(p), "rows": n, "sha256": hashlib.sha256(data).hexdigest()})
    return rows, inputs


def _kv(text: str) -> tuple[str, float]:
    lab, _, val = text.partition("=")
    if not lab or not val:
        raise argparse.ArgumentTypeError(f"expected LABEL=VALUE, got {text!r}")
    if lab == "g":
        raise argparse.ArgumentTypeError("the price g is given with --g or --g-json, not --threshold")
    try:
        v = float(val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r}: value is not a number") from None
    if not math.isfinite(v):
        raise argparse.ArgumentTypeError(f"{text!r}: value must be finite")
    return lab, v


def _json_file(path: str, what: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        raise RelevanceInputError(f"{what} {path}: {e}") from None


def _bands(text: str) -> tuple:
    try:
        b = tuple(float(x) for x in text.split(",") if x.strip())
    except ValueError:
        raise argparse.ArgumentTypeError(f"bands must be comma-separated numbers, got {text!r}") from None
    if not b or min(b) <= 0:
        raise argparse.ArgumentTypeError(f"bands must be positive, got {text!r}")
    return b


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Decision-relevance check on spt_transition/v1 records (P5).")
    ap.add_argument("rows", nargs="+", help="JSONL files of spt_transition/v1 rows")
    ap.add_argument("--out", required=True, help="markdown report to write (directories are created)")
    ap.add_argument("--json", help="also write the summary as JSON")
    gp = ap.add_mutually_exclusive_group()
    gp.add_argument("--g", type=float, help="run price g (raw units) for every node")
    gp.add_argument("--g-json", help="JSON file mapping node -> price g")
    ap.add_argument("--threshold", type=_kv, action="append", default=[],
                    help="extra E1 threshold LABEL=VALUE (repeatable), reported next to g")
    hp = ap.add_mutually_exclusive_group()
    hp.add_argument("--h", type=float, help="E2 keep threshold for the margin (default 0)")
    hp.add_argument("--h-json", help="JSON file mapping node -> keep threshold h")
    ap.add_argument("--e2-stat", choices=("m_hat", "delta_hat"), default="m_hat")
    ap.add_argument("--forks", choices=("root", "weighted"), default="root")
    ap.add_argument("--cluster", choices=CLUSTERS, default="instance_id")
    ap.add_argument("--belief")
    ap.add_argument("--bands", type=_bands, default=BANDS)
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--title")
    a = ap.parse_args(argv)
    try:
        rows, inputs = _read(a.rows)
        g = _json_file(a.g_json, "--g-json") if a.g_json else a.g
        h = _json_file(a.h_json, "--h-json") if a.h_json else a.h
        thr = {"g": g, **dict(a.threshold)}
        summ = relevance(rows, thresholds=thr, h=h, belief=a.belief, bands=a.bands, e2_stat=a.e2_stat,
                         forks=a.forks, cluster=a.cluster, validate=not a.no_validate)
        md = markdown(summ, title=a.title, inputs=inputs, validated=not a.no_validate)
        js = None
        if a.json:
            js = json.dumps({"inputs": inputs, "validated": not a.no_validate, "forks": a.forks, "cluster": a.cluster,
                             "nodes": {k: v.to_dict() for k, v in summ.items()}}, indent=1, allow_nan=False) + "\n"
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        if js is not None:
            Path(a.json).parent.mkdir(parents=True, exist_ok=True)
            Path(a.json).write_text(js)
    except (ValueError, OSError, AttributeError) as e:   # RelevanceInputError, JSON / Unicode errors, I/O
        print(f"relevance: {e}", file=sys.stderr)
        return 2
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
