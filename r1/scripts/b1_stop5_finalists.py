"""STOP 5: independent recomputation of the B1 finalists from the published batch manifests.

ENGINEERING_ONLY; AI-assisted (Claude, Mac agent). Reimplements the frozen ``x5_rule/v2`` finalist rule without
importing ``r1.exam.analyze``:

* checks the evidence ``SHA256SUMS``, the rule bytes (sha256 ``53018aa7…16ad``) and every manifest's ``rule_sha256``;
* checks the registry (bytes from the run HEAD) against the manifests' ``registry_sha256`` and each manifest's family,
  role and registry order;
* checks every audited proposal: seeds 9101–9104, four paired metrics, ``delta_audit`` = mean(candidate) − mean(incumbent);
* recomputes mu_hat (mean thinking-off ``delta_audit``) with the rule's paired node-instance cluster bootstrap;
* eligibility: role candidate, ``stage_a_pass``, ``d28_pass`` and thinking-off capable (registry ``thinking_policy``:
  not always_on; mode off; a switchable model needs its declared off_switch);
* finalists: top ``top_by_mean`` by mu_hat (ties: registry order), plus the best of an eligible family absent from
  the top four, at most ``maximum``;
* compares with the published complete-batch verifier output.

``d28_pass`` is read from the batch manifests: the run's ``verify_batch`` checked it against the root ledgers on the
host; those ledgers are not on the Mac, so D28 is not re-derived here. A descriptive variant without the D28 filter
is printed and marked as not the rule.

Usage: python r1/scripts/b1_stop5_finalists.py --evidence <dir> --rule <x5_rule_v2.yaml> --registry <registry.yaml>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import yaml

RULE_SHA = "53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad"
B1_AUDIT_SEEDS = [9101, 9102, 9103, 9104]


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_sums(evidence: Path) -> dict:
    out = {}
    for line in (evidence / "SHA256SUMS").read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.strip().lstrip("*")
        actual = sha(evidence / name)
        if actual != digest:
            raise SystemExit(f"STOP: {name} sha256 {actual} != SHA256SUMS {digest}")
        out[name] = digest
    return out


def registry_rows(reg: dict) -> list[dict]:
    """The runner's registry order: software anchors, LLM anchors, candidates, sensitivities."""
    return (reg["software_anchors"] + [r for r in reg["candidates"] if r["role"] == "anchor"]
            + [r for r in reg["candidates"] if r["role"] == "candidate"] + reg.get("sensitivities", []))


def thinking_off_capable(policy) -> bool:
    if not isinstance(policy, dict) or policy.get("mode") == "always_on" or policy.get("mode") != "off":
        return False
    return policy.get("off_switch") is True or policy.get("switchable") is not True


def cluster_bootstrap(rows: list[dict], resamples: int, seed: int) -> dict:
    groups: dict[str, list[float]] = {}
    for r in rows:
        groups.setdefault(str(r["instance_id"]), []).append(float(r["delta_audit"]))
    clusters = list(groups.values())
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(resamples):
        pick = rng.integers(0, len(clusters), len(clusters))
        vals = [v for i in pick for v in clusters[i]]
        draws.append(sum(vals) / len(vals))
    lo, hi = np.quantile(draws, [0.025, 0.975])
    allv = [v for c in clusters for v in c]
    return {"mean": sum(allv) / len(allv), "lower": float(lo), "upper": float(hi), "clusters": len(clusters)}


