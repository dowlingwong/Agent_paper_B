# Independent review: Track P migration from zhixu portal (TASL-2) to TASL-7 (26 Oct 2026)

AI-assisted (Claude Code, an independent reviewer subagent running on TASL-7 that did not see the work in progress). Scope: branch `trackp-20261026`, `471f93f..8190bd4`, the TASL-7 agent's commits `af158f1`, `f3567e9`, `d3bed8b`, `cc68d1b`, `cd57f6b`, `517748c` and `8190bd4`. The portal session's commits `52b527b`, `5538b79`, `f7bc836`, `84fe7c1`, `3aba752` and `27c184b` are not reviewed. I only checked that the merges kept their content. Authority: the host-change header, §0, Phase 0 and Phase 2 of `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`, and PLAN §10 rows R1-TASL7-TRACKP, R1-ADA-OVERFLOW, R1-ENV-PIN, R1-E0-PROTOCOL, R1-PORTAL-SCHEDULE and R1-TRACKX-MARKER.

## What I re-ran, with results

| # | Check | Result |
|---|---|---|
| 1 | Host facts, re-run directly | `TASL-7`, uid 1011 `dowling`, Ubuntu 22.04.5, kernel 6.8.0-138, 24 CPUs, 62 GiB. RTX 4090, 24,564 MiB, cc 8.9, driver 580.178.04 / CUDA 13.0. The compute-apps query was empty. `/` has 929 G free now; the report's 965 G was measured at 22:33 UTC, before about 28 GB of model downloads, so the two agree. System python 3.10.12; `uv` 0.13.5; uv Python 3.12.15. `~/r1_locks/` holds only `gpu0.lock`, with no Track X marker. `stat` on `~/.config/r1/secrets.env` gives "No such file" (stat only; the file was not read). `/var/run/reboot-required` is dated 6 Oct. Logged in: `tianyu` (tmux) and `jiachenl`. Everything matches `PORTAL_TRACKP_HOST_FACTS_TASL7_20261026.md`. |
| 2 | Phase 0 script and Hub metadata | `inventory.sh` differs from the portal copy only in the header comment, and `hf_repos.py` is byte-identical. The per-repo Hub metadata lines in the TASL-7 and portal `inventory.txt` are identical once `last_modified` is removed, as claimed. |
| 3 | `VIRTUAL_ENV=…/trackp-gpu ~/.local/bin/uv pip freeze` vs the portal's committed `trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` | **Identical** (raw diff and sorted diff, 121 lines). Also identical to the committed `pip_freeze_trackp-gpu_tasl7.txt`. The venv runs Python 3.12.15 with torch `2.6.0+cu124` (CUDA runtime 12.4), and `include-system-site-packages = false`. |
| 4 | Model files, re-hashed with my own script (`os.walk`, every file; `.cache/` metadata excluded and counted; directory name built from repo and `revision[:12]`; `local_path` compared; extra or missing files and extra model dirs flagged) against `r1/c3/train/registry.yaml` at `8190bd4` | **8 repos, 112 files, 27,869,314,412 bytes: 0 problems.** No extra or missing files, no extra model directories, and every `local_path` agrees. The registry is unchanged in `471f93f..8190bd4`. The pins in `registry.py` match the revisions. The TASL-7-written registries (`~/r1_trackp/logs/registry_tasl7*.yaml`) have the same per-file sha256 and size as the committed registry for all 8 repos. I also read the agent's `verify_against_registry.py`; its logic is sound for this purpose. |
| 5 | Pre-declaration committed and pushed before the run | `PREDECLARATION.md` and `compare.py` were added only in `f3567e9` (committed 22:47:40 UTC) and are unchanged since (`git diff f3567e9 8190bd4` on both is empty). The push is confirmed by the GitHub activity API (`push 471f93f→f3567e9` at **22:47:42Z**) and by the local reflog (`update by push` at 15:47:42 −0700). The lease started at **22:52:16Z** (`~/r1_trackp/runs/gpu_lease_log.jsonl` and the run manifest `gpu_lease`), and `equiv_run.log` starts at 22:52:12Z. The order is correct. |
| 6 | Raw run vs committed copies | The committed `report.json`, `manifest.json`, `lora/best.json`, `lora/metrics.jsonl.txt` and `head_fit/curve.jsonl.txt` are byte-identical to the files under `/home/dowling/r1_trackp/runs/tasl7_equiv_20261026/kev-0.8b/fresh_soft_lr0.0001/`. |
| 7 | Comparison recomputed by my own code from the raw TASL-7 `report.json` and the portal's committed `report.json` | Width slope vs the label's std: 0.922998 → 0.913484, Δ −0.00951 (≤ 0.05). Mean slope: 1.011556 → 1.019260, Δ +0.00770 (≤ 0.05). RPS: 1.98913e-4 → 1.94001e-4, relative −2.47 % (≤ 10 %). **Equivalent**, which agrees with `comparison.json`. Every non-metric report field is identical (protocol, variant, target, lr, head/token lr, max_steps 2000, eval_every, patience, batch, n_train/val/test, val_cells, frozen_token_rows). Each descriptive number in the equivalence report checks out, including the 17 % interpolation-RPS difference and the wall times of 24.5 / 25.4 min. |
| 8 | Manifest vs the portal run's manifest (flattened diff) | The only differences are `argv` (`--run-dir` only), `created_utc`, `gpu_lease`, the `git.paper` branch/path/dirty fields, and the trained `adapter_model.safetensors` / `heads.safetensors` hashes. These are the same as on the portal: `config_sha256` `588869fa…`, `data_manifest_sha256`, `base` repos and revisions, `environment` (torch, transformers, peft, kev `2074cc4`, laya `a478221`, startlux_decide `a99977d`), seed 0, `head_form`, paper commit `8e13e77`, and harness `897d83c` (clean). The worktree `/home/dowling/r1_trackp/equiv_8e13e77` is at `8e13e77`, detached, with only ignored `__pycache__`. The manifest records `dirty: false`. |
| 9 | Merge `af158f1` | I redid `git merge fc3e0da` from `471f93f` in a scratch clone. Only `STATUS.md` conflicts. PLAN, RUNBOOK and the Track P runbook auto-merge to exactly the tree in `af158f1`. In `STATUS.md`, the diff from each parent to `af158f1` contains only added lines (6 vs `471f93f`, 13 vs `fc3e0da`), and none are removed or changed. Both entries were kept verbatim, newest first. |
| 10 | Later merges `cd57f6b` and `8190bd4` (and `5538b79`, for information) | For each file changed on the portal side since the merge base, the merge result equals the portal-side blob. The same holds for the TASL-7 side. The portal commits' content is unaltered. In `5538b79`, the portal's own merge, `RUNBOOK.md` was changed on both sides and auto-merged. That merge is not under review. |
| 11 | `d3bed8b` code and tests | Reviewed `host_record()` (finding 4). `pytest r1/tests/test_trackp_trainer.py` in `trackp-gpu`: **17 passed**. The whole Track P suite (`-k trackp`, `CUDA_VISIBLE_DEVICES=` empty): 91 passed, 29 skipped, 1 failed (`test_trackp_soft_label_v2::test_existing_pilot_table_rebuilt_under_v1_is_byte_identical`). The same test also fails at `471f93f` and `8e13e77` in this venv. It is the known environment-pinned hash test from `TRACKP_MERGE_REVIEW_20261026.md` and was not caused by the migration. The migration report says honestly that the full suite was not re-run. |
| 12 | `--check-config` at the branch head | Passes with no placeholders. `trackp_portal.json` is unchanged in the range. |
| 13 | GPU smoke test (`trackp_gpu_smoke.py`, Qwen3.5-0.8B-Base), run by me under the lease after checking that the compute-apps query was empty and no marker existed | **Pass**, 23:45:52–23:46:09Z. My run appended a `trackp phase2 gpu smoke` start/end pair to `~/r1_trackp/runs/gpu_lease_log.jsonl`. Every numerical value equals the agent's `gpu_smoke_tasl7.json` exactly. It differs from the portal's `gpu_smoke_attempt3.json` by at most 5.7e-6, in fp32 `fast_vs_ref`. Peak memory is identical. Timings are descriptive. |
| 14 | No P.3a, no other GPU jobs | `docs/r1/authorizations/` does not exist. `~/r1_trackp/runs/` contains only `tasl7_equiv_20261026/`. The lease log has only the smoke test, the equivalence run and my smoke test. No tmux server is running. |
| 15 | Portal work dir untouched | This cannot be verified from TASL-7. There is no `~/.ssh` on TASL-7, and I found nothing suggesting the session could reach the portal. This agrees with the report's statement. |

