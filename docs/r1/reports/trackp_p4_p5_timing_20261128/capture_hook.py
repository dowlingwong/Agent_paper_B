import atexit, json, os, sys, time
_T0 = time.time()
_OUT = os.environ.get("KERNEL_CAPTURE_OUT")
_NAMES = ("torch_chunk_gated_delta_rule", "torch_recurrent_gated_delta_rule", "causal_conv1d_fn", "causal_conv1d_update")

def _bound(wrapper):
    for cell in getattr(wrapper, "__closure__", None) or ():
        f = cell.cell_contents
        if callable(f) and getattr(f, "__name__", "") and f is not getattr(wrapper, "__wrapped__", None) \
                and not getattr(f, "__module__", "").startswith("transformers"):
            return f"{f.__module__}.{f.__name__}"
    inner = getattr(wrapper, "__wrapped__", wrapper)
    return f"{inner.__module__}.{inner.__name__} (torch path)"

def _dump():
    if not _OUT:
        return
    rec = {"started_unix": _T0, "finished_unix": time.time(), "wall_s": round(time.time() - _T0, 3)}
    try:
        import torch
        rec["torch"] = torch.__version__
        rec["cuda_runtime"] = torch.version.cuda
        rec["device_name"] = torch.cuda.get_device_name(0)
        rec["capability"] = list(torch.cuda.get_device_capability(0))
        rec["device_uuid"] = str(torch.cuda.get_device_properties(0).uuid)
        rec["peak_allocated_mib"] = round(torch.cuda.max_memory_allocated() / 2**20, 3)
        rec["peak_reserved_mib"] = round(torch.cuda.max_memory_reserved() / 2**20, 3)
    except Exception as exc:
        rec["torch_error"] = repr(exc)
    try:
        import transformers
        rec["transformers"] = transformers.__version__
        qm = sys.modules.get("transformers.models.qwen3_5.modeling_qwen3_5")
        if qm is None:
            import transformers.models.qwen3_5.modeling_qwen3_5 as qm
        rec["kernels_bound"] = {n: _bound(getattr(qm, n)) for n in _NAMES}
    except Exception as exc:
        rec["kernel_error"] = repr(exc)
    try:
        with open(_OUT + ".tmp", "w") as fh:
            json.dump(rec, fh, indent=1, sort_keys=True)
        os.replace(_OUT + ".tmp", _OUT)
    except Exception:
        pass
atexit.register(_dump)
