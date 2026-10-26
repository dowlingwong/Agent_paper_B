# Track P Phase 1 review (26 October 2026)

- Reviewer: independent subagent (Claude Code, on zhixu portal `TASL-2`). It had not seen the implementation agent's work in progress and judged the work against the runbook and spec, re-running everything itself.
- Date: 2026-10-26, about 02:00–03:30 UTC (portal local time 25 Oct, about 19:00–20:30).
- Phase: Track P Phase 1, "Code" (`docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` §0, table 1.1–1.11, STOP 1).
- Commit range: `ef3e2f3..8ba6b6f` on `trackp-20261026`. That is 20 commits (4 merges of worker branches) and 43 files, +5,632/−31.
- Deliverable: `docs/r1/overnight/TRACKP_CODE_HANDOFF.md` and `docs/r1/overnight/trackp_code_20261026/`.
- Also read: spec `docs/r1/TRACK_P_POST_TRAINING.md` §0–§7 and PLAN §10 rows R1-C3-POST, R1-SOFT-SIGMA, R1-JEV-RUNG, R1-RB-TEACHER, R1-PORTAL-SCHEDULE and R1-TRACKP-RUNBOOK. I also read every new module in full: `r1/c3/train/*`, `r1/c3/{jev_client,rb_demos}.py`, the diffs to `labels.py`, `offline_eval.py`, `prior_model.py` and `serve.py`, `r1/scripts/trackp.py`, the config and the rule file, plus the new tests.
- Environment: `~/r1_trackp/venvs/trackp-cpu` (Python 3.12.15, torch 2.14.1+cpu), `CUDA_VISIBLE_DEVICES=""`, `HF_HUB_OFFLINE=1`, `TMPDIR=/tmp/claude-1008/trackp_review`. No installs, no weights, no GPU job and no secret read (`~/.config/r1/secrets.env` does not exist on the host).

## What I re-ran

1. **Paper suite** (`python -m pytest -q -p no:cacheprovider --continue-on-collection-errors r1/tests`): **536 passed, 1 skipped, 11 failed, 4 collection errors**. The failing and erroring set is identical to `after_paper.txt` and `baseline_paper.txt`. It took 27 min only because the dry runs below ran at the same time. The 129 new tests are confirmed (`--collect-only r1/tests/test_trackp_*.py` collects 129).
2. **Harness suite** (`PYTHONPATH=src python -m pytest ... tests` in `autoresearch_harness`): **434 passed, 9 failed, 1 error, 55 subtests passed**, identical to `baseline_harness.txt`. I deleted the untracked `paper/tables/artifact_completeness_report.txt` afterwards. The harness clone is clean at `264011e`.
3. **The four modules that fail to collect, run with a review-only stand-in** (TMPDIR shim) for the missing harness symbols `SKIP_DISPLAY_ONE_LINE` / `is_control_plane_skip`. Result: `test_c3_sidecar.py` gave 4 passed and 2 failed, and one of the two failures was caused by this phase (finding 3).
4. **Tiny-model dry runs through the CLI** (`r1/scripts/trackp.py ... --tiny --allow-placeholders`, run dirs under `/tmp/claude-1008/trackp_review/runs/`):
   - `spike --steps 4 --examples 32` for `kev`, `laya`, `startlux` and `qwen_control` (softmax-12), plus `kev` and `qwen_control` with `--head-form cumulative11`. All exited 0 with `reload_identical: true` and `reload_max_diff: 0.0`. Each manifest carries `DRYRUN`, the paper commit `8ba6b6fe` (not dirty) and the sha256 of adapter and heads. Packing was refused on the hybrids ("linear-attention") and recorded as not implemented for Laya.
   - `toy --family kev --steps 16 --examples 64` uninterrupted, and the same run **SIGKILLed after step 5** (complete checkpoints at steps 2 and 4), then rerun. The rerun logged "resumed from … step_0000004 at step 4". The final adapter and heads safetensors are **bit-identical** to the uninterrupted run, and both reports are identical. `metrics.jsonl` logs step 5 twice (finding 5).
   - `e0 --family qwen_control --steps 4 --examples 32 --n-test 32 --with-probes --n-probe 4` exited 0. The report has `head_fit`/`lora` metrics, `pass` (false on a random tiny model, as expected), A3/A4/A5 results, and A1/A2 "model does not pack".
   - Fixed-batch overfit (`toy --examples 8 --steps 40`, so the same batch every step) on `qwen_control`: softmax-12 loss went 3.29 → 3.08 (converged). **Cumulative-11 loss went 13.14 → 11.17 and stalled** (finding 1).
   - `--check-config`: rc 1 with 30 placeholders listed. `--check-config --allow-placeholders`: rc 0.
   - Real-base runs refuse placeholders: `spike --base kev-0.8b` gives a STOP listing every `TODO_VERIFY` path (rc 2), and adding `--allow-placeholders` gives a STOP "for --tiny dry runs only" (rc 2). With a config copy where every placeholder is filled (`/tmp/.../filled.json`): `e0 --base laya --evidence EVIDENCE` gives a STOP for the missing authorization note, while **`e0 --base laya` with the default label goes past the authorization gate** and through the GPU-lease checks, and stops only at "no CUDA device" (finding 2).
