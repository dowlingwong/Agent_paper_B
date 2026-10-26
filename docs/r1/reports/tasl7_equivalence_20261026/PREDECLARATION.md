# TASL-7 host-equivalence check — pre-declaration (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on TASL-7). DRYRUN, not evidence. Authority: PLAN §10 R1-TASL7-TRACKP; `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`, host-change header, migration step (3). **This file is committed and pushed before the TASL-7 run starts and before any comparison is made.**

## Configuration reproduced

One configuration from the portal's E0 v2 DRYRUN (`docs/r1/reports/TRACKP_E0V2_DRYRUN_20261026.md`): the run the DRYRUN selected for Kev-0.8B.

| Item | Value |
|---|---|
| Portal run | `trackp_e0v2_dryrun_20261026/runs/kev-0.8b/fresh_soft_lr0.0001/` (`report.json`, `manifest.json`) |
| Base | `kev-0.8b` (Qwen/Qwen3.5-0.8B-Base @ `dc7cdfe2ee41`, jaredpalmer/kev-0.8b @ `788ddbdd6571`) |
| Variant | fresh LayerNorm + linear head, soft labels (`y_soft`) |
| Adapter lr / head lr | 1e-4 / 1e-3 |
| Seed | 0 |
| Step budget | head fit and LoRA each ≤ 2,000 steps, eval every 100, patience 5, batch 8 |
| Code | paper `8e13e77` (detached worktree), harness `897d83c`; config bytes identical (`config_sha256` `588869fa…`, same paths under `/home/dowling/r1_trackp`) |
| Environment | venv rebuilt from `pip_freeze_trackp-gpu.txt` (torch 2.6.0+cu124); models re-verified against `r1/c3/train/registry.yaml` |
| Command | `trackp.py e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --run-dir <runs>/tasl7_equiv_20261026/kev-0.8b/fresh_soft_lr0.0001` |

Why this configuration: the header asks for "same base, lr, seed, step budget"; this is the selected (lowest val RPS) run of the base that every later DRYRUN step used, and it exercises the head fit, LoRA training with gradient checkpointing, the DeltaNet kernels and the held-out-cell metrics in one ~25-minute job. The current branch's two-stage driver (`471f93f`) is not used, because no portal run of it exists to compare with.

## Tolerance (fixed now, the header's default)

Metrics are the `lora.test` block of `report.json` (held-out test cells, 1,000 prompts). Portal reference values:

| Metric | Field | Portal value | Tolerance |
|---|---|---|---|
| Width slope vs the label's own std (primary, R1-E0-PROTOCOL) | `lora.test.width_slope_vs_label` | 0.922998 | \|Δ\| ≤ 0.05 |
| Mean slope | `lora.test.mean_slope` | 1.011556 | \|Δ\| ≤ 0.05 |
| RPS | `lora.test.rps` | 1.98913e-4 | \|Δ\| / portal ≤ 10 % |

All three must hold for "equivalent". A miss on any is a **STOP for the author**; no re-run to obtain a pass, no other configuration substituted. Reported descriptively, not judged: the head-fit block, the v1 width slope vs s, width ratio, interpolation/extrapolation RPS, best/stopped step, wall time, peak behaviour. The comparison is computed by `compare.py` in this directory (committed with this file).
