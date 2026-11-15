"""Headroom census on existing logs (build runbook PH; BUILD_LIST B16; R1-PAPERC-CENSUS-FIRST). ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 16 Nov 2026; revised after review round 1).

Read-only. Every input is read from a pinned commit with ``git cat-file`` (nothing is copied into ``paperC/``), so the
census is reproducible from the clone alone. ``run`` records the git object id of each file or directory it read.

Sources:

* **Track S** (``trackS-ops-20261030`` @ ``fab88fc``; ``digits_mlp``, ``tabular_mlp``): S0.5 roots (A2-U, rep 0),
  S0.5b truncations, S0.4 rows (campaign increment ``delta_hat`` and 5-seed fresh audit ``delta_audit`` per executed
  proposal) and S0.4 roots; all S0.4 + S0.5 roots for the trial-1 drop; S1.1 factorials (also ``openml_breast_w``).
  S0.4 kept iff delta_hat > 0 (``ExecuteNonRuleController``, prior None); S0.5 kept iff A2-U's m_hat > 0.
  Hosts: digits S0.4 on TASL-2, all other Track S runs on TASL-7.
* **Paper B sweep 1** (``codex/coordinator-20261031`` @ ``10742f8``): C3 label sweep, 7B proposer, 8 CPU nodes x 18
  instances x 20 runs, memory ``none`` and ``append_only_summary`` (reported per mode). Increments are fixed-seed
  ``delta_vs_best`` at the node default seed; no fresh audits exist (Paper B's B.2 has not run).
* **C1 noise floor**: the D28 composite (``results/r1/noise/D28_REPAIR_20261027/summary.json`` @ ``10742f8``, the file
  the sweep cites for sigma_d). Per edit: ``sd_joint`` (sd over 30 joint seeds of the *paired* difference
  m(c_k, s) - m(c0, s); ``r1/noise/e1_report.py``), ``rho_joint`` (seed correlation of the two configurations),
  ``flip_emp`` (single-seed sign-flip rate), ``campaign_wrong``, ``decision_regret``; per node ``sigma_joint`` (the
  start configuration's own seed sd). The sweep's **sigma_d is itself a paired unit**: it equals the median
  ``sd_joint`` over the node's *material* edits (asserted by a test). The census also reports the median over *all*
  edits as a bracket (the "paired" columns) and the per-edit range, because the noise depends strongly on the edit.
  Track S's sigma_node is the median over all five edits.
* **C3 audit pilot** (``results/r1/engineering/c3_audit_pilot_20261019T001338Z`` @ ``10742f8``): LLM proposals
  audited on 6 fresh seeds; random-selection rows give false / missed keep counts. Older harness, tiny sample.
* **E1b pilots** (``results/r1/pilot/E1b_*/analysis.json`` @ ``10742f8``): verify vs continue contrasts and the naive
  oracle headroom on ``digits_mlp`` and ``openml_ionosphere``. PILOT, 6 instances.

Not read: the B1/B2 exam campaigns (on TASL-7, not in the repository), sweep 2 and T1 data (do not exist), fresh
audits of sweep 1 (do not exist).

Units. Increments are reported in sigma_d (sweep) or sigma_node (Track S), **and** in a second noise unit: the median
``sd_joint`` over all C1 edits for sweep 1 ("paired, all edits"), the robust sd of delta_hat - delta_audit for Track S. "Near" is within 0.5 of the unit.
``float('inf')`` is written as the string ``"inf"``; a node-level forecaster whose assumed noise is at least the
observed increment sd is flagged ``misspecified`` instead of reporting a value; robust statistics with MAD = 0 are
flagged ``degenerate``.

Deviation from the runbook (PH step 3): the census reads the raw ledgers through the small adapters below
(``join_keeps``, ``parse_sweep_campaign``, ``c1_paired``), not through P1 records; converting Paper B ledgers into
``spt_transition/v1`` rows is the loader of BUILD_LIST B5, which depends on Paper B revision W1.

Thresholds that make a channel "decision-relevant" are proposed in the report, not set here.
"""
from __future__ import annotations

import json
import math
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from scipy.stats import norm