5. **Independent recomputations**:
   - **Pilot table under v1:** I exported `ef3e2f3` (`git archive`, pre-change code) into TMPDIR. `offline_eval.assemble(PILOT, seed_split=True/False)` and the `evaluate()` JSON give the same sha256 with the old code and the new code (`5960856d…`, `e1e7c128…`, `b12f1f5f…`).
   - **E0 set:** `exam_synthetic.generate()` regenerates `e0_v1.jsonl.gz` byte-identically (`4f4db29b…`). The split is 3,000/1,000 and no held-out cell appears in the training split.
   - **Rule file:** `sha256sum r1/c3/rules/p3_rule_v1.yaml` matches the committed `8df1abad…f840c`.
   - **Maximum-length prompt:** a prompt at the 896-token neutral limit fits Laya's own framing (798 ids, not truncated) and the bin-token framing (883 tokens).
   - **Cumulative-11 at init:** a probe of `cumulative_probs` at random initialisation (results in finding 1).
6. **Ground rules.** All 20 commits are authored and committed by `Dowling Wong <wangdowling@gmail.com>` and end with the `Co-Authored-By: Claude …` line. On GitHub, only `trackp-20261026` (at `8ba6b6f`) is new; the worker branches `trackp-20261026-{labels,models,serialize,clients,exam}` exist only locally as worktrees in `~/r1_trackp/wt/` (housekeeping only). Nothing in the code reads the secrets file; the API keys come only from `TYPESAFE_API_KEY` / `DEEPSEEK_API_KEY` and are sent only in the request header. No `kill` or `signal` call is made on foreign processes. Everything Phase 1 wrote lives inside `~/r1_trackp` (clones, venv, `ext/` code repos, `hf_cache` with tokenizer files only, `wt/`).
7. **Side effects of my own runs, undone.** Check 4's filled-config `e0 --base laya` run took the real GPU lease path. It created `~/r1_locks/gpu0.lock` and `~/r1_trackp/runs/gpu_lease_log.jsonl` (one start/end pair, no GPU work) and ran `git fetch origin main` in the clone. That fetch changed only `FETCH_HEAD`; `origin/main` is unchanged at `b5a7aec`. I deleted both files and both directories, since neither existed before. The clone's working tree is clean apart from this review file.

## Confirmed against "Done when"

