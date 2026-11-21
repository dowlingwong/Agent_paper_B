"""R1-T1-HOST-H200 host facts + §3 conditions that need no sandbox: non-root, timeout factor 3.

Writes one JSON. The runner/isolation imports are used only for the timeout-factor and ptrace probes; a failure
to import is recorded, not raised.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

import lib_iso


def timeout_factor_check(repo: str) -> dict:
    out: dict = {"repo": repo}
    try:
        sys.path.insert(0, os.path.join(repo, "src"))
        from autoresearch.trackg.runner import ResourceLimits, RunnerError  # noqa: E402
        from autoresearch.trackg import isolation  # noqa: E402

        lim = ResourceLimits(uncapped_reason="host check: no CPU/memory cap needed for the condition probe",
                             measured_run_seconds=10.0)
        timeout, basis = lim.timeout()
        out.update({
            "default_timeout_factor": lim.timeout_factor,
            "timeout_seconds_at_measured_10s": timeout,
            "timeout_basis": basis,
            "factor_is_three": lim.timeout_factor == 3.0,
            "enforced_timeout_is_3x": abs(timeout - 30.0) < 1e-9,
            "ptrace_scope_via_unit": isolation.ptrace_scope(),
            "limits_text_first_lines": isolation.limits_text()[:4],
        })
        refused = None
        try:
            ResourceLimits(uncapped_reason="probe", measured_run_seconds=10.0, timeout_factor=2.0)
        except RunnerError as error:
            refused = str(error)
        except Exception as error:  # noqa: BLE001
            refused = f"unexpected {type(error).__name__}: {error}"
        out["factor_two_refused"] = refused is not None
        out["factor_two_refusal_message"] = refused
        out["ok"] = bool(out["factor_is_three"] and out["enforced_timeout_is_3x"] and refused)
        return out
    except Exception:  # noqa: BLE001
        out["ok"] = False
        out["error"] = traceback.format_exc()
        return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="harness repo whose accepted core is read for the checks")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    facts = lib_iso.host_facts()
    facts["timeout_factor_check"] = timeout_factor_check(args.repo)
    facts["conditions_without_sandbox"] = {
        "C2_not_root": {"euid": os.geteuid(), "pass": os.geteuid() != 0},
        "C5_timeout_factor_three": {"pass": bool(facts["timeout_factor_check"].get("ok"))},
    }
    lib_iso.write_json(args.out, facts)
    print(json.dumps({"out": args.out, "euid": os.geteuid(),
                      "ptrace_scope": facts["sysctls"]["kernel.yama.ptrace_scope"]["value"],
                      "timeout_factor_ok": facts["timeout_factor_check"].get("ok")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