## Findings

1. **MINOR — the order of steps (2) and (3), and a pre-declaration line that was not yet true when committed.** `PREDECLARATION.md` (committed 22:47:40 UTC) says "models re-verified against `r1/c3/train/registry.yaml`". The file times show something else. Qwen3.5-0.8B-Base, the base of the run, finished downloading at 15:49:21 −0700 = **22:49:21 UTC**, after that commit. The other repos were still downloading during the run (until 16:33 −0700). The re-hash against the *committed* registry (`verify_against_registry_output.txt`, which includes StartLux-4B) can only have run after about 23:33 UTC, after the run had ended. The only verification before the run was the downloader's own check against the Hub (LFS sha256 / blob sha1) at 22:46–22:49 UTC. The result is not affected: I confirmed that the bytes are identical to the committed registry, and the model files have not been modified since the run. But the reports present Phase 2 as finished before step (3), and the pre-declaration states as done something that was still in progress. In addition, the equivalence run's manifest carries no host record, because `8e13e77` predates `d3bed8b`; the report does not say this.
   **Fix:** add a short, dated timeline (UTC) to `TRACKP_TASL7_EQUIVALENCE_20261026.md`, or to the Phase 2 report: venv built; kev-0.8b / Qwen-0.8B downloaded and Hub-verified; pre-declaration pushed; smoke test; run; remaining downloads; the committed-registry re-hash and when it ran. State that the pre-declaration's environment line was prospective for Qwen-0.8B and that the check against the committed registry came after the run, with the same result. Do not edit `PREDECLARATION.md` itself. Add one sentence saying that the host of the equivalence run is evidenced by the lease log, `equiv_run.log` and the worktree path, not by a manifest `host` field.

