# Track P Phase 2 review — environment, downloads and pins (STOP 2)

- **Reviewer:** independent reviewer subagent (Claude Code, zhixu portal `TASL-2`); had not seen the Phase 2 work in progress.
- **Date:** 26 Oct 2026 (UTC; portal local clock 25 Oct).
- **Branch / range:** `trackp-20261026`, `51d0d57..7285791` (one commit, `7285791`, also `origin/trackp-20261026`). Per the author's overnight instruction Phase 2 runs on this reviewed branch instead of a merged `main`; the report records this.
- **Authority:** `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` §0 and Phase 2 (2.1–2.3, STOP 2: "the reviewer re-checks revisions and sha256"); Phase 0 facts `docs/r1/reports/PORTAL_TRACKP_HOST_FACTS_20261026.md` (accepted).
- **Deliverables reviewed:** `docs/r1/reports/TRACKP_PHASE2_ENV_PINS_20261026.md`, `docs/r1/reports/trackp_phase2_20261026/`, `r1/c3/train/registry.py`, `r1/c3/train/registry.yaml`, `r1/scripts/configs/trackp_portal.json`, `r1/scripts/trackp_gpu_smoke.py`, `r1/tests/test_trackp_cli.py`.

Reviewer scratch (not committed): `/tmp/claude-1008/-home-dowling-Agent-paper-B/6f21eb35-e6e1-4dfb-b486-109de5f39d91/scratchpad/rev/` (`check.py`, `tarcheck.py`, `cfgcheck.py`, `smoke_review.json`, smoke stdout/stderr, `freeze_now.txt`).

## What I re-ran, and results

### Revisions (2.2)

| Check | Result |
|---|---|
| Registry `PINS` / `registry.yaml` repo and full revision vs Phase 0 (full 40-char hashes from `portal_trackp_host_facts_20261026/`) | All 8 identical. |
| Kev `v1.0` tag on the Hub (`/api/models/<repo>/refs`, my own call) | `jaredpalmer/kev-0.8b` v1.0 → `788ddbdd65715bb03a56788c822f6c632c9a551d`; `jaredpalmer/kev-4b` v1.0 → `591dcb5bd6d05eb0b5131ea6608f93f10243335c`. Both = registry. (`main` is elsewhere: `bf75a6a8848e`, `6cfce5c2fa4b`, as Phase 0 found.) |
| Other 6 repos: pinned revision vs current Hub `main` | All still equal to `main` today (no drift since Phase 0). |
| Files came from the pinned revision | `snapshot_download` metadata under each `<dir>/.cache/huggingface/download/*.metadata`: every file's recorded commit = the pinned revision (8/8 dirs, 112/112 files). Independently, the files' bytes equal the Hub tree at that revision (below). |
| Kev `training_config.json` `base_revision` | `dc7cdfe2…` (0.8B) and `1001bb4d…` (4B) = pinned Qwen bases; `adapter_config.json` `base_model_name_or_path` = matching Qwen repos. |

### sha256 (2.2), re-hashed with my own script (not `registry.py`)

`check.py` streamed every file once, computing sha256 and the git blob sha1, and fetched the Hub tree (`/api/models/<repo>/tree/<rev>?recursive=true`) for each pin:

- **112 files hashed; 0 problems.** Every sha256 and size equals `registry.yaml`.
- File sets: on disk (excluding `.cache/`) = registry = Hub tree at the revision, for all 8 repos (no missing, no extra).
- **Hub's own records:** all 22 LFS files (every weight file — Qwen 0.8B/4B shards, StartLux 0.8B/2B/4B shards, Laya `model.safetensors`, Kev `adapter_model.safetensors` and `head.pt` for both sizes — plus tokenizers and StartLux figures) match the Hub LFS sha256 and size; all 90 non-LFS files match the Hub git blob sha1 and size.
- Totals per repo match the report's GB table.

### Kev GitHub release cross-check