TRACKS_PIN = "fab88fced839c5fb794ed62a0742b4646cb76ea2"
SWEEP_PIN = "10742f85f3450eb93650ac645182460a755ab89e"
TRACKS_RUNS = {
    "digits_mlp": {"s04": "results/r1/tracks/digits_mlp/s04_rerun20261111",
                   "s05": "results/r1/tracks/digits_mlp/s05_t7_20261113"},
    "tabular_mlp": {"s04": "results/r1/tracks/tabular_mlp/s04_t7_20261114",
                    "s05": "results/r1/tracks/tabular_mlp/s05_t7_20261114"},
}
S11_FILES = {"digits_mlp": "results/r1/tracks/digits_mlp/s11/digits.json",
             "tabular_mlp": "results/r1/tracks/tabular_mlp/s11/tabular.json",
             "openml_breast_w": "results/r1/tracks/openml_breast_w/s11/breast_w.json"}
SWEEP_RUNS = {"none": "results/r1/evidence/C3_sweep_none_20261027T224356Z",
              "append_only_summary": "results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z"}
C1_FILE = "results/r1/noise/D28_REPAIR_20261027/summary.json"
C3_PILOT = "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
E1B_FILES = ("results/r1/pilot/E1b_20261012T161034Z/analysis.json",
             "results/r1/pilot/E1b_20261013T151857Z/analysis.json",
             "results/r1/pilot/E1b_vary_ionosphere_20261012/analysis.json")
PRICE_SIGMA = 0.1          # Track S's declared run price, in sigma units
NEAR_BAND = 0.5            # +- band around a threshold, in units of the stated noise unit
TAIL = 4.0                 # |increment| beyond this many sigma counts as tail


# ---------------------------------------------------------------- reading pinned blobs

