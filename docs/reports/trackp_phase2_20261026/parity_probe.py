import sys, json, torch
sys.path.insert(0, "/home/dowling/r1_trackp/Agent_paper_B")
from pathlib import Path
from r1.c3.train import run as R
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers.models.qwen3_5.modeling_qwen3_5 as qm
sys.path.insert(0, "/home/dowling/r1_trackp/Agent_paper_B/r1/scripts")
from trackp_gpu_smoke import torch_path
M = "/home/dowling/r1_trackp/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41"
tok = AutoTokenizer.from_pretrained(M)
text = ("node digits_mlp; budget 4 of 20 used; incumbent lr=0.01, hidden=64; proposed edit: set hidden_units from 64 to 128. How much will the validation metric change? ") * 8
ids = torch.tensor([tok.encode(text)])
m = AutoModelForCausalLM.from_pretrained(M, dtype=torch.float32).eval()
with torch.no_grad(), torch_path(qm):
    cpu = m(ids).logits.float()
out = {"logit_abs_max": float(cpu.abs().max()), "logit_std": float(cpu.std())}
with R.gpu_lease("trackp phase2 parity probe", lock_path=Path.home()/"r1_locks/gpu0.lock", log_path=Path.home()/"r1_trackp/runs/gpu_lease_log.jsonl"):
    m = m.cuda(); g = ids.cuda()
    for tf32 in (False, True):
        torch.backends.cuda.matmul.allow_tf32 = tf32
        with torch.no_grad():
            fast = m(g).logits.float().cpu()
            with torch_path(qm):
                ref = m(g).logits.float().cpu()
        out[f"tf32={tf32}"] = {"fast_vs_cpu": float((fast-cpu).abs().max()), "torchgpu_vs_cpu": float((ref-cpu).abs().max()),
                              "fast_vs_torchgpu": float((fast-ref).abs().max())}
print(json.dumps(out, indent=1)); open(sys.argv[1], "w").write(json.dumps(out, indent=1))
