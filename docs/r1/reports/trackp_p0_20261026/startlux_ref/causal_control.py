"""Control: StartLux's reference with the stock causal mask vs its bidirectional read-out (transformers 5.8)."""
import json, sys, torch, transformers
from startlux_decide.backends import bidirectional
io = json.load(open(sys.argv[1]))
cfg = transformers.AutoConfig.from_pretrained(io["model_dir"])
m = getattr(transformers, cfg.architectures[0]).from_pretrained(io["model_dir"], dtype=torch.bfloat16, device_map={"": "cuda"}).eval()
body = getattr(m.model, "language_model", m.model); bidirectional.enable(body)
head = m.get_output_embeddings().weight; letters = torch.tensor(io["letter_ids"], device="cuda")
d = []
with torch.no_grad():
    for r in io["rows"]:
        ids = torch.tensor([r["ids"]], device="cuda")
        bi = (head[letters] @ bidirectional.text_forward(body, ids)[0, -1]).float()
        ca = (head[letters] @ bidirectional.text_forward(body, ids, causal=True)[0, -1]).float()
        d.append(float((bi - ca).abs().max()))
out = {"causal_vs_bidirectional_max_abs_logit_diff": max(d), "mean": sum(d) / len(d)}
print(json.dumps(out)); json.dump(out, open(sys.argv[2], "w"))
