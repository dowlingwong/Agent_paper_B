"""G.5 T1 label-run projection for the G.5 authorization draft (section 8). Pre-pilot; ENGINEERING_ONLY.

One formula with the G.4 recompute: ``g4_lib.g5_node`` (12 instances x W = 20; campaigns + audits of the
evaluated non-inert, non-duplicate proposals and their parents x K x run x 1.25 + 1,500 s per job). Pre-pilot
inputs: census run times (Ada, B1); campaign seconds per manager call = 60 s LLM + ran share x run x 1.25 + the
instance baseline amortized; keep share 0.2; cross-instance duplicate factor 1.0 (conservative: the pilot measures
the real rate). G5-MEM "both" doubles the campaigns and audits (12 instances per mode; an upper bound, since twin
campaigns share labels by key). Requested slot-hours: per job, 3,600 s + 1.5 x its GPU-seconds of work.
Usage: python sweep2/g4/g5_projection.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g4_lib  # noqa: E402

PARAMS = json.loads((Path(__file__).resolve().parent / "g4_dates_params.json").read_text())


def table() -> dict:
    out = {}
    for w in ("manager_calls", "worker_runs"):
        for mem, factor in (("one_mode", 1), ("both_modes", 2)):
            for share in (0.6, 0.8):
                for k in (6, 10):
                    gpu = slot = audited = 0.0
                    for node, run_s in PARAMS["run_seconds"].items():
                        per_call = PARAMS["llm_seconds_fallback"] + share * run_s * PARAMS["campaign_inflation"] \
                            + run_s / g4_lib.G5_W
                        r = g4_lib.g5_node(run_s=run_s, per_call_s=per_call, ran_share=share,
                                           keep_share=PARAMS["keep_share_fallback"], k=k, w_semantics=w,
                                           dup_factor=PARAMS["dup_factor"], audit_inflation=PARAMS["audit_inflation"],
                                           startup_s=PARAMS["startup_s"], walltime_limit_s=86400)
                        gpu += factor * r["gpu_hours"]
                        work_h = r["gpu_hours"] - r["jobs"] * PARAMS["startup_s"] / 3600
                        slot += factor * (r["jobs"] * 1.0 + 1.5 * work_h)
                        audited = factor * r["audited"]
                    out[f"W={w} MEM={mem} share={share} K={k}"] = {
                        "gpu_hours": round(gpu, 1), "requested_slot_hours": round(slot, 1),
                        "audited_per_node": round(audited)}
    return out


if __name__ == "__main__":
    print(json.dumps(table(), indent=1))