- **1.1** All wrappers (`PointerWrapper`/Kev, `LayaWrapper` and `StartLuxWrapper` under `HeadWrapper`, `BinTokenWrapper`, `ReasonThenBinWrapper`) return `belief_logits [N,12]` and `action_logit [N]`. Save → load gives bit-identical belief and action logits in both head forms. The sha256 manifest is written and a tampered heads file is refused. Laya's `_core_forward` matches `laya.common.DecisionModel.forward` line for line (checked by reading, not by a test; see finding 9). The Kev variant of `ReasonThenBinWrapper` is not built and raises, as the handoff says.
- **1.2** One template, built from what `featurize_view` reads. The spy test proves that only `budget_index`, `ledger_prefix`, `current_best` and `proposal` are read from the view, and only `ROW_FIELDS` from prefix rows. Audit, sibling and free-text fields planted on prefix rows leave the text unchanged; a future row raises `FeatureLeakError`. The length rule (896 + 128 framing reserve; drop the oldest history first) is tested under all 6 pool tokenizers.
- **1.3** RPS, CE, cost-sensitive BCE, R-A3, RPS skill, all-bins and top-1 ECE, PIT (closed form, flat for p = y, U-shape for an overconfident forecast), width ratio and disagreement rate: I re-derived each hand value in `test_trackp_losses_metrics.py`. RPS as implemented is proper: the bin-0 Brier term and the label-weighted ordinal term depend on the independent parameters p₀ and p[1:]/(1−p₀), and as an expected score it equals the outcome-RPS up to a constant. It lies in [0, 1]. Torch and numpy agree. One definition is used throughout (`exam_synthetic` imports `metrics.rps`).
- **1.4** `soft_label(..., sigma_mode="pooled_node")`: s = σ̂/√K, with σ̂ defaulting to σ_node, so 1/√K in z units (spec §3.4). Calling it with `se` under v2 is refused, so an old call cannot silently change width. Versions are recorded. The C1 table sha256 is checked. Pilot v1 is byte-identical (re-run above). `action_target` = mean Δ × keep − 0.1 σ_node, with keep from `rules.keep` under the A1 prior moments (tau floor) and the logged Δ̂ (spec §3.5). Only the existing tests' calls were made explicit (`sigma_mode="se_audit"`); no assertion was relaxed.
- **1.5** The mask is exactly M_ij = 1[j ≤ i]·1[g_j = 0 ∨ g_j = g_i] (asserted element-wise and equal to Kev's `branch_mask`). Positions use tree depth (branches restart at S). Packed = unpacked ≤ 1e-5 on a tiny full-attention model, the result is invariant to branch order, and packing is refused on hybrids.
- **1.6** Subcommands present; `sft`/`a6`/`rb` refuse. A checkpoint is written every ¼ epoch with a `COMPLETE` marker. The data order is a function of (seed, epoch). RNG, optimizer and scheduler state are restored. Resume after SIGKILL is bit-identical (re-run). The manifest has every field the runbook requires. Placeholders are refused. A CPU real-base run is a STOP.
- **1.7** The E0 grid, held-out cells, distractor fields in the real serialisation, the committed hash with byte-identical regeneration, the E0 metrics and pass, and the A1–A5 constructors and criteria all match spec §5.5–5.6.
- **1.8** The rule implements §5.7 steps 1–7. Step 4/5 is read as described in finding 11c. The rule was committed with its sha256 (`f3b976d`, before `faffd34`), and a mismatch is refused. The bootstrap is paired over instance clusters with 2,000 resamples and a fixed seed. The floor check is conservative ("no floor result" counts as a stop).
- **1.9** `POST /v1/systemone`. Only versioned `jev-x.y.z` IDs are accepted; aliases are refused. One request per (state, repeat), 3 repeats, a monotone CDF via cumulative max, and a full JSON log with the returned model. The key is redacted in the log (the test asserts the key is absent from the log). A version mismatch raises `JevVersionMismatch` after the offending response has been logged. No meta field or label reaches the request.
- **1.10** The prompt is built only from `.state` and `.proposal`. Peak windows match the runbook (weekdays 01–04 and 06–10 UTC). The returned model, prompt, output and usage are logged; the key never is.
- **1.11** `TorchLoraLoader` builds from the pin's `model` spec. `model.load` re-checks every manifest sha256. Rows without a `prompt` field are a 500, which sends the request to the unchanged A1 fallback. `write_model_pin` writes adapter, head and manifest with their sha256.

## Findings

1. **Blocking: the cumulative-11 head cannot learn (dead bins from the hard cumulative max and the clamp).**
   - Claim: handoff 1.1 says the "softmax-12 and cumulative-11 heads" are done, and the tiny spikes "both head forms: all reload-identical".
   - Observed:
     - `cumulative_probs` makes P(z > e_k) monotone with a hard `cummax`. Whenever a later sigmoid exceeds an earlier one, the bins between them get **exactly zero** mass.
     - `belief_logits_from` then returns `log(p.clamp_min(1e-6))`. A zero bin gets no gradient through the clamp, and through the `cummax` tie the two neighbouring S values cancel. Nothing can reopen such a bin.
     - At random initialisation, **65 % of bins 1–11 are dead** (256 rows, `Linear(64→11)`). Training free per-row logits directly with Adam (lr 0.05, 500 steps) on a target in bin 6 leaves **139 of 256 rows dead**, with loss 11.7 → 7.6. Softmax-12 under the same budget reaches p[bin 6] = 0.99.
     - In the real wrapper, the fixed-batch overfit of `qwen_control` stalls at 11.17 for cumulative-11, against 3.08 for softmax-12. The spikes show cumulative loss rising (kev 14.37 → 14.41, qwen 12.58 → 13.74).
     - E7 (softmax-12 vs cumulative-11) would therefore be decided by this defect, not by the head form. No test checks that either head form can learn.
   - Required fix:
     - Parametrise the thresholds so they are monotone by construction, for example S_k = σ(b − Σ_{j≤k} softplus(δ_j)). Spec §2.3's "cumulative max" then becomes a no-op guard instead of the gradient path. Alternatively initialise to ordered thresholds and use a smooth monotone map.
     - Return log-probabilities without a hard clamp floor that kills gradients (for example log of p + ε, with ε handled in the loss).
     - Add a test per head form and family: a fixed-batch overfit from random init must reduce the loss by a stated margin, and no bin with label mass may stay at 0.
     - Re-run the cumulative spikes.

2. **Blocking: the authorization-note gate fires only with `--evidence EVIDENCE`; by default a real P.3a/P.3b run needs no note, and the test of the gate cannot fail.**
   - Claim: runbook §0 and Phase 5/7 say P.3a/P.3b (and P.4–P.6) need `docs/r1/authorizations/trackp_<phase>_<date>.md`. The `trackp.py` docstring says these runs need it "unless labelled DRYRUN". The handoff says "evidence runs need their authorization note".
   - Observed:
     - `_require_authorization` checks only when `_evidence(args) == "EVIDENCE"`, and the default label is `ENGINEERING_ONLY`.
     - With a filled config, `e0 --base laya` (default label) passed the gate, took the GPU lease, and stopped only because no CUDA device was visible. On the portal with the card visible it would have run E0, an input to model selection, on a real model without a note, labelled ENGINEERING_ONLY. The same holds for `probes` and `exam`.
     - `test_evidence_runs_need_their_authorization_note` uses the shipped config, so the placeholder STOP fires before the gate: the test passes whatever the gate does. Its first assertion (`rc == 0 or "STOP" not in stderr`) also passes on a crash.
   - Required fix:
     - Require the note for every run of `e0`/`probes`/`exam` (and `sft`/`a6`/`rb`) that is not DRYRUN, as the docstring says, or forbid ENGINEERING_ONLY for those subcommands.
     - Test the gate with a temporary filled config and a monkeypatched `AUTH_DIR`, asserting refusal without a note and acceptance with one, for each label.
     - Tighten the first assertion to `rc == 0`.

3. **Blocking: a Track H test is broken by 1.11, and the baseline comparison hides it.**
   - Claim (handoff): "The after-run failing set is identical to the baseline; every new test passes."
   - Observed:
     - `r1/tests/test_c3_sidecar.py` cannot be collected in this environment (harness pin `6afdb0e` missing), so it ran in neither the baseline nor the after run.
     - Run with a stand-in for the two missing harness symbols, `test_refuses_an_adapter_whose_sha256_differs_from_the_pin` **fails**: it expects `TorchLoraLoader().load(fake pin)` to raise `NotImplementedError`, which was the old contract, and it now raises `PinError("a model pin needs files ('adapter', 'head', 'manifest') …")`. (The second failure there, `test_campaign_survives_a_dead_sidecar…`, is a `TypeError` in the harness's `run_real_campaign` signature, which is environmental.)
     - Once the harness pin reaches GitHub, this Track H acceptance test fails because of Phase 1.
   - Required fix:
     - Update that test to the new contract: a fake pin without a model spec or manifest is refused with `PinError`, and the adapter-sha256 refusal is kept.
     - Run the four modules that cannot be collected (`test_c3_direct_arms`, `test_c3_rule_controller`, `test_c3_sidecar`, `test_c3_skip_display`) with a stand-in for the missing symbols, and report per-test results before and after the change.
     - Correct the handoff sentence.

4. **Minor: the evaluation-seed guard exists but nothing calls it.**
   - Claim (handoff 1.6): "Refuses evaluation-seed columns before the P.4 final evaluation."
   - Observed:
     - `run.guard_rows` / `strip_eval_columns` are called only in their unit test. No CLI path, the `Trainer`, `exam_run` or `exam_analyze` invokes them.
     - The guard is a heuristic on top-level column names (`(^|_)eval($|_)`, `y_eval` and so on); nested keys or seed-indexed names (for example `delta_7006`) pass.
     - Today no code reads a label table, so seeds 7006–7010 are not reachable. But the guard is not yet enforced.
   - Required fix:
     - Call `guard_rows(rows, purpose=…)` inside `Trainer.__init__`, and in the one label-table reader when Phase 6 writes it.
     - Add a test that a `Trainer` (and `cmd_toy`/`cmd_e0` given a table) refuses rows that carry eval columns.
     - Reword the handoff ("guard implemented; wired into the trainer").

5. **Minor: `metrics.jsonl` duplicates steps after a resume.**
   - Observed: in my SIGKILL run (killed after step 5, last checkpoint at step 4), `metrics.jsonl` contains `step 5` twice. In real runs, with checkpoints every ¼ epoch, every step between the last checkpoint and the kill is re-logged. The CLI kill test (`test_toy_kill_and_resume…`) is racy for the same reason: a kill between a step's metrics line and its checkpoint makes the assertion fail. The parameters themselves are correct (bit-identical).
   - Required fix: on resume, drop the `metrics.jsonl` records with step greater than the checkpoint step (or tag each record with a resume attempt and de-duplicate on read). Make the test deterministic, for example with `stop_after` in a subprocess, or by asserting on the de-duplicated log.

6. **Minor: Track X detection depends on a STATUS convention nobody writes, and `gpu.lock_path` in the config is ignored.**
   - Observed: `TRACK_X_RUNNING` matches only a `## … B1|B2 … running|started|in progress` heading. `PORTAL_EXAM_RUNBOOK.md` defines no such STATUS entry; it only wraps jobs in `flock`. As written, the check fires only if Track X happens to write that heading, and a stale heading of that form would block forever. The `nvidia-smi` and `flock` checks still protect a running Track X job, so the risk is limited. `run.LOCK_PATH` is hard-coded and `config.gpu.lock_path` is unused.
   - Required fix: agree the marker with the coordinating session (for example a STATUS line `Track X evidence phase running: B1`), or treat any B1/B2 entry not followed by an "accepted/stopped/done" entry as running. Read the lock path from the config. Add a test against the agreed format.

7. **Minor: the Kev real build bypasses Kev's base-revision check.**
   - Observed: `trackp.py` `_build` calls `build_model("kev", local_path, …, revision=None, …)`. `PointerWrapper` passes that `revision` into `Meta(base_revision=…)`, and `kev.checkpoint.Checkpoint.warm_start` skips the base-revision comparison when either side is `None`. The pinned `bases.*.base_revision` is never compared with the adapter's `provenance.json`.
   - Required fix: pass the config `base_revision` as the `Meta` base revision, separately from the Hub download revision (which is moot for a local path), and test the refusal on a mismatched revision with a tiny checkpoint.

8. **Minor: save/load integrity has gaps.**
   - Observed: `_Wrapper.load` verifies only the files listed in the manifest, then loads `adapter/adapter_model.safetensors` and `heads.safetensors` whether or not they are listed. A manifest edited to drop an entry bypasses the check. `set_peft_model_state_dict` missing keys are not checked (only unexpected keys), so a partial adapter would load silently with LoRA weights at their initial values.
   - Required fix: require both files in the manifest, refuse missing LoRA keys, and add a test for each case.

9. **Minor: Laya readout has no parity test.**
   - Observed: `LayaWrapper._core_forward` re-implements `laya.common.DecisionModel.forward` up to the scorer, to also return the [CLS] state. It matches the pinned `a478221` by reading, but nothing guards against drift, and E1 zero-shot uses this path.
   - Required fix: a test that the wrapper's native logits equal `core(ids, att, marker_pos, marker_mask, qtype)[0]` on the tiny model.

10. **Minor: client error handling.**
    - Observed: `JevVersionMismatch` subclasses `JevError`, so a caller that retries or skips on `JevError` would swallow the STOP. In both clients, a non-HTTP failure (timeout, `URLError`) raises before any log record is written, so the "full log" misses those calls.
    - Required fix: make the mismatch its own exception, not a `JevError`, or document and test that runners re-raise it. Log a record for transport failures too.

11. **Minor (author decisions needed before P.3/P.4; no code defect beyond what is listed).** These are already listed in the handoff as Q1–Q3. They change the loss, the exam metric and the frozen rule, so they must be settled, with a PLAN row, before the rule's sha256 is recorded in PLAN (Phase 6c) and before any evidence run:
    - a. **RPS normalisation.** Spec §6.1 says Σ_k (P_k − Y_k)² plus the bin-0 Brier term; the code uses 0.5·(Brier₀ + (1−y₀)·mean_k (Q_k − R_k)²) on renormalised non-inert parts. This changes the relative weight of bin 0 against the ordinal part by up to 10×, and adds the (1 − y₀) weighting.
    - b. **10 finite edges, not 11.** Both `labels.EDGES` and spec §3.3 have 10 interior edges. The Jev rung adds an 11th "inert" question that R1-JEV-RUNG does not mention.
    - c. **Exam rule, steps 4–5.** Finalist 1 is the first of the tied set after the tie-breaks, which may differ from the E3 top. Spec step 5 says "the top model".

12. **Info (no fix required in Phase 1).**
    - StartLux runs on a transformers 5.19 port of the bidirectional mask; comparison with the 5.8 reference is deferred to Phase 3 (handoff Q4).
    - Kev's own pin (torch < 2.9) conflicts with the venv's torch 2.14.1.
    - The online controller does not yet attach `row["prompt"]`, so a real sidecar answers every row with A1 (handoff deviation 7, Track H follow-up).
    - The five worker worktrees and local branches in `~/r1_trackp/wt/` can be removed after merge.

Verdict: pending fixes (blocking: 1, 2, 3; minor: 4–11).


## Implementation agent's response (26 Oct)

Commits `ca5165e` (finding 1) and `5115232` (findings 2–10); handoff updated.

1. Fixed. `cumulative_probs`: logit S_1 = raw₁, logit S_{k+1} = logit S_k − softplus(raw_{k+1}) (monotone by construction; cummax kept as an identity guard); `belief_logits_from` returns log(p + 1e-12), no clamp. New tests: `test_head_forms_can_learn_from_free_logits[softmax12|cumulative11]` (fails on the old code — checked by stashing the fix — passes now), `test_every_family_and_head_form_learns_a_fixed_batch` (kev/laya/startlux/qwen_control × both forms: loss falls, every bin > 0). Tiny cumulative spikes re-run: loss falls in all four families (kev 5.86→4.92, laya 9.37→8.15, startlux 7.72→6.71, qwen_control 6.66→5.79), reload identical.
2. Fixed. `_require_authorization`: every `e0`/`probes`/`exam`/`sft`/`a6`/`rb` run not labelled DRYRUN needs its note. `test_authorization_gate_for_every_non_dryrun_label` calls the gate in-process with a monkeypatched `AUTH_DIR` for every subcommand × label, with and without a note; the CLI test now asserts a `--tiny` run succeeds with rc 0 and is labelled DRYRUN.
3. Fixed. `test_c3_sidecar.py` updated to the 1.11 contract (`PinError`, "model pin needs"). Before/after per-test results of the uncollectable modules with a stand-in for the missing symbols: `docs/r1/overnight/trackp_code_20261026/trackh_modules_before_after.txt` (stand-in committed beside it). The only Phase-1 difference was that test; with the update it passes (5/6 in the module; the other failure is the harness `run_real_campaign(skip_display=)` signature). Handoff sentence corrected. `test_c3_skip_display` cannot be collected even with the stand-in (needs `SKIP_DISPLAY_TEXT` and more); Phase 1 touches nothing it imports.
4. Fixed. `Trainer.__init__` calls `guard_rows(rows, purpose=...)`; the guard scans nested keys and DecisionPrompt `meta`, and seed-indexed names 7006–7010; `test_trainer_refuses_evaluation_seed_fields`. The label-table reader (Phase 6) will call it as well.
5. Fixed. `Trainer.resume` drops metrics records after the checkpoint step; `test_steps_after_the_checkpoint_are_logged_once_after_resume`; the CLI kill test now runs 40 steps and asserts each step logged exactly once.
6. Fixed as far as possible without the coordinating session: the newest STATUS heading naming Track X/exam B1/B2 decides (running/started/launched/in progress vs accepted/stopped/done/complete/finished); proposed marker documented in `run.py` and put to the author (handoff Q6); `gpu.lock_path` from the config is used; test `test_track_x_status_reading_uses_the_newest_b1_b2_heading`.
7. Fixed. `PointerWrapper(base_revision=...)` feeds `Meta.base_revision`; `trackp.py` passes the config's `base_revision`; `test_pointer_wrapper_refuses_a_checkpoint_of_another_base_revision`.
8. Fixed. `load` requires adapter and heads in the manifest and refuses an adapter missing any key of the wrapper's peft state dict; both cases tested in every round trip.
9. Fixed. `test_laya_native_readout_equals_layas_own_forward` (atol 1e-5).
10. Fixed. `JevVersionMismatch` is no longer a `JevError`; transport failures (URLError/timeout/OSError) are logged before raising in both clients; tests.
11. Recorded as author questions (handoff Q1–Q3); no code change.
