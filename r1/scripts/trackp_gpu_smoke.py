"""Track P Phase 2.1 GPU smoke test (RUNBOOK Track P 2.1 "Done when"). ENGINEERING_ONLY; AI-assisted (Claude).

Under the GPU lease: (1) a bf16 matmul on the card checked against fp32; (2) one forward of the downloaded, verified
Qwen3.5-0.8B-Base (Gated DeltaNet hybrid) on the GPU with the kernels transformers binds (flash-linear-attention
for the gated delta rule, causal-conv1d for the short convolution), compared with the same forward on transformers'
pure-torch fallbacks (the module globals swapped for their ``__wrapped__`` torch functions), in fp32 and bf16.
Criterion for (2), calibrated (attempt 1 used an arbitrary 2e-3 that the measurement showed to be below TF32
precision): against a pure-fp32 CPU forward on the torch path, the fast path's max |logit diff| must be at most
``CAL_FACTOR`` x that of a known-correct reduced-precision GPU run of the torch path (TF32 matmuls for fp32; the bf16
model for bf16), floored at ``FLOOR``, and the next-token argmax must agree with the reference on >= 99 % of positions.
Writes a JSON report; exit 0 only if every check passes.

    python r1/scripts/trackp_gpu_smoke.py --model ~/r1_trackp/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41 --out x.json
"""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from r1.c3.train import run as R  # noqa: E402

KERNEL_NAMES = ("torch_chunk_gated_delta_rule", "torch_recurrent_gated_delta_rule", "causal_conv1d_fn",
                "causal_conv1d_update")
CAL_FACTOR, FLOOR, MIN_ARGMAX = 2.0, 1e-3, 0.99


@contextlib.contextmanager
def torch_path(mod):
    saved = {n: getattr(mod, n) for n in KERNEL_NAMES}
    try:
        for n, f in saved.items():
            setattr(mod, n, getattr(f, "__wrapped__", f))
        yield
    finally:
        for n, f in saved.items():
            setattr(mod, n, f)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lock", default=str(R.LOCK_PATH))
    ap.add_argument("--lease-log", default=str(R.LEASE_LOG))
    args = ap.parse_args(argv)
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import transformers.models.qwen3_5.modeling_qwen3_5 as qm
    rep = {"torch": torch.__version__, "cuda_runtime": torch.version.cuda, "transformers": transformers.__version__,
           "kernels_bound": {n: f"{getattr(qm, n).__module__}.{getattr(qm, n).__name__}" for n in KERNEL_NAMES},
           "checks": {}, "lease": []}
    try:
        import fla
        import causal_conv1d
        rep["fla"], rep["causal_conv1d"] = fla.__version__, causal_conv1d.__version__
    except Exception as exc:  # recorded; the comparison then shows the torch path on both sides
        rep["kernel_import_error"] = repr(exc)
    with R.gpu_lease("trackp phase2 gpu smoke", lock_path=Path(args.lock), log_path=Path(args.lease_log),
                     run_log=rep["lease"]):
        dev = torch.device("cuda")
        rep["device"] = torch.cuda.get_device_name(0)
        rep["capability"] = list(torch.cuda.get_device_capability(0))
        a = torch.randn(2048, 2048, device=dev)
        b = torch.randn(2048, 2048, device=dev)
        t0 = time.perf_counter()
        c16 = (a.bfloat16() @ b.bfloat16()).float()
        torch.cuda.synchronize()
        rel = float((c16 - a @ b).norm() / (a @ b).norm())
        rep["checks"]["bf16_matmul"] = {"rel_err_vs_fp32": rel, "ms": 1e3 * (time.perf_counter() - t0),
                                        "pass": rel < 1e-2}
        tok = AutoTokenizer.from_pretrained(args.model)
        text = ("node digits_mlp; budget 4 of 20 used; incumbent lr=0.01, hidden=64; proposed edit: set hidden_units "
                "from 64 to 128. How much will the validation metric change? ") * 8
        ids = torch.tensor([tok.encode(text)], device=dev)
        rep["seq_len"] = int(ids.shape[1])
        cpu_model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.float32).eval()
        with torch.no_grad(), torch_path(qm):
            ref_cpu = cpu_model(ids.cpu()).logits.float()
        del cpu_model
        rep["reference"] = {"what": "fp32 CPU forward, torch path", "logit_abs_max": float(ref_cpu.abs().max())}
        for dtype in ("float32", "bfloat16"):
            m = AutoModelForCausalLM.from_pretrained(args.model, dtype=getattr(torch, dtype)).to(dev).eval()
            with torch.no_grad():
                m(ids)  # warm-up: Triton compiles its kernels on the first call
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                t0 = time.perf_counter()
                fast = m(ids).logits.float().cpu()
                torch.cuda.synchronize()
                t_fast = time.perf_counter() - t0
                torch.backends.cuda.matmul.allow_tf32 = dtype == "float32"   # calibration run: reduced precision
                with torch_path(qm):
                    t0 = time.perf_counter()
                    cal = m(ids).logits.float().cpu()
                    torch.cuda.synchronize()
                    t_ref = time.perf_counter() - t0
                torch.backends.cuda.matmul.allow_tf32 = False
            d_fast = float((fast - ref_cpu).abs().max())
            d_cal = float((cal - ref_cpu).abs().max())
            tol = max(CAL_FACTOR * d_cal, FLOOR)
            agree = float((fast.argmax(-1) == ref_cpu.argmax(-1)).float().mean())
            ok = bool(torch.isfinite(fast).all()) and d_fast <= tol and agree >= MIN_ARGMAX
            rep["checks"][f"deltanet_forward_{dtype}"] = {
                "finite": bool(torch.isfinite(fast).all()), "fast_vs_ref": d_fast,
                "calibration_vs_ref": d_cal, "calibration": "torch path, TF32" if dtype == "float32" else
                "torch path, bf16", "tol": tol, "argmax_agreement_vs_ref": agree, "fast_s": t_fast,
                "torch_path_s": t_ref, "peak_mib": torch.cuda.max_memory_allocated() / 2**20, "pass": ok}
            del m
            torch.cuda.empty_cache()
    rep["pass"] = all(c["pass"] for c in rep["checks"].values())
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(rep, indent=1, sort_keys=True))
    print(json.dumps(rep, indent=1, sort_keys=True))
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