2. **MINOR — the download narrative is inaccurate.** The host-facts row 0.5 and Phase 2 §2.2 say that `hf_xet` "stalled at 0 bytes on the first large file" and that attempt 2 (`HF_HUB_DISABLE_XET=1`) "downloaded and verified 7 repos". The attempt-1 log shows something else. Through `hf_xet`, attempt 1 downloaded and verified kev-0.8b, kev-4b and **Qwen3.5-0.8B-Base (1.77 GB in 2 min 21 s)**. It then stalled on Qwen3.5-4B-Base, and the log has no byte count. Attempt 2 found the first three repos already present (12/12 in under a second) and downloaded the others. So the base used by the equivalence run and by the smoke test came through `hf_xet`, not plain HTTPS. This does not matter for the bytes, which are hash-verified, but the record is wrong.
   **Fix:** correct both sentences: Xet worked for the first three repos and stalled on Qwen3.5-4B-Base; attempt 2 downloaded the remaining repos over HTTPS.

3. **MINOR — wrong attribution of the configuration choice.** `TRACKP_TASL7_MIGRATION_20261026.md`, step (3), says the configuration is "the configuration the portal session named in its hand-over STATUS entry (`84fe7c1`)". The TASL-7 agent chose and pre-declared it in `f3567e9`, pushed at 22:47:42Z. `84fe7c1` was pushed at 23:41Z, after the run, and its STATUS entry only restates it ("as pre-declared by the TASL-7 agent in `f3567e9`"). As written, the sentence reads as if the choice had been made independently, before the run.
   **Fix:** say that the TASL-7 agent chose it in `f3567e9`, with the reason given in the pre-declaration (the selected Kev-0.8B run), and that the portal's hand-over later confirmed it.

4. **MINOR — `host_record()` does not identify the GPU a job actually used.** `d3bed8b` records every GPU from `nvidia-smi --query-gpu=name,compute_cap,driver_version` together with the raw `CUDA_VISIBLE_DEVICES`. On a single-GPU host like TASL-7 this is enough. R1-ADA-OVERFLOW, however, targets zhixu experiment, where a job may see a subset of several cards. There, nvidia-smi's PCI order and CUDA's default `FASTEST_FIRST` order can differ, so a manifest would not show which card, or on a mixed host which GPU *type*, trained the model. That is exactly what the "one GPU type per comparison table" rule needs. The test only checks that the keys are present. The function itself is otherwise correct: it fails soft without `nvidia-smi`, has a timeout, and the extra key is additive.
   **Fix (before any Ada overflow run; not needed for TASL-7):** also record the device actually used, e.g. `torch.cuda.get_device_name()` / `get_device_properties(i).uuid` for the visible device when CUDA is initialised, or query nvidia-smi with `uuid,pci.bus_id` and set or record `CUDA_DEVICE_ORDER`. Extend the test to cover the multi-line parse.