class Blobs:
    """Read files at a commit through one ``git cat-file --batch`` process; record what was read."""

    def __init__(self, repo: Path):
        self.repo = Path(repo)
        self.read_log: dict[tuple[str, str], str] = {}
        self.proc = subprocess.Popen(["git", "-C", str(self.repo), "cat-file", "--batch"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE)

    def read(self, ref: str, path: str) -> bytes:
        self.proc.stdin.write(f"{ref}:{path}\n".encode())
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().decode().split()
        if len(header) < 3 or header[1] == "missing":
            raise FileNotFoundError(f"{ref[:8]}:{path}")
        data = self.proc.stdout.read(int(header[2]))
        self.proc.stdout.read(1)
        self.read_log[(ref, path)] = header[0]
        return data

    def jsonl(self, ref: str, path: str) -> list[dict]:
        return [json.loads(l) for l in self.read(ref, path).decode().splitlines() if l.strip()]

    def json(self, ref: str, path: str):
        return json.loads(self.read(ref, path))

    def ls(self, ref: str, path: str) -> list[str]:
        return subprocess.run(["git", "-C", str(self.repo), "ls-tree", "-r", "--name-only", ref, path], check=True,
                              capture_output=True, text=True).stdout.split()

    def tree_id(self, ref: str, path: str) -> str:
        return subprocess.run(["git", "-C", str(self.repo), "rev-parse", f"{ref}:{path}"], check=True,
                              capture_output=True, text=True).stdout.strip()

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


# ---------------------------------------------------------------- helpers

def v_star(mu: float, tau: float, sigma: float) -> float:
    """One-step value E[max(m_hat, 0)], prior N(mu, tau^2), measurement sd sigma (Track S S0.5 summary §4)."""
    if tau <= 0:
        return max(mu, 0.0)
    s = tau * tau / math.sqrt(tau * tau + sigma * sigma)
    return mu * norm.cdf(mu / s) + s * norm.pdf(mu / s)


def _r(x, k=3):
    if x is None:
        return None
    x = float(x)
    if math.isnan(x):
        return None
    return "inf" if math.isinf(x) else round(x, k)


def node_level_v_star(inc_sigma, noise_sd: float) -> dict:
    """Node-level forecaster fitted to observed increments (sigma units) with measurement sd ``noise_sd``."""
    x = np.asarray(inc_sigma, float)
    sd = float(np.std(x, ddof=1))
    if sd <= noise_sd:
        return {"noise_sd": _r(noise_sd, 4), "observed_sd": _r(sd), "status": "misspecified (observed sd <= noise sd)"}
    tau = math.sqrt(sd * sd - noise_sd * noise_sd)
    vs = v_star(float(np.mean(x)), tau, noise_sd)
    return {"noise_sd": _r(noise_sd, 4), "observed_sd": _r(sd), "status": "ok", "v_star": _r(vs, 4),
            "price_over_v_star": _r(PRICE_SIGMA / vs if vs > 0 else math.inf)}


def robust_sd(x) -> float:
    x = np.asarray(x, float)
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else float("nan")


def share(mask) -> float:
    m = np.asarray(mask, bool)
    return float(m.mean()) if m.size else float("nan")


def _se(x) -> float:
    x = np.asarray(x, float)
    return float(np.std(x, ddof=1) / math.sqrt(len(x))) if len(x) > 1 else float("nan")


@dataclass
class NodeCensus:
    node: str
    source: str
    sigma: float
    sigma_source: str
    n_campaigns: int
    e1: dict = field(default_factory=dict)
    e2: dict = field(default_factory=dict)
    keep_quality: dict = field(default_factory=dict)
    incumbent: dict = field(default_factory=dict)
    budget: dict = field(default_factory=dict)
    tails: dict = field(default_factory=dict)
    trial1: dict = field(default_factory=dict)
    per_mode: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------- adapters (pure functions, fixture-tested)

def join_keeps(roots: list[dict], rows: list[dict]) -> list[dict]:
    """Per S0.4 campaign: (delta_hat, delta_audit) of its keeps after trial 1, the audited gain y_terminal -
    y_after_trial1, and the number of keep decisions without a row. Rows map to E2 decisions with index > 1 by
    (instance without the ``tracks_`` prefix, budget_index)."""
    by = {(r["instance"].removeprefix("tracks_"), r["budget_index"]): r for r in rows}
    out = []
    for r in roots:
        if r.get("status") != "ok" or r.get("y_terminal") is None or r.get("y_after_trial1") is None:
            continue
        keeps, missing = [], 0
        for d in r["decisions"]:
            if d["epoch"] == "E2" and d["action"] == "keep" and d["index"] > 1:
                row = by.get((r["instance_id"], d["index"]))
                if row is None:
                    missing += 1
                else:
                    keeps.append((row["delta_hat"], row["delta_audit"]))
        out.append({"instance": r["instance_id"], "keeps": keeps, "missing": missing,
                    "audited_gain": r["y_terminal"] - r["y_after_trial1"]})
    return out


def logged_action_mismatches(roots: list[dict], rows: list[dict]) -> int:
    """S0.4 rows whose logged E2 action disagrees with the default keep rule delta_hat > 0."""
    act = {(r["instance_id"], d["index"]): d["action"] for r in roots for d in r["decisions"] if d["epoch"] == "E2"}
    bad = 0
    for row in rows:
        a = act.get((row["instance"].removeprefix("tracks_"), row["budget_index"]))
        if a in ("keep", "discard") and (a == "keep") != (row["delta_hat"] > 0):
            bad += 1
    return bad


def parse_sweep_campaign(trials: list[dict]) -> dict:
    """One sweep-1 campaign.

    Duplicates by patch hash; comparisons = ``delta_vs_best`` of valid, non-duplicate trials after the first;
    kept increments; keeps after trial 1; the trial-1 metric (the first ``current_best_before``); the final recorded
    best; invalid trials.
    """
    trials = sorted(trials, key=lambda t: t["budget_index"])
    seen, dup, comps, kept, invalid = set(), 0, [], [], 0
    for t in trials:
        is_dup = t["patch_hash"] in seen
        seen.add(t["patch_hash"])
        dup += is_dup
        if t["validity_status"] != "valid":
            invalid += 1
            continue
        if t["delta_vs_best"] is not None and not is_dup:
            comps.append(t["delta_vs_best"])
            if t["decision"] == "kept":
                kept.append(t["delta_vs_best"])
    befores = [t["current_best_before"] for t in trials if t["current_best_before"] is not None]
    after_keeps = [t["current_best_before"] + t["delta_vs_best"] for t in trials
                   if t["decision"] == "kept" and t["delta_vs_best"] is not None and t["current_best_before"] is not None]
    return {"n_trials": len(trials), "duplicates": dup, "comparisons": comps, "kept": kept, "invalid": invalid,
            "keeps_after_trial1": len(kept), "trial1_metric": befores[0] if befores else None,
            "final_best": max(befores + after_keeps) if befores else None}


def c1_paired(node_rec: dict) -> dict:
    """C1 per-node noise summary. ``sd_joint`` already is the sd of a paired difference; it is used as is."""
    eds = node_rec["edits"]
    sds = [e["sd_joint"] for e in eds if e.get("sd_joint") is not None]
    mat = [e["sd_joint"] for e in eds if e.get("sd_joint") is not None and e.get("material")]
    regrets = [e["decision_regret"] for e in eds if e.get("decision_regret") is not None]
    flips = [e["flip_emp"] for e in eds if e.get("flip_emp") is not None]
    return {"paired_sd": float(np.median(sds)) if sds else float("nan"),
            "paired_sd_material": float(np.median(mat)) if mat else float("nan"),
            "paired_sd_min": float(min(sds)) if sds else float("nan"),
            "paired_sd_max": float(max(sds)) if sds else float("nan"),
            "start_seed_sd": node_rec.get("sigma_joint"),
            "flip_emp_mean": float(np.mean(flips)) if flips else float("nan"),
            "campaign_wrong_share": share([bool(e.get("campaign_wrong")) for e in eds]),
            "decision_regret_median": float(np.median(regrets)) if regrets else float("nan"),
            "material_share": share([bool(e.get("material")) for e in eds]),
            "default_metric": node_rec.get("default_metric"), "n_edits": len(eds)}


# ---------------------------------------------------------------- Track S

def census_tracks(blobs: Blobs, node: str) -> NodeCensus:
    runs = TRACKS_RUNS[node]
    m5 = blobs.json(TRACKS_PIN, runs["s05"] + "/manifest.json")
    m4 = blobs.json(TRACKS_PIN, runs["s04"] + "/manifest.json")
    sig, g = float(m5["sigma_node"]), float(m5["g0"])
    all5 = blobs.jsonl(TRACKS_PIN, runs["s05"] + "/roots.jsonl")
    roots5 = [r for r in all5 if r["policy"] == "a2u" and r["rep"] == 0]
    dec = [d for r in roots5 for d in r["decisions"]]
    e1 = [d for d in dec if d["epoch"] == "E1" and d["eligible"]]
    e1_all = [d for d in dec if d["epoch"] == "E1"]
    e2 = [d for d in dec if d["epoch"] == "E2" and d.get("margin") is not None]
    e2_all = [d for d in dec if d["epoch"] == "E2"]
    v = np.array([d["index_value"] for d in e1])
    m1 = np.array([d["margin"] for d in e1])
    m2 = np.array([d["margin"] for d in e2])
    rows = blobs.jsonl(TRACKS_PIN, runs["s04"] + "/s04_rows.jsonl")
    roots4 = blobs.jsonl(TRACKS_PIN, runs["s04"] + "/roots.jsonl")
    dh = np.array([r["delta_hat"] for r in rows])
    da = np.array([r["delta_audit"] for r in rows])
    se = np.array([r["se"] for r in rows])
    cmp_sd, cmp_rsd = float(np.std(dh - da, ddof=1)), robust_sd(dh - da)
    c = NodeCensus(node, "Track S S0.4/S0.5 (A2-U, qwen2.5-coder:7b)", sig, "run manifest sigma_node", len(roots5))
    c.notes += [f"hosts: S0.4 {m4.get('host')}, S0.5 {m5.get('host')}",
                "S0.4 kept iff delta_hat > 0 (ExecuteNonRuleController, prior None); S0.5 kept iff A2-U m_hat > 0",
                "trial 1 is executed and kept unconditionally (no incumbent metric before it)"]
    c.e1 = {
        "n_eligible": len(e1), "price_sigma": _r(g / sig),
        "v_star_median_sigma": _r(np.median(v) / sig), "v_star_range_sigma": _r(np.ptp(v) / sig),
        "margin_min_sigma": _r(m1.min() / sig), "margin_max_sigma": _r(m1.max() / sig),
        "price_over_v_star": _r(g / np.median(v)),
        "near_price_share": _r(share(np.abs(m1) <= NEAR_BAND * sig)),
        "rule_skip_share": _r(share([d["action"] == "skip" for d in e1_all])),
        "skip_reasons": dict(Counter(d.get("skip_reason") for d in e1_all if d["action"] == "skip")),
    }
    c.e2 = {
        "n_with_margin": len(e2),
        "near_zero_share": _r(share(np.abs(m2) <= NEAR_BAND * sig)),
        "near_zero_share_cmp_unit": _r(share(np.abs(m2) <= NEAR_BAND * cmp_rsd)),
        "margin_p05_sigma": _r(np.percentile(m2, 5) / sig), "margin_p95_sigma": _r(np.percentile(m2, 95) / sig),
        "actions": dict(Counter(d["action"] for d in e2_all)),
        "keep_share": _r(sum(d["action"] == "keep" for d in e2_all) / len(e2_all)),
    }
    trunc = blobs.jsonl(TRACKS_PIN, runs["s05"] + "/s05b_truncated.jsonl")
    byw = defaultdict(list)
    for t in trunc:
        byw[t["W"]].append(t["binding"])
    c.budget = {"binding_share_by_W": {int(w): _r(share(b), 2) for w, b in sorted(byw.items())},
                "llm_cap_reached_share_at_W40": _r(share([r["llm_calls"] >= r["llm_cap"] for r in roots5]), 2),
                "runs_used_at_W40": [int(min(r["runs_used"] for r in roots5)), int(max(r["runs_used"] for r in roots5))],
                "shadow_price": "undefined: V* is constant across proposals, so a binding W changes where a campaign "
                                "stops, not any decision (S0.5 summary §4); W matters here only as the price of "
                                "verify runs"}
    kept = dh > 0
    clear = np.abs(da) > 2 * se
    miss = ~kept & (da > 0)
    c.keep_quality = {
        "n_audited": len(rows), "audit_k": int(rows[0]["k"]),
        "keep_rule": "S0.4: delta_hat > 0 (the rule those campaigns used)",
        "logged_action_mismatches": logged_action_mismatches(roots4, rows),
        "false_keep": _r(share(da[kept] <= 0)), "n_kept": int(kept.sum()),
        "missed_keep": _r(share(da[~kept] > 0)), "n_discarded": int((~kept).sum()),
        "false_keep_clear": _r(share(da[kept & clear] <= 0)), "missed_keep_clear": _r(share(da[~kept & clear] > 0)),
        "missed_keeps_that_are_ties": int((miss & (dh == 0)).sum()), "n_missed": int(miss.sum()),
        "missed_audited_median_sigma": _r(np.median(da[miss]) / sig) if miss.any() else None,
        "missed_audited_max_sigma": _r(da[miss].max() / sig) if miss.any() else None,
        "corr_delta_hat_audit": _r(np.corrcoef(dh, da)[0, 1]),
        "comparison_noise_sd_sigma": _r(cmp_sd / sig), "comparison_noise_robust_sd_sigma": _r(cmp_rsd / sig),
    }
    c.tails = {"audit_positive_share": _r(share(da > 0)),
               "audit_tail_positive_share": _r(share(da > TAIL * sig)),
               "audit_tail_negative_share": _r(share(da < -TAIL * sig)),
               "audit_sd_sigma": _r(np.std(da, ddof=1) / sig), "audit_robust_sd_sigma": _r(robust_sd(da) / sig),
               "failed_invalid_share_E2": _r(c.e2["actions"].get("failed_invalid", 0) / len(e2_all))}
    camps = join_keeps(roots4, rows)
    per_keep = np.array([h - a for cp in camps for h, a in cp["keeps"]])
    per_camp = np.array([sum(h - a for h, a in cp["keeps"]) for cp in camps])
    nkeeps = np.array([len(cp["keeps"]) for cp in camps])
    c.incumbent = {
        "measure": "sum over keeps after trial 1 of (delta_hat - delta_audit): a summed per-keep selection bias on "
                   "the S0.4 audit seeds; it cancels any shared offset of the recorded trial-1 value, so it is not "
                   "the incumbent-value curse itself",
        "n_campaigns": len(camps), "n_keeps": int(len(per_keep)),
        "per_keep_mean_sigma": _r(per_keep.mean() / sig), "per_keep_se_sigma": _r(_se(per_keep) / sig),
        "per_campaign_mean_sigma": _r(per_camp.mean() / sig), "per_campaign_se_sigma": _r(_se(per_camp) / sig),
        "corr_with_n_keeps": _r(np.corrcoef(nkeeps, per_camp)[0, 1]) if nkeeps.std() > 0 else None,
        "keeps_without_row": int(sum(cp["missing"] for cp in camps)),
        "reading": "no winner's curse detected (per-keep mean within 2 se of 0)"
        if abs(per_keep.mean()) <= 2 * _se(per_keep) else "per-keep mean differs from 0 by more than 2 se",
    }
    allr = [r for r in all5 + roots4 if r.get("y_after_trial1") is not None and r.get("y_start") is not None]
    drop = np.array([(r["y_after_trial1"] - r["y_start"]) / sig for r in allr])
    net = np.array([(r["y_terminal"] - r["y_start"]) / sig for r in allr if r.get("y_terminal") is not None])
    distinct = {(round(r["y_start"], 9), round(r["y_after_trial1"], 9), round(r.get("y_terminal") or 0.0, 9))
                for r in allr}
    c.trial1 = {"n_campaigns": len(allr), "n_distinct_outcomes": len(distinct),
                "independence_note": "S0.5 static roots repeat the a2u roots' actions and y_terminal (S0.5 summary "
                                     "section 4), so fewer campaigns are distinct than listed",
                "drop_median_sigma": _r(np.median(drop)),
                "drop_range_sigma": [_r(drop.min()), _r(drop.max())],
                "net_terminal_minus_start_median_sigma": _r(np.median(net)),
                "note": "recorded gains after trial 1 are mostly recoveries of the trial-1 drop"}
    return c


# ---------------------------------------------------------------- sweep 1

def census_sweep(blobs: Blobs, c1: dict) -> list[NodeCensus]:
    per_node: dict[str, dict[str, list]] = defaultdict(dict)
    sigmas = {}
    for mode, run in SWEEP_RUNS.items():
        man = blobs.json(SWEEP_PIN, run + "/manifest.json")
        for node, nz in man["noise"].items():
            sigmas[node] = float(nz["sigma_d"])
        files = [f for f in blobs.ls(SWEEP_PIN, run + "/provenance/ledgers/roots") if f.endswith("root_trials.jsonl")]
        for f in files:
            trials = blobs.jsonl(SWEEP_PIN, f)
            if trials:
                per_node[trials[0]["node_id"]].setdefault(mode, []).append(parse_sweep_campaign(trials))
    out = []
    for node in sorted(per_node):
        sig = sigmas[node]
        pnode = c1.get(node, {})
        psd = pnode.get("paired_sd", float("nan")) / sig            # paired sd in sigma_d units
        camps = [cp for mode in per_node[node].values() for cp in mode]
        comps = np.array([x for cp in camps for x in cp["comparisons"]]) / sig
        kept = np.array([x for cp in camps for x in cp["kept"]]) / sig
        n_trials = sum(cp["n_trials"] for cp in camps)
        nz = comps != 0
        rsd = robust_sd(comps)
        c = NodeCensus(node, "Paper B sweep 1 (C3 labels, qwen2.5-coder:7b, 20 runs)", sig,
                       "sweep manifest noise.sigma_d (D28 composite)", len(camps))
        c.e1 = {"price_sigma": PRICE_SIGMA,
                "node_level_noise_1_sigma_d": node_level_v_star(comps, 1.0),
                "node_level_noise_paired_all_edits": node_level_v_star(comps, psd) if math.isfinite(psd) else None,
                "per_proposal_discrimination": "not measurable without a per-proposal forecaster (Paper B C3)",
                "reading": "node-level fits depend on the noise unit and the increments are zero-inflated; E1 "
                           "relevance is not determinable from them"}
        c.e2 = {"n_comparisons": len(comps),
                "near_zero_share_sigma_d": _r(share(np.abs(comps) <= NEAR_BAND)),
                "near_zero_share_paired_all_edits": _r(share(np.abs(comps) <= NEAR_BAND * psd)) if math.isfinite(psd) else None,
                "exact_zero_share": _r(share(~nz)),
                "keep_share": _r(len(kept) / len(comps) if len(comps) else float("nan")),
                "kept_increment_median_sigma_d": _r(np.median(kept)) if len(kept) else None,
                "kept_increment_median_paired_all_edits": _r(np.median(kept) / psd) if len(kept) and psd > 0 else None,
                "increment_sd_sigma_d": _r(np.std(comps, ddof=1)),
                "increment_robust_sd_sigma_d": _r(rsd) if rsd > 0 else "degenerate (MAD = 0)"}
        c.keep_quality = {"c1_paired_sd_all_edits_sigma_d": _r(psd, 4),
                          "c1_paired_sd_material_edits_sigma_d":
                              _r(pnode.get("paired_sd_material", float("nan")) / sig, 4),
                          "c1_paired_sd_edit_range_sigma_d":
                              [_r(pnode.get("paired_sd_min", float("nan")) / sig, 3),
                               _r(pnode.get("paired_sd_max", float("nan")) / sig, 3)],
                          "c1_flip_emp_mean": _r(pnode.get("flip_emp_mean")),
                          "c1_campaign_wrong_share": _r(pnode.get("campaign_wrong_share")),
                          "c1_decision_regret_median_sigma_d":
                              _r(pnode.get("decision_regret_median", float("nan")) / sig),
                          "note": "no fresh audits of sweep 1; C1 gives single-seed sign-flip rates on 5 standard "
                                  "edits per node"}
        dm = pnode.get("default_metric")
        t1 = np.array([(cp["trial1_metric"] - dm) / sig for cp in camps if cp["trial1_metric"] is not None and dm])
        gain = np.array([(cp["final_best"] - cp["trial1_metric"]) / sig for cp in camps
                         if cp["final_best"] is not None and cp["trial1_metric"] is not None])
        ssd = pnode.get("start_seed_sd")
        c.trial1 = {"trial1_minus_c1_default_median_sigma_d": _r(np.median(t1)) if len(t1) else None,
                    "start_config_seed_sd_sigma_d": _r(ssd / sig) if ssd else None,
                    "note": "trial-1 metric at instance seeds vs the C1 default at the C1 seed: compare with the start "
                            "configuration's own seed sd",
                    "recorded_gain_after_trial1_median_sigma_d": _r(np.median(gain)) if len(gain) else None}
        c.tails = {"failed_invalid_share": _r(sum(cp["invalid"] for cp in camps) / n_trials),
                   "tail_share": _r(share(np.abs(comps) > TAIL)),
                   "negative_tail_share": _r(share(comps < -TAIL)), "positive_tail_share": _r(share(comps > TAIL))}
        for mode, cps in sorted(per_node[node].items()):
            nt = sum(cp["n_trials"] for cp in cps)
            c.per_mode[mode] = {
                "campaigns": len(cps),
                "duplicate_share": _r(sum(cp["duplicates"] for cp in cps) / nt),
                "comparisons_per_campaign": _r(np.mean([len(cp["comparisons"]) for cp in cps])),
                "keeps_after_trial1_per_campaign": _r(np.mean([cp["keeps_after_trial1"] for cp in cps])),
                "campaigns_without_keep_after_trial1": _r(share([cp["keeps_after_trial1"] == 0 for cp in cps])),
            }
        c.budget = {"runs_per_campaign": int(np.median([cp["n_trials"] for cp in camps])),
                    "e1_screening": "none (every proposal executed); duplicates by patch hash"}
        c.incumbent = {"note": "needs fresh audits of final incumbents"}
        out.append(c)
    return out


# ---------------------------------------------------------------- other sources

def c3_pilot(blobs: Blobs) -> dict:
    props = {p["proposal_id"]: p for p in blobs.jsonl(SWEEP_PIN, C3_PILOT + "/proposals.jsonl")}
    audits = blobs.jsonl(SWEEP_PIN, C3_PILOT + "/audits.jsonl")
    per = defaultdict(lambda: {"kept": 0, "false_keep": 0, "discarded": 0, "missed_keep": 0})
    for a in audits:
        if a.get("reason") != "random" or a["proposal_id"] not in props:
            continue
        p = props[a["proposal_id"]]
        d = per[a["node"]]
        if p["delta_hat"] > 0:
            d["kept"] += 1
            d["false_keep"] += int(a["delta_audit"] <= 0)
        else:
            d["discarded"] += 1
            d["missed_keep"] += int(a["delta_audit"] > 0)
    return {"label": "ENGINEERING_ONLY (older harness, other node versions, tiny sample)",
            "rule": "keep iff delta_hat > 0; random-selection rows; 6 fresh seeds", "per_node": dict(sorted(per.items()))}


def e1b_pilots(blobs: Blobs, sigmas: dict) -> list[dict]:
    out = []
    for f in E1B_FILES:
        a = blobs.json(SWEEP_PIN, f)
        for node, x in a["per_node"].items():
            if node == "ALL":
                continue
            k = x["contrasts"]
            s = sigmas.get(node)
            out.append({"file": f, "label": a.get("label"), "node": node, "n_points": x.get("n_points"),
                        "verify_minus_continue_sigma_d": _r(k["always_verify - rho"] / s) if s else None,
                        "oracle_naive_minus_continue_sigma_d": _r(k["oracle_naive - rho"] / s) if s else None})
    return out


def s11_interactions(blobs: Blobs, sigmas: dict) -> list[dict]:
    out = []
    for node, f in S11_FILES.items():
        d = blobs.json(TRACKS_PIN, f)
        s = sigmas.get(node)
        for r in d["results"]:
            lo, hi = r["ci95_t"]
            out.append({"node": node, "pair": "x".join(r["pair"]), "interaction_sigma": _r(r["interaction"] / s),
                        "ci95_excludes_0": bool(lo > 0 or hi < 0), "main_A_sigma": _r(r["main_A"] / s),
                        "main_B_sigma": _r(r["main_B"] / s)})
    return out


def run(repo: Path) -> dict:
    blobs = Blobs(repo)
    try:
        c1raw = blobs.json(SWEEP_PIN, C1_FILE)["nodes"]
        c1 = {n: c1_paired(v) for n, v in c1raw.items()}
        tracks = [census_tracks(blobs, n) for n in TRACKS_RUNS]
        sweep = census_sweep(blobs, c1)
        sig_sweep = {c.node: c.sigma for c in sweep}
        sig_s11 = {**sig_sweep, **{c.node: c.sigma for c in tracks}}
        extra = {"c1": {n: {k: (_r(v, 5) if isinstance(v, float) else v) for k, v in d.items()} for n, d in c1.items()},
                 "c3_audit_pilot": c3_pilot(blobs), "e1b_pilots": e1b_pilots(blobs, sig_sweep),
                 "s11_interactions": s11_interactions(blobs, sig_s11)}
        inputs = sorted({(ref, path, oid) for (ref, path), oid in blobs.read_log.items()
                         if "/provenance/ledgers/" not in path})
        trees = [(SWEEP_PIN, r + "/provenance/ledgers", blobs.tree_id(SWEEP_PIN, r + "/provenance/ledgers"))
                 for r in SWEEP_RUNS.values()]
    finally:
        blobs.close()
    return {"schema": "paperc_census/v2", "pins": {"tracks": TRACKS_PIN, "sweep": SWEEP_PIN},
            "constants": {"price_sigma": PRICE_SIGMA, "near_band": NEAR_BAND, "tail_sigma": TAIL},
            "inputs": [{"ref": r[:8], "path": p, "object": o} for r, p, o in inputs + trees],
            "tracks": [asdict(c) for c in tracks], "sweep": [asdict(c) for c in sweep], "other": extra}


def main(repo: Path | None = None) -> Path:
    repo = repo or Path(__file__).resolve().parents[3]
    out = Path(__file__).resolve().parents[2] / "census" / "census_v1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(run(repo), indent=2, sort_keys=True) + "\n")
    return out


if __name__ == "__main__":
    print(main())
