# Review: Track P implementation of the author's decisions of 26 Oct 2026

AI-assisted. Independent reviewer (Claude, separate session from the executing Track P agent; makes no fixes).
Scope: `git diff 6f67717 86404c7` on `trackp-20261026` — `0b12d15` (PLAN / spec), `d0b7b33` (code), `86404c7` (DRYRUN
driver, Track H evidence) — plus the merge `70b7580` (origin/main into the branch), checked only for what Track P relies
on. The running E0 v2 DRYRUN (`runs/p5_e0v2_dryrun/`) and its results are not reviewed. CPU only; no GPU used.

Tests run here (venv `trackp-cpu`, HF_HOME set, at `70b7580`): `r1/tests/test_trackp_*.py` **187 passed**; the four
Track H modules (`test_c3_direct_arms`, `test_c3_rule_controller`, `test_c3_sidecar`, `test_c3_skip_display`) **29 passed**
(harness checkout at `6afdb0e`). Throwaway probes in `/tmp/claude-1008/rv/` (fp32 token rows on a bf16 tiny Qwen; A3
budget on the real pool tokenizers).

## Findings

1. **blocking — The frozen selection rule still applies the withdrawn E0 v1 criterion.**
   `r1/c3/rules/p3_rule_v1.yaml` (`e0_pass: width_slope_min 0.7, mean_slope_min 0.8`) and
   `r1/c3/train/exam_analyze.py:114-117` (`_step1` checks `e0["width_slope"]`, the slope vs s) are unchanged. The spec
   (§5.5: "the v1 thresholds … no longer apply") and PLAN R1-E0-PROTOCOL replace that criterion with the slope against the
   label's own std and thresholds the author has not yet set, but nothing in PLAN, the spec or the code says that the
   frozen rule must be replaced. As it stands, P.3b analysis would disqualify models in step 1 using a criterion the author
   withdrew, on the wrong metric. Step 4 of the rule (`tie_breaks`, `_order_key`) already matches R1-TIEBREAK and needs no
   change. Fix: note in spec §5.7 (and in the R1-E0-PROTOCOL row or the report) that a `p3_rule_v2.yaml` with the v2 E0 metric
   (`width_slope_vs_label`, `mean_slope`) and the author's E0/A4 thresholds is committed, with its sha256, after the author's
   threshold row and before any P.3b data; until then make `exam_analyze` refuse (e.g. refuse E0 records not produced by
   `trackp_e0/v2`, or refuse rule v1's `e0_pass`).

2. **minor — Readings made by the Track P agent appear in the author's decision rows and spec text without being marked as such.**
   The PLAN block (`docs/r1/PLAN.md:505-520`) is headed "Fixed, not proposals", but it and the spec include points the author did not decide:
   - R1-TOKEN-INIT (`PLAN.md:516`): "at a lower lr **than the new heads**". The author said only "a lower lr". The value chosen,
     `token_lr = 1e-4` (`trackp_portal.json:99-100`), is lower than the heads (1e-3) but equal to or higher than every
     adapter lr in the grid (1e-5, 3e-5, 1e-4). The config flags the value as the agent's choice; the PLAN row does not.
   - R1-TEMPERATURE (`PLAN.md:515`): "(E5 and later)" was added by the agent. The E1 zero-shot path still applies Kev's released T
     (`native_temperature=True`).
   - Spec §4 (`TRACK_P_POST_TRAINING.md:190`): the grid also applies to "(and released heads)".
   - Spec §5.6 A4 (`:281`): the criterion form "non-decreasing wherever the label's std increases" (and `a4_pass_v2`).
   - E0: `eval_every 100` and `patience 5` (flagged in the config only); "at most 2,000 steps" applied **per stage**: the
     head fit and the LoRA stage each get up to 2,000, so up to 4,000 in total (`exam_run.py:195-213`); the lr picked on
     the fresh soft run is reused for the hard-label and native runs (`driver.sh`), with no grid of their own; the validation
     cells chosen (`VAL_CELLS`, including the m-edge cells (0,3), (9,3)).
   - R1-STARTLUX-TRAINABLE (`PLAN.md:507`): the sentence about the `author_rung: trainable` input field.
   These readings are reasonable. Fix: mark each one "(Track P agent reading; author to confirm)" in the rows and the
   spec, or move them to a list in the DRYRUN report for the author, so that the PLAN rows contain only what the author said.

3. **minor — Early-stopping state can disagree with `best/` after a resume.** `trainer.py:170-185` writes `best/` and
   `best.json` at every improving evaluation, but `self.best` is persisted only in step checkpoints (`:269`). With the E0
   sizes (≈ 2,700 training rows, batch 8) checkpoints fall every ≈ 84 steps and evaluations every 100, so a crash between
   an improving evaluation and the next checkpoint resumes with an older `self.best` while `best/` already holds the newer model.
   On a non-deterministic GPU replay, a later evaluation that is worse than `best/` but better than the rolled-back value
   overwrites `best/`. Otherwise the final `model.load(best/)` returns a model whose step differs from the `best_step`
   that is reported. The test covers resume only after a stop that wrote a checkpoint. Fix: write a checkpoint (or at
   least persist `self.best` in the step state) whenever an evaluation improves, or on resume take `self.best` from
   `best.json` and check it against a step tag stored in `best/`.

4. **minor — The LoRA stage never evaluates its starting point.** In `e0_v2` the Trainer's first evaluation is at step
   `eval_every`. The stage-1 (head-fit) model is never a candidate, so if LoRA only hurts, the "best" LoRA checkpoint is
   worse than the model it started from. `out["pass"]` (and `e0-select`) use the LoRA result only. Fix: evaluate at step 0
   (start `best` with the stage-1 val RPS and save `best/` before the first step), or state explicitly that E0 is judged
   on the LoRA stage even when it is worse.

5. **minor — Environment pins are recorded but neither enforced nor logged per run.** R1-ENV-PIN says "pin it". Torch
   `2.6.0+cu124` and Kev @ `2074cc4` appear only as text in `trackp_portal.json` (`venv.torch_pin`, `code_pins`).
   `run.run_manifest` records neither the torch version nor the kev / laya / startlux code commits, and nothing checks them at
   start. Fix: in `trackp.py` (non-tiny) refuse unless `torch.__version__ == "2.6.0+cu124"` and the installed kev
   (`direct_url.json` commit) equals `code_pins.kev`, and write both, plus the laya / startlux commits, into every manifest.

6. **minor — The Kev pin record is inconsistent.** `docs/r1/reports/trackp_phase2_20261026/kev_diff_vs_kev-1.0.txt:3` says
   "commits between: 1". This is an artefact of the shallow clone in `ext/kev`: `2074cc4` has no parent locally,
   `git merge-base kev-1.0 2074cc4` fails, and `git rev-list 2074cc4..kev-1.0` counts 327. `trackp_portal.json:169` says "23
   commits after the kev-1.0 tag" and points to a non-existent `docs/r1/reports/trackp_env_pins_20261026/`. The tree diff
   in the `.txt` / `.patch` files is valid. Fix: deepen the clone, record the true ancestry and commit count (or say that
   it is unknown in a shallow clone), and correct the path to `trackp_phase2_20261026/`.

7. **minor — Stale "11 yes/no questions".** `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md:60` (step 1.9, Jev client) still
   says 11 questions per state. Correct it to 10 (R1-EDGES-10).

8. **minor — A3 levels are coarse and the fraction actually reached is not reported.** `a3_probe_budget`
   (`exam_synthetic.py:396-432`) adds history in whole lines of ≈ 25–40 tokens. On the real pool tokenizers (my probe,
   n = 8, budgets 270–437 tokens) the 25 % level reaches ≈ 16–18 % of the budget (prompt 0: 0.16 / 0.48 / 0.93 for the 0.25 /
   0.5 / 1.0 levels). `probes` reports only the maximum tokens per level. Fix: report the fraction reached per level
   (mean / min over prompts), and/or trim the last line at token level so that each level lands closer to its target.

9. **minor — The Track H evidence predates the code commit and the merge.** `trackh_modules_at_6afdb0e.txt` ran on
   `6f67717` + an uncommitted tree. After the merge `r1/scripts/HARNESS_PIN_C3` is `897d83c` (origin/r1), while the
   harness checkout is `6afdb0e`; `6afdb0e` is an ancestor of `origin/r1`, so the author's condition "on GitHub" holds.
   My re-run at `70b7580` with the harness at `6afdb0e` passed (29/29). Fix: re-run the four modules at the branch head
   with the harness at the pin the branch now carries (or record why `6afdb0e` remains Track P's harness), and commit that
   output.

10. **minor — Small asymmetry in the "fresh head for every model" run.** In the fresh (`linear12`) variant the Qwen
    control still trains its 14 new token rows (`token_row_parameters`, at `token_lr`), because the bin tokens appear in
    its input listing. No other family gets extra trainable input rows. This is probably harmless, but it should be stated in
    the report, or the rows frozen for the fresh variant.

## Checked and found correct

- **E0 (a):** `width_slope_vs_label` regresses the predicted std on the std of the soft label `y_soft`, computed with the
  same `belief_moments` bin representatives. This is also used for the hard-label run, which is the right reference.
  `label_ceiling` reports the label's own slope vs s (and vs m). A test confirms slope 1 for the labels themselves and
  the ceiling equal to the labels' slope vs s. A4: `a4_label_std` rebuilds the same A4 prompts (same n / seed) and
  `a4_pass_v2` uses that reference. The v1 numbers are still reported. `e0_pass_v2` returns None until the author sets
  thresholds, so no threshold was invented.
- **E0 (b):** `VAL_CELLS` are disjoint from `HELDOUT`, and `e0_split` takes them only from the train split (tested).
  Early stopping on val RPS in both stages; `fit_head_on_states` and the Trainer restore the best state. A resume after an
  exhausted patience does not train further (`exhausted()` check, tested). The same `max_steps`, `eval_every`, `patience`
  and batch for every base come from one config block; the cosine schedule runs over `max_steps` for every model.
- **E0 (c):** `linear12` = LayerNorm + Linear(hidden → 12) on the readout state the action head reads, for all four
  families (Kev `<decide>` state; Laya mean-pooled encoder output; StartLux last valid token; Qwen belief position).
  It is fitted at `head_lr` 1e-3 in both stages and is in `new_head_parameters`. Released / native readouts run separately
  (`--variant native`: zero-shot, then LoRA).
- **Frozen-feature fit:** states are cached in `eval()` under `no_grad`. This equals a frozen-backbone fit with the
  backbone in eval mode. For Kev (released LoRA with nonzero B, dropout 0.05) a train-mode fit would add dropout noise, so
  eval mode is the right reading. The pool configs have no other dropout.
- **A3 budget:** limit 1,024 = Laya's `max_len` and the Kev wrapper's `max_state` (Kev's row limit is 1,664 at that
  state limit, so the total-length cap is conservative). The counters reproduce each wrapper's input: Kev `km.encode` of
  the same record (`load_tokenizer` = `AutoTokenizer` of the base); Laya `encode` without truncation (raises if it
  truncates); StartLux `prompt_text` with chat framing, `add_special_tokens=False` as in `forward`; Qwen `segments(p)[0]`
  including the bin-token listing and suffix. On real tokenizers every level stays ≤ 1,024 for every family and Laya does
  not truncate at the 100 % level. 2k / 8k are descriptive only (`pass` forced to None).
- **Token rows:** the mean of existing rows uses ids < `len(tokenizer)` excluding the new ids, so the padding rows of the
  248,320-row matrix are excluded. The probe on a bf16 model shows the delta is fp32, the gradient reaches it in fp32, the
  input path uses peft's `.to(W)` cast, and the LM-head readout reads the fp32 rows. The rows form a separate optimizer group
  at `token_lr`, disjoint from the heads.
- **lr grid:** `e0` refuses an lr outside `lr_grid`; `e0-select` requires exactly one run per grid lr of one base / variant /
  target and picks the lowest best val RPS.
- **RPS:** `losses.rps` / `metrics.rps` are the mean of 10 cumulative terms over bins 1–11, i.e. 1/(K−1) with K = 11. The
  code is unchanged, and the spec now documents the ½(Brier₀ + (1−y₀)·ordinal) combination that is already implemented.
- **10 edges / Jev:** the inert question is removed; 10 edge questions; `bins_from_answers` gives bins 1–11 from the 10
  CDF values and bin 0 = 0. `cumulative11` = 1 + 10 outputs. The spec text is corrected.
- **Exam step 4:** `_order_key` = (−E2 skill, |width ratio − 1|, base before instruct, cost), applied only to the tied set.
  The rule file and `exam_analyze` already implement R1-TIEBREAK; the rule's sha256 is unchanged and verifies.
- **Track X marker:** `gpu_lease` refuses if `~/r1_locks/trackx_evidence.active` exists, both before taking the flock and
  again under it, and logs that the marker was absent. STATUS stays as a second check, and every GPU step of `driver.sh`
  goes through `trackp.py`. This matches main's R1-PORTAL-SCHEDULE amendment in effect (the check lives in `gpu_lease`
  rather than in `track_x_running`).
- **StartLux:** licence noted in the registry entries (0.8B / 2B / 4B) and in the spec. Rule v1 still lists StartLux under
  `pending_author_families`; it is admitted with `author_rung: trainable`, which the PLAN row now authorises.
- **Merge `70b7580`:** no Track P file was changed except docs (PLAN rows added above the Track P block; the portal runbook
  card schedule now names the marker). The change to `dataset.py` (`refuse_exam`) is not on the Track P import path. All
  Track P tests pass after the merge.
- **No relaxation:** no other acceptance criterion or pinned value was changed (RL gate, E3 budget, E4 limits, A1 / A2 /
  A3 / A5 criteria, revisions and sha256 untouched). The v1 E0 / A4 thresholds are withdrawn only where the author said
  so.

Verdict: changes required

## Re-check of the fixes (`70b7580..8e13e77`)

Same reviewer, same rules: CPU only, no GPU, no edits except this file. Tests at `8e13e77`: `r1/tests/test_trackp_*.py`
**190 passed**. The four Track H modules: **29 passed**, harness clone at `897d83c` (= `HARNESS_PIN_C3`).

1. **Resolved.** `analyze` raises `RuleSuperseded` for any E0 record that does not declare `trackp_e0/v1`, including
   records with no protocol field, so v2 results cannot be judged by the withdrawn thresholds (test added). Spec §9
   records that `p3_rule_v2.yaml` must be committed, sha256-frozen, before any P.3b data, with the author's thresholds
   and StartLux no longer pending. The v1 rule file and its sha256 are untouched.
2. **Partly resolved — minor, still open.** The agent's choices are now listed in a note under the PLAN rows and marked
   in spec §4, §5.5 and §5.6. "(E5 and later)" is removed, and the StartLux sentence is marked as an implementation note.
   One reading is still in the author's wording: R1-TOKEN-INIT (`PLAN.md:516`) and spec §2.2 (`TRACK_P_POST_TRAINING.md:77`)
   say "at a lower lr **than the new heads**", but the author said only "at a lower lr". Note item (1) covers the
   value, 1e-4, but not that "lower" is measured against the heads rather than the adapter. Fix: drop "than the new heads"
   from the row and from §2.2, or mark it "(Track P agent's reading)".
3. **Resolved.** When early stopping is on, a step checkpoint is now written at every evaluation, so the early-stopping
   state and `best/` can disagree only if the process dies between renaming `best/` and finishing that same step's
   checkpoint. On resume that step is replayed and re-evaluated. Note, not a finding: the `best.json` re-sync in
   `resume()` (`trainer.py:207-211`) needs `best.json`'s step ≤ the checkpoint step and different from the checkpointed
   best. Checkpoints now follow every evaluation, so that case cannot arise and the branch is effectively dead code.
   If it ever ran, it would reset `bad` to 0. It is harmless, but could be removed.
4. **Resolved.** The starting model is evaluated at step 0 and is an early-stopping candidate; a run that never improves
   returns it (test). In E0 the LoRA stage's step 0 is the head-fit model.
5. **Resolved.**
   - `check_environment` stops real `spike` / `toy` / `e0` / `probes` runs when torch or a pip-recorded code commit
     differs from the config, or when the imported checkout is at another commit or has a dirty tree.
   - Every manifest now carries `environment_record()`.
   - In the GPU venv (imports only, with CUDA hidden), torch `2.6.0+cu124` and the commits of kev, laya and
     startlux_decide all match their pins, and the check passes. `peft` came back null only because that venv cannot
     import peft with CUDA hidden, a known limit of this probe.
6. **Resolved.** `ext/kev` is no longer shallow. I confirmed `rev-list kev-1.0..2074cc4` = 23 and
   `2074cc4..kev-1.0` = 0, so the tag is an ancestor of the pin; the checkout sits at `2074cc4` with a clean tree. The
   diff file is regenerated and the config path is corrected.
7. **Resolved.** Runbook 1.9 now says 10 questions.
8. **Resolved.** Levels are now filled to the word, and every level is checked against its cap. On the real pool
   tokenizers (my probe, n = 8) the fraction of the budget reached is 0.233–0.247, 0.48–0.50 and 0.985–1.00 for the
   0.25 / 0.5 / 1.0 levels. Every level stays ≤ 1,024 tokens for every family, and Laya does not truncate. `probes`
   reports `budget_fraction_reached_min_mean`.
9. **Resolved.** `trackh_modules.txt` ran at harness `897d83c` (= the pin) and gives 29/29. Its header reads "paper
   9365ab4 … clean: 1 changes", which contradicts itself; `8e13e77` adds only report files, and my own re-run at `8e13e77`
   also passed. The five full-suite failures are recorded as also failing on `origin/main`; I did not re-check them.
10. **Resolved.** The fresh variant freezes the Qwen token rows and reports `frozen_token_rows`.

Verdict: changes required

## Second re-check (`8e13e77..a2859b3`): finding 2 and the E0 v2 DRYRUN report

Same reviewer and rules: CPU only, no GPU job, no edits except this file. I checked
`docs/r1/reports/TRACKP_E0V2_DRYRUN_20261026.md` against the raw run directories in `~/r1_trackp/runs/p5_e0v2_dryrun/`
and the lease log. My recomputation script is `/tmp/claude-1008/rv/recompute.py`.

**Finding 2: closed.** "Lower than what is not stated; the Track P agent reads it as lower than the new heads' 1e-3 and
uses 1e-4 — author to confirm" now stands in PLAN R1-TOKEN-INIT (`PLAN.md:516`) and in spec §2.2 and §4. The
`trackh_modules.txt` header nit is fixed.

**DRYRUN report: what checks out**
- **Copied evidence.** Every top-level `report.json` / `manifest.json` under `runs/` is byte-identical to the raw run
  directories. The curves are copied too.
- **E0 numbers.** I recomputed every E0 table row from `pred_test_{head_fit,lora}.npy` with `e0_metrics_v2` on the 1,000
  test items. RPS, width slope against the label's std, width slope against s, mean slope and width ratio all match
  `report.json`, with a maximum difference of 0. The ceiling is 0.925 and the label's mean slope is 1.029. The v1
  criterion 0.7 / 0.925 is 0.76.
- **Selection and claims.**
  - `e0-select` picked lr 1e-4 for both bases, the lowest best val RPS.
  - Every soft LoRA run has its best step at 1,700–2,000 and ran to 2,000; Kev at 1e-5 is best at 2,000.
  - The step-0 model was never selected.
  - The hard runs are best at step 100 and stopped at 600, with width ratio 0.27 / 0.20.
  - The head-fit rows are identical across the lr runs.
  - The Qwen fresh runs report `frozen_token_rows: true`.
  - Claims 2–5 of "What the numbers say" follow from these data.
- **E6.**
  - A3: ΔRPS is 2.1–2.9e-5 (Kev) and 2.5–2.6e-5 (Qwen). The budget fraction reached is 0.24 (min 0.23), 0.49 (0.48) and
    1.00 (0.98). The budget runs 194–496 tokens, mean 374. Maximum tokens per family: StartLux 830 → 1,024, Kev 965,
    Qwen 980, Laya 871.
  - Kev's 2k / 8k levels end in `ContextOverflow` (2,383 / 8,400).
  - A4 v2 is 1.00 for both bases, with median slopes 1.04 / 1.05.
  - A5 max TV is 0.20, against the unchanged spec criterion.
- **Attempts.** The smoke manifests are at a clean `70b7580`. The aborted run stopped after 15 evaluations (1,500
  steps), and its lease has no end record.
- **GPU use.** The 12 DRYRUN jobs from the manifests total 3.66 h; with the 2 smoke jobs that makes 14 jobs and 3.69 h,
  09:33–13:49 UTC, which matches the lease log. The aborted job ran from 09:35:51 until the restart at 10:08:26
  (≈ 0.5 h).
- **Environment.** Every manifest records torch 2.6.0+cu124, peft 0.21.2, and kev / laya / startlux_decide at
  `2074cc4` / `a478221` / `a99977d`. The harness is `897d83c`, clean. The evidence label is DRYRUN; the Track X marker
  was absent at every start.
- **Reserved items.** The report sets no E0 or A4 threshold and gives no E0 / A4 verdict (`pass: null`). It leaves the
  budget, the head-fit and A5 readings and the Phase 5 authorization to the author. A3 and A5 are judged against the
  spec's unchanged criteria, which is allowed.

**New findings**

R2-1. **minor — The "clean tree" claim is contradicted by the manifests.** The report ("All runs are at commit `8e13e77`
(clean tree …)") and STATUS imply a clean tree. All 14 manifests record `git.paper.dirty: true`. That flag comes from
`git status` when the manifest is written at the end of each job, and every one of those jobs ended at or after
10:33Z. The likely cause is this reviewer's uncommitted append of the first re-check section to the tracked review file
(mtime ≈ 10:17Z); `8e13e77..a2859b3` changes only docs, and no code file differs. Fix: state that the manifests show
`dirty: true` and give the likely cause (a docs-only change to the tracked review file; code identical to `8e13e77`).
Optionally, record `git status --porcelain` names in `git_commit` from now on, so that the cause of a dirty flag is
recorded in the manifest itself.

R2-2. **minor — "No width information in the frozen backbone" is overclaimed.** "What the numbers say" item 1 says
the frozen backbone "carries no width information through a linear head", and STATUS says the head fit "learns no
width". But the head fit had not converged. Qwen's head-fit val RPS was still falling at the cap (best at 2,000;
0.0383 → 0.0365 over the last 400 steps), and Kev's was close to it (best at 1,600; 0.0493 → 0.0488). Head-fit test RPS
is 0.034–0.043, against ≈ 0.0002 after LoRA. The data support only "within the 2,000-step head fit, which was still
improving, the linear head recovered no width". Fix: reword item 1 and STATUS, and add the head fit to item 3 and to
question 3 for the author. The question of reporting the head fit only descriptively rests on this reading.

R2-3. **minor (nits).**
- The protocol section says 2,700 train / 300 val; `e0_split` gives 2,714 / 286.
- Kev's best val RPS at lr 1e-4 is 4.5e-5, not 4e-5.

Verdict: changes required — every finding of the decisions review is now closed, including finding 2. Three minor
findings on the DRYRUN report (R2-1 to R2-3) remain.

## Final re-check (`a2859b3..b4f7107`)

- **R2-1: the report is resolved, but the new code has a bug (minor).** The report and STATUS now state that the
  manifests are dirty, give the cause, and show that `git diff 8e13e77 a2859b3 -- r1` is empty; I confirmed that diff is
  empty. But the new `dirty_files` in `run.git_commit` (`r1/c3/train/run.py:199-200`) is computed from `g(...)`, which
  `.strip()`s the whole `git status --porcelain` output. That removes the leading space of the first line's status
  field, so `ln[3:]` cuts the first character off the first file name. On a throwaway repo with two modified files,
  `abc.txt` and `def.txt`, it returns `['bc.txt', 'def.txt']`. Fix: parse the raw output without stripping (e.g.
  `subprocess.run([... "status", "--porcelain", "-z", "--untracked-files=no"])`, split on NUL), and add a test with an
  unstaged change.
- **R2-2: resolved.** Item 1 now says the head fit learned no width within 2,000 steps, had not converged, and that this
  does not show the frozen features carry no width information. Item 3 covers the head fit, question 3 asks about its
  budget, and STATUS is reworded to match.
- **R2-3: resolved.** The report now says 2,714 / 286 and 4.5e-5.

Verdict: changes required — one minor bug remains (`dirty_files` drops the first character of the first file name).
Everything else in the decisions review, the re-checks and the DRYRUN report is closed.