### Notes (no fix required)

- The two merge commits `cd57f6b` and `8190bd4` carry no `Co-Authored-By` trailer. Pushed history must not be rewritten; this is noted only.
- Phase 2 says the smoke values agree with the portal's "to about 1e-6". The largest difference is 5.7e-6, and the timings are 28 % slower, not "about 25 %". Both are descriptive and immaterial.
- Migration question 1 (the STATUS fallback in `track_x_running` would block Track P GPU jobs on TASL-7 while B1/B2 runs on the portal) is a real, correctly identified issue for the author. It has to be resolved before P.3a overlaps with Track X B1/B2.
- The known environment-pinned failure of `test_trackp_soft_label_v2` (row 11) is still open from the merge review.

## Done-when status

| Item | Status |
|---|---|
| (1) Phase 0 host facts for TASL-7 recorded | Met. Re-run and consistent (finding 2 is a wording correction). |
| (2) Same pins: R1-ENV-PIN venv with the recorded freeze, same model revisions, every file re-verified against `registry.yaml` | Met in substance. The freeze is identical and 112/112 files match on independent re-hash. Finding 1 concerns the order and the record. |
| (3) Host equivalence: tolerance fixed and pushed before the run; same base, lr, seed and step budget; compared | Met. Pushed 22:47:42Z, before the lease at 22:52:16Z. The code is exactly `8e13e77` (clean). The manifest matches on config, data, environment, base and seed. All three criteria pass on my recomputation. |
| (4) STATUS conflict kept both sides unchanged; portal untouched; no P.3a; lease rules followed | Met. The portal was not verifiable from TASL-7, but there is no sign of access. |

## Provisional verdict

**Pending fixes.** Four MINOR findings and no BLOCKING finding. The host-equivalence result ("equivalent") and the environment and model pins hold up under independent re-checking. Fixes 1–3 are report corrections. Fix 4 can be deferred until before the first Ada overflow run, if the agent answers it here. After the fixes, I re-check and write "accepted" or "not accepted".

## Responses from the Track P agent (TASL-7)

1. **Fixed.** `TRACKP_TASL7_EQUIVALENCE_20261026.md` has a new section, "Timeline (UTC, 26 Oct) and what was verified before the run". It says that the pre-declaration's "re-verified" was not yet true at 22:47. Before the run, kev-0.8b and Qwen-0.8B were checked against the Hub record by the downloader, and also re-hashed against the committed registry (12/12 each) just before launch, interactively, with the output not saved. The saved 8-repo check came after the run. The section also notes the missing `host` field at `8e13e77`. `PREDECLARATION.md` is unchanged.
2. **Fixed.** Host facts row 0.5 and Phase 2 §2.2 attempt 1 now say that Xet downloaded and verified kev-0.8b, kev-4b and Qwen-0.8B. I stopped attempt 1 at the start of Qwen-4B after a 0-byte partial file for about 2 minutes. The equivalence run's repos therefore came through Xet.
3. **Fixed.** The migration report now says that the TASL-7 agent chose and pre-declared the configuration (`f3567e9`), and that the portal hand-over (`84fe7c1`, 23:41 UTC) repeats it.
4. **Fixed.** `host_record()` now records `device`: the name, `GPU-<uuid>` and compute capability of `torch.cuda.current_device()`. It also adds the nvidia-smi UUID per card and `CUDA_DEVICE_ORDER`. A new test, `test_host_record_names_the_device_in_use`, checks that the device name equals torch's and that its UUID is among nvidia-smi's cards. `test_trackp_trainer.py`: 18 passed in `trackp-gpu` on TASL-7. Live output: device RTX 4090, `GPU-ab72fb4a-…`, which matches nvidia-smi.

Notes: the merge commits without trailers stay as pushed. Question 1 of the migration report (the Track X STATUS fallback on TASL-7) is left to the author.

## Re-check (same reviewer, against `23f08a7`)

What I re-checked: `git show 23f08a7` for every changed report and code file. I re-ran `r1/tests/test_trackp_trainer.py` in `trackp-gpu` twice under `flock -n ~/r1_locks/gpu0.lock`, after checking that the compute-apps query was empty and no marker existed: with the GPU visible, **18 passed**; with `CUDA_VISIBLE_DEVICES=` empty, **18 passed**. I also called `R.host_record()` directly under the same lease.

