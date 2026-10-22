# C3 preparation batch (22 Oct 2026) — handoff

**ENGINEERING_ONLY (code, configs, DRYRUN) and PILOT (numbers on old data). AI-assisted (Claude), implementation agent.** Nothing here is evidence. Branch `c3-prep-22oct` (worktree `.claude-worktrees/c3-prep-22oct`), based on `main` @ `259db53`. Not merged, not pushed. `docs/r1/PLAN.md` and `docs/r1/STATUS.md` untouched. No LLM, Ollama, GPU, SSH or network use; CPU and file-only work. The harness repository was not changed.

## Commits (oldest first)

| Commit | Content |
|---|---|
| `0ff33b4` | Tasks 1, 2, 5: gate at the declared g only; freed-run sensitivity; audit K = 10 and explicit seed split |
| `e7adebe` | Task 3: no-op kinds, `r1/c3/duplicate_report.py`, pilot report |
| `4b87b85` | Task 4: audited-outcome mode in `r1/diagnostics/di_test.py` |
| `79e88d3` | Task 6: `r1/scripts/paper_a_status.py` + Ada config + tests |
| `c1df6d9` | Task 7: `r1/scripts/configs/c3_sweep_ada.json`, runner `audit` / `nodes_pending` keys, `--check-config`, dry run `--base-config`, DRYRUN record |
| (this file) | Handoff |

## Tests

Command: `python -m pytest -q r1/tests -p no:cacheprovider --deselect r1/tests/test_rerun2_batch4c.py::test_real_runner_desktop_dryrun` (venv313 first on PATH, `AR_HARNESS_ROOT` = harness checkout).

- Baseline on `259db53` in this worktree: **248 passed** (98.6 s).
- Final on this branch: **288 passed, 1 deselected** (112.6 s). Nothing that passed before fails. +40 new tests: `test_c3_arms_eval.py` (+3: declared g / single gate, freed-run unit test, freed-run next to primary; 2 rewritten), `test_c3_audit.py` (+4), `test_c3_duplicate_report.py` (4, new), `test_di_test.py` (+4), `test_paper_a_status.py` (21, new), `test_c3_label_sweep.py` (+4).

## Task 1 — gate at the declared g only (`r1/c3/offline_eval.py`)

