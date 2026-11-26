import torch
from r1.c3.train import tiny, spike as S, losses as L
for form in ("softmax12", "cumulative11"):
    m = tiny.build_tiny("laya", "/tmp/claude-1008/trackp_tmp/lg", head_form=form)
    rows = S.toy_rows(4); y = torch.stack([r["y"] for r in rows])
    opt = torch.optim.Adam(list(m.trainable_parameters()), lr=3e-3); m.train(); ls = []
    for _ in range(80):
        p = L.softmax_probs(m([r["prompt"] for r in rows])["belief_logits"]); loss = L.soft_ce(p, y).mean()
        opt.zero_grad(); loss.backward(); opt.step(); ls.append(float(loss.detach()))
    print(form, torch.__version__, round(ls[0], 3), "->", round(ls[-1], 3), "pass", ls[-1] < ls[0] - 0.2 and ls[-1] < 3.0 and bool((p > 0).all()))
