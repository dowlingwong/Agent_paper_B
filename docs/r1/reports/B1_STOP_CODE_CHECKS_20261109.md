# B1 STOP — code-only checks D5 and D6 (9 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local overnight agent under `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` §1 step 1). Static reading of committed code only: no host contact, no run data, no anchor value. It classifies nothing and changes no STOP, pin or criterion. Plan: `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §3 (D5, D6). STOP record: `reports/B1_STOP_6835_20261108.md` (run `6835_20261108_a`, frozen checkout `68357d3d`).

**Checkouts compared.** Paper: Stage A's accepted checkout `3b3283f7` (the `t7h8` code named in PLAN §10) against the B1 checkout `68357d3d`. Harness: Stage A pin `897d83c8` (`PORTAL_EXAM_PHASE1_20261026.md`) against the B1 pin `a3fedbbd` (R1-EXAM-B1-HARNESS-PIN). The harness was read from the full harness clone at `.claude-worktrees/harness-cacheprompt` (HEAD `a3fedbb`; both commits present).

## D5 — metric orientation

| Node | Metric (harness `configs/nodes/<node>.yaml` at `a3fedbb`) | Direction | Acceptance rule | Changed `897d83c..a3fedbb`? |
|---|---|---|---|---|
| `digits_mlp` | `val_score` (validation accuracy) | maximize | `candidate_metric > current_best_metric` | no |
| `openml_credit_approval` | `val_auc` | maximize | `candidate_metric > current_best_metric` | no |
| `openml_ionosphere` | `val_auc` | maximize | `candidate_metric > current_best_metric` | no |

- `r1/c3/audit.py::paired(cand, inc)` returns `delta_audit = mean(cand − inc)` over seeds with both values present (unchanged in body since Stage A). With all three nodes maximizing, **positive `delta_audit` is an improvement on every node**.
- `r1/exam/campaign.py::_collect_b1_review` calls `paired(candidate_metrics, incumbent_metrics)` in that order and STOPs unless `k == 4` (all audit seeds 9101–9104 present).
- `r1/scripts/exam_runner.py::anchor_gate` calls `paired_instance_bootstrap(scripted, random_valid)`, so `difference = scripted − random_valid`; the gate STOPs if `difference_lower ≤ 0`. This is the direction RUNBOOK X.3 states ("random-valid < scripted").
- **No sign or orientation error is visible.** D5 does not support H4.

## D6 — anchor path between Stage A and B1

### Proposal laws and value grid

| Component | Stage A → B1 | Bearing |
|---|---|---|
| `scripted` = `r1/headroom/scripted_manager.py::ScriptedRandomManager` | **unchanged** (blob `1f1af532` in both) | one editable numeric symbol × log-uniform factor in [1/3, 3], clipped; 30 % categorical switch on OpenML nodes; RNG keyed by (instance seed, repetition 0, budget index) |
| `random_valid` = harness `autoresearch/manager/random_valid.py::RandomValidManager` | **unchanged** (blob `02c5385a` at both `897d83c` and `a3fedbb`; last changed in `897d83c`) | uniform active key, then uniform value from the declared grid; RNG `manager_seed(campaign_id, budget_index)` |
| `r1/exam/value_grids.yaml` | **unchanged** (blob `c29138a4`; file SHA-256 `7ab60c161433bf54d7392f7b3278b656a0e49ba1c28df05db81b410824b1ea14`) | grid for `random_valid` |
| node configs and node sources of the three B1 nodes (harness `configs/nodes/*.yaml`, `nodes/<node>/`) | **unchanged** `897d83c..a3fedbb` | the harness changes in that range touch four other OpenML nodes (D28 start configs) |
| `r1/exam/rules/x5_rule_v2.yaml` | new in B1 (SHA-256 `53018aa7…16ad`) | contains **no** anchor criterion; the ordering criterion lives only in RUNBOOK X.3 and `anchor_gate` |

### Gate and statistic

| Component | Stage A → B1 | Bearing |
|---|---|---|
| `r1/exam/guards.py::paired_instance_bootstrap` | **unchanged** (blob `c153c159`) | 2000 resamples of instance-pair differences, seed 20261026, 95 % percentile interval |
| `anchor_gate` | logic as accepted on 26 Oct; never exercised on real data before 8 Nov (DRYRUN overrides it) | as plan §1 |
| `r1/c3/audit.py::paired` | **unchanged** body | as D5 |