- Tarballs in `~/r1_trackp/ext/kev_release_dl/`: my sha256 of `kev-0.8b.tar.gz` (`0ae144c7…`), `kev-4b.tar.gz` (`2e707e2e…`) and `SHA256SUMS.txt` (`495d104f…`) equal `kev_release_tarballs.sha256`, the lines in `SHA256SUMS.txt`, and GitHub's own asset digests (`gh api repos/jaredpalmer/kev/releases/tags/kev-1.0`; sizes also equal).
- Tar members hashed in memory (`tarfile`, `python -I`, nothing extracted): every member that exists in the Hub repo is byte-identical to the registry entry — 11/11 for 0.8B and 16/16 for 4B, including `adapter_model.safetensors`, `head.pt`, `adapter_config.json`. The report's claim holds, and holds more broadly than it says. Each tarball also has `locked_test.json`, which is not on the Hub and not in the registry (see note N1).

### 2.1 venv

- `uv pip freeze` of `~/r1_trackp/venvs/trackp-gpu` now is **identical** (sorted diff empty) to the committed `pip_freeze_trackp-gpu.txt`. Python 3.12.15; torch 2.6.0+cu124, triton 3.2.0, transformers 5.19.0, peft 0.21.2, safetensors 0.8.0, accelerate 1.15.0, datasets 5.1.0, flash-linear-attention 0.5.2 / fla-core 0.5.2, causal-conv1d 1.7.0, `kev@2074cc4`, `laya@a478221`, `startlux-decide@a99977d` — all as in the report and in `trackp_portal.json` `venv`. `uv` 0.13.5.
- Binding mechanism checked in the installed transformers source (`integrations/hub_kernels.py`): `use_kernel_func_from_hub_with_fallback` imports `fla.ops.gated_delta_rule.chunk_gated_delta_rule` / `causal_conv1d.causal_conv1d_fn` if importable, otherwise the torch function; the `kernels` package is not installed, so the outer hub decorator is the identity, and the module global's `__wrapped__` is the torch function. The smoke test's `torch_path()` swap therefore really does select the torch path.

