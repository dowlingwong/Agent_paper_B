# Track P — TASL-7 host-equivalence check (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on TASL-7). **DRYRUN, not evidence.** Authority: PLAN §10 R1-TASL7-TRACKP; `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`, host-change header, migration step (3). The configuration and the tolerance were fixed in `tasl7_equivalence_20261026/PREDECLARATION.md` together with `compare.py`. Both were committed and pushed in `f3567e9` at 22:47:40 UTC, before the run started at 22:52 UTC.

**Result: equivalent.** All three pre-declared criteria hold.

## Configuration

This is the portal's E0 v2 DRYRUN run `kev-0.8b / fresh_soft_lr0.0001`: Kev-0.8B, a fresh LayerNorm + linear head, soft labels, adapter lr 1e-4, head lr 1e-3, seed 0. The head fit and the LoRA stage each have a cap of 2,000 steps, with evaluation every 100 steps, patience 5 and batch 8.

The run used paper `8e13e77` in a clean detached worktree, harness `897d83c`, and the same `trackp.py e0` arguments apart from `--run-dir`. Driver: `tasl7_equivalence_20261026/driver.sh`.

Manifest check against the portal run:

| Field | Same as the portal run? |
|---|---|
| `config_sha256` (`588869fa…`) | same |
| `data_manifest_sha256` | same |
| `base` (repos and revisions) | same |
| `environment` (torch 2.6.0+cu124, transformers 5.19.0, peft 0.21.2, kev/laya/startlux code pins) | same |
| seed, head form | same |
| Trained `adapter_model.safetensors` and `heads.safetensors` sha256 | differ, as expected: bf16 GPU training is not bit-reproducible |

The TASL-7 tree is clean (`dirty: false`). The portal manifests were marked dirty only because of an uncommitted review-file edit.

## Criteria

All values are from the `lora.test` block: held-out test cells, 1,000 prompts.

| Metric | Portal (TASL-2, driver 535) | TASL-7 (driver 580) | Difference | Tolerance | Pass |
|---|---|---|---|---|---|
| Width slope vs the label's own std | 0.92300 | 0.91348 | −0.0095 | \|Δ\| ≤ 0.05 | yes |
| Mean slope | 1.01156 | 1.01926 | +0.0077 | \|Δ\| ≤ 0.05 | yes |
| RPS | 1.9891e-4 | 1.9400e-4 | −2.5 % | ≤ 10 % relative | yes |

## Descriptive only (not judged)

| Item | Portal | TASL-7 |
|---|---|---|
| LoRA best step / stopped at | 1,700 / 2,000 | 1,800 / 2,000 |
| v1 width slope vs s | 0.862 | 0.854 |
| Width ratio | 1.083 | 1.093 |
| RPS interpolation / extrapolation cells | 5.41e-5 / 4.28e-4 | 6.34e-5 / 4.01e-4 |
| Head fit (frozen): RPS, width slope vs label, mean slope, best step | 0.0430, −0.0013, 0.122, 1,600 | 0.0428, −0.0013, 0.124, 1,600 |
| Label ceiling (width slope vs s, mean slope vs m) | 0.9254, 1.0291 | identical |
| Wall time under the lease | 24.5 min (10:57:51–11:22:23 UTC) | 25.4 min (22:52:16–23:17:42 UTC) |

The interpolation-cell RPS differs by 17 % relative. That is about 1e-5 in absolute terms, on the subset with the smallest errors. It was not a pre-declared criterion and is reported as is.

## Files

These are in `tasl7_equivalence_20261026/`:
- `run/report.json` and `run/manifest.json`.
- `run/lora/best.json`.
- `run/lora/metrics.jsonl.txt` and `run/head_fit/curve.jsonl.txt`: the curves, renamed because `*.jsonl` is git-ignored.
- `comparison.json`: the output of `compare.py`, exit 0.

The checkpoints and predictions stay under `/home/dowling/r1_trackp/runs/tasl7_equiv_20261026/`.

## Timeline (UTC, 26 Oct) and what was verified before the run

Added after review finding 1.
- **22:47:40–42** `PREDECLARATION.md` and `compare.py` were committed (`f3567e9`) and pushed. The pre-declaration's environment row says that the models are "re-verified against `r1/c3/train/registry.yaml`". At that moment this was not yet true: the Qwen-0.8B weights were still downloading.
- **22:49:21** The Qwen-0.8B weight file was complete. The downloader had checked each file of kev-0.8b and Qwen-0.8B against the Hub's own record at the pinned revision (LFS sha256 / git blob sha1).
- **≈ 22:52** Before the run, I re-hashed kev-0.8b and Qwen-0.8B (the only repos the run reads) against the **committed `registry.yaml`**: 12/12 and 12/12 files matched. That check was run interactively and its output was not saved; the only saved record is the full check below.
- **22:52:16–23:17:42** The equivalence run, under the lease.
- **≈ 23:3x** The saved check of all 8 repos (112 files) against the committed registry (`tasl7_phase2_20261026/verify_against_registry_output.txt`), after StartLux-4B finished. The reviewer re-hashed all files independently, with the same result.

The run's manifest has **no `host` field**, because code `8e13e77` predates `host_record()` (`d3bed8b`). The host is TASL-7: see the lease log entry (pid 4065542) and this report. `PREDECLARATION.md` is left unchanged.

## GPU use

One job, 25.4 leased minutes. Before the job: no Track X marker, no foreign compute process, the lock was free and `origin/main` STATUS showed no Track X B1/B2 running. The phase GPU total also includes the Phase 2 smoke test (22:50:48–22:51:39 UTC).
