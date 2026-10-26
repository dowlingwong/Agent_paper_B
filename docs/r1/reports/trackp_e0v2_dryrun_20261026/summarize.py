"""Collect the E0 v2 DRYRUN reports into one JSON and markdown tables. AI-assisted (Claude); CPU only.

Usage: python summarize.py <runs_dir> <out_dir>   (runs_dir = ~/r1_trackp/runs/p5_e0v2_dryrun)
Copies each run's report.json / manifest.json / curves next to the summary (evidence) and prints the tables.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

KEYS = ("rps", "width_slope_vs_label", "width_slope", "mean_slope", "width_ratio", "label_width_slope_vs_s",
        "label_mean_slope_vs_m", "rps_interp", "rps_extrap")


def row(name: str, stage: str, m: dict, extra: str = "") -> str:
    return (f"| {name} | {stage} | {m['rps']:.4f} | **{m['width_slope_vs_label']:.3f}** | {m['width_slope']:.3f} | "
            f"{m['mean_slope']:.3f} | {m['width_ratio']:.2f} | {extra} |")


def main(runs: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    summary: dict = {}
    lines = ["| run | stage | RPS | width slope vs label std | (v1: vs s) | mean slope | width ratio | steps |",
             "|---|---|---|---|---|---|---|---|"]
    for base in sorted(p for p in runs.iterdir() if p.is_dir() and not p.name.startswith("_")):
        summary[base.name] = {}
        for run in sorted(p for p in base.iterdir() if (p / "report.json").is_file()):
            rep = json.loads((run / "report.json").read_text())
            man = json.loads((run / "manifest.json").read_text())
            dst = out / base.name / run.name
            dst.mkdir(parents=True, exist_ok=True)
            for f in ("report.json", "manifest.json"):
                shutil.copy(run / f, dst / f)
            for f in ("head_fit/curve.jsonl", "lora/metrics.jsonl", "lora/best.json"):
                if (run / f).is_file():
                    (dst / f).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(run / f, dst / f)
            summary[base.name][run.name] = {"report": rep, "git": man["git"]["paper"], "lease": man["gpu_lease"]}
            if "lora" not in rep:
                continue
            name = f"{base.name} {run.name}"
            if "head_fit" in rep:
                h = rep["head_fit"]
                steps = (f"best {h['best_step']} / stop {h['stopped_at']}" if "best_step" in h
                         else f"L-BFGS {h['outer_iterations']} outer, converged {h['converged']}")
                lines.append(row(name, "head fit (frozen)", h["test"], steps))
            if "zero_shot" in rep:
                lines.append(row(name, "zero-shot (native)", rep["zero_shot"]["test"], "0"))
            lo = rep["lora"]
            lines.append(row(name, "+ LoRA", lo["test"], f"best {lo['best_step']} / stop {lo['stopped_at']}"))
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str))
    (out / "tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(Path(sys.argv[1]).expanduser(), Path(sys.argv[2]))
