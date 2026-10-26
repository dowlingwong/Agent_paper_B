"""P.0 StartLux check: our transformers-5.19 bidirectional port vs StartLux's own transformers-5.8 code. ENGINEERING_ONLY; AI-assisted (Claude).

Two steps, two venvs, same GPU lease each:

* ``--ours`` (run venv, transformers 5.19): builds ``StartLuxWrapper`` on the real weights (fresh LoRA: B = 0, so the
  adapter is the identity), renders 20 prompts in StartLux's trained format, and writes their token ids and the
  wrapper's native 12 letter logits (softmax-12 readout) to ``--io``.
* ``--reference`` (venv ``trackp-sl58``, transformers 5.8.1): loads the same folder exactly as
  ``startlux_decide.backends.transformers`` does, ``bidirectional.enable(body)`` (StartLux's own module, with its
  three self-checks), ``text_forward`` on the same ids, letter logits = output embeddings at the last token; compares.

The vLLM-plugin path (StartLux's serving path) is not run: vLLM 0.31 / 0.19.1 is not installed on this host
(recorded in the P.0 report).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
N_PROMPTS = 20


def provenance(argv) -> dict:
    from r1.c3.train import run as R
    return {"git": R.git_commit(REPO), "argv": list(argv), "python": sys.executable, "utc": R.utcnow()}


def ours(model_dir: str, io: Path, dtype: str) -> None:
    sys.path.insert(0, str(REPO))
    import torch
    from r1.c3.train import exam_synthetic as E
    from r1.c3.train.model import build_model
    w = build_model("startlux", model_dir, dtype=getattr(torch, dtype), device="cuda")
    w.eval()
    items = [it for it in E.load() if it["split"] == "test"][:N_PROMPTS]
    prompts = [E.prompt_from_dict(it["prompt"]) for it in items]
    rows = []
    with torch.no_grad():
        for p in prompts:
            ids = w.tok.encode(w.prompt_text(p), add_special_tokens=False)
            logits = w([p])["belief_logits"][0].float().cpu().tolist()
            rows.append({"ids": ids, "ours": logits})
    io.write_text(json.dumps({"model_dir": model_dir, "dtype": dtype, "letter_ids": list(w.letter_ids),
                              "check_report": w.check_report, "rows": rows, "provenance": provenance(sys.argv)}))
    print(json.dumps({"written": str(io), "n": len(rows), "check_report": w.check_report}))


def reference(io: Path, out: Path) -> int:
    import torch
    import transformers
    from startlux_decide.backends import bidirectional
    data = json.loads(io.read_text())
    cfg = transformers.AutoConfig.from_pretrained(data["model_dir"])
    cls = getattr(transformers, cfg.architectures[0])
    model = cls.from_pretrained(data["model_dir"], dtype=getattr(torch, data["dtype"]), device_map={"": "cuda"}).eval()
    inner = model.model
    body = getattr(inner, "language_model", inner)
    check = bidirectional.enable(body)
    head = model.get_output_embeddings().weight
    letters = torch.tensor(data["letter_ids"], device="cuda")
    diffs, agree, causal = [], [], []
    with torch.no_grad():
        for r in data["rows"]:
            ids = torch.tensor([r["ids"]], device="cuda")
            h = bidirectional.text_forward(body, ids)[0, -1]
            ref = (head[letters] @ h).float().cpu()
            # control: the same read-out with the stock causal mask (what a mask error looks like)
            hc = bidirectional.text_forward(body, ids, causal=True)[0, -1]
            causal.append(float(((head[letters] @ hc).float().cpu() - ref).abs().max()))
            o = torch.tensor(r["ours"])
            diffs.append(float((ref - o).abs().max()))
            p_ref, p_o = torch.softmax(ref, -1), torch.softmax(o, -1)
            agree.append(float(0.5 * (p_ref - p_o).abs().sum()))
    rep = {"transformers": transformers.__version__, "torch": torch.__version__, "dtype": data["dtype"],
           "reference_check": check, "ours_check": data["check_report"], "n": len(diffs),
           "max_abs_logit_diff": max(diffs), "mean_abs_logit_diff_max": sum(diffs) / len(diffs),
           "max_tv_distance": max(agree), "vllm_path": "not run: vLLM is not installed on this host",
           "control_causal_vs_bidirectional_max": max(causal),
           "control_causal_vs_bidirectional_mean": sum(causal) / len(causal),
           "ours_provenance": data.get("provenance"), "reference_provenance": provenance(sys.argv)}
    out.write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", metavar="MODEL_DIR")
    ap.add_argument("--reference", action="store_true")
    ap.add_argument("--io", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--dtype", default="float32")
    args = ap.parse_args(argv)
    from r1.c3.train import run as R   # the GPU lease: Track X check, no foreign compute process, flock, logged
    step = "ours" if args.ours else "reference"
    with R.gpu_lease(f"trackp p0 startlux comparison {step} {args.io.name}"):
        if args.ours:
            ours(args.ours, args.io, args.dtype)
            return 0
        return reference(args.io, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
