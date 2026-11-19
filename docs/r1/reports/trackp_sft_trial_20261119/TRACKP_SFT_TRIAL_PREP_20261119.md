# Track P SFT trial on TASL-2 — prepared and RUN, 19 Nov 2026

**Status: RAN — PASS as an ENGINEERING trial (rc 0, 159 s), with one recorded host-setting deviation
(`sft.micro_batch` 8 → 4 after a CUDA OOM at the default).** No evidence, no selection, no tuning; the
7006–7010 evaluation block was never read. Authority: PLAN `R1-TRACKP-SFT-DEV` and `R1-TRACKP-SFT-DUP`
(both `main`, author 17 Nov 2026), with `docs/r1/reports/TRACKP_SFT_DEV_20261117.md`,
`docs/r1/reports/TRACKP_SFT_DUP_20261117.md` and `docs/r1/reviews/TRACKP_SFT_DUP_REVIEW_20261117.md`
(ACCEPTED, round 2, reviewed code tip `1f9e8232`). `R1-TRACKP-TASL2-HOST` permits TASL-2; target host TASL-2
only (TASL-7 not used). No deletion, no force push, no HTCondor/deepthought use, no commit/push.
AI-assisted (Claude). Nothing here is evidence.

Record path: `docs/r1/reports/trackp_sft_trial_20261119/` (this report, `captures/`, `scripts/`,
`SHA256SUMS`; uncommitted, in the `ops-tasl-20261116` worktree). Raw captures also on TASL-2 under
`/home/dowling/r1_engineering/sft_trial_20261119/captures/`.

## 1. What ran (exact commands, TASL-2, 19 Nov 2026 UTC)

Common environment: `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1`,
`AR_HARNESS_ROOT=/home/dowling/r1_engineering/sft_trial_20261119/harness_6adf3859`,
`PYTHONPATH=/home/dowling/r1_engineering/sft_trial_20261119/code_de3de54f`, venv
`/home/dowling/r1_trackp/venvs/trackp-gpu`. CPU commands keep CUDA visible (see §6).

**(a) Data build — rc 0, wall 28 s, 00:33:24Z–00:33:52Z.**
```
python r1/scripts/trackp.py sft-data \
  --table /home/dowling/r1_engineering/sft_trial_20261119/inputs/c3_features_v3_20261115T232007Z \
  --sweep /home/dowling/r1_engineering/sft_trial_20261119/code_de3de54f/results/r1/pilot/C3_sweep_index_20261028T033315Z.json \
  --paper-root /home/dowling/r1_engineering/sft_trial_20261119/code_de3de54f \
  --classification /home/dowling/r1_engineering/sft_trial_20261119/code_de3de54f/results/r1/evidence/C3_sweep_classification_20261028.json \
  --labels synthetic \
  --run-dir /home/dowling/r1_trackp/runs/sft_data/sweep1_v3_synthetic
```
Output: `…/sweep1_v3_synthetic/{report.json,manifest.json,data/{rows.jsonl,sft_data.json,splits.json}}`;
`sft_data_sha256` **403938500f…**, peak RSS 1,491,980 KB (1.42 GiB), 7,984 FS output blocks.
Counts reproduce the decision's sizes exactly (`sft_data.json.counts`): table rows 4,999 / labelled 1,725 /
**train 1,176** / **primary val 47** / **val_seen 240** / val_full 287 / labelled test 262 / test rows seen on
train or val 188 / **primary labelled test 74**; `val_dropped_seen_in_train = 0`. `splits.json` records
`cross_split_duplicates: heldout_excludes_seen` at **both** `config.cross_split_duplicates` and the top level,
with `heldout_populations` (primary/secondary), the 674-id exclusion list, and `labels.kind = synthetic`
("synthetic labels for dry runs; not audit data", seed 0).