**GPU smoke re-run (my one GPU job).** Preconditions: `origin/main` = `b5a7aec`, its STATUS has no running Track X B1/B2 (Track X's branch `exam-x-20261026` is at its Phase 1 authorization); compute-apps query empty; lock free. Command: `HF_HUB_OFFLINE=1 AR_HARNESS_ROOT=~/r1_trackp/autoresearch_harness ~/r1_trackp/venvs/trackp-gpu/bin/python r1/scripts/trackp_gpu_smoke.py --model ~/r1_trackp/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41 --out <scratch>/smoke_review.json`. Lease taken by the script; `~/r1_trackp/runs/gpu_lease_log.jsonl` gained start 04:47:20Z / end 04:47:35Z (pid 1948195), left in place. **Exit 0, pass**, numbers reproduce attempt 2 to every digit:

| Check | Value | Tol | Pass |
|---|---|---|---|
| bf16 matmul 2048² rel. err vs fp32 | 2.88e-3 | 1e-2 | yes |
| fp32 forward: fast vs fp32-CPU ref (max \|Δlogit\|) | 0.02935 | 0.04026 (2 × TF32 torch path 0.02013) | yes; argmax agreement 100 % |
| bf16 forward: fast vs ref | 0.2361 | 0.5303 (2 × bf16 torch path 0.2651) | yes; argmax 99.51 % |

No "falling back to its reference PyTorch implementation" warning in stderr (the wrapper emits it when fla is not bound); the only warning is fla's Triton 3.2 < 3.3 notice. So fla/causal-conv1d are bound and the **runbook "Done when" (bf16 matmul and one DeltaNet forward on the GPU) is met.**

**Judgement on the criterion change.** Justified, not a relaxation of anything the runbook asks: the runbook criterion is only that both run on the GPU, which attempt 1 already showed (it "failed" only the author's own extra parity check). The 2e-3 of attempt 1 was below the precision of fla's fp32 Triton dots (TF32-class); the replacement anchors the tolerance to a known-correct reduced-precision torch-path run against an fp32 CPU reference, which is a sound design, and the fast path is closer to fp32 than the bf16 torch path. Two caveats (finding 5): the factor 2 was set after seeing 0.029 / 0.020 = 1.46, and in bf16 the tolerance (0.53 logits) is loose — the discriminating part there is argmax agreement ≥ 99 %. The report already discloses that this is its own check.

### 2.3 config

- `trackp-cpu/bin/python r1/scripts/trackp.py --check-config` → `"placeholders": []`, exit 0, digest `f9b7354f…` (as reported; the file's raw sha256 is `da3ca51a…`, the digest is the CLI's canonical one). `r1/tests/test_trackp_cli.py` in `trackp-cpu`: 8 passed. `grep -c TODO_VERIFY` = 0.
- My cross-check (`cfgcheck.py`): every `bases.*` `base_repo`/`base_revision`/`local_path`, and Kev `adapter_repo`/`adapter_revision`/`adapter_local_path`, equals the registry entry (Kev bases mapped to the Qwen base of the same size); all local paths exist. Host `TASL-2`, GPU "NVIDIA GeForce RTX 4090", cc 8.9 (`nvidia-smi`), lock path `~/r1_locks/gpu0.lock` exists, `hf_home` and `runs_dir` exist. `--check-config` itself only checks placeholders; it does not compare against the registry (not required by the runbook).
- Values chosen rather than read: `jev.model = jev-1.14.0` (flagged in the report and in the config comment — correct); `code_pins` (not flagged — finding 3); `hf_home` path (a layout choice, harmless). `rb_demos.model = deepseek-flash` predates Phase 2 (note N3).

### Ground rules

- Commit `7285791`: author and committer `Dowling Wong <wangdowling@gmail.com>`, message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Remote refs: only `trackp-20261026` among Track P branches (= `7285791`); `main` still `b5a7aec`; the local `trackp-20261026-*` branches are not pushed.
- Secrets: `~/.config/r1/secrets.env` does not exist (stat only), so nothing could have been read; the diff contains no key material and no reference to the file.
- Free space: report ≈ 879 GB at start; `registry.py` checks the 100 GB floor before and after each download; now 792 GB free on `/` (Track X also writes there). Floor respected.
- GPU: attempt 1, parity probe, attempt 2 and the GPU-venv test run all in the lease log with start/end; no Track X evidence phase was running.

## Findings

1. **Minor — the cited lease-log evidence is not committed.** Claim: "Lease log (`gpu_lease_log.jsonl`): …" with the evidence in `trackp_phase2_20261026/`. Observation: `trackp_phase2_20261026/gpu_lease_log.jsonl` exists locally but is ignored by `.gitignore:49` (`*.jsonl`) and is not in `7285791`; the start/end times are only in the report text and partially inside the two smoke JSONs. Required fix: commit it (`git add -f`, or a `.txt` copy), or state in the report that the canonical log is `~/r1_trackp/runs/gpu_lease_log.jsonl` on the host and is not committed.

2. **Minor — the Kev tar-member comparison is not in the evidence.** Claim: the three files inside the release tarballs are byte-identical to the Hub files. Observation: true (I reproduced it, and in fact all 11/16 shared members match), but `kev_release_tarballs.sha256` holds only the three tarball hashes; nothing committed shows the member hashes or the comparison. Required fix: commit the member-level table (member, size, sha256, registry match) or the script that produced it plus its output.

3. **Minor — code pins are a choice, not read from Phase 0, and not flagged.** Claim: "code pins `kev` @ `2074cc4`, `laya` @ `a478221`, `startlux-decide` @ `a99977d`". Observation: Phase 0 recorded no code-repo commits; these are the repos' HEADs at install time (Kev and StartLux are still HEAD; Laya HEAD has since moved to `b9fe351`). Kev's code pin is 23 commits **after** the GitHub `kev-1.0` tag (`6b719c3`, 1 Oct), while the Kev adapters are pinned at the v1.0 release; the `kev/` changes in that range are device probing, `Checkpoint.release_date`, CLI flags and diagnostics (no model-math change seen in the diff summary) plus the release-verification records. Reasonable, but it is a decision the author should see. Required fix: in the report, list the three code pins under "chosen, to be confirmed", with the rationale (HEAD at install; for Kev: post-tag commits are tooling and include the v1.0 verification) — or pin Kev code to the tag.

4. **Minor — `kernels_bound` in the smoke report does not show what is bound.** Claim: "fla + causal-conv1d bound". Observation: `kernels_bound` prints `transformers.models.qwen3_5.modeling_qwen3_5.<name>` for all four functions — the `functools.wraps` wrapper, identical whether fla is bound or not; the implementation lives in the wrapper's closure. The claim is nevertheless true (packages import, no fallback warning, fast ≠ torch path numerically, different timings). Required fix: record the real implementation (e.g. `qm.torch_chunk_gated_delta_rule.__closure__` cell holding `fla.ops.gated_delta_rule.chunk.chunk_gated_delta_rule`, or check the absence of the fallback warning) or drop the field / reword it.

5. **Minor — calibrated criterion: post-hoc factor and missing probe output.** Claim: calibrated criterion replaces an arbitrary one. Observation: justified (see judgement above), but the factor 2 was chosen after the 1.46 ratio was known, and the basis of the change — `parity_probe.py`'s output with TF32 off and on (fast vs CPU, torch-GPU vs CPU, fast vs torch-GPU) — is not committed; only the script is. Required fix: commit the probe's output and add one sentence that the factor was set after attempt 1 and that, in bf16, the effective check is argmax agreement ≥ 99 %. No change to the pass/fail outcome is needed.

6. **Minor — GPU-venv test failures are asserted to be "two kinds" without evidence.** Claim: 27 failed / 3 errors in `trackp-gpu`, "all of these two kinds" (CPU-only `causal_conv1d`, and transformers not importing without a visible device). Observation: `trackp_tests_in_gpu_venv.txt` has only the `FAILED`/`ERROR` lines, no reasons; the list includes `test_every_family_and_head_form_learns_a_fixed_batch[laya-softmax12]` (ModernBERT, no DeltaNet/causal-conv1d) and the three sidecar-loader errors, which the stated causes do not obviously explain. Required fix: commit the short failure reasons (`pytest -rfE --tb=line` output) and confirm that every failure is one of the two stated kinds, or explain the others. (These tests pass in `trackp-cpu`; this is a record-accuracy issue, not a Phase 2 criterion.)

## Notes (no fix required for STOP 2)

- N1. The Kev release tarballs include `locked_test.json` (Kev's locked test split), absent from the Hub repos and from the registry. Not needed by Track P; mention if Kev's own split ever matters for leakage arguments.
- N2. The smoke test exercises the chunked (prefill) gated-delta-rule and `causal_conv1d_fn`; the decode-path kernels (`fused_recurrent_gated_delta_rule`, `causal_conv1d_update`) are not exercised. Sufficient for Phase 3 training forwards; generation (reason-then-bin, P.6) should be smoke-tested when it first runs.
- N3. `rb_demos.model = "deepseek-flash"` was set in Phase 1, not here; R1-RB-TEACHER names DeepSeek-V4.1-Flash-1017. Confirm the exact id before Phase 9 (not a Phase 2 matter).
- N4. The 100 GB floor is checked before and after each repo, not during; with ≈ 800 GB free and ≤ 9.4 GB per repo this cannot be breached.
- N5. torch 2.6.0+cu124 on driver 535 via CUDA minor-version compatibility, and the CPU/GPU venv split, are disclosed and are author questions; the smoke test passed on this stack.

## Verdict

**Verdict: pending fixes.** No blocking finding: revisions (Kev at the `v1.0` tag commits, verified on the Hub) and all 112 sha256 values re-check independently against the files, the registry and the Hub's own LFS/blob records; the Kev release cross-check holds; the venv matches its freeze; the "Done when" for 2.1–2.3 is met and the GPU smoke test reproduces exactly. Findings 1–6 are minor record/evidence fixes (commit the lease log, tar-member table, probe output and test failure reasons; flag the code pins as a choice; fix the `kernels_bound` field or wording). I will re-check them and then write "accepted" or "not accepted".


## Implementation agent's response (26 Oct)

1. Fixed: the lease log is committed as `trackp_phase2_20261026/gpu_lease_log.txt` (the `.jsonl` was git-ignored); report reference updated.
2. Fixed: `kev_release_members_vs_registry.txt` — every tar member hashed in memory: 26 MATCH, `locked_test.json` ×2 NOT_ON_HUB.
3. Fixed: the report flags the three code pins as choices (HEAD at clone time; Kev 23 commits after `kev-1.0`) and asks the author (Q3). Not re-pinned overnight: Phase 1 was reviewed against `2074cc4`.
4. Fixed: `bound_implementation()` reads the wrapper's closure; attempt 3 (`gpu_smoke_attempt3.json`) records the fla and causal-conv1d functions; same numbers, pass.
5. Recorded in the report: factor 2 chosen after the 1.46 ratio was known; bf16's discriminating check is the next-token agreement; probe output committed (`parity_probe_output.json`, re-run under the lease).
6. Fixed: `trackp_tests_in_gpu_venv.txt` now gives each failure's error line. 26 × `Expected x.is_cuda()` (the 3 sidecar errors are the tiny Kev fixture), 3 × import quirk in CLI subprocesses, and `laya-softmax12` — a real weakness of the learnability test (lr 1e-2 unstable for Laya's head; passed on torch 2.14 only by 0.078). Test changed to lr 3e-3, 80 steps, margin 0.2 (stricter): 8/8 pass in `trackp-cpu`; Laya in `trackp-gpu` by script: softmax-12 2.49 → 2.08, cumulative-11 4.19 → 1.47 (`laya_learnability_gpu_venv.txt`).

## Re-check (26 Oct 2026)

Same independent reviewer. Range re-checked: `7285791..c6d0887` (`origin/trackp-20261026` = `c6d0887`; full Phase 2 range `51d0d57..c6d0887`). No GPU job run for the re-check. Commit `c6d0887`: author/committer `Dowling Wong <wangdowling@gmail.com>`, Claude co-author line present; remote `main` still `b5a7aec`, only `trackp-20261026` pushed. The registry, the model files and the config are unchanged since `7285791`, so the revision and sha256 results above still hold.

1. **Resolved.** `trackp_phase2_20261026/gpu_lease_log.txt` is committed. It is identical to `~/r1_trackp/runs/gpu_lease_log.jsonl`, now including my re-run (04:47:20–04:47:35Z), attempt 3 (04:52:52–04:53:07Z), the probe re-run and the Laya runs. Every GPU job has a start and an end entry. The report points to the `.txt` file.
2. **Resolved.** `kev_release_members_vs_registry.txt`: 26 MATCH and 2 × `locked_test.json` NOT_ON_HUB. Every hash equals my own in-memory hashes and the registry. The report text is updated.
3. **Resolved.** The report now lists the three code pins as choices: each is HEAD at clone time, and Kev's is 23 commits after `kev-1.0` (`6b719c3`). The author is asked about them as Q3. Not re-pinning because Phase 1 was reviewed at `2074cc4` is a fair reason.
4. **Resolved.** `bound_implementation()` reads the wrapper's closure. Attempt 3 (`gpu_smoke_attempt3.json`) records `fla.ops.gated_delta_rule.chunk.chunk_gated_delta_rule`, `fla.ops.gated_delta_rule.fused_recurrent.fused_recurrent_gated_delta_rule` and `causal_conv1d.causal_conv1d_interface.causal_conv1d_fn` / `causal_conv1d_update`. These are the functions I found in the installed packages. The numbers are the same as attempts 2 and my re-run (pass). The closure scan skips the `__wrapped__` torch function and anything in `transformers.*`, so on a torch fallback it reports "(torch path)". Correct for this transformers version.
5. **Resolved.** `parity_probe_output.json` is committed. With TF32 off, torch-GPU vs CPU is 5.1e-5 and fast vs CPU is 0.0294; with TF32 on, torch-GPU vs CPU is 0.0201. This supports the explanation that the 0.029 gap is TF32-level precision in fla's kernels, not a kernel error. The report now says that the factor 2 was chosen after the 1.46 ratio was known, and that in bf16 the check that discriminates is the ≥ 99 % next-token agreement. Decode-path kernels are recorded as bound but not exercised (N2).
6. **Resolved in substance, but the counts are wrong (residual R1 below).** `trackp_tests_in_gpu_venv.txt` now gives the error lines.
   - The sidecar errors are `Expected x.is_cuda()` (the tiny Kev fixture), and the CLI failures are `ModuleNotFoundError` from the subprocess import quirk.
   - `laya-softmax12` was a real assertion failure: the loss oscillated (2.48 → 2.46). The explanation that lr 1e-2 is unstable for Laya's head is correct.
   - The test change (lr 1e-2 → 3e-3, 40 → 80 steps, required drop 0.05 → 0.2) is a reasonable robustness fix, not a weakening: the required drop is 4× larger and the final-loss bound < 3.0 is unchanged.
   - Re-run in `trackp-cpu`: with `HF_HOME=~/r1_trackp/hf_cache HF_HUB_OFFLINE=1`, **8 passed**. Without `HF_HOME` the two Laya cases skip because the tokenizer is not in the default cache; that skip is the test's intended behaviour. The cache holds 91 MB of tokenizer files and no weights.
   - Laya in `trackp-gpu` by script: 2.49 → 2.08 and 4.19 → 1.47 (`laya_learnability_gpu_venv.txt`). The script itself is not committed; only its output is.

**Residual R1 (minor, documentation; does not block acceptance).** The new `trackp_tests_in_gpu_venv.txt` has 27 test lines, not 30. Compared with the original list, three failures have no error line: `learns_a_fixed_batch[qwen_control-softmax12]`, `[qwen_control-cumulative11]` and `[startlux-cumulative11]`. The report's breakdown "26 `is_cuda`, 3 import quirk, 1 Laya" also does not match the file: the file shows 22 `is_cuda`, **4** `ModuleNotFoundError` and 1 Laya. With the three missing lines (Qwen3.5-family on CPU tensors, so almost certainly `is_cuda`), the correct breakdown is 25 / 4 / 1. Required: when the Phase 2 report is finalised, add the three missing lines and correct the breakdown to 25 / 4 / 1. This is a record correction about a non-criterion test run in a venv that is documented as GPU-only. It does not affect any Phase 2 "Done when", and all of these tests pass in `trackp-cpu`.

Unrelated observation: the working tree has an untracked `r1/scripts/trackp_startlux_ref.py`. It is not part of the reviewed range and was not reviewed.

**Verdict: accepted.** Phase 2 (2.1–2.3) meets the runbook:
- Revisions are verified on the Hub, with Kev at the `v1.0` tag commits.
- All 112 sha256 values were re-hashed independently and match the registry and the Hub's LFS/blob records; the Kev release cross-check holds.
- The bf16 matmul and the DeltaNet forward run on the GPU with fla and causal-conv1d bound, which is now recorded.
- `--check-config` passes, and the config values match the registry and the host.

Findings 1–6 are resolved. Residual R1 is to be corrected in the report as described; author questions Q1–Q3 remain open.