### Worker, audit and campaign wrappers (new or changed since Stage A)

| Component | Change | Effect on which edits run or how they count |
|---|---|---|
| `r1/c3/audit.py::run_config` | `_copy_audit_node` copies unedited files, then exclusively creates the selected editables (old code copied everything, then overwrote); `preserve_node_outputs` adds the B1 OpenML cache mixin and artifact guard; `stop_on_invalid` turns any failed or non-finite audit seed into a STOP; work directories are kept | same files end up in the audit copy; a failed audit seed now STOPs instead of being dropped, so every audited proposal has `k = 4` — consistent with the observed run reaching all 36 roots |
| `r1/exam/b1_proposal_guard.py::B1IntegrityWorker` | verifies that the structured edit and the worker's parsed directive agree, refuses regex escapes and non-literal Python values, otherwise runs the pinned `LocalWorker` | **raises a STOP, it does not mark edits invalid**; a mismatch would have stopped a campaign, which did not happen |
| `r1/exam/b1_editable_preserve.py::preserve_pinned_editables` | I/O adapter: before each write/unlink of an editable it retires the old inode into `node/_to_delete/` | no change to file contents written by the harness; `_to_delete/` sits beside the editable and is not read by the node's training script |
| `r1/exam/b1_openml_cache_guard.py` | refuses to run an OpenML node without the verified pilot data cache | prevents a fresh download; no effect on edit semantics |
| harness `control_plane/campaign.py` `897d83c..a3fedbb` | adds `controller_ledger_view` (identity when `None`, as in B1) and records `cache_prompt` on failed LLM calls | no effect on the software anchors |

### Features of the shared campaign logic relevant to H1/H2 (unchanged, but worth stating)

- The harness keeps the **first valid trial unconditionally** (`decision.py`: "First valid metric becomes the current best"). Each campaign's first audited proposal is therefore kept whatever its effect; its `delta_audit` is still measured against the start configuration.
- Software anchors run with an LLM budget of 1,000,000 and stop at `W = 20` worker runs. Proposals that are no-ops or repeat an evaluated configuration are excluded from the audit set (`active_equals_incumbent`, `active_seen_before`), so the two anchors can contribute different numbers of audited proposals per root and their budget indices can exceed 20.
- `scripted` makes small multiplicative moves of one numeric symbol; `random_valid` jumps to any grid value of any active key (including categorical keys such as `model_type` on OpenML nodes). The accepted descriptive capture's ranges (per-root mean `delta_audit` about −0.0166…+0.0148 for `random_valid`, −0.0028…+0.0013 for `scripted`) are consistent with that difference in step size; this is a reading of ranges, not of paired values.

## σ_node for D3 (constants embedded in the diagnosis script)

From the committed D21 noise floor `reports/NOISE_FLOOR_COMMON_20261022.md` (commit `511c3797`, file SHA-256 `9be292b773799d1591e55ea6845551a8fa121b00ec1a0dfe324b2c46de52c01d`), Table 1, 30 seeds per condition:

| Node | σ_joint [95 % CI] | median sd(Δ̂) |
|---|---|---|
| `digits_mlp` | 0.0102 [0.0081, 0.0137] | 0.0066 |
| `openml_credit_approval` | 0.0279 [0.0222, 0.0375] | 0.0030 |
| `openml_ionosphere` | 0.0410 [0.0327, 0.0551] | 0.0160 |

σ_joint is the primary scale because B1 audits set train seed = split seed (joint variation).

## Conclusion of the code checks

- **D5:** orientation and sign are correct on all three nodes.
- **D6:** both proposal laws, the value grid, the node configurations, the bootstrap and the gate statistic are byte-identical to what Stage A accepted. What is new (audit copy, integrity guard, editable preservation, OpenML cache guard) either leaves the evaluated files unchanged or converts failures into STOPs, not into silently miscounted trials.
- **No engineering defect was found in the code.** H4 stays open only for what the code cannot show: the data-side counts and consistency checks D0/D2 in the host diagnosis. No fix branch `mac-b1-fix-20261109` is opened.
