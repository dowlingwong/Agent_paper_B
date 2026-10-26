import torch, json
from r1.c3.train.model import build_model
from r1.c3.train import spike as S
cfg = json.load(open("r1/scripts/configs/trackp_portal.json"))
w = build_model("laya", cfg["bases"]["laya"]["local_path"]); w.eval()
rows = S.toy_rows(16, offset=100)
cap = {}
orig = w._core_forward
def spy(ids, att, mp, mm, qt):
    core = w.core
    enc = core.encoder(input_ids=ids, attention_mask=att).last_hidden_state
    m0 = att[..., None].float(); cap["enc_cls"] = enc[:, 0].float(); cap["enc_mean"] = (enc * m0).sum(1).float() / m0.sum(1)
    h = enc + core.type_emb(qt)[:, None, :]
    for layer in core.head.layers:
        h = layer(h, src_key_padding_mask=~att.bool())
    idx = mp[:, :, None].expand(-1, -1, h.size(-1)); cap["marker_mean"] = torch.gather(h, 1, idx).mean(1).float()
    cap["cls"] = h[:, 0].float(); m = att[..., None].float(); cap["mean"] = (h * m).sum(1).float() / m.sum(1)
    return orig(ids, att, mp, mm, qt)
w._core_forward = spy
with torch.no_grad():
    w([r["prompt"] for r in rows])
for k, v in cap.items():
    v = torch.nn.functional.layer_norm(v, v.shape[-1:]); print(k, "(after per-sample LayerNorm) norm", round(float(v.norm(dim=-1).mean()), 1), "between-prompt std / mean norm", round(float(v.std(0).norm() / v.norm(dim=-1).mean()), 4))
