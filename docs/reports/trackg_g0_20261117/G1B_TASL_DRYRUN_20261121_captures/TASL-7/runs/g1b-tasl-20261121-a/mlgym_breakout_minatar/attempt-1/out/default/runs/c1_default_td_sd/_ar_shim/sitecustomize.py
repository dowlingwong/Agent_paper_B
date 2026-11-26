# Written by autoresearch.trackg.determinism; applied at interpreter start.
# The settings are applied in every Python interpreter of the run (including
# spawned data-loader workers); the record is written by the first one only.
def _ar_trackg_determinism():
    import json, os
    path = os.environ.get("AR_DETERMINISM_RECORD")
    warn_only = os.environ.get("AR_DETERMINISTIC_WARN_ONLY", "0") == "1"
    rec = {"schema": "trackg_determinism/v1", "settings": [], "warn_only": warn_only}
    def note(setting, status, reason=""):
        rec["settings"].append({"setting": setting, "status": status, "reason": reason})
    try:
        import torch
    except Exception as error:  # torch absent: record, never fail the run
        for s in ("cudnn.benchmark=False", "torch.use_deterministic_algorithms(True)",
                  "torch.set_num_threads"):
            note(s, "not_forced", "torch_absent: %s" % type(error).__name__)
    else:
        rec["torch_version"] = getattr(torch, "__version__", None)
        try:
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
            note("cudnn.benchmark=False", "forced")
        except Exception as error:
            note("cudnn.benchmark=False", "not_forced", repr(error))
        try:
            if warn_only:
                torch.use_deterministic_algorithms(True, warn_only=True)
                note("torch.use_deterministic_algorithms(True)", "forced", "warn_only=True")
            else:
                torch.use_deterministic_algorithms(True)
                note("torch.use_deterministic_algorithms(True)", "forced")
        except Exception as error:
            note("torch.use_deterministic_algorithms(True)", "not_forced", repr(error))
        try:
            n = int(os.environ.get("AR_NUM_THREADS", "0"))
            if n > 0:
                torch.set_num_threads(n)
                note("torch.set_num_threads", "forced", str(n))
            else:
                note("torch.set_num_threads", "not_forced", "AR_NUM_THREADS unset")
        except Exception as error:
            note("torch.set_num_threads", "not_forced", repr(error))
    if not path or os.path.exists(path):
        return
    try:
        with open(path, "x", encoding="utf-8") as handle:
            json.dump(rec, handle, sort_keys=True)
    except Exception:
        pass
try:
    _ar_trackg_determinism()
except Exception:
    pass
del _ar_trackg_determinism
