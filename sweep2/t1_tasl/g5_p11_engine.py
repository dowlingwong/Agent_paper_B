"""Run the pinned G.5 engine with one sealed-off synthetic proposal source."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from pathlib import Path

from autoresearch.trackg import audit_g5 as A


class SyntheticChat:
    """Ten applied synthetic edits per campaign, followed by inert edits."""

    def __init__(self, data: dict, out: Path):
        self.budget = data["budget"]
        self.calls = 0
        self.state = 0
        self.restart = data["run_id"].endswith("-restart")
        self.out = out

    def __call__(self, payload):
        instance, step = divmod(self.calls, self.budget)
        if step == 0:
            self.state = 0
        if self.restart and self.calls == 0:
            (self.out / "restart-ready").touch(exist_ok=False)
            while not (self.out / "restart-continue").is_file():
                time.sleep(1)
        self.calls += 1
        if step < 10:
            value = 32 * (instance + 1) + step
            new_line = f"OFFSET = {value}"
        else:
            value = self.state
            new_line = f"OFFSET = {value}  # inert"
        diff = f"--- a/train.py\n+++ b/train.py\n@@ -3,3 +3,3 @@\n \n-OFFSET = {self.state}\n+{new_line}\n \n"
        self.state = value
        return json.dumps({"rationale": "P11 synthetic", "summary": "change integer offset",
                           "objective": "synthetic CUDA checksum", "diff": diff}), {
            "prompt_tokens": 128, "completion_tokens": 64,
        }


def infrastructure_runner(*args, **kwargs):
    runner = A.WorkingCopyRunner(*args, **kwargs)
    run = runner.run

    def fail_first_pair(run_id, *args, **kwargs):
        if run_id.startswith("u000_s7001_"):
            raise A.RunnerError("P11 synthetic host failure before worker start")
        return run(run_id, *args, **kwargs)

    runner.run = fail_first_pair
    return runner


def metrics(out: Path) -> dict:
    rows = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
    good = [r for r in rows if r["kind"] == "ok"]
    if any(not math.isfinite(r["outcome"]["value"]) for r in good):
        raise ValueError("non-finite synthetic audit value")
    return {(r["unit"], r["seed"]): r["outcome"]["value"] for r in good}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("campaign", "audit"))
    inputs = p.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--campaign", type=Path)
    inputs.add_argument("--chunk", type=Path)
    p.add_argument("--harness-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--gpu-uuid", required=True)
    a = p.parse_args()
    infile = a.campaign if a.mode == "campaign" else a.chunk
    if infile is None:
        p.error("input does not match the engine command")
    data = json.loads(infile.read_bytes())
    run_id = data["run_id"]
    if not re.fullmatch(r"g5-p11-[0-9]{8}T[0-9]{6}Z(?:-[a-z0-9]+)?", run_id):
        p.error("P11 requires a synthetic run ID")
    base = Path.home() / "r1_engineering" / "g5-p11"
    if a.harness_root.resolve() != base / "kit" / run_id or base / "runs" / run_id not in a.out.resolve().parents:
        p.error("P11 engine inputs and outputs must use the engineering root")
    if a.mode == "audit" and run_id.endswith("-lease") and os.uname().nodename == "TASL-7":
        (a.out.parent / "lease-ready").touch(exist_ok=False)
        while not (a.out.parent / "lease-continue").is_file():
            time.sleep(1)
    gpu_uuids = A.resolve_gpus(data["node"], a.gpu_uuid, os.environ)
    kwargs = {"gpu_uuids": gpu_uuids, "cpu_list": tuple(sorted(os.sched_getaffinity(0)))}
    if a.mode == "campaign":
        rec = A.run_campaign(A.validate_campaign(data), a.harness_root, a.out,
                             chat=SyntheticChat(data, a.out), **kwargs)
    else:
        if run_id.endswith("-infra"):
            kwargs["runner_factory"] = infrastructure_runner
        rec = A.run_audit(A.validate_chunk(data), a.harness_root, a.out, **kwargs)
        if rec["stop"] is None and run_id.endswith("-determinism"):
            # Repeat the same claims using the real engine and isolation gate. Only synthetic values are compared.
            repeat = a.out.parent / "audit-repeat"
            replay = A.run_audit(data, a.harness_root, repeat, **kwargs)
            original, repeated = metrics(a.out), metrics(repeat)
            if replay["stop"] or original != repeated or len(original) != len(data["runs"]):
                raise ValueError("P11 synthetic fixed-seed replays differ or did not complete")
            (a.out / "determinism.json").write_text(json.dumps({
                "label": "ENGINEERING_ONLY", "same_fixed_seed_outcomes": len(original),
            }) + "\n")
    (a.out / "p11-unread.bin").write_bytes(b"\xff\x00P11\x00\x80")
    if run_id.endswith("-tar"):
        # An existing directory makes the actual tar command fail without exhausting shared disk.
        (a.out.parent.parent / "out.tar").mkdir(exist_ok=False)
    return 0 if rec["stop"] is None else 3


if __name__ == "__main__":
    raise SystemExit(main())