**(b) Trial attempt 1 — the DEV report's default command — CUDA OOM (rc 1, 25 s, 00:34:25Z–00:34:50Z).**
```
python r1/scripts/trackp.py sft-dev \
  --data /home/dowling/r1_trackp/runs/sft_data/sweep1_v3_synthetic/data \
  --base kev-0.8b --lr 3e-5 --seed 0 \
  --run-dir /home/dowling/r1_trackp/runs/sft_dev/kev-0.8b_lr3e-5_s0
```
The default host config leaves `sft.micro_batch` unset, so the protocol default 8 was used; the run wrote the
step-0 evaluation and then failed on the first training forward:
`torch.OutOfMemoryError: Tried to allocate 164.00 MiB. GPU 0 has 23.62 GiB total, 132.06 MiB free; … this
process has 23.14 GiB in use` (peak sampled 24,051 MiB of 24,564 MiB). The partial run directory was **moved
aside, not deleted**: `…/sft_dev/kev-0.8b_lr3e-5_s0.partial_oom_micro8_20261119T0034Z` (step-0 eval
`val_rps 0.074614`, `best.json`, 44 MB ckpt + 44 MB best, preserved). The GPU lease was taken and released
cleanly (00:34:28Z / 00:34:49Z).

**(c) Trial attempt 2 — host config copy with `sft.micro_batch: 4` — rc 0, wall 159 s, 00:36:05Z–00:38:44Z.**
```
python r1/scripts/trackp.py --config /home/dowling/r1_engineering/sft_trial_20261119/inputs/trackp_portal_sft_micro4_20261119.json \
  sft-dev --data /home/dowling/r1_trackp/runs/sft_data/sweep1_v3_synthetic/data \
  --base kev-0.8b --lr 3e-5 --seed 0 \
  --run-dir /home/dowling/r1_trackp/runs/sft_dev/kev-0.8b_lr3e-5_s0
```
The copied config is byte-identical to `r1/scripts/configs/trackp_portal.json` except
`"sft": {…, "micro_batch": 4}` (original sha `049bafed…`, copy sha `00846240…`; manifest `config_sha256`
`4d166ba2…`); effective batch stays 16 (accumulation 4 instead of 2), so the protocol is unchanged and the run
records `protocol.micro_batch = 4`, no `protocol_deviation`. This is the host knob the DEV report's open point 5
anticipates ("set as `sft.micro_batch` in the host config"); the repository config was not modified (worktree
clean). Peak GPU 16,511 MiB (of 24,564), 100 % util, 70 °C; host RSS 2,521,456 KB (2.4 GiB).

**Trial result (ENGINEERING_ONLY; all values are readiness numbers, not evidence).** `report.json`
(schema `trackp_sft_report/v1`) and `stage_s/sft_report.json` record:

| field | value |
|---|---|
| `evidence_label` (manifest) | `ENGINEERING_ONLY` |
| `cross_split_duplicates` / `heldout_rule` | `heldout_excludes_seen` / "R1-TRACKP-SFT-DUP: primary = val without training duplicates (early stopping, temperature, selection); secondary = full val (reported only)" |
| `n_train` / `n_val` / `n_val_secondary_only` | 1,176 / 47 / 240 |
| `steps_per_epoch` / `total_steps` | 74 / 370 |
| `train` | best_step 90, best val RPS 0.0470981, early_stopped at 126, `completed: true` |
| `temperature` | 0.740567 (fitted on primary val) |
| `selected` (primary val) | RPS 0.047098, skill 0.007663, NLL 2.09133, ECE(all bins) 0.006391, ECE(top-1) 0.043625, width ratio 2.5047 |
| `selected_temperature_scaled` | RPS 0.047125, NLL 2.08128, ECE(all) 0.002536, ECE(top-1) 0.020095 |
| `selected_full_heldout` (secondary) | full-val RPS 0.040721, skill −0.008687, NLL 2.10660, ECE(all) 0.006231 |
| `selected_full_heldout_temperature_scaled` | full-val RPS 0.040843, NLL 2.09914, ECE(all) 0.000708 |

So the decided rule is live end-to-end: primary val (47 rows) drives early stopping, temperature and the
selected metrics, while the full held-out population (287 rows) is written as a **report-only** secondary
metric. `stage_s/pred_val_logits.npy` + `pred_val_seen_logits.npy`, `stage_s/best/{adapter/,heads.safetensors,
manifest.json,temperature.json}` and `metrics.jsonl` (135 lines, incl. the step-0 evaluation) are present; run
directory 174 MB.