- Constants: `G_PRIMARY = 0.1`, `G_SENSITIVITY = (0.05, 0.2)`, `G_EVAL = (0.1, 0.05, 0.2)` (σ_node units), `G_THEORY = 0.0`, `GATE_MIN_NODES = 2`. `G_GRID` is gone.
- `evaluate(rows, mode, k, g_values=G_EVAL, noise)` computes exactly the declared values and **refuses any other g** (`ValueError`; stricter than asked, so that no grid can be re-introduced through the API). Output: `values[g]` with `role` (`primary` / `sensitivity`), per-arm values, `A3_minus_A2` (gain per 20, CI, δ_n — no verdict), `freed_run_sensitivity`, plus `g_declaration`, `run_accounting`, `scores`, `theory_checks`. No `pass`/`verdict` field anywhere in `evaluate` output (tested).
- `gate_verdict(evaluation)` is the only function that produces a verdict: g = 0.1, primary accounting, per node `meets_node_criterion` (gain ≥ δ_n and lower 95 % bound > 0), `pass` iff ≥ 2 nodes, `verdict` "pass"/"fail". The CLI computes it on the **instance** split only and puts it at the top level (`gate`); LONO is reported without a verdict (choice: C3_DESIGN §6's gate is the in-distribution comparison; LONO is H2b).
- `sensitivity_view` reports 0.05 and 0.2 (gain, CI, δ_n) with no pass/fail field, plus the freed-run numbers at every g.
- g = 0 is used only in `theory_checks` (Proposition 7 realised threshold gain), labelled in a `note`. Proposition 8 now uses the declared g values (was 0.05/0.1/0.2 already).
- `--no-seed-split` kept. The CLI prints `{"gate_verdict", "g_sigma_units", "split", "seed_split", "nodes": {gain, ci95, delta_n, meets}}`.
- Check: on the 19 Oct split-recheck table and audits, the primary gains and CIs at 0.05/0.1/0.2 are **identical** to the committed `c3_split_recheck_20261019/offline_eval.json` (`per_g`).

## Task 2 — run accounting (`offline_eval.py`, `RUN_ACCOUNTING`)

- **Ledger investigation (confirmed):** every root ledger has exactly W rows (DT4: 12 × 20; rerun-2 arm A: 54 × 20; liveness: 8 × 10), `budget_index` contiguous 1..W, `cumulative_budget_consumed == budget_index` on every row (0 mismatches), no `skipped` rows; the liveness events show exactly one `llm_call` / `proposal_created` per trial (80/80). One logged proposal = one run; there is no logged proposal after the last run. A literal replay that hands freed runs to later logged proposals therefore cannot spend them.
- **Primary (unchanged):** `skip_credited_at_g` — r = Δ·keep − g·execute, a skip scores 0, freed runs not re-spent, per-20 = 20 × weighted mean per logged proposal. Stated in the module docstring and in the JSON (`run_accounting`).
- **Sensitivity implemented by this agent:** `freed_run_exchangeable` — each freed run credited with the arm's held-out mean reward per executed proposal (per-20 = 20 × that mean). It scales with 1/exec-rate and inflated the pilot differences (digits +0.039).
- **Revised in acceptance by the coordinating session (Claude), 22 Oct:** replaced by `freed_run_call_cap`. Freed runs are re-spent on further proposals exchangeable with the arm's own, under a cap of c × W LLM proposals per campaign: value = m × min(W, e·c·W), with m the mean reward per executed proposal and e the execution rate. c = 1 equals the primary accounting exactly; reported sensitivities are c = 2 (realistic) and c = ∞ (this agent's original variant, kept as an optimistic upper bound). Functions: `capped_value`, `cluster_boot_capped_diff`; output under `values[g].freed_run_sensitivity.A3_minus_A2[node].by_call_cap`. Tests updated.
- **Deviation from PLAN wording (for the PLAN row):** PLAN §10 "Run accounting (22 Oct)" says the sensitivity "gives each freed run to the next logged proposal of the same campaign". Root ledgers hold exactly one proposal per run (W rows; budget index = cumulative budget), so no logged proposal exists beyond the end of a campaign; a literal replay cannot spend freed runs. The PLAN row is corrected to the call-cap form.

PILOT numbers at 0.1σ after the revision (A3 − A2 per 20): primary digits +0.0051, tabular +0.0016, breast-w −0.0006; call cap c = 2: digits +0.0103 [0.0037, 0.0172], tabular +0.0033 [−0.0017, 0.0073], breast-w −0.0012 [−0.0021, −0.0005]; c = ∞: digits +0.039, tabular +0.002, breast-w −0.0078.

Original agent text follows.

PILOT numbers (19 Oct split-recheck table + audits, seed split, instance cross-fit; ENGINEERING_ONLY, not a gate decision): primary gate at 0.1σ **fail** (1 node meets: digits +0.0051 [0.0018, 0.0086]; tabular +0.0016 [−0.0008, 0.0037]; breast-w −0.0006 [−0.0010, −0.0002]). Freed-run A3 − A2 per 20 at 0.1σ: digits +0.039 [0.015, 0.072]; tabular +0.002 [−0.009, 0.017]; breast-w −0.0078 (A2 executes nothing there, A3 7.8 %).

## Task 3 — C1 duplicate-rate report