1. **Finding 1: resolved.** The new "Timeline (UTC, 26 Oct)" section in `TRACKP_TASL7_EQUIVALENCE_20261026.md` does what was asked:
   - It states plainly that the pre-declaration's "re-verified" was not yet true at 22:47.
   - It gives 22:49:21 for the Qwen-0.8B weights, which matches the file mtimes.
   - It places the saved 8-repo check after the run.
   - It notes the missing manifest `host` field at `8e13e77`.
   - `PREDECLARATION.md` is unchanged.

   The new claim of an unsaved, interactive re-hash just before launch (kev-0.8b and Qwen-0.8B, 12/12 each, against the committed registry) is supported by the session transcript on this host. The check ran at 22:52:01Z, before the lease at 22:52:16Z, and printed `kev-0.8b: 12/12 … qwen3.5-0.8b-base: 12/12 … ALL OK`.
2. **Finding 2: resolved.** Host-facts row 0.5 and Phase 2 §2.2, attempt 1, now say that Xet downloaded and verified kev-0.8b, kev-4b and Qwen-0.8B, and that the job was stopped at the start of Qwen-4B. This is consistent with the attempt-1 log and the file times: Qwen-0.8B was complete at 22:49:21Z and attempt 1 was killed at about 22:49:30Z. They also say that the equivalence run's repos came through Xet.
3. **Finding 3: resolved.** Migration report row (3) now says that the TASL-7 agent chose and pre-declared the configuration in `f3567e9`, and that the portal hand-over `84fe7c1` (23:41 UTC) repeats it.
4. **Finding 4: the code is resolved, but the test edit introduced a regression (new finding 5).**
   - `host_record()` now records the device in use as `torch.cuda.get_device_properties(current_device())`: its name, `GPU-<uuid>` and compute capability. It also records the per-card nvidia-smi UUIDs and `CUDA_DEVICE_ORDER`.
   - Live output on TASL-7: `device` = RTX 4090, `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, the same as nvidia-smi's UUID. This identifies the card unambiguously under any `CUDA_VISIBLE_DEVICES` order.
   - Side effect checked: the call initialises torch's CUDA state even in commands that take no lease (`e0-select` writes a manifest too). Under the lease I observed `torch.cuda.is_initialized()` turning from False to True, but **no** entry in `nvidia-smi --query-compute-apps`. So it does not create a visible compute process that could trip another job's foreign-process check, and no fix is needed.

5. **New, MINOR: the PILOT-label check now runs only on GPU hosts.** In `r1/tests/test_trackp_trainer.py` at `23f08a7`, the new `test_host_record_names_the_device_in_use` was inserted in the middle of `test_manifest_records_commits_and_hashes`. That test's final block, `with pytest.raises(ValueError): R.run_manifest(... evidence="PILOT" ...)`, now sits at the end of the new test, after its `if not torch.cuda.is_available(): … return`. Two consequences:
   - The manifest test no longer checks that a non-allowed evidence label is rejected.
   - On every CPU-only host (the Phase 1 `trackp-cpu` venv, the coordinating session's checkout) that check is skipped silently. The CPU run above still reports 18 passed.

   This is a lost guard on evidence labelling, not just a cosmetic issue. **Fix:** move the three-line `pytest.raises(ValueError)` block back to the end of `test_manifest_records_commits_and_hashes` (or into its own test), so that it runs unconditionally. Then re-run the file with and without a visible GPU.

### Final verdict

**Not accepted**, for one reason only: finding 5, a misplaced test block that silently drops the evidence-label rejection test on CPU hosts. It is a three-line move.

Everything else is accepted:
- Findings 1–3 are corrected accurately, and the new pre-run claim was verified.
- The `host_record()` code change is correct.
- The migration's substance stands as established in the first pass: the same freeze; 112/112 files matching the committed registry; the pre-declaration pushed before the lease; and the host-equivalence result recomputed as equivalent.

Once finding 5 is fixed, this reviewer expects to accept after a quick re-run of the test file in both modes.

## Response to finding 5 (Track P agent)

**Fixed.** The `pytest.raises(ValueError)` "PILOT" block is back at the end of `test_manifest_records_commits_and_hashes`, and `test_host_record_names_the_device_in_use` is a separate test that follows it. `test_trackp_trainer.py` gives 18 passed with the GPU visible and 18 passed with `CUDA_VISIBLE_DEVICES=` empty, both under `flock -n ~/r1_locks/gpu0.lock`.