**Run identity:** `manifest.json` `created_utc 2026-11-19T00:38:44Z`, `data_manifest_sha256 29c83995…`,
`git.paper {de3de54f…, clean}`, `git.harness {6adf3859…, clean}`, `host.device` = RTX 4090 UUID
`GPU-4d623e76-…` on TASL-2, `gpu_lease` start 00:36:08Z / end 00:38:44Z, `argv` as above.
Key hashes: `report.json` `7c5ec34a…`, `manifest.json` `f7b338c1…`, `stage_s/sft_report.json` `6695aaa1…`,
`stage_s/metrics.jsonl` `bfa48497…`, `stage_s/best/manifest.json` `4ebba22a…`, `best/temperature.json`
`44a4b3fa…`, `best/adapter/adapter_model.safetensors` `d7856faa…`.

## 2. The missing data input was resolved: the pinned table is published

The trial could not have run until the pinned sweep-1 `c3_features/v3` table was on TASL-2. It was found in the
**W2 v3 rebuild unit's committed run record** (branch `origin/w2-3-rebuild-unit-20261115`, commit
`2989f383`, "self-contained evidence (proposals.jsonl/configs.json copied; SHA256SUMS verifies 4/4)"):
`docs/r1/reports/w2_3_rebuild_20261115/run_20261115T232007Z/` on the Mac. The two pinned data files were copied
to TASL-2 (`inputs/c3_features_v3_20261115T232007Z/`, with `build.json`, `manifest.json`, `SHA256SUMS`,
`build.stdout`) and verified: **`proposals.jsonl` = `d0048567a4bedb…`**, **`configs.json` = `b585b72758668a…`**
— exactly the pins in `trackp_sft.json` — and `build.json` = `7f56619c…`, the `build_json_sha256_on_deepthought`
recorded in the config; the table manifest records `code_commit d8aa9561`, `featurizer c3_features/v3`,
`prompt trackp_prompt/v2`, `label EVIDENCE`, 4,999 proposals, harness `6adf3859`, and `SHA256SUMS` verifies 4/4.
This is the DEV report's sanctioned route ("elsewhere copy it (the pins check the bytes)"); no deepthought use.
The earlier STOP therefore no longer applies.

## 3. TASL-2 state (before the run, 19 Nov 2026 01:22–01:28 CET)

| item | value |
|---|---|
| host | `TASL-2`, Linux 6.8.0-149-generic, x86_64 |
| GPU | NVIDIA GeForce RTX 4090, UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, PCI `00000000:01:00.0`, 24,564 MiB total, **353 MiB used / 23,830 MiB free**, 0 % util, 37 °C, 13.9 W, driver 535.309.01, compute 8.9 |
| GPU compute apps | none (only root `Xorg` + `gnome-shell` display) |
| co-tenancy | `who`/`w` empty (0 logged-in users); load 0.35; 62 GB RAM, 60.2 GB available; `/` 1.9 T with 372 G free. No other user's GPU/CPU job seen before or during the run. |
| cgroup | session scope under `user.slice/user-1008.slice`; `MemoryMax=infinity`, `MemoryHigh=infinity`, no CPU quota — no per-user memory cap beyond the 62 GB host RAM (the run used 2.1 GB host RSS) |
| GPU lease | `/home/dowling/r1_locks/gpu0.lock` present; free before, during (held by our run only) and after; lease log 193 → 197 lines, sha `edc8247b…` → `a0433998…` (two start/end pairs, the OOM attempt and the successful run) |

## 4. Code, environment and policy verification (all PASS)

- **Run checkout** `code_de3de54f`: detached clean worktree at published main
  `de3de54fd22dcdd86215be0924307e36a64ed08b` (fetched from GitHub on TASL-2 this session). The reviewed SFT
  code is byte-identical here to the reviewed tip `1f9e8232` (`trackp.py`, `sft_data.py`, `sft.py`,
  `serialize.py`, `tiny.py`, `trackp_sft.json` all `IDENTICAL`; `git diff 1f9e8232 de3de54f -- r1/` = only the
  later B.2 package markers/regression test, 3 files). The data build requires a checkout at *current
  published main*: the evidence-classification guard (`_verify_published`) STOPs a reviewed-tip-only checkout
  with `published origin/main differs from evidence authority: docs/r1/PLAN.md` — captured.
