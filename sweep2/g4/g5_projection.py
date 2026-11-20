"""G.5 T1 label-run projection (draft T1_G5_AUTHORIZATION_DRAFT_20261120.md section 8). Pre-pilot; ENGINEERING_ONLY.

Per node, with r the census baseline run time (Ada, B1), s the executed share:
  campaigns: 12 baselines x r + manager calls x 60 s + ran proposals x r x 1.25
  audits:    (0.9 x ran + 12 + 0.2 x ran) x K x r x 1.25   (inert/duplicates excluded; keeps create parents)
  startup:   1,500 s per job; 2 campaign waves + audit chunks under 86,400 s - 3,600 s with the x 1.5 walltime rule
W "A" = 20 manager calls per campaign; W "B" = 20 worker runs with an LLM-call cap of 80 per campaign.
Usage: python sweep2/g4/g5_projection.py
"""
import math, json
RUN = {"mlab_cifar10":12.297,"mlab_imdb":64.142,"mlab_ogbn_arxiv":5.651,"mlgym_cifar10":31.731,"mlgym_fmnist":34.376,"mlgym_breakout_minatar":61.248}
LLM, F, A, KEEP, START, WALL = 60.0, 1.25, 0.9, 0.2, 1500.0, 86400 - 3600
def node(r, s, K, w):
    if w == "A":   # 20 manager calls per instance
        calls, ran = 240, 240 * s
    else:          # 20 worker runs per instance, LLM-call cap 80 per instance
        calls, ran = min(240 / s, 12 * 80), 240.0
    camp = 12 * r + calls * LLM + ran * r * F
    audited = ran * A
    parents = 12 + KEEP * ran
    aud = (audited + parents) * K * r * F
    chunks = max(1, math.ceil(aud * 1.5 / WALL))
    jobs = 2 + chunks
    return {"camp_h": camp/3600, "audit_h": aud/3600, "jobs": jobs, "start_h": jobs*START/3600,
            "total_h": (camp + aud + jobs*START)/3600, "audited": audited, "audit_chunks": chunks}
out = {}
for w in "AB":
    for s in (0.6, 0.8):
        for K in (6, 10):
            per = {n: node(r, s, K, w) for n, r in RUN.items()}
            out[f"W{w} s{s} K{K}"] = {"total_gpu_h": round(sum(v["total_h"] for v in per.values()), 1),
                                     "audited_per_node": round(per["mlab_cifar10"]["audited"]),
                                     "max_audit_chunks": max(v["audit_chunks"] for v in per.values())}
print(json.dumps(out, indent=1))