- No-op kinds: `features.replay_campaign` now emits `noop_kind` (`inactive_edit` = edited key inactive for the candidate's model and the configuration changed; `incumbent_repeat` = every other no-op). `arms.noop_kind(row)` uses the field or derives it from existing features (`active_key`, `cfg_equals_incumbent`, `edit.symbol`) for older tables.
- `r1/c3/duplicate_report.py` (`python -m r1.c3.duplicate_report --table DIR [--out] [--md] [--label]`): per source × node × memory mode, per memory mode and total: proposals, campaigns, inactive edits, incumbent repeats (literal no-change subset), duplicates, other, fractions, wasted runs under ρ (total, per campaign, fraction). JSON + Markdown.
- Table: the 19 Oct proposal table was not committed (`*.jsonl` is git-ignored in `c3_split_recheck_20261019/`), so I rebuilt it with `r1.c3.dataset build` into `results/r1/engineering/c3_duplicate_rate_20261022/`; it is row-identical to the uncommitted 19 Oct table except for the new `noop_kind`. Committed: `build.json`, `duplicate_rate.json`, `duplicate_rate.md` (proposals.jsonl stays ignored and reproducible).
- Report: `docs/r1/reports/DUPLICATE_RATE_PILOT_20261022.md` (PILOT). Headline: 841 / 1,323 proposals (63.6 %) are rule-detectable; duplicates 727, no-ops 114 (all inactive edits, all DT4 ionosphere); 0 incumbent repeats. Memory-on rerun-2 arm A duplicates 51–66 % (9.7–12.5 wasted runs per 20-run campaign); DT4 digits (memory off) 77 %. The comparison with arXiv 2610.15738's 28–63 % is one sentence, noting their deterministic setting; I could not re-read that paper (no network) and quote the range from PLAN.

## Task 4 — audited-outcome mode in `di_test.py`

- Opt-in: `--outcome abs_metric --immediate audited --immediate-audits FILE --audit-source NAME`. `load_immediate_audits` reads `{"rows": [...]}` (the `di_candidate_audits.json` format) or a list, filtered by `source`; `apply_immediate_audits` replaces the immediate value at changed points with +Δ_audit (promotion) / −Δ_audit (demotion), refuses a direction mismatch, keeps the logged value where no audit exists, and reports coverage (`changed_points_with_audit`, `changed_points_logged`, unmatched audits). The report gains `immediate`, `immediate_audit`, `audited_mode_author` and a Markdown section with a per-point table — only in this mode.
- **Default output byte-identical:** checked by running the `259db53` version and the new version on the committed rerun-2 arm A (abs_metric) and DT4 (abs_metric and legacy) runs at the same input revision: all six files `cmp`-identical. Existing DI tests pass; +4 synthetic tests.
- PILOT result (file-only, ~35 s; outputs not committed — the CLI forbids writing under `results/`):
  - memory-on tabular (rerun-2 arm A, 13/13 changed points audited): value residual −0.00122 [−0.00222, −0.00026] (logged) → **+0.000041 [−0.00120, 0.00093]** (audited); verdict "violated in value terms" → "undetermined at this sample size".
  - memory-off digits (DT4, 6/6 audited): +0.00051 [−0.00259, 0.00418] → −0.000031 [−0.00147, 0.00340]; verdict unchanged (undetermined).
  - The point estimates reproduce the 19 Oct pilot report §3. **Limitations:** the bootstrap holds the audit values fixed (audit sampling error, se ≈ 0.0008–0.002 per point, is not propagated); the audits use all 6 seeds (no label/evaluation split is needed here); 10 of the 19 candidates are duplicates and two point pairs share the same (candidate, incumbent) pair. Not evidence.

## Task 5 — audit seeds K = 10

- `r1/c3/audit.py`: `DEFAULT_SEEDS = 7001..7010`; `PILOT_SEEDS = 7001..7006`; `split_seeds(seeds)` (even K ≥ 2; first half label, second half evaluation) and `split_audit(row)` (splits by the row's own recorded `seeds`, so K = 6 rows give 3 + 3 and K = 10 rows 5 + 5); `offline_eval.assemble` uses `split_audit`. `run` writes `audit_seeds.json` (latest seeds, with the label/evaluation halves); `collect` without `--seeds` reads it, else infers the seeds present in `runs.jsonl` (the pilot → 7001..7006). Extending an older directory to more seeds is allowed (cached runs reused).
- Sweep: config `audit` block (K = 10, 5 + 5) validated by the runner and written into the sweep manifests and the index (`seeds`, `label_seeds`, `evaluation_seeds`; index text now says K = 10).
- Cost note: at the pilot's 4.7 run-seconds per audited proposal for K = 6, K = 10 is ≈ 7.8 run-seconds, i.e. ≈ 2.2–6.5 CPU-hours per rerun-2-sized sweep (estimate, not measured).

## Task 6 — Paper A coordination command (`r1/scripts/paper_a_status.py`)

- Read-only, stdlib only; prints one JSON line (`verdict`, `reasons`, `evidence`, host, UTC, labels). `"paper_a_live_waiting_for_card": false` only for `clear_running` (running state value + live tmux session + ≥ 1 Paper A process among `nvidia-smi --query-compute-apps` PIDs, matched by `process_patterns` in `ps -o args=`) or `clear_finished` (finished/stopped state value or marker file, **and** no session, no Paper A GPU process, no unidentifiable GPU process). `true` for a waiting state value or a live session without a Paper A GPU process. Key omitted (`unknown`) for: wrong host, missing checkout/run dir, wrong or detached branch, unreadable state/key, a value in two sets, stale running state (optional max age), any unconfigured live signal (tmux session, process patterns), tmux/nvidia-smi errors, finished evidence contradicted by live signals, running state without both live signals, no state and nothing alive (stopped vs not started cannot be told). Any exception → unknown. Exit code 0 in all cases (the runner refuses on `true` or a missing key).
- Ada config `r1/scripts/configs/paper_a_status_ada.json`: host `ucrtasl`, branch `paper-a-v4-ada`, run dir `results/paper_a/replay_panel_v4/live_20261018T234416Z`; **`paper_a_checkout`, `state_file`, `state_key`, the value sets, `tmux_session` and `process_patterns` are null/empty (unverified), so the check refuses until they are filled.** Tested (`test_ada_config_refuses_until_verified`).
- **Verify read-only on Ada before first use** (also listed in the config's `verify_before_first_use`):
  1. the absolute path of the `agent-checkpoint-intervention` checkout running the live campaign; `git -C <path> symbolic-ref --short HEAD` prints `paper-a-v4-ada`;
  2. `results/paper_a/replay_panel_v4/live_20261018T234416Z` exists under it (or the absolute run path);
  3. which JSON file in the run directory the live runner updates (state/manifest/batch_state) and which dotted key holds its phase; every value that key takes, sorted into running (has its card, computing), finished/stopped, waiting-for-card; unclear values left out;
  4. any file written only at finish/stop (marker);
  5. the tmux session name (`tmux ls`; socket via `tmux_args` if not the default);
  6. a substring present in every Paper A GPU process command line and in no Paper B / other-user process (`nvidia-smi --query-compute-apps=pid --format=csv,noheader`, then `ps -o args= -p <pid>`);
  7. then run `python3 r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json` on Ada and compare verdict and evidence with what is observed.

## Task 7 — sweep config (`r1/scripts/configs/c3_sweep_ada.json`)

- Nodes = the five D21 nodes; `nodes_pending` = `openml_credit_approval`, `openml_diabetes` (a new runner key: recorded in manifests and index, **never run**, must be disjoint from `nodes`); 18 instances × W = 20 × {`append_only_summary`, `none`}; liveness 2 × W = 10 memory on; workers 4; transport retry 3; Paper A check = the new script + Ada config; pinned `qwen2.5-coder:7b` (digest pin unchanged in the runner); Ollama `/usr/local/bin/ollama`, own port 11481, models dir under the batch dir seeded from `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/ollama_models`; `allowed_hosts: ["ucrtasl"]`; audit K = 10 (5 + 5).
- How the liveness gate handles PLAN: the runner runs D28 liveness on all configured nodes first; a failing node is dropped from **both** memory modes (one eligible list). So `digits_mlp` stays out of memory-on collection unless it passes D28 in that phase, and if it fails it is also out of the memory-off sweep, leaving the memory-off-only vs exclusion choice to the author (PLAN 22 Oct). `openml_ionosphere` stays in: it passed D28 on 14 Oct and its 19 Oct exclusion is from the DI-test eligible pool (no decision-changed points), not from C3 labels — **coordinator please confirm**; the C3_DESIGN §4 count "4 nodes" predates wdbc's inclusion.
- Validation: `python r1/scripts/c3_label_sweep.py --config r1/scripts/configs/c3_sweep_ada.json --check-config` → rc 0 (new flag; runs the runner's own `load_config`, starts nothing). Desktop DRYRUN with the real config (`c3_sweep_dryrun.py --scenario retry --base-config …`; overrides only nodes→digits+breast-w, scale, GPU wait, fake Ollama, Paper A check → real `paper_a_status.py` against a fake finished Paper A run): **passed in 43.6 s** — dropped chat call resent with the same seed, all phases committed to the bare remote, restart refused, index carries audit seeds 7001..7010 (5 + 5) and the pending nodes, Paper A verdict `clear_finished`. Record: `results/r1/engineering/c3_sweep_dryrun_20261022T103215Z/` (DRYRUN). The default both-scenario dry run also passes inside the suite.

## Open issues and things I am unsure about

1. **The C3 pipeline does not know `openml_wdbc`** (nor credit_approval / diabetes): `r1/c3/features.py` `NODE_INFO`/`NODE_CODES` cover 4 nodes, so `dataset.build`, features and the audit stage would fail on sweep ledgers containing wdbc; `OPENML_ACTIVE` also drops `imputer` for every OpenML node, which is wrong for credit_approval (imputer active, NODE_KEY_AUDIT). `r1/diagnostics/di_test.project` likewise covers 4 nodes. Needs a small extension before the audit stage (not before the sweep launch).
2. `dataset.build` reads only the fixed historical `SOURCES`; there is no adapter from `C3_sweep_index_*.json` to a proposal table yet.
3. The Paper A Ada config is deliberately not launch-ready (nulls). The seeded models path and port 11481 are unverified on Ada (the runner refuses a used port and a digest mismatch).
4. `C3_DESIGN.md` §4 "Audit" bullet still says K = 6, and `HARNESS_AND_RUNNER_HANDOFF.md` item 8 too; PLAN's run-accounting row needs the corrected sensitivity wording (task 2). I did not edit design docs.
5. Freed-run variant: unbounded proposals (no LLM-call cap) and 1/exec-rate amplification — the pilot numbers show how large that can be; I would not read it as more than a bound-like sensitivity.
6. Gate verdict only on the instance split; LONO has no verdict. If the coordinator wants a LONO verdict too, that is a design decision.
7. The audited DI mode does not propagate audit noise into the CI (audits fixed across bootstrap draws).
8. `min_live_nodes` stays 2 (runner default); PLAN does not fix it for the sweep.


## Acceptance notes (coordinating session, 22 Oct)

- Freed-run sensitivity revised to the call-cap form (above).
- `r1/c3/features.py`: `openml_wdbc` and `openml_credit_approval` added to `NODE_INFO`; the D25 projection now comes from `OPENML_BY_MODEL_TYPE` minus a per-node `OPENML_DATASET_EXCLUDED` (imputer stays active on credit-approval, which has categorical columns); unknown OpenML nodes raise instead of being guessed; `NODE_CODES` is explicit so the original four nodes keep their codes (the rebuilt pilot table is byte-identical). `r1/diagnostics/di_test.project` extended the same way. A test checks both against the harness `configs/nodes/*.yaml`.
- C3_DESIGN §4 and the 19 Oct runner handoff now say K = 10 (5 + 5).
- Still open: adapter from the sweep index to `dataset.build`; Ada read-only verification of the Paper A config, seeded models path and port.