- **Reviewed-tip checkout** `code_1f9e8232`: detached clean worktree at `1f9e8232` (the review's
  `Code-Commit:`), kept as the reviewed reference tree.
- **Harness** `harness_6adf3859`: clean detached clone at `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, the pin
  recorded by the sweep-1 index/manifests; it is what the run manifest records (clean). The TASL-2 harness
  clones at `897d83c` do not contain this commit and were left untouched.
- **Venv** Python 3.12.15, torch 2.6.0+cu124, transformers 5.19.0, peft 0.21.2, CUDA available; `uv pip freeze`
  is **byte-identical** to the committed freeze (`pip_freeze_trackp-gpu.txt`: 121 sorted lines, both sha
  `50238e5a…`, diff empty).
- `--check-config` on the portal config: `placeholders: []`, digest `64073cea…`; `R.check_environment` (torch +
  kev/laya/startlux pins): **OK, no STOP**.
- Pool tokenizers: 6/6 load offline (qwen3.5-0.8b/4b-base, laya, startlux 0.8b/2b/4b) from the TASL-2 HF cache.
  Base/adapter present: `Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41` (1.7 GB) + `jaredpalmer__kev-0.8b@788ddbdd6571`.
- SFT suite on TASL-2: `r1/tests/test_trackp_sft.py` **35 passed, 0 failed** (matches the unit's 35).

## 5. Findings (recorded, none blocked the trial)

1. **Default micro-batch 8 does not fit the 24 GB 4090 for kev-0.8b on this data.** The SFT path (`_stage_s`)
   does not enable gradient checkpointing (`_stage_s` never calls `model.enable_gradient_checkpointing()`,
   although the portal config sets `gpu.gradient_checkpointing: true`; only the e0 commands apply it). At
   micro-batch 8 the first training forward OOMs (23.14 GiB in use); micro-batch 4 completes at a 16,511 MiB
   peak with the effective batch unchanged at 16. This is a host-fit operating point the DEV report's open
   point 5 anticipates; it is recorded here as a **host-config deviation**, not a protocol change. Enabling
   gradient checkpointing in the SFT path (likely fitting micro-batch 8) would be a code change and was not
   made.
2. **transformers 5.19.0 + hidden CUDA:** with `CUDA_VISIBLE_DEVICES=""`, `from transformers import
   AutoTokenizer` fails ("Cannot access accelerator device when none is available"); 5 CPU-`--tiny` tests in
   `test_trackp_cli.py` fail on TASL-2 for this reason (the suite was verified with transformers 4.49 on the
   Mac). Real-base runs keep CUDA visible and are unaffected; CPU data builds must also keep it visible.
3. **`--config` is a top-level option and must precede the subcommand**; `sft-dev --config …` is an argparse
   error (rc 2). One intermediate invocation was wasted on this (no run directory created).
4. **Minor reporting gap:** the run `manifest.json` has an empty `model_files_sha256` because `_stage_s` reads
   `stage_s/best/record.json`, which the trainer does not write; the model files and their hashes are recorded
   in `stage_s/best/manifest.json` (adapter README/config/model + heads, four hashes) — cited above.
5. **Minor robustness gap:** `sft-dev` on a *missing* data directory raises an uncaught `FileNotFoundError`
   traceback (rc 1) instead of a clean `STOP:` (rc 2). Not reached with a valid data directory.

## 6. Outputs and where they live

On TASL-2 (new; nothing deleted):
- `/home/dowling/r1_engineering/sft_trial_20261119/` — `code_1f9e8232/`, `code_de3de54f/`,
  `harness_6adf3859/`, `inputs/` (the verified table + the micro-4 host-config copy), `captures/`, `tmp/`,
  `scripts/` (482 MB before the run).
- `/home/dowling/r1_trackp/runs/sft_data/sweep1_v3_synthetic/` — data build outputs (4 MB).
- `/home/dowling/r1_trackp/runs/sft_dev/kev-0.8b_lr3e-5_s0/` — the successful trial run (174 MB).
- `/home/dowling/r1_trackp/runs/sft_dev/kev-0.8b_lr3e-5_s0.partial_oom_micro8_20261119T0034Z/` — the preserved
  partial OOM run (moved aside, not deleted).
On this record: `captures/` (all raw captures incl. the full `report.json`/`manifest.json`, GPU sampling CSV,
OOM log, data dir manifests, command/env record) and `scripts/gpu_sampler.sh`; `SHA256SUMS` verifies them.

## 7. Side effects / non-actions

- `git fetch origin main` on the TASL-2 clone moved `refs/remotes/origin/main` `26177d82…` → `de3de54f…`
  (and wrote `FETCH_HEAD`) — the same side effect the 17 Nov rehearsal recorded; no push.
- New worktrees/clone/dirs under `/home/dowling/r1_engineering/sft_trial_20261119/`; the table and the
  micro-4 host-config copy under `inputs/`; new data and run directories under `/home/dowling/r1_trackp/runs/`;
  partial OOM run moved aside (no deletion); the sampler (a 1 s `nvidia-smi` loop) was stopped via a stop file.
- GPU lease taken/released twice by the CLI itself; lease log 193 → 197 lines (sha `edc8247b…` →
  `a0433998…`); GPU idle (353 MiB, 0 %) and lock free after; no TASL-7 action; no commit/push; tracked trees
  clean (`code_1f9e8232`, `code_de3de54f`, `harness_6adf3859` all dirty=0).

## 8. What remains

1. **Real-label run:** rebuild the data directory from sweep-1 B.2's `label_block.jsonl` when it exists
   (authority `R1-B2-PIN-FIX2`, 19 Nov: one fresh B.2 attempt after the 18 Nov preflight STOP), i.e. the same
   `sft-data` command with `--labels <audit>/label_block.jsonl --label-sweep sweep1` into a **new** run
   directory, then the same `sft-dev` command. Today only synthetic labels exist, which is the report's
   authorized stand-in for a readiness trial.
2. Optional readiness breadth: the lr grid is {1e-5, 3e-5, 1e-4} × seeds {0,1,2}; at ~2.7 min per run a full
   9-run grid plus `sft-select` would take ≈ 25–30 min. Not required for the readiness trial.
3. P.4 evidence runs remain "not yet" (the code refuses them); they need sweep-2 labels, a pinned table, a
   separate `verify_evidence_completion` record and the authorization note.
4. The SFT unit's verification environment on the portal is transformers 5.19 (vs 4.49 on the Mac); only the
   CPU-`--tiny` tests are affected (finding 2). A gradient-checkpointing fix for the SFT path (finding 1) and
   the two minor gaps (findings 4, 5) belong to a later code unit, not this trial.

## 9. Captures

`captures/`: `host_state.txt`, `git_policy.txt`, `env.txt`, `check_config.txt`, `check_environment.txt`,
`tokenizers.txt`, `data_presence.txt`, `models_lease.txt`, `harness.txt`, `models_and_layout.txt`,
`final_state.txt`, `tests_sft_only.log`, `tests_cli_only.log`, `tests_sft_cli.log`,
`sft_data_preflight.log`, `sft_data_preflight_main.log`, `sft_dev_preflight.log`,
`sft_data_run.stdout`, `sft_data_run.stderr`, `data_build_report.json`, `data_build_manifest.json`,
`data_sft_data.json`, `data_splits.json`, `sft_dev_run.stdout`, `sft_dev_run.stderr` (default-command OOM),
`sft_dev_run_micro4.stdout`, `sft_dev_run_micro4.stderr`, `run_report.json`, `run_manifest.json`,
`run_stage_s_sft_report.json`, `run_best_manifest.json`, `run_best.json`, `run_temperature.json`,
`host_config_micro4.json`, `gpu_samples.csv`, `sampler.stop`, `run_commands_and_env.txt`,
`partial_oom_micro8.txt`.
