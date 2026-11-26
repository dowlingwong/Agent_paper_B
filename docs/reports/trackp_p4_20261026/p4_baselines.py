"""Phase 4 baselines on the fixed 64-example toy batch: constant base-rate predictors; saved Laya action AUC."""
import json, sys, torch
from r1.c3.train import spike as S, losses as L
rows = S.toy_rows(64, offset=100)
y = torch.stack([r["y"] for r in rows]); u = torch.stack([r["u"] for r in rows])
p_base = y.mean(0, keepdim=True).expand_as(y)
belief_base = float(L.stage_s_loss(p_base, y))
# best constant action logit under the cost-weighted BCE: weighted fraction of u > 0
w = u.abs(); t = (u > 0).float(); q = float((w * t).sum() / w.sum())
logit = torch.full_like(u, torch.logit(torch.tensor(q)).item())
action_base = float(L.action_loss(logit, u))
out = {"belief_base_rate": belief_base, "action_best_constant": action_base, "action_weighted_positive_fraction": q}
if len(sys.argv) > 1:   # a saved Laya model: weighted AUC of its action probabilities
    from r1.c3.train.model import build_model
    cfg = json.load(open("r1/scripts/configs/trackp_portal.json"))
    m = build_model("laya", cfg["bases"]["laya"]["local_path"]); m.load(sys.argv[1]); m.eval()
    with torch.no_grad():
        a = torch.cat([m([r["prompt"] for r in rows[i:i + 8]])["action_logit"] for i in range(0, 64, 8)])
    pos, neg = (u > 0), (u <= 0)
    num = sum(float(w[i] * w[j]) * (1.0 if a[i] > a[j] else 0.5 if a[i] == a[j] else 0.0) for i in range(64) if pos[i] for j in range(64) if neg[j])
    den = sum(float(w[i] * w[j]) for i in range(64) if pos[i] for j in range(64) if neg[j])
    out["laya_action_weighted_auc"] = num / den
    out["laya_action_corr_with_u"] = float(torch.corrcoef(torch.stack([a.float(), u]))[0, 1])
print(json.dumps(out, indent=1))
