"""Run and LLM-call accounting of online C3 campaigns (RUNBOOK Track H.6). ENGINEERING_ONLY; AI-assisted (Claude).

``campaign_usage`` reads one campaign's ledger and event stream and returns a
``r1.branch.matching.CampaignUsage`` for ``matching_report(..., usage=...)``:

* worker runs: trials whose worker ran (not control-plane skips, not
  precondition rejections), plus 2 r per verify;
* LLM calls: every manager proposal and revision of a non-deterministic manager
  (one call each, as the harness charges them) plus the controller's charged
  calls (``control_decision.llm_calls``: A4 queries, LLM self-control);
* sidecar forecasts: counted, compute seconds summed (compute only; not LLM
  calls); controller latency summed (descriptive).
"""
from __future__ import annotations

import json
from pathlib import Path

from r1.branch.matching import CampaignUsage


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def campaign_usage(records_path: Path | str, events_path: Path | str, *, arm: str, instance: str,
                   information_set: str, worker_run_cap: int | None, llm_call_cap: int | None,
                   manager_deterministic: bool) -> CampaignUsage:
    rows, events = _jsonl(Path(records_path)), _jsonl(Path(events_path))
    runs = 0
    for r in rows:
        mode = str(r.get("worker_mode") or "")
        if mode != "control_plane" and not mode.endswith("_precheck"):
            runs += 1
        verify = (r.get("extra", {}).get("control") or {}).get("verify")
        if verify:
            runs += 2 * int(verify.get("r", len(verify.get("pairs") or [])))
    manager_calls = 0
    if not manager_deterministic:
        manager_calls = sum(1 for e in events if e["event_type"] in ("proposal_created", "proposal_revised"))
        manager_calls += sum(1 for e in events if e["event_type"] == "proposal_rejected_inactive_key"
                             and not e["payload"].get("skipped"))
    decisions = [e["payload"] for e in events if e["event_type"] == "control_decision"]
    controller_calls = sum(int(d.get("llm_calls") or 0) for d in decisions)
    details = [d.get("detail") or {} for d in decisions]
    sidecar = [d for d in details if "sidecar_compute_s" in d]
    return CampaignUsage(arm=arm, instance=instance, information_set=information_set,
                         worker_run_cap=worker_run_cap, llm_call_cap=llm_call_cap, worker_runs=runs,
                         llm_calls=manager_calls + controller_calls, controller_llm_calls=controller_calls,
                         sidecar_calls=len(sidecar), sidecar_compute_s=float(sum(d["sidecar_compute_s"] for d in sidecar)),
                         prior_unavailable=sum(1 for e in events if e["event_type"] == "prior_unavailable"),
                         controller_latency_s=float(sum(float(d.get("latency_s") or 0.0) for d in details)))