def choose(rows: list[dict], rule: dict, *, use_d28: bool = True) -> list[str]:
    elig = [r for r in rows if r["role"] == "candidate" and r["stage_a_pass"] and (r["d28_pass"] or not use_d28)
            and r["thinking_off_capable"] and r["mu_hat"] is not None]
    ranked = sorted(elig, key=lambda r: (-r["mu_hat"], r["registry_order"]))
    top = ranked[: rule["finalists"]["top_by_mean"]]
    fams = {r["family"] for r in top}
    extra = [r for r in ranked[len(top):] if r["family"] not in fams][: rule["finalists"]["absent_family_extra"]]
    return [r["candidate"] for r in top + extra][: rule["finalists"]["maximum"]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--rule", type=Path, required=True)
    ap.add_argument("--registry", type=Path, required=True)
    a = ap.parse_args(argv)
    sums = check_sums(a.evidence)
    rule_sha = sha(a.rule)
    if rule_sha != RULE_SHA:
        raise SystemExit(f"STOP: rule sha256 {rule_sha} != frozen {RULE_SHA}")
    rule = yaml.safe_load(a.rule.read_text())
    if rule.get("version") != "x5_rule/v2" or rule.get("ranking_mode") != "off":
        raise SystemExit("STOP: rule is not x5_rule/v2 with thinking-off ranking")
    data = json.loads((a.evidence / "b1_manifests.json").read_text())
    if data.get("label") != "EXAM":
        raise SystemExit("STOP: manifests label")
    manifests = data["manifests"]
    reg_sha = sha(a.registry)
    reg = yaml.safe_load(a.registry.read_text())
    order = {r["id"]: i for i, r in enumerate(registry_rows(reg))}
    by_id = {r["id"]: r for r in registry_rows(reg)}
    rows, checked = [], 0
    for m in manifests:
        cid = m["candidate"]
        if m.get("label") != "EXAM" or m.get("phase") != "b1" or m.get("status") != "COMPLETE":
            raise SystemExit(f"STOP: {cid} manifest not a complete EXAM B1 manifest")
        if m.get("rule_sha256") != RULE_SHA:
            raise SystemExit(f"STOP: {cid} rule_sha256 differs")
        if m.get("registry_sha256") != reg_sha:
            raise SystemExit(f"STOP: {cid} registry_sha256 {m.get('registry_sha256')} != registry bytes {reg_sha}")
        src = by_id[cid]
        if (m["family"], m["role"], m["registry_order"]) != (src["family"], src["role"], order[cid]):
            raise SystemExit(f"STOP: {cid} family/role/order differs from registry")
        for p in m["audited_proposals"]:
            if p["audit_seeds"] != B1_AUDIT_SEEDS or len(p["candidate_metrics"]) != 4 or len(p["incumbent_metrics"]) != 4:
                raise SystemExit(f"STOP: {cid} audit seeds/metrics")
            d = sum(p["candidate_metrics"]) / 4 - sum(p["incumbent_metrics"]) / 4
            if not math.isclose(d, float(p["delta_audit"]), abs_tol=1e-12):
                raise SystemExit(f"STOP: {cid} {p['proposal_id']} delta differs from raw audits")
            checked += 1
        off = [p for p in m["audited_proposals"] if p["mode"] == "off"]
        cap = thinking_off_capable(src.get("thinking_policy")) if m["role"] == "candidate" else None
        boot = cluster_bootstrap(off, rule["bootstrap"]["resamples"], rule["bootstrap"]["seed"]) if off else None
        rows.append({"candidate": cid, "role": m["role"], "family": m["family"], "registry_order": m["registry_order"],
                     "stage_a_pass": m["stage_a_pass"], "d28_pass": m["d28_pass"], "thinking_off_capable": cap,
                     "thinking_policy_mode": (src.get("thinking_policy") or {}).get("mode"),
                     "n_off_audited": len(off), "mu_hat": boot["mean"] if boot else None, "bootstrap": boot})
    finalists = choose(rows, rule)
    ranking = [r["candidate"] for r in sorted([r for r in rows if r["role"] == "candidate" and r["mu_hat"] is not None],
                                               key=lambda r: (-r["mu_hat"], r["registry_order"]))]
    ver = json.loads((a.evidence / "complete_batch_verifier.json").read_text())
    vmu = {r["candidate"]: r.get("mu_hat") for r in ver["rows"]}
    vci = {r["candidate"]: r.get("cluster_interval") for r in ver["rows"]}
    mu_diff = max(abs(r["mu_hat"] - vmu[r["candidate"]]) for r in rows if r["mu_hat"] is not None)
    ci_diff = max(max(abs(r["bootstrap"]["lower"] - vci[r["candidate"]]["lower"]),
                      abs(r["bootstrap"]["upper"] - vci[r["candidate"]]["upper"]))
                  for r in rows if r["bootstrap"] is not None and vci.get(r["candidate"]))
    out = {"schema": "b1_stop5_finalists/v1", "label": "ENGINEERING_ONLY",
           "evidence_sha256": sums, "rule_sha256": rule_sha, "registry_sha256": reg_sha,
           "audited_proposals_checked": checked, "rows": rows,
           "finalists": finalists,
           "verifier": {"file_sha256": sums.get("complete_batch_verifier.json"), "finalists": ver["finalists"],
                        "finalists_equal": finalists == ver["finalists"], "max_abs_mu_hat_diff": mu_diff,
                        "max_abs_interval_diff": ci_diff, "rule_sha256": ver.get("rule_sha256"),
                        "execution_label": ver.get("execution_label")},
           "candidate_ranking_by_mu_hat_all_candidates": ranking,
           "descriptive_not_the_rule": {
               "finalists_if_d28_filter_ignored": choose(rows, rule, use_d28=False),
               "note": "D28 is part of x5_rule/v2 eligibility; this variant is descriptive only"},
           "limits": "d28_pass is read from the batch manifests (checked against the root ledgers by verify_batch on "
                     "the host at run time); the root ledgers are not on the Mac, so D28 is not re-derived here"}
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0 if out["verifier"]["finalists_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
