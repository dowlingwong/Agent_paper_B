"""Headroom census on existing logs (build runbook PH; BUILD_LIST B16; R1-PAPERC-CENSUS-FIRST). ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 16 Nov 2026).

Read-only. Every input is read from a pinned commit of the repository with ``git cat-file`` (nothing is copied
into ``paperC/``), so the census is reproducible from the clone alone. Sources:

* **Track S** (``trackS-ops-20261030`` @ ``fab88fc``), nodes ``digits_mlp`` and ``tabular_mlp``:
  S0.5 roots (A2-U, rep 0; E1 and E2 decisions with V\\* and margins), S0.5b truncations (budget binding per W),
  S0.4 rows (each executed proposal's campaign increment ``delta_hat`` and its 5-seed fresh audit ``delta_audit``)
  and S0.4 roots (audited start / after-trial-1 / terminal values). ``sigma_node`` from the run manifests.
* **Paper B sweep 1** (``codex/coordinator-20261031`` @ ``10742f8``): the C3 label sweep with the 7B proposer,
  8 CPU nodes x 18 instances x 20 runs, memory ``none`` and ``append_only_summary``. Ledgers carry, per trial, the
  validity, failure category, keep decision and ``delta_vs_best`` at the node's default seed. No fresh audits exist
  for sweep 1 (Paper B's B.2 has not run), so keep quality is measured only on Track S. ``sigma_d`` per node comes
  from the sweep manifest (the D28 noise table, "median sd_joint").

Quantities per node (all increments in units of the node's sigma):

* **E1 relevance** — under A2-U (Track S, from logged decisions): range of V\\*, V\\* - g, and the share of eligible
  decisions within +-0.5 sigma of the price. Under a node-level forecaster (sweep: one predictive law per node, fitted
  to the node's observed increments, plain and robust): V\\* and the ratio g / V\\* at Track S's price g = 0.1 sigma.
  A node-level forecaster has no per-proposal discrimination by construction (sd(V\\*) = 0), which is the A2-U
  situation; per-proposal discrimination needs Paper B's C3 belief and is not measurable here.
* **E2 relevance** — the share of keep decisions whose margin lies within +-0.5 sigma of 0 (Track S: A2-U's m_hat;
  sweep: the observed ``delta_vs_best`` of non-duplicate valid comparisons), and the share of keeps with an observed
  increment in (0, 1 sigma].
* **Keep quality** (Track S S0.4) — with the harness's default keep rule (keep iff delta_hat > 0): false-keep rate
  P(delta_audit <= 0 | delta_hat > 0), missed-keep rate P(delta_audit > 0 | delta_hat <= 0), the same restricted to
  audits whose sign is clear (|delta_audit| > 2 se), and the correlation of delta_hat and delta_audit.
* **Incumbent winner's curse** (Track S S0.4) — per campaign, recorded gain (sum of delta_hat over keeps after
  trial 1) minus audited gain (y_terminal - y_after_trial1).
* **Budget** — Track S: binding share per W from S0.5b. Sweep: every proposal is executed (no E1 screening), so
  runs = trials.
* **Tails and failures** — share of failed_invalid runs, duplicate proposals, and |increment| > 4 sigma.

The thresholds that would make a channel "decision-relevant" are not set here; the report proposes them and the
author decides (R1-PAPERC-CENSUS-FIRST).
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
SWEEP_RUNS = {"none": "results/r1/evidence/C3_sweep_none_20261027T224356Z",
              "append_only_summary": "results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z"}
PRICE_SIGMA = 0.1          # Track S's declared run price, in sigma units
NEAR_BAND = 0.5            # +- band around a threshold, in sigma units
TAIL = 4.0                 # |increment| beyond this many sigma counts as tail


# ---------------------------------------------------------------- reading pinned blobs

class Blobs:
    """Read files at a commit through one ``git cat-file --batch`` process."""

    def __init__(self, repo: Path):
        self.repo = Path(repo)
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
        return data

    def jsonl(self, ref: str, path: str) -> list[dict]:
        return [json.loads(l) for l in self.read(ref, path).decode().splitlines() if l.strip()]

    def json(self, ref: str, path: str):
        return json.loads(self.read(ref, path))

    def ls(self, ref: str, path: str) -> list[str]:
        return subprocess.run(["git", "-C", str(self.repo), "ls-tree", "-r", "--name-only", ref, path], check=True,
                              capture_output=True, text=True).stdout.split()

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


# ---------------------------------------------------------------- helpers

def v_star(mu: float, tau: float, sigma: float) -> float:
    """One-step value E[max(m_hat, 0)] of executing a proposal with prior N(mu, tau^2) and measurement sd sigma.

    m_hat ~ N(mu, s^2) with s = tau^2 / sqrt(tau^2 + sigma^2); E[max(m_hat, 0)] = mu Phi(mu/s) + s phi(mu/s).
    At mu = 0 this is 0.3989 tau^2 / sqrt(tau^2 + sigma^2), the expression in the Track S S0.5 summary §4.
    """
    if tau <= 0:
        return max(mu, 0.0)
    s = tau * tau / math.sqrt(tau * tau + sigma * sigma)
    return mu * norm.cdf(mu / s) + s * norm.pdf(mu / s)


def robust_sd(x) -> float:
    x = np.asarray(x, float)
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else float("nan")


def share(mask) -> float:
    m = np.asarray(mask, bool)
    return float(m.mean()) if m.size else float("nan")


def _r(x, k=3):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(float(x), k)


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
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------- Track S

def census_tracks(blobs: Blobs, node: str) -> NodeCensus:
    runs = TRACKS_RUNS[node]
    m5 = blobs.json(TRACKS_PIN, runs["s05"] + "/manifest.json")
    sig = float(m5["sigma_node"])
    g = float(m5["g0"])
    roots5 = [r for r in blobs.jsonl(TRACKS_PIN, runs["s05"] + "/roots.jsonl") if r["policy"] == "a2u" and r["rep"] == 0]
    dec = [d for r in roots5 for d in r["decisions"]]
    e1 = [d for d in dec if d["epoch"] == "E1" and d["eligible"]]
    e1_all = [d for d in dec if d["epoch"] == "E1"]
    e2 = [d for d in dec if d["epoch"] == "E2" and d.get("margin") is not None]
    e2_all = [d for d in dec if d["epoch"] == "E2"]
    v = np.array([d["index_value"] for d in e1])
    m1 = np.array([d["margin"] for d in e1])
    m2 = np.array([d["margin"] for d in e2])
    c = NodeCensus(node, "Track S S0.4/S0.5 (A2-U, qwen2.5-coder:7b)", sig, "run manifest sigma_node",
                   len(roots5))
    c.e1 = {
        "n_eligible": len(e1),
        "price_sigma": _r(g / sig),
        "v_star_median_sigma": _r(np.median(v) / sig),
        "v_star_range_sigma": _r(np.ptp(v) / sig),
        "margin_min_sigma": _r(m1.min() / sig), "margin_max_sigma": _r(m1.max() / sig),
        "price_over_v_star": _r(g / np.median(v)),
        "near_price_share": _r(share(np.abs(m1) <= NEAR_BAND * sig)),
        "rule_skip_share": _r(share([d["action"] == "skip" for d in e1_all])),
        "skip_reasons": dict(Counter(d.get("skip_reason") for d in e1_all if d["action"] == "skip")),
    }
    keeps = sum(d["action"] == "keep" for d in e2_all)
    c.e2 = {
        "n_with_margin": len(e2),
        "near_zero_share": _r(share(np.abs(m2) <= NEAR_BAND * sig)),
        "margin_p05_sigma": _r(np.percentile(m2, 5) / sig), "margin_p95_sigma": _r(np.percentile(m2, 95) / sig),
        "actions": dict(Counter(d["action"] for d in e2_all)),
        "keep_share": _r(keeps / len(e2_all)),
    }
    # budget binding per W (S0.5b)
    trunc = blobs.jsonl(TRACKS_PIN, runs["s05"] + "/s05b_truncated.jsonl")     # all 50 roots, as the S0.5 summary
    byw = defaultdict(list)
    for t in trunc:
        byw[t["W"]].append(t["binding"])
    c.budget = {"binding_share_by_W": {int(w): _r(share(b), 2) for w, b in sorted(byw.items())},
                "llm_cap_reached_share_at_W40": _r(share([r["llm_calls"] >= r["llm_cap"] for r in roots5]), 2),
                "runs_used_at_W40": [int(min(r["runs_used"] for r in roots5)), int(max(r["runs_used"] for r in roots5))]}
    # keep quality and winner's curse (S0.4)
    rows = blobs.jsonl(TRACKS_PIN, runs["s04"] + "/s04_rows.jsonl")
    dh = np.array([r["delta_hat"] for r in rows])
    da = np.array([r["delta_audit"] for r in rows])
    se = np.array([r["se"] for r in rows])
    kept = dh > 0
    clear = np.abs(da) > 2 * se
    c.keep_quality = {
        "n_audited": len(rows), "audit_k": int(rows[0]["k"]),
        "false_keep": _r(share(da[kept] <= 0)), "missed_keep": _r(share(da[~kept] > 0)),
        "false_keep_clear": _r(share(da[kept & clear] <= 0)), "missed_keep_clear": _r(share(da[~kept & clear] > 0)),
        "n_clear": int(clear.sum()),
        "corr_delta_hat_audit": _r(np.corrcoef(dh, da)[0, 1]),
        "sd_delta_hat_minus_audit_sigma": _r(np.std(dh - da, ddof=1) / sig),
        "audited_near_zero_share": _r(share(np.abs(da) <= NEAR_BAND * sig)),
        "keep_rule": "harness default/v1: keep iff delta_hat > 0",
    }
    c.tails = {"audit_tail_share": _r(share(np.abs(da) > TAIL * sig)),
               "audit_sd_sigma": _r(np.std(da, ddof=1) / sig), "audit_robust_sd_sigma": _r(robust_sd(da) / sig),
               "failed_invalid_share_E2": _r(c.e2["actions"].get("failed_invalid", 0) / len(e2_all))}
    roots4 = blobs.jsonl(TRACKS_PIN, runs["s04"] + "/roots.jsonl")
    rows_by = {(r["instance"].removeprefix("tracks_"), r["budget_index"]): r for r in rows}
    curse = []
    for r in roots4:
        if r.get("status") != "ok" or r["y_terminal"] is None or r["y_after_trial1"] is None:
            continue
        rec = 0.0
        missing = 0
        for d in r["decisions"]:
            if d["epoch"] == "E2" and d["action"] == "keep" and d["index"] > 1:
                row = rows_by.get((r["instance_id"], d["index"]))
                if row is None:
                    missing += 1
                else:
                    rec += row["delta_hat"]
        aud = r["y_terminal"] - r["y_after_trial1"]
        curse.append((rec - aud, rec, aud, missing))
    cu = np.array([x[0] for x in curse])
    c.incumbent = {"n_campaigns": len(curse), "recorded_minus_audited_gain_mean_sigma": _r(cu.mean() / sig),
                   "recorded_minus_audited_gain_sd_sigma": _r(cu.std(ddof=1) / sig),
                   "share_recorded_above_audited": _r(share(cu > 0)),
                   "keeps_without_row": int(sum(x[3] for x in curse))}
    c.notes.append("A2-U V* is nearly constant across proposals (S0.5 summary §4): E1 has no decision-relevant state.")
    return c


# ---------------------------------------------------------------- sweep 1

def _sweep_trials(blobs: Blobs, run: str) -> dict[str, list[list[dict]]]:
    out = defaultdict(list)
    files = [f for f in blobs.ls(SWEEP_PIN, run + "/provenance/ledgers/roots") if f.endswith("root_trials.jsonl")]
    for f in files:
        trials = sorted(blobs.jsonl(SWEEP_PIN, f), key=lambda t: t["budget_index"])
        if trials:
            out[trials[0]["node_id"]].append(trials)
    return out


def census_sweep(blobs: Blobs) -> list[NodeCensus]:
    per_node: dict[str, dict[str, list]] = defaultdict(dict)
    sigmas = {}
    for mode, run in SWEEP_RUNS.items():
        man = blobs.json(SWEEP_PIN, run + "/manifest.json")
        for node, nz in man["noise"].items():
            sigmas[node] = float(nz["sigma_d"])
        for node, camps in _sweep_trials(blobs, run).items():
            per_node[node][mode] = camps
    out = []
    for node in sorted(per_node):
        sig = sigmas[node]
        camps = [c for mode in per_node[node].values() for c in mode]
        trials = [t for c in camps for t in c]
        valid = [t for t in trials if t["validity_status"] == "valid"]
        invalid = [t for t in trials if t["validity_status"] != "valid"]
        dup, comps, kept_inc = 0, [], []
        for camp in camps:
            seen = set()
            for t in camp:
                is_dup = t["patch_hash"] in seen
                seen.add(t["patch_hash"])
                dup += is_dup
                if t["validity_status"] == "valid" and t["delta_vs_best"] is not None and not is_dup:
                    comps.append(t["delta_vs_best"])
                    if t["decision"] == "kept":
                        kept_inc.append(t["delta_vs_best"])
        d = np.array(comps) / sig
        k = np.array(kept_inc) / sig
        mu, sd, rsd = float(np.mean(d)), float(np.std(d, ddof=1)), robust_sd(d)
        tau_plain = math.sqrt(max(sd * sd - 1.0, 0.0))      # in sigma units; measurement sd taken as 1 sigma
        tau_rob = math.sqrt(max(rsd * rsd - 1.0, 0.0))
        vs_plain, vs_rob = v_star(mu, tau_plain, 1.0), v_star(float(np.median(d)), tau_rob, 1.0)
        c = NodeCensus(node, "Paper B sweep 1 (C3 labels, qwen2.5-coder:7b, 20 runs, memory none + summary)", sig,
                       "sweep manifest noise.sigma_d (D28 table)", len(camps))
        c.e1 = {"price_sigma": PRICE_SIGMA,
                "node_level_v_star_sigma": _r(vs_plain), "price_over_v_star": _r(PRICE_SIGMA / vs_plain if vs_plain else float("inf")),
                "node_level_v_star_robust_sigma": _r(vs_rob),
                "price_over_v_star_robust": _r(PRICE_SIGMA / vs_rob if vs_rob else float("inf")),
                "per_proposal_discrimination": "not measurable without a per-proposal forecaster (Paper B C3)"}
        nz = d != 0
        c.e2 = {"n_comparisons": len(comps), "near_zero_share": _r(share(np.abs(d) <= NEAR_BAND)),
                "exact_zero_share": _r(share(~nz)),
                "near_zero_share_nonzero": _r(share(np.abs(d[nz]) <= NEAR_BAND)),
                "keep_share": _r(len(kept_inc) / len(comps) if comps else float("nan")),
                "keeps_within_1sigma_share": _r(share((k > 0) & (k <= 1.0))),
                "increment_mean_sigma": _r(mu), "increment_sd_sigma": _r(sd), "increment_robust_sd_sigma": _r(rsd)}
        c.tails = {"failed_invalid_share": _r(len(invalid) / len(trials)),
                   "failure_categories": dict(Counter(t["failure_category"] for t in invalid)),
                   "duplicate_share": _r(dup / len(trials)),
                   "tail_share": _r(share(np.abs(d) > TAIL)),
                   "negative_tail_share": _r(share(d < -TAIL)), "positive_tail_share": _r(share(d > TAIL))}
        c.budget = {"runs_per_campaign": int(np.median([len(cc) for cc in camps])),
                    "e1_screening": "none (every proposal executed)"}
        c.keep_quality = {"note": "no fresh audits for sweep 1 (B.2 not run)"}
        c.incumbent = {"note": "needs fresh audits of final incumbents"}
        c.notes.append(f"modes: {sorted(per_node[node])}; campaigns per mode: "
                       f"{ {m: len(v) for m, v in per_node[node].items()} }")
        out.append(c)
    return out


def run(repo: Path) -> dict:
    blobs = Blobs(repo)
    try:
        tracks = [census_tracks(blobs, n) for n in TRACKS_RUNS]
        sweep = census_sweep(blobs)
    finally:
        blobs.close()
    return {"schema": "paperc_census/v1", "pins": {"tracks": TRACKS_PIN, "sweep": SWEEP_PIN},
            "constants": {"price_sigma": PRICE_SIGMA, "near_band_sigma": NEAR_BAND, "tail_sigma": TAIL},
            "tracks": [asdict(c) for c in tracks], "sweep": [asdict(c) for c in sweep]}


def main(repo: Path | None = None) -> Path:
    repo = repo or Path(__file__).resolve().parents[3]
    out = Path(__file__).resolve().parents[2] / "census" / "census_v1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(run(repo), indent=2, sort_keys=True) + "\n")
    return out


if __name__ == "__main__":
    print(main())
